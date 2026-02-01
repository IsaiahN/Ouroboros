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

    return _seed_primitives


class DecisionStrategy(Enum):
    """How to combine rung outputs"""
    LADDER = "ladder"           # First confident answer wins
    WEIGHTED = "weighted"       # All rungs vote, weighted sum
    PHASED = "phased"           # Different ordering by phase
    PARALLEL = "parallel"       # Run all, pick highest confidence
    CONTEXT_ADAPTIVE = "context_adaptive"  # Select strategy based on context (frontier/replay/optimization)


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
    temporal_spread_hours: float = 0.0 # How spread out in time (recent vs ancient)

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

        # Temporal spread bonus: patterns that persist over time are more valid
        temporal_factor = min(1.0, self.temporal_spread_hours / 24.0)  # Cap at 1 day

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
            'temporal_spread_hours': self.temporal_spread_hours,
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

    NOTE: Uses self.core._build_survey_context() private method.
    Kept as core access since it reads internal survey state.
    """
    name = "survey"
    category = "orientation"
    default_priority = 5
    confidence_threshold = 0.0  # Always runs, modifies context not action

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        if not self.core:
            return RungResult()

        # Check if survey already done for this level
        if context.get('survey_complete', False):
            return RungResult(confidence=0.0, reason="Survey already complete")

        # Build survey context
        try:
            survey: Dict[str, Any] = self.core._build_survey_context() if hasattr(self.core, '_build_survey_context') else {}
            context['survey'] = survey
            context['survey_complete'] = True
            return RungResult(
                confidence=0.1,  # Low confidence - doesn't suggest action, just observes
                reason=f"Survey complete: {len(survey.get('detected_features', {}))} features detected",
                metadata={'survey': survey}
            )
        except Exception as e:
            return RungResult(reason=f"Survey failed: {e}")


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

            # Initialize weights at 1.0 for all actions
            weights = {f'ACTION{i}': 1.0 for i in range(1, 8)}
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

    NOTE: Uses self.core._last_discovery private attribute.
    Kept as core access since it reads ephemeral discovery state.
    """
    name = "discovery_exploitation"
    category = "exploitation"
    default_priority = 20
    confidence_threshold = 0.3

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        if not self.core:
            return RungResult()

        try:
            discovery = getattr(self.core, '_last_discovery', None)
            if not discovery:
                return RungResult()

            action = discovery.get('action', '')
            reliability = discovery.get('reliability_score', 0.0)
            validated = discovery.get('validated', False)

            if not action.startswith('ACTION'):
                return RungResult()

            if reliability >= 0.6 or validated:
                return RungResult(
                    action=action,
                    confidence=0.9,
                    reason=f"Exploiting discovery: {discovery.get('controlled_color', '?')} (rel={reliability:.2f})",
                    metadata={'discovery': discovery}
                )
            elif reliability >= 0.3:
                return RungResult(
                    action=action,
                    confidence=0.5,
                    reason=f"Testing hypothesis: {discovery.get('controlled_color', '?')} (rel={reliability:.2f})",
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
                return RungResult(
                    action=suggestion.get('action'),
                    confidence=suggestion.get('confidence', 0),
                    reason=f"Embedding match: {suggestion.get('similar_count', 0)} similar frames",
                    metadata={'suggestion': suggestion}
                )

            # Even below threshold, return as weighted boost
            if suggestion and suggestion.get('confidence', 0) >= 0.4:
                return RungResult(
                    confidence=suggestion.get('confidence', 0),
                    weights={suggestion.get('action', 'ACTION1'): 1.0 + suggestion.get('confidence', 0) * 0.5},
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
                # Force exploration/revision
                exploration_actions = ['ACTION1', 'ACTION2', 'ACTION3', 'ACTION4']
                return RungResult(
                    action=random.choice(exploration_actions),
                    confidence=0.7,
                    reason=f"Theory contradicted - forcing exploration",
                    metadata={'theory_stage': theory_stage}
                )
            elif theory_stage == 'speculating':
                # Boost exploration
                return RungResult(
                    confidence=0.3,
                    weights={f'ACTION{i}': 1.2 for i in range(1, 5)},  # Boost movement
                    reason=f"Speculating - exploration boosted",
                    metadata={'theory_stage': theory_stage}
                )
            return RungResult(metadata={'theory_stage': theory_stage})
        except Exception as e:
            return RungResult(reason=f"Scientific method failed: {e}")


class TwoStreamsRung(DecisionRung):
    """Stream A (private) vs Stream B (network) conflict detection - HYPOTHESIS

    NOTE: Uses self.core._wA and self.core._wB private attributes.
    Kept as core access since it reads stream weight state.
    """
    name = "two_streams"
    category = "hypothesis"
    default_priority = 30
    confidence_threshold = 0.4

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        if not self.core:
            return RungResult()

        try:
            wA = getattr(self.core, '_wA', 0.5)
            wB = getattr(self.core, '_wB', 0.5)

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
    """Historical action traces from network - EXPLOITATION

    NOTE: This rung uses self.core._get_network_action_wisdom() which is a private
    method on CoreGameplay. Kept as core access for now.
    """
    name = "network_wisdom"
    category = "exploitation"
    default_priority = 35
    confidence_threshold = 0.4

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        # Uses private method on core, not an engine
        if not self.core or not hasattr(self.core, '_get_network_action_wisdom'):
            return RungResult()

        try:
            game_type = context.get('game_type', '')
            level = context.get('level', 1)

            wisdom = self.core._get_network_action_wisdom(game_type, level)

            if wisdom and wisdom.get('confidence', 0) >= self.confidence_threshold:
                return RungResult(
                    action=wisdom.get('action'),
                    confidence=wisdom.get('confidence', 0),
                    reason=f"Network wisdom: {wisdom.get('action')} (conf={wisdom.get('confidence', 0):.2f})",
                    metadata={'wisdom': wisdom}
                )
            elif wisdom and wisdom.get('is_least_bad', False):
                return RungResult(
                    action=wisdom.get('action'),
                    confidence=wisdom.get('confidence', 0),
                    reason=f"Least-bad network wisdom: {wisdom.get('action')}",
                    metadata={'wisdom': wisdom, 'is_least_bad': True}
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
                return RungResult(
                    action=f"ACTION{result.action}",
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
                return RungResult(
                    action=prediction.get('test_action'),
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
                exploration_actions = ['ACTION1', 'ACTION2', 'ACTION3', 'ACTION4', 'ACTION6']
                return RungResult(
                    action=random.choice(exploration_actions),
                    confidence=0.6,
                    reason=f"Discovery phase: budget={budget_used:.0%}, coverage={coverage:.0%}",
                    metadata={'phase': 'discovery', 'budget_used': budget_used, 'coverage': coverage}
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

            # Initialize weights with EXPLORATION BONUS for untried actions
            weights = {f'ACTION{i}': 1.5 for i in range(1, 8)}  # Start high - untried = bonus!
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
            temporal_hours = 0.0
            if first_seen and last_seen:
                try:
                    from datetime import datetime

                    # Handle string or datetime
                    if isinstance(first_seen, str):
                        first_dt = datetime.fromisoformat(first_seen.replace('Z', '+00:00'))
                    else:
                        first_dt = first_seen
                    if isinstance(last_seen, str):
                        last_dt = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
                    else:
                        last_dt = last_seen
                    temporal_hours = (last_dt - first_dt).total_seconds() / 3600.0
                except Exception:
                    pass

            provenance = KnowledgeProvenance(
                detection_source='action_traces',
                sample_size=total_data_points,
                agent_diversity=len(unique_sessions),  # Unique sessions as proxy for diversity
                temporal_spread_hours=temporal_hours,
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

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        try:
            strategy = context.get('fallback_strategy', 'balanced')

            if strategy == 'exploration':
                weights = {'ACTION1': 1.2, 'ACTION2': 1.2, 'ACTION3': 1.2, 'ACTION4': 1.2,
                          'ACTION5': 0.5, 'ACTION6': 1.0, 'ACTION7': 0.3}
            elif strategy == 'exploitation':
                weights = {'ACTION1': 0.8, 'ACTION2': 0.8, 'ACTION3': 0.8, 'ACTION4': 0.8,
                          'ACTION5': 1.5, 'ACTION6': 1.2, 'ACTION7': 1.0}
            else:  # balanced
                weights = {f'ACTION{i}': 1.0 for i in range(1, 8)}

            # Weighted random choice
            total = sum(weights.values())
            r = random.random() * total
            cumulative = 0
            for action, weight in weights.items():
                cumulative += weight
                if r <= cumulative:
                    return RungResult(
                        action=action,
                        confidence=0.1,
                        reason=f"Fallback ({strategy}): {action}",
                        weights=weights
                    )

            return RungResult(action='ACTION1', confidence=0.1, reason="Ultimate fallback")
        except Exception as e:
            return RungResult(action='ACTION1', confidence=0.1, reason=f"Fallback error: {e}")


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
                # Emergency! Pick random action
                action = random.choice(['ACTION1', 'ACTION2', 'ACTION3', 'ACTION4', 'ACTION6'])
                return RungResult(
                    action=action,
                    confidence=0.95,
                    reason=f"EMERGENCY: Breaking infinite loop (stuck {stuck_count}/20)",
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

    NOTE: Uses self.core._last_action_no_change private attribute.
    Kept as core access since it reads collision state.
    """
    name = "map_intel_collision"
    category = "exploitation"
    default_priority = 24
    confidence_threshold = 0.5

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        if not self.core:
            return RungResult()

        try:
            last_no_change = getattr(self.core, '_last_action_no_change', False)
            last_action = context.get('last_action', '')

            if not last_no_change or last_action not in ['ACTION1', 'ACTION2', 'ACTION3', 'ACTION4']:
                return RungResult()

            # Get perpendicular alternatives
            perpendicular_map = {
                'ACTION1': ['ACTION3', 'ACTION4'],
                'ACTION2': ['ACTION3', 'ACTION4'],
                'ACTION3': ['ACTION1', 'ACTION2'],
                'ACTION4': ['ACTION1', 'ACTION2'],
            }

            alternatives = perpendicular_map.get(last_action, [])
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
    """Working theory must score proposals, contradicted = force exploration - FINALIZER"""
    name = "theory_gate"
    category = "hypothesis"
    default_priority = 32
    confidence_threshold = 0.6

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        sme = self.engines.scientific_method_engine
        if sme is None:
            return RungResult()

        try:
            theory = sme.get_working_theory() if hasattr(sme, 'get_working_theory') else None

            if theory and theory.get('stage') == 'contradicted':
                # Force exploration/revision
                exploration_actions = ['ACTION1', 'ACTION2', 'ACTION3', 'ACTION4', 'ACTION6']
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
                        return RungResult(
                            action=template[action_idx],
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
                    if action:
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
                        # Return first action and signal that checkpoint is now active
                        return RungResult(
                            action=sequence[0],
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
                return RungResult(
                    action=action,
                    confidence=0.8,
                    reason=f"Following sequence: step {sequence_position + 1}/{len(active_sequence)}",
                    metadata={'sequence_length': len(active_sequence), 'position': sequence_position}
                )
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
                    return RungResult(
                        action=result['sequence'][0] if result['sequence'] else None,
                        confidence=result.get('confidence', 0.5),
                        reason=f"Multi-stage match: {result.get('stage', 'unknown')}",
                        metadata={'match_result': result}
                    )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Multi-stage matching failed: {e}")


class ThreeLayerFilterRung(DecisionRung):
    """Meta-learning filter preventing wasted actions - FILTER

    NOTE: Uses self.core._action_filter_layer* private methods.
    Kept as core access since these are tightly coupled filter methods.
    """
    name = "three_layer_filter"
    category = "filter"
    default_priority = 55
    confidence_threshold = 0.0  # Modifies weights, doesn't suggest

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        if not self.core:
            return RungResult()

        try:
            weights: Dict[str, float] = {}
            frame = game_state.frame if hasattr(game_state, 'frame') else None
            position = context.get('position', (0, 0))

            # Layer 1: Cache check
            if hasattr(self.core, '_action_filter_layer1_cache_check'):
                for i in range(1, 8):
                    action = f'ACTION{i}'
                    failed = self.core._action_filter_layer1_cache_check(action, position, frame)
                    weights[action] = 0.1 if failed else 1.0

            # Layer 2: Object prefilter (for click actions)
            if hasattr(self.core, '_action_filter_layer2_object_prefilter'):
                for action in ['ACTION5', 'ACTION6', 'ACTION7']:
                    has_object = self.core._action_filter_layer2_object_prefilter(action, position, frame)
                    if not has_object:
                        weights[action] = weights.get(action, 1.0) * 0.3

            # Layer 3: Pattern prediction
            if hasattr(self.core, '_action_filter_layer3_pattern_predict'):
                for i in range(1, 8):
                    action = f'ACTION{i}'
                    prob = self.core._action_filter_layer3_pattern_predict(action, context)
                    if prob < 0.15:
                        weights[action] = weights.get(action, 1.0) * 0.2

            if weights:
                return RungResult(
                    confidence=0.3,
                    weights=weights,
                    reason=f"3-layer filter applied: {sum(1 for w in weights.values() if w < 1.0)} actions penalized",
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
            game_type = context.get('game_type', '')
            level = context.get('level', 1)
            role = context.get('agent_role', 'generalist')

            # Role-adjusted penalty multipliers
            role_multipliers = {
                'pioneer': 0.3,
                'optimizer': 1.0,
                'generalist': 0.7,
                'exploiter': 0.5
            }
            multiplier = role_multipliers.get(role, 0.7)

            if hasattr(vpe, 'get_pariahs'):
                pariahs = vpe.get_pariahs(game_type, level)
                weights: Dict[str, float] = {}
                for pariah in pariahs:
                    action = pariah.get('failed_action')
                    toxicity = pariah.get('toxicity', 0.5)
                    # Apply role-adjusted penalty
                    penalty = toxicity * multiplier
                    weights[action] = max(0.05, 1.0 - penalty)

                if weights:
                    return RungResult(
                        confidence=0.4,
                        weights=weights,
                        reason=f"Pariah avoidance: {len(pariahs)} patterns, role={role}",
                        metadata={'pariahs': len(pariahs), 'role_multiplier': multiplier}
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
                        action=random.choice(['ACTION1', 'ACTION2', 'ACTION3', 'ACTION4', 'ACTION6']),
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
                    weights = {f'ACTION{i}': 1.0 for i in range(1, 8)}
                    if fatal_action:
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

                # Convert sensations to action biases
                weights: Dict[str, float] = {}
                if sensation.get('approach_score', 0) > 0.5:
                    # Bias toward movement actions
                    for action in ['ACTION1', 'ACTION2', 'ACTION3', 'ACTION4']:
                        weights[action] = 1.0 + sensation['approach_score'] * 0.3
                if sensation.get('threat_level', 0) > 0.5:
                    # Bias away from certain directions
                    threat_direction = sensation.get('threat_direction')
                    if threat_direction:
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
                    return RungResult(
                        action=persona['suggested_action'],
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
                    if suggested:
                        return RungResult(
                            action=suggested,
                            confidence=insights.get('confidence', 0.4),
                            reason=f"Near-miss insight: {insights.get('category', 'unknown')}",
                            metadata={'insights': insights}
                        )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Near-miss analyzer failed: {e}")


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
                    return RungResult(
                        action=subgoal['next_action'],
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
                        # Build epistemological provenance
                        # Cross-role resonance is the gold standard for validation
                        role_diversity = best.get('role_diversity', 1)
                        game_types = best.get('game_types', [])

                        provenance = KnowledgeProvenance(
                            detection_source='resonance_patterns',
                            sample_size=role_diversity * len(game_types),
                            agent_diversity=role_diversity,  # Different ROLES = different cognitive biases
                            temporal_spread_hours=0.0,  # Not tracked for resonance
                            validation_type='cross_role_convergence',  # The gold standard
                            positive_outcomes=role_diversity,  # Each role validated
                            negative_outcomes=0,
                            crystallization_stage=4 if role_diversity >= 3 else 3,  # High: crystallized
                            resonance_games=len(game_types),  # How many games share this pattern
                            resonance_score=resonance_score
                        )

                        return RungResult(
                            action=best.get('suggested_action'),
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
                        # Suggest a different action entirely
                        current_action = context.get('last_action', 'ACTION6')
                        alternatives = [a for a in ['ACTION1', 'ACTION2', 'ACTION3', 'ACTION4', 'ACTION5', 'ACTION7']
                                       if a != current_action]
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

            if hasattr(sm, 'get_network_object_inventory'):
                inventory = sm.get_network_object_inventory(game_type, level)
                if inventory.get('total_unique', 0) > 0:
                    # Bias toward interacting with known objects
                    interactable = inventory.get('interactable', [])
                    if interactable:
                        return RungResult(
                            action='ACTION6',
                            confidence=0.5,
                            reason=f"Network inventory: {len(interactable)} interactable positions",
                            metadata={'inventory': inventory}
                        )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Network object inventory failed: {e}")


class DeliberationSystemRung(DecisionRung):
    """TRM-inspired iterative refinement - HYPOTHESIS

    NOTE: Uses self.core._last_deliberation_result private attribute.
    Kept as core access since it reads ephemeral deliberation state.
    """
    name = "deliberation_system"
    category = "hypothesis"
    default_priority = 29
    confidence_threshold = 0.5

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        if not self.core:
            return RungResult()

        try:
            deliberation = getattr(self.core, '_last_deliberation_result', None)

            if deliberation:
                if deliberation.get('convergence_achieved', False):
                    action = deliberation.get('consensus_action')
                    if action:
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
                    return RungResult(
                        action=prediction.get('action'),
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
                    if sequence_action:
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
# ORDERING PRESETS
# =============================================================================

ORDERING_PRESETS = {
    # Current behavior - efficiency-optimized (15 rungs - core only)
    'efficiency': [
        ('infinite_loop_breaker', 1),
        ('coordinate_oscillation', 3),
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

    # LLM-optimal - understanding first (all 42 rungs)
    'llm_optimal': [
        ('infinite_loop_breaker', 1),
        ('coordinate_oscillation', 2),
        ('imagination_budget', 3),
        ('breakthrough_budget', 4),
        ('regulatory_signal', 5),
        ('survey', 6),
        ('network_exploration_stats', 7),
        ('scientific_method', 10),
        ('questioning_engine', 12),
        ('frustration_detection', 14),
        ('two_streams', 16),
        ('i_thread', 18),
        ('metacognitive_prediction', 20),
        ('deliberation_system', 22),
        ('theory_gate', 24),
        ('sensation_engine', 26),
        ('resonance_detector', 28),
        ('network_wisdom', 30),
        ('death_avoidance', 32),
        ('terminal_pattern', 34),
        ('pariah_avoidance', 36),
        ('three_layer_filter', 38),
        ('three_try_sequence', 40),
        ('discovery_exploitation', 42),
        ('embedding_suggestion', 44),
        ('multi_stage_matching', 46),
        ('replay_learning', 48),
        ('primitive_suggester', 50),
        ('abstraction_templates', 54),
        ('few_shot_invariants', 56),
        ('subgoal_planning', 58),
        ('visual_analyzer', 60),
        ('network_object_inventory', 62),
        ('near_miss_analyzer', 64),
        ('completion_prediction', 66),
        ('frontier_topology', 68),
        ('map_intel_collision', 70),
        ('exploration_phase', 72),
        ('grid_exploration', 74),
        ('smart_action_selection', 99),
    ],

    # Human brain - parallel attention + fear interrupt
    'human_brain': [
        ('infinite_loop_breaker', 1),   # Panic response
        ('coordinate_oscillation', 2),  # Repetitive behavior detection
        ('death_avoidance', 3),         # Amygdala - fast fear (12ms)
        ('terminal_pattern', 4),        # Pattern recognition of danger
        ('survey', 5),                  # Attention - what's salient?
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

    # Full 42-rung comprehensive ordering
    'comprehensive': [
        # EMERGENCY (Priority 1-5)
        ('infinite_loop_breaker', 1),
        ('coordinate_oscillation', 2),

        # ORIENTATION - Understanding the world (Priority 5-20)
        ('imagination_budget', 5),
        ('breakthrough_budget', 6),
        ('regulatory_signal', 7),
        ('survey', 8),
        ('network_exploration_stats', 9),
        ('questioning_engine', 10),
        ('exploration_phase', 12),
        ('frustration_detection', 13),

        # FILTER - Modify action weights (Priority 15-25)
        ('death_avoidance', 15),
        ('terminal_pattern', 16),
        ('pariah_avoidance', 17),
        ('three_layer_filter', 18),

        # HYPOTHESIS - Form and test theories (Priority 25-40)
        ('scientific_method', 25),
        ('theory_gate', 26),
        ('metacognitive_prediction', 27),
        ('deliberation_system', 28),
        ('two_streams', 29),
        ('i_thread', 30),
        ('sensation_engine', 31),
        ('resonance_detector', 32),

        # EXPLOITATION - Use known knowledge (Priority 40-80)
        ('three_try_sequence', 40),
        ('discovery_exploitation', 41),
        ('embedding_suggestion', 42),
        ('multi_stage_matching', 43),
        ('replay_learning', 44),
        ('primitive_suggester', 45),
        ('network_wisdom', 47),
        ('abstraction_templates', 48),
        ('few_shot_invariants', 49),
        ('subgoal_planning', 50),
        ('visual_analyzer', 51),
        ('network_object_inventory', 52),
        ('near_miss_analyzer', 53),
        ('completion_prediction', 54),
        ('frontier_topology', 55),
        ('map_intel_collision', 56),
        ('grid_exploration', 57),

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

    # Exploration-heavy for frontier games
    'frontier_exploration': [
        ('infinite_loop_breaker', 1),
        ('coordinate_oscillation', 2),
        ('frontier_checkpoint', 4),  # Replay best known progress on frontier
        ('survey', 5),
        ('network_exploration_stats', 8),
        ('exploration_phase', 10),
        ('questioning_engine', 15),
        ('scientific_method', 20),
        ('grid_exploration', 25),
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

    # Registry of all available rungs (All 42 + frontier_checkpoint + prior_lessons = 44)
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
        'subgoal_planning': SubgoalPlanningRung,
        'breakthrough_budget': BreakthroughBudgetRung,
        'regulatory_signal': RegulatorySignalRung,
        'visual_analyzer': VisualAnalyzerRung,
        'resonance_detector': ResonanceDetectorRung,

        # Console log features (Features 29-36) - removed: micro_counterfactual, primitive_stuck_detection (stubs)
        'coordinate_oscillation': CoordinateOscillationRung,
        'grid_exploration': GridExplorationRung,
        'network_object_inventory': NetworkObjectInventoryRung,

        # Reasoning log features (Features 37-42)
        'deliberation_system': DeliberationSystemRung,
        'replay_learning': ReplayLearningRung,
        'imagination_budget': ImaginationBudgetRung,
        'completion_prediction': CompletionPredictionRung,
        'network_exploration_stats': NetworkExplorationStatsRung,
    }

    def __init__(self,
                 strategy: str = 'context_adaptive',
                 core_gameplay_ref: Any = None,
                 config_path: Optional[str] = None,
                 engine_registry: Optional["EngineRegistry"] = None):
        """
        Args:
            strategy: 'ladder', 'weighted', 'phased', 'parallel', or 'context_adaptive' (default)
            core_gameplay_ref: Reference to CoreGameplay instance (legacy)
            config_path: Optional path to custom ordering config
            engine_registry: EngineRegistry for modular engine access (preferred)

        Note: CONTEXT_ADAPTIVE is recommended - it selects strategy based on game context:
        - replay_mode (following winning sequence): LADDER - deterministic replay
        - frontier_mode (unbeaten level): WEIGHTED - all rungs vote
        - optimization_mode (refining beaten game): WEIGHTED - find improvements
        - Emergency rungs (loop_breaker, oscillation) always checked first with LADDER semantics
        """
        self.strategy = DecisionStrategy(strategy)
        self.core: Any = core_gameplay_ref
        self._engine_registry: Optional["EngineRegistry"] = engine_registry
        self.rungs: List[DecisionRung] = []
        self.ordering_name = 'default'
        self.config_path = config_path or str(Path(__file__).parent / 'config' / 'rung_orderings.json')

        # Stats
        self.total_decisions = 0
        self.rung_wins: Dict[str, int] = {}

        # Last decision metadata (for checkpoint handoff to context builder)
        self.last_decision_metadata: Dict[str, Any] = {}

        # Load default ordering
        self.load_ordering('efficiency')

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

    def load_ordering(self, preset_name: str) -> None:
        """Load a preset ordering or custom config"""
        self.ordering_name = preset_name
        self.rungs = []

        if preset_name in ORDERING_PRESETS:
            ordering = ORDERING_PRESETS[preset_name]
        else:
            # Try loading from config file
            ordering = self._load_custom_ordering(preset_name)
            if not ordering:
                print(f"[RUNG-SYSTEM] Warning: Unknown ordering '{preset_name}', using efficiency")
                ordering = ORDERING_PRESETS['efficiency']

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
        else:
            return self._decide_ladder(game_state, context)

    def _decide_ladder(self, game_state: Any, context: Dict[str, Any]) -> Tuple[str, str]:
        """First confident answer wins"""
        accumulated_weights: Dict[str, float] = {f'ACTION{i}': 1.0 for i in range(1, 8)}
        self.last_decision_metadata = {}  # Reset metadata

        for rung in self.rungs:
            if not rung.enabled:
                continue

            result = rung.evaluate(game_state, context)

            # Accumulate weights from filter rungs
            if result.weights:
                for action, weight in result.weights.items():
                    accumulated_weights[action] = accumulated_weights.get(action, 1.0) * weight

            # Check if this rung has a confident suggestion
            if result.has_suggestion(rung.confidence_threshold):
                self.rung_wins[rung.name] = self.rung_wins.get(rung.name, 0) + 1
                rung.record_outcome(was_accepted=True)
                # Capture metadata for checkpoint handoff
                self.last_decision_metadata = result.metadata or {}
                return result.action or 'ACTION1', f"[{rung.name}] {result.reason}"

        # No confident answer - use accumulated weights for fallback
        return self._weighted_random_choice(accumulated_weights), "Weighted fallback after ladder"

    def _decide_weighted(self, game_state: Any, context: Dict[str, Any]) -> Tuple[str, str]:
        """All rungs vote, weighted sum decides"""
        action_votes: Dict[str, float] = {f'ACTION{i}': 0.0 for i in range(1, 8)}
        reasons: List[str] = []
        self.last_decision_metadata = {}  # Reset metadata

        for rung in self.rungs:
            if not rung.enabled:
                continue

            result = rung.evaluate(game_state, context)

            if result.action:
                # Weight by confidence and rung priority (lower priority = higher weight)
                weight = result.confidence * (100 - rung.get_priority()) / 100
                action_votes[result.action] = action_votes.get(result.action, 0) + weight
                reasons.append(f"{rung.name}:{result.action}({weight:.2f})")

            # Add explicit weights
            if result.weights:
                for action, w in result.weights.items():
                    action_votes[action] = action_votes.get(action, 0) + w * 0.1

        # Pick highest voted action
        best_action = max(action_votes, key=lambda k: action_votes[k])
        return best_action, f"Weighted vote: {best_action} ({action_votes[best_action]:.2f}) from [{', '.join(reasons[:3])}]"

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

        for rung in self.rungs:
            if not rung.enabled:
                continue

            result = rung.evaluate(game_state, context)

            if result.action and (best_result is None or result.confidence > best_result.confidence):
                best_result = result
                best_rung = rung

        if best_result and best_rung:
            self.rung_wins[best_rung.name] = self.rung_wins.get(best_rung.name, 0) + 1
            return best_result.action or 'ACTION1', f"[{best_rung.name}] {best_result.reason}"

        return 'ACTION1', "No suggestions from any rung"

    def _weighted_random_choice(self, weights: Dict[str, float]) -> str:
        """Make a weighted random choice"""
        total = sum(max(0.05, w) for w in weights.values())  # Minimum 0.05
        r = random.random() * total
        cumulative = 0
        for action, weight in weights.items():
            cumulative += max(0.05, weight)
            if r <= cumulative:
                return action
        return 'ACTION1'

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
                self.rung_wins[rung.name] = self.rung_wins.get(rung.name, 0) + 1
                rung.record_outcome(was_accepted=True)
                return result.action or 'ACTION1', f"[EMERGENCY:{rung.name}] {result.reason}"

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
        action_votes: Dict[str, float] = {f'ACTION{i}': 0.0 for i in range(1, 8)}
        accumulated_weights: Dict[str, float] = {f'ACTION{i}': 1.0 for i in range(1, 8)}
        reasons: List[str] = []

        for rung in self.rungs:
            if not rung.enabled:
                continue
            # Skip emergency rungs - already checked
            if rung.name in self.EMERGENCY_RUNG_NAMES:
                continue

            result = rung.evaluate(game_state, context)

            # Accumulate filter weights (multiplicative)
            if result.weights:
                for action, weight in result.weights.items():
                    accumulated_weights[action] = accumulated_weights.get(action, 1.0) * weight

            # Add suggestion votes (additive, weighted by confidence and priority)
            if result.action:
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
            return self._weighted_random_choice(accumulated_weights), "Weighted random (low confidence)"

        top_contributors = ', '.join(reasons[:3]) if reasons else 'filters only'
        return best_action, f"[WEIGHTED] {best_action} ({best_score:.2f}) from [{top_contributors}]"

    def _decide_ladder_non_emergency(self, game_state: Any, context: Dict[str, Any]) -> Tuple[str, str]:
        """
        LADDER strategy excluding emergency rungs (already checked).
        First confident non-emergency answer wins.
        """
        accumulated_weights: Dict[str, float] = {f'ACTION{i}': 1.0 for i in range(1, 8)}

        for rung in self.rungs:
            if not rung.enabled:
                continue
            # Skip emergency rungs - already checked
            if rung.name in self.EMERGENCY_RUNG_NAMES:
                continue

            result = rung.evaluate(game_state, context)

            # Accumulate weights from filter rungs
            if result.weights:
                for action, weight in result.weights.items():
                    accumulated_weights[action] = accumulated_weights.get(action, 1.0) * weight

            # Check if this rung has a confident suggestion
            if result.has_suggestion(rung.confidence_threshold):
                self.rung_wins[rung.name] = self.rung_wins.get(rung.name, 0) + 1
                rung.record_outcome(was_accepted=True)
                # Capture metadata for checkpoint handoff
                self.last_decision_metadata = result.metadata or {}
                return result.action or 'ACTION1', f"[{rung.name}] {result.reason}"

        # No confident answer - use accumulated weights for fallback
        return self._weighted_random_choice(accumulated_weights), "Weighted fallback after ladder"

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

    def __init__(self, core_gameplay_ref: Any, ordering: str = 'efficiency'):
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

            # Safety weights (from graduated danger system)
            context['action_safety_weights'] = getattr(self.core, '_action_safety_weights', {i: 1.0 for i in range(1, 8)})

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
self.decision_adapter = CoreGameplayAdapter(self, ordering='efficiency')

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
