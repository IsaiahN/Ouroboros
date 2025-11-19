"""
Minimal reproduction script for 0 actions bug.
Runs a single game using GameplayEngine to see if actions are taken.
Updated to fetch available games dynamically.
"""
import asyncio
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.append(os.getcwd())

from core_gameplay import GameplayEngine
from arc_api_client import ARCClient

async def run_test():
    print("🚀 Starting minimal game loop test...")
    
    try:
        # Initialize engine
        engine = GameplayEngine()
        print("✅ Engine initialized")
        
        # Get a valid game ID
        async with ARCClient() as client:
            games = await client.get_available_games()
            if not games:
                print("❌ No games available!")
                return
            
            first_game = games[0]
            if isinstance(first_game, dict):
                game_id = first_game.get('id') or first_game.get('game_id')
            else:
                game_id = first_game
                
        print(f"🎮 Playing game {game_id}...")
        result = await engine.play_single_game(game_id, agent_id="test_agent_001")
        
        print("\n📊 Game Result:")
        print(f"  State: {result.get('final_state')}")
        print(f"  Score: {result.get('final_score')}")
        print(f"  Actions: {result.get('actions_taken')}")
        print(f"  Levels: {result.get('level_completions')}")
        
        if result.get('actions_taken') == 0:
            print("\n❌ FAILURE: 0 actions taken!")
        else:
            print("\n✅ SUCCESS: Actions were taken.")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_test())
