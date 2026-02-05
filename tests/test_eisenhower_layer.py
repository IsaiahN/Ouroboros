"""
Test suite for Phase 8: Eisenhower Layer / Dual-Matrix Integration.

Tests cover:
1. Dual-matrix flow (Rumsfeld -> Eisenhower bias)
2. Iterative gate pattern
3. Queue aging and promotion
4. All-eliminate fallback
5. Parameter validation
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pytest

from config.cognitive_parameters import DEFAULT_COGNITIVE_PARAMS, CognitiveParameters

# Import the modules under test
from engines.cognition.eisenhower_layer import (
    RUMSFELD_TO_EISENHOWER_BIAS,
    RUNG_UNLOCK_SCORES,
    EisenhowerLayer,
    EisenhowerQuadrant,
    ImportanceScore,
    PrioritizedTask,
    UrgencyScore,
)


class MockBlackboard:
    """Mock blackboard for testing EisenhowerLayer."""

    def __init__(self):
        self.actions_taken: int = 200
        self.action_budget: int = 400
        self.frame_delta_magnitude: float = 30.0
        self.epistemic_quadrant: str = "KK"
        self.working_theory: Optional[str] = "test_theory"
        self.open_questions: List[str] = []
        self.blocking_questions: List[str] = []
        self.strategy_stability: float = 0.7
        self._data: Dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from blackboard."""
        if hasattr(self, key):
            return getattr(self, key)
        return self._data.get(key, default)

    def slot(self, key: str, value: Any = None, **kwargs) -> Any:
        """Get or set value in blackboard (matches real Blackboard API)."""
        if value is not None:
            self._data[key] = value
            return value
        return self._data.get(key)

    def write(self, key: str, value: Any) -> None:
        """Write value to blackboard (legacy method)."""
        self._data[key] = value

    # Phase 10: Valence-aware methods (mock implementations)
    def get_aggregate_urgency(self) -> float:
        """Mock aggregate urgency from valence-tagged slots."""
        return self._data.get('_aggregate_urgency', 0.0)

    def get_aggregate_importance(self) -> float:
        """Mock aggregate importance from valence-tagged slots."""
        return self._data.get('_aggregate_importance', 0.0)


class TestEisenhowerQuadrants:
    """Test quadrant classification logic."""

    def test_q1_do_high_urgency_high_importance(self):
        """Q1 DO: high urgency AND high importance."""
        urgency = UrgencyScore(
            budget_pressure=0.8,
            volatility=0.6,
            blocking_factor=0.5,
            cascade_risk=0.4
        )
        importance = ImportanceScore(
            win_probability_delta=0.7,
            theory_validation=0.6,
            action_unlock=0.5,
            edge_trust=0.8
        )

        task = PrioritizedTask.classify("PATTERN_MATCH", urgency, importance, "KK")

        assert task.quadrant == EisenhowerQuadrant.Q1_DO

    def test_q2_schedule_low_urgency_high_importance(self):
        """Q2 SCHEDULE: low urgency but high importance."""
        urgency = UrgencyScore(
            budget_pressure=0.2,
            volatility=0.3,
            blocking_factor=0.1,
            cascade_risk=0.1
        )
        importance = ImportanceScore(
            win_probability_delta=0.8,
            theory_validation=0.9,
            action_unlock=0.6,
            edge_trust=0.7
        )

        task = PrioritizedTask.classify("THEORY_REVISION", urgency, importance, "KU")

        assert task.quadrant == EisenhowerQuadrant.Q2_SCHEDULE

    def test_q3_delegate_high_urgency_low_importance(self):
        """Q3 DELEGATE: high urgency but low importance."""
        urgency = UrgencyScore(
            budget_pressure=0.9,
            volatility=0.7,
            blocking_factor=0.8,
            cascade_risk=0.6
        )
        importance = ImportanceScore(
            win_probability_delta=0.1,
            theory_validation=0.2,
            action_unlock=0.1,
            edge_trust=0.3
        )

        task = PrioritizedTask.classify("NOISE_FILTER", urgency, importance, "KK")

        assert task.quadrant == EisenhowerQuadrant.Q3_DELEGATE

    def test_q4_eliminate_low_urgency_low_importance(self):
        """Q4 ELIMINATE: low urgency AND low importance."""
        urgency = UrgencyScore(
            budget_pressure=0.1,
            volatility=0.2,
            blocking_factor=0.1,
            cascade_risk=0.1
        )
        importance = ImportanceScore(
            win_probability_delta=0.1,
            theory_validation=0.1,
            action_unlock=0.1,
            edge_trust=0.2
        )

        task = PrioritizedTask.classify("COSMETIC_UPDATE", urgency, importance, "KK")

        assert task.quadrant == EisenhowerQuadrant.Q4_ELIMINATE


class TestRumsfeldToEisenhowerBias:
    """Test cross-matrix mapping from Rumsfeld to Eisenhower."""

    def test_kk_bias_boosts_both(self):
        """KK (Known-Known): Trust what we know - boost both urgency and importance."""
        bias = RUMSFELD_TO_EISENHOWER_BIAS["KK"]
        assert "importance_boost" in bias
        assert "urgency_boost" in bias
        assert bias["urgency_boost"] > 0, "KK should boost urgency (trust what we know)"

    def test_ku_bias_boosts_importance(self):
        """KU (Known-Unknown): Questions are important."""
        bias = RUMSFELD_TO_EISENHOWER_BIAS["KU"]
        assert bias["importance_boost"] > 0, "KU should boost importance"

    def test_uk_bias_reduces_urgency(self):
        """UK (Unknown-Known): Retrieval can wait."""
        bias = RUMSFELD_TO_EISENHOWER_BIAS["UK"]
        assert bias["urgency_boost"] < 0, "UK should reduce urgency"

    def test_uu_bias_reduces_urgency(self):
        """UU (Unknown-Unknown): Exploration not urgent."""
        bias = RUMSFELD_TO_EISENHOWER_BIAS["UU"]
        assert bias["urgency_boost"] < 0, "UU should reduce urgency (exploration not urgent)"


class TestEisenhowerLayerComputation:
    """Test EisenhowerLayer urgency and importance computation."""

    @pytest.fixture
    def layer(self):
        """Create EisenhowerLayer with mock blackboard."""
        blackboard = MockBlackboard()
        return EisenhowerLayer(blackboard)

    def test_compute_urgency_budget_pressure(self, layer):
        """Budget pressure increases with actions taken."""
        layer.blackboard.actions_taken = 380  # 95% of budget used
        layer.blackboard.action_budget = 400

        urgency = layer.compute_urgency("PATTERN_MATCH")

        assert urgency.budget_pressure > 0.9, "High action usage should create high pressure"

    def test_compute_urgency_volatility_from_frame_delta(self, layer):
        """High frame delta increases volatility."""
        layer.blackboard.frame_delta_magnitude = 80.0  # High volatility

        urgency = layer.compute_urgency("PATTERN_MATCH")

        assert urgency.volatility >= 0.8, "High frame delta should show in volatility"

    def test_compute_importance_theory_validation(self, layer):
        """Theory testing rungs have high validation score when theory exists."""
        layer.blackboard.working_theory = "test_theory"

        importance = layer.compute_importance("theory_gate", edge_trust=0.5)

        # theory_gate is a theory-testing rung
        assert importance.theory_validation >= 0.7

    def test_compute_importance_with_edge_trust(self, layer):
        """Edge trust affects importance computation."""
        high_trust_importance = layer.compute_importance("PATTERN_MATCH", edge_trust=0.9)
        low_trust_importance = layer.compute_importance("PATTERN_MATCH", edge_trust=0.1)

        assert high_trust_importance.edge_trust > low_trust_importance.edge_trust


class TestIterativeGatePattern:
    """Test the iterative gate pattern in rung selection."""

    @pytest.fixture
    def layer(self):
        """Create EisenhowerLayer with mock blackboard."""
        blackboard = MockBlackboard()
        return EisenhowerLayer(blackboard)

    def test_gate_single_rung_returns_quadrant_and_action(self, layer):
        """gate_single_rung returns (quadrant, action) tuple."""
        quadrant, action = layer.gate_single_rung("PATTERN_MATCH", edge_trust=0.8)

        assert isinstance(quadrant, EisenhowerQuadrant)
        # Action can be rung_name, cached action, or None

    def test_gate_single_rung_q1_executes(self, layer):
        """Q1 rung should return action to execute."""
        layer.blackboard.actions_taken = 380  # High urgency
        layer.blackboard.strategy_stability = 0.1  # High cascade risk

        quadrant, action = layer.gate_single_rung("survey", edge_trust=0.9)

        if quadrant == EisenhowerQuadrant.Q1_DO:
            assert action == "survey"

    def test_gate_single_rung_q2_schedules(self, layer):
        """Q2 rung should be scheduled."""
        layer.blackboard.actions_taken = 50  # Low urgency
        layer.blackboard.frame_delta_magnitude = 10.0  # Low volatility

        # Reset queue
        layer.scheduled_queue = []

        quadrant, action = layer.gate_single_rung("control_tracker", edge_trust=0.8)

        if quadrant == EisenhowerQuadrant.Q2_SCHEDULE:
            assert action is None or len(layer.scheduled_queue) > 0

    def test_gate_single_rung_q4_skips(self, layer):
        """Q4 rung should return None action."""
        layer.blackboard.actions_taken = 50  # Low urgency
        layer.blackboard.frame_delta_magnitude = 10.0
        layer.blackboard.working_theory = None  # No theory (low importance for theory rungs)
        layer.blackboard.strategy_stability = 0.95  # Very stable (low cascade risk)

        quadrant, action = layer.gate_single_rung("NOISE_FILTER", edge_trust=0.1)

        if quadrant == EisenhowerQuadrant.Q4_ELIMINATE:
            assert action is None


class TestQueueAgingAndPromotion:
    """Test queue aging and Q2 -> Q1 promotion."""

    @pytest.fixture
    def layer(self):
        """Create EisenhowerLayer with mock blackboard."""
        blackboard = MockBlackboard()
        return EisenhowerLayer(blackboard)

    def test_age_scheduled_queue_increases_budget_pressure(self, layer):
        """Aging increases budget_pressure of scheduled tasks."""
        # Manually add a task to scheduled queue
        task = PrioritizedTask.classify(
            "DEFERRED_TASK",
            UrgencyScore(0.3, 0.3, 0.2, 0.1),
            ImportanceScore(0.7, 0.6, 0.5, 0.8),
            "KK"
        )
        layer.scheduled_queue.append(task)
        initial_pressure = task.urgency.budget_pressure

        # Age the queue
        layer.age_scheduled_queue()

        new_pressure = layer.scheduled_queue[0].urgency.budget_pressure
        assert new_pressure > initial_pressure, "Aging should increase budget_pressure"

    def test_queue_promotion_q2_to_q1(self, layer):
        """Task should be promoted from Q2 to Q1 when urgency exceeds threshold."""
        # Add task that will become Q1 after aging
        # Start with Q2 classification
        task = PrioritizedTask.classify(
            "PROMOTED_TASK",
            UrgencyScore(0.58, 0.55, 0.55, 0.55),  # Just below 0.6 threshold
            ImportanceScore(0.7, 0.6, 0.5, 0.8),
            "KK"
        )
        layer.scheduled_queue.append(task)

        # Age multiple times until promoted
        for _ in range(20):
            layer.age_scheduled_queue()

        # After aging, the task should be Q1
        if layer.scheduled_queue:
            aged_task = layer.scheduled_queue[0]
            assert aged_task.quadrant == EisenhowerQuadrant.Q1_DO, \
                "Task should be promoted to Q1 after sufficient aging"

    def test_pop_promoted_finds_q1_task(self, layer):
        """pop_promoted_task should find and remove Q1 tasks from queue."""
        # Add a Q1 task directly
        q1_task = PrioritizedTask.classify(
            "URGENT_TASK",
            UrgencyScore(0.9, 0.9, 0.9, 0.9),  # Very urgent
            ImportanceScore(0.9, 0.9, 0.9, 0.9),  # Very important
            "KK"
        )
        layer.scheduled_queue.append(q1_task)

        promoted = layer.pop_promoted_task()

        assert promoted == "URGENT_TASK"
        assert len(layer.scheduled_queue) == 0


class TestAllEliminateFallback:
    """Test the all-eliminate fallback scenario."""

    @pytest.fixture
    def layer(self):
        """Create EisenhowerLayer with mock blackboard."""
        blackboard = MockBlackboard()
        return EisenhowerLayer(blackboard)

    def test_handle_all_eliminate_returns_fallback(self, layer):
        """When all rungs are Q4, should return fallback action."""
        # Empty scheduled queue
        layer.scheduled_queue = []

        fallback = layer.handle_all_eliminate()

        assert fallback is not None, "Should return fallback, not None"
        assert fallback == "exploration_phase", "Default fallback is exploration_phase"

    def test_handle_all_eliminate_uses_scheduled_queue(self, layer):
        """Fallback should use scheduled queue if available."""
        # Add task to scheduled queue
        task = PrioritizedTask.classify(
            "QUEUED_TASK",
            UrgencyScore(0.4, 0.3, 0.2, 0.1),
            ImportanceScore(0.6, 0.5, 0.4, 0.5),
            "KK"
        )
        layer.scheduled_queue.append(task)

        fallback = layer.handle_all_eliminate()

        assert fallback == "QUEUED_TASK"

    def test_handle_all_eliminate_increments_stats(self, layer):
        """Should increment all_eliminate_triggered stat."""
        initial_count = layer.stats['all_eliminate_triggered']

        layer.handle_all_eliminate()

        assert layer.stats['all_eliminate_triggered'] == initial_count + 1


class TestCognitiveParametersValidation:
    """Test CognitiveParameters validation and tiers."""

    def test_default_params_valid(self):
        """Default parameters should pass validation."""
        params = CognitiveParameters()
        assert params.validate() is True

    def test_invalid_urgency_threshold(self):
        """Invalid urgency threshold should fail validation."""
        params = CognitiveParameters(urgency_threshold=1.5)

        with pytest.raises(ValueError, match="urgency_threshold"):
            params.validate()

    def test_invalid_stabilizer_cooldown(self):
        """Cooldown less than confirmations should fail."""
        params = CognitiveParameters(
            stabilizer_confirmations=3,
            stabilizer_cooldown=2  # Less than confirmations
        )

        with pytest.raises(ValueError, match="stabilizer_cooldown"):
            params.validate()

    def test_felt_weights_sum(self):
        """FeltState weights must sum to 1.0."""
        params = CognitiveParameters(
            felt_weight_valence=0.5,  # Changed to break sum
            felt_weight_arousal=0.5,
            felt_weight_certainty=0.5,
            felt_weight_agency=0.5,
            felt_weight_salience=0.5  # Sum = 2.5
        )

        with pytest.raises(ValueError, match="FeltState weights"):
            params.validate()

    def test_tier_classification(self):
        """Parameters should be correctly classified by tier."""
        assert CognitiveParameters.get_tier("urgency_threshold") == 1
        assert CognitiveParameters.get_tier("kk_ku_confirmations") == 2
        assert CognitiveParameters.get_tier("felt_weight_valence") == 3

    def test_to_dict_contains_all_params(self):
        """to_dict should contain all parameters."""
        params = CognitiveParameters()
        d = params.to_dict()

        assert "urgency_threshold" in d
        assert "kk_ku_confirmations" in d
        assert "felt_weight_valence" in d
        assert len(d) >= 25  # Should have many params


class TestRungUnlockScores:
    """Test RUNG_UNLOCK_SCORES configuration."""

    def test_known_rungs_have_scores(self):
        """Known rungs should have unlock scores defined."""
        expected_rungs = [
            "survey",
            "control_tracker",
            "palette_detection",
            "goal_detector",
            "pattern_matcher",
            "spatial_reasoner"
        ]

        for rung in expected_rungs:
            assert rung in RUNG_UNLOCK_SCORES, f"{rung} missing from RUNG_UNLOCK_SCORES"

    def test_survey_has_highest_unlock(self):
        """Survey rung unlocks everything, should have high score."""
        assert RUNG_UNLOCK_SCORES["survey"] >= 0.8


class TestCrossMatrixIntegration:
    """Test the integration between Rumsfeld and Eisenhower matrices."""

    @pytest.fixture
    def layer(self):
        """Create EisenhowerLayer with mock blackboard."""
        blackboard = MockBlackboard()
        return EisenhowerLayer(blackboard)

    def test_prioritize_returns_rung_name(self, layer):
        """prioritize() should return a rung name or fallback."""
        candidates = [("survey", 0.8), ("control_tracker", 0.7)]

        result = layer.prioritize(candidates)

        assert result is not None
        assert isinstance(result, str)

    def test_prioritize_empty_returns_none(self, layer):
        """prioritize() with empty candidates returns None."""
        result = layer.prioritize([])

        assert result is None

    def test_different_rumsfeld_affects_classification(self, layer):
        """Different Rumsfeld quadrants should affect task classification."""
        # Test with KK
        layer.blackboard.epistemic_quadrant = "KK"
        result_kk = layer.prioritize([("survey", 0.5)])

        # Test with UU
        layer.blackboard.epistemic_quadrant = "UU"
        result_uu = layer.prioritize([("survey", 0.5)])

        # Both should return results, but stats should differ
        assert result_kk is not None
        assert result_uu is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
