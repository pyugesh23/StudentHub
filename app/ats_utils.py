
import docx
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBox, LTChar
import io

def get_pdf_structure(file_stream):
    """
    Extracts text with font and coordinate info from PDF.
    """
    structure = []
    try:
        # Seek to beginning in case stream was read before
        file_stream.seek(0)
        for page_layout in extract_pages(file_stream):
            for element in page_layout:
                if isinstance(element, LTTextBox):
                    for line in element:
                        line_text = line.get_text().strip()
                        if not line_text:
                            continue
                            
                        sizes = []
                        fonts = []
                        for char in line:
                            if isinstance(char, LTChar):
                                sizes.append(char.size)
                                fonts.append(char.fontname)
                        
                        if sizes:
                            structure.append({
                                'text': line_text,
                                'x': element.x0,
                                'y': element.y0,
                                'size': sum(sizes) / len(sizes),
                                'font': fonts[0] if fonts else "Unknown"
                            })
    except Exception as e:
        print(f"PDF Structure extraction error: {e}")
    return structure

def get_docx_structure(file_stream):
    """
    Extracts structure from DOCX.
    """
    structure = []
    try:
        file_stream.seek(0)
        doc = docx.Document(file_stream)
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
                
            # Heuristic for size/font in docx
            # We take the first run's properties as representative
            size = 11.0 # default
            font = "Normal"
            if para.runs:
                run = para.runs[0]
                if run.font.size:
                    size = run.font.size.pt
                if run.font.name:
                    font = run.font.name
            
            structure.append({
                'text': text,
                'x': 0, # docx doesn't give coords easily, but we can detect indentation
                'y': 0,
                'size': size,
                'font': font,
                'alignment': para.alignment
            })
    except Exception as e:
        print(f"DOCX Structure extraction error: {e}")
    return structure
