"""
Routing Metrics Tracker - Phase 5.2.

Tracks key performance metrics for cognitive routing:
1. Avg rungs evaluated per decision (<15 target)
2. Decision latency (<50ms target)
3. First-win rate (>60% target)
4. Backtracking frequency (<5% target)
5. Contradiction detection rate (>80% target)

Usage:
    tracker = RoutingMetricsTracker()

    # Record a decision
    tracker.record_decision(
        rungs_evaluated=12,
        latency_ms=35,
        first_win=True,
        backtracked=False,
        contradictions_detected=2,
        contradictions_actual=2
    )

    # Get metrics
    metrics = tracker.get_metrics()
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

import logging
import statistics
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Deque, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# METRIC TARGETS (from Phase 5.2)
# =============================================================================

@dataclass
class MetricTargets:
    """Target values for routing metrics."""
    avg_rungs_evaluated: float = 15.0       # < 15 rungs per decision
    decision_latency_ms: float = 50.0       # < 50ms
    first_win_rate: float = 0.60            # > 60%
    backtracking_rate: float = 0.05         # < 5%
    contradiction_detection: float = 0.80   # > 80%

    # Baseline values (current static system)
    baseline_rungs: float = 40.0
    baseline_latency_ms: float = 100.0
    baseline_first_win: float = 0.30


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class DecisionMetrics:
    """Metrics for a single decision."""
    timestamp: str
    game_id: str
    agent_id: str

    # Core metrics
    rungs_evaluated: int
    latency_ms: float
    first_win: bool  # Did rungs 1-5 provide the answer?
    backtracked: bool

    # Contradiction metrics
    contradictions_detected: int = 0
    contradictions_actual: int = 0

    # Context
    algorithm_used: str = "unknown"
    quadrant: str = "UU"
    used_fallback: bool = False


@dataclass
class AggregateMetrics:
    """Aggregate metrics over a time period."""
    period_start: str
    period_end: str
    decision_count: int

    # Averages
    avg_rungs_evaluated: float
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float

    # Rates
    first_win_rate: float
    backtracking_rate: float
    contradiction_detection_rate: float
    fallback_rate: float

    # Distribution
    rungs_histogram: Dict[str, int]  # "1-5", "6-10", "11-15", "16-20", "21+"
    latency_histogram: Dict[str, int]  # "0-10", "10-25", "25-50", "50-100", "100+"

    # Comparison to targets
    meets_rungs_target: bool
    meets_latency_target: bool
    meets_first_win_target: bool
    meets_backtracking_target: bool
    meets_contradiction_target: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'period_start': self.period_start,
            'period_end': self.period_end,
            'decision_count': self.decision_count,
            'avg_rungs_evaluated': self.avg_rungs_evaluated,
            'avg_latency_ms': self.avg_latency_ms,
            'p95_latency_ms': self.p95_latency_ms,
            'p99_latency_ms': self.p99_latency_ms,
            'first_win_rate': self.first_win_rate,
            'backtracking_rate': self.backtracking_rate,
            'contradiction_detection_rate': self.contradiction_detection_rate,
            'fallback_rate': self.fallback_rate,
            'rungs_histogram': self.rungs_histogram,
            'latency_histogram': self.latency_histogram,
            'meets_rungs_target': self.meets_rungs_target,
            'meets_latency_target': self.meets_latency_target,
            'meets_first_win_target': self.meets_first_win_target,
            'meets_backtracking_target': self.meets_backtracking_target,
            'meets_contradiction_target': self.meets_contradiction_target,
        }


class MetricStatus(Enum):
    """Status of a metric relative to target."""
    EXCELLENT = "excellent"  # Better than target by >20%
    GOOD = "good"            # Meets or beats target
    WARNING = "warning"      # Within 20% of target
    CRITICAL = "critical"    # Worse than target by >20%


# =============================================================================
# METRICS TRACKER
# =============================================================================

class RoutingMetricsTracker:
    """
    Tracks routing metrics with rolling windows and aggregation.

    Maintains:
    - Last 1000 decisions for rolling statistics
    - Per-game metrics
    - Per-algorithm metrics
    - Trend analysis
    """

    def __init__(
        self,
        targets: Optional[MetricTargets] = None,
        window_size: int = 1000,
        db_interface: Optional[Any] = None
    ):
        """Initialize metrics tracker."""
        self.targets = targets or MetricTargets()
        self.window_size = window_size
        self.db = db_interface

        # Rolling window of recent decisions
        self._decisions: Deque[DecisionMetrics] = deque(maxlen=window_size)

        # Per-game aggregates
        self._game_metrics: Dict[str, List[DecisionMetrics]] = {}

        # Per-algorithm aggregates
        self._algorithm_metrics: Dict[str, List[DecisionMetrics]] = {}

        # Counters for rates
        self._total_decisions = 0
        self._first_wins = 0
        self._backtracks = 0
        self._contradictions_detected = 0
        self._contradictions_actual = 0
        self._fallbacks = 0

        # For percentile calculations
        self._latencies: Deque[float] = deque(maxlen=window_size)
        self._rungs: Deque[int] = deque(maxlen=window_size)

        logger.info("[METRICS] Routing metrics tracker initialized")

    # -------------------------------------------------------------------------
    # RECORDING
    # -------------------------------------------------------------------------

    def record_decision(
        self,
        rungs_evaluated: int,
        latency_ms: float,
        first_win: bool = False,
        backtracked: bool = False,
        contradictions_detected: int = 0,
        contradictions_actual: int = 0,
        game_id: str = "unknown",
        agent_id: str = "unknown",
        algorithm_used: str = "unknown",
        quadrant: str = "UU",
        used_fallback: bool = False
    ) -> None:
        """Record metrics for a single decision."""
        metrics = DecisionMetrics(
            timestamp=datetime.now().isoformat(),
            game_id=game_id,
            agent_id=agent_id,
            rungs_evaluated=rungs_evaluated,
            latency_ms=latency_ms,
            first_win=first_win,
            backtracked=backtracked,
            contradictions_detected=contradictions_detected,
            contradictions_actual=contradictions_actual,
            algorithm_used=algorithm_used,
            quadrant=quadrant,
            used_fallback=used_fallback,
        )

        # Add to rolling window
        self._decisions.append(metrics)
        self._latencies.append(latency_ms)
        self._rungs.append(rungs_evaluated)

        # Update counters
        self._total_decisions += 1
        if first_win:
            self._first_wins += 1
        if backtracked:
            self._backtracks += 1
        if used_fallback:
            self._fallbacks += 1
        self._contradictions_detected += contradictions_detected
        self._contradictions_actual += contradictions_actual

        # Per-game tracking
        if game_id not in self._game_metrics:
            self._game_metrics[game_id] = []
        self._game_metrics[game_id].append(metrics)

        # Per-algorithm tracking
        if algorithm_used not in self._algorithm_metrics:
            self._algorithm_metrics[algorithm_used] = []
        self._algorithm_metrics[algorithm_used].append(metrics)

        # Store to database if configured
        if self.db:
            self._store_metrics(metrics)

    def _store_metrics(self, metrics: DecisionMetrics) -> None:
        """Store metrics to database."""
        if self.db is None:
            return
        try:
            self.db.execute("""
                INSERT INTO routing_metrics (
                    timestamp, game_id, agent_id, rungs_evaluated,
                    latency_ms, first_win, backtracked,
                    contradictions_detected, contradictions_actual,
                    algorithm_used, quadrant, used_fallback
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.timestamp, metrics.game_id, metrics.agent_id,
                metrics.rungs_evaluated, metrics.latency_ms,
                int(metrics.first_win), int(metrics.backtracked),
                metrics.contradictions_detected, metrics.contradictions_actual,
                metrics.algorithm_used, metrics.quadrant, int(metrics.used_fallback),
            ))
        except Exception as e:
            logger.error(f"[METRICS] Failed to store metrics: {e}")

    # -------------------------------------------------------------------------
    # AGGREGATION
    # -------------------------------------------------------------------------

    def get_metrics(self) -> AggregateMetrics:
        """Get aggregate metrics for the rolling window."""
        if not self._decisions:
            return self._empty_metrics()

        decisions = list(self._decisions)
        latencies = list(self._latencies)
        rungs = list(self._rungs)

        # Basic averages
        avg_rungs = statistics.mean(rungs)
        avg_latency = statistics.mean(latencies)

        # Percentiles
        sorted_latencies = sorted(latencies)
        p95_idx = int(len(sorted_latencies) * 0.95)
        p99_idx = int(len(sorted_latencies) * 0.99)
        p95_latency = sorted_latencies[p95_idx] if sorted_latencies else 0
        p99_latency = sorted_latencies[p99_idx] if sorted_latencies else 0

        # Rates
        n = len(decisions)
        first_wins = sum(1 for d in decisions if d.first_win)
        backtracks = sum(1 for d in decisions if d.backtracked)
        fallbacks = sum(1 for d in decisions if d.used_fallback)

        detected = sum(d.contradictions_detected for d in decisions)
        actual = sum(d.contradictions_actual for d in decisions)

        first_win_rate = first_wins / n
        backtracking_rate = backtracks / n
        fallback_rate = fallbacks / n
        contradiction_rate = detected / actual if actual > 0 else 1.0

        # Histograms
        rungs_hist = self._compute_rungs_histogram(rungs)
        latency_hist = self._compute_latency_histogram(latencies)

        return AggregateMetrics(
            period_start=decisions[0].timestamp,
            period_end=decisions[-1].timestamp,
            decision_count=n,
            avg_rungs_evaluated=avg_rungs,
            avg_latency_ms=avg_latency,
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency,
            first_win_rate=first_win_rate,
            backtracking_rate=backtracking_rate,
            contradiction_detection_rate=contradiction_rate,
            fallback_rate=fallback_rate,
            rungs_histogram=rungs_hist,
            latency_histogram=latency_hist,
            meets_rungs_target=avg_rungs < self.targets.avg_rungs_evaluated,
            meets_latency_target=avg_latency < self.targets.decision_latency_ms,
            meets_first_win_target=first_win_rate > self.targets.first_win_rate,
            meets_backtracking_target=backtracking_rate < self.targets.backtracking_rate,
            meets_contradiction_target=contradiction_rate > self.targets.contradiction_detection,
        )

    def _empty_metrics(self) -> AggregateMetrics:
        """Return empty metrics when no data."""
        now = datetime.now().isoformat()
        return AggregateMetrics(
            period_start=now,
            period_end=now,
            decision_count=0,
            avg_rungs_evaluated=0,
            avg_latency_ms=0,
            p95_latency_ms=0,
            p99_latency_ms=0,
            first_win_rate=0,
            backtracking_rate=0,
            contradiction_detection_rate=0,
            fallback_rate=0,
            rungs_histogram={},
            latency_histogram={},
            meets_rungs_target=False,
            meets_latency_target=False,
            meets_first_win_target=False,
            meets_backtracking_target=False,
            meets_contradiction_target=False,
        )

    def _compute_rungs_histogram(self, rungs: List[int]) -> Dict[str, int]:
        """Compute histogram of rungs evaluated."""
        hist = {"1-5": 0, "6-10": 0, "11-15": 0, "16-20": 0, "21+": 0}
        for r in rungs:
            if r <= 5:
                hist["1-5"] += 1
            elif r <= 10:
                hist["6-10"] += 1
            elif r <= 15:
                hist["11-15"] += 1
            elif r <= 20:
                hist["16-20"] += 1
            else:
                hist["21+"] += 1
        return hist

    def _compute_latency_histogram(self, latencies: List[float]) -> Dict[str, int]:
        """Compute histogram of latencies."""
        hist = {"0-10": 0, "10-25": 0, "25-50": 0, "50-100": 0, "100+": 0}
        for l in latencies:
            if l <= 10:
                hist["0-10"] += 1
            elif l <= 25:
                hist["10-25"] += 1
            elif l <= 50:
                hist["25-50"] += 1
            elif l <= 100:
                hist["50-100"] += 1
            else:
                hist["100+"] += 1
        return hist

    # -------------------------------------------------------------------------
    # PER-ENTITY METRICS
    # -------------------------------------------------------------------------

    def get_game_metrics(self, game_id: str) -> Optional[AggregateMetrics]:
        """Get metrics for a specific game."""
        if game_id not in self._game_metrics:
            return None

        decisions = self._game_metrics[game_id]
        return self._aggregate_decisions(decisions)

    def get_algorithm_metrics(self, algorithm: str) -> Optional[AggregateMetrics]:
        """Get metrics for a specific algorithm."""
        if algorithm not in self._algorithm_metrics:
            return None

        decisions = self._algorithm_metrics[algorithm]
        return self._aggregate_decisions(decisions)

    def _aggregate_decisions(self, decisions: List[DecisionMetrics]) -> AggregateMetrics:
        """Aggregate a list of decisions into metrics."""
        if not decisions:
            return self._empty_metrics()

        latencies = [d.latency_ms for d in decisions]
        rungs = [d.rungs_evaluated for d in decisions]

        n = len(decisions)
        avg_rungs = statistics.mean(rungs)
        avg_latency = statistics.mean(latencies)

        sorted_latencies = sorted(latencies)
        p95_idx = int(len(sorted_latencies) * 0.95)
        p99_idx = int(len(sorted_latencies) * 0.99)
        p95_latency = sorted_latencies[p95_idx] if sorted_latencies else 0
        p99_latency = sorted_latencies[p99_idx] if sorted_latencies else 0

        first_wins = sum(1 for d in decisions if d.first_win)
        backtracks = sum(1 for d in decisions if d.backtracked)
        fallbacks = sum(1 for d in decisions if d.used_fallback)

        detected = sum(d.contradictions_detected for d in decisions)
        actual = sum(d.contradictions_actual for d in decisions)

        return AggregateMetrics(
            period_start=decisions[0].timestamp,
            period_end=decisions[-1].timestamp,
            decision_count=n,
            avg_rungs_evaluated=avg_rungs,
            avg_latency_ms=avg_latency,
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency,
            first_win_rate=first_wins / n,
            backtracking_rate=backtracks / n,
            contradiction_detection_rate=detected / actual if actual > 0 else 1.0,
            fallback_rate=fallbacks / n,
            rungs_histogram=self._compute_rungs_histogram(rungs),
            latency_histogram=self._compute_latency_histogram(latencies),
            meets_rungs_target=avg_rungs < self.targets.avg_rungs_evaluated,
            meets_latency_target=avg_latency < self.targets.decision_latency_ms,
            meets_first_win_target=first_wins / n > self.targets.first_win_rate,
            meets_backtracking_target=backtracks / n < self.targets.backtracking_rate,
            meets_contradiction_target=detected / actual > self.targets.contradiction_detection if actual > 0 else True,
        )

    # -------------------------------------------------------------------------
    # STATUS CHECKS
    # -------------------------------------------------------------------------

    def get_metric_status(self, metric_name: str) -> MetricStatus:
        """Get status of a specific metric relative to target."""
        metrics = self.get_metrics()

        if metric_name == "rungs":
            value = metrics.avg_rungs_evaluated
            target = self.targets.avg_rungs_evaluated
            lower_is_better = True
        elif metric_name == "latency":
            value = metrics.avg_latency_ms
            target = self.targets.decision_latency_ms
            lower_is_better = True
        elif metric_name == "first_win":
            value = metrics.first_win_rate
            target = self.targets.first_win_rate
            lower_is_better = False
        elif metric_name == "backtracking":
            value = metrics.backtracking_rate
            target = self.targets.backtracking_rate
            lower_is_better = True
        elif metric_name == "contradiction":
            value = metrics.contradiction_detection_rate
            target = self.targets.contradiction_detection
            lower_is_better = False
        else:
            return MetricStatus.WARNING

        return self._compute_status(value, target, lower_is_better)

    def _compute_status(
        self,
        value: float,
        target: float,
        lower_is_better: bool
    ) -> MetricStatus:
        """Compute status based on value vs target."""
        if target == 0:
            return MetricStatus.GOOD

        ratio = value / target

        if lower_is_better:
            if ratio < 0.8:
                return MetricStatus.EXCELLENT
            elif ratio <= 1.0:
                return MetricStatus.GOOD
            elif ratio <= 1.2:
                return MetricStatus.WARNING
            else:
                return MetricStatus.CRITICAL
        else:
            if ratio > 1.2:
                return MetricStatus.EXCELLENT
            elif ratio >= 1.0:
                return MetricStatus.GOOD
            elif ratio >= 0.8:
                return MetricStatus.WARNING
            else:
                return MetricStatus.CRITICAL

    def get_all_statuses(self) -> Dict[str, MetricStatus]:
        """Get status of all metrics."""
        return {
            'rungs': self.get_metric_status('rungs'),
            'latency': self.get_metric_status('latency'),
            'first_win': self.get_metric_status('first_win'),
            'backtracking': self.get_metric_status('backtracking'),
            'contradiction': self.get_metric_status('contradiction'),
        }

    def is_ready_for_rollout(self) -> Tuple[bool, List[str]]:
        """Check if metrics indicate readiness for rollout."""
        metrics = self.get_metrics()
        issues = []

        if not metrics.meets_rungs_target:
            issues.append(
                f"Avg rungs ({metrics.avg_rungs_evaluated:.1f}) exceeds target ({self.targets.avg_rungs_evaluated})"
            )
        if not metrics.meets_latency_target:
            issues.append(
                f"Avg latency ({metrics.avg_latency_ms:.1f}ms) exceeds target ({self.targets.decision_latency_ms}ms)"
            )
        if not metrics.meets_first_win_target:
            issues.append(
                f"First-win rate ({metrics.first_win_rate:.1%}) below target ({self.targets.first_win_rate:.0%})"
            )
        if not metrics.meets_backtracking_target:
            issues.append(
                f"Backtracking rate ({metrics.backtracking_rate:.1%}) exceeds target ({self.targets.backtracking_rate:.0%})"
            )
        if not metrics.meets_contradiction_target:
            issues.append(
                f"Contradiction detection ({metrics.contradiction_detection_rate:.1%}) below target ({self.targets.contradiction_detection:.0%})"
            )

        return len(issues) == 0, issues

    # -------------------------------------------------------------------------
    # RESET
    # -------------------------------------------------------------------------

    def reset(self) -> None:
        """Reset all metrics."""
        self._decisions.clear()
        self._latencies.clear()
        self._rungs.clear()
        self._game_metrics.clear()
        self._algorithm_metrics.clear()
        self._total_decisions = 0
        self._first_wins = 0
        self._backtracks = 0
        self._contradictions_detected = 0
        self._contradictions_actual = 0
        self._fallbacks = 0


# =============================================================================
# DATABASE SCHEMA
# =============================================================================

ROUTING_METRICS_SCHEMA = """
CREATE TABLE IF NOT EXISTS routing_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    game_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    rungs_evaluated INTEGER,
    latency_ms REAL,
    first_win INTEGER,
    backtracked INTEGER,
    contradictions_detected INTEGER,
    contradictions_actual INTEGER,
    algorithm_used TEXT,
    quadrant TEXT,
    used_fallback INTEGER
);

CREATE INDEX IF NOT EXISTS idx_routing_metrics_game_id ON routing_metrics(game_id);
CREATE INDEX IF NOT EXISTS idx_routing_metrics_algorithm ON routing_metrics(algorithm_used);
CREATE INDEX IF NOT EXISTS idx_routing_metrics_timestamp ON routing_metrics(timestamp);
"""
