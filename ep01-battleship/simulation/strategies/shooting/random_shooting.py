from __future__ import annotations
import random
from typing import Optional

from simulation.core.models import CellCoord, GameConfig, ShotRecord
from simulation.strategies.base import BaseShootingStrategy, register_shooting


@register_shooting("random", description="Random firing without repeats")
class RandomShootingStrategy(BaseShootingStrategy):
    def initialize(self, config: GameConfig, rng: random.Random) -> None:
        super().initialize(config, rng)
        # Pre-shuffle all available cells
        self.available_cells: list[CellCoord] = [
            CellCoord(r, c)
            for r in range(config.board_size)
            for c in range(config.board_size)
        ]
        self.rng.shuffle(self.available_cells)

    def next_shot(self) -> CellCoord:
        while self.available_cells:
            cell = self.available_cells.pop()
            if cell not in self.shots_fired:
                return cell
        raise RuntimeError("No available cells left to shoot!")

    def record_result(self, record: ShotRecord) -> None:
        self.shots_fired.add(record.cell)
