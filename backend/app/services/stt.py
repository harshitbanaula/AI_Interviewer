# backend/app/services/stt.py

import numpy as np
from faster_whisper import WhisperModel

# Initialize Whisper model once (global, safe)
model = WhisperModel(
    model_size_or_path="small",
    device="cpu",
    compute_type="int8"
)


def transcribe_chunk(audio_buffer: bytes, sample_rate: int = 16000) -> str:

    if not audio_buffer:
        return ""

    try:

        audio_int16 = np.frombuffer(audio_buffer, dtype=np.int16)

        if len(audio_int16) == 0:
            return ""

        # Normalize to float32 (-1.0 to 1.0)
        audio_np = audio_int16.astype(np.float32) / 32768.0

        # Guard: very short chunks create noise
        if len(audio_np) < sample_rate // 2:
            return ""

        # Transcribe
        segments, _ = model.transcribe(
            audio_np,
            language="en",
            beam_size=1,
            vad_filter=True
        )

        text_parts = []
        for segment in segments:
            cleaned = segment.text.strip()
            if cleaned:
                text_parts.append(cleaned)

        return " ".join(text_parts).strip()

    except Exception as e:
        print(f"[STT ERROR] {e}")
        return ""
