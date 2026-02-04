"""
Catastrophic Fallback - Circuit Breaker for Cognitive Router.

Phase 4.0 Implementation - Cognitive Routing

This module implements the CatastrophicFallback circuit breaker that protects
against:
1. Stuck loops (quadrant oscillation)
2. Empty frontiers (no valid rungs available)
3. Contradiction storms (too many conflicts)
4. Infinite iterations

When triggered, it provides an escape hatch back to static ordering,
logs the event for analysis, and allows the system to recover gracefully.

Usage:
    fallback = CatastrophicFallback()

    # In router main loop:
    fallback.reset()  # At decision start

    fallback.record_quadrant(current_quadrant)
    fallback.record_iteration(iteration_count)

    if contradiction_detected:
        fallback.record_contradiction()

    if not next_rungs:
        fallback.record_empty_frontier()

    should_fallback, failure_type = fallback.should_fallback()
    if should_fallback:
        ordering = fallback.trigger_fallback(...)
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from engines.cognition.blackboard import RumsfeldQuadrant

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class FailureType(Enum):
    """Types of catastrophic failures that trigger fallback."""
    NONE = "none"                       # No failure
    QUADRANT_LOOP = "quadrant_loop"     # Oscillating between quadrants
    EMPTY_FRONTIER = "empty_frontier"   # No valid rungs to execute
    CONTRADICTION_STORM = "contradiction_storm"  # Too many contradictions
    MAX_ITERATIONS = "max_iterations"   # Hit iteration limit
    STUCK_QUADRANT = "stuck_quadrant"   # Too long in one quadrant without progress
    ALGORITHM_FAILURE = "algorithm_failure"  # Algorithm returned invalid result


class FallbackStrategy(Enum):
    """Strategies for fallback ordering."""
    SAFE_MINIMAL = "safe_minimal"       # Minimal safe rungs only
    EXPLORATION = "exploration"         # Exploration-focused ordering
    EXPLOITATION = "exploitation"       # Exploitation-focused ordering
    REPLAY = "replay"                   # Use replay sequence if available


# =============================================================================
# CATASTROPHIC EVENT
# =============================================================================

@dataclass
class CatastrophicEvent:
    """Record of a catastrophic failure for review and learning."""
    failure_type: FailureType
    timestamp: datetime
    game_id: str
    decision_id: int
    iteration_count: int
    quadrant_history: List[str]
    contradiction_count: int
    empty_frontier_count: int
    context_snapshot: Dict[str, Any]

    # Analysis data
    rungs_visited: Set[str] = field(default_factory=set)
    fallback_strategy: Optional[FallbackStrategy] = None
    recovery_successful: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for database storage."""
        return {
            'failure_type': self.failure_type.value,
            'timestamp': self.timestamp.isoformat(),
            'game_id': self.game_id,
            'decision_id': self.decision_id,
            'iteration_count': self.iteration_count,
            'quadrant_history': self.quadrant_history,
            'contradiction_count': self.contradiction_count,
            'empty_frontier_count': self.empty_frontier_count,
            'context_snapshot': self.context_snapshot,
            'rungs_visited': list(self.rungs_visited),
            'fallback_strategy': self.fallback_strategy.value if self.fallback_strategy else None,
            'recovery_successful': self.recovery_successful,
        }


# =============================================================================
# FALLBACK ORDERINGS
# =============================================================================

# Safe minimal ordering - just survey and basic observation
SAFE_MINIMAL_ORDERING = [
    "survey",
    "frame_interpretation",
    "control_tracker",
    "network_wisdom",
    "smart_action_selection",
]

# Exploration-focused ordering
EXPLORATION_ORDERING = [
    "survey",
    "frame_interpretation",
    "control_tracker",
    "hypothesis_generation",
    "theory_gate",
    "exploration_phase",
    "curiosity_drive",
    "network_wisdom",
    "smart_action_selection",
]

# Exploitation-focused ordering
EXPLOITATION_ORDERING = [
    "cached_sequence",
    "winning_sequence_replay",
    "checkpoint_exploitation",
    "network_wisdom",
    "optimization_refinement",
    "smart_action_selection",
    "survey",  # Fallback if no cache
]


# =============================================================================
# THRESHOLDS
# =============================================================================

@dataclass
class FallbackThresholds:
    """Configurable thresholds for triggering fallback."""
    # Maximum consecutive empty frontiers before fallback
    max_empty_frontiers: int = 3

    # Maximum contradictions in one decision
    max_contradictions: int = 5

    # Maximum iterations without progress
    max_iterations: int = 50

    # Maximum quadrant oscillations (A->B->A->B pattern)
    max_quadrant_oscillations: int = 4

    # Maximum time in one quadrant without confidence increase
    max_stuck_ticks: int = 15

    # Minimum confidence progress expected per tick in quadrant
    min_confidence_progress: float = 0.01


DEFAULT_THRESHOLDS = FallbackThresholds()


# =============================================================================
# CATASTROPHIC FALLBACK
# =============================================================================

class CatastrophicFallback:
    """
    Circuit breaker that triggers fallback to static ordering when
    dynamic routing fails catastrophically.

    The fallback monitors for:
    1. Quadrant loops (oscillating between quadrants)
    2. Empty frontiers (no rungs to execute)
    3. Contradiction storms (too many conflicts)
    4. Stuck states (no progress)
    5. Iteration limits (runaway execution)

    When triggered, it:
    1. Logs the failure for later analysis
    2. Selects appropriate fallback strategy
    3. Returns a static ordering to use
    4. Resets monitoring state
    """

    def __init__(
        self,
        thresholds: Optional[FallbackThresholds] = None,
        game_id: str = "",
        decision_id: int = 0,
    ):
        """
        Initialize the fallback circuit breaker.

        Args:
            thresholds: Configurable thresholds (uses defaults if None)
            game_id: Current game identifier for logging
            decision_id: Current decision number for logging
        """
        self.thresholds = thresholds or DEFAULT_THRESHOLDS
        self.game_id = game_id
        self.decision_id = decision_id

        # Counters
        self._contradiction_count = 0
        self._empty_frontier_count = 0
        self._iteration_count = 0

        # Quadrant tracking for loop detection
        self._quadrant_history: deque = deque(maxlen=20)

        # Progress tracking
        self._confidence_at_quadrant_entry: float = 0.0
        self._ticks_in_current_quadrant: int = 0
        self._last_quadrant: Optional[str] = None

        # Visited rungs
        self._visited_rungs: Set[str] = set()

        # Event history
        self._events: List[CatastrophicEvent] = []

        # Fallback state
        self._fallback_triggered = False
        self._current_failure_type: FailureType = FailureType.NONE

    def reset(self, game_id: str = "", decision_id: int = 0) -> None:
        """
        Reset all counters for a new decision.

        Call this at the start of each decision cycle.
        """
        self._contradiction_count = 0
        self._empty_frontier_count = 0
        self._iteration_count = 0
        self._quadrant_history.clear()
        self._confidence_at_quadrant_entry = 0.0
        self._ticks_in_current_quadrant = 0
        self._last_quadrant = None
        self._visited_rungs.clear()
        self._fallback_triggered = False
        self._current_failure_type = FailureType.NONE

        if game_id:
            self.game_id = game_id
        if decision_id:
            self.decision_id = decision_id

    # -------------------------------------------------------------------------
    # RECORDING METHODS
    # -------------------------------------------------------------------------

    def record_quadrant(self, quadrant: str, confidence: float = 0.0) -> None:
        """
        Record current quadrant for loop detection.

        Args:
            quadrant: Current quadrant name (KK, KU, UK, UU)
            confidence: Current max confidence
        """
        self._quadrant_history.append(quadrant)

        if quadrant != self._last_quadrant:
            # Quadrant changed - reset stuck tracking
            self._confidence_at_quadrant_entry = confidence
            self._ticks_in_current_quadrant = 0
            self._last_quadrant = quadrant
        else:
            # Same quadrant - increment stuck counter
            self._ticks_in_current_quadrant += 1

    def record_iteration(self, visited_rung: Optional[str] = None) -> None:
        """
        Record an iteration of the main loop.

        Args:
            visited_rung: Rung visited in this iteration (optional)
        """
        self._iteration_count += 1
        if visited_rung:
            self._visited_rungs.add(visited_rung)

    def record_contradiction(self) -> None:
        """Record a contradiction detection."""
        self._contradiction_count += 1
        logger.debug(f"Contradiction #{self._contradiction_count} recorded")

    def record_empty_frontier(self) -> None:
        """Record an empty frontier condition."""
        self._empty_frontier_count += 1
        logger.debug(f"Empty frontier #{self._empty_frontier_count} recorded")

    def record_algorithm_failure(self, algorithm_name: str, error: str) -> None:
        """Record an algorithm failure."""
        logger.warning(f"Algorithm failure in {algorithm_name}: {error}")
        self._current_failure_type = FailureType.ALGORITHM_FAILURE

    # -------------------------------------------------------------------------
    # DETECTION METHODS
    # -------------------------------------------------------------------------

    def should_fallback(self, current_confidence: float = 0.0) -> Tuple[bool, FailureType]:
        """
        Check if fallback should be triggered.

        Returns:
            Tuple of (should_fallback: bool, failure_type: FailureType)
        """
        if self._fallback_triggered:
            return True, self._current_failure_type

        # Check empty frontiers
        if self._empty_frontier_count >= self.thresholds.max_empty_frontiers:
            self._current_failure_type = FailureType.EMPTY_FRONTIER
            return True, FailureType.EMPTY_FRONTIER

        # Check contradictions
        if self._contradiction_count >= self.thresholds.max_contradictions:
            self._current_failure_type = FailureType.CONTRADICTION_STORM
            return True, FailureType.CONTRADICTION_STORM

        # Check iterations
        if self._iteration_count >= self.thresholds.max_iterations:
            self._current_failure_type = FailureType.MAX_ITERATIONS
            return True, FailureType.MAX_ITERATIONS

        # Check quadrant loop (oscillation pattern)
        if self._detect_quadrant_loop():
            self._current_failure_type = FailureType.QUADRANT_LOOP
            return True, FailureType.QUADRANT_LOOP

        # Check stuck in quadrant
        if self._detect_stuck(current_confidence):
            self._current_failure_type = FailureType.STUCK_QUADRANT
            return True, FailureType.STUCK_QUADRANT

        # Check algorithm failure flag
        if self._current_failure_type == FailureType.ALGORITHM_FAILURE:
            return True, FailureType.ALGORITHM_FAILURE

        return False, FailureType.NONE

    def _detect_quadrant_loop(self) -> bool:
        """
        Detect oscillating quadrant pattern (A->B->A->B->A->B).

        Returns:
            True if oscillation pattern detected
        """
        if len(self._quadrant_history) < self.thresholds.max_quadrant_oscillations * 2:
            return False

        # Get recent history
        recent = list(self._quadrant_history)[-self.thresholds.max_quadrant_oscillations * 2:]

        # Check for A-B-A-B pattern
        if len(set(recent)) == 2:  # Only two unique quadrants
            # Check if it's alternating
            is_alternating = True
            for i in range(len(recent) - 2):
                if recent[i] != recent[i + 2]:  # Should be same every other
                    is_alternating = False
                    break
            if is_alternating:
                logger.warning(f"Quadrant oscillation detected: {recent}")
                return True

        return False

    def _detect_stuck(self, current_confidence: float) -> bool:
        """
        Detect stuck in quadrant without progress.

        Args:
            current_confidence: Current max confidence

        Returns:
            True if stuck detected
        """
        if self._ticks_in_current_quadrant < self.thresholds.max_stuck_ticks:
            return False

        # Check if confidence has improved
        expected_progress = (
            self._ticks_in_current_quadrant *
            self.thresholds.min_confidence_progress
        )
        actual_progress = current_confidence - self._confidence_at_quadrant_entry

        if actual_progress < expected_progress:
            logger.warning(
                f"Stuck in quadrant {self._last_quadrant}: "
                f"{self._ticks_in_current_quadrant} ticks, "
                f"progress {actual_progress:.3f} < expected {expected_progress:.3f}"
            )
            return True

        return False

    # -------------------------------------------------------------------------
    # FALLBACK EXECUTION
    # -------------------------------------------------------------------------

    def trigger_fallback(
        self,
        context_snapshot: Dict[str, Any],
        has_replay_sequence: bool = False,
        current_confidence: float = 0.0,
    ) -> List[str]:
        """
        Trigger fallback and return static ordering.

        Args:
            context_snapshot: Current context state for logging
            has_replay_sequence: Whether a replay sequence is available
            current_confidence: Current max confidence

        Returns:
            List of rung names to execute in order
        """
        self._fallback_triggered = True

        # Create event record
        event = CatastrophicEvent(
            failure_type=self._current_failure_type,
            timestamp=datetime.now(),
            game_id=self.game_id,
            decision_id=self.decision_id,
            iteration_count=self._iteration_count,
            quadrant_history=list(self._quadrant_history),
            contradiction_count=self._contradiction_count,
            empty_frontier_count=self._empty_frontier_count,
            context_snapshot=context_snapshot,
            rungs_visited=self._visited_rungs.copy(),
        )

        # Select strategy
        strategy = self._select_fallback_strategy(
            has_replay_sequence,
            current_confidence
        )
        event.fallback_strategy = strategy

        # Get ordering
        ordering = self._get_ordering_for_strategy(strategy)

        # Filter out already visited rungs that failed
        # (keep visited if they might succeed with different context)
        if self._current_failure_type == FailureType.CONTRADICTION_STORM:
            # After contradictions, skip rungs involved in conflicts
            ordering = [r for r in ordering if r not in self._visited_rungs]

        # Ensure we have at least some rungs
        if not ordering:
            ordering = SAFE_MINIMAL_ORDERING.copy()

        # Store event
        self._events.append(event)

        # Log
        logger.warning(
            f"[CATASTROPHIC FALLBACK] {self._current_failure_type.value} - "
            f"Strategy: {strategy.value}, Ordering: {ordering[:5]}..."
        )

        return ordering

    def _select_fallback_strategy(
        self,
        has_replay_sequence: bool,
        current_confidence: float,
    ) -> FallbackStrategy:
        """
        Select appropriate fallback strategy based on failure type.

        Args:
            has_replay_sequence: Whether replay is available
            current_confidence: Current max confidence

        Returns:
            Fallback strategy to use
        """
        failure = self._current_failure_type

        # Replay if available and not a contradiction storm
        if has_replay_sequence and failure != FailureType.CONTRADICTION_STORM:
            return FallbackStrategy.REPLAY

        # Exploitation if we have some confidence
        if current_confidence > 0.5 and failure != FailureType.STUCK_QUADRANT:
            return FallbackStrategy.EXPLOITATION

        # Exploration if we're stuck or in early stages
        if failure in (FailureType.STUCK_QUADRANT, FailureType.QUADRANT_LOOP):
            return FallbackStrategy.EXPLORATION

        # Safe minimal for serious failures
        return FallbackStrategy.SAFE_MINIMAL

    def _get_ordering_for_strategy(self, strategy: FallbackStrategy) -> List[str]:
        """Get ordering for the selected strategy."""
        if strategy == FallbackStrategy.SAFE_MINIMAL:
            return SAFE_MINIMAL_ORDERING.copy()
        elif strategy == FallbackStrategy.EXPLORATION:
            return EXPLORATION_ORDERING.copy()
        elif strategy == FallbackStrategy.EXPLOITATION:
            return EXPLOITATION_ORDERING.copy()
        elif strategy == FallbackStrategy.REPLAY:
            # Caller should handle replay sequence
            return EXPLOITATION_ORDERING.copy()
        else:
            return SAFE_MINIMAL_ORDERING.copy()

    # -------------------------------------------------------------------------
    # ANALYSIS METHODS
    # -------------------------------------------------------------------------

    def get_events(self) -> List[CatastrophicEvent]:
        """Get all catastrophic events from this session."""
        return self._events.copy()

    def get_last_event(self) -> Optional[CatastrophicEvent]:
        """Get the most recent catastrophic event."""
        return self._events[-1] if self._events else None

    def mark_recovery_successful(self) -> None:
        """Mark that recovery was successful (for learning)."""
        if self._events:
            self._events[-1].recovery_successful = True

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about fallback triggers."""
        if not self._events:
            return {
                'total_triggers': 0,
                'recovery_rate': 0.0,
                'by_type': {},
            }

        by_type: Dict[str, int] = {}
        successful = 0

        for event in self._events:
            type_name = event.failure_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1
            if event.recovery_successful:
                successful += 1

        return {
            'total_triggers': len(self._events),
            'recovery_rate': successful / len(self._events),
            'by_type': by_type,
        }

    @property
    def is_triggered(self) -> bool:
        """Check if fallback has been triggered."""
        return self._fallback_triggered

    @property
    def contradiction_count(self) -> int:
        """Current contradiction count."""
        return self._contradiction_count

    @property
    def empty_frontier_count(self) -> int:
        """Current empty frontier count."""
        return self._empty_frontier_count

    @property
    def iteration_count(self) -> int:
        """Current iteration count."""
        return self._iteration_count
