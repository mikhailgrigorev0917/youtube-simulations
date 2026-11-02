#!/usr/bin/env python3
"""
Episode 07: Limit Order Book & Market Sweep Slippage Analyzer.
Computes VWAP execution, depth ladders, and market impact across varying order sizes.
"""

import json
from pathlib import Path
import sys

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA_FILE = Path(__file__).resolve().parent / "data" / "binance_btcusdt_orderbook.json"

def analyze_orderbook():
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    bids = data["bids"]
    asks = data["asks"]

    best_bid = float(bids[0][0])
    best_ask = float(asks[0][0])
    spread = best_ask - best_bid
    mid_price = (best_bid + best_ask) / 2.0

    print("=" * 60)
    print("📖 BINANCE BTC/USDT L2 ORDER BOOK SNAPSHOT")
    print("=" * 60)
    print(f"Best Bid:   ${best_bid:,.2f}")
    print(f"Best Ask:   ${best_ask:,.2f}")
    print(f"Spread:     ${spread:.2f} ({spread / mid_price * 10000:.2f} bps)")
    print(f"Mid Price:  ${mid_price:,.2f}")

    # Sweep analysis on Ask side for a Buy Market Order
    test_sizes_usd = [10_000, 50_000, 250_000, 1_000_000]
    print("\n💥 MARKET SWEEP IMPACT (TAKER BUY SLIPPAGE):")
    for target_usd in test_sizes_usd:
        accum_usd = 0.0
        accum_btc = 0.0
        levels_consumed = 0
        
        for level in asks:
            p = float(level[0])
            qty = float(level[1])
            level_usd = p * qty
            levels_consumed += 1
            if accum_usd + level_usd >= target_usd:
                needed_usd = target_usd - accum_usd
                needed_btc = needed_usd / p
                accum_btc += needed_btc
                accum_usd += needed_usd
                break
            else:
                accum_usd += level_usd
                accum_btc += qty
                
        vwap = accum_usd / accum_btc if accum_btc > 0 else best_ask
        slippage_bps = (vwap - best_ask) / best_ask * 10000
        print(f"   • ${target_usd:>9,}: VWAP ${vwap:,.2f} | Slippage: +{slippage_bps:>5.2f} bps | Consumed {levels_consumed} levels")

if __name__ == "__main__":
    analyze_orderbook()
