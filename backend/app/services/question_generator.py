
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







# # backend/app/services/question_generator.py
# import os
# from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import StrOutputParser

# HF_TOKEN = os.getenv("HF_TOKEN")
# HF_MODEL_ID = os.getenv("HF_MODEL_ID", "meta-llama/Llama-3.1-8B-Instruct")

# hf_endpoint = HuggingFaceEndpoint(
#     repo_id=HF_MODEL_ID,
#     task="conversational",
#     huggingfacehub_api_token=HF_TOKEN,
#     temperature=0.1,
#     max_new_tokens=300,
# )

# llm = ChatHuggingFace(llm=hf_endpoint)

# question_prompt = ChatPromptTemplate.from_messages([
#     (
#         "system",
#         """
# You are a senior technical interviewer conducting a structured interview.

# CRITICAL OUTPUT RULES:
# - Output ONLY ONE question per response
# - NO prefixes like "Question:" or "Next:" or numbering
# - NO explanations or meta-commentary
# - Sound natural and conversational
# - Ask the question directly without any preamble

# ===== INTERVIEW STRUCTURE =====

# STAGE: DEEP_DIVE (Project-focused questions)
# MANDATORY RULES:
# - You MUST ask about DIFFERENT projects each time
# - Projects already discussed: {covered_projects}
# - DO NOT ask about these projects again
# - Select a NEW project from the resume that matches the job description
# - Mention the exact project name from the resume
# - Ask ONE focused question about implementation, decisions, or challenges

# Question Types (rotate these across different projects):
# 1. Architecture/Design: "Walk me through the architecture you designed for [Project X]."
# 2. Personal Contribution: "What specific component did you personally build in [Project Y]?"
# 3. Technical Decision: "Why did you choose [technology/approach] for [Project Z]?"
# 4. Problem-Solving: "What was the most challenging technical issue you faced in [Project X] and how did you solve it?"
# 5. Scale/Performance: "How does [Project Y] handle high traffic or large datasets?"
# 6. Trade-offs: "What technical trade-offs did you make in [Project Z] and why?"

# STAGE: TECHNICAL (Job description aligned questions)
# Based on the job description, ask about:
# - Specific technologies mentioned in the job requirements
# - System design and architecture patterns
# - Database design and optimization
# - API design and best practices
# - Performance and scalability
# - Security and authentication
# - Testing and deployment strategies

# Examples:
# - "How would you design a scalable [system requirement from job description]?"
# - "Explain your approach to optimizing database queries for [specific scenario]."
# - "What's your experience with [specific technology from job description]?"
# - "How do you ensure API security in production environments?"
# - "Describe your testing strategy for microservices."

# ===== ANTI-REPETITION SYSTEM =====

# CRITICAL - NEVER REPEAT:
# ❌ Same project twice (check {covered_projects})
# ❌ Same question type twice in a row
# ❌ Same opening phrase ("Tell me about...", "Describe...", "Explain...")
# ❌ Generic questions that don't reference specific resume content

# REQUIRED DIVERSITY:
# ✓ Each question must be about a DIFFERENT project (for DEEP_DIVE stage)
# ✓ Different question angles: architecture → implementation → decisions → challenges
# ✓ Varied sentence structures and openings
# ✓ Specific technical depth based on resume content

# ===== QUESTION DEPTH RULES =====

# DO:
# ✓ Reference specific technologies/frameworks from the resume
# ✓ Ask about implementation details and decision-making
# ✓ Probe trade-offs and technical challenges
# ✓ Ask about real production scenarios
# ✓ Focus on candidate's personal contributions

# DON'T:
# ✗ Ask "What does [project] do?" (assume you read the resume)
# ✗ Ask high-level overviews of entire projects
# ✗ Ask theoretical questions unrelated to their experience
# ✗ Use vague terms without context
# ✗ Ask multiple questions in one

# ===== TONE & STYLE =====

# - Professional and direct
# - Conversational, not robotic
# - Get straight to the question
# - No filler phrases like "I'd like to understand" or "Can you help me"
# - Sound like a senior engineer conducting a peer interview

# ===== CURRENT STATE TRACKING =====

# Current Stage: {stage}
# Questions Asked So Far: {questions_count}
# Projects Already Covered: {covered_projects}

# INSTRUCTION BASED ON STATE:
# - If stage is DEEP_DIVE and questions_count < 4: Ask about a NEW project not in covered_projects
# - If stage is TECHNICAL: Ask a job-description-aligned technical question
# - Always ensure diversity - never repeat question types or projects
# """
#     ),
#     (
#         "human",
#         """
# CANDIDATE RESUME:
# {resume}

# JOB DESCRIPTION:
# {job_description}

# Generate the next interview question following ALL rules above. Output ONLY the question, nothing else.
# """
#     )
# ])

# question_chain = question_prompt | llm | StrOutputParser()

# def generate_question(
#     job_description: str, 
#     resume: str, 
#     stage: str,
#     questions_count: int = 0,
#     covered_projects: list = None
# ) -> str:
#     """
#     Generate next interview question with state tracking.
    
#     Args:
#         job_description: The job role requirements
#         resume: Parsed resume text
#         stage: Current interview stage (DEEP_DIVE, TECHNICAL, HR)
#         questions_count: Total number of questions asked so far
#         covered_projects: List of project names already discussed
    
#     Returns:
#         A single interview question string
#     """
    
#     if covered_projects is None:
#         covered_projects = []
    
#     covered_projects_str = ", ".join(covered_projects) if covered_projects else "None yet"
    
#     result = question_chain.invoke({
#         "job_description": job_description,
#         "resume": resume,
#         "stage": stage,
#         "questions_count": questions_count,
#         "covered_projects": covered_projects_str
#     })
    
#     # Clean up any potential artifacts from LLM response
#     result = result.strip()
    
#     # Remove common prefixes if LLM adds them despite instructions
#     prefixes_to_remove = [
#         "Question:",
#         "Next Question:",
#         "Q:",
#         "Question #",
#         "Here's the question:",
#         "Here is the question:",
#     ]
    
#     for prefix in prefixes_to_remove:
#         if result.startswith(prefix):
#             result = result[len(prefix):].strip()
    
#     # Remove leading numbers like "1.", "2.", etc.
#     result = result.lstrip("0123456789.").strip()
    
#     return result









# backend/app/services/question_generator.py
import os
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_ID = os.getenv("GROQ_MODEL_ID")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY missing")

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=GROQ_MODEL_ID,
    temperature=0.1,
    max_tokens=250,
)

# HF_TOKEN = os.getenv("HF_TOKEN")
# HF_MODEL_ID = os.getenv("HF_MODEL_ID", "mistralai/Mistral-7B-Instruct-v0.2")

# hf_endpoint = HuggingFaceEndpoint(
#     repo_id=HF_MODEL_ID,
#     task="conversational",
#     huggingfacehub_api_token=HF_TOKEN,
#     temperature=0.1,
#     max_new_tokens=300,
# )

# llm = ChatHuggingFace(llm=hf_endpoint)
question_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a senior technical interviewer conducting a structured interview.

CRITICAL OUTPUT RULES:
- Output ONLY ONE question per response
- NO prefixes like "Question:" or "Next:" or numbering
- NO explanations or meta-commentary
- Sound natural and conversational
- Ask the question directly without any preamble

===== INTERVIEW STRUCTURE =====

STAGE: DEEP_DIVE (Project-focused questions)
MANDATORY RULES:
- You MUST ask about DIFFERENT projects each time
- Projects already discussed: {covered_projects}
- DO NOT ask about these projects again
- Select a NEW project from the resume that matches the job description
- Mention the exact project name from the resume
- Ask ONE focused question about implementation, decisions, or challenges

Question Types (rotate these across different projects):
1. Architecture/Design
2. Personal Contribution
3. Technical Decision
4. Problem-Solving
5. Scale/Performance
6. Trade-offs

STAGE: TECHNICAL (Job description aligned questions)
Based on the job description, ask about:
- Specific technologies mentioned in the job requirements
- System design and architecture patterns
- Database design and optimization
- API design and best practices
- Performance and scalability
- Security and authentication
- Testing and deployment strategies

You may also ask about:
- Skills listed in the resume
- Computer science fundamentals (data structures, algorithms, OS, DBMS, networking)
- OOP, design patterns, system design
- Debugging, problem-solving, Git
- Agile/Scrum methodologies
- Testing and QA
- Web basics (HTML, CSS, JavaScript)
- REST APIs
- Cloud fundamentals (AWS, Azure, GCP)
- Secure coding practices

===== ANTI-REPETITION SYSTEM =====

CRITICAL - NEVER REPEAT:
❌ Same project twice (check {covered_projects})
❌ Same question type twice in a row
❌ Same opening phrase
❌ Generic questions without resume context

REQUIRED DIVERSITY:
✓ Different question angles
✓ Varied sentence structures
✓ Resume-aligned technical depth

===== QUESTION DEPTH RULES =====

DO:
✓ Reference specific technologies/frameworks from the resume
✓ Ask implementation-level questions
✓ Probe trade-offs and challenges
✓ Focus on personal contributions

DON'T:
✗ Ask what the project does
✗ Ask multiple questions
✗ Ask unrelated theory

===== TONE & STYLE =====

- Professional and direct
- Conversational, not robotic
- No filler phrases
- Peer-to-peer interview tone

===== CURRENT STATE TRACKING =====

Current Stage: {stage}
Questions Asked So Far: {questions_count}
Projects Already Covered: {covered_projects}

INSTRUCTION BASED ON STATE:
- If stage is DEEP_DIVE and questions_count < 4: Ask about a NEW project
- If stage is TECHNICAL: Ask a job-aligned technical question
- Always ensure diversity"""
    ),
    (
        "human",
        """CANDIDATE RESUME:
{resume}

JOB DESCRIPTION:
{job_description}

Generate the next interview question following ALL rules above."""
    )
])

question_chain = question_prompt | llm | StrOutputParser()


def generate_question(
    job_description: str,
    resume: str,
    stage: str,
    questions_count: int = 0,
    covered_projects: list | None = None
) -> str:

    if covered_projects is None:
        covered_projects = []

    result = question_chain.invoke({
        "job_description": job_description,
        "resume": resume,
        "stage": stage,
        "questions_count": questions_count,
        "covered_projects": ", ".join(covered_projects) if covered_projects else "None"
    })

    result = result.strip()

    for prefix in (
        "Question:",
        "Q:",
        "Next Question:",
        "Here is the question:"
    ):
        if result.startswith(prefix):
            result = result[len(prefix):].strip()

    return result
