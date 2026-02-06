"""
Routing Trace Storage - Phase 6.3.

Stores cognitive routing decisions and outcomes for:
1. Post-hoc analysis of routing decisions
2. Training signal for graph evolution
3. Debugging and observability
4. Performance optimization

Each trace captures:
- Path taken through the rung graph
- Algorithm used at each step
- Epistemic state transitions
- Final action and confidence
- Actual outcome (for learning)

Usage:
    store = RoutingTraceStore(db_interface)

    # Record a trace
    trace_id = store.record_trace(
        game_id="ab12-1",
        agent_id="agent_42",
        path=["survey", "control_tracker", "network_wisdom"],
        algorithm_used="landmark_astar",
        rumsfeld_assessment={"quadrant": "KK", "confidence": 0.85},
        final_action="ACTION3",
        final_confidence=0.9
    )

    # Later, update with outcome
    store.record_outcome(trace_id, outcome_score=1.0)
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class RumsfeldAssessment:
    """Epistemic state assessment at decision time."""
    quadrant: str                    # KK, KU, UK, UU
    confidence: float                # Overall confidence
    known_knowns: List[str] = field(default_factory=list)   # What we know we know
    known_unknowns: List[str] = field(default_factory=list) # What we know we don't know

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            'quadrant': self.quadrant,
            'confidence': self.confidence,
            'known_knowns': self.known_knowns,
            'known_unknowns': self.known_unknowns,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RumsfeldAssessment':
        """Create from dictionary."""
        return cls(
            quadrant=data.get('quadrant', 'UU'),
            confidence=data.get('confidence', 0.5),
            known_knowns=data.get('known_knowns', []),
            known_unknowns=data.get('known_unknowns', []),
        )


@dataclass
class RoutingTrace:
    """Complete trace of a routing decision."""
    trace_id: str
    timestamp: str
    game_id: str
    agent_id: str

    # Path information
    path: List[str]                  # Ordered list of rung names traversed
    algorithm_used: str              # Primary algorithm used
    algorithms_history: List[str] = field(default_factory=list)  # All algorithms used

    # Epistemic state
    initial_quadrant: str = "UU"
    final_quadrant: str = "UU"
    quadrant_transitions: List[Tuple[str, str]] = field(default_factory=list)
    rumsfeld_assessment: Optional[RumsfeldAssessment] = None

    # Decision output
    final_action: str = ""
    final_confidence: float = 0.0
    backtrack_count: int = 0
    iterations: int = 0

    # Outcome (filled in later)
    outcome_score: Optional[float] = None
    outcome_reason: str = ""

    # Timing
    decision_latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'trace_id': self.trace_id,
            'timestamp': self.timestamp,
            'game_id': self.game_id,
            'agent_id': self.agent_id,
            'path': self.path,
            'algorithm_used': self.algorithm_used,
            'algorithms_history': self.algorithms_history,
            'initial_quadrant': self.initial_quadrant,
            'final_quadrant': self.final_quadrant,
            'quadrant_transitions': self.quadrant_transitions,
            'rumsfeld_assessment': self.rumsfeld_assessment.to_dict() if self.rumsfeld_assessment else None,
            'final_action': self.final_action,
            'final_confidence': self.final_confidence,
            'backtrack_count': self.backtrack_count,
            'iterations': self.iterations,
            'outcome_score': self.outcome_score,
            'outcome_reason': self.outcome_reason,
            'decision_latency_ms': self.decision_latency_ms,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RoutingTrace':
        """Create from dictionary."""
        rumsfeld = data.get('rumsfeld_assessment')
        return cls(
            trace_id=data['trace_id'],
            timestamp=data['timestamp'],
            game_id=data['game_id'],
            agent_id=data['agent_id'],
            path=data.get('path', []),
            algorithm_used=data.get('algorithm_used', 'unknown'),
            algorithms_history=data.get('algorithms_history', []),
            initial_quadrant=data.get('initial_quadrant', 'UU'),
            final_quadrant=data.get('final_quadrant', 'UU'),
            quadrant_transitions=data.get('quadrant_transitions', []),
            rumsfeld_assessment=RumsfeldAssessment.from_dict(rumsfeld) if rumsfeld else None,
            final_action=data.get('final_action', ''),
            final_confidence=data.get('final_confidence', 0.0),
            backtrack_count=data.get('backtrack_count', 0),
            iterations=data.get('iterations', 0),
            outcome_score=data.get('outcome_score'),
            outcome_reason=data.get('outcome_reason', ''),
            decision_latency_ms=data.get('decision_latency_ms', 0.0),
        )


@dataclass
class TraceQuery:
    """Query parameters for trace retrieval."""
    game_id: Optional[str] = None
    agent_id: Optional[str] = None
    algorithm: Optional[str] = None
    quadrant: Optional[str] = None
    min_confidence: Optional[float] = None
    max_confidence: Optional[float] = None
    has_outcome: Optional[bool] = None
    limit: int = 100
    offset: int = 0


# =============================================================================
# DATABASE ADAPTER
# =============================================================================

class _CursorProxy:
    """Proxy for cursor-like result from DatabaseInterface.execute_query."""

    def __init__(self, results: list):
        self._results = results
        self.rowcount = len(results)

    def fetchone(self):
        return self._results[0] if self._results else None

    def fetchall(self):
        return self._results


class _DatabaseInterfaceAdapter:
    """Adapts DatabaseInterface (execute_query) to sqlite3-like interface (execute).

    The RoutingTraceStore was written for raw sqlite3 connections that have
    .execute() returning cursors. DatabaseInterface provides .execute_query()
    which returns List[Dict]. This adapter bridges the gap.
    """

    def __init__(self, db_interface: Any):
        self._db = db_interface

    def execute(self, sql: str, params: tuple = ()) -> '_CursorProxy':
        """Execute SQL via DatabaseInterface.execute_query, return cursor-like proxy."""
        try:
            results = self._db.execute_query(sql, params)
            # Convert List[Dict] to List[tuple] for positional row access
            if results and isinstance(results[0], dict):
                rows = [tuple(r.values()) for r in results]
            else:
                rows = results or []
            return _CursorProxy(rows)
        except Exception:
            return _CursorProxy([])


# =============================================================================
# ROUTING TRACE STORE
# =============================================================================

class RoutingTraceStore:
    """
    Storage and retrieval for cognitive routing traces.

    Supports:
    - Recording traces during decisions
    - Updating traces with outcomes
    - Querying traces for analysis
    - Aggregating trace statistics
    """

    def __init__(self, db_interface: Optional[Any] = None):
        """Initialize trace store.

        Args:
            db_interface: Either a raw sqlite3 connection (has .execute)
                         or a DatabaseInterface (has .execute_query).
                         Wraps DatabaseInterface to provide .execute compatibility.
        """
        self.db = db_interface

        # If the db has execute_query but not execute, wrap it for compatibility
        if self.db and not hasattr(self.db, 'execute') and hasattr(self.db, 'execute_query'):
            self.db = _DatabaseInterfaceAdapter(self.db)

        # Ensure schema exists
        if self.db:
            self._ensure_schema()

        # In-memory cache for recent traces
        self._recent_traces: Dict[str, RoutingTrace] = {}
        self._max_cache_size = 1000

        # Statistics
        self._total_traces = 0
        self._traces_with_outcome = 0

        logger.info("[TRACE-STORE] Routing trace store initialized")

    def _ensure_schema(self) -> None:
        """Ensure the routing traces table exists."""
        if not self.db:
            return
        try:
            for statement in ROUTING_TRACES_SCHEMA.split(';'):
                statement = statement.strip()
                if statement:
                    self.db.execute(statement)
            logger.debug("[TRACE-STORE] Schema verified/created")
        except Exception as e:
            logger.warning(f"[TRACE-STORE] Schema creation warning: {e}")

    # -------------------------------------------------------------------------
    # TRACE RECORDING
    # -------------------------------------------------------------------------

    def record_trace(
        self,
        game_id: str,
        agent_id: str,
        path: List[str],
        algorithm_used: str,
        final_action: str,
        final_confidence: float,
        rumsfeld_assessment: Optional[Dict[str, Any]] = None,
        initial_quadrant: str = "UU",
        final_quadrant: str = "UU",
        quadrant_transitions: Optional[List[Tuple[str, str]]] = None,
        algorithms_history: Optional[List[str]] = None,
        backtrack_count: int = 0,
        iterations: int = 0,
        decision_latency_ms: float = 0.0
    ) -> str:
        """
        Record a routing trace.

        Returns:
            Trace ID for later outcome update
        """
        trace_id = str(uuid.uuid4())[:8]

        trace = RoutingTrace(
            trace_id=trace_id,
            timestamp=datetime.now().isoformat(),
            game_id=game_id,
            agent_id=agent_id,
            path=path,
            algorithm_used=algorithm_used,
            algorithms_history=algorithms_history or [algorithm_used],
            initial_quadrant=initial_quadrant,
            final_quadrant=final_quadrant,
            quadrant_transitions=quadrant_transitions or [],
            rumsfeld_assessment=(
                RumsfeldAssessment.from_dict(rumsfeld_assessment)
                if rumsfeld_assessment else None
            ),
            final_action=final_action,
            final_confidence=final_confidence,
            backtrack_count=backtrack_count,
            iterations=iterations,
            decision_latency_ms=decision_latency_ms,
        )

        # Cache
        self._cache_trace(trace)

        # Persist
        if self.db:
            self._save_trace(trace)

        self._total_traces += 1

        logger.debug(
            f"[TRACE-STORE] Recorded trace {trace_id}: "
            f"{len(path)} rungs, {algorithm_used}, {final_action}"
        )

        return trace_id

    def record_outcome(
        self,
        trace_id: str,
        outcome_score: float,
        outcome_reason: str = ""
    ) -> bool:
        """
        Update a trace with its outcome.

        Args:
            trace_id: Trace to update
            outcome_score: Score in [0, 1] (0 = bad, 1 = good)
            outcome_reason: Optional explanation

        Returns:
            True if trace was found and updated
        """
        # Try cache first
        if trace_id in self._recent_traces:
            trace = self._recent_traces[trace_id]
            trace.outcome_score = outcome_score
            trace.outcome_reason = outcome_reason

            if self.db:
                self._update_trace_outcome(trace_id, outcome_score, outcome_reason)

            self._traces_with_outcome += 1
            return True

        # Try database
        if self.db:
            success = self._update_trace_outcome(trace_id, outcome_score, outcome_reason)
            if success:
                self._traces_with_outcome += 1
            return success

        return False

    # -------------------------------------------------------------------------
    # TRACE RETRIEVAL
    # -------------------------------------------------------------------------

    def get_trace(self, trace_id: str) -> Optional[RoutingTrace]:
        """Get a trace by ID."""
        # Check cache
        if trace_id in self._recent_traces:
            return self._recent_traces[trace_id]

        # Check database
        if self.db:
            return self._load_trace(trace_id)

        return None

    def query_traces(self, query: TraceQuery) -> List[RoutingTrace]:
        """Query traces with filters."""
        if not self.db:
            # Query from cache only
            return self._query_cache(query)

        return self._query_db(query)

    def get_traces_for_game(self, game_id: str) -> List[RoutingTrace]:
        """Get all traces for a game."""
        return self.query_traces(TraceQuery(game_id=game_id))

    def get_traces_for_agent(self, agent_id: str) -> List[RoutingTrace]:
        """Get all traces for an agent."""
        return self.query_traces(TraceQuery(agent_id=agent_id))

    def get_recent_traces(self, n: int = 10) -> List[RoutingTrace]:
        """Get most recent traces."""
        traces = list(self._recent_traces.values())
        traces.sort(key=lambda t: t.timestamp, reverse=True)
        return traces[:n]

    # -------------------------------------------------------------------------
    # STATISTICS
    # -------------------------------------------------------------------------

    def get_statistics(self) -> Dict[str, Any]:
        """Get trace store statistics."""
        # Compute from cache/db
        traces = list(self._recent_traces.values())

        if not traces:
            return {
                'total_traces': self._total_traces,
                'traces_with_outcome': self._traces_with_outcome,
                'cache_size': 0,
                'avg_path_length': 0,
                'avg_confidence': 0,
                'avg_latency_ms': 0,
                'by_algorithm': {},
                'by_quadrant': {},
            }

        # Aggregate stats
        by_algorithm: Dict[str, int] = {}
        by_quadrant: Dict[str, int] = {}
        path_lengths = []
        confidences = []
        latencies = []

        for trace in traces:
            by_algorithm[trace.algorithm_used] = by_algorithm.get(trace.algorithm_used, 0) + 1
            by_quadrant[trace.final_quadrant] = by_quadrant.get(trace.final_quadrant, 0) + 1
            path_lengths.append(len(trace.path))
            confidences.append(trace.final_confidence)
            latencies.append(trace.decision_latency_ms)

        return {
            'total_traces': self._total_traces,
            'traces_with_outcome': self._traces_with_outcome,
            'cache_size': len(self._recent_traces),
            'avg_path_length': sum(path_lengths) / len(path_lengths),
            'avg_confidence': sum(confidences) / len(confidences),
            'avg_latency_ms': sum(latencies) / len(latencies),
            'by_algorithm': by_algorithm,
            'by_quadrant': by_quadrant,
        }

    def get_outcome_correlation(self) -> Dict[str, Any]:
        """Get correlation between routing decisions and outcomes."""
        traces_with_outcome = [
            t for t in self._recent_traces.values()
            if t.outcome_score is not None
        ]

        if not traces_with_outcome:
            return {'count': 0}

        # Aggregate by algorithm
        by_algorithm: Dict[str, List[float]] = {}
        for trace in traces_with_outcome:
            alg = trace.algorithm_used
            if alg not in by_algorithm:
                by_algorithm[alg] = []
            by_algorithm[alg].append(trace.outcome_score)

        algorithm_performance = {
            alg: sum(scores) / len(scores)
            for alg, scores in by_algorithm.items()
        }

        # Aggregate by quadrant
        by_quadrant: Dict[str, List[float]] = {}
        for trace in traces_with_outcome:
            q = trace.final_quadrant
            if q not in by_quadrant:
                by_quadrant[q] = []
            by_quadrant[q].append(trace.outcome_score)

        quadrant_performance = {
            q: sum(scores) / len(scores)
            for q, scores in by_quadrant.items()
        }

        return {
            'count': len(traces_with_outcome),
            'algorithm_performance': algorithm_performance,
            'quadrant_performance': quadrant_performance,
        }

    # -------------------------------------------------------------------------
    # CACHE MANAGEMENT
    # -------------------------------------------------------------------------

    def _cache_trace(self, trace: RoutingTrace) -> None:
        """Add trace to cache, evicting old entries if needed."""
        if len(self._recent_traces) >= self._max_cache_size:
            # Evict oldest
            oldest_id = min(
                self._recent_traces.keys(),
                key=lambda k: self._recent_traces[k].timestamp
            )
            del self._recent_traces[oldest_id]

        self._recent_traces[trace.trace_id] = trace

    def _query_cache(self, query: TraceQuery) -> List[RoutingTrace]:
        """Query traces from cache."""
        results = []

        for trace in self._recent_traces.values():
            if query.game_id and trace.game_id != query.game_id:
                continue
            if query.agent_id and trace.agent_id != query.agent_id:
                continue
            if query.algorithm and trace.algorithm_used != query.algorithm:
                continue
            if query.quadrant and trace.final_quadrant != query.quadrant:
                continue
            if query.min_confidence and trace.final_confidence < query.min_confidence:
                continue
            if query.max_confidence and trace.final_confidence > query.max_confidence:
                continue
            if query.has_outcome is not None:
                if query.has_outcome and trace.outcome_score is None:
                    continue
                if not query.has_outcome and trace.outcome_score is not None:
                    continue

            results.append(trace)

        # Sort by timestamp descending
        results.sort(key=lambda t: t.timestamp, reverse=True)

        # Apply limit/offset
        return results[query.offset:query.offset + query.limit]

    # -------------------------------------------------------------------------
    # DATABASE OPERATIONS
    # -------------------------------------------------------------------------

    def _save_trace(self, trace: RoutingTrace) -> None:
        """Save trace to database."""
        if not self.db:
            return

        try:
            self.db.execute("""
                INSERT INTO cognitive_routing_traces (
                    trace_id, timestamp, game_id, agent_id,
                    path, algorithm_used, algorithms_history,
                    initial_quadrant, final_quadrant, quadrant_transitions,
                    rumsfeld_assessment, final_action, final_confidence,
                    backtrack_count, iterations, decision_latency_ms,
                    outcome_score, outcome_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trace.trace_id,
                trace.timestamp,
                trace.game_id,
                trace.agent_id,
                json.dumps(trace.path),
                trace.algorithm_used,
                json.dumps(trace.algorithms_history),
                trace.initial_quadrant,
                trace.final_quadrant,
                json.dumps(trace.quadrant_transitions),
                json.dumps(trace.rumsfeld_assessment.to_dict()) if trace.rumsfeld_assessment else None,
                trace.final_action,
                trace.final_confidence,
                trace.backtrack_count,
                trace.iterations,
                trace.decision_latency_ms,
                trace.outcome_score,
                trace.outcome_reason,
            ))
        except Exception as e:
            logger.error(f"[TRACE-STORE] Failed to save trace: {e}")

    def _update_trace_outcome(
        self,
        trace_id: str,
        outcome_score: float,
        outcome_reason: str
    ) -> bool:
        """Update trace outcome in database."""
        if not self.db:
            return False

        try:
            cursor = self.db.execute("""
                UPDATE cognitive_routing_traces
                SET outcome_score = ?, outcome_reason = ?
                WHERE trace_id = ?
            """, (outcome_score, outcome_reason, trace_id))
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"[TRACE-STORE] Failed to update outcome: {e}")
            return False

    def _load_trace(self, trace_id: str) -> Optional[RoutingTrace]:
        """Load trace from database."""
        if not self.db:
            return None

        try:
            row = self.db.execute("""
                SELECT trace_id, timestamp, game_id, agent_id,
                       path, algorithm_used, algorithms_history,
                       initial_quadrant, final_quadrant, quadrant_transitions,
                       rumsfeld_assessment, final_action, final_confidence,
                       backtrack_count, iterations, decision_latency_ms,
                       outcome_score, outcome_reason
                FROM cognitive_routing_traces
                WHERE trace_id = ?
            """, (trace_id,)).fetchone()

            if not row:
                return None

            return RoutingTrace(
                trace_id=row[0],
                timestamp=row[1],
                game_id=row[2],
                agent_id=row[3],
                path=json.loads(row[4]) if row[4] else [],
                algorithm_used=row[5],
                algorithms_history=json.loads(row[6]) if row[6] else [],
                initial_quadrant=row[7],
                final_quadrant=row[8],
                quadrant_transitions=json.loads(row[9]) if row[9] else [],
                rumsfeld_assessment=(
                    RumsfeldAssessment.from_dict(json.loads(row[10]))
                    if row[10] else None
                ),
                final_action=row[11],
                final_confidence=row[12],
                backtrack_count=row[13],
                iterations=row[14],
                decision_latency_ms=row[15],
                outcome_score=row[16],
                outcome_reason=row[17] or "",
            )
        except Exception as e:
            logger.error(f"[TRACE-STORE] Failed to load trace: {e}")
            return None

    def _query_db(self, query: TraceQuery) -> List[RoutingTrace]:
        """Query traces from database."""
        if not self.db:
            return []

        try:
            conditions = []
            params = []

            if query.game_id:
                conditions.append("game_id = ?")
                params.append(query.game_id)
            if query.agent_id:
                conditions.append("agent_id = ?")
                params.append(query.agent_id)
            if query.algorithm:
                conditions.append("algorithm_used = ?")
                params.append(query.algorithm)
            if query.quadrant:
                conditions.append("final_quadrant = ?")
                params.append(query.quadrant)
            if query.min_confidence is not None:
                conditions.append("final_confidence >= ?")
                params.append(query.min_confidence)
            if query.max_confidence is not None:
                conditions.append("final_confidence <= ?")
                params.append(query.max_confidence)
            if query.has_outcome is not None:
                if query.has_outcome:
                    conditions.append("outcome_score IS NOT NULL")
                else:
                    conditions.append("outcome_score IS NULL")

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            sql = f"""
                SELECT trace_id, timestamp, game_id, agent_id,
                       path, algorithm_used, algorithms_history,
                       initial_quadrant, final_quadrant, quadrant_transitions,
                       rumsfeld_assessment, final_action, final_confidence,
                       backtrack_count, iterations, decision_latency_ms,
                       outcome_score, outcome_reason
                FROM cognitive_routing_traces
                WHERE {where_clause}
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            """
            params.extend([query.limit, query.offset])

            rows = self.db.execute(sql, params).fetchall()

            traces = []
            for row in rows:
                trace = RoutingTrace(
                    trace_id=row[0],
                    timestamp=row[1],
                    game_id=row[2],
                    agent_id=row[3],
                    path=json.loads(row[4]) if row[4] else [],
                    algorithm_used=row[5],
                    algorithms_history=json.loads(row[6]) if row[6] else [],
                    initial_quadrant=row[7],
                    final_quadrant=row[8],
                    quadrant_transitions=json.loads(row[9]) if row[9] else [],
                    rumsfeld_assessment=(
                        RumsfeldAssessment.from_dict(json.loads(row[10]))
                        if row[10] else None
                    ),
                    final_action=row[11],
                    final_confidence=row[12],
                    backtrack_count=row[13],
                    iterations=row[14],
                    decision_latency_ms=row[15],
                    outcome_score=row[16],
                    outcome_reason=row[17] or "",
                )
                traces.append(trace)

            return traces

        except Exception as e:
            logger.error(f"[TRACE-STORE] Failed to query traces: {e}")
            return []


# =============================================================================
# DATABASE SCHEMA
# =============================================================================

ROUTING_TRACES_SCHEMA = """
CREATE TABLE IF NOT EXISTS cognitive_routing_traces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trace_id TEXT UNIQUE NOT NULL,
    timestamp TEXT NOT NULL,
    game_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    path TEXT,
    algorithm_used TEXT,
    algorithms_history TEXT,
    initial_quadrant TEXT,
    final_quadrant TEXT,
    quadrant_transitions TEXT,
    rumsfeld_assessment TEXT,
    final_action TEXT,
    final_confidence REAL,
    backtrack_count INTEGER DEFAULT 0,
    iterations INTEGER DEFAULT 0,
    decision_latency_ms REAL DEFAULT 0.0,
    outcome_score REAL,
    outcome_reason TEXT
);

CREATE INDEX IF NOT EXISTS idx_routing_traces_game_id ON cognitive_routing_traces(game_id);
CREATE INDEX IF NOT EXISTS idx_routing_traces_agent_id ON cognitive_routing_traces(agent_id);
CREATE INDEX IF NOT EXISTS idx_routing_traces_algorithm ON cognitive_routing_traces(algorithm_used);
CREATE INDEX IF NOT EXISTS idx_routing_traces_timestamp ON cognitive_routing_traces(timestamp);
CREATE INDEX IF NOT EXISTS idx_routing_traces_outcome ON cognitive_routing_traces(outcome_score);
"""
