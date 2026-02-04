"""
Epistemic Tracker - State Machine for Cognitive Routing.

This module implements the EpistemicTracker which is the core of Part 3's insight:
The Rumsfeld matrix is a STATE MACHINE where transitions drive algorithm selection.

Phase 1.5.2 of cognitive_routing_implementation_plan.md

Key responsibilities:
1. Track current epistemic state (KK/KU/UK/UU quadrants)
2. Detect TRANSITIONS between quadrants
3. Maintain history for pattern detection
4. Provide transition events that drive algorithm switching
"""

import copy
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

from engines.cognition.blackboard import KnownFact, Question, RumsfeldQuadrant
from engines.cognition.epistemic_state import (
    QUADRANT_DEFAULT_ALGORITHMS,
    EpistemicSnapshot,
    EpistemicState,
    EpistemicTransition,
    TransitionResponse,
)

if TYPE_CHECKING:
    from engines.cognition.blackboard import Blackboard

logger = logging.getLogger(__name__)


# =============================================================================
# RUNG RESULT PROTOCOL
# =============================================================================

@dataclass
class RungResult:
    """
    Result from executing a rung.

    This is the interface that rungs use to communicate results to the
    epistemic tracker. Key fields:
    - slot_name: Which blackboard slot was affected
    - value: The value written
    - confidence: How confident the rung is in this result
    - raises_questions: New questions discovered (KU)
    - surprise_level: How unexpected this result was (affects UU)
    """
    rung_name: str
    slot_name: Optional[str] = None
    value: Any = None
    confidence: float = 0.0
    raises_questions: List[Question] = field(default_factory=list)
    answers_questions: List[str] = field(default_factory=list)  # Question IDs answered
    surprise_level: float = 0.0  # 0.0 = expected, 1.0 = completely unexpected
    contradiction_detected: bool = False
    contradiction_with: Optional[str] = None  # Slot name that contradicts

    @property
    def is_confident(self) -> bool:
        """Is this a high-confidence result?"""
        return self.confidence > 0.8

    @property
    def is_uncertain(self) -> bool:
        """Is this a low-confidence result?"""
        return self.confidence < 0.4

    @property
    def raised_questions(self) -> bool:
        """Did this result raise new questions?"""
        return len(self.raises_questions) > 0

    @property
    def answered_questions(self) -> bool:
        """Did this result answer questions?"""
        return len(self.answers_questions) > 0


# =============================================================================
# EPISTEMIC TRACKER
# =============================================================================

class EpistemicTracker:
    """
    Tracks epistemic state and detects TRANSITIONS.

    This is the core of Part 3's insight: Algorithm selection happens on
    TRANSITIONS, not on every decision. The tracker:

    1. Maintains current EpistemicState
    2. Updates state after each rung execution
    3. Detects when quadrant changes (transition)
    4. Returns transitions that tell the router to switch algorithms

    Usage:
        tracker = EpistemicTracker()

        # After each rung execution:
        transitions = tracker.update_from_rung_result(
            rung_name="survey",
            result=rung_result,
            blackboard=blackboard,
            all_rungs=all_rung_names,
            visited_rungs=visited_rung_names
        )

        if transitions:
            # Switch algorithm based on transition
            response = get_algorithm_for_transition(transitions[-1])
    """

    # Confidence threshold for KK classification
    KK_CONFIDENCE_THRESHOLD = 0.8

    # Confidence threshold for answering questions
    ANSWER_CONFIDENCE_THRESHOLD = 0.6

    # Surprise threshold for increasing UU
    SURPRISE_THRESHOLD = 0.7

    # Learning rate for UU decay
    UU_DECAY_RATE = 0.9

    # Maximum history size
    MAX_HISTORY_SIZE = 100

    def __init__(self):
        """Initialize the epistemic tracker."""
        self.current_state = EpistemicState()
        self.history: List[EpistemicSnapshot] = []
        self.transitions: List[EpistemicTransition] = []
        self._last_quadrant = RumsfeldQuadrant.UU
        self._tick = 0

    def reset(self) -> None:
        """Reset tracker for a new decision/game."""
        self.current_state = EpistemicState()
        self.history.clear()
        self.transitions.clear()
        self._last_quadrant = RumsfeldQuadrant.UU
        self._tick = 0

    def update_from_rung_result(
        self,
        rung_name: str,
        result: RungResult,
        blackboard: 'Blackboard',
        all_rungs: Set[str],
        visited_rungs: Set[str]
    ) -> List[EpistemicTransition]:
        """
        Update epistemic state after rung execution.

        This is the main update method. It:
        1. Updates KK (known knowns) based on confidence
        2. Updates KU (known unknowns) - answers old questions, adds new
        3. Updates UK (unknown knowns) - untapped rungs with cached knowledge
        4. Updates UU (unknown unknowns) - exploration estimate
        5. Detects quadrant transitions

        Args:
            rung_name: Name of the rung that just executed
            result: The RungResult from the rung
            blackboard: Current blackboard state
            all_rungs: Set of all available rung names
            visited_rungs: Set of rungs already visited this decision

        Returns:
            List of transitions that occurred (usually 0 or 1)
        """
        self._tick += 1
        transitions: List[EpistemicTransition] = []

        # Snapshot current state
        old_quadrant = self.current_state.primary_quadrant

        # === Update KK (Known Knowns) ===
        self._update_kk(rung_name, result)

        # === Update KU (Known Unknowns) ===
        questions_answered, questions_raised = self._update_ku(rung_name, result)

        # === Update UK (Unknown Knowns) ===
        self._update_uk(all_rungs, visited_rungs, blackboard)

        # === Update UU (Unknown Unknowns) ===
        self._update_uu(result)

        # === Update timestamp ===
        action_count = blackboard.slot('action_count') if blackboard else self._tick
        self.current_state.timestamp = action_count if action_count else self._tick

        # === Detect Transitions ===
        new_quadrant = self.current_state.compute_primary_quadrant()
        self.current_state.primary_quadrant = new_quadrant

        if new_quadrant != old_quadrant:
            transition = EpistemicTransition(
                from_quadrant=old_quadrant,
                to_quadrant=new_quadrant,
                trigger_rung=rung_name,
                trigger_reason=self._infer_transition_reason(
                    old_quadrant, new_quadrant, result
                ),
                timestamp=self.current_state.timestamp,
                trigger_slot=result.slot_name,
                trigger_confidence=result.confidence,
                questions_raised=[q.question_id for q in questions_raised],
                questions_answered=questions_answered,
            )
            transitions.append(transition)
            self.transitions.append(transition)
            self._last_quadrant = new_quadrant

            logger.debug(
                f"Epistemic transition: {transition.transition_key} "
                f"triggered by {rung_name}"
            )

        # Save history (pruned)
        self._save_history()

        return transitions

    def _update_kk(self, rung_name: str, result: RungResult) -> None:
        """Update KK (Known Knowns) based on result confidence."""
        if result.confidence > self.KK_CONFIDENCE_THRESHOLD and result.slot_name:
            self.current_state.known_knowns[result.slot_name] = KnownFact(
                slot_name=result.slot_name,
                value=result.value,
                confidence=result.confidence,
                source_rung=rung_name,
                verified_at=self.current_state.timestamp
            )

        # Recalculate aggregate KK confidence
        if self.current_state.known_knowns:
            total_confidence = sum(
                f.confidence for f in self.current_state.known_knowns.values()
            )
            self.current_state.kk_confidence = (
                total_confidence / len(self.current_state.known_knowns)
            )
        else:
            self.current_state.kk_confidence = 0.0

    def _update_ku(
        self,
        rung_name: str,
        result: RungResult
    ) -> tuple[List[str], List[Question]]:
        """
        Update KU (Known Unknowns).

        Returns:
            Tuple of (answered_question_ids, raised_questions)
        """
        answered: List[str] = []
        raised: List[Question] = []

        # Check if rung answered existing questions
        for q_id, question in list(self.current_state.known_unknowns.items()):
            if rung_name in question.answerable_by:
                if result.confidence > self.ANSWER_CONFIDENCE_THRESHOLD:
                    # Question answered
                    question.mark_answered(result.confidence)
                    answered.append(q_id)
                    del self.current_state.known_unknowns[q_id]

        # Also check explicit answers from result
        for q_id in result.answers_questions:
            if q_id in self.current_state.known_unknowns:
                self.current_state.known_unknowns[q_id].mark_answered(result.confidence)
                answered.append(q_id)
                del self.current_state.known_unknowns[q_id]

        # Add new questions raised by this rung
        for question in result.raises_questions:
            self.current_state.known_unknowns[question.question_id] = question
            raised.append(question)

        # Update KU urgency based on question count and priorities
        if self.current_state.known_unknowns:
            total_priority = sum(
                q.priority for q in self.current_state.known_unknowns.values()
            )
            self.current_state.ku_urgency = min(
                1.0, total_priority / max(len(self.current_state.known_unknowns), 1)
            )
        else:
            self.current_state.ku_urgency = 0.0

        return answered, raised

    def _update_uk(
        self,
        all_rungs: Set[str],
        visited_rungs: Set[str],
        blackboard: Optional['Blackboard']
    ) -> None:
        """Update UK (Unknown Knowns) - untapped cached/network knowledge."""
        # UK = rungs not yet visited that have cached knowledge
        unvisited = all_rungs - visited_rungs

        # Filter to only those with cached/network knowledge
        self.current_state.unknown_knowns = {
            r for r in unvisited
            if self._has_cached_knowledge(r, blackboard)
        }

        # Update UK potential
        if all_rungs:
            self.current_state.uk_potential = (
                len(self.current_state.unknown_knowns) / len(all_rungs)
            )
        else:
            self.current_state.uk_potential = 0.0

    def _update_uu(self, result: RungResult) -> None:
        """Update UU (Unknown Unknowns) - exploration estimate."""
        # Learning reduces UU (we're filling in the map)
        if result.confidence > 0.5:
            self.current_state.uu_estimate *= self.UU_DECAY_RATE

        # Surprises increase UU (we found something unexpected)
        if result.surprise_level > self.SURPRISE_THRESHOLD:
            self.current_state.uu_estimate = min(
                1.0,
                self.current_state.uu_estimate + 0.2
            )

        # Contradictions significantly increase UU
        if result.contradiction_detected:
            self.current_state.uu_estimate = min(
                1.0,
                self.current_state.uu_estimate + 0.3
            )

    def _has_cached_knowledge(
        self,
        rung_name: str,
        blackboard: Optional['Blackboard']
    ) -> bool:
        """Check if rung has cached/network knowledge to offer."""
        if blackboard is None:
            return False

        # Check if network wisdom cache has data for this rung
        network_cache = blackboard.slot('network_wisdom_cache')
        if network_cache and rung_name in network_cache:
            return True

        # Check if it's a network/retrieval rung
        retrieval_prefixes = ('network_', 'cached_', 'winning_sequence')
        if any(rung_name.startswith(p) for p in retrieval_prefixes):
            return True

        return False

    def _infer_transition_reason(
        self,
        from_q: RumsfeldQuadrant,
        to_q: RumsfeldQuadrant,
        result: RungResult
    ) -> str:
        """Infer human-readable reason for transition."""
        key = (from_q, to_q)

        if key == (RumsfeldQuadrant.UU, RumsfeldQuadrant.KU):
            return f"Found question: {result.raises_questions[0].description if result.raises_questions else 'unknown'}"
        elif key == (RumsfeldQuadrant.KU, RumsfeldQuadrant.KK):
            return f"Answered question with confidence {result.confidence:.2f}"
        elif key == (RumsfeldQuadrant.UK, RumsfeldQuadrant.KK):
            return f"Retrieved cached knowledge from {result.rung_name}"
        elif key == (RumsfeldQuadrant.KK, RumsfeldQuadrant.KU):
            return f"Mild contradiction - confidence dropped"
        elif key == (RumsfeldQuadrant.KK, RumsfeldQuadrant.UU):
            return f"Severe contradiction with {result.contradiction_with or 'previous belief'}"
        elif key == (RumsfeldQuadrant.UU, RumsfeldQuadrant.UK):
            return f"Discovered untapped cached knowledge"
        else:
            return f"Quadrant shift from {from_q.name} to {to_q.name}"

    def _save_history(self) -> None:
        """Save current state to history (with pruning)."""
        snapshot = EpistemicSnapshot.from_state(self.current_state)
        self.history.append(snapshot)

        # Prune old history
        if len(self.history) > self.MAX_HISTORY_SIZE:
            self.history = self.history[-self.MAX_HISTORY_SIZE:]

    def get_transition_pattern(self, last_n: int = 5) -> str:
        """
        Get string pattern of recent transitions for pattern matching.

        Example: "UU->KU->KK" means we went from exploration to question to exploit.
        """
        if not self.transitions:
            return self._last_quadrant.name

        if len(self.transitions) < last_n:
            transitions = self.transitions
        else:
            transitions = self.transitions[-last_n:]

        return "->".join(t.to_quadrant.name for t in transitions)

    def get_state_duration(self, quadrant: RumsfeldQuadrant) -> int:
        """How many ticks have we been in the given quadrant?"""
        count = 0
        for snapshot in reversed(self.history):
            if snapshot.quadrant == quadrant:
                count += 1
            else:
                break
        return count

    def is_stagnating(self, threshold: int = 5) -> bool:
        """Are we stuck in the same quadrant for too long?"""
        if not self.history:
            return False
        current = self.current_state.primary_quadrant
        return self.get_state_duration(current) >= threshold

    def get_current_algorithm(self) -> str:
        """Get the default algorithm for the current quadrant."""
        return QUADRANT_DEFAULT_ALGORITHMS.get(
            self.current_state.primary_quadrant,
            "InformationMaximizingSearch"
        )

    def __repr__(self) -> str:
        return (
            f"EpistemicTracker(quadrant={self.current_state.primary_quadrant.name}, "
            f"transitions={len(self.transitions)}, tick={self._tick})"
        )
