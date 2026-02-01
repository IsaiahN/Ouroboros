#!/usr/bin/env python3
import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
Optimization Threshold System
=============================

Tracks optimization progress per game-level and determines when a level is
"sufficiently optimized" (diminishing returns). Once optimized, optimizers
should use the best sequence and move on to unoptimized levels.

Philosophy:
- Track optimization improvement rate per generation
- If improvement < X% for N generations → level is "optimized"
- Optimizers use best sequence for optimized levels (no more attempts)
- Focus optimizer effort on high-value targets (unoptimized/unbeaten)

Rule 2: All data in database
Rule 4: LLM Self-Management - adaptive thresholds
"""

import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


class OptimizationThresholdSystem:
    """
    Determines when game-levels are sufficiently optimized.

    A level is considered "optimized" when:
    1. Has at least MIN_SEQUENCES sequences (3+)
    2. Improvement rate < OPTIMIZATION_THRESHOLD (2%) for STAGNATION_GENERATIONS (3)
    3. Best sequence has reasonable efficiency (>0.01 score/action)

    Once optimized, optimizers should:
    - Use best sequence for that level (no more optimization attempts)
    - Focus on unoptimized levels or unbeaten levels
    - Maximize efficiency by working on high-value targets
    """

    def __init__(self, db: DatabaseInterface):
        self.db = db

        # Optimization thresholds (adaptive)
        self.OPTIMIZATION_THRESHOLD = 0.02  # 2% improvement required to keep trying
        self.STAGNATION_GENERATIONS = 3     # Generations without improvement
        self.MIN_SEQUENCES = 3               # Need at least 3 sequences to call it optimized
        self.MIN_EFFICIENCY = 0.01           # Minimum efficiency score (prevent garbage sequences)

        self._initialize_database()

    def _initialize_database(self):
        """Create optimization tracking table"""
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS optimization_status (
                status_id TEXT PRIMARY KEY,
                game_id TEXT NOT NULL,
                level_number INTEGER NOT NULL,

                -- Optimization metrics
                is_optimized BOOLEAN DEFAULT FALSE,
                best_sequence_id TEXT,
                best_actions INTEGER,
                best_efficiency REAL,

                -- Tracking improvement
                last_improvement_generation INTEGER,
                generations_without_improvement INTEGER DEFAULT 0,
                improvement_rate REAL DEFAULT 0.0,  -- % improvement in recent generations

                -- Sequence diversity
                total_sequences INTEGER DEFAULT 0,
                active_sequences INTEGER DEFAULT 0,

                -- Timestamps
                first_sequence_at TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                optimized_at TIMESTAMP,

                UNIQUE(game_id, level_number)
            )
        """)

        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_optimization_game_level
            ON optimization_status(game_id, level_number)
        """)

        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_optimization_status
            ON optimization_status(is_optimized, generations_without_improvement)
        """)

        logger.info("[✓] Optimization threshold system initialized")

    def update_optimization_status(self, generation: int) -> Dict[str, int]:
        """
        Update optimization status for all game-levels based on current generation.

        Args:
            generation: Current generation number

        Returns:
            Dict with counts of optimized/unoptimized levels
        """
        logger.info(f"\n[OPTIMIZATION] Analyzing level optimization status (Gen {generation})")

        # Get all game-level combinations that have sequences
        game_levels = self.db.execute_query("""
            SELECT
                game_id,
                level_number,
                COUNT(*) as sequence_count,
                MIN(total_actions) as best_actions,
                MAX(efficiency_score) as best_efficiency,
                MIN(generation_discovered) as first_gen,
                MAX(generation_discovered) as last_gen,
                MIN(discovered_at) as first_time
            FROM winning_sequences
            WHERE is_active = TRUE
            GROUP BY game_id, level_number
        """)

        newly_optimized = 0
        still_optimizing = 0

        for gl in game_levels:
            game_id = gl['game_id']
            level_number = gl['level_number']
            sequence_count = gl['sequence_count']
            best_actions = gl['best_actions']
            best_efficiency = gl['best_efficiency']
            first_gen = gl['first_gen']
            last_gen = gl['last_gen']
            first_time = gl['first_time']

            # Get best sequence_id
            best_seq = self.db.execute_query("""
                SELECT sequence_id
                FROM winning_sequences
                WHERE game_id = ? AND level_number = ? AND is_active = TRUE
                ORDER BY total_actions ASC, efficiency_score DESC
                LIMIT 1
            """, (game_id, level_number))

            best_sequence_id = best_seq[0]['sequence_id'] if best_seq else None

            # Get existing status
            existing = self.db.execute_query("""
                SELECT * FROM optimization_status
                WHERE game_id = ? AND level_number = ?
            """, (game_id, level_number))

            if existing:
                status = existing[0]
                status_id = status['status_id']
                prev_best_actions = status['best_actions']
                prev_gen = status['last_improvement_generation']

                # Calculate improvement rate
                if prev_best_actions and prev_best_actions > 0:
                    improvement = (prev_best_actions - best_actions) / prev_best_actions
                else:
                    improvement = 0.0

                # Check if we improved
                if best_actions < prev_best_actions:
                    # Improved! Reset stagnation counter
                    generations_without_improvement = 0
                    last_improvement_generation = generation
                    improvement_rate = improvement
                else:
                    # No improvement
                    generations_without_improvement = status['generations_without_improvement'] + 1
                    last_improvement_generation = status['last_improvement_generation']
                    improvement_rate = status['improvement_rate'] * 0.9  # Decay old improvement rate

            else:
                # New game-level, create status
                import uuid
                status_id = f"opt_{uuid.uuid4().hex[:12]}"
                generations_without_improvement = 0
                last_improvement_generation = generation
                improvement_rate = 0.0

            # Determine if optimized
            is_optimized = (
                sequence_count >= self.MIN_SEQUENCES and
                generations_without_improvement >= self.STAGNATION_GENERATIONS and
                best_efficiency >= self.MIN_EFFICIENCY
            )

            # Track newly optimized
            if is_optimized and (not existing or not existing[0]['is_optimized']):
                newly_optimized += 1
                optimized_at = datetime.now().isoformat()
                logger.info(f"✓ {game_id} L{level_number} OPTIMIZED: {best_actions} actions, "
                          f"{sequence_count} sequences, {generations_without_improvement} gens stagnant")
            elif is_optimized:
                optimized_at = existing[0].get('optimized_at')
            else:
                optimized_at = None
                still_optimizing += 1

            # Update or insert status
            self.db.execute_query("""
                INSERT OR REPLACE INTO optimization_status (
                    status_id, game_id, level_number,
                    is_optimized, best_sequence_id, best_actions, best_efficiency,
                    last_improvement_generation, generations_without_improvement, improvement_rate,
                    total_sequences, active_sequences,
                    first_sequence_at, last_updated, optimized_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                status_id, game_id, level_number,
                is_optimized, best_sequence_id, best_actions, best_efficiency,
                last_improvement_generation, generations_without_improvement, improvement_rate,
                sequence_count, sequence_count,  # total_sequences = active_sequences for now
                first_time, datetime.now().isoformat(), optimized_at
            ))

        # Commit changes immediately
        self.db.checkpoint_wal()

        summary = {
            'total_levels': len(game_levels),
            'newly_optimized': newly_optimized,
            'optimized': sum(1 for gl in self._get_all_statuses() if gl['is_optimized']),
            'still_optimizing': still_optimizing
        }

        logger.info(f"[OPTIMIZATION] Summary: {summary['optimized']} optimized, "
                   f"{summary['still_optimizing']} still optimizing, "
                   f"{summary['newly_optimized']} newly optimized")

        # Cleanup stale entries where sequences no longer exist
        stale_count = self._cleanup_stale_optimization_status()
        if stale_count > 0:
            logger.info(f"[OPTIMIZATION] Cleaned up {stale_count} stale optimization_status entries (sequences deleted)")

        return summary

    def _cleanup_stale_optimization_status(self) -> int:
        """
        Remove optimization_status entries where the sequences no longer exist.
        This happens when sequences are purged/deleted but optimization_status wasn't updated.

        Returns:
            Number of stale entries removed
        """
        # Find optimization_status entries with no matching active sequences
        stale_entries = self.db.execute_query("""
            SELECT os.status_id, os.game_id, os.level_number
            FROM optimization_status os
            WHERE NOT EXISTS (
                SELECT 1 FROM winning_sequences ws
                WHERE ws.game_id = os.game_id
                  AND ws.level_number = os.level_number
                  AND ws.is_active = 1
            )
        """)

        if stale_entries:
            # Delete stale entries
            for entry in stale_entries:
                self.db.execute_query("""
                    DELETE FROM optimization_status
                    WHERE status_id = ?
                """, (entry['status_id'],))

            self.db.checkpoint_wal()
            sample_entries = [f"{e['game_id']} L{e['level_number']}" for e in stale_entries[:5]]
            logger.debug(f"Removed {len(stale_entries)} stale optimization_status entries: {sample_entries}")

        return len(stale_entries)

    def is_level_optimized(self, game_id: str, level_number: int) -> bool:
        """
        Check if a specific game-level is optimized.

        Args:
            game_id: Game identifier
            level_number: Level number

        Returns:
            True if optimized (optimizer should use best sequence, not try to optimize)
        """
        status = self.db.execute_query("""
            SELECT is_optimized FROM optimization_status
            WHERE game_id = ? AND level_number = ?
        """, (game_id, level_number))

        return status[0]['is_optimized'] if status else False

    def get_best_sequence_for_level(self, game_id: str, level_number: int) -> Optional[str]:
        """
        Get best sequence_id for an optimized level.

        Args:
            game_id: Game identifier
            level_number: Level number

        Returns:
            sequence_id of best sequence, or None
        """
        status = self.db.execute_query("""
            SELECT best_sequence_id FROM optimization_status
            WHERE game_id = ? AND level_number = ?
        """, (game_id, level_number))

        return status[0]['best_sequence_id'] if status else None

    def get_optimization_targets(self, agent_mode: str, limit: int = 10) -> List[Dict]:
        """
        Get prioritized list of game-levels for optimizer agents to target.

        Priority:
        1. Unbeaten levels (no sequences at all) - HIGH VALUE
        2. Unoptimized levels with sequences - MEDIUM VALUE
        3. Skip optimized levels - LOW VALUE (use best sequence)

        Args:
            agent_mode: Agent operating mode ('optimizer', 'pioneer', etc.)
            limit: Maximum targets to return

        Returns:
            List of game-level dictionaries with priority scores
        """
        if agent_mode != 'optimizer':
            # Non-optimizers don't use this system
            return []

        # RULE: Optimizers ONLY work on levels WITH existing sequences to optimize
        # Per Master Ruleset: "Work on beaten games ONLY" / "NEVER work on unbeaten LEVELS"

        # Get unoptimized levels that HAVE sequences (viable optimizer targets)
        unoptimized = self.db.execute_query("""
            SELECT
                game_id,
                level_number,
                best_actions,
                best_efficiency,
                generations_without_improvement,
                improvement_rate,
                total_sequences,
                'unoptimized' as priority_class
            FROM optimization_status
            WHERE is_optimized = FALSE
              AND total_sequences > 0  -- CRITICAL: Must have sequences to optimize!
            ORDER BY
                generations_without_improvement ASC,  -- Prefer recently improved
                improvement_rate DESC,                 -- Prefer high improvement potential
                best_actions DESC                      -- Prefer levels needing more optimization
            LIMIT ?
        """, (limit,))

        # REMOVED: Unbeaten levels logic
        # Optimizers should NEVER target games with NO sequences
        # That's Pioneer work! Optimizers refine EXISTING solutions.
        # Previous bug: Was sending optimizers to games with 0 sequences (like vc33)

        targets = unoptimized  # Only unoptimized levels WITH sequences

        return targets[:limit]

    def _get_all_statuses(self) -> List[Dict]:
        """Get all optimization statuses"""
        return self.db.execute_query("""
            SELECT * FROM optimization_status
            ORDER BY is_optimized ASC, generations_without_improvement DESC
        """)

    def print_optimization_report(self):
        """Print human-readable optimization status report"""
        statuses = self._get_all_statuses()

        if not statuses:
            print("\n[OPTIMIZATION] No levels tracked yet")
            return

        print("\n" + "="*80)
        print("[OPTIMIZATION STATUS REPORT]")
        print("="*80)

        optimized = [s for s in statuses if s['is_optimized']]
        unoptimized = [s for s in statuses if not s['is_optimized']]

        print(f"\nOptimized Levels: {len(optimized)}")
        print(f"Still Optimizing: {len(unoptimized)}")

        if optimized:
            print("\n--- OPTIMIZED LEVELS (use best sequence) ---")
            for s in optimized[:10]:
                print(f"  {s['game_id']} L{s['level_number']}: "
                      f"{s['best_actions']} actions, "
                      f"{s['total_sequences']} sequences, "
                      f"{s['generations_without_improvement']} gens stagnant")

        if unoptimized:
            print("\n--- UNOPTIMIZED LEVELS (optimization targets) ---")
            for s in unoptimized[:10]:
                print(f"  {s['game_id']} L{s['level_number']}: "
                      f"{s['best_actions']} actions, "
                      f"{s['total_sequences']} sequences, "
                      f"{s['generations_without_improvement']} gens stagnant, "
                      f"{s['improvement_rate']*100:.1f}% recent improvement")

        print("="*80 + "\n")


def main():
    """Test the optimization threshold system"""
    db = DatabaseInterface("core_data.db")
    system = OptimizationThresholdSystem(db)

    # Get current generation
    agents = db.execute_query("SELECT MAX(generation) as gen FROM agents")
    current_gen = agents[0]['gen'] if agents and agents[0]['gen'] else 0

    # Update optimization status
    summary = system.update_optimization_status(current_gen)

    # Print report
    system.print_optimization_report()

    # Show optimizer targets
    targets = system.get_optimization_targets('optimizer', limit=10)
    if targets:
        print("\n[OPTIMIZER TARGETS] Top priority levels:")
        for t in targets:
            print(f"  {t['game_id']} L{t['level_number']} - {t['priority_class']}")


if __name__ == "__main__":
    main()
