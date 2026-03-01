from flask import Blueprint, render_template, redirect, url_for, request, jsonify, session
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

    # 🔹 Manage Chat History in Session
    if 'chat_history' not in session:
        session['chat_history'] = []
    
    # 🔹 Identify if it's likely a follow-up question
    context_words = {'for', 'about', 'how', 'what', 'it', 'they', 'them', 'then', 'his', 'her', 'its', 'who'}
    query_words_set = set(user_query.split())
    has_history = len(session['chat_history']) > 0
    is_follow_up = has_history and (query_words_set.intersection(context_words) or len(query_words_set) <= 3)

    from .models import InterviewQuestion
    # 🔹 DB Match Search with Scoring
    greetings = {'hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'namaste', 'morning'}
    
    best_match = None
    max_score = 0

    # Skip DB match if it's a greeting or a likely follow-up
    if user_query not in greetings and not is_follow_up:
        stopwords = {'what', 'is', 'the', 'of', 'in', 'and', 'for', 'a', 'to', 'how', 'an', 'are', 'tell', 'me', 'about', 'difference', 'between'}
        query_words = [w for w in user_query.split() if w not in stopwords and len(w) > 2]
        
        all_questions = InterviewQuestion.query.all()
        for q in all_questions:
            q_text = q.question.lower()
            score = 0
            
            if user_query == q_text:
                score += 50
            elif len(user_query) > 3 and user_query in q_text:
                score += 30
                
            for word in query_words:
                if word in q_text:
                    score += 10
            
            if score > max_score:
                max_score = score
                best_match = q

    # If multiple words were searched, require a higher score (at least 20) to prevent single-word false matches
    threshold = 20 if "query_words" in locals() and len(query_words) > 1 else 10

    if best_match and max_score >= threshold:
        answer = f"[{best_match.category.upper()}] {best_match.answer}"
        # Store in history for context
        session['chat_history'].append({"role": "user", "content": user_query})
        session['chat_history'].append({"role": "assistant", "content": answer})
        session['chat_history'] = session['chat_history'][-10:] # Keep last 10
        session.modified = True
        return jsonify({"answer": answer})

    # 🔥 GROQ AI FALLBACK
    try:
        from dotenv import load_dotenv
        load_dotenv(override=True)
        
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or "YOUR_GROQ_API_KEY" in api_key:
            return jsonify({"answer": "AI service is initializing. Please try again in 1 minute."})

        client = Groq(api_key=api_key)
        
        # Build messages with history
        messages = [{"role": "system", "content": "You are StudentHub Assistant. Be concise and professional. You remember the conversation history."}]
        for hist in session['chat_history']:
            messages.append(hist)
        messages.append({"role": "user", "content": user_query})

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.7,
            max_tokens=300
        )
        
        ai_answer = response.choices[0].message.content
        
        # Update Session History
        session['chat_history'].append({"role": "user", "content": user_query})
        session['chat_history'].append({"role": "assistant", "content": ai_answer})
        session['chat_history'] = session['chat_history'][-10:] # Keep last 10
        session.modified = True
        
        return jsonify({"answer": f"[AI Assistant] {ai_answer}"})
    except Exception as e:
        print(f"GROQ ERROR: {e}")
        return jsonify({"answer": f"I'm currently unable to process advanced queries. Error: {str(e)}"})

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
