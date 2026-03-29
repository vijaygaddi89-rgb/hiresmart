from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from api.auth import get_current_user
from models.models import User
from services.analytics_service import (
    compute_and_save_analytics,
    get_user_analytics_history,
    get_overall_stats,
    get_score_trend,
    get_role_breakdown,
    get_best_and_worst_sessions,
)

router = APIRouter(tags=["analytics"])


@router.post("/save/{session_id}")
def save_session_analytics(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Call after finishing a session.
    Computes stats from all feedback and saves/updates an Analytics record.
    """
    try:
        record = compute_and_save_analytics(db, current_user.id, session_id)
        return {
            "message": "Analytics saved successfully",
            "session_id": session_id,
            "job_role": record.job_role,
            "average_score": record.average_score,
            "answered_questions": record.answered_questions,
            "total_questions": record.total_questions,
            "top_skill": record.top_skill,
            "weak_skill": record.weak_skill,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")


@router.get("/history")
def get_analytics_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns all past session analytics for the current user, newest first."""
    records = get_user_analytics_history(db, current_user.id)
    return [
        {
            "id": r.id,
            "session_id": r.session_id,
            "job_role": r.job_role,
            "total_questions": r.total_questions,
            "answered_questions": r.answered_questions,
            "average_score": r.average_score,
            "top_skill": r.top_skill,
            "weak_skill": r.weak_skill,
            "created_at": r.created_at.isoformat(),
        }
        for r in records
    ]


@router.get("/overview")
def get_analytics_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aggregated stats across all sessions."""
    return get_overall_stats(db, current_user.id)


@router.get("/trend")
def get_trend(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Per-session score trend ordered oldest → newest. Use this for charts."""
    return get_score_trend(db, current_user.id)


@router.get("/role-breakdown")
def role_breakdown(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Avg score, session count, and best score grouped by job role."""
    return get_role_breakdown(db, current_user.id)


@router.get("/best-worst")
def best_worst_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns the best and worst sessions by average score."""
    return get_best_and_worst_sessions(db, current_user.id)