import asyncio
import os
import json
import uvicorn
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import PROM_URL, LLM_MODEL, BATCH_INTERVAL_MINUTES, MONGO_URI
from app.core.logging import logger
from app.core.time import now_ist, ist_to_utc, format_ist
from app.core.helpers import parse_json

from app.services.langfuse_service import (
    initialize_langfuse, flush_langfuse, is_langfuse_enabled, 
    get_langfuse_client, make_batch_session_id, make_batch_window
)
from app.services.slack_service import send_slack_alert_text, slack_is_configured
from app.services.email_service import send_alert
from app.services.mongodb_service import get_db
from app.services.prometheus_service import fetch_metrics
from app.services.llm_service import ask_llm
from app.services.session_service import session_manager

from app.api.router import api_router

try:
    from langfuse import propagate_attributes
except ImportError:
    propagate_attributes = None

class BatchMonitor:
    """Handles batch metric analysis with LLM-based anomaly detection"""
    
    def __init__(self, interval_minutes: int = BATCH_INTERVAL_MINUTES):
        self.interval = interval_minutes
        self.max_metrics = int(os.getenv("BATCH_MAX_METRICS", "600"))
        self._task: Optional[asyncio.Task] = None
    
    def get_window(self) -> Tuple[datetime, datetime]:
        """Calculate current batch window in IST"""
        current_ist = now_ist()
        # Convert to UTC for make_batch_window compatibility
        current_utc = ist_to_utc(current_ist)
        start_utc, end_utc = make_batch_window(current_utc.replace(tzinfo=None), self.interval)
        # Convert back to IST
        return (
            start_utc.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=5, minutes=30))),
            end_utc.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=5, minutes=30)))
        )
    
    def get_session_id(self, window_start: datetime) -> str:
        """Generate Langfuse session ID for batch"""
        # Convert to naive UTC for compatibility
        utc_start = ist_to_utc(window_start).replace(tzinfo=None)
        return make_batch_session_id(utc_start, self.interval, "batch")
    
    def is_processed(self, db, start: datetime, end: datetime) -> bool:
        """Check if window already processed"""
        if db is None:
            return False
        # Store as UTC for consistency
        start_utc = ist_to_utc(start).replace(tzinfo=None)
        end_utc = ist_to_utc(end).replace(tzinfo=None)
        return db.alert_windows.find_one({"window_start": start_utc, "window_end": end_utc}) is not None
    
    def mark_processed(self, db, start: datetime, end: datetime, session_id: str, incident_id: Any):
        """Mark window as processed"""
        if db is None:
            return
        # Store as UTC for consistency
        start_utc = ist_to_utc(start).replace(tzinfo=None)
        end_utc = ist_to_utc(end).replace(tzinfo=None)
        db.alert_windows.update_one(
            {"window_start": start_utc, "window_end": end_utc},
            {"$set": {
                "window_start": start_utc, "window_end": end_utc,
                "processed_at": datetime.utcnow(),
                "langfuse_session_id": session_id,
                "incident_id": incident_id,
            }},
            upsert=True
        )
    
    def build_prompt(self, metrics: List[Dict], start: datetime, end: datetime) -> str:
        """Build LLM analysis prompt with IST times"""
        # Group metrics by instance
        grouped: Dict[str, List[Dict]] = {}
        for m in metrics:
            inst = m.get("instance", "unknown")
            grouped.setdefault(inst, []).append(m)
        
        # Build metrics text (capped)
        lines, total = [], 0
        for inst, inst_metrics in sorted(grouped.items()):
            lines.append(f"\n### Instance: {inst}")
            for m in sorted(inst_metrics, key=lambda x: x.get("name", ""))[:200]:
                if total >= self.max_metrics:
                    break
                lines.append(f"  {m['name']}: {m['value']}")
                total += 1
            if total >= self.max_metrics:
                lines.append(f"\n  ... (capped at {self.max_metrics})")
                break
        
        schema = {
            "incident": {
                "title": "string", "severity": "low|medium|high|critical",
                "confidence": 0.0, "summary": "string", "root_cause": "string",
                "contributing_factors": [], "blast_radius": "string",
                "evidence": [{"metric": "", "instance": "", "value": 0, "why_it_matters": ""}],
                "fix_plan": {"immediate": [], "next_24h": [], "prevention": []}
            },
            "anomalies": [{"metric": "", "instance": "", "observed": 0, "expected": "", "symptom": "", "cluster": ""}],
            "clusters": [{"name": "", "theme": "", "anomaly_indexes": []}]
        }
        
        # Format times in IST
        start_str = format_ist(start, include_tz=True)
        end_str = format_ist(end, include_tz=True)
        
        return f"""You are an expert SRE analyzing Prometheus metrics.

BATCH WINDOW (IST): {start_str} -> {end_str} ({self.interval} min)

TASKS:
1. Detect anomalies (spikes, drops, errors, high resource usage)
2. Cluster related anomalies by root cause
3. Provide collective RCA with evidence
4. Return ONLY valid JSON (no markdown)

METRICS ({total}/{len(metrics)} included):
{"".join(lines)}

SCHEMA:
{json.dumps(schema, indent=2)}

RETURN ONLY JSON:"""

    async def call_llm(self, prompt: str, session_id: str, metadata: Dict) -> Dict:
        """Call LLM for batch analysis"""
        result = await asyncio.get_event_loop().run_in_executor(
            None, ask_llm, prompt, "Batch Collective RCA", metadata, session_id
        )
        if not result:
            return {}
        text, _ = result
        return parse_json(text) if text else {}
    
    def store_results(self, db, start: datetime, end: datetime, session_id: str,
                      metrics: List[Dict], analysis: Dict) -> Tuple[Any, Any]:
        """Store batch results in MongoDB with UTC times"""
        if db is None:
            return None, None
        
        # Convert to UTC for storage
        start_utc = ist_to_utc(start).replace(tzinfo=None)
        end_utc = ist_to_utc(end).replace(tzinfo=None)
        
        batch_id = incident_id = None
        try:
            # Store metrics batch
            batch_id = db.metrics_batches.insert_one({
                "window_start": start_utc, "window_end": end_utc,
                "collected_at": datetime.utcnow(),
                "metrics_count": len(metrics), "metrics": metrics,
                "langfuse_session_id": session_id,
            }).inserted_id
            
            # Store incident
            inc = analysis.get("incident", {})
            incident_id = db.incidents.insert_one({
                "created_at": datetime.utcnow(),
                "window_start": start_utc, "window_end": end_utc, "batch_id": batch_id,
                "title": inc.get("title", "Batch Analysis"),
                "severity": inc.get("severity", "low"),
                "confidence": float(inc.get("confidence", 0)),
                "summary": inc.get("summary", ""),
                "root_cause": inc.get("root_cause", ""),
                "contributing_factors": inc.get("contributing_factors", []),
                "blast_radius": inc.get("blast_radius", ""),
                "evidence": inc.get("evidence", []),
                "fix_plan": inc.get("fix_plan", {}),
                "clusters": analysis.get("clusters", []),
                "langfuse_session_id": session_id,
                "raw_analysis": analysis,
            }).inserted_id
            
            # Store anomalies
            anomalies = analysis.get("anomalies", [])
            if anomalies:
                db.anomalies.insert_many([{
                    "created_at": datetime.utcnow(),
                    "window_start": start_utc, "window_end": end_utc,
                    "batch_id": batch_id, "incident_id": incident_id,
                    "metric": a.get("metric"), "instance": a.get("instance", "unknown"),
                    "observed": a.get("observed"), "expected": a.get("expected"),
                    "symptom": a.get("symptom"), "cluster": a.get("cluster"),
                    "langfuse_session_id": session_id,
                } for a in anomalies])
            
            # Store RCA (backward compat)
            db.rca.insert_one({
                "timestamp": datetime.utcnow(),
                "window_start": start_utc, "window_end": end_utc,
                "batch_id": batch_id, "incident_id": incident_id,
                "summary": inc.get("summary"), "cause": inc.get("root_cause"),
                "fix": inc.get("fix_plan", {}).get("immediate", []),
                "langfuse_session_id": session_id, "raw": analysis,
            })
            
            logger.info(f"[Batch] Stored: batch={batch_id}, incident={incident_id}, anomalies={len(anomalies)}")
        except Exception as e:
            logger.error(f"[Batch] Storage error: {e}")
        
        return batch_id, incident_id
    
    def send_alerts(self, incident: Dict, anomalies: List, start: datetime, end: datetime, session_id: str):
        """Send Slack and Email alerts with IST times"""
        sev = incident.get("severity", "low").upper()
        title = incident.get("title", "Batch Analysis")
        # Format window in IST
        window = f"{start.strftime('%Y-%m-%d %H:%M')} -> {end.strftime('%H:%M')} IST"
        immediate = incident.get("fix_plan", {}).get("immediate", [])
        
        # Slack
        if slack_is_configured():
            msg = f"""🚨 [{sev}] {title}
📅 Window: {window}
📋 {incident.get('summary', '')}
🔍 Root Cause: {incident.get('root_cause', 'Unknown')}
💥 Blast Radius: {incident.get('blast_radius', 'Unknown')}
⚡ Actions: {', '.join(immediate) or 'None'}
📊 Anomalies: {len(anomalies)}
🔗 Session: {session_id}"""
            try:
                send_slack_alert_text(msg)
            except Exception as e:
                logger.error(f"[Alerts] Slack error: {e}")
        
        # Email
        try:
            html = f"""<h2>🚨 [{sev}] {title}</h2>
<p><b>Window:</b> {window}</p>
<p><b>Summary:</b> {incident.get('summary', '')}</p>
<p><b>Root Cause:</b> {incident.get('root_cause', '')}</p>
<p><b>Blast Radius:</b> {incident.get('blast_radius', '')}</p>
<p><b>Immediate Actions:</b></p><ul>{''.join(f'<li>{a}</li>' for a in immediate) or '<li>None</li>'}</ul>
<p><b>Anomalies:</b> {len(anomalies)} | <b>Confidence:</b> {incident.get('confidence', 0):.0%}</p>"""
            send_alert(f"[{sev}] {title}", html)
        except Exception as e:
            logger.error(f"[Alerts] Email error: {e}")
    
    async def run_once(self):
        """Execute single batch analysis with IST logging"""
        start, end = self.get_window()
        session_id = self.get_session_id(start)
        window_str = f"{start.strftime('%H:%M')}->{end.strftime('%H:%M')} IST"
        
        logger.info(f"[Batch] Running: {window_str} | Session: {session_id}")
        
        db = get_db()
        if self.is_processed(db, start, end):
            logger.info(f"[Batch] Already processed - skipping")
            return
        
        # Langfuse span setup
        langfuse = get_langfuse_client()
        span_ctx = prop_ctx = None
        
        if langfuse and is_langfuse_enabled():
            try:
                span_ctx = langfuse.start_as_current_observation(
                    as_type="span", name="Batch Monitoring",
                    metadata={
                        "window_start": start.isoformat(),
                        "window_end": end.isoformat(),
                        "timezone": "IST"
                    }
                )
                span_ctx.__enter__()
                if propagate_attributes:
                    prop_ctx = propagate_attributes(session_id=session_id)
                    prop_ctx.__enter__()
            except Exception as e:
                logger.warning(f"[Langfuse] Span error: {e}")
        
        try:
            # Fetch metrics
            metrics = await fetch_metrics()
            if not metrics:
                logger.warning("[Batch] No metrics - skipping")
                return
            
            logger.info(f"[Batch] Fetched {len(metrics)} metrics")
            
            # LLM analysis
            analysis = await self.call_llm(
                self.build_prompt(metrics, start, end),
                session_id,
                {
                    "window_start": start.isoformat(),
                    "window_end": end.isoformat(),
                    "metrics_count": len(metrics),
                    "timezone": "IST"
                }
            )
            
            if not analysis:
                logger.error("[Batch] LLM analysis failed")
                return
            
            incident = analysis.get("incident", {})
            anomalies = analysis.get("anomalies", [])
            
            logger.info(f"[Batch] Result: {incident.get('title')} | {incident.get('severity')} | {len(anomalies)} anomalies")
            
            # Store & alert
            _, incident_id = self.store_results(db, start, end, session_id, metrics, analysis)
            self.send_alerts(incident, anomalies, start, end, session_id)
            self.mark_processed(db, start, end, session_id, incident_id)
            
        finally:
            if prop_ctx:
                try: prop_ctx.__exit__(None, None, None)
                except: pass
            if span_ctx:
                try: span_ctx.__exit__(None, None, None)
                except: pass
        
        logger.info(f"[Batch] Complete: {window_str}")
    
    async def run_loop(self):
        """Continuous batch monitoring loop with IST scheduling"""
        logger.info(f"[Batch] Monitor started (every {self.interval} min)")
        
        while True:
            try:
                # Calculate next run time in IST
                now = now_ist()
                bucket = (now.minute // self.interval) * self.interval
                next_run = now.replace(minute=bucket, second=0, microsecond=0)
                if now >= next_run:
                    next_run += timedelta(minutes=self.interval)
                
                sleep_sec = (next_run - now).total_seconds()
                if sleep_sec > 0:
                    logger.info(f"[Batch] Next run: {next_run.strftime('%H:%M:%S')} IST ({sleep_sec:.0f}s)")
                    await asyncio.sleep(sleep_sec)
                
                await self.run_once()
                
            except asyncio.CancelledError:
                logger.info("[Batch] Monitor stopped")
                break
            except Exception as e:
                logger.error(f"[Batch] Error: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait before retry
    
    def start(self) -> asyncio.Task:
        """Start background monitor task"""
        self._task = asyncio.create_task(self.run_loop())
        return self._task
    
    async def stop(self):
        """Stop monitor task"""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass


batch_monitor = BatchMonitor()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    logger.info("=" * 60)
    logger.info("[Startup] AI DevOps Monitor v2.0")
    logger.info(f"[Config] Timezone: IST (UTC+5:30)")
    logger.info(f"[Config] Current Time: {format_ist(now_ist())}")
    logger.info(f"[Config] Prometheus: {PROM_URL or 'NOT SET'}")
    logger.info(f"[Config] LLM: {LLM_MODEL}")
    logger.info(f"[Config] MongoDB: {MONGO_URI[:30] if MONGO_URI else 'NOT SET'}...")
    logger.info(f"[Config] Batch Interval: {BATCH_INTERVAL_MINUTES} min")
    
    # Initialize services
    initialize_langfuse()
    logger.info(f"[Langfuse] {'✅ Enabled' if is_langfuse_enabled() else '❌ Disabled'}")
    logger.info(f"[Slack] {'✅ Enabled' if slack_is_configured() else '❌ Disabled'}")
    
    # Initialize database indexes
    db = get_db()
    if db is not None:
        try:
            # Email config
            if not db.email_config.find_one({}):
                db.email_config.insert_one({"enabled": False, "recipients": []})
            
            # Indexes
            db.chat_sessions.create_index("session_id", unique=True)
            db.chat_sessions.create_index("last_activity")
            db.metrics_batches.create_index([("window_start", -1), ("window_end", -1)])
            db.incidents.create_index([("window_start", -1), ("severity", 1)])
            db.anomalies.create_index([("window_start", -1), ("instance", 1)])
            db.alert_windows.create_index([("window_start", 1), ("window_end", 1)], unique=True)
            logger.info("[Database] Indexes created")
        except Exception as e:
            logger.warning(f"[Database] Index warning: {e}")
    
    # Start background tasks
    batch_monitor.start()
    
    async def cleanup_sessions():
        """Cleanup old chat sessions hourly"""
        while True:
            await asyncio.sleep(3600)
            cleanup_db = get_db()
            if cleanup_db is not None:
                session_manager.cleanup_old_sessions(cleanup_db, hours=720)
    
    cleanup_task = asyncio.create_task(cleanup_sessions())
    
    logger.info("[Startup] ✅ Ready")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("[Shutdown] Stopping services...")
    await batch_monitor.stop()
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    logger.info("[Shutdown] ✅ Complete")

app = FastAPI(
    title="AI DevOps Monitor",
    description="Intelligent monitoring with LLM-based anomaly detection and AI-powered RCA (IST Timezone)",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)

# Centralized Router
app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)