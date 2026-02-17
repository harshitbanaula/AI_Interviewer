# backend/app/repository.py

from sqlalchemy.orm import Session
from datetime import datetime
from app.database import InterviewSessionModel, InterviewAnswerModel

#SESSION Operations

def db_create_session(db: Session, session_id : str,job_description: str):

    row = InterviewSessionModel(
        session_id = session_id,
        job_description = job_description,
        created_at = datetime.utcnow(),
        status = "created"
    )
    db.add(row)
    db.commit()
    print(f"Session created in DB: {session_id}")


def db_start_session(db: Session, session_id: str):

    row = db.query(InterviewSessionModel).filter(InterviewSessionModel.session_id == session_id).first()
    if row:
        row.status = "active"
        row.started_at = datetime.utcnow()
        db.commit()
        print(f"Session started in DB: {session_id}")
        


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

        # Exact fields from evaluator.py score_answer()
        length_correctness=score.get("length_correctness"),
        semantic_correctness=score.get("semantic_correctness"),
        reasoning_quality=score.get("reasoning_quality"),
        clarity=score.get("clarity"),
        final_score=score.get("final_score"),
        strengths=score.get("strengths", []),
        improvements=score.get("improvements", []),

        answered_at=datetime.utcnow()
    )
    db.add(row)
    db.commit()
    print(f"[DB] Answer saved: session={session_id}, Q{question_index}")


def db_complete_session(db: Session, session_id: str, summary: dict):
    row = db.query(InterviewSessionModel).filter_by(session_id=session_id).first()
    if row:
        row.status = "completed"
        row.completed_at = datetime.utcnow()
        row.total_duration_sec = summary.get("total_duration_seconds")
        row.average_score = summary.get("average_score")
        row.result = summary.get("result")
        row.completion_reason = summary.get("completion_reason")
        row.questions_asked = summary.get("questions_asked",0)
        row.questions_answered = summary.get("questions_answered",0)
        row.covered_projects = summary.get("covered_projects", [])
        row.feedback = summary.get("feedback", "")
        db.commit()
        print(f"[DB] Session Completed: {session_id},-> {summary.get('result')}")


# READ Operations

def db_get_session(db: Session, session_id: str):
    return db.query(InterviewSessionModel).filter_by(session_id=session_id).first()


def db_get_answers(db: Session, session_id: str):
    return db.query(InterviewAnswerModel).filter_by(session_id=session_id).order_by(InterviewAnswerModel.question_index).all()

def db_get_all_sessions(db: Session, limit: int = 50, offset: int = 0):
    return db.query(InterviewSessionModel)\
        .order_by(InterviewSessionModel.created_at.desc())\
        .offset(offset).limit(limit).all()