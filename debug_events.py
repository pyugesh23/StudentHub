# debug_events.py
from app import create_app
from app.models import Event, User
from datetime import datetime
import pytz

app = create_app()

with app.app_context():
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    print(f"Current time (IST): {now}")
    
    events = Event.query.all()
    print(f"Total events: {len(events)}")
    
    for event in events:
        user = User.query.get(event.user_id)
        email_status = "SENT" if event.email_sent else "NOT SENT"
        expired_status = "EXPIRED" if event.is_expired else "NOT EXPIRED"
        print(f"Event: {event.title} | User: {user.email if user else 'N/A'} | Status: {email_status} | Expired: {expired_status} | Date: {event.date} | Time: {event.time}")
