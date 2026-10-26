from __future__ import annotations
from collections import Counter
import random
from typing import List, Dict, Any
from strategies.base import BaseStrategy
from card import Card, Color, CardType

BASE_COLORS = [Color.RED, Color.YELLOW, Color.GREEN, Color.BLUE]


class AggressiveAttackerStrategy(BaseStrategy):
    """
    Highly offensive bot:
    - Prioritizes inflicting maximum penalties and turn disruption immediately.
    - Priority order: Wild Draw Four > Draw Two > Skip > Reverse > High Number.
    - Declares the color it has the most of.
    """

    def __init__(self, name: str = "AggressiveAttacker"):
        super().__init__(name)

    def _type_priority(self, card: Card) -> int:
        if card.card_type == CardType.WILD_DRAW_FOUR:
            return 0
        elif card.card_type == CardType.DRAW_TWO:
            return 1
        elif card.card_type == CardType.SKIP:
            return 2
        elif card.card_type == CardType.REVERSE:
            return 3
        elif card.card_type == CardType.WILD:
            return 4
        else:
            # Number cards: higher points first
            return 10 - int(card.value)

    def choose_card(
        self,
        hand: List[Card],
        valid_moves: List[Card],
        current_card: Card,
        active_color: Color,
        game_state: Dict[str, Any]
    ) -> Card:
        sorted_moves = sorted(valid_moves, key=self._type_priority)
        return sorted_moves[0]

    def choose_color(self, hand: List[Card], game_state: Dict[str, Any]) -> Color:
        counts = Counter(c.color for c in hand if c.color in BASE_COLORS)
        if not counts:
            return random.choice(BASE_COLORS)
        return counts.most_common(1)[0][0]
