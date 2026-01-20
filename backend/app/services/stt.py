from faster_whisper import WhisperModel

model = WhisperModel(
    "medium",
    device="cpu",
    compute_type="int8"
)

def speech_to_text(wav_path: str) -> str:
    segments, _ = model.transcribe(wav_path)
    return " ".join(segment.text for segment in segments).strip()
