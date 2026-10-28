#!/usr/bin/env python3
"""
Unit tests for Episode 03 Catan Simulation Engine (board topology, Distance Rule,
Longest Road DFS, and 4-player game loop).
"""
from __future__ import annotations
import sys
from pathlib import Path

SIM_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SIM_DIR))

from board import CatanBoard
from game import play_catan_game


def test_planar_graph_counts() -> None:
    board = CatanBoard(seed=42)
    assert len(board.hexes) == 19
    assert len(board.vertices) == 54
    assert len(board.edges) == 72
    # Exactly 1 desert tile with 0 pips
    deserts = [h for h in board.hexes if h.resource == "desert"]
    assert len(deserts) == 1
    assert deserts[0].pips == 0


def test_distance_rule_enforcement() -> None:
    board = CatanBoard(seed=7)
    occupied = {0: (0, 1)}
    assert not board.is_legal_settlement(0, occupied)
    for nb in board.vertices[0].neighbors:
        assert not board.is_legal_settlement(nb, occupied)
    blocked = board.blocked_vertices_mask(occupied)
    assert len(blocked) == 1 + len(board.vertices[0].neighbors)


def test_longest_road_dfs_and_cutoff() -> None:
    board = CatanBoard(seed=10)
    # Build a simple chain of 5 connected edges for player 0 along hex 0 perimeter
    h0_verts = board.hexes[0].vertices
    chain_edges = []
    for i in range(5):
        u, v = h0_verts[i], h0_verts[i + 1]
        eid = board.edge_by_pair[(min(u, v), max(u, v))]
        chain_edges.append(eid)

    edge_owners = {eid: 0 for eid in chain_edges}
    occupied = {}
    assert board.longest_road_for_player(0, edge_owners, occupied) == 5

    # Now place an opponent (player 1) settlement in the middle vertex h0_verts[2]
    occupied[h0_verts[2]] = (1, 1)
    assert board.longest_road_for_player(0, edge_owners, occupied) == 3


def test_full_game_simulation_and_event_export() -> None:
    lineup = ["alpha_catan", "ows_city_engine", "port_specialist", "road_builder"]
    res = play_catan_game(lineup, seed=123, record_events=True, max_turns=50)
    assert res["winner"] in (0, 1, 2, 3)
    assert 20 <= res["turn0BlockedVertices"] <= 32
    assert res["board"] is not None
    assert len(res["events"]) >= 8
