"""Custom exceptions for Copilot Council."""


class CouncilError(Exception):
    """Base exception for all council errors."""

    pass


class ConfigurationError(CouncilError):
    """Invalid configuration."""

    pass


class CopilotExecutionError(CouncilError):
    """Copilot CLI execution failed."""

    pass


class CopilotAuthError(CopilotExecutionError):
    """Authentication with Copilot failed."""

    pass


class CopilotTimeoutError(CopilotExecutionError):
    """Copilot CLI timed out."""

    pass


class ValidationError(CouncilError):
    """Response validation failed."""

    pass


class StrategyError(CouncilError):
    """Strategy execution failed."""

    pass
