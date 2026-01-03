"""Unit tests for Copilot CLI adapter."""

from copilot_council.adapters.copilot import CopilotAdapter
from copilot_council.models.response import CopilotResponse


class TestCommandBuilding:
    """Tests for building CLI commands."""

    def test_basic_command(self) -> None:
        """Build basic command with defaults."""
        adapter = CopilotAdapter()
        cmd = adapter._build_command(
            prompt="Hello",
            model="gpt-5",
            allowed_tools=None,
            denied_tools=None,
        )

        assert cmd[0] == "copilot"
        assert "--model" in cmd
        assert "gpt-5" in cmd
        assert "-p" in cmd
        assert "Hello" in cmd
        assert "--no-color" in cmd
        assert "--allow-all-tools" in cmd

    def test_command_with_allowed_tools(self) -> None:
        """Build command with allowed tools."""
        adapter = CopilotAdapter()
        cmd = adapter._build_command(
            prompt="Test",
            model="gpt-5",
            allowed_tools=["shell(git:*)", "read"],
            denied_tools=None,
        )

        assert "--allow-tool" in cmd
        assert "shell(git:*)" in cmd
        assert "read" in cmd
        assert "--allow-all-tools" not in cmd

    def test_command_with_denied_tools(self) -> None:
        """Build command with denied tools."""
        adapter = CopilotAdapter()
        cmd = adapter._build_command(
            prompt="Test",
            model="claude-sonnet-4",
            allowed_tools=None,
            denied_tools=["write", "shell(*)"],
        )

        assert "--deny-tool" in cmd
        assert "write" in cmd
        assert "shell(*)" in cmd


class TestResponseParsing:
    """Tests for parsing CLI output."""

    def test_parse_response_extracts_content(
        self,
        mock_copilot_output: str,
    ) -> None:
        """Content should be extracted before usage stats."""
        adapter = CopilotAdapter()
        response = adapter._parse_response(mock_copilot_output, "gpt-5")

        assert "response content from the model" in response.content
        assert "def hello():" in response.content
        assert "Total usage est:" not in response.content

    def test_parse_response_extracts_tokens_with_k_suffix(
        self,
        mock_copilot_output: str,
    ) -> None:
        """Token counts with 'k' suffix should be parsed correctly."""
        adapter = CopilotAdapter()
        response = adapter._parse_response(mock_copilot_output, "gpt-5")

        assert response.input_tokens == 5500  # 5.5k
        assert response.output_tokens == 150

    def test_parse_response_extracts_tokens_without_suffix(
        self,
        mock_copilot_output_simple: str,
    ) -> None:
        """Token counts without 'k' suffix."""
        adapter = CopilotAdapter()
        response = adapter._parse_response(mock_copilot_output_simple, "gpt-5")

        assert response.input_tokens == 1000
        assert response.output_tokens == 10

    def test_parse_response_extracts_duration(
        self,
        mock_copilot_output: str,
    ) -> None:
        """Durations should be parsed from usage stats."""
        adapter = CopilotAdapter()
        response = adapter._parse_response(mock_copilot_output, "gpt-5")

        assert response.duration_api == 5.0
        assert response.duration_wall == 8.0

    def test_parse_simple_response(self) -> None:
        """Parse response without usage stats."""
        adapter = CopilotAdapter()
        response = adapter._parse_response("Just a simple answer.", "gpt-5")

        assert response.content == "Just a simple answer."
        assert response.input_tokens == 0
        assert response.output_tokens == 0


class TestResponseValidation:
    """Tests for response validation."""

    def test_empty_response_is_invalid(self) -> None:
        """Empty responses should fail validation."""
        adapter = CopilotAdapter()
        response = CopilotResponse(content="", model="gpt-5", raw_output="")

        validated = adapter._validate_response(response)

        assert validated.is_valid is False
        assert "Empty response received" in validated.validation_errors

    def test_whitespace_only_is_invalid(self) -> None:
        """Whitespace-only responses should fail validation."""
        adapter = CopilotAdapter()
        response = CopilotResponse(content="   \n\t  ", model="gpt-5", raw_output="")

        validated = adapter._validate_response(response)

        assert validated.is_valid is False

    def test_valid_response_passes(self, sample_response: CopilotResponse) -> None:
        """Valid responses should pass validation."""
        adapter = CopilotAdapter()

        validated = adapter._validate_response(sample_response)

        assert validated.is_valid is True
        assert validated.validation_errors == []

    def test_error_indicator_detected(self) -> None:
        """Error patterns in response should be detected."""
        adapter = CopilotAdapter()
        response = CopilotResponse(
            content="Error: something went wrong",
            model="gpt-5",
            raw_output="",
        )

        validated = adapter._validate_response(response)

        assert validated.is_valid is False
        assert any("Error indicator" in e for e in validated.validation_errors)

    def test_rate_limit_detected(self) -> None:
        """Rate limit messages should be detected."""
        adapter = CopilotAdapter()
        response = CopilotResponse(
            content="You have hit a rate limit. Please try again later.",
            model="gpt-5",
            raw_output="",
        )

        validated = adapter._validate_response(response)

        assert validated.is_valid is False
        assert any("Rate limit" in e for e in validated.validation_errors)
