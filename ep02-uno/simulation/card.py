from __future__ import annotations
from enum import Enum
from typing import List, Optional
import random


class Color(str, Enum):
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"
    BLUE = "blue"
    WILD = "wild"


class CardType(str, Enum):
    NUMBER = "number"
    SKIP = "skip"
    REVERSE = "reverse"
    DRAW_TWO = "draw_two"
    WILD = "wild"
    WILD_DRAW_FOUR = "wild_draw_four"


class Card:
    __slots__ = ("color", "value", "card_type", "points")

    def __init__(self, color: Color, value: str, card_type: CardType):
        self.color = color
        self.value = value
        self.card_type = card_type
        self.points = self._calc_points()

    def _calc_points(self) -> int:
        if self.card_type == CardType.NUMBER:
            return int(self.value)
        elif self.card_type in (CardType.SKIP, CardType.REVERSE, CardType.DRAW_TWO):
            return 20
        elif self.card_type in (CardType.WILD, CardType.WILD_DRAW_FOUR):
            return 50
        return 0

    def is_wild(self) -> bool:
        return self.color == Color.WILD or self.card_type in (CardType.WILD, CardType.WILD_DRAW_FOUR)

    def can_play_on(self, current_card: Card, active_color: Color) -> bool:
        if self.is_wild():
            return True
        if self.color == active_color:
            return True
        if self.value == current_card.value:
            return True
        return False

    def __repr__(self) -> str:
        if self.is_wild():
            return f"[{self.card_type.value.upper()}]"
        return f"[{self.color.value.upper()}:{self.value}]"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return False
        return self.color == other.color and self.value == other.value

    def __hash__(self) -> int:
        return hash((self.color, self.value))


def create_standard_deck() -> List[Card]:
    cards: List[Card] = []
    base_colors = [Color.RED, Color.YELLOW, Color.GREEN, Color.BLUE]

    for color in base_colors:
        # One 0 per color
        cards.append(Card(color, "0", CardType.NUMBER))
        # Two of each 1-9
        for n in range(1, 10):
            cards.append(Card(color, str(n), CardType.NUMBER))
            cards.append(Card(color, str(n), CardType.NUMBER))
        # Two Skips, Reverses, Draw Twos
        for _ in range(2):
            cards.append(Card(color, "skip", CardType.SKIP))
            cards.append(Card(color, "reverse", CardType.REVERSE))
            cards.append(Card(color, "draw_two", CardType.DRAW_TWO))

    # Wild cards (4 Wild, 4 Wild Draw Four)
    for _ in range(4):
        cards.append(Card(Color.WILD, "wild", CardType.WILD))
        cards.append(Card(Color.WILD, "wild_draw_four", CardType.WILD_DRAW_FOUR))

    return cards
