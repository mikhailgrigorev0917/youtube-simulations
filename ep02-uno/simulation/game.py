from __future__ import annotations
import random
from typing import List, Dict, Optional, Any
from card import Card, Color, CardType, create_standard_deck
from strategies.base import BaseStrategy

BASE_COLORS = [Color.RED, Color.YELLOW, Color.GREEN, Color.BLUE]
MAX_TURNS = 1500


def card_to_dict(card: Card) -> Dict[str, Any]:
    return {"color": card.color.value, "value": card.value, "type": card.card_type.value}


class GameStats:
    def __init__(self, num_players: int):
        self.winner_index: int = -1
        self.total_turns: int = 0
        self.turns_per_player: List[int] = [0] * num_players
        self.cards_drawn_per_player: List[int] = [0] * num_players
        self.actions_played_per_player: List[int] = [0] * num_players
        self.final_hand_sizes: List[int] = [0] * num_players
        self.final_hand_points: List[int] = [0] * num_players
        # Hand size of every player after every turn (for trajectory charts)
        self.hand_size_trace: List[List[int]] = []
        # Size of every forced draw penalty (+2 / +4 / stacked chains)
        self.penalties: List[int] = []
        self.history: List[Dict[str, Any]] = []


class UnoGame:
    """
    UNO round engine.

    Rules:
      - Official Mattel rules by default.
      - `allow_stacking`: house rule, +2 may be answered with +2/+4, +4 with +4; the
        player who cannot answer draws the accumulated total and loses the turn.
      - `restrict_wild_draw_four`: official rule — Wild Draw Four may only be played
        when you hold no card matching the active colour (challenges are not modelled).
      - Drawing: if you cannot play you draw one card; if it is playable you play it.
    """

    def __init__(
        self,
        players: List[BaseStrategy],
        allow_stacking: bool = False,
        restrict_wild_draw_four: bool = True,
        seed: Optional[int] = None,
        record_history: bool = False,
    ):
        self.players = players
        self.num_players = len(players)
        self.allow_stacking = allow_stacking
        self.restrict_wild_draw_four = restrict_wild_draw_four
        self.record_history = record_history
        self.rng = random.Random(seed)

        self.draw_pile: List[Card] = []
        self.discard_pile: List[Card] = []
        self.hands: List[List[Card]] = [[] for _ in range(self.num_players)]

        self.current_player: int = 0
        self.direction: int = 1
        self.active_color: Color = Color.RED
        self.pending_draw: int = 0
        self.game_over: bool = False
        self.stats = GameStats(self.num_players)

    # ------------------------------------------------------------------ deck
    def _reshuffle_discard_into_draw(self) -> None:
        if len(self.discard_pile) <= 1:
            return
        top = self.discard_pile.pop()
        cards = self.discard_pile[:]
        self.discard_pile = [top]
        self.rng.shuffle(cards)
        self.draw_pile.extend(cards)

    def draw_card(self, player_idx: int) -> Optional[Card]:
        if not self.draw_pile:
            self._reshuffle_discard_into_draw()
        if not self.draw_pile:
            return None
        card = self.draw_pile.pop()
        self.hands[player_idx].append(card)
        self.stats.cards_drawn_per_player[player_idx] += 1
        return card

    def _give_penalty(self, player_idx: int, count: int) -> None:
        for _ in range(count):
            self.draw_card(player_idx)
        self.stats.penalties.append(count)

    def _next_player_index(self, step: int = 1) -> int:
        return (self.current_player + self.direction * step) % self.num_players

    # ------------------------------------------------------------------ rules
    def _legal(self, card: Card, hand: List[Card]) -> bool:
        top = self.discard_pile[-1]
        if not card.can_play_on(top, self.active_color):
            return False
        if self.restrict_wild_draw_four and card.card_type == CardType.WILD_DRAW_FOUR:
            if any(c.color == self.active_color for c in hand):
                return False
        return True

    def get_valid_moves(self, player_idx: int) -> List[Card]:
        top = self.discard_pile[-1]
        hand = self.hands[player_idx]
        if self.allow_stacking and self.pending_draw > 0:
            if top.card_type == CardType.DRAW_TWO:
                return [c for c in hand if c.card_type in (CardType.DRAW_TWO, CardType.WILD_DRAW_FOUR)]
            if top.card_type == CardType.WILD_DRAW_FOUR:
                return [c for c in hand if c.card_type == CardType.WILD_DRAW_FOUR]
        return [c for c in hand if self._legal(c, hand)]

    # ------------------------------------------------------------------ events
    def _broadcast_event(self, event_type: str, data: Dict[str, Any]) -> None:
        if self.record_history:
            record = {"event": event_type, "turn": self.stats.total_turns}
            for k, v in data.items():
                if isinstance(v, Card):
                    record[k] = card_to_dict(v)
                elif isinstance(v, Color):
                    record[k] = v.value
                else:
                    record[k] = v
            record["handSizes"] = [len(h) for h in self.hands]
            record["hands"] = [[card_to_dict(c) for c in h] for h in self.hands]
            record["activeColor"] = self.active_color.value
            record["direction"] = self.direction
            record["pendingDraw"] = self.pending_draw
            self.stats.history.append(record)
        for player in self.players:
            player.on_event(event_type, data)

    # ------------------------------------------------------------------ setup
    def _init_game(self) -> None:
        self.draw_pile = create_standard_deck()
        self.rng.shuffle(self.draw_pile)
        for i, player in enumerate(self.players):
            player.on_game_start(i, self.num_players)

        for _ in range(7):
            for i in range(self.num_players):
                self.hands[i].append(self.draw_pile.pop())

        first = self.draw_pile.pop()
        while first.card_type == CardType.WILD_DRAW_FOUR:
            self.draw_pile.insert(0, first)
            first = self.draw_pile.pop()
        self.discard_pile.append(first)
        self.active_color = self.rng.choice(BASE_COLORS) if first.is_wild() else first.color

        self._broadcast_event("game_started", {"card": first})

        if first.card_type == CardType.DRAW_TWO:
            if self.allow_stacking:
                self.pending_draw = 2
            else:
                self._give_penalty(0, 2)
                self.current_player = self._next_player_index(1)
        elif first.card_type == CardType.REVERSE:
            if self.num_players == 2:
                self.current_player = self._next_player_index(1)
            else:
                self.direction *= -1
                self.current_player = self.num_players - 1
        elif first.card_type == CardType.SKIP:
            self.current_player = self._next_player_index(1)

    # ------------------------------------------------------------------ turn
    def play_turn(self) -> bool:
        if self.game_over:
            return False

        player_idx = self.current_player
        player = self.players[player_idx]
        hand = self.hands[player_idx]
        self.stats.total_turns += 1
        self.stats.turns_per_player[player_idx] += 1

        top_card = self.discard_pile[-1]
        valid_moves = self.get_valid_moves(player_idx)
        state_view = {
            "player_index": player_idx,
            "num_players": self.num_players,
            "hand_counts": [len(h) for h in self.hands],
            "direction": self.direction,
            "next_player_index": self._next_player_index(1),
            "draw_pile_count": len(self.draw_pile),
            "pending_draw": self.pending_draw,
        }

        if self.allow_stacking and self.pending_draw > 0 and not valid_moves:
            count = self.pending_draw
            self._give_penalty(player_idx, count)
            self.pending_draw = 0
            self._broadcast_event("stacked_penalty_taken", {"player_index": player_idx, "count": count})
            self.current_player = self._next_player_index(1)
            self._after_turn()
            return not self.game_over

        chosen: Optional[Card] = None
        if valid_moves:
            chosen = player.choose_card(hand, valid_moves, top_card, self.active_color, state_view)
        else:
            drawn = self.draw_card(player_idx)
            if drawn is not None and self._legal(drawn, hand):
                self._broadcast_event("player_drew", {"player_index": player_idx, "playable": True})
                chosen = player.choose_card(hand, [drawn], top_card, self.active_color, state_view)
            else:
                # Public information leak: this player holds nothing playable on this colour/value
                self._broadcast_event("player_drew_no_play", {
                    "player_index": player_idx,
                    "active_color": self.active_color,
                    "top_value": top_card.value,
                })

        if chosen is not None:
            hand.remove(chosen)
            self.discard_pile.append(chosen)
            if chosen.is_wild():
                self.active_color = player.choose_color(hand, state_view)
            else:
                self.active_color = chosen.color

            step = 1
            target = self._next_player_index(1)
            penalty_target: Optional[int] = None
            penalty = 0
            if chosen.card_type in (CardType.DRAW_TWO, CardType.WILD_DRAW_FOUR, CardType.SKIP, CardType.REVERSE):
                self.stats.actions_played_per_player[player_idx] += 1

            if len(hand) > 0:
                if chosen.card_type == CardType.DRAW_TWO:
                    if self.allow_stacking:
                        self.pending_draw += 2
                    else:
                        penalty_target, penalty = target, 2
                        step = 2
                elif chosen.card_type == CardType.WILD_DRAW_FOUR:
                    if self.allow_stacking:
                        self.pending_draw += 4
                    else:
                        penalty_target, penalty = target, 4
                        step = 2
                elif chosen.card_type == CardType.SKIP:
                    step = 2
                elif chosen.card_type == CardType.REVERSE:
                    if self.num_players == 2:
                        step = 2
                    else:
                        self.direction *= -1

            if penalty_target is not None:
                self._give_penalty(penalty_target, penalty)

            self._broadcast_event("card_played", {
                "player_index": player_idx,
                "strategy": player.name,
                "card": chosen,
                "chosen_color": self.active_color,
                "cards_left": len(hand),
                "penalty_target": penalty_target,
                "penalty": penalty,
            })

            if len(hand) == 0:
                self.game_over = True
                self.stats.winner_index = player_idx
                self._finish_game()
                self._after_turn()
                return False

            self.current_player = self._next_player_index(step)
        else:
            self.current_player = self._next_player_index(1)

        self._after_turn()
        if self.stats.total_turns > MAX_TURNS and not self.game_over:
            self.game_over = True
            self.stats.winner_index = -1
            self._finish_game()
        return not self.game_over

    def _after_turn(self) -> None:
        self.stats.hand_size_trace.append([len(h) for h in self.hands])

    def _finish_game(self) -> None:
        for i in range(self.num_players):
            self.stats.final_hand_sizes[i] = len(self.hands[i])
            self.stats.final_hand_points[i] = sum(c.points for c in self.hands[i])

    def run(self) -> GameStats:
        self._init_game()
        while not self.game_over:
            self.play_turn()
        return self.stats
