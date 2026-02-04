"""
Precomputation Manager - Offline Preprocessing for O(1) Query

Phase 3.5 Implementation - Cognitive Routing

This module precomputes expensive data structures at startup:
- Landmark distances for O(1) A* heuristics
- Topological order for O(V+E) causal search
- Category clusters for hierarchical search
- Reverse edges for bidirectional search

Key insight from Part 2: Precomputation turns O(V log V) per-query heuristics
into O(L) = O(5) = O(1) lookups.
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

import heapq
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

# Hub rungs that many paths go through - used as landmarks
DEFAULT_LANDMARKS: List[str] = [
    "survey",
    "control_tracker",
    "hypothesis_testing",
    "network_wisdom",
    "smart_action_selection",
]

# Rung categories for hierarchical search
CATEGORY_ORDER: List[str] = [
    "emergency",
    "orientation",
    "filter",
    "hypothesis",
    "exploitation",
    "metacognition",
]


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class PrecomputedData:
    """
    All precomputed data for efficient search.

    Injected into SearchContext for algorithm use.
    """
    # Landmark distances: landmark -> {rung: distance}
    landmark_distances: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # Topological order (if DAG)
    topological_order: Optional[List[str]] = None

    # Is the graph a DAG?
    is_dag: bool = False

    # Category clusters: category -> list of rungs
    cluster_assignments: Dict[str, List[str]] = field(default_factory=dict)

    # Reverse cluster lookup: rung -> category
    rung_to_cluster: Dict[str, str] = field(default_factory=dict)

    # Reverse edges: target -> list of sources
    reverse_edges: Dict[str, List[str]] = field(default_factory=dict)

    # Category-level abstract graph
    abstract_edges: Dict[str, List[str]] = field(default_factory=dict)

    # Dependencies: rung -> list of rungs that must run first
    dependencies: Dict[str, List[str]] = field(default_factory=dict)

    # Computation stats
    computation_time_ms: float = 0.0
    landmark_count: int = 0
    node_count: int = 0
    edge_count: int = 0


@dataclass
class GraphInfo:
    """
    Graph structure info for algorithms.

    Combines precomputed data with runtime graph state.
    """
    nodes: Dict[str, Dict[str, Any]]  # rung_name -> {category, priority, etc}
    edges: Dict[str, List[str]]  # source -> [targets]
    reverse_edges: Dict[str, List[str]]  # target -> [sources]
    dependencies: Dict[str, List[str]]
    is_dag: bool
    visit_counts: Dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_precomputed(
        cls,
        precomputed: PrecomputedData,
        nodes: Dict[str, Dict[str, Any]],
        edges: Dict[str, List[str]]
    ) -> 'GraphInfo':
        """Create GraphInfo from precomputed data."""
        return cls(
            nodes=nodes,
            edges=edges,
            reverse_edges=precomputed.reverse_edges,
            dependencies=precomputed.dependencies,
            is_dag=precomputed.is_dag,
        )


# =============================================================================
# PRECOMPUTATION MANAGER
# =============================================================================

class PrecomputationManager:
    """
    Manages offline preprocessing of graph structures.

    Computes expensive data structures once at startup:
    1. Landmark distances - O(L × (V + E log V)) preprocessing
    2. Topological order - O(V + E)
    3. Category clusters - O(V)
    4. Reverse edges - O(E)
    """

    def __init__(
        self,
        landmarks: Optional[List[str]] = None,
        categories: Optional[List[str]] = None
    ):
        self._landmarks = landmarks or DEFAULT_LANDMARKS
        self._categories = categories or CATEGORY_ORDER
        self._cached_data: Optional[PrecomputedData] = None

    def precompute(
        self,
        nodes: Dict[str, Dict[str, Any]],
        edges: Dict[str, List[str]],
        edge_costs: Optional[Dict[Tuple[str, str], float]] = None
    ) -> PrecomputedData:
        """
        Perform all precomputation.

        Args:
            nodes: Dict of rung_name -> {category, default_priority, ...}
            edges: Dict of source -> [target1, target2, ...]
            edge_costs: Optional dict of (source, target) -> cost

        Returns:
            PrecomputedData with all precomputed structures
        """
        start_time = time.perf_counter()

        data = PrecomputedData()
        data.node_count = len(nodes)
        data.edge_count = sum(len(targets) for targets in edges.values())

        # 1. Reverse edges - O(E)
        logger.info("[PRECOMPUTE] Building reverse edges...")
        data.reverse_edges = self._build_reverse_edges(edges)

        # 2. Dependencies - O(E)
        logger.info("[PRECOMPUTE] Extracting dependencies...")
        data.dependencies = self._extract_dependencies(nodes, edges)

        # 3. Cluster assignments - O(V)
        logger.info("[PRECOMPUTE] Building clusters...")
        data.cluster_assignments, data.rung_to_cluster = self._build_clusters(nodes)

        # 4. Abstract graph - O(C²) where C ≈ 6
        logger.info("[PRECOMPUTE] Building abstract graph...")
        data.abstract_edges = self._build_abstract_graph()

        # 5. Check for DAG and compute topological order - O(V + E)
        logger.info("[PRECOMPUTE] Computing topological order...")
        data.is_dag, data.topological_order = self._compute_topological_order(nodes, edges)

        # 6. Landmark distances - O(L × (V + E log V))
        logger.info(f"[PRECOMPUTE] Computing landmark distances for {len(self._landmarks)} landmarks...")
        data.landmark_distances = self._compute_landmark_distances(
            nodes, edges, edge_costs or {}
        )
        data.landmark_count = len(data.landmark_distances)

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        data.computation_time_ms = elapsed_ms

        logger.info(
            f"[PRECOMPUTE] Complete in {elapsed_ms:.1f}ms: "
            f"{data.node_count} nodes, {data.edge_count} edges, "
            f"{data.landmark_count} landmarks, DAG={data.is_dag}"
        )

        self._cached_data = data
        return data

    @property
    def cached_data(self) -> Optional[PrecomputedData]:
        """Get cached precomputed data."""
        return self._cached_data

    def invalidate(self):
        """Invalidate cached data (e.g., when graph changes)."""
        self._cached_data = None

    # =========================================================================
    # REVERSE EDGES
    # =========================================================================

    def _build_reverse_edges(
        self,
        edges: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        """Build reverse edge mapping: target -> [sources]."""
        reverse: Dict[str, List[str]] = defaultdict(list)
        for source, targets in edges.items():
            for target in targets:
                reverse[target].append(source)
        return dict(reverse)

    # =========================================================================
    # DEPENDENCIES
    # =========================================================================

    def _extract_dependencies(
        self,
        nodes: Dict[str, Dict[str, Any]],
        edges: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        """
        Extract dependencies from node metadata and edge structure.

        Dependencies are rungs that MUST run before a rung can execute.
        """
        dependencies: Dict[str, List[str]] = defaultdict(list)

        # From node metadata
        for rung_name, metadata in nodes.items():
            if 'required_inputs' in metadata:
                # Map required slots to provider rungs
                for slot in metadata['required_inputs']:
                    providers = self._find_slot_providers(slot, nodes)
                    dependencies[rung_name].extend(providers)

            if 'depends_on' in metadata:
                dependencies[rung_name].extend(metadata['depends_on'])

        # Ensure unique dependencies
        return {k: list(set(v)) for k, v in dependencies.items()}

    def _find_slot_providers(
        self,
        slot: str,
        nodes: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Find rungs that provide (write to) a slot."""
        providers = []
        for rung_name, metadata in nodes.items():
            outputs = metadata.get('output_slots', [])
            if slot in outputs:
                providers.append(rung_name)
        return providers

    # =========================================================================
    # CLUSTERS
    # =========================================================================

    def _build_clusters(
        self,
        nodes: Dict[str, Dict[str, Any]]
    ) -> Tuple[Dict[str, List[str]], Dict[str, str]]:
        """
        Build category clusters.

        Returns:
            (category -> [rungs], rung -> category)
        """
        clusters: Dict[str, List[str]] = {cat: [] for cat in self._categories}
        rung_to_cluster: Dict[str, str] = {}

        for rung_name, metadata in nodes.items():
            category = metadata.get('category', 'unknown')

            # Map to known category or default
            if category in clusters:
                clusters[category].append(rung_name)
                rung_to_cluster[rung_name] = category
            else:
                # Default to 'hypothesis' for unknown categories
                clusters.setdefault('hypothesis', []).append(rung_name)
                rung_to_cluster[rung_name] = 'hypothesis'

        return clusters, rung_to_cluster

    # =========================================================================
    # ABSTRACT GRAPH
    # =========================================================================

    def _build_abstract_graph(self) -> Dict[str, List[str]]:
        """
        Build category-level abstract graph.

        Captures typical flow between categories.
        """
        abstract: Dict[str, List[str]] = {cat: [] for cat in self._categories}

        # Sequential flow
        for i, cat in enumerate(self._categories[:-1]):
            next_cat = self._categories[i + 1]
            abstract[cat].append(next_cat)

        # Skip edges (common shortcuts)
        # orientation -> exploitation (skip hypothesis when confident)
        if 'orientation' in abstract and 'exploitation' in self._categories:
            abstract['orientation'].append('exploitation')

        # filter -> exploitation (skip hypothesis when filtered)
        if 'filter' in abstract and 'exploitation' in self._categories:
            abstract['filter'].append('exploitation')

        # hypothesis -> hypothesis (self-refinement)
        if 'hypothesis' in abstract:
            abstract['hypothesis'].append('hypothesis')

        # metacognition can go anywhere
        if 'metacognition' in abstract:
            for cat in self._categories:
                if cat != 'metacognition':
                    abstract['metacognition'].append(cat)

        return abstract

    # =========================================================================
    # TOPOLOGICAL ORDER
    # =========================================================================

    def _compute_topological_order(
        self,
        nodes: Dict[str, Dict[str, Any]],
        edges: Dict[str, List[str]]
    ) -> Tuple[bool, Optional[List[str]]]:
        """
        Compute topological order if graph is DAG.

        Uses Kahn's algorithm - O(V + E).

        Returns:
            (is_dag, topological_order or None)
        """
        # Compute in-degrees
        in_degree: Dict[str, int] = {name: 0 for name in nodes}
        for source, targets in edges.items():
            for target in targets:
                if target in in_degree:
                    in_degree[target] += 1

        # Start with zero in-degree nodes
        queue = deque([n for n, d in in_degree.items() if d == 0])
        result: List[str] = []

        while queue:
            node = queue.popleft()
            result.append(node)

            for target in edges.get(node, []):
                if target in in_degree:
                    in_degree[target] -= 1
                    if in_degree[target] == 0:
                        queue.append(target)

        # If all nodes processed, it's a DAG
        is_dag = len(result) == len(nodes)

        return is_dag, result if is_dag else None

    # =========================================================================
    # LANDMARK DISTANCES
    # =========================================================================

    def _compute_landmark_distances(
        self,
        nodes: Dict[str, Dict[str, Any]],
        edges: Dict[str, List[str]],
        edge_costs: Dict[Tuple[str, str], float]
    ) -> Dict[str, Dict[str, float]]:
        """
        Compute distances from each landmark to all nodes.

        Uses Dijkstra from each landmark - O(L × (V + E log V)).
        """
        landmark_distances: Dict[str, Dict[str, float]] = {}

        for landmark in self._landmarks:
            if landmark not in nodes:
                logger.warning(f"[PRECOMPUTE] Landmark '{landmark}' not in graph, skipping")
                continue

            distances = self._dijkstra(landmark, nodes, edges, edge_costs)
            landmark_distances[landmark] = distances

            reachable = sum(1 for d in distances.values() if d < float('inf'))
            logger.debug(f"[PRECOMPUTE] Landmark '{landmark}': {reachable}/{len(nodes)} reachable")

        return landmark_distances

    def _dijkstra(
        self,
        source: str,
        nodes: Dict[str, Dict[str, Any]],
        edges: Dict[str, List[str]],
        edge_costs: Dict[Tuple[str, str], float]
    ) -> Dict[str, float]:
        """
        Dijkstra's algorithm from source.

        Returns distances to all reachable nodes.
        """
        distances: Dict[str, float] = {name: float('inf') for name in nodes}
        distances[source] = 0.0

        # Priority queue: (distance, node)
        pq: List[Tuple[float, str]] = [(0.0, source)]
        visited: Set[str] = set()

        while pq:
            dist, node = heapq.heappop(pq)

            if node in visited:
                continue
            visited.add(node)

            if dist > distances[node]:
                continue

            for target in edges.get(node, []):
                # Get edge cost (default 1.0)
                cost = edge_costs.get((node, target), 1.0)
                new_dist = dist + cost

                if new_dist < distances.get(target, float('inf')):
                    distances[target] = new_dist
                    heapq.heappush(pq, (new_dist, target))

        return distances

    # =========================================================================
    # HEURISTIC COMPUTATION
    # =========================================================================

    def get_landmark_heuristic(
        self,
        node: str,
        goal: str,
        data: Optional[PrecomputedData] = None
    ) -> float:
        """
        Compute landmark heuristic for A*.

        Uses triangle inequality: h(n,g) >= |d(n,L) - d(g,L)| for any landmark L.
        Take max over all landmarks for tightest bound.

        Complexity: O(L) = O(5) = O(1)
        """
        precomputed = data or self._cached_data
        if not precomputed or not precomputed.landmark_distances:
            return 0.0

        h = 0.0
        for landmark, distances in precomputed.landmark_distances.items():
            d_node = distances.get(node, float('inf'))
            d_goal = distances.get(goal, float('inf'))

            if d_node < float('inf') and d_goal < float('inf'):
                h = max(h, abs(d_node - d_goal))

        return h


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_precomputation_manager(
    landmarks: Optional[List[str]] = None,
    categories: Optional[List[str]] = None
) -> PrecomputationManager:
    """Create a new PrecomputationManager."""
    return PrecomputationManager(landmarks=landmarks, categories=categories)


def precompute_from_rungs(
    rungs: List[Any],
    manager: Optional[PrecomputationManager] = None
) -> PrecomputedData:
    """
    Convenience function to precompute from a list of DecisionRung objects.

    Args:
        rungs: List of DecisionRung objects with name, category, etc.
        manager: Optional existing manager

    Returns:
        PrecomputedData
    """
    manager = manager or PrecomputationManager()

    # Build nodes dict
    nodes: Dict[str, Dict[str, Any]] = {}
    for rung in rungs:
        nodes[rung.name] = {
            'category': getattr(rung, 'category', 'unknown'),
            'default_priority': getattr(rung, 'default_priority', 50),
            'required_inputs': getattr(rung, 'required_inputs', []),
            'output_slots': getattr(rung, 'output_slots', []),
        }

    # Build edges from triggers
    edges: Dict[str, List[str]] = defaultdict(list)
    for rung in rungs:
        # Explicit triggers
        for trigger in getattr(rung, 'output_triggers', []):
            if isinstance(trigger, dict):
                target = trigger.get('target')
            else:
                target = trigger
            if target:
                edges[rung.name].append(target)

        # Implicit edges from category adjacency
        # (handled by EdgeInferenceEngine, not here)

    return manager.precompute(nodes, dict(edges))


# =============================================================================
# INCREMENTAL UPDATE (FUTURE)
# =============================================================================

class IncrementalUpdater:
    """
    Incrementally update precomputed data when graph changes.

    More efficient than full recomputation for small changes.
    """

    def __init__(self, manager: PrecomputationManager):
        self._manager = manager

    def add_edge(
        self,
        source: str,
        target: str,
        cost: float = 1.0
    ) -> bool:
        """
        Add an edge and update affected data.

        Returns True if update successful, False if full recompute needed.
        """
        data = self._manager.cached_data
        if not data:
            return False

        # Update reverse edges
        if target not in data.reverse_edges:
            data.reverse_edges[target] = []
        if source not in data.reverse_edges[target]:
            data.reverse_edges[target].append(source)

        # Check if this breaks DAG property
        if data.is_dag and self._creates_cycle(source, target, data):
            data.is_dag = False
            data.topological_order = None

        # Landmark distances may need update
        # For now, mark as needing full recompute for landmarks
        # TODO: Implement incremental Dijkstra updates

        return True

    def remove_edge(
        self,
        source: str,
        target: str
    ) -> bool:
        """
        Remove an edge and update affected data.

        Returns True if update successful, False if full recompute needed.
        """
        data = self._manager.cached_data
        if not data:
            return False

        # Update reverse edges
        if target in data.reverse_edges:
            if source in data.reverse_edges[target]:
                data.reverse_edges[target].remove(source)

        # Removing edges can't create cycles, but may change distances
        # For now, require full recompute for landmarks
        return True

    def _creates_cycle(
        self,
        source: str,
        target: str,
        data: PrecomputedData
    ) -> bool:
        """Check if adding edge source->target creates a cycle."""
        # DFS from target to see if we can reach source
        visited: Set[str] = set()
        stack = [target]

        while stack:
            node = stack.pop()
            if node == source:
                return True
            if node in visited:
                continue
            visited.add(node)

            # Follow forward edges from this node
            # (Would need edges dict, using reverse for now)
            for pred in data.reverse_edges.get(node, []):
                # This is backwards - need actual edges
                pass

        return False
