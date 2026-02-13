"""
Search Algorithms - Domain-Specific Algorithm Portfolio

Phase 3.2 Implementation - Cognitive Routing

This module provides a portfolio of search algorithms optimized for different domains:

| Domain        | Algorithm              | Complexity    | Best For                    |
|---------------|------------------------|---------------|------------------------------|
| Physics       | TopologicalDPSearch    | O(V + E)      | Causal chains, DAGs          |
| Symbolic      | BidirectionalSearch    | O(b^(d/2))    | Known goal state (key→lock)  |
| Spatial       | HierarchicalAStar      | O(C² + V_c²)  | Region clusters              |
| Exploitation  | GreedyBestFirst        | O(V)          | High confidence (>0.8)       |
| Exploration   | InformationMaximizing  | O(iter × d)   | Low confidence (<0.3)        |
| Time Pressure | BeamSearch             | O(k × b × d)  | Budget < 20%                 |
| Contradiction | BacktrackingAStar      | O(E × bt)     | After conflict detected      |
| General       | LandmarkAStar          | O(E), O(1) h  | Default fallback             |

Key insight from Part 3: Transition-Driven Complexity Win
- Static A* on 63 rungs: O(63 × 25) = O(1575)
- Transition-Driven: O(12-26) typical = 60x improvement
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

import logging
import math
import random
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from engines.cognition.search_context import SearchContext

logger = logging.getLogger(__name__)


# =============================================================================
# BASE CLASS
# =============================================================================

class SearchAlgorithm(ABC):
    """
    Base class for all search algorithms.

    Algorithms are STATELESS - all state comes through SearchContext.
    This enables:
    - Easy testing with mock contexts
    - Serializable state for debugging
    - Router control over state mutations
    """

    name: str = "base_algorithm"
    description: str = "Base search algorithm"

    # Complexity info for logging
    time_complexity: str = "O(?)"
    space_complexity: str = "O(?)"

    # Applicability
    requires_dag: bool = False  # Only works on DAGs
    requires_goal: bool = False  # Needs explicit goal state

    def __init__(self, **kwargs):
        """Accept extra kwargs for compatibility with get_algorithm()."""
        pass

    @abstractmethod
    def get_next_rungs(
        self,
        frontier: Set[str],
        context: SearchContext,
        graph_info: Dict[str, Any]
    ) -> List[str]:
        """
        Get the next rung(s) to execute.

        Args:
            frontier: Available rungs (not visited, not excluded)
            context: Search context with all state
            graph_info: Graph structure info (edges, nodes, etc.)

        Returns:
            Ordered list of rungs to try (first = highest priority)
        """
        pass

    def is_applicable(self, context: SearchContext, graph_info: Dict[str, Any]) -> bool:
        """Check if this algorithm is applicable to current situation."""
        if self.requires_dag and not graph_info.get('is_dag', False):
            return False
        if self.requires_goal and not context.get_slot('goal_rungs'):
            return False
        return True

    def estimate_cost(self, context: SearchContext, graph_info: Dict[str, Any]) -> float:
        """Estimate computational cost for this algorithm."""
        return 1.0  # Default: neutral cost

    def _score_rung(self, rung: str, context: SearchContext, graph_info: Dict[str, Any]) -> float:
        """
        Score a rung based on expected value.

        Default implementation uses confidence + category bonus.
        Subclasses can override for domain-specific scoring.
        """
        # Base score from rung metadata
        rung_info = graph_info.get('nodes', {}).get(rung, {})
        priority = rung_info.get('priority', rung_info.get('default_priority', 50))

        # Lower priority number = higher score (survey=5 should score higher)
        base_score = 1.0 - (priority / 100.0)

        # Boost for category alignment
        current_quadrant = context.current_quadrant
        category = rung_info.get('category', 'unknown')

        category_alignment = {
            'KK': {'exploitation': 0.3, 'filter': 0.1},
            'KU': {'hypothesis': 0.3, 'orientation': 0.1},
            'UK': {'hypothesis': 0.2, 'exploitation': 0.1},
            'UU': {'orientation': 0.3, 'hypothesis': 0.1},
        }
        bonus = category_alignment.get(current_quadrant, {}).get(category, 0.0)

        return base_score + bonus


# =============================================================================
# TOPOLOGICAL DP SEARCH
# =============================================================================

class TopologicalDPSearch(SearchAlgorithm):
    """
    For DAG-structured problems (physics, causal chains).

    Uses precomputed topological order for O(V + E) complexity.
    Only applicable when graph has no cycles.
    """

    name = "topological_dp"
    description = "Dynamic programming on topological order"
    time_complexity = "O(V + E)"
    space_complexity = "O(V)"
    requires_dag = True

    def get_next_rungs(
        self,
        frontier: Set[str],
        context: SearchContext,
        graph_info: Dict[str, Any]
    ) -> List[str]:
        # Use precomputed topological order
        topo_order = context.topological_order

        if not topo_order:
            logger.warning("[TOPO-DP] No topological order available")
            return list(frontier)[:1] if frontier else []

        # Return first unvisited rung in topological order
        for rung in topo_order:
            if rung in frontier:
                # Check dependencies satisfied
                deps = graph_info.get('dependencies', {}).get(rung, [])
                if all(d in context.visited_rungs for d in deps):
                    return [rung]

        # Fallback: any frontier rung
        return list(frontier)[:1] if frontier else []

    def is_applicable(self, context: SearchContext, graph_info: Dict[str, Any]) -> bool:
        return bool(context.topological_order)


# =============================================================================
# BIDIRECTIONAL SEARCH
# =============================================================================

class BidirectionalSearch(SearchAlgorithm):
    """
    Search from start AND goal simultaneously - O(b^(d/2)) instead of O(b^d).

    For symbolic puzzles where goal is known (key→lock).
    Requires explicit goal rungs to be specified.
    """

    name = "bidirectional"
    description = "Meet-in-the-middle search"
    time_complexity = "O(b^(d/2))"
    space_complexity = "O(b^(d/2))"
    requires_goal = True

    def get_next_rungs(
        self,
        frontier: Set[str],
        context: SearchContext,
        graph_info: Dict[str, Any]
    ) -> List[str]:
        goal_rungs = context.get_slot('goal_rungs') or ['smart_action_selection']
        goal_set = set(goal_rungs) if isinstance(goal_rungs, list) else {goal_rungs}

        # Forward frontier: expand from visited rungs
        forward_candidates = frontier

        # Backward frontier: what can reach goal?
        reverse_edges = graph_info.get('reverse_edges', {})
        backward_candidates = set()
        for goal in goal_set:
            if goal in reverse_edges:
                backward_candidates.update(reverse_edges[goal])

        # Find meeting point (intersection)
        meeting = forward_candidates & backward_candidates
        if meeting:
            # Score by proximity to goal
            best = min(meeting, key=lambda r: self._distance_to_goal(r, goal_set, graph_info))
            return [best]

        # No meeting yet - prefer forward rungs that get closer to goal
        if forward_candidates:
            scored = [
                (self._distance_to_goal(r, goal_set, graph_info), r)
                for r in forward_candidates
            ]
            scored.sort()
            return [scored[0][1]]

        return []

    def _distance_to_goal(
        self,
        rung: str,
        goals: Set[str],
        graph_info: Dict[str, Any]
    ) -> float:
        """Estimate distance to nearest goal using landmark heuristic."""
        edges = graph_info.get('edges', {})

        # Simple BFS distance estimate
        if rung in goals:
            return 0.0

        # Check if direct edge to goal
        for goal in goals:
            if goal in edges.get(rung, []):
                return 1.0

        # Default estimate based on priority difference
        rung_info = graph_info.get('nodes', {}).get(rung, {})
        rung_priority = rung_info.get('priority', rung_info.get('default_priority', 50))
        goal_priority = 60  # Assume goals are exploitation phase

        return abs(goal_priority - rung_priority) / 10.0


# =============================================================================
# LANDMARK A* SEARCH
# =============================================================================

class LandmarkAStar(SearchAlgorithm):
    """
    A* with precomputed landmark distances for O(1) heuristic.

    Uses triangle inequality: h(n,g) = max_L |d(n,L) - d(g,L)|

    This is the general-purpose algorithm when no domain-specific
    algorithm is applicable.
    """

    name = "landmark_astar"
    description = "A* with landmark heuristics"
    time_complexity = "O(E log V)"
    space_complexity = "O(V)"

    # Default landmarks (can be overridden)
    DEFAULT_LANDMARKS = [
        "survey",
        "control_tracker",
        "network_wisdom",
        "hypothesis_testing",
        "smart_action_selection"
    ]

    def get_next_rungs(
        self,
        frontier: Set[str],
        context: SearchContext,
        graph_info: Dict[str, Any]
    ) -> List[str]:
        if not frontier:
            return []

        # Goal: high confidence decision
        goal = context.get_slot('goal_rungs') or 'smart_action_selection'
        if isinstance(goal, list):
            goal = goal[0]

        # Score each frontier rung with f(n) = g(n) + h(n)
        g = context.get_depth()  # Cost so far

        scored = []
        for rung in frontier:
            # Heuristic from landmarks
            h = context.get_landmark_heuristic(rung, goal, self.DEFAULT_LANDMARKS)

            # Edge cost modifier
            if context.current_path:
                last_rung = context.current_path[-1]
                edge_cost = context.get_edge_cost(last_rung, rung)
            else:
                edge_cost = 1.0

            f = g + edge_cost + h
            scored.append((f, rung))

        scored.sort()
        return [scored[0][1]]

    def is_applicable(self, context: SearchContext, graph_info: Dict[str, Any]) -> bool:
        # Always applicable as general fallback
        return True


# =============================================================================
# GREEDY BEST-FIRST SEARCH
# =============================================================================

class GreedyBestFirst(SearchAlgorithm):
    """
    Simple greedy - pick highest expected confidence.

    O(V) complexity. Best for exploitation when confidence is high.
    No backtracking - commits to locally best choice.
    """

    name = "greedy_best_first"
    description = "Greedy selection by expected confidence"
    time_complexity = "O(V)"
    space_complexity = "O(1)"

    def get_next_rungs(
        self,
        frontier: Set[str],
        context: SearchContext,
        graph_info: Dict[str, Any]
    ) -> List[str]:
        if not frontier:
            return []

        # Score by expected confidence contribution
        scored = []
        for rung in frontier:
            score = self._expected_confidence(rung, context, graph_info)
            scored.append((score, rung))

        scored.sort(reverse=True)  # Highest first
        # Return top-K candidates for batch evaluation and agreement
        # checking. The router evaluates this batch in one pass and
        # looks for action agreement between rungs. Returning only 1
        # rung forces the router into a brute-force O(V) linear scan
        # of all rungs across iterations, defeating focused search.
        max_k = graph_info.get('max_rungs_per_call', 5)
        return [r for _, r in scored[:max_k]]

    def _expected_confidence(
        self,
        rung: str,
        context: SearchContext,
        graph_info: Dict[str, Any]
    ) -> float:
        """Estimate confidence gain from executing this rung.

        Prioritizes rungs proven to produce high-confidence results
        (tracked as known_knowns by the epistemic tracker). Without
        this, KK decisions waste 35+ iterations scoring all rungs at
        ~0.3 default instead of jumping to the proven rung first.
        """
        # Priority 1: If this rung is a proven known_known source,
        # score it above all unknown rungs so KK exploits immediately
        known_rungs = graph_info.get('known_rungs', {})
        if rung in known_rungs:
            return known_rungs[rung] + 1.0  # e.g. 0.6 + 1.0 = 1.6

        rung_info = graph_info.get('nodes', {}).get(rung, {})

        # Base confidence from rung's historical performance
        base_conf = rung_info.get('avg_confidence', 0.3)

        # Boost for exploitation rungs when already confident
        current_conf = context.get_confidence()
        category = rung_info.get('category', 'unknown')

        if category == 'exploitation' and current_conf > 0.6:
            base_conf *= 1.3

        return base_conf


# =============================================================================
# BEAM SEARCH
# =============================================================================

class BeamSearch(SearchAlgorithm):
    """
    Keep only top-k paths - O(k·b·d). Guaranteed time bound.

    Best for time pressure situations where we need a decision fast.
    """

    name = "beam_search"
    description = "Bounded-width search"
    time_complexity = "O(k·b·d)"
    space_complexity = "O(k·d)"

    def __init__(self, beam_width: int = 3, **_kwargs: object):
        self.beam_width = beam_width

    def get_next_rungs(
        self,
        frontier: Set[str],
        context: SearchContext,
        graph_info: Dict[str, Any]
    ) -> List[str]:
        if not frontier:
            return []

        # Score all frontier rungs
        scored = []
        for rung in frontier:
            score = self._score_rung(rung, context, graph_info)
            scored.append((score, rung))

        scored.sort(reverse=True)

        # Return top-k (but typically we only execute first)
        top_k = scored[:self.beam_width]
        return [r for _, r in top_k]


# =============================================================================
# INFORMATION MAXIMIZING SEARCH
# =============================================================================

class InformationMaximizingSearch(SearchAlgorithm):
    """
    Pick rung with highest information gain / cost ratio.

    Like Bayesian Optimization - UCB-style acquisition function.
    Best for exploration when confidence is low (UU quadrant).
    """

    name = "information_maximizing"
    description = "UCB-style information gain optimization"
    time_complexity = "O(V)"
    space_complexity = "O(1)"

    def __init__(self, exploration_bonus: float = 1.0, curiosity_weight: float = 0.2,
                 epsilon: float = 0.05, **_kwargs: object):
        self.exploration_bonus = exploration_bonus
        self.curiosity_weight = curiosity_weight
        self.epsilon = epsilon  # Stochastic tie-breaking noise

    def get_next_rungs(
        self,
        frontier: Set[str],
        context: SearchContext,
        graph_info: Dict[str, Any]
    ) -> List[str]:
        if not frontier:
            return []

        scored = []
        for rung in frontier:
            info_gain = self._expected_info_gain(rung, context, graph_info)
            cost = self._compute_cost(rung, context, graph_info)

            # UCB-style: acquisition = expected gain + exploration bonus
            visit_count = graph_info.get('visit_counts', {}).get(rung, 0)
            exploration = self.exploration_bonus / math.sqrt(1 + visit_count)

            # Add small random noise for stochastic tie-breaking
            # Without this, deterministic scoring produces identical rung
            # orderings every single decision (all 49 rungs, same order)
            noise = random.uniform(0, self.epsilon)

            acquisition = info_gain / (cost + 0.1) + self.curiosity_weight * exploration + noise
            scored.append((acquisition, rung))

        scored.sort(reverse=True)
        max_k = graph_info.get('max_rungs_per_call', 5)
        return [r for _, r in scored[:max_k]]

    def _expected_info_gain(
        self,
        rung: str,
        context: SearchContext,
        graph_info: Dict[str, Any]
    ) -> float:
        """Estimate information gain from executing this rung."""
        rung_info = graph_info.get('nodes', {}).get(rung, {})
        category = rung_info.get('category', 'unknown')

        # Orientation rungs provide most info when we know little
        current_uu = context.get_slot('uu_estimate', 0.5)

        category_info = {
            'orientation': 0.4 * current_uu,
            'hypothesis': 0.3,
            'filter': 0.1,
            'exploitation': 0.2 * (1 - current_uu),
            'metacognition': 0.15,
        }

        return category_info.get(category, 0.2)

    def _compute_cost(
        self,
        rung: str,
        context: SearchContext,
        graph_info: Dict[str, Any]
    ) -> float:
        """Compute expected cost of executing this rung."""
        rung_info = graph_info.get('nodes', {}).get(rung, {})

        # Cost based on priority (higher priority number = lower urgency = higher cost)
        # Node dict stores 'priority' (set from rung.get_priority()), not
        # 'default_priority'. The mismatch caused every rung to score 50/50=1.0,
        # making the algorithm blind to priority differences.
        priority = rung_info.get('priority', rung_info.get('default_priority', 50))
        base_cost = priority / 50.0  # Normalize to ~1.0

        # Edge cost modifier
        if context.current_path:
            last_rung = context.current_path[-1]
            edge_cost = context.get_edge_cost(last_rung, rung)
            base_cost *= edge_cost

        return base_cost


# =============================================================================
# HIERARCHICAL A* SEARCH
# =============================================================================

class HierarchicalAStar(SearchAlgorithm):
    """
    Two-level search: abstract (categories) then detail (rungs within category).

    Reduces O(V²) to O(C² + max(V_c)²) where C=6 categories, V_c≈10 rungs per category.
    Best for spatial problems with clear region structure.
    """

    name = "hierarchical_astar"
    description = "Two-level category-then-rung search"
    time_complexity = "O(C² + V_c²)"
    space_complexity = "O(C + V_c)"

    CATEGORY_ORDER = [
        'orientation',
        'hypothesis',
        'filter',
        'exploitation',
        'metacognition'
    ]

    def get_next_rungs(
        self,
        frontier: Set[str],
        context: SearchContext,
        graph_info: Dict[str, Any]
    ) -> List[str]:
        if not frontier:
            return []

        # Phase 1: Which category? O(C²) where C≈6
        target_category = self._search_abstract(context, graph_info)

        # Phase 2: Which rung within category? O(V_c²) where V_c≈10
        category_rungs = [
            r for r in frontier
            if context.cluster_assignments.get(r) == target_category
        ]

        if not category_rungs:
            # No rungs in target category available - fall back to best available
            return list(frontier)[:1]

        return self._search_within_category(category_rungs, context, graph_info)

    def _search_abstract(self, context: SearchContext, graph_info: Dict[str, Any]) -> str:
        """Determine target category based on epistemic state."""
        quadrant = context.current_quadrant

        # Map quadrant to preferred category
        quadrant_categories = {
            'UU': 'orientation',
            'KU': 'hypothesis',
            'UK': 'hypothesis',
            'KK': 'exploitation',
        }

        return quadrant_categories.get(quadrant, 'hypothesis')

    def _search_within_category(
        self,
        rungs: List[str],
        context: SearchContext,
        graph_info: Dict[str, Any]
    ) -> List[str]:
        """Search within a category using standard scoring."""
        scored = [
            (self._score_rung(r, context, graph_info), r)
            for r in rungs
        ]
        scored.sort(reverse=True)
        return [scored[0][1]]


# =============================================================================
# BACKTRACKING A* SEARCH
# =============================================================================

class BacktrackingAStar(SearchAlgorithm):
    """
    A* with systematic backtracking after contradiction.

    When a contradiction is detected, restores to checkpoint and
    excludes the path that led to the contradiction.
    """

    name = "backtracking_astar"
    description = "A* with systematic undo on contradiction"
    time_complexity = "O(E × backtrack_depth)"
    space_complexity = "O(V)"

    def __init__(self, checkpoint_id: Optional[int] = None, excluded_rungs: Optional[Set[str]] = None, **_kwargs: object):
        self.checkpoint_id = checkpoint_id
        self.excluded_rungs = excluded_rungs or set()

    def get_next_rungs(
        self,
        frontier: Set[str],
        context: SearchContext,
        graph_info: Dict[str, Any]
    ) -> List[str]:
        # First, request backtrack if checkpoint specified
        if self.checkpoint_id is not None:
            context.request_backtrack(self.checkpoint_id, "Contradiction recovery")
            context.request_exclude(self.excluded_rungs, "Contradiction path")

        # Filter frontier
        available = frontier - self.excluded_rungs - context.excluded_rungs

        if not available:
            logger.warning("[BACKTRACK-A*] No available rungs after exclusions")
            return []

        # Use landmark A* on filtered frontier
        goal = context.get_slot('goal_rungs') or 'smart_action_selection'
        if isinstance(goal, list):
            goal = goal[0]

        scored = []
        g = context.get_depth()

        for rung in available:
            h = context.get_landmark_heuristic(rung, goal)
            f = g + 1 + h
            scored.append((f, rung))

        scored.sort()
        return [scored[0][1]]


# =============================================================================
# TARGETED QUESTION SEARCH (KU Quadrant)
# =============================================================================

class TargetedQuestionSearch(SearchAlgorithm):
    """
    KU quadrant: We know what we don't know - search toward answerers.

    A* with heuristic pointing at rungs that can answer our questions.
    """

    name = "targeted_question"
    description = "A* toward question-answering rungs"
    time_complexity = "O(V log V)"
    space_complexity = "O(V)"

    def get_next_rungs(
        self,
        frontier: Set[str],
        context: SearchContext,
        graph_info: Dict[str, Any]
    ) -> List[str]:
        if not frontier:
            return []

        # Get active questions
        questions = context.get_questions()
        if not questions:
            # No questions - fall back to standard A*
            return LandmarkAStar().get_next_rungs(frontier, context, graph_info)

        # Find rungs that can answer questions
        answerer_rungs = set()
        for q_id, question in questions.items():
            if isinstance(question, dict):
                answerers = question.get('answerable_by', [])
            elif hasattr(question, 'answerable_by'):
                answerers = question.answerable_by
            else:
                continue
            answerer_rungs.update(answerers)

        # Prefer rungs that can answer questions
        max_k = graph_info.get('max_rungs_per_call', 5)
        answerers_in_frontier = frontier & answerer_rungs
        if answerers_in_frontier:
            # Score by question priority
            scored = []
            for rung in answerers_in_frontier:
                priority = self._question_priority(rung, questions)
                scored.append((priority, rung))
            scored.sort(reverse=True)
            return [r for _, r in scored[:max_k]]

        # No direct answerers - find path to answerers
        scored = []
        for rung in frontier:
            # Estimate distance to nearest answerer
            min_dist = float('inf')
            for answerer in answerer_rungs:
                dist = context.get_landmark_heuristic(rung, answerer)
                min_dist = min(min_dist, dist)
            scored.append((min_dist, rung))

        scored.sort()  # Lowest distance first
        return [r for _, r in scored[:max_k]]

    def _question_priority(self, rung: str, questions: Dict[str, Any]) -> float:
        """Get priority of questions this rung can answer."""
        total_priority = 0.0
        for q_id, question in questions.items():
            if isinstance(question, dict):
                answerers = question.get('answerable_by', [])
                priority = question.get('priority', 0.5)
            elif hasattr(question, 'answerable_by'):
                answerers = question.answerable_by
                priority = getattr(question, 'priority', 0.5)
            else:
                continue

            if rung in answerers:
                total_priority += priority

        return total_priority


# =============================================================================
# RETRIEVAL SEARCH (UK Quadrant)
# =============================================================================

class RetrievalSearch(SearchAlgorithm):
    """
    UK quadrant: We have cached/network knowledge - go get it.

    Greedy toward network_wisdom and cache-heavy rungs.
    """

    name = "retrieval"
    description = "Greedy toward cached knowledge"
    time_complexity = "O(V)"
    space_complexity = "O(1)"

    RETRIEVAL_RUNGS = {
        'network_wisdom',
        'hypothesis_retrieval',
        'pattern_lookup',
        'cached_sequence',
        'winning_sequence_replay',
        'prior_lessons',
        'embedding_suggestion'
    }

    def get_next_rungs(
        self,
        frontier: Set[str],
        context: SearchContext,
        graph_info: Dict[str, Any]
    ) -> List[str]:
        if not frontier:
            return []

        max_k = graph_info.get('max_rungs_per_call', 5)

        # Prefer retrieval rungs
        retrieval_in_frontier = frontier & self.RETRIEVAL_RUNGS
        if retrieval_in_frontier:
            # Score by expected value from UK index
            uk_candidates = set(context.get_uk_candidates())

            scored = []
            for rung in retrieval_in_frontier:
                # Higher score if in UK candidates
                score = 1.0 if rung in uk_candidates else 0.5
                scored.append((score, rung))

            scored.sort(reverse=True)
            max_k = graph_info.get('max_rungs_per_call', 5)
            return [r for _, r in scored[:max_k]]

        # Navigate toward retrieval rungs
        scored = []
        for rung in frontier:
            # Estimate distance to nearest retrieval rung
            min_dist = float('inf')
            for ret_rung in self.RETRIEVAL_RUNGS:
                dist = context.get_landmark_heuristic(rung, ret_rung)
                min_dist = min(min_dist, dist)
            scored.append((min_dist, rung))

        scored.sort()
        return [r for _, r in scored[:max_k]]


# =============================================================================
# EXPLORATION WITH EXCLUSIONS (After KK→UU)
# =============================================================================

class ExplorationWithExclusions(SearchAlgorithm):
    """
    UU quadrant after contradiction: Explore while avoiding failed paths.

    Used when KK→UU transition occurs (contradiction detected).
    """

    name = "exploration_exclusions"
    description = "Explore novel paths, exclude failed ones"
    time_complexity = "O(V)"
    space_complexity = "O(1)"

    def __init__(self, boost_novel: bool = True, **_kwargs: object):
        self.boost_novel = boost_novel

    def get_next_rungs(
        self,
        frontier: Set[str],
        context: SearchContext,
        graph_info: Dict[str, Any]
    ) -> List[str]:
        if not frontier:
            return []

        # Score rungs, boosting novel (less visited) ones
        visit_counts = graph_info.get('visit_counts', {})

        scored = []
        for rung in frontier:
            visits = visit_counts.get(rung, 0)

            # Base score
            score = self._score_rung(rung, context, graph_info)

            # Novelty boost
            if self.boost_novel:
                novelty_bonus = 0.5 / (1 + visits)
                score += novelty_bonus

            scored.append((score, rung))

        scored.sort(reverse=True)
        max_k = graph_info.get('max_rungs_per_call', 5)
        return [r for _, r in scored[:max_k]]


# =============================================================================
# ALGORITHM REGISTRY
# =============================================================================

# Domain → Algorithm mapping
DOMAIN_ALGORITHMS: Dict[str, Dict[str, str]] = {
    "physics": {
        "primary": "topological_dp",
        "fallback": "landmark_astar",
    },
    "symbolic": {
        "primary": "bidirectional",
        "fallback": "landmark_astar",
    },
    "spatial": {
        "primary": "hierarchical_astar",
        "fallback": "landmark_astar",
    },
    "exploitation": {
        "primary": "greedy_best_first",
        "fallback": "beam_search",
    },
    "exploration": {
        "primary": "information_maximizing",
        "fallback": "landmark_astar",
    },
    "time_pressure": {
        "primary": "beam_search",
        "fallback": "greedy_best_first",
    },
    "contradiction": {
        "primary": "backtracking_astar",
        "fallback": "exploration_exclusions",
    },
    "general": {
        "primary": "landmark_astar",
        "fallback": "greedy_best_first",
    },
}

# Quadrant → Algorithm mapping (from Part 3)
QUADRANT_ALGORITHMS: Dict[str, str] = {
    "KK": "greedy_best_first",
    "KU": "targeted_question",
    "UK": "retrieval",
    "UU": "information_maximizing",
}

# Algorithm class registry
ALGORITHM_CLASSES: Dict[str, type] = {
    "topological_dp": TopologicalDPSearch,
    "bidirectional": BidirectionalSearch,
    "landmark_astar": LandmarkAStar,
    "greedy_best_first": GreedyBestFirst,
    "beam_search": BeamSearch,
    "information_maximizing": InformationMaximizingSearch,
    "hierarchical_astar": HierarchicalAStar,
    "backtracking_astar": BacktrackingAStar,
    "targeted_question": TargetedQuestionSearch,
    "retrieval": RetrievalSearch,
    "exploration_exclusions": ExplorationWithExclusions,
}


def get_algorithm(name: str, **kwargs) -> SearchAlgorithm:
    """
    Get an algorithm instance by name.

    Args:
        name: Algorithm name (e.g., 'landmark_astar')
        **kwargs: Algorithm-specific parameters

    Returns:
        Algorithm instance
    """
    # Defensive: normalise PascalCase / camelCase to snake_case registry keys
    if name not in ALGORITHM_CLASSES:
        import re
        normalised = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', '_', name).lower()
        if normalised in ALGORITHM_CLASSES:
            name = normalised
        else:
            logger.warning(f"[ALGORITHMS] Unknown algorithm '{name}', using landmark_astar")
            name = "landmark_astar"

    return ALGORITHM_CLASSES[name](**kwargs)


def get_algorithm_for_quadrant(quadrant: str) -> SearchAlgorithm:
    """Get the recommended algorithm for an epistemic quadrant."""
    name = QUADRANT_ALGORITHMS.get(quadrant, "landmark_astar")
    return get_algorithm(name)


def get_algorithm_for_domain(domain: str, use_fallback: bool = False) -> SearchAlgorithm:
    """Get the recommended algorithm for a domain."""
    config = DOMAIN_ALGORITHMS.get(domain, DOMAIN_ALGORITHMS["general"])
    name = config["fallback"] if use_fallback else config["primary"]
    return get_algorithm(name)
