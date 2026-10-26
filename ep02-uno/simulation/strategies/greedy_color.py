from __future__ import annotations
from collections import Counter
import random
from typing import List, Dict, Any
from strategies.base import BaseStrategy
from card import Card, Color

BASE_COLORS = [Color.RED, Color.YELLOW, Color.GREEN, Color.BLUE]


class GreedyColorStrategy(BaseStrategy):
    """
    Maximizes color flow:
    - Counts how many cards of each color are currently in hand.
    - Favors playing cards that match the dominant color in hand.
    - Saves Wild cards unless forced or if dominant color changes.
    - Always declares the color they have the most cards of.
    """

    def __init__(self, name: str = "GreedyColor"):
        super().__init__(name)

    def _color_counts(self, hand: List[Card]) -> Counter:
        return Counter(c.color for c in hand if c.color in BASE_COLORS)

    def choose_card(
        self,
        hand: List[Card],
        valid_moves: List[Card],
        current_card: Card,
        active_color: Color,
        game_state: Dict[str, Any]
    ) -> Card:
        counts = self._color_counts(hand)
        
        # Sort valid moves:
        # 1. Non-wild cards matching dominant color
        # 2. Other non-wild cards
        # 3. Wild cards
        def move_score(card: Card) -> tuple:
            is_wild = card.is_wild()
            color_frequency = counts.get(card.color, 0)
            return (
                0 if not is_wild else 1,  # Prefer non-wild first
                -color_frequency,          # Highest color count first
                -card.points               # Tie-break: dump higher points
            )

        sorted_moves = sorted(valid_moves, key=move_score)
        return sorted_moves[0]

    def choose_color(self, hand: List[Card], game_state: Dict[str, Any]) -> Color:
        counts = self._color_counts(hand)
        if not counts:
            return random.choice(BASE_COLORS)
        return counts.most_common(1)[0][0]
