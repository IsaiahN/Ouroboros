"""
Main Game Runner

Entry point for running ARC games using the core game mechanics.
Provides command-line interface for playing games.
"""

import asyncio
import argparse
import logging
import sys
import os
from typing import Optional
import json

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, fall back to system environment variables
    pass

from .core_gameplay import GameplayEngine, random_strategy, conservative_strategy, exploration_strategy
from .database_interface import DatabaseInterface

# Configure database logging
from database_logger import setup_database_logging

# Set up database logging instead of file logging
db_handler = setup_database_logging()
logger = logging.getLogger(__name__)


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

        result = await engine.play_single_game(game_id, callback)
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
    async with GameplayEngine(api_key, db_path) as engine:
        engine.configure(strategy=strategy)
        result = await engine.run_session(mode, max_games)
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
    play_parser.add_argument('--strategy', choices=['balanced', 'random', 'conservative', 'exploration'],
                           default='balanced', help='Strategy to use')
    play_parser.add_argument('--db-path', default='core_data.db',
                           help='Database file path')

    # Run session
    session_parser = subparsers.add_parser('session', help='Run a gaming session')
    session_parser.add_argument('--max-games', type=int, help='Maximum number of games to play')
    session_parser.add_argument('--api-key', help='ARC API key (or set ARC_API_KEY env var)')
    session_parser.add_argument('--strategy', choices=['balanced', 'random', 'conservative', 'exploration'],
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

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()