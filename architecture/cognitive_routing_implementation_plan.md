# Cognitive Routing Implementation Plan

**Created**: 2026-02-03
**Updated**: 2026-02-03 (incorporated Parts 2, 3, 3.5, 4 & 5 - review refinements)
**Status**: DRAFT
**Source**: [cognitive routing solution.md](../DOCS/cognitive%20routing%20solution.md), [routing part 2.md](../DOCS/routing%20part%202.md), [routing part 3.md](../DOCS/routing%20part%203.md), [routing part 3 and a half.md](../DOCS/routing%20part%203%20and%20a%20half.md), [metaphor routing part 4.md](../DOCS/metaphor%20routing%20part%204.md), [routing part 5.md](../DOCS/routing%20part%205.md)
**Target**: Replace static ORDERING_PRESETS with dynamic graph-based routing

---

## Executive Summary

The cognitive routing solution proposes replacing fixed rung orderings with a **Blackboard + Meta-Planner + Cognitive Graph** architecture.

**Part 2 optimizations**:
1. **MetaPlannerCache** with bucketed keys for O(1) algorithm selection (90%+ cache hits)
2. **EdgeInferenceEngine** for automatic edge discovery (eliminates manual O(n²) work)
3. **Algorithm Portfolio** with domain-specific algorithms (TopologicalDP, Bidirectional, BeamSearch, etc.)
4. **PrecomputationManager** for front-loaded O(1) heuristic lookups

**Part 3 optimizations** (critical insight):
5. **EpistemicTracker** - Track KK/KU/UK/UU quadrants as a STATE MACHINE, not just classification
6. **Transition-Driven Switching** - Algorithm changes on epistemic TRANSITIONS (UU→KU, KU→KK, etc.)
7. **Quadrant-Specific Algorithms** - TargetedQuestionSearch (KU), RetrievalSearch (UK), GreedyExploitation (KK), InformationMaximizing (UU)
8. **Complexity Win**: O(26) typical case vs O(1500) static A* via early termination + focused search + exclusions

**Part 3.5 optimizations** (operational details):
9. **Hysteresis System** - Confirmation counts + cooldowns + signal decay to prevent quadrant thrashing
10. **Question Discovery Protocol** - Standardized `raises_questions` field in RungResult with question lifecycle
11. **UK Potential Index** - Precomputed bloom filter + relevance table for O(1) "might we know?" checks
12. **Structured Epistemic Logging** - EpistemicTraceEntry schema for queryable decision archaeology

**Part 4 insights** (graph evolution & process knowledge):
13. **Cumulative Edge Trust** - Edge weights accumulate across games, not just per-decision; graph evolves over time
14. **Rung Role Taxonomy** - Classify rungs by problem-solving role (entry/leverage/compounding/resolution), not just category
15. **Path Crystallization** - Detect when paths are traversed enough to become lookups instead of searches
16. **Process Knowledge Extraction** - Extract abstract patterns from successes, not just concrete rung sequences
17. **Negative Reputation Penalty** - KK→UU (contradiction) is worse than fresh start; apply trust penalty to failed path

**Part 5 refinements** (review-driven improvements):
18. **Epistemic Module Split** - epistemic_tracker.py split into 3 files (state/tracker/contradiction) for testability
19. **Question Taxonomy Grounding** - Auto-infer `answerable_by` from rung READ patterns, not just manual config
20. **UK Cold-Start Fallback** - Structural UK detection (network/cache metadata) for first game or new game types
21. **CatastrophicFallback Circuit Breaker** - Escape hatch for stuck loops, empty frontiers, contradiction storms
22. **Domain-Relative Crystallization** - Threshold = min(10, 50% of domain games) for rare game types
23. **Domain-Specific Process Patterns** - Track pattern success per domain, allow deviations from universal pattern
24. **Three-List Edge Validation** - Confident (auto-accept) / Uncertain (human review) / Missing (investigate)
25. **Stateless Algorithms with SearchContext** - Algorithms receive all context per call via injectable SearchContext
26. **Stabilization Weeks** - Add explicit stabilization weeks after Phase 4 and Phase 7
27. **Early Phase 7 Data Structures** - Define EdgeTrustRecord and CrystallizedPath in Phase 1 to avoid retrofit

This plan breaks implementation into 8 phases with validation gates and 2 stabilization weeks.

---

## Phase 0: Audit Current State (Week 1)

### 0.1 Inventory Existing Components

| Component | File | Status | Notes |
|-----------|------|--------|-------|
| 63+ Rungs | `decision_rung_system.py` | DONE | All implemented |
| 110+ Primitives | `seed_primitives.py` | DONE | Registered in categories |
| ORDERING_PRESETS | `decision_rung_system.py` | TO DEPRECATE | 9+ static orderings |
| Context dict | passed to `decide()` | AD-HOC | Untyped, scattered |
| Strategy selection | `_decide_context_adaptive()` | BASIC | Only replay/frontier/optimization |

### 0.2 Map Implicit Dependencies

Scan all 63 rungs for implicit dependencies (reads from context that another rung wrote):

```
survey           → writes: survey_complete, survey (context keys)
control_tracker  → reads: survey (needs objects found first)
event_understanding → reads: physics_game (from frame_interpretation)
theory_gate      → reads: working_theory (from scientific_method)
...
```

**Deliverable**: `architecture/rung_dependency_matrix.json` - explicit dependency graph

### 0.3 Identify Edge Relationships

For each rung pair, determine if relationship exists:

| From | To | Edge Type | Condition |
|------|----|-----------|-----------|
| survey | control_tracker | DEPENDENCY | Always |
| frame_interpretation | event_understanding | IMPLICATION | physics_game=True |
| network_wisdom | exploration_phase | FALLBACK | network_wisdom_empty |
| theory_gate | discovery_exploitation | CONTRADICTION | theory contradicts discovery |
| discovery_exploitation | hypothesis_testing | REFINEMENT | confidence < 0.7 |
| palette_detection | sparse_grid | COACTIVATION | Both early orientation |

**Deliverable**: `config/cognitive_edges.json` - 150-200 edges

### 0.4 Primitive → Blackboard Slot Mapping

Map each primitive category to blackboard slots it can populate:

| Primitive Category | Blackboard Slot | Example |
|--------------------|-----------------|---------|
| OBJECT_INTERACTION | slot[controlled_object] | test_object_control → confidence |
| ATTENTION | slot[novelty_score] | detect_change → change_pixels |
| METACOGNITION | slot[confidence_map] | get_confidence → per-domain |
| SPATIAL | slot[spatial_relations] | detect_adjacency → object pairs |

**Deliverable**: `architecture/primitive_to_slot_mapping.md`

### 0.5 Auto-Infer Question Taxonomy [NEW FROM PART 5]

**Problem**: `answerable_by` lists in RUNG_QUESTION_TEMPLATES could be 50% wrong initially.

**Solution**: Scan rung implementations for what slots they READ (not just write). A rung that reads `control_hypothesis` can probably ANSWER questions about control.

```python
# manual_tools/infer_answerable_by.py

def infer_answerable_by_from_reads():
    """
    Scan all rung implementations for slot reads.
    Generate answerable_by mapping from read patterns.
    """
    rung_reads = {}  # rung_name -> set of slots read

    for rung in ALL_RUNGS:
        reads = extract_slot_reads(rung.execute_function)
        rung_reads[rung.name] = reads

    # Invert: for each slot, which rungs read it?
    slot_to_readers = defaultdict(set)
    for rung_name, reads in rung_reads.items():
        for slot in reads:
            slot_to_readers[slot].add(rung_name)

    # Generate answerable_by
    question_taxonomy = {}
    for slot, readers in slot_to_readers.items():
        question_id = f"what_is_{slot}"
        question_taxonomy[question_id] = {
            "text": f"What is {slot.replace('_', ' ')}?",
            "answerable_by": list(readers),
            "inferred": True,  # Flag as auto-generated
        }

    return question_taxonomy

# Output goes to config/question_taxonomy_inferred.json
# Human validates, merges with RUNG_QUESTION_TEMPLATES
```

**Three-List Validation** (for question taxonomy and edges):
1. **Confident** (auto-accept): Rung explicitly reads slot, high confidence
2. **Uncertain** (human review): Rung might answer, needs verification
3. **Missing** (investigate): Expected from category but not found

**Deliverable**: `config/question_taxonomy_inferred.json`, validated `config/question_templates.json`

---

## Phase 1: Blackboard Core (Week 2)

### 1.1 Define Blackboard Data Structures

```python
# engines/cognition/blackboard.py

@dataclass
class BlackboardSlot:
    """Single slot in the cognitive blackboard."""
    value: Any
    confidence: float  # 0.0 to 1.0
    source_rung: str   # Which rung wrote this
    timestamp: int     # Action number when written
    ttl: Optional[int] = None  # Time-to-live in actions (None = permanent)

@dataclass
class RumsfeldAssessment:
    """Epistemological state of the agent."""
    known_knowns: List[str]      # High-confidence slots
    kk_confidence: float         # Aggregate confidence in KK
    known_unknowns: List[str]    # Questions we know we need answered
    ku_answerable_by: Dict[str, List[str]]  # question → rungs that might answer
    unknown_knowns_candidates: List[str]    # Rungs not yet tried
    uu_estimate: float           # 0.0 (familiar) to 1.0 (novel)

    def compute_routing_priority(self) -> str:
        """Determine which search strategy to use."""
        if self.uu_estimate > 0.7:
            return "EXPLORATION_FIRST"
        elif len(self.known_unknowns) > 5:
            return "INFORMATION_MAXIMIZING"
        elif self.kk_confidence > 0.8:
            return "EXPLOITATION_GREEDY"
        else:
            return "BALANCED_SEARCH"

class Blackboard:
    """Cognitive blackboard - shared working memory for all rungs."""

    def __init__(self):
        self._slots: Dict[str, BlackboardSlot] = {}
        self._history: List[Tuple[str, Any, int]] = []  # (key, value, timestamp)
        self._checkpoints: List[Dict[str, BlackboardSlot]] = []
        self._contradiction_stack: List[Dict[str, Any]] = []

    def slot(self, key: str, value: Any = None, **kwargs) -> Any:
        """Get or set a slot. Pass value=None to get, value=X to set."""
        if value is not None:
            self._slots[key] = BlackboardSlot(value=value, **kwargs)
            self._history.append((key, value, kwargs.get('timestamp', 0)))
        slot = self._slots.get(key)
        return slot.value if slot else None

    def checkpoint(self) -> int:
        """Save current state, return checkpoint ID."""
        import copy
        self._checkpoints.append(copy.deepcopy(self._slots))
        return len(self._checkpoints) - 1

    def restore(self, checkpoint_id: int) -> None:
        """Restore to a previous checkpoint (for backtracking)."""
        if 0 <= checkpoint_id < len(self._checkpoints):
            self._slots = copy.deepcopy(self._checkpoints[checkpoint_id])

    def rumsfeld_assessment(self, visited_rungs: Set[str], all_rungs: Set[str]) -> RumsfeldAssessment:
        """Compute current epistemological state."""
        # KK: slots with confidence > 0.8
        known_knowns = [k for k, v in self._slots.items() if v.confidence > 0.8]
        kk_confidence = sum(self._slots[k].confidence for k in known_knowns) / max(len(known_knowns), 1)

        # KU: explicit questions
        known_unknowns = self.slot('information_need') or []

        # UK: rungs not yet visited
        unknown_knowns_candidates = list(all_rungs - visited_rungs)

        # UU: estimate based on frame novelty and problem complexity
        complexity = self.slot('complexity') or 'MEDIUM'
        novelty = self.slot('novelty_score') or 0.5
        uu_estimate = 0.3 + (0.7 * novelty) if complexity == 'WICKED' else novelty * 0.5

        return RumsfeldAssessment(
            known_knowns=known_knowns,
            kk_confidence=kk_confidence,
            known_unknowns=known_unknowns,
            ku_answerable_by={},  # Populated from edge graph
            unknown_knowns_candidates=unknown_knowns_candidates,
            uu_estimate=uu_estimate,
        )
```

### 1.2 Integrate with Existing Context

The blackboard wraps and extends the current context dict:

```python
class Blackboard:
    def from_context(self, context: Dict[str, Any]) -> 'Blackboard':
        """Initialize blackboard from legacy context dict."""
        # Copy known context keys to typed slots
        if 'survey' in context:
            self.slot('survey_result', context['survey'], confidence=0.9, source_rung='survey')
        if 'controlled_object' in context:
            self.slot('control_hypothesis', context['controlled_object'], confidence=0.6, source_rung='control_tracker')
        # ... etc
        return self

    def to_context(self) -> Dict[str, Any]:
        """Export blackboard to legacy context dict for backward compat."""
        return {k: v.value for k, v in self._slots.items()}
```

**Deliverable**: `engines/cognition/blackboard.py` - 300 LOC

### 1.3 Early Phase 7 Data Structures [NEW FROM PART 5]

**Tactical Recommendation**: Define graph evolution data structures NOW in Phase 1, even if not populated until Phase 7. This avoids painful retrofit later.

```python
# engines/cognition/blackboard.py (additions for forward compatibility)

@dataclass
class EdgeTrustRecord:
    """
    Trust accumulated for a rung-to-rung edge over time.
    Defined in Phase 1, populated in Phase 7.
    """
    from_rung: str
    to_rung: str
    trust_score: float = 0.0        # Accumulated across games
    traversal_count: int = 0        # How often this edge was taken
    success_count: int = 0          # How often it led to positive outcome
    is_crystallized: bool = False   # True = proven, use as lookup not search
    last_updated_game: str = ""     # Last game that updated this

@dataclass
class CrystallizedPath:
    """
    A path proven reliable enough to become a lookup instead of search.
    Defined in Phase 1, populated in Phase 7.
    """
    path: List[str]                 # Rung sequence
    domain_tags: List[str]          # What game types this applies to
    traversal_count: int = 0        # How many times traversed
    avg_confidence: float = 0.0     # Average confidence at path end
    crystallized_at: Optional[str] = None  # Game ID when crystallized

class Blackboard:
    def __init__(self):
        # ... existing init ...

        # Phase 7 forward compatibility - define now, populate later
        self._edge_trust: Dict[Tuple[str, str], EdgeTrustRecord] = {}
        self._crystallized_paths: List[CrystallizedPath] = []

    def get_edge_trust(self, from_rung: str, to_rung: str) -> float:
        """Get trust for an edge. Returns 0.0 if not yet tracked."""
        key = (from_rung, to_rung)
        record = self._edge_trust.get(key)
        return record.trust_score if record else 0.0

    def lookup_crystallized_path(self, domain_tags: List[str]) -> Optional[List[str]]:
        """Check if there's a crystallized path for this domain."""
        for cp in self._crystallized_paths:
            if any(tag in cp.domain_tags for tag in domain_tags):
                return cp.path
        return None
```

**Why Now**: When CognitiveGraph and algorithms are built in later phases, they'll naturally integrate with these structures rather than needing a retrofit.

---

## Phase 1.5: Epistemic Tracker (Week 2.5) [NEW FROM PART 3]

### The Critical Insight: Rumsfeld as State Machine

**Part 3's key contribution**: The Rumsfeld matrix isn't just a classification - it's a **STATE MACHINE** where transitions drive algorithm selection.

```
          ┌──────────────────────────────────────────────────────────┐
          │                    RUMSFELD STATE MACHINE                 │
          │                                                           │
          │     KNOWN                        UNKNOWN                  │
          │    (to self)                    (to self)                │
          │                                                           │
          │   ┌─────────────────┐        ┌─────────────────┐         │
          │   │                 │        │                 │         │
          │   │       KK        │───────→│       KU        │         │
KNOWN     │   │   exploitation  │        │   targeted      │         │
(about    │   │                 │←───────│   search        │         │
world)    │   └────────┬────────┘        └────────┬────────┘         │
          │            │                          │                  │
          │            ↓                          ↓                  │
          │   ┌─────────────────┐        ┌─────────────────┐         │
          │   │                 │        │                 │         │
          │   │       UK        │───────→│       UU        │         │
UNKNOWN   │   │   retrieval     │        │   exploration   │         │
(about    │   │   search        │←───────│                 │         │
world)    │   └─────────────────┘        └─────────────────┘         │
          │                                                           │
          └──────────────────────────────────────────────────────────┘

Transitions trigger algorithm switches - NOT domain re-classification!
```

### 1.5.1 EpistemicState Data Structure

```python
# engines/cognition/epistemic_tracker.py

from dataclasses import dataclass, field
from typing import Dict, Set, List, Optional, Tuple
from enum import Enum

class EpistemicQuadrant(Enum):
    KK = "known_knowns"      # High confidence + verified knowledge
    KU = "known_unknowns"    # Know what we don't know (specific questions)
    UK = "unknown_knowns"    # Untapped cached/network knowledge
    UU = "unknown_unknowns"  # Novel territory, no framework yet

@dataclass
class KnownFact:
    """A fact we're confident about."""
    slot_name: str
    value: any
    confidence: float
    source_rung: str
    verified_at: int  # Action number when verified

@dataclass
class Question:
    """A specific question we know we need answered."""
    question_id: str
    description: str
    answerable_by: List[str]  # Rungs that might answer this
    priority: float
    asked_at: int

@dataclass
class EpistemicState:
    """
    Complete epistemic state of the agent at a moment.
    This is the STATE in the state machine.
    """
    # KK: What we know with high confidence
    known_knowns: Dict[str, KnownFact] = field(default_factory=dict)
    kk_confidence: float = 0.0

    # KU: Specific questions we know we need answered
    known_unknowns: Dict[str, Question] = field(default_factory=dict)
    ku_urgency: float = 0.0  # How urgently we need answers

    # UK: Cached/network knowledge not yet accessed
    unknown_knowns: Set[str] = field(default_factory=set)  # Rung names
    uk_potential: float = 0.0  # Estimated value of untapped knowledge

    # UU: Estimate of unexplored territory
    uu_estimate: float = 0.5  # 0.0 = fully known, 1.0 = totally novel

    # Primary quadrant determines base algorithm
    primary_quadrant: EpistemicQuadrant = EpistemicQuadrant.UU

    def compute_primary_quadrant(self) -> EpistemicQuadrant:
        """Determine which quadrant dominates current state."""
        # Priority order: UK (quick wins) > KU (targeted) > UU (explore) > KK (exploit)
        if self.uk_potential > 0.5 and len(self.unknown_knowns) > 3:
            return EpistemicQuadrant.UK
        if len(self.known_unknowns) >= 2 and self.ku_urgency > 0.4:
            return EpistemicQuadrant.KU
        if self.uu_estimate > 0.6:
            return EpistemicQuadrant.UU
        if self.kk_confidence > 0.7:
            return EpistemicQuadrant.KK
        return EpistemicQuadrant.UU  # Default to exploration

@dataclass
class EpistemicTransition:
    """A transition between epistemic states."""
    from_quadrant: EpistemicQuadrant
    to_quadrant: EpistemicQuadrant
    trigger_rung: str
    trigger_result: any
    timestamp: int
```

### 1.5.2 EpistemicTracker: The State Machine

```python
class EpistemicTracker:
    """
    Tracks epistemic state and detects TRANSITIONS.
    This is the core of Part 3's insight.
    """

    def __init__(self):
        self.current_state = EpistemicState()
        self.history: List[EpistemicState] = []
        self.transitions: List[EpistemicTransition] = []
        self._last_quadrant = EpistemicQuadrant.UU

    def update_from_rung_result(
        self,
        rung_name: str,
        result: 'RungResult',
        blackboard: 'Blackboard',
        all_rungs: Set[str],
        visited_rungs: Set[str]
    ) -> List[EpistemicTransition]:
        """
        Update epistemic state after rung execution.
        Returns any transitions that occurred.
        """
        transitions = []

        # Snapshot current state
        old_quadrant = self.current_state.primary_quadrant

        # === Update KK (Known Knowns) ===
        if result.confidence > 0.8:
            self.current_state.known_knowns[result.slot_name] = KnownFact(
                slot_name=result.slot_name,
                value=result.value,
                confidence=result.confidence,
                source_rung=rung_name,
                verified_at=blackboard.slot('action_count') or 0
            )

        # Recalculate KK aggregate confidence
        if self.current_state.known_knowns:
            self.current_state.kk_confidence = sum(
                f.confidence for f in self.current_state.known_knowns.values()
            ) / len(self.current_state.known_knowns)

        # === Update KU (Known Unknowns) ===
        # Rung may answer existing questions
        answered = []
        for q_id, question in self.current_state.known_unknowns.items():
            if rung_name in question.answerable_by and result.confidence > 0.6:
                answered.append(q_id)
        for q_id in answered:
            del self.current_state.known_unknowns[q_id]

        # Rung may raise NEW questions
        if hasattr(result, 'raises_questions'):
            for q in result.raises_questions:
                self.current_state.known_unknowns[q.question_id] = q

        # === Update UK (Unknown Knowns) ===
        # Remove visited rungs from UK
        self.current_state.unknown_knowns = all_rungs - visited_rungs
        # Filter to only those with cached/network knowledge
        self.current_state.unknown_knowns = {
            r for r in self.current_state.unknown_knowns
            if self._has_cached_knowledge(r, blackboard)
        }
        self.current_state.uk_potential = len(self.current_state.unknown_knowns) / max(len(all_rungs), 1)

        # === Update UU (Unknown Unknowns) ===
        # Decreases as we learn, increases on contradictions/surprises
        if result.confidence > 0.5:
            self.current_state.uu_estimate *= 0.9  # Learning reduces UU
        if hasattr(result, 'surprise_level') and result.surprise_level > 0.7:
            self.current_state.uu_estimate = min(1.0, self.current_state.uu_estimate + 0.2)

        # === Detect Transitions ===
        new_quadrant = self.current_state.compute_primary_quadrant()
        self.current_state.primary_quadrant = new_quadrant

        if new_quadrant != old_quadrant:
            transition = EpistemicTransition(
                from_quadrant=old_quadrant,
                to_quadrant=new_quadrant,
                trigger_rung=rung_name,
                trigger_result=result,
                timestamp=blackboard.slot('action_count') or 0
            )
            transitions.append(transition)
            self.transitions.append(transition)
            self._last_quadrant = new_quadrant

        # Save history
        self.history.append(self._copy_state())

        return transitions

    def _has_cached_knowledge(self, rung_name: str, blackboard: 'Blackboard') -> bool:
        """Check if rung has cached/network knowledge to offer."""
        # Check if network wisdom exists for this rung's domain
        network_cache = blackboard.slot('network_wisdom_cache') or {}
        return rung_name in network_cache or rung_name.startswith('network_')

    def _copy_state(self) -> EpistemicState:
        """Deep copy current state for history."""
        import copy
        return copy.deepcopy(self.current_state)

    def get_transition_pattern(self, last_n: int = 5) -> str:
        """Get string pattern of recent transitions for pattern matching."""
        if len(self.transitions) < last_n:
            return "->".join(t.to_quadrant.name for t in self.transitions)
        return "->".join(t.to_quadrant.name for t in self.transitions[-last_n:])
```

### 1.5.3 Transition Response Map

```python
# The heart of Part 3: Transitions drive algorithm selection

TRANSITION_RESPONSES = {
    # === Discovery Transitions ===
    (EpistemicQuadrant.UU, EpistemicQuadrant.KU): {
        "algorithm": "TargetedQuestionSearch",
        "action": "focus",
        "description": "Found a specific question - switch to targeted search",
        "params": {"use_answerer_heuristic": True}
    },
    (EpistemicQuadrant.KU, EpistemicQuadrant.KK): {
        "algorithm": "GreedyExploitation",
        "action": "exploit",
        "description": "Question answered with confidence - exploit knowledge",
        "params": {"commit_threshold": 0.8}
    },
    (EpistemicQuadrant.UK, EpistemicQuadrant.KK): {
        "algorithm": "GreedyExploitation",
        "action": "exploit",
        "description": "Retrieved cached knowledge - exploit it",
        "params": {"commit_threshold": 0.8}
    },

    # === Contradiction / Regression Transitions ===
    (EpistemicQuadrant.KK, EpistemicQuadrant.KU): {
        "algorithm": "BacktrackingTargetedSearch",
        "action": "backtrack_and_target",
        "description": "Mild contradiction - backtrack and re-target",
        "params": {"backtrack_depth": 1, "exclude_last": True}
    },
    (EpistemicQuadrant.KK, EpistemicQuadrant.UU): {
        "algorithm": "ExplorationWithExclusions",
        "action": "reset_and_explore",
        "description": "Severe contradiction - reset and explore with exclusions",
        "params": {"exclude_failed_path": True, "boost_novel_rungs": True}
    },

    # === Stagnation Transitions ===
    (EpistemicQuadrant.UU, EpistemicQuadrant.UU): {
        "algorithm": "InformationMaximizingSearch",
        "action": "widen",
        "description": "Stuck in exploration - widen search with UCB",
        "params": {"exploration_bonus": 1.5, "curiosity_weight": 0.3}
    },
    (EpistemicQuadrant.KU, EpistemicQuadrant.KU): {
        "algorithm": "AlternateQuestionSearch",
        "action": "pivot",
        "description": "Question unanswerable - try different question",
        "params": {"deprioritize_current": True}
    },

    # === Retrieval Transitions ===
    (EpistemicQuadrant.UU, EpistemicQuadrant.UK): {
        "algorithm": "RetrievalSearch",
        "action": "retrieve",
        "description": "Realized we have cached knowledge - retrieve it",
        "params": {"query_network_first": True}
    },
    (EpistemicQuadrant.KU, EpistemicQuadrant.UK): {
        "algorithm": "RetrievalSearch",
        "action": "retrieve",
        "description": "Found relevant cached knowledge for question",
        "params": {"filter_by_question": True}
    },
}

def get_algorithm_for_transition(transition: EpistemicTransition) -> Dict:
    """Look up response for a given transition."""
    key = (transition.from_quadrant, transition.to_quadrant)
    return TRANSITION_RESPONSES.get(key, {
        "algorithm": "LandmarkAStar",
        "action": "continue",
        "description": "Unknown transition - use general search"
    })
```

### 1.5.4 Quadrant-Specific Algorithms

```python
# engines/cognition/algorithms.py (additions for Part 3)

class TargetedQuestionSearch(SearchAlgorithm):
    """
    KU quadrant: We know what we don't know - search toward answerers.
    A* with heuristic pointing at rungs that can answer our questions.
    """

    def __init__(self, questions: Dict[str, Question]):
        self.questions = questions
        self._answerer_distances: Dict[str, float] = {}

    def get_next_rungs(self, graph: CognitiveGraph, blackboard: Blackboard) -> List[str]:
        if not self.questions:
            return []  # Fall back to general search

        frontier = graph.get_frontier(blackboard)
        if not frontier:
            return []

        # Score by: how many questions can this rung answer?
        scored = []
        for rung in frontier:
            score = 0.0
            for q_id, question in self.questions.items():
                if rung in question.answerable_by:
                    score += question.priority
            # Add distance heuristic if precomputed
            if self._precomputed:
                for q_id, question in self.questions.items():
                    for answerer in question.answerable_by:
                        dist = self._precomputed.get("landmark_distances", {}).get(rung, {}).get(answerer, 10.0)
                        score += 1.0 / (dist + 1)  # Closer = higher score
            scored.append((score, rung))

        scored.sort(reverse=True)
        return [scored[0][1]] if scored else []

class RetrievalSearch(SearchAlgorithm):
    """
    UK quadrant: We have cached/network knowledge - go get it.
    Greedy toward network_wisdom and cache-heavy rungs.
    """

    RETRIEVAL_RUNGS = {"network_wisdom", "hypothesis_retrieval", "pattern_lookup",
                       "cached_sequence", "winning_sequence_replay"}

    def get_next_rungs(self, graph: CognitiveGraph, blackboard: Blackboard) -> List[str]:
        frontier = graph.get_frontier(blackboard)

        # Prioritize retrieval rungs
        retrieval_frontier = [r for r in frontier if r in self.RETRIEVAL_RUNGS]
        if retrieval_frontier:
            return [retrieval_frontier[0]]

        # Otherwise head toward nearest retrieval rung
        return self._navigate_toward_retrieval(graph, blackboard, frontier)

class GreedyExploitation(SearchAlgorithm):
    """
    KK quadrant: High confidence - exploit aggressively.
    Skip hypothesis testing, go straight to action.
    """

    EXPLOITATION_RUNGS = {"smart_action_selection", "action_execution",
                          "confident_commit", "optimal_sequence"}

    def __init__(self, commit_threshold: float = 0.8):
        self.commit_threshold = commit_threshold

    def get_next_rungs(self, graph: CognitiveGraph, blackboard: Blackboard) -> List[str]:
        # If already above threshold, go to commit
        if (blackboard.slot("max_confidence") or 0) > self.commit_threshold:
            for rung in self.EXPLOITATION_RUNGS:
                if rung in graph.get_frontier(blackboard):
                    return [rung]

        # Otherwise greedy toward highest confidence gain
        frontier = graph.get_frontier(blackboard)
        scored = [(self._expected_confidence(r, blackboard), r) for r in frontier]
        scored.sort(reverse=True)
        return [scored[0][1]] if scored else []

class ExplorationWithExclusions(SearchAlgorithm):
    """
    KK→UU transition: Severe contradiction - explore but exclude failed path.
    """

    def __init__(self, excluded_rungs: Set[str], exploration_bonus: float = 1.5):
        self.excluded = excluded_rungs
        self.bonus = exploration_bonus

    def get_next_rungs(self, graph: CognitiveGraph, blackboard: Blackboard) -> List[str]:
        frontier = graph.get_frontier(blackboard)

        # Remove excluded rungs
        frontier = [r for r in frontier if r not in self.excluded]

        if not frontier:
            return []  # Dead end - need human intervention

        # Score by novelty (inverse of visit count) with exploration bonus
        visit_counts = blackboard.slot("rung_visit_counts") or {}
        scored = []
        for rung in frontier:
            novelty = 1.0 / (visit_counts.get(rung, 0) + 1)
            info_gain = self._estimate_info_gain(rung, blackboard)
            score = (novelty * self.bonus) + info_gain
            scored.append((score, rung))

        scored.sort(reverse=True)
        return [scored[0][1]]

class BacktrackingTargetedSearch(SearchAlgorithm):
    """
    KK→KU transition: Mild contradiction - backtrack and re-target.
    Combines BacktrackingSearch with TargetedQuestionSearch.
    """

    def __init__(self, checkpoint_id: int, new_questions: Dict[str, Question]):
        self.checkpoint_id = checkpoint_id
        self.questions = new_questions

    def get_next_rungs(self, graph: CognitiveGraph, blackboard: Blackboard) -> List[str]:
        # Restore checkpoint
        blackboard.restore(self.checkpoint_id)

        # Now use targeted search for the new questions
        targeted = TargetedQuestionSearch(self.questions)
        return targeted.get_next_rungs(graph, blackboard)
```

**Deliverable**: Split into 3 files per Part 5 recommendation:
- `engines/cognition/epistemic_state.py` - Data structures only (~150 LOC)
- `engines/cognition/epistemic_tracker.py` - Transition detection (~200 LOC)
- `engines/cognition/contradiction_detector.py` - KK→KU/UU logic (~150 LOC)

**Why Split**: Makes unit testing tractable. Each file has single responsibility.

---

## Phase 1.6: Epistemic Stability & Observability (Week 2.6) [NEW FROM PART 3.5]

Part 3.5 addresses four operational concerns: hysteresis, question discovery, UK detection, and logging.

### 1.6.1 Hysteresis System: Preventing Quadrant Thrashing

**Problem**: System might oscillate rapidly: KK→KU→KK→KU→KK...

**Solution**: Confirmation counts + cooldowns + signal decay.

```python
# engines/cognition/hysteresis.py (split from epistemic_tracker per Part 5)

@dataclass
class TransitionGate:
    """Gate that prevents premature transitions."""
    # Confirmation counts needed before allowing transition
    CONFIRMATIONS_REQUIRED = {
        (EpistemicQuadrant.UU, EpistemicQuadrant.KU): 1,  # Questions are cheap
        (EpistemicQuadrant.KU, EpistemicQuadrant.KK): 2,  # Need solid answer
        (EpistemicQuadrant.KK, EpistemicQuadrant.KU): 2,  # Don't abandon hastily
        (EpistemicQuadrant.KK, EpistemicQuadrant.UU): 3,  # Nuclear option
        (EpistemicQuadrant.UK, EpistemicQuadrant.KK): 1,  # Retrieval is fast
        (EpistemicQuadrant.UU, EpistemicQuadrant.UK): 1,  # Retrieval is cheap
    }

    # Cooldown: After leaving quadrant, can't return for N ticks
    COOLDOWN_TICKS = {
        EpistemicQuadrant.KK: 3,  # Prevent KK→KU→KK ping-pong
        EpistemicQuadrant.KU: 2,
        EpistemicQuadrant.UK: 1,
        EpistemicQuadrant.UU: 0,  # Always allow return to exploration
    }

class HysteresisManager:
    """Manages transition stability with confirmations, cooldowns, and decay."""

    def __init__(self):
        self.pending_signals: Dict[Tuple[EpistemicQuadrant, EpistemicQuadrant], List[float]] = defaultdict(list)
        self.cooldowns: Dict[EpistemicQuadrant, int] = {}  # quadrant -> tick when cooldown expires
        self.current_tick: int = 0

    def record_signal(self, from_q: EpistemicQuadrant, to_q: EpistemicQuadrant) -> bool:
        """
        Record a signal suggesting transition. Returns True if transition should fire.
        """
        key = (from_q, to_q)

        # Check cooldown
        if to_q in self.cooldowns and self.current_tick < self.cooldowns[to_q]:
            return False  # On cooldown, ignore signal

        # Record signal with timestamp
        self.pending_signals[key].append(self.current_tick)

        # Apply signal decay (signals older than 10 ticks fade)
        self.pending_signals[key] = [
            t for t in self.pending_signals[key]
            if self.current_tick - t < 10
        ]

        # Check if we have enough confirmations
        required = TransitionGate.CONFIRMATIONS_REQUIRED.get(key, 2)
        if len(self.pending_signals[key]) >= required:
            # Transition approved - clear signals and set cooldown for origin
            self.pending_signals[key] = []
            cooldown_ticks = TransitionGate.COOLDOWN_TICKS.get(from_q, 2)
            self.cooldowns[from_q] = self.current_tick + cooldown_ticks
            return True

        return False

    def tick(self):
        """Advance time by one tick."""
        self.current_tick += 1
```

### 1.6.2 Question Discovery Protocol

**Problem**: Rungs need a standardized way to declare questions they can't answer.

**Solution**: `raises_questions` field in RungResult + question lifecycle.

```python
# engines/cognition/question_manager.py

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional

class QuestionStatus(Enum):
    RAISED = "raised"          # Just discovered
    ACTIVE = "active"          # Being pursued
    ANSWERED = "answered"      # Got satisfactory answer
    ABANDONED = "abandoned"    # Gave up after too many attempts
    DEMOTED = "demoted"        # Low priority after 3+ failed attempts

@dataclass
class Question:
    """A specific question we know we need answered."""
    question_id: str
    text: str                           # Human-readable question
    answerable_by: List[str]            # Rungs that might answer this
    priority: float = 0.5               # 0.0 to 1.0
    status: QuestionStatus = QuestionStatus.RAISED
    asked_at: int = 0                   # Tick when first raised
    attempts: int = 0                   # How many times we've tried to answer
    context: Dict = field(default_factory=dict)  # Additional context

# Common question patterns by rung category
RUNG_QUESTION_TEMPLATES = {
    "survey": [
        Question(question_id="what_objects", text="What are these objects?",
                 answerable_by=["frame_interpretation", "pattern_detection"]),
        Question(question_id="whats_interactive", text="What's interactive?",
                 answerable_by=["control_tracker", "discovery_exploitation"]),
    ],
    "frame_interpretation": [
        Question(question_id="physics_or_turn", text="Is this physics or turn-based?",
                 answerable_by=["event_understanding", "physics_detection"]),
        Question(question_id="what_changed", text="What caused that change?",
                 answerable_by=["event_understanding", "causal_analysis"]),
    ],
    "control_tracker": [
        Question(question_id="control_correct", text="Is my control hypothesis correct?",
                 answerable_by=["hypothesis_testing", "discovery_exploitation"]),
    ],
    "hypothesis_testing": [
        Question(question_id="rule_generalizes", text="Does this rule generalize?",
                 answerable_by=["abstraction_testing", "rule_transfer"]),
    ],
}

class QuestionManager:
    """Manages question lifecycle."""

    def __init__(self):
        self.questions: Dict[str, Question] = {}
        self.answered_questions: List[str] = []  # History of answered IDs

    def raise_question(self, question: Question, current_tick: int):
        """Add a new question or update priority if exists."""
        if question.question_id in self.questions:
            # Boost priority if re-raised
            self.questions[question.question_id].priority = min(
                1.0, self.questions[question.question_id].priority + 0.1
            )
        else:
            question.asked_at = current_tick
            question.status = QuestionStatus.ACTIVE
            self.questions[question.question_id] = question

    def record_attempt(self, question_id: str, succeeded: bool, confidence: float):
        """Record an attempt to answer a question."""
        if question_id not in self.questions:
            return

        q = self.questions[question_id]
        q.attempts += 1

        if succeeded and confidence > 0.6:
            q.status = QuestionStatus.ANSWERED
            self.answered_questions.append(question_id)
            del self.questions[question_id]
        elif q.attempts >= 3 and not succeeded:
            q.status = QuestionStatus.DEMOTED
            q.priority *= 0.5  # Halve priority

    def get_active_questions(self) -> List[Question]:
        """Get all active questions sorted by priority."""
        active = [q for q in self.questions.values()
                  if q.status in (QuestionStatus.ACTIVE, QuestionStatus.DEMOTED)]
        return sorted(active, key=lambda q: q.priority, reverse=True)
```

### 1.6.3 UK Potential Index: Precomputed "What Might We Know?"

**Problem**: Checking "do I have cached knowledge?" requires DB queries. Too slow.

**Solution**: Maintain a lightweight UK Potential Index updated asynchronously.

```python
# engines/cognition/uk_potential_index.py

from dataclasses import dataclass
from typing import Dict, Set, Optional
import mmh3  # MurmurHash for bloom filter

@dataclass
class UKEntry:
    """Entry in the UK Potential Index."""
    rung_name: str
    has_cached: bool
    cache_count: int         # Number of cached items
    relevance: float         # 0.0 to 1.0, relevance to current game
    last_updated: int        # Tick when last refreshed

class UKPotentialIndex:
    """
    Lightweight index for O(1) "might we know?" checks.
    Updated asynchronously, not during routing.
    """

    def __init__(self):
        self.index: Dict[str, UKEntry] = {}
        self.bloom_filter: bytearray = bytearray(1024)  # 8KB bloom filter
        self._bloom_hash_count = 3

    def populate_for_game(self, game_id: str, game_type: str, db_connection):
        """
        Populate index at game start. Queries DB once, not during routing.
        """
        # Clear old index
        self.index.clear()
        self._reset_bloom()

        # Query what's available
        available = self._query_cached_knowledge(db_connection, game_id, game_type)

        for rung_name, cache_info in available.items():
            self.index[rung_name] = UKEntry(
                rung_name=rung_name,
                has_cached=cache_info['count'] > 0,
                cache_count=cache_info['count'],
                relevance=cache_info['relevance'],
                last_updated=0
            )
            if cache_info['count'] > 0:
                self._bloom_add(rung_name)

    def has_potential(self, rung_name: str, min_relevance: float = 0.3) -> bool:
        """
        O(1) check: Does this rung have cached knowledge worth accessing?
        """
        # Fast bloom filter check first
        if not self._bloom_might_contain(rung_name):
            return False  # Definitely no

        # Check index
        entry = self.index.get(rung_name)
        if not entry:
            return False

        return entry.has_cached and entry.relevance >= min_relevance

    def mark_surfaced(self, rung_name: str):
        """Mark that cached knowledge was accessed (UK → KK)."""
        if rung_name in self.index:
            self.index[rung_name].has_cached = False  # No longer "unknown"

    def _bloom_add(self, item: str):
        """Add item to bloom filter."""
        for i in range(self._bloom_hash_count):
            idx = mmh3.hash(item, i) % (len(self.bloom_filter) * 8)
            self.bloom_filter[idx // 8] |= (1 << (idx % 8))

    def _bloom_might_contain(self, item: str) -> bool:
        """Check if item might be in bloom filter."""
        for i in range(self._bloom_hash_count):
            idx = mmh3.hash(item, i) % (len(self.bloom_filter) * 8)
            if not (self.bloom_filter[idx // 8] & (1 << (idx % 8))):
                return False
        return True

    def _reset_bloom(self):
        """Reset bloom filter."""
        self.bloom_filter = bytearray(1024)

    def _query_cached_knowledge(self, db, game_id: str, game_type: str) -> Dict:
        """Query DB for available cached knowledge. Called once per game."""
        # Example query structure
        return {
            "network_wisdom": {"count": 142, "relevance": 0.8},
            "prior_lessons": {"count": 3, "relevance": 0.9},
            "embedding_suggestion": {"count": 50, "relevance": 0.6},
            "rule_transfer": {"count": 0, "relevance": 0.0},
            "abstraction_templates": {"count": 2, "relevance": 0.5},
        }

    # === COLD-START FALLBACK [NEW FROM PART 5] ===

    # Structural UK metadata - used when DB is empty (first game, new game type)
    STRUCTURAL_UK_RUNGS = {
        "network_wisdom": {"has_network_component": True, "always_worth_trying": True},
        "prior_lessons": {"has_cache": True},
        "embedding_suggestion": {"has_cache": True},
        "rule_transfer": {"has_network_component": True},
        "abstraction_templates": {"has_network_component": True},
        "global_game_patterns": {"has_network_component": True},
        "similar_game_lookup": {"has_cache": True},
    }

    def populate_structural_fallback(self):
        """
        Fallback for cold-start: first game ever or new game type never seen.
        Uses structural metadata about which rungs COULD have knowledge.
        """
        for rung_name, metadata in self.STRUCTURAL_UK_RUNGS.items():
            self.index[rung_name] = UKEntry(
                rung_name=rung_name,
                has_cached=True,  # Assume yes until proven otherwise
                cache_count=0,    # Unknown count
                relevance=0.5,    # Default relevance
                last_updated=0,
            )
            self._bloom_add(rung_name)

    def is_cold_start(self, db_result: Dict) -> bool:
        """Check if this is a cold-start situation."""
        return all(info['count'] == 0 for info in db_result.values())
```

### 1.6.4 Structured Epistemic Logging

**Problem**: Need to debug "why did it make that decision?" after the fact.

**Solution**: Structured EpistemicTraceEntry for queryable decision archaeology.

```python
# engines/cognition/epistemic_logging.py

from dataclasses import dataclass, asdict
from typing import List, Optional
import json

@dataclass
class EpistemicTraceEntry:
    """Single entry in epistemic trace log."""
    tick: int
    quadrant: str                           # UU/KU/KK/UK
    transition: Optional[str]               # e.g., "UU→KU" or None
    transition_trigger: Optional[str]       # What caused it
    algorithm: str                          # Current search algorithm
    algorithm_switch: Optional[str]         # e.g., "InfoMax→Targeted"
    rung_executed: str
    rung_result_summary: str
    confidence_before: float
    confidence_after: float
    questions_raised: List[str]
    questions_answered: List[str]
    contradictions: List[str]
    kk_count: int                           # Number of known facts
    ku_count: int                           # Number of open questions
    uu_estimate: float                      # Unknown-unknowns estimate

class EpistemicLogger:
    """Structured logging for epistemic traces."""

    def __init__(self, game_id: str, agent_id: str):
        self.game_id = game_id
        self.agent_id = agent_id
        self.traces: List[EpistemicTraceEntry] = []
        self._last_algorithm = "InfoMax"

    def log(self, entry: EpistemicTraceEntry):
        """Log an epistemic trace entry."""
        self.traces.append(entry)

        # Also write to structured log for real-time monitoring
        log_line = json.dumps(asdict(entry))
        # Would write to database or log file

    def log_from_state(
        self,
        tick: int,
        state: 'EpistemicState',
        transition: Optional['EpistemicTransition'],
        rung_executed: str,
        rung_result: 'RungResult',
        algorithm_name: str
    ):
        """Convenience method to log from current state."""
        algorithm_switch = None
        if algorithm_name != self._last_algorithm:
            algorithm_switch = f"{self._last_algorithm}→{algorithm_name}"
            self._last_algorithm = algorithm_name

        entry = EpistemicTraceEntry(
            tick=tick,
            quadrant=state.primary_quadrant.name,
            transition=f"{transition.from_quadrant.name}→{transition.to_quadrant.name}" if transition else None,
            transition_trigger=transition.trigger_rung if transition else None,
            algorithm=algorithm_name,
            algorithm_switch=algorithm_switch,
            rung_executed=rung_executed,
            rung_result_summary=str(rung_result)[:100],
            confidence_before=getattr(rung_result, 'confidence_before', 0.0),
            confidence_after=getattr(rung_result, 'confidence', 0.0),
            questions_raised=[q.question_id for q in getattr(rung_result, 'raises_questions', [])],
            questions_answered=getattr(rung_result, 'answers_questions', []),
            contradictions=getattr(rung_result, 'contradictions', []),
            kk_count=len(state.known_knowns),
            ku_count=len(state.known_unknowns),
            uu_estimate=state.uu_estimate,
        )
        self.log(entry)

    def get_summary(self) -> Dict:
        """Get summary statistics for dashboard."""
        if not self.traces:
            return {}

        transitions_by_type = {}
        for t in self.traces:
            if t.transition:
                transitions_by_type[t.transition] = transitions_by_type.get(t.transition, 0) + 1

        return {
            "total_ticks": len(self.traces),
            "transitions": transitions_by_type,
            "final_quadrant": self.traces[-1].quadrant,
            "avg_confidence": sum(t.confidence_after for t in self.traces) / len(self.traces),
            "question_resolution_rate": self._calc_question_resolution_rate(),
            "thrashing_score": self._calc_thrashing_score(),
        }

    def _calc_question_resolution_rate(self) -> float:
        """Calculate percentage of questions that got answered."""
        raised = sum(len(t.questions_raised) for t in self.traces)
        answered = sum(len(t.questions_answered) for t in self.traces)
        return answered / max(raised, 1)

    def _calc_thrashing_score(self) -> float:
        """
        Calculate thrashing score (0.0 = stable, 1.0 = highly unstable).
        Based on how often quadrant changes.
        """
        if len(self.traces) < 2:
            return 0.0
        changes = sum(1 for i in range(1, len(self.traces))
                      if self.traces[i].quadrant != self.traces[i-1].quadrant)
        return changes / (len(self.traces) - 1)

# Database schema for traces
EPISTEMIC_TRACE_SCHEMA = """
CREATE TABLE IF NOT EXISTS epistemic_traces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    decision_id TEXT NOT NULL,
    tick INTEGER NOT NULL,
    quadrant TEXT NOT NULL,
    transition TEXT,
    algorithm TEXT NOT NULL,
    rung_executed TEXT NOT NULL,
    confidence_after REAL,
    kk_count INTEGER,
    ku_count INTEGER,
    uu_estimate REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games(id)
);

CREATE INDEX idx_epistemic_traces_game ON epistemic_traces(game_id);
CREATE INDEX idx_epistemic_traces_quadrant ON epistemic_traces(quadrant);
CREATE INDEX idx_epistemic_traces_transition ON epistemic_traces(transition);
"""
```

**Deliverables**:
- `engines/cognition/hysteresis.py` - 150 LOC
- `engines/cognition/question_manager.py` - 200 LOC
- `engines/cognition/uk_potential_index.py` - 200 LOC
- `engines/cognition/epistemic_logging.py` - 250 LOC

### 2.1 Define Edge Types

```python
# engines/cognition/cognitive_graph.py

class EdgeType(Enum):
    DEPENDENCY = "dependency"      # B requires A's output
    IMPLICATION = "implication"    # If A says X, consider B
    CONTRADICTION = "contradiction"  # A and B conflict
    REFINEMENT = "refinement"      # B refines A's answer
    FALLBACK = "fallback"          # If A fails, try B
    COACTIVATION = "coactivation"  # A and B should run together

@dataclass
class CognitiveEdge:
    source: str          # Source rung name
    target: str          # Target rung name
    edge_type: EdgeType
    base_cost: float = 1.0       # Compute cost
    base_info_gain: float = 0.5  # Expected information gain
    condition: Optional[str] = None  # Blackboard slot condition (e.g., "physics_game")
    condition_value: Any = True  # Value that activates this edge

    def is_active(self, blackboard: Blackboard) -> bool:
        """Check if this edge's condition is met."""
        if self.condition is None:
            return True
        return blackboard.slot(self.condition) == self.condition_value
```

### 2.2 Build Graph from Configuration

```python
class CognitiveGraph:
    """Graph of rungs connected by cognitive edges."""

    def __init__(self, rungs: Dict[str, DecisionRung], edges_config: str):
        self.nodes = rungs
        self.edges = self._load_edges(edges_config)
        self._adjacency: Dict[str, List[CognitiveEdge]] = defaultdict(list)
        for edge in self.edges:
            self._adjacency[edge.source].append(edge)

    def _load_edges(self, config_path: str) -> List[CognitiveEdge]:
        """Load edges from JSON config."""
        with open(config_path) as f:
            data = json.load(f)
        return [CognitiveEdge(**e) for e in data['edges']]

    def get_frontier(self, blackboard: Blackboard) -> List[str]:
        """Get rungs reachable from current state."""
        visited = set(blackboard.slot('visited_rungs') or [])
        frontier = []

        for name, rung in self.nodes.items():
            if name in visited:
                continue
            # Check if all dependencies are satisfied
            if self._dependencies_satisfied(name, visited):
                frontier.append(name)

        return frontier

    def _dependencies_satisfied(self, rung_name: str, visited: Set[str]) -> bool:
        """Check if all DEPENDENCY edges to this rung are satisfied."""
        for edge in self.edges:
            if edge.target == rung_name and edge.edge_type == EdgeType.DEPENDENCY:
                if edge.source not in visited:
                    return False
        return True

    def get_active_edges(self, source: str, blackboard: Blackboard) -> List[CognitiveEdge]:
        """Get edges from source that are currently active."""
        return [e for e in self._adjacency[source] if e.is_active(blackboard)]
```

### 2.3 Create Edge Configuration

**File**: `config/cognitive_edges.json`

```json
{
  "version": "1.0",
  "edges": [
    {
      "source": "survey",
      "target": "control_tracker",
      "edge_type": "dependency",
      "base_cost": 1.0,
      "base_info_gain": 0.3
    },
    {
      "source": "frame_interpretation",
      "target": "event_understanding",
      "edge_type": "implication",
      "base_cost": 0.5,
      "base_info_gain": 0.6,
      "condition": "physics_game",
      "condition_value": true
    },
    {
      "source": "network_wisdom",
      "target": "exploration_phase",
      "edge_type": "fallback",
      "base_cost": 1.0,
      "base_info_gain": 0.5,
      "condition": "network_wisdom_empty",
      "condition_value": true
    },
    {
      "source": "discovery_exploitation",
      "target": "hypothesis_testing",
      "edge_type": "refinement",
      "base_cost": 2.0,
      "base_info_gain": 0.4,
      "condition": "discovery_confidence",
      "condition_value": "<0.7"
    }
  ]
}
```

**Deliverable**: `engines/cognition/cognitive_graph.py` + `config/cognitive_edges.json`

---

## Phase 2.5: Edge Inference Engine (Week 3.5) [NEW FROM PART 2]

Manual edge specification is O(n²) work and error-prone. The EdgeInferenceEngine automates this.

### 2.5.1 Multi-Layer Edge Inference

```python
# engines/cognition/edge_inference.py

class EdgeInferenceEngine:
    """Automatically infer edges from rung metadata and runtime observation."""

    def __init__(self, rungs: List[DecisionRung]):
        self.rungs = {r.name: r for r in rungs}
        self.edges: Dict[str, List[CognitiveEdge]] = defaultdict(list)

        # Layer 1: Static inference (runs once at startup)
        self._infer_from_declarations()   # ~30% of edges
        self._infer_from_slot_analysis()  # ~50% of edges (AST parsing)
        self._infer_from_categories()     # ~20% of edges

        # Layer 2: Runtime learning (updated during gameplay)
        self._learned_edges: Dict[str, List[CognitiveEdge]] = defaultdict(list)

    def _infer_from_declarations(self):
        """Rungs declare their dependencies explicitly via required_slots."""
        for name, rung in self.rungs.items():
            for req in getattr(rung, 'required_slots', []):
                providers = self._find_slot_providers(req)
                for provider in providers:
                    self.edges[provider].append(CognitiveEdge(
                        source=provider, target=name,
                        edge_type=EdgeType.DEPENDENCY,
                        base_cost=1.0, base_info_gain=0.0,
                        metadata={"inferred_by": "declaration"}
                    ))

    def _infer_from_slot_analysis(self):
        """AST analysis of which slots each rung reads/writes."""
        import ast, inspect

        slot_writers: Dict[str, List[str]] = defaultdict(list)
        slot_readers: Dict[str, List[str]] = defaultdict(list)

        for name, rung in self.rungs.items():
            # Parse evaluate() method
            try:
                source = inspect.getsource(rung.evaluate)
                tree = ast.parse(source)

                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        slot_name = self._extract_slot_access(node)
                        if slot_name:
                            if self._is_slot_write(node):
                                slot_writers[slot_name].append(name)
                            else:
                                slot_readers[slot_name].append(name)
            except (OSError, TypeError):
                continue  # Can't parse, skip

        # Create edges: writer → reader
        for slot, readers in slot_readers.items():
            for writer in slot_writers.get(slot, []):
                for reader in readers:
                    if writer != reader:
                        self.edges[writer].append(CognitiveEdge(
                            source=writer, target=reader,
                            edge_type=EdgeType.DEPENDENCY,
                            base_cost=1.0, base_info_gain=0.2,
                            metadata={"inferred_by": "slot_dataflow", "slot": slot}
                        ))

    def _infer_from_categories(self):
        """Category-based edge templates."""
        CATEGORY_TEMPLATES = {
            ("orientation", "hypothesis"): EdgeType.DEPENDENCY,
            ("orientation", "exploitation"): EdgeType.DEPENDENCY,
            ("hypothesis", "hypothesis"): EdgeType.REFINEMENT,
            ("filter", "exploitation"): EdgeType.CONTRADICTION,
            ("exploitation", "exploitation"): EdgeType.FALLBACK,
        }

        for name, rung in self.rungs.items():
            for other_name, other_rung in self.rungs.items():
                if name == other_name:
                    continue
                key = (rung.category, other_rung.category)
                if key in CATEGORY_TEMPLATES:
                    self.edges[name].append(CognitiveEdge(
                        source=name, target=other_name,
                        edge_type=CATEGORY_TEMPLATES[key],
                        base_cost=self._default_cost(CATEGORY_TEMPLATES[key]),
                        base_info_gain=self._default_gain(CATEGORY_TEMPLATES[key]),
                        metadata={"inferred_by": "category_template"}
                    ))

    def observe_transition(self, from_rung: str, to_rung: str, outcome: 'TransitionOutcome'):
        """Learn edge weights from observed transitions (runtime learning)."""
        edge = self._find_or_create_edge(from_rung, to_rung)
        edge.observation_count = getattr(edge, 'observation_count', 0) + 1

        # Update info_gain based on observed confidence delta
        if outcome.led_to_confidence_gain:
            edge.base_info_gain = 0.9 * edge.base_info_gain + 0.1 * outcome.confidence_delta

        # Adjust cost based on outcome
        if outcome.led_to_commit:
            edge.base_cost = 0.9 * edge.base_cost + 0.1 * 0.5  # Lower cost
        elif outcome.led_to_backtrack:
            edge.base_cost = 0.9 * edge.base_cost + 0.1 * 2.0  # Higher cost

@dataclass
class TransitionOutcome:
    """Outcome of transitioning between rungs."""
    confidence_delta: float
    led_to_confidence_gain: bool
    led_to_commit: bool
    led_to_backtrack: bool
```

### 2.5.2 Three-List Edge Validation [ENHANCED FROM PART 5]

```python
# manual_tools/validate_inferred_edges.py

from dataclasses import dataclass
from typing import List, Dict

@dataclass
class EdgeValidationResult:
    """Result of edge validation with three-list categorization."""
    confident: List[Dict]    # Auto-accept: high evidence
    uncertain: List[Dict]    # Human review: moderate evidence
    missing: List[Dict]      # Investigate: expected but not found

def validate_edges(engine: EdgeInferenceEngine, expected_patterns: Dict) -> EdgeValidationResult:
    """
    Generate three-list report for human review of inferred edges.

    Part 5 enhancement: Categorize edges into confident/uncertain/missing
    instead of just flagging suspicious ones.
    """
    confident = []
    uncertain = []

    for source, edges in engine.edges.items():
        for edge in edges:
            record = {
                "source": source,
                "target": edge.target,
                "type": edge.edge_type.value,
                "inferred_by": edge.metadata.get("inferred_by"),
                "observation_count": getattr(edge, 'observation_count', 0),
            }

            # Categorize by confidence
            if edge.metadata.get("inferred_by") == "declaration":
                record["confidence"] = "HIGH"
                confident.append(record)
            elif edge.metadata.get("inferred_by") == "slot_dataflow":
                # Slot analysis is reliable
                record["confidence"] = "HIGH"
                confident.append(record)
            elif getattr(edge, 'observation_count', 0) >= 5:
                # Runtime confirmed
                record["confidence"] = "MEDIUM-HIGH"
                confident.append(record)
            else:
                record["confidence"] = "MEDIUM"
                uncertain.append(record)

    # Find MISSING edges (Part 5 insight)
    missing = find_missing_edges(engine, expected_patterns)

    return EdgeValidationResult(
        confident=confident,
        uncertain=uncertain,
        missing=missing
    )

def find_missing_edges(engine: EdgeInferenceEngine, expected_patterns: Dict) -> List[Dict]:
    """
    Find edges that SHOULD exist based on patterns but weren't inferred.

    E.g., "survey should connect to control_tracker but doesn't"
    """
    missing = []

    # Expected patterns by category
    EXPECTED_CATEGORY_FLOWS = {
        "orientation": ["hypothesis", "exploitation", "filter"],
        "hypothesis": ["exploitation", "filter"],
        "meta": ["all"],  # Meta rungs should connect broadly
    }

    for source_name, source_rung in engine.rungs.items():
        expected_targets = EXPECTED_CATEGORY_FLOWS.get(source_rung.category, [])

        for target_name, target_rung in engine.rungs.items():
            if source_name == target_name:
                continue

            should_connect = (
                target_rung.category in expected_targets or
                "all" in expected_targets
            )

            has_edge = any(
                e.target == target_name
                for e in engine.edges.get(source_name, [])
            )

            if should_connect and not has_edge:
                missing.append({
                    "source": source_name,
                    "target": target_name,
                    "expected_because": f"{source_rung.category}→{target_rung.category}",
                    "action": "INVESTIGATE"
                })

    return missing
```

**Deliverable**: `engines/cognition/edge_inference.py` + `manual_tools/validate_inferred_edges.py`

---

## Phase 3: Meta-Planner with Caching (Week 4) [ENHANCED FROM PART 2]

### 3.0 SearchContext: Stateless Algorithms [NEW FROM PART 5]

**Architecture Decision**: Algorithms should be **stateless with injectable context**.

The `CognitiveRouter` maintains a `SearchContext` object passed to each algorithm call. Algorithms can request mutations to the context (like "please checkpoint here") but don't hold state themselves.

```python
# engines/cognition/search_context.py

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set

@dataclass
class SearchContext:
    """
    Injectable context for stateless algorithms.

    Part 5 insight: Algorithms receive all context per call, don't hold state.
    This is cleaner and easier to serialize/debug.
    """
    # Current state
    blackboard_snapshot: Dict[str, Any]
    visited_rungs: Set[str]
    current_path: List[str]
    current_quadrant: str

    # Precomputed data (injected once, used many times)
    landmark_distances: Dict[str, Dict[str, float]] = field(default_factory=dict)
    cluster_assignments: Dict[str, str] = field(default_factory=dict)
    topological_order: List[str] = field(default_factory=list)

    # Graph evolution data (from Phase 7)
    edge_trust_modifiers: Dict[str, float] = field(default_factory=dict)
    crystallized_paths: Dict[str, List[str]] = field(default_factory=dict)

    # Requested mutations (algorithms request, router applies)
    requested_checkpoint: bool = False
    requested_backtrack_to: Optional[int] = None
    requested_exclusions: Set[str] = field(default_factory=set)

    def request_checkpoint(self):
        """Request router to checkpoint after this iteration."""
        self.requested_checkpoint = True

    def request_backtrack(self, checkpoint_id: int):
        """Request router to restore to checkpoint."""
        self.requested_backtrack_to = checkpoint_id

    def request_exclude(self, rungs: Set[str]):
        """Request router to exclude these rungs from future search."""
        self.requested_exclusions.update(rungs)

    def get_edge_cost(self, source: str, target: str, base_cost: float) -> float:
        """Get modified edge cost including trust modifier."""
        modifier = self.edge_trust_modifiers.get(f"{source}→{target}", 1.0)
        return base_cost / modifier  # Higher trust = lower cost

    def has_crystallized_path(self, domain: str) -> Optional[List[str]]:
        """Check if there's a crystallized path for this domain."""
        return self.crystallized_paths.get(domain)

# Usage in algorithm:
class TargetedQuestionSearch(SearchAlgorithm):
    def get_next_rungs(
        self,
        graph: CognitiveGraph,
        context: SearchContext  # Not blackboard directly
    ) -> List[str]:
        # Algorithm is stateless - all state comes from context
        questions = context.blackboard_snapshot.get('known_unknowns', {})

        # Use precomputed data
        if 'survey' in context.topological_order:
            # ...

        # Request mutations instead of applying directly
        if should_checkpoint:
            context.request_checkpoint()

        return next_rungs
```

**Why Stateless**:
- Easier to serialize/debug (full state is in context)
- Algorithms can be unit tested with mock contexts
- No hidden state causing subtle bugs
- Router has full control over state mutations

### 3.1 Algorithm Selection Caching [NEW]

The key optimization: Cache algorithm selection with smart invalidation.

```python
# engines/cognition/meta_planner.py

ALGORITHM_RELEVANT_SLOTS = {
    "complexity", "rumsfeld", "contradiction",
    "time_budget_remaining", "domain_signature"
}

class MetaPlannerCache:
    """Cache algorithm selection with smart invalidation."""

    def __init__(self):
        self._cached_algorithm: Optional[SearchAlgorithm] = None
        self._cache_key: Optional[int] = None
        self._cache_hits = 0
        self._cache_misses = 0

    def get_algorithm(self, blackboard: Blackboard,
                      select_fn: Callable) -> SearchAlgorithm:
        current_key = self._compute_cache_key(blackboard)

        if self._cache_key == current_key and self._cached_algorithm:
            self._cache_hits += 1
            return self._cached_algorithm

        # Cache miss - recompute
        self._cache_misses += 1
        self._cached_algorithm = select_fn(blackboard)
        self._cache_key = current_key
        return self._cached_algorithm

    def _compute_cache_key(self, blackboard: Blackboard) -> int:
        """Key based on BUCKETED factors - prevents cache thrashing."""
        key_factors = (
            blackboard.slot("complexity"),
            self._bucket_confidence(blackboard.slot("max_confidence") or 0.0),
            self._bucket_uu(blackboard.slot("uu_estimate") or 0.5),
            blackboard.slot("contradiction") is not None,
            self._bucket_time(blackboard.slot("time_budget_remaining") or 1.0),
            blackboard.slot("dominant_domain") or "unknown",
        )
        return hash(key_factors)

    def _bucket_confidence(self, conf: float) -> str:
        if conf < 0.3: return "LOW"
        if conf < 0.6: return "MEDIUM"
        if conf < 0.9: return "HIGH"
        return "VERY_HIGH"

    def _bucket_uu(self, uu: float) -> str:
        if uu < 0.3: return "LOW"
        if uu < 0.7: return "MEDIUM"
        return "HIGH"

    def _bucket_time(self, time: float) -> str:
        if time < 0.2: return "CRITICAL"
        if time < 0.5: return "LOW"
        return "PLENTY"

    def invalidate(self):
        self._cache_key = None

# Precomputed profiles for O(1) common case lookup
class AlgorithmProfile:
    PROFILES = {
        ("SIMPLE", "HIGH", "LOW", False, "PLENTY", "physics"): "TopologicalDP",
        ("SIMPLE", "HIGH", "LOW", False, "PLENTY", "symbolic"): "Bidirectional",
        ("MEDIUM", "MEDIUM", "MEDIUM", False, "PLENTY", "unknown"): "LandmarkAStar",
        ("COMPLEX", "LOW", "HIGH", False, "PLENTY", "unknown"): "InformationMaximizing",
        # Contradiction ALWAYS triggers backtracking regardless of other factors
    }

    @classmethod
    def lookup(cls, cache_key: tuple) -> Optional[str]:
        # Exact match
        if cache_key in cls.PROFILES:
            return cls.PROFILES[cache_key]

        # Contradiction check (4th element)
        if cache_key[3]:  # has_contradiction = True
            return "BacktrackingAStar"

        # Time pressure check (5th element)
        if cache_key[4] == "CRITICAL":
            return "BeamSearch"

        return None  # Fall back to full computation
```

### 3.1 Domain-Specific Algorithm Portfolio [NEW FROM PART 2]

```python
# engines/cognition/algorithms.py

class SearchAlgorithm(ABC):
    @abstractmethod
    def get_next_rungs(self, graph: CognitiveGraph, blackboard: Blackboard) -> List[str]:
        pass

    def set_precomputed(self, data: Dict[str, Any]):
        """Receive precomputed data from PrecomputationManager."""
        self._precomputed = data

# Domain → Algorithm mapping
DOMAIN_ALGORITHMS = {
    "physics": {
        "primary": "TopologicalDPSearch",      # O(V+E) - causal chains are DAGs
        "fallback": "AStarSearch",
    },
    "symbolic": {
        "primary": "BidirectionalSearch",      # O(b^(d/2)) - known goal state
        "fallback": "IDAStarSearch",
    },
    "spatial": {
        "primary": "HierarchicalAStar",        # O(C² + V_c²) - region clusters
        "fallback": "AStarSearch",
    },
    "exploitation": {
        "primary": "GreedyBestFirst",          # O(V) - high confidence, go fast
        "fallback": "BeamSearch",
    },
    "exploration": {
        "primary": "InformationMaximizingSearch",  # UCB-style
        "fallback": "AStarSearch",
    },
    "time_pressure": {
        "primary": "BeamSearch",               # O(k·b·d) - hard bound
        "fallback": "GreedyBestFirst",
    },
    "contradiction": {
        "primary": "BacktrackingAStar",        # Systematic undo
        "fallback": "RestartWithExclusions",
    },
    "general": {
        "primary": "LandmarkAStar",            # O(E) with O(1) heuristic
        "fallback": "AStarSearch",
    },
}

class TopologicalDPSearch(SearchAlgorithm):
    """
    For DAG-structured problems (physics, causal chains).
    O(V + E) - linear in graph size!
    """

    def is_applicable(self, graph: CognitiveGraph) -> bool:
        return not graph.has_cycles()

    def get_next_rungs(self, graph: CognitiveGraph, blackboard: Blackboard) -> List[str]:
        # Use precomputed topological order
        topo_order = self._precomputed.get("topo_order")
        if not topo_order:
            return []

        visited = set(blackboard.slot('visited_rungs') or [])

        # Return first unvisited rung in topological order
        for rung in topo_order:
            if rung not in visited and graph._dependencies_satisfied(rung, visited):
                return [rung]

        return []

class BidirectionalSearch(SearchAlgorithm):
    """
    Search from start AND goal simultaneously - O(b^(d/2)) instead of O(b^d).
    For symbolic puzzles where goal is known (key→lock).
    """

    def get_next_rungs(self, graph: CognitiveGraph, blackboard: Blackboard) -> List[str]:
        goal_rungs = blackboard.slot("goal_rungs") or ["smart_action_selection"]
        start_rungs = self._get_start_rungs(blackboard)

        # Meet in the middle
        forward_frontier = self._expand_forward(graph, blackboard, start_rungs)
        backward_frontier = self._expand_backward(graph, blackboard, goal_rungs)

        # Find meeting point
        meeting = forward_frontier & backward_frontier
        if meeting:
            return [meeting.pop()]

        # Otherwise return best forward option
        return [forward_frontier.pop()] if forward_frontier else []

class LandmarkAStar(SearchAlgorithm):
    """
    A* with precomputed landmark distances for O(1) heuristic.
    """
    LANDMARKS = ["survey", "control_tracker", "network_wisdom",
                 "hypothesis_testing", "smart_action_selection"]

    def heuristic(self, node: str, goal: str) -> float:
        """Triangle inequality heuristic - O(L) = O(5) = O(1)."""
        h = 0
        landmark_distances = self._precomputed.get("landmark_distances", {})

        for landmark in self.LANDMARKS:
            d_node = landmark_distances.get(landmark, {}).get(node, float('inf'))
            d_goal = landmark_distances.get(landmark, {}).get(goal, float('inf'))
            h = max(h, abs(d_node - d_goal))

        return h

class BeamSearch(SearchAlgorithm):
    """
    Keep only top-k paths - O(k·b·d). Guaranteed time bound.
    """
    def __init__(self, beam_width: int = 3):
        self.k = beam_width

    def get_next_rungs(self, graph: CognitiveGraph, blackboard: Blackboard) -> List[str]:
        frontier = graph.get_frontier(blackboard)
        if not frontier:
            return []

        # Score and keep top k
        scored = [(self._score(r, blackboard), r) for r in frontier]
        scored.sort(reverse=True)
        top_k = scored[:self.k]

        return [top_k[0][1]] if top_k else []

class HierarchicalAStar(SearchAlgorithm):
    """
    Two-level search: abstract (categories) then detail (rungs within category).
    Reduces O(V²) to O(C² + max(V_c)²).
    """

    def get_next_rungs(self, graph: CognitiveGraph, blackboard: Blackboard) -> List[str]:
        clusters = self._precomputed.get("clusters", {})

        # Phase 1: Which category? O(C²) where C=6
        target_category = self._search_abstract(blackboard)

        # Phase 2: Which rung within category? O(V_c²) where V_c≈10
        rungs_in_category = clusters.get(target_category, [])
        return self._search_within_category(graph, blackboard, rungs_in_category)
```

### 3.2 Meta-Planner: Algorithm Selection (Enhanced)

```python
# engines/cognition/meta_planner.py

class SearchAlgorithm(ABC):
    @abstractmethod
    def get_next_rungs(self, graph: CognitiveGraph, blackboard: Blackboard) -> List[str]:
        """Return next rung(s) to execute."""
        pass

class GreedySearch(SearchAlgorithm):
    """Simple greedy - pick highest expected confidence."""
    def get_next_rungs(self, graph: CognitiveGraph, blackboard: Blackboard) -> List[str]:
        frontier = graph.get_frontier(blackboard)
        if not frontier:
            return []
        # Sort by expected confidence (from rung metadata or historical stats)
        scored = [(self._expected_confidence(r), r) for r in frontier]
        scored.sort(reverse=True)
        return [scored[0][1]]

class AStarSearch(SearchAlgorithm):
    """A* with heuristic toward confident decision."""
    def __init__(self, heuristic_fn: Callable):
        self.heuristic_fn = heuristic_fn

    def get_next_rungs(self, graph: CognitiveGraph, blackboard: Blackboard) -> List[str]:
        frontier = graph.get_frontier(blackboard)
        if not frontier:
            return []

        # f(n) = g(n) + h(n)
        # g(n) = cost so far (number of rungs visited)
        # h(n) = heuristic (estimated rungs to confident decision)
        g = len(blackboard.slot('visited_rungs') or [])
        scored = []
        for rung in frontier:
            h = self.heuristic_fn(rung, blackboard)
            f = g + h
            scored.append((f, rung))

        scored.sort()  # Lowest f first
        return [scored[0][1]]

class InformationMaximizingSearch(SearchAlgorithm):
    """Pick rung with highest information gain / cost ratio."""
    def get_next_rungs(self, graph: CognitiveGraph, blackboard: Blackboard) -> List[str]:
        frontier = graph.get_frontier(blackboard)
        if not frontier:
            return []

        scored = []
        for rung in frontier:
            info_gain = self._expected_info_gain(rung, blackboard)
            cost = self._compute_cost(rung, blackboard)
            acquisition = info_gain / (cost + 0.1)  # Like Bayesian Opt
            scored.append((acquisition, rung))

        scored.sort(reverse=True)
        return [scored[0][1]]

class BacktrackingSearch(SearchAlgorithm):
    """Restore checkpoint and try alternate path after contradiction."""
    def __init__(self, checkpoint_id: int, excluded_rungs: Set[str]):
        self.checkpoint_id = checkpoint_id
        self.excluded_rungs = excluded_rungs

    def get_next_rungs(self, graph: CognitiveGraph, blackboard: Blackboard) -> List[str]:
        # Restore to checkpoint
        blackboard.restore(self.checkpoint_id)

        # Get frontier excluding rungs that led to contradiction
        frontier = graph.get_frontier(blackboard)
        frontier = [r for r in frontier if r not in self.excluded_rungs]

        if not frontier:
            return []  # No alternate paths - must commit with best available

        return [frontier[0]]  # Take first available alternate
```

### 3.2 Meta-Planner: Algorithm Selection

```python
class MetaPlanner:
    """Selects search algorithm based on problem characterization."""

    def __init__(self, graph: CognitiveGraph):
        self.graph = graph

    def select_algorithm(self, blackboard: Blackboard) -> SearchAlgorithm:
        """Choose search strategy based on Rumsfeld assessment."""
        assessment = blackboard.rumsfeld_assessment(
            visited_rungs=set(blackboard.slot('visited_rungs') or []),
            all_rungs=set(self.graph.nodes.keys())
        )

        strategy = assessment.compute_routing_priority()

        if strategy == "EXPLORATION_FIRST":
            return InformationMaximizingSearch()

        elif strategy == "INFORMATION_MAXIMIZING":
            return QuestionDrivenSearch(
                questions=assessment.known_unknowns,
                answerers=assessment.ku_answerable_by
            )

        elif strategy == "EXPLOITATION_GREEDY":
            return GreedySearch()

        else:  # BALANCED_SEARCH
            return AStarSearch(heuristic_fn=self._default_heuristic)

        # Special cases
        if blackboard.slot('contradiction'):
            conflict = blackboard.slot('contradiction')
            checkpoint = blackboard.slot('last_checkpoint_id') or 0
            return BacktrackingSearch(
                checkpoint_id=checkpoint,
                excluded_rungs={conflict['source_rung']}
            )

        if blackboard.slot('time_budget_remaining', 1.0) < 0.2:
            return BeamSearch(beam_width=3)

    def _default_heuristic(self, rung: str, blackboard: Blackboard) -> float:
        """Estimate cost to reach confident decision from this rung."""
        current_conf = blackboard.slot('max_confidence') or 0.0
        target_conf = 0.85  # COMMIT_THRESHOLD
        gap = target_conf - current_conf
        return gap / 0.15  # Assume ~15% confidence gain per rung
```

**Deliverable**: `engines/cognition/meta_planner.py` - 400 LOC

---

## Phase 3.5: Precomputation Manager (Week 4.5) [NEW FROM PART 2]

Front-load expensive computations for O(1) query-time lookups.

```python
# engines/cognition/precomputation.py

class PrecomputationManager:
    """
    Manage precomputed data structures for fast query-time search.
    Run once at startup, provides O(1) lookups during gameplay.
    """

    def __init__(self, graph: CognitiveGraph):
        self.graph = graph

        # ALWAYS precompute (small constant cost at startup)
        self.category_clusters = self._cluster_by_category()  # O(V)
        self.landmark_distances = self._compute_landmarks()    # O(L·V·logV)
        self.topological_order = self._try_topo_sort()         # O(V+E) or None
        self.abstract_graph = self._build_abstract_graph()     # O(C²)

        logger.info(f"[PRECOMPUTE] Clusters: {len(self.category_clusters)} categories")
        logger.info(f"[PRECOMPUTE] Landmarks: {len(self.landmark_distances)} nodes")
        logger.info(f"[PRECOMPUTE] Topo order: {'available' if self.topological_order else 'N/A (cycles)'}")

    def _cluster_by_category(self) -> Dict[str, List[str]]:
        """Group rungs by category for HierarchicalA*."""
        clusters = defaultdict(list)
        for name, rung in self.graph.nodes.items():
            clusters[rung.category].append(name)
        return dict(clusters)

    def _compute_landmarks(self) -> Dict[str, Dict[str, float]]:
        """
        Dijkstra from each landmark - O(L · (V + E log V)).
        With L=5, V=63, E=200: ~5 * 63 * log(63) ≈ 2000 ops, done once.
        """
        LANDMARKS = ["survey", "control_tracker", "network_wisdom",
                     "hypothesis_testing", "smart_action_selection"]

        distances = {}
        for lm in LANDMARKS:
            if lm in self.graph.nodes:
                distances[lm] = self._dijkstra(lm)

        return distances

    def _dijkstra(self, start: str) -> Dict[str, float]:
        """Single-source shortest paths from start node."""
        import heapq

        dist = {node: float('inf') for node in self.graph.nodes}
        dist[start] = 0
        pq = [(0, start)]

        while pq:
            d, node = heapq.heappop(pq)
            if d > dist[node]:
                continue

            for edge in self.graph.get_active_edges(node, None):  # All edges
                new_dist = d + edge.base_cost
                if new_dist < dist[edge.target]:
                    dist[edge.target] = new_dist
                    heapq.heappush(pq, (new_dist, edge.target))

        return dist

    def _try_topo_sort(self) -> Optional[List[str]]:
        """
        If graph is DAG, precompute topological order.
        Returns None if cycles exist.
        """
        # Kahn's algorithm
        in_degree = defaultdict(int)
        for edges in self.graph._adjacency.values():
            for edge in edges:
                in_degree[edge.target] += 1

        queue = [n for n in self.graph.nodes if in_degree[n] == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)
            for edge in self.graph._adjacency.get(node, []):
                in_degree[edge.target] -= 1
                if in_degree[edge.target] == 0:
                    queue.append(edge.target)

        if len(result) == len(self.graph.nodes):
            return result  # Valid topological order
        return None  # Has cycles

    def _build_abstract_graph(self) -> Dict[str, Dict[str, float]]:
        """Build category-level graph with aggregate costs."""
        CATEGORY_ORDER = ["emergency", "orientation", "filter",
                         "hypothesis", "exploitation", "fallback"]

        abstract = {}
        for i, cat in enumerate(CATEGORY_ORDER[:-1]):
            next_cat = CATEGORY_ORDER[i + 1]
            # Cost = average cost of rungs in target category
            rungs_in_next = self.category_clusters.get(next_cat, [])
            if rungs_in_next:
                avg_cost = sum(self.graph.nodes[r].default_priority for r in rungs_in_next) / len(rungs_in_next)
            else:
                avg_cost = 50.0
            abstract.setdefault(cat, {})[next_cat] = avg_cost

        # Skip edges
        abstract.setdefault("orientation", {})["exploitation"] = 30.0
        abstract.setdefault("filter", {})["exploitation"] = 20.0

        return abstract

    def get_algorithm_data(self, algorithm_name: str) -> Dict[str, Any]:
        """Provide precomputed data to algorithm instance."""

        if algorithm_name == "TopologicalDPSearch":
            if self.topological_order:
                return {"topo_order": self.topological_order}
            raise ValueError("Graph has cycles, can't use TopologicalDP")

        elif algorithm_name == "LandmarkAStar":
            return {"landmark_distances": self.landmark_distances}

        elif algorithm_name == "HierarchicalAStar":
            return {
                "clusters": self.category_clusters,
                "abstract_graph": self.abstract_graph
            }

        elif algorithm_name == "BidirectionalSearch":
            return {"landmark_distances": self.landmark_distances}  # For heuristic

        return {}
```

**Deliverable**: `engines/cognition/precomputation.py` - 200 LOC

---

## Phase 4: Cognitive Router with Transition-Driven Switching (Week 5) [ENHANCED]

### 4.0 CatastrophicFallback: Circuit Breaker [NEW FROM PART 5]

**Problem**: What happens if the router gets stuck in a loop, every algorithm returns empty frontier, or contradiction count exceeds 5 in one decision?

**Solution**: CatastrophicFallback as a circuit breaker.

```python
# engines/cognition/catastrophic_fallback.py

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class CatastrophicEvent:
    """Record of a catastrophic failure for review."""
    game_id: str
    agent_id: str
    timestamp: str
    failure_type: str  # "loop", "empty_frontier", "contradiction_storm", "timeout"
    iterations: int
    path_taken: List[str]
    quadrant_history: List[str]
    contradiction_count: int
    context_snapshot: Dict[str, Any]

class CatastrophicFallback:
    """
    Escape hatch for when the cognitive router fails catastrophically.
    Falls back to static 'comprehensive' ordering.
    """

    # Thresholds that trigger catastrophic fallback
    MAX_QUADRANT_OSCILLATIONS = 6    # Same quadrant pair 6+ times
    MAX_CONTRADICTIONS = 5           # 5+ contradictions in one decision
    MAX_EMPTY_FRONTIERS = 3          # 3+ consecutive empty frontiers
    MAX_LOOP_ITERATIONS = 50         # Iterations without progress

    def __init__(self):
        self.events: List[CatastrophicEvent] = []
        self._quadrant_history: List[str] = []
        self._contradiction_count = 0
        self._empty_frontier_count = 0
        self._last_path_length = 0
        self._stall_iterations = 0

    def reset(self):
        """Reset counters at start of new decision."""
        self._quadrant_history = []
        self._contradiction_count = 0
        self._empty_frontier_count = 0
        self._last_path_length = 0
        self._stall_iterations = 0

    def record_quadrant(self, quadrant: str):
        """Record quadrant visit."""
        self._quadrant_history.append(quadrant)

    def record_contradiction(self):
        """Record a contradiction."""
        self._contradiction_count += 1

    def record_empty_frontier(self):
        """Record empty frontier from algorithm."""
        self._empty_frontier_count += 1

    def record_iteration(self, path_length: int):
        """Check for stall (no progress)."""
        if path_length == self._last_path_length:
            self._stall_iterations += 1
        else:
            self._stall_iterations = 0
            self._last_path_length = path_length

    def should_fallback(self) -> tuple[bool, Optional[str]]:
        """
        Check if we should trigger catastrophic fallback.
        Returns (should_fallback, failure_type).
        """
        # Check quadrant oscillation
        if len(self._quadrant_history) >= 6:
            recent = self._quadrant_history[-6:]
            pairs = [(recent[i], recent[i+1]) for i in range(0, 5, 2)]
            if len(set(pairs)) == 1:  # Same pair repeating
                return True, "quadrant_loop"

        # Check contradiction storm
        if self._contradiction_count >= self.MAX_CONTRADICTIONS:
            return True, "contradiction_storm"

        # Check empty frontier
        if self._empty_frontier_count >= self.MAX_EMPTY_FRONTIERS:
            return True, "empty_frontier"

        # Check stall
        if self._stall_iterations >= self.MAX_LOOP_ITERATIONS:
            return True, "stall_loop"

        return False, None

    def trigger_fallback(
        self,
        game_id: str,
        agent_id: str,
        failure_type: str,
        path: List[str],
        context: Dict[str, Any]
    ) -> List[str]:
        """
        Log catastrophic failure and return static comprehensive ordering.
        """
        event = CatastrophicEvent(
            game_id=game_id,
            agent_id=agent_id,
            timestamp=datetime.now().isoformat(),
            failure_type=failure_type,
            iterations=len(path),
            path_taken=path.copy(),
            quadrant_history=self._quadrant_history.copy(),
            contradiction_count=self._contradiction_count,
            context_snapshot={k: str(v)[:100] for k, v in context.items()},
        )
        self.events.append(event)

        # Log to database (catastrophic_failures table)
        self._persist_event(event)

        # Return the static comprehensive ordering as fallback
        return self._get_comprehensive_ordering()

    def _persist_event(self, event: CatastrophicEvent):
        """Persist catastrophic event to database for human review."""
        # Would insert into catastrophic_failures table
        pass

    def _get_comprehensive_ordering(self) -> List[str]:
        """Return the old static comprehensive ordering."""
        # This is the ORDERING_PRESETS['comprehensive'] from old system
        return [
            "survey", "frame_interpretation", "control_tracker",
            "sparse_grid", "pattern_detection", "hypothesis_testing",
            "discovery_exploitation", "smart_action_selection",
            # ... full comprehensive list
        ]
```

**Usage in Router**:
```python
# In CognitiveRouter.decide():
self.catastrophic_fallback.reset()  # At start

# In main loop:
self.catastrophic_fallback.record_quadrant(current_quadrant.name)
self.catastrophic_fallback.record_iteration(len(path))
if transitions and any(t.from_quadrant == KK and t.to_quadrant == UU for t in transitions):
    self.catastrophic_fallback.record_contradiction()
if not next_rungs:
    self.catastrophic_fallback.record_empty_frontier()

should_fallback, failure_type = self.catastrophic_fallback.should_fallback()
if should_fallback:
    fallback_ordering = self.catastrophic_fallback.trigger_fallback(
        game_id, agent_id, failure_type, path, blackboard.to_context()
    )
    return self._execute_static_ordering(fallback_ordering, game_state, blackboard)
```

### 4.1 Key Part 3 Integration: Transition-Driven Algorithm Selection

**The critical insight from Part 3**: Don't re-classify domain every iteration. Track **epistemic transitions** and switch algorithms only when quadrant changes.

```
┌────────────────────────────────────────────────────────────────────────┐
│                    TRANSITION-DRIVEN ROUTER FLOW                        │
│                                                                         │
│  Start → Initial Quadrant Assessment → Select Initial Algorithm         │
│            │                                                            │
│            ▼                                                            │
│       ┌─────────────────────────────────────────────────────────┐      │
│       │                   MAIN LOOP                              │      │
│       │  1. Run current algorithm for K rungs                    │      │
│       │  2. EpistemicTracker.update_from_rung_result()          │      │
│       │  3. IF transition detected:                              │      │
│       │       - Look up TRANSITION_RESPONSES[old→new]           │      │
│       │       - Switch to new algorithm                          │      │
│       │       - Apply transition action (focus/exploit/reset)    │      │
│       │  4. Check termination (commit/exhausted/timeout)         │      │
│       └─────────────────────────────────────────────────────────┘      │
│            │                                                            │
│            ▼                                                            │
│       Commit best action                                                │
│                                                                         │
│  Complexity: O(transitions × avg_rungs_per_quadrant)                   │
│            = O(3 × 8) = O(24) typical case                             │
│            vs O(63 × 25) = O(1575) for static A*                       │
└────────────────────────────────────────────────────────────────────────┘
```

### 4.1 TransitionDrivenRouter (Enhanced CognitiveRouter)

```python
# engines/cognition/cognitive_router.py

class CognitiveRouter:
    """
    Orchestrates dynamic rung traversal via blackboard.

    Key enhancement from Part 3: TRANSITION-DRIVEN algorithm switching.
    Don't re-classify every iteration - switch only on epistemic transitions.
    """

    COMMIT_THRESHOLD = 0.85
    MAX_ITERATIONS = 20
    RUNGS_PER_ALGORITHM_STEP = 3  # Run K rungs before checking transitions

    def __init__(self, rungs: Dict[str, DecisionRung], edges_config: str):
        self.rungs = rungs
        self.graph = CognitiveGraph(rungs, edges_config)
        self.edge_inference = EdgeInferenceEngine(list(rungs.values()))
        self.precompute = PrecomputationManager(self.graph)
        self.planner = MetaPlanner(self.graph)
        self.cache = MetaPlannerCache()

        # NEW: Epistemic tracking from Part 3
        self.epistemic_tracker = EpistemicTracker()

        # NEW: Catastrophic fallback from Part 5
        self.catastrophic_fallback = CatastrophicFallback()

    def decide(self, game_state: Any, context: Dict[str, Any]) -> Tuple[str, str]:
        """
        Make action decision via TRANSITION-DRIVEN routing.

        Algorithm selection is driven by epistemic state TRANSITIONS,
        not continuous re-classification.
        """
        blackboard = Blackboard().from_context(context)
        self._assess_problem(blackboard, game_state)

        # Initialize epistemic state
        all_rungs = set(self.rungs.keys())
        visited_rungs = set()
        self.epistemic_tracker = EpistemicTracker()  # Fresh tracker per decision

        # Initial algorithm based on starting quadrant
        initial_quadrant = self.epistemic_tracker.current_state.compute_primary_quadrant()
        algorithm = self._get_algorithm_for_quadrant(initial_quadrant, blackboard)

        path = []
        iterations = 0
        rungs_since_transition = 0

        while iterations < self.MAX_ITERATIONS:
            iterations += 1

            if self._should_commit(blackboard):
                return self._commit(blackboard, path)

            # Checkpoint for backtracking
            checkpoint_id = blackboard.checkpoint()
            blackboard.slot('last_checkpoint_id', checkpoint_id)

            # Run algorithm for a few rungs
            next_rungs = algorithm.get_next_rungs(self.graph, blackboard)

            if not next_rungs:
                break

            # Execute rung
            rung_name = next_rungs[0]
            rung = self.rungs[rung_name]
            result = rung.evaluate(game_state, blackboard.to_context())
            self._update_blackboard(blackboard, rung_name, result)
            path.append(rung_name)
            visited_rungs.add(rung_name)
            rungs_since_transition += 1

            # === PART 3 CORE: Detect epistemic transitions ===
            transitions = self.epistemic_tracker.update_from_rung_result(
                rung_name=rung_name,
                result=result,
                blackboard=blackboard,
                all_rungs=all_rungs,
                visited_rungs=visited_rungs
            )

            # === Algorithm switching on transitions ===
            if transitions:
                for transition in transitions:
                    response = get_algorithm_for_transition(transition)
                    new_algorithm_name = response.get("algorithm", "LandmarkAStar")
                    action = response.get("action", "continue")

                    logger.debug(
                        f"[EPISTEMIC] {transition.from_quadrant.name}->{transition.to_quadrant.name} "
                        f"at {rung_name}: {action} -> {new_algorithm_name}"
                    )

                    # Apply transition action
                    if action == "backtrack_and_target":
                        # Restore checkpoint and inject new questions
                        algorithm = BacktrackingTargetedSearch(
                            checkpoint_id=checkpoint_id,
                            new_questions=self.epistemic_tracker.current_state.known_unknowns
                        )
                    elif action == "reset_and_explore":
                        # Exclude failed path and widen search
                        algorithm = ExplorationWithExclusions(
                            excluded_rungs=set(path[-5:]),  # Exclude recent path
                            exploration_bonus=response.get("params", {}).get("exploration_bonus", 1.5)
                        )
                    elif action in ("focus", "exploit", "retrieve", "widen", "pivot"):
                        # Normal algorithm switch
                        algorithm = self._get_algorithm_for_quadrant(
                            transition.to_quadrant, blackboard
                        )

                    # Inject precomputed data
                    try:
                        precomputed = self.precompute.get_algorithm_data(new_algorithm_name)
                        algorithm.set_precomputed(precomputed)
                    except ValueError:
                        pass  # Some algorithms don't need precomputed data

                    rungs_since_transition = 0
                    self.cache.invalidate()  # Invalidate on transition

            # Record transition for edge learning
            if len(path) >= 2:
                self.edge_inference.observe_transition(
                    from_rung=path[-2],
                    to_rung=path[-1],
                    outcome=TransitionOutcome(
                        confidence_delta=result.confidence - (blackboard.slot('prev_confidence') or 0),
                        led_to_confidence_gain=result.confidence > 0.5,
                        led_to_commit=result.confidence > self.COMMIT_THRESHOLD,
                        led_to_backtrack=any(t.from_quadrant == EpistemicQuadrant.KK
                                           and t.to_quadrant in (EpistemicQuadrant.KU, EpistemicQuadrant.UU)
                                           for t in transitions)
                    )
                )
            blackboard.slot('prev_confidence', result.confidence)

            if result.confidence > self.COMMIT_THRESHOLD:
                return result.action, f"[{rung_name}] {result.reason}"

        return self._commit(blackboard, path)

    def _get_algorithm_for_quadrant(
        self,
        quadrant: EpistemicQuadrant,
        blackboard: Blackboard
    ) -> SearchAlgorithm:
        """Get optimal algorithm for a given epistemic quadrant."""

        QUADRANT_ALGORITHMS = {
            EpistemicQuadrant.KK: GreedyExploitation,
            EpistemicQuadrant.KU: TargetedQuestionSearch,
            EpistemicQuadrant.UK: RetrievalSearch,
            EpistemicQuadrant.UU: InformationMaximizingSearch,
        }

        algorithm_class = QUADRANT_ALGORITHMS.get(quadrant, LandmarkAStar)

        # Initialize with appropriate parameters
        if quadrant == EpistemicQuadrant.KU:
            return algorithm_class(self.epistemic_tracker.current_state.known_unknowns)
        elif quadrant == EpistemicQuadrant.KK:
            return algorithm_class(commit_threshold=self.COMMIT_THRESHOLD)
        else:
            return algorithm_class()

    def _get_transition_stats(self) -> Dict[str, Any]:
        """Get statistics about transitions for debugging/logging."""
        return {
            "total_transitions": len(self.epistemic_tracker.transitions),
            "transition_pattern": self.epistemic_tracker.get_transition_pattern(),
            "final_quadrant": self.epistemic_tracker.current_state.primary_quadrant.name,
            "kk_confidence": self.epistemic_tracker.current_state.kk_confidence,
            "uu_estimate": self.epistemic_tracker.current_state.uu_estimate,
        }

    def _quick_classify(self, blackboard: Blackboard) -> str:
        """O(1) domain classification from blackboard state."""
        if blackboard.slot("contradiction"):
            return "contradiction"

        if blackboard.slot("physics_game_confirmed"):
            return "physics"

        if blackboard.slot("goal_state") is not None:
            return "symbolic"

        if (blackboard.slot("time_budget_remaining") or 1.0) < 0.2:
            return "time_pressure"

        confidence = blackboard.slot("max_confidence") or 0.0
        if confidence > 0.8:
            return "exploitation"
        elif confidence < 0.3:
            return "exploration"

        return "general"

    def _get_algorithm_for_domain(self, domain: str) -> SearchAlgorithm:
        """Get cached algorithm for domain, with precomputed data."""
        algorithm_name = DOMAIN_ALGORITHMS.get(domain, {}).get("primary", "LandmarkAStar")
        algorithm_class = ALGORITHM_CLASSES[algorithm_name]
        algorithm = algorithm_class()

        # Inject precomputed data
        try:
            precomputed = self.precompute.get_algorithm_data(algorithm_name)
            algorithm.set_precomputed(precomputed)
        except ValueError:
            # Fall back if precomputation not available for this algorithm
            fallback_name = DOMAIN_ALGORITHMS.get(domain, {}).get("fallback", "AStarSearch")
            algorithm = ALGORITHM_CLASSES[fallback_name]()

        return algorithm

ALGORITHM_CLASSES = {
    "TopologicalDPSearch": TopologicalDPSearch,
    "BidirectionalSearch": BidirectionalSearch,
    "LandmarkAStar": LandmarkAStar,
    "HierarchicalAStar": HierarchicalAStar,
    "BeamSearch": BeamSearch,
    "GreedyBestFirst": GreedySearch,
    "InformationMaximizingSearch": InformationMaximizingSearch,
    "BacktrackingAStar": BacktrackingSearch,
    "AStarSearch": AStarSearch,
}
```

    def _assess_problem(self, blackboard: Blackboard, game_state: Any):
        """Initial problem characterization."""
        # Complexity estimate
        frame = game_state.frame if hasattr(game_state, 'frame') else None
        if frame is not None:
            entropy = self._compute_entropy(frame)
            objects = len(find_distinct_objects(frame)) if callable(find_distinct_objects) else 10
            complexity = 'SIMPLE' if entropy < 2.0 and objects < 5 else 'WICKED' if entropy > 4.0 else 'MEDIUM'
        else:
            complexity = 'MEDIUM'

        blackboard.slot('complexity', complexity, confidence=0.7, source_rung='router')

        # Domain signature (from frame analysis or game_type hint)
        game_type = blackboard.slot('game_type') or 'unknown'
        domain_sig = {
            'physics': 0.7 if 'physics' in game_type.lower() else 0.3,
            'symbolic': 0.7 if 'puzzle' in game_type.lower() else 0.3,
            'spatial': 0.5,  # Default medium
        }
        blackboard.slot('domain_signature', domain_sig, confidence=0.5, source_rung='router')

    def _should_commit(self, blackboard: Blackboard) -> bool:
        """Check if we should commit to an action."""
        # Explicit committed action
        if blackboard.slot('committed_action'):
            return True

        # Confidence threshold met
        if (blackboard.slot('max_confidence') or 0.0) > self.COMMIT_THRESHOLD:
            return True

        # All frontier exhausted
        frontier = self.graph.get_frontier(blackboard)
        if not frontier:
            return True

        return False

    def _commit(self, blackboard: Blackboard) -> Tuple[str, str]:
        """Return the committed action."""
        action = blackboard.slot('committed_action')
        reason = blackboard.slot('committed_reason')

        if action:
            return action, reason

        # Fallback: weighted combination of partial actions
        partial = blackboard.slot('partial_action')
        if partial and partial.get('candidates'):
            weights = partial.get('weights', [1.0] * len(partial['candidates']))
            # Weighted random choice
            import random
            action = random.choices(partial['candidates'], weights=weights, k=1)[0]
            return action, "Weighted fallback from partial actions"

        # Ultimate fallback
        return 'ACTION1', "No confident decision - ultimate fallback"
```

### 4.2 Integration with DecisionRungSystem

```python
# Modification to decision_rung_system.py

class DecisionRungSystem:
    def __init__(self, ...):
        # ... existing init ...

        # NEW: Cognitive router for dynamic mode
        self._cognitive_router: Optional[CognitiveRouter] = None
        self._use_cognitive_routing = False  # Feature flag

    def enable_cognitive_routing(self, edges_config: str = 'config/cognitive_edges.json'):
        """Enable dynamic cognitive routing (replaces static orderings)."""
        from engines.cognition.cognitive_router import CognitiveRouter
        self._cognitive_router = CognitiveRouter(
            rungs=self._get_rung_instances(),
            edges_config=edges_config
        )
        self._use_cognitive_routing = True

    def decide(self, game_state: Any, context: Dict[str, Any]) -> Tuple[str, str]:
        """Make decision - routes to cognitive router if enabled."""
        if self._use_cognitive_routing and self._cognitive_router:
            return self._cognitive_router.decide(game_state, context)

        # Fall back to existing strategy-based decide
        return self._decide_existing(game_state, context)
```

**Deliverable**: `engines/cognition/cognitive_router.py` + integration

---

## Phase 5: Validation & Testing (Week 6)

### 5.1 Shadow Mode Testing

Run both systems in parallel, compare outputs:

```python
def shadow_test(game_state, context):
    """Compare cognitive router vs static ordering."""
    # Static system
    static_system = DecisionRungSystem(strategy='ladder')
    static_system.load_ordering('comprehensive')
    static_action, static_reason = static_system.decide(game_state, context)

    # Cognitive router
    router = CognitiveRouter(rungs, 'config/cognitive_edges.json')
    router_action, router_reason = router.decide(game_state, context)

    # Log divergence
    if static_action != router_action:
        log_divergence(game_state, context, static_action, router_action)

    return static_action, static_reason  # Use static for safety
```

### 5.2 Metrics to Track

| Metric | Target | Current Baseline |
|--------|--------|------------------|
| Avg rungs evaluated per decision | < 15 | ~40 (ladder runs all) |
| Decision latency | < 50ms | ~100ms |
| First-win rate (rung 1-5 provides answer) | > 60% | ~30% |
| Backtracking frequency | < 5% | N/A (no backtracking) |
| Contradiction detection rate | > 80% of conflicts | 0% |

### 5.3 A/B Testing on ARC Games

```
Phase 5a: 10% of games use cognitive routing
Phase 5b: 50% of games (if metrics good)
Phase 5c: 100% (deprecate ORDERING_PRESETS)
```

---

## Phase 5.5: Stabilization Week 1 [NEW FROM PART 5]

**Purpose**: Integration bugs surface when pieces interact. Explicit stabilization week.

**Focus Areas**:
1. Fix bugs discovered in Phase 4-5 integration
2. Tune hysteresis parameters (confirmation counts, cooldowns)
3. Validate epistemic tracker accuracy
4. Review catastrophic fallback triggers (should be rare)
5. Performance profiling and optimization

**Exit Criteria**:
- Zero catastrophic fallbacks in 100 consecutive games
- Thrashing score < 0.3 average
- Decision latency < 50ms p95
- Shadow mode divergence understood and documented

---

## Phase 6: Production Rollout (Week 8)

### 6.1 Deprecation Path

1. Mark ORDERING_PRESETS as `@deprecated`
2. Log warning when static orderings used
3. Remove static orderings in v3.0

### 6.2 Edge Evolution

Edges should evolve based on observed utility:

```python
def update_edge_weights(edge: CognitiveEdge, outcome: float):
    """Update edge info_gain based on observed outcome."""
    # Exponential moving average
    alpha = 0.1
    edge.base_info_gain = alpha * outcome + (1 - alpha) * edge.base_info_gain
```

### 6.3 Database Integration

Store routing decisions and outcomes:

```sql
CREATE TABLE IF NOT EXISTS cognitive_routing_traces (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    game_id TEXT,
    agent_id TEXT,
    path TEXT,  -- JSON array of rung names in traversal order
    algorithm_used TEXT,
    rumsfeld_assessment TEXT,  -- JSON
    final_action TEXT,
    final_confidence REAL,
    outcome_score REAL,
    backtrack_count INTEGER
);
```

---

## Phase 7: Graph Evolution & Process Knowledge (Week 8+) [NEW FROM PART 4]

The cognitive graph should not be static. Every traversal is both a decision AND a training signal. The graph after 1000 games should look fundamentally different than at start.

### 7.1 Cumulative Edge Trust

Edge weights accumulate across games, not just per-decision.

```python
# engines/cognition/graph_evolution.py

@dataclass
class EdgeTrustRecord:
    """Cumulative trust record for an edge across all games."""
    edge_id: str                    # source→target
    traversal_count: int = 0        # How many times traversed
    success_count: int = 0          # How many times led to good outcome
    failure_count: int = 0          # How many times led to contradiction
    cumulative_confidence_gain: float = 0.0  # Sum of confidence deltas
    last_traversed: int = 0         # Generation number

    @property
    def trust_score(self) -> float:
        """Calculate trust score from history."""
        if self.traversal_count == 0:
            return 0.5  # Neutral for untested edges

        success_rate = self.success_count / self.traversal_count
        avg_gain = self.cumulative_confidence_gain / self.traversal_count

        # Trust = weighted combination of success rate and gain
        return 0.6 * success_rate + 0.4 * min(1.0, avg_gain)

    @property
    def is_crystallized(self) -> bool:
        """Has this edge been traversed enough to be considered proven?"""
        return self.traversal_count >= 20 and self.trust_score > 0.8

class GraphEvolutionManager:
    """Manages long-term evolution of the cognitive graph."""

    def __init__(self, db_connection):
        self.db = db_connection
        self.edge_trust: Dict[str, EdgeTrustRecord] = {}
        self._load_from_db()

    def record_traversal(
        self,
        source: str,
        target: str,
        outcome: 'TraversalOutcome'
    ):
        """Record a single edge traversal and its outcome."""
        edge_id = f"{source}→{target}"

        if edge_id not in self.edge_trust:
            self.edge_trust[edge_id] = EdgeTrustRecord(edge_id=edge_id)

        record = self.edge_trust[edge_id]
        record.traversal_count += 1
        record.cumulative_confidence_gain += outcome.confidence_delta

        if outcome.led_to_success:
            record.success_count += 1
        if outcome.led_to_contradiction:
            record.failure_count += 1
            # Apply negative reputation penalty (Part 4 insight)
            record.cumulative_confidence_gain -= 0.3  # Contradiction hurts more than neutral

    def get_edge_modifier(self, source: str, target: str) -> float:
        """Get trust-based modifier for edge cost/info_gain."""
        edge_id = f"{source}→{target}"
        record = self.edge_trust.get(edge_id)

        if not record:
            return 1.0  # No history, neutral

        # High trust = lower cost / higher info_gain
        # Low trust = higher cost / lower info_gain
        return 0.5 + record.trust_score  # Range: 0.5 to 1.5
```

### 7.2 Rung Role Taxonomy

Classify rungs by their role in the universal problem-solving pattern, not just category.

```python
# engines/cognition/rung_roles.py

class RungRole(Enum):
    """Roles rungs play in the universal problem-solving pattern."""
    ENTRY = "entry"              # Low-friction starting points
    LEVERAGE = "leverage"        # Build on entry points to reach harder targets
    COMPOUNDING = "compounding"  # Connections multiply, knowledge spreads
    RESOLUTION = "resolution"    # Path becomes obvious, commit to action

# Map rungs to their primary role
RUNG_ROLE_MAP = {
    # Entry rungs: Low friction, broad coverage, orientation
    "survey": RungRole.ENTRY,
    "frame_interpretation": RungRole.ENTRY,
    "sparse_grid": RungRole.ENTRY,
    "palette_detection": RungRole.ENTRY,
    "scan_for_goals": RungRole.ENTRY,

    # Leverage rungs: Use entry results to reach deeper understanding
    "control_tracker": RungRole.LEVERAGE,
    "object_interaction_test": RungRole.LEVERAGE,
    "hypothesis_testing": RungRole.LEVERAGE,
    "event_understanding": RungRole.LEVERAGE,
    "spatial_relationship": RungRole.LEVERAGE,

    # Compounding rungs: Knowledge spreads, connections multiply
    "rule_transfer": RungRole.COMPOUNDING,
    "abstraction_matching": RungRole.COMPOUNDING,
    "network_wisdom": RungRole.COMPOUNDING,
    "theory_gate": RungRole.COMPOUNDING,
    "causal_chain": RungRole.COMPOUNDING,

    # Resolution rungs: Path crystallizes, commit to action
    "smart_action_selection": RungRole.RESOLUTION,
    "optimal_sequence": RungRole.RESOLUTION,
    "confident_commit": RungRole.RESOLUTION,
    "action_execution": RungRole.RESOLUTION,
}

def get_role_for_phase(phase: str) -> RungRole:
    """Map problem-solving phase to appropriate rung role."""
    PHASE_ROLE_MAP = {
        "exploration": RungRole.ENTRY,
        "building": RungRole.LEVERAGE,
        "connecting": RungRole.COMPOUNDING,
        "resolving": RungRole.RESOLUTION,
    }
    return PHASE_ROLE_MAP.get(phase, RungRole.ENTRY)
```

### 7.3 Path Crystallization Detection

Detect when paths have been traversed enough to become direct lookups instead of searches.

```python
# engines/cognition/path_crystallization.py

@dataclass
class CrystallizedPath:
    """A path proven reliable enough to skip search."""
    domain_signature: str        # e.g., "physics_puzzle", "symbolic_grid"
    path: List[str]              # Ordered list of rung names
    traversal_count: int         # How many times this exact path succeeded
    avg_confidence: float        # Average final confidence
    avg_ticks: int               # Average ticks to resolution

    def is_reliable(self, domain_game_count: int = 100) -> bool:
        """
        Is this path reliable enough to use as a lookup?

        Part 5 refinement: Use domain-relative threshold for rare game types.
        Threshold = min(10, 50% of domain games)
        """
        # Domain-relative threshold (Part 5)
        threshold = min(10, max(3, domain_game_count // 2))

        return (
            self.traversal_count >= threshold and
            self.avg_confidence > 0.85 and
            self.avg_ticks < 15
        )

class PathCrystallizer:
    """Detects and stores crystallized paths."""

    def __init__(self):
        self.path_history: Dict[str, List[CrystallizedPath]] = defaultdict(list)

    def record_successful_path(
        self,
        domain: str,
        path: List[str],
        confidence: float,
        ticks: int
    ):
        """Record a successful path for potential crystallization."""
        path_key = "→".join(path)

        # Find or create crystallized path record
        for cp in self.path_history[domain]:
            if "→".join(cp.path) == path_key:
                # Update existing
                cp.traversal_count += 1
                cp.avg_confidence = (cp.avg_confidence * (cp.traversal_count - 1) + confidence) / cp.traversal_count
                cp.avg_ticks = int((cp.avg_ticks * (cp.traversal_count - 1) + ticks) / cp.traversal_count)
                return

        # New path
        self.path_history[domain].append(CrystallizedPath(
            domain_signature=domain,
            path=path,
            traversal_count=1,
            avg_confidence=confidence,
            avg_ticks=ticks,
        ))

    def get_crystallized_path(self, domain: str) -> Optional[List[str]]:
        """
        Get a crystallized path for domain if one exists.
        Returns None if no reliable path exists (must search).
        """
        candidates = [cp for cp in self.path_history.get(domain, []) if cp.is_reliable]

        if not candidates:
            return None

        # Return most reliable
        best = max(candidates, key=lambda cp: cp.traversal_count * cp.avg_confidence)
        return best.path
```

### 7.4 Process Knowledge Extraction

Extract abstract patterns from successes, not just concrete rung sequences.

```python
# engines/cognition/process_knowledge.py

@dataclass
class AbstractPattern:
    """
    Abstract pattern extracted from concrete paths.

    Instead of: "survey → control_tracker → event_understanding"
    We extract: "entry → leverage → compounding" with domain mappings
    """
    pattern_id: str
    role_sequence: List[RungRole]    # Abstract: [ENTRY, LEVERAGE, COMPOUNDING]
    domain_instantiations: Dict[str, List[str]]  # domain → concrete rungs
    success_count: int = 0

    def instantiate_for_domain(self, domain: str) -> Optional[List[str]]:
        """Get concrete rung sequence for a domain, or None if unknown."""
        return self.domain_instantiations.get(domain)

    def add_instantiation(self, domain: str, concrete_path: List[str]):
        """Record a new domain instantiation of this pattern."""
        self.domain_instantiations[domain] = concrete_path
        self.success_count += 1

class ProcessKnowledgeExtractor:
    """Extracts abstract patterns from successful concrete paths."""

    def __init__(self):
        self.patterns: Dict[str, AbstractPattern] = {}

    def extract_pattern(self, path: List[str]) -> str:
        """
        Extract abstract role pattern from concrete path.
        Returns pattern_id.
        """
        role_sequence = [RUNG_ROLE_MAP.get(rung, RungRole.ENTRY) for rung in path]
        pattern_id = "→".join(r.name for r in role_sequence)
        return pattern_id

    def record_success(self, domain: str, path: List[str]):
        """Record a successful path, extracting its abstract pattern."""
        pattern_id = self.extract_pattern(path)

        if pattern_id not in self.patterns:
            role_sequence = [RUNG_ROLE_MAP.get(rung, RungRole.ENTRY) for rung in path]
            self.patterns[pattern_id] = AbstractPattern(
                pattern_id=pattern_id,
                role_sequence=role_sequence,
                domain_instantiations={},
            )

        self.patterns[pattern_id].add_instantiation(domain, path)

    def suggest_path_for_new_domain(
        self,
        new_domain: str,
        available_rungs: Dict[str, RungRole]
    ) -> Optional[List[str]]:
        """
        Suggest a path for a new domain based on successful patterns.
        Uses the most successful abstract pattern and instantiates for new domain.
        """
        if not self.patterns:
            return None

        # Find most successful pattern
        best_pattern = max(self.patterns.values(), key=lambda p: p.success_count)

        # Try to instantiate for new domain
        suggested_path = []
        for role in best_pattern.role_sequence:
            # Find a rung with this role that's available
            candidates = [rung for rung, r in available_rungs.items() if r == role]
            if candidates:
                suggested_path.append(candidates[0])  # Take first match
            else:
                return None  # Can't instantiate this pattern

        return suggested_path

    # === DOMAIN-SPECIFIC PATTERNS [NEW FROM PART 5] ===

    def get_best_pattern_for_domain(
        self,
        domain: str,
        available_rungs: Dict[str, RungRole]
    ) -> Optional[List[str]]:
        """
        Part 5 refinement: Track pattern success per domain.
        Different domains may need different patterns.

        E.g., spatial puzzles might skip COMPOUNDING and go ENTRY→LEVERAGE→RESOLUTION
        """
        # Calculate pattern success rates per domain
        domain_pattern_success: Dict[str, Dict[str, float]] = defaultdict(dict)

        for pattern_id, pattern in self.patterns.items():
            if domain in pattern.domain_instantiations:
                # This pattern has been tried in this domain
                domain_success_rate = self._get_domain_success_rate(pattern_id, domain)
                domain_pattern_success[domain][pattern_id] = domain_success_rate

        if not domain_pattern_success.get(domain):
            # No domain-specific data, fall back to universal best
            return self.suggest_path_for_new_domain(domain, available_rungs)

        # Use best pattern FOR THIS DOMAIN
        best_pattern_id = max(
            domain_pattern_success[domain].items(),
            key=lambda x: x[1]
        )[0]

        pattern = self.patterns[best_pattern_id]
        return pattern.domain_instantiations.get(domain)

    def _get_domain_success_rate(self, pattern_id: str, domain: str) -> float:
        """Get success rate of pattern in specific domain."""
        # Would query from database: SELECT COUNT(*) WHERE pattern=X AND domain=Y AND success=True
        # For now, return placeholder
        return 0.5
```

### 7.5 Negative Reputation Penalty

KK→UU (contradiction) should be worse than a fresh start - apply trust penalty.

```python
# Update to GraphEvolutionManager

def apply_contradiction_penalty(self, failed_path: List[str]):
    """
    Apply negative reputation to edges in a path that led to contradiction.
    This is WORSE than having no history - we actively distrust this path.
    """
    CONTRADICTION_PENALTY = -0.5  # Significant negative weight

    for i in range(len(failed_path) - 1):
        source, target = failed_path[i], failed_path[i + 1]
        edge_id = f"{source}→{target}"

        if edge_id not in self.edge_trust:
            self.edge_trust[edge_id] = EdgeTrustRecord(edge_id=edge_id)

        record = self.edge_trust[edge_id]
        record.failure_count += 1
        record.cumulative_confidence_gain += CONTRADICTION_PENALTY

        # Decay recent success memory - contradiction calls past successes into question
        record.success_count = int(record.success_count * 0.8)
```

**Deliverables**:
- `engines/cognition/graph_evolution.py` - 300 LOC
- `engines/cognition/rung_roles.py` - 100 LOC
- `engines/cognition/path_crystallization.py` - 200 LOC
- `engines/cognition/process_knowledge.py` - 250 LOC

---

## Phase 7.5: Stabilization Week 2 [NEW FROM PART 5]

**Purpose**: Graph evolution introduces long-term feedback loops. Stabilize before declaring done.

**Focus Areas**:
1. Verify edge trust accumulates correctly over 100+ games
2. Validate crystallization doesn't occur prematurely
3. Check process knowledge extraction accuracy
4. Ensure domain-specific patterns emerge as expected
5. Review negative reputation decay (not too aggressive)

**Exit Criteria**:
- Edge trust variance stabilizes (not oscillating wildly)
- Crystallized paths have >90% success rate when used
- Abstract patterns successfully apply to new domains
- No unexpected crystallization for rare game types

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Performance regression | Shadow mode, gradual rollout |
| Edge config errors | EdgeInferenceEngine auto-discovery + three-list validation |
| Infinite loops | MAX_ITERATIONS cap, cycle detection, CatastrophicFallback |
| Memory from checkpoints | LRU cache on checkpoints (max 5) |
| Algorithm selection overhead | MetaPlannerCache with 90%+ hit rate |
| Wrong algorithm for domain | Adaptive mid-search switching |
| **Thrashing between quadrants** | HysteresisManager: confirmation counts + cooldowns + signal decay |
| **Missed transitions** | EpistemicLogger: log all rung results, post-hoc transition detection |
| **Wrong transition response** | TRANSITION_RESPONSES is configurable, can tune |
| **KK→UU loop (repeated contradictions)** | CatastrophicFallback after 5 contradictions |
| **Stale epistemic state** | Reset tracker at start of each decision |
| **Question accumulation** | QuestionManager: demote after 3 failed attempts, lifecycle management |
| **UK detection latency** | UKPotentialIndex with bloom filter for O(1) "definitely no" |
| **Debug difficulty** | Structured EpistemicTraceEntry with queryable SQL schema |
| **Edge trust data loss** | GraphEvolutionManager persists to database, survives restarts |
| **Premature crystallization** | Domain-relative threshold: min(10, 50% of domain games) |
| **Abstract pattern overfitting** | ProcessKnowledgeExtractor requires 3+ domains before suggesting |
| **Role misclassification** | RUNG_ROLE_MAP is configurable, validated against empirical data |
| **Catastrophic router failure** | CatastrophicFallback circuit breaker falls back to static ordering |
| **Empty frontier** | CatastrophicFallback triggers after 3 consecutive empty frontiers |
| **UK cold start** | Structural UK fallback uses rung metadata for first game/new type |
| **Wrong answerable_by mapping** | Auto-infer from rung READ patterns, three-list validation |
| **Stateful algorithm bugs** | Stateless algorithms with SearchContext - all state explicit |
| **Integration bugs** | Two stabilization weeks (Phase 5.5, 7.5) for debugging |
| **Aggressive timeline** | Built-in stabilization weeks, adjust based on Phase 0 findings |

---

## Complexity Summary by Domain (Reference) [ENHANCED WITH PART 3]

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ALGORITHM SELECTION BY DOMAIN                             │
│                                                                              │
│  Domain          Algorithm              Complexity       When to Use         │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Physics         Topological DP         O(V + E)         Causal chains,     │
│                                                          no cycles           │
│  Symbolic        Bidirectional          O(b^(d/2))       Known goal state   │
│                                                          (key→lock)          │
│  Spatial         Hierarchical A*        O(C² + V_c²)     Region clusters    │
│  Exploitation    Greedy Best-First      O(V)             High confidence    │
│                                                          (>0.8)              │
│  Exploration     Info-Maximizing        O(iter × d)      Low confidence     │
│                                                          (<0.3)              │
│  Time Pressure   Beam Search            O(k × b × d)     Budget < 20%       │
│  Contradiction   Backtracking A*        O(E × bt)        Conflict detected  │
│  General         Landmark A*            O(E), O(1) h     Default fallback   │
│                                                                              │
│  Key insight: V=63 rungs, E≈200 edges, b≈4 branching, d≈8 depth            │
│  So even O(V²) = O(4000) is tractable, but O(V+E) = O(263) is better       │
│                                                                              │
│  Biggest wins:                                                               │
│    - Topological DP on DAGs: O(V²) → O(V+E)                                 │
│    - Bidirectional: O(b^d) → O(b^(d/2)) = O(65536) → O(256)                │
│    - Hierarchical: O(V²) → O(C² + V_c²) = O(36 + 225) = O(261)             │
│    - Landmarks: O(V) heuristic → O(1) heuristic                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│              EPISTEMIC QUADRANT ALGORITHMS (PART 3)                         │
│                                                                              │
│  Quadrant   Algorithm                 Best For                               │
│  ─────────────────────────────────────────────────────────────────────────  │
│  KK         GreedyExploitation        High confidence, go fast               │
│  KU         TargetedQuestionSearch    Specific questions, A* toward answers  │
│  UK         RetrievalSearch           Untapped cached/network knowledge      │
│  UU         InformationMaximizing     Novel territory, UCB-style exploration │
│                                                                              │
│  TRANSITION-DRIVEN COMPLEXITY WIN:                                          │
│                                                                              │
│  Static A* on 63 rungs:                                                     │
│    - Expand all reachable nodes: O(63 × 25) = O(1575)                       │
│    - No early termination, no exclusions, wrong algorithm fit               │
│                                                                              │
│  Transition-Driven (Part 3):                                                │
│    - Typical path: UU(5) → KU(3) → KK(2) = 10 rungs                        │
│    - With early termination: ~8 rungs                                       │
│    - With focused search: ~6 rungs                                          │
│    - With exclusions (post-contradiction): ~5 rungs                         │
│    - With algorithm fit: ~4 rungs per phase = O(12-26) total               │
│                                                                              │
│  RESULT: O(26) typical vs O(1575) static = 60x improvement                 │
│                                                                              │
│  Why it works:                                                               │
│    1. Early termination in KK (high confidence = stop)                      │
│    2. Focused search in KU (only toward answerers)                          │
│    3. Exclusions after KK→UU (don't repeat failed path)                     │
│    4. Algorithm fit (each quadrant uses optimal search)                     │
│    5. Transitions are sparse (typically 2-4 per decision)                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Success Criteria

Phase 0-7 complete (with stabilization weeks) when:

1. [x] All 63+ rungs mapped to cognitive graph nodes
2. [ ] EdgeInferenceEngine auto-discovers 150+ edges with three-list validation
3. [ ] MetaPlannerCache achieves >90% hit rate
4. [ ] PrecomputationManager initializes <100ms at startup
5. [ ] Blackboard replaces ad-hoc context for 80% of data
6. [ ] Adaptive algorithm switching triggers correctly on domain change
7. [ ] Cognitive router matches or exceeds static ordering performance
8. [ ] Average rungs evaluated drops from ~40 to <15 per decision
9. [ ] ORDERING_PRESETS deprecated
10. [ ] **EpistemicTracker correctly identifies quadrant (KK/KU/UK/UU)**
11. [ ] **Transition detection triggers algorithm switch within 1 rung**
12. [ ] **Typical decision uses <30 rung evaluations (vs 1500 static)**
13. [ ] **KK→UU (contradiction) correctly triggers exclusion-based exploration**
14. [ ] **UU→KU (question discovery) correctly triggers targeted search**
15. [ ] **HysteresisManager prevents >2 transitions between same quadrant pair per decision**
16. [ ] **QuestionManager tracks question lifecycle (RAISED→ACTIVE→ANSWERED/ABANDONED)**
17. [ ] **UKPotentialIndex bloom filter has <5% false positive rate**
18. [ ] **EpistemicLogger captures all traces in queryable format**
19. [ ] **Thrashing score <0.3 on average across decisions**
20. [ ] **Question resolution rate >60%**
21. [ ] **GraphEvolutionManager accumulates edge trust across 100+ games**
22. [ ] **PathCrystallizer identifies ≥3 crystallized paths per major domain**
23. [ ] **ProcessKnowledgeExtractor extracts ≥5 reusable abstract patterns**
24. [ ] **Crystallized path lookup reduces search time by >80% for known domains**
25. [ ] **Contradiction penalty causes failed paths to be avoided in subsequent games**
26. [ ] **CatastrophicFallback triggers <1% of decisions** [NEW FROM PART 5]
27. [ ] **UK cold-start works correctly for first game** [NEW FROM PART 5]
28. [ ] **Question answerable_by auto-inference has >70% accuracy** [NEW FROM PART 5]
29. [ ] **Zero catastrophic fallbacks in 100 consecutive games (Phase 5.5 exit)** [NEW FROM PART 5]
30. [ ] **Stabilization Week 2 exits with stable edge trust variance** [NEW FROM PART 5]

---

## Appendix A: Immediate Next Steps

### This Week (Phase 0 Start)

1. **Run dependency scan**: `python manual_tools/analysis/analyze_dependencies.py --core`
2. **Create EdgeInferenceEngine prototype**: Auto-discover edges from slot dataflow
3. **Draft edge JSON**: Start with obvious dependencies (survey→control_tracker, etc.)
4. **Create blackboard stub**: Empty class with slot() method for interface testing
5. **Profile current system**: Baseline timing for comparison
6. **Create EpistemicTracker stub**: Quadrant classification from blackboard state
7. **Define RungResult.raises_questions protocol**: Standardize question discovery
8. **Create RUNG_QUESTION_TEMPLATES**: Map rung categories to typical questions
9. **Draft RUNG_ROLE_MAP**: Classify all 63+ rungs by role (entry/leverage/compounding/resolution)
10. **Run answerable_by auto-inference**: `python manual_tools/infer_answerable_by.py` [NEW FROM PART 5]
11. **Define EdgeTrustRecord/CrystallizedPath**: Add to blackboard.py NOW for forward compat [NEW FROM PART 5]

---

## Appendix B: File Structure

After implementation, new files:

```
engines/
  cognition/
    __init__.py
    blackboard.py             # Phase 1 - 350 LOC (+50 for Phase 7 forward compat)
    epistemic_state.py        # Phase 1.5 - 150 LOC [SPLIT FROM PART 5]
    epistemic_tracker.py      # Phase 1.5 - 200 LOC [SPLIT FROM PART 5]
    contradiction_detector.py # Phase 1.5 - 150 LOC [SPLIT FROM PART 5]
    hysteresis.py             # Phase 1.6 - 150 LOC
    question_manager.py       # Phase 1.6 - 200 LOC
    uk_potential_index.py     # Phase 1.6 - 250 LOC (+50 for cold-start fallback)
    epistemic_logging.py      # Phase 1.6 - 250 LOC
    cognitive_graph.py        # Phase 2 - 250 LOC
    edge_inference.py         # Phase 2.5 - 400 LOC (+50 for three-list validation)
    search_context.py         # Phase 3 - 150 LOC [NEW FROM PART 5]
    algorithms.py             # Phase 3 - 700 LOC
    meta_planner.py           # Phase 3 - 300 LOC
    precomputation.py         # Phase 3.5 - 200 LOC
    catastrophic_fallback.py  # Phase 4 - 150 LOC [NEW FROM PART 5]
    cognitive_router.py       # Phase 4 - 550 LOC (+50 for fallback integration)
    graph_evolution.py        # Phase 7 - 300 LOC
    rung_roles.py             # Phase 7 - 100 LOC
    path_crystallization.py   # Phase 7 - 250 LOC (+50 for domain-relative threshold)
    process_knowledge.py      # Phase 7 - 300 LOC (+50 for domain-specific patterns)

config/
  cognitive_edges.json        # Phase 2 - auto-generated + three-list validated
  transition_responses.json   # Phase 1.5 - epistemic transition mappings
  question_templates.json     # Phase 1.6 - rung category → question templates (+ auto-inferred)
  question_taxonomy_inferred.json  # Phase 0.5 - auto-inferred answerable_by [NEW FROM PART 5]
  rung_roles.json             # Phase 7 - rung → role mapping

manual_tools/
  infer_answerable_by.py      # Phase 0.5 - 100 LOC [NEW FROM PART 5]
  validate_inferred_edges.py  # Phase 2.5 - 150 LOC (+50 for three-list)
  visualize_epistemic_flow.py # Phase 1.5 - 150 LOC
  analyze_epistemic_traces.py # Phase 1.6 - 200 LOC
  analyze_graph_evolution.py  # Phase 7 - 150 LOC
```

**Total new code**: ~5650 LOC (was 5000, +650 for Part 5 refinements)
**Estimated time**: 12-13 weeks (was 10-11, +2 for stabilization weeks)

---

## Appendix C: Example Decision Traces (Part 3)

### Trace 1: Typical Discovery Path

```
Action 1:
  Quadrant: UU (novel game, no knowledge)
  Algorithm: InformationMaximizingSearch
  Rungs: survey → frame_interpretation → sparse_grid
  Transitions: None

Action 2:
  Quadrant: UU → KU (discovered: "what controls blue object?")
  Algorithm: TargetedQuestionSearch
  Rungs: control_tracker → object_interaction_test
  Transitions: UU→KU (focus)

Action 3:
  Quadrant: KU → KK (answered: player controls blue square)
  Algorithm: GreedyExploitation
  Rungs: smart_action_selection
  Transitions: KU→KK (exploit)
  COMMIT: ACTION3 with confidence 0.89

Total: 6 rungs, 2 transitions, O(6 × 4) = O(24)
```

### Trace 2: Contradiction Recovery

```
Action 1-5:
  Path: survey → control_tracker → theory_gate → hypothesis_test
  Quadrant: UU → KU → KK (confidence 0.82)

Action 6:
  Result: physics_game=True contradicts control_hypothesis
  Quadrant: KK → UU (severe contradiction)
  Algorithm: ExplorationWithExclusions
  Excluded: {control_tracker, theory_gate}  # failed path

Action 7-9:
  Path: frame_interpretation → event_understanding → physics_action
  Quadrant: UU → KU → KK
  COMMIT: ACTION2 with confidence 0.91

Total: 9 rungs, 4 transitions, backtrack saved 15+ wasted rungs
```

---

## Appendix D: Epistemic Health Dashboard (Part 3.5)

### Real-Time Monitoring Display

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      EPISTEMIC HEALTH DASHBOARD                              │
│                                                                              │
│ ┌─────────────────────────────┐  ┌─────────────────────────────────────────┐│
│ │ CURRENT DECISION CYCLE      │  │ SESSION STATISTICS                      ││
│ │                             │  │                                         ││
│ │ Quadrant: KU (2 ticks)      │  │ Transitions:                            ││
│ │ Open Questions: 2           │  │   UU→KU: 3  KU→KK: 2  KK→KU: 1         ││
│ │   - "what's controllable?"  │  │                                         ││
│ │   - "is this physics?"      │  │ Contradictions: 1                       ││
│ │                             │  │ Avg ticks to KK: 4.2                    ││
│ │ Algorithm: TargetedSearch   │  │ Question Resolution: 67%                ││
│ │ Last Rung: control_tracker  │  │                                         ││
│ │ Confidence: 0.52            │  │ Decisions This Session: 15              ││
│ └─────────────────────────────┘  └─────────────────────────────────────────┘│
│                                                                              │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ HEALTH INDICATORS                                                       │ │
│ │                                                                         │ │
│ │ Thrashing Score:    [====------] 0.12 (LOW - stable)                   │ │
│ │ Convergence:        [========--] 0.82 (GOOD - trending toward KK)       │ │
│ │ Question Backlog:   [==--------] 2/10 (OK)                             │ │
│ │ UK Utilization:     [======----] 0.60 (MEDIUM - cached knowledge used) │ │
│ │                                                                         │ │
│ │ Hysteresis Status:                                                      │ │
│ │   KK cooldown: ACTIVE (2 ticks remaining)                              │ │
│ │   Pending signals: KU→KK (1/2 confirmations)                           │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ RECENT TRACE (last 7 ticks)                                            │ │
│ │                                                                         │ │
│ │ Tick  Quad  Transition  Algorithm     Rung              Conf   Notes    │ │
│ │ ───────────────────────────────────────────────────────────────────────│ │
│ │ 001   UU    -           InfoMax       survey            0.25   5 objs   │ │
│ │ 002   KU    UU→KU       InfoMax→Targ  -                 0.25   Q raised │ │
│ │ 003   KU    -           Targeted      frame_interp      0.40   physics  │ │
│ │ 004   KU    -           Targeted      control_tracker   0.52   testing  │ │
│ │ 005   ...                                                               │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### SQL Queries for Post-Hoc Analysis

```sql
-- Find all decisions that thrashed (>3 quadrant changes)
SELECT game_id, decision_id, COUNT(DISTINCT quadrant) as quadrants_visited
FROM epistemic_traces
GROUP BY game_id, decision_id
HAVING COUNT(*) > 1 AND COUNT(DISTINCT quadrant) > 3;

-- Find successful contradiction recovery patterns
SELECT t1.transition, t2.quadrant as recovery_quadrant,
       COUNT(*) as occurrences, AVG(t2.confidence_after) as avg_recovery_conf
FROM epistemic_traces t1
JOIN epistemic_traces t2 ON t1.game_id = t2.game_id
                         AND t1.decision_id = t2.decision_id
                         AND t2.tick > t1.tick
WHERE t1.transition = 'KK→UU'
  AND t2.quadrant = 'KK'
GROUP BY t1.transition, t2.quadrant;

-- Average ticks per quadrant by game type
SELECT g.game_type, t.quadrant, AVG(ticks_in_quadrant) as avg_ticks
FROM (
    SELECT game_id, quadrant,
           COUNT(*) as ticks_in_quadrant
    FROM epistemic_traces
    GROUP BY game_id, decision_id, quadrant
) t
JOIN games g ON t.game_id = g.id
GROUP BY g.game_type, t.quadrant
ORDER BY g.game_type, avg_ticks DESC;

-- Question resolution rate by rung category
SELECT r.category,
       SUM(CASE WHEN q.status = 'answered' THEN 1 ELSE 0 END) as answered,
       COUNT(*) as total,
       ROUND(100.0 * SUM(CASE WHEN q.status = 'answered' THEN 1 ELSE 0 END) / COUNT(*), 1) as resolution_pct
FROM questions q
JOIN rungs r ON q.raised_by_rung = r.name
GROUP BY r.category
ORDER BY resolution_pct DESC;
```

---

**Document Owner**: LLM Autonomous System
**Review Cadence**: Every 5 generations
