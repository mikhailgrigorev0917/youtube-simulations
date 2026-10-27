from __future__ import annotations
import random

from simulation.core.engine import is_valid_placement
from simulation.core.models import CellCoord, GameConfig, Ship
from simulation.strategies.base import BasePlacementStrategy, register_placement
from simulation.strategies.placement.random_placement import (
    SHIP_NAMES,
    can_place_single_ship,
    generate_ship_cells,
)


def min_distance_to_placed(candidate: list[CellCoord], placed_ships: list[Ship]) -> float:
    if not placed_ships:
        return 10.0
    min_dist = float("inf")
    for s in placed_ships:
        for c1 in candidate:
            for c2 in s.cells:
                # Chebyshev or Manhattan distance
                d = max(abs(c1.row - c2.row), abs(c1.col - c2.col))
                if d < min_dist:
                    min_dist = d
    return float(min_dist)


@register_placement("uniform", description="Maximizes spacing and uniform distribution across the board")
class UniformPlacementStrategy(BasePlacementStrategy):
    def place_ships(self, config: GameConfig, rng: random.Random) -> list[Ship]:
        board_size = config.board_size
        ship_sizes = sorted(config.ship_sizes, reverse=True)

        for attempt in range(500):
            ships: list[Ship] = []
            placed_all = True
            ship_counters: dict[int, int] = {}

            for size in ship_sizes:
                idx = ship_counters.get(size, 1)
                ship_counters[size] = idx + 1
                ship_name = f"{SHIP_NAMES.get(size, 'Ship')}-{idx}"
                ship_id = f"{ship_name.lower()}"

                valid_candidates: list[tuple[float, list[CellCoord]]] = []
                for is_horiz in (True, False):
                    max_r = board_size if is_horiz else board_size - size + 1
                    max_c = board_size - size + 1 if is_horiz else board_size
                    for r in range(max_r):
                        for c in range(max_c):
                            cells = generate_ship_cells(r, c, size, is_horiz)
                            if can_place_single_ship(cells, ships, board_size, config.allow_touching):
                                dist = min_distance_to_placed(cells, ships)
                                valid_candidates.append((dist, cells))

                if not valid_candidates:
                    placed_all = False
                    break

                # Sort by distance descending
                valid_candidates.sort(key=lambda x: x[0], reverse=True)
                top_dist = valid_candidates[0][0]
                top_candidates = [c for d, c in valid_candidates if d >= top_dist - 0.5]

                chosen_cells = rng.choice(top_candidates)
                ships.append(Ship(id=ship_id, name=ship_name, size=size, cells=chosen_cells))

            if placed_all:
                valid, _ = is_valid_placement(ships, board_size, config.allow_touching, config.ship_sizes)
                if valid:
                    return ships

        raise RuntimeError("Failed to place uniformly spaced ships after 500 attempts")
