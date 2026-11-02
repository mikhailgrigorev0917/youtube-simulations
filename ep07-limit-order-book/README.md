# Episode 07: How a Limit Order Book Actually Works

Mathematical breakdown of continuous double auctions, FIFO price-time priority queues, market sweep slippage, and high-frequency trading microstructure.

[Watch the full video on YouTube](https://youtu.be/B4aalVt3ZkE)

## Key Concepts

* **Continuous Double Auction:** The bid-ask ladder of resting limit intentions.
* **FIFO Matching Priority:** Orders within a price tick execute in order of arrival; priority is lost if an order size is modified.
* **VWAP Slippage:** Why market orders suffer exponential price degradation when sweeping through shallow order books.
* **The Arbitrage Race:** How nanosecond latency differences result in stale quote sniping by informed traders.

## Quickstart

```bash
cd ep07-limit-order-book
python analyze_orderbook.py
```
