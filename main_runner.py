"""
Main Game Runner

Entry point for running ARC games using the core game mechanics.
Provides command-line interface for playing games.
"""

# Disable Python bytecode compilation
import os
import sys
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.dont_write_bytecode = True

import asyncio
import argparse
import logging
import sys
import os
import subprocess
import platform
from typing import Optional

# Disable Python bytecode compilation
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
import json
from datetime import datetime

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, fall back to system environment variables
    pass

try:
    from .core_gameplay import GameplayEngine, random_strategy, conservative_strategy, exploration_strategy
    from .database_interface import DatabaseInterface
except ImportError:
    # Fallback for standalone execution
    from core_gameplay import GameplayEngine, random_strategy, conservative_strategy, exploration_strategy
    from database_interface import DatabaseInterface

# Configure database logging
from database_logger import setup_database_logging

# Set up database logging instead of file logging
db_handler = setup_database_logging()
logger = logging.getLogger(__name__)

# Import evolution system components with graceful fallback
try:
    from evolution_manager import EvolutionManager, EvolutionConfig
    from algorithm_evaluator import AlgorithmEvaluator, GameContext
    from routine_manager import RoutineManager
    EVOLUTION_AVAILABLE = True
    logger.info("Evolution system components loaded successfully")
except ImportError as e:
    logger.warning(f"Evolution system not available: {e}")
    EvolutionManager = None
    AlgorithmEvaluator = None
    GameContext = None
    RoutineManager = None
    EVOLUTION_AVAILABLE = False


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


async def evolved_strategy(game_state, action_handler, evolution_manager=None, game_context=None):
    """Evolved algorithm strategy using the seeded algorithm system."""
    if not EVOLUTION_AVAILABLE or not evolution_manager:
        logger.warning("Evolution system not available, falling back to random strategy")
        return {"action": await random_strategy(game_state, action_handler), "algorithm_id": "random_fallback"}

    try:
        # Update game context with current state
        if game_context:
            # Track score changes for coordinate success analysis
            previous_score = game_context.current_score
            game_context.previous_score = previous_score
            
            # CRITICAL FIX: Ensure game_state.score is always a number, not a list
            current_score = game_state.score
            if isinstance(current_score, (list, tuple)):
                logger.warning(f"Score is list/tuple: {current_score}, taking first element")
                current_score = current_score[0] if len(current_score) > 0 else 0.0
            elif not isinstance(current_score, (int, float)):
                logger.warning(f"Score is not numeric: {type(current_score)} {current_score}, using 0.0")
                current_score = 0.0
            
            game_context.current_score = float(current_score)
            
            # actions_taken should be passed from the calling context, not from game_state
            # Keep existing value if already set, otherwise default to 0
            if not hasattr(game_context, 'actions_taken') or game_context.actions_taken is None:
                game_context.actions_taken = 0
            game_context.available_actions = game_state.available_actions
            game_context.game_id = getattr(game_state, 'game_id', 'unknown')
            game_context.frame = getattr(game_state, 'frame', None)

            # Track ACTION6 success based on score improvement
            if hasattr(game_context, 'track_action6_success'):
                try:
                    # CRITICAL FIX: Ensure both scores are numbers before subtraction
                    current_score = game_context.current_score
                    if isinstance(current_score, (list, tuple)):
                        logger.warning(f"Current score is list/tuple: {current_score}, taking first element")
                        current_score = current_score[0] if len(current_score) > 0 else 0.0
                    elif not isinstance(current_score, (int, float)):
                        logger.warning(f"Current score is not numeric: {type(current_score)} {current_score}, using 0.0")
                        current_score = 0.0

                    if isinstance(previous_score, (list, tuple)):
                        logger.warning(f"Previous score is list/tuple: {previous_score}, taking first element")
                        previous_score = previous_score[0] if len(previous_score) > 0 else 0.0
                    elif not isinstance(previous_score, (int, float)):
                        logger.warning(f"Previous score is not numeric: {type(previous_score)} {previous_score}, using 0.0")
                        previous_score = 0.0

                    score_improvement = float(current_score) - float(previous_score)
                    if score_improvement > 0:
                        game_context.track_action6_success(score_improvement)
                except (TypeError, ValueError) as e:
                    logger.warning(f"Score improvement calculation failed: {e}")
                    logger.warning(f"Current: {type(game_context.current_score)} {game_context.current_score}")
                    logger.warning(f"Previous: {type(previous_score)} {previous_score}")

        # Check for mid-game algorithm switching based on level performance
        if hasattr(evolution_manager, 'routine_manager') and game_context:
            # CRITICAL FIX: Ensure score is numeric before passing to update_routine_context
            routine_score = game_state.score
            if isinstance(routine_score, (list, tuple)):
                logger.warning(f"Routine score is list/tuple: {routine_score}, taking first element")
                routine_score = routine_score[0] if len(routine_score) > 0 else 0.0
            elif not isinstance(routine_score, (int, float)):
                logger.warning(f"Routine score is not numeric: {type(routine_score)} {routine_score}, using 0.0")
                routine_score = 0.0
            routine_score = float(routine_score)

            new_algorithm = evolution_manager.update_routine_context(
                game_context.game_id,
                routine_score,
                game_context.actions_taken
            )
            if new_algorithm:
                logger.info(f"Switched algorithm mid-game: {new_algorithm.algorithm_id}")

        # Get current algorithm from evolution manager (AWAIT added)
        current_algorithm = await evolution_manager.get_current_algorithm()

        if current_algorithm:
            # Update game context with algorithm information
            if game_context:
                game_context.algorithm_id = current_algorithm.algorithm_id

            # Use algorithm evaluator to determine action
            evaluator = AlgorithmEvaluator()
            result = evaluator.evaluate_algorithm(current_algorithm, game_context or GameContext())

            # Log action with coordinate information
            coord_info = ""
            if result.coordinates:
                coord_info = f" at ({result.coordinates['x']}, {result.coordinates['y']})"
            logger.info(f"Evolved algorithm selected: {result.action}{coord_info} (confidence: {result.confidence:.2f})")

            # Convert action result to action handler call
            if result.action == "ACTION1":
                return {"action": "ACTION1", "algorithm_id": current_algorithm.algorithm_id}
            elif result.action == "ACTION2":
                return {"action": "ACTION2", "algorithm_id": current_algorithm.algorithm_id}
            elif result.action == "ACTION3":
                return {"action": "ACTION3", "algorithm_id": current_algorithm.algorithm_id}
            elif result.action == "ACTION4":
                return {"action": "ACTION4", "algorithm_id": current_algorithm.algorithm_id}
            elif result.action == "ACTION5":
                return {"action": "ACTION5", "algorithm_id": current_algorithm.algorithm_id}
            elif result.action == "ACTION6" and result.coordinates:
                # For ACTION6, we need to return a custom action
                async def action6_with_coords():
                    return await action_handler.send_action_6(
                        result.coordinates.get('x', 32),
                        result.coordinates.get('y', 32),
                        game_state.frame
                    )
                return {
                    "action": action6_with_coords, 
                    "algorithm_id": current_algorithm.algorithm_id,
                    "coordinates": result.coordinates
                }
            elif result.action == "ACTION7":
                return {"action": "ACTION7", "algorithm_id": current_algorithm.algorithm_id}
            else:
                logger.warning(f"Unknown action from evolved algorithm: {result.action}")
                return {"action": await random_strategy(game_state, action_handler), "algorithm_id": "unknown_fallback"}
        else:
            logger.warning("No current algorithm available, using random fallback")
            return {"action": await random_strategy(game_state, action_handler), "algorithm_id": "no_algorithm"}

    except Exception as e:
        logger.error(f"Error in evolved strategy: {e}")
        return {"action": await random_strategy(game_state, action_handler), "algorithm_id": "error_fallback"}


async def run_single_game(game_id: str, api_key: str, strategy: str = "balanced",
                         db_path: str = None) -> dict:
    """Run a single game.

    Args:
        game_id: Game ID to play
        api_key: ARC API key
        strategy: Strategy to use
        db_path: Database path

    Returns:
        Game results
    """
    if db_path is None:
        db_path = os.getenv('DATABASE_PATH', 'core_data.db')

    # Initialize evolution system if evolved strategy is requested
    evolution_manager = None
    game_context = None
    
    if strategy == "evolved" and EVOLUTION_AVAILABLE:
        try:
            # Initialize database interface
            from database_interface import DatabaseInterface
            db = DatabaseInterface(db_path)

            # Ensure database schema is created
            db._create_database_from_schema()

            # Initialize evolution manager
            evolution_config = EvolutionConfig(
                population_size=15,
                evolution_frequency=3,
                min_games_for_evolution=2
            )
            
            evolution_manager = EvolutionManager(evolution_config, db)
            
            # Initialize seeded algorithms
            init_result = evolution_manager.initialize_seeded_algorithms()
            logger.info(f"Evolution system initialized: {init_result['seeded_count']} algorithms loaded")
            
            # Initialize game context
            game_context = GameContext()
            game_context.game_id = game_id
            
        except Exception as e:
            logger.error(f"Failed to initialize evolution system: {e}")
            logger.info("Falling back to balanced strategy")
            strategy = "balanced"

    async with GameplayEngine(api_key, db_path) as engine:
        engine.configure(strategy=strategy)

        # Select strategy callback if specified
        callback = None
        if strategy == "random":
            callback = random_strategy
        elif strategy == "conservative":
            callback = conservative_strategy
        elif strategy == "exploration":
            callback = exploration_strategy
        elif strategy == "evolved" and evolution_manager:
            # Create evolved strategy callback with evolution manager
            async def evolved_callback(game_state, action_handler):
                return await evolved_strategy(game_state, action_handler, evolution_manager, game_context)
            callback = evolved_callback

        result = await engine.play_single_game(game_id, callback)
        
        # Update evolution system with game results if evolved strategy was used
        if evolution_manager and strategy == "evolved":
            try:
                # Get current algorithm
                current_algorithm = evolution_manager.get_current_algorithm()
                
                if current_algorithm:
                    # Prepare game result for evolution system
                    game_result = {
                        "game_id": game_id,
                        "session_id": result.get('session_id', 'main_runner_session'),
                        "final_score": result['final_score'],
                        "actions_taken": result['actions_taken'],
                        "win_detected": result['win'],
                        "final_state": result.get('final_state', 'completed'),
                        "algorithm_id": current_algorithm.algorithm_id
                    }
                    
                    # Update algorithm performance
                    evolution_manager.update_algorithm_performance(
                        current_algorithm.algorithm_id, game_result
                    )
                    
                    logger.info(f"Updated evolution system with game result: "
                               f"algorithm={current_algorithm.algorithm_id}, "
                               f"score={result['final_score']}, win={result['win']}")
                    
            except Exception as e:
                logger.error(f"Failed to update evolution system: {e}")
        
        return result


async def run_session(max_games: Optional[int] = None, api_key: str = None,
                     strategy: str = "balanced", mode: str = "gameplay",
                     db_path: str = "core_data.db") -> dict:
    """Run a gaming session.

    Args:
        max_games: Maximum number of games to play
        api_key: ARC API key
        strategy: Strategy to use
        mode: Session mode
        db_path: Database path

    Returns:
        Session results
    """
    # Initialize evolution system if evolved strategy is requested
    evolution_manager = None
    
    if strategy == "evolved" and EVOLUTION_AVAILABLE:
        try:
            # Initialize database interface
            from database_interface import DatabaseInterface
            db = DatabaseInterface(db_path)

            # Ensure database schema is created
            db._create_database_from_schema()

            # Initialize evolution manager
            evolution_config = EvolutionConfig(
                population_size=20,  # Larger population for sessions
                evolution_frequency=5,  # Evolve every 5 games
                min_games_for_evolution=3
            )
            
            evolution_manager = EvolutionManager(evolution_config, db)
            
            # Initialize seeded algorithms
            init_result = evolution_manager.initialize_seeded_algorithms()
            logger.info(f"Evolution system initialized for session: {init_result['seeded_count']} algorithms loaded")
            
        except Exception as e:
            logger.error(f"Failed to initialize evolution system for session: {e}")
            logger.info("Falling back to balanced strategy")
            strategy = "balanced"

    async with GameplayEngine(api_key, db_path) as engine:
        engine.configure(strategy=strategy)
        
        # If using evolved strategy, set up the evolution manager in the engine
        if evolution_manager and strategy == "evolved":
            # Store evolution manager reference for use in gameplay
            engine.evolution_manager = evolution_manager
            logger.info("Evolution manager configured for session gameplay")
        
        result = await engine.run_session(mode, max_games)
        
        # Log evolution system summary if it was used
        if evolution_manager and strategy == "evolved":
            try:
                system_status = evolution_manager.get_system_status()
                logger.info(f"Session completed with evolution system - "
                           f"Generation: {system_status['current_generation']}, "
                           f"Best fitness: {system_status['best_fitness_ever']:.2f}, "
                           f"Total games: {system_status['total_games_played']}")
            except Exception as e:
                logger.warning(f"Could not retrieve evolution system summary: {e}")
        
        return result


def show_stats(db_path: str = "core_data.db", session_id: str = None):
    """Show performance statistics.

    Args:
        db_path: Database path
        session_id: Optional session ID filter
    """
    db = DatabaseInterface(db_path)

    try:
        # Database stats
        db_stats = db.get_database_stats()
        print("\n=== Database Statistics ===")
        for key, value in db_stats.items():
            print(f"{key}: {value}")

        # Performance stats
        engine = GameplayEngine(db_path=db_path)
        perf_stats = engine.get_performance_stats(session_id)
        print("\n=== Performance Statistics ===")
        for key, value in perf_stats.items():
            if isinstance(value, float):
                print(f"{key}: {value:.3f}")
            else:
                print(f"{key}: {value}")

        # Recent sessions
        sessions = db.execute_query("""
            SELECT session_id, mode, status, total_games, total_wins, win_rate, avg_score,
                   start_time, end_time
            FROM training_sessions
            ORDER BY start_time DESC
            LIMIT 10
        """)

        if sessions:
            print("\n=== Recent Sessions ===")
            for session in sessions:
                print(f"Session: {session['session_id']}")
                print(f"  Mode: {session['mode']}, Status: {session['status']}")
                print(f"  Games: {session['total_games']}, Wins: {session['total_wins']}")
                print(f"  Win Rate: {session['win_rate']:.3f}, Avg Score: {session['avg_score']:.3f}")
                print(f"  Time: {session['start_time']} to {session['end_time']}")
                print()

    finally:
        db.close()

def show_evolution_stats(db_path: str = "core_data.db"):
    """Show evolution system statistics.
    
    Args:
        db_path: Database path
    """
    if not EVOLUTION_AVAILABLE:
        print("Evolution system not available. Install required components.")
        return
        
    try:
        from database_interface import DatabaseInterface
        db = DatabaseInterface(db_path)
        
        print("\n=== Evolution System Statistics ===")
        
        # Get seeded algorithm stats
        seeded_stats = db.get_seeded_algorithm_stats()
        
        if 'overall' in seeded_stats:
            overall = seeded_stats['overall']
            print(f"Total Seeded Algorithms: {overall.get('total_seeded_algorithms', 0)}")
            print(f"Overall Average Performance: {overall.get('overall_avg_performance', 0):.3f}")
            print(f"Best Performance: {overall.get('best_performance', 0):.3f}")
        
        # Show category breakdown
        if 'categories' in seeded_stats and seeded_stats['categories']:
            print("\n--- Performance by Category ---")
            for category in seeded_stats['categories']:
                print(f"{category['category']}: {category['count']} algorithms, "
                      f"avg performance: {category['avg_performance']:.3f}")
        
        # Show game type performance
        if 'game_types' in seeded_stats and seeded_stats['game_types']:
            print("\n--- Performance by Game Type ---")
            for game_type in seeded_stats['game_types']:
                print(f"{game_type['game_type']}: {game_type['routine_count']} routines, "
                      f"success rate: {game_type['avg_success_rate']:.3f}")
        
        # Get top algorithms
        top_algorithms = db.get_best_algorithms_by_category(limit=5)
        if top_algorithms:
            print("\n--- Top Performing Algorithms ---")
            for algo in top_algorithms:
                print(f"{algo['original_name']} ({algo['category']}): "
                      f"fitness={algo['fitness_score']:.2f}, "
                      f"performance={algo['avg_performance']:.2f}")
        
        # Get evolution history
        evolution_history = db.get_evolution_history(limit=5)
        if evolution_history:
            print("\n--- Recent Evolution History ---")
            for record in evolution_history:
                print(f"Generation {record['generation']}: "
                      f"best fitness={record['best_fitness']:.2f}, "
                      f"avg fitness={record['avg_fitness']:.2f}, "
                      f"population={record['population_size']}")
        
        db.close()
        
    except Exception as e:
        logger.error(f"Error showing evolution stats: {e}")
        print(f"Error: {e}")


def manage_evolution_system(action: str, db_path: str = "core_data.db"):
    """Manage the evolution system.
    
    Args:
        action: Action to perform ('init', 'evolve', 'reset')
        db_path: Database path
    """
    if not EVOLUTION_AVAILABLE:
        print("Evolution system not available. Install required components.")
        return
        
    try:
        from database_interface import DatabaseInterface
        db = DatabaseInterface(db_path)

        # Ensure database schema is created
        db._create_database_from_schema()

        evolution_config = EvolutionConfig(
            population_size=20,
            evolution_frequency=3,
            min_games_for_evolution=2
        )
        
        evolution_manager = EvolutionManager(evolution_config, db)
        
        if action == "init":
            print("Initializing evolution system...")
            init_result = evolution_manager.initialize_seeded_algorithms()
            print(f"[PASS] Initialized {init_result['seeded_count']} seeded algorithms")
            print(f"[PASS] Population size: {init_result['population_size']}")
            if init_result.get('errors'):
                print(f"[WARN] {len(init_result['errors'])} errors encountered")
        
        elif action == "evolve":
            print("Forcing evolution cycle...")
            try:
                evolution_result = evolution_manager.evolve_population()
                print(f"[PASS] Evolution completed")
                print(f"[PASS] New generation: {evolution_result.get('new_generation', 'unknown')}")
                print(f"[PASS] Population size: {evolution_result.get('population_size', 'unknown')}")
            except Exception as e:
                print(f"[FAIL] Evolution failed: {e}")
        
        elif action == "status":
            print("Evolution system status:")
            status = evolution_manager.get_system_status()
            print(f"Current Generation: {status['current_generation']}")
            print(f"Population Size: {status['population_size']}")
            print(f"Total Games Played: {status['total_games_played']}")
            print(f"Best Fitness Ever: {status['best_fitness_ever']:.3f}")
            print(f"Games Since Last Evolution: {status['games_since_last_evolution']}")
        
        else:
            print(f"Unknown action: {action}")
            print("Available actions: init, evolve, status")
        
        db.close()
        
    except Exception as e:
        logger.error(f"Error managing evolution system: {e}")
        print(f"Error: {e}")


def list_games(api_key: str):
    """List available games.

    Args:
        api_key: ARC API key
    """
    async def _list_games():
        async with GameplayEngine(api_key) as engine:
            games = await engine.session_manager.get_available_games()
            print(f"\n=== Available Games ({len(games)}) ===")
            for i, game in enumerate(games):
                game_id = game.get('id', game.get('game_id', f'game_{i}'))
                title = game.get('title', game.get('name', 'Unknown'))
                print(f"{i+1:3d}. {game_id} - {title}")

    asyncio.run(_list_games())


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Core Game Mechanics - ARC-AGI-3 Game Runner"
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Play single game
    play_parser = subparsers.add_parser('play', help='Play a single game')
    play_parser.add_argument('game_id', help='Game ID to play')
    play_parser.add_argument('--api-key', help='ARC API key (or set ARC_API_KEY env var)')
    play_parser.add_argument('--strategy', choices=['balanced', 'random', 'conservative', 'exploration', 'evolved', 'level_beating'],
                           default='balanced', help='Strategy to use')
    play_parser.add_argument('--db-path', default='core_data.db',
                           help='Database file path')

    # Run session
    session_parser = subparsers.add_parser('session', help='Run a gaming session')
    session_parser.add_argument('--max-games', type=int, help='Maximum number of games to play')
    session_parser.add_argument('--api-key', help='ARC API key (or set ARC_API_KEY env var)')
    session_parser.add_argument('--strategy', choices=['balanced', 'random', 'conservative', 'exploration', 'evolved', 'level_beating'],
                              default='balanced', help='Strategy to use')
    session_parser.add_argument('--mode', default='gameplay', help='Session mode')
    session_parser.add_argument('--db-path', default='core_data.db',
                              help='Database file path')

    # Show stats
    stats_parser = subparsers.add_parser('stats', help='Show performance statistics')
    stats_parser.add_argument('--db-path', default='core_data.db',
                            help='Database file path')
    stats_parser.add_argument('--session-id', help='Filter by session ID')

    # List games
    list_parser = subparsers.add_parser('list', help='List available games')
    list_parser.add_argument('--api-key', help='ARC API key (or set ARC_API_KEY env var)')

    # Evolution system commands
    evolution_parser = subparsers.add_parser('evolution', help='Manage evolution system')
    evolution_subparsers = evolution_parser.add_subparsers(dest='evolution_action', help='Evolution actions')

    # Evolution stats
    evol_stats_parser = evolution_subparsers.add_parser('stats', help='Show evolution system statistics')
    evol_stats_parser.add_argument('--db-path', default='core_data.db', help='Database file path')

    # Evolution management
    evol_manage_parser = evolution_subparsers.add_parser('manage', help='Manage evolution system')
    evol_manage_parser.add_argument('action', choices=['init', 'evolve', 'status'],
                                   help='Management action to perform')
    evol_manage_parser.add_argument('--db-path', default='core_data.db', help='Database file path')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == 'play':
            api_key = args.api_key or os.getenv('ARC_API_KEY')
            if not api_key:
                print("Error: API key required. Set ARC_API_KEY environment variable or use --api-key")
                return

            result = asyncio.run(run_single_game(
                args.game_id, api_key, args.strategy, args.db_path
            ))

            print(f"\n=== Game Results ===")
            print(f"Game ID: {result['game_id']}")
            print(f"Final State: {result['final_state']}")
            print(f"Final Score: {result['final_score']}")
            print(f"Actions Taken: {result['actions_taken']}")
            print(f"Duration: {result['duration_seconds']:.2f} seconds")
            print(f"Win: {result['win']}")

        elif args.command == 'session':
            api_key = args.api_key or os.getenv('ARC_API_KEY')
            if not api_key:
                print("Error: API key required. Set ARC_API_KEY environment variable or use --api-key")
                return

            result = asyncio.run(run_session(
                args.max_games, api_key, args.strategy, args.mode, args.db_path
            ))

            print(f"\n=== Session Results ===")
            print(f"Session ID: {result['session_id']}")
            print(f"Mode: {result['mode']}")
            print(f"Total Games: {result['total_games']}")
            print(f"Wins: {result['wins']}")
            print(f"Win Rate: {result['win_rate']:.3f}")
            print(f"Average Score: {result['avg_score']:.2f}")
            print(f"Total Actions: {result['total_actions']}")
            print(f"Avg Actions/Game: {result['avg_actions_per_game']:.1f}")

        elif args.command == 'stats':
            show_stats(args.db_path, args.session_id)

        elif args.command == 'list':
            api_key = args.api_key or os.getenv('ARC_API_KEY')
            if not api_key:
                print("Error: API key required. Set ARC_API_KEY environment variable or use --api-key")
                return

            list_games(api_key)

        elif args.command == 'evolution':
            if not hasattr(args, 'evolution_action') or not args.evolution_action:
                print("Error: Evolution action required. Use 'stats' or 'manage'")
                return

            if args.evolution_action == 'stats':
                show_evolution_stats(args.db_path)
            elif args.evolution_action == 'manage':
                if not hasattr(args, 'action') or not args.action:
                    print("Error: Management action required (init, evolve, status)")
                    return
                manage_evolution_system(args.action, args.db_path)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()