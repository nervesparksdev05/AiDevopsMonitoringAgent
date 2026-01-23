```markdown
# AI DevOps Monitor (FastAPI + Prometheus + MongoDB + LLM)

A lightweight DevOps monitoring service that:
- Pulls metrics from **Prometheus**
- Detects **anomalies** (threshold + z-score)
- Generates **RCA (root cause + fix)** using an **LLM**
- Stores everything in **MongoDB**
- Optionally sends **email alerts**
- Exposes APIs + Prometheus `/metrics` for Grafana dashboards

---

## Features

- ✅ Periodic Prometheus metric collection
- ✅ Anomaly detection:
  - Rule-based **threshold checks**
  - Statistical **z-score** outlier detection
- ✅ RCA via LLM (JSON output: summary, cause, fix)
- ✅ Stores:
  - raw metrics (sampled)
  - anomalies
  - RCA results
  - email configuration
- ✅ Email alerts (SMTP + MongoDB-driven enable/recipients)
- ✅ FastAPI endpoints for dashboard integration
- ✅ `/metrics` endpoint exposed for Prometheus scraping (via Instrumentator)

---

## Project Structure

```

fastapi_metrics/
├─ main.py
├─ config.py
├─ .env                # optional (if your config.py loads env)
├─ requirements.txt
└─ README.md

````

---

## Requirements

- Python 3.10+
- Prometheus running locally or remotely
- MongoDB running locally or remotely
- LLM endpoint (example: Ollama-style `/api/generate`)

---

## Install

### 1) Create venv + install dependencies

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt
````

---

## Configuration

Your `main.py` imports from `config.py`:

```py
PROM_URL, MONGO_URI, DB_NAME,
LLM_URL, LLM_MODEL,
MONITOR_INTERVAL, Z_THRESHOLD, MAX_DOCS,
SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, ALERT_EMAILS
```

### Example `config.py` (reference)

```python
import os

PROM_URL = os.getenv("PROM_URL", "http://localhost:9090")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "ai_devops_monitor")

LLM_URL = os.getenv("LLM_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-oss:latest")

MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL", "10"))  # seconds
Z_THRESHOLD = float(os.getenv("Z_THRESHOLD", "2.5"))
MAX_DOCS = int(os.getenv("MAX_DOCS", "100"))

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

ALERT_EMAILS = os.getenv("ALERT_EMAILS", "")
```

> **Note:** Email recipients are primarily taken from MongoDB `email_config` collection (not `ALERT_EMAILS`).

---

## Run

### 1) Start MongoDB

**Local example**

```bash
mongod
```

### 2) Start Prometheus

Run Prometheus with your `prometheus.yml` (example):

```bash
prometheus --config.file=prometheus.yml
```

Verify:

* Prometheus UI: `http://localhost:9090`

### 3) Start the FastAPI monitor

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Verify:

* API root: `http://localhost:8000/`
* Prometheus metrics endpoint: `http://localhost:8000/metrics`

---

## MongoDB Collections

Database: `DB_NAME`

Collections created/used:

* `metrics`

  * Stores periodic snapshots (count + up to 50 metrics sample)
* `anomalies`

  * Stores anomalies detected (threshold or z-score)
* `rca`

  * Stores LLM RCA outputs linked with `anomaly_id`
* `targets`

  * Optional: list of Prometheus endpoints to scrape from MongoDB
* `email_config`

  * Stores email enabled flag + recipients list

---

## API Endpoints

### Health / Info

* `GET /`

  * Returns running status + configured Prometheus + model

### Dashboard stats

* `GET /stats`

  * Returns counts for metrics/anomalies/rca

### Data

* `GET /prom-metrics`

  * Returns last 10 metric snapshots
* `GET /anomalies`

  * Returns last 20 anomalies
* `GET /rca`

  * Returns last 20 RCA results

### Email config

* `GET /agent/email-config`
* `PUT /agent/email-config`

  * Body:

    ```json
    {
      "enabled": true,
      "recipients": ["you@example.com"]
    }
    ```
* `POST /agent/test-email`

  * Sends a test email if SMTP creds + config are valid

---

## Prometheus Targets (Optional)

If `targets` collection contains enabled targets, the system pulls metrics from them instead of only `PROM_URL`.

Example document in `targets`:

```json
{
  "name": "my-service",
  "endpoint": "localhost:9090",
  "job": "serviceA",
  "enabled": true
}
```

---

## Anomaly Detection Rules

### Threshold rules (built-in)

Examples:

* `up < 1` → critical
* `cpu_usage > 80` → high
* `memory_usage > 80` → high
* `http_request_duration_seconds > 5` → high
* `errors_total > 10` → high
* `disk_usage > 90` → critical

### Z-score rules

* Uses rolling history of last **10** values per metric
* Needs at least **5 values** before detecting outliers
* Flags if `z > Z_THRESHOLD`

---

## Data Retention / Cleanup

The monitor enforces `MAX_DOCS` retention for:

* `metrics`
* `anomalies`
* `rca`

Oldest documents are deleted when the collection exceeds `MAX_DOCS`.

---

## Troubleshooting

### 1) “Database objects do not implement truth value testing”

✅ Fixed by using explicit checks:

* `if db is None:` instead of `if not db:`
* `if db is not None:` instead of `if db:`

### 2) No anomalies visible

* Ensure Prometheus is returning metrics from your targets
* Increase `MONITOR_INTERVAL` to allow history to build
* Ensure your service metrics include values that can cross thresholds

### 3) Email not sending

* Enable email config:

  * `PUT /agent/email-config`
* Ensure `SMTP_USER` and `SMTP_PASSWORD` are set
* For Gmail, use **App Passwords** (not your normal password)

---

## Example: Enable email alerts

```bash
curl -X PUT http://localhost:8000/agent/email-config \
  -H "Content-Type: application/json" \
  -d "{\"enabled\": true, \"recipients\": [\"you@example.com\"]}"
```

Test:

```bash
curl -X POST http://localhost:8000/agent/test-email
```

---

## Grafana Setup (Quick)

1. Add Prometheus datasource:

   * URL: `http://localhost:9090`
2. Add dashboard panels using:

   * Prometheus metrics from your services
   * Your FastAPI `/metrics` endpoint if needed

---

