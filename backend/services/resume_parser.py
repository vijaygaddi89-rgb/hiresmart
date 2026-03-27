# backend/services/resume_parser.py

import re
import io
import json
import anthropic
from typing import Optional
from decouple import config
import pdfplumber
import docx
import spacy

# Load spaCy model once at module level
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = None
    print("⚠️ spaCy model not found. Run: py -m spacy download en_core_web_sm")

# Initialize Claude client once at module level
client = anthropic.Anthropic(api_key=config("ANTHROPIC_API_KEY"))


# ── Text Extraction ───────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract all text from a PDF file."""
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract all text from a DOCX file."""
    doc = docx.Document(io.BytesIO(file_bytes))
    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
    return "\n".join(paragraphs)


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Route to correct extractor based on file extension."""
    filename_lower = filename.lower()
    if filename_lower.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif filename_lower.endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {filename}")


# ── NLP Parsers ───────────────────────────────────────────────

def extract_email(text: str) -> Optional[str]:
    """Extract first email address found in text."""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(pattern, text)
    return match.group(0) if match else None


def extract_phone(text: str) -> Optional[str]:
    """Extract first phone number found in text."""
    pattern = r'(\+?\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}'
    match = re.search(pattern, text)
    return match.group(0).strip() if match else None


def extract_experience_years(text: str) -> Optional[int]:
    """Extract years of experience from text."""
    patterns = [
        r'(\d+)\+?\s*years?\s*of\s*experience',
        r'(\d+)\+?\s*years?\s*experience',
        r'experience\s*of\s*(\d+)\+?\s*years?',
        r'(\d+)\+?\s*yrs?\s*of\s*experience',
    ]
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return int(match.group(1))
    return None


def extract_name(text: str) -> Optional[str]:
    """Use spaCy NER to extract person name from resume."""
    if nlp is None:
        return None
    doc = nlp(text[:200])
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    return None


# ── Claude-Powered Skill Extraction ───────────────────────────

def extract_skills(text: str) -> list[str]:
    """
    Use Claude to intelligently extract skills from resume text.
    Much better than keyword matching — understands context.
    """
    resume_snippet = text[:3000]

    prompt = f"""You are an expert technical recruiter analyzing a resume.
Extract ALL technical skills, tools, frameworks, and technologies mentioned.

Resume Text:
{resume_snippet}

Return ONLY a JSON array of skills. No explanation, no markdown, no extra text.
Example: ["python", "machine learning", "fastapi", "postgresql", "docker"]

Rules:
- Lowercase all skills
- Include programming languages, frameworks, libraries, tools, platforms
- Include ML/AI skills, cloud platforms, databases, DevOps tools
- Be specific (e.g. "pytorch" not "deep learning frameworks")
- Max 40 skills

Return only the JSON array:"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = message.content[0].text.strip()

        # Strip markdown code blocks if Claude wraps response in them
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()

        skills = json.loads(response_text)
        if not isinstance(skills, list):
            return []
        return [str(skill).lower().strip() for skill in skills]

    except Exception as e:
        print(f"⚠️ Claude skill extraction failed: {e}. Returning empty list.")
        return []


# ── Main Parser ───────────────────────────────────────────────

def parse_resume(file_bytes: bytes, filename: str) -> dict:
    """
    Full pipeline:
    1. Extract raw text from PDF/DOCX
    2. Run all NLP parsers
    3. Claude extracts skills intelligently
    4. Return structured dict
    """
    raw_text = extract_text(file_bytes, filename)

    parsed = {
        "raw_text": raw_text,
        "extracted_name": extract_name(raw_text),
        "extracted_email": extract_email(raw_text),
        "extracted_phone": extract_phone(raw_text),
        "extracted_skills": extract_skills(raw_text),
        "years_of_experience": extract_experience_years(raw_text),
        "word_count": len(raw_text.split()),
    }

    return parsed