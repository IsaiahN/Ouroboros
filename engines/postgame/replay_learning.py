import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
Replay Learning - Learn WHY Sequences Work
==========================================

This is a re-export of the replay learning engine for the postgame module.
The full implementation remains in engines/planning/replay_learning_engine.py
since replay learning can also happen during active play (not just post-game).

However, the postgame module provides access to it since post-game analysis
is a key time to process replays.

The ReplayLearningEngine enables agents to:
- Generate predictions BEFORE each replay action
- Compare predictions to actual outcomes
- Induce rules and primitives from prediction/outcome comparisons
- Identify wasted actions (optimizer signal)
- Store learning events for network synthesis

Following Rules:
- Rule 3: No orphaned code (re-export, not duplicate)
- Rule 10: Enhance existing architecture
"""

# Re-export from the full implementation
from engines.planning.replay_learning_engine import (
    ReplayLearningEngine,
    ReplayLearningContext,
    ReplayPrediction,
)

# Alias for consistency with postgame module naming
ReplayLearner = ReplayLearningEngine

__all__ = [
    'ReplayLearner',
    'ReplayLearningEngine',
    'ReplayLearningContext',
    'ReplayPrediction',
]
