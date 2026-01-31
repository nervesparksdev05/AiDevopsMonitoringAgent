# AI DevOps Monitoring Platform

**Multi-user intelligent infrastructure monitoring with AI-powered root cause analysis**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-6.0+-success.svg)](https://www.mongodb.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Production-ready SaaS platform for real-time monitoring with LLM-powered anomaly detection, batch analysis, and intelligent alerting

---

## 🎯 Overview

AI DevOps Monitor is a complete multi-user monitoring platform that collects Prometheus metrics and uses Large Language Models (LLM) to detect anomalies, identify root causes, and provide actionable remediation steps. Each user has their own isolated workspace with custom monitoring targets and notification settings.

### ✨ Key Features

- **👥 Multi-User Architecture** - Complete user isolation with JWT authentication
- **🤖 100% LLM-Powered Detection** - AI detects anomalies from raw metrics (no threshold rules)
- **📊 Batch Analysis** - Analyzes entire metric batches for holistic incident detection
- **🎯 Dynamic Target Management** - Add/remove monitoring targets via UI
- **🔔 User-Specific Alerts** - Email and Slack notifications per user
- **💾 Full Observability** - MongoDB storage with Langfuse LLM tracking
- **⚡ Production Ready** - Async operations, IST timezone support, comprehensive error handling
- **🎨 Modern UI** - Beautiful React frontend with real-time updates

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+** (for frontend)
- **MongoDB 6.0+**
- **Prometheus** (with Docker or standalone)
- **LLM Provider** (OpenAI or Ollama)

### 1. Backend Setup

```bash
# Clone repository
git clone https://github.com/yourusername/ai-devops-monitor.git
cd ai-devops-monitor

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings (see Configuration section)
```

### 2. Frontend Setup

```bash
cd frontend
npm install
```

### 3. Start Prometheus

```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Or start standalone Prometheus with prometheus.yml
```

### 4. Run the Application

```bash
# Terminal 1: Backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

### 5. Access the Application

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000/docs
- **Prometheus:** http://localhost:9090

---

## ⚙️ Configuration

### Environment Variables (.env)

```env
# ============================================
# CORE SERVICES
# ============================================
PROM_URL=http://localhost:9090
MONGO_URI=mongodb://localhost:27017
BATCH_INTERVAL_MINUTES=1

# ============================================
# LLM PROVIDER (Choose one)
# ============================================

# Option 1: OpenAI (Recommended for production)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Option 2: Ollama (Free, local)
# LLM_PROVIDER=ollama
# LLM_URL=http://localhost:11434
# LLM_MODEL=llama3.2

# ============================================
# AUTHENTICATION
# ============================================
JWT_SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# ============================================
# EMAIL ALERTS (Optional, per-user config)
# ============================================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# ============================================
# SLACK ALERTS (Optional, per-user config)
# ============================================
# Users configure their own webhooks in UI

# ============================================
# LANGFUSE TRACKING (Optional)
# ============================================
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

### Gmail App Password Setup

1. Enable 2-Step Verification: https://myaccount.google.com/security
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use the 16-character password in `SMTP_PASSWORD`

### Prometheus Configuration

The system uses **file-based service discovery** for dynamic targets:

**prometheus.yml:**
```yaml
global:
  scrape_interval: 5s

scrape_configs:
  - job_name: "dynamic-targets"
    file_sd_configs:
      - files:
          - "/etc/prometheus/targets.json"
        refresh_interval: 30s
```

**targets.json** (auto-managed by UI):
```json
[
  {
    "targets": ["192.168.1.4:9182"],
    "labels": {
      "job": "dynamic-targets",
      "name": "server",
      "user_id": "697db48e10965d8fb0ff3bb7"
    }
  }
]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./targets.json:/etc/prometheus/targets.json
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.enable-lifecycle'
    restart: unless-stopped

volumes:
  prometheus_data:
```

---

## 🏗️ Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────┐
│                  AI DevOps Monitor (Multi-User)              │
│                                                              │
│  React UI ──▶ FastAPI ──▶ MongoDB (User Isolation)         │
│      │           │                                           │
│   Register    JWT Auth                                       │
│   Login       Protected                                      │
│   Dashboard   Endpoints                                      │
│                │                                             │
│  Prometheus ──▶│──▶ LLM ──▶ Anomalies ──▶ Email/Slack      │
│   (per user)   │    AI       (per user)     (per user)      │
│                │                                             │
│  Targets ──────┘                                             │
│  (user_id)                                                   │
└──────────────────────────────────────────────────────────────┘
```

### Multi-User Data Isolation

Every data collection is filtered by `user_id`:

```python
# All queries include user filter
user_filter = {"user_id": user.id}

# Examples:
db.metrics_batches.find(user_filter)
db.anomalies.find(user_filter)
db.targets.find(user_filter)
db.email_config.find_one(user_filter)
```

### Batch Monitoring Flow (Per User)

```
Every 1 minute (per user):
1. Fetch metrics from Prometheus filtered by user_id label
2. Group by instance and build LLM prompt
3. LLM analyzes batch and detects anomalies
4. Store: batch → incident → anomalies → RCA (all with user_id)
5. Send alerts using user's email/Slack config
6. Track with Langfuse for observability
```

---

## 📱 User Guide

### Getting Started

1. **Register Account**
   - Visit http://localhost:5173
   - Click "Register"
   - Create username, email, and password
   - Auto-login after registration

2. **Add Monitoring Targets**
   - Go to Settings → Alerts & Servers
   - Click "Add Server"
   - Enter server IP and port (e.g., `192.168.1.4:9182`)
   - Give it a name
   - Click Save

3. **Configure Notifications**
   - **Email:** Settings → Email Config
     - Toggle "Enable Email Alerts"
     - Add recipient emails
     - Click "Test Email" to verify
   
   - **Slack:** Settings → Alerts & Servers
     - Enter Slack Webhook URL
     - Toggle "Enable Slack Alerts"
     - Click "Test Slack" to verify

4. **View Monitoring Data**
   - **Dashboard:** System overview and stats
   - **Metrics:** View all collected metric batches
   - **Anomalies:** AI-detected issues
   - **RCA Results:** Root cause analyses

### Adding Prometheus Targets

The system supports **Windows Exporter**, **Node Exporter**, or any Prometheus-compatible exporter:

**Windows Exporter:**
```powershell
# Download from https://github.com/prometheus-community/windows_exporter
# Run installer or use Chocolatey
choco install prometheus-windows-exporter.install

# Default port: 9182
# Add to UI: <your-ip>:9182
```

**Node Exporter (Linux):**
```bash
# Download from https://prometheus.io/download/#node_exporter
wget https://github.com/prometheus/node_exporter/releases/download/v*/node_exporter-*-linux-amd64.tar.gz
tar xvfz node_exporter-*-linux-amd64.tar.gz
cd node_exporter-*
./node_exporter

# Default port: 9100
# Add to UI: <your-ip>:9100
```

---

## 📚 API Documentation

### Authentication Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/auth/register` | POST | ❌ | Create new account |
| `/api/auth/login` | POST | ❌ | Login and get JWT |
| `/api/auth/me` | GET | ✅ | Get current user |

### Data Endpoints (All require authentication)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | System health check |
| `/stats` | GET | User's collection statistics |
| `/batches` | GET | User's metrics batches |
| `/anomalies` | GET | User's detected anomalies |
| `/rca` | GET | User's root cause analyses |
| `/incidents` | GET | User's detected incidents |

### Configuration Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/agent/email-config` | GET/PUT | User's email settings |
| `/agent/slack-config` | GET/PUT | User's Slack settings |
| `/agent/targets` | GET/POST/DELETE | User's Prometheus targets |
| `/agent/test-email` | POST | Send test email |
| `/agent/test-slack` | POST | Send test Slack message |

### Interactive API Docs

Visit http://localhost:8000/docs for full Swagger documentation with "Try it out" functionality.

---

## 🔍 How It Works

### LLM-Powered Detection

The system uses **pure AI detection** - no threshold rules or statistical methods:

1. **Fetch Metrics** - Queries Prometheus for user's targets
2. **Group by Instance** - Organizes metrics by server/service
3. **Build Prompt** - Creates structured prompt with time window and ALL metrics
4. **LLM Analysis** - AI analyzes the entire batch and decides what's anomalous
5. **Parse Response** - Extracts incident, anomalies, clusters from JSON
6. **Store Everything** - Saves to MongoDB with user_id
7. **Send Alerts** - Notifies via user's configured Email/Slack

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

### Example LLM Response

```json
{
  "incident": {
    "title": "High Memory Usage with Disk I/O Spikes",
    "severity": "high",
    "summary": "Memory at 92% with unusual disk write patterns",
    "root_cause": "Potential memory leak causing swap usage",
    "fix_plan": {
      "immediate": ["Restart affected service", "Check application logs"],
      "prevention": ["Add memory profiling", "Set up swap alerts"]
    }
  },
  "anomalies": [
    {
      "metric": "node_memory_MemAvailable_bytes",
      "instance": "192.168.1.4:9182",
      "observed": "800MB",
      "expected": "4GB average",
      "symptom": "Memory critically low"
    }
  ]
}
```

---

## 🔔 Alerting

### Email Alert Example

```
Subject: [HIGH] High Memory Usage with Disk I/O Spikes

🔴 HIGH INCIDENT
─────────────────
Window: 2026-01-31 15:20 → 15:21 IST

Summary: Memory at 92% with unusual disk write patterns

Root Cause: Potential memory leak causing swap usage

Immediate Actions:
• Restart affected service
• Check application logs

Anomalies: 2 | Confidence: 85%
```

### Slack Alert Example

```
🔴 [HIGH] High Memory Usage with Disk I/O Spikes
📅 Window: 2026-01-31 15:20 → 15:21 IST
📋 Memory at 92% with unusual disk write patterns
🔍 Root Cause: Potential memory leak causing swap usage
⚡ Actions: Restart affected service, Check application logs
📊 Anomalies: 2
```

---

## 🐛 Troubleshooting

### Prometheus Targets Not Loading

**Issue:** Dashboard shows 0 metric batches

**Check:**
1. Prometheus is running: http://localhost:9090/targets
2. `targets.json` is mounted in Docker container
3. Target server is accessible and running exporter

**Solution:**
```bash
# Restart Prometheus to reload targets
docker-compose restart prometheus

# Verify target is UP in Prometheus UI
# http://localhost:9090/targets
```

### Email/Slack Notifications Not Working

**Issue:** Alerts not being sent despite anomalies detected

**Reason:** Email/Slack configs are **per-user**, not global

**Solution:**
1. Login to your account
2. Go to Settings → Email Config or Alerts & Servers
3. Enable and configure your settings
4. Click "Test Email" or "Test Slack" to verify
5. Save configuration

The system will now use YOUR configured recipients/webhook, not the `.env` defaults.

### Dashboard Shows "Inactive" for Email/Slack

**Issue:** Configured email/Slack but dashboard shows inactive

**Solution:**
1. Refresh browser
2. Go to Settings and toggle OFF then ON
3. Click Save again
4. Return to Dashboard - should show "Active"

### No Anomalies Being Detected

**This is actually GOOD!** It means:
- ✅ Your system is healthy
- ✅ AI doesn't see any issues
- ✅ Everything is within normal operating parameters

The AI only alerts when it **genuinely** detects problems.

### Frontend Can't Connect to Backend

**Issue:** CORS errors or 401 Unauthorized

**Check:**
1. Backend is running on port 8000
2. Frontend is running on port 5173
3. You're logged in (check localStorage for token)

**Solution:**
```bash
# Backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend
cd frontend && npm run dev
```

---

## 📊 Data Storage

### MongoDB Collections

| Collection | Purpose | User-Specific |
|-----------|---------|---------------|
| `users` | User accounts | ✅ |
| `metrics_batches` | Prometheus metric snapshots | ✅ |
| `incidents` | AI-detected incidents | ✅ |
| `anomalies` | Individual anomalies | ✅ |
| `rca` | Root cause analyses | ✅ |
| `targets` | Prometheus targets | ✅ |
| `email_config` | Email settings | ✅ |
| `slack_config` | Slack settings | ✅ |
| `chat_sessions` | AI chat history | ✅ |

All collections (except `users`) include `user_id` field for data isolation.

---

## ⚡ Performance

### Benchmarks (1-minute batches, ~20 metrics)

| Metric | Value |
|--------|-------|
| Metric fetch | ~1s |
| LLM analysis (OpenAI) | 2-5s |
| LLM analysis (Ollama) | 10-15s |
| Alert delivery | 1-2s |
| **Total cycle** | **~5-15s** |
| Memory usage | ~200MB |
| Concurrent users | 20+ |

### Scaling Recommendations

- **1-10 users:** Single server setup (current)
- **10-50 users:** Add Redis for session management
- **50+ users:** Separate batch workers, load balancer
- **100+ users:** Kubernetes deployment, managed MongoDB

---

## 🔒 Security

### Current Implementation

- ✅ JWT authentication with Argon2 password hashing
- ✅ User data isolation via `user_id` filtering
- ✅ Protected API endpoints
- ✅ CORS configured for localhost
- ✅ HTTP-only cookies option available

### Production Hardening

See `production_auth_blueprint.md` for comprehensive security guide including:

- Rate limiting
- Strong JWT secrets
- Email verification
- Password reset flow
- 2FA/TOTP
- Session management
- HTTPS enforcement
- Secrets management

### Quick Security Wins

```bash
# 1. Generate strong JWT secret
python -c "import secrets; print(secrets.token_urlsafe(64))"
# Update JWT_SECRET_KEY in .env

# 2. Restrict CORS in production
# Edit app/main.py:
allow_origins=["https://yourdomain.com"]

# 3. Use environment-based config
ENVIRONMENT=production
FRONTEND_URL=https://yourdomain.com
```

---

## 🚀 Deployment

### Docker Deployment

```bash
# Build backend
docker build -t ai-devops-monitor .

# Run with docker-compose
docker-compose up -d
```

### Production Checklist

- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Generate strong `JWT_SECRET_KEY`
- [ ] Configure `FRONTEND_URL` to production domain
- [ ] Enable MongoDB authentication
- [ ] Set up HTTPS/SSL certificates
- [ ] Configure firewall rules
- [ ] Set up automated backups
- [ ] Test email/Slack alerts
- [ ] Monitor application logs
- [ ] Set up health check monitoring

---
## 🙏 Acknowledgments

- **FastAPI** - Modern async web framework
- **React** - Frontend UI library
- **Prometheus** - Industry-standard metrics
- **MongoDB** - Flexible document storage
- **OpenAI** - GPT models for analysis
- **Langfuse** - LLM observability and cost tracking
- **Argon2** - Secure password hashing

