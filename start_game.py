#!/usr/bin/env python3
"""
Quick Game Starter Script for BitterTruth-AI

Standalone script to start a game without module import issues.
"""

# Disable Python bytecode compilation
import os
import sys
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.dont_write_bytecode = True

import asyncio
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

# Try to import evolution system
try:
    import evolution_manager
    import algorithm_evaluator
    import main_runner
    EVOLUTION_AVAILABLE = True
except ImportError as e:
    print(f"Evolution system not available: {e}")
    EVOLUTION_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def start_single_game(max_actions: int = None):
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
        # Create ARC client with async context manager
        async with arc_api_client.ARCClient(api_key) as client:
            # Get available games
            print("Fetching available games...")
            games = await client.get_available_games()

            if not games:
                print("No games available")
                return

            print(f"Found {len(games)} available games:")
            for i, game in enumerate(games[:5]):  # Show first 5
                game_id = game.get('game_id', f'game_{i}')
                title = game.get('title', 'Unknown Game')
                print(f"  {i+1}. {game_id} - {title}")

            # Use the first available game
            first_game = games[0]
            first_game_id = first_game.get('game_id', 'game_0')
            print(f"\nStarting game: {first_game_id}")
            print("=" * 50)

            # Create session manager and start session
            session_manager = game_session_manager.GameSessionManager(api_key)
            session_id = await session_manager.start_session()
            print(f"Started session: {session_id}")

            # Create game
            game_data = await session_manager.create_game(first_game_id)
            scorecard_id = game_data.get('scorecard_id', 'unknown')
            print(f"Created game with scorecard: {scorecard_id}")

            # Create action handler
            action_handler_instance = action_handler.ActionHandler(session_manager)

            # Play some actions
            print("\nPlaying game...")
            # Extract game state from the dict
            game_state_dict = game_data if isinstance(game_data, dict) else game_data.__dict__
            game_state = arc_api_client.GameState.from_dict(game_state_dict)
            actions_taken = 0

            # Continue until game ends naturally (WIN/GAME_OVER) or optional action limit
            while game_state.state == "NOT_FINISHED":
                # Check optional action limit
                if max_actions and actions_taken >= max_actions:
                    print(f"\nReached action limit of {max_actions} actions")
                    break
                print(f"\n--- Action {actions_taken + 1} ---")
                print(f"Current Score: {game_state.score} / {game_state.win_score} (Win Score)")
                print(f"Game State: {game_state.state}")
                print(f"Available Actions: {game_state.available_actions}")

                # Use evolved strategy system for intelligent action selection
                action_taken = None
                evolution_success = False

                # Try evolution system first
                if EVOLUTION_AVAILABLE:
                    try:
                        # Initialize evolution system if not already done
                        if not hasattr(start_single_game, '_evolution_manager'):
                            print("Initializing evolution system...")
                            # Create database interface
                            db = database_interface.DatabaseInterface()
                            config = evolution_manager.EvolutionConfig(population_size=15, evolution_frequency=3)
                            evo_manager = evolution_manager.EvolutionManager(config, db)

                            # Initialize seeded algorithms
                            init_result = evo_manager.initialize_seeded_algorithms()
                            print(f"Loaded {init_result['seeded_count']} evolved algorithms")

                            # Initialize routine manager and create level-based routine
                            if hasattr(evo_manager, 'routine_manager'):
                                algorithms = [alg.algorithm_id for alg in evo_manager.active_population[:4]]
                                if algorithms:
                                    routine = evo_manager.routine_manager.create_level_based_routine(
                                        first_game_id.split('-')[0], algorithms, aggressive_switching=True
                                    )
                                    evo_manager.routine_manager.start_routine(first_game_id, routine)
                                    print(f"Started level-based switching routine with {len(algorithms)} algorithms")

                            start_single_game._evolution_manager = evo_manager
                            start_single_game._game_context = algorithm_evaluator.GameContext()
                            start_single_game._game_context.game_id = first_game_id

                        # Update game context
                        context = start_single_game._game_context

                        # CRITICAL FIX: Ensure score is numeric, not a list
                        current_score = game_state.score
                        if isinstance(current_score, (list, tuple)):
                            print(f"[WARN] Score is list/tuple: {current_score}, taking first element")
                            current_score = current_score[0] if len(current_score) > 0 else 0.0
                        elif not isinstance(current_score, (int, float)):
                            print(f"[WARN] Score is not numeric: {type(current_score)} {current_score}, using 0.0")
                            current_score = 0.0
                        context.current_score = float(current_score)
                        context.actions_taken = actions_taken
                        context.available_actions = game_state.available_actions

                        # Update frame and detect changes for meta strategies
                        context.update_frame(game_state.frame)

                        # Use evolved strategy to select action
                        action_result = await main_runner.evolved_strategy(
                            game_state, action_handler_instance,
                            start_single_game._evolution_manager, context
                        )

                        # Execute the selected action (now handles dict format with algorithm info)
                        if isinstance(action_result, dict):
                            action_name = action_result.get("action")
                            algorithm_id = action_result.get("algorithm_id", "unknown")
                            coordinates = action_result.get("coordinates", {})

                            if isinstance(action_name, str):
                                if action_name == "ACTION1":
                                    print(f"Taking ACTION1 (algorithm: {algorithm_id})...")
                                    game_state = await action_handler_instance.send_action_1()
                                    action_taken = "ACTION1"
                                    evolution_success = True
                                elif action_name == "ACTION2":
                                    print(f"Taking ACTION2 (algorithm: {algorithm_id})...")
                                    game_state = await action_handler_instance.send_action_2()
                                    action_taken = "ACTION2"
                                    evolution_success = True
                                elif action_name == "ACTION3":
                                    print(f"Taking ACTION3 (algorithm: {algorithm_id})...")
                                    game_state = await action_handler_instance.send_action_3()
                                    action_taken = "ACTION3"
                                    evolution_success = True
                                elif action_name == "ACTION4":
                                    print(f"Taking ACTION4 (algorithm: {algorithm_id})...")
                                    game_state = await action_handler_instance.send_action_4()
                                    action_taken = "ACTION4"
                                    evolution_success = True
                                elif action_name == "ACTION5":
                                    print(f"Taking ACTION5 (algorithm: {algorithm_id})...")
                                    game_state = await action_handler_instance.send_action_5()
                                    action_taken = "ACTION5"
                                    evolution_success = True
                                elif action_name == "ACTION7":
                                    print(f"Taking ACTION7 (algorithm: {algorithm_id})...")
                                    game_state = await action_handler_instance.send_action_7()
                                    action_taken = "ACTION7"
                                    evolution_success = True
                            elif callable(action_name):
                                # ACTION6 with dynamic coordinates
                                x = coordinates.get('x', 'dynamic')
                                y = coordinates.get('y', 'dynamic')
                                print(f"Taking ACTION6 (algorithm: {algorithm_id}) at ({x}, {y})...")
                                game_state = await action_name()
                                action_taken = f"ACTION6(x={x}, y={y})"
                                evolution_success = True
                        elif isinstance(action_result, str):
                            # Backward compatibility for old string format
                            action_name = action_result
                            if action_name == "ACTION1":
                                print("Taking ACTION1 (evolved)...")
                                game_state = await action_handler_instance.send_action_1()
                                action_taken = "ACTION1"
                                evolution_success = True
                            # ... other actions with old format
                        elif callable(action_result):
                            # Backward compatibility for old callable format
                            print("Taking ACTION6 (evolved with dynamic coordinates)...")
                            game_state = await action_result()
                            # Extract coordinates from result if available
                            x, y = getattr(action_result, 'x', 'dynamic'), getattr(action_result, 'y', 'dynamic')
                            action_taken = f"ACTION6(x={x}, y={y})"
                            evolution_success = True

                    except Exception as e:
                        print(f"[WARN] Evolution strategy failed: {e}")
                        evolution_success = False

                # Fallback to simple action logic if evolution not successful
                if not evolution_success:
                    try:
                        if 1 in game_state.available_actions:
                            print("Taking ACTION1 (fallback)...")
                            game_state = await action_handler_instance.send_action_1()
                            action_taken = "ACTION1"
                        elif 6 in game_state.available_actions:
                            # Use dynamic coordinates for fallback ACTION6
                            try:
                                import coordinate_strategies
                                x, y = coordinate_strategies.generate_action6_coordinates('fallback_algo', actions_taken=actions_taken)
                            except ImportError:
                                x, y = 32, 32  # Final fallback
                            print(f"Taking ACTION6(x={x}, y={y}) (fallback)...")
                            game_state = await action_handler_instance.send_action_6(x=x, y=y)
                            action_taken = f"ACTION6(x={x}, y={y})"
                        else:
                            print("[FAIL] No available actions to take")
                            break
                    except Exception as e:
                        print(f"[FAIL] Fallback action failed: {e}")
                        break

                # Update action counter and print status (for both evolution and fallback success)
                if evolution_success or action_taken:
                    actions_taken += 1
                    print(f"[PASS] Successfully executed {action_taken}")
                    print(f"New Score: {game_state.score} / {game_state.win_score}")
                    print(f"New State: {game_state.state}")

                    # Check if game ended
                    if game_state.state != "NOT_FINISHED":
                        print(f"\n[GAME] Game ended with state: {game_state.state}")
                        break

            # Finish the game (with error handling)
            try:
                await session_manager.finish_game(game_state.state, game_state.score)
            except Exception as e:
                print(f"Warning: Error finishing game: {e}")

            print("\n=== GAME COMPLETED ===")
            print(f"Game ID: {first_game_id}")
            print(f"Final State: {game_state.state}")
            print(f"Final Score: {game_state.score} / {game_state.win_score}")
            print(f"Actions Taken: {actions_taken}")
            print(f"Win: {game_state.state == 'WIN'}")
            if game_state.state == 'WIN':
                print("[WIN] CONGRATULATIONS! Game won!")
            elif game_state.state == 'GAME_OVER':
                print("[GAME_OVER] Game over - better luck next time!")
            elif game_state.state == 'CANCELLED':
                print("[CANCELLED] Game cancelled gracefully")

            # CRITICAL: Update evolution system with game results
            if (EVOLUTION_AVAILABLE and
                hasattr(start_single_game, '_evolution_manager') and
                start_single_game._evolution_manager):

                try:
                    print("Updating evolution system with game results...")

                    # Package game results
                    # CRITICAL FIX: Ensure final score is numeric, not a list
                    final_score = game_state.score
                    if isinstance(final_score, (list, tuple)):
                        print(f"[WARN] Final score is list/tuple: {final_score}, taking first element")
                        final_score = final_score[0] if len(final_score) > 0 else 0.0
                    elif not isinstance(final_score, (int, float)):
                        print(f"[WARN] Final score is not numeric: {type(final_score)} {final_score}, using 0.0")
                        final_score = 0.0
                    final_score = float(final_score)

                    game_result = {
                        'game_id': first_game_id,
                        'session_id': session_manager.session_id if hasattr(session_manager, 'session_id') else 'unknown',
                        'final_score': final_score,
                        'win_score': float(game_state.win_score) if isinstance(game_state.win_score, (int, float)) else 0.0,
                        'actions_taken': actions_taken,
                        'final_state': game_state.state,
                        'win_detected': game_state.state == 'WIN'
                    }

                    # Update algorithm performance (this triggers evolution check)
                    if hasattr(start_single_game, '_game_context') and start_single_game._game_context:
                        current_algorithm_id = getattr(start_single_game._game_context, 'algorithm_id', None)
                        if current_algorithm_id:
                            await start_single_game._evolution_manager.update_algorithm_performance(
                                current_algorithm_id, game_result
                            )
                            print(f"Updated performance for algorithm: {current_algorithm_id}")
                        else:
                            print("No algorithm ID found - skipping performance update")
                    else:
                        print("No game context found - skipping performance update")

                except Exception as e:
                    print(f"Warning: Error updating evolution system: {e}")

        # Shutdown session (with error handling)
        try:
            await session_manager.shutdown()
        except Exception as e:
            print(f"Warning: Error during session shutdown: {e}")

    except Exception as e:
        print(f"Error starting game: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(start_single_game())