from fastapi import APIRouter, WebSocket
import json

from app.services.audio_buffer import AudioBuffer
from app.services.stt import speech_to_text

router = APIRouter()

@router.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    buffer = AudioBuffer()

    while True:
        message = await ws.receive()

        # HANDLE DISCONNECT EXPLICITLY
        if message["type"] == "websocket.disconnect":
            print("WebSocket disconnected cleanly")
            break

        # Binary audio frames
        if message.get("bytes") is not None:
            buffer.add(message["bytes"])

        # Control messages
        if message.get("text") is not None:
            data = json.loads(message["text"])

            if data.get("type") == "END":
                wav_path = buffer.save()
                transcript = speech_to_text(wav_path)

                await ws.send_text(json.dumps({
                    "type": "TRANSCRIPT",
                    "text": transcript
                }))

                buffer = AudioBuffer()
