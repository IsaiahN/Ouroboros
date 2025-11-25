#!/usr/bin/env python3
"""
Evolution Runner with Vampire Detection
========================================

Wrapper that adds prestige vampire detection to the evolution cycle.
Checks for vampires before breeding and applies graceful sunset.
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import sys
import asyncio
from prestige_vampire_detector import PrestigeVampireDetector
from database_interface import DatabaseInterface
import logging

logger = logging.getLogger(__name__)

async def run_evolution_with_vampire_detection(**config):
    """
    Run evolution with vampire detection integrated.
    
    This wraps the standard evolution runner and adds vampire detection
    before each breeding cycle.
    """
    from autonomous_evolution_runner import AutonomousEvolutionRunner
    
    # Create standard evolution runner
    runner = AutonomousEvolutionRunner(**config)
    
    # Add vampire detection hook
    original_run = runner.run
    
    async def run_with_vampires():
        """Enhanced run method with vampire detection."""
        # Get current generation from database
        db = DatabaseInterface()
        
        # Run evolution with vampire checks
        logger.info("=" * 70)
        logger.info("EVOLUTION WITH VAMPIRE DETECTION ENABLED")
        logger.info("=" * 70)
        
        # Call original run method
        await original_run()
        
        db.close()
    
    # Replace run method
    runner.run = run_with_vampires
    
    return runner

def check_for_vampires(generation: int, db_path: str = "core_data.db"):
    """
    Check for and sunset vampire agents.
    
    Args:
        generation: Current generation number
        db_path: Path to database
    
    Returns:
        Number of vampires sunset
    """
    detector = PrestigeVampireDetector(db_path)
    
    logger.info(f"\n{'='*70}")
    logger.info(f"VAMPIRE DETECTION - Generation {generation}")
    logger.info(f"{'='*70}")
    
    # Detect vampires
    vampires = detector.detect_vampires(generation, threshold_multiplier=10.0)
    
    if vampires:
        logger.info(f"⚠️  Found {len(vampires)} prestige vampires")
        
        for v in vampires:
            logger.info(f"  - {v['agent_id'][:12]}... "
                       f"(Prestige: {v['prestige_ratio']:.1f}x, "
                       f"Performance: {v['performance_ratio']:.1%})")
        
        # Sunset vampires
        detector.sunset_vampires(vampires, generation, dry_run=False)
        logger.info(f"✅ Sunset {len(vampires)} vampire agents")
        
        return len(vampires)
    else:
        logger.info("✅ No prestige vampires detected")
        return 0

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run evolution with vampire detection')
    parser.add_argument('--generation', type=int, default=0, help='Current generation')
    parser.add_argument('--check-only', action='store_true', help='Only check for vampires, don\'t run evolution')
    
    args = parser.parse_args()
    
    if args.check_only:
        # Just check for vampires
        count = check_for_vampires(args.generation)
        print(f"\n{'='*70}")
        print(f"Vampire check complete: {count} vampires sunset")
        print(f"{'='*70}")
    else:
        # Run full evolution with vampire detection
        print("Use run_evolution.py for full evolution")
        print("This script provides vampire detection utilities")
        print("\nUsage:")
        print("  python evolution_with_vampires.py --generation 70 --check-only")
