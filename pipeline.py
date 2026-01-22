import os
import sys
import time
import json
import threading
import logging
import logging.config
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import requests
from pymongo import MongoClient
from bson import ObjectId

from config import (
    PROM_URL, MONGO_URI, DB_NAME,
    LLM_URL, LLM_MODEL,
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD,
    ALERT_EMAIL, SEND_EMAIL_ALERTS
)

# ---------------- LOGGING ----------------
def build_pipeline_log_config(level: str = "DEBUG"):
    level = level.upper()
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
            }
        },
        "handlers": {
            "console": {"class": "logging.StreamHandler", "formatter": "default", "stream": "ext://sys.stdout"},
            "file": {"class": "logging.FileHandler", "formatter": "default", "filename": "pipeline.log", "mode": "a", "encoding": "utf-8"},
        },
        "loggers": {
            "pipeline": {"handlers": ["console", "file"], "level": level, "propagate": False},
            "pymongo": {"handlers": ["console", "file"], "level": "WARNING", "propagate": False},
            "urllib3": {"handlers": ["console", "file"], "level": "WARNING", "propagate": False},
        },
        "root": {"handlers": ["console", "file"], "level": "INFO"},
    }

PIPELINE_LOG_LEVEL = os.getenv("PIPELINE_LOG_LEVEL", "DEBUG")
logging.config.dictConfig(build_pipeline_log_config(PIPELINE_LOG_LEVEL))
logger = logging.getLogger("pipeline")


# ---------------- HELPERS ----------------
def get_db():
    logger.debug(f"Connecting to MongoDB: {DB_NAME}")
    if not MONGO_URI:
        raise RuntimeError("MONGO_URI is missing in config/.env")
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return client[DB_NAME]


def keep_latest_n(db, collection: str, n: int = 100, sort_field: str = "timestamp"):
    """
    Keep only latest N documents (delete older).
    This stops MongoDB from growing forever.
    """
    try:
        col = db[collection]
        total = col.count_documents({})
        if total <= n:
            return

        # find docs older than the newest N
        cursor = col.find({}, {"_id": 1}).sort(sort_field, -1).skip(n)
        old_ids = [d["_id"] for d in cursor]
        if old_ids:
            result = col.delete_many({"_id": {"$in": old_ids}})
            logger.info(f"🧹 Retention: deleted {result.deleted_count} old docs from '{collection}' (kept latest {n})")
    except Exception as e:
        logger.warning(f"Retention cleanup failed for {collection}: {e}", exc_info=True)


def call_llm(prompt: str):
    """Call local Ollama LLM"""
    logger.info("🤖 Calling LLM")
    logger.debug(f"LLM URL: {LLM_URL}, Model: {LLM_MODEL}, Prompt length: {len(prompt)}")

    try:
        resp = requests.post(
            f"{LLM_URL}/api/generate",
            headers={"Content-Type": "application/json"},
            json={"model": LLM_MODEL, "prompt": prompt, "stream": False},
            timeout=120
        )
        logger.debug(f"LLM response status: {resp.status_code}")
        resp.raise_for_status()
        out = resp.json().get("response", "")
        logger.debug(f"LLM response preview: {out[:200]}...")
        return out
    except requests.exceptions.Timeout:
        logger.error("⏱️ LLM request timed out")
        return None
    except requests.exceptions.ConnectionError as e:
        logger.error(f"❌ Cannot connect to LLM at {LLM_URL}: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ LLM error: {e}", exc_info=True)
        return None


def fetch_prometheus_metrics():
    """Fetch and filter Prometheus metrics"""
    logger.info("📊 Fetching Prometheus metrics")
    logger.debug(f"Prometheus URL: {PROM_URL}")

    try:
        query = '{__name__=~".+"}'
        r = requests.get(f"{PROM_URL}/api/v1/query", params={"query": query}, timeout=30)
        logger.debug(f"Prometheus response: {r.status_code}")
        r.raise_for_status()

        result = r.json().get("data", {}).get("result", [])
        logger.info(f"📥 Raw series received: {len(result)}")

        filtered = []
        for m in result:
            name = m.get("metric", {}).get("__name__", "")
            if name.startswith(("prometheus_", "go_", "scrape_")):
                continue

            value = m.get("value", [None, None])[1]
            if value is None:
                continue

            filtered.append({
                "name": name,
                "value": value,
                "instance": m.get("metric", {}).get("instance", "unknown"),
                "job": m.get("metric", {}).get("job", "unknown"),
            })

        # keep top 30 for LLM context
        filtered = filtered[:30]
        logger.info(f"✅ Selected metrics for analysis: {len(filtered)}")
        logger.debug("Metrics sample: " + ", ".join([x["name"] for x in filtered[:10]]))
        return filtered

    except requests.exceptions.Timeout:
        logger.error("⏱️ Prometheus request timed out")
        return []
    except requests.exceptions.ConnectionError as e:
        logger.error(f"❌ Cannot connect to Prometheus at {PROM_URL}: {e}")
        return []
    except Exception as e:
        logger.error(f"❌ Prometheus fetch error: {e}", exc_info=True)
        return []


def send_email_alert(subject: str, body_html: str):
    logger.info("📧 Attempting to send email alert")

    try:
        db = get_db()
        email_config = db.agent_config.find_one({"type": "email"})

        if not email_config or not email_config.get("enabled", False):
            logger.info("📧 Email disabled (agent_config.type=email)")
            return False

        recipients = email_config.get("recipients", [])
        if not recipients and ALERT_EMAIL:
            recipients = [ALERT_EMAIL]

        if not recipients:
            logger.info("📧 No recipients configured")
            return False

        if not SMTP_USER or not SMTP_PASSWORD:
            logger.error("❌ SMTP credentials not configured")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = ", ".join(recipients)

        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif;">
            <h2 style="color:#d32f2f;">🚨 Anomaly Alert</h2>
            <div style="background:#f5f5f5;padding:12px;border-radius:6px;">
              {body_html}
            </div>
            <hr>
            <p style="color:#777;font-size:12px;">Generated by AI DevOps Monitoring Agent</p>
          </body>
        </html>
        """
        msg.attach(MIMEText(html, "html"))

        logger.debug(f"SMTP: {SMTP_HOST}:{SMTP_PORT}, Recipients: {recipients}")

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"✅ Email sent to {len(recipients)} recipient(s)")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("❌ SMTP authentication failed")
        return False
    except Exception as e:
        logger.error(f"❌ Email error: {e}", exc_info=True)
        return False


# ---------------- PIPELINE ----------------
def automated_anomaly_pipeline(stop_event: threading.Event):
    logger.info("=" * 80)
    logger.info("🚀 AUTOMATED PIPELINE STARTED")
    logger.info("=" * 80)

    db = get_db()
    iteration = 0

    while not stop_event.is_set():
        iteration += 1
        logger.info("=" * 80)
        logger.info(f"🔄 ITERATION #{iteration}")
        logger.info("=" * 80)

        try:
            # 1) fetch metrics
            metrics = fetch_prometheus_metrics()
            if not metrics:
                logger.info("No metrics fetched. Sleeping 30s...")
                time.sleep(30)
                continue

            metrics_text = "\n".join([f"- {m['name']} ({m['instance']}): {m['value']}" for m in metrics])

            # 2) anomaly detection
            anomaly_prompt = f"""Analyze these Prometheus metrics and identify if there are any anomalies.

Metrics:
{metrics_text}

Look for unusual spikes, drops, high memory/CPU usage, or performance issues.

If you find an anomaly, respond with ONLY a JSON object:
{{"is_anomaly": true, "metric_name": "name", "value": value, "description": "one-line description", "severity": "critical/high/medium/low"}}

If NO anomaly, respond with:
{{"is_anomaly": false}}

Respond with ONLY the JSON, no other text."""
            logger.info("🧠 LLM anomaly detection started")
            llm_response = call_llm(anomaly_prompt)

            if not llm_response:
                logger.info("LLM unavailable. Sleeping 30s...")
                time.sleep(30)
                continue

            anomaly_result = {"is_anomaly": False}
            try:
                start = llm_response.find("{")
                end = llm_response.rfind("}") + 1
                if start != -1 and end > start:
                    anomaly_result = json.loads(llm_response[start:end])
                logger.debug(f"Anomaly JSON: {anomaly_result}")
            except Exception as e:
                logger.warning(f"Anomaly JSON parse failed: {e}")
                anomaly_result = {"is_anomaly": False}

            if not anomaly_result.get("is_anomaly"):
                logger.info("✅ No anomalies detected. Sleeping 30s...")
                time.sleep(30)
                continue

            # 3) save anomaly
            logger.info("⚠️ ANOMALY DETECTED")
            logger.info(f"   Metric: {anomaly_result.get('metric_name')}")
            logger.info(f"   Value: {anomaly_result.get('value')}")
            logger.info(f"   Severity: {str(anomaly_result.get('severity', 'medium')).upper()}")
            logger.debug(f"   Description: {anomaly_result.get('description')}")

            anomaly_doc = {
                "timestamp": datetime.utcnow(),
                "metric_name": anomaly_result.get("metric_name", "unknown"),
                "value": anomaly_result.get("value", 0),
                "description": anomaly_result.get("description", "Anomaly detected"),
                "severity": anomaly_result.get("severity", "medium"),
            }
            res = db.anomalies.insert_one(anomaly_doc)
            anomaly_id = res.inserted_id
            logger.info(f"💾 Saved anomaly: {anomaly_id}")

            keep_latest_n(db, "anomalies", n=100, sort_field="timestamp")

            # 4) RCA
            rca_prompt = f"""Analyze this system anomaly and provide root cause analysis.

Anomaly Details:
- Metric: {anomaly_doc['metric_name']}
- Value: {anomaly_doc['value']}
- Description: {anomaly_doc['description']}
- Severity: {anomaly_doc['severity']}

Provide detailed root cause analysis and actionable recommendation.

Respond with ONLY a JSON object:
{{"root_cause": "detailed explanation", "recommendation": "specific actionable steps"}}

Respond with ONLY the JSON, no other text."""
            logger.info("🔍 LLM RCA generation started")
            rca_response = call_llm(rca_prompt)

            rca_result = {"root_cause": "Unable to generate RCA", "recommendation": "Investigate manually"}
            try:
                if rca_response:
                    start = rca_response.find("{")
                    end = rca_response.rfind("}") + 1
                    if start != -1 and end > start:
                        rca_result = json.loads(rca_response[start:end])
                logger.debug(f"RCA JSON: {rca_result}")
            except Exception as e:
                logger.warning(f"RCA JSON parse failed: {e}")

            rca_doc = {
                "anomaly_id": anomaly_id,
                "timestamp": datetime.utcnow(),
                "root_cause": rca_result.get("root_cause", "Unknown"),
                "recommendation": rca_result.get("recommendation", "Investigate"),
            }
            db.rca.insert_one(rca_doc)
            logger.info("💾 Saved RCA")

            keep_latest_n(db, "rca", n=100, sort_field="timestamp")

            # 5) email
            if SEND_EMAIL_ALERTS:
                logger.info("📧 Sending email alert (if enabled in agent_config)")
                email_subject = f"🚨 {str(anomaly_doc['severity']).upper()} Anomaly: {anomaly_doc['metric_name']}"
                email_body = f"""
                <h3>Anomaly</h3>
                <ul>
                  <li><b>Metric:</b> {anomaly_doc['metric_name']}</li>
                  <li><b>Value:</b> {anomaly_doc['value']}</li>
                  <li><b>Severity:</b> {str(anomaly_doc['severity']).upper()}</li>
                  <li><b>Description:</b> {anomaly_doc['description']}</li>
                </ul>
                <h3>Root Cause</h3>
                <p>{rca_doc['root_cause']}</p>
                <h3>Recommendation</h3>
                <p><b>{rca_doc['recommendation']}</b></p>
                """
                sent = send_email_alert(email_subject, email_body)
                logger.info(f"📧 Email status: {'SENT' if sent else 'NOT SENT'}")
            else:
                logger.info("📧 SEND_EMAIL_ALERTS=false (skipping email step)")

            logger.info("✅ PIPELINE COMPLETE (Prometheus → Anomaly → RCA → Email)")
        except Exception as e:
            logger.error(f"❌ PIPELINE ERROR: {e}", exc_info=True)

        logger.info("⏸️ Sleeping 30 seconds...")
        time.sleep(30)


def main():
    logger.info("=" * 80)
    logger.info("🚀 AI DEVOPS MONITORING PIPELINE")
    logger.info("=" * 80)
    logger.info(f"📡 Prometheus: {PROM_URL}")
    logger.info(f"🗄️  MongoDB: {DB_NAME}")
    logger.info(f"🤖 LLM: {LLM_MODEL} at {LLM_URL}")
    logger.info(f"📧 Email flag: {'Enabled' if SEND_EMAIL_ALERTS else 'Disabled'}")
    logger.info("=" * 80)

    stop = threading.Event()
    t = threading.Thread(target=automated_anomaly_pipeline, args=(stop,), daemon=True)
    t.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 Shutdown requested")
        stop.set()
        t.join(timeout=5)
        logger.info("✅ Pipeline stopped")


if __name__ == "__main__":
    main()
