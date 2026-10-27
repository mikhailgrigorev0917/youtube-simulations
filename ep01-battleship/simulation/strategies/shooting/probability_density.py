from __future__ import annotations
import random
from typing import Optional

from simulation.core.engine import get_surrounding_cells, is_in_bounds
from simulation.core.models import CellCoord, GameConfig, ShotRecord, ShotResult
from simulation.strategies.base import register_shooting
from simulation.strategies.shooting.hunt_target import HuntTargetShootingStrategy


@register_shooting("probability_density", description="Dynamic heatmap/probability density Monte Carlo targeting")
class ProbabilityDensityShootingStrategy(HuntTargetShootingStrategy):
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

        # 1. If we have active hits, prioritize targeting them directly or weighting them heavily
        if self.active_hits:
            candidates = self.get_candidate_targets()
            if candidates:
                # Rank candidates by probability density
                heat = self._compute_heatmap(require_overlap_with_hits=True)
                candidates.sort(key=lambda c: heat[c.row][c.col], reverse=True)
                return candidates[0]

        # 2. Compute full probability density matrix for remaining ships
        heat = self._compute_heatmap(require_overlap_with_hits=False)

        # Find maximum value among unshot & unexcluded cells
        max_val = -1.0
        best_cells: list[CellCoord] = []

        for r in range(board_size):
            for c in range(board_size):
                coord = CellCoord(r, c)
                if coord in self.shots_fired or coord in self.excluded_cells:
                    continue
                score = heat[r][c]
                if score > max_val:
                    max_val = score
                    best_cells = [coord]
                elif score == max_val:
                    best_cells.append(coord)

        if best_cells and max_val > 0:
            return self.rng.choice(best_cells)

        # Fallback to superclass (e.g. random unshot)
        return super().next_shot()

    def _compute_heatmap(self, require_overlap_with_hits: bool) -> list[list[float]]:
        board_size = self.config.board_size
        heat = [[0.0 for _ in range(board_size)] for _ in range(board_size)]
        hits_set = set(self.active_hits)

        for size in self.remaining_ship_sizes:
            # Check horizontal placements
            for r in range(board_size):
                for c in range(board_size - size + 1):
                    cells = [CellCoord(r, c + i) for i in range(size)]
                    if self._is_legal_hypothetical(cells, hits_set, require_overlap_with_hits):
                        # Weight multiplier: if it covers active hits, boost score
                        weight = 100.0 if require_overlap_with_hits else 1.0
                        for cell in cells:
                            heat[cell.row][cell.col] += weight

            # Check vertical placements (if size > 1)
            if size > 1:
                for r in range(board_size - size + 1):
                    for c in range(board_size):
                        cells = [CellCoord(r + i, c) for i in range(size)]
                        if self._is_legal_hypothetical(cells, hits_set, require_overlap_with_hits):
                            weight = 100.0 if require_overlap_with_hits else 1.0
                            for cell in cells:
                                heat[cell.row][cell.col] += weight

        return heat

    def _is_legal_hypothetical(
        self,
        cells: list[CellCoord],
        hits_set: set[CellCoord],
        require_overlap_with_hits: bool,
    ) -> bool:
        overlaps = 0
        for cell in cells:
            if cell in self.excluded_cells:
                return False
            if cell in self.shots_fired:
                if cell in hits_set:
                    overlaps += 1
                else:
                    # Missed cell or sunk hit
                    return False
        if require_overlap_with_hits and overlaps == 0:
            return False
        return True
