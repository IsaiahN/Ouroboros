#!/usr/bin/env python3
import os
import sys

# Enforce no bytecode before any imports
sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
Quick Start Evolution Script
=============================

Simple wrapper to launch autonomous evolution with sensible defaults.
Just run this and let it evolve!

Usage:
    python run_evolution.py              # Default settings
    python run_evolution.py --fast       # Faster cycles (30 min intervals)
    python run_evolution.py --thorough   # More games per generation
    python run_evolution.py --quick      # Quick test (5 generations max)
"""

import argparse
import asyncio
import os
import sys

# Load environment variables from .env if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from autonomous_evolution_runner import AutonomousEvolutionRunner
from manual_tools.utilities.cleanup_temp_files import cleanup_temp_files


def main():
    # Auto-cleanup temporary diagnostic files
    try:
        cleanup_temp_files()
    except Exception as e:
        print(f"[WARN] Cleanup failed (non-critical): {e}")

    parser = argparse.ArgumentParser(description='Quick Start Evolution')

    parser.add_argument('--fast', action='store_true',
                       help='Fast mode: 30 min intervals, 10 games/gen')
    parser.add_argument('--thorough', action='store_true',
                       help='Thorough mode: 90 min intervals, 50 games/gen')
    parser.add_argument('--quick', action='store_true',
                       help='Quick test: 5 generations max')
    parser.add_argument('--test', action='store_true',
                       help='Minimal test: 1 agent, 1 game, 1 generation')
    parser.add_argument('--max-generations', type=int, default=None,
                       help='Override max generations (useful when resuming from checkpoint)')
    parser.add_argument('--diversity', action='store_true',
                       help='Diversity mode: Diverse games, anti-overfitting, generalization focus')
    parser.add_argument('--specialist', action='store_true',
                       help='Specialist mode: Narrow agents, deep mastery, repetition-based learning')
    parser.add_argument('--game', type=str, default=None,
                       help='Focus on specific game (e.g., --game as66). All agents play only this game.')
    parser.add_argument('--replay-validation', action='store_true',
                       help='Run replay validation batch using replay_index pointers (no live gameplay)')
    parser.add_argument('--replay-limit', type=int, default=None,
                       help='Limit number of replay validations (most recent first)')
    parser.add_argument('--no-replay', action='store_true',
                       help='Skip sequence retrieval/replay but still capture new sequences on win')

    args = parser.parse_args()

    # Configure based on mode
    if args.test:
        print(">> TEST MODE - Minimal test (1 agent, 1 game)")
        # Skip heavy pariah backfill during quick smoke test
        os.environ["OUROBOROS_SKIP_PARIAH_BACKFILL"] = "1"
        config = {
            'initial_population_size': 1,
            'games_per_generation': 1,
            'evolution_interval_minutes': 1,
            'max_generations': 1,
            'skip_cleanup': True  # Skip slow database cleanup in test mode
        }
    elif args.fast:
        print(">> FAST MODE - Quick iterations")
        config = {
            'initial_population_size': 8,
            'games_per_generation': 6,  # All 6 currently available games
            'evolution_interval_minutes': 30,
            'max_generations': 30,
            'ensure_game_type_coverage': True  # Force one game per unique type
        }
    elif args.thorough:
        print(">> THOROUGH MODE - Deep evaluation")
        config = {
            'initial_population_size': 15,
            'games_per_generation': 20,  # REDUCED: 50 -> 20 for reasonable times
            'evolution_interval_minutes': 90,
            'max_generations': 20
        }
    elif args.quick:
        print(">> QUICK TEST - 5 generations")
        config = {
            'initial_population_size': 5,
            'games_per_generation': 5,  # REDUCED: 10 -> 5
            'evolution_interval_minutes': 15,
            'max_generations': 5
        }
    else:
        print(">> STANDARD MODE - Balanced evolution")
        config = {
            'initial_population_size': 80,  # Balanced for ~25 games per generation
            'games_per_generation': 25,  # ADAPTIVE: 80 * 0.31 = 25 (min 25)
            'evolution_interval_minutes': 60,
            'max_generations': 50
        }

    # Override max_generations if specified (useful when resuming)
    if args.max_generations:
        config['max_generations'] = args.max_generations
        print(f"[OVERRIDE] Max Generations set to {args.max_generations}")

    # Check API key
    api_key = os.getenv('ARC_API_KEY')
    if not api_key or api_key == 'your_api_key_here':
        print("\n[ERROR] Need valid ARC_API_KEY in .env file")
        return

    print(f"\n{'='*60}")
    print("Configuration:")
    print(f"  Initial Population: {config['initial_population_size']} agents (or existing if higher)")
    print(f"  Games per Generation: ADAPTIVE (agents * 25%, min 10, max 200)")
    print(f"  Evolution Interval: {config['evolution_interval_minutes']} minutes")
    print(f"  Max Generations: {config['max_generations']}")
    if args.diversity:
        print(f"  Diversity Mode: ENABLED (generalization focus)")
    if args.specialist:
        print(f"  Specialist Mode: ENABLED (deep mastery focus)")
    if args.game:
        print(f"  Target Game: {args.game} (focused mastery)")
    if args.replay_validation:
        limit_text = f"limit {args.replay_limit}" if args.replay_limit else "no limit"
        print(f"  Replay Validation Batch: ENABLED ({limit_text})")
    if args.no_replay:
        print(f"  No Replay Mode: ENABLED (pure exploration, capture still enabled)")
    if config.get('ensure_game_type_coverage'):
        print(f"  Game Type Coverage: ENABLED (one game per type guaranteed)")
    print(f"{'='*60}\n")

    # Add diversity mode to config if requested
    if args.diversity:
        config['agi_mode'] = True

    # Add specialist mode to config if requested
    if args.specialist:
        config['specialist_mode'] = True

    # Add target game filter if specified
    if args.game:
        config['target_game'] = args.game

    # Replay validation batch (REPLAY_VALIDATION mode)
    if args.replay_validation:
        config['replay_validation_batch'] = True
        if args.replay_limit:
            config['replay_validation_limit'] = args.replay_limit
    else:
        config['replay_validation_batch'] = False

    # No replay mode (skip sequence retrieval, still capture)
    if args.no_replay:
        config['skip_sequence_retrieval'] = True

    # Create and run
    runner = AutonomousEvolutionRunner(**config)
    asyncio.run(runner.run())


if __name__ == "__main__":
    main()
