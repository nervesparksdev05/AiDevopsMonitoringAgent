import os
import sys
import uuid
import logging
import logging.config
from datetime import datetime
from typing import Optional, List, Dict, Any

import httpx
from bson import ObjectId
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from prometheus_fastapi_instrumentator import Instrumentator
from pymongo import MongoClient

load_dotenv()

# ---------------- LOGGING ----------------
def build_log_config(app_level: str = "DEBUG") -> Dict[str, Any]:
    """
    A single logging config shared by:
    - app logger ("api")
    - uvicorn.error
    - uvicorn.access (the GET /metrics lines)
    """
    log_level = app_level.upper()

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
            },
            "access": {
                # keeps uvicorn access logs in uvicorn style
                "format": "%(levelprefix)s %(client_addr)s - \"%(request_line)s\" %(status_code)s"
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
            "file_api": {
                "class": "logging.FileHandler",
                "formatter": "default",
                "filename": "api.log",
                "mode": "a",
                "encoding": "utf-8",
            },
            "access_console": {
                "class": "logging.StreamHandler",
                "formatter": "access",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "api": {"handlers": ["console", "file_api"], "level": log_level, "propagate": False},

            # Uvicorn logs
            "uvicorn": {"handlers": ["console", "file_api"], "level": "INFO", "propagate": False},
            "uvicorn.error": {"handlers": ["console", "file_api"], "level": "INFO", "propagate": False},

            # This is what prints: INFO: 127.0.0.1:xxxxx - "GET /metrics HTTP/1.1" 200 OK
            "uvicorn.access": {"handlers": ["access_console"], "level": "INFO", "propagate": False},

            # Noisy libs
            "pymongo": {"handlers": ["console", "file_api"], "level": "WARNING", "propagate": False},
            "httpx": {"handlers": ["console", "file_api"], "level": "INFO", "propagate": False},
        },
        "root": {"handlers": ["console", "file_api"], "level": "INFO"},
    }


APP_LOG_LEVEL = os.getenv("APP_LOG_LEVEL", "DEBUG")
logging.config.dictConfig(build_log_config(APP_LOG_LEVEL))
logger = logging.getLogger("api")

logger.info("=" * 80)
logger.info("🚀 Initializing AI DevOps Monitoring API...")
logger.info("=" * 80)

# ---------------- FASTAPI ----------------
app = FastAPI(
    title="AI DevOps Monitoring API",
    description="API for AI-powered monitoring with configurable targets and email alerts",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- MONGO ----------------
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB", "observability")


def get_db():
    logger.debug(f"Connecting to MongoDB: {DB_NAME}")
    if not MONGO_URI:
        raise RuntimeError("MONGO_URI is not set in environment/.env")

    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return client[DB_NAME]


# ---------------- PROMETHEUS METRICS ----------------
logger.info("✅ Enabling Prometheus instrumentation for FastAPI")
Instrumentator().instrument(app).expose(app)
logger.info("✅ Prometheus metrics endpoint exposed at /metrics")

# ---------------- MODELS ----------------
class Target(BaseModel):
    name: str
    endpoint: str
    job: str
    enabled: bool = True


class EmailConfig(BaseModel):
    enabled: bool
    recipients: List[EmailStr]


# ---------------- ROUTES ----------------
@app.get("/")
def root():
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "service": "AI DevOps Monitoring API - Automated Pipeline",
        "version": "3.0.0",
        "note": "Anomaly detection, RCA, and email alerts are automated via pipeline.py",
        "endpoints": [
            "/metrics",
            "/metrics/prometheus",
            "/anomalies",
            "/rca",
            "/stats",
            "/agent/targets",
            "/agent/email-config",
        ],
    }


@app.get("/metrics/prometheus")
async def get_metrics_from_prometheus(
    query: Optional[str] = Query(
        None,
        description='PromQL query (e.g. up, http_requests_total, or {__name__=~".+"} for all)',
    )
):
    logger.info("📊 Prometheus Metrics Fetch Request Started")
    logger.debug(f"Query: {query}")

    prometheus_url = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
    api_url = f"{prometheus_url}/api/v1/query"

    if not query:
        query = '{__name__=~".+"}'
        logger.info("No query provided, fetching ALL metrics")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(api_url, params={"query": query})
            logger.info(f"📡 Prometheus response: {response.status_code}")
            response.raise_for_status()

            data = response.json()
            if data.get("status") != "success":
                raise HTTPException(status_code=500, detail="Prometheus query failed")

            result = data.get("data", {}).get("result", [])
            logger.info(f"✅ Query successful: {len(result)} series returned")

            formatted = []
            for m in result:
                metric_name = m.get("metric", {}).get("__name__", "unknown")
                labels = m.get("metric", {})
                value_data = m.get("value", [None, None])
                formatted.append(
                    {
                        "metric_name": metric_name,
                        "labels": labels,
                        "value": value_data[1],
                        "timestamp": value_data[0],
                    }
                )

            return {
                "status": "success",
                "prometheus_server": prometheus_url,
                "query": query,
                "metrics_count": len(formatted),
                "metrics": formatted,
            }

    except httpx.ConnectError:
        logger.error("❌ Cannot connect to Prometheus (check localhost:9090)")
        raise HTTPException(status_code=503, detail="Cannot connect to Prometheus at localhost:9090")

    except httpx.TimeoutException:
        logger.error("⏱️ Prometheus request timed out")
        raise HTTPException(status_code=408, detail="Timeout connecting to Prometheus")

    except Exception as e:
        logger.error(f"❌ Error querying Prometheus: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------- AGENT TARGETS ----------------
@app.get("/agent/targets")
def get_targets():
    logger.info("📋 Fetching monitoring targets")
    try:
        db = get_db()
        config = db.agent_config.find_one({"type": "targets"})

        if not config:
            logger.info("No targets found, creating default targets")
            default_targets = [
                {"id": str(uuid.uuid4()), "name": "Prometheus", "endpoint": "localhost:9090", "job": "prometheus", "enabled": True},
                {"id": str(uuid.uuid4()), "name": "FastAPI Backend", "endpoint": "localhost:8000", "job": "fastapi-backend", "enabled": True},
                {"id": str(uuid.uuid4()), "name": "FastAPI Service 2", "endpoint": "localhost:8081", "job": "fastapi-service-2", "enabled": True},
                {"id": str(uuid.uuid4()), "name": "Windows Exporter", "endpoint": "localhost:9182", "job": "windows-exporter", "enabled": True},
            ]
            db.agent_config.insert_one({"type": "targets", "targets": default_targets})
            return {"targets": default_targets}

        return {"targets": config.get("targets", [])}
    except Exception as e:
        logger.error(f"Error fetching targets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/targets")
def add_target(target: Target):
    logger.info(f"➕ Adding new target: {target.name}")
    try:
        db = get_db()

        new_target = {
            "id": str(uuid.uuid4()),
            "name": target.name,
            "endpoint": target.endpoint,
            "job": target.job,
            "enabled": target.enabled,
            "created_at": datetime.utcnow().isoformat(),
        }

        db.agent_config.update_one(
            {"type": "targets"},
            {"$push": {"targets": new_target}},
            upsert=True,
        )

        return {"status": "success", "message": "Target added", "target": new_target}
    except Exception as e:
        logger.error(f"Error adding target: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/agent/targets/{target_id}")
def delete_target(target_id: str):
    logger.info(f"🗑️ Deleting target: {target_id}")
    try:
        db = get_db()
        config = db.agent_config.find_one({"type": "targets"})
        if not config:
            raise HTTPException(status_code=404, detail="No targets configured")

        targets = config.get("targets", [])
        new_targets = [t for t in targets if t.get("id") != target_id]
        if len(new_targets) == len(targets):
            raise HTTPException(status_code=404, detail="Target not found")

        db.agent_config.update_one({"type": "targets"}, {"$set": {"targets": new_targets}})
        return {"status": "success", "message": "Target deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting target: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/agent/targets/{target_id}")
def update_target(target_id: str, enabled: bool):
    logger.info(f"🔄 Updating target {target_id}: enabled={enabled}")
    try:
        db = get_db()
        config = db.agent_config.find_one({"type": "targets"})
        if not config:
            raise HTTPException(status_code=404, detail="No targets configured")

        targets = config.get("targets", [])
        found = False
        for t in targets:
            if t.get("id") == target_id:
                t["enabled"] = enabled
                found = True
                break

        if not found:
            raise HTTPException(status_code=404, detail="Target not found")

        db.agent_config.update_one({"type": "targets"}, {"$set": {"targets": targets}})
        return {"status": "success", "message": f"Target {'enabled' if enabled else 'disabled'}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating target: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------- EMAIL CONFIG ----------------
@app.get("/agent/email-config")
def get_email_config():
    logger.info("📧 Fetching email configuration")
    try:
        db = get_db()
        config = db.agent_config.find_one({"type": "email"})

        if not config:
            return {
                "enabled": os.getenv("SEND_EMAIL_ALERTS", "true").lower() == "true",
                "recipients": [os.getenv("ALERT_EMAIL", "")],
            }

        return {"enabled": config.get("enabled", False), "recipients": config.get("recipients", [])}
    except Exception as e:
        logger.error(f"Error fetching email config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/agent/email-config")
def update_email_config(config: EmailConfig):
    logger.info(f"🔄 Updating email config: enabled={config.enabled}, recipients={len(config.recipients)}")
    try:
        db = get_db()
        db.agent_config.update_one(
            {"type": "email"},
            {"$set": {"enabled": config.enabled, "recipients": [str(r) for r in config.recipients]}},
            upsert=True,
        )
        return {"status": "success", "config": config.dict()}
    except Exception as e:
        logger.error(f"Error updating email config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------- VIEWING ----------------
@app.get("/anomalies")
def get_anomalies(limit: int = Query(10, ge=1, le=100)):
    logger.info(f"📊 Fetching anomalies (limit={limit})")
    try:
        db = get_db()
        docs = list(db.anomalies.find().sort("timestamp", -1).limit(limit))

        for d in docs:
            d["_id"] = str(d["_id"])
            if isinstance(d.get("timestamp"), datetime):
                d["timestamp"] = d["timestamp"].isoformat()

        return {"count": len(docs), "anomalies": docs}
    except Exception as e:
        logger.error(f"Error fetching anomalies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rca")
def get_rca(limit: int = Query(10, ge=1, le=100)):
    logger.info(f"📊 Fetching RCA results (limit={limit})")
    try:
        db = get_db()
        docs = list(db.rca.find().sort("timestamp", -1).limit(limit))

        for d in docs:
            d["_id"] = str(d["_id"])
            if "anomaly_id" in d:
                d["anomaly_id"] = str(d["anomaly_id"])
            if isinstance(d.get("timestamp"), datetime):
                d["timestamp"] = d["timestamp"].isoformat()

        return {"count": len(docs), "rca_results": docs}
    except Exception as e:
        logger.error(f"Error fetching RCA results: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
def get_stats():
    logger.info("📊 Fetching System Statistics")
    try:
        db = get_db()
        total_anomalies = db.anomalies.count_documents({})
        total_rca = db.rca.count_documents({})

        severity_counts = {}
        for sev in ["critical", "high", "medium", "low"]:
            c = db.anomalies.count_documents({"severity": sev})
            if c:
                severity_counts[sev] = c

        recent = db.anomalies.find_one(sort=[("timestamp", -1)])
        last_anomaly_time = None
        if recent and isinstance(recent.get("timestamp"), datetime):
            last_anomaly_time = recent["timestamp"].isoformat()

        return {
            "total_anomalies": total_anomalies,
            "total_rca": total_rca,
            "severity_breakdown": severity_counts,
            "last_anomaly": last_anomaly_time,
            "pipeline_status": "automated",
        }
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------- LIFECYCLE ----------------
@app.on_event("startup")
async def startup_event():
    logger.info("=" * 80)
    logger.info("🚀 FASTAPI SERVER STARTING")
    logger.info(f"   MongoDB DB: {DB_NAME}")
    logger.info("   Metrics endpoint: http://localhost:8000/metrics")
    logger.info("   Prometheus query: http://localhost:8000/metrics/prometheus")
    logger.info("=" * 80)


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("=" * 80)
    logger.info("🛑 FASTAPI SERVER SHUTTING DOWN")
    logger.info("=" * 80)


# ---------------- RUN UVICORN (so you get access logs) ----------------
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn_log_level = os.getenv("UVICORN_LOG_LEVEL", "info").lower()
    reload_dev = os.getenv("RELOAD", "true").lower() == "true"

    # log_config ensures access logs print correctly + your file logger works
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=reload_dev,
        log_level=uvicorn_log_level,
        access_log=True,
        log_config=build_log_config(APP_LOG_LEVEL),
    )
