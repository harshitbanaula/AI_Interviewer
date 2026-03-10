

# backend/app/services/interview_state.py

import time
import json
import redis
import threading
from typing import Dict, List, Optional

from app.services.question_generator import generate_question
from app.services.evaluator import score_answer
from app.services.llm_feedback import generate_feedback

# ─── REDIS CONFIG ───
import os

REDIS_URL = os.getenv("REDIS_URL")

_redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True,
)

# TTL constants
SESSION_TTL_SECONDS       = 2 * 60 * 60
COMPLETED_TTL_SECONDS     = 30 * 60
SESSION_KEY_PREFIX        = "interview:session:"


def _key(session_id: str) -> str:
    return f"{SESSION_KEY_PREFIX}{session_id}"


# ─── SERIALIZATION HELPERS ───

def _serialize_session(session: "InterviewSession") -> str:
    data = {
        "resume_text":            session.resume_text,
        "job_description":        session.job_description,
        "stage":                  session.stage,
        "expecting_answer":       session.expecting_answer,
        "completed":              session.completed,
        "is_finalized":           session.is_finalized,
        "completion_reason":      session.completion_reason,
        "questions":              session.questions,
        "answers":                session.answers,
        "scores":                 session.scores,
        "covered_projects":       session.covered_projects,
        "current_topic":          session.current_topic,
        "topic_weakness":         session.topic_weakness,
        "session_start_time":     session.session_start_time,
        "created_at":             session.created_at,
        "completed_at":           session.completed_at,
        "current_question_start": session.current_question_start,
        "answer_durations":       session.answer_durations,
        "feedback_text":          session.feedback_text,
        "in_buffer_time":         session.in_buffer_time,
    }
    return json.dumps(data)


def _deserialize_session(raw: str) -> "InterviewSession":
    data = json.loads(raw)
    session = InterviewSession.__new__(InterviewSession)

    # Restore all fields
    session.resume_text            = data["resume_text"]
    session.job_description        = data["job_description"]
    session.stage                  = data["stage"]
    session.expecting_answer       = data["expecting_answer"]
    session.completed              = data["completed"]
    session.is_finalized           = data["is_finalized"]
    session.completion_reason      = data.get("completion_reason")
    session.questions              = data["questions"]
    session.answers                = data["answers"]
    session.scores                 = data["scores"]
    session.covered_projects       = data["covered_projects"]
    session.current_topic          = data.get("current_topic")
    session.topic_weakness         = data["topic_weakness"]
    session.session_start_time     = data.get("session_start_time")
    session.created_at             = data["created_at"]
    session.completed_at           = data.get("completed_at")
    session.current_question_start = data.get("current_question_start")
    session.answer_durations       = data["answer_durations"]
    session.feedback_text          = data.get("feedback_text", "")
    session.in_buffer_time         = data.get("in_buffer_time", False)

    # Non-serialized: locks (always fresh)
    session._finalize_lock = threading.Lock()
    session._state_lock    = threading.Lock()

    return session


# ─── REDIS SESSION STORE ───

def _load_session(session_id: str) -> Optional["InterviewSession"]:
    try:
        raw = _redis_client.get(_key(session_id))
        if raw is None:
            return None
        return _deserialize_session(raw)
    except Exception as e:
        print(f"[REDIS] Load error for {session_id}: {e}")
        return None


def _save_session(session_id: str, session: "InterviewSession"):
    try:
        raw = _serialize_session(session)
        ttl = COMPLETED_TTL_SECONDS if session.completed else SESSION_TTL_SECONDS
        _redis_client.setex(_key(session_id), ttl, raw)
    except Exception as e:
        print(f"[REDIS] Save error for {session_id}: {e}")


def _delete_session_key(session_id: str):
    try:
        _redis_client.delete(_key(session_id))
    except Exception as e:
        print(f"[REDIS] Delete error for {session_id}: {e}")


# ─── SESSION CLASS ───

class InterviewSession:
    MAX_TECH_QUESTIONS     = 10
    MAX_RETRY              = 5
    SESSION_LIMIT_SECONDS  = 45 * 60
    GRACE_PERIOD_SECONDS   = 2 * 60

    def __init__(self, resume_text: str, job_description: str):
        self.resume_text        = resume_text
        self.job_description    = job_description
        self.stage              = "INTRO"
        self.expecting_answer   = False
        self.completed          = False
        self.is_finalized       = False
        self.completion_reason: Optional[str] = None
        self._finalize_lock     = threading.Lock()
        self._state_lock        = threading.Lock()
        self.questions:          List[str]  = []
        self.answers:            List[str]  = []
        self.scores:             List[dict] = []
        self.covered_projects:   List[str]  = []
        self.current_topic:      Optional[str] = None
        self.topic_weakness:     Dict[str, int] = {}
        self.session_start_time: Optional[float] = None
        self.created_at:         float = time.time()
        self.completed_at:       Optional[float] = None
        self.current_question_start: Optional[float] = None
        self.answer_durations:   List[float] = []
        self.feedback_text:      str = ""
        self.in_buffer_time      = False

    # ─── TIME ───
    def get_elapsed_time(self) -> float:
        if not self.session_start_time:
            return 0.0
        return time.time() - self.session_start_time

    def _main_time_exceeded(self)   -> bool:
        return self.get_elapsed_time() >= self.SESSION_LIMIT_SECONDS

    def _buffer_time_exceeded(self) -> bool:
        return self.get_elapsed_time() >= (self.SESSION_LIMIT_SECONDS + self.GRACE_PERIOD_SECONDS)

    def _question_limit_reached(self) -> bool:
        return len(self.answers) >= self.MAX_TECH_QUESTIONS

    # ─── FINALIZATION ───
    def finalize(self, force_save_current_answer: bool = False, reason: Optional[str] = None):
        with self._finalize_lock:
            with self._state_lock:
                if self.is_finalized:
                    return

                self.is_finalized     = True
                self.completed        = True
                self.expecting_answer = False
                self.completed_at     = time.time()

                if reason:
                    self.completion_reason = reason
                elif self._buffer_time_exceeded():
                    self.completion_reason = "TIME_LIMIT_EXCEEDED"
                elif self._question_limit_reached():
                    self.completion_reason = "QUESTION_LIMIT_REACHED"
                else:
                    self.completion_reason = "COMPLETED_NORMALLY"

                print(f"[FINALIZE] Reason: {self.completion_reason}")

                if force_save_current_answer and len(self.questions) > len(self.answers):
                    current_question = self.questions[-1]
                    incomplete_answer = "Answer not completed (time expired)"
                    self.answers.append(incomplete_answer)
                    duration = round(
                        max(time.time() - self.current_question_start, 0), 2
                    ) if self.current_question_start else 0.0
                    self.answer_durations.append(duration)
                    score = score_answer(incomplete_answer, current_question)
                    self.scores.append(score)

                self.current_question_start = None

            print(f"[FINALIZE] Generating feedback...")
            self._generate_feedback_sync()
            print(f"[FINALIZE] Done: {len(self.feedback_text)} chars")

    def _generate_feedback_sync(self):
        if not self.questions or not self.answers:
            self.feedback_text = "No answers provided to generate feedback."
            return
        try:
            qa_list = []
            for i, q in enumerate(self.questions):
                ans = self.answers[i] if i < len(self.answers) else "No answer provided"
                sc  = self.scores[i]  if i < len(self.scores)  else score_answer(ans, q)
                qa_list.append({"question": q, "answer": ans, "scores": sc})

            avg_score = round(
                sum(s["final_score"] for s in self.scores) / len(self.scores), 2
            ) if self.scores else 0.0

            self.feedback_text = generate_feedback(qa_list, avg_score)

            if not self.feedback_text or not self.feedback_text.strip():
                self.feedback_text = (
                    f"Overall performance: {avg_score:.2f}/1.00. "
                    f"Interview completed with {len(self.answers)} answers."
                )
        except Exception as e:
            print(f"[FEEDBACK] Error: {e}")
            avg_score = round(
                sum(s["final_score"] for s in self.scores) / len(self.scores), 2
            ) if self.scores else 0.0
            self.feedback_text = (
                f"Interview completed. Average score: {avg_score:.2f}/1.00. "
                f"Answered {len(self.answers)} of {len(self.questions)} questions."
            )

    # ─── HELPERS ───
    def _is_duplicate(self, question: str) -> bool:
        return question.strip() in self.questions

    def _detect_topic(self, question: str) -> Optional[str]:
        for project in self.covered_projects:
            if project.lower() in question.lower():
                return project
        return None

    def _classify_answer(self, score: float) -> str:
        if score >= 0.75: return "STRONG"
        if score >= 0.40: return "CONFUSED"
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
        if self._buffer_time_exceeded():
            self.finalize(force_save_current_answer=True, reason="TIME_LIMIT_EXCEEDED")
            return None

        if self._question_limit_reached():
            self.finalize(reason="QUESTION_LIMIT_REACHED")
            return None

        with self._state_lock:
            if self.is_finalized or self.completed:
                return None
            if self._main_time_exceeded() and not self.in_buffer_time:
                self.in_buffer_time = True
            if self.expecting_answer:
                return None

            self.expecting_answer = True
            current_stage = self.stage
            is_intro = current_stage == "INTRO"
            if is_intro:
                self.stage = "TECH_SWITCH"

        if is_intro:
            q = "Please briefly introduce yourself and your professional background."
        else:
            q = self._generate_unique_question(current_stage)

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
            self.finalize(force_save_current_answer=False, reason="TIME_LIMIT_EXCEEDED")
            return

        with self._state_lock:
            if self.is_finalized or self.completed or not self.expecting_answer:
                return

            answer_text = answer.strip() or "No answer provided"
            question    = self.questions[-1]
            duration    = round(time.time() - self.current_question_start, 2) \
                          if self.current_question_start else 0.0

            self.answer_durations.append(duration)
            self.current_question_start = None

            score = score_answer(answer_text, question)
            self.answers.append(answer_text)
            self.scores.append(score)

            classification = self._classify_answer(score["final_score"])
            self.stage     = self._decide_next_stage(self.current_topic, classification)
            self.expecting_answer = False

            print(f"[SAVE_ANSWER] {len(self.answers)}/{self.MAX_TECH_QUESTIONS}, score={score['final_score']:.2f}")

    def force_finalize(self):
        self.finalize(force_save_current_answer=True, reason="FORCED_FINALIZATION")

    # ─── RESULT ───
    def final_result(self) -> dict:
        with self._state_lock:
            avg_score = round(
                sum(s["final_score"] for s in self.scores) / len(self.scores), 2
            ) if self.scores else 0.0

            return {
                "average_score":           avg_score,
                "result":                  "PASS" if avg_score >= 0.7 else "FAIL",
                "total_duration_seconds":  round(self.get_elapsed_time(), 2),
                "time_per_answer_seconds": self.answer_durations,
                "questions":               self.questions,
                "answers":                 self.answers,
                "scores":                  self.scores,
                "feedback":                self.feedback_text,
                "covered_projects":        self.covered_projects,
                "completion_reason":       self.completion_reason or "UNKNOWN",
                "questions_answered":      len(self.answers),
                "questions_asked":         len(self.questions),
            }


# ─── PUBLIC API (drop-in replacement for old in-memory store) ───

def create_session(session_id: str, job_description: str, resume_text: str) -> str:
    session = InterviewSession(resume_text=resume_text, job_description=job_description)
    _save_session(session_id, session)
    print(f"[SESSION] Created {session_id} in Redis")
    return session_id


def get_session(session_id: str) -> Optional[InterviewSession]:
    return _load_session(session_id)


def delete_session(session_id: str):
    _delete_session_key(session_id)
    print(f"[SESSION] Deleted {session_id} from Redis")


def get_active_session_count() -> int:
    try:
        keys = _redis_client.keys(f"{SESSION_KEY_PREFIX}*")
        return len(keys)
    except Exception:
        return -1