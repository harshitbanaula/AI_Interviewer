# backend/app/services/job_inference.py
import os
import re
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
from pyparsing import line

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_ID = os.getenv("GROQ_MODEL_ID")

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=GROQ_MODEL_ID,
    temperature=0.1,
    max_tokens=150,
)


inference_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a Senior Technical Recruiter analyzing resumes.

Your task: Identify the candidate's most suitable job title and core expertise.

OUTPUT FORMAT (strict):
[Job Title] - [One sentence description]

RULES:
1. Output ONLY in the format above
2. NO markdown formatting (no ###, no **, no bullets)
3. NO explanations or preambles
4. NO multiple lines
5. Job title should be 2-4 words
6. Description should be ONE sentence (15-25 words)

EXAMPLES:
Backend Python Developer - Expert in building scalable REST APIs using Python, FastAPI, and PostgreSQL with focus on performance optimization.
Senior Data Scientist - Specializes in machine learning model development using TensorFlow and large-scale data processing with Spark.
Marketing Analytics Manager - Leads data-driven marketing campaigns using Google Analytics, SQL, and Tableau for actionable insights.
Full Stack Engineer - Builds end-to-end web applications using React, Node.js, and MongoDB with emphasis on user experience.

IMPORTANT: Output ONLY the single line in the format shown above.
"""
    ),
    ("human", "Resume:\n{resume_text}\n\nProvide job title and description:")
])


chain = inference_prompt | llm | StrOutputParser()

def clean_llm_output(text: str) -> str:
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = text.replace("**", "").replace("__", "").replace("_", "")
    text = re.sub(r'```[\w]*\n?', '', text)

    prefies_to_remove =[
        "Job Title:",
        "Description:",
        "Role:",
        "Position:",
        "Title:",
        "Summary:",
        "Output:",
        "Answer:",
        "Result:",
        "Response:",
    ]

    for prefix in prefies_to_remove:
        if text.strip().startswith(prefix):
            text = text.strip()[len(prefix):].strip()

    lines = [line.strip() for line in text.split('\n') if line.strip()]

    for line in lines:

        if any(skip in line.lower() for skip in[
            "this job", "the short", "based on", "candidate", "suitable",
            "appropriate", "fit", "matches","match", "inferred",
            "predicted", "likely", "probably"
        ]):
            continue

        if " - " in line:
            line = line.strip('"\'')
            return line 
        
    if lines:
        return lines[0].strip('"\'')
    return ""

   

def infer_job_description(resume_text: str) -> str:
    try:
        truncated_text = resume_text[:3000]
        raw_result = chain.invoke({"resume_text": truncated_text})
        cleaned = clean_llm_output(raw_result)

        if cleaned and " - " in cleaned:
            parts = cleaned.split(" - ", 1)
            job_title = parts[0].strip()
            description = parts[1].strip() if len(parts) > 1 else ""

            if 2 <= len(job_title) <= 50 and description:
                return cleaned
            
        print("[Job inference] format validation failed, using fallback")
        return fallback_inference(resume_text)
    
    except Exception as e:
        print(f"Error during job inference: {e}")
        return fallback_inference(resume_text)
    

def fallback_inference(resume_text: str) -> str:
    resume_lower = resume_text.lower()

    title_patterns = {

    # --- Core Software Roles ---
    "software engineer": [
        "python", "java", "c++", "c#", "oop", "data structures",
        "algorithms", "design patterns", "software development"
    ],

    "backend developer": [
        "api", "rest", "microservices", "server", "spring boot",
        "django", "flask", "fastapi", "node.js", "database", 
        "postgresql", "mysql"
    ],

    "frontend developer": [
        "react", "angular", "vue", "next.js", "javascript",
        "typescript", "html", "css", "redux", "ui", "ux"
    ],

    "full stack developer": [
        "react", "angular", "vue", "node.js", "django",
        "mongodb", "postgresql", "full stack", "rest api"
    ],

    # --- Data Roles ---
    "data scientist": [
        "machine learning", "deep learning", "nlp",
        "tensorflow", "pytorch", "scikit-learn",
        "model training", "feature engineering"
    ],

    "machine learning engineer": [
        "ml pipeline", "model deployment", "mlops",
        "tensorflow", "pytorch", "model serving",
        "feature store"
    ],

    "data analyst": [
        "sql", "excel", "power bi", "tableau",
        "dashboard", "data visualization", "reporting"
    ],

    "data engineer": [
        "etl", "data pipeline", "spark", "hadoop",
        "airflow", "data warehouse", "bigquery",
        "snowflake", "kafka"
    ],

    # --- DevOps / Infra ---
    "devops engineer": [
        "docker", "kubernetes", "ci/cd",
        "jenkins", "github actions",
        "aws", "azure", "gcp",
        "terraform", "infrastructure as code"
    ],

    "site reliability engineer": [
        "sre", "monitoring", "prometheus",
        "grafana", "incident response",
        "high availability", "scalability"
    ],

    "cloud engineer": [
        "aws", "azure", "gcp",
        "ec2", "lambda", "s3",
        "cloud architecture"
    ],

    # --- Security ---
    "security engineer": [
        "penetration testing", "vulnerability assessment",
        "owasp", "cybersecurity", "siem",
        "encryption", "authentication"
    ],

    # --- QA ---
    "qa engineer": [
        "selenium", "automation testing",
        "unit testing", "integration testing",
        "test cases", "manual testing"
    ],

    # --- Mobile ---
    "android developer": [
        "android", "kotlin", "java android",
        "jetpack", "android studio"
    ],

    "ios developer": [
        "swift", "objective-c",
        "ios", "xcode"
    ],

    "flutter developer": [
        "flutter", "dart", "mobile app"
    ],

    # --- Product / Business ---
    "product manager": [
        "product roadmap", "stakeholder management",
        "requirement gathering", "prd",
        "user stories"
    ],

    "business analyst": [
        "business requirements",
        "gap analysis", "process improvement",
        "stakeholder communication"
    ],

    "marketing manager": [
        "seo", "google ads",
        "campaign management",
        "lead generation",
        "digital marketing"
    ]
}
    
    scores = {}
    for title, keywords in title_patterns.items():
        score = sum(1 for kw in keywords if kw in resume_lower)
        if score > 0:
            scores[title] = score

    if scores:
        best_title = max(scores, key=scores.get)
        return f"{best_title.title()} - Professional with relevant experience and skills"
    
    return "Software Engineer - Professional with relevant background"

