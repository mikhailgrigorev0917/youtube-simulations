from __future__ import annotations
from concurrent.futures import ProcessPoolExecutor, as_completed
import os
from pathlib import Path
from typing import Optional, Sequence

from simulation.core.engine import BattleshipEngine
from simulation.core.exporter import export_replay_to_json
from simulation.core.models import GameConfig, GameResult
from simulation.runner.stats import MatchupStats
from simulation.strategies.base import (
    get_placement_strategies,
    get_placement_strategy,
    get_shooting_strategies,
    get_shooting_strategy,
)
# Ensure strategies are registered
import simulation.strategies.placement  # noqa: F401
import simulation.strategies.shooting  # noqa: F401


def _run_single_game(
    placement_name: str,
    shooting_name: str,
    config: GameConfig,
    seed: int,
    record_full_replay: bool,
) -> tuple[int, Optional[GameResult]]:
    placement = get_placement_strategy(placement_name)
    shooter = get_shooting_strategy(shooting_name)
    engine = BattleshipEngine(config)
    result = engine.play(placement, shooter, seed=seed)
    return result.turns, (result if record_full_replay else None)


def _batch_worker(
    placement_name: str,
    shooting_name: str,
    config: GameConfig,
    seeds: list[int],
    record_first_replay: bool,
) -> tuple[list[int], Optional[GameResult]]:
    turns_list: list[int] = []
    sample_game: Optional[GameResult] = None

    for i, seed in enumerate(seeds):
        want_replay = record_first_replay and (i == 0)
        turns, game_res = _run_single_game(
            placement_name,
            shooting_name,
            config,
            seed,
            want_replay,
        )
        turns_list.append(turns)
        if want_replay:
            sample_game = game_res

    return turns_list, sample_game


class TournamentRunner:
    def __init__(
        self,
        config: Optional[GameConfig] = None,
        max_workers: Optional[int] = None,
    ):
        self.config = config or GameConfig()
        self.max_workers = max_workers or max(1, (os.cpu_count() or 4) - 1)

    def run_matchup(
        self,
        placement_name: str,
        shooting_name: str,
        num_games: int = 1000,
        base_seed: int = 10000,
    ) -> MatchupStats:
        all_turns: list[int] = []
        sample_game: Optional[GameResult] = None

        chunk_size = max(50, num_games // self.max_workers)
        chunks = []
        cur_idx = 0
        while cur_idx < num_games:
            count = min(chunk_size, num_games - cur_idx)
            seeds = [base_seed + cur_idx + j for j in range(count)]
            record_first = (cur_idx == 0)
            chunks.append((seeds, record_first))
            cur_idx += count

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(
                    _batch_worker,
                    placement_name,
                    shooting_name,
                    self.config,
                    seeds,
                    rec,
                )
                for seeds, rec in chunks
            ]
            for future in as_completed(futures):
                turns, sample = future.result()
                all_turns.extend(turns)
                if sample is not None and sample_game is None:
                    sample_game = sample

        # Create dummy GameResults wrapper for stats calculation
        dummy_results = [
            GameResult(
                turns=t,
                shots=[],
                ships=[],
                placement_strategy=placement_name,
                shooting_strategy=shooting_name,
                board_size=self.config.board_size,
            )
            for t in all_turns
        ]

        return MatchupStats.from_results(
            placement=placement_name,
            shooting=shooting_name,
            results=dummy_results,
            sample_game=sample_game,
        )

    def run_tournament(
        self,
        placement_names: Optional[Sequence[str]] = None,
        shooting_names: Optional[Sequence[str]] = None,
        num_games_per_matchup: int = 1000,
        save_replays: bool = True,
        replays_dir: Optional[Path | str] = None,
    ) -> list[MatchupStats]:
        all_p = list(get_placement_strategies().keys()) if placement_names is None else list(placement_names)
        all_s = list(get_shooting_strategies().keys()) if shooting_names is None else list(shooting_names)

        results: list[MatchupStats] = []
        replays_path = Path(replays_dir or "data/battleship/replays")

        seed_counter = 42
        for p in all_p:
            for s in all_s:
                stats = self.run_matchup(p, s, num_games=num_games_per_matchup, base_seed=seed_counter)
                seed_counter += num_games_per_matchup + 100
                results.append(stats)

                if save_replays and stats.sample_game is not None:
                    filename = f"replay_{p}_vs_{s}.json"
                    export_replay_to_json(
                        stats.sample_game,
                        replays_path / filename,
                        scene_id=f"replay-{p}-{s}",
                    )

        return results
