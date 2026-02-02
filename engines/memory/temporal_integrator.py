"""
Temporal Integrator - Multi-Scale Exponential Integration of Agent Experience

Implements continuous integration of outcomes with exponential decay at multiple
timescales. Different decay windows create different temporal scopes of influence,
all operating on the same underlying data stream.

Time Model:
    Generation = "Big TIME" - the fundamental macro unit
    Action = micro unit within generation

    Composite time: t = generation + (action_in_gen / max_actions_per_gen)

    This makes the system hardware-agnostic:
    - Fast computer: generation = 10 seconds wall-clock
    - Slow computer: generation = 10 hours wall-clock
    - Software doesn't change - only generation count matters

Mathematical Model:
    For state variable S at composite time t:

    S(t) = sum_{i=0}^{t} outcome_i * exp(-lambda * (t - i))

    Where lambda = ln(2) / half_life determines decay rate.

    Different lambda values create different temporal windows:
    - Immediate (0.1 gen):  Session behavior, exploration appetite
    - Tactical (1.0 gen):   Game-level strategy
    - Strategic (10 gen):   Agent personality evolution
    - Historical (inf):     Network wisdom (no decay)

Neurological Basis:
    This mirrors biological calcium dynamics in astrocytes:
    - Accumulate signal over time
    - Decay when input stops
    - Threshold crossing triggers state change

    The "give up" behavior emerges when integral crosses threshold,
    not from explicit state machines or counters.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


@dataclass
class TemporalWindow:
    """Configuration for a temporal integration window."""
    name: str
    half_life_generations: float  # Half-life in generation units
    description: str

    @property
    def decay_rate(self) -> float:
        """Lambda value for exponential decay: ln(2) / half_life"""
        if self.half_life_generations <= 0:
            return 0.0  # No decay (infinite half-life)
        return math.log(2) / self.half_life_generations


# Standard temporal windows - all measured in generations
TEMPORAL_WINDOWS = {
    'immediate': TemporalWindow(
        name='immediate',
        half_life_generations=0.1,  # ~10% of a generation
        description='Session behavior, exploration appetite'
    ),
    'tactical': TemporalWindow(
        name='tactical',
        half_life_generations=1.0,  # 1 generation
        description='Game-level strategy selection'
    ),
    'strategic': TemporalWindow(
        name='strategic',
        half_life_generations=10.0,  # 10 generations
        description='Agent personality, w_A/w_B evolution'
    ),
    'historical': TemporalWindow(
        name='historical',
        half_life_generations=0.0,  # Infinite (no decay)
        description='Network wisdom, permanent knowledge'
    ),
}


class TemporalIntegrator:
    """
    Multi-scale exponential integration of agent experience.

    Replaces discrete state machines with continuous decay windows.
    The same outcome stream feeds all timescales simultaneously.

    All time is measured in generations (Big TIME), making the system
    completely hardware-agnostic. Whether a generation takes 10 seconds
    or 10 hours of wall-clock time, the decay mathematics work identically.

    Usage:
        integrator = TemporalIntegrator(db)

        # After each action outcome
        integrator.record_outcome(
            agent_id='agent_001',
            game_type='SP80',
            generation=42,
            action_in_generation=150,
            outcome_value=0.5  # Positive outcome
        )

        # Get current exploration appetite
        appetite = integrator.get_exploration_appetite(
            agent_id='agent_001',
            game_type='SP80',
            current_generation=42,
            current_action=175
        )

        # Get rung priority modulation
        modulation = integrator.get_rung_modulation(...)
    """

    def __init__(
        self,
        db: Optional["DatabaseInterface"] = None,
        max_actions_per_generation: int = 10000,
        windows: Optional[Dict[str, TemporalWindow]] = None
    ):
        """
        Initialize temporal integrator.

        Args:
            db: Database interface for persistence (optional for in-memory only)
            max_actions_per_generation: Normalizer for action count within generation
            windows: Custom temporal windows (uses defaults if None)
        """
        self.db = db
        self.max_actions_per_generation = max_actions_per_generation
        self.windows = windows or TEMPORAL_WINDOWS.copy()

        # In-memory buffer for current generation (flushed at generation end)
        # Structure: {(agent_id, game_type): [(composite_time, outcome_value), ...]}
        self._outcome_buffer: Dict[Tuple[str, str], List[Tuple[float, float]]] = {}

        # Cache for computed integrals (invalidated on new outcomes)
        self._integral_cache: Dict[Tuple[str, str, str, float], float] = {}

    def _composite_time(self, generation: int, action_in_generation: int) -> float:
        """
        Convert generation + action to composite time.

        Composite time = generation + (action / max_actions)

        This creates a continuous timeline where:
        - Generation 0, action 0 = 0.0
        - Generation 0, action 5000 (half) = 0.5
        - Generation 1, action 0 = 1.0
        - Generation 10, action 2500 = 10.25
        """
        return generation + (action_in_generation / self.max_actions_per_generation)

    def record_outcome(
        self,
        agent_id: str,
        game_type: str,
        generation: int,
        action_in_generation: int,
        outcome_value: float,
        persist: bool = False
    ) -> None:
        """
        Record an outcome for temporal integration.

        Args:
            agent_id: Agent identifier
            game_type: Game type identifier
            generation: Current generation number (Big TIME)
            action_in_generation: Action count within this generation
            outcome_value: Signed outcome (-1 to +1 typical)
                          +1 = strong positive (score increase, level complete)
                          0 = neutral (no change)
                          -1 = strong negative (death, score decrease)
            persist: If True, write to database immediately
        """
        composite_t = self._composite_time(generation, action_in_generation)
        key = (agent_id, game_type)

        if key not in self._outcome_buffer:
            self._outcome_buffer[key] = []

        self._outcome_buffer[key].append((composite_t, outcome_value))

        # Invalidate cache for this agent/game
        self._invalidate_cache(agent_id, game_type)

        # Optional immediate persistence
        if persist and self.db is not None:
            self._persist_outcome(agent_id, game_type, generation, action_in_generation, outcome_value)

    def _invalidate_cache(self, agent_id: str, game_type: str) -> None:
        """Invalidate cached integrals for this agent/game."""
        keys_to_remove = [
            k for k in self._integral_cache
            if k[0] == agent_id and k[1] == game_type
        ]
        for k in keys_to_remove:
            del self._integral_cache[k]

    def _persist_outcome(
        self,
        agent_id: str,
        game_type: str,
        generation: int,
        action_in_generation: int,
        outcome_value: float
    ) -> None:
        """Persist outcome to database for historical queries."""
        if self.db is None:
            return

        try:
            self.db.execute_update("""
                INSERT INTO temporal_outcomes
                (agent_id, game_type, generation, action_in_generation, outcome_value, composite_time)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                agent_id, game_type, generation, action_in_generation,
                outcome_value, self._composite_time(generation, action_in_generation)
            ))
        except Exception as e:
            # Table might not exist yet - that's OK, buffer still works
            logger.debug(f"[TEMPORAL] Persist failed (table may not exist): {e}")

    def get_integrated_state(
        self,
        agent_id: str,
        game_type: str,
        current_generation: int,
        current_action: int,
        window: str = 'immediate'
    ) -> float:
        """
        Compute exponentially-weighted integral of recent outcomes.

        Args:
            agent_id: Agent identifier
            game_type: Game type (or '*' for all games)
            current_generation: Current generation (Big TIME)
            current_action: Current action within generation
            window: Temporal window name ('immediate', 'tactical', 'strategic')

        Returns:
            Normalized value in [-1, 1] range:
            - Negative: Recent experience predominantly negative
            - Zero: Balanced or no data
            - Positive: Recent experience predominantly positive
        """
        current_t = self._composite_time(current_generation, current_action)
        cache_key = (agent_id, game_type, window, current_t)

        # Check cache
        if cache_key in self._integral_cache:
            return self._integral_cache[cache_key]

        window_config = self.windows.get(window)
        if window_config is None:
            logger.warning(f"[TEMPORAL] Unknown window '{window}', using immediate")
            window_config = self.windows['immediate']

        # Collect outcomes from buffer
        key = (agent_id, game_type)
        outcomes = self._outcome_buffer.get(key, [])

        # Also query database for historical data if available and window is long enough
        if self.db is not None and window_config.half_life_generations >= 1.0:
            db_outcomes = self._query_historical_outcomes(
                agent_id, game_type, current_t, window_config
            )
            outcomes = db_outcomes + outcomes

        if not outcomes:
            return 0.0

        # Compute exponentially-weighted integral
        weighted_sum = 0.0
        weight_total = 0.0
        decay_rate = window_config.decay_rate

        # Limit lookback to 5 half-lives (captures 97% of signal)
        lookback_limit = current_t - (5 * window_config.half_life_generations) if decay_rate > 0 else 0

        for outcome_t, outcome_value in outcomes:
            if outcome_t > current_t:
                continue  # Future outcome (shouldn't happen)
            if decay_rate > 0 and outcome_t < lookback_limit:
                continue  # Too old to matter

            age = current_t - outcome_t

            if decay_rate > 0:
                weight = math.exp(-decay_rate * age)
            else:
                weight = 1.0  # No decay (historical window)

            weighted_sum += outcome_value * weight
            weight_total += weight

        # Normalize to [-1, 1]
        if weight_total > 0:
            result = weighted_sum / weight_total
        else:
            result = 0.0

        # Clamp to valid range
        result = max(-1.0, min(1.0, result))

        # Cache result
        self._integral_cache[cache_key] = result

        return result

    def _query_historical_outcomes(
        self,
        agent_id: str,
        game_type: str,
        current_t: float,
        window_config: TemporalWindow
    ) -> List[Tuple[float, float]]:
        """Query database for historical outcomes within window."""
        if self.db is None:
            return []

        try:
            lookback = 5 * window_config.half_life_generations if window_config.decay_rate > 0 else 100
            min_t = current_t - lookback

            if game_type == '*':
                results = self.db.execute_query("""
                    SELECT composite_time, outcome_value
                    FROM temporal_outcomes
                    WHERE agent_id = ? AND composite_time >= ? AND composite_time <= ?
                    ORDER BY composite_time DESC
                    LIMIT 1000
                """, (agent_id, min_t, current_t))
            else:
                results = self.db.execute_query("""
                    SELECT composite_time, outcome_value
                    FROM temporal_outcomes
                    WHERE agent_id = ? AND game_type = ?
                      AND composite_time >= ? AND composite_time <= ?
                    ORDER BY composite_time DESC
                    LIMIT 1000
                """, (agent_id, game_type, min_t, current_t))

            return [(r['composite_time'], r['outcome_value']) for r in results]
        except Exception as e:
            logger.debug(f"[TEMPORAL] Historical query failed: {e}")
            return []

    def get_exploration_appetite(
        self,
        agent_id: str,
        game_type: str,
        current_generation: int,
        current_action: int
    ) -> float:
        """
        Compute exploration appetite from immediate window.

        Maps integrated state to [0, 1] appetite:
        - 0.0: Suppress exploration (recent failures dominate)
        - 0.5: Neutral
        - 1.0: Encourage exploration (recent successes dominate)

        This is the "astrocyte function" - continuous integration that
        modulates behavior without explicit state machines.
        """
        state = self.get_integrated_state(
            agent_id, game_type, current_generation, current_action, 'immediate'
        )

        # Sigmoid mapping: state in [-1,1] -> appetite in [0,1]
        # Steepness factor of 3 gives reasonable sensitivity
        return 1.0 / (1.0 + math.exp(-3.0 * state))

    def get_rung_modulation(
        self,
        agent_id: str,
        game_type: str,
        current_generation: int,
        current_action: int
    ) -> Dict[str, float]:
        """
        Compute priority multipliers for rung categories.

        Returns dict mapping category names to multipliers:
        - 'exploration': Multiplier for exploration-category rungs
        - 'exploitation': Multiplier for exploitation-category rungs
        - 'safety': Multiplier for safety-category rungs

        COMPREHENSION-BASED MODULATION (preferred):
        If prediction data exists, uses comprehension confidence:
        - Low confidence → EXPLORE to understand
        - High confidence → EXPLOIT understanding

        FALLBACK (outcome-based) when no prediction data:
        - Struggling → EXPLORE (current approach not working)
        - Succeeding → EXPLOIT (keep doing what works)
        """
        # Try comprehension-based modulation first (if we have prediction data)
        key = (agent_id, game_type)
        has_prediction_data = (
            hasattr(self, '_confidence_buffer') and
            key in self._confidence_buffer and
            len(self._confidence_buffer[key]) > 5  # Need enough data
        )

        if has_prediction_data:
            return self.get_rung_modulation_v2(
                agent_id, game_type, current_generation, current_action
            )

        # Fallback: outcome-based modulation
        appetite = self.get_exploration_appetite(
            agent_id, game_type, current_generation, current_action
        )

        # OUTCOME-BASED FALLBACK:
        # Low appetite (struggling) = explore more, exploit less
        # High appetite (succeeding) = explore less, exploit more
        return {
            'exploration': 1.3 - appetite * 0.8,    # [0.5, 1.3] - HIGH when struggling
            'exploitation': 0.5 + appetite * 0.8,   # [0.5, 1.3] - HIGH when succeeding
            'safety': 1.0 + (0.5 - appetite) * 0.4, # [0.8, 1.2] - higher at extremes
            'metacognition': 1.0,                    # Always neutral
            'filter': 1.0,                           # Always neutral
        }

    def get_strategic_state(
        self,
        agent_id: str,
        current_generation: int,
        current_action: int
    ) -> Dict[str, float]:
        """
        Get strategic-level integration (personality timescale).

        Returns state across all games, useful for agent-level decisions
        like role transitions.
        """
        state = self.get_integrated_state(
            agent_id, '*', current_generation, current_action, 'strategic'
        )

        return {
            'overall_trajectory': state,
            'should_consider_role_change': abs(state) > 0.5,  # Strong signal either direction
            'network_alignment': (state + 1) / 2,  # Map to [0, 1] for w_B proxy
        }

    def flush_to_database(self, current_generation: int) -> None:
        """
        Flush in-memory buffer to database at generation end.

        Call this at the end of each generation to persist outcomes.
        Clears buffer after successful flush.
        """
        if self.db is None:
            return

        total_flushed = 0

        for (agent_id, game_type), outcomes in self._outcome_buffer.items():
            for composite_t, outcome_value in outcomes:
                # Decompose composite time back to generation + action
                gen = int(composite_t)
                action = int((composite_t - gen) * self.max_actions_per_generation)

                try:
                    self.db.execute_update("""
                        INSERT OR IGNORE INTO temporal_outcomes
                        (agent_id, game_type, generation, action_in_generation,
                         outcome_value, composite_time)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (agent_id, game_type, gen, action, outcome_value, composite_t))
                    total_flushed += 1
                except Exception as e:
                    logger.debug(f"[TEMPORAL] Flush failed: {e}")

        # Clear buffer after flush
        self._outcome_buffer.clear()
        self._integral_cache.clear()

        if total_flushed > 0:
            logger.debug(f"[TEMPORAL] Flushed {total_flushed} outcomes to database")

    def clear_buffer(self) -> None:
        """Clear in-memory buffer without persisting (for testing/reset)."""
        self._outcome_buffer.clear()
        self._integral_cache.clear()
        self._prediction_buffer.clear()
        self._confidence_cache.clear()

    # =========================================================================
    # PREDICTION-ERROR BASED CONFIDENCE SYSTEM
    # =========================================================================
    # The key insight: Confidence should be based on COMPREHENSION, not outcomes.
    # - Predicted success that succeeds → Confidence UP (I understand this)
    # - Predicted failure that fails → Confidence UP (I understand this)
    # - Surprised by success → Confidence DOWN (got lucky, don't know why)
    # - Surprised by failure → Confidence DOWN (my model is wrong)
    #
    # Confidence drives exploration vs exploitation:
    # - Low confidence → EXPLORE to understand
    # - High confidence → EXPLOIT understanding
    # =========================================================================

    def record_prediction(
        self,
        agent_id: str,
        game_type: str,
        generation: int,
        action_in_generation: int,
        predicted_outcome: float,
        prediction_confidence: float = 0.5
    ) -> None:
        """
        Record a prediction BEFORE taking an action.

        Args:
            agent_id: Agent identifier
            game_type: Game type identifier
            generation: Current generation (Big TIME)
            action_in_generation: Action count within generation
            predicted_outcome: Expected outcome [-1, 1]
                              +1 = expect success
                              0 = uncertain/neutral
                              -1 = expect failure
            prediction_confidence: How confident in this prediction [0, 1]
        """
        composite_t = self._composite_time(generation, action_in_generation)
        key = (agent_id, game_type)

        if not hasattr(self, '_prediction_buffer'):
            self._prediction_buffer: Dict[Tuple[str, str], List[Tuple[float, float, float]]] = {}

        if key not in self._prediction_buffer:
            self._prediction_buffer[key] = []

        self._prediction_buffer[key].append((composite_t, predicted_outcome, prediction_confidence))

    def record_outcome_with_prediction_error(
        self,
        agent_id: str,
        game_type: str,
        generation: int,
        action_in_generation: int,
        actual_outcome: float
    ) -> float:
        """
        Record outcome and compute prediction error.

        Returns the surprise value (prediction error magnitude).
        Updates comprehension confidence based on prediction accuracy.

        Args:
            agent_id: Agent identifier
            game_type: Game type identifier
            generation: Current generation
            action_in_generation: Action count
            actual_outcome: What actually happened [-1, 1]

        Returns:
            Surprise value [0, 1] where 0 = predicted correctly, 1 = completely wrong
        """
        composite_t = self._composite_time(generation, action_in_generation)
        key = (agent_id, game_type)

        # Get most recent prediction for this agent/game
        predicted_outcome = 0.0  # Default: no prediction (neutral)
        prediction_confidence = 0.0  # Default: not confident

        if hasattr(self, '_prediction_buffer') and key in self._prediction_buffer:
            predictions = self._prediction_buffer[key]
            # Find the prediction closest to this time
            if predictions:
                # Get latest prediction before or at this time
                valid_predictions = [(t, pred, conf) for t, pred, conf in predictions if t <= composite_t]
                if valid_predictions:
                    _, predicted_outcome, prediction_confidence = valid_predictions[-1]

        # Compute prediction error (surprise)
        # Error = |predicted - actual| weighted by prediction confidence
        raw_error = abs(predicted_outcome - actual_outcome)
        # Scale error by prediction confidence: if you weren't confident, being wrong is less surprising
        surprise = raw_error * prediction_confidence

        # Update comprehension confidence based on surprise
        # Low surprise = confidence UP, high surprise = confidence DOWN
        confidence_delta = (1.0 - surprise * 2.0) * 0.1  # Scale factor for gradual updates
        self._update_comprehension_confidence(agent_id, game_type, composite_t, confidence_delta)

        # Also record the raw outcome for backward compatibility
        self.record_outcome(agent_id, game_type, generation, action_in_generation, actual_outcome)

        return surprise

    def _update_comprehension_confidence(
        self,
        agent_id: str,
        game_type: str,
        composite_t: float,
        confidence_delta: float
    ) -> None:
        """Update comprehension confidence based on prediction accuracy."""
        if not hasattr(self, '_confidence_buffer'):
            self._confidence_buffer: Dict[Tuple[str, str], List[Tuple[float, float]]] = {}

        key = (agent_id, game_type)
        if key not in self._confidence_buffer:
            self._confidence_buffer[key] = []

        self._confidence_buffer[key].append((composite_t, confidence_delta))

        # Invalidate confidence cache
        if hasattr(self, '_confidence_cache'):
            keys_to_remove = [k for k in self._confidence_cache if k[0] == agent_id and k[1] == game_type]
            for k in keys_to_remove:
                del self._confidence_cache[k]

    def get_comprehension_confidence(
        self,
        agent_id: str,
        game_type: str,
        current_generation: int,
        current_action: int
    ) -> float:
        """
        Get current comprehension confidence for an agent on a game.

        This is NOT outcome-based - it's based on prediction accuracy.
        High confidence = "I understand how this game works"
        Low confidence = "I don't understand what's happening"

        Returns:
            Confidence value [0, 1] where:
            0.0 = No understanding (explore heavily)
            0.5 = Partial understanding
            1.0 = Full understanding (exploit knowledge)
        """
        current_t = self._composite_time(current_generation, current_action)

        if not hasattr(self, '_confidence_cache'):
            self._confidence_cache: Dict[Tuple[str, str, float], float] = {}

        cache_key = (agent_id, game_type, current_t)
        if cache_key in self._confidence_cache:
            return self._confidence_cache[cache_key]

        # Get confidence buffer
        if not hasattr(self, '_confidence_buffer'):
            self._confidence_buffer = {}

        key = (agent_id, game_type)
        deltas = self._confidence_buffer.get(key, [])

        if not deltas:
            # No data - start at 0.2 (low confidence, need to explore)
            return 0.2

        # Integrate confidence deltas with decay (tactical window)
        window_config = self.windows.get('tactical', self.windows['immediate'])
        decay_rate = window_config.decay_rate
        lookback_limit = current_t - (5 * window_config.half_life_generations) if decay_rate > 0 else 0

        weighted_sum = 0.0
        weight_total = 0.0

        for delta_t, delta_value in deltas:
            if delta_t > current_t:
                continue
            if decay_rate > 0 and delta_t < lookback_limit:
                continue

            age = current_t - delta_t
            weight = math.exp(-decay_rate * age) if decay_rate > 0 else 1.0

            weighted_sum += delta_value * weight
            weight_total += weight

        if weight_total > 0:
            # Confidence changes integrated over time, mapped to [0, 1]
            # Start at 0.2, can grow to 1.0 or shrink to 0.0
            base_confidence = 0.2
            confidence = base_confidence + weighted_sum
            confidence = max(0.0, min(1.0, confidence))
        else:
            confidence = 0.2  # Default starting confidence

        self._confidence_cache[cache_key] = confidence
        return confidence

    def get_rung_modulation_v2(
        self,
        agent_id: str,
        game_type: str,
        current_generation: int,
        current_action: int
    ) -> Dict[str, float]:
        """
        Compute rung modulation based on COMPREHENSION CONFIDENCE.

        This replaces the outcome-based modulation with understanding-based:
        - Low confidence (don't understand) → EXPLORE to learn
        - High confidence (understand well) → EXPLOIT that understanding

        Returns dict mapping category names to multipliers.
        """
        confidence = self.get_comprehension_confidence(
            agent_id, game_type, current_generation, current_action
        )

        # Also factor in recent outcome trajectory for safety
        appetite = self.get_exploration_appetite(
            agent_id, game_type, current_generation, current_action
        )

        # COMPREHENSION-BASED MODULATION:
        # Low confidence → explore more, exploit less
        # High confidence → exploit more, explore less
        return {
            # Exploration: HIGH when confidence LOW (need to understand)
            'exploration': 1.3 - confidence * 0.8,  # [0.5, 1.3] - boosted when confused

            # Exploitation: HIGH when confidence HIGH (can use understanding)
            'exploitation': 0.5 + confidence * 0.8,  # [0.5, 1.3] - boosted when confident

            # Safety: Boosted when EITHER extreme (very confident or very lost)
            # - Very lost: be careful, don't know what's dangerous
            # - Very confident but failing: something's wrong, be careful
            'safety': 1.0 + abs(confidence - 0.5) * 0.4 + (1.0 - appetite) * 0.3,

            # Metacognition: Always active (helps build understanding)
            'metacognition': 1.0,

            # Filters: Always active
            'filter': 1.0,
        }


# Module-level singleton
_default_integrator: Optional[TemporalIntegrator] = None


def get_temporal_integrator(db: Optional["DatabaseInterface"] = None) -> TemporalIntegrator:
    """Get or create the default TemporalIntegrator singleton."""
    global _default_integrator
    if _default_integrator is None:
        _default_integrator = TemporalIntegrator(db=db)
    elif db is not None and _default_integrator.db is None:
        _default_integrator.db = db
    return _default_integrator
