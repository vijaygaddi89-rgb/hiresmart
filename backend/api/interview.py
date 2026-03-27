from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models.models import Resume, InterviewSession
from services.question_generator import generate_interview_questions
from api.auth import get_current_user
import json

router = APIRouter(tags=["Interview"])

class GenerateQuestionsRequest(BaseModel):
    job_description: str

@router.post("/generate-questions")
async def generate_questions(
    request: GenerateQuestionsRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get user's latest resume
    resume = db.query(Resume).filter(
        Resume.user_id == current_user.id
    ).order_by(Resume.created_at.desc()).first()  # ← fixed: uploaded_at → created_at

    if not resume:
        raise HTTPException(status_code=404, detail="No resume found. Please upload your resume first.")

    if not resume.raw_text:  # ← fixed: extracted_text → raw_text
        raise HTTPException(status_code=400, detail="Resume text not extracted. Please re-upload.")

    # Generate questions using RAG + Claude
    questions = await generate_interview_questions(
        resume_text=resume.raw_text,  # ← fixed here too
        job_description=request.job_description
    )

    # Save session to DB
    session = InterviewSession(
        user_id=current_user.id,
        resume_id=resume.id,
        questions=json.dumps(questions)
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "questions": questions,
        "total": len(questions)
    }