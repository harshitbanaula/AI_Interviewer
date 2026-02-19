# backend/app/repository.py

from sqlalchemy.orm import Session
from datetime import datetime
from app.database import InterviewSessionModel, InterviewAnswerModel
import os

#SESSION Operations

def db_create_session(db: Session, session_id : str,job_description: str,resume_text: str = None, candidate_name: str = None, candidate_email: str = None):
    
    try:
        row = InterviewSessionModel(
            session_id=session_id,
            job_description=job_description,
            resume_text=resume_text,
            candidate_name=candidate_name,
            candidate_email=candidate_email,
            status="created",
            created_at=datetime.utcnow()
        )
        db.add(row)
        db.commit()
        print(f"[DB] Session created: {session_id}")
        return True
    except Exception as e:
        db.rollback()
        print(f"[DB ERROR] create_session: {e}")
        return False



def db_start_session(db: Session, session_id: str):

    try:
        row = db.query(InterviewSessionModel).filter_by(session_id=session_id).first()
        if row:
            row.status = "active"
            row.started_at = datetime.utcnow()
            db.commit()
            print(f"[DB] Session started: {session_id}")
            return True
        return False
    except Exception as e:
        db.rollback()
        print(f"[DB ERROR] start_session: {e}")
        return False

def db_save_answer(
        db: Session,
    session_id: str,
    question_index: int,
    question_text: str,
    answer_text: str,
    score: dict,
    duration_seconds: float,
    audio_file_path: str,
    stage: str = None,
    project_mentioned: str = None,
    is_skipped: bool = False
        
):
    try:
        # ── Validate and normalize audio path ──
        if audio_file_path and os.path.exists(audio_file_path):
            # Store relative path only (cleaner for portability)
            audio_file_path = os.path.relpath(audio_file_path)
        else:
            audio_file_path = None

        row = InterviewAnswerModel(
            session_id=session_id,
            question_index=question_index,
            question_text=question_text,
            answer_text=answer_text,
            stage=stage,
            project_mentioned=project_mentioned,
            is_skipped=is_skipped,
            duration_seconds=duration_seconds,
            audio_file_path=audio_file_path,

            # Scores
            length_correctness=score.get("length_correctness"),
            semantic_correctness=score.get("semantic_correctness"),
            reasoning_quality=score.get("reasoning_quality"),
            clarity=score.get("clarity"),
            final_score=score.get("final_score"),
            strengths=score.get("strengths", []),
            improvements=score.get("improvements", []),

            # Timestamps auto-set by model defaults
            created_at=datetime.utcnow(),
            answered_at=datetime.utcnow()
        )
        
        db.add(row)
        db.commit()
        print(f"[DB] Answer saved: session={session_id}, Q{question_index}")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"[DB ERROR] save_answer Q{question_index}: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    


def db_complete_session(db: Session, session_id: str, summary: dict):
    try:
        row = db.query(InterviewSessionModel).filter_by(session_id=session_id).first()
        if row:
            row.status = "completed"
            row.completed_at = datetime.utcnow()
            row.total_duration_sec = summary.get("total_duration_seconds")
            row.average_score = summary.get("average_score")
            row.result = summary.get("result")
            row.completion_reason = summary.get("completion_reason")
            row.questions_asked = summary.get("questions_asked", 0)
            row.questions_answered = summary.get("questions_answered", 0)
            row.covered_projects = summary.get("covered_projects", [])
            row.feedback_text = summary.get("feedback", "")
            db.commit()
            print(f"[DB] Session completed: {session_id} → {summary.get('result')}")
            return True
        return False
    except Exception as e:
        db.rollback()
        print(f"[DB ERROR] complete_session: {e}")
        return False


# READ Operations

def db_get_session(db: Session, session_id: str):
    return db.query(InterviewSessionModel).filter_by(session_id=session_id).first()


def db_get_answers(db: Session, session_id: str):
    return db.query(InterviewAnswerModel).filter_by(session_id=session_id).order_by(InterviewAnswerModel.question_index).all()

def db_get_all_sessions(db: Session, limit: int = 50, offset: int = 0, status: str = None):
    query = db.query(InterviewSessionModel)
    if status:
        query = query.filter(InterviewSessionModel.status == status)

    return query.order_by(InterviewSessionModel.created_at.desc()).offset(offset).limit(limit).all()


def db_count_sessions(db: Session, status: str = None) -> int:
    query = db.query(InterviewSessionModel)
    
    if status:
        query = query.filter(InterviewSessionModel.status == status)
    
    return query.count()


def db_get_statistics(db: Session) -> dict:
    from sqlalchemy import func
    
    total = db.query(func.count(InterviewSessionModel.session_id)).scalar() or 0
    
    completed = db.query(InterviewSessionModel)\
        .filter(InterviewSessionModel.status == "completed")\
        .count()
    
    passed = db.query(InterviewSessionModel)\
        .filter(InterviewSessionModel.result == "PASS")\
        .count()
    
    avg_score = db.query(func.avg(InterviewSessionModel.average_score))\
        .filter(InterviewSessionModel.average_score.isnot(None))\
        .scalar()
    
    avg_duration = db.query(func.avg(InterviewSessionModel.total_duration_sec))\
        .filter(InterviewSessionModel.total_duration_sec.isnot(None))\
        .scalar()
    
    return {
        "total_interviews": total,
        "completed_interviews": completed,
        "passed_interviews": passed,
        "pass_rate": round(passed / completed * 100, 1) if completed > 0 else 0,
        "average_score": round(avg_score, 2) if avg_score else 0,
        "average_duration_minutes": round(avg_duration / 60, 1) if avg_duration else 0
    }
