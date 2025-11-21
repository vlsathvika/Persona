import docx2txt
import fitz  # PyMuPDF
import docx
from io import BytesIO


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
    """Extract text from a DOCX file-like object using python-docx.

    Accepts a Streamlit UploadedFile (file-like) and returns plain text.
    Falls back to docx2txt only if python-docx parsing fails.
    """
    try:
        data = file.read()
        doc = docx.Document(BytesIO(data))
        paragraphs = [p.text for p in doc.paragraphs]
        # Join paragraphs with double newlines to preserve some spacing
        text = "\n\n".join(p for p in paragraphs if p and p.strip())
        return text if text.strip() else ""
    except Exception as e:
        try:
            # Attempt fallback using docx2txt (may require a file path); try passing bytes
            file.seek(0)
            return docx2txt.process(file)
        except Exception as e2:
            return f"Error reading DOCX: {e}; fallback error: {e2}"

def load_persona_profiles(path):
    import json
    with open(path, 'r') as f:
        return json.load(f)
