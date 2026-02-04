"""
Blackboard Architecture - Typed Slots with Epistemic Metadata

Phase 1 Implementation - Cognitive Routing

This module implements the full Blackboard architecture as the central knowledge store
that replaces the raw `context` dict. Each slot has:
- A typed value
- Confidence score (0.0-1.0)
- Source tracking (which rung/primitive populated it)
- Staleness detection
- Checkpointing support
- Rumsfeld quadrant classification

The Blackboard enables:
1. Epistemic state tracking (KK/KU/UK/UU quadrants)
2. Automatic slot dependency management
3. Checkpoint/restore for backtracking
4. Legacy context dict compatibility
5. Phase 7 forward compatibility (graph evolution structures)
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

import copy
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, Generic, List, Optional, Set, Tuple, TypeVar

T = TypeVar('T')

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class SlotCategory(Enum):
    """Categories of blackboard slots."""
    ORIENTATION = "orientation"      # Initial game state understanding
    IDENTITY = "identity"            # Self-model and control
    HYPOTHESIS = "hypothesis"        # Beliefs, theories, predictions
    EXPLOITATION = "exploitation"    # Sequences, checkpoints, navigation
    FILTER = "filter"               # Safety, avoidance, constraints
    METACOGNITION = "metacognition" # Learning, adaptation, confidence
    HISTORY = "history"             # Read-only external state


class RumsfeldQuadrant(Enum):
    """Rumsfeld epistemic quadrants."""
    KK = "known_known"      # We know that we know
    KU = "known_unknown"    # We know that we don't know
    UK = "unknown_known"    # We don't know that we know (latent)
    UU = "unknown_unknown"  # We don't know that we don't know


class EdgeType(Enum):
    """Types of edges in the cognitive graph."""
    DEPENDENCY = "dependency"        # A must run before B (data dependency)
    IMPLICATION = "implication"      # If A succeeds, B likely succeeds
    CONTRADICTION = "contradiction"  # A and B should not both activate
    REFINEMENT = "refinement"        # B refines/improves A's output
    FALLBACK = "fallback"           # If A fails, try B
    COACTIVATION = "coactivation"   # A and B often succeed together


class SlotState(Enum):
    """Lifecycle states for a slot."""
    EMPTY = auto()       # Never populated
    POPULATED = auto()   # Has value
    STALE = auto()       # Value too old
    INVALID = auto()     # Value invalidated by contradiction


class RoutingPriority(Enum):
    """Routing priority based on epistemic state."""
    EXPLORATION_FIRST = "exploration_first"      # High UU - explore unknown
    INFORMATION_MAXIMIZING = "information_max"   # High KU - answer questions
    RETRIEVAL_SEARCH = "retrieval_search"        # High UK - tap cached knowledge
    EXPLOITATION_GREEDY = "exploitation_greedy"  # High KK - exploit known
    BALANCED_SEARCH = "balanced_search"          # Mixed state


# =============================================================================
# QUESTION AND KNOWLEDGE STRUCTURES
# =============================================================================

@dataclass
class Question:
    """A specific question we know we need answered (KU quadrant)."""
    question_id: str
    description: str
    answerable_by: List[str]  # Rungs that might answer this
    priority: float = 0.5     # 0.0 to 1.0
    asked_at: int = 0         # Action number when asked
    answered: bool = False
    answer_confidence: float = 0.0

    def mark_answered(self, confidence: float) -> None:
        """Mark this question as answered."""
        self.answered = True
        self.answer_confidence = confidence


@dataclass
class KnownFact:
    """A fact we're confident about (KK quadrant)."""
    slot_name: str
    value: Any
    confidence: float
    source_rung: str
    verified_at: int  # Action number when verified


@dataclass
class RumsfeldAssessment:
    """
    Epistemological state of the agent.

    This is the core data structure for the Rumsfeld state machine.
    It tracks what the agent knows, doesn't know, and doesn't know it doesn't know.
    """
    # KK: High-confidence slots
    known_knowns: List[str] = field(default_factory=list)
    kk_confidence: float = 0.0  # Aggregate confidence in KK
    kk_facts: Dict[str, KnownFact] = field(default_factory=dict)

    # KU: Specific questions we need answered
    known_unknowns: List[str] = field(default_factory=list)  # Question IDs
    ku_questions: Dict[str, Question] = field(default_factory=dict)
    ku_urgency: float = 0.0  # How urgently we need answers
    ku_answerable_by: Dict[str, List[str]] = field(default_factory=dict)  # question -> rungs

    # UK: Cached/network knowledge not yet accessed
    unknown_knowns_candidates: List[str] = field(default_factory=list)  # Rung names
    uk_potential: float = 0.0  # Estimated value of untapped knowledge

    # UU: Estimate of unexplored territory
    uu_estimate: float = 0.5  # 0.0 (familiar) to 1.0 (novel)

    # Primary quadrant (determines base algorithm)
    primary_quadrant: RumsfeldQuadrant = RumsfeldQuadrant.UU

    def compute_routing_priority(self) -> RoutingPriority:
        """Determine which search strategy to use based on epistemic state."""
        # Priority order: UK (quick wins) > KU (targeted) > UU (explore) > KK (exploit)
        if self.uk_potential > 0.5 and len(self.unknown_knowns_candidates) > 3:
            return RoutingPriority.RETRIEVAL_SEARCH
        if self.uu_estimate > 0.7:
            return RoutingPriority.EXPLORATION_FIRST
        if len(self.known_unknowns) > 5 or self.ku_urgency > 0.6:
            return RoutingPriority.INFORMATION_MAXIMIZING
        if self.kk_confidence > 0.8:
            return RoutingPriority.EXPLOITATION_GREEDY
        return RoutingPriority.BALANCED_SEARCH

    def compute_primary_quadrant(self) -> RumsfeldQuadrant:
        """Determine which quadrant dominates current state."""
        # Priority: UK > KU > UU > KK
        if self.uk_potential > 0.5 and len(self.unknown_knowns_candidates) > 3:
            return RumsfeldQuadrant.UK
        if len(self.known_unknowns) >= 2 and self.ku_urgency > 0.4:
            return RumsfeldQuadrant.KU
        if self.uu_estimate > 0.6:
            return RumsfeldQuadrant.UU
        if self.kk_confidence > 0.7:
            return RumsfeldQuadrant.KK
        return RumsfeldQuadrant.UU  # Default to exploration

    def add_question(self, question: Question) -> None:
        """Add a question to KU quadrant."""
        self.ku_questions[question.question_id] = question
        self.known_unknowns.append(question.question_id)
        if question.answerable_by:
            self.ku_answerable_by[question.question_id] = question.answerable_by
        self._recalculate_urgency()

    def answer_question(self, question_id: str, confidence: float) -> None:
        """Mark a question as answered."""
        if question_id in self.ku_questions:
            self.ku_questions[question_id].mark_answered(confidence)
            if question_id in self.known_unknowns:
                self.known_unknowns.remove(question_id)
        self._recalculate_urgency()

    def add_fact(self, fact: KnownFact) -> None:
        """Add a fact to KK quadrant."""
        self.kk_facts[fact.slot_name] = fact
        if fact.slot_name not in self.known_knowns:
            self.known_knowns.append(fact.slot_name)
        self._recalculate_kk_confidence()

    def _recalculate_kk_confidence(self) -> None:
        """Recalculate aggregate KK confidence."""
        if self.kk_facts:
            self.kk_confidence = sum(f.confidence for f in self.kk_facts.values()) / len(self.kk_facts)
        else:
            self.kk_confidence = 0.0

    def _recalculate_urgency(self) -> None:
        """Recalculate KU urgency based on unanswered questions."""
        unanswered = [q for q in self.ku_questions.values() if not q.answered]
        if unanswered:
            self.ku_urgency = sum(q.priority for q in unanswered) / len(unanswered)
        else:
            self.ku_urgency = 0.0


# =============================================================================
# CORE DATA STRUCTURES
# =============================================================================

@dataclass
class SlotMetadata:
    """Metadata for a single blackboard slot."""
    source_rung: Optional[str] = None       # Which rung populated this
    source_primitive: Optional[str] = None  # Which primitive was used
    timestamp: Optional[datetime] = None     # When it was populated
    confidence: float = 0.0                  # 0.0-1.0 certainty
    staleness_threshold_ms: int = 5000       # When to consider stale
    access_count: int = 0                    # How many times read
    last_accessed: Optional[datetime] = None # When last read
    invalidated_by: Optional[str] = None     # Rung that invalidated this

    def is_stale(self) -> bool:
        """Check if the slot value is stale."""
        if self.timestamp is None:
            return True
        age_ms = (datetime.now() - self.timestamp).total_seconds() * 1000
        return age_ms > self.staleness_threshold_ms


@dataclass
class TypedSlot(Generic[T]):
    """A typed slot in the blackboard with full metadata."""
    name: str
    category: SlotCategory
    value: Optional[T] = None
    state: SlotState = SlotState.EMPTY
    metadata: SlotMetadata = field(default_factory=SlotMetadata)

    # Type information
    expected_type: Optional[str] = None  # e.g., "Dict[str, Any]", "List[int]"
    default_value: Optional[T] = None

    # Dependencies
    depends_on: List[str] = field(default_factory=list)  # Slots this depends on
    invalidates: List[str] = field(default_factory=list)  # Slots this invalidates when updated

    def set_value(self, value: T, source_rung: str, confidence: float = 1.0,
                  source_primitive: Optional[str] = None) -> None:
        """Set the slot value with full metadata tracking."""
        self.value = value
        self.state = SlotState.POPULATED
        self.metadata.source_rung = source_rung
        self.metadata.source_primitive = source_primitive
        self.metadata.timestamp = datetime.now()
        self.metadata.confidence = confidence

    def get_value(self) -> Optional[T]:
        """Get the slot value, updating access tracking."""
        self.metadata.access_count += 1
        self.metadata.last_accessed = datetime.now()
        return self.value

    def invalidate(self, by_rung: str) -> None:
        """Mark the slot as invalid."""
        self.state = SlotState.INVALID
        self.metadata.invalidated_by = by_rung
        self.metadata.confidence = 0.0


# =============================================================================
# PHASE 7 FORWARD COMPATIBILITY: GRAPH EVOLUTION STRUCTURES
# =============================================================================

@dataclass
class EdgeTrustRecord:
    """
    Track trust/reliability of an edge in the cognitive graph.

    This enables the graph to evolve based on runtime experience:
    - Edges that consistently help decisions gain trust
    - Edges that lead to failures lose trust
    - Trust below threshold -> edge becomes inactive
    - Trust above threshold -> edge becomes crystallized

    Formula:
        trust(t+1) = trust(t) * decay + outcome_weight * learning_rate

    Where outcome_weight:
        +1.0 if edge contributed to success
        -0.5 if edge contributed to failure
         0.0 if edge was not used
    """
    # Edge identification
    source_rung: str
    target_rung: str
    edge_type: EdgeType

    # Trust metrics
    trust_score: float = 0.5           # Initial neutral trust
    activation_count: int = 0          # How many times edge was traversed
    success_count: int = 0             # Times activation led to success
    failure_count: int = 0             # Times activation led to failure

    # Learning parameters
    learning_rate: float = 0.1         # How fast trust updates
    decay_rate: float = 0.99           # Trust decays toward neutral over time

    # Thresholds
    crystallization_threshold: float = 0.85  # Above this -> crystallized
    deactivation_threshold: float = 0.15     # Below this -> inactive

    # State
    is_crystallized: bool = False      # Permanently trusted
    is_inactive: bool = False          # Temporarily disabled
    last_activation: Optional[datetime] = None

    # Attribution
    slot_mediated: Optional[str] = None  # The slot that mediates this edge
    weight: float = 1.0                   # Static weight from cognitive_edges.json

    def record_outcome(self, success: bool) -> None:
        """Record the outcome of an edge traversal."""
        self.activation_count += 1
        self.last_activation = datetime.now()

        if success:
            self.success_count += 1
            outcome_weight = 1.0
        else:
            self.failure_count += 1
            outcome_weight = -0.5

        # Update trust with decay
        self.trust_score = (
            self.trust_score * self.decay_rate +
            outcome_weight * self.learning_rate
        )

        # Clamp to [0, 1]
        self.trust_score = max(0.0, min(1.0, self.trust_score))

        # Check thresholds
        if self.trust_score >= self.crystallization_threshold:
            self.is_crystallized = True
            self.is_inactive = False
        elif self.trust_score <= self.deactivation_threshold:
            self.is_inactive = True

    def get_effective_weight(self) -> float:
        """Get the effective weight combining static weight and trust."""
        if self.is_inactive:
            return 0.0
        if self.is_crystallized:
            return self.weight * 1.2  # Bonus for crystallized edges
        return self.weight * self.trust_score

    @property
    def success_rate(self) -> float:
        """Calculate the success rate."""
        if self.activation_count == 0:
            return 0.5  # Neutral
        return self.success_count / self.activation_count


@dataclass
class CrystallizedPath:
    """
    A proven sequence of rung activations that reliably produces good outcomes.

    When the same sequence of rungs consistently leads to success, we
    "crystallize" it as a fast-path that can be reused without full routing.

    This is the "cached solution" for common cognitive situations:
    - On a beaten level with known sequence -> crystallized exploitation path
    - In a physics game with moving objects -> crystallized physics reasoning path
    - When stuck in oscillation -> crystallized escape path
    """
    # Path identification
    path_id: str                          # Hash of the rung sequence
    rung_sequence: List[str]              # Ordered list of rung names

    # Trigger conditions (when to use this path)
    trigger_slots: Dict[str, Any]         # Slot values that trigger this path
    trigger_rumsfeld: RumsfeldQuadrant    # Epistemic state that triggers this

    # Performance metrics
    success_count: int = 0
    failure_count: int = 0
    average_actions_to_success: float = 0.0

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    creator_agent: Optional[str] = None   # Which agent discovered this

    # Validity
    is_active: bool = True
    invalidated_reason: Optional[str] = None
    min_success_rate: float = 0.7         # Below this, deactivate path

    @classmethod
    def from_rung_sequence(cls, rungs: List[str],
                          trigger_slots: Dict[str, Any],
                          trigger_rumsfeld: RumsfeldQuadrant) -> "CrystallizedPath":
        """Create a crystallized path from a rung sequence."""
        # Generate deterministic path ID
        path_str = "|".join(rungs) + "|" + json.dumps(trigger_slots, sort_keys=True)
        path_id = hashlib.md5(path_str.encode()).hexdigest()[:12]

        return cls(
            path_id=path_id,
            rung_sequence=rungs,
            trigger_slots=trigger_slots,
            trigger_rumsfeld=trigger_rumsfeld
        )

    def record_outcome(self, success: bool, actions_taken: int) -> None:
        """Record the outcome of using this path."""
        self.last_used = datetime.now()

        if success:
            self.success_count += 1
            # Update running average
            total = self.success_count + self.failure_count
            self.average_actions_to_success = (
                (self.average_actions_to_success * (total - 1) + actions_taken) / total
            )
        else:
            self.failure_count += 1

            # Check if path should be invalidated
            if self.success_rate < self.min_success_rate and self.total_uses > 5:
                self.is_active = False
                self.invalidated_reason = f"Success rate {self.success_rate:.2f} below threshold"

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.success_count + self.failure_count
        if total == 0:
            return 1.0  # Optimistic default
        return self.success_count / total

    @property
    def total_uses(self) -> int:
        """Total number of times this path was used."""
        return self.success_count + self.failure_count

    def matches_trigger(self, current_slots: Dict[str, Any],
                       current_rumsfeld: RumsfeldQuadrant) -> bool:
        """Check if current state matches this path's triggers."""
        if not self.is_active:
            return False

        if current_rumsfeld != self.trigger_rumsfeld:
            return False

        # Check all trigger slots
        for slot_name, expected_value in self.trigger_slots.items():
            actual_value = current_slots.get(slot_name)
            if actual_value != expected_value:
                return False

        return True


# =============================================================================
# BLACKBOARD CHECKPOINT (for rollback/recovery)
# =============================================================================

@dataclass
class BlackboardCheckpoint:
    """
    A snapshot of the blackboard state for rollback.

    Used for:
    1. Recovery from failed hypothesis tests
    2. Counterfactual reasoning ("what if I had...")
    3. Multi-path exploration with backtracking
    """
    checkpoint_id: str
    timestamp: datetime
    slot_values: Dict[str, Any]           # Serialized slot values
    slot_confidences: Dict[str, float]    # Confidence at checkpoint
    rumsfeld_state: Dict[str, int]        # KK/KU/UK/UU counts
    active_path: Optional[str] = None     # CrystallizedPath ID if any

    @classmethod
    def create(cls, blackboard: "Blackboard") -> "BlackboardCheckpoint":
        """Create a checkpoint from current blackboard state."""
        checkpoint_id = hashlib.md5(
            f"{datetime.now().isoformat()}".encode()
        ).hexdigest()[:8]

        slot_values = {}
        slot_confidences = {}

        for name, slot in blackboard.slots.items():
            if slot.value is not None:
                # Attempt to serialize
                try:
                    slot_values[name] = json.dumps(slot.value)
                except (TypeError, ValueError):
                    slot_values[name] = str(slot.value)
                slot_confidences[name] = slot.metadata.confidence

        return cls(
            checkpoint_id=checkpoint_id,
            timestamp=datetime.now(),
            slot_values=slot_values,
            slot_confidences=slot_confidences,
            rumsfeld_state=blackboard.get_rumsfeld_counts()
        )


# =============================================================================
# UK POTENTIAL INDEX (for Unknown-Known discovery)
# =============================================================================

@dataclass
class UKPotentialEntry:
    """
    Entry in the Unknown-Known potential index.

    Tracks slots that COULD answer questions we haven't asked yet.
    This enables discovery of latent knowledge.
    """
    slot_name: str
    questions_answerable: List[str]       # Question IDs this slot answers
    rungs_that_populate: List[str]        # Rungs that can write this slot
    current_value_hash: Optional[str]     # Hash of current value (if any)
    last_query_attempt: Optional[datetime] = None
    query_attempts: int = 0

    def should_probe(self, min_interval_seconds: float = 60.0) -> bool:
        """Check if we should try to populate this slot."""
        if self.last_query_attempt is None:
            return True

        elapsed = (datetime.now() - self.last_query_attempt).total_seconds()

        # Exponential backoff based on failed attempts
        backoff = min_interval_seconds * (2 ** min(self.query_attempts, 5))
        return elapsed > backoff


# =============================================================================
# BLACKBOARD CLASS - Phase 1 Full Implementation
# =============================================================================

class Blackboard:
    """
    Central knowledge store for cognitive routing.

    The Blackboard is the single source of truth for all slot values,
    epistemic state tracking, and decision audit trails. It replaces
    the raw context dict with typed, validated slots.

    Key Features:
    - TypedSlot storage with validation
    - Checkpoint/restore for backtracking
    - RumsfeldAssessment computation
    - Legacy context compatibility
    - UK index for discovery tracking

    Phase 1 Implementation.
    """

    # Maximum checkpoints to retain (prevents memory bloat)
    MAX_CHECKPOINTS: int = 20

    def __init__(self, slot_registry: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        Initialize the Blackboard.

        Args:
            slot_registry: Optional registry of slot definitions from
                           SLOT_DEFINITIONS. If None, slots created on demand.
        """
        self.slots: Dict[str, TypedSlot] = {}
        self._edge_trust: Dict[Tuple[str, str], EdgeTrustRecord] = {}
        self._crystallized_paths: Dict[str, CrystallizedPath] = {}
        self._uk_index: Dict[str, UKPotentialEntry] = {}
        self._checkpoints: List[BlackboardCheckpoint] = []
        self._checkpoint_counter: int = 0
        self._slot_registry = slot_registry or {}
        self._logger = logging.getLogger(__name__)

        # Pre-populate slots from registry if provided
        if self._slot_registry:
            self._initialize_from_registry()

    def _initialize_from_registry(self) -> None:
        """Pre-create slots from the slot registry."""
        for slot_name, definition in self._slot_registry.items():
            category = definition.get("category", SlotCategory.ORIENTATION)
            if isinstance(category, str):
                category = SlotCategory[category.upper()]

            # TypedSlot only accepts: name, category, expected_type
            expected_type = definition.get("expected_type")
            expected_type_str = None
            if expected_type is not None:
                if isinstance(expected_type, type):
                    expected_type_str = expected_type.__name__
                elif isinstance(expected_type, str):
                    expected_type_str = expected_type

            self.slots[slot_name] = TypedSlot(
                name=slot_name,
                category=category,
                expected_type=expected_type_str
            )

    # =========================================================================
    # Core Slot Access
    # =========================================================================

    def slot(
        self,
        key: str,
        value: Any = None,
        *,
        source_rung: str = "unknown",
        confidence: float = 1.0,
        source_primitive: Optional[str] = None,
        category: Optional[SlotCategory] = None
    ) -> Any:
        """
        Get or set a slot value.

        When called with just key: returns current value (getter mode)
        When called with key and value: sets value and returns it (setter mode)

        Args:
            key: Slot name
            value: Value to set (None = getter mode)
            source_rung: Rung that wrote this value (for audit)
            confidence: Confidence in this value [0.0, 1.0]
            source_primitive: Optional primitive that generated value
            category: Slot category (auto-detected if not provided)

        Returns:
            Current slot value (after setting if value provided)

        Example:
            # Get value
            current = blackboard.slot("grid_size")

            # Set value with metadata
            blackboard.slot("pattern_type", "rotation",
                           source_rung="R3_PATTERN_DETECTION",
                           confidence=0.85)
        """
        # Ensure slot exists
        if key not in self.slots:
            # Try to get category from registry
            if key in self._slot_registry:
                cat = self._slot_registry[key].get("category", SlotCategory.ORIENTATION)
                if isinstance(cat, str):
                    cat = SlotCategory[cat.upper()]
            else:
                cat = category or SlotCategory.ORIENTATION

            self.slots[key] = TypedSlot(name=key, category=cat)

        slot = self.slots[key]

        # Setter mode
        if value is not None:
            slot.set_value(
                value=value,
                source_rung=source_rung,
                confidence=confidence,
                source_primitive=source_primitive
            )
            return value

        # Getter mode
        return slot.get_value()

    def slot_metadata(self, key: str) -> Optional[SlotMetadata]:
        """Get metadata for a slot without retrieving value."""
        if key in self.slots:
            return self.slots[key].metadata
        return None

    def slot_state(self, key: str) -> SlotState:
        """Get the state of a slot."""
        if key not in self.slots:
            return SlotState.EMPTY
        return self.slots[key].state

    def slot_confidence(self, key: str) -> float:
        """Get confidence for a slot (0.0 if not populated)."""
        if key in self.slots and self.slots[key].state == SlotState.POPULATED:
            return self.slots[key].metadata.confidence
        return 0.0

    # =========================================================================
    # Dict-like Interface (Legacy Compatibility)
    # =========================================================================

    def __getitem__(self, key: str) -> Any:
        """Dict-like access: blackboard['key']."""
        return self.slot(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Dict-like write: blackboard['key'] = value."""
        self.slot(key, value, source_rung="legacy_write")

    def __contains__(self, key: str) -> bool:
        """Support 'key in blackboard' syntax."""
        return key in self.slots and self.slots[key].state == SlotState.POPULATED

    def __len__(self) -> int:
        """Return count of populated slots."""
        return sum(1 for s in self.slots.values() if s.state == SlotState.POPULATED)

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like get with default value."""
        value = self.slot(key)
        return value if value is not None else default

    def keys(self) -> List[str]:
        """Return all populated slot names."""
        return [k for k, s in self.slots.items() if s.state == SlotState.POPULATED]

    def items(self) -> List[Tuple[str, Any]]:
        """Return all populated (key, value) pairs."""
        return [
            (k, s.get_value())
            for k, s in self.slots.items()
            if s.state == SlotState.POPULATED
        ]

    def values(self) -> List[Any]:
        """Return all populated values."""
        return [
            s.get_value()
            for s in self.slots.values()
            if s.state == SlotState.POPULATED
        ]

    def update(self, other: Dict[str, Any], source_rung: str = "bulk_update") -> None:
        """Update multiple slots from a dict."""
        for key, value in other.items():
            self.slot(key, value, source_rung=source_rung)

    # =========================================================================
    # Checkpoint/Restore (Backtracking Support)
    # =========================================================================

    def checkpoint(self) -> int:
        """
        Create a checkpoint of current state for backtracking.

        Returns:
            Checkpoint ID (string hash from BlackboardCheckpoint)

        Use case: Before speculative reasoning, create checkpoint.
        If reasoning fails, restore to try alternative path.
        """
        # Use the existing BlackboardCheckpoint.create() classmethod
        checkpoint = BlackboardCheckpoint.create(self)
        self._checkpoints.append(checkpoint)

        # Prune old checkpoints
        if len(self._checkpoints) > self.MAX_CHECKPOINTS:
            self._checkpoints = self._checkpoints[-self.MAX_CHECKPOINTS:]

        return checkpoint.checkpoint_id

    def restore(self, checkpoint_id: str) -> bool:
        """
        Restore state from a checkpoint.

        Args:
            checkpoint_id: ID from previous checkpoint() call

        Returns:
            True if restored successfully, False if checkpoint not found
        """
        target_id = str(checkpoint_id)

        # Find the checkpoint
        checkpoint = None
        for cp in self._checkpoints:
            if cp.checkpoint_id == target_id:
                checkpoint = cp
                break

        if checkpoint is None:
            self._logger.warning(f"Checkpoint {checkpoint_id} not found")
            return False

        # Restore slot values (values stored as JSON strings in checkpoint)
        for key, json_value in checkpoint.slot_values.items():
            if key in self.slots:
                # Deserialize JSON if possible
                try:
                    value = json.loads(json_value)
                except (json.JSONDecodeError, TypeError):
                    value = json_value

                self.slots[key].value = value
                self.slots[key].state = SlotState.POPULATED if value is not None else SlotState.EMPTY

                # Restore confidence
                if key in checkpoint.slot_confidences:
                    self.slots[key].metadata.confidence = checkpoint.slot_confidences[key]

        self._logger.debug(f"Restored from checkpoint {checkpoint_id}")
        return True

    def list_checkpoints(self) -> List[Tuple[str, datetime]]:
        """List available checkpoints as (id, timestamp) tuples."""
        return [(cp.checkpoint_id, cp.timestamp) for cp in self._checkpoints]

    def create_checkpoint(self) -> str:
        """Create checkpoint and return string ID (legacy interface)."""
        return self.checkpoint()

    # =========================================================================
    # Rumsfeld Assessment
    # =========================================================================

    def get_rumsfeld_counts(self) -> Dict[str, int]:
        """Get counts of slots in each Rumsfeld quadrant."""
        counts = {"KK": 0, "KU": 0, "UK": 0, "UU": 0}

        for slot in self.slots.values():
            if slot.state == SlotState.POPULATED:
                if slot.metadata.confidence > 0.7:
                    counts["KK"] += 1
                else:
                    counts["KU"] += 1
            elif slot.state == SlotState.EMPTY:
                if slot.name in self._uk_index:
                    counts["UK"] += 1
                else:
                    counts["UU"] += 1

        return counts

    def rumsfeld_assessment(
        self,
        visited_rungs: Optional[List[str]] = None,
        all_rungs: Optional[List[str]] = None,
        action_number: int = 0
    ) -> RumsfeldAssessment:
        """
        Compute comprehensive epistemic state assessment.

        This analyzes all slots to determine:
        - What we know with confidence (KK)
        - What we know we don't know (KU)
        - What we don't know we know - hidden knowledge (UK)
        - What we don't know we don't know (UU)

        Args:
            visited_rungs: Rungs already visited this cycle
            all_rungs: All available rungs (for UK detection)
            action_number: Current action number for fact/question timestamps

        Returns:
            RumsfeldAssessment with computed metrics
        """
        visited_rungs = visited_rungs or []
        all_rungs = all_rungs or []

        # Start with a fresh assessment
        assessment = RumsfeldAssessment()

        # Analyze each slot
        for slot_name, slot in self.slots.items():
            if slot.state == SlotState.POPULATED:
                conf = slot.metadata.confidence

                if conf > 0.7:
                    # Known Known - high confidence populated
                    fact = KnownFact(
                        slot_name=slot_name,
                        value=slot.value,
                        confidence=conf,
                        source_rung=slot.metadata.source_rung or "unknown",
                        verified_at=action_number
                    )
                    assessment.add_fact(fact)
                else:
                    # Known Unknown - low confidence populated
                    question = Question(
                        question_id=f"q_{slot_name}",
                        description=f"What is the true value of {slot_name}?",
                        answerable_by=[],
                        priority=1.0 - conf  # Lower confidence = higher priority
                    )
                    assessment.add_question(question)

            elif slot.state == SlotState.EMPTY:
                if slot_name in self._uk_index:
                    # Unknown Known - we know we need this but don't have it
                    uk_entry = self._uk_index[slot_name]
                    if slot_name not in assessment.unknown_knowns_candidates:
                        assessment.unknown_knowns_candidates.append(slot_name)
                        assessment.uk_potential += 0.1  # Increment potential

        # Estimate UU based on unvisited rungs
        if all_rungs:
            unvisited_ratio = 1.0 - (len(visited_rungs) / len(all_rungs)) if all_rungs else 0.5
            assessment.uu_estimate = max(0.0, min(1.0, unvisited_ratio))

        # Compute primary quadrant
        assessment.primary_quadrant = assessment.compute_primary_quadrant()

        return assessment

    # =========================================================================
    # UK Index Management (Discovery Tracking)
    # =========================================================================

    def register_uk_need(
        self,
        slot_name: str,
        potential_sources: List[str],
        questions_answerable: Optional[List[str]] = None
    ) -> None:
        """
        Register that we know we need a slot but don't have it.

        This promotes a slot from UU to UK quadrant.

        Args:
            slot_name: The slot we need
            potential_sources: Rungs that might provide it
            questions_answerable: Question IDs this slot can answer
        """
        self._uk_index[slot_name] = UKPotentialEntry(
            slot_name=slot_name,
            questions_answerable=questions_answerable or [],
            rungs_that_populate=potential_sources,
            current_value_hash=None
        )

    def clear_uk_need(self, slot_name: str) -> None:
        """Remove slot from UK index (it's been discovered)."""
        if slot_name in self._uk_index:
            del self._uk_index[slot_name]

    # =========================================================================
    # Legacy Context Conversion
    # =========================================================================

    @classmethod
    def from_context(
        cls,
        context: Dict[str, Any],
        slot_registry: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> "Blackboard":
        """
        Create a Blackboard from a legacy context dict.

        This enables gradual migration from raw dicts to typed slots.

        Args:
            context: Legacy context dictionary
            slot_registry: Optional slot definitions

        Returns:
            New Blackboard populated from context
        """
        blackboard = cls(slot_registry=slot_registry)

        for key, value in context.items():
            if value is not None:
                # Determine category from registry or default
                category = SlotCategory.ORIENTATION
                if slot_registry and key in slot_registry:
                    cat = slot_registry[key].get("category", "ORIENTATION")
                    if isinstance(cat, str):
                        category = SlotCategory[cat.upper()]
                    else:
                        category = cat

                blackboard.slot(
                    key,
                    value,
                    source_rung="legacy_migration",
                    confidence=0.8,  # Legacy data gets moderate confidence
                    category=category
                )

        return blackboard

    def to_context(self) -> Dict[str, Any]:
        """
        Export Blackboard to legacy context dict.

        This enables backward compatibility with code expecting dicts.

        Returns:
            Dictionary of slot_name -> value for all populated slots
        """
        return {
            key: slot.get_value()
            for key, slot in self.slots.items()
            if slot.state == SlotState.POPULATED
        }

    # =========================================================================
    # Edge Trust Management
    # =========================================================================

    def record_edge_traversal(
        self,
        from_rung: str,
        to_rung: str,
        edge_type: EdgeType,
        success: bool
    ) -> None:
        """Record a rung-to-rung edge traversal for trust computation."""
        key = (from_rung, to_rung)

        if key not in self._edge_trust:
            self._edge_trust[key] = EdgeTrustRecord(
                source_rung=from_rung,
                target_rung=to_rung,
                edge_type=edge_type
            )

        # Use the record_outcome method which handles trust updates
        record = self._edge_trust[key]
        record.record_outcome(success)

    def get_edge_trust(self, from_rung: str, to_rung: str) -> float:
        """Get trust score for an edge (default 0.5 if unknown)."""
        key = (from_rung, to_rung)
        if key in self._edge_trust:
            return self._edge_trust[key].trust_score
        return 0.5  # Neutral default

    # =========================================================================
    # Crystallized Path Management
    # =========================================================================

    def crystallize_path(
        self,
        rung_sequence: List[str],
        trigger_slots: Dict[str, Any],
        trigger_rumsfeld: RumsfeldQuadrant
    ) -> str:
        """
        Record a successful rung sequence as crystallized path.

        Returns:
            The path_id of the created crystallized path.
        """
        path = CrystallizedPath.from_rung_sequence(
            rungs=rung_sequence,
            trigger_slots=trigger_slots,
            trigger_rumsfeld=trigger_rumsfeld
        )
        self._crystallized_paths[path.path_id] = path
        return path.path_id

    def get_crystallized_path(
        self,
        current_slots: Dict[str, Any],
        current_rumsfeld: RumsfeldQuadrant
    ) -> Optional[CrystallizedPath]:
        """Find a crystallized path matching current state."""
        for path in self._crystallized_paths.values():
            if path.matches_trigger(current_slots, current_rumsfeld):
                return path
        return None

    def get_crystallized_path_by_id(self, path_id: str) -> Optional[CrystallizedPath]:
        """Get a specific crystallized path by ID."""
        return self._crystallized_paths.get(path_id)

    # =========================================================================
    # Debugging and Introspection
    # =========================================================================

    def summary(self) -> Dict[str, Any]:
        """Get a summary of blackboard state for debugging."""
        rumsfeld = self.get_rumsfeld_counts()
        return {
            "total_slots": len(self.slots),
            "populated_slots": len(self),
            "rumsfeld_counts": rumsfeld,
            "checkpoints": len(self._checkpoints),
            "uk_index_size": len(self._uk_index),
            "edge_trust_records": len(self._edge_trust),
            "crystallized_paths": len(self._crystallized_paths)
        }

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"Blackboard(slots={len(self)}/{len(self.slots)}, checkpoints={len(self._checkpoints)})"


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "SlotCategory",
    "RumsfeldQuadrant",
    "EdgeType",
    "SlotState",
    "RoutingPriority",
    # Core structures
    "SlotMetadata",
    "TypedSlot",
    # Epistemic structures (Phase 1)
    "Question",
    "KnownFact",
    "RumsfeldAssessment",
    # Phase 7 structures
    "EdgeTrustRecord",
    "CrystallizedPath",
    # Supporting structures
    "BlackboardCheckpoint",
    "UKPotentialEntry",
    # Blackboard class
    "Blackboard",
]
