from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Callable, ClassVar, Optional, Type
import random

from simulation.core.models import CellCoord, GameConfig, Ship, ShotRecord


class BasePlacementStrategy(ABC):
    name: ClassVar[str] = "base_placement"
    description: ClassVar[str] = "Base placement strategy"

    @abstractmethod
    def place_ships(self, config: GameConfig, rng: random.Random) -> list[Ship]:
        """Places all ships defined in config and returns the list of Ships."""
        pass


class BaseShootingStrategy(ABC):
    name: ClassVar[str] = "base_shooting"
    description: ClassVar[str] = "Base shooting strategy"

    def __init__(self):
        self.config: Optional[GameConfig] = None
        self.rng: Optional[random.Random] = None
        self.shots_fired: set[CellCoord] = set()
        self.hits: set[CellCoord] = set()
        self.sunk_ships: list[Ship] = []

    def initialize(self, config: GameConfig, rng: random.Random) -> None:
        self.config = config
        self.rng = rng
        self.shots_fired = set()
        self.hits = set()
        self.sunk_ships = []

    @abstractmethod
    def next_shot(self) -> CellCoord:
        """Returns the next cell to fire upon. Must be an unshot coordinate in bounds."""
        pass

    @abstractmethod
    def record_result(self, record: ShotRecord) -> None:
        """Receives feedback from the shot."""
        pass


# Global Registries
_PLACEMENT_REGISTRY: dict[str, Type[BasePlacementStrategy]] = {}
_SHOOTING_REGISTRY: dict[str, Type[BaseShootingStrategy]] = {}


def register_placement(name: str, description: str = ""):
    def decorator(cls: Type[BasePlacementStrategy]):
        cls.name = name
        if description:
            cls.description = description
        _PLACEMENT_REGISTRY[name] = cls
        return cls
    return decorator


def register_shooting(name: str, description: str = ""):
    def decorator(cls: Type[BaseShootingStrategy]):
        cls.name = name
        if description:
            cls.description = description
        _SHOOTING_REGISTRY[name] = cls
        return cls
    return decorator


def get_placement_strategies() -> dict[str, Type[BasePlacementStrategy]]:
    return dict(_PLACEMENT_REGISTRY)


def get_shooting_strategies() -> dict[str, Type[BaseShootingStrategy]]:
    return dict(_SHOOTING_REGISTRY)


def get_placement_strategy(name: str) -> BasePlacementStrategy:
    if name not in _PLACEMENT_REGISTRY:
        raise KeyError(f"Placement strategy '{name}' not found. Available: {list(_PLACEMENT_REGISTRY.keys())}")
    return _PLACEMENT_REGISTRY[name]()


def get_shooting_strategy(name: str) -> BaseShootingStrategy:
    if name not in _SHOOTING_REGISTRY:
        raise KeyError(f"Shooting strategy '{name}' not found. Available: {list(_SHOOTING_REGISTRY.keys())}")
    return _SHOOTING_REGISTRY[name]()
