"""
Decision Rung System - Modular Action Decision Architecture
============================================================

Allows swapping the order of decision features like LEGO bricks.
Each "rung" is a pluggable component with a standard interface.

INTEGRATION WITH PRIMITIVES:
----------------------------
The rung system integrates with Seed Primitives via PrimitiveSuggester:

1. DIRECT RUNG: PrimitiveSuggesterRung applies primitives to frames and
   maps outputs to action suggestions with RLVR feedback.

2. PRIMITIVE-AWARE RUNGS: Rungs can declare `required_primitives` to use
   seed primitives directly (e.g., detect_novelty, get_confidence).

3. IMPLICIT FLOW: Many rungs use primitive discoveries indirectly through
   network knowledge, validated patterns, and shared hypotheses.

The architecture separates:
- WHAT primitives are available (SeedPrimitiveRegistry - 315 primitives)
- HOW they map to actions (PrimitiveSuggester)
- WHEN to use them (Decision Rung System)
- FEEDBACK (RLVR - learn what works per game type)

Ordering Strategies:
1. LADDER: First confident answer wins (current behavior)
2. WEIGHTED: All rungs vote, weighted sum decides
3. PHASED: Different orderings for orientation/hypothesis/exploitation phases

Integration with core_gameplay.py:
----------------------------------
The rung system can REPLACE the 1500+ line _select_action() method through
gradual migration:

PHASE 1 (SHADOW MODE): Run both systems, compare outputs, log divergences
PHASE 2 (PARTIAL): Use rung system for specific categories (e.g., emergency)
PHASE 3 (FULL): Replace _select_action() with DecisionRungSystem.decide()

Usage:
    system = DecisionRungSystem(strategy='ladder')
    system.load_ordering('llm_optimal')  # or 'human_brain', 'efficiency', 'custom'
    action, reason = system.decide(game_state, agent_context)
"""

import os

# Prevent pycache (Rule 1)
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import json
import logging
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple

# Set up logging with database support (Rule 2) + console output
# setup_database_logging configures root logger with both handlers
try:
    from database_logger import setup_database_logging
    setup_database_logging(level='INFO')  # Returns handler, but configures root logger
    logger = logging.getLogger(__name__)  # Get a child logger of configured root
except ImportError:
    # Fallback to standard logging if database_logger not available
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('[%(name)s:%(levelname)s] %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

# =============================================================================
# COGNITIVE ROUTER INTEGRATION - Lazy loading to avoid circular imports
# =============================================================================
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

# Type hints for engine registry (avoid circular imports)
if TYPE_CHECKING:
    from engines.registry import EngineRegistry

# =============================================================================
# PRIMITIVE INTEGRATION - Lazy loading to avoid circular imports
# =============================================================================
_primitives_loaded: bool = False
_seed_primitives: Any = None

def _load_primitives() -> Any:
    """Lazy-load seed primitives registry."""
    global _primitives_loaded, _seed_primitives
    if _primitives_loaded:
        return _seed_primitives

    try:
        from seed_primitives import get_seed_primitives
        _seed_primitives = get_seed_primitives()
        _primitives_loaded = True
        if _seed_primitives is not None:
            logger.debug(f"[RUNG-PRIMITIVES] Loaded {_seed_primitives.count()} seed primitives")
    except ImportError as e:
        logger.debug(f"[RUNG-PRIMITIVES] seed_primitives not available: {e}")
        _primitives_loaded = True
        _seed_primitives = None


# =============================================================================
# DEPRECATION TRACKING - Phase 6 (Cognitive Routing Migration)
# =============================================================================
import warnings

# Track deprecation warnings to avoid spamming
_deprecation_warned: Dict[str, bool] = {}

def _warn_ordering_deprecated(ordering_name: str, suppress_if_cognitive: bool = False) -> None:
    """Warn that static ORDERING_PRESETS are deprecated.

    Phase 6.1: Mark static orderings as deprecated in favor of cognitive routing.
    - Phase 6.1a: Emit deprecation warnings (current)
    - Phase 6.1b: Log to database for tracking
    - Phase 6.1c: Remove in v3.0

    Args:
        ordering_name: Name of the ordering preset
        suppress_if_cognitive: If True, don't warn (COGNITIVE strategy uses rungs differently)
    """
    global _deprecation_warned

    # COGNITIVE strategy initializes rungs but uses graph-based selection
    # Don't warn since it's using the architecture correctly
    if suppress_if_cognitive:
        return

    # Only warn once per ordering per session
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


def filter_available_actions(actions: List[str], context: Dict[str, Any]) -> List[str]:
    """Filter action list to only those available in current game state.

    Args:
        actions: List of action strings like ['ACTION1', 'ACTION2', 'ACTION6']
        context: Decision context containing 'available_actions' as list of ints

    Returns:
        Filtered list containing only available actions
    """
    available = context.get('available_actions', [1, 2, 3, 4, 5, 6, 7])
    if not available:
        return actions

    # Convert available ints to action strings
    available_strs = {f'ACTION{a}' for a in available}

    # Filter to only available actions
    filtered = [a for a in actions if a in available_strs]

    # If nothing left after filtering, return all available as fallback
    if not filtered:
        return [f'ACTION{a}' for a in available]

    return filtered


# =============================================================================
# ACTION6 COORDINATE SYSTEM - Innate Understanding
# =============================================================================
# ACTION6 is fundamentally different from ACTION1-5. It's a PARAMETERIZED action
# that requires explicit (x, y) coordinates. Think of it as:
#   - ACTION1-5: "Move/interact in this direction" (no params needed)
#   - ACTION6: "Touch/click THIS SPECIFIC PIXEL at (x, y)" (requires coordinates)
#
# This is analogous to the difference between "walk forward" and "teleport to (x,y)".
# Every part of the system that can produce ACTION6 MUST provide coordinates.
# =============================================================================

class Action6CoordinateProvider:
    """
    Centralized provider for ACTION6 coordinates.

    This class encapsulates the "innate understanding" that ACTION6 requires
    coordinates. It provides multiple strategies for obtaining coordinates
    based on available information.

    Coordinate System (64x64 grid):
        (0,0) ─────────────────── (63,0)
          │                          │
          │      Y increases ↓       │
          │      X increases →       │
          │                          │
        (0,63) ─────────────────── (63,63)
    """

    @staticmethod
    def get_coordinates(
        context: Dict[str, Any],
        engines: Optional[Any] = None,
        frame: Optional[List[List[int]]] = None
    ) -> Dict[str, Any]:
        """
        Get coordinates for ACTION6 using the best available strategy.

        Priority order:
        1. Detected interactive objects (pseudobuttons, selectable shapes)
        2. Grid exploration targets (systematic search)
        3. Visually interesting regions (color analysis)
        4. Random valid position (fallback)

        Args:
            context: Decision context with game state
            engines: EngineRegistry for accessing visual_analyzer, action6_behavior
            frame: Current game frame (64x64 grid)

        Returns:
            Dict with 'x', 'y', and 'source' keys
        """
        game_type = context.get('game_type', '')
        level = context.get('level', 1)

        # Strategy 1: Try to get detected objects/pseudobuttons
        if engines:
            try:
                a6e = engines.action6_behavior
                if a6e and hasattr(a6e, 'get_untried_objects_for_frontier'):
                    tried_colors = context.get('tried_colors', [])
                    objects = a6e.get_untried_objects_for_frontier(
                        game_type=game_type, level=level,
                        frame=frame, tried_colors=tried_colors
                    )
                    if objects:
                        obj = objects[0]
                        return {
                            'x': obj.get('center_x', obj.get('x', 32)),
                            'y': obj.get('center_y', obj.get('y', 32)),
                            'source': 'detected_object',
                            'target_object': obj
                        }
            except Exception:
                pass

            # Strategy 2: Grid exploration targets
            try:
                va = engines.visual_analyzer
                if va and hasattr(va, 'get_grid_exploration_targets'):
                    targets = va.get_grid_exploration_targets()
                    if targets:
                        target = targets[0]
                        return {
                            'x': target.get('x', 32),
                            'y': target.get('y', 32),
                            'source': 'grid_exploration',
                            'grid_target': target
                        }
            except Exception:
                pass

        # Strategy 3: Frame analysis for interesting regions
        if frame:
            try:
                coords = Action6CoordinateProvider._find_interesting_region(frame)
                if coords:
                    return {**coords, 'source': 'frame_analysis'}
            except Exception:
                pass

        # Strategy 4: Random valid position
        return {
            'x': random.randint(4, 60),
            'y': random.randint(4, 60),
            'source': 'random_fallback'
        }

    @staticmethod
    def _find_interesting_region(frame: List[List[int]]) -> Optional[Dict[str, int]]:
        """
        Find visually interesting regions in the frame.

        Looks for:
        - Non-background colors (not 0)
        - Color clusters (multiple adjacent pixels of same color)
        - Centers of colored regions

        Returns:
            Dict with 'x', 'y' or None if no interesting regions found
        """
        if not frame or len(frame) < 64:
            return None

        # Find all non-background pixels
        interesting_points: List[Tuple[int, int, int]] = []  # (x, y, color)
        for y, row in enumerate(frame):
            for x, pixel in enumerate(row):
                if pixel != 0:  # Non-background
                    interesting_points.append((x, y, pixel))

        if not interesting_points:
            return None

        # Group by color and find cluster centers
        color_groups: Dict[int, List[Tuple[int, int]]] = {}
        for x, y, color in interesting_points:
            if color not in color_groups:
                color_groups[color] = []
            color_groups[color].append((x, y))

        # Find the largest non-background group
        largest_group = max(color_groups.values(), key=len)

        # Return centroid of largest group
        avg_x = sum(p[0] for p in largest_group) // len(largest_group)
        avg_y = sum(p[1] for p in largest_group) // len(largest_group)

        return {'x': avg_x, 'y': avg_y}

    @staticmethod
    def enrich_result_with_coordinates(
        result: "RungResult",
        context: Dict[str, Any],
        engines: Optional[Any] = None,
        frame: Optional[List[List[int]]] = None
    ) -> "RungResult":
        """
        Ensure a RungResult for ACTION6 has coordinates.

        This is the "safety net" - if any rung returns ACTION6 without
        coordinates, this method adds them.

        Args:
            result: The RungResult to potentially enrich
            context: Decision context
            engines: EngineRegistry
            frame: Current game frame

        Returns:
            The result, potentially with coordinates added to metadata
        """
        if result.action != 'ACTION6':
            return result

        # Check if coordinates already exist
        metadata = result.metadata or {}
        has_coords = (
            ('x' in metadata and 'y' in metadata) or
            'pixel_position' in metadata or
            'target' in metadata or
            'grid_target' in metadata
        )

        if has_coords:
            return result

        # Need to add coordinates
        coords = Action6CoordinateProvider.get_coordinates(context, engines, frame)
        new_metadata = {**metadata, **coords}
        return RungResult(
            action=result.action,
            confidence=result.confidence,
            reason=result.reason + f" [coords added: ({coords['x']},{coords['y']})]",
            weights=result.weights,
            metadata=new_metadata,
            provenance=result.provenance
        )

    @staticmethod
    def is_action6_game(context: Dict[str, Any]) -> bool:
        """Check if ACTION6 is the only available action (click-only game)."""
        available = context.get('available_actions', [1, 2, 3, 4, 5, 6, 7])
        return available == [6]

    @staticmethod
    def action6_available(context: Dict[str, Any]) -> bool:
        """Check if ACTION6 is available."""
        available = context.get('available_actions', [1, 2, 3, 4, 5, 6, 7])
        return 6 in available


def get_random_available_action(context: Dict[str, Any]) -> str:
    """Get a random action from available actions in context."""
    available = context.get('available_actions', [1, 2, 3, 4])
    return f'ACTION{random.choice(available)}'


def get_available_action_weights(context: Dict[str, Any], default_weight: float = 1.0) -> Dict[str, float]:
    """Get a weights dict initialized to default_weight for all available actions only.

    Args:
        context: Decision context containing 'available_actions' as list of ints
        default_weight: Initial weight for each action (default 1.0)

    Returns:
        Dict like {'ACTION1': 1.0, 'ACTION2': 1.0, ...} for available actions only
    """
    available = context.get('available_actions', [1, 2, 3, 4, 5, 6, 7])
    return {f'ACTION{a}': default_weight for a in available}


def get_available_actions_list(context: Dict[str, Any]) -> List[str]:
    """Get list of available action strings from context.

    Returns:
        List like ['ACTION1', 'ACTION2', 'ACTION3', 'ACTION4'] for available actions
    """
    available = context.get('available_actions', [1, 2, 3, 4, 5, 6, 7])
    return [f'ACTION{a}' for a in available]


def is_action_available(action: Optional[str], context: Dict[str, Any]) -> bool:
    """Check if an action string is in the available actions for this game.

    Args:
        action: Action string like 'ACTION6' or None
        context: Decision context containing 'available_actions'

    Returns:
        True if action is available (or action is None), False otherwise
    """
    if action is None:
        return True  # None is always "available" (means no suggestion)
    if not isinstance(action, str) or not action.startswith('ACTION'):
        return False
    try:
        action_num = int(action.replace('ACTION', ''))
        available = context.get('available_actions', [])
        if not available:
            return True  # No availability info = assume available
        # Support both string format ("ACTION1") and int format (1)
        # game_loop.py stores strings, evolution_runner.py stores ints
        return action in available or action_num in available
    except (ValueError, TypeError):
        return False


def validate_action(action: Optional[str], context: Dict[str, Any]) -> Optional[str]:
    """Validate an action and return it if available, None otherwise.

    Use this to filter out unavailable actions before returning from rungs.
    """
    if is_action_available(action, context):
        return action
    return None


class DecisionStrategy(Enum):
    """How to combine rung outputs"""
    LADDER = "ladder"           # First confident answer wins
    WEIGHTED = "weighted"       # All rungs vote, weighted sum
    PHASED = "phased"           # Different ordering by phase
    PARALLEL = "parallel"       # Run all, pick highest confidence
    CONTEXT_ADAPTIVE = "context_adaptive"  # Select strategy based on context (frontier/replay/optimization)
    COGNITIVE = "cognitive"     # Transition-driven cognitive routing (Phase 4)


@dataclass
class KnowledgeProvenance:
    """Tracks HOW knowledge became knowable - epistemological provenance.

    From 'Simultaneous Learning' theory: "Amplification != Validity"
    We need to distinguish between 'frequently tried' and 'actually validated'.

    Stages (from Knowledge Crystallization Pipeline):
    - detection: How was this pattern first identified?
    - classification: How was it named/bounded?
    - amplification: What drove its spread? (frequency vs outcome-based)
    - normalization: Is this now assumed/foundational knowledge?
    """
    # Detection metadata
    detection_source: str = "unknown"  # e.g., 'action_traces', 'winning_sequences', 'hypothesis'
    sample_size: int = 0               # How many data points support this
    agent_diversity: int = 0           # How many different agents/sessions contributed
    temporal_spread_generations: float = 0.0  # Generation spread of observations (hardware-agnostic)

    # Validation metadata
    validation_type: str = "frequency"  # 'frequency', 'outcome_based', 'win_validated', 'cross_game'
    positive_outcomes: int = 0          # Actions that led to good results
    negative_outcomes: int = 0          # Actions that led to bad results (deaths, etc.)

    # Crystallization stage (0-4 from the pipeline)
    crystallization_stage: int = 1     # 1=detected, 2=classified, 3=amplified, 4=normalized

    # Resonance (cross-domain validation)
    resonance_games: int = 0           # How many different games show similar pattern
    resonance_score: float = 0.0       # Structural similarity across domains (0-1)

    def validity_score(self) -> float:
        """Calculate validity score - separating 'widely known' from 'actually true'.

        High frequency + low outcome validation = potentially inflated
        Moderate frequency + high outcome validation = likely valid
        Cross-game resonance = strong structural truth
        """
        # Base: outcome ratio
        total_outcomes = self.positive_outcomes + self.negative_outcomes
        outcome_ratio = self.positive_outcomes / max(1, total_outcomes)

        # Diversity bonus: knowledge from many sources is more reliable
        diversity_factor = min(1.0, self.agent_diversity / 5.0)

        # Temporal spread bonus: patterns observed across many generations are more valid
        temporal_factor = min(1.0, self.temporal_spread_generations / 20.0)  # Cap at 20 gens

        # Resonance bonus: cross-game patterns are structural truths
        resonance_factor = self.resonance_score * 0.5

        # Validation type multiplier
        validation_multiplier = {
            'frequency': 0.5,      # Just "tried often" - lowest validity
            'outcome_based': 0.8,  # Validated by outcomes
            'win_validated': 1.0,  # Part of winning sequence
            'cross_game': 1.2,     # Resonates across games - highest
        }.get(self.validation_type, 0.5)

        return min(1.0, (
            outcome_ratio * 0.4 +
            diversity_factor * 0.2 +
            temporal_factor * 0.1 +
            resonance_factor * 0.3
        ) * validation_multiplier)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'detection_source': self.detection_source,
            'sample_size': self.sample_size,
            'agent_diversity': self.agent_diversity,
            'temporal_spread_generations': self.temporal_spread_generations,
            'validation_type': self.validation_type,
            'positive_outcomes': self.positive_outcomes,
            'negative_outcomes': self.negative_outcomes,
            'crystallization_stage': self.crystallization_stage,
            'resonance_games': self.resonance_games,
            'resonance_score': self.resonance_score,
            'validity_score': self.validity_score(),
        }


@dataclass
class RungResult:
    """Standard output from a decision rung"""
    action: Optional[str] = None          # e.g., "ACTION1" or None if no suggestion
    confidence: float = 0.0               # 0.0 to 1.0
    reason: str = ""                      # Human-readable explanation
    weights: Optional[Dict[str, float]] = None  # Per-action weights (for graduated systems)
    metadata: Dict[str, Any] = field(default_factory=lambda: {})  # Extra info for debugging
    primitives_used: List[str] = field(default_factory=lambda: [])  # Which primitives contributed
    provenance: Optional[KnowledgeProvenance] = None  # HOW this knowledge became knowable

    def has_suggestion(self, threshold: float = 0.0) -> bool:
        return self.action is not None and self.confidence > threshold

    def adjusted_confidence(self) -> float:
        """Confidence adjusted by provenance validity - prevents 'amplification != validity' trap."""
        if self.provenance is None:
            return self.confidence
        return self.confidence * self.provenance.validity_score()


class DecisionRung(ABC):
    """
    Base class for all decision rungs.
    Each rung evaluates the current state and optionally suggests an action.

    PRIMITIVE INTEGRATION:
    Rungs can declare `required_primitives` to access seed primitives.
    The primitive registry is loaded lazily to avoid circular imports.

    Example:
        class MyRung(DecisionRung):
            required_primitives = ['detect_novelty', 'get_confidence']

            def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
                novelty = self.call_primitive('detect_novelty', game_state.frame)
                conf = self.call_primitive('get_confidence')
                ...
    """

    # Class-level metadata
    name: str = "base_rung"
    category: str = "unknown"  # orientation, hypothesis, exploitation, filter, emergency
    default_priority: int = 50  # 1=highest priority, 100=lowest
    confidence_threshold: float = 0.3  # Minimum confidence to "win" in ladder mode

    # Primitive requirements (override in subclasses)
    required_primitives: List[str] = []  # e.g., ['detect_novelty', 'get_confidence']

    def __init__(
        self,
        core_gameplay_ref: Any = None,
        engine_registry: Optional["EngineRegistry"] = None
    ):
        """
        Args:
            core_gameplay_ref: Reference to CoreGameplay instance (legacy)
            engine_registry: EngineRegistry for modular engine access (preferred)
        """
        self.core: Any = core_gameplay_ref
        self._engine_registry: Optional["EngineRegistry"] = engine_registry
        self.enabled = True
        self.priority_override: Optional[int] = None
        self.stats: Dict[str, Any] = {
            'calls': 0,
            'suggestions': 0,
            'accepted': 0,
            'avg_confidence': 0.0
        }

        # Lazy-load primitives
        self._primitives = None
        self._primitives_validated = False

    @property
    def engines(self) -> "EngineRegistry":
        """
        Access modular engines via registry.

        Falls back to creating a registry from self.core if not provided.
        This allows gradual migration from self.core.X to self.engines.X
        """
        if self._engine_registry is not None:
            return self._engine_registry

        # Lazy-create registry from legacy core
        if self.core is not None:
            from engines.registry import EngineRegistry
            self._engine_registry = EngineRegistry(legacy_core=self.core)
        else:
            # Return a minimal registry with stubs
            from engines.registry import EngineRegistry
            self._engine_registry = EngineRegistry()

        return self._engine_registry

    def _ensure_primitives(self) -> bool:
        """Ensure primitives are loaded and validated."""
        if self._primitives_validated:
            return self._primitives is not None

        self._primitives = _load_primitives()
        self._primitives_validated = True

        # Validate required primitives
        if self.required_primitives and self._primitives:
            missing: List[str] = []
            for name in self.required_primitives:
                if not self._primitives.get(name):
                    missing.append(name)
            if missing:
                logger.warning(f"[RUNG-{self.name}] Missing primitives: {missing}")

        return self._primitives is not None

    def call_primitive(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """
        Call a seed primitive by name.

        Args:
            name: Primitive name (e.g., 'detect_novelty')
            *args, **kwargs: Arguments to pass to the primitive

        Returns:
            Primitive result, or None if primitive not available
        """
        if not self._ensure_primitives() or self._primitives is None:
            return None

        try:
            primitive = self._primitives.get(name)
            if primitive and hasattr(primitive, 'execute'):
                return primitive.execute(*args, **kwargs)
            elif primitive and callable(getattr(primitive, 'func', None)):
                return primitive.func(*args, **kwargs)
        except Exception as e:
            logger.debug(f"[RUNG-{self.name}] Primitive {name} failed: {e}")

        return None

    def has_primitive(self, name: str) -> bool:
        """Check if a primitive is available."""
        if not self._ensure_primitives() or self._primitives is None:
            return False
        return self._primitives.get(name) is not None

    @abstractmethod
    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        """
        Evaluate this rung and return a result.

        Args:
            game_state: Current game state (frame, score, etc.)
            context: Additional context (agent info, level info, etc.)

        Returns:
            RungResult with optional action suggestion
        """
        pass

    def get_priority(self) -> int:
        """Return current priority (considering override)"""
        return self.priority_override if self.priority_override is not None else self.default_priority

    def record_outcome(self, was_accepted: bool, outcome_score: float = 0.0):
        """Record whether this rung's suggestion was used and how it went"""
        self.stats['calls'] += 1
        if was_accepted:
            self.stats['accepted'] += 1
        # Rolling average of confidence
        n = self.stats['calls']
        self.stats['avg_confidence'] = (self.stats['avg_confidence'] * (n-1) + outcome_score) / n


# =============================================================================
# CONCRETE RUNG IMPLEMENTATIONS
# Each wraps an existing feature from core_gameplay.py
# =============================================================================

class SurveyRung(DecisionRung):
    """Survey the environment at level start - ORIENTATION

    Uses grid_analyzer engine to analyze frame and build survey context.
    Identifies objects, colors, and grid structure for the agent's world model.
    """
    name = "survey"
    category = "orientation"
    default_priority = 5
    confidence_threshold = 0.0  # Always runs, modifies context not action

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        # Check if survey already done for this level
        if context.get('survey_complete', False):
            return RungResult(confidence=0.0, reason="Survey already complete")

        # Build survey context using grid_analyzer
        try:
            survey: Dict[str, Any] = self._build_survey_context(game_state, context)
            context['survey'] = survey
            context['survey_complete'] = True
            return RungResult(
                confidence=0.1,  # Low confidence - doesn't suggest action, just observes
                reason=f"Survey complete: {len(survey.get('detected_features', {}))} features detected",
                metadata={'survey': survey}
            )
        except Exception as e:
            return RungResult(reason=f"Survey failed: {e}")

    def _build_survey_context(self, game_state: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build survey context from frame analysis using grid_analyzer."""
        survey: Dict[str, Any] = {
            'detected_features': {},
            'unique_colors': set(),
            'object_count': 0,
            'grid_size': (0, 0),
            'has_boundary': False
        }

        # Get frame from game_state
        frame = None
        if hasattr(game_state, 'frame'):
            frame = game_state.frame
        elif hasattr(game_state, 'observation'):
            obs = game_state.observation
            if isinstance(obs, dict) and 'frame' in obs:
                frame = obs['frame']

        if frame is None:
            return survey

        # Convert numpy array to list if needed
        if hasattr(frame, 'tolist'):
            frame = frame.tolist()

        # Analyze grid structure
        if isinstance(frame, list) and len(frame) > 0:
            survey['grid_size'] = (len(frame), len(frame[0]) if frame else 0)

            # Find unique colors and objects
            colors: set = set()
            object_positions: Dict[int, List[tuple]] = {}

            for y, row in enumerate(frame):
                for x, color in enumerate(row):
                    if color > 0:  # Non-background
                        colors.add(color)
                        if color not in object_positions:
                            object_positions[color] = []
                        object_positions[color].append((y, x))

            survey['unique_colors'] = colors
            survey['object_count'] = len(object_positions)

            # Detect features for each color
            for color, positions in object_positions.items():
                feature = {
                    'color': color,
                    'pixel_count': len(positions),
                    'positions': positions[:10],  # Sample for memory
                    'is_single': len(positions) <= 4,
                    'is_large': len(positions) > 20
                }

                # Check if on boundary (potential boundary marker)
                boundary_positions = [p for p in positions if p[0] == 0 or p[1] == 0
                                      or p[0] == len(frame) - 1 or p[1] == len(frame[0]) - 1]
                if len(boundary_positions) > len(positions) * 0.5:
                    feature['likely_boundary'] = True
                    survey['has_boundary'] = True

                survey['detected_features'][f'color_{color}'] = feature

        # Try to use grid_analyzer for more sophisticated analysis
        grid_analyzer = self.engines.grid_analyzer
        if grid_analyzer and frame:
            try:
                if hasattr(grid_analyzer, 'analyze_grid_structure'):
                    analysis = grid_analyzer.analyze_grid_structure(frame)
                    survey['grid_analysis'] = analysis
            except Exception:
                pass  # Grid analyzer enhancement is optional

        return survey


class QuestioningRung(DecisionRung):
    """Q1-Q9 questioning engine - can BLOCK actions - ORIENTATION"""
    name = "questioning_engine"
    category = "orientation"
    default_priority = 10
    confidence_threshold = 0.5

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        sme = self.engines.scientific_method_engine
        if sme is None:
            return RungResult()

        try:
            if not hasattr(sme, 'questioning_engine'):
                return RungResult()

            qe = sme.questioning_engine
            blocking_questions: List[Any] = qe.get_blocking_questions() if hasattr(qe, 'get_blocking_questions') else []

            if blocking_questions:
                # Q4, Q9, or META is blocking - force specific action types
                allowed_actions = qe.get_allowed_actions(blocking_questions)
                return RungResult(
                    action=random.choice(allowed_actions) if allowed_actions else None,
                    confidence=0.8,
                    reason=f"Blocked by questions: {blocking_questions}",
                    metadata={'blocking_questions': blocking_questions, 'allowed': allowed_actions}
                )
            return RungResult(confidence=0.0)
        except Exception as e:
            return RungResult(reason=f"Questioning failed: {e}")


class DeathAvoidanceRung(DecisionRung):
    """Position-bucket death pattern avoidance - FILTER (modifies weights)"""
    name = "death_avoidance"
    category = "filter"
    default_priority = 15
    confidence_threshold = 0.6

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        detector = self.engines.terminal_pattern_detector
        if detector is None:
            return RungResult()

        try:
            # Get graduated weights from terminal pattern detector
            if hasattr(detector, 'get_graduated_action_weights'):
                game_type = context.get('game_type', '')
                level = context.get('level', 1)
                position = context.get('position', (0, 0))
                frontier_mode = context.get('frontier_mode', False)

                weights = detector.get_graduated_action_weights(
                    game_type=game_type,
                    level=level,
                    position=position,
                    frontier_mode=frontier_mode
                )

                # Find most dangerous action
                min_weight = min(weights.values()) if weights else 1.0
                dangerous_actions = [a for a, w in weights.items() if w < 0.3]

                return RungResult(
                    confidence=0.7 if dangerous_actions else 0.1,
                    reason=f"Danger weights calculated, {len(dangerous_actions)} risky actions",
                    weights=weights,
                    metadata={'dangerous_actions': dangerous_actions, 'min_weight': min_weight}
                )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Death avoidance failed: {e}")


class PriorLessonsRung(DecisionRung):
    """Apply prior game lessons as graduated action weights - FILTER

    Converts lessons from game_lessons_learned table into safety weights.
    Lessons with caused_death=True heavily penalize their key_action.
    Lessons from wins boost their key_action.

    This closes the "last mile" gap where lessons were collected but never
    used in action selection.
    """
    name = "prior_lessons"
    category = "filter"
    default_priority = 16  # Right after death_avoidance (15)
    confidence_threshold = 0.3

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        try:
            # Get prior lessons from context (loaded by evolution runner)
            prior_lessons = context.get('prior_lessons', [])
            if not prior_lessons:
                return RungResult()

            # Initialize weights at 1.0 for AVAILABLE actions only
            weights = get_available_action_weights(context, 1.0)
            lessons_applied = 0

            for idx, lesson in enumerate(prior_lessons[:10]):  # Max 10 lessons
                key_action = lesson.get('key_action', '')
                if not key_action or not key_action.startswith('ACTION'):
                    continue

                confidence = lesson.get('confidence', 0.5)
                caused_death = lesson.get('caused_death', False)
                from_win = lesson.get('from_win', False)
                severity = lesson.get('severity', 1)
                occurrence = lesson.get('occurrence_count', 1)

                # Recency factor: earlier lessons in list are more recent/salient
                recency_factor = 1.0 - (idx * 0.05)

                if caused_death:
                    # Death lessons reduce weight significantly
                    # Formula: severity (1-3) * confidence * recency
                    penalty = min(0.9, severity * 0.25 * confidence * recency_factor)
                    weights[key_action] *= max(0.05, 1.0 - penalty)
                    lessons_applied += 1
                elif from_win:
                    # Win lessons boost the action
                    boost = min(0.5, 0.15 * confidence * recency_factor * min(occurrence, 5))
                    weights[key_action] = min(1.5, weights[key_action] * (1.0 + boost))
                    lessons_applied += 1
                else:
                    # Neutral lessons: slight penalty for failures
                    penalty = min(0.3, 0.1 * confidence * recency_factor)
                    weights[key_action] *= max(0.7, 1.0 - penalty)
                    lessons_applied += 1

            if lessons_applied == 0:
                return RungResult()

            # Find penalized actions
            penalized = [a for a, w in weights.items() if w < 0.7]
            boosted = [a for a, w in weights.items() if w > 1.0]

            return RungResult(
                confidence=min(0.8, 0.3 + lessons_applied * 0.05),
                reason=f"Prior lessons: {lessons_applied} applied, {len(penalized)} penalized, {len(boosted)} boosted",
                weights=weights,
                metadata={
                    'lessons_applied': lessons_applied,
                    'penalized_actions': penalized,
                    'boosted_actions': boosted
                }
            )
        except Exception as e:
            return RungResult(reason=f"Prior lessons failed: {e}")


class DiscoveryExploitationRung(DecisionRung):
    """Exploit recent discoveries immediately - EXPLOITATION

    Uses discovery_engine to get current discovery state and suggest actions
    that exploit what the agent has learned about object behaviors.
    """
    name = "discovery_exploitation"
    category = "exploitation"
    default_priority = 20
    confidence_threshold = 0.3

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        discovery_engine = self.engines.discovery_engine
        if discovery_engine is None:
            return RungResult()

        try:
            # Get current discovery state from the engine
            discovery_state = discovery_engine.get_state() if hasattr(discovery_engine, 'get_state') else None

            if not discovery_state:
                # Also check context for discovery info from evolution runner
                discovery = context.get('last_discovery')
                if not discovery:
                    return RungResult()
            else:
                # Extract discovery info from state
                discoveries = discovery_state.discoveries if hasattr(discovery_state, 'discoveries') else {}
                if not discoveries:
                    return RungResult()

                # Find the most recently discovered controllable object
                discovery = None
                for obj_id, behavior in discoveries.items():
                    if str(behavior) == 'ObjectBehavior.PLAYER_CONTROLLED':
                        discovery = {
                            'controlled_object': obj_id,
                            'behavior': str(behavior),
                            'reliability_score': 0.8,
                            'validated': True,
                            'action': 'ACTION1'  # Movement discovery suggests movement
                        }
                        break

                if not discovery:
                    return RungResult()

            action = discovery.get('action', '')
            reliability = discovery.get('reliability_score', 0.0)
            validated = discovery.get('validated', False)

            if not action.startswith('ACTION'):
                return RungResult()

            # CRITICAL: Validate action is available in this game
            if not is_action_available(action, context):
                return RungResult(reason=f"Discovery action {action} not available")

            if reliability >= 0.6 or validated:
                obj_info = discovery.get('controlled_object', discovery.get('controlled_color', '?'))
                return RungResult(
                    action=action,
                    confidence=0.9,
                    reason=f"Exploiting discovery: {obj_info} (rel={reliability:.2f})",
                    metadata={'discovery': discovery}
                )
            elif reliability >= 0.3:
                obj_info = discovery.get('controlled_object', discovery.get('controlled_color', '?'))
                return RungResult(
                    action=action,
                    confidence=0.5,
                    reason=f"Testing hypothesis: {obj_info} (rel={reliability:.2f})",
                    metadata={'discovery': discovery}
                )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Discovery exploitation failed: {e}")


class EmbeddingSuggestionRung(DecisionRung):
    """Cross-game neural similarity matching - EXPLOITATION"""
    name = "embedding_suggestion"
    category = "exploitation"
    default_priority = 25
    confidence_threshold = 0.7

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        sm = self.engines.self_model
        if sm is None:
            return RungResult()

        try:
            suggestion = sm.get_embedding_suggested_action(
                game_type=None,  # Search all games
                level=None,
                current_frame=game_state.frame if hasattr(game_state, 'frame') else None,
                top_k=10
            )

            if suggestion and suggestion.get('confidence', 0) >= self.confidence_threshold:
                action = suggestion.get('action')
                # CRITICAL: Validate action is available in this game
                if is_action_available(action, context):
                    return RungResult(
                        action=action,
                        confidence=suggestion.get('confidence', 0),
                        reason=f"Embedding match: {suggestion.get('similar_count', 0)} similar frames",
                        metadata={'suggestion': suggestion}
                    )

            # Even below threshold, return as weighted boost
            if suggestion and suggestion.get('confidence', 0) >= 0.4:
                suggested_action = suggestion.get('action')
                # CRITICAL: Validate action is available in this game
                if suggested_action and is_action_available(suggested_action, context):
                        return RungResult(
                            confidence=suggestion.get('confidence', 0),
                            weights={suggested_action: 1.0 + suggestion.get('confidence', 0) * 0.5},
                            reason=f"Embedding boost (below threshold): conf={suggestion.get('confidence', 0):.2f}",
                            metadata={'suggestion': suggestion}
                        )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Embedding suggestion failed: {e}")


class ScientificMethodRung(DecisionRung):
    """Theory formation and testing - HYPOTHESIS"""
    name = "scientific_method"
    category = "hypothesis"
    default_priority = 12
    confidence_threshold = 0.4

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        sme = self.engines.scientific_method_engine
        if sme is None:
            return RungResult()

        try:
            theory_stage = sme.get_theory_stage() if hasattr(sme, 'get_theory_stage') else 'exploring'

            if theory_stage == 'contradicted':
                # Force exploration/revision using available movement actions
                exploration_actions = filter_available_actions(
                    ['ACTION1', 'ACTION2', 'ACTION3', 'ACTION4'], context
                )
                return RungResult(
                    action=random.choice(exploration_actions),
                    confidence=0.7,
                    reason=f"Theory contradicted - forcing exploration",
                    metadata={'theory_stage': theory_stage}
                )
            elif theory_stage == 'speculating':
                # Boost exploration using available movement actions
                movement_actions = filter_available_actions(
                    ['ACTION1', 'ACTION2', 'ACTION3', 'ACTION4'], context
                )
                return RungResult(
                    confidence=0.3,
                    weights={a: 1.2 for a in movement_actions},  # Boost available movement
                    reason=f"Speculating - exploration boosted",
                    metadata={'theory_stage': theory_stage}
                )
            return RungResult(metadata={'theory_stage': theory_stage})
        except Exception as e:
            return RungResult(reason=f"Scientific method failed: {e}")


class TwoStreamsRung(DecisionRung):
    """Stream A (private) vs Stream B (network) conflict detection - HYPOTHESIS

    Implements the two-stream consciousness model from the unified theory:
    - Stream A: Private memory (agent's personal experience)
    - Stream B: Collective wisdom (network knowledge)

    Uses i_thread engine for stream weights (wA, wB).
    """
    name = "two_streams"
    category = "hypothesis"
    default_priority = 30
    confidence_threshold = 0.4

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        i_thread = self.engines.i_thread
        agent_id = context.get('agent_id', '')

        # Default weights if i_thread not available
        wA, wB = 0.5, 0.5

        try:
            if i_thread and agent_id:
                state = i_thread.get_state(agent_id)
                if state:
                    wA = state.w_a
                    wB = state.w_b

            stream_a_actions = context.get('stream_a_proposals', set())
            stream_b_actions = context.get('stream_b_proposals', set())

            conflict = stream_a_actions and stream_b_actions and stream_a_actions != stream_b_actions

            if conflict:
                # Conflict = learning signal
                return RungResult(
                    confidence=0.5,
                    reason=f"Stream conflict: A={stream_a_actions}, B={stream_b_actions}, wA={wA:.2f}",
                    metadata={'conflict': True, 'wA': wA, 'wB': wB, 'stream_a': list(stream_a_actions), 'stream_b': list(stream_b_actions)}
                )
            return RungResult(metadata={'conflict': False, 'wA': wA, 'wB': wB})
        except Exception as e:
            return RungResult(reason=f"Two streams failed: {e}")


class NetworkWisdomRung(DecisionRung):
    """Query network-wide action wisdom from action traces - EXPLOITATION

    This is Stream B (collective wisdom) in the two-stream model.
    Queries action_traces and winning_sequences to find what worked across all agents.

    Uses engines.memory.episodic_memory.EpisodicMemory for database queries.
    """
    name = "network_wisdom"
    category = "exploitation"
    default_priority = 35
    confidence_threshold = 0.4

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        # Use episodic_memory engine to query network wisdom
        episodic = self.engines.episodic_memory
        if episodic is None:
            return RungResult()

        try:
            game_type = context.get('game_type', '')
            available = context.get('available_actions', [1, 2, 3, 4, 5, 6, 7])

            # Query network wisdom for each available action
            best_action = None
            best_confidence = 0.0
            best_reason = ""

            for action_num in available:
                action_name = f"ACTION{action_num}"
                if hasattr(episodic, '_get_network_action_wisdom'):
                    wisdom = episodic._get_network_action_wisdom(game_type, action_name)
                    if wisdom.get('recommendation') == 'use':
                        conf = wisdom.get('confidence', 0)
                        if conf > best_confidence:
                            best_confidence = conf
                            best_action = action_name
                            best_reason = wisdom.get('reasoning', '')

            if best_action and best_confidence >= self.confidence_threshold:
                return RungResult(
                    action=best_action,
                    confidence=best_confidence,
                    reason=f"Network wisdom: {best_action} ({best_reason})",
                    metadata={'source': 'episodic_memory'}
                )

            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Network wisdom failed: {e}")


class PrimitiveSuggesterRung(DecisionRung):
    """Primitive-based action suggestions - EXPLOITATION

    Simplified replacement for CODS. Applies seed primitives to frames
    and maps outputs to action suggestions with RLVR feedback.

    Uses engines.social.primitive_suggester.PrimitiveSuggester for actual
    primitive-to-action mapping with RLVR feedback.
    """
    name = "primitive_suggester"
    category = "exploitation"
    default_priority = 40
    confidence_threshold = 0.35

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._suggester: Optional[Any] = None

    def _get_suggester(self) -> Optional[Any]:
        """Get or create PrimitiveSuggester instance."""
        if self._suggester is None:
            try:
                from database_interface import DatabaseInterface
                from engines.social.primitive_suggester import PrimitiveSuggester
                db = DatabaseInterface()
                self._suggester = PrimitiveSuggester(db)
            except ImportError as e:
                logger.debug(f"[RUNG-PRIMITIVE] Failed to load PrimitiveSuggester: {e}")
        return self._suggester

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        suggester = self._get_suggester()
        if suggester is None:
            return RungResult()

        try:
            frame = getattr(game_state, 'frame', None)
            if frame is None:
                return RungResult()

            game_type = context.get('game_type') or context.get('game_id', '').split('-')[0]
            recent_actions = context.get('recent_actions', [])

            result = suggester.suggest_action(frame, game_type, recent_actions)

            if result and result.confidence >= self.confidence_threshold:
                action = f"ACTION{result.action}"
                # CRITICAL: Validate action is available in this game
                if not is_action_available(action, context):
                    return RungResult(reason=f"Primitive suggested unavailable action: {action}")
                return RungResult(
                    action=action,
                    confidence=result.confidence,
                    reason=f"Primitive: {result.primitive} - {result.reasoning}",
                    metadata={'primitive_result': result.to_dict()}
                )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Primitive suggester failed: {e}")


class MetacognitivePredictionRung(DecisionRung):
    """Make predictions, learn from errors - HYPOTHESIS"""
    name = "metacognitive_prediction"
    category = "hypothesis"
    default_priority = 18
    confidence_threshold = 0.3

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        # Use metacognitive_engine which has get_current_prediction()
        me = self.engines.metacognitive_engine
        if me is None:
            return RungResult()

        try:
            prediction = me.get_current_prediction() if hasattr(me, 'get_current_prediction') else None

            if prediction:
                action = prediction.get('test_action')
                # CRITICAL: Validate action is available in this game
                if action and is_action_available(action, context):
                    return RungResult(
                        action=action,
                        confidence=prediction.get('confidence', 0.3),
                        reason=f"Testing prediction: {prediction.get('hypothesis', '?')}",
                        metadata={'prediction': prediction}
                    )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Metacognitive prediction failed: {e}")


class ExplorationPhaseRung(DecisionRung):
    """Phase-based exploration forcing - ORIENTATION"""
    name = "exploration_phase"
    category = "orientation"
    default_priority = 22
    confidence_threshold = 0.5

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        try:
            budget_used = context.get('budget_used_percent', 0)
            coverage = context.get('coverage_percent', 0)

            # Discovery phase: 0-30% budget
            if budget_used < 0.3 and coverage < 0.3:
                exploration_actions = filter_available_actions(
                    ['ACTION1', 'ACTION2', 'ACTION3', 'ACTION4', 'ACTION6'], context
                )
                chosen_action = random.choice(exploration_actions)

                # If ACTION6 (click), provide coordinates from visual_analyzer
                metadata: Dict[str, Any] = {
                    'phase': 'discovery',
                    'budget_used': budget_used,
                    'coverage': coverage
                }
                if chosen_action == 'ACTION6':
                    # Try to get grid exploration targets for coordinates
                    va = self.engines.visual_analyzer if self.engines else None
                    if va and hasattr(va, 'get_grid_exploration_targets'):
                        targets = va.get_grid_exploration_targets()
                        if targets:
                            target = targets[0]
                            metadata['x'] = target.get('x', 32)
                            metadata['y'] = target.get('y', 32)
                            metadata['grid_target'] = target
                        else:
                            # Fallback: random position in 64x64 grid
                            metadata['x'] = random.randint(4, 60)
                            metadata['y'] = random.randint(4, 60)
                    else:
                        # No visual analyzer - use random position
                        metadata['x'] = random.randint(4, 60)
                        metadata['y'] = random.randint(4, 60)

                return RungResult(
                    action=chosen_action,
                    confidence=0.6,
                    reason=f"Discovery phase: budget={budget_used:.0%}, coverage={coverage:.0%}",
                    metadata=metadata
                )
            return RungResult(metadata={'phase': 'intermediate' if budget_used < 0.7 else 'final'})
        except Exception as e:
            return RungResult(reason=f"Exploration phase failed: {e}")


class FrontierTopologyRung(DecisionRung):
    """Network-level topology aggregation for frontier levels - EXPLOITATION

    Queries action_traces from ALL agents to build a collective map:
    - "From this frame_hash, what actions have been tried?"
    - "What were the outcomes (score_change, game_over)?"
    - Boost actions that led to positive outcomes
    - Penalize actions that led to death
    - Heavily boost UNTRIED actions (exploration bonus)

    This is the "whole point" - combining all agents' partial explorations
    into shared knowledge, even if no single agent has explored much.
    """
    name = "frontier_topology"
    category = "exploitation"
    default_priority = 28
    confidence_threshold = 0.3  # Can help even with sparse data

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        try:
            is_frontier = context.get('frontier_mode', False)
            if not is_frontier:
                return RungResult()

            # Get current frame hash from context
            frame_hash = context.get('frame_hash', '')
            if not frame_hash:
                return RungResult(reason="No frame_hash in context")

            game_type = context.get('game_type', '')
            level = context.get('level', 1)

            # Query network's collective knowledge for this exact frame
            db = None
            if self.engines:
                try:
                    db = self.engines._get_db_interface()
                except Exception:
                    pass
            if db is None:
                return RungResult(reason="No database connection")

            # Network-level topology: What has ANYONE tried from this frame?
            results = db.execute_query("""
                SELECT
                    action_number,
                    COUNT(*) as attempts,
                    SUM(CASE WHEN score_change > 0 THEN 1 ELSE 0 END) as positive_outcomes,
                    SUM(CASE WHEN resulted_in_game_over = 1 THEN 1 ELSE 0 END) as deaths,
                    AVG(score_change) as avg_score_change,
                    SUM(CASE WHEN frame_changed = 1 THEN 1 ELSE 0 END) as frame_changes,
                    COUNT(DISTINCT session_id) as unique_sessions,
                    MIN(created_at) as first_seen,
                    MAX(created_at) as last_seen
                FROM action_traces
                WHERE frame_hash = ?
                  AND game_id LIKE ?
                  AND level_number = ?
                  AND action_number BETWEEN 1 AND 7
                GROUP BY action_number
            """, (frame_hash, f"{game_type}%", level))

            # Initialize weights with EXPLORATION BONUS for untried actions (available only)
            weights = get_available_action_weights(context, 1.5)  # Start high - untried = bonus!
            tried_actions: Set[str] = set()
            total_data_points = 0
            best_action = None
            best_score = -999

            # Provenance tracking
            total_positive = 0
            total_negative = 0
            unique_sessions: Set[int] = set()
            first_seen = None
            last_seen = None

            if results:
                for row in results:
                    action = f"ACTION{row['action_number']}"
                    tried_actions.add(action)
                    attempts = row['attempts'] or 1
                    positive = row['positive_outcomes'] or 0
                    deaths = row['deaths'] or 0
                    avg_change = row['avg_score_change'] or 0
                    frame_changes = row['frame_changes'] or 0
                    total_data_points += attempts

                    # CRITICAL: Skip actions that aren't available in this game
                    if not is_action_available(action, context):
                        continue

                    # Track provenance data
                    total_positive += positive
                    total_negative += deaths
                    sessions = row.get('unique_sessions', 1) or 1
                    unique_sessions.add(sessions)  # Approximate - actual is per-action
                    if row.get('first_seen'):
                        if first_seen is None or row['first_seen'] < first_seen:
                            first_seen = row['first_seen']
                    if row.get('last_seen'):
                        if last_seen is None or row['last_seen'] > last_seen:
                            last_seen = row['last_seen']

                    # Calculate action quality
                    success_rate = positive / attempts if attempts > 0 else 0
                    death_rate = deaths / attempts if attempts > 0 else 0
                    movement_rate = frame_changes / attempts if attempts > 0 else 0

                    # Score: positive outcomes good, deaths bad, movement good
                    action_score = (
                        success_rate * 2.0 +      # Big bonus for score increases
                        avg_change * 0.5 +         # Bonus for positive score change
                        movement_rate * 0.3 -      # Small bonus for causing frame change
                        death_rate * 1.5           # Penalty for deaths
                    )

                    # Convert score to weight (0.1 to 1.3 range for tried actions)
                    # Tried actions lose the exploration bonus but gain knowledge bonus
                    weight = max(0.1, min(1.3, 0.7 + action_score))
                    weights[action] = weight

                    if action_score > best_score:
                        best_score = action_score
                        best_action = action

            # Count untried actions (still have exploration bonus of 1.5)
            untried_actions = [a for a in weights if a not in tried_actions]
            untried_count = len(untried_actions)

            # Calculate confidence based on data coverage
            coverage = len(tried_actions) / 7.0
            sample_confidence = min(1.0, total_data_points / 20.0)
            confidence = coverage * 0.6 + sample_confidence * 0.4

            # Build provenance - track HOW this knowledge became knowable
            # Generation spread: if we have generation data, use it; else estimate from timestamps
            temporal_generations = 0.0

            # Try to get generation spread from action_traces if available
            try:
                gen_results = db.execute_query("""
                    SELECT MIN(generation) as min_gen, MAX(generation) as max_gen
                    FROM action_traces
                    WHERE frame_hash = ?
                      AND game_id LIKE ?
                      AND level_number = ?
                      AND generation IS NOT NULL
                """, (frame_hash, f"{game_type}%", level))

                if gen_results and gen_results[0].get('min_gen') is not None:
                    min_gen = gen_results[0]['min_gen']
                    max_gen = gen_results[0]['max_gen']
                    temporal_generations = float(max_gen - min_gen)
            except Exception:
                pass  # Generation column may not exist yet

            provenance = KnowledgeProvenance(
                detection_source='action_traces',
                sample_size=total_data_points,
                agent_diversity=len(unique_sessions),  # Unique sessions as proxy for diversity
                temporal_spread_generations=temporal_generations,
                validation_type='outcome_based' if total_positive > 0 else 'frequency',
                positive_outcomes=total_positive,
                negative_outcomes=total_negative,
                crystallization_stage=2 if total_data_points > 10 else 1,  # Detected -> Classified
            )

            # Build reason string
            if untried_count == 7:
                reason = f"Frontier topology: No data for this frame - all actions have exploration bonus"
            elif untried_count > 0:
                reason = f"Frontier topology: {7-untried_count}/7 actions mapped, {untried_count} untried (boosted)"
            else:
                reason = f"Frontier topology: All actions mapped, best={best_action} (score={best_score:.2f})"

            return RungResult(
                action=best_action if best_action and confidence >= 0.5 else None,
                confidence=confidence,
                reason=reason,
                weights=weights,
                metadata={
                    'tried_actions': list(tried_actions),
                    'untried_actions': untried_actions,
                    'total_data_points': total_data_points,
                    'best_action': best_action,
                    'best_score': best_score,
                    'coverage': coverage
                },
                provenance=provenance,
            )
        except Exception as e:
            return RungResult(reason=f"Frontier topology failed: {e}")


class SmartActionSelectionRung(DecisionRung):
    """Fallback: strategy-based random selection - FALLBACK"""
    name = "smart_action_selection"
    category = "fallback"
    default_priority = 99  # Always last
    confidence_threshold = 0.0  # Always provides answer

    def _get_action6_coordinates(self) -> Dict[str, int]:
        """Get coordinates for ACTION6 from visual_analyzer or random fallback."""
        va = self.engines.visual_analyzer if self.engines else None
        if va and hasattr(va, 'get_grid_exploration_targets'):
            targets = va.get_grid_exploration_targets()
            if targets:
                target = targets[0]
                return {'x': target.get('x', 32), 'y': target.get('y', 32), 'grid_target': target}
        # Fallback: random position
        return {'x': random.randint(4, 60), 'y': random.randint(4, 60)}

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        try:
            strategy = context.get('fallback_strategy', 'balanced')
            available = context.get('available_actions', [1, 2, 3, 4, 5, 6, 7])
            available_strs = {f'ACTION{a}' for a in available}

            if strategy == 'exploration':
                all_weights = {'ACTION1': 1.2, 'ACTION2': 1.2, 'ACTION3': 1.2, 'ACTION4': 1.2,
                          'ACTION5': 0.5, 'ACTION6': 1.0, 'ACTION7': 0.3}
            elif strategy == 'exploitation':
                all_weights = {'ACTION1': 0.8, 'ACTION2': 0.8, 'ACTION3': 0.8, 'ACTION4': 0.8,
                          'ACTION5': 1.5, 'ACTION6': 1.2, 'ACTION7': 1.0}
            else:  # balanced
                all_weights = get_available_action_weights(context, 1.0)

            # Filter to only available actions
            weights = {k: v for k, v in all_weights.items() if k in available_strs}
            if not weights:
                weights = get_available_action_weights(context, 1.0)

            # Weighted random choice
            total = sum(weights.values())
            r = random.random() * total
            cumulative = 0
            for action, weight in weights.items():
                cumulative += weight
                if r <= cumulative:
                    # Add coordinates if ACTION6
                    metadata: Dict[str, Any] = {'strategy': strategy}
                    if action == 'ACTION6':
                        metadata.update(self._get_action6_coordinates())
                    return RungResult(
                        action=action,
                        confidence=0.1,
                        reason=f"Fallback ({strategy}): {action}",
                        weights=weights,
                        metadata=metadata
                    )

            fallback_action = get_random_available_action(context)
            # Add coordinates if ACTION6
            metadata = {'strategy': 'ultimate_fallback'}
            if fallback_action == 'ACTION6':
                metadata.update(self._get_action6_coordinates())
            return RungResult(action=fallback_action, confidence=0.1, reason="Ultimate fallback", metadata=metadata)
        except Exception as e:
            fallback_action = get_random_available_action(context)
            metadata = {'error': str(e)}
            if fallback_action == 'ACTION6':
                metadata.update({'x': random.randint(4, 60), 'y': random.randint(4, 60)})
            return RungResult(action=fallback_action, confidence=0.1, reason=f"Fallback error: {e}", metadata=metadata)


class InfiniteLoopBreakerRung(DecisionRung):
    """Emergency escape from stuck loops - EMERGENCY"""
    name = "infinite_loop_breaker"
    category = "emergency"
    default_priority = 1  # Highest priority when triggered
    confidence_threshold = 0.9

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        try:
            stuck_count = context.get('recent_stuck_count', 0)

            if stuck_count >= 15:
                # Emergency! Prefer movement actions (ACTION1-4) that haven't
                # already failed, since random ACTION6 clicks rarely unstick
                # the game and can create a self-reinforcing emergency loop.
                available = context.get('available_actions', [1, 2, 3, 4])
                failed = context.get('failed_actions', set())
                failed_nums = {int(a.replace('ACTION', '')) for a in failed if isinstance(a, str) and a.startswith('ACTION')}

                # Priority 1: untried movement actions
                movement = [a for a in available if a in (1, 2, 3, 4) and a not in failed_nums]
                if movement:
                    action = f'ACTION{random.choice(movement)}'
                # Priority 2: any untried action
                elif [a for a in available if a not in failed_nums]:
                    action = f'ACTION{random.choice([a for a in available if a not in failed_nums])}'
                # Priority 3: true last resort - anything available
                else:
                    action = get_random_available_action(context)

                return RungResult(
                    action=action,
                    confidence=0.95,
                    reason=f"EMERGENCY: Breaking infinite loop (stuck {stuck_count})",
                    metadata={'stuck_count': stuck_count, 'emergency': True}
                )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Loop breaker failed: {e}")


# =============================================================================
# ADDITIONAL RUNGS (Features 14-42 from action_decision_system.md)
# =============================================================================

class MapIntelCollisionRung(DecisionRung):
    """Obstacle avoidance when last action caused no frame change - EXPLOITATION

    Uses context 'frame_changed' flag to detect collisions and suggest
    perpendicular movement alternatives.
    """
    name = "map_intel_collision"
    category = "exploitation"
    default_priority = 24
    confidence_threshold = 0.5

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        try:
            # Check if last action caused no frame change (collision detection)
            # This is set by evolution_runner when it detects no change between frames
            frame_changed = context.get('frame_changed', True)
            last_action = context.get('last_action', '')
            available = context.get('available_actions', [1, 2, 3, 4])

            # Only applies to movement actions (1-4) that are available
            movement_available = [f'ACTION{a}' for a in available if a in [1, 2, 3, 4]]

            # If frame changed or last action wasn't movement, no collision recovery needed
            if frame_changed or last_action not in movement_available:
                return RungResult()

            # Get perpendicular alternatives (filtered by available)
            perpendicular_map = {
                'ACTION1': ['ACTION3', 'ACTION4'],
                'ACTION2': ['ACTION3', 'ACTION4'],
                'ACTION3': ['ACTION1', 'ACTION2'],
                'ACTION4': ['ACTION1', 'ACTION2'],
            }

            alternatives = perpendicular_map.get(last_action, [])
            # Filter to only available alternatives
            alternatives = [a for a in alternatives if a in movement_available]
            if alternatives:
                action = random.choice(alternatives)
                return RungResult(
                    action=action,
                    confidence=0.6,
                    reason=f"Collision recovery: {last_action} blocked, trying {action}",
                    metadata={'blocked_action': last_action, 'alternatives': alternatives}
                )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Map intel collision failed: {e}")


class TheoryGateRung(DecisionRung):
    """Working theory must score proposals, contradicted = force exploration - FINALIZER

    Uses scientific_method_engine to check current theory status and force
    exploration when theory is contradicted.
    """
    name = "theory_gate"
    category = "hypothesis"
    default_priority = 32
    confidence_threshold = 0.6

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        sme = self.engines.scientific_method_engine
        if sme is None:
            return RungResult()

        try:
            # Get game context for theory lookup
            game_type = context.get('game_type', '')
            level = context.get('level', 1)

            # get_working_theory requires game_type and level_number
            theory = None
            if hasattr(sme, 'get_working_theory') and game_type:
                theory = sme.get_working_theory(game_type, level)

            if theory and theory.get('stage') == 'contradicted':
                # Force exploration/revision
                exploration_actions = filter_available_actions(
                    ['ACTION1', 'ACTION2', 'ACTION3', 'ACTION4', 'ACTION6'], context
                )
                action = random.choice(exploration_actions)
                return RungResult(
                    action=action,
                    confidence=0.7,
                    reason=f"Theory contradicted: forcing exploration with {action}",
                    metadata={'theory': theory, 'forced_exploration': True}
                )
            return RungResult(metadata={'theory_stage': theory.get('stage') if theory else 'none'})
        except Exception as e:
            return RungResult(reason=f"Theory gate failed: {e}")


class AbstractionTemplatesRung(DecisionRung):
    """Use pattern templates from winning sequences - EXPLOITATION"""
    name = "abstraction_templates"
    category = "exploitation"
    default_priority = 45
    confidence_threshold = 0.4

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        engine = self.engines.abstraction_engine
        if engine is None:
            return RungResult()

        try:
            game_type = context.get('game_type', '')
            level = context.get('level', 1)

            if hasattr(engine, 'should_use_template') and engine.should_use_template(game_type, level):
                template = engine.get_template_for_replay(game_type, level)
                if template:
                    action_idx = context.get('template_position', 0)
                    if action_idx < len(template):
                        action = template[action_idx]
                        # CRITICAL: Validate action is available in this game
                        if is_action_available(action, context):
                            return RungResult(
                                action=action,
                                confidence=0.6,
                                reason=f"Following template: step {action_idx + 1}/{len(template)}",
                                metadata={'template': template, 'position': action_idx}
                            )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Abstraction templates failed: {e}")


class FewShotInvariantsRung(DecisionRung):
    """Relational bias from few-shot control relations - EXPLOITATION"""
    name = "few_shot_invariants"
    category = "exploitation"
    default_priority = 46
    confidence_threshold = 0.35

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        sm = self.engines.self_model
        if sm is None:
            return RungResult()

        try:
            if hasattr(sm, 'get_few_shot_control_relations'):
                invariants = sm.get_few_shot_control_relations()
                if invariants and invariants.get('sample_size', 0) >= 2:
                    action = invariants.get('suggested_action')
                    # CRITICAL: Validate action is available in this game
                    if action and is_action_available(action, context):
                        return RungResult(
                            action=action,
                            confidence=0.5,
                            reason=f"Few-shot invariant: sample_size={invariants.get('sample_size')}",
                            metadata={'invariants': invariants}
                        )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Few-shot invariants failed: {e}")


class FrontierCheckpointRung(DecisionRung):
    """Replay best frontier checkpoint on unbeaten levels - EXPLOITATION

    On frontier (unbeaten) levels, queries the frontier_checkpoints table for
    the best known partial progress. Replays that checkpoint sequence to skip
    already-explored territory, then lets exploration take over.

    This implements constructive pathfinding - building winning sequences
    incrementally by remembering the best partial progress across all agents.

    See: architecture/frontier_checkpoint_system.md
    """
    name = "frontier_checkpoint"
    category = "exploitation"
    default_priority = 6  # Very early - before three_try_sequence (8)
    confidence_threshold = 0.85

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._cached_checkpoint: Optional[Dict[str, Any]] = None
        self._cache_key: Optional[Tuple[str, int]] = None
        self._db: Any = None  # Lazy-loaded database interface

    def _get_db(self) -> Any:
        """Get database interface, lazy-loading if needed."""
        if self._db is None and self.engines:
            try:
                self._db = self.engines._get_db_interface()
            except Exception:
                pass
        return self._db

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        try:
            # Only fire on frontier levels (no winning sequence exists)
            is_frontier = context.get('is_frontier', False) or context.get('frontier_mode', False)
            if not is_frontier:
                return RungResult()

            # Check if we're already replaying a checkpoint
            checkpoint_position = context.get('checkpoint_position', 0)
            checkpoint_sequence = context.get('checkpoint_sequence')

            # If checkpoint sequence is active and we have more actions to replay
            if checkpoint_sequence and checkpoint_position < len(checkpoint_sequence):
                action = checkpoint_sequence[checkpoint_position]
                # CRITICAL: Validate action is available in this game
                if is_action_available(action, context):
                    return RungResult(
                        action=action,
                        confidence=0.85,
                        reason=f"Frontier checkpoint replay: step {checkpoint_position + 1}/{len(checkpoint_sequence)}",
                        metadata={
                            'checkpoint_replay': True,
                            'checkpoint_position': checkpoint_position,
                            'checkpoint_length': len(checkpoint_sequence),
                        }
                    )
                # Action not available - skip checkpoint replay
                return RungResult(reason=f"Checkpoint action {action} not available")

            # If no active checkpoint, try to load one from database
            db = self._get_db()
            if checkpoint_sequence is None and db is not None:
                game_type = context.get('game_type', '')
                level = context.get('level', 1)

                # Check cache first
                cache_key = (game_type, level)
                if self._cache_key != cache_key:
                    self._cached_checkpoint = self._query_best_checkpoint(game_type, level)
                    self._cache_key = cache_key

                if self._cached_checkpoint:
                    sequence = self._cached_checkpoint.get('action_sequence', [])
                    if sequence:
                        first_action = sequence[0]
                        # CRITICAL: Validate first action is available
                        if is_action_available(first_action, context):
                            return RungResult(
                                action=first_action,
                                confidence=0.85,
                                reason=f"Starting frontier checkpoint: {len(sequence)} actions from best progress",
                                metadata={
                                    'checkpoint_replay': True,
                                    'checkpoint_position': 0,
                                    'checkpoint_length': len(sequence),
                                    'checkpoint_loaded': True,
                                    'checkpoint_data': self._cached_checkpoint,
                                }
                            )

            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Frontier checkpoint failed: {e}")

    def _query_best_checkpoint(self, game_type: str, level: int) -> Optional[Dict[str, Any]]:
        """Query database for best checkpoint for this game_type/level."""
        db = self._get_db()
        if db is None:
            return None

        try:
            result: List[Dict[str, Any]] = db.execute_query("""
                SELECT action_sequence, actions_count, survival_score,
                       unique_frames_seen, terminal_frame_hash
                FROM frontier_checkpoints
                WHERE game_type = ? AND level_number = ?
                ORDER BY survival_score DESC, times_extended DESC
                LIMIT 1
            """, (game_type, level))

            if result and len(result) > 0:
                row = result[0]
                action_sequence: Any = json.loads(row.get('action_sequence', '[]')) if isinstance(row.get('action_sequence'), str) else row.get('action_sequence', [])
                return {
                    'action_sequence': action_sequence,
                    'actions_count': row.get('actions_count', 0),
                    'survival_score': row.get('survival_score', 0),
                    'unique_frames_seen': row.get('unique_frames_seen', 0),
                    'terminal_frame_hash': row.get('terminal_frame_hash'),
                }
        except Exception as e:
            logger.debug(f"[FRONTIER-CHECKPOINT] Query failed: {e}")

        return None

    def clear_cache(self) -> None:
        """Clear cached checkpoint (call on level transition)."""
        self._cached_checkpoint = None
        self._cache_key = None


class ThreeTrySequenceRung(DecisionRung):
    """Try up to 3 ranked sequences before exploration - GAME-LEVEL"""
    name = "three_try_sequence"
    category = "exploitation"
    default_priority = 8  # Early - before most decisions
    confidence_threshold = 0.7

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        try:
            # Check if we have an active sequence
            active_sequence = context.get('active_sequence')
            sequence_position = context.get('sequence_position', 0)

            if active_sequence and sequence_position < len(active_sequence):
                action = active_sequence[sequence_position]
                # CRITICAL: Validate action is available in this game
                if is_action_available(action, context):
                    return RungResult(
                        action=action,
                        confidence=0.8,
                        reason=f"Following sequence: step {sequence_position + 1}/{len(active_sequence)}",
                        metadata={'sequence_length': len(active_sequence), 'position': sequence_position}
                    )
                # Action not available - skip this sequence step
                return RungResult(reason=f"Sequence action {action} not available")
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Three-try sequence failed: {e}")


class MultiStageMatchingRung(DecisionRung):
    """Cascading sequence matching with 5 fallback strategies - EXPLOITATION"""
    name = "multi_stage_matching"
    category = "exploitation"
    default_priority = 42
    confidence_threshold = 0.5

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        pipeline = self.engines.multi_stage_pipeline
        if pipeline is None:
            return RungResult()

        try:
            game_type = context.get('game_type', '')
            level = context.get('level', 1)

            if hasattr(pipeline, 'get_sequence_with_fallback'):
                result = pipeline.get_sequence_with_fallback(game_type, level)
                if result and result.get('sequence'):
                    first_action = result['sequence'][0] if result['sequence'] else None
                    # CRITICAL: Validate action is available in this game
                    if first_action and is_action_available(first_action, context):
                        return RungResult(
                            action=first_action,
                            confidence=result.get('confidence', 0.5),
                            reason=f"Multi-stage match: {result.get('stage', 'unknown')}",
                            metadata={'match_result': result}
                        )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Multi-stage matching failed: {e}")


class ThreeLayerFilterRung(DecisionRung):
    """Meta-learning filter preventing wasted actions - FILTER

    Implements three filtering layers using context and prior lessons:
    Layer 1: Failed action cache - penalize recently failed actions
    Layer 2: Object prefilter - penalize click actions with no valid target
    Layer 3: Pattern prediction - penalize actions with low success history
    """
    name = "three_layer_filter"
    category = "filter"
    default_priority = 55
    confidence_threshold = 0.0  # Modifies weights, doesn't suggest

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        try:
            weights: Dict[str, float] = {}
            frame = None
            if hasattr(game_state, 'frame'):
                frame = game_state.frame
                # Convert numpy array to list if needed
                if hasattr(frame, 'tolist'):
                    frame = frame.tolist()
            position = context.get('position', (0, 0))
            # Ensure position is a tuple of ints
            if hasattr(position, '__iter__') and not isinstance(position, str):
                position = tuple(int(p) for p in position[:2]) if len(list(position)) >= 2 else (0, 0)
            else:
                position = (0, 0)
            available = context.get('available_actions', [1, 2, 3, 4, 5, 6, 7])

            # Layer 1: Cache check - penalize recently failed actions
            # Uses 'failed_actions' from context (set by evolution_runner)
            failed_actions = context.get('failed_actions', set())
            recent_actions = context.get('recent_actions', [])

            for i in available:
                action = f'ACTION{i}'
                if action in failed_actions:
                    weights[action] = 0.1  # Heavily penalize failed actions
                else:
                    weights[action] = 1.0

            # Layer 2: Object prefilter for click actions
            # Penalize ACTION5/6/7 if there's no non-background pixel at position
            if frame and isinstance(frame, list):
                for action_num in [5, 6, 7]:
                    if action_num in available:
                        action = f'ACTION{action_num}'
                        # Check if there's something to click at current position
                        y, x = position if len(position) >= 2 else (0, 0)
                        has_object = False

                        # Check 3x3 region around position
                        for dy in range(-1, 2):
                            for dx in range(-1, 2):
                                check_y, check_x = y + dy, x + dx
                                if (0 <= check_y < len(frame) and
                                    0 <= check_x < len(frame[0]) and
                                    frame[check_y][check_x] > 0):
                                    has_object = True
                                    break
                            if has_object:
                                break

                        if not has_object:
                            weights[action] = weights.get(action, 1.0) * 0.3

            # Layer 3: Pattern prediction using prior lessons
            prior_lessons = context.get('prior_lessons', [])
            for lesson in prior_lessons[:5]:
                key_action = lesson.get('key_action', '')
                if key_action in weights and lesson.get('caused_death', False):
                    severity = lesson.get('severity', 1)
                    weights[key_action] = weights.get(key_action, 1.0) * max(0.2, 1.0 - severity * 0.2)

            penalized_count = sum(1 for w in weights.values() if w < 1.0)
            if penalized_count > 0:
                return RungResult(
                    confidence=0.3,
                    weights=weights,
                    reason=f"3-layer filter applied: {penalized_count} actions penalized",
                    metadata={'filter_weights': weights}
                )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Three-layer filter failed: {e}")


class PariahAvoidanceRung(DecisionRung):
    """Avoid actions that historically led to failures - FILTER"""
    name = "pariah_avoidance"
    category = "filter"
    default_priority = 17
    confidence_threshold = 0.0  # Modifies weights

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        vpe = self.engines.viral_package_engine
        if vpe is None:
            return RungResult()

        try:
            agent_id = context.get('agent_id', '')
            game_id = context.get('game_id', '')
            level = context.get('level', 1)
            role = context.get('agent_role', 'generalist')

            if not agent_id:
                return RungResult()

            # Role-adjusted penalty multipliers
            role_multipliers = {
                'pioneer': 0.3,
                'optimizer': 1.0,
                'generalist': 0.7,
                'exploiter': 0.5
            }
            multiplier = role_multipliers.get(role, 0.7)

            # Use the correct API: get_role_adjusted_pariah_penalties or get_pariah_action_penalties
            if hasattr(vpe, 'get_role_adjusted_pariah_penalties'):
                penalties = vpe.get_role_adjusted_pariah_penalties(
                    agent_id=agent_id,
                    agent_role=role,
                    game_id=game_id,
                    current_level=level
                )
            elif hasattr(vpe, 'get_pariah_action_penalties'):
                penalties = vpe.get_pariah_action_penalties(
                    agent_id=agent_id,
                    game_id=game_id,
                    current_level=level
                )
            else:
                return RungResult()

            if not penalties:
                return RungResult()

            # Convert penalties to weights (penalty -> weight inversion)
            weights: Dict[str, float] = {}
            for action_num, penalty in penalties.items():
                action = f'ACTION{action_num}'
                # Apply role multiplier to penalty, then convert to weight
                adjusted_penalty = penalty * multiplier
                weights[action] = max(0.05, 1.0 - min(0.95, adjusted_penalty))

            if weights:
                return RungResult(
                    confidence=0.4,
                    weights=weights,
                    reason=f"Pariah avoidance: {len(penalties)} actions penalized, role={role}",
                    metadata={'penalties': len(penalties), 'role_multiplier': multiplier}
                )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Pariah avoidance failed: {e}")


class FrustrationDetectionRung(DecisionRung):
    """Detect stuck agents and trigger network signals - ORIENTATION"""
    name = "frustration_detection"
    category = "orientation"
    default_priority = 13
    confidence_threshold = 0.6

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        fd = self.engines.frustration_detector
        if fd is None:
            return RungResult()

        try:
            if hasattr(fd, 'is_frustrated'):
                frustration = fd.is_frustrated()
                if frustration.get('is_frustrated', False):
                    # Force exploration when frustrated
                    return RungResult(
                        action=get_random_available_action(context),
                        confidence=0.65,
                        reason=f"Frustration detected: {frustration.get('reason', 'unknown')}",
                        metadata={'frustration': frustration}
                    )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Frustration detection failed: {e}")


class TerminalPatternRung(DecisionRung):
    """Recognize approaching terminal states and avoid fatal action - FILTER"""
    name = "terminal_pattern"
    category = "filter"
    default_priority = 14
    confidence_threshold = 0.7

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        tpd = self.engines.terminal_pattern_detector
        if tpd is None:
            return RungResult()

        try:
            frame = game_state.frame if hasattr(game_state, 'frame') else None

            if hasattr(tpd, 'detect_terminal_approach'):
                terminal = tpd.detect_terminal_approach(frame, context.get('last_actions', []))
                if terminal.get('approaching_terminal', False):
                    fatal_action = terminal.get('fatal_action')
                    weights = get_available_action_weights(context, 1.0)
                    if fatal_action and fatal_action in weights:
                        weights[fatal_action] = 0.05  # Near-block the fatal action
                    return RungResult(
                        confidence=0.75,
                        weights=weights,
                        reason=f"Terminal approach detected: avoid {fatal_action}",
                        metadata={'terminal': terminal}
                    )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Terminal pattern failed: {e}")


class SensationEngineRung(DecisionRung):
    """Emotional context for actions based on object feelings - HYPOTHESIS"""
    name = "sensation_engine"
    category = "hypothesis"
    default_priority = 33
    confidence_threshold = 0.35

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        se = self.engines.sensation_engine
        if se is None:
            return RungResult()

        try:
            if hasattr(se, 'get_tetrahedral_sensation'):
                sensation = se.get_tetrahedral_sensation(context)

                # Convert sensations to action biases (only for available movement actions)
                weights: Dict[str, float] = {}
                available_movement = filter_available_actions(
                    ['ACTION1', 'ACTION2', 'ACTION3', 'ACTION4'], context
                )
                if sensation.get('approach_score', 0) > 0.5:
                    # Bias toward available movement actions
                    for action in available_movement:
                        weights[action] = 1.0 + sensation['approach_score'] * 0.3
                if sensation.get('threat_level', 0) > 0.5:
                    # Bias away from certain directions
                    threat_direction = sensation.get('threat_direction')
                    if threat_direction and threat_direction in weights:
                        weights[threat_direction] = max(0.1, 1.0 - sensation['threat_level'])

                if weights:
                    return RungResult(
                        confidence=0.4,
                        weights=weights,
                        reason=f"Sensation: approach={sensation.get('approach_score', 0):.2f}, threat={sensation.get('threat_level', 0):.2f}",
                        metadata={'sensation': sensation}
                    )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Sensation engine failed: {e}")


class IThreadRung(DecisionRung):
    """Maintain persistent identity, weave stream weights - HYPOTHESIS"""
    name = "i_thread"
    category = "hypothesis"
    default_priority = 31
    confidence_threshold = 0.4

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        ithread = self.engines.i_thread
        if ithread is None:
            return RungResult()

        try:

            # Get stream weights
            wA = ithread.get_wA() if hasattr(ithread, 'get_wA') else 0.5
            wB = ithread.get_wB() if hasattr(ithread, 'get_wB') else 0.5

            # Check for death personas (near cull)
            cull_distance = context.get('cull_distance', 1.0)
            if cull_distance < 0.2 and hasattr(ithread, 'spawn_death_persona'):
                persona = ithread.spawn_death_persona(context.get('agent_role', 'generalist'))
                if persona and persona.get('suggested_action'):
                    action = persona['suggested_action']
                    # CRITICAL: Validate action is available in this game
                    if is_action_available(action, context):
                        return RungResult(
                            action=action,
                            confidence=0.7,
                            reason=f"Death persona ({persona.get('name', 'unknown')}): {persona.get('reason', '')}",
                            metadata={'persona': persona, 'cull_distance': cull_distance}
                        )

            return RungResult(metadata={'wA': wA, 'wB': wB, 'cull_distance': cull_distance})
        except Exception as e:
            return RungResult(reason=f"I-Thread failed: {e}")


class NearMissAnalyzerRung(DecisionRung):
    """Learn from high-score failures - POST-HOC"""
    name = "near_miss_analyzer"
    category = "exploitation"
    default_priority = 48
    confidence_threshold = 0.4

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        nma = self.engines.near_miss_analyzer
        if nma is None:
            return RungResult()

        try:
            game_type = context.get('game_type', '')
            level = context.get('level', 1)

            if hasattr(nma, 'get_insights'):
                insights = nma.get_insights(game_type, level)
                if insights:
                    # Use insights to suggest action
                    suggested = insights.get('suggested_action')
                    # CRITICAL: Validate action is available in this game
                    if suggested and is_action_available(suggested, context):
                        return RungResult(
                            action=suggested,
                            confidence=insights.get('confidence', 0.4),
                            reason=f"Near-miss insight: {insights.get('category', 'unknown')}",
                            metadata={'insights': insights}
                        )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Near-miss analyzer failed: {e}")


class StateMatchingRung(DecisionRung):
    """
    Compare current player properties to learned goal requirements - EXPLOITATION

    Part of Symbolic Reasoning Implementation (Phase 4).

    This rung uses LEARNED data (not hard-coded game knowledge) to:
    1. Check if current player properties match goal requirements
    2. If mismatch, find a transformer that can fix it
    3. Suggest navigation toward transformer or goal

    Data Sources:
    - player_state_history: Current player properties (from PlayerLocalizer/PropertyExtractor)
    - goal_requirements: Learned requirements from successes/failures
    - property_transformations: Known transformers that change properties

    Graceful degradation: Returns empty result when no learned data exists.
    """
    name = "state_matching"
    category = "exploitation"
    default_priority = 26  # After rule_transfer (25), before frontier_topology (28)
    confidence_threshold = 0.5

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._db: Optional[Any] = None
        # Cache for current game session
        self._cached_requirements: Dict[str, Any] = {}
        self._cached_transformers: Dict[str, Any] = {}

    def _get_db(self) -> Optional[Any]:
        """Lazy-load database interface."""
        if self._db is None:
            try:
                from database_interface import DatabaseInterface
                self._db = DatabaseInterface()
            except ImportError as e:
                logger.debug(f"[STATE-MATCHING] Failed to load DatabaseInterface: {e}")
        return self._db

    def _get_goal_requirements(self, game_type: str, level: int) -> Optional[Dict[str, Any]]:
        """Query learned goal requirements for this game/level."""
        cache_key = f"{game_type}:{level}"
        if cache_key in self._cached_requirements:
            return self._cached_requirements[cache_key]

        db = self._get_db()
        if db is None:
            return None

        try:
            result = db.execute_query("""
                SELECT required_dominant_color, required_shape_phash, required_orientation,
                       times_succeeded, times_failed, confidence
                FROM goal_requirements
                WHERE game_id LIKE ? AND level_number = ?
                  AND confidence >= 0.5
                ORDER BY confidence DESC
                LIMIT 1
            """, (f"{game_type}%", level))

            row = result.fetchone() if result else None
            if row:
                req = {
                    'dominant_color': row[0],
                    'shape_signature': row[1],
                    'orientation': row[2],
                    'times_succeeded': row[3],
                    'times_failed': row[4],
                    'confidence': row[5],
                }
                self._cached_requirements[cache_key] = req
                return req

            self._cached_requirements[cache_key] = None
            return None
        except Exception as e:
            logger.debug(f"[STATE-MATCHING] Goal query failed: {e}")
            return None

    def _get_transformers(self, game_type: str, level: int, property_needed: str) -> List[Dict[str, Any]]:
        """Query known transformers that can change the specified property."""
        cache_key = f"{game_type}:{level}:{property_needed}"
        if cache_key in self._cached_transformers:
            return self._cached_transformers[cache_key]

        db = self._get_db()
        if db is None:
            return []

        try:
            result = db.execute_query("""
                SELECT object_position_x, object_position_y,
                       value_before, value_after,
                       times_observed, confidence
                FROM property_transformations
                WHERE game_id LIKE ? AND level_number = ?
                  AND property_changed = ?
                  AND confidence >= 0.5
                ORDER BY confidence DESC
                LIMIT 5
            """, (f"{game_type}%", level, property_needed))

            transformers = []
            for row in result.fetchall() if result else []:
                transformers.append({
                    'position': (row[0], row[1]),
                    'value_before': row[2],
                    'value_after': row[3],
                    'times_observed': row[4],
                    'confidence': row[5],
                })

            self._cached_transformers[cache_key] = transformers
            return transformers
        except Exception as e:
            logger.debug(f"[STATE-MATCHING] Transformer query failed: {e}")
            return []

    def _get_current_properties(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get current player properties from context or recent state history."""
        # First check if properties are in context (injected by evolution_runner)
        if 'player_properties' in context:
            return context['player_properties']

        # Otherwise query recent player_state_history
        db = self._get_db()
        if db is None:
            return None

        try:
            session_id = context.get('session_id')
            if not session_id:
                return None

            result = db.execute_query("""
                SELECT dominant_color, shape_phash, orientation, properties_json
                FROM player_state_history
                WHERE session_id = ?
                  AND dominant_color IS NOT NULL
                ORDER BY id DESC
                LIMIT 1
            """, (session_id,))

            row = result.fetchone() if result else None
            if row:
                return {
                    'dominant_color': row[0],
                    'shape_signature': row[1],
                    'orientation': row[2],
                }
            return None
        except Exception as e:
            logger.debug(f"[STATE-MATCHING] Properties query failed: {e}")
            return None

    def _find_mismatches(
        self,
        current: Dict[str, Any],
        required: Dict[str, Any]
    ) -> List[str]:
        """Find which properties don't match requirements."""
        mismatches = []

        # Check dominant_color
        if required.get('dominant_color') and current.get('dominant_color'):
            req_color = str(required['dominant_color'])
            cur_color = str(current['dominant_color'])
            if req_color != cur_color:
                mismatches.append('dominant_color')

        # Check orientation
        if required.get('orientation') is not None and current.get('orientation') is not None:
            if int(required['orientation']) != int(current['orientation']):
                mismatches.append('orientation')

        # Check shape_signature (allow some hamming distance)
        if required.get('shape_signature') and current.get('shape_signature'):
            req_sig = required['shape_signature']
            cur_sig = current['shape_signature']
            if len(req_sig) == len(cur_sig):
                hamming = sum(c1 != c2 for c1, c2 in zip(req_sig, cur_sig))
                if hamming > 8:  # Allow up to 8-bit difference in 64-bit signature
                    mismatches.append('shape_signature')

        return mismatches

    def _suggest_direction_to_position(
        self,
        target_pos: Tuple[int, int],
        context: Dict[str, Any]
    ) -> Optional[str]:
        """Suggest action to move toward a target position."""
        # Get current player position from context
        player_pos = context.get('player_position')
        if not player_pos:
            return None

        curr_row, curr_col = player_pos
        target_row, target_col = target_pos

        # Calculate direction
        row_diff = target_row - curr_row
        col_diff = target_col - curr_col

        # Prioritize larger difference
        if abs(row_diff) > abs(col_diff):
            if row_diff < 0:
                return 'ACTION1'  # Up
            else:
                return 'ACTION2'  # Down
        else:
            if col_diff < 0:
                return 'ACTION3'  # Left
            elif col_diff > 0:
                return 'ACTION4'  # Right

        return None

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        """
        Evaluate state matching and suggest action if applicable.

        Returns empty result if:
        - No learned goal requirements exist
        - Current properties not available
        - Properties already match (no action needed from this rung)
        """
        game_type = context.get('game_type', '')
        level = context.get('level', 1)

        # Step 1: Get learned goal requirements
        requirements = self._get_goal_requirements(game_type, level)
        if not requirements:
            # No learned requirements yet - graceful degradation
            return RungResult()

        # Step 2: Get current player properties
        current_props = self._get_current_properties(context)
        if not current_props:
            # Can't determine current state
            return RungResult(reason="No current properties available")

        # Step 3: Find mismatches
        mismatches = self._find_mismatches(current_props, requirements)

        if not mismatches:
            # Properties match! Suggest moving toward goal
            # (but we don't know goal position, so just report match)
            return RungResult(
                confidence=0.3,  # Low confidence - just informational
                reason=f"Properties match goal requirements (conf={requirements['confidence']:.2f})",
                metadata={
                    'state': 'properties_match',
                    'requirements': requirements,
                    'current': current_props,
                }
            )

        # Step 4: Find transformer to fix first mismatch
        first_mismatch = mismatches[0]
        transformers = self._get_transformers(game_type, level, first_mismatch)

        if not transformers:
            # We know there's a mismatch but don't know any transformers
            return RungResult(
                confidence=0.2,  # Very low - we identified a problem but can't solve it
                reason=f"Property mismatch ({first_mismatch}) but no known transformers",
                metadata={
                    'state': 'mismatch_no_transformer',
                    'mismatches': mismatches,
                    'current': current_props,
                    'required': requirements,
                }
            )

        # Step 5: Suggest navigation toward transformer
        best_transformer = transformers[0]
        target_pos = best_transformer['position']

        if target_pos[0] is None or target_pos[1] is None:
            # Transformer position unknown
            return RungResult(
                confidence=0.3,
                reason=f"Found transformer for {first_mismatch} but position unknown",
                metadata={
                    'state': 'transformer_unknown_position',
                    'transformer': best_transformer,
                }
            )

        suggested_action = self._suggest_direction_to_position(target_pos, context)

        if suggested_action:
            # Validate action is available
            if not is_action_available(suggested_action, context):
                return RungResult(
                    reason=f"State matching suggested unavailable action: {suggested_action}"
                )

            return RungResult(
                action=suggested_action,
                confidence=min(0.6, best_transformer['confidence']),
                reason=f"Navigate to transformer for {first_mismatch} ({best_transformer['value_before']}->{best_transformer['value_after']})",
                metadata={
                    'state': 'navigating_to_transformer',
                    'target_position': target_pos,
                    'mismatch': first_mismatch,
                    'transformer': best_transformer,
                    'current': current_props,
                    'required': requirements,
                }
            )

        # Can't determine direction (maybe at transformer already?)
        return RungResult(
            confidence=0.3,
            reason=f"Need {first_mismatch} change, transformer at {target_pos}",
            metadata={
                'state': 'at_or_near_transformer',
                'transformer': best_transformer,
                'mismatches': mismatches,
            }
        )

    def clear_cache(self):
        """Clear cached data (call on game/level change)."""
        self._cached_requirements.clear()
        self._cached_transformers.clear()


# =============================================================================
# EVENT UNDERSTANDING RUNGS - World Model Building
# =============================================================================

class PaletteDetectionRung(DecisionRung):
    """
    TWO-STAGE DECOMPOSITION: Stage 1 - Detect palette/legend blocks.

    Based on ARC-AGI-2 insights (76.11% success):
    "~70% of models cluster around wrong solutions where they use the 'palette'
    as top-to-bottom instead of inside-out."

    This rung runs EARLY to:
    1. Extract all objects from the frame (hollow frames, fills, irregular)
    2. Detect multi-colored palette/legend blocks
    3. Determine correct mapping direction (inside-out vs top-to-bottom)
    4. Populate context for downstream rungs

    Sets context fields:
    - detected_palette: PaletteInfo dict or None
    - extracted_objects: Dict with categorized objects
    - detected_transformations: List of detected transformation rules
    """
    name = "palette_detection"
    category = "orientation"
    default_priority = 3  # Very early - before frame_interpretation
    confidence_threshold = 0.0  # Context setter, not action suggester

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._palette_detector: Optional[Any] = None
        self._cached_analysis: Dict[str, Any] = {}  # Cache by frame hash

    def _get_palette_detector(self) -> Optional[Any]:
        """Lazy-load palette detector."""
        if self._palette_detector is None:
            try:
                from engines.perception.palette_detector import PaletteDetector
                self._palette_detector = PaletteDetector()
            except ImportError as e:
                logger.debug(f"[PALETTE-RUNG] PaletteDetector not available: {e}")
        return self._palette_detector

    def _frame_to_hash(self, frame: Any) -> str:
        """Generate hash for frame caching."""
        if frame is None:
            return "none"
        try:
            import hashlib
            if hasattr(frame, 'tobytes'):
                return hashlib.md5(frame.tobytes()).hexdigest()[:16]
            return hashlib.md5(str(frame).encode()).hexdigest()[:16]
        except Exception:
            return "unknown"

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        # Get frame from game_state
        frame = None
        if hasattr(game_state, 'frame'):
            frame = game_state.frame
        elif hasattr(game_state, 'observation'):
            obs = game_state.observation
            if isinstance(obs, dict) and 'frame' in obs:
                frame = obs['frame']

        if frame is None:
            return RungResult(
                confidence=0.0,
                reason="No frame available for palette detection"
            )

        # Check cache
        frame_hash = self._frame_to_hash(frame)
        if frame_hash in self._cached_analysis:
            cached = self._cached_analysis[frame_hash]
            context['detected_palette'] = cached.get('detected_palette')
            context['extracted_objects'] = cached.get('extracted_objects')
            context['detected_transformations'] = cached.get('detected_transformations')
            return RungResult(
                confidence=0.1,
                reason=f"Cached palette analysis: {'found' if cached.get('detected_palette') else 'none'}",
                metadata={'cached': True, **cached}
            )

        # Get detector
        detector = self._get_palette_detector()
        if detector is None:
            return RungResult(
                confidence=0.0,
                reason="Palette detector not available"
            )

        try:
            import numpy as np
            frame_arr = np.array(frame) if not isinstance(frame, np.ndarray) else frame
        except Exception as e:
            return RungResult(
                confidence=0.0,
                reason=f"Could not convert frame to array: {e}"
            )

        # Stage 1: Extract objects
        try:
            extracted = detector.extract_objects(frame_arr)
            extracted_dict = {
                'palettes': [o.to_dict() for o in extracted.get('palettes', [])],
                'hollow_frames': [o.to_dict() for o in extracted.get('hollow_frames', [])],
                'filled_shapes': [o.to_dict() for o in extracted.get('filled_shapes', [])],
                'irregular_shapes': [o.to_dict() for o in extracted.get('irregular_shapes', [])],
                'object_count': len(extracted.get('all_objects', [])),
            }
        except Exception as e:
            extracted_dict = {'error': str(e), 'object_count': 0}
            extracted = {}

        # Stage 1.5: Detect palette
        palette_dict = None
        try:
            palette = detector.detect_palette(frame_arr)
            if palette:
                palette_dict = palette.to_dict()
        except Exception as e:
            logger.debug(f"[PALETTE-RUNG] Palette detection failed: {e}")

        # Stage 2: Detect transformations
        transformations = []
        try:
            if palette and extracted:
                trans = detector.detect_transformations(extracted, palette, frame_arr)
                transformations = [t.to_dict() for t in trans]
        except Exception as e:
            logger.debug(f"[PALETTE-RUNG] Transformation detection failed: {e}")

        # Set context
        context['detected_palette'] = palette_dict
        context['extracted_objects'] = extracted_dict
        context['detected_transformations'] = transformations

        # Cache result
        analysis = {
            'detected_palette': palette_dict,
            'extracted_objects': extracted_dict,
            'detected_transformations': transformations,
        }
        self._cached_analysis[frame_hash] = analysis

        # Limit cache size
        if len(self._cached_analysis) > 100:
            oldest = list(self._cached_analysis.keys())[:50]
            for k in oldest:
                del self._cached_analysis[k]

        # Build reason
        parts = []
        if palette_dict:
            parts.append(f"palette={palette_dict.get('palette_type', 'unknown')}")
            parts.append(f"direction={palette_dict.get('mapping_direction', 'unknown')}")
            parts.append(f"conf={palette_dict.get('confidence', 0):.2f}")
        else:
            parts.append("no_palette")

        parts.append(f"objects={extracted_dict.get('object_count', 0)}")
        if transformations:
            parts.append(f"transforms={len(transformations)}")

        return RungResult(
            confidence=0.1 if palette_dict else 0.0,  # Low - context setter
            reason=f"Two-stage analysis: {', '.join(parts)}",
            metadata={
                'palette_found': palette_dict is not None,
                'object_count': extracted_dict.get('object_count', 0),
                'transformation_count': len(transformations),
                'analysis': analysis,
            }
        )

    def clear_cache(self):
        """Clear analysis cache (call on game/level change)."""
        self._cached_analysis.clear()


class SparseGridRung(DecisionRung):
    """
    SPARSE GRID REPRESENTATION: Efficient frame analysis for pattern matching.

    Converts frames to sparse representation (only non-background cells) for:
    1. Efficient structural comparison between frames
    2. Position-invariant pattern hashing
    3. Color-invariant pattern matching
    4. Connected component extraction

    Sets context fields:
    - sparse_grid: SparseGrid object for current frame
    - sparse_hash: Structural hash of current frame
    - sparse_cell_count: Number of non-background cells
    - sparse_colors: Set of colors used (excluding background)
    - sparse_components: List of connected component bounding boxes
    """
    name = "sparse_grid"
    category = "orientation"
    default_priority = 3  # Very early - alongside palette_detection
    confidence_threshold = 0.0  # Context setter, not action suggester

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._cached_sparse: Dict[str, Any] = {}  # Cache by frame hash
        self._previous_sparse: Optional[Any] = None  # For diff calculation

    def _frame_to_hash(self, frame: Any) -> str:
        """Generate hash for frame caching."""
        if frame is None:
            return "none"
        try:
            import hashlib
            if hasattr(frame, 'tobytes'):
                return hashlib.md5(frame.tobytes()).hexdigest()[:16]
            return hashlib.md5(str(frame).encode()).hexdigest()[:16]
        except Exception:
            return "unknown"

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        # Get frame from game_state
        frame = None
        if hasattr(game_state, 'frame'):
            frame = game_state.frame
        elif hasattr(game_state, 'observation'):
            obs = game_state.observation
            if isinstance(obs, dict) and 'frame' in obs:
                frame = obs['frame']

        if frame is None:
            return RungResult(
                confidence=0.0,
                reason="No frame available for sparse grid"
            )

        # Check cache
        frame_hash = self._frame_to_hash(frame)
        if frame_hash in self._cached_sparse:
            cached = self._cached_sparse[frame_hash]
            context['sparse_grid'] = cached.get('sparse_grid')
            context['sparse_hash'] = cached.get('sparse_hash')
            context['sparse_cell_count'] = cached.get('sparse_cell_count')
            context['sparse_colors'] = cached.get('sparse_colors')
            context['sparse_components'] = cached.get('sparse_components')
            context['sparse_diff'] = cached.get('sparse_diff')
            return RungResult(
                confidence=0.1,
                reason=f"Cached sparse: {cached.get('sparse_cell_count', 0)} cells",
                metadata={'cached': True, **cached}
            )

        # Import sparse grid module
        try:
            from engines.perception.sparse_grid import sparse_from_frame
        except ImportError as e:
            return RungResult(
                confidence=0.0,
                reason=f"Sparse grid module not available: {e}"
            )

        try:
            import numpy as np
            frame_arr = np.array(frame) if not isinstance(frame, np.ndarray) else frame
        except Exception as e:
            return RungResult(
                confidence=0.0,
                reason=f"Could not convert frame to array: {e}"
            )

        # Create sparse grid
        try:
            sparse = sparse_from_frame(frame_arr)
            sparse_hash = sparse.structural_hash()
            cell_count = len(sparse)
            colors = sparse.colors  # Property, not method

            # Extract connected components
            components = []
            try:
                comps = sparse.extract_connected_components()
                for comp in comps:
                    bbox = comp.bounding_box  # Property, not method
                    if bbox:
                        components.append({
                            'min_y': bbox[0], 'min_x': bbox[1],
                            'max_y': bbox[2], 'max_x': bbox[3],
                            'cell_count': len(comp),
                            'colors': list(comp.colors),  # Property, not method
                        })
            except Exception as e:
                logger.debug(f"[SPARSE-RUNG] Component extraction failed: {e}")

            # Calculate diff from previous frame
            diff_info = None
            if self._previous_sparse is not None:
                try:
                    diff = self._previous_sparse.diff(sparse)  # Use method, not function
                    diff_info = {
                        'added_count': len(diff.added),
                        'removed_count': len(diff.removed),
                        'changed_count': len(diff.changed),
                        'total_changes': diff.total_changes,  # Correct property name
                    }
                except Exception as e:
                    logger.debug(f"[SPARSE-RUNG] Diff calculation failed: {e}")

            # Store for next diff
            self._previous_sparse = sparse

        except Exception as e:
            return RungResult(
                confidence=0.0,
                reason=f"Sparse grid creation failed: {e}"
            )

        # Set context
        context['sparse_grid'] = sparse
        context['sparse_hash'] = sparse_hash
        context['sparse_cell_count'] = cell_count
        context['sparse_colors'] = colors
        context['sparse_components'] = components
        context['sparse_diff'] = diff_info

        # Cache result
        sparse_data = {
            'sparse_grid': sparse,
            'sparse_hash': sparse_hash,
            'sparse_cell_count': cell_count,
            'sparse_colors': colors,
            'sparse_components': components,
            'sparse_diff': diff_info,
        }
        self._cached_sparse[frame_hash] = sparse_data

        # Limit cache size
        if len(self._cached_sparse) > 100:
            oldest = list(self._cached_sparse.keys())[:50]
            for k in oldest:
                del self._cached_sparse[k]

        # Build reason
        parts = [f"cells={cell_count}", f"colors={len(colors)}"]
        if components:
            parts.append(f"components={len(components)}")
        if diff_info:
            parts.append(f"delta={diff_info['total_changes']}")

        return RungResult(
            confidence=0.1,  # Low - context setter
            reason=f"Sparse grid: {', '.join(parts)}",
            metadata={
                'sparse_hash': sparse_hash,
                'cell_count': cell_count,
                'color_count': len(colors),
                'component_count': len(components),
                'diff_info': diff_info,
            }
        )

    def clear_cache(self):
        """Clear sparse cache (call on game/level change)."""
        self._cached_sparse.clear()
        self._previous_sparse = None


class FrameInterpretationRung(DecisionRung):
    """
    HIGH PRIORITY: Interpret dramatic frame changes and set context.

    This rung sets context flags for downstream rungs based on frame delta
    magnitude. Does NOT suppress actions - the ARC API is blocking so spam
    is impossible anyway.

    Sets context flags:
    - likely_physics_game: True if large frame delta
    - expect_large_deltas: True if physics signature detected
    - detected_process_type: The type of process observed
    """
    name = "frame_interpretation"
    category = "orientation"
    default_priority = 4  # Early, after emergency rungs
    confidence_threshold = 0.0  # Context setter, not action suggester

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._event_detector: Optional[Any] = None
        self._recent_process_types: List[str] = []

    def _get_event_detector(self) -> Optional[Any]:
        """Lazy-load event detector."""
        if self._event_detector is None:
            try:
                from engines.perception.event_detector import EventDetector
                self._event_detector = EventDetector()
            except ImportError:
                pass
        return self._event_detector

    def _has_physics_signature(self, events: List[Any]) -> bool:
        """Check if events show physics-like behavior."""
        if not events:
            return False

        movement_count = sum(
            1 for e in events
            if hasattr(e, 'event_type') and str(e.event_type) == 'MOVEMENT'
        )
        return movement_count >= 3

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        delta_count = context.get('frame_delta_count', 0)
        recent_events = context.get('recent_events', [])

        # Interpret dramatic changes
        if delta_count > 500:  # Significant frame change
            # Annotate context for downstream rungs
            context['likely_physics_game'] = True
            context['expect_large_deltas'] = True

            # Check for physics signature
            if recent_events and self._has_physics_signature(recent_events):
                context['detected_process_type'] = 'PHYSICS_SIMULATION'
                self._recent_process_types.append('PHYSICS_SIMULATION')

            return RungResult(
                confidence=0.0,  # No action suggestion
                reason=f"Large frame delta ({delta_count}) - likely physics/animation game",
                metadata={
                    'delta_count': delta_count,
                    'physics_signature': bool(recent_events and self._has_physics_signature(recent_events)),
                    'recent_process_types': self._recent_process_types[-5:] if self._recent_process_types else [],
                }
            )

        # Small delta - probably direct control game
        if delta_count > 0 and delta_count < 100:
            context['likely_direct_control'] = True

        return RungResult()


class EventUnderstandingRung(DecisionRung):
    """
    Use causal world model to inform decisions.

    This rung builds understanding from frame-to-frame changes:
    - Tracks object movements and interactions
    - Detects collisions, fusions, and other events
    - Attributes causality to actions
    - Classifies the overall process type

    Uses this understanding to:
    - Set context flags for downstream rungs
    - Boost weights for actions that caused productive events
    - Predict continuation of causal chains
    """
    name = "event_understanding"
    category = "hypothesis"
    default_priority = 23  # After orientation, before exploitation
    confidence_threshold = 0.4

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._event_detector: Optional[Any] = None
        self._object_tracker: Optional[Any] = None
        self._event_history: List[Dict] = []  # Recent events for causal chain analysis
        self._db: Optional[Any] = None

    def _get_event_detector(self) -> Optional[Any]:
        """Lazy-load event detector."""
        if self._event_detector is None:
            try:
                from engines.perception.event_detector import EventDetector
                self._event_detector = EventDetector()
            except ImportError:
                pass
        return self._event_detector

    def _get_object_tracker(self) -> Optional[Any]:
        """Lazy-load object tracker."""
        if self._object_tracker is None:
            try:
                from engines.perception.object_tracker import ObjectTracker
                self._object_tracker = ObjectTracker()
            except ImportError:
                pass
        return self._object_tracker

    def _get_db(self) -> Optional[Any]:
        """Lazy-load database interface."""
        if self._db is None:
            try:
                from database_interface import DatabaseInterface
                self._db = DatabaseInterface()
            except ImportError:
                pass
        return self._db

    def _get_recent_events(self, context: Dict[str, Any]) -> List[Dict]:
        """Get recent events from context or database."""
        if 'recent_events' in context:
            return context['recent_events']

        db = self._get_db()
        if db is None:
            return self._event_history[-10:]

        try:
            game_type = context.get('game_type', '')
            result = db.execute_query("""
                SELECT event_type, objects_involved, positions, confidence
                FROM detected_events
                WHERE game_type = ?
                ORDER BY timestamp DESC
                LIMIT 10
            """, (game_type,))

            return [
                {'type': r[0], 'objects': r[1], 'positions': r[2], 'confidence': r[3]}
                for r in (result.fetchall() if result else [])
            ]
        except Exception:
            return self._event_history[-10:]

    def _last_action_caused_productive_event(self, events: List[Dict]) -> bool:
        """Check if the last action caused a productive event."""
        if not events:
            return False

        # Productive events: COLLECTION, TRANSFORMATION toward goal, FUSION
        productive_types = {'COLLECTION', 'TRANSFORMATION', 'FUSION'}

        for event in events[:3]:  # Check recent events
            event_type = event.get('type', event.get('event_type', ''))
            if isinstance(event_type, str) and event_type in productive_types:
                return True
            elif hasattr(event_type, 'value') and event_type.value in productive_types:
                return True

        return False

    def _detected_physics_process(self, events: List[Dict]) -> bool:
        """Check if physics simulation was detected."""
        if not events:
            return False

        movement_count = 0
        for event in events:
            event_type = event.get('type', event.get('event_type', ''))
            if 'MOVEMENT' in str(event_type):
                movement_count += 1

        return movement_count >= 3

    def _get_active_causal_chain(self, events: List[Dict]) -> List[Dict]:
        """Identify active causal chain from recent events."""
        if len(events) < 2:
            return []

        # Look for sequence of related events
        chain = []
        for event in events:
            event_type = str(event.get('type', event.get('event_type', '')))
            if event_type in {'MOVEMENT', 'COLLISION', 'FUSION', 'CHAIN_REACTION'}:
                chain.append(event)
            elif chain:
                break  # Chain broken

        return chain

    def _predict_chain_continuation(self, chain: List[Dict]) -> Optional[str]:
        """Predict what action would continue the causal chain."""
        if not chain:
            return None

        # If last event was a collision, maybe continue pushing
        last_event = chain[-1]
        last_type = str(last_event.get('type', last_event.get('event_type', '')))

        if 'COLLISION' in last_type or 'MOVEMENT' in last_type:
            # Continue in same direction if we have that info
            positions = last_event.get('positions', [])
            if len(positions) >= 2:
                # Calculate movement direction
                try:
                    dy = float(positions[1][0]) - float(positions[0][0])
                    dx = float(positions[1][1]) - float(positions[0][1])

                    if abs(dy) > abs(dx):
                        return 'ACTION2' if dy > 0 else 'ACTION1'  # Down or Up
                    elif abs(dx) > 0:
                        return 'ACTION4' if dx > 0 else 'ACTION3'  # Right or Left
                except (IndexError, TypeError, ValueError):
                    pass

        return None

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        recent_events = self._get_recent_events(context)

        if not recent_events:
            return RungResult()  # No understanding yet

        # Build weight modifiers based on understanding
        weights = get_available_action_weights(context, 1.0)

        # If last action caused productive event, boost similar actions
        if self._last_action_caused_productive_event(recent_events):
            last_action = context.get('last_action')
            if last_action and last_action in weights:
                weights[last_action] = 1.3  # Boost similar actions

        # If physics simulation detected, set context
        if self._detected_physics_process(recent_events):
            context['physics_game_confirmed'] = True

        # If we understand the causal chain, boost actions that extend it
        causal_chain = self._get_active_causal_chain(recent_events)
        if causal_chain:
            next_action = self._predict_chain_continuation(causal_chain)
            if next_action and is_action_available(next_action, context):
                return RungResult(
                    action=next_action,
                    confidence=0.55,
                    reason=f"Continuing causal chain of {len(causal_chain)} events",
                    weights=weights,
                    metadata={
                        'chain_length': len(causal_chain),
                        'last_event_type': str(causal_chain[-1].get('type', '')),
                    }
                )

        return RungResult(weights=weights)


class SpatialRelationshipRung(DecisionRung):
    """
    Learn and exploit spatial relationships in click puzzles.

    Tracks: "clicking position A affects positions B, C, D"
    Uses: "to change position X, I should click position Y"

    This rung is particularly useful for:
    - Lights Out-style games (clicking affects neighbors)
    - Tile puzzles with spatial dependencies
    - Any game where clicks have predictable spatial effects
    """
    name = "spatial_relationship"
    category = "exploitation"
    default_priority = 44  # After state_matching (42), before frontier_topology
    confidence_threshold = 0.5

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._effect_learner: Optional[Any] = None
        self._goal_tracker: Optional[Any] = None
        self._property_extractor: Optional[Any] = None
        self._db: Optional[Any] = None
        # Cache
        self._effect_pattern_cache: Dict[str, List[Tuple[int, int]]] = {}
        self._goal_cache: Dict[Tuple[str, int], Dict] = {}

    def _get_db(self) -> Optional[Any]:
        """Lazy-load database interface."""
        if self._db is None:
            try:
                from database_interface import DatabaseInterface
                self._db = DatabaseInterface()
            except ImportError:
                pass
        return self._db

    def _get_effect_learner(self) -> Optional[Any]:
        """Lazy-load spatial effect learner."""
        if self._effect_learner is None:
            try:
                from engines.perception.spatial_learning import SpatialEffectLearner
                db = self._get_db()
                if db:
                    self._effect_learner = SpatialEffectLearner(db)
            except ImportError:
                pass
        return self._effect_learner

    def _get_goal_tracker(self) -> Optional[Any]:
        """Lazy-load goal tracker."""
        if self._goal_tracker is None:
            try:
                from engines.perception.spatial_learning import MultiObjectGoalTracker
                db = self._get_db()
                if db:
                    self._goal_tracker = MultiObjectGoalTracker(db)
            except ImportError:
                pass
        return self._goal_tracker

    def _get_property_extractor(self) -> Optional[Any]:
        """Lazy-load property extractor."""
        if self._property_extractor is None:
            try:
                from engines.perception.spatial_learning import PropertyExtractor
                self._property_extractor = PropertyExtractor()
            except ImportError:
                pass
        return self._property_extractor

    def _extract_grid_state(self, frame: Any) -> Dict[Tuple[int, int], int]:
        """Extract current grid state from frame."""
        extractor = self._get_property_extractor()
        if extractor is None or frame is None:
            return {}

        try:
            import numpy as np
            if isinstance(frame, np.ndarray):
                return extractor.extract_grid_state(frame)
        except Exception:
            pass
        return {}

    def _get_effect_pattern(self, game_type: str) -> List[Tuple[int, int]]:
        """Get learned effect pattern for this game."""
        if game_type in self._effect_pattern_cache:
            return self._effect_pattern_cache[game_type]

        learner = self._get_effect_learner()
        if learner is None:
            return []

        try:
            pattern = learner.get_effect_pattern(game_type)
            self._effect_pattern_cache[game_type] = pattern
            return pattern
        except Exception:
            return []

    def _get_target_configuration(
        self,
        game_type: str,
        level: int
    ) -> Optional[Dict[Tuple[int, int], int]]:
        """Get known winning configuration for this level."""
        cache_key = (game_type, level)
        if cache_key in self._goal_cache:
            return self._goal_cache[cache_key]

        tracker = self._get_goal_tracker()
        if tracker is None:
            return None

        try:
            target = tracker.get_target_configuration(game_type, level)
            if target:
                self._goal_cache[cache_key] = target
            return target
        except Exception:
            return None

    def _find_differences(
        self,
        current: Dict[Tuple[int, int], int],
        target: Dict[Tuple[int, int], int]
    ) -> List[Tuple[int, int]]:
        """Find positions where current differs from target."""
        differences = []
        all_positions = set(current.keys()) | set(target.keys())

        for pos in all_positions:
            if current.get(pos, 0) != target.get(pos, 0):
                differences.append(pos)

        return differences

    def _find_best_click(
        self,
        current: Dict[Tuple[int, int], int],
        target: Dict[Tuple[int, int], int],
        differences: List[Tuple[int, int]],
        effect_pattern: List[Tuple[int, int]],
        grid_size: int = 8
    ) -> Optional[Tuple[int, int]]:
        """Find click position that reduces difference from goal."""
        best_click = None
        best_improvement = 0

        # Try clicking each grid position
        for gx in range(grid_size):
            for gy in range(grid_size):
                improvement = 0

                # Simulate effect
                for (rel_x, rel_y) in effect_pattern:
                    affected_x = gx + rel_x
                    affected_y = gy + rel_y

                    if (affected_x, affected_y) in differences:
                        improvement += 1

                if improvement > best_improvement:
                    best_improvement = improvement
                    best_click = (gx, gy)

        return best_click if best_improvement > 0 else None

    def _grid_to_pixel(
        self,
        grid_pos: Tuple[int, int],
        frame_size: int = 64,
        grid_size: int = 8
    ) -> Tuple[int, int]:
        """Convert grid position to pixel coordinates (center of cell)."""
        cell_size = frame_size // grid_size
        pixel_x = grid_pos[0] * cell_size + cell_size // 2
        pixel_y = grid_pos[1] * cell_size + cell_size // 2
        return (pixel_x, pixel_y)

    def on_action_complete(
        self,
        action: str,
        action_data: Dict[str, Any],
        frame_before: Any,
        frame_after: Any,
        context: Dict[str, Any]
    ) -> None:
        """Learn from click effects (called by outcome processor)."""
        if action != 'ACTION6':
            return

        learner = self._get_effect_learner()
        extractor = self._get_property_extractor()

        if learner is None or extractor is None:
            return

        try:
            import numpy as np
            if not isinstance(frame_before, np.ndarray) or not isinstance(frame_after, np.ndarray):
                return

            game_type = context.get('game_type', '')
            click_x = action_data.get('x', 0)
            click_y = action_data.get('y', 0)

            # Detect grid size and convert pixel to grid
            grid_size = extractor._detect_grid_size(frame_before)
            click_grid_pos = extractor.pixel_to_grid(
                click_x, click_y,
                frame_before.shape[1], frame_before.shape[0],
                grid_size
            )

            # Detect position changes
            changes = extractor.detect_position_changes(frame_before, frame_after, grid_size)

            if changes:
                learner.record_click_effect(game_type, click_grid_pos, changes)
                # Invalidate cache
                self._effect_pattern_cache.pop(game_type, None)

        except Exception:
            pass

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        # ACTION6 only
        available = context.get('available_actions', [1, 2, 3, 4, 5, 6, 7])
        if 6 not in available:
            return RungResult()

        game_type = context.get('game_type', '')
        level = context.get('level', 1)

        # Get current grid state
        frame = game_state.frame if hasattr(game_state, 'frame') else None
        current_state = self._extract_grid_state(frame)

        if not current_state:
            return RungResult()

        # Get target configuration (if known)
        target = self._get_target_configuration(game_type, level)

        if not target:
            return RungResult()  # Don't know goal yet

        # Find differences
        differences = self._find_differences(current_state, target)

        if not differences:
            return RungResult(
                confidence=0.3,
                reason="Grid state matches known goal configuration",
                metadata={'state': 'at_goal'}
            )

        # Get effect pattern
        effect_pattern = self._get_effect_pattern(game_type)

        if not effect_pattern:
            return RungResult()  # Don't know effects yet

        # Find click that moves us toward goal
        best_click = self._find_best_click(
            current_state, target, differences, effect_pattern
        )

        if best_click:
            click_x, click_y = self._grid_to_pixel(best_click)
            return RungResult(
                action='ACTION6',
                confidence=0.6,
                reason=f"Click ({best_click[0]}, {best_click[1]}) to change {len(differences)} tiles toward goal",
                metadata={
                    'grid_position': best_click,
                    'pixel_position': (click_x, click_y),
                    'differences_count': len(differences),
                    'effect_pattern_size': len(effect_pattern),
                }
            )

        return RungResult()

    def clear_cache(self):
        """Clear cached data."""
        self._effect_pattern_cache.clear()
        self._goal_cache.clear()


class SubgoalPlanningRung(DecisionRung):
    """Decompose complex levels into subgoals - EXPLOITATION"""
    name = "subgoal_planning"
    category = "exploitation"
    default_priority = 38
    confidence_threshold = 0.5

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        planner = self.engines.subgoal_planner
        if planner is None:
            return RungResult()

        try:
            if hasattr(planner, 'get_current_subgoal'):
                subgoal = planner.get_current_subgoal()
                if subgoal and subgoal.get('next_action'):
                    action = subgoal['next_action']
                    # CRITICAL: Validate action is available in this game
                    if not is_action_available(action, context):
                        return RungResult(reason=f"Subgoal action {action} not available")
                    return RungResult(
                        action=action,
                        confidence=subgoal.get('confidence', 0.5),
                        reason=f"Subgoal {subgoal.get('index', '?')}/{subgoal.get('total', '?')}: {subgoal.get('description', '')}",
                        metadata={'subgoal': subgoal}
                    )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Subgoal planning failed: {e}")


class BreakthroughBudgetRung(DecisionRung):
    """Dynamic action allocation based on breakthrough potential - ORIENTATION"""
    name = "breakthrough_budget"
    category = "orientation"
    default_priority = 6
    confidence_threshold = 0.0  # Context modifier, not action suggester

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        allocator = self.engines.breakthrough_allocator
        if allocator is None:
            return RungResult()

        try:
            game_type = context.get('game_type', '')

            if hasattr(allocator, 'get_budget'):
                budget = allocator.get_budget(game_type)
                context['action_budget'] = budget.get('per_level', 400)
                context['total_budget'] = budget.get('total', 2000)
                context['budget_phase'] = budget.get('phase', 'DISCOVERY')

                return RungResult(
                    confidence=0.1,  # Low - doesn't suggest action
                    reason=f"Budget phase: {budget.get('phase', 'DISCOVERY')}, per_level={budget.get('per_level', 400)}",
                    metadata={'budget': budget}
                )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Breakthrough budget failed: {e}")


class RegulatorySignalRung(DecisionRung):
    """Network homeostasis through distributed signals - ORIENTATION"""
    name = "regulatory_signal"
    category = "orientation"
    default_priority = 7
    confidence_threshold = 0.0  # Context modifier

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        re = self.engines.regulatory_engine
        if re is None:
            return RungResult()

        try:
            if hasattr(re, 'get_active_signals'):
                signals = re.get_active_signals()

                # Apply signal effects to context
                for signal in signals:
                    if signal.get('type') == 'diversity_stress':
                        context['knowledge_diversity_boost'] = context.get('knowledge_diversity_boost', 0) + 0.15
                    elif signal.get('type') == 'metabolism_stress':
                        context['action_budget_multiplier'] = context.get('action_budget_multiplier', 1.0) + 0.1
                    elif signal.get('type') == 'exploration_need':
                        context['mutation_rate'] = context.get('mutation_rate', 0) + 0.05

                if signals:
                    return RungResult(
                        confidence=0.1,
                        reason=f"Regulatory signals: {len(signals)} active",
                        metadata={'signals': signals}
                    )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Regulatory signal failed: {e}")


class VisualAnalyzerRung(DecisionRung):
    """Identify priority targets for ACTION6 clicks - EXPLOITATION"""
    name = "visual_analyzer"
    category = "exploitation"
    default_priority = 36
    confidence_threshold = 0.5

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        va = self.engines.visual_analyzer
        if va is None:
            return RungResult()

        try:
            # ACTION6 is typically 'click' - only suggest if available
            available = context.get('available_actions', [1, 2, 3, 4, 5, 6, 7])
            if 6 not in available:
                return RungResult()  # Click not available for this game

            frame = game_state.frame if hasattr(game_state, 'frame') else None

            if hasattr(va, 'get_priority_targets'):
                targets = va.get_priority_targets(frame)
                if targets:
                    best = targets[0]
                    return RungResult(
                        action='ACTION6',
                        confidence=best.get('confidence', 0.5),
                        reason=f"Visual target: {best.get('reason', 'unknown')} at ({best.get('x', 0)}, {best.get('y', 0)})",
                        metadata={'target': best, 'all_targets': len(targets)}
                    )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Visual analyzer failed: {e}")


class ResonanceDetectorRung(DecisionRung):
    """Cross-role pattern discovery for objective truth - HYPOTHESIS

    Implements the Resonance Discovery Principle from harmonies theory:
    When agents with radically different biases (Pioneers, Generalists, Exploiters)
    converge on the same pattern, that's evidence of OBJECTIVE TRUTH.

    Resonance detection is the bridge between "widely believed" and "actually true".
    High resonance + high role diversity = structural truth transcending individual bias.
    """
    name = "resonance_detector"
    category = "hypothesis"
    default_priority = 34
    confidence_threshold = 0.5

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        rd = self.engines.resonance_detector
        if rd is None:
            return RungResult()

        try:
            role = context.get('agent_role', 'generalist')

            # Role-specific query frequencies (from harmonies theory)
            query_probs = {'pioneer': 0.15, 'optimizer': 0.20, 'generalist': 0.30, 'exploiter': 0.10}
            if random.random() > query_probs.get(role, 0.15):
                return RungResult()  # Skip query this time

            if hasattr(rd, 'get_resonant_patterns'):
                # Query patterns with minimum resonance score
                patterns = rd.get_resonant_patterns(min_score=0.6, limit=10)
                if patterns:
                    best = patterns[0]
                    resonance_score = best.get('resonance_score', 0)

                    if resonance_score > 0.6:
                        suggested_action = best.get('suggested_action')
                        # CRITICAL: Validate action is available in this game
                        if not is_action_available(suggested_action, context):
                            return RungResult(reason=f"Resonance pattern suggested unavailable action: {suggested_action}")

                        # Build epistemological provenance
                        # Cross-role resonance is the gold standard for validation
                        role_diversity = best.get('role_diversity', 1)
                        game_types = best.get('game_types', [])

                        provenance = KnowledgeProvenance(
                            detection_source='resonance_patterns',
                            sample_size=role_diversity * len(game_types),
                            agent_diversity=role_diversity,  # Different ROLES = different cognitive biases
                            temporal_spread_generations=0.0,  # Not tracked for resonance
                            validation_type='cross_role_convergence',  # The gold standard
                            positive_outcomes=role_diversity,  # Each role validated
                            negative_outcomes=0,
                            crystallization_stage=4 if role_diversity >= 3 else 3,  # High: crystallized
                            resonance_games=len(game_types),  # How many games share this pattern
                            resonance_score=resonance_score
                        )

                        return RungResult(
                            action=suggested_action,
                            confidence=resonance_score,
                            reason=f"Resonant pattern ({role_diversity} roles, {len(game_types)} games): {best.get('theory_type', 'unknown')}",
                            metadata={
                                'pattern': best,
                                'pattern_hash': best.get('pattern_hash'),
                                'roles_found': best.get('roles_found', []),
                                'game_types': game_types,  # Store the actual list in metadata
                            },
                            provenance=provenance
                        )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Resonance detector failed: {e}")


class CoordinateOscillationRung(DecisionRung):
    """Detect bouncing between coordinates and break loop - EMERGENCY"""
    name = "coordinate_oscillation"
    category = "emergency"
    default_priority = 3
    confidence_threshold = 0.8

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        ah = self.engines.action_handler
        if ah is None:
            return RungResult()

        try:
            if hasattr(ah, 'detect_oscillation'):
                oscillation = ah.detect_oscillation()
                if oscillation.get('oscillation_detected', False):
                    # Try combination point or new direction
                    coords = oscillation.get('oscillating_coords', [])
                    if len(coords) >= 2:
                        # Suggest a different available action
                        current_action = context.get('last_action', 'ACTION1')
                        available_list = get_available_actions_list(context)
                        alternatives = [a for a in available_list if a != current_action]
                        if alternatives:
                            return RungResult(
                                action=random.choice(alternatives),
                                confidence=0.85,
                                reason=f"Breaking oscillation between {len(coords)} coords",
                                metadata={'oscillation': oscillation}
                            )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Coordinate oscillation failed: {e}")


class GridExplorationRung(DecisionRung):
    """Systematic 8x8 grid walking when stuck - EXPLORATION"""
    name = "grid_exploration"
    category = "orientation"
    default_priority = 47
    confidence_threshold = 0.3

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        va = self.engines.visual_analyzer
        if va is None:
            return RungResult()

        try:
            # ACTION6 is typically 'click' - only suggest if available
            available = context.get('available_actions', [1, 2, 3, 4, 5, 6, 7])
            if 6 not in available:
                return RungResult()  # Click not available for this game

            if hasattr(va, 'get_grid_exploration_targets'):
                targets = va.get_grid_exploration_targets()
                if targets:
                    target = targets[0]
                    return RungResult(
                        action='ACTION6',
                        confidence=0.35,
                        reason=f"Grid exploration: ({target.get('x', 0)}, {target.get('y', 0)}) - systematic search",
                        metadata={'grid_target': target, 'grid_index': va.grid_walking_index if hasattr(va, 'grid_walking_index') else 0}
                    )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Grid exploration failed: {e}")


class Action6ObjectExplorationRung(DecisionRung):
    """
    Use Action6BehaviorEngine to find clickable objects - EXPLORATION

    This rung uses the sophisticated pseudobutton/object selection system to:
    1. Find objects in the current frame that match known selectable shapes
    2. Prioritize unexplored objects for frontier exploration
    3. Return specific click coordinates for ACTION6

    This is critical for ACTION6-only games like vc33.
    """
    name = "action6_object_exploration"
    category = "exploration"
    default_priority = 38  # Higher priority than GridExplorationRung (47)
    confidence_threshold = 0.35

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        # Check if ACTION6 is available
        available = context.get('available_actions', [1, 2, 3, 4, 5, 6, 7])
        if 6 not in available:
            return RungResult()

        # Get the action6_behavior engine
        a6e = self.engines.action6_behavior
        if a6e is None:
            return RungResult()

        try:
            game_type = context.get('game_type', '')
            level = context.get('level', 1)

            # Get current frame from game_state
            frame = None
            if hasattr(game_state, 'frame'):
                frame = game_state.frame
            elif isinstance(game_state, dict):
                frame = game_state.get('frame')

            if not frame:
                return RungResult()

            # First try: Get objects matching known selectable shapes for this game
            if hasattr(a6e, 'get_untried_objects_for_frontier'):
                tried_colors = context.get('tried_colors', [])
                objects = a6e.get_untried_objects_for_frontier(
                    game_type=game_type,
                    level=level,
                    frame=frame,
                    tried_colors=tried_colors
                )
                if objects:
                    obj = objects[0]  # Highest confidence match
                    # Get center coordinates of the object
                    x = obj.get('center_x', obj.get('x', 32))
                    y = obj.get('center_y', obj.get('y', 32))
                    return RungResult(
                        action='ACTION6',
                        confidence=0.55 + (obj.get('shape_confidence', 0) * 0.2),
                        reason=f"Object exploration: color={obj.get('color')} shape={obj.get('shape_signature')} at ({x},{y})",
                        metadata={
                            'x': x,
                            'y': y,
                            'target_object': obj,
                            'source': 'shape_matching'
                        }
                    )

            # Second try: Get known pseudo-buttons for this game/level
            if hasattr(a6e, 'get_all_pseudo_buttons'):
                buttons = a6e.get_all_pseudo_buttons(game_type, level)
                if buttons:
                    # Find highest-confidence button that produces useful action
                    for button in buttons:
                        if button.get('confidence', 0) >= 0.5:
                            # Region coords are 0-7, convert to pixel coords (center of 8x8 region)
                            region_x = button.get('region_x', 4)
                            region_y = button.get('region_y', 4)
                            x = region_x * 8 + 4  # Center of region
                            y = region_y * 8 + 4
                            return RungResult(
                                action='ACTION6',
                                confidence=0.50 + button.get('confidence', 0) * 0.3,
                                reason=f"Pseudo-button at region ({region_x},{region_y}) -> ({x},{y})",
                                metadata={
                                    'x': x,
                                    'y': y,
                                    'pseudo_button': button,
                                    'source': 'pseudo_button'
                                }
                            )

            # Third try: Get selectable objects from network knowledge
            if hasattr(a6e, 'get_selectable_objects'):
                objects = a6e.get_selectable_objects(game_type, level, min_confidence=0.4)
                if objects:
                    obj = objects[0]
                    coords = obj.get('coordinates', '')
                    # Parse coordinates like "(32,45)"
                    if coords:
                        import re
                        match = re.match(r'\((\d+),(\d+)\)', coords)
                        if match:
                            x, y = int(match.group(1)), int(match.group(2))
                            return RungResult(
                                action='ACTION6',
                                confidence=0.45 + obj.get('confidence', 0) * 0.3,
                                reason=f"Selectable object color={obj.get('object_color')} at ({x},{y})",
                                metadata={
                                    'x': x,
                                    'y': y,
                                    'selectable_object': obj,
                                    'source': 'network_knowledge'
                                }
                            )

            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Action6 object exploration failed: {e}")


class NetworkObjectInventoryRung(DecisionRung):
    """Query network knowledge about interactable objects - EXPLOITATION"""
    name = "network_object_inventory"
    category = "exploitation"
    default_priority = 37
    confidence_threshold = 0.45

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        sm = self.engines.self_model
        if sm is None:
            return RungResult()

        try:
            game_type = context.get('game_type', '')
            level = context.get('level', 1)

            # ACTION6 is typically 'click' - only suggest if available
            available = context.get('available_actions', [1, 2, 3, 4, 5, 6, 7])
            if 6 not in available:
                return RungResult()  # Click not available for this game

            if hasattr(sm, 'get_network_object_inventory'):
                inventory = sm.get_network_object_inventory(game_type, level)
                if inventory.get('total_unique', 0) > 0:
                    # Bias toward interacting with known objects
                    interactable = inventory.get('interactable', [])
                    if interactable:
                        # Extract coordinates from first interactable object
                        first_obj = interactable[0]
                        x = first_obj.get('x', first_obj.get('center_x', 32))
                        y = first_obj.get('y', first_obj.get('center_y', 32))
                        return RungResult(
                            action='ACTION6',
                            confidence=0.5,
                            reason=f"Network inventory: {len(interactable)} interactable at ({x},{y})",
                            metadata={
                                'x': x,
                                'y': y,
                                'inventory': inventory,
                                'target_object': first_obj
                            }
                        )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Network object inventory failed: {e}")


class ClickBehaviorLearningRung(DecisionRung):
    """Learn and predict click behaviors using ClickBehaviorClassifier - EXPLOITATION

    Uses engines/self_model/click_behavior.py to:
    1. Predict what clicking an object will do (collect, toggle, trigger, etc.)
    2. Suggest clicks on objects with positive behaviors (score+)
    3. Avoid clicks on objects with negative behaviors (score-)

    This enables intelligent clicking based on learned object behaviors.
    """
    name = "click_behavior_learning"
    category = "exploitation"
    default_priority = 36  # Just above NetworkObjectInventoryRung
    confidence_threshold = 0.4

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        cb = self.engines.click_behavior
        if cb is None:
            return RungResult()

        try:
            # ACTION6 is typically 'click' - only suggest if available
            available = context.get('available_actions', [1, 2, 3, 4, 5, 6, 7])
            if 6 not in available:
                return RungResult()  # Click not available for this game

            game_type = context.get('game_type', '')
            if not game_type:
                return RungResult()

            # First: Check for collectible objects (positive score impact)
            if hasattr(cb, 'get_collectible_objects'):
                collectibles = cb.get_collectible_objects(game_type)
                if collectibles:
                    # Click on the most valuable collectible
                    best = collectibles[0]
                    x = best.get('x', best.get('center_x', 32))
                    y = best.get('y', best.get('center_y', 32))
                    return RungResult(
                        action='ACTION6',
                        confidence=0.6 + best.get('avg_score_impact', 0) * 0.2,
                        reason=f"Collectible object at ({x},{y}) - avg impact: {best.get('avg_score_impact', 0):.2f}",
                        metadata={
                            'x': x,
                            'y': y,
                            'collectible': best,
                            'behavior_type': 'collect'
                        }
                    )

            # Second: Check for trigger objects (chain reactions)
            if hasattr(cb, 'get_trigger_objects'):
                triggers = cb.get_trigger_objects(game_type)
                if triggers:
                    best = triggers[0]
                    x = best.get('x', best.get('center_x', 32))
                    y = best.get('y', best.get('center_y', 32))
                    return RungResult(
                        action='ACTION6',
                        confidence=0.5,
                        reason=f"Trigger object at ({x},{y}) - may cause chain reaction",
                        metadata={
                            'x': x,
                            'y': y,
                            'trigger': best,
                            'behavior_type': 'trigger'
                        }
                    )

            # Third: Predict behavior for objects in current frame
            frame = getattr(game_state, 'frame', None)
            if frame is not None and hasattr(cb, 'predict_click_behavior'):
                # Try center region first as likely interactive area
                prediction = cb.predict_click_behavior(
                    object_id='center_region',
                    color=-1,  # Unknown
                    game_type=game_type
                )
                if prediction and prediction.behavior.value not in ('unknown', 'no_effect', 'destroy'):
                    return RungResult(
                        action='ACTION6',
                        confidence=prediction.confidence * 0.8,
                        reason=f"Predicted behavior: {prediction.behavior.value} at center",
                        metadata={
                            'x': 32,
                            'y': 32,
                            'prediction': prediction.behavior.value,
                            'behavior_type': 'predicted'
                        }
                    )

            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Click behavior learning failed: {e}")


class ControlTrackerRung(DecisionRung):
    """Track which objects the agent controls - ORIENTATION (self-model)

    Uses engines/self_model/control_tracker.py to:
    1. Track action-movement correlations to identify controlled objects
    2. Provide "I am this object" identity information
    3. Suggest actions that move the controlled object toward goals

    This is CRITICAL for agents to understand their embodiment in the game.
    """
    name = "control_tracker"
    category = "orientation"
    default_priority = 8  # Early - need to know what we control
    confidence_threshold = 0.3

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        ct = self.engines.control_tracker
        if ct is None:
            return RungResult()

        try:
            game_id = context.get('game_id', context.get('game_type', ''))
            level = context.get('level', context.get('level_number', 1))

            if not game_id:
                return RungResult()

            # Get controlled objects for this game/level
            if hasattr(ct, 'get_controlled_objects'):
                controlled = ct.get_controlled_objects(game_id, level)

                if controlled:
                    # We know what we control - add to context for other rungs
                    best = controlled[0]  # Highest confidence
                    action_map = best.action_map

                    # If we have a goal/target, suggest action to move toward it
                    target = context.get('target_position') or context.get('goal_position')
                    player_pos = context.get('player_position')

                    if target and player_pos:
                        dx = target[0] - player_pos[0]
                        dy = target[1] - player_pos[1]

                        # Find action that moves in correct direction
                        for action, direction in action_map.items():
                            if direction == 'right' and dx > 0:
                                return RungResult(
                                    action=action,
                                    confidence=0.6,
                                    reason=f"Move {best.object_id} right toward target",
                                    metadata={'controlled_object': best.to_dict(), 'direction': 'right'}
                                )
                            elif direction == 'left' and dx < 0:
                                return RungResult(
                                    action=action,
                                    confidence=0.6,
                                    reason=f"Move {best.object_id} left toward target",
                                    metadata={'controlled_object': best.to_dict(), 'direction': 'left'}
                                )
                            elif direction == 'down' and dy > 0:
                                return RungResult(
                                    action=action,
                                    confidence=0.6,
                                    reason=f"Move {best.object_id} down toward target",
                                    metadata={'controlled_object': best.to_dict(), 'direction': 'down'}
                                )
                            elif direction == 'up' and dy < 0:
                                return RungResult(
                                    action=action,
                                    confidence=0.6,
                                    reason=f"Move {best.object_id} up toward target",
                                    metadata={'controlled_object': best.to_dict(), 'direction': 'up'}
                                )

                    # No target - just return info about what we control
                    return RungResult(
                        confidence=0.3,
                        reason=f"Control tracker: {best.object_id} ({best.confidence.value})",
                        metadata={
                            'controlled_objects': [c.to_dict() for c in controlled],
                            'primary_control': best.to_dict()
                        }
                    )

            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Control tracker failed: {e}")


class BeliefSystemRung(DecisionRung):
    """Track and use agent beliefs - HYPOTHESIS

    Uses engines/self_model/belief_system.py to:
    1. Query current beliefs about the game
    2. Use high-confidence beliefs to guide action selection
    3. Track belief invalidation cascades

    Beliefs provide persistent knowledge across actions.
    """
    name = "belief_system"
    category = "hypothesis"
    default_priority = 25
    confidence_threshold = 0.4

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        bs = self.engines.belief_system
        if bs is None:
            return RungResult()

        try:
            game_type = context.get('game_type', '')
            if not game_type:
                return RungResult()

            # Get active beliefs for this game
            if hasattr(bs, 'get_active_beliefs'):
                beliefs = bs.get_active_beliefs(game_type)

                if beliefs:
                    # Find high-confidence beliefs with action implications
                    for belief in beliefs:
                        if belief.get('confidence', 0) > 0.7:
                            # Check if belief suggests an action
                            statement = belief.get('statement', '')
                            if 'ACTION' in statement.upper():
                                # Extract action suggestion
                                for i in range(1, 8):
                                    if f'ACTION{i}' in statement.upper():
                                        return RungResult(
                                            action=f'ACTION{i}',
                                            confidence=belief.get('confidence', 0.5) * 0.7,
                                            reason=f"Belief: {statement[:50]}...",
                                            metadata={'belief': belief}
                                        )

                    # Return belief context for other rungs
                    return RungResult(
                        confidence=0.3,
                        reason=f"Belief system: {len(beliefs)} active beliefs",
                        metadata={'active_beliefs': beliefs[:5]}  # Top 5
                    )

            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Belief system failed: {e}")


class HypothesisSystemRung(DecisionRung):
    """Manage agent hypotheses - HYPOTHESIS

    Uses engines/social/hypothesis_system.py to:
    1. Get untested hypotheses that need validation
    2. Suggest actions to test hypotheses
    3. Record test results for learning

    This enables agents to actively test their theories.
    """
    name = "hypothesis_system"
    category = "hypothesis"
    default_priority = 26
    confidence_threshold = 0.4

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        hs = self.engines.hypothesis_system
        if hs is None:
            return RungResult()

        try:
            agent_id = context.get('agent_id', '')
            game_type = context.get('game_type', '')

            if not agent_id or not game_type:
                return RungResult()

            # Get testable hypotheses for this game
            if hasattr(hs, 'get_agent_hypotheses'):
                hypotheses = hs.get_agent_hypotheses(agent_id, game_type, status='testing')

                if hypotheses:
                    # Find hypothesis with predicted action
                    for hyp in hypotheses:
                        predicted_action = hyp.get('predicted_action')
                        if predicted_action:
                            return RungResult(
                                action=predicted_action,
                                confidence=0.55,
                                reason=f"Testing hypothesis: {hyp.get('hypothesis_text', '')[:40]}...",
                                metadata={
                                    'hypothesis_id': hyp.get('hypothesis_id'),
                                    'hypothesis': hyp,
                                    'testing_mode': True
                                }
                            )

                        # Check for action sequence
                        sequence = hyp.get('action_sequence')
                        if sequence and isinstance(sequence, list) and len(sequence) > 0:
                            # Get position in sequence
                            seq_pos = context.get('hypothesis_sequence_position', 0)
                            if seq_pos < len(sequence):
                                return RungResult(
                                    action=sequence[seq_pos],
                                    confidence=0.5,
                                    reason=f"Hypothesis sequence step {seq_pos + 1}/{len(sequence)}",
                                    metadata={
                                        'hypothesis_id': hyp.get('hypothesis_id'),
                                        'sequence_position': seq_pos,
                                        'full_sequence': sequence
                                    }
                                )

            # Check for hypothesis suggestions from patterns
            if hasattr(hs, 'suggest_hypothesis_from_pattern'):
                observations = context.get('recent_observations', [])
                if observations:
                    suggestion = hs.suggest_hypothesis_from_pattern(agent_id, game_type, observations)
                    if suggestion:
                        return RungResult(
                            confidence=0.3,
                            reason=f"Hypothesis suggestion: {suggestion.get('suggested_hypothesis', '')[:40]}...",
                            metadata={'hypothesis_suggestion': suggestion}
                        )

            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Hypothesis system failed: {e}")


class TriggerSequencesRung(DecisionRung):
    """Learn and use trigger chains - EXPLOITATION

    Uses engines/self_model/trigger_sequences.py to:
    1. Record trigger chains (X causes Y which causes Z)
    2. Replay proven action sequences for levels
    3. Predict trigger effects

    Critical for puzzle games with cause-effect chains.
    """
    name = "trigger_sequences"
    category = "exploitation"
    default_priority = 43
    confidence_threshold = 0.5

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        ts = self.engines.trigger_sequences
        if ts is None:
            return RungResult()

        try:
            game_type = context.get('game_type', '')
            level = context.get('level', context.get('level_number', 1))

            if not game_type:
                return RungResult()

            # Check for proven trigger sequence for this level
            if hasattr(ts, 'get_proven_sequence'):
                proven = ts.get_proven_sequence(game_type, level)
                if proven:
                    # Get current position in sequence
                    action_count = context.get('action_count', 0)
                    if action_count < len(proven):
                        step = proven[action_count]
                        return RungResult(
                            action=step.get('action', f'ACTION{step.get("step_number", 1)}'),
                            confidence=0.75,
                            reason=f"Proven trigger sequence step {action_count + 1}/{len(proven)}",
                            metadata={
                                'trigger_step': step,
                                'full_sequence': proven,
                                'sequence_position': action_count
                            }
                        )

            # Check for known trigger effects
            if hasattr(ts, 'predict_trigger_effect'):
                frame = getattr(game_state, 'frame', None)
                if frame is not None:
                    # Get available actions
                    available = context.get('available_actions', list(range(1, 8)))
                    for action_num in available:
                        action = f'ACTION{action_num}'
                        prediction = ts.predict_trigger_effect(game_type, level, action)
                        if prediction and prediction.get('effect') == 'score_change':
                            if prediction.get('score_delta', 0) > 0:
                                return RungResult(
                                    action=action,
                                    confidence=0.6,
                                    reason=f"Trigger predicts +score: {prediction.get('effect_target')}",
                                    metadata={'trigger_prediction': prediction}
                                )

            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Trigger sequences failed: {e}")


class SymbolicTrackerRung(DecisionRung):
    """Track symbolic state for transformation puzzles - HYPOTHESIS

    Uses engines/self_model/symbolic_tracker.py to:
    1. Identify key objects (controllable) vs lock objects (target)
    2. Track symbolic properties: shape, color, orientation
    3. Suggest actions to make key match lock

    Essential for transformation/matching puzzles.
    """
    name = "symbolic_tracker"
    category = "hypothesis"
    default_priority = 24
    confidence_threshold = 0.45

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        st = self.engines.symbolic_tracker
        if st is None:
            return RungResult()

        try:
            frame = getattr(game_state, 'frame', None)
            if frame is None:
                return RungResult()

            # Identify symbolic objects
            if hasattr(st, 'identify_symbolic_objects'):
                controlled_colors = context.get('controlled_colors', [])
                objects = st.identify_symbolic_objects(frame, controlled_colors)

                keys = objects.get('keys', {})
                locks = objects.get('locks', {})
                tools = objects.get('tools', {})

                if keys and locks:
                    # Check match score
                    if hasattr(st, 'calculate_match_score'):
                        match_score = st.calculate_match_score()

                        if match_score < 1.0:
                            # Not matching - try to identify transformation needed
                            if hasattr(st, 'suggest_transformation'):
                                suggestion = st.suggest_transformation()
                                if suggestion:
                                    action = suggestion.get('action')
                                    if action:
                                        return RungResult(
                                            action=action,
                                            confidence=0.55,
                                            reason=f"Symbolic match {match_score:.0%} - {suggestion.get('reason', 'transform')}",
                                            metadata={
                                                'match_score': match_score,
                                                'keys': keys,
                                                'locks': locks,
                                                'suggestion': suggestion
                                            }
                                        )

                        # Near match - return status
                        return RungResult(
                            confidence=0.3 + match_score * 0.3,
                            reason=f"Symbolic tracking: {len(keys)} keys, {len(locks)} locks, match={match_score:.0%}",
                            metadata={'keys': keys, 'locks': locks, 'tools': tools, 'match_score': match_score}
                        )

            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Symbolic tracker failed: {e}")


class EmbeddingMatcherRung(DecisionRung):
    """Use frame embeddings to find similar past situations - EXPLOITATION

    Uses engines/self_model/embedding_matcher.py to:
    1. Find similar past game frames using neural embeddings
    2. Return what action worked best in those situations
    3. Apply recency weighting (recent experiences weighted higher)

    This enables implicit generalization through learned representations.
    """
    name = "embedding_matcher"
    category = "exploitation"
    default_priority = 44
    confidence_threshold = 0.4

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        em = self.engines.embedding_matcher
        if em is None:
            return RungResult()

        try:
            frame = getattr(game_state, 'frame', None)
            if frame is None:
                return RungResult()

            game_type = context.get('game_type', '')
            level = context.get('level', context.get('level_number', 1))

            if not game_type:
                return RungResult()

            # Get embedding-based action suggestion
            if hasattr(em, 'get_embedding_suggested_action'):
                suggestion = em.get_embedding_suggested_action(
                    game_type=game_type,
                    level=level,
                    current_frame=frame,
                    top_k=5
                )

                if suggestion and suggestion.get('suggested_action'):
                    action = suggestion['suggested_action']
                    confidence = suggestion.get('confidence', 0.5)
                    similar_count = len(suggestion.get('similar_situations', []))

                    return RungResult(
                        action=f'ACTION{action}' if isinstance(action, int) else action,
                        confidence=confidence * 0.8,
                        reason=f"Embedding match: {similar_count} similar situations suggest action {action}",
                        metadata={
                            'similar_situations': suggestion.get('similar_situations', [])[:3],
                            'embedding_confidence': confidence
                        }
                    )

            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Embedding matcher failed: {e}")


class FewShotRelationsRung(DecisionRung):
    """Use few-shot invariants for quick control bootstrapping - EXPLOITATION

    Uses engines/self_model/few_shot_relations.py to:
    1. Get control invariants (what ALWAYS works for this action)
    2. Get control variants (what CHANGES based on context)
    3. Suggest actions based on proven invariants

    Enables quick learning from small numbers of examples.
    """
    name = "few_shot_relations"
    category = "exploitation"
    default_priority = 52
    confidence_threshold = 0.45

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        fsr = self.engines.few_shot_relations
        if fsr is None:
            return RungResult()

        try:
            game_id = context.get('game_id', context.get('game_type', ''))
            level = context.get('level', context.get('level_number', 1))

            if not game_id:
                return RungResult()

            # Get few-shot control relations
            if hasattr(fsr, 'get_few_shot_control_relations'):
                relations = fsr.get_few_shot_control_relations(game_id, level)

                if relations and relations.get('confidence', 0) > 0.5:
                    invariants = relations.get('invariants', {})

                    # Find an action with strong invariants
                    for action, props in invariants.items():
                        if props and props.get('success_rate', 0) > 0.7:
                            return RungResult(
                                action=action,
                                confidence=props.get('success_rate', 0.6) * 0.7,
                                reason=f"Few-shot invariant: {action} has {props.get('success_rate', 0):.0%} success",
                                metadata={
                                    'invariants': invariants,
                                    'variants': relations.get('variants', {}),
                                    'relation_confidence': relations.get('confidence')
                                }
                            )

            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Few-shot relations failed: {e}")


class NetworkSharingRung(DecisionRung):
    """Query network for shared control hypotheses - EXPLOITATION

    Uses engines/self_model/network_sharing.py to:
    1. Get validated control hypotheses from other agents
    2. Learn from network "I am this object" discoveries
    3. Use high-reliability patterns from the network

    Implements the thought process colony for self-model knowledge.
    """
    name = "network_sharing"
    category = "exploitation"
    default_priority = 50
    confidence_threshold = 0.45

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        ns = self.engines.network_sharing
        if ns is None:
            return RungResult()

        try:
            game_id = context.get('game_id', context.get('game_type', ''))
            level = context.get('level', context.get('level_number', 1))
            game_type = game_id.split('-')[0] if '-' in game_id else game_id

            if not game_type:
                return RungResult()

            # Get network control hypotheses
            if hasattr(ns, 'get_network_control_hypotheses'):
                hypotheses = ns.get_network_control_hypotheses(game_type, level)

                if hypotheses:
                    # Find highest-reliability hypothesis
                    best = max(hypotheses, key=lambda h: h.get('reliability_score', 0))

                    if best.get('reliability_score', 0) > 0.6:
                        action_map = best.get('action_response_map', {})

                        # Suggest first action from the map
                        if action_map:
                            action = list(action_map.keys())[0]
                            return RungResult(
                                action=action,
                                confidence=best.get('reliability_score', 0.5) * 0.7,
                                reason=f"Network hypothesis: {best.get('hypothesis_id', 'unknown')[:20]}",
                                metadata={
                                    'hypothesis': best,
                                    'action_map': action_map,
                                    'validation_count': best.get('validation_attempts', 0)
                                }
                            )

            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Network sharing failed: {e}")


class PrimitiveSuggesterRung(DecisionRung):
    """Use primitives directly for action suggestions - EXPLOITATION

    Uses engines/social/primitive_suggester.py to:
    1. Apply seed primitives to the current frame
    2. Map primitive outputs to action suggestions
    3. Use learned effectiveness (RLVR feedback)

    Simple, direct primitive-to-action mapping without CODS complexity.
    """
    name = "primitive_suggester"
    category = "exploitation"
    default_priority = 48
    confidence_threshold = 0.35

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        ps = self.engines.primitive_suggester
        if ps is None:
            return RungResult()

        try:
            frame = getattr(game_state, 'frame', None)
            if frame is None:
                return RungResult()

            game_type = context.get('game_type', '')
            recent_actions = context.get('last_actions', [])

            # Get primitive-based suggestion
            if hasattr(ps, 'suggest_action'):
                result = ps.suggest_action(
                    frame=frame,
                    game_type=game_type,
                    recent_actions=recent_actions
                )

                if result and result.action:
                    # Convert to dict if it's a dataclass
                    result_dict = result.to_dict() if hasattr(result, 'to_dict') else {}

                    return RungResult(
                        action=f'ACTION{result.action}',
                        confidence=result.confidence * 0.8,
                        reason=f"Primitive {result.primitive}: {result.reasoning[:50]}",
                        metadata={
                            'primitive': result.primitive,
                            'primitives_applied': result_dict.get('primitives_applied', []),
                            'candidates': result_dict.get('candidates', [])[:3]
                        }
                    )

            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Primitive suggester failed: {e}")


class ValenceGoalsRung(DecisionRung):
    """Use valence associations and inferred goals - FILTER/EXPLOITATION

    Uses engines/self_model/valence_goals.py to:
    1. Check valence of nearby objects (good/bad/neutral)
    2. Use inferred goals to guide action selection
    3. Avoid negative-valence objects, approach positive ones

    Provides emotional coloring to guide exploration.
    """
    name = "valence_goals"
    category = "exploitation"
    default_priority = 35
    confidence_threshold = 0.4

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        vg = self.engines.valence_goals
        if vg is None:
            return RungResult()

        try:
            game_type = context.get('game_type', '')
            level = context.get('level', context.get('level_number', 1))
            player_pos = context.get('player_position')

            if not game_type:
                return RungResult()

            # Check for inferred goals
            if hasattr(vg, 'get_inferred_goal'):
                goal = vg.get_inferred_goal(game_type, level)

                if goal and goal.get('confidence', 0) > 0.5:
                    goal_type = goal.get('goal_type')
                    targets = goal.get('target_regions', [])

                    if targets and player_pos:
                        # Move toward goal target
                        target = targets[0]
                        dx = target[1] - player_pos[0] if len(target) > 1 else 0
                        dy = target[0] - player_pos[1] if len(target) > 0 else 0

                        if abs(dx) > abs(dy):
                            action = 'ACTION3' if dx > 0 else 'ACTION4'
                            direction = 'right' if dx > 0 else 'left'
                        else:
                            action = 'ACTION2' if dy > 0 else 'ACTION1'
                            direction = 'down' if dy > 0 else 'up'

                        return RungResult(
                            action=action,
                            confidence=goal.get('confidence', 0.5) * 0.6,
                            reason=f"Goal {goal_type}: move {direction} toward target",
                            metadata={'goal': goal, 'target': target}
                        )

            # Check valence of nearby objects for avoidance
            if hasattr(vg, 'get_negative_valence_objects'):
                dangers = vg.get_negative_valence_objects(game_type)

                if dangers:
                    # Return as filter info rather than action
                    return RungResult(
                        confidence=0.3,
                        reason=f"Valence: {len(dangers)} negative objects to avoid",
                        metadata={
                            'negative_objects': dangers[:5],
                            'filter_mode': True
                        }
                    )

            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Valence goals failed: {e}")


class DeliberationSystemRung(DecisionRung):
    """TRM-inspired iterative refinement - HYPOTHESIS

    Uses scientific_method_engine to get theory hints and deliberation results
    for multi-agent reasoning convergence.
    """
    name = "deliberation_system"
    category = "hypothesis"
    default_priority = 29
    confidence_threshold = 0.5

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        sme = self.engines.scientific_method_engine
        if sme is None:
            return RungResult()

        try:
            # Use scientific method engine's theory hint for deliberation guidance
            if hasattr(sme, 'get_active_theory_hint'):
                hint = sme.get_active_theory_hint()

                if hint and hint.get('prediction'):
                    # Theory has a prediction - this is deliberation output
                    action = hint.get('prediction', {}).get('action')
                    confidence = hint.get('weight', 0.5) + 0.3  # Boost confidence

                    # CRITICAL: Validate action is available in this game
                    if action and is_action_available(action, context):
                        return RungResult(
                            action=action,
                            confidence=min(0.9, confidence),
                            reason=f"Deliberation hint: {hint.get('reason', 'theory-guided')}",
                            metadata={'deliberation_hint': hint}
                        )

            # Fallback: Check context for deliberation results from other systems
            deliberation = context.get('deliberation_result')
            if deliberation and deliberation.get('convergence_achieved', False):
                action = deliberation.get('consensus_action')
                # CRITICAL: Validate action is available in this game
                if action and is_action_available(action, context):
                    return RungResult(
                        action=action,
                        confidence=deliberation.get('refinement_confidence', 0.6),
                        reason=f"Deliberation converged: {deliberation.get('refinement_passes', 0)} passes",
                        metadata={'deliberation': deliberation}
                    )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Deliberation system failed: {e}")


class ReplayLearningRung(DecisionRung):
    """Prediction-based learning during sequence replay - EXPLOITATION"""
    name = "replay_learning"
    category = "exploitation"
    default_priority = 43
    confidence_threshold = 0.5

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        rle = self.engines.replay_learning_engine
        if rle is None:
            return RungResult()

        try:
            if hasattr(rle, 'get_current_prediction'):
                prediction = rle.get_current_prediction()
                if prediction and context.get('is_replay', False):
                    action = prediction.get('action')
                    # CRITICAL: Validate action is available in this game
                    if action and is_action_available(action, context):
                        return RungResult(
                            action=action,
                            confidence=prediction.get('confidence', 0.5),
                            reason=f"Replay prediction: {prediction.get('hypothesis', 'unknown')}",
                            metadata={'prediction': prediction, 'is_replay': True}
                        )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Replay learning failed: {e}")


class ImaginationBudgetRung(DecisionRung):
    """Allocate computational budget based on novelty - ORIENTATION"""
    name = "imagination_budget"
    category = "orientation"
    default_priority = 4
    confidence_threshold = 0.0  # Context modifier

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        ib = self.engines.imagination_budget
        if ib is None:
            return RungResult()

        try:
            if hasattr(ib, 'calculate_budget'):
                budget = ib.calculate_budget(
                    is_novel=context.get('is_novel_game', False),
                    is_frontier=context.get('frontier_mode', False),
                    surprise_score=context.get('surprise_score', 0)
                )

                context['imagination_budget_remaining'] = budget.get('total', 0.5)
                context['question_tier'] = budget.get('tier', 'Q1')

                return RungResult(
                    confidence=0.1,
                    reason=f"Imagination budget: {budget.get('total', 0.5):.2f}, tier={budget.get('tier', 'Q1')}",
                    metadata={'budget': budget}
                )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Imagination budget failed: {e}")


class CompletionPredictionRung(DecisionRung):
    """Estimate steps to completion - EXPLOITATION"""
    name = "completion_prediction"
    category = "exploitation"
    default_priority = 39
    confidence_threshold = 0.4

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        try:
            prediction = context.get('completion_prediction', {})

            if prediction:
                match_progress = prediction.get('match_progress', 0)
                remaining = prediction.get('remaining_steps', 100)

                # If close to completion, stay on sequence
                if match_progress > 0.8 and remaining < 10:
                    sequence_action = context.get('next_sequence_action')
                    # CRITICAL: Validate action is available in this game
                    if sequence_action and is_action_available(sequence_action, context):
                        return RungResult(
                            action=sequence_action,
                            confidence=0.7,
                            reason=f"Near completion: {match_progress:.0%}, {remaining} steps left",
                            metadata={'prediction': prediction}
                        )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Completion prediction failed: {e}")


class NetworkExplorationStatsRung(DecisionRung):
    """Track coverage, identify coldspots/hotspots - ORIENTATION"""
    name = "network_exploration_stats"
    category = "orientation"
    default_priority = 9
    confidence_threshold = 0.4

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        net = self.engines.network_exploration_tracker
        if net is None:
            return RungResult()

        try:
            game_type = context.get('game_type', '')
            level = context.get('level', 1)

            if hasattr(net, 'get_exploration_stats'):
                stats = net.get_exploration_stats(game_type, level)

                context['coverage_percent'] = stats.get('coverage_percent', 0)

                # If there are coldspots, bias toward them
                coldspots = stats.get('coldspots', [])
                if coldspots:
                    direction = stats.get('recommended_direction')
                    direction_map = {'north': 'ACTION1', 'south': 'ACTION2', 'west': 'ACTION3', 'east': 'ACTION4'}
                    if direction and direction in direction_map:
                        return RungResult(
                            action=direction_map[direction],
                            confidence=0.45,
                            reason=f"Exploring coldspot: {direction}, coverage={stats.get('coverage_percent', 0):.0%}",
                            metadata={'stats': stats, 'coldspots': len(coldspots)}
                        )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Network exploration stats failed: {e}")


# =============================================================================
# WIRED METACOGNITION RUNGS (Feb 2026)
# =============================================================================
# These rungs wire previously-unused methods from engines/cognition/ and
# engines/consciousness/ into the decision system.

class RuleTransferRung(DecisionRung):
    """Apply learned rules from other games - EXPLOITATION

    Wires: engines/cognition/rule_induction.py:
        - get_applicable_rules()
        - update_rule_success()  # Feedback loop

    Queries the learned_rules table for rules that match the current game frame.
    Enables cross-game knowledge transfer where patterns discovered in one game
    can guide action selection in structurally similar games.

    Feedback Loop: After action outcome, calls update_rule_success() to adjust
    rule confidence. Successful rules gain confidence (+0.05), failed rules lose (-0.1).
    """
    name = "rule_transfer"
    category = "exploitation"
    default_priority = 25  # After hypothesis, before network wisdom
    confidence_threshold = 0.5

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._rule_engine: Optional[Any] = None
        # Track active rule for feedback loop
        self._active_rule_id: Optional[str] = None
        self._active_rule_game: Optional[str] = None

    def _get_rule_engine(self) -> Optional[Any]:
        """Lazy-load rule induction engine."""
        if self._rule_engine is None:
            try:
                from database_interface import DatabaseInterface
                from engines.cognition.rule_induction import RuleInductionEngine
                db = DatabaseInterface()
                self._rule_engine = RuleInductionEngine(db)
            except ImportError as e:
                logger.debug(f"[RULE-TRANSFER] Failed to load RuleInductionEngine: {e}")
        return self._rule_engine

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        engine = self._get_rule_engine()
        if engine is None:
            return RungResult()

        try:
            frame = getattr(game_state, 'frame', None)
            if frame is None:
                return RungResult()

            agent_id = context.get('agent_id')
            min_confidence = self.confidence_threshold

            # Get rules that match current game frame
            applicable_rules = engine.get_applicable_rules(
                current_frame=frame,
                agent_id=agent_id,
                min_confidence=min_confidence
            )

            if not applicable_rules:
                return RungResult()

            # Use highest-confidence rule
            best_rule, confidence = applicable_rules[0]
            action_template = best_rule.get('action_template', {})
            suggested_action = action_template.get('action')

            if not suggested_action:
                return RungResult()

            # CRITICAL: Validate action is available in this game
            if not is_action_available(suggested_action, context):
                return RungResult(reason=f"Rule suggested unavailable action: {suggested_action}")

            # Track rule for feedback loop (instance-level, not context-level)
            self._active_rule_id = best_rule.get('rule_id')
            self._active_rule_game = context.get('game_type', '')

            return RungResult(
                action=suggested_action,
                confidence=confidence,
                reason=f"Rule transfer: {best_rule.get('rule_type', 'unknown')} from {best_rule.get('source_game', 'network')}",
                metadata={
                    'rule_id': best_rule.get('rule_id'),
                    'rule_type': best_rule.get('rule_type'),
                    'source_game': best_rule.get('source_game'),
                    'match_confidence': confidence,
                    'success_count': best_rule.get('success_count', 0),
                }
            )
        except Exception as e:
            return RungResult(reason=f"Rule transfer failed: {e}")

    def record_outcome(self, was_accepted: bool, success: bool = False) -> None:
        """Update rule success/failure after action outcome.

        Wires: engines/cognition/rule_induction.py:update_rule_success()
        This closes the feedback loop - rules that work gain confidence,
        rules that fail lose confidence.
        """
        super().record_outcome(was_accepted)

        # If rule was used and we have outcome, update the rule
        if was_accepted and self._active_rule_id and self._rule_engine is not None:
            try:
                self._rule_engine.update_rule_success(
                    rule_id=self._active_rule_id,
                    success=success,
                    target_game_id=self._active_rule_game or 'unknown'
                )
            except Exception:
                pass  # Don't fail silently, but don't break gameplay
            finally:
                # Clear active rule after feedback
                self._active_rule_id = None
                self._active_rule_game = None

class TheoryContradictionRung(DecisionRung):
    """Filter actions that contradict current working theory - FILTER

    Wires: engines/cognition/metacognition.py:get_contradicted_actions()

    When metacognition's theory revision marks actions as contradicted
    (failed prediction -> action disproven), this rung applies negative
    weights to those actions, preventing repeated mistakes.
    """
    name = "theory_contradiction"
    category = "filter"
    default_priority = 17  # After death_avoidance (15), before hypothesis
    confidence_threshold = 0.3

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        me = self.engines.metacognitive_engine
        if me is None:
            return RungResult()

        try:
            # Get actions contradicted by failed theories
            if not hasattr(me, 'get_contradicted_actions'):
                return RungResult()

            contradicted = me.get_contradicted_actions()

            if not contradicted:
                return RungResult()

            # Build penalty weights for contradicted actions (available only)
            weights = get_available_action_weights(context, 1.0)
            penalized = []

            for action_str, contradiction_count in contradicted.items():
                if action_str in weights:
                    # More contradictions = stronger penalty
                    # 1 contradiction = 0.7, 2 = 0.5, 3+ = 0.3
                    penalty = min(0.7, 0.2 * contradiction_count)
                    weights[action_str] = max(0.3, 1.0 - penalty)
                    penalized.append(f"{action_str}({contradiction_count})")

            if not penalized:
                return RungResult()

            return RungResult(
                confidence=0.5,
                reason=f"Theory contradictions: {', '.join(penalized)}",
                weights=weights,
                metadata={'contradicted_actions': contradicted}
            )
        except Exception as e:
            return RungResult(reason=f"Theory contradiction failed: {e}")


class HypothesisTestingRung(DecisionRung):
    """Test untested assumptions to validate or disprove them - HYPOTHESIS

    Wires: engines/cognition/metacognition.py:
        - get_untested_assumptions()
        - register_assumption()
        - challenge_assumption()

    Prioritizes actions that would test currently-held assumptions.
    E.g., if agent assumes "ACTION1 moves me up", this rung will
    suggest ACTION1 when testing is needed.
    """
    name = "hypothesis_testing"
    category = "hypothesis"
    default_priority = 19  # After metacognitive_prediction (18)
    confidence_threshold = 0.4

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        me = self.engines.metacognitive_engine
        if me is None:
            return RungResult()

        try:
            game_type = context.get('game_type', '')
            level = context.get('level', 1)

            # Get untested assumptions for this game/level
            if not hasattr(me, 'get_untested_assumptions'):
                return RungResult()

            untested = me.get_untested_assumptions(game_type, level)

            if not untested:
                return RungResult()

            # Find an assumption we can test
            for assumption in untested:
                assumption_text = assumption.get('assumption_text', '')
                assumption_type = assumption.get('assumption_type', '')
                assumption_id = assumption.get('assumption_id', '')

                # Parse assumption to find testable action
                # E.g., "ACTION1 moves me up" -> suggest ACTION1
                import re
                action_match = re.search(r'ACTION(\d+)', assumption_text.upper())

                if action_match:
                    action = f"ACTION{action_match.group(1)}"
                    # Store assumption_id for challenge_assumption callback
                    context['_testing_assumption_id'] = assumption_id
                    context['_testing_assumption_text'] = assumption_text

                    return RungResult(
                        action=action,
                        confidence=0.55,
                        reason=f"Testing: {assumption_text[:50]}",
                        metadata={
                            'assumption_id': assumption_id,
                            'assumption_type': assumption_type,
                            'assumption_text': assumption_text,
                        }
                    )

                # For non-action assumptions (e.g., "blue is goal"), no direct action
                # but we can store for later validation

            return RungResult(
                confidence=0.1,
                reason=f"{len(untested)} untested assumptions, none directly testable",
                metadata={'untested_count': len(untested)}
            )
        except Exception as e:
            return RungResult(reason=f"Hypothesis testing failed: {e}")


class SelfTrustBoostRung(DecisionRung):
    """Manage wA (self-trust) based on context - ORIENTATION

    Wires: engines/consciousness/i_thread.py:
        - boost_self_trust()
        - restore_self_trust()

    On frontier levels (no winning sequences), boosts self-trust to encourage
    exploration over network following. When sequences become available,
    restores normal trust balance.

    This implements the Two Streams principle: trust yourself more when
    network wisdom doesn't apply.
    """
    name = "self_trust_boost"
    category = "orientation"
    default_priority = 3  # Very early - affects all downstream decisions
    confidence_threshold = 0.0  # Always runs, just adjusts weights

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._last_frontier_state: Dict[str, bool] = {}  # agent_id -> was_frontier

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        i_thread = self.engines.i_thread
        if i_thread is None:
            return RungResult()

        try:
            agent_id = context.get('agent_id', 'default')
            is_frontier = context.get('frontier_mode', False) or context.get('is_frontier', False)
            has_sequence = context.get('has_winning_sequence', False) or context.get('active_sequence')

            # Track state transition
            was_frontier = self._last_frontier_state.get(agent_id, False)
            self._last_frontier_state[agent_id] = is_frontier

            # Boost when entering frontier (no sequences available)
            if is_frontier and not has_sequence and not was_frontier:
                if hasattr(i_thread, 'boost_self_trust'):
                    original, boosted, new_wB = i_thread.boost_self_trust(
                        agent_id=agent_id,
                        boost_amount=0.25,
                        reason='frontier_exploration'
                    )
                    return RungResult(
                        confidence=0.1,  # Context modifier, not action suggestion
                        reason=f"Frontier boost: wA {original:.2f} -> {boosted:.2f}",
                        metadata={
                            'boost_applied': True,
                            'original_wA': original,
                            'boosted_wA': boosted,
                            'trigger': 'frontier_entry'
                        }
                    )

            # Restore when leaving frontier (sequences now available)
            if (not is_frontier or has_sequence) and was_frontier:
                if hasattr(i_thread, 'restore_self_trust'):
                    restored_wA, restored_wB = i_thread.restore_self_trust(agent_id=agent_id)
                    return RungResult(
                        confidence=0.1,
                        reason=f"Trust restored: wA -> {restored_wA:.2f}",
                        metadata={
                            'restore_applied': True,
                            'restored_wA': restored_wA,
                            'trigger': 'frontier_exit'
                        }
                    )

            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Self trust boost failed: {e}")


class AssumptionFormationRung(DecisionRung):
    """Form and register assumptions based on observed patterns - HYPOTHESIS

    Wires: engines/cognition/metacognition.py:
        - register_assumption()
        - challenge_assumption()

    Monitors gameplay to detect correlations and form testable assumptions.
    E.g., "When I press ACTION1, the blue object moves up" -> registers assumption.

    This is the WRITE side of the assumption system (HypothesisTestingRung is READ).
    Together they form a complete hypothesis testing loop:
    1. AssumptionFormationRung detects correlation -> register_assumption()
    2. HypothesisTestingRung suggests action to test -> get_untested_assumptions()
    3. After outcome -> challenge_assumption() to validate/invalidate
    """
    name = "assumption_formation"
    category = "hypothesis"
    default_priority = 16  # Before hypothesis_testing
    confidence_threshold = 0.3

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        # Track recent observations for pattern detection
        self._recent_observations: List[Dict[str, Any]] = []
        self._max_observations = 20

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        me = self.engines.metacognitive_engine
        if me is None:
            return RungResult()

        try:
            game_type = context.get('game_type', '')
            level = context.get('level', 1)
            agent_id = context.get('agent_id', 'default')
            last_action = context.get('last_action')
            frame_change = context.get('frame_change', {})

            # Skip if no action taken yet
            if not last_action:
                return RungResult()

            # Record observation
            observation = {
                'action': last_action,
                'frame_change': frame_change,
                'score_delta': context.get('score_delta', 0),
                'game_type': game_type,
                'level': level,
            }
            self._recent_observations.append(observation)
            if len(self._recent_observations) > self._max_observations:
                self._recent_observations.pop(0)

            # Need at least 3 observations to detect patterns
            if len(self._recent_observations) < 3:
                return RungResult()

            # Look for consistent action->outcome correlations
            assumptions_formed = []
            action_outcomes: Dict[str, List[Dict]] = {}

            for obs in self._recent_observations:
                action = obs.get('action', '')
                if action:
                    if action not in action_outcomes:
                        action_outcomes[action] = []
                    action_outcomes[action].append(obs)

            # Check each action for consistent outcomes
            for action, outcomes in action_outcomes.items():
                if len(outcomes) >= 2:
                    # Check for consistent positive score
                    positive_scores = [o for o in outcomes if o.get('score_delta', 0) > 0]
                    if len(positive_scores) >= 2:
                        assumption_text = f"{action} consistently gives positive score"
                        if hasattr(me, 'register_assumption'):
                            assumption_id = me.register_assumption(
                                agent_id=agent_id,
                                game_type=game_type,
                                level_number=level,
                                assumption=assumption_text,
                                assumption_type='rule'
                            )
                            assumptions_formed.append(assumption_text)

                    # Check for consistent negative score (form avoidance assumption)
                    negative_scores = [o for o in outcomes if o.get('score_delta', 0) < 0]
                    if len(negative_scores) >= 2:
                        assumption_text = f"{action} consistently causes penalty"
                        if hasattr(me, 'register_assumption'):
                            me.register_assumption(
                                agent_id=agent_id,
                                game_type=game_type,
                                level_number=level,
                                assumption=assumption_text,
                                assumption_type='rule'
                            )
                            assumptions_formed.append(assumption_text)

            if assumptions_formed:
                return RungResult(
                    confidence=0.3,
                    reason=f"Formed {len(assumptions_formed)} assumptions",
                    metadata={'assumptions': assumptions_formed}
                )

            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Assumption formation failed: {e}")


class ContextualFailureRung(DecisionRung):
    """Track contextual failures - position/direction/object-aware - FILTER

    Unlike global action elimination, tracks CONTEXTUAL failure signatures:
    - Position region where failure occurred
    - Direction of movement (toward/away from object)
    - Nearby object types at time of failure

    This allows "ACTION3 toward wall at (3,4)" to be avoided without
    eliminating ACTION3 globally (which could deadlock all movement).

    Failure signatures decay over time (things can change).
    """
    name = "contextual_failure"
    category = "filter"
    default_priority = 14  # Before death_avoidance
    confidence_threshold = 0.3

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        # In-memory failure signatures (per game_type, per level)
        # Structure: {(game_type, level): [FailureSignature, ...]}
        self._failure_signatures: Dict[Tuple[str, int], List[Dict[str, Any]]] = {}
        self._max_signatures_per_level = 50
        self._signature_decay_rate = 0.1  # Per evaluation cycle

    def _compute_position_region(self, position: Tuple[int, int]) -> Tuple[int, int]:
        """Bucket position into regions for fuzzy matching."""
        # 3x3 region bucketing - positions (0,0), (0,1), (0,2) all -> region (0, 0)
        return (position[0] // 3, position[1] // 3)

    def _compute_movement_direction(self, action: str, nearby_objects: List[Dict]) -> str:
        """Determine if action moves toward/away/parallel to nearest object."""
        # Simplified: Map actions to directions
        action_directions = {
            'ACTION1': 'up', 'ACTION2': 'down',
            'ACTION3': 'left', 'ACTION4': 'right',
            'ACTION5': 'stay', 'ACTION7': 'special',
        }
        direction = action_directions.get(action, 'unknown')

        if not nearby_objects:
            return 'no_nearby_object'

        # For simplicity, just return the direction - full implementation would
        # compute vector from agent to nearest object and compare
        return f"{direction}_near_object"

    def record_failure(
        self,
        game_type: str,
        level: int,
        position: Tuple[int, int],
        action: str,
        nearby_objects: List[Dict[str, Any]],
        outcome: str = 'death'
    ) -> None:
        """Record a contextual failure signature."""
        key = (game_type, level)

        if key not in self._failure_signatures:
            self._failure_signatures[key] = []

        signature = {
            'game_type': game_type,
            'level': level,
            'position_region': self._compute_position_region(position),
            'action': action,
            'movement_context': self._compute_movement_direction(action, nearby_objects),
            'nearby_colors': [o.get('color') for o in nearby_objects[:3]],
            'outcome': outcome,
            'confidence': 0.8,  # Initial confidence
            'created_at': datetime.now().isoformat(),
        }

        self._failure_signatures[key].append(signature)

        # Prune old signatures
        if len(self._failure_signatures[key]) > self._max_signatures_per_level:
            # Remove lowest confidence signatures
            self._failure_signatures[key].sort(key=lambda s: s['confidence'], reverse=True)
            self._failure_signatures[key] = self._failure_signatures[key][:self._max_signatures_per_level]

    def _decay_signatures(self, key: Tuple[str, int]) -> None:
        """Apply decay to signatures, removing those below threshold."""
        if key not in self._failure_signatures:
            return

        decayed = []
        for sig in self._failure_signatures[key]:
            sig['confidence'] -= self._signature_decay_rate
            if sig['confidence'] > 0.2:  # Keep if still confident
                decayed.append(sig)

        self._failure_signatures[key] = decayed

    def _match_signature(
        self,
        action: str,
        position: Tuple[int, int],
        nearby_objects: List[Dict],
        signatures: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Check if current context matches any failure signature."""
        current_region = self._compute_position_region(position)
        current_context = self._compute_movement_direction(action, nearby_objects)
        current_colors = set(o.get('color') for o in nearby_objects[:3])

        for sig in signatures:
            # Must match action
            if sig['action'] != action:
                continue

            # Must match position region
            if sig['position_region'] != current_region:
                continue

            # Check color overlap (at least one matching nearby color)
            sig_colors = set(sig.get('nearby_colors', []))
            if sig_colors and current_colors and not sig_colors.intersection(current_colors):
                continue

            # Match found
            return sig

        return None

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        try:
            game_type = context.get('game_type', '')
            level = context.get('level', 1)
            position = context.get('agent_position', (0, 0))
            nearby_objects = context.get('nearby_objects', [])

            key = (game_type, level)

            # Apply decay each evaluation
            self._decay_signatures(key)

            signatures = self._failure_signatures.get(key, [])
            if not signatures:
                return RungResult()

            # Record failure if last action caused death/penalty
            if context.get('last_outcome') == 'death' or context.get('score_delta', 0) < 0:
                last_action = context.get('last_action')
                last_position = context.get('last_position', position)
                if last_action:
                    self.record_failure(
                        game_type=game_type,
                        level=level,
                        position=last_position,
                        action=last_action,
                        nearby_objects=nearby_objects,
                        outcome='death' if context.get('last_outcome') == 'death' else 'penalty'
                    )

            # Check each action for matching failure signatures (available only)
            weights = get_available_action_weights(context, 1.0)
            penalized_actions = []
            available = context.get('available_actions', [1, 2, 3, 4, 5, 6, 7])

            for action_num in available:
                action = f'ACTION{action_num}'
                match = self._match_signature(action, position, nearby_objects, signatures)

                if match:
                    # Penalty proportional to signature confidence
                    penalty = match['confidence'] * 0.5  # Max 50% weight reduction
                    weights[action] = max(0.3, 1.0 - penalty)
                    penalized_actions.append(
                        f"{action}@{match['position_region']}({match['confidence']:.1f})"
                    )

            if penalized_actions:
                return RungResult(
                    confidence=0.4,
                    reason=f"Contextual failures: {', '.join(penalized_actions[:3])}",
                    weights=weights,
                    metadata={
                        'matched_signatures': len(penalized_actions),
                        'total_signatures': len(signatures),
                    }
                )

            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Contextual failure check failed: {e}")


# =============================================================================
# ORDERING PRESETS (DEPRECATED - Phase 6)
# =============================================================================
#
# DEPRECATION NOTICE: Static ordering presets are deprecated as of Phase 6.
# Use DecisionStrategy.COGNITIVE with CognitiveRouter for dynamic selection.
# These presets will be removed in v3.0.
#
# Migration path:
#   1. Switch strategy to COGNITIVE: DecisionRungSystem(strategy='cognitive')
#   2. CognitiveRouter handles graph-based rung selection automatically
#   3. Edge weights evolve based on observed outcomes
#
# For details see: architecture/cognitive_routing_implementation_plan.md
#

ORDERING_PRESETS = {
    # Current behavior - efficiency-optimized (15 rungs - core only)
    'efficiency': [
        ('infinite_loop_breaker', 1),
        ('coordinate_oscillation', 3),
        ('palette_detection', 3),  # Two-stage: extract objects + detect palette FIRST
        ('frontier_checkpoint', 4),  # Skip explored territory on frontier
        ('three_try_sequence', 5),
        ('discovery_exploitation', 10),
        ('death_avoidance', 15),
        ('prior_lessons', 16),  # NEW: Apply game lessons as weights
        ('terminal_pattern', 17),
        ('embedding_suggestion', 20),
        ('frontier_topology', 25),
        ('exploration_phase', 30),
        ('two_streams', 35),
        ('primitive_suggester', 40),
        ('network_wisdom', 45),
        ('smart_action_selection', 99),
    ],

    # LLM-optimal - understanding first (all 48 rungs including wired metacognition)
    'llm_optimal': [
        ('infinite_loop_breaker', 1),
        ('coordinate_oscillation', 2),
        ('palette_detection', 3),  # Two-stage: extract objects + detect palette FIRST
        ('self_trust_boost', 4),  # Manage wA based on frontier/replay context
        ('control_tracker', 5),  # "I am this object" - self-model
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
        ('symbolic_tracker', 23),  # Key/lock symbolic matching
        ('theory_gate', 24),
        ('belief_system', 25),  # Belief tracking
        ('hypothesis_system', 26),  # Agent-initiated hypothesis testing
        ('sensation_engine', 27),
        ('resonance_detector', 28),
        ('valence_goals', 29),  # Good/bad valence and goals
        ('network_wisdom', 30),
        ('death_avoidance', 32),
        ('terminal_pattern', 34),
        ('theory_contradiction', 35),  # Filter actions contradicted by failed theories
        ('pariah_avoidance', 36),
        ('three_layer_filter', 38),
        ('hypothesis_testing', 39),  # Test untested assumptions
        ('three_try_sequence', 40),
        ('rule_transfer', 41),  # Apply rules from other games
        ('discovery_exploitation', 42),
        ('trigger_sequences', 43),  # Trigger chain learning
        ('embedding_suggestion', 44),
        ('embedding_matcher', 45),  # Neural frame similarity
        ('multi_stage_matching', 46),
        ('primitive_suggester', 48),  # Direct primitive-to-action
        ('network_sharing', 49),  # Network control hypotheses
        ('replay_learning', 50),
        ('network_wisdom', 51),
        ('abstraction_templates', 54),
        ('few_shot_relations', 55),  # Control invariants from examples
        ('few_shot_invariants', 56),
        ('subgoal_planning', 58),
        ('visual_analyzer', 60),
        ('network_object_inventory', 62),
        ('action6_object_exploration', 64),  # Use Action6BehaviorEngine for click targets
        ('click_behavior_learning', 65),  # Learn click patterns (collectibles, triggers)
        ('near_miss_analyzer', 66),
        ('completion_prediction', 68),
        ('frontier_topology', 70),
        ('map_intel_collision', 72),
        ('exploration_phase', 74),
        ('grid_exploration', 76),  # Fallback: systematic grid walking
        ('smart_action_selection', 99),
    ],

    # Human brain - parallel attention + fear interrupt
    'human_brain': [
        ('infinite_loop_breaker', 1),   # Panic response
        ('coordinate_oscillation', 2),  # Repetitive behavior detection
        ('palette_detection', 3),       # Object extraction + palette detection
        ('death_avoidance', 4),         # Amygdala - fast fear (12ms)
        ('terminal_pattern', 5),        # Pattern recognition of danger
        ('survey', 6),                  # Attention - what's salient?
        ('embedding_suggestion', 8),    # Pattern recognition - I've seen this
        ('network_wisdom', 10),         # Social learning - what did others do?
        ('pariah_avoidance', 12),       # Social learning - what to avoid
        ('exploration_phase', 14),      # Curiosity - novelty seeking
        ('scientific_method', 20),      # Prefrontal - slow reasoning
        ('theory_gate', 22),            # Theory validation
        ('metacognitive_prediction', 24), # Am I confused?
        ('i_thread', 26),               # Self-awareness
        ('two_streams', 28),            # Conflict detection
        ('sensation_engine', 30),       # Emotional coloring
        ('primitive_suggester', 35),    # Primitive-based reasoning
        ('discovery_exploitation', 40), # Use what works
        ('smart_action_selection', 99),
    ],

    # Full 49-rung comprehensive ordering (includes wired metacognition rungs + palette detection)
    'comprehensive': [
        # EMERGENCY (Priority 1-5)
        ('infinite_loop_breaker', 1),
        ('coordinate_oscillation', 2),
        ('palette_detection', 3),  # Two-stage: extract objects + detect palette FIRST
        ('sparse_grid', 3),        # Sparse grid representation for efficient pattern matching
        ('self_trust_boost', 4),  # Manage wA based on context
        ('frame_interpretation', 5),  # Context setting for dramatic frame changes

        # ORIENTATION - Understanding the world (Priority 5-20)
        ('imagination_budget', 6),
        ('breakthrough_budget', 7),
        ('control_tracker', 8),  # "I am this object" - self-model
        ('regulatory_signal', 9),
        ('survey', 10),
        ('network_exploration_stats', 11),
        ('questioning_engine', 12),
        ('exploration_phase', 13),
        ('frustration_detection', 14),

        # FILTER - Modify action weights (Priority 15-25)
        ('contextual_failure', 15),   # Context-aware failure avoidance (before death_avoidance)
        ('death_avoidance', 16),
        ('terminal_pattern', 17),
        ('theory_contradiction', 18),  # Filter contradicted actions
        ('pariah_avoidance', 19),
        ('three_layer_filter', 20),

        # HYPOTHESIS - Form and test theories (Priority 25-40)
        ('event_understanding', 23),  # Causal world model
        ('symbolic_tracker', 24),  # Key/lock symbolic matching
        ('assumption_formation', 25), # Form assumptions from observations
        ('belief_system', 26),  # Belief tracking
        ('hypothesis_system', 27),  # Agent-initiated hypothesis testing
        ('scientific_method', 28),
        ('theory_gate', 29),
        ('metacognitive_prediction', 30),
        ('hypothesis_testing', 31),  # Test untested assumptions
        ('deliberation_system', 32),
        ('two_streams', 33),
        ('i_thread', 34),
        ('valence_goals', 35),  # Good/bad valence and goals
        ('sensation_engine', 36),
        ('resonance_detector', 37),

        # EXPLOITATION - Use known knowledge (Priority 40-80)
        ('three_try_sequence', 40),
        ('rule_transfer', 41),  # Apply rules from other games
        ('state_matching', 42), # Symbolic reasoning - property matching
        ('trigger_sequences', 43),  # Trigger chain learning
        ('discovery_exploitation', 44),
        ('embedding_matcher', 45),  # Neural frame similarity
        ('spatial_relationship', 46),  # Click effect patterns for puzzles
        ('embedding_suggestion', 47),
        ('multi_stage_matching', 48),
        ('primitive_suggester', 49),  # Direct primitive-to-action
        ('network_sharing', 50),  # Network control hypotheses
        ('replay_learning', 51),
        ('network_wisdom', 52),
        ('abstraction_templates', 53),
        ('few_shot_relations', 54),  # Control invariants from examples
        ('few_shot_invariants', 55),
        ('subgoal_planning', 56),
        ('visual_analyzer', 57),
        ('network_object_inventory', 58),
        ('action6_object_exploration', 59),  # Use Action6BehaviorEngine for click targets
        ('click_behavior_learning', 60),  # Learn click patterns (collectibles, triggers)
        ('near_miss_analyzer', 61),
        ('completion_prediction', 62),
        ('frontier_topology', 63),
        ('map_intel_collision', 64),
        ('grid_exploration', 65),  # Fallback: systematic grid walking

        # FALLBACK (Priority 99)
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

    # ==========================================================================
    # ACTION6 WORLD - For games where ACTION6 is available/primary
    # ==========================================================================
    # When ACTION6 is available, the game transforms from "move in direction"
    # to "interact with a world of objects". This is a fundamentally different
    # cognitive paradigm requiring:
    # 1. Object detection and categorization (what's in the world?)
    # 2. Self-model (what do I control? what can I select?)
    # 3. World model (what are the physics? what happens when I click X?)
    # 4. Causality understanding (click A -> enables B -> unlocks C)
    # 5. Button/trigger detection (what's interactive?)
    # 6. Strategic targeting (click meaningful things, not random)
    #
    # Think of ACTION6 as a touchpad - every frame is a touchscreen interface
    # where objects have different roles: player, obstacles, triggers, goals.
    # ==========================================================================
    'action6_world': [
        # EMERGENCY - Still need these
        ('infinite_loop_breaker', 1),
        ('coordinate_oscillation', 2),

        # PERCEPTION - Understand the visual world FIRST
        ('palette_detection', 3),  # Extract objects and colors from frame
        ('sparse_grid', 4),        # Efficient spatial representation
        ('visual_analyzer', 5),    # Deep frame analysis

        # SELF-MODEL - What do I control? What can I select?
        ('control_tracker', 6),    # "I am this object" / "I can select these"
        ('frame_interpretation', 7),  # What changed? What did my click cause?

        # WORLD MODEL - What are the rules of this world?
        ('event_understanding', 8),  # Causal chains: click X -> Y happens
        ('trigger_sequences', 9),   # Learn trigger/button chains
        ('click_behavior_learning', 10),  # What do clicks DO in this game?
        ('belief_system', 11),      # Current beliefs about the world
        ('symbolic_tracker', 12),   # Key/lock, button/door relationships

        # OBJECT TARGETING - Find meaningful click targets
        ('action6_object_exploration', 13),  # Find clickable objects
        ('network_object_inventory', 14),    # What objects does network know?
        ('primitive_suggester', 15),         # Primitive-to-action mapping

        # HYPOTHESIS - Form theories about unknown objects
        ('hypothesis_system', 16),  # "I think clicking blue opens the door"
        ('scientific_method', 17),  # Test and validate theories
        ('theory_gate', 18),        # Score proposals against working theory
        ('assumption_formation', 19),  # Form assumptions from observations

        # NETWORK KNOWLEDGE - What has the colony learned?
        ('network_wisdom', 20),     # Community knowledge about this game
        ('network_sharing', 21),    # Cross-agent self-model sharing
        ('few_shot_relations', 22), # Control invariants from examples
        ('resonance_detector', 23), # Patterns that resonate across games

        # VALENCE - What's good/bad to click?
        ('valence_goals', 24),      # Good/bad associations
        ('death_avoidance', 25),    # Don't click things that kill
        ('pariah_avoidance', 26),   # Avoid known-bad patterns

        # EXPLORATION - Systematic when all else fails
        ('grid_exploration', 30),   # Systematic grid walking
        ('exploration_phase', 35),  # Budget-based exploration

        # METACOGNITION - Am I stuck? Am I learning?
        ('frustration_detection', 40),
        ('metacognitive_prediction', 41),

        # FALLBACK
        ('smart_action_selection', 99),
    ],

    # ACTION6-only game (like vc33) - everything is about understanding the touchscreen
    'action6_only': [
        # EMERGENCY
        ('infinite_loop_breaker', 1),
        ('coordinate_oscillation', 2),

        # PERCEPTION - What's on the screen?
        ('palette_detection', 3),
        ('sparse_grid', 4),
        ('visual_analyzer', 5),

        # OBJECT UNDERSTANDING - This is the core for click-only games
        ('action6_object_exploration', 6),  # ELEVATED: Primary action
        ('click_behavior_learning', 7),     # ELEVATED: Learn what clicks do
        ('trigger_sequences', 8),           # ELEVATED: Button chains
        ('network_object_inventory', 9),    # What objects exist?

        # WORLD MODEL - Causality is everything
        ('event_understanding', 10),  # What causes what?
        ('belief_system', 11),
        ('symbolic_tracker', 12),     # Key/lock relationships
        ('control_tracker', 13),      # What can I select/control?

        # HYPOTHESIS - Test theories about objects
        ('hypothesis_system', 14),
        ('scientific_method', 15),
        ('theory_gate', 16),

        # NETWORK - Community knowledge
        ('network_wisdom', 17),
        ('network_sharing', 18),
        ('primitive_suggester', 19),
        ('valence_goals', 20),

        # SAFETY
        ('death_avoidance', 25),
        ('pariah_avoidance', 26),

        # EXPLORATION - Systematic coverage
        ('grid_exploration', 30),
        ('exploration_phase', 35),

        # FALLBACK
        ('smart_action_selection', 99),
    ],

    # Exploration-heavy for frontier games (includes trust boost + palette detection)
    'frontier_exploration': [
        ('infinite_loop_breaker', 1),
        ('coordinate_oscillation', 2),
        ('palette_detection', 3),  # Two-stage: objects + palette FIRST
        ('self_trust_boost', 4),  # Boost wA on frontier entry
        ('frontier_checkpoint', 5),  # Replay best known progress on frontier
        ('survey', 6),
        ('network_exploration_stats', 8),
        ('exploration_phase', 10),
        ('assumption_formation', 11),  # Form assumptions during exploration
        ('hypothesis_testing', 12),  # Test assumptions during exploration
        ('contextual_failure', 13),  # Avoid contextual failures (not global)
        ('questioning_engine', 15),
        ('scientific_method', 20),
        ('rule_transfer', 22),  # Apply rules from similar games
        ('action6_object_exploration', 24),  # Use Action6BehaviorEngine for click targets
        ('click_behavior_learning', 25),  # Learn click patterns for ACTION6 games
        ('grid_exploration', 26),  # Fallback: systematic grid walking
        ('death_avoidance', 40),  # Lower priority on frontier
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
    """

    # Registry of all available rungs (46 + assumption_formation + contextual_failure = 48)
    RUNG_REGISTRY: Dict[str, type] = {
        # Core 15 rungs (original + prior_lessons)
        'survey': SurveyRung,
        'questioning_engine': QuestioningRung,
        'death_avoidance': DeathAvoidanceRung,
        'prior_lessons': PriorLessonsRung,  # NEW: Apply lessons as graduated weights
        'discovery_exploitation': DiscoveryExploitationRung,
        'embedding_suggestion': EmbeddingSuggestionRung,
        'scientific_method': ScientificMethodRung,
        'two_streams': TwoStreamsRung,
        'network_wisdom': NetworkWisdomRung,
        'primitive_suggester': PrimitiveSuggesterRung,  # Replaced cods_engine
        'metacognitive_prediction': MetacognitivePredictionRung,
        'exploration_phase': ExplorationPhaseRung,
        'frontier_topology': FrontierTopologyRung,
        'smart_action_selection': SmartActionSelectionRung,
        'infinite_loop_breaker': InfiniteLoopBreakerRung,

        # External/supporting systems (Features 14-28)
        'map_intel_collision': MapIntelCollisionRung,
        'theory_gate': TheoryGateRung,
        'abstraction_templates': AbstractionTemplatesRung,
        'few_shot_invariants': FewShotInvariantsRung,
        'frontier_checkpoint': FrontierCheckpointRung,  # NEW: Constructive pathfinding
        'three_try_sequence': ThreeTrySequenceRung,
        'multi_stage_matching': MultiStageMatchingRung,
        'three_layer_filter': ThreeLayerFilterRung,
        'pariah_avoidance': PariahAvoidanceRung,
        'frustration_detection': FrustrationDetectionRung,
        'terminal_pattern': TerminalPatternRung,
        'sensation_engine': SensationEngineRung,
        'i_thread': IThreadRung,
        'near_miss_analyzer': NearMissAnalyzerRung,
        'state_matching': StateMatchingRung,         # Symbolic reasoning - compare properties to goals
        'palette_detection': PaletteDetectionRung,   # Two-stage: extract objects + detect palette FIRST
        'sparse_grid': SparseGridRung,               # Sparse grid representation for pattern matching
        'frame_interpretation': FrameInterpretationRung,  # Context setting for dramatic frame changes
        'event_understanding': EventUnderstandingRung,    # Causal world model for physics games
        'spatial_relationship': SpatialRelationshipRung,  # Click effect patterns for puzzles
        'subgoal_planning': SubgoalPlanningRung,
        'breakthrough_budget': BreakthroughBudgetRung,
        'regulatory_signal': RegulatorySignalRung,
        'visual_analyzer': VisualAnalyzerRung,
        'resonance_detector': ResonanceDetectorRung,

        # Console log features (Features 29-36) - removed: micro_counterfactual, primitive_stuck_detection (stubs)
        'coordinate_oscillation': CoordinateOscillationRung,
        'grid_exploration': GridExplorationRung,
        'network_object_inventory': NetworkObjectInventoryRung,
        'action6_object_exploration': Action6ObjectExplorationRung,  # Use Action6BehaviorEngine for click targets
        'click_behavior_learning': ClickBehaviorLearningRung,  # Learn click patterns (collectibles, triggers)

        # Self-model and symbolic reasoning (Feb 2026 wiring)
        'control_tracker': ControlTrackerRung,      # "I am this object" tracking
        'belief_system': BeliefSystemRung,          # Belief tracking with cascade invalidation
        'hypothesis_system': HypothesisSystemRung,  # Agent-initiated hypothesis testing
        'trigger_sequences': TriggerSequencesRung,  # Trigger chain learning
        'symbolic_tracker': SymbolicTrackerRung,    # Key/lock symbolic matching

        # Remaining orphaned engines wired (Feb 2026)
        'embedding_matcher': EmbeddingMatcherRung,  # Neural frame similarity
        'few_shot_relations': FewShotRelationsRung,  # Control invariants from examples
        'network_sharing': NetworkSharingRung,      # Network control hypotheses
        'primitive_suggester': PrimitiveSuggesterRung,  # Direct primitive-to-action
        'valence_goals': ValenceGoalsRung,          # Good/bad valence and goals

        # Reasoning log features (Features 37-42)
        'deliberation_system': DeliberationSystemRung,
        'replay_learning': ReplayLearningRung,
        'imagination_budget': ImaginationBudgetRung,
        'completion_prediction': CompletionPredictionRung,
        'network_exploration_stats': NetworkExplorationStatsRung,

        # Wired metacognition rungs (Feb 2026) - previously-unused methods now integrated
        'rule_transfer': RuleTransferRung,           # Cross-game rule application
        'theory_contradiction': TheoryContradictionRung,  # Filter contradicted actions
        'hypothesis_testing': HypothesisTestingRung,  # Test untested assumptions
        'self_trust_boost': SelfTrustBoostRung,      # Manage wA based on context
        'assumption_formation': AssumptionFormationRung,  # Form testable assumptions
        'contextual_failure': ContextualFailureRung,  # Context-aware failure avoidance
    }

    def __init__(self,
                 strategy: str = 'context_adaptive',
                 core_gameplay_ref: Any = None,
                 config_path: Optional[str] = None,
                 engine_registry: Optional["EngineRegistry"] = None,
                 cognitive_router: Optional[Any] = None,
                 routing_trace_store: Optional[Any] = None):
        """
        Args:
            strategy: 'ladder', 'weighted', 'phased', 'parallel', 'cognitive', or 'context_adaptive' (default)
            core_gameplay_ref: Reference to CoreGameplay instance (legacy)
            config_path: Optional path to custom ordering config
            engine_registry: EngineRegistry for modular engine access (preferred)
            cognitive_router: Pre-configured CognitiveRouter instance (avoids lazy-load duplication)
            routing_trace_store: RoutingTraceStore for recording decision traces

        Note: CONTEXT_ADAPTIVE is recommended - it selects strategy based on game context:
        - replay_mode (following winning sequence): LADDER - deterministic replay
        - frontier_mode (unbeaten level): WEIGHTED - all rungs vote
        - optimization_mode (refining beaten game): WEIGHTED - find improvements
        - Emergency rungs (loop_breaker, oscillation) always checked first with LADDER semantics

        For COGNITIVE strategy: Pass a configured CognitiveRouter for transition-driven routing.
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

        # Track winning rung for feedback loop (so we can report outcome back)
        self._last_winning_rung: Optional[DecisionRung] = None

        # Store last outcome context for rungs that need extra details
        self._last_outcome_context: Dict[str, Any] = {}

        # =====================================================================
        # TEMPORAL INTEGRATION - Multi-scale experience integration
        # Maps existing categories to modulation categories:
        #   exploration: hypothesis, orientation (trying new things)
        #   exploitation: exploitation (using known strategies)
        #   safety: filter, emergency (avoiding harm)
        #   neutral: fallback, metacognition (not modulated)
        # =====================================================================
        self._temporal_integrator = None  # Lazy-loaded
        self._category_modulation_map = {
            # Exploration-like categories (suppressed when struggling)
            'hypothesis': 'exploration',
            'orientation': 'exploration',
            # Exploitation categories (boosted when struggling)
            'exploitation': 'exploitation',
            # Safety categories (boosted at extremes)
            'filter': 'safety',
            'emergency': 'safety',
            # Neutral (not modulated)
            'fallback': 'neutral',
            'metacognition': 'neutral',
            'unknown': 'neutral',
        }

        # Current temporal context (set by caller)
        self._current_generation: int = 0
        self._current_action_in_generation: int = 0

        # =====================================================================
        # DELIBERATION AUDIT - Record alternative interpretations for analysis
        # Record top 5 alternatives per decision for post-hoc analysis
        # of where the system goes wrong
        # =====================================================================
        self._deliberation_auditor = None  # Lazy-loaded
        self._current_deliberation: Optional[Any] = None  # Active deliberation record

        # =====================================================================
        # COGNITIVE ROUTER INTEGRATION (Phase 4)
        # Transition-driven algorithm switching for intelligent routing
        # =====================================================================
        self._cognitive_router: Optional[Any] = cognitive_router  # Use passed router or lazy-load
        self._cognitive_router_initialized: bool = (cognitive_router is not None)
        if cognitive_router is not None:
            # Ensure _RungResult_Cognitive is set even when router is passed in
            _load_cognitive_router()

        # Load default ordering (rungs are needed even for COGNITIVE strategy)
        # COGNITIVE strategy uses rungs differently - graph-based selection, not static order
        self._suppress_ordering_deprecation = (self.strategy == DecisionStrategy.COGNITIVE)
        self.load_ordering('comprehensive')

    @property
    def engines(self) -> "EngineRegistry":
        """Access modular engines via registry."""
        if self._engine_registry is not None:
            return self._engine_registry

        # Lazy-create registry from legacy core
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

                # Try to get DB from engine registry
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
        """Lazy-load deliberation auditor for recording alternative interpretations."""
        if self._deliberation_auditor is None:
            try:
                from engines.reasoning.deliberation_audit import (
                    get_deliberation_auditor,
                )

                # Try to get DB from engine registry
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
        """Lazy-load cognitive router for transition-driven algorithm switching."""
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

    def set_temporal_context(
        self,
        generation: int,
        action_in_generation: int
    ) -> None:
        """
        Set current temporal context for decay calculations.

        Call this before decide() with the current generation (Big TIME)
        and action count within the generation.

        Args:
            generation: Current generation number (fundamental time unit)
            action_in_generation: Action count within this generation
        """
        self._current_generation = generation
        self._current_action_in_generation = action_in_generation

    def record_outcome(
        self,
        agent_id: str,
        game_type: str,
        outcome_value: float
    ) -> None:
        """
        Record an action outcome for temporal integration.

        Call this after each action with the signed outcome:
        - +1.0: Strong positive (score increase, level complete)
        - +0.5: Weak positive (progress without score)
        - 0.0: Neutral (no change)
        - -0.5: Weak negative (bad position, wasted action)
        - -1.0: Strong negative (death, game over)

        The temporal integrator uses this to modulate rung priorities
        based on recent experience at multiple timescales.
        """
        if self.temporal_integrator is not None:
            self.temporal_integrator.record_outcome(
                agent_id=agent_id,
                game_type=game_type,
                generation=self._current_generation,
                action_in_generation=self._current_action_in_generation,
                outcome_value=outcome_value
            )

        # =====================================================================
        # DELIBERATION AUDIT - Record outcome for current deliberation
        # =====================================================================
        if self.deliberation_auditor is not None and self._current_deliberation is not None:
            try:
                # Map outcome_value to outcome type string
                if outcome_value > 0.0:
                    outcome_type_str = "positive"
                elif outcome_value < 0.0:
                    outcome_type_str = "negative"
                else:
                    outcome_type_str = "neutral"

                # Record outcome
                self.deliberation_auditor.record_outcome(
                    outcome_type=outcome_type_str,
                    score_change=outcome_value,
                )

                # Finalize and save to database
                self.deliberation_auditor.finalize()
                self._current_deliberation = None

            except Exception as e:
                logger.debug(f"[RUNG-SYSTEM] Deliberation outcome recording failed: {e}")

    def _get_category_modulation(self, agent_id: str, game_type: str) -> Dict[str, float]:
        """
        Get rung category priority modulation from temporal integration.

        Returns multipliers for each category based on recent experience.
        When recent outcomes are negative, exploration is suppressed and
        exploitation is boosted (and vice versa).
        """
        if self.temporal_integrator is None:
            return {}  # No modulation if integrator not available

        return self.temporal_integrator.get_rung_modulation(
            agent_id=agent_id,
            game_type=game_type,
            current_generation=self._current_generation,
            current_action=self._current_action_in_generation
        )

    def _get_modulated_priority(self, rung: DecisionRung, modulation: Dict[str, float]) -> float:
        """
        Get a rung's priority adjusted by temporal modulation.

        Maps rung.category to modulation category and applies multiplier.
        Lower values = higher priority (fires earlier in ladder).
        """
        base_priority = rung.get_priority()

        if not modulation:
            return base_priority

        # Map rung category to modulation category
        mod_category = self._category_modulation_map.get(rung.category, 'neutral')

        if mod_category == 'neutral':
            return base_priority

        multiplier = modulation.get(mod_category, 1.0)

        # Invert for priority (higher multiplier = lower priority number = fires earlier)
        # Actually: higher multiplier = MORE likely to fire
        # In weighted mode: multiply confidence by multiplier
        # In ladder mode: divide priority by multiplier (lower = earlier)
        return base_priority / multiplier

    def load_ordering(self, preset_name: str) -> None:
        """Load a preset ordering or custom config.

        .. deprecated:: Phase 6
            Static ORDERING_PRESETS are deprecated. Use DecisionStrategy.COGNITIVE
            with CognitiveRouter for dynamic, graph-based rung selection.

        Note: COGNITIVE strategy still calls this to initialize rungs, but uses
        graph-based selection instead of static ordering. No warning is emitted
        when using COGNITIVE strategy.
        """
        self.ordering_name = preset_name
        self.rungs = []

        # Check if we should suppress deprecation (COGNITIVE strategy)
        suppress = getattr(self, '_suppress_ordering_deprecation', False)

        if preset_name in ORDERING_PRESETS:
            # Phase 6.1: Emit deprecation warning for static orderings
            # (suppressed when using COGNITIVE strategy which uses graph-based selection)
            _warn_ordering_deprecated(preset_name, suppress_if_cognitive=suppress)
            ordering = ORDERING_PRESETS[preset_name]
        else:
            # Try loading from config file
            ordering = self._load_custom_ordering(preset_name)
            if not ordering:
                print(f"[RUNG-SYSTEM] Warning: Unknown ordering '{preset_name}', using efficiency")
                ordering = ORDERING_PRESETS['comprehensive']

        # Instantiate rungs with both legacy core AND engine registry
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

        # Sort by priority
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

    def decide(self, game_state: Any, context: Dict[str, Any]) -> Tuple[str, str]:
        """
        Make an action decision using current strategy.

        Args:
            game_state: Current game state
            context: Additional context (agent info, etc.)

        Returns:
            (action, reason) tuple
        """
        self.total_decisions += 1

        # =================================================================
        # DYNAMIC ORDERING SWITCHING FOR ACTION6 GAMES
        # =================================================================
        # When ACTION6 is the only available action, this is a fundamentally
        # different game paradigm - a "touchscreen world" where understanding
        # objects, causality, and triggers is paramount. Switch to the
        # action6-optimized ordering automatically.
        # =================================================================
        available = context.get('available_actions', [1, 2, 3, 4, 5, 6, 7])
        current_ordering = self.ordering_name

        # Detect if we need to switch ordering for this decision
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
            # Restore original ordering if we switched
            if target_ordering != current_ordering:
                self._switch_ordering_temporarily(current_ordering)

    def _select_ordering_for_context(
        self,
        available_actions: List[int],
        context: Dict[str, Any]
    ) -> str:
        """
        Select the best ordering based on available actions and context.

        This implements the "innate understanding" that different action
        profiles require fundamentally different cognitive approaches.
        """
        # ACTION6-only game (vc33 style) - touchscreen world
        if available_actions == [6]:
            return 'action6_only'

        # ACTION6 is available alongside other actions - hybrid world
        if 6 in available_actions:
            # If current ordering is already action6-aware, keep it
            if self.ordering_name in ('action6_world', 'action6_only', 'frontier_exploration'):
                return self.ordering_name
            # If it's a frontier game, use action6_world
            if context.get('frontier_mode', False):
                return 'action6_world'
            # Otherwise, let it use whatever was set
            return self.ordering_name

        # No ACTION6 - standard directional game
        return self.ordering_name

    def _switch_ordering_temporarily(self, target_ordering: str) -> None:
        """
        Switch to a different ordering without permanent state change.

        This re-sorts rungs by the new ordering's priorities without
        reinstantiating them (which would lose state).
        """
        if target_ordering not in ORDERING_PRESETS:
            return

        ordering = ORDERING_PRESETS[target_ordering]
        priority_map = {name: priority for name, priority in ordering}

        # Update priorities for existing rungs
        for rung in self.rungs:
            if rung.name in priority_map:
                rung.priority_override = priority_map[rung.name]
            else:
                # Rung not in this ordering - give it very low priority
                rung.priority_override = 200

        # Re-sort by new priorities
        self.rungs.sort(key=lambda r: r.get_priority())
        self.ordering_name = target_ordering

    def _decide_ladder(self, game_state: Any, context: Dict[str, Any]) -> Tuple[str, str]:
        """First confident answer wins, with temporal modulation of rung priorities."""
        # Initialize weights for AVAILABLE actions only
        accumulated_weights = get_available_action_weights(context, 1.0)
        self.last_decision_metadata = {}  # Reset metadata
        self._last_winning_rung = None  # Reset for feedback loop

        # Get temporal modulation for rung priority adjustment
        agent_id = context.get('agent_id', 'unknown')
        game_type = context.get('game_type', 'unknown')
        modulation = self._get_category_modulation(agent_id, game_type)

        # Inject exploration appetite into context for rungs that want it
        if self.temporal_integrator is not None:
            context['exploration_appetite'] = self.temporal_integrator.get_exploration_appetite(
                agent_id=agent_id,
                game_type=game_type,
                current_generation=self._current_generation,
                current_action=self._current_action_in_generation
            )

        # Sort rungs by modulated priority (lower = fires earlier)
        sorted_rungs = sorted(
            self.rungs,
            key=lambda r: self._get_modulated_priority(r, modulation)
        )

        for rung in sorted_rungs:
            if not rung.enabled:
                continue

            result = rung.evaluate(game_state, context)

            # Accumulate weights from filter rungs (only for available actions)
            if result.weights:
                for action, weight in result.weights.items():
                    if is_action_available(action, context):
                        accumulated_weights[action] = accumulated_weights.get(action, 1.0) * weight

            # Check if this rung has a confident suggestion
            if result.has_suggestion(rung.confidence_threshold):
                # CRITICAL: Validate action is available (defense-in-depth)
                if result.action and not is_action_available(result.action, context):
                    # Skip this rung's suggestion - it returned an unavailable action
                    continue

                # CRITICAL: Ensure ACTION6 has coordinates (safety net)
                if result.action == 'ACTION6':
                    result = Action6CoordinateProvider.enrich_result_with_coordinates(
                        result, context, self._engine_registry, game_state
                    )

                self.rung_wins[rung.name] = self.rung_wins.get(rung.name, 0) + 1
                self._last_winning_rung = rung  # Track for feedback
                rung.record_outcome(was_accepted=True)
                # Capture metadata for checkpoint handoff
                self.last_decision_metadata = result.metadata or {}
                return result.action or get_random_available_action(context), f"[{rung.name}] {result.reason}"

        # No confident answer - use accumulated weights for fallback
        action, reason = self._weighted_random_choice(accumulated_weights, context), "Weighted fallback after ladder"

        # CRITICAL: If fallback chose ACTION6, ensure coordinates
        if action == 'ACTION6':
            coords = Action6CoordinateProvider.get_coordinates(context, self._engine_registry, game_state)
            self.last_decision_metadata = coords
            reason += f" [coords: ({coords['x']},{coords['y']})]"

        return action, reason

    def _decide_weighted(self, game_state: Any, context: Dict[str, Any]) -> Tuple[str, str]:
        """All rungs vote, weighted sum decides, with temporal modulation."""
        # Initialize votes for AVAILABLE actions only
        action_votes = get_available_action_weights(context, 0.0)
        reasons: List[str] = []
        self.last_decision_metadata = {}  # Reset metadata
        self._last_winning_rung = None  # Reset for feedback loop

        # Get temporal modulation for vote weight adjustment
        agent_id = context.get('agent_id', 'unknown')
        game_type = context.get('game_type', 'unknown')
        modulation = self._get_category_modulation(agent_id, game_type)

        # =====================================================================
        # DELIBERATION AUDIT - Start recording alternatives
        # =====================================================================
        if self.deliberation_auditor is not None:
            game_id = context.get('game_id', context.get('scorecard_id', 'unknown'))
            level_number = context.get('level_number', context.get('level', 0))
            action_number = context.get('action_count', 0)
            self.deliberation_auditor.start_deliberation(
                game_id=game_id,
                game_type=game_type[:4] if len(game_type) >= 4 else game_type,
                level_number=level_number,
                action_number=action_number,
                agent_id=agent_id,
                context=context,
            )

        # Inject exploration appetite into context for rungs that want it
        if self.temporal_integrator is not None:
            context['exploration_appetite'] = self.temporal_integrator.get_exploration_appetite(
                agent_id=agent_id,
                game_type=game_type,
                current_generation=self._current_generation,
                current_action=self._current_action_in_generation
            )

        # Track which rung contributed most to final decision
        rung_contributions: Dict[str, Tuple[DecisionRung, float, str]] = {}  # action -> (rung, weight, name)

        # Track all alternatives for deliberation audit (action -> (confidence, reason, rung))
        all_alternatives: Dict[str, Tuple[float, str, str]] = {}

        for rung in self.rungs:
            if not rung.enabled:
                continue

            result = rung.evaluate(game_state, context)

            if result.action:
                # CRITICAL: Skip unavailable actions (defense-in-depth)
                if not is_action_available(result.action, context):
                    continue  # Don't count votes for unavailable actions

                # Weight by confidence and rung priority (lower priority = higher weight)
                base_weight = result.confidence * (100 - rung.get_priority()) / 100

                # Apply temporal modulation to weight
                mod_category = self._category_modulation_map.get(rung.category, 'neutral')
                mod_multiplier = modulation.get(mod_category, 1.0) if modulation else 1.0
                weight = base_weight * mod_multiplier

                action_votes[result.action] = action_votes.get(result.action, 0) + weight
                reasons.append(f"{rung.name}:{result.action}({weight:.2f})")

                # Track strongest contributor per action
                if result.action not in rung_contributions or weight > rung_contributions[result.action][1]:
                    rung_contributions[result.action] = (rung, weight, rung.name)

                # Track for deliberation audit (best confidence per action)
                if result.action not in all_alternatives or result.confidence > all_alternatives[result.action][0]:
                    all_alternatives[result.action] = (result.confidence, result.reason, rung.name)

            # Add explicit weights (only for available actions)
            if result.weights:
                for action, w in result.weights.items():
                    if is_action_available(action, context):
                        action_votes[action] = action_votes.get(action, 0) + w * 0.1

        # Pick highest voted action
        best_action = max(action_votes, key=lambda k: action_votes[k])

        # =====================================================================
        # DELIBERATION AUDIT - Record alternatives and choice
        # =====================================================================
        if self.deliberation_auditor is not None:
            # Record all alternatives (sorted by vote weight)
            sorted_actions = sorted(action_votes.items(), key=lambda x: x[1], reverse=True)
            for action, vote_weight in sorted_actions[:5]:  # Top 5 alternatives
                if action in all_alternatives:
                    conf, reason, rung_name = all_alternatives[action]
                    why_rejected = None if action == best_action else f"lower_vote:{vote_weight:.2f}"
                    self.deliberation_auditor.add_alternative(
                        action=action,
                        confidence=conf,
                        reason=reason,
                        rung=rung_name,
                        why_rejected=why_rejected,
                    )

            # Record the final choice
            if best_action in all_alternatives:
                conf, reason, rung_name = all_alternatives[best_action]
            else:
                conf, reason, rung_name = action_votes.get(best_action, 0.0), "weighted_vote", "aggregate"
            self.deliberation_auditor.record_choice(
                chosen_action=best_action,
                confidence=conf,
                reason=reason,
                rung=rung_name,
            )

            # Add sparse grid context if available
            sparse_cell_count = context.get('sparse_cell_count', 0)
            sparse_colors = context.get('sparse_colors', set())
            sparse_hash = context.get('sparse_hash', '')
            if sparse_cell_count > 0:
                self.deliberation_auditor.set_sparse_context(
                    cell_count=sparse_cell_count,
                    colors=list(sparse_colors) if isinstance(sparse_colors, set) else sparse_colors,
                    sparse_hash=sparse_hash,
                )

            # Store current deliberation for outcome recording
            self._current_deliberation = self.deliberation_auditor._current_record

        # Track the strongest contributor to winning action
        if best_action in rung_contributions:
            self._last_winning_rung = rung_contributions[best_action][0]
            self._last_winning_rung.record_outcome(was_accepted=True)

        reason = f"Weighted vote: {best_action} ({action_votes[best_action]:.2f}) from [{', '.join(reasons[:3])}]"

        # CRITICAL: If ACTION6, ensure coordinates in metadata
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

        # Temporarily switch ordering
        old_rungs = self.rungs
        self.load_ordering(phase_ordering)
        action, reason = self._decide_ladder(game_state, context)
        self.rungs = old_rungs

        return action, f"[{phase_ordering}] {reason}"

    def _decide_parallel(self, game_state: Any, context: Dict[str, Any]) -> Tuple[str, str]:
        """Run all rungs in parallel, pick highest confidence"""""
        best_result: Optional[RungResult] = None
        best_rung: Optional[DecisionRung] = None
        self._last_winning_rung = None  # Reset for feedback loop

        for rung in self.rungs:
            if not rung.enabled:
                continue

            result = rung.evaluate(game_state, context)

            # CRITICAL: Only consider results with available actions (defense-in-depth)
            if result.action and is_action_available(result.action, context):
                if best_result is None or result.confidence > best_result.confidence:
                    best_result = result
                    best_rung = rung

        if best_result and best_rung:
            self.rung_wins[best_rung.name] = self.rung_wins.get(best_rung.name, 0) + 1
            self._last_winning_rung = best_rung  # Track for feedback
            best_rung.record_outcome(was_accepted=True)
            return best_result.action or get_random_available_action(context), f"[{best_rung.name}] {best_result.reason}"

        return get_random_available_action(context), "No suggestions from any rung"

    def _weighted_random_choice(self, weights: Dict[str, float], context: Optional[Dict[str, Any]] = None) -> str:
        """Make a weighted random choice from weights dict (already filtered to available)"""
        if not weights:
            # Ultimate fallback - use context-aware random if available
            if context:
                return get_random_available_action(context)
            return 'ACTION1'  # Absolute last resort
        total = sum(max(0.05, w) for w in weights.values())  # Minimum 0.05
        r = random.random() * total
        cumulative = 0
        for action, weight in weights.items():
            cumulative += max(0.05, weight)
            if r <= cumulative:
                return action
        # Return first available action from weights as fallback
        return next(iter(weights.keys()))

    # =========================================================================
    # OUTCOME FEEDBACK - Report results back to winning rung
    # =========================================================================

    def report_outcome(
        self,
        action: str,
        success: bool,
        is_death: bool = False,
        score_delta: float = 0.0,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Report the actual outcome of the last decision back to the winning rung.

        This closes the feedback loop - rungs can learn whether their suggestions
        actually worked. Called by GameLoop after action execution.

        Args:
            action: The action that was executed (for verification)
            success: Whether the action achieved positive result (score/progress)
            is_death: Whether the action caused death/failure
            score_delta: How much the score changed
            context: Optional additional context (position, level, etc.)

        Wires to:
            - RuleTransferRung.record_outcome() -> update_rule_success()
            - AssumptionFormationRung (future: challenge_assumption)
            - HypothesisTestingRung (future: mark_assumption_tested)
            - TemporalIntegrator.record_outcome() -> multi-scale experience integration
        """
        if self._last_winning_rung is None:
            return

        # Store outcome context for rungs that need extra details
        self._last_outcome_context = {
            'action': action,
            'success': success,
            'is_death': is_death,
            'score_delta': score_delta,
            'context': context or {}
        }

        try:
            # Call the rung's record_outcome with actual success
            self._last_winning_rung.record_outcome(
                was_accepted=True,
                success=success
            )
        except TypeError:
            # Rung doesn't support success parameter - use base signature
            pass
        except Exception:
            # Don't break gameplay on feedback errors
            pass

        # Feed temporal integrator for multi-scale experience tracking
        # Convert outcome to signed value: death=-1.0, success=+score_delta or +0.5, fail=-0.3
        if is_death:
            outcome_value = -1.0
        elif success:
            # Use score_delta if meaningful, otherwise weak positive
            outcome_value = min(1.0, max(0.1, score_delta)) if score_delta > 0 else 0.5
        else:
            outcome_value = -0.3  # Weak negative for non-success non-death

        ctx = context or {}
        self.record_outcome(
            agent_id=ctx.get('agent_id', 'unknown'),
            game_type=ctx.get('game_type', 'unknown'),
            outcome_value=outcome_value
        )

    def notify_action_complete(
        self,
        action: str,
        action_data: Dict[str, Any],
        frame_before: Any,
        frame_after: Any,
        context: Dict[str, Any]
    ) -> None:
        """Notify rungs that have on_action_complete hooks.

        Enables rungs like SpatialRelationshipRung to learn from action effects.
        Called by GameLoop after action execution and outcome processing.

        Args:
            action: The action name that was executed
            action_data: Action parameters (x, y for clicks)
            frame_before: Frame before the action
            frame_after: Frame after the action
            context: Decision context
        """
        for rung in self.rungs:
            if hasattr(rung, 'on_action_complete'):
                try:
                    rung.on_action_complete(
                        action=action,
                        action_data=action_data,
                        frame_before=frame_before,
                        frame_after=frame_after,
                        context=context
                    )
                except Exception:
                    # Don't break on hook errors
                    pass

    # =========================================================================
    # EMERGENCY RUNGS - Always checked first regardless of strategy
    # =========================================================================
    EMERGENCY_RUNG_NAMES = frozenset({
        'infinite_loop_breaker',
        'coordinate_oscillation',
    })

    def _decide_context_adaptive(self, game_state: Any, context: Dict[str, Any]) -> Tuple[str, str]:
        """
        Context-dependent strategy selection.

        This addresses the "early exit problem" identified in architecture review:
        - LADDER strategy discards accumulated weights when a suggestion fires
        - On frontier levels, we want ALL rungs to vote (WEIGHTED)
        - On replay/optimization, we want deterministic sequence following (LADDER)
        - Emergency rungs (loop_breaker, oscillation) ALWAYS get LADDER priority

        Strategy selection:
        - replay_mode (following winning sequence): LADDER - deterministic replay
        - frontier_mode (unbeaten level): WEIGHTED - all rungs vote
        - optimization_mode (refining beaten game): WEIGHTED - find improvements
        - default: LADDER for backwards compatibility
        """
        # Phase 1: ALWAYS check emergency rungs first (LADDER-style)
        emergency_result = self._check_emergency_rungs(game_state, context)
        if emergency_result is not None:
            return emergency_result

        # Phase 2: Determine effective strategy from context
        effective_strategy = self._select_effective_strategy(context)

        # Phase 3: Execute with effective strategy
        if effective_strategy == 'weighted':
            return self._decide_weighted_non_emergency(game_state, context)
        else:
            return self._decide_ladder_non_emergency(game_state, context)

    def _check_emergency_rungs(self, game_state: Any, context: Dict[str, Any]) -> Optional[Tuple[str, str]]:
        """
        Check emergency rungs with LADDER semantics (first confident answer wins).
        Returns None if no emergency action needed.
        """
        for rung in self.rungs:
            if not rung.enabled:
                continue
            if rung.name not in self.EMERGENCY_RUNG_NAMES:
                continue

            result = rung.evaluate(game_state, context)

            if result.has_suggestion(rung.confidence_threshold):
                # CRITICAL: Validate action is available (defense-in-depth)
                if result.action and not is_action_available(result.action, context):
                    continue  # Skip - emergency rung returned unavailable action

                # CRITICAL: Ensure ACTION6 has coordinates
                if result.action == 'ACTION6':
                    result = Action6CoordinateProvider.enrich_result_with_coordinates(
                        result, context, self._engine_registry, game_state
                    )
                    self.last_decision_metadata = result.metadata or {}

                self.rung_wins[rung.name] = self.rung_wins.get(rung.name, 0) + 1
                rung.record_outcome(was_accepted=True)
                return result.action or get_random_available_action(context), f"[EMERGENCY:{rung.name}] {result.reason}"

        return None

    def _select_effective_strategy(self, context: Dict[str, Any]) -> str:
        """
        Select effective strategy based on context.

        Returns:
            'weighted' or 'ladder'
        """
        # Explicit replay mode: use LADDER for deterministic sequence following
        replay_mode = context.get('replay_mode', False)
        active_sequence = context.get('active_sequence')
        sequence_position = context.get('sequence_position', 0)

        # Check if we're actively replaying (have sequence AND haven't exhausted it)
        # This handles the frontier checkpoint edge case: once we exhaust the checkpoint
        # prefix, we switch to WEIGHTED for the exploration-beyond-checkpoint phase
        if replay_mode:
            return 'ladder'
        if active_sequence and sequence_position < len(active_sequence):
            return 'ladder'

        # Frontier mode (unbeaten level): use WEIGHTED so all rungs contribute
        frontier_mode = context.get('frontier_mode', False)
        if frontier_mode:
            return 'weighted'

        # Optimization mode (refining beaten game): use WEIGHTED to find improvements
        optimization_mode = context.get('optimization_mode', False)
        if optimization_mode:
            return 'weighted'

        # Check game state - if no winning sequence exists, treat as frontier
        game_state_mode = context.get('game_state_mode', 'unknown')
        if game_state_mode == 'exploration':
            return 'weighted'

        # Beaten level but not in explicit replay or optimization mode:
        # Use WEIGHTED to allow for improvement discovery
        # (This addresses Edge Case 2: agent learning a beaten level fresh)
        has_winning_sequence = context.get('has_winning_sequence', False)
        if has_winning_sequence and not active_sequence:
            return 'weighted'

        # Default: LADDER for backwards compatibility
        return 'ladder'

    def _decide_weighted_non_emergency(self, game_state: Any, context: Dict[str, Any]) -> Tuple[str, str]:
        """
        WEIGHTED strategy excluding emergency rungs (already checked).
        All non-emergency rungs vote, weighted sum decides.
        """
        # Initialize for AVAILABLE actions only
        action_votes = get_available_action_weights(context, 0.0)
        accumulated_weights = get_available_action_weights(context, 1.0)
        reasons: List[str] = []

        for rung in self.rungs:
            if not rung.enabled:
                continue
            # Skip emergency rungs - already checked
            if rung.name in self.EMERGENCY_RUNG_NAMES:
                continue

            result = rung.evaluate(game_state, context)

            # Accumulate filter weights (multiplicative) - only for available actions
            if result.weights:
                for action, weight in result.weights.items():
                    if is_action_available(action, context):
                        accumulated_weights[action] = accumulated_weights.get(action, 1.0) * weight

            # Add suggestion votes (additive, weighted by confidence and priority)
            if result.action:
                # CRITICAL: Skip unavailable actions (defense-in-depth)
                if not is_action_available(result.action, context):
                    continue
                # Weight by confidence and rung priority (lower priority = higher weight)
                weight = result.confidence * (100 - rung.get_priority()) / 100
                action_votes[result.action] = action_votes.get(result.action, 0) + weight
                reasons.append(f"{rung.name}:{result.action}({weight:.2f})")

        # Combine: multiply votes by accumulated filter weights
        final_scores: Dict[str, float] = {}
        for action in action_votes:
            # Base vote + small boost from filter weights
            vote = action_votes[action]
            filter_weight = accumulated_weights.get(action, 1.0)
            # Filter weights modify the final score
            # If filter_weight < 1.0, action is penalized (e.g., death avoidance)
            # If filter_weight > 1.0, action is boosted
            final_scores[action] = (vote + 0.1) * filter_weight  # +0.1 ensures all actions have some chance

        # Pick highest scored action
        best_action = max(final_scores, key=lambda k: final_scores[k])
        best_score = final_scores[best_action]

        # If best score is very low, fall back to weighted random
        if best_score < 0.15:
            action, reason = self._weighted_random_choice(accumulated_weights, context), "Weighted random (low confidence)"
            # CRITICAL: If ACTION6, ensure coordinates
            if action == 'ACTION6':
                coords = Action6CoordinateProvider.get_coordinates(context, self._engine_registry, game_state)
                self.last_decision_metadata = coords
                reason += f" [coords: ({coords['x']},{coords['y']})]"
            return action, reason

        top_contributors = ', '.join(reasons[:3]) if reasons else 'filters only'
        reason = f"[WEIGHTED] {best_action} ({best_score:.2f}) from [{top_contributors}]"

        # CRITICAL: If ACTION6, ensure coordinates
        if best_action == 'ACTION6':
            coords = Action6CoordinateProvider.get_coordinates(context, self._engine_registry, game_state)
            self.last_decision_metadata = {**self.last_decision_metadata, **coords}
            reason += f" [coords: ({coords['x']},{coords['y']})]"

        return best_action, reason

    def _decide_ladder_non_emergency(self, game_state: Any, context: Dict[str, Any]) -> Tuple[str, str]:
        """
        LADDER strategy excluding emergency rungs (already checked).
        First confident non-emergency answer wins.
        """
        # Initialize for AVAILABLE actions only
        accumulated_weights = get_available_action_weights(context, 1.0)

        for rung in self.rungs:
            if not rung.enabled:
                continue
            # Skip emergency rungs - already checked
            if rung.name in self.EMERGENCY_RUNG_NAMES:
                continue

            result = rung.evaluate(game_state, context)

            # Accumulate weights from filter rungs (only for available actions)
            if result.weights:
                for action, weight in result.weights.items():
                    if is_action_available(action, context):
                        accumulated_weights[action] = accumulated_weights.get(action, 1.0) * weight

            # Check if this rung has a confident suggestion
            if result.has_suggestion(rung.confidence_threshold):
                # CRITICAL: Validate action is available (defense-in-depth)
                if result.action and not is_action_available(result.action, context):
                    continue  # Skip - returned unavailable action

                # CRITICAL: Ensure ACTION6 has coordinates (safety net)
                if result.action == 'ACTION6':
                    result = Action6CoordinateProvider.enrich_result_with_coordinates(
                        result, context, self._engine_registry, game_state
                    )

                self.rung_wins[rung.name] = self.rung_wins.get(rung.name, 0) + 1
                rung.record_outcome(was_accepted=True)
                # Capture metadata for checkpoint handoff
                self.last_decision_metadata = result.metadata or {}
                return result.action or get_random_available_action(context), f"[{rung.name}] {result.reason}"

        # No confident answer - use accumulated weights for fallback
        action, reason = self._weighted_random_choice(accumulated_weights, context), "Weighted fallback after ladder"

        # CRITICAL: If fallback chose ACTION6, ensure coordinates
        if action == 'ACTION6':
            coords = Action6CoordinateProvider.get_coordinates(context, self._engine_registry, game_state)
            self.last_decision_metadata = coords
            reason += f" [coords: ({coords['x']},{coords['y']})]"

        return action, reason

    def _decide_cognitive(self, game_state: Any, context: Dict[str, Any]) -> Tuple[str, str]:
        """
        Cognitive routing strategy - full pipeline as described in architecture.

        The cognitive router IS the decision system. It:
        1. Compresses state via phenomenology (FeltState)
        2. Assesses knowledge via epistemic tracker (Rumsfeld quadrant)
        3. Selects search strategy via meta-planner
        4. Prioritizes by urgency x importance (Eisenhower)
        5. Executes the winning rung and records trajectory

        This method is a thin integration layer that:
        - Checks emergency rungs first (safety invariant)
        - Provides a rung_executor that properly bridges legacy rungs
          to the cognitive RungResult protocol (with epistemic data)
        - Extracts the actual ACTION string from DecisionResult.action_value
          without re-executing rungs (the executor already ran them)
        - Handles ACTION6 coordinates as a final safety net

        Falls back to context_adaptive strategy if CognitiveRouter is unavailable.
        """
        # Check if cognitive router is available
        router = self.cognitive_router
        if router is None:
            logger.warning("[RUNG-SYSTEM] CognitiveRouter unavailable, falling back to context_adaptive")
            return self._decide_context_adaptive(game_state, context)

        # =====================================================================
        # EMERGENCY RUNGS - Always checked first (safety invariant)
        # These are checked BEFORE the cognitive router because they represent
        # hard safety constraints (infinite loop breaking, oscillation detection)
        # that should override any cognitive strategy.
        # =====================================================================
        emergency_result = self._check_emergency_rungs(game_state, context)
        if emergency_result is not None:
            return emergency_result

        # Initialize router if needed (once per game)
        game_id = context.get('game_id', context.get('scorecard_id', 'unknown'))
        if not hasattr(self, '_cognitive_game_id') or self._cognitive_game_id != game_id:
            # Build node structure from rungs (excluding emergency rungs -
            # they're handled above, not part of the cognitive search space)
            nodes = {
                rung.name: {
                    'name': rung.name,
                    'category': rung.category,
                    'priority': rung.get_priority(),
                }
                for rung in self.rungs
                if rung.name not in self.EMERGENCY_RUNG_NAMES
            }

            # Use EdgeInferenceEngine to populate edges from slot dataflow
            edges: Dict[str, List[str]] = {}
            try:
                from engines.cognition.edge_inference import EdgeInferenceEngine
                edge_engine = EdgeInferenceEngine()
                rung_classes = [type(r) for r in self.rungs if r.name not in self.EMERGENCY_RUNG_NAMES]
                edge_engine.analyze_rungs(rung_classes)
                inferred = edge_engine.infer_all_edges()
                # Convert InferredEdge list to adjacency dict
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
            # Reset per-game contradiction tracking
            self._cognitive_previously_successful_rungs = set()

        # =====================================================================
        # RUNG EXECUTOR - Bridges legacy rungs to cognitive RungResult protocol
        #
        # This closure evaluates a legacy rung and converts its output to the
        # cognitive RungResult format. Key design decisions:
        #
        # 1. The actual ACTION string goes into RungResult.value so the
        #    cognitive router can carry it through to DecisionResult.action_value
        #    without needing to re-execute the rung.
        #
        # 2. Epistemic data is extracted from the legacy result where possible:
        #    - contradiction_detected from metadata
        #    - surprise_level from confidence inversion (low confidence = surprise)
        #    - The cognitive router's epistemic tracker uses these signals to
        #      drive quadrant transitions (KK->KU on contradiction, etc.)
        #
        # 3. Rung metadata (coordinates, provenance) is cached in
        #    _cognitive_last_rung_metadata so _decide_cognitive can attach it
        #    to the final output without re-evaluation.
        # =====================================================================
        self._cognitive_last_rung_metadata: Dict[str, Any] = {}
        self._cognitive_last_winning_rung: Optional[DecisionRung] = None

        # Track rungs that produced actions in previous decisions (per-game).
        # Used to detect contradictions: a rung that previously worked but
        # now fails is a genuine surprise/contradiction signal that can
        # drive KK->KU/KK->UU regressions in the epistemic state machine.
        if not hasattr(self, '_cognitive_previously_successful_rungs'):
            self._cognitive_previously_successful_rungs: set = set()

        def rung_executor(rung_name: str, _game_state_dict: Dict) -> Any:
            """Execute a legacy rung and bridge to cognitive RungResult."""
            rung = next((r for r in self.rungs if r.name == rung_name), None)
            if rung is None or not rung.enabled:
                if _RungResult_Cognitive:
                    return _RungResult_Cognitive(rung_name=rung_name, confidence=0.0)
                return None

            # Execute the rung ONCE - this is the only evaluation
            try:
                result = rung.evaluate(game_state, context)
            except Exception as eval_err:
                logger.debug(f"[RUNG-EXECUTOR] {rung_name} evaluate() failed: {eval_err}")
                if _RungResult_Cognitive:
                    return _RungResult_Cognitive(rung_name=rung_name, confidence=0.0)
                return None

            # Cache the winning rung and metadata for post-processing
            if result.action and result.confidence > 0:
                self._cognitive_last_winning_rung = rung
                self._cognitive_last_rung_metadata = result.metadata or {}
                # Track this rung as previously successful for contradiction detection
                self._cognitive_previously_successful_rungs.add(rung_name)

            # Extract epistemic signals from legacy result
            metadata = result.metadata or {}
            contradiction_detected = metadata.get('contradiction_detected', False)
            # Legacy rungs can't express genuine surprise. Low confidence
            # is NOT surprise — it's just uncertainty. Set to 0.0 to prevent
            # UU from being boosted by weak suggestions.
            # Real surprise would require comparing result to expectation.
            surprise_level = 0.0

            # =========================================================
            # CONTRADICTION DETECTION (bridge for KK->KU/KK->UU regressions)
            #
            # A rung that previously produced an action but now fails is a
            # genuine contradiction — the world changed or our model was wrong.
            # This is the primary mechanism for KK->KU (mild) and KK->UU
            # (severe) regressions. Without this, KK is a terminal state.
            # =========================================================
            if (not result.action
                    and rung_name in self._cognitive_previously_successful_rungs):
                # Previously-successful rung now fails = contradiction
                contradiction_detected = True
                # Genuine surprise: we expected success, got failure
                surprise_level = 0.8

            # =========================================================
            # EPISTEMIC SIGNAL SYNTHESIS (bridge legacy rungs to state machine)
            #
            # Legacy rungs don't produce slot_name, questions, or answers.
            # Without these signals, the epistemic tracker is blind:
            # - No slot_name -> KK never accumulates
            # - No raises_questions -> KU never triggers
            # - No answers_questions -> KU->KK never happens
            #
            # Fix: Synthesize these signals from what we DO have.
            # =========================================================

            # (B) slot_name: Use rung_name as proxy when legacy doesn't provide one.
            # A rung producing an action IS knowledge about "what to do".
            slot_name = metadata.get('slot_name')
            if not slot_name and result.action:
                slot_name = rung_name  # The rung's identity IS the knowledge slot

            # (C) Question generation: When a rung returns no action, that's a
            # discovery - we know we DON'T know what to do. Classic Known Unknown.
            questions_raised = []
            answers = []
            if not result.action and not self._cognitive_last_winning_rung:
                # No rung has produced an action yet - raise a question
                try:
                    from engines.cognition.blackboard import Question
                    questions_raised.append(Question(
                        question_id=f"what_works_for_{game_id}",
                        description=f"What action works in current game state?",
                        answerable_by=[r.name for r in self.rungs
                                       if r.name not in self.EMERGENCY_RUNG_NAMES],
                        priority=0.6,
                    ))
                except ImportError:
                    pass  # Graceful degradation

            # (D) Question injection for KK regression: When a previously-
            # successful rung contradicts, raise a high-priority question.
            # This enables KK->KU transition (mild contradiction path).
            if contradiction_detected and rung_name in self._cognitive_previously_successful_rungs:
                try:
                    from engines.cognition.blackboard import Question
                    questions_raised.append(Question(
                        question_id=f"why_failed_{rung_name}_{game_id}",
                        description=f"Why did {rung_name} stop working?",
                        answerable_by=[r.name for r in self.rungs
                                       if r.name != rung_name
                                       and r.name not in self.EMERGENCY_RUNG_NAMES],
                        priority=0.8,  # High priority - regression is urgent
                    ))
                except ImportError:
                    pass  # Graceful degradation

            # (C) Answer generation: When a rung produces a confident action,
            # it answers the "what works" question.
            if result.action and result.confidence > 0.3:
                answers.append(f"what_works_for_{game_id}")

            if _RungResult_Cognitive:
                return _RungResult_Cognitive(
                    rung_name=rung_name,
                    slot_name=slot_name,
                    value=result.action,  # Actual ACTION string (e.g., 'ACTION3')
                    confidence=result.confidence,
                    raises_questions=questions_raised,
                    answers_questions=answers,
                    surprise_level=surprise_level,
                    contradiction_detected=contradiction_detected,
                    contradiction_with=metadata.get('contradiction_with'),
                )
            return result

        # =====================================================================
        # RUN THE COGNITIVE ROUTER
        # The router handles the full pipeline:
        #   Phenomenology -> Epistemic -> Meta-Planner -> Eisenhower -> Execute
        # =====================================================================
        try:
            decision_result = router.decide(
                game_state={'frame': getattr(game_state, 'frame', None), **context},
                rung_executor=rung_executor
            )

            # Extract the actual ACTION string - no re-execution needed
            # The rung_executor already evaluated the rung and stored the
            # action in RungResult.value, which flows through to
            # DecisionResult.action_value
            action = decision_result.action_value  # e.g., 'ACTION3'
            rung_name = decision_result.action      # e.g., 'survey'
            confidence = decision_result.confidence
            reasoning = f"[COGNITIVE:{rung_name}] {decision_result.reasoning}"

            # Track the winning rung for feedback
            if self._cognitive_last_winning_rung is not None:
                self._last_winning_rung = self._cognitive_last_winning_rung
                self.rung_wins[rung_name] = self.rung_wins.get(rung_name, 0) + 1
                self._cognitive_last_winning_rung.record_outcome(was_accepted=True)

            # Safety net: validate action is a real ACTION and is available
            if not action or not is_action_available(action, context):
                # The router found a rung but it didn't produce a usable action
                # (e.g., filter rung, or action not available in this game)
                accumulated_weights = get_available_action_weights(context, 1.0)
                action = self._weighted_random_choice(accumulated_weights, context)
                reasoning = f"[COGNITIVE:{rung_name}] Fallback: no usable action from router"

            # Final format check (defense-in-depth)
            if action not in {f'ACTION{i}' for i in range(1, 8)}:
                action = get_random_available_action(context)
                reasoning = f"[COGNITIVE] Random fallback: invalid action format"

            # CRITICAL: If ACTION6, ensure coordinates
            if action == 'ACTION6':
                # Use cached metadata from the rung executor if it has coords
                coords = self._cognitive_last_rung_metadata
                if 'x' not in coords or 'y' not in coords:
                    coords = Action6CoordinateProvider.get_coordinates(
                        context, self._engine_registry, game_state
                    )
                self.last_decision_metadata = coords
                reasoning += f" [coords: ({coords.get('x', 32)},{coords.get('y', 32)})]"

            # RECORD DECISION TRACE (full architecture compliance)
            if self._routing_trace_store is not None:
                try:
                    trace_id = self._routing_trace_store.record_trace(
                        game_id=game_id,
                        agent_id=context.get('agent_id', 'unknown'),
                        path=decision_result.path,
                        algorithm_used=getattr(decision_result, 'algorithm_name', decision_result.final_quadrant),
                        final_action=action,
                        final_confidence=confidence,
                        initial_quadrant=getattr(decision_result, 'initial_quadrant', decision_result.final_quadrant),
                        final_quadrant=decision_result.final_quadrant,
                        quadrant_transitions=getattr(decision_result, 'quadrant_transitions', []),
                        algorithms_history=getattr(decision_result, 'algorithms_history', []),
                        backtrack_count=getattr(decision_result, 'backtrack_count', 0),
                        iterations=decision_result.iterations,
                        decision_latency_ms=decision_result.time_elapsed * 1000
                    )
                    self.last_decision_metadata['trace_id'] = trace_id
                    logger.debug(f"[COGNITIVE] Recorded trace {trace_id}")
                except Exception as trace_err:
                    logger.warning(f"[COGNITIVE] Failed to record trace: {trace_err}")

            # Log statistics periodically
            if self.total_decisions % 100 == 0:
                stats = router.get_statistics()
                logger.info(
                    f"[COGNITIVE] Stats: {stats['total_decisions']} decisions, "
                    f"{stats['total_fallbacks']} fallbacks ({stats['fallback_rate']:.1%})"
                )

            return action, reasoning

        except Exception as e:
            logger.error(f"[COGNITIVE] Router error: {e}, falling back to context_adaptive")
            return self._decide_context_adaptive(game_state, context)

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

    def experiment_orderings(self, game_state: Any, context: Dict[str, Any], orderings: List[str]) -> Dict[str, Tuple[str, str]]:
        """
        Test multiple orderings on same state (for analysis).

        Returns:
            Dict mapping ordering name to (action, reason)
        """
        results: Dict[str, Tuple[str, str]] = {}
        original = self.ordering_name

        for ordering in orderings:
            self.load_ordering(ordering)
            action, reason = self._decide_ladder(game_state, context)
            results[ordering] = (action, reason)

        self.load_ordering(original)
        return results


# =============================================================================
# INTEGRATION ADAPTER - Bridge between rung system and core_gameplay.py
# =============================================================================

class CoreGameplayAdapter:
    """
    Adapter to integrate DecisionRungSystem with existing CoreGameplay._select_action().

    This enables a phased migration:

    PHASE 1 - SHADOW MODE (Current):
    --------------------------------
    Run BOTH systems, log divergences, learn which is better.

        adapter = CoreGameplayAdapter(core_gameplay_instance)
        adapter.enable_shadow_mode()

        # In _select_action():
        old_action, old_reason = self._original_select_action(game_state)
        adapter.shadow_compare(game_state, context, old_action)

    PHASE 2 - CATEGORY TAKEOVER:
    ----------------------------
    Let rung system handle specific categories (e.g., emergency, filter).

        # In _select_action():
        emergency_result = adapter.decide_category('emergency', game_state, context)
        if emergency_result.has_suggestion(0.7):
            return emergency_result.action, emergency_result.reason
        # ... continue with old logic for other categories

    PHASE 3 - FULL REPLACEMENT:
    ---------------------------
    Replace _select_action() entirely.

        async def _select_action(self, game_state, loop_state=None):
            context = self._build_decision_context(game_state, loop_state)
            return self.decision_system.decide(game_state, context)

    Migration Benefits:
    - Zero-downtime transition (shadow mode validates before switch)
    - Category-by-category migration (reduces risk)
    - Easy rollback (just disable categories)
    - Performance metrics for A/B comparison
    """

    def __init__(self, core_gameplay_ref: Any, ordering: str = 'comprehensive'):
        self.core: Any = core_gameplay_ref
        self.rung_system = DecisionRungSystem(
            strategy='ladder',
            core_gameplay_ref=core_gameplay_ref
        )
        self.rung_system.load_ordering(ordering)

        # Shadow mode state
        self.shadow_mode = False
        self.shadow_log: List[Dict[str, Any]] = []
        self.divergence_count = 0
        self.agreement_count = 0

        # Phase 11: Advanced shadow tester (lazy-loaded)
        self._shadow_tester: Any = None

        # Category takeover state
        self.category_enabled: Dict[str, bool] = {
            'emergency': False,
            'filter': False,
            'orientation': False,
            'hypothesis': False,
            'exploitation': False,
            'fallback': False,
        }

    def enable_shadow_mode(self, log_limit: int = 1000):
        """Enable shadow mode - run both systems and compare."""
        self.shadow_mode = True
        self.shadow_log = []
        self._shadow_log_limit = log_limit
        logger.info("[RUNG-ADAPTER] Shadow mode ENABLED - comparing decisions")

    def get_shadow_tester(self) -> Any:
        """Lazy-load the advanced ShadowTester from shadow_testing.py."""
        if self._shadow_tester is None:
            try:
                from engines.cognition.shadow_testing import ShadowTester
                self._shadow_tester = ShadowTester()
                logger.info("[RUNG-ADAPTER] Advanced ShadowTester loaded")
            except ImportError:
                logger.warning("[RUNG-ADAPTER] ShadowTester not available")
        return self._shadow_tester

    def disable_shadow_mode(self) -> Dict[str, Any]:
        """Disable shadow mode and return comparison stats."""
        self.shadow_mode = False
        total = self.divergence_count + self.agreement_count
        agreement_rate = self.agreement_count / total if total > 0 else 0

        stats: Dict[str, Any] = {
            'total_comparisons': total,
            'agreements': self.agreement_count,
            'divergences': self.divergence_count,
            'agreement_rate': agreement_rate,
            'divergence_samples': self.shadow_log[-10:],  # Last 10 divergences
        }

        logger.info(f"[RUNG-ADAPTER] Shadow mode DISABLED - agreement rate: {agreement_rate:.1%}")
        return stats

    def shadow_compare(self, game_state: Any, context: Dict[str, Any], old_action: str) -> Dict[str, Any]:
        """
        Compare rung system decision with old system decision.

        Returns comparison result without affecting actual action.
        """
        if not self.shadow_mode:
            return {}

        # Get rung system decision
        rung_action, rung_reason = self.rung_system.decide(game_state, context)

        # Compare
        agrees = rung_action == old_action

        if agrees:
            self.agreement_count += 1
        else:
            self.divergence_count += 1

            # Log divergence (limited)
            if len(self.shadow_log) < self._shadow_log_limit:
                self.shadow_log.append({
                    'old_action': old_action,
                    'rung_action': rung_action,
                    'rung_reason': rung_reason,
                    'ordering': self.rung_system.ordering_name,
                    'game_type': context.get('game_type'),
                    'level': context.get('level'),
                })

            logger.debug(f"[SHADOW-DIVERGE] old={old_action}, rung={rung_action} ({rung_reason[:50]})")

        return {
            'agrees': agrees,
            'old_action': old_action,
            'rung_action': rung_action,
            'rung_reason': rung_reason,
        }

    def enable_category(self, category: str):
        """Enable rung system for a specific category (e.g., 'emergency')."""
        if category in self.category_enabled:
            self.category_enabled[category] = True
            logger.info(f"[RUNG-ADAPTER] Category '{category}' ENABLED")

    def disable_category(self, category: str):
        """Disable rung system for a specific category."""
        if category in self.category_enabled:
            self.category_enabled[category] = False
            logger.info(f"[RUNG-ADAPTER] Category '{category}' DISABLED")

    def decide_category(self, category: str, game_state: Any, context: Dict[str, Any]) -> RungResult:
        """
        Get decision from only rungs in a specific category.

        Use this for gradual category takeover.
        """
        if not self.category_enabled.get(category, False):
            return RungResult()  # Empty result if category not enabled

        # Filter to only rungs in this category
        category_rungs = [r for r in self.rung_system.rungs if r.category == category]

        if not category_rungs:
            return RungResult()

        # Evaluate category rungs in priority order
        for rung in sorted(category_rungs, key=lambda r: r.get_priority()):
            result = rung.evaluate(game_state, context)
            if result.has_suggestion(rung.confidence_threshold):
                return result

        return RungResult()

    def build_context_from_core(self, game_state: Any, loop_state: Any = None) -> Dict[str, Any]:
        """
        Build rung context from CoreGameplay state.

        This extracts all the relevant state that _select_action() uses
        and packages it into the context dict that rungs expect.
        """
        context: Dict[str, Any] = {}

        try:
            # Game identification
            if hasattr(self.core, 'session_manager') and self.core.session_manager:
                game_id = self.core.session_manager.current_game_id
                context['game_id'] = game_id
                context['game_type'] = game_id[:4] if game_id and len(game_id) >= 4 else None

            # Level and score
            if hasattr(game_state, 'score'):
                context['level'] = int(game_state.score) + 1
                context['score'] = game_state.score

            # Budget tracking
            if loop_state:
                context['action_count'] = getattr(loop_state, 'action_count', 0)
                context['budget_used_percent'] = context['action_count'] / 2000.0  # Assume 2000 budget

            # Agent info
            if hasattr(self.core, 'game_config'):
                context['agent_id'] = self.core.game_config.get('agent_id')
                context['agent_role'] = self.core.game_config.get('agent_role')

            # Two-streams weights
            context['w_A'] = getattr(self.core, '_current_wA', 0.5)
            context['w_B'] = getattr(self.core, '_current_wB', 0.5)

            # Position
            context['agent_position'] = getattr(self.core, '_current_agent_position', None)

            # Safety weights (from graduated danger system) - use available actions
            available = context.get('available_actions', [1, 2, 3, 4, 5, 6, 7])
            default_safety = {a: 1.0 for a in available}
            context['action_safety_weights'] = getattr(self.core, '_action_safety_weights', default_safety)

            # Recent actions
            context['recent_actions'] = getattr(self.core, '_recent_actions', [])[-10:]

            # Game type for primitive suggester
            context['game_type'] = context.get('game_id', '').split('-')[0] if context.get('game_id') else None

            # Self-model
            if hasattr(self.core, 'agent_self_model') and self.core.agent_self_model:
                context['self_model'] = self.core.agent_self_model

            # Exploration state
            context['is_frontier'] = self.core._is_frontier_level(
                context.get('game_id', ''),
                context.get('level', 1)
            ) if hasattr(self.core, '_is_frontier_level') else False

        except Exception as e:
            logger.debug(f"[RUNG-ADAPTER] Context build partial failure: {e}")

        return context

    def full_decide(self, game_state: Any, loop_state: Any = None) -> Tuple[str, str]:
        """
        Full replacement for _select_action() - PHASE 3.

        Use this when ready for complete migration.
        """
        context = self.build_context_from_core(game_state, loop_state)
        return self.rung_system.decide(game_state, context)


# =============================================================================
# HELPER: Create custom ordering interactively
# =============================================================================

def create_custom_ordering(name: str, rung_priorities: Dict[str, int]) -> List[Tuple[str, int]]:
    """
    Create a custom ordering.

    Args:
        name: Name for the ordering
        rung_priorities: Dict mapping rung names to priorities (1=highest)

    Example:
        ordering = create_custom_ordering('my_ordering', {
            'survey': 5,
            'death_avoidance': 10,
            'discovery_exploitation': 15,
            'smart_action_selection': 99,
        })
    """
    ordering = [(rung, priority) for rung, priority in sorted(rung_priorities.items(), key=lambda x: x[1])]
    return ordering


# =============================================================================
# INTEGRATION PLAN - How to wire this into core_gameplay.py
# =============================================================================
"""
INTEGRATION PLAN: Decision Rung System -> core_gameplay.py
==========================================================

CURRENT STATE:
- _select_action() is ~1500 lines of sequential decision logic
- Hardcoded ordering: discovery -> danger -> embedding -> topology -> exploration -> ...
- No easy way to experiment with different orderings

TARGET STATE:
- _select_action() calls DecisionRungSystem.decide()
- Ordering is configurable per agent/game/phase
- New features = new rungs (no touching existing code)

MIGRATION STEPS:

STEP 1: ADD IMPORTS (at top of core_gameplay.py)
------------------------------------------------
from decision_rung_system import (
    ORDERING_PRESETS,
    CoreGameplayAdapter,
    DecisionRungSystem,
)

STEP 2: INITIALIZE IN __init__ (in CoreGameplay.__init__)
---------------------------------------------------------
# Near other engine initialization
self.decision_adapter = CoreGameplayAdapter(self, ordering='comprehensive')

# Optional: Enable shadow mode for testing
if self.game_config.get('shadow_mode_decisions'):
    self.decision_adapter.enable_shadow_mode()

STEP 3A: SHADOW MODE (in _select_action, at the END before return)
------------------------------------------------------------------
# Shadow compare before returning old decision
if hasattr(self, 'decision_adapter') and self.decision_adapter.shadow_mode:
    context = self.decision_adapter.build_context_from_core(game_state, loop_state)
    self.decision_adapter.shadow_compare(game_state, context, action)

return action, reasoning

STEP 3B: CATEGORY TAKEOVER (in _select_action, at the START)
------------------------------------------------------------
# Let rung system handle emergency category
if hasattr(self, 'decision_adapter'):
    context = self.decision_adapter.build_context_from_core(game_state, loop_state)

    # Emergency rungs (infinite loop breaker, coordinate oscillation)
    emergency = self.decision_adapter.decide_category('emergency', game_state, context)
    if emergency.has_suggestion(0.8):
        return emergency.action, f"[RUNG-EMERGENCY] {emergency.reason}"

    # Filter rungs (danger weights, pariah avoidance)
    filter_result = self.decision_adapter.decide_category('filter', game_state, context)
    if filter_result.weights:
        # Apply weights to action_safety_weights
        for action, weight in filter_result.weights.items():
            action_safety_weights[action] *= weight

STEP 4: FULL REPLACEMENT (replace entire _select_action body)
-------------------------------------------------------------
async def _select_action(self, game_state, loop_state=None):
    '''Select action using modular rung system.'''
    if not hasattr(self, 'decision_adapter'):
        self.decision_adapter = CoreGameplayAdapter(self)

    return self.decision_adapter.full_decide(game_state, loop_state)

CONFIGURATION OPTIONS:
----------------------
# In game_config or agent config:
{
    'decision_ordering': 'llm_optimal',  # or 'human_brain', 'efficiency', etc.
    'decision_strategy': 'ladder',       # or 'weighted', 'phased', 'parallel'
    'shadow_mode_decisions': True,       # Enable comparison logging
    'rung_categories_enabled': ['emergency', 'filter'],  # Partial takeover
}

ROLLBACK:
---------
If issues arise, simply:
1. Disable shadow mode / category takeover
2. Comment out the rung system calls
3. Original _select_action() logic remains intact
"""


if __name__ == '__main__':
    # Demo: Show available rungs and orderings
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
        rungs = [r[0] for r in ordering]
        print(f"  - {name}: {len(ordering)} rungs")
        print(f"    Order: {' -> '.join(rungs[:5])}...")

    print("\n" + "=" * 60)
    print("Usage:")
    print("  system = DecisionRungSystem(strategy='ladder')")
    print("  system.load_ordering('llm_optimal')")
    print("  action, reason = system.decide(game_state, context)")
    print("=" * 60)

    print("\nIntegration with core_gameplay.py:")
    print("  adapter = CoreGameplayAdapter(core_gameplay_ref)")
    print("  adapter.enable_shadow_mode()  # Compare decisions")
    print("  adapter.enable_category('emergency')  # Partial takeover")
    print("  action, reason = adapter.full_decide(game_state)  # Full replacement")
    print("=" * 60)
