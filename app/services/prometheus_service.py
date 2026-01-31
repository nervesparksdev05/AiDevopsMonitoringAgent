"""
Prometheus Service - Auto-Discovery from Prometheus Targets
Automatically fetches metrics from ALL targets configured in Prometheus
"""
from typing import List, Dict, Optional
import httpx
from app.core.config import PROM_URL
from app.core.logging import logger


async def get_active_targets() -> List[str]:
    """
    Fetch all active target jobs from Prometheus.
    This automatically discovers whatever you configured in prometheus.yml
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Query Prometheus targets API
            resp = await client.get(f"{PROM_URL}/api/v1/targets")
            resp.raise_for_status()
            data = resp.json()
            
            if data.get("status") != "success":
                logger.warning(f"[Prometheus] Targets API failed: {data.get('error', 'unknown')}")
                return []
            
            # Extract unique job names from active targets
            targets = data.get("data", {}).get("activeTargets", [])
            jobs = set()
            
            for target in targets:
                # Only include targets that are UP
                if target.get("health") == "up":
                    job = target.get("labels", {}).get("job")
                    if job:
                        jobs.add(job)
                        logger.debug(f"[Prometheus] Found active job: {job}")
            
            job_list = list(jobs)
            logger.info(f"[Prometheus] Discovered {len(job_list)} active jobs: {job_list}")
            return job_list
            
    except Exception as e:
        logger.error(f"[Prometheus] Error fetching targets: {e}")
        return []


async def fetch_metrics_from_prom(query: str) -> List[Dict]:
    """Execute a PromQL query against Prometheus"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{PROM_URL}/api/v1/query",
                params={"query": query},
            )
            resp.raise_for_status()
            data = resp.json()

            if data.get("status") != "success":
                logger.warning(f"[Prometheus] Query failed: {data.get('error', 'unknown')}")
                return []

            results = data.get("data", {}).get("result", [])
            
            metrics = []
            for m in results:
                name = m.get("metric", {}).get("__name__", "")
                
                # Skip Prometheus internal metrics
                if name.startswith(("prometheus_", "go_", "scrape_", "promhttp_")):
                    continue
                
                # Extract value
                val = m.get("value", [None, None])[1]
                
                # Extract instance
                instance = m.get("metric", {}).get("instance", "unknown")
                
                # Extract user_id (important for multi-user)
                user_id = m.get("metric", {}).get("user_id", "unknown")
                
                if val is not None and val != "":
                    try:
                        metrics.append({
                            "name": name,
                            "value": float(val),
                            "instance": instance,
                            "user_id": user_id
                        })
                    except Exception:
                        metrics.append({
                            "name": name,
                            "value": val,
                            "instance": instance,
                            "user_id": user_id
                        })
            
            return metrics
            
    except Exception as e:
        logger.error(f"[Prometheus] Error querying {PROM_URL}: {e}")
        return []


async def fetch_metrics() -> List[Dict]:
    """
    Auto-discover and fetch metrics from ALL active Prometheus targets.
    No manual configuration needed - just add targets to prometheus.yml!
    """
    # Step 1: Get all active jobs from Prometheus
    active_jobs = await get_active_targets()
    
    if not active_jobs:
        logger.warning("[Prometheus] No active targets found, falling back to default queries")
        # Fallback to default queries if target discovery fails
        active_jobs = ["fastapi", "dynamic-targets"]
    
    all_metrics = []
    
    # Step 2: Query metrics from each discovered job
    for job in active_jobs:
        logger.info(f"[Prometheus] Querying job: {job}")
        
        # Query all metrics for this job
        query = f'{{job="{job}"}}'
        metrics = await fetch_metrics_from_prom(query)
        
        if metrics:
            all_metrics.extend(metrics)
            logger.info(f"[Prometheus] ✅ Got {len(metrics)} metrics from job '{job}'")
        else:
            logger.debug(f"[Prometheus] No metrics from job '{job}'")
    
    # Step 3: Also try HTTP metrics (FastAPI self-monitoring)
    logger.info("[Prometheus] Querying: HTTP metrics")
    http_metrics = await fetch_metrics_from_prom('{__name__=~"http_.*"}')
    if http_metrics:
        all_metrics.extend(http_metrics)
        logger.info(f"[Prometheus] ✅ Got {len(http_metrics)} HTTP metrics")
    
    # Step 4: Remove duplicates based on name+instance
    seen = set()
    unique_metrics = []
    for m in all_metrics:
        key = (m["name"], m["instance"])
        if key not in seen:
            seen.add(key)
            unique_metrics.append(m)
    
    logger.info(f"[Prometheus] Total unique metrics: {len(unique_metrics)}")
    
    if not unique_metrics:
        logger.warning("[Prometheus] ⚠️ No metrics found!")
        logger.warning("[Prometheus] Check targets at http://localhost:9090/targets")
        logger.warning("[Prometheus] Make sure targets are UP and exposing metrics")
    
    return unique_metrics


async def fetch_metrics_for_user(user_id: str) -> List[Dict]:
    """
    Fetch metrics for a specific user by filtering on user_id label.
    This is the key function for multi-user isolation!
    """
    logger.info(f"[Prometheus] Fetching metrics for user: {user_id}")
    
    try:
        # Query metrics with user_id label filter
        query = f'{{user_id="{user_id}"}}'
        metrics = await fetch_metrics_from_prom(query)
        
        if metrics:
            logger.info(f"[Prometheus] ✅ Got {len(metrics)} metrics for user {user_id}")
        else:
            logger.debug(f"[Prometheus] No metrics found for user {user_id}")
        
        return metrics
        
    except Exception as e:
        logger.error(f"[Prometheus] Error fetching metrics for user {user_id}: {e}")
        return []


async def fetch_metrics_for_ip(ip: str, port: int = 9100) -> List[Dict]:
    """
    Fetch metrics for a specific IP:PORT instance
    """
    instance = f"{ip}:{port}"
    logger.info(f"[Prometheus] Fetching metrics for instance: {instance}")
    
    try:
        # Query metrics for this specific instance
        query = f'{{instance="{instance}"}}'
        metrics = await fetch_metrics_from_prom(query)
        
        if metrics:
            logger.info(f"[Prometheus] ✅ Got {len(metrics)} metrics from {instance}")
        else:
            logger.warning(f"[Prometheus] No metrics from {instance}")
        
        return metrics
        
    except Exception as e:
        logger.error(f"[Prometheus] Error fetching metrics for {instance}: {e}")
        return []


async def fetch_metrics_for_multiple_ips(ips: List[tuple]) -> Dict[str, List[Dict]]:
    """
    Fetch metrics for multiple IPs
    Args:
        ips: List of (ip, port) tuples
    Returns:
        Dict mapping "ip:port" to list of metrics
    """
    results = {}
    
    for ip, port in ips:
        instance = f"{ip}:{port}"
        metrics = await fetch_metrics_for_ip(ip, port)
        results[instance] = metrics
    
    return results
