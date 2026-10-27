from __future__ import annotations
import random
from typing import Optional

from simulation.core.models import CellCoord, GameConfig, ShotRecord, ShotResult
from simulation.strategies.base import register_shooting
from simulation.strategies.shooting.hunt_target import HuntTargetShootingStrategy


def get_quadrant(coord: CellCoord, board_size: int) -> int:
    half = board_size // 2
    r_top = coord.row < half
    c_left = coord.col < half
    if r_top and c_left:
        return 0  # Top-Left
    elif r_top and not c_left:
        return 1  # Top-Right
    elif not r_top and c_left:
        return 2  # Bottom-Left
    else:
        return 3  # Bottom-Right


@register_shooting(
    "anti_cluster",
    description="Sector probing hunter: detects ship clusters and aggressively saturates that quadrant before searching elsewhere",
)
class AntiClusterShootingStrategy(HuntTargetShootingStrategy):
    def initialize(self, config: GameConfig, rng: random.Random) -> None:
        super().initialize(config, rng)
        self.quadrant_hits: dict[int, int] = {0: 0, 1: 0, 2: 0, 3: 0}
        self.suspected_cluster_quad: Optional[int] = None

    def record_result(self, record: ShotRecord) -> None:
        super().record_result(record)
        if record.result in (ShotResult.HIT, ShotResult.SUNK):
            quad = get_quadrant(record.cell, self.config.board_size)
            self.quadrant_hits[quad] += 1
            # If a quadrant has 2+ hits, suspect cluster
            if self.quadrant_hits[quad] >= 2:
                self.suspected_cluster_quad = quad

    def next_shot(self) -> CellCoord:
        board_size = self.config.board_size

        # 1. Target mode: if we have active hits, finish them off immediately
        if self.active_hits:
            candidates = self.get_candidate_targets()
            if candidates:
                return candidates[0]

        # 2. Cluster saturation mode: if we suspect a cluster quadrant, search ALL unshot cells in it first!
        if self.suspected_cluster_quad is not None:
            quad_unshot = [
                CellCoord(r, c)
                for r in range(board_size)
                for c in range(board_size)
                if get_quadrant(CellCoord(r, c), board_size) == self.suspected_cluster_quad
                and CellCoord(r, c) not in self.shots_fired
                and CellCoord(r, c) not in self.excluded_cells
            ]
            if quad_unshot:
                # Prefer parity cells in cluster quad
                parity_quad = [c for c in quad_unshot if (c.row + c.col) % 2 == 0]
                if parity_quad:
                    return self.rng.choice(parity_quad)
                return self.rng.choice(quad_unshot)
            else:
                # Suspected quadrant fully exhausted! Clear suspicion
                self.suspected_cluster_quad = None

        # 3. Probe mode: pick unshot cells from the quadrant with the fewest shots to find ships fast
        quad_shot_counts = {0: 0, 1: 0, 2: 0, 3: 0}
        for s in self.shots_fired:
            quad_shot_counts[get_quadrant(s, board_size)] += 1

        # Sort quadrants by least explored
        sorted_quads = sorted([0, 1, 2, 3], key=lambda q: (quad_shot_counts[q], -self.quadrant_hits[q]))

        for quad in sorted_quads:
            quad_cells = [
                CellCoord(r, c)
                for r in range(board_size)
                for c in range(board_size)
                if get_quadrant(CellCoord(r, c), board_size) == quad
                and (r + c) % 2 == 0
                and CellCoord(r, c) not in self.shots_fired
                and CellCoord(r, c) not in self.excluded_cells
            ]
            if quad_cells:
                return self.rng.choice(quad_cells)

        # Fallback to superclass (any unshot)
        return super().next_shot()
