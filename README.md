# FastAPI Metrics Pipeline

Automated metrics collection, anomaly detection with LLM analysis, and RCA generation.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp config.env.example .env
   # Edit .env with your values
   ```

3. **Run Prometheus** (to scrape metrics):
   ```bash
   # Windows: download from https://prometheus.io/download/
   prometheus.exe --config.file=prometheus.yml
   ```

4. **Run FastAPI app** (optional, exposes /metrics):
   ```bash
   pip install fastapi uvicorn prometheus-fastapi-instrumentator
   uvicorn main:app --port 8000
   ```

5. **Run the pipeline:**
   ```bash
   python pipeline.py
   ```

## Collections (MongoDB)

| Collection | Fields |
|------------|--------|
| `prom_rollup_1m` | ts, metric, instance, job, value, min, max, avg |
| `anomalies` | anomaly_id, metric, instance, severity, expected, actual, deviation_pct, status, llm_analysis |
| `rca_results` | rca_id, anomaly_id, metric, severity, root_cause, action, analyzed_at |

## Configuration

| Variable | Description |
|----------|-------------|
| `PROM_URL` | Prometheus server URL |
| `MONGO_URI` | MongoDB connection string |
| `MONGO_DB` | Database name |
| `LLM_URL` | Local LLM API endpoint (Ollama) |
| `LLM_MODEL` | Model name |
