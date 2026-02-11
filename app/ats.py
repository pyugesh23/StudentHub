from flask import Blueprint, render_template, request, flash
from flask_login import login_required
import re
import io
from pypdf import PdfReader
import docx
from collections import Counter
from .ats_utils import get_pdf_structure, get_docx_structure

ats = Blueprint('ats', __name__)

def extract_text_from_pdf(file_stream):
    try:
        file_stream.seek(0)
        reader = PdfReader(file_stream)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return ""

def extract_text_from_docx(file_stream):
    try:
        file_stream.seek(0)
        doc = docx.Document(file_stream)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except Exception as e:
        print(f"DOCX extraction error: {e}")
        return ""

def calculate_ats_score(resume_text, job_description=None, structure_data=None):
    results = {
        'total_score': 0,
        'categories': {
            'content': {'score': 0, 'checks': []},
            'sections': {'score': 0, 'checks': []},
            'formatting': {'score': 0, 'checks': []},
            'layout': {'score': 0, 'checks': []},
            'essentials': {'score': 0, 'checks': []},
            'tailoring': {'score': 0, 'checks': []}
        },
        'missing_keywords': [],
        'parsed_text_preview': resume_text[:1000] + "..." if len(resume_text) > 1000 else resume_text
    }

    words = re.findall(r'\w+', resume_text.lower())
    
    # 1. CONTENT ANALYSIS (20% Weight) - Reduced from 40% to make room for visuals
    action_verbs = {
        'implemented', 'developed', 'managed', 'led', 'created', 'designed', 'optimized', 'spearheaded', 
        'orchestrated', 'coordinated', 'achieved', 'launched', 'accelerated', 'administered', 'analyzed',
        'arranged', 'authored', 'budgeted', 'built', 'calculated', 'centralized', 'clarified', 'collaborated',
        'composed', 'conducted', 'consolidated', 'constructed', 'consulted', 'controlled', 'converted',
        'counseled', 'criticized', 'cultivated', 'customized', 'debugged', 'decreased', 'delegated',
        'delivered', 'demonstrated', 'depicted', 'detailed', 'determined', 'devised', 'directed',
        'discovered', 'drafted', 'educated', 'eliminated', 'enabled', 'enforced', 'engineered',
        'enhanced', 'established', 'evaluated', 'examined', 'executed', 'expanded', 'expedited',
        'explained', 'facilitated', 'finalized', 'focused', 'forecasted', 'formed', 'formulated',
        'fostered', 'generated', 'guided', 'handled', 'identified', 'illustrated', 'improved',
        'increased', 'influenced', 'informed', 'initiated', 'inspected', 'inspired', 'installed',
        'instigated', 'instructed', 'insured', 'integrated', 'interpreted', 'investigated', 'itemized'
    }
    verbs_found = [w for w in words if w in action_verbs]
    verbs_score = min(100, len(set(verbs_found)) * 10)
    
    metrics_found = len(re.findall(r'\d+%|\$\d+|[0-9]+[\s]*(?:percent|dollars|users|employees|clients|revenue|profit|growth|scale|impact|saved|reduced|increased|improved)', resume_text, re.I))
    impact_score = min(100, metrics_found * 20)
    
    cliches = {'passionate', 'hardworking', 'team-player', 'guru', 'ninja', 'motivated', 'synergy', 'thought-leader'}
    cliches_found = [w for w in words if w in cliches]
    cliche_penalty = len(set(cliches_found)) * 5
    
    content_score = max(0, round(((verbs_score * 0.6) + (impact_score * 0.4)) - cliche_penalty))
    
    results['categories']['content']['score'] = content_score
    results['categories']['content']['checks'] = [
        {'name': 'Action Verbs', 'status': 'pass' if verbs_score >= 70 else 'fail', 
         'message': f'Found {len(set(verbs_found))} unique action verbs. Try adding more leadership words like "Spearheaded" or "Accelerated".' if verbs_score < 70 else f'Great use of {len(set(verbs_found))} unique action verbs!'},
        {'name': 'Impact Metrics', 'status': 'pass' if impact_score >= 60 else 'fail', 
         'message': f'Found only {metrics_found} quantifiable results. Proof your impact with percentages (%) or numbers.' if impact_score < 60 else f'Excellent job quantifying your impact with {metrics_found} metrics.'}
    ]

    # 2. SECTIONS & STRUCTURE (15% Weight)
    essential_sections = {
        'Experience': ([r'experience', r'employment', r'work history', r'background'], "Your professional work history is missing or not clearly labeled."),
        'Education': ([r'education', r'academic', r'degree'], "Your academic background couldn't be detected."),
        'Skills': ([r'skills', r'technologies', r'expertise', r'tools'], "A dedicated 'Skills' section helps highlight your technical toolkit."),
        'Summary': ([r'summary', r'objective', r'profile'], "A Professional Summary at the top helps frame your value proposition.")
    }
    found_sections = 0
    for section, (patterns, help_text) in essential_sections.items():
        found = any(re.search(p, resume_text, re.I) for p in patterns)
        if found: found_sections += 1
        results['categories']['sections']['checks'].append({
            'name': f'{section} Section',
            'status': 'pass' if found else 'fail',
            'message': help_text if not found else f'Found your {section} section.'
        })
    results['categories']['sections']['score'] = int((found_sections / len(essential_sections)) * 100)

    # 3. FORMATTING & STYLE (15% Weight) - NEW
    formatting_score = 100
    formatting_checks = []
    
    if structure_data:
        # Check font sizes
        font_sizes = [item['size'] for item in structure_data if item.get('size')]
        if font_sizes:
            avg_size = sum(font_sizes) / len(font_sizes)
            small_text_count = len([s for s in font_sizes if s < 9])
            if small_text_count / len(font_sizes) > 0.1:
                formatting_score -= 20
                formatting_checks.append({'name': 'Font Size', 'status': 'fail', 'message': 'Some of your text is too small (below 9pt). This can make it hard for recruiters to read.'})
            else:
                formatting_checks.append({'name': 'Font Size', 'status': 'pass', 'message': 'Font sizes are consistently readable.'})
        
        # Check fonts (Heuristic for professionalism)
        unprofessional_fonts = ['comic', 'papyrus', 'chiller', 'curlz', 'joker']
        fonts_found = {item['font'].lower() for item in structure_data if item.get('font')}
        bad_fonts = [f for f in fonts_found if any(up in f for up in unprofessional_fonts)]
        if bad_fonts:
            formatting_score -= 30
            formatting_checks.append({'name': 'Font Choice', 'status': 'fail', 'message': f'Avoid using unprofessional fonts like "{bad_fonts[0]}". Stick to cleaner fonts like Arial, Calibri, or Inter.'})
        else:
            formatting_checks.append({'name': 'Font Choice', 'status': 'pass', 'message': 'Professional font choices detected.'})

        # Font Consistency Check - NEW
        if len(fonts_found) > 2:
            formatting_score -= 15
            formatting_checks.append({'name': 'Font Consistency', 'status': 'warn', 'message': f'You are using {len(fonts_found)} different fonts. Using more than 2 fonts can make the layout look cluttered.'})
        else:
            formatting_checks.append({'name': 'Font Consistency', 'status': 'pass', 'message': 'Good font consistency.'})
    else:
        formatting_score = 70 # Default if no structure data
        formatting_checks.append({'name': 'Visual Data', 'status': 'warn', 'message': 'Detailed styling data could not be extracted.'})

    results['categories']['formatting']['score'] = max(0, formatting_score)
    results['categories']['formatting']['checks'] = formatting_checks

    # 4. STRUCTURE & LAYOUT (15% Weight) - NEW
    layout_score = 100
    layout_checks = []
    
    if structure_data:
        # Double Column Detection (Heuristic based on X-coordinates)
        x_positions = [item['x'] for item in structure_data if item.get('x')]
        if len(x_positions) > 10:
            # Check if there's a significant amount of text in the second half of the page
            page_width_est = 600 # standard PDF width roughly
            right_side_count = len([x for x in x_positions if x > page_width_est / 2.5])
            if right_side_count / len(x_positions) > 0.3:
                layout_score -= 40
                layout_checks.append({'name': 'Page Layout', 'status': 'fail', 'message': 'Double-column layout detected. ATS systems often struggle with columns; single-column is safer.'})
            else:
                layout_checks.append({'name': 'Page Layout', 'status': 'pass', 'message': 'Single-column layout detected, which is ideal for ATS.'})
        
        # Check for consistent alignment
        if x_positions:
            unique_starts = len(set([round(x, -1) for x in x_positions])) # Group by 10px
            if unique_starts > 15:
                layout_score -= 15
                layout_checks.append({'name': 'Alignment', 'status': 'warn', 'message': 'Your text alignments seem inconsistent. A clean, left-aligned structure is more professional.'})
            else:
                layout_checks.append({'name': 'Alignment', 'status': 'pass', 'message': 'Good, consistent text alignment.'})
        
        # Density Check - NEW
        text_length = len(resume_text)
        if text_length > 100:
            density = text_length / len(structure_data) if structure_data else 0
            if density > 80:
                layout_score -= 10
                layout_checks.append({'name': 'Density', 'status': 'warn', 'message': 'Your text blocks look very dense. Try adding more bullet points or whitespace between sections.'})
            elif density < 20:
                layout_score -= 10
                layout_checks.append({'name': 'Density', 'status': 'warn', 'message': 'Your resume looks a bit sparse. Try expanding on your achievements with more detail.'})
    else:
        layout_score = 70
        layout_checks.append({'name': 'Structural Data', 'status': 'warn', 'message': 'Layout analysis limited for this file type.'})

    results['categories']['layout']['score'] = max(0, layout_score)
    results['categories']['layout']['checks'] = layout_checks

    # 5. ATS ESSENTIALS (15% Weight)
    contact_checks = {
        'Email': (r'[\w\.-]+@[\w\.-]+', "Provide a valid email address."),
        'Phone': (r'\+?[\d\s\-\.\(\)]{10,18}', "Include a professional phone number."),
        'Socials': (r'(?:linkedin\.com\/in\/|github\.com/|portfolio|behance\.net)', "Add your LinkedIn or Portfolio link.")
    }
    found_contacts = 0
    for label, (pattern, help_text) in contact_checks.items():
        found = bool(re.search(pattern, resume_text, re.I))
        if found: found_contacts += 1
        results['categories']['essentials']['checks'].append({
            'name': label, 'status': 'pass' if found else 'fail', 'message': help_text if not found else f'{label} detected.'
        })
    
    word_count = len(words)
    length_status = 'pass' if 200 <= word_count <= 1000 else 'fail' if word_count < 200 else 'warn'
    results['categories']['essentials']['checks'].append({'name': 'Length', 'status': length_status, 'message': f'{word_count} words is a good length.' if length_status == 'pass' else 'Your resume is too short or too long.'})
    
    results['categories']['essentials']['score'] = round(((found_contacts / 3) * 70) + (30 if length_status == 'pass' else 15))

    # 6. TAILORING (20% Weight)
    has_jd = bool(job_description and job_description.strip())
    if has_jd:
        resume_words_set = set(words)
        job_words = set(re.sub(r'[^a-zA-Z0-9\s]', '', job_description.lower()).split())
        stop_words = {'and', 'the', 'to', 'of', 'a', 'in', 'is', 'for', 'with', 'on', 'at', 'by', 'an', 'be', 'this', 'that'}
        job_keywords = {w for w in job_words if len(w) > 3 and w not in stop_words}
        
        if job_keywords:
            matched = resume_words_set.intersection(job_keywords)
            tailoring_score = (len(matched) / len(job_keywords)) * 100
            results['missing_keywords'] = sorted(list(job_keywords - resume_words_set))[:10]
            results['categories']['tailoring']['score'] = round(tailoring_score)
            results['categories']['tailoring']['checks'].append({
                'name': 'Job Match', 'status': 'pass' if tailoring_score >= 50 else 'fail', 'message': 'Integrated some JD keywords.' if tailoring_score > 20 else 'Low keyword match with JD.'
            })
    else:
        results['categories']['tailoring']['score'] = 75
        results['categories']['tailoring']['checks'].append({'name': 'Core Relevance', 'status': 'pass', 'message': 'No JD provided.'})
    
    # FINAL WEIGHTED SCORE
    weights = {'content': 0.2, 'sections': 0.15, 'formatting': 0.15, 'layout': 0.15, 'essentials': 0.15, 'tailoring': 0.2}
    total = sum(results['categories'][cat]['score'] * weight for cat, weight in weights.items())
    results['total_score'] = round(total)
    
    # Improvements list - Now more comprehensive
    results['improvements'] = []
    
    # Priority 1: All Fails
    for cat_id in results['categories']:
        for check in results['categories'][cat_id]['checks']:
            if check['status'] == 'fail':
                results['improvements'].append(check['message'])
                
    # Priority 2: All Warns (Always include them now)
    for cat_id in results['categories']:
        for check in results['categories'][cat_id]['checks']:
            if check['status'] == 'warn':
                results['improvements'].append(check['message'])
    
    # Priority 3: Context-aware gaps
    if results['categories']['content']['score'] < 90:
        if verbs_score < 90:
            results['improvements'].append(f"Strength Tip: Your resume uses {len(set(verbs_found))} action verbs. For a top-tier resume, aim for 15+ unique leadership verbs.")
        if impact_score < 90:
            results['improvements'].append(f"Result Tip: We found {metrics_found} metrics. Try to quantify at least 5-7 achievements with numbers or % to prove your value.")
            
    if has_jd and results['categories']['tailoring']['score'] < 85:
        top_missing = ", ".join([f'"{m.capitalize()}"' for m in results['missing_keywords'][:3]])
        results['improvements'].append(f"JD Match: You're missing key skills like {top_missing} mentioned in the job description.")

    # Remove duplicates while preserving order
    results['improvements'] = list(dict.fromkeys(results['improvements']))
    
    return results

@ats.route('/ats-checker', methods=['GET', 'POST'])
@login_required
def ats_checker():
    report = None
    resume_text = ""
    job_desc = ""
    
    if request.method == 'POST':
        job_desc = request.form.get('job_desc', '')
        resume_file = request.files.get('resume_file')
        
        if resume_file and resume_file.filename != '':
            filename = resume_file.filename.lower()
            file_copy = io.BytesIO(resume_file.read())
            resume_file.seek(0)
            
            structure_data = None
            if filename.endswith('.pdf'):
                resume_text = extract_text_from_pdf(file_copy)
                structure_data = get_pdf_structure(file_copy)
            elif filename.endswith('.docx'):
                resume_text = extract_text_from_docx(file_copy)
                structure_data = get_docx_structure(file_copy)
            else:
                flash('Unsupported format.', 'danger')
        
            if resume_text:
                report = calculate_ats_score(resume_text, job_desc, structure_data)
            else:
                flash('Please upload a resume.', 'warning')
    
    return render_template('resume/ats.html', report=report, resume_text=resume_text, job_desc=job_desc)
