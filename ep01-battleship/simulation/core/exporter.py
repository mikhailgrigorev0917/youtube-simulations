from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Optional

from simulation.core.models import GameResult, ShotResult


def game_result_to_scene_spec(
    result: GameResult,
    scene_id: Optional[str] = None,
    fps: int = 30,
    frame_stride: int = 10,
    initial_delay: int = 15,
) -> dict[str, Any]:
    """Converts a GameResult into a Remotion SceneSpec JSON-serializable dictionary."""
    if scene_id is None:
        p_name = result.placement_strategy.lower().replace(" ", "_")
        s_name = result.shooting_strategy.lower().replace(" ", "_")
        scene_id = f"sim_{p_name}_vs_{s_name}"

    total_shots = len(result.shots)
    total_frames = initial_delay + (total_shots * frame_stride) + 30

    hits = sum(1 for s in result.shots if s.result in (ShotResult.HIT, ShotResult.SUNK))
    misses = total_shots - hits

    shots_data = []
    for idx, s in enumerate(result.shots):
        frame = initial_delay + idx * frame_stride
        res_str = "hit" if s.result in (ShotResult.HIT, ShotResult.SUNK) else "miss"
        shots_data.append({
            "frame": frame,
            "cell": {"row": s.cell.row, "col": s.cell.col},
            "result": res_str,
        })

    ships_data = []
    for ship in result.ships:
        ships_data.append({
            "id": ship.id,
            "name": ship.name,
            "cells": [{"row": c.row, "col": c.col} for c in ship.cells],
            "sunk": ship.is_sunk,
        })

    return {
        "id": scene_id,
        "domain": "battleship",
        "compositionId": "BattleshipShotSequence",
        "durationInFrames": total_frames,
        "fps": fps,
        "width": 1920,
        "height": 1080,
        "seed": result.seed or 42,
        "data": {
            "boardSize": result.board_size,
            "ships": ships_data,
            "shots": shots_data,
            "stats": {
                "totalShots": total_shots,
                "hits": hits,
                "misses": misses,
            },
        },
    }


def export_replay_to_json(
    result: GameResult,
    output_path: str | Path,
    scene_id: Optional[str] = None,
    frame_stride: int = 10,
) -> Path:
    """Exports GameResult to a JSON file on disk."""
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    spec = game_result_to_scene_spec(
        result,
        scene_id=scene_id or out_file.stem,
        frame_stride=frame_stride,
    )
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
    return out_file
