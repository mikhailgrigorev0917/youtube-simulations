"""Greedy score-maximizing strategy."""

from typing import Optional
from board import BoardType, Move, make_move, get_legal_moves

class GreedyBot:
    def get_move(self, board: BoardType) -> Optional[Move]:
        legal = get_legal_moves(board)
        if not legal:
            return None

        best_score = -1
        best_move = legal[0]

        for move in legal:
            _, score, _ = make_move(board, move)
            if score > best_score:
                best_score = score
                best_move = move

        return best_move
