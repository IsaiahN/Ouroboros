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
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from engines.cognition.algorithms import (
    QUADRANT_ALGORITHMS,
    SearchAlgorithm,
    get_algorithm,
)
from engines.cognition.blackboard import Blackboard, RumsfeldQuadrant
from engines.cognition.catastrophic_fallback import CatastrophicFallback, FailureType
from engines.cognition.eisenhower_layer import EisenhowerLayer, EisenhowerQuadrant
from engines.cognition.epistemic_state import EpistemicTransition, TransitionResponse
from engines.cognition.epistemic_tracker import EpistemicTracker, RungResult
from engines.cognition.hysteresis import HysteresisManager
from engines.cognition.meta_planner import MetaPlanner
from engines.cognition.phenomenology_layer import (
    AlgorithmModulation,
    PhenomenologyLayer,
    Valence,
)
from engines.cognition.precomputation import PrecomputationManager, PrecomputedData
from engines.cognition.search_context import (
    MutationType,
    SearchContext,
    create_search_context,
)
from engines.cognition.valence_tagged_slot import CRITICAL_SLOT_VALENCE_RULES

# Graph evolution for edge trust tracking (Phase 7+11)
try:
    from engines.reasoning.graph_evolution import GraphEvolution as _GraphEvolution
    _GRAPH_EVOLUTION_AVAILABLE = True
except ImportError:
    _GraphEvolution = None
    _GRAPH_EVOLUTION_AVAILABLE = False

# GameFeelTrajectory store for anomaly detection (Phase 7+11)
try:
    from engines.reasoning.graph_evolution import FeelTrajectoryStore
    _FEEL_TRAJECTORY_AVAILABLE = True
except ImportError:
    FeelTrajectoryStore = None  # type: ignore[assignment,misc]
    _FEEL_TRAJECTORY_AVAILABLE = False

# Slot registry for typed blackboard initialisation (Phase 1)
try:
    from engines.cognition.slot_registry import SLOT_DEFINITIONS
    _SLOT_REGISTRY_AVAILABLE = True
except ImportError:
    SLOT_DEFINITIONS = None  # type: ignore[assignment]
    _SLOT_REGISTRY_AVAILABLE = False

# Question manager for KU lifecycle (Phase 6)
try:
    from engines.cognition.question_manager import QuestionManager
    _QUESTION_MANAGER_AVAILABLE = True
except ImportError:
    QuestionManager = None  # type: ignore[assignment,misc]
    _QUESTION_MANAGER_AVAILABLE = False

# Routing metrics tracker (Phase 5)
try:
    from engines.cognition.routing_metrics import RoutingMetricsTracker
    _ROUTING_METRICS_AVAILABLE = True
except ImportError:
    RoutingMetricsTracker = None  # type: ignore[assignment,misc]
    _ROUTING_METRICS_AVAILABLE = False

# Epistemic logger for trace buffering (Phase 6)
try:
    from engines.cognition.epistemic_logging import EpistemicLogger
    _EPISTEMIC_LOGGER_AVAILABLE = True
except ImportError:
    EpistemicLogger = None  # type: ignore[assignment,misc]
    _EPISTEMIC_LOGGER_AVAILABLE = False

# UK Potential Index for bloom-filter knowledge checks (Phase 6)
try:
    from engines.cognition.uk_potential_index import UKPotentialIndex
    _UK_INDEX_AVAILABLE = True
except ImportError:
    UKPotentialIndex = None  # type: ignore[assignment,misc]
    _UK_INDEX_AVAILABLE = False

# Process knowledge extractor for transfer learning (Phase 7.4)
try:
    from engines.cognition.process_knowledge import ProcessKnowledgeExtractor
    _PROCESS_KNOWLEDGE_AVAILABLE = True
except ImportError:
    ProcessKnowledgeExtractor = None  # type: ignore[assignment,misc]
    _PROCESS_KNOWLEDGE_AVAILABLE = False

# Cognitive parameter history for debugging (global singleton)
try:
    from config.cognitive_parameters import PARAMETER_HISTORY, CognitiveParameters
    _PARAM_HISTORY_AVAILABLE = True
except ImportError:
    PARAMETER_HISTORY = None  # type: ignore[assignment]
    CognitiveParameters = None  # type: ignore[assignment,misc]
    _PARAM_HISTORY_AVAILABLE = False

logger = logging.getLogger(__name__)


# =============================================================================
# TRANSITION RESPONSE MAP - loaded from config/transition_responses.json
# =============================================================================

# Map JSON algorithm names -> internal algorithm registry names
_ALGORITHM_NAME_MAP: Dict[str, str] = {
    "TargetedQuestionSearch": "targeted_question",
    "GreedyExploitation": "greedy_best_first",
    "BacktrackingTargetedSearch": "backtracking_astar",
    "ExplorationWithExclusions": "exploration_exclusions",
    "InformationMaximizingSearch": "information_maximizing",
    "AlternateQuestionSearch": "targeted_question",  # Variant of targeted
    "RetrievalSearch": "retrieval",
    "LandmarkAStar": "landmark_astar",
}


def _load_transition_responses() -> Dict[Tuple[RumsfeldQuadrant, RumsfeldQuadrant], TransitionResponse]:
    """Load transition responses from JSON config, falling back to hardcoded defaults."""
    import json as _json
    from pathlib import Path as _Path

    config_path = _Path(__file__).resolve().parents[2] / "config" / "transition_responses.json"
    if not config_path.exists():
        logger.warning("[ROUTER] transition_responses.json not found, using hardcoded defaults")
        return _HARDCODED_TRANSITION_RESPONSES

    try:
        with open(config_path, 'r') as f:
            data = _json.load(f)

        quadrant_map = {
            'KK': RumsfeldQuadrant.KK,
            'KU': RumsfeldQuadrant.KU,
            'UK': RumsfeldQuadrant.UK,
            'UU': RumsfeldQuadrant.UU,
        }

        result: Dict[Tuple[RumsfeldQuadrant, RumsfeldQuadrant], TransitionResponse] = {}
        for key_str, cfg in data.get('transitions', {}).items():
            parts = key_str.split('->')
            if len(parts) != 2:
                continue
            from_q = quadrant_map.get(parts[0].strip())
            to_q = quadrant_map.get(parts[1].strip())
            if from_q is None or to_q is None:
                continue

            # Resolve algorithm name to internal registry name
            algo = _ALGORITHM_NAME_MAP.get(cfg['algorithm'], cfg['algorithm'].lower())

            result[(from_q, to_q)] = TransitionResponse(
                algorithm=algo,
                action=cfg.get('action', 'continue'),
                description=cfg.get('description', ''),
                params=cfg.get('params', {}),
            )

        logger.info(f"[ROUTER] Loaded {len(result)} transition responses from JSON config")
        return result

    except Exception as e:
        logger.warning(f"[ROUTER] Failed to load transition_responses.json: {e}, using defaults")
        return _HARDCODED_TRANSITION_RESPONSES


# Hardcoded fallback (original map, kept for resilience)
_HARDCODED_TRANSITION_RESPONSES: Dict[Tuple[RumsfeldQuadrant, RumsfeldQuadrant], TransitionResponse] = {
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

    # === Forward Progress (UU->KK) ===
    (RumsfeldQuadrant.UU, RumsfeldQuadrant.KK): TransitionResponse(
        algorithm="greedy_best_first",
        action="exploit",
        description="Exploration yielded knowledge - exploit it",
        params={"commit_threshold": 0.55}
    ),

    # === Contradiction Recovery (KU->UU, UK->KU, UK->UU) ===
    (RumsfeldQuadrant.KU, RumsfeldQuadrant.UU): TransitionResponse(
        algorithm="information_maximizing",
        action="broaden",
        description="Question led to contradiction - broaden search",
        params={"exploration_bonus": 1.5, "exclude_answered": True}
    ),
    (RumsfeldQuadrant.UK, RumsfeldQuadrant.KU): TransitionResponse(
        algorithm="targeted_question",
        action="focus",
        description="Retrieved knowledge raised new questions",
        params={"use_answerer_heuristic": True}
    ),
    (RumsfeldQuadrant.UK, RumsfeldQuadrant.UU): TransitionResponse(
        algorithm="exploration_exclusions",
        action="reset",
        description="Cached knowledge contradicted - explore afresh",
        params={"exclude_failed_path": True}
    ),
    (RumsfeldQuadrant.KK, RumsfeldQuadrant.UK): TransitionResponse(
        algorithm="retrieval",
        action="retrieve",
        description="Exploiting but untapped knowledge available",
        params={"query_network_first": True}
    ),
}

# Load from JSON at module level (falls back to hardcoded)
TRANSITION_RESPONSES = _load_transition_responses()


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
    # Maximum iterations per decision (each evaluates up to max_rungs_per_call)
    # With batch evaluation: 15 iterations x 5 rungs = 75 rung evals max.
    # The rung graph has ~63 nodes, so 15 iterations guarantees full
    # coverage even when some candidates are skipped.
    # Architecture target: O(26) typical. With agreement boost, the router
    # usually commits in 2-4 iterations when rungs agree.
    max_iterations: int = 15

    # Maximum rungs to evaluate per algorithm call (batch size)
    # Algorithms return their top-K candidates ranked by expected value.
    # The router evaluates all K in one pass and checks for agreement.
    max_rungs_per_call: int = 5

    # Confidence threshold for committing
    # Most rungs output confidence ~0.6. At 0.50, a single confident rung
    # can commit. With agreement boost (+0.15), two agreeing rungs reach
    # 0.75, well above threshold. Previous 0.65 was unreachable for single
    # rungs, causing 100% fallback.
    commit_threshold: float = 0.50

    # Time budget per decision (seconds).
    # Must be generous enough for engine warm-up (first call per game
    # initialises DB connections and engine objects inside rung evaluations)
    # and for DB-querying rungs on large databases (3+ GB).
    # The action budget is the real limiter, not wall-clock time.
    time_budget_seconds: float = 30.0

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

    # Best result that carries a valid ACTION string (e.g., 'ACTION3').
    # Many rungs (survey, filters) produce confidence > 0 but no action.
    # Without this, _finalize_decision returns a non-actionable rung,
    # forcing the caller to fall back to random action selection.
    best_actionable_result: Optional[RungResult] = None
    max_actionable_confidence: float = 0.0

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
    # Selected rung name (the cognitive unit that won)
    action: str

    # Reasoning for the decision
    reasoning: str

    # Confidence in the decision
    confidence: float

    # The actual ACTION string (e.g., 'ACTION3') produced by the winning rung.
    # This bridges the cognitive plane (rung names, epistemic tracking) with
    # the action plane (ACTION1-7 sent to ARC API). When present, callers
    # should use this instead of re-executing the rung named in `action`.
    action_value: Optional[str] = None

    # Metadata from the winning rung (e.g., coordinates for ACTION6)
    action_metadata: Dict[str, Any] = field(default_factory=dict)

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

    # Initial quadrant (at start of decision, for tracking transitions)
    initial_quadrant: str = "UU"

    # Algorithm tracking
    algorithm_name: str = "unknown"
    algorithms_history: List[str] = field(default_factory=list)
    quadrant_transitions: List[tuple] = field(default_factory=list)
    backtrack_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'action': self.action,
            'action_value': self.action_value,
            'action_metadata': self.action_metadata,
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
            'initial_quadrant': self.initial_quadrant,
            'algorithm_name': self.algorithm_name,
            'algorithms_history': self.algorithms_history,
            'quadrant_transitions': self.quadrant_transitions,
            'backtrack_count': self.backtrack_count,
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
        self.blackboard = blackboard or Blackboard(
            slot_registry=SLOT_DEFINITIONS if _SLOT_REGISTRY_AVAILABLE else None
        )
        self.epistemic_tracker = EpistemicTracker()
        self.hysteresis = HysteresisManager() if self.config.use_hysteresis else None

        # Meta-planner for algorithm selection
        self.meta_planner = MetaPlanner() if self.config.use_meta_planner_cache else None

        # Catastrophic fallback
        self.fallback = CatastrophicFallback() if self.config.use_catastrophic_fallback else None

        # Precomputation manager
        self.precomputation = PrecomputationManager()
        self._precomputed_data: Optional[PrecomputedData] = None

        # Phase 8: Eisenhower Layer for urgency x importance prioritization
        self.eisenhower = EisenhowerLayer(self.blackboard)

        # Phase 9: Phenomenology Layer for compressed state feedback
        self.phenomenology = PhenomenologyLayer(self.blackboard)

        # Phase 7+11: Graph Evolution for edge trust and crystallization
        # Tracks traversals with FeltState context for intelligent path learning
        self.graph_evolution = _GraphEvolution() if _GRAPH_EVOLUTION_AVAILABLE else None

        # H41: Rung affinity model for learned priority boosting
        self.rung_affinity: Optional[Any] = None

        # Phase 12: Path Crystallization for shortcutting known-good paths
        self.path_crystallizer: Optional[Any] = None
        try:
            from engines.cognition.path_crystallization import PathCrystallizer
            self.path_crystallizer = PathCrystallizer()
        except ImportError:
            pass

        # Phase 6: Question Manager for KU question lifecycle
        self.question_manager = QuestionManager() if _QUESTION_MANAGER_AVAILABLE else None

        # Phase 5: Routing Metrics for decision-level telemetry
        self.metrics_tracker = RoutingMetricsTracker() if _ROUTING_METRICS_AVAILABLE else None

        # Phase 6: Epistemic Logger (created per-game in initialize())
        self.epistemic_logger: Optional[Any] = None

        # Phase 6: UK Potential Index for bloom-filter knowledge checks
        self.uk_index = UKPotentialIndex() if _UK_INDEX_AVAILABLE else None

        # Phase 7.4: Process Knowledge Extractor for transfer learning
        self.process_knowledge = ProcessKnowledgeExtractor() if _PROCESS_KNOWLEDGE_AVAILABLE else None

        # Phase 7+11: FeelTrajectoryStore for game-level anomaly detection
        self.feel_trajectory_store = FeelTrajectoryStore() if _FEEL_TRAJECTORY_AVAILABLE else None

        # Parameter history snapshot at init
        if _PARAM_HISTORY_AVAILABLE and PARAMETER_HISTORY is not None:
            PARAMETER_HISTORY.snapshot("router_init", CognitiveParameters())

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

        # Phase 0.2: Epistemic signal quality tracking
        # Counts genuine (from resolved_questions) vs synthetic (from confidence)
        self._genuine_epistemic_signals = 0
        self._synthetic_epistemic_signals = 0

    # -------------------------------------------------------------------------
    # Phase 0.2: Epistemic ratio persistence
    # -------------------------------------------------------------------------

    def get_epistemic_signal_ratio(self) -> Dict[str, Any]:
        """Return genuine vs synthetic epistemic signal counts and ratio."""
        total = self._genuine_epistemic_signals + self._synthetic_epistemic_signals
        return {
            'genuine': self._genuine_epistemic_signals,
            'synthetic': self._synthetic_epistemic_signals,
            'total': total,
            'genuine_ratio': (
                self._genuine_epistemic_signals / total if total > 0 else 0.0
            ),
        }

    def persist_epistemic_ratio(self) -> None:
        """Log genuine/synthetic ratio via standard logger (goes to system_logs via DatabaseLogHandler).

        Call at end-of-game or generation boundary so the ratio is persisted
        in the database without requiring a dedicated table.
        """
        stats = self.get_epistemic_signal_ratio()
        if stats['total'] > 0:
            logger.info(
                "[EPISTEMIC-RATIO] game=%s genuine=%d synthetic=%d ratio=%.2f",
                self._game_id,
                stats['genuine'],
                stats['synthetic'],
                stats['genuine_ratio'],
            )
        # Reset counters for next game / generation
        self._genuine_epistemic_signals = 0
        self._synthetic_epistemic_signals = 0

        # Game context
        self._game_id = ""
        self._decision_id = 0
        self._last_decision_confidence = 0.0  # For confidence_delta tracking

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
        self.blackboard = Blackboard(
            slot_registry=SLOT_DEFINITIONS if _SLOT_REGISTRY_AVAILABLE else None
        )
        self.eisenhower = EisenhowerLayer(self.blackboard)  # Recreate with new blackboard
        self.phenomenology = PhenomenologyLayer(self.blackboard)  # Recreate with new blackboard
        self.epistemic_tracker.hard_reset()  # Full reset between games (different rules)
        if self.hysteresis:
            self.hysteresis.reset()
        if self.question_manager:
            self.question_manager.reset()
        if self.uk_index:
            self.uk_index.reset()

        # Phase 6: Create per-game epistemic logger
        if _EPISTEMIC_LOGGER_AVAILABLE:
            self.epistemic_logger = EpistemicLogger(game_id=game_id)

        # Phase 6: Populate UK index for this game
        if self.uk_index:
            game_type = ""  # Will be set from context later
            self.uk_index.populate_for_game(game_id, game_type)

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
        # NOTE: hysteresis is NOT reset per-decision -- signals accumulate
        # across decisions within a game. Game-level reset happens in
        # initialize(). This allows transition momentum to build.
        if self.fallback:
            self.fallback.reset(self._game_id, self._decision_id)

        # Update blackboard from game state
        self._update_blackboard_from_game_state(game_state)

        # Create initial search context
        context = self._create_search_context()

        # Initial algorithm selection happens inside _decision_loop
        # after phenomenology modulation is computed (Phase 9)
        quadrant = self.epistemic_tracker.current_state.primary_quadrant
        self._initial_quadrant = quadrant  # Save for DecisionResult
        # Bridge initial quadrant to blackboard for phenomenology/eisenhower
        self.blackboard.slot('epistemic_quadrant', quadrant.name)
        self._switch_algorithm(quadrant.name, context)
        # Pre-satisfy cooldown so the initial algorithm can be switched
        # immediately if a transition fires in the first iteration.
        self._state.iterations_since_switch = self.config.algorithm_switch_cooldown

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

        Phase 8 enhancement: Eisenhower layer gates each rung execution with
        urgency x importance evaluation. Queue aging can promote Q2 tasks.

        Phase 9 enhancement: Phenomenology layer compresses state to FeltState
        and feeds it back into the blackboard, creating a consciousness-like loop.
        """
        algorithm_switches = 0

        # Snapshot Eisenhower sparsity BEFORE the loop.  This ensures the
        # guard stays stable for the entire decision — rung evaluations that
        # write to the blackboard mid-loop cannot flip the guard and cause
        # subsequent candidates to be Q4_ELIMINATE'd.
        self.eisenhower.snapshot_sparsity()

        # Phase 9: Compress previous state and inject (phenomenology feedback)
        # This creates the High-D → Compress → Summary → Feed back loop
        felt = self.phenomenology.compress()
        self.phenomenology.inject(felt)

        # Phase 9: Get algorithm modulation from felt state
        # This is where 'feeling' becomes actionable
        modulation = self.phenomenology.get_algorithm_modulation(felt)

        # Phase 9: Re-apply modulation to initial algorithm selection
        # (Initial switch happened in decide() before modulation was available)
        if modulation and (modulation.algorithm_override or modulation.exploration_boost > 0
                           or modulation.exclusion_set or modulation.beam_width_multiplier != 1.0):
            self._switch_algorithm(
                self._state.current_algorithm_name, context, modulation=modulation
            )

        # Phase 8: Age scheduled queue at start of cycle
        # This can promote Q2 tasks to Q1 through urgency increase
        self.eisenhower.age_scheduled_queue()

        # Check for tasks promoted via aging
        promoted = self.eisenhower.pop_promoted_task()
        if promoted:
            logger.debug(f"[ROUTER] Executing promoted task from aging: {promoted}")
            result = self._execute_rung(promoted, game_state, rung_executor)
            # Process the result normally below

        # Phase 12: Check for crystallized path shortcut
        # If a reliable path exists for this domain, execute it directly
        # instead of running the full search loop
        if self.path_crystallizer and rung_executor:
            domain = game_state.get('domain', game_state.get('game_type', ''))
            if domain:
                crystallized = self.path_crystallizer.get_crystallized_path(domain)
                if crystallized:
                    logger.info(
                        f"[ROUTER] Using crystallized path for {domain}: "
                        f"{len(crystallized)} rungs"
                    )
                    last_result = None
                    for rung_name in crystallized:
                        last_result = self._execute_rung(
                            rung_name, game_state, rung_executor
                        )
                        self._state.path.append(rung_name)
                        if last_result and last_result.confidence >= self.config.commit_threshold:
                            return self._commit_decision(last_result)
                    # If crystallized path didn't commit, fall through to search

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
                break  # No more rungs - exit loop, use best so far

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
                break  # Algorithm returned nothing - exit loop

            # =================================================================
            # H41: AFFINITY-DRIVEN RUNG BOOST (replaces hardcoded click boost)
            # Uses learned rung affinities from solver imitation to boost
            # high-affinity rungs for the current game type. Falls back to
            # hardcoded click boost when no affinity data exists yet.
            # =================================================================
            next_rungs_set = set(next_rungs)
            game_type = game_state.get('game_type', '')
            affinity_boosted = False

            if self.rung_affinity and game_type:
                boost_rungs = self.rung_affinity.get_boost_rungs(game_type)
                if boost_rungs:
                    missing_boost = [
                        r for r in boost_rungs
                        if r in frontier and r not in next_rungs_set
                    ]
                    if missing_boost:
                        next_rungs = missing_boost + list(next_rungs)
                        affinity_boosted = True

            # Fallback: hardcoded click-game boost (pre-H41 behavior)
            if not affinity_boosted:
                available_actions = list(game_state.get('available_actions', []))
                if available_actions == [6]:
                    _CLICK_BOOST_RUNGS = frozenset({
                        'causal_click_mapping', 'constraint_satisfaction',
                        'constraint_decoder', 'object_color_targeting',
                        'click_behavior_learning', 'action6_object_exploration',
                    })
                    missing_click_rungs = [
                        r for r in _CLICK_BOOST_RUNGS
                        if r in frontier and r not in next_rungs_set
                    ]
                    if missing_click_rungs:
                        next_rungs = missing_click_rungs + list(next_rungs)

            # =================================================================
            # BATCH EVALUATION: Evaluate top-K candidates in one pass
            # Architecture target: O(26) typical via focused search.
            # Each iteration evaluates a batch of K candidates (default 5),
            # checks for action agreement within the batch, and commits
            # if agreement found. This replaces the old 1-rung-per-iter
            # approach that brute-forced all 50 rungs in O(V) linear scan.
            # =================================================================
            batch_results = []  # (rung_name, result) pairs for this iteration

            for candidate in next_rungs:
                # Phase 8: Eisenhower gate - evaluate urgency x importance
                edge_trust = self._get_edge_trust(candidate)
                quadrant, action = self.eisenhower.gate_single_rung(candidate, edge_trust)

                if quadrant == EisenhowerQuadrant.Q4_ELIMINATE:
                    continue  # Skip useless rungs
                elif quadrant == EisenhowerQuadrant.Q2_SCHEDULE:
                    continue  # Queue for later, try next in batch

                # Q1_DO or Q3_DELEGATE: execute this rung
                rung_name = action
                result = self._execute_rung(rung_name, game_state, rung_executor)

                # Record traversal for graph evolution
                if self.graph_evolution and len(self._state.path) > 0:
                    prev_rung = self._state.path[-1]
                    self.graph_evolution.record_traversal(
                        from_rung=prev_rung,
                        to_rung=rung_name,
                        success=result.confidence > 0.5,
                        felt_state=felt
                    )

                # Update visited state
                self._state.path.append(rung_name)
                self._state.visited_rungs.add(rung_name)
                context.visited_rungs.add(rung_name)
                context.current_path.append(rung_name)

                # Track best result (any confidence)
                if result.confidence > self._state.max_confidence:
                    self._state.max_confidence = result.confidence
                    self._state.best_result = result

                # Track best ACTIONABLE result separately.
                # Rungs like survey/filters produce confidence but no ACTION.
                # Without this, finalize returns a non-actionable rung and
                # the caller falls back to random — wasting SmartActionSelection.
                is_actionable = (
                    isinstance(result.value, str)
                    and result.value.startswith('ACTION')
                )
                if is_actionable and result.confidence > self._state.max_actionable_confidence:
                    self._state.max_actionable_confidence = result.confidence
                    self._state.best_actionable_result = result

                batch_results.append((rung_name, result))

                # Epistemic update (MUST happen for learning)
                transitions = self.epistemic_tracker.update_from_rung_result(
                    rung_name=rung_name,
                    result=result,
                    blackboard=self.blackboard,
                    all_rungs=self._all_rungs,
                    visited_rungs=self._state.visited_rungs
                )

                # Bridge live epistemic quadrant to blackboard so
                # Phenomenology / Eisenhower see the real quadrant,
                # not the 'UU' default.
                current_q = self.epistemic_tracker.current_state.primary_quadrant
                self.blackboard.slot('epistemic_quadrant', current_q.name)

                # Bridge contradiction signal from rung result to blackboard
                # so Phenomenology THREAT detection can fire.
                if getattr(result, 'contradiction_detected', False):
                    self.blackboard.slot('contradiction_detected', True)

                # Dead-signal fix: Bridge surprise_level from rung result
                # to 'surprise_score' for Phenomenology salience computation.
                rung_surprise = getattr(result, 'surprise_level', 0.0)
                if rung_surprise > 0:
                    # Use max so the highest surprise in a batch persists
                    prev_surprise = self.blackboard.get('surprise_score', 0.0)
                    self.blackboard.slot(
                        'surprise_score', max(prev_surprise, rung_surprise)
                    )

                # Dead-signal fix: Derive 'pattern_break' for Phenomenology.
                # A pattern break = frame was static for 3+ frames then changed,
                # OR score suddenly shifted. Signals "something new happened".
                no_change = self.blackboard.get('no_change_frames', 0)
                frame_just_changed = self.blackboard.get('frame_changed', False)
                if frame_just_changed and no_change == 0:
                    # Frame changed after being tracked — check if the prior
                    # streak was long enough to count as a break.
                    prev_streak = self.blackboard.get('_prev_no_change_streak', 0)
                    if prev_streak >= 3:
                        self.blackboard.slot('pattern_break', True)
                elif no_change >= 3 and not self.blackboard.get('pattern_break', False):
                    # Currently in a long static stretch — not a break yet
                    self.blackboard.slot('_prev_no_change_streak', no_change)

                # Handle transitions (algorithm switching, etc.)
                for transition in transitions:
                    self._state.transitions.append(transition)
                    # Save checkpoint at every transition boundary so
                    # backtracking has a restore point. Without this,
                    # self._state.checkpoints is always empty and the
                    # backtrack path at KK->KU never fires.
                    self._state.checkpoints.append({
                        "path": self._state.path.copy(),
                        "visited": self._state.visited_rungs.copy(),
                        "confidence": self._state.max_confidence,
                    })
                    if self.hysteresis:
                        should_switch = self.hysteresis.record_signal(
                            transition.from_quadrant,
                            transition.to_quadrant
                        )
                        if not should_switch:
                            continue
                    if self._state.iterations_since_switch < self.config.algorithm_switch_cooldown:
                        continue
                    response = get_algorithm_for_transition(transition)
                    if response.action == "backtrack" and self._state.checkpoints:
                        self._handle_backtrack(context, response.params)
                    elif response.action == "reset":
                        self._handle_reset(context, response.params)
                    if response.algorithm != self._state.current_algorithm_name:
                        self._switch_algorithm(response.algorithm, context, response.params, modulation=modulation)
                        algorithm_switches += 1
                        self._state.iterations_since_switch = 0
                    if self.fallback:
                        self.fallback.record_quadrant(
                            transition.to_quadrant.name,
                            self._state.max_confidence
                        )
                        if transition.is_regression:
                            self.fallback.record_contradiction()

            # Record one iteration for catastrophic fallback tracking.
            # This is per outer-loop iteration (not per-rung) so the
            # max_iterations threshold counts decision cycles, not the
            # 5x-inflated rung evaluation count.
            if self.fallback and batch_results:
                self.fallback.record_iteration(batch_results[-1][0])

            # =================================================================
            # AGREEMENT CHECK: Look for action consensus within the batch
            # If 2+ rungs in the batch produced the same ACTION, boost
            # confidence and commit. This is meaningful cognitive agreement
            # between independent evaluation units, not random coincidence.
            # =================================================================
            action_votes = {}  # ACTION string -> list of (rung_name, result)
            for rung_name, result in batch_results:
                if (result.value and isinstance(result.value, str)
                        and result.value.startswith('ACTION')):
                    action_votes.setdefault(result.value, []).append((rung_name, result))

            # Find best agreement (most votes, then highest confidence)
            best_agreement = None
            best_agreement_conf = 0.0
            for action_str, voters in action_votes.items():
                if len(voters) >= 2:
                    # Agreement found! Use highest-confidence voter's result
                    best_voter = max(voters, key=lambda v: v[1].confidence)
                    agreement_boost = 0.15
                    boosted_conf = min(1.0, best_voter[1].confidence + agreement_boost)
                    if boosted_conf > best_agreement_conf:
                        best_agreement = best_voter
                        best_agreement_conf = boosted_conf

            if best_agreement:
                rung_name, orig_result = best_agreement
                # Create boosted result for commitment
                boosted_result = RungResult(
                    rung_name=rung_name,
                    slot_name=orig_result.slot_name,
                    value=orig_result.value,
                    confidence=best_agreement_conf,
                    raises_questions=getattr(orig_result, 'raises_questions', []),
                    answers_questions=getattr(orig_result, 'answers_questions', []),
                    surprise_level=getattr(orig_result, 'surprise_level', 0.0),
                    contradiction_detected=getattr(orig_result, 'contradiction_detected', False),
                    contradiction_with=getattr(orig_result, 'contradiction_with', None),
                )
                self._state.max_confidence = best_agreement_conf
                self._state.best_result = boosted_result

                # Check commit threshold
                quadrant = self.epistemic_tracker.current_state.primary_quadrant
                if quadrant == RumsfeldQuadrant.UU:
                    # UU: Use base threshold so anti-monopoly-capped rungs
                    # (0.55) can still commit. Agreement boost (+0.15)
                    # provides quality signal on top.
                    effective_threshold = self.config.commit_threshold
                else:
                    # KK/KU/UK: Agreement easily clears base threshold
                    effective_threshold = self.config.commit_threshold

                if best_agreement_conf >= effective_threshold:
                    return self._commit_decision(boosted_result)

            # No agreement in batch - check if any single result crossed
            # the threshold (e.g., from external validation like score_delta)
            #
            # ACTIONABILITY GUARD: Only commit if the candidate produces a
            # valid ACTION string.  Non-actionable rungs (survey, filters,
            # or network_sharing with a malformed key) must NOT terminate
            # the search — doing so blocks genuinely actionable rungs from
            # ever being evaluated.
            commit_candidate = (
                self._state.best_actionable_result
                or self._state.best_result
            )
            if commit_candidate:
                candidate_is_actionable = (
                    isinstance(commit_candidate.value, str)
                    and commit_candidate.value.startswith('ACTION')
                )
                quadrant = self.epistemic_tracker.current_state.primary_quadrant
                if quadrant == RumsfeldQuadrant.UU:
                    # UU: Use base threshold so anti-monopoly-capped rungs
                    # (0.55) can commit. Prevents deadlock where cap < threshold.
                    effective_threshold = self.config.commit_threshold
                else:
                    # KK/KU/UK: Single confident rung (0.6) can commit
                    effective_threshold = self.config.commit_threshold

                if candidate_is_actionable and commit_candidate.confidence >= effective_threshold:
                    return self._commit_decision(commit_candidate)

            # Phase 6: Log epistemic state
            if self.epistemic_logger:
                active_q_count = (
                    len(self.question_manager.get_active_questions())
                    if self.question_manager else 0
                )
                uk_pot = (
                    self.uk_index.get_potential_score()
                    if self.uk_index and hasattr(self.uk_index, 'get_potential_score')
                    else 0.0
                )
                last_transition = self._state.transitions[-1] if self._state.transitions else None
                self.epistemic_logger.log_from_state(
                    tick=self._state.iteration,
                    state=self.epistemic_tracker.current_state,
                    transition=last_transition,
                    algorithm=self._state.current_algorithm_name,
                    thrashing_score=self.epistemic_tracker.get_thrashing_score()
                        if hasattr(self.epistemic_tracker, 'get_thrashing_score') else 0.0,
                    active_questions=active_q_count,
                    uk_potential=uk_pot,
                )

            # Phase 6: Raise questions from low-confidence batch results
            if self.question_manager:
                for rung_name, result in batch_results:
                    if result.confidence < 0.4:
                        self.question_manager.raise_question(
                            question_id=f"low_conf_{rung_name}_{self._state.iteration}",
                            text=f"Why did {rung_name} score only {result.confidence:.2f}?",
                            answerable_by=[rung_name],
                            raised_by=rung_name,
                            current_tick=self._state.iteration,
                            priority=0.3 + (0.4 - result.confidence),
                        )

            # Phase 7+11: Detect game-feel anomaly
            if self.feel_trajectory_store and _FEEL_TRAJECTORY_AVAILABLE and felt:
                progress = self._state.iteration / max(1, self.config.max_iterations)
                if progress < 0.3:
                    phase = 'opening'
                elif progress < 0.7:
                    phase = 'midgame'
                else:
                    phase = 'resolution'
                anomaly = self.feel_trajectory_store.detect_anomaly(
                    self._game_id, felt, phase
                )
                if anomaly:
                    logger.debug(
                        f"[ROUTER] Feel anomaly in {phase}: {anomaly.description}"
                    )
                    # ACT on the anomaly instead of just logging it.
                    # Inject signal into blackboard so downstream systems
                    # (Eisenhower, phenomenology, meta-planner) can react.
                    self.blackboard.write_with_valence(
                        'feel_anomaly_active', True,
                        valence=Valence.THREAT if anomaly.severity > 0.6 else Valence.CONFUSION,
                        urgency=min(1.0, anomaly.severity + 0.2),
                        importance=anomaly.severity,
                        reason=anomaly.description,
                        source_rung='feel_trajectory',
                    )
                    # Raise a high-priority question so the epistemic tracker
                    # can direct investigation toward the mismatch.
                    if self.question_manager:
                        self.question_manager.raise_question(
                            question_id=f"feel_anomaly_{phase}_{self._state.iteration}",
                            text=(
                                f"Feel anomaly in {phase}: expected "
                                f"{anomaly.expected_valence.value}, got "
                                f"{anomaly.actual_valence.value}"
                            ),
                            answerable_by=[],  # open question
                            raised_by='feel_trajectory',
                            current_tick=self._state.iteration,
                            priority=0.5 + anomaly.severity * 0.5,
                        )
                    # Severe anomaly: force exploration boost on next iteration
                    if anomaly.severity > 0.7:
                        visited_list = list(self._state.visited_rungs)
                        context.excluded_rungs.update(
                            visited_list[-3:]
                            if len(visited_list) >= 3
                            else visited_list
                        )

            # Update context
            context = self._update_search_context(context)
            self._state.iterations_since_switch += 1

            # Advance hysteresis tick so cooldowns can expire.
            # Without this, current_tick stays at 0 and cooldowns
            # (set to current_tick + N) become permanent lockouts.
            if self.hysteresis:
                self.hysteresis.tick()

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
        params: Optional[Dict[str, Any]] = None,
        modulation: Optional[AlgorithmModulation] = None
    ) -> None:
        """
        Switch to a new algorithm.

        Args:
            algorithm_name: Name of algorithm to switch to
            context: Current search context
            params: Additional parameters for algorithm
            modulation: Phase 9 modulation from phenomenology layer
        """
        params = params or {}

        # Phase 9: Apply phenomenology modulation if provided
        if modulation:
            # Algorithm override from FeltState (e.g., panic mode)
            if modulation.algorithm_override:
                algorithm_name = modulation.algorithm_override
                logger.debug(
                    f"[ROUTER] Phenomenology override: {algorithm_name}"
                )

            # Apply exploration boost
            if modulation.exploration_boost > 0:
                params['exploration_bonus'] = params.get('exploration_bonus', 0) + modulation.exploration_boost

            # Apply exclusion set
            if modulation.exclusion_set:
                context.excluded_rungs.update(modulation.exclusion_set)

        # Use meta-planner for selection if available
        # CRITICAL: If phenomenology issued an algorithm override (panic, threat,
        # boredom), respect it. The felt state override is a higher-priority signal
        # than the meta-planner's epistemic-based selection.
        phenomenology_override_active = (
            modulation and modulation.algorithm_override is not None
        )
        if self.meta_planner and not phenomenology_override_active:
            selection = self.meta_planner.select_algorithm(context)
            if selection.algorithm:
                # SelectionResult.algorithm is a SearchAlgorithm instance
                algorithm_name = selection.algorithm.name
                # Note: SelectionResult doesn't have params, use provided ones

        # Get algorithm instance
        try:
            # Translate quadrant names (KK, KU, UK, UU) to algorithm names
            if algorithm_name in QUADRANT_ALGORITHMS:
                algorithm_name = QUADRANT_ALGORITHMS[algorithm_name]
            algorithm = get_algorithm(algorithm_name, **params)

            # Phase 9: Apply beam width modulation
            if modulation and modulation.beam_width_multiplier != 1.0:
                if hasattr(algorithm, 'beam_width'):
                    algorithm.beam_width = int(algorithm.beam_width * modulation.beam_width_multiplier)
                    logger.debug(
                        f"[ROUTER] Beam width adjusted to: {algorithm.beam_width}"
                    )

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
        synthetic result for testing. Always ensures the result is a
        proper cognitive RungResult (adapts legacy results if needed).
        """
        if rung_executor:
            result = rung_executor(rung_name, game_state)
            # Ensure we have a cognitive RungResult - adapt legacy if needed
            if result is None:
                return RungResult(rung_name=rung_name, confidence=0.0)
            if not hasattr(result, 'answers_questions'):
                # Legacy RungResult - adapt it with proper epistemic signals
                # CRITICAL FIX: The old adapter set surprise_level = 1 - confidence,
                # which inflated uu_estimate on every low-confidence result,
                # permanently trapping the router in UU quadrant.
                #
                # Fix: Derive epistemic signals from blackboard (external evidence)
                # rather than just rung confidence (internal). Per architecture:
                # "Balances internal signals with external validation."
                raw_confidence = getattr(result, 'confidence', 0.0)
                metadata = getattr(result, 'metadata', {}) or {}

                # Boost confidence when external evidence confirms the action
                frame_changed = self.blackboard.get('frame_changed', False)
                score_delta = self.blackboard.get('score_delta', 0.0)
                last_outcome = self.blackboard.get('last_outcome', 'neutral')

                adapted_confidence = raw_confidence
                if score_delta > 0:
                    # Score improved - strong external validation
                    adapted_confidence = max(adapted_confidence, 0.85)
                elif frame_changed and last_outcome == 'positive':
                    # Frame changed positively
                    adapted_confidence = max(adapted_confidence, 0.7)
                elif frame_changed:
                    # At least something happened
                    adapted_confidence = max(adapted_confidence, 0.4)

                # Surprise comes from UNEXPECTED changes, not low confidence
                # A routine low-confidence result is not surprising
                surprise = 0.0
                if score_delta < 0:
                    surprise = 0.4  # Unexpected regression
                elif last_outcome == 'death':
                    surprise = 0.6  # Unexpected death
                elif isinstance(metadata, dict) and metadata.get('contradiction_detected'):
                    surprise = 0.5  # Contradiction found

                # Phase 0.2: Transfer genuine resolved_questions from DRS
                # result into epistemic answers_questions. When present, the
                # epistemic tracker uses these for real KU->KK transitions
                # instead of synthesizing from confidence alone.
                genuine_answers = getattr(result, 'resolved_questions', []) or []

                # Track signal quality
                if genuine_answers:
                    self._genuine_epistemic_signals += 1
                else:
                    self._synthetic_epistemic_signals += 1

                return RungResult(
                    rung_name=rung_name,
                    slot_name=f"rung_{rung_name}",  # Enable KK accumulation
                    value=getattr(result, 'action', None),
                    confidence=adapted_confidence,
                    answers_questions=genuine_answers,
                    surprise_level=surprise,
                    contradiction_detected=metadata.get('contradiction_detected', False) if isinstance(metadata, dict) else False,
                )
            return result

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

        # Prefer best_actionable_result (has valid ACTION string) over
        # best_result.  Same logic as _finalize_decision.  Many rungs
        # (palette_detection, survey, filters) produce non-zero confidence
        # without suggesting an action.  Without this preference, the
        # caller always falls back to random action selection.
        action_value = None
        confidence = self._state.max_confidence
        if self._state.best_actionable_result:
            action_value = self._state.best_actionable_result.value
            action = self._state.best_actionable_result.rung_name
            confidence = self._state.best_actionable_result.confidence
        elif self._state.best_result:
            if isinstance(self._state.best_result.value, str) and self._state.best_result.value.startswith('ACTION'):
                action_value = self._state.best_result.value

        return DecisionResult(
            action=action,
            reasoning=f"Fallback triggered: {failure_type.value}",
            confidence=confidence,
            action_value=action_value,
            iterations=self._state.iteration,
            rungs_evaluated=len(self._state.visited_rungs),
            transitions_count=len(self._state.transitions),
            time_elapsed=time.perf_counter() - self._state.start_time,
            path=self._state.path,
            used_fallback=True,
            fallback_reason=failure_type.value,
            final_quadrant=self.epistemic_tracker.current_state.primary_quadrant.name,
            initial_quadrant=getattr(self, '_initial_quadrant', self.epistemic_tracker.current_state.primary_quadrant).name,
            algorithm_name=self._state.current_algorithm_name or "unknown",
            algorithms_history=list(self._algorithm_usage.keys()),
            quadrant_transitions=[
                (t.from_quadrant.name, t.to_quadrant.name)
                for t in self._state.transitions
            ],
            backtrack_count=sum(
                1 for t in self._state.transitions if t.is_regression
            ),
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
        """Commit to a decision based on high-confidence result.

        The result.value field carries the actual ACTION string (e.g., 'ACTION3')
        produced by the rung. This is set by the rung_executor closure in
        _decide_cognitive, which evaluates the legacy rung and captures its output.
        """
        domain = self.blackboard.get('domain', self.blackboard.get('game_type', ''))

        # Phase 12: Record successful path for crystallization
        if self.path_crystallizer and self._state.path:
            if domain:
                self.path_crystallizer.record_successful_path(
                    domain=domain,
                    path=list(self._state.path),
                    confidence=result.confidence,
                    ticks=self._state.iteration,
                )

        # Phase 7.4: Record successful path for process knowledge extraction
        if self.process_knowledge and self._state.path and domain:
            try:
                self.process_knowledge.record_success(domain, list(self._state.path))
            except Exception as pk_err:
                logger.debug(f"[ROUTER] Process knowledge record failed: {pk_err}")

        # Phase 5: Record decision metrics
        elapsed = time.perf_counter() - self._state.start_time
        if self.metrics_tracker:
            has_backtrack = any(
                t.is_regression for t in self._state.transitions
            ) if self._state.transitions else False
            contradictions = sum(
                1 for t in self._state.transitions if t.is_regression
            )
            self.metrics_tracker.record_decision(
                rungs_evaluated=len(self._state.visited_rungs),
                latency_ms=elapsed * 1000,
                first_win=(self._state.iteration == 1),
                backtracked=has_backtrack,
                contradictions_detected=contradictions,
                game_id=self._game_id,
                algorithm_used=self._state.current_algorithm_name or "unknown",
                quadrant=self.epistemic_tracker.current_state.primary_quadrant.name,
                used_fallback=False,
            )

        # Phase 6: Record question lifecycle — answered by committed rung
        if self.question_manager:
            for q in self.question_manager.get_questions_for_rung(result.rung_name):
                self.question_manager.record_attempt(
                    question_id=q.question_id,
                    succeeded=(result.confidence >= 0.6),
                    confidence=result.confidence,
                    answer_source=result.rung_name,
                    current_tick=self._state.iteration,
                )

        # Save confidence for next cycle's confidence_delta computation
        self._last_decision_confidence = result.confidence

        # Extract actual ACTION string from the rung result's value field
        action_value = None
        if isinstance(result.value, str) and result.value.startswith('ACTION'):
            action_value = result.value

        return DecisionResult(
            action=result.rung_name,
            reasoning=f"High confidence ({result.confidence:.2f}) from {result.rung_name}",
            confidence=result.confidence,
            action_value=action_value,
            iterations=self._state.iteration,
            rungs_evaluated=len(self._state.visited_rungs),
            transitions_count=len(self._state.transitions),
            time_elapsed=elapsed,
            path=self._state.path,
            final_quadrant=self.epistemic_tracker.current_state.primary_quadrant.name,
            initial_quadrant=getattr(self, '_initial_quadrant', self.epistemic_tracker.current_state.primary_quadrant).name,
            algorithm_name=self._state.current_algorithm_name or "unknown",
            algorithms_history=list(self._algorithm_usage.keys()),
            quadrant_transitions=[
                (t.from_quadrant.name, t.to_quadrant.name)
                for t in self._state.transitions
            ],
            backtrack_count=sum(
                1 for t in self._state.transitions if t.is_regression
            ),
        )

    def _finalize_decision(self, algorithm_switches: int) -> DecisionResult:
        """Finalize decision after loop ends."""
        action_value = None

        # Prefer best actionable result (has a valid ACTION string) over
        # best overall result. Many rungs (survey, filters) produce non-zero
        # confidence without suggesting an action. Without this preference,
        # finalize returns survey/filter rung names with action_value=None,
        # forcing the caller into random action selection every time.
        chosen_result = None
        if self._state.best_actionable_result:
            chosen_result = self._state.best_actionable_result
        elif self._state.best_result:
            chosen_result = self._state.best_result

        if chosen_result:
            action = chosen_result.rung_name
            confidence = chosen_result.confidence
            reasoning = f"Best result from {action} ({confidence:.2f})"
            # Extract actual ACTION string if available
            if isinstance(chosen_result.value, str) and chosen_result.value.startswith('ACTION'):
                action_value = chosen_result.value
        else:
            action = self._state.path[-1] if self._state.path else "survey"
            confidence = self._state.max_confidence
            reasoning = "Loop ended without high-confidence result"

        # Phase 5: Record decision metrics (non-committed path)
        elapsed = time.perf_counter() - self._state.start_time
        if self.metrics_tracker:
            has_backtrack = any(
                t.is_regression for t in self._state.transitions
            ) if self._state.transitions else False
            self.metrics_tracker.record_decision(
                rungs_evaluated=len(self._state.visited_rungs),
                latency_ms=elapsed * 1000,
                first_win=False,
                backtracked=has_backtrack,
                game_id=self._game_id,
                algorithm_used=self._state.current_algorithm_name or "unknown",
                quadrant=self.epistemic_tracker.current_state.primary_quadrant.name,
                used_fallback=False,
            )

        # Save confidence for next cycle's confidence_delta computation
        self._last_decision_confidence = confidence

        # Phase 6: Flush epistemic logger at decision end
        if self.epistemic_logger:
            try:
                self.epistemic_logger.flush()
            except Exception:
                pass  # Best-effort flush

        return DecisionResult(
            action=action,
            reasoning=reasoning,
            confidence=confidence,
            action_value=action_value,
            iterations=self._state.iteration,
            rungs_evaluated=len(self._state.visited_rungs),
            transitions_count=len(self._state.transitions),
            algorithm_switches=algorithm_switches,
            time_elapsed=elapsed,
            path=self._state.path,
            final_quadrant=self.epistemic_tracker.current_state.primary_quadrant.name,
            initial_quadrant=getattr(self, '_initial_quadrant', self.epistemic_tracker.current_state.primary_quadrant).name,
            algorithm_name=self._state.current_algorithm_name or "unknown",
            algorithms_history=list(self._algorithm_usage.keys()),
            quadrant_transitions=[
                (t.from_quadrant.name, t.to_quadrant.name)
                for t in self._state.transitions
            ],
            backtrack_count=sum(
                1 for t in self._state.transitions if t.is_regression
            ),
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
        """Update blackboard from game state.

        This bridges the context dict (populated by ContextBuilder) to the
        blackboard slots that cognitive components (Eisenhower, Phenomenology,
        Epistemic Tracker) expect. It handles:

        1. Direct pass-through of context keys -> blackboard slots
        2. Aliasing context keys to cognitive slot names where they differ
        3. Computing derived slots that cognitive components need
        """
        # Pass through all context keys (skip large data)
        # Use write_with_valence for critical slots so the valence store
        # populates aggregate urgency/importance for Eisenhower (Phase 10)
        for key, value in game_state.items():
            if key not in ('frame', 'raw_frame'):
                if key in CRITICAL_SLOT_VALENCE_RULES:
                    self.blackboard.write_with_valence(key, value)
                else:
                    self.blackboard.slot(key, value)

        # =====================================================================
        # ALIASING: Context keys -> Cognitive slot names
        # The context builder uses different names than cognitive components.
        #
        # DEAD SIGNAL AUDIT (2026-02-07): Phenomenology and Eisenhower read
        # ~20 blackboard keys that nothing ever wrote. This section bridges
        # the evolution_runner context dict to the slot names that cognitive
        # components expect. Without these bridges, phenomenology runs on
        # ~80% default values and its valence/arousal/certainty/agency/
        # salience outputs are systematically wrong.
        # =====================================================================

        # Reset ephemeral signals that are populated during the routing loop.
        # Without this, stale values from a previous decide() call persist
        # and phenomenology/eisenhower see old data.
        self.blackboard.slot('surprise_score', 0.0)
        self.blackboard.slot('pattern_break', False)
        self.blackboard.slot('feel_anomaly_active', False)
        self.blackboard.slot('contradiction_detected', False)

        # Eisenhower reads 'actions_taken' but context passes 'action_count'
        if 'action_count' in game_state and self.blackboard.get('actions_taken') is None:
            self.blackboard.slot('actions_taken', game_state['action_count'])

        # Phenomenology reads 'stuck_detected', context has 'recent_stuck_count'
        stuck_count = game_state.get('recent_stuck_count', 0)
        if stuck_count > 0:
            self.blackboard.slot('stuck_detected', True)

        # Phenomenology reads 'death_count', derive from last_outcome history
        last_outcome = game_state.get('last_outcome', 'neutral')
        death_count = self.blackboard.get('death_count', 0)
        if last_outcome == 'death':
            death_count += 1
        self.blackboard.slot('death_count', death_count)

        # Phenomenology reads 'recent_success_rate', derive from frame_changed
        frame_changed = game_state.get('frame_changed', False)
        _success_window = self.blackboard.get('_success_window', [])
        _success_window.append(1.0 if frame_changed else 0.0)
        if len(_success_window) > 20:
            _success_window = _success_window[-20:]
        self.blackboard.slot('_success_window', _success_window)
        if _success_window:
            self.blackboard.slot(
                'recent_success_rate',
                sum(_success_window) / len(_success_window)
            )

        # Phenomenology reads 'no_change_frames', track consecutive no-change
        no_change = self.blackboard.get('no_change_frames', 0)
        if not frame_changed:
            no_change += 1
        else:
            no_change = 0
        self.blackboard.slot('no_change_frames', no_change)

        # Phenomenology reads 'frame_delta_magnitude'
        # Approximate from frame_changed + score_delta
        score_delta_raw = game_state.get('score_delta', 0)
        magnitude = abs(score_delta_raw) * 10 if frame_changed else 0
        self.blackboard.slot('frame_delta_magnitude', magnitude)

        # Eisenhower reads 'action_budget' for budget calculations
        action_budget = game_state.get('action_budget', 400)
        self.blackboard.slot('action_budget', action_budget)

        # Phenomenology reads 'controlled_object' for agency computation.
        # Dead-signal fix: Bridge from context. The evolution_runner passes
        # 'player_position' from player_localizer. If we have a real
        # localization (not the default sentinel), an object was detected.
        # Also accept 'controlled_object' if the context already has one
        # (e.g., from control_tracker integration).
        if self.blackboard.get('controlled_object') is None:
            controlled = game_state.get('controlled_object')
            if controlled is None:
                # Derive from player_position: default (32,32) is sentinel
                pos = game_state.get('player_position')
                if pos is not None and tuple(pos) != (32, 32):
                    controlled = f"player_at_{pos[0]}_{pos[1]}"
            if controlled is not None:
                self.blackboard.slot('controlled_object', controlled)

        # Phenomenology reads 'open_questions' - bridge from question_manager
        if self.question_manager:
            active_qs = self.question_manager.get_active_questions()
            self.blackboard.slot('open_questions', active_qs)

        # Phenomenology reads 'contradiction_detected' - initialise from
        # last_outcome; will be updated live from rung results in the loop
        if last_outcome == 'death':
            self.blackboard.slot('contradiction_detected', True)

        # Phenomenology reads 'cascade_failure' for THREAT valence.
        # A cascade failure = multiple negative signals simultaneously:
        # death + stuck + high budget pressure = system is failing broadly.
        is_cascade = (
            last_outcome == 'death'
            and stuck_count > 0
            and game_state.get('action_count', 0) > game_state.get('action_budget', 400) * 0.5
        )
        self.blackboard.slot('cascade_failure', is_cascade)

        # Phenomenology reads 'recent_path' for THREAT exclusion modulation.
        # Bridge from visited_rungs so the exclusion set has real data.
        if hasattr(self, '_state') and self._state.visited_rungs:
            self.blackboard.slot('recent_path', list(self._state.visited_rungs))

        # =====================================================================
        # DERIVED SLOTS: Computed from raw context for cognitive components
        # =====================================================================

        # Budget pressure as a fraction (for phenomenology)
        action_budget = game_state.get('action_budget', 400)
        action_count = game_state.get('action_count', 0)
        if action_budget > 0:
            budget_pressure = action_count / action_budget
            self.blackboard.slot('budget_pressure', budget_pressure)
            # Flag critical budget for phenomenology THREAT detection
            if budget_pressure > 0.85:
                self.blackboard.write_with_valence('action_budget_critical', True)

        # Level progress for phenomenology external validation
        levels_completed = game_state.get('levels_completed', 0)
        total_levels = game_state.get('total_levels', 1)
        if total_levels > 0:
            self.blackboard.slot('level_progress', levels_completed / total_levels)

        # Score tracking for phenomenology
        current_score = game_state.get('current_score', 0)
        previous_score = self.blackboard.get('_prev_score', 0)
        score_delta = current_score - previous_score
        self.blackboard.slot('score_delta', score_delta)
        self.blackboard.slot('_prev_score', current_score)

        # Dead-signal fix: Bridge active_sequence to cached_sequence_* slots.
        # Eisenhower Q3_DELEGATE reads cached_sequence_{rung_name} to shortcut
        # rung execution when a winning sequence already exists. The context
        # passes active_sequence (full winning sequence) and sequence_position.
        # When available, we store the remaining actions as the cached sequence
        # keyed by a generic rung name so ANY rung can be delegated via it.
        active_seq = game_state.get('active_sequence') or []
        seq_pos = game_state.get('sequence_position', 0)
        if len(active_seq) > 0 and seq_pos < len(active_seq):
            remaining = active_seq[seq_pos:]
            # Convert int actions to ACTION strings for rung compatibility
            remaining_actions = [
                f"ACTION{a}" if isinstance(a, int) else a for a in remaining
            ]
            # Write as a generic cached_sequence that any Q3_DELEGATE rung
            # can use. Eisenhower reads cached_sequence_{rung_name}, so we
            # populate a wildcard entry under the key 'cached_sequence_replay'.
            self.blackboard.slot('cached_sequence_replay', remaining_actions)
            # Also set per-rung entries for common replay-relevant rungs
            # so the exact key Eisenhower looks up has data.
            for rung in ('survey', 'exploration_phase', 'random_walk',
                         'action_repeater', 'landmark_navigator'):
                self.blackboard.slot(f'cached_sequence_{rung}', remaining_actions)

        # =====================================================================
        # EPISTEMIC SIGNAL ENRICHMENT
        # Bridge game-state evidence into epistemic-compatible signals.
        # Without these, the epistemic tracker stays in UU permanently
        # because legacy rungs never produce slot_name or questions.
        # =====================================================================
        frame_changed = game_state.get('frame_changed', False)
        last_outcome = game_state.get('last_outcome', 'neutral')

        # Track consecutive productive actions (frame changes that matter)
        productive_streak = self.blackboard.get('_productive_streak', 0)
        if frame_changed and score_delta >= 0:
            productive_streak += 1
        else:
            productive_streak = max(0, productive_streak - 1)
        self.blackboard.slot('_productive_streak', productive_streak)

        # Write working_theory slot based on game progress.
        # CRITICAL: Phenomenology and Eisenhower read 'working_theory',
        # NOT 'working_theory_confirmed'. Write BOTH for backward compat.
        if levels_completed > 0:
            theory_conf = min(1.0, 0.5 + levels_completed * 0.15)
            self.blackboard.slot(
                'working_theory', f'level_{levels_completed}_cleared',
                confidence=theory_conf,
                source_rung='game_evidence'
            )
            self.blackboard.slot(
                'working_theory_confirmed', True,
                confidence=theory_conf,
                source_rung='game_evidence'
            )

        # Confidence delta for phenomenology valence computation.
        # Track how confidence is trending across decisions.
        prev_conf = self.blackboard.get('_prev_confidence', 0.0)
        # Use best result confidence from previous decision if available
        current_conf = getattr(self, '_last_decision_confidence', prev_conf)
        self.blackboard.slot('confidence_delta', current_conf - prev_conf)
        self.blackboard.slot('_prev_confidence', current_conf)

        # Novelty detection for phenomenology salience
        if score_delta > 0:
            self.blackboard.slot('novelty_score', 0.8, source_rung='game_evidence')
        elif frame_changed:
            self.blackboard.slot('novelty_score', 0.3, source_rung='game_evidence')

        # Strategy stability signal
        if productive_streak > 5:
            self.blackboard.slot('strategy_stability', 0.8, source_rung='game_evidence')

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
        """Build graph info for algorithm.

        Includes visit_counts from current decision so the algorithm's
        exploration bonus (UCB) can differentiate between visited and
        unvisited rungs. Without this, every rung has visit_count=0 and
        the exploration term is identical for all candidates.

        Also injects known_rungs from the epistemic tracker so that
        algorithms (especially GreedyBestFirst in KK) can prioritize
        rungs proven to produce high-confidence results. Without this,
        every rung scores ~0.3 default and KK wastes 35+ iterations.
        """
        # Build visit counts from current decision's visited rungs
        visit_counts = {}
        for rung_name in self._state.path:
            visit_counts[rung_name] = visit_counts.get(rung_name, 0) + 1

        # Extract proven rungs from epistemic known_knowns
        # Maps rung_name -> max confidence from any fact it produced
        known_rungs: Dict[str, float] = {}
        for fact in self.epistemic_tracker.current_state.known_knowns.values():
            rung = fact.source_rung
            if rung:
                known_rungs[rung] = max(
                    known_rungs.get(rung, 0.0), fact.confidence
                )

        if self._precomputed_data:
            return {
                'nodes': self._nodes,
                'edges': self._edges,
                'reverse_edges': self._precomputed_data.reverse_edges,
                'is_dag': self._precomputed_data.is_dag,
                'topological_order': self._precomputed_data.topological_order,
                'visit_counts': visit_counts,
                'known_rungs': known_rungs,
                'max_rungs_per_call': self.config.max_rungs_per_call,
            }
        return {
            'nodes': self._nodes,
            'edges': self._edges,
            'reverse_edges': {},
            'is_dag': False,
            'topological_order': [],
            'visit_counts': visit_counts,
            'known_rungs': known_rungs,
            'max_rungs_per_call': self.config.max_rungs_per_call,
        }

    def _get_edge_trust(self, rung_name: str) -> float:
        """
        Get edge trust score for a rung from graph evolution.

        Edge trust represents historical success rate of traversals
        TO this rung. Used by Eisenhower layer for importance calculation.

        Priority order:
        1. Graph evolution (real learned trust from traversal history)
        2. Blackboard override (set by external systems)
        3. Node priority heuristic (from rung metadata)
        4. Neutral default (0.5)

        Args:
            rung_name: Name of the rung to get trust for

        Returns:
            Trust score 0.0-1.0 (default 0.5 if unknown)
        """
        # Priority 1: Graph evolution with real traversal data
        if self.graph_evolution and self._state.path:
            prev_rung = self._state.path[-1]
            trust = self.graph_evolution.get_edge_trust(prev_rung, rung_name)
            if trust > 0.0:  # 0.0 means no data, not low trust
                return trust

        # Priority 2: Blackboard override (set by external systems)
        edge_trust = self.blackboard.get(f'edge_trust_{rung_name}')
        if edge_trust is not None:
            return float(edge_trust)

        # Priority 3: Node priority heuristic
        if self._precomputed_data:
            node_info = self._nodes.get(rung_name, {})
            priority = node_info.get('priority', 50)
            # Convert priority (0=highest, 100=lowest) to trust (0-1)
            # Lower priority number = higher trust
            return max(0.1, 1.0 - priority / 100.0)

        # Priority 4: Neutral default
        return 0.5

    # -------------------------------------------------------------------------
    # MUTATION PROCESSING
    # -------------------------------------------------------------------------

    def _process_mutations(self, context: SearchContext) -> None:
        """Process mutation requests from algorithms."""
        mutations = context.get_pending_mutations()
        # get_pending_mutations() already clears the list internally

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
        stats: Dict[str, Any] = {
            'total_decisions': self._total_decisions,
            'total_fallbacks': self._total_fallbacks,
            'fallback_rate': self._total_fallbacks / max(1, self._total_decisions),
            'algorithm_usage': dict(self._algorithm_usage),
            'game_id': self._game_id,
            # Phase 8: Eisenhower layer stats
            'eisenhower': self.eisenhower.get_stats(),
            'eisenhower_scheduled_queue': self.eisenhower.get_scheduled_queue_summary(),
            # Phase 9: Phenomenology layer stats
            'phenomenology': self.phenomenology.get_stats(),
            'current_felt_state': (
                self.phenomenology.previous_felt.to_dict()
                if self.phenomenology.previous_felt else None
            ),
            # Phase 7+11: Graph evolution stats
            'graph_evolution': {
                'total_edges': len(self.graph_evolution.edges) if self.graph_evolution else 0,
                'crystallized_edges': len(self.graph_evolution._crystallized_paths) if self.graph_evolution else 0,
            },
        }

        # Phase 5: Routing metrics summary
        if self.metrics_tracker:
            try:
                stats['routing_metrics'] = self.metrics_tracker.get_metrics()
            except Exception:
                stats['routing_metrics'] = {}

        # Phase 6: Question manager summary
        if self.question_manager:
            active = self.question_manager.get_active_questions()
            stats['question_manager'] = {
                'total_raised': self.question_manager._total_raised,
                'total_answered': self.question_manager._total_answered,
                'active_questions': len(active),
            }

        # Phase 6: Epistemic logger summary
        if self.epistemic_logger:
            try:
                stats['epistemic_logger'] = self.epistemic_logger.get_summary()
            except Exception:
                stats['epistemic_logger'] = {}

        # Phase 6: UK potential index
        if self.uk_index:
            stats['uk_index'] = {
                'game_id': self.uk_index._game_id,
                'entries': len(self.uk_index.index),
                'cold_start': self.uk_index._is_cold_start,
            }

        # Phase 7.4: Process knowledge
        if self.process_knowledge:
            stats['process_knowledge'] = {
                'total_paths_recorded': self.process_knowledge._total_paths_recorded,
                'unique_patterns': self.process_knowledge._unique_patterns_found,
            }

        # Phase 7+11: Feel trajectory store
        if self.feel_trajectory_store:
            stats['feel_trajectories'] = self.feel_trajectory_store.get_statistics()

        return stats

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
