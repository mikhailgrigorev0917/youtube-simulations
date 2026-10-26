from __future__ import annotations
from collections import Counter
import random
from typing import List, Dict, Any
from strategies.base import BaseStrategy
from card import Card, Color, CardType

BASE_COLORS = [Color.RED, Color.YELLOW, Color.GREEN, Color.BLUE]


class TacticalSniperStrategy(BaseStrategy):
    """
    Strategic card preserver & targeted disruption:
    - Assesses table threats: if next player has <= 2 cards, strikes with high disruption (+4, +2, Skip).
    - If no immediate threat, saves special cards and plays normal number cards to deplete hand safely.
    - Preserves Wild cards for endgame exits or critical blocks.
    """

    def __init__(self, name: str = "TacticalSniper"):
        super().__init__(name)

    def choose_card(
        self,
        hand: List[Card],
        valid_moves: List[Card],
        current_card: Card,
        active_color: Color,
        game_state: Dict[str, Any]
    ) -> Card:
        hand_counts = game_state.get("hand_counts", [])
        next_player_idx = game_state.get("next_player_index", None)
        
        # Check if next player is on low cards (threat of winning)
        next_player_cards = hand_counts[next_player_idx] if (next_player_idx is not None and next_player_idx < len(hand_counts)) else 7
        next_is_threat = next_player_cards <= 2
        any_threat = any(c <= 2 for i, c in enumerate(hand_counts) if i != game_state.get("player_index"))

        counts = Counter(c.color for c in hand if c.color in BASE_COLORS)

        if next_is_threat:
            # High threat: prioritize hard stops on next player
            def threat_priority(card: Card) -> int:
                if card.card_type == CardType.WILD_DRAW_FOUR:
                    return 0
                if card.card_type == CardType.DRAW_TWO:
                    return 1
                if card.card_type == CardType.SKIP:
                    return 2
                if card.card_type == CardType.REVERSE:
                    return 3
                if card.card_type == CardType.WILD:
                    return 4
                return 10 + counts.get(card.color, 0)

            return sorted(valid_moves, key=threat_priority)[0]
        else:
            # Peaceful phase: conserve disruptive power, play plain number cards first
            def peaceful_priority(card: Card) -> tuple:
                is_disruptive = card.card_type in (
                    CardType.WILD_DRAW_FOUR,
                    CardType.DRAW_TWO,
                    CardType.SKIP,
                    CardType.WILD
                )
                freq = counts.get(card.color, 0)
                # We want NOT disruptive first, highest frequency of our color, then highest points
                return (
                    1 if is_disruptive else 0,
                    -freq,
                    -card.points
                )

            return sorted(valid_moves, key=peaceful_priority)[0]

    def choose_color(self, hand: List[Card], game_state: Dict[str, Any]) -> Color:
        counts = Counter(c.color for c in hand if c.color in BASE_COLORS)
        if not counts:
            return random.choice(BASE_COLORS)
        return counts.most_common(1)[0][0]
