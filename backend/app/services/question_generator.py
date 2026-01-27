
# import os
# from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import StrOutputParser

# HF_TOKEN = os.getenv("HF_TOKEN")
# HF_MODEL_ID = os.getenv("HF_MODEL_ID", "mistralai/Mistral-7B-Instruct-v0.2")

# hf_endpoint = HuggingFaceEndpoint(
#     repo_id=HF_MODEL_ID,
#     task="conversational",
#     huggingfacehub_api_token=HF_TOKEN,
#     temperature=0.2,
#     max_new_tokens=400,
# )

# llm = ChatHuggingFace(llm=hf_endpoint)

# question_prompt = ChatPromptTemplate.from_messages([
#     (
#         "system",
#         """
# You are a senior technical interviewer at a top product company.

# Your task:
# - Generate interview questions based on Job Description and Candidate Resume
# - Ask clear, professional, non-repetitive questions
# - Focus on real-world skills, projects, and decision-making
# - One question at a time, no answers
# - Interview structure:
#   1. Introduction
#   2. Resume-based technical & project questions
#   3. Skill deep-dive questions
#   4. HR questions at the end
# Tone: Professional, interview-ready
# """
#     ),
#     (
#         "human",
#         """
# Job Description:
# {job_description}

# Candidate Resume:
# {resume}

# Interview Stage:
# {stage}

# Generate the next best interview question.
# """
#     )
# ])

# question_chain = question_prompt | llm | StrOutputParser()

# def generate_question(job_description: str, resume: str, stage: str) -> str:
#     return question_chain.invoke({
#         "job_description": job_description,
#         "resume": resume,
#         "stage": stage
#     })





import os
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser



HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL_ID = os.getenv("HF_MODEL_ID", "mistralai/Mistral-7B-Instruct-v0.2")

hf_endpoint = HuggingFaceEndpoint(
    repo_id=HF_MODEL_ID,
    task="conversational",
    huggingfacehub_api_token=HF_TOKEN,
    temperature=0.2,
    max_new_tokens=400,
)

llm = ChatHuggingFace(llm=hf_endpoint)

question_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are a senior technical interviewer.

Your task:
- Generate interview questions based on Job Description and Candidate Resume
- Ask clear, professional, non-repetitive questions
- Focus on real-world skills and projects
- One question at a time
- Do NOT include answers

Interview flow:
1. Introduction (1 question)
2. Resume-based technical & project questions
3. Deep dive skills
4. HR / Behavioral questions

Tone:
Professional, clear, interview-ready.
"""
    ),
    (
        "human",
        """
Job Description:
{job_description}

Candidate Resume:
{resume}

Interview Stage:
{stage}

Generate the next best interview question.
"""
    )
])

question_chain = question_prompt | llm | StrOutputParser()

def generate_question(job_description: str, resume: str, stage: str) -> str:
    return question_chain.invoke({
        "job_description": job_description,
        "resume": resume,
        "stage": stage
    })
