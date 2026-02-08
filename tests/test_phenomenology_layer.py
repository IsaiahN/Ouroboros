"""
Test suite for Phase 9: Phenomenology Layer.

Tests cover:
1. FeltState dataclass and properties
2. Valence computation from blackboard state
3. FeltStateStabilizer hysteresis
4. Algorithm modulation based on FeltState
5. Feedback loop (compress -> inject -> next cycle)
6. Trace logging
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

from typing import Any, Dict, List, Optional

import pytest

# Import the modules under test
from engines.cognition.phenomenology_layer import (
    AlgorithmModulation,
    FeltState,
    FeltStateStabilizer,
    FeltStateTraceEntry,
    PhenomenologyLayer,
    Valence,
)


class MockBlackboard:
    """Mock blackboard for testing PhenomenologyLayer."""

    def __init__(self):
        self._data: Dict[str, Any] = {
            'epistemic_quadrant': 'KK',
            'working_theory': None,
            'controlled_object': None,
            'contradiction_detected': False,
            'cascade_failure': False,
            'action_budget_critical': False,
            'frame_delta_magnitude': 30.0,
            'strategy_stability': 0.7,
            'recent_success_rate': 0.5,
            'novelty_score': 0.3,
            'surprise_score': 0.2,
            'pattern_break': False,
            'stuck_detected': False,
            'levels_completed': 0,
            'total_levels': 5,
            'death_count': 0,
            'no_change_frames': 0,
            'confidence_delta': 0.0,
            'known_unknowns': [],
            'open_questions': [],
            'current_tick': 0,
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from blackboard."""
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

    def set(self, key: str, value: Any) -> None:
        """Alias for write."""
        self._data[key] = value


class TestFeltState:
    """Test FeltState dataclass and properties."""

    def test_feltstate_creation(self):
        """FeltState can be created with all dimensions."""
        felt = FeltState(
            valence=Valence.STABILITY,
            arousal=0.5,
            certainty=0.7,
            agency=0.6,
            salience=0.4,
            momentum=0.1,
            compression_ratio=5.0,
            dominant_contributors=['epistemic_quadrant']
        )

        assert felt.valence == Valence.STABILITY
        assert felt.arousal == 0.5
        assert felt.certainty == 0.7
        assert felt.agency == 0.6
        assert felt.salience == 0.4
        assert felt.momentum == 0.1

    def test_to_urgency_bias_threat(self):
        """THREAT valence with high arousal = high urgency."""
        felt = FeltState(
            valence=Valence.THREAT,
            arousal=0.9,
            certainty=0.5,
            agency=0.3,
            salience=0.8,
            momentum=-0.3,
            compression_ratio=5.0,
            dominant_contributors=[]
        )

        urgency = felt.to_urgency_bias()
        assert urgency > 0.7, "THREAT + high arousal should give high urgency"

    def test_to_urgency_bias_stability(self):
        """STABILITY valence with low arousal = low urgency."""
        felt = FeltState(
            valence=Valence.STABILITY,
            arousal=0.2,
            certainty=0.8,
            agency=0.8,
            salience=0.2,
            momentum=0.1,
            compression_ratio=5.0,
            dominant_contributors=[]
        )

        urgency = felt.to_urgency_bias()
        assert urgency < 0.1, "STABILITY + low arousal should give low urgency"

    def test_to_importance_bias_confident_and_capable(self):
        """High certainty + high agency = high importance."""
        felt = FeltState(
            valence=Valence.STABILITY,
            arousal=0.5,
            certainty=0.8,
            agency=0.8,
            salience=0.5,
            momentum=0.0,
            compression_ratio=5.0,
            dominant_contributors=[]
        )

        importance = felt.to_importance_bias()
        assert importance >= 0.7, "High certainty + agency should be important"

    def test_to_dict_serialization(self):
        """FeltState can be serialized to dict."""
        felt = FeltState(
            valence=Valence.OPPORTUNITY,
            arousal=0.6,
            certainty=0.5,
            agency=0.5,
            salience=0.5,
            momentum=0.2,
            compression_ratio=4.0,
            dominant_contributors=['working_theory']
        )

        d = felt.to_dict()

        assert d['valence'] == 'opportunity'
        assert d['arousal'] == 0.6
        assert d['certainty'] == 0.5
        assert 'dominant_contributors' in d


class TestValenceComputation:
    """Test valence computation from blackboard state."""

    @pytest.fixture
    def layer(self):
        """Create PhenomenologyLayer with mock blackboard."""
        blackboard = MockBlackboard()
        layer = PhenomenologyLayer(blackboard)
        # Initialize with a previous state so compress() doesn't cold-start
        layer.previous_felt = FeltState(
            valence=Valence.STABILITY,
            arousal=0.5,
            certainty=0.5,
            agency=0.5,
            salience=0.5,
            momentum=0.0,
            compression_ratio=5.0,
            dominant_contributors=[]
        )
        return layer

    def test_valence_threat_from_contradiction(self, layer):
        """Contradiction detected = THREAT valence."""
        layer.blackboard.set('contradiction_detected', True)

        valence = layer._compute_valence()

        assert valence == Valence.THREAT

    def test_valence_threat_from_cascade_failure(self, layer):
        """Cascade failure = THREAT valence."""
        layer.blackboard.set('cascade_failure', True)

        valence = layer._compute_valence()

        assert valence == Valence.THREAT

    def test_valence_threat_from_budget_critical(self, layer):
        """Budget critical = THREAT valence."""
        layer.blackboard.set('action_budget_critical', True)

        valence = layer._compute_valence()

        assert valence == Valence.THREAT

    def test_valence_confusion_from_uu_quadrant(self, layer):
        """Low raw valence score (between threat and confusion thresholds) = CONFUSION.

        Previously this was hardcoded to UU→CONFUSION. Now it's score-driven:
        a raw score between -0.3 and -0.1 produces CONFUSION regardless of
        epistemic quadrant.
        """
        layer.blackboard.set('epistemic_quadrant', 'UU')
        layer.blackboard.set('contradiction_detected', False)
        # Push score into confusion range [-0.3, -0.1) by adding
        # strong negative internal signals + stuck penalty
        layer.blackboard.set('confidence_delta', -1.0)
        layer.blackboard.set('agency_score', 0.0)
        layer.blackboard.set('recent_success_rate', 0.0)
        layer.blackboard.set('stuck_detected', True)

        valence = layer._compute_valence()

        assert valence == Valence.CONFUSION

    def test_valence_boredom_from_no_change(self, layer):
        """No change for many frames = BOREDOM valence."""
        layer.blackboard.set('epistemic_quadrant', 'KK')
        layer.blackboard.set('no_change_frames', 15)

        valence = layer._compute_valence()

        assert valence == Valence.BOREDOM

    def test_valence_stability_default(self, layer):
        """Normal state = STABILITY valence."""
        layer.blackboard.set('epistemic_quadrant', 'KK')
        layer.blackboard.set('no_change_frames', 2)
        layer.blackboard.set('contradiction_detected', False)

        valence = layer._compute_valence()

        assert valence == Valence.STABILITY


class TestFeltStateStabilizer:
    """Test FeltStateStabilizer hysteresis."""

    def test_stabilizer_blocks_rapid_change(self):
        """Stabilizer should block rapid valence changes."""
        stabilizer = FeltStateStabilizer()

        previous = FeltState(
            valence=Valence.STABILITY, arousal=0.5, certainty=0.5,
            agency=0.5, salience=0.5, momentum=0.0,
            compression_ratio=5.0, dominant_contributors=[]
        )

        # Try to change to THREAT (requires 2 confirmations)
        raw = FeltState(
            valence=Valence.THREAT, arousal=0.8, certainty=0.3,
            agency=0.3, salience=0.8, momentum=-0.3,
            compression_ratio=5.0, dominant_contributors=[]
        )

        # First signal - should be blocked
        result = stabilizer.stabilize(raw, previous)
        assert result.valence == Valence.STABILITY, "First signal should be blocked"

    def test_stabilizer_allows_after_confirmation(self):
        """Stabilizer should allow change after confirmations."""
        stabilizer = FeltStateStabilizer()

        previous = FeltState(
            valence=Valence.STABILITY, arousal=0.5, certainty=0.5,
            agency=0.5, salience=0.5, momentum=0.0,
            compression_ratio=5.0, dominant_contributors=[]
        )

        raw_threat = FeltState(
            valence=Valence.THREAT, arousal=0.8, certainty=0.3,
            agency=0.3, salience=0.8, momentum=-0.3,
            compression_ratio=5.0, dominant_contributors=[]
        )

        # First signal
        result1 = stabilizer.stabilize(raw_threat, previous)
        # Second signal (STABILITY -> THREAT requires 2)
        result2 = stabilizer.stabilize(raw_threat, result1)

        assert result2.valence == Valence.THREAT, "After 2 signals, THREAT should be allowed"

    def test_stabilizer_enforces_cooldown(self):
        """Stabilizer should enforce cooldown after transition."""
        stabilizer = FeltStateStabilizer()

        previous = FeltState(
            valence=Valence.STABILITY, arousal=0.5, certainty=0.5,
            agency=0.5, salience=0.5, momentum=0.0,
            compression_ratio=5.0, dominant_contributors=[]
        )

        # Force transition to THREAT
        raw_threat = FeltState(
            valence=Valence.THREAT, arousal=0.8, certainty=0.3,
            agency=0.3, salience=0.8, momentum=-0.3,
            compression_ratio=5.0, dominant_contributors=[]
        )

        # Get to THREAT state
        stabilizer.stabilize(raw_threat, previous)
        threat_state = stabilizer.stabilize(raw_threat, previous)

        # Now try to immediately go back to STABILITY
        raw_stability = FeltState(
            valence=Valence.STABILITY, arousal=0.3, certainty=0.7,
            agency=0.7, salience=0.3, momentum=0.2,
            compression_ratio=5.0, dominant_contributors=[]
        )

        # Should be blocked by cooldown
        result = stabilizer.stabilize(raw_stability, threat_state)
        assert result.valence == Valence.THREAT, "Cooldown should prevent immediate reversal"

    def test_stabilizer_instant_panic_from_boredom(self):
        """BOREDOM -> THREAT should be instant (1 signal)."""
        stabilizer = FeltStateStabilizer()

        previous = FeltState(
            valence=Valence.BOREDOM, arousal=0.2, certainty=0.5,
            agency=0.5, salience=0.2, momentum=0.0,
            compression_ratio=5.0, dominant_contributors=[]
        )

        raw_threat = FeltState(
            valence=Valence.THREAT, arousal=0.9, certainty=0.3,
            agency=0.2, salience=0.9, momentum=-0.5,
            compression_ratio=5.0, dominant_contributors=[]
        )

        # First signal should be enough for BOREDOM -> THREAT
        result = stabilizer.stabilize(raw_threat, previous)
        assert result.valence == Valence.THREAT, "BOREDOM -> THREAT should be instant"


class TestAlgorithmModulation:
    """Test algorithm modulation based on FeltState."""

    @pytest.fixture
    def layer(self):
        """Create PhenomenologyLayer with mock blackboard."""
        blackboard = MockBlackboard()
        return PhenomenologyLayer(blackboard)

    def test_panic_mode_overrides_algorithm(self, layer):
        """High arousal + low agency = panic mode."""
        felt = FeltState(
            valence=Valence.THREAT,
            arousal=0.9,  # High arousal
            certainty=0.5,
            agency=0.2,   # Low agency
            salience=0.8,
            momentum=-0.3,
            compression_ratio=5.0,
            dominant_contributors=[]
        )

        modulation = layer.get_algorithm_modulation(felt)

        assert modulation.algorithm_override == 'beam_search'
        assert modulation.beam_width_multiplier < 1.0

    def test_confident_but_threatened_excludes_path(self, layer):
        """THREAT + high certainty = exclude recent path."""
        layer.blackboard.set('recent_path', ['rung_a', 'rung_b', 'rung_c'])

        felt = FeltState(
            valence=Valence.THREAT,
            arousal=0.5,
            certainty=0.8,  # High certainty
            agency=0.5,
            salience=0.5,
            momentum=-0.2,
            compression_ratio=5.0,
            dominant_contributors=[]
        )

        modulation = layer.get_algorithm_modulation(felt)

        assert 'rung_a' in modulation.exclusion_set
        assert modulation.exploration_boost > 0

    def test_boredom_boosts_exploration(self, layer):
        """BOREDOM = high exploration boost."""
        felt = FeltState(
            valence=Valence.BOREDOM,
            arousal=0.2,
            certainty=0.5,
            agency=0.5,
            salience=0.1,
            momentum=-0.1,
            compression_ratio=5.0,
            dominant_contributors=[]
        )

        modulation = layer.get_algorithm_modulation(felt)

        assert modulation.exploration_boost >= 0.5

    def test_high_salience_widens_beam(self, layer):
        """High salience = wider beam search."""
        felt = FeltState(
            valence=Valence.OPPORTUNITY,
            arousal=0.6,
            certainty=0.6,
            agency=0.6,
            salience=0.9,  # High salience
            momentum=0.2,
            compression_ratio=5.0,
            dominant_contributors=[]
        )

        modulation = layer.get_algorithm_modulation(felt)

        assert modulation.beam_width_multiplier > 1.0

    def test_normal_state_no_modulation(self, layer):
        """Normal STABILITY state = no modulation."""
        felt = FeltState(
            valence=Valence.STABILITY,
            arousal=0.5,
            certainty=0.6,
            agency=0.6,
            salience=0.4,
            momentum=0.1,
            compression_ratio=5.0,
            dominant_contributors=[]
        )

        modulation = layer.get_algorithm_modulation(felt)

        assert modulation.algorithm_override is None
        assert modulation.beam_width_multiplier == 1.0
        assert modulation.exploration_boost == 0.0
        assert len(modulation.exclusion_set) == 0


class TestFeedbackLoop:
    """Test the compress -> inject -> next cycle feedback loop."""

    @pytest.fixture
    def layer(self):
        """Create PhenomenologyLayer with mock blackboard."""
        blackboard = MockBlackboard()
        return PhenomenologyLayer(blackboard)

    def test_cold_start_returns_confusion(self, layer):
        """First compression (cold start) returns CONFUSION."""
        felt = layer.compress()

        assert felt.valence == Valence.CONFUSION
        assert 'cold_start' in felt.dominant_contributors

    def test_inject_writes_felt_slots(self, layer):
        """inject() should write felt_* slots to blackboard."""
        felt = FeltState(
            valence=Valence.OPPORTUNITY,
            arousal=0.7,
            certainty=0.6,
            agency=0.8,
            salience=0.5,
            momentum=0.2,
            compression_ratio=5.0,
            dominant_contributors=['working_theory']
        )

        layer.inject(felt)

        assert layer.blackboard.get('felt_valence') == 'opportunity'
        assert layer.blackboard.get('felt_arousal') == 0.7
        assert layer.blackboard.get('felt_certainty') == 0.6
        assert layer.blackboard.get('felt_agency') == 0.8
        assert layer.blackboard.get('felt_salience') == 0.5
        assert layer.blackboard.get('felt_momentum') == 0.2

    def test_inject_writes_biases(self, layer):
        """inject() should write urgency/importance biases."""
        felt = FeltState(
            valence=Valence.THREAT,
            arousal=0.8,
            certainty=0.3,
            agency=0.3,
            salience=0.8,
            momentum=-0.3,
            compression_ratio=5.0,
            dominant_contributors=[]
        )

        layer.inject(felt)

        assert layer.blackboard.get('felt_urgency_bias') is not None
        assert layer.blackboard.get('felt_importance_bias') is not None
        assert layer.blackboard.get('felt_urgency_bias') > 0.5  # THREAT = high urgency

    def test_full_feedback_loop(self, layer):
        """Test complete compress -> inject -> compress cycle."""
        # First cycle (cold start)
        felt1 = layer.compress()
        layer.inject(felt1)

        # Modify blackboard to simulate game progress
        layer.blackboard.set('epistemic_quadrant', 'KK')
        layer.blackboard.set('controlled_object', 'player')
        layer.blackboard.set('working_theory', 'push_blocks')
        layer.blackboard.set('recent_success_rate', 0.8)

        # Second cycle - still in hysteresis (CONFUSION -> STABILITY needs 2 confirmations)
        felt2 = layer.compress()
        layer.inject(felt2)

        # Note: Valence may still be CONFUSION due to stabilizer hysteresis
        # but other dimensions should reflect improved state
        assert felt2.certainty > felt1.certainty
        assert felt2.agency > felt1.agency

        # Third cycle - after enough confirmations, should transition
        felt3 = layer.compress()
        layer.inject(felt3)

        # After 2 confirmations, should have transitioned away from CONFUSION
        # With KK quadrant and high success rate, external validation is positive
        # so we expect OPPORTUNITY (not STABILITY) due to weighted valence scoring
        assert felt3.valence != Valence.CONFUSION
        assert felt3.valence in (Valence.STABILITY, Valence.OPPORTUNITY)


class TestTraceLogging:
    """Test trace logging for debugging."""

    @pytest.fixture
    def layer(self):
        """Create PhenomenologyLayer with mock blackboard."""
        blackboard = MockBlackboard()
        return PhenomenologyLayer(blackboard)

    def test_compress_creates_trace(self, layer):
        """compress() should create trace entry."""
        felt = layer.compress()

        assert len(layer.trace_log) == 1
        trace = layer.trace_log[0]
        assert trace.felt_state == felt

    def test_trace_has_explanation(self, layer):
        """Trace entry should have explanation method."""
        layer.compress()

        trace = layer.trace_log[0]
        explanation = trace.explain()

        assert 'Felt' in explanation
        assert 'Tick' in explanation

    def test_trace_log_limited(self, layer):
        """Trace log should be limited to MAX_TRACE_LOG entries."""
        # Force many compressions
        for i in range(600):
            layer.blackboard.set('current_tick', i)
            felt = layer.compress()
            layer.inject(felt)

        assert len(layer.trace_log) <= layer.MAX_TRACE_LOG

    def test_get_recent_traces(self, layer):
        """get_recent_traces() should return last N traces."""
        # Create some traces
        for i in range(10):
            layer.blackboard.set('current_tick', i)
            felt = layer.compress()
            layer.inject(felt)

        recent = layer.get_recent_traces(5)

        assert len(recent) == 5
        # Most recent should be last
        assert recent[-1].tick == 9


class TestStatistics:
    """Test statistics and reset functionality."""

    @pytest.fixture
    def layer(self):
        """Create PhenomenologyLayer with mock blackboard."""
        blackboard = MockBlackboard()
        return PhenomenologyLayer(blackboard)

    def test_stats_track_compressions(self, layer):
        """Stats should track compression count."""
        layer.compress()
        layer.compress()
        layer.compress()

        stats = layer.get_stats()

        assert stats['compressions'] == 3
        # Note: All compressions after cold start still count as cold_starts
        # because inject() is what sets previous_felt
        # Without inject(), each compress() sees previous_felt=None
        # So we need to inject to properly advance the feedback loop

    def test_stats_track_cold_starts_correctly(self, layer):
        """Only first compression without prior inject is a cold start."""
        felt1 = layer.compress()  # Cold start
        layer.inject(felt1)       # Sets previous_felt

        felt2 = layer.compress()  # Not a cold start
        layer.inject(felt2)

        felt3 = layer.compress()  # Not a cold start

        stats = layer.get_stats()
        assert stats['compressions'] == 3
        assert stats['cold_starts'] == 1

    def test_stats_track_injections(self, layer):
        """Stats should track injection count."""
        felt = layer.compress()
        layer.inject(felt)
        layer.inject(felt)

        stats = layer.get_stats()

        assert stats['injections'] == 2

    def test_reset_clears_state(self, layer):
        """reset() should clear all state."""
        layer.compress()
        felt = FeltState(
            valence=Valence.STABILITY, arousal=0.5, certainty=0.5,
            agency=0.5, salience=0.5, momentum=0.0,
            compression_ratio=5.0, dominant_contributors=[]
        )
        layer.inject(felt)

        layer.reset()

        assert layer.previous_felt is None
        assert len(layer.history) == 0
        assert len(layer.trace_log) == 0
        assert layer.get_stats()['compressions'] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
