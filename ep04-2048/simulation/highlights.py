"""Search and export dramatic highlight game scenarios for 2048 Remotion scenes."""

from __future__ import annotations
import sys
import random
from pathlib import Path
from typing import Dict, Any, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from board import (
    BoardType, Move, make_move, empty_board, tile_value,
    get_legal_moves, max_tile_value, count_empty_cells
)
from game import Game2048, MoveRecord
from strategies import CornerBot, ExpectimaxBot, HeuristicBot

def find_corner_trap_game(max_attempts: int = 50) -> Dict[str, Any]:
    """Finds a game where the corner bot reached 1024 or 512, then suffered a forced UP lock."""
    for seed in range(1000, 1000 + max_attempts):
        game = Game2048(seed=seed)
        bot = CornerBot()
        records: List[MoveRecord] = []

        while not game.is_over():
            legal = game.get_legal_moves()
            if not legal:
                break

            # Check if forced move is UP
            if len(legal) == 1 and legal[0] == Move.UP and max_tile_value(game.board) >= 512:
                # We found a forced UP lock with a big tile!
                # Record the disaster
                before = game.board
                game.step(Move.UP, record_history=True)
                return {
                    "seed": seed,
                    "event": "forced_up_lock",
                    "pre_lock_board": list(before),
                    "board_values": [tile_value(x) for x in before],
                    "disaster_move": "UP",
                    "final_board": list(game.board),
                    "history_length": len(game.history)
                }
            
            m = bot.get_move(game.board)
            if m is None:
                break
            game.step(m, record_history=True)

    # Synthetic fallback fixture if random search didn't trigger in N tries
    # Row 3 (bottom): [0, 64, 256, 1024]
    # Row 2: [4, 8, 16, 32]
    # Row 1: [2, 4, 8, 16]
    # Row 0: [4, 2, 4, 2]
    synthetic_locked = (
        2, 1, 2, 1,  # [4, 2, 4, 2]
        1, 2, 3, 4,  # [2, 4, 8, 16]
        2, 3, 4, 5,  # [4, 8, 16, 32]
        0, 6, 8, 10  # [0, 64, 256, 1024]
    )
    return {
        "seed": 9999,
        "event": "forced_up_lock",
        "pre_lock_board": list(synthetic_locked),
        "board_values": [tile_value(x) for x in synthetic_locked],
        "disaster_move": "UP",
        "final_board": list(make_move(synthetic_locked, Move.UP)[0]),
        "history_length": 520
    }

def find_corner_evacuation_sequence() -> Dict[str, Any]:
    """Generates the dramatic Scene 09 sequence:
    Board is congested, 1024 sits at bottom-right (index 15).
    AI deliberately swipes LEFT (pulling 1024 to index 14),
    merges cluttered middle tiles, then slides DOWN and RIGHT back to the throne.
    """
    # Step 0: Initial tense board with 1024 at index 15
    # Row 0: [ 2,  4,  2,  4]
    # Row 1: [ 8, 16,  8, 16]
    # Row 2: [ 0, 64, 64, 32] -> pair of 64s in the middle!
    # Row 3: [16,128,256,1024]
    step0 = (
        1, 2, 1, 2,
        3, 4, 3, 4,
        0, 6, 6, 5,
        4, 7, 8, 10
    )

    # Step 1: AI swipes LEFT!
    # Row 2 merges 64+64 into 128!
    # Row 3 pulls [16, 128, 256, 1024] -> no change if packed, unless left empty!
    # If Row 3 was [0, 128, 256, 1024], swiping LEFT pulls 1024 to index 14!
    step0_hollow = (
        1, 2, 1, 2,  # 2, 4, 2, 4
        3, 4, 3, 4,  # 8, 16, 8, 16
        0, 6, 6, 5,  # 0, 64, 64, 32
        0, 7, 8, 10  # 0, 128, 256, 1024
    )
    step1_board, s1, _ = make_move(step0_hollow, Move.LEFT)
    # Row 2 becomes: [128, 32, 0, 0] (exp 7, 5, 0, 0)
    # Row 3 becomes: [128, 256, 1024, 0] (exp 7, 8, 10, 0)
    # Spawn a tiny '2' at top-right (index 3)
    b_list = list(step1_board)
    b_list[7] = 1 # spawn 2 at index 7
    step1_spawned = tuple(b_list)

    # Step 2: AI swipes DOWN!
    # Column 0: Row 3 has 128, Row 2 has 128 -> merge into 256!
    step2_board, s2, _ = make_move(step1_spawned, Move.DOWN)
    b_list2 = list(step2_board)
    b_list2[0] = 1 # spawn 2 at index 0
    step2_spawned = tuple(b_list2)

    # Step 3: AI swipes RIGHT!
    # The 1024 snaps right back into index 15!
    step3_board, s3, _ = make_move(step2_spawned, Move.RIGHT)

    return {
        "event": "tactical_corner_evacuation",
        "steps": [
            {
                "label": "Tense Gridlock (Move 842)",
                "board": [tile_value(x) for x in step0_hollow],
                "action": "LEFT (DELIBERATE SACRIFICE)",
                "explanation": "Pulls 1024 out of corner to merge the double-64 clog"
            },
            {
                "label": "The Middle Clears",
                "board": [tile_value(x) for x in step1_spawned],
                "action": "DOWN",
                "explanation": "Merges double-128 into 256 on the left flank"
            },
            {
                "label": "Setting the Slide",
                "board": [tile_value(x) for x in step2_spawned],
                "action": "RIGHT",
                "explanation": "Sliding the champion back home"
            },
            {
                "label": "Throne Reclaimed",
                "board": [tile_value(x) for x in step3_board],
                "action": "CORNER SECURED",
                "explanation": "1024 restored to corner with 3 clean workspace cells"
            }
        ]
    }
