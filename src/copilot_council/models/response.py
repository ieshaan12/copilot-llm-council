"""Response models for Copilot CLI output."""

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class CopilotResponse:
    """Parsed response from Copilot CLI.

    Attributes
    ----------
    content : str
        The actual response text (parsed from CLI output).
    model : str
        Model that generated the response.
    prompt : str
        The prompt that was sent.
    system_prompt : str
        The system prompt used (if any).
    input_tokens : int
        Number of input tokens used.
    output_tokens : int
        Number of output tokens generated.
    duration_api : float
        API processing duration in seconds.
    duration_wall : float
        Wall clock duration in seconds.
    raw_output : str
        Full CLI output for debugging.
    is_valid : bool
        Whether response passed validation.
    validation_errors : list[str]
        List of validation error messages.
    """

    content: str
    model: str
    prompt: str = ""
    system_prompt: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    duration_api: float = 0.0
    duration_wall: float = 0.0
    raw_output: str = ""
    is_valid: bool = True
    validation_errors: list[str] = field(default_factory=list)


@dataclass
class MemberResponse:
    """Response from a council member.

    Attributes
    ----------
    member_name : str
        Name of the member who generated this response.
    role : str
        Role of the member.
    response : CopilotResponse
        The underlying Copilot response.
    timestamp : datetime
        When the response was received.
    round_number : int
        Which deliberation round this response is from.
    """

    member_name: str
    role: str
    response: CopilotResponse
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    round_number: int = 1

    def to_dict(self) -> dict:
        """Convert to dictionary for logging."""
        return {
            "member_name": self.member_name,
            "role": self.role,
            "round_number": self.round_number,
            "timestamp": self.timestamp.isoformat(),
            "prompt": self.response.prompt,
            "system_prompt": self.response.system_prompt,
            "content": self.response.content,
            "model": self.response.model,
            "input_tokens": self.response.input_tokens,
            "output_tokens": self.response.output_tokens,
            "duration_api": self.response.duration_api,
            "duration_wall": self.response.duration_wall,
            "raw_output": self.response.raw_output,
            "is_valid": self.response.is_valid,
            "validation_errors": self.response.validation_errors,
        }
