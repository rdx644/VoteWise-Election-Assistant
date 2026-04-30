"""
Google Cloud Secret Manager integration for VoteWise.

Retrieves secrets securely in production; falls back to environment variables locally.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache

from backend.config import settings

logger = logging.getLogger("votewise.secrets")

_sm_client = None

if settings.is_production and settings.google_cloud_project:  # pragma: no cover
    try:
        from google.cloud import secretmanager
        _sm_client = secretmanager.SecretManagerServiceClient()
        logger.info("Secret Manager initialized")
    except Exception as e:
        logger.warning(f"Secret Manager unavailable: {e}")


def _get_env_fallback(secret_id: str) -> str:
    """Map secret IDs to environment variable names."""
    mapping = {
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", ""),
        "ADMIN_API_KEY": os.getenv("ADMIN_API_KEY", ""),
    }
    return mapping.get(secret_id, "")


@lru_cache(maxsize=32)
def get_secret(secret_id: str, fallback: str = "") -> str:
    """Retrieve a secret value. Uses Secret Manager in production, env vars locally."""
    if _sm_client and settings.google_cloud_project:  # pragma: no cover
        try:
            name = f"projects/{settings.google_cloud_project}/secrets/{secret_id}/versions/latest"
            response = _sm_client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.warning(f"Secret Manager lookup failed for {secret_id}: {e}")

    env_value = _get_env_fallback(secret_id)
    return env_value or fallback


def list_available_secrets() -> list[str]:
    """List available secret IDs."""
    available = []
    for key in ["GEMINI_API_KEY", "ADMIN_API_KEY"]:
        if _get_env_fallback(key):
            available.append(key)
    return available
