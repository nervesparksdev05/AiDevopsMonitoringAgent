import os
from dotenv import load_dotenv

load_dotenv()

# Prometheus
PROM_URL = os.getenv("PROM_URL", "http://localhost:9090")

# MongoDB
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB", "observability")

# LLM (Ollama)
LLM_URL = os.getenv("LLM_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2")

# Monitoring
MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL", "30"))
Z_THRESHOLD = float(os.getenv("Z_THRESHOLD", "3.0"))
MAX_DOCS = int(os.getenv("MAX_DOCS", "100"))

# Email
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
# Support both ALERT_EMAIL (single) and ALERT_EMAILS (multiple)
_emails = os.getenv("ALERT_EMAILS", "") or os.getenv("ALERT_EMAIL", "")
ALERT_EMAILS = [e.strip() for e in _emails.split(",") if e.strip()]