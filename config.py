
import os
from dotenv import load_dotenv

load_dotenv()

# Prometheus
PROM_URL = os.getenv("PROM_URL", "http://localhost:9090")

# MongoDB
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB", "observability")

# Environment
ENV = os.getenv("ENV", "local")

# LLM (Ollama)
LLM_URL = os.getenv("LLM_URL", "http://124.123.18.150:11434/api/generate")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-oss:latest")

# Pipeline settings - DEMO MODE (for presentations)
STEP = 5                     # Prometheus query step (seconds)
COLLECT_WINDOW = 10          # Data collection window (seconds)
LOOKBACK_MIN = 5             # Anomaly detection lookback (minutes)
Z_THRESHOLD = 1.5            # ULTRA SENSITIVE for demo
MIN_POINTS = 3               # Minimum data points for detection
MAX_DOCS = 25

# Metrics to collect
METRICS = [
    "process_resident_memory_bytes",
    "process_open_fds",
    "go_goroutines",
    "go_memstats_alloc_bytes",
    "process_cpu_seconds_total",
]

# SMTP Email Configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "rajshekhar@nervesparks.in")
SEND_EMAIL_ALERTS = os.getenv("SEND_EMAIL_ALERTS", "true").lower() == "true"
