import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
AutopoiesisMonitor - Core autopoiesis metrics for self-regulation.

Part of the Societal Metrics System.
See DOCS/Societal_Metrics_Implementation_Analysis.md for design rationale.

Autopoiesis = Self-creation and self-maintenance
The system must observe itself not just to improve,
but to maintain its identity as a learning organism.

Key Metrics:
- Emergence Gain: Is network smarter than sum of agents?
- Functional Identity Drift: Are we still optimizing the right goals?
- Control Error: Is regulation undershooting or overshooting?
- Loop Detection: Are agents stuck in oscillations?
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class AutopoiesisMonitor:
    """
    Monitor core autopoiesis metrics for system self-regulation.

    Autopoiesis Role: Central identity and emergence monitoring
    Problem Solved: System observing itself to maintain coherent identity

    The autopoietic system must:
    1. Maintain boundary integrity (not drift from original goals)
    2. Generate emergence (network > sum of parts)
    3. Self-regulate (feedback loops work correctly)
    4. Detect stuck states (oscillations, loops)

    Usage:
        monitor = AutopoiesisMonitor(db)
        health = monitor.get_system_health(generation)

        if health['identity_drift'] > 0.3:
            reset_metric_weights()
    """

    # Target values for control
    TARGET_FRONTIER_PROGRESS_PER_GEN = 0.5  # New levels beaten per generation
    IDENTITY_DRIFT_THRESHOLD = 0.3          # Max acceptable drift
    EMERGENCE_GAIN_MINIMUM = 1.0            # Network must outperform individuals

    def __init__(self, db):
        """
        Initialize with database interface (dependency injection).

        Args:
            db: DatabaseInterface instance for persistence
        """
        self.db = db
        self._ensure_schema()

    def _ensure_schema(self):
        """Create autopoiesis tables if not exist (idempotent)."""
        try:
            # Ecosystem metrics table (shared with other modules)
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS ecosystem_metrics (
                    metric_name TEXT NOT NULL,
                    generation INTEGER NOT NULL,
                    value REAL NOT NULL,
                    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    PRIMARY KEY (metric_name, generation)
                )
            """)

            # Autopoiesis snapshots
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS autopoiesis_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    generation INTEGER NOT NULL,
                    emergence_gain REAL,
                    identity_drift REAL,
                    control_error REAL,
                    loop_detection_score REAL,
                    overall_health REAL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_autopoiesis_gen
                ON autopoiesis_snapshots(generation)
            """)

        except Exception as e:
            logger.warning(f"Schema creation warning (may already exist): {e}")

    # =========================================================================
    # EMERGENCE GAIN
    # =========================================================================

    def calculate_emergence_gain(self, generation: int) -> float:
        """
        Calculate if network intelligence exceeds sum of individual agents.

        Emergence Gain > 1.0 means collective intelligence is working.

        Formula:
            network_wins_using_shared_knowledge / max(solo_discoveries, 1)

        Args:
            generation: Current generation

        Returns:
            Emergence gain ratio (>1.0 = emergence working)
        """
        try:
            # Network level: Wins where agent used sequence discovered by another
            network_wins_result = self.db.execute_query("""
                SELECT COUNT(*) as count
                FROM agent_arc_performance aap
                WHERE aap.game_timestamp > datetime('now', '-7 days')
                  AND EXISTS (
                      SELECT 1 FROM winning_sequences ws
                      WHERE ws.game_id = aap.game_id
                        AND ws.discovered_by_agent_id != aap.agent_id
                        AND ws.times_referenced > 0
                  )
            """)
            network_wins = network_wins_result[0]['count'] if network_wins_result else 0

            # Individual level: Sequences discovered that were never shared/reused
            solo_result = self.db.execute_query("""
                SELECT COUNT(DISTINCT sequence_id) as count
                FROM winning_sequences
                WHERE discovered_at > datetime('now', '-7 days')
                  AND times_referenced = 0
            """)
            solo_discoveries = max(solo_result[0]['count'] if solo_result else 1, 1)

            emergence_gain = network_wins / solo_discoveries

            # Store metric
            self._store_metric('emergence_gain', generation, emergence_gain)

            logger.info(f"[EMERGENCE] Generation {generation}: "
                       f"gain={emergence_gain:.2f} "
                       f"(network_wins={network_wins}, solo={solo_discoveries})")

            return emergence_gain

        except Exception as e:
            logger.error(f"Error calculating emergence gain: {e}")
            return 1.0  # Neutral on error

    # =========================================================================
    # IDENTITY DRIFT
    # =========================================================================

    def calculate_identity_drift(self, generation: int) -> float:
        """
        Calculate if system is drifting from original goals.

        Original goal: Beat all levels of all games
        Drift = optimizing proxies instead of the actual goal

        Drift signals:
        - High prestige without actual discoveries
        - Actions without level progress
        - Sequences created but never validated/used

        Args:
            generation: Current generation

        Returns:
            Identity drift (0.0 = aligned, 1.0 = completely drifted)
        """
        try:
            # Positive: Frontier levels beaten (actual progress)
            frontier_result = self.db.execute_query("""
                SELECT COUNT(DISTINCT game_id || '-' || level_number) as count
                FROM winning_sequences
                WHERE discovered_at > datetime('now', '-7 days')
                  AND is_active = 1
            """)
            frontier_progress = max(frontier_result[0]['count'] if frontier_result else 0, 1)

            # Negative signal 1: High prestige agents with low contributions
            prestige_parasite_result = self.db.execute_query("""
                SELECT COUNT(*) as count
                FROM agents a
                WHERE a.is_active = 1
                  AND a.prestige > (SELECT AVG(prestige) * 2 FROM agents WHERE is_active = 1)
                  AND (
                      SELECT COUNT(*) FROM winning_sequences ws
                      WHERE ws.discovered_by_agent_id = a.agent_id
                        AND ws.discovered_at > datetime('now', '-7 days')
                  ) = 0
            """)
            prestige_without_value = prestige_parasite_result[0]['count'] if prestige_parasite_result else 0

            # Negative signal 2: Games played with zero progress
            wasted_result = self.db.execute_query("""
                SELECT COUNT(*) as count
                FROM game_results
                WHERE game_timestamp > datetime('now', '-24 hours')
                  AND final_score = 0
            """)
            wasted_actions = wasted_result[0]['count'] if wasted_result else 0

            # Negative signal 3: Sequences never validated
            orphan_result = self.db.execute_query("""
                SELECT COUNT(*) as count
                FROM winning_sequences
                WHERE discovered_at > datetime('now', '-7 days')
                  AND times_validated = 0
                  AND times_referenced = 0
            """)
            orphan_sequences = orphan_result[0]['count'] if orphan_result else 0

            # Calculate drift
            negative_signals = prestige_without_value + (wasted_actions / 10) + orphan_sequences
            drift = negative_signals / (frontier_progress * 10)
            drift = min(1.0, drift)  # Cap at 1.0

            # Store metric
            self._store_metric('identity_drift', generation, drift, metadata={
                'frontier_progress': frontier_progress,
                'prestige_parasites': prestige_without_value,
                'wasted_games': wasted_actions,
                'orphan_sequences': orphan_sequences
            })

            if drift > self.IDENTITY_DRIFT_THRESHOLD:
                logger.warning(f"[DRIFT] High identity drift detected: {drift:.2f} "
                              f"(threshold: {self.IDENTITY_DRIFT_THRESHOLD})")
            else:
                logger.info(f"[DRIFT] Identity drift: {drift:.2f}")

            return drift

        except Exception as e:
            logger.error(f"Error calculating identity drift: {e}")
            return 0.0  # Assume no drift on error

    # =========================================================================
    # CONTROL ERROR
    # =========================================================================

    def calculate_control_error(self, generation: int) -> float:
        """
        Calculate if regulation is overshooting or undershooting targets.

        Control Error = target - actual
        Positive error = undershooting (need more)
        Negative error = overshooting (need less)

        Args:
            generation: Current generation

        Returns:
            Control error (positive = undershooting, negative = overshooting)
        """
        try:
            # Get actual frontier progress this generation
            actual_result = self.db.execute_query("""
                SELECT COUNT(DISTINCT game_id || '-' || level_number) as count
                FROM winning_sequences
                WHERE generation = ?
            """, (generation,))
            actual = actual_result[0]['count'] if actual_result else 0

            control_error = self.TARGET_FRONTIER_PROGRESS_PER_GEN - actual

            # Store metric
            self._store_metric('control_error', generation, control_error, metadata={
                'target': self.TARGET_FRONTIER_PROGRESS_PER_GEN,
                'actual': actual
            })

            if abs(control_error) > 0.5:
                logger.warning(f"[CONTROL] High control error: {control_error:.2f} "
                              f"(target={self.TARGET_FRONTIER_PROGRESS_PER_GEN}, actual={actual})")
            else:
                logger.info(f"[CONTROL] Control error: {control_error:.2f}")

            return control_error

        except Exception as e:
            logger.error(f"Error calculating control error: {e}")
            return 0.0

    # =========================================================================
    # LOOP DETECTION
    # =========================================================================

    def calculate_loop_detection_score(self, generation: int) -> float:
        """
        Calculate how many agents appear to be stuck in loops.

        Loop signals:
        - Same games played repeatedly without progress
        - Action patterns repeating
        - Score stagnation

        Args:
            generation: Current generation

        Returns:
            Loop score (0.0 = no loops, 1.0 = many agents stuck)
        """
        try:
            # Agents playing same game repeatedly without score improvement
            stuck_result = self.db.execute_query("""
                SELECT COUNT(DISTINCT agent_id) as count
                FROM (
                    SELECT agent_id, game_id,
                           COUNT(*) as plays,
                           MAX(final_score) - MIN(final_score) as score_delta
                    FROM game_results
                    WHERE game_timestamp > datetime('now', '-24 hours')
                    GROUP BY agent_id, game_id
                    HAVING plays > 5 AND score_delta < 1
                )
            """)
            stuck_agents = stuck_result[0]['count'] if stuck_result else 0

            # Total active agents
            total_result = self.db.execute_query("""
                SELECT COUNT(*) as count FROM agents WHERE is_active = 1
            """)
            total_agents = max(total_result[0]['count'] if total_result else 1, 1)

            loop_score = stuck_agents / total_agents

            # Store metric
            self._store_metric('loop_detection', generation, loop_score, metadata={
                'stuck_agents': stuck_agents,
                'total_agents': total_agents
            })

            if loop_score > 0.3:
                logger.warning(f"[LOOP] High loop detection: {loop_score:.2f} "
                              f"({stuck_agents}/{total_agents} agents stuck)")
            else:
                logger.info(f"[LOOP] Loop detection score: {loop_score:.2f}")

            return loop_score

        except Exception as e:
            logger.error(f"Error calculating loop detection: {e}")
            return 0.0

    # =========================================================================
    # AGGREGATED HEALTH
    # =========================================================================

    def get_system_health(self, generation: int) -> Dict[str, Any]:
        """
        Calculate comprehensive system health metrics.

        Aggregates all autopoiesis metrics into a single health snapshot.

        Args:
            generation: Current generation

        Returns:
            Dict with all health metrics and overall score
        """
        emergence_gain = self.calculate_emergence_gain(generation)
        identity_drift = self.calculate_identity_drift(generation)
        control_error = self.calculate_control_error(generation)
        loop_score = self.calculate_loop_detection_score(generation)

        # Calculate overall health (0.0 = critical, 1.0 = excellent)
        # Weight factors
        health_factors = []

        # Emergence: >1.0 is good
        emergence_health = min(emergence_gain, 2.0) / 2.0
        health_factors.append(emergence_health * 0.30)

        # Identity: 0.0 is good
        identity_health = 1.0 - identity_drift
        health_factors.append(identity_health * 0.30)

        # Control: near 0.0 is good
        control_health = 1.0 - min(abs(control_error), 1.0)
        health_factors.append(control_health * 0.20)

        # Loops: 0.0 is good
        loop_health = 1.0 - loop_score
        health_factors.append(loop_health * 0.20)

        overall_health = sum(health_factors)

        health = {
            'generation': generation,
            'emergence_gain': emergence_gain,
            'identity_drift': identity_drift,
            'control_error': control_error,
            'loop_detection_score': loop_score,
            'overall_health': overall_health,
            'status': self._get_health_status(overall_health),
            'warnings': self._get_warnings(
                emergence_gain, identity_drift, control_error, loop_score
            )
        }

        # Store snapshot
        self._store_snapshot(generation, health)

        logger.info(f"[HEALTH] Generation {generation}: "
                   f"overall={overall_health:.2f} ({health['status']})")

        return health

    def _get_health_status(self, overall_health: float) -> str:
        """Convert overall health score to status string."""
        if overall_health >= 0.8:
            return 'EXCELLENT'
        elif overall_health >= 0.6:
            return 'GOOD'
        elif overall_health >= 0.4:
            return 'FAIR'
        elif overall_health >= 0.2:
            return 'POOR'
        else:
            return 'CRITICAL'

    def _get_warnings(self, emergence: float, drift: float,
                      control: float, loops: float) -> List[str]:
        """Generate warnings for problematic metrics."""
        warnings = []

        if emergence < self.EMERGENCE_GAIN_MINIMUM:
            warnings.append(f"Low emergence gain ({emergence:.2f} < {self.EMERGENCE_GAIN_MINIMUM})")

        if drift > self.IDENTITY_DRIFT_THRESHOLD:
            warnings.append(f"High identity drift ({drift:.2f} > {self.IDENTITY_DRIFT_THRESHOLD})")

        if control > 0.5:
            warnings.append(f"Undershooting target (control error: {control:.2f})")
        elif control < -0.5:
            warnings.append(f"Overshooting target (control error: {control:.2f})")

        if loops > 0.3:
            warnings.append(f"Many agents stuck in loops ({loops:.0%})")

        return warnings

    # =========================================================================
    # STORAGE
    # =========================================================================

    def _store_metric(self, metric_name: str, generation: int,
                      value: float, metadata: Optional[Dict] = None):
        """Store a metric value in ecosystem_metrics table."""
        try:
            self.db.execute_query("""
                INSERT INTO ecosystem_metrics (metric_name, generation, value, metadata)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(metric_name, generation) DO UPDATE SET
                    value = excluded.value,
                    metadata = excluded.metadata,
                    measured_at = CURRENT_TIMESTAMP
            """, (metric_name, generation, value,
                  json.dumps(metadata) if metadata else None))

        except Exception as e:
            logger.error(f"Error storing metric {metric_name}: {e}")

    def _store_snapshot(self, generation: int, health: Dict[str, Any]):
        """Store autopoiesis snapshot."""
        try:
            import uuid
            snapshot_id = f"snap_{uuid.uuid4().hex[:12]}"

            self.db.execute_query("""
                INSERT INTO autopoiesis_snapshots
                (snapshot_id, generation, emergence_gain, identity_drift,
                 control_error, loop_detection_score, overall_health, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot_id, generation,
                health['emergence_gain'], health['identity_drift'],
                health['control_error'], health['loop_detection_score'],
                health['overall_health'],
                json.dumps({
                    'status': health['status'],
                    'warnings': health['warnings']
                })
            ))

        except Exception as e:
            logger.error(f"Error storing snapshot: {e}")

    # =========================================================================
    # QUERIES
    # =========================================================================

    def get_health_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent health snapshots."""
        try:
            result = self.db.execute_query("""
                SELECT * FROM autopoiesis_snapshots
                ORDER BY generation DESC
                LIMIT ?
            """, (limit,))

            return result if result else []

        except Exception as e:
            logger.error(f"Error getting health history: {e}")
            return []

    def get_metric_trend(self, metric_name: str,
                         window: int = 20) -> Dict[str, Any]:
        """
        Get trend analysis for a specific metric.

        Args:
            metric_name: Name of the metric
            window: Generations to analyze

        Returns:
            Dict with trend analysis
        """
        try:
            result = self.db.execute_query("""
                SELECT value, generation
                FROM ecosystem_metrics
                WHERE metric_name = ?
                ORDER BY generation DESC
                LIMIT ?
            """, (metric_name, window))

            if not result or len(result) < 2:
                return {'metric_name': metric_name, 'trend': 'UNKNOWN', 'data_points': 0}

            values = [r['value'] for r in result]

            # Calculate trend
            first_half = sum(values[len(values)//2:]) / len(values[len(values)//2:])
            second_half = sum(values[:len(values)//2]) / len(values[:len(values)//2])

            if second_half > first_half * 1.1:
                trend = 'IMPROVING'
            elif second_half < first_half * 0.9:
                trend = 'DECLINING'
            else:
                trend = 'STABLE'

            return {
                'metric_name': metric_name,
                'trend': trend,
                'current_value': values[0],
                'average': sum(values) / len(values),
                'min': min(values),
                'max': max(values),
                'data_points': len(values)
            }

        except Exception as e:
            logger.error(f"Error getting metric trend: {e}")
            return {'metric_name': metric_name, 'trend': 'ERROR', 'error': str(e)}

    def detect_regime_change(self, generation: int, window: int = 20) -> bool:
        """
        Detect if the system has entered a new regime.

        Regime change signals:
        - Task distribution shift (frontier -> optimization)
        - Correlation breakdown between metrics
        - Variance spike

        Args:
            generation: Current generation
            window: Generations to compare

        Returns:
            True if regime change detected
        """
        try:
            # Get metric values for recent vs historical
            recent_result = self.db.execute_query("""
                SELECT metric_name, AVG(value) as avg_value,
                       AVG(value * value) - AVG(value) * AVG(value) as variance
                FROM ecosystem_metrics
                WHERE generation > ? - ?
                GROUP BY metric_name
            """, (generation, window))

            historical_result = self.db.execute_query("""
                SELECT metric_name, AVG(value) as avg_value,
                       AVG(value * value) - AVG(value) * AVG(value) as variance
                FROM ecosystem_metrics
                WHERE generation > ? - ? AND generation <= ? - ?
                GROUP BY metric_name
            """, (generation, window * 2, generation, window))

            if not recent_result or not historical_result:
                return False

            # Check for variance spike
            recent_vars = {r['metric_name']: r['variance'] or 0 for r in recent_result}
            historical_vars = {r['metric_name']: r['variance'] or 0 for r in historical_result}

            variance_increase = 0
            for metric in recent_vars:
                if metric in historical_vars and historical_vars[metric] > 0:
                    ratio = recent_vars[metric] / historical_vars[metric]
                    if ratio > 2.0:  # Variance doubled
                        variance_increase += 1

            # If multiple metrics show variance spike, regime change likely
            regime_changed = variance_increase >= 2

            if regime_changed:
                logger.warning(f"[REGIME] Regime change detected at generation {generation} "
                              f"({variance_increase} metrics with variance spike)")

            return regime_changed

        except Exception as e:
            logger.error(f"Error detecting regime change: {e}")
            return False
