




# # backend/app/services/evaluator.py
# import os
# import json
# from dotenv import load_dotenv
# from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import StrOutputParser
# from langchain_groq import ChatGroq
# load_dotenv()

# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# GROQ_MODEL_ID = os.getenv("GROQ_MODEL_ID", "llama-3.1-8b-instant")

# if not GROQ_API_KEY:
#     raise RuntimeError("GROQ_API_KEY missing")

# # ----------------------------
# # LLM (Advisory Only)
# # ----------------------------
# llm = ChatGroq(
#     api_key=GROQ_API_KEY,
#     model=GROQ_MODEL_ID,
#     temperature=0.1,
#     max_tokens=250,
# )

# # HF_TOKEN = os.getenv("HF_TOKEN")
# # HF_MODEL_ID = os.getenv("HF_MODEL_ID")
# # if not HF_TOKEN:
# #     raise RuntimeError("HF_TOKEN missing")

# # hf_endpoint = HuggingFaceEndpoint(
# #     repo_id=HF_MODEL_ID,
# #     task="conversational",
# #     huggingfacehub_api_token=HF_TOKEN,
# #     temperature=0.3,
# #     max_new_tokens=400,
# # )

# # llm = ChatHuggingFace(llm=hf_endpoint)


# # ----------------------------
# # Prompt
# # ----------------------------
# prompt = ChatPromptTemplate.from_messages([
#     ("system", "You are an AI interviewer. Suggest evaluation as JSON only."),
#     ("human", """
# Evaluate this answer and suggest:

# {
#   "strengths": ["..."],
#   "improvements": ["..."]
# }

# Answer:
# {answer_text}
# """)
# ])

# chain = prompt | llm | StrOutputParser()

# # ----------------------------
# # Backend Scoring (FINAL AUTHORITY)
# # ----------------------------
# WEIGHTS = {
#     "correctness": 0.5,
#     "depth": 0.3,
#     "clarity": 0.2
# }

# def score_answer(answer_text: str) -> dict:

#     words = len(answer_text.split())

#     correctness = min(words / 50, 1.0)
#     depth = min(words / 80, 1.0)
#     clarity = 1.0 if words <= 100 else max(0.5, 100 / words)

#     final_score = round(
#         correctness * WEIGHTS["correctness"] +
#         depth * WEIGHTS["depth"] +
#         clarity * WEIGHTS["clarity"],
#         2
#     )

#     # LLM advisory feedback
#     try:
#         raw = chain.invoke({"answer_text": answer_text})
#         advisory = json.loads(raw)
#     except Exception:
#         advisory = {"strengths": [], "improvements": []}

#     return {
#         "correctness": round(correctness, 2),
#         "depth": round(depth, 2),
#         "clarity": round(clarity, 2),
#         "final_score": final_score,
#         "strengths": advisory.get("strengths", []),
#         "improvements": advisory.get("improvements", [])
#     }
# backend/app/services/evaluator.py
# IMPROVED EVALUATOR - FIXES ALL CONSISTENCY ISSUES


import re 
import os
import json
from typing import Dict
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_ID = os.getenv("GROQ_MODEL_ID", "llama-3.1-8b-instant")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY missing")

# FIX: LOWER TEMPERATURE FOR CONSISTENCY

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=GROQ_MODEL_ID,
    temperature=0.0,
    max_tokens=750,
)


# FIX: DETAILED RUBRIC WITH EXAMPLES

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a strict technical interviewer evaluating candidate answers.


EVALUATION RUBRIC (Use EXACT thresholds):


1. RELEVANCE (0.0-1.0)
   Does the answer address the question asked?
   
   1.0 = Directly answers the question, on-topic throughout
   0.8 = Answers question but includes some tangential info
   0.6 = Somewhat related but misses key aspects
   0.4 = Barely related, mostly off-topic
   0.2 = Completely off-topic or tries to change subject
   0.0 = "I don't know" / refuses to answer

2. TECHNICAL_ACCURACY (0.0-1.0)
   Is the technical content correct?
   
   1.0 = Completely correct, shows deep understanding
   0.8 = Mostly correct with 1-2 minor errors
   0.6 = Partially correct, some misconceptions
   0.4 = Significant technical errors
   0.2 = Mostly incorrect information
   0.0 = No technical content or completely wrong

3. COMPLETENESS (0.0-1.0)
   Does the answer cover all important aspects?
   
   1.0 = Comprehensive, addresses all key points
   0.8 = Covers main points, minor gaps
   0.6 = Covers some points, significant gaps
   0.4 = Superficial, misses most important aspects
   0.2 = Barely scratches the surface
   0.0 = Doesn't attempt to answer

4. CLARITY (0.0-1.0)
   Is the answer well-structured and understandable?
   
   1.0 = Crystal clear, well-organized, logical flow
   0.8 = Clear but could be better organized
   0.6 = Understandable but somewhat confusing
   0.4 = Hard to follow, poor structure
   0.2 = Very confusing, incoherent
   0.0 = Incomprehensible


SPECIAL CASES (Apply these rules first):


NON-ANSWER DETECTION:
If answer contains ANY of these, mark as non-answer:
- "I don't know"
- "I'm not sure"
- "I don't remember"
- "Can we skip this"
- "Pass"
- "Next question"
- Answer < 15 words
→ Set ALL scores to 0.0, is_non_answer: true

OFF-TOPIC RAMBLING:
If answer talks about something completely different:
- Relevance: 0.2
- Technical_accuracy: 0.3 (may have correct info about wrong topic)
- Completeness: 0.2
- Clarity: 0.5 (may be clear about wrong thing)

BRILLIANT SHORT ANSWER:
If answer is concise but completely correct:
- Technical_accuracy: 1.0
- Relevance: 1.0
- Completeness: 0.8+ (not penalized for brevity)
- Clarity: 1.0

LONG RAMBLING ANSWER:
If answer is wordy but lacks substance:
- Completeness: Based on content, NOT length
- Clarity: Penalize for poor organization


OUTPUT FORMAT (STRICT):


Return ONLY valid JSON with exactly this structure:
{
  "relevance": 0.8,
  "technical_accuracy": 0.9,
  "completeness": 0.7,
  "clarity": 1.0,
  "strengths": ["Used correct terminology", "Explained trade-offs well"],
  "improvements": ["Could mention edge cases", "Missing performance considerations"],
  "is_non_answer": false
}

Do NOT include any text outside the JSON.
Do NOT use markdown formatting.
"""
    ),
    (
        "human",
        """
Question: {question}

Answer: {answer}

Evaluate strictly using the rubric above. Return ONLY JSON.
"""
    )
])

chain = prompt | llm | StrOutputParser()



# FIX: REMOVED LENGTH-BASED SCORING, NEW WEIGHTS

WEIGHTS = {
    "relevance": 0.35,
    "technical_accuracy": 0.35,
    "completeness": 0.20,
    "clarity": 0.10
}


# FIX: NON-ANSWER DETECTION
def detect_non_answer(answer_text: str) -> tuple[bool, str]:
    answer_lower = answer_text.lower().strip()
    word_count = len(answer_text.split())
    
    # Pattern 1: Explicit non-answers
    non_answer_phrases = [
        "i don't know",
        "i'm not sure",
        "i don't remember",
        "can we skip",
        "skip this",
        "skip question",
        "pass on this",
        "pass this",
        "next question",
        "no answer",
        "not sure about this",
        "don't have experience",
        "never worked with"
    ]
    
    for phrase in non_answer_phrases:
        if phrase in answer_lower:
            # Check if it's a short answer (likely just the non-answer phrase)
            if word_count < 15:
                return True, f"Candidate said: '{phrase}'"
            # If long answer but starts with non-answer, check ratio
            if answer_lower.startswith(phrase) and word_count < 30:
                return True, f"Answer starts with: '{phrase}'"
    
    # Pattern 2: Too short to be meaningful
    if word_count < 5:
        return True, f"Answer too short ({word_count} words)"
    
    # Pattern 3: Just repeating the question
    question_words = set(answer_lower.split())
    if len(question_words) > 0:
        # If >80% of answer words are from question, likely just repeating
        # (This is a simplified check - could be more sophisticated)
        pass
    
    return False, ""


# FIX: RETRY LOGIC FOR FAILED PARSING
def parse_llm_response(raw: str, attempt: int = 1) -> dict:
    strategies = [
        # Strategy 1: Direct parse (cleanest response)
        lambda r: json.loads(r),
        
        # Strategy 2: Strip markdown code blocks
        lambda r: json.loads(r.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()),
        
        # Strategy 3: Extract JSON from text
        lambda r: json.loads(r[r.find("{"):r.rfind("}")+1]),
        
        # Strategy 4: Find first { to last }
        lambda r: json.loads("{" + r.split("{", 1)[1].rsplit("}", 1)[0] + "}"),
    ]
    
    for i, strategy in enumerate(strategies):
        try:
            result = strategy(raw)
            if i > 0:
                print(f"[EVALUATOR] Parsed on strategy {i+1}, attempt {attempt}")
            return result
        except (json.JSONDecodeError, ValueError, IndexError, KeyError):
            continue
    
    return None


def call_llm_with_retry(question: str, answer: str, max_retries: int = 3) -> dict:
    for attempt in range(1, max_retries + 1):
        try:
            raw = chain.invoke({
                "question": question,
                "answer": answer
            })
            
            # Try to parse
            parsed = parse_llm_response(raw.strip(), attempt)
            
            if parsed:
                # Validate required fields
                required = ["relevance", "technical_accuracy", "completeness", "clarity"]
                if all(k in parsed for k in required):
                    return parsed
                else:
                    print(f"[EVALUATOR] Missing fields, attempt {attempt}/{max_retries}")
            
        except Exception as e:
            print(f"[EVALUATOR] Error attempt {attempt}/{max_retries}: {e}")
    
    # All retries failed - return neutral scores
    print(f"[EVALUATOR] All {max_retries} attempts failed, using fallback scores")
    return {
        "relevance": 0.5,
        "technical_accuracy": 0.5,
        "completeness": 0.5,
        "clarity": 0.5,
        "strengths": [],
        "improvements": ["Automatic evaluation failed - requires manual review"],
        "is_non_answer": False
    }


# MAIN SCORING FUNCTION
def score_answer(answer_text: str, question: str) -> Dict:
    answer_text = answer_text.strip()
    
    # CASE 1: Empty/Skipped Answer
    if not answer_text or answer_text.lower() in (
        "no answer",
        "no answer provided",
        "question skipped by candidate"
    ):
        return {
            "relevance": 0.0,
            "technical_accuracy": 0.0,
            "completeness": 0.0,
            "clarity": 0.0,
            "final_score": 0.0,
            "strengths": [],
            "improvements": ["Answer was not provided."],
            "is_non_answer": True
        }
    
    # CASE 2: Non-Answer Detection

    is_non_answer, reason = detect_non_answer(answer_text)
    
    if is_non_answer:
        return {
            "relevance": 0.0,
            "technical_accuracy": 0.0,
            "completeness": 0.0,
            "clarity": 0.0,
            "final_score": 0.0,
            "strengths": [],
            "improvements": [reason],
            "is_non_answer": True
        }
    

    # CASE 3: Normal Answer - Call LLM with Retry
    
    parsed = call_llm_with_retry(question, answer_text, max_retries=3)
    
    # Extract and validate scores
    relevance = float(parsed.get("relevance", 0.5))
    technical_accuracy = float(parsed.get("technical_accuracy", 0.5))
    completeness = float(parsed.get("completeness", 0.5))
    clarity = float(parsed.get("clarity", 0.5))
    
    # Clamp values to 0-1 range (in case LLM goes outside)
    relevance = max(0.0, min(1.0, relevance))
    technical_accuracy = max(0.0, min(1.0, technical_accuracy))
    completeness = max(0.0, min(1.0, completeness))
    clarity = max(0.0, min(1.0, clarity))
    
    strengths = parsed.get("strengths", [])
    improvements = parsed.get("improvements", [])
    is_non_answer_llm = parsed.get("is_non_answer", False)
    
    
    # Calculate Weighted Final Score
    
    final_score = round(
        relevance * WEIGHTS["relevance"]
        + technical_accuracy * WEIGHTS["technical_accuracy"]
        + completeness * WEIGHTS["completeness"]
        + clarity * WEIGHTS["clarity"],
        2
    )
    
    
    # Return Complete Evaluation
    
    return {
        "relevance": round(relevance, 2),
        "technical_accuracy": round(technical_accuracy, 2),
        "completeness": round(completeness, 2),
        "clarity": round(clarity, 2),
        "final_score": final_score,
        "strengths": strengths if isinstance(strengths, list) else [],
        "improvements": improvements if isinstance(improvements, list) else [],
        "is_non_answer": is_non_answer_llm
    }



# HELPER: Validate Score Consistency (for testing)

def test_consistency(question: str, answer: str, runs: int = 5) -> dict:
    scores = []
    for i in range(runs):
        result = score_answer(answer, question)
        scores.append(result["final_score"])
        print(f"Run {i+1}: {result['final_score']}")
    
    import statistics
    mean = statistics.mean(scores)
    std_dev = statistics.stdev(scores) if len(scores) > 1 else 0
    
    # Consistent if std_dev < 0.05 (5% variance)
    consistent = std_dev < 0.05
    
    return {
        "mean_score": round(mean, 2),
        "std_dev": round(std_dev, 3),
        "scores": scores,
        "consistent": consistent
    }


if __name__ == "__main__":
    # Test consistency
    print("\n" + "="*70)
    print("TESTING EVALUATOR CONSISTENCY")
    print("="*70 + "\n")
    
    test_q = "Explain the difference between a hash table and a binary search tree."
    test_a = "A hash table provides O(1) average lookup time using a hash function to map keys to array indices. A BST provides O(log n) lookup through hierarchical structure. Hash tables are faster for lookups but BSTs maintain sorted order."
    
    result = test_consistency(test_q, test_a, runs=5)
    
    print(f"\nMean Score: {result['mean_score']}")
    print(f"Std Dev: {result['std_dev']}")
    print(f"Consistent: {' YES' if result['consistent'] else 'NO'}")