import os
import requests
from flask import Blueprint, render_template, request
from flask_login import login_required

compiler = Blueprint('compiler', __name__)

# Piston API Configuration
PISTON_URL = "https://emkc.org/api/v2/piston/execute"

# Language Version Mapping for Piston
LANGUAGE_CONFIG = {
    "python": {"version": "3.10.0", "name": "python"},
    "c": {"version": "10.2.0", "name": "c"},
    "cpp": {"version": "10.2.0", "name": "cpp"},
    "java": {"version": "15.0.2", "name": "java"}
}

@compiler.route('/compiler', methods=['GET', 'POST'])
@login_required
def index():
    code = ""
    output = ""
    error = ""
    language = "python"
    
    if request.method == 'POST':
        code = request.form.get('code', '')
        language = request.form.get('language', 'python')
        
        if not code.strip():
            error = "Please provide some code to run."
            return render_template('compiler/index.html', code=code, output=output, error=error, language=language)

        try:
            config = LANGUAGE_CONFIG.get(language)
            if not config:
                error = f"Language '{language}' is not supported."
            else:
                payload = {
                    "language": config["name"],
                    "version": config["version"],
                    "files": [{"content": code}]
                }
                
                response = requests.post(PISTON_URL, json=payload, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    run_result = data.get("run", {})
                    compile_result = data.get("compile", {})
                    
                    # Output from execution
                    output = run_result.get("stdout", "")
                    
                    # Capture errors from both compilation and execution
                    error_out = run_result.get("stderr", "")
                    compile_error = compile_result.get("stderr", "")
                    
                    if compile_error:
                        error = compile_error
                    elif error_out:
                        error = error_out
                else:
                    error = f"Cloud Error ({response.status_code}): {response.text}"

        except requests.exceptions.Timeout:
            error = "Cloud execution timed out (10s limit)."
        except Exception as e:
            error = f"System Error: {str(e)}"

    return render_template('compiler/index.html', code=code, output=output, error=error, language=language)
