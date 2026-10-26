# Episode 02: I Simulated 1,000,000 Games of UNO

High-performance Python Monte Carlo simulation engine evaluating 6 distinct UNO algorithms across **1,000,000 simulated games** under both Official Mattel Rules and House Stacking Rules (`+2` on `+2`, `+4` on `+4`).

---

## Empirical Results: Win Rate vs 3 Casual Players

| **#1** | **Card Counter** | `31.82%` | `±0.37%` | Bayesian tracking of opponent color voids; forces dead colors. |
| **#2** | **Greedy Color** | `31.98%` | `±0.37%` | Plays dominant hand color; minimizes draw pile reliance. |
| **#3** | **Tactical Sniper** | `31.09%` | `±0.37%` | Holds action cards in reserve until an opponent calls UNO. |
| **#4** | **Point Minimizer** | `26.28%` | `±0.35%` | Prioritizes dumping high-point cards to reduce loss penalties. |
| **#5** | **Aggressive Attacker** | `26.67%` | `±0.35%` | Fires +2, +4, and Skips immediately in the opening turns. |
| **#6** | **Random Baseline** | `24.76%` | `±0.35%` | Baseline pure luck line (1 in 4 players = 25.0%). |

| Rank | Strategy | Win Rate | 95% CI | Philosophy |
|:---:|---|:---:|:---:|---|
| **#1** | **Card Counter** | `31.82%` | `±0.37%` | Bayesian tracking of opponent color voids; forces dead colors. |
| **#2** | **Greedy Color** | `31.98%` | `±0.37%` | Plays dominant hand color; minimizes draw pile reliance. |
| **#3** | **Tactical Sniper** | `31.09%` | `±0.37%` | Holds action cards in reserve until an opponent calls UNO. |
| **#4** | **Point Minimizer** | `26.28%` | `±0.35%` | Prioritizes dumping high-point cards to reduce loss penalties. |
| **#5** | **Aggressive Attacker** | `26.67%` | `±0.35%` | Fires +2, +4, and Skips immediately in the opening turns. |
| **#6** | **Random Baseline** | `24.76%` | `±0.35%` | Baseline pure luck line (1 in 4 players = 25.0%). |

---

## Repository Structure

- `simulation/card.py` — 108-card standard UNO deck, legality rules, point scoring.
- `simulation/game.py` — Full UNO state machine supporting Official and Stacking rules, public draw-void broadcasts.
- `simulation/strategies/` — 6 modular bot implementations (`BaseStrategy` interface):
  - `random_bot.py` (`Random`)
  - `greedy_color.py` (`GreedyColor`)
  - `aggressive_attacker.py` (`AggressiveAttacker`)
  - `tactical_sniper.py` (`TacticalSniper`)
  - `card_counter.py` (`CardCounter`)
  - `point_minimizer.py` (`PointMinimizer`)
- `simulation/tournament.py` — Multi-core `ProcessPoolExecutor` tournament runner with randomized seat permutation.
- `simulation/analyze.py` — Reproduces the full **1,000,000-game** telemetry in `data/results.json`.
- `simulation/tests/test_uno.py` — Unit test suite verifying deck composition, action rules, and game termination.

---

## Write Your Own Strategy

Inherit from `BaseStrategy` in `simulation/strategies/base.py`:

```python
from strategies.base import BaseStrategy, GameView
from card import Card, Color

class MyCustomBot(BaseStrategy):
    @property
    def name(self) -> str:
        return "MyCustomBot"

    def choose_card(self, hand: list[Card], playable: list[Card], view: GameView) -> Card:
        # Your custom logic here
        return playable[0]

    def choose_wild_color(self, hand: list[Card], view: GameView) -> Color:
        return Color.RED
```
