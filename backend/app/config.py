from dotenv import load_dotenv
import os

# Load .env variables
load_dotenv()

# Database
DB_URL = os.getenv("DB_URL")

# Hugging Face LLM
HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL_ID = os.getenv("HF_MODEL_ID")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.0))

Groq_API_Key = os.getenv("GROQ_API_KEY")
GROQ_MODEL_ID = os.getenv("GROQ_MODEL_ID")

# TTS
TTS_MODEL = os.getenv("TTS_MODEL")

# Server
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
