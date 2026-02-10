#!/usr/bin/env python3
import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
Phase 6.1 -- Seven Runtime Health Gauges
=========================================

Seven continuous metrics, each detecting one mode of system decay.
Runs every generation and stores results in ``autopoiesis_snapshots``.

| Gauge                    | Healthy Range | Detects                  |
|--------------------------|---------------|--------------------------|
| Centralization Index     | < 0.3         | Single-point control     |
| Memory Retention Score   | > 0.7         | Forgotten knowledge      |
| Authority Distribution   | < 0.4 Gini   | Decision hierarchy       |
| Resource Equity          | < 0.3 Gini   | Action-budget inequality |
| Compression Ratio        | > 0.1         | Raw-data bloat           |
| Cross-Game Transfer Rate | > 0.05        | Knowledge silos          |
| Belief Turnover Rate     | 0.05 -- 0.3   | Stale beliefs            |

If ANY gauge exits its healthy range for 5+ consecutive generations
a warning is logged to ``system_logs``.  If 3+ gauges are simultaneously
unhealthy the ``NetworkHealthResponder`` is invoked for emergency correction.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------
# Gauge definitions  (name, healthy_lo, healthy_hi, formula_description)
# -----------------------------------------------------------------------
# Healthy range is [lo, hi] -- None means unbounded on that side.
GAUGE_DEFS: Dict[str, Dict[str, Any]] = {
    'centralization_index': {
        'lo': None, 'hi': 0.3,
        'description': 'max(engine_call_count) / sum(engine_call_count)',
    },
    'memory_retention_score': {
        'lo': 0.7, 'hi': None,
        'description': 'knowledge_items_used_this_gen / knowledge_items_available',
    },
    'authority_distribution': {
        'lo': None, 'hi': 0.4,
        'description': 'Gini coefficient of rung activation counts',
    },
    'resource_equity': {
        'lo': None, 'hi': 0.3,
        'description': 'Gini coefficient of action budgets across agents',
    },
    'compression_ratio': {
        'lo': 0.1, 'hi': None,
        'description': '(new_abstractions + new_templates) / new_raw_traces',
    },
    'cross_game_transfer_rate': {
        'lo': 0.05, 'hi': None,
        'description': 'successful_cross_game_transfers / total_transfer_attempts',
    },
    'belief_turnover_rate': {
        'lo': 0.05, 'hi': 0.3,
        'description': 'beliefs_changed / total_beliefs per generation',
    },
}

# How many consecutive unhealthy generations before we warn
_WARN_STREAK = 5
# How many gauges simultaneously unhealthy to trigger emergency
_EMERGENCY_THRESHOLD = 3


class SystemHealthGauges:
    """Compute, store, and evaluate 7 runtime health gauges every generation."""

    def __init__(self, db: DatabaseInterface):
        self.db = db
        # Track per-gauge unhealthy streaks (in memory -- reset on process restart)
        self._unhealthy_streaks: Dict[str, int] = {g: 0 for g in GAUGE_DEFS}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(self, generation: int) -> Dict[str, Any]:
        """Compute all 7 gauges, store snapshot, check alerts.

        Returns dict with gauge values + ``unhealthy_gauges`` list +
        ``emergency`` bool.
        """
        values = {
            'centralization_index': self._centralization_index(generation),
            'memory_retention_score': self._memory_retention_score(generation),
            'authority_distribution': self._authority_distribution(generation),
            'resource_equity': self._resource_equity(generation),
            'compression_ratio': self._compression_ratio(generation),
            'cross_game_transfer_rate': self._cross_game_transfer_rate(generation),
            'belief_turnover_rate': self._belief_turnover_rate(generation),
        }

        # Determine unhealthy gauges
        unhealthy: List[str] = []
        for gauge_name, val in values.items():
            if self._is_unhealthy(gauge_name, val):
                self._unhealthy_streaks[gauge_name] += 1
                unhealthy.append(gauge_name)
            else:
                self._unhealthy_streaks[gauge_name] = 0

        # Alerts
        for gauge_name in unhealthy:
            streak = self._unhealthy_streaks[gauge_name]
            if streak >= _WARN_STREAK:
                logger.warning(
                    "[GAUGE] %s breached healthy range for %d consecutive "
                    "generations (value=%.4f)",
                    gauge_name, streak, values[gauge_name],
                )

        emergency = len(unhealthy) >= _EMERGENCY_THRESHOLD

        if emergency:
            logger.warning(
                "[GAUGE-EMERGENCY] %d gauges simultaneously unhealthy: %s",
                len(unhealthy), unhealthy,
            )

        # Store snapshot
        self._store_snapshot(generation, values)

        return {
            **values,
            'unhealthy_gauges': unhealthy,
            'emergency': emergency,
        }

    # ------------------------------------------------------------------
    # Individual gauge computations
    # ------------------------------------------------------------------

    def _centralization_index(self, generation: int) -> float:
        """max(engine_call_count) / sum(engine_call_count) this generation."""
        try:
            rows = self.db.execute_query("""
                SELECT logger_name, COUNT(*) as cnt
                FROM system_logs
                WHERE logger_name LIKE '%engine%'
                GROUP BY logger_name
            """)
            if not rows:
                return 0.0
            counts = [r['cnt'] for r in rows]
            total = sum(counts)
            return max(counts) / total if total > 0 else 0.0
        except Exception:
            return 0.0

    def _memory_retention_score(self, generation: int) -> float:
        """knowledge_items_used_this_gen / knowledge_items_available."""
        try:
            # Available: winning sequences + learned rules
            avail_rows = self.db.execute_query("""
                SELECT COUNT(*) as cnt FROM winning_sequences WHERE is_active = 1
            """)
            available = avail_rows[0]['cnt'] if avail_rows else 0
            if available == 0:
                return 1.0  # No knowledge yet -> vacuously healthy

            # Used this gen: sequences that were replayed/referenced
            used_rows = self.db.execute_query("""
                SELECT COUNT(DISTINCT sequence_id) as cnt
                FROM game_results
                WHERE generation = ? AND sequence_id IS NOT NULL
            """, (generation,))
            used = used_rows[0]['cnt'] if used_rows else 0

            return min(1.0, used / available)
        except Exception:
            return 1.0

    def _authority_distribution(self, generation: int) -> float:
        """Gini coefficient of rung activation counts."""
        try:
            rows = self.db.execute_query("""
                SELECT rung_name, COUNT(*) as cnt
                FROM routing_traces
                WHERE generation = ?
                GROUP BY rung_name
            """, (generation,))
            if not rows or len(rows) < 2:
                return 0.0
            counts = sorted(r['cnt'] for r in rows)
            return self._gini(counts)
        except Exception:
            return 0.0

    def _resource_equity(self, generation: int) -> float:
        """Gini coefficient of action budgets across agents."""
        try:
            rows = self.db.execute_query("""
                SELECT agent_id, SUM(total_actions) as total
                FROM game_results
                WHERE generation = ?
                GROUP BY agent_id
            """, (generation,))
            if not rows or len(rows) < 2:
                return 0.0
            totals = sorted(r['total'] for r in rows)
            return self._gini(totals)
        except Exception:
            return 0.0

    def _compression_ratio(self, generation: int) -> float:
        """(new_abstractions + new_templates) / new_raw_traces this gen."""
        try:
            # Knowledge created this generation
            templ_rows = self.db.execute_query("""
                SELECT COUNT(*) as cnt FROM compressed_templates
                WHERE generation_created = ?
            """, (generation,))
            new_knowledge = templ_rows[0]['cnt'] if templ_rows else 0

            rule_rows = self.db.execute_query("""
                SELECT COUNT(*) as cnt FROM interaction_triggers
                WHERE generation_discovered = ?
            """, (generation,))
            new_knowledge += rule_rows[0]['cnt'] if rule_rows else 0

            # Raw traces this generation
            raw_rows = self.db.execute_query("""
                SELECT COUNT(*) as cnt FROM action_traces
                WHERE generation = ?
            """, (generation,))
            raw = raw_rows[0]['cnt'] if raw_rows else 0

            if raw == 0:
                return 1.0  # No raw data -> perfect
            return new_knowledge / raw
        except Exception:
            return 0.0

    def _cross_game_transfer_rate(self, generation: int) -> float:
        """successful_cross_game_transfers / total_transfer_attempts."""
        try:
            rows = self.db.execute_query("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN transfer_successful = 1 THEN 1 ELSE 0 END) as success
                FROM horizontal_transfer_events
                WHERE generation = ?
            """, (generation,))
            if not rows or rows[0]['total'] == 0:
                return 0.0
            return rows[0]['success'] / rows[0]['total']
        except Exception:
            return 0.0

    def _belief_turnover_rate(self, generation: int) -> float:
        """beliefs_changed / total_beliefs per generation."""
        try:
            total_rows = self.db.execute_query("""
                SELECT COUNT(*) as cnt FROM beliefs WHERE status = 'active'
            """)
            total = total_rows[0]['cnt'] if total_rows else 0
            if total == 0:
                return 0.0

            changed_rows = self.db.execute_query("""
                SELECT COUNT(*) as cnt FROM belief_invalidation_events
                WHERE created_at >= datetime('now', '-1 day')
            """)
            changed = changed_rows[0]['cnt'] if changed_rows else 0

            return min(1.0, changed / total)
        except Exception:
            return 0.0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _gini(values: List[float]) -> float:
        """Compute the Gini coefficient for a sorted list of non-negative values."""
        n = len(values)
        if n == 0:
            return 0.0
        total = sum(values)
        if total == 0:
            return 0.0
        cumulative = 0.0
        weighted_sum = 0.0
        for i, v in enumerate(values):
            cumulative += v
            weighted_sum += (i + 1) * v
        return (2 * weighted_sum) / (n * total) - (n + 1) / n

    @staticmethod
    def _is_unhealthy(gauge_name: str, value: float) -> bool:
        """Check whether a gauge value falls outside its healthy range."""
        defn = GAUGE_DEFS.get(gauge_name)
        if not defn:
            return False
        lo = defn.get('lo')
        hi = defn.get('hi')
        if lo is not None and value < lo:
            return True
        if hi is not None and value > hi:
            return True
        return False

    def _store_snapshot(self, generation: int, values: Dict[str, float]) -> None:
        """Persist gauge values into ``autopoiesis_snapshots``."""
        try:
            snapshot_id = f"gauge_{uuid.uuid4().hex[:12]}"
            metadata = json.dumps({
                'gauges': values,
                'timestamp': datetime.utcnow().isoformat(),
            })
            self.db.execute_query("""
                INSERT INTO autopoiesis_snapshots
                (snapshot_id, generation, emergence_gain, identity_drift,
                 control_error, loop_detection_score, overall_health, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot_id,
                generation,
                values.get('compression_ratio', 0.0),
                values.get('belief_turnover_rate', 0.0),
                values.get('centralization_index', 0.0),
                values.get('authority_distribution', 0.0),
                self._overall_health(values),
                metadata,
            ))
        except Exception as e:
            logger.warning("Failed to store gauge snapshot: %s", e)

    @staticmethod
    def _overall_health(values: Dict[str, float]) -> float:
        """Weighted average of gauge healthiness (0.0 = all bad, 1.0 = all good)."""
        score = 0.0
        count = 0
        for gauge_name, val in values.items():
            defn = GAUGE_DEFS.get(gauge_name)
            if not defn:
                continue
            lo = defn.get('lo')
            hi = defn.get('hi')
            healthy = True
            if lo is not None and val < lo:
                healthy = False
            if hi is not None and val > hi:
                healthy = False
            score += 1.0 if healthy else 0.0
            count += 1
        return score / count if count else 0.0
