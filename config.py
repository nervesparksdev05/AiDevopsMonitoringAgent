
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
LLM_URL = os.getenv("LLM_URL", "")
LLM_MODEL = os.getenv("LLM_MODEL", "")

# Pipeline settings - ADJUSTED for better anomaly detection
STEP = 5                     # Prometheus query step (seconds)
COLLECT_WINDOW = 10          # Data collection window (seconds)
LOOKBACK_MIN = 10            # Anomaly detection lookback (minutes) - INCREASED to get more data points
Z_THRESHOLD = 1.2            # SENSITIVE for demo - lowered to detect more anomalies
MIN_POINTS = 2               # Minimum data points for detection - REDUCED from 3 to 2
MAX_DOCS = 25


# SMTP Email Configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "rajshekhar@nervesparks.in")
SEND_EMAIL_ALERTS = os.getenv("SEND_EMAIL_ALERTS", "true").lower() == "true"
