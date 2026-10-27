from __future__ import annotations
import random

from simulation.core.models import CellCoord, GameConfig
from simulation.strategies.base import register_shooting
from simulation.strategies.shooting.hunt_target import HuntTargetShootingStrategy


@register_shooting("parity_hunt", description="Checkerboard parity grid hunting with smart axis-aligned targeting")
class ParityShootingStrategy(HuntTargetShootingStrategy):
    def next_shot(self) -> CellCoord:
        board_size = self.config.board_size

        # 1. Target mode: if we have active hits, target them
        if self.active_hits:
            candidates = self.get_candidate_targets()
            if candidates:
                return candidates[0]

        # 2. Parity hunt mode: cells where (row + col) % 2 == 0
        parity_cells = [
            CellCoord(r, c)
            for r in range(board_size)
            for c in range(board_size)
            if (r + c) % 2 == 0
            and CellCoord(r, c) not in self.shots_fired
            and CellCoord(r, c) not in self.excluded_cells
        ]
        if parity_cells:
            return self.rng.choice(parity_cells)

        # 3. Off-parity cells (for single-cell ships or remaining gaps)
        off_parity = [
            CellCoord(r, c)
            for r in range(board_size)
            for c in range(board_size)
            if CellCoord(r, c) not in self.shots_fired
            and CellCoord(r, c) not in self.excluded_cells
        ]
        if off_parity:
            return self.rng.choice(off_parity)

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
