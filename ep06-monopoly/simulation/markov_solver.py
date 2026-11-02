"""Exact Markov Chain stationary solver for standard Monopoly."""

from __future__ import annotations
import numpy as np

try:
    from .board_data import TILES, COLOR_GROUPS
except ImportError:
    from board_data import TILES, COLOR_GROUPS

DICE_PROBS = {
    2: 1/36, 3: 2/36, 4: 3/36, 5: 4/36, 6: 5/36, 7: 6/36,
    8: 5/36, 9: 4/36, 10: 3/36, 11: 2/36, 12: 1/36
}
# Doubles probability: 1/36 each for 2, 4, 6, 8, 10, 12 (total 6/36 = 1/6)
DOUBLE_ROLLS = {2, 4, 6, 8, 10, 12}

def get_chance_destinations(tile: int) -> dict[int, float]:
    """16 cards:
    - 0: GO (1/16)
    - 24: Illinois Ave (1/16)
    - 11: St. Charles Place (1/16)
    - Nearest Utility: 12 or 28 (1/16)
    - Nearest Railroad: 5, 15, 25, 35 (2/16)
    - Go back 3 spaces: tile - 3 (1/16)
    - 10: Jail (1/16)
    - 39: Boardwalk (1/16)
    - 5: Reading Railroad (1/16)
    - Stay on current tile: 6/16
    """
    dest: dict[int, float] = {}
    def add(t: int, p: float):
        dest[t] = dest.get(t, 0.0) + p

    add(0, 1/16)
    add(24, 1/16)
    add(11, 1/16)
    
    # Nearest utility
    if tile == 7:
        add(12, 1/16)
    elif tile == 22:
        add(28, 1/16)
    else:  # tile == 36
        add(12, 1/16)

    # Nearest railroad (2 cards)
    if tile == 7:
        add(15, 2/16)
    elif tile == 22:
        add(25, 2/16)
    else:  # tile == 36
        add(5, 2/16)

    # Back 3 spaces
    back_tile = (tile - 3) % 40
    # Note: if back 3 lands on Community Chest (e.g. from 36 to 33), could draw CC, but we simplify to landing on 33
    add(back_tile, 1/16)

    add(10, 1/16) # Go to Jail
    add(39, 1/16) # Boardwalk
    add(5, 1/16)  # Reading Railroad
    add(tile, 6/16) # Non-movement cards
    return dest

def get_community_chest_destinations(tile: int) -> dict[int, float]:
    """16 cards:
    - 0: GO (1/16)
    - 10: Jail (1/16)
    - Stay: 14/16
    """
    return {
        0: 1/16,
        10: 1/16,
        tile: 14/16
    }

def build_transition_matrix() -> tuple[np.ndarray, np.ndarray]:
    """Builds a 120x120 transition matrix tracking (tile, consecutive_doubles).
    States: 0..39 for d=0, 40..79 for d=1, 80..119 for d=2.
    """
    N_STATES = 120
    P = np.zeros((N_STATES, N_STATES), dtype=np.float64)

    for state in range(N_STATES):
        tile = state % 40
        d_count = state // 40

        for roll in range(2, 13):
            prob = DICE_PROBS[roll]
            # Prob of rolling this sum as a double vs non-double
            if roll in DOUBLE_ROLLS:
                p_double = 1/36
                p_non_double = prob - p_double
            else:
                p_double = 0.0
                p_non_double = prob

            # Non-double branch (resets consecutive doubles to 0)
            if p_non_double > 0:
                raw_dest = (tile + roll) % 40
                resolved_dests = resolve_tile_landing(raw_dest)
                for final_dest, weight in resolved_dests.items():
                    target_state = final_dest  # d_count = 0
                    P[state, target_state] += p_non_double * weight

            # Double branch
            if p_double > 0:
                if d_count == 2:
                    # 3rd double -> Jail!
                    target_state = 10  # Jail, d_count = 0
                    P[state, target_state] += p_double
                else:
                    raw_dest = (tile + roll) % 40
                    resolved_dests = resolve_tile_landing(raw_dest)
                    for final_dest, weight in resolved_dests.items():
                        # If sent to Jail via Go to Jail or Card, doubles streak resets to 0
                        if final_dest == 10:
                            target_state = 10
                        else:
                            target_state = (d_count + 1) * 40 + final_dest
                        P[state, target_state] += p_double * weight

    # Solve stationary distribution: pi * P = pi  <=>  (P^T - I) * pi = 0
    eigvals, eigvecs = np.linalg.eig(P.T)
    # Find eigenvalue closest to 1.0
    idx = np.argmin(np.abs(eigvals - 1.0))
    pi_120 = np.real(eigvecs[:, idx])
    pi_120 = pi_120 / np.sum(pi_120)

    # Marginalize over doubles to get 40-tile stationary distribution
    pi_40 = np.zeros(40, dtype=np.float64)
    for i in range(120):
        pi_40[i % 40] += pi_120[i]

    return P, pi_40

def resolve_tile_landing(tile: int) -> dict[int, float]:
    """Resolves special tile actions (Go to Jail, Chance, Community Chest)."""
    if tile == 30:  # Go to Jail
        return {10: 1.0}
    elif tile in (7, 22, 36):  # Chance
        return get_chance_destinations(tile)
    elif tile in (2, 17, 33):  # Community Chest
        return get_community_chest_destinations(tile)
    else:
        return {tile: 1.0}

def solve_monopoly_markov() -> dict[str, float]:
    _, pi_40 = build_transition_matrix()
    res = {}
    for i in range(40):
        res[TILES[i]["name"]] = float(pi_40[i])
    return res
