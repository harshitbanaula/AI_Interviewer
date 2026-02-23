# backend/app/routers/ws.py
# FIXED: Properly waits for finalization before sending END message

import time
import json
import asyncio
from fastapi import APIRouter, WebSocket, Query, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.stt import transcribe_chunk
from app.services.interview_state import get_session, delete_session
from app.services.tts import synthesize_speech
from app.services.audio_storage import save_candidate_audio
from app.repository import (
    db_start_session,
    db_save_answer,
    db_complete_session
)

router = APIRouter()


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

    async def safe_send_json(payload: dict):
        nonlocal socket_open
        if socket_open:
            try:
                await ws.send_json(payload)
            except Exception:
                socket_open = False

    async def safe_send_bytes(data: bytes):
        nonlocal socket_open
        if socket_open:
            try:
                await ws.send_bytes(data)
            except Exception:
                socket_open = False

    async def send_end_and_close():
        nonlocal end_sent, socket_open

        if end_sent:
            print(f"[WS {session_id}] END already sent, skipping")
            return

        print(f"[WS {session_id}] send_end_and_close() called")

        # ── STEP 1: Finalize interview (if not already done) ──
        if not session.is_finalized:
            print(f"[WS {session_id}] Finalizing interview...")
            session.finalize(force_save_current_answer=True)
            
            # Give finalization a moment to complete (feedback generation)
            await asyncio.sleep(0.5)
        
        print(f"[WS {session_id}] Interview finalized, is_finalized={session.is_finalized}")

        # ── STEP 2: Get final results ──
        summary = session.final_result()
        
        print(f"[WS {session_id}] Got summary: {summary['questions_asked']}Q, {summary['questions_answered']}A, feedback: {len(summary['feedback'])} chars")

        # ── STEP 3: Save to database ──
        try:
            db_complete_session(db, session_id, summary)
            print(f"[WS {session_id}] Saved to database")
        except Exception as e:
            print(f"[DB ERROR] complete_session: {e}")

        # ── STEP 4: Send END message with full results ──
        try:
            await safe_send_json({"type": "END", "summary": summary})
            print(f"[WS {session_id}] END message sent")
        except Exception as e:
            print(f"[WS {session_id}] Error sending END: {e}")

        # ── STEP 5: Cleanup ──
        end_sent = True
        socket_open = False
        
        await asyncio.sleep(0.5)
        
        try:
            await ws.close()
        except:
            pass

        delete_session(session_id)
        print(f"[WS {session_id}] Session deleted")

    def _save_answer_to_db(
        question_index: int,
        answer_text: str,
        audio_path: str,
        is_skipped: bool
    ):
        try:
            score = session.scores[-1] if session.scores else {}
            question_text = session.questions[question_index - 1] \
                if question_index <= len(session.questions) else ""
            duration = session.answer_durations[-1] \
                if session.answer_durations else 0.0

            success = db_save_answer(
                db=db,
                session_id=session_id,
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

            if not success:
                print(f"[DB ERROR] Failed to save answer for Q{question_index}")

        except Exception as e:
            print(f"[DB ERROR] save_answer Q{question_index}: {e}")

    async def send_question(q: str):
        if session.completed or not socket_open:
            return

        elapsed = time.time() - session.session_start_time

        if elapsed < session.SESSION_LIMIT_SECONDS:
            remaining = int(session.SESSION_LIMIT_SECONDS - elapsed)
            in_buffer = False
        else:
            buffer_elapsed = elapsed - session.SESSION_LIMIT_SECONDS
            remaining = int(session.GRACE_PERIOD_SECONDS - buffer_elapsed)
            remaining = max(remaining, 0)
            in_buffer = True

        await safe_send_json({
            "type": "TIMER_UPDATE",
            "remaining_seconds": remaining,
            "in_buffer_time": in_buffer
        })

        await safe_send_json({"type": "QUESTION", "text": q})

        audio = synthesize_speech(q, speaker_id=0, speed=0.85)
        if audio and socket_open:
            await safe_send_json({"type": "TTS_START"})
            await safe_send_bytes(audio)
            await safe_send_json({"type": "TTS_END"})

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
                remaining = int(session.GRACE_PERIOD_SECONDS - buffer_elapsed)
                in_buffer = True

            await safe_send_json({
                "type": "TIMER_UPDATE",
                "remaining_seconds": max(0, remaining),
                "in_buffer_time": in_buffer
            })

            if elapsed >= session.SESSION_LIMIT_SECONDS and not buffer_warning_sent:
                print(f"[WS {session_id}] Main time expired")
                await safe_send_json({
                    "type": "BUFFER_TIME_WARNING",
                    "message": "⚠️ Main time expired! You have 2 minutes buffer time remaining."
                })
                buffer_warning_sent = True

            if elapsed >= (session.SESSION_LIMIT_SECONDS + session.GRACE_PERIOD_SECONDS):
                print(f"[WS {session_id}] Buffer time expired - ending interview")
                await send_end_and_close()
                break

    time_monitor_task = asyncio.create_task(monitor_time_limit())

    # ── First question ──
    first_q = session.next_question()

    if first_q:
        session.session_start_time = time.time()

        try:
            db_start_session(db, session_id)
        except Exception as e:
            print(f"[DB ERROR] start_session: {e}")

        print(f"[WS {session_id}] ⏱️  Timer started")
        await send_question(first_q)
    else:
        await send_end_and_close()
        time_monitor_task.cancel()
        db.close()
        return

    # ── Main loop ──
    try:
        while socket_open:
            msg = await ws.receive()

            if session.is_finalized:
                continue

            # Handle AUDIO
            if msg.get("bytes") and session.expecting_answer:
                audio_buffer.extend(msg["bytes"])
                continue

            # Handle TEXT
            if msg.get("text"):
                try:
                    payload = json.loads(msg["text"])
                    action = payload.get("action")

                    # ── SUBMIT ANSWER ──
                    if action == "SUBMIT_ANSWER":
                        if not session.expecting_answer:
                            continue

                        current_q_idx = len(session.answers) + 1

                        if audio_buffer:
                            audio_path = save_candidate_audio(
                                session_id, current_q_idx, bytes(audio_buffer)
                            )
                            answer_text = transcribe_chunk(bytes(audio_buffer))
                            audio_buffer.clear()
                        else:
                            audio_path = None
                            answer_text = payload.get("text", "").strip() or "No answer provided"

                        print(f"[WS {session_id}] Answer: {answer_text[:50]}...")

                        session.save_answer(answer_text)

                        _save_answer_to_db(
                            question_index=current_q_idx,
                            answer_text=answer_text,
                            audio_path=audio_path,
                            is_skipped=False
                        )

                        await safe_send_json({
                            "type": "FINAL_TRANSCRIPT",
                            "text": answer_text
                        })

                        # Check if interview should end
                        if session.is_finalized:
                            await send_end_and_close()
                            break

                        next_q = session.next_question()
                        if next_q:
                            await send_question(next_q)
                        else:
                            await send_end_and_close()
                            break

                    # ── SKIP QUESTION ──
                    elif action == "SKIP_QUESTION":
                        if not session.expecting_answer:
                            continue

                        current_q_idx = len(session.answers) + 1

                        print(f"[WS {session_id}] Question {current_q_idx} skipped")

                        if audio_buffer:
                            audio_buffer.clear()

                        session.save_answer("Question skipped by candidate")

                        _save_answer_to_db(
                            question_index=current_q_idx,
                            answer_text="Question skipped by candidate",
                            audio_path=None,
                            is_skipped=True
                        )

                        await safe_send_json({
                            "type": "FINAL_TRANSCRIPT",
                            "text": "⏭️ Question skipped"
                        })

                        if session.is_finalized:
                            await send_end_and_close()
                            break

                        next_q = session.next_question()
                        if next_q:
                            await send_question(next_q)
                        else:
                            await send_end_and_close()
                            break

                except json.JSONDecodeError:
                    pass

    except WebSocketDisconnect:
        print(f"[WS {session_id}] WebSocket disconnected")
        socket_open = False
    except Exception as e:
        print(f"[WS {session_id}] Error: {e}")
        import traceback
        traceback.print_exc()
        socket_open = False
    finally:
        time_monitor_task.cancel()
        try:
            await time_monitor_task
        except:
            pass
        db.close()

        if socket_open and not end_sent:
            await send_end_and_close()