"""
VoteWise Configuration — Pydantic Settings with environment variable binding.

Supports dual-mode operation:
    - Development: Local defaults, in-memory database
    - Production: Google Cloud services, Firestore, Secret Manager
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration with environment variable binding."""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    # --- Google Services ---
    gemini_api_key: str = ""
    google_cloud_project: str = ""

    # --- Google Cloud Storage ---
    gcs_bucket_name: str = ""
    gcs_location: str = "us-central1"

    # --- App Config ---
    app_env: str = "development"
    app_port: int = 8080
    app_host: str = "0.0.0.0"
    log_level: str = "INFO"
    app_title: str = "VoteWise — AI Election Education Platform"
    app_version: str = "1.0.0"

    # --- Feature Modes ---
    database_mode: str = "memory"
    tts_mode: str = "browser"

    # --- Security ---
    admin_api_key: str = ""
    allowed_origins: str = ""
    rate_limit_rpm: int = 60
    rate_limit_burst: int = 20

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def use_firestore(self) -> bool:
        return self.database_mode == "firestore"

    @property
    def cors_origins(self) -> list[str]:
        if self.allowed_origins:
            return [o.strip() for o in self.allowed_origins.split(",")]
        if self.is_production:
            return ["https://*.run.app"]
        return ["*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
