import os
from flask import Flask
from flask_mail import Mail, Message
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Mail Configuration (from .env)
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

mail = Mail(app)

def test_send():
    with app.app_context():
        try:
            msg = Message(
                subject="StudentHub Email Test",
                recipients=[app.config['MAIL_USERNAME']], # Send to self
                body="Testing StudentHub email notification system. If you receive this, the SMTP settings are correct."
            )
            mail.send(msg)
            print("SUCCESS: Email sent successfully!")
        except Exception as e:
            print(f"FAILED: Email delivery failed. Error: {e}")

if __name__ == '__main__':
    test_send()
