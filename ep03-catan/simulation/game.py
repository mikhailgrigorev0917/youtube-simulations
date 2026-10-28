#!/usr/bin/env python3
"""
4-Player Catan Simulation Engine & 6 Bot Archetypes for Episode 03.
"""
from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from board import CatanBoard, RESOURCES

DEV_CARD_DECK_TEMPLATE = (
    ["knight"] * 14
    + ["vp"] * 5
    + ["monopoly"] * 2
    + ["year_of_plenty"] * 2
    + ["road_building"] * 2
)

BOT_LABELS: Dict[str, str] = {
    "random_settler": "Random Settler",
    "naive_pip": "Bot #1: Naive Pip Maximizer",
    "port_specialist": "Bot #2: Port Specialist (2:1)",
    "road_builder": "Bot #3: Road Builder",
    "ows_city_engine": "Bot #4: OWS City Engine",
    "alpha_catan": "Bot #5: AlphaCatan",
}


@dataclass
class PlayerState:
    id: int
    strategy: str
    hand: Dict[str, int] = field(default_factory=lambda: {r: 0 for r in RESOURCES})
    settlements: Set[int] = field(default_factory=set)
    cities: Set[int] = field(default_factory=set)
    roads: Set[int] = field(default_factory=set)
    ports: Set[str] = field(default_factory=set)
    dev_cards: Dict[str, int] = field(
        default_factory=lambda: {
            "knight": 0,
            "vp": 0,
            "monopoly": 0,
            "year_of_plenty": 0,
            "road_building": 0,
        }
    )
    knights_played: int = 0
    monopolies_played: int = 0
    monopoly_cards_stolen: int = 0
    robber_losses: int = 0
    bank_trades_4to1: int = 0
    port_trades: int = 0
    last_robbed_by: Optional[int] = None

    def hand_size(self) -> int:
        return sum(self.hand.values())

    def trade_ratio(self, res: str) -> int:
        if f"2:1_{res}" in self.ports:
            return 2
        if "3:1" in self.ports:
            return 3
        return 4


def score_vertex_for_strategy(
    board: CatanBoard,
    vid: int,
    strategy: str,
    existing_res_pips: Dict[str, int],
    existing_ports: Set[str],
    rng: random.Random,
) -> float:
    if strategy == "random_settler":
        return rng.random()

    v = board.vertices[vid]
    total_pips = board.vertex_pips(vid)
    res_pips = board.vertex_resources(vid)

    if strategy == "naive_pip":
        # Pure dot counter: blindly chases highest total pips, ignores diversity and ports
        return total_pips * 10.0 + rng.uniform(0, 0.2)

    if strategy == "road_builder":
        # Heavy bias toward Wood and Brick, ignores Ore
        wb_pips = res_pips["wood"] + res_pips["brick"]
        synergy = 4.0 if (res_pips["wood"] > 0 and res_pips["brick"] > 0) else 0.0
        wheat_sheep = (res_pips["wheat"] + res_pips["sheep"]) * 0.65
        return wb_pips * 2.4 + wheat_sheep + synergy + rng.uniform(0, 0.2)

    if strategy == "port_specialist":
        # Loves coastal 2:1 / 3:1 ports or heavy concentration in a port-matched resource
        port_bonus = 0.0
        if v.port:
            if v.port.startswith("2:1_"):
                target_r = v.port.split("_", 1)[1]
                existing_r = existing_res_pips.get(target_r, 0) + res_pips[target_r]
                port_bonus = 10.0 + existing_r * 2.2
            else:
                port_bonus = 6.5
        for p in existing_ports:
            if p.startswith("2:1_"):
                target_r = p.split("_", 1)[1]
                port_bonus += res_pips[target_r] * 1.9
        return total_pips * 1.45 + port_bonus + res_pips["wheat"] * 0.8 + rng.uniform(0, 0.2)

    if strategy == "ows_city_engine":
        # Prioritizes Ore + Wheat + Sheep for Cities and Dev Cards
        ows_score = res_pips["wheat"] * 2.4 + res_pips["ore"] * 2.3 + res_pips["sheep"] * 1.5
        wb_score = (res_pips["wood"] + res_pips["brick"]) * 0.75
        combined = {r: existing_res_pips.get(r, 0) + res_pips[r] for r in RESOURCES}
        ows_synergy = 6.0 if (combined["wheat"] >= 4 and combined["ore"] >= 3) else 0.0
        return ows_score + wb_score + ows_synergy + rng.uniform(0, 0.2)

    # alpha_catan: Wheat-anchored Pip x Entropy + OWS/Port hybrid
    combined = {r: existing_res_pips.get(r, 0) + res_pips[r] for r in RESOURCES}
    distinct_res = sum(1 for r in RESOURCES if combined[r] > 0)
    wheat_bonus = 7.5 if combined["wheat"] >= 4 else (3.5 if combined["wheat"] > 0 else -6.0)
    ore_bonus = 5.0 if combined["ore"] >= 3 else (2.0 if combined["ore"] > 0 else 0.0)
    port_synergy = 0.0
    if v.port and v.port.startswith("2:1_"):
        tr = v.port.split("_", 1)[1]
        if combined[tr] >= 5:
            port_synergy = 6.5
    return (
        total_pips * 1.85
        + distinct_res * 2.8
        + wheat_bonus
        + ore_bonus
        + port_synergy
        + rng.uniform(0, 0.15)
    )


def choose_initial_road(
    board: CatanBoard,
    vid: int,
    player_id: int,
    occupied_vertices: Dict[int, Tuple[int, int]],
    edge_owners: Dict[int, int],
    strategy: str,
    rng: random.Random,
) -> int:
    legal_edges = [eid for eid in board.vertices[vid].edges if eid not in edge_owners]
    if not legal_edges:
        return board.vertices[vid].edges[0]
    if strategy == "random_settler":
        return rng.choice(legal_edges)

    # Pick road pointing toward the neighbor vertex whose further neighbors have best open pips/ports
    best_eid = legal_edges[0]
    best_val = -1e9
    for eid in legal_edges:
        e = board.edges[eid]
        nb = e.v if e.u == vid else e.u
        val = 0.0
        for step2 in board.vertices[nb].neighbors:
            if step2 != vid and board.is_legal_settlement(step2, occupied_vertices):
                v_pips = board.vertex_pips(step2)
                port_b = 4.0 if board.vertices[step2].port else 0.0
                val = max(val, v_pips + port_b)
        if val > best_val:
            best_val = val
            best_eid = eid
    return best_eid


def play_catan_game(
    strategies: List[str],
    seed: int = 42,
    record_events: bool = False,
    max_turns: int = 85,
) -> dict:
    rng = random.Random(seed)
    board = CatanBoard(seed=seed)
    players = [PlayerState(id=i, strategy=strategies[i]) for i in range(4)]

    # occupied_vertices: vid -> (player_id, building_level: 1=settlement, 2=city)
    occupied_vertices: Dict[int, Tuple[int, int]] = {}
    edge_owners: Dict[int, int] = {}

    dev_deck = list(DEV_CARD_DECK_TEMPLATE)
    rng.shuffle(dev_deck)

    events: List[dict] = []

    def visible_vp(pid: int) -> int:
        p = players[pid]
        vp = len(p.settlements) + 2 * len(p.cities)
        if longest_road_holder == pid:
            vp += 2
        if largest_army_holder == pid:
            vp += 2
        return vp

    def total_vp(pid: int) -> int:
        return visible_vp(pid) + players[pid].dev_cards["vp"]

    def player_pip_income(pid: int) -> int:
        p = players[pid]
        total = 0
        for v in p.settlements:
            total += board.vertex_pips(v)
        for v in p.cities:
            total += 2 * board.vertex_pips(v)
        return total

    def snapshot_event(ev_type: str, turn_num: int, actor: int, **extra: object) -> None:
        if not record_events:
            return
        events.append(
            {
                "event": ev_type,
                "turn": turn_num,
                "actor": actor,
                "robberHex": board.robber_hex,
                "longestRoadHolder": longest_road_holder,
                "largestArmyHolder": largest_army_holder,
                "scores": [total_vp(i) for i in range(4)],
                "visibleScores": [visible_vp(i) for i in range(4)],
                "handSizes": [players[i].hand_size() for i in range(4)],
                "pips": [player_pip_income(i) for i in range(4)],
                "settlements": [sorted(list(players[i].settlements)) for i in range(4)],
                "cities": [sorted(list(players[i].cities)) for i in range(4)],
                "roads": [sorted(list(players[i].roads)) for i in range(4)],
                **extra,
            }
        )

    longest_road_holder: Optional[int] = None
    longest_road_len: int = 4
    largest_army_holder: Optional[int] = None
    largest_army_count: int = 2

    # --- SNAKE DRAFT INITIAL PLACEMENT (0, 1, 2, 3, 3, 2, 1, 0) ---
    draft_order = [0, 1, 2, 3, 3, 2, 1, 0]
    player_res_pips: List[Dict[str, int]] = [{r: 0 for r in RESOURCES} for _ in range(4)]

    for step_idx, pid in enumerate(draft_order):
        p = players[pid]
        legal_verts = [
            v.id for v in board.vertices if board.is_legal_settlement(v.id, occupied_vertices)
        ]
        chosen_v = max(
            legal_verts,
            key=lambda vid: score_vertex_for_strategy(
                board, vid, p.strategy, player_res_pips[pid], p.ports, rng
            ),
        )
        occupied_vertices[chosen_v] = (pid, 1)
        p.settlements.add(chosen_v)
        if board.vertices[chosen_v].port:
            p.ports.add(board.vertices[chosen_v].port)  # type: ignore

        v_res = board.vertex_resources(chosen_v)
        for r, val in v_res.items():
            player_res_pips[pid][r] += val

        # Second settlement yields starting resources
        if step_idx >= 4:
            for hid in board.vertices[chosen_v].hex_ids:
                res = board.hexes[hid].resource
                if res in RESOURCES:
                    p.hand[res] += 1

        chosen_e = choose_initial_road(
            board, chosen_v, pid, occupied_vertices, edge_owners, p.strategy, rng
        )
        edge_owners[chosen_e] = pid
        p.roads.add(chosen_e)
        snapshot_event(
            "initial_placement",
            0,
            pid,
            vertexId=chosen_v,
            edgeId=chosen_e,
            blockedVertices=sorted(list(board.blocked_vertices_mask(occupied_vertices))),
        )

    turn0_blocked_count = len(board.blocked_vertices_mask(occupied_vertices))
    starting_wheat_pips = [player_res_pips[i]["wheat"] for i in range(4)]
    starting_total_pips = [sum(player_res_pips[i].values()) for i in range(4)]

    def update_longest_road(turn_num: int) -> None:
        nonlocal longest_road_holder, longest_road_len
        for pid in range(4):
            r_len = board.longest_road_for_player(pid, edge_owners, occupied_vertices)
            if r_len >= 5 and r_len > longest_road_len:
                longest_road_len = r_len
                if longest_road_holder != pid:
                    longest_road_holder = pid
                    snapshot_event("longest_road_claimed", turn_num, pid, length=r_len)

    def move_robber(mover_id: int, turn_num: int) -> None:
        mover = players[mover_id]
        best_hid = board.robber_hex
        best_score = -1e9
        victim_id: Optional[int] = None

        for h in board.hexes:
            if h.id == board.robber_hex or h.resource == "desert":
                continue
            occupants: Set[int] = set()
            tile_pain = 0.0
            for vid in h.vertices:
                if vid in occupied_vertices:
                    owner, lvl = occupied_vertices[vid]
                    if owner == mover_id:
                        tile_pain -= 50.0  # Don't self-block!
                    else:
                        occupants.add(owner)
                        if mover.strategy == "alpha_catan":
                            # Cold-blooded EV Threat formula
                            threat = (
                                visible_vp(owner) * 3.5
                                + players[owner].dev_cards["vp"] * 2.0
                                + 0.25 * player_pip_income(owner)
                            )
                            res_mult = 1.6 if h.resource in ("wheat", "ore") else 1.0
                            tile_pain += threat * h.pips * lvl * res_mult
                        elif mover.strategy in ("ows_city_engine", "port_specialist"):
                            tile_pain += (visible_vp(owner) * 2.0 + h.pips) * lvl
                        else:
                            # Emotional Tit-for-Tat revenge or naive random
                            revenge = 25.0 if mover.last_robbed_by == owner else 1.0
                            tile_pain += revenge * h.pips + rng.uniform(0, 3.0)

            if occupants and tile_pain > best_score:
                best_score = tile_pain
                best_hid = h.id
                # Pick highest-VP occupant with cards
                valid_victims = [o for o in occupants if players[o].hand_size() > 0]
                if valid_victims:
                    victim_id = max(valid_victims, key=lambda o: (visible_vp(o), players[o].hand_size()))

        board.robber_hex = best_hid
        stolen_res: Optional[str] = None
        if victim_id is not None:
            v_hand = players[victim_id].hand
            avail = [r for r in RESOURCES for _ in range(v_hand[r])]
            if avail:
                stolen_res = rng.choice(avail)
                v_hand[stolen_res] -= 1
                mover.hand[stolen_res] += 1
                players[victim_id].last_robbed_by = mover_id

        snapshot_event(
            "robber_moved",
            turn_num,
            mover_id,
            hexId=best_hid,
            victim=victim_id,
            resource=stolen_res,
        )

    def maritime_trade_for(p: PlayerState, needed: Dict[str, int]) -> bool:
        """Attempts to trade surplus resources via ports or bank to fulfill `needed` recipe."""
        # Naive Pip Maximizer hoards cards more often unless it has massive excess
        hoard_buffer = 2 if p.strategy == "naive_pip" else 0

        for target_r, req_qty in needed.items():
            while p.hand[target_r] < req_qty:
                # Find a resource we have in surplus
                traded = False
                for give_r in RESOURCES:
                    if give_r == target_r:
                        continue
                    ratio = p.trade_ratio(give_r)
                    keep = needed.get(give_r, 0) + hoard_buffer
                    if p.hand[give_r] >= keep + ratio:
                        p.hand[give_r] -= ratio
                        p.hand[target_r] += 1
                        if ratio == 4:
                            p.bank_trades_4to1 += 1
                        else:
                            p.port_trades += 1
                        traded = True
                        break
                if not traded:
                    return False
        return True

    def try_spend_recipe(p: PlayerState, recipe: Dict[str, int]) -> bool:
        if all(p.hand[r] >= q for r, q in recipe.items()):
            for r, q in recipe.items():
                p.hand[r] -= q
            return True
        if maritime_trade_for(p, recipe) and all(p.hand[r] >= q for r, q in recipe.items()):
            for r, q in recipe.items():
                p.hand[r] -= q
            return True
        return False

    def find_reachable_settlement_vertices(pid: int) -> List[int]:
        p = players[pid]
        connected_verts: Set[int] = set()
        for eid in p.roads:
            e = board.edges[eid]
            connected_verts.add(e.u)
            connected_verts.add(e.v)
        return [
            vid
            for vid in connected_verts
            if board.is_legal_settlement(vid, occupied_vertices)
        ]

    def find_legal_road_edges(pid: int) -> List[int]:
        p = players[pid]
        frontier_verts: Set[int] = set(p.settlements) | set(p.cities)
        for eid in p.roads:
            e = board.edges[eid]
            # Can only extend road through a vertex if not blocked by an opponent settlement
            if e.u not in occupied_vertices or occupied_vertices[e.u][0] == pid:
                frontier_verts.add(e.u)
            if e.v not in occupied_vertices or occupied_vertices[e.v][0] == pid:
                frontier_verts.add(e.v)
        legal_e: Set[int] = set()
        for vid in frontier_verts:
            for eid in board.vertices[vid].edges:
                if eid not in edge_owners:
                    legal_e.add(eid)
        return list(legal_e)

    longest_road_by_turn: List[Optional[int]] = []
    recent_high_pip_rolls = 0
    winner_id: Optional[int] = None

    # --- MAIN GAME LOOP ---
    for round_num in range(1, max_turns + 1):
        for pid in range(4):
            p = players[pid]

            # 1. Roll 2d6
            roll = rng.randint(1, 6) + rng.randint(1, 6)
            if roll in (6, 8):
                recent_high_pip_rolls += 1
            else:
                recent_high_pip_rolls = max(0, recent_high_pip_rolls - 1)

            if roll == 7:
                # 7-Card Robber Tax: anyone holding > 7 cards loses half their hand
                for victim_p in players:
                    h_sz = victim_p.hand_size()
                    if h_sz > 7:
                        drop_cnt = h_sz // 2
                        victim_p.robber_losses += drop_cnt
                        for _ in range(drop_cnt):
                            avail = [r for r in RESOURCES if victim_p.hand[r] > 0]
                            if avail:
                                victim_p.hand[rng.choice(avail)] -= 1
                move_robber(pid, round_num)
            else:
                for h in board.hexes:
                    if h.number == roll and h.id != board.robber_hex and h.resource in RESOURCES:
                        for vid in h.vertices:
                            if vid in occupied_vertices:
                                owner, lvl = occupied_vertices[vid]
                                players[owner].hand[h.resource] += lvl
                snapshot_event("dice_rolled", round_num, pid, roll=roll)

            # 2. Play Development Cards (Knight / Monopoly / Year of Plenty / Road Building)
            if p.dev_cards["knight"] > 0:
                # Play knight if robber is on our tile or to chase Largest Army
                rob_on_us = any(
                    vid in occupied_vertices and occupied_vertices[vid][0] == pid
                    for vid in board.hexes[board.robber_hex].vertices
                )
                if rob_on_us or p.strategy in ("ows_city_engine", "alpha_catan"):
                    p.dev_cards["knight"] -= 1
                    p.knights_played += 1
                    if p.knights_played >= 3 and p.knights_played > largest_army_count:
                        largest_army_count = p.knights_played
                        largest_army_holder = pid
                    move_robber(pid, round_num)

            if p.dev_cards["monopoly"] > 0:
                # AlphaCatan & OWS wait for a cluster of resource accumulation (or late game)
                best_r = max(
                    RESOURCES,
                    key=lambda r: sum(players[o].hand[r] for o in range(4) if o != pid),
                )
                pool_qty = sum(players[o].hand[best_r] for o in range(4) if o != pid)
                should_trigger = (
                    (p.strategy == "alpha_catan" and (pool_qty >= 7 or round_num >= 16))
                    or (p.strategy == "ows_city_engine" and (pool_qty >= 6 or round_num >= 14))
                    or (p.strategy not in ("alpha_catan", "ows_city_engine") and pool_qty >= 3)
                )
                if should_trigger and pool_qty > 0:
                    p.dev_cards["monopoly"] -= 1
                    p.monopolies_played += 1
                    for o in range(4):
                        if o != pid:
                            taken = players[o].hand[best_r]
                            players[o].hand[best_r] = 0
                            p.hand[best_r] += taken
                            p.monopoly_cards_stolen += taken
                    snapshot_event(
                        "monopoly_played",
                        round_num,
                        pid,
                        resource=best_r,
                        stolen=p.monopoly_cards_stolen,
                    )

            if p.dev_cards["year_of_plenty"] > 0:
                p.dev_cards["year_of_plenty"] -= 1
                p.hand["wheat"] += 1
                p.hand["ore"] += 1

            # 3. Building & Action Phase by Archetype Priority
            city_recipe = {"wheat": 2, "ore": 3}
            settle_recipe = {"wood": 1, "brick": 1, "sheep": 1, "wheat": 1}
            dev_recipe = {"sheep": 1, "wheat": 1, "ore": 1}
            road_recipe = {"wood": 1, "brick": 1}

            # Strategy-specific action loops
            for _ in range(3):
                # Priority A: If at 8+ VP and can snatch Longest Road to win immediately (Survivorship Bias finisher!)
                if (
                    p.strategy in ("alpha_catan", "ows_city_engine", "port_specialist")
                    and total_vp(pid) >= 8
                    and longest_road_holder != pid
                ):
                    cur_r = board.longest_road_for_player(pid, edge_owners, occupied_vertices)
                    if cur_r >= longest_road_len - 1 and len(p.roads) < 15:
                        legal_e = find_legal_road_edges(pid)
                        if legal_e and try_spend_recipe(p, road_recipe):
                            eid = rng.choice(legal_e)
                            edge_owners[eid] = pid
                            p.roads.add(eid)
                            update_longest_road(round_num)
                            snapshot_event("road_built", round_num, pid, edgeId=eid)
                            if total_vp(pid) >= 10:
                                break

                # Priority B: Upgrade Settlement to City
                if (
                    p.settlements
                    and len(p.cities) < 4
                    and (
                        p.strategy in ("ows_city_engine", "alpha_catan", "port_specialist", "naive_pip")
                        or len(p.settlements) >= 3
                        or round_num >= 12
                    )
                ):
                    if try_spend_recipe(p, city_recipe):
                        best_v = max(p.settlements, key=lambda vid: board.vertex_pips(vid))
                        p.settlements.remove(best_v)
                        p.cities.add(best_v)
                        occupied_vertices[best_v] = (pid, 2)
                        snapshot_event("city_upgraded", round_num, pid, vertexId=best_v)
                        continue

                # Priority C: Build Settlement on reachable open vertex
                open_settle_verts = find_reachable_settlement_vertices(pid)
                if open_settle_verts and len(p.settlements) + len(p.cities) < 5:
                    if try_spend_recipe(p, settle_recipe):
                        best_v = max(
                            open_settle_verts,
                            key=lambda vid: score_vertex_for_strategy(
                                board, vid, p.strategy, player_res_pips[pid], p.ports, rng
                            ),
                        )
                        p.settlements.add(best_v)
                        occupied_vertices[best_v] = (pid, 1)
                        if board.vertices[best_v].port:
                            p.ports.add(board.vertices[best_v].port)  # type: ignore
                        # Building a settlement on an opponent's road can break their Longest Road!
                        update_longest_road(round_num)
                        snapshot_event("settlement_built", round_num, pid, vertexId=best_v)
                        continue

                # Priority D: Road Builder aggressively builds roads first
                if p.strategy == "road_builder" or (not open_settle_verts and len(p.roads) < 12):
                    legal_e = find_legal_road_edges(pid)
                    if legal_e and len(p.roads) < 15:
                        # OWS only builds roads if needed for a great spot or late game
                        if p.strategy in ("ows_city_engine", "alpha_catan") and len(p.cities) < 2 and round_num < 12:
                            pass
                        elif try_spend_recipe(p, road_recipe):
                            eid = choose_initial_road(
                                board,
                                board.edges[legal_e[0]].u,
                                pid,
                                occupied_vertices,
                                edge_owners,
                                p.strategy,
                                rng,
                            )
                            if eid not in legal_e:
                                eid = rng.choice(legal_e)
                            edge_owners[eid] = pid
                            p.roads.add(eid)
                            update_longest_road(round_num)
                            snapshot_event("road_built", round_num, pid, edgeId=eid)
                            continue

                # Priority E: Buy Development Card
                if dev_deck and (
                    p.strategy in ("ows_city_engine", "alpha_catan", "port_specialist")
                    or round_num >= 10
                ):
                    if try_spend_recipe(p, dev_recipe):
                        card = dev_deck.pop()
                        p.dev_cards[card] += 1
                        continue

                # Priority F: Port Specialist & AlphaCatan shed excess cards above 7 to dodge the 51.8% Robber Tax!
                if p.strategy in ("port_specialist", "alpha_catan", "ows_city_engine") and p.hand_size() > 7:
                    most_r = max(RESOURCES, key=lambda r: p.hand[r])
                    least_r = min(RESOURCES, key=lambda r: p.hand[r])
                    ratio = p.trade_ratio(most_r)
                    if p.hand[most_r] >= ratio:
                        p.hand[most_r] -= ratio
                        p.hand[least_r] += 1
                        if ratio == 4:
                            p.bank_trades_4to1 += 1
                        else:
                            p.port_trades += 1
                        continue

                break

            if total_vp(pid) >= 10:
                winner_id = pid
                snapshot_event("game_won", round_num, pid)
                break

        longest_road_by_turn.append(longest_road_holder)
        if winner_id is not None:
            break

    if winner_id is None:
        winner_id = max(range(4), key=lambda i: (total_vp(i), player_pip_income(i)))
        snapshot_event("game_won", max_turns, winner_id)

    return {
        "seed": seed,
        "winner": winner_id,
        "winnerStrategy": strategies[winner_id],
        "turns": round_num,
        "finalScores": [total_vp(i) for i in range(4)],
        "longestRoadHolder": longest_road_holder,
        "largestArmyHolder": largest_army_holder,
        "longestRoadByTurn": longest_road_by_turn,
        "turn0BlockedVertices": turn0_blocked_count,
        "startingWheatPips": starting_wheat_pips,
        "startingTotalPips": starting_total_pips,
        "robberLosses": [players[i].robber_losses for i in range(4)],
        "bankTrades4to1": [players[i].bank_trades_4to1 for i in range(4)],
        "portTrades": [players[i].port_trades for i in range(4)],
        "monopoliesPlayed": [players[i].monopolies_played for i in range(4)],
        "monopolyCardsStolen": [players[i].monopoly_cards_stolen for i in range(4)],
        "board": board.export_geometry() if record_events else None,
        "events": events if record_events else None,
    }
