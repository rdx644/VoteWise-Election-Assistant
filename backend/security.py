"""
Input sanitization and content safety for VoteWise.
"""

from __future__ import annotations

import html
import re


def sanitize_string(value: str, field_name: str = "input", max_length: int = 5000) -> str:
    """Sanitize a user-provided string."""
    if not isinstance(value, str):
        return ""
    value = value.strip()
    value = html.escape(value)
    if len(value) > max_length:
        value = value[:max_length]
    return value


def filter_generated_content(content: str) -> str:
    """Filter AI-generated content for safety."""
    blocked_patterns = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
    ]
    for pattern in blocked_patterns:
        content = re.sub(pattern, "", content, flags=re.IGNORECASE | re.DOTALL)
    return content
