from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.database import init_db, SessionLocal
from app.services.interview_state import create_session, get_session, get_active_session_count
from app.services.resume_parser import parse_resume
from app.services.job_inference import infer_job_description
from app.repository import db_create_session
from app.core.rate_limiter import RateLimit
from app.services.session_auth import create_session_token
from uuid import uuid4
from dotenv import load_dotenv
import re
from app.routers.ws import router as ws_router
from app.routers import finalize

load_dotenv()

app = FastAPI(title="AI Interviewer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── File size limits 
MAX_FILE_SIZE      = 3 * 1024 * 1024
MIN_FILE_SIZE      = 1024
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt"}

# ── Rate limit: 5 resume uploads per 10 minutes per IP 

_upload_limit = RateLimit("upload_resume", max_requests=5, window_seconds=600)


# ── Startup 
@app.on_event("startup")
def startup():
    init_db()
    print("[STARTUP] Database initialized")


# ── Routers 

app.include_router(ws_router)
app.include_router(finalize.router)


# ── Helpers 

def extract_candidate_name(resume_text: str) -> str:
    lines = [line.strip() for line in resume_text.split("\n") if line.strip()]

    if not lines:
        return "Unknown Candidate"

    first_line = lines[0]
    name_pattern = r'^([A-Z][a-z]+(?: [A-Z][a-z]+){1,3})$'
    if re.match(name_pattern, first_line):
        return first_line

    for line in lines[:5]:
        if line.lower().startswith("name:"):
            name = line.split(":", 1)[1].strip()
            if name:
                return name

    words = first_line.split()
    name_words = []
    for word in words[:3]:
        if word and word[0].isupper():
            name_words.append(word)
        else:
            break

    return " ".join(name_words) if name_words else "Unknown Candidate"


def extract_candidate_email(resume_text: str) -> str:
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.findall(email_pattern, resume_text)
    return matches[0] if matches else None


# ── Routes 

@app.get("/")
def health():
    return {
        "status": "running",
        "message": "AI Interviewer API is operational",
        "active_sessions": get_active_session_count()
    }


@app.post("/upload_resume")
async def upload_resume(
    request: Request,
    file: UploadFile = File(...),
    _: None = Depends(_upload_limit),
):
    # ── File validation 
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    if not content or len(content) < MIN_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too small. Minimum size: {MIN_FILE_SIZE} bytes"
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024 * 1024):.1f} MB"
        )

    # ── Parse resume 
    try:
        resume_text = parse_resume(file.filename, content)
        print(f" Resume parsed: {len(resume_text)} characters")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse resume: {str(e)}")

    if not resume_text or len(resume_text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Resume content too short or unreadable")

    # ── Extract candidate info 
    candidate_name  = extract_candidate_name(resume_text)
    candidate_email = extract_candidate_email(resume_text)
    print(f"Candidate: {candidate_name}, Email: {candidate_email or 'Not found'}")

    # ── Infer job description 
    try:
        job_description = infer_job_description(resume_text)
        print(f"Job inferred: {job_description}")
    except Exception as e:
        print(f" Job inference failed, using fallback: {e}")
        job_description = "Software Engineer"

    # ── Create session in Redis 
    try:
        session_id = str(uuid4())
        create_session(session_id, job_description, resume_text)
        print(f" Memory session created: {session_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")
    
    # Generate WS access token----------------
    token = create_session_token(session_id)

    # ── Create session in DB 
    try:
        db = SessionLocal()
        success = db_create_session(
            db=db,
            session_id=session_id,
            job_description=job_description,
            resume_text=resume_text,
            candidate_name=candidate_name,
            candidate_email=candidate_email,
        )
        db.close()

        if success:
            print(f"DB session created: {session_id}")
        else:
            print("DB session creation failed (non-critical)")

    except Exception as e:
        print(f"DB error (non-critical): {e}")

    return JSONResponse(
        status_code=201,
        content={
            "session_id": session_id,
            "token": token,
            "job_description": job_description,
            "candidate_name":  candidate_name,
            "status": "success",
            "message": "Resume uploaded successfully",
        }
    )


@app.get("/session/{session_id}")
def check_session(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "exists":           True,
        "session_id":       session_id,
        "questions_count":  len(session.questions),
        "answers_count":    len(session.answers),
        "completed":        session.completed,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)