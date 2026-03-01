from app import create_app, mail
from flask_mail import Message
import os
from dotenv import load_dotenv

def test_app_mail():
    load_dotenv()
    app = create_app()
    with app.app_context():
        print("Testing Mail Configuration...")
        print(f"Server: {app.config['MAIL_SERVER']}")
        print(f"Port: {app.config['MAIL_PORT']}")
        print(f"User: {app.config['MAIL_USERNAME']}")
        
        recipient = app.config['MAIL_USERNAME']
        msg = Message(
            subject="StudentHub App Context Mail Test",
            recipients=[recipient],
            body="This is a test email from the Flask app context."
        )
        
        try:
            print(f"Attempting to send mail to {recipient}...")
            mail.send(msg)
            print("SUCCESS! Email sent.")
        except Exception as e:
            print(f"FAILED: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_app_mail()
