# backend/app/services/job_inference.py
import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_ID = os.getenv("GROQ_MODEL_ID")

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=GROQ_MODEL_ID,
    temperature=0.3,
    max_tokens=200,
)


inference_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        ### ROLE
        You are a Senior Technical Recruiter and Expert HR Manager specializing in talent mapping.
        
        ### TASK
        Analyze the provided resume text to identify the most accurate professional identity. 
        1. **Job Title**: Extract the candidate's current or most suitable professional title based on their experience, skills, and seniority level (e.g., "Senior Software Engineer", "Junior Marketing Analyst").
        2. **Short Description**: Provide a high-impact, 1-sentence summary of their core value proposition and primary technical/functional expertise.

        ### GUIDELINES
        - If the resume matches multiple roles, select the one with the most recent or deepest experience.
        - Ensure the 'Job Title' is industry-standard.
        - The 'Short Description' must be concise and avoid generic buzzwords.
        - If the resume is highly diverse, infer the strongest "Best Fit" role.

        ### OUTPUT FORMAT
        [Job Title] - [Short Description]

        ### EXAMPLES
        - Full Stack Developer - Expert in building responsive web applications using React and Node.js with a focus on cloud-native architecture.
        - Data Scientist - Specializes in predictive modeling and natural language processing using Python, PyTorch, and large-scale data pipelines.
        """
    ),
    ("human", "{resume_text}")
])

chain = inference_prompt | llm | StrOutputParser()


def infer_job_description(resume_text: str) ->str:

    try:
        truncated_text = resume_text[:3000]

        result = chain.invoke({"resume_text" : truncated_text})
        return result.strip()
    except Exception as e:
        print(f" Error inferring job description : {e}")
        return "Sogtware Engineer"

