"""
Terminal Pattern Detection - Submodules
========================================

Split from terminal_pattern_detector.py for maintainability.

Modules:
- death_zones: Spatial danger region tracking
- dangerous_objects: Color/pattern-based danger detection
- game_over_theory: Human-readable failure hypothesis generation
"""

from engines.perception.terminal.death_zones import DeathZoneTracker
from engines.perception.terminal.dangerous_objects import DangerousObjectTracker
from engines.perception.terminal.game_over_theory import GameOverTheoryGenerator

__all__ = [
    'DeathZoneTracker',
    'DangerousObjectTracker', 
    'GameOverTheoryGenerator',
]
