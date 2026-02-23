## backend/app/services/interview_state.py

import time
import threading
from typing import Dict, List, Optional

from app.services.question_generator import generate_question
from app.services.evaluator import score_answer
from app.services.llm_feedback import generate_feedback


# ─── SESSION TTL CONFIGURATION ───
SESSION_TTL_SECONDS = 2 * 60 * 60
COMPLETED_TTL_SECONDS = 30 * 60
CLEANUP_INTERVAL_SECONDS = 15 * 60


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

        self.is_finalized = False
        self.completion_reason: Optional[str] = None
        self._finalize_lock = threading.Lock()

        self.questions: List[str] = []
        self.answers: List[str] = []
        self.scores: List[dict] = []

        self.covered_projects: List[str] = []

        self.current_topic: Optional[str] = None
        self.topic_weakness: Dict[str, int] = {}

        self.session_start_time: Optional[float] = None

        self.created_at: float = time.time()
        self.completed_at: Optional[float] = None

        self.current_question_start: Optional[float] = None
        self.answer_durations: List[float] = []

        self.feedback_text: str = ""
        self.in_buffer_time = False

        self._state_lock = threading.Lock()

    # ─── TIME CALCULATION ───
    def get_elapsed_time(self) -> float:
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


    # CENTRALIZED FINALIZATION - SINGLE POINT OF COMPLETION
    
    def finalize(self, force_save_current_answer: bool = False, reason: Optional[str] = None):
        with self._finalize_lock:
            # ── STEP 1: Check if already finalized ──
            with self._state_lock:
                if self.is_finalized:
                    print(f"[FINALIZE] Already finalized, skipping")
                    return

                # Mark as finalized FIRST to prevent double-finalization
                self.is_finalized = True
                self.completed = True
                self.expecting_answer = False
                self.completed_at = time.time()

                # Determine completion reason
                if reason:
                    self.completion_reason = reason
                else:
                    if self._buffer_time_exceeded():
                        self.completion_reason = "TIME_LIMIT_EXCEEDED"
                    elif self._question_limit_reached():
                        self.completion_reason = "QUESTION_LIMIT_REACHED"
                    else:
                        self.completion_reason = "COMPLETED_NORMALLY"

                print(f"[FINALIZE] Reason: {self.completion_reason}")

                # ── STEP 2: Save incomplete answer if needed ──
                if force_save_current_answer and len(self.questions) > len(self.answers):
                    current_question = self.questions[-1]
                    incomplete_answer = "Answer not completed (time expired)"
                    
                    self.answers.append(incomplete_answer)

                    duration = round(
                        max(time.time() - self.current_question_start, 0), 2
                    ) if self.current_question_start else 0.0

                    self.answer_durations.append(duration)
                    
                    # Score the incomplete answer
                    score = score_answer(incomplete_answer, current_question)
                    self.scores.append(score)
                    
                    print(f"[FINALIZE] Saved incomplete answer for Q{len(self.questions)}")

                self.current_question_start = None

            # ── STEP 3: Generate feedback (outside lock, can be slow) ──
            print(f"[FINALIZE] Generating feedback...")
            self._generate_feedback_sync()
            print(f"[FINALIZE] Feedback generated: {len(self.feedback_text)} chars")

    def _generate_feedback_sync(self):
        if not self.questions or not self.answers:
            self.feedback_text = "No answers provided to generate feedback."
            return

        try:
            # Build Q&A list for feedback generation
            qa_list = []
            for i, q in enumerate(self.questions):
                ans = self.answers[i] if i < len(self.answers) else "No answer provided"
                sc = self.scores[i] if i < len(self.scores) else score_answer(ans, q)
                qa_list.append({
                    "question": q,
                    "answer": ans,
                    "scores": sc
                })

            # Calculate average score
            avg_score = round(
                sum(s["final_score"] for s in self.scores) / len(self.scores), 2
            ) if self.scores else 0.0

            print(f"[FEEDBACK] Generating for {len(qa_list)} Q&A pairs, avg score: {avg_score}")

            # Generate feedback using LLM
            self.feedback_text = generate_feedback(qa_list, avg_score)

            if not self.feedback_text or self.feedback_text.strip() == "":
                self.feedback_text = f"Overall performance: {avg_score:.2f}/1.00. Interview completed with {len(self.answers)} answers."

            print(f"[FEEDBACK] Generated successfully")

        except Exception as e:
            print(f"[FEEDBACK] Error generating feedback: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback feedback
            avg_score = round(
                sum(s["final_score"] for s in self.scores) / len(self.scores), 2
            ) if self.scores else 0.0
            
            self.feedback_text = f"Interview completed. Average score: {avg_score:.2f}/1.00. Answered {len(self.answers)} of {len(self.questions)} questions."

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
        
        # Check termination conditions BEFORE acquiring lock
        if self._buffer_time_exceeded():
            print(f"[NEXT_QUESTION] Buffer time exceeded, finalizing")
            self.finalize(force_save_current_answer=True, reason="TIME_LIMIT_EXCEEDED")
            return None
        
        if self._question_limit_reached():
            print(f"[NEXT_QUESTION] Question limit reached, finalizing")
            self.finalize(reason="QUESTION_LIMIT_REACHED")
            return None

        with self._state_lock:
            if self.is_finalized or self.completed:
                return None

            if self._main_time_exceeded() and not self.in_buffer_time:
                self.in_buffer_time = True
                print(f"[NEXT_QUESTION] Entered buffer time")

            if self.expecting_answer:
                return None

            # Reserve slot
            self.expecting_answer = True
            current_stage = self.stage
            is_intro = current_stage == "INTRO"

            if is_intro:
                self.stage = "TECH_SWITCH"

        # Generate question (outside lock)
        if is_intro:
            q = "Please briefly introduce yourself and your professional background."
        else:
            q = self._generate_unique_question(current_stage)

        # Write result
        with self._state_lock:
            if self.is_finalized or self.completed:
                self.expecting_answer = False
                return None

            self.questions.append(q)
            self.current_topic = self._detect_topic(q)
            self.current_question_start = time.time()

        return q

    def save_answer(self, answer: str):        
        if self._buffer_time_exceeded():
            print(f"[SAVE_ANSWER] Buffer time exceeded during save, finalizing")
            self.finalize(force_save_current_answer=False, reason="TIME_LIMIT_EXCEEDED")
            return
        
        with self._state_lock:
            if self.is_finalized or self.completed or not self.expecting_answer:
                return

            answer_text = answer.strip() or "No answer provided"
            question = self.questions[-1]

            duration = round(time.time() - self.current_question_start, 2) \
                if self.current_question_start else 0.0
            self.answer_durations.append(duration)

            self.current_question_start = None

            # Score answer
            score = score_answer(answer_text, question)

            self.answers.append(answer_text)
            self.scores.append(score)

            classification = self._classify_answer(score["final_score"])
            self.stage = self._decide_next_stage(self.current_topic, classification)

            self.expecting_answer = False

            print(f"[SAVE_ANSWER] Saved answer {len(self.answers)}/{self.MAX_TECH_QUESTIONS}, score: {score['final_score']:.2f}")

    def force_finalize(self):        
        print(f"[FORCE_FINALIZE] Called")
        self.finalize(force_save_current_answer=True, reason="FORCED_FINALIZATION")

    # ─── RESULT GENERATION ───
    def final_result(self) -> dict:
        with self._state_lock:
            total_time = round(self.get_elapsed_time(), 2)

            avg_score = round(
                sum(s["final_score"] for s in self.scores) / len(self.scores), 2
            ) if self.scores else 0.0

            result = {
                "average_score": avg_score,
                "result": "PASS" if avg_score >= 0.7 else "FAIL",
                "total_duration_seconds": total_time,
                "time_per_answer_seconds": self.answer_durations,
                "questions": self.questions,
                "answers": self.answers,
                "scores": self.scores,
                "feedback": self.feedback_text,  # Already generated in finalize()
                "covered_projects": self.covered_projects,
                "completion_reason": self.completion_reason or "UNKNOWN",
                "questions_answered": len(self.answers),
                "questions_asked": len(self.questions)
            }

            print(f"[FINAL_RESULT] Returning result: {avg_score:.2f}, {len(self.questions)}Q, {len(self.answers)}A, feedback: {len(self.feedback_text)} chars")
            
            return result

    def _get_completion_reason(self) -> str:
        return self.completion_reason or "UNKNOWN"



# SESSION STORE WITH AUTO-CLEANUP

_sessions: Dict[str, InterviewSession] = {}
_sessions_lock = threading.Lock()


def _cleanup_expired_sessions():
    while True:
        time.sleep(CLEANUP_INTERVAL_SECONDS)

        now = time.time()
        expired_ids = []

        with _sessions_lock:
            for session_id, session in _sessions.items():
                if session.completed and session.completed_at:
                    if now - session.completed_at > COMPLETED_TTL_SECONDS:
                        expired_ids.append(session_id)
                else:
                    if now - session.created_at > SESSION_TTL_SECONDS:
                        expired_ids.append(session_id)

            for session_id in expired_ids:
                del _sessions[session_id]

        if expired_ids:
            print(f"[CLEANUP] Removed {len(expired_ids)} sessions. Active: {len(_sessions)}")


_cleanup_thread = threading.Thread(
    target=_cleanup_expired_sessions,
    daemon=True,
    name="SessionCleanup"
)
_cleanup_thread.start()
print("[SESSION STORE] Auto-cleanup thread started")


def create_session(session_id: str, job_description: str, resume_text: str) -> str:
    with _sessions_lock:
        _sessions[session_id] = InterviewSession(
            resume_text=resume_text,
            job_description=job_description
        )
    print(f"[SESSION STORE] Created {session_id}. Total active: {len(_sessions)}")
    return session_id


def get_session(session_id: str) -> Optional[InterviewSession]:
    with _sessions_lock:
        return _sessions.get(session_id)


def delete_session(session_id: str):
    with _sessions_lock:
        if session_id in _sessions:
            del _sessions[session_id]
            print(f"[SESSION STORE] Deleted {session_id}. Total active: {len(_sessions)}")


def get_active_session_count() -> int:
    with _sessions_lock:
        return len(_sessions)