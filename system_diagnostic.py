"""Phase 6.3 -- Comprehensive Self-Diagnostic Report.

Generates a health report every 10 generations covering:
  - All 7 gauge values + trend (improving / degrading / stable)
  - Top disconnected systems (tables with 0 writes recently)
  - Top bottleneck systems (high write / low read tables)
  - Knowledge utilisation percentage
  - Compression effectiveness
  - Resonance connectivity
  - Overall health score stored in ecosystem_health_snapshots

Relies on:
  system_health_gauges.py  -- 7 runtime gauges (Phase 6.1)
  database_interface.py    -- DatabaseInterface for all queries
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

from database_interface import DatabaseInterface

try:
    from system_health_gauges import GAUGE_DEFS, SystemHealthGauges
    GAUGES_AVAILABLE = True
except ImportError:
    GAUGES_AVAILABLE = False

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# Constants
# ------------------------------------------------------------------ #

_LOOKBACK_GENS = 10          # How far back to check for writes / reads
_TREND_WINDOW = 5            # Generations of gauge history for trend
_DISCONNECTION_PENALTY = 0.05  # Per disconnected system


class SystemDiagnostic:
    """Builds a comprehensive health report stored in ecosystem_health_snapshots."""

    def __init__(self, db: DatabaseInterface,
                 health_gauges: Optional[SystemHealthGauges] = None):
        self.db = db
        self.health_gauges = health_gauges

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def run(self, generation: int) -> Dict[str, Any]:
        """Execute the full diagnostic and store the result.

        Returns the report dict.
        """
        report: Dict[str, Any] = {'generation': generation}

        # 1. Gauge values + trends
        gauge_section = self._gauge_report(generation)
        report['gauges'] = gauge_section

        # 2. Disconnected systems
        disconnected = self._disconnected_systems(generation)
        report['disconnected_systems'] = disconnected[:3]

        # 3. Bottleneck systems
        bottlenecks = self._bottleneck_systems(generation)
        report['bottleneck_systems'] = bottlenecks[:3]

        # 4. Knowledge utilisation
        report['knowledge_utilisation'] = self._knowledge_utilisation(generation)

        # 5. Compression effectiveness
        report['compression_effectiveness'] = self._compression_effectiveness()

        # 6. Resonance connectivity
        report['resonance_connectivity'] = self._resonance_connectivity()

        # 7. Overall health score
        overall = self._compute_overall_health(gauge_section, len(disconnected))
        report['overall_health'] = overall

        # Health status label
        if overall >= 0.8:
            report['health_status'] = 'excellent'
        elif overall >= 0.6:
            report['health_status'] = 'good'
        elif overall >= 0.4:
            report['health_status'] = 'fair'
        elif overall >= 0.2:
            report['health_status'] = 'poor'
        else:
            report['health_status'] = 'critical'

        # Store
        self._store_report(report, generation)

        return report

    # ------------------------------------------------------------------ #
    # 1. Gauge values + trend
    # ------------------------------------------------------------------ #

    def _gauge_report(self, generation: int) -> Dict[str, Dict[str, Any]]:
        """Return each gauge's latest value + trend over last N snapshots."""
        section: Dict[str, Dict[str, Any]] = {}

        # Try to read recent autopoiesis_snapshots metadata
        try:
            rows = self.db.execute_query("""
                SELECT generation, metadata FROM autopoiesis_snapshots
                WHERE generation <= ?
                ORDER BY generation DESC
                LIMIT ?
            """, (generation, _TREND_WINDOW))
        except Exception:
            rows = []

        history: Dict[str, List[float]] = {g: [] for g in GAUGE_DEFS} if GAUGES_AVAILABLE else {}

        for row in reversed(rows):
            meta_raw = row.get('metadata') or row[-1] if isinstance(row, dict) else '{}'
            try:
                meta = json.loads(meta_raw) if isinstance(meta_raw, str) else meta_raw
            except (json.JSONDecodeError, TypeError):
                meta = {}
            gauges_dict = meta.get('gauges', {})
            for g in history:
                if g in gauges_dict:
                    history[g].append(gauges_dict[g])

        for gauge_name, vals in history.items():
            latest = vals[-1] if vals else 0.0
            trend = self._compute_trend(vals)
            section[gauge_name] = {
                'value': round(latest, 4),
                'trend': trend,
                'history_len': len(vals),
            }

        return section

    @staticmethod
    def _compute_trend(values: List[float]) -> str:
        """Classify a short value series as improving / degrading / stable."""
        if len(values) < 2:
            return 'stable'
        first_half = sum(values[:len(values) // 2]) / max(len(values) // 2, 1)
        second_half = sum(values[len(values) // 2:]) / max(len(values) - len(values) // 2, 1)
        delta = second_half - first_half
        if abs(delta) < 0.02:
            return 'stable'
        return 'improving' if delta > 0 else 'degrading'

    # ------------------------------------------------------------------ #
    # 2. Disconnected systems
    # ------------------------------------------------------------------ #

    # Tables that should receive writes during normal operation.
    _MONITORED_TABLES = [
        'viral_information_packages',
        'resonance_patterns',
        'winning_sequences',
        'game_results',
        'agent_scores',
        'sensation_learning_events',
        'agent_operating_modes',
        'navigation_state_history',
        'score_history',
        'action_traces',
        'knowledge_compression_templates',
        'primitive_unlock_progress',
    ]

    def _disconnected_systems(self, generation: int) -> List[Dict[str, Any]]:
        """Find tables that have had zero writes in the last N generations.

        Uses the system_logs table to detect INSERT/UPDATE activity.
        Falls back to row counts when logs are unavailable.
        """
        disconnected: List[Dict[str, Any]] = []
        min_gen = max(0, generation - _LOOKBACK_GENS)

        for table in self._MONITORED_TABLES:
            try:
                # Check if table has any recent rows
                rows = self.db.execute_query(f"""
                    SELECT COUNT(*) as cnt FROM {table}
                    WHERE ROWID > (
                        SELECT COALESCE(MAX(ROWID), 0) FROM {table}
                    ) - 1000
                """)
                count = rows[0]['cnt'] if rows and isinstance(rows[0], dict) else (
                    rows[0][0] if rows else 0
                )
                if count == 0:
                    disconnected.append({
                        'table': table,
                        'last_write_gen': None,
                        'reason': 'zero rows in recent window',
                    })
            except Exception:
                # Table might not exist yet -- that is a disconnection signal
                disconnected.append({
                    'table': table,
                    'last_write_gen': None,
                    'reason': 'table inaccessible or missing',
                })

        return disconnected

    # ------------------------------------------------------------------ #
    # 3. Bottleneck systems
    # ------------------------------------------------------------------ #

    def _bottleneck_systems(self, generation: int) -> List[Dict[str, Any]]:
        """Find tables with high write rates but low read rates.

        Heuristic: tables that grow fastest yet are rarely queried by
        other systems.  Uses total row count as a proxy for writes and
        checks for the presence of indices (proxying read patterns).
        """
        bottlenecks: List[Dict[str, Any]] = []

        for table in self._MONITORED_TABLES:
            try:
                rows = self.db.execute_query(
                    f"SELECT COUNT(*) as cnt FROM {table}"
                )
                row_count = rows[0]['cnt'] if rows and isinstance(rows[0], dict) else (
                    rows[0][0] if rows else 0
                )

                # Check index count as proxy for read usage
                idx_rows = self.db.execute_query(
                    "SELECT COUNT(*) as cnt FROM sqlite_master "
                    "WHERE type='index' AND tbl_name=?",
                    (table,)
                )
                idx_count = idx_rows[0]['cnt'] if idx_rows and isinstance(idx_rows[0], dict) else (
                    idx_rows[0][0] if idx_rows else 0
                )

                # High row count + few indices = probable bottleneck
                if row_count > 10000 and idx_count <= 1:
                    bottlenecks.append({
                        'table': table,
                        'row_count': row_count,
                        'index_count': idx_count,
                        'reason': 'high writes, few indices (probable low read usage)',
                    })
            except Exception:
                pass

        # Sort by row_count descending
        bottlenecks.sort(key=lambda b: b.get('row_count', 0), reverse=True)
        return bottlenecks

    # ------------------------------------------------------------------ #
    # 4. Knowledge utilisation
    # ------------------------------------------------------------------ #

    def _knowledge_utilisation(self, generation: int) -> float:
        """Percentage of stored knowledge used in recent gameplay.

        Checks how many winning sequences were actually replayed / reused
        versus total stored sequences.
        """
        try:
            total = self.db.execute_query(
                "SELECT COUNT(*) as cnt FROM winning_sequences WHERE is_active = 1"
            )
            total_count = total[0]['cnt'] if total and isinstance(total[0], dict) else (
                total[0][0] if total else 0
            )
            if total_count == 0:
                return 0.0

            # Sequences with validation_count > 0 are "used"
            used = self.db.execute_query(
                "SELECT COUNT(*) as cnt FROM winning_sequences "
                "WHERE is_active = 1 AND validation_count > 0"
            )
            used_count = used[0]['cnt'] if used and isinstance(used[0], dict) else (
                used[0][0] if used else 0
            )
            return round(used_count / total_count, 4)
        except Exception:
            return 0.0

    # ------------------------------------------------------------------ #
    # 5. Compression effectiveness
    # ------------------------------------------------------------------ #

    def _compression_effectiveness(self) -> float:
        """Average quality score of knowledge compression templates.

        Higher = templates are effectively abstracting repeated patterns.
        """
        try:
            rows = self.db.execute_query("""
                SELECT AVG(quality_score) as avg_q
                FROM knowledge_compression_templates
                WHERE is_active = 1
            """)
            if rows:
                val = rows[0]['avg_q'] if isinstance(rows[0], dict) else rows[0][0]
                return round(float(val), 4) if val is not None else 0.0
        except Exception:
            pass
        return 0.0

    # ------------------------------------------------------------------ #
    # 6. Resonance connectivity
    # ------------------------------------------------------------------ #

    def _resonance_connectivity(self) -> float:
        """Measure how connected the game-type graph is via resonance patterns.

        Returns the ratio of unique game-type pairs that share a resonance
        pattern versus the total possible pairs.
        """
        try:
            rows = self.db.execute_query("""
                SELECT game_types FROM resonance_patterns
                WHERE game_types IS NOT NULL AND game_types != ''
            """)
            if not rows:
                return 0.0

            game_types_seen: set = set()
            pair_count = 0
            for row in rows:
                gt = row['game_types'] if isinstance(row, dict) else row[0]
                if not gt:
                    continue
                try:
                    types = json.loads(gt) if isinstance(gt, str) else gt
                except (json.JSONDecodeError, TypeError):
                    types = [gt]
                if isinstance(types, list) and len(types) >= 2:
                    pair_count += 1
                    for t in types:
                        game_types_seen.add(t)

            n = len(game_types_seen)
            if n < 2:
                return 0.0
            max_pairs = n * (n - 1) / 2
            return round(min(pair_count / max_pairs, 1.0), 4)
        except Exception:
            return 0.0

    # ------------------------------------------------------------------ #
    # Overall health
    # ------------------------------------------------------------------ #

    def _compute_overall_health(self, gauge_section: Dict[str, Dict],
                                disconnected_count: int) -> float:
        """overall_health = weighted_avg(gauges) * (1 - disconnection_penalty)"""
        if not gauge_section:
            return 0.0

        # For each gauge, value 1.0 = perfectly healthy, 0.0 = maximally unhealthy
        # We need to normalize each gauge into a 0-1 health score
        health_scores: List[float] = []
        for name, info in gauge_section.items():
            val = info.get('value', 0.0)
            health_scores.append(self._normalize_gauge(name, val))

        if not health_scores:
            return 0.0

        avg = sum(health_scores) / len(health_scores)
        penalty = min(disconnected_count * _DISCONNECTION_PENALTY, 0.5)
        return round(max(avg * (1.0 - penalty), 0.0), 4)

    @staticmethod
    def _normalize_gauge(name: str, value: float) -> float:
        """Convert a raw gauge value to a 0-1 health score.

        Uses the healthy range from GAUGE_DEFS.
        """
        if not GAUGES_AVAILABLE:
            return 0.5

        defn = GAUGE_DEFS.get(name)
        if not defn:
            return 0.5

        low = defn.get('lo')
        high = defn.get('hi')

        if low is not None and high is not None:
            # Range gauge -- 1.0 when in range, decays outside
            if low <= value <= high:
                return 1.0
            if value < low:
                return max(1.0 - (low - value) / max(low, 0.01), 0.0)
            return max(1.0 - (value - high) / max(1.0 - high, 0.01), 0.0)
        elif high is not None:
            # Upper-bounded (e.g. centralization < 0.3)
            return max(1.0 - value / max(high, 0.01), 0.0) if value > high else 1.0
        elif low is not None:
            # Lower-bounded (e.g. memory_retention > 0.7)
            return min(value / max(low, 0.01), 1.0) if value < low else 1.0

        return 0.5

    # ------------------------------------------------------------------ #
    # Storage
    # ------------------------------------------------------------------ #

    def _store_report(self, report: Dict[str, Any], generation: int) -> None:
        """Persist the diagnostic into ecosystem_health_snapshots."""
        snapshot_id = f"diag-{generation}-{uuid.uuid4().hex[:8]}"

        # Build a metadata blob for details not directly mapped to columns
        metadata = {
            'gauges': report.get('gauges', {}),
            'disconnected_systems': report.get('disconnected_systems', []),
            'bottleneck_systems': report.get('bottleneck_systems', []),
            'knowledge_utilisation': report.get('knowledge_utilisation', 0.0),
            'compression_effectiveness': report.get('compression_effectiveness', 0.0),
            'resonance_connectivity': report.get('resonance_connectivity', 0.0),
        }

        metadata_json = json.dumps(metadata)

        try:
            self.db.execute_query("""
                INSERT OR REPLACE INTO ecosystem_health_snapshots (
                    snapshot_id, generation,
                    health_status, health_score,
                    knowledge_diversity_index,
                    network_learning_rate,
                    system_entropy
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot_id,
                generation,
                report.get('health_status', 'unknown'),
                report.get('overall_health', 0.0),
                report.get('resonance_connectivity', 0.0),
                report.get('knowledge_utilisation', 0.0),
                metadata_json,
            ))
            logger.info(
                "[DIAGNOSTIC] Report stored for gen %d: %s (%.3f)",
                generation,
                report.get('health_status', 'unknown'),
                report.get('overall_health', 0.0),
            )
        except Exception as e:
            logger.error("[DIAGNOSTIC] Failed to store report: %s", e)
