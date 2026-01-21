# from fastapi import APIRouter, WebSocket
# import json

# from app.services.audio_buffer import AudioBuffer
# from app.services.stt import speech_to_text

# router = APIRouter()

# @router.websocket("/ws")
# async def ws_endpoint(ws: WebSocket):
#     await ws.accept()
#     buffer = AudioBuffer()

#     while True:
#         message = await ws.receive()

#         # HANDLE DISCONNECT EXPLICITLY
#         if message["type"] == "websocket.disconnect":
#             print("WebSocket disconnected cleanly")
#             break

#         # Binary audio frames
#         if message.get("bytes") is not None:
#             buffer.add(message["bytes"])

#         # Control messages
#         if message.get("text") is not None:
#             data = json.loads(message["text"])

#             if data.get("type") == "END":
#                 wav_path = buffer.save()
#                 transcript = speech_to_text(wav_path)

#                 await ws.send_text(json.dumps({
#                     "type": "TRANSCRIPT",
#                     "text": transcript
#                 }))

#                 buffer = AudioBuffer()



# from fastapi import APIRouter, WebSocket, WebSocketDisconnect
# from app.services.stt import transcribe_chunk

# router = APIRouter()

# SAMPLE_RATE = 16000
# CHUNK_SECONDS = 1.5
# SAMPLES_PER_CHUNK = int(SAMPLE_RATE * CHUNK_SECONDS)
# BYTES_PER_SAMPLE = 4  # float32
# BYTES_PER_CHUNK = SAMPLES_PER_CHUNK * BYTES_PER_SAMPLE


# @router.websocket("/ws")
# async def ws_endpoint(ws: WebSocket):
#     await ws.accept()
#     audio_buffer = bytearray()
#     disconnected = False

#     try:
#         while True:
#             message = await ws.receive()

#             # Client disconnected
#             if message["type"] == "websocket.disconnect":
#                 print("WebSocket disconnected cleanly")
#                 disconnected = True
#                 break

#             # Audio frame
#             if message.get("bytes") is not None:
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

#             # Control messages (END, etc.)
#             if message.get("text") is not None:
#                 data = message["text"]

#                 if data == "END":
#                     if audio_buffer:
#                         text = transcribe_chunk(bytes(audio_buffer),language="en")
#                         if text:
#                             await ws.send_json({
#                                 "type": "FINAL_TRANSCRIPT",
#                                 "text": text
#                             })
#                         audio_buffer.clear()
#                     disconnected = True
#                     break

#     except WebSocketDisconnect:
#         print("Client disconnected unexpectedly")
#         disconnected = True

#     except Exception as e:
#         print("WebSocket error:", e)
#         disconnected = True

#     finally:
#         # Only try to close if not already disconnected
#         if not disconnected:
#             try:
#                 await ws.close()
#             except Exception:
#                 pass




# backend/app/routers/ws.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.stt import transcribe_chunk
from app.services.evaluator import get_feedback
import asyncio

router = APIRouter()

SAMPLE_RATE = 16000
CHUNK_SECONDS = 1.5
SAMPLES_PER_CHUNK = int(SAMPLE_RATE * CHUNK_SECONDS)
BYTES_PER_SAMPLE = 4  # float32
BYTES_PER_CHUNK = SAMPLES_PER_CHUNK * BYTES_PER_SAMPLE

@router.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    audio_buffer = bytearray()

    try:
        while True:
            message = await ws.receive()

            # Client disconnected
            if message["type"] == "websocket.disconnect":
                print("WebSocket disconnected")
                break

            # Audio bytes received
            if message.get("bytes") is not None:
                audio_buffer.extend(message["bytes"])

                if len(audio_buffer) >= BYTES_PER_CHUNK:
                    chunk = bytes(audio_buffer)
                    audio_buffer.clear()

                    text = transcribe_chunk(chunk)
                    if text:
                        # Send live transcript
                        await ws.send_json({
                            "type": "PARTIAL_TRANSCRIPT",
                            "text": text
                        })

                        #  Live feedback (only if meaningful)
                        if len(text.split()) >= 6:
                            feedback = await asyncio.to_thread(
                                get_feedback, text
                            )
                            if feedback:
                                await ws.send_json({
                                    "type": "FEEDBACK",
                                    "text": feedback
                                })

            # END message from client
            if message.get("text") == "END":
                if audio_buffer:
                    text = transcribe_chunk(bytes(audio_buffer))
                    if text:
                        await ws.send_json({
                            "type": "FINAL_TRANSCRIPT",
                            "text": text
                        })

                        feedback = await asyncio.to_thread(
                            get_feedback, text
                        )
                        if feedback:
                            await ws.send_json({
                                "type": "FEEDBACK",
                                "text": feedback
                            })

                audio_buffer.clear()
                break

    except WebSocketDisconnect:
        print("Client disconnected")

    except Exception as e:
        print("WebSocket error:", e)

    finally:
        try:
            await ws.close()
        except:
            pass
