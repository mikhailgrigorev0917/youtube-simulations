from __future__ import annotations
from collections import Counter
import random
from typing import List, Dict, Set, Any
from strategies.base import BaseStrategy
from card import Card, Color, CardType

BASE_COLORS = [Color.RED, Color.YELLOW, Color.GREEN, Color.BLUE]


class CardCounterStrategy(BaseStrategy):
    """
    Information-aware Bayesian card counter:
    1. Tracks revealed color voids: when an opponent draws a card, records that they lacked that color.
    2. Exploits opponent weaknesses: if the next player is low on cards, chooses or switches to a color they are void in.
    3. Retains defensive action cards until opponents hit danger thresholds (<= 2 cards).
    4. Balances hand synergy with information exploitation.
    """

    def __init__(self, name: str = "CardCounter"):
        super().__init__(name)
        self.voids: Dict[int, Set[Color]] = {}
        self.discarded_colors: Counter = Counter()

    def on_game_start(self, player_index: int, total_players: int) -> None:
        self.voids = {i: set() for i in range(total_players)}
        self.discarded_colors = Counter()

    def on_event(self, event_type: str, data: Dict[str, Any]) -> None:
        if event_type == "player_drew_no_play":
            p_idx = data.get("player_index")
            active_col = data.get("active_color")
            if p_idx is not None and active_col in BASE_COLORS and p_idx in self.voids:
                self.voids[p_idx].add(active_col)
        elif event_type == "card_played":
            card = data.get("card")
            p_idx = data.get("player_index")
            if card and card.color in BASE_COLORS:
                self.discarded_colors[card.color] += 1
                # If player successfully played this color, they might not be void anymore
                if p_idx is not None and p_idx in self.voids and card.color in self.voids[p_idx]:
                    self.voids[p_idx].remove(card.color)

    def choose_card(
        self,
        hand: List[Card],
        valid_moves: List[Card],
        current_card: Card,
        active_color: Color,
        game_state: Dict[str, Any]
    ) -> Card:
        hand_counts = game_state.get("hand_counts", [])
        next_player = game_state.get("next_player_index", None)
        next_cards = hand_counts[next_player] if (next_player is not None and next_player < len(hand_counts)) else 7
        next_threat = next_cards <= 2

        next_voids = self.voids.get(next_player, set()) if next_player is not None else set()
        hand_counts_by_color = Counter(c.color for c in hand if c.color in BASE_COLORS)

        # If next player is an immediate threat:
        if next_threat:
            # 1. Action cards to stop them directly (+4, +2, Skip, Reverse)
            actions = [c for c in valid_moves if c.card_type in (CardType.WILD_DRAW_FOUR, CardType.DRAW_TWO, CardType.SKIP, CardType.REVERSE)]
            if actions:
                # Prioritize draw cards over skips
                order = {CardType.WILD_DRAW_FOUR: 0, CardType.DRAW_TWO: 1, CardType.SKIP: 2, CardType.REVERSE: 3}
                return sorted(actions, key=lambda c: order[c.card_type])[0]

            # 2. Can we switch color to one they are void in?
            void_moves = [c for c in valid_moves if not c.is_wild() and c.color in next_voids]
            if void_moves:
                return sorted(void_moves, key=lambda c: -hand_counts_by_color.get(c.color, 0))[0]

            # 3. Wild card to force void color
            wilds = [c for c in valid_moves if c.is_wild()]
            if wilds and next_voids:
                return wilds[0]

        # Peaceful phase:
        # Avoid wasting specials (+4, +2, Wild, Skip)
        plain_moves = [c for c in valid_moves if c.card_type == CardType.NUMBER]
        if plain_moves:
            # Prefer playing our dominant color, or a color the next player is void in
            def rank_plain(c: Card) -> tuple:
                is_next_void = 1 if c.color in next_voids else 0
                freq = hand_counts_by_color.get(c.color, 0)
                return (-is_next_void, -freq, -c.points)

            return sorted(plain_moves, key=rank_plain)[0]

        # If no plain cards, play actions with lowest value first
        return sorted(valid_moves, key=lambda c: (1 if c.is_wild() else 0, c.points))[0]

    def choose_color(self, hand: List[Card], game_state: Dict[str, Any]) -> Color:
        next_player = game_state.get("next_player_index", None)
        next_voids = self.voids.get(next_player, set()) if next_player is not None else set()
        hand_counts_by_color = Counter(c.color for c in hand if c.color in BASE_COLORS)

        # If next player is weak (has known voids) and we also have at least one card of that void color, force it!
        exploitable_colors = [col for col in next_voids if hand_counts_by_color.get(col, 0) > 0]
        if exploitable_colors:
            return sorted(exploitable_colors, key=lambda col: -hand_counts_by_color[col])[0]

        # Otherwise pick our most frequent color
        if hand_counts_by_color:
            return hand_counts_by_color.most_common(1)[0][0]

        return random.choice(BASE_COLORS)
