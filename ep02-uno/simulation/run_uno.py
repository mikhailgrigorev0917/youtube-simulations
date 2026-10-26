#!/usr/bin/env python3
"""
UNO Simulation & Tournament CLI
Episode 02: The Mathematics & Strategies of UNO
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

import io

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Add simulation dir to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from card import create_standard_deck
from game import UnoGame
from tournament import TournamentRunner
from scene_exporter import export_game_to_scene_spec
from strategies import (
    RandomStrategy,
    GreedyColorStrategy,
    AggressiveAttackerStrategy,
    TacticalSniperStrategy,
    CardCounterStrategy,
    PointMinimizerStrategy,
)


def run_single_demo_game():
    print("\n" + "=" * 60)
    print(" 🃏 UNO Simulation: 4-Player Battle Royale Demo")
    print("=" * 60)

    players = [
        RandomStrategy("Random-Bot"),
        GreedyColorStrategy("Greedy-Color"),
        TacticalSniperStrategy("Tactical-Sniper"),
        CardCounterStrategy("Card-Counter"),
    ]

    game = UnoGame(players=players, allow_stacking=True, seed=42, record_history=True)
    stats = game.run()

    print(f"Winner: {players[stats.winner_index].name} (Player {stats.winner_index})")
    print(f"Total turns: {stats.total_turns}")
    for i, p in enumerate(players):
        print(f"  [{i}] {p.name:<18} | Hand left: {stats.final_hand_sizes[i]:>2} cards | Penalties: {stats.final_hand_points[i]:>3} pts | Cards drawn: {stats.cards_drawn_per_player[i]:>2}")

    # Export scene
    scenes_dir = Path(__file__).resolve().parent.parent / "scenes"
    out_file = scenes_dir / "01-demo-battle.json"
    export_game_to_scene_spec(game, "anim-01-demo-battle", out_file)
    print(f"\n[+] Scene JSON exported to: {out_file.relative_to(Path.cwd())}")


def run_tournament(games: int = 10000, stacking: bool = False):
    print("\n" + "=" * 65)
    print(f" 🏆 Running UNO Tournament: {games:,} Games (Stacking={stacking})")
    print("=" * 65)

    strategies = [
        RandomStrategy,
        GreedyColorStrategy,
        AggressiveAttackerStrategy,
        TacticalSniperStrategy,
        CardCounterStrategy,
        PointMinimizerStrategy,
    ]

    runner = TournamentRunner(
        strategy_classes=strategies,
        games_per_matchup=games,
        allow_stacking=stacking
    )

    results = runner.run_4player_all_vs_all(total_games=games)

    print(f"\nCompleted {results['total_games']:,} games in {results['duration_seconds']}s")
    print(f"Average turns per game: {results['avg_turns_per_game']}")
    print("-" * 65)
    print(f"{'Rank':<5}{'Strategy':<24}{'Win Rate':<12}{'Wins':<10}{'Avg Penalty':<12}")
    print("-" * 65)

    for rank, (name, stats) in enumerate(results["leaderboard"], 1):
        print(f"#{rank:<4}{name:<24}{stats['win_rate_pct']:>6.2f}%    {stats['wins']:<10}{stats['avg_penalty_points']:>8.1f} pts")
    print("=" * 65)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UNO Game & Strategy Simulator")
    parser.add_argument("--games", type=int, default=5000, help="Number of tournament games")
    parser.add_argument("--stacking", action="store_true", help="Enable +2/+4 stacking rule")
    parser.add_argument("--demo", action="store_true", help="Run a single narrated demo game")

    args = parser.parse_args()

    if args.demo:
        run_single_demo_game()
    else:
        run_tournament(games=args.games, stacking=args.stacking)
