"""Unit tests for Monopoly simulation mathematical engine."""

import sys
from pathlib import Path

SIM_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SIM_DIR))

import pytest
import numpy as np
from board_data import TILES, COLOR_GROUPS
from markov_solver import build_transition_matrix, solve_monopoly_markov

def test_tile_count():
    assert len(TILES) == 40
    assert TILES[0]["name"] == "GO"
    assert TILES[10]["name"] == "Jail / Just Visiting"
    assert TILES[30]["name"] == "Go to Jail"
    assert TILES[39]["name"] == "Boardwalk"

def test_transition_matrix_stochastic():
    P, pi_40 = build_transition_matrix()
    assert P.shape == (120, 120)
    # Check that row sums of P are all 1.0 (stochastic matrix)
    row_sums = np.sum(P, axis=1)
    np.testing.assert_allclose(row_sums, 1.0, atol=1e-5)
    # Check that stationary distribution sums to 1.0
    assert abs(np.sum(pi_40) - 1.0) < 1e-5

def test_jail_is_highest_visited_tile():
    _, pi_40 = build_transition_matrix()
    # Jail (tile 10) must be the single highest probability tile on the board
    jail_prob = pi_40[10]
    for i in range(40):
        if i != 10:
            assert jail_prob > pi_40[i]
    assert jail_prob > 0.055 # At least 5.5%

def test_orange_dominates_dark_blue():
    _, pi_40 = build_transition_matrix()
    orange_prob = sum(pi_40[i] for i in COLOR_GROUPS["Orange"])
    dark_blue_prob = sum(pi_40[i] for i in COLOR_GROUPS["Dark Blue"])
    assert orange_prob > dark_blue_prob * 1.5 # Orange is far more visited than Dark Blue
