"""
Database service with dual-mode support (InMemory + Firestore).

Provides a unified ``DatabaseProtocol`` interface so callers are decoupled
from the backing store.  Pre-loaded with demo user data for the prototype.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol, runtime_checkable

from backend.config import settings
from backend.models import (
    ChatSession,
    QuizSession,
    UserProfile,
    UserProgress,
)

logger = logging.getLogger("votewise.database")


@runtime_checkable
class DatabaseProtocol(Protocol):
    """Abstract interface for all database implementations.

    Every concrete database (InMemory, Firestore, etc.) must satisfy this
    protocol so the rest of the application can swap implementations
    without code changes.
    """

    def get_user(self, user_id: str) -> UserProfile | None:
        """Retrieve a user by ID, or ``None`` if not found."""
        ...

    def list_users(self) -> list[UserProfile]:
        """Return all registered users."""
        ...

    def create_user(self, user: UserProfile) -> UserProfile:
        """Persist a new user and return it."""
        ...

    def update_user(self, user_id: str, data: dict[str, Any]) -> UserProfile | None:
        """Partially update a user. Returns ``None`` if not found."""
        ...

    def delete_user(self, user_id: str) -> bool:
        """Delete a user. Returns ``True`` if the user existed."""
        ...

    def get_chat_session(self, session_id: str) -> ChatSession | None:
        """Retrieve a chat session by ID."""
        ...

    def save_chat_session(self, session: ChatSession) -> ChatSession:
        """Create or update a chat session."""
        ...

    def list_chat_sessions(self, user_id: str) -> list[ChatSession]:
        """List chat sessions belonging to a user."""
        ...

    def get_quiz_session(self, session_id: str) -> QuizSession | None:
        """Retrieve a quiz session by ID."""
        ...

    def save_quiz_session(self, session: QuizSession) -> QuizSession:
        """Create or update a quiz session."""
        ...

    def list_quiz_sessions(self, user_id: str) -> list[QuizSession]:
        """List quiz sessions belonging to a user."""
        ...

    def get_user_progress(self, user_id: str) -> UserProgress | None:
        """Retrieve learning progress for a user."""
        ...

    def save_user_progress(self, progress: UserProgress) -> UserProgress:
        """Create or update user progress."""
        ...


# ── Demo Data ──

DEMO_USERS: list[UserProfile] = [
    UserProfile(
        id="user-demo-01",
        name="Alex Johnson",
        email="alex@example.com",
        state="California",
        learning_level="beginner",
        xp_points=150,
        quizzes_completed=3,
        quizzes_passed=2,
        topics_explored=["voter_registration", "election_day"],
        badges=["First Quiz", "Registration Ready"],
    ),
    UserProfile(
        id="user-demo-02",
        name="Sarah Williams",
        email="sarah@example.com",
        state="Texas",
        learning_level="intermediate",
        xp_points=320,
        quizzes_completed=7,
        quizzes_passed=6,
        topics_explored=["electoral_college", "primary_elections", "voting_rights"],
        badges=["First Quiz", "Quiz Master", "History Buff"],
    ),
    UserProfile(
        id="user-demo-03",
        name="Marcus Chen",
        email="marcus@example.com",
        state="New York",
        learning_level="advanced",
        xp_points=550,
        quizzes_completed=12,
        quizzes_passed=11,
        topics_explored=[
            "voter_registration",
            "electoral_college",
            "gerrymandering",
            "voting_rights",
        ],
        civic_readiness_score=95.0,
        badges=["First Quiz", "Quiz Master", "Civic Champion", "Election Expert"],
    ),
]


# ── InMemory Database ──


class InMemoryDatabase:
    """Thread-safe in-memory data store seeded with demo data.

    Used during development and testing.  All data lives in Python dicts
    and is lost when the process restarts.
    """

    def __init__(self) -> None:
        self._users: dict[str, UserProfile] = {}
        self._chat_sessions: dict[str, ChatSession] = {}
        self._quiz_sessions: dict[str, QuizSession] = {}
        self._user_progress: dict[str, UserProgress] = {}
        self._seed_demo_data()

    def _seed_demo_data(self) -> None:
        """Populate the store with demo user records."""
        for user in DEMO_USERS:
            self._users[user.id] = user.model_copy()
        logger.info("Loaded %d demo users", len(self._users))

    # ── User CRUD ──

    def get_user(self, user_id: str) -> UserProfile | None:
        """Retrieve a user by their unique identifier."""
        return self._users.get(user_id)

    def list_users(self) -> list[UserProfile]:
        """Return every user in the store."""
        return list(self._users.values())

    def create_user(self, user: UserProfile) -> UserProfile:
        """Insert a new user record."""
        self._users[user.id] = user
        return user

    def update_user(self, user_id: str, data: dict[str, Any]) -> UserProfile | None:
        """Merge *data* into an existing user. Returns ``None`` on miss."""
        if user_id not in self._users:
            return None
        current = self._users[user_id]
        updated = current.model_copy(update=data)
        self._users[user_id] = updated
        return updated

    def delete_user(self, user_id: str) -> bool:
        """Remove a user. Returns ``True`` if the user was present."""
        return self._users.pop(user_id, None) is not None

    # ── Chat Sessions ──

    def get_chat_session(self, session_id: str) -> ChatSession | None:
        """Retrieve a chat session by ID."""
        return self._chat_sessions.get(session_id)

    def save_chat_session(self, session: ChatSession) -> ChatSession:
        """Persist a chat session (insert or update)."""
        self._chat_sessions[session.id] = session
        return session

    def list_chat_sessions(self, user_id: str) -> list[ChatSession]:
        """Return all chat sessions for a given user."""
        return [s for s in self._chat_sessions.values() if s.user_id == user_id]

    # ── Quiz Sessions ──

    def get_quiz_session(self, session_id: str) -> QuizSession | None:
        """Retrieve a quiz session by ID."""
        return self._quiz_sessions.get(session_id)

    def save_quiz_session(self, session: QuizSession) -> QuizSession:
        """Persist a quiz session (insert or update)."""
        self._quiz_sessions[session.id] = session
        return session

    def list_quiz_sessions(self, user_id: str) -> list[QuizSession]:
        """Return all quiz sessions for a given user."""
        return [s for s in self._quiz_sessions.values() if s.user_id == user_id]

    # ── User Progress ──

    def get_user_progress(self, user_id: str) -> UserProgress | None:
        """Retrieve learning progress for a specific user."""
        return self._user_progress.get(user_id)

    def save_user_progress(self, progress: UserProgress) -> UserProgress:
        """Create or update a user's learning progress."""
        self._user_progress[progress.user_id] = progress
        return progress


# ── Firestore Database ──


class FirestoreDatabase:  # pragma: no cover
    """Google Cloud Firestore database implementation.

    Used in production on Google Cloud Run.  Requires a valid
    ``GOOGLE_CLOUD_PROJECT`` environment variable.
    """

    def __init__(self) -> None:
        from google.cloud import firestore

        self._client = firestore.Client(project=settings.google_cloud_project)
        logger.info("Firestore database initialized")

    # ── User CRUD ──

    def get_user(self, user_id: str) -> UserProfile | None:
        """Retrieve a user document from the ``users`` collection."""
        doc = self._client.collection("users").document(user_id).get()
        return UserProfile(**doc.to_dict()) if doc.exists else None

    def list_users(self) -> list[UserProfile]:
        """Stream all user documents."""
        return [UserProfile(**d.to_dict()) for d in self._client.collection("users").stream()]

    def create_user(self, user: UserProfile) -> UserProfile:
        """Write a new user document."""
        self._client.collection("users").document(user.id).set(user.model_dump(mode="json"))
        return user

    def update_user(self, user_id: str, data: dict[str, Any]) -> UserProfile | None:
        """Partially update an existing user document."""
        ref = self._client.collection("users").document(user_id)
        if not ref.get().exists:
            return None
        ref.update(data)
        return UserProfile(**ref.get().to_dict())

    def delete_user(self, user_id: str) -> bool:
        """Delete a user document. Returns ``True`` on success."""
        ref = self._client.collection("users").document(user_id)
        if ref.get().exists:
            ref.delete()
            return True
        return False

    # ── Chat Sessions ──

    def get_chat_session(self, session_id: str) -> ChatSession | None:
        """Retrieve a chat session from the ``chats`` collection."""
        doc = self._client.collection("chats").document(session_id).get()
        return ChatSession(**doc.to_dict()) if doc.exists else None

    def save_chat_session(self, session: ChatSession) -> ChatSession:
        """Persist a chat session document."""
        self._client.collection("chats").document(session.id).set(session.model_dump(mode="json"))
        return session

    def list_chat_sessions(self, user_id: str) -> list[ChatSession]:
        """List all chat sessions for a given user."""
        docs = self._client.collection("chats").where("user_id", "==", user_id).stream()
        return [ChatSession(**d.to_dict()) for d in docs]

    # ── Quiz Sessions ──

    def get_quiz_session(self, session_id: str) -> QuizSession | None:
        """Retrieve a quiz session from the ``quizzes`` collection."""
        doc = self._client.collection("quizzes").document(session_id).get()
        return QuizSession(**doc.to_dict()) if doc.exists else None

    def save_quiz_session(self, session: QuizSession) -> QuizSession:
        """Persist a quiz session document."""
        self._client.collection("quizzes").document(session.id).set(session.model_dump(mode="json"))
        return session

    def list_quiz_sessions(self, user_id: str) -> list[QuizSession]:
        """List all quiz sessions for a given user."""
        docs = self._client.collection("quizzes").where("user_id", "==", user_id).stream()
        return [QuizSession(**d.to_dict()) for d in docs]

    # ── User Progress ──

    def get_user_progress(self, user_id: str) -> UserProgress | None:
        """Retrieve user progress from the ``progress`` collection."""
        doc = self._client.collection("progress").document(user_id).get()
        return UserProgress(**doc.to_dict()) if doc.exists else None

    def save_user_progress(self, progress: UserProgress) -> UserProgress:
        """Persist a user progress document."""
        self._client.collection("progress").document(progress.user_id).set(progress.model_dump(mode="json"))
        return progress


# ── Factory ──


def _create_database() -> InMemoryDatabase | FirestoreDatabase:
    """Instantiate the correct database backend based on settings."""
    if settings.use_firestore:  # pragma: no cover
        return FirestoreDatabase()
    return InMemoryDatabase()


db: InMemoryDatabase | FirestoreDatabase = _create_database()
