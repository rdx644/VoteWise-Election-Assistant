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

    def test_delete_user(self, client: TestClient) -> None:
        created = client.post("/api/users", json={"name": "Delete Me"}).json()
        res = client.delete(f"/api/users/{created['id']}")
        assert res.status_code == 200


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


class TestChatEndpoints:
    def test_send_message(self, client: TestClient) -> None:
        res = client.post("/api/chat", json={"message": "How do I register to vote?"})
        assert res.status_code == 200
        data = res.json()
        assert "message" in data
        assert "session_id" in data
        assert "suggested_questions" in data


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
