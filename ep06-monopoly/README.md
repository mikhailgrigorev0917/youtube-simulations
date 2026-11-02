# Episode 06: Monopoly Simulation & Markov Analysis

Exact 40x40 Markov stationary probability matrix and 50,000-game Monte Carlo multi-bot tournament examining whether Boardwalk is positive expected value.

[Watch the full video on YouTube](https://youtu.be/ucVBjFOFMOU)

## Core Empirical Findings

1. **The Jail Attractor State:** Tile 10 (Jail) has a stationary probability of `6.20%` (1 in every 16 turns), making it the single most visited square on the board due to the 3-doubles rule, Chance/Community Chest cards, and Go to Jail square.
2. **The Orange Dominance:** Exiting Jail with rolls of 6, 8, or 9 lands players squarely on the Orange color group (`8.81%` visit frequency vs `4.82%` for Dark Blue Boardwalk).
3. **The 3-House Inflection:** Upgrading from 2 to 3 houses multiplies rent by `2.73x–2.75x`, providing the optimal capital breakeven horizon.
4. **The 32-House Bank Starvation:** With strictly 32 houses in the box (Official Hasbro Rule 14), locking 24 houses on Light Blue and Orange starves opponents of ever building hotels.

## Quickstart

```bash
cd ep06-monopoly
python run_tournament.py --markov-only
python run_tournament.py --games 5000
```
