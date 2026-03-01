import os
import sys
import pytz
from datetime import datetime
from app import create_app, db, mail
from app.models import Event, User
from flask_mail import Message

def debug_reminders():
    app = create_app()
    with app.app_context():
        print(f"--- REMINDER DEBUG START ---")
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        print(f"Current IST Time: {now}")
        
        # Check all unsent events
        events_to_notify = Event.query.filter_by(email_sent=False).all()
        print(f"Found {len(events_to_notify)} unsent events in DB.")
        
        for event in events_to_notify:
            print(f"\nAnalyzing Event ID: {event.id}, Title: {event.title}")
            print(f"  - Date (DB naive): {event.date}")
            print(f"  - Time (DB string): {event.time}")
            
            is_expired = event.is_expired
            print(f"  - Is Expired/Due (model check): {is_expired}")
            
            if is_expired:
                user = User.query.get(event.user_id)
                if user and user.email:
                    print(f"  - Sending email to: {user.email}")
                    try:
                        msg = Message(
                            subject=f"DEBUG Reminder: {event.title}",
                            recipients=[user.email],
                            body=f"Hi {user.username},\n\nThis is a DEBUG reminder for your event: {event.title}\nTime: {event.time}"
                        )
                        mail.send(msg)
                        print(f"  - SUCCESS: Email sent for {event.title}")
                    except Exception as e:
                        print(f"  - FAILED: Email delivery error: {e}")
                else:
                    print(f"  - WARNING: No user or email found for user_id {event.user_id}")
            else:
                print(f"  - Status: Not yet due.")
        
        print(f"\n--- REMINDER DEBUG END ---")

if __name__ == "__main__":
    debug_reminders()
