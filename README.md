# FastAPI Metrics Observability Pipeline

Automated metrics collection from Prometheus, AI-powered anomaly detection, and root cause analysis with REST API endpoints.

## Features

- 📊 **Metrics Collection**: Aggregates Prometheus metrics every 5 seconds
- 🔍 **Anomaly Detection**: Statistical Z-score analysis with LLM insights
- 🤖 **AI-Powered RCA**: Local LLM generates root cause analysis and recommendations
- 🌐 **REST API**: Query anomalies, RCA results, and metrics via HTTP endpoints
- 🗄️ **MongoDB Storage**: Simplified schema with 25-document cap per collection

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp config.env.example .env
# Edit .env with your MongoDB URI, Prometheus URL, and LLM endpoint
```

### 3. Run Services

**Start Prometheus** (scrapes metrics):
```bash
# Download from https://prometheus.io/download/
prometheus.exe --config.file=prometheus.yml
```

**Start the Pipeline** (background worker):
```bash
python pipeline.py
```

**Start the API Server** (REST endpoints):
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

**Start the Frontend** (React dashboard):
```bash
cd frontend
npm install  # First time only
npm run dev
```

Frontend will run on: `http://localhost:5173`  
Backend API will run on: `http://localhost:8080`

## Architecture

```
Prometheus → Collector → MongoDB (prom_rollup_1m)
                ↓
         Anomaly Detector → MongoDB (anomalies) + LLM Analysis
                ↓
         RCA Generator → MongoDB (rca_results) + LLM RCA
                ↓
         Cleanup (keeps 25 docs max)
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/anomalies` | GET | List anomalies (filter: severity, status) |
| `/anomalies/{id}` | GET | Get specific anomaly |
| `/rca` | GET | List RCA results |
| `/rca/{id}` | GET | Get specific RCA |
| `/prom-metrics` | GET | Prometheus metrics rollup |
| `/stats` | GET | Database statistics |
| `/metrics` | GET | Prometheus metrics endpoint |

**Base URL**: `http://localhost:8080`

**Example**:
```bash
curl http://localhost:8080/anomalies?severity=critical&limit=5
```

See [POSTMAN_GUIDE.md](POSTMAN_GUIDE.md) for detailed API testing.

## MongoDB Collections

| Collection | Schema |
|------------|--------|
| `prom_rollup_1m` | `ts, metric, instance, job, value, min, max, avg` |
| `anomalies` | `anomaly_id, metric, instance, severity, expected, actual, deviation_pct, z_score, status, llm_analysis` |
| `rca_results` | `rca_id, anomaly_id, metric, severity, root_cause, action, analyzed_at` |

## Configuration (config.py)

| Variable | Default | Description |
|----------|---------|-------------|
| `PROM_URL` | `http://localhost:9090` | Prometheus server |
| `MONGO_URI` | - | MongoDB connection string |
| `MONGO_DB` | `observability` | Database name |
| `LLM_URL` | `http://124.123.18.150:11434/api/generate` | Ollama LLM endpoint |
| `LLM_MODEL` | `gpt-oss:latest` | LLM model name |
| `STEP` | `5` | Prometheus query step (seconds) |
| `COLLECT_WINDOW` | `5` | Collection window (seconds) |
| `LOOKBACK_MIN` | `15` | Anomaly detection lookback (minutes) |
| `Z_THRESHOLD` | `2.0` | Z-score threshold for anomalies |
| `MIN_POINTS` | `5` | Minimum data points for detection |
| `MAX_DOCS` | `25` | Max documents per collection |

## Workers (Threads)

| Worker | Interval | Function |
|--------|----------|----------|
| `collector` | 5s | Queries Prometheus, writes to `prom_rollup_1m` |
| `anomaly_detector` | 5s | Detects anomalies (Z-score), calls LLM, writes to `anomalies` |
| `rca_generator` | 5s | Generates RCA for open anomalies, writes to `rca_results` |
| `cleanup` | 5s | Trims collections to 25 documents |

## Project Structure

```
fastapi_metrics/
├── config.py              # Configuration settings
├── pipeline.py            # Main pipeline (4 workers)
├── main.py                # FastAPI REST API server
├── prometheus.yml         # Prometheus scrape config
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (gitignored)
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## Development

**View logs**:
```bash
# Pipeline logs show worker activity
[collector] wrote 5 docs
[anomaly] high: process_resident_memory_bytes on localhost:9090 (23% deviation)
[rca] done: process_resident_memory_bytes
[cleanup] anomalies -> 25
```

**Test API**:
```bash
# Get stats
curl http://localhost:8080/stats

# Get anomalies
curl http://localhost:8080/anomalies?limit=10

# Get RCA results
curl http://localhost:8080/rca?severity=critical
```


