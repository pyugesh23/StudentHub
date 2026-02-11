# StudentHub - Industry-Grade Student Platform

## Project Overview
StudentHub is a unified, scalable platform designed to consolidate essential student tools—resume building, ATS evaluation, coding practice, and academic reminders—into a single modular system.

## Key Industry Statements (Viva-Safe)
- "The system follows a modular, template-driven architecture."
- "Resume templates are decoupled from business logic."
- "The design supports scalability without code refactoring."
- "StudentHub is designed as a real SaaS-style platform."

## Module Features

### 1. Authentication
- Secure login/registration with `Werkzeug` hashing.
- Session management via `Flask-Login`.

### 2. Dashboard
- Centralized hub for easy navigation.
- Real-time updates of upcoming events.

### 3. Resume Builder (Core)
- **Architecture**: Template-first, metadata-driven (Overleaf-style).
- **Templates**: Defined in `templates.json`, decoupled from logic.
- **Editor**: Inline editing with real-time saving.
- **Export**: Server-side PDF generation using ReportLab.

### 4. ATS Score Checker
- **Logic**: NLP-based keyword matching (set intersection).
- **Output**: Match score percentage and missing keywords.

### 5. Online Coding Compiler
- **Exec**: Controlled `subprocess` execution.
- **Languages**: Python, C, C++, Java supported (requires local compilers).

### 6. Event Reminders
- CRUD operations for academic deadlines.

## Setup Instructions
1. `pip install -r requirements.txt`
2. `python init_db.py` (Initialize Database)
3. `python run.py` (Start Server)
4. Access at `http://127.0.0.1:5000`

## Future Scope
- Premium resume templates
- AI resume rewriting
- Cloud database integration
