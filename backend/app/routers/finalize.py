from fastapi import APIRouter,HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.interview_state import get_session, delete_session, _save_session
from app.repository import db_complete_session
from app.database import SessionLocal
from app. services.session_auth import delete_session_token

router = APIRouter()

class FinalizeRequest(BaseModel):
    session_id: str
    completion_reason: Optional[str] = "manual_submit"


@router.post("/finalize_session")
async def finalize_session(body : FinalizeRequest):
    session_id = body.session_id
    completion_reason = body.completion_reason or "manual_submit"

    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or already expired. It may have been completed already")
    
    if session.is_finalized:
        summary = session.final_result()
        delete_session(session_id)
        return {"status":"already finished","summary":summary}
    
    if len(session.questions) == 0:
        raise HTTPException(status_code= 400, detail="No Questions were answered. Cannot finalize an empty session.")
    

    try:
        session.finalize(False)
        _save_session(session_id,session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"finalization failed: {str(e)}")
    
    summary = session.final_result()

    summary["completion_reason"] = completion_reason

    # save to db
    db= SessionLocal()

    try:
        db_complete_session(db, session_id,summary)
    except Exception as e:
         print(f"[FINALIZE REST] DB save failed for {session_id}: {e}")

    finally:
        db.close()

 
    # clean up redis
    delete_session(session_id)
    delete_session_token(session_id)

    print(f"[FINALIZE REST] Session {session_id} finalized via REST — {summary.get('result', 'N/A')}")

    return {"status": "finalized", "summary": summary}

