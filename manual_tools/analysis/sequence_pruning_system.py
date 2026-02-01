#!/usr/bin/env python3
import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
Sequence Pruning System
=======================

Removes bad sequences that fail repeatedly via voting system.
Runs at the end of each generation to clean up garbage sequences.

Following Rule 2: All data in database (no log files)
Following Rule 4: LLM self-management (autonomous cleanup)

Pruning Strategy:
- Track sequence usage across generations
- Give sequences 2 generations to prove themselves
- Remove sequences with <10% success rate after 10+ attempts
- Remove sequences with >10,000 actions (garbage)
- Remove sequences that score <2 points consistently
"""

import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from database_interface import DatabaseInterface
from database_logger import setup_database_logging

# Get logger properly
setup_database_logging(level='INFO')
logger = logging.getLogger(__name__)


class SequencePruningSystem:
    """
    Autonomous sequence cleanup system.

    Prunes bad sequences based on performance voting:
    - Usage tracking across generations
    - Success rate thresholds
    - Action count limits
    - Score quality filters
    """

    def __init__(self, db: DatabaseInterface):
        """
        Initialize pruning system.

        Args:
            db: Database interface
        """
        self.db = db

        # Pruning thresholds
        self.min_attempts_before_pruning = 5  # Lowered from 10 to catch bad sequences faster
        self.min_success_rate = 0.10  # 10%
        self.max_action_count = 10000
        self.min_score_threshold = 2.0
        self.generations_grace_period = 2

    def prune_bad_sequences(self, current_generation: int, dry_run: bool = False) -> Dict[str, int]:
        """
        Prune sequences that have proven to be ineffective.

        Args:
            current_generation: Current generation number
            dry_run: If True, don't actually delete, just report

        Returns:
            Dict with counts of pruned sequences by reason
        """
        logger.info(f"[SEQUENCE PRUNING] Starting pruning for generation {current_generation}")

        results = {
            'low_success_rate': 0,
            'excessive_actions': 0,
            'low_score': 0,
            'validation_failure': 0,
            'total_pruned': 0,
            'total_kept': 0
        }

        # Get all active sequences
        sequences = self._get_all_sequences()

        logger.info(f"[SEQUENCE PRUNING] Found {len(sequences)} active sequences to evaluate")

        sequences_to_prune = []

        for seq in sequences:
            seq_id = seq['sequence_id']
            game_id = seq['game_id']
            total_actions = seq['total_actions']
            total_score = seq['total_score']
            times_referenced = seq['times_referenced']
            success_rate = seq['success_rate_when_reused']
            generation_discovered = seq['generation_discovered']

            # Calculate age in generations
            age_generations = current_generation - generation_discovered

            # Grace period: Don't prune sequences younger than 2 generations
            if age_generations < self.generations_grace_period:
                continue

            prune_reason = None

            # Rule 1: Excessive actions (obvious garbage)
            if total_actions > self.max_action_count:
                prune_reason = 'excessive_actions'
                results['excessive_actions'] += 1

            # Rule 2: Low success rate after sufficient attempts
            elif times_referenced >= self.min_attempts_before_pruning:
                if success_rate < self.min_success_rate:
                    prune_reason = 'low_success_rate'
                    results['low_success_rate'] += 1

            # Rule 3: Consistently low score
            elif times_referenced >= self.min_attempts_before_pruning:
                if total_score < self.min_score_threshold:
                    prune_reason = 'low_score'
                    results['low_score'] += 1

            # Rule 4: Validation Failure (Independent check - not elif)
            # Prune if validated 3+ times with 0% success, or 5+ times with <20% success
            if not prune_reason and seq.get('validation_attempts', 0) >= 3:
                attempts = seq['validation_attempts']
                successes = seq['validation_successes']
                val_rate = successes / attempts if attempts > 0 else 0.0

                if successes == 0:
                    prune_reason = 'validation_failure_zero_success'
                    results['validation_failure'] = results.get('validation_failure', 0) + 1
                elif attempts >= 5 and val_rate < 0.2:
                    prune_reason = 'validation_failure_low_rate'
                    results['validation_failure'] = results.get('validation_failure', 0) + 1

            if prune_reason:
                sequences_to_prune.append({
                    'seq_id': seq_id,
                    'game_id': game_id,
                    'reason': prune_reason,
                    'actions': total_actions,
                    'score': total_score,
                    'attempts': times_referenced,
                    'success_rate': success_rate,
                    'age': age_generations
                })

        results['total_pruned'] = len(sequences_to_prune)
        results['total_kept'] = len(sequences) - len(sequences_to_prune)

        # Log pruning details
        logger.info(f"[SEQUENCE PRUNING] Identified {len(sequences_to_prune)} sequences for removal")

        if dry_run:
            logger.info("[SEQUENCE PRUNING] DRY RUN - Not actually deleting sequences")
            self._log_pruning_details(sequences_to_prune)
            return results

        # Deactivate sequences (don't delete for audit trail)
        for seq_info in sequences_to_prune:
            self._deactivate_sequence(
                seq_info['seq_id'],
                seq_info['reason'],
                current_generation
            )

            logger.info(
                f"[SEQUENCE PRUNING] Deactivated {seq_info['seq_id'][:8]}... ({seq_info['game_id']}): "
                f"{seq_info['reason']} | Actions: {seq_info['actions']} | "
                f"Score: {seq_info['score']:.1f} | Success: {seq_info['success_rate']:.1%} "
                f"({seq_info['attempts']} attempts)"
            )

        # Log summary
        logger.info(
            f"[SEQUENCE PRUNING] Complete - "
            f"Pruned: {results['total_pruned']} | "
            f"Kept: {results['total_kept']} | "
            f"Reasons: excessive_actions={results['excessive_actions']}, "
            f"low_success={results['low_success_rate']}, "
            f"low_score={results['low_score']}"
        )

        # Store pruning event in database
        self._record_pruning_event(current_generation, results, sequences_to_prune)

        return results

    def _get_all_sequences(self) -> List[Dict]:
        """Get all active sequences with their metrics."""
        query = """
        SELECT
            ws.sequence_id,
            ws.game_id,
            ws.total_actions,
            ws.total_score,
            ws.times_referenced,
            ws.success_rate_when_reused,
            ws.generation_discovered,
            ws.discovered_at,
            sr.total_validation_attempts as validation_attempts,
            sr.successful_validations as validation_successes
        FROM winning_sequences ws
        LEFT JOIN sequence_reputation sr ON ws.sequence_id = sr.sequence_id
        WHERE ws.is_active = 1
        ORDER BY ws.times_referenced DESC
        """

        rows = self.db.execute_query(query)

        sequences = []
        if rows:
            for row in rows:
                sequences.append({
                    'sequence_id': row['sequence_id'],
                    'game_id': row['game_id'],
                    'total_actions': row['total_actions'],
                    'total_score': row['total_score'],
                    'times_referenced': row['times_referenced'],
                    'success_rate_when_reused': row['success_rate_when_reused'] if row['success_rate_when_reused'] is not None else 0.0,
                    'generation_discovered': row['generation_discovered'] if row['generation_discovered'] is not None else 0,
                    'discovered_at': row['discovered_at'],
                    'validation_attempts': row['validation_attempts'] if row['validation_attempts'] is not None else 0,
                    'validation_successes': row['validation_successes'] if row['validation_successes'] is not None else 0
                })

        return sequences

    def _deactivate_sequence(self, sequence_id: str, reason: str, generation: int):
        """
        Deactivate a sequence (don't delete for audit trail).

        Args:
            sequence_id: Sequence to deactivate
            reason: Reason for deactivation
            generation: Current generation
        """
        query = """
        UPDATE winning_sequences
        SET
            is_active = 0,
            last_referenced = CURRENT_TIMESTAMP
        WHERE sequence_id = ?
        """

        self.db.execute_query(query, (sequence_id,))

    def _record_pruning_event(
        self,
        generation: int,
        results: Dict[str, int],
        pruned_sequences: List[Dict]
    ):
        """
        Record pruning event in system_logs for audit trail.

        Args:
            generation: Current generation
            results: Pruning results summary
            pruned_sequences: List of pruned sequence details
        """
        event_details = {
            'generation': generation,
            'total_pruned': results['total_pruned'],
            'total_kept': results['total_kept'],
            'reasons': {
                'excessive_actions': results['excessive_actions'],
                'low_success_rate': results['low_success_rate'],
                'low_score': results['low_score']
            },
            'pruned_sequences': [
                {
                    'seq_id': seq['seq_id'][:8],
                    'game_id': seq['game_id'],
                    'reason': seq['reason'],
                    'actions': seq['actions'],
                    'score': seq['score'],
                    'attempts': seq['attempts'],
                    'success_rate': seq['success_rate']
                }
                for seq in pruned_sequences[:10]  # Limit to first 10 for space
            ]
        }

        import json

        log_query = """
        INSERT INTO system_logs (level, logger_name, message, extra_data)
        VALUES (?, ?, ?, ?)
        """

        self.db.execute_query(
            log_query,
            (
                'INFO',
                'sequence_pruning',
                f'Sequence pruning completed for generation {generation}',
                json.dumps(event_details)
            )
        )

    def _log_pruning_details(self, sequences_to_prune: List[Dict]):
        """Log details of sequences that would be pruned (dry run)."""
        if not sequences_to_prune:
            logger.info("[SEQUENCE PRUNING] No sequences to prune")
            return

        logger.info(f"[SEQUENCE PRUNING] Would prune {len(sequences_to_prune)} sequences:")

        for seq in sequences_to_prune[:20]:  # Show first 20
            logger.info(
                f"  {seq['seq_id'][:8]}... ({seq['game_id']}): "
                f"{seq['reason']} | Actions: {seq['actions']} | "
                f"Score: {seq['score']:.1f} | Success: {seq['success_rate']:.1%} "
                f"({seq['attempts']} attempts) | Age: {seq['age']} generations"
            )

    def get_pruning_stats(self) -> Dict[str, Any]:
        """
        Get statistics about sequence quality and pruning history.

        Returns:
            Dict with sequence quality metrics
        """
        stats = {}

        # Active sequences
        active_query = """
        SELECT
            COUNT(*) as total,
            AVG(times_referenced) as avg_uses,
            AVG(success_rate_when_reused) as avg_success_rate,
            SUM(CASE WHEN times_referenced >= 10 THEN 1 ELSE 0 END) as well_tested,
            SUM(CASE WHEN success_rate_when_reused >= 0.5 THEN 1 ELSE 0 END) as high_success
        FROM winning_sequences
        WHERE is_active = 1
        """

        result = self.db.execute_query(active_query)
        if result:
            row = result[0]
            stats['active_sequences'] = row['total']
            stats['avg_uses'] = row['avg_uses'] or 0.0
            stats['avg_success_rate'] = row['avg_success_rate'] or 0.0
            stats['well_tested'] = row['well_tested'] or 0
            stats['high_success'] = row['high_success'] or 0

        # Inactive sequences (pruned)
        inactive_query = """
        SELECT COUNT(*) as count FROM winning_sequences WHERE is_active = 0
        """

        result = self.db.execute_query(inactive_query)
        if result:
            stats['pruned_sequences'] = result[0]['count']

        # Recent pruning events
        pruning_events_query = """
        SELECT COUNT(*) as count
        FROM system_logs
        WHERE message LIKE '%Sequence pruning completed%'
            AND timestamp > datetime('now', '-7 days')
        """

        result = self.db.execute_query(pruning_events_query)
        if result:
            stats['pruning_events_last_7_days'] = result[0]['count']

        return stats


def display_pruning_report(stats: Dict[str, Any]):
    """
    Display a formatted pruning statistics report.

    Args:
        stats: Statistics dict from get_pruning_stats()
    """
    print("\n" + "="*70)
    print("SEQUENCE QUALITY & PRUNING REPORT")
    print("="*70)

    print(f"\nActive Sequences: {stats.get('active_sequences', 0)}")
    print(f"  Average Uses: {stats.get('avg_uses', 0):.1f}")
    print(f"  Average Success Rate: {stats.get('avg_success_rate', 0):.1%}")
    print(f"  Well-Tested (≥10 uses): {stats.get('well_tested', 0)}")
    print(f"  High Success (≥50%): {stats.get('high_success', 0)}")

    print(f"\nPruned Sequences: {stats.get('pruned_sequences', 0)}")
    print(f"Pruning Events (last 7 days): {stats.get('pruning_events_last_7_days', 0)}")

    # Quality assessment
    active = stats.get('active_sequences', 0)
    high_success = stats.get('high_success', 0)

    if active > 0:
        quality_pct = (high_success / active) * 100
        print(f"\nSequence Quality: {quality_pct:.1f}% high-success")

        if quality_pct < 20:
            print("  [WARN]  Low quality - most sequences failing")
        elif quality_pct < 50:
            print("  ⚙️  Moderate quality - some good sequences")
        else:
            print("  ✓  Good quality - many reliable sequences")

    print("="*70)


if __name__ == "__main__":
    """Command-line interface for sequence pruning."""
    import argparse

    parser = argparse.ArgumentParser(description="Prune bad sequences from database")
    parser.add_argument('--generation', type=int, default=0, help='Current generation number')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be pruned without deleting')
    parser.add_argument('--stats', action='store_true', help='Show pruning statistics')

    args = parser.parse_args()

    db = DatabaseInterface()
    pruner = SequencePruningSystem(db)

    if args.stats:
        stats = pruner.get_pruning_stats()
        display_pruning_report(stats)
    else:
        results = pruner.prune_bad_sequences(args.generation, dry_run=args.dry_run)

        print("\n" + "="*70)
        print("SEQUENCE PRUNING RESULTS")
        print("="*70)
        print(f"Total Pruned: {results['total_pruned']}")
        print(f"Total Kept: {results['total_kept']}")
        print(f"\nPruning Reasons:")
        print(f"  Excessive Actions (>10K): {results['excessive_actions']}")
        print(f"  Low Success Rate (<10%): {results['low_success_rate']}")
        print(f"  Low Score (<2 pts): {results['low_score']}")
        print("="*70)

        if args.dry_run:
            print("\n[WARN]  DRY RUN - No sequences were actually deleted")
        else:
            print("\n✓ Sequences deactivated (audit trail preserved)")
