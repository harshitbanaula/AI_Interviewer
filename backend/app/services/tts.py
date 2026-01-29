# # backend/app/services/tts.py

# import torch
# from transformers import VitsModel, AutoTokenizer
# import io
# import scipy.io.wavfile
# from typing import Optional
# import numpy as np

# # Load model once when the service starts
# MODEL_NAME = "kakao-enterprise/vits-vctk"
# DEVICE = "cpu"

# model = VitsModel.from_pretrained(MODEL_NAME).to(DEVICE)
# tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)


# def synthesize_speech(text: str, speaker_id: int = 0) -> Optional[bytes]:
#     """
#     Generate WAV bytes from text using Kakao VITS
#     """
#     if not text.strip():
#         return None

#     try:
#         # Tokenize
#         inputs = tokenizer(text, return_tensors="pt").to(DEVICE)

#         with torch.no_grad():
#             # Generate waveform
#             output = model(**inputs, speaker_id=speaker_id).waveform[0]  # shape: [num_samples]

#         # Convert float tensor [-1,1] → int16 PCM
#         audio_np = output.cpu().numpy()
#         audio_np = np.clip(audio_np, -1.0, 1.0)
#         pcm16 = (audio_np * 32767).astype(np.int16)

#         # Save WAV to in-memory bytes
#         byte_io = io.BytesIO()
#         scipy.io.wavfile.write(byte_io, model.config.sampling_rate, pcm16)
#         return byte_io.getvalue()

#     except Exception as e:
#         print("Local TTS error:", e)
#         return None



# backend/app/services/tts.py

import torch
from transformers import VitsModel, AutoTokenizer
import io
import scipy.io.wavfile
from typing import Optional
import numpy as np
from scipy.signal import resample  # for speed adjustment

# Load model once when the service starts
MODEL_NAME = "kakao-enterprise/vits-vctk"
DEVICE = "cpu"

model = VitsModel.from_pretrained(MODEL_NAME).to(DEVICE)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)


def synthesize_speech(text: str, speaker_id: int = 0, speed: float = 1.0) -> Optional[bytes]:
    """
    Generate WAV bytes from text using Kakao VITS with adjustable speed.
    
    Args:
        text (str): Text to synthesize
        speaker_id (int): Speaker ID (0-108)
        speed (float): Playback speed. <1.0 = slower, >1.0 = faster. Default 1.0
    Returns:
        bytes: WAV audio bytes
    """
    if not text.strip():
        return None

    try:
        # Tokenize input text
        inputs = tokenizer(text, return_tensors="pt").to(DEVICE)

        with torch.no_grad():
            output = model(**inputs, speaker_id=speaker_id).waveform[0]  # [num_samples]

        # Convert to numpy
        audio_np = output.cpu().numpy()
        audio_np = np.clip(audio_np, -1.0, 1.0)

        # Adjust speed if needed
        if speed != 1.0:
            num_samples = int(len(audio_np) / speed)
            audio_np = resample(audio_np, num_samples)

        # Convert float [-1,1] → int16 PCM
        pcm16 = (audio_np * 32767).astype(np.int16)

        # Save to WAV bytes
        byte_io = io.BytesIO()
        scipy.io.wavfile.write(byte_io, model.config.sampling_rate, pcm16)
        return byte_io.getvalue()

    except Exception as e:
        print("Local TTS error:", e)
        return None
