# backend/app/services/audio_storage.py

import os
import wave

# Root directory for recordings
RECORDINGS_ROOT = "recordings"

def save_candidate_audio(session_id: str, question_index: int, audio_data: bytes, sample_rate: int = 16000):
    try:
        if not audio_data:
            return None

        # 1. Create the session-specific folder
        session_dir = os.path.join(RECORDINGS_ROOT, session_id)
        os.makedirs(session_dir, exist_ok=True)

        # 2. Define the filename (e.g., question_1.wav)
        filename = f"question_{question_index}.wav"
        filepath = os.path.join(session_dir, filename)

        # 3. Write the WAV file
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(1)       # Mono
            wf.setsampwidth(2)       # 2 bytes per sample (16-bit PCM)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data)

        print(f" Audio saved: {filepath}")
        return filepath

    except Exception as e:
        print(f" Error saving audio file: {e}")
        return None