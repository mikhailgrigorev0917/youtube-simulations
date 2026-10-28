"""Unit tests for 2048 board simulation logic."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from board import (
    Move, make_move, is_game_over, empty_board, tile_value, ROW_SLIDE_LEFT
)

def test_single_merge_left():
    # [2, 2, 4, 8] -> [4, 4, 8, 0] with exponents [1, 1, 2, 3] -> [2, 2, 3, 0]
    row = (1, 1, 2, 3)
    res, score, changed = ROW_SLIDE_LEFT[row]
    assert res == (2, 2, 3, 0)
    assert score == 4  # 2^2
    assert changed is True

def test_no_double_merge_left():
    # [2, 2, 2, 2] -> [4, 4, 0, 0] with exponents [1, 1, 1, 1] -> [2, 2, 0, 0]
    row = (1, 1, 1, 1)
    res, score, changed = ROW_SLIDE_LEFT[row]
    assert res == (2, 2, 0, 0)
    assert score == 8  # 4 + 4

def test_slide_without_merge():
    # [0, 2, 0, 4] -> [2, 4, 0, 0] with exponents [0, 1, 0, 2] -> [1, 2, 0, 0]
    row = (0, 1, 0, 2)
    res, score, changed = ROW_SLIDE_LEFT[row]
    assert res == (1, 2, 0, 0)
    assert score == 0
    assert changed is True

def test_board_move_down():
    # Board with 2 at (0, 0) and 2 at (1, 0) -> move DOWN merges at (3, 0)
    b = [0] * 16
    b[0] = 1 # 2
    b[4] = 1 # 2
    board = tuple(b)
    new_b, score, changed = make_move(board, Move.DOWN)
    assert changed is True
    assert score == 4
    assert new_b[12] == 2 # 4 at bottom-left
    assert new_b[0] == 0
    assert new_b[4] == 0

def test_board_move_right():
    # Row 0: [2, 0, 2, 4] -> Right should be [0, 0, 4, 4]
    b = [0] * 16
    b[0] = 1
    b[2] = 1
    b[3] = 2
    board = tuple(b)
    new_b, score, changed = make_move(board, Move.RIGHT)
    assert changed is True
    assert score == 4
    assert new_b[0] == 0
    assert new_b[1] == 0
    assert new_b[2] == 2 # 4
    assert new_b[3] == 2 # 4

def test_is_game_over():
    # Full board with no adjacent matches
    # 1 2 1 2
    # 2 1 2 1
    # 1 2 1 2
    # 2 1 2 1
    board = (
        1, 2, 1, 2,
        2, 1, 2, 1,
        1, 2, 1, 2,
        2, 1, 2, 1
    )
    assert is_game_over(board) is True

    # But if one pair matches horizontally
    board2 = (
        1, 1, 2, 3,
        4, 5, 6, 7,
        8, 9, 10, 11,
        12, 13, 14, 15
    )
    assert is_game_over(board2) is False
