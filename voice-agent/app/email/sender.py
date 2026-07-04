import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL", SMTP_USER)  # Admin email to receive notifications


def send_meeting_email_sync(date_str: str, time_str: str, user_email: str, notes: str = None):
    if not SMTP_USER or not SMTP_PASS:
        print(">>> SMTP_USER or SMTP_PASS not set. Skipping email notification.")
        return

    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = NOTIFY_EMAIL
    msg['Subject'] = f"New Meeting Scheduled: {date_str} at {time_str}"

    body = f"""
    A new meeting has been scheduled via the Voice Agent!

    Date: {date_str}
    Time: {time_str}
    Client Email: {user_email}
    Notes: {notes or 'None'}

    Please check the Admin Dashboard for more details.
    """
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        print(">>> Meeting notification email sent successfully.")
    except Exception as e:
        print(f">>> Failed to send email: {e}")

async def send_meeting_email(date_str: str, time_str: str, user_email: str, notes: str = None):
    import asyncio
    await asyncio.to_thread(send_meeting_email_sync, date_str, time_str, user_email, notes)
