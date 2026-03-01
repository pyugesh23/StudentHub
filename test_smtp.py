import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv()

def test_smtp():
    server = os.getenv('MAIL_SERVER')
    port = int(os.getenv('MAIL_PORT', 587))
    user = os.getenv('MAIL_USERNAME')
    password = os.getenv('MAIL_PASSWORD')
    sender = os.getenv('MAIL_DEFAULT_SENDER')

    print(f"Connecting to {server}:{port}...")
    try:
        msg = MIMEText("Standalone SMTP test")
        msg['Subject'] = "SMTP Test"
        msg['From'] = sender
        msg['To'] = user

        with smtplib.SMTP(server, port) as smtp:
            smtp.set_debuglevel(1)
            smtp.starttls()
            print("Logging in...")
            smtp.login(user, password)
            print("Sending...")
            smtp.send_message(msg)
            print("SUCCESS!")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_smtp()
