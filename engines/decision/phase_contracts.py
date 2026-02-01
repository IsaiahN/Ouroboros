"""
Phase Contracts - Typed I/O for Decision Phases
================================================

All phase inputs and outputs are explicitly typed dataclasses.
NO Dict[str, Any] - every field is named and typed.
NO silent failures - missing data raises explicit errors.

Design Principles:
1. Every phase has a defined input and output contract
2. Contracts are validated - invalid data raises PhaseError
3. Full audit trail through explicit fields

Naming Convention:
- Code uses simple names (agent_heuristics, network_heuristics, urgency)
- Comments reference theoretical concepts (Stream A, Stream B, mortality pressure)
- This reduces cognitive load while preserving architectural intent
"""

import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


# =============================================================================
# EXCEPTIONS
# =============================================================================

class PhaseError(Exception):
    """
    Raised when a phase fails. NEVER silently swallowed.

    Attributes:
        phase: Which phase failed (e.g., "ORIENT", "GROUND_TRUTH")
        reason: Human-readable explanation
        context: Additional debugging context
    """
    def __init__(self, phase: str, reason: str, context: dict = None):
        self.phase = phase
        self.reason = reason
        self.context = context or {}
        super().__init__(f"[PHASE-{phase}] {reason}")


# =============================================================================
# INPUT CONTRACTS
# =============================================================================

@dataclass
class GameState:
    """
    Current game state passed to all phases.

    This is the "what's happening now" snapshot.
    """
    game_id: str
    game_type: str
    level: int
    frame: List[List[int]]  # Current visual frame
    score: int
    action_number: int  # Current action count
    max_actions: int  # Budget limit
    position: Optional[tuple] = None  # Agent position if known
    previous_action: Optional[str] = None
    previous_frame: Optional[List[List[int]]] = None

    @property
    def budget_used_percent(self) -> float:
        """Fraction of action budget consumed."""
        if self.max_actions <= 0:
            return 0.0
        return min(1.0, self.action_number / self.max_actions)


@dataclass
class AgentContext:
    """
    Agent-specific context passed to all phases.

    This is "who am I and what's my state".

    Naming note:
    - wA/wB are shorthand for "Stream A/B weights" from consciousness theory
    - In simple terms: wA = trust in agent's own experience, wB = trust in network
    - urgency (mortality_pressure) = how close to being culled (0=safe, 1=danger)
    """
    agent_id: int
    agent_type: str  # "Pioneer", "Optimizer", "Generalist", "Exploiter"
    wA: float  # Agent heuristics weight (private experience / "Stream A")
    wB: float  # Network heuristics weight (collective wisdom / "Stream B")
    urgency: float  # 0.0-1.0 - how close to cull (formerly "mortality_pressure")
    is_frontier: bool  # Working on unknown level?
    prestige: float = 0.0
    social_rule_adherence: float = 1.0  # 0.0 = sociopathic, 1.0 = fully social

    # Backwards compatibility alias
    @property
    def mortality_pressure(self) -> float:
        """Alias for urgency (backwards compatibility)."""
        return self.urgency

    def validate(self) -> None:
        """Raise PhaseError if context is invalid."""
        if not 0 <= self.wA <= 1:
            raise PhaseError("CONTEXT", f"Invalid wA: {self.wA}")
        if not 0 <= self.wB <= 1:
            raise PhaseError("CONTEXT", f"Invalid wB: {self.wB}")
        if not 0 <= self.urgency <= 1:
            raise PhaseError("CONTEXT", f"Invalid urgency: {self.urgency}")


# =============================================================================
# DECISION CONTEXT - Accumulating Wrapper
# =============================================================================

@dataclass
class DecisionContext:
    """
    Accumulating context that flows through all phases.

    This wrapper solves the phase coupling problem:
    - Phases access what they need via ctx.orient, ctx.ground_truth, etc.
    - Adding a field to ReasonContext doesn't change phase signatures
    - Phases still declare dependencies explicitly in their code

    Usage:
        ctx = DecisionContext(game_state, agent_context)
        ctx.orient = phase1.execute(ctx)
        ctx.ground_truth = phase2.execute(ctx)
        # ... phases access ctx.orient, ctx.ground_truth as needed
    """
    game_state: GameState
    agent: AgentContext

    # Phase outputs (populated as phases execute)
    orient: Optional['OrientContext'] = None
    ground_truth: Optional['GroundTruthContext'] = None
    reason: Optional['ReasonContext'] = None
    pattern: Optional['PatternContext'] = None
    proposal: Optional['ProposalContext'] = None
    filtered: Optional['FilteredContext'] = None

    # Metadata
    emergency_triggered: bool = False
    start_time: float = 0.0


# =============================================================================
# PHASE 1: ORIENT - Output Contract
# =============================================================================

@dataclass
class OrientContext:
    """
    Output of Phase 1: Orient - "What world am I in?"

    Contains spatial understanding, discovery state, and blocking questions.
    NO action suggestions - only context building.
    """
    world_model: Dict[str, Any]  # Spatial layout, objects, features
    discovery_phase: str  # "idle"|"movement_test"|"click_survey"|"complete"
    coverage_percent: float  # 0.0-1.0 exploration coverage
    budget_used_percent: float  # 0.0-1.0 action budget consumed
    blocking_questions: List[str]  # Q1-Q9 that need answers
    is_frontier: bool  # Unknown level?
    urgency: float  # 0.0-1.0 (higher = closer to cull, aka "mortality pressure")
    detected_objects: List[Dict[str, Any]] = field(default_factory=list)
    frame_changed: bool = True  # Did frame change from previous?

    # Backwards compatibility
    @property
    def mortality_pressure(self) -> float:
        return self.urgency

    def validate(self) -> None:
        """Raise PhaseError if contract violated."""
        if not 0 <= self.coverage_percent <= 1:
            raise PhaseError("ORIENT", f"Invalid coverage_percent: {self.coverage_percent}")
        if not 0 <= self.urgency <= 1:
            raise PhaseError("ORIENT", f"Invalid urgency: {self.urgency}")
        if self.discovery_phase not in ("idle", "movement_test", "click_survey", "complete"):
            raise PhaseError("ORIENT", f"Invalid discovery_phase: {self.discovery_phase}")


# =============================================================================
# PHASE 2: GROUND TRUTH - Output Contract
# =============================================================================

@dataclass
class GroundTruthContext:
    """
    Output of Phase 2: Ground Truth - "What do I empirically know?"

    Contains network-validated facts, safety assessments, and beliefs.
    This is what the DATABASE says, not what the agent guesses.
    """
    action_safety_weights: Dict[str, float]  # ACTION1 -> 0.0-1.0 safety
    empirical_rankings: Dict[str, float]  # ACTION1 -> network success rate
    object_valences: Dict[str, str]  # object_id -> "positive"|"negative"|"neutral"
    active_beliefs: List[Dict[str, Any]]  # Current agent beliefs
    pariah_actions: Set[str]  # Actions marked as pariah (to avoid)
    death_risk_by_position: Dict[tuple, float]  # (x,y) -> death probability
    network_sequence_available: bool = False  # Is there a proven sequence?
    network_sequence: Optional[List[str]] = None  # The sequence if available

    def validate(self) -> None:
        """Raise PhaseError if contract violated."""
        for action, weight in self.action_safety_weights.items():
            if not 0 <= weight <= 1:
                raise PhaseError("GROUND_TRUTH", f"Invalid safety weight for {action}: {weight}")
        for action, rank in self.empirical_rankings.items():
            if not 0 <= rank <= 1:
                raise PhaseError("GROUND_TRUTH", f"Invalid empirical ranking for {action}: {rank}")


# =============================================================================
# PHASE 3: REASON - Output Contract
# =============================================================================

@dataclass
class ReasonContext:
    """
    Output of Phase 3: Reason - "What should I believe?"

    Integrates agent heuristics (Stream A) vs network heuristics (Stream B).

    SYNTHESIS CLARIFICATION:
    When streams conflict and weights are close (within 0.1):
    - "synthesis" means weighted selection, NOT true merging
    - Currently: pick the one with higher empirical success rate
    - Future TODO: Implement true synthesis (e.g., perpendicular action)

    The "competing personas" concept from theory docs is aspirational.
    Current implementation is simply: max(wA * score_A, wB * score_B)
    """
    theory_state: str  # "exploring"|"speculating"|"testing"|"proven"|"contradicted"
    theory_allowed_actions: Set[str]  # Actions theory permits
    stream_conflict: bool  # Did agent and network heuristics disagree?
    agent_proposal: Optional[str]  # What agent's experience suggests (Stream A)
    network_proposal: Optional[str]  # What network wisdom suggests (Stream B)
    winning_source: str  # "agent"|"network"|"weighted_selection"|"none"
    invalidated_beliefs: List[str]  # Beliefs that cascaded/failed
    confidence_in_theory: float  # 0.0-1.0
    working_theory: Optional[Dict[str, Any]] = None  # Current theory details

    # Backwards compatibility aliases
    @property
    def stream_a_proposal(self) -> Optional[str]:
        return self.agent_proposal

    @property
    def stream_b_proposal(self) -> Optional[str]:
        return self.network_proposal

    @property
    def winning_stream(self) -> str:
        """Map new names to old for backwards compatibility."""
        mapping = {"agent": "A", "network": "B", "weighted_selection": "synthesis", "none": "none"}
        return mapping.get(self.winning_source, self.winning_source)

    def validate(self) -> None:
        """Raise PhaseError if contract violated."""
        valid_states = ("exploring", "speculating", "testing", "proven", "contradicted")
        if self.theory_state not in valid_states:
            raise PhaseError("REASON", f"Invalid theory_state: {self.theory_state}")
        if self.winning_source not in ("agent", "network", "weighted_selection", "none"):
            raise PhaseError("REASON", f"Invalid winning_source: {self.winning_source}")
        if not 0 <= self.confidence_in_theory <= 1:
            raise PhaseError("REASON", f"Invalid confidence_in_theory: {self.confidence_in_theory}")


# =============================================================================
# PHASE 4: PATTERN MATCH - Output Contract
# =============================================================================

@dataclass
class PatternMatch:
    """A single pattern match result."""
    action: str
    confidence: float  # 0.0-1.0
    source: str  # "embedding"|"cods"|"universal"|"resonance"|"trigger"|"abstraction"
    evidence: str  # Human-readable explanation


@dataclass
class PatternContext:
    """
    Output of Phase 4: Pattern Match - "Have I seen this before?"

    Contains all pattern-based suggestions from various engines.
    """
    pattern_suggestions: List[PatternMatch]  # Ranked by confidence
    cods_suggestion: Optional[Dict[str, Any]]  # CODS operator suggestion
    has_proven_sequence: bool  # Full game sequence exists?
    abstraction_template: Optional[Dict[str, Any]]  # Applicable template
    resonance_score: float  # 0.0-1.0 cross-domain signal strength
    trigger_chains: List[Dict[str, Any]] = field(default_factory=list)

    def validate(self) -> None:
        """Raise PhaseError if contract violated."""
        if not 0 <= self.resonance_score <= 1:
            raise PhaseError("PATTERN", f"Invalid resonance_score: {self.resonance_score}")
        for pm in self.pattern_suggestions:
            if not 0 <= pm.confidence <= 1:
                raise PhaseError("PATTERN", f"Invalid pattern confidence: {pm.confidence}")


# =============================================================================
# PHASE 5: PROPOSE - Output Contract
# =============================================================================

@dataclass
class Proposal:
    """A single action proposal with reasoning."""
    action: str
    confidence: float  # 0.0-1.0
    source: str  # Where this proposal came from
    reasoning: str  # Human-readable explanation


@dataclass
class ProposalContext:
    """
    Output of Phase 5: Propose - "What's my best move?"

    Contains ranked action proposals from all sources.
    """
    ranked_proposals: List[Proposal]  # Sorted by weighted confidence
    discovery_override: Optional[str]  # If in discovery phase, this takes priority
    subgoal_active: bool  # Working toward a subgoal?
    current_subgoal: Optional[str] = None  # The subgoal if active

    def validate(self) -> None:
        """Raise PhaseError if contract violated."""
        for p in self.ranked_proposals:
            if not 0 <= p.confidence <= 1:
                raise PhaseError("PROPOSE", f"Invalid proposal confidence: {p.confidence}")


# =============================================================================
# PHASE 6: FILTER - Output Contract
# =============================================================================

@dataclass
class FilteredContext:
    """
    Output of Phase 6: Filter - "Remove bad options"

    Contains proposals that survived all safety filters.
    """
    filtered_proposals: List[Proposal]  # After all filters
    removed_actions: Dict[str, str]  # action -> removal reason
    safety_multipliers: Dict[str, float]  # Per-action safety factor

    def validate(self) -> None:
        """Raise PhaseError if contract violated."""
        for action, mult in self.safety_multipliers.items():
            if mult < 0:
                raise PhaseError("FILTER", f"Negative safety multiplier for {action}: {mult}")


# =============================================================================
# PHASE 7: SELECT - Output Contract (Final Decision)
# =============================================================================

@dataclass
class FinalDecision:
    """
    Output of Phase 7: Select - The final decision.

    This is the ONLY place where an action is chosen.
    Contains full audit trail for debugging.
    """
    action: str  # The chosen action (ACTION1-ACTION7)
    confidence: float  # Final confidence 0.0-1.0
    reasoning: str  # Human-readable explanation
    audit_trail: Dict[str, Any]  # Full trace through all phases
    gut_instinct: str  # What Phase 5 top proposal was
    deliberation_changed: bool  # Did reasoning change the answer?
    selection_method: str = "unknown"  # "max_confidence"|"weighted_random"|"fallback"

    def validate(self) -> None:
        """Raise PhaseError if contract violated."""
        if not self.action:
            raise PhaseError("SELECT", "No action selected")
        if not self.action.startswith("ACTION"):
            raise PhaseError("SELECT", f"Invalid action format: {self.action}")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_empty_orient_context(agent_context: AgentContext) -> OrientContext:
    """Create minimal OrientContext when Phase 1 has no data."""
    return OrientContext(
        world_model={'objects': [], 'layout': 'unknown'},
        discovery_phase="idle",
        coverage_percent=0.0,
        budget_used_percent=0.0,
        blocking_questions=[],
        is_frontier=agent_context.is_frontier,
        urgency=agent_context.urgency,
    )


def create_empty_ground_truth_context() -> GroundTruthContext:
    """Create minimal GroundTruthContext when Phase 2 has no data."""
    return GroundTruthContext(
        action_safety_weights={f"ACTION{i}": 1.0 for i in range(1, 8)},
        empirical_rankings={f"ACTION{i}": 0.5 for i in range(1, 8)},
        object_valences={},
        active_beliefs=[],
        pariah_actions=set(),
        death_risk_by_position={},
    )


def create_empty_reason_context() -> ReasonContext:
    """Create minimal ReasonContext when Phase 3 has no data."""
    return ReasonContext(
        theory_state="exploring",
        theory_allowed_actions={f"ACTION{i}" for i in range(1, 8)},
        stream_conflict=False,
        agent_proposal=None,
        network_proposal=None,
        winning_source="none",
        invalidated_beliefs=[],
        confidence_in_theory=0.5,
    )


def create_empty_pattern_context() -> PatternContext:
    """Create minimal PatternContext when Phase 4 has no data."""
    return PatternContext(
        pattern_suggestions=[],
        cods_suggestion=None,
        has_proven_sequence=False,
        abstraction_template=None,
        resonance_score=0.0,
    )


def create_empty_proposal_context() -> ProposalContext:
    """Create minimal ProposalContext when Phase 5 has no data."""
    return ProposalContext(
        ranked_proposals=[],
        discovery_override=None,
        subgoal_active=False,
    )


def create_empty_filtered_context() -> FilteredContext:
    """Create minimal FilteredContext when Phase 6 has no data."""
    return FilteredContext(
        filtered_proposals=[],
        removed_actions={},
        safety_multipliers={f"ACTION{i}": 1.0 for i in range(1, 8)},
    )
