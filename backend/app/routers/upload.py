import os
import uuid
import tempfile
from fastapi import APIRouter, UploadFile, File, Form
from app.services.resume_parser import parse_resume
from app.services.interview_state import create_session

router = APIRouter()


@router.post("/upload_resume")
async def upload_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...)
):
    try:
        file_bytes = await file.read()

        resume_text = parse_resume(
            filename=file.filename,
            content_bytes=file_bytes
        )

        session_id = create_session(
            resume_text=resume_text,
            job_description=job_description
        )

        return {
            "session_id": session_id,
            "message": "Resume uploaded and parsed successfully"
        }

    except Exception as e:
        return {"error": str(e)}
