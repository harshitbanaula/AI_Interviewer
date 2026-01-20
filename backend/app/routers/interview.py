from fastapi import APIRouter

router = APIRouter(prefix="/interview")

@router.post("/start")
async def start_interview():
    return {
        "message": "Interview session created",
        "first_question": "Tell me about yourself"
    }
