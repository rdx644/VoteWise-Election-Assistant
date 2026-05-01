"""
Regression tests for safety, fallback, and edge-case behavior.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend import cloud_storage
from backend.database import InMemoryDatabase
from backend.gemini_service import (
    _build_conversation_history,
    _extract_topics,
    _generate_suggestions,
    _get_civic_tip,
    _get_fallback_response,
    _get_level_context,
    generate_chat_response,
)
from backend.middleware import RateLimitMiddleware
from backend.models import ChatMessage, ChatRole, ChatSession, LearningLevel, UserProgress
from backend.quiz_engine import complete_quiz, generate_quiz, submit_answer
from backend.tts_service import synthesize_speech


class TestApiEdgeCases:
    def test_invalid_timeline_type_defaults_to_general(self, client: TestClient) -> None:
        res = client.get("/api/timeline?election_type=unknown")
        assert res.status_code == 200
        assert res.json()["election_type"] == "general"

    def test_invalid_timeline_phase_returns_400(self, client: TestClient) -> None:
        res = client.get("/api/timeline/phases/not-a-phase")
        assert res.status_code == 400

    def test_invalid_quiz_difficulty_defaults_to_easy(self, client: TestClient) -> None:
        res = client.post("/api/quiz/generate?difficulty=expert&num_questions=1")
        assert res.status_code == 200
        assert res.json()["difficulty"] == "easy"

    def test_quiz_answer_missing_session_returns_404(self, client: TestClient) -> None:
        res = client.post("/api/quiz/answer?session_id=missing&question_id=q-1&selected_answer=0")
        assert res.status_code == 404

    def test_quiz_complete_missing_session_returns_404(self, client: TestClient) -> None:
        res = client.post("/api/quiz/complete/missing")
        assert res.status_code == 404

    def test_frontend_routes_are_served(self, client: TestClient) -> None:
        assert client.get("/").status_code == 200
        assert client.get("/css/style.css").status_code == 200
        assert client.get("/client-side-route").status_code == 200

    def test_security_headers_are_hardened(self, client: TestClient) -> None:
        res = client.get("/api/health")
        csp = res.headers["content-security-policy"]
        assert "script-src 'self'" in csp
        assert "'unsafe-inline'" not in csp.split("script-src", 1)[1].split(";", 1)[0]
        pp = res.headers["permissions-policy"]
        assert "camera=()" in pp
        assert "microphone=()" in pp
        assert "geolocation=()" in pp
        assert "payment=()" in pp
        assert res.headers["cross-origin-opener-policy"] == "same-origin"

    def test_user_update_and_delete_not_found_paths(self, client: TestClient) -> None:
        created = client.post("/api/users", json={"name": "Updater"}).json()
        updated = client.put(f"/api/users/{created['id']}", json={"state": "Oregon"})
        assert updated.status_code == 200
        assert updated.json()["state"] == "Oregon"
        assert client.put("/api/users/missing", json={"state": "Nowhere"}).status_code == 404
        assert client.delete("/api/users/missing").status_code == 404

    def test_chat_session_routes(self, client: TestClient, monkeypatch) -> None:
        monkeypatch.setattr("backend.gemini_service._get_model", lambda: None)
        created = client.post("/api/chat", json={"message": "Tell me about ballots", "user_id": "edge-user"}).json()
        session_id = created["session_id"]

        session = client.get(f"/api/chat/sessions/{session_id}")
        assert session.status_code == 200
        assert len(session.json()["messages"]) == 2

        listed = client.get("/api/chat/sessions?user_id=edge-user")
        assert listed.status_code == 200
        assert any(item["id"] == session_id for item in listed.json())
        assert client.get("/api/chat/sessions").json() == []
        assert client.get("/api/chat/sessions/missing").status_code == 404

    def test_analytics_export_and_filtered_questions(self, client: TestClient) -> None:
        export = client.post("/api/analytics/export")
        assert export.status_code == 200
        assert export.json()["status"] in {"exported", "local_only"}

        invalid_filter = client.get("/api/quiz/questions?difficulty=invalid")
        assert invalid_filter.status_code == 200
        assert len(invalid_filter.json()) > 0

        topic_filter = client.get("/api/quiz/questions?topic=voter_registration")
        assert topic_filter.status_code == 200
        assert all(item["topic"] == "voter_registration" for item in topic_filter.json())


class TestGeminiFallbacks:
    def test_level_context_defaults_to_beginner(self) -> None:
        assert "BEGINNER" in _get_level_context("unknown")
        assert "ADVANCED" in _get_level_context(LearningLevel.ADVANCED)

    def test_conversation_history_maps_roles(self) -> None:
        session = ChatSession(
            messages=[
                ChatMessage(role=ChatRole.USER, content="hello"),
                ChatMessage(role=ChatRole.ASSISTANT, content="hi"),
            ],
        )
        assert _build_conversation_history(session) == [
            {"role": "user", "parts": ["hello"]},
            {"role": "model", "parts": ["hi"]},
        ]

    def test_fallback_response_selection(self) -> None:
        assert "Voter Registration" in _get_fallback_response("registration deadline")
        assert "Election Timeline" in _get_fallback_response("timeline steps")
        assert "Great question" in _get_fallback_response("campaign finance")

    def test_suggestions_and_topics(self) -> None:
        assert "Can I register online?" in _generate_suggestions("register online")
        assert "Can the popular vote differ?" in _generate_suggestions("electoral college")
        assert "When are primaries held?" in _generate_suggestions("primary election")
        assert "Can I vote by mail?" in _generate_suggestions("ballot")
        assert "electoral_college" in _extract_topics("Explain the Electoral College and electors")
        assert "absentee_voting" in _extract_topics("Can I vote by mail?")
        assert _get_civic_tip()

    @pytest.mark.asyncio
    async def test_generate_chat_response_uses_offline_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("backend.gemini_service._get_model", lambda: None)
        response = await generate_chat_response("How do I register?", ChatSession())
        assert response.session_id
        assert "vote.gov" in response.civic_tip
        assert response.suggested_questions

    @pytest.mark.asyncio
    async def test_generate_chat_response_uses_model_without_history(self, monkeypatch: pytest.MonkeyPatch) -> None:
        class FakeResponse:
            text = "Model answer"

        class FakeModel:
            def generate_content(self, prompt: str) -> FakeResponse:
                assert "User question: What is a ballot?" in prompt
                return FakeResponse()

        monkeypatch.setattr("backend.gemini_service._get_model", lambda: FakeModel())
        monkeypatch.setattr("backend.gemini_service._get_civic_tip", lambda: "Tip")

        response = await generate_chat_response("What is a ballot?", ChatSession(), LearningLevel.INTERMEDIATE)
        assert response.message == "Model answer"
        assert "election_day" in response.related_topics

    @pytest.mark.asyncio
    async def test_generate_chat_response_uses_model_with_history(self, monkeypatch: pytest.MonkeyPatch) -> None:
        class FakeResponse:
            text = "Chat answer"

        class FakeChat:
            def send_message(self, prompt: str) -> FakeResponse:
                assert "User question" in prompt
                return FakeResponse()

        class FakeModel:
            def start_chat(self, history: list[dict[str, str]]) -> FakeChat:
                assert history
                return FakeChat()

        session = ChatSession(messages=[ChatMessage(role=ChatRole.USER, content="Earlier question")])
        monkeypatch.setattr("backend.gemini_service._get_model", lambda: FakeModel())
        monkeypatch.setattr("backend.gemini_service._get_civic_tip", lambda: "Tip")

        response = await generate_chat_response("How do I register?", session, LearningLevel.ADVANCED)
        assert response.message == "Chat answer"

    @pytest.mark.asyncio
    async def test_generate_chat_response_falls_back_on_model_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        class FailingModel:
            def generate_content(self, prompt: str):
                raise RuntimeError(f"model unavailable for {prompt[:10]}")

        monkeypatch.setattr("backend.gemini_service._get_model", lambda: FailingModel())

        response = await generate_chat_response("registration help", ChatSession())
        assert "Voter Registration" in response.message


class TestStorageAndTts:
    @pytest.mark.asyncio
    async def test_tts_browser_mode_returns_none(self) -> None:
        assert await synthesize_speech("Hello") is None

    def test_cloud_storage_success_paths(self, monkeypatch: pytest.MonkeyPatch) -> None:
        class FakeBlob:
            def __init__(self) -> None:
                self.uploads: list[tuple[bytes | str, str]] = []

            def upload_from_string(self, payload, content_type: str) -> None:
                self.uploads.append((payload, content_type))

        class FakeBucket:
            name = "test-bucket"

            def blob(self, path: str) -> FakeBlob:
                assert path
                return FakeBlob()

        monkeypatch.setattr(cloud_storage, "_bucket", FakeBucket())
        assert cloud_storage.store_audio(b"audio", "topic", "id") == "gs://test-bucket/audio/topic/id.mp3"
        assert cloud_storage.export_quiz_results([{"score": 100}]).startswith("gs://test-bucket/exports/")
        assert cloud_storage.store_analytics_report({"active": True}).startswith("gs://test-bucket/analytics/")

    def test_cloud_storage_error_paths(self, monkeypatch: pytest.MonkeyPatch) -> None:
        class FailingBucket:
            name = "failing-bucket"

            def blob(self, path: str):
                raise RuntimeError(f"cannot create blob: {path}")

        monkeypatch.setattr(cloud_storage, "_bucket", FailingBucket())
        assert cloud_storage.store_audio(b"audio", "topic", "id") is None
        assert cloud_storage.export_quiz_results([]) is None
        assert cloud_storage.store_analytics_report({}) is None


class TestDataAndMiddlewareEdges:
    def test_in_memory_progress_and_chat_listing(self) -> None:
        database = InMemoryDatabase()
        progress = database.save_user_progress(UserProgress(user_id="user-demo-01"))
        assert database.get_user_progress("user-demo-01") == progress

        session = database.save_chat_session(ChatSession(user_id="user-demo-01"))
        assert database.list_chat_sessions("user-demo-01") == [session]

        quiz = database.save_quiz_session(
            generate_quiz(user_id="user-demo-01", topic="not-a-real-topic", num_questions=50)
        )
        assert database.get_quiz_session(quiz.id) == quiz
        assert database.list_quiz_sessions("user-demo-01")

    def test_quiz_engine_user_updates_and_error_paths(self) -> None:
        topic_session = generate_quiz(user_id="user-demo-01", topic="voter_registration", num_questions=2)
        assert topic_session.topic == "voter_registration"
        assert submit_answer(topic_session.id, "missing-question", 0)["error"] == "Question not found in this quiz"

        for question in topic_session.questions:
            submit_answer(topic_session.id, question.id, question.correct_answer)
        result = complete_quiz(topic_session.id)
        assert not isinstance(result, dict)
        assert result.xp_awarded >= topic_session.points_earned

    @pytest.mark.asyncio
    async def test_rate_limit_middleware_blocks_excess_requests(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("backend.middleware.settings.app_env", "development")
        calls = 0

        async def app(scope, receive, send):
            nonlocal calls
            calls += 1
            await send({"type": "http.response.start", "status": 204, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        middleware = RateLimitMiddleware(app, rpm=1, burst=1)
        scope = {"type": "http", "method": "GET", "path": "/", "headers": [], "client": ("127.0.0.1", 1234)}
        first_events = []
        second_events = []

        async def send_first(message):
            first_events.append(message)

        async def send_second(message):
            second_events.append(message)

        await middleware(scope, receive, send_first)
        await middleware(scope, receive, send_second)

        assert calls == 1
        assert first_events[0]["status"] == 204
        assert second_events[0]["status"] == 429
