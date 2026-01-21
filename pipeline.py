import os, time, json, threading, uuid, re
from datetime import datetime, timezone, timedelta

import requests
import numpy as np
from pymongo import MongoClient, UpdateOne

# Import config from separate file
from config import (
    PROM_URL, MONGO_URI, DB_NAME, ENV,
    LLM_URL, LLM_MODEL,
    STEP, COLLECT_WINDOW, LOOKBACK_MIN,
    Z_THRESHOLD, MIN_POINTS, MAX_DOCS,
    METRICS
)

# ---------------- HELPERS ----------------
def get_db():
    return MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)[DB_NAME]

def call_llm(prompt):
    """Call local Ollama LLM"""
    try:
        resp = requests.post(
            LLM_URL,
            headers={"Content-Type": "application/json"},
            json={"model": LLM_MODEL, "prompt": prompt, "stream": False},
            timeout=120
        )
        resp.raise_for_status()
        return resp.json().get("response", "")
    except Exception as e:
        print(f"[llm] error: {e}")
        return None

def prom_query(query, start, end, step):
    """Query Prometheus range API"""
    try:
        r = requests.get(
            f"{PROM_URL}/api/v1/query_range",
            params={"query": query, "start": start, "end": end, "step": step},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["data"]["result"]
    except Exception as e:
        print(f"[prom] error querying {query}: {e}")
        return []

def robust_z(vals):
    """Calculate robust Z-score"""
    v = np.array(vals)
    med = np.median(v)
    mad = np.median(np.abs(v - med)) + 1e-9
    z = 0.6745 * (v[-1] - med) / mad
    return z, med

# ---------------- WORKERS ----------------
def collector(stop):
    """
    Collects metrics from Prometheus.
    Simple prom_rollup_1m schema:
    - ts, metric, instance, value, min, max, avg
    """
    db = get_db()
    col = db.prom_rollup_1m

    while not stop.is_set():
        now = int(time.time())
        start = now - COLLECT_WINDOW
        ts = datetime.fromtimestamp(now - now % 60, timezone.utc)

        ops = []
        for metric in METRICS:
            for s in prom_query(metric, start, now, STEP):
                instance = s["metric"].get("instance", "unknown")
                job = s["metric"].get("job", "unknown")
                
                vals = []
                for _, v in s["values"]:
                    try:
                        vals.append(float(v))
                    except:
                        pass
                
                if not vals:
                    continue

                doc = {
                    "ts": ts,
                    "metric": metric,
                    "instance": instance,
                    "job": job,
                    "value": vals[-1],
                    "min": min(vals),
                    "max": max(vals),
                    "avg": sum(vals) / len(vals),
                }

                ops.append(UpdateOne(
                    {"ts": ts, "metric": metric, "instance": instance},
                    {"$set": doc},
                    upsert=True,
                ))

        if ops:
            col.bulk_write(ops, ordered=False)
            print(f"[collector] wrote {len(ops)} docs")

        time.sleep(5)

def anomaly_detector(stop):
    """
    Detects anomalies using Z-score.
    Simple anomalies schema:
    - anomaly_id, metric, instance, severity
    - expected, actual, deviation_pct
    - detected_at, status, llm_analysis
    """
    db = get_db()
    src = db.prom_rollup_1m
    out = db.anomalies

    while not stop.is_set():
        print("[anomaly] running")
        end = datetime.now(timezone.utc)
        start = end - timedelta(minutes=LOOKBACK_MIN)

        # Group by metric+instance
        data = {}
        for d in src.find({"ts": {"$gte": start, "$lte": end}}):
            try:
                key = (d["metric"], d["instance"])
                data.setdefault(key, []).append(d)
            except KeyError:
                continue  # Skip docs with missing keys

        for (metric, instance), docs in data.items():
            if len(docs) < MIN_POINTS:
                continue

            vals = [d["avg"] for d in docs]
            z, baseline = robust_z(vals)

            if abs(z) >= Z_THRESHOLD:
                actual = vals[-1]
                deviation = abs((actual - baseline) / baseline) * 100 if baseline else 0
                
                # Determine severity
                if abs(z) >= 4:
                    severity = "critical"
                elif abs(z) >= 3:
                    severity = "high"
                elif abs(z) >= 2.5:
                    severity = "medium"
                else:
                    severity = "low"
                
                anomaly_id = str(uuid.uuid4())
                
                # Simple anomaly document
                doc = {
                    "anomaly_id": anomaly_id,
                    "metric": metric,
                    "instance": instance,
                    "severity": severity,
                    "expected": round(baseline, 2),
                    "actual": round(actual, 2),
                    "deviation_pct": round(deviation, 1),
                    "z_score": round(z, 2),
                    "detected_at": end,
                    "status": "open",
                }
                
                # Quick LLM analysis
                prompt = f"Briefly analyze this anomaly in 2 sentences: {metric} on {instance} jumped from {baseline:.0f} to {actual:.0f} ({deviation:.0f}% change). Severity: {severity}"
                llm_resp = call_llm(prompt)
                if llm_resp:
                    doc["llm_analysis"] = llm_resp[:500]
                
                _id = f"{metric}|{instance}|{end.isoformat()}"
                out.update_one({"_id": _id}, {"$set": {**doc, "_id": _id}}, upsert=True)
                print(f"[anomaly] {severity}: {metric} on {instance} ({deviation:.0f}% deviation)")

        time.sleep(5)

def rca_generator(stop):
    """
    Generates RCA for open anomalies.
    Simple rca_results schema:
    - rca_id, anomaly_id, metric, severity
    - root_cause, action, analyzed_at
    """
    db = get_db()
    an = db.anomalies
    rca = db.rca_results

    while not stop.is_set():
        print("[rca] running")
        for a in an.find({"status": "open"}):
            try:
                prompt = f"""Analyze this anomaly and provide RCA in JSON:
Metric: {a['metric']}
Instance: {a['instance']}
Expected: {a['expected']}, Actual: {a['actual']}
Deviation: {a['deviation_pct']}%, Severity: {a['severity']}

Return JSON: {{"root_cause": "explanation", "action": "what to do"}}"""

                resp = call_llm(prompt)
                if not resp:
                    continue
                
                # Extract JSON
                try:
                    match = re.search(r'\{[\s\S]*\}', resp)
                    rca_json = json.loads(match.group()) if match else {}
                except:
                    rca_json = {"root_cause": resp[:300], "action": "Investigate manually"}
                
                # Simple RCA document
                rca_doc = {
                    "rca_id": str(uuid.uuid4()),
                    "anomaly_id": a["anomaly_id"],
                    "metric": a["metric"],
                    "instance": a["instance"],
                    "severity": a["severity"],
                    "root_cause": rca_json.get("root_cause", "Unknown"),
                    "action": rca_json.get("action", "Investigate"),
                    "analyzed_at": datetime.now(timezone.utc),
                }

                rca.update_one(
                    {"anomaly_id": a["anomaly_id"]},
                    {"$set": rca_doc},
                    upsert=True,
                )
                an.update_one({"_id": a["_id"]}, {"$set": {"status": "analyzed"}})
                print(f"[rca] done: {a['metric']}")
                
            except Exception as e:
                print(f"[rca] error: {e}")

        time.sleep(5)

def cleanup(stop):
    """Keep only MAX_DOCS documents per collection"""
    db = get_db()
    while not stop.is_set():
        for name, field in [("prom_rollup_1m", "ts"), ("anomalies", "detected_at"), ("rca_results", "analyzed_at")]:
            col = db[name]
            count = col.count_documents({})
            if count > MAX_DOCS:
                ids = [d["_id"] for d in col.find().sort(field, 1).limit(count - MAX_DOCS)]
                col.delete_many({"_id": {"$in": ids}})
                print(f"[cleanup] {name} -> {MAX_DOCS}")
        time.sleep(5)

# ---------------- MAIN ----------------
def main():
    print(f"📡 Prometheus: {PROM_URL}")
    print(f"🗄️  MongoDB: {DB_NAME}")
    print(f"🤖 LLM: {LLM_MODEL}")
    print()
    
    stop = threading.Event()
    for fn in [collector, anomaly_detector, rca_generator, cleanup]:
        threading.Thread(target=fn, args=(stop,), daemon=True).start()

    print("✅ Pipeline running")
    print("   Schemas: prom_rollup_1m | anomalies | rca_results")
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
