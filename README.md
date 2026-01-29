# AI DevOps Monitor

**Intelligent infrastructure monitoring with AI-powered root cause analysis**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-6.0+-success.svg)](https://www.mongodb.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Real-time monitoring with LLM-powered anomaly detection, batch analysis, and intelligent alerting

---

## 🎯 Overview

AI DevOps Monitor collects Prometheus metrics and uses LLM (Large Language Model) to detect anomalies, identify root causes, and provide actionable remediation steps. Built for production with FastAPI, MongoDB, and comprehensive observability.

### Key Features

- **🤖 100% LLM-Powered** - AI detects anomalies from raw metrics (no threshold rules)
- **📊 Batch Analysis** - Analyzes entire metric batches for holistic incident detection
- **🔔 Multi-Channel Alerts** - Email and Slack notifications with rich formatting
- **💾 Full Observability** - MongoDB storage with Langfuse LLM tracking
- **⚡ Production Ready** - Async operations, IST timezone support, comprehensive error handling

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- MongoDB 6.0+
- Prometheus
- Ollama (or compatible LLM)

### Installation

```bash
# Clone and setup
git clone https://github.com/yourusername/ai-devops-monitor.git
cd ai-devops-monitor
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your settings

# Start
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Visit `http://localhost:8000/docs` for API documentation.

---

## ⚙️ Configuration

### Environment Variables

```env
# Core Services
PROM_URL=http://localhost:9090
MONGO_URI=mongodb://localhost:27017
LLM_URL=http://localhost:11434
LLM_MODEL=llama3.2

# Monitoring Settings
BATCH_INTERVAL_MINUTES=1          # Analysis frequency
BATCH_MAX_METRICS=600            # Max metrics per prompt

# Email Alerts (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Gmail: Use App Password

# Slack Alerts (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK

# Langfuse Tracking (Optional)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

**Gmail App Password Setup:**
1. Enable 2-Step Verification at https://myaccount.google.com/security
2. Generate App Password at https://myaccount.google.com/apppasswords
3. Use the 16-character password in `SMTP_PASSWORD`

**Slack Webhook Setup:**
1. Create app at https://api.slack.com/apps
2. Enable Incoming Webhooks
3. Add webhook to workspace and copy URL

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  AI DevOps Monitor                      │
│                                                         │
│  Prometheus ──▶ FastAPI ──▶ LLM ──▶ MongoDB           │
│      ↓            │           │         │              │
│   Metrics      Batch       RCA     Storage             │
│                Analysis                                 │
│                   │                                     │
│                   └──▶ Alerts (Email + Slack)          │
└─────────────────────────────────────────────────────────┘
```

### Batch Monitoring Flow

```
Every 1 minute:
1. Fetch metrics from Prometheus (self-monitoring + targets)
2. Group by instance and build LLM prompt
3. LLM analyzes batch and detects anomalies
4. Store: batch → incident → anomalies → RCA
5. Send alerts (Email + Slack) if incidents detected
6. Track with Langfuse for observability
```

---

## 📚 API Endpoints

### Core

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | System status |
| `/health` | GET | Health check with IST time |
| `/stats` | GET | Collection statistics |
| `/docs` | GET | Interactive API docs |

### Data

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/anomalies` | GET | LLM-detected anomalies |
| `/rca` | GET | Root cause analyses |
| `/batches` | GET | Metrics batches |
| `/incidents` | GET | Detected incidents |

### Configuration

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/agent/email-config` | GET/PUT | Email settings |
| `/agent/slack-config` | GET/PUT | Slack settings |
| `/agent/targets` | GET/POST | Prometheus targets |
| `/agent/test-email` | POST | Send test email |
| `/agent/test-slack` | POST | Send test Slack message |

### AI Chat

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Chat with AI about incidents |
| `/api/sessions` | GET | List chat sessions |
| `/api/sessions/{id}` | DELETE | Delete session |

---

## 🔍 How It Works

### LLM-Powered Detection

The system uses **pure AI detection** - no threshold rules or statistical methods:

1. **Fetch Metrics** - Queries Prometheus for all relevant metrics
2. **Group by Instance** - Organizes metrics by server/service
3. **Build Prompt** - Creates structured prompt with time window and ALL metrics
4. **LLM Analysis** - AI analyzes the entire batch and decides what's anomalous
5. **Parse Response** - Extracts incident, anomalies, clusters from JSON
6. **Store Everything** - Saves to MongoDB for history
7. **Send Alerts** - Notifies via Email/Slack if issues found

### Why LLM-Only?

**Advantages:**
- ✅ **No Configuration Needed** - AI learns what's normal
- ✅ **Context-Aware** - Considers relationships between metrics
- ✅ **Adaptive** - Adjusts to changing baselines automatically
- ✅ **Explains Itself** - Provides reasons for each detection

**Traditional threshold monitoring:**
```
if cpu > 80%: alert("High CPU")  # Might be normal during deployments
```

**AI monitoring:**
```
"CPU at 95% but this is expected during the scheduled backup window.
However, memory is also spiking unusually, suggesting a leak."
```

### LLM Prompt Structure

```
You are an expert SRE analyzing Prometheus metrics.

BATCH WINDOW (IST): 2026-01-29 03:15:00 IST -> 03:16:00 IST (1 min)

TASKS:
1. Detect anomalies (spikes, drops, errors, high resource usage)
2. Cluster related anomalies by root cause
3. Provide collective RCA with evidence
4. Return ONLY valid JSON

METRICS (16/16 included):

### Instance: host.docker.internal:8000
  http_requests_total: 130.0
  http_request_duration_seconds: 1.8324
  http_request_size_bytes_sum: 0.0  ← AI notices this is unusual
  ...

SCHEMA:
{
  "incident": {...},
  "anomalies": [...],
  "clusters": [...]
}
```

### AI Response Format

```json
{
  "incident": {
    "title": "Missing HTTP Request Size Metrics",
    "severity": "medium",
    "summary": "Request size sum is zero despite 130 total requests",
    "root_cause": "Instrumentation configuration issue",
    "fix_plan": {
      "immediate": ["Check prometheus-fastapi-instrumentator config"],
      "prevention": ["Add monitoring for metric collection gaps"]
    }
  },
  "anomalies": [
    {
      "metric": "http_request_size_bytes_sum",
      "instance": "host.docker.internal:8000",
      "observed": 0.0,
      "expected": "non-zero average size per request",
      "symptom": "Zero request body size recorded"
    }
  ]
}
```

---

## 🔔 Alerting

### Email Alert Example

```
Subject: [MEDIUM] Missing HTTP Request Size Metrics

🟡 MEDIUM INCIDENT
─────────────────
Window: 2026-01-29 03:15 -> 03:16 IST

Summary: Request size sum is zero despite 130 total requests

Root Cause: Instrumentation configuration issue

Immediate Actions:
• Check prometheus-fastapi-instrumentator config

Anomalies: 1 | Confidence: 75%
```

### Slack Alert Example

```
🟡 [MEDIUM] Missing HTTP Request Size Metrics
📅 Window: 2026-01-29 03:15 -> 03:16 IST
📋 Request size sum is zero despite 130 total requests
🔍 Root Cause: Instrumentation configuration issue
⚡ Actions: Check prometheus-fastapi-instrumentator config
📊 Anomalies: 1
```

---

## 🐛 Troubleshooting

### No Anomalies Being Detected

**This is actually GOOD!** It means:
- ✅ Your system is healthy
- ✅ AI doesn't see any issues
- ✅ Everything is within normal operating parameters

The AI only alerts when it **genuinely** detects problems, not based on arbitrary thresholds.

### Prometheus Not Returning Metrics

**Check Prometheus:**
```bash
curl http://localhost:9090/api/v1/query?query=up
```

**Check Backend Logs:**
```
[Batch] No metrics - skipping
```

**Solution:** Configure Prometheus to scrape your FastAPI app:
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'fastapi'
    static_configs:
      - targets: ['localhost:8000']
```

### Timestamps Wrong in Frontend

**Issue:** Times showing in UTC instead of IST

**Solution:** Replace frontend `Anomalies.jsx` with the IST-fixed version

### Email Not Sending

**Common issues:**
1. Gmail requires App Password, not regular password
2. `SMTP_USER` and `SMTP_PASSWORD` must be set in `.env`
3. Email config must be enabled via API: `PUT /agent/email-config`

**Test SMTP:**
```bash
curl -X POST http://localhost:8000/agent/test-email
```

### LLM Not Responding

**Check Ollama:**
```bash
ollama list  # Should show llama3.2
curl http://localhost:11434/api/tags
```

**Pull model if missing:**
```bash
ollama pull llama3.2
```

### LLM Too Slow

**Options:**
1. Use smaller model: `LLM_MODEL=llama3.2:1b` (faster but less accurate)
2. Increase batch interval: `BATCH_INTERVAL_MINUTES=5` (analyze less frequently)
3. Reduce metrics: `BATCH_MAX_METRICS=300` (send less data to LLM)

---

## 📊 Data Storage

### MongoDB Collections

| Collection | Purpose | Retention |
|-----------|---------|-----------|
| `metrics_batches` | Prometheus metric snapshots | Permanent |
| `incidents` | AI-detected incidents | Permanent |
| `anomalies` | Individual anomalies from LLM | Permanent |
| `rca` | Root cause analyses | Permanent |
| `chat_sessions` | AI chat history | 30 days |
| `email_config` | Email recipients | Permanent |
| `slack_config` | Slack webhook settings | Permanent |
| `targets` | Prometheus targets | Permanent |

### Session Cleanup

Chat sessions are cleaned up automatically after 30 days. To change retention, edit `main.py` line 392:

```python

# Keep for 1 month
session_manager.cleanup_old_sessions(db, hours=720)

```

---

## ⚡ Performance

### Benchmarks (1-minute batches, 16 metrics)

| Metric | Value |
|--------|-------|
| Metric fetch | ~1s |
| LLM analysis | 10-15s |
| Alert delivery | 1-2s |
| **Total cycle** | **~15s** |
| Memory usage | ~200MB |


## 🔒 Security

### Best Practices

- ✅ Store secrets in `.env` (never commit to git)
- ✅ Use MongoDB authentication in production
- ✅ Restrict CORS to known domains
- ✅ Use HTTPS for public deployments
- ✅ Rotate Slack webhooks regularly
- ✅ Use App Passwords for Gmail (not regular passwords)
- ✅ Keep dependencies updated: `pip install --upgrade -r requirements.txt`

### Production Checklist

- [ ] `.env` in `.gitignore`
- [ ] MongoDB authentication enabled
- [ ] CORS restricted to frontend domain
- [ ] Firewall rules configured
- [ ] Regular backups scheduled
- [ ] Monitoring alerts tested
- [ ] Langfuse session tracking verified

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 🙏 Acknowledgments

- **FastAPI** - Modern async web framework
- **Prometheus** - Industry-standard metrics
- **MongoDB** - Flexible document storage
- **Ollama** - Easy local LLM deployment
- **Langfuse** - LLM observability and cost tracking

---
