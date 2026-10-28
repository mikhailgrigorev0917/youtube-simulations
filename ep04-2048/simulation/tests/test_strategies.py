"""Test that all strategies play games without error."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from game import Game2048
from strategies import RandomBot, GreedyBot, CornerBot, HeuristicBot, ExpectimaxBot

def test_random_bot():
    game = Game2048(seed=42)
    bot = RandomBot()
    res = game.play(bot.get_move, bot_id="Random")
    assert res.move_count > 10
    assert res.score > 0

def test_greedy_bot():
    game = Game2048(seed=42)
    bot = GreedyBot()
    res = game.play(bot.get_move, bot_id="Greedy")
    assert res.move_count > 10
    assert res.score > 0

def test_corner_bot():
    game = Game2048(seed=42)
    bot = CornerBot()
    res = game.play(bot.get_move, bot_id="Corner")
    assert res.move_count > 10
    assert res.score > 0

def test_heuristic_bot():
    game = Game2048(seed=42)
    bot = HeuristicBot()
    res = game.play(bot.get_move, bot_id="Heuristic")
    assert res.move_count > 50
    assert res.max_tile >= 128

def test_expectimax_bot():
    game = Game2048(seed=42)
    bot = ExpectimaxBot(max_depth=2)
    # Just run 20 moves to verify search execution
    for _ in range(20):
        if game.is_over():
            break
        m = bot.get_move(game.board)
        if m is not None:
            game.step(m)
    assert game.move_count == 20
    assert game.score > 0
