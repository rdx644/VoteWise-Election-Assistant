"""
Custom exception hierarchy for the VoteWise platform.
"""

from __future__ import annotations
from typing import Any


class VoteWiseError(Exception):
    """Base exception for all VoteWise errors."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "votewise_error",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"error": self.error_code, "message": self.message}
        if self.details:
            result["details"] = self.details
        return result


class EntityNotFoundError(VoteWiseError):
    def __init__(self, entity_type: str, entity_id: str):
        super().__init__(
            f"{entity_type} not found: {entity_id}",
            error_code="entity_not_found",
            status_code=404,
            details={"entity_type": entity_type, "entity_id": entity_id},
        )


class AIGenerationError(VoteWiseError):
    def __init__(self, reason: str, *, model: str = "gemini-2.0-flash", fallback_used: bool = False):
        super().__init__(
            f"AI generation failed: {reason}",
            error_code="ai_generation_error",
            status_code=503,
            details={"model": model, "fallback_used": fallback_used},
        )


class ExternalServiceError(VoteWiseError):
    def __init__(self, service_name: str, reason: str):
        super().__init__(
            f"{service_name} error: {reason}",
            error_code="external_service_error",
            status_code=502,
            details={"service": service_name},
        )


class SecretManagerError(ExternalServiceError):
    def __init__(self, reason: str):
        super().__init__("Secret Manager", reason)


class CloudStorageError(ExternalServiceError):
    def __init__(self, reason: str):
        super().__init__("Cloud Storage", reason)


class CloudLoggingError(ExternalServiceError):
    def __init__(self, reason: str):
        super().__init__("Cloud Logging", reason)


class RateLimitError(VoteWiseError):
    def __init__(self, retry_after: int = 60):
        super().__init__(
            "Rate limit exceeded. Please try again later.",
            error_code="rate_limit_exceeded",
            status_code=429,
            details={"retry_after_seconds": retry_after},
        )


class ConfigurationError(VoteWiseError):
    def __init__(self, field: str, reason: str = ""):
        super().__init__(
            f"Configuration error for {field}: {reason}",
            error_code="configuration_error",
            status_code=500,
            details={"field": field},
        )


class QuizValidationError(VoteWiseError):
    def __init__(self, reason: str):
        super().__init__(
            f"Quiz validation error: {reason}",
            error_code="quiz_validation_error",
            status_code=422,
            details={"reason": reason},
        )
