"""Unit tests for Council class."""

import pytest

from copilot_council.council import Council, CouncilResult
from copilot_council.models.member import CouncilMember


class TestCouncil:
    """Tests for Council orchestrator."""

    def test_create_council(self) -> None:
        """Create a basic council."""
        members = [
            CouncilMember(name="alice", role="critic"),
            CouncilMember(name="bob", role="principal_engineer"),
        ]

        council = Council(
            name="test-council",
            members=members,
            strategy="parallel",
        )

        assert council.name == "test-council"
        assert len(council.members) == 2
        assert council.strategy == "parallel"
        assert council.max_rounds == 3

    def test_create_council_with_strategy_name(self) -> None:
        """Create council with strategy as string."""
        members = [CouncilMember(name="alice", role="critic")]

        council = Council(name="test", members=members, strategy="sequential")

        assert council.strategy == "sequential"

    def test_invalid_strategy_raises_error(self) -> None:
        """Unknown strategy should raise error."""
        members = [CouncilMember(name="alice", role="critic")]

        with pytest.raises(ValueError, match="Unknown strategy"):
            Council(name="test", members=members, strategy="invalid")

    def test_from_config(self, sample_config_dict: dict) -> None:
        """Create council from config dictionary."""
        council = Council.from_config(sample_config_dict)

        assert council.name == "test-council"
        assert len(council.members) == 2
        assert council.members[0].name == "alice"
        assert council.members[1].model == "claude-sonnet-4"


class TestCouncilResult:
    """Tests for CouncilResult."""

    def test_to_markdown(self, sample_session, sample_member_response) -> None:
        """Convert result to markdown."""
        sample_session.complete()
        result = CouncilResult(
            session=sample_session,
            responses=[sample_member_response],
        )

        markdown = result.to_markdown()

        assert "# Council Deliberation:" in markdown
        assert sample_session.session_id in markdown
        assert "Alice" in markdown
        assert "critic" in markdown
