"""
Finds real, reproducible highlight games for Episode 02 scenes.
Every highlight is a genuine simulated game (seed + lineup are stored in the scene JSON).
"""
from __future__ import annotations
import random
from typing import Any, Dict, List, Optional

from game import UnoGame
from tournament import STRATEGY_BY_NAME

STOPPERS = ("draw_two", "wild_draw_four", "skip")
DISPLAY = {
    "Random": "Random",
    "GreedyColor": "Greedy Color",
    "AggressiveAttacker": "Aggressor",
    "TacticalSniper": "Sniper",
    "CardCounter": "Card Counter",
    "PointMinimizer": "Point Minimizer",
}


def play(lineup: List[str], seed: int, stacking: bool) -> UnoGame:
    random.seed(seed)
    players = [STRATEGY_BY_NAME[n]() for n in lineup]
    g = UnoGame(players, allow_stacking=stacking, seed=seed, record_history=True)
    g.run()
    return g


def _pack(g: UnoGame, lineup: List[str], seed: int, stacking: bool, events: List[Dict[str, Any]], **extra) -> Dict[str, Any]:
    return {
        "seed": seed,
        "stacking": stacking,
        "lineup": lineup,
        "players": [{"name": DISPLAY[n]} for n in lineup],
        "events": events,
        "winner": g.stats.winner_index,
        **extra,
    }


def find_cold_open(max_seeds: int = 20000) -> Optional[Dict[str, Any]]:
    """Stacking game: a player on UNO (1 card) eats a stacked chain of >= 10 cards."""
    lineup = ["CardCounter", "AggressiveAttacker", "GreedyColor", "TacticalSniper"]
    best = None
    for seed in range(max_seeds):
        g = play(lineup, seed, True)
        ev = g.stats.history
        for i, e in enumerate(ev):
            if e["event"] == "stacked_penalty_taken" and e["count"] >= 10:
                p = e["player_index"]
                if ev[i - 1]["handSizes"][p] == 1 and (best is None or e["count"] > best[0]):
                    # chain start = first card_played that began the pending draw
                    j = i - 1
                    while j > 0 and ev[j]["pendingDraw"] > 0:
                        j -= 1
                    best = (e["count"], seed, max(0, j - 6), i + 3, i)
        if best and best[0] >= 12:
            break
    if not best:
        return None
    count, seed, a, b, hit = best
    g = play(lineup, seed, True)
    events = g.stats.history[a:b]
    return _pack(g, lineup, seed, True, events, hitIndex=hit - a, penalty=count)


def find_sniper(max_seeds: int = 5000) -> Optional[Dict[str, Any]]:
    """Official rules: Sniper hits a player who is on UNO with +2/+4, and later wins."""
    lineup = ["TacticalSniper", "Random", "GreedyColor", "Random"]
    for seed in range(max_seeds):
        g = play(lineup, seed, False)
        if g.stats.winner_index != 0:
            continue
        ev = g.stats.history
        for i, e in enumerate(ev):
            if (e["event"] == "card_played" and e["player_index"] == 0 and e["card"]["type"] in ("draw_two", "wild_draw_four")
                    and e["penalty_target"] is not None and ev[i - 1]["handSizes"][e["penalty_target"]] == 1):
                # sniper must have held this kind of card for a while (shows patience)
                a, b = max(0, i - 8), min(len(ev), i + 4)
                return _pack(g, lineup, seed, False, ev[a:b], hitIndex=i - a)
    return None


def find_aggressive_trap(max_seeds: int = 5000) -> Optional[Dict[str, Any]]:
    """Aggressor burns >= 2 stoppers early; later an opponent on UNO wins while Aggressor holds none."""
    lineup = ["AggressiveAttacker", "GreedyColor", "Random", "TacticalSniper"]
    for seed in range(max_seeds):
        g = play(lineup, seed, False)
        w = g.stats.winner_index
        if w <= 0:
            continue
        ev = g.stats.history
        early = [i for i, e in enumerate(ev[:18]) if e["event"] == "card_played" and e["player_index"] == 0 and e["card"]["type"] in STOPPERS]
        if len(early) < 2 or len(ev) < 45:
            continue
        # moment the winner reaches one card
        uno_i = next((i for i in range(len(ev) - 1, 0, -1) if ev[i]["handSizes"][w] == 1 and ev[i - 1]["handSizes"][w] != 1), None)
        if uno_i is None or uno_i < 25:
            continue
        ammo = [c for c in ev[uno_i]["hands"][0] if c["type"] in STOPPERS]
        if ammo or len(ev[uno_i]["hands"][0]) < 3:
            continue
        a_end = early[-1] + 3
        part1 = ev[0:a_end]
        part2 = ev[max(a_end, uno_i - 4):]
        return _pack(g, lineup, seed, False, part1 + part2, jumpIndex=len(part1),
                     turnsSkipped=part2[0]["turn"] - part1[-1]["turn"], unoIndex=len(part1) + (uno_i - max(a_end, uno_i - 4)))
    return None


def _voids_until(ev: List[Dict[str, Any]], idx: int, n: int) -> List[set]:
    v = [set() for _ in range(n)]
    for e in ev[: idx + 1]:
        p = e.get("player_index")
        if p is None:
            continue
        if e["event"] == "player_drew_no_play":
            v[p].add(e["active_color"])
        elif e["event"] == "card_played":
            v[p].discard(e["card"]["color"])
    return v


def find_card_counter(max_seeds: int = 8000) -> Optional[Dict[str, Any]]:
    """Counter switches colour with a Wild to a colour the next player is known to lack;
    that player is on <= 2 cards and is forced to draw and pass."""
    lineup = ["CardCounter", "Random", "Random", "GreedyColor"]
    for seed in range(max_seeds):
        g = play(lineup, seed, False)
        ev = g.stats.history
        for i, e in enumerate(ev[:-1]):
            if not (e["event"] == "card_played" and e["player_index"] == 0 and e["card"]["color"] == "wild"):
                continue
            nxt = ev[i + 1]
            t = nxt.get("player_index")
            if t is None or t == 0 or nxt["event"] != "player_drew_no_play":
                continue
            if ev[i - 1]["handSizes"][t] > 2:
                continue
            voids_before = _voids_until(ev, i - 1, 4)
            if e["chosen_color"] not in voids_before[t]:
                continue
            reveal = max(k for k in range(i) if ev[k]["event"] == "player_drew_no_play" and ev[k]["player_index"] == t
                         and ev[k]["active_color"] == e["chosen_color"])
            if i - reveal <= 22:
                a = max(0, reveal - 3)
                events = ev[a:i + 3]
                return _pack(g, lineup, seed, False, events, revealIndex=reveal - a, hitIndex=i - a,
                             target=t, color=e["chosen_color"])
            part1 = ev[max(0, reveal - 3):reveal + 3]
            part2 = ev[i - 5:i + 3]
            return _pack(g, lineup, seed, False, part1 + part2, revealIndex=3 if reveal >= 3 else reveal,
                         jumpIndex=len(part1), hitIndex=len(part1) + 5, target=t, color=e["chosen_color"])
    return None
