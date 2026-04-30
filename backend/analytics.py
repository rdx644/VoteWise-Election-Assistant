"""
Analytics service for VoteWise — engagement metrics and system health.
"""

from __future__ import annotations

import logging
from collections import Counter
from datetime import UTC, datetime
from typing import Any

from backend.cloud_logging import log_event
from backend.config import settings
from backend.database import db

logger = logging.getLogger("votewise.analytics")


def compute_user_analytics() -> dict[str, Any]:
    """Compute platform-wide user engagement analytics."""
    users = db.list_users()
    if not users:
        return {"total_users": 0, "generated_at": datetime.now(UTC).isoformat()}

    total_xp = sum(u.xp_points for u in users)
    total_quizzes = sum(u.quizzes_completed for u in users)
    total_passed = sum(u.quizzes_passed for u in users)
    level_counter: Counter[str] = Counter(u.learning_level.value for u in users)

    badge_counter: Counter[str] = Counter()
    for u in users:
        for b in u.badges:
            badge_counter[b] += 1

    metrics = {
        "total_users": len(users),
        "total_xp_awarded": total_xp,
        "avg_xp_per_user": round(total_xp / len(users), 1),
        "total_quizzes_completed": total_quizzes,
        "total_quizzes_passed": total_passed,
        "quiz_pass_rate": round(total_passed / total_quizzes * 100, 1) if total_quizzes else 0,
        "users_by_level": dict(level_counter),
        "popular_badges": dict(badge_counter.most_common(5)),
        "generated_at": datetime.now(UTC).isoformat(),
    }

    log_event("analytics_computed", {"total_users": len(users), "total_quizzes": total_quizzes})
    return metrics


def compute_system_health() -> dict[str, Any]:
    """Compute system health metrics for monitoring."""
    users = db.list_users()
    return {
        "services": {
            "gemini_configured": bool(settings.gemini_api_key),
            "tts_mode": settings.tts_mode,
            "database_mode": settings.database_mode,
            "environment": settings.app_env,
            "cloud_project": settings.google_cloud_project or "not configured",
            "cloud_logging": settings.is_production,
            "cloud_storage": bool(settings.gcs_bucket_name or settings.google_cloud_project),
        },
        "data": {
            "total_users": len(users),
            "active_users": sum(1 for u in users if u.xp_points > 0),
        },
        "generated_at": datetime.now(UTC).isoformat(),
    }
