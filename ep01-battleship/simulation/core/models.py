from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import NamedTuple, Optional, Sequence


class CellCoord(NamedTuple):
    row: int
    col: int

    def __repr__(self) -> str:
        col_letter = chr(ord('A') + self.col)
        return f"{col_letter}{self.row + 1}"


class ShotResult(str, Enum):
    MISS = "miss"
    HIT = "hit"
    SUNK = "sunk"


@dataclass
class Ship:
    id: str
    name: str
    size: int
    cells: list[CellCoord]
    hits: set[CellCoord] = field(default_factory=set)

    @property
    def is_sunk(self) -> bool:
        return len(self.hits) >= len(self.cells) and len(self.cells) > 0


@dataclass(frozen=True)
class GameConfig:
    board_size: int = 10
    ship_sizes: tuple[int, ...] = (4, 3, 3, 2, 2, 2, 1, 1, 1, 1)
    allow_touching: bool = False  # False = no touching even at corners (1 cell gap halo)


@dataclass
class ShotRecord:
    turn: int
    cell: CellCoord
    result: ShotResult
    ship_id: Optional[str] = None
    sunk_ship: Optional[Ship] = None
    sunk_cells: Optional[list[CellCoord]] = None


@dataclass
class GameResult:
    turns: int
    shots: list[ShotRecord]
    ships: list[Ship]
    placement_strategy: str
    shooting_strategy: str
    board_size: int
    seed: Optional[int] = None
