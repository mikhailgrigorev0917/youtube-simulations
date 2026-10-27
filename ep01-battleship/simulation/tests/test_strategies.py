from __future__ import annotations
import random
import pytest

from simulation.core.engine import BattleshipEngine
from simulation.core.models import GameConfig
from simulation.strategies.base import (
    get_placement_strategies,
    get_placement_strategy,
    get_shooting_strategies,
    get_shooting_strategy,
)
import simulation.strategies.placement  # noqa: F401
import simulation.strategies.shooting  # noqa: F401


@pytest.mark.parametrize("placement_name", list(get_placement_strategies().keys()))
def test_all_placement_strategies(placement_name: str):
    config = GameConfig(board_size=10, allow_touching=False)
    rng = random.Random(123)
    strat = get_placement_strategy(placement_name)
    ships = strat.place_ships(config, rng)
    assert len(ships) == len(config.ship_sizes)
    total_cells = sum(s.size for s in ships)
    assert total_cells == sum(config.ship_sizes)


@pytest.mark.parametrize("shooting_name", list(get_shooting_strategies().keys()))
def test_all_shooting_strategies(shooting_name: str):
    config = GameConfig(board_size=10, allow_touching=False)
    engine = BattleshipEngine(config)
    placement = get_placement_strategy("random")
    shooter = get_shooting_strategy(shooting_name)

    result = engine.play(placement, shooter, seed=42)
    assert result.turns >= sum(config.ship_sizes)
    assert result.turns <= 100
    assert all(s.is_sunk for s in result.ships)
