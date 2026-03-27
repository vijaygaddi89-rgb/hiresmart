from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models.models import Resume
from services.job_parser import extract_skills_from_jd
from api.auth import get_current_user
from models.models import User
import json
import ast

router = APIRouter(tags=["jobs"])


# --- Request/Response Schemas ---

class JobAnalyzeRequest(BaseModel):
    job_title: str
    job_description: str


class JobAnalyzeResponse(BaseModel):
    job_title: str
    required_skills: list[str]
    total_skills_found: int


class SkillGapResponse(BaseModel):
    job_title: str
    resume_skills: list[str]
    required_skills: list[str]
    matched_skills: list[str]
    missing_skills: list[str]
    match_percentage: float


# --- Endpoints ---

@router.post("/analyze", response_model=JobAnalyzeResponse)
async def analyze_job_description(
    request: JobAnalyzeRequest,
    current_user: User = Depends(get_current_user)
):
    skills = await extract_skills_from_jd(request.job_title, request.job_description)
    return JobAnalyzeResponse(
        job_title=request.job_title,
        required_skills=skills,
        total_skills_found=len(skills)
    )


@router.get("/skill-gap", response_model=SkillGapResponse)
async def get_skill_gap(
    job_title: str,
    job_description: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Get user's resume from DB
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="No resume found. Please upload your resume first.")

    # 2. Parse resume skills — stored as Python list string e.g. "['python', 'sql']"
    try:
        resume_skills = ast.literal_eval(resume.parsed_skills) if resume.parsed_skills else []
    except (ValueError, SyntaxError, TypeError):
        resume_skills = []

    # 3. Extract job skills via Claude
    job_skills = await extract_skills_from_jd(job_title, job_description)

    # 4. Normalize to lowercase for fair comparison
    resume_skills_lower = [s.lower().strip() for s in resume_skills]
    job_skills_lower = [s.lower().strip() for s in job_skills]

    # 5. Compute matched and missing
    matched = [s for s in job_skills_lower if s in resume_skills_lower]
    missing = [s for s in job_skills_lower if s not in resume_skills_lower]

    # 6. Match percentage
    match_pct = (len(matched) / len(job_skills_lower) * 100) if job_skills_lower else 0.0

    return SkillGapResponse(
        job_title=job_title,
        resume_skills=resume_skills,
        required_skills=job_skills,
        matched_skills=matched,
        missing_skills=missing,
        match_percentage=round(match_pct, 1)
    )