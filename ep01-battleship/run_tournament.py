#!/usr/bin/env python3
"""CLI runner for Battleship Strategy Tournament and Statistics Generator.

Usage:
  python run_tournament.py --games 1000
  python run_tournament.py --list
  python run_tournament.py --games 200 --placements border,random --shooters hunt_target,parity_hunt
"""

from __future__ import annotations
import argparse
import sys
import time

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from rich.console import Console

from simulation.core.models import GameConfig
from simulation.runner.display import (
    plot_heatmap_matrix,
    print_pivot_table,
    print_rich_table,
)
from simulation.runner.tournament import TournamentRunner
from simulation.strategies.base import (
    get_placement_strategies,
    get_shooting_strategies,
)
# Ensure all strategies are imported and registered
import simulation.strategies.placement  # noqa: F401
import simulation.strategies.shooting  # noqa: F401


def parse_args():
    parser = argparse.ArgumentParser(
        description="Battleship Strategy Tournament & Statistics Generator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--games",
        "-g",
        type=int,
        default=500,
        help="Number of simulated games per matchup pair",
    )
    parser.add_argument(
        "--board-size",
        "-b",
        type=int,
        default=10,
        help="Board size (NxN)",
    )
    parser.add_argument(
        "--allow-touching",
        action="store_true",
        help="Allow ships to touch (by default, no touching even at corners)",
    )
    parser.add_argument(
        "--placements",
        "-p",
        type=str,
        default="",
        help="Comma-separated placement strategies to include (default: all)",
    )
    parser.add_argument(
        "--shooters",
        "-s",
        type=str,
        default="",
        help="Comma-separated shooting strategies to include (default: all)",
    )
    parser.add_argument(
        "--no-replays",
        action="store_true",
        help="Do not save replay JSON files",
    )
    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Do not generate the heatmap PNG plot",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all registered placement and shooting strategies and exit",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    console = Console()

    if args.list:
        console.print("\n[bold cyan]Registered Placement Strategies (Defense):[/bold cyan]")
        for name, cls in get_placement_strategies().items():
            console.print(f"  • [yellow]{name:<15}[/yellow] — {cls.description}")

        console.print("\n[bold green]Registered Shooting Strategies (Offense):[/bold green]")
        for name, cls in get_shooting_strategies().items():
            console.print(f"  • [yellow]{name:<22}[/yellow] — {cls.description}")
        console.print()
        sys.exit(0)

    config = GameConfig(
        board_size=args.board_size,
        allow_touching=args.allow_touching,
    )

    placements = [p.strip() for p in args.placements.split(",") if p.strip()] if args.placements else None
    shooters = [s.strip() for s in args.shooters.split(",") if s.strip()] if args.shooters else None

    avail_p = list(get_placement_strategies().keys()) if placements is None else placements
    avail_s = list(get_shooting_strategies().keys()) if shooters is None else shooters

    total_matchups = len(avail_p) * len(avail_s)
    total_games = total_matchups * args.games

    console.print(
        f"\n[bold magenta]=== Starting Battleship Tournament ===[/bold magenta]\n"
        f"  [cyan]{len(avail_p)} placements[/cyan] x [green]{len(avail_s)} shooters[/green] "
        f"= [bold yellow]{total_matchups} matchups[/bold yellow] ([bold white]{total_games:,} total games[/bold white])\n"
    )

    start_time = time.perf_counter()

    runner = TournamentRunner(config=config)
    stats_list = runner.run_tournament(
        placement_names=placements,
        shooting_names=shooters,
        num_games_per_matchup=args.games,
        save_replays=not args.no_replays,
        replays_dir="data/battleship/replays",
    )

    elapsed = time.perf_counter() - start_time
    gps = total_games / max(elapsed, 0.001)

    console.print(f"\n[bold green]Simulation completed in {elapsed:.2f}s ({gps:.0f} games/sec)![/bold green]\n")

    # Display results
    print_rich_table(stats_list)
    console.print()
    print_pivot_table(stats_list)

    if not args.no_plot:
        plot_path = plot_heatmap_matrix(stats_list, "output/battleship/stats_matrix.png")
        console.print(f"\n[bold cyan]Saved strategy heatmap to: {plot_path}[/bold cyan]")

    if not args.no_replays:
        console.print(f"[bold cyan]Saved game replays to: data/battleship/replays/[/bold cyan]\n")


if __name__ == "__main__":
    main()
