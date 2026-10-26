from __future__ import annotations
import random
from typing import List, Dict, Any
from strategies.base import BaseStrategy
from card import Card, Color

BASE_COLORS = [Color.RED, Color.YELLOW, Color.GREEN, Color.BLUE]


class PointMinimizerStrategy(BaseStrategy):
    """
    Tournament-oriented risk-averse strategy:
    - High-value cards (Wild: 50, Action: 20, 9-7) are disastrous if someone else wins.
    - Dumps highest point cards first whenever valid, reducing expected penalty score.
    """

    def __init__(self, name: str = "PointMinimizer"):
        super().__init__(name)

    def choose_card(
        self,
        hand: List[Card],
        valid_moves: List[Card],
        current_card: Card,
        active_color: Color,
        game_state: Dict[str, Any]
    ) -> Card:
        # Highest points first
        return sorted(valid_moves, key=lambda c: -c.points)[0]

    def choose_color(self, hand: List[Card], game_state: Dict[str, Any]) -> Color:
        # Pick color that holds the most total points in our remaining hand
        color_points = {c: 0 for c in BASE_COLORS}
        for card in hand:
            if card.color in BASE_COLORS:
                color_points[card.color] += card.points
        best = max(color_points.items(), key=lambda x: x[1])
        if best[1] > 0:
            return best[0]
        return random.choice(BASE_COLORS)
