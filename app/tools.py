from flask import Blueprint, render_template
from flask_login import login_required

tools = Blueprint('tools', __name__)

@tools.route('/tools')
@login_required
def index():
    return render_template('tools/index.html')
