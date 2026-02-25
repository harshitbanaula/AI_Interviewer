# backend/app/routers/ws.py

import time
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, WebSocket, Query, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.stt import transcribe_chunk
from app.services.interview_state import get_session, delete_session, _save_session
from app.services.tts import synthesize_speech
from app.services.audio_storage import save_candidate_audio
from app.services.evaluator import score_answer
from app.repository import db_start_session, db_save_answer, db_complete_session

router = APIRouter()

# Thread pool for ALL blocking operations (LLM, TTS, STT, DB)
_executor = ThreadPoolExecutor(max_workers=6, thread_name_prefix="ws_worker")


async def run_blocking(func, *args):
    """Run any blocking function in a thread without freezing the event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, func, *args)


def get_db_session() -> Session:
    return SessionLocal()


@router.websocket("/ws/interview")
async def interview_ws(ws: WebSocket, session_id: str = Query(...)):
    await ws.accept()

    session = get_session(session_id)
    if not session:
        await ws.send_json({"type": "ERROR", "text": "Invalid session"})
        await ws.close()
        return

    socket_open = True
    end_sent = False
    buffer_warning_sent = False
    audio_buffer = bytearray()
    db = get_db_session()

    # ─────────────────────────────────────────────────────────────────────────
    # SAFE SEND HELPERS
    # Always check socket_open before sending — the socket can close at any
    # point during the 9-10s TTS synthesis gap.
    # ─────────────────────────────────────────────────────────────────────────

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

    # ─────────────────────────────────────────────────────────────────────────
    # FIX 2: TTS WITH KEEPALIVE
    # Problem: TTS takes 9-10s. During this time, nothing is sent to the
    # frontend. The browser WebSocket times out and closes the connection.
    # Solution: Send a KEEPALIVE ping every 2s while TTS is processing.
    # The frontend ignores KEEPALIVE messages — they just reset the timeout.
    # ─────────────────────────────────────────────────────────────────────────

    async def synthesize_with_keepalive(text: str) -> bytes:
        """Run TTS in thread, ping frontend every 2s to prevent timeout."""
        tts_task = asyncio.create_task(run_blocking(synthesize_speech, text, 0, 0.85))

        while not tts_task.done():
            try:
                await asyncio.wait_for(asyncio.shield(tts_task), timeout=2.0)
            except asyncio.TimeoutError:
                # TTS still running — send keepalive so browser doesn't close
                if socket_open:
                    await safe_send_json({"type": "KEEPALIVE"})
                    print(f"[WS {session_id}] KEEPALIVE sent during TTS")

        try:
            return tts_task.result()
        except Exception as e:
            print(f"[WS {session_id}] TTS failed: {e}")
            return None

    async def send_question(q: str):
        """Send question text immediately, then stream TTS audio."""
        if session.completed or not socket_open:
            return

        # Timer update
        if session.session_start_time:
            elapsed = time.time() - session.session_start_time
            if elapsed < session.SESSION_LIMIT_SECONDS:
                remaining = int(session.SESSION_LIMIT_SECONDS - elapsed)
                in_buffer = False
            else:
                buffer_elapsed = elapsed - session.SESSION_LIMIT_SECONDS
                remaining = max(int(session.GRACE_PERIOD_SECONDS - buffer_elapsed), 0)
                in_buffer = True

            await safe_send_json({
                "type": "TIMER_UPDATE",
                "remaining_seconds": remaining,
                "in_buffer_time": in_buffer
            })

        # Send question TEXT immediately — don't wait for audio
        await safe_send_json({"type": "QUESTION", "text": q})

        # Now synthesize audio with keepalive pings
        if not socket_open:
            return

        audio = await synthesize_with_keepalive(q)

        if audio and socket_open:
            await safe_send_json({"type": "TTS_START"})
            await safe_send_bytes(audio)
            await safe_send_json({"type": "TTS_END"})

    # ─────────────────────────────────────────────────────────────────────────
    # END + CLOSE
    # ─────────────────────────────────────────────────────────────────────────

    async def send_end_and_close():
        nonlocal end_sent, socket_open
        if end_sent:
            return

        print(f"[WS {session_id}] Finalizing interview...")

        if not session.is_finalized:
            # Finalize (feedback generation) in thread with keepalive
            finalize_task = asyncio.create_task(
                run_blocking(session.finalize, True)
            )
            while not finalize_task.done():
                try:
                    await asyncio.wait_for(asyncio.shield(finalize_task), timeout=2.0)
                except asyncio.TimeoutError:
                    if socket_open:
                        await safe_send_json({"type": "KEEPALIVE"})

            _save_session(session_id, session)

        summary = session.final_result()

        try:
            db_complete_session(db, session_id, summary)
        except Exception as e:
            print(f"[DB ERROR] complete_session: {e}")

        await safe_send_json({"type": "END", "summary": summary})
        print(f"[WS {session_id}] END sent")

        end_sent = True
        socket_open = False

        await asyncio.sleep(0.3)
        try:
            await ws.close()
        except Exception:
            pass

        delete_session(session_id)
        print(f"[WS {session_id}] Session cleaned up")

    def _save_answer_to_db(question_index, answer_text, audio_path, is_skipped):
        try:
            score = session.scores[-1] if session.scores else {}
            question_text = session.questions[question_index - 1] \
                if question_index <= len(session.questions) else ""
            duration = session.answer_durations[-1] if session.answer_durations else 0.0

            db_save_answer(
                db=db, session_id=session_id,
                question_index=question_index,
                question_text=question_text,
                answer_text=answer_text,
                score=score,
                duration_seconds=duration,
                audio_file_path=audio_path or "",
                stage=session.stage,
                project_mentioned=session.current_topic,
                is_skipped=is_skipped
            )
        except Exception as e:
            print(f"[DB ERROR] save_answer Q{question_index}: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # TIME MONITOR
    # ─────────────────────────────────────────────────────────────────────────

    async def monitor_time_limit():
        nonlocal buffer_warning_sent
        while socket_open and not session.is_finalized:
            await asyncio.sleep(1)
            if not session.session_start_time:
                continue

            elapsed = time.time() - session.session_start_time
            if elapsed < session.SESSION_LIMIT_SECONDS:
                remaining = int(session.SESSION_LIMIT_SECONDS - elapsed)
                in_buffer = False
            else:
                buffer_elapsed = elapsed - session.SESSION_LIMIT_SECONDS
                remaining = max(int(session.GRACE_PERIOD_SECONDS - buffer_elapsed), 0)
                in_buffer = True

            await safe_send_json({
                "type": "TIMER_UPDATE",
                "remaining_seconds": max(0, remaining),
                "in_buffer_time": in_buffer
            })

            if elapsed >= session.SESSION_LIMIT_SECONDS and not buffer_warning_sent:
                await safe_send_json({
                    "type": "BUFFER_TIME_WARNING",
                    "message": "⚠️ Main time expired! 2 minutes buffer remaining."
                })
                buffer_warning_sent = True

            if elapsed >= (session.SESSION_LIMIT_SECONDS + session.GRACE_PERIOD_SECONDS):
                print(f"[WS {session_id}] Buffer time expired")
                await send_end_and_close()
                break

    # ─────────────────────────────────────────────────────────────────────────
    # CORE: PROCESS ANSWER + GET NEXT QUESTION
    # Parallel execution: score runs while question generates
    # TTS has keepalive pings throughout
    # ─────────────────────────────────────────────────────────────────────────

    async def process_answer_and_get_next(answer_text: str, current_q_idx: int,
                                           audio_path: str, is_skipped: bool):

        # ── 1. Acknowledge receipt immediately ──
        await safe_send_json({
            "type": "FINAL_TRANSCRIPT",
            "text": "⏭️ Question skipped" if is_skipped else answer_text
        })

        # ── 2. Score answer in background thread ──
        score_task = asyncio.create_task(
            run_blocking(score_answer, answer_text, session.questions[-1])
        )

        # Send keepalive while scoring (usually 3-8s)
        while not score_task.done():
            try:
                await asyncio.wait_for(asyncio.shield(score_task), timeout=2.0)
            except asyncio.TimeoutError:
                if socket_open:
                    await safe_send_json({"type": "KEEPALIVE"})

        score = score_task.result()
        print(f"[PERF] Score computed: {score['final_score']:.2f}")

        # ── 3. Write score into session (fast in-memory ops) ──
        with session._state_lock:
            if not session.is_finalized and session.expecting_answer:
                duration = round(time.time() - session.current_question_start, 2) \
                           if session.current_question_start else 0.0
                session.answer_durations.append(duration)
                session.current_question_start = None
                session.answers.append(answer_text)
                session.scores.append(score)
                classification = session._classify_answer(score["final_score"])
                session.stage = session._decide_next_stage(session.current_topic, classification)
                session.expecting_answer = False

        _save_session(session_id, session)

        # ── 4. DB save in background — don't block on it ──
        asyncio.create_task(
            run_blocking(_save_answer_to_db, current_q_idx, answer_text, audio_path, is_skipped)
        )

        # ── 5. Check if interview should end ──
        if session.is_finalized or session._question_limit_reached():
            await send_end_and_close()
            return

        # ── 6. Generate next question in thread ──
        print(f"[PERF] Generating next question...")
        t_start = time.time()

        # Send keepalive while generating question (0.3-8s depending on cache)
        question_task = asyncio.create_task(run_blocking(session.next_question))

        while not question_task.done():
            try:
                await asyncio.wait_for(asyncio.shield(question_task), timeout=2.0)
            except asyncio.TimeoutError:
                if socket_open:
                    await safe_send_json({"type": "KEEPALIVE"})

        next_q = question_task.result()
        _save_session(session_id, session)
        print(f"[PERF] Question generated in {time.time() - t_start:.2f}s")

        if not next_q:
            await send_end_and_close()
            return

        # ── 7. Send question TEXT immediately (before TTS) ──
        # User can start reading/thinking while audio loads
        if session.session_start_time:
            elapsed = time.time() - session.session_start_time
            remaining = max(int(session.SESSION_LIMIT_SECONDS - elapsed), 0)
            in_buffer = elapsed >= session.SESSION_LIMIT_SECONDS
            await safe_send_json({
                "type": "TIMER_UPDATE",
                "remaining_seconds": remaining,
                "in_buffer_time": in_buffer
            })

        await safe_send_json({"type": "QUESTION", "text": next_q})

        if not socket_open:
            return

        # ── 8. Synthesize TTS with keepalive pings ──
        print(f"[PERF] Synthesizing TTS...")
        t_tts = time.time()
        audio = await synthesize_with_keepalive(next_q)
        print(f"[PERF] TTS done in {time.time() - t_tts:.2f}s")

        if audio and socket_open:
            await safe_send_json({"type": "TTS_START"})
            await safe_send_bytes(audio)
            await safe_send_json({"type": "TTS_END"})

    # ─────────────────────────────────────────────────────────────────────────
    # STARTUP: First question
    # FIX 1: Set session_start_time BEFORE calling send_question()
    # Old code set it AFTER, meaning it was null during the first 9s TTS wait
    # ─────────────────────────────────────────────────────────────────────────

    time_monitor_task = asyncio.create_task(monitor_time_limit())

    # Generate first question in thread
    first_q = await run_blocking(session.next_question)
    _save_session(session_id, session)

    if first_q:
        # ── CRITICAL FIX: Set timer BEFORE send_question, not after ──
        session.session_start_time = time.time()
        _save_session(session_id, session)

        try:
            db_start_session(db, session_id)
        except Exception as e:
            print(f"[DB ERROR] start_session: {e}")

        print(f"[WS {session_id}] ⏱️ Timer started, sending first question")
        await send_question(first_q)
    else:
        await send_end_and_close()
        time_monitor_task.cancel()
        db.close()
        return

    # ─────────────────────────────────────────────────────────────────────────
    # MAIN LOOP
    # FIX 3: Handle PING action so client heartbeats don't cause errors
    # ─────────────────────────────────────────────────────────────────────────

    try:
        while socket_open:
            msg = await ws.receive()

            if session.is_finalized:
                continue

            # ── Audio chunk ──
            if msg.get("bytes") and session.expecting_answer:
                audio_buffer.extend(msg["bytes"])
                continue

            # ── Text message ──
            if msg.get("text"):
                try:
                    payload = json.loads(msg["text"])
                    action = payload.get("action")

                    # FIX 3: Silently ignore client pings — just a heartbeat
                    if action == "PING":
                        continue

                    # ── SUBMIT ANSWER ──
                    elif action == "SUBMIT_ANSWER":
                        if not session.expecting_answer:
                            continue

                        current_q_idx = len(session.answers) + 1

                        if audio_buffer:
                            audio_bytes = bytes(audio_buffer)
                            audio_buffer.clear()

                            # Transcribe + save audio in parallel
                            audio_path, answer_text = await asyncio.gather(
                                run_blocking(save_candidate_audio, session_id,
                                             current_q_idx, audio_bytes),
                                run_blocking(transcribe_chunk, audio_bytes)
                            )
                        else:
                            audio_path = None
                            answer_text = payload.get("text", "").strip() or "No answer provided"

                        if not answer_text or not answer_text.strip():
                            answer_text = "No answer provided"

                        print(f"[WS {session_id}] Answer ({len(answer_text.split())} words): "
                              f"{answer_text[:60]}...")

                        await process_answer_and_get_next(
                            answer_text, current_q_idx, audio_path, is_skipped=False
                        )

                    # ── SKIP QUESTION ──
                    elif action == "SKIP_QUESTION":
                        if not session.expecting_answer:
                            continue

                        current_q_idx = len(session.answers) + 1
                        audio_buffer.clear()

                        print(f"[WS {session_id}] Q{current_q_idx} skipped")

                        await process_answer_and_get_next(
                            "Question skipped by candidate",
                            current_q_idx, None, is_skipped=True
                        )

                except json.JSONDecodeError:
                    pass

    except WebSocketDisconnect:
        print(f"[WS {session_id}] Client disconnected")
        socket_open = False
    except Exception as e:
        print(f"[WS {session_id}] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        socket_open = False
    finally:
        time_monitor_task.cancel()
        try:
            await time_monitor_task
        except Exception:
            pass
        db.close()

        if not end_sent:
            # Session ended without clean END message — save what we have
            try:
                if not session.is_finalized:
                    session.finalize(force_save_current_answer=False,
                                    reason="CONNECTION_DROPPED")
                    _save_session(session_id, session)
                summary = session.final_result()
                db_complete_session(db, session_id, summary)
                print(f"[WS {session_id}] Saved partial session on disconnect")
            except Exception as e:
                print(f"[WS {session_id}] Error saving on disconnect: {e}")