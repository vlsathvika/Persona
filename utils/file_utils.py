import docx2txt
import fitz  # PyMuPDF

def extract_text_from_file(uploaded_file):
    if uploaded_file.name.endswith('.pdf'):
        return extract_text_from_pdf(uploaded_file)
    elif uploaded_file.name.endswith('.docx'):
        return extract_text_from_docx(uploaded_file)
    else:
        return "Unsupported file type."

def extract_text_from_pdf(file):
    text = ""
    try:
        with fitz.open(stream=file.read(), filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
    except Exception as e:
        text = f"Error reading PDF: {e}"
    return text

def extract_text_from_docx(file):
    try:
        return docx2txt.process(file)
    except Exception as e:
        return f"Error reading DOCX: {e}"

def load_persona_profiles(path):
    import json
    with open(path, 'r') as f:
        return json.load(f)
