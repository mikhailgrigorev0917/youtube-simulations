#!/usr/bin/env python3
"""
Episode 06: Monopoly Markov Matrix Solver & Multi-Bot Tournament Runner.
"""

import argparse
import sys

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from simulation.markov_solver import build_transition_matrix
from simulation.tournament import run_tournament, calculate_group_roi

def main():
    parser = argparse.ArgumentParser(description="Monopoly Markov & Monte Carlo Simulation")
    parser.add_argument("--games", type=int, default=1000, help="Number of games to simulate")
    parser.add_argument("--markov-only", action="store_true", help="Only compute Markov stationary matrix")
    args = parser.parse_args()

    print("🎲 Computing 40x40 Monopoly Markov Transition Matrix...")
    P, pi_40 = build_transition_matrix()
    
    print("\n📊 Top Visited Squares:")
    top_indices = pi_40.argsort()[::-1][:5]
    from simulation.board_data import TILES
    for idx in top_indices:
        print(f"   Tile {idx:2d} ({TILES[idx]['name']:<20}): {pi_40[idx]*100:.2f}%")

    if not args.markov_only:
        print(f"\n🏆 Running {args.games:,} Multi-Bot Tournament matches...")
        res = run_tournament(n_games=args.games)
        print("\n✅ Tournament Results:")
        for bot, rate in res.get("win_rates", {}).items():
            print(f"   {bot:<35}: {rate:.1f}% Win Rate")

if __name__ == "__main__":
    main()
