import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import requests
from flask_apscheduler import APScheduler
from datetime import datetime
import pytz

load_dotenv()

# Force insecure transport for local development
os.environ['AUTHLIB_INSECURE_TRANSPORT'] = '1'

db = SQLAlchemy()
login_manager = LoginManager()
oauth = OAuth()
scheduler = APScheduler()


# ===============================
# SendGrid Email Function
# ===============================
def send_email(to_email, subject, body):
    api_key = os.environ.get("SENDGRID_API_KEY")
    sender = os.environ.get("MAIL_DEFAULT_SENDER")

    if not api_key:
        print("ERROR: SENDGRID_API_KEY not found.")
        return False

    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "personalizations": [{
            "to": [{"email": to_email}],
            "subject": subject
        }],
        "from": {"email": sender},
        "content": [{
            "type": "text/plain",
            "value": body
        }]
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)

        if 200 <= response.status_code < 300:
            print("Email sent successfully ✅")
            return True
        else:
            print(f"ERROR: SendGrid API returned {response.status_code}: {response.text}")
            return False

    except Exception as e:
        print(f"ERROR: SendGrid request failed: {e}")
        return False


# ===============================
# App Factory
# ===============================
def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-prod')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SCHEDULER_API_ENABLED'] = True

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    oauth.init_app(app)
    scheduler.init_app(app)

    # Google OAuth
    google_client_id = os.getenv('GOOGLE_CLIENT_ID', '').strip()
    google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET', '').strip()
    discovery_url = os.getenv(
        'GOOGLE_DISCOVERY_URL',
        'https://accounts.google.com/.well-known/openid-configuration'
    ).strip()

    if google_client_id and google_client_secret:
        oauth.register(
            name='google',
            client_id=google_client_id,
            client_secret=google_client_secret,
            server_metadata_url=discovery_url,
            client_kwargs={
                'scope': 'openid email profile',
            }
        )

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .resume import resume as resume_blueprint
    app.register_blueprint(resume_blueprint)

    from .ats import ats as ats_blueprint
    app.register_blueprint(ats_blueprint)

    from .compiler import compiler as compiler_blueprint
    app.register_blueprint(compiler_blueprint)

    from .events import events as events_blueprint
    app.register_blueprint(events_blueprint)

    from .tools import tools as tools_blueprint
    app.register_blueprint(tools_blueprint)

    from .games import games as games_blueprint
    app.register_blueprint(games_blueprint, url_prefix='/games')

    from .interview import interview as interview_blueprint
    app.register_blueprint(interview_blueprint)

    with app.app_context():
        db.create_all()

    # ===============================
    # Reminder Job
    # ===============================
    def check_for_reminders():
        with app.app_context():
            print(f"[{datetime.now()}] Scheduler checking for due reminders...")

            from .models import Event, User

            ist = pytz.timezone('Asia/Kolkata')
            now = datetime.now(ist)

            events_to_notify = Event.query.filter_by(email_sent=False).all()
            print(f"Found {len(events_to_notify)} unsent events.")

            for event in events_to_notify:
                if event.is_expired:
                    user = User.query.get(event.user_id)

                    if user and user.email:
                        success = send_email(
                            user.email,
                            f"Reminder: {event.title}",
                            f"""Hi {user.username},

This is a reminder for your event: {event.title}

Description: {event.description}
Time: {event.time}

Best regards,
StudentHub Team"""
                        )

                        if success:
                            event.email_sent = True
                            db.session.commit()
                            print(f"Notification sent for event: {event.title}")
                        else:
                            db.session.rollback()

    # ===============================
    # Start Scheduler (Production Safe)
    # ===============================
    if not scheduler.running:
        scheduler.add_job(
            id='reminder_job',
            func=check_for_reminders,
            trigger='interval',
            seconds=120,
            max_instances=1,
            replace_existing=True,
            misfire_grace_time=30,
            coalesce=True
        )
        scheduler.start()
        print("Scheduler started successfully.")

    return app