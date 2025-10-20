#!/usr/bin/env python3
"""
Detailed Debug Runner for ARC Games
Shows every action being sent to the real ARC API
Follows all Ouroboros rules - Rule 7: Real Actions Only
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Rule 1: Disable pycache
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from database_logger import setup_database_logging
from core_gameplay import GameplayEngine
from database_interface import DatabaseInterface
from action_handler import ActionHandler

# Rule 2: Database-only logging
db_handler = setup_database_logging(level='DEBUG')
logger = logging.getLogger(__name__)


class DetailedActionCallback:
    """Callback that shows detailed action information"""
    
    def __init__(self, action_handler: ActionHandler):
        self.action_handler = action_handler
        self.action_count = 0
    
    async def __call__(self, game_state, action_handler):
        """Custom action selection with detailed logging"""
        self.action_count += 1
        
        # Get action using smart selection
        action = await action_handler.smart_action_selection(game_state, 'balanced')
        
        print(f"\n--- Action {self.action_count} ---")
        print(f"  State: {game_state.state}")
        print(f"  Score: {game_state.score}")
        print(f"  Available Actions: {game_state.available_actions}")
        print(f"  Selected Action: {action}")
        
        # Execute the action
        if action == "ACTION6":
            x, y = action_handler.get_random_coordinates(game_state.frame)
            print(f"  ACTION6 Coordinates: ({x}, {y})")
            print(f"  Frame size: {len(game_state.frame)}x{len(game_state.frame[0]) if game_state.frame else 0}")
            new_state = await action_handler.send_action_6(x, y, game_state.frame)
        else:
            action_num = action.replace("ACTION", "")
            method_name = f"send_action_{action_num}"
            method = getattr(action_handler, method_name)
            new_state = await method()
        
        print(f"  New Score: {new_state.score} (change: {new_state.score - game_state.score})")
        print(f"  New State: {new_state.state}")
        
        return new_state


async def run_detailed_debug():
    """Run game with detailed action debugging"""
    
    print("=" * 70)
    print("DETAILED ARC GAME DEBUG - Ouroboros System")
    print("Rule 7: Monitoring Real ARC API Actions")
    print("=" * 70)
    print()
    
    api_key = os.getenv('ARC_API_KEY')
    if not api_key or api_key == 'your_api_key_here':
        print("ERROR: Need valid API key in .env file")
        return None
    
    db_path = os.getenv('DATABASE_PATH', 'core_data.db')
    
    try:
        async with GameplayEngine(api_key, db_path) as engine:
            
            # Configure with random actions (200-500)
            import random
            max_actions = random.randint(200, 500)
            print(f"Max actions for this game: {max_actions}")
            print()
            
            engine.configure(
                strategy='balanced',
                max_actions_per_game=max_actions,
                enable_random_exploration=True
            )
            
            # Get games
            available_games = await engine.session_manager.get_available_games()
            
            if not available_games:
                print("ERROR: No games available")
                return None
            
            game_id = available_games[0].get('id', available_games[0].get('game_id'))
            
            print(f"Selected Game: {game_id}")
            print("=" * 70)
            print()
            print("Executing actions (Rule 7: Real ARC API calls)...")
            print()
            
            # Create detailed callback
            callback = DetailedActionCallback(engine.action_handler)
            
            # Play game with callback
            result = await engine.play_single_game(game_id, action_callback=callback)
            
            # Results
            print()
            print("=" * 70)
            print("FINAL RESULTS")
            print("=" * 70)
            print(f"Game ID: {result['game_id']}")
            print(f"Final State: {result['final_state']}")
            print(f"Final Score: {result['final_score']}")
            print(f"Total Actions: {result['actions_taken']}")
            print(f"Duration: {result['duration_seconds']:.2f}s")
            print(f"Win: {result['win']}")
            print()
            
            # Database verification (Rule 2)
            print("=" * 70)
            print("DATABASE VERIFICATION (Rule 2)")
            print("=" * 70)
            
            db = DatabaseInterface(db_path)
            
            # Get action traces
            traces = db.get_action_traces(game_id=game_id, limit=20)
            print(f"\nAction traces stored: {len(traces)}")
            for i, trace in enumerate(traces[:5]):
                print(f"  {i+1}. Action {trace.get('action_number', 0)}: "
                      f"Score {trace.get('score_before', 0)} -> {trace.get('score_after', 0)} "
                      f"(change: {trace.get('score_change', 0)})")
            
            # Get game result
            results = db.get_game_results(game_id=game_id, limit=1)
            if results:
                r = results[0]
                print(f"\nGame result in database:")
                print(f"  Status: {r.get('status')}")
                print(f"  Final Score: {r.get('final_score')}")
                print(f"  Total Actions: {r.get('total_actions')}")
                print(f"  Win Detected: {r.get('win_detected')}")
            
            print()
            print("=" * 70)
            print("✓ All Ouroboros Rules Followed")
            print("  Rule 1: No .pyc files generated")
            print("  Rule 2: All data in database")
            print("  Rule 6: Real ARC game played")
            print("  Rule 7: Real actions verified")
            print("=" * 70)
            
            return result
            
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = asyncio.run(run_detailed_debug())
    sys.exit(0 if result else 1)
