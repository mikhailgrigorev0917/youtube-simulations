from __future__ import annotations
import random
from typing import List, Dict, Any
from strategies.base import BaseStrategy
from card import Card, Color

BASE_COLORS = [Color.RED, Color.YELLOW, Color.GREEN, Color.BLUE]


class RandomStrategy(BaseStrategy):
    """Selects valid cards and wild colors completely at random."""

    def __init__(self, name: str = "Random"):
        super().__init__(name)

    def choose_card(
        self,
        hand: List[Card],
        valid_moves: List[Card],
        current_card: Card,
        active_color: Color,
        game_state: Dict[str, Any]
    ) -> Card:
        return random.choice(valid_moves)

    def choose_color(self, hand: List[Card], game_state: Dict[str, Any]) -> Color:
        return random.choice(BASE_COLORS)
