from __future__ import annotations
import tempfile
from pathlib import Path

from simulation.core.engine import BattleshipEngine
from simulation.core.exporter import export_replay_to_json, game_result_to_scene_spec
from simulation.core.models import GameConfig
from simulation.strategies.base import get_placement_strategy, get_shooting_strategy
import simulation.strategies.placement  # noqa: F401
import simulation.strategies.shooting  # noqa: F401


def test_exporter_schema():
    config = GameConfig(board_size=10, allow_touching=False)
    engine = BattleshipEngine(config)
    result = engine.play(
        get_placement_strategy("random"),
        get_shooting_strategy("hunt_target"),
        seed=42,
    )

    spec = game_result_to_scene_spec(result, scene_id="test-spec")
    assert spec["id"] == "test-spec"
    assert spec["domain"] == "battleship"
    assert spec["compositionId"] == "BattleshipShotSequence"
    assert "data" in spec
    data = spec["data"]
    assert data["boardSize"] == 10
    assert len(data["ships"]) == 10
    assert len(data["shots"]) == result.turns
    assert data["stats"]["totalShots"] == result.turns

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / "test_replay.json"
        saved = export_replay_to_json(result, tmp_path)
        assert saved.exists()
