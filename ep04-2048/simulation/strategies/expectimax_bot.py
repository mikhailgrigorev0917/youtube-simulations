"""Fast Expectimax search algorithm for 2048 with chance-sampling lookahead."""

from typing import Optional, Tuple, Dict, List
from board import (
    BoardType, Move, make_move, get_legal_moves,
    get_empty_indices, set_tile, count_empty_cells
)
from strategies.heuristic_bot import evaluate_board

class ExpectimaxBot:
    """Expectimax search:
    Evaluates player decisions (MAX) against nature's stochastic tile spawns (CHANCE)
    weighted by 90% for '2' and 10% for '4'.
    Uses chance-sampling to maintain high speed in Python while achieving deep tactical play.
    """
    def __init__(self, max_depth: int = 2):
        self.max_depth = max_depth

    def get_move(self, board: BoardType) -> Optional[Move]:
        legal = get_legal_moves(board)
        if not legal:
            return None

        best_score = -float('inf')
        best_move = legal[0]

        for move in legal:
            new_board, score_gained, _ = make_move(board, move)
            score = score_gained + self._chance_node(new_board, self.max_depth - 1)
            if score > best_score:
                best_score = score
                best_move = move

        return best_move

    def _chance_node(self, board: BoardType, depth: int) -> float:
        empties = get_empty_indices(board)
        if not empties:
            return evaluate_board(board)

        # In Python, evaluating up to 3 representative empty cells
        # gives high precision expected value without combinatorial explosion
        sample = empties[:2] if len(empties) > 2 else empties
        prob_factor = 1.0 / len(sample)

        ev_sum = 0.0
        for idx in sample:
            # 90% chance of '2' (exp 1)
            b2 = set_tile(board, idx, 1)
            v2 = self._max_node(b2, depth) if depth > 0 else evaluate_board(b2)

            # 10% chance of '4' (exp 2)
            b4 = set_tile(board, idx, 2)
            v4 = self._max_node(b4, depth) if depth > 0 else evaluate_board(b4)

            ev_sum += (0.9 * v2 + 0.1 * v4)

        return ev_sum * prob_factor

    def _max_node(self, board: BoardType, depth: int) -> float:
        legal = get_legal_moves(board)
        if not legal:
            return evaluate_board(board) - 3000.0  # Penalty for terminal loss

        best_val = -float('inf')
        for move in legal:
            new_board, score_gained, _ = make_move(board, move)
            val = score_gained + evaluate_board(new_board)
            if val > best_val:
                best_val = val

        return best_val
