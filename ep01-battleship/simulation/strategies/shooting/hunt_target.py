from __future__ import annotations
from collections import deque
import random
from typing import Optional

from simulation.core.engine import get_surrounding_cells, is_in_bounds
from simulation.core.models import CellCoord, GameConfig, ShotRecord, ShotResult
from simulation.strategies.base import BaseShootingStrategy, register_shooting


@register_shooting("hunt_target", description="Random hunt until hit, then targets along ship axis and eliminates halos")
class HuntTargetShootingStrategy(BaseShootingStrategy):
    def initialize(self, config: GameConfig, rng: random.Random) -> None:
        super().initialize(config, rng)
        self.excluded_cells: set[CellCoord] = set()
        self.active_hits: list[CellCoord] = []
        self.target_queue: deque[CellCoord] = deque()

    def get_candidate_targets(self) -> list[CellCoord]:
        """Calculates smart targets adjacent to active hits."""
        if not self.active_hits:
            return []

        board_size = self.config.board_size

        if len(self.active_hits) == 1:
            hit = self.active_hits[0]
            candidates = []
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                n = CellCoord(hit.row + dr, hit.col + dc)
                if is_in_bounds(n, board_size) and n not in self.shots_fired and n not in self.excluded_cells:
                    candidates.append(n)
            return candidates

        # 2 or more hits: determine orientation
        rows = {h.row for h in self.active_hits}
        cols = {h.col for h in self.active_hits}

        candidates = []
        if len(rows) == 1:
            # Horizontal ship
            r = self.active_hits[0].row
            min_c = min(h.col for h in self.active_hits)
            max_c = max(h.col for h in self.active_hits)
            left = CellCoord(r, min_c - 1)
            right = CellCoord(r, max_c + 1)
            for c in (left, right):
                if is_in_bounds(c, board_size) and c not in self.shots_fired and c not in self.excluded_cells:
                    candidates.append(c)
        elif len(cols) == 1:
            # Vertical ship
            c = self.active_hits[0].col
            min_r = min(h.row for h in self.active_hits)
            max_r = max(h.row for h in self.active_hits)
            up = CellCoord(min_r - 1, c)
            down = CellCoord(max_r + 1, c)
            for coord in (up, down):
                if is_in_bounds(coord, board_size) and coord not in self.shots_fired and coord not in self.excluded_cells:
                    candidates.append(coord)
        else:
            # Fallback if overlapping hits occurred
            for h in self.active_hits:
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    n = CellCoord(h.row + dr, h.col + dc)
                    if is_in_bounds(n, board_size) and n not in self.shots_fired and n not in self.excluded_cells:
                        candidates.append(n)

        return candidates

    def next_shot(self) -> CellCoord:
        board_size = self.config.board_size

        # 1. Target mode: if we have active hits, target them
        if self.active_hits:
            candidates = self.get_candidate_targets()
            if candidates:
                return candidates[0]

        # 2. Hunt mode: pick random unshot and unexcluded cell
        unshot = [
            CellCoord(r, c)
            for r in range(board_size)
            for c in range(board_size)
            if CellCoord(r, c) not in self.shots_fired and CellCoord(r, c) not in self.excluded_cells
        ]
        if unshot:
            return self.rng.choice(unshot)

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

    def record_result(self, record: ShotRecord) -> None:
        self.shots_fired.add(record.cell)

        if record.result == ShotResult.HIT:
            self.hits.add(record.cell)
            self.active_hits.append(record.cell)

        elif record.result == ShotResult.SUNK:
            self.hits.add(record.cell)
            self.active_hits.append(record.cell)

            sunk_cells = set(record.sunk_cells or [record.cell])

            # Exclude halo cells around the sunk ship
            if not self.config.allow_touching:
                halo = get_surrounding_cells(list(sunk_cells), self.config.board_size, include_self=False)
                self.excluded_cells.update(halo)

            # Remove sunk ship's cells from active hits
            self.active_hits = [h for h in self.active_hits if h not in sunk_cells]
