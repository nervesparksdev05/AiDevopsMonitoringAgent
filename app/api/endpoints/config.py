"""
Configuration Routes - Fixed for Frontend
"""
from fastapi import APIRouter, HTTPException
from app.schemas.config import EmailConfig
from app.services.mongodb_service import get_db
from app.services.email_service import send_alert
from app.services.slack_service import send_slack_alert_text, slack_is_configured

router = APIRouter()


@router.get("/agent/email-config")
def get_email_config():
    """Get email configuration"""
    db = get_db()
    if db is None:
        return {"enabled": False, "recipients": []}

    config = db.email_config.find_one({})
    if not config:
        # Initialize if not exists
        db.email_config.insert_one({"enabled": False, "recipients": []})
        return {"enabled": False, "recipients": []}

    return {
        "enabled": config.get("enabled", False), 
        "recipients": config.get("recipients", [])
    }


@router.put("/agent/email-config")
def update_email_config(config: EmailConfig):
    """Update email configuration"""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    db.email_config.update_one(
        {},
        {"$set": {"enabled": config.enabled, "recipients": config.recipients}},
        upsert=True,
    )
    return {"message": "Email config updated"}


@router.post("/agent/test-email")
def send_test_email():
    """Send test email"""
    success = send_alert(
        "[TEST] AI DevOps Monitor",
        """
        <h2>✅ Test Email</h2>
        <p>This is a test email from your AI DevOps Monitoring system.</p>
        <p>If you received this, your email configuration is working correctly!</p>
        <p><strong>Time:</strong> Email alerts are now active.</p>
        """,
    )
    if success:
        return {"message": "Test email sent successfully!"}
    raise HTTPException(
        status_code=500, 
        detail="Failed to send test email. Check SMTP settings in .env file."
    )


@router.post("/agent/test-slack")
def test_slack():
    """Send test Slack message"""
    if not slack_is_configured():
        raise HTTPException(
            status_code=400,
            detail="Slack is not configured. Enable it in Settings → Alerts & Servers."
        )
    
    ok = send_slack_alert_text("✅ [TEST] AI DevOps Monitor: Slack webhook is working!")
    if ok:
        return {"message": "Test Slack message sent successfully!"}
    
    raise HTTPException(
        status_code=500, 
        detail="Failed to send Slack message. Check webhook URL."
    )