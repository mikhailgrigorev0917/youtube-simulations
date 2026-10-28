"""Full 2048 game execution and history recording."""

from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Any, Callable
from board import (
    BoardType, Move, empty_board, spawn_random_tile, make_move,
    get_legal_moves, is_game_over, max_tile_value, max_power, count_empty_cells
)

@dataclass
class MoveRecord:
    board_before: BoardType
    move: Move
    score_gained: int
    board_after_move: BoardType
    spawn_index: int
    spawn_power: int
    board_after_spawn: BoardType

@dataclass
class GameResult:
    bot_id: str
    seed: int
    score: int
    move_count: int
    max_tile: int
    max_power: int
    won_2048: bool
    reached_4096: bool
    reached_8192: bool
    reached_16384: bool
    reached_32768: bool
    reached_65536: bool
    history: List[MoveRecord] = field(default_factory=list)

class Game2048:
    def __init__(self, seed: Optional[int] = None, p4: float = 0.1):
        self.rng = random.Random(seed)
        self.seed = seed if seed is not None else random.randint(0, 10**9)
        self.p4 = p4
        self.board: BoardType = empty_board()
        self.score: int = 0
        self.move_count: int = 0
        self.history: List[MoveRecord] = []
        self._init_board()

    def _init_board(self) -> None:
        # Spawn two starting tiles
        self.board, _, _ = spawn_random_tile(self.board, self.rng, self.p4)
        self.board, _, _ = spawn_random_tile(self.board, self.rng, self.p4)

    def is_over(self) -> bool:
        return is_game_over(self.board)

    def get_legal_moves(self) -> List[Move]:
        return get_legal_moves(self.board)

    def step(self, move: Move, record_history: bool = False) -> bool:
        """Executes a move. Returns True if legal and executed, False otherwise."""
        board_before = self.board
        new_board, score_gained, changed = make_move(board_before, move)
        if not changed:
            return False

        self.score += score_gained
        self.move_count += 1

        # Spawn new tile
        board_after_spawn, spawn_idx, spawn_pow = spawn_random_tile(new_board, self.rng, self.p4)
        self.board = board_after_spawn

        if record_history:
            self.history.append(MoveRecord(
                board_before=board_before,
                move=move,
                score_gained=score_gained,
                board_after_move=new_board,
                spawn_index=spawn_idx,
                spawn_power=spawn_pow,
                board_after_spawn=board_after_spawn
            ))
        return True

    def play(self, strategy_func: Callable[[BoardType], Optional[Move]], bot_id: str = "bot", record_history: bool = False) -> GameResult:
        while not self.is_over():
            move = strategy_func(self.board)
            if move is None:
                # No legal move
                break
            success = self.step(move, record_history=record_history)
            if not success:
                # Illegal move picked, fallback to any legal move or break
                legal = self.get_legal_moves()
                if not legal:
                    break
                self.step(legal[0], record_history=record_history)

        m_tile = max_tile_value(self.board)
        m_pow = max_power(self.board)
        return GameResult(
            bot_id=bot_id,
            seed=self.seed,
            score=self.score,
            move_count=self.move_count,
            max_tile=m_tile,
            max_power=m_pow,
            won_2048=(m_tile >= 2048),
            reached_4096=(m_tile >= 4096),
            reached_8192=(m_tile >= 8192),
            reached_16384=(m_tile >= 16384),
            reached_32768=(m_tile >= 32768),
            reached_65536=(m_tile >= 65536),
            history=self.history
        )
