"""Base strategy protocol."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from copilot_council.adapters.copilot import CopilotAdapter
from copilot_council.models.response import CopilotResponse, MemberResponse
from copilot_council.roles.predefined import get_role

if TYPE_CHECKING:
    from copilot_council.models.member import CouncilMember
    from copilot_council.models.session import CouncilSession

logger = logging.getLogger(__name__)


class Strategy(ABC):
    """Abstract base class for council deliberation strategies.

    Subclasses must implement the `execute` method to define
    how members interact and produce responses.

    Attributes
    ----------
    adapter : CopilotAdapter
        The Copilot CLI adapter for queries.
    """

    def __init__(self, adapter: CopilotAdapter | None = None) -> None:
        """Initialize the strategy.

        Parameters
        ----------
        adapter : CopilotAdapter | None, optional
            Copilot adapter to use, creates default if None.
        """
        self.adapter = adapter or CopilotAdapter()

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the strategy name."""
        ...

    @abstractmethod
    async def execute(
        self,
        members: list[CouncilMember],
        task: str,
        session: CouncilSession,
        max_rounds: int = 1,
    ) -> list[MemberResponse]:
        """Execute the deliberation strategy.

        Parameters
        ----------
        members : list[CouncilMember]
            List of council members.
        task : str
            The task/prompt for the council.
        session : CouncilSession
            The session tracker for logging.
        max_rounds : int, optional
            Maximum deliberation rounds, by default 1.

        Returns
        -------
        list[MemberResponse]
            All responses generated during deliberation.
        """
        ...

    async def _query_member(
        self,
        member: CouncilMember,
        prompt: str,
        round_number: int = 1,
    ) -> MemberResponse:
        """Query a single member and return response.

        Parameters
        ----------
        member : CouncilMember
            The member to query.
        prompt : str
            The prompt to send.
        round_number : int, optional
            Current round number, by default 1.

        Returns
        -------
        MemberResponse
            The member's response.
        """
        # Get system prompt from role or member override
        system_prompt = member.system_prompt
        if not system_prompt:
            role = get_role(member.role)
            if role:
                system_prompt = role.system_prompt

        # Get denied tools from role defaults
        denied_tools = list(member.denied_tools)
        role = get_role(member.role)
        if role and role.default_denied_tools:
            denied_tools.extend(role.default_denied_tools)

        # Log the request (DEBUG level for verbose output)
        logger.debug(
            "Querying member '%s' (role: %s, model: %s)",
            member.name,
            member.role,
            member.model,
            extra={
                "member_name": member.name,
                "role": member.role,
                "model": member.model,
                "round": round_number,
                "prompt": prompt,
                "system_prompt": system_prompt or "",
            },
        )

        response: CopilotResponse = await self.adapter.query(
            prompt=prompt,
            model=member.model,
            allowed_tools=member.allowed_tools if member.allowed_tools else None,
            denied_tools=denied_tools if denied_tools else None,
            system_prompt=system_prompt,
        )

        # Log the response (DEBUG level for verbose output)
        logger.debug(
            "Response from '%s' (round %d): %d input tokens, %d output tokens",
            member.name,
            round_number,
            response.input_tokens,
            response.output_tokens,
            extra={
                "member_name": member.name,
                "round": round_number,
                "content": response.content,
                "raw_output": response.raw_output,
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "duration_api": response.duration_api,
                "duration_wall": response.duration_wall,
                "is_valid": response.is_valid,
                "validation_errors": response.validation_errors,
            },
        )

        return MemberResponse(
            member_name=member.name,
            role=member.role,
            response=response,
            timestamp=datetime.now(UTC),
            round_number=round_number,
        )
