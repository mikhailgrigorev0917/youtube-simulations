from __future__ import annotations
import sys
from pathlib import Path
from typing import Sequence

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from rich.console import Console
from rich.table import Table

from simulation.runner.stats import MatchupStats


def print_rich_table(stats_list: Sequence[MatchupStats]) -> None:
    console = Console()
    table = Table(
        title="Battleship Strategy Tournament Results (Turns to Win)",
        header_style="bold magenta",
        show_lines=True,
    )

    table.add_column("Placement (Defense)", style="cyan", justify="left")
    table.add_column("Shooting (Offense)", style="green", justify="left")
    table.add_column("Games", justify="right")
    table.add_column("Mean ± Std", justify="center", style="bold yellow")
    table.add_column("Median", justify="right")
    table.add_column("Min", justify="right", style="dim")
    table.add_column("Max", justify="right", style="dim")
    table.add_column("P90 (90%)", justify="right")

    # Sort by shooting strategy, then mean turns
    sorted_stats = sorted(stats_list, key=lambda s: (s.shooting, s.mean_turns))

    for s in sorted_stats:
        table.add_row(
            s.placement,
            s.shooting,
            str(s.games_count),
            f"{s.mean_turns:.2f} ± {s.std_turns:.2f}",
            f"{s.median_turns:.1f}",
            str(s.min_turns),
            str(s.max_turns),
            f"{s.p90_turns:.1f}",
        )

    console.print(table)


def print_pivot_table(stats_list: Sequence[MatchupStats]) -> None:
    console = Console()
    placements = sorted(list({s.placement for s in stats_list}))
    shootings = sorted(list({s.shooting for s in stats_list}))

    lookup = {(s.placement, s.shooting): s.mean_turns for s in stats_list}

    matrix_table = Table(
        title="Mean Turns Matrix (Placement vs Shooting Strategy) — Lower is Better for Shooter",
        header_style="bold cyan",
        show_lines=True,
    )

    matrix_table.add_column("Placement \\ Shooter", style="bold yellow")
    for s in shootings:
        matrix_table.add_column(s, justify="center")

    for p in placements:
        row_vals = [p]
        for s in shootings:
            val = lookup.get((p, s))
            if val is not None:
                # Color code: green if <= 45, yellow if <= 65, red if > 65
                color = "bold green" if val <= 45 else ("yellow" if val <= 65 else "red")
                row_vals.append(f"[{color}]{val:.1f}[/{color}]")
            else:
                row_vals.append("-")
        matrix_table.add_row(*row_vals)

    console.print(matrix_table)


def plot_heatmap_matrix(
    stats_list: Sequence[MatchupStats],
    output_path: str | Path = "output/battleship/stats_matrix.png",
) -> Path:
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    data = [
        {"Placement": s.placement, "Shooter": s.shooting, "MeanTurns": s.mean_turns}
        for s in stats_list
    ]
    df = pd.DataFrame(data)
    pivot = df.pivot(index="Placement", columns="Shooter", values="MeanTurns")

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)

    # Plot custom annotated heatmap
    cax = ax.imshow(pivot.values, cmap="magma_r", aspect="auto")
    fig.colorbar(cax, ax=ax, label="Mean Turns (Fewer = Faster Win)")

    ax.set_xticks(np.arange(len(pivot.columns)))
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_xticklabels(pivot.columns, fontsize=11, rotation=25, ha="right", color="#e2e8f0")
    ax.set_yticklabels(pivot.index, fontsize=11, color="#e2e8f0")

    # Annotate values inside cells
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.iloc[i, j]
            color = "white" if val > pivot.values.mean() else "black"
            ax.text(j, i, f"{val:.1f}", ha="center", va="center", color=color, fontweight="bold", fontsize=11)

    ax.set_title("Battleship Strategy Performance Matrix (Mean Turns to Sink All Ships)", fontsize=14, pad=15, color="#f8fafc")
    ax.set_xlabel("Shooting Strategy (Offense)", fontsize=12, labelpad=10, color="#94a3b8")
    ax.set_ylabel("Placement Strategy (Defense)", fontsize=12, labelpad=10, color="#94a3b8")

    plt.tight_layout()
    fig.savefig(out_file)
    plt.close(fig)
    return out_file
