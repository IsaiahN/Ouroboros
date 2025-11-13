#!/usr/bin/env python3
"""
Quick Game Starter Script for BitterTruth-AI

Standalone script to start a game without module import issues.
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import asyncio
import sys
import logging

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, fall back to system environment variables
    pass

# Import local modules directly
import arc_api_client
import game_session_manager
import action_handler
import database_interface
import core_gameplay

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def start_single_game():
    """Start and play a single game."""
    print("=== BitterLesson-AI Game Starter ===")
    print()

    # Get API key from environment
    api_key = os.getenv('ARC_API_KEY')
    if not api_key:
        print("ERROR: ARC_API_KEY not found in .env file")
        print("Please check your .env file and ensure ARC_API_KEY is set")
        return

    print(f"Using API key: {api_key[:8]}...")
    print()

    try:
        # Create ARC client
        client = arc_api_client.ARCClient(api_key)

        # Get available games
        print("Fetching available games...")
        games = await client.get_available_games()

        if not games:
            print("No games available")
            return

        print(f"Found {len(games)} available games:")
        for i, game in enumerate(games[:5]):  # Show first 5
            game_id = game.get('id', f'game_{i}')
            title = game.get('title', 'Unknown Game')
            print(f"  {i+1}. {game_id} - {title}")

        # Use the first available game
        first_game_id = games[0].get('id', 'game_0')
        print(f"\nStarting game: {first_game_id}")
        print("=" * 50)

        # Create session manager and start session
        session_manager = game_session_manager.GameSessionManager(client)
        session_id = await session_manager.start_session()
        print(f"Started session: {session_id}")

        # Create game
        game_data = await session_manager.create_game(first_game_id)
        print(f"Created game with scorecard: {game_data.scorecard.guid}")

        # Create action handler
        action_handler_instance = action_handler.ActionHandler(session_manager)

        # Play some actions
        print("\nPlaying game...")
        game_state = game_data.game_state
        actions_taken = 0
        max_actions = 10

        while game_state.state == "NOT_FINISHED" and actions_taken < max_actions:
            print(f"Action {actions_taken + 1}: Score = {game_state.score}")

            # Try ACTION1 first
            try:
                game_state = await action_handler_instance.send_action_1()
                actions_taken += 1

                if game_state.state != "NOT_FINISHED":
                    break

            except Exception as e:
                print(f"Action failed: {e}")
                break

        # Finish the game
        await session_manager.finish_game(game_state.state, game_state.score)

        print("\n=== GAME COMPLETED ===")
        print(f"Game ID: {first_game_id}")
        print(f"Final State: {game_state.state}")
        print(f"Final Score: {game_state.score}")
        print(f"Actions Taken: {actions_taken}")
        print(f"Win: {game_state.state == 'WIN'}")

        # Shutdown session
        await session_manager.shutdown()

    except Exception as e:
        print(f"Error starting game: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(start_single_game())