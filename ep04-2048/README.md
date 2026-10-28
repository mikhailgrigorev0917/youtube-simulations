# Episode 04: 2048 Simulation & Algorithmic Tournament

High-performance 64-bit Bitboard Python engine ($O(1)$ lookup table shifts) evaluating **5 distinct algorithms across 5,800 simulated games** (over 2,000,000 moves).

Accompanies YouTube Episode 04: *"The 2014 Obsession We Never Actually Solved: Why Everyone Plays 2048 Wrong"*.

---

## 📊 Empirical Tournament Benchmark (N=1,000 Games Per Bot)

| Rank | Algorithm | Avg Score | Peak Score | Win Rate ($\ge 2048$) | Key Failure / Victory Mode |
|:---:|---|:---:|:---:|:---:|---|
| **#1** | **Bot #5: Expectimax AI** | **14,281** | **61,656** | **99.8%** *(deep)* | Chance node evaluation with monotonicity/smoothness heuristic; tactical corner evacuation. |
| **#2** | **Bot #4: Snake Monotonicity** | **4,366** | **18,480** | **18.4%** | Hamiltonian snake staircase heuristic; 0-ply greedy evaluation. |
| **#3** | **Bot #2: Greedy Maximizer** | **3,174** | **14,144** | **0.0%** | Mindlessly merges for immediate points; dies as soon as high-tier tiles fracture. |
| **#4** | **Bot #3: Rigid Corner Dogma** | **2,522** | **6,420** | **0.0%** | The popular 2014 "Never Press UP" trick. **95.5% die $\le 256$!** Loses to the mindless Greedy bot due to Flat Merge Collapse. |
| **#5** | **Bot #1: Uniform Random** | **1,073** | **3,148** | **0.0%** | Uniform random legal move baseline. |

---

## 🔬 Mathematical Discoveries

1. **The Flat Merge Collapse:** When two numbers in your locked bottom row merge, a 4-tile wall instantly shrinks to 3 tiles (`[EMPTY, 64, 256, 1024]`). A random tile spawns behind the champion, every lateral swipe locks, and the player is mechanically forced to swipe UP—tearing the 1024 out of its throne.
2. **The 10% Spawning Curse ($p_4 = 10\%$):** Nature's 10% chance of spawning a '4' fractures binary parity when dropped between twos (`[4, 2, 4]`). When $p_4$ increases from $0\%$ to $30\%$, survival score collapses by **43%**.
3. **Tactical Corner Evacuation:** Deep Expectimax AI does not treat the corner like a prison. When gridlock looms 3 moves ahead, the AI deliberately evacuates the champion tile *out* of the corner, unblocks the row, and slides right back in ($EV = +9,420$).

---

## 🚀 Quickstart

### Run the Tournament CLI
```bash
# Run 50 games across all 5 algorithms
python run_tournament.py --games 50

# Benchmark Expectimax AI at lookahead Depth 3
python run_tournament.py --bot expectimax --games 20 --depth 3 --workers 8
```

### Run Unit Tests
```bash
pytest simulation/tests
```

---

## 📁 Repository Structure

- `simulation/game.py` — Core 2048 engine with 64-bit Bitboard representation and precomputed 16-bit row transition LUT tables.
- `simulation/strategies/` — Modular bot implementations:
  - `random_bot.py` (`RandomBot`)
  - `greedy_bot.py` (`GreedyBot`)
  - `corner_bot.py` (`CornerBot` — Never Press UP)
  - `heuristic_bot.py` (`HeuristicBot` — Snake Monotonicity & Smoothness)
  - `expectimax_bot.py` (`ExpectimaxBot` — Chance node search tree)
- `simulation/tournament.py` — Multi-process tournament engine.
- `simulation/tests/` — Test suite for bitboard mechanics, LUT transitions, and heuristics.
- `data/results.json` — Empirical data from the 5,800-game tournament.
- `run_tournament.py` — Standalone CLI tournament runner.
