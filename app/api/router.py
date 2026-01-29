from fastapi import APIRouter
from app.api.endpoints import health, data, chat, config, target, slack_config

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(data.router, tags=["Data"])
api_router.include_router(chat.router, tags=["Chat"])
api_router.include_router(config.router, tags=["Configuration"])
api_router.include_router(target.router, tags=["Target Management"])
api_router.include_router(slack_config.router, tags=["Slack Configuration"])
