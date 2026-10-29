# Game Theory & Monte Carlo Simulations

Open-source simulation engines, evolutionary bot tournaments, and empirical datasets accompanying the YouTube quantitative game theory channel.

## Episodes

| Episode | Topic | Simulated Games | Folder | YouTube Video |
|:---:|---|:---:|:---:|:---:|
| **Ep 01** | **Battleship:** Evolutionary Strategy Tournament, Parity & Bayesian Heatmaps | `10,000,000` | [`ep01-battleship/`](./ep01-battleship/) | [Watch](https://youtu.be/N-Gf9bL14kU) |
| **Ep 02** | **UNO:** The Math of Betrayal, Color Flow & Bayesian Card Counting | `1,000,000` | [`ep02-uno/`](./ep02-uno/) | [Watch](https://youtu.be/cKz7uD14VpY) |
| **Ep 03** | **Catan:** 47,000 Human Matches & 500,000 Multi-Agent Simulations | `500,000` | [`ep03-catan/`](./ep03-catan/) | [Watch](https://youtu.be/yU_14mK12nQ) |
| **Ep 04** | **2048:** The 2014 Corner Lie, Parity Poisoning & Expectimax AI | `5,800` | [`ep04-2048/`](./ep04-2048/) | [Watch](https://youtu.be/VLQegGMLVSA) |
| **Ep 05** | **Scrabble:** 2M Turns, The 6-Tile Trap & Rack Leave AI | `2,005,498` | [`ep05-scrabble/`](./ep05-scrabble/) | [Watch](https://youtu.be/Ro8JRJaJnQo) |

---

## Quickstarts

### Episode 01 — Battleship Evolutionary Tournament
```bash
cd ep01-battleship
pytest simulation/tests
python run_tournament.py --games 1000 --no-plot --no-replays
```

### Episode 02 — UNO Simulator
```bash
cd ep02-uno
pytest simulation/tests/test_uno.py
python simulation/run_uno.py --games 10000
```

### Episode 03 — Catan Multi-Agent Tournament
```bash
cd ep03-catan
pytest simulation/tests
python run_tournament.py --games 500 --workers 8
```

### Episode 04 — 2048 Expectimax AI & Tournament
```bash
cd ep04-2048
pytest simulation/tests
python run_tournament.py --games 50
python run_tournament.py --bot expectimax --games 20 --depth 3
```

### Episode 05 — Scrabble 5-Bot Tournament
```bash
cd ep05-scrabble
pytest simulation/tests
python run_tournament.py --games 50
```

---

## License

MIT License — feel free to fork, test your own custom strategies, and submit pull requests!
