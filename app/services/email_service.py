"""
Email Service
Email alert functionality
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
from app.services.mongodb_service import get_db
from app.core.logging import logger


def send_alert(subject: str, body: str) -> bool:
    """Send email alert to configured recipients"""
    db = get_db()
    if db is None:
        return False

    config = db.email_config.find_one({})
    if not config or not config.get("enabled"):
        return False

    recipients = config.get("recipients", [])
    if not recipients or not SMTP_USER or not SMTP_PASSWORD:
        return False

    try:
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = ", ".join(recipients)
        msg.attach(MIMEText(body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error(f"[Email] Error: {e}")
        return False
