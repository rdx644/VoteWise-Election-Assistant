"""
Quiz routes — Adaptive quiz generation, answer submission, and scoring.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from backend.election_data import QUIZ_QUESTIONS
from backend.models import QuizDifficulty
from backend.quiz_engine import complete_quiz, generate_quiz, submit_answer

router = APIRouter(prefix="/api/quiz", tags=["Quiz"])


@router.post("/generate")
async def create_quiz(
    difficulty: str = "easy",
    num_questions: int = 5,
    topic: str = "",
    user_id: str = "",
) -> dict[str, Any]:
    """Generate a new quiz with random questions."""
    try:
        diff = QuizDifficulty(difficulty)
    except ValueError:
        diff = QuizDifficulty.EASY

    num_questions = max(1, min(num_questions, 20))
    session = generate_quiz(user_id=user_id, difficulty=diff, num_questions=num_questions, topic=topic)
    return session.model_dump()


@router.post("/answer")
async def answer_question(
    session_id: str,
    question_id: str,
    selected_answer: int,
    time_taken: float = 0,
) -> dict[str, Any]:
    """Submit an answer to a quiz question."""
    result = submit_answer(session_id, question_id, selected_answer, time_taken)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/complete/{session_id}")
async def finish_quiz(session_id: str) -> dict[str, Any]:
    """Complete a quiz session and get results."""
    result = complete_quiz(session_id)
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result.model_dump()


@router.get("/questions")
async def list_questions(difficulty: str = "", topic: str = "") -> list[dict[str, Any]]:
    """List available quiz questions (without answers for study)."""
    questions = QUIZ_QUESTIONS
    if difficulty:
        try:
            d = QuizDifficulty(difficulty)
            questions = [q for q in questions if q.difficulty == d]
        except ValueError:
            pass
    if topic:
        questions = [q for q in questions if q.topic == topic]

    # Return without correct answers for study mode
    return [
        {
            "id": q.id,
            "question": q.question,
            "options": q.options,
            "difficulty": q.difficulty.value,
            "topic": q.topic,
            "points": q.points,
        }
        for q in questions
    ]
