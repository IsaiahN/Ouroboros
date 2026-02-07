"""
Epistemic State Data Structures for Cognitive Routing.

This module defines the core data structures for the Rumsfeld state machine
that drives algorithm selection in the cognitive router.

Phase 1.5.1 of cognitive_routing_implementation_plan.md

The Rumsfeld matrix is a STATE MACHINE where transitions drive algorithm selection:
    - KK (Known Knowns): High confidence, exploit aggressively
    - KU (Known Unknowns): Specific questions, targeted search
    - UK (Unknown Knowns): Untapped cached/network knowledge, retrieval
    - UU (Unknown Unknowns): Novel territory, information-maximizing exploration
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

# Import shared types from blackboard (avoid duplication)
from engines.cognition.blackboard import KnownFact, Question, RumsfeldQuadrant

# =============================================================================
# EPISTEMIC STATE
# =============================================================================

@dataclass
class EpistemicState:
    """
    Complete epistemic state of the agent at a moment.

    This is the STATE in the Rumsfeld state machine. It captures what the agent
    knows, what questions it has, what untapped knowledge exists, and how much
    territory remains unexplored.

    The primary_quadrant determines which search algorithm to use.
    """
    # KK: What we know with high confidence
    known_knowns: Dict[str, KnownFact] = field(default_factory=dict)
    kk_confidence: float = 0.0  # Aggregate confidence in KK

    # KU: Specific questions we know we need answered
    known_unknowns: Dict[str, Question] = field(default_factory=dict)
    ku_urgency: float = 0.0  # How urgently we need answers (0.0 to 1.0)

    # UK: Cached/network knowledge not yet accessed (rung names)
    unknown_knowns: Set[str] = field(default_factory=set)
    uk_potential: float = 0.0  # Estimated value of untapped knowledge (0.0 to 1.0)

    # UU: Estimate of unexplored territory
    uu_estimate: float = 0.8  # 0.0 = fully known, 1.0 = totally novel (start high)

    # Primary quadrant determines base algorithm
    primary_quadrant: RumsfeldQuadrant = RumsfeldQuadrant.UU

    # Timestamp for state tracking
    timestamp: int = 0  # Action number when state was computed

    def compute_primary_quadrant(self) -> RumsfeldQuadrant:
        """
        Determine which quadrant dominates current state.

        Priority order:
        - KK first when strong (exploit established high-confidence knowledge)
        - UK (retrieve untapped cached knowledge when KK not established)
        - KU (targeted search for specific questions)
        - UU (explore when nothing specific known)
        - KK fallback (any accumulated knowledge)

        Previous bug: UK had highest priority with trivially low thresholds
        (uk_potential > 0.03, 2+ unknown_knowns). Since ~61 rungs exist and
        many have retrieval prefixes, UK ALWAYS triggered, making KK
        unreachable. Agents would go KK→UK on every decision.

        Fix: KK takes priority when confidence is strong (> 0.5) or when
        substantial knowledge has accumulated (3+ known facts). This lets
        the greedy_best_first algorithm exploit proven knowledge instead of
        always falling back to retrieval search.

        Returns:
            The dominant quadrant that should drive algorithm selection
        """
        # KK: Exploit established knowledge with strong confidence.
        # When we KNOW things confidently, use greedy_best_first to commit
        # quickly rather than retrieving more knowledge (UK) or exploring (UU).
        if self.kk_confidence > 0.5:
            return RumsfeldQuadrant.KK
        if self.known_knowns and len(self.known_knowns) >= 3:
            return RumsfeldQuadrant.KK

        # UK: Retrieve untapped cached/network knowledge
        # Thresholds raised from 0.03/2 to 0.15/5 because ~12 retrieval-
        # prefixed rungs always exceeded the old thresholds, locking every
        # decision into UK and making KK unreachable.
        if self.uk_potential > 0.15 and len(self.unknown_knowns) >= 5:
            return RumsfeldQuadrant.UK
        # KU: Even ONE open question with moderate urgency triggers targeted search
        if len(self.known_unknowns) >= 1 and self.ku_urgency > 0.2:
            return RumsfeldQuadrant.KU
        if self.uu_estimate > 0.6:
            return RumsfeldQuadrant.UU
        # If we have ANY accumulated knowledge, exploit it rather than
        # defaulting back to UU exploration (breaks the UU→UU loop)
        if self.known_knowns:
            return RumsfeldQuadrant.KK
        return RumsfeldQuadrant.UU  # True default: no knowledge at all

    def update_primary_quadrant(self) -> RumsfeldQuadrant:
        """Compute and update the primary quadrant. Returns the new quadrant."""
        self.primary_quadrant = self.compute_primary_quadrant()
        return self.primary_quadrant

    @property
    def kk_count(self) -> int:
        """Number of known facts."""
        return len(self.known_knowns)

    @property
    def ku_count(self) -> int:
        """Number of open questions."""
        return len(self.known_unknowns)

    @property
    def uk_count(self) -> int:
        """Number of untapped knowledge sources."""
        return len(self.unknown_knowns)

    def summary(self) -> str:
        """Return a brief summary of the epistemic state."""
        return (
            f"EpistemicState("
            f"quadrant={self.primary_quadrant.name}, "
            f"KK={self.kk_count}@{self.kk_confidence:.2f}, "
            f"KU={self.ku_count}@{self.ku_urgency:.2f}, "
            f"UK={self.uk_count}@{self.uk_potential:.2f}, "
            f"UU={self.uu_estimate:.2f})"
        )


# =============================================================================
# EPISTEMIC TRANSITION
# =============================================================================

@dataclass
class EpistemicTransition:
    """
    A transition between epistemic quadrants.

    Transitions are the core insight of Part 3: Algorithm selection happens
    on TRANSITIONS, not on every decision. When the quadrant changes, we
    switch algorithms.

    Key transitions:
    - UU -> KU: Found a specific question (focus search)
    - KU -> KK: Answered the question (exploit)
    - KK -> KU: Mild contradiction (backtrack and target)
    - KK -> UU: Severe contradiction (reset with exclusions)
    - UU -> UK: Realized we have cached knowledge (retrieve)
    """
    from_quadrant: RumsfeldQuadrant
    to_quadrant: RumsfeldQuadrant
    trigger_rung: str  # Which rung caused the transition
    trigger_reason: str  # Human-readable reason
    timestamp: int  # Action number when transition occurred
    created_at: datetime = field(default_factory=datetime.now)

    # Optional context about what triggered the transition
    trigger_slot: Optional[str] = None  # Slot that changed
    trigger_confidence: Optional[float] = None  # Confidence that triggered
    questions_raised: List[str] = field(default_factory=list)  # New questions
    questions_answered: List[str] = field(default_factory=list)  # Answered questions

    @property
    def is_progression(self) -> bool:
        """Is this a forward progression (learning/discovery)?"""
        # Forward: UU->KU, KU->KK, UK->KK
        forward_transitions = {
            (RumsfeldQuadrant.UU, RumsfeldQuadrant.KU),
            (RumsfeldQuadrant.KU, RumsfeldQuadrant.KK),
            (RumsfeldQuadrant.UK, RumsfeldQuadrant.KK),
            (RumsfeldQuadrant.UU, RumsfeldQuadrant.UK),
        }
        return (self.from_quadrant, self.to_quadrant) in forward_transitions

    @property
    def is_regression(self) -> bool:
        """Is this a regression (contradiction/failure)?"""
        # Regression: KK->KU, KK->UU
        regression_transitions = {
            (RumsfeldQuadrant.KK, RumsfeldQuadrant.KU),
            (RumsfeldQuadrant.KK, RumsfeldQuadrant.UU),
        }
        return (self.from_quadrant, self.to_quadrant) in regression_transitions

    @property
    def is_stagnation(self) -> bool:
        """Is this staying in the same quadrant (stagnation)?"""
        return self.from_quadrant == self.to_quadrant

    @property
    def transition_key(self) -> str:
        """Get a string key for this transition type (e.g., 'UU->KU')."""
        return f"{self.from_quadrant.name}->{self.to_quadrant.name}"

    def __repr__(self) -> str:
        return (
            f"EpistemicTransition({self.transition_key}, "
            f"trigger={self.trigger_rung}, t={self.timestamp})"
        )


# =============================================================================
# TRANSITION RESPONSE
# =============================================================================

@dataclass
class TransitionResponse:
    """
    Response to an epistemic transition.

    When a transition is detected, this tells the router:
    1. Which algorithm to switch to
    2. What action to take (focus, exploit, reset, etc.)
    3. Any parameters for the new algorithm
    """
    algorithm: str  # Name of algorithm to use
    action: str     # Action type: focus, exploit, reset, backtrack, etc.
    description: str  # Human-readable description
    params: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def default(cls) -> 'TransitionResponse':
        """Default response for unknown transitions."""
        return cls(
            algorithm="LandmarkAStar",
            action="continue",
            description="Unknown transition - use general search",
            params={}
        )


# =============================================================================
# EPISTEMIC SNAPSHOT (for history tracking)
# =============================================================================

@dataclass
class EpistemicSnapshot:
    """
    A snapshot of epistemic state for history tracking.

    This is a lighter-weight copy of EpistemicState suitable for
    storing in history without deep-copying all the data.
    """
    quadrant: RumsfeldQuadrant
    kk_confidence: float
    ku_urgency: float
    ku_count: int
    uk_potential: float
    uk_count: int
    uu_estimate: float
    timestamp: int

    @classmethod
    def from_state(cls, state: EpistemicState) -> 'EpistemicSnapshot':
        """Create a snapshot from a full epistemic state."""
        return cls(
            quadrant=state.primary_quadrant,
            kk_confidence=state.kk_confidence,
            ku_urgency=state.ku_urgency,
            ku_count=len(state.known_unknowns),
            uk_potential=state.uk_potential,
            uk_count=len(state.unknown_knowns),
            uu_estimate=state.uu_estimate,
            timestamp=state.timestamp
        )


# =============================================================================
# CONSTANTS
# =============================================================================

# Quadrant algorithm mappings (default algorithms per quadrant)
QUADRANT_DEFAULT_ALGORITHMS = {
    RumsfeldQuadrant.KK: "GreedyExploitation",
    RumsfeldQuadrant.KU: "TargetedQuestionSearch",
    RumsfeldQuadrant.UK: "RetrievalSearch",
    RumsfeldQuadrant.UU: "InformationMaximizingSearch",
}

# Transition types that indicate problems
REGRESSION_TRANSITIONS = {
    (RumsfeldQuadrant.KK, RumsfeldQuadrant.KU),  # Mild contradiction
    (RumsfeldQuadrant.KK, RumsfeldQuadrant.UU),  # Severe contradiction
    (RumsfeldQuadrant.KU, RumsfeldQuadrant.UU),  # Question led to confusion
    (RumsfeldQuadrant.UK, RumsfeldQuadrant.UU),  # Cached knowledge contradicted
}

# Transition types that indicate progress
PROGRESSION_TRANSITIONS = {
    (RumsfeldQuadrant.UU, RumsfeldQuadrant.KU),  # Found a question
    (RumsfeldQuadrant.KU, RumsfeldQuadrant.KK),  # Answered a question
    (RumsfeldQuadrant.UK, RumsfeldQuadrant.KK),  # Retrieved knowledge
    (RumsfeldQuadrant.UU, RumsfeldQuadrant.UK),  # Found cached knowledge
    (RumsfeldQuadrant.UU, RumsfeldQuadrant.KK),  # Exploration yielded knowledge
    (RumsfeldQuadrant.KK, RumsfeldQuadrant.UK),  # Found untapped knowledge while exploiting
    (RumsfeldQuadrant.UK, RumsfeldQuadrant.KU),  # Retrieved knowledge raised questions
}

# Stagnation transitions (staying in same quadrant too long)
STAGNATION_TRANSITIONS = {
    (RumsfeldQuadrant.UU, RumsfeldQuadrant.UU),  # Stuck exploring
    (RumsfeldQuadrant.KU, RumsfeldQuadrant.KU),  # Question unanswerable
}
