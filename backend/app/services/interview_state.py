


# # backend/app/services/interview_state.py
# import uuid
# import re
# from typing import Dict, List
# from app.services.question_generator import generate_question
# from app.services.evaluator import score_answer


# class InterviewSession:
#     HR_QUESTIONS = [
#         "Can you describe a situation where you faced a challenge and how you handled it?",
#         "How do you prioritize tasks when working on multiple projects?",
#         "Tell me about a time you worked in a team and faced conflict.",
#         "Describe a time you had to learn a new technology quickly.",
#         "What motivates you in your professional career?"
#     ]

#     MAX_TECH_QUESTIONS = 5
#     MAX_DEEP_DIVE_QUESTIONS = 2

#     def __init__(self, resume_text: str, job_description: str):
#         self.resume_text = resume_text
#         self.job_description = job_description

#         self.stage = "INTRO"
#         self.expecting_answer = False
#         self.completed = False

#         self.questions: List[str] = []
#         self.answers: List[str] = []
#         self.scores: List[dict] = []

#         self.tech_count = 0
#         self.deep_dive_count = 0
#         self.hr_index = 0

#         #  FIX: track projects already asked
#         self.covered_projects: List[str] = []

#     def _extract_project_from_question(self, question: str) -> str | None:
#         """
#         Extract project name from question text.
#         Assumes project names are quoted.
#         """
#         match = re.search(r'"([^"]+)"', question)
#         if match:
#             return match.group(1)
#         return None

#     def next_question(self) -> str | None:
#         if self.completed:
#             return None

#         self.expecting_answer = True

#         # INTRO (hard-coded, industry standard)
#         if self.stage == "INTRO":
#             self.stage = "TECHNICAL"
#             q = "Please briefly introduce yourself and your professional background."

#         # TECHNICAL QUESTIONS
#         elif self.stage == "TECHNICAL" and self.tech_count < self.MAX_TECH_QUESTIONS:
#             self.tech_count += 1
#             q = generate_question(
#                 job_description=self.job_description,
#                 resume=self.resume_text,
#                 stage="TECHNICAL",
#                 questions_count=len(self.questions),
#                 covered_projects=self.covered_projects
#             )

#         elif self.stage == "TECHNICAL":
#             self.stage = "DEEP_DIVE"
#             return self.next_question()

#         # DEEP DIVE (PROJECT-BASED)
#         elif self.stage == "DEEP_DIVE" and self.deep_dive_count < self.MAX_DEEP_DIVE_QUESTIONS:
#             self.deep_dive_count += 1
#             q = generate_question(
#                 job_description=self.job_description,
#                 resume=self.resume_text,
#                 stage="DEEP_DIVE",
#                 questions_count=len(self.questions),
#                 covered_projects=self.covered_projects
#             )

#         elif self.stage == "DEEP_DIVE":
#             self.stage = "HR"
#             return self.next_question()

#         # HR QUESTIONS
#         elif self.stage == "HR" and self.hr_index < len(self.HR_QUESTIONS):
#             q = self.HR_QUESTIONS[self.hr_index]
#             self.hr_index += 1

#         else:
#             self.completed = True
#             self.expecting_answer = False
#             return None

#         # Track asked question
#         self.questions.append(q)

#         #  FIX: track covered project
#         project = self._extract_project_from_question(q)
#         if project and project not in self.covered_projects:
#             self.covered_projects.append(project)

#         return q

#     def save_answer(self, answer: str):
#         if not self.expecting_answer:
#             return

#         self.answers.append(answer)
#         self.scores.append(score_answer(answer))
#         self.expecting_answer = False

#     def final_result(self) -> dict:
#         avg_score = round(
#             sum(s["final_score"] for s in self.scores) / len(self.scores),
#             2
#         ) if self.scores else 0

#         return {
#             "average_score": avg_score,
#             # 🔥 FIX: 70% PASS threshold
#             "result": "PASS" if avg_score >= 0.7 else "FAIL",
#             "questions": self.questions,
#             "answers": self.answers,
#             "scores": self.scores
#         }


# _sessions: Dict[str, InterviewSession] = {}

# def create_session(resume_text: str, job_description: str) -> str:
#     sid = str(uuid.uuid4())
#     _sessions[sid] = InterviewSession(resume_text, job_description)
#     return sid

# def get_session(session_id: str) -> InterviewSession | None:
#     return _sessions.get(session_id)






# import uuid
# import re
# from typing import Dict, List
# from app.services.question_generator import generate_question
# from app.services.evaluator import score_answer

# class InterviewSession:
#     HR_QUESTIONS = [
#         "Can you describe a situation where you faced a challenge and how you handled it?",
#         "How do you prioritize tasks when working on multiple projects?",
#         "Tell me about a time you worked in a team and faced conflict.",
#         "Describe a time you had to learn a new technology quickly.",
#         "What motivates you in your professional career?"
#     ]

#     MAX_TECH_QUESTIONS = 5
#     MAX_DEEP_DIVE_QUESTIONS = 2

#     def __init__(self, resume_text: str, job_description: str):
#         self.resume_text = resume_text
#         self.job_description = job_description

#         self.stage = "INTRO"
#         self.expecting_answer = False
#         self.completed = False

#         self.questions: List[str] = []
#         self.answers: List[str] = []
#         self.scores: List[dict] = []

#         self.tech_count = 0
#         self.deep_dive_count = 0
#         self.hr_index = 0

#         self.covered_projects: List[str] = []

#     def _extract_project_from_question(self, question: str) -> str | None:
#         match = re.search(r'"([^"]+)"', question)
#         if match:
#             return match.group(1)
#         return None

#     def next_question(self) -> str | None:
#         if self.completed:
#             return None

#         self.expecting_answer = True

#         # INTRO
#         if self.stage == "INTRO":
#             self.stage = "TECHNICAL"
#             q = "Please briefly introduce yourself and your professional background."

#         # TECHNICAL QUESTIONS
#         elif self.stage == "TECHNICAL" and self.tech_count < self.MAX_TECH_QUESTIONS:
#             self.tech_count += 1
#             q = generate_question(
#                 job_description=self.job_description,
#                 resume=self.resume_text,
#                 stage="TECHNICAL",
#                 questions_count=len(self.questions),
#                 covered_projects=self.covered_projects
#             )

#         elif self.stage == "TECHNICAL":
#             self.stage = "DEEP_DIVE"
#             return self.next_question()

#         # DEEP DIVE
#         elif self.stage == "DEEP_DIVE" and self.deep_dive_count < self.MAX_DEEP_DIVE_QUESTIONS:
#             self.deep_dive_count += 1
#             q = generate_question(
#                 job_description=self.job_description,
#                 resume=self.resume_text,
#                 stage="DEEP_DIVE",
#                 questions_count=len(self.questions),
#                 covered_projects=self.covered_projects
#             )

#         elif self.stage == "DEEP_DIVE":
#             self.stage = "HR"
#             return self.next_question()

#         # HR
#         elif self.stage == "HR" and self.hr_index < len(self.HR_QUESTIONS):
#             q = self.HR_QUESTIONS[self.hr_index]
#             self.hr_index += 1

#         else:
#             self.completed = True
#             self.expecting_answer = False
#             return None

#         # Track question
#         self.questions.append(q)

#         # Track project
#         project = self._extract_project_from_question(q)
#         if project and project not in self.covered_projects:
#             self.covered_projects.append(project)

#         return q

#     def save_answer(self, answer: str = ""):
#         """
#         Save answer. If user didn't speak, empty string is accepted.
#         """
#         if not self.expecting_answer:
#             return

#         self.answers.append(answer if answer else "No answer provided")
#         self.scores.append(score_answer(answer))
#         self.expecting_answer = False

#     def final_result(self) -> dict:
#         """
#         Return structured result for frontend:
#         - Score per question
#         - Average score
#         - PASS/FAIL
#         - Strengths & improvements aggregated
#         """
#         # Ensure all questions have scores
#         while len(self.answers) < len(self.questions):
#             self.save_answer("No answer provided")

#         avg_score = round(
#             sum(s["final_score"] for s in self.scores) / len(self.scores),
#             2
#         ) if self.scores else 0

#         aggregated_strengths = []
#         aggregated_improvements = []

#         for s in self.scores:
#             aggregated_strengths.extend(s.get("strengths", []))
#             aggregated_improvements.extend(s.get("improvements", []))

#         # Remove duplicates
#         aggregated_strengths = list(dict.fromkeys(aggregated_strengths))
#         aggregated_improvements = list(dict.fromkeys(aggregated_improvements))

#         # Structured per-question info
#         per_question = []
#         for i, q in enumerate(self.questions):
#             per_question.append({
#                 "question": q,
#                 "answer": self.answers[i],
#                 "scores": self.scores[i]
#             })

#         return {
#             "average_score": avg_score,
#             "result": "PASS" if avg_score >= 0.7 else "FAIL",
#             "questions": per_question,
#             "strengths": aggregated_strengths,
#             "improvements": aggregated_improvements
#         }


# _sessions: Dict[str, InterviewSession] = {}

# def create_session(resume_text: str, job_description: str) -> str:
#     sid = str(uuid.uuid4())
#     _sessions[sid] = InterviewSession(resume_text, job_description)
#     return sid

# def get_session(session_id: str) -> InterviewSession | None:
#     return _sessions.get(session_id)


# # backend/app/services/interview_state.py

# import uuid
# import re
# from typing import Dict, List
# from app.services.question_generator import generate_question
# from app.services.evaluator import score_answer
# from app.services.llm_feedback import generate_feedback


# class InterviewSession:
#     HR_QUESTIONS = [
#         "Can you describe a situation where you faced a challenge and how you handled it?",
#         "How do you prioritize tasks when working on multiple projects?",
#         "Tell me about a time you worked in a team and faced conflict.",
#         "Describe a time you had to learn a new technology quickly.",
#         "What motivates you in your professional career?"
#     ]

#     MAX_TECH_QUESTIONS = 5
#     MAX_DEEP_DIVE_QUESTIONS = 2
#     MAX_RETRY = 5  

#     def __init__(self, resume_text: str, job_description: str):
#         self.resume_text = resume_text
#         self.job_description = job_description

#         self.stage = "INTRO"
#         self.expecting_answer = False
#         self.completed = False

#         self.questions: List[str] = []
#         self.answers: List[str] = []
#         self.scores: List[dict] = []

#         self.tech_count = 0
#         self.deep_dive_count = 0
#         self.hr_index = 0
#         self.covered_projects: List[str] = []

#         self.feedback_text: str = ""

#     # --------------------------------------------------
#     # Helpers
#     # --------------------------------------------------

#     def _extract_project_from_question(self, question: str) -> str | None:
#         match = re.search(r'for the ([A-Za-z0-9 _-]+) project', question, re.IGNORECASE)
#         return match.group(1).strip() if match else None

#     def _is_duplicate(self, question: str) -> bool:
#         return question.strip() in self.questions

#     def _generate_unique_question(self, stage: str) -> str:
        
#         for _ in range(self.MAX_RETRY):
#             q = generate_question(
#                 job_description=self.job_description,
#                 resume=self.resume_text,
#                 stage=stage,
#                 questions_count=len(self.questions),
#                 covered_projects=self.covered_projects
#             )
#             if q and not self._is_duplicate(q):
#                 return q

#         # Fallback (never blocks interview)
#         return "Can you explain a technical decision you made recently and why?"

#     # --------------------------------------------------
#     # Interview Flow
#     # --------------------------------------------------

#     def next_question(self) -> str | None:
#         if self.completed:
#             return None

#         self.expecting_answer = True

#         # INTRO
#         if self.stage == "INTRO":
#             self.stage = "TECHNICAL"
#             q = "Please briefly introduce yourself and your professional background."

#         # TECHNICAL
#         elif self.stage == "TECHNICAL" and self.tech_count < self.MAX_TECH_QUESTIONS:
#             self.tech_count += 1
#             q = self._generate_unique_question("TECHNICAL")

#         elif self.stage == "TECHNICAL":
#             self.stage = "DEEP_DIVE"
#             return self.next_question()

#         # DEEP DIVE
#         elif self.stage == "DEEP_DIVE" and self.deep_dive_count < self.MAX_DEEP_DIVE_QUESTIONS:
#             self.deep_dive_count += 1
#             q = self._generate_unique_question("DEEP_DIVE")

#         elif self.stage == "DEEP_DIVE":
#             self.stage = "HR"
#             return self.next_question()

#         # HR
#         elif self.stage == "HR" and self.hr_index < len(self.HR_QUESTIONS):
#             q = self.HR_QUESTIONS[self.hr_index]
#             self.hr_index += 1

#         else:
#             self.completed = True
#             self.expecting_answer = False
#             self.generate_feedback()
#             return None

#         # Track question
#         self.questions.append(q)

#         # Track covered project
#         project = self._extract_project_from_question(q)
#         if project and project not in self.covered_projects:
#             self.covered_projects.append(project)

#         return q

#     # --------------------------------------------------
#     # Answer Handling
#     # --------------------------------------------------

#     def save_answer(self, answer: str):
#         if not self.expecting_answer:
#             return

#         answer_text = answer.strip() or "No answer provided"

#         self.answers.append(answer_text)
#         self.scores.append(score_answer(answer_text))
#         self.expecting_answer = False

#     # --------------------------------------------------
#     # Feedback
#     # --------------------------------------------------

#     def generate_feedback(self):
#         qa_list = []
#         for i, q in enumerate(self.questions):
#             ans = self.answers[i] if i < len(self.answers) else "No answer provided"
#             sc = self.scores[i] if i < len(self.scores) else score_answer(ans)
#             qa_list.append({
#                 "question": q,
#                 "answer": ans,
#                 "scores": sc
#             })

#         avg_score = round(
#             sum(s["final_score"] for s in self.scores) / len(self.scores),
#             2
#         ) if self.scores else 0

#         self.feedback_text = generate_feedback(qa_list, avg_score)

#     # --------------------------------------------------
#     # Final Result
#     # --------------------------------------------------

#     def final_result(self) -> dict:
#         avg_score = round(
#             sum(s["final_score"] for s in self.scores) / len(self.scores),
#             2
#         ) if self.scores else 0

#         return {
#             "average_score": avg_score,
#             "result": "PASS" if avg_score >= 0.7 else "FAIL",
#             "questions": self.questions,
#             "answers": self.answers,
#             "scores": self.scores,
#             "feedback": self.feedback_text
#         }


# # --------------------------------------------------
# # Session Store
# # --------------------------------------------------

# _sessions: Dict[str, InterviewSession] = {}

# def create_session(resume_text: str, job_description: str) -> str:
#     sid = str(uuid.uuid4())
#     _sessions[sid] = InterviewSession(resume_text, job_description)
#     return sid

# def get_session(session_id: str) -> InterviewSession | None:
#     return _sessions.get(session_id)





import uuid
import re
from typing import Dict, List
from app.services.question_generator import generate_question
from app.services.evaluator import score_answer
from app.services.llm_feedback import generate_feedback


class InterviewSession:
    HR_QUESTIONS = [
        "Can you describe a situation where you faced a challenge and how you handled it?",
        "How do you prioritize tasks when working on multiple projects?",
        "Tell me about a time you worked in a team and faced conflict.",
        "Describe a time you had to learn a new technology quickly.",
        "What motivates you in your professional career?"
    ]

    MAX_TECH_QUESTIONS = 5
    MAX_DEEP_DIVE_QUESTIONS = 2
    MAX_RETRY = 5  

    def __init__(self, resume_text: str, job_description: str):
        self.resume_text = resume_text
        self.job_description = job_description

        self.stage = "INTRO"
        self.expecting_answer = False
        self.completed = False

        self.questions: List[str] = []
        self.answers: List[str] = []
        self.scores: List[dict] = []

        self.tech_count = 0
        self.deep_dive_count = 0
        self.hr_index = 0
        self.covered_projects: List[str] = []

        self.feedback_text: str = ""

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def _extract_project_from_question(self, question: str) -> str | None:
        match = re.search(r'for the ([A-Za-z0-9 _-]+) project', question, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _is_duplicate(self, question: str) -> bool:
        return question.strip() in self.questions

    def _generate_unique_question(self, stage: str) -> str:
        """
        Generate a unique question and update covered_projects.
        Returns just the question string.
        """
        for _ in range(self.MAX_RETRY):
            # Pass previous questions to avoid repetitive phrasing
            result = generate_question(
                job_description=self.job_description,
                resume=self.resume_text,
                stage=stage,
                questions_count=len(self.questions),
                covered_projects=self.covered_projects,
                previous_questions=self.questions
            )
            
            if isinstance(result, dict):
                q = result.get("question", "")
                self.covered_projects = result.get("covered_projects", self.covered_projects)
            else:
                q = result
            
            if q and not self._is_duplicate(q):
                return q

        # Fallback question if retries fail
        return "Can you explain a technical decision you made recently and why?"

    # --------------------------------------------------
    # Interview Flow
    # --------------------------------------------------

    def next_question(self) -> str | None:
        """
        Generate next question. Returns a STRING (not dict).
        """
        if self.completed:
            return None

        self.expecting_answer = True

        # INTRO
        if self.stage == "INTRO":
            self.stage = "TECHNICAL"
            q = "Please briefly introduce yourself and your professional background."

        # TECHNICAL
        elif self.stage == "TECHNICAL" and self.tech_count < self.MAX_TECH_QUESTIONS:
            self.tech_count += 1
            q = self._generate_unique_question("TECHNICAL")

        elif self.stage == "TECHNICAL":
            self.stage = "DEEP_DIVE"
            return self.next_question()

        # DEEP DIVE
        elif self.stage == "DEEP_DIVE" and self.deep_dive_count < self.MAX_DEEP_DIVE_QUESTIONS:
            self.deep_dive_count += 1
            q = self._generate_unique_question("DEEP_DIVE")

        elif self.stage == "DEEP_DIVE":
            self.stage = "HR"
            return self.next_question()

        # HR
        elif self.stage == "HR" and self.hr_index < len(self.HR_QUESTIONS):
            q = self.HR_QUESTIONS[self.hr_index]
            self.hr_index += 1

        else:
            self.completed = True
            self.expecting_answer = False
            self.generate_feedback()
            return None

        # Track question
        self.questions.append(q)

        # Track covered project
        project = self._extract_project_from_question(q)
        if project and project not in self.covered_projects:
            self.covered_projects.append(project)

        return q

    # --------------------------------------------------
    # Answer Handling
    # --------------------------------------------------

    def save_answer(self, answer: str):
        if not self.expecting_answer:
            return

        answer_text = answer.strip() or "No answer provided"

        self.answers.append(answer_text)
        self.scores.append(score_answer(answer_text))
        self.expecting_answer = False

    # --------------------------------------------------
    # Feedback
    # --------------------------------------------------

    def generate_feedback(self):
        qa_list = []
        for i, q in enumerate(self.questions):
            ans = self.answers[i] if i < len(self.answers) else "No answer provided"
            sc = self.scores[i] if i < len(self.scores) else score_answer(ans)
            qa_list.append({
                "question": q,
                "answer": ans,
                "scores": sc
            })

        avg_score = round(
            sum(s["final_score"] for s in self.scores) / len(self.scores),
            2
        ) if self.scores else 0

        self.feedback_text = generate_feedback(qa_list, avg_score)

    # --------------------------------------------------
    # Final Result
    # --------------------------------------------------

    def final_result(self) -> dict:
        avg_score = round(
            sum(s["final_score"] for s in self.scores) / len(self.scores),
            2
        ) if self.scores else 0

        return {
            "average_score": avg_score,
            "result": "PASS" if avg_score >= 0.7 else "FAIL",
            "questions": self.questions,
            "answers": self.answers,
            "scores": self.scores,
            "feedback": self.feedback_text,
            "covered_projects": self.covered_projects
        }


# --------------------------------------------------
# Session Store
# --------------------------------------------------

_sessions: Dict[str, InterviewSession] = {}

def create_session(resume_text: str, job_description: str) -> str:
    sid = str(uuid.uuid4())
    _sessions[sid] = InterviewSession(resume_text, job_description)
    return sid

def get_session(session_id: str) -> InterviewSession | None:
    return _sessions.get(session_id)
