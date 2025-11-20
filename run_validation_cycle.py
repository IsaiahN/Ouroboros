#!/usr/bin/env python3
"""
Sequence Validation Cycle with Repair Integration
==================================================

Orchestrates: Repair → Validate → Prune

Usage:
    python run_validation_cycle.py --repair --target-suspicious --prune
"""

import os
import asyncio
import argparse
import logging
from database_interface import DatabaseInterface
from validate_sequences import run_validation_batch
from sequence_pruning_system import SequencePruningSystem

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def target_suspicious_sequences(db: DatabaseInterface):
    """Queue high-usage sequences with no validation data."""
    logger.info("Targeting suspicious sequences...")
    
    query = """
        SELECT ws.sequence_id, ws.game_id
        FROM winning_sequences ws
        LEFT JOIN sequence_reputation sr ON ws.sequence_id = sr.sequence_id
        WHERE ws.is_active = 1
        AND ws.times_referenced > 10
        AND (sr.total_validation_attempts IS NULL OR sr.total_validation_attempts = 0)
        LIMIT 50
    """
    
    sequences = db.execute_query(query)
    
    count = 0
    for seq in sequences:
        db.execute_query("""
            INSERT OR IGNORE INTO sequence_validation_queue 
            (sequence_id, game_id, priority, status)
            VALUES (?, ?, 10, 'pending')
        """, (seq['sequence_id'], seq['game_id']))
        count += 1
        
    logger.info(f"Queued {count} high-usage sequences for validation")
    return count

async def run_cycle(target_suspicious: bool = False, prune: bool = False, repair: bool = False):
    """Run the full validation cycle: Repair → Validate → Prune"""
    db = DatabaseInterface()
    
    try:
        # Step 0: Repair sequences (if requested)
        if repair:
            logger.info("Starting sequence repair...")
            from repair_optimizer_sequences import SequenceRepairSystem
            repair_system = SequenceRepairSystem(db.db_path)
            repaired_count = await repair_system.repair_sequences(limit=50)
            logger.info(f"Repair complete: {repaired_count} sequences fixed")
        
        # Step 1: Target sequences
        if target_suspicious:
            target_suspicious_sequences(db)
            
        # Step 2: Run validation batch
        logger.info("Starting validation batch...")
        await run_validation_batch(max_validations=20)
        
        # Step 3: Prune failed sequences
        if prune:
            logger.info("Starting pruning cycle...")
            pruner = SequencePruningSystem(db)
            
            # Get current max generation to bypass grace period
            max_gen_row = db.execute_query("SELECT MAX(generation_discovered) as max_gen FROM winning_sequences")
            current_generation = max_gen_row[0]['max_gen'] if max_gen_row and max_gen_row[0]['max_gen'] else 0
            
            results = pruner.prune_bad_sequences(generation=current_generation + 2)
            
            logger.info(f"Pruning complete: {results['total_pruned']} sequences removed")
            if results.get('validation_failure', 0) > 0:
                logger.info(f"  - {results['validation_failure']} removed due to validation failure")
                
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run sequence validation cycle")
    parser.add_argument("--target-suspicious", action="store_true", help="Target suspicious sequences")
    parser.add_argument("--prune", action="store_true", help="Run pruning after validation")
    parser.add_argument("--repair", action="store_true", help="Attempt to repair failed sequences before validation")
    
    args = parser.parse_args()
    
    asyncio.run(run_cycle(
        target_suspicious=args.target_suspicious,
        prune=args.prune,
        repair=args.repair
    ))
