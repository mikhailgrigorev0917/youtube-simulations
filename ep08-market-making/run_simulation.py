#!/usr/bin/env python3
"""
Episode 08: Market Making & Adverse Selection Simulator.
Runs the 100,000-trade 4-Player Market Microcosm Tournament.
"""

import argparse
import json
import sys

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from simulation.adverse_selection_sim import run_four_player_simulation

def main():
    parser = argparse.ArgumentParser(description="Market Making Adverse Selection Simulation")
    parser.add_argument("--events", type=int, default=100000, help="Number of trade events to simulate")
    parser.add_argument("--spread", type=float, default=0.10, help="Quoted total spread ($)")
    parser.add_argument("--retail-ratio", type=float, default=0.70, help="Ratio of retail noise flow")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    print(f"🚀 Running 4-Player Microstructure Tournament ({args.events:,} events)...")
    res = run_four_player_simulation(
        num_events=args.events,
        spread=args.spread,
        retail_ratio=args.retail_ratio,
        seed=args.seed,
    )

    naive = res["naive_maker_results"]
    smart = res["smart_maker_results"]
    k = res["key_takeaways"]

    print("\n" + "=" * 65)
    print("📊 SIMULATION TOURNAMENT RESULTS")
    print("=" * 65)
    print(f"Naive Maker (You):")
    print(f"   • Total Fills:               {naive['total_fills']:,}")
    print(f"   • Retail Share:              {naive['retail_fill_share_pct']:.1f}% (split with Smart Maker)")
    print(f"   • Informed Share:            {naive['informed_fill_share_pct']:.1f}% (100% asymmetric absorption!)")
    print(f"   • Profit from Retail:       +${naive['total_profit_from_retail']:,.2f}")
    print(f"   • Loss to Informed:         -${abs(naive['total_loss_to_informed']):,.2f}")
    print(f"   • Net Total PnL:             ${naive['net_total_pnl']:,.2f}")
    print(f"   • Realized Spread:           ${naive['avg_realized_spread_per_trade']:.4f} / trade")

    print(f"\nSmart Maker (HFT):")
    print(f"   • Total Fills:               {smart['total_fills']:,} (retail only)")
    print(f"   • Toxic Fills:               {smart['informed_fills']} (canceled on signal)")
    print(f"   • Net Profit:               +${smart['total_profit']:,.2f}")

    print("\n💡 Key Mathematical Verdict:")
    print(f"   • Quoted Half-Spread:       +${k['theoretical_expected_half_spread']:.2f}")
    print(f"   • Realized Spread:           ${k['naive_actual_realized_spread']:.4f}")
    print(f"   • Adverse Selection Tax:    -${k['adverse_selection_penalty']:.4f}")
    print("=" * 65)

if __name__ == "__main__":
    main()
