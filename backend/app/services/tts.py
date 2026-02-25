# # backend/app/services/tts.py

# import torch
# from transformers import VitsModel, AutoTokenizer
# import io
# import scipy.io.wavfile
# from typing import Optional, List
# import numpy as np
# from scipy.signal import resample
# import re

# MODEL_NAME = "kakao-enterprise/vits-vctk"
# DEVICE = "cpu"

# print("🔊 Loading TTS model...")
# model = VitsModel.from_pretrained(MODEL_NAME).to(DEVICE)
# tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
# model.eval()
# print(" TTS model loaded")


# def normalize_text(text) -> str:
#     if isinstance(text, (list, tuple)):
#         text = " ".join(str(x) for x in text)
#     return str(text).strip()


# def split_text_for_tts(text: str, max_chars: int = 200) -> List[str]:
#     """
#     VITS-safe sentence chunking.
#     Splits by punctuation and ensures no chunk exceeds max_chars
#     to prevent tokenizer truncation.
#     """
#     # 1. Replace newlines with spaces to avoid treating them as hard breaks or ignoring them
#     text = text.replace('\n', ' ')
    
#     # 2. Treat colons and semicolons as soft sentence breaks for better flow
#     text = text.replace(':', '.')
#     text = text.replace(';', '.')

#     # 3. Split by standard sentence terminators
#     # This keeps the punctuation with the preceding sentence
#     raw_sentences = re.split(r'(?<=[.!?])\s+', text)
    
#     processed_sentences = []
    
#     for s in raw_sentences:
#         s = s.strip()
#         if not s: 
#             continue
        
#         # 4. If a sentence is still too long (e.g. run-on sentence without punctuation),
#         # force split it by commas or spaces
#         if len(s) > max_chars:
#             # Try splitting by commas first
#             comma_parts = re.split(r'(?<=,)\s+', s)
#             current_part = ""
#             for part in comma_parts:
#                 if len(current_part) + len(part) < max_chars:
#                     current_part = f"{current_part} {part}".strip()
#                 else:
#                     if current_part:
#                         processed_sentences.append(current_part)
#                     current_part = part
#             if current_part:
#                 processed_sentences.append(current_part)
#         else:
#             processed_sentences.append(s)

#     # 5. Group short sentences back together to form optimal chunks
#     chunks = []
#     current_chunk = ""

#     for s in processed_sentences:
#         # Check if adding this sentence exceeds the limit
#         if len(current_chunk) + len(s) + 1 <= max_chars:
#             current_chunk = f"{current_chunk} {s}".strip()
#         else:
#             if current_chunk:
#                 chunks.append(current_chunk)
#             # If s itself is larger than max_chars (fallback from step 4 logic edge cases),
#             # it will be its own chunk (or already split)
#             current_chunk = s

#     if current_chunk:
#         chunks.append(current_chunk)

#     return chunks

# def synthesize_speech(
#     text: str,
#     speaker_id: int = 0,
#     speed: float = 1.0
# ) -> Optional[bytes]:

#     text = normalize_text(text)
#     if not text:
#         return None

#     try:
#         # Reduced max_chars to be safe with tokenizer limit (max_length=256 tokens)
#         chunks = split_text_for_tts(text, max_chars=180)
#         audio_segments = []

#         for chunk in chunks:
#             inputs = tokenizer(
#                 chunk,
#                 return_tensors="pt",
#                 padding=False,
#                 truncation=True,
#                 max_length=500
#             )

#             inputs = {k: v.to(DEVICE) for k, v in inputs.items()}

#             with torch.no_grad():
#                 output = model(**inputs, speaker_id=speaker_id)
#                 waveform = output.waveform.squeeze(0)

#             audio_np = waveform.cpu().numpy()
#             audio_np = np.clip(audio_np, -1.0, 1.0)
#             audio_segments.append(audio_np)
            
#             # Add a small silence between chunks (0.2s) for better pacing
#             silence = np.zeros(int(model.config.sampling_rate * 0.2))
#             audio_segments.append(silence)

#         if not audio_segments:
#             return None

#         audio_np = np.concatenate(audio_segments)

#         # Speed control
#         if speed != 1.0:
#             new_len = int(len(audio_np) / speed)
#             audio_np = resample(audio_np, new_len)

#         pcm16 = (audio_np * 32767).astype(np.int16)

#         buf = io.BytesIO()
#         scipy.io.wavfile.write(
#             buf,
#             model.config.sampling_rate,
#             pcm16
#         )

#         return buf.getvalue()

#     except Exception as e:
#         print(f"Local TTS error: {e}")
#         return None




# backend/app/services/tts.py
# Replaced slow local VITS model (~9s) with edge-tts (~0.5s)
# edge-tts is free, uses Microsoft Azure voices, no API key needed

import asyncio
import io
import edge_tts

VOICE = "en-US-GuyNeural"   # Male, clear, professional
RATE  = "-10%"               # Slightly slower for interview clarity

async def _synthesize_async(text: str) -> bytes:
    communicate = edge_tts.Communicate(text, voice=VOICE, rate=RATE)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data


def synthesize_speech(text: str, speaker_id: int = 0, speed: float = 1.0) -> bytes:
    if not text or not text.strip():
        return None
    try:
        # Worker threads don't have an event loop — create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_synthesize_async(text))
            return result if result else None
        finally:
            loop.close()
    except Exception as e:
        print(f"[TTS ERROR] {e}")
        return None