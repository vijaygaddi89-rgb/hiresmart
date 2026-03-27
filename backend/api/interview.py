from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models.models import Resume, InterviewSession, Feedback
from services.question_generator import generate_interview_questions
from services.answer_evaluator import evaluate_answer
from api.auth import get_current_user
import json

router = APIRouter(tags=["Interview"])

# ─── Request Schemas ───────────────────────────────────────────────

class GenerateQuestionsRequest(BaseModel):
    job_description: str

class EvaluateRequest(BaseModel):
    question: str
    answer: str
    job_description: str = ""

# ─── Generate Interview Questions (Day 6) ──────────────────────────

@router.post("/generate-questions")
async def generate_questions(
    request: GenerateQuestionsRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resume = db.query(Resume).filter(
        Resume.user_id == current_user.id
    ).order_by(Resume.created_at.desc()).first()

    if not resume:
        raise HTTPException(status_code=404, detail="No resume found. Please upload your resume first.")

    if not resume.raw_text:
        raise HTTPException(status_code=400, detail="Resume text not extracted. Please re-upload.")

    questions = await generate_interview_questions(
        resume_text=resume.raw_text,
        job_description=request.job_description
    )

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

# ─── Evaluate Answer (Day 7) ───────────────────────────────────────

@router.post("/evaluate-answer")
async def evaluate_user_answer(
    request: EvaluateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    resume = db.query(Resume).filter(
        Resume.user_id == current_user.id
    ).order_by(Resume.created_at.desc()).first()

    resume_text = resume.raw_text if resume else "No resume uploaded."

    result = await evaluate_answer(
        question=request.question,
        answer=request.answer,
        resume_text=resume_text,
        job_description=request.job_description
    )

    feedback = Feedback(
        user_id=current_user.id,
        question=request.question,
        answer=request.answer,
        score=result["score"],
        feedback_text=f"STRENGTHS: {result['strengths']}\n\nIMPROVEMENTS: {result['improvements']}",
        ideal_answer=result["ideal_answer"]
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return {
        "feedback_id": feedback.id,
        "score": result["score"],
        "strengths": result["strengths"],
        "improvements": result["improvements"],
        "ideal_answer": result["ideal_answer"]
    }

# ─── Get My Feedback History ───────────────────────────────────────

@router.get("/my-feedback")
def get_my_feedback(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    feedbacks = db.query(Feedback).filter(
        Feedback.user_id == current_user.id
    ).order_by(Feedback.id.desc()).all()

    return [
        {
            "id": f.id,
            "question": f.question,
            "score": f.score,
            "feedback_text": f.feedback_text,
            "ideal_answer": f.ideal_answer
        }
        for f in feedbacks
    ]