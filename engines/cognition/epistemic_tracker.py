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

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

from engines.cognition.blackboard import KnownFact, Question, RumsfeldQuadrant
from engines.cognition.epistemic_state import (
    QUADRANT_DEFAULT_ALGORITHMS,
    EpistemicSnapshot,
    EpistemicState,
    EpistemicTransition,
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
    # NOTE: Most rungs output confidence=0.6, threshold must be at or below that
    KK_CONFIDENCE_THRESHOLD = 0.55

    # Confidence threshold for answering questions
    # Legacy rungs typically output confidence=0.6. Set below that
    # so successful rung results can answer auto-generated questions.
    ANSWER_CONFIDENCE_THRESHOLD = 0.4

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
        self._no_change_streak: int = 0  # Phase 0.2: consecutive no-frame-change actions

    def reset(self) -> None:
        """Soft reset for a new decision within same game.

        Preserves accumulated knowledge so learning carries across decisions:
        - known_knowns: Facts we've established (which rungs produce actions)
        - kk_confidence: Aggregate confidence in our knowledge
        - uu_estimate: Exploration decay (prevents permanent UU)
        - known_unknowns: Open questions (enables KU transitions)

        Only resets transient state (UK potential, history, transitions).
        """
        # Preserve cross-decision learning
        preserved_kk = self.current_state.known_knowns
        preserved_kk_conf = self.current_state.kk_confidence
        preserved_uu = self.current_state.uu_estimate
        preserved_ku = self.current_state.known_unknowns
        preserved_ku_urgency = self.current_state.ku_urgency

        self.current_state = EpistemicState()

        # Restore accumulated knowledge
        self.current_state.known_knowns = preserved_kk
        self.current_state.kk_confidence = preserved_kk_conf
        self.current_state.uu_estimate = preserved_uu
        self.current_state.known_unknowns = preserved_ku
        self.current_state.ku_urgency = preserved_ku_urgency

        # CRITICAL: Recompute primary_quadrant from preserved state.
        # Without this, primary_quadrant defaults to UU (from EpistemicState())
        # even when the preserved uu_estimate and kk_confidence say KK.
        self.current_state.primary_quadrant = self.current_state.compute_primary_quadrant()

        self.history.clear()
        self.transitions.clear()
        self._last_quadrant = self.current_state.primary_quadrant
        self._tick = 0
        self._no_change_streak = 0

    def hard_reset(self) -> None:
        """Full reset for a completely new game (no knowledge preserved)."""
        self.current_state = EpistemicState()
        self.history.clear()
        self.transitions.clear()
        self._last_quadrant = RumsfeldQuadrant.UU
        self._tick = 0
        self._no_change_streak = 0

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
                trigger_slot=getattr(result, 'slot_name', None),
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
        slot_name = getattr(result, 'slot_name', None)
        value = getattr(result, 'value', None)
        if result.confidence > self.KK_CONFIDENCE_THRESHOLD and slot_name:
            self.current_state.known_knowns[slot_name] = KnownFact(
                slot_name=slot_name,
                value=value,
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
        # Use getattr for robustness against legacy RungResult objects
        for q_id in getattr(result, 'answers_questions', []):
            if q_id in self.current_state.known_unknowns:
                self.current_state.known_unknowns[q_id].mark_answered(result.confidence)
                answered.append(q_id)
                del self.current_state.known_unknowns[q_id]

        # Add new questions raised by this rung
        for question in getattr(result, 'raises_questions', []):
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
        """Update UU (Unknown Unknowns) - exploration estimate.

        UU represents how much territory remains unexplored. It decreases as
        we explore (visit rungs) and increases when we encounter genuine surprises.

        Key fix: Every rung visit reduces UU slightly (baseline decay 0.98x)
        because visiting a rung IS exploration even if the rung produced nothing.
        Without this, UU only decays on confident results and 49/50 rungs
        produce nothing, keeping UU permanently high.
        """
        # Baseline decay: every visited rung reduces the unknown frontier
        # 0.98^50 iterations = 0.364, so UU drops from 0.8 to ~0.29 over
        # a full 50-iteration search, even without any confident results.
        BASELINE_DECAY = 0.98
        self.current_state.uu_estimate *= BASELINE_DECAY

        # Confident results decay UU faster (we found something real)
        if result.confidence > 0.5:
            self.current_state.uu_estimate *= self.UU_DECAY_RATE

        # Surprises increase UU (we found something unexpected)
        # Use getattr for robustness against legacy RungResult objects
        surprise_level = getattr(result, 'surprise_level', 0.0)
        if surprise_level > self.SURPRISE_THRESHOLD:
            self.current_state.uu_estimate = min(
                1.0,
                self.current_state.uu_estimate + 0.2
            )

        # Contradictions significantly increase UU
        contradiction_detected = getattr(result, 'contradiction_detected', False)
        if contradiction_detected:
            self.current_state.uu_estimate = min(
                1.0,
                self.current_state.uu_estimate + 0.3
            )

    # =================================================================
    # Phase 0.2: Evidence-based epistemic updates from action feedback
    # =================================================================

    def update_from_action_feedback(
        self,
        _action_name: str,
        frame_changed: bool,
        score_changed: bool = False,
    ) -> None:
        """Update epistemic state from real action outcomes.

        Called by the game loop after each action. This closes the gap
        between confidence-threshold KU->KK transitions and evidence-based
        transitions: if the world doesn't respond to our actions, our
        "knowledge" is suspect.

        Args:
            _action_name: The action that was executed (e.g. 'ACTION6').
            frame_changed: Whether the frame pixels changed after the action.
            score_changed: Whether the score changed after the action.
        """
        if frame_changed:
            # World responded -- evidence confirms our knowledge
            self._no_change_streak = 0
            boost = 1.1 if score_changed else 1.05
            self.current_state.kk_confidence = min(
                1.0, self.current_state.kk_confidence * boost
            )
            # Score change also reduces UU (strong evidence of understanding)
            if score_changed:
                self.current_state.uu_estimate *= 0.9
        else:
            # World did NOT respond -- our knowledge may be wrong
            self._no_change_streak += 1
            self.current_state.kk_confidence *= 0.95

            # After 5+ consecutive no-change actions, aggressively decay
            if self._no_change_streak >= 5:
                self.current_state.kk_confidence *= 0.8
                # We clearly don't understand this world yet
                self.current_state.uu_estimate = min(
                    1.0, self.current_state.uu_estimate + 0.05
                )

        # Recompute primary quadrant so downstream readers see the update
        self.current_state.primary_quadrant = (
            self.current_state.compute_primary_quadrant()
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

        # Check if it's a rung that ACTUALLY has data in the database.
        # Previously, any rung with a retrieval-sounding prefix was assumed
        # to have cached knowledge, inflating unknown_knowns to ~12 rungs
        # and uk_potential to ~0.24. This caused permanent UK quadrant lock
        # (UK always exceeded threshold 0.03/2 unknowns).
        # Now only return True for rungs with ACTUAL blackboard data.
        retrieval_prefixes = (
            'network_',           # network_wisdom, network_sharing, etc.
            'cached_',            # cached sequences
            'winning_sequence',   # winning sequence replay
        )
        if any(rung_name.startswith(p) for p in retrieval_prefixes):
            # Only count if the blackboard actually has relevant data
            slot = blackboard.slot(rung_name)
            if slot is not None:
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
        # Use getattr for robustness against legacy RungResult objects
        raises_questions = getattr(result, 'raises_questions', [])
        rung_name = getattr(result, 'rung_name', 'unknown')
        contradiction_with = getattr(result, 'contradiction_with', None)

        if key == (RumsfeldQuadrant.UU, RumsfeldQuadrant.KU):
            return f"Found question: {raises_questions[0].description if raises_questions else 'unknown'}"
        elif key == (RumsfeldQuadrant.KU, RumsfeldQuadrant.KK):
            return f"Answered question with confidence {result.confidence:.2f}"
        elif key == (RumsfeldQuadrant.UK, RumsfeldQuadrant.KK):
            return f"Retrieved cached knowledge from {rung_name}"
        elif key == (RumsfeldQuadrant.KK, RumsfeldQuadrant.KU):
            return f"Mild contradiction - confidence dropped"
        elif key == (RumsfeldQuadrant.KK, RumsfeldQuadrant.UU):
            return f"Severe contradiction with {contradiction_with or 'previous belief'}"
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
