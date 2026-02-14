import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv

load_dotenv()

# Force insecure transport for local development
os.environ['AUTHLIB_INSECURE_TRANSPORT'] = '1'

db = SQLAlchemy()
login_manager = LoginManager()
oauth = OAuth()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-prod')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    oauth.init_app(app)

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

    with app.app_context():
        db.create_all()

    return app
