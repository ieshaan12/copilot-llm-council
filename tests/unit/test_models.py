"""Unit tests for data models."""

import pytest

from copilot_council.models.member import CouncilMember
from copilot_council.models.response import CopilotResponse, MemberResponse
from copilot_council.models.session import CouncilSession


class TestCouncilMember:
    """Tests for CouncilMember model."""

    def test_create_basic_member(self) -> None:
        """Create a member with required fields."""
        member = CouncilMember(name="Alice", role="critic")

        assert member.name == "Alice"
        assert member.role == "critic"
        assert member.model == "gpt-5"  # default
        assert member.system_prompt is None
        assert member.allowed_tools == []
        assert member.denied_tools == []

    def test_create_member_with_all_fields(self) -> None:
        """Create a member with all fields specified."""
        member = CouncilMember(
            name="Bob",
            role="principal_engineer",
            model="claude-sonnet-4",
            system_prompt="You are an expert.",
            allowed_tools=["shell(git:*)"],
            denied_tools=["write"],
        )

        assert member.name == "Bob"
        assert member.model == "claude-sonnet-4"
        assert member.system_prompt == "You are an expert."
        assert member.allowed_tools == ["shell(git:*)"]
        assert member.denied_tools == ["write"]

    def test_empty_name_raises_error(self) -> None:
        """Empty name should raise ValueError."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            CouncilMember(name="", role="critic")

    def test_empty_role_raises_error(self) -> None:
        """Empty role should raise ValueError."""
        with pytest.raises(ValueError, match="role cannot be empty"):
            CouncilMember(name="Alice", role="")


class TestCopilotResponse:
    """Tests for CopilotResponse model."""

    def test_create_response(self) -> None:
        """Create a basic response."""
        response = CopilotResponse(content="Hello", model="gpt-5")

        assert response.content == "Hello"
        assert response.model == "gpt-5"
        assert response.is_valid is True
        assert response.validation_errors == []

    def test_response_with_tokens(self) -> None:
        """Response with token counts."""
        response = CopilotResponse(
            content="Test",
            model="gpt-5",
            input_tokens=100,
            output_tokens=20,
        )

        assert response.input_tokens == 100
        assert response.output_tokens == 20


class TestMemberResponse:
    """Tests for MemberResponse model."""

    def test_create_member_response(self, sample_response: CopilotResponse) -> None:
        """Create a member response."""
        mr = MemberResponse(
            member_name="Alice",
            role="critic",
            response=sample_response,
        )

        assert mr.member_name == "Alice"
        assert mr.role == "critic"
        assert mr.round_number == 1
        assert mr.response.content == sample_response.content

    def test_to_dict(self, sample_member_response: MemberResponse) -> None:
        """Convert response to dictionary."""
        data = sample_member_response.to_dict()

        assert data["member_name"] == "Alice"
        assert data["role"] == "critic"
        assert "timestamp" in data
        assert "content" in data


class TestCouncilSession:
    """Tests for CouncilSession model."""

    def test_create_session(self) -> None:
        """Create a new session."""
        session = CouncilSession(
            council_name="test-council",
            task="Do something",
        )

        assert session.council_name == "test-council"
        assert session.task == "Do something"
        assert session.status == "running"
        assert len(session.session_id) == 36  # UUID format
        assert session.ended_at is None

    def test_complete_session(self, sample_session: CouncilSession) -> None:
        """Mark session as completed."""
        sample_session.complete()

        assert sample_session.status == "completed"
        assert sample_session.ended_at is not None
        assert sample_session.duration_seconds is not None
        assert sample_session.duration_seconds >= 0

    def test_fail_session(self, sample_session: CouncilSession) -> None:
        """Mark session as failed."""
        sample_session.fail("Something went wrong")

        assert sample_session.status == "failed"
        assert sample_session.error_message == "Something went wrong"
        assert sample_session.ended_at is not None

    def test_add_response(
        self,
        sample_session: CouncilSession,
        sample_member_response: MemberResponse,
    ) -> None:
        """Add response to session."""
        sample_session.add_response(sample_member_response)

        assert len(sample_session.member_responses) == 1
        assert sample_session.total_input_tokens > 0

    def test_to_dict(self, sample_session: CouncilSession) -> None:
        """Convert session to dictionary."""
        data = sample_session.to_dict()

        assert data["session_id"] == sample_session.session_id
        assert data["council_name"] == "test-council"
        assert data["status"] == "running"
