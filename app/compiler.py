import os
import re
import requests
from flask import Blueprint, render_template, request
from flask_login import login_required

compiler = Blueprint('compiler', __name__)

# Judge0 Community Edition Configuration
JUDGE0_URL = "https://ce.judge0.com/submissions?base64_encoded=false&wait=true"

# Language IDs for Judge0 CE
LANGUAGE_IDS = {
    "c": 75,          # GCC 11.4.0
    "cpp": 76,        # GCC 11.4.0
    "java": 91,       # OpenJDK 17
    "python": 92,     # Python 3.11.2
    "javascript": 93  # Node.js 18.15.0
}

@compiler.route('/compiler')
@login_required
def index():
    # Just render the page, logic is now handled via AJAX
    return render_template('compiler/index.html')

@compiler.route('/compiler/run', methods=['POST'])
@login_required
def run_code():
    data = request.json
    source_code = data.get('source_code', '')
    language_key = data.get('language', 'python')
    stdin = data.get('stdin', '')

    language_id = LANGUAGE_IDS.get(language_key)
    if not language_id:
        return {"error": "Invalid language selected"}, 400

    payload = {
        "source_code": source_code,
        "language_id": language_id,
        "stdin": stdin
    }

    try:
        response = requests.post(JUDGE0_URL, json=payload, timeout=15)
        if response.status_code in [200, 201]:
            result = response.json()
            
            # Extract relevant fields from Judge0 response
            # stdout, stderr, compile_output are initially null if not present
            output = result.get("stdout") or ""
            stderr = result.get("stderr") or ""
            compile_output = result.get("compile_output") or ""
            
            status = result.get("status", {}).get("description", "Unknown")
            time = result.get("time") # in seconds
            memory = result.get("memory") # in KB

            return {
                "stdout": output,
                "stderr": stderr,
                "compile_output": compile_output,
                "status": status,
                "time": time,
                "memory": memory
            }
        else:
            return {"error": f"Judge0 API Error: {response.status_code}"}, 500
            
    except Exception as e:
        return {"error": f"Execution failed: {str(e)}"}, 500

    return render_template('compiler/index.html', code=code, output=output, error=error, language=language)
