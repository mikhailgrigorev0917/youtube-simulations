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


def edge_score(cells: list[CellCoord], board_size: int) -> float:
    """Calculates how close cells are to the outer boundary (higher = closer to edge)."""
    score = 0.0
    for c in cells:
        dist_to_edge = min(c.row, board_size - 1 - c.row, c.col, board_size - 1 - c.col)
        # 0 distance (on edge) gives highest weight
        score += max(0, 5 - dist_to_edge)
    return score


@register_placement("border", description="Biases ship placement along the outer edges and corners")
class BorderPlacementStrategy(BasePlacementStrategy):
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
                                score = edge_score(cells, board_size)
                                valid_candidates.append((score, cells))

                if not valid_candidates:
                    placed_all = False
                    break

                # Sort by edge score descending and sample from top tier
                valid_candidates.sort(key=lambda x: x[0], reverse=True)
                top_score = valid_candidates[0][0]
                # Filter candidates close to the maximum edge score
                top_candidates = [c for s, c in valid_candidates if s >= top_score - 1.5]

                chosen_cells = rng.choice(top_candidates)
                ships.append(Ship(id=ship_id, name=ship_name, size=size, cells=chosen_cells))

            if placed_all:
                valid, _ = is_valid_placement(ships, board_size, config.allow_touching, config.ship_sizes)
                if valid:
                    return ships

        raise RuntimeError("Failed to place border ships after 500 attempts")
