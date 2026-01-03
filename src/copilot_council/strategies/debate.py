"""Debate strategy with multiple rounds."""

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


class DebateStrategy(Strategy):
    """Multi-round debate between members.

    Round 1: All members respond to original task.
    Round 2+: Members critique/respond to each other.
    Final round: Synthesis.
    """

    @property
    def name(self) -> str:
        """Return strategy name."""
        return "debate"

    async def execute(
        self,
        members: list[CouncilMember],
        task: str,
        session: CouncilSession,
        max_rounds: int = 3,
    ) -> list[MemberResponse]:
        """Execute multi-round debate.

        Parameters
        ----------
        members : list[CouncilMember]
            Council members to query.
        task : str
            The task prompt.
        session : CouncilSession
            Session tracker.
        max_rounds : int, optional
            Number of debate rounds, by default 3.

        Returns
        -------
        list[MemberResponse]
            All responses from all rounds.
        """
        logger.info(f"Executing debate strategy with {len(members)} members, {max_rounds} rounds")

        all_responses: list[MemberResponse] = []

        for round_num in range(1, max_rounds + 1):
            logger.info(f"Starting round {round_num}/{max_rounds}")
            round_responses = await self._execute_round(
                members, task, all_responses, round_num, session
            )
            all_responses.extend(round_responses)

        logger.info(f"Debate completed with {len(all_responses)} total responses")
        return all_responses

    async def _execute_round(
        self,
        members: list[CouncilMember],
        original_task: str,
        previous_responses: list[MemberResponse],
        round_num: int,
        session: CouncilSession,
    ) -> list[MemberResponse]:
        """Execute a single debate round.

        Parameters
        ----------
        members : list[CouncilMember]
            Council members.
        original_task : str
            Original task prompt.
        previous_responses : list[MemberResponse]
            All previous responses.
        round_num : int
            Current round number.
        session : CouncilSession
            Session tracker.

        Returns
        -------
        list[MemberResponse]
            Responses from this round.
        """
        if round_num == 1:
            # First round: parallel initial responses
            tasks = [self._query_member(member, original_task, round_num) for member in members]
        else:
            # Subsequent rounds: respond to others
            tasks = [
                self._query_member(
                    member,
                    self._build_debate_prompt(
                        member.name, original_task, previous_responses, round_num
                    ),
                    round_num,
                )
                for member in members
            ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        responses: list[MemberResponse] = []
        for i, result in enumerate(results):
            if isinstance(result, BaseException):
                logger.error(f"Member {members[i].name} failed in round {round_num}: {result}")
                continue
            response: MemberResponse = result
            responses.append(response)
            session.add_response(response)

        return responses

    def _build_debate_prompt(
        self,
        member_name: str,
        original_task: str,
        previous_responses: list[MemberResponse],
        round_num: int,
    ) -> str:
        """Build debate prompt for a member.

        Parameters
        ----------
        member_name : str
            Name of the member being prompted.
        original_task : str
            Original task.
        previous_responses : list[MemberResponse]
            All previous responses.
        round_num : int
            Current round number.

        Returns
        -------
        str
            Debate prompt.
        """
        # Get responses from OTHER members in recent rounds
        other_responses = [r for r in previous_responses if r.member_name != member_name]

        # Also get this member's previous response for reference
        own_responses = [r for r in previous_responses if r.member_name == member_name]

        parts = [
            f"Original Task: {original_task}",
            "",
            f"This is round {round_num} of the debate.",
            "",
        ]

        if own_responses:
            parts.append("Your previous response:")
            parts.append(f"  {own_responses[-1].response.content[:500]}...")
            parts.append("")

        parts.append("Other council members have said:")
        for r in other_responses[-len(other_responses) :]:  # Recent responses
            parts.append(f"\n--- {r.member_name} ({r.role}, Round {r.round_number}) ---")
            parts.append(r.response.content)

        parts.append("\n---")
        parts.append(
            "Consider the above perspectives. Critique if needed, "
            "refine your position, and provide your updated response:"
        )

        return "\n".join(parts)
