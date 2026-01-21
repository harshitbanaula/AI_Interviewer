import wave
import uuid
import os

RECORDINGS_DIR = "recordings"
os.makedirs(RECORDINGS_DIR, exist_ok=True)

class AudioBuffer:
    def __init__(self):
        self.frames = []
    
    def reset(self):
        self.frames = []

    def add(self, chunk: bytes):
        self.frames.append(chunk)

    def save(self, sample_rate=16000):
        filename = f"{uuid.uuid4()}.wav"
        path = os.path.join(RECORDINGS_DIR, filename)

        with wave.open(path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(b"".join(self.frames))

        return path
