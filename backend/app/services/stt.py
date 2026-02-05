
# backend/app/services/stt.py
import numpy as np
from faster_whisper import WhisperModel

# Initialize the Whisper model 
model = WhisperModel(
    model_size_or_path="small",
    device="cpu",
    compute_type="int8"
)


# Transcribes a short audio chunk (~1–2 seconds) Returns partial transcript

def transcribe_chunk(audio_buffer: bytes, sample_rate: int = 16000) -> str:
    

    if not audio_buffer:
        return ""

    # Convert bytes → float32 numpy array
    audio_np = np.frombuffer(audio_buffer, dtype=np.float32)

    if len(audio_np) < sample_rate:
        return ""

    segments, _ = model.transcribe(
        audio_np,
        language="en",
        beam_size=1,
        vad_filter=True
    )

    text = ""
    for segment in segments:
        text += segment.text.strip() + " "

    return text.strip()

