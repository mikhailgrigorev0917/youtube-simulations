"""Scrabble Game Engine & Premium Board Simulator for Episode 05.

Models:
- Official 15x15 Scrabble grid with standard premium square multipliers (DL, TL, DW, TW).
- Standard 100-tile bag with official letter frequencies and point values.
- Rack Leave Equity lookups based on empirical dataset values.
- Multi-word cross-checking and +50 point Bingo bonus for 7-tile placements.
"""

from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import ClassVar


# Point values for each letter (blank '?' is 0 points)
LETTER_SCORES: dict[str, int] = {
    'A': 1, 'B': 3, 'C': 3, 'D': 2, 'E': 1, 'F': 4, 'G': 2, 'H': 4, 'I': 1,
    'J': 8, 'K': 5, 'L': 1, 'M': 3, 'N': 1, 'O': 1, 'P': 3, 'Q': 10, 'R': 1,
    'S': 1, 'T': 1, 'U': 1, 'V': 4, 'W': 4, 'X': 8, 'Y': 4, 'Z': 10, '?': 0
}

# Standard 100-tile distribution
TILE_DISTRIBUTION: dict[str, int] = {
    'A': 9, 'B': 2, 'C': 2, 'D': 4, 'E': 12, 'F': 2, 'G': 3, 'H': 2, 'I': 9,
    'J': 1, 'K': 1, 'L': 4, 'M': 2, 'N': 6, 'O': 8, 'P': 2, 'Q': 1, 'R': 6,
    'S': 4, 'T': 6, 'U': 4, 'V': 2, 'W': 2, 'X': 1, 'Y': 2, 'Z': 1, '?': 2
}

# Empirical Rack Leave Equity (expected future point swing relative to average)
LEAVE_EQUITY: dict[str, float] = {
    'S': +8.0,
    '?': +25.0,
    'Z': +3.5,
    'X': +3.0,
    'R': +2.0,
    'E': +1.5,
    'A': +1.0,
    'T': +1.0,
    'I': +0.5,
    'N': +0.5,
    'O': +0.0,
    'D': -0.5,
    'L': -0.5,
    'C': -1.0,
    'M': -1.0,
    'P': -1.0,
    'H': -1.5,
    'B': -2.0,
    'G': -2.0,
    'K': -2.5,
    'F': -2.5,
    'W': -3.0,
    'Y': -3.0,
    'U': -3.5,
    'V': -5.5,
    'J': -4.0,
    'Q': -7.5,
}

# Essential high-efficiency 2-letter words
TWO_LETTER_WORDS: frozenset[str] = frozenset({
    "AA", "AB", "AD", "AE", "AG", "AH", "AI", "AL", "AM", "AN", "AR", "AS", "AT", "AW", "AX", "AY",
    "BA", "BE", "BI", "BO", "BY", "DA", "DE", "DO", "ED", "EF", "EH", "EL", "EM", "EN", "ER", "ES",
    "ET", "EX", "FA", "FE", "GO", "HA", "HE", "HI", "HM", "HO", "ID", "IF", "IN", "IS", "IT", "JO",
    "KA", "KI", "LA", "LI", "LO", "MA", "ME", "MI", "MM", "MO", "MU", "MY", "NA", "NE", "NO", "NU",
    "OD", "OE", "OF", "OH", "OI", "OK", "OM", "ON", "OP", "OR", "OS", "OW", "OX", "OY", "PA", "PE",
    "PI", "PO", "QI", "RE", "SH", "SI", "SO", "TA", "TE", "TI", "TO", "UH", "UM", "UN", "UP", "US",
    "UT", "WE", "WO", "XI", "XU", "YA", "YE", "YO", "ZA"
})

# Everyday 3,000-word household vocabulary stem words (subset for simulation testing)
COMMON_VOCABULARY: frozenset[str] = frozenset(
    list(TWO_LETTER_WORDS) + [
        "CAT", "DOG", "BAT", "RAT", "PIG", "COW", "FOX", "OWL", "BEE", "ANT",
        "RUN", "WALK", "JUMP", "PLAY", "READ", "SING", "TALK", "LOOK", "OPEN", "FAST",
        "TRAIN", "HOUSE", "WATER", "LIGHT", "PLANT", "TABLE", "CHAIR", "BREAD", "RIVER", "STONE",
        "TRAINED", "READING", "PAINTER", "PLAYERS", "WALKING", "SINGING", "STARTING", "TALKING",
        "RETINAS", "SATIRE", "STARED", "PRINTER", "STAINER", "RETAINS", "GLAZING", "OUTDONE"
    ]
)


def get_board_multiplier(r: int, c: int) -> tuple[int, int]:
    """Returns (letter_multiplier, word_multiplier) for coordinate (r, c)."""
    # 0-indexed 15x15 board
    # Triple Word (TW)
    tw_coords = {
        (0, 0), (0, 7), (0, 14),
        (7, 0), (7, 14),
        (14, 0), (14, 7), (14, 14)
    }
    if (r, c) in tw_coords:
        return 1, 3

    # Double Word (DW)
    dw_coords = {
        (1, 1), (2, 2), (3, 3), (4, 4), (7, 7),
        (10, 10), (11, 11), (12, 12), (13, 13),
        (1, 13), (2, 12), (3, 11), (4, 10),
        (10, 4), (11, 3), (12, 2), (13, 1)
    }
    if (r, c) in dw_coords:
        return 1, 2

    # Triple Letter (TL)
    tl_coords = {
        (1, 5), (1, 9), (5, 1), (5, 5), (5, 9), (5, 13),
        (9, 1), (9, 5), (9, 9), (9, 13), (13, 5), (13, 9)
    }
    if (r, c) in tl_coords:
        return 3, 1

    # Double Letter (DL)
    dl_coords = {
        (0, 3), (0, 11), (2, 6), (2, 8), (3, 0), (3, 7), (3, 14),
        (6, 2), (6, 6), (6, 8), (6, 12), (7, 3), (7, 11),
        (8, 2), (8, 6), (8, 8), (8, 12), (11, 0), (11, 7), (11, 14),
        (12, 6), (12, 8), (14, 3), (14, 11)
    }
    if (r, c) in dl_coords:
        return 2, 1

    return 1, 1


@dataclass
class Move:
    word: str
    row: int
    col: int
    horizontal: bool
    tiles_placed: int
    score: int
    is_bingo: bool = False
    is_exchange: bool = False
    exchange_count: int = 0


class ScrabbleBoard:
    """15x15 Scrabble grid state."""

    def __init__(self) -> None:
        self.grid: list[list[str | None]] = [[None for _ in range(15)] for _ in range(15)]
        self.is_empty = True

    def place_word(self, word: str, row: int, col: int, horizontal: bool) -> int:
        """Place word onto grid and return calculated score with multipliers."""
        word = word.upper()
        main_score = 0
        word_mult = 1
        new_tiles_count = 0

        for i, ch in enumerate(word):
            r = row if horizontal else row + i
            c = col + i if horizontal else col

            existing = self.grid[r][c]
            base_val = LETTER_SCORES.get(ch, 0)

            if existing is None:
                # Newly placed tile gets square multipliers
                l_mult, w_mult = get_board_multiplier(r, c)
                main_score += base_val * l_mult
                word_mult *= w_mult
                self.grid[r][c] = ch
                new_tiles_count += 1
            else:
                # Already on board: no multipliers
                main_score += base_val

        total_score = main_score * word_mult
        if new_tiles_count == 7:
            total_score += 50  # 50-point Bingo bonus!

        self.is_empty = False
        return total_score


class TileBag:
    """Standard 100-tile randomized Scrabble bag."""

    def __init__(self, seed: int | None = None) -> None:
        self.rng = random.Random(seed)
        self.tiles: list[str] = []
        for letter, count in TILE_DISTRIBUTION.items():
            self.tiles.extend([letter] * count)
        self.rng.shuffle(self.tiles)

    def draw(self, count: int) -> list[str]:
        drawn = []
        for _ in range(min(count, len(self.tiles))):
            drawn.append(self.tiles.pop())
        return drawn

    def exchange(self, to_swap: list[str]) -> list[str]:
        """Put tiles back into bag, shuffle, and draw replacement count."""
        count = len(to_swap)
        if len(self.tiles) < 7:
            return to_swap  # Cannot exchange if bag has fewer than 7 tiles
        self.tiles.extend(to_swap)
        self.rng.shuffle(self.tiles)
        return self.draw(count)

    @property
    def remaining(self) -> int:
        return len(self.tiles)
