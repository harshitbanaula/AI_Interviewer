




# backend/app/services/evaluator.py
import os
import json
from dotenv import load_dotenv
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_ID = os.getenv("GROQ_MODEL_ID", "llama-3.1-8b-instant")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY missing")

# ----------------------------
# LLM (Advisory Only)
# ----------------------------
llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=GROQ_MODEL_ID,
    temperature=0.1,
    max_tokens=250,
)

# HF_TOKEN = os.getenv("HF_TOKEN")
# HF_MODEL_ID = os.getenv("HF_MODEL_ID")
# if not HF_TOKEN:
#     raise RuntimeError("HF_TOKEN missing")

# hf_endpoint = HuggingFaceEndpoint(
#     repo_id=HF_MODEL_ID,
#     task="conversational",
#     huggingfacehub_api_token=HF_TOKEN,
#     temperature=0.3,
#     max_new_tokens=400,
# )

# llm = ChatHuggingFace(llm=hf_endpoint)


# ----------------------------
# Prompt
# ----------------------------
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an AI interviewer. Suggest evaluation as JSON only."),
    ("human", """
Evaluate this answer and suggest:

{
  "strengths": ["..."],
  "improvements": ["..."]
}

Answer:
{answer_text}
""")
])

chain = prompt | llm | StrOutputParser()

# ----------------------------
# Backend Scoring (FINAL AUTHORITY)
# ----------------------------
WEIGHTS = {
    "correctness": 0.5,
    "depth": 0.3,
    "clarity": 0.2
}

def score_answer(answer_text: str) -> dict:
    """
    Backend-controlled scoring.
    LLM is advisory for feedback only.
    """

    words = len(answer_text.split())

    correctness = min(words / 50, 1.0)
    depth = min(words / 80, 1.0)
    clarity = 1.0 if words <= 100 else max(0.5, 100 / words)

    final_score = round(
        correctness * WEIGHTS["correctness"] +
        depth * WEIGHTS["depth"] +
        clarity * WEIGHTS["clarity"],
        2
    )

    # LLM advisory feedback
    try:
        raw = chain.invoke({"answer_text": answer_text})
        advisory = json.loads(raw)
    except Exception:
        advisory = {"strengths": [], "improvements": []}

    return {
        "correctness": round(correctness, 2),
        "depth": round(depth, 2),
        "clarity": round(clarity, 2),
        "final_score": final_score,
        "strengths": advisory.get("strengths", []),
        "improvements": advisory.get("improvements", [])
    }
