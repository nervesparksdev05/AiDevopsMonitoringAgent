"""
Slack Configuration Routes
Configure Slack Webhook dynamically.
"""
from fastapi import APIRouter, HTTPException
from app.schemas.slack_config import SlackConfig
from app.services.mongodb_service import get_db
from app.services.slack_service import slack_is_configured

router = APIRouter()

@router.get("/agent/slack-config", response_model=SlackConfig)
def get_slack_config():
    """Get Slack configuration"""
    db = get_db()
    if db is None:
        return SlackConfig(enabled=False, webhook_url="")
        
    config = db.slack_config.find_one({})
    if not config:
        return SlackConfig(enabled=False, webhook_url="")
        
    return SlackConfig(
        enabled=config.get("enabled", False),
        webhook_url=config.get("webhook_url", "")
    )


@router.put("/agent/slack-config")
def update_slack_config(config: SlackConfig):
    """Update Slack configuration"""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=500, detail="Database error")
        
    db.slack_config.update_one(
        {},
        {"$set": {"enabled": config.enabled, "webhook_url": config.webhook_url}},
        upsert=True
    )
    
    # Note: Changes take effect immediately as services check DB/Env
    return {"message": "Slack config updated"}
