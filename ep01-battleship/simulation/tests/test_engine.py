from __future__ import annotations
import pytest

from simulation.core.engine import (
    BattleshipBoard,
    get_surrounding_cells,
    is_in_bounds,
    is_valid_placement,
)
from simulation.core.models import CellCoord, Ship, ShotResult


def test_is_in_bounds():
    assert is_in_bounds(CellCoord(0, 0), 10)
    assert is_in_bounds(CellCoord(9, 9), 10)
    assert not is_in_bounds(CellCoord(10, 0), 10)
    assert not is_in_bounds(CellCoord(-1, 5), 10)


def test_get_surrounding_cells():
    cells = [CellCoord(1, 1)]
    neighbors = get_surrounding_cells(cells, 10, include_self=False)
    assert len(neighbors) == 8
    assert CellCoord(0, 0) in neighbors
    assert CellCoord(2, 2) in neighbors
    assert CellCoord(1, 1) not in neighbors


def test_valid_placement_touching_rule():
    # Two adjacent ships
    ship1 = Ship("s1", "S1", 1, [CellCoord(0, 0)])
    ship2 = Ship("s2", "S2", 1, [CellCoord(1, 1)])  # Diagonal touch!

    # When touching is NOT allowed, should fail
    valid, msg = is_valid_placement([ship1, ship2], 10, allow_touching=False)
    assert not valid
    assert "halo" in msg

    # When touching IS allowed, should pass
    valid, msg = is_valid_placement([ship1, ship2], 10, allow_touching=True)
    assert valid


def test_board_shooting():
    ship = Ship("carrier", "Carrier", 2, [CellCoord(0, 0), CellCoord(0, 1)])
    board = BattleshipBoard([ship], 10)

    # Miss
    r1 = board.fire(CellCoord(5, 5))
    assert r1.result == ShotResult.MISS
    assert not board.is_all_sunk

    # Hit
    r2 = board.fire(CellCoord(0, 0))
    assert r2.result == ShotResult.HIT
    assert not board.is_all_sunk

    # Repeat shot should raise ValueError
    with pytest.raises(ValueError):
        board.fire(CellCoord(0, 0))

    # Sunk
    r3 = board.fire(CellCoord(0, 1))
    assert r3.result == ShotResult.SUNK
    assert board.is_all_sunk
