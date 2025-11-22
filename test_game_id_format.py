#!/usr/bin/env python3
"""
Test script to verify game ID format issue
"""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import asyncio
import logging
from arc_api_client import ARCClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_game_ids():
    """Test fetching full game IDs and creating a game."""
    try:
        client = ARCClient()
        
        async with client:
            # Get the full list of games with their complete IDs
            logger.info("Fetching game list...")
            games = await client.get_available_games()
            
            logger.info(f"Found {len(games)} games")
            for game in games[:5]:  # Show first 5
                logger.info(f"  Game: {game.get('game_id', 'N/A')}")
            
            # Find ft09 with full ID
            ft09_game = None
            for game in games:
                if game.get('game_id', '').startswith('ft09'):
                    ft09_game = game
                    break
            
            if ft09_game:
                full_game_id = ft09_game['game_id']
                logger.info(f"\n✓ Found ft09 with full ID: {full_game_id}")
                
                # Try creating a game with the FULL ID
                logger.info(f"\nTesting game creation with full ID...")
                game_data = await client.create_game(full_game_id, tags=["test", "debug"])
                logger.info(f"✓ SUCCESS! Game created: {game_data.get('game_id')}")
                logger.info(f"  State: {game_data.get('state')}")
                logger.info(f"  Score: {game_data.get('score')}")
                logger.info(f"  GUID: {game_data.get('guid')}")
            else:
                logger.error("Could not find ft09 game!")
                
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_game_ids())
