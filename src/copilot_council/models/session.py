"""Session tracking for council runs."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from copilot_council.models.response import MemberResponse


@dataclass
class CouncilSession:
    """Tracks a single council deliberation session.

    Attributes
    ----------
    session_id : str
        Unique UUID4 identifier for this session.
    council_name : str
        Name of the council configuration.
    task : str
        The task/prompt given to the council.
    started_at : datetime
        UTC timestamp when session started.
    ended_at : datetime | None
        UTC timestamp when session ended, or None if still running.
    status : str
        Current status: "running", "completed", "failed".
    """

    council_name: str
    task: str
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    ended_at: datetime | None = None
    status: str = "running"
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    member_responses: list[MemberResponse] = field(default_factory=list)
    error_message: str | None = None

    def complete(self) -> None:
        """Mark session as completed."""
        self.ended_at = datetime.now(UTC)
        self.status = "completed"

    def fail(self, error: str) -> None:
        """Mark session as failed."""
        self.ended_at = datetime.now(UTC)
        self.status = "failed"
        self.error_message = error

    @property
    def duration_seconds(self) -> float | None:
        """Calculate session duration in seconds."""
        if self.ended_at is None:
            return None
        return (self.ended_at - self.started_at).total_seconds()

    def add_response(self, response: MemberResponse) -> None:
        """Add a member response and update token counts."""
        self.member_responses.append(response)
        self.total_input_tokens += response.response.input_tokens
        self.total_output_tokens += response.response.output_tokens

    def to_dict(self) -> dict:
        """Convert session to dictionary for logging."""
        return {
            "session_id": self.session_id,
            "council_name": self.council_name,
            "task": self.task,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "status": self.status,
            "duration_seconds": self.duration_seconds,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "error_message": self.error_message,
            "member_count": len(self.member_responses),
        }
