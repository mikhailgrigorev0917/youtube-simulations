"""Classic Human Corner Dogma strategy: Down > Right > Left > Never Up."""

from typing import Optional
from board import BoardType, Move, get_legal_moves

class CornerBot:
    """Follows the classic human corner gospel:
    Strict preference: DOWN, then RIGHT, then LEFT.
    UP is forbidden and only played when absolutely forced.
    """
    PRIORITY = [Move.DOWN, Move.RIGHT, Move.LEFT, Move.UP]

    def get_move(self, board: BoardType) -> Optional[Move]:
        legal = set(get_legal_moves(board))
        if not legal:
            return None

        for move in self.PRIORITY:
            if move in legal:
                return move

        return None
