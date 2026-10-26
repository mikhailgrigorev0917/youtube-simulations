# Game Theory & Monte Carlo Simulations

Open-source simulation engines, bot strategies, and empirical datasets accompanying the YouTube episodes.

## Episodes

| Episode | Topic | Simulated Games | Folder |
|:---:|---|:---:|---|
| **Ep 01** | **Battleship:** Parity Hunting & Probability Density Heatmaps | `100,000+` | [`ep01-battleship/`](./ep01-battleship/) |
| **Ep 02** | **UNO:** The Math of Betrayal, Color Flow & Bayesian Card Counting | `1,000,000` | [`ep02-uno/`](./ep02-uno/) |

---

## Quickstart (Episode 02 — UNO Simulator)

```bash
cd ep02-uno

# Run unit tests
pytest simulation/tests/test_uno.py

# Run a fast tournament benchmark in terminal
python simulation/run_uno.py --games 10000

# Reproduce the full 1,000,000-game empirical dataset (writes data/results.json)
python simulation/analyze.py
```

## License

MIT License — feel free to fork, test your own custom strategies, and submit pull requests with new house rules!
