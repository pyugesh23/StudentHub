from app import create_app, db
from app.models import Event
import os

def inspect_db():
    app = create_app()
    with app.app_context():
        import os
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        print(f"DATABASE_URI: {db_uri}")
        print(f"INSTANCE_PATH: {os.path.abspath(app.instance_path)}")
        
        # Determine the effective path
        if db_uri.startswith('sqlite:///'):
            db_file = db_uri[len('sqlite:///'):]
            abs_db_path = os.path.join(app.instance_path, db_file)
            print(f"EFFECTIVE ABSOLUTE DB PATH: {os.path.abspath(abs_db_path)}")
            print(f"File exists: {os.path.exists(abs_db_path)}")
            if os.path.exists(abs_db_path):
                print(f"File size: {os.path.getsize(abs_db_path)} bytes")
        
        events = Event.query.all()
        print(f"Total events found: {len(events)}")
        
        for e in events:
            # Manually check expiry logic
            from datetime import datetime
            import pytz
            ist = pytz.timezone('Asia/Kolkata')
            now = datetime.now(ist)
            
            print(f"--- Event ID: {e.id} ---")
            print(f"  Title: {e.title}")
            print(f"  Date: {e.date}")
            print(f"  Time: {e.time}")
            print(f"  Email Sent: {e.email_sent}")
            
            # Re-run is_expired logic directly for transparency
            try:
                hour, minute = map(int, e.time.split(':'))
                event_datetime = ist.localize(e.date.replace(hour=hour, minute=minute, second=0, microsecond=0))
                is_exp = now >= event_datetime
                print(f"  Computed Expired: {is_exp} (Now: {now} vs Event: {event_datetime})")
            except Exception as ex:
                print(f"  Expiry Check Failed: {ex}")

if __name__ == "__main__":
    inspect_db()
