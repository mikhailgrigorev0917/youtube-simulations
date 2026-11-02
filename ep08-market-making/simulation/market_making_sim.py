"""
Simulation for Episode 08: Market Making & Adverse Selection.
Demonstrates why standing passively on the best bid/ask with a positive quoted spread
results in guaranteed bankruptcy due to adverse selection (the Winner's Curse).
"""

import numpy as np
import json
from pathlib import Path

def run_market_making_simulation(
    num_steps: int = 100_000,
    initial_price: float = 100.0,
    quoted_spread: float = 2.0,  # $2.00 spread ($1.00 half-spread)
    informed_ratio: float = 0.25, # 25% informed predators, 75% noise traders
    volatility: float = 0.5,
    seed: int = 42,
):
    np.random.seed(seed)
    half_spread = quoted_spread / 2.0
    
    # Fundamental fair value random walk
    innovations = np.random.normal(0, volatility, size=num_steps)
    fundamental_price = initial_price + np.cumsum(innovations)
    
    # Trader types: 0 = Noise Trader (uninformed), 1 = Informed Predator
    is_informed = (np.random.uniform(0, 1, size=num_steps) < informed_ratio)
    
    # Market maker quotes around their best estimate of current price
    # Naive maker quotes mid = fundamental_price[t] with constant half-spread
    # But informed trader knows innovation at t+1 or has private signal!
    
    noise_pnl = []
    informed_pnl = []
    all_pnl = []
    
    inventory = 0
    cash = 0.0
    equity_curve = []
    
    fills_noise = 0
    fills_informed = 0
    
    for t in range(num_steps - 1):
        mid = fundamental_price[t]
        bid = mid - half_spread
        ask = mid + half_spread
        
        future_price = fundamental_price[t + 1] # Next tick fair value
        price_delta = future_price - mid
        
        if not is_informed[t]:
            # Noise trader: 50% buy, 50% sell, regardless of price direction
            side = 1 if np.random.rand() < 0.5 else -1 # 1 = buy from maker (hit ask), -1 = sell to maker (hit bid)
            fills_noise += 1
            if side == 1:
                # Trader buys at ask (maker sells at ask)
                # Maker PnL relative to next fair value: (ask - future_price) = (+half_spread - price_delta)
                trade_pnl = ask - future_price
                cash += ask
                inventory -= 1
            else:
                # Trader sells at bid (maker buys at bid)
                # Maker PnL relative to next fair value: (future_price - bid) = (+half_spread + price_delta)
                trade_pnl = future_price - bid
                cash -= bid
                inventory += 1
            noise_pnl.append(trade_pnl)
            all_pnl.append(trade_pnl)
        else:
            # Informed trader: only trades if price_delta > half_spread (profitable to take)
            # They know fair value is moving!
            if price_delta > half_spread:
                # Informed buys at ask (maker sells at ask right before upward surge)
                side = 1
                fills_informed += 1
                trade_pnl = ask - future_price # Will be strongly NEGATIVE
                cash += ask
                inventory -= 1
                informed_pnl.append(trade_pnl)
                all_pnl.append(trade_pnl)
            elif price_delta < -half_spread:
                # Informed sells at bid (maker buys at bid right before downward plunge)
                side = -1
                fills_informed += 1
                trade_pnl = future_price - bid # Will be strongly NEGATIVE
                cash -= bid
                inventory += 1
                informed_pnl.append(trade_pnl)
                all_pnl.append(trade_pnl)
            else:
                # No informed trade (spread protects maker from small moves)
                pass
                
        # Mark to market equity
        current_equity = cash + inventory * fundamental_price[t]
        if t % 100 == 0:
            equity_curve.append(current_equity)

    noise_pnl = np.array(noise_pnl)
    informed_pnl = np.array(informed_pnl)
    all_pnl = np.array(all_pnl)
    
    results = {
        "num_trades": int(len(all_pnl)),
        "quoted_spread": quoted_spread,
        "half_spread": half_spread,
        "noise_fills": int(fills_noise),
        "informed_fills": int(fills_informed),
        "avg_pnl_per_trade_total": float(np.mean(all_pnl)),
        "avg_pnl_per_trade_noise": float(np.mean(noise_pnl)),
        "avg_pnl_per_trade_informed": float(np.mean(informed_pnl)),
        "realized_spread_total": float(np.mean(all_pnl)),
        "adverse_selection_component": float(half_spread - np.mean(all_pnl)),
        "final_equity": float(equity_curve[-1]),
        "total_noise_profit": float(np.sum(noise_pnl)),
        "total_informed_loss": float(np.sum(informed_pnl)),
    }
    
    return results

if __name__ == "__main__":
    res = run_market_making_simulation()
    out_dir = Path("episodes/ep08-market-making-adverse-selection/data")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "results.json", "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    print("Simulation completed:")
    print(json.dumps(res, indent=2))
