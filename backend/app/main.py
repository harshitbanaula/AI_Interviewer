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





# backend/app/main.py

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from app.services.interview_state import create_session
from app.services.resume_parser import parse_resume
from uuid import uuid4
import os
from app.services.job_inference import infer_job_description
from dotenv import load_dotenv


load_dotenv()

app = FastAPI(title="AI Interviewer")

# CORS Configuration - CRITICAL for WebSocket
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from app.routers.ws import router as ws_router

# Include WebSocket router FIRST
app.include_router(ws_router)

@app.get("/")
def health():
    return {"status": "running", "message": "AI Interviewer API is operational"}

@app.post("/upload_resume")
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload resume and create interview session
    """
    try:
        print(f"Uploading resume: {file.filename}")
        
        # Read file content
        content = await file.read()
        
        # Parse resume
        resume_text = parse_resume(file.filename, content)
        print(f"Resume parsed successfully: {len(resume_text)} characters")
        job_description = infer_job_description(resume_text)
        # Generate session ID
        session_id = str(uuid4())
        print(f"Generated session ID: {session_id}")
        
        # Create session
        create_session(session_id,job_description, resume_text)
        print(f"Session created successfully")
        
        return {
            "session_id": session_id,
            "job description ": job_description,
            "status": "success",
            "message": "Resume uploaded successfully"
        }
        
    except Exception as e:
        print(f" Error uploading resume: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "status": "failed"
        }

@app.get("/session/{session_id}")
def check_session(session_id: str):
    """
    Check if session exists (for debugging)
    """
    from app.services.interview_state import get_session
    session = get_session(session_id)
    
    if session:
        return {
            "exists": True,
            "session_id": session_id,
            "questions_count": len(session.questions),
            "completed": session.completed
        }
    else:
        return {
            "exists": False,
            "session_id": session_id
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)