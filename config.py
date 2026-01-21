
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

# Pipeline settings
STEP = 5
COLLECT_WINDOW = 5
LOOKBACK_MIN = 15
Z_THRESHOLD = 2.0
MIN_POINTS = 5
MAX_DOCS = 25

# Metrics to collect
METRICS = [
    "process_resident_memory_bytes",
    "process_open_fds",
    "go_goroutines",
    "go_memstats_alloc_bytes",
    "process_cpu_seconds_total",
]
