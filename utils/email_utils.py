import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database.db import log_email

# ─── Email Config (from .env or defaults) ────────────────────────────────────
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
BRAND_EMAIL = os.getenv("BRAND_EMAIL", "brand-antifake@example.com")

# ─── Simulated Email (always works, no real SMTP needed) ─────────────────────
def send_brand_alert(report_data: dict, report_id: int, escalated: bool = False) -> dict:
    """
    Send (or simulate) an alert email to the brand anti-counterfeiting team.
    Returns a dict with status and mock email content.
    """
    subject = (
        f"🚨 ESCALATED FRAUD ALERT: {report_data.get('qr_id')} | {report_data.get('shop_name')}"
        if escalated else
        f"⚠️ New Counterfeit Report: {report_data.get('qr_id')} | {report_data.get('shop_name')}"
    )

    body = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{"🚨 HIGH PRIORITY ESCALATION" if escalated else "⚠️ COUNTERFEIT PRODUCT REPORT"}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Report ID: #{report_id}
Timestamp: {datetime.now().strftime("%d %b %Y, %I:%M %p IST")}
Priority: {"CRITICAL / ESCALATED" if escalated else "NORMAL"}

─── PRODUCT DETAILS ───────────────────
QR Code ID   : {report_data.get('qr_id', 'N/A')}
Shop Name    : {report_data.get('shop_name', 'N/A')}
Shop Address : {report_data.get('shop_address', 'N/A')}
GPS Location : {report_data.get('latitude', 'N/A')}, {report_data.get('longitude', 'N/A')}

─── ANOMALY INFO ──────────────────────
Type         : {report_data.get('anomaly_type', 'N/A')}
Details      : {report_data.get('anomaly_details', 'N/A')}

─── REPORTER INFO ─────────────────────
Name         : {report_data.get('reporter_name', 'Anonymous')}
Phone        : {report_data.get('reporter_phone', 'N/A')}
Email        : {report_data.get('reporter_email', 'N/A')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Powered by VeriScan Anti-Counterfeiting Platform
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    # Log in DB (always)
    log_email(BRAND_EMAIL, subject, body, report_id)

    # Try real SMTP if configured
    real_sent = False
    if SMTP_USER and SMTP_PASS:
        try:
            msg = MIMEMultipart()
            msg['From'] = SMTP_USER
            msg['To'] = BRAND_EMAIL
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(SMTP_USER, BRAND_EMAIL, msg.as_string())
            real_sent = True
        except Exception as e:
            real_sent = False

    return {
        "status": "sent" if real_sent else "simulated",
        "to": BRAND_EMAIL,
        "subject": subject,
        "body": body,
        "real_smtp": real_sent
    }


def send_escalation_alert(qr_id: str, shop_name: str, count: int, pdf_path: str = None) -> dict:
    """Send escalation notification when threshold is reached."""
    subject = f"🔴 AUTO-ESCALATION: {count} reports for QR {qr_id} at {shop_name}"
    body = f"""
🔴 CROWD-SOURCED ESCALATION TRIGGERED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

QR Code     : {qr_id}
Shop Name   : {shop_name}
Reports     : {count} independent users reported the SAME fake product
Priority    : {"CRITICAL" if count >= 10 else "HIGH"}
Action      : Immediate brand investigation required

This is NOT a single complaint — {count} different customers
reported the same counterfeit product at the same location.
This constitutes strong evidence of organized counterfeiting.

{f"PDF Report attached: {pdf_path}" if pdf_path else ""}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VeriScan Crowd Aggregation Engine
"""
    log_email(BRAND_EMAIL, subject, body)
    return {"status": "simulated", "subject": subject, "body": body}
