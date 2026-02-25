"""
Decision Rung System - Modular Action Decision Architecture
============================================================

Allows swapping the order of decision features like LEGO bricks.
Each "rung" is a pluggable component with a standard interface.

Rung implementations live in the ``rungs/`` package, grouped by domain:
  - rungs/orientation.py   (15 rungs)
  - rungs/hypothesis.py    (16 rungs)
  - rungs/exploitation.py  (32 rungs)
  - rungs/filter_rungs.py  (11 rungs)
  - rungs/emergency.py     (2 rungs)
  - rungs/exploration.py   (2 rungs)

This file contains:
  - ORDERING_PRESETS      (static rung orderings, deprecated Phase 6)
  - DecisionRungSystem    (main orchestrator)
  - CoreGameplayAdapter   (integration bridge)

Usage:
    system = DecisionRungSystem(strategy='ladder')
    system.load_ordering('comprehensive')
    action, reason = system.decide(game_state, context)
"""

import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import json
import logging
import random
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple

# Set up logging with database support (Rule 2) + console output
try:
    from database_logger import setup_database_logging
    setup_database_logging(level='INFO')
    logger = logging.getLogger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('[%(name)s:%(levelname)s] %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

# ── Re-export everything from rungs package ──────────────────────────────────
# Backward compatibility: code importing from decision_rung_system still works.
from rungs import RUNG_REGISTRY  # noqa: F401
from rungs.base import (  # noqa: F401
    Action6CoordinateProvider,
    DecisionRung,
    DecisionStrategy,
    KnowledgeProvenance,
    RungResult,
    filter_available_actions,
    get_available_action_weights,
    get_available_actions_list,
    get_random_available_action,
    is_action_available,
    validate_action,
)

# ── Cognitive Router (lazy-load) ─────────────────────────────────────────────
_cognitive_router_loaded: bool = False
_CognitiveRouter: Any = None
_RungResult_Cognitive: Any = None


def _load_cognitive_router() -> Any:
    """Lazy-load cognitive router to avoid circular imports."""
    global _cognitive_router_loaded, _CognitiveRouter, _RungResult_Cognitive
    if _cognitive_router_loaded:
        return _CognitiveRouter

    try:
        from engines.cognition.cognitive_router import CognitiveRouter
        from engines.cognition.epistemic_tracker import (
            RungResult as RungResultCognitive,
        )
        _CognitiveRouter = CognitiveRouter
        _RungResult_Cognitive = RungResultCognitive
        _cognitive_router_loaded = True
        logger.debug("[RUNG-COGNITIVE] Loaded CognitiveRouter")
    except ImportError as e:
        logger.debug(f"[RUNG-COGNITIVE] CognitiveRouter not available: {e}")
        _cognitive_router_loaded = True
        _CognitiveRouter = None
        _RungResult_Cognitive = None

    return _CognitiveRouter


if TYPE_CHECKING:
    from engines.registry import EngineRegistry

# ── Deprecation Tracking (Phase 6) ──────────────────────────────────────────
_deprecation_warned: Dict[str, bool] = {}


def _warn_ordering_deprecated(ordering_name: str, suppress_if_cognitive: bool = False) -> None:
    """Warn that static ORDERING_PRESETS are deprecated."""
    global _deprecation_warned

    if suppress_if_cognitive:
        return
    if ordering_name in _deprecation_warned:
        return
    _deprecation_warned[ordering_name] = True

    message = (
        f"ORDERING_PRESETS['{ordering_name}'] is deprecated as of Phase 6. "
        f"Use DecisionStrategy.COGNITIVE with CognitiveRouter for dynamic, "
        f"graph-based rung selection. Static orderings will be removed in v3.0. "
        f"See architecture/cognitive_routing_implementation_plan.md for migration guide."
    )
    warnings.warn(message, DeprecationWarning, stacklevel=3)
    logger.warning(f"[DEPRECATION] {message}")


# =============================================================================
# ORDERING PRESETS (DEPRECATED - Phase 6)
# =============================================================================

ORDERING_PRESETS = {
    # Current behavior - efficiency-optimized (15 rungs - core only)
    'efficiency': [
        ('infinite_loop_breaker', 1),
        ('coordinate_oscillation', 3),
        ('palette_detection', 3),
        ('frontier_checkpoint', 4),
        ('three_try_sequence', 5),
        ('discovery_exploitation', 10),
        ('death_avoidance', 15),
        ('prior_lessons', 16),
        ('terminal_pattern', 17),
        ('embedding_suggestion', 20),
        ('frontier_topology', 25),
        ('exploration_phase', 30),
        ('two_streams', 35),
        ('primitive_suggester', 40),
        ('network_wisdom', 45),
        ('smart_action_selection', 99),
    ],

    # LLM-optimal - understanding first (all rungs including wired metacognition)
    'llm_optimal': [
        ('infinite_loop_breaker', 1),
        ('coordinate_oscillation', 2),
        ('palette_detection', 3),
        ('self_trust_boost', 4),
        ('control_tracker', 5),
        ('budget_aware_planning', 5),
        ('affordance_detection', 6),
        ('imagination_budget', 6),
        ('breakthrough_budget', 6),
        ('regulatory_signal', 7),
        ('survey', 8),
        ('network_exploration_stats', 8),
        ('scientific_method', 10),
        ('questioning_engine', 12),
        ('frustration_detection', 14),
        ('two_streams', 16),
        ('i_thread', 18),
        ('metacognitive_prediction', 20),
        ('deliberation_system', 22),
        ('symbolic_tracker', 23),
        ('theory_gate', 24),
        ('belief_system', 25),
        ('hypothesis_system', 26),
        ('sensation_engine', 27),
        ('resonance_detector', 28),
        ('valence_goals', 29),
        ('network_wisdom', 30),
        ('death_avoidance', 32),
        ('terminal_pattern', 34),
        ('theory_contradiction', 35),
        ('metacognitive_elimination', 35),
        ('pariah_avoidance', 36),
        ('viral_package_weights', 37),
        ('three_layer_filter', 38),
        ('hypothesis_testing', 39),
        ('three_try_sequence', 40),
        ('rule_transfer', 41),
        ('discovery_exploitation', 42),
        ('trigger_sequences', 43),
        ('embedding_suggestion', 44),
        ('embedding_matcher', 45),
        ('multi_stage_matching', 46),
        ('primitive_suggester', 48),
        ('network_sharing', 49),
        ('replay_learning', 50),
        ('network_wisdom', 51),
        ('abstraction_templates', 54),
        ('few_shot_relations', 55),
        ('few_shot_invariants', 56),
        ('subgoal_planning', 58),
        ('visual_analyzer', 60),
        ('network_object_inventory', 62),
        ('action6_object_exploration', 64),
        ('click_behavior_learning', 65),
        ('causal_click_mapping', 66),
        ('constraint_satisfaction', 66),
        ('destructive_action_detection', 66),
        ('goal_relationship_modeling', 67),
        ('interactable_tile_discovery', 67),
        ('object_color_targeting', 66),
        ('wall_aware_navigation', 67),
        ('controlled_movement_planning', 67),
        ('spatial_map', 68),
        ('near_miss_analyzer', 68),
        ('completion_prediction', 68),
        ('frontier_topology', 70),
        ('map_intel_collision', 72),
        ('exploration_phase', 74),
        ('grid_exploration', 76),
        ('smart_action_selection', 99),
    ],

    # Human brain - parallel attention + fear interrupt
    'human_brain': [
        ('infinite_loop_breaker', 1),
        ('coordinate_oscillation', 2),
        ('palette_detection', 3),
        ('death_avoidance', 4),
        ('terminal_pattern', 5),
        ('survey', 6),
        ('embedding_suggestion', 8),
        ('network_wisdom', 10),
        ('pariah_avoidance', 12),
        ('metacognitive_elimination', 12),
        ('viral_package_weights', 13),
        ('exploration_phase', 14),
        ('scientific_method', 20),
        ('theory_gate', 22),
        ('metacognitive_prediction', 24),
        ('i_thread', 26),
        ('two_streams', 28),
        ('sensation_engine', 30),
        ('primitive_suggester', 35),
        ('discovery_exploitation', 40),
        ('smart_action_selection', 99),
    ],

    # Full comprehensive ordering
    'comprehensive': [
        # EMERGENCY (Priority 1-5)
        ('infinite_loop_breaker', 1),
        ('coordinate_oscillation', 2),
        ('palette_detection', 3),
        ('sparse_grid', 3),
        ('self_trust_boost', 4),
        ('frame_interpretation', 5),
        # ORIENTATION (Priority 5-20)
        ('budget_aware_planning', 6),
        ('imagination_budget', 6),
        ('breakthrough_budget', 7),
        ('affordance_detection', 8),
        ('control_tracker', 8),
        ('wall_aware_navigation', 9),
        ('regulatory_signal', 10),
        ('survey', 11),
        ('network_exploration_stats', 12),
        ('questioning_engine', 13),
        ('exploration_phase', 13),
        ('frustration_detection', 14),
        # FILTER (Priority 15-25)
        ('contextual_failure', 15),
        ('metacognitive_elimination', 15),
        ('destructive_action_detection', 16),
        ('death_avoidance', 16),
        ('terminal_pattern', 17),
        ('theory_contradiction', 18),
        ('pariah_avoidance', 19),
        ('viral_package_weights', 20),
        ('three_layer_filter', 21),
        # HYPOTHESIS (Priority 25-40)
        ('event_understanding', 23),
        ('symbolic_tracker', 24),
        ('assumption_formation', 25),
        ('interactable_tile_discovery', 25),
        ('goal_relationship_modeling', 26),
        ('belief_system', 26),
        ('hypothesis_system', 27),
        ('scientific_method', 28),
        ('theory_gate', 29),
        ('metacognitive_prediction', 30),
        ('hypothesis_testing', 31),
        ('deliberation_system', 32),
        ('two_streams', 33),
        ('i_thread', 34),
        ('valence_goals', 35),
        ('sensation_engine', 36),
        ('resonance_detector', 37),
        # EXPLOITATION (Priority 40-80)
        ('three_try_sequence', 40),
        ('rule_transfer', 41),
        ('state_matching', 42),
        ('trigger_sequences', 43),
        ('discovery_exploitation', 44),
        ('embedding_matcher', 45),
        ('spatial_relationship', 46),
        ('causal_click_mapping', 46),
        ('constraint_decoder', 46),
        ('constraint_satisfaction', 46),
        ('object_color_targeting', 47),
        ('controlled_movement_planning', 47),
        ('spatial_map', 47),
        ('embedding_suggestion', 48),
        ('multi_stage_matching', 48),
        ('primitive_suggester', 49),
        ('network_sharing', 50),
        ('replay_learning', 51),
        ('network_wisdom', 52),
        ('abstraction_templates', 53),
        ('few_shot_relations', 54),
        ('few_shot_invariants', 55),
        ('subgoal_planning', 56),
        ('visual_analyzer', 57),
        ('network_object_inventory', 58),
        ('action6_object_exploration', 59),
        ('click_behavior_learning', 60),
        ('near_miss_analyzer', 61),
        ('completion_prediction', 62),
        ('frontier_topology', 63),
        ('map_intel_collision', 64),
        ('grid_exploration', 65),
        # FALLBACK
        ('smart_action_selection', 99),
    ],

    # Fix 1.4: ACTION6-only ordering for click-based puzzle games
    # (FT09, VC33). Prioritises visual analysis, click-effect learning,
    # and constraint satisfaction over movement-oriented rungs.
    'action6_only': [
        # EMERGENCY (Priority 1-5)
        ('infinite_loop_breaker', 1),
        ('coordinate_oscillation', 2),
        ('palette_detection', 3),
        ('sparse_grid', 3),
        # VISUAL UNDERSTANDING (Priority 5-15) — find what's clickable
        ('frame_interpretation', 5),
        ('affordance_detection', 6),
        ('visual_analyzer', 7),
        ('network_object_inventory', 8),
        ('action6_object_exploration', 9),
        ('survey', 10),
        # CLICK BEHAVIOUR (Priority 15-30) — apply learned patterns
        ('click_behavior_learning', 15),
        ('causal_click_mapping', 16),
        ('object_color_targeting', 17),
        ('interactable_tile_discovery', 18),
        # CONSTRAINT SOLVING (Priority 30-45)
        ('constraint_satisfaction', 30),
        ('constraint_decoder', 31),
        ('goal_relationship_modeling', 32),
        ('near_miss_analyzer', 33),
        ('completion_prediction', 34),
        ('state_matching', 35),
        # HYPOTHESIS & REASONING (Priority 45-60)
        ('hypothesis_system', 45),
        ('scientific_method', 46),
        ('theory_gate', 47),
        ('hypothesis_testing', 48),
        ('belief_system', 49),
        ('two_streams', 50),
        ('discovery_exploitation', 51),
        # NETWORK KNOWLEDGE (Priority 60-70)
        ('network_sharing', 60),
        ('network_wisdom', 61),
        ('embedding_suggestion', 62),
        ('primitive_suggester', 63),
        # EXPLORATION FALLBACK (Priority 70-99)
        ('grid_exploration', 75),
        ('exploration_phase', 80),
        ('smart_action_selection', 99),
    ],

    # Phased approach - different order by budget phase
    'phased_orientation': [
        ('infinite_loop_breaker', 1),
        ('coordinate_oscillation', 2),
        ('imagination_budget', 3),
        ('survey', 5),
        ('questioning_engine', 10),
        ('exploration_phase', 15),
        ('scientific_method', 20),
        ('network_exploration_stats', 25),
        ('death_avoidance', 35),
        ('grid_exploration', 40),
        ('smart_action_selection', 99),
    ],
    'phased_hypothesis': [
        ('infinite_loop_breaker', 1),
        ('coordinate_oscillation', 2),
        ('scientific_method', 5),
        ('metacognitive_prediction', 10),
        ('theory_gate', 15),
        ('deliberation_system', 20),
        ('two_streams', 25),
        ('death_avoidance', 30),
        ('network_wisdom', 35),
        ('exploration_phase', 40),
        ('smart_action_selection', 99),
    ],
    'phased_exploitation': [
        ('infinite_loop_breaker', 1),
        ('coordinate_oscillation', 2),
        ('death_avoidance', 5),
        ('terminal_pattern', 7),
        ('three_try_sequence', 10),
        ('discovery_exploitation', 15),
        ('embedding_suggestion', 20),
        ('multi_stage_matching', 25),
        ('network_wisdom', 30),
        ('primitive_suggester', 35),
        ('completion_prediction', 40),
        ('frontier_topology', 45),
        ('smart_action_selection', 99),
    ],

    # Minimal - only essential rungs for fast execution
    'minimal': [
        ('infinite_loop_breaker', 1),
        ('death_avoidance', 5),
        ('discovery_exploitation', 10),
        ('network_wisdom', 20),
        ('exploration_phase', 30),
        ('smart_action_selection', 99),
    ],

    # ACTION6 WORLD - For games where ACTION6 is available/primary
    'action6_world': [
        ('infinite_loop_breaker', 1),
        ('coordinate_oscillation', 2),
        ('palette_detection', 3),
        ('sparse_grid', 4),
        ('visual_analyzer', 5),
        ('affordance_detection', 5),
        ('budget_aware_planning', 5),
        ('control_tracker', 6),
        ('frame_interpretation', 7),
        ('event_understanding', 8),
        ('causal_click_mapping', 9),
        ('constraint_decoder', 10),
        ('trigger_sequences', 10),
        ('click_behavior_learning', 11),
        ('object_color_targeting', 12),
        ('constraint_satisfaction', 12),
        ('destructive_action_detection', 12),
        ('goal_relationship_modeling', 13),
        ('belief_system', 13),
        ('symbolic_tracker', 14),
        ('action6_object_exploration', 15),
        ('network_object_inventory', 16),
        ('primitive_suggester', 15),
        ('hypothesis_system', 16),
        ('scientific_method', 17),
        ('theory_gate', 18),
        ('assumption_formation', 19),
        ('network_wisdom', 20),
        ('network_sharing', 21),
        ('few_shot_relations', 22),
        ('resonance_detector', 23),
        ('valence_goals', 24),
        ('death_avoidance', 25),
        ('metacognitive_elimination', 25),
        ('pariah_avoidance', 26),
        ('viral_package_weights', 27),
        ('grid_exploration', 30),
        ('exploration_phase', 35),
        ('frustration_detection', 40),
        ('metacognitive_prediction', 41),
        ('smart_action_selection', 99),
    ],

    # ACTION6-only game (like vc33)
    'action6_only': [
        ('infinite_loop_breaker', 1),
        ('coordinate_oscillation', 2),
        ('palette_detection', 3),
        ('sparse_grid', 4),
        ('visual_analyzer', 5),
        ('affordance_detection', 5),
        ('budget_aware_planning', 5),
        ('action6_object_exploration', 6),
        ('click_behavior_learning', 7),
        ('object_color_targeting', 7),
        ('causal_click_mapping', 8),
        ('constraint_decoder', 8),
        ('constraint_satisfaction', 8),
        ('destructive_action_detection', 9),
        ('goal_relationship_modeling', 9),
        ('trigger_sequences', 9),
        ('network_object_inventory', 10),
        ('event_understanding', 11),
        ('belief_system', 11),
        ('symbolic_tracker', 12),
        ('control_tracker', 13),
        ('hypothesis_system', 14),
        ('scientific_method', 15),
        ('theory_gate', 16),
        ('network_wisdom', 17),
        ('network_sharing', 18),
        ('primitive_suggester', 19),
        ('valence_goals', 20),
        ('death_avoidance', 25),
        ('metacognitive_elimination', 25),
        ('pariah_avoidance', 26),
        ('viral_package_weights', 27),
        ('grid_exploration', 30),
        ('exploration_phase', 35),
        ('smart_action_selection', 99),
    ],

    # Exploration-heavy for frontier games
    'frontier_exploration': [
        ('infinite_loop_breaker', 1),
        ('coordinate_oscillation', 2),
        ('palette_detection', 3),
        ('self_trust_boost', 4),
        ('budget_aware_planning', 4),
        ('affordance_detection', 5),
        ('frontier_checkpoint', 5),
        ('survey', 6),
        ('network_exploration_stats', 8),
        ('exploration_phase', 10),
        ('wall_aware_navigation', 11),
        ('controlled_movement_planning', 12),
        ('assumption_formation', 13),
        ('hypothesis_testing', 14),
        ('contextual_failure', 15),
        ('questioning_engine', 15),
        ('scientific_method', 20),
        ('rule_transfer', 22),
        ('action6_object_exploration', 24),
        ('click_behavior_learning', 25),
        ('causal_click_mapping', 26),
        ('constraint_decoder', 26),
        ('constraint_satisfaction', 26),
        ('interactable_tile_discovery', 27),
        ('object_color_targeting', 27),
        ('destructive_action_detection', 27),
        ('goal_relationship_modeling', 28),
        ('spatial_map', 28),
        ('grid_exploration', 28),
        ('metacognitive_elimination', 35),
        ('viral_package_weights', 36),
        ('death_avoidance', 40),
        ('discovery_exploitation', 45),
        ('smart_action_selection', 99),
    ],
}


# =============================================================================
# MAIN DECISION SYSTEM
# =============================================================================

class DecisionRungSystem:
    """
    Modular action decision system with swappable rung orderings.

    All rung classes are imported from the ``rungs`` package.
    """

    # Use the unified registry from rungs/__init__.py
    RUNG_REGISTRY: Dict[str, type] = RUNG_REGISTRY

    def __init__(self,
                 strategy: str = 'context_adaptive',
                 core_gameplay_ref: Any = None,
                 config_path: Optional[str] = None,
                 engine_registry: Optional["EngineRegistry"] = None,
                 cognitive_router: Optional[Any] = None,
                 routing_trace_store: Optional[Any] = None):
        """
        Args:
            strategy: 'ladder', 'weighted', 'phased', 'parallel', 'cognitive', or 'context_adaptive'
            core_gameplay_ref: Reference to CoreGameplay instance (legacy)
            config_path: Optional path to custom ordering config
            engine_registry: EngineRegistry for modular engine access (preferred)
            cognitive_router: Pre-configured CognitiveRouter instance
            routing_trace_store: RoutingTraceStore for recording decision traces
        """
        self.strategy = DecisionStrategy(strategy)
        self.core: Any = core_gameplay_ref
        self._engine_registry: Optional["EngineRegistry"] = engine_registry
        self._routing_trace_store: Optional[Any] = routing_trace_store
        self.rungs: List[DecisionRung] = []
        self.ordering_name = 'default'
        self.config_path = config_path or str(Path(__file__).parent / 'config' / 'rung_orderings.json')

        # Stats
        self.total_decisions = 0
        self.rung_wins: Dict[str, int] = {}

        # Last decision metadata (for checkpoint handoff to context builder)
        self.last_decision_metadata: Dict[str, Any] = {}

        # Track winning rung for feedback loop
        self._last_winning_rung: Optional[DecisionRung] = None
        self._last_outcome_context: Dict[str, Any] = {}

        # Temporal integration
        self._temporal_integrator = None
        self._category_modulation_map = {
            'hypothesis': 'exploration',
            'orientation': 'exploration',
            'exploitation': 'exploitation',
            'filter': 'safety',
            'emergency': 'safety',
            'fallback': 'neutral',
            'metacognition': 'neutral',
            'unknown': 'neutral',
        }
        self._current_generation: int = 0
        self._current_action_in_generation: int = 0

        # Deliberation audit
        self._deliberation_auditor = None
        self._current_deliberation: Optional[Any] = None

        # Cognitive router
        self._cognitive_router: Optional[Any] = cognitive_router
        self._cognitive_router_initialized: bool = (cognitive_router is not None)
        if cognitive_router is not None:
            _load_cognitive_router()

        # Load default ordering
        self._suppress_ordering_deprecation = (self.strategy == DecisionStrategy.COGNITIVE)
        self.load_ordering('comprehensive')

    @property
    def engines(self) -> "EngineRegistry":
        """Access modular engines via registry."""
        if self._engine_registry is not None:
            return self._engine_registry
        if self.core is not None:
            from engines.registry import EngineRegistry
            self._engine_registry = EngineRegistry(legacy_core=self.core)
        else:
            from engines.registry import EngineRegistry
            self._engine_registry = EngineRegistry()
        return self._engine_registry

    @property
    def temporal_integrator(self):
        """Lazy-load temporal integrator for multi-scale experience integration."""
        if self._temporal_integrator is None:
            try:
                from engines.memory.temporal_integrator import get_temporal_integrator
                db = None
                if self._engine_registry is not None:
                    try:
                        db = self._engine_registry._get_db_interface()
                    except Exception:
                        pass
                self._temporal_integrator = get_temporal_integrator(db)
            except ImportError:
                logger.debug("[RUNG-SYSTEM] TemporalIntegrator not available")
                self._temporal_integrator = None
        return self._temporal_integrator

    @property
    def deliberation_auditor(self):
        """Lazy-load deliberation auditor."""
        if self._deliberation_auditor is None:
            try:
                from engines.reasoning.deliberation_audit import (
                    get_deliberation_auditor,
                )
                db = None
                if self._engine_registry is not None:
                    try:
                        db = self._engine_registry._get_db_interface()
                    except Exception:
                        pass
                self._deliberation_auditor = get_deliberation_auditor(db)
            except ImportError:
                logger.debug("[RUNG-SYSTEM] DeliberationAuditor not available")
                self._deliberation_auditor = None
        return self._deliberation_auditor

    @property
    def cognitive_router(self):
        """Lazy-load cognitive router."""
        if self._cognitive_router is None and not self._cognitive_router_initialized:
            CognitiveRouterClass = _load_cognitive_router()
            if CognitiveRouterClass is not None:
                try:
                    self._cognitive_router = CognitiveRouterClass()
                    logger.info("[RUNG-SYSTEM] CognitiveRouter initialized")
                except Exception as e:
                    logger.warning(f"[RUNG-SYSTEM] Failed to initialize CognitiveRouter: {e}")
            self._cognitive_router_initialized = True
        return self._cognitive_router

    # ── Temporal context ─────────────────────────────────────────────────────

    def set_temporal_context(self, generation: int, action_in_generation: int) -> None:
        """Set current temporal context for decay calculations."""
        self._current_generation = generation
        self._current_action_in_generation = action_in_generation

    def record_outcome(self, agent_id: str, game_type: str, outcome_value: float) -> None:
        """Record an action outcome for temporal integration."""
        if self.temporal_integrator is not None:
            self.temporal_integrator.record_outcome(
                agent_id=agent_id, game_type=game_type,
                generation=self._current_generation,
                action_in_generation=self._current_action_in_generation,
                outcome_value=outcome_value
            )

        if self.deliberation_auditor is not None and self._current_deliberation is not None:
            try:
                if outcome_value > 0.0:
                    outcome_type_str = "positive"
                elif outcome_value < 0.0:
                    outcome_type_str = "negative"
                else:
                    outcome_type_str = "neutral"
                self.deliberation_auditor.record_outcome(
                    outcome_type=outcome_type_str, score_change=outcome_value,
                )
                self.deliberation_auditor.finalize()
                self._current_deliberation = None
            except Exception as e:
                logger.debug(f"[RUNG-SYSTEM] Deliberation outcome recording failed: {e}")

    def _get_category_modulation(self, agent_id: str, game_type: str) -> Dict[str, float]:
        """Get rung category priority modulation from temporal integration."""
        if self.temporal_integrator is None:
            return {}
        return self.temporal_integrator.get_rung_modulation(
            agent_id=agent_id, game_type=game_type,
            current_generation=self._current_generation,
            current_action=self._current_action_in_generation
        )

    def _get_modulated_priority(self, rung: DecisionRung, modulation: Dict[str, float]) -> float:
        """Get a rung's priority adjusted by temporal modulation."""
        base_priority = rung.get_priority()
        if not modulation:
            return base_priority
        mod_category = self._category_modulation_map.get(rung.category, 'neutral')
        if mod_category == 'neutral':
            return base_priority
        multiplier = modulation.get(mod_category, 1.0)
        return base_priority / multiplier

    # ── Ordering management ──────────────────────────────────────────────────

    def load_ordering(self, preset_name: str) -> None:
        """Load a preset ordering or custom config."""
        self.ordering_name = preset_name
        self.rungs = []

        suppress = getattr(self, '_suppress_ordering_deprecation', False)

        if preset_name in ORDERING_PRESETS:
            _warn_ordering_deprecated(preset_name, suppress_if_cognitive=suppress)
            ordering = ORDERING_PRESETS[preset_name]
        else:
            ordering = self._load_custom_ordering(preset_name)
            if not ordering:
                print(f"[RUNG-SYSTEM] Warning: Unknown ordering '{preset_name}', using comprehensive")
                ordering = ORDERING_PRESETS['comprehensive']

        # Shared engine registry
        if self._engine_registry is None:
            from engines.registry import EngineRegistry
            if self.core is not None:
                self._engine_registry = EngineRegistry(legacy_core=self.core)
            else:
                self._engine_registry = EngineRegistry()

        for rung_name, priority in ordering:
            if rung_name in self.RUNG_REGISTRY:
                rung = self.RUNG_REGISTRY[rung_name](
                    core_gameplay_ref=self.core,
                    engine_registry=self._engine_registry
                )
                rung.priority_override = priority
                self.rungs.append(rung)
            else:
                print(f"[RUNG-SYSTEM] Warning: Unknown rung '{rung_name}'")

        self.rungs.sort(key=lambda r: r.get_priority())
        print(f"[RUNG-SYSTEM] Loaded ordering '{preset_name}' with {len(self.rungs)} rungs")

    def _load_custom_ordering(self, name: str) -> Optional[List[Tuple[str, int]]]:
        """Load custom ordering from config file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    return config.get(name)
        except Exception as e:
            print(f"[RUNG-SYSTEM] Error loading config: {e}")
        return None

    def save_ordering(self, name: str, ordering: List[Tuple[str, int]]) -> None:
        """Save a custom ordering to config file"""
        try:
            config = {}
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
            config[name] = ordering
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"[RUNG-SYSTEM] Saved ordering '{name}'")
        except Exception as e:
            print(f"[RUNG-SYSTEM] Error saving config: {e}")

    # ── Main decide() entry point ────────────────────────────────────────────

    # Phase 0.1: keys a valid DecisionContext must carry
    _CONTEXT_EXPECTED_KEYS = frozenset({
        'available_actions', 'game_id', 'agent_id',
        'action_count', 'level_number',
    })

    def _get_wall_blocked_actions(self, context: Dict[str, Any]) -> Set[str]:
        """H16: Query the spatial_map rung for actions that lead to known walls.

        Returns a set of action names (e.g. {'ACTION1', 'ACTION3'}) that would
        move the agent into a known wall at the current position. Other rungs
        and the weighted-random fallback use this to avoid wasted actions.
        """
        game_type = context.get('game_type', '')
        level = context.get('level', 1)
        game_key = f"{game_type}_L{level}"

        spatial_rung = next(
            (r for r in self.rungs if r.name == 'spatial_map'), None
        )
        if spatial_rung is None:
            return set()

        pos = spatial_rung._position.get(game_key)
        if pos is None:
            return set()

        spatial_map = spatial_rung._maps.get(game_key, {})
        if not spatial_map:
            return set()

        blocked: Set[str] = set()
        for action, (dx, dy) in spatial_rung.ACTION_DELTAS.items():
            neighbor = (pos[0] + dx, pos[1] + dy)
            if spatial_map.get(neighbor) == 'wall':
                blocked.add(action)
        return blocked

    def decide(self, game_state: Any, context: Dict[str, Any]) -> Tuple[str, str]:
        """Make an action decision using current strategy."""
        self.total_decisions += 1

        # Phase 0.1: Warn once per session if context is a raw dict missing expected keys
        missing = self._CONTEXT_EXPECTED_KEYS - set(context.keys())
        if missing and not getattr(self, '_context_warned', False):
            import logging as _logging
            _logging.getLogger(__name__).warning(
                "[DRS] DecisionContext missing keys (raw dict?): %s", missing,
            )
            self._context_warned = True

        available = context.get('available_actions', [1, 2, 3, 4, 5, 6, 7])

        # H16: Inject wall-blocked actions into context so ALL strategies
        # can avoid known walls, not just the spatial_map rung.
        context['_wall_blocked_actions'] = self._get_wall_blocked_actions(context)
        current_ordering = self.ordering_name

        target_ordering = self._select_ordering_for_context(available, context)
        if target_ordering != current_ordering:
            self._switch_ordering_temporarily(target_ordering)

        try:
            if self.strategy == DecisionStrategy.LADDER:
                return self._decide_ladder(game_state, context)
            elif self.strategy == DecisionStrategy.WEIGHTED:
                return self._decide_weighted(game_state, context)
            elif self.strategy == DecisionStrategy.PHASED:
                return self._decide_phased(game_state, context)
            elif self.strategy == DecisionStrategy.PARALLEL:
                return self._decide_parallel(game_state, context)
            elif self.strategy == DecisionStrategy.CONTEXT_ADAPTIVE:
                return self._decide_context_adaptive(game_state, context)
            elif self.strategy == DecisionStrategy.COGNITIVE:
                return self._decide_cognitive(game_state, context)
            else:
                return self._decide_ladder(game_state, context)
        finally:
            if target_ordering != current_ordering:
                self._switch_ordering_temporarily(current_ordering)

    def _select_ordering_for_context(self, available_actions: List[int], context: Dict[str, Any]) -> str:
        """Select the best ordering based on available actions, game type, and agent role.

        Fix 1.4: ACTION6-only games now get the 'action6_only' preset.
        Fix 3.2: Agent role influences ordering — exploiters get minimal,
        optimizers get efficiency, pioneers get comprehensive.
        """
        actions_list = list(available_actions) if available_actions is not None else []

        # Fix 1.4: ACTION6-only games always use click-specialised ordering
        if actions_list == [6]:
            return 'action6_only'

        if 6 in available_actions:
            if self.ordering_name in ('action6_world', 'action6_only', 'frontier_exploration'):
                return self.ordering_name
            if context.get('frontier_mode', False):
                return 'action6_world'

        # Fix 3.2: Role-based ordering selection (archetype differentiation).
        # Exploiters use minimal proven strategies; optimizers refine
        # known patterns; pioneers explore everything.
        agent_role = context.get('agent_role', 'pioneer')
        if agent_role == 'exploiter':
            return 'efficiency'  # Only proven strategies
        elif agent_role == 'optimizer':
            return 'efficiency'  # Exploit known patterns, some exploration
        elif agent_role == 'pioneer':
            return 'comprehensive'  # Full exploration + all hypotheses

        return self.ordering_name

    def _switch_ordering_temporarily(self, target_ordering: str) -> None:
        """Switch to a different ordering without reinstantiating rungs."""
        if target_ordering not in ORDERING_PRESETS:
            return
        ordering = ORDERING_PRESETS[target_ordering]
        priority_map = {name: priority for name, priority in ordering}
        for rung in self.rungs:
            if rung.name in priority_map:
                rung.priority_override = priority_map[rung.name]
            else:
                rung.priority_override = 200
        self.rungs.sort(key=lambda r: r.get_priority())
        self.ordering_name = target_ordering

    # ── Strategy implementations ─────────────────────────────────────────────

    def _decide_ladder(self, game_state: Any, context: Dict[str, Any]) -> Tuple[str, str]:
        """First confident answer wins, with temporal modulation."""
        accumulated_weights = get_available_action_weights(context, 1.0)
        self.last_decision_metadata = {}
        self._last_winning_rung = None

        agent_id = context.get('agent_id', 'unknown')
        game_type = context.get('game_type', 'unknown')
        modulation = self._get_category_modulation(agent_id, game_type)

        if self.temporal_integrator is not None:
            context['exploration_appetite'] = self.temporal_integrator.get_exploration_appetite(
                agent_id=agent_id, game_type=game_type,
                current_generation=self._current_generation,
                current_action=self._current_action_in_generation
            )

        sorted_rungs = sorted(self.rungs, key=lambda r: self._get_modulated_priority(r, modulation))

        for rung in sorted_rungs:
            if not rung.enabled:
                continue
            result = rung.evaluate(game_state, context)

            if result.weights:
                for action, weight in result.weights.items():
                    if is_action_available(action, context):
                        accumulated_weights[action] = accumulated_weights.get(action, 1.0) * weight

            if result.has_suggestion(rung.confidence_threshold):
                if result.action and not is_action_available(result.action, context):
                    continue
                if result.action == 'ACTION6':
                    result = Action6CoordinateProvider.enrich_result_with_coordinates(
                        result, context, self._engine_registry, game_state
                    )
                self.rung_wins[rung.name] = self.rung_wins.get(rung.name, 0) + 1
                self._last_winning_rung = rung
                rung.record_outcome(was_accepted=True)
                self.last_decision_metadata = result.metadata or {}
                self.last_decision_metadata['rung_name'] = rung.name
                return result.action or get_random_available_action(context), f"[{rung.name}] {result.reason}"

        action, reason = self._weighted_random_choice(accumulated_weights, context), "Weighted fallback after ladder"
        self.last_decision_metadata['rung_name'] = 'weighted_fallback'
        if action == 'ACTION6':
            coords = Action6CoordinateProvider.get_coordinates(context, self._engine_registry, game_state)
            self.last_decision_metadata = {**coords, 'rung_name': 'weighted_fallback'}
            reason += f" [coords: ({coords['x']},{coords['y']})]"
        return action, reason

    def _decide_weighted(self, game_state: Any, context: Dict[str, Any]) -> Tuple[str, str]:
        """All rungs vote, weighted sum decides."""
        action_votes = get_available_action_weights(context, 0.0)
        reasons: List[str] = []
        self.last_decision_metadata = {}
        self._last_winning_rung = None

        agent_id = context.get('agent_id', 'unknown')
        game_type = context.get('game_type', 'unknown')
        modulation = self._get_category_modulation(agent_id, game_type)

        # Deliberation audit
        if self.deliberation_auditor is not None:
            game_id = context.get('game_id', context.get('scorecard_id', 'unknown'))
            level_number = context.get('level_number', context.get('level', 0))
            action_number = context.get('action_count', 0)
            self.deliberation_auditor.start_deliberation(
                game_id=game_id,
                game_type=game_type[:4] if len(game_type) >= 4 else game_type,
                level_number=level_number, action_number=action_number,
                agent_id=agent_id, context=context,
            )

        if self.temporal_integrator is not None:
            context['exploration_appetite'] = self.temporal_integrator.get_exploration_appetite(
                agent_id=agent_id, game_type=game_type,
                current_generation=self._current_generation,
                current_action=self._current_action_in_generation
            )

        rung_contributions: Dict[str, Tuple[DecisionRung, float, str]] = {}
        all_alternatives: Dict[str, Tuple[float, str, str]] = {}

        for rung in self.rungs:
            if not rung.enabled:
                continue
            result = rung.evaluate(game_state, context)

            if result.action:
                if not is_action_available(result.action, context):
                    continue
                base_weight = result.confidence * (100 - rung.get_priority()) / 100
                mod_category = self._category_modulation_map.get(rung.category, 'neutral')
                mod_multiplier = modulation.get(mod_category, 1.0) if modulation else 1.0
                weight = base_weight * mod_multiplier
                action_votes[result.action] = action_votes.get(result.action, 0) + weight
                reasons.append(f"{rung.name}:{result.action}({weight:.2f})")
                if result.action not in rung_contributions or weight > rung_contributions[result.action][1]:
                    rung_contributions[result.action] = (rung, weight, rung.name)
                if result.action not in all_alternatives or result.confidence > all_alternatives[result.action][0]:
                    all_alternatives[result.action] = (result.confidence, result.reason, rung.name)

            if result.weights:
                for action, w in result.weights.items():
                    if is_action_available(action, context):
                        action_votes[action] = action_votes.get(action, 0) + w * 0.1

        best_action = max(action_votes, key=lambda k: action_votes[k])

        # Deliberation audit recording
        if self.deliberation_auditor is not None:
            sorted_actions = sorted(action_votes.items(), key=lambda x: x[1], reverse=True)
            for action, vote_weight in sorted_actions[:5]:
                if action in all_alternatives:
                    conf, reason_txt, rung_name = all_alternatives[action]
                    why_rejected = None if action == best_action else f"lower_vote:{vote_weight:.2f}"
                    self.deliberation_auditor.add_alternative(
                        action=action, confidence=conf, reason=reason_txt,
                        rung=rung_name, why_rejected=why_rejected,
                    )
            if best_action in all_alternatives:
                conf, reason_txt, rung_name = all_alternatives[best_action]
            else:
                conf, reason_txt, rung_name = action_votes.get(best_action, 0.0), "weighted_vote", "aggregate"
            self.deliberation_auditor.record_choice(
                chosen_action=best_action, confidence=conf, reason=reason_txt, rung=rung_name,
            )
            sparse_cell_count = context.get('sparse_cell_count', 0)
            sparse_colors = context.get('sparse_colors', set())
            sparse_hash = context.get('sparse_hash', '')
            if sparse_cell_count > 0:
                self.deliberation_auditor.set_sparse_context(
                    cell_count=sparse_cell_count,
                    colors=list(sparse_colors) if isinstance(sparse_colors, set) else sparse_colors,
                    sparse_hash=sparse_hash,
                )
            self._current_deliberation = self.deliberation_auditor._current_record

        if best_action in rung_contributions:
            self._last_winning_rung = rung_contributions[best_action][0]
            self._last_winning_rung.record_outcome(was_accepted=True)
            self.last_decision_metadata['rung_name'] = rung_contributions[best_action][2]
        else:
            self.last_decision_metadata['rung_name'] = 'aggregate'

        reason = f"Weighted vote: {best_action} ({action_votes[best_action]:.2f}) from [{', '.join(reasons[:3])}]"

        if best_action == 'ACTION6':
            coords = Action6CoordinateProvider.get_coordinates(context, self._engine_registry, game_state)
            self.last_decision_metadata = {**self.last_decision_metadata, **coords}
            reason += f" [coords: ({coords['x']},{coords['y']})]"

        return best_action, reason

    def _decide_phased(self, game_state: Any, context: Dict[str, Any]) -> Tuple[str, str]:
        """Use different orderings based on budget phase"""
        budget_used: float = float(context.get('budget_used_percent', 0))
        if budget_used < 0.1:
            phase_ordering = 'phased_orientation'
        elif budget_used < 0.3:
            phase_ordering = 'phased_hypothesis'
        else:
            phase_ordering = 'phased_exploitation'
        old_rungs = self.rungs
        self.load_ordering(phase_ordering)
        action, reason = self._decide_ladder(game_state, context)
        self.rungs = old_rungs
        return action, f"[{phase_ordering}] {reason}"

    def _decide_parallel(self, game_state: Any, context: Dict[str, Any]) -> Tuple[str, str]:
        """Run all rungs, pick highest confidence"""
        best_result: Optional[RungResult] = None
        best_rung: Optional[DecisionRung] = None
        self._last_winning_rung = None

        for rung in self.rungs:
            if not rung.enabled:
                continue
            result = rung.evaluate(game_state, context)
            if result.action and is_action_available(result.action, context):
                if best_result is None or result.confidence > best_result.confidence:
                    best_result = result
                    best_rung = rung

        if best_result and best_rung:
            self.rung_wins[best_rung.name] = self.rung_wins.get(best_rung.name, 0) + 1
            self._last_winning_rung = best_rung
            best_rung.record_outcome(was_accepted=True)
            self.last_decision_metadata = best_result.metadata or {}
            self.last_decision_metadata['rung_name'] = best_rung.name
            return best_result.action or get_random_available_action(context), f"[{best_rung.name}] {best_result.reason}"

        self.last_decision_metadata['rung_name'] = 'no_suggestion'
        return get_random_available_action(context), "No suggestions from any rung"

    def _weighted_random_choice(self, weights: Dict[str, float], context: Optional[Dict[str, Any]] = None) -> str:
        """Make a weighted random choice from weights dict."""
        if not weights:
            if context:
                return get_random_available_action(context)
            return 'ACTION1'

        # H16: Suppress actions that lead to known walls.
        # Only filter if we have alternatives — never block ALL actions.
        wall_blocked = context.get('_wall_blocked_actions', set()) if context else set()
        if wall_blocked:
            safe_weights = {a: w for a, w in weights.items() if a not in wall_blocked}
            if safe_weights:
                weights = safe_weights

        total = sum(max(0.05, w) for w in weights.values())
        r = random.random() * total
        cumulative = 0
        for action, weight in weights.items():
            cumulative += max(0.05, weight)
            if r <= cumulative:
                return action
        return next(iter(weights.keys()))

    # ── Outcome feedback ─────────────────────────────────────────────────────

    def report_outcome(self, action: str, success: bool, is_death: bool = False,
                       score_delta: float = 0.0, context: Optional[Dict[str, Any]] = None) -> None:
        """Report the actual outcome of the last decision back to the winning rung."""
        if self._last_winning_rung is None:
            return
        self._last_outcome_context = {
            'action': action, 'success': success, 'is_death': is_death,
            'score_delta': score_delta, 'context': context or {}
        }
        try:
            self._last_winning_rung.record_outcome(was_accepted=True, success=success)
        except TypeError:
            pass
        except Exception:
            pass

        if is_death:
            outcome_value = -1.0
        elif success:
            outcome_value = min(1.0, max(0.1, score_delta)) if score_delta > 0 else 0.5
        else:
            outcome_value = -0.3

        ctx = context or {}
        self.record_outcome(
            agent_id=ctx.get('agent_id', 'unknown'),
            game_type=ctx.get('game_type', 'unknown'),
            outcome_value=outcome_value
        )

    def notify_action_complete(self, action: str, action_data: Dict[str, Any],
                               frame_before: Any, frame_after: Any,
                               context: Dict[str, Any]) -> None:
        """Notify rungs that have on_action_complete hooks.

        Gap 4D: Also adjusts rung confidence based on action outcome.
        If the action was destructive or wasted, the rung that suggested
        it should lose confidence. If productive, confidence is boosted.
        """
        # ═══ GAP 4D: Outcome-based confidence adjustment ═══
        # Find which rung was responsible for the last action
        last_rung_name = context.get('last_rung_name') or (
            self._last_winning_rung.name if self._last_winning_rung else None)
        was_productive = context.get('was_productive', False)
        was_destructive = context.get('was_destructive', False)
        was_wasted = context.get('was_wasted', False)

        if last_rung_name:
            for rung in self.rungs:
                if rung.name == last_rung_name:
                    # Adjust confidence threshold based on outcome
                    if was_destructive:
                        # Rung produced harmful action -> raise threshold (harder to fire)
                        rung.confidence_threshold = min(
                            0.95, rung.confidence_threshold + 0.05)
                    elif was_wasted:
                        # Rung produced no-effect action -> slight threshold increase
                        rung.confidence_threshold = min(
                            0.95, rung.confidence_threshold + 0.02)
                    elif was_productive:
                        # Rung produced good action -> lower threshold (easier to fire)
                        rung.confidence_threshold = max(
                            0.1, rung.confidence_threshold - 0.03)
                    break

        for rung in self.rungs:
            if hasattr(rung, 'on_action_complete'):
                try:
                    rung.on_action_complete(
                        action=action, action_data=action_data,
                        frame_before=frame_before, frame_after=frame_after,
                        context=context
                    )
                except Exception:
                    pass

    # ── Emergency rungs ──────────────────────────────────────────────────────

    EMERGENCY_RUNG_NAMES = frozenset({'infinite_loop_breaker', 'coordinate_oscillation'})

    def _decide_context_adaptive(self, game_state: Any, context: Dict[str, Any]) -> Tuple[str, str]:
        """Context-dependent strategy selection."""
        emergency_result = self._check_emergency_rungs(game_state, context)
        if emergency_result is not None:
            return emergency_result

        effective_strategy = self._select_effective_strategy(context)
        if effective_strategy == 'weighted':
            return self._decide_weighted_non_emergency(game_state, context)
        else:
            return self._decide_ladder_non_emergency(game_state, context)

    def _check_emergency_rungs(self, game_state: Any, context: Dict[str, Any]) -> Optional[Tuple[str, str]]:
        """Check emergency rungs with LADDER semantics."""
        for rung in self.rungs:
            if not rung.enabled or rung.name not in self.EMERGENCY_RUNG_NAMES:
                continue
            result = rung.evaluate(game_state, context)
            if result.has_suggestion(rung.confidence_threshold):
                if result.action and not is_action_available(result.action, context):
                    continue
                if result.action == 'ACTION6':
                    result = Action6CoordinateProvider.enrich_result_with_coordinates(
                        result, context, self._engine_registry, game_state
                    )
                    self.last_decision_metadata = result.metadata or {}
                self.rung_wins[rung.name] = self.rung_wins.get(rung.name, 0) + 1
                rung.record_outcome(was_accepted=True)
                self.last_decision_metadata['rung_name'] = rung.name
                return result.action or get_random_available_action(context), f"[EMERGENCY:{rung.name}] {result.reason}"
        return None

    def _select_effective_strategy(self, context: Dict[str, Any]) -> str:
        """Select effective strategy based on context."""
        if context.get('replay_mode', False):
            return 'ladder'
        active_sequence = context.get('active_sequence')
        if active_sequence and context.get('sequence_position', 0) < len(active_sequence):
            return 'ladder'
        if context.get('frontier_mode', False):
            return 'weighted'
        if context.get('optimization_mode', False):
            return 'weighted'
        if context.get('game_state_mode', 'unknown') == 'exploration':
            return 'weighted'
        if context.get('has_winning_sequence', False) and not context.get('active_sequence'):
            return 'weighted'
        return 'ladder'

    def _decide_weighted_non_emergency(self, game_state: Any, context: Dict[str, Any]) -> Tuple[str, str]:
        """WEIGHTED strategy excluding emergency rungs."""
        action_votes = get_available_action_weights(context, 0.0)
        accumulated_weights = get_available_action_weights(context, 1.0)
        reasons: List[str] = []

        for rung in self.rungs:
            if not rung.enabled or rung.name in self.EMERGENCY_RUNG_NAMES:
                continue
            result = rung.evaluate(game_state, context)

            if result.weights:
                for action, weight in result.weights.items():
                    if is_action_available(action, context):
                        accumulated_weights[action] = accumulated_weights.get(action, 1.0) * weight

            if result.action:
                if not is_action_available(result.action, context):
                    continue
                weight = result.confidence * (100 - rung.get_priority()) / 100
                action_votes[result.action] = action_votes.get(result.action, 0) + weight
                reasons.append(f"{rung.name}:{result.action}({weight:.2f})")

        final_scores: Dict[str, float] = {}
        for action in action_votes:
            vote = action_votes[action]
            filter_weight = accumulated_weights.get(action, 1.0)
            final_scores[action] = (vote + 0.1) * filter_weight

        # H16: Remove wall-blocked actions from candidates if alternatives exist.
        wall_blocked = context.get('_wall_blocked_actions', set())
        if wall_blocked:
            safe_scores = {a: s for a, s in final_scores.items() if a not in wall_blocked}
            if safe_scores:
                final_scores = safe_scores

        best_action = max(final_scores, key=lambda k: final_scores[k])
        best_score = final_scores[best_action]

        if best_score < 0.15:
            action, reason = self._weighted_random_choice(accumulated_weights, context), "Weighted random (low confidence)"
            self.last_decision_metadata['rung_name'] = 'weighted_random'
            if action == 'ACTION6':
                coords = Action6CoordinateProvider.get_coordinates(context, self._engine_registry, game_state)
                self.last_decision_metadata = {**coords, 'rung_name': 'weighted_random'}
                reason += f" [coords: ({coords['x']},{coords['y']})]"
            return action, reason

        top_contributors = ', '.join(reasons[:3]) if reasons else 'filters only'
        reason = f"[WEIGHTED] {best_action} ({best_score:.2f}) from [{top_contributors}]"

        # Extract winning rung name from top contributor
        _wnr_rung = reasons[0].split(':')[0] if reasons else 'aggregate'
        self.last_decision_metadata['rung_name'] = _wnr_rung

        if best_action == 'ACTION6':
            coords = Action6CoordinateProvider.get_coordinates(context, self._engine_registry, game_state)
            self.last_decision_metadata = {**self.last_decision_metadata, **coords, 'rung_name': _wnr_rung}
            reason += f" [coords: ({coords['x']},{coords['y']})]"

        return best_action, reason

    def _decide_ladder_non_emergency(self, game_state: Any, context: Dict[str, Any]) -> Tuple[str, str]:
        """LADDER strategy excluding emergency rungs."""
        accumulated_weights = get_available_action_weights(context, 1.0)

        for rung in self.rungs:
            if not rung.enabled or rung.name in self.EMERGENCY_RUNG_NAMES:
                continue
            result = rung.evaluate(game_state, context)

            if result.weights:
                for action, weight in result.weights.items():
                    if is_action_available(action, context):
                        accumulated_weights[action] = accumulated_weights.get(action, 1.0) * weight

            if result.has_suggestion(rung.confidence_threshold):
                if result.action and not is_action_available(result.action, context):
                    continue
                # H16: Skip movement actions that lead to known walls.
                # The spatial_map rung already avoids walls, but other rungs
                # may suggest wall-hitting movements. Skip and try the next rung.
                wall_blocked = context.get('_wall_blocked_actions', set())
                if result.action in wall_blocked:
                    continue
                if result.action == 'ACTION6':
                    result = Action6CoordinateProvider.enrich_result_with_coordinates(
                        result, context, self._engine_registry, game_state
                    )
                self.rung_wins[rung.name] = self.rung_wins.get(rung.name, 0) + 1
                rung.record_outcome(was_accepted=True)
                self.last_decision_metadata = result.metadata or {}
                self.last_decision_metadata['rung_name'] = rung.name
                return result.action or get_random_available_action(context), f"[{rung.name}] {result.reason}"

        action, reason = self._weighted_random_choice(accumulated_weights, context), "Weighted fallback after ladder"
        self.last_decision_metadata['rung_name'] = 'weighted_fallback'
        if action == 'ACTION6':
            coords = Action6CoordinateProvider.get_coordinates(context, self._engine_registry, game_state)
            self.last_decision_metadata = {**coords, 'rung_name': 'weighted_fallback'}
            reason += f" [coords: ({coords['x']},{coords['y']})]"
        return action, reason

    def _decide_cognitive(self, game_state: Any, context: Dict[str, Any]) -> Tuple[str, str]:
        """Cognitive routing strategy - full pipeline."""
        router = self.cognitive_router
        if router is None:
            logger.warning("[RUNG-SYSTEM] CognitiveRouter unavailable, falling back to context_adaptive")
            return self._decide_context_adaptive(game_state, context)

        # Emergency rungs first (safety invariant)
        emergency_result = self._check_emergency_rungs(game_state, context)
        if emergency_result is not None:
            return emergency_result

        # Replay fast-path
        active_seq = context.get('active_sequence')
        seq_pos = context.get('sequence_position', 0)
        if active_seq and seq_pos < len(active_seq) and context.get('is_replay'):
            seq_action = active_seq[seq_pos]
            if is_action_available(seq_action, context):
                rung_name = 'three_try_sequence'
                self.rung_wins[rung_name] = self.rung_wins.get(rung_name, 0) + 1
                rung_obj = next((r for r in self.rungs if r.name == rung_name), None)
                if rung_obj:
                    rung_obj.record_outcome(was_accepted=True)
                    self._last_winning_rung = rung_obj
                self.last_decision_metadata['rung_name'] = rung_name
                return seq_action, f"[COGNITIVE:{rung_name}] Replay fast-path: step {seq_pos + 1}/{len(active_seq)}"

        # Initialize router per game
        game_id = context.get('game_id', context.get('scorecard_id', 'unknown'))
        if not hasattr(self, '_cognitive_game_id') or self._cognitive_game_id != game_id:
            nodes = {
                rung.name: {'name': rung.name, 'category': rung.category, 'priority': rung.get_priority()}
                for rung in self.rungs if rung.name not in self.EMERGENCY_RUNG_NAMES
            }
            edges: Dict[str, List[str]] = {}
            try:
                from engines.cognition.edge_inference import EdgeInferenceEngine
                edge_engine = EdgeInferenceEngine()
                rung_classes = [type(r) for r in self.rungs if r.name not in self.EMERGENCY_RUNG_NAMES]
                edge_engine.analyze_rungs(rung_classes)
                inferred = edge_engine.infer_all_edges()
                for ie in inferred:
                    if ie.source_rung not in edges:
                        edges[ie.source_rung] = []
                    if ie.target_rung not in edges[ie.source_rung]:
                        edges[ie.source_rung].append(ie.target_rung)
                logger.info(f"[RUNG-SYSTEM] Edge inference: {len(inferred)} edges for {len(nodes)} rungs")
            except Exception as edge_err:
                logger.warning(f"[RUNG-SYSTEM] Edge inference failed, using empty edges: {edge_err}")

            router.initialize(nodes, edges, game_id)
            self._cognitive_game_id = game_id
            self._cognitive_previously_successful_rungs = set()

        # Rung executor closure
        self._cognitive_last_rung_metadata: Dict[str, Any] = {}
        self._cognitive_last_winning_rung: Optional[DecisionRung] = None
        if not hasattr(self, '_cognitive_previously_successful_rungs'):
            self._cognitive_previously_successful_rungs: set = set()

        def rung_executor(rung_name: str, _game_state_dict: Dict) -> Any:
            """Execute a legacy rung and bridge to cognitive RungResult."""
            rung = next((r for r in self.rungs if r.name == rung_name), None)
            if rung is None or not rung.enabled:
                if _RungResult_Cognitive:
                    return _RungResult_Cognitive(rung_name=rung_name, confidence=0.0)
                return None

            try:
                result = rung.evaluate(game_state, context)
            except Exception as eval_err:
                logger.debug(f"[RUNG-EXECUTOR] {rung_name} evaluate() failed: {eval_err}")
                if _RungResult_Cognitive:
                    return _RungResult_Cognitive(rung_name=rung_name, confidence=0.0)
                return None

            if result.action and result.confidence > 0:
                self._cognitive_last_winning_rung = rung
                self._cognitive_last_rung_metadata = result.metadata or {}
                self._cognitive_previously_successful_rungs.add(rung_name)

            metadata = result.metadata or {}
            contradiction_detected = metadata.get('contradiction_detected', False)
            surprise_level = 0.0

            if not result.action and rung_name in self._cognitive_previously_successful_rungs:
                contradiction_detected = True
                surprise_level = 0.8

            slot_name = metadata.get('slot_name')
            if not slot_name and result.action:
                slot_name = rung_name

            questions_raised = []
            answers = []
            if not result.action and not self._cognitive_last_winning_rung:
                try:
                    from engines.cognition.blackboard import Question
                    questions_raised.append(Question(
                        question_id=f"what_works_for_{game_id}",
                        description="What action works in current game state?",
                        answerable_by=[r.name for r in self.rungs if r.name not in self.EMERGENCY_RUNG_NAMES],
                        priority=0.6,
                    ))
                except ImportError:
                    pass

            if contradiction_detected and rung_name in self._cognitive_previously_successful_rungs:
                try:
                    from engines.cognition.blackboard import Question
                    questions_raised.append(Question(
                        question_id=f"why_failed_{rung_name}_{game_id}",
                        description=f"Why did {rung_name} stop working?",
                        answerable_by=[r.name for r in self.rungs if r.name != rung_name and r.name not in self.EMERGENCY_RUNG_NAMES],
                        priority=0.8,
                    ))
                except ImportError:
                    pass

            if result.action and result.confidence > 0.3:
                answers.append(f"what_works_for_{game_id}")

            if _RungResult_Cognitive:
                return _RungResult_Cognitive(
                    rung_name=rung_name, slot_name=slot_name,
                    value=result.action, confidence=result.confidence,
                    raises_questions=questions_raised, answers_questions=answers,
                    surprise_level=surprise_level,
                    contradiction_detected=contradiction_detected,
                    contradiction_with=metadata.get('contradiction_with'),
                )
            return result

        # Run the cognitive router
        try:
            decision_result = router.decide(
                game_state={'frame': getattr(game_state, 'frame', None), **context},
                rung_executor=rung_executor
            )

            action = decision_result.action_value
            rung_name = decision_result.action
            confidence = decision_result.confidence
            reasoning = f"[COGNITIVE:{rung_name}] {decision_result.reasoning}"

            if self._cognitive_last_winning_rung is not None:
                self._last_winning_rung = self._cognitive_last_winning_rung
                self.rung_wins[rung_name] = self.rung_wins.get(rung_name, 0) + 1
                self._cognitive_last_winning_rung.record_outcome(was_accepted=True)

            self.last_decision_metadata['rung_name'] = rung_name

            if not action or not is_action_available(action, context):
                weighted_action, weighted_reason = self._decide_weighted_non_emergency(game_state, context)
                action = weighted_action
                reasoning = f"[COGNITIVE:{rung_name}] Weighted fallback (router rung had no action) -> {weighted_reason}"

            if action not in {f'ACTION{i}' for i in range(1, 8)}:
                action = get_random_available_action(context)
                reasoning = "[COGNITIVE] Random fallback: invalid action format"

            if action == 'ACTION6':
                coords = self._cognitive_last_rung_metadata
                if 'x' not in coords or 'y' not in coords:
                    coords = Action6CoordinateProvider.get_coordinates(context, self._engine_registry, game_state)
                self.last_decision_metadata = {**coords, 'rung_name': rung_name}
                reasoning += f" [coords: ({coords.get('x', 32)},{coords.get('y', 32)})]"

            # Record trace
            if self._routing_trace_store is not None:
                try:
                    trace_id = self._routing_trace_store.record_trace(
                        game_id=game_id, agent_id=context.get('agent_id', 'unknown'),
                        path=decision_result.path,
                        algorithm_used=getattr(decision_result, 'algorithm_name', decision_result.final_quadrant),
                        final_action=action, final_confidence=confidence,
                        initial_quadrant=getattr(decision_result, 'initial_quadrant', decision_result.final_quadrant),
                        final_quadrant=decision_result.final_quadrant,
                        quadrant_transitions=getattr(decision_result, 'quadrant_transitions', []),
                        algorithms_history=getattr(decision_result, 'algorithms_history', []),
                        backtrack_count=getattr(decision_result, 'backtrack_count', 0),
                        iterations=decision_result.iterations,
                        decision_latency_ms=decision_result.time_elapsed * 1000
                    )
                    self.last_decision_metadata['trace_id'] = trace_id
                except Exception as trace_err:
                    logger.warning(f"[COGNITIVE] Failed to record trace: {trace_err}")

            if self.total_decisions % 100 == 0:
                stats = router.get_statistics()
                logger.info(
                    f"[COGNITIVE] Stats: {stats['total_decisions']} decisions, "
                    f"{stats['total_fallbacks']} fallbacks ({stats['fallback_rate']:.1%})"
                )

            return action, reasoning

        except Exception as e:
            import traceback
            logger.error(f"[COGNITIVE] Router error: {e}, falling back to context_adaptive\n{traceback.format_exc()}")
            return self._decide_context_adaptive(game_state, context)

    # ── Stats & experiments ──────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Get decision statistics"""
        return {
            'total_decisions': self.total_decisions,
            'ordering': self.ordering_name,
            'strategy': self.strategy.value,
            'rung_wins': self.rung_wins,
            'rung_count': len(self.rungs),
            'rungs': [{'name': r.name, 'priority': r.get_priority(), 'enabled': r.enabled} for r in self.rungs]
        }

    def experiment_orderings(self, game_state: Any, context: Dict[str, Any],
                             orderings: List[str]) -> Dict[str, Tuple[str, str]]:
        """Test multiple orderings on same state (for analysis)."""
        results: Dict[str, Tuple[str, str]] = {}
        original = self.ordering_name
        for ordering in orderings:
            self.load_ordering(ordering)
            action, reason = self._decide_ladder(game_state, context)
            results[ordering] = (action, reason)
        self.load_ordering(original)
        return results


# =============================================================================
# INTEGRATION ADAPTER
# =============================================================================

class CoreGameplayAdapter:
    """
    Adapter to integrate DecisionRungSystem with existing CoreGameplay._select_action().

    Enables phased migration:
    - PHASE 1: Shadow mode (run both, compare)
    - PHASE 2: Category takeover (rung system handles specific categories)
    - PHASE 3: Full replacement
    """

    def __init__(self, core_gameplay_ref: Any, ordering: str = 'comprehensive'):
        self.core: Any = core_gameplay_ref
        self.rung_system = DecisionRungSystem(
            strategy='ladder', core_gameplay_ref=core_gameplay_ref
        )
        self.rung_system.load_ordering(ordering)

        self.shadow_mode = False
        self.shadow_log: List[Dict[str, Any]] = []
        self.divergence_count = 0
        self.agreement_count = 0
        self._shadow_tester: Any = None
        self.category_enabled: Dict[str, bool] = {
            'emergency': False, 'filter': False, 'orientation': False,
            'hypothesis': False, 'exploitation': False, 'fallback': False,
        }

    def enable_shadow_mode(self, log_limit: int = 1000):
        """Enable shadow mode."""
        self.shadow_mode = True
        self.shadow_log = []
        self._shadow_log_limit = log_limit
        logger.info("[RUNG-ADAPTER] Shadow mode ENABLED")

    def get_shadow_tester(self) -> Any:
        """Lazy-load ShadowTester."""
        if self._shadow_tester is None:
            try:
                from engines.cognition.shadow_testing import ShadowTester
                self._shadow_tester = ShadowTester()
            except ImportError:
                logger.warning("[RUNG-ADAPTER] ShadowTester not available")
        return self._shadow_tester

    def disable_shadow_mode(self) -> Dict[str, Any]:
        """Disable shadow mode and return stats."""
        self.shadow_mode = False
        total = self.divergence_count + self.agreement_count
        agreement_rate = self.agreement_count / total if total > 0 else 0
        stats: Dict[str, Any] = {
            'total_comparisons': total, 'agreements': self.agreement_count,
            'divergences': self.divergence_count, 'agreement_rate': agreement_rate,
            'divergence_samples': self.shadow_log[-10:],
        }
        logger.info(f"[RUNG-ADAPTER] Shadow mode DISABLED - agreement rate: {agreement_rate:.1%}")
        return stats

    def shadow_compare(self, game_state: Any, context: Dict[str, Any], old_action: str) -> Dict[str, Any]:
        """Compare rung system decision with old system decision."""
        if not self.shadow_mode:
            return {}
        rung_action, rung_reason = self.rung_system.decide(game_state, context)
        agrees = rung_action == old_action
        if agrees:
            self.agreement_count += 1
        else:
            self.divergence_count += 1
            if len(self.shadow_log) < self._shadow_log_limit:
                self.shadow_log.append({
                    'old_action': old_action, 'rung_action': rung_action,
                    'rung_reason': rung_reason, 'ordering': self.rung_system.ordering_name,
                    'game_type': context.get('game_type'), 'level': context.get('level'),
                })
        return {'agrees': agrees, 'old_action': old_action, 'rung_action': rung_action, 'rung_reason': rung_reason}

    def enable_category(self, category: str):
        """Enable rung system for a specific category."""
        if category in self.category_enabled:
            self.category_enabled[category] = True

    def disable_category(self, category: str):
        """Disable rung system for a specific category."""
        if category in self.category_enabled:
            self.category_enabled[category] = False

    def decide_category(self, category: str, game_state: Any, context: Dict[str, Any]) -> RungResult:
        """Get decision from only rungs in a specific category."""
        if not self.category_enabled.get(category, False):
            return RungResult()
        category_rungs = [r for r in self.rung_system.rungs if r.category == category]
        if not category_rungs:
            return RungResult()
        for rung in sorted(category_rungs, key=lambda r: r.get_priority()):
            result = rung.evaluate(game_state, context)
            if result.has_suggestion(rung.confidence_threshold):
                return result
        return RungResult()

    def build_context_from_core(self, game_state: Any, loop_state: Any = None) -> Dict[str, Any]:
        """Build rung context from CoreGameplay state."""
        context: Dict[str, Any] = {}
        try:
            if hasattr(self.core, 'session_manager') and self.core.session_manager:
                game_id = self.core.session_manager.current_game_id
                context['game_id'] = game_id
                context['game_type'] = game_id[:4] if game_id and len(game_id) >= 4 else None

            if hasattr(game_state, 'score'):
                context['level'] = int(game_state.score) + 1
                context['score'] = game_state.score

            if loop_state:
                context['action_count'] = getattr(loop_state, 'action_count', 0)
                action_budget = context.get('action_budget') or getattr(
                    getattr(self.core, '_loop_config', None), 'max_actions', 400
                )
                context.setdefault('action_budget', action_budget)
                context['budget_used_percent'] = context['action_count'] / max(action_budget, 1)

            if hasattr(self.core, 'game_config'):
                context['agent_id'] = self.core.game_config.get('agent_id')
                context['agent_role'] = self.core.game_config.get('agent_role')

            context['w_A'] = getattr(self.core, '_current_wA', 0.5)
            context['w_B'] = getattr(self.core, '_current_wB', 0.5)
            context['agent_position'] = getattr(self.core, '_current_agent_position', None)

            available = context.get('available_actions', [1, 2, 3, 4, 5, 6, 7])
            default_safety = {a: 1.0 for a in available}
            context['action_safety_weights'] = getattr(self.core, '_action_safety_weights', default_safety)
            context['recent_actions'] = getattr(self.core, '_recent_actions', [])[-10:]
            context['game_type'] = context.get('game_id', '').split('-')[0] if context.get('game_id') else None

            context['is_frontier'] = self.core._is_frontier_level(
                context.get('game_id', ''), context.get('level', 1)
            ) if hasattr(self.core, '_is_frontier_level') else False

        except Exception as e:
            logger.debug(f"[RUNG-ADAPTER] Context build partial failure: {e}")

        return context

    def full_decide(self, game_state: Any, loop_state: Any = None) -> Tuple[str, str]:
        """Full replacement for _select_action() - PHASE 3."""
        context = self.build_context_from_core(game_state, loop_state)
        return self.rung_system.decide(game_state, context)


# =============================================================================
# HELPER: Create custom ordering interactively
# =============================================================================

def create_custom_ordering(name: str, rung_priorities: Dict[str, int]) -> List[Tuple[str, int]]:
    """Create a custom ordering."""
    return [(rung, priority) for rung, priority in sorted(rung_priorities.items(), key=lambda x: x[1])]


if __name__ == '__main__':
    print("=" * 60)
    print("DECISION RUNG SYSTEM - MODULAR ACTION ARCHITECTURE")
    print("=" * 60)

    print("\nAvailable Rungs:")
    for name, cls in DecisionRungSystem.RUNG_REGISTRY.items():
        category = getattr(cls, 'category', 'unknown')
        priority = getattr(cls, 'default_priority', 50)
        print(f"  - {name}: {category} (default priority: {priority})")

    print("\nAvailable Orderings:")
    for name, ordering in ORDERING_PRESETS.items():
        rungs_list = [r[0] for r in ordering]
        print(f"  - {name}: {len(ordering)} rungs")
        print(f"    Order: {' -> '.join(rungs_list[:5])}...")

    print("=" * 60)
