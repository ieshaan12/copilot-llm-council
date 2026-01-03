"""Sequential execution strategy."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from copilot_council.models.response import MemberResponse
from copilot_council.strategies.base import Strategy

if TYPE_CHECKING:
    from copilot_council.models.member import CouncilMember
    from copilot_council.models.session import CouncilSession

logger = logging.getLogger(__name__)


class SequentialStrategy(Strategy):
    """Execute members sequentially, passing context forward.

    Each member sees the previous members' responses and builds upon them.
    """

    @property
    def name(self) -> str:
        """Return strategy name."""
        return "sequential"

    async def execute(
        self,
        members: list[CouncilMember],
        task: str,
        session: CouncilSession,
        max_rounds: int = 1,
    ) -> list[MemberResponse]:
        """Execute members one by one, building context.

        Parameters
        ----------
        members : list[CouncilMember]
            Council members to query.
        task : str
            The task prompt.
        session : CouncilSession
            Session tracker.
        max_rounds : int, optional
            Ignored for sequential strategy.

        Returns
        -------
        list[MemberResponse]
            All member responses in order.
        """
        logger.info(f"Executing sequential strategy with {len(members)} members")

        responses: list[MemberResponse] = []

        for i, member in enumerate(members):
            # Build prompt with previous responses
            if responses:
                prompt = self._build_context(task, responses)
            else:
                prompt = task

            logger.debug(f"Querying member {i + 1}/{len(members)}: {member.name}")
            response = await self._query_member(member, prompt)
            responses.append(response)
            session.add_response(response)

        logger.info(f"Sequential strategy completed with {len(responses)} responses")
        return responses

    def _build_context(
        self,
        original_task: str,
        previous_responses: list[MemberResponse],
    ) -> str:
        """Build context prompt including previous responses.

        Parameters
        ----------
        original_task : str
            The original task.
        previous_responses : list[MemberResponse]
            Responses from previous members.

        Returns
        -------
        str
            Combined prompt with context.
        """
        parts = [
            f"Original Task: {original_task}",
            "",
            "Previous council members have provided the following input:",
        ]

        for r in previous_responses:
            parts.append(f"\n--- {r.member_name} ({r.role}) ---")
            parts.append(r.response.content)

        parts.append("\n\n---")
        parts.append("Build upon the above responses and provide your perspective:")

        return "\n".join(parts)
