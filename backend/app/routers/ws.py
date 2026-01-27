# # from fastapi import APIRouter, WebSocket
# # import json

# # from app.services.audio_buffer import AudioBuffer
# # from app.services.stt import speech_to_text

# # router = APIRouter()

# # @router.websocket("/ws")
# # async def ws_endpoint(ws: WebSocket):
# #     await ws.accept()
# #     buffer = AudioBuffer()

# #     while True:
# #         message = await ws.receive()

# #         # HANDLE DISCONNECT EXPLICITLY
# #         if message["type"] == "websocket.disconnect":
# #             print("WebSocket disconnected cleanly")
# #             break

# #         # Binary audio frames
# #         if message.get("bytes") is not None:
# #             buffer.add(message["bytes"])

# #         # Control messages
# #         if message.get("text") is not None:
# #             data = json.loads(message["text"])

# #             if data.get("type") == "END":
# #                 wav_path = buffer.save()
# #                 transcript = speech_to_text(wav_path)

# #                 await ws.send_text(json.dumps({
# #                     "type": "TRANSCRIPT",
# #                     "text": transcript
# #                 }))

# #                 buffer = AudioBuffer()



# # # backend/app/routers/ws.py
# # from fastapi import APIRouter, WebSocket, WebSocketDisconnect
# # from app.services.stt import transcribe_chunk
# # from app.services.evaluator import get_feedback
# # import asyncio
# # from app.services.interview_state import InterviewSession


# # router = APIRouter()

# # SAMPLE_RATE = 16000
# # CHUNK_SECONDS = 1.5
# # SAMPLES_PER_CHUNK = int(SAMPLE_RATE * CHUNK_SECONDS)
# # BYTES_PER_SAMPLE = 4  # float32
# # BYTES_PER_CHUNK = SAMPLES_PER_CHUNK * BYTES_PER_SAMPLE

# # @router.websocket("/ws")
# # async def ws_endpoint(ws: WebSocket):
# #     await ws.accept()

# #     audio_buffer = bytearray()

    

# #     try:
# #         while True:
# #             message = await ws.receive()

# #             # Client disconnected
# #             if message["type"] == "websocket.disconnect":
# #                 print("WebSocket disconnected")
# #                 break

# #             # Audio bytes received
# #             if message.get("bytes") is not None:
# #                 audio_buffer.extend(message["bytes"])

# #                 if len(audio_buffer) >= BYTES_PER_CHUNK:
# #                     chunk = bytes(audio_buffer)
# #                     audio_buffer.clear()

# #                     text = transcribe_chunk(chunk)
# #                     if text:
# #                         # Send live transcript
# #                         await ws.send_json({
# #                             "type": "PARTIAL_TRANSCRIPT",
# #                             "text": text
# #                         })

# #                         #  Live feedback (only if meaningful)
# #                         if len(text.split()) >= 6:
# #                             feedback = await asyncio.to_thread(
# #                                 get_feedback, text
# #                             )
# #                             if feedback:
# #                                 await ws.send_json({
# #                                     "type": "FEEDBACK",
# #                                     "text": feedback
# #                                 })

# #             # END message from client
# #             if message.get("text") == "END":
# #                 if audio_buffer:
# #                     text = transcribe_chunk(bytes(audio_buffer))
# #                     if text:
# #                         await ws.send_json({
# #                             "type": "FINAL_TRANSCRIPT",
# #                             "text": text
# #                         })

# #                         feedback = await asyncio.to_thread(
# #                             get_feedback, text
# #                         )
# #                         if feedback:
# #                             await ws.send_json({
# #                                 "type": "FEEDBACK",
# #                                 "text": feedback
# #                             })

# #                 audio_buffer.clear()
# #                 break

# #     except WebSocketDisconnect:
# #         print("Client disconnected")

# #     except Exception as e:
# #         print("WebSocket error:", e)

# #     finally:
# #         try:
# #             await ws.close()
# #         except:
# #             pass



# # backend/app/routers/ws.py
# from fastapi import APIRouter, WebSocket, WebSocketDisconnect
# from app.services.stt import transcribe_chunk
# from app.services.evaluator import get_feedback
# from app.services.interview_state import InterviewSession
# import asyncio

# router = APIRouter()

# SAMPLE_RATE = 16000
# CHUNK_SECONDS = 1.5
# SAMPLES_PER_CHUNK = int(SAMPLE_RATE * CHUNK_SECONDS)
# BYTES_PER_SAMPLE = 4  # float32
# BYTES_PER_CHUNK = SAMPLES_PER_CHUNK * BYTES_PER_SAMPLE


# @router.websocket("/ws")
# async def ws_endpoint(ws: WebSocket):
#     await ws.accept()

#     #  Interview session state
#     session = InterviewSession()
#     audio_buffer = bytearray()

#     #  Send first interview question
#     await ws.send_json({
#         "type": "QUESTION",
#         "text": session.get_current_question()
#     })

#     try:
#         while True:
#             message = await ws.receive()

#             #  Client disconnected
#             if message["type"] == "websocket.disconnect":
#                 print("WebSocket disconnected")
#                 break

#             #  Audio chunk received
#             if message.get("bytes") is not None:
#                 audio_buffer.extend(message["bytes"])

#                 if len(audio_buffer) >= BYTES_PER_CHUNK:
#                     chunk = bytes(audio_buffer)
#                     audio_buffer.clear()

#                     text = transcribe_chunk(chunk)
#                     if not text:
#                         continue

#                     #  Live transcript
#                     await ws.send_json({
#                         "type": "PARTIAL_TRANSCRIPT",
#                         "text": text
#                     })

#                     #  Real-time feedback (only meaningful answers)
#                     if len(text.split()) >= 6:
#                         feedback = await asyncio.to_thread(
#                             get_feedback, text
#                         )
#                         if feedback:
#                             await ws.send_json({
#                                 "type": "FEEDBACK",
#                                 "text": feedback
#                             })

#             #  END signal from frontend
#             if message.get("text") == "END":
#                 final_answer = ""

#                 if audio_buffer:
#                     final_answer = transcribe_chunk(bytes(audio_buffer))
#                     audio_buffer.clear()

#                 if final_answer:
#                     #  Final transcript
#                     await ws.send_json({
#                         "type": "FINAL_TRANSCRIPT",
#                         "text": final_answer
#                     })

#                     #  Store answer against question
#                     session.save_answer(final_answer)

#                     #  Final feedback for the answer
#                     feedback = await asyncio.to_thread(
#                         get_feedback, final_answer
#                     )
#                     if feedback:
#                         await ws.send_json({
#                             "type": "FEEDBACK",
#                             "text": feedback
#                         })

#                 # Move to next question
#                 next_question = session.next_question()
#                 if next_question:
#                     await ws.send_json({
#                         "type": "QUESTION",
#                         "text": next_question
#                     })
#                 else:
#                     await ws.send_json({
#                         "type": "INTERVIEW_COMPLETE",
#                         "text": "Interview completed successfully."
#                     })
#                     break

#     except WebSocketDisconnect:
#         print("Client disconnected")

#     except Exception as e:
#         print("WebSocket error:", e)

#     finally:
#         try:
#             await ws.close()
#         except:
#             pass




# from fastapi import APIRouter, WebSocket, WebSocketDisconnect
# from app.services.stt import transcribe_chunk
# from app.services.evaluator import get_feedback
# from app.services.interview_state import get_session
# import asyncio

# router = APIRouter()

# SAMPLE_RATE = 16000
# CHUNK_SECONDS = 1.5
# SAMPLES_PER_CHUNK = int(SAMPLE_RATE * CHUNK_SECONDS)
# BYTES_PER_SAMPLE = 4
# BYTES_PER_CHUNK = SAMPLES_PER_CHUNK * BYTES_PER_SAMPLE

# @router.websocket("/ws/{session_id}")
# async def ws_endpoint(ws: WebSocket, session_id: str):
#     await ws.accept()
#     session = get_session(session_id)
#     if not session:
#         await ws.send_json({"type": "ERROR", "text": "Invalid session"})
#         await ws.close()
#         return

#     audio_buffer = bytearray()
#     # Send first question
#     await ws.send_json({"type": "QUESTION", "text": session.get_current_question()})

#     try:
#         while True:
#             message = await ws.receive()

#             if message["type"] == "websocket.disconnect":
#                 print("WebSocket disconnected")
#                 break

#             if message.get("bytes") is not None:
#                 audio_buffer.extend(message["bytes"])
#                 if len(audio_buffer) >= BYTES_PER_CHUNK:
#                     chunk = bytes(audio_buffer)
#                     audio_buffer.clear()
#                     text = transcribe_chunk(chunk)
#                     if text:
#                         await ws.send_json({"type": "PARTIAL_TRANSCRIPT", "text": text})
#                         if len(text.split()) >= 6:
#                             feedback = await asyncio.to_thread(get_feedback, text)
#                             if feedback:
#                                 await ws.send_json({"type": "FEEDBACK", "text": feedback})

#             if message.get("text") == "END":
#                 if audio_buffer:
#                     text = transcribe_chunk(bytes(audio_buffer))
#                     if text:
#                         await ws.send_json({"type": "FINAL_TRANSCRIPT", "text": text})
#                         feedback = await asyncio.to_thread(get_feedback, text)
#                         if feedback:
#                             await ws.send_json({"type": "FEEDBACK", "text": feedback})
#                 audio_buffer.clear()
#                 await ws.send_json({"type": "END"})
#                 break

#             # Automatically send next question after each final transcript
#             if message.get("text") == "NEXT_QUESTION":
#                 q = session.get_current_question()
#                 await ws.send_json({"type": "QUESTION", "text": q})

#     except WebSocketDisconnect:
#         print("Client disconnected")
#     except Exception as e:
#         print("WebSocket error:", e)
#     finally:
#         try:
#             await ws.close()
#         except:
#             pass



# from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
# from app.services.stt import transcribe_chunk
# from app.services.evaluator import get_feedback
# from app.services.interview_state import get_session
# import asyncio
# import json

# router = APIRouter()

# SAMPLE_RATE = 16000
# CHUNK_SECONDS = 1.5
# SAMPLES_PER_CHUNK = int(SAMPLE_RATE * CHUNK_SECONDS)
# BYTES_PER_SAMPLE = 4
# BYTES_PER_CHUNK = SAMPLES_PER_CHUNK * BYTES_PER_SAMPLE


# @router.websocket("/ws/interview")
# async def interview_ws(ws: WebSocket, session_id: str = Query(...)):
#     await ws.accept()

#     session = get_session(session_id)
#     if not session:
#         await ws.send_json({"type": "ERROR", "text": "Invalid session_id"})
#         return

#     audio_buffer = bytearray()

#     # Send first question
#     question = session.next_question()
#     await ws.send_json({"type": "QUESTION", "text": question})

#     try:
#         while True:
#             message = await ws.receive()

#             # ---------------- DISCONNECT ----------------
#             if message["type"] == "websocket.disconnect":
#                 break

#             # ---------------- AUDIO STREAM ----------------
#             if message.get("bytes"):
#                 audio_buffer.extend(message["bytes"])

#                 if len(audio_buffer) >= BYTES_PER_CHUNK:
#                     chunk = bytes(audio_buffer)
#                     audio_buffer.clear()

#                     text = transcribe_chunk(chunk)
#                     if text:
#                         await ws.send_json({
#                             "type": "PARTIAL_TRANSCRIPT",
#                             "text": text
#                         })

#             # ---------------- CONTROL MESSAGES ----------------
#             if message.get("text"):
#                 try:
#                     payload = json.loads(message["text"])
#                     command = payload.get("text")
#                 except Exception:
#                     continue

#                 # ---------- STOP INTERVIEW ----------
#                 if command == "STOP_INTERVIEW":
#                     await ws.send_json({
#                         "type": "END",
#                         "text": "Interview ended. Thank you for your time!"
#                     })
#                     break

#                 # ---------- SUBMIT ANSWER ----------
#                 if command == "SUBMIT_ANSWER":

#                     # Always finalize transcription
#                     final_text = ""
#                     if audio_buffer:
#                         final_text = transcribe_chunk(bytes(audio_buffer))
#                         audio_buffer.clear()

#                     if not final_text.strip():
#                         await ws.send_json({
#                             "type": "ERROR",
#                             "text": "No answer detected. Please speak before submitting."
#                         })
#                         continue

#                     # Save answer
#                     session.save_answer(final_text)

#                     await ws.send_json({
#                         "type": "FINAL_TRANSCRIPT",
#                         "text": final_text
#                     })

#                     # Feedback ONLY for valid answers
#                     feedback = await asyncio.to_thread(get_feedback, final_text)
#                     if feedback:
#                         await ws.send_json({
#                             "type": "FEEDBACK",
#                             "text": feedback
#                         })

#                     # Next question
#                     next_q = session.next_question()

#                     if next_q:
#                         await ws.send_json({
#                             "type": "QUESTION",
#                             "text": next_q
#                         })
#                     else:
#                         await ws.send_json({
#                             "type": "END",
#                             "text": "Interview completed successfully. You may stop now."
#                         })
#                         break

#     except WebSocketDisconnect:
#         print("WebSocket disconnected")

#     except Exception as e:
#         print("WebSocket error:", e)






from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.services.stt import transcribe_chunk
from app.services.evaluator import get_feedback
from app.services.interview_state import get_session
import asyncio
import json

router = APIRouter()

SAMPLE_RATE = 16000
CHUNK_SECONDS = 1.5
SAMPLES_PER_CHUNK = int(SAMPLE_RATE * CHUNK_SECONDS)
BYTES_PER_SAMPLE = 4
BYTES_PER_CHUNK = SAMPLES_PER_CHUNK * BYTES_PER_SAMPLE


@router.websocket("/ws/interview")
async def interview_ws(ws: WebSocket, session_id: str = Query(...)):
    await ws.accept()

    session = get_session(session_id)
    if not session:
        await ws.send_json({"type": "ERROR", "text": "Invalid session_id"})
        await ws.close()
        return

    audio_buffer = bytearray()
    interview_active = True

    # Send first question
    first_question = session.next_question()
    await ws.send_json({"type": "QUESTION", "text": first_question})

    try:
        while interview_active:
            message = await ws.receive()

            # Client disconnected
            if message["type"] == "websocket.disconnect":
                break

            # 🔊 AUDIO BYTES
            if message.get("bytes"):
                audio_buffer.extend(message["bytes"])

                if len(audio_buffer) >= BYTES_PER_CHUNK:
                    chunk = bytes(audio_buffer)
                    audio_buffer.clear()

                    text = transcribe_chunk(chunk)
                    if text:
                        await ws.send_json({"type": "PARTIAL_TRANSCRIPT", "text": text})

                        if len(text.split()) >= 6:
                            feedback = await asyncio.to_thread(get_feedback, text)
                            if feedback:
                                await ws.send_json({"type": "FEEDBACK", "text": feedback})

            # 🧠 CONTROL MESSAGES (JSON)
            if message.get("text"):
                try:
                    payload = json.loads(message["text"])
                    command = payload.get("text")
                except Exception:
                    continue

                # ❌ STOP INTERVIEW COMPLETELY
                if command == "STOP_INTERVIEW":
                    await ws.send_json({
                        "type": "END",
                        "text": "Interview ended by candidate. Thank you!"
                    })
                    interview_active = False
                    break

                # ✅ SUBMIT ANSWER (button OR silence)
                if command == "SUBMIT_ANSWER":
                    final_text = None

                    if audio_buffer:
                        final_text = transcribe_chunk(bytes(audio_buffer))
                        audio_buffer.clear()

                    if final_text:
                        session.save_answer(final_text)

                        await ws.send_json({
                            "type": "FINAL_TRANSCRIPT",
                            "text": final_text
                        })

                        feedback = await asyncio.to_thread(get_feedback, final_text)
                        if feedback:
                            await ws.send_json({
                                "type": "FEEDBACK",
                                "text": feedback
                            })

                    # 🔁 NEXT QUESTION
                    next_q = session.next_question()
                    if next_q:
                        await ws.send_json({
                            "type": "QUESTION",
                            "text": next_q
                        })
                    else:
                        await ws.send_json({
                            "type": "END",
                            "text": "Interview complete. Thank you!"
                        })
                        interview_active = False
                        break

    except WebSocketDisconnect:
        print("WebSocket disconnected")

    except Exception as e:
        print("WebSocket error:", e)

    finally:
        if ws.client_state.name != "DISCONNECTED":
            await ws.close()
