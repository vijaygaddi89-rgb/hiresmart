"""
interview.py — Day 8: Full Session Orchestration
"""

import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import get_db
from models.models import User, Resume, InterviewSession, Feedback
from api.auth import get_current_user
from services.question_generator import generate_interview_questions as generate_questions_service
from services.answer_evaluator import evaluate_answer

router = APIRouter(tags=["interview"])


# ─────────────────────────────────────────────
# Pydantic Schemas
# ─────────────────────────────────────────────

class GenerateQuestionsRequest(BaseModel):
    job_description: str
    job_role: Optional[str] = "Software Engineer"
    resume_id: Optional[int] = None
    num_questions: int = 5

class EvaluateAnswerRequest(BaseModel):
    question: str
    answer: str
    job_role: Optional[str] = "Software Engineer"

class StartSessionRequest(BaseModel):
    job_role: str
    job_description: str = ""          # ← FIXED: was missing, caused empty questions
    resume_id: Optional[int] = None
    num_questions: int = 5

class SubmitAnswerRequest(BaseModel):
    session_id: int
    answer: str

class FinishSessionRequest(BaseModel):
    session_id: int


# ─────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────

def _get_resume_text(resume_id: Optional[int], user_id: int, db: Session) -> Optional[str]:
    if not resume_id:
        return None
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()
    return resume.raw_text if resume else None


# ─────────────────────────────────────────────
# EXISTING ENDPOINTS
# ─────────────────────────────────────────────

@router.post("/generate-questions")
async def api_generate_questions(
    request: GenerateQuestionsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resume_text = _get_resume_text(request.resume_id, current_user.id, db)

    questions = await generate_questions_service(
        resume_text=resume_text or "",
        job_description=request.job_description
    )

    session = InterviewSession(
        user_id=current_user.id,
        resume_id=request.resume_id,
        questions=json.dumps(questions),
        job_role=request.job_role,
        status="active"
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "job_role": request.job_role,
        "questions": questions,
        "total": len(questions)
    }


@router.post("/evaluate-answer")
async def api_evaluate_answer(
    request: EvaluateAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = await evaluate_answer(
        question=request.question,
        answer=request.answer,
        job_role=request.job_role
    )

    feedback_text = result.get("strengths", "") + " " + result.get("improvements", "")

    feedback = Feedback(
        user_id=current_user.id,
        session_id=None,
        question=request.question,
        answer=request.answer,
        score=result["score"],
        feedback_text=feedback_text.strip(),
        ideal_answer=result["ideal_answer"]
    )
    db.add(feedback)
    db.commit()

    return {
        "score": result["score"],
        "strengths": result.get("strengths", ""),
        "improvements": result.get("improvements", ""),
        "ideal_answer": result.get("ideal_answer", ""),
        "feedback": feedback_text.strip()
    }


@router.get("/my-feedback")
def get_my_feedback(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    feedbacks = db.query(Feedback).filter(
        Feedback.user_id == current_user.id
    ).order_by(Feedback.created_at.desc()).all()

    return {
        "total": len(feedbacks),
        "feedback": [
            {
                "id": f.id,
                "question": f.question,
                "answer": f.answer,
                "score": f.score,
                "feedback": f.feedback_text,
                "ideal_answer": f.ideal_answer,
                "session_id": f.session_id,
                "created_at": str(f.created_at)
            }
            for f in feedbacks
        ]
    }


# ─────────────────────────────────────────────
# SESSION ENDPOINTS
# ─────────────────────────────────────────────

@router.post("/start")
async def start_session(
    request: StartSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resume_text = _get_resume_text(request.resume_id, current_user.id, db)

    # ← FIXED: use job_description, fallback to job_role if empty
    questions = await generate_questions_service(
        resume_text=resume_text or "",
        job_description=request.job_description or request.job_role
    )

    # ← FIXED: guard against empty questions list
    if not questions:
        raise HTTPException(
            status_code=500,
            detail="Question generation failed. Upload your resume first, then retry."
        )

    session = InterviewSession(
        user_id=current_user.id,
        resume_id=request.resume_id,
        questions=json.dumps(questions),
        job_role=request.job_role,
        status="active"
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "job_role": request.job_role,
        "total_questions": len(questions),
        "current_question_index": 0,
        "current_question": questions[0],
        "message": f"Session started! Answer {len(questions)} questions to complete your mock interview."
    }


@router.get("/next-question")
def get_next_question(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status == "completed":
        return {
            "session_complete": True,
            "message": "This session is already completed. View your summary!",
            "session_id": session_id
        }

    questions = json.loads(session.questions)

    answered_count = db.query(Feedback).filter(
        Feedback.session_id == session_id,
        Feedback.user_id == current_user.id
    ).count()

    if answered_count >= len(questions):
        return {
            "session_complete": True,
            "message": "All questions answered! Click Finish to see your summary.",
            "session_id": session_id,
            "answered": answered_count,
            "total": len(questions)
        }

    return {
        "session_complete": False,
        "session_id": session_id,
        "current_question_index": answered_count,
        "current_question": questions[answered_count],
        "answered": answered_count,
        "total": len(questions),
        "progress_percent": int((answered_count / len(questions)) * 100)
    }


@router.post("/submit-answer")
async def submit_answer(
    request: SubmitAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == request.session_id,
        InterviewSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status == "completed":
        raise HTTPException(status_code=400, detail="Session already completed")

    questions = json.loads(session.questions)

    answered_count = db.query(Feedback).filter(
        Feedback.session_id == request.session_id,
        Feedback.user_id == current_user.id
    ).count()

    if answered_count >= len(questions):
        raise HTTPException(
            status_code=400,
            detail="All questions already answered. Please finish the session."
        )

    current_question = questions[answered_count]

    result = await evaluate_answer(
        question=current_question,
        answer=request.answer,
        job_role=session.job_role
    )

    feedback_text = result.get("strengths", "") + " " + result.get("improvements", "")

    feedback = Feedback(
        user_id=current_user.id,
        session_id=request.session_id,
        question=current_question,
        answer=request.answer,
        score=result["score"],
        feedback_text=feedback_text.strip(),
        ideal_answer=result["ideal_answer"]
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    new_answered_count = answered_count + 1
    is_last_question = new_answered_count >= len(questions)

    response = {
        "feedback_id": feedback.id,
        "question": current_question,
        "answer": request.answer,
        "score": result["score"],
        "feedback": feedback_text.strip(),
        "ideal_answer": result.get("ideal_answer", ""),
        "strengths": result.get("strengths", ""),
        "improvements": result.get("improvements", ""),
        "question_number": answered_count + 1,
        "total_questions": len(questions),
        "session_complete": is_last_question
    }

    if not is_last_question:
        response["next_question"] = questions[new_answered_count]
        response["next_question_index"] = new_answered_count
    else:
        response["message"] = "🎉 All questions answered! Click 'Finish Session' to see your full report."

    return response


@router.post("/finish")
def finish_session(
    request: FinishSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == request.session_id,
        InterviewSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status == "completed":
        return {"message": "Session already completed", "session_id": request.session_id}

    questions = json.loads(session.questions)
    answered_count = db.query(Feedback).filter(
        Feedback.session_id == request.session_id
    ).count()

    session.status = "completed"
    db.commit()

    return {
        "message": "Session completed successfully!",
        "session_id": request.session_id,
        "questions_answered": answered_count,
        "total_questions": len(questions)
    }


@router.get("/session-summary")
def get_session_summary(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    feedbacks = db.query(Feedback).filter(
        Feedback.session_id == session_id
    ).order_by(Feedback.created_at.asc()).all()

    if not feedbacks:
        raise HTTPException(status_code=404, detail="No answers found for this session")

    scores = [f.score for f in feedbacks]
    avg_score = round(sum(scores) / len(scores), 1)

    if avg_score >= 8:
        performance, performance_color = "🏆 Excellent", "green"
    elif avg_score >= 6:
        performance, performance_color = "👍 Good", "blue"
    elif avg_score >= 4:
        performance, performance_color = "📈 Needs Improvement", "orange"
    else:
        performance, performance_color = "⚠️ Needs Significant Work", "red"

    questions = json.loads(session.questions)

    return {
        "session_id": session_id,
        "job_role": session.job_role,
        "status": session.status,
        "avg_score": avg_score,
        "performance": performance,
        "performance_color": performance_color,
        "total_questions": len(questions),
        "answered_questions": len(feedbacks),
        "scores": scores,
        "highest_score": max(scores),
        "lowest_score": min(scores),
        "breakdown": [
            {
                "question_number": i + 1,
                "question": f.question,
                "your_answer": f.answer,
                "score": f.score,
                "feedback": f.feedback_text,
                "ideal_answer": f.ideal_answer,
            }
            for i, f in enumerate(feedbacks)
        ]
    }