"""
Example Usage Scripts

Demonstrates how to use the Core Game Mechanics module for various tasks.
"""

import asyncio
import os
import logging
from typing import Dict, Any

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, fall back to system environment variables
    pass

from . import GameplayEngine, ARCClient, GameSessionManager, ActionHandler
from . import random_strategy, conservative_strategy, exploration_strategy

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_single_game():
    """Example: Play a single game with default strategy."""
    print("=== Example: Single Game ===")

    api_key = os.getenv('ARC_API_KEY')
    if not api_key:
        print("Please set ARC_API_KEY environment variable")
        return

    async with GameplayEngine(api_key) as engine:
        # Configure engine
        engine.configure(
            max_actions_per_game=50,
            strategy='balanced'
        )

        # Play a single game
        result = await engine.play_single_game("game_001")

        print(f"Game completed!")
        print(f"Final state: {result['final_state']}")
        print(f"Final score: {result['final_score']}")
        print(f"Actions taken: {result['actions_taken']}")
        print(f"Duration: {result['duration_seconds']:.2f} seconds")


async def example_multiple_games():
    """Example: Play multiple games in sequence."""
    print("\n=== Example: Multiple Games ===")

    api_key = os.getenv('ARC_API_KEY')
    if not api_key:
        print("Please set ARC_API_KEY environment variable")
        return

    async with GameplayEngine(api_key) as engine:
        # Get available games
        available_games = await engine.session_manager.get_available_games()
        game_ids = [game.get('id', f'game_{i}') for i, game in enumerate(available_games[:3])]

        print(f"Playing {len(game_ids)} games...")

        # Play multiple games
        results = await engine.play_multiple_games(game_ids)

        # Show summary
        wins = sum(1 for r in results if r.get('win', False))
        total_score = sum(r['final_score'] for r in results)

        print(f"Results: {wins}/{len(results)} wins")
        print(f"Total score: {total_score}")
        print(f"Average score: {total_score / len(results):.2f}")


async def example_custom_strategy():
    """Example: Using a custom action selection strategy."""
    print("\n=== Example: Custom Strategy ===")

    api_key = os.getenv('ARC_API_KEY')
    if not api_key:
        print("Please set ARC_API_KEY environment variable")
        return

    async def custom_strategy(game_state, action_handler):
        """Custom strategy that prefers ACTION1 and ACTION2."""
        available = game_state.available_actions or ["ACTION1", "ACTION2", "ACTION3", "ACTION4", "ACTION5", "ACTION7"]

        # Prefer ACTION1 and ACTION2
        preferred = [a for a in available if a in ["ACTION1", "ACTION2"]]
        if preferred:
            return action_handler.get_random_action(preferred)
        else:
            return action_handler.get_random_action(available)

    async with GameplayEngine(api_key) as engine:
        result = await engine.play_single_game("game_001", custom_strategy)

        print(f"Custom strategy result:")
        print(f"Final state: {result['final_state']}")
        print(f"Final score: {result['final_score']}")


async def example_session_management():
    """Example: Manual session management."""
    print("\n=== Example: Session Management ===")

    api_key = os.getenv('ARC_API_KEY')
    if not api_key:
        print("Please set ARC_API_KEY environment variable")
        return

    # Manual session management
    session_manager = GameSessionManager(api_key)
    action_handler = ActionHandler(session_manager)

    try:
        # Start session
        session_id = await session_manager.start_session("manual_test")
        print(f"Started session: {session_id}")

        # Create a game
        game_data = await session_manager.create_game("manual_game_001")
        print(f"Created game: {game_data['game_id']}")

        # Send some actions
        for i in range(5):
            action = f"ACTION{(i % 5) + 1}"
            try:
                game_state = await action_handler.send_action_1() if i == 0 else await action_handler.send_action_2()
                print(f"Action {i+1}: {action} -> Score: {game_state.score}")

                if game_state.state != "NOT_FINISHED":
                    print(f"Game ended with state: {game_state.state}")
                    break
            except Exception as e:
                print(f"Action failed: {e}")
                break

        # Get session stats
        stats = session_manager.get_session_stats()
        print(f"Session stats: {stats}")

    finally:
        await session_manager.shutdown()


async def example_database_operations():
    """Example: Database operations and statistics."""
    print("\n=== Example: Database Operations ===")

    from .database_interface import DatabaseInterface

    db = DatabaseInterface("example_core_game_mechanics.db")

    try:
        # Create a test session
        session_id = db.create_session("example_session", "testing")
        print(f"Created session: {session_id}")

        # Save some test data
        db.save_game_result({
            'game_id': 'test_game_001',
            'session_id': session_id,
            'status': 'completed',
            'final_score': 85.5,
            'total_actions': 25,
            'win_detected': True
        })

        db.save_action_trace({
            'session_id': session_id,
            'game_id': 'test_game_001',
            'action_number': 1,
            'timestamp': '2024-01-01 12:00:00',
            'score_before': 0.0,
            'score_after': 10.0,
            'score_change': 10.0
        })

        # Update action effectiveness
        db.update_action_effectiveness('test_game_001', 1, True, 10.0)

        # Get statistics
        db_stats = db.get_database_stats()
        print("Database statistics:")
        for key, value in db_stats.items():
            print(f"  {key}: {value}")

        # Get game results
        game_results = db.get_game_results(session_id=session_id)
        print(f"\nFound {len(game_results)} game results")

        # End session
        db.end_session(session_id)

    finally:
        db.close()


async def example_direct_api_usage():
    """Example: Direct API client usage."""
    print("\n=== Example: Direct API Usage ===")

    api_key = os.getenv('ARC_API_KEY')
    if not api_key:
        print("Please set ARC_API_KEY environment variable")
        return

    async with ARCClient(api_key) as client:
        # Get available games
        games = await client.get_available_games()
        print(f"Available games: {len(games)}")

        if games:
            # Create a game
            game_id = games[0].get('id', 'test_game')
            game_data = await client.create_game(game_id)

            print(f"Created game: {game_data['game_id']}")
            print(f"Initial score: {game_data['score']}")

            # Send a few actions
            for i in range(3):
                try:
                    game_state = await client.send_action(f"ACTION{i+1}")
                    print(f"Action {i+1}: Score = {game_state.score}, State = {game_state.state}")

                    if game_state.state != "NOT_FINISHED":
                        break
                except Exception as e:
                    print(f"Action failed: {e}")
                    break

            # Close scorecard
            if client.current_scorecard_id:
                await client.close_scorecard()


async def run_all_examples():
    """Run all examples."""
    examples = [
        example_single_game,
        example_multiple_games,
        example_custom_strategy,
        example_session_management,
        example_database_operations,
        example_direct_api_usage
    ]

    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"Example failed: {e}")
        print()


def main():
    """Main function to run examples."""
    print("Core Game Mechanics - Example Usage")
    print("====================================")

    # Check for API key
    if not os.getenv('ARC_API_KEY'):
        print("Note: Some examples require ARC_API_KEY environment variable")
        print("Only database examples will run without API key")
        print()

    asyncio.run(run_all_examples())


if __name__ == "__main__":
    main()