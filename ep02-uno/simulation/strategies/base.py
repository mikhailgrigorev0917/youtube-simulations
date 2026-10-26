from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict, Set, Optional, Any
from card import Card, Color


class BaseStrategy(ABC):
    """Abstract base class for UNO strategies."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def choose_card(
        self,
        hand: List[Card],
        valid_moves: List[Card],
        current_card: Card,
        active_color: Color,
        game_state: Dict[str, Any]
    ) -> Card:
        """Choose one card to play from the list of valid_moves."""
        pass

    @abstractmethod
    def choose_color(
        self,
        hand: List[Card],
        game_state: Dict[str, Any]
    ) -> Color:
        """When playing a Wild card, select the declared color (RED, YELLOW, GREEN, BLUE)."""
        pass

    def on_game_start(self, player_index: int, total_players: int) -> None:
        """Hook called when a new game starts."""
        pass

    def on_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Hook for public table events (e.g., player drew cards, color changed)."""
        pass
