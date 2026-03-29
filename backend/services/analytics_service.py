# services/analytics_service.py

from sqlalchemy.orm import Session
from models.models import Feedback, InterviewSession, Analytics
import json


def compute_and_save_analytics(db: Session, user_id: int, session_id: int) -> Analytics:
    """
    Called after a session is finished.
    Reads all Feedback rows for the session, computes stats, saves to Analytics.
    """
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == user_id
    ).first()

    if not session:
        raise ValueError(f"Session {session_id} not found for user {user_id}")

    feedbacks = db.query(Feedback).filter(
        Feedback.session_id == session_id,
        Feedback.user_id == user_id
    ).all()

    total_questions = len(json.loads(session.questions)) if session.questions else 0
    answered = len(feedbacks)
    avg_score = round(sum(f.score for f in feedbacks) / answered, 2) if answered > 0 else 0.0

    # Try to extract top/weak skill from question text (simple heuristic)
    top_skill, weak_skill = _extract_skill_insights(feedbacks)

    record = Analytics(
        user_id=user_id,
        session_id=session_id,
        job_role=session.job_role,
        total_questions=total_questions,
        answered_questions=answered,
        average_score=avg_score,
        top_skill=top_skill,
        weak_skill=weak_skill,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _extract_skill_insights(feedbacks):
    """
    Very simple: highest score feedback question = top_skill,
    lowest score = weak_skill. Trims question to first 60 chars.
    """
    if not feedbacks:
        return None, None

    sorted_fb = sorted(feedbacks, key=lambda f: f.score, reverse=True)
    top_skill = sorted_fb[0].question[:60] if sorted_fb[0].question else None
    weak_skill = sorted_fb[-1].question[:60] if sorted_fb[-1].question else None

    # Avoid returning same question for both
    if top_skill == weak_skill:
        weak_skill = None

    return top_skill, weak_skill


def get_user_analytics_history(db: Session, user_id: int) -> list:
    """Returns all analytics records for a user, newest first."""
    records = db.query(Analytics).filter(
        Analytics.user_id == user_id
    ).order_by(Analytics.created_at.desc()).all()
    return records


def get_overall_stats(db: Session, user_id: int) -> dict:
    """
    Aggregated stats across all sessions:
    - total sessions
    - overall avg score
    - best score session
    - total questions answered
    """
    records = get_user_analytics_history(db, user_id)

    if not records:
        return {
            "total_sessions": 0,
            "overall_avg_score": 0.0,
            "best_session_score": 0.0,
            "total_questions_answered": 0,
        }

    total_sessions = len(records)
    overall_avg = round(sum(r.average_score for r in records) / total_sessions, 2)
    best_score = round(max(r.average_score for r in records), 2)
    total_answered = sum(r.answered_questions for r in records)

    return {
        "total_sessions": total_sessions,
        "overall_avg_score": overall_avg,
        "best_session_score": best_score,
        "total_questions_answered": total_answered,
    }