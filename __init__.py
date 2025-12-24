import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
Core Game Mechanics

A clean, modular implementation of essential ARC-AGI-3 game functionality.
Contains only the core mechanics needed to play games without the complexity
of architect, governor, or director systems.

Main Components:
- ARCClient: API client for ARC-AGI-3
- GameSessionManager: Session lifecycle management
- ActionHandler: Action sending and validation
- GameplayEngine: Core gameplay logic
- DatabaseInterface: Game data persistence

Example Usage:
    from CORE_GAME_MECHANICS import GameplayEngine

    async def play_game():
        async with GameplayEngine(api_key="your_key") as engine:
            result = await engine.play_single_game("game_123")
            print(f"Final score: {result['final_score']}")

    asyncio.run(play_game())
"""

# Handle both package imports and direct execution
try:
    # When imported as a package (e.g., from BitterTruth-AI import ...)
    from .arc_api_client import ARCClient, GameState, Scorecard, ARCError, ARCAuthenticationError, ARCAPIError
    from .database_interface import DatabaseInterface
    from .game_session_manager import GameSessionManager, SessionContext
    from .action_handler import ActionHandler
    from .core_gameplay import GameplayEngine, random_strategy, conservative_strategy, exploration_strategy
except ImportError:
    # When run directly or imported from a script in the same directory
    # This prevents pytest from failing when it tries to import this file
    pass

__version__ = "1.0.0"
__author__ = "Tabula Rasa Team"

__all__ = [
    # Core classes
    "ARCClient",
    "GameState",
    "Scorecard",
    "DatabaseInterface",
    "GameSessionManager",
    "SessionContext",
    "ActionHandler",
    "GameplayEngine",

    # Strategies
    "random_strategy",
    "conservative_strategy",
    "exploration_strategy",

    # Exceptions
    "ARCError",
    "ARCAuthenticationError",
    "ARCAPIError",
]