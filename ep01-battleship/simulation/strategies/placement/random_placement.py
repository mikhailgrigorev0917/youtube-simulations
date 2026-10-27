from __future__ import annotations
import random
from typing import Optional

from simulation.core.engine import get_surrounding_cells, is_in_bounds, is_valid_placement
from simulation.core.models import CellCoord, GameConfig, Ship
from simulation.strategies.base import BasePlacementStrategy, register_placement


SHIP_NAMES = {
    4: "Battleship",
    3: "Cruiser",
    2: "Destroyer",
    1: "Submarine",
}


def generate_ship_cells(
    start_row: int,
    start_col: int,
    size: int,
    is_horizontal: bool,
) -> list[CellCoord]:
    if is_horizontal:
        return [CellCoord(start_row, start_col + i) for i in range(size)]
    else:
        return [CellCoord(start_row + i, start_col) for i in range(size)]


def can_place_single_ship(
    candidate_cells: list[CellCoord],
    existing_ships: list[Ship],
    board_size: int,
    allow_touching: bool,
) -> bool:
    for c in candidate_cells:
        if not is_in_bounds(c, board_size):
            return False

    occupied = {c for s in existing_ships for c in s.cells}
    for c in candidate_cells:
        if c in occupied:
            return False

    if not allow_touching:
        halos = {
            h
            for s in existing_ships
            for h in get_surrounding_cells(s.cells, board_size, include_self=False)
        }
        for c in candidate_cells:
            if c in halos:
                return False

    return True


@register_placement("random", description="Pure random valid placement across entire board")
class RandomPlacementStrategy(BasePlacementStrategy):
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

                # Generate all valid positions for this size
                valid_candidates: list[list[CellCoord]] = []
                for is_horiz in (True, False):
                    max_r = board_size if is_horiz else board_size - size + 1
                    max_c = board_size - size + 1 if is_horiz else board_size
                    for r in range(max_r):
                        for c in range(max_c):
                            cells = generate_ship_cells(r, c, size, is_horiz)
                            if can_place_single_ship(cells, ships, board_size, config.allow_touching):
                                valid_candidates.append(cells)

                if not valid_candidates:
                    placed_all = False
                    break

                chosen_cells = rng.choice(valid_candidates)
                ships.append(Ship(id=ship_id, name=ship_name, size=size, cells=chosen_cells))

            if placed_all:
                valid, _ = is_valid_placement(ships, board_size, config.allow_touching, config.ship_sizes)
                if valid:
                    return ships

        raise RuntimeError("Failed to place ships randomly after 500 attempts")
