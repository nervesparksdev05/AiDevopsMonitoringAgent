# AI DevOps Monitor

**Intelligent infrastructure monitoring with AI-powered root cause analysis**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-6.0+-success.svg)](https://www.mongodb.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Real-time monitoring with AI-powered anomaly detection, batch analysis, and intelligent alerting

---

## 🎯 Overview

AI DevOps Monitor collects Prometheus metrics, detects anomalies using statistical analysis, and generates actionable insights through LLM-powered root cause analysis. Built for production with FastAPI, MongoDB, and comprehensive observability.

### Key Features

- **🤖 Batch AI Analysis** - LLM analyzes entire metric batches for holistic incident detection
- **📊 Smart Detection** - Combines threshold rules with Z-score outlier detection
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
3. LLM analyzes entire batch holistically
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
| `/anomalies` | GET | Recent anomalies |
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

### Batch Analysis

The system analyzes metrics in batches every minute (configurable):

1. **Fetch Metrics** - Queries Prometheus for all relevant metrics
2. **Group by Instance** - Organizes metrics by server/service
3. **Build Prompt** - Creates structured prompt with time window and metrics
4. **LLM Analysis** - Sends to LLM for holistic analysis
5. **Parse Response** - Extracts incident, anomalies, clusters from JSON
6. **Store Everything** - Saves to MongoDB for history
7. **Send Alerts** - Notifies via Email/Slack if issues found

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
  ...

SCHEMA:
{
  "incident": {...},
  "anomalies": [...],
  "clusters": [...]
}
```

### Response Format

```json
{
  "incident": {
    "title": "High Request Latency",
    "severity": "high",
    "summary": "Request duration increased 3x above baseline",
    "root_cause": "Database query performance degradation",
    "fix_plan": {
      "immediate": ["Check slow query log", "Restart DB connection pool"],
      "next_24h": ["Add indexes", "Optimize queries"],
      "prevention": ["Set up query performance monitoring"]
    }
  },
  "anomalies": [
    {"metric": "http_request_duration_seconds", "observed": 5.2, "expected": "< 2.0"}
  ]
}
```

---

## 🔔 Alerting

### Email Alert Example

```
Subject: [HIGH] High Request Latency

🚨 HIGH INCIDENT
─────────────────
Window: 2026-01-29 03:15 -> 03:16 IST

Summary: Request duration increased 3x above baseline

Root Cause: Database query performance degradation

Immediate Actions:
• Check slow query log
• Restart DB connection pool

Anomalies: 2 | Confidence: 85%
```

### Slack Alert Example

```
🟠 [HIGH] High Request Latency
📅 Window: 2026-01-29 03:15 -> 03:16 IST
📋 Request duration increased 3x above baseline
🔍 Root Cause: Database query performance degradation
⚡ Actions: Check slow query log, Restart DB connection pool
📊 Anomalies: 2
```

---

## 🐛 Troubleshooting

### No Metrics Being Collected

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

### Timestamps Wrong

**Issue:** Times showing in UTC instead of IST

**Solution:** Replace `Anomalies.jsx` with `Anomalies_IST_FIXED.jsx` (converts UTC to IST in frontend)

### Email Not Sending

**Common issues:**
1. Gmail requires App Password, not regular password
2. `SMTP_USER` and `SMTP_PASSWORD` must be set
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

---

## 📊 Data Storage

### MongoDB Collections

| Collection | Purpose | Retention |
|-----------|---------|-----------|
| `metrics_batches` | Prometheus metric snapshots | Permanent |
| `incidents` | Detected incidents | Permanent |
| `anomalies` | Individual anomalies | Permanent |
| `rca` | Root cause analyses | Permanent |
| `chat_sessions` | AI chat history | 30 days (configurable) |
| `email_config` | Email recipients | Permanent |
| `slack_config` | Slack webhook settings | Permanent |
| `targets` | Prometheus targets | Permanent |

### Session Cleanup

Chat sessions are cleaned up automatically:

```python
# Default: Keep for 30 days
session_manager.cleanup_old_sessions(db, hours=720)
```

To keep longer, edit `main.py` line 392.

---

## ⚡ Performance

### Benchmarks (1-minute batches)

| Metric | Value |
|--------|-------|
| Metric fetch | ~1s |
| LLM analysis | 10-15s |
| Alert delivery | 1-2s |
| **Total cycle** | **~15s** |
| Memory usage | ~200MB |

### Optimization Tips

1. **Reduce batch size:** Set `BATCH_MAX_METRICS=300`
2. **Use smaller model:** `LLM_MODEL=llama3.2:1b`
3. **Increase interval:** `BATCH_INTERVAL_MINUTES=5`
4. **Filter metrics:** Modify `prometheus_service.py` to skip unwanted metrics

---

## 🔒 Security

### Best Practices

- ✅ Store secrets in `.env` (never commit)
- ✅ Use MongoDB authentication in production
- ✅ Restrict CORS to known domains
- ✅ Use HTTPS for public deployments
- ✅ Rotate Slack webhooks regularly
- ✅ Use App Passwords for Gmail
- ✅ Keep dependencies updated: `pip install --upgrade -r requirements.txt`

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **FastAPI** - Modern async web framework
- **Prometheus** - Industry-standard metrics
- **MongoDB** - Flexible document storage
- **Ollama** - Easy local LLM deployment
- **Langfuse** - LLM observability

---

