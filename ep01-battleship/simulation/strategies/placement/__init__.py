"""Placement strategies."""
from simulation.strategies.placement.random_placement import RandomPlacementStrategy
from simulation.strategies.placement.border_placement import BorderPlacementStrategy
from simulation.strategies.placement.uniform_placement import UniformPlacementStrategy
from simulation.strategies.placement.cluster_placement import ClusterPlacementStrategy
from simulation.strategies.placement.anti_parity_placement import AntiParityPlacementStrategy
from simulation.strategies.placement.stealth_submarines import StealthSubmarinesPlacementStrategy
from simulation.strategies.placement.anti_probability import AntiProbabilityPlacementStrategy

__all__ = [
    "RandomPlacementStrategy",
    "BorderPlacementStrategy",
    "UniformPlacementStrategy",
    "ClusterPlacementStrategy",
    "AntiParityPlacementStrategy",
    "StealthSubmarinesPlacementStrategy",
    "AntiProbabilityPlacementStrategy",
]
