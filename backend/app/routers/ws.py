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




from fastapi import APIRouter, WebSocket, Query
from app.services.stt import transcribe_chunk
from app.services.interview_state import get_session
# from app.services.llm_feedback import generate_feedback 
import json

router = APIRouter()

@router.websocket("/ws/interview")
async def interview_ws(ws: WebSocket, session_id: str = Query(...)):
    await ws.accept()

    session = get_session(session_id)
    if not session:
        await ws.send_json({"type": "ERROR", "text": "Invalid session"})
        return

    audio_buffer = bytearray()

    # Send first question
    q = session.next_question()
    await ws.send_json({"type": "QUESTION", "text": q})

    try:
        while True:
            msg = await ws.receive()

            # Audio bytes from client
            if msg.get("bytes") and session.expecting_answer:
                audio_buffer.extend(msg["bytes"])

            # Control messages
            if msg.get("text"):
                payload = json.loads(msg["text"])

                if payload.get("text") == "SUBMIT_ANSWER":
                    # Convert audio to text if available
                    text = transcribe_chunk(bytes(audio_buffer)) if audio_buffer else ""
                    audio_buffer.clear()

                    session.save_answer(text)

                    # Send live transcript
                    await ws.send_json({
                        "type": "FINAL_TRANSCRIPT",
                        "text": text if text else "No answer provided"
                    })

                    # Next question or finish
                    next_q = session.next_question()
                    if next_q:
                        await ws.send_json({"type": "QUESTION", "text": next_q})
                    else:
                        summary = session.final_result()
                        await ws.send_json({
                                "type": "END",
                                "text": "Interview completed",
                                "summary": summary
                        })  


    except Exception as e:
        print("WebSocket error:", e)
        await ws.close()
