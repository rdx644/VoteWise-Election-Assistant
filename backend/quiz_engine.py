"""
Adaptive Quiz Engine for VoteWise.

Generates quizzes from the question bank, scores answers, and awards XP/badges.
Supports difficulty filtering, topic targeting, and gamified progression.
"""

from __future__ import annotations

import logging
import random
from typing import Any

from backend.cloud_logging import log_event
from backend.database import db
from backend.election_data import QUIZ_QUESTIONS, get_questions_by_difficulty
from backend.models import (
    QuizAttempt,
    QuizDifficulty,
    QuizResult,
    QuizSession,
)

logger = logging.getLogger("votewise.quiz")

# ── Constants ──

PASS_THRESHOLD_PERCENT: float = 70.0
"""Minimum score percentage required to pass a quiz."""

PASS_BONUS_XP: int = 25
"""Bonus XP awarded when a user passes a quiz."""

MAX_CONTEXT_MESSAGES: int = 10
"""Maximum conversation history messages sent to Gemini for context."""

BADGE_MILESTONES: dict[int, str] = {
    1: "First Quiz",
    5: "Quiz Enthusiast",
    10: "Quiz Master",
    20: "Election Expert",
    50: "Civic Champion",
}
"""Badge names awarded when a user completes N total quizzes."""


def generate_quiz(
    user_id: str = "",
    difficulty: QuizDifficulty = QuizDifficulty.EASY,
    num_questions: int = 5,
    topic: str = "",
) -> QuizSession:
    """Generate a new quiz session with randomly selected questions.

    Args:
        user_id: Optional user identifier for tracking progress.
        difficulty: Target difficulty tier for question selection.
        num_questions: Desired number of questions (capped by pool size).
        topic: Optional topic filter (e.g., ``voter_registration``).

    Returns:
        A persisted ``QuizSession`` ready for answer submission.
    """
    pool = get_questions_by_difficulty(difficulty)
    if topic:
        pool = [q for q in pool if q.topic == topic] or pool

    if len(pool) < num_questions:
        pool = QUIZ_QUESTIONS.copy()

    selected = random.sample(pool, min(num_questions, len(pool)))
    total_points = sum(q.points for q in selected)

    session = QuizSession(
        user_id=user_id,
        topic=topic or "mixed",
        difficulty=difficulty,
        questions=selected,
        total_points=total_points,
    )

    db.save_quiz_session(session)
    log_event(
        "quiz_generated",
        {
            "session_id": session.id,
            "difficulty": difficulty.value,
            "num_questions": len(selected),
        },
    )
    return session


def submit_answer(
    session_id: str,
    question_id: str,
    selected_answer: int,
    time_taken: float = 0,
) -> dict[str, Any]:
    """Submit an answer to a quiz question and return instant feedback.

    Args:
        session_id: Active quiz session identifier.
        question_id: The question being answered.
        selected_answer: Zero-based index of the chosen option.
        time_taken: Seconds the user spent on the question.

    Returns:
        A dict containing correctness, explanation, running score, etc.
    """
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

    correct_count = sum(1 for a in session.attempts if a.is_correct)
    session.score = (correct_count / len(session.attempts) * 100) if session.attempts else 0

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


def complete_quiz(session_id: str) -> QuizResult | dict[str, str]:
    """Finalize a quiz session, compute results, and award XP/badges.

    Args:
        session_id: The quiz session to complete.

    Returns:
        A ``QuizResult`` on success, or an error dict if the session is missing.
    """
    session = db.get_quiz_session(session_id)
    if not session:
        return {"error": "Quiz session not found"}

    session.completed = True
    correct = sum(1 for a in session.attempts if a.is_correct)
    total = len(session.questions)
    score_pct = (correct / total * 100) if total > 0 else 0
    passed = score_pct >= PASS_THRESHOLD_PERCENT

    xp = session.points_earned
    if passed:
        xp += PASS_BONUS_XP

    badges_earned = _compute_new_badges(session.user_id, passed)

    _update_user_stats(session.user_id, xp, passed, badges_earned)

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

    log_event(
        "quiz_completed",
        {
            "session_id": session_id,
            "score": result.score_percent,
            "xp": xp,
            "badges": badges_earned,
        },
    )

    return result


# ── Private Helpers ──


def _compute_new_badges(user_id: str, passed: bool) -> list[str]:
    """Determine which new badges a user has earned after this quiz."""
    user = db.get_user(user_id) if user_id else None
    if not user:
        return []

    new_total = user.quizzes_completed + 1
    return [
        badge_name
        for threshold, badge_name in BADGE_MILESTONES.items()
        if new_total >= threshold and badge_name not in user.badges
    ]


def _update_user_stats(
    user_id: str,
    xp: int,
    passed: bool,
    badges_earned: list[str],
) -> None:
    """Persist updated XP, quiz counts, and badges to the user record."""
    user = db.get_user(user_id) if user_id else None
    if not user:
        return

    update_data: dict[str, Any] = {
        "quizzes_completed": user.quizzes_completed + 1,
        "quizzes_passed": user.quizzes_passed + (1 if passed else 0),
        "xp_points": user.xp_points + xp,
        "badges": user.badges + badges_earned,
    }
    db.update_user(user.id, update_data)
