"""
Data Retrieval Routes - FIXED ObjectId serialization error
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from app.services.mongodb_service import get_db

router = APIRouter()


def _iso(d):
    """Convert datetime to ISO string"""
    if isinstance(d, datetime):
        return d.isoformat()
    return d


def _stringify_id(doc: dict, field: str = "_id"):
    if field in doc:
        doc[field] = str(doc[field])
    return doc


@router.get("/stats")
def get_stats():
    """Get statistics - FIXED ObjectId serialization"""
    db = get_db()
    if db is None:
        return {"collections": {}}

    # Get email config safely
    email_config = db.email_config.find_one({}) or {}
    email_enabled = email_config.get("enabled", False)
    email_recipients = len(email_config.get("recipients", []))
    
    # Get slack config safely
    slack_config = db.slack_config.find_one({}) or {}
    slack_enabled = slack_config.get("enabled", False)
    slack_webhook = slack_config.get("webhook_url", "")

    return {
        "collections": {
            "metrics_batches": {"total": db.metrics_batches.count_documents({})},
            "incidents": {"total": db.incidents.count_documents({})},
            "metrics": {"total": db.metrics.count_documents({})},
            "anomalies": {
                "total": db.anomalies.count_documents({}),
                "open": db.anomalies.count_documents({"severity": {"$in": ["critical", "high"]}}),
                "analyzed": db.rca.count_documents({})
            },
            "chat_sessions": {
                "total": db.chat_sessions.count_documents({}),
                "active": db.chat_sessions.count_documents({
                    "last_activity": {"$gte": datetime.utcnow() - timedelta(hours=1)}
                }),
            },
        },
        "notifications": {
            "email": {
                "enabled": email_enabled,
                "recipients": email_recipients
            },
            "slack": {
                "enabled": slack_enabled,
                "configured": bool(slack_webhook)
            }
        }
    }


@router.get("/batches")
def get_batches(limit: int = 10):
    """Get recent metrics batches"""
    db = get_db()
    if db is None:
        return {"batches": []}
    
    docs = list(db.metrics_batches.find().sort("collected_at", -1).limit(max(1, min(limit, 50))))
    for d in docs:
        _stringify_id(d)
        d["collected_at"] = _iso(d.get("collected_at"))
        d["window_start"] = _iso(d.get("window_start"))
        d["window_end"] = _iso(d.get("window_end"))
    
    return {"batches": docs}


@router.get("/incidents")
def get_incidents(limit: int = 20):
    """Get recent incidents"""
    db = get_db()
    if db is None:
        return {"incidents": []}
    
    docs = list(db.incidents.find().sort("created_at", -1).limit(max(1, min(limit, 100))))
    for d in docs:
        _stringify_id(d)
        d["batch_id"] = str(d.get("batch_id")) if d.get("batch_id") is not None else ""
        d["created_at"] = _iso(d.get("created_at"))
        d["timestamp"] = _iso(d.get("timestamp") or d.get("created_at"))
        d["window_start"] = _iso(d.get("window_start"))
        d["window_end"] = _iso(d.get("window_end"))
    
    return {"incidents": docs}


@router.get("/anomalies")
def get_anomalies(limit: int = 50):
    """Get recent anomalies"""
    db = get_db()
    if db is None:
        return {"anomalies": []}
    
    docs = list(db.anomalies.find().sort("created_at", -1).limit(max(1, min(limit, 200))))
    for d in docs:
        _stringify_id(d)
        d["timestamp"] = _iso(d.get("created_at") or d.get("timestamp"))
        if "incident_id" in d:
            d["incident_id"] = str(d.get("incident_id") or "")
        if "batch_id" in d:
            d["batch_id"] = str(d.get("batch_id") or "")
        
        # Ensure severity exists
        if "severity" not in d:
            d["severity"] = "medium"
    
    return {"anomalies": docs}


@router.get("/rca")
def get_rca(limit: int = 20):
    """Get recent RCA docs"""
    db = get_db()
    if db is None:
        return {"rca": []}
    
    docs = list(db.rca.find().sort("timestamp", -1).limit(max(1, min(limit, 100))))
    for d in docs:
        _stringify_id(d)
        d["timestamp"] = _iso(d.get("timestamp"))
        d["batch_id"] = str(d.get("batch_id") or "")
        if "incident_id" in d:
            d["incident_id"] = str(d.get("incident_id") or "")
        d["window_start"] = _iso(d.get("window_start"))
        d["window_end"] = _iso(d.get("window_end"))
    
    return {"rca": docs}


@router.get("/prom-metrics")
def get_prom_metrics():
    """Get recent Prometheus metrics snapshots"""
    db = get_db()
    if db is None:
        return {"metrics": []}
    
    docs = list(db.metrics.find().sort("timestamp", -1).limit(10))
    for d in docs:
        _stringify_id(d)
        d["timestamp"] = _iso(d.get("timestamp"))
    
    return {"metrics": docs}


@router.get("/api/sessions")
def get_sessions():
    """Get all chat sessions"""
    db = get_db()
    if db is None:
        return {"sessions": []}

    sessions = list(db.chat_sessions.find().sort("last_activity", -1).limit(50))
    for s in sessions:
        _stringify_id(s)
        s["created_at"] = _iso(s.get("created_at"))
        s["last_activity"] = _iso(s.get("last_activity"))
    
    return {"sessions": sessions}


@router.get("/api/sessions/{session_id}")
def get_session_details(session_id: str):
    """Get details for a specific session"""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    from app.services.session_service import session_manager
    session = session_manager.get_session(session_id, db)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    _stringify_id(session)
    session["created_at"] = _iso(session.get("created_at"))
    session["last_activity"] = _iso(session.get("last_activity"))
    
    return session


@router.delete("/api/sessions/{session_id}")
def delete_session(session_id: str):
    """Delete a chat session"""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    result = db.chat_sessions.delete_one({"session_id": session_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")

    from app.services.session_service import session_manager
    if session_id in session_manager.active_sessions:
        del session_manager.active_sessions[session_id]

    return {"message": "Session deleted successfully"}