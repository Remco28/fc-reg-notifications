import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_notification(subject: str, body: str) -> None:
    """
    Send email notification using SMTP configuration from environment variables.

    Args:
        subject: Email subject line
        body: Email body content (plain text)
    """
    # Read SMTP configuration from environment variables
    smtp_host = os.getenv('SMTP_HOST', 'localhost')
    smtp_port = int(os.getenv('SMTP_PORT', '1025'))
    sender_email = os.getenv('SENDER_EMAIL', 'test@example.com')
    recipient_email = os.getenv('RECIPIENT_EMAIL', 'you@example.com')

    # Create message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    # Add body to email
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Create SMTP session
        server = smtplib.SMTP(smtp_host, smtp_port)

        # Send email
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()

        print(f"Email sent successfully: {subject}")

    except Exception as e:
        print(f"Failed to send email: {e}")