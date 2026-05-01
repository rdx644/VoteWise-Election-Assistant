"""
Google Cloud Logging integration for VoteWise.

Provides structured JSON logging with severity levels and latency tracking.
Falls back to standard Python logging in development.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from backend.config import settings

logger = logging.getLogger("votewise")

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

_cloud_client = None

if settings.is_production and settings.google_cloud_project:  # pragma: no cover
    try:
        from google.cloud import logging as cloud_logging

        _cloud_client = cloud_logging.Client(project=settings.google_cloud_project)
        _cloud_client.setup_logging()
        logger.info("Google Cloud Logging initialized")
    except Exception as e:
        logger.warning("Cloud Logging unavailable: %s", e)


def get_logger(module_name: str) -> logging.Logger:
    """Get a named logger for a module."""
    return logging.getLogger(f"votewise.{module_name}")


def log_event(
    event_type: str,
    payload: dict[str, Any] | None = None,
    severity: str = "INFO",
) -> None:
    """Log a structured event."""
    event = {"event_type": event_type, "service": "votewise", **(payload or {})}

    if _cloud_client:  # pragma: no cover
        cloud_logger = _cloud_client.logger("votewise-events")
        cloud_logger.log_struct(event, severity=severity)
    else:
        log_level = getattr(logging, severity, logging.INFO)
        logger.log(log_level, "[%s] %s", event_type, event)


def log_latency(
    operation: str,
    start_time: float,
    metadata: dict[str, Any] | None = None,
) -> float:
    """Log operation latency in milliseconds."""
    latency_ms = (time.monotonic() - start_time) * 1000
    event = {"operation": operation, "latency_ms": round(latency_ms, 2), **(metadata or {})}
    log_event(f"latency.{operation}", event)
    return latency_ms
