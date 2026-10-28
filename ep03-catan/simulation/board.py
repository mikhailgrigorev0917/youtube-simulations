#!/usr/bin/env python3
"""
Exact 19-Hex Catan Board & Planar Graph G = (V, E) Geometry.
- 19 Hexes in axial coordinates (q, r)
- 54 Vertices (intersections where up to 3 hexes meet)
- 72 Edges (road segments connecting adjacent vertices)
- 9 Harbors (four 3:1 generic ports + five 2:1 specialized resource ports)
- Distance Rule enforcement & DFS Longest Road calculation
"""
from __future__ import annotations
import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

RESOURCES = ("wood", "brick", "sheep", "wheat", "ore")

STANDARD_TILE_POOL = (
    ["wood"] * 4
    + ["sheep"] * 4
    + ["wheat"] * 4
    + ["brick"] * 3
    + ["ore"] * 3
    + ["desert"] * 1
)

STANDARD_NUMBER_TOKENS = [2, 3, 3, 4, 4, 5, 5, 6, 6, 8, 8, 9, 9, 10, 10, 11, 11, 12]

PIP_MAP: Dict[int, int] = {
    2: 1,
    3: 2,
    4: 3,
    5: 4,
    6: 5,
    7: 0,
    8: 5,
    9: 4,
    10: 3,
    11: 2,
    12: 1,
    0: 0,
}

# Axial coordinates (q, r) for the 19-hex Catan island (radius 2 hexagon)
HEX_AXIAL_COORDS: List[Tuple[int, int]] = [
    (q, r)
    for r in range(-2, 3)
    for q in range(-2, 3)
    if abs(q + r) <= 2
]


@dataclass
class HexTile:
    id: int
    q: int
    r: int
    x: float
    y: float
    resource: str
    number: int
    pips: int
    vertices: List[int] = field(default_factory=list)


@dataclass
class VertexNode:
    id: int
    x: float
    y: float
    hex_ids: List[int] = field(default_factory=list)
    neighbors: List[int] = field(default_factory=list)
    edges: List[int] = field(default_factory=list)
    port: Optional[str] = None  # "3:1" or "2:1_wood", "2:1_brick", "2:1_sheep", "2:1_wheat", "2:1_ore"


@dataclass
class EdgeSegment:
    id: int
    u: int
    v: int


class CatanBoard:
    """
    Constructs the canonical 19-hex, 54-vertex, 72-edge Catan planar graph.
    Uses pointy-top hexagons with unit radius R = 1.0 in normalized board space.
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        self.rng = random.Random(seed)
        self.hexes: List[HexTile] = []
        self.vertices: List[VertexNode] = []
        self.edges: List[EdgeSegment] = []
        self.edge_by_pair: Dict[Tuple[int, int], int] = {}
        self.robber_hex: int = 0
        self._build_topology()
        self.randomize_resources()

    def _build_topology(self) -> None:
        sqrt3 = math.sqrt(3.0)
        vertex_lookup: Dict[Tuple[int, int], int] = {}

        def get_or_create_vertex(vx: float, vy: float) -> int:
            # Quantize to integer grid (thousandths) to deduplicate shared corners of adjacent hexes
            key = (round(vx * 1000), round(vy * 1000))
            for (kx, ky), vid in vertex_lookup.items():
                if abs(kx - key[0]) <= 3 and abs(ky - key[1]) <= 3:
                    return vid
            vid = len(self.vertices)
            self.vertices.append(VertexNode(id=vid, x=round(vx, 4), y=round(vy, 4)))
            vertex_lookup[key] = vid
            return vid

        for hid, (q, r) in enumerate(HEX_AXIAL_COORDS):
            cx = sqrt3 * (q + r / 2.0)
            cy = 1.5 * r
            tile = HexTile(
                id=hid,
                q=q,
                r=r,
                x=round(cx, 4),
                y=round(cy, 4),
                resource="desert",
                number=0,
                pips=0,
            )
            # 6 corners of pointy-top hex
            for corner in range(6):
                angle = math.radians(60 * corner - 30)
                vx = cx + math.cos(angle)
                vy = cy + math.sin(angle)
                vid = get_or_create_vertex(vx, vy)
                tile.vertices.append(vid)
                if hid not in self.vertices[vid].hex_ids:
                    self.vertices[vid].hex_ids.append(hid)
            self.hexes.append(tile)

        # Build the 72 unique edges from the 6 sides of each hex
        for tile in self.hexes:
            verts = tile.vertices
            for i in range(6):
                u = verts[i]
                v = verts[(i + 1) % 6]
                pair = (min(u, v), max(u, v))
                if pair not in self.edge_by_pair:
                    eid = len(self.edges)
                    self.edges.append(EdgeSegment(id=eid, u=pair[0], v=pair[1]))
                    self.edge_by_pair[pair] = eid
                    self.vertices[u].neighbors.append(v)
                    self.vertices[v].neighbors.append(u)
                    self.vertices[u].edges.append(eid)
                    self.vertices[v].edges.append(eid)

        # Assign 9 canonical harbors along the coastal perimeter vertices
        coastal = [v for v in self.vertices if len(v.hex_ids) < 3]
        coastal_sorted = sorted(coastal, key=lambda v: math.atan2(v.y, v.x))
        port_types = [
            "3:1",
            "2:1_wheat",
            "2:1_ore",
            "3:1",
            "2:1_sheep",
            "3:1",
            "3:1",
            "2:1_brick",
            "2:1_wood",
        ]
        # Place each harbor on a pair of adjacent coastal vertices spaced evenly around the island
        step = len(coastal_sorted) / len(port_types)
        used_v: Set[int] = set()
        for idx, ptype in enumerate(port_types):
            base_v = coastal_sorted[int(idx * step) % len(coastal_sorted)]
            if base_v.id in used_v:
                continue
            base_v.port = ptype
            used_v.add(base_v.id)
            # Also assign to closest coastal neighbor
            for nb_id in base_v.neighbors:
                if len(self.vertices[nb_id].hex_ids) < 3 and nb_id not in used_v:
                    self.vertices[nb_id].port = ptype
                    used_v.add(nb_id)
                    break

    def randomize_resources(self) -> None:
        tiles = list(STANDARD_TILE_POOL)
        self.rng.shuffle(tiles)
        tokens = list(STANDARD_NUMBER_TOKENS)
        self.rng.shuffle(tokens)

        # Prevent red numbers (6 and 8) from being adjacent on balanced boards (Try up to 25 times)
        for _ in range(25):
            tok_iter = iter(tokens)
            temp_nums: List[int] = []
            for res in tiles:
                temp_nums.append(0 if res == "desert" else next(tok_iter))
            if not self._has_adjacent_red_numbers(temp_nums):
                break
            self.rng.shuffle(tokens)

        tok_iter = iter(tokens)
        for hid, tile in enumerate(self.hexes):
            res = tiles[hid]
            tile.resource = res
            if res == "desert":
                tile.number = 0
                tile.pips = 0
                self.robber_hex = hid
            else:
                num = next(tok_iter)
                tile.number = num
                tile.pips = PIP_MAP[num]

    def _has_adjacent_red_numbers(self, nums: List[int]) -> bool:
        red_hexes = {h.id for h, n in zip(self.hexes, nums) if n in (6, 8)}
        for h1 in red_hexes:
            v1 = set(self.hexes[h1].vertices)
            for h2 in red_hexes:
                if h1 < h2 and len(v1.intersection(self.hexes[h2].vertices)) >= 2:
                    return True
        return False

    def is_legal_settlement(self, vid: int, occupied_vertices: Dict[int, Tuple[int, int]]) -> bool:
        """Enforces the Distance Rule: vertex and all its neighbors must be unoccupied."""
        if vid in occupied_vertices:
            return False
        for nb in self.vertices[vid].neighbors:
            if nb in occupied_vertices:
                return False
        return True

    def blocked_vertices_mask(self, occupied_vertices: Dict[int, Tuple[int, int]]) -> Set[int]:
        """Returns the set of all vertices blocked by the Distance Rule."""
        blocked: Set[int] = set()
        for vid in occupied_vertices:
            blocked.add(vid)
            for nb in self.vertices[vid].neighbors:
                blocked.add(nb)
        return blocked

    def vertex_pips(self, vid: int) -> int:
        return sum(self.hexes[hid].pips for hid in self.vertices[vid].hex_ids)

    def vertex_resources(self, vid: int) -> Dict[str, int]:
        res_pips: Dict[str, int] = {r: 0 for r in RESOURCES}
        for hid in self.vertices[vid].hex_ids:
            h = self.hexes[hid]
            if h.resource in res_pips:
                res_pips[h.resource] += h.pips
        return res_pips

    def longest_road_for_player(
        self,
        player_id: int,
        edge_owners: Dict[int, int],
        occupied_vertices: Dict[int, Tuple[int, int]],
    ) -> int:
        """Calculates the longest simple road path for `player_id` via DFS."""
        player_edges = [eid for eid, owner in edge_owners.items() if owner == player_id]
        if not player_edges:
            return 0

        adj: Dict[int, List[Tuple[int, int]]] = {}
        for eid in player_edges:
            e = self.edges[eid]
            adj.setdefault(e.u, []).append((e.v, eid))
            adj.setdefault(e.v, []).append((e.u, eid))

        best = 0
        visited_edges: Set[int] = set()

        def dfs(curr_v: int, length: int) -> None:
            nonlocal best
            if length > best:
                best = length
            # Opponent settlement breaks road continuity
            if length > 0 and curr_v in occupied_vertices and occupied_vertices[curr_v][0] != player_id:
                return
            for nxt_v, eid in adj.get(curr_v, []):
                if eid not in visited_edges:
                    visited_edges.add(eid)
                    dfs(nxt_v, length + 1)
                    visited_edges.remove(eid)

        for start_v in adj:
            dfs(start_v, 0)

        return best

    def export_geometry(self) -> dict:
        """Serializes board topology and tiles for Remotion visualizations."""
        return {
            "hexes": [
                {
                    "id": h.id,
                    "q": h.q,
                    "r": h.r,
                    "x": h.x,
                    "y": h.y,
                    "resource": h.resource,
                    "number": h.number,
                    "pips": h.pips,
                    "vertices": h.vertices,
                }
                for h in self.hexes
            ],
            "vertices": [
                {
                    "id": v.id,
                    "x": v.x,
                    "y": v.y,
                    "hexIds": v.hex_ids,
                    "neighbors": v.neighbors,
                    "port": v.port,
                }
                for v in self.vertices
            ],
            "edges": [{"id": e.id, "u": e.u, "v": e.v} for e in self.edges],
            "robberHex": self.robber_hex,
        }
