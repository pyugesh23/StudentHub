import json
import re
import io
import os
from flask import Blueprint, render_template, request, Response, flash, redirect, url_for
from flask_login import login_required, current_user
from .models import Resume
from . import db
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import pypdf
import docx

resume = Blueprint('resume', __name__)

def get_templates():
    json_path = os.path.join(os.path.dirname(__file__), 'templates.json')
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def extract_text_from_pdf(filepath):
    text = ""
    try:
        reader = pypdf.PdfReader(filepath)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
    return text

def extract_text_from_docx(filepath):
    text = ""
    try:
        doc = docx.Document(filepath)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print(f"Error extracting DOCX text: {e}")
    return text

def parse_resume_content(text):
    """
    Basic parsing to extract contact info and dump rest into summary.
    Ideally this would use NLP or more complex regex.
    """
    content = {
        "name": "Your Name",
        "title": "Professional Title",
        "email": "",
        "phone": "",
        "summary": "",
        "skills": "Skill 1, Skill 2, ...",
        "experience": "<h5>Experience</h5><p>Extracted content below:</p>",
        "education": "<h5>Education</h5>"
    }
    
    # Try to find email
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    if email_match:
        content['email'] = email_match.group(0)
        
    # Try to find phone (simple regex)
    phone_match = re.search(r'(\+\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}', text)
    if phone_match:
        content['phone'] = phone_match.group(0)
        
    # Dump the rest into summary for now, assuming user will edit it
    # Cleaning up text slightly
    clean_text = re.sub(r'\n+', '\n', text).strip()
    content['summary'] = clean_text[:500] + "..." if len(clean_text) > 500 else clean_text
    
    # Also put full text in experience so they can copy-paste parts
    content['experience'] += f"<pre>{clean_text}</pre>"
    
    return content

@resume.route('/resume-builder')
@login_required
def gallery():
    templates = get_templates()
    return render_template('resume/gallery.html', templates=templates)

@resume.route('/resume-builder/edit/<template_id>', methods=['GET', 'POST'])
@resume.route('/resume-builder/edit/<template_id>/<int:resume_id>', methods=['GET', 'POST'])
@login_required
def editor(template_id, resume_id=None):
    # If editing an existing resume, check if it's an uploaded one
    # This handles cases where template_id might have been changed but we want to force uploaded view
    if resume_id:
        existing_resume = Resume.query.get(resume_id)
        if existing_resume and existing_resume.user_id == current_user.id:
            if 'uploaded_file' in existing_resume.content:
                template_id = 'uploaded'

    # Handle uploaded resumes editing
    if template_id == 'uploaded':
        if not resume_id:
            flash('Cannot create a new uploaded resume here. Please use the upload button on the dashboard.', 'error')
            return redirect(url_for('resume.my_resumes'))
            
        resume_data = Resume.query.get_or_404(resume_id)
        if resume_data.user_id != current_user.id:
            return "Unauthorized", 403
            
        if request.method == 'POST':
            resume_title = request.form.get('resume_title', '').strip()
            if not resume_title:
                flash('Resume title is required', 'error')
                return redirect(request.url)
                
            resume_data.title = resume_title
            
            if 'resume_file' in request.files:
                file = request.files['resume_file']
                if file.filename != '':
                    allowed_extensions = {'.pdf', '.doc', '.docx'}
                    file_ext = os.path.splitext(file.filename)[1].lower()
                    
                    if file_ext not in allowed_extensions:
                        flash('Invalid file type. Please upload PDF, DOC, or DOCX files.', 'error')
                        return redirect(request.url)
                        
                    # Remove old file
                    if 'uploaded_file' in resume_data.content:
                        upload_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'resumes')
                        old_filepath = os.path.join(upload_folder, resume_data.content['uploaded_file'])
                        if os.path.exists(old_filepath):
                            try:
                                os.remove(old_filepath)
                            except:
                                pass # Ignore errors deleting old file
                            
                    # Save new file
                    upload_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'resumes')
                    os.makedirs(upload_folder, exist_ok=True)
                    
                    import time
                    filename = f"{current_user.id}_{int(time.time())}_{file.filename}"
                    filepath = os.path.join(upload_folder, filename)
                    file.save(filepath)
                    
                    # Update content
                    # We need to assign a new dict to trigger SQLAlchemy update for JSON field sometimes
                    new_content = dict(resume_data.content) if resume_data.content else {}
                    new_content['uploaded_file'] = filename
                    new_content['file_type'] = file_ext
                    resume_data.content = new_content
            
            db.session.commit()
            flash('Resume updated successfully!', 'success')
            return redirect(url_for('resume.my_resumes'))
        
        return render_template('resume/edit_upload.html',
                             resume_title=resume_data.title,
                             file_type=resume_data.content.get('file_type', 'Unknown'),
                             original_filename=resume_data.content.get('uploaded_file', 'No file'),
                             resume_id=resume_id)
    if request.method == 'POST':
        # Get resume title from form
        resume_title = request.form.get('resume_title', '').strip()
        if not resume_title:
            flash('Please provide a resume title/role name', 'error')
            return redirect(request.url)
        
        # Get all form data except resume_title
        data = {k: v for k, v in request.form.to_dict().items() if k != 'resume_title'}
        
        if resume_id:
            # Update existing resume
            existing_resume = Resume.query.get_or_404(resume_id)
            if existing_resume.user_id != current_user.id:
                return "Unauthorized", 403
            
            existing_resume.title = resume_title
            existing_resume.content = data
            existing_resume.template_id = template_id
            db.session.commit()
            flash('Resume updated successfully!', 'success')
        else:
            # Create new resume
            new_resume = Resume(
                user_id=current_user.id,
                title=resume_title, 
                content=data,
                template_id=template_id
            )
            db.session.add(new_resume)
            db.session.commit()
            flash('Resume saved successfully!', 'success')
        
        return redirect(url_for('resume.my_resumes'))

    # For GET, render the editor
    templates = get_templates()
    selected_template = next((t for t in templates if t['id'] == template_id), None)
    
    if not selected_template:
        return "Template not found", 404

    # Check if editing existing resume
    resume_data = None
    resume_title = ""
    if resume_id:
        resume_data = Resume.query.get_or_404(resume_id)
        if resume_data.user_id != current_user.id:
            return "Unauthorized", 403
        content = resume_data.content
        resume_title = resume_data.title
    else:
        # Default content for a new resume
        content = {
            "name": "Your Name Here",
            "title": "Professional Title",
            "email": "email@example.com",
            "phone": "+1 234 567 890",
            "summary": "Brief professional summary...",
            "skills": "Python, JavaScript, SQL...",
            "experience": "<h5>Job Title</h5><p>Company | Date</p><ul><li>Achievement 1</li><li>Achievement 2</li></ul>",
            "education": "<h5>Degree</h5><p>University | Date</p>"
        }

    return render_template('resume/editor.html', 
                         template_id=template_id,
                         resume_id=resume_id,
                         resume_title=resume_title,
                         template_layout=selected_template['html_layout'],
                         content=content,
                         is_editing=resume_id is not None)

@resume.route('/resume-builder/my-resumes')
@login_required
def my_resumes():
    """Display all saved resumes for the current user"""
    resumes = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.created_at.desc()).all()
    templates = get_templates()
    
    # Create a dict for quick template lookup
    template_dict = {t['id']: t['name'] for t in templates}
    
    return render_template('resume/my_resumes.html', resumes=resumes, template_dict=template_dict)

@resume.route('/resume-builder/upload', methods=['POST'])
@login_required
def upload_resume():
    """Handle resume file upload from local system"""
    if 'resume_file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('resume.my_resumes'))
    
    file = request.files['resume_file']
    resume_title = request.form.get('resume_title', '').strip()
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('resume.my_resumes'))
    
    if not resume_title:
        flash('Please provide a resume title', 'error')
        return redirect(url_for('resume.my_resumes'))
    
    # Validate file extension
    allowed_extensions = {'.pdf', '.doc', '.docx'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        flash('Invalid file type. Please upload PDF, DOC, or DOCX files only.', 'error')
        return redirect(url_for('resume.my_resumes'))
    
    # Create uploads directory if it doesn't exist
    upload_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'resumes')
    os.makedirs(upload_folder, exist_ok=True)
    
    # Generate unique filename
    import time
    filename = f"{current_user.id}_{int(time.time())}_{file.filename}"
    filepath = os.path.join(upload_folder, filename)
    
    # Save file
    file.save(filepath)
    
    # Save to database with file path
    new_resume = Resume(
        user_id=current_user.id,
        title=resume_title,
        content={'uploaded_file': filename, 'file_type': file_ext},
        template_id='uploaded'
    )
    db.session.add(new_resume)
    db.session.commit()
    
    flash(f'Resume "{resume_title}" uploaded successfully!', 'success')
    return redirect(url_for('resume.my_resumes'))

@resume.route('/resume-builder/delete/<int:resume_id>', methods=['POST'])
@login_required
def delete_resume(resume_id):
    """Delete a resume"""
    resume_data = Resume.query.get_or_404(resume_id)
    if resume_data.user_id != current_user.id:
        return "Unauthorized", 403
    
    # If it's an uploaded resume, delete the file too
    if resume_data.template_id == 'uploaded' and 'uploaded_file' in resume_data.content:
        upload_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'resumes')
        filepath = os.path.join(upload_folder, resume_data.content['uploaded_file'])
        if os.path.exists(filepath):
            os.remove(filepath)
    
    db.session.delete(resume_data)
    db.session.commit()
    flash('Resume deleted successfully!', 'success')
    return redirect(url_for('resume.my_resumes'))

@resume.route('/resume-builder/view/<int:resume_id>')
@login_required
def view_file(resume_id):
    resume_data = Resume.query.get_or_404(resume_id)
    if resume_data.user_id != current_user.id:
        return "Unauthorized", 403

    # Check if this is an uploaded resume
    if 'uploaded_file' in resume_data.content:
        # Serve the uploaded file
        upload_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'resumes')
        filepath = os.path.join(upload_folder, resume_data.content['uploaded_file'])
        
        if os.path.exists(filepath):
            from flask import send_file
            # Use original filename for inline view, but with inline disposition
            safe_filename = "".join(c for c in resume_data.title if c.isalnum() or c in (' ', '-', '_')).strip()
            file_ext = resume_data.content.get('file_type', '.pdf')
            safe_filename = safe_filename.replace(' ', '_') + file_ext
            
            return send_file(filepath, as_attachment=False, download_name=safe_filename)
        else:
            return "File not found", 404
            
    return "Not an uploaded file", 404

@resume.route('/resume-builder/download/<resume_id>')
@login_required
def download(resume_id):
    resume_data = Resume.query.get_or_404(resume_id)
    if resume_data.user_id != current_user.id:
        return "Unauthorized", 403

    # Check if this is an uploaded resume
    if resume_data.template_id == 'uploaded' and 'uploaded_file' in resume_data.content:
        # Serve the uploaded file
        upload_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'resumes')
        filepath = os.path.join(upload_folder, resume_data.content['uploaded_file'])
        
        if os.path.exists(filepath):
            from flask import send_file
            # Use original filename for download
            safe_filename = "".join(c for c in resume_data.title if c.isalnum() or c in (' ', '-', '_')).strip()
            file_ext = resume_data.content.get('file_type', '.pdf')
            safe_filename = safe_filename.replace(' ', '_') + file_ext
            
            return send_file(filepath, as_attachment=True, download_name=safe_filename)
        else:
            flash('Resume file not found', 'error')
            return redirect(url_for('resume.my_resumes'))
    
    # Generate PDF for created resumes using ReportLab
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Simple PDF generation based on data
    # In a real app, this would interpret the template layout
    y = height - 50
    p.drawString(100, y, f"Name: {resume_data.content.get('name', 'N/A')}")
    y -= 20
    p.drawString(100, y, f"Email: {resume_data.content.get('email', 'N/A')}")
    y -= 20
    p.drawString(100, y, "Summary:")
    y -= 20
    p.drawString(120, y, resume_data.content.get('summary', ''))
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    # Use resume title as filename, sanitize it
    safe_filename = "".join(c for c in resume_data.title if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_filename = safe_filename.replace(' ', '_') + '.pdf'
    

    return Response(buffer, mimetype='application/pdf', 
                    headers={"Content-Disposition": f"attachment;filename={safe_filename}"})

@resume.route('/resume-builder/convert/<int:resume_id>', methods=['POST'])
@login_required
def convert_to_editable(resume_id):
    """Convert an uploaded resume to an editable format"""
    resume_data = Resume.query.get_or_404(resume_id)
    if resume_data.user_id != current_user.id:
        return "Unauthorized", 403
        
    if 'uploaded_file' not in resume_data.content:
        flash('This resume is already editable.', 'info')
        return redirect(url_for('resume.editor', template_id=resume_data.template_id, resume_id=resume_id))
        
    # Get file path
    upload_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'resumes')
    filepath = os.path.join(upload_folder, resume_data.content['uploaded_file'])
    
    if not os.path.exists(filepath):
        flash('Original file not found.', 'error')
        return redirect(url_for('resume.my_resumes'))
        
    # Extract text
    text = ""
    file_ext = resume_data.content.get('file_type', '').lower()
    
    if file_ext == '.pdf':
        text = extract_text_from_pdf(filepath)
    elif file_ext in ['.doc', '.docx']:
        text = extract_text_from_docx(filepath)
        
    if not text:
        flash('Could not extract text from file.', 'error')
        return redirect(url_for('resume.my_resumes'))
        
    # Parse content
    parsed_content = parse_resume_content(text)
    
    # Create new resume
    new_title = f"Editable Copy - {resume_data.title}"
    new_resume = Resume(
        user_id=current_user.id,
        title=new_title,
        content=parsed_content,
        template_id='classic' # Default to classic template
    )
    
    db.session.add(new_resume)
    db.session.commit()
    
    flash('Resume converted successfully! You can now edit the content.', 'success')
    return redirect(url_for('resume.editor', template_id='classic', resume_id=new_resume.id))
