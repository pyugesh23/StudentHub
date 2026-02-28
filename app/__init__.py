import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask_mail import Mail, Message
from flask_apscheduler import APScheduler
from datetime import datetime
import pytz

load_dotenv()

# Force insecure transport for local development
os.environ['AUTHLIB_INSECURE_TRANSPORT'] = '1'

db = SQLAlchemy()
login_manager = LoginManager()
oauth = OAuth()
mail = Mail()
scheduler = APScheduler()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-prod')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Mail Configuration
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

    # Scheduler Configuration
    app.config['SCHEDULER_API_ENABLED'] = True

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    oauth.init_app(app)
    mail.init_app(app)
    scheduler.init_app(app)

    # Configure Google OAuth
    google_client_id = os.getenv('GOOGLE_CLIENT_ID', '').strip()
    google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET', '').strip()
    discovery_url = os.getenv('GOOGLE_DISCOVERY_URL', 'https://accounts.google.com/.well-known/openid-configuration').strip()
    
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
    else:
        app.logger.warning("Google OAuth credentials not fully configured in .env")

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

    # Define the background job
    def check_for_reminders():
        with app.app_context():
            from .models import Event, User
            ist = pytz.timezone('Asia/Kolkata')
            now = datetime.now(ist)
            
            # Find events that are due but email has not been sent
            events_to_notify = Event.query.filter_by(email_sent=False).all()
            
            for event in events_to_notify:
                if event.is_expired: # is_expired now uses IST
                    user = User.query.get(event.user_id)
                    if user and user.email:
                        try:
                            msg = Message(
                                subject=f"Reminder: {event.title}",
                                recipients=[user.email],
                                body=f"Hi {user.username},\n\nThis is a reminder for your event: {event.title}\n\nDescription: {event.description}\nTime: {event.time}\n\nBest regards,\nStudentHub Team"
                            )
                            mail.send(msg)
                            # Update and commit immediately to prevent duplicates
                            event.email_sent = True
                            db.session.add(event)
                            db.session.commit()
                            print(f"Notification sent for event: {event.title}")
                        except Exception as e:
                            print(f"Email delivery failed for event '{event.title}'. Error: [REDACTED]")
                            db.session.rollback() # Rollback on error to keep status consistent

    # Add and start the job if not already running
    # Using a check for 'WERKZEUG_RUN_MAIN' to avoid double execution in debug mode
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        if not scheduler.running:
            scheduler.add_job(id='reminder_job', func=check_for_reminders, trigger='interval', seconds=60)
            scheduler.start()

    return app
