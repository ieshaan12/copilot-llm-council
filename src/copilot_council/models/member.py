"""Council member model definitions."""

from dataclasses import dataclass, field


@dataclass
class CouncilMember:
    """A member of an LLM council.

    Represents an individual AI agent with a specific role, model,
    and permission set within the council.

    Attributes
    ----------
    name : str
        Unique identifier for this member within the council.
    role : str
        Role name that determines behavior (e.g., "critic", "engineer").
    model : str
        Model identifier for Copilot CLI (e.g., "gpt-5", "claude-sonnet-4").
    system_prompt : str | None
        Custom system prompt override. If None, uses role's default.
    allowed_tools : list[str]
        Tool patterns to allow (e.g., ["shell(git:*)", "write"]).
    denied_tools : list[str]
        Tool patterns to deny (takes precedence over allowed).
    """

    name: str
    role: str
    model: str = "gpt-5"
    system_prompt: str | None = None
    allowed_tools: list[str] = field(default_factory=list)
    denied_tools: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate member configuration."""
        if not self.name.strip():
            raise ValueError("Member name cannot be empty")
        if not self.role.strip():
            raise ValueError("Member role cannot be empty")
