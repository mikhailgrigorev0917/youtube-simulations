# Episode 01: I Simulated 10,000,000 Games of Battleship — The Evolutionary Tournament

High-performance Python Monte Carlo simulation engine and multi-core tournament runner evaluating **6 Defensive Placement Strategies** against **7 Offensive Shooting Algorithms** under strict classical Battleship rules (`10×10` grid, fleet of `1×4, 2×3, 3×2, 4×1` = `20 ship cells`, no touching even diagonally).

---

## Grand Final 5×5 Evolved Championship Matrix (Mean Shots to Sink All Ships)

*Lower shots = faster kill for Offense; Higher shots = longer survival for Defense.*

| Defense \ Offense | `anti_border` | `anti_cluster` | `dynamic_stride` | `parity_hunt` | `probability_density` | **Defense Avg** |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **`border`** (Border Hugging) | **`35.3`** ⚡ | `66.9` | `62.4` | `63.1` | **`69.4`** 🛡️ | `59.4` |
| **`cluster`** (Corner Cluster) | `64.7` | **`52.6`** ⚡ | `60.2` | `59.7` | `61.0` | **`59.6` (#1 Def)** |
| **`anti_probability`** (Cold Ring) | `59.4` | `61.6` | `56.4` | `57.3` | `59.4` | **`58.8` (#2 Def)** |
| **`random`** (Random Placement) | `60.5` | `57.3` | `55.1` | `57.6` | **`52.9`** | `56.7` |
| **`stealth_submarines`** (Decoy + Subs) | `62.4` | `57.5` | **`54.5`** | `56.2` | `54.7` | `57.1` |
| **Offense Avg** | `56.5`* | `59.2` | **`57.7` (#1 Consistent)** | `58.8` | `59.5` | |

> **Key Evolutionary Takeaway**:
> - **The Trap of Extreme Gimmicks**: Hiding all ships along the outer walls (`border`) fools center-biased Bayesian heatmaps (`69.4` shots), but triggers a direct counter-strategy (`anti_border`) that sweeps the perimeter first and obliterates the fleet in **`35.3` shots**!
> - **Convergence to Balanced Mastery**: Across all evolved defenses, **Adaptive Dynamic Stride (`dynamic_stride`, `57.7` avg)** and **Checkerboard Parity (`parity_hunt`, `58.8` avg)** never get trapped by borders, clusters, or cold rings. On defense, **Corner Cluster (`59.6` avg)** and **Anti-Probability Cold Ring (`58.8` avg)** survive the longest across the entire gauntlet.

---

## Registered Strategies

### Defensive Placement Strategies (`simulation/strategies/placement/`)
1. `random` — Unbiased random legal placement (baseline).
2. `uniform` — Maximizes pairwise Euclidean distance between ships; centered ships leak 12 Halo cells when sunk.
3. `border` — Hugs the outer edges (`row/col in {0, 9}`), clipping 50% of the Halo off the board (leaking only 7 cells vs 12) and dodging center heatmaps.
4. `cluster` — Packs ships tightly into a single quadrant so Halos overlap and 70% of the ocean remains empty water.
5. `anti_probability` — Places multi-cell ships in the "Cold Ring" (`1–2 cells` off the wall), dodging both perimeter sweeps and center heatmap peaks.
6. `stealth_submarines` — Uses capital ships (`4, 3`) near the edges as decoys while scattering `1×1` submarines deep in interior pockets.

### Offensive Shooting Strategies (`simulation/strategies/shooting/`)
1. `random` — Blind random firing without Halo marking (`95.5` avg shots).
2. `hunt_target` — Random hunt + orthogonal target mode + 8-neighbor diagonal Halo exclusion (`58.2` shots vs Random).
3. `parity_hunt` — Checkerboard parity invariant `(r + c) mod L_min == 0` (`56.8` shots vs Uniform).
4. `probability_density` — Combinatorial Bayesian probability density heatmap over all valid remaining ship placements (`52.9` shots vs Random).
5. `anti_border` — Iteration 1 counter-strategy: sweeps the outer perimeter ring first (`35.3` shots vs Border).
6. `anti_cluster` — Iteration 2 counter-strategy: probes all 4 quadrants evenly and locks onto any sector registering 2+ hits (`52.6` shots vs Cluster).
7. `dynamic_stride` — Iteration 2 champion: dynamically adapts parity grid stride `L_max = 4 -> 3 -> 2` combined with Bayesian probability tie-breaking (`54.5` shots vs Stealth Submarines).

---

## Quickstart

```bash
# 1. Run all unit tests
pytest simulation/tests

# 2. List all strategies
python run_tournament.py --list

# 3. Run a custom tournament in terminal
python run_tournament.py --games 500 --placements border,cluster,anti_probability,random,stealth_submarines --shooters anti_border,anti_cluster,dynamic_stride,parity_hunt,probability_density --no-plot --no-replays
```

---

## Write Your Own Strategy

Register a new shooting or placement strategy in `simulation/strategies/`:

```python
import random
from simulation.core.models import Coordinate, GameConfig, ShotResult
from simulation.strategies.base import BaseShootingStrategy, register_shooting_strategy

@register_shooting_strategy
class MyCustomShooter(BaseShootingStrategy):
    name = "my_custom_shooter"
    description = "Custom hunting algorithm"

    def initialize(self, config: GameConfig, rng: random.Random) -> None:
        super().initialize(config, rng)

    def next_shot(self) -> Coordinate:
        available = list(self.available_cells)
        return self.rng.choice(available)

    def record_result(self, coord: Coordinate, result: ShotResult, sunk_ship=None) -> None:
        super().record_result(coord, result, sunk_ship)
```
