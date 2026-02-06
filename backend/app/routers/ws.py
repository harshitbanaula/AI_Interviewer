# # backend/app/routers/ws.py

# from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
# from app.services.stt import transcribe_chunk
# from app.services.interview_state import get_session
# import json

# router = APIRouter()

# @router.websocket("/ws/interview")
# async def interview_ws(ws: WebSocket, session_id: str = Query(...)):
#     await ws.accept()

#     session = get_session(session_id)
#     if not session:
#         await ws.send_json({"type": "ERROR", "text": "Invalid session"})
#         return

#     audio_buffer = bytearray()

#     # Send first question
#     q = session.next_question()
#     if q:
#         await ws.send_json({"type": "QUESTION", "text": q})

#     try:
#         while True:
#             msg = await ws.receive()

#             # Audio bytes
#             if msg.get("bytes") and session.expecting_answer:
#                 audio_buffer.extend(msg["bytes"])

#             # Control messages
#             if msg.get("text"):
#                 payload = json.loads(msg["text"])

#                 # Manual answer submission
#                 if payload.get("text") == "SUBMIT_ANSWER":
#                     # Convert audio to text
#                     text = transcribe_chunk(bytes(audio_buffer))
#                     audio_buffer.clear()

#                     # Ensure non-empty placeholder
#                     if not text or not text.strip():
#                         text = "[No answer provided]"

#                     # Save answer and generate score
#                     session.save_answer(text)

#                     # Send feedback for this answer
#                     latest_score = session.scores[-1]
#                     feedback_msg = {
#                         "type": "FEEDBACK",
#                         "text": json.dumps({
#                             "overall": latest_score.get("final_score", 0),
#                             "content_score": latest_score.get("correctness", 0),
#                             "technical_depth": latest_score.get("depth", 0),
#                             "communication_score": latest_score.get("clarity", 0),
#                             "strengths": latest_score.get("strengths", []),
#                             "improvements": latest_score.get("improvements", [])
#                         })
#                     }
#                     await ws.send_json(feedback_msg)

#                     # Send next question or end
#                     next_q = session.next_question()
#                     if next_q:
#                         await ws.send_json({"type": "QUESTION", "text": next_q})
#                     else:
#                         summary = session.final_result()
#                         await ws.send_json({
#                             "type": "END",
#                             "text": "Interview completed",
#                             "summary": summary
#                         })
#                         break

#                 # Stop interview manually
#                 elif payload.get("text") == "STOP_INTERVIEW":
#                     break

#     except WebSocketDisconnect:
#         print("WebSocket client disconnected")

#     except Exception as e:
#         print("WebSocket error:", e)

#     finally:
#         # Cleanup audio
#         audio_buffer.clear()





# # backend/app/routers/ws.py

# from fastapi import APIRouter, WebSocket, Query
# from app.services.stt import transcribe_chunk
# from app.services.interview_state import get_session
# # from app.services.llm_feedback import generate_feedback 
# import json

# router = APIRouter()

# @router.websocket("/ws/interview")
# async def interview_ws(ws: WebSocket, session_id: str = Query(...)):
#     await ws.accept()

#     session = get_session(session_id)
#     if not session:
#         await ws.send_json({"type": "ERROR", "text": "Invalid session"})
#         return

#     audio_buffer = bytearray()

#     # Send first question
#     q = session.next_question()
#     await ws.send_json({"type": "QUESTION", "text": q})

#     try:
#         while True:
#             msg = await ws.receive()

#             # Audio bytes from client
#             if msg.get("bytes") and session.expecting_answer:
#                 audio_buffer.extend(msg["bytes"])

#             # Control messages
#             if msg.get("text"):
#                 payload = json.loads(msg["text"])

#                 if payload.get("text") == "SUBMIT_ANSWER":
#                     # Convert audio to text if available
#                     text = transcribe_chunk(bytes(audio_buffer)) if audio_buffer else ""
#                     audio_buffer.clear()

#                     session.save_answer(text)

#                     # Send live transcript
#                     await ws.send_json({
#                         "type": "FINAL_TRANSCRIPT",
#                         "text": text if text else "No answer provided"
#                     })

#                     # Next question or finish
#                     next_q = session.next_question()
#                     if next_q:
#                         await ws.send_json({"type": "QUESTION", "text": next_q})
#                     else:
#                         summary = session.final_result()
#                         await ws.send_json({
#                                 "type": "END",
#                                 "text": "Interview completed",
#                                 "summary": summary
#                         })  


#     except Exception as e:
#         print("WebSocket error:", e)
#         await ws.close()


# # backend/app/routers/ws.py

# from fastapi import APIRouter, WebSocket, Query
# from app.services.stt import transcribe_chunk
# from app.services.interview_state import get_session
# from app.services.tts import synthesize_speech
# import json

# router = APIRouter()


# @router.websocket("/ws/interview")
# async def interview_ws(ws: WebSocket, session_id: str = Query(...)):
#     await ws.accept()

#     session = get_session(session_id)
#     if not session:
#         await ws.send_json({"type": "ERROR", "text": "Invalid session"})
#         await ws.close()
#         return

#     audio_buffer = bytearray()

#     # Send first question (TEXT + TTS)
#     q = session.next_question()
#     await ws.send_json({"type": "QUESTION", "text": q})

#     audio = synthesize_speech(q, speaker_id=0)
#     if audio:
#         await ws.send_json({"type": "TTS_START"})
#         await ws.send_bytes(audio)
#         await ws.send_json({"type": "TTS_END"})

#     try:
#         while True:
#             msg = await ws.receive()

#             # Audio bytes from client
#             if msg.get("bytes") and session.expecting_answer:
#                 audio_buffer.extend(msg["bytes"])

#             # Control messages
#             if msg.get("text"):
#                 payload = json.loads(msg["text"])

#                 if payload.get("text") == "SUBMIT_ANSWER":
#                     # Convert audio to text
#                     text = transcribe_chunk(bytes(audio_buffer)) if audio_buffer else ""
#                     audio_buffer.clear()

#                     session.save_answer(text)

#                     # Send final transcript
#                     await ws.send_json({
#                         "type": "FINAL_TRANSCRIPT",
#                         "text": text if text else "No answer provided"
#                     })

#                     # Send next question
#                     next_q = session.next_question()
#                     if next_q:
#                         await ws.send_json({"type": "QUESTION", "text": next_q})

#                         audio = synthesize_speech(next_q, speaker_id=0)
#                         if audio:
#                             await ws.send_json({"type": "TTS_START"})
#                             await ws.send_bytes(audio)
#                             await ws.send_json({"type": "TTS_END"})
#                     else:
#                         summary = session.final_result()
#                         await ws.send_json({
#                             "type": "END",
#                             "text": "Interview completed",
#                             "summary": summary
#                         })

#     except Exception as e:
#         print("WebSocket error:", e)
#         await ws.close()


# # backend/app/routers/ws.py

# from fastapi import APIRouter, WebSocket, Query
# from app.services.stt import transcribe_chunk
# from app.services.interview_state import get_session
# from app.services.tts import synthesize_speech
# import json

# router = APIRouter()

# @router.websocket("/ws/interview")
# async def interview_ws(ws: WebSocket, session_id: str = Query(...)):
#     await ws.accept()
#     session = get_session(session_id)

#     if not session:
#         await ws.send_json({"type": "ERROR", "text": "Invalid session"})
#         await ws.close()
#         return

#     audio_buffer = bytearray()

#     # Send first question
#     q = session.next_question()
#     if q:
#         await ws.send_json({"type": "QUESTION", "text": q})
#         audio = synthesize_speech(q, speaker_id=0, speed=0.85)
#         if audio:
#             await ws.send_json({"type": "TTS_START"})
#             await ws.send_bytes(audio)
#             await ws.send_json({"type": "TTS_END"})

#     try:
#         while True:
#             # Only receive if connection is open
#             try:
#                 msg = await ws.receive()
#             except Exception:
#                 print("WebSocket closed, exiting loop.")
#                 break

#             if msg.get("bytes") and session.expecting_answer:
#                 audio_buffer.extend(msg["bytes"])

#             if msg.get("text"):
#                 try:
#                     payload = json.loads(msg["text"])
#                 except json.JSONDecodeError:
#                     continue

#                 if payload.get("text") == "SUBMIT_ANSWER":
#                     text = transcribe_chunk(bytes(audio_buffer)) if audio_buffer else ""
#                     audio_buffer.clear()
#                     session.save_answer(text)

#                     await ws.send_json({
#                         "type": "FINAL_TRANSCRIPT",
#                         "text": text if text else "No answer provided"
#                     })

#                     next_q = session.next_question()
#                     if next_q:
#                         await ws.send_json({"type": "QUESTION", "text": next_q})
#                         audio = synthesize_speech(next_q, speaker_id=0,speed=0.85)
#                         if audio:
#                             await ws.send_json({"type": "TTS_START"})
#                             await ws.send_bytes(audio)
#                             await ws.send_json({"type": "TTS_END"})
#                     else:
#                         summary = session.final_result()
#                         await ws.send_json({
#                             "type": "END",
#                             "text": "Interview completed",
#                             "summary": summary
#                         })
#                         # Once interview ends, close websocket safely
#                         try:
#                             await ws.close()
#                         except:
#                             pass
#                         break

#     except Exception as e:
#         print("WebSocket error:", e)
#         try:
#             await ws.close()
#         except:
#             pass



# backend/app/routers/ws.py

import time
import json
import asyncio
from fastapi import APIRouter, WebSocket, Query, WebSocketDisconnect
from app.services.stt import transcribe_chunk
from app.services.interview_state import get_session
from app.services.tts import synthesize_speech

router = APIRouter()


@router.websocket("/ws/interview")
async def interview_ws(ws: WebSocket, session_id: str = Query(...)):
    await ws.accept()

    session = get_session(session_id)
    if not session:
        await ws.send_json({"type": "ERROR", "text": "Invalid session"})
        await ws.close()
        return

    session.session_start_time = time.time()
    socket_open = True
    end_sent = False

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
        if end_sent or not socket_open:
            return

        # Force finalization
        if not session.completed:
            session._finalize_interview()

        summary = session.final_result()
        print(f"[SESSION {session_id}] Sending END with summary")
        await safe_send_json({"type": "END", "summary": summary})
        end_sent = True
        socket_open = False
        
        await asyncio.sleep(0.5)
        await ws.close()

    # Send initial timer
    await safe_send_json({
        "type": "TIMER_INIT",
        "total_seconds": session.SESSION_LIMIT_SECONDS
    })

    audio_buffer = bytearray()

    async def send_question(q: str):
        if session.completed or not socket_open:
            return

        remaining = session.get_remaining_time()

        await safe_send_json({
            "type": "TIMER_UPDATE",
            "remaining_seconds": remaining
        })

        await safe_send_json({
            "type": "QUESTION",
            "text": q
        })

        # TTS
        audio = synthesize_speech(q, speaker_id=0, speed=0.85)
        if audio and socket_open:
            await safe_send_json({"type": "TTS_START"})
            await safe_send_bytes(audio)
            await safe_send_json({"type": "TTS_END"})

    # Background time monitor
    async def monitor_time_limit():
        while socket_open and not session.completed:
            await asyncio.sleep(5)
            
            if session._time_exceeded():
                print(f"[SESSION {session_id}] Time exceeded - ending interview")
                await send_end_and_close()
                break

    time_monitor_task = asyncio.create_task(monitor_time_limit())

    # Send FIRST question
    first_q = session.next_question()
    if first_q:
        await send_question(first_q)
    else:
        await send_end_and_close()
        time_monitor_task.cancel()
        return

    try:
        while socket_open:
            msg = await ws.receive()

            # Already completed - ignore further messages
            if session.completed:
                continue

            # Handle AUDIO
            if msg.get("bytes") and session.expecting_answer:
                audio_buffer.extend(msg["bytes"])
                continue

            # Handle TEXT
            if msg.get("text"):
                payload = json.loads(msg["text"])

                if payload.get("action") == "SUBMIT_ANSWER":
                    
                    # Transcribe
                    if audio_buffer:
                        answer_text = transcribe_chunk(bytes(audio_buffer))
                        audio_buffer.clear()
                    else:
                        answer_text = payload.get("text", "").strip() or "No answer provided"

                    print(f"[SESSION {session_id}] Answer received: {answer_text[:50]}...")

                    # Save answer
                    session.save_answer(answer_text)

                    # Send transcript
                    await safe_send_json({
                        "type": "FINAL_TRANSCRIPT",
                        "text": answer_text
                    })

                    # Check if completed AFTER saving answer
                    if session.completed:
                        print(f"[SESSION {session_id}] Interview completed after saving answer")
                        await send_end_and_close()
                        break

                    # Try to get NEXT question
                    next_q = session.next_question()
                    
                    if next_q:
                        # Send next question
                        print(f"[SESSION {session_id}] Sending next question")
                        await send_question(next_q)
                    else:
                        # No more questions - end interview
                        print(f"[SESSION {session_id}] No more questions - ending interview")
                        await send_end_and_close()
                        break

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
        
        if socket_open and not end_sent:
            await send_end_and_close()