import google.generativeai as genai
from config import Config
import io
import pypdf
import docx
import re

def configure_gemini():
    if Config.GEMINI_API_KEY:
        genai.configure(api_key=Config.GEMINI_API_KEY)
        return True
    return False

def extract_text_from_bytes(content_bytes, filename):
    """
    Safely extracts text from PDF, DOCX, or TXT bytes.
    """
    if not content_bytes:
        return ""
        
    filename = filename.lower()
    
    try:
        if filename.endswith('.pdf'):
            reader = pypdf.PdfReader(io.BytesIO(content_bytes))
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            return text.strip()
            
        elif filename.endswith('.docx'):
            doc = docx.Document(io.BytesIO(content_bytes))
            text = "\n".join([para.text for para in doc.paragraphs])
            return text.strip()
            
        else:
            # Try UTF-8, fallback to latin-1 for corrupted text files
            try:
                return content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                return content_bytes.decode('latin-1')
    except Exception as e:
        print(f"Extraction Error: {str(e)}")
        return ""

def summarize_text(text):
    """
    Summarizes text using Gemini 2.5 Flash with safety checks.
    """
    if not configure_gemini():
        return "AI not configured."

    clean_text = text.strip()
    if len(clean_text) < 10:
        return "Document too short to summarize."

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        # Optimized prompt for professional output
        prompt = f"Summarize this document content concisely in 3-5 sentences. Use clear language:\n\n{clean_text[:15000]}"
        
        response = model.generate_content(prompt)
        
        # Safety check: check if the response was blocked
        if not response.candidates or not response.candidates[0].content.parts:
            return "The AI could not generate a summary for this content (it may have been flagged or blocked)."
            
        return response.text
    except Exception as e:
        return f"Summarization Error: {str(e)}"

def extract_tags(text):
    """
    Extracts 5 tags using regex cleaning to ensure consistent format.
    """
    if not configure_gemini() or not text:
        return []

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"List 5 key topics from this text as single words, separated by commas only:\n\n{text[:5000]}"
        
        response = model.generate_content(prompt)
        if not response.candidates or not response.candidates[0].content.parts:
            return ["Analysis"]

        # Clean tags: remove markdown, hashtags, and whitespace
        raw_tags = response.text
        tags = [re.sub(r'[^a-zA-Z0-9]', '', t.strip()) for t in raw_tags.split(",")]
        return [t for t in tags if t][:5]
    except Exception:
        return ["Document"]
