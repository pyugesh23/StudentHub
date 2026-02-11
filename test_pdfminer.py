
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar
import os

def test_pdfminer(file_path):
    print(f"Testing {file_path}")
    try:
        pages = list(extract_pages(file_path))
        print(f"Found {len(pages)} pages")
        for page_layout in pages:
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    text = element.get_text().strip()
                    if text:
                        print(f"Container Text: {text[:30]}...")
                        # Just some basic info
                        for text_line in element:
                            for char in text_line:
                                if isinstance(char, LTChar):
                                    print(f"  Char: {char.get_text()} | Font: {char.fontname} | Size: {char.size:.2f}")
                                    break
                            break
            break 
    except Exception as e:
        print(f"Error: {e}")

uploads_dir = "c:/Users/pyuge/OneDrive/Desktop/StudentHub/uploads/resumes"
if os.path.exists(uploads_dir):
    files = [f for f in os.listdir(uploads_dir) if f.endswith('.pdf')]
    if files:
        test_pdfminer(os.path.join(uploads_dir, files[0]))
