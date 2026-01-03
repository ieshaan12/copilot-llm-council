"""Unit tests for configuration loading."""

import tempfile

import pytest

from copilot_council.config.loader import load_config
from copilot_council.config.schema import CouncilConfig, MemberConfig
from copilot_council.exceptions import ConfigurationError


class TestConfigSchema:
    """Tests for configuration schema validation."""

    def test_valid_config(self, sample_config_dict: dict) -> None:
        """Valid config should pass validation."""
        config = CouncilConfig.model_validate(sample_config_dict)

        assert config.name == "test-council"
        assert config.strategy == "parallel"
        assert len(config.members) == 2

    def test_missing_name_fails(self, sample_config_dict: dict) -> None:
        """Config without name should fail."""
        del sample_config_dict["name"]

        with pytest.raises(ValueError):
            CouncilConfig.model_validate(sample_config_dict)

    def test_empty_members_fails(self, sample_config_dict: dict) -> None:
        """Config with no members should fail."""
        sample_config_dict["members"] = []

        with pytest.raises(ValueError):
            CouncilConfig.model_validate(sample_config_dict)

    def test_max_rounds_bounds(self, sample_config_dict: dict) -> None:
        """max_rounds should be between 1 and 10."""
        sample_config_dict["max_rounds"] = 15

        with pytest.raises(ValueError):
            CouncilConfig.model_validate(sample_config_dict)

    def test_member_config_defaults(self) -> None:
        """Member config should have sensible defaults."""
        member = MemberConfig(name="test", role="critic")

        assert member.model == "gpt-5"
        assert member.system_prompt is None
        assert member.allowed_tools == []
        assert member.denied_tools == []


class TestConfigLoader:
    """Tests for loading config from files."""

    def test_load_valid_yaml(self, sample_config_dict: dict) -> None:
        """Load a valid YAML config file."""
        import yaml

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(sample_config_dict, f)
            f.flush()

            config = load_config(f.name)

            assert config.name == "test-council"
            assert len(config.members) == 2

    def test_file_not_found(self) -> None:
        """Non-existent file should raise error."""
        with pytest.raises(ConfigurationError, match="not found"):
            load_config("/nonexistent/path/config.yaml")

    def test_invalid_extension(self) -> None:
        """Non-YAML extension should raise error."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"not yaml")
            f.flush()

            with pytest.raises(ConfigurationError, match="must be YAML"):
                load_config(f.name)

    def test_invalid_yaml_syntax(self) -> None:
        """Invalid YAML should raise error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            f.flush()

            with pytest.raises(ConfigurationError, match="Invalid YAML"):
                load_config(f.name)

    def test_empty_file(self) -> None:
        """Empty file should raise error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            f.flush()

            with pytest.raises(ConfigurationError, match="Empty"):
                load_config(f.name)
