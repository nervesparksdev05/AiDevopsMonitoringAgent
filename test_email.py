"""
Test email functionality
"""
from config import *
from pipeline import send_email_alert

# Test email
subject = "🚨 TEST: RCA Alert System"
body = """
<h3>Test Email</h3>
<p>This is a test email from your Metrics Observability Pipeline.</p>
<p>If you receive this, SMTP is configured correctly!</p>
"""

print("Sending test email...")
result = send_email_alert(subject, body)

if result:
    print("✅ Email sent successfully!")
else:
    print("❌ Email failed to send. Check SMTP settings.")
