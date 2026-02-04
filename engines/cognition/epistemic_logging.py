"""
Epistemic Logging for Cognitive Routing.

This module provides structured logging for epistemic state tracking,
enabling analysis and debugging of routing decisions.

Phase 1.6.4 of cognitive_routing_implementation_plan.md

Key features:
1. EpistemicTraceEntry - lightweight dataclass for trace records
2. EpistemicLogger - manages trace lifecycle and persistence
3. SQL schema for epistemic_traces table
4. Summary generation for analysis
"""

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# Import from Phase 1.5
try:
    from engines.cognition.epistemic_state import EpistemicQuadrant as RumsfeldQuadrant
    from engines.cognition.epistemic_state import (
        EpistemicSnapshot,
        EpistemicState,
        EpistemicTransition,
    )
except ImportError:
    # Fallback for standalone testing
    from enum import Enum
    class RumsfeldQuadrant(Enum):
        KK = "KK"
        KU = "KU"
        UK = "UK"
        UU = "UU"

logger = logging.getLogger(__name__)


# =============================================================================
# SQL SCHEMA (for complete_database_schema.sql integration)
# =============================================================================

EPISTEMIC_TRACES_SCHEMA = """
-- Epistemic state traces for analysis and debugging
-- Added: Phase 1.6.4 cognitive routing
CREATE TABLE IF NOT EXISTS epistemic_traces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    agent_id TEXT,

    -- Timing
    tick INTEGER NOT NULL,
    timestamp_ms INTEGER NOT NULL,

    -- State
    quadrant TEXT NOT NULL,  -- KK, KU, UK, UU
    confidence REAL NOT NULL,
    certainty REAL NOT NULL,

    -- Transition info (null if no transition this tick)
    transition_from TEXT,
    transition_to TEXT,
    transition_reason TEXT,

    -- Algorithm
    algorithm_selected TEXT,
    algorithm_reason TEXT,

    -- Metrics
    thrashing_score REAL,
    active_questions INTEGER,
    uk_potential REAL,

    -- Full context (JSON blob)
    context_json TEXT,

    -- Indexing
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indices for common queries
CREATE INDEX IF NOT EXISTS idx_epistemic_traces_game
    ON epistemic_traces(game_id);
CREATE INDEX IF NOT EXISTS idx_epistemic_traces_agent
    ON epistemic_traces(agent_id);
CREATE INDEX IF NOT EXISTS idx_epistemic_traces_quadrant
    ON epistemic_traces(quadrant);
CREATE INDEX IF NOT EXISTS idx_epistemic_traces_tick
    ON epistemic_traces(game_id, tick);
"""


# =============================================================================
# TRACE ENTRY
# =============================================================================

@dataclass
class EpistemicTraceEntry:
    """
    Lightweight trace entry for epistemic state logging.

    Designed to be serializable and efficient for high-frequency logging.
    """
    # Required fields
    game_id: str
    tick: int
    quadrant: str           # "KK", "KU", "UK", "UU"
    confidence: float
    certainty: float

    # Optional timing
    timestamp_ms: int = 0
    agent_id: Optional[str] = None

    # Transition info
    transition_from: Optional[str] = None
    transition_to: Optional[str] = None
    transition_reason: Optional[str] = None

    # Algorithm selection
    algorithm_selected: Optional[str] = None
    algorithm_reason: Optional[str] = None

    # Metrics
    thrashing_score: float = 0.0
    active_questions: int = 0
    uk_potential: float = 0.0

    # Extended context (not indexed, stored as JSON)
    context: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.timestamp_ms == 0:
            self.timestamp_ms = int(time.time() * 1000)

    @classmethod
    def from_state(
        cls,
        game_id: str,
        tick: int,
        state: "EpistemicState",
        agent_id: Optional[str] = None,
        transition: Optional["EpistemicTransition"] = None,
        algorithm: Optional[str] = None,
        algorithm_reason: Optional[str] = None,
        thrashing_score: float = 0.0,
        active_questions: int = 0,
        uk_potential: float = 0.0,
        context: Optional[Dict[str, Any]] = None
    ) -> "EpistemicTraceEntry":
        """Create trace entry from EpistemicState."""
        # Extract values from the actual EpistemicState structure
        # Use .name to get "KK", "KU", etc. instead of .value which gives "known_known"
        entry = cls(
            game_id=game_id,
            tick=tick,
            quadrant=state.primary_quadrant.name,  # Use .name for short form
            confidence=state.kk_confidence,
            certainty=1.0 - state.uu_estimate,
            agent_id=agent_id,
            algorithm_selected=algorithm,
            algorithm_reason=algorithm_reason,
            thrashing_score=thrashing_score,
            active_questions=active_questions,
            uk_potential=uk_potential if uk_potential > 0 else state.uk_potential,
            context=context or {}
        )

        if transition:
            entry.transition_from = transition.from_quadrant.name  # Use .name
            entry.transition_to = transition.to_quadrant.name      # Use .name
            entry.transition_reason = transition.trigger_reason

        return entry

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    def to_db_row(self) -> Dict[str, Any]:
        """Convert to database row format."""
        return {
            "game_id": self.game_id,
            "agent_id": self.agent_id,
            "tick": self.tick,
            "timestamp_ms": self.timestamp_ms,
            "quadrant": self.quadrant,
            "confidence": self.confidence,
            "certainty": self.certainty,
            "transition_from": self.transition_from,
            "transition_to": self.transition_to,
            "transition_reason": self.transition_reason,
            "algorithm_selected": self.algorithm_selected,
            "algorithm_reason": self.algorithm_reason,
            "thrashing_score": self.thrashing_score,
            "active_questions": self.active_questions,
            "uk_potential": self.uk_potential,
            "context_json": json.dumps(self.context) if self.context else None,
        }


# =============================================================================
# EPISTEMIC LOGGER
# =============================================================================

class EpistemicLogger:
    """
    Manages epistemic state logging with buffered writes.

    Usage:
        logger = EpistemicLogger(game_id="FT09", buffer_size=50)

        # Log each tick
        entry = EpistemicTraceEntry.from_state(...)
        logger.log(entry)

        # Periodic flush to DB
        if tick % 50 == 0:
            logger.flush(db_interface)

        # Get summary for analysis
        summary = logger.get_summary()
    """

    DEFAULT_BUFFER_SIZE = 100

    def __init__(
        self,
        game_id: str,
        agent_id: Optional[str] = None,
        buffer_size: int = DEFAULT_BUFFER_SIZE,
        auto_flush: bool = False
    ):
        """
        Initialize epistemic logger.

        Args:
            game_id: Current game identifier
            agent_id: Optional agent identifier
            buffer_size: Number of entries before auto-flush
            auto_flush: Whether to auto-flush when buffer is full
        """
        self.game_id = game_id
        self.agent_id = agent_id
        self.buffer_size = buffer_size
        self.auto_flush = auto_flush

        self._buffer: List[EpistemicTraceEntry] = []
        self._flushed_count = 0

        # Summary statistics (maintained incrementally)
        self._quadrant_counts: Dict[str, int] = {
            "KK": 0, "KU": 0, "UK": 0, "UU": 0
        }
        self._transition_counts: Dict[str, int] = {}  # "KK->KU": count
        self._algorithm_counts: Dict[str, int] = {}
        self._total_thrashing = 0.0
        self._max_thrashing = 0.0

    def log(self, entry: EpistemicTraceEntry) -> None:
        """
        Log an epistemic trace entry.

        Args:
            entry: Trace entry to log
        """
        self._buffer.append(entry)

        # Update summary stats
        self._quadrant_counts[entry.quadrant] += 1

        if entry.transition_from and entry.transition_to:
            key = f"{entry.transition_from}->{entry.transition_to}"
            self._transition_counts[key] = self._transition_counts.get(key, 0) + 1

        if entry.algorithm_selected:
            self._algorithm_counts[entry.algorithm_selected] = \
                self._algorithm_counts.get(entry.algorithm_selected, 0) + 1

        self._total_thrashing += entry.thrashing_score
        self._max_thrashing = max(self._max_thrashing, entry.thrashing_score)

        # Auto-flush if enabled and buffer full
        if self.auto_flush and len(self._buffer) >= self.buffer_size:
            logger.debug(f"EpistemicLogger: Auto-flush at {len(self._buffer)} entries")
            # Note: Actual flush requires db_interface, caller must handle

    def log_from_state(
        self,
        tick: int,
        state: "EpistemicState",
        transition: Optional["EpistemicTransition"] = None,
        algorithm: Optional[str] = None,
        algorithm_reason: Optional[str] = None,
        thrashing_score: float = 0.0,
        active_questions: int = 0,
        uk_potential: float = 0.0,
        context: Optional[Dict[str, Any]] = None
    ) -> EpistemicTraceEntry:
        """
        Convenience method to create and log entry from EpistemicState.

        Args:
            tick: Current tick number
            state: Current epistemic state
            transition: Optional transition that just occurred
            algorithm: Selected algorithm
            algorithm_reason: Reason for algorithm selection
            thrashing_score: Current thrashing score
            active_questions: Number of active questions
            uk_potential: UK potential index score
            context: Additional context data

        Returns:
            The created trace entry
        """
        entry = EpistemicTraceEntry.from_state(
            game_id=self.game_id,
            tick=tick,
            state=state,
            agent_id=self.agent_id,
            transition=transition,
            algorithm=algorithm,
            algorithm_reason=algorithm_reason,
            thrashing_score=thrashing_score,
            active_questions=active_questions,
            uk_potential=uk_potential,
            context=context
        )
        self.log(entry)
        return entry

    def flush(self, db_interface: Optional[Any] = None) -> int:
        """
        Flush buffer to database.

        Args:
            db_interface: Database interface with execute_many method

        Returns:
            Number of entries flushed
        """
        if not self._buffer:
            return 0

        count = len(self._buffer)

        if db_interface:
            try:
                rows = [e.to_db_row() for e in self._buffer]
                # Batch insert
                columns = list(rows[0].keys())
                placeholders = ", ".join(["?" for _ in columns])
                column_str = ", ".join(columns)

                sql = f"INSERT INTO epistemic_traces ({column_str}) VALUES ({placeholders})"
                values = [tuple(row[c] for c in columns) for row in rows]

                db_interface.execute_many(sql, values)
                logger.debug(f"EpistemicLogger: Flushed {count} entries to DB")
            except Exception as e:
                logger.error(f"EpistemicLogger: Flush failed: {e}")
                # Keep buffer on failure
                return 0
        else:
            logger.debug(f"EpistemicLogger: Discarding {count} entries (no DB)")

        self._flushed_count += count
        self._buffer.clear()
        return count

    def get_buffer(self) -> List[EpistemicTraceEntry]:
        """Get current buffer contents."""
        return list(self._buffer)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for the game.

        Returns:
            Dictionary with quadrant distribution, transitions, algorithms, etc.
        """
        total_ticks = sum(self._quadrant_counts.values())

        # Calculate quadrant percentages
        quadrant_pcts = {}
        for q, count in self._quadrant_counts.items():
            quadrant_pcts[q] = count / total_ticks if total_ticks > 0 else 0.0

        # Find dominant quadrant
        dominant_quadrant = max(
            self._quadrant_counts.items(),
            key=lambda x: x[1]
        )[0] if total_ticks > 0 else "UU"

        # Calculate stability (inverse of transition rate)
        total_transitions = sum(self._transition_counts.values())
        transition_rate = total_transitions / total_ticks if total_ticks > 0 else 0.0
        stability = 1.0 - min(1.0, transition_rate)

        # Average thrashing
        avg_thrashing = self._total_thrashing / total_ticks if total_ticks > 0 else 0.0

        return {
            "game_id": self.game_id,
            "agent_id": self.agent_id,
            "total_ticks": total_ticks,
            "buffered": len(self._buffer),
            "flushed": self._flushed_count,

            "quadrant_counts": dict(self._quadrant_counts),
            "quadrant_percentages": quadrant_pcts,
            "dominant_quadrant": dominant_quadrant,

            "transition_counts": dict(self._transition_counts),
            "total_transitions": total_transitions,
            "transition_rate": transition_rate,
            "stability": stability,

            "algorithm_counts": dict(self._algorithm_counts),

            "avg_thrashing_score": avg_thrashing,
            "max_thrashing_score": self._max_thrashing,
        }

    def get_transition_matrix(self) -> Dict[str, Dict[str, int]]:
        """
        Get transition matrix for analysis.

        Returns:
            Nested dict: from_quadrant -> to_quadrant -> count
        """
        matrix = {q: {"KK": 0, "KU": 0, "UK": 0, "UU": 0} for q in ["KK", "KU", "UK", "UU"]}

        for key, count in self._transition_counts.items():
            parts = key.split("->")
            if len(parts) == 2:
                from_q, to_q = parts
                if from_q in matrix and to_q in matrix[from_q]:
                    matrix[from_q][to_q] = count

        return matrix

    def detect_patterns(self) -> Dict[str, Any]:
        """
        Detect patterns in epistemic state history.

        Returns:
            Dictionary with detected patterns:
            - oscillation: Repeated back-and-forth transitions
            - stagnation: Long periods in single quadrant
            - regression_bursts: Multiple regressions in short time
        """
        patterns = {
            "oscillation": False,
            "stagnation": False,
            "regression_bursts": False,
            "pattern_details": {}
        }

        if len(self._buffer) < 10:
            return patterns

        # Check for oscillation (same transition appears > 20% of transitions)
        if self._transition_counts:
            max_transition_count = max(self._transition_counts.values())
            total_transitions = sum(self._transition_counts.values())
            if total_transitions > 5 and max_transition_count / total_transitions > 0.4:
                patterns["oscillation"] = True
                patterns["pattern_details"]["oscillating_transition"] = max(
                    self._transition_counts.items(),
                    key=lambda x: x[1]
                )[0]

        # Check for stagnation (> 80% in one quadrant)
        total_ticks = sum(self._quadrant_counts.values())
        if total_ticks > 10:
            max_quadrant_count = max(self._quadrant_counts.values())
            if max_quadrant_count / total_ticks > 0.8:
                patterns["stagnation"] = True
                patterns["pattern_details"]["stagnant_quadrant"] = max(
                    self._quadrant_counts.items(),
                    key=lambda x: x[1]
                )[0]

        # Check for regression bursts (high thrashing score)
        if self._max_thrashing > 0.5:
            patterns["regression_bursts"] = True
            patterns["pattern_details"]["max_thrashing"] = self._max_thrashing

        return patterns

    def reset(self) -> None:
        """Reset logger for a new game."""
        self._buffer.clear()
        self._flushed_count = 0
        self._quadrant_counts = {"KK": 0, "KU": 0, "UK": 0, "UU": 0}
        self._transition_counts.clear()
        self._algorithm_counts.clear()
        self._total_thrashing = 0.0
        self._max_thrashing = 0.0

    def __repr__(self) -> str:
        return (
            f"EpistemicLogger(game={self.game_id}, "
            f"buffered={len(self._buffer)}, "
            f"flushed={self._flushed_count})"
        )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_epistemic_tables(db_interface: Any) -> bool:
    """
    Create epistemic_traces table if it doesn't exist.

    Args:
        db_interface: Database interface with execute method

    Returns:
        True if successful
    """
    try:
        # Split schema into individual statements
        statements = [s.strip() for s in EPISTEMIC_TRACES_SCHEMA.split(";") if s.strip()]
        for stmt in statements:
            if stmt and not stmt.startswith("--"):
                db_interface.execute(stmt + ";")
        return True
    except Exception as e:
        logger.error(f"Failed to create epistemic tables: {e}")
        return False


def load_traces_for_game(
    db_interface: Any,
    game_id: str,
    limit: int = 1000
) -> List[EpistemicTraceEntry]:
    """
    Load traces for a specific game from database.

    Args:
        db_interface: Database interface
        game_id: Game ID to load traces for
        limit: Maximum number of traces to load

    Returns:
        List of EpistemicTraceEntry objects
    """
    try:
        sql = """
            SELECT game_id, agent_id, tick, timestamp_ms, quadrant, confidence,
                   certainty, transition_from, transition_to, transition_reason,
                   algorithm_selected, algorithm_reason, thrashing_score,
                   active_questions, uk_potential, context_json
            FROM epistemic_traces
            WHERE game_id = ?
            ORDER BY tick
            LIMIT ?
        """
        rows = db_interface.execute(sql, (game_id, limit)).fetchall()

        entries = []
        for row in rows:
            context = json.loads(row[15]) if row[15] else {}
            entry = EpistemicTraceEntry(
                game_id=row[0],
                tick=row[2],
                quadrant=row[4],
                confidence=row[5],
                certainty=row[6],
                timestamp_ms=row[3],
                agent_id=row[1],
                transition_from=row[7],
                transition_to=row[8],
                transition_reason=row[9],
                algorithm_selected=row[10],
                algorithm_reason=row[11],
                thrashing_score=row[12],
                active_questions=row[13],
                uk_potential=row[14],
                context=context
            )
            entries.append(entry)

        return entries
    except Exception as e:
        logger.error(f"Failed to load traces for {game_id}: {e}")
        return []
