"""
Analytics routes — Platform metrics and data export.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from backend.analytics import compute_system_health, compute_user_analytics
from backend.cloud_storage import export_quiz_results, store_analytics_report
from backend.database import db

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/summary")
async def get_analytics_summary() -> dict[str, Any]:
    """Get platform-wide user engagement analytics."""
    return compute_user_analytics()


@router.get("/health")
async def get_system_health() -> dict[str, Any]:
    """Get system health metrics for monitoring."""
    return compute_system_health()


@router.get("/leaderboard")
async def get_leaderboard(limit: int = 10) -> list[dict[str, Any]]:
    """Get top users by XP points."""
    users = db.list_users()
    sorted_users = sorted(users, key=lambda u: u.xp_points, reverse=True)[:limit]
    return [
        {"rank": i + 1, "name": u.name, "xp_points": u.xp_points,
         "quizzes_completed": u.quizzes_completed, "badges": u.badges,
         "level": u.learning_level.value}
        for i, u in enumerate(sorted_users)
    ]


@router.post("/export")
async def export_data() -> dict[str, Any]:
    """Export analytics data to Google Cloud Storage."""
    report = compute_user_analytics()
    gcs_path = store_analytics_report(report)
    return {
        "status": "exported" if gcs_path else "local_only",
        "gcs_path": gcs_path,
        "report": report,
    }
