"""Heuristic strategy using Monotonicity, Smoothness, Empty Cells, and Snake weights."""

import math
from typing import Optional, Tuple
from board import (
    BoardType, Move, make_move, get_legal_moves,
    count_empty_cells, max_power
)

# Classic Snake weight matrix favoring bottom-right anchor:
#  0   1   2   3
#  7   6   5   4
#  8   9  10  11
# 15  14  13  12  <- or anchored at 15
SNAKE_WEIGHTS = (
    1,     2,     4,     8,
    128,   64,    32,    16,
    256,   512,  1024,  2048,
    32768, 16384, 8192,  4096
)

def evaluate_board(board: BoardType) -> float:
    """Computes a composite heuristic score:
    - Snake alignment (monotonicity path)
    - Smoothness penalty (-sum of log differences between adjacent non-zero tiles)
    - Empty cell capacity bonus
    - Corner champion bonus
    """
    empty_cnt = count_empty_cells(board)
    empty_score = empty_cnt * 100.0

    # 1. Snake weighted sum
    snake_score = 0.0
    for i in range(16):
        exp = board[i]
        if exp > 0:
            snake_score += (1 << exp) * SNAKE_WEIGHTS[i]

    # 2. Smoothness: penalize value differences between neighbors
    smoothness = 0.0
    for r in range(4):
        offset = r * 4
        for c in range(3):
            v1 = board[offset + c]
            v2 = board[offset + c + 1]
            if v1 > 0 and v2 > 0:
                smoothness -= abs(v1 - v2) * 15.0

    for c in range(4):
        for r in range(3):
            v1 = board[r * 4 + c]
            v2 = board[(r + 1) * 4 + c]
            if v1 > 0 and v2 > 0:
                smoothness -= abs(v1 - v2) * 15.0

    # 3. Monotonicity along bottom-right gradient
    monotonicity = 0.0
    # Left to right in bottom row (increasing towards index 12 / corner 12)
    # Check if max tile is in the corner (index 12 is bottom-left, index 15 is bottom-right)
    m_pow = max_power(board)
    corner_bonus = 0.0
    if board[12] == m_pow or board[15] == m_pow or board[0] == m_pow or board[3] == m_pow:
        corner_bonus = 1000.0

    return snake_score * 0.1 + empty_score + smoothness + corner_bonus

class HeuristicBot:
    def get_move(self, board: BoardType) -> Optional[Move]:
        legal = get_legal_moves(board)
        if not legal:
            return None

        best_score = -float('inf')
        best_move = legal[0]

        for move in legal:
            new_board, score_gained, _ = make_move(board, move)
            eval_score = evaluate_board(new_board) + score_gained
            if eval_score > best_score:
                best_score = eval_score
                best_move = move

        return best_move
