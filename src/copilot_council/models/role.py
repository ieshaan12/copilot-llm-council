"""Predefined role definitions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Role:
    """A council member role with default prompts and permissions.

    Attributes
    ----------
    name : str
        Role identifier (e.g., "critic", "principal_engineer").
    description : str
        Human-readable description of the role's purpose.
    system_prompt : str
        Default system prompt for members with this role.
    default_denied_tools : tuple[str, ...]
        Tools denied by default for this role.
    """

    name: str
    description: str
    system_prompt: str
    default_denied_tools: tuple[str, ...] = ()

    def __str__(self) -> str:
        """Return string representation."""
        return f"Role({self.name})"
