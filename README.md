```markdown
# AI DevOps Monitor
**FastAPI + Prometheus + MongoDB + LLM (+ optional Email + Slack)**

A lightweight monitoring service that:
- pulls metrics from **Prometheus**
- detects **anomalies** (threshold + z-score)
- generates **RCA (root cause + fix)** using an **LLM**
- stores everything in **MongoDB**
- optionally sends **email alerts**
- optionally sends **Slack alerts (ENV only)**
- exposes REST APIs + Prometheus `/metrics` for Grafana dashboards

---

## Table of Contents
- [What this does](#what-this-does)
- [Architecture (high level)](#architecture-high-level)
- [Features](#features)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
  - [.env example](#env-example)
  - [config.py reference](#configpy-reference)
  - [Prometheus targets (optional)](#prometheus-targets-optional)
- [Run](#run)
- [MongoDB Collections](#mongodb-collections)
- [API Endpoints](#api-endpoints)
- [Anomaly Detection](#anomaly-detection)
- [RCA via LLM](#rca-via-llm)
- [Alerts](#alerts)
  - [Email](#email)
  - [Slack (ENV only)](#slack-env-only)
- [Data Retention](#data-retention)
- [Grafana Setup](#grafana-setup)
- [Troubleshooting](#troubleshooting)
- [Security Notes](#security-notes)

---

## What this does

Every `MONITOR_INTERVAL` seconds, the monitor:
1. Queries Prometheus for metrics.
2. Stores a sampled snapshot in MongoDB (`metrics`).
3. Runs anomaly detection:
   - **Threshold rules** (e.g., CPU > 80)
   - **Z-score outlier detection** (rolling window)
4. Stores anomalies in MongoDB (`anomalies`).
5. For each anomaly, asks the LLM for RCA (root cause + fix).
6. Stores RCA in MongoDB (`rca`).
7. Optionally sends alerts:
   - Email (SMTP + MongoDB-driven enable/recipients)
   - Slack (webhook via env only)

---

## Architecture (high level)

- **FastAPI**: runs the service + exposes endpoints
- **Prometheus**: metrics source (your services + exporters)
- **MongoDB**: storage for snapshots/anomalies/rca/config/sessions
- **LLM**: generates RCA (Ollama-style `/api/generate`)
- **Instrumentator**: exposes `/metrics` for scraping

---

## Features

### Monitoring + Storage
- ✅ Periodic Prometheus metric collection  
- ✅ Stores sampled metric snapshots to MongoDB  
- ✅ Stores anomalies + RCA to MongoDB  
- ✅ Multi-target support (optional via MongoDB `targets`)

### Detection + RCA
- ✅ Threshold-based anomaly detection
- ✅ Z-score based outlier detection
- ✅ RCA generation via LLM (JSON output)

### Alerting
- ✅ Email alerts (SMTP)
- ✅ Slack alerts via incoming webhook (**env only**)

### Ops / Observability
- ✅ `/metrics` endpoint for Prometheus scraping (FastAPI Instrumentator)
- ✅ Dashboard-friendly APIs (`/stats`, `/anomalies`, `/rca`)
- ✅ Session tracking for chat + monitoring traces (Langfuse optional)

---

## Project Structure

```

fastapi_metrics/
├─ main.py
├─ config.py
├─ .env                 # optional
├─ requirements.txt
└─ README.md

````

---

## Prerequisites

- Python **3.10+**
- Prometheus (local or remote)
- MongoDB (local or remote)
- LLM endpoint (example: Ollama-style API)

---

## Installation

### 1) Create venv and install dependencies

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

Your `main.py` imports settings from `config.py`, and `config.py` reads env vars.

### .env example

Minimal required for the system to run:

```env
# Prometheus
PROM_URL=http://localhost:9090

# MongoDB
MONGO_URI=mongodb://localhost:27017
MONGO_DB=observability

# LLM (Ollama style)
LLM_URL=http://localhost:11434
LLM_MODEL=llama3.2

# Monitoring
MONITOR_INTERVAL=30
Z_THRESHOLD=3.0
MAX_DOCS=100
```

Optional email:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASSWORD=app_password_here
```

Optional Slack (**only 2 vars required**):

```env
SLACK_ENABLED=true
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ
```

Optional Langfuse:

```env
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...
LANGFUSE_HOST=https://cloud.langfuse.com
```

---

### config.py reference

Your `config.py` should expose values like:

```py
PROM_URL, MONGO_URI, DB_NAME,
LLM_URL, LLM_MODEL,
MONITOR_INTERVAL, Z_THRESHOLD, MAX_DOCS,
SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, ALERT_EMAILS,
SLACK_ENABLED, SLACK_WEBHOOK_URL
```

> **Note:** Email recipients are taken from MongoDB (`email_config`), not `ALERT_EMAILS`.

---

### Prometheus targets (optional)

If MongoDB has enabled target documents in `targets`, the service will scrape those instead of only `PROM_URL`.

Example document:

```json
{
  "name": "my-prom",
  "endpoint": "localhost:9090",
  "job": "serviceA",
  "enabled": true
}
```

---

## Run

### 1) Start MongoDB

Local example:

```bash
mongod
```

### 2) Start Prometheus

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

* Root: `http://localhost:8000/`
* FastAPI metrics: `http://localhost:8000/metrics`

---

## MongoDB Collections

Database: `DB_NAME`

| Collection      | Purpose                                               |
| --------------- | ----------------------------------------------------- |
| `metrics`       | periodic metric snapshots (count + sample of metrics) |
| `anomalies`     | detected anomalies with severity/reason               |
| `rca`           | LLM RCA output linked to anomaly                      |
| `targets`       | optional list of Prometheus endpoints                 |
| `email_config`  | email enabled + recipients                            |
| `chat_sessions` | chat session metadata (tokens, messages, timestamps)  |

---

## API Endpoints

### Health / Info

* `GET /`
  Shows service status and whether Slack/Langfuse are enabled.

### Dashboard stats

* `GET /stats`
  Counts for metrics/anomalies/rca/chat sessions.

### Data

* `GET /prom-metrics` — last 10 metric snapshots
* `GET /anomalies` — last 20 anomalies
* `GET /rca` — last 20 RCA results

### Chat (LLM)

* `POST /api/chat` — returns response + `session_id`

Body:

```json
{
  "message": "What does high CPU mean?",
  "context": {},
  "session_id": null
}
```

### Email config

* `GET /agent/email-config`
* `PUT /agent/email-config`
* `POST /agent/test-email`

Body for PUT:

```json
{
  "enabled": true,
  "recipients": ["you@example.com"]
}
```

### Slack (env only)

* `GET /agent/slack-status`
* `POST /agent/test-slack`

> No Slack config is stored in MongoDB in the env-only setup.

---

## Anomaly Detection

### 1) Threshold rules (built-in)

Examples:

* `up < 1` → **critical**
* `cpu_usage > 80` → **high**
* `memory_usage > 80` → **high**
* `http_request_duration_seconds > 5` → **high**
* `errors_total > 10` → **high**
* `disk_usage > 90` → **critical**

### 2) Z-score outliers

* Maintains a rolling history of last **10** values per metric
* Needs at least **5 samples** before detecting outliers
* Flags outlier if `z > Z_THRESHOLD`

---

## RCA via LLM

For each anomaly, the service builds a prompt with:

* anomaly details (metric/value/severity/reason)
* a small context window (top ~15 metrics)

Expected LLM output: **valid JSON**

```json
{
  "summary": "one-line technical summary",
  "simplified": "ELI5 explanation",
  "cause": "most likely root cause",
  "fix": "specific remediation steps"
}
```

If the LLM fails/unavailable, the service stores a fallback RCA.

---

## Alerts

### Email

Email alerts are controlled via MongoDB `email_config`:

* enabled flag
* recipients list

Enable (example):

```bash
curl -X PUT http://localhost:8000/agent/email-config \
  -H "Content-Type: application/json" \
  -d "{\"enabled\": true, \"recipients\": [\"you@example.com\"]}"
```

Test:

```bash
curl -X POST http://localhost:8000/agent/test-email
```

**Gmail note:** Use an **App Password**, not your normal password.

---

### Slack (ENV only)

Slack alerts are controlled purely via env:

```env
SLACK_ENABLED=true
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ
```

Test:

```bash
curl -X POST http://localhost:8000/agent/test-slack
```

> Incoming webhooks post to the channel you selected while creating the webhook.
> This setup does not override channel/username via env.

---

## Data Retention

The monitor enforces retention (`MAX_DOCS`) for:

* `metrics`
* `anomalies`
* `rca`

When a collection exceeds `MAX_DOCS`, the oldest documents are deleted.

---

## Grafana Setup

1. Add Prometheus datasource in Grafana:

   * URL: `http://localhost:9090`

2. Create dashboards using:

   * metrics from your services in Prometheus
   * optional: FastAPI `/metrics` for API runtime stats

---

## Troubleshooting

### “Database objects do not implement truth value testing”

Use explicit checks:

* ✅ `if db is None:` not `if not db:`
* ✅ `if db is not None:` not `if db:`

### No anomalies visible

* Confirm Prometheus is returning metrics for your target(s)
* Increase `MONITOR_INTERVAL` to allow history to build
* Ensure metric names match your threshold patterns
* Try lowering thresholds temporarily to validate end-to-end flow

### Email not sending

* Ensure email config enabled via API
* Ensure `SMTP_USER` and `SMTP_PASSWORD` set
* Check provider rules (Gmail requires App Password)

### Slack not sending

* Ensure `SLACK_ENABLED=true`
* Ensure webhook is correct (no quotes, no trailing spaces)
* Confirm your environment is loaded (`load_dotenv(override=True)`)

---

```
