# backend/api/schemas.py

from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional
from typing import Optional, List


class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_length(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        if len(v) > 72:
            raise ValueError("Password must be 72 characters or less")
        return v

class UserLogin(BaseModel):
    """What the client sends to login."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """What we send back after successful login."""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    name: str
    email: str


class UserResponse(BaseModel):
    """Safe user representation — never includes password."""
    id: int
    name: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True   # Allows building from SQLAlchemy model objects

# ── Resume Schemas ─────────────────────────────────────────────────────────────
class ResumeResponse(BaseModel):
    id: int
    filename: str
    extracted_skills: Optional[List[str]] = []

    class Config:
        from_attributes = True

# ── Job Description Schemas ────────────────────────────────────────────────────
class JobDescriptionInput(BaseModel):
    job_title: str
    job_description: str
    resume_id: int

class SkillGapResponse(BaseModel):
    job_title: str
    required_skills: List[str]
    matched_skills: List[str]
    missing_skills: List[str]
    match_score: float
    recommendation: str