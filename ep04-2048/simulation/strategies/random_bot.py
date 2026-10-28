"""Random legal move strategy."""

import random
from typing import Optional
from board import BoardType, Move, get_legal_moves

class RandomBot:
    def __init__(self, rng: Optional[random.Random] = None):
        self.rng = rng or random.Random()

    def get_move(self, board: BoardType) -> Optional[Move]:
        legal = get_legal_moves(board)
        if not legal:
            return None
        return self.rng.choice(legal)
