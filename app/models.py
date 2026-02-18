from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=True)
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.JSON, nullable=False) # Stores resume data
    template_id = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    time = db.Column(db.String(10), nullable=True) # Stores the time (e.g., "10:00 AM")
    description = db.Column(db.String(500))
    # type: e.g., 'exam', 'assignment', 'interview'
    type = db.Column(db.String(50), default='personal')

    @property
    def is_expired(self):
        """Checks if the event is in the past."""
        now = datetime.now()
        if not self.time:
            return now.date() > self.date.date()
        
        try:
            # time is typically in 'HH:MM' format from HTML time input
            hour, minute = map(int, self.time.split(':'))
            # An event at 10:30 is not 'expired' until 10:31:00
            event_datetime = self.date.replace(hour=hour, minute=minute, second=59, microsecond=999999)
            return now > event_datetime
        except (ValueError, AttributeError):
            return now.date() > self.date.date()
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    type = db.Column(db.String(50), default='info') # e.g., 'welcome', 'info', 'warning'
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('notifications', lazy=True))

class InterviewQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False) # e.g., Python, HR, DSA
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(20), default='Medium') # Easy, Medium, Hard

