from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
import os
import re
from groq import Groq
from .models import Event, Notification, InterviewQuestion
from . import db

main = Blueprint('main', __name__)

@main.route('/chatbot/ask', methods=['POST'])
@login_required
def ask_assistant():
    data = request.json
    user_query = data.get('message', '').strip().lower()
    
    if not user_query:
        return jsonify({"answer": "I didn't quite catch that. Could you please rephrase?"})

    from .models import InterviewQuestion
    # 🔹 DB Match Search with Scoring
    greetings = {'hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'namaste', 'morning'}
    if user_query in greetings:
        best_match = None # Skip DB and let AI handle it
    else:
        stopwords = {'what', 'is', 'the', 'of', 'in', 'and', 'for', 'a', 'to', 'how', 'an', 'are', 'tell', 'me', 'about', 'difference', 'between'}
        query_words = [w for w in user_query.split() if w not in stopwords and len(w) > 2]
        
        all_questions = InterviewQuestion.query.all()
        best_match = None
        max_score = 0

        for q in all_questions:
            q_text = q.question.lower()
            score = 0
            
            # Exact sentence match gets highest priority
            if user_query == q_text:
                score += 50
            # Substring match only for longer queries to avoid "hi" match
            elif len(user_query) > 3 and user_query in q_text:
                score += 30
                
            # Keyword matches
            for word in query_words:
                if word in q_text:
                    score += 10
            
            if score > max_score:
                max_score = score
                best_match = q

    # If multiple words were searched, require a higher score (at least 20) to prevent single-word false matches
    threshold = 20 if "query_words" in locals() and len(query_words) > 1 else 10

    if best_match and max_score >= threshold:
        return jsonify({"answer": f"[{best_match.category.upper()}] {best_match.answer}"})

    # 🔥 GROQ AI FALLBACK
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or "YOUR_GROQ_API_KEY" in api_key:
            return jsonify({"answer": "AI service is initializing. Please try again in 1 minute."})

        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are StudentHub Assistant. Be concise and professional."},
                {"role": "user", "content": user_query}
            ],
            temperature=0.7,
            max_tokens=300
        )
        return jsonify({"answer": f"[AI Assistant] {response.choices[0].message.content}"})
    except Exception as e:
        print(f"GROQ ERROR: {e}")
        return jsonify({"answer": "I'm currently unable to process advanced queries. Please try again later."})

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
@main.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    new_username = request.form.get('username')
    if new_username:
        current_user.username = new_username
        db.session.commit()
    return redirect(request.referrer or url_for('main.dashboard'))
