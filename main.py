"""
AI DevOps Monitor - Updated with Agent Config, Email Settings & Langfuse v3 Integration
Run: uvicorn main:app --port 8000 --reload

MongoDB Collections:
- metrics: Raw metrics from Prometheus
- anomalies: Detected anomalies
- rca: Root cause analysis
- targets: Prometheus targets configuration
- email_config: Email alert settings

Langfuse v3 SDK uses:
- get_client() for singleton client
- start_as_current_observation() context manager
- @observe decorator
"""
import threading #to look  for the threads

import sys
import io
import json
import asyncio
import smtplib
import ssl
import os
from datetime import datetime
from typing import Optional, List, Dict
from contextlib import asynccontextmanager
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import deque
import logging
# adding multithreading 

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from concurrent.futures import ThreadPoolExecutor

ANOMALY_WORKERS = 4  # configurable
anomaly_executor = ThreadPoolExecutor(max_workers=ANOMALY_WORKERS)
MAIN_EVENT_LOOP = None


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
        logging.StreamHandler(sys.stdout)
    ]
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


# Import Langfuse v3
LANGFUSE_AVAILABLE = False
langfuse = None

try:
    from langfuse import Langfuse, get_client
    LANGFUSE_AVAILABLE = True
    logger.info("[Langfuse] v3 SDK imported successfully")
except ImportError:
    # Trigger reload 2
    logger.warning("[Langfuse] Package not installed. Run: pip install langfuse --break-system-packages")

from config import (
    PROM_URL, MONGO_URI, DB_NAME,
    LLM_URL, LLM_MODEL,
    MONITOR_INTERVAL, Z_THRESHOLD, MAX_DOCS,
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, ALERT_EMAILS
)

# ============ LANGFUSE v3 CONFIGURATION ============
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "").strip()
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "").strip()
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com").strip()
LANGFUSE_ENABLED = LANGFUSE_AVAILABLE and bool(LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY)

# Initialize Langfuse v3
if LANGFUSE_ENABLED:
    try:
        # v3: Initialize with constructor, then use get_client()
        Langfuse(
            public_key=LANGFUSE_PUBLIC_KEY,
            secret_key=LANGFUSE_SECRET_KEY,
            host=LANGFUSE_HOST
        )
        langfuse = get_client()
        
        # Verify connection
        langfuse.auth_check()
        logger.info("[Langfuse]  v3 Connected successfully!")
    except Exception as e:
        logger.error(f"[Langfuse]  Failed to initialize: {e}")
        langfuse = None
        LANGFUSE_ENABLED = False
else:
    if not LANGFUSE_AVAILABLE:
        logger.info("[Langfuse]  Not installed")
    else:
        logger.info("[Langfuse]  Disabled (API keys not set in .env)")

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

class ChatResponse(BaseModel):
    response: str


# ============ THRESHOLDS ============
THRESHOLDS = {
    "up": {"min": 1, "severity": "critical", "msg": "Service is DOWN"},
    "cpu_usage": {"max": 1, "severity": "high", "msg": "High CPU usage"},
    "memory_usage": {"max": 1, "severity": "high", "msg": "High memory usage"},
    "http_request_duration_seconds": {"max": 5, "severity": "high", "msg": "High latency"},
    "errors_total": {"max": 10, "severity": "high", "msg": "High error count"},
    "disk_usage": {"max": 1, "severity": "critical", "msg": "Disk almost full"},
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
                maxPoolSize=ANOMALY_WORKERS + 2

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

# ============ LLM WITH LANGFUSE v3 ============
def ask_llm(prompt: str, trace_name: str = "LLM Call", metadata: dict = None) -> Optional[str]:
    """
    Call LLM with Langfuse v3 tracking
    Uses: start_as_current_observation() context manager
    """
    
    response_text = None
    
    # If Langfuse is enabled, use context manager
    if langfuse:
        try:
            # Create a span for the entire operation
            with langfuse.start_as_current_observation(
                as_type="span",
                name=trace_name,
                metadata={
                    **(metadata or {}),
                    "model": LLM_MODEL,
                    "endpoint": LLM_URL
                }
            ) as span:
                # Create nested generation for the LLM call
                with langfuse.start_as_current_observation(
                    as_type="generation",
                    name="llm_call",
                    model=LLM_MODEL,
                    input=prompt
                ) as generation:
                    try:
                        logger.info(f"[LLM] Calling {LLM_URL}...")
                        start_time = datetime.utcnow()
                        
                        resp = requests.post(
                            f"{LLM_URL}/api/generate",
                            json={"model": LLM_MODEL, "prompt": prompt, "stream": False},
                            timeout=30
                        )
                        
                        end_time = datetime.utcnow()
                        latency_ms = (end_time - start_time).total_seconds() * 1000
                        
                        logger.info(f"[LLM] Response received ({latency_ms:.0f}ms)")
                        
                        if not resp.ok:
                            logger.error(f"[LLM] Error: HTTP {resp.status_code}")
                            generation.update(
                                output=f"Error: HTTP {resp.status_code}",
                                metadata={"error": True, "status_code": resp.status_code, "latency_ms": latency_ms}
                            )
                            return None
                        
                        response_text = resp.json().get("response", "")
                        
                        # Estimate tokens
                        input_tokens = int(len(prompt.split()) * 1.3)
                        output_tokens = int(len(response_text.split()) * 1.3)
                        
                        # Update generation with output
                        generation.update(
                            output=response_text,
                            usage_details={
                                "input_tokens": input_tokens,
                                "output_tokens": output_tokens,
                                "total_tokens": input_tokens + output_tokens
                            },
                            metadata={"latency_ms": latency_ms, "error": False}
                        )
                        parsed = {}
                        try:
                           parsed = parse_json(response_text)
                        except Exception:
                           parsed = {}

                        if parsed:
                            quality = 0.0
                            if parsed.get("summary"): quality += 0.33
                            if parsed.get("cause"): quality += 0.33
                            if parsed.get("fix"): quality += 0.34

                            try:
                               generation.score(
                                 name="rca_completeness",
                                 value=quality,
                                 comment=f"Fields present: {list(parsed.keys())}"
        )
                               logger.info(f"[Langfuse]  RCA quality score: {quality:.2f}")
                            except Exception as e:
                              logger.warning(f"[Langfuse] Score failed: {e}")

                        logger.info(f"[Langfuse]  Logged generation ({input_tokens + output_tokens} tokens)")
                        
                    except requests.exceptions.Timeout:
                        logger.error("[LLM] Timeout after 30s")
                        generation.update(output="Error: Timeout", metadata={"error": True, "timeout": True})
                        return None
                    
                    except Exception as e:
                        logger.error(f"[LLM] Error: {e}")
                        generation.update(output=f"Error: {str(e)}", metadata={"error": True})
                        return None
                
                # Update span with final output
                span.update(output={"response": response_text[:100] if response_text else "No response"})
            
            return response_text
            
        except Exception as e:
            logger.warning(f"[Langfuse] Error in tracing: {e}")
            # Fall through to non-traced call
    
    # Fallback: Call LLM without Langfuse tracing
    try:
        logger.info(f"[LLM] Calling {LLM_URL} (no tracing)...")
        resp = requests.post(
            f"{LLM_URL}/api/generate",
            json={"model": LLM_MODEL, "prompt": prompt, "stream": False},
            timeout=30
        )
        
        if not resp.ok:
            logger.error(f"[LLM] Error: HTTP {resp.status_code}")
            return None
        
        return resp.json().get("response", "")
        
    except Exception as e:
        logger.error(f"[LLM] Error: {e}")
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
        logger.error(f"[Prometheus] Error fetching from {target_url}: {e}")
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
        logger.error(f"[Email] Error: {e}")
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

# ============ LLM ANALYSIS WITH LANGFUSE ============
async def get_llm_analysis(anomaly: Dict, metrics: List[Dict], anomaly_id: str) -> Dict:
    """Get LLM analysis with Langfuse tracking"""
    
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

    # Call LLM with tracking
    metadata = {
        "anomaly_id": str(anomaly_id),
        "metric": anomaly['metric'],
        "severity": anomaly.get('severity', 'unknown'),
        "instance": anomaly.get('instance', 'unknown')
    }
    
    resp = await asyncio.get_running_loop().run_in_executor(
        None,
        ask_llm,
        prompt,
        f"RCA: {anomaly['metric']}",
        metadata
    )
    
    # Parse response
    parsed = parse_json(resp) if resp else {}
    
 
    return parsed


# ============ MONITORING SESSION TRACKING ============
class MonitoringSession:
    """Track entire monitoring cycle in Langfuse v3"""
    
    def __init__(self, timestamp: str):
        self.timestamp = timestamp
        self.span = None
        self._context = None
        
        if langfuse:
            try:
                # Use context manager for span
                self._context = langfuse.start_as_current_observation(
                    as_type="span",
                    name="Monitoring Cycle",
                    metadata={
                        "timestamp": timestamp,
                        "cycle_type": "scheduled"
                    }
                )
                self.span = self._context.__enter__()
            except Exception as e:
                logger.warning(f"[Langfuse] Could not start monitoring span: {e}")
                self._context = None
                self.span = None
    
    def end(self, metrics_count: int = 0, anomalies_count: int = 0, success: bool = True):
        """End monitoring session"""
        if self.span and self._context:
            try:
                self.span.update(
                    output={
                        "metrics_collected": metrics_count,
                        "anomalies_detected": anomalies_count,
                        "success": success
                    }
                )
                self._context.__exit__(None, None, None)
            except Exception as e:
                logger.warning(f"[Langfuse] Could not end monitoring span: {e}")

#=========adding multithreading++++
def process_single_anomaly(anomaly, metrics):
    logger.info(
    f"[THREAD] name={threading.current_thread().name} "
    f"id={threading.get_ident()} "
    f"metric={anomaly['metric']}"
)

    db = get_db()
    ts = datetime.now().strftime("%H:%M:%S")

    sev = anomaly["severity"].upper()
    logger.error(
        f"[{ts}] ANOMALY [{sev}]: {anomaly['metric']}={anomaly['value']} - {anomaly['reason']}"
    )

    # Save anomaly
    result = db.anomalies.insert_one({
        "timestamp": datetime.utcnow(),
        "metric": anomaly["metric"],
        "value": anomaly["value"],
        "instance": anomaly.get("instance", "unknown"),
        "severity": anomaly["severity"],
        "reason": anomaly["reason"]
    })
    anomaly_id = result.inserted_id

    # LLM analysis (blocking)
    
    future = asyncio.run_coroutine_threadsafe(
      get_llm_analysis(anomaly, metrics, str(anomaly_id)),
      MAIN_EVENT_LOOP
    )

    analysis = future.result() or {}

    logger.info(f"[{ts}] RCA: {analysis.get('cause')} | Fix: {analysis.get('fix')}")

    # Save RCA
    db.rca.insert_one({
        "timestamp": datetime.utcnow(),
        "anomaly_id": anomaly_id,
        "metric": anomaly["metric"],
        "instance": anomaly.get("instance", "unknown"),
        "summary": analysis.get("summary"),
        "simplified": analysis.get("simplified"),
        "cause": analysis.get("cause"),
        "fix": analysis.get("fix")
    })

    # Send email
    body = f"""
    <h2>{sev} Anomaly</h2>
    <p><b>Metric:</b> {anomaly['metric']}</p>
    <p><b>Value:</b> {anomaly['value']}</p>
    <p><b>Reason:</b> {anomaly['reason']}</p>
    """

    send_alert(f"[{sev}] {anomaly['metric']}", body)


# ============ MONITOR LOOP ============
async def monitor():
    logger.info("[Monitor] Starting monitor loop...")
    await asyncio.sleep(2)

    while True:
        ts = datetime.now().strftime("%H:%M:%S")
        session = MonitoringSession(ts)

        try:
            db = get_db()

            # 1. Fetch metrics
            metrics = await fetch_metrics()
            if not metrics:
                logger.info(f"[{ts}] No metrics from Prometheus")
                session.end(metrics_count=0, anomalies_count=0, success=True)
                await asyncio.sleep(MONITOR_INTERVAL)
                continue

            logger.info(f"[{ts}] Fetched {len(metrics)} metrics")

            # 2. Save metrics
            if db is not None:
                await asyncio.get_running_loop().run_in_executor(
                    None,
                    lambda: db.metrics.insert_one({
                        "timestamp": datetime.utcnow(),
                        "count": len(metrics),
                        "data": metrics[:50]
                    })
                )

            # 3. Cleanup
            if db is not None:
                await asyncio.get_running_loop().run_in_executor(None, lambda: cleanup_collection(db, "metrics"))
                await asyncio.get_running_loop().run_in_executor(None, lambda: cleanup_collection(db, "anomalies"))
                await asyncio.get_running_loop().run_in_executor(None, lambda: cleanup_collection(db, "rca"))

            # 4. Detect anomalies
            anomalies = detect_anomalies(metrics)

            if not anomalies:
                logger.info(f"[{ts}] No anomalies")
                session.end(metrics_count=len(metrics), anomalies_count=0, success=True)
                await asyncio.sleep(MONITOR_INTERVAL)
                continue

            # 5. Deduplicate + cap
            seen = set()
            unique_anomalies = []
            for a in anomalies:
                if a["metric"] not in seen:
                    seen.add(a["metric"])
                    unique_anomalies.append(a)
            anomalies = unique_anomalies[:3]

            # 6. MULTITHREADED anomaly processing
            loop = asyncio.get_running_loop()
            tasks = [
                loop.run_in_executor(
                    anomaly_executor,
                    process_single_anomaly,
                    anomaly,
                    metrics
                )
                for anomaly in anomalies
            ]

            await asyncio.gather(*tasks)

            # 7. End monitoring session
            session.end(
                metrics_count=len(metrics),
                anomalies_count=len(anomalies),
                success=True
            )

        except Exception as e:
            logger.error(f"[{ts}] Monitor error: {e}")
            session.end(metrics_count=0, anomalies_count=0, success=False)

        await asyncio.sleep(MONITOR_INTERVAL)

# ============ FASTAPI ============
@asynccontextmanager
async def lifespan(app: FastAPI):
    global MAIN_EVENT_LOOP
    MAIN_EVENT_LOOP = asyncio.get_running_loop()

    logger.info(f"Monitor started | Prometheus: {PROM_URL} | LLM: {LLM_MODEL}")
    logger.info(f"MongoDB URI: {MONGO_URI[:30] if MONGO_URI else 'NOT SET'}...")
    status_msg = " Enabled (v3)" if LANGFUSE_ENABLED else " Disabled"
    if not LANGFUSE_ENABLED:
        status_msg += f" (Module: {LANGFUSE_AVAILABLE}, PK: {bool(LANGFUSE_PUBLIC_KEY)}, SK: {bool(LANGFUSE_SECRET_KEY)})"
    logger.info(f"Langfuse: {status_msg}")

    # Initialize default email config
    db = get_db()
    if db is not None:
        if not db.email_config.find_one({}):
            db.email_config.insert_one({
                "enabled": False,
                "recipients": []
            })
            logger.info("[Email] Initialized default config")

    task = asyncio.create_task(monitor())
    yield
    
    # Shutdown: Flush Langfuse data
    if langfuse:
        try:
            logger.info("[Langfuse] Flushing remaining data...")
            langfuse.flush()
            logger.info("[Langfuse]  Flush complete")
        except Exception as e:
            logger.warning(f"[Langfuse] Flush error: {e}")
    
    task.cancel()
    anomaly_executor.shutdown(wait=False)



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
    return {
        "status": "running",
        "prometheus": PROM_URL,
        "llm": LLM_MODEL,
        "langfuse": "enabled (v3)" if LANGFUSE_ENABLED else "disabled"
    }

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

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage):
    """General AI chat endpoint with Langfuse tracking"""
    context_str = ""
    if message.context:
        # Format context for prompt
        context_lines = ["Context:"]
        for k, v in message.context.items():
            context_lines.append(f"- {k}: {v}")
        context_str = "\n".join(context_lines)

    prompt = f"""You are a helpful DevOps assistant.
User asks: {message.message}

{context_str}

Provide a helpful, concise answer. Explain technical concepts simply if asked."""

    # Call LLM
    response = await asyncio.get_running_loop().run_in_executor(
        None,
        ask_llm,
        prompt,
        "AI Chat",
        {"user_message": message.message, **message.context}
    )

    return {"response": response or "Sorry, I'm having trouble connecting to the AI service."}


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

# ============ LANGFUSE STATUS ENDPOINT ============

@app.get("/langfuse/status")
def get_langfuse_status():
    """Get Langfuse v3 connection status"""
    status = {
        "installed": LANGFUSE_AVAILABLE,
        "enabled": LANGFUSE_ENABLED,
        "version": "v3",
        "host": LANGFUSE_HOST if LANGFUSE_ENABLED else None,
        "connected": False
    }
    
    if langfuse:
        try:
            langfuse.auth_check()
            status["connected"] = True
        except Exception as e:
            status["error"] = str(e)
    
    return status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)