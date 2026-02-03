# AI DevOps Monitoring Platform

**Multi-user intelligent infrastructure monitoring with AI-powered root cause analysis**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-6.0+-success.svg)](https://www.mongodb.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)

> Production-ready SaaS platform for real-time monitoring with LLM-powered anomaly detection, batch analysis, and intelligent alerting

---

## 🔥 Recent Updates

### v2.1.0 - February 2026
- **🤖 OpenAI Integration**: Primary LLM now uses OpenAI (gpt-4o-mini) with automatic fallback to Gemma3
- **🔄 Intelligent Fallback**: System continues working even if OpenAI is unavailable
- **🐛 Bug Fix**: Resolved target deletion issue - deleted servers now properly removed from `targets.json`
- **📊 Enhanced Logging**: Better error tracking and debugging for LLM calls and target management

---

## 🎯 Overview

AI DevOps Monitor is a complete multi-user monitoring platform that collects Prometheus metrics and uses Large Language Models (OpenAI + Gemma3) to detect anomalies, identify root causes, and provide actionable remediation steps. Each user has their own isolated workspace with custom monitoring targets and notification settings.

### ✨ Key Features

- **👥 Multi-User Architecture** - Complete user isolation with JWT authentication
- **🔐 Session Management** - JWT-based sessions with device tracking and remote revocation
- **🤖 100% LLM-Powered Detection** - AI detects anomalies from raw metrics (no threshold rules)
- **📊 Batch Analysis** - Analyzes entire metric batches for holistic incident detection
- **🎯 Dynamic Target Management** - Add/remove monitoring targets via UI
- **📈 Grafana Integration** - Universal dashboard for visualizing metrics across all exporters
- **💬 AI Chat Assistant** - Interactive chat for querying metrics and getting insights
- **🔔 User-Specific Alerts** - Email and Slack notifications per user
- **💾 Full Observability** - MongoDB storage with Langfuse LLM tracking
- **⚡ Production Ready** - Async operations, IST timezone support, comprehensive error handling
- **🎨 Modern UI** - Beautiful React frontend with real-time updates and enhanced validation

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

### 3. Start Prometheus & Grafana

```bash
# Using Docker Compose (recommended)
docker-compose up -d

# This starts:
# - Prometheus (port 9090)
# - Grafana (port 3000)

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
- **Grafana:** http://localhost:3000 (default login: admin/admin)

---

## ⚙️ Configuration

### Environment Variables (.env)

```env
# ============================================
# CORE SERVICES
# ============================================
PROM_URL=http://localhost:9090
MONGO_URI=mongodb://localhost:27017
MONGO_DB=observability
BATCH_INTERVAL_MINUTES=5

# ============================================
# LLM CONFIGURATION (Primary + Fallback)
# ============================================

# Primary LLM: OpenAI (Recommended for production)
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini

# Fallback LLM: Gemma3 via Ollama (Automatic fallback if OpenAI fails)
LLM_URL=http://localhost:11434
LLM_MODEL=gemma3:1b

# The system will:
# 1. Try OpenAI first (fast, high quality)
# 2. Automatically fall back to Gemma3 if OpenAI fails
# 3. Continue working even if one provider is down

# ============================================
# AUTHENTICATION
# ============================================
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production-12345
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# ============================================
# RATE LIMITING
# ============================================
ENABLE_RATE_LIMITING=true
AUTH_RATE_LIMIT=5/minute
API_RATE_LIMIT=100/minute

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

## 📁 Project Structure

```
fastapi_metrics/
│
├── app/                              # Backend application
│   ├── __init__.py
│   ├── main.py                       # FastAPI app entry point
│   │
│   ├── api/                          # API routes
│   │   ├── __init__.py
│   │   └── endpoints/
│   │       ├── __init__.py
│   │       ├── auth.py               # Authentication endpoints
│   │       ├── chat.py               # AI chat assistant
│   │       ├── config.py             # Email/Slack config
│   │       ├── metrics.py            # Metrics endpoints
│   │       ├── session.py            # Session management
│   │       └── target.py             # Target management
│   │
│   ├── core/                         # Core functionality
│   │   ├── __init__.py
│   │   ├── auth.py                   # JWT authentication
│   │   ├── config.py                 # Environment configuration
│   │   ├── logging.py                # Logging setup
│   │   └── rate_limit.py             # Rate limiting
│   │
│   ├── models/                       # Data models
│   │   ├── __init__.py
│   │   ├── anomaly.py
│   │   ├── batch.py
│   │   ├── incident.py
│   │   └── rca.py
│   │
│   ├── schemas/                      # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── chat.py
│   │   ├── config.py
│   │   ├── target.py
│   │   └── user.py
│   │
│   ├── services/                     # Business logic
│   │   ├── __init__.py
│   │   ├── batch_service.py          # Batch monitoring
│   │   ├── email_service.py          # Email alerts
│   │   ├── langfuse_service.py       # LLM observability
│   │   ├── llm_service.py            # OpenAI + Gemma3 LLM calls
│   │   ├── mongodb_service.py        # Database operations
│   │   ├── prometheus_service.py     # Prometheus queries
│   │   └── slack_service.py          # Slack notifications
│   │
│   └── migrations/                   # Database migrations
│       └── migrate_sessions.py
│
├── frontend/                         # React frontend
│   ├── public/
│   │   └── vite.svg
│   │
│   ├── src/
│   │   ├── assets/                   # Static assets
│   │   │   └── react.svg
│   │   │
│   │   ├── components/               # React components
│   │   │   ├── Anomalies.jsx
│   │   │   ├── ChatAssistant.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── EmailConfig.jsx
│   │   │   ├── Login.jsx
│   │   │   ├── MetricsBatches.jsx
│   │   │   ├── MetricsOverview.jsx
│   │   │   ├── Navbar.jsx
│   │   │   ├── ProtectedRoute.jsx
│   │   │   ├── RCAResults.jsx
│   │   │   ├── Register.jsx
│   │   │   ├── ServerSettings.jsx
│   │   │   └── SessionManagement.jsx
│   │   │
│   │   ├── services/                 # API client
│   │   │   └── api.js
│   │   │
│   │   ├── App.jsx                   # Main app component
│   │   ├── index.css                 # Tailwind CSS v4
│   │   └── main.jsx                  # React entry point
│   │
│   ├── index.html
│   ├── package.json
│   ├── postcss.config.js
│   ├── tailwind.config.js
│   └── vite.config.js
│
├── grafana/                          # Grafana configuration
│   ├── dashboards/
│   │   └── server-monitoring.json
│   └── provisioning/
│       └── dashboards/
│           └── dashboard.yml
│
├── .env                              # Environment variables
├── .env.example                      # Example environment file
├── .gitignore
├── docker-compose.yml                # Docker services
├── prometheus.yml                    # Prometheus config
├── targets.json                      # Dynamic targets (auto-managed)
├── requirements.txt                  # Python dependencies
└── README.md                         # This file
```

### Key Files Explained

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI application entry point, CORS, routes |
| `app/core/config.py` | Loads all environment variables |
| `app/core/auth.py` | JWT token creation and validation |
| `app/services/llm_service.py` | OpenAI (primary) + Gemma3 (fallback) integration |
| `app/services/batch_service.py` | Periodic metric collection and analysis |
| `app/api/endpoints/target.py` | Dynamic target management API |
| `frontend/src/services/api.js` | Centralized API client with auth |
| `frontend/src/components/Dashboard.jsx` | Main dashboard UI |
| `targets.json` | Auto-generated Prometheus targets |
| `prometheus.yml` | Prometheus scrape configuration |



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
   - **Grafana:** Visual dashboards at http://localhost:3000
   - **AI Chat:** Ask questions about your metrics

5. **Manage Sessions**
   - Go to Settings → Sessions
   - View all active login sessions
   - See device info (browser, OS, IP address)
   - Revoke individual sessions or all other sessions
   - Current session is highlighted and cannot be revoked

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
| `/api/auth/sessions` | GET | ✅ | Get all active sessions |
| `/api/auth/sessions/{id}` | DELETE | ✅ | Revoke specific session |
| `/api/auth/sessions/revoke-all` | POST | ✅ | Revoke all other sessions |

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
| `/chat` | POST | Send message to AI chat assistant |
| `/chat/sessions` | GET | Get user's chat sessions |
| `/chat/sessions/{id}` | GET | Get specific chat session |

### Interactive API Docs

Visit http://localhost:8000/docs for full Swagger documentation with "Try it out" functionality.

---

## 📈 Grafana Integration

### Universal Dashboard

The platform includes a pre-configured Grafana dashboard that automatically detects and displays metrics from different exporters:

**Features:**
- **Auto-Detection:** Works with Windows Exporter, Node Exporter, and other Prometheus exporters
- **Universal Metrics:** Uses OR queries to accommodate varying metric names
- **Multi-Instance:** Displays all monitored servers in a single dashboard
- **Real-Time:** Updates every 5 seconds

**Access Grafana:**
1. Open http://localhost:3000
2. Login with default credentials: `admin` / `admin`
3. Navigate to Dashboards → Server Monitoring
4. Select instance from dropdown to view specific server

**Dashboard Panels:**
- CPU Usage (per core and total)
- Memory Usage (available, used, total)
- Disk I/O (read/write rates)
- Network Traffic (sent/received)
- System Uptime
- Process Count

**Customization:**
The dashboard JSON is located at `grafana/dashboards/server-monitoring.json` and can be modified to add custom panels.

---

## 🔐 Session Management

### JWT-Based Sessions

The platform implements secure session management with device tracking:

**Features:**
- **Device Detection:** Automatically identifies browser, OS, and device type
- **IP Tracking:** Records IP address for each session
- **Activity Monitoring:** Tracks last active timestamp
- **Remote Revocation:** Revoke sessions from any device
- **Multi-Device Support:** Login from multiple devices simultaneously

**Session Information:**
Each session includes:
- Device type (Desktop, Mobile, Tablet)
- Browser name and version
- Operating system
- IP address
- Creation timestamp
- Last activity timestamp

**Security:**
- Sessions are stored in MongoDB with user_id isolation
- JWT tokens expire after 24 hours (configurable)
- Revoking a session immediately invalidates the JWT
- Current session cannot be revoked (use logout instead)

**Usage:**
```bash
# View sessions in UI
Settings → Sessions

# Or via API
curl -H "Authorization: Bearer YOUR_JWT" http://localhost:8000/api/auth/sessions
```

---

## 💬 AI Chat Assistant

### Interactive Metric Queries

Chat with AI to get insights about your infrastructure:

**Features:**
- **Natural Language:** Ask questions in plain English
- **Context-Aware:** AI understands your metrics and history
- **Session History:** All conversations are saved per user
- **Multi-Session:** Create multiple chat sessions for different topics

**Example Queries:**
- "What's the current CPU usage on my servers?"
- "Show me memory trends for the last hour"
- "Are there any anomalies I should be concerned about?"
- "Explain the root cause of the latest incident"

**Access:**
- Frontend: Dashboard → Chat icon
- API: `POST /chat` with message payload

---

## 🔍 How It Works

### LLM-Powered Detection

The system uses **pure AI detection** with intelligent fallback - no threshold rules or statistical methods:

1. **Fetch Metrics** - Queries Prometheus for user's targets
2. **Group by Instance** - Organizes metrics by server/service
3. **Build Prompt** - Creates structured prompt with time window and ALL metrics
4. **LLM Analysis** - AI analyzes the entire batch (OpenAI primary, Gemma3 fallback)
5. **Parse Response** - Extracts incident, anomalies, clusters from JSON
6. **Store Everything** - Saves to MongoDB with user_id
7. **Send Alerts** - Notifies via user's configured Email/Slack

**LLM Provider Strategy:**
- **Primary**: OpenAI (gpt-4o-mini) - Fast, high-quality analysis
- **Fallback**: Gemma3 (via Ollama) - Automatic fallback if OpenAI fails
- **Resilience**: System continues working even if one provider is down

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
| `auth_sessions` | Active login sessions | ✅ |

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

