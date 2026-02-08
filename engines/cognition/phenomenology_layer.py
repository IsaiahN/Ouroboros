"""
Phenomenology Layer - Compressed State with Valence-Tagged Feedback.

Phase 9 Implementation - Cognitive Routing Addon

This module implements the phenomenology layer that:
1. Compresses high-dimensional blackboard state to 5D FeltState
2. Injects FeltState back into blackboard for next cycle
3. Uses valence-tagged priorities in the encoding itself

Key insight from the design doc:
    "Experience isn't something added to data—it's the compressed output.
     Pain doesn't represent damage then add 'bad'—pain IS the representation
     of damage in a format that includes urgency."

The feedback loop creates consciousness-like behavior:
    High-D state → Compress → Summary → Feed back → High-D state → ...

This isn't "adding consciousness"—it's making explicit the compression
that was already implicit, and closing the loop.
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

import logging
import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

from config.cognitive_parameters import DEFAULT_COGNITIVE_PARAMS as _PARAMS

if TYPE_CHECKING:
    from engines.cognition.blackboard import Blackboard

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class Valence(Enum):
    """
    Core felt quality of current state.

    This is NOT metadata about the state—it IS the state compressed
    to include urgency/valence in the representation itself.
    """
    THREAT = "threat"           # Something is wrong, act NOW
    OPPORTUNITY = "opportunity" # Something is possible, explore
    STABILITY = "stability"     # All is well, continue
    CONFUSION = "confusion"     # Don't understand, pause/gather
    BOREDOM = "boredom"         # Nothing happening, seek novelty


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class FeltState:
    """
    Low-dimensional compression of full system state.

    This is NOT metadata about the state—it IS the state,
    in a format that includes urgency and valence.

    Like pain encoding "STOP" in the representation itself,
    not "damage data" + separate "urgency lookup".

    5 core dimensions compress 100+ blackboard slots:
    - valence: Overall felt quality (discrete)
    - arousal: Energy/activation level (0-1)
    - certainty: How confident are we (0-1)
    - agency: Do we feel in control (0-1)
    - salience: How attention-grabbing (0-1)
    """
    # Core dimensions (5D summary of 100+D state)
    valence: Valence              # Overall felt quality
    arousal: float                # 0-1: energy/activation level
    certainty: float              # 0-1: how confident are we
    agency: float                 # 0-1: do we feel in control
    salience: float               # 0-1: how attention-grabbing

    # Temporal dimension
    momentum: float               # -1 to 1: getting better or worse

    # Compression metadata
    compression_ratio: float      # How much info was lost (higher = more loss)
    dominant_contributors: List[str] = field(default_factory=list)

    def to_urgency_bias(self) -> float:
        """
        Convert felt state to urgency bias for Eisenhower layer.

        THREAT + high arousal = high urgency
        STABILITY + low arousal = low urgency
        """
        valence_urgency = {
            Valence.THREAT: 0.8,
            Valence.CONFUSION: 0.5,
            Valence.OPPORTUNITY: 0.3,
            Valence.STABILITY: 0.1,
            Valence.BOREDOM: 0.0,
        }
        base = valence_urgency[self.valence]
        return base * self.arousal

    def to_importance_bias(self) -> float:
        """
        Convert felt state to importance bias for Eisenhower layer.

        High certainty + high agency = exploit (important)
        Low certainty + high salience = investigate (important)
        """
        if self.certainty > _PARAMS.phenomenology_certainty_high and self.agency > _PARAMS.phenomenology_agency_high:
            return 0.8  # We know what to do and can do it
        if self.certainty < _PARAMS.phenomenology_certainty_low and self.salience > _PARAMS.phenomenology_salience_high:
            return 0.7  # We don't know, but this matters
        if self.momentum < _PARAMS.phenomenology_momentum_negative:
            return 0.6  # Things are getting worse
        return 0.4  # Default moderate importance

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/storage."""
        return {
            'valence': self.valence.value,
            'arousal': self.arousal,
            'certainty': self.certainty,
            'agency': self.agency,
            'salience': self.salience,
            'momentum': self.momentum,
            'compression_ratio': self.compression_ratio,
            'dominant_contributors': self.dominant_contributors,
        }

    def __repr__(self) -> str:
        return (
            f"FeltState({self.valence.value}, "
            f"A={self.arousal:.2f}, C={self.certainty:.2f}, "
            f"Ag={self.agency:.2f}, S={self.salience:.2f}, "
            f"M={self.momentum:+.2f})"
        )


@dataclass
class FeltStateTraceEntry:
    """
    Debug trace entry for 'why did it feel this way?'

    Essential for debugging phenomenology decisions and understanding
    why the system felt THREAT vs STABILITY in a given situation.
    """
    tick: int
    felt_state: FeltState
    raw_valence_score: float
    dominant_contributors: List[str]
    blackboard_snapshot: Dict[str, Any]
    timestamp_ms: float = field(default_factory=lambda: time.time() * 1000)

    def explain(self) -> str:
        """Human-readable explanation of this felt state."""
        return (
            f"Tick {self.tick}: Felt {self.felt_state.valence.value} because: "
            f"{', '.join(self.dominant_contributors)}. "
            f"Raw score: {self.raw_valence_score:.2f}, "
            f"Certainty: {self.felt_state.certainty:.2f}, "
            f"Agency: {self.felt_state.agency:.2f}"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'tick': self.tick,
            'felt_state': self.felt_state.to_dict(),
            'raw_valence_score': self.raw_valence_score,
            'dominant_contributors': self.dominant_contributors,
            'blackboard_snapshot': self.blackboard_snapshot,
            'timestamp_ms': self.timestamp_ms,
        }


# =============================================================================
# STABILIZER (Hysteresis for Valence Transitions)
# =============================================================================

class FeltStateStabilizer:
    """
    Prevents FeltState thrashing (THREAT→STABILITY→THREAT oscillation).

    Uses confirmation counts and cooldowns, similar to epistemic hysteresis
    in the Rumsfeld layer.

    Key transitions and their confirmation requirements:
    - STABILITY → THREAT: Need 2 signals (don't panic too easily)
    - THREAT → STABILITY: Need 3 signals (don't calm down too fast)
    - BOREDOM → THREAT: Need 1 signal (instant panic from boredom)
    """

    # Confirmation required before transition
    VALENCE_CONFIRMATION_REQUIRED: Dict[tuple, int] = {
        (Valence.STABILITY, Valence.THREAT): 2,    # Need 2 signals before panic
        (Valence.THREAT, Valence.STABILITY): 3,    # Need 3 signals to calm down
        (Valence.CONFUSION, Valence.STABILITY): 2, # Need 2 signals to feel stable
        (Valence.BOREDOM, Valence.THREAT): 1,      # Instant panic from boredom
        (Valence.STABILITY, Valence.CONFUSION): 2, # Don't get confused too easily
        (Valence.OPPORTUNITY, Valence.THREAT): 2,  # Don't panic when exploring
    }

    # Cooldown after transition (cycles before can transition again) - from CognitiveParameters
    TRANSITION_COOLDOWN: int = _PARAMS.phenomenology_transition_cooldown

    def __init__(self):
        self.pending_valence: Optional[Valence] = None
        self.confirmation_count: int = 0
        self.cooldown_remaining: int = 0

        # Statistics
        self.stats = {
            'transitions_blocked': 0,
            'transitions_allowed': 0,
            'cooldowns_enforced': 0,
        }

    def stabilize(self, raw_felt: FeltState,
                  previous_felt: Optional[FeltState]) -> FeltState:
        """
        Apply hysteresis to prevent thrashing.

        Args:
            raw_felt: The freshly computed FeltState
            previous_felt: The previous cycle's FeltState

        Returns:
            Stabilized FeltState (may have different valence than raw_felt)
        """
        if previous_felt is None:
            return raw_felt

        # Decrement cooldown
        if self.cooldown_remaining > 0:
            self.cooldown_remaining -= 1
            self.stats['cooldowns_enforced'] += 1
            # Force previous valence during cooldown
            return FeltState(
                valence=previous_felt.valence,
                arousal=raw_felt.arousal,
                certainty=raw_felt.certainty,
                agency=raw_felt.agency,
                salience=raw_felt.salience,
                momentum=raw_felt.momentum,
                compression_ratio=raw_felt.compression_ratio,
                dominant_contributors=raw_felt.dominant_contributors,
            )

        # Check if valence is trying to change
        if raw_felt.valence != previous_felt.valence:
            transition = (previous_felt.valence, raw_felt.valence)
            required = self.VALENCE_CONFIRMATION_REQUIRED.get(transition, 1)

            if self.pending_valence == raw_felt.valence:
                self.confirmation_count += 1
            else:
                self.pending_valence = raw_felt.valence
                self.confirmation_count = 1

            if self.confirmation_count >= required:
                # Transition confirmed
                self.cooldown_remaining = self.TRANSITION_COOLDOWN
                self.pending_valence = None
                self.confirmation_count = 0
                self.stats['transitions_allowed'] += 1
                logger.debug(
                    "[PHENOMENOLOGY] Valence transition: %s -> %s (confirmed)",
                    previous_felt.valence.value, raw_felt.valence.value
                )
                return raw_felt
            else:
                # Not enough confirmations, keep previous valence
                self.stats['transitions_blocked'] += 1
                return FeltState(
                    valence=previous_felt.valence,
                    arousal=raw_felt.arousal,
                    certainty=raw_felt.certainty,
                    agency=raw_felt.agency,
                    salience=raw_felt.salience,
                    momentum=raw_felt.momentum,
                    compression_ratio=raw_felt.compression_ratio,
                    dominant_contributors=raw_felt.dominant_contributors,
                )

        # No change
        self.pending_valence = None
        self.confirmation_count = 0
        return raw_felt

    def reset(self) -> None:
        """Reset stabilizer state for new game."""
        self.pending_valence = None
        self.confirmation_count = 0
        self.cooldown_remaining = 0


# =============================================================================
# ALGORITHM MODULATION
# =============================================================================

@dataclass
class AlgorithmModulation:
    """
    Modulation parameters based on FeltState.

    This is where 'feeling' becomes actionable—not just recorded,
    but used to change behavior.
    """
    algorithm_override: Optional[str] = None
    beam_width_multiplier: float = 1.0
    exploration_boost: float = 0.0
    exclusion_set: Set[str] = field(default_factory=set)
    confidence_threshold_adjustment: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            'algorithm_override': self.algorithm_override,
            'beam_width_multiplier': self.beam_width_multiplier,
            'exploration_boost': self.exploration_boost,
            'exclusion_set': list(self.exclusion_set),
            'confidence_threshold_adjustment': self.confidence_threshold_adjustment,
        }


# =============================================================================
# PHENOMENOLOGY LAYER
# =============================================================================

class PhenomenologyLayer:
    """
    Explicit compression layer that:
    1. Compresses full blackboard to FeltState (5D)
    2. Injects FeltState back into blackboard for next cycle
    3. Uses valence-tagged priorities in the encoding itself

    This creates the feedback loop that might be consciousness-like:
        High-D state → Compress → Summary → Feed back → High-D state → ...
    """

    # Performance budget: compression must complete in time limit
    MAX_COMPRESSION_MS: float = _PARAMS.phenomenology_compression_budget_ms

    # History size limits - from CognitiveParameters
    MAX_HISTORY: int = _PARAMS.phenomenology_max_history
    MAX_TRACE_LOG: int = _PARAMS.phenomenology_max_trace_log

    def __init__(self, blackboard: 'Blackboard'):
        """
        Initialize phenomenology layer with blackboard reference.

        Args:
            blackboard: The shared blackboard for reading/writing state
        """
        self.blackboard = blackboard
        self.previous_felt: Optional[FeltState] = None
        self.history: List[FeltState] = []
        self.stabilizer = FeltStateStabilizer()
        self.trace_log: List[FeltStateTraceEntry] = []

        # Statistics
        self.stats = {
            'compressions': 0,
            'injections': 0,
            'slow_compressions': 0,
            'cold_starts': 0,
        }

    # =========================================================================
    # COMPRESSION (High-D → 5D)
    # =========================================================================

    def compress(self) -> FeltState:
        """
        Compress full blackboard state to 5D FeltState.

        This is lossy BY DESIGN. The ineffability of experience
        is the information loss in this compression.

        Returns:
            FeltState representing compressed current state
        """
        start = time.perf_counter()
        self.stats['compressions'] += 1

        # COLD START: First cycle has no previous state
        if self.previous_felt is None:
            self.stats['cold_starts'] += 1
            felt = FeltState(
                valence=Valence.CONFUSION,  # Don't know anything yet
                arousal=0.5,
                certainty=0.2,
                agency=0.3,
                salience=0.7,  # Everything is novel
                momentum=0.0,
                compression_ratio=0.0,
                dominant_contributors=['cold_start'],
            )
            self._log_trace(felt, 0.0)
            return felt

        # Compute all dimensions
        valence = self._compute_valence()
        arousal = self._compute_arousal()
        certainty = self._compute_certainty()
        agency = self._compute_agency()
        salience = self._compute_salience()
        momentum = self._compute_momentum()
        contributors = self._get_dominant_contributors()

        # Estimate compression ratio
        slots_with_data = self._count_active_slots()
        compression_ratio = slots_with_data / 5.0  # 5 output dimensions

        raw_felt = FeltState(
            valence=valence,
            arousal=arousal,
            certainty=certainty,
            agency=agency,
            salience=salience,
            momentum=momentum,
            compression_ratio=compression_ratio,
            dominant_contributors=contributors,
        )

        # Apply hysteresis to prevent valence thrashing
        felt = self.stabilizer.stabilize(raw_felt, self.previous_felt)

        # Performance guard
        elapsed_ms = (time.perf_counter() - start) * 1000
        if elapsed_ms > self.MAX_COMPRESSION_MS:
            self.stats['slow_compressions'] += 1
            logger.warning(
                "[PHENOMENOLOGY] Slow compression: %.2fms (limit: %.2fms)",
                elapsed_ms, self.MAX_COMPRESSION_MS
            )

        # Log trace for debugging
        raw_score = self._compute_raw_valence_score()
        self._log_trace(felt, raw_score)

        return felt

    def _count_active_slots(self) -> int:
        """Count blackboard slots with non-None values."""
        count = 0
        # Use blackboard's get method to check known slots
        known_slots = [
            'epistemic_quadrant', 'working_theory', 'controlled_object',
            'contradiction_detected', 'cascade_failure', 'action_budget_critical',
            'frame_delta_magnitude', 'strategy_stability', 'recent_success_rate',
            'novelty_score', 'surprise_score', 'pattern_break', 'stuck_detected',
            'levels_completed', 'total_levels', 'death_count', 'no_change_frames',
        ]
        for slot in known_slots:
            if self.blackboard.get(slot) is not None:
                count += 1
        return count

    # =========================================================================
    # VALENCE COMPUTATION
    # =========================================================================

    def _compute_valence(self) -> Valence:
        """
        Determine overall felt quality.

        Uses a composite score approach that considers multiple signals,
        then maps to discrete Valence category.
        """
        # Compute raw valence score (continuous -1 to 1)
        raw_score = self._compute_raw_valence_score()

        # THREAT signals override score
        if self.blackboard.get('contradiction_detected', False):
            return Valence.THREAT
        if self.blackboard.get('cascade_failure', False):
            return Valence.THREAT
        if self.blackboard.get('action_budget_critical', False):
            return Valence.THREAT

        # Score-based mapping - uses CognitiveParameters thresholds
        if raw_score < _PARAMS.phenomenology_valence_threat_threshold:
            return Valence.THREAT
        elif raw_score < _PARAMS.phenomenology_confusion_threshold:
            # Between threat (-0.3) and confusion (-0.1) = CONFUSION
            return Valence.CONFUSION
        elif raw_score > _PARAMS.phenomenology_valence_opportunity_threshold:
            return Valence.OPPORTUNITY

        # Middle range: use discrete signals as tie-breakers
        # BOREDOM signals
        if self.blackboard.get('no_change_frames', 0) > 10:
            return Valence.BOREDOM

        # Default
        return Valence.STABILITY

    def _compute_raw_valence_score(self) -> float:
        """
        Compute continuous valence score from multiple signals.
        Uses tanh squashing for bounded output.

        CRITICAL: Balances internal signals (confidence, agency) with
        external validation (score changes, action success, deaths) to
        prevent "feeling good while losing" - per LLM architecture feedback.

        Returns:
            Score in range [-1, 1]
        """
        # ===== INTERNAL SIGNALS (what we "feel") =====
        # Confidence trend from our own reasoning
        confidence_trend = self.blackboard.get('confidence_delta', 0)

        # Agency - how much we feel in control
        # Dead-signal fix: 'agency_score' was a phantom read (never written).
        # Use _compute_agency() which reads real blackboard signals
        # (controlled_object, working_theory, recent_success_rate).
        agency = self._compute_agency()

        # Certainty from epistemic state
        epistemic = self.blackboard.get('epistemic_quadrant', 'UU')
        certainty_map = {'KK': 0.9, 'KU': 0.5, 'UK': 0.6, 'UU': 0.2}
        certainty = certainty_map.get(epistemic, 0.5)

        # Internal score: confidence + agency + certainty
        internal_score = (confidence_trend + agency + certainty) / 3

        # ===== EXTERNAL SIGNALS (reality check) =====
        # Actual game progress
        levels_completed = self.blackboard.get('levels_completed', 0)
        total_levels = max(self.blackboard.get('total_levels', 1), 1)
        progress = levels_completed / total_levels

        # Score delta - did our score actually improve?
        score_delta = self.blackboard.get('score_delta', 0)
        # Normalize to reasonable range (assuming scores change by 0-100 typically)
        score_change = max(min(score_delta / 100, 1.0), -1.0)

        # Action success rate - are our actions working?
        action_success_rate = self.blackboard.get('recent_success_rate', 0.5)

        # Death count - external failure signal
        death_count = self.blackboard.get('death_count', 0)
        death_penalty = death_count * _PARAMS.valence_death_penalty_weight

        # Known unknowns - contradictions found
        known_unknowns = self.blackboard.get('known_unknowns', [])
        contradiction_count = len(known_unknowns) if isinstance(known_unknowns, list) else 0
        contradictions = contradiction_count * -0.1

        # Stuck detection
        stuck_penalty = -0.3 if self.blackboard.get('stuck_detected') else 0

        # External score: progress + score_change + action_success - penalties
        external_score = (
            progress * _PARAMS.valence_progress_weight +
            score_change * _PARAMS.valence_score_delta_weight +
            action_success_rate * _PARAMS.valence_action_success_weight +
            death_penalty +
            contradictions +
            stuck_penalty
        )

        # ===== WEIGHTED COMBINATION =====
        # This prevents "feeling good while losing" by requiring external validation
        raw = (
            internal_score * _PARAMS.valence_internal_weight +
            external_score * _PARAMS.valence_external_weight
        )

        return math.tanh(raw)  # Squash to [-1, 1]

    # =========================================================================
    # OTHER DIMENSION COMPUTATION
    # =========================================================================

    def _compute_arousal(self) -> float:
        """Compute energy/activation level (0-1)."""
        signals = [
            self.blackboard.get('frame_delta_magnitude', 0) / 100,
            len(self.blackboard.get('open_questions', [])) / 10,
            1.0 - self.blackboard.get('strategy_stability', 1.0),
        ]
        return min(sum(signals) / len(signals), 1.0)

    def _compute_certainty(self) -> float:
        """Compute confidence level from epistemic state (0-1)."""
        quadrant_certainty = {
            'KK': 0.9,
            'KU': 0.5,  # We know what we don't know
            'UK': 0.6,  # We have knowledge we're not using
            'UU': 0.2,
        }
        epistemic = self.blackboard.get('epistemic_quadrant', 'UU')
        base = quadrant_certainty.get(epistemic, 0.5)

        # Adjust by recent success rate
        recent_success = self.blackboard.get('recent_success_rate', 0.5)
        return base * 0.7 + recent_success * 0.3

    def _compute_agency(self) -> float:
        """Compute sense of control (0-1)."""
        has_control = self.blackboard.get('controlled_object') is not None
        has_theory = self.blackboard.get('working_theory') is not None
        actions_work = self.blackboard.get('recent_success_rate', 0.5) > 0.5

        return (
            0.4 * float(has_control) +
            0.3 * float(has_theory) +
            0.3 * float(actions_work)
        )

    def _compute_salience(self) -> float:
        """Compute attention-grabbing level (0-1)."""
        return min(
            self.blackboard.get('novelty_score', 0) +
            self.blackboard.get('surprise_score', 0) +
            (0.5 if self.blackboard.get('pattern_break', False) else 0),
            1.0
        )

    def _compute_momentum(self) -> float:
        """Compute whether things are getting better or worse (-1 to 1)."""
        if len(self.history) < 2:
            return 0.0

        recent = self.history[-5:] if len(self.history) >= 5 else self.history

        certainty_trend = recent[-1].certainty - recent[0].certainty
        agency_trend = recent[-1].agency - recent[0].agency

        # Valence transitions
        valence_score = {
            Valence.STABILITY: 0,
            Valence.OPPORTUNITY: 0.3,
            Valence.CONFUSION: -0.3,
            Valence.THREAT: -0.5,
            Valence.BOREDOM: -0.2,
        }
        valence_momentum = (
            valence_score[recent[-1].valence] -
            valence_score[recent[0].valence]
        )

        return max(-1.0, min(1.0, (certainty_trend + agency_trend + valence_momentum) / 3))

    def _get_dominant_contributors(self) -> List[str]:
        """Identify which blackboard slots dominated the compression."""
        contributors = []

        if self.blackboard.get('contradiction_detected', False):
            contributors.append('contradiction_detected')
        if self.blackboard.get('cascade_failure', False):
            contributors.append('cascade_failure')
        if self.blackboard.get('action_budget_critical', False):
            contributors.append('action_budget_critical')
        if self.blackboard.get('epistemic_quadrant'):
            contributors.append('epistemic_quadrant')
        if self.blackboard.get('controlled_object'):
            contributors.append('controlled_object')
        if self.blackboard.get('working_theory'):
            contributors.append('working_theory')
        if self.blackboard.get('stuck_detected'):
            contributors.append('stuck_detected')

        return contributors[:5]  # Top 5

    # =========================================================================
    # INJECTION (Feed back into blackboard)
    # =========================================================================

    def inject(self, felt: FeltState) -> None:
        """
        Feed compressed state back into blackboard.

        This closes the loop: the system's compressed self-perception
        influences its next cycle of processing.

        Args:
            felt: The FeltState to inject
        """
        self.stats['injections'] += 1

        # Store as "felt_*" slots that rungs can read
        # Using slot() method which is Blackboard's core write API
        self.blackboard.slot('felt_valence', felt.valence.value, source_rung='phenomenology')
        self.blackboard.slot('felt_arousal', felt.arousal, source_rung='phenomenology')
        self.blackboard.slot('felt_certainty', felt.certainty, source_rung='phenomenology')
        self.blackboard.slot('felt_agency', felt.agency, source_rung='phenomenology')
        self.blackboard.slot('felt_salience', felt.salience, source_rung='phenomenology')
        self.blackboard.slot('felt_momentum', felt.momentum, source_rung='phenomenology')

        # Store urgency/importance biases for Eisenhower layer
        self.blackboard.slot('felt_urgency_bias', felt.to_urgency_bias(), source_rung='phenomenology')
        self.blackboard.slot('felt_importance_bias', felt.to_importance_bias(), source_rung='phenomenology')

        # Store in history for momentum calculation
        self.history.append(felt)
        if len(self.history) > self.MAX_HISTORY:
            self.history = self.history[-self.MAX_HISTORY:]

        self.previous_felt = felt

    # =========================================================================
    # ALGORITHM MODULATION
    # =========================================================================

    def get_algorithm_modulation(self, felt: FeltState) -> AlgorithmModulation:
        """
        Let phenomenological state influence algorithm choice.

        This is where 'feeling' becomes actionable—not just recorded,
        but used to change behavior.

        Args:
            felt: Current FeltState

        Returns:
            AlgorithmModulation with parameters to apply
        """
        modulation = AlgorithmModulation()

        # PANIC MODE: High arousal + low agency
        # Use faster, more conservative algorithm
        if felt.arousal > 0.8 and felt.agency < 0.3:
            modulation.algorithm_override = 'beam_search'
            modulation.beam_width_multiplier = 0.5  # Narrow beam, fast
            logger.debug("[PHENOMENOLOGY] PANIC MODE: narrow beam search")
            return modulation

        # CONFIDENT BUT UNHAPPY: THREAT + high certainty
        # Something's wrong with our approach, try different path
        if felt.valence == Valence.THREAT and felt.certainty > 0.7:
            recent_path = self.blackboard.get('recent_path', [])
            if recent_path:
                modulation.exclusion_set = set(recent_path)
            modulation.exploration_boost = 0.3
            logger.debug("[PHENOMENOLOGY] Confident but threatened: excluding recent path")
            return modulation

        # BORED: Nothing happening, seek novelty
        if felt.valence == Valence.BOREDOM:
            modulation.exploration_boost = 0.5
            logger.debug("[PHENOMENOLOGY] BORED: boosting exploration")
            return modulation

        # HIGH SALIENCE: Something important happening
        # Don't rush, pay attention
        if felt.salience > 0.8:
            modulation.beam_width_multiplier = 1.5  # Wider search
            logger.debug("[PHENOMENOLOGY] High salience: widening search")
            return modulation

        # CONFUSED: Lower confidence threshold
        if felt.valence == Valence.CONFUSION:
            modulation.confidence_threshold_adjustment = -0.1
            logger.debug("[PHENOMENOLOGY] Confused: lowering confidence threshold")
            return modulation

        return modulation

    # =========================================================================
    # TRACE LOGGING
    # =========================================================================

    def _log_trace(self, felt: FeltState, raw_score: float) -> None:
        """Log trace entry for debugging 'why did it feel this way?'"""
        entry = FeltStateTraceEntry(
            tick=self.blackboard.get('current_tick', 0),
            felt_state=felt,
            raw_valence_score=raw_score,
            dominant_contributors=felt.dominant_contributors,
            blackboard_snapshot={
                'epistemic_quadrant': self.blackboard.get('epistemic_quadrant'),
                'contradiction_detected': self.blackboard.get('contradiction_detected'),
                'controlled_object': self.blackboard.get('controlled_object') is not None,
                'working_theory': self.blackboard.get('working_theory') is not None,
                'action_budget_critical': self.blackboard.get('action_budget_critical'),
                'no_change_frames': self.blackboard.get('no_change_frames', 0),
            }
        )
        self.trace_log.append(entry)
        if len(self.trace_log) > self.MAX_TRACE_LOG:
            self.trace_log = self.trace_log[-self.MAX_TRACE_LOG:]

    def get_recent_traces(self, count: int = 10) -> List[FeltStateTraceEntry]:
        """Get recent trace entries for debugging."""
        return self.trace_log[-count:]

    def explain_current_state(self) -> str:
        """Get human-readable explanation of current felt state."""
        if not self.trace_log:
            return "No trace log available"
        return self.trace_log[-1].explain()

    # =========================================================================
    # STATISTICS / DEBUG
    # =========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for monitoring."""
        return {
            **self.stats,
            'history_size': len(self.history),
            'trace_log_size': len(self.trace_log),
            'stabilizer_stats': self.stabilizer.stats.copy(),
            'current_valence': self.previous_felt.valence.value if self.previous_felt else None,
        }

    def reset(self) -> None:
        """Reset for new game."""
        self.previous_felt = None
        self.history.clear()
        self.stabilizer.reset()
        self.trace_log.clear()
        self.stats = {
            'compressions': 0,
            'injections': 0,
            'slow_compressions': 0,
            'cold_starts': 0,
        }
