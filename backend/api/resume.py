from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
import ast

from database import get_db
from api.auth import get_current_user
from models.models import User, Resume
from services.resume_parser import parse_resume

router = APIRouter(tags=["Resume"])

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("/upload", status_code=201)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    filename = file.filename
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{ext}' not allowed. Use PDF or DOCX."
        )

    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 5MB."
        )

    try:
        parsed = parse_resume(file_bytes, filename)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse resume: {str(e)}"
        )

    existing = db.query(Resume).filter(Resume.user_id == current_user.id).first()

    if existing:
        existing.filename = filename
        existing.raw_text = parsed["raw_text"]
        existing.parsed_skills = str(parsed["extracted_skills"])
        existing.extracted_email = parsed["extracted_email"]
        existing.extracted_phone = parsed["extracted_phone"]
        existing.years_of_experience = parsed["years_of_experience"]
        db.commit()
        db.refresh(existing)
        resume = existing
    else:
        resume = Resume(
            user_id=current_user.id,
            filename=filename,
            raw_text=parsed["raw_text"],
            parsed_skills=str(parsed["extracted_skills"]),
            extracted_email=parsed["extracted_email"],
            extracted_phone=parsed["extracted_phone"],
            years_of_experience=parsed["years_of_experience"],
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)

    return {
        "message": "Resume uploaded and parsed successfully",
        "resume_id": resume.id,
        "filename": filename,
        "word_count": parsed["word_count"],
        "extracted_name": parsed["extracted_name"],
        "extracted_email": parsed["extracted_email"],
        "extracted_phone": parsed["extracted_phone"],
        "years_of_experience": parsed["years_of_experience"],
        "skills_found": parsed["extracted_skills"],
        "skills_count": len(parsed["extracted_skills"]),
    }


@router.get("/me")
def get_my_resume(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No resume found. Please upload one."
        )

    try:
        skills = ast.literal_eval(resume.parsed_skills) if resume.parsed_skills else []
    except (ValueError, SyntaxError):
        skills = []

    return {
        "resume_id": resume.id,
        "filename": resume.filename,
        "extracted_email": resume.extracted_email,
        "extracted_phone": resume.extracted_phone,
        "years_of_experience": resume.years_of_experience,
        "skills": skills,
        "uploaded_at": resume.created_at,
    }