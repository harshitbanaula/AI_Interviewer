# # backend/app/main.py

# from fastapi import FastAPI, UploadFile, File, Form
# from fastapi.middleware.cors import CORSMiddleware
# from app.routers.ws import router as ws_router
# from app.services.interview_state import create_session
# from app.services.resume_parser import parse_resume
# from uuid import uuid4
# import os
# from dotenv import load_dotenv

# load_dotenv()

# app = FastAPI(title="AI Interviewer")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# from app.routers.upload import router as upload_router

# app.include_router(upload_router)
# app.include_router(ws_router)

# @app.get("/")
# def health():
#     return {"status": "running"}

# @app.post("/upload_resume")
# async def upload_resume(file: UploadFile = File(...), job_description: str = Form(...)):
#     try:
#         content = await file.read()
#         resume_text = parse_resume(file.filename, content)
#         session_id = str(uuid4())
#         create_session(session_id, job_description, resume_text)
#         return {"session_id": session_id}
#     except Exception as e:
#         return {"error": str(e)}





# # backend/app/main.py

# from fastapi import FastAPI, UploadFile, File, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from app.services.interview_state import create_session,get_session,get_active_session_count
# from app.services.resume_parser import parse_resume
# from uuid import uuid4
# import os
# from app.services.job_inference import infer_job_description
# from dotenv import load_dotenv


# load_dotenv()

# app = FastAPI(title="AI Interviewer")

# # CORS Configuration - CRITICAL for WebSocket
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Import routers
# from app.routers.ws import router as ws_router
# # Include WebSocket router FIRST
# app.include_router(ws_router)

# @app.get("/")
# def health():
#     return {"status": "running", "message": "AI Interviewer API is operational"}

# @app.post("/upload_resume")
# async def upload_resume(file: UploadFile = File(...)):
#     try:
#         print(f"Uploading resume: {file.filename}")
        
#         # Read file content
#         content = await file.read()
        
#         # Parse resume
#         resume_text = parse_resume(file.filename, content)
#         print(f"Resume parsed successfully: {len(resume_text)} characters")
#         job_description = infer_job_description(resume_text)
#         # Generate session ID
#         session_id = str(uuid4())
#         print(f"Generated session ID: {session_id}")
        
#         # Create session
#         create_session(session_id,job_description, resume_text)
#         print(f"Session created successfully")
        
#         return {
#             "session_id": session_id,
#             "job description ": job_description,
#             "status": "success",
#             "message": "Resume uploaded successfully"
#         }
        
#     except Exception as e:
#         print(f" Error uploading resume: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         return {
#             "error": str(e),
#             "status": "failed"
#         }

# @app.get("/session/{session_id}")
# def check_session(session_id: str):
#     """
#     Check if session exists (for debugging)
#     """
#     from app.services.interview_state import get_session
#     session = get_session(session_id)
    
#     if session:
#         return {
#             "exists": True,
#             "session_id": session_id,
#             "questions_count": len(session.questions),
#             "completed": session.completed
#         }
#     else:
#         return {
#             "exists": False,
#             "session_id": session_id
#         }

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)




# # backend/app/main.py
# # FIX #2 - PROPER HTTP STATUS CODES ON FAILURE

# from fastapi import FastAPI, UploadFile, File, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse
# from app.services.interview_state import create_session, get_session, get_active_session_count
# from app.services.resume_parser import parse_resume
# from app.services.job_inference import infer_job_description
# from uuid import uuid4
# from dotenv import load_dotenv

# load_dotenv()

# app = FastAPI(title="AI Interviewer")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# from app.routers.ws import router as ws_router
# app.include_router(ws_router)


# @app.get("/")
# def health():
#     return {
#         "status": "running",
#         "message": "AI Interviewer API is operational",
#         "active_sessions": get_active_session_count()
#     }


# @app.post("/upload_resume")
# async def upload_resume(file: UploadFile = File(...)):
#     """
#     Upload resume and create interview session.
#     Returns 400 for bad input, 500 for server errors.
#     """

#     # ── VALIDATE FILE ──
#     if not file.filename:
#         raise HTTPException(status_code=400, detail="No file provided")

#     allowed_extensions = [".pdf", ".doc", ".docx", ".txt"]
#     ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
#     if ext not in allowed_extensions:
#         raise HTTPException(
#             status_code=400,
#             detail=f"Invalid file type '{ext}'. Allowed: {allowed_extensions}"
#         )

#     # ── READ FILE ──
#     try:
#         content = await file.read()
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

#     if not content or len(content) == 0:
#         raise HTTPException(status_code=400, detail="Uploaded file is empty")

#     # ── PARSE RESUME ──
#     try:
#         resume_text = parse_resume(file.filename, content)
#         print(f"Resume parsed: {len(resume_text)} characters")
#     except Exception as e:
#         print(f"Resume parse error: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to parse resume: {str(e)}")

#     if not resume_text or len(resume_text.strip()) < 50:
#         raise HTTPException(status_code=400, detail="Resume content too short or unreadable")

#     # ── INFER JOB DESCRIPTION ──
#     try:
#         job_description = infer_job_description(resume_text)
#         print(f"Job inferred: {job_description}")
#     except Exception as e:
#         print(f"Job inference failed, using fallback: {e}")
#         job_description = "Software Engineer"   # Clean fallback (Fix #8 typo also fixed here)

#     # ── CREATE SESSION ──
#     try:
#         session_id = str(uuid4())
#         create_session(session_id, job_description, resume_text)
#         print(f" Session created: {session_id}")
#     except Exception as e:
#         print(f" Session creation error: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

#     return JSONResponse(
#         status_code=201,  # 201 Created - correct for resource creation
#         content={
#             "session_id": session_id,
#             "job_description": job_description,
#             "status": "success",
#             "message": "Resume uploaded successfully"
#         }
#     )


# @app.get("/session/{session_id}")
# def check_session(session_id: str):
#     """Check session status"""
#     session = get_session(session_id)

#     if not session:
#         raise HTTPException(status_code=404, detail="Session not found")

#     return {
#         "exists": True,
#         "session_id": session_id,
#         "questions_count": len(session.questions),
#         "answers_count": len(session.answers),
#         "completed": session.completed
#     }


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)



# backend/app/main.py - WITH DATABASE INTEGRATION

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.database import init_db, SessionLocal
from app.services.interview_state import create_session, get_session, get_active_session_count
from app.services.resume_parser import parse_resume
from app.services.job_inference import infer_job_description
from app.repository import db_create_session
from uuid import uuid4
from dotenv import load_dotenv
import re

load_dotenv()

app = FastAPI(title="AI Interviewer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Create DB tables on startup ──
@app.on_event("startup")
def startup():
    init_db()
    print("[STARTUP] Database initialized")

from app.routers.ws import router as ws_router
app.include_router(ws_router)


def extract_candidate_name(resume_text: str) -> str:
    lines = [line.strip() for line in resume_text.split("\n") if line.strip()]
    
    if not lines:
        return "Unknown Candidate"
    
    # Try first non-empty line
    first_line = lines[0]
    
    # Check if it looks like a name (2-4 capitalized words, no special chars)
    name_pattern = r'^([A-Z][a-z]+(?: [A-Z][a-z]+){1,3})$'
    if re.match(name_pattern, first_line):
        return first_line
    
    # Fallback: look for "Name:" pattern
    for line in lines[:5]:
        if line.lower().startswith("name:"):
            name = line.split(":", 1)[1].strip()
            if name:
                return name
    
    # Last resort: take first 2-3 capitalized words from first line
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




@app.get("/")
def health():
    return {
        "status": "running",
        "message": "AI Interviewer API is operational",
        "active_sessions": get_active_session_count()
    }


@app.post("/upload_resume")
async def upload_resume(file: UploadFile = File(...)):
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    allowed_extensions = [".pdf", ".doc", ".docx", ".txt"]
    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{ext}'. Allowed: {allowed_extensions}"
        )

    # ── Read file ──
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    if not content or len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # ── Parse resume ──
    try:
        resume_text = parse_resume(file.filename, content)
        print(f" Resume parsed: {len(resume_text)} characters")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse resume: {str(e)}")

    if not resume_text or len(resume_text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Resume content too short or unreadable")


    # ── Extract candidate info ──
    candidate_name = extract_candidate_name(resume_text)
    candidate_email = extract_candidate_email(resume_text)
    print(f"Candidate: {candidate_name}, Email: {candidate_email or 'Not found'}")


    # ── Infer job description ──
    try:
        job_description = infer_job_description(resume_text)
        print(f"Job inferred: {job_description}")
    except Exception as e:
        print(f" Job inference failed, using fallback: {e}")
        job_description = "Software Engineer"

    # ── Create session in memory ──
    try:
        session_id = str(uuid4())
        create_session(session_id, job_description, resume_text)
        print(f" Memory session created: {session_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

    # ── Create session in DB with candidate data ──
    try:
        db = SessionLocal()
        success = db_create_session(
            db=db,
            session_id=session_id,
            job_description=job_description,
            resume_text=resume_text,
            candidate_name=candidate_name,
            candidate_email=candidate_email
        )
        db.close()
        
        if success:
            print(f"DB session created: {session_id}")
        else:
            print(f"DB session creation failed (non-critical)")
            
    except Exception as e:
        print(f"DB error (non-critical): {e}")

    return JSONResponse(
        status_code=201,
        content={
            "session_id": session_id,
            "job_description": job_description,
            "candidate_name": candidate_name,
            "status": "success",
            "message": "Resume uploaded successfully"
        }
    )


@app.get("/session/{session_id}")
def check_session(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "exists": True,
        "session_id": session_id,
        "questions_count": len(session.questions),
        "answers_count": len(session.answers),
        "completed": session.completed
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)