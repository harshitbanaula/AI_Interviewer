# import time
# import json
# import asyncio

# from fastapi import APIRouter, WebSocket, Query, WebSocketDisconnect

# from sqlalchemy.orm import Session
# from app.database import SessionLocal
# from app.services.stt import transcribe_chunk
# from app.services.interview_state import get_session, delete_session, _save_session
# from app.services.tts import synthesize_speech
# from app.services.audio_storage import save_candidate_audio
# from app.services.evaluator import score_answer
# from app.repository import db_start_session, db_save_answer, db_complete_session
# from app.core.thread_pool import run_in_thread

# router = APIRouter()


# # Minimum PCM bytes before we bother running Whisper.
# # 16 kHz × 16-bit = 32 000 bytes/s  →  3 200 bytes ≈ 0.1 s of audio.
# # Anything shorter is noise / an accidental click and we treat it as skip.
# _MIN_AUDIO_BYTES = 3_200


# async def run_blocking(func, *args):
#     return await run_in_thread(func, *args)

# def get_db_session() -> Session:
#     return SessionLocal()


# # ─── WebSocket handler  

# @router.websocket("/ws/interview")
# async def interview_ws(ws: WebSocket, session_id: str = Query(...)):
#     await ws.accept()

#     session = get_session(session_id)
#     if not session:
#         await ws.send_json({
#             "type": "ERROR",
#             "text": "Invalid or expired session. Please start a new interview.",
#         })
#         await ws.close()
#         return

#     # ── Detect reconnect  
#     is_reconnect = (
#         len(session.questions) > 0
#         and session.session_start_time is not None
#         and not session.is_finalized
#         and not session.completed
#     )

#     # ── Per-connection state  
#     socket_open         = True
#     end_sent            = False
#     buffer_warning_sent = False
#     audio_buffer        = bytearray()
#     accepting_audio     = False
#     is_processing       = False

#     db = get_db_session()

#     # ─── SAFE SEND HELPERS  

#     async def safe_send_json(payload: dict):
#         nonlocal socket_open
#         if not socket_open:
#             return
#         try:
#             await ws.send_json(payload)
#         except Exception as e:
#             print(f"[WS {session_id}] send_json failed: {e}")
#             socket_open = False

#     async def safe_send_bytes(data: bytes):
#         nonlocal socket_open
#         if not socket_open:
#             return
#         try:
#             await ws.send_bytes(data)
#         except Exception as e:
#             print(f"[WS {session_id}] send_bytes failed: {e}")
#             socket_open = False

#     # ─── KEEPALIVE WRAPPER  
#     # Accepts coroutine, Task, or Future.

#     async def with_keepalive(task_or_coro, interval: float = 2.0):
#         if asyncio.iscoroutine(task_or_coro):
#             task = asyncio.create_task(task_or_coro)
#         else:
#             task = task_or_coro   # Future or Task — use directly

#         while not task.done():
#             try:
#                 await asyncio.wait_for(asyncio.shield(task), timeout=interval)
#             except asyncio.TimeoutError:
#                 if socket_open:
#                     await safe_send_json({"type": "KEEPALIVE"})

#         return task.result()

#     # ─── TTS SYNTHESIS  

#     async def synthesize_with_keepalive(text: str) -> bytes | None:
#         task = asyncio.create_task(run_blocking(synthesize_speech, text, 0, 0.85))
#         try:
#             return await with_keepalive(task)
#         except Exception as e:
#             print(f"[WS {session_id}] TTS failed: {e}")
#             return None

#     # ─── SEND QUESTION  

#     async def send_question(q: str):
#         nonlocal accepting_audio, is_processing

#         if session.completed or not socket_open:
#             return

#         # Timer snapshot
#         if session.session_start_time:
#             elapsed   = time.time() - session.session_start_time
#             in_buf    = elapsed >= session.SESSION_LIMIT_SECONDS
#             total_lim = session.SESSION_LIMIT_SECONDS + session.GRACE_PERIOD_SECONDS
#             remaining = max(
#                 int(total_lim - elapsed if in_buf else session.SESSION_LIMIT_SECONDS - elapsed),
#                 0,
#             )
#             await safe_send_json({
#                 "type":              "TIMER_UPDATE",
#                 "remaining_seconds": remaining,
#                 "in_buffer_time":    in_buf,
#             })

#         # Text first — candidate reads while audio loads
#         await safe_send_json({"type": "QUESTION", "text": q})
#         if not socket_open:
#             return

#         # Audio with keepalive
#         audio = await synthesize_with_keepalive(q)
#         if audio and socket_open:
#             await safe_send_json({"type": "TTS_START"})
#             await safe_send_bytes(audio)
#             await safe_send_json({"type": "TTS_END"})

#         # Open PCM gate after TTS completes
#         accepting_audio = True
#         is_processing   = False

#     # ─── CLEAN END SEQUENCE  

#     async def send_end_and_close():
#         nonlocal end_sent, socket_open

#         if end_sent:
#             return

#         print(f"[WS {session_id}] Finalizing interview…")

#         if not session.is_finalized:
#             try:
#                 finalize_task = asyncio.create_task(run_blocking(session.finalize, True))
#                 await with_keepalive(finalize_task)
#             except Exception as e:
#                 print(f"[WS {session_id}] Finalize error: {e}")
#             _save_session(session_id, session)

#         summary = session.final_result()

#         try:
#             db_complete_session(db, session_id, summary)
#         except Exception as e:
#             print(f"[DB ERROR] complete_session: {e}")

#         await safe_send_json({"type": "END", "summary": summary})
#         print(f"[WS {session_id}] END sent")

#         end_sent    = True
#         socket_open = False

#         await asyncio.sleep(0.3)
#         try:
#             await ws.close()
#         except Exception:
#             pass

#         delete_session(session_id)
#         print(f"[WS {session_id}] Session cleaned up")

#     # ─── DB ANSWER SAVE (runs in thread pool)  

#     def _save_answer_to_db(question_index, answer_text, audio_path, is_skipped):
#         try:
#             score         = session.scores[-1] if session.scores else {}
#             question_text = (
#                 session.questions[question_index - 1]
#                 if question_index <= len(session.questions) else ""
#             )
#             duration = session.answer_durations[-1] if session.answer_durations else 0.0

#             db_save_answer(
#                 db=db,
#                 session_id=session_id,
#                 question_index=question_index,
#                 question_text=question_text,
#                 answer_text=answer_text,
#                 score=score,
#                 duration_seconds=duration,
#                 audio_file_path=audio_path or "",
#                 stage=session.stage,
#                 project_mentioned=session.current_topic,
#                 is_skipped=is_skipped,
#             )
#         except Exception as e:
#             print(f"[DB ERROR] save_answer Q{question_index}: {e}")

#     # ─── TIME MONITOR  

#     async def monitor_time_limit():
#         nonlocal buffer_warning_sent

#         while socket_open and not session.is_finalized:
#             await asyncio.sleep(1)

#             if not session.session_start_time:
#                 continue

#             elapsed   = time.time() - session.session_start_time
#             in_buf    = elapsed >= session.SESSION_LIMIT_SECONDS
#             total_lim = session.SESSION_LIMIT_SECONDS + session.GRACE_PERIOD_SECONDS
#             remaining = max(
#                 int(total_lim - elapsed if in_buf else session.SESSION_LIMIT_SECONDS - elapsed),
#                 0,
#             )

#             await safe_send_json({
#                 "type":              "TIMER_UPDATE",
#                 "remaining_seconds": remaining,
#                 "in_buffer_time":    in_buf,
#             })

#             if in_buf and not buffer_warning_sent:
#                 buffer_warning_sent = True
#                 await safe_send_json({
#                     "type":    "BUFFER_TIME_WARNING",
#                     "message": "⚠️ Main time expired! 2 minutes buffer remaining.",
#                 })

#             if elapsed >= total_lim:
#                 print(f"[WS {session_id}] Buffer time expired, ending")
#                 await send_end_and_close()
#                 break

#     # ─── STT + AUDIO-SAVE (keepalive-wrapped)  

#     async def transcribe_and_save(
#         audio_bytes_snapshot: bytes, current_q_idx: int
#     ) -> tuple[str | None, str]:
#         if len(audio_bytes_snapshot) < _MIN_AUDIO_BYTES:
#             print(
#                 f"[WS {session_id}] Audio too short "
#                 f"({len(audio_bytes_snapshot)} bytes < {_MIN_AUDIO_BYTES}), skipping STT"
#             )
#             return None, ""

#         try:
#             gather_future = asyncio.gather(
#                 run_blocking(save_candidate_audio, session_id, current_q_idx, audio_bytes_snapshot),
#                 run_blocking(transcribe_chunk, audio_bytes_snapshot),
#             )
#             audio_path, answer_text = await with_keepalive(gather_future)
#             return audio_path, answer_text
#         except Exception as e:
#             print(f"[WS {session_id}] STT/save failed: {e}")
#             return None, ""

#     # ─── PROCESS ANSWER → NEXT QUESTION  

#     async def process_answer_and_get_next(
#         answer_text: str,
#         current_q_idx: int,
#         audio_path: str | None,
#         is_skipped: bool,
#     ):
#         nonlocal is_processing

#         is_processing = True

#         # Acknowledge receipt immediately
#         if socket_open:
#             await safe_send_json({
#                 "type": "FINAL_TRANSCRIPT",
#                 "text": "Question skipped" if is_skipped else answer_text,
#             })

#         # Score with keepalive
#         try:
#             score_task = asyncio.create_task(
#                 run_blocking(score_answer, answer_text, session.questions[-1])
#             )
#             score = await with_keepalive(score_task)
#             print(f"[PERF] Score: {score['final_score']:.2f}")
#         except Exception as e:
#             print(f"[WS {session_id}] Scoring failed, using fallback: {e}")
#             score = {
#                 "relevance": 0.5, "technical_accuracy": 0.5,
#                 "completeness": 0.5, "clarity": 0.5,
#                 "final_score": 0.5, "strengths": [],
#                 "improvements": ["Automatic evaluation failed — manual review needed."],
#                 "is_non_answer": False,
#             }

#         # Write into session (lock-protected)
#         with session._state_lock:
#             if not session.is_finalized and session.expecting_answer:
#                 duration = (
#                     round(time.time() - session.current_question_start, 2)
#                     if session.current_question_start else 0.0
#                 )
#                 session.answer_durations.append(duration)
#                 session.current_question_start = None
#                 session.answers.append(answer_text)
#                 session.scores.append(score)
#                 classification = session._classify_answer(score["final_score"])
#                 session.stage  = session._decide_next_stage(
#                     session.current_topic, classification
#                 )
#                 session.expecting_answer = False

#         _save_session(session_id, session)

#         # DB save in background
#         asyncio.create_task(
#             run_blocking(
#                 _save_answer_to_db, current_q_idx, answer_text, audio_path, is_skipped
#             )
#         )

#         # End check
#         if session.is_finalized or session._question_limit_reached():
#             await send_end_and_close()
#             return

#         # Generate next question with keepalive
#         print(f"[PERF] Generating next question…")
#         t0 = time.time()
#         try:
#             question_task = asyncio.create_task(run_blocking(session.next_question))
#             next_q = await with_keepalive(question_task)
#         except Exception as e:
#             print(f"[WS {session_id}] Question generation failed: {e}")
#             next_q = None

#         _save_session(session_id, session)
#         print(f"[PERF] Question in {time.time() - t0:.2f}s")

#         if not next_q:
#             await send_end_and_close()
#             return

#         await send_question(next_q)

#     # ─── START: RECONNECT PATH

#     time_monitor_task = None

#     if is_reconnect:
#         print(
#             f"[WS {session_id}] RECONNECT — "
#             f"Q={len(session.questions)}, A={len(session.answers)}"
#         )

#         elapsed   = time.time() - session.session_start_time
#         in_buf    = elapsed >= session.SESSION_LIMIT_SECONDS
#         total_lim = session.SESSION_LIMIT_SECONDS + session.GRACE_PERIOD_SECONDS
#         remaining = max(
#             int(total_lim - elapsed if in_buf else session.SESSION_LIMIT_SECONDS - elapsed),
#             0,
#         )

#         if elapsed >= total_lim:
#             print(f"[WS {session_id}] Time expired during disconnect, finalizing")
#             await send_end_and_close()
#             db.close()
#             return

#         await safe_send_json({
#             "type":               "RESUMED",
#             "questions_answered": len(session.answers),
#             "questions_asked":    len(session.questions),
#             "remaining_seconds":  remaining,
#             "in_buffer_time":     in_buf,
#             "is_processing":      session.is_finalized or not session.expecting_answer,
#         })

#         time_monitor_task = asyncio.create_task(monitor_time_limit())

#         if session.expecting_answer and len(session.questions) > len(session.answers):
#             current_q = session.questions[-1]
#             print(f"[WS {session_id}] Replaying: {current_q[:60]}…")
#             await send_question(current_q)

#         elif not session.expecting_answer:
#             print(f"[WS {session_id}] Between questions — generating next")
#             try:
#                 question_task = asyncio.create_task(run_blocking(session.next_question))
#                 next_q = await with_keepalive(question_task)
#             except Exception as e:
#                 print(f"[WS {session_id}] Question gen on reconnect failed: {e}")
#                 next_q = None

#             _save_session(session_id, session)

#             if next_q:
#                 await send_question(next_q)
#             else:
#                 await send_end_and_close()
#                 db.close()
#                 return
#         else:
#             print(f"[WS {session_id}] Unexpected state on reconnect, ending")
#             await send_end_and_close()
#             db.close()
#             return

#     # ─── START: FRESH PATH  

#     else:
#         print(f"[WS {session_id}] Fresh connection")
#         time_monitor_task = asyncio.create_task(monitor_time_limit())

#         try:
#             first_q = await with_keepalive(
#                 asyncio.create_task(run_blocking(session.next_question))
#             )
#         except Exception as e:
#             print(f"[WS {session_id}] First question generation failed: {e}")
#             first_q = None

#         _save_session(session_id, session)

#         if not first_q:
#             await send_end_and_close()
#             time_monitor_task.cancel()
#             db.close()
#             return

#         session.session_start_time = time.time()
#         _save_session(session_id, session)

#         try:
#             db_start_session(db, session_id)
#         except Exception as e:
#             print(f"[DB ERROR] start_session: {e}")

#         print(f"[WS {session_id}] ⏱ Timer started, sending first question")
#         await send_question(first_q)

#     # ─── MAIN RECEIVE LOOP

#     try:
#         while socket_open:
#             msg = await ws.receive()

#             # exit cleanly on disconnect message  
#             if msg.get("type") == "websocket.disconnect":
#                 print(f"[WS {session_id}] Disconnect message received, exiting loop")
#                 socket_open = False
#                 break

#             if session.is_finalized:
#                 continue

#             # ── Binary: PCM audio  
#             if msg.get("bytes"):
#                 if accepting_audio and session.expecting_answer:
#                     audio_buffer.extend(msg["bytes"])
#                 continue

#             # ── Text: JSON action  
#             if not msg.get("text"):
#                 continue

#             try:
#                 payload = json.loads(msg["text"])
#             except json.JSONDecodeError:
#                 continue

#             action = payload.get("action")

#             if action == "PING":
#                 continue

#             elif action == "SUBMIT_ANSWER":
#                 if not session.expecting_answer or is_processing:
#                     print(
#                         f"[WS {session_id}] Ignored duplicate SUBMIT_ANSWER "
#                         f"(expecting={session.expecting_answer}, processing={is_processing})"
#                     )
#                     continue

#                 accepting_audio      = False
#                 audio_bytes_snapshot = bytes(audio_buffer)
#                 audio_buffer.clear()

#                 current_q_idx = len(session.answers) + 1

#                 if audio_bytes_snapshot:
#                     audio_path, answer_text = await transcribe_and_save(
#                         audio_bytes_snapshot, current_q_idx
#                     )
#                 else:
#                     audio_path  = None
#                     answer_text = payload.get("text", "").strip()

#                 if not answer_text or not answer_text.strip():
#                     answer_text = "No answer provided"

#                 print(
#                     f"[WS {session_id}] Answer ({len(answer_text.split())} words): "
#                     f"{answer_text[:60]}…"
#                 )

#                 await process_answer_and_get_next(
#                     answer_text, current_q_idx, audio_path, is_skipped=False
#                 )

#             elif action == "SKIP_QUESTION":
#                 if not session.expecting_answer or is_processing:
#                     print(f"[WS {session_id}] Ignored duplicate SKIP_QUESTION")
#                     continue

#                 accepting_audio = False
#                 audio_buffer.clear()
#                 current_q_idx = len(session.answers) + 1

#                 print(f"[WS {session_id}] Q{current_q_idx} skipped")

#                 await process_answer_and_get_next(
#                     "Question skipped by candidate",
#                     current_q_idx,
#                     None,
#                     is_skipped=True,
#                 )

#     except WebSocketDisconnect:
#         print(f"[WS {session_id}] Client disconnected (WebSocketDisconnect)")
#         socket_open = False

#     except RuntimeError as e:
#         if "disconnect" in str(e).lower() or "receive" in str(e).lower():
#             print(f"[WS {session_id}] Client disconnected (RuntimeError: {e})")
#         else:
#             print(f"[WS {session_id}] Unexpected RuntimeError: {e}")
#             import traceback
#             traceback.print_exc()
#         socket_open = False

#     except Exception as e:
#         print(f"[WS {session_id}] Unexpected error: {e}")
#         import traceback
#         traceback.print_exc()
#         socket_open = False

#     # ─── FINALLY: cleanup 

#     finally:
#         if time_monitor_task:
#             time_monitor_task.cancel()
#             try:
#                 await time_monitor_task
#             except BaseException:
#                 pass

#         db.close()

#         if end_sent:
#             return

#         try:
#             if not session.is_finalized:
#                 _save_session(session_id, session)
#                 print(
#                     f"[WS {session_id}] State preserved in Redis "
#                     f"(Q={len(session.questions)}, A={len(session.answers)})"
#                 )

#                 async def _delayed_save():
#                     await asyncio.sleep(15)
#                     try:
#                         from app.services.interview_state import get_session as _check_session
#                         still_exists = _check_session(session_id)
#                         if still_exists and not session.is_finalized:
#                             _save_session(session_id, session)
#                             print(f"[WS {session_id}] Delayed Redis save completed")
#                         else:
#                             print(f"[WS {session_id}] Delayed save skipped — session already finalized or deleted")
#                     except Exception as ex:
#                         print(f"[WS {session_id}] Delayed save failed: {ex}")

#                 asyncio.create_task(_delayed_save())

#             else:
#                 # Session was finalized during this connection — write to DB
#                 fresh_db = SessionLocal()
#                 try:
#                     summary = session.final_result()
#                     db_complete_session(fresh_db, session_id, summary)
#                     print(f"[WS {session_id}] Finalized session written to DB on disconnect")
#                 except Exception as e:
#                     print(f"[WS {session_id}] DB complete on disconnect failed: {e}")
#                 finally:
#                     fresh_db.close()   # FIX: was never closed in original code

#         except Exception as e:
#             print(f"[WS {session_id}] Error in disconnect handler: {e}")



import time
import json
import asyncio

from fastapi import APIRouter, WebSocket, Query, WebSocketDisconnect

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.stt import transcribe_chunk
from app.services.interview_state import get_session, delete_session, _save_session
from app.services.tts import synthesize_speech
from app.services.audio_storage import save_candidate_audio
from app.services.evaluator import score_answer
from app.repository import db_start_session, db_save_answer, db_complete_session
from app.core.thread_pool import run_in_thread
from app.core.rate_limiter import check_ws_rate_limit
from app.services.session_auth import verify_session_token, delete_session_token
from app.services.interview_state import get_session as _check_session
router = APIRouter()


# Minimum PCM bytes before we bother running Whisper.
# 16 kHz × 16-bit = 32 000 bytes/s  →  3 200 bytes ≈ 0.1 s of audio.
# Anything shorter is noise / an accidental click and we treat it as skip.
_MIN_AUDIO_BYTES = 3_200


async def run_blocking(func, *args):
    return await run_in_thread(func, *args)

def get_db_session() -> Session:
    return SessionLocal()


# ─── WebSocket handler

@router.websocket("/ws/interview")
async def interview_ws(
    ws:         WebSocket,
    session_id: str = Query(...),
    token:      str = Query(...),
):
    # ── Rate limit: 10 WS connections per minute per IP ────────
    if not check_ws_rate_limit(ws, "ws_interview", max_requests=10, window_seconds=60):
        await ws.accept()
        await ws.send_json({
            "type": "ERROR",
            "text": "Too many connection attempts. Please wait a few minutes before trying again.",
        })
        await ws.close(code=1008)
        return

    await ws.accept()

    # ── Token verification
    if not verify_session_token(session_id, token):
        await ws.send_json({
            "type": "ERROR",
            "text": "Unauthorised. Your session token is invalid or has expired.",
        })
        await ws.close()
        print(f"[AUTH] Rejected WS for session {session_id[:8]}... — bad token")
        return

    session = get_session(session_id)
    if not session:
        await ws.send_json({
            "type": "ERROR",
            "text": "Invalid or expired session. Please start a new interview.",
        })
        await ws.close()
        return

    # ── Detect reconnect  
    is_reconnect = (
        len(session.questions) > 0
        and session.session_start_time is not None
        and not session.is_finalized
        and not session.completed
    )

    # ── Per-connection state  
    socket_open         = True
    end_sent            = False
    buffer_warning_sent = False
    audio_buffer        = bytearray()
    accepting_audio     = False
    is_processing       = False

    db = get_db_session()

    # ─── SAFE SEND HELPERS  

    async def safe_send_json(payload: dict):
        nonlocal socket_open
        if not socket_open:
            return
        try:
            await ws.send_json(payload)
        except Exception as e:
            print(f"[WS {session_id}] send_json failed: {e}")
            socket_open = False

    async def safe_send_bytes(data: bytes):
        nonlocal socket_open
        if not socket_open:
            return
        try:
            await ws.send_bytes(data)
        except Exception as e:
            print(f"[WS {session_id}] send_bytes failed: {e}")
            socket_open = False

    # ─── KEEPALIVE WRAPPER 
    # Accepts coroutine, Task, or Future.

    async def with_keepalive(task_or_coro, interval: float = 2.0):
        if asyncio.iscoroutine(task_or_coro):
            task = asyncio.create_task(task_or_coro)
        else:
            task = task_or_coro   # Future or Task — use directly

        while not task.done():
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=interval)
            except asyncio.TimeoutError:
                if socket_open:
                    await safe_send_json({"type": "KEEPALIVE"})

        return task.result()

    # ─── TTS SYNTHESIS 

    async def synthesize_with_keepalive(text: str) -> bytes | None:
        task = asyncio.create_task(run_blocking(synthesize_speech, text, 0, 0.85))
        try:
            return await with_keepalive(task)
        except Exception as e:
            print(f"[WS {session_id}] TTS failed: {e}")
            return None

    # ─── SEND QUESTION 

    async def send_question(q: str):
        nonlocal accepting_audio, is_processing

        if session.completed or not socket_open:
            return

        # Timer snapshot
        if session.session_start_time:
            elapsed   = time.time() - session.session_start_time
            in_buf    = elapsed >= session.SESSION_LIMIT_SECONDS
            total_lim = session.SESSION_LIMIT_SECONDS + session.GRACE_PERIOD_SECONDS
            remaining = max(
                int(total_lim - elapsed if in_buf else session.SESSION_LIMIT_SECONDS - elapsed),
                0,
            )
            await safe_send_json({
                "type":              "TIMER_UPDATE",
                "remaining_seconds": remaining,
                "in_buffer_time":    in_buf,
            })

        # Text first — candidate reads while audio loads
        await safe_send_json({"type": "QUESTION", "text": q})
        if not socket_open:
            return

        # Audio with keepalive
        audio = await synthesize_with_keepalive(q)
        if audio and socket_open:
            await safe_send_json({"type": "TTS_START"})
            await safe_send_bytes(audio)
            await safe_send_json({"type": "TTS_END"})

        # Open PCM gate after TTS completes
        accepting_audio = True
        is_processing   = False

    # ─── CLEAN END SEQUENCE 

    async def send_end_and_close():
        nonlocal end_sent, socket_open

        if end_sent:
            return

        print(f"[WS {session_id}] Finalizing interview…")

        if not session.is_finalized:
            try:
                finalize_task = asyncio.create_task(run_blocking(session.finalize, True))
                await with_keepalive(finalize_task)
            except Exception as e:
                print(f"[WS {session_id}] Finalize error: {e}")
            _save_session(session_id, session)

        summary = session.final_result()

        try:
            db_complete_session(db, session_id, summary)
        except Exception as e:
            print(f"[DB ERROR] complete_session: {e}")

        await safe_send_json({"type": "END", "summary": summary})
        print(f"[WS {session_id}] END sent")

        end_sent    = True
        socket_open = False

        await asyncio.sleep(0.3)
        try:
            await ws.close()
        except Exception:
            pass

        delete_session(session_id)
        delete_session_token(session_id)
        print(f"[WS {session_id}] Session cleaned up")

    # ─── DB ANSWER SAVE (runs in thread pool) 

    def _save_answer_to_db(question_index, answer_text, audio_path, is_skipped):
        fresh_db = SessionLocal()
        try:
            score = session.scores[-1] if session.scores else {}
            question_text = (
                session.questions[question_index - 1]
                if question_index <= len(session.questions) else ""
            )
            duration = session.answer_durations[-1] if session.answer_durations else 0.0

            db_save_answer(
                db=fresh_db,
                session_id=session_id,
                question_index=question_index,
                question_text=question_text,
                answer_text=answer_text,
                score=score,
                duration_seconds=duration,
                audio_file_path=audio_path or "",
                stage=session.stage,
                project_mentioned=session.current_topic,
                is_skipped=is_skipped,
            )
        except Exception as e:
            print(f"[DB ERROR] save_answer Q{question_index}: {e}")
        finally:
            fresh_db.close()

    # ─── TIME MONITOR 

    async def monitor_time_limit():
        nonlocal buffer_warning_sent

        while socket_open and not session.is_finalized:
            await asyncio.sleep(1)

            if not session.session_start_time:
                continue

            elapsed   = time.time() - session.session_start_time
            in_buf    = elapsed >= session.SESSION_LIMIT_SECONDS
            total_lim = session.SESSION_LIMIT_SECONDS + session.GRACE_PERIOD_SECONDS
            remaining = max(
                int(total_lim - elapsed if in_buf else session.SESSION_LIMIT_SECONDS - elapsed),
                0,
            )

            await safe_send_json({
                "type":              "TIMER_UPDATE",
                "remaining_seconds": remaining,
                "in_buffer_time":    in_buf,
            })

            if in_buf and not buffer_warning_sent:
                buffer_warning_sent = True
                await safe_send_json({
                    "type":    "BUFFER_TIME_WARNING",
                    "message": "⚠️ Main time expired! 2 minutes buffer remaining.",
                })

            if elapsed >= total_lim:
                print(f"[WS {session_id}] Buffer time expired, ending")
                await send_end_and_close()
                break

    # ─── STT + AUDIO-SAVE (keepalive-wrapped) 

    async def transcribe_and_save(
        audio_bytes_snapshot: bytes, current_q_idx: int
    ) -> tuple[str | None, str]:
        if len(audio_bytes_snapshot) < _MIN_AUDIO_BYTES:
            print(
                f"[WS {session_id}] Audio too short "
                f"({len(audio_bytes_snapshot)} bytes < {_MIN_AUDIO_BYTES}), skipping STT"
            )
            return None, ""

        try:
            gather_future = asyncio.gather(
                run_blocking(save_candidate_audio, session_id, current_q_idx, audio_bytes_snapshot),
                run_blocking(transcribe_chunk, audio_bytes_snapshot),
            )
            audio_path, answer_text = await with_keepalive(gather_future)
            return audio_path, answer_text
        except Exception as e:
            print(f"[WS {session_id}] STT/save failed: {e}")
            return None, ""

    # ─── PROCESS ANSWER → NEXT QUESTION 

    async def process_answer_and_get_next(
        answer_text: str,
        current_q_idx: int,
        audio_path: str | None,
        is_skipped: bool,
    ):
        nonlocal is_processing

        is_processing = True

        try:

            # Acknowledge receipt immediately
            if socket_open:
                await safe_send_json({
                    "type": "FINAL_TRANSCRIPT",
                    "text": "Question skipped" if is_skipped else answer_text,
                })

            # Score with keepalive
            try:
                score_task = asyncio.create_task(
                    run_blocking(score_answer, answer_text, session.questions[-1])
                )
                score = await with_keepalive(score_task)
                print(f"[PERF] Score: {score['final_score']:.2f}")
            except Exception as e:
                print(f"[WS {session_id}] Scoring failed, using fallback: {e}")
                score = {
                    "relevance": 0.5, "technical_accuracy": 0.5,
                    "completeness": 0.5, "clarity": 0.5,
                    "final_score": 0.5, "strengths": [],
                    "improvements": ["Automatic evaluation failed — manual review needed."],
                    "is_non_answer": False,
                }

            # Write into session (lock-protected)
            with session._state_lock:
                if not session.is_finalized and session.expecting_answer:
                    duration = (
                        round(time.time() - session.current_question_start, 2)
                        if session.current_question_start else 0.0
                    )
                    session.answer_durations.append(duration)
                    session.current_question_start = None
                    session.answers.append(answer_text)
                    session.scores.append(score)
                    classification = session._classify_answer(score["final_score"])
                    session.stage  = session._decide_next_stage(
                        session.current_topic, classification
                    )
                    session.expecting_answer = False
            if get_session(session_id) is not None:
                _save_session(session_id, session)

            # DB save in background
            asyncio.create_task(
                run_blocking(
                    _save_answer_to_db, current_q_idx, answer_text, audio_path, is_skipped
                )
            )

            # End check
            if session.is_finalized or session._question_limit_reached():
                await send_end_and_close()
                return

            # Generate next question with keepalive
            print(f"[PERF] Generating next question…")
            t0 = time.time()
            try:
                question_task = asyncio.create_task(run_blocking(session.next_question))
                next_q = await with_keepalive(question_task)
            except Exception as e:
                print(f"[WS {session_id}] Question generation failed: {e}")
                next_q = None

            if get_session(session_id) is not None:
                _save_session(session_id, session)

            print(f"[PERF] Question in {time.time() - t0:.2f}s")

            if not next_q:
                await send_end_and_close()
                return

            await send_question(next_q)

        finally:
            is_processing = False
        

    # ─── START: RECONNECT PATH 

    time_monitor_task = None

    if is_reconnect:
        print(
            f"[WS {session_id}] RECONNECT — "
            f"Q={len(session.questions)}, A={len(session.answers)}"
        )

        elapsed   = time.time() - session.session_start_time
        in_buf    = elapsed >= session.SESSION_LIMIT_SECONDS
        total_lim = session.SESSION_LIMIT_SECONDS + session.GRACE_PERIOD_SECONDS
        remaining = max(
            int(total_lim - elapsed if in_buf else session.SESSION_LIMIT_SECONDS - elapsed),
            0,
        )

        if elapsed >= total_lim:
            print(f"[WS {session_id}] Time expired during disconnect, finalizing")
            await send_end_and_close()
            db.close()
            return

        await safe_send_json({
            "type":               "RESUMED",
            "questions_answered": len(session.answers),
            "questions_asked":    len(session.questions),
            "remaining_seconds":  remaining,
            "in_buffer_time":     in_buf,
            "is_processing":      session.is_finalized or not session.expecting_answer,
        })

        time_monitor_task = asyncio.create_task(monitor_time_limit())

        if session.expecting_answer and len(session.questions) > len(session.answers):
            current_q = session.questions[-1]
            print(f"[WS {session_id}] Replaying: {current_q[:60]}…")
            await send_question(current_q)

        elif not session.expecting_answer:
            print(f"[WS {session_id}] Between questions — generating next")
            try:
                question_task = asyncio.create_task(run_blocking(session.next_question))
                next_q = await with_keepalive(question_task)
            except Exception as e:
                print(f"[WS {session_id}] Question gen on reconnect failed: {e}")
                next_q = None

            _save_session(session_id, session)

            if next_q:
                await send_question(next_q)
            else:
                await send_end_and_close()
                db.close()
                return
        else:
            print(f"[WS {session_id}] Unexpected state on reconnect, ending")
            await send_end_and_close()
            db.close()
            return

    # ─── START: FRESH PATH 

    else:
        print(f"[WS {session_id}] Fresh connection")
        time_monitor_task = asyncio.create_task(monitor_time_limit())

        try:
            first_q = await with_keepalive(
                asyncio.create_task(run_blocking(session.next_question))
            )
        except Exception as e:
            print(f"[WS {session_id}] First question generation failed: {e}")
            first_q = None

        _save_session(session_id, session)

        if not first_q:
            await send_end_and_close()
            time_monitor_task.cancel()
            db.close()
            return

        session.session_start_time = time.time()
        _save_session(session_id, session)

        try:
            db_start_session(db, session_id)
        except Exception as e:
            print(f"[DB ERROR] start_session: {e}")

        print(f"[WS {session_id}] ⏱ Timer started, sending first question")
        await send_question(first_q)

    # ─── MAIN RECEIVE LOOP

    try:
        while socket_open:
            msg = await ws.receive()

            # ── FIX: exit cleanly on disconnect message 
            if msg.get("type") == "websocket.disconnect":
                print(f"[WS {session_id}] Disconnect message received, exiting loop")
                socket_open = False
                break

            if session.is_finalized:
                continue

            # ── Binary: PCM audio 
            if msg.get("bytes"):
                if accepting_audio and session.expecting_answer:
                    audio_buffer.extend(msg["bytes"])
                continue

            # ── Text: JSON action 
            if not msg.get("text"):
                continue

            try:
                payload = json.loads(msg["text"])
            except json.JSONDecodeError:
                continue

            action = payload.get("action")

            if action == "PING":
                continue

            # Guard: reject all actions if session deleted from redis

            if not _check_session(session_id):
                print(f"[WS {session_id}] Session no longer exists in Redis — closing")
                await safe_send_json({
                    "Type" : "ERROR",
                    "text" : "This interview has already been submitted and cannot be continued. "
                })
                socket_open = False
                try:
                    await ws.close()
                except Exception:
                    pass
                break


            elif action == "SUBMIT_ANSWER":
                if not session.expecting_answer or is_processing:
                    print(
                        f"[WS {session_id}] Ignored duplicate SUBMIT_ANSWER "
                        f"(expecting={session.expecting_answer}, processing={is_processing})"
                    )
                    continue

                accepting_audio      = False
                audio_bytes_snapshot = bytes(audio_buffer)
                audio_buffer.clear()

                current_q_idx = len(session.answers) + 1

                if audio_bytes_snapshot:
                    audio_path, answer_text = await transcribe_and_save(
                        audio_bytes_snapshot, current_q_idx
                    )
                else:
                    audio_path  = None
                    answer_text = payload.get("text", "").strip()

                if not answer_text or not answer_text.strip():
                    answer_text = "No answer provided"

                print(
                    f"[WS {session_id}] Answer ({len(answer_text.split())} words): "
                    f"{answer_text[:60]}…"
                )

                await process_answer_and_get_next(
                    answer_text, current_q_idx, audio_path, is_skipped=False
                )

            elif action == "SKIP_QUESTION":
                if not session.expecting_answer or is_processing:
                    print(f"[WS {session_id}] Ignored duplicate SKIP_QUESTION")
                    continue

                accepting_audio = False
                audio_buffer.clear()
                current_q_idx = len(session.answers) + 1

                print(f"[WS {session_id}] Q{current_q_idx} skipped")

                await process_answer_and_get_next(
                    "Question skipped by candidate",
                    current_q_idx,
                    None,
                    is_skipped=True,
                )

    except WebSocketDisconnect:
        print(f"[WS {session_id}] Client disconnected (WebSocketDisconnect)")
        socket_open = False

    except RuntimeError as e:
        if "disconnect" in str(e).lower() or "receive" in str(e).lower():
            print(f"[WS {session_id}] Client disconnected (RuntimeError: {e})")
        else:
            print(f"[WS {session_id}] Unexpected RuntimeError: {e}")
            import traceback
            traceback.print_exc()
        socket_open = False

    except Exception as e:
        print(f"[WS {session_id}] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        socket_open = False

    # ─── FINALLY: cleanup 

    finally:
        if time_monitor_task:
            time_monitor_task.cancel()
            try:
                await time_monitor_task
            except BaseException:
                pass

        db.close()

        if end_sent:
            return

        try:
            if not session.is_finalized and get_session(session_id) is not None:
                _save_session(session_id, session)
                print(
                    f"[WS {session_id}] State preserved in Redis "
                    f"(Q={len(session.questions)}, A={len(session.answers)})"
                )

                async def _delayed_save():
                    await asyncio.sleep(15)
                    try:
                        from app.services.interview_state import get_session as _check_session
                        still_exists = _check_session(session_id)
                        if still_exists and not session.is_finalized:
                            _save_session(session_id, session)
                            print(f"[WS {session_id}] Delayed Redis save completed")
                        else:
                            print(f"[WS {session_id}] Delayed save skipped — session already finalized or deleted")
                    except Exception as ex:
                        print(f"[WS {session_id}] Delayed save failed: {ex}")

                asyncio.create_task(_delayed_save())

            else:
                # Session was finalized during this connection — write to DB
                fresh_db = SessionLocal()
                try:
                    summary = session.final_result()
                    db_complete_session(fresh_db, session_id, summary)
                    print(f"[WS {session_id}] Finalized session written to DB on disconnect")
                except Exception as e:
                    print(f"[WS {session_id}] DB complete on disconnect failed: {e}")
                finally:
                    fresh_db.close()

        except Exception as e:
            print(f"[WS {session_id}] Error in disconnect handler: {e}")