import os
import redis
from fastapi import Request, HTTPException
from starlette.websockets import WebSocket

_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_r = redis.from_url(_REDIS_URL, decode_responses=True)


def _get_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _get_ws_ip(ws: WebSocket) -> str:
    forwarded = ws.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return ws.client.host if ws.client else "unknown"


def _check(key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
    try:
        count = _r.incr(key)
        if count == 1:
            _r.expire(key, window_seconds)
        return count <= limit, count
    except Exception as e:
        # Redis down — fail open so the app keeps running
        print(f"[RATE LIMITER] Redis error, failing open: {e}")
        return True, 0


class RateLimit:
    def __init__(self, route_name: str, max_requests: int, window_seconds: int):
        self.route_name     = route_name
        self.max_requests   = max_requests
        self.window_seconds = window_seconds

    async def __call__(self, request: Request):
        ip      = _get_ip(request)
        key     = f"rl:{self.route_name}:{ip}"
        allowed, count = _check(key, self.max_requests, self.window_seconds)

        if not allowed:
            minutes = self.window_seconds // 60
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Too many requests — limit is {self.max_requests} per "
                    f"{minutes} minute(s). Please wait before trying again."
                ),
            )
        print(f"[RATE LIMITER] {self.route_name} — {ip}: {count}/{self.max_requests}")


def check_ws_rate_limit(ws: WebSocket, route_name: str, max_requests: int, window_seconds: int) -> bool:
    ip      = _get_ws_ip(ws)
    key     = f"rl:{route_name}:{ip}"
    allowed, count = _check(key, max_requests, window_seconds)

    if not allowed:
        print(f"[RATE LIMITER] {route_name} BLOCKED — {ip}: {count}/{max_requests}")
        return False

    print(f"[RATE LIMITER] {route_name} — {ip}: {count}/{max_requests}")
    return True