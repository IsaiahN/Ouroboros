#!/usr/bin/env python3
"""
BitterLesson-AI Unified Game Runner

A comprehensive ARC-AGI-3 game runner that:
- Opens scorecard with BitterLesson tags
- Starts a game
- Executes 10 random actions
- Closes the game and scorecard

This serves as a foundation for more sophisticated gameplay logic.
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import asyncio
import subprocess
import platform
import random
from datetime import datetime
import aiohttp
import logging

# Configure database logging
from database_logger import setup_database_logging

# Set up database logging instead of file logging
db_handler = setup_database_logging()
logger = logging.getLogger(__name__)

def load_env():
    """Load .env file manually."""
    try:
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    except FileNotFoundError:
        logger.warning("Warning: .env file not found")

def generate_bitterlesson_tags():
    """Generate tags including BitterLesson, git branch, and commit ID."""
    tags = ["BitterLesson"]

    # Add Git information
    try:
        # Get current git branch
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5
        )
        if branch_result.returncode == 0:
            branch_name = branch_result.stdout.strip()
            tags.append(f"branch_{branch_name}")

        # Get last commit ID (short hash)
        commit_result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5
        )
        if commit_result.returncode == 0:
            commit_id = commit_result.stdout.strip()
            tags.append(f"commit_{commit_id}")
    except:
        tags.append("git_unavailable")

    # Add runtime info
    tags.append(f"pid_{os.getpid()}")
    tags.append(f"ts_{datetime.now().strftime('%H%M%S')}")
    tags.append(f"sys_{platform.system().lower()}")

    return tags

async def send_random_action(session, base_url, headers, game_id, guid, available_actions):
    """Send a random action to the game."""
    if not available_actions:
        logger.warning("No available actions")
        return None

    # Choose random action from available ones
    action_num = random.choice(available_actions)
    action_name = f"ACTION{action_num}"

    # Build request payload
    payload = {
        "game_id": game_id,
        "guid": guid,
        "reasoning": {"policy": f"BitterLesson_random_{action_name}"}
    }

    # ACTION6 needs coordinates
    if action_num == 6:
        payload["x"] = random.randint(0, 63)
        payload["y"] = random.randint(0, 63)
        logger.info(f"Sending {action_name} at ({payload['x']}, {payload['y']})")
    else:
        logger.info(f"Sending {action_name}")

    try:
        async with session.post(f"{base_url}/api/cmd/{action_name}",
                              headers=headers, json=payload) as response:
            if response.status != 200:
                text = await response.text()
                logger.error(f"Error sending {action_name}: {response.status} - {text}")
                return None

            return await response.json()
    except Exception as e:
        logger.error(f"Exception sending {action_name}: {e}")
        return None

async def run_complete_game():
    """Run a complete game session with random actions."""
    # Load environment
    load_env()

    logger.info("=== BitterLesson-AI Unified Game Runner ===")

    # Configuration
    api_key = os.getenv('ARC_API_KEY')
    base_url = os.getenv('ARC_BASE_URL', 'https://three.arcprize.org')

    if not api_key:
        logger.error("ERROR: ARC_API_KEY not found in .env file")
        return

    logger.info(f"API Key: {api_key[:8]}...")
    logger.info(f"Base URL: {base_url}")

    # Generate tags
    tags = generate_bitterlesson_tags()
    logger.info(f"Generated tags: {tags}")

    headers = {
        "X-API-Key": api_key,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        try:
            # Step 1: Get available games
            logger.info("STEP 1: Getting available games...")
            async with session.get(f"{base_url}/api/games", headers=headers) as response:
                if response.status != 200:
                    text = await response.text()
                    logger.error(f"Error getting games: {response.status} - {text}")
                    return

                games_data = await response.json()
                if not games_data:
                    logger.error("No games available")
                    return

                logger.info(f"Found {len(games_data)} games")
                for i, game in enumerate(games_data[:3]):  # Show first 3
                    game_id = game.get('game_id', f'game_{i}')
                    logger.info(f"  {i+1}. {game_id}")

                # Use the first game
                selected_game = games_data[0]
                game_id = selected_game.get('game_id')
                logger.info(f"Selected game: {game_id}")

            # Step 2: Open scorecard
            logger.info("STEP 2: Opening scorecard with BitterLesson tags...")
            scorecard_payload = {"tags": tags}

            async with session.post(f"{base_url}/api/scorecard/open",
                                  headers=headers, json=scorecard_payload) as response:
                if response.status != 200:
                    text = await response.text()
                    logger.error(f"Error opening scorecard: {response.status} - {text}")
                    return

                scorecard_data = await response.json()
                card_id = scorecard_data.get('card_id')
                logger.info(f"Scorecard opened: {card_id}")

            # Step 3: Start the game
            logger.info("STEP 3: Starting game with RESET...")
            reset_payload = {"game_id": game_id, "card_id": card_id}

            async with session.post(f"{base_url}/api/cmd/RESET",
                                  headers=headers, json=reset_payload) as response:
                if response.status != 200:
                    text = await response.text()
                    logger.error(f"Error starting game: {response.status} - {text}")
                    return

                game_data = await response.json()
                guid = game_data.get('guid')
                state = game_data.get('state')
                score = game_data.get('score', 0)
                win_score = game_data.get('win_score', 0)
                available_actions = game_data.get('available_actions', [])

                logger.info(f"Game started - GUID: {guid}")
                logger.info(f"Initial state: {state}, Score: {score}/{win_score}")
                logger.info(f"Available actions: {available_actions}")

            # Step 4: Execute 10 random actions
            logger.info("STEP 4: Executing 10 random actions...")

            current_state = state
            current_score = score
            current_available = available_actions
            actions_completed = 0

            for action_num in range(1, 11):  # 10 actions
                if current_state in ["WIN", "GAME_OVER"]:
                    logger.info(f"Game ended early at action {action_num}: {current_state}")
                    break

                if not current_available:
                    logger.warning(f"No available actions at step {action_num}")
                    break

                logger.info(f"--- Action {action_num}/10 ---")
                logger.info(f"Current state: {current_state}, Score: {current_score}")

                # Send random action
                result = await send_random_action(
                    session, base_url, headers, game_id, guid, current_available
                )

                if result:
                    current_state = result.get('state', current_state)
                    current_score = result.get('score', current_score)
                    current_available = result.get('available_actions', current_available)

                    logger.info(f"Result: {current_state}, Score: {current_score}")
                    logger.info(f"New available actions: {current_available}")
                    actions_completed += 1
                else:
                    logger.error(f"Failed to execute action {action_num}")
                    break

                # Small delay between actions
                await asyncio.sleep(0.5)

            # Step 5: Close scorecard
            logger.info("STEP 5: Closing scorecard...")
            close_payload = {"card_id": card_id}

            async with session.post(f"{base_url}/api/scorecard/close",
                                  headers=headers, json=close_payload) as response:
                if response.status != 200:
                    text = await response.text()
                    logger.error(f"Error closing scorecard: {response.status} - {text}")
                else:
                    logger.info("Scorecard closed successfully!")
                    logger.info(f"View results at: {base_url}/scorecards/{card_id}")

            # Final summary
            logger.info("=== GAME SESSION COMPLETE ===")
            logger.info(f"Game: {game_id}")
            logger.info(f"Final state: {current_state}")
            logger.info(f"Final score: {current_score}")
            logger.info(f"Actions completed: {actions_completed}/10")
            logger.info(f"Scorecard: {card_id}")

            return {
                "game_id": game_id,
                "final_state": current_state,
                "final_score": current_score,
                "actions_completed": actions_completed,
                "scorecard_id": card_id
            }

        except Exception as e:
            logger.error(f"Error during game session: {e}")
            import traceback
            traceback.print_exc()
            return None

if __name__ == "__main__":
    result = asyncio.run(run_complete_game())
    if result:
        print(f"\nSUCCESS: Game completed with {result['actions_completed']} actions")
    else:
        print("\nFAILED: Game session encountered errors")