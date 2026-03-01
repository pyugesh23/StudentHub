from app import create_app, db
from app.models import Event
import os
import pytz
from datetime import datetime

with open('final_debug.log', 'w') as f:
    try:
        app = create_app()
        f.write(f"App created. Instance path: {app.instance_path}\n")
        f.write(f"DB URI: {app.config['SQLALCHEMY_DATABASE_URI']}\n")
        
        with app.app_context():
            events = Event.query.all()
            f.write(f"Found {len(events)} events in database.\n")
            
            ist = pytz.timezone('Asia/Kolkata')
            now = datetime.now(ist)
            f.write(f"Current Time (IST): {now}\n")
            
            for e in events:
                f.write(f"\n- Event: {e.title} (ID: {e.id})\n")
                f.write(f"  Time: {e.time}, Date: {e.date}, Sent: {e.email_sent}\n")
                f.write(f"  Is Expired (Prop): {e.is_expired}\n")
                
                # Manual decomposition
                if e.time:
                    try:
                        hour, minute = map(int, e.time.split(':'))
                        # Note: we assume e.date is naive and in IST
                        event_dt = ist.localize(e.date.replace(hour=hour, minute=minute))
                        f.write(f"  Calculated DT: {event_dt}\n")
                        f.write(f"  Comparison (now >= event_dt): {now >= event_dt}\n")
                    except Exception as ex:
                        f.write(f"  Calc Error: {ex}\n")
    except Exception as e:
        f.write(f"FAILURE: {e}\n")
        import traceback
        f.write(traceback.format_exc())
