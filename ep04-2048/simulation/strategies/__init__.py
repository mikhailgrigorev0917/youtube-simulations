"""Bot strategies for 2048."""

from .random_bot import RandomBot
from .greedy_bot import GreedyBot
from .corner_bot import CornerBot
from .heuristic_bot import HeuristicBot
from .expectimax_bot import ExpectimaxBot

__all__ = [
    "RandomBot",
    "GreedyBot",
    "CornerBot",
    "HeuristicBot",
    "ExpectimaxBot"
]
