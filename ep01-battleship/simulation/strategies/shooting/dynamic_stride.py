from __future__ import annotations
import random
from typing import Optional

from simulation.core.models import CellCoord, GameConfig, ShotRecord, ShotResult
from simulation.strategies.base import register_shooting
from simulation.strategies.shooting.hunt_target import HuntTargetShootingStrategy


@register_shooting(
    "dynamic_stride",
    description="Multi-phase stride parity: searches stride 4 for battleship, 3 for cruisers, 2 for destroyers",
)
class DynamicStrideShootingStrategy(HuntTargetShootingStrategy):
    def initialize(self, config: GameConfig, rng: random.Random) -> None:
        super().initialize(config, rng)
        self.remaining_ship_sizes: list[int] = sorted(list(config.ship_sizes), reverse=True)

    def record_result(self, record: ShotRecord) -> None:
        super().record_result(record)
        if record.result == ShotResult.SUNK:
            sunk_len = len(record.sunk_cells or [record.cell])
            if sunk_len in self.remaining_ship_sizes:
                self.remaining_ship_sizes.remove(sunk_len)

    def next_shot(self) -> CellCoord:
        board_size = self.config.board_size

        # 1. Target mode: if we have active hits, target them
        if self.active_hits:
            candidates = self.get_candidate_targets()
            if candidates:
                return candidates[0]

        # 2. Determine current optimal stride based on largest remaining multi-cell ship
        max_remaining = max(self.remaining_ship_sizes) if self.remaining_ship_sizes else 1

        stride = min(max_remaining, 4)

        if stride >= 2:
            # Look for unshot cells matching stride pattern
            for offset in range(stride):
                matching = [
                    CellCoord(r, c)
                    for r in range(board_size)
                    for c in range(board_size)
                    if (r + c) % stride == offset
                    and CellCoord(r, c) not in self.shots_fired
                    and CellCoord(r, c) not in self.excluded_cells
                ]
                if matching:
                    return self.rng.choice(matching)

        # 3. Fallback for single-cell ships or remaining gaps
        remaining = [
            CellCoord(r, c)
            for r in range(board_size)
            for c in range(board_size)
            if CellCoord(r, c) not in self.shots_fired
            and CellCoord(r, c) not in self.excluded_cells
        ]
        if remaining:
            return self.rng.choice(remaining)

        # Fallback to any unshot
        fallback = [
            CellCoord(r, c)
            for r in range(board_size)
            for c in range(board_size)
            if CellCoord(r, c) not in self.shots_fired
        ]
        if fallback:
            return self.rng.choice(fallback)

        raise RuntimeError("No remaining shots available!")
