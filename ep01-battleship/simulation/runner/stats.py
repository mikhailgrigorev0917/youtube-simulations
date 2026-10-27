from __future__ import annotations
from dataclasses import dataclass
import statistics
from typing import Optional

from simulation.core.models import GameResult


@dataclass
class MatchupStats:
    placement: str
    shooting: str
    games_count: int
    mean_turns: float
    median_turns: float
    std_turns: float
    min_turns: int
    max_turns: int
    p10_turns: float
    p90_turns: float
    turns_list: list[int]
    sample_game: Optional[GameResult] = None

    @classmethod
    def from_results(
        cls,
        placement: str,
        shooting: str,
        results: list[GameResult],
        sample_game: Optional[GameResult] = None,
    ) -> MatchupStats:
        turns = [r.turns for r in results]
        n = len(turns)
        if n == 0:
            raise ValueError("Cannot calculate stats from empty results")

        mean = statistics.mean(turns)
        median = statistics.median(turns)
        std = statistics.stdev(turns) if n > 1 else 0.0
        sorted_turns = sorted(turns)
        p10 = sorted_turns[int(0.10 * n)]
        p90 = sorted_turns[min(int(0.90 * n), n - 1)]

        return cls(
            placement=placement,
            shooting=shooting,
            games_count=n,
            mean_turns=round(mean, 2),
            median_turns=round(median, 2),
            std_turns=round(std, 2),
            min_turns=min(turns),
            max_turns=max(turns),
            p10_turns=round(p10, 2),
            p90_turns=round(p90, 2),
            turns_list=turns,
            sample_game=sample_game or (results[0] if results else None),
        )
