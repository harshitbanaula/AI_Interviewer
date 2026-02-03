# backend/app/services/resume_parser.py
import os
import re
import tempfile
from typing import List, Dict
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader


def parse_resume(filename: str, content_bytes: bytes) -> str:
    """
    Parse resume content using LangChain loaders.
    Supports PDF, DOCX, TXT.
    Returns clean, normalized resume text.
    """
    suffix = filename.split(".")[-1].lower()

    # Create temp file safely
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
        tmp.write(content_bytes)
        tmp_path = tmp.name

    try:
        # Select loader
        if suffix == "pdf":
            loader = PyPDFLoader(tmp_path)
        elif suffix in ["docx", "doc"]:
            loader = Docx2txtLoader(tmp_path)
        elif suffix == "txt":
            loader = TextLoader(tmp_path, encoding="utf-8")
        else:
            raise ValueError(f"Unsupported resume format: {suffix}")

        # Load document
        docs = loader.load()
        raw_text = "\n".join(doc.page_content for doc in docs)

        # Clean and normalize
        cleaned_text = clean_resume_text(raw_text)

        return cleaned_text

    except Exception as e:
        raise RuntimeError(f"Failed to parse resume: {str(e)}")

    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


# ----------------------------
# Helper Functions
# ----------------------------

def clean_resume_text(text: str) -> str:

    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'Page\s*\d+\s*(of\s*\d+)?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'[\u2022•▪]', '-', text)
    text = re.sub(r'[ \t]+', ' ', text)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return '\n'.join(lines).strip()


def extract_projects_section(resume_text: str) -> str:

    # match = re.search(r'PROJECT EXPERIENCE(.*?)(EDUCATION|CERTIFICATIONS|$)', resume_text, re.DOTALL | re.IGNORECASE)
    match = re.search(
    r'(PROJECTS?|PROJECT\s+EXPERIENCE|ACADEMIC\s+PROJECTS?|PERSONAL\s+PROJECTS?|KEY\s+PROJECTS?|MAJOR\s+PROJECTS?)'
    r'(.*?)(EDUCATION|EXPERIENCE|WORK\s+EXPERIENCE|SKILLS|CERTIFICATIONS|ACHIEVEMENTS|INTERNSHIPS|SUMMARY|PROFILE|$)',
    resume_text,
    re.DOTALL | re.IGNORECASE
)

    section = match.group(1).strip() if match else ""

    # Fix missing newlines between projects
    # Insert newline before any capitalized project that follows a period without space
    section = re.sub(r'\.([A-Z][A-Za-z0-9\s\-\(\)/]+?\|)', r'.\n\1', section)

    return section
def parse_projects(resume_text: str) -> List[Dict[str, str]]:
    section_text = extract_projects_section(resume_text)
    projects = []

    if not section_text:
        return projects

    lines = section_text.split('\n')
    current_project = None

    for line in lines:
        # Project title detection
        if re.match(r'^[A-Z][A-Za-z0-9\s\-\(\)/]+$', line.split('|')[0].strip()):
            if current_project:
                projects.append(current_project)
            current_project = {"name": line.strip(), "description": ""}
        else:
            if current_project:
                if current_project["description"]:
                    current_project["description"] += "\n" + line.strip()
                else:
                    current_project["description"] = line.strip()

    if current_project:
        projects.append(current_project)

    # Numbering
    for idx, proj in enumerate(projects, 1):
        proj["name"] = f"Project {idx}: {proj['name']}"

    return projects



def get_resume_summary(resume_text: str) -> Dict[str, any]:

    projects = parse_projects(resume_text)
    technologies = extract_technologies_from_resume(resume_text)

    return {
        "full_text": resume_text,
        "projects": projects,
        "num_projects": len(projects),
        "technologies": technologies,
        "word_count": len(resume_text.split()),
        "has_projects": len(projects) > 0
    }


def extract_technologies_from_resume(resume_text: str) -> List[str]:

    tech_patterns = [
        r'\bPython\b', r'\bJava\b', r'\bJavaScript\b', r'\bTypeScript\b',
        r'\bReact\b', r'\bAngular\b', r'\bVue\b',
        r'\bDjango\b', r'\bFlask\b', r'\bFastAPI\b',
        r'\bNode\.js\b', r'\bMongoDB\b', r'\bPostgreSQL\b',
        r'\bMySQL\b', r'\bAWS\b', r'\bDocker\b', r'\bKubernetes\b',
        r'\bREST\b', r'\bGraphQL\b', r'\bWebSocket\b',
        r'\bMachine Learning\b', r'\bAI\b'
    ]

    technologies = set()
    for pattern in tech_patterns:
        if re.search(pattern, resume_text, re.IGNORECASE):
            technologies.add(pattern.replace('\\b', ''))

    return list(technologies)

