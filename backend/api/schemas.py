from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
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
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    name: str
    email: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class ResumeResponse(BaseModel):
    id: int
    filename: str
    extracted_skills: Optional[List[str]] = []

    class Config:
        from_attributes = True


class JobDescriptionInput(BaseModel):
    job_title: str
    job_description: str
    resume_id: int