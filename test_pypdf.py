
import io
from pypdf import PdfReader

# This is a test script to see what data we can get from pypdf visitors
def visitor_body(text, cm, tm, font_dict, font_size):
    if text.strip():
        # tm is the text matrix
        # font_size is the font size
        # font_dict has font name
        print(f"Text: {text[:20]} | Size: {font_size} | Pos: {tm[4]}, {tm[5]}")

def test_pdf_parsing(file_path):
    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            page.extract_text(visitor_text=visitor_body)
    except Exception as e:
        print(f"Error: {e}")

# I'll try to find a PDF in the uploads folder to test
import os
uploads_dir = "c:/Users/pyuge/OneDrive/Desktop/StudentHub/uploads/resumes"
if os.path.exists(uploads_dir):
    files = [f for f in os.listdir(uploads_dir) if f.endswith('.pdf')]
    if files:
        test_pdf_parsing(os.path.join(uploads_dir, files[0]))
    else:
        print("No PDF files found in uploads.")
else:
    print("Uploads directory not found.")
