"""Configuration management for Copilot Council."""

from copilot_council.config.loader import load_config
from copilot_council.config.schema import CouncilConfig, LoggingConfig, MemberConfig

__all__ = [
    "CouncilConfig",
    "LoggingConfig",
    "MemberConfig",
    "load_config",
]
