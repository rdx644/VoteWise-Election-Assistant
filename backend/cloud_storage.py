"""
Google Cloud Storage integration for VoteWise.

Handles storage of TTS audio clips, quiz exports, and analytics reports.
Falls back gracefully when GCS is not configured.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from backend.config import settings

logger = logging.getLogger("votewise.storage")

_bucket = None

if settings.is_production and settings.google_cloud_project:  # pragma: no cover
    try:
        from google.cloud import storage

        _client = storage.Client(project=settings.google_cloud_project)
        bucket_name = settings.gcs_bucket_name or f"{settings.google_cloud_project}-votewise"
        try:
            _bucket = _client.get_bucket(bucket_name)
        except Exception:
            _bucket = _client.create_bucket(bucket_name, location=settings.gcs_location)
        logger.info(f"Cloud Storage initialized: {bucket_name}")
    except Exception as e:
        logger.warning(f"Cloud Storage unavailable: {e}")


def store_audio(audio_bytes: bytes, topic: str, identifier: str) -> str | None:
    """Store TTS audio clip in Cloud Storage."""
    if not _bucket:
        return None
    try:  # pragma: no cover
        blob_path = f"audio/{topic}/{identifier}.mp3"
        blob = _bucket.blob(blob_path)
        blob.upload_from_string(audio_bytes, content_type="audio/mpeg")
        return f"gs://{_bucket.name}/{blob_path}"
    except Exception as e:
        logger.warning(f"Audio storage failed: {e}")
        return None


def export_quiz_results(results: list[dict[str, Any]]) -> str | None:
    """Export quiz results to Cloud Storage as JSON."""
    if not _bucket:
        return None
    try:  # pragma: no cover
        ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        blob_path = f"exports/quiz-results-{ts}.json"
        blob = _bucket.blob(blob_path)
        blob.upload_from_string(json.dumps(results, default=str), content_type="application/json")
        return f"gs://{_bucket.name}/{blob_path}"
    except Exception as e:
        logger.warning(f"Quiz export failed: {e}")
        return None


def store_analytics_report(report: dict[str, Any]) -> str | None:
    """Store analytics report snapshot in Cloud Storage."""
    if not _bucket:
        return None
    try:  # pragma: no cover
        ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        blob_path = f"analytics/report-{ts}.json"
        blob = _bucket.blob(blob_path)
        blob.upload_from_string(json.dumps(report, default=str), content_type="application/json")
        return f"gs://{_bucket.name}/{blob_path}"
    except Exception as e:
        logger.warning(f"Analytics report storage failed: {e}")
        return None
