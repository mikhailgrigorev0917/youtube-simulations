#!/usr/bin/env python3
"""CLI Multi-Agent Tournament Runner for Episode 03: Catan Simulation.

Runs head-to-head matches between 6 distinct bot archetypes:
1. Random Settler (baseline)
2. Bot #1: Naive Pip Maximizer
3. Bot #2: Port Specialist (2:1)
4. Bot #3: Road Builder (Wood+Brick)
5. Bot #4: OWS City Engine (Ore-Wheat-Sheep)
6. Bot #5: AlphaCatan (Hybrid Synergy AI)

Usage:
    python run_tournament.py --games 1000
    python run_tournament.py --games 100 --workers 4
"""

from __future__ import annotations
import argparse
import concurrent.futures
import os
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add simulation folder to path
sys.path.insert(0, str(Path(__file__).resolve().parent / "simulation"))

from game import play_catan_game, BOT_LABELS

ALL_BOTS = [
    "random_settler",
    "naive_pip",
    "port_specialist",
    "road_builder",
    "ows_city_engine",
    "alpha_catan",
]

def simulate_single_match(seed: int) -> dict:
    rng = random.Random(seed)
    # Pick 4 distinct bot archetypes (or random permutation)
    active_strategies = rng.sample(ALL_BOTS, 4)
    res = play_catan_game(active_strategies, seed=seed)
    return {
        "participants": active_strategies,
        "winner": res["winnerStrategy"],
        "turns": res["turns"],
        "longest_road": res["longestRoadHolder"],
        "largest_army": res["largestArmyHolder"],
    }

def main():
    parser = argparse.ArgumentParser(description="Run Catan Multi-Agent Tournament")
    parser.add_argument("--games", type=int, default=500, help="Number of simulated games (default: 500)")
    parser.add_argument("--workers", type=int, default=os.cpu_count() or 4, help="CPU workers (default: all)")
    args = parser.parse_args()

    print("=" * 70)
    print("🎲 CATAN MULTI-AGENT MONTE CARLO TOURNAMENT")
    print(f"   Target Games: {args.games:,}")
    print(f"   CPU Workers:  {args.workers}")
    print("=" * 70)

    start_time = time.time()
    played_counts = defaultdict(int)
    win_counts = defaultdict(int)
    total_turns = 0

    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(simulate_single_match, seed=i + 1000) for i in range(args.games)]
        completed = 0
        for fut in concurrent.futures.as_completed(futures):
            res = fut.result()
            for bot in res["participants"]:
                played_counts[bot] += 1
            win_counts[res["winner"]] += 1
            total_turns += res["turns"]
            completed += 1
            if completed % max(1, args.games // 10) == 0 or completed == args.games:
                pct = completed / args.games * 100
                speed = completed / (time.time() - start_time + 0.001)
                print(f"   Progress: {completed:,}/{args.games:,} ({pct:.0f}%) — {speed:.1f} games/sec")

    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"🏆 TOURNAMENT FINAL LEADERBOARD ({args.games:,} Games in {elapsed:.1f}s)")
    print("=" * 70)
    print(f"{'Rank':<5} {'Bot Strategy':<35} {'Games':<8} {'Wins':<8} {'Win Rate':<10}")
    print("-" * 70)

    # Sort by Win Rate descending
    rank = 1
    sorted_bots = sorted(ALL_BOTS, key=lambda b: (win_counts[b] / max(1, played_counts[b])), reverse=True)
    for bot in sorted_bots:
        g = played_counts[bot]
        w = win_counts[bot]
        wr = (w / g * 100) if g > 0 else 0.0
        label = BOT_LABELS.get(bot, bot)
        print(f"#{rank:<4} {label:<35} {g:<8} {w:<8} {wr:>6.1f}%")
        rank += 1

    print("-" * 70)
    print(f"Average Match Length: {total_turns / args.games:.1f} turns")
    print("=" * 70)

if __name__ == "__main__":
    main()
