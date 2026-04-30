"""
Google Gemini AI service for VoteWise election education chat.

Provides contextual, adaptive responses about election processes using
Google Gemini 2.0 Flash with structured system prompts and conversation history.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from backend.cloud_logging import log_event, log_latency
from backend.config import settings
from backend.models import ChatResponse, ChatSession, LearningLevel

logger = logging.getLogger("votewise.gemini")

_model = None


def _get_model():  # pragma: no cover
    """Lazy-initialize the Gemini model."""
    global _model
    if _model is None:
        import google.generativeai as genai
        api_key = settings.gemini_api_key
        if not api_key:
            logger.warning("GEMINI_API_KEY not set — using fallback responses")
            return None
        genai.configure(api_key=api_key)
        _model = genai.GenerativeModel(
            "gemini-2.0-flash",
            generation_config={"temperature": 0.7, "max_output_tokens": 1024, "top_p": 0.9},
        )
    return _model


SYSTEM_PROMPT = """You are VoteWise, an expert AI assistant that helps people understand the election process in the United States. Your role is to:

1. EDUCATE: Explain election concepts clearly and accurately
2. GUIDE: Walk users through voter registration, voting steps, and timelines
3. ENGAGE: Make learning about elections interactive and interesting
4. ADAPT: Adjust your explanations based on the user's learning level

LEARNING LEVELS:
- BEGINNER: Use simple language, analogies, and step-by-step explanations
- INTERMEDIATE: Provide more detail, context, and historical background
- ADVANCED: Include nuanced analysis, policy implications, and comparisons

RULES:
- Always be nonpartisan and factual
- Never endorse any candidate or political party
- Cite official sources when possible (vote.gov, state election websites)
- If unsure, say so and recommend official resources
- End responses with a relevant follow-up question or civic tip
- Keep responses concise but informative (under 300 words)

TOPICS YOU COVER:
- Voter registration process and requirements
- Election timelines and key dates
- Types of elections (primary, general, midterm, local)
- How to find polling locations
- Absentee and mail-in voting
- Understanding your ballot
- Electoral College explained
- Voting rights and amendments
- Campaign finance basics
- State-specific voting rules
"""


def _get_level_context(level: LearningLevel) -> str:
    """Return level-specific instruction."""
    contexts = {
        LearningLevel.BEGINNER: "The user is a BEGINNER. Use simple words, short sentences, and real-world analogies. Break complex topics into small steps.",
        LearningLevel.INTERMEDIATE: "The user is INTERMEDIATE. Provide moderate detail with historical context and comparisons between states or systems.",
        LearningLevel.ADVANCED: "The user is ADVANCED. Include detailed policy analysis, constitutional references, and nuanced discussion of election law.",
    }
    return contexts.get(level, contexts[LearningLevel.BEGINNER])


def _build_conversation_history(session: ChatSession) -> list[dict[str, str]]:
    """Convert chat session to Gemini conversation format."""
    history = []
    for msg in session.messages[-10:]:  # Last 10 messages for context
        role = "user" if msg.role.value == "user" else "model"
        history.append({"role": role, "parts": [msg.content]})
    return history


FALLBACK_RESPONSES: dict[str, str] = {
    "default": (
        "Great question about elections! While I'm currently running in offline mode, "
        "I can share that the U.S. election process involves several key steps: "
        "voter registration, primary elections, campaigning, and the general election. "
        "Each step is designed to ensure every eligible citizen can participate in "
        "choosing their representatives.\n\n"
        "💡 **Civic Tip**: Visit vote.gov to check your voter registration status!"
    ),
    "registration": (
        "**Voter Registration** is your first step to participating in democracy!\n\n"
        "📝 **How to register:**\n"
        "1. Visit vote.gov for your state's registration portal\n"
        "2. You'll need your name, address, date of birth, and ID/SSN\n"
        "3. Most states require registration 15-30 days before Election Day\n"
        "4. Some states offer same-day registration\n\n"
        "💡 **Civic Tip**: You can also register at your local DMV or library!"
    ),
    "timeline": (
        "**The Election Timeline** follows a clear progression:\n\n"
        "1️⃣ **Voter Registration** — Register early!\n"
        "2️⃣ **Candidate Filing** — Candidates declare their run\n"
        "3️⃣ **Campaigning** — Research candidates\n"
        "4️⃣ **Primary Elections** — Parties select candidates\n"
        "5️⃣ **Early Voting** — Vote before Election Day\n"
        "6️⃣ **Election Day** — First Tuesday after first Monday in November\n"
        "7️⃣ **Vote Counting** — Ballots are tallied\n"
        "8️⃣ **Certification** — Results are made official\n"
        "9️⃣ **Inauguration** — Officials take office\n\n"
        "💡 **Civic Tip**: Check your state's specific deadlines!"
    ),
}


def _get_fallback_response(message: str) -> str:
    """Return a fallback response when Gemini is unavailable."""
    msg_lower = message.lower()
    if any(w in msg_lower for w in ["register", "registration", "sign up"]):
        return FALLBACK_RESPONSES["registration"]
    if any(w in msg_lower for w in ["timeline", "steps", "process", "how"]):
        return FALLBACK_RESPONSES["timeline"]
    return FALLBACK_RESPONSES["default"]


async def generate_chat_response(
    message: str,
    session: ChatSession,
    learning_level: LearningLevel = LearningLevel.BEGINNER,
) -> ChatResponse:
    """Generate an AI response to a user's election question."""
    start = time.monotonic()

    model = _get_model()

    if model is None:
        # Fallback when Gemini is not available
        fallback = _get_fallback_response(message)
        log_event("chat_fallback", {"reason": "no_api_key", "message_length": len(message)})
        return ChatResponse(
            session_id=session.id,
            message=fallback,
            suggested_questions=[
                "How do I register to vote?",
                "What are the steps in an election?",
                "What is the Electoral College?",
            ],
            related_topics=["voter_registration", "election_timeline"],
            civic_tip="Visit vote.gov for official voter information!",
        )

    # Build prompt with context  # pragma: no cover
    level_context = _get_level_context(learning_level)
    full_prompt = f"{SYSTEM_PROMPT}\n\n{level_context}\n\nUser question: {message}"

    try:  # pragma: no cover
        history = _build_conversation_history(session)
        if history:
            chat = model.start_chat(history=history)
            response = chat.send_message(full_prompt)
        else:
            response = model.generate_content(full_prompt)

        response_text = response.text
        latency = log_latency("gemini_chat", start, metadata={
            "level": learning_level.value,
            "message_length": len(message),
        })

        log_event("chat_generated", {
            "session_id": session.id,
            "level": learning_level.value,
            "response_length": len(response_text),
            "latency_ms": round(latency, 2),
        })

        return ChatResponse(
            session_id=session.id,
            message=response_text,
            suggested_questions=_generate_suggestions(message),
            related_topics=_extract_topics(message),
            civic_tip=_get_civic_tip(),
        )

    except Exception as e:  # pragma: no cover
        logger.error(f"Gemini generation failed: {e}")
        log_event("chat_error", {"error": str(e)}, severity="ERROR")
        return ChatResponse(
            session_id=session.id,
            message=_get_fallback_response(message),
            suggested_questions=["How do I register to vote?"],
            civic_tip="Visit vote.gov for official voter information!",
        )


def _generate_suggestions(message: str) -> list[str]:
    """Generate follow-up question suggestions based on the user's message."""
    msg = message.lower()
    suggestions = []
    if "register" in msg:
        suggestions = ["What ID do I need to register?", "Can I register online?", "What's the deadline?"]
    elif "electoral college" in msg:
        suggestions = ["How are electors chosen?", "Can the popular vote differ?", "What is a faithless elector?"]
    elif "primary" in msg:
        suggestions = ["What's the difference between open and closed primaries?", "When are primaries held?"]
    elif "ballot" in msg or "vote" in msg:
        suggestions = ["How do I find my polling place?", "Can I vote by mail?", "What is early voting?"]
    else:
        suggestions = [
            "How do I register to vote?",
            "What happens on Election Day?",
            "How does the Electoral College work?",
        ]
    return suggestions[:3]


def _extract_topics(message: str) -> list[str]:
    """Extract relevant topics from a user message."""
    topic_keywords = {
        "voter_registration": ["register", "registration", "sign up", "eligible"],
        "election_day": ["election day", "polling", "vote", "ballot"],
        "electoral_college": ["electoral college", "electors", "270"],
        "primary_elections": ["primary", "caucus", "nomination"],
        "voting_rights": ["rights", "amendment", "discrimination", "suffrage"],
        "absentee_voting": ["absentee", "mail-in", "mail", "early voting"],
    }
    msg = message.lower()
    return [topic for topic, keywords in topic_keywords.items() if any(k in msg for k in keywords)]


def _get_civic_tip() -> str:
    """Return a random civic engagement tip."""
    import random
    tips = [
        "Visit vote.gov to check your voter registration status!",
        "Mark your calendar — know your state's registration deadline!",
        "Research candidates using nonpartisan voter guides.",
        "Find your polling place before Election Day.",
        "You have the right to take time off work to vote in most states.",
        "Bring a friend to vote — civic engagement is contagious!",
        "Review a sample ballot before heading to the polls.",
        "Every election matters — local races shape your daily life!",
    ]
    return random.choice(tips)  # noqa: S311
