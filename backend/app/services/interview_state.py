# import uuid
# from typing import Dict, List
# from app.services.question_generator import generate_question

# class InterviewSession:
#     HR_QUESTIONS = [
#         "Tell me about a time you faced a challenge at work and how you handled it.",
#         "How do you prioritize your tasks when working on multiple projects?",
#         "Describe a situation where you had to work with a difficult team member.",
#         "What motivates you to do your best at work?",
#         "Where do you see yourself in the next 3–5 years?"
#     ]

#     MAX_TECH_QUESTIONS = 7

#     def __init__(self, resume_text: str, job_description: str):
#         self.resume_text = resume_text
#         self.job_description = job_description
#         self.stage = "INTRO"
#         self.questions: List[str] = []
#         self.answers: List[str] = []
#         self.tech_count = 0
#         self.hr_index = 0

#     def next_question(self) -> str:
#         """
#         Returns the next question based on current stage.
#         """
#         # Intro question (always first)
#         if self.stage == "INTRO":
#             question = "Introduce yourself."
#             self.stage = "TECHNICAL"
#             self.questions.append(question)
#             return question

#         # Technical / Deep Dive questions
#         if self.stage == "TECHNICAL":
#             if self.tech_count < self.MAX_TECH_QUESTIONS:
#                 question = generate_question(
#                     job_description=self.job_description,
#                     resume=self.resume_text,
#                     stage=self.stage
#                 )
#                 self.tech_count += 1
#                 self.questions.append(question)
#                 # After reaching max tech questions, move to HR
#                 if self.tech_count >= self.MAX_TECH_QUESTIONS:
#                     self.stage = "HR"
#                 return question

#         # HR / Behavioral questions
#         if self.stage == "HR":
#             if self.hr_index < len(self.HR_QUESTIONS):
#                 question = self.HR_QUESTIONS[self.hr_index]
#                 self.hr_index += 1
#                 self.questions.append(question)
#                 return question
#             else:
#                 # No more questions
#                 return None

#     def save_answer(self, answer: str):
#         self.answers.append(answer)

# # In-memory session store
# _sessions: Dict[str, InterviewSession] = {}

# def create_session(resume_text: str, job_description: str) -> str:
#     session_id = str(uuid.uuid4())
#     _sessions[session_id] = InterviewSession(
#         resume_text=resume_text,
#         job_description=job_description
#     )
#     return session_id

# def get_session(session_id: str) -> InterviewSession:
#     return _sessions.get(session_id)




# import uuid
# from typing import Dict, List, Optional
# from app.services.question_generator import generate_question


# class InterviewSession:
#     HR_QUESTIONS = [
#         "Can you describe a situation where you faced a challenge and how you handled it?",
#         "How do you prioritize tasks when working on multiple projects?",
#         "Tell me about a time you worked in a team and faced conflict. How did you resolve it?",
#         "Describe a time you had to learn a new technology quickly. How did you approach it?",
#         "What motivates you in your professional career?"
#     ]

#     MAX_TECH_QUESTIONS = 5
#     MAX_DEEP_DIVE_QUESTIONS = 2

#     def __init__(self, resume_text: str, job_description: str):
#         self.resume_text = resume_text
#         self.job_description = job_description

#         self.stage = "INTRO"  # INTRO → TECHNICAL → DEEP_DIVE → HR → DONE
#         self.answers: List[str] = []

#         self.tech_count = 0
#         self.deep_dive_count = 0
#         self.hr_index = 0

#         self.completed = False

#     def next_question(self) -> Optional[str]:
#         """
#         Returns the next interview question.
#         Returns None ONLY when interview is fully completed.
#         """

#         if self.completed:
#             return None

#         # ---------------- INTRO ----------------
#         if self.stage == "INTRO":
#             self.stage = "TECHNICAL"
#             return "Please introduce yourself."

#         # ---------------- TECHNICAL ----------------
#         if self.stage == "TECHNICAL":
#             if self.tech_count < self.MAX_TECH_QUESTIONS:
#                 self.tech_count += 1
#                 return generate_question(
#                     job_description=self.job_description,
#                     resume=self.resume_text,
#                     stage="TECHNICAL"
#                 )
#             else:
#                 self.stage = "DEEP_DIVE"

#         # ---------------- DEEP DIVE ----------------
#         if self.stage == "DEEP_DIVE":
#             if self.deep_dive_count < self.MAX_DEEP_DIVE_QUESTIONS:
#                 self.deep_dive_count += 1
#                 return generate_question(
#                     job_description=self.job_description,
#                     resume=self.resume_text,
#                     stage="DEEP_DIVE"
#                 )
#             else:
#                 self.stage = "HR"

#         # ---------------- HR ----------------
#         if self.stage == "HR":
#             if self.hr_index < len(self.HR_QUESTIONS):
#                 question = self.HR_QUESTIONS[self.hr_index]
#                 self.hr_index += 1
#                 return question
#             else:
#                 self.stage = "DONE"
#                 self.completed = True
#                 return (
#                     "Thank you for completing the interview. "
#                     "You may now click 'Stop' to end the session."
#                 )

#         return None

#     def save_answer(self, answer: str):
#         if answer and not self.completed:
#             self.answers.append(answer)


# # ---------------- SESSION STORE ----------------

# _sessions: Dict[str, InterviewSession] = {}


# def create_session(resume_text: str, job_description: str) -> str:
#     session_id = str(uuid.uuid4())
#     _sessions[session_id] = InterviewSession(
#         resume_text=resume_text,
#         job_description=job_description
#     )
#     return session_id


# def get_session(session_id: str) -> Optional[InterviewSession]:
#     return _sessions.get(session_id)


import uuid
from typing import Dict, List
from app.services.question_generator import generate_question

class InterviewSession:
    HR_QUESTIONS = [
        "Can you describe a situation where you faced a challenge and how you handled it?",
        "How do you prioritize tasks when working on multiple projects?",
        "Tell me about a time you worked in a team and faced conflict. How did you resolve it?",
        "Describe a time you had to learn a new technology quickly. How did you approach it?",
        "What motivates you in your professional career?"
    ]

    MAX_TECH_QUESTIONS = 5
    MAX_DEEP_DIVE_QUESTIONS = 2

    def __init__(self, resume_text: str, job_description: str):
        self.resume_text = resume_text
        self.job_description = job_description
        self.stage = "INTRO"  # INTRO -> TECHNICAL -> DEEP_DIVE -> HR
        self.questions: List[str] = ["Please introduce yourself."]
        self.answers: List[str] = []
        self.current_index = 0
        self.completed = False
        self.tech_count = 0
        self.deep_dive_count = 0
        self.hr_index = 0

    def next_question(self) -> str:
        if self.completed:
            return None

        # INTRO stage
        if self.stage == "INTRO":
            self.stage = "TECHNICAL"
            return self.questions[0]

        # TECHNICAL stage
        if self.stage == "TECHNICAL":
            if self.tech_count < self.MAX_TECH_QUESTIONS:
                question = generate_question(
                    job_description=self.job_description,
                    resume=self.resume_text,
                    stage="TECHNICAL"
                )
                self.questions.append(question)
                self.tech_count += 1
                return question
            else:
                self.stage = "DEEP_DIVE"

        # DEEP_DIVE stage
        if self.stage == "DEEP_DIVE":
            if self.deep_dive_count < self.MAX_DEEP_DIVE_QUESTIONS:
                question = generate_question(
                    job_description=self.job_description,
                    resume=self.resume_text,
                    stage="DEEP_DIVE"
                )
                self.questions.append(question)
                self.deep_dive_count += 1
                return question
            else:
                self.stage = "HR"

        # HR stage
        if self.stage == "HR":
            if self.hr_index < len(self.HR_QUESTIONS):
                question = self.HR_QUESTIONS[self.hr_index]
                self.hr_index += 1
                return question
            else:
                self.completed = True
                return "Thank you for your interview. You may now click 'Stop' to end the session."

    def save_answer(self, answer: str):
        if answer:
            self.answers.append(answer)

# Session store
_sessions: Dict[str, InterviewSession] = {}

def create_session(resume_text: str, job_description: str) -> str:
    session_id = str(uuid.uuid4())
    _sessions[session_id] = InterviewSession(
        resume_text=resume_text,
        job_description=job_description
    )
    return session_id

def get_session(session_id: str) -> InterviewSession:
    return _sessions.get(session_id)
