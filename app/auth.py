from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
from .models import User, Notification
from . import db, oauth

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash('Please check your login details and try again.')
            return redirect(url_for('auth.login'))

        login_user(user, remember=remember)
        return redirect(url_for('main.dashboard'))

    return render_template('auth/login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user:
            flash('Email address already exists')
            return redirect(url_for('auth.register'))

        new_user = User(email=email, username=username)
        new_user.set_password(password) # Use the set_password method to hash!

        db.session.add(new_user)
        db.session.commit()

        # Create welcome notification
        welcome_note = Notification(
            user_id=new_user.id,
            message="Welcome to StudentHub! We're glad to have you here. Explore your dashboard to get started.",
            type='welcome'
        )
        db.session.add(welcome_note)
        db.session.commit()

        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@auth.route('/login/google')
def google_login():
    redirect_uri = url_for('auth.google_authorize', _external=True)
    return oauth.google.authorize_redirect(redirect_uri, prompt='consent')

@auth.route('/login/google/authorize')
def google_authorize():
    try:
        token = oauth.google.authorize_access_token()
    except Exception as e:
        print(f"OAuth Error: {str(e)}")
        flash(f'OAuth error: {str(e)}')
        return redirect(url_for('auth.login'))
        
    resp = token.get('userinfo')
    if not resp:
        flash('Failed to fetch user info from Google.')
        return redirect(url_for('auth.login'))
    
    email = resp.get('email')
    google_id = resp.get('sub') # Google's unique identifier for the user
    name = resp.get('name') or resp.get('given_name') or email.split('@')[0]
    
    # Try to find user by google_id first, then fallback to email
    user = User.query.filter_by(google_id=google_id).first()
    if not user:
        user = User.query.filter_by(email=email).first()
    
    if not user:
        # Create a new user if one doesn't exist
        import os
        user = User(email=email, username=name, google_id=google_id)
        # Set a random password to satisfy the NOT NULL constraint in the database
        user.set_password(os.urandom(24).hex())
        db.session.add(user)
        db.session.commit()

        # Create welcome notification
        welcome_note = Notification(
            user_id=user.id,
            message="Welcome to StudentHub! We're glad to have you here. Since it's your first time, check out the Resume Builder and Games!",
            type='welcome'
        )
        db.session.add(welcome_note)
        db.session.commit()
    elif not user.google_id:
        # Link existing email-based user to their Google ID
        user.google_id = google_id
        db.session.commit()
    
    login_user(user)
    return redirect(url_for('main.dashboard'))
