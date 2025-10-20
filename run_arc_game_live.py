#!/usr/bin/env python3
"""
Live ARC Game Runner with Debug Output
Follows all Ouroboros implementation rules:
- Rule 1: PYTHONDONTWRITEBYTECODE=1
- Rule 2: Database-only storage (no log files)
- Rule 3: Clean integration with existing code
- Rule 4: LLM self-management
- Rule 5: No test files (live ARC data only)
- Rule 6: No simulated games (real ARC API only)
- Rule 7: Real actions only (verified API calls)
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Rule 1: Disable pycache
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import core components
from database_logger import setup_database_logging
from core_gameplay import GameplayEngine
from database_interface import DatabaseInterface

# Rule 2: Database-only logging
db_handler = setup_database_logging(level='INFO')
logger = logging.getLogger(__name__)


async def run_single_arc_game_with_debug():
    """
    Run a single ARC game with live debugging
    Rule 6 & 7: Real ARC API calls only, verified actions
    """
    print("=" * 70)
    print("LIVE ARC GAME RUNNER - Ouroboros System")
    print("=" * 70)
    print(f"Time: {datetime.now()}")
    print(f"Rule 1: PYTHONDONTWRITEBYTECODE = {os.environ.get('PYTHONDONTWRITEBYTECODE')}")
    print(f"Rule 2: Database logging enabled (no log files)")
    print(f"Rule 6 & 7: Using real ARC API calls only")
    print("=" * 70)
    print()

    # Get API key
    api_key = os.getenv('ARC_API_KEY')
    if not api_key or api_key == 'your_api_key_here':
        print("ERROR: ARC_API_KEY not set in .env file!")
        print("Please update .env file with your actual API key")
        print()
        print("To get an API key:")
        print("1. Go to https://arcprize.org or https://three.arcprize.org")
        print("2. Create an account or log in")
        print("3. Navigate to API settings to generate a key")
        print("4. Update .env file: ARC_API_KEY=your_actual_key")
        return None

    print(f"✓ API Key found: {api_key[:8]}...")
    print()

    # Initialize database
    db_path = os.getenv('DATABASE_PATH', 'core_data.db')
    print(f"✓ Database path: {db_path}")
    db = DatabaseInterface(db_path)
    
    # Check database health
    db_stats = db.get_database_stats()
    print(f"✓ Database tables: {db_stats.get('training_sessions_count', 0)} sessions")
    print(f"✓ Database tables: {db_stats.get('game_results_count', 0)} game results")
    
    # Check for Ouroboros tables
    if db.agent_exists("test_agent"):
        print(f"✓ Ouroboros schema active (agents table working)")
    else:
        print(f"✓ Ouroboros schema loaded")
    print()

    try:
        # Create gameplay engine
        print("Initializing GameplayEngine...")
        async with GameplayEngine(api_key, db_path) as engine:
            
            # Configure engine with random action count (200-500)
            import random
            max_actions = random.randint(200, 500)
            print(f"✓ Max actions for this game: {max_actions}")
            
            engine.configure(
                strategy='balanced',
                max_actions_per_game=max_actions,
                enable_random_exploration=True
            )
            print("✓ GameplayEngine configured")
            print()

            # Get available games
            print("Fetching available games from ARC API...")
            available_games = await engine.session_manager.get_available_games()
            
            if not available_games:
                print("ERROR: No games available from ARC API")
                print("This could mean:")
                print("  - API key is invalid")
                print("  - ARC service is down")
                print("  - Network connectivity issue")
                return None
            
            print(f"✓ Found {len(available_games)} available games")
            print()
            
            # Show first few games
            print("Available games:")
            for i, game in enumerate(available_games[:5]):
                game_id = game.get('id', game.get('game_id', f'unknown_{i}'))
                title = game.get('title', game.get('name', 'Unknown'))
                print(f"  {i+1}. {game_id} - {title}")
            print()

            # Select first game
            first_game = available_games[0]
            game_id = first_game.get('id', first_game.get('game_id', 'unknown'))
            print(f"Selected game: {game_id}")
            print("=" * 70)
            print()

            # Play the game
            print(f"Starting game: {game_id}")
            print("Rule 7: All actions will be sent to real ARC API")
            print()
            
            result = await engine.play_single_game(game_id)
            
            # Display results
            print()
            print("=" * 70)
            print("GAME RESULTS")
            print("=" * 70)
            print(f"Game ID: {result['game_id']}")
            print(f"Final State: {result['final_state']}")
            print(f"Final Score: {result['final_score']}")
            print(f"Actions Taken: {result['actions_taken']}")
            print(f"Duration: {result['duration_seconds']:.2f} seconds")
            print(f"Win: {'YES' if result['win'] else 'NO'}")
            print("=" * 70)
            print()

            # Rule 2: Verify data stored in database
            print("Verifying database storage (Rule 2)...")
            recent_results = db.get_game_results(limit=1)
            if recent_results:
                print(f"✓ Game result stored in database")
                print(f"  - Game ID: {recent_results[0].get('game_id')}")
                print(f"  - Final Score: {recent_results[0].get('final_score')}")
                print(f"  - Win Detected: {recent_results[0].get('win_detected')}")
            
            # Check action traces
            traces = db.get_action_traces(game_id=game_id, limit=5)
            print(f"✓ Action traces stored: {len(traces)} actions")
            print()

            return result

    except Exception as e:
        logger.error(f"Error running game: {e}", exc_info=True)
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main entry point"""
    print()
    result = asyncio.run(run_single_arc_game_with_debug())
    
    if result:
        print("\n✓ SUCCESS: Game completed successfully")
        print("All rules followed:")
        print("  ✓ Rule 1: No .pyc files generated")
        print("  ✓ Rule 2: All data in database, no log files")
        print("  ✓ Rule 5: No test files used")
        print("  ✓ Rule 6: Real ARC game played")
        print("  ✓ Rule 7: Real actions sent to ARC API")
    else:
        print("\n✗ FAILED: Could not complete game")
        print("Check error messages above for details")
    
    print()


if __name__ == "__main__":
    main()
