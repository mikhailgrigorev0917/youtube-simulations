"""Core 2048 simulation board logic with LUT-accelerated slide mechanics."""

from __future__ import annotations
import random
from typing import Tuple, List, Optional, Dict
from enum import IntEnum

# Board is a 16-tuple of exponents:
# 0 -> empty (0)
# 1 -> 2 (2^1)
# 2 -> 4 (2^2)
# ...
# 11 -> 2048 (2^11)
# 16 -> 65536 (2^16)

BoardType = Tuple[int, ...]  # 16 integers 0..16

class Move(IntEnum):
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3

# Precomputed Lookup Tables for row sliding
# Row is a 4-tuple of exponents (c0, c1, c2, c3)
# ROW_SLIDE_LEFT[row] = (new_row, score_gained, changed)
ROW_SLIDE_LEFT: Dict[Tuple[int, int, int, int], Tuple[Tuple[int, int, int, int], int, bool]] = {}

def _compute_row_slide_left(row: Tuple[int, int, int, int]) -> Tuple[Tuple[int, int, int, int], int, bool]:
    # Extract non-zero tiles
    tiles = [x for x in row if x != 0]
    result: List[int] = []
    score = 0
    skip = False
    
    for i in range(len(tiles)):
        if skip:
            skip = False
            continue
        if i + 1 < len(tiles) and tiles[i] == tiles[i + 1]:
            # Merge
            new_power = tiles[i] + 1
            result.append(new_power)
            score += (1 << new_power)
            skip = True
        else:
            result.append(tiles[i])
            
    while len(result) < 4:
        result.append(0)
        
    res_tuple = (result[0], result[1], result[2], result[3])
    changed = (res_tuple != row)
    return res_tuple, score, changed

# Pre-populate LUT for all 17^4 possible rows (17 states: 0..16)
# 17^4 = 83,521 entries
def _init_lut() -> None:
    for c0 in range(17):
        for c1 in range(17):
            for c2 in range(17):
                for c3 in range(17):
                    row = (c0, c1, c2, c3)
                    ROW_SLIDE_LEFT[row] = _compute_row_slide_left(row)

_init_lut()

# Helper transformations for 4x4 boards
def empty_board() -> BoardType:
    return (0,) * 16

def tile_value(exp: int) -> int:
    return 1 << exp if exp > 0 else 0

def board_values(board: BoardType) -> List[int]:
    return [tile_value(x) for x in board]

def max_power(board: BoardType) -> int:
    return max(board)

def max_tile_value(board: BoardType) -> int:
    m = max(board)
    return 1 << m if m > 0 else 0

def get_empty_indices(board: BoardType) -> List[int]:
    return [i for i, x in enumerate(board) if x == 0]

def count_empty_cells(board: BoardType) -> int:
    return board.count(0)

def spawn_random_tile(board: BoardType, rng: random.Random, p4: float = 0.1) -> Tuple[BoardType, int, int]:
    """Spawns a 2 (exp 1, 90%) or 4 (exp 2, 10%) into a random empty cell.
    Returns (new_board, index, spawned_exp).
    """
    empty = get_empty_indices(board)
    if not empty:
        return board, -1, 0
    idx = rng.choice(empty)
    val_exp = 2 if rng.random() < p4 else 1
    
    new_board = list(board)
    new_board[idx] = val_exp
    return tuple(new_board), idx, val_exp

def set_tile(board: BoardType, idx: int, exp: int) -> BoardType:
    b = list(board)
    b[idx] = exp
    return tuple(b)

def make_move(board: BoardType, move: Move) -> Tuple[BoardType, int, bool]:
    """Applies a move to the board.
    Returns (new_board, score_gained, changed).
    """
    score = 0
    changed = False
    
    if move == Move.LEFT:
        r0, s0, c0 = ROW_SLIDE_LEFT[(board[0], board[1], board[2], board[3])]
        r1, s1, c1 = ROW_SLIDE_LEFT[(board[4], board[5], board[6], board[7])]
        r2, s2, c2 = ROW_SLIDE_LEFT[(board[8], board[9], board[10], board[11])]
        r3, s3, c3 = ROW_SLIDE_LEFT[(board[12], board[13], board[14], board[15])]
        new_b = (
            r0[0], r0[1], r0[2], r0[3],
            r1[0], r1[1], r1[2], r1[3],
            r2[0], r2[1], r2[2], r2[3],
            r3[0], r3[1], r3[2], r3[3],
        )
        score = s0 + s1 + s2 + s3
        changed = c0 or c1 or c2 or c3
        return new_b, score, changed

    elif move == Move.RIGHT:
        # Reverse rows, slide left, reverse back
        r0, s0, c0 = ROW_SLIDE_LEFT[(board[3], board[2], board[1], board[0])]
        r1, s1, c1 = ROW_SLIDE_LEFT[(board[7], board[6], board[5], board[4])]
        r2, s2, c2 = ROW_SLIDE_LEFT[(board[11], board[10], board[9], board[8])]
        r3, s3, c3 = ROW_SLIDE_LEFT[(board[15], board[14], board[13], board[12])]
        new_b = (
            r0[3], r0[2], r0[1], r0[0],
            r1[3], r1[2], r1[1], r1[0],
            r2[3], r2[2], r2[1], r2[0],
            r3[3], r3[2], r3[1], r3[0],
        )
        score = s0 + s1 + s2 + s3
        changed = c0 or c1 or c2 or c3
        return new_b, score, changed

    elif move == Move.UP:
        # Columns become rows
        c0_tuple, s0, ch0 = ROW_SLIDE_LEFT[(board[0], board[4], board[8], board[12])]
        c1_tuple, s1, ch1 = ROW_SLIDE_LEFT[(board[1], board[5], board[9], board[13])]
        c2_tuple, s2, ch2 = ROW_SLIDE_LEFT[(board[2], board[6], board[10], board[14])]
        c3_tuple, s3, ch3 = ROW_SLIDE_LEFT[(board[3], board[7], board[11], board[15])]
        new_b = (
            c0_tuple[0], c1_tuple[0], c2_tuple[0], c3_tuple[0],
            c0_tuple[1], c1_tuple[1], c2_tuple[1], c3_tuple[1],
            c0_tuple[2], c1_tuple[2], c2_tuple[2], c3_tuple[2],
            c0_tuple[3], c1_tuple[3], c2_tuple[3], c3_tuple[3],
        )
        score = s0 + s1 + s2 + s3
        changed = ch0 or ch1 or ch2 or ch3
        return new_b, score, changed

    elif move == Move.DOWN:
        # Columns reversed become rows
        c0_tuple, s0, ch0 = ROW_SLIDE_LEFT[(board[12], board[8], board[4], board[0])]
        c1_tuple, s1, ch1 = ROW_SLIDE_LEFT[(board[13], board[9], board[5], board[1])]
        c2_tuple, s2, ch2 = ROW_SLIDE_LEFT[(board[14], board[10], board[6], board[2])]
        c3_tuple, s3, ch3 = ROW_SLIDE_LEFT[(board[15], board[11], board[7], board[3])]
        new_b = (
            c0_tuple[3], c1_tuple[3], c2_tuple[3], c3_tuple[3],
            c0_tuple[2], c1_tuple[2], c2_tuple[2], c3_tuple[2],
            c0_tuple[1], c1_tuple[1], c2_tuple[1], c3_tuple[1],
            c0_tuple[0], c1_tuple[0], c2_tuple[0], c3_tuple[0],
        )
        score = s0 + s1 + s2 + s3
        changed = ch0 or ch1 or ch2 or ch3
        return new_b, score, changed

    return board, 0, False

def get_legal_moves(board: BoardType) -> List[Move]:
    moves = []
    for m in (Move.UP, Move.RIGHT, Move.DOWN, Move.LEFT):
        _, _, changed = make_move(board, m)
        if changed:
            moves.append(m)
    return moves

def is_game_over(board: BoardType) -> bool:
    if 0 in board:
        return False
    # Check horizontal adjacent matches
    for r in range(4):
        offset = r * 4
        if board[offset] == board[offset + 1] or \
           board[offset + 1] == board[offset + 2] or \
           board[offset + 2] == board[offset + 3]:
            return False
    # Check vertical adjacent matches
    for c in range(4):
        if board[c] == board[c + 4] or \
           board[c + 4] == board[c + 8] or \
           board[c + 8] == board[c + 12]:
            return False
    return True
