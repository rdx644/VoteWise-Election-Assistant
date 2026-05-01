"""
Tests for Google Cloud service integrations and security utilities.
"""

from __future__ import annotations

import os
import time

os.environ["APP_ENV"] = "testing"

from backend.cloud_logging import get_logger, log_event, log_latency
from backend.cloud_storage import export_quiz_results, store_analytics_report, store_audio
from backend.secret_manager import _get_env_fallback, get_secret, list_available_secrets
from backend.security import filter_generated_content, sanitize_string, validate_identifier


class TestCloudLogging:
    def test_get_logger(self):
        logger = get_logger("test")
        assert logger.name == "votewise.test"

    def test_get_logger_nested(self):
        logger = get_logger("routes.chat")
        assert logger.name == "votewise.routes.chat"

    def test_log_event_no_crash(self):
        log_event("test_event", {"key": "value"})

    def test_log_event_with_severity(self):
        log_event("test_warning", {"msg": "test"}, severity="WARNING")

    def test_log_event_no_payload(self):
        log_event("empty_event")

    def test_log_latency_returns_ms(self, monkeypatch):
        times = iter([100.0, 100.012])
        monkeypatch.setattr(time, "monotonic", lambda: next(times))
        start = time.monotonic()
        ms = log_latency("test_op", start)
        assert round(ms, 2) == 12.0

    def test_log_latency_with_metadata(self, monkeypatch):
        times = iter([0.0, 0.05])
        monkeypatch.setattr(time, "monotonic", lambda: next(times))
        start = time.monotonic()
        ms = log_latency("db_query", start, metadata={"table": "users"})
        assert ms > 0


class TestCloudStorage:
    def test_store_audio_returns_none_locally(self):
        assert store_audio(b"test", "topic", "id") is None

    def test_export_quiz_results_returns_none_locally(self):
        assert export_quiz_results([{"score": 100}]) is None

    def test_store_analytics_returns_none_locally(self):
        assert store_analytics_report({"test": True}) is None

    def test_store_audio_with_empty_bytes(self):
        assert store_audio(b"", "empty", "empty") is None

    def test_export_empty_results(self):
        assert export_quiz_results([]) is None


class TestSecretManager:
    def test_get_env_fallback(self):
        os.environ["GEMINI_API_KEY"] = "test-key"
        result = _get_env_fallback("GEMINI_API_KEY")
        assert result == "test-key"
        del os.environ["GEMINI_API_KEY"]

    def test_get_env_fallback_missing(self):
        result = _get_env_fallback("NONEXISTENT_KEY")
        assert result == ""

    def test_get_secret_with_fallback(self):
        result = get_secret("NONEXISTENT", fallback="default")
        assert result == "default"

    def test_get_secret_empty_fallback(self):
        result = get_secret("NONEXISTENT_SECRET_XYZ")
        assert result == ""

    def test_list_available_secrets(self):
        result = list_available_secrets()
        assert isinstance(result, list)

    def test_list_secrets_with_env_set(self):
        os.environ["GEMINI_API_KEY"] = "test-value"
        result = list_available_secrets()
        assert "GEMINI_API_KEY" in result
        del os.environ["GEMINI_API_KEY"]


class TestSecurity:
    def test_sanitize_string(self):
        result = sanitize_string("  <script>alert('xss')</script>  ")
        assert "<script>" not in result

    def test_sanitize_max_length(self):
        result = sanitize_string("a" * 100, max_length=10)
        assert len(result) == 10

    def test_sanitize_non_string(self):
        result = sanitize_string(123)  # type: ignore[arg-type]
        assert result == ""

    def test_sanitize_empty_string(self):
        result = sanitize_string("   ")
        assert result == ""

    def test_sanitize_null_bytes(self):
        result = sanitize_string("hello\x00world")
        assert "\x00" not in result
        assert "hello" in result

    def test_sanitize_unicode_normalization(self):
        result = sanitize_string("café")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_sanitize_preserves_newlines(self):
        result = sanitize_string("line1\nline2")
        assert "\n" in result

    def test_filter_generated_content(self):
        result = filter_generated_content("Hello <script>bad</script> world")
        assert "<script>" not in result
        assert "Hello" in result

    def test_filter_empty_content(self):
        result = filter_generated_content("")
        assert result == ""

    def test_filter_js_protocol(self):
        result = filter_generated_content("javascript:alert(1)")
        assert "javascript:" not in result

    def test_filter_event_handlers(self):
        result = filter_generated_content('<img onerror="alert(1)">')
        assert "onerror=" not in result

    def test_filter_data_uri(self):
        result = filter_generated_content("data:text/html;base64,PHNjcmlwdD4=")
        assert "base64" not in result

    def test_filter_css_expression(self):
        result = filter_generated_content("background: expression(alert(1))")
        assert "expression(" not in result

    def test_validate_identifier_valid(self):
        result = validate_identifier("user-123_abc")
        assert result == "user-123_abc"

    def test_validate_identifier_empty(self):
        import pytest

        with pytest.raises(ValueError):
            validate_identifier("")

    def test_validate_identifier_special_chars(self):
        import pytest

        with pytest.raises(ValueError):
            validate_identifier("user; DROP TABLE")

    def test_validate_identifier_strips_whitespace(self):
        result = validate_identifier("  user123  ")
        assert result == "user123"

    def test_validate_identifier_non_string(self):
        import pytest

        with pytest.raises(ValueError):
            validate_identifier(None)  # type: ignore[arg-type]
