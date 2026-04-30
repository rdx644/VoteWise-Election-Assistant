"""
Chat routes — AI-powered election education chat endpoints.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from backend.cloud_logging import log_event
from backend.database import db
from backend.gemini_service import generate_chat_response
from backend.models import ChatMessage, ChatRequest, ChatRole, ChatSession
from backend.security import sanitize_string

logger = logging.getLogger("votewise.routes.chat")
router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("")
async def send_message(request: ChatRequest) -> dict[str, Any]:
    """Send a message to the VoteWise AI assistant."""
    sanitized_msg = sanitize_string(request.message, "message", max_length=2000)

    # Get or create session
    session = None
    if request.session_id:
        session = db.get_chat_session(request.session_id)
    if not session:
        session = ChatSession(user_id=request.user_id, topic=request.topic, learning_level=request.learning_level)
        db.save_chat_session(session)

    # Add user message
    user_msg = ChatMessage(role=ChatRole.USER, content=sanitized_msg)
    session.messages.append(user_msg)

    # Generate AI response
    response = await generate_chat_response(sanitized_msg, session, request.learning_level)

    # Add assistant message
    assistant_msg = ChatMessage(role=ChatRole.ASSISTANT, content=response.message)
    session.messages.append(assistant_msg)
    db.save_chat_session(session)

    log_event("chat_message", {"session_id": session.id, "topic": request.topic})

    return response.model_dump()


@router.get("/sessions/{session_id}")
async def get_session(session_id: str) -> dict[str, Any]:
    """Retrieve a chat session with full message history."""
    session = db.get_chat_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session.model_dump()


@router.get("/sessions")
async def list_sessions(user_id: str = "") -> list[dict[str, Any]]:
    """List chat sessions for a user."""
    sessions = db.list_chat_sessions(user_id) if user_id else []
    return [s.model_dump() for s in sessions]
