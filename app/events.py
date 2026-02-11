from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import Event
from . import db
from datetime import datetime

events = Blueprint('events', __name__)

@events.route('/events', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        title = request.form.get('title')
        date_str = request.form.get('date')
        time_str = request.form.get('time')
        description = request.form.get('description')
        event_type = request.form.get('type')
        
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            new_event = Event(
                user_id=current_user.id,
                title=title,
                date=date_obj,
                time=time_str,
                description=description,
                type=event_type
            )
            db.session.add(new_event)
            db.session.commit()
            flash('Event added successfully!')
        except ValueError:
            flash('Invalid date format.')
            
        return redirect(url_for('events.index'))

    user_events = Event.query.filter_by(user_id=current_user.id).order_by(Event.date).all()
    return render_template('events/index.html', events=user_events)

@events.route('/events/delete/<int:event_id>')
@login_required
def delete(event_id):
    event = Event.query.get_or_404(event_id)
    if event.user_id != current_user.id:
        flash('Unauthorized')
        return redirect(url_for('events.index'))
    
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted.')
    return redirect(url_for('events.index'))
