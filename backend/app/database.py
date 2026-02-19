# backend/app/databse.py

from sqlalchemy import create_engine,Index,ForeignKey
from sqlalchemy.orm import sessionmaker,DeclarativeBase,relationship
from sqlalchemy import (
    Column,String,Float,Integer,
    Boolean, DateTime, Text ,JSON
)
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL not set in environment.\n"
        "Add to .env: DATABASE_URL=postgresql://username:password@host:port/dbname"

    )

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# BASE CLASS
class Base(DeclarativeBase):
    pass

# Models

class InterviewSessionModel(Base):
    __tablename__ ="interview_sessions"

    session_id = Column(String, primary_key=True, index = True)
    job_description = Column(Text, nullable=False)

    candidate_name = Column(String, nullable=True)
    candidate_email = Column(String, nullable=True)
    resume_text = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    total_duration_sec = Column(Float, nullable=True)

    status = Column(String, default="created")
    completion_reason = Column(String, nullable=True)

    questions_asked =Column(Integer, default=0)
    questions_answered = Column(Integer, default=0)
    average_score = Column(Float, nullable=True)
    result = Column(String, nullable=True)

    covered_projects = Column(JSON, nullable=True)
    feedback = Column(Text, nullable=True)

    answers = relationship(
        "InterviewAnswerModel",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="select"
    )

class InterviewAnswerModel(Base):
    __tablename__ = "interview_answers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("interview_sessions.session_id",ondelete="CASCADE"), nullable=False,index = True)

    question_index = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    stage = Column(String, nullable=False)
    project_mentioned = Column(String, nullable=True)

    answer_text = Column(Text, nullable=False)
    is_skipped = Column(Boolean, default=False)
    duration_seconds = Column(Float, nullable=True)
    audio_file_path = Column(String, nullable=True)

    length_correctness = Column(Float, nullable=True)
    semantic_correctness = Column(Float, nullable=True)
    reasoning_quality = Column(Float, nullable=True)
    clarity = Column(Float, nullable=True)
    final_score = Column(Float, nullable=True)


    strengths = Column(JSON, default=list)
    improvements = Column(JSON, default=list)


    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    answered_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("InterviewSessionModel", back_populates="answers")

    __table_args__=(
        Index("idx_session_question", "session_id", "question_index"),
        # Query: SELECT * FROM answers WHERE session_id=X ORDER BY question_index
        # Without index: O(n log n) table scan
        # With index: O(log n) index lookup
    )
# create all tables

def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database initialized and tables created.")

# Db session dependency

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
