



from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from app.routers.ws import router as ws_router
from app.services.interview_state import create_session
from app.services.resume_parser import parse_resume
from uuid import uuid4
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI Interviewer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers.upload import router as upload_router

app.include_router(upload_router)

app.include_router(ws_router)

@app.get("/")
def health():
    return {"status": "running"}

@app.post("/upload_resume")
async def upload_resume(file: UploadFile = File(...), job_description: str = Form(...)):
    try:
        content = await file.read()
        resume_text = parse_resume(file.filename, content)
        session_id = str(uuid4())
        create_session(session_id, job_description, resume_text)
        return {"session_id": session_id}
    except Exception as e:
        return {"error": str(e)}
