import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import emails_from_email, emails_from_name
import os

def send_email(to_email: str, subject: str, body: str, html: bool = False):
    msg = MIMEMultipart()
    msg['From'] = f"{emails_from_name} <{emails_from_email}>"
    msg['To'] = to_email
    msg['Subject'] = subject
    if html:
        msg.attach(MIMEText(body, 'html'))
    else:
        msg.attach(MIMEText(body, 'plain'))
    # SMTP config from environment or config.py
    smtp_host = os.getenv('SMTP_HOST', 'localhost')
    smtp_port = int(os.getenv('SMTP_PORT', 25))
    smtp_user = os.getenv('SMTP_USER', None)
    smtp_pass = os.getenv('SMTP_PASS', None)
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        if smtp_user and smtp_pass:
            server.starttls()
            server.login(smtp_user, smtp_pass)
        server.sendmail(emails_from_email, to_email, msg.as_string()) 