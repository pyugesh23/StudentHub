import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key-change-in-prod' # TODO: Use environment variable
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

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

    with app.app_context():
        db.create_all()

    return app
