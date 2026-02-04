"""
Edge Inference Engine - Automatic Cognitive Edge Discovery

Phase 2.5 Implementation - Cognitive Routing

This module automates the discovery of edges between rungs in the cognitive graph.
Instead of manually specifying O(n²) edges, we infer them from:

1. STATIC ANALYSIS: Slot dataflow (writes → reads dependencies)
2. RUNTIME OBSERVATION: Track actual rung transitions and outcomes
3. HEURISTIC RULES: Category-based edge inference

The engine produces:
- DEPENDENCY edges: Rung A writes slot that Rung B reads
- IMPLICATION edges: Rung A success implies B likely succeeds
- FALLBACK edges: If A fails, try B (same slot, different approach)
- COACTIVATION edges: A and B often succeed together

Output is classified into three lists (per Part 5):
- CONFIDENT: Auto-accept (strong evidence)
- UNCERTAIN: Human review needed
- MISSING: Expected but not found
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

import hashlib
import inspect
import json
import logging
import re
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND CONSTANTS
# =============================================================================

class EdgeType(Enum):
    """Types of edges in the cognitive graph."""
    DEPENDENCY = "dependency"        # A must run before B (data dependency)
    IMPLICATION = "implication"      # If A succeeds, B likely succeeds
    CONTRADICTION = "contradiction"  # A and B should not both activate
    REFINEMENT = "refinement"        # B refines/improves A's output
    FALLBACK = "fallback"           # If A fails, try B
    COACTIVATION = "coactivation"   # A and B often succeed together


class InferenceConfidence(Enum):
    """Confidence levels for inferred edges."""
    CONFIDENT = "confident"      # Auto-accept (strong evidence)
    UNCERTAIN = "uncertain"      # Human review needed
    SPECULATIVE = "speculative"  # Low evidence, keep for observation


class InferenceSource(Enum):
    """Source of edge inference."""
    STATIC_DATAFLOW = "static_dataflow"      # From slot read/write analysis
    STATIC_CATEGORY = "static_category"       # From category relationships
    RUNTIME_SEQUENCE = "runtime_sequence"     # From observed sequences
    RUNTIME_OUTCOME = "runtime_outcome"       # From success/failure patterns
    HEURISTIC_RULE = "heuristic_rule"        # From domain knowledge rules


# Slot patterns that indicate reads/writes
CONTEXT_WRITE_PATTERNS = [
    r"context\[(['\"])(\w+)\1\]\s*=",        # context['slot'] =
    r"context\.setdefault\(['\"](\w+)['\"]", # context.setdefault('slot', ...)
    r"context\.update\(\{['\"](\w+)['\"]:",  # context.update({'slot': ...})
]

CONTEXT_READ_PATTERNS = [
    r"context\.get\(['\"](\w+)['\"]",          # context.get('slot')
    r"context\[(['\"])(\w+)\1\](?!\s*=)",      # context['slot'] (not assignment)
    r"context\.get\(['\"](\w+)['\"],\s*\w+\)", # context.get('slot', default)
]


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class SlotInfo:
    """Information about a slot's usage by rungs."""
    slot_name: str
    writers: Set[str] = field(default_factory=set)     # Rungs that write to this slot
    readers: Set[str] = field(default_factory=set)     # Rungs that read from this slot
    write_confidence: Dict[str, float] = field(default_factory=dict)  # writer -> confidence
    read_patterns: Dict[str, str] = field(default_factory=dict)       # reader -> pattern type

    def add_writer(self, rung_name: str, confidence: float = 1.0) -> None:
        """Record a rung that writes to this slot."""
        self.writers.add(rung_name)
        self.write_confidence[rung_name] = max(
            self.write_confidence.get(rung_name, 0.0), confidence
        )

    def add_reader(self, rung_name: str, pattern: str = "get") -> None:
        """Record a rung that reads from this slot."""
        self.readers.add(rung_name)
        self.read_patterns[rung_name] = pattern


@dataclass
class InferredEdge:
    """An edge inferred by the EdgeInferenceEngine."""
    source_rung: str
    target_rung: str
    edge_type: EdgeType
    confidence: InferenceConfidence
    score: float  # 0.0 to 1.0
    source: InferenceSource
    evidence: List[str] = field(default_factory=list)  # Supporting evidence
    condition: Optional[str] = None  # When this edge applies

    # Runtime tracking (updated during observation)
    observed_count: int = 0
    success_count: int = 0
    last_observed: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'source': self.source_rung,
            'target': self.target_rung,
            'type': self.edge_type.value,
            'confidence': self.confidence.value,
            'score': self.score,
            'inference_source': self.source.value,
            'evidence': self.evidence,
            'condition': self.condition,
            'observed_count': self.observed_count,
            'success_count': self.success_count,
            'last_observed': self.last_observed.isoformat() if self.last_observed else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InferredEdge':
        """Create from dictionary."""
        return cls(
            source_rung=data['source'],
            target_rung=data['target'],
            edge_type=EdgeType(data['type']),
            confidence=InferenceConfidence(data['confidence']),
            score=data['score'],
            source=InferenceSource(data['inference_source']),
            evidence=data.get('evidence', []),
            condition=data.get('condition'),
            observed_count=data.get('observed_count', 0),
            success_count=data.get('success_count', 0),
            last_observed=datetime.fromisoformat(data['last_observed']) if data.get('last_observed') else None
        )

    def edge_key(self) -> Tuple[str, str, str]:
        """Unique key for this edge."""
        return (self.source_rung, self.target_rung, self.edge_type.value)


@dataclass
class TransitionOutcome:
    """Outcome of transitioning between rungs (runtime observation)."""
    from_rung: str
    to_rung: str
    timestamp: datetime
    success: bool  # Did target rung produce useful result?
    confidence_delta: float  # Change in overall confidence
    led_to_backtrack: bool  # Did this transition lead to backtracking?
    context_hash: str  # Hash of context state for deduplication


@dataclass
class RungMetadata:
    """Extracted metadata about a rung."""
    name: str
    category: str
    default_priority: int
    confidence_threshold: float
    required_primitives: List[str]
    slots_written: Set[str] = field(default_factory=set)
    slots_read: Set[str] = field(default_factory=set)
    engines_used: Set[str] = field(default_factory=set)
    source_code: str = ""


@dataclass
class EdgeValidationResult:
    """Result of three-list edge validation."""
    confident: List[InferredEdge] = field(default_factory=list)   # Auto-accept
    uncertain: List[InferredEdge] = field(default_factory=list)   # Human review
    missing: List[Dict[str, Any]] = field(default_factory=list)   # Investigate


# =============================================================================
# STATIC ANALYSIS LAYER
# =============================================================================

class StaticAnalyzer:
    """
    Analyzes rung source code to extract slot read/write patterns.

    This forms the foundation of DEPENDENCY edge inference:
    If Rung A writes slot X and Rung B reads slot X, there's a dependency.
    """

    def __init__(self):
        self.slot_info: Dict[str, SlotInfo] = {}  # slot_name -> SlotInfo
        self.rung_metadata: Dict[str, RungMetadata] = {}  # rung_name -> metadata
        self._write_patterns = [re.compile(p) for p in CONTEXT_WRITE_PATTERNS]
        self._read_patterns = [re.compile(p) for p in CONTEXT_READ_PATTERNS]

    def analyze_rung(self, rung_class: type) -> RungMetadata:
        """
        Extract metadata from a rung class via source code analysis.

        Args:
            rung_class: The DecisionRung subclass to analyze

        Returns:
            RungMetadata with extracted slot patterns
        """
        name = getattr(rung_class, 'name', rung_class.__name__.lower())

        metadata = RungMetadata(
            name=name,
            category=getattr(rung_class, 'category', 'unknown'),
            default_priority=getattr(rung_class, 'default_priority', 50),
            confidence_threshold=getattr(rung_class, 'confidence_threshold', 0.3),
            required_primitives=getattr(rung_class, 'required_primitives', [])
        )

        # Get source code of evaluate method
        try:
            source = inspect.getsource(rung_class)
            metadata.source_code = source

            # Extract slot writes
            for pattern in self._write_patterns:
                for match in pattern.finditer(source):
                    slot_name = match.group(2) if len(match.groups()) > 1 else match.group(1)
                    metadata.slots_written.add(slot_name)
                    self._record_slot_write(slot_name, name)

            # Extract slot reads
            for pattern in self._read_patterns:
                for match in pattern.finditer(source):
                    slot_name = match.group(2) if len(match.groups()) > 1 else match.group(1)
                    metadata.slots_read.add(slot_name)
                    self._record_slot_read(slot_name, name)

            # Extract engine usage (self.engines.X patterns)
            engine_pattern = re.compile(r'self\.engines\.(\w+)')
            for match in engine_pattern.finditer(source):
                metadata.engines_used.add(match.group(1))

        except (TypeError, OSError) as e:
            logger.warning(f"[EDGE-INFERENCE] Could not analyze {name}: {e}")

        self.rung_metadata[name] = metadata
        return metadata

    def _record_slot_write(self, slot_name: str, rung_name: str) -> None:
        """Record a slot write."""
        if slot_name not in self.slot_info:
            self.slot_info[slot_name] = SlotInfo(slot_name=slot_name)
        self.slot_info[slot_name].add_writer(rung_name)

    def _record_slot_read(self, slot_name: str, rung_name: str) -> None:
        """Record a slot read."""
        if slot_name not in self.slot_info:
            self.slot_info[slot_name] = SlotInfo(slot_name=slot_name)
        self.slot_info[slot_name].add_reader(rung_name)

    def infer_dependency_edges(self) -> List[InferredEdge]:
        """
        Infer DEPENDENCY edges from slot dataflow.

        Rule: If A writes slot X and B reads slot X, A -> B is a dependency.
        """
        edges: List[InferredEdge] = []

        for slot_name, info in self.slot_info.items():
            for writer in info.writers:
                for reader in info.readers:
                    if writer == reader:
                        continue  # Skip self-edges

                    # Calculate confidence based on write confidence
                    write_conf = info.write_confidence.get(writer, 0.5)
                    score = min(0.9, write_conf)  # Cap at 0.9 for static analysis

                    # Determine confidence level
                    if score > 0.7:
                        confidence = InferenceConfidence.CONFIDENT
                    elif score > 0.4:
                        confidence = InferenceConfidence.UNCERTAIN
                    else:
                        confidence = InferenceConfidence.SPECULATIVE

                    edge = InferredEdge(
                        source_rung=writer,
                        target_rung=reader,
                        edge_type=EdgeType.DEPENDENCY,
                        confidence=confidence,
                        score=score,
                        source=InferenceSource.STATIC_DATAFLOW,
                        evidence=[f"'{writer}' writes '{slot_name}', '{reader}' reads it"]
                    )
                    edges.append(edge)

        return edges

    def get_rung_dependencies(self, rung_name: str) -> Dict[str, Set[str]]:
        """
        Get the slots a rung depends on (reads) and provides (writes).

        Returns:
            Dict with 'reads' and 'writes' slot sets
        """
        metadata = self.rung_metadata.get(rung_name)
        if not metadata:
            return {'reads': set(), 'writes': set()}
        return {
            'reads': metadata.slots_read.copy(),
            'writes': metadata.slots_written.copy()
        }


# =============================================================================
# CATEGORY-BASED INFERENCE
# =============================================================================

# Category adjacency rules (which categories naturally flow into which)
CATEGORY_ADJACENCY = {
    'orientation': {'hypothesis', 'exploitation', 'filter'},  # Survey -> hypothesize -> act
    'hypothesis': {'exploitation', 'filter', 'metacognition'},
    'exploitation': {'filter', 'metacognition'},
    'filter': {'exploitation', 'metacognition'},  # Filters can gate exploitation
    'metacognition': {'orientation', 'hypothesis'},  # Meta can trigger re-survey
    'emergency': set(),  # Emergency is terminal
}

# Categories that are natural fallbacks for each other
CATEGORY_FALLBACKS = {
    'hypothesis': 'orientation',    # If hypothesis fails, re-survey
    'exploitation': 'hypothesis',   # If exploit fails, re-hypothesize
    'filter': 'exploitation',       # If filtered, try different exploit
    'metacognition': 'orientation', # If meta confused, start over
}


class CategoryAnalyzer:
    """
    Infers edges based on category relationships between rungs.

    Uses domain knowledge about how categories relate:
    - ORIENTATION -> HYPOTHESIS -> EXPLOITATION is natural flow
    - FILTER can gate any category
    - METACOGNITION can trigger any category
    """

    def __init__(self, rung_metadata: Dict[str, RungMetadata]):
        self.rung_metadata = rung_metadata
        self._category_rungs: Dict[str, Set[str]] = defaultdict(set)

        for name, meta in rung_metadata.items():
            self._category_rungs[meta.category].add(name)

    def infer_implication_edges(self) -> List[InferredEdge]:
        """
        Infer IMPLICATION edges based on category adjacency.

        If categories A and B are adjacent, successful rungs in A imply
        rungs in B might be useful.
        """
        edges: List[InferredEdge] = []

        for source_cat, target_cats in CATEGORY_ADJACENCY.items():
            source_rungs = self._category_rungs.get(source_cat, set())

            for target_cat in target_cats:
                target_rungs = self._category_rungs.get(target_cat, set())

                for source_rung in source_rungs:
                    for target_rung in target_rungs:
                        if source_rung == target_rung:
                            continue

                        # Priority-based scoring
                        source_meta = self.rung_metadata.get(source_rung)
                        target_meta = self.rung_metadata.get(target_rung)

                        if not source_meta or not target_meta:
                            continue

                        # Lower priority difference = stronger implication
                        priority_diff = abs(source_meta.default_priority - target_meta.default_priority)
                        score = max(0.3, 0.7 - (priority_diff * 0.01))

                        edge = InferredEdge(
                            source_rung=source_rung,
                            target_rung=target_rung,
                            edge_type=EdgeType.IMPLICATION,
                            confidence=InferenceConfidence.UNCERTAIN,
                            score=score,
                            source=InferenceSource.STATIC_CATEGORY,
                            evidence=[f"Category flow: {source_cat} -> {target_cat}"]
                        )
                        edges.append(edge)

        return edges

    def infer_fallback_edges(self) -> List[InferredEdge]:
        """
        Infer FALLBACK edges based on category fallback rules.

        When a rung in category X fails, fallback to category Y.
        """
        edges: List[InferredEdge] = []

        for fail_cat, fallback_cat in CATEGORY_FALLBACKS.items():
            fail_rungs = self._category_rungs.get(fail_cat, set())
            fallback_rungs = self._category_rungs.get(fallback_cat, set())

            for fail_rung in fail_rungs:
                for fallback_rung in fallback_rungs:
                    if fail_rung == fallback_rung:
                        continue

                    edge = InferredEdge(
                        source_rung=fail_rung,
                        target_rung=fallback_rung,
                        edge_type=EdgeType.FALLBACK,
                        confidence=InferenceConfidence.UNCERTAIN,
                        score=0.5,
                        source=InferenceSource.STATIC_CATEGORY,
                        evidence=[f"Fallback rule: {fail_cat} -> {fallback_cat}"],
                        condition=f"{fail_rung}_failed"
                    )
                    edges.append(edge)

        return edges

    def infer_coactivation_edges(self) -> List[InferredEdge]:
        """
        Infer COACTIVATION edges for rungs in the same category.

        Rungs in the same category often work together.
        """
        edges: List[InferredEdge] = []

        for category, rungs in self._category_rungs.items():
            rung_list = list(rungs)
            for i, rung_a in enumerate(rung_list):
                for rung_b in rung_list[i+1:]:
                    # Score based on priority similarity
                    meta_a = self.rung_metadata.get(rung_a)
                    meta_b = self.rung_metadata.get(rung_b)

                    if not meta_a or not meta_b:
                        continue

                    priority_diff = abs(meta_a.default_priority - meta_b.default_priority)
                    if priority_diff < 20:  # Close priorities = likely coactivate
                        edge = InferredEdge(
                            source_rung=rung_a,
                            target_rung=rung_b,
                            edge_type=EdgeType.COACTIVATION,
                            confidence=InferenceConfidence.SPECULATIVE,
                            score=0.4,
                            source=InferenceSource.STATIC_CATEGORY,
                            evidence=[f"Same category ({category}), similar priority"]
                        )
                        edges.append(edge)

        return edges


# =============================================================================
# RUNTIME OBSERVATION LAYER
# =============================================================================

class RuntimeObserver:
    """
    Observes actual rung transitions during gameplay to refine edge inferences.

    This layer:
    - Tracks which rung transitions actually occur
    - Measures success/failure of transitions
    - Updates edge confidence based on real data
    """

    def __init__(self, max_history: int = 10000):
        self.transitions: List[TransitionOutcome] = []
        self.max_history = max_history

        # Aggregated statistics
        self._transition_counts: Dict[Tuple[str, str], int] = defaultdict(int)
        self._transition_successes: Dict[Tuple[str, str], int] = defaultdict(int)
        self._sequence_patterns: Dict[Tuple[str, ...], int] = defaultdict(int)  # Common sequences

    def record_transition(
        self,
        from_rung: str,
        to_rung: str,
        success: bool,
        confidence_delta: float,
        led_to_backtrack: bool,
        context: Dict[str, Any]
    ) -> None:
        """
        Record a rung-to-rung transition.

        Args:
            from_rung: Source rung name
            to_rung: Target rung name
            success: Whether target produced useful result
            confidence_delta: Change in overall decision confidence
            led_to_backtrack: Whether this transition eventually led to backtracking
            context: Current context state (hashed for deduplication)
        """
        # Create context hash for deduplication
        context_hash = self._hash_context(context)

        outcome = TransitionOutcome(
            from_rung=from_rung,
            to_rung=to_rung,
            timestamp=datetime.now(),
            success=success,
            confidence_delta=confidence_delta,
            led_to_backtrack=led_to_backtrack,
            context_hash=context_hash
        )

        self.transitions.append(outcome)

        # Update aggregates
        key = (from_rung, to_rung)
        self._transition_counts[key] += 1
        if success:
            self._transition_successes[key] += 1

        # Prune old transitions
        if len(self.transitions) > self.max_history:
            self.transitions = self.transitions[-self.max_history:]

    def record_sequence(self, rungs: List[str], success: bool) -> None:
        """Record a sequence of rungs that led to a decision."""
        if len(rungs) >= 2:
            key = tuple(rungs)
            self._sequence_patterns[key] += 1

    def _hash_context(self, context: Dict[str, Any]) -> str:
        """Create a hash of context for deduplication."""
        # Hash only stable keys
        stable_keys = ['game_id', 'level', 'action_count']
        stable_data = {k: str(context.get(k, '')) for k in stable_keys}
        return hashlib.md5(json.dumps(stable_data, sort_keys=True).encode()).hexdigest()[:8]

    def get_transition_stats(self, from_rung: str, to_rung: str) -> Dict[str, Any]:
        """Get statistics for a specific transition."""
        key = (from_rung, to_rung)
        count = self._transition_counts.get(key, 0)
        successes = self._transition_successes.get(key, 0)

        return {
            'count': count,
            'successes': successes,
            'success_rate': successes / count if count > 0 else 0.0
        }

    def infer_runtime_edges(self, min_observations: int = 5) -> List[InferredEdge]:
        """
        Infer edges from observed runtime behavior.

        Args:
            min_observations: Minimum transitions to consider edge valid

        Returns:
            List of runtime-inferred edges
        """
        edges: List[InferredEdge] = []

        for (from_rung, to_rung), count in self._transition_counts.items():
            if count < min_observations:
                continue

            successes = self._transition_successes.get((from_rung, to_rung), 0)
            success_rate = successes / count

            # High success rate = IMPLICATION edge
            if success_rate > 0.7:
                edge = InferredEdge(
                    source_rung=from_rung,
                    target_rung=to_rung,
                    edge_type=EdgeType.IMPLICATION,
                    confidence=InferenceConfidence.CONFIDENT if count > 20 else InferenceConfidence.UNCERTAIN,
                    score=success_rate,
                    source=InferenceSource.RUNTIME_OUTCOME,
                    evidence=[f"Observed {count} transitions, {success_rate:.1%} success rate"],
                    observed_count=count,
                    success_count=successes
                )
                edges.append(edge)

            # Low success rate = potential CONTRADICTION
            elif success_rate < 0.3 and count > 10:
                edge = InferredEdge(
                    source_rung=from_rung,
                    target_rung=to_rung,
                    edge_type=EdgeType.CONTRADICTION,
                    confidence=InferenceConfidence.UNCERTAIN,
                    score=1.0 - success_rate,  # Inverse - higher = stronger contradiction
                    source=InferenceSource.RUNTIME_OUTCOME,
                    evidence=[f"Observed {count} transitions, only {success_rate:.1%} success rate"],
                    observed_count=count,
                    success_count=successes
                )
                edges.append(edge)

        return edges

    def get_common_sequences(self, min_count: int = 3, max_length: int = 5) -> List[Tuple[Tuple[str, ...], int]]:
        """Get commonly observed rung sequences."""
        sequences = [
            (seq, count) for seq, count in self._sequence_patterns.items()
            if count >= min_count and len(seq) <= max_length
        ]
        return sorted(sequences, key=lambda x: -x[1])


# =============================================================================
# HEURISTIC RULES
# =============================================================================

@dataclass
class HeuristicRule:
    """A heuristic rule for edge inference."""
    name: str
    description: str
    applies_to: Callable[[RungMetadata, RungMetadata], bool]
    edge_type: EdgeType
    score: float
    condition: Optional[str] = None


# Built-in heuristic rules
HEURISTIC_RULES: List[HeuristicRule] = [
    HeuristicRule(
        name="survey_first",
        description="Survey should run before most other rungs",
        applies_to=lambda src, tgt: src.name == 'survey' and tgt.category != 'orientation',
        edge_type=EdgeType.DEPENDENCY,
        score=0.8
    ),
    HeuristicRule(
        name="theory_before_test",
        description="Theory formation should precede hypothesis testing",
        applies_to=lambda src, tgt: 'theory' in src.name and 'test' in tgt.name,
        edge_type=EdgeType.DEPENDENCY,
        score=0.7
    ),
    HeuristicRule(
        name="control_before_action",
        description="Control tracking should precede smart action selection",
        applies_to=lambda src, tgt: src.name == 'control_tracker' and 'action' in tgt.name,
        edge_type=EdgeType.DEPENDENCY,
        score=0.75
    ),
    HeuristicRule(
        name="network_fallback",
        description="Network wisdom is a fallback when local hypotheses fail",
        applies_to=lambda src, tgt: src.category == 'hypothesis' and tgt.name == 'network_wisdom',
        edge_type=EdgeType.FALLBACK,
        score=0.6,
        condition="hypothesis_failed"
    ),
    HeuristicRule(
        name="death_avoidance_priority",
        description="Death avoidance should gate all actions",
        applies_to=lambda src, tgt: src.name == 'death_avoidance' and tgt.category == 'exploitation',
        edge_type=EdgeType.IMPLICATION,
        score=0.9
    ),
    HeuristicRule(
        name="metacognition_reflection",
        description="Metacognition rungs can trigger re-orientation",
        applies_to=lambda src, tgt: src.category == 'metacognition' and tgt.category == 'orientation',
        edge_type=EdgeType.FALLBACK,
        score=0.5,
        condition="confidence_low"
    ),
    HeuristicRule(
        name="filter_gates_exploit",
        description="Filter rungs should gate exploitation",
        applies_to=lambda src, tgt: src.category == 'filter' and tgt.category == 'exploitation',
        edge_type=EdgeType.IMPLICATION,
        score=0.65
    ),
]


class HeuristicAnalyzer:
    """
    Applies domain-knowledge heuristic rules to infer edges.
    """

    def __init__(self, rung_metadata: Dict[str, RungMetadata], rules: Optional[List[HeuristicRule]] = None):
        self.rung_metadata = rung_metadata
        self.rules = rules or HEURISTIC_RULES

    def apply_rules(self) -> List[InferredEdge]:
        """Apply all heuristic rules to infer edges."""
        edges: List[InferredEdge] = []

        rung_list = list(self.rung_metadata.values())

        for rule in self.rules:
            for source_meta in rung_list:
                for target_meta in rung_list:
                    if source_meta.name == target_meta.name:
                        continue

                    try:
                        if rule.applies_to(source_meta, target_meta):
                            edge = InferredEdge(
                                source_rung=source_meta.name,
                                target_rung=target_meta.name,
                                edge_type=rule.edge_type,
                                confidence=InferenceConfidence.UNCERTAIN,
                                score=rule.score,
                                source=InferenceSource.HEURISTIC_RULE,
                                evidence=[f"Rule '{rule.name}': {rule.description}"],
                                condition=rule.condition
                            )
                            edges.append(edge)
                    except Exception as e:
                        logger.debug(f"[EDGE-INFERENCE] Rule {rule.name} failed: {e}")

        return edges


# =============================================================================
# MAIN ENGINE
# =============================================================================

class EdgeInferenceEngine:
    """
    Main engine for automatic cognitive edge discovery.

    Combines:
    - Static analysis (slot dataflow)
    - Category-based inference
    - Runtime observation
    - Heuristic rules

    Produces three-list validated output:
    - CONFIDENT: Auto-accept
    - UNCERTAIN: Human review
    - MISSING: Expected but not found
    """

    def __init__(self):
        self.static_analyzer = StaticAnalyzer()
        self.category_analyzer: Optional[CategoryAnalyzer] = None
        self.runtime_observer = RuntimeObserver()
        self.heuristic_analyzer: Optional[HeuristicAnalyzer] = None

        # All inferred edges (deduplicated)
        self._edges: Dict[Tuple[str, str, str], InferredEdge] = {}

        # Metadata
        self._last_inference_time: Optional[datetime] = None
        self._rung_count: int = 0

    def analyze_rungs(self, rung_classes: List[type]) -> int:
        """
        Analyze a list of rung classes to extract metadata.

        Args:
            rung_classes: List of DecisionRung subclasses

        Returns:
            Number of rungs analyzed
        """
        count = 0
        for rung_class in rung_classes:
            try:
                self.static_analyzer.analyze_rung(rung_class)
                count += 1
            except Exception as e:
                logger.warning(f"[EDGE-INFERENCE] Failed to analyze {rung_class}: {e}")

        self._rung_count = count

        # Initialize category and heuristic analyzers with metadata
        self.category_analyzer = CategoryAnalyzer(self.static_analyzer.rung_metadata)
        self.heuristic_analyzer = HeuristicAnalyzer(self.static_analyzer.rung_metadata)

        logger.info(f"[EDGE-INFERENCE] Analyzed {count} rungs, found {len(self.static_analyzer.slot_info)} slots")
        return count

    def infer_all_edges(self) -> List[InferredEdge]:
        """
        Run all inference layers and combine results.

        Returns:
            List of all inferred edges (deduplicated)
        """
        all_edges: List[InferredEdge] = []

        # Layer 1: Static dataflow analysis
        static_edges = self.static_analyzer.infer_dependency_edges()
        all_edges.extend(static_edges)
        logger.debug(f"[EDGE-INFERENCE] Static analysis: {len(static_edges)} edges")

        # Layer 2: Category-based inference
        if self.category_analyzer:
            impl_edges = self.category_analyzer.infer_implication_edges()
            fall_edges = self.category_analyzer.infer_fallback_edges()
            coact_edges = self.category_analyzer.infer_coactivation_edges()
            all_edges.extend(impl_edges)
            all_edges.extend(fall_edges)
            all_edges.extend(coact_edges)
            logger.debug(f"[EDGE-INFERENCE] Category analysis: {len(impl_edges) + len(fall_edges) + len(coact_edges)} edges")

        # Layer 3: Heuristic rules
        if self.heuristic_analyzer:
            heuristic_edges = self.heuristic_analyzer.apply_rules()
            all_edges.extend(heuristic_edges)
            logger.debug(f"[EDGE-INFERENCE] Heuristic rules: {len(heuristic_edges)} edges")

        # Layer 4: Runtime observation (if available)
        runtime_edges = self.runtime_observer.infer_runtime_edges()
        all_edges.extend(runtime_edges)
        logger.debug(f"[EDGE-INFERENCE] Runtime observation: {len(runtime_edges)} edges")

        # Deduplicate and merge
        self._merge_edges(all_edges)

        self._last_inference_time = datetime.now()

        logger.info(f"[EDGE-INFERENCE] Total unique edges: {len(self._edges)}")
        return list(self._edges.values())

    def _merge_edges(self, edges: List[InferredEdge]) -> None:
        """
        Merge edges, keeping highest confidence for duplicates.
        """
        for edge in edges:
            key = edge.edge_key()

            if key not in self._edges:
                self._edges[key] = edge
            else:
                existing = self._edges[key]

                # Keep higher confidence
                if edge.score > existing.score:
                    self._edges[key] = edge
                elif edge.score == existing.score:
                    # Merge evidence
                    existing.evidence.extend(edge.evidence)
                    existing.evidence = list(set(existing.evidence))  # Dedupe

    def record_transition(
        self,
        from_rung: str,
        to_rung: str,
        success: bool,
        confidence_delta: float = 0.0,
        led_to_backtrack: bool = False,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record a runtime transition for observation.
        """
        self.runtime_observer.record_transition(
            from_rung=from_rung,
            to_rung=to_rung,
            success=success,
            confidence_delta=confidence_delta,
            led_to_backtrack=led_to_backtrack,
            context=context or {}
        )

    def get_edges_for_rung(self, rung_name: str) -> Dict[str, List[InferredEdge]]:
        """
        Get all edges related to a specific rung.

        Returns:
            Dict with 'outgoing' and 'incoming' edge lists
        """
        outgoing = []
        incoming = []

        for edge in self._edges.values():
            if edge.source_rung == rung_name:
                outgoing.append(edge)
            if edge.target_rung == rung_name:
                incoming.append(edge)

        return {
            'outgoing': sorted(outgoing, key=lambda e: -e.score),
            'incoming': sorted(incoming, key=lambda e: -e.score)
        }

    def validate_edges(self, expected_patterns: Optional[Dict[str, Any]] = None) -> EdgeValidationResult:
        """
        Validate inferred edges using three-list categorization.

        Args:
            expected_patterns: Optional dict of expected edge patterns for "missing" detection

        Returns:
            EdgeValidationResult with confident, uncertain, and missing lists
        """
        result = EdgeValidationResult()

        for edge in self._edges.values():
            if edge.confidence == InferenceConfidence.CONFIDENT:
                result.confident.append(edge)
            else:
                result.uncertain.append(edge)

        # Check for missing edges based on expected patterns
        if expected_patterns:
            result.missing = self._find_missing_edges(expected_patterns)

        return result

    def _find_missing_edges(self, expected_patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find expected edges that weren't inferred.
        """
        missing: List[Dict[str, Any]] = []

        # Check expected dependencies
        for source, targets in expected_patterns.get('dependencies', {}).items():
            for target in targets:
                key = (source, target, EdgeType.DEPENDENCY.value)
                if key not in self._edges:
                    missing.append({
                        'source': source,
                        'target': target,
                        'expected_type': 'dependency',
                        'reason': 'Expected dependency not found in inference'
                    })

        return missing

    def export_to_json(self, filepath: str) -> None:
        """Export all edges to JSON file."""
        edges_data = {
            'version': '1.0',
            'generated_at': datetime.now().isoformat(),
            'rung_count': self._rung_count,
            'edge_count': len(self._edges),
            'edges': [e.to_dict() for e in self._edges.values()]
        }

        with open(filepath, 'w') as f:
            json.dump(edges_data, f, indent=2)

        logger.info(f"[EDGE-INFERENCE] Exported {len(self._edges)} edges to {filepath}")

    def import_from_json(self, filepath: str) -> int:
        """Import edges from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        count = 0
        for edge_data in data.get('edges', []):
            edge = InferredEdge.from_dict(edge_data)
            key = edge.edge_key()
            self._edges[key] = edge
            count += 1

        logger.info(f"[EDGE-INFERENCE] Imported {count} edges from {filepath}")
        return count

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about inferred edges."""
        by_type: Dict[str, int] = defaultdict(int)
        by_confidence: Dict[str, int] = defaultdict(int)
        by_source: Dict[str, int] = defaultdict(int)

        for edge in self._edges.values():
            by_type[edge.edge_type.value] += 1
            by_confidence[edge.confidence.value] += 1
            by_source[edge.source.value] += 1

        return {
            'total_edges': len(self._edges),
            'rung_count': self._rung_count,
            'slot_count': len(self.static_analyzer.slot_info),
            'by_type': dict(by_type),
            'by_confidence': dict(by_confidence),
            'by_source': dict(by_source),
            'last_inference': self._last_inference_time.isoformat() if self._last_inference_time else None,
            'runtime_observations': len(self.runtime_observer.transitions)
        }

    def get_slot_dataflow(self) -> Dict[str, Dict[str, Any]]:
        """Get slot read/write dataflow information."""
        result = {}
        for slot_name, info in self.static_analyzer.slot_info.items():
            result[slot_name] = {
                'writers': list(info.writers),
                'readers': list(info.readers),
                'write_confidence': info.write_confidence
            }
        return result


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_edge_inference_engine() -> EdgeInferenceEngine:
    """Factory function to create an EdgeInferenceEngine."""
    return EdgeInferenceEngine()


def load_rung_classes_from_module(module) -> List[type]:
    """
    Load all DecisionRung subclasses from a module.

    Args:
        module: The module to scan (e.g., decision_rung_system)

    Returns:
        List of DecisionRung subclasses
    """
    from decision_rung_system import DecisionRung

    rung_classes = []
    for name in dir(module):
        obj = getattr(module, name)
        if (isinstance(obj, type) and
            issubclass(obj, DecisionRung) and
            obj is not DecisionRung and
            hasattr(obj, 'name')):
            rung_classes.append(obj)

    return rung_classes
