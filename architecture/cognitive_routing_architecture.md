# Cognitive Routing Architecture

**Version**: 1.0
**Date**: 2026-02-05
**Status**: IMPLEMENTED (Phases 0-11 Complete)
**Supersedes**: `decision_cognitive_architecture.md` (legacy document)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [The Three Metacognitive Layers](#the-three-metacognitive-layers)
4. [Component Architecture](#component-architecture)
5. [Phase 1: Blackboard Core](#phase-1-blackboard-core)
6. [Phase 1.5-1.6: Epistemic Tracker](#phase-15-16-epistemic-tracker)
7. [Phase 2-2.5: Cognitive Graph](#phase-2-25-cognitive-graph)
8. [Phase 3-3.5: Meta-Planner](#phase-3-35-meta-planner)
9. [Phase 4: Cognitive Router](#phase-4-cognitive-router)
10. [Phase 5-7.5: Graph Evolution](#phase-5-75-graph-evolution)
11. [Phase 8: Eisenhower Layer](#phase-8-eisenhower-layer)
12. [Phase 9: Phenomenology Layer](#phase-9-phenomenology-layer)
13. [Phase 10: Valence-Tagged Knowledge](#phase-10-valence-tagged-knowledge)
14. [Phase 11: Phenomenology ↔ Graph Integration](#phase-11-phenomenology--graph-integration)
15. [Complete Decision Pipeline](#complete-decision-pipeline)
16. [File Reference](#file-reference)

---

## Executive Summary

The Cognitive Routing System replaces static `ORDERING_PRESETS` with a dynamic **Blackboard + Meta-Planner + Cognitive Graph** architecture enhanced with **three metacognitive layers**:

1. **Epistemic Layer** (Rumsfeld): What's my knowledge state? (KK/KU/UK/UU)
2. **Pragmatic Layer** (Eisenhower): What's urgent and important? (Q1-Q4)
3. **Affective Layer** (Phenomenology): What's my compressed feeling? (FeltState)

**Key Complexity Win**: O(26) typical case vs O(1575) static A* via early termination + focused search + exclusions.

**Implementation Status**: All 11 phases complete with 194+ tests passing.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         COGNITIVE ROUTING PIPELINE                           │
│                                                                              │
│  Frame Arrives                                                               │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    PHENOMENOLOGY LAYER (Phase 9)                     │   │
│  │  "How do I feel about last cycle?"                                   │   │
│  │                                                                       │   │
│  │  Blackboard (100+ slots) ──compress()──► FeltState (5D)             │   │
│  │       valence: THREAT|CONFUSION|NEUTRAL|CURIOSITY|MASTERY           │   │
│  │       arousal: 0.0-1.0 (activation level)                           │   │
│  │       certainty: 0.0-1.0 (epistemic confidence)                     │   │
│  │       agency: 0.0-1.0 (feeling of control)                          │   │
│  │       salience: 0.0-1.0 (attention capture)                         │   │
│  │                                                                       │   │
│  │  FeltState ──inject()──► felt_* slots in Blackboard                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    EPISTEMIC TRACKER (Phase 1.5)                     │   │
│  │  "What do I know? What don't I know?"                                │   │
│  │                                                                       │   │
│  │       ┌────────────────┬────────────────┐                           │   │
│  │       │      KK        │      KU        │  KNOWN                    │   │
│  │       │  (exploit)     │  (research)    │  (about self)             │   │
│  │       ├────────────────┼────────────────┤                           │   │
│  │       │      UK        │      UU        │  UNKNOWN                  │   │
│  │       │  (retrieve)    │  (explore)     │  (about self)             │   │
│  │       └────────────────┴────────────────┘                           │   │
│  │              KNOWN            UNKNOWN                                │   │
│  │            (about world)    (about world)                           │   │
│  │                                                                       │   │
│  │  Transitions (KK→KU, UU→UK, etc.) trigger algorithm switches        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│       │                                                                      │
│       ▼ Quadrant + FeltState determine algorithm                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    META-PLANNER (Phase 3)                            │   │
│  │  "How should I search?"                                              │   │
│  │                                                                       │   │
│  │  Algorithm selection based on:                                       │   │
│  │    - Epistemic quadrant (KK/KU/UK/UU)                               │   │
│  │    - Domain signature                                                │   │
│  │    - FeltState modulation (panic→narrow, bored→explore)             │   │
│  │                                                                       │   │
│  │  Algorithms: TargetedQuestionSearch, RetrievalSearch,               │   │
│  │              GreedyExploitation, ExplorationWithExclusions          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│       │                                                                      │
│       ▼ Algorithm returns candidate rungs [R1, R2, R3...]                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    EISENHOWER LAYER (Phase 8)                        │   │
│  │  "What should I do RIGHT NOW?"                                       │   │
│  │                                                                       │   │
│  │           │ URGENT              │ NOT URGENT                         │   │
│  │   ────────┼─────────────────────┼─────────────────────               │   │
│  │   IMPORT- │ Q1: DO NOW          │ Q2: SCHEDULE                       │   │
│  │   ANT     │ (Execute this rung) │ (Queue for later)                  │   │
│  │   ────────┼─────────────────────┼─────────────────────               │   │
│  │   NOT     │ Q3: DELEGATE        │ Q4: ELIMINATE                      │   │
│  │   IMPORT- │ (Use cached path)   │ (Don't waste actions)              │   │
│  │   ANT     │                     │                                    │   │
│  │                                                                       │   │
│  │  Urgency: time pressure, resource scarcity, volatility              │   │
│  │  Importance: epistemic value, goal alignment, strategic value       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│       │                                                                      │
│       ▼ Single prioritized action                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    COGNITIVE ROUTER (Phase 4)                        │   │
│  │  Executes selected rung, updates blackboard                          │   │
│  │  Records traversal for graph evolution                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│       │                                                                      │
│       ▼                                                                      │
│  (action, confidence, reason) ──► ARC API                                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## The Three Metacognitive Layers

The system implements three complementary metacognitive layers that feed back into each cycle:

| Layer | Question | Output | Module |
|-------|----------|--------|--------|
| **Phenomenology** | "How do I feel?" | FeltState (5D) | `phenomenology_layer.py` |
| **Epistemic** | "What do I know?" | Rumsfeld quadrant | `epistemic_tracker.py` |
| **Pragmatic** | "What do I do?" | Eisenhower quadrant | `eisenhower_layer.py` |

### Why Three Layers?

Each layer captures a different aspect of intelligent decision-making:

1. **Phenomenology captures affect**: A system can be in KK (knows what to do) but feel THREAT (something's wrong). The mismatch is informative.

2. **Epistemic captures knowledge state**: Knowing what you know vs. don't know determines search strategy.

3. **Pragmatic captures action priority**: Not all knowledge gaps are equal—some are urgent, some can wait.

**Key Insight**: Low `felt_agency` + high `kk_confidence` = "I think I know, but I feel out of control" → something's wrong with the model.

---

## Component Architecture

### Core Files by Phase

| Phase | Files | LOC | Purpose |
|-------|-------|-----|---------|
| 1 | `blackboard.py` | ~1360 | Shared working memory with typed slots |
| 1.5 | `epistemic_tracker.py`, `epistemic_state.py` | ~400 | Rumsfeld state machine |
| 1.6 | `hysteresis.py`, `question_manager.py`, `epistemic_logging.py` | ~600 | Stability & observability |
| 2 | `cognitive_graph.py` | ~400 | Rungs as nodes, edges with trust |
| 2.5 | `edge_inference.py` | ~350 | Automatic edge discovery |
| 3 | `meta_planner.py` | ~400 | Algorithm selection with caching |
| 3.5 | `precomputation.py` | ~300 | Front-loaded O(1) lookups |
| 4 | `cognitive_router.py` | ~1100 | Orchestrates all components |
| 5-6 | `routing_traces.py`, `routing_metrics.py` | ~500 | Validation & production |
| 7 | `graph_evolution.py`, `rung_roles.py`, `path_crystallization.py`, `process_knowledge.py` | ~1500 | Long-term learning |
| 8 | `eisenhower_layer.py` | ~635 | Urgency × importance prioritization |
| 9 | `phenomenology_layer.py` | ~782 | FeltState compression & feedback |
| 10 | `valence_tagged_slot.py` | ~683 | Valence as inherent property |
| 11 | `graph_evolution.py` (enhanced) | +200 | Valence-weighted crystallization |

### Test Coverage

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_blackboard.py` | 37 | Blackboard core |
| `test_epistemic_tracker.py` | 25 | Rumsfeld transitions |
| `test_cognitive_graph.py` | 30 | Graph operations |
| `test_cognitive_router.py` | 50 | Full routing |
| `test_eisenhower_layer.py` | 33 | Q1-Q4 classification |
| `test_phenomenology_layer.py` | 32 | FeltState compression |
| `test_valence_tagged_slot.py` | 38 | Valence tagging |
| `test_graph_evolution.py` | 54 | Edge trust & crystallization |
| **Total** | **299+** | All phases |

---

## Phase 1: Blackboard Core

### Purpose

Shared working memory for all cognitive components. Replaces ad-hoc context dict with typed, observable slots.

### Key Data Structures

```python
@dataclass
class BlackboardSlot:
    """Single slot in the cognitive blackboard."""
    value: Any
    confidence: float = 1.0      # 0.0-1.0
    source_rung: str = "unknown"
    timestamp: int = 0           # Action number when written
    ttl: Optional[int] = None    # Time-to-live in actions

class RumsfeldQuadrant(Enum):
    KK = "known_knowns"      # High confidence + verified
    KU = "known_unknowns"    # Have questions, seeking answers
    UK = "unknown_knowns"    # Cached knowledge we forgot we have
    UU = "unknown_unknowns"  # Novel territory

class Blackboard:
    """Cognitive blackboard - shared working memory."""

    def slot(self, key: str, value: Any = None, **kwargs) -> Any:
        """Get or set slot value."""

    def get(self, key: str, default: Any = None) -> Any:
        """Get slot value with default."""

    def write_with_valence(self, key: str, value: Any,
                           valence: 'Valence', urgency: float,
                           importance: float) -> None:
        """Write value with inherent urgency/importance (Phase 10)."""

    def get_aggregate_urgency(self) -> float:
        """O(1) aggregate urgency from valence-tagged slots."""

    def get_aggregate_importance(self) -> float:
        """O(1) aggregate importance from valence-tagged slots."""
```

### Integration

The Blackboard is passed to all cognitive components:
- `EpistemicTracker(blackboard)`
- `MetaPlanner(blackboard, graph)`
- `EisenhowerLayer(blackboard)`
- `PhenomenologyLayer(blackboard)`
- `CognitiveRouter(blackboard, ...)`

---

## Phase 1.5-1.6: Epistemic Tracker

### Purpose

Track knowledge state as a **state machine** where transitions drive algorithm selection.

### The Rumsfeld Matrix as State Machine

```
          ┌──────────────────────────────────────────────────────────┐
          │                    KNOWN (about self)                     │
          │                                                           │
          │   ┌─────────────────┐        ┌─────────────────┐         │
          │   │       KK        │───────→│       KU        │         │
KNOWN     │   │   exploitation  │        │   targeted      │         │
(about    │   │                 │←───────│   search        │         │
world)    │   └────────┬────────┘        └────────┬────────┘         │
          │            │                          │                  │
          │            ▼                          ▼                  │
          │   ┌─────────────────┐        ┌─────────────────┐         │
          │   │       UK        │───────→│       UU        │         │
UNKNOWN   │   │   retrieval     │        │   exploration   │         │
(about    │   │   search        │←───────│                 │         │
world)    │   └─────────────────┘        └─────────────────┘         │
          │                                                           │
          └──────────────────────────────────────────────────────────┘

Transitions trigger algorithm switches - NOT domain re-classification!
```

### Key Classes

```python
@dataclass
class EpistemicTransition:
    """A transition between epistemic states."""
    from_quadrant: RumsfeldQuadrant
    to_quadrant: RumsfeldQuadrant
    trigger: str           # What caused the transition
    confidence: float      # How confident in this transition
    timestamp: int

class EpistemicTracker:
    """Tracks epistemic state as a state machine."""

    def update(self, rung_result: RungResult) -> Optional[EpistemicTransition]:
        """Process rung result, detect transitions."""

    def get_current_quadrant(self) -> RumsfeldQuadrant:
        """Get current epistemic quadrant."""

    def get_open_questions(self) -> List[Question]:
        """Get questions we know we need answered (KU)."""
```

### Transition Response Map

```python
TRANSITION_RESPONSES = {
    # Discovery: UU → KU (found something to investigate)
    ('UU', 'KU'): {
        'algorithm': 'TargetedQuestionSearch',
        'priority_boost': ['hypothesis_rungs'],
    },

    # Verification: KU → KK (answered our question)
    ('KU', 'KK'): {
        'algorithm': 'GreedyExploitation',
        'priority_boost': ['exploitation_rungs'],
    },

    # Contradiction: KK → KU (our knowledge was wrong!)
    ('KK', 'KU'): {
        'algorithm': 'BacktrackingSearch',
        'priority_boost': ['theory_revision_rungs'],
        'trust_penalty': 0.3,  # Penalize the failed path
    },

    # Retrieval: UK → KK (remembered something useful)
    ('UK', 'KK'): {
        'algorithm': 'GreedyExploitation',
        'use_cached_path': True,
    },
}
```

### Hysteresis (Preventing Thrashing)

```python
class HysteresisManager:
    """Prevents rapid quadrant oscillation."""

    def __init__(self):
        self.confirmation_threshold = 3   # Confirms before transition
        self.cooldown_ticks = 5           # Ticks before same transition
        self.signal_decay = 0.9           # Signal strength decay per tick

    def should_transition(self, proposed: EpistemicTransition) -> bool:
        """Check if transition should proceed (enough confirmations)."""
```

---

## Phase 2-2.5: Cognitive Graph

### Purpose

Represent rungs as nodes connected by weighted edges. Enables graph-based search instead of linear ordering.

### Key Classes

```python
class EdgeType(Enum):
    DEPENDENCY = "dependency"      # B requires A's output
    IMPLICATION = "implication"    # A suggests B is relevant
    CONTRADICTION = "contradiction" # A and B conflict
    REFINEMENT = "refinement"      # B refines A's output
    FALLBACK = "fallback"          # Use B if A fails
    COACTIVATION = "coactivation"  # A and B should run together

@dataclass
class CognitiveEdge:
    source: str          # Source rung name
    target: str          # Target rung name
    edge_type: EdgeType
    weight: float        # Trust weight (0.0-1.0)
    condition: Optional[str] = None  # When this edge applies

class CognitiveGraph:
    """Graph of rungs connected by cognitive edges."""

    def get_successors(self, rung: str, context: SearchContext) -> List[str]:
        """Get valid successor rungs given current context."""

    def get_edge_weight(self, from_rung: str, to_rung: str) -> float:
        """Get trust weight for edge."""

    def update_edge_trust(self, from_rung: str, to_rung: str,
                          success: bool) -> None:
        """Update edge trust based on traversal outcome."""
```

### Edge Inference Engine

```python
class EdgeInferenceEngine:
    """Automatically infer edges from rung metadata and runtime."""

    def infer_from_slot_dependencies(self) -> List[CognitiveEdge]:
        """Infer DEPENDENCY edges from slot read/write patterns."""

    def infer_from_runtime_transitions(self) -> List[CognitiveEdge]:
        """Infer edges from observed successful transitions."""

    def validate_edges(self) -> EdgeValidationResult:
        """Three-list validation: confident/uncertain/missing."""
```

---

## Phase 3-3.5: Meta-Planner

### Purpose

Select the right search algorithm based on epistemic state, domain, and FeltState.

### Algorithm Selection

```python
class MetaPlanner:
    """Selects search algorithm based on context."""

    def select_algorithm(self, blackboard: Blackboard,
                         felt_state: Optional[FeltState] = None
                        ) -> SearchAlgorithm:
        """
        Selection based on:
        1. Epistemic quadrant (primary)
        2. Domain signature (secondary)
        3. FeltState modulation (tertiary)
        """

# Quadrant → Algorithm mapping
QUADRANT_ALGORITHMS = {
    'KK': GreedyExploitation,      # Exploit what we know
    'KU': TargetedQuestionSearch,  # Research our questions
    'UK': RetrievalSearch,         # Retrieve cached knowledge
    'UU': ExplorationWithExclusions,  # Explore cautiously
}
```

### FeltState Modulation (Phase 9 Integration)

```python
@dataclass
class AlgorithmModulation:
    """How FeltState modulates algorithm behavior."""
    beam_width_multiplier: float = 1.0
    exploration_bonus: float = 0.0
    exploitation_bonus: float = 0.0
    path_exclusions: List[str] = field(default_factory=list)

def get_modulation(felt: FeltState) -> AlgorithmModulation:
    """Convert FeltState to algorithm modulation."""

    if felt.valence == Valence.THREAT and felt.arousal > 0.7:
        # Panic mode: narrow focus
        return AlgorithmModulation(
            beam_width_multiplier=0.5,
            exploitation_bonus=0.3,
        )

    elif felt.valence == Valence.MASTERY and felt.certainty > 0.8:
        # Confident: exploit hard
        return AlgorithmModulation(
            exploitation_bonus=0.5,
        )

    elif felt.valence == Valence.BOREDOM:
        # Bored: explore more
        return AlgorithmModulation(
            beam_width_multiplier=1.5,
            exploration_bonus=0.3,
        )
```

### Caching

```python
class MetaPlannerCache:
    """Cache algorithm selection with smart invalidation."""

    # Only these slots invalidate the cache
    RELEVANT_SLOTS = {
        'epistemic_quadrant', 'domain_signature',
        'contradiction_detected', 'felt_valence'
    }

    def get_cached_algorithm(self, context_hash: str) -> Optional[SearchAlgorithm]:
        """O(1) lookup for cached algorithm selection."""
```

---

## Phase 4: Cognitive Router

### Purpose

Orchestrates all cognitive components into a unified decision pipeline.

### Key Class

```python
class CognitiveRouter:
    """Main orchestrator for cognitive routing."""

    def __init__(self, blackboard: Blackboard, graph: CognitiveGraph,
                 meta_planner: MetaPlanner, epistemic_tracker: EpistemicTracker,
                 eisenhower_layer: EisenhowerLayer,
                 phenomenology_layer: PhenomenologyLayer):
        self.blackboard = blackboard
        self.graph = graph
        self.meta_planner = meta_planner
        self.epistemic = epistemic_tracker
        self.eisenhower = eisenhower_layer
        self.phenomenology = phenomenology_layer
        self.fallback = CatastrophicFallback()

    def route(self, game_state: Dict, context: Dict) -> RungResult:
        """
        Main routing pipeline:
        1. Phenomenology: Compress to FeltState, inject back
        2. Epistemic: Update quadrant, detect transitions
        3. Meta-Planner: Select algorithm (modulated by FeltState)
        4. Algorithm: Get candidate rungs
        5. Eisenhower: Prioritize by urgency × importance
        6. Execute: Run selected rung
        7. Record: Update graph evolution
        """
```

### Catastrophic Fallback

```python
class CatastrophicFallback:
    """Circuit breaker for stuck states."""

    def check(self, blackboard: Blackboard) -> Optional[FailureType]:
        """
        Detect catastrophic states:
        - Stuck loop (same state 10+ times)
        - Empty frontier (no valid rungs)
        - Contradiction storm (3+ contradictions in 5 ticks)
        """

    def get_escape_action(self, failure_type: FailureType) -> RungResult:
        """Get emergency escape action."""
```

---

## Phase 5-7.5: Graph Evolution

### Purpose

Long-term learning: edge trust accumulates across games, paths crystallize into lookups.

### Edge Trust

```python
@dataclass
class EdgeTrustRecord:
    """Cumulative trust record for an edge."""
    from_rung: str
    to_rung: str
    total_traversals: int = 0
    successful_traversals: int = 0
    contradiction_count: int = 0
    last_updated_game: str = ""

    @property
    def trust_score(self) -> float:
        """Trust with negative reputation penalty."""
        if self.total_traversals == 0:
            return 0.5  # Neutral prior

        base = self.successful_traversals / self.total_traversals
        penalty = self.contradiction_count * 0.1  # Contradictions hurt
        return max(0.0, base - penalty)
```

### Path Crystallization

```python
@dataclass
class CrystallizedPath:
    """A path proven reliable enough to become a lookup."""
    domain: str
    path: List[str]          # Rung sequence
    traversal_count: int
    success_count: int
    crystallized_at: Optional[str] = None

    def is_reliable(self, domain_game_count: int) -> bool:
        """Domain-relative threshold: min(10, 50% of domain games)."""
        threshold = min(10, max(3, domain_game_count // 2))
        return (self.traversal_count >= threshold and
                self.success_rate >= 0.9)

class PathCrystallizer:
    """Detect when paths should become lookups."""

    def record_successful_path(self, domain: str, path: List[str]) -> None:
        """Record a successful path traversal."""

    def get_crystallized_path(self, domain: str) -> Optional[CrystallizedPath]:
        """Get crystallized path for domain (if exists)."""
```

### Process Knowledge

```python
@dataclass
class AbstractPattern:
    """Abstract pattern extracted from concrete paths."""
    pattern_id: str
    role_sequence: List[RungRole]  # ENTRY → LEVERAGE → RESOLUTION
    domain_instantiations: Dict[str, List[str]]  # domain → concrete path
    success_by_domain: Dict[str, float]

class ProcessKnowledgeExtractor:
    """Extract transferable patterns from successful paths."""

    def extract_pattern(self, path: List[str]) -> AbstractPattern:
        """Extract role sequence from concrete rung path."""

    def suggest_path_for_new_domain(self, domain: str,
                                     similar_domains: List[str]
                                    ) -> Optional[List[str]]:
        """Transfer learning: suggest path based on similar domains."""
```

---

## Phase 8: Eisenhower Layer

### Purpose

Prioritize tasks by urgency × importance into 4 quadrants.

### Key Classes

```python
class EisenhowerQuadrant(Enum):
    Q1_DO = "do_now"           # Urgent + Important → Execute immediately
    Q2_SCHEDULE = "schedule"    # Not Urgent + Important → Queue for later
    Q3_DELEGATE = "delegate"    # Urgent + Not Important → Use cached path
    Q4_ELIMINATE = "eliminate"  # Not Urgent + Not Important → Skip

@dataclass
class UrgencyScore:
    """Computed urgency based on game state."""
    time_pressure: float       # Actions remaining / budget
    resource_scarcity: float   # How close to limits
    volatility: float          # How fast things change
    external_forcing: float    # Deadline pressure

    @property
    def total(self) -> float:
        """Normalized urgency 0.0-1.0."""
        return min(1.0, (self.time_pressure * 0.3 +
                         self.resource_scarcity * 0.3 +
                         self.volatility * 0.2 +
                         self.external_forcing * 0.2))

@dataclass
class ImportanceScore:
    """Computed importance based on expected impact."""
    epistemic_value: float     # How much we'd learn
    goal_alignment: float      # How much it helps winning
    strategic_value: float     # Long-term benefit

    @property
    def total(self) -> float:
        """Normalized importance 0.0-1.0."""
        return min(1.0, (self.epistemic_value * 0.4 +
                         self.goal_alignment * 0.4 +
                         self.strategic_value * 0.2))
```

### Eisenhower Layer

```python
class EisenhowerLayer:
    """Prioritize tasks by urgency × importance."""

    def __init__(self, blackboard: Blackboard):
        self.blackboard = blackboard
        self.scheduled_queue: List[PrioritizedTask] = []

    def compute_urgency(self, task: Any) -> UrgencyScore:
        """Compute urgency from blackboard state."""

    def compute_importance(self, task: Any) -> ImportanceScore:
        """Compute importance from blackboard state."""

    def classify(self, task: Any) -> EisenhowerClassification:
        """Classify task into Q1-Q4."""

    def prioritize(self, candidates: List[Any]) -> Iterator[PrioritizedTask]:
        """Yield candidates in priority order (Q1 first, Q4 eliminated)."""

    def age_scheduled_queue(self) -> List[PrioritizedTask]:
        """Age Q2 tasks, promote to Q1 if now urgent."""
```

### Cross-Matrix Mapping

Rumsfeld quadrant influences Eisenhower classification:

```python
RUMSFELD_TO_EISENHOWER_BIAS = {
    'KK': {'importance_boost': 0.1, 'urgency_boost': 0.2},   # Trust what we know
    'KU': {'importance_boost': 0.2, 'urgency_boost': 0.0},   # Questions are important
    'UK': {'importance_boost': 0.1, 'urgency_boost': -0.1},  # Retrieval not urgent
    'UU': {'importance_boost': 0.0, 'urgency_boost': -0.2},  # Exploration not urgent
}
```

---

## Phase 9: Phenomenology Layer

### Purpose

Compress high-dimensional blackboard state to 5D FeltState, inject back for feedback loop.

### Core Insight

> "Phenomenology is the compressed output. The JPEG of captured input."
>
> Pain doesn't represent tissue damage then add "bad"—pain IS the representation of damage in a format that includes urgency.

### Key Classes

```python
class Valence(Enum):
    """Core felt quality of current state."""
    THREAT = "threat"           # Danger, need to escape
    CONFUSION = "confusion"     # Lost, need orientation
    NEUTRAL = "neutral"         # Stable, no strong signal
    CURIOSITY = "curiosity"     # Interesting, worth exploring
    MASTERY = "mastery"         # Confident, in control

@dataclass
class FeltState:
    """5D compressed representation of cognitive state."""
    valence: Valence           # Core felt quality
    arousal: float             # 0.0-1.0 activation level
    certainty: float           # 0.0-1.0 epistemic confidence
    agency: float              # 0.0-1.0 feeling of control
    salience: float            # 0.0-1.0 attention capture
    momentum: float = 0.0      # -1.0 to 1.0 (improving/worsening)

    def to_urgency_bias(self) -> float:
        """Convert to Eisenhower urgency bias."""
        if self.valence == Valence.THREAT:
            return 0.3 * self.arousal
        elif self.valence == Valence.CONFUSION:
            return 0.1 * (1 - self.certainty)
        return 0.0

    def to_importance_bias(self) -> float:
        """Convert to Eisenhower importance bias."""
        if self.valence == Valence.MASTERY:
            return 0.2 * self.certainty
        elif self.valence == Valence.CURIOSITY:
            return 0.15 * self.salience
        return 0.0
```

### Phenomenology Layer

```python
class PhenomenologyLayer:
    """Compress blackboard to FeltState, inject back."""

    def __init__(self, blackboard: Blackboard):
        self.blackboard = blackboard
        self.stabilizer = FeltStateStabilizer()
        self.trace_log: List[FeltStateTraceEntry] = []

    def compress(self) -> FeltState:
        """
        Compress 100+ blackboard slots to 5D FeltState.

        Valence determined by:
        - THREAT: cascade_failure OR action_budget_critical
        - CONFUSION: UU quadrant OR no working_theory
        - MASTERY: KK quadrant AND high strategy_stability
        - CURIOSITY: high novelty_score OR recent discovery
        - NEUTRAL: default

        Arousal = f(frame_delta_magnitude, surprise_score)
        Certainty = f(epistemic_quadrant, confidence_scores)
        Agency = f(controlled_object, action_success_rate)
        Salience = f(novelty_score, pattern_break, stuck_detected)
        """

    def inject(self, felt: FeltState) -> None:
        """Inject FeltState back into blackboard as felt_* slots."""
        self.blackboard.slot('felt_valence', felt.valence.value,
                             source_rung='phenomenology')
        self.blackboard.slot('felt_arousal', felt.arousal,
                             source_rung='phenomenology')
        self.blackboard.slot('felt_certainty', felt.certainty,
                             source_rung='phenomenology')
        self.blackboard.slot('felt_agency', felt.agency,
                             source_rung='phenomenology')
        self.blackboard.slot('felt_salience', felt.salience,
                             source_rung='phenomenology')
        self.blackboard.slot('felt_momentum', felt.momentum,
                             source_rung='phenomenology')
        self.blackboard.slot('felt_urgency_bias', felt.to_urgency_bias(),
                             source_rung='phenomenology')
        self.blackboard.slot('felt_importance_bias', felt.to_importance_bias(),
                             source_rung='phenomenology')

    def get_algorithm_modulation(self) -> AlgorithmModulation:
        """Convert current FeltState to algorithm parameter modulation."""
```

### Stabilizer (Preventing Thrashing)

```python
class FeltStateStabilizer:
    """Prevent rapid FeltState oscillation."""

    def __init__(self):
        self.inertia = 0.3              # Blend with previous state
        self.max_valence_changes = 2    # Per 5 cycles
        self.smoothing_window = 5       # Cycles to average

    def stabilize(self, raw: FeltState, previous: FeltState) -> FeltState:
        """Apply inertia and smoothing to raw FeltState."""
```

---

## Phase 10: Valence-Tagged Knowledge

### Purpose

Encode urgency/importance IN the representation, not as separate lookup.

### Core Insight

> "Pain doesn't represent tissue damage then feel bad. Pain IS the representation in a format that includes 'STOP DOING THIS' as part of the encoding."

### Key Classes

```python
@dataclass
class ValenceTaggedValue:
    """Value with inherent urgency/importance encoding."""
    value: Any
    valence: Valence
    urgency: float           # 0.0-1.0 inherent urgency
    importance: float        # 0.0-1.0 inherent importance
    timestamp: float
    source: str = "unknown"

class ValenceSlotStore:
    """Store for valence-tagged values with O(1) aggregates."""

    def __init__(self):
        self._slots: Dict[str, ValenceTaggedValue] = {}
        self._urgency_sum: float = 0.0
        self._importance_sum: float = 0.0
        self._count: int = 0

    def write(self, key: str, value: Any, valence: Valence,
              urgency: float, importance: float) -> None:
        """Write value with valence tagging, update aggregates."""

    def get_aggregate_urgency(self) -> float:
        """O(1) average urgency across all tagged slots."""
        return self._urgency_sum / self._count if self._count > 0 else 0.0

    def get_aggregate_importance(self) -> float:
        """O(1) average importance across all tagged slots."""
        return self._importance_sum / self._count if self._count > 0 else 0.0

# Auto-tagging rules for known slots
CRITICAL_SLOT_VALENCE_RULES = {
    'cascade_failure': (Valence.THREAT, 1.0, 1.0),
    'action_budget_critical': (Valence.THREAT, 0.9, 0.8),
    'contradiction_detected': (Valence.CONFUSION, 0.7, 0.9),
    'discovery_made': (Valence.CURIOSITY, 0.3, 0.7),
    'goal_achieved': (Valence.MASTERY, 0.2, 1.0),
}
```

### Benefits

1. **No urgency lookup**: Eisenhower reads urgency from slot itself
2. **Context-appropriate**: Same fact has different urgency in different contexts
3. **O(1) aggregates**: Instant urgency/importance summary
4. **Matches biology**: This is how pain/pleasure actually work

---

## Phase 11: Phenomenology ↔ Graph Integration

### Purpose

Paths discovered under different FeltStates have different reliability. Track discovery context.

### Key Classes

```python
@dataclass
class ValenceWeightedEdge:
    """Edge that tracks FeltState context of discovery."""
    from_rung: str
    to_rung: str
    discovery_valence: Valence
    discovery_certainty: float
    traversal_count: int = 0
    success_count: int = 0

class GraphEvolution:
    """Enhanced with valence-weighted crystallization."""

    def record_traversal_with_feel(self, from_rung: str, to_rung: str,
                                    success: bool, felt: FeltState) -> None:
        """Record traversal with phenomenology context."""

    def get_crystallization_threshold(self, edge: ValenceWeightedEdge) -> int:
        """
        Dynamic threshold based on discovery valence:
        - MASTERY: 0.7x (crystallize faster - high confidence discovery)
        - NEUTRAL: 1.0x (standard threshold)
        - CONFUSION: 2.0x (more validation needed)
        - THREAT: 1.5x (panic discoveries need verification)
        """

@dataclass
class GameFeelTrajectory:
    """Track FeltState progression across a game."""
    game_id: str
    trajectory: List[FeltState]
    phase_boundaries: Dict[str, int]  # phase → tick when entered

    def detect_anomaly(self, current: FeltState, tick: int) -> Optional[str]:
        """Detect if current FeltState is anomalous for this phase."""
```

### Crystallization Thresholds

| Discovery Valence | Threshold Multiplier | Rationale |
|-------------------|---------------------|-----------|
| MASTERY | 0.7x | High confidence discovery, crystallize faster |
| CURIOSITY | 0.8x | Intentional exploration, slightly faster |
| NEUTRAL | 1.0x | Standard threshold |
| THREAT | 1.5x | Panic discovery, needs verification |
| CONFUSION | 2.0x | Lucky fluke, needs much more validation |

---

## Complete Decision Pipeline

### Per-Cycle Flow

```python
def route(self, game_state: Dict, context: Dict) -> RungResult:
    """Complete cognitive routing pipeline."""

    # 1. PHENOMENOLOGY: Compress to FeltState
    felt = self.phenomenology.compress()
    self.phenomenology.inject(felt)

    # 2. EPISTEMIC: Update quadrant
    transition = self.epistemic.update(last_result)
    quadrant = self.epistemic.get_current_quadrant()

    # 3. META-PLANNER: Select algorithm (modulated by FeltState)
    modulation = self.phenomenology.get_algorithm_modulation()
    algorithm = self.meta_planner.select_algorithm(
        self.blackboard, felt_state=felt
    )
    algorithm.apply_modulation(modulation)

    # 4. ALGORITHM: Get candidate rungs
    search_context = create_search_context(self.blackboard)
    candidates = algorithm.get_candidates(self.graph, search_context)

    # 5. EISENHOWER: Prioritize by urgency × importance
    # Apply FeltState bias to urgency/importance
    for candidate in candidates:
        candidate.urgency += felt.to_urgency_bias()
        candidate.importance += felt.to_importance_bias()

    prioritized = list(self.eisenhower.prioritize(candidates))

    if not prioritized:
        return self.fallback.get_escape_action(FailureType.EMPTY_FRONTIER)

    # 6. EXECUTE: Run highest priority rung (Q1)
    selected = prioritized[0]
    result = selected.rung.execute(game_state, self.blackboard)

    # 7. RECORD: Update graph evolution with FeltState context
    self.graph_evolution.record_traversal_with_feel(
        from_rung=last_rung,
        to_rung=selected.rung.name,
        success=result.confidence > 0.5,
        felt=felt
    )

    return result
```

### Feedback Loop

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          THE FEEDBACK LOOP                               │
│                                                                          │
│   High-D State ──► Compress ──► FeltState ──► Inject ──► High-D State   │
│        │              │             │            │             │         │
│        │              │             │            │             │         │
│        │              │             ▼            │             │         │
│        │              │      "How do I feel?"    │             │         │
│        │              │             │            │             │         │
│        │              │             ▼            │             │         │
│        │              │      Modulate behavior   │             │         │
│        │              │             │            │             │         │
│        └──────────────┴─────────────┴────────────┴─────────────┘         │
│                                                                          │
│   The system responds to its own compressed self-perception              │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## File Reference

### Core Cognitive Routing (`engines/cognition/`)

| File | LOC | Purpose |
|------|-----|---------|
| `blackboard.py` | ~1360 | Shared working memory with typed slots |
| `cognitive_router.py` | ~1100 | Main routing orchestrator |
| `cognitive_graph.py` | ~400 | Rungs as nodes, edges with trust |
| `meta_planner.py` | ~400 | Algorithm selection with caching |
| `algorithms.py` | ~500 | Search algorithms (Greedy, Targeted, etc.) |
| `epistemic_tracker.py` | ~200 | Rumsfeld state machine |
| `epistemic_state.py` | ~150 | Epistemic data structures |
| `eisenhower_layer.py` | ~635 | Urgency × importance prioritization |
| `phenomenology_layer.py` | ~782 | FeltState compression & feedback |
| `valence_tagged_slot.py` | ~683 | Valence as inherent property |
| `hysteresis.py` | ~150 | Transition stability |
| `question_manager.py` | ~200 | Question lifecycle |
| `edge_inference.py` | ~350 | Automatic edge discovery |
| `precomputation.py` | ~300 | Front-loaded O(1) lookups |
| `catastrophic_fallback.py` | ~200 | Circuit breaker |
| `routing_traces.py` | ~300 | Decision archaeology |
| `routing_metrics.py` | ~200 | A/B testing infrastructure |
| `epistemic_logging.py` | ~250 | Structured logging |

### Graph Evolution (`engines/reasoning/`)

| File | LOC | Purpose |
|------|-----|---------|
| `graph_evolution.py` | ~813 | Edge trust, crystallization, valence integration |
| `path_crystallization.py` | ~400 | Detect reliable paths |
| `process_knowledge.py` | ~450 | Abstract pattern extraction |
| `rung_roles.py` | ~300 | Rung role taxonomy |

### Tests (`tests/`)

| File | Tests | Purpose |
|------|-------|---------|
| `test_blackboard.py` | 37 | Blackboard operations |
| `test_epistemic_tracker.py` | 25 | Rumsfeld transitions |
| `test_epistemic_stability.py` | 18 | Hysteresis |
| `test_cognitive_graph.py` | 30 | Graph operations |
| `test_cognitive_router.py` | 50 | Full routing |
| `test_eisenhower_layer.py` | 33 | Q1-Q4 classification |
| `test_phenomenology_layer.py` | 32 | FeltState compression |
| `test_valence_tagged_slot.py` | 38 | Valence tagging |
| `test_graph_evolution.py` | 54 | Edge trust & crystallization |
| `test_phase5_validation.py` | 50 | Phase 5 validation |
| `test_phase6_production.py` | 42 | Phase 6 production |
| `test_phase7_evolution.py` | 45 | Phase 7 evolution |
| `test_phase75_stabilization.py` | 21 | Stabilization |

---

## Appendix: Migration from Legacy System

### What's Preserved

- **63+ Rungs**: All existing rungs work unchanged
- **ORDERING_PRESETS**: Still available but deprecated
- **Context dict**: Wrapped by Blackboard, backward compatible

### What's New

- **Dynamic routing**: Graph-based search replaces static ordering
- **Epistemic awareness**: System tracks its own knowledge state
- **Pragmatic prioritization**: Urgency × importance filtering
- **Affective feedback**: Phenomenology layer closes the loop
- **Long-term learning**: Paths crystallize, patterns transfer

### Deprecation Timeline

| Component | Status | Removal Target |
|-----------|--------|----------------|
| `ORDERING_PRESETS` | DEPRECATED | Phase 12 |
| `_decide_context_adaptive()` | DEPRECATED | Phase 12 |
| Direct context dict access | DEPRECATED | Phase 13 |

---

**End of Document**

*Last Updated: 2026-02-05*
*Version: 1.0*
*Status: All phases implemented and tested*
