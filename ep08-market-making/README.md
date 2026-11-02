# Episode 08: Market Making & Adverse Selection Simulation

A 100,000-trade microstructure tournament proving why naive spread capture mathematically guarantees bankruptcy in the presence of informed flow (The Winner's Curse).

[Watch the full video on YouTube](https://youtu.be/nIxISlYutcg)

## The 4-Player Market Microcosm

1. **The Naive Maker (You):** Passively quotes best bid and ask, believing the spread is free passive income.
2. **The Smart Maker (HFT):** Quotes alongside you, but cancels orders within 200 nanoseconds upon detecting directional flow.
3. **The Retail Taker:** Uninformed noise flow (random DCA and liquidity demand).
4. **The Informed Predator:** Institutional sweepers and latency arbitrageurs with forward price signals.

## The Mathematical Trap

* **On Retail Trades:** You split volume with Smart Makers (~50/50), earning tiny pennies (+5¢).
* **On Toxic Trades:** Smart Makers vanish, leaving you to absorb 100% of the crash (-35¢).
* **Result:** While quoted spread is `+$0.05`, actual realized spread collapses to `-$0.13` per trade.

## Quickstart

```bash
cd ep08-market-making
python run_simulation.py --events 100000
```
