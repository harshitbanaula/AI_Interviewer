import os
import uuid
import redis
from dotenv import load_dotenv

load_dotenv()

_REDIS_URL = os.getenv("REDIS_URL")
_TOKEN_TTL = 7_200
_KEY_PREFX = "ws_token:"

_r = redis.from_url(_REDIS_URL,decode_responses = True)

def create_session_token(session_id: str)-> str:
    token = str(uuid.uuid4())
    key = f"{_KEY_PREFX}{session_id}"
    _r.setex(key, _TOKEN_TTL, token)
    print(f"[AUTH] Token created for session {session_id[:8]}...")
    return token 

def verify_session_token(session_id: str, token: str)-> bool:
    if not token or not session_id:
        return False
    key = f"{_KEY_PREFX}{session_id}"
    stored = _r.get(key)
    if not stored:
        print(f"[AUTH] No token found for session{session_id[:8]}...(expired or invalid)")
        return False
    if stored != token:
        print(f"[AUTH] Token mismatch for session {session_id[:8]}...")
        return False
    return True

def delete_session_token(session_id: str)-> None:
    key = f"{_KEY_PREFX}{session_id}"
    _r.delete(key)
    print(f"[AUTH] Token deleted for session {session_id[:8]}...")
