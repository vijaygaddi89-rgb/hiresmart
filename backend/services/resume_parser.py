# backend/services/resume_parser.py

import re
import io
from typing import Optional
import pdfplumber
import docx
import spacy

# Load spaCy model once at module level (expensive to load repeatedly)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = None
    print("⚠️ spaCy model not found. Run: python -m spacy download en_core_web_sm")


# ── Skills Database ───────────────────────────────────────────
# A curated list of tech skills we scan for in resumes
TECH_SKILLS = {
    # Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "scala", "kotlin", "swift", "r", "matlab", "sql", "bash", "php", "ruby",

    # ML / Data Science
    "machine learning", "deep learning", "nlp", "computer vision",
    "scikit-learn", "sklearn", "tensorflow", "keras", "pytorch",
    "pandas", "numpy", "scipy", "matplotlib", "seaborn", "plotly",
    "xgboost", "lightgbm", "catboost", "huggingface", "transformers",
    "langchain", "openai", "llm", "rag", "faiss", "vector database",

    # Data Engineering
    "spark", "hadoop", "kafka", "airflow", "dbt", "etl",
    "snowflake", "redshift", "bigquery", "databricks",

    # Web / Backend
    "fastapi", "django", "flask", "nodejs", "express", "react", "vue",
    "angular", "nextjs", "graphql", "rest api", "microservices",

    # Databases
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "sqlite", "cassandra", "dynamodb",

    # DevOps / Cloud
    "docker", "kubernetes", "aws", "gcp", "azure", "terraform",
    "ci/cd", "jenkins", "github actions", "linux",

    # Tools
    "git", "jira", "confluence", "tableau", "power bi",
}


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


def extract_skills(text: str) -> list[str]:
    """Match resume text against known skills list."""
    text_lower = text.lower()
    found_skills = []
    for skill in TECH_SKILLS:
        # Use word boundary matching to avoid partial matches
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.append(skill)
    return sorted(found_skills)


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
    # Usually the name is in the first 200 characters
    doc = nlp(text[:200])
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    return None


# ── Main Parser ───────────────────────────────────────────────

def parse_resume(file_bytes: bytes, filename: str) -> dict:
    """
    Full pipeline:
    1. Extract raw text from PDF/DOCX
    2. Run all NLP parsers
    3. Return structured dict
    """
    # Step 1: Extract text
    raw_text = extract_text(file_bytes, filename)

    # Step 2: Parse everything
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