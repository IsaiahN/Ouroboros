import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
BitterTruth-AI - ARC-AGI-3 Evolution System

A clean, modular implementation for autonomous ARC-AGI-3 game playing.

Main Components:
- ArcadeWrapper: Official arc_agi SDK wrapper (arc_api_adapter.py)
- GameplayEngine: Core gameplay logic (core_gameplay.py)
- DatabaseInterface: Game data persistence

Example Usage:
    from arc_api_adapter import ArcadeWrapper, GameAction

    wrapper = ArcadeWrapper()
    env = wrapper.make("ls20")
    obs = env.step(GameAction.ACTION1)
"""

# Handle both package imports and direct execution
try:
    # When imported as a package
    from .arc_api_adapter import (
        ArcadeWrapper,
        GameConfig,
        GameEnvironment,
        GameInfo,
        Observation,
    )
    from .core_gameplay import (
        GameplayEngine,
        conservative_strategy,
        exploration_strategy,
        random_strategy,
    )
    from .database_interface import DatabaseInterface
except ImportError:
    # When run directly or imported from a script in the same directory
    pass

__version__ = "2.0.0"
__author__ = "Tabula Rasa Team"

__all__ = [
    # Core classes (arc_api_adapter - official SDK wrapper)
    "ArcadeWrapper",
    "GameConfig",
    "GameEnvironment",
    "GameInfo",
    "Observation",

    # Database
    "DatabaseInterface",

    # Gameplay
    "GameplayEngine",

    # Strategies
    "random_strategy",
    "conservative_strategy",
    "exploration_strategy",
]
