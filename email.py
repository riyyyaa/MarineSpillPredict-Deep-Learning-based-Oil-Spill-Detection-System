import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# NOTE: For real use, configure an App Password from your Google Account
# and set these environment variables or replace these placeholders.
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "marinspill2026@gmail.com"
SENDER_PASSWORD = "zmdcaaddpfgekxmx"

def send_spill_alert(user_email: str, oil_percentage: float, confidence: float):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = user_email
        msg['Subject'] = "🚨 ALERT: Oil Spill Detected! 🚨"

        body = f"""
Hello,

Our system has confidently detected a possible oil spill in the recently uploaded image.

An alert has been generated for monitoring and response purposes. Please review the system dashboard for further details.

Stay safe,
Marinespillpredict
"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Alert email sent to {user_email}.")
        
    except Exception as e:
        print(f"Failed to send email: {e}")
