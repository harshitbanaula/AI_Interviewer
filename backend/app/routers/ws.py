# # backend/app/routers/ws.py

# import time
# import json
# import asyncio
# from fastapi import APIRouter, WebSocket, Query, WebSocketDisconnect
# from app.services.stt import transcribe_chunk
# from app.services.interview_state import get_session
# from app.services.tts import synthesize_speech
# from app.services.audio_storage import save_candidate_audio  # <--- NEW IMPORT

# router = APIRouter()

# @router.websocket("/ws/interview")
# async def interview_ws(ws: WebSocket, session_id: str = Query(...)):
#     await ws.accept()

#     session = get_session(session_id)
#     if not session:
#         await ws.send_json({"type": "ERROR", "text": "Invalid session"})
#         await ws.close()
#         return

#     # Start timer if not started
#     if not hasattr(session, 'session_start_time') or session.session_start_time is None:
#         session.session_start_time = time.time()
        
#     socket_open = True
#     end_sent = False
#     buffer_warning_sent = False
    
#     # We maintain a local buffer for the current question's audio
#     audio_buffer = bytearray()

#     async def safe_send_json(payload: dict):
#         nonlocal socket_open
#         if socket_open:
#             try:
#                 await ws.send_json(payload)
#             except Exception:
#                 socket_open = False

#     async def safe_send_bytes(data: bytes):
#         nonlocal socket_open
#         if socket_open:
#             try:
#                 await ws.send_bytes(data)
#             except Exception:
#                 socket_open = False

#     async def send_end_and_close():
#         nonlocal end_sent, socket_open, audio_buffer

#         if end_sent or not socket_open:
#             return

#         # Handle pending audio on timeout/close
#         if not session.completed:
#             if session.expecting_answer and audio_buffer:
#                 try:
#                     # --- RECORDING START (Timeout) ---
#                     # Determine current question number (1-based index)
#                     current_q_idx = len(session.answers) + 1
#                     save_candidate_audio(session_id, current_q_idx, bytes(audio_buffer))
#                     # --- RECORDING END ---

#                     answer_text = transcribe_chunk(bytes(audio_buffer))
#                     audio_buffer.clear()

#                     if answer_text.strip():
#                         print(f"[SESSION {session_id}] Timeout transcription captured.")
#                         session.save_answer(answer_text)
#                     else:
#                         print(f"[SESSION {session_id}] Timeout - no valid speech detected.")

#                 except Exception as e:
#                     print(f"[SESSION {session_id}] Timeout transcription error: {e}")

#             # Finalize Safely
#             session._finalize_interview(force_save_current_answer=True)

#         summary = session.final_result()

#         print(
#             f"[SESSION {session_id}] Sending END. "
#             f"Questions: {summary['questions_asked']}, "
#             f"Answers: {summary['questions_answered']}"
#         )

#         await safe_send_json({"type": "END", "summary": summary})

#         end_sent = True
#         socket_open = False
#         await asyncio.sleep(0.5)
#         await ws.close()

#     async def send_question(q: str):
#         if session.completed or not socket_open:
#             return

#         # Calculate effective elapsed time
#         elapsed = session.get_effective_elapsed_time()
        
#         if elapsed < session.SESSION_LIMIT_SECONDS:
#             remaining = int(session.SESSION_LIMIT_SECONDS - elapsed)
#             in_buffer = False
#         else:
#             buffer_elapsed = elapsed - session.SESSION_LIMIT_SECONDS
#             remaining = int(session.GRACE_PERIOD_SECONDS - buffer_elapsed)
#             remaining = max(remaining, 0)
#             in_buffer = True

#         await safe_send_json({
#             "type": "TIMER_UPDATE",
#             "remaining_seconds": remaining,
#             "in_buffer_time": in_buffer
#         })

#         await safe_send_json({
#             "type": "QUESTION",
#             "text": q
#         })

#         # TTS
#         audio = synthesize_speech(q, speaker_id=0, speed=0.85)
#         if audio and socket_open:
#             await safe_send_json({"type": "TTS_START"})
#             await safe_send_bytes(audio)
#             await safe_send_json({"type": "TTS_END"})

#     # Background time monitor
#     async def monitor_time_limit():
#         nonlocal buffer_warning_sent
        
#         while socket_open and not session.completed:
#             await asyncio.sleep(1)
            
#             elapsed = session.get_effective_elapsed_time()
            
#             if elapsed < session.SESSION_LIMIT_SECONDS:
#                 remaining = int(session.SESSION_LIMIT_SECONDS - elapsed)
#                 in_buffer = False
#             else:
#                 buffer_elapsed = elapsed - session.SESSION_LIMIT_SECONDS
#                 remaining = int(session.GRACE_PERIOD_SECONDS - buffer_elapsed)
#                 in_buffer = True
            
#             await safe_send_json({
#                 "type": "TIMER_UPDATE",
#                 "remaining_seconds": max(0, remaining),
#                 "in_buffer_time": in_buffer
#             })
            
#             if elapsed >= session.SESSION_LIMIT_SECONDS and not buffer_warning_sent:
#                 print(f"[SESSION {session_id}] Main time expired, entering buffer time")
#                 await safe_send_json({
#                     "type": "BUFFER_TIME_WARNING",
#                     "message": "⚠️ Main time expired! You have 2 minutes buffer time remaining."
#                 })
#                 buffer_warning_sent = True
            
#             if elapsed >= (session.SESSION_LIMIT_SECONDS + session.GRACE_PERIOD_SECONDS):
#                 print(f"[SESSION {session_id}] Buffer time expired - force ending interview")
#                 await send_end_and_close()
#                 break

#     time_monitor_task = asyncio.create_task(monitor_time_limit())

#     # Send FIRST question
#     first_q = session.next_question()
#     if first_q:
#         await send_question(first_q)
#     else:
#         await send_end_and_close()
#         time_monitor_task.cancel()
#         return

#     try:
#         while socket_open:
#             msg = await ws.receive()

#             if session.completed:
#                 continue

#             # Handle AUDIO
#             if msg.get("bytes") and session.expecting_answer:
#                 audio_buffer.extend(msg["bytes"])
#                 continue

#             # Handle TEXT messages (JSON)
#             if msg.get("text"):
#                 try:
#                     payload = json.loads(msg["text"])
#                     msg_type = payload.get("type")
#                     action = payload.get("action")

#                     # TTS SYNC
#                     if msg_type == "TTS_PLAYBACK_START":
#                         session.pause_timer()
#                         continue
                    
#                     if msg_type == "TTS_PLAYBACK_END":
#                         session.resume_timer()
#                         continue

#                     if action == "SUBMIT_ANSWER":
#                         if not session.expecting_answer:
#                             continue
                        
#                         # --- RECORDING START ---
#                         if audio_buffer:
#                             # 1. Determine current question number (e.g., if we have 0 answers, this is question 1)
#                             current_q_idx = len(session.answers) + 1
                            
#                             # 2. Save the Audio Buffer to Disk
#                             save_candidate_audio(session_id, current_q_idx, bytes(audio_buffer))
                            
#                             # 3. Transcribe
#                             answer_text = transcribe_chunk(bytes(audio_buffer))
#                             audio_buffer.clear()
#                         else:
#                             answer_text = payload.get("text", "").strip() or "No answer provided"
#                         # --- RECORDING END ---

#                         print(f"[SESSION {session_id}] Answer received: {answer_text[:50]}...")

#                         session.save_answer(answer_text)

#                         await safe_send_json({
#                             "type": "FINAL_TRANSCRIPT",
#                             "text": answer_text
#                         })

#                         if session.completed:
#                             print(f"[SESSION {session_id}] Interview completed after saving answer")
#                             await send_end_and_close()
#                             break

#                         next_q = session.next_question()
                        
#                         if next_q:
#                             print(f"[SESSION {session_id}] Sending next question")
#                             await send_question(next_q)
#                         else:
#                             print(f"[SESSION {session_id}] No more questions - ending interview")
#                             await send_end_and_close()
#                             break
                            
#                 except json.JSONDecodeError:
#                     pass

#     except WebSocketDisconnect:
#         print(f"[SESSION {session_id}] WebSocket disconnected")
#         socket_open = False
#     except Exception as e:
#         print(f"[SESSION {session_id}] Error: {e}")
#         import traceback
#         traceback.print_exc()
#         socket_open = False
#     finally:
#         time_monitor_task.cancel()
        
#         if socket_open and not end_sent:
#             await send_end_and_close()




# # backend/app/routers/ws.py - WITH SKIP QUESTION SUPPORT

# import time
# import json
# import asyncio
# from fastapi import APIRouter, WebSocket, Query, WebSocketDisconnect
# from app.services.stt import transcribe_chunk
# from app.services.interview_state import get_session
# from app.services.tts import synthesize_speech
# from app.services.audio_storage import save_candidate_audio

# router = APIRouter()

# @router.websocket("/ws/interview")
# async def interview_ws(ws: WebSocket, session_id: str = Query(...)):
#     await ws.accept()

#     session = get_session(session_id)
#     if not session:
#         await ws.send_json({"type": "ERROR", "text": "Invalid session"})
#         await ws.close()
#         return

#     socket_open = True
#     end_sent = False
#     buffer_warning_sent = False
#     audio_buffer = bytearray()

#     async def safe_send_json(payload: dict):
#         nonlocal socket_open
#         if socket_open:
#             try:
#                 await ws.send_json(payload)
#             except Exception:
#                 socket_open = False

#     async def safe_send_bytes(data: bytes):
#         nonlocal socket_open
#         if socket_open:
#             try:
#                 await ws.send_bytes(data)
#             except Exception:
#                 socket_open = False

#     async def send_end_and_close():
#         nonlocal end_sent, socket_open, audio_buffer

#         if end_sent or not socket_open:
#             return

#         if not session.completed:
#             if session.expecting_answer and audio_buffer:
#                 try:
#                     current_q_idx = len(session.answers) + 1
#                     save_candidate_audio(session_id, current_q_idx, bytes(audio_buffer))
                    
#                     answer_text = transcribe_chunk(bytes(audio_buffer))
#                     audio_buffer.clear()

#                     if answer_text.strip():
#                         session.save_answer(answer_text)

#                 except Exception as e:
#                     print(f"[SESSION {session_id}] Timeout transcription error: {e}")

#             session._finalize_interview(force_save_current_answer=True)

#         summary = session.final_result()

#         print(
#             f"[SESSION {session_id}] Sending END. "
#             f"Questions: {summary['questions_asked']}, "
#             f"Answers: {summary['questions_answered']}"
#         )

#         await safe_send_json({"type": "END", "summary": summary})

#         end_sent = True
#         socket_open = False
#         await asyncio.sleep(0.5)
#         await ws.close()

#     async def send_question(q: str):
#         """Send question - timer continues running throughout"""
#         if session.completed or not socket_open:
#             return

#         elapsed = time.time() - session.session_start_time
        
#         if elapsed < session.SESSION_LIMIT_SECONDS:
#             remaining = int(session.SESSION_LIMIT_SECONDS - elapsed)
#             in_buffer = False
#         else:
#             buffer_elapsed = elapsed - session.SESSION_LIMIT_SECONDS
#             remaining = int(session.GRACE_PERIOD_SECONDS - buffer_elapsed)
#             remaining = max(remaining, 0)
#             in_buffer = True

#         await safe_send_json({
#             "type": "TIMER_UPDATE",
#             "remaining_seconds": remaining,
#             "in_buffer_time": in_buffer
#         })

#         await safe_send_json({
#             "type": "QUESTION",
#             "text": q
#         })

#         audio = synthesize_speech(q, speaker_id=0, speed=0.85)
#         if audio and socket_open:
#             await safe_send_json({"type": "TTS_START"})
#             await safe_send_bytes(audio)
#             await safe_send_json({"type": "TTS_END"})

#     async def monitor_time_limit():
#         nonlocal buffer_warning_sent
        
#         while socket_open and not session.completed:
#             await asyncio.sleep(1)
            
#             if not session.session_start_time:
#                 continue
            
#             elapsed = time.time() - session.session_start_time
            
#             if elapsed < session.SESSION_LIMIT_SECONDS:
#                 remaining = int(session.SESSION_LIMIT_SECONDS - elapsed)
#                 in_buffer = False
#             else:
#                 buffer_elapsed = elapsed - session.SESSION_LIMIT_SECONDS
#                 remaining = int(session.GRACE_PERIOD_SECONDS - buffer_elapsed)
#                 in_buffer = True
            
#             await safe_send_json({
#                 "type": "TIMER_UPDATE",
#                 "remaining_seconds": max(0, remaining),
#                 "in_buffer_time": in_buffer
#             })
            
#             if elapsed >= session.SESSION_LIMIT_SECONDS and not buffer_warning_sent:
#                 print(f"[SESSION {session_id}] Main time expired, entering buffer time")
#                 await safe_send_json({
#                     "type": "BUFFER_TIME_WARNING",
#                     "message": "⚠️ Main time expired! You have 2 minutes buffer time remaining."
#                 })
#                 buffer_warning_sent = True
            
#             if elapsed >= (session.SESSION_LIMIT_SECONDS + session.GRACE_PERIOD_SECONDS):
#                 print(f"[SESSION {session_id}] Buffer time expired - force ending interview")
#                 await send_end_and_close()
#                 break

#     time_monitor_task = asyncio.create_task(monitor_time_limit())

#     # First question - start timer
#     first_q = session.next_question()
    
#     if first_q:
#         session.session_start_time = time.time()
#         print(f"[SESSION {session_id}] ⏱️  Timer started")
#         await send_question(first_q)
#     else:
#         await send_end_and_close()
#         time_monitor_task.cancel()
#         return

#     # Main loop
#     try:
#         while socket_open:
#             msg = await ws.receive()

#             if session.completed:
#                 continue

#             # Handle AUDIO
#             if msg.get("bytes") and session.expecting_answer:
#                 audio_buffer.extend(msg["bytes"])
#                 continue

#             # Handle TEXT messages
#             if msg.get("text"):
#                 try:
#                     payload = json.loads(msg["text"])
#                     action = payload.get("action")

                    
#                     # SUBMIT ANSWER
                    
#                     if action == "SUBMIT_ANSWER":
#                         if not session.expecting_answer:
#                             continue
                        
#                         # Save audio and transcribe
#                         if audio_buffer:
#                             current_q_idx = len(session.answers) + 1
#                             save_candidate_audio(session_id, current_q_idx, bytes(audio_buffer))
#                             answer_text = transcribe_chunk(bytes(audio_buffer))
#                             audio_buffer.clear()
#                         else:
#                             answer_text = payload.get("text", "").strip() or "No answer provided"

#                         print(f"[SESSION {session_id}] Answer: {answer_text[:50]}...")

#                         session.save_answer(answer_text)

#                         await safe_send_json({
#                             "type": "FINAL_TRANSCRIPT",
#                             "text": answer_text
#                         })

#                         if session.completed:
#                             print(f"[SESSION {session_id}] Interview completed")
#                             await send_end_and_close()
#                             break

#                         next_q = session.next_question()
                        
#                         if next_q:
#                             print(f"[SESSION {session_id}] Sending next question")
#                             await send_question(next_q)
#                         else:
#                             print(f"[SESSION {session_id}] No more questions")
#                             await send_end_and_close()
#                             break

                    
#                     # SKIP QUESTION (NEW)
                    
#                     elif action == "SKIP_QUESTION":
#                         if not session.expecting_answer:
#                             continue
                        
#                         print(f"[SESSION {session_id}] Question skipped by candidate")
                        
#                         # Clear any buffered audio
#                         if audio_buffer:
#                             audio_buffer.clear()
                        
#                         # Save as skipped
#                         session.save_answer("Question skipped by candidate")

#                         await safe_send_json({
#                             "type": "FINAL_TRANSCRIPT",
#                             "text": "⏭️ Question skipped"
#                         })

#                         if session.completed:
#                             print(f"[SESSION {session_id}] Interview completed")
#                             await send_end_and_close()
#                             break

#                         next_q = session.next_question()
                        
#                         if next_q:
#                             print(f"[SESSION {session_id}] Sending next question after skip")
#                             await send_question(next_q)
#                         else:
#                             print(f"[SESSION {session_id}] No more questions")
#                             await send_end_and_close()
#                             break
                            
#                 except json.JSONDecodeError:
#                     pass

#     except WebSocketDisconnect:
#         print(f"[SESSION {session_id}] WebSocket disconnected")
#         socket_open = False
#     except Exception as e:
#         print(f"[SESSION {session_id}] Error: {e}")
#         import traceback
#         traceback.print_exc()
#         socket_open = False
#     finally:
#         time_monitor_task.cancel()
        
#         if socket_open and not end_sent:
#             await send_end_and_close()



# backend/app/routers/ws.py - WITH DATABASE INTEGRATION

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
    """Get a new DB session for WebSocket handler"""
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

    # DB session for this interview
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
        nonlocal end_sent, socket_open, audio_buffer

        if end_sent or not socket_open:
            return

        if not session.completed:
            if session.expecting_answer and audio_buffer:
                try:
                    current_q_idx = len(session.answers) + 1
                    audio_path = save_candidate_audio(session_id, current_q_idx, bytes(audio_buffer))
                    answer_text = transcribe_chunk(bytes(audio_buffer))
                    audio_buffer.clear()

                    if answer_text.strip():
                        session.save_answer(answer_text)

                        # ── DB: save final answer ──
                        _save_answer_to_db(
                            question_index=current_q_idx,
                            answer_text=answer_text,
                            audio_path=audio_path,
                            is_skipped=False
                        )

                except Exception as e:
                    print(f"[SESSION {session_id}] Timeout transcription error: {e}")

            session._finalize_interview(force_save_current_answer=True)

        summary = session.final_result()

        # ── DB: mark session complete ──
        try:
            db_complete_session(db, session_id, summary)
        except Exception as e:
            print(f"[DB ERROR] complete_session: {e}")

        print(
            f"[SESSION {session_id}] Sending END. "
            f"Questions: {summary['questions_asked']}, "
            f"Answers: {summary['questions_answered']}"
        )

        await safe_send_json({"type": "END", "summary": summary})

        end_sent = True
        socket_open = False
        await asyncio.sleep(0.5)
        await ws.close()

        delete_session(session_id)

    def _save_answer_to_db(
        question_index: int,
        answer_text: str,
        audio_path: str,
        is_skipped: bool
    ):
        """
        Helper to save answer to DB.
        Reads scores and question from session state.
        """
        try:
            # Get the score that was just saved to session
            score = session.scores[-1] if session.scores else {}
            question_text = session.questions[question_index - 1] \
                if question_index <= len(session.questions) else ""
            duration = session.answer_durations[-1] \
                if session.answer_durations else 0.0

            db_save_answer(
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

        while socket_open and not session.completed:
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
                print(f"[SESSION {session_id}] Main time expired")
                await safe_send_json({
                    "type": "BUFFER_TIME_WARNING",
                    "message": "Main time expired! You have 2 minutes buffer time remaining."
                })
                buffer_warning_sent = True

            if elapsed >= (session.SESSION_LIMIT_SECONDS + session.GRACE_PERIOD_SECONDS):
                print(f"[SESSION {session_id}] Buffer time expired - force ending")
                await send_end_and_close()
                break

    time_monitor_task = asyncio.create_task(monitor_time_limit())

    # ── First question - start timer + DB ──
    first_q = session.next_question()

    if first_q:
        session.session_start_time = time.time()

        # ── DB: mark session as active ──
        try:
            db_start_session(db, session_id)
        except Exception as e:
            print(f"[DB ERROR] start_session: {e}")

        print(f"[SESSION {session_id}] ⏱️  Timer started")
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

            if session.completed:
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

                        print(f"[SESSION {session_id}] Answer: {answer_text[:50]}...")

                        session.save_answer(answer_text)

                        # ── DB: save answer ──
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

                        if session.completed:
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

                        print(f"[SESSION {session_id}] Question {current_q_idx} skipped")

                        # Clear audio buffer
                        if audio_buffer:
                            audio_buffer.clear()

                        session.save_answer("Question skipped by candidate")

                        # ── DB: save skipped answer ──
                        _save_answer_to_db(
                            question_index=current_q_idx,
                            answer_text="Question skipped by candidate",
                            audio_path=None,
                            is_skipped=True     # ← marks as skipped in DB
                        )

                        await safe_send_json({
                            "type": "FINAL_TRANSCRIPT",
                            "text": " Question skipped"
                        })

                        if session.completed:
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
        print(f"[SESSION {session_id}] WebSocket disconnected")
        socket_open = False
    except Exception as e:
        print(f"[SESSION {session_id}] Error: {e}")
        import traceback
        traceback.print_exc()
        socket_open = False
    finally:
        time_monitor_task.cancel()
        db.close()  # Always close DB session

        if socket_open and not end_sent:
            await send_end_and_close()