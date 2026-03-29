from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from api.auth import get_current_user
from models.models import User
from services.analytics_service import (
    compute_and_save_analytics,
    get_user_analytics_history,
    get_overall_stats,
)

router = APIRouter(tags=["analytics"])


@router.post("/save/{session_id}")
async def save_session_analytics(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        record = compute_and_save_analytics(db, current_user.id, session_id)
        return {
            "message": "Analytics saved successfully",
            "session_id": session_id,
            "average_score": record.average_score,
            "answered_questions": record.answered_questions,
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
    stats = get_overall_stats(db, current_user.id)
    return stats