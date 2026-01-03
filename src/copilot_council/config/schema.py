"""Pydantic schemas for configuration validation."""

from pydantic import BaseModel, Field


class MemberConfig(BaseModel):
    """Configuration for a council member."""

    name: str = Field(..., description="Unique member name")
    role: str = Field(..., description="Role name")
    model: str = Field(default="gpt-5", description="Model identifier")
    system_prompt: str | None = Field(default=None, description="Custom prompt override")
    allowed_tools: list[str] = Field(default_factory=list)
    denied_tools: list[str] = Field(default_factory=list)


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO")
    file: str | None = Field(default=None, description="Log file path")
    format: str = Field(default="json")


class CouncilConfig(BaseModel):
    """Root configuration for a council."""

    name: str = Field(..., description="Council name")
    description: str = Field(default="", description="Council description")
    strategy: str = Field(default="parallel")
    max_rounds: int = Field(default=3, ge=1, le=10)
    members: list[MemberConfig] = Field(..., min_length=1)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    def to_dict(self) -> dict:
        """Convert to dictionary for Council.from_config()."""
        return {
            "name": self.name,
            "description": self.description,
            "strategy": self.strategy,
            "max_rounds": self.max_rounds,
            "members": [m.model_dump() for m in self.members],
            "logging": self.logging.model_dump(),
        }
