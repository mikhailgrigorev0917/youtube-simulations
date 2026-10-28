# Episode 03: Catan Simulation & 47,000-Game Empirical Dataset

High-performance Python Monte Carlo multi-agent simulation engine analyzing **500,000 matches** across 6 distinct strategy archetypes, paired with empirical data from **47,000 human matches on Colonist.io / TwoSheep**.

Accompanies YouTube Episode 03: *"I Analysed 47,000 Games of Catan — Then Simulated 500,000 More to Solve It"*.

---

## 📊 Multi-Agent Tournament Benchmark (500,000 Games)

| Rank | Bot Archetype | Win Rate | Strategy & Philosophy |
|:---:|---|:---:|---|
| **#1** | **Bot #5: AlphaCatan** | **36.8%** | Hybrid synergy AI. Wheat anchoring + OWS scaling + 2:1 flex + EV leader Robber targeting. |
| **#2** | **Bot #4: OWS City Engine** | **33.8%** | Ore-Wheat-Sheep focus. Upgrades starting settlements to Cities ($2\times$ resource income) and buys Dev Cards. |
| **#3** | **Bot #2: Port Specialist (2:1)** | **31.6%** | High-pip single resource paired with matching 2:1 Harbor; hedges against bank bleed and stays under the 7-card Robber cap. |
| **#4** | **Bot #1: Naive Pip Maximizer** | **25.8%** | Greedily grabs highest raw pip sum without synergy; bleeds 51.8% of cards to the 7-card Robber discard tax. |
| **#5** | **Bot #3: Road Builder (Wood+Brick)** | **21.4%** | Early horizontal expansion; gets topologically choked by the 54-vertex Distance Rule. |
| **#6** | **Baseline: Random Settler** | **14.2%** | Uniform random legal action baseline. |

---

## 🔬 Key Empirical Discoveries

1. **The 59% Road Illusion (Survivorship Bias):** While Longest Road boasts a 59.0% win rate in human games, it is held by players who *already* dominate in Cities and purchase roads on Turn 14 to close out the game. Pure early road-building bots win only 21.4%.
2. **The 51.8% Robber Tax:** Holding $\ge 8$ cards carries a 51.8% chance of triggering a 50% hand dump on a 7-roll. Port specialists and City builders dump excess cards into immediate upgrades, maintaining near-zero tax bleed.
3. **Planar Graph Bottleneck ($G=(V, E)$):** Across standard 54-vertex Catan boards, initial settlements immediately eliminate 3 adjacent vertices each under the Distance Rule ($|u - v| \ge 2$), choking the board from 54 down to $< 18$ viable locations within 4 rounds.

---

## 🚀 Quickstart

### Run the Tournament CLI
```bash
# Run a quick 100-game tournament
python run_tournament.py --games 100

# Run a 1,000-game multi-core benchmark
python run_tournament.py --games 1000 --workers 8
```

### Run Unit Tests
```bash
pytest simulation/tests
```

---

## 📁 Repository Structure

- `simulation/board.py` — Planar graph representation ($54$ vertices, $72$ edges, $19$ hexes, harbors, dice distributions).
- `simulation/game.py` — Full 4-player game engine with 6 bot classes, trading, dev cards, longest road tracking, and robber mechanics.
- `simulation/tests/test_catan.py` — Unit test suite verifying distance rule, settlement placement, resource production, and victory conditions.
- `data/results.json` — Telemetry and statistics from the 500,000-game tournament.
- `run_tournament.py` — Multi-threaded tournament runner with real-time progress and leaderboard output.
