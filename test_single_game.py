#!/usr/bin/env python3
"""
Single Game Test - Minimal script to test one game with detailed logging
"""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import asyncio
import logging
from database_logger import setup_database_logging
from core_gameplay import GameplayEngine
from arc_api_client import ARCClient

# Setup logging to console for immediate visibility
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def get_full_game_id(short_id: str) -> str:
    """Fetch full game ID from ARC API using short prefix."""
    client = ARCClient()
    async with client:
        games = await client.get_available_games()
        for game in games:
            if game.get('game_id', '').startswith(short_id):
                return game['game_id']
    raise ValueError(f"Game {short_id} not found in available games")

async def test_single_game():
    """Play a single game with verbose logging."""
    try:
        logger.info("=" * 80)
        logger.info("STARTING SINGLE GAME TEST")
        logger.info("=" * 80)
        
        # CRITICAL FIX: Fetch full game ID from API
        short_id = "ft09"
        full_game_id = await get_full_game_id(short_id)
        logger.info(f"Fetched full game ID: {full_game_id}")
        
        # Initialize engine
        engine = GameplayEngine(db_path="core_data.db")
        
        # Configure for one game
        engine.game_config = {
            'max_total_actions': 50,  # Low limit for quick test
            'max_actions_per_level': 25,
            'enable_pattern_learning': False,  # Disable to avoid sequence complexity
            'agent_operating_mode': 'pioneer'  # Simple mode
        }
        
        # Play one game WITH FULL ID
        logger.info(f"Playing game: {full_game_id}")
        
        result = await engine.play_single_game(
            game_id=full_game_id,  # Use FULL game ID
            agent_id=None,
            action_callback=None
        )
        
        logger.info("=" * 80)
        logger.info("GAME RESULT:")
        logger.info(f"  Game ID: {result['game_id']}")
        logger.info(f"  Final State: {result['final_state']}")
        logger.info(f"  Final Score: {result['final_score']}")
        logger.info(f"  Actions Taken: {result['actions_taken']}")
        logger.info(f"  Method: {result.get('method', 'N/A')}")
        logger.info("=" * 80)
        
        return result
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    result = asyncio.run(test_single_game())
    print(f"\n[SUCCESS] Test complete: {result['actions_taken']} actions taken")
