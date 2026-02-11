




# # backend/app/services/evaluator.py
# import os
# import json
# from dotenv import load_dotenv
# from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import StrOutputParser
# from langchain_groq import ChatGroq
# load_dotenv()

# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# GROQ_MODEL_ID = os.getenv("GROQ_MODEL_ID", "llama-3.1-8b-instant")

# if not GROQ_API_KEY:
#     raise RuntimeError("GROQ_API_KEY missing")

# # ----------------------------
# # LLM (Advisory Only)
# # ----------------------------
# llm = ChatGroq(
#     api_key=GROQ_API_KEY,
#     model=GROQ_MODEL_ID,
#     temperature=0.1,
#     max_tokens=250,
# )

# # HF_TOKEN = os.getenv("HF_TOKEN")
# # HF_MODEL_ID = os.getenv("HF_MODEL_ID")
# # if not HF_TOKEN:
# #     raise RuntimeError("HF_TOKEN missing")

# # hf_endpoint = HuggingFaceEndpoint(
# #     repo_id=HF_MODEL_ID,
# #     task="conversational",
# #     huggingfacehub_api_token=HF_TOKEN,
# #     temperature=0.3,
# #     max_new_tokens=400,
# # )

# # llm = ChatHuggingFace(llm=hf_endpoint)


# # ----------------------------
# # Prompt
# # ----------------------------
# prompt = ChatPromptTemplate.from_messages([
#     ("system", "You are an AI interviewer. Suggest evaluation as JSON only."),
#     ("human", """
# Evaluate this answer and suggest:

# {
#   "strengths": ["..."],
#   "improvements": ["..."]
# }

# Answer:
# {answer_text}
# """)
# ])

# chain = prompt | llm | StrOutputParser()

# # ----------------------------
# # Backend Scoring (FINAL AUTHORITY)
# # ----------------------------
# WEIGHTS = {
#     "correctness": 0.5,
#     "depth": 0.3,
#     "clarity": 0.2
# }

# def score_answer(answer_text: str) -> dict:

#     words = len(answer_text.split())

#     correctness = min(words / 50, 1.0)
#     depth = min(words / 80, 1.0)
#     clarity = 1.0 if words <= 100 else max(0.5, 100 / words)

#     final_score = round(
#         correctness * WEIGHTS["correctness"] +
#         depth * WEIGHTS["depth"] +
#         clarity * WEIGHTS["clarity"],
#         2
#     )

#     # LLM advisory feedback
#     try:
#         raw = chain.invoke({"answer_text": answer_text})
#         advisory = json.loads(raw)
#     except Exception:
#         advisory = {"strengths": [], "improvements": []}

#     return {
#         "correctness": round(correctness, 2),
#         "depth": round(depth, 2),
#         "clarity": round(clarity, 2),
#         "final_score": final_score,
#         "strengths": advisory.get("strengths", []),
#         "improvements": advisory.get("improvements", [])
#     }

# backend/app/services/evaluator.py

import os
import json
from typing import Dict, Optional
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

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
    max_tokens=350,
)



# ----------------------------
# LLM PROMPT
# ----------------------------
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an expert technical interviewer. "
        "Evaluate the answer strictly and return JSON only."
    ),
    (
        "human",
        """
Question:
{question}

Answer:
{answer}

Evaluate on:
- semantic_correctness: Does the answer actually address the question?
- reasoning_quality: Is the logic clear and well explained?
- clarity: Is the answer structured and understandable?

Return JSON ONLY:
{{
  "semantic_correctness": number between 0 and 1,
  "reasoning_quality": number between 0 and 1,
  "clarity": number between 0 and 1,
  "strengths": ["short bullet points"],
  "improvements": ["short bullet points"]
}}
"""
    )
])

chain = prompt | llm | StrOutputParser()

# ----------------------------
# BACKEND SCORING WEIGHTS
# ----------------------------
WEIGHTS = {
    "length_correctness": 0.3,
    "semantic_correctness": 0.4,
    "reasoning_quality": 0.3
}

# ----------------------------
# MAIN EVALUATOR
# ----------------------------
def score_answer(answer_text: str, question: str) -> Dict:


    answer_text = answer_text.strip()
    if not answer_text or answer_text.lower() in ("no answer", "no answer provided"):
        return {
            "length_correctness": 0.0,
            "semantic_correctness": 0.0,
            "reasoning_quality": 0.0,
            "final_score": 0.0,
            "strengths": [],
            "improvements": ["Answer was not provided."]
        }

    # ----------------------------
    # Backend basic metric
    # ----------------------------
    words = len(answer_text.split())
    length_correctness = min(words / 60, 1.0)

    # Defaults
    semantic_correctness = 0.5
    reasoning_quality = 0.5
    clarity = 0.5
    strengths = []
    improvements = []

    # ----------------------------
    # LLM Evaluation
    # ----------------------------
    try:
        raw = chain.invoke({
            "question": question,
            "answer": answer_text
        })
        parsed = json.loads(raw)

        semantic_correctness = float(parsed.get("semantic_correctness", 0.5))
        reasoning_quality = float(parsed.get("reasoning_quality", 0.5))
        clarity = float(parsed.get("clarity", 0.5))
        strengths = parsed.get("strengths", [])
        improvements = parsed.get("improvements", [])

    except Exception:
        # fallback safe values
        semantic_correctness = 0.5
        reasoning_quality = 0.5
        clarity = 0.5

    # ----------------------------
    # Final score (weighted)
    # ----------------------------
    final_score = round(
        length_correctness * WEIGHTS["length_correctness"]
        + semantic_correctness * WEIGHTS["semantic_correctness"]
        + reasoning_quality * WEIGHTS["reasoning_quality"],
        2
    )


    return {
        "length_correctness": round(length_correctness, 2),
        "semantic_correctness": round(semantic_correctness, 2),
        "reasoning_quality": round(reasoning_quality, 2),
        "clarity": round(clarity, 2),
        "final_score": final_score,
        "strengths": strengths,
        "improvements": improvements
    }
