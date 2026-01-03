"""Parallel execution strategy."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from copilot_council.models.response import MemberResponse
from copilot_council.strategies.base import Strategy

if TYPE_CHECKING:
    from copilot_council.models.member import CouncilMember
    from copilot_council.models.session import CouncilSession

logger = logging.getLogger(__name__)


class ParallelStrategy(Strategy):
    """Execute all members in parallel.

    All members receive the same task and respond independently.
    Responses are collected and returned together.
    """

    @property
    def name(self) -> str:
        """Return strategy name."""
        return "parallel"

    async def execute(
        self,
        members: list[CouncilMember],
        task: str,
        session: CouncilSession,
        max_rounds: int = 1,
    ) -> list[MemberResponse]:
        """Execute all members in parallel.

        Parameters
        ----------
        members : list[CouncilMember]
            Council members to query.
        task : str
            The task prompt.
        session : CouncilSession
            Session tracker.
        max_rounds : int, optional
            Ignored for parallel strategy.

        Returns
        -------
        list[MemberResponse]
            All member responses.
        """
        logger.info(f"Executing parallel strategy with {len(members)} members")

        tasks = [self._query_member(member, task) for member in members]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        responses: list[MemberResponse] = []
        for i, result in enumerate(results):
            if isinstance(result, BaseException):
                logger.error(f"Member {members[i].name} failed: {result}")
                continue
            response: MemberResponse = result
            responses.append(response)
            session.add_response(response)

        logger.info(f"Parallel strategy completed with {len(responses)} responses")
        return responses
