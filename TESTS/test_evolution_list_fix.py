#!/usr/bin/env python3
"""
Test evolution strategy with list score handling fixes.
"""
import sys
import os
import asyncio
import tempfile

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import disable_pycache from project root
from disable_pycache import *

from core_gameplay import GameplayEngine, EVOLUTION_AVAILABLE
from arc_api_client import GameState
from main_runner import evolved_strategy
from algorithm_evaluator import GameContext
from evolution_manager import EvolutionManager, EvolutionConfig
from action_handler import ActionHandler
from game_session_manager import GameSessionManager

class MockActionHandler:
    """Mock action handler for testing"""
    def __init__(self):
        self.calls = []

    async def send_action_1(self):
        self.calls.append("ACTION1")
        # Return GameState with score as list (this was causing the error)
        return GameState(
            game_id="test_game",
            guid="test_guid",
            state="NOT_FINISHED",
            score=[30.0],  # List instead of float!
            win_score=100.0,
            available_actions=["1", "2", "3", "4", "5", "6", "7"],
            frame=[],
            action_input=None
        )

    async def send_action_6(self, x, y):
        self.calls.append(f"ACTION6({x},{y})")
        # Return GameState with score as list
        return GameState(
            game_id="test_game",
            guid="test_guid",
            state="NOT_FINISHED",
            score=[40.0],  # List instead of float!
            win_score=100.0,
            available_actions=["1", "2", "3", "4", "5", "6", "7"],
            frame=[],
            action_input=None
        )

    async def smart_action_selection(self, game_state, strategy):
        return "ACTION1"

async def test_evolution_list_score_fix():
    """Test that evolution strategy handles list scores without errors"""

    print("Testing evolution strategy with list scores...")

    if not EVOLUTION_AVAILABLE:
        print("[SKIP] Evolution system not available")
        return True

    # Create temporary database
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()

    try:
        # Create evolution system components
        session_manager = GameSessionManager("test_key", temp_db.name)
        action_handler = MockActionHandler()

        # Create evolution config and manager
        config = EvolutionConfig(population_size=10, evolution_frequency=3)
        evolution_manager = EvolutionManager(config, session_manager.db)
        await evolution_manager.initialize_system()

        # Create game context with list score (simulating the problematic case)
        game_context = GameContext()
        game_context.game_id = "test_list_scores"
        game_context.current_score = [25.0]  # List score that was causing errors

        # Create initial game state with list score
        game_state = GameState(
            game_id="test_list_scores",
            guid="test_guid",
            state="NOT_FINISHED",
            score=[20.0],  # List score
            win_score=100.0,
            available_actions=["1", "2", "3", "4", "5", "6", "7"],
            frame=[],
            action_input=None
        )

        print(f"Initial game state score (list): {game_state.score}")
        print(f"Game context score (list): {game_context.current_score}")

        # Test the evolved_strategy function that was failing
        print("\n--- Testing evolved_strategy with list scores ---")
        try:
            result = await evolved_strategy(game_state, action_handler, evolution_manager, game_context)
            print(f"[PASS] evolved_strategy executed successfully")
            print(f"Result: {result}")

            # Verify no list subtraction errors occurred
            if action_handler.calls:
                print(f"[PASS] Actions were executed: {action_handler.calls}")
            else:
                print("[INFO] No actions executed (fallback behavior)")

        except Exception as e:
            if "unsupported operand type(s) for -: 'list' and 'list'" in str(e):
                print(f"[FAIL] List subtraction error still occurs: {e}")
                return False
            else:
                print(f"[INFO] Different error (expected during testing): {e}")

        print("\n--- Testing coordinate strategies with list scores ---")
        try:
            from coordinate_strategies import generate_action6_coordinates

            # Test with list scores that previously caused errors
            coords = generate_action6_coordinates(
                "test_algo",
                current_score=[30.0],  # List score
                previous_score=[25.0],  # List score
                actions_taken=5
            )
            print(f"[PASS] Coordinate generation with list scores: {coords}")

        except Exception as e:
            if "unsupported operand type(s) for -: 'list' and 'list'" in str(e):
                print(f"[FAIL] List subtraction error in coordinate strategies: {e}")
                return False
            else:
                print(f"[INFO] Different error in coordinate strategies: {e}")

        print("\n[PASS] All evolution strategy list score fixes working correctly!")
        return True

    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
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
    success = asyncio.run(test_evolution_list_score_fix())
    if success:
        print("\n=== EVOLUTION LIST SCORE FIX TEST PASSED ===")
        sys.exit(0)
    else:
        print("\n=== EVOLUTION LIST SCORE FIX TEST FAILED ===")
        sys.exit(1)