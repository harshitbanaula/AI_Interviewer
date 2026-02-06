# backend/app/services/interview_state.py

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
#         """
#         Generate a unique question and update covered_projects.
#         Returns just the question string.
#         """
#         for _ in range(self.MAX_RETRY):
#             # Pass previous questions to avoid repetitive phrasing
#             result = generate_question(
#                 job_description=self.job_description,
#                 resume=self.resume_text,
#                 stage=stage,
#                 questions_count=len(self.questions),
#                 covered_projects=self.covered_projects,
#                 previous_questions=self.questions
#             )
            
#             if isinstance(result, dict):
#                 q = result.get("question", "")
#                 self.covered_projects = result.get("covered_projects", self.covered_projects)
#             else:
#                 q = result
            
#             if q and not self._is_duplicate(q):
#                 return q

#         # Fallback question if retries fail
#         return "Can you explain a technical decision you made recently and why?"

#     # --------------------------------------------------
#     # Interview Flow
#     # --------------------------------------------------

#     def next_question(self) -> str | None:
#         """
#         Generate next question. Returns a STRING (not dict).
#         """
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
#             "feedback": self.feedback_text,
#             "covered_projects": self.covered_projects
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








# backend/app/services/interview_state.py

import uuid
import time
from typing import Dict, List, Optional

from app.services.question_generator import generate_question
from app.services.evaluator import score_answer, set_current_question
from app.services.llm_feedback import generate_feedback


class InterviewSession:

    MAX_TECH_QUESTIONS = 10
    MAX_RETRY = 5

    SESSION_LIMIT_SECONDS = 45 * 60  # 45 minutes
    GRACE_PERIOD_SECONDS = 2 * 60    # 2 minutes grace period

    def __init__(self, resume_text: str, job_description: str):
        self.resume_text = resume_text
        self.job_description = job_description

        self.stage = "INTRO"
        self.expecting_answer = False
        self.completed = False

        self.questions: List[str] = []
        self.answers: List[str] = []
        self.scores: List[dict] = []

        self.covered_projects: List[str] = []

        self.current_topic: Optional[str] = None
        self.topic_weakness: Dict[str, int] = {}

        self.session_start_time = time.time()
        self.current_question_start: Optional[float] = None
        self.answer_durations: List[float] = []

        self.feedback_text: str = ""

    # =======================
    # TERMINATION LOGIC
    # =======================

    def _time_exceeded(self) -> bool:
        """Check if total time limit exceeded (including grace period)"""
        elapsed = time.time() - self.session_start_time
        return elapsed >= (self.SESSION_LIMIT_SECONDS + self.GRACE_PERIOD_SECONDS)

    def _question_limit_reached(self) -> bool:
        """Check if maximum questions asked (INTRO + MAX_TECH_QUESTIONS)"""
        return len(self.questions) >= (self.MAX_TECH_QUESTIONS + 1)

    def _should_end_interview(self) -> bool:
        """Determine if interview should end"""
        return self.completed or self._time_exceeded() or self._question_limit_reached()

    def _finalize_interview(self):
        """Force finalize the interview and generate feedback"""
        if self.completed:
            return  # Already finalized

        self.completed = True
        self.expecting_answer = False
        self.current_question_start = None
        
        # CRITICAL: Always generate feedback when finalizing
        self.generate_feedback()

    # =======================
    # HELPERS
    # =======================

    def _is_duplicate(self, question: str) -> bool:
        return question.strip() in self.questions

    def _detect_topic(self, question: str) -> Optional[str]:
        """Detect which project/topic this question is about"""
        for project in self.covered_projects:
            if project.lower() in question.lower():
                return project
        return None

    def _classify_answer(self, score: float) -> str:
        """Classify answer quality to determine next action"""
        if score >= 0.75:
            return "STRONG"
        elif score >= 0.40:
            return "CONFUSED"
        return "WEAK"

    def _decide_next_stage(self, topic: Optional[str], classification: str) -> str:
        """Adaptive logic: decide what type of question to ask next"""
        if not topic:
            return "TECH_SWITCH"

        if classification == "STRONG":
            self.topic_weakness[topic] = 0
            return "TECH_DEEPEN"

        if classification == "CONFUSED":
            return "TECH_CLARIFY"

        # WEAK answer
        self.topic_weakness[topic] = self.topic_weakness.get(topic, 0) + 1
        return "TECH_SWITCH" if self.topic_weakness[topic] >= 2 else "TECH_SIMPLIFY"

    def _generate_unique_question(self, stage: str) -> str:
        """Generate a unique question using LLM"""
        for _ in range(self.MAX_RETRY):
            result = generate_question(
                job_description=self.job_description,
                resume=self.resume_text,
                stage=stage,
                questions_count=len(self.questions),
                covered_projects=self.covered_projects,
                previous_questions=self.questions
            )
            q = result.get("question", "").strip()
            self.covered_projects = result.get("covered_projects", self.covered_projects)

            if q and not self._is_duplicate(q):
                return q

        return "Can you explain a technical decision you made recently?"

    # =======================
    # INTERVIEW FLOW
    # =======================

    def next_question(self) -> Optional[str]:
        """
        Generate and return the next question.
        Returns None if interview should end.
        """
        # HARD STOP - check all termination conditions
        if self._should_end_interview():
            self._finalize_interview()
            return None

        # Do NOT allow skipping answers
        if self.expecting_answer:
            return None

        # Double-check question limit before generating
        if self._question_limit_reached():
            self._finalize_interview()
            return None

        self.expecting_answer = True

        # Generate question based on stage
        if self.stage == "INTRO":
            q = "Please briefly introduce yourself and your professional background."
            self.stage = "TECH_SWITCH"  # Move to technical questions
        else:
            q = self._generate_unique_question(self.stage)

        # Track question
        self.questions.append(q)
        self.current_topic = self._detect_topic(q)
        self.current_question_start = time.time()
        
        return q

    def save_answer(self, answer: str):
        """
        Save the candidate's answer and adaptively decide next question type.
        """
        # Ignore if not expecting answer or already completed
        if self.completed or not self.expecting_answer:
            return

        # Check time limit before processing
        if self._time_exceeded():
            self._finalize_interview()
            return

        answer_text = answer.strip() or "No answer provided"
        question = self.questions[-1]

        # Track answer duration
        if self.current_question_start:
            self.answer_durations.append(
                round(time.time() - self.current_question_start, 2)
            )
        else:
            self.answer_durations.append(0.0)

        self.current_question_start = None

        # Score the answer
        set_current_question(question)
        score = score_answer(answer_text, question)

        self.answers.append(answer_text)
        self.scores.append(score)

        # Adaptive logic: determine next question type
        classification = self._classify_answer(score["final_score"])
        self.stage = self._decide_next_stage(self.current_topic, classification)

        self.expecting_answer = False

        # Check if we've reached question limit after saving answer
        if self._question_limit_reached():
            self._finalize_interview()

    # =======================
    # FEEDBACK & RESULT
    # =======================

    def generate_feedback(self):
        """Generate comprehensive feedback using LLM"""
        qa_list = []
        for i, q in enumerate(self.questions):
            ans = self.answers[i] if i < len(self.answers) else "No answer provided"
            sc = self.scores[i] if i < len(self.scores) else score_answer(ans, q)
            qa_list.append({
                "question": q,
                "answer": ans,
                "scores": sc
            })

        avg_score = round(
            sum(s["final_score"] for s in self.scores) / len(self.scores), 2
        ) if self.scores else 0.0

        # Generate LLM-based feedback
        self.feedback_text = generate_feedback(qa_list, avg_score)

    def final_result(self) -> dict:
        """Return complete interview results"""
        total_time = round(time.time() - self.session_start_time, 2)
        avg_score = round(
            sum(s["final_score"] for s in self.scores) / len(self.scores), 2
        ) if self.scores else 0.0

        return {
            "average_score": avg_score,
            "result": "PASS" if avg_score >= 0.7 else "FAIL",
            "total_duration_seconds": total_time,
            "time_per_answer_seconds": self.answer_durations,
            "questions": self.questions,
            "answers": self.answers,
            "scores": self.scores,
            "feedback": self.feedback_text,
            "covered_projects": self.covered_projects,
            "completion_reason": self._get_completion_reason()
        }

    def _get_completion_reason(self) -> str:
        """Determine why the interview ended"""
        if self._time_exceeded():
            return "TIME_LIMIT_EXCEEDED"
        elif self._question_limit_reached():
            return "QUESTION_LIMIT_REACHED"
        else:
            return "COMPLETED_NORMALLY"

    def get_remaining_time(self) -> int:
        """Get remaining time in seconds"""
        elapsed = time.time() - self.session_start_time
        remaining = max(self.SESSION_LIMIT_SECONDS - elapsed, 0)
        return int(remaining)


# SESSION STORE


_sessions: Dict[str, InterviewSession] = {}


def create_session(session_id: str, job_description: str, resume_text: str) -> str:
    """
    Create a new interview session with given ID.
    Note: session_id is passed in (generated by caller)
    """
    _sessions[session_id] = InterviewSession(
        resume_text=resume_text,
        job_description=job_description
    )
    return session_id


def get_session(session_id: str) -> Optional[InterviewSession]:
    """Retrieve an existing session"""
    return _sessions.get(session_id)