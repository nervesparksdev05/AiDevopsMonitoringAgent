"""
Target Management Routes
Add/Remove Prometheus scrape targets dynamically.
"""
import json
import os
from typing import List

from fastapi import APIRouter, HTTPException
from app.schemas.target import Target
from app.services.mongodb_service import get_db
from app.core.logging import logger

router = APIRouter()

TARGETS_FILE = "targets.json"

def _regenerate_targets_file(db):
    """Regenerate targets.json from MongoDB"""
    try:
        targets = list(db.targets.find({"enabled": True}))
        
        # Group by job (optional, but good practice) or just flat list
        # For simple file_sd, we usually output a list of target groups
        
        file_sd_content = []
        for t in targets:
            file_sd_content.append({
                "targets": [t["endpoint"]],
                "labels": {
                    "job": "dynamic-targets", 
                    "name": t.get("name", "Unknown"),
                    **(t.get("labels", {}) or {})
                }
            })
            
        # Write to file
        with open(TARGETS_FILE, "w") as f:
            json.dump(file_sd_content, f, indent=2)
            
        logger.info(f"[Targets] Regenerated {TARGETS_FILE} with {len(targets)} targets")
        return True
    except Exception as e:
        logger.error(f"[Targets] Failed to regenerate file: {e}")
        return False


@router.get("/agent/targets", response_model=List[Target])
def get_targets():
    """Get all configured targets"""
    db = get_db()
    if db is None:
        return []
        
    targets = list(db.targets.find({}))
    results = []
    for t in targets:
        results.append(Target(
            name=t.get("name", ""),
            endpoint=t.get("endpoint", ""),
            labels=t.get("labels", {}),
            enabled=t.get("enabled", True)
        ))
    return results


@router.post("/agent/targets")
def add_target(target: Target):
    """Add a new monitoring target"""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=500, detail="Database error")
        
    # Check if exists
    if db.targets.find_one({"endpoint": target.endpoint}):
        raise HTTPException(status_code=400, detail="Target already exists")
        
    db.targets.insert_one(target.dict())
    
    # Regenerate file
    _regenerate_targets_file(db)
    
    return {"message": "Target added and monitoring updated"}


@router.delete("/agent/targets/{endpoint}")
def remove_target(endpoint: str):
    """Remove a target"""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=500, detail="Database error")
        
    res = db.targets.delete_one({"endpoint": endpoint})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Target not found")
        
    # Regenerate file
    _regenerate_targets_file(db)
    
    return {"message": "Target removed"}
