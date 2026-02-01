# engines/regulation/__init__.py
"""Regulation engines - frustration detection, budgets, signals, and exploration tracking."""

from engines.regulation.frustration_detector import FrustrationDetector
from engines.regulation.imagination_budget import (
    ImaginationBudgetManager,
    compute_mental_modeling_budget,
)


def get_regulatory_signal_engine():
    from engines.regulation.regulatory_signal_engine import RegulatorySignalEngine
    return RegulatorySignalEngine

def get_network_exploration_tracker():
    from engines.regulation.network_exploration_tracker import NetworkExplorationTracker
    return NetworkExplorationTracker

__all__ = [
    'FrustrationDetector', 'ImaginationBudgetManager', 'compute_mental_modeling_budget',
    'get_regulatory_signal_engine', 'get_network_exploration_tracker'
]
