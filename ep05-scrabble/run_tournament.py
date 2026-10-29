#!/usr/bin/env python3
"""CLI Multi-Agent Tournament Runner for Episode 05: Scrabble Simulation.

Benchmarks 5 distinct algorithms sharing the exact same household vocabulary:
1. Bot #1: Long-Word Professor (Maximizes word length >= 5 tiles)
2. Bot #2: Naive Greedy Scorer (Maximizes immediate turn score)
3. Bot #3: Two-Letter Hook Specialist (Tetris-style parallel 2-letter overlaps)
4. Bot #4: Leave Equity & S/Blank Saver (Evaluates Score + Leave, preserves SATIREN stems)
5. Bot #5: Full 4-Rule Tactical AI (Hooks + Leave Equity + S/Blank Tax + 3W Lane Defense)

Usage:
    python run_tournament.py --games 100
    python run_tournament.py --games 500 --workers 4
"""

from __future__ import annotations
import argparse
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent / "simulation"))

from game import ScrabbleBoard, TileBag
from strategies import (
    GreedyBot,
    LeaveEquityBot,
    LongWordBot,
    MasterTacticalBot,
    TwoLetterHookBot,
)

BOTS = [
    ("long_word", LongWordBot()),
    ("greedy", GreedyBot()),
    ("two_letter", TwoLetterHookBot()),
    ("leave_equity", LeaveEquityBot()),
    ("tactical_ai", MasterTacticalBot()),
]


def play_game(bot_a_name: str, bot_a, bot_b_name: str, bot_b, seed: int) -> dict:
    """Simulate a full 2-player match between two bots."""
    rng = random.Random(seed)
    bag = TileBag(seed=seed)
    board = ScrabbleBoard()

    rack_a = bag.draw(7)
    rack_b = bag.draw(7)

    score_a = 0
    score_b = 0
    turns = 0
    max_turns = 24  # Standard ~12-14 turns per player

    while turns < max_turns and (rack_a or rack_b):
        turns += 1
        # Player A turn
        move_a = bot_a.choose_move(rack_a, board)
        if move_a:
            if move_a.is_exchange:
                to_swap = [ch for ch in rack_a if ch in "AEIOU"][:move_a.exchange_count]
                rack_a = [ch for ch in rack_a if ch not in to_swap] + bag.exchange(to_swap)
            else:
                score_a += move_a.score
                for ch in move_a.word:
                    if ch in rack_a:
                        rack_a.remove(ch)
                    elif '?' in rack_a:
                        rack_a.remove('?')
                rack_a.extend(bag.draw(7 - len(rack_a)))

        # Player B turn
        move_b = bot_b.choose_move(rack_b, board)
        if move_b:
            if move_b.is_exchange:
                to_swap = [ch for ch in rack_b if ch in "AEIOU"][:move_b.exchange_count]
                rack_b = [ch for ch in rack_b if ch not in to_swap] + bag.exchange(to_swap)
            else:
                score_b += move_b.score
                for ch in move_b.word:
                    if ch in rack_b:
                        rack_b.remove(ch)
                    elif '?' in rack_b:
                        rack_b.remove('?')
                rack_b.extend(bag.draw(7 - len(rack_b)))

    return {
        "bot_a": bot_a_name,
        "score_a": score_a,
        "bot_b": bot_b_name,
        "score_b": score_b,
        "winner": bot_a_name if score_a > score_b else (bot_b_name if score_b > score_a else "Tie"),
    }


def main():
    parser = argparse.ArgumentParser(description="Scrabble Multi-Agent Simulation Tournament")
    parser.add_argument("--games", type=int, default=50, help="Number of head-to-head games per matchup")
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("🎲 SCRABBLE TOURNAMENT: 5 BOTS (SAME 3,000-WORD HOUSEHOLD VOCABULARY)")
    print(f"🎯 Total Games Per Pair: {args.games}")
    print("=" * 70)

    t0 = time.time()
    scores: dict[str, list[int]] = defaultdict(list)
    wins: dict[str, int] = defaultdict(int)
    matches_count: dict[str, int] = defaultdict(int)

    bot_keys = [k for k, _ in BOTS]
    bot_dict = dict(BOTS)

    for i in range(len(bot_keys)):
        for j in range(i + 1, len(bot_keys)):
            k_a = bot_keys[i]
            k_b = bot_keys[j]
            bot_a = bot_dict[k_a]
            bot_b = bot_dict[k_b]

            print(f"⚔️  Matchup: {bot_a.name} vs {bot_b.name} ({args.games} games)...")
            for g in range(args.games):
                res = play_game(k_a, bot_a, k_b, bot_b, seed=g * 100 + i * 10 + j)
                scores[k_a].append(res["score_a"])
                scores[k_b].append(res["score_b"])
                matches_count[k_a] += 1
                matches_count[k_b] += 1

                if res["winner"] == k_a:
                    wins[k_a] += 1
                elif res["winner"] == k_b:
                    wins[k_b] += 1

    elapsed = time.time() - t0

    print("\n" + "=" * 80)
    print("🏆 FINAL TOURNAMENT LEADERBOARD (SORTED BY WIN RATE)")
    print("=" * 80)
    print(f"{'Bot Strategy':<38} | {'Avg Score':>10} | {'Win Rate':>10} | {'Total Matches':>14}")
    print("-" * 80)

    results_table = []
    for k, bot in BOTS:
        total_m = matches_count[k]
        w = wins[k]
        wr = (w / total_m * 100) if total_m > 0 else 0
        avg_s = sum(scores[k]) / len(scores[k]) if scores[k] else 0
        results_table.append((wr, bot.name, avg_s, w, total_m))

    results_table.sort(key=lambda x: x[0], reverse=True)
    for wr, name, avg_s, w, total_m in results_table:
        print(f"{name:<38} | {avg_s:>9.1f}  | {wr:>9.1f}% | {total_m:>14}")

    print("=" * 80)
    print(f"⏱️ Tournament finished in {elapsed:.2f}s\n")


if __name__ == "__main__":
    main()
