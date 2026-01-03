"""Configuration loader for council YAML files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from copilot_council.config.schema import CouncilConfig
from copilot_council.exceptions import ConfigurationError


def load_config(path: str | Path) -> CouncilConfig:
    """Load and validate a council configuration file.

    Parameters
    ----------
    path : str | Path
        Path to the YAML configuration file.

    Returns
    -------
    CouncilConfig
        Validated configuration object.

    Raises
    ------
    ConfigurationError
        If the file cannot be read or validation fails.
    """
    path = Path(path)

    if not path.exists():
        raise ConfigurationError(f"Configuration file not found: {path}")

    if path.suffix.lower() not in (".yaml", ".yml"):
        raise ConfigurationError(f"Configuration file must be YAML: {path}")

    try:
        with open(path) as f:
            data: dict[str, Any] = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML in {path}: {e}") from e

    if data is None:
        raise ConfigurationError(f"Empty configuration file: {path}")

    try:
        return CouncilConfig.model_validate(data)
    except Exception as e:
        raise ConfigurationError(f"Configuration validation failed: {e}") from e


def create_template(path: str | Path, name: str) -> None:
    """Create a template council configuration file.

    Parameters
    ----------
    path : str | Path
        Path to write the template.
    name : str
        Council name.
    """
    template = f"""# Council Configuration: {name}
name: {name}
description: A sample LLM council configuration
strategy: parallel  # Options: parallel, sequential, debate
max_rounds: 3

members:
  - name: alice
    role: critic
    model: gpt-5
    # system_prompt: Optional custom prompt
    # allowed_tools:
    #   - shell(git:*)
    # denied_tools:
    #   - write

  - name: bob
    role: principal_engineer
    model: claude-sonnet-4

  - name: charlie
    role: security_expert
    model: gpt-5

logging:
  level: INFO
  file: ./logs/{name}.log
  format: json
"""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(template)
