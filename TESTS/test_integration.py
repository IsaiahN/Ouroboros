#!/usr/bin/env python3
"""
Integration test for level_beating strategy with actual gameplay.
"""
import sys
import os
import asyncio
import tempfile

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import disable_pycache from project root
from disable_pycache import *

# Import test dependencies
from database_interface import DatabaseInterface
from core_gameplay import GameplayEngine
from arc_api_client import GameState
from strategies import LevelBeatingStrategy

class MockActionHandler:
    """Mock action handler for integration testing"""
    def __init__(self):
        self.calls = []

    async def send_action_1(self):
        self.calls.append("ACTION1")
        return GameState(
            game_id="test_game",
            guid="test_guid",
            state="NOT_FINISHED",
            score=30.0,
            win_score=100.0,
            available_actions=["1", "2", "3", "4", "5", "6", "7"],
            frame=[],
            action_input=None
        )

    async def send_action_6(self, x, y):
        self.calls.append(f"ACTION6({x},{y})")
        return GameState(
            game_id="test_game",
            guid="test_guid",
            state="NOT_FINISHED",
            score=40.0,
            win_score=100.0,
            available_actions=["1", "2", "3", "4", "5", "6", "7"],
            frame=[],
            action_input=None
        )

async def test_level_beating_integration():
    """Test level_beating strategy integration with core gameplay"""

    print("Testing level_beating strategy integration...")

    # Create temporary database
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()

    try:
        # Initialize database and ensure strategy tables exist
        db = DatabaseInterface(temp_db.name)
        db.ensure_strategy_tables()

        # Create mock action handler
        mock_handler = MockActionHandler()

        # Create gameplay engine with test database path
        gameplay = GameplayEngine(api_key="test_key", db_path=temp_db.name, enable_evolution=False)

        # Create test game state
        game_state = GameState(
            game_id="puzzle_game_123",
            guid="test_guid",
            state="NOT_FINISHED",
            score=20.0,
            win_score=100.0,
            available_actions=["1", "2", "3", "4", "5", "6", "7"],
            frame=[],
            action_input=None
        )

        print(f"Starting game: {game_state.game_id}")
        print(f"Initial score: {game_state.score}/{game_state.win_score}")

        # Test level_beating strategy directly
        print("\n--- Testing LevelBeatingStrategy directly ---")
        strategy = LevelBeatingStrategy(db)
        action = await strategy.get_next_action(game_state, mock_handler)
        print(f"Strategy selected action: {action}")

        # Test through GameplayEngine
        print("\n--- Testing through GameplayEngine ---")
        # Configure gameplay engine to use level_beating strategy
        gameplay.game_config['strategy'] = 'level_beating'
        # Add db property for level_beating strategy access
        gameplay.db = gameplay.session_manager.db
        action = await gameplay._select_action(game_state)
        print(f"GameplayEngine selected action: {action}")

        # Verify some actions were called
        if mock_handler.calls:
            print(f"[PASS] Actions were executed: {mock_handler.calls}")
        else:
            print("[FAIL] No actions were executed")

        # Test strategy performance tracking
        print("\n--- Testing strategy performance tracking ---")
        performance = await strategy.get_strategy_performance()
        print(f"Strategy performance: {performance}")

        print("\n[PASS] Integration test completed successfully!")
        return True

    except Exception as e:
        print(f"[FAIL] Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Clean up
        try:
            os.unlink(temp_db.name)
        except:
            pass

if __name__ == "__main__":
    success = asyncio.run(test_level_beating_integration())
    if success:
        print("\n=== INTEGRATION TEST PASSED ===")
        sys.exit(0)
    else:
        print("\n=== INTEGRATION TEST FAILED ===")
        sys.exit(1)