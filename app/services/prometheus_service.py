"""
Prometheus Service - Production Ready
"""
from typing import List, Dict
import httpx
from app.core.config import PROM_URL
from app.services.mongodb_service import get_db
from app.core.logging import logger


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
                
                if val is not None and val != "":
                    try:
                        metrics.append({
                            "name": name,
                            "value": float(val),
                            "instance": instance
                        })
                    except Exception:
                        metrics.append({
                            "name": name,
                            "value": val,
                            "instance": instance
                        })
            
            return metrics
            
    except Exception as e:
        logger.error(f"[Prometheus] Error querying {PROM_URL}: {e}")
        return []


async def fetch_metrics() -> List[Dict]:
    """
    Fetch metrics from Prometheus
    Production-ready: Tries multiple query strategies
    """
    # Try these queries in order (stop when we get enough metrics)
    queries_to_try = [
        # 1. HTTP metrics (FastAPI self-monitoring)
        ('{__name__=~"http_.*"}', "HTTP metrics"),
        
        # 2. Configured targets
        ('{job="dynamic-targets"}', "Dynamic targets"),
        
        # 3. FastAPI job
        ('{job="fastapi"}', "FastAPI job"),
    ]
    
    all_metrics = []
    
    for query, description in queries_to_try:
        logger.info(f"[Prometheus] Querying: {description}")
        metrics = await fetch_metrics_from_prom(query)
        
        if metrics:
            all_metrics.extend(metrics)
            logger.info(f"[Prometheus] ✅ Got {len(metrics)} metrics from {description}")
        else:
            logger.debug(f"[Prometheus] No metrics from {description}")
    
    # Remove duplicates based on name+instance
    seen = set()
    unique_metrics = []
    for m in all_metrics:
        key = (m["name"], m["instance"])
        if key not in seen:
            seen.add(key)
            unique_metrics.append(m)
    
    logger.info(f"[Prometheus] Total unique metrics: {len(unique_metrics)}")
    
    if not unique_metrics:
        logger.warning("Prometheus targets at http://localhost:9090/targets")
    
    return unique_metricsb