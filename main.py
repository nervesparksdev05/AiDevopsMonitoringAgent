from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

# exposes /metrics
Instrumentator().instrument(app).expose(app)
