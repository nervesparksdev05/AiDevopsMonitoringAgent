"""
AI DevOps Monitor - Updated with Session Management for Langfuse v3.12+ + Slack Integration (ENV ONLY)
Run: uvicorn main:app --port 8000 --reload

MongoDB Collections:
- metrics: Raw metrics from Prometheus
- anomalies: Detected anomalies
- rca: Root cause analysis
- targets: Prometheus targets configuration
- email_config: Email alert settings
- chat_sessions: Chat conversation sessions

Slack (ENV ONLY):
- SLACK_ENABLED=true/false
- SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

Langfuse v3.12+ SDK uses:
- get_client() for singleton client
- start_as_current_observation() context manager
- propagate_attributes() for session_id, user_id
- @observe decorator for function-level tracing
"""
import sys
import json
import asyncio
import smtplib
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from contextlib import asynccontextmanager, nullcontext
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import deque
import logging

# Configure logging
class MultiFileHandler(logging.Handler):
    """Custom handler to duplicate logs to multiple destinations based on level"""
    def __init__(self):
        super().__init__()
        self.error_handler = logging.FileHandler("error.log")
        self.error_handler.setLevel(logging.ERROR)

        self.debug_handler = logging.FileHandler("debug.log")
        self.debug_handler.setLevel(logging.DEBUG)

        self.info_handler = logging.FileHandler("app.log")
        self.info_handler.setLevel(logging.INFO)

        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        self.error_handler.setFormatter(formatter)
        self.debug_handler.setFormatter(formatter)
        self.info_handler.setFormatter(formatter)

    def emit(self, record):
        self.info_handler.emit(record)
        self.debug_handler.emit(record)
        if record.levelno >= logging.ERROR:
            self.error_handler.emit(record)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        MultiFileHandler(),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(override=True)

import httpx
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from pymongo import MongoClient
from pydantic import BaseModel


# ============ LANGFUSE v3.12+ CONFIGURATION ============
from langfuse import Langfuse, get_client, propagate_attributes, observe

LANGFUSE_AVAILABLE = True
langfuse = None


from config import (
    PROM_URL, MONGO_URI, DB_NAME,
    LLM_URL, LLM_MODEL,
    MONITOR_INTERVAL, Z_THRESHOLD, MAX_DOCS,
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, ALERT_EMAILS,
    SLACK_ENABLED, SLACK_WEBHOOK_URL,
)


# ============ LANGFUSE v3.12+ INITIALIZATION ============
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "").strip()
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "").strip()
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com").strip()
LANGFUSE_ENABLED = LANGFUSE_AVAILABLE and bool(LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY)

if LANGFUSE_ENABLED:
    try:
        Langfuse(
            public_key=LANGFUSE_PUBLIC_KEY,
            secret_key=LANGFUSE_SECRET_KEY,
            host=LANGFUSE_HOST,
        )
        langfuse = get_client()
        langfuse.auth_check()
        logger.info("[Langfuse] ✅ v3.12+ Connected successfully!")
    except Exception as e:
        logger.error(f"[Langfuse] ❌ Failed to initialize: {e}")
        langfuse = None
        LANGFUSE_ENABLED = False
else:
    if not LANGFUSE_AVAILABLE:
        logger.info("[Langfuse] ⚠️ Not installed")
    else:
        logger.info("[Langfuse] ⚠️ Disabled (API keys not set in .env)")


# ============ MODELS ============
class Target(BaseModel):
    name: str
    endpoint: str
    job: str

class EmailConfig(BaseModel):
    enabled: bool
    recipients: List[str]

class ChatMessage(BaseModel):
    message: str
    context: Dict = {}
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str


# ============ SESSION MANAGEMENT ============
class SessionManager:
    """Manage chat sessions and their metadata"""

    def __init__(self):
        self.active_sessions = {}  # In-memory cache

    def create_session(self, db) -> str:
        session_id = str(uuid.uuid4())
        session_data = {
            "session_id": session_id,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "message_count": 0,
            "total_tokens": 0,
        }
        if db is not None:
            try:
                db.chat_sessions.insert_one(session_data)
                logger.info(f"[Session] Created new session: {session_id}")
            except Exception as e:
                logger.error(f"[Session] Failed to create session in DB: {e}")
        self.active_sessions[session_id] = session_data
        return session_id

    def get_session(self, session_id: str, db) -> Optional[Dict]:
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        if db is not None:
            try:
                session = db.chat_sessions.find_one({"session_id": session_id})
                if session:
                    self.active_sessions[session_id] = session
                    return session
            except Exception as e:
                logger.error(f"[Session] Failed to fetch session: {e}")
        return None

    def update_session(self, session_id: str, db, tokens: int = 0):
        now = datetime.utcnow()
        if db is not None:
            try:
                db.chat_sessions.update_one(
                    {"session_id": session_id},
                    {
                        "$set": {"last_activity": now},
                        "$inc": {"message_count": 1, "total_tokens": tokens},
                    },
                )
            except Exception as e:
                logger.error(f"[Session] Failed to update session: {e}")

        if session_id in self.active_sessions:
            self.active_sessions[session_id]["last_activity"] = now
            self.active_sessions[session_id]["message_count"] = self.active_sessions[session_id].get("message_count", 0) + 1
            self.active_sessions[session_id]["total_tokens"] = self.active_sessions[session_id].get("total_tokens", 0) + tokens

    def cleanup_old_sessions(self, db, hours: int = 24):
        if db is None:
            return
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        try:
            result = db.chat_sessions.delete_many({"last_activity": {"$lt": cutoff}})
            if result.deleted_count > 0:
                logger.info(f"[Session] Cleaned up {result.deleted_count} old sessions")

            to_remove = [
                sid for sid, data in self.active_sessions.items()
                if data.get("last_activity", datetime.utcnow()) < cutoff
            ]
            for sid in to_remove:
                del self.active_sessions[sid]
        except Exception as e:
            logger.error(f"[Session] Cleanup failed: {e}")

session_manager = SessionManager()


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
            logger.error("[MongoDB Error] MONGO_URI not set")
            return None

        if _mongo_client is None:
            logger.info("[MongoDB] Connecting...")
            _mongo_client = MongoClient(
                uri,
                serverSelectionTimeoutMS=2000,
                connectTimeoutMS=2000,
                socketTimeoutMS=2000,
                maxPoolSize=1,
            )
            _db_connected = False

        if not _db_connected:
            _mongo_client[DB_NAME].list_collection_names()
            _db_connected = True
            logger.info("[MongoDB] Connected!")

        return _mongo_client[DB_NAME]
    except Exception as e:
        logger.error(f"[MongoDB Error] {e}")
        _mongo_client = None
        _db_connected = False
        return None

def cleanup_collection(db, collection: str):
    count = db[collection].count_documents({})
    if count > MAX_DOCS:
        old = list(db[collection].find().sort("timestamp", 1).limit(count - MAX_DOCS))
        if old:
            db[collection].delete_many({"_id": {"$in": [d["_id"] for d in old]}})
            logger.info(f"[cleanup] Removed {len(old)} old docs from {collection}")


# ============ SLACK ============
def _mask_webhook(url: str) -> str:
    if not url:
        return ""
    return url[:30] + "..." + url[-8:] if len(url) > 45 else "***"

def slack_is_configured() -> bool:
    return bool(SLACK_ENABLED and (SLACK_WEBHOOK_URL or "").strip())

def send_slack_alert_text(text: str) -> bool:
    """
    Minimal Slack sender using ONLY:
      - SLACK_ENABLED
      - SLACK_WEBHOOK_URL
    """
    if not SLACK_ENABLED:
        return False
    webhook = (SLACK_WEBHOOK_URL or "").strip()
    if not webhook:
        logger.warning("[Slack] SLACK_ENABLED=true but SLACK_WEBHOOK_URL is empty")
        return False

    payload = {
        "text": text,
        "username": "AI DevOps Monitor",
        "icon_emoji": ":rotating_light:",
    }

    try:
        logger.info(f"[Slack] Sending (webhook={_mask_webhook(webhook)})")
        resp = requests.post(webhook, json=payload, timeout=10)
        if not resp.ok:
            logger.error(f"[Slack] Failed: HTTP {resp.status_code} | {resp.text[:200]}")
            return False
        logger.info("[Slack] ✅ Alert sent")
        return True
    except Exception as e:
        logger.error(f"[Slack] Error: {e}")
        return False


# ============ LLM WITH LANGFUSE & SESSION SUPPORT ============
def ask_llm(
    prompt: str,
    trace_name: str = "LLM Call",
    metadata: dict = None,
    session_id: Optional[str] = None,
) -> Optional[tuple[str, int]]:
    response_text = None
    total_tokens = 0

    if langfuse and LANGFUSE_ENABLED:
        try:
            with langfuse.start_as_current_observation(
                as_type="span",
                name=trace_name,
                metadata={**(metadata or {}), "model": LLM_MODEL, "endpoint": LLM_URL},
            ) as root_span:
                with propagate_attributes(session_id=session_id) if session_id else nullcontext():
                    with langfuse.start_as_current_observation(
                        as_type="generation",
                        name="llm-generation",
                        model=LLM_MODEL,
                        input=prompt,
                    ) as generation:
                        try:
                            log_msg = f"[LLM] Calling {LLM_URL}..."
                            if session_id:
                                log_msg += f" (session: {session_id})"
                            logger.info(log_msg)

                            start_time = datetime.utcnow()
                            resp = requests.post(
                                f"{LLM_URL}/api/generate",
                                json={"model": LLM_MODEL, "prompt": prompt, "stream": False},
                                timeout=30,
                            )
                            end_time = datetime.utcnow()
                            latency_ms = (end_time - start_time).total_seconds() * 1000

                            logger.info(f"[LLM] Response received ({latency_ms:.0f}ms)")

                            if not resp.ok:
                                logger.error(f"[LLM] Error: HTTP {resp.status_code}")
                                generation.update(
                                    output=f"Error: HTTP {resp.status_code}",
                                    metadata={"error": True, "status_code": resp.status_code, "latency_ms": latency_ms},
                                )
                                return None, 0

                            response_text = resp.json().get("response", "")

                            input_tokens = int(len(prompt.split()) * 1.3)
                            output_tokens = int(len(response_text.split()) * 1.3)
                            total_tokens = input_tokens + output_tokens

                            generation.update(
                                output=response_text,
                                usage={"input": input_tokens, "output": output_tokens, "total": total_tokens},
                                metadata={"latency_ms": latency_ms, "error": False},
                            )

                            logger.info(f"[Langfuse] ✅ Logged generation ({total_tokens} tokens)")
                        except requests.exceptions.Timeout:
                            logger.error("[LLM] Timeout after 30s")
                            generation.update(output="Error: Timeout", metadata={"error": True, "timeout": True})
                            return None, 0
                        except Exception as e:
                            logger.error(f"[LLM] Error: {e}")
                            generation.update(output=f"Error: {str(e)}", metadata={"error": True})
                            return None, 0

                root_span.update(output={"response": response_text, "tokens": total_tokens})
            return response_text, total_tokens
        except Exception as e:
            logger.warning(f"[Langfuse] Error in tracing: {e}")

    # Fallback no tracing
    try:
        logger.info(f"[LLM] Calling {LLM_URL} (no tracing)...")
        resp = requests.post(
            f"{LLM_URL}/api/generate",
            json={"model": LLM_MODEL, "prompt": prompt, "stream": False},
            timeout=30,
        )
        if not resp.ok:
            logger.error(f"[LLM] Error: HTTP {resp.status_code}")
            return None, 0
        response_text = resp.json().get("response", "")
        total_tokens = int(len((prompt + response_text).split()) * 1.3)
        return response_text, total_tokens
    except Exception as e:
        logger.error(f"[LLM] Error: {e}")
        return None, 0


def parse_json(text: str) -> dict:
    try:
        s, e = text.find("{"), text.rfind("}") + 1
        return json.loads(text[s:e]) if s != -1 and e > s else {}
    except Exception:
        return {}


# ============ PROMETHEUS ============
async def fetch_metrics_from_target(target_url: str) -> List[Dict]:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{target_url}/api/v1/query",
                params={"query": '{__name__=~".+"}'},
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
                    except Exception:
                        metrics.append({"name": name, "value": value, "instance": instance})
            return metrics
    except Exception as e:
        logger.error(f"[Prometheus] Error fetching from {target_url}: {e}")
        return []

async def fetch_metrics() -> List[Dict]:
    db = get_db()
    if db is None:
        return []

    targets = list(db.targets.find({"enabled": True}))
    if not targets:
        return await fetch_metrics_from_target(PROM_URL)

    all_metrics: List[Dict] = []
    for target in targets:
        target_url = f"http://{target['endpoint']}"
        metrics = await fetch_metrics_from_target(target_url)
        all_metrics.extend(metrics)
    return all_metrics


# ============ EMAIL ============
def send_alert(subject: str, body: str) -> bool:
    db = get_db()
    if db is None:
        return False

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
        logger.error(f"[Email] Error: {e}")
        return False


# ============ ANOMALY DETECTION ============
def update_history(name: str, value: float):
    if name not in metric_history:
        metric_history[name] = deque(maxlen=10)
    metric_history[name].append(value)

def detect_anomalies(metrics: List[Dict]) -> List[Dict]:
    anomalies: List[Dict] = []

    for m in metrics:
        name, value = m["name"], m["value"]
        instance = m.get("instance", "unknown")

        if isinstance(value, (int, float)):
            update_history(name, float(value))

        # Threshold check
        for pattern, rules in THRESHOLDS.items():
            if pattern in name.lower():
                try:
                    val = float(value)
                    if "min" in rules and val < rules["min"]:
                        anomalies.append({"metric": name, "value": val, "instance": instance, "severity": rules["severity"], "reason": rules["msg"]})
                    if "max" in rules and val > rules["max"]:
                        anomalies.append({"metric": name, "value": val, "instance": instance, "severity": rules["severity"], "reason": rules["msg"]})
                except Exception:
                    pass

        # Z-score check
        if isinstance(value, (int, float)) and name in metric_history:
            history = list(metric_history[name])
            if len(history) >= 5:
                avg = sum(history) / len(history)
                std = (sum((x - avg) ** 2 for x in history) / len(history)) ** 0.5
                if std > 0:
                    z = abs(float(value) - avg) / std
                    if z > Z_THRESHOLD:
                        anomalies.append({"metric": name, "value": float(value), "instance": instance, "severity": "medium", "reason": f"Statistical outlier (z={z:.1f})"})
    return anomalies


# ============ LLM ANALYSIS WITH LANGFUSE v3.12+ & SESSION ============
async def get_llm_analysis(anomaly: Dict, metrics: List[Dict], anomaly_id: str, session_id: str) -> Dict:
    context = "\n".join([f"- {m['name']}: {m['value']}" for m in metrics[:15]])

    prompt = f"""Anomaly detected:
Metric: {anomaly['metric']}
Value: {anomaly['value']}
Instance: {anomaly.get('instance', 'unknown')}
Severity: {anomaly.get('severity', 'unknown')}
Reason: {anomaly['reason']}

Related metrics:
{context}

Analyze this anomaly and respond with ONLY valid JSON in this format:
{{"summary": "technical one-line description", "simplified": "simple explanation for non-technical users (ELI5)", "cause": "most likely root cause", "fix": "specific remediation steps"}}"""

    metadata = {
        "anomaly_id": str(anomaly_id),
        "metric": anomaly["metric"],
        "severity": anomaly.get("severity", "unknown"),
        "instance": anomaly.get("instance", "unknown"),
    }

    result = await asyncio.get_event_loop().run_in_executor(
        None,
        ask_llm,
        prompt,
        f"RCA: {anomaly['metric']}",
        metadata,
        session_id,
    )

    resp, _tokens = result if result else (None, 0)
    parsed = parse_json(resp) if resp else {}

    if langfuse and LANGFUSE_ENABLED and parsed:
        try:
            quality = 0.0
            if parsed.get("summary"): quality += 0.33
            if parsed.get("cause"): quality += 0.33
            if parsed.get("fix"): quality += 0.34
            logger.info(f"[Langfuse] RCA quality score: {quality:.2f}")
        except Exception as e:
            logger.warning(f"[Langfuse] Could not calculate score: {e}")

    return parsed or {
        "summary": anomaly["reason"],
        "cause": "Unknown - LLM unavailable or parsing failed",
        "fix": "Check logs and investigate manually",
    }


# ============ MONITORING SESSION TRACKING (Langfuse v3.12+) ============
class MonitoringSession:
    """Track entire monitoring cycle in Langfuse v3.12+"""

    def __init__(self, timestamp: str):
        self.timestamp = timestamp
        self.session_id = f"monitor-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.root_span = None
        self._context = None
        self._propagate_ctx = None

        if langfuse and LANGFUSE_ENABLED:
            try:
                self._context = langfuse.start_as_current_observation(
                    as_type="span",
                    name="Monitoring Cycle",
                    metadata={"timestamp": timestamp, "cycle_type": "scheduled", "session_id": self.session_id},
                )
                self.root_span = self._context.__enter__()

                self._propagate_ctx = propagate_attributes(session_id=self.session_id)
                self._propagate_ctx.__enter__()

                logger.info(f"[Session] Started monitoring session: {self.session_id}")
            except Exception as e:
                logger.warning(f"[Langfuse] Could not start monitoring trace: {e}")
                self.root_span = None
                self._context = None
                self._propagate_ctx = None

    def end(self, metrics_count: int = 0, anomalies_count: int = 0, success: bool = True):
        if self.root_span and self._context:
            try:
                self.root_span.update(
                    output={"metrics_collected": metrics_count, "anomalies_detected": anomalies_count, "success": success}
                )

                if self._propagate_ctx:
                    try:
                        self._propagate_ctx.__exit__(None, None, None)
                    except Exception:
                        pass

                self._context.__exit__(None, None, None)
                logger.info(f"[Session] Ended monitoring session: {self.session_id}")
            except Exception as e:
                logger.warning(f"[Langfuse] Could not end monitoring span: {e}")


# ============ MONITOR LOOP ============
async def monitor():
    logger.info("[Monitor] Starting monitor loop...")
    await asyncio.sleep(2)

    while True:
        ts = datetime.now().strftime("%H:%M:%S")
        session = MonitoringSession(ts)

        try:
            db = get_db()

            # 1) Fetch metrics
            metrics = await fetch_metrics()
            if not metrics:
                logger.info(f"[{ts}] No metrics from Prometheus")
                session.end(metrics_count=0, anomalies_count=0, success=True)
                await asyncio.sleep(MONITOR_INTERVAL)
                continue

            logger.info(f"[{ts}] Fetched {len(metrics)} metrics")

            # 2) Save metrics
            if db is not None:
                try:
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: db.metrics.insert_one({"timestamp": datetime.utcnow(), "count": len(metrics), "data": metrics[:50]}),
                    )
                    logger.info(f"[{ts}] Saved metrics to MongoDB")
                except Exception as e:
                    logger.error(f"[{ts}] MongoDB save error: {e}")

            # Cleanup
            if db is not None:
                try:
                    await asyncio.get_event_loop().run_in_executor(None, lambda: cleanup_collection(db, "metrics"))
                    await asyncio.get_event_loop().run_in_executor(None, lambda: cleanup_collection(db, "anomalies"))
                    await asyncio.get_event_loop().run_in_executor(None, lambda: cleanup_collection(db, "rca"))
                except Exception as e:
                    logger.error(f"[{ts}] Cleanup error: {e}")

            # 3) Detect anomalies
            anomalies = detect_anomalies(metrics)
            if not anomalies:
                logger.info(f"[{ts}] No anomalies")
                session.end(metrics_count=len(metrics), anomalies_count=0, success=True)
                await asyncio.sleep(MONITOR_INTERVAL)
                continue

            # Deduplicate and limit
            seen = set()
            unique_anomalies = []
            for a in anomalies:
                if a["metric"] not in seen:
                    seen.add(a["metric"])
                    unique_anomalies.append(a)
            anomalies = unique_anomalies[:3]

            # 4) Process anomalies
            for anomaly in anomalies:
                sev = anomaly["severity"].upper()
                logger.error(f"[{ts}] ANOMALY [{sev}]: {anomaly['metric']}={anomaly['value']} - {anomaly['reason']}")

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
                                "reason": anomaly["reason"],
                            }),
                        )
                        anomaly_id = result.inserted_id
                    except Exception as e:
                        logger.error(f"[{ts}] Anomaly save error: {e}")

                analysis = await get_llm_analysis(
                    anomaly,
                    metrics,
                    str(anomaly_id) if anomaly_id else "unknown",
                    session.session_id,
                )
                logger.info(f"[{ts}] RCA: {analysis.get('cause')} | Fix: {analysis.get('fix')}")

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
                                "simplified": analysis.get("simplified"),
                                "cause": analysis.get("cause"),
                                "fix": analysis.get("fix"),
                            }),
                        )
                    except Exception as e:
                        logger.error(f"[{ts}] RCA save error: {e}")

                # Email
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
                    logger.info(f"[{ts}] Email sent")

                # Slack (ENV ONLY)
                try:
                    slack_msg = (
                        f"[{sev}] Anomaly\n"
                        f"Metric: {anomaly['metric']}\n"
                        f"Instance: {anomaly.get('instance','unknown')}\n"
                        f"Value: {anomaly['value']}\n"
                        f"Reason: {anomaly['reason']}\n"
                        f"Cause: {analysis.get('cause')}\n"
                        f"Fix: {analysis.get('fix')}\n"
                        f"Session: {session.session_id}"
                    )
                    if send_slack_alert_text(slack_msg):
                        logger.info(f"[{ts}] Slack sent")
                except Exception as e:
                    logger.error(f"[{ts}] Slack send error: {e}")

            session.end(metrics_count=len(metrics), anomalies_count=len(anomalies), success=True)

        except Exception as e:
            logger.error(f"[{ts}] Monitor error: {e}")
            session.end(metrics_count=0, anomalies_count=0, success=False)

        await asyncio.sleep(MONITOR_INTERVAL)


# ============ FASTAPI ============
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Monitor started | Prometheus: {PROM_URL} | LLM: {LLM_MODEL}")
    logger.info(f"MongoDB URI: {MONGO_URI[:30] if MONGO_URI else 'NOT SET'}...")

    status_msg = "✅ Enabled (v3.12+)" if LANGFUSE_ENABLED else "❌ Disabled"
    if not LANGFUSE_ENABLED:
        status_msg += f" (Module: {LANGFUSE_AVAILABLE}, PK: {bool(LANGFUSE_PUBLIC_KEY)}, SK: {bool(LANGFUSE_SECRET_KEY)})"
    logger.info(f"Langfuse: {status_msg}")

    logger.info(f"Slack: {'✅ Enabled' if slack_is_configured() else '❌ Disabled'}")

    db = get_db()
    if db is not None:
        # default email config
        if not db.email_config.find_one({}):
            db.email_config.insert_one({"enabled": False, "recipients": []})
            logger.info("[Email] Initialized default config")

        # indexes for chat sessions
        try:
            db.chat_sessions.create_index("session_id", unique=True)
            db.chat_sessions.create_index("last_activity")
            logger.info("[Session] Created database indexes")
        except Exception as e:
            logger.warning(f"[Session] Index creation warning: {e}")

    task = asyncio.create_task(monitor())

    async def cleanup_sessions():
        while True:
            await asyncio.sleep(3600)
            db2 = get_db()
            if db2:
                session_manager.cleanup_old_sessions(db2, hours=24)

    cleanup_task = asyncio.create_task(cleanup_sessions())

    yield

    if langfuse and LANGFUSE_ENABLED:
        try:
            logger.info("[Langfuse] Flushing remaining data...")
            langfuse.flush()
            logger.info("[Langfuse] ✅ Flush complete")
        except Exception as e:
            logger.warning(f"[Langfuse] Flush error: {e}")

    task.cancel()
    cleanup_task.cancel()


app = FastAPI(title="AI DevOps Monitor", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
Instrumentator().instrument(app).expose(app)


# ============ API ENDPOINTS ============
@app.get("/")
def root():
    return {
        "status": "running",
        "prometheus": PROM_URL,
        "llm": LLM_MODEL,
        "langfuse": "enabled (v3.12+)" if LANGFUSE_ENABLED else "disabled",
        "sessions": "enabled",
        "slack": "enabled" if slack_is_configured() else "disabled",
        "slack_webhook_set": bool((SLACK_WEBHOOK_URL or "").strip()),
    }

@app.get("/stats")
def get_stats():
    db = get_db()
    if db is None:
        return {"collections": {}}

    return {
        "collections": {
            "metrics": {"total": db.metrics.count_documents({})},
            "anomalies": {
                "total": db.anomalies.count_documents({}),
                "open": db.anomalies.count_documents({"severity": {"$in": ["critical", "high"]}}),
                "analyzed": db.rca.count_documents({}),
            },
            "rca_results": {"total": db.rca.count_documents({})},
            "chat_sessions": {
                "total": db.chat_sessions.count_documents({}),
                "active": db.chat_sessions.count_documents({"last_activity": {"$gte": datetime.utcnow() - timedelta(hours=1)}}),
            },
        }
    }

@app.get("/prom-metrics")
def get_prom_metrics():
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


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage):
    db = get_db()

    session_id = message.session_id
    if not session_id or not session_manager.get_session(session_id, db):
        session_id = session_manager.create_session(db)
        logger.info(f"[Chat] New conversation session: {session_id}")
    else:
        logger.info(f"[Chat] Continuing session: {session_id}")

    context_str = ""
    if message.context:
        context_lines = ["Context:"]
        for k, v in message.context.items():
            if k != "session_id":
                context_lines.append(f"- {k}: {v}")
        context_str = "\n".join(context_lines)

    prompt = f"""You are a helpful DevOps assistant.
User asks: {message.message}

{context_str}

Provide a helpful, concise answer. Explain technical concepts simply if asked."""

    result = await asyncio.get_event_loop().run_in_executor(
        None,
        ask_llm,
        prompt,
        "AI Chat",
        {"user_message": message.message, **message.context},
        session_id,
    )

    response_text, tokens = result if result else (None, 0)
    session_manager.update_session(session_id, db, tokens)

    return {
        "response": response_text or "Sorry, I'm having trouble connecting to the AI service.",
        "session_id": session_id,
    }


# ============ SESSION MANAGEMENT ENDPOINTS ============
@app.get("/api/sessions")
def get_sessions():
    db = get_db()
    if db is None:
        return {"sessions": []}

    sessions = list(db.chat_sessions.find().sort("last_activity", -1).limit(50))
    for s in sessions:
        s["_id"] = str(s["_id"])
        s["created_at"] = s["created_at"].isoformat()
        s["last_activity"] = s["last_activity"].isoformat()
    return {"sessions": sessions}

@app.get("/api/sessions/{session_id}")
def get_session_details(session_id: str):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    session = session_manager.get_session(session_id, db)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session["_id"] = str(session["_id"])
    session["created_at"] = session["created_at"].isoformat()
    session["last_activity"] = session["last_activity"].isoformat()
    return session

@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: str):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    result = db.chat_sessions.delete_one({"session_id": session_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")

    if session_id in session_manager.active_sessions:
        del session_manager.active_sessions[session_id]

    return {"message": "Session deleted successfully"}


# ============ EMAIL CONFIG ENDPOINTS ============
@app.get("/agent/email-config")
def get_email_config():
    db = get_db()
    if db is None:
        return {"enabled": False, "recipients": []}

    config = db.email_config.find_one({})
    if not config:
        return {"enabled": False, "recipients": []}

    return {"enabled": config.get("enabled", False), "recipients": config.get("recipients", [])}

@app.put("/agent/email-config")
def update_email_config(config: EmailConfig):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    db.email_config.update_one(
        {},
        {"$set": {"enabled": config.enabled, "recipients": config.recipients}},
        upsert=True,
    )
    return {"message": "Email config updated"}

@app.post("/agent/test-email")
def send_test_email():
    success = send_alert(
        "[TEST] AI DevOps Monitor",
        """
        <h2>Test Email</h2>
        <p>This is a test email from your AI DevOps Monitoring system.</p>
        <p>If you received this, your email configuration is working correctly!</p>
        """,
    )
    if success:
        return {"message": "Test email sent successfully!"}
    raise HTTPException(status_code=500, detail="Failed to send test email. Check your configuration.")


# ============ SLACK TEST ENDPOINT (ENV ONLY) ============
@app.get("/agent/slack-status")
def slack_status():
    return {
        "enabled_flag": bool(SLACK_ENABLED),
        "webhook_url_set": bool((SLACK_WEBHOOK_URL or "").strip()),
        "active": slack_is_configured(),
    }

@app.post("/agent/test-slack")
def test_slack():
    if not slack_is_configured():
        raise HTTPException(status_code=400, detail="Slack is not configured. Set SLACK_ENABLED=true and SLACK_WEBHOOK_URL.")
    ok = send_slack_alert_text("[TEST] AI DevOps Monitor: Slack webhook is working ✅")
    if ok:
        return {"message": "Test Slack message sent successfully!"}
    raise HTTPException(status_code=500, detail="Failed to send Slack message. Check webhook / network.")


# ============ LANGFUSE STATUS ENDPOINT ============
@app.get("/langfuse/status")
def get_langfuse_status():
    status = {
        "installed": LANGFUSE_AVAILABLE,
        "enabled": LANGFUSE_ENABLED,
        "version": "v3.12+",
        "host": LANGFUSE_HOST if LANGFUSE_ENABLED else None,
        "connected": False,
        "session_tracking": True,
        "api_methods": {
            "tracing": "start_as_current_observation()",
            "sessions": "propagate_attributes(session_id=...)",
            "decorator": "@observe",
        },
    }
    if langfuse and LANGFUSE_ENABLED:
        try:
            langfuse.auth_check()
            status["connected"] = True
        except Exception as e:
            status["error"] = str(e)
    return status


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
