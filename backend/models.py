"""
VoteWise Data Models — Pydantic v2 models for users, quizzes, chat, and election data.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ElectionType(str, Enum):
    GENERAL = "general"
    PRIMARY = "primary"
    MIDTERM = "midterm"
    LOCAL = "local"
    SPECIAL = "special"


class LearningLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class QuizDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ElectionPhase(str, Enum):
    VOTER_REGISTRATION = "voter_registration"
    CANDIDATE_FILING = "candidate_filing"
    CAMPAIGNING = "campaigning"
    PRIMARY_ELECTION = "primary_election"
    EARLY_VOTING = "early_voting"
    ELECTION_DAY = "election_day"
    VOTE_COUNTING = "vote_counting"
    CERTIFICATION = "certification"
    INAUGURATION = "inauguration"


class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# ── User & Progress ──

class UserProfile(BaseModel):
    id: str = Field(default_factory=lambda: f"user-{uuid.uuid4().hex[:8]}")
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(default="", max_length=200)
    state: str = Field(default="", max_length=50)
    learning_level: LearningLevel = LearningLevel.BEGINNER
    xp_points: int = Field(default=0, ge=0)
    quizzes_completed: int = Field(default=0, ge=0)
    quizzes_passed: int = Field(default=0, ge=0)
    topics_explored: list[str] = Field(default_factory=list)
    civic_readiness_score: float = Field(default=0.0, ge=0, le=100)
    badges: list[str] = Field(default_factory=list)
    registered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_active: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty")
        return v


class UserProgress(BaseModel):
    user_id: str
    phases_completed: list[ElectionPhase] = Field(default_factory=list)
    current_phase: ElectionPhase = ElectionPhase.VOTER_REGISTRATION
    total_time_spent_minutes: int = 0
    last_quiz_score: float | None = None


# ── Election Timeline ──

class ElectionStep(BaseModel):
    id: str
    phase: ElectionPhase
    order: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=200)
    summary: str = Field(min_length=1, max_length=500)
    detailed_description: str = ""
    key_dates: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    tips: list[str] = Field(default_factory=list)
    icon: str = "📋"


class ElectionTimeline(BaseModel):
    election_type: ElectionType
    country: str = "United States"
    steps: list[ElectionStep] = Field(default_factory=list)
    total_phases: int = 0
    description: str = ""


# ── Quiz ──

class QuizQuestion(BaseModel):
    id: str = Field(default_factory=lambda: f"q-{uuid.uuid4().hex[:8]}")
    question: str = Field(min_length=5)
    options: list[str] = Field(min_length=2, max_length=6)
    correct_answer: int = Field(ge=0)
    explanation: str = ""
    difficulty: QuizDifficulty = QuizDifficulty.EASY
    topic: str = ""
    phase: ElectionPhase | None = None
    points: int = Field(default=10, ge=1)

    @field_validator("correct_answer")
    @classmethod
    def validate_correct_answer(cls, v: int, info: Any) -> int:
        if "options" in info.data and v >= len(info.data["options"]):
            raise ValueError("correct_answer index out of range")
        return v


class QuizAttempt(BaseModel):
    question_id: str
    selected_answer: int = Field(ge=0)
    is_correct: bool = False
    time_taken_seconds: float = 0
    answered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class QuizSession(BaseModel):
    id: str = Field(default_factory=lambda: f"quiz-{uuid.uuid4().hex[:8]}")
    user_id: str = ""
    topic: str = ""
    difficulty: QuizDifficulty = QuizDifficulty.EASY
    questions: list[QuizQuestion] = Field(default_factory=list)
    attempts: list[QuizAttempt] = Field(default_factory=list)
    score: float = 0.0
    total_points: int = 0
    points_earned: int = 0
    completed: bool = False
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class QuizResult(BaseModel):
    session_id: str
    user_id: str
    score_percent: float
    correct_count: int
    total_count: int
    points_earned: int
    xp_awarded: int
    badges_earned: list[str] = Field(default_factory=list)


# ── Chat ──

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: f"msg-{uuid.uuid4().hex[:8]}")
    role: ChatRole
    content: str = Field(min_length=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatSession(BaseModel):
    id: str = Field(default_factory=lambda: f"chat-{uuid.uuid4().hex[:8]}")
    user_id: str = ""
    messages: list[ChatMessage] = Field(default_factory=list)
    topic: str = "general"
    learning_level: LearningLevel = LearningLevel.BEGINNER
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str = ""
    user_id: str = ""
    learning_level: LearningLevel = LearningLevel.BEGINNER
    topic: str = "general"

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty")
        return v


class ChatResponse(BaseModel):
    session_id: str
    message: str
    sources: list[str] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)
    related_topics: list[str] = Field(default_factory=list)
    civic_tip: str = ""
    audio_base64: str | None = None


# ── Civic Readiness ──

class ReadinessCheckRequest(BaseModel):
    user_id: str = ""
    state: str = Field(default="", max_length=50)
    age: int = Field(default=18, ge=16, le=120)
    is_registered: bool = False
    knows_polling_location: bool = False
    has_valid_id: bool = False
    understands_ballot: bool = False


class ReadinessCheckResult(BaseModel):
    score: float = Field(ge=0, le=100)
    status: str = ""
    recommendations: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    checklist: dict[str, bool] = Field(default_factory=dict)
