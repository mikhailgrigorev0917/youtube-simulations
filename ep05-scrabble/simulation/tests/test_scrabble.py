"""Unit tests for Scrabble Simulation Engine (Episode 05)."""

import sys
from pathlib import Path

# Add simulation dir to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from game import (
    COMMON_VOCABULARY,
    LEAVE_EQUITY,
    LETTER_SCORES,
    TILE_DISTRIBUTION,
    TWO_LETTER_WORDS,
    ScrabbleBoard,
    TileBag,
    get_board_multiplier,
)
from strategies import (
    GreedyBot,
    LeaveEquityBot,
    LongWordBot,
    MasterTacticalBot,
    TwoLetterHookBot,
    compute_leave_equity,
)


def test_tile_bag_total_count():
    """Verify official standard Scrabble tile distribution equals 100 tiles."""
    total = sum(TILE_DISTRIBUTION.values())
    assert total == 100, f"Expected 100 tiles, got {total}"

    bag = TileBag(seed=42)
    assert bag.remaining == 100
    drawn = bag.draw(7)
    assert len(drawn) == 7
    assert bag.remaining == 93


def test_premium_multipliers():
    """Verify official board multipliers (Center DW, Corners TW, DL, TL)."""
    # Center square (7, 7) must be Double Word (1, 2)
    assert get_board_multiplier(7, 7) == (1, 2)

    # Corner square (0, 0) must be Triple Word (1, 3)
    assert get_board_multiplier(0, 0) == (1, 3)

    # Triple Letter (1, 5)
    assert get_board_multiplier(1, 5) == (3, 1)

    # Double Letter (0, 3)
    assert get_board_multiplier(0, 3) == (2, 1)

    # Neutral square (4, 1)
    assert get_board_multiplier(4, 1) == (1, 1)


def test_bingo_bonus():
    """Verify placing 7 tiles grants the +50 point Bingo bonus."""
    board = ScrabbleBoard()
    # Center square (7, 7) is Double Word
    # Word 'RETINAS' (R=1, E=1, T=1, I=1, N=1, A=1, S=1 = 7 base pts)
    # Placing across row 7 from col 1 to 7
    score = board.place_word("RETINAS", row=7, col=1, horizontal=True)
    # Center (7, 7) has 2x word multiplier, plus 50-point bonus
    assert score > 50, f"Expected > 50 score with Bingo, got {score}"
    assert board.is_empty is False


def test_two_letter_words_set():
    """Verify high-power two-letter words exist in the dictionary."""
    essential = ["QI", "ZA", "OX", "XI", "EX", "JO"]
    for w in essential:
        assert w in TWO_LETTER_WORDS, f"Missing essential 2-letter word: {w}"


def test_leave_equity():
    """Verify Rack Leave Equity table assigns highest value to 'S' and '?' and lowest to 'Q'."""
    assert LEAVE_EQUITY['S'] > 0
    assert LEAVE_EQUITY['?'] > LEAVE_EQUITY['S']
    assert LEAVE_EQUITY['Q'] < -5.0

    rack = ['S', 'A', 'T', 'I', 'R', 'E', 'Q']
    # If we dump Q, leave is positive SATIRE
    equity_dump_q = compute_leave_equity(rack, played=['Q'])
    # If we dump S, leave is crippled with Q
    equity_dump_s = compute_leave_equity(rack, played=['S'])
    assert equity_dump_q > equity_dump_s


def test_bot_strategies():
    """Verify all 5 bot archetypes can evaluate and pick moves."""
    board = ScrabbleBoard()
    rack = ['Z', 'A', 'S', 'E', 'T', 'I', 'N']

    b1 = LongWordBot()
    m1 = b1.choose_move(rack, board)
    assert m1 is not None

    b2 = GreedyBot()
    m2 = b2.choose_move(rack, board)
    assert m2 is not None

    b3 = TwoLetterHookBot()
    m3 = b3.choose_move(rack, board)
    assert m3 is not None
    assert m3.word == "ZA"  # Should prioritize high-power 2-letter hook

    b4 = LeaveEquityBot()
    m4 = b4.choose_move(rack, board)
    assert m4 is not None

    b5 = MasterTacticalBot()
    m5 = b5.choose_move(rack, board)
    assert m5 is not None
