"""
Cognitive Router - Transition-Driven Algorithm Switching.

Phase 4.1 Implementation - Cognitive Routing

This is the central router that orchestrates cognitive search:
1. Maintains blackboard and epistemic state
2. Detects transitions between epistemic quadrants
3. Switches algorithms based on transitions
4. Coordinates with meta-planner for algorithm selection
5. Integrates catastrophic fallback for safety

Key insight from Part 3: Algorithm selection happens on TRANSITIONS,
not on every iteration. Typical decision uses O(12-26) rung evaluations
vs O(1575) for static A* - a 60x improvement.

Usage:
    router = CognitiveRouter()

    # Initialize for a new game
    router.initialize(game_state, all_rungs)

    # Main decision loop
    action, reasoning = router.decide(game_state)
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Set, Tuple

from engines.cognition.algorithms import (
    ALGORITHM_CLASSES,
    DOMAIN_ALGORITHMS,
    QUADRANT_ALGORITHMS,
    SearchAlgorithm,
    get_algorithm,
)
from engines.cognition.blackboard import Blackboard, RumsfeldQuadrant
from engines.cognition.catastrophic_fallback import CatastrophicFallback, FailureType
from engines.cognition.epistemic_state import EpistemicTransition, TransitionResponse
from engines.cognition.epistemic_tracker import EpistemicTracker, RungResult
from engines.cognition.hysteresis import HysteresisManager
from engines.cognition.meta_planner import MetaPlanner
from engines.cognition.precomputation import PrecomputationManager, PrecomputedData
from engines.cognition.search_context import (
    MutationRequest,
    MutationType,
    SearchContext,
    SearchPhase,
    create_search_context,
)

logger = logging.getLogger(__name__)


# =============================================================================
# TRANSITION RESPONSE MAP
# =============================================================================

# The heart of Part 3: Transitions drive algorithm selection
TRANSITION_RESPONSES: Dict[Tuple[RumsfeldQuadrant, RumsfeldQuadrant], TransitionResponse] = {
    # === Discovery Transitions ===
    (RumsfeldQuadrant.UU, RumsfeldQuadrant.KU): TransitionResponse(
        algorithm="targeted_question",
        action="focus",
        description="Found a specific question - focus search toward answerers",
        params={"use_answerer_heuristic": True}
    ),
    (RumsfeldQuadrant.KU, RumsfeldQuadrant.KK): TransitionResponse(
        algorithm="greedy_best_first",
        action="exploit",
        description="Answered the question - exploit aggressively",
        params={"commit_threshold": 0.8}
    ),
    (RumsfeldQuadrant.UK, RumsfeldQuadrant.KK): TransitionResponse(
        algorithm="greedy_best_first",
        action="exploit",
        description="Retrieved knowledge - exploit",
        params={"commit_threshold": 0.8}
    ),

    # === Contradiction / Regression Transitions ===
    (RumsfeldQuadrant.KK, RumsfeldQuadrant.KU): TransitionResponse(
        algorithm="backtracking_astar",
        action="backtrack",
        description="Mild contradiction - backtrack and target new question",
        params={"backtrack_depth": 1, "exclude_last": True}
    ),
    (RumsfeldQuadrant.KK, RumsfeldQuadrant.UU): TransitionResponse(
        algorithm="exploration_exclusions",
        action="reset",
        description="Severe contradiction - reset with exclusions",
        params={"exclude_failed_path": True, "boost_novel_rungs": True}
    ),

    # === Stagnation Transitions ===
    (RumsfeldQuadrant.UU, RumsfeldQuadrant.UU): TransitionResponse(
        algorithm="information_maximizing",
        action="continue",
        description="Still exploring - maximize information gain",
        params={"exploration_bonus": 1.5, "curiosity_weight": 0.3}
    ),
    (RumsfeldQuadrant.KU, RumsfeldQuadrant.KU): TransitionResponse(
        algorithm="targeted_question",
        action="alternate",
        description="Question still open - try alternate answerers",
        params={"deprioritize_current": True}
    ),

    # === Retrieval Transitions ===
    (RumsfeldQuadrant.UU, RumsfeldQuadrant.UK): TransitionResponse(
        algorithm="retrieval",
        action="retrieve",
        description="Found cached knowledge - retrieve it",
        params={"query_network_first": True}
    ),
    (RumsfeldQuadrant.KU, RumsfeldQuadrant.UK): TransitionResponse(
        algorithm="retrieval",
        action="retrieve",
        description="Network might answer our question - query it",
        params={"filter_by_question": True}
    ),
}


def get_algorithm_for_transition(transition: EpistemicTransition) -> TransitionResponse:
    """Look up response for a given transition."""
    key = (transition.from_quadrant, transition.to_quadrant)
    return TRANSITION_RESPONSES.get(key, TransitionResponse.default())


# =============================================================================
# ROUTER CONFIGURATION
# =============================================================================

@dataclass
class RouterConfig:
    """Configuration for the CognitiveRouter."""
    # Maximum iterations per decision
    max_iterations: int = 50

    # Maximum rungs to evaluate per algorithm call
    max_rungs_per_call: int = 5

    # Confidence threshold for committing
    commit_threshold: float = 0.85

    # Time budget per decision (seconds)
    time_budget_seconds: float = 5.0

    # Enable hysteresis for quadrant transitions
    use_hysteresis: bool = True

    # Enable meta-planner caching
    use_meta_planner_cache: bool = True

    # Enable catastrophic fallback
    use_catastrophic_fallback: bool = True

    # Algorithm switching cooldown (iterations)
    algorithm_switch_cooldown: int = 3

    # Whether to precompute graph structures at initialization
    precompute_on_init: bool = True


DEFAULT_CONFIG = RouterConfig()


# =============================================================================
# ROUTER STATE
# =============================================================================

@dataclass
class RouterState:
    """Internal state of the router during a decision."""
    # Current iteration
    iteration: int = 0

    # Current algorithm
    current_algorithm: Optional[SearchAlgorithm] = None
    current_algorithm_name: str = ""

    # Iteration since last algorithm switch
    iterations_since_switch: int = 0

    # Path of rungs visited
    path: List[str] = field(default_factory=list)

    # Rungs visited (set for O(1) lookup)
    visited_rungs: Set[str] = field(default_factory=set)

    # Rungs excluded (after contradictions)
    excluded_rungs: Set[str] = field(default_factory=set)

    # Checkpoints for backtracking
    checkpoints: List[Dict[str, Any]] = field(default_factory=list)

    # Maximum confidence seen
    max_confidence: float = 0.0

    # Best rung result so far
    best_result: Optional[RungResult] = None

    # Time tracking
    start_time: float = 0.0

    # Transitions seen
    transitions: List[EpistemicTransition] = field(default_factory=list)


# =============================================================================
# DECISION RESULT
# =============================================================================

@dataclass
class DecisionResult:
    """Result of a decision cycle."""
    # Selected action (typically rung name)
    action: str

    # Reasoning for the decision
    reasoning: str

    # Confidence in the decision
    confidence: float

    # Statistics
    iterations: int = 0
    rungs_evaluated: int = 0
    transitions_count: int = 0
    algorithm_switches: int = 0
    time_elapsed: float = 0.0

    # Path taken
    path: List[str] = field(default_factory=list)

    # Whether fallback was used
    used_fallback: bool = False
    fallback_reason: Optional[str] = None

    # Final quadrant
    final_quadrant: str = "UU"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'action': self.action,
            'reasoning': self.reasoning,
            'confidence': self.confidence,
            'iterations': self.iterations,
            'rungs_evaluated': self.rungs_evaluated,
            'transitions_count': self.transitions_count,
            'algorithm_switches': self.algorithm_switches,
            'time_elapsed': self.time_elapsed,
            'path': self.path,
            'used_fallback': self.used_fallback,
            'fallback_reason': self.fallback_reason,
            'final_quadrant': self.final_quadrant,
        }


# =============================================================================
# COGNITIVE ROUTER
# =============================================================================

class CognitiveRouter:
    """
    Transition-Driven Cognitive Router.

    The router orchestrates cognitive search by:
    1. Tracking epistemic state (KK/KU/UK/UU quadrants)
    2. Detecting transitions between quadrants
    3. Switching algorithms based on transitions
    4. Using meta-planner for algorithm selection
    5. Falling back to static ordering when catastrophic failure detected

    Main flow:
    1. Initialize with game state and rungs
    2. Call decide() for each decision
    3. Router maintains state across decisions within a game
    """

    def __init__(
        self,
        config: Optional[RouterConfig] = None,
        blackboard: Optional[Blackboard] = None
    ):
        """
        Initialize the cognitive router.

        Args:
            config: Router configuration
            blackboard: Existing blackboard (or creates new one)
        """
        self.config = config or DEFAULT_CONFIG

        # Core components
        self.blackboard = blackboard or Blackboard()
        self.epistemic_tracker = EpistemicTracker()
        self.hysteresis = HysteresisManager() if self.config.use_hysteresis else None

        # Meta-planner for algorithm selection
        self.meta_planner = MetaPlanner() if self.config.use_meta_planner_cache else None

        # Catastrophic fallback
        self.fallback = CatastrophicFallback() if self.config.use_catastrophic_fallback else None

        # Precomputation manager
        self.precomputation = PrecomputationManager()
        self._precomputed_data: Optional[PrecomputedData] = None

        # Graph structure
        self._nodes: Dict[str, Dict[str, Any]] = {}
        self._edges: Dict[str, List[str]] = {}
        self._all_rungs: Set[str] = set()

        # Router state (reset per decision)
        self._state = RouterState()

        # Statistics
        self._total_decisions = 0
        self._total_fallbacks = 0
        self._algorithm_usage: Dict[str, int] = defaultdict(int)

        # Game context
        self._game_id = ""
        self._decision_id = 0

    # -------------------------------------------------------------------------
    # INITIALIZATION
    # -------------------------------------------------------------------------

    def initialize(
        self,
        nodes: Dict[str, Dict[str, Any]],
        edges: Dict[str, List[str]],
        game_id: str = "",
    ) -> None:
        """
        Initialize router for a new game.

        Args:
            nodes: Dict of rung_name -> {category, priority, etc}
            edges: Dict of source -> [target1, target2, ...]
            game_id: Game identifier for logging
        """
        self._nodes = nodes
        self._edges = edges
        self._all_rungs = set(nodes.keys())
        self._game_id = game_id
        self._decision_id = 0

        # Precompute graph structures
        if self.config.precompute_on_init:
            self._precomputed_data = self.precomputation.precompute(nodes, edges)
            logger.info(
                f"[ROUTER] Precomputed: {self._precomputed_data.node_count} nodes, "
                f"{self._precomputed_data.edge_count} edges"
            )

        # Reset components
        self.blackboard = Blackboard()
        self.epistemic_tracker.reset()
        if self.hysteresis:
            self.hysteresis.reset()

        logger.info(f"[ROUTER] Initialized for game {game_id} with {len(nodes)} rungs")

    def initialize_from_context(
        self,
        context: Dict[str, Any],
        all_rungs: Set[str],
        game_id: str = ""
    ) -> None:
        """
        Initialize from legacy context dict.

        This provides backward compatibility with the existing system.
        """
        # Build minimal node structure from rungs
        nodes = {r: {"name": r, "category": "general"} for r in all_rungs}
        edges: Dict[str, List[str]] = {}  # No edges in legacy mode

        self.initialize(nodes, edges, game_id)

        # Import context into blackboard
        self.blackboard.from_context(context)

    # -------------------------------------------------------------------------
    # MAIN DECISION LOOP
    # -------------------------------------------------------------------------

    def decide(
        self,
        game_state: Dict[str, Any],
        rung_executor: Optional[Callable[[str, Dict], RungResult]] = None
    ) -> DecisionResult:
        """
        Make a decision for the current game state.

        This is the main entry point. It:
        1. Initializes decision state
        2. Runs the transition-driven loop
        3. Returns best action found

        Args:
            game_state: Current game state
            rung_executor: Optional function to execute rungs (for simulation)

        Returns:
            DecisionResult with action, reasoning, and statistics
        """
        self._decision_id += 1
        self._total_decisions += 1

        # Reset state for new decision
        self._state = RouterState()
        self._state.start_time = time.perf_counter()

        # Reset tracking components
        self.epistemic_tracker.reset()
        if self.hysteresis:
            self.hysteresis.reset()
        if self.fallback:
            self.fallback.reset(self._game_id, self._decision_id)

        # Update blackboard from game state
        self._update_blackboard_from_game_state(game_state)

        # Create initial search context
        context = self._create_search_context()

        # Select initial algorithm based on quadrant
        quadrant = self.epistemic_tracker.current_state.primary_quadrant
        self._switch_algorithm(quadrant.name, context)

        try:
            # Run main loop
            result = self._decision_loop(game_state, context, rung_executor)
            return result

        except Exception as e:
            logger.error(f"[ROUTER] Decision error: {e}")
            # Return safe fallback
            return DecisionResult(
                action="survey",  # Safe default
                reasoning=f"Error in decision: {e}",
                confidence=0.0,
                used_fallback=True,
                fallback_reason=str(e),
            )

    def _decision_loop(
        self,
        game_state: Dict[str, Any],
        context: SearchContext,
        rung_executor: Optional[Callable[[str, Dict], RungResult]]
    ) -> DecisionResult:
        """
        Main decision loop with transition-driven switching.

        This implements the Part 3 insight: Switch algorithms only on transitions,
        not every iteration.
        """
        algorithm_switches = 0

        while self._state.iteration < self.config.max_iterations:
            self._state.iteration += 1

            # Check time budget
            elapsed = time.perf_counter() - self._state.start_time
            if elapsed > self.config.time_budget_seconds:
                logger.warning(f"[ROUTER] Time budget exceeded: {elapsed:.2f}s")
                break

            # Check catastrophic fallback
            if self.fallback:
                should_fallback, failure_type = self.fallback.should_fallback(
                    self._state.max_confidence
                )
                if should_fallback:
                    return self._handle_fallback(failure_type, context)

            # Get frontier (available rungs)
            frontier = self._get_frontier(context)

            if not frontier:
                if self.fallback:
                    self.fallback.record_empty_frontier()
                    should_fallback, failure_type = self.fallback.should_fallback()
                    if should_fallback:
                        return self._handle_fallback(failure_type, context)
                continue

            # Get next rungs from current algorithm
            if self._state.current_algorithm is None:
                break

            graph_info = self._build_graph_info()
            next_rungs = self._state.current_algorithm.get_next_rungs(
                frontier, context, graph_info
            )

            if not next_rungs:
                if self.fallback:
                    self.fallback.record_empty_frontier()
                continue

            # Execute the rung
            rung_name = next_rungs[0]
            result = self._execute_rung(rung_name, game_state, rung_executor)

            # Update state
            self._state.path.append(rung_name)
            self._state.visited_rungs.add(rung_name)
            context.visited_rungs.add(rung_name)
            context.current_path.append(rung_name)

            if self.fallback:
                self.fallback.record_iteration(rung_name)

            # Track best result
            if result.confidence > self._state.max_confidence:
                self._state.max_confidence = result.confidence
                self._state.best_result = result

            # Check for commitment
            if result.confidence >= self.config.commit_threshold:
                return self._commit_decision(result)

            # Update epistemic state
            transitions = self.epistemic_tracker.update_from_rung_result(
                rung_name=rung_name,
                result=result,
                blackboard=self.blackboard,
                all_rungs=self._all_rungs,
                visited_rungs=self._state.visited_rungs
            )

            # Handle transitions
            for transition in transitions:
                self._state.transitions.append(transition)

                # Apply hysteresis filtering
                if self.hysteresis:
                    should_switch = self.hysteresis.record_signal(
                        transition.from_quadrant,
                        transition.to_quadrant
                    )
                    if not should_switch:
                        continue

                # Check algorithm switch cooldown
                if self._state.iterations_since_switch < self.config.algorithm_switch_cooldown:
                    continue

                # Get transition response
                response = get_algorithm_for_transition(transition)

                # Handle special actions
                if response.action == "backtrack" and self._state.checkpoints:
                    self._handle_backtrack(context, response.params)
                elif response.action == "reset":
                    self._handle_reset(context, response.params)

                # Switch algorithm
                if response.algorithm != self._state.current_algorithm_name:
                    self._switch_algorithm(response.algorithm, context, response.params)
                    algorithm_switches += 1
                    self._state.iterations_since_switch = 0

                # Record with fallback
                if self.fallback:
                    self.fallback.record_quadrant(
                        transition.to_quadrant.name,
                        self._state.max_confidence
                    )

                    # Check for contradiction
                    if transition.is_regression:
                        self.fallback.record_contradiction()

            # Update context
            context = self._update_search_context(context)
            self._state.iterations_since_switch += 1

            # Process mutation requests
            self._process_mutations(context)

        # Loop ended without commitment - return best result
        return self._finalize_decision(algorithm_switches)

    # -------------------------------------------------------------------------
    # ALGORITHM SWITCHING
    # -------------------------------------------------------------------------

    def _switch_algorithm(
        self,
        algorithm_name: str,
        context: SearchContext,
        params: Optional[Dict[str, Any]] = None
    ) -> None:
        """Switch to a new algorithm."""
        params = params or {}

        # Use meta-planner for selection if available
        if self.meta_planner:
            selection = self.meta_planner.select_algorithm(context)
            if selection.algorithm:
                # SelectionResult.algorithm is a SearchAlgorithm instance
                algorithm_name = selection.algorithm.name
                # Note: SelectionResult doesn't have params, use provided ones

        # Get algorithm instance
        try:
            algorithm = get_algorithm(algorithm_name, **params)
            # Use the actual algorithm name (get_algorithm may fall back)
            self._state.current_algorithm = algorithm
            self._state.current_algorithm_name = algorithm.name
            self._algorithm_usage[algorithm.name] += 1

            logger.debug(f"[ROUTER] Switched to algorithm: {algorithm.name}")

        except Exception as e:
            logger.error(f"[ROUTER] Failed to switch to {algorithm_name}: {e}")
            # Fall back to landmark A*
            self._state.current_algorithm = get_algorithm("landmark_astar")
            self._state.current_algorithm_name = "landmark_astar"

    # -------------------------------------------------------------------------
    # RUNG EXECUTION
    # -------------------------------------------------------------------------

    def _execute_rung(
        self,
        rung_name: str,
        game_state: Dict[str, Any],
        rung_executor: Optional[Callable[[str, Dict], RungResult]]
    ) -> RungResult:
        """
        Execute a rung and get the result.

        If a rung_executor is provided, use it. Otherwise, create a
        synthetic result for testing.
        """
        if rung_executor:
            return rung_executor(rung_name, game_state)

        # Create synthetic result for testing
        return RungResult(
            rung_name=rung_name,
            confidence=0.5,  # Neutral confidence
        )

    # -------------------------------------------------------------------------
    # FALLBACK HANDLING
    # -------------------------------------------------------------------------

    def _handle_fallback(
        self,
        failure_type: FailureType,
        context: SearchContext
    ) -> DecisionResult:
        """Handle catastrophic fallback."""
        self._total_fallbacks += 1

        context_snapshot = {
            'quadrant': self.epistemic_tracker.current_state.primary_quadrant.name,
            'max_confidence': self._state.max_confidence,
            'visited_rungs': list(self._state.visited_rungs),
            'path': self._state.path,
        }

        # Get fallback ordering
        has_replay = self.blackboard.slot('winning_sequence') is not None
        if self.fallback is None:
            ordering = ["survey"]  # Default fallback
        else:
            ordering = self.fallback.trigger_fallback(
                context_snapshot,
                has_replay_sequence=has_replay,
                current_confidence=self._state.max_confidence
            )

        # Return first rung from ordering as action
        action = ordering[0] if ordering else "survey"

        return DecisionResult(
            action=action,
            reasoning=f"Fallback triggered: {failure_type.value}",
            confidence=self._state.max_confidence,
            iterations=self._state.iteration,
            rungs_evaluated=len(self._state.visited_rungs),
            transitions_count=len(self._state.transitions),
            time_elapsed=time.perf_counter() - self._state.start_time,
            path=self._state.path,
            used_fallback=True,
            fallback_reason=failure_type.value,
            final_quadrant=self.epistemic_tracker.current_state.primary_quadrant.name,
        )

    # -------------------------------------------------------------------------
    # BACKTRACKING AND RESET
    # -------------------------------------------------------------------------

    def _handle_backtrack(
        self,
        context: SearchContext,
        params: Dict[str, Any]
    ) -> None:
        """Handle backtrack action from transition response."""
        if not self._state.checkpoints:
            return

        depth = params.get("backtrack_depth", 1)
        exclude_last = params.get("exclude_last", True)

        # Pop checkpoints
        for _ in range(min(depth, len(self._state.checkpoints))):
            checkpoint = self._state.checkpoints.pop()

            # Restore state
            if "path" in checkpoint:
                # Exclude rungs in the failed path section
                if exclude_last:
                    failed_section = self._state.path[len(checkpoint["path"]):]
                    self._state.excluded_rungs.update(failed_section)
                    context.excluded_rungs.update(failed_section)

                self._state.path = checkpoint["path"]
                self._state.visited_rungs = set(checkpoint["path"])
                context.visited_rungs = set(checkpoint["path"])
                context.current_path = checkpoint["path"].copy()

        logger.debug(f"[ROUTER] Backtracked, excluded: {self._state.excluded_rungs}")

    def _handle_reset(
        self,
        context: SearchContext,
        params: Dict[str, Any]
    ) -> None:
        """Handle reset action from transition response."""
        exclude_failed = params.get("exclude_failed_path", True)

        if exclude_failed:
            # Exclude entire path that led to contradiction
            self._state.excluded_rungs.update(self._state.path)
            context.excluded_rungs.update(self._state.path)

        # Clear path
        self._state.path = []
        self._state.visited_rungs.clear()
        context.visited_rungs.clear()
        context.current_path.clear()

        # Clear checkpoints
        self._state.checkpoints.clear()

        logger.debug(f"[ROUTER] Reset with exclusions: {self._state.excluded_rungs}")

    # -------------------------------------------------------------------------
    # COMMITMENT
    # -------------------------------------------------------------------------

    def _commit_decision(self, result: RungResult) -> DecisionResult:
        """Commit to a decision based on high-confidence result."""
        return DecisionResult(
            action=result.rung_name,
            reasoning=f"High confidence ({result.confidence:.2f}) from {result.rung_name}",
            confidence=result.confidence,
            iterations=self._state.iteration,
            rungs_evaluated=len(self._state.visited_rungs),
            transitions_count=len(self._state.transitions),
            time_elapsed=time.perf_counter() - self._state.start_time,
            path=self._state.path,
            final_quadrant=self.epistemic_tracker.current_state.primary_quadrant.name,
        )

    def _finalize_decision(self, algorithm_switches: int) -> DecisionResult:
        """Finalize decision after loop ends."""
        if self._state.best_result:
            action = self._state.best_result.rung_name
            confidence = self._state.best_result.confidence
            reasoning = f"Best result from {action} ({confidence:.2f})"
        else:
            action = self._state.path[-1] if self._state.path else "survey"
            confidence = self._state.max_confidence
            reasoning = "Loop ended without high-confidence result"

        return DecisionResult(
            action=action,
            reasoning=reasoning,
            confidence=confidence,
            iterations=self._state.iteration,
            rungs_evaluated=len(self._state.visited_rungs),
            transitions_count=len(self._state.transitions),
            algorithm_switches=algorithm_switches,
            time_elapsed=time.perf_counter() - self._state.start_time,
            path=self._state.path,
            final_quadrant=self.epistemic_tracker.current_state.primary_quadrant.name,
        )

    # -------------------------------------------------------------------------
    # CONTEXT MANAGEMENT
    # -------------------------------------------------------------------------

    def _create_search_context(self) -> SearchContext:
        """Create initial search context."""
        precomputed = self._precomputed_data or PrecomputedData()
        quadrant = self.epistemic_tracker.current_state.primary_quadrant

        return create_search_context(
            blackboard=self.blackboard,
            precomputed=precomputed,
            edge_trust={},  # Phase 7 will populate this
            crystallized={},  # Phase 7 will populate this
            current_quadrant=quadrant.name
        )

    def _update_search_context(self, context: SearchContext) -> SearchContext:
        """Update search context after iteration."""
        # Update quadrant
        context.current_quadrant = self.epistemic_tracker.current_state.primary_quadrant.name

        # Update time budget
        elapsed = time.perf_counter() - self._state.start_time
        context.time_budget = max(0.0, 1.0 - elapsed / self.config.time_budget_seconds)

        # Update from blackboard
        context.blackboard_snapshot = self.blackboard.to_dict()

        return context

    def _update_blackboard_from_game_state(self, game_state: Dict[str, Any]) -> None:
        """Update blackboard from game state."""
        for key, value in game_state.items():
            if key not in ('frame', 'raw_frame'):  # Skip large data
                self.blackboard.slot(key, value)

    # -------------------------------------------------------------------------
    # FRONTIER MANAGEMENT
    # -------------------------------------------------------------------------

    def _get_frontier(self, context: SearchContext) -> Set[str]:
        """Get available rungs (not visited, not excluded)."""
        frontier = self._all_rungs - context.visited_rungs - context.excluded_rungs
        return frontier

    # -------------------------------------------------------------------------
    # GRAPH INFO
    # -------------------------------------------------------------------------

    def _build_graph_info(self) -> Dict[str, Any]:
        """Build graph info for algorithm."""
        if self._precomputed_data:
            return {
                'nodes': self._nodes,
                'edges': self._edges,
                'reverse_edges': self._precomputed_data.reverse_edges,
                'is_dag': self._precomputed_data.is_dag,
                'topological_order': self._precomputed_data.topological_order,
            }
        return {
            'nodes': self._nodes,
            'edges': self._edges,
            'reverse_edges': {},
            'is_dag': False,
            'topological_order': [],
        }

    # -------------------------------------------------------------------------
    # MUTATION PROCESSING
    # -------------------------------------------------------------------------

    def _process_mutations(self, context: SearchContext) -> None:
        """Process mutation requests from algorithms."""
        mutations = context.get_pending_mutations()
        context.clear_pending_mutations()

        # Sort by priority
        mutations.sort(key=lambda m: -m.priority)

        for mutation in mutations:
            if mutation.mutation_type == MutationType.CHECKPOINT:
                self._state.checkpoints.append({
                    "path": self._state.path.copy(),
                    "visited": self._state.visited_rungs.copy(),
                    "confidence": self._state.max_confidence,
                })
            elif mutation.mutation_type == MutationType.EXCLUDE_RUNGS:
                rungs = mutation.payload.get('rungs', set())
                self._state.excluded_rungs.update(rungs)
                context.excluded_rungs.update(rungs)
            elif mutation.mutation_type == MutationType.RECORD_CONTRADICTION:
                if self.fallback:
                    self.fallback.record_contradiction()

    # -------------------------------------------------------------------------
    # STATISTICS
    # -------------------------------------------------------------------------

    def get_statistics(self) -> Dict[str, Any]:
        """Get router statistics."""
        return {
            'total_decisions': self._total_decisions,
            'total_fallbacks': self._total_fallbacks,
            'fallback_rate': self._total_fallbacks / max(1, self._total_decisions),
            'algorithm_usage': dict(self._algorithm_usage),
            'game_id': self._game_id,
        }

    # -------------------------------------------------------------------------
    # LEGACY COMPATIBILITY
    # -------------------------------------------------------------------------

    def get_ordering_for_context(
        self,
        context: Dict[str, Any]
    ) -> List[str]:
        """
        Get a static ordering based on context (legacy compatibility).

        This provides backward compatibility with code that expects
        a static ordering rather than dynamic decisions.
        """
        # Initialize from context
        all_rungs = set(self._nodes.keys()) if self._nodes else set()
        if not all_rungs:
            return ["survey", "control_tracker", "network_wisdom", "smart_action_selection"]

        # Determine domain/mode
        if context.get('replay_sequence'):
            return ["cached_sequence", "winning_sequence_replay", "checkpoint_exploitation"]

        if context.get('frontier', False):
            return list(self._all_rungs)[:20]  # First 20 rungs

        # Default ordering based on category priority
        ordered = sorted(
            all_rungs,
            key=lambda r: self._nodes.get(r, {}).get('priority', 50)
        )
        return ordered[:30]
