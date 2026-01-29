# from faster_whisper import WhisperModel

# model = WhisperModel(
#     "medium",
#     device="cpu",
#     compute_type="int8"
# )

# def speech_to_text(wav_path: str) -> str:
#     segments, _ = model.transcribe(wav_path)
#     return " ".join(segment.text for segment in segments).strip()



# backend/app/services/stt.py
import numpy as np
from faster_whisper import WhisperModel

# Initialize the Whisper model 
model = WhisperModel(
    model_size_or_path="small",
    device="cpu",
    compute_type="int8"
)

def transcribe_chunk(audio_buffer: bytes, sample_rate: int = 16000) -> str:
    """
    Transcribes a short audio chunk (~1–2 seconds)
    Returns partial transcript
    """

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
