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
        # Template-specific defaults
        if template_id == 'harshibar':
            content = {
                "name": "Harshibar",
                "phone": "555.555.5555",
                "email": "hello@email.com",
                "youtube": "harshibar",
                "location": "U.S. Citizen",
                "experience": """
                <div style="margin-bottom: 12px;">
                    <div class="entry-header"><strong>YouTube</strong><span>Aug. 2019 – Present</span></div>
                    <div class="entry-subtitle">Creator (@harshibar)<span>San Francisco, CA</span></div>
                    <ul>
                        <li>Grew channel to <strong>60k subscribers in 1.5 years</strong>; created 80+ videos on tech and productivity</li>
                        <li>Conducted A/B testing on titles and thumbnails; <strong>increased video impressions by 2.5M</strong> in 3 months</li>
                        <li>Designed a Notion workflow to streamline video production and roadmapping; boosted productivity by 20%</li>
                        <li>Partnered with brands like <strong>Skillshare and Squarespace</strong> to expand their outreach via sponsorships</li>
                        <li><strong>Highlights:</strong> <u>The Problem with Productivity Apps</u>, <u>Obsidian App Review</u>, <u>Not-So-Minimal Desk Setup</u></li>
                    </ul>
                </div>
                <div style="margin-bottom: 12px;">
                    <div class="entry-header"><strong>Google Verily</strong><span>Aug. 2018 – Sept. 2019</span></div>
                    <div class="entry-subtitle">Software Engineer<span>San Francisco, CA</span></div>
                    <ul>
                        <li>Led front-end development of a dashboard to process 50k blood samples and detect early-stage cancer</li>
                        <li>Rebuilt a Quality Control product with input from 20 cross-functional stakeholders, <strong>saving $1M annually</strong></li>
                        <li>Spearheaded product development of a new lab workflow tool, leading to a 40% increase in efficiency; shadowed 10 core users, iterated on design docs, and implemented the solution with one engineer</li>
                    </ul>
                </div>
                <div>
                    <div class="entry-header"><strong>Amazon</strong><span>May 2017 – Aug. 2017</span></div>
                    <div class="entry-subtitle">Software Engineering Intern<span>Seattle, WA</span></div>
                    <ul>
                        <li>Worked on the Search Customer Experience Team; received a return offer for a full-time position</li>
                        <li>Shipped a <strong>new feature to 2M+ users</strong> to improve the search experience for movie series-related queries</li>
                        <li>Built a back-end database service in Java and implemented a front-end UI to support future changes</li>
                    </ul>
                </div>""",
                "projects": """
                <div style="margin-bottom: 8px;">
                    <div class="entry-header"><strong>Hyku Consulting</strong></div>
                    <ul>
                        <li>Mentored 15 students towards acceptance at top US boarding schools; achieved <strong>100% success rate</strong></li>
                        <li>Designed a <strong>collaborative learning ecosystem</strong> for students and parents with Trello, Miro, and Google Suite</li>
                    </ul>
                </div>
                <div style="margin-bottom: 8px;">
                    <div class="entry-header"><strong>Minimal Icon Pack</strong></div>
                    <ul>
                        <li>Designed and released 100+ minimal iOS and Android icons from scratch using Procreate and Figma</li>
                        <li>Marketed the product and design process on YouTube; accumulated over <strong>$250 in sales</strong> on Gumroad</li>
                    </ul>
                </div>
                <div>
                    <div class="entry-header"><strong>CommonIntern</strong></div>
                    <ul>
                        <li>Built a Python script to automatically apply to jobs on Glassdoor using BeautifulSoup and Selenium</li>
                        <li><strong>500 stars on GitHub</strong>; featured on Hackaday; made the front page of r/python and r/programming</li>
                    </ul>
                </div>""",
                "education": """
                <div>
                    <div class="entry-header"><strong>Wellesley College</strong><span>Aug. 2014 – May 2018</span></div>
                    <div class="entry-subtitle">Bachelor of Arts in Computer Science and Pre-Med<span>Wellesley, MA</span></div>
                    <ul>
                        <li><strong>Coursework:</strong> Data Structures, Algorithms, Databases, Computer Systems, Machine Learning</li>
                        <li><strong>Research:</strong> MIT Graybiel Lab (published author), MIT Media Lab (analyzed urban microbe spread)</li>
                    </ul>
                </div>""",
                "skills_languages": "Python, JavaScript (React.js), HTML/CSS, SQL (PostgreSQL, MySQL)",
                "skills_tools": "Figma, Notion, Jira, Trello, Miro, Google Analytics, GitHub, DaVinci Resolve, OBS"
            }
        elif template_id == 'academic_pro':
            content = {
                "name": "AKSHAY VAISHNAV",
                "address": "C-101, Dreamland Apartment, Backbone Park, Rajkot-360004, Gujarat",
                "phone": "91 720 393 7889",
                "email": "vaishnavakshay007@gmail.com",
                "degree": "Bachelor of Engineering in Mechanical Engineering",
                "edu_date": "August 2012 - May 2016",
                "university": "Sanjaybhai Rajguru College of Engineering, Rajkot",
                "edu_details": "Gujarat Technological University, CGPA: 8.38/10.00",
                "education_extra": """
                <div class="entry">
                    <div class="entry-header">
                        <span>HSC, Class XII</span>
                        <span>June 2010 - April 2012</span>
                    </div>
                    <div class="entry-subheader">
                        <span>Shree S.G. Dholakiya Higher Secondary School, Rajkot, Gujarat, 57%</span>
                    </div>
                </div>
                <div class="entry">
                    <div class="entry-header">
                        <span>SSC, Class X</span>
                        <span>March 2009 - March 2010</span>
                    </div>
                    <div class="entry-subheader">
                        <span>Shree S.G. Dholakiya Secondary School, Rajkot, Gujarat, 83%</span>
                    </div>
                </div>""",
                "interests": "Product Development, Design, Automobile, CAD/CAE, Finite Element Analysis, Optimization, Fluid Mechanics, Robotics, Modeling and Simulation",
                "skills_software": "Basic AUTOCAD, CATIA V5, ANSYS (Static Structural, Transient Structural, Static Thermal, Transient Thermal, Harmonic Response, Model analysis, Acoustic, Fluent), OptimumLap, MATLAB",
                "projects": """
                <div class="entry">
                    <div class="entry-header">
                        <span>Design Optimization of Hydraulic Press Plate using Finite Element Analysis</span>
                        <span>January 2016 - April 2016</span>
                    </div>
                    <div class="entry-subheader">
                        <span>Major Project as a part of curriculum</span>
                    </div>
                    <ul>
                        <li>An Industrial Defined Project in collaboration with Incredible Machines, Rajkot</li>
                        <li>Designed and performed an FEA analysis of the plates of Hydraulic machine with the capacity of 250-ton</li>
                        <li>Optimization in terms of design and material reduction, leading to cost effectiveness, considering minimum deformation of plates during operation</li>
                    </ul>
                </div>
                <div class="entry">
                    <div class="entry-header">
                        <span>Mathematical Modeling and Analysis of a Hydro-pneumatic Suspension Column of a Car</span>
                        <span>July 2015 - October 2015</span>
                    </div>
                    <div class="entry-subheader">
                        <span>Minor Project as a part of curriculum</span>
                    </div>
                    <ul>
                        <li>Modeled a 2-DOF system considering sprung and unsprung mass of the vehicle</li>
                        <li>Performed sensitivity analysis to minimize the displacement of sprung and unsprung mass caused by vehicle hitting a bump using Transfer Function approach</li>
                        <li>The settling time and displacement of the system were decreased using Hydro-pneumatic suspension system</li>
                    </ul>
                </div>
                <div class="entry">
                    <div class="entry-header">
                        <span>Design and Thermal analysis of Disk Brake Rotor using ANSYS</span>
                        <span>March 2016</span>
                    </div>
                    <div class="entry-subheader">
                        <span>GT Motorsports, a Formula Student Team of GTU</span>
                    </div>
                    <ul>
                        <li>Applied Energy Equation to calculate theoretical data for the input of simulation</li>
                        <li>Devised boundary conditions for modeling the system by calculating including Heat power and Heat flux</li>
                        <li>A Static thermal analysis in ANSYS Workbench using real time boundary conditions to obtain temperature distribution of Brake Rotor</li>
                    </ul>
                </div>
                <div class="entry">
                    <div class="entry-header">
                        <span>Design, Development and Analysis of Exhaust System and Muffler assembly</span>
                        <span>Sept 2015 - Jan 2016</span>
                    </div>
                    <div class="entry-subheader">
                        <span>GT Motorsports, a Formula Student Team of GTU</span>
                    </div>
                    <ul>
                        <li>Design and Development of complete muffler assembly for the reduction of noise under 110 dBC as per the rulebook</li>
                        <li>Modeling and Acoustics analysis of muffler assembly in ANSYS to determine the Transmission Loss</li>
                        <li>A CFD analysis of Exhaust Manifold using ANSYS Fluent to optimize the exhaust gas flow</li>
                    </ul>
                </div>"""
            }
        elif template_id == 'javid_pro':
            content = {
                "name": "Mohamed Javid",
                "website": "http://mohamedjavid.webs.com",
                "email": "smj.javid@hotmail.com",
                "phone": "91-9787815969",
                "objective": "learn the current state of the art in a creative and open environment, then identify the necessary process to expand on current knowledge, and prove the existence of the first cause.",
                "edu1_school": "SRM UNIVERSITY",
                "edu1_degree": "M.Tech in Robotics",
                "edu1_details": "Grad. May 2015 | Chennai, India",
                "edu1_gpa": "7.29 / 10.0",
                "edu2_school": "ANNA UNIVERSITY",
                "edu2_degree": "B.E in MECHANICAL ENGINEERING",
                "edu2_details": "Grad. May 2013 | Tamil Nadu, India",
                "edu2_gpa": "6.83 / 10.0",
                "linkedin": "smj-javid",
                "twitter": "@smj_javid",
                "facebook": "smj.javid",
                "course_post": "Kinematics and Dynamics of Robots, Robot Programming, Artificial Intelligence for Robotics, Robot Vision, Robotic Sensors",
                "course_under": "Engineering Graphics, Engineering Mechanics, Kinematics and Dynamics of Machinery, Manufacturing Technology, Engineering Thermodynamics, Finite Element Analysis, Automobile and Power plant Engineering",
                "skills_prog": "PLC • Ladder Diagram • Matlab, FBD • C • C++ • Python • Embedded C",
                "skills_soft": "KUKA Sim LAYOUT • Solidworks • DCS, AutoCAD • SCADA • PAC • HMI • VFD",
                "skills_lang": "Tamil • Urdu • English • German, Japanese",
                "exp1_company": "REDD ROBOTICS",
                "exp1_title": "ASSOCIATE ENGINEER, RESEARCH AND DEVELOPMENT",
                "exp1_date": "Nov 2015 – Present | Chennai, India",
                "exp2_company": "REDD ROBOTICS",
                "exp2_title": "ENGINEERING INTERN",
                "exp2_date": "Aug 2015 – Oct 2015 | Chennai, India",
                "proj1_title": "CHOCOLATE 3D PRINTER",
                "proj1_date": "Jun 2016 – Jul 2016 | REDD Robotics, Chennai, India",
                "proj1_desc": "Based on the same principals of additive layer manufacturing and plastic printing the chocolate printer is designed to provide the best possible results when printing in chocolate.",
                "projects_extra": """
                <div class="main-entry">
                    <div class="project-title">BIO 3D PRINTER</div>
                    <div class="main-entry-date">Mar 2016 – May 2016 | REDD Robotics, Chennai, India</div>
                    <p>Utilizes the layer-by-layer method to create tissue-like structures using bio inks.</p>
                </div>
                <div class="main-entry">
                    <div class="project-title">DESIGN AND FABRICATION OF AN OUTDOOR QUADCOPTER</div>
                    <div class="main-entry-date">Jun 2014 – May 2015 | SRM University, Chennai, India</div>
                    <p>An autonomous quadcopter is designed, fabricated and programmed to recognize, track and follow objects/human using vision based techniques.</p>
                </div>
                <div class="main-entry">
                    <div class="project-title">DESIGN AND IMPLEMENTATION OF DEBURRING TOOL AND HOLDER</div>
                    <div class="main-entry-date">Jan 2013 – May 2013 | Anna University, Tamil Nadu, India</div>
                    <p>A tool is designed in half trapezoidal shape of 35 degree in angle and it is attached to the drilling machine holder to remove the burr’s that are formed during drilling process.</p>
                </div>""",
                "training": """
                <div class="main-entry">
                    <div class="main-entry-header">POST GRADUATE DIPLOMA IN INDUSTRIAL AUTOMATION</div>
                    <div class="main-entry-date">Technocrat Automation, Chennai, India</div>
                    <p>Hands on practical experience in Industrial Automation Tools specializing in PLC, DCS, SCADA and VFD.</p>
                </div>
                <div class="main-entry">
                    <div class="main-entry-header">ADVANCED ROBOT PROGRAMMING IN KUKA ROBOTS</div>
                    <div class="main-entry-date">AKGEC-KUKA Robotics, Ghaziabad, U.P, India</div>
                    <p>Structured programming, Variables and declarations, Subprograms and functions, Data manipulation, Program execution control, Automatic external functions</p>
                </div>
                <div class="main-entry">
                    <div class="main-entry-header">BASIC ROBOT PROGRAMMING IN KUKA ROBOTS</div>
                    <div class="main-entry-date">AKGEC-KUKA Robotics, Ghaziabad, U.P, India</div>
                    <p>Offline Programming, Online Programming, Robot mastering and Tool calibration</p>
                </div>""",
                "publication": """
                <div class="main-entry">
                    <div class="main-entry-header">DESIGN AND FABRICATION OF AN OUTDOOR QUADCOPTER</div>
                    <p>International Journal of Applied Engineering Research, ISSN 0973-4562 Volume 10, Number 8 (2015) pp. 20703-20713</p>
                </div>"""
            }
        else:
            # Default content (Generic)
            content = {
                "name": "YOUR NAME HERE",
                "title": "Professional Title",
                "email": "hello@example.com",
                "phone": "+1 234 567 890",
                "location": "City, Country",
                "summary": "Your professional summary goes here...",
                "experience": "<ul><li>Work Experience 1</li><li>Work Experience 2</li></ul>",
                "education": "<p>Education Detail 1</p>",
                "skills": "Skill 1, Skill 2, Skill 3"
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
