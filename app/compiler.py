import os
import re
import requests
from flask import Blueprint, render_template, request
from flask_login import login_required

compiler = Blueprint('compiler', __name__)

# Piston API Configuration
# Option 1: Official Piston API (Recommended by User)
# Note: As of Feb 15, 2026, this may require whitelisting (returns 401).
PISTON_MIRRORS = [
    "https://p-as.io/api/v2/piston/execute",
    "https://piston.sh/api/v2/piston/execute",
    "https://rinstun.com/api/v2/piston/execute",
    "https://emkc.org/api/v2/piston/execute",
    "https://piston.engineer-man.com/api/v2/piston/execute"
]

# Judge0 Configuration (Backup Provider)
# Note: Using base64_encoded=false and checking for 400 errors.
JUDGE0_URL = "https://ce.judge0.com/submissions?base64_encoded=false&wait=true"
JUDGE0_LANG_MAP = {
    "python": 71,
    "c": 50,
    "cpp": 54,
    "java": 62
}

# Language Version Mapping for Piston
LANGUAGE_CONFIG = {
    "python": {"version": "3.10.0", "name": "python"},
    "c": {"version": "10.2.0", "name": "c"},
    "cpp": {"version": "10.2.0", "name": "cpp"},
    "java": {"version": "15.0.2", "name": "java"}
}

def get_java_filename(code):
    """
    Extracts the public class name from Java code to use as a filename.
    If no public class is found, it looks for the first class defined.
    Defaults to 'Main.java' if no class is found.
    """
    # Look for: public class [Name]
    public_class_match = re.search(r'public\s+class\s+([a-zA-Z0-9_$]+)', code)
    if public_class_match:
        return f"{public_class_match.group(1)}.java"
    
    # Fallback: Look for any class definition
    class_match = re.search(r'class\s+([a-zA-Z0-9_$]+)', code)
    if class_match:
        return f"{class_match.group(1)}.java"
        
    return "Main.java"

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
        stdin = request.form.get('stdin', '')
        
        if not code.strip():
            error = "Please provide some code to run."
            return render_template('compiler/index.html', code=code, output=output, error=error, language=language)

        config = LANGUAGE_CONFIG.get(language)
        if not config:
            error = f"Language '{language}' is not supported."
        else:
            # Determine filename (crucial for Java)
            filename = "script." + language
            if language == "java":
                filename = get_java_filename(code)
            elif language == "c":
                filename = "main.c"
            elif language == "cpp":
                filename = "main.cpp"
            elif language == "python":
                filename = "main.py"

            payload = {
                "language": config["name"],
                "version": config["version"],
                "files": [{"name": filename, "content": code}],
                "stdin": stdin
            }
            
            success = False
            provider_errors = []

            # 1. Try Piston Mirrors (Starting with Official emkc.org)
            for url in PISTON_MIRRORS:
                try:
                    response = requests.post(url, json=payload, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        run_result = data.get("run", {})
                        compile_result = data.get("compile", {})
                        
                        output = run_result.get("stdout", "")
                        error_out = run_result.get("stderr", "")
                        compile_error = compile_result.get("stderr", "")
                        
                        if compile_error:
                            error = compile_error
                        elif error_out:
                            error = error_out
                        
                        success = True
                        break
                    elif response.status_code == 401:
                        provider_errors.append(f"{url.split('/')[2]}: Restricted (401)")
                    else:
                        provider_errors.append(f"{url.split('/')[2]}: Error {response.status_code}")
                except Exception as e:
                    provider_errors.append(f"{url.split('/')[2]}: {str(e)[:50]}")
                    continue
            
            # 2. Try Judge0 Fallback if Piston failed
            if not success:
                judge0_id = JUDGE0_LANG_MAP.get(language)
                if judge0_id:
                    try:
                        # For Java in Judge0, it forces the filename to 'Main.java'.
                        # If the class is named something else, 'java Main' will fail.
                        # Fix: Rename the detected class to 'Main' in the code.
                        j0_code = code
                        if language == "java":
                            class_name = get_java_filename(code).replace(".java", "")
                            if class_name != "Main":
                                # Rename class definition
                                j0_code = re.sub(r'(class\s+)' + re.escape(class_name), r'\1Main', code)
                                # Rename constructors if any
                                j0_code = re.sub(r'(\b)' + re.escape(class_name) + r'(\s*\()', r'\1Main\2', j0_code)

                        j0_payload = {
                            "source_code": j0_code,
                            "language_id": judge0_id,
                            "stdin": stdin
                        }
                        
                        # Only add compiler options for C/C++ (fix for 422 error)
                        if language in ["c", "cpp"]:
                            j0_payload["compiler_options"] = "-lm"

                        # Try with base64_encoded=false first
                        response = requests.post(JUDGE0_URL, json=j0_payload, timeout=10)
                        
                        # If 400, try a simpler payload without stdin
                        if response.status_code == 400:
                            del j0_payload["stdin"]
                            response = requests.post(JUDGE0_URL, json=j0_payload, timeout=10)

                        if response.status_code in [200, 201]:
                            data = response.json()
                            output = data.get("stdout") or ""
                            error = data.get("stderr") or data.get("compile_output") or ""
                            
                            status_desc = data.get("status", {}).get("description")
                            if not output and not error and status_desc != "Accepted":
                                error = f"Judge0: {status_desc}"
                            
                            success = True
                        else:
                            provider_errors.append(f"Judge0: {response.status_code}")
                    except Exception as e:
                        provider_errors.append(f"Judge0: {str(e)[:50]}")

            if not success:
                error = "All providers failed. " + " | ".join(provider_errors)
                if "401" in error:
                    error += " (Note: Official Piston API now requires whitelisting. Contact EngineerMan on Discord.)"

    return render_template('compiler/index.html', code=code, output=output, error=error, language=language)
