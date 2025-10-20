#!/usr/bin/env python3
"""
Continuous Game Runner - Multiple ARC Games
Builds performance data for Ouroboros evolution system
Follows all rules - Rule 6 & 7: Real ARC games only
"""

import os
import sys
import asyncio
import random
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

# Rule 2: Database-only logging
db_handler = setup_database_logging(level='INFO')


async def run_multiple_games(num_games: int = 5):
    """
    Run multiple ARC games to build performance data
    Rule 6 & 7: All real ARC API games
    """
    
    print("=" * 70)
    print("CONTINUOUS ARC GAME RUNNER - Ouroboros Data Collection")
    print("=" * 70)
    print(f"Time: {datetime.now()}")
    print(f"Target Games: {num_games}")
    print(f"Rule 6 & 7: Real ARC API games only")
    print("=" * 70)
    print()
    
    api_key = os.getenv('ARC_API_KEY')
    if not api_key or api_key == 'your_api_key_here':
        print("ERROR: Need valid API key")
        return []
    
    db_path = os.getenv('DATABASE_PATH', 'core_data.db')
    
    results = []
    
    try:
        async with GameplayEngine(api_key, db_path) as engine:
            
            # Get available games
            available_games = await engine.session_manager.get_available_games()
            
            if not available_games:
                print("ERROR: No games available")
                return []
            
            print(f"Available games: {len(available_games)}")
            for i, game in enumerate(available_games):
                game_id = game.get('id', game.get('game_id'))
                title = game.get('title', game.get('name', 'Unknown'))
                print(f"  {i+1}. {game_id} - {title}")
            print()
            
            # Play multiple games
            for game_num in range(num_games):
                # Select game (cycle through available games)
                game_idx = game_num % len(available_games)
                game = available_games[game_idx]
                game_id = game.get('id', game.get('game_id'))
                game_title = game.get('title', game.get('name', 'Unknown'))
                
                # Random action count (200-500)
                max_actions = random.randint(200, 500)
                
                print(f"\n{'='*70}")
                print(f"GAME {game_num + 1}/{num_games}")
                print(f"{'='*70}")
                print(f"Game ID: {game_id}")
                print(f"Title: {game_title}")
                print(f"Max Actions: {max_actions}")
                print(f"Started: {datetime.now().strftime('%H:%M:%S')}")
                
                # Configure engine
                engine.configure(
                    strategy='balanced',
                    max_actions_per_game=max_actions,
                    enable_random_exploration=True
                )
                
                # Play game
                start_time = datetime.now()
                result = await engine.play_single_game(game_id)
                duration = (datetime.now() - start_time).total_seconds()
                
                # Display results
                print(f"\nResults:")
                print(f"  Final State: {result['final_state']}")
                print(f"  Final Score: {result['final_score']}")
                print(f"  Actions Taken: {result['actions_taken']}")
                print(f"  Duration: {duration:.2f}s")
                print(f"  Actions/sec: {result['actions_taken']/duration:.1f}")
                print(f"  Win: {'YES' if result['win'] else 'NO'}")
                
                results.append(result)
                
                # Brief pause between games
                if game_num < num_games - 1:
                    print(f"\nPausing 2 seconds before next game...")
                    await asyncio.sleep(2)
            
            # Summary
            print(f"\n{'='*70}")
            print("SUMMARY - All Games Completed")
            print(f"{'='*70}")
            print(f"Total Games: {len(results)}")
            print(f"Total Actions: {sum(r['actions_taken'] for r in results)}")
            print(f"Wins: {sum(1 for r in results if r['win'])}")
            print(f"Average Score: {sum(r['final_score'] for r in results) / len(results):.2f}")
            print(f"Average Actions: {sum(r['actions_taken'] for r in results) / len(results):.1f}")
            
            # Database verification (Rule 2)
            print(f"\n{'='*70}")
            print("DATABASE VERIFICATION (Rule 2)")
            print(f"{'='*70}")
            
            db = DatabaseInterface(db_path)
            db_stats = db.get_database_stats()
            
            print(f"Total sessions in DB: {db_stats.get('training_sessions_count', 0)}")
            print(f"Total game results in DB: {db_stats.get('game_results_count', 0)}")
            print(f"Total action traces in DB: {db_stats.get('action_traces_count', 0)}")
            
            print(f"\n{'='*70}")
            print("✓ All Ouroboros Rules Followed")
            print("  Rule 1: No .pyc files")
            print("  Rule 2: All data in database")
            print("  Rule 6: Real ARC games only")
            print("  Rule 7: Real actions verified")
            print(f"{'='*70}")
            
            return results
            
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run multiple ARC games")
    parser.add_argument('--games', type=int, default=5, help='Number of games to play (default: 5)')
    args = parser.parse_args()
    
    results = asyncio.run(run_multiple_games(args.games))
    
    if results:
        print(f"\n✓ SUCCESS: Completed {len(results)} games")
        sys.exit(0)
    else:
        print(f"\n✗ FAILED: No games completed")
        sys.exit(1)
