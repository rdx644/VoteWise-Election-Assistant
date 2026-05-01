"""
Input sanitization and content safety for VoteWise.

Provides defense-in-depth input validation, XSS filtering,
and content safety checks for all user-facing inputs.
"""

from __future__ import annotations

import html
import logging
import re
import unicodedata

logger = logging.getLogger("votewise.security")

# Compiled patterns for performance
_SCRIPT_TAG_RE = re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL)
_JS_PROTOCOL_RE = re.compile(r"javascript\s*:", re.IGNORECASE)
_EVENT_HANDLER_RE = re.compile(r"on\w+\s*=", re.IGNORECASE)
_DATA_URI_RE = re.compile(r"data\s*:[^,]*;base64", re.IGNORECASE)
_STYLE_EXPR_RE = re.compile(r"expression\s*\(", re.IGNORECASE)

_BLOCKED_PATTERNS: list[re.Pattern[str]] = [
    _SCRIPT_TAG_RE,
    _JS_PROTOCOL_RE,
    _EVENT_HANDLER_RE,
    _DATA_URI_RE,
    _STYLE_EXPR_RE,
]


def sanitize_string(
    value: str,
    field_name: str = "input",
    max_length: int = 5000,
) -> str:
    """Sanitize a user-provided string.

    Applies:
    - Type checking and stripping
    - Unicode normalization (NFC)
    - Null byte removal
    - HTML entity escaping
    - Length truncation
    """
    if not isinstance(value, str):
        return ""

    # Normalize Unicode to prevent homoglyph attacks
    value = unicodedata.normalize("NFC", value)

    # Remove null bytes and other control characters
    value = value.replace("\x00", "")
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Cc" or ch in ("\n", "\r", "\t"))

    value = value.strip()

    if not value:
        logger.debug("Empty %s after sanitization", field_name)
        return ""

    # Escape HTML entities
    value = html.escape(value)

    # Enforce length limit
    if len(value) > max_length:
        value = value[:max_length]
        logger.debug("Truncated %s to %d characters", field_name, max_length)

    return value


def filter_generated_content(content: str) -> str:
    """Filter AI-generated content for safety.

    Removes script tags, JS protocol handlers, inline event handlers,
    data URIs, and CSS expression injections.
    """
    if not content:
        return ""

    for pattern in _BLOCKED_PATTERNS:
        content = pattern.sub("", content)

    return content.strip()


def validate_identifier(value: str, field_name: str = "id") -> str:
    """Validate a resource identifier (e.g., user_id, session_id).

    Only allows alphanumeric characters, hyphens, and underscores.
    """
    if not isinstance(value, str) or not value.strip():
        msg = f"Invalid {field_name}: must be a non-empty string"
        raise ValueError(msg)

    cleaned = value.strip()

    if not re.fullmatch(r"[a-zA-Z0-9\-_]{1,128}", cleaned):
        msg = f"Invalid {field_name}: contains disallowed characters"
        raise ValueError(msg)

    return cleaned
