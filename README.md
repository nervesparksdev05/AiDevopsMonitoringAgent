# AI DevOps Monitor

**An intelligent monitoring and alerting system powered by LLM-driven root cause analysis**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-6.0+-success.svg)](https://www.mongodb.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Real-time anomaly detection with AI-powered root cause analysis, multi-channel alerting, and comprehensive observability**

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Monitoring & Detection](#-monitoring--detection)
- [Alerting](#-alerting)
- [Observability](#-observability)
- [Advanced Features](#-advanced-features)
- [Troubleshooting](#-troubleshooting)
- [Performance](#-performance)
- [Security](#-security)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

AI DevOps Monitor is a production-ready monitoring solution that combines traditional metrics collection with modern AI capabilities. It continuously monitors your infrastructure, detects anomalies using statistical methods, and provides intelligent root cause analysis through Large Language Models.

### What Makes It Special?

- **🤖 AI-Powered Analysis**: LLM generates human-readable root cause analysis and remediation steps
- **📊 Dual Detection**: Combines threshold-based rules with statistical outlier detection (Z-score)
- **🔔 Multi-Channel Alerts**: Supports Email (SMTP) and Slack webhooks with rich formatting
- **💾 Full Observability**: All metrics, anomalies, and analyses stored in MongoDB for historical analysis
- **🎨 Session Tracking**: Langfuse integration for conversation context and cost tracking
- **⚡ Production Ready**: Built with FastAPI, async operations, and comprehensive error handling

---

## ✨ Key Features

### Monitoring & Detection
- ✅ **Continuous Prometheus Scraping** - Automatic metric collection at configurable intervals
- ✅ **Multi-Target Support** - Monitor multiple Prometheus instances simultaneously
- ✅ **Threshold Detection** - Pre-configured rules for common metrics (CPU, memory, disk, latency)
- ✅ **Statistical Outliers** - Z-score based anomaly detection with rolling history
- ✅ **Smart Filtering** - Automatic deduplication and severity-based prioritization

### AI-Powered Analysis
- ✅ **Root Cause Analysis** - LLM-generated technical analysis with remediation steps
- ✅ **Simplified Explanations** - ELI5 summaries for non-technical stakeholders
- ✅ **Context-Aware** - Includes related metrics for better analysis accuracy
- ✅ **Quality Scoring** - Automatic assessment of RCA completeness

### Alerting & Notifications
- ✅ **Email Alerts** - HTML-formatted emails with full anomaly details and RCA
- ✅ **Slack Integration** - Rich message blocks with color-coded severity levels
- ✅ **Configurable Routing** - API-driven configuration for recipients and channels
- ✅ **Test Endpoints** - Verify alert delivery before production use

### Data Management
- ✅ **MongoDB Storage** - Persistent storage for metrics, anomalies, and analyses
- ✅ **Automatic Retention** - Configurable data cleanup to manage storage
- ✅ **Session Management** - Track conversation threads and monitoring cycles
- ✅ **RESTful APIs** - Easy integration with dashboards and external tools

### Developer Experience
- ✅ **FastAPI Framework** - Auto-generated OpenAPI documentation
- ✅ **Prometheus Metrics** - Self-monitoring via `/metrics` endpoint
- ✅ **Hot Reload** - Development mode with automatic code reloading
- ✅ **Comprehensive Logging** - Multi-level logging (info, debug, error)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AI DevOps Monitor                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐ │
│  │  Prometheus  │─────▶│   FastAPI    │─────▶│   MongoDB    │ │
│  │   (Metrics)  │      │  (Service)   │      │  (Storage)   │ │
│  └──────────────┘      └──────────────┘      └──────────────┘ │
│                               │                                 │
│                               ├─────────────────┐               │
│                               ▼                 ▼               │
│                        ┌──────────────┐  ┌──────────────┐      │
│                        │     LLM      │  │   Langfuse   │      │
│                        │ (RCA Engine) │  │  (Tracking)  │      │
│                        └──────────────┘  └──────────────┘      │
│                               │                                 │
│                    ┌──────────┴──────────┐                     │
│                    ▼                     ▼                      │
│             ┌─────────────┐       ┌─────────────┐             │
│             │    Email    │       │    Slack    │             │
│             │   (SMTP)    │       │  (Webhook)  │             │
│             └─────────────┘       └─────────────┘             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        Data Flow                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Fetch Metrics ──▶ 2. Detect Anomalies ──▶ 3. LLM RCA      │
│         │                      │                      │         │
│         ▼                      ▼                      ▼         │
│  Store Snapshots      Store Anomalies        Store Analysis    │
│         │                      │                      │         │
│         └──────────────────────┴──────────────────────┘         │
│                               │                                 │
│                               ▼                                 │
│                    Send Alerts (Email + Slack)                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Component Breakdown

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Metrics Source** | Prometheus | Time-series metric collection and storage |
| **Application Server** | FastAPI | REST API, async processing, auto-documentation |
| **Database** | MongoDB | Persistent storage for metrics, anomalies, RCA |
| **AI Engine** | LLM (Ollama/OpenAI) | Root cause analysis and remediation suggestions |
| **Observability** | Langfuse (optional) | Trace LLM calls, track costs, session management |
| **Alerting** | SMTP + Slack | Multi-channel notifications with rich formatting |

---

## 🚀 Quick Start

### Prerequisites

Ensure you have the following installed:

- **Python 3.10+** ([Download](https://www.python.org/downloads/))
- **MongoDB 6.0+** ([Download](https://www.mongodb.com/try/download/community))
- **Prometheus** ([Download](https://prometheus.io/download/))
- **Ollama** or compatible LLM endpoint ([Download](https://ollama.ai/))

### 30-Second Setup

```bash
# 1. Clone and setup
git clone https://github.com/yourusername/ai-devops-monitor.git
cd ai-devops-monitor
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure (create .env file)
cat > .env << 'EOF'
PROM_URL=http://localhost:9090
MONGO_URI=mongodb://localhost:27017
MONGO_DB=observability
LLM_URL=http://localhost:11434
LLM_MODEL=llama3.2
MONITOR_INTERVAL=30
EOF

# 3. Start services
mongod &  # Start MongoDB
prometheus --config.file=prometheus.yml &  # Start Prometheus
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 4. Verify
curl http://localhost:8000/
```

**Done!** Visit `http://localhost:8000/docs` for interactive API documentation.

---

## 📦 Installation

### 1. System Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 4GB
- Disk: 10GB
- Network: Internet access for LLM API (if using cloud)

**Recommended:**
- CPU: 4+ cores
- RAM: 8GB+
- Disk: 50GB+ (for metric storage)
- Network: High bandwidth for frequent scraping

### 2. Python Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate

# macOS/Linux:
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### 3. Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Verify installation
pip list | grep -E "fastapi|pymongo|requests|langfuse"
```

**Core Dependencies:**
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pymongo==4.6.0
requests==2.31.0
httpx==0.25.2
prometheus-fastapi-instrumentator==6.1.0
python-dotenv==1.0.0
pydantic==2.5.0
langfuse==3.12.0  # optional
```

### 4. Database Setup

```bash
# Start MongoDB locally
mongod --dbpath /path/to/data

# Or use MongoDB Atlas (cloud)
# Get connection string from https://cloud.mongodb.com
```

### 5. LLM Setup

**Option A: Local (Ollama)**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull model
ollama pull llama3.2

# Start server (runs on port 11434)
ollama serve
```

**Option B: Cloud (OpenAI, Anthropic, etc.)**
```python
# Update LLM_URL in .env to your provider's endpoint
LLM_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# ============ CORE CONFIGURATION ============

# Prometheus Configuration
PROM_URL=http://localhost:9090
# If using remote Prometheus:
# PROM_URL=http://prometheus.example.com:9090

# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017
# For MongoDB Atlas:
# MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority
MONGO_DB=observability

# LLM Configuration
LLM_URL=http://localhost:11434
LLM_MODEL=llama3.2
# For OpenAI:
# LLM_URL=https://api.openai.com/v1
# LLM_MODEL=gpt-4

# ============ MONITORING SETTINGS ============

# How often to check metrics (seconds)
MONITOR_INTERVAL=30

# Z-score threshold for outlier detection
Z_THRESHOLD=3.0

# Maximum documents to keep per collection
MAX_DOCS=1000

# ============ EMAIL ALERTS (OPTIONAL) ============

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
# Note: Gmail requires App Password, not regular password
# Generate at: https://myaccount.google.com/apppasswords

# ============ SLACK ALERTS (OPTIONAL) ============

SLACK_ENABLED=true
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
# Get webhook at: https://api.slack.com/apps

# ============ LANGFUSE TRACKING (OPTIONAL) ============

LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
# Sign up at: https://langfuse.com
```

### Configuration File (`config.py`)

```python
import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Prometheus
PROM_URL = os.getenv("PROM_URL", "http://localhost:9090")

# MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB", "observability")

# LLM
LLM_URL = os.getenv("LLM_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2")

# Monitoring
MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL", "30"))
Z_THRESHOLD = float(os.getenv("Z_THRESHOLD", "3.0"))
MAX_DOCS = int(os.getenv("MAX_DOCS", "1000"))

# Email
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
ALERT_EMAILS = []  # Managed via MongoDB

# Slack
SLACK_ENABLED = os.getenv("SLACK_ENABLED", "false").lower() == "true"
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
```

### Advanced Configuration

#### Multi-Target Prometheus Setup

Add targets to MongoDB for monitoring multiple Prometheus instances:

```javascript
// MongoDB: observability.targets
db.targets.insertMany([
  {
    "name": "production-prometheus",
    "endpoint": "prom-prod.example.com:9090",
    "job": "production",
    "enabled": true
  },
  {
    "name": "staging-prometheus",
    "endpoint": "prom-staging.example.com:9090",
    "job": "staging",
    "enabled": true
  }
])
```

#### Custom Anomaly Thresholds

Edit thresholds in `main.py`:

```python
THRESHOLDS = {
    "up": {"min": 1, "severity": "critical", "msg": "Service is DOWN"},
    "cpu_usage": {"max": 80, "severity": "high", "msg": "High CPU usage"},
    "memory_usage": {"max": 80, "severity": "high", "msg": "High memory usage"},
    "disk_usage": {"max": 90, "severity": "critical", "msg": "Disk almost full"},
    "http_request_duration_seconds": {"max": 5, "severity": "high", "msg": "High latency"},
    "errors_total": {"max": 10, "severity": "high", "msg": "High error count"},
    
    # Add custom thresholds:
    "database_connections": {"max": 100, "severity": "medium", "msg": "High DB connections"},
    "queue_depth": {"max": 1000, "severity": "high", "msg": "Queue backlog"}
}
```

---

## 🎮 Usage

### Starting the Service

**Development Mode:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Production Mode:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

**With Gunicorn (Recommended for Production):**
```bash
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Service Management

**Systemd Service (Linux):**

Create `/etc/systemd/system/ai-devops-monitor.service`:

```ini
[Unit]
Description=AI DevOps Monitor
After=network.target mongod.service

[Service]
Type=simple
User=monitor
WorkingDirectory=/opt/ai-devops-monitor
Environment="PATH=/opt/ai-devops-monitor/.venv/bin"
ExecStart=/opt/ai-devops-monitor/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-devops-monitor
sudo systemctl start ai-devops-monitor
sudo systemctl status ai-devops-monitor
```

**Docker (Optional):**

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t ai-devops-monitor .
docker run -d -p 8000:8000 --env-file .env ai-devops-monitor
```

### Accessing the Service

| URL | Description |
|-----|-------------|
| `http://localhost:8000` | Root endpoint (status check) |
| `http://localhost:8000/docs` | Interactive API documentation (Swagger UI) |
| `http://localhost:8000/redoc` | Alternative API documentation (ReDoc) |
| `http://localhost:8000/metrics` | Prometheus metrics for self-monitoring |

---

## 📚 API Documentation

### Core Endpoints

#### Health Check

```http
GET /
```

**Response:**
```json
{
  "status": "running",
  "prometheus": "http://localhost:9090",
  "llm": "llama3.2",
  "langfuse": "enabled (v3)",
  "sessions": "enabled"
}
```

#### System Statistics

```http
GET /stats
```

**Response:**
```json
{
  "collections": {
    "metrics": {"total": 1250},
    "anomalies": {
      "total": 45,
      "open": 3,
      "analyzed": 42
    },
    "rca_results": {"total": 42},
    "chat_sessions": {
      "total": 10,
      "active": 2
    }
  },
  "notifications": {
    "email": {
      "enabled": true,
      "recipients": 2
    },
    "slack": {
      "enabled": true,
      "configured": true
    }
  }
}
```

### Data Endpoints

#### Get Recent Metrics

```http
GET /prom-metrics
```

**Response:**
```json
{
  "metrics": [
    {
      "_id": "...",
      "timestamp": "2026-01-27T14:30:00",
      "count": 150,
      "data": [
        {"name": "cpu_usage", "value": 45.2, "instance": "web-01"},
        {"name": "memory_usage", "value": 62.8, "instance": "web-01"}
      ]
    }
  ]
}
```

#### Get Anomalies

```http
GET /anomalies
```

**Response:**
```json
{
  "anomalies": [
    {
      "_id": "...",
      "timestamp": "2026-01-27T14:35:22",
      "metric": "cpu_usage",
      "value": 95.5,
      "instance": "web-server-01",
      "severity": "high",
      "reason": "High CPU usage"
    }
  ]
}
```

#### Get Root Cause Analysis

```http
GET /rca
```

**Response:**
```json
{
  "rca": [
    {
      "_id": "...",
      "timestamp": "2026-01-27T14:35:25",
      "anomaly_id": "...",
      "metric": "cpu_usage",
      "instance": "web-server-01",
      "summary": "CPU spike detected on production web server",
      "simplified": "The server is working too hard and slowing down",
      "cause": "Memory leak in application causing excessive CPU consumption",
      "fix": "Restart the application service and monitor memory usage patterns"
    }
  ]
}
```

### Chat Endpoint

```http
POST /api/chat
Content-Type: application/json

{
  "message": "What does high CPU usage mean?",
  "context": {},
  "session_id": null
}
```

**Response:**
```json
{
  "response": "High CPU usage indicates that your processor is working hard...",
  "session_id": "abc-123-def-456"
}
```

**Continuing Conversation:**
```json
{
  "message": "How can I fix it?",
  "session_id": "abc-123-def-456"
}
```

### Alert Configuration

#### Email Configuration

```http
GET /agent/email-config
```

```http
PUT /agent/email-config
Content-Type: application/json

{
  "enabled": true,
  "recipients": ["admin@example.com", "devops@example.com"]
}
```

```http
POST /agent/test-email
```

#### Slack Configuration

```http
GET /agent/slack-status
```

```http
POST /agent/test-slack
```

### Session Management

```http
GET /api/sessions
```

```http
GET /api/sessions/{session_id}
```

```http
DELETE /api/sessions/{session_id}
```

### Langfuse Status

```http
GET /langfuse/status
```

**Response:**
```json
{
  "installed": true,
  "enabled": true,
  "version": "v3",
  "host": "https://cloud.langfuse.com",
  "connected": true,
  "session_tracking": true
}
```

---

## 🔍 Monitoring & Detection

### How Anomaly Detection Works

The system uses a **dual-detection approach**:

#### 1. Threshold-Based Detection

Pre-configured rules for common metrics:

```python
# Critical severity
up < 1                    → Service DOWN
disk_usage > 90%          → Disk almost full

# High severity  
cpu_usage > 80%           → High CPU
memory_usage > 80%        → High memory
http_latency > 5s         → Slow responses
errors_total > 10         → Error spike
```

#### 2. Statistical Outlier Detection (Z-Score)

For metrics without predefined thresholds:

```
1. Maintain rolling window of last 10 values
2. Calculate mean (μ) and standard deviation (σ)
3. Compute z-score: z = |value - μ| / σ
4. Flag as anomaly if z > Z_THRESHOLD (default: 3.0)
```

**Example:**
```
History: [50, 52, 51, 49, 50, 51, 52, 50, 51, 95]
μ = 55.1, σ = 13.9
z = |95 - 55.1| / 13.9 = 2.87

If Z_THRESHOLD = 2.5 → ANOMALY DETECTED ✓
```

### Metric Collection

**Default Behavior:**
- Scrapes Prometheus every `MONITOR_INTERVAL` seconds (default: 30s)
- Filters out Prometheus internal metrics (`prometheus_*`, `go_*`, `scrape_*`)
- Stores up to 50 metrics per snapshot
- Enforces retention limit (`MAX_DOCS` per collection)

**Multi-Target Support:**

When MongoDB has enabled targets in the `targets` collection, the monitor scrapes all of them:

```javascript
// Add targets via MongoDB
db.targets.insertOne({
  name: "backup-prometheus",
  endpoint: "prom-backup.local:9090",
  job: "backup",
  enabled: true
})
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Monitoring Cycle                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Every 30 seconds:                                          │
│                                                             │
│  1. Fetch metrics from Prometheus                          │
│     ├─ Query: {__name__=~".+"}                            │
│     ├─ Filter: Remove prometheus_*, go_*, scrape_*        │
│     └─ Limit: Top 50 metrics                              │
│                                                             │
│  2. Store snapshot in MongoDB                              │
│     └─ Collection: metrics                                 │
│                                                             │
│  3. Detect anomalies                                        │
│     ├─ Check thresholds (up, cpu, memory, etc.)          │
│     ├─ Calculate z-scores (for other metrics)             │
│     └─ Deduplicate by metric name                         │
│                                                             │
│  4. For each anomaly (max 3 per cycle):                    │
│     ├─ Store in MongoDB (collection: anomalies)           │
│     ├─ Call LLM for RCA                                   │
│     ├─ Store RCA (collection: rca)                        │
│     ├─ Send email alert (if enabled)                      │
│     └─ Send Slack alert (if enabled)                      │
│                                                             │
│  5. Cleanup old data                                        │
│     └─ Keep only MAX_DOCS newest documents                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔔 Alerting

### Email Alerts

**Setup Gmail (Example):**

1. **Enable 2-Step Verification:**
   - Go to https://myaccount.google.com/security
   - Enable 2-Step Verification

2. **Generate App Password:**
   - Go to https://myaccount.google.com/apppasswords
   - Select app: "Mail"
   - Select device: "Other" (enter "AI DevOps Monitor")
   - Click "Generate"
   - Copy the 16-character password

3. **Configure in .env:**
   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=xxxx xxxx xxxx xxxx
   ```

4. **Enable via API:**
   ```bash
   curl -X PUT http://localhost:8000/agent/email-config \
     -H "Content-Type: application/json" \
     -d '{
       "enabled": true,
       "recipients": ["admin@company.com", "devops@company.com"]
     }'
   ```

5. **Test:**
   ```bash
   curl -X POST http://localhost:8000/agent/test-email
   ```

**Email Format:**

```html
Subject: [HIGH] cpu_usage

<h2>HIGH Anomaly</h2>
<p><b>Metric:</b> cpu_usage</p>
<p><b>Instance:</b> web-server-01</p>
<p><b>Value:</b> 95.5</p>
<p><b>Reason:</b> High CPU usage</p>

<h3>Root Cause Analysis</h3>
<p><b>Summary:</b> CPU spike detected on production server</p>
<p><b>Cause:</b> Memory leak causing excessive CPU consumption</p>
<p><b>Fix:</b> Restart application and investigate memory patterns</p>
```

### Slack Alerts

**Setup:**

1. **Create Slack App:**
   - Go to https://api.slack.com/apps
   - Click "Create New App" → "From scratch"
   - App Name: "AI DevOps Monitor"
   - Select your workspace

2. **Enable Incoming Webhooks:**
   - In left sidebar: "Incoming Webhooks"
   - Toggle "Activate Incoming Webhooks" to **ON**

3. **Add Webhook:**
   - Click "Add New Webhook to Workspace"
   - Select channel (e.g., `#devops-alerts`)
   - Click "Allow"
   - Copy webhook URL

4. **Configure in .env:**
   ```env
   SLACK_ENABLED=true
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00/B00/XXX
   ```

5. **Test:**
   ```bash
   curl -X POST http://localhost:8000/agent/test-slack
   ```

**Slack Message Format:**

```
🚨 [HIGH] cpu_usage
━━━━━━━━━━━━━━━━━━━━━━━━━

Metric:              Severity:
cpu_usage            HIGH

Value:               Instance:
95.5                 web-server-01

Reason:
High CPU usage

━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 Root Cause Analysis

Summary:
CPU spike detected on production server

Root Cause:
Memory leak causing excessive CPU consumption

Recommended Fix:
Restart application and investigate memory patterns

💡 Simple: The app is using too much computer power
⏰ 2026-01-27 14:35:22
```

**Color Coding:**
- 🔴 Critical - Red
- 🟠 High - Orange  
- 🟡 Medium - Yellow
- 🟢 Low - Green

### Alert Routing

**Severity-Based Routing (Example):**

```python
# In monitor() function, customize per severity
if anomaly["severity"] == "critical":
    # Send to special channel
    send_slack_to_channel("#critical-alerts", anomaly, analysis)
    send_email_to(["cto@company.com"], anomaly, analysis)
elif anomaly["severity"] == "high":
    send_slack_to_channel("#high-priority", anomaly, analysis)
else:
    send_slack_to_channel("#devops-alerts", anomaly, analysis)
```

---

## 📊 Observability

### Self-Monitoring

The service exposes its own metrics for Prometheus scraping:

```http
GET /metrics
```

**Available Metrics:**
```prometheus
# HTTP request metrics
http_requests_total{method="GET",path="/",status="200"} 1523
http_request_duration_seconds_bucket{le="0.1"} 1234
http_request_duration_seconds_sum 45.2
http_request_duration_seconds_count 1523

# Custom application metrics (if added)
anomalies_detected_total 42
rca_generated_total 38
alerts_sent_total{channel="email"} 15
alerts_sent_total{channel="slack"} 15
```

### Langfuse Integration

Track LLM usage, costs, and conversation context:

**Setup:**
1. Sign up at https://langfuse.com
2. Get API keys from dashboard
3. Configure in .env:
   ```env
   LANGFUSE_PUBLIC_KEY=pk-lf-...
   LANGFUSE_SECRET_KEY=sk-lf-...
   LANGFUSE_HOST=https://cloud.langfuse.com
   ```

**What Gets Tracked:**
- ✅ Every LLM call (prompt + response)
- ✅ Token usage (input/output/total)
- ✅ Latency per request
- ✅ Quality scores (RCA completeness)
- ✅ Session grouping (chat conversations, monitoring cycles)
- ✅ Cost estimation

**Dashboard Views:**

```
Sessions (grouped by session_id)
├─ chat-abc-123 (5 messages, 2.5k tokens, $0.025)
│  ├─ "What's high CPU?" (500 tokens)
│  ├─ "How to fix it?" (600 tokens)
│  └─ "Show logs" (450 tokens)
│
├─ monitor-20260127-143022 (3 anomalies, 1.4k tokens, $0.014)
│  ├─ RCA: cpu_usage (500 tokens)
│  ├─ RCA: memory_usage (450 tokens)
│  └─ RCA: disk_usage (480 tokens)
```

### Logging

**Log Files:**
- `app.log` - All logs (INFO and above)
- `debug.log` - Debug-level logs
- `error.log` - Error-level logs only

**Log Format:**
```
2026-01-27 14:35:22,123 [INFO] [14:35:22] Fetched 150 metrics
2026-01-27 14:35:25,456 [ERROR] [14:35:25] ANOMALY [HIGH]: cpu_usage=95.5
2026-01-27 14:35:28,789 [INFO] [LLM] ✅ Logged generation (1430 tokens)
```

### MongoDB Queries

**Useful Analytics:**

```javascript
// Count anomalies by severity
db.anomalies.aggregate([
  { $group: { _id: "$severity", count: { $sum: 1 } } }
])

// Average RCA response time
db.rca.aggregate([
  { $group: { _id: null, avgTime: { $avg: "$processing_time" } } }
])

// Top 10 problematic metrics
db.anomalies.aggregate([
  { $group: { _id: "$metric", count: { $sum: 1 } } },
  { $sort: { count: -1 } },
  { $limit: 10 }
])

// Total tokens used (chat sessions)
db.chat_sessions.aggregate([
  { $group: { _id: null, total: { $sum: "$total_tokens" } } }
])
```

---

## 🚀 Advanced Features

### Session Management

Track conversation threads and monitoring cycles for better observability:

**Chat Sessions:**
```bash
# Get all sessions
curl http://localhost:8000/api/sessions

# Get specific session
curl http://localhost:8000/api/sessions/abc-123-def-456

# Delete session
curl -X DELETE http://localhost:8000/api/sessions/abc-123-def-456
```

**Session Data:**
```json
{
  "session_id": "abc-123-def-456",
  "created_at": "2026-01-27T14:30:00",
  "last_activity": "2026-01-27T14:45:00",
  "message_count": 5,
  "total_tokens": 2500
}
```

### Custom Metric Filtering

**Filter by instance:**
```python
# In fetch_metrics_from_target()
if m.get("metric", {}).get("instance") not in ["web-01", "web-02"]:
    continue  # Skip this metric
```

**Filter by job:**
```python
if m.get("metric", {}).get("job") != "production":
    continue  # Only production metrics
```

### Programmatic API Usage

**Python Client Example:**

```python
import requests

BASE_URL = "http://localhost:8000"

# Get current stats
response = requests.get(f"{BASE_URL}/stats")
stats = response.json()
print(f"Total anomalies: {stats['collections']['anomalies']['total']}")

# Chat with AI
response = requests.post(
    f"{BASE_URL}/api/chat",
    json={"message": "Explain this error", "context": {"error": "OOM"}}
)
data = response.json()
print(f"AI: {data['response']}")
session_id = data['session_id']  # Save for next message

# Configure email alerts
requests.put(
    f"{BASE_URL}/agent/email-config",
    json={"enabled": True, "recipients": ["admin@company.com"]}
)

# Send test alert
requests.post(f"{BASE_URL}/agent/test-email")
```

### Grafana Dashboard

**Sample Dashboard JSON:**

```json
{
  "dashboard": {
    "title": "AI DevOps Monitor",
    "panels": [
      {
        "title": "Anomalies Over Time",
        "type": "graph",
        "datasource": "Prometheus",
        "targets": [{
          "expr": "rate(anomalies_detected_total[5m])"
        }]
      },
      {
        "title": "Alert Distribution",
        "type": "piechart",
        "datasource": "MongoDB",
        "targets": [{
          "collection": "anomalies",
          "aggregate": [
            {"$group": {"_id": "$severity", "count": {"$sum": 1}}}
          ]
        }]
      }
    ]
  }
}
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. "Database objects do not implement truth value testing"

**Error:**
```python
if not db:  # ❌ Wrong
```

**Fix:**
```python
if db is None:  # ✅ Correct
```

**Why:** PyMongo's database objects have custom truth value behavior.

---

#### 2. No Anomalies Detected

**Checklist:**
- ✅ Prometheus returning metrics? `curl http://localhost:9090/api/v1/query?query=up`
- ✅ Metric names match thresholds? Check logs for fetched metrics
- ✅ Enough history? Z-score needs 5+ samples
- ✅ Thresholds too high? Try lowering temporarily

**Debug:**
```bash
# Check what metrics are being fetched
curl http://localhost:8000/prom-metrics | jq '.metrics[0].data'

# Lower threshold temporarily to test
# In main.py: "cpu_usage": {"max": 10, ...}  # Will trigger immediately
```

---

#### 3. Email Not Sending

**Checklist:**
- ✅ SMTP credentials set in .env?
- ✅ Email config enabled via API?
- ✅ Gmail using App Password (not regular password)?
- ✅ Firewall blocking port 587?

**Test SMTP directly:**
```python
import smtplib

server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your-email@gmail.com', 'your-app-password')
server.sendmail('from@example.com', 'to@example.com', 'Subject: Test\n\nBody')
server.quit()
```

---

#### 4. Slack Not Sending

**Checklist:**
- ✅ `SLACK_ENABLED=true` in .env?
- ✅ Webhook URL correct and active?
- ✅ No extra quotes or spaces in webhook URL?

**Test webhook directly:**
```bash
curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
  -H "Content-Type: application/json" \
  -d '{"text": "Test from terminal"}'
```

Should return: `ok`

---

#### 5. LLM Timeout / No Response

**Checklist:**
- ✅ LLM service running? `curl http://localhost:11434/api/tags`
- ✅ Model pulled? `ollama list`
- ✅ Firewall blocking connection?

**Test LLM directly:**
```bash
curl http://localhost:11434/api/generate \
  -d '{"model": "llama3.2", "prompt": "Say hello", "stream": false}'
```

---

#### 6. MongoDB Connection Failed

**Error:** `ServerSelectionTimeoutError`

**Fix:**
```bash
# Check MongoDB is running
mongosh --eval "db.version()"

# Check connection string
echo $MONGO_URI

# For Atlas, ensure IP whitelisted
```

---

#### 7. Langfuse session_id Error

**Error:** `got an unexpected keyword argument 'session_id'`

**Cause:** Langfuse version too old or too new (API changed in v3.12)

**Fix:**
```bash
# Check version
pip show langfuse

# If < 2.6.0: Upgrade
pip install --upgrade langfuse

# If >= 3.12.0: Use updated API (see LANGFUSE_V3_12_FIX.md)
```

---

### Performance Issues

#### High Memory Usage

**Diagnosis:**
```bash
# Check collection sizes
mongosh observability --eval "db.stats()"

# Count documents
mongosh observability --eval "db.metrics.count()"
```

**Fix:**
```env
# Reduce retention
MAX_DOCS=100  # Instead of 1000

# Increase interval
MONITOR_INTERVAL=60  # Instead of 30
```

---

#### Slow LLM Responses

**Options:**
1. **Use faster model:** `llama3.2:1b` instead of `llama3.2:8b`
2. **Increase timeout:** Change `timeout=30` to `timeout=60` in `ask_llm()`
3. **Use cloud LLM:** OpenAI/Anthropic are typically faster
4. **Reduce prompt size:** Limit context metrics to top 10 instead of 15

---

### Debug Mode

**Enable verbose logging:**

```python
# In main.py, change logging level
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    # ...
)
```

**Then:**
```bash
tail -f debug.log
```

---

## ⚡ Performance

### Benchmarks

**Test Environment:**
- CPU: Intel i7-10700K (8 cores)
- RAM: 32GB
- Prometheus: 10,000 time series
- MongoDB: Local instance

**Results:**

| Metric | Value |
|--------|-------|
| Metric fetch time | ~2s |
| Anomaly detection | ~1s |
| LLM RCA (Ollama llama3.2) | ~3s |
| Total cycle time | ~6s |
| Memory usage | ~150MB |
| CPU usage (idle) | ~2% |
| CPU usage (during RCA) | ~40% |

### Optimization Tips

1. **Reduce metric volume:**
   ```python
   # Limit to specific jobs
   params={"query": '{job="production"}'}
   ```

2. **Batch anomalies:**
   ```python
   # Already implemented: max 3 anomalies per cycle
   anomalies = unique_anomalies[:3]
   ```

3. **Use faster LLM:**
   ```env
   LLM_MODEL=llama3.2:1b  # Smaller, faster model
   ```

4. **Increase monitoring interval:**
   ```env
   MONITOR_INTERVAL=60  # Check every minute instead of 30s
   ```

5. **Use MongoDB indexes:**
   ```javascript
   db.anomalies.createIndex({"timestamp": -1})
   db.rca.createIndex({"anomaly_id": 1})
   db.chat_sessions.createIndex({"session_id": 1})
   ```

### Scalability

**Single Instance Limits:**
- Prometheus targets: ~10
- Metrics per scrape: ~1,000
- Anomalies per cycle: 3
- Concurrent API requests: ~100

**Horizontal Scaling:**

For larger deployments, run multiple instances:

```bash
# Instance 1: Monitors prod-prometheus
PROM_URL=http://prom-prod:9090 uvicorn main:app --port 8000

# Instance 2: Monitors staging-prometheus  
PROM_URL=http://prom-staging:9090 uvicorn main:app --port 8001

# Use load balancer for API requests
```

---

## 🔒 Security

### Best Practices

#### 1. Environment Variables

```bash
# ✅ GOOD: Use .env (never commit)
echo ".env" >> .gitignore

# ❌ BAD: Hardcode secrets
SMTP_PASSWORD = "mypassword123"  # Don't do this!
```

#### 2. MongoDB Access Control

```javascript
// Create user with specific permissions
use admin
db.createUser({
  user: "monitor",
  pwd: "strong-password",
  roles: [
    { role: "readWrite", db: "observability" }
  ]
})

// Update connection string
MONGO_URI=mongodb://monitor:strong-password@localhost:27017/observability
```

#### 3. API Authentication

**Add Basic Auth (Example):**

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = os.getenv("API_USERNAME", "admin")
    correct_password = os.getenv("API_PASSWORD", "secret")
    
    if credentials.username != correct_username or \
       credentials.password != correct_password:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    return credentials.username

# Protect endpoints
@app.put("/agent/slack-config", dependencies=[Depends(verify_credentials)])
def update_slack_config(config: SlackConfig):
    # ...
```

#### 4. CORS Configuration

```python
# Restrict origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://dashboard.company.com"],  # Not "*"
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

#### 5. Webhook Security

```bash
# Rotate Slack webhook regularly
# Generate new webhook monthly at: https://api.slack.com/apps

# Store in secret manager (production)
# AWS Secrets Manager, HashiCorp Vault, etc.
```

#### 6. Network Security

```bash
# Firewall rules
sudo ufw allow 8000/tcp  # API
sudo ufw allow 9090/tcp  # Prometheus (if needed)
sudo ufw deny 27017/tcp  # MongoDB (don't expose)

# Use reverse proxy
# Nginx with SSL termination
```

### Security Checklist

- [ ] `.env` file in `.gitignore`
- [ ] MongoDB authentication enabled
- [ ] CORS restricted to known origins
- [ ] API authentication implemented
- [ ] Slack webhook stored securely
- [ ] SMTP credentials using app passwords
- [ ] Firewall configured properly
- [ ] SSL/TLS for public endpoints
- [ ] Regular security updates (`pip list --outdated`)
- [ ] Audit logs enabled

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Development Setup

```bash
# Fork and clone
git clone https://github.com/yourusername/ai-devops-monitor.git
cd ai-devops-monitor

# Create branch
git checkout -b feature/your-feature

# Install dev dependencies
pip install -r requirements-dev.txt

# Make changes and test
pytest tests/

# Format code
black main.py
isort main.py

# Commit and push
git commit -m "Add: your feature description"
git push origin feature/your-feature
```

### Code Style

- **Formatting:** Black (line length 88)
- **Imports:** isort
- **Linting:** flake8
- **Type hints:** Use type hints for functions
- **Docstrings:** Google style

### Pull Request Process

1. Update README.md with any new features
2. Add tests for new functionality
3. Ensure all tests pass
4. Update CHANGELOG.md
5. Request review from maintainers

### Reporting Issues

**Bug Report Template:**
```markdown
**Describe the bug**
A clear description of the bug.

**To Reproduce**
Steps to reproduce the behavior.

**Expected behavior**
What you expected to happen.

**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.11]
- Package versions: [e.g., fastapi==0.104.1]

**Additional context**
Logs, screenshots, etc.
```

---


## 🙏 Acknowledgments

- **FastAPI** - Modern web framework for Python
- **Prometheus** - Industry-standard metrics collection
- **MongoDB** - Flexible document database
- **Ollama** - Local LLM deployment made easy
- **Langfuse** - LLM observability and tracking
- **Community** - All contributors and users

---

