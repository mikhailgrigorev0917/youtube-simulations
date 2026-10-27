from __future__ import annotations
from typing import Optional, Sequence
import random

from simulation.core.models import (
    CellCoord,
    GameConfig,
    GameResult,
    Ship,
    ShotRecord,
    ShotResult,
)


def is_in_bounds(coord: CellCoord, board_size: int) -> bool:
    return 0 <= coord.row < board_size and 0 <= coord.col < board_size


def get_surrounding_cells(
    cells: Sequence[CellCoord],
    board_size: int,
    include_self: bool = False,
) -> set[CellCoord]:
    """Returns all 8-neighbor cells surrounding the given sequence of cells."""
    result: set[CellCoord] = set()
    self_set = set(cells)
    for c in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = c.row + dr, c.col + dc
                neighbor = CellCoord(nr, nc)
                if is_in_bounds(neighbor, board_size):
                    if neighbor not in self_set:
                        result.add(neighbor)
    if include_self:
        result.update(self_set)
    return result


def is_valid_placement(
    ships: Sequence[Ship],
    board_size: int,
    allow_touching: bool,
    expected_sizes: Optional[Sequence[int]] = None,
) -> tuple[bool, str]:
    """Validates the full set of ships on the board."""
    if expected_sizes is not None:
        actual_sizes = sorted([s.size for s in ships], reverse=True)
        exp_sorted = sorted(list(expected_sizes), reverse=True)
        if actual_sizes != exp_sorted:
            return False, f"Ship sizes mismatch: got {actual_sizes}, expected {exp_sorted}"

    occupied: set[CellCoord] = set()
    halos: set[CellCoord] = set()

    for ship in ships:
        if len(ship.cells) != ship.size:
            return False, f"Ship {ship.id} size mismatch: has {len(ship.cells)} cells, declared size {ship.size}"

        # Check straight line (horizontal or vertical) and contiguous
        rows = [c.row for c in ship.cells]
        cols = [c.col for c in ship.cells]
        for c in ship.cells:
            if not is_in_bounds(c, board_size):
                return False, f"Ship {ship.id} cell {c} out of bounds"

        if len(ship.cells) > 1:
            is_horiz = len(set(rows)) == 1 and sorted(cols) == list(range(min(cols), max(cols) + 1))
            is_vert = len(set(cols)) == 1 and sorted(rows) == list(range(min(rows), max(rows) + 1))
            if not (is_horiz or is_vert):
                return False, f"Ship {ship.id} cells are not contiguous and straight: {ship.cells}"

        # Check overlap
        for c in ship.cells:
            if c in occupied:
                return False, f"Cell {c} is occupied by multiple ships"

        if not allow_touching:
            for c in ship.cells:
                if c in halos:
                    return False, f"Ship {ship.id} touches another ship's halo at {c}"
            ship_halo = get_surrounding_cells(ship.cells, board_size, include_self=False)
            halos.update(ship_halo)

        occupied.update(ship.cells)

    return True, "Valid"


class BattleshipBoard:
    def __init__(self, ships: list[Ship], board_size: int):
        self.board_size = board_size
        self.ships = ships
        self.cell_to_ship: dict[CellCoord, Ship] = {}
        for ship in ships:
            for c in ship.cells:
                self.cell_to_ship[c] = ship
        self.shots_fired: set[CellCoord] = set()
        self.shot_records: list[ShotRecord] = []

    @property
    def is_all_sunk(self) -> bool:
        return all(s.is_sunk for s in self.ships)

    def fire(self, coord: CellCoord) -> ShotRecord:
        if not is_in_bounds(coord, self.board_size):
            raise ValueError(f"Shot {coord} is out of bounds (board size {self.board_size})")
        if coord in self.shots_fired:
            raise ValueError(f"Shot {coord} was already fired previously!")

        self.shots_fired.add(coord)
        turn = len(self.shots_fired)

        ship = self.cell_to_ship.get(coord)
        if ship is None:
            record = ShotRecord(turn=turn, cell=coord, result=ShotResult.MISS)
        else:
            ship.hits.add(coord)
            if ship.is_sunk:
                record = ShotRecord(
                    turn=turn,
                    cell=coord,
                    result=ShotResult.SUNK,
                    ship_id=ship.id,
                    sunk_ship=ship,
                    sunk_cells=list(ship.cells),
                )
            else:
                record = ShotRecord(
                    turn=turn,
                    cell=coord,
                    result=ShotResult.HIT,
                    ship_id=ship.id,
                )

        self.shot_records.append(record)
        return record


class BattleshipEngine:
    """Manages the full game lifecycle between a placement and a shooting strategy."""

    def __init__(self, config: Optional[GameConfig] = None):
        self.config = config or GameConfig()

    def play(
        self,
        placement_strategy,
        shooting_strategy,
        seed: Optional[int] = None,
    ) -> GameResult:
        rng = random.Random(seed)

        # 1. Place ships
        ships = placement_strategy.place_ships(self.config, rng)
        is_valid, msg = is_valid_placement(
            ships,
            self.config.board_size,
            self.config.allow_touching,
            self.config.ship_sizes,
        )
        if not is_valid:
            raise RuntimeError(f"Invalid placement by {placement_strategy.name}: {msg}")

        # 2. Setup board and shooter
        board = BattleshipBoard(ships, self.config.board_size)
        shooting_strategy.initialize(self.config, rng)

        # 3. Game loop
        max_turns = self.config.board_size * self.config.board_size
        while not board.is_all_sunk and len(board.shots_fired) < max_turns:
            coord = shooting_strategy.next_shot()
            record = board.fire(coord)
            shooting_strategy.record_result(record)

        return GameResult(
            turns=len(board.shots_fired),
            shots=board.shot_records,
            ships=ships,
            placement_strategy=placement_strategy.name,
            shooting_strategy=shooting_strategy.name,
            board_size=self.config.board_size,
            seed=seed,
        )
