"""Tournament runner and empirical data generator for 2048 with large sample sizes (N=1000)."""

from __future__ import annotations
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any
import multiprocessing as mp

sys.path.insert(0, str(Path(__file__).resolve().parent))

from game import Game2048, GameResult
from strategies import RandomBot, GreedyBot, CornerBot, HeuristicBot, ExpectimaxBot

BOT_FACTORIES = {
    "random": lambda: RandomBot(),
    "greedy": lambda: GreedyBot(),
    "corner": lambda: CornerBot(),
    "heuristic": lambda: HeuristicBot(),
    "expectimax": lambda: ExpectimaxBot(max_depth=2),
}

def _run_single_game(args: tuple) -> Dict[str, Any]:
    bot_id, seed, p4 = args
    factory = BOT_FACTORIES[bot_id]
    bot = factory()
    game = Game2048(seed=seed, p4=p4)
    res = game.play(bot.get_move, bot_id=bot_id, record_history=False)
    return {
        "bot_id": bot_id,
        "seed": seed,
        "score": res.score,
        "moves": res.move_count,
        "max_tile": res.max_tile,
        "won_2048": res.won_2048,
        "reached_4096": res.reached_4096,
        "reached_8192": res.reached_8192,
        "reached_16384": res.reached_16384,
    }

def run_bot_tournament(bot_id: str, num_games: int, p4: float = 0.1, workers: int = 14) -> Dict[str, Any]:
    tasks = [(bot_id, 10000 + i, p4) for i in range(num_games)]
    results: List[Dict[str, Any]] = []
    chunk_size = 50

    print(f"[*] Starting {num_games} games for '{bot_id}' on {workers} CPU workers...", flush=True)
    t0 = time.time()

    with mp.Pool(workers) as pool:
        for i in range(0, num_games, chunk_size):
            chunk = tasks[i : i + chunk_size]
            res_chunk = pool.map(_run_single_game, chunk)
            results.extend(res_chunk)
            done = len(results)
            won = sum(1 for r in results if r["won_2048"])
            cur_wr = (won / done) * 100
            print(f"    -> [{bot_id}] Progress: {done}/{num_games} games ({done*100//num_games}%) | Live 2048 WR: {cur_wr:.1f}%", flush=True)

    el = time.time() - t0
    total = len(results)
    scores = [r["score"] for r in results]
    moves = [r["moves"] for r in results]
    won_2048_count = sum(1 for r in results if r["won_2048"])
    reached_4096_count = sum(1 for r in results if r["reached_4096"])
    reached_8192_count = sum(1 for r in results if r["reached_8192"])

    tile_dist: Dict[int, int] = {}
    for r in results:
        t = r["max_tile"]
        tile_dist[t] = tile_dist.get(t, 0) + 1

    summary = {
        "bot_id": bot_id,
        "games_played": total,
        "p4": p4,
        "avg_score": round(sum(scores) / total, 1),
        "max_score": max(scores),
        "avg_moves": round(sum(moves) / total, 1),
        "win_rate_2048": round(won_2048_count / total * 100, 2),
        "rate_4096": round(reached_4096_count / total * 100, 2),
        "rate_8192": round(reached_8192_count / total * 100, 2),
        "tile_distribution": tile_dist
    }
    print(f"    [OK] '{bot_id}' Complete in {el:.1f}s | Final 2048 WR: {summary['win_rate_2048']}% | Avg Score: {summary['avg_score']}\n", flush=True)
    return summary

def run_phase_transition_study(bot_id: str = "heuristic", games_per_p: int = 100, workers: int = 14) -> List[Dict[str, Any]]:
    p4_values = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40]
    curve = []
    print(f"[*] Running Phase Transition analysis ({games_per_p} games per probability point)...", flush=True)
    for p4 in p4_values:
        res = run_bot_tournament(bot_id, num_games=games_per_p, p4=p4, workers=workers)
        curve.append({
            "p4": p4,
            "win_rate_2048": res["win_rate_2048"],
            "avg_score": res["avg_score"]
        })
    return curve

def main():
    print("=" * 60, flush=True)
    print("2048 Scale Tournament (N=1,000 per sample)", flush=True)
    print("=" * 60, flush=True)

    start_time = time.time()
    data_dir = Path(__file__).resolve().parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    game_counts = {
        "random": 1000,
        "greedy": 1000,
        "corner": 1000,
        "heuristic": 1000,
        "expectimax": 1000
    }

    leaderboard = []
    for bot_id, count in game_counts.items():
        res = run_bot_tournament(bot_id, num_games=count, workers=14)
        leaderboard.append(res)

    phase_curve = run_phase_transition_study(bot_id="heuristic", games_per_p=100, workers=14)

    output_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tournament_summary": leaderboard,
        "phase_transition_curve": phase_curve
    }

    out_file = data_dir / "results.json"
    with open(out_file, "w") as f:
        json.dump(output_data, f, indent=2)

    total_time = time.time() - start_time
    print(f"[OK] Full 5,800-game simulation successfully finished in {total_time:.1f}s!", flush=True)
    print(f"[OK] Results saved to: {out_file}", flush=True)

if __name__ == "__main__":
    main()
