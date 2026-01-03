"""Deliberation strategies for council execution."""

from copilot_council.strategies.base import Strategy
from copilot_council.strategies.debate import DebateStrategy
from copilot_council.strategies.parallel import ParallelStrategy
from copilot_council.strategies.sequential import SequentialStrategy

__all__ = [
    "DebateStrategy",
    "ParallelStrategy",
    "SequentialStrategy",
    "Strategy",
]

STRATEGY_REGISTRY: dict[str, type[Strategy]] = {
    "parallel": ParallelStrategy,
    "sequential": SequentialStrategy,
    "debate": DebateStrategy,
}


def get_strategy(name: str) -> type[Strategy]:
    """Get a strategy class by name.

    Parameters
    ----------
    name : str
        Strategy name.

    Returns
    -------
    type[Strategy]
        Strategy class.

    Raises
    ------
    ValueError
        If strategy name is not recognized.
    """
    if name not in STRATEGY_REGISTRY:
        valid = ", ".join(STRATEGY_REGISTRY.keys())
        raise ValueError(f"Unknown strategy '{name}'. Valid options: {valid}")
    return STRATEGY_REGISTRY[name]
