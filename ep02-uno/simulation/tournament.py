from __future__ import annotations
import os
import random
import time
from concurrent.futures import ProcessPoolExecutor
from typing import List, Dict, Any, Type, Tuple

from game import UnoGame
from strategies.base import BaseStrategy
from strategies import (
    RandomStrategy,
    GreedyColorStrategy,
    AggressiveAttackerStrategy,
    TacticalSniperStrategy,
    CardCounterStrategy,
    PointMinimizerStrategy,
)

ALL_STRATEGIES: List[Type[BaseStrategy]] = [
    RandomStrategy,
    GreedyColorStrategy,
    AggressiveAttackerStrategy,
    TacticalSniperStrategy,
    CardCounterStrategy,
    PointMinimizerStrategy,
]
STRATEGY_BY_NAME: Dict[str, Type[BaseStrategy]] = {cls().name: cls for cls in ALL_STRATEGIES}


def _play_chunk(args: Tuple[List[List[str]], List[int], bool, bool]) -> List[Dict[str, Any]]:
    """Worker: plays a batch of games. Each lineup is a list of strategy names (seat order)."""
    lineups, seeds, stacking, restrict_w4 = args
    out = []
    for lineup, seed in zip(lineups, seeds):
        random.seed(seed)  # strategies use the global RNG for tie-breaks
        players = [STRATEGY_BY_NAME[n]() for n in lineup]
        stats = UnoGame(players, allow_stacking=stacking, restrict_wild_draw_four=restrict_w4, seed=seed).run()
        out.append({
            "lineup": lineup,
            "winner": stats.winner_index,
            "turns": stats.total_turns,
            "points": stats.final_hand_points,
            "penalties": stats.penalties,
            "drawn": stats.cards_drawn_per_player,
        })
    return out


def run_games(
    lineups: List[List[str]],
    stacking: bool = False,
    restrict_w4: bool = True,
    base_seed: int = 0,
    workers: int | None = None,
) -> List[Dict[str, Any]]:
    workers = workers or max(1, (os.cpu_count() or 2) - 1)
    seeds = [base_seed + i for i in range(len(lineups))]
    chunk = max(50, len(lineups) // (workers * 4) + 1)
    jobs = [
        (lineups[i:i + chunk], seeds[i:i + chunk], stacking, restrict_w4)
        for i in range(0, len(lineups), chunk)
    ]
    results: List[Dict[str, Any]] = []
    if workers == 1:
        for j in jobs:
            results.extend(_play_chunk(j))
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for part in ex.map(_play_chunk, jobs):
                results.extend(part)
    return results


def random_lineups(names: List[str], n_games: int, seats: int = 4, seed: int = 0) -> List[List[str]]:
    """Random distinct 4-strategy tables with shuffled seats (removes seat-order bias)."""
    rng = random.Random(seed)
    return [rng.sample(names, seats) for _ in range(n_games)]


def summarize(results: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    wins: Dict[str, int] = {}
    played: Dict[str, int] = {}
    pts: Dict[str, int] = {}
    for r in results:
        for seat, name in enumerate(r["lineup"]):
            played[name] = played.get(name, 0) + 1
            pts[name] = pts.get(name, 0) + r["points"][seat]
            if r["winner"] == seat:
                wins[name] = wins.get(name, 0) + 1
    table = {}
    for name in played:
        n = played[name]
        w = wins.get(name, 0)
        p = w / n
        se = (p * (1 - p) / n) ** 0.5
        table[name] = {
            "games": n,
            "wins": w,
            "win_rate_pct": round(100 * p, 2),
            "ci95_pct": round(196 * se, 2),
            "avg_penalty_points": round(pts[name] / n, 1),
        }
    return dict(sorted(table.items(), key=lambda kv: -kv[1]["win_rate_pct"]))


class TournamentRunner:
    """Backwards-compatible wrapper used by run_uno.py."""

    def __init__(self, strategy_classes: List[Type[BaseStrategy]], games_per_matchup: int = 1000,
                 allow_stacking: bool = False):
        self.names = [cls().name for cls in strategy_classes]
        self.allow_stacking = allow_stacking

    def run_4player_all_vs_all(self, total_games: int = 10000) -> Dict[str, Any]:
        t0 = time.time()
        res = run_games(random_lineups(self.names, total_games), stacking=self.allow_stacking)
        return {
            "total_games": total_games,
            "duration_seconds": round(time.time() - t0, 2),
            "avg_turns_per_game": round(sum(r["turns"] for r in res) / len(res), 2),
            "allow_stacking": self.allow_stacking,
            "leaderboard": list(summarize(res).items()),
        }
