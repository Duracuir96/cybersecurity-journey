import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.api.settings import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, ALERT_EMAIL_TO

def send_anomaly_email(anomaly: dict):
    subject = f"🚨 [{anomaly['severity'].upper()}] SalesFlow anomaly"

    body = f"""
An anomaly has been detected.

Scope      : {anomaly.get('scope')}
SKU        : {anomaly.get('sku')}
Product    : {anomaly.get('name')}
Period     : {anomaly.get('period')}

Type       : {anomaly.get('type')}
Date       : {anomaly.get('date')}
Value      : {anomaly.get('value')}
Z-Score    : {anomaly.get('score')}

Explanation:
{anomaly.get('explanation')}
"""

    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = ALERT_EMAIL_TO
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
if __name__ == "__main__":
    send_anomaly_email({
        "severity": "high",
        "scope": "TEST",
        "sku": "TEST-SKU",
        "name": "Test Product",
        "period": "daily",
        "type": "MANUAL_TEST",
        "date": "2025-01-01",
        "value": 999,
        "score": 5.2,
        "explanation": "This is a manual test email"
    })
