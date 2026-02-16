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




# # backend/app/services/interview_state.py

# import uuid
# import time
# from typing import Dict, List, Optional

# from app.services.question_generator import generate_question
# from app.services.evaluator import score_answer, set_current_question
# from app.services.llm_feedback import generate_feedback


# class InterviewSession:

#     MAX_TECH_QUESTIONS = 10
#     MAX_RETRY = 5

#     SESSION_LIMIT_SECONDS = 45 * 60
#     GRACE_PERIOD_SECONDS = 2 * 60

#     def __init__(self, resume_text: str, job_description: str):
#         self.resume_text = resume_text
#         self.job_description = job_description

#         self.stage = "INTRO"
#         self.expecting_answer = False
#         self.completed = False

#         self.questions: List[str] = []
#         self.answers: List[str] = []
#         self.scores: List[dict] = []

#         self.covered_projects: List[str] = []

#         self.current_topic: Optional[str] = None
#         self.topic_weakness: Dict[str, int] = {}

#         self.session_start_time = time.time()
#         self.current_question_start: Optional[float] = None
#         self.answer_durations: List[float] = []

#         self.feedback_text: str = ""
#         self.in_buffer_time = False

   
#     # TERMINATION LOGIC
  

#     def _main_time_exceeded(self) -> bool:
#         elapsed = time.time() - self.session_start_time
#         return elapsed >= self.SESSION_LIMIT_SECONDS

#     def _buffer_time_exceeded(self) -> bool:
#         elapsed = time.time() - self.session_start_time
#         return elapsed >= (self.SESSION_LIMIT_SECONDS + self.GRACE_PERIOD_SECONDS)

#     def _question_limit_reached(self) -> bool:
#         total_allowed = self.MAX_TECH_QUESTIONS + 1 
#         return len(self.answers) >= total_allowed

#     def _should_end_interview(self) -> bool:
#         return self.completed or self._buffer_time_exceeded()

#     def _finalize_interview(self, force_save_current_answer: bool = False):
#         if self.completed:
#             return

#         # If buffer time expired and user is still answering, save what they have
#         if force_save_current_answer and self.expecting_answer and len(self.questions) > len(self.answers):
#             # User was in middle of answering - save empty answer
#             current_question = self.questions[-1]
#             self.answers.append("Answer not completed (time expired)")
            
#             if self.current_question_start:
#                 self.answer_durations.append(
#                     round(time.time() - self.current_question_start, 2)
#                 )
#             else:
#                 self.answer_durations.append(0.0)
            
#             # Score the incomplete answer
#             set_current_question(current_question)
#             score = score_answer("Answer not completed (time expired)", current_question)
#             self.scores.append(score)

#         self.completed = True
#         self.expecting_answer = False
#         self.current_question_start = None
        
#         # ALWAYS generate feedback
#         self.generate_feedback()

#     # HELPERS

#     def _is_duplicate(self, question: str) -> bool:
#         return question.strip() in self.questions

#     def _detect_topic(self, question: str) -> Optional[str]:
#         for project in self.covered_projects:
#             if project.lower() in question.lower():
#                 return project
#         return None

#     def _classify_answer(self, score: float) -> str:
#         if score >= 0.75:
#             return "STRONG"
#         elif score >= 0.40:
#             return "CONFUSED"
#         return "WEAK"

#     def _decide_next_stage(self, topic: Optional[str], classification: str) -> str:
#         if not topic:
#             return "TECH_SWITCH"

#         if classification == "STRONG":
#             self.topic_weakness[topic] = 0
#             return "TECH_DEEPEN"

#         if classification == "CONFUSED":
#             return "TECH_CLARIFY"

#         self.topic_weakness[topic] = self.topic_weakness.get(topic, 0) + 1
#         return "TECH_SWITCH" if self.topic_weakness[topic] >= 2 else "TECH_SIMPLIFY"

#     def _generate_unique_question(self, stage: str) -> str:
#         for _ in range(self.MAX_RETRY):
#             result = generate_question(
#                 job_description=self.job_description,
#                 resume=self.resume_text,
#                 stage=stage,
#                 questions_count=len(self.questions),
#                 covered_projects=self.covered_projects,
#                 previous_questions=self.questions
#             )
#             q = result.get("question", "").strip()
#             self.covered_projects = result.get("covered_projects", self.covered_projects)

#             if q and not self._is_duplicate(q):
#                 return q

#         return "Can you explain a technical decision you made recently?"

#     # INTERVIEW FLOW

#     def next_question(self) -> Optional[str]:
        
#         # Check buffer time expiration
#         if self._buffer_time_exceeded():
#             self._finalize_interview(force_save_current_answer=True)
#             return None

#         # Already completed
#         if self.completed:
#             return None

#         # Check if main time exceeded (enter buffer period)
#         if self._main_time_exceeded() and not self.in_buffer_time:
#             self.in_buffer_time = True
#             print(f"[INTERVIEW] Entered buffer time (2 minutes remaining)")

#         # Don't allow new question if waiting for answer
#         if self.expecting_answer:
#             return None

#         # Check if question limit reached
#         if self._question_limit_reached():
#             self._finalize_interview()
#             return None

#         self.expecting_answer = True

#         # Generate question
#         if self.stage == "INTRO":
#             q = "Please briefly introduce yourself and your professional background."
#             self.stage = "TECH_SWITCH"
#         else:
#             q = self._generate_unique_question(self.stage)

#         self.questions.append(q)
#         self.current_topic = self._detect_topic(q)
#         self.current_question_start = time.time()
        
#         return q

#     def save_answer(self, answer: str):
#         if self.completed or not self.expecting_answer:
#             return

#         # Check if buffer time expired
#         if self._buffer_time_exceeded():
#             self._finalize_interview(force_save_current_answer=False)
#             return

#         answer_text = answer.strip() or "No answer provided"
#         question = self.questions[-1]

#         # Track duration
#         if self.current_question_start:
#             self.answer_durations.append(
#                 round(time.time() - self.current_question_start, 2)
#             )
#         else:
#             self.answer_durations.append(0.0)

#         self.current_question_start = None

#         # Score answer
#         set_current_question(question)
#         score = score_answer(answer_text, question)

#         self.answers.append(answer_text)
#         self.scores.append(score)

#         # Adaptive logic
#         classification = self._classify_answer(score["final_score"])
#         self.stage = self._decide_next_stage(self.current_topic, classification)

#         self.expecting_answer = False

#     # FEEDBACK & RESULT
 

#     def generate_feedback(self):
#         """Generate feedback even for partial interviews"""
#         qa_list = []
#         for i, q in enumerate(self.questions):
#             ans = self.answers[i] if i < len(self.answers) else "No answer provided"
#             sc = self.scores[i] if i < len(self.scores) else score_answer(ans, q)
#             qa_list.append({"question": q, "answer": ans, "scores": sc})

#         # Calculate average only from answered questions
#         if self.scores:
#             avg_score = round(
#                 sum(s["final_score"] for s in self.scores) / len(self.scores), 2
#             )
#         else:
#             avg_score = 0.0

#         self.feedback_text = generate_feedback(qa_list, avg_score)

#     def final_result(self) -> dict:
#         total_time = round(time.time() - self.session_start_time, 2)
        
#         # Calculate average only from answered questions
#         if self.scores:
#             avg_score = round(
#                 sum(s["final_score"] for s in self.scores) / len(self.scores), 2
#             )
#         else:
#             avg_score = 0.0

#         return {
#             "average_score": avg_score,
#             "result": "PASS" if avg_score >= 0.7 else "FAIL",
#             "total_duration_seconds": total_time,
#             "time_per_answer_seconds": self.answer_durations,
#             "questions": self.questions,
#             "answers": self.answers,
#             "scores": self.scores,
#             "feedback": self.feedback_text,
#             "covered_projects": self.covered_projects,
#             "completion_reason": self._get_completion_reason(),
#             "questions_answered": len(self.answers),
#             "questions_asked": len(self.questions)
#         }

#     def _get_completion_reason(self) -> str:
#         if self._buffer_time_exceeded():
#             return "TIME_LIMIT_EXCEEDED"
#         elif self._question_limit_reached():
#             return "QUESTION_LIMIT_REACHED"
#         else:
#             return "COMPLETED_NORMALLY"

#     def get_remaining_time(self) -> int:
#         elapsed = time.time() - self.session_start_time
#         total_allowed = self.SESSION_LIMIT_SECONDS + self.GRACE_PERIOD_SECONDS
#         remaining = max(total_allowed - elapsed, 0)
#         return int(remaining)

#     def is_in_buffer_time(self) -> bool:
#         elapsed = time.time() - self.session_start_time
#         return elapsed >= self.SESSION_LIMIT_SECONDS and elapsed < (self.SESSION_LIMIT_SECONDS + self.GRACE_PERIOD_SECONDS)



# # SESSION STORE

# _sessions: Dict[str, InterviewSession] = {}


# def create_session(session_id: str, job_description: str, resume_text: str) -> str:
#     _sessions[session_id] = InterviewSession(
#         resume_text=resume_text,
#         job_description=job_description
#     )
#     return session_id


# def get_session(session_id: str) -> Optional[InterviewSession]:
#     return _sessions.get(session_id)



# # backend/app/services/interview_state.py

# import uuid
# import time
# from typing import Dict, List, Optional

# from app.services.question_generator import generate_question
# from app.services.evaluator import score_answer
# from app.services.llm_feedback import generate_feedback

# import threading  # for session store make thread safe


# class InterviewSession:

#     MAX_TECH_QUESTIONS = 10
#     MAX_RETRY = 5

#     SESSION_LIMIT_SECONDS = 45 * 60
#     GRACE_PERIOD_SECONDS = 2 * 60

#     def __init__(self, resume_text: str, job_description: str):
#         self.resume_text = resume_text
#         self.job_description = job_description

#         self.stage = "INTRO"
#         self.expecting_answer = False
#         self.completed = False

#         self.questions: List[str] = []
#         self.answers: List[str] = []
#         self.scores: List[dict] = []

#         self.covered_projects: List[str] = []

#         self.current_topic: Optional[str] = None
#         self.topic_weakness: Dict[str, int] = {}

#         self.session_start_time = time.time()
        
#         # TIME TRACKING FOR PAUSES (AI Speaking)
#         self.total_paused_duration = 0.0
#         self.current_pause_start: Optional[float] = None
        
#         self.current_question_start: Optional[float] = None
#         self.answer_durations: List[float] = []

#         self.feedback_text: str = ""
#         self.in_buffer_time = False

#     #  TIME CALCULATIONS (Adjusted for AI Speaking)

#     def pause_timer(self):
#         """Called when AI starts speaking (TTS)"""
#         if self.current_pause_start is None:
#             self.current_pause_start = time.time()
#             # If we are in the middle of a question timer, pause that too implicitly
#             # by noting the wall clock difference later.

#     def resume_timer(self):
#         """Called when AI stops speaking"""
#         if self.current_pause_start is not None:
#             paused_amount = time.time() - self.current_pause_start
#             self.total_paused_duration += paused_amount
#             self.current_pause_start = None

#     def get_effective_elapsed_time(self) -> float:
#         """
#         Returns the duration of the interview EXCLUDING time when AI was speaking.
#         """
#         wall_elapsed = time.time() - self.session_start_time
        
#         current_pause = 0.0
#         if self.current_pause_start is not None:
#             current_pause = time.time() - self.current_pause_start
            
#         return wall_elapsed - (self.total_paused_duration + current_pause)

#     #  TERMINATION LOGIC

#     def _main_time_exceeded(self) -> bool:
#         return self.get_effective_elapsed_time() >= self.SESSION_LIMIT_SECONDS

#     def _buffer_time_exceeded(self) -> bool:
#         return self.get_effective_elapsed_time() >= (self.SESSION_LIMIT_SECONDS + self.GRACE_PERIOD_SECONDS)

#     def _question_limit_reached(self) -> bool:
#         return len(self.answers) >= self.MAX_TECH_QUESTIONS

#     def _should_end_interview(self) -> bool:
#         return self.completed or self._buffer_time_exceeded()

#     def _finalize_interview(self, force_save_current_answer: bool = False):
#         if self.completed:
#             return
#         # Mark completed immediately (prevents race condition)
#         self.completed=True
#         self.expecting_answer = False

#         # if user was mid-answer and nothing saved yet
#         if(force_save_current_answer and len(self.questions) > len(self.answers)):
#             current_question = self.questions[-1]
#             self.answers.append("Answer not completed (time expired)")

#             if self.current_question_start:
#                 duration = time.time() - self.current_question_start
#             else:
#                 duration = 0.0
            
#             self.answer_durations.append(round(max(duration, 0),2))

#             score = score_answer(
#                 "answer not completed (time expired)",
#                 current_question
#             )
#             self.scores.append(score)
#         self.current_question_start = None

#         # GEnerate feedback exactly once 
#         self.generate_feedback()
        
       

#     # HELPERS

#     def _is_duplicate(self, question: str) -> bool:
#         return question.strip() in self.questions

#     def _detect_topic(self, question: str) -> Optional[str]:
#         for project in self.covered_projects:
#             if project.lower() in question.lower():
#                 return project
#         return None

#     def _classify_answer(self, score: float) -> str:
#         if score >= 0.75:
#             return "STRONG"
#         elif score >= 0.40:
#             return "CONFUSED"
#         return "WEAK"

#     def _decide_next_stage(self, topic: Optional[str], classification: str) -> str:
#         if not topic:
#             return "TECH_SWITCH"

#         if classification == "STRONG":
#             self.topic_weakness[topic] = 0
#             return "TECH_DEEPEN"

#         if classification == "CONFUSED":
#             return "TECH_CLARIFY"

#         self.topic_weakness[topic] = self.topic_weakness.get(topic, 0) + 1
#         return "TECH_SWITCH" if self.topic_weakness[topic] >= 2 else "TECH_SIMPLIFY"

#     def _generate_unique_question(self, stage: str) -> str:
#         for _ in range(self.MAX_RETRY):
#             result = generate_question(
#                 job_description=self.job_description,
#                 resume=self.resume_text,
#                 stage=stage,
#                 questions_count=len(self.questions),
#                 covered_projects=self.covered_projects,
#                 previous_questions=self.questions
#             )
#             q = result.get("question", "").strip()
#             self.covered_projects = result.get("covered_projects", self.covered_projects)

#             if q and not self._is_duplicate(q):
#                 return q

#         return "Can you explain a technical decision you made recently?"

#     # INTERVIEW FLOW

#     def next_question(self) -> Optional[str]:
        
#         # Check buffer time expiration
#         if self._buffer_time_exceeded():
#             self._finalize_interview(force_save_current_answer=True)
#             return None

#         # Already completed
#         if self.completed:
#             return None

#         # Check if main time exceeded (enter buffer period)
#         if self._main_time_exceeded() and not self.in_buffer_time:
#             self.in_buffer_time = True
#             print(f"[INTERVIEW] Entered buffer time (2 minutes remaining)")

#         # Don't allow new question if waiting for answer
#         if self.expecting_answer:
#             return None

#         # Check if question limit reached
#         if self._question_limit_reached():
#             self._finalize_interview()
#             return None

#         self.expecting_answer = True

#         # Generate question
#         if self.stage == "INTRO":
#             q = "Please briefly introduce yourself and your professional background."
#             self.stage = "TECH_SWITCH"
#         else:
#             q = self._generate_unique_question(self.stage)

#         self.questions.append(q)
#         self.current_topic = self._detect_topic(q)
#         self.current_question_start = time.time()
        
#         return q

#     def save_answer(self, answer: str):
#         if self.completed or not self.expecting_answer:
#             return

#         # Check if buffer time expired
#         if self._buffer_time_exceeded():
#             self._finalize_interview(force_save_current_answer=False)
#             return

#         answer_text = answer.strip() or "No answer provided"
#         question = self.questions[-1]

#         # Track duration
#         if self.current_question_start:
#             self.answer_durations.append(
#                 round(time.time() - self.current_question_start, 2)
#             )
#         else:
#             self.answer_durations.append(0.0)

#         self.current_question_start = None

#         # Score answer
#         score = score_answer(answer_text, question)

#         self.answers.append(answer_text)
#         self.scores.append(score)

#         # Adaptive logic
#         classification = self._classify_answer(score["final_score"])
#         self.stage = self._decide_next_stage(self.current_topic, classification)

#         self.expecting_answer = False

#     # FEEDBACK & RESULT
 
#     def generate_feedback(self):
#         """Generate feedback even for partial interviews"""
#         qa_list = []
#         for i, q in enumerate(self.questions):
#             ans = self.answers[i] if i < len(self.answers) else "No answer provided"
#             sc = self.scores[i] if i < len(self.scores) else score_answer(ans, q)
#             qa_list.append({"question": q, "answer": ans, "scores": sc})

#         # Calculate average only from answered questions
#         if self.scores:
#             avg_score = round(
#                 sum(s["final_score"] for s in self.scores) / len(self.scores), 2
#             )
#         else:
#             avg_score = 0.0

#         self.feedback_text = generate_feedback(qa_list, avg_score)

#     def final_result(self) -> dict:
#         total_time = round(self.get_effective_elapsed_time(), 2)
        
#         # Calculate average only from answered questions
#         if self.scores:
#             avg_score = round(
#                 sum(s["final_score"] for s in self.scores) / len(self.scores), 2
#             )
#         else:
#             avg_score = 0.0

#         return {
#             "average_score": avg_score,
#             "result": "PASS" if avg_score >= 0.7 else "FAIL",
#             "total_duration_seconds": total_time,
#             "time_per_answer_seconds": self.answer_durations,
#             "questions": self.questions,
#             "answers": self.answers,
#             "scores": self.scores,
#             "feedback": self.feedback_text,
#             "covered_projects": self.covered_projects,
#             "completion_reason": self._get_completion_reason(),
#             "questions_answered": len(self.answers),
#             "questions_asked": len(self.questions)
#         }

#     def _get_completion_reason(self) -> str:
#         if self._buffer_time_exceeded():
#             return "TIME_LIMIT_EXCEEDED"
#         elif self._question_limit_reached():
#             return "QUESTION_LIMIT_REACHED"
#         else:
#             return "COMPLETED_NORMALLY"


# # SESSION STORE

# _sessions: Dict[str, InterviewSession] = {}
# _sessions_lock = threading.Lock()


# def create_session(session_id: str, job_description: str, resume_text: str) -> str:
#     with _sessions_lock:
#         _sessions[session_id] = InterviewSession(
#             resume_text=resume_text,
#             job_description=job_description
#         )
#     return session_id


# def get_session(session_id: str) -> Optional[InterviewSession]:
#     with _sessions_lock:
#         return _sessions.get(session_id)


# backend/app/services/interview_state.py - CONTINUOUS TIMER (NO PAUSES)

import uuid
import time
from typing import Dict, List, Optional

from app.services.question_generator import generate_question
from app.services.evaluator import score_answer
from app.services.llm_feedback import generate_feedback

import threading


class InterviewSession:

    MAX_TECH_QUESTIONS = 10
    MAX_RETRY = 5

    SESSION_LIMIT_SECONDS = 45 * 60
    GRACE_PERIOD_SECONDS = 2 * 60

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

        # Timer starts when first question is sent (set in WebSocket)
        self.session_start_time: Optional[float] = None
        
        self.current_question_start: Optional[float] = None
        self.answer_durations: List[float] = []

        self.feedback_text: str = ""
        self.in_buffer_time = False

    # ─── TIME CALCULATION (SIMPLE) ───

    def get_elapsed_time(self) -> float:
        """Simple elapsed time - no pauses"""
        if not self.session_start_time:
            return 0.0
        return time.time() - self.session_start_time

    # ─── TERMINATION LOGIC ───

    def _main_time_exceeded(self) -> bool:
        return self.get_elapsed_time() >= self.SESSION_LIMIT_SECONDS

    def _buffer_time_exceeded(self) -> bool:
        return self.get_elapsed_time() >= (self.SESSION_LIMIT_SECONDS + self.GRACE_PERIOD_SECONDS)

    def _question_limit_reached(self) -> bool:
        return len(self.answers) >= self.MAX_TECH_QUESTIONS

    def _finalize_interview(self, force_save_current_answer: bool = False):
        if self.completed:
            return
        
        self.completed = True
        self.expecting_answer = False

        # If user was mid-answer
        if force_save_current_answer and len(self.questions) > len(self.answers):
            current_question = self.questions[-1]
            self.answers.append("Answer not completed (time expired)")

            if self.current_question_start:
                duration = time.time() - self.current_question_start
            else:
                duration = 0.0
            
            self.answer_durations.append(round(max(duration, 0), 2))

            score = score_answer(
                "Answer not completed (time expired)",
                current_question
            )
            self.scores.append(score)
        
        self.current_question_start = None

        # Generate feedback
        self.generate_feedback()

    # ─── HELPERS ───

    def _is_duplicate(self, question: str) -> bool:
        return question.strip() in self.questions

    def _detect_topic(self, question: str) -> Optional[str]:
        for project in self.covered_projects:
            if project.lower() in question.lower():
                return project
        return None

    def _classify_answer(self, score: float) -> str:
        if score >= 0.75:
            return "STRONG"
        elif score >= 0.40:
            return "CONFUSED"
        return "WEAK"

    def _decide_next_stage(self, topic: Optional[str], classification: str) -> str:
        if not topic:
            return "TECH_SWITCH"

        if classification == "STRONG":
            self.topic_weakness[topic] = 0
            return "TECH_DEEPEN"

        if classification == "CONFUSED":
            return "TECH_CLARIFY"

        self.topic_weakness[topic] = self.topic_weakness.get(topic, 0) + 1
        return "TECH_SWITCH" if self.topic_weakness[topic] >= 2 else "TECH_SIMPLIFY"

    def _generate_unique_question(self, stage: str) -> str:
        """Generate question - timer continues running"""
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

    # ─── INTERVIEW FLOW ───

    def next_question(self) -> Optional[str]:
        """Generate next question - timer continues"""
        
        # Check buffer time expiration
        if self._buffer_time_exceeded():
            self._finalize_interview(force_save_current_answer=True)
            return None

        # Already completed
        if self.completed:
            return None

        # Check if main time exceeded
        if self._main_time_exceeded() and not self.in_buffer_time:
            self.in_buffer_time = True
            print(f"[INTERVIEW] Entered buffer time (2 minutes remaining)")

        # Don't allow new question if waiting for answer
        if self.expecting_answer:
            return None

        # Check if question limit reached
        if self._question_limit_reached():
            self._finalize_interview()
            return None

        self.expecting_answer = True

        # Generate question (timer continues)
        if self.stage == "INTRO":
            q = "Please briefly introduce yourself and your professional background."
            self.stage = "TECH_SWITCH"
        else:
            q = self._generate_unique_question(self.stage)

        self.questions.append(q)
        self.current_topic = self._detect_topic(q)
        self.current_question_start = time.time()
        
        return q

    def save_answer(self, answer: str):
        """Save answer - timer continues"""
        if self.completed or not self.expecting_answer:
            return

        # Check if buffer time expired
        if self._buffer_time_exceeded():
            self._finalize_interview(force_save_current_answer=False)
            return

        answer_text = answer.strip() or "No answer provided"
        question = self.questions[-1]

        # Track duration
        if self.current_question_start:
            self.answer_durations.append(
                round(time.time() - self.current_question_start, 2)
            )
        else:
            self.answer_durations.append(0.0)

        self.current_question_start = None

        # Score answer
        score = score_answer(answer_text, question)

        self.answers.append(answer_text)
        self.scores.append(score)

        # Adaptive logic
        classification = self._classify_answer(score["final_score"])
        self.stage = self._decide_next_stage(self.current_topic, classification)

        self.expecting_answer = False

    # ─── FEEDBACK & RESULT ───
 
    def generate_feedback(self):
        """Generate feedback - timer continues (or interview is over)"""
        qa_list = []
        for i, q in enumerate(self.questions):
            ans = self.answers[i] if i < len(self.answers) else "No answer provided"
            sc = self.scores[i] if i < len(self.scores) else score_answer(ans, q)
            qa_list.append({"question": q, "answer": ans, "scores": sc})

        if self.scores:
            avg_score = round(
                sum(s["final_score"] for s in self.scores) / len(self.scores), 2
            )
        else:
            avg_score = 0.0

        self.feedback_text = generate_feedback(qa_list, avg_score)

    def final_result(self) -> dict:
        total_time = round(self.get_elapsed_time(), 2)
        
        if self.scores:
            avg_score = round(
                sum(s["final_score"] for s in self.scores) / len(self.scores), 2
            )
        else:
            avg_score = 0.0

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
            "completion_reason": self._get_completion_reason(),
            "questions_answered": len(self.answers),
            "questions_asked": len(self.questions)
        }

    def _get_completion_reason(self) -> str:
        if self._buffer_time_exceeded():
            return "TIME_LIMIT_EXCEEDED"
        elif self._question_limit_reached():
            return "QUESTION_LIMIT_REACHED"
        else:
            return "COMPLETED_NORMALLY"


# ─── SESSION STORE ───

_sessions: Dict[str, InterviewSession] = {}
_sessions_lock = threading.Lock()


def create_session(session_id: str, job_description: str, resume_text: str) -> str:
    with _sessions_lock:
        _sessions[session_id] = InterviewSession(
            resume_text=resume_text,
            job_description=job_description
        )
    return session_id


def get_session(session_id: str) -> Optional[InterviewSession]:
    with _sessions_lock:
        return _sessions.get(session_id)