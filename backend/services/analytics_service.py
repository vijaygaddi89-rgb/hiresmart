from sqlalchemy.orm import Session
from sqlalchemy import func
from models.models import Feedback, InterviewSession, Analytics
import json


def compute_and_save_analytics(db: Session, user_id: int, session_id: int) -> Analytics:
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

    top_skill, weak_skill = _extract_skill_insights(feedbacks)

    # Check if analytics already saved for this session — update if so
    existing = db.query(Analytics).filter(
        Analytics.session_id == session_id,
        Analytics.user_id == user_id
    ).first()

    if existing:
        existing.total_questions = total_questions
        existing.answered_questions = answered
        existing.average_score = avg_score
        existing.top_skill = top_skill
        existing.weak_skill = weak_skill
        db.commit()
        db.refresh(existing)
        return existing

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
    if not feedbacks:
        return None, None

    sorted_fb = sorted(feedbacks, key=lambda f: f.score, reverse=True)

    top_skill = sorted_fb[0].question[:60] if sorted_fb[0].question else None

    # Only set weak_skill if there are multiple feedbacks and scores differ
    if len(sorted_fb) > 1 and sorted_fb[0].score != sorted_fb[-1].score:
        weak_skill = sorted_fb[-1].question[:60] if sorted_fb[-1].question else None
    else:
        weak_skill = None

    return top_skill, weak_skill


def get_user_analytics_history(db: Session, user_id: int) -> list:
    records = db.query(Analytics).filter(
        Analytics.user_id == user_id
    ).order_by(Analytics.created_at.desc()).all()
    return records


def get_overall_stats(db: Session, user_id: int) -> dict:
    records = get_user_analytics_history(db, user_id)

    if not records:
        return {
            "total_sessions": 0,
            "overall_avg_score": 0.0,
            "best_session_score": 0.0,
            "total_questions_answered": 0,
            "most_practiced_role": None,
            "improvement_trend": "no data",
        }

    total_sessions = len(records)
    overall_avg = round(sum(r.average_score for r in records) / total_sessions, 2)
    best_score = round(max(r.average_score for r in records), 2)
    total_answered = sum(r.answered_questions for r in records)

    # Most practiced role
    role_counts = {}
    for r in records:
        if r.job_role:
            role_counts[r.job_role] = role_counts.get(r.job_role, 0) + 1
    most_practiced_role = max(role_counts, key=role_counts.get) if role_counts else None

    # Improvement trend — compare last 3 sessions avg vs previous 3
    improvement_trend = _compute_trend(records)

    return {
        "total_sessions": total_sessions,
        "overall_avg_score": overall_avg,
        "best_session_score": best_score,
        "total_questions_answered": total_answered,
        "most_practiced_role": most_practiced_role,
        "improvement_trend": improvement_trend,
    }


def _compute_trend(records: list) -> str:
    if len(records) < 2:
        return "not enough data"

    # records are newest first
    recent = records[:3]
    older = records[3:6]

    recent_avg = sum(r.average_score for r in recent) / len(recent)

    if not older:
        return "improving" if recent_avg >= 6.0 else "needs practice"

    older_avg = sum(r.average_score for r in older) / len(older)

    diff = recent_avg - older_avg
    if diff >= 0.5:
        return "improving"
    elif diff <= -0.5:
        return "declining"
    else:
        return "stable"


def get_score_trend(db: Session, user_id: int) -> list:
    """Returns per-session score trend for charting — newest last."""
    records = db.query(Analytics).filter(
        Analytics.user_id == user_id
    ).order_by(Analytics.created_at.asc()).all()

    return [
        {
            "session_id": r.session_id,
            "job_role": r.job_role,
            "average_score": r.average_score,
            "answered_questions": r.answered_questions,
            "date": r.created_at.strftime("%d %b"),
        }
        for r in records
    ]


def get_role_breakdown(db: Session, user_id: int) -> list:
    """Returns avg score grouped by job role."""
    records = get_user_analytics_history(db, user_id)

    role_data = {}
    for r in records:
        role = r.job_role or "Unknown"
        if role not in role_data:
            role_data[role] = {"scores": [], "sessions": 0}
        role_data[role]["scores"].append(r.average_score)
        role_data[role]["sessions"] += 1

    return [
        {
            "job_role": role,
            "sessions": data["sessions"],
            "avg_score": round(sum(data["scores"]) / len(data["scores"]), 2),
            "best_score": round(max(data["scores"]), 2),
        }
        for role, data in role_data.items()
    ]


def get_best_and_worst_sessions(db: Session, user_id: int) -> dict:
    """Returns the best and worst sessions by average score."""
    records = get_user_analytics_history(db, user_id)

    if not records:
        return {"best": None, "worst": None}

    best = max(records, key=lambda r: r.average_score)
    worst = min(records, key=lambda r: r.average_score)

    def fmt(r):
        return {
            "session_id": r.session_id,
            "job_role": r.job_role,
            "average_score": r.average_score,
            "answered_questions": r.answered_questions,
            "date": r.created_at.strftime("%d %b %Y"),
        }

    return {
        "best": fmt(best),
        "worst": fmt(worst) if best.session_id != worst.session_id else None,
    }