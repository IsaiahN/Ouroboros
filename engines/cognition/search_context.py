"""
Search Context - Injectable Context for Stateless Algorithms

Phase 3.0 Implementation - Cognitive Routing

Part 5 insight: Algorithms should be STATELESS with injectable context.
The CognitiveRouter maintains a SearchContext object passed to each algorithm call.
Algorithms can REQUEST mutations to the context but don't hold state themselves.

Benefits:
- Easier to serialize/debug (full state is in context)
- Algorithms can be unit tested with mock contexts
- No hidden state causing subtle bugs
- Router has full control over state mutations
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

import copy
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class SearchPhase(Enum):
    """Phases of the search process."""
    INITIALIZATION = "initialization"
    EXPANSION = "expansion"
    EVALUATION = "evaluation"
    BACKTRACKING = "backtracking"
    TERMINATION = "termination"


class MutationType(Enum):
    """Types of mutations algorithms can request."""
    CHECKPOINT = "checkpoint"
    BACKTRACK = "backtrack"
    EXCLUDE_RUNGS = "exclude_rungs"
    UPDATE_PRIORITY = "update_priority"
    RECORD_CONTRADICTION = "record_contradiction"


# =============================================================================
# MUTATION REQUESTS
# =============================================================================

@dataclass
class MutationRequest:
    """A request from an algorithm to mutate router state."""
    mutation_type: MutationType
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0  # Higher = process first
    reason: str = ""

    @staticmethod
    def checkpoint(reason: str = "") -> 'MutationRequest':
        """Create a checkpoint request."""
        return MutationRequest(
            mutation_type=MutationType.CHECKPOINT,
            reason=reason or "Algorithm requested checkpoint"
        )

    @staticmethod
    def backtrack(checkpoint_id: int, reason: str = "") -> 'MutationRequest':
        """Create a backtrack request."""
        return MutationRequest(
            mutation_type=MutationType.BACKTRACK,
            payload={'checkpoint_id': checkpoint_id},
            priority=10,  # High priority - process first
            reason=reason or f"Backtrack to checkpoint {checkpoint_id}"
        )

    @staticmethod
    def exclude_rungs(rungs: Set[str], reason: str = "") -> 'MutationRequest':
        """Create an exclusion request."""
        return MutationRequest(
            mutation_type=MutationType.EXCLUDE_RUNGS,
            payload={'rungs': rungs},
            reason=reason or f"Exclude rungs: {rungs}"
        )

    @staticmethod
    def record_contradiction(source_rung: str, target_rung: str, details: Dict[str, Any]) -> 'MutationRequest':
        """Record a contradiction for future analysis."""
        return MutationRequest(
            mutation_type=MutationType.RECORD_CONTRADICTION,
            payload={
                'source_rung': source_rung,
                'target_rung': target_rung,
                'details': details
            },
            priority=5,
            reason=f"Contradiction: {source_rung} -> {target_rung}"
        )


# =============================================================================
# SEARCH CONTEXT
# =============================================================================

@dataclass
class SearchContext:
    """
    Injectable context for stateless algorithms.

    All algorithm state comes through this context object.
    Algorithms request mutations through the context; the router applies them.

    This design ensures:
    - Full state visibility (no hidden algorithm state)
    - Easy serialization for debugging
    - Unit testable algorithms with mock contexts
    - Router maintains control over state changes
    """

    # -------------------------------------------------------------------------
    # CURRENT STATE (read-only for algorithms)
    # -------------------------------------------------------------------------

    # Snapshot of blackboard slots relevant to search
    blackboard_snapshot: Dict[str, Any] = field(default_factory=dict)

    # Rungs already visited in this decision cycle
    visited_rungs: Set[str] = field(default_factory=set)

    # Current path taken (ordered list)
    current_path: List[str] = field(default_factory=list)

    # Current epistemic quadrant (KK, KU, UK, UU)
    current_quadrant: str = "UU"

    # Current search phase
    phase: SearchPhase = SearchPhase.INITIALIZATION

    # -------------------------------------------------------------------------
    # PRECOMPUTED DATA (injected by PrecomputationManager)
    # -------------------------------------------------------------------------

    # Landmark distances for A* heuristics - O(1) lookup
    # Structure: {landmark_name: {rung_name: distance}}
    landmark_distances: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # Cluster assignments for hierarchical search
    # Structure: {rung_name: category}
    cluster_assignments: Dict[str, str] = field(default_factory=dict)

    # Topological order (if graph is DAG, else empty)
    topological_order: List[str] = field(default_factory=list)

    # Category-level abstract graph
    # Structure: {from_category: {to_category: cost}}
    abstract_graph: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # -------------------------------------------------------------------------
    # GRAPH EVOLUTION DATA (from Phase 7, forward compatibility)
    # -------------------------------------------------------------------------

    # Trust modifiers for edges - higher = more trusted
    # Structure: {"source→target": modifier}
    edge_trust_modifiers: Dict[str, float] = field(default_factory=dict)

    # Crystallized paths by domain - skip search, use directly
    # Structure: {domain_tag: [rung_sequence]}
    crystallized_paths: Dict[str, List[str]] = field(default_factory=dict)

    # -------------------------------------------------------------------------
    # ALGORITHM CONSTRAINTS
    # -------------------------------------------------------------------------

    # Rungs to exclude from search (e.g., after contradiction)
    excluded_rungs: Set[str] = field(default_factory=set)

    # Maximum depth for this search
    max_depth: int = 20

    # Time budget remaining (0.0 to 1.0)
    time_budget: float = 1.0

    # Confidence threshold for committing
    commit_threshold: float = 0.85

    # -------------------------------------------------------------------------
    # MUTATION REQUESTS (algorithms write, router processes)
    # -------------------------------------------------------------------------

    _pending_mutations: List[MutationRequest] = field(default_factory=list)

    # -------------------------------------------------------------------------
    # STATISTICS (for debugging and optimization)
    # -------------------------------------------------------------------------

    rungs_evaluated: int = 0
    backtrack_count: int = 0
    checkpoint_count: int = 0

    # =========================================================================
    # QUERY METHODS (for algorithms to read state)
    # =========================================================================

    def get_slot(self, slot_name: str, default: Any = None) -> Any:
        """Get a slot value from the blackboard snapshot."""
        return self.blackboard_snapshot.get(slot_name, default)

    def get_confidence(self) -> float:
        """Get current maximum confidence."""
        return self.get_slot('max_confidence', 0.0)

    def get_questions(self) -> Dict[str, Any]:
        """Get active questions (KU quadrant)."""
        return self.get_slot('known_unknowns', {})

    def get_uk_candidates(self) -> List[str]:
        """Get untapped knowledge candidates (UK quadrant)."""
        return self.get_slot('unknown_knowns_candidates', [])

    def is_rung_visited(self, rung_name: str) -> bool:
        """Check if a rung has been visited."""
        return rung_name in self.visited_rungs

    def is_rung_excluded(self, rung_name: str) -> bool:
        """Check if a rung is excluded."""
        return rung_name in self.excluded_rungs

    def get_frontier(self, all_rungs: Set[str]) -> Set[str]:
        """Get available rungs (not visited, not excluded)."""
        return all_rungs - self.visited_rungs - self.excluded_rungs

    def get_depth(self) -> int:
        """Get current search depth."""
        return len(self.current_path)

    def is_depth_exceeded(self) -> bool:
        """Check if max depth reached."""
        return self.get_depth() >= self.max_depth

    def is_time_critical(self) -> bool:
        """Check if time budget is critical (<20%)."""
        return self.time_budget < 0.2

    def should_commit(self) -> bool:
        """Check if confidence threshold reached."""
        return self.get_confidence() >= self.commit_threshold

    # =========================================================================
    # EDGE COST METHODS (with trust modifiers)
    # =========================================================================

    def get_edge_cost(self, source: str, target: str, base_cost: float = 1.0) -> float:
        """
        Get modified edge cost including trust modifier.

        Higher trust = lower cost (prefer trusted edges).
        """
        key = f"{source}→{target}"
        modifier = self.edge_trust_modifiers.get(key, 1.0)

        # Trust acts as divisor: high trust (>1) reduces cost
        return base_cost / max(modifier, 0.1)

    def get_landmark_heuristic(self, node: str, goal: str, landmarks: Optional[List[str]] = None) -> float:
        """
        Get landmark-based heuristic using triangle inequality.

        h(n,g) = max over all landmarks L of |d(n,L) - d(g,L)|

        This gives O(1) admissible heuristic after O(L*V*logV) precomputation.
        """
        if landmarks is None:
            landmarks = list(self.landmark_distances.keys())

        h = 0.0
        for landmark in landmarks:
            distances = self.landmark_distances.get(landmark, {})
            d_node = distances.get(node, float('inf'))
            d_goal = distances.get(goal, float('inf'))

            if d_node < float('inf') and d_goal < float('inf'):
                h = max(h, abs(d_node - d_goal))

        return h

    # =========================================================================
    # CRYSTALLIZED PATH METHODS
    # =========================================================================

    def has_crystallized_path(self, domain: str) -> bool:
        """Check if there's a crystallized path for this domain."""
        return domain in self.crystallized_paths and len(self.crystallized_paths[domain]) > 0

    def get_crystallized_path(self, domain: str) -> Optional[List[str]]:
        """Get crystallized path for domain if exists."""
        return self.crystallized_paths.get(domain)

    def get_next_crystallized_rung(self, domain: str) -> Optional[str]:
        """Get next unvisited rung from crystallized path."""
        path = self.crystallized_paths.get(domain)
        if not path:
            return None

        for rung in path:
            if rung not in self.visited_rungs:
                return rung

        return None  # All rungs in path visited

    # =========================================================================
    # MUTATION REQUEST METHODS (algorithms call these)
    # =========================================================================

    def request_checkpoint(self, reason: str = "") -> None:
        """Request router to create a checkpoint after this iteration."""
        self._pending_mutations.append(MutationRequest.checkpoint(reason))
        logger.debug(f"[SEARCH-CONTEXT] Checkpoint requested: {reason}")

    def request_backtrack(self, checkpoint_id: int, reason: str = "") -> None:
        """Request router to restore to a checkpoint."""
        self._pending_mutations.append(MutationRequest.backtrack(checkpoint_id, reason))
        logger.debug(f"[SEARCH-CONTEXT] Backtrack requested: checkpoint {checkpoint_id}")

    def request_exclude(self, rungs: Set[str], reason: str = "") -> None:
        """Request router to exclude rungs from future search."""
        self._pending_mutations.append(MutationRequest.exclude_rungs(rungs, reason))
        logger.debug(f"[SEARCH-CONTEXT] Exclusion requested: {rungs}")

    def request_contradiction(self, source_rung: str, target_rung: str, details: Dict[str, Any]) -> None:
        """Record a contradiction for analysis."""
        self._pending_mutations.append(
            MutationRequest.record_contradiction(source_rung, target_rung, details)
        )
        logger.debug(f"[SEARCH-CONTEXT] Contradiction recorded: {source_rung} -> {target_rung}")

    def get_pending_mutations(self) -> List[MutationRequest]:
        """Get and clear pending mutation requests."""
        mutations = sorted(self._pending_mutations, key=lambda m: -m.priority)
        self._pending_mutations = []
        return mutations

    def has_pending_mutations(self) -> bool:
        """Check if there are pending mutations."""
        return len(self._pending_mutations) > 0

    # =========================================================================
    # STATE UPDATE METHODS (called by router, not algorithms)
    # =========================================================================

    def mark_visited(self, rung_name: str) -> None:
        """Mark a rung as visited (called by router)."""
        self.visited_rungs.add(rung_name)
        self.current_path.append(rung_name)
        self.rungs_evaluated += 1

    def update_quadrant(self, quadrant: str) -> None:
        """Update current epistemic quadrant (called by router)."""
        self.current_quadrant = quadrant

    def update_phase(self, phase: SearchPhase) -> None:
        """Update search phase (called by router)."""
        self.phase = phase

    def add_exclusions(self, rungs: Set[str]) -> None:
        """Add rungs to exclusion set (called by router)."""
        self.excluded_rungs.update(rungs)

    def update_time_budget(self, remaining: float) -> None:
        """Update remaining time budget (called by router)."""
        self.time_budget = max(0.0, min(1.0, remaining))

    def record_backtrack(self) -> None:
        """Record a backtrack event (called by router)."""
        self.backtrack_count += 1

    def record_checkpoint(self) -> None:
        """Record a checkpoint event (called by router)."""
        self.checkpoint_count += 1

    # =========================================================================
    # SERIALIZATION
    # =========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """Serialize context to dictionary for debugging."""
        return {
            'current_quadrant': self.current_quadrant,
            'phase': self.phase.value,
            'visited_rungs': list(self.visited_rungs),
            'current_path': self.current_path,
            'excluded_rungs': list(self.excluded_rungs),
            'depth': self.get_depth(),
            'confidence': self.get_confidence(),
            'time_budget': self.time_budget,
            'rungs_evaluated': self.rungs_evaluated,
            'backtrack_count': self.backtrack_count,
            'checkpoint_count': self.checkpoint_count,
            'has_crystallized_paths': bool(self.crystallized_paths),
            'has_topo_order': bool(self.topological_order),
        }

    def get_summary(self) -> str:
        """Get a one-line summary of context state."""
        return (
            f"[{self.current_quadrant}] depth={self.get_depth()} "
            f"conf={self.get_confidence():.2f} "
            f"visited={len(self.visited_rungs)} "
            f"excluded={len(self.excluded_rungs)} "
            f"time={self.time_budget:.1%}"
        )

    # =========================================================================
    # COPY / SNAPSHOT
    # =========================================================================

    def snapshot(self) -> 'SearchContext':
        """Create a deep copy of the context for checkpointing."""
        return SearchContext(
            blackboard_snapshot=copy.deepcopy(self.blackboard_snapshot),
            visited_rungs=self.visited_rungs.copy(),
            current_path=self.current_path.copy(),
            current_quadrant=self.current_quadrant,
            phase=self.phase,
            landmark_distances=self.landmark_distances,  # Shared, immutable
            cluster_assignments=self.cluster_assignments,  # Shared, immutable
            topological_order=self.topological_order,  # Shared, immutable
            abstract_graph=self.abstract_graph,  # Shared, immutable
            edge_trust_modifiers=self.edge_trust_modifiers,  # Shared, immutable
            crystallized_paths=self.crystallized_paths,  # Shared, immutable
            excluded_rungs=self.excluded_rungs.copy(),
            max_depth=self.max_depth,
            time_budget=self.time_budget,
            commit_threshold=self.commit_threshold,
            rungs_evaluated=self.rungs_evaluated,
            backtrack_count=self.backtrack_count,
            checkpoint_count=self.checkpoint_count,
        )


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_search_context(
    blackboard: Any,  # Blackboard instance or dict
    precomputed: Optional[Any] = None,  # PrecomputedData or dict
    edge_trust: Optional[Dict[str, float]] = None,
    crystallized: Optional[Dict[str, List[str]]] = None,
    current_quadrant: Optional[str] = None,
) -> SearchContext:
    """
    Factory function to create a SearchContext from a Blackboard.

    Args:
        blackboard: The Blackboard instance or dict to snapshot
        precomputed: Precomputed data from PrecomputationManager or dict
        edge_trust: Edge trust modifiers from graph evolution
        crystallized: Crystallized paths by domain
        current_quadrant: Override for current quadrant (optional)

    Returns:
        A new SearchContext initialized from the blackboard
    """
    # Extract relevant slots from blackboard
    snapshot = {}
    if isinstance(blackboard, dict):
        snapshot = blackboard
    elif hasattr(blackboard, '_slots'):
        for name, slot in blackboard._slots.items():
            if hasattr(slot, 'value'):
                snapshot[name] = slot.value
            else:
                snapshot[name] = slot
    elif hasattr(blackboard, 'to_context'):
        snapshot = blackboard.to_context()

    # Determine quadrant
    quadrant = current_quadrant or snapshot.get('primary_quadrant', 'UU')

    # Create context
    ctx = SearchContext(
        blackboard_snapshot=snapshot,
        visited_rungs=set(snapshot.get('visited_rungs', [])),
        current_quadrant=quadrant,
    )

    # Inject precomputed data
    if precomputed:
        # Handle both PrecomputedData objects and dicts
        if hasattr(precomputed, 'landmark_distances'):
            ctx.landmark_distances = precomputed.landmark_distances
            ctx.cluster_assignments = precomputed.rung_to_cluster
            ctx.topological_order = precomputed.topological_order or []
            ctx.abstract_graph = precomputed.abstract_edges
        elif isinstance(precomputed, dict):
            ctx.landmark_distances = precomputed.get('landmark_distances', {})
            ctx.cluster_assignments = precomputed.get('cluster_assignments', {})
            ctx.topological_order = precomputed.get('topological_order', [])
            ctx.abstract_graph = precomputed.get('abstract_graph', {})

    # Inject graph evolution data
    if edge_trust:
        ctx.edge_trust_modifiers = edge_trust
    if crystallized:
        ctx.crystallized_paths = crystallized

    return ctx
