"""
AI DevOps Monitor - Updated with Agent Config & Email Settings
Run: uvicorn main:app --port 8000 --reload

MongoDB Collections:
- metrics: Raw metrics from Prometheus
- anomalies: Detected anomalies
- rca: Root cause analysis
- email_config: Email alert settings
"""
import sys
import json
import asyncio
import smtplib
import ssl
from datetime import datetime
from typing import Optional, List, Dict
from contextlib import asynccontextmanager
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import deque

import httpx
import requests
import certifi
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from pymongo import MongoClient
from pydantic import BaseModel

from config import (
    PROM_URL, MONGO_URI, DB_NAME,
    LLM_URL, LLM_MODEL,
    MONITOR_INTERVAL, Z_THRESHOLD, MAX_DOCS,
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, ALERT_EMAILS
)

# ============ MODELS ============
class Target(BaseModel):
    name: str
    endpoint: str
    job: str

class EmailConfig(BaseModel):
    enabled: bool
    recipients: List[str]

# Force unbuffered output
def log(msg):
    print(msg, flush=True)

# ============ THRESHOLDS ============
THRESHOLDS = {
    "up": {"min": 1, "severity": "critical", "msg": "Service is DOWN"},
    "cpu_usage": {"max": 80, "severity": "high", "msg": "High CPU usage"},
    "memory_usage": {"max": 80, "severity": "high", "msg": "High memory usage"},
    "http_request_duration_seconds": {"max": 5, "severity": "high", "msg": "High latency"},
    "errors_total": {"max": 10, "severity": "high", "msg": "High error count"},
    "disk_usage": {"max": 90, "severity": "critical", "msg": "Disk almost full"},
}

metric_history: Dict[str, deque] = {}

# ============ DATABASE ============
_mongo_client = None
_db_connected = False

def get_db():
    global _mongo_client, _db_connected
    try:
        uri = (MONGO_URI or "").strip()
        if not uri:
            log("[MongoDB Error] MONGO_URI not set")
            return None

        if _mongo_client is None:
            log("[MongoDB] Connecting...")
            _mongo_client = MongoClient(
                uri,
                serverSelectionTimeoutMS=2000,
                connectTimeoutMS=2000,
                socketTimeoutMS=2000,
                maxPoolSize=1
            )
            _db_connected = False

        if not _db_connected:
            _mongo_client[DB_NAME].list_collection_names()
            _db_connected = True
            log("[MongoDB] Connected!")

        return _mongo_client[DB_NAME]
    except Exception as e:
        log(f"[MongoDB Error] {e}")
        _mongo_client = None
        _db_connected = False
        return None

def cleanup_collection(db, collection: str):
    count = db[collection].count_documents({})
    if count > MAX_DOCS:
        old = list(db[collection].find().sort("timestamp", 1).limit(count - MAX_DOCS))
        if old:
            db[collection].delete_many({"_id": {"$in": [d["_id"] for d in old]}})
            log(f"[cleanup] Removed {len(old)} old docs from {collection}")

# ============ LLM ============
def ask_llm(prompt: str) -> Optional[str]:
    try:
        log(f"[LLM] Calling {LLM_URL}...")
        resp = requests.post(
            f"{LLM_URL}/api/generate",
            json={"model": LLM_MODEL, "prompt": prompt, "stream": False},
            timeout=30
        )
        log("[LLM] Response received")
        return resp.json().get("response", "") if resp.ok else None
    except requests.exceptions.Timeout:
        log("[LLM] Timeout after 30s")
        return None
    except Exception as e:
        log(f"[LLM] Error: {e}")
        return None

def parse_json(text: str) -> dict:
    try:
        s, e = text.find("{"), text.rfind("}") + 1
        return json.loads(text[s:e]) if s != -1 and e > s else {}
    except:
        return {}

# ============ PROMETHEUS ============
async def fetch_metrics_from_target(target_url: str) -> List[Dict]:
    """Fetch metrics from a specific target"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{target_url}/api/v1/query",
                params={"query": '{__name__=~".+"}'}
            )
            resp.raise_for_status()
            data = resp.json()

            if data.get("status") != "success":
                return []

            metrics = []
            for m in data.get("data", {}).get("result", []):
                name = m.get("metric", {}).get("__name__", "")
                if name.startswith(("prometheus_", "go_", "scrape_", "promhttp_")):
                    continue
                value = m.get("value", [None, None])[1]
                instance = m.get("metric", {}).get("instance", "unknown")
                if value is not None and value != "":
                    try:
                        metrics.append({"name": name, "value": float(value), "instance": instance})
                    except:
                        metrics.append({"name": name, "value": value, "instance": instance})
            return metrics
    except Exception as e:
        log(f"[Prometheus] Error fetching from {target_url}: {e}")
        return []

async def fetch_metrics() -> List[Dict]:
    """Fetch metrics from all configured targets"""
    db = get_db()
    if db is None:
        return []

    # Get all enabled targets from MongoDB
    targets = list(db.targets.find({"enabled": True}))

    # If no targets, use default PROM_URL
    if not targets:
        return await fetch_metrics_from_target(PROM_URL)

    # Fetch from all targets
    all_metrics = []
    for target in targets:
        target_url = f"http://{target['endpoint']}"
        metrics = await fetch_metrics_from_target(target_url)
        all_metrics.extend(metrics)

    return all_metrics

# ============ EMAIL ============
def send_alert(subject: str, body: str):
    db = get_db()
    if db is None:
        return False

    # Get email config from MongoDB
    config = db.email_config.find_one({})
    if not config or not config.get("enabled"):
        return False

    recipients = config.get("recipients", [])
    if not recipients or not SMTP_USER or not SMTP_PASSWORD:
        return False

    try:
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = ", ".join(recipients)
        msg.attach(MIMEText(body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        log(f"[Email] Error: {e}")
        return False

# ============ ANOMALY DETECTION ============
def update_history(name: str, value: float):
    if name not in metric_history:
        metric_history[name] = deque(maxlen=10)
    metric_history[name].append(value)

def detect_anomalies(metrics: List[Dict]) -> List[Dict]:
    anomalies = []

    for m in metrics:
        name, value = m["name"], m["value"]
        instance = m.get("instance", "unknown")

        if isinstance(value, (int, float)):
            update_history(name, value)

        # Threshold check
        for pattern, rules in THRESHOLDS.items():
            if pattern in name.lower():
                try:
                    val = float(value)
                    if "min" in rules and val < rules["min"]:
                        anomalies.append({
                            "metric": name,
                            "value": val,
                            "instance": instance,
                            "severity": rules["severity"],
                            "reason": rules["msg"]
                        })
                    if "max" in rules and val > rules["max"]:
                        anomalies.append({
                            "metric": name,
                            "value": val,
                            "instance": instance,
                            "severity": rules["severity"],
                            "reason": rules["msg"]
                        })
                except:
                    pass

        # Z-score check
        if isinstance(value, (int, float)) and name in metric_history:
            history = list(metric_history[name])
            if len(history) >= 5:
                avg = sum(history) / len(history)
                std = (sum((x - avg) ** 2 for x in history) / len(history)) ** 0.5
                if std > 0:
                    z = abs(value - avg) / std
                    if z > Z_THRESHOLD:
                        anomalies.append({
                            "metric": name,
                            "value": value,
                            "instance": instance,
                            "severity": "medium",
                            "reason": f"Statistical outlier (z={z:.1f})"
                        })

    return anomalies

# ============ LLM ANALYSIS ============
async def get_llm_analysis(anomaly: Dict, metrics: List[Dict]) -> Dict:
    context = "\n".join([f"- {m['name']}: {m['value']}" for m in metrics[:15]])

    prompt = f"""Anomaly detected:
Metric: {anomaly['metric']}
Value: {anomaly['value']}
Reason: {anomaly['reason']}

Context:
{context}

Respond JSON only:
{{"summary": "one line description", "cause": "root cause", "fix": "how to fix"}}"""

    resp = await asyncio.get_event_loop().run_in_executor(None, ask_llm, prompt)
    return parse_json(resp) if resp else {"summary": anomaly["reason"], "cause": "Unknown", "fix": "Investigate"}

# ============ MONITOR LOOP ============
async def monitor():
    log("[Monitor] Starting monitor loop...")
    await asyncio.sleep(2)

    while True:
        ts = datetime.now().strftime("%H:%M:%S")

        try:
            db = get_db()

            # 1. Fetch metrics from all targets
            metrics = await fetch_metrics()
            if not metrics:
                log(f"[{ts}] No metrics from Prometheus")
                await asyncio.sleep(MONITOR_INTERVAL)
                continue

            log(f"[{ts}] Fetched {len(metrics)} metrics")

            # 2. Save metrics to MongoDB
            if db is not None:
                try:
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: db.metrics.insert_one({
                            "timestamp": datetime.utcnow(),
                            "count": len(metrics),
                            "data": metrics[:50]
                        })
                    )
                    log(f"[{ts}] Saved metrics to MongoDB")
                except Exception as e:
                    log(f"[{ts}] MongoDB save error: {e}")

            # Optional: enforce MAX_DOCS (kept from your file, but it was never called)
            if db is not None:
                try:
                    await asyncio.get_event_loop().run_in_executor(None, lambda: cleanup_collection(db, "metrics"))
                    await asyncio.get_event_loop().run_in_executor(None, lambda: cleanup_collection(db, "anomalies"))
                    await asyncio.get_event_loop().run_in_executor(None, lambda: cleanup_collection(db, "rca"))
                except Exception as e:
                    log(f"[{ts}] Cleanup error: {e}")

            # 3. Detect anomalies
            anomalies = detect_anomalies(metrics)

            if not anomalies:
                log(f"[{ts}] No anomalies")
                await asyncio.sleep(MONITOR_INTERVAL)
                continue

            # Deduplicate
            seen = set()
            unique_anomalies = []
            for a in anomalies:
                if a["metric"] not in seen:
                    seen.add(a["metric"])
                    unique_anomalies.append(a)
            anomalies = unique_anomalies[:3]

            # 4. Process each anomaly
            for anomaly in anomalies:
                sev = anomaly["severity"].upper()
                log(f"[{ts}] ANOMALY [{sev}]: {anomaly['metric']}={anomaly['value']} - {anomaly['reason']}")

                # 5. Save anomaly to MongoDB
                anomaly_id = None
                if db is not None:
                    try:
                        result = await asyncio.get_event_loop().run_in_executor(
                            None,
                            lambda: db.anomalies.insert_one({
                                "timestamp": datetime.utcnow(),
                                "metric": anomaly["metric"],
                                "value": anomaly["value"],
                                "instance": anomaly.get("instance", "unknown"),
                                "severity": anomaly["severity"],
                                "reason": anomaly["reason"]
                            })
                        )
                        anomaly_id = result.inserted_id
                    except Exception as e:
                        log(f"[{ts}] Anomaly save error: {e}")

                # 6. Get LLM analysis
                analysis = await get_llm_analysis(anomaly, metrics)
                log(f"[{ts}] RCA: {analysis.get('cause')} | Fix: {analysis.get('fix')}")

                # 7. Save RCA to MongoDB
                if db is not None and anomaly_id is not None:
                    try:
                        await asyncio.get_event_loop().run_in_executor(
                            None,
                            lambda: db.rca.insert_one({
                                "timestamp": datetime.utcnow(),
                                "anomaly_id": anomaly_id,
                                "metric": anomaly["metric"],
                                "instance": anomaly.get("instance", "unknown"),
                                "summary": analysis.get("summary"),
                                "cause": analysis.get("cause"),
                                "fix": analysis.get("fix")
                            })
                        )
                    except Exception as e:
                        log(f"[{ts}] RCA save error: {e}")

                # 8. Send email
                body = f"""
                <h2>{sev} Anomaly</h2>
                <p><b>Metric:</b> {anomaly['metric']}</p>
                <p><b>Instance:</b> {anomaly.get('instance', 'unknown')}</p>
                <p><b>Value:</b> {anomaly['value']}</p>
                <p><b>Reason:</b> {anomaly['reason']}</p>
                <h3>RCA</h3>
                <p><b>Summary:</b> {analysis.get('summary')}</p>
                <p><b>Cause:</b> {analysis.get('cause')}</p>
                <p><b>Fix:</b> {analysis.get('fix')}</p>
                """
                if send_alert(f"[{sev}] {anomaly['metric']}", body):
                    log(f"[{ts}] Email sent")

        except Exception as e:
            log(f"[{ts}] Monitor error: {e}")

        await asyncio.sleep(MONITOR_INTERVAL)

# ============ FASTAPI ============
@asynccontextmanager
async def lifespan(app: FastAPI):
    log(f"Monitor started | Prometheus: {PROM_URL} | LLM: {LLM_MODEL}")
    log(f"MongoDB URI: {MONGO_URI[:30] if MONGO_URI else 'NOT SET'}...")

    # Initialize default email config
    db = get_db()
    if db is not None:
        if not db.email_config.find_one({}):
            db.email_config.insert_one({
                "enabled": False,
                "recipients": []
            })
            log("[Email] Initialized default config")

    task = asyncio.create_task(monitor())
    yield
    task.cancel()

app = FastAPI(title="AI DevOps Monitor", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
Instrumentator().instrument(app).expose(app)

# ============ API ENDPOINTS ============

@app.get("/")
def root():
    return {"status": "running", "prometheus": PROM_URL, "llm": LLM_MODEL}

@app.get("/stats")
def get_stats():
    """Get statistics for dashboard"""
    db = get_db()
    if db is None:
        return {"collections": {}}

    return {
        "collections": {
            "metrics": {"total": db.metrics.count_documents({})},
            "anomalies": {
                "total": db.anomalies.count_documents({}),
                "open": db.anomalies.count_documents({"severity": {"$in": ["critical", "high"]}}),
                "analyzed": db.rca.count_documents({})
            },
            "rca_results": {"total": db.rca.count_documents({})}
        }
    }

@app.get("/prom-metrics")
def get_prom_metrics():
    """Get recent metrics"""
    db = get_db()
    if db is None:
        return {"metrics": []}
    docs = list(db.metrics.find().sort("timestamp", -1).limit(10))
    for d in docs:
        d["_id"] = str(d["_id"])
        d["timestamp"] = d["timestamp"].isoformat()
    return {"metrics": docs}

@app.get("/anomalies")
def get_anomalies():
    db = get_db()
    if db is None:
        return {"anomalies": []}
    docs = list(db.anomalies.find().sort("timestamp", -1).limit(20))
    for d in docs:
        d["_id"] = str(d["_id"])
        d["timestamp"] = d["timestamp"].isoformat()
    return {"anomalies": docs}

@app.get("/rca")
def get_rca():
    db = get_db()
    if db is None:
        return {"rca": []}
    docs = list(db.rca.find().sort("timestamp", -1).limit(20))
    for d in docs:
        d["_id"] = str(d["_id"])
        d["anomaly_id"] = str(d.get("anomaly_id", ""))
        d["timestamp"] = d["timestamp"].isoformat()
    return {"rca": docs}

# ============ EMAIL CONFIG ENDPOINTS ============

@app.get("/agent/email-config")
def get_email_config():
    """Get email configuration"""
    db = get_db()
    if db is None:
        return {"enabled": False, "recipients": []}

    config = db.email_config.find_one({})
    if not config:
        return {"enabled": False, "recipients": []}

    return {
        "enabled": config.get("enabled", False),
        "recipients": config.get("recipients", [])
    }

@app.put("/agent/email-config")
def update_email_config(config: EmailConfig):
    """Update email configuration"""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    db.email_config.update_one(
        {},
        {"$set": {
            "enabled": config.enabled,
            "recipients": config.recipients
        }},
        upsert=True
    )

    return {"message": "Email config updated"}

@app.post("/agent/test-email")
def send_test_email():
    """Send a test email"""
    success = send_alert(
        "[TEST] AI DevOps Monitor",
        """
        <h2>Test Email</h2>
        <p>This is a test email from your AI DevOps Monitoring system.</p>
        <p>If you received this, your email configuration is working correctly!</p>
        """
    )

    if success:
        return {"message": "Test email sent successfully!"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send test email. Check your configuration.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
