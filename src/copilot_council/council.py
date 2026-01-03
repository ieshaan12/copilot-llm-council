"""Council orchestration class."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from copilot_council.adapters.copilot import CopilotAdapter
from copilot_council.models.member import CouncilMember
from copilot_council.models.response import MemberResponse
from copilot_council.models.session import CouncilSession
from copilot_council.strategies import Strategy, get_strategy

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class CouncilResult:
    """Result of a council deliberation.

    Attributes
    ----------
    session : CouncilSession
        The session tracking information.
    responses : list[MemberResponse]
        All member responses.
    """

    session: CouncilSession
    responses: list[MemberResponse] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Convert result to markdown format.

        Returns
        -------
        str
            Markdown formatted result.
        """
        lines = [
            f"# Council Deliberation: {self.session.council_name}",
            "",
            f"**Session ID:** `{self.session.session_id}`",
            f"**Task:** {self.session.task}",
            f"**Status:** {self.session.status}",
            f"**Duration:** {self.session.duration_seconds:.1f}s"
            if self.session.duration_seconds
            else "**Duration:** N/A",
            f"**Total Tokens:** {self.session.total_input_tokens} input, "
            f"{self.session.total_output_tokens} output",
            "",
            "---",
            "",
        ]

        # Group by round
        rounds: dict[int, list[MemberResponse]] = {}
        for r in self.responses:
            rounds.setdefault(r.round_number, []).append(r)

        for round_num in sorted(rounds.keys()):
            lines.append(f"## Round {round_num}")
            lines.append("")

            for r in rounds[round_num]:
                lines.append(f"### {r.member_name} ({r.role})")
                lines.append("")
                lines.append(f"*Model: {r.response.model}*")
                lines.append("")
                lines.append(r.response.content)
                lines.append("")

        return "\n".join(lines)


class Council:
    """LLM Council orchestrator.

    Manages a group of council members and executes deliberation strategies.

    Attributes
    ----------
    name : str
        Council name.
    members : list[CouncilMember]
        List of council members.
    strategy : Strategy
        Deliberation strategy.
    max_rounds : int
        Maximum deliberation rounds.
    """

    def __init__(
        self,
        name: str,
        members: list[CouncilMember],
        strategy: str | Strategy = "parallel",
        max_rounds: int = 3,
        adapter: CopilotAdapter | None = None,
    ) -> None:
        """Initialize the council.

        Parameters
        ----------
        name : str
            Council name.
        members : list[CouncilMember]
            List of council members.
        strategy : str | Strategy, optional
            Strategy name or instance, by default "parallel".
        max_rounds : int, optional
            Maximum rounds for debate, by default 3.
        adapter : CopilotAdapter | None, optional
            Shared adapter instance.
        """
        self.name = name
        self.members = members
        self.max_rounds = max_rounds
        self._adapter = adapter or CopilotAdapter()

        if isinstance(strategy, str):
            strategy_cls = get_strategy(strategy)
            self._strategy = strategy_cls(adapter=self._adapter)
        else:
            self._strategy = strategy

    @property
    def strategy(self) -> str:
        """Get strategy name."""
        return self._strategy.name

    async def deliberate(self, task: str) -> CouncilResult:
        """Run a council deliberation on a task.

        Parameters
        ----------
        task : str
            The task/prompt for the council.

        Returns
        -------
        CouncilResult
            The deliberation result with all responses.
        """
        session = CouncilSession(
            council_name=self.name,
            task=task,
        )

        logger.info(f"Starting council '{self.name}' deliberation (session: {session.session_id})")
        logger.info(f"Strategy: {self.strategy}, Members: {len(self.members)}")

        try:
            responses = await self._strategy.execute(
                members=self.members,
                task=task,
                session=session,
                max_rounds=self.max_rounds,
            )
            session.complete()
            logger.info(f"Council deliberation completed in {session.duration_seconds:.1f}s")

        except Exception as e:
            session.fail(str(e))
            logger.error(f"Council deliberation failed: {e}")
            responses = session.member_responses  # Return partial responses

        return CouncilResult(session=session, responses=responses)

    @classmethod
    def from_config(cls, config: dict) -> Council:
        """Create a council from configuration dict.

        Parameters
        ----------
        config : dict
            Council configuration.

        Returns
        -------
        Council
            Configured council instance.
        """
        members = [
            CouncilMember(
                name=m["name"],
                role=m["role"],
                model=m.get("model", "gpt-5"),
                system_prompt=m.get("system_prompt"),
                allowed_tools=m.get("allowed_tools", []),
                denied_tools=m.get("denied_tools", []),
            )
            for m in config["members"]
        ]

        return cls(
            name=config["name"],
            members=members,
            strategy=config.get("strategy", "parallel"),
            max_rounds=config.get("max_rounds", 3),
        )
