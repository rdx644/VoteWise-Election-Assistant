"""
Tests for Google Cloud service integrations.
"""

from __future__ import annotations

import os
import time

os.environ["APP_ENV"] = "testing"

from backend.cloud_logging import get_logger, log_event, log_latency  # noqa: E402
from backend.cloud_storage import export_quiz_results, store_analytics_report, store_audio  # noqa: E402
from backend.secret_manager import _get_env_fallback, get_secret, list_available_secrets  # noqa: E402
from backend.security import filter_generated_content, sanitize_string  # noqa: E402


class TestCloudLogging:
    def test_get_logger(self):
        logger = get_logger("test")
        assert logger.name == "votewise.test"

    def test_log_event_no_crash(self):
        log_event("test_event", {"key": "value"})

    def test_log_latency_returns_ms(self):
        start = time.monotonic()
        time.sleep(0.01)
        ms = log_latency("test_op", start)
        assert ms >= 5


class TestCloudStorage:
    def test_store_audio_returns_none_locally(self):
        assert store_audio(b"test", "topic", "id") is None

    def test_export_quiz_results_returns_none_locally(self):
        assert export_quiz_results([{"score": 100}]) is None

    def test_store_analytics_returns_none_locally(self):
        assert store_analytics_report({"test": True}) is None


class TestSecretManager:
    def test_get_env_fallback(self):
        os.environ["GEMINI_API_KEY"] = "test-key"
        result = _get_env_fallback("GEMINI_API_KEY")
        assert result == "test-key"
        del os.environ["GEMINI_API_KEY"]

    def test_get_secret_with_fallback(self):
        result = get_secret("NONEXISTENT", fallback="default")
        assert result == "default"

    def test_list_available_secrets(self):
        result = list_available_secrets()
        assert isinstance(result, list)


class TestSecurity:
    def test_sanitize_string(self):
        result = sanitize_string("  <script>alert('xss')</script>  ")
        assert "<script>" not in result

    def test_sanitize_max_length(self):
        result = sanitize_string("a" * 100, max_length=10)
        assert len(result) == 10

    def test_filter_generated_content(self):
        result = filter_generated_content("Hello <script>bad</script> world")
        assert "<script>" not in result
        assert "Hello" in result
