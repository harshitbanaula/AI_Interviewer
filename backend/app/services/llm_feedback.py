# backend/app/services/llm_feedback.py

import os
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

# HF_TOKEN = os.getenv("HF_TOKEN")
# HF_MODEL_ID = os.getenv("HF_MODEL_ID", "meta-llama/Llama-3.1-8B-Instruct")

# hf_endpoint = HuggingFaceEndpoint(
#     repo_id=HF_MODEL_ID,
#     task="conversational",
#     huggingfacehub_api_token=HF_TOKEN,
#     temperature=0.3,
#     max_new_tokens=400,
# )

# llm = ChatHuggingFace(llm=hf_endpoint)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_ID = os.getenv("GROQ_MODEL_ID")
if not GROQ_API_KEY or not GROQ_MODEL_ID:
    raise ValueError("GROQ_API_KEY and GROQ_MODEL_ID must be set in environment variables.")

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=GROQ_MODEL_ID,
    temperature=0.1,
    max_tokens=250,
)

feedback_prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are a senior technical interviewer providing final interview feedback.

Rules:
- Be honest, constructive, and professional
- If answers are missing, acknowledge it clearly
- Give actionable advice
- Encourage improvement
- Do NOT mention scores numerically in the text unless helpful
"""),
    ("human", """
Interview Summary Data:
{qa_data}

Overall Average Score: {average_score}

Provide:
1. Overall performance summary
2. Key strengths
3. Key improvement areas
4. Final recommendation to the candidate
""")
])

feedback_chain = feedback_prompt | llm | StrOutputParser()


def generate_feedback(qa_list: list, average_score: float) -> str:
    """
    Generate LLM-based interview feedback.
    """

    qa_text = ""
    for idx, qa in enumerate(qa_list, 1):
        qa_text += (
            f"{idx}. Question: {qa['question']}\n"
            f"   Answer: {qa['answer']}\n"
            f"   Final Score: {qa['scores']['final_score']}\n\n"
        )

    feedback = feedback_chain.invoke({
        "qa_data": qa_text,
        "average_score": average_score
    })

    return feedback.strip()
