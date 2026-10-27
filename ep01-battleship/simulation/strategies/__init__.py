"""Strategy implementations for placement and shooting."""
from simulation.strategies.base import (
    BasePlacementStrategy,
    BaseShootingStrategy,
    register_placement,
    register_shooting,
    get_placement_strategies,
    get_shooting_strategies,
    get_placement_strategy,
    get_shooting_strategy,
)

__all__ = [
    "BasePlacementStrategy",
    "BaseShootingStrategy",
    "register_placement",
    "register_shooting",
    "get_placement_strategies",
    "get_shooting_strategies",
    "get_placement_strategy",
    "get_shooting_strategy",
]
