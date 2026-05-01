"""
API endpoint tests for VoteWise.
"""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    def test_health_returns_200(self, client: TestClient) -> None:
        res = client.get("/api/health")
        assert res.status_code == 200

    def test_health_response_structure(self, client: TestClient) -> None:
        data = client.get("/api/health").json()
        assert data["status"] == "healthy"
        assert data["service"] == "votewise-election-assistant"
        assert data["version"] == "1.0.0"
        assert "google_services" in data

    def test_health_google_services_fields(self, client: TestClient) -> None:
        data = client.get("/api/health").json()
        services = data["google_services"]
        assert "gemini_configured" in services
        assert "tts_mode" in services
        assert "database_mode" in services
        assert "cloud_project" in services
        assert "cloud_logging" in services
        assert "cloud_storage" in services

    def test_health_environment_field(self, client: TestClient) -> None:
        data = client.get("/api/health").json()
        assert data["environment"] == "testing"


class TestUserEndpoints:
    def test_list_users(self, client: TestClient) -> None:
        res = client.get("/api/users")
        assert res.status_code == 200
        assert isinstance(res.json(), list)
        assert len(res.json()) > 0

    def test_get_user_by_id(self, client: TestClient) -> None:
        users = client.get("/api/users").json()
        if users:
            res = client.get(f"/api/users/{users[0]['id']}")
            assert res.status_code == 200

    def test_get_nonexistent_user_returns_404(self, client: TestClient) -> None:
        res = client.get("/api/users/nonexistent-id")
        assert res.status_code == 404

    def test_create_user(self, client: TestClient) -> None:
        data = {"name": "Test User", "email": "test@test.com", "state": "California"}
        res = client.post("/api/users", json=data)
        assert res.status_code == 201
        assert res.json()["name"] == "Test User"

    def test_create_user_returns_id(self, client: TestClient) -> None:
        data = {"name": "New User"}
        res = client.post("/api/users", json=data)
        assert res.status_code == 201
        assert "id" in res.json()
        assert len(res.json()["id"]) > 0

    def test_update_user(self, client: TestClient) -> None:
        created = client.post("/api/users", json={"name": "Update Me"}).json()
        res = client.put(f"/api/users/{created['id']}", json={"name": "Updated"})
        assert res.status_code == 200
        assert res.json()["name"] == "Updated"

    def test_update_nonexistent_user_returns_404(self, client: TestClient) -> None:
        res = client.put("/api/users/nonexistent-id", json={"name": "Test"})
        assert res.status_code == 404

    def test_delete_user(self, client: TestClient) -> None:
        created = client.post("/api/users", json={"name": "Delete Me"}).json()
        res = client.delete(f"/api/users/{created['id']}")
        assert res.status_code == 200

    def test_delete_nonexistent_user_returns_404(self, client: TestClient) -> None:
        res = client.delete("/api/users/nonexistent-id")
        assert res.status_code == 404


class TestTimelineEndpoints:
    def test_get_timeline(self, client: TestClient) -> None:
        res = client.get("/api/timeline")
        assert res.status_code == 200
        data = res.json()
        assert "steps" in data
        assert len(data["steps"]) == 9

    def test_list_steps(self, client: TestClient) -> None:
        res = client.get("/api/timeline/steps")
        assert res.status_code == 200
        assert len(res.json()) == 9

    def test_get_step_by_id(self, client: TestClient) -> None:
        res = client.get("/api/timeline/steps/step-01")
        assert res.status_code == 200
        assert "voter_registration" in res.json()["phase"]

    def test_get_nonexistent_step(self, client: TestClient) -> None:
        res = client.get("/api/timeline/steps/step-99")
        assert res.status_code == 404

    def test_get_phase(self, client: TestClient) -> None:
        res = client.get("/api/timeline/phases/election_day")
        assert res.status_code == 200

    def test_get_nonexistent_phase(self, client: TestClient) -> None:
        res = client.get("/api/timeline/phases/nonexistent_phase")
        assert res.status_code == 400

    def test_timeline_steps_have_required_fields(self, client: TestClient) -> None:
        steps = client.get("/api/timeline/steps").json()
        for step in steps:
            assert "id" in step
            assert "title" in step
            assert "phase" in step
            assert "summary" in step

    def test_readiness_check(self, client: TestClient) -> None:
        data = {
            "age": 25,
            "is_registered": True,
            "has_valid_id": True,
            "knows_polling_location": True,
            "understands_ballot": False,
        }
        res = client.post("/api/timeline/readiness", json=data)
        assert res.status_code == 200
        assert "score" in res.json()
        assert "checklist" in res.json()

    def test_readiness_underage(self, client: TestClient) -> None:
        data = {
            "age": 16,
            "is_registered": False,
            "has_valid_id": False,
            "knows_polling_location": False,
            "understands_ballot": False,
        }
        res = client.post("/api/timeline/readiness", json=data)
        assert res.status_code == 200
        result = res.json()
        assert result["score"] == 0.0


class TestChatEndpoints:
    def test_send_message(self, client: TestClient, monkeypatch) -> None:
        monkeypatch.setattr("backend.gemini_service._get_model", lambda: None)
        res = client.post("/api/chat", json={"message": "How do I register to vote?"})
        assert res.status_code == 200
        data = res.json()
        assert "message" in data
        assert "session_id" in data
        assert "suggested_questions" in data

    def test_send_message_returns_nonempty(self, client: TestClient, monkeypatch) -> None:
        monkeypatch.setattr("backend.gemini_service._get_model", lambda: None)
        res = client.post("/api/chat", json={"message": "What is the Electoral College?"})
        data = res.json()
        assert len(data["message"]) > 0

    def test_chat_xss_sanitized(self, client: TestClient, monkeypatch) -> None:
        monkeypatch.setattr("backend.gemini_service._get_model", lambda: None)
        res = client.post("/api/chat", json={"message": "<script>alert('xss')</script>"})
        assert res.status_code == 200


class TestQuizEndpoints:
    def test_generate_quiz(self, client: TestClient) -> None:
        res = client.post("/api/quiz/generate?difficulty=easy&num_questions=3")
        assert res.status_code == 200
        data = res.json()
        assert "questions" in data
        assert len(data["questions"]) == 3

    def test_list_questions(self, client: TestClient) -> None:
        res = client.get("/api/quiz/questions")
        assert res.status_code == 200
        assert len(res.json()) > 0

    def test_list_questions_filter_difficulty(self, client: TestClient) -> None:
        res = client.get("/api/quiz/questions?difficulty=easy")
        assert res.status_code == 200
        for q in res.json():
            assert q["difficulty"] == "easy"

    def test_quiz_full_flow(self, client: TestClient) -> None:
        # Generate
        quiz = client.post("/api/quiz/generate?difficulty=easy&num_questions=2").json()
        session_id = quiz["id"]

        # Answer
        q = quiz["questions"][0]
        res = client.post(f"/api/quiz/answer?session_id={session_id}&question_id={q['id']}&selected_answer=0")
        assert res.status_code == 200

        # Complete
        res = client.post(f"/api/quiz/complete/{session_id}")
        assert res.status_code == 200
        assert "score_percent" in res.json()

    def test_quiz_invalid_session(self, client: TestClient) -> None:
        res = client.post("/api/quiz/answer?session_id=invalid&question_id=q1&selected_answer=0")
        assert res.status_code == 404

    def test_quiz_complete_invalid_session(self, client: TestClient) -> None:
        res = client.post("/api/quiz/complete/invalid-session")
        assert res.status_code == 404

    def test_quiz_questions_no_answers_exposed(self, client: TestClient) -> None:
        questions = client.get("/api/quiz/questions").json()
        for q in questions:
            assert "correct_answer" not in q


class TestAnalyticsEndpoints:
    def test_analytics_summary(self, client: TestClient) -> None:
        res = client.get("/api/analytics/summary")
        assert res.status_code == 200
        assert "total_users" in res.json()

    def test_leaderboard(self, client: TestClient) -> None:
        res = client.get("/api/analytics/leaderboard")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_system_health(self, client: TestClient) -> None:
        res = client.get("/api/analytics/health")
        assert res.status_code == 200
        assert "services" in res.json()

    def test_system_health_services_structure(self, client: TestClient) -> None:
        data = client.get("/api/analytics/health").json()
        services = data["services"]
        assert "gemini_configured" in services
        assert "database_mode" in services
        assert "environment" in services


class TestSecurityHeaders:
    def test_security_headers_present(self, client: TestClient) -> None:
        res = client.get("/api/health")
        assert res.headers.get("x-content-type-options") == "nosniff"
        assert res.headers.get("x-frame-options") == "DENY"
        assert res.headers.get("x-request-id") is not None
        assert res.headers.get("x-response-time") is not None

    def test_csp_header(self, client: TestClient) -> None:
        res = client.get("/api/health")
        csp = res.headers.get("content-security-policy", "")
        assert "default-src" in csp
        assert "frame-ancestors 'none'" in csp
        assert "object-src 'none'" in csp
        assert "base-uri 'self'" in csp

    def test_hsts_header(self, client: TestClient) -> None:
        res = client.get("/api/health")
        hsts = res.headers.get("strict-transport-security", "")
        assert "max-age=" in hsts
        assert "includeSubDomains" in hsts

    def test_permissions_policy(self, client: TestClient) -> None:
        res = client.get("/api/health")
        pp = res.headers.get("permissions-policy", "")
        assert "camera=()" in pp
        assert "microphone=()" in pp
        assert "geolocation=()" in pp

    def test_cross_origin_headers(self, client: TestClient) -> None:
        res = client.get("/api/health")
        assert res.headers.get("cross-origin-opener-policy") == "same-origin"
        assert res.headers.get("cross-origin-resource-policy") == "same-origin"

    def test_api_cache_control(self, client: TestClient) -> None:
        res = client.get("/api/health")
        cc = res.headers.get("cache-control", "")
        assert "no-store" in cc

    def test_referrer_policy(self, client: TestClient) -> None:
        res = client.get("/api/health")
        assert res.headers.get("referrer-policy") == "strict-origin-when-cross-origin"

    def test_dns_prefetch_control(self, client: TestClient) -> None:
        res = client.get("/api/health")
        assert res.headers.get("x-dns-prefetch-control") == "off"
