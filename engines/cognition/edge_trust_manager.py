"""
Graph Evolution Manager - Phase 6.2.

Manages long-term evolution of the cognitive graph through:
1. Cumulative edge trust - Weights accumulate across games
2. Edge weight updates - Exponential moving average based on outcomes
3. Trust-based modifiers - High trust = lower cost, higher info_gain
4. Negative reputation penalty - Contradictions hurt more than neutral

Key insight from Part 4: The graph after 1000 games should look
fundamentally different than at start. Every traversal is both
a decision AND a training signal.

Usage:
    manager = GraphEvolutionManager(db_interface)

    # Record traversal outcome
    manager.record_traversal(
        source="survey",
        target="control_tracker",
        outcome=TraversalOutcome(led_to_success=True, confidence_delta=0.15)
    )

    # Get trust-based edge modifier
    modifier = manager.get_edge_modifier("survey", "control_tracker")
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class TraversalOutcome:
    """Outcome of traversing an edge."""
    led_to_success: bool = False      # Did this lead to a good outcome?
    led_to_contradiction: bool = False  # Did this lead to a contradiction?
    confidence_delta: float = 0.0     # Change in confidence from this traversal
    ticks_to_outcome: int = 0         # How many ticks until outcome was known

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'led_to_success': self.led_to_success,
            'led_to_contradiction': self.led_to_contradiction,
            'confidence_delta': self.confidence_delta,
            'ticks_to_outcome': self.ticks_to_outcome,
        }


@dataclass
class EdgeTrustRecord:
    """
    Cumulative trust record for an edge across all games.

    Part 4 insight: Edge weights accumulate across games, not just per-decision.
    """
    edge_id: str                          # source->target
    traversal_count: int = 0              # How many times traversed
    success_count: int = 0                # How many times led to good outcome
    failure_count: int = 0                # How many times led to contradiction
    cumulative_confidence_gain: float = 0.0  # Sum of confidence deltas
    last_traversed: int = 0               # Generation number

    # EMA-smoothed info_gain (Phase 6.2)
    base_info_gain: float = 0.5           # Current smoothed info_gain

    @property
    def trust_score(self) -> float:
        """Calculate trust score from history."""
        if self.traversal_count == 0:
            return 0.5  # Neutral for untested edges

        success_rate = self.success_count / self.traversal_count
        avg_gain = self.cumulative_confidence_gain / self.traversal_count

        # Trust = weighted combination of success rate and gain
        return 0.6 * success_rate + 0.4 * min(1.0, max(0.0, avg_gain))

    @property
    def is_crystallized(self) -> bool:
        """Has this edge been traversed enough to be considered proven?"""
        return self.traversal_count >= 20 and self.trust_score > 0.8

    @property
    def is_toxic(self) -> bool:
        """Has this edge shown consistently bad outcomes?"""
        if self.traversal_count < 5:
            return False
        failure_rate = self.failure_count / self.traversal_count
        return failure_rate > 0.6

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'edge_id': self.edge_id,
            'traversal_count': self.traversal_count,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'cumulative_confidence_gain': self.cumulative_confidence_gain,
            'last_traversed': self.last_traversed,
            'base_info_gain': self.base_info_gain,
            'trust_score': self.trust_score,
            'is_crystallized': self.is_crystallized,
            'is_toxic': self.is_toxic,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EdgeTrustRecord':
        """Create from dictionary."""
        return cls(
            edge_id=data['edge_id'],
            traversal_count=data.get('traversal_count', 0),
            success_count=data.get('success_count', 0),
            failure_count=data.get('failure_count', 0),
            cumulative_confidence_gain=data.get('cumulative_confidence_gain', 0.0),
            last_traversed=data.get('last_traversed', 0),
            base_info_gain=data.get('base_info_gain', 0.5),
        )


@dataclass
class EdgeEvolutionConfig:
    """Configuration for edge evolution."""
    # EMA parameters
    ema_alpha: float = 0.1              # Smoothing factor for info_gain updates

    # Trust thresholds
    crystallization_threshold: int = 20  # Traversals needed for crystallization
    crystallization_trust: float = 0.8   # Trust score needed for crystallization
    toxic_threshold: float = 0.6         # Failure rate for toxic classification

    # Penalties
    contradiction_penalty: float = 0.3   # Extra penalty for contradictions

    # Modifiers
    min_modifier: float = 0.5           # Minimum edge modifier (toxic edges)
    max_modifier: float = 1.5           # Maximum edge modifier (crystallized edges)
    neutral_modifier: float = 1.0       # Modifier for untested edges


# =============================================================================
# GRAPH EVOLUTION MANAGER
# =============================================================================

class GraphEvolutionManager:
    """
    Manages long-term evolution of the cognitive graph.

    Key responsibilities:
    1. Track edge traversals and outcomes
    2. Update edge trust scores based on history
    3. Provide trust-based modifiers for graph search
    4. Persist evolution state to database
    """

    def __init__(
        self,
        db_interface: Optional[Any] = None,
        config: Optional[EdgeEvolutionConfig] = None
    ):
        """Initialize graph evolution manager."""
        self.db = db_interface
        self.config = config or EdgeEvolutionConfig()

        # Edge trust records (edge_id -> EdgeTrustRecord)
        self.edge_trust: Dict[str, EdgeTrustRecord] = {}

        # Current generation for tracking recency
        self._current_generation: int = 0

        # Statistics
        self._total_traversals = 0
        self._crystallized_count = 0
        self._toxic_count = 0

        # Load from database if available
        if self.db:
            self._load_from_db()

        logger.info("[GRAPH-EVOLUTION] Manager initialized")

    # -------------------------------------------------------------------------
    # EDGE CREATION
    # -------------------------------------------------------------------------

    def _make_edge_id(self, source: str, target: str) -> str:
        """Create edge ID from source and target."""
        return f"{source}->{target}"

    def _get_or_create_record(self, edge_id: str) -> EdgeTrustRecord:
        """Get or create an edge trust record."""
        if edge_id not in self.edge_trust:
            self.edge_trust[edge_id] = EdgeTrustRecord(edge_id=edge_id)
        return self.edge_trust[edge_id]

    # -------------------------------------------------------------------------
    # TRAVERSAL RECORDING
    # -------------------------------------------------------------------------

    def record_traversal(
        self,
        source: str,
        target: str,
        outcome: TraversalOutcome
    ) -> None:
        """
        Record a single edge traversal and its outcome.

        This is the primary learning signal for graph evolution.
        """
        edge_id = self._make_edge_id(source, target)
        record = self._get_or_create_record(edge_id)

        # Update counts
        record.traversal_count += 1
        record.last_traversed = self._current_generation
        record.cumulative_confidence_gain += outcome.confidence_delta

        if outcome.led_to_success:
            record.success_count += 1

        if outcome.led_to_contradiction:
            record.failure_count += 1
            # Apply negative reputation penalty (Part 4 insight)
            # KK->UU (contradiction) is worse than fresh start
            record.cumulative_confidence_gain -= self.config.contradiction_penalty

        # Update EMA-smoothed info_gain
        outcome_score = 1.0 if outcome.led_to_success else (0.0 if outcome.led_to_contradiction else 0.5)
        record.base_info_gain = (
            self.config.ema_alpha * outcome_score +
            (1 - self.config.ema_alpha) * record.base_info_gain
        )

        # Update statistics
        self._total_traversals += 1
        self._update_statistics()

        # Persist to database
        if self.db:
            self._save_edge(record)

        logger.debug(
            f"[GRAPH-EVOLUTION] Recorded traversal {edge_id}: "
            f"trust={record.trust_score:.2f}, traversals={record.traversal_count}"
        )

    def record_path(
        self,
        path: List[str],
        outcomes: List[TraversalOutcome]
    ) -> None:
        """Record traversals for an entire path."""
        if len(path) < 2:
            return

        for i, outcome in enumerate(outcomes):
            if i + 1 < len(path):
                self.record_traversal(path[i], path[i + 1], outcome)

    # -------------------------------------------------------------------------
    # EDGE WEIGHT UPDATES (Phase 6.2)
    # -------------------------------------------------------------------------

    def update_edge_weight(
        self,
        source: str,
        target: str,
        outcome: float
    ) -> None:
        """
        Update edge info_gain based on observed outcome.

        Uses exponential moving average for smooth adaptation.

        Args:
            source: Source rung name
            target: Target rung name
            outcome: Outcome score (0.0 = bad, 1.0 = good)
        """
        edge_id = self._make_edge_id(source, target)
        record = self._get_or_create_record(edge_id)

        # Exponential moving average update
        alpha = self.config.ema_alpha
        record.base_info_gain = alpha * outcome + (1 - alpha) * record.base_info_gain

        if self.db:
            self._save_edge(record)

    # -------------------------------------------------------------------------
    # TRUST-BASED MODIFIERS
    # -------------------------------------------------------------------------

    def get_edge_modifier(self, source: str, target: str) -> float:
        """
        Get trust-based modifier for edge cost/info_gain.

        - High trust = lower cost / higher info_gain (modifier > 1.0)
        - Low trust = higher cost / lower info_gain (modifier < 1.0)
        - Neutral = no modification (modifier = 1.0)

        Returns:
            Modifier in range [0.5, 1.5]
        """
        edge_id = self._make_edge_id(source, target)
        record = self.edge_trust.get(edge_id)

        if not record:
            return self.config.neutral_modifier  # No history, neutral

        # High trust = higher modifier (lower cost in A* terms)
        # Low trust = lower modifier (higher cost)
        # Trust score is in [0, 1], so modifier is in [0.5, 1.5]
        return self.config.min_modifier + record.trust_score

    def get_edge_info_gain(self, source: str, target: str) -> float:
        """Get the current info_gain estimate for an edge."""
        edge_id = self._make_edge_id(source, target)
        record = self.edge_trust.get(edge_id)

        if not record:
            return 0.5  # Default neutral info_gain

        return record.base_info_gain

    def get_edge_trust(self, source: str, target: str) -> float:
        """Get trust score for an edge."""
        edge_id = self._make_edge_id(source, target)
        record = self.edge_trust.get(edge_id)

        if not record:
            return 0.5  # Neutral

        return record.trust_score

    # -------------------------------------------------------------------------
    # CRYSTALLIZATION & TOXICITY
    # -------------------------------------------------------------------------

    def is_edge_crystallized(self, source: str, target: str) -> bool:
        """Check if an edge is crystallized (proven reliable)."""
        edge_id = self._make_edge_id(source, target)
        record = self.edge_trust.get(edge_id)
        return record.is_crystallized if record else False

    def is_edge_toxic(self, source: str, target: str) -> bool:
        """Check if an edge is toxic (consistently bad)."""
        edge_id = self._make_edge_id(source, target)
        record = self.edge_trust.get(edge_id)
        return record.is_toxic if record else False

    def get_crystallized_edges(self) -> List[str]:
        """Get list of all crystallized edge IDs."""
        return [
            edge_id for edge_id, record in self.edge_trust.items()
            if record.is_crystallized
        ]

    def get_toxic_edges(self) -> List[str]:
        """Get list of all toxic edge IDs."""
        return [
            edge_id for edge_id, record in self.edge_trust.items()
            if record.is_toxic
        ]

    # -------------------------------------------------------------------------
    # GENERATION MANAGEMENT
    # -------------------------------------------------------------------------

    def advance_generation(self) -> None:
        """Advance to next generation."""
        self._current_generation += 1
        self._update_statistics()
        logger.debug(f"[GRAPH-EVOLUTION] Advanced to generation {self._current_generation}")

    @property
    def current_generation(self) -> int:
        """Get current generation number."""
        return self._current_generation

    # -------------------------------------------------------------------------
    # STATISTICS
    # -------------------------------------------------------------------------

    def _update_statistics(self) -> None:
        """Update statistics counts."""
        self._crystallized_count = sum(
            1 for r in self.edge_trust.values() if r.is_crystallized
        )
        self._toxic_count = sum(
            1 for r in self.edge_trust.values() if r.is_toxic
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get evolution statistics."""
        if not self.edge_trust:
            return {
                'total_edges': 0,
                'total_traversals': 0,
                'crystallized_count': 0,
                'toxic_count': 0,
                'avg_trust': 0.0,
                'current_generation': self._current_generation,
            }

        trust_scores = [r.trust_score for r in self.edge_trust.values()]

        return {
            'total_edges': len(self.edge_trust),
            'total_traversals': self._total_traversals,
            'crystallized_count': self._crystallized_count,
            'toxic_count': self._toxic_count,
            'avg_trust': sum(trust_scores) / len(trust_scores),
            'min_trust': min(trust_scores),
            'max_trust': max(trust_scores),
            'current_generation': self._current_generation,
        }

    def get_edge_record(self, source: str, target: str) -> Optional[EdgeTrustRecord]:
        """Get the trust record for an edge."""
        edge_id = self._make_edge_id(source, target)
        return self.edge_trust.get(edge_id)

    def get_all_edges(self) -> List[EdgeTrustRecord]:
        """Get all edge trust records."""
        return list(self.edge_trust.values())

    # -------------------------------------------------------------------------
    # DATABASE PERSISTENCE
    # -------------------------------------------------------------------------

    def _load_from_db(self) -> None:
        """Load edge trust records from database."""
        if not self.db:
            return

        try:
            rows = self.db.execute("""
                SELECT edge_id, traversal_count, success_count, failure_count,
                       cumulative_confidence_gain, last_traversed, base_info_gain
                FROM edge_trust_records
            """).fetchall()

            for row in rows:
                record = EdgeTrustRecord(
                    edge_id=row[0],
                    traversal_count=row[1],
                    success_count=row[2],
                    failure_count=row[3],
                    cumulative_confidence_gain=row[4],
                    last_traversed=row[5],
                    base_info_gain=row[6],
                )
                self.edge_trust[row[0]] = record

            # Get current generation
            gen_row = self.db.execute("""
                SELECT MAX(last_traversed) FROM edge_trust_records
            """).fetchone()
            if gen_row and gen_row[0]:
                self._current_generation = gen_row[0]

            self._update_statistics()
            logger.info(f"[GRAPH-EVOLUTION] Loaded {len(self.edge_trust)} edges from database")

        except Exception as e:
            logger.warning(f"[GRAPH-EVOLUTION] Failed to load from database: {e}")

    def _save_edge(self, record: EdgeTrustRecord) -> None:
        """Save an edge trust record to database."""
        if not self.db:
            return

        try:
            self.db.execute("""
                INSERT OR REPLACE INTO edge_trust_records (
                    edge_id, traversal_count, success_count, failure_count,
                    cumulative_confidence_gain, last_traversed, base_info_gain
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                record.edge_id,
                record.traversal_count,
                record.success_count,
                record.failure_count,
                record.cumulative_confidence_gain,
                record.last_traversed,
                record.base_info_gain,
            ))
        except Exception as e:
            logger.error(f"[GRAPH-EVOLUTION] Failed to save edge: {e}")

    def save_all(self) -> None:
        """Save all edge trust records to database."""
        if not self.db:
            return

        for record in self.edge_trust.values():
            self._save_edge(record)

        logger.info(f"[GRAPH-EVOLUTION] Saved {len(self.edge_trust)} edges to database")


# =============================================================================
# DATABASE SCHEMA
# =============================================================================

EDGE_TRUST_SCHEMA = """
CREATE TABLE IF NOT EXISTS edge_trust_records (
    edge_id TEXT PRIMARY KEY,
    traversal_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    cumulative_confidence_gain REAL DEFAULT 0.0,
    last_traversed INTEGER DEFAULT 0,
    base_info_gain REAL DEFAULT 0.5
);

CREATE INDEX IF NOT EXISTS idx_edge_trust_traversal ON edge_trust_records(traversal_count);
CREATE INDEX IF NOT EXISTS idx_edge_trust_generation ON edge_trust_records(last_traversed);
"""
