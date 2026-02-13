"""
Rung Base Infrastructure
========================
Shared types, ABC, utilities, and Action6 coordinate system
used by all decision rung implementations.

Extracted from decision_rung_system.py Phase 4.2.
"""

import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import logging
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

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

# ── Lazy loaders (avoid circular imports) ────────────────────────────────────

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

    return _seed_primitives


# Type hints for engine registry (avoid circular imports)
if TYPE_CHECKING:
    from engines.registry import EngineRegistry


# ── Enums ────────────────────────────────────────────────────────────────────

class DecisionStrategy(Enum):
    """How to combine rung outputs"""
    LADDER = "ladder"
    WEIGHTED = "weighted"
    PHASED = "phased"
    PARALLEL = "parallel"
    CONTEXT_ADAPTIVE = "context_adaptive"
    COGNITIVE = "cognitive"


# ── Data Classes ─────────────────────────────────────────────────────────────

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
    detection_source: str = "unknown"
    sample_size: int = 0
    agent_diversity: int = 0
    temporal_spread_generations: float = 0.0

    validation_type: str = "frequency"
    positive_outcomes: int = 0
    negative_outcomes: int = 0

    crystallization_stage: int = 1

    resonance_games: int = 0
    resonance_score: float = 0.0

    def validity_score(self) -> float:
        """Calculate validity score - separating 'widely known' from 'actually true'."""
        total_outcomes = self.positive_outcomes + self.negative_outcomes
        outcome_ratio = self.positive_outcomes / max(1, total_outcomes)

        diversity_factor = min(1.0, self.agent_diversity / 5.0)
        temporal_factor = min(1.0, self.temporal_spread_generations / 20.0)
        resonance_factor = self.resonance_score * 0.5

        validation_multiplier = {
            'frequency': 0.5,
            'outcome_based': 0.8,
            'win_validated': 1.0,
            'cross_game': 1.2,
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
    action: Optional[str] = None
    confidence: float = 0.0
    reason: str = ""
    weights: Optional[Dict[str, float]] = None
    metadata: Dict[str, Any] = field(default_factory=lambda: {})
    primitives_used: List[str] = field(default_factory=lambda: [])
    provenance: Optional[KnowledgeProvenance] = None
    resolved_questions: List[str] = field(default_factory=lambda: [])

    def has_suggestion(self, threshold: float = 0.0) -> bool:
        return self.action is not None and self.confidence > threshold

    def adjusted_confidence(self) -> float:
        """Confidence adjusted by provenance validity."""
        if self.provenance is None:
            return self.confidence
        return self.confidence * self.provenance.validity_score()


# ── Utility Functions ────────────────────────────────────────────────────────

def filter_available_actions(actions: List[str], context: Dict[str, Any]) -> List[str]:
    """Filter action list to only those available in current game state."""
    available = context.get('available_actions', [1, 2, 3, 4, 5, 6, 7])
    if not available:
        return actions

    available_strs = {f'ACTION{a}' for a in available}
    filtered = [a for a in actions if a in available_strs]

    if not filtered:
        return [f'ACTION{a}' for a in available]

    return filtered


def get_random_available_action(context: Dict[str, Any]) -> str:
    """Get a random action from available actions in context."""
    available = context.get('available_actions', [1, 2, 3, 4])
    return f'ACTION{random.choice(available)}'


def get_available_action_weights(context: Dict[str, Any], default_weight: float = 1.0) -> Dict[str, float]:
    """Get a weights dict initialized to default_weight for all available actions only."""
    available = context.get('available_actions', [1, 2, 3, 4, 5, 6, 7])
    return {f'ACTION{a}': default_weight for a in available}


def get_available_actions_list(context: Dict[str, Any]) -> List[str]:
    """Get list of available action strings from context."""
    available = context.get('available_actions', [1, 2, 3, 4, 5, 6, 7])
    return [f'ACTION{a}' for a in available]


def is_action_available(action: Optional[str], context: Dict[str, Any]) -> bool:
    """Check if an action string is in the available actions for this game."""
    if action is None:
        return True
    if not isinstance(action, str) or not action.startswith('ACTION'):
        return False
    try:
        action_num = int(action.replace('ACTION', ''))
        available = context.get('available_actions', [])
        if not available:
            return True
        return action in available or action_num in available
    except (ValueError, TypeError):
        return False


def validate_action(action: Optional[str], context: Dict[str, Any]) -> Optional[str]:
    """Validate an action and return it if available, None otherwise."""
    if is_action_available(action, context):
        return action
    return None


# ── Action6 Coordinate System ───────────────────────────────────────────────

class Action6CoordinateProvider:
    """
    Centralized provider for ACTION6 coordinates.

    ACTION6 is a PARAMETERIZED action that requires explicit (x, y) coordinates.
    Every part of the system that can produce ACTION6 MUST provide coordinates.

    Coordinate System (64x64 grid):
        (0,0) ------------- (63,0)
          |                    |
          |   Y increases v    |
          |   X increases >    |
          |                    |
        (0,63) ----------- (63,63)
    """

    @staticmethod
    def get_coordinates(
        context: Dict[str, Any],
        engines: Optional[Any] = None,
        frame: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Get coordinates for ACTION6 using best available strategy."""
        game_type = context.get('game_type', '')
        level = context.get('level', 1)

        # Strategy 1: Detected objects/pseudobuttons
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
        if frame is not None:
            try:
                game_key = f"{game_type}_L{level}"
                coords = Action6CoordinateProvider._find_interesting_region(frame, game_key)
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

    # Per-game cycling state: game_key -> cycle index
    _cycle_indices: Dict[str, int] = {}

    @staticmethod
    def _find_interesting_region(frame: List[List[int]], game_key: str = "") -> Optional[Dict[str, int]]:
        """Find visually interesting regions in the frame, cycling through objects per-game."""
        if frame is None or len(frame) < 4:
            return None

        interesting_points: List[Tuple[int, int, int]] = []
        for y, row in enumerate(frame):
            for x, pixel in enumerate(row):
                val = int(pixel) if hasattr(pixel, '__int__') else pixel
                if val != 0:
                    interesting_points.append((x, y, val))

        if not interesting_points:
            return None

        color_groups: Dict[int, List[Tuple[int, int]]] = {}
        for x, y, color in interesting_points:
            if color not in color_groups:
                color_groups[color] = []
            color_groups[color].append((x, y))

        frame_area = len(frame) * (len(frame[0]) if len(frame) > 0 else 64)
        valid_groups = {
            c: pts for c, pts in color_groups.items()
            if 3 <= len(pts) <= frame_area * 0.4
        }
        if not valid_groups:
            valid_groups = color_groups

        sorted_colors = sorted(valid_groups.keys(), key=lambda c: len(valid_groups[c]), reverse=True)

        # Per-game cycling: each game tracks its own index through color groups
        current_idx = Action6CoordinateProvider._cycle_indices.get(game_key, 0)
        current_idx += 1
        Action6CoordinateProvider._cycle_indices[game_key] = current_idx

        idx = current_idx % len(sorted_colors)
        target_color = sorted_colors[idx]
        target_group = valid_groups[target_color]

        avg_x = sum(p[0] for p in target_group) // len(target_group)
        avg_y = sum(p[1] for p in target_group) // len(target_group)

        return {'x': avg_x, 'y': avg_y}

    @staticmethod
    def enrich_result_with_coordinates(
        result: "RungResult",
        context: Dict[str, Any],
        engines: Optional[Any] = None,
        frame: Optional[Any] = None
    ) -> "RungResult":
        """Ensure a RungResult for ACTION6 has coordinates."""
        if result.action != 'ACTION6':
            return result

        metadata = result.metadata or {}
        has_coords = (
            ('x' in metadata and 'y' in metadata) or
            'pixel_position' in metadata or
            'target' in metadata or
            'grid_target' in metadata
        )

        if has_coords:
            return result

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


# ── DecisionRung ABC ─────────────────────────────────────────────────────────

class DecisionRung(ABC):
    """
    Base class for all decision rungs.
    Each rung evaluates the current state and optionally suggests an action.

    PRIMITIVE INTEGRATION:
    Rungs can declare ``required_primitives`` to access seed primitives.
    The primitive registry is loaded lazily to avoid circular imports.
    """

    name: str = "base_rung"
    category: str = "unknown"
    default_priority: int = 50
    confidence_threshold: float = 0.3

    required_primitives: List[str] = []

    def __init__(
        self,
        core_gameplay_ref: Any = None,
        engine_registry: Optional["EngineRegistry"] = None
    ):
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
        self._primitives = None
        self._primitives_validated = False

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

    def _ensure_primitives(self) -> bool:
        """Ensure primitives are loaded and validated."""
        if self._primitives_validated:
            return self._primitives is not None

        self._primitives = _load_primitives()
        self._primitives_validated = True

        if self.required_primitives and self._primitives:
            missing: List[str] = []
            for pname in self.required_primitives:
                if not self._primitives.get(pname):
                    missing.append(pname)
            if missing:
                logger.warning(f"[RUNG-{self.name}] Missing primitives: {missing}")

        return self._primitives is not None

    def call_primitive(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """Call a seed primitive by name."""
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
        """Evaluate this rung and return a result."""
        pass

    def get_priority(self) -> int:
        """Return current priority (considering override)"""
        return self.priority_override if self.priority_override is not None else self.default_priority

    def record_outcome(self, was_accepted: bool, outcome_score: float = 0.0):
        """Record whether this rung's suggestion was used and how it went"""
        self.stats['calls'] += 1
        if was_accepted:
            self.stats['accepted'] += 1
        n = self.stats['calls']
        self.stats['avg_confidence'] = (self.stats['avg_confidence'] * (n-1) + outcome_score) / n
