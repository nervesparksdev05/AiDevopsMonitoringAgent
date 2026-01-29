"""
Slack Service
Slack webhook integration for alerts
"""
import requests
from app.core.config import SLACK_ENABLED, SLACK_WEBHOOK_URL
from app.core.helpers import mask_webhook
from app.core.logging import logger


def get_slack_config():
    """Get active Slack configuration (DB > Env)"""
    # 1. Check DB first
    from app.services.mongodb_service import get_db
    db = get_db()
    if db is not None:
        config = db.slack_config.find_one({})
        if config:
            return config.get("enabled", False), config.get("webhook_url", "")
            
    # 2. Fallback to Env
    return SLACK_ENABLED, SLACK_WEBHOOK_URL


def slack_is_configured() -> bool:
    """Check if Slack is enabled and configured"""
    enabled, url = get_slack_config()
    return enabled and bool((url or "").strip())


def send_slack_alert_text(text: str) -> bool:
    """Send a simple text message to Slack"""
    enabled, url = get_slack_config()
    
    if not enabled:
        return False
        
    webhook = (url or "").strip()
    if not webhook:
        return False

    payload = {
        "text": text,
        "username": "AI DevOps Monitor",
        "icon_emoji": ":rotating_light:",
    }

    try:
        logger.info(f"[Slack] Sending (webhook={mask_webhook(webhook)})")
        resp = requests.post(webhook, json=payload, timeout=10)
        if not resp.ok:
            logger.error(f"[Slack] Failed: HTTP {resp.status_code} | {resp.text[:200]}")
            return False
        logger.info("[Slack] ✅ Alert sent")
        return True
    except Exception as e:
        logger.error(f"[Slack] Error: {e}")
        return False
