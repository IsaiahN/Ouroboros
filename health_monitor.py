#!/usr/bin/env python3
"""
HealthMonitor — post-generation health assertions and cleanup.

Extracted from EvolutionRunner._run_generation_health_checks
and _run_safe_cleanup (Phase 4.1 decomposition).

Receives ALL dependencies via constructor injection.
Does NOT create its own DB connections.
"""

import os
import sys

sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from typing import Any, Dict, Optional

from database_interface import DatabaseInterface


class HealthMonitor:
    """Post-generation health assertions and scheduled cleanup.

    Catches the EXACT bug patterns from sessions 7n-7p:
    - Fitness pipeline disconnection (game_results -> agent_arc_performance)
    - Population bloat (zombie agents from failed culling)
    - Zero evolution signal (random drift for N generations)

    Prints [HEALTH-WARN] / [HEALTH-CRIT] but does NOT gate execution.
    These are diagnostic signals, not hard stops.
    """

    def __init__(
        self,
        db: DatabaseInterface,
        population_size: int = 100,
        verbose: bool = False,
    ):
        self.db = db
        self.population_size = population_size
        self.verbose = verbose

    def run_generation_health_checks(
        self,
        current_generation: int,
        stats: Optional[Dict] = None,
    ) -> None:
        """Post-generation health assertions.

        Args:
            current_generation: The generation just completed.
            stats: Optional generation statistics dict.
        """
        try:
            # CHECK 1: Population size sanity
            active_count_rows = self.db.execute_query(
                "SELECT COUNT(*) as cnt FROM agents WHERE is_active = 1"
            )
            active_count = active_count_rows[0]['cnt'] if active_count_rows else 0

            bloat_ratio = active_count / max(self.population_size, 1)
            if bloat_ratio > 2.0:
                print(f"  [HEALTH-CRIT] Population bloat: {active_count} active "
                      f"vs {self.population_size} expected ({bloat_ratio:.1f}x)")
            elif bloat_ratio > 1.5:
                print(f"  [HEALTH-WARN] Population slightly bloated: "
                      f"{active_count} vs {self.population_size} expected")

            # CHECK 2: Fitness pipeline -- agent_arc_performance must grow with game_results
            # NOTE: agent_arc_performance has NO 'generation' column.
            # Previous code queried WHERE generation = ? which silently failed
            # inside the try/except -- the very watchdog designed to catch
            # fitness disconnection was itself broken (Junction 10).
            # Use game_results.generation to find this gen's session_ids,
            # then count matching arc_performance rows.
            gr_rows = self.db.execute_query(
                "SELECT COUNT(*) as cnt FROM game_results "
                "WHERE generation = ?", [current_generation]
            )
            gr_count = gr_rows[0]['cnt'] if gr_rows else 0

            if gr_count > 0:
                # Count arc_performance rows for the same sessions
                arc_rows = self.db.execute_query("""
                    SELECT COUNT(*) as cnt FROM agent_arc_performance ap
                    WHERE EXISTS (
                        SELECT 1 FROM game_results gr
                        WHERE gr.session_id = ap.session_id
                        AND gr.generation = ?
                    )
                """, [current_generation])
                arc_count = arc_rows[0]['cnt'] if arc_rows else 0

                if arc_count == 0:
                    print(f"  [HEALTH-CRIT] Fitness disconnected: {gr_count} game_results "
                          f"this gen but 0 agent_arc_performance rows! "
                          f"Evolution has ZERO selection signal.")

            # CHECK 3: Evolution signal -- are scores improving?
            if current_generation > 20 and current_generation % 10 == 0:
                trend_rows = self.db.execute_query("""
                    SELECT AVG(final_score) as avg_score FROM game_results
                    WHERE generation BETWEEN ? AND ?
                """, [current_generation - 10, current_generation])
                recent_avg = trend_rows[0]['avg_score'] if trend_rows and trend_rows[0]['avg_score'] else 0

                if recent_avg == 0.0:
                    print(f"  [HEALTH-WARN] Average score is 0.0 for last 10 generations. "
                          f"Evolution may lack selection signal.")

        except Exception as e:
            # Health checks must NEVER crash the evolution loop
            if self.verbose:
                print(f"  [HEALTH-ERR] Health check failed: {e}")

    def run_safe_cleanup(self, current_generation: int) -> None:
        """Rule 12 compliance: Run SafeDatabaseCleaner every 10 generations.

        Per Master Ruleset: "Automatic: Runs every 10 generations in
        autonomous_evolution_runner.py"

        Also truncates observation_log.jsonl to keep only the latest 10k lines.

        Args:
            current_generation: Current generation number.
        """
        if current_generation % 10 != 0 or current_generation == 0:
            return

        # Truncate observation log (rolling 10k lines)
        self._truncate_observation_log()

        try:
            from safe_cleanup import SafeDatabaseCleaner
            cleaner = SafeDatabaseCleaner(db_path=self.db.db_path)
            results = cleaner.cleanup(dry_run=False, verbose=False)
            total_deleted = results.get('total_deleted', 0)
            if total_deleted > 0:
                print(f"  [CLEANUP] Rule 12: Cleaned {total_deleted} stale records "
                      f"(gen {current_generation})")
        except Exception as e:
            if self.verbose:
                print(f"  [CLEANUP-ERR] Safe cleanup failed: {e}")

    def _truncate_observation_log(
        self, path: str = "log/observation_log.jsonl", max_lines: int = 10_000
    ) -> None:
        """Keep only the latest max_lines in the observation log."""
        import os
        if not os.path.exists(path):
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            if len(lines) > max_lines:
                keep = lines[-max_lines:]
                with open(path, 'w', encoding='utf-8') as f:
                    f.writelines(keep)
                if self.verbose:
                    print(f"  [CLEANUP] Truncated observation log: "
                          f"{len(lines)} -> {len(keep)} lines")
        except Exception as e:
            if self.verbose:
                print(f"  [CLEANUP-ERR] Observation log truncation failed: {e}")
