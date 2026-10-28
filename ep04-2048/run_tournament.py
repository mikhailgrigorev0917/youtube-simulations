#!/usr/bin/env python3
"""CLI Multi-Agent Tournament Runner for Episode 04: 2048 Simulation.

Benchmarks 5 distinct algorithms on 64-bit Bitboard LUT engine:
1. Uniform Random (Baseline)
2. Bot #2: Greedy Score Maximizer
3. Bot #3: Rigid Corner Dogma (Never Press UP)
4. Bot #4: 0-Ply Snake Monotonicity & Smoothness Heuristic
5. Bot #5: Expectimax Lookahead AI (Chance Nodes + Dynamic Pruning)

Usage:
    python run_tournament.py --games 100
    python run_tournament.py --bot expectimax --games 50 --depth 3
"""

from __future__ import annotations
import argparse
import concurrent.futures
import multiprocessing as mp
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add simulation folder to path
sys.path.insert(0, str(Path(__file__).resolve().parent / "simulation"))

from game import Game2048
from strategies import RandomBot, GreedyBot, CornerBot, HeuristicBot, ExpectimaxBot

BOT_NAMES = {
    "random": "Bot #1: Uniform Random",
    "greedy": "Bot #2: Greedy Maximizer",
    "corner": "Bot #3: Rigid Corner Dogma",
    "heuristic": "Bot #4: Snake Monotonicity",
    "expectimax": "Bot #5: Expectimax AI",
}

def play_match(args: tuple) -> dict:
    bot_id, seed, p4, depth = args
    if bot_id == "random":
        bot = RandomBot()
    elif bot_id == "greedy":
        bot = GreedyBot()
    elif bot_id == "corner":
        bot = CornerBot()
    elif bot_id == "heuristic":
        bot = HeuristicBot()
    elif bot_id == "expectimax":
        bot = ExpectimaxBot(max_depth=depth)
    else:
        raise ValueError(f"Unknown bot {bot_id}")

    game = Game2048(seed=seed, p4=p4)
    res = game.play(bot.get_move, bot_id=bot_id, record_history=False)
    return {
        "bot_id": bot_id,
        "score": res.score,
        "max_tile": res.max_tile,
        "moves": res.move_count,
        "reached_2048": (res.max_tile >= 2048),
    }

def main():
    parser = argparse.ArgumentParser(description="Run 2048 Strategy Tournament")
    parser.add_argument("--games", type=int, default=50, help="Games per bot (default: 50)")
    parser.add_argument("--bot", choices=["all", "random", "greedy", "corner", "heuristic", "expectimax"], default="all")
    parser.add_argument("--depth", type=int, default=2, help="Expectimax lookahead depth (default: 2)")
    parser.add_argument("--workers", type=int, default=os.cpu_count() or 4, help="CPU workers")
    args = parser.parse_args()

    bots_to_run = list(BOT_NAMES.keys()) if args.bot == "all" else [args.bot]
    total_matches = len(bots_to_run) * args.games

    print("=" * 70)
    print("🎮 2048 ALGORITHMIC SIMULATION TOURNAMENT")
    print(f"   Bots:         {', '.join(bots_to_run)}")
    print(f"   Games / Bot:  {args.games:,}")
    print(f"   Total Games:  {total_matches:,}")
    print(f"   Expectimax:   Depth {args.depth}")
    print(f"   CPU Workers:  {args.workers}")
    print("=" * 70)

    tasks = []
    for bot_id in bots_to_run:
        for i in range(args.games):
            tasks.append((bot_id, 10000 + i, 0.10, args.depth))

    start_time = time.time()
    results_by_bot = defaultdict(list)
    completed = 0

    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(play_match, t) for t in tasks]
        for fut in concurrent.futures.as_completed(futures):
            res = fut.result()
            results_by_bot[res["bot_id"]].append(res)
            completed += 1
            if completed % max(1, total_matches // 10) == 0 or completed == total_matches:
                speed = completed / (time.time() - start_time + 0.001)
                print(f"   Progress: {completed:,}/{total_matches:,} ({completed/total_matches*100:.0f}%) — {speed:.1f} games/sec")

    elapsed = time.time() - start_time
    print("\n" + "=" * 80)
    print(f"🏆 TOURNAMENT FINAL LEADERBOARD ({total_matches:,} Games in {elapsed:.1f}s)")
    print("=" * 80)
    print(f"{'Rank':<5} {'Algorithm':<28} {'Avg Score':<12} {'Max Tile':<12} {'Win Rate (≥2048)':<18}")
    print("-" * 80)

    # Sort by Average Score descending
    rank = 1
    sorted_bots = sorted(bots_to_run, key=lambda b: sum(r["score"] for r in results_by_bot[b]) / len(results_by_bot[b]), reverse=True)
    for bot_id in sorted_bots:
        items = results_by_bot[bot_id]
        avg_score = sum(r["score"] for r in items) / len(items)
        max_tile = max(r["max_tile"] for r in items)
        wins = sum(1 for r in items if r["reached_2048"])
        wr = wins / len(items) * 100
        print(f"#{rank:<4} {BOT_NAMES[bot_id]:<28} {avg_score:>9.0f}   {max_tile:>8}     {wr:>6.1f}%")
        rank += 1

    print("=" * 80)

if __name__ == "__main__":
    main()
