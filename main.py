from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from pymongo import MongoClient
from typing import Optional, List
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Metrics Observability API",
    description="API for querying anomalies, RCA results, and metrics",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB", "observability")

def get_db():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return client[DB_NAME]

# Prometheus metrics endpoint
Instrumentator().instrument(app).expose(app)

# ==================== ENDPOINTS ====================

@app.get("/")
def root():
    """API health check"""
    return {
        "status": "healthy",
        "service": "Metrics Observability API",
        "endpoints": [
            "/metrics",
            "/anomalies",
            "/anomalies/{anomaly_id}",
            "/rca",
            "/rca/{rca_id}",
            "/prom-metrics"
        ]
    }

@app.get("/anomalies")
def get_anomalies(
    severity: Optional[str] = Query(None, description="Filter by severity: critical, high, medium, low"),
    status: Optional[str] = Query(None, description="Filter by status: open, analyzed"),
    limit: int = Query(10, ge=1, le=100, description="Number of results")
):
    """Get list of anomalies with optional filters"""
    try:
        db = get_db()
        query = {}
        
        if severity:
            query["severity"] = severity
        if status:
            query["status"] = status
        
        anomalies = list(db.anomalies.find(query).sort("detected_at", -1).limit(limit))
        
        # Convert ObjectId to string
        for a in anomalies:
            a["_id"] = str(a["_id"])
            if "detected_at" in a:
                a["detected_at"] = a["detected_at"].isoformat()
        
        return {
            "count": len(anomalies),
            "anomalies": anomalies
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/anomalies/{anomaly_id}")
def get_anomaly_by_id(anomaly_id: str):
    """Get specific anomaly by ID"""
    try:
        db = get_db()
        anomaly = db.anomalies.find_one({"anomaly_id": anomaly_id})
        
        if not anomaly:
            raise HTTPException(status_code=404, detail="Anomaly not found")
        
        anomaly["_id"] = str(anomaly["_id"])
        if "detected_at" in anomaly:
            anomaly["detected_at"] = anomaly["detected_at"].isoformat()
        
        return anomaly
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rca")
def get_rca_results(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(10, ge=1, le=100, description="Number of results")
):
    """Get RCA results with optional filters"""
    try:
        db = get_db()
        query = {}
        
        if severity:
            query["severity"] = severity
        
        rca_results = list(db.rca_results.find(query).sort("analyzed_at", -1).limit(limit))
        
        for r in rca_results:
            r["_id"] = str(r["_id"])
            if "analyzed_at" in r:
                r["analyzed_at"] = r["analyzed_at"].isoformat()
        
        return {
            "count": len(rca_results),
            "rca_results": rca_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rca/{rca_id}")
def get_rca_by_id(rca_id: str):
    """Get specific RCA by ID"""
    try:
        db = get_db()
        rca = db.rca_results.find_one({"rca_id": rca_id})
        
        if not rca:
            raise HTTPException(status_code=404, detail="RCA not found")
        
        rca["_id"] = str(rca["_id"])
        if "analyzed_at" in rca:
            rca["analyzed_at"] = rca["analyzed_at"].isoformat()
        
        return rca
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/prom-metrics")
def get_prom_metrics(
    metric: Optional[str] = Query(None, description="Filter by metric name"),
    instance: Optional[str] = Query(None, description="Filter by instance"),
    limit: int = Query(20, ge=1, le=100, description="Number of results")
):
    """Get Prometheus metrics rollup data"""
    try:
        db = get_db()
        query = {}
        
        if metric:
            query["metric"] = metric
        if instance:
            query["instance"] = instance
        
        metrics = list(db.prom_rollup_1m.find(query).sort("ts", -1).limit(limit))
        
        for m in metrics:
            m["_id"] = str(m["_id"])
            if "ts" in m:
                m["ts"] = m["ts"].isoformat()
        
        return {
            "count": len(metrics),
            "metrics": metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
def get_stats():
    """Get database statistics"""
    try:
        db = get_db()
        
        return {
            "collections": {
                "anomalies": {
                    "total": db.anomalies.count_documents({}),
                    "open": db.anomalies.count_documents({"status": "open"}),
                    "analyzed": db.anomalies.count_documents({"status": "analyzed"})
                },
                "rca_results": {
                    "total": db.rca_results.count_documents({})
                },
                "prom_rollup_1m": {
                    "total": db.prom_rollup_1m.count_documents({})
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
