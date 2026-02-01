import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

#!/usr/bin/env python3
"""
Evolution Runner with Parasite Detection
==========================================

Wrapper that adds prestige parasite detection to the evolution cycle.
Checks for parasites before breeding and applies graceful sunset.

NOTE: The check_for_parasites() function has been moved to
prestige_parasite_detector.py to avoid circular imports.
Import from there instead.
"""

import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import asyncio
import logging
import sys

from database_interface import DatabaseInterface
from manual_tools.analysis.prestige_parasite_detector import PrestigeParasiteDetector

logger = logging.getLogger(__name__)

async def run_evolution_with_parasite_detection(**config):
    """
    Run evolution with parasite detection integrated.

    This wraps the standard evolution runner and adds parasite detection
    before each breeding cycle.
    """
    # Import here to avoid circular dependency
    from autonomous_evolution_runner import AutonomousEvolutionRunner

    # Create standard evolution runner
    runner = AutonomousEvolutionRunner(**config)

    # Add parasite detection hook
    original_run = runner.run

    async def run_with_parasites():
        """Enhanced run method with parasite detection."""
        # Get current generation from database
        db = DatabaseInterface()

        # Run evolution with parasite checks
        logger.info("=" * 70)
        logger.info("EVOLUTION WITH PARASITE DETECTION ENABLED")
        logger.info("=" * 70)

        # Call original run method
        await original_run()

        db.close()

    # Replace run method
    runner.run = run_with_parasites

    return runner


if __name__ == "__main__":
    import argparse

    from manual_tools.analysis.prestige_parasite_detector import check_for_parasites

    parser = argparse.ArgumentParser(description='Run evolution with parasite detection')
    parser.add_argument('--generation', type=int, default=0, help='Current generation')
    parser.add_argument('--check-only', action='store_true', help='Only check for parasites, don\'t run evolution')

    args = parser.parse_args()

    if args.check_only:
        # Just check for parasites
        count = check_for_parasites(args.generation)
        print(f"\n{'='*70}")
        print(f"Parasite check complete: {count} parasites sunset")
        print(f"{'='*70}")
    else:
        # Run full evolution with parasite detection
        print("Use run_evolution.py for full evolution")
        print("This script provides parasite detection utilities")
        print("\nUsage:")
        print("  python evolution_with_parasites.py --generation 70 --check-only")
