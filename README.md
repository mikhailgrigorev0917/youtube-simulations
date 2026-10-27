# Game Theory & Monte Carlo Simulations

Open-source simulation engines, evolutionary bot tournaments, and empirical datasets accompanying the YouTube episodes.

## Episodes

| Episode | Topic | Simulated Games | Folder |
|:---:|---|:---:|---|
| **Ep 01** | **Battleship:** Evolutionary Strategy Tournament, Parity & Bayesian Heatmaps | `10,000,000` | [`ep01-battleship/`](./ep01-battleship/) |
| **Ep 02** | **UNO:** The Math of Betrayal, Color Flow & Bayesian Card Counting | `1,000,000` | [`ep02-uno/`](./ep02-uno/) |

---

## Quickstart (Episode 01 — Battleship Evolutionary Tournament)

```bash
cd ep01-battleship

# Run unit tests (engine, halo rule, placement & shooting strategies)
pytest simulation/tests

# List all registered offensive & defensive strategies
python run_tournament.py --list

# Run the full head-to-head evolutionary tournament
python run_tournament.py --games 1000 --no-plot --no-replays
```

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

MIT License — feel free to fork, test your own custom strategies, and submit pull requests!
