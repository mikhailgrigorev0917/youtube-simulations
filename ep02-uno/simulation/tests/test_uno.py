import sys
from pathlib import Path

# Add simulation folder to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from card import Card, Color, CardType, create_standard_deck
from game import UnoGame
from strategies.random_bot import RandomStrategy
from strategies.greedy_color import GreedyColorStrategy
from strategies.tactical_sniper import TacticalSniperStrategy
from strategies.card_counter import CardCounterStrategy



def test_standard_deck():
    deck = create_standard_deck()
    assert len(deck) == 108
    # 4 Wild and 4 Wild Draw Four
    wilds = [c for c in deck if c.card_type == CardType.WILD]
    wild4s = [c for c in deck if c.card_type == CardType.WILD_DRAW_FOUR]
    assert len(wilds) == 4
    assert len(wild4s) == 4


def test_card_matching():
    r5 = Card(Color.RED, "5", CardType.NUMBER)
    r9 = Card(Color.RED, "9", CardType.NUMBER)
    b5 = Card(Color.BLUE, "5", CardType.NUMBER)
    g3 = Card(Color.GREEN, "3", CardType.NUMBER)
    wild = Card(Color.WILD, "wild", CardType.WILD)

    # Same color matches
    assert r9.can_play_on(r5, Color.RED) is True
    # Same number matches
    assert b5.can_play_on(r5, Color.RED) is True
    # Different color and number does not match
    assert g3.can_play_on(r5, Color.RED) is False
    # Wild matches anything
    assert wild.can_play_on(r5, Color.RED) is True


def test_uno_game_completion():
    players = [
        RandomStrategy("Bot1"),
        GreedyColorStrategy("Bot2"),
        TacticalSniperStrategy("Bot3"),
        CardCounterStrategy("Bot4")
    ]
    game = UnoGame(players=players, allow_stacking=False, seed=123)
    stats = game.run()
    assert stats.winner_index in (0, 1, 2, 3)
    assert stats.total_turns > 0
    assert stats.final_hand_sizes[stats.winner_index] == 0


def test_stacking_game_completion():
    players = [
        TacticalSniperStrategy("Sniper1"),
        CardCounterStrategy("Counter1"),
        GreedyColorStrategy("Greedy1"),
        RandomStrategy("Random1")
    ]
    game = UnoGame(players=players, allow_stacking=True, seed=999)
    stats = game.run()
    assert stats.winner_index in (0, 1, 2, 3)
    assert stats.final_hand_sizes[stats.winner_index] == 0
