from flask import Blueprint, render_template, request
from .models import InterviewQuestion
from . import db

interview = Blueprint('interview', __name__, url_prefix='/interview')

@interview.route('/')
def index():
    category = request.args.get('category', 'All')
    if category == 'All':
        questions = InterviewQuestion.query.all()
    else:
        questions = InterviewQuestion.query.filter_by(category=category).all()
    
    categories = db.session.query(InterviewQuestion.category).distinct().all()
    categories = [c[0] for c in categories]
    if 'All' not in categories:
        categories.insert(0, 'All')
        
    return render_template('interview/index.html', questions=questions, categories=categories, active_category=category)
