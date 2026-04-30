"""
Adaptive Quiz Engine for VoteWise.

Generates quizzes from the question bank, scores answers, and awards XP/badges.
"""

from __future__ import annotations

import logging
import random
from datetime import UTC, datetime

from backend.cloud_logging import log_event
from backend.database import db
from backend.election_data import QUIZ_QUESTIONS, get_questions_by_difficulty
from backend.models import (
    QuizAttempt,
    QuizDifficulty,
    QuizQuestion,
    QuizResult,
    QuizSession,
)

logger = logging.getLogger("votewise.quiz")

BADGES = {
    1: "First Quiz",
    5: "Quiz Enthusiast",
    10: "Quiz Master",
    20: "Election Expert",
    50: "Civic Champion",
}


def generate_quiz(
    user_id: str = "",
    difficulty: QuizDifficulty = QuizDifficulty.EASY,
    num_questions: int = 5,
    topic: str = "",
) -> QuizSession:
    """Generate a new quiz session with random questions."""
    pool = get_questions_by_difficulty(difficulty)
    if topic:
        pool = [q for q in pool if q.topic == topic] or pool

    if len(pool) < num_questions:
        pool = QUIZ_QUESTIONS.copy()

    selected = random.sample(pool, min(num_questions, len(pool)))  # noqa: S311
    total_points = sum(q.points for q in selected)

    session = QuizSession(
        user_id=user_id,
        topic=topic or "mixed",
        difficulty=difficulty,
        questions=selected,
        total_points=total_points,
    )

    db.save_quiz_session(session)
    log_event("quiz_generated", {
        "session_id": session.id,
        "difficulty": difficulty.value,
        "num_questions": len(selected),
    })
    return session


def submit_answer(
    session_id: str,
    question_id: str,
    selected_answer: int,
    time_taken: float = 0,
) -> dict:
    """Submit an answer to a quiz question and return feedback."""
    session = db.get_quiz_session(session_id)
    if not session:
        return {"error": "Quiz session not found"}

    question = next((q for q in session.questions if q.id == question_id), None)
    if not question:
        return {"error": "Question not found in this quiz"}

    is_correct = selected_answer == question.correct_answer

    attempt = QuizAttempt(
        question_id=question_id,
        selected_answer=selected_answer,
        is_correct=is_correct,
        time_taken_seconds=time_taken,
    )
    session.attempts.append(attempt)

    if is_correct:
        session.points_earned += question.points

    session.score = (
        sum(1 for a in session.attempts if a.is_correct) / len(session.attempts) * 100
        if session.attempts else 0
    )

    db.save_quiz_session(session)

    return {
        "is_correct": is_correct,
        "correct_answer": question.correct_answer,
        "correct_option": question.options[question.correct_answer],
        "explanation": question.explanation,
        "points_earned": question.points if is_correct else 0,
        "running_score": session.score,
        "questions_answered": len(session.attempts),
        "questions_total": len(session.questions),
    }


def complete_quiz(session_id: str) -> QuizResult | dict:
    """Finalize a quiz session and award XP/badges."""
    session = db.get_quiz_session(session_id)
    if not session:
        return {"error": "Quiz session not found"}

    session.completed = True
    correct = sum(1 for a in session.attempts if a.is_correct)
    total = len(session.questions)
    score_pct = (correct / total * 100) if total > 0 else 0
    passed = score_pct >= 70

    xp = session.points_earned
    if passed:
        xp += 25  # Bonus for passing

    badges_earned = []
    user = db.get_user(session.user_id) if session.user_id else None
    if user:
        new_total = user.quizzes_completed + 1
        for threshold, badge_name in BADGES.items():
            if new_total >= threshold and badge_name not in user.badges:
                badges_earned.append(badge_name)

        update_data = {
            "quizzes_completed": new_total,
            "quizzes_passed": user.quizzes_passed + (1 if passed else 0),
            "xp_points": user.xp_points + xp,
            "badges": user.badges + badges_earned,
        }
        db.update_user(user.id, update_data)

    db.save_quiz_session(session)

    result = QuizResult(
        session_id=session_id,
        user_id=session.user_id,
        score_percent=round(score_pct, 1),
        correct_count=correct,
        total_count=total,
        points_earned=session.points_earned,
        xp_awarded=xp,
        badges_earned=badges_earned,
    )

    log_event("quiz_completed", {
        "session_id": session_id,
        "score": result.score_percent,
        "xp": xp,
        "badges": badges_earned,
    })

    return result
