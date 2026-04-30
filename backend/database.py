"""
Database service with dual-mode support (InMemory + Firestore).

Pre-loaded with demo user data for the prototype.
"""

from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

from backend.config import settings
from backend.models import (
    ChatSession,
    QuizSession,
    UserProfile,
    UserProgress,
    ElectionPhase,
)

logger = logging.getLogger("votewise.database")


@runtime_checkable
class DatabaseProtocol(Protocol):
    """Abstract interface for all database implementations."""

    def get_user(self, user_id: str) -> UserProfile | None: ...
    def list_users(self) -> list[UserProfile]: ...
    def create_user(self, user: UserProfile) -> UserProfile: ...
    def update_user(self, user_id: str, data: dict) -> UserProfile | None: ...
    def delete_user(self, user_id: str) -> bool: ...

    def get_chat_session(self, session_id: str) -> ChatSession | None: ...
    def save_chat_session(self, session: ChatSession) -> ChatSession: ...
    def list_chat_sessions(self, user_id: str) -> list[ChatSession]: ...

    def get_quiz_session(self, session_id: str) -> QuizSession | None: ...
    def save_quiz_session(self, session: QuizSession) -> QuizSession: ...
    def list_quiz_sessions(self, user_id: str) -> list[QuizSession]: ...

    def get_user_progress(self, user_id: str) -> UserProgress | None: ...
    def save_user_progress(self, progress: UserProgress) -> UserProgress: ...


# ── Demo Data ──

DEMO_USERS: list[UserProfile] = [
    UserProfile(
        id="user-demo-01", name="Alex Johnson", email="alex@example.com",
        state="California", learning_level="beginner", xp_points=150,
        quizzes_completed=3, quizzes_passed=2,
        topics_explored=["voter_registration", "election_day"],
        badges=["First Quiz", "Registration Ready"],
    ),
    UserProfile(
        id="user-demo-02", name="Sarah Williams", email="sarah@example.com",
        state="Texas", learning_level="intermediate", xp_points=320,
        quizzes_completed=7, quizzes_passed=6,
        topics_explored=["electoral_college", "primary_elections", "voting_rights"],
        badges=["First Quiz", "Quiz Master", "History Buff"],
    ),
    UserProfile(
        id="user-demo-03", name="Marcus Chen", email="marcus@example.com",
        state="New York", learning_level="advanced", xp_points=550,
        quizzes_completed=12, quizzes_passed=11,
        topics_explored=["voter_registration", "electoral_college", "gerrymandering", "voting_rights"],
        civic_readiness_score=95.0,
        badges=["First Quiz", "Quiz Master", "Civic Champion", "Election Expert"],
    ),
]


# ── InMemory Database ──

class InMemoryDatabase:
    """Thread-safe in-memory data store with demo data."""

    def __init__(self):
        self.users: dict[str, UserProfile] = {}
        self.chat_sessions: dict[str, ChatSession] = {}
        self.quiz_sessions: dict[str, QuizSession] = {}
        self.user_progress: dict[str, UserProgress] = {}
        self._load_demo_data()

    def _load_demo_data(self):
        for u in DEMO_USERS:
            self.users[u.id] = u.model_copy()
        logger.info(f"Loaded {len(self.users)} demo users")

    # User CRUD
    def get_user(self, user_id: str) -> UserProfile | None:
        return self.users.get(user_id)

    def list_users(self) -> list[UserProfile]:
        return list(self.users.values())

    def create_user(self, user: UserProfile) -> UserProfile:
        self.users[user.id] = user
        return user

    def update_user(self, user_id: str, data: dict) -> UserProfile | None:
        if user_id not in self.users:
            return None
        current = self.users[user_id]
        updated = current.model_copy(update=data)
        self.users[user_id] = updated
        return updated

    def delete_user(self, user_id: str) -> bool:
        return self.users.pop(user_id, None) is not None

    # Chat Sessions
    def get_chat_session(self, session_id: str) -> ChatSession | None:
        return self.chat_sessions.get(session_id)

    def save_chat_session(self, session: ChatSession) -> ChatSession:
        self.chat_sessions[session.id] = session
        return session

    def list_chat_sessions(self, user_id: str) -> list[ChatSession]:
        return [s for s in self.chat_sessions.values() if s.user_id == user_id]

    # Quiz Sessions
    def get_quiz_session(self, session_id: str) -> QuizSession | None:
        return self.quiz_sessions.get(session_id)

    def save_quiz_session(self, session: QuizSession) -> QuizSession:
        self.quiz_sessions[session.id] = session
        return session

    def list_quiz_sessions(self, user_id: str) -> list[QuizSession]:
        return [s for s in self.quiz_sessions.values() if s.user_id == user_id]

    # User Progress
    def get_user_progress(self, user_id: str) -> UserProgress | None:
        return self.user_progress.get(user_id)

    def save_user_progress(self, progress: UserProgress) -> UserProgress:
        self.user_progress[progress.user_id] = progress
        return progress


# ── Firestore Database ──

class FirestoreDatabase:  # pragma: no cover
    """Google Cloud Firestore database implementation."""

    def __init__(self):
        from google.cloud import firestore
        self.client = firestore.Client(project=settings.google_cloud_project)
        logger.info("Firestore database initialized")

    def get_user(self, user_id: str) -> UserProfile | None:
        doc = self.client.collection("users").document(user_id).get()
        return UserProfile(**doc.to_dict()) if doc.exists else None

    def list_users(self) -> list[UserProfile]:
        return [UserProfile(**d.to_dict()) for d in self.client.collection("users").stream()]

    def create_user(self, user: UserProfile) -> UserProfile:
        self.client.collection("users").document(user.id).set(user.model_dump(mode="json"))
        return user

    def update_user(self, user_id: str, data: dict) -> UserProfile | None:
        ref = self.client.collection("users").document(user_id)
        if not ref.get().exists:
            return None
        ref.update(data)
        return UserProfile(**ref.get().to_dict())

    def delete_user(self, user_id: str) -> bool:
        ref = self.client.collection("users").document(user_id)
        if ref.get().exists:
            ref.delete()
            return True
        return False

    def get_chat_session(self, session_id: str) -> ChatSession | None:
        doc = self.client.collection("chats").document(session_id).get()
        return ChatSession(**doc.to_dict()) if doc.exists else None

    def save_chat_session(self, session: ChatSession) -> ChatSession:
        self.client.collection("chats").document(session.id).set(session.model_dump(mode="json"))
        return session

    def list_chat_sessions(self, user_id: str) -> list[ChatSession]:
        docs = self.client.collection("chats").where("user_id", "==", user_id).stream()
        return [ChatSession(**d.to_dict()) for d in docs]

    def get_quiz_session(self, session_id: str) -> QuizSession | None:
        doc = self.client.collection("quizzes").document(session_id).get()
        return QuizSession(**doc.to_dict()) if doc.exists else None

    def save_quiz_session(self, session: QuizSession) -> QuizSession:
        self.client.collection("quizzes").document(session.id).set(session.model_dump(mode="json"))
        return session

    def list_quiz_sessions(self, user_id: str) -> list[QuizSession]:
        docs = self.client.collection("quizzes").where("user_id", "==", user_id).stream()
        return [QuizSession(**d.to_dict()) for d in docs]

    def get_user_progress(self, user_id: str) -> UserProgress | None:
        doc = self.client.collection("progress").document(user_id).get()
        return UserProgress(**doc.to_dict()) if doc.exists else None

    def save_user_progress(self, progress: UserProgress) -> UserProgress:
        self.client.collection("progress").document(progress.user_id).set(progress.model_dump(mode="json"))
        return progress


# ── Factory ──

def _create_database() -> InMemoryDatabase | FirestoreDatabase:
    if settings.use_firestore:  # pragma: no cover
        return FirestoreDatabase()
    return InMemoryDatabase()


db = _create_database()
