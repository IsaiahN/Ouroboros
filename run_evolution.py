#!/usr/bin/env python3
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

import os
import sys
import asyncio
import argparse

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from autonomous_evolution_runner import AutonomousEvolutionRunner


def main():
    parser = argparse.ArgumentParser(description='Quick Start Evolution')
    
    parser.add_argument('--fast', action='store_true',
                       help='Fast mode: 30 min intervals, 10 games/gen')
    parser.add_argument('--thorough', action='store_true',
                       help='Thorough mode: 90 min intervals, 50 games/gen')
    parser.add_argument('--quick', action='store_true',
                       help='Quick test: 5 generations max')
    parser.add_argument('--diversity', action='store_true',
                       help='Diversity mode: Diverse games, anti-overfitting, generalization focus')
    parser.add_argument('--specialist', action='store_true',
                       help='Specialist mode: Narrow agents, deep mastery, repetition-based learning')
    
    args = parser.parse_args()
    
    # Configure based on mode
    if args.fast:
        print("🚀 FAST MODE - Quick iterations")
        config = {
            'initial_population_size': 8,
            'games_per_generation': 10,
            'evolution_interval_minutes': 30,
            'max_generations': 30,
            'target_win_rate': 0.50
        }
    elif args.thorough:
        print("🔬 THOROUGH MODE - Deep evaluation")
        config = {
            'initial_population_size': 15,
            'games_per_generation': 50,
            'evolution_interval_minutes': 90,
            'max_generations': 20,
            'target_win_rate': 0.50
        }
    elif args.quick:
        print("⚡ QUICK TEST - 5 generations")
        config = {
            'initial_population_size': 5,
            'games_per_generation': 10,
            'evolution_interval_minutes': 15,
            'max_generations': 5,
            'target_win_rate': 0.50
        }
    else:
        print("🧬 STANDARD MODE - Balanced evolution")
        config = {
            'initial_population_size': 10,
            'games_per_generation': 20,
            'evolution_interval_minutes': 60,
            'max_generations': 50,
            'target_win_rate': 0.50
        }
    
    # Check API key
    api_key = os.getenv('ARC_API_KEY')
    if not api_key or api_key == 'your_api_key_here':
        print("\n❌ ERROR: Need valid ARC_API_KEY in .env file")
        return
    
    print(f"\n{'='*60}")
    print("Configuration:")
    print(f"  Initial Population: {config['initial_population_size']} agents")
    print(f"  Games per Generation: {config['games_per_generation']}")
    print(f"  Evolution Interval: {config['evolution_interval_minutes']} minutes")
    print(f"  Max Generations: {config['max_generations']}")
    print(f"  Target Win Rate: {config['target_win_rate']:.0%}")
    if args.diversity:
        print(f"  Diversity Mode: ENABLED (generalization focus)")
    if args.specialist:
        print(f"  Specialist Mode: ENABLED (deep mastery focus)")
    print(f"{'='*60}\n")
    
    # Add diversity mode to config if requested
    if args.diversity:
        config['agi_mode'] = True
    
    # Add specialist mode to config if requested
    if args.specialist:
        config['specialist_mode'] = True
    
    # Create and run
    runner = AutonomousEvolutionRunner(**config)
    asyncio.run(runner.run())


if __name__ == "__main__":
    main()
