from __future__ import annotations
import random

from simulation.core.models import CellCoord, GameConfig
from simulation.strategies.base import register_shooting
from simulation.strategies.shooting.hunt_target import HuntTargetShootingStrategy


@register_shooting("anti_border", description="Counter-strategy: sweeps outer borders first to punish border-huggers")
class AntiBorderShootingStrategy(HuntTargetShootingStrategy):
    def next_shot(self) -> CellCoord:
        board_size = self.config.board_size

        # 1. Target mode: if we have active hits, target them
        if self.active_hits:
            candidates = self.get_candidate_targets()
            if candidates:
                return candidates[0]

        # 2. Border hunt mode: priority to boundary cells
        # Tier 1: exact border (depth 0)
        border_tier1 = [
            CellCoord(r, c)
            for r in range(board_size)
            for c in range(board_size)
            if (r == 0 or r == board_size - 1 or c == 0 or c == board_size - 1)
            and CellCoord(r, c) not in self.shots_fired
            and CellCoord(r, c) not in self.excluded_cells
        ]
        if border_tier1:
            # Alternating stride to cover border efficiently
            parity_border = [c for c in border_tier1 if (c.row + c.col) % 2 == 0]
            if parity_border:
                return self.rng.choice(parity_border)
            return self.rng.choice(border_tier1)

        # Tier 2: inner perimeter (depth 1)
        border_tier2 = [
            CellCoord(r, c)
            for r in range(board_size)
            for c in range(board_size)
            if (r == 1 or r == board_size - 2 or c == 1 or c == board_size - 2)
            and CellCoord(r, c) not in self.shots_fired
            and CellCoord(r, c) not in self.excluded_cells
        ]
        if border_tier2:
            return self.rng.choice(border_tier2)

        # Tier 3: remaining center cells
        remaining = [
            CellCoord(r, c)
            for r in range(board_size)
            for c in range(board_size)
            if CellCoord(r, c) not in self.shots_fired
            and CellCoord(r, c) not in self.excluded_cells
        ]
        if remaining:
            return self.rng.choice(remaining)

        # Fallback
        fallback = [
            CellCoord(r, c)
            for r in range(board_size)
            for c in range(board_size)
            if CellCoord(r, c) not in self.shots_fired
        ]
        if fallback:
            return self.rng.choice(fallback)

        raise RuntimeError("No remaining shots available!")
