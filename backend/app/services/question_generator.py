import os
import re
import json
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
from difflib import SequenceMatcher

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_ID = os.getenv("GROQ_MODEL_ID")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY missing")

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=GROQ_MODEL_ID,
    temperature=0.75,
    max_tokens=300,
    top_p=0.90,
)


# DYNAMIC SKILL EXTRACTION
extraction_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """Extract key information from this resume.

Return ONLY valid JSON with this structure:
{{
  "skills": ["skill1", "skill2"],
  "projects": ["Project Name 1", "Project Name 2"],
  "experience": ["Company 1 - Role", "Company 2 - Role"]
}}

Rules:
- Extract ONLY what is explicitly mentioned
- Do NOT infer or assume skills
- Skills can be: technologies, tools, platforms, methodologies, or competencies
- Keep project names concise
- Maximum 15 skills, 5 projects, 5 experience entries

Return ONLY JSON, no explanation."""
    ),
    (
        "human",
        "Resume:\n{resume}\n\nExtract skills, projects, and experience."
    )
])

extraction_chain = extraction_prompt | llm | StrOutputParser()

_resume_cache = {}


def extract_resume_skills(resume: str) -> dict:
    resume_hash = hash(resume[:500])
    if resume_hash in _resume_cache:
        print("[EXTRACT] Using cached resume data")
        return _resume_cache[resume_hash]
    
    try:
        print("[EXTRACT] Analyzing resume...")
        raw = extraction_chain.invoke({"resume": resume[:3000]})
        
        raw = raw.strip()
        if raw.startswith("```json"):
            raw = raw[7:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()
        
        data = json.loads(raw)
        
        result = {
            "skills": data.get("skills", [])[:15],
            "projects": data.get("projects", [])[:5],
            "experience": data.get("experience", [])[:5]
        }
        
        _resume_cache[resume_hash] = result
        
        print(f"[EXTRACT] Found {len(result['skills'])} skills, {len(result['projects'])} projects")
        return result
        
    except Exception as e:
        print(f"[EXTRACT] Extraction failed: {e}, using fallback")
        
        words = re.findall(r'\b([A-Z][a-z]{2,15})\b', resume)
        unique_words = list(set(words))[:15]
        
        result = {
            "skills": unique_words,
            "projects": [],
            "experience": []
        }
        
        _resume_cache[resume_hash] = result
        return result


def format_resume_context(data: dict) -> str:
    parts = []
    
    if data["skills"]:
        parts.append("Skills/Tools: " + ", ".join(data["skills"]))
    
    if data["projects"]:
        parts.append("Projects: " + ", ".join(data["projects"]))
    
    if data["experience"]:
        parts.append("Experience: " + ", ".join(data["experience"]))
    
    return "\n".join(parts) if parts else "Limited information in resume"



# NEW: DETERMINE QUESTION TYPE (PROJECT vs SKILL DEEP-DIVE)

def get_question_type(questions_count: int, answered_count: int) -> str:
  
    if questions_count == 0:
        return "INTRO"
    elif questions_count % 2 == 1:
        return "PROJECT"
    else:
        return "SKILL"


def get_question_focus(question_type: str) -> str:
    
    if question_type == "INTRO":
        return "Ask for a brief professional introduction. No technical pressure yet."
    
    elif question_type == "PROJECT":
        return """Ask about a specific PROJECT they worked on.
Focus on:
- What they built
- Challenges they faced
- Design decisions they made
- Results/outcomes

Example: "How did you implement X feature in your Y project?"
"""
    
    elif question_type == "SKILL":
        return """Ask a DEEP TECHNICAL question about a specific SKILL from their resume.

For programming languages (Python, JavaScript, Java, etc.):
- Language internals (decorators, closures, async, memory management)
- Best practices and design patterns
- Performance optimization
- Advanced features

For frameworks (Django, React, Flask, etc.):
- Architecture and lifecycle
- How it works under the hood
- Trade-offs and limitations
- Advanced usage

For cloud/tools (AWS, Docker, Git, etc.):
- Core concepts and architecture
- Best practices
- Common pitfalls
- Real-world scenarios

For databases (PostgreSQL, MongoDB, etc.):
- Query optimization
- Indexing strategies
- Transactions and ACID
- Scaling approaches

IMPORTANT: 
- Ask conceptual/theoretical questions about the SKILL itself
- NOT about how they used it in a project (that's PROJECT type)
- Go DEEP - assume they know the basics
- Test understanding of internals/advanced concepts

Example: "Explain how Python decorators work under the hood"
Example: "What's the difference between async/await and callbacks in JavaScript?"
Example: "How does AWS Lambda handle cold starts?"
"""
    
    return ""



# FUZZY DUPLICATE DETECTION

def similarity_ratio(str1: str, str2: str) -> float:
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


def is_similar_question(new_q: str, prev_questions: list, threshold: float = 0.70) -> bool:
    for prev_q in prev_questions:
        if similarity_ratio(new_q, prev_q) > threshold:
            print(f"[QUESTION] Rejected - too similar to: {prev_q[:50]}...")
            return True
    return False


# BALANCED QUESTION GENERATION PROMPT

question_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are Alex, a senior interviewer conducting a professional interview.


CANDIDATE'S BACKGROUND -:


{resume_context}

CRITICAL: ONLY ask about what's listed above.


QUESTION TYPE FOR THIS TURN -:


Type: {question_type}

{question_focus}


INTERVIEW CONTEXT -:


Current Stage: {stage}
Projects/Topics Already Covered: {covered_projects}

Recent Questions:
{recent_questions}


GUIDELINES -:


If QUESTION TYPE is "PROJECT":
 Ask about implementation details of their actual projects
 Focus on challenges, decisions, trade-offs
 Reference specific project names from their background

If QUESTION TYPE is "SKILL":
 Ask deep technical/conceptual questions about the skill itself
 Test understanding of internals, advanced concepts
 Go beyond basics - assume they know fundamentals
 Do NOT ask "how did you use X in your project" (that's PROJECT type)
 Ask theoretical: "What is...", "Explain...", "How does... work", "What's the difference..."

Examples of GOOD SKILL questions:
- "Explain how Python's GIL works and its impact on multithreading"
- "What's the difference between cookies and JWT for authentication?"
- "How does AWS Lambda's execution model differ from EC2?"
- "Explain database indexing strategies and trade-offs"

Examples of BAD SKILL questions (these are PROJECT type):
- "How did you use Python in your project?" 
- "Tell me about your AWS experience" 


OUTPUT:


Generate ONE natural question based on the TYPE specified above.
Sound conversational, not robotic.
Output ONLY the question.
"""
    ),
    (
        "human",
        "Generate the next {question_type} question."
    )
])

question_chain = question_prompt | llm | StrOutputParser()



# MAIN FUNCTION

def generate_question(
    job_description: str,
    resume: str,
    stage: str,
    questions_count: int = 0,
    covered_projects: list = None,
    previous_questions: list = None
) -> dict:
    
    if covered_projects is None:
        covered_projects = []
    if previous_questions is None:
        previous_questions = []

    # ── STEP 1: Extract skills ──
    resume_data = extract_resume_skills(resume)
    resume_context = format_resume_context(resume_data)
    
    # ── STEP 2: Determine question type (PROJECT or SKILL) ──
    question_type = get_question_type(questions_count, len(previous_questions))
    question_focus = get_question_focus(question_type)
    
    print(f"[QUESTION] Type for Q{questions_count}: {question_type}")
    
    # ── STEP 3: Format context ──
    covered_str = ", ".join(covered_projects) if covered_projects else "None yet"
    
    recent_questions = previous_questions[-3:] if len(previous_questions) >= 3 else previous_questions
    recent_questions_str = "\n".join([f"- {q}" for q in recent_questions]) if recent_questions else "None yet"

    # ── STEP 4: Generate question ──
    max_retries = 5
    
    for attempt in range(1, max_retries + 1):
        try:
            result = question_chain.invoke({
                "resume_context": resume_context,
                "question_type": question_type,
                "question_focus": question_focus,
                "stage": stage,
                "covered_projects": covered_str,
                "recent_questions": recent_questions_str
            })

            result = result.strip()
            
            # Clean artifacts
            for prefix in ("Question:", "Q:", "Next:", "Here's", "Let me"):
                if result.startswith(prefix):
                    result = result.split(":", 1)[-1].strip() if ":" in result else result[len(prefix):].strip()
            
            result = result.strip('"\'')

            # Check duplicates
            if not is_similar_question(result, previous_questions, threshold=0.70):
                
                project_mentioned = extract_project_from_question(result, resume)
                
                updated_covered_projects = covered_projects.copy()
                if project_mentioned and project_mentioned not in updated_covered_projects:
                    updated_covered_projects.append(project_mentioned)
                
                print(f"[QUESTION]  {question_type} question (attempt {attempt}): {result[:60]}...")
                
                return {
                    "question": result,
                    "covered_projects": updated_covered_projects,
                    "project_mentioned": project_mentioned
                }
            else:
                print(f"[QUESTION] Attempt {attempt}: Duplicate, retrying...")
                
        except Exception as e:
            print(f"[QUESTION] Error attempt {attempt}: {e}")

    # ── STEP 5: Fallback ──
    print(f"[QUESTION]  Using fallback")
    
    if question_type == "PROJECT" and resume_data["projects"]:
        fallback = f"Tell me about your {resume_data['projects'][0]} work."
    elif question_type == "SKILL" and resume_data["skills"]:
        fallback = f"Explain your understanding of {resume_data['skills'][0]} in depth."
    else:
        fallback = "Tell me about your most recent professional experience."
    
    return {
        "question": fallback,
        "covered_projects": covered_projects,
        "project_mentioned": None
    }


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