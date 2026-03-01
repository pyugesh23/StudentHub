import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_sendgrid():
    api_key = os.environ.get("SENDGRID_API_KEY")
    sender = os.environ.get("MAIL_DEFAULT_SENDER")
    
    if not api_key or "your_sendgrid" in api_key:
        print("ERROR: Please update SENDGRID_API_KEY in .env first.")
        return

    print(f"Testing SendGrid API...")
    print(f"Sender: {sender}")
    
    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "personalizations": [{"to": [{"email": sender}]}],
        "from": {"email": sender},
        "subject": "SendGrid Verification",
        "content": [{"type": "text/plain", "value": "If you receive this, SendGrid is working!"}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code >= 200 and response.status_code < 300:
            print("SUCCESS: Test email sent!")
        else:
            print(f"FAILED: Status {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_sendgrid()
