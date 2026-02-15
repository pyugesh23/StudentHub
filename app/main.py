from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from .models import Event, Notification
from . import db

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/dashboard')
@login_required
def dashboard():
    from .models import Resume
    from datetime import datetime, timedelta
    
    events = Event.query.filter_by(user_id=current_user.id).order_by(Event.date).all()
    resume_count = Resume.query.filter_by(user_id=current_user.id).count()
    
    # Calculate upcoming deadlines (events in next 7 days)
    now = datetime.now()
    seven_days_later = now + timedelta(days=7)
    upcoming_deadlines = sum(1 for event in events 
                            if not event.is_expired and event.date <= seven_days_later)
    
    return render_template('dashboard/index.html', 
                          name=current_user.username, 
                          events=events,
                          resume_count=resume_count,
                          upcoming_deadlines=upcoming_deadlines)

@main.route('/notifications/read/<int:notification_id>')
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first_or_404()
    notification.is_read = True
    db.session.commit()
    return redirect(request.referrer or url_for('main.dashboard'))

