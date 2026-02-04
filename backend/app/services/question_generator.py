# # backend/app/services/question_generator.py

# import os
# from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
# from dotenv import load_dotenv
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import StrOutputParser
# from dotenv import load_dotenv
# from langchain_groq import ChatGroq

# load_dotenv()
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# GROQ_MODEL_ID = os.getenv("GROQ_MODEL_ID")
# if not GROQ_API_KEY:
#     raise RuntimeError("GROQ_API_KEY missing")

# llm = ChatGroq(
#     api_key=GROQ_API_KEY,
#     model=GROQ_MODEL_ID,
#     temperature=0.1,
#     max_tokens=250,
# )

# # HF_TOKEN = os.getenv("HF_TOKEN")
# # HF_MODEL_ID = os.getenv("HF_MODEL_ID", "mistralai/Mistral-7B-Instruct-v0.2")

# # hf_endpoint = HuggingFaceEndpoint(
# #     repo_id=HF_MODEL_ID,
# #     task="conversational",
# #     huggingfacehub_api_token=HF_TOKEN,
# #     temperature=0.1,
# #     max_new_tokens=300,
# # )

# # llm = ChatHuggingFace(llm=hf_endpoint)



# question_prompt = ChatPromptTemplate.from_messages([
#     (
#         "system",
#         """You are a senior technical interviewer conducting a comprehensive interview.

# CRITICAL OUTPUT RULES:
# - Output ONLY ONE question per response
# - NO prefixes like "Question:" or "Next:" or numbering
# - NO explanations or meta-commentary
# - Sound natural and conversational
# - Ask the question directly without any preamble

# ===== INTERVIEW STRUCTURE (13 QUESTIONS TOTAL) =====

# STAGE: INTRODUCTION (Questions 0-1)
# - Start with: "Please briefly introduce yourself and your professional background."
# - Ask about career goals and motivations

# STAGE: DEEP_DIVE (Questions 2-7, Project-focused)
# MANDATORY RULES:
# - You MUST ask about DIFFERENT projects each time
# - Projects already discussed: {covered_projects}
# - DO NOT repeat questions about the same project
# - Select a NEW project from the resume each time
# - Mention the exact project name from the resume in your question
# - Ask ONE focused question about implementation, architecture, decisions, or challenges

# Question Types (rotate across different projects):
# 1. Architecture/Design decisions
# 2. Your personal contribution and role
# 3. Technical implementation details
# 4. Problem-solving and challenges faced
# 5. Scale/Performance considerations
# 6. Trade-offs and alternative approaches

# STAGE: TECHNICAL (Questions 8-10, Skills & Job-aligned)
# Focus on skills from resume and job requirements:
# - Specific technologies/frameworks listed in resume (Python, Django, React, etc.)
# - Backend development (APIs, databases, authentication)
# - Frontend development (UI/UX, responsive design)
# - System design and architecture
# - Database design and queries
# - Cloud/DevOps if mentioned
# - Testing and debugging practices
# - Performance optimization
# - Security best practices

# STAGE: BEHAVIORAL_HR (Questions 11-13)
# Professional and soft skills:
# - "Can you describe a situation where you faced a challenge and how you handled it?"
# - "How do you prioritize tasks when working on multiple projects?"
# - "Tell me about a time you worked in a team and faced conflict."
# - "Describe a time you had to learn a new technology quickly."
# - "What motivates you in your professional career?"
# - "How do you stay updated with new technologies?"

# ===== ANTI-REPETITION SYSTEM =====

# CRITICAL - NEVER REPEAT:
# ❌ Same project twice (check {covered_projects})
# ❌ Same question type twice in a row
# ❌ Same technical topic twice
# ❌ Similar phrasing or sentence structure
# ❌ Generic questions without resume context

# REQUIRED DIVERSITY:
# ✓ Cover ALL projects listed in resume
# ✓ Cover ALL major skills from resume
# ✓ Different question angles each time
# ✓ Varied sentence structures
# ✓ Balance technical depth with breadth

# ===== QUESTION DEPTH RULES =====

# FOR PROJECT QUESTIONS:
# ✓ Reference specific project name and technology stack
# ✓ Ask about implementation challenges
# ✓ Probe technical decisions and trade-offs
# ✓ Focus on candidate's personal contributions
# ✗ Don't ask what the project does
# ✗ Don't ask vague or generic questions

# FOR TECHNICAL QUESTIONS:
# ✓ Reference skills from resume
# ✓ Ask scenario-based questions
# ✓ Test practical understanding
# ✓ Align with job description requirements
# ✗ Don't ask pure theory without context

# FOR HR QUESTIONS:
# ✓ Ask behavioral questions using STAR format prompts
# ✓ Focus on soft skills and problem-solving
# ✓ Ask about teamwork and communication
# ✓ Professional growth and learning

# ===== STAGE PROGRESSION LOGIC =====

# Current Stage: {stage}
# Questions Asked: {questions_count}
# Projects Covered: {covered_projects}

# STAGE RULES:
# - questions_count 0-1: INTRODUCTION stage
# - questions_count 2-7: DEEP_DIVE stage (different project each time)
# - questions_count 8-10: TECHNICAL stage (skills and job-aligned)
# - questions_count 11-13: BEHAVIORAL_HR stage

# ===== TONE & STYLE =====

# - Professional and direct
# - Conversational, not robotic
# - No filler phrases like "Now let's talk about..."
# - Peer-to-peer interview tone
# - Ask questions naturally as a senior interviewer would

# ===== DIVERSITY CHECKLIST =====

# Ensure coverage across:
# □ All major projects in resume
# □ All key skills mentioned (programming languages, frameworks, tools)
# □ Technical implementation questions
# □ System design thinking
# □ Problem-solving ability
# □ Behavioral and soft skills
# □ Career motivation and goals"""
#     ),
#     (
#         "human",
#         """CANDIDATE RESUME:
# {resume}

# JOB DESCRIPTION:
# {job_description}

# CURRENT INTERVIEW STATE:
# - Stage: {stage}
# - Questions asked so far: {questions_count}
# - Projects already covered: {covered_projects}

# Generate the next interview question following ALL rules above. Ensure maximum diversity and coverage of resume content."""
#     )
# ])



# question_chain = question_prompt | llm | StrOutputParser()


# def generate_question(
#     job_description: str,
#     resume: str,
#     stage: str,
#     questions_count: int = 0,
#     covered_projects: list | None = None
# ) -> str:

#     if covered_projects is None:
#         covered_projects = []

#     result = question_chain.invoke({
#         "job_description": job_description,
#         "resume": resume,
#         "stage": stage,
#         "questions_count": questions_count,
#         "covered_projects": ", ".join(covered_projects) if covered_projects else "None"
#     })

#     result = result.strip()

#     for prefix in (
#         "Question:",
#         "Q:",
#         "Next Question:",
#         "Here is the question:"
#     ):
#         if result.startswith(prefix):
#             result = result[len(prefix):].strip()

#     return result


# backend/app/services/question_generator.py
import os
import re
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_ID = os.getenv("GROQ_MODEL_ID")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY missing")

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=GROQ_MODEL_ID,
    temperature=0.80,
    max_tokens=250,
    top_p=0.95,
)

question_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are Alex, a senior software engineer conducting a real technical interview.

Rules:
- Ask technical questions
- Sound human and conversational, never templated
- Ask ONE clear, focused question at a time
- NEVER repeat or rephrase a previous question
- NEVER ask textbook or generic questions
- Base questions ONLY on:
  - Resume projects
  - Explicitly mentioned skills
  - Job role requirements

Adaptive behavior based on interview intent:
- TECH_DEEPEN → go deeper into internals, trade-offs, edge cases
- TECH_CLARIFY → ask for clarification on unclear logic
- TECH_SIMPLIFY → simplify the same topic, reduce scope
- TECH_SWITCH → switch to a new project or skill

Focus areas when present in resume:
- Databases → schema, queries, indexing, transactions
- Networking → latency, protocols, failures, Basic Networking Questions 
- Frameworks → lifecycle, internals, performance
- Prior work → decisions THEY made, constraints THEY faced

Projects already discussed:
{covered_projects}

Recent questions:
{recent_questions}

Current intent:
{stage}

Output ONLY the question.
"""
    ),
    (
        "human",
        """
Resume:
{resume}

Job Description:
{job_description}

Generate the next question naturally, like a real interviewer.
"""
    )
])


question_chain = question_prompt | llm | StrOutputParser()


def extract_project_from_question(question: str, resume: str) -> str | None:
    project_patterns = [
        r'(?:in|for|with|on|during|building|developing|creating)\s+(?:the\s+)?([A-Z][^.?!,]+?(?:System|Platform|Application|App|Agent|Tool|Website|Portal|Dashboard|API|Bot|Service))',
        r'([A-Z][^.?!,]+?(?:System|Platform|Application|App|Agent|Tool|Website|Portal|Dashboard|API|Bot|Service))',
    ]
    for pattern in project_patterns:
        matches = re.findall(pattern, question)
        for match in matches:
            if match.lower() in resume.lower():
                return match.strip()
    return None


def generate_question(
    job_description: str,
    resume: str,
    stage: str,
    questions_count: int = 0,
    covered_projects: list | None = None,
    previous_questions: list | None = None
) -> dict:
    if covered_projects is None:
        covered_projects = []
    if previous_questions is None:
        previous_questions = []

    covered_str = ", ".join(covered_projects) if covered_projects else "None yet"
    recent_questions = previous_questions[-3:] if len(previous_questions) >= 3 else previous_questions
    recent_questions_str = "\n".join([f"- {q}" for q in recent_questions]) if recent_questions else "None yet"

    result = question_chain.invoke({
        "job_description": job_description,
        "resume": resume,
        "stage": stage,
        "questions_count": questions_count,
        "covered_projects": covered_str,
        "recent_questions": recent_questions_str
    })

    result = result.strip()
    for prefix in ("Question:", "Q:", "Next Question:", "Here is the question:", "Next:"):
        if result.startswith(prefix):
            result = result[len(prefix):].strip()

    project_mentioned = extract_project_from_question(result, resume)
    updated_covered_projects = covered_projects.copy()
    if project_mentioned and project_mentioned not in updated_covered_projects:
        updated_covered_projects.append(project_mentioned)

    return {
        "question": result,
        "covered_projects": updated_covered_projects,
        "project_mentioned": project_mentioned
    }
