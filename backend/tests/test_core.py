"""
Tests for election data knowledge base, quiz engine, and models.
"""

from __future__ import annotations

from backend.election_data import (
    ELECTION_STEPS,
    QUIZ_QUESTIONS,
    compute_readiness,
    get_full_timeline,
    get_questions_by_difficulty,
    get_step_by_id,
    get_step_by_phase,
)
from backend.exceptions import (
    AIGenerationError,
    ConfigurationError,
    EntityNotFoundError,
    QuizValidationError,
    RateLimitError,
    VoteWiseError,
)
from backend.models import (
    ChatRequest,
    ElectionPhase,
    LearningLevel,
    QuizDifficulty,
    QuizQuestion,
    ReadinessCheckRequest,
    UserProfile,
)
from backend.quiz_engine import complete_quiz, generate_quiz, submit_answer


class TestElectionData:
    def test_timeline_has_9_steps(self):
        assert len(ELECTION_STEPS) == 9

    def test_full_timeline(self):
        timeline = get_full_timeline()
        assert timeline.total_phases == 9
        assert timeline.country == "United States"

    def test_step_by_id(self):
        step = get_step_by_id("step-01")
        assert step is not None
        assert step.phase == ElectionPhase.VOTER_REGISTRATION

    def test_step_by_id_not_found(self):
        assert get_step_by_id("step-99") is None

    def test_step_by_phase(self):
        step = get_step_by_phase(ElectionPhase.ELECTION_DAY)
        assert step is not None
        assert "Election Day" in step.title

    def test_questions_exist(self):
        assert len(QUIZ_QUESTIONS) >= 18

    def test_filter_by_difficulty(self):
        easy = get_questions_by_difficulty(QuizDifficulty.EASY)
        assert all(q.difficulty == QuizDifficulty.EASY for q in easy)

    def test_readiness_full_score(self):
        req = ReadinessCheckRequest(
            age=25,
            is_registered=True,
            knows_polling_location=True,
            has_valid_id=True,
            understands_ballot=True,
        )
        result = compute_readiness(req)
        assert result.score == 100.0
        assert "Well Prepared" in result.status

    def test_readiness_zero_score(self):
        req = ReadinessCheckRequest(age=17)
        result = compute_readiness(req)
        assert result.score == 0.0
        assert "Needs Preparation" in result.status
        assert len(result.recommendations) > 0


class TestQuizEngine:
    def test_generate_quiz(self):
        session = generate_quiz(difficulty=QuizDifficulty.EASY, num_questions=3)
        assert len(session.questions) == 3
        assert session.total_points > 0

    def test_submit_correct_answer(self):
        session = generate_quiz(difficulty=QuizDifficulty.EASY, num_questions=1)
        q = session.questions[0]
        result = submit_answer(session.id, q.id, q.correct_answer)
        assert result["is_correct"] is True

    def test_submit_wrong_answer(self):
        session = generate_quiz(difficulty=QuizDifficulty.EASY, num_questions=1)
        q = session.questions[0]
        wrong = (q.correct_answer + 1) % len(q.options)
        result = submit_answer(session.id, q.id, wrong)
        assert result["is_correct"] is False

    def test_complete_quiz(self):
        session = generate_quiz(difficulty=QuizDifficulty.EASY, num_questions=2)
        for q in session.questions:
            submit_answer(session.id, q.id, q.correct_answer)
        result = complete_quiz(session.id)
        assert result.score_percent == 100.0

    def test_invalid_session_returns_error(self):
        result = submit_answer("invalid-id", "q-001", 0)
        assert "error" in result


class TestModels:
    def test_user_profile_creation(self):
        user = UserProfile(name="Test User")
        assert user.name == "Test User"
        assert user.xp_points == 0

    def test_user_validates_empty_name(self):
        import pytest

        with pytest.raises(ValueError):
            UserProfile(name="   ")

    def test_quiz_question_validation(self):
        q = QuizQuestion(
            question="Test question?",
            options=["A", "B", "C"],
            correct_answer=1,
        )
        assert q.correct_answer == 1

    def test_chat_request_validation(self):
        import pytest

        with pytest.raises(ValueError):
            ChatRequest(message="   ")

    def test_learning_levels(self):
        assert LearningLevel.BEGINNER.value == "beginner"
        assert LearningLevel.ADVANCED.value == "advanced"


class TestExceptions:
    def test_base_error(self):
        err = VoteWiseError("test", error_code="test_err", status_code=400)
        assert err.status_code == 400
        d = err.to_dict()
        assert d["error"] == "test_err"

    def test_base_error_message(self):
        err = VoteWiseError("Something went wrong")
        assert str(err) == "Something went wrong"

    def test_base_error_default_status(self):
        err = VoteWiseError("test")
        assert err.status_code == 500

    def test_entity_not_found(self):
        err = EntityNotFoundError("User", "123")
        assert err.status_code == 404

    def test_entity_not_found_message(self):
        err = EntityNotFoundError("Session", "abc")
        assert "Session" in str(err)

    def test_ai_generation_error(self):
        err = AIGenerationError("timeout")
        assert err.status_code == 503

    def test_rate_limit_error(self):
        err = RateLimitError(30)
        assert err.status_code == 429
        assert err.details["retry_after_seconds"] == 30

    def test_quiz_validation_error(self):
        err = QuizValidationError("bad answer")
        assert err.status_code == 422

    def test_configuration_error(self):
        err = ConfigurationError("api_key", "missing")
        assert err.status_code == 500

    def test_error_to_dict_has_message(self):
        err = VoteWiseError("test error", error_code="test")
        d = err.to_dict()
        assert "message" in d
        assert "error" in d


class TestQuizEdgeCases:
    def test_quiz_with_max_questions(self):
        session = generate_quiz(difficulty=QuizDifficulty.EASY, num_questions=10)
        assert len(session.questions) <= 10

    def test_quiz_with_user_id(self):
        session = generate_quiz(user_id="test-user", difficulty=QuizDifficulty.MEDIUM, num_questions=2)
        assert session.user_id == "test-user"

    def test_complete_quiz_without_answers(self):
        session = generate_quiz(difficulty=QuizDifficulty.EASY, num_questions=2)
        result = complete_quiz(session.id)
        assert result.score_percent == 0.0

    def test_quiz_invalid_question_id(self):
        session = generate_quiz(difficulty=QuizDifficulty.EASY, num_questions=1)
        result = submit_answer(session.id, "nonexistent-q", 0)
        assert "error" in result

    def test_quiz_all_difficulties(self):
        for diff in QuizDifficulty:
            session = generate_quiz(difficulty=diff, num_questions=1)
            assert len(session.questions) >= 1


class TestDatabaseOperations:
    def test_database_list_users(self):
        from backend.database import db

        users = db.list_users()
        assert isinstance(users, list)

    def test_database_create_and_get_user(self):
        from backend.database import db

        user = UserProfile(name="DB Test User")
        created = db.create_user(user)
        fetched = db.get_user(created.id)
        assert fetched is not None
        assert fetched.name == "DB Test User"

    def test_database_get_nonexistent_user(self):
        from backend.database import db

        result = db.get_user("nonexistent-user-xyz")
        assert result is None

    def test_database_delete_user(self):
        from backend.database import db

        user = UserProfile(name="To Delete")
        created = db.create_user(user)
        assert db.delete_user(created.id) is True
        assert db.get_user(created.id) is None

    def test_database_delete_nonexistent(self):
        from backend.database import db

        result = db.delete_user("nonexistent-user-xyz")
        assert result is False


class TestReadinessEdgeCases:
    def test_readiness_partial_score(self):
        req = ReadinessCheckRequest(age=21, is_registered=True, has_valid_id=True)
        result = compute_readiness(req)
        assert 0 < result.score < 100

    def test_readiness_has_recommendations(self):
        req = ReadinessCheckRequest(age=20)
        result = compute_readiness(req)
        assert len(result.recommendations) > 0

    def test_readiness_all_fields(self):
        req = ReadinessCheckRequest(
            age=30,
            state="Texas",
            is_registered=True,
            knows_polling_location=True,
            has_valid_id=True,
            understands_ballot=True,
        )
        result = compute_readiness(req)
        assert result.score == 100.0

    def test_readiness_checklist_populated(self):
        req = ReadinessCheckRequest(age=25, is_registered=True)
        result = compute_readiness(req)
        assert len(result.checklist) > 0
