#!/usr/bin/env python3
"""
Episode 02 — data collection for the script.

Runs every experiment the script quotes and writes ONE source of truth:
    episodes/ep02-uno-simulation/data/results.json

Usage:
    python episodes/ep02-uno-simulation/simulation/analyze.py            # full run
    python episodes/ep02-uno-simulation/simulation/analyze.py --quick    # smoke test
"""
from __future__ import annotations
import argparse
import io
import json
import random
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))

from card import CardType  # noqa: E402
from game import UnoGame  # noqa: E402
from tournament import STRATEGY_BY_NAME, run_games, random_lineups, summarize  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "data" / "results.json"
NAMES = list(STRATEGY_BY_NAME)
ACTION_TYPES = (CardType.DRAW_TWO, CardType.WILD_DRAW_FOUR, CardType.SKIP)


def vs_three_randoms(n: int, stacking: bool, seed: int) -> dict:
    rng = random.Random(seed)
    out = {}
    for name in NAMES:
        lineups, hero_seats = [], []
        for _ in range(n):
            seats = ["Random"] * 4
            hero = rng.randrange(4)
            seats[hero] = name
            lineups.append(seats)
            hero_seats.append(hero)
        res = run_games(lineups, stacking=stacking, base_seed=seed * 1_000_000)
        # Count only wins by the hero seat (matters when name == "Random")
        wins = sum(1 for r, s in zip(res, hero_seats) if r["winner"] == s)
        p = wins / n
        out[name] = {"games": n, "win_rate_pct": round(100 * p, 2),
                     "ci95_pct": round(196 * (p * (1 - p) / n) ** 0.5, 2)}
    return out


def seat_advantage(n: int) -> dict:
    res = run_games([["Random"] * 4 for _ in range(n)], base_seed=7_000_000)
    c = Counter(r["winner"] for r in res)
    return {f"seat_{i}": round(100 * c[i] / n, 2) for i in range(4)}


def penalty_stats(results: list) -> dict:
    pens = [p for r in results for p in r["penalties"]]
    hist = Counter(pens)
    turns = [r["turns"] for r in results]
    return {
        "hits": len(pens),
        "mean": round(statistics.mean(pens), 2) if pens else 0,
        "variance": round(statistics.pvariance(pens), 2) if pens else 0,
        "max": max(pens) if pens else 0,
        "histogram": {str(k): hist[k] for k in sorted(hist)},
        "share_8_plus_pct": round(100 * sum(v for k, v in hist.items() if k >= 8) / max(1, len(pens)), 2),
        "games_with_8_plus_pct": round(100 * sum(1 for r in results if any(p >= 8 for p in r["penalties"])) / len(results), 2),
        "avg_turns": round(statistics.mean(turns), 1),
        "turns_stdev": round(statistics.pstdev(turns), 1),
    }


def instrumented(name: str, n: int, seed: int) -> dict:
    """Seat 0 = `name`, seats 1-3 = Random.
    Tracks (a) own hand size per round, (b) action cards held when an opponent is on UNO."""
    rounds = 30
    hand_sum = [0.0] * rounds
    ammo_at_threat, threat_turns, blocked = 0, 0, 0
    for g in range(n):
        random.seed(seed + g)
        players = [STRATEGY_BY_NAME[name]()] + [STRATEGY_BY_NAME["Random"]() for _ in range(3)]
        game = UnoGame(players, seed=seed + g)
        game._init_game()
        own_turn = 0
        last_size = 7
        while not game.game_over:
            if game.current_player == 0:
                opp_on_uno = any(len(game.hands[i]) == 1 for i in range(1, 4))
                if opp_on_uno:
                    threat_turns += 1
                    ammo = sum(1 for c in game.hands[0] if c.card_type in ACTION_TYPES)
                    ammo_at_threat += ammo
                    if ammo > 0:
                        blocked += 1
            was_turn = game.current_player == 0
            game.play_turn()
            if was_turn:
                if own_turn < rounds:
                    last_size = len(game.hands[0])
                    hand_sum[own_turn] += last_size
                own_turn += 1
        for r in range(own_turn, rounds):  # game ended: carry final size forward
            hand_sum[r] += len(game.hands[0])
    return {
        "avg_hand_by_own_turn": [round(s / n, 2) for s in hand_sum],
        "avg_action_cards_when_opponent_on_uno": round(ammo_at_threat / max(1, threat_turns), 2),
        "pct_turns_with_ammo_when_opponent_on_uno": round(100 * blocked / max(1, threat_turns), 1),
    }


def _instrumented_worker(args: tuple[str, int, int]) -> tuple[str, dict]:
    name, n, seed = args
    return name, instrumented(name, n, seed)


def main() -> None:
    from concurrent.futures import ProcessPoolExecutor
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    # 3 * N + 6 * N_VS + 5 * N_INST = 600,000 + 360,000 + 40,000 = 1,000,000 games
    N = 1000 if args.quick else 200000
    N_VS = 500 if args.quick else 60000
    N_INST = 200 if args.quick else 8000

    t0 = time.time()
    data: dict = {"meta": {"rules": "Official Mattel rules, Wild Draw Four restricted (no challenges), 4 players, 7-card deal"}}

    print(f"1/6 seat advantage (4x Random, {N:,} games)…", flush=True)
    data["seat_advantage_4_random"] = seat_advantage(N)

    print(f"2/6 each strategy vs 3 Random bots (6 x {N_VS:,} games)…", flush=True)
    data["vs_three_randoms"] = vs_three_randoms(N_VS, stacking=False, seed=11)

    print(f"3/6 6-strategy tournament (official, {N:,} games)…", flush=True)
    off = run_games(random_lineups(NAMES, N, seed=21), stacking=False, base_seed=21_000_000)
    data["tournament_official"] = {"games": N, "leaderboard": summarize(off)}

    print(f"4/6 6-strategy tournament (stacking, {N:,} games)…", flush=True)
    stk = run_games(random_lineups(NAMES, N, seed=31), stacking=True, base_seed=31_000_000)
    data["tournament_stacking"] = {"games": N, "leaderboard": summarize(stk)}

    print("5/6 penalty distributions…", flush=True)
    data["penalties_official"] = penalty_stats(off)
    data["penalties_stacking"] = penalty_stats(stk)

    inst_names = ["Random", "AggressiveAttacker", "GreedyColor", "TacticalSniper", "CardCounter"]
    print(f"6/6 instrumented hand trajectories (5 x {N_INST:,} games)…", flush=True)
    with ProcessPoolExecutor(max_workers=len(inst_names)) as ex:
        pairs = list(ex.map(_instrumented_worker, [(nm, N_INST, 41_000_000) for nm in inst_names]))
    data["instrumented_vs_randoms"] = dict(pairs)

    data["meta"]["total_games"] = N + N_VS * len(NAMES) + 2 * N + 5 * N_INST
    data["meta"]["runtime_s"] = round(time.time() - t0, 1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(json.dumps(data, indent=2))
    print(f"\nSaved → {OUT}")


if __name__ == "__main__":
    main()
