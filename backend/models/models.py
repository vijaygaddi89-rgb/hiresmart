from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    resumes = relationship("Resume", back_populates="user")
    sessions = relationship("InterviewSession", back_populates="user")
    feedbacks = relationship("Feedback", back_populates="user")              # ← ADDED


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    raw_text = Column(Text, nullable=True)
    parsed_skills = Column(Text, nullable=True)
    extracted_email = Column(String, nullable=True)
    extracted_phone = Column(String, nullable=True)
    years_of_experience = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="resumes")
    sessions = relationship("InterviewSession", back_populates="resume")


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)
    questions = Column(Text, nullable=True)
    job_role = Column(String, nullable=True)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="sessions")
    resume = relationship("Resume", back_populates="sessions")
    feedbacks = relationship("Feedback", back_populates="session")


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)        # ← ADDED
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=True)  # ← made nullable
    question = Column(Text, nullable=True)
    answer = Column(Text, nullable=True)
    score = Column(Integer, nullable=True)
    feedback_text = Column(Text, nullable=True)
    ideal_answer = Column(Text, nullable=True)                               # ← ADDED
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="feedbacks")                  # ← ADDED
    session = relationship("InterviewSession", back_populates="feedbacks")
class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=True)
    job_role = Column(String, nullable=True)
    total_questions = Column(Integer, default=0)
    answered_questions = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    top_skill = Column(String, nullable=True)       # highest-scoring topic
    weak_skill = Column(String, nullable=True)      # lowest-scoring topic
    created_at = Column(DateTime, default=datetime.utcnow)    