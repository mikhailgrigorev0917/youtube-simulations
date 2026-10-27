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


@register_placement(
    "anti_probability",
    description="Avoids the high-density center, placing ships in cold combinatorial zones to waste Bayesian shots",
)
class AntiProbabilityPlacementStrategy(BasePlacementStrategy):
    def place_ships(self, config: GameConfig, rng: random.Random) -> list[Ship]:
        board_size = config.board_size
        ship_sizes = sorted(config.ship_sizes, reverse=True)
        center = (board_size - 1) / 2.0

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
                                # Calculate penalty for being near the center
                                avg_center_dist = sum(
                                    abs(cell.row - center) + abs(cell.col - center)
                                    for cell in cells
                                ) / len(cells)

                                # Also slight penalty for being on exact outer border (to not look like border strat)
                                avg_edge_dist = min(
                                    min(cell.row, board_size - 1 - cell.row, cell.col, board_size - 1 - cell.col)
                                    for cell in cells
                                )
                                # Sweet spot: distance 1 or 2 from edges, far from center
                                score = avg_center_dist + (2.0 if avg_edge_dist in (1, 2) else 0.5)

                                valid_candidates.append((score, cells))

                if not valid_candidates:
                    placed_all = False
                    break

                valid_candidates.sort(key=lambda x: x[0], reverse=True)
                top_score = valid_candidates[0][0]
                top_candidates = [c for s, c in valid_candidates if s >= top_score - 1.0]

                chosen_cells = rng.choice(top_candidates)
                ships.append(Ship(id=ship_id, name=ship_name, size=size, cells=chosen_cells))

            if placed_all:
                valid, _ = is_valid_placement(ships, board_size, config.allow_touching, config.ship_sizes)
                if valid:
                    return ships

        raise RuntimeError("Failed to place anti-probability ships after 500 attempts")
