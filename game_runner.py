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

import asyncio
import os
import subprocess
import platform
import random
from datetime import datetime
import aiohttp
import logging

# Configure database logging
from database_logger import setup_database_logging

# Import evolution system components
try:
    from evolution_manager import EvolutionManager, EvolutionConfig
    from algorithm_evaluator import AlgorithmEvaluator, GameContext
    from database_interface import DatabaseInterface
    EVOLUTION_AVAILABLE = True
    logger.info("Evolution system components loaded successfully")
except ImportError as e:
    logger.warning(f"Evolution system not available: {e}")
    EvolutionManager = None
    AlgorithmEvaluator = None
    GameContext = None
    DatabaseInterface = None
    EVOLUTION_AVAILABLE = False

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

async def send_evolved_action(session, base_url, headers, game_id, guid,
                            available_actions, evolution_manager, game_context):
    """Send an action selected by the evolved algorithm system."""
    if not available_actions:
        logger.warning("No available actions")
        return None

    action_name = None
    coordinates = None
    reasoning_policy = "BitterLesson_random_fallback"

    # Try to use evolved algorithm
    if EVOLUTION_AVAILABLE and evolution_manager:
        try:
            # Get current algorithm
            current_algorithm = await evolution_manager.get_current_algorithm()

            if current_algorithm:
                # Update game context
                game_context.available_actions = available_actions

                # Evaluate algorithm to get action
                evaluator = AlgorithmEvaluator()
                result = evaluator.evaluate_algorithm(current_algorithm, game_context)

                action_name = result.action
                coordinates = result.coordinates
                reasoning_policy = f"BitterLesson_evolved_{current_algorithm.algorithm_id}_{result.confidence:.2f}"

                logger.info(f"Evolved algorithm selected: {action_name} (confidence: {result.confidence:.2f})")
            else:
                logger.warning("No current algorithm available, using random fallback")

        except Exception as e:
            logger.error(f"Error in evolved action selection: {e}")

    # Fallback to random action if evolution failed
    if not action_name:
        action_num = random.choice(available_actions)
        action_name = f"ACTION{action_num}"
        if action_num == 6:
            coordinates = {"x": random.randint(0, 63), "y": random.randint(0, 63)}

    # Build request payload
    payload = {
        "game_id": game_id,
        "guid": guid,
        "reasoning": {"policy": reasoning_policy}
    }

    # Add coordinates for ACTION6
    if action_name == "ACTION6" and coordinates:
        payload["x"] = coordinates["x"]
        payload["y"] = coordinates["y"]
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


async def send_random_action(session, base_url, headers, game_id, guid, available_actions):
    """Send a random action to the game. (Legacy function for fallback)"""
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
    """Run a complete game session with evolved algorithms."""
    # Load environment
    load_env()

    logger.info("=== BitterLesson-AI Evolved Game Runner ===")

    # Initialize evolution system
    evolution_manager = None
    game_context = None

    if EVOLUTION_AVAILABLE:
        try:
            # Initialize database interface
            db_path = os.getenv('DATABASE_PATH', 'core_data.db')
            db = DatabaseInterface(db_path)

            # Initialize evolution manager
            evolution_config = EvolutionConfig(
                population_size=20,  # Smaller for testing
                evolution_frequency=3,  # Evolve every 3 games
                min_games_for_evolution=5
            )

            evolution_manager = EvolutionManager(evolution_config, db)

            # Initialize the evolution system
            init_result = await evolution_manager.initialize_system()
            logger.info(f"Evolution system status: {init_result}")

            # Initialize game context
            game_context = GameContext()

        except Exception as e:
            logger.error(f"Failed to initialize evolution system: {e}")
            logger.info("Falling back to random action system")
            evolution_manager = None

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

            # Step 4: Execute evolved algorithm actions
            if evolution_manager:
                logger.info("STEP 4: Executing evolved algorithm actions...")
            else:
                logger.info("STEP 4: Executing random actions (evolution system unavailable)...")

            current_state = state
            current_score = score
            current_available = available_actions
            actions_completed = 0
            max_actions = 20  # Increased from 10 to allow more exploration

            # Initialize game context with current game state
            if game_context:
                game_context.current_score = current_score
                game_context.actions_taken = 0
                game_context.available_actions = current_available
                game_context.game_id = game_id
                game_context.frame_changed_history = []

            for action_num in range(1, max_actions + 1):
                if current_state in ["WIN", "GAME_OVER"]:
                    logger.info(f"Game ended early at action {action_num}: {current_state}")
                    break

                if not current_available:
                    logger.warning(f"No available actions at step {action_num}")
                    break

                logger.info(f"--- Action {action_num}/{max_actions} ---")
                logger.info(f"Current state: {current_state}, Score: {current_score}")

                # Update game context
                if game_context:
                    game_context.current_score = current_score
                    game_context.actions_taken = actions_completed
                    game_context.available_actions = current_available

                # Send evolved or random action
                if evolution_manager and game_context:
                    result = await send_evolved_action(
                        session, base_url, headers, game_id, guid,
                        current_available, evolution_manager, game_context
                    )
                else:
                    result = await send_random_action(
                        session, base_url, headers, game_id, guid, current_available
                    )

                if result:
                    # Store previous state for frame change detection
                    previous_score = current_score

                    current_state = result.get('state', current_state)
                    current_score = result.get('score', current_score)
                    current_available = result.get('available_actions', current_available)

                    # Update frame change history
                    if game_context:
                        frame_changed = current_score != previous_score
                        game_context.frame_changed_history.append(frame_changed)

                        # Keep only last 5 frame changes
                        if len(game_context.frame_changed_history) > 5:
                            game_context.frame_changed_history.pop(0)

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

            # Update evolution system with game results
            if evolution_manager:
                try:
                    # Get current algorithm
                    current_algorithm = await evolution_manager.get_current_algorithm()

                    if current_algorithm:
                        # Prepare game result for evolution system
                        game_result = {
                            "game_id": game_id,
                            "session_id": card_id,  # Use card_id as session identifier
                            "final_score": current_score,
                            "actions_taken": actions_completed,
                            "win_detected": current_state == "WIN",
                            "final_state": current_state,
                            "algorithm_id": current_algorithm.algorithm_id
                        }

                        # Update algorithm performance
                        await evolution_manager.update_algorithm_performance(
                            current_algorithm.algorithm_id, game_result
                        )

                        logger.info(f"Updated evolution system with game result: "
                                   f"score={current_score}, actions={actions_completed}, "
                                   f"win={current_state == 'WIN'}")

                        # Get system status
                        system_status = evolution_manager.get_system_status()
                        logger.info(f"Evolution system status: Generation {system_status['current_generation']}, "
                                   f"Population {system_status['population_size']}, "
                                   f"Games played {system_status['total_games_played']}")

                    else:
                        logger.warning("No current algorithm to update performance for")

                except Exception as e:
                    logger.error(f"Failed to update evolution system: {e}")

            # Final summary
            logger.info("=== GAME SESSION COMPLETE ===")
            logger.info(f"Game: {game_id}")
            logger.info(f"Final state: {current_state}")
            logger.info(f"Final score: {current_score}")
            logger.info(f"Actions completed: {actions_completed}/{max_actions}")
            logger.info(f"Scorecard: {card_id}")

            # Prepare return data
            result = {
                "game_id": game_id,
                "final_state": current_state,
                "final_score": current_score,
                "actions_completed": actions_completed,
                "max_actions": max_actions,
                "scorecard_id": card_id,
                "evolution_enabled": evolution_manager is not None
            }

            # Add evolution system information
            if evolution_manager:
                try:
                    current_algorithm = await evolution_manager.get_current_algorithm()
                    system_status = evolution_manager.get_system_status()

                    result.update({
                        "algorithm_used": current_algorithm.algorithm_id if current_algorithm else None,
                        "generation": system_status['current_generation'],
                        "population_size": system_status['population_size'],
                        "total_games_played": system_status['total_games_played'],
                        "best_fitness_ever": system_status['best_fitness_ever']
                    })

                    logger.info(f"Evolution summary - Algorithm: {result['algorithm_used']}, "
                               f"Generation: {result['generation']}, "
                               f"Best fitness: {result['best_fitness_ever']:.2f}")

                except Exception as e:
                    logger.warning(f"Could not gather evolution summary: {e}")

            return result

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