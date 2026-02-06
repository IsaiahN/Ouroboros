"""
Hysteresis Manager for Epistemic State Machine.

This module prevents quadrant thrashing by implementing:
1. Confirmation counts - require multiple signals before transition
2. Cooldowns - after leaving quadrant, can't return immediately
3. Signal decay - old signals fade over time

Phase 1.6.1 of cognitive_routing_implementation_plan.md

Problem: Without hysteresis, the system might oscillate rapidly:
    KK->KU->KK->KU->KK... (ping-pong)

Solution: TransitionGate requires confirmations before allowing transitions,
and HysteresisManager tracks signals with decay and cooldowns.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from engines.cognition.blackboard import RumsfeldQuadrant

logger = logging.getLogger(__name__)


# =============================================================================
# TRANSITION GATE CONFIGURATION
# =============================================================================

@dataclass
class TransitionGate:
    """
    Gate that prevents premature transitions.

    Configuration for how many confirmations are needed and cooldown periods.
    """
    # Confirmation counts needed before allowing transition
    # Higher values = more stability, slower response
    CONFIRMATIONS_REQUIRED: Dict[Tuple[RumsfeldQuadrant, RumsfeldQuadrant], int] = field(
        default_factory=lambda: {
            # Easy transitions (low confirmation)
            (RumsfeldQuadrant.UU, RumsfeldQuadrant.KU): 1,  # Questions are cheap
            (RumsfeldQuadrant.UK, RumsfeldQuadrant.KK): 1,  # Retrieval is fast
            (RumsfeldQuadrant.UU, RumsfeldQuadrant.UK): 1,  # Retrieval is cheap
            (RumsfeldQuadrant.UU, RumsfeldQuadrant.KK): 1,  # Forward progress - allow immediately

            # Moderate transitions
            (RumsfeldQuadrant.KU, RumsfeldQuadrant.KK): 2,  # Need solid answer
            (RumsfeldQuadrant.KK, RumsfeldQuadrant.KU): 2,  # Don't abandon hastily
            (RumsfeldQuadrant.KU, RumsfeldQuadrant.UU): 2,  # Broadening search
            (RumsfeldQuadrant.UK, RumsfeldQuadrant.KU): 2,  # Retrieval raised questions
            (RumsfeldQuadrant.KK, RumsfeldQuadrant.UK): 2,  # Found untapped knowledge

            # Hard transitions (high confirmation)
            (RumsfeldQuadrant.KK, RumsfeldQuadrant.UU): 3,  # Nuclear option - severe contradiction
            (RumsfeldQuadrant.UK, RumsfeldQuadrant.UU): 3,  # Cached knowledge contradicted
        }
    )

    # Cooldown: After leaving quadrant, can't return for N ticks
    COOLDOWN_TICKS: Dict[RumsfeldQuadrant, int] = field(
        default_factory=lambda: {
            RumsfeldQuadrant.KK: 3,  # Prevent KK->KU->KK ping-pong
            RumsfeldQuadrant.KU: 2,  # Moderate cooldown
            RumsfeldQuadrant.UK: 1,  # Short cooldown
            RumsfeldQuadrant.UU: 0,  # Always allow return to exploration
        }
    )

    # Signal decay: Signals older than this many ticks are discarded
    SIGNAL_DECAY_TICKS: int = 10

    # Default confirmation if transition not in table
    DEFAULT_CONFIRMATIONS: int = 2


# Global default gate configuration
DEFAULT_GATE = TransitionGate()


# =============================================================================
# HYSTERESIS MANAGER
# =============================================================================

class HysteresisManager:
    """
    Manages transition stability with confirmations, cooldowns, and decay.

    The manager acts as a filter between raw transition signals (from
    EpistemicTracker) and actual quadrant changes. It ensures:

    1. Multiple confirming signals before transition fires
    2. Cooldown periods prevent rapid oscillation
    3. Old signals decay to prevent stale data from triggering

    Usage:
        manager = HysteresisManager()

        # When epistemic tracker suggests a transition
        should_transition = manager.record_signal(
            from_q=RumsfeldQuadrant.KK,
            to_q=RumsfeldQuadrant.KU
        )

        if should_transition:
            # Actually perform the transition
            tracker.force_transition(...)

        # After each tick
        manager.tick()
    """

    def __init__(self, gate: Optional[TransitionGate] = None):
        """
        Initialize hysteresis manager.

        Args:
            gate: TransitionGate configuration. Uses defaults if not provided.
        """
        self.gate = gate or DEFAULT_GATE

        # Pending signals: (from, to) -> list of tick timestamps
        self.pending_signals: Dict[
            Tuple[RumsfeldQuadrant, RumsfeldQuadrant],
            List[int]
        ] = defaultdict(list)

        # Cooldowns: quadrant -> tick when cooldown expires
        self.cooldowns: Dict[RumsfeldQuadrant, int] = {}

        # Current tick counter
        self.current_tick: int = 0

        # Statistics
        self._signals_received: int = 0
        self._signals_filtered: int = 0
        self._transitions_allowed: int = 0

    def reset(self) -> None:
        """Reset manager for a new decision/game."""
        self.pending_signals.clear()
        self.cooldowns.clear()
        self.current_tick = 0
        self._signals_received = 0
        self._signals_filtered = 0
        self._transitions_allowed = 0

    def tick(self) -> None:
        """Advance time by one tick. Call after each rung execution."""
        self.current_tick += 1
        self._decay_old_signals()

    def record_signal(
        self,
        from_q: RumsfeldQuadrant,
        to_q: RumsfeldQuadrant
    ) -> bool:
        """
        Record a signal suggesting transition.

        Args:
            from_q: Current quadrant
            to_q: Proposed destination quadrant

        Returns:
            True if transition should fire (enough confirmations, not on cooldown)
        """
        self._signals_received += 1
        key = (from_q, to_q)

        # Check if destination is on cooldown
        if self._is_on_cooldown(to_q):
            self._signals_filtered += 1
            logger.debug(
                f"Transition {from_q.name}->{to_q.name} blocked: "
                f"{to_q.name} on cooldown until tick {self.cooldowns[to_q]}"
            )
            return False

        # Record signal with current timestamp
        self.pending_signals[key].append(self.current_tick)

        # Apply signal decay (prune old signals)
        self._decay_signals_for_key(key)

        # Check if we have enough confirmations
        required = self.gate.CONFIRMATIONS_REQUIRED.get(
            key,
            self.gate.DEFAULT_CONFIRMATIONS
        )

        if len(self.pending_signals[key]) >= required:
            # Transition approved!
            self._transitions_allowed += 1

            # Clear signals for this transition
            self.pending_signals[key] = []

            # Set cooldown for origin quadrant
            cooldown_ticks = self.gate.COOLDOWN_TICKS.get(from_q, 2)
            if cooldown_ticks > 0:
                self.cooldowns[from_q] = self.current_tick + cooldown_ticks

            logger.debug(
                f"Transition {from_q.name}->{to_q.name} APPROVED "
                f"(confirmations={required})"
            )
            return True

        # Not enough confirmations yet
        logger.debug(
            f"Transition {from_q.name}->{to_q.name} pending: "
            f"{len(self.pending_signals[key])}/{required} confirmations"
        )
        return False

    def _is_on_cooldown(self, quadrant: RumsfeldQuadrant) -> bool:
        """Check if a quadrant is on cooldown."""
        if quadrant not in self.cooldowns:
            return False
        return self.current_tick < self.cooldowns[quadrant]

    def _decay_signals_for_key(
        self,
        key: Tuple[RumsfeldQuadrant, RumsfeldQuadrant]
    ) -> None:
        """Remove old signals for a specific transition."""
        decay_threshold = self.current_tick - self.gate.SIGNAL_DECAY_TICKS
        self.pending_signals[key] = [
            t for t in self.pending_signals[key]
            if t > decay_threshold
        ]

    def _decay_old_signals(self) -> None:
        """Remove all old signals (called on tick)."""
        decay_threshold = self.current_tick - self.gate.SIGNAL_DECAY_TICKS
        for key in list(self.pending_signals.keys()):
            self.pending_signals[key] = [
                t for t in self.pending_signals[key]
                if t > decay_threshold
            ]
            # Clean up empty entries
            if not self.pending_signals[key]:
                del self.pending_signals[key]

    def get_pending_count(
        self,
        from_q: RumsfeldQuadrant,
        to_q: RumsfeldQuadrant
    ) -> int:
        """Get number of pending signals for a transition."""
        key = (from_q, to_q)
        return len(self.pending_signals.get(key, []))

    def get_cooldown_remaining(self, quadrant: RumsfeldQuadrant) -> int:
        """Get ticks remaining on cooldown for a quadrant (0 if not on cooldown)."""
        if quadrant not in self.cooldowns:
            return 0
        remaining = self.cooldowns[quadrant] - self.current_tick
        return max(0, remaining)

    def force_clear_cooldown(self, quadrant: RumsfeldQuadrant) -> None:
        """Force clear cooldown for a quadrant (emergency override)."""
        if quadrant in self.cooldowns:
            del self.cooldowns[quadrant]
            logger.warning(f"Force cleared cooldown for {quadrant.name}")

    def get_thrashing_score(self) -> float:
        """
        Calculate thrashing score based on filtered vs allowed transitions.

        Returns:
            0.0 (stable) to 1.0 (highly unstable/thrashing)
        """
        total = self._signals_received
        if total == 0:
            return 0.0

        # High filter rate = thrashing
        return self._signals_filtered / total

    def get_statistics(self) -> Dict:
        """Get manager statistics for debugging/monitoring."""
        return {
            "current_tick": self.current_tick,
            "signals_received": self._signals_received,
            "signals_filtered": self._signals_filtered,
            "transitions_allowed": self._transitions_allowed,
            "thrashing_score": self.get_thrashing_score(),
            "active_cooldowns": {
                q.name: self.get_cooldown_remaining(q)
                for q in self.cooldowns
                if self.get_cooldown_remaining(q) > 0
            },
            "pending_signals": {
                f"{k[0].name}->{k[1].name}": len(v)
                for k, v in self.pending_signals.items()
            }
        }

    def __repr__(self) -> str:
        return (
            f"HysteresisManager(tick={self.current_tick}, "
            f"pending={len(self.pending_signals)}, "
            f"cooldowns={len([c for c in self.cooldowns.values() if c > self.current_tick])})"
        )
