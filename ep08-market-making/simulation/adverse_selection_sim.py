"""
Simulation for Episode 08: Market Making & Adverse Selection.
Implements the 4-Player Market Microcosm:
1. Naive Maker (You): Stands passively on Best Bid/Ask, unaware of fast signals.
2. Smart Maker (HFT): Quotes alongside you, but cancels orders before toxic events.
3. Retail Taker: Uninformed noise trader (buys/sells randomly for liquidity/DCA).
4. Informed Taker: Algorithmic predator with forward price signal (CPI, arbitrage, liquidations).

Demonstrates:
- On Retail trades: Naive and Smart Makers compete (share volume ~50/50).
- On Informed trades: Smart Maker cancels, leaving Naive Maker to absorb 100% of the toxic blast.
- Net result: Realized spread is negative, Naive Maker bleeds out.
"""

import numpy as np
import json
from pathlib import Path

def run_four_player_simulation(
    num_events: int = 100_000,
    initial_price: float = 100.0,
    spread: float = 0.10,          # $0.10 total spread ($0.05 half-spread)
    retail_ratio: float = 0.70,     # 70% of incoming taker events are retail noise
    informed_ratio: float = 0.30,   # 30% are informed predatory sweeps
    informed_jump_mean: float = 0.35, # Informed moves average $0.35 (7x the half-spread!)
    seed: int = 42,
):
    np.random.seed(seed)
    half_spread = spread / 2.0
    
    current_mid = initial_price
    
    # Tracking for Naive Maker (You)
    naive_inventory = 0
    naive_cash = 0.0
    naive_retail_fills = 0
    naive_informed_fills = 0
    naive_retail_pnl = []
    naive_informed_pnl = []
    naive_equity_curve = []
    
    # Tracking for Smart Maker
    smart_inventory = 0
    smart_cash = 0.0
    smart_retail_fills = 0
    smart_informed_fills = 0
    smart_retail_pnl = []
    smart_informed_pnl = []
    smart_equity_curve = []
    
    for t in range(num_events):
        bid = current_mid - half_spread
        ask = current_mid + half_spread
        
        # Decide if this taker event is Retail or Informed
        is_retail = np.random.rand() < retail_ratio
        
        if is_retail:
            # ── Event A: Retail Taker Arrives (Uninformed Noise) ──
            # Random direction: 50% buy (hit ask), 50% sell (hit bid)
            is_buy = np.random.rand() < 0.5
            side = 1 if is_buy else -1
            
            # Post-trade price drift is zero-mean random noise
            drift = np.random.normal(0, 0.02)
            post_price = current_mid + drift
            
            # Both Naive and Smart Maker are resting at the quote.
            # Queue tie-breaker / volume share: 50% chance Naive gets filled, 50% Smart gets filled
            naive_gets_fill = np.random.rand() < 0.5
            
            if naive_gets_fill:
                naive_retail_fills += 1
                if is_buy:
                    # Retail buys at ask from Naive Maker
                    pnl = ask - post_price
                    naive_cash += ask
                    naive_inventory -= 1
                else:
                    # Retail sells at bid to Naive Maker
                    pnl = post_price - bid
                    naive_cash -= bid
                    naive_inventory += 1
                naive_retail_pnl.append(pnl)
            else:
                smart_retail_fills += 1
                if is_buy:
                    pnl = ask - post_price
                    smart_cash += ask
                    smart_inventory -= 1
                else:
                    pnl = post_price - bid
                    smart_cash -= bid
                    smart_inventory += 1
                smart_retail_pnl.append(pnl)
                
            current_mid = post_price
            
        else:
            # ── Event B: Informed Taker Arrives (Directional Signal) ──
            # Signal: price is about to jump violently!
            direction = 1 if np.random.rand() < 0.5 else -1 # 1 = upward surge, -1 = downward crash
            jump_size = np.random.exponential(informed_jump_mean) + half_spread
            future_mid = current_mid + direction * jump_size
            
            # Smart Maker sees the signal (or gets faster cancellation via microwave/co-lo):
            # Smart Maker cancels their resting quote 100% of the time!
            # Naive Maker remains sitting on the quote unaware.
            
            # Informed trader executes against the remaining quote:
            naive_informed_fills += 1
            if direction == 1:
                # Market is jumping up! Informed buys from Naive at old Ask.
                pnl = ask - future_mid # Strongly NEGATIVE
                naive_cash += ask
                naive_inventory -= 1
            else:
                # Market is crashing down! Informed sells to Naive at old Bid.
                pnl = future_mid - bid # Strongly NEGATIVE
                naive_cash -= bid
                naive_inventory += 1
            naive_informed_pnl.append(pnl)
            
            # Smart Maker had cancelled -> 0 fills, 0 loss!
            
            current_mid = future_mid

        if t % 500 == 0:
            naive_equity_curve.append(naive_cash + naive_inventory * current_mid)
            smart_equity_curve.append(smart_cash + smart_inventory * current_mid)

    # Compute aggregate statistics
    naive_retail_pnl = np.array(naive_retail_pnl)
    naive_informed_pnl = np.array(naive_informed_pnl)
    all_naive_pnl = np.concatenate([naive_retail_pnl, naive_informed_pnl])
    
    smart_retail_pnl = np.array(smart_retail_pnl) if len(smart_retail_pnl) > 0 else np.array([0.0])
    
    results = {
        "simulation_parameters": {
            "num_events": num_events,
            "quoted_spread": spread,
            "half_spread": half_spread,
            "retail_ratio_pct": retail_ratio * 100,
            "informed_ratio_pct": informed_ratio * 100,
            "avg_informed_jump": informed_jump_mean,
        },
        "naive_maker_results": {
            "total_fills": int(len(all_naive_pnl)),
            "retail_fills": int(naive_retail_fills),
            "informed_fills": int(naive_informed_fills),
            "retail_fill_share_pct": float(naive_retail_fills / (naive_retail_fills + smart_retail_fills) * 100),
            "informed_fill_share_pct": 100.0, # Absorbed 100% of all informed trades!
            "total_profit_from_retail": float(np.sum(naive_retail_pnl)),
            "avg_profit_per_retail_fill": float(np.mean(naive_retail_pnl)),
            "total_loss_to_informed": float(np.sum(naive_informed_pnl)),
            "avg_loss_per_informed_fill": float(np.mean(naive_informed_pnl)),
            "net_total_pnl": float(np.sum(all_naive_pnl)),
            "avg_realized_spread_per_trade": float(np.mean(all_naive_pnl)),
            "final_equity": float(naive_equity_curve[-1]),
        },
        "smart_maker_results": {
            "total_fills": int(smart_retail_fills),
            "retail_fills": int(smart_retail_fills),
            "informed_fills": 0,
            "total_profit": float(np.sum(smart_retail_pnl)),
            "avg_profit_per_fill": float(np.mean(smart_retail_pnl)),
            "final_equity": float(smart_equity_curve[-1]),
        },
        "key_takeaways": {
            "theoretical_expected_half_spread": half_spread,
            "naive_actual_realized_spread": float(np.mean(all_naive_pnl)),
            "adverse_selection_penalty": float(half_spread - np.mean(all_naive_pnl)),
        }
    }
    
    return results

if __name__ == "__main__":
    res = run_four_player_simulation()
    out_dir = Path("episodes/ep08-market-making-adverse-selection/data")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "results.json", "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    print("Simulation completed successfully. Results:")
    print(json.dumps(res, indent=2))
