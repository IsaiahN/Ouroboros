"""
Tests for Epistemic State Machine components (Phase 1.5).

Tests cover:
1. EpistemicState - quadrant computation and state tracking
2. EpistemicTracker - transition detection
3. ContradictionDetector - contradiction classification
4. Integration - full epistemic flow
"""

from datetime import datetime
from typing import Set

import pytest

from engines.cognition.blackboard import (
    Blackboard,
    KnownFact,
    Question,
    RumsfeldQuadrant,
)
from engines.cognition.contradiction_detector import (
    ContradictionDetector,
    ContradictionRecord,
    ContradictionSeverity,
)
from engines.cognition.epistemic_state import (
    QUADRANT_DEFAULT_ALGORITHMS,
    EpistemicSnapshot,
    EpistemicState,
    EpistemicTransition,
    TransitionResponse,
)
from engines.cognition.epistemic_tracker import EpistemicTracker, RungResult

# =============================================================================
# EPISTEMIC STATE TESTS
# =============================================================================

class TestEpistemicState:
    """Tests for EpistemicState data structure."""

    def test_default_state(self):
        """Test default epistemic state."""
        state = EpistemicState()

        assert state.primary_quadrant == RumsfeldQuadrant.UU
        assert state.kk_confidence == 0.0
        assert state.ku_urgency == 0.0
        assert state.uk_potential == 0.0
        assert state.uu_estimate == 0.5
        assert len(state.known_knowns) == 0
        assert len(state.known_unknowns) == 0
        assert len(state.unknown_knowns) == 0

    def test_compute_quadrant_kk(self):
        """Test KK quadrant when high confidence."""
        state = EpistemicState()
        state.kk_confidence = 0.85
        state.uu_estimate = 0.2

        quadrant = state.compute_primary_quadrant()
        assert quadrant == RumsfeldQuadrant.KK

    def test_compute_quadrant_ku(self):
        """Test KU quadrant when urgent questions."""
        state = EpistemicState()
        state.ku_urgency = 0.6
        state.known_unknowns = {
            "q1": Question("q1", "What is X?", ["rung1"]),
            "q2": Question("q2", "What is Y?", ["rung2"]),
        }
        state.uu_estimate = 0.4

        quadrant = state.compute_primary_quadrant()
        assert quadrant == RumsfeldQuadrant.KU

    def test_compute_quadrant_uk(self):
        """Test UK quadrant when high untapped potential."""
        state = EpistemicState()
        state.uk_potential = 0.7
        state.unknown_knowns = {"r1", "r2", "r3", "r4"}

        quadrant = state.compute_primary_quadrant()
        assert quadrant == RumsfeldQuadrant.UK

    def test_compute_quadrant_uu(self):
        """Test UU quadrant when high exploration estimate."""
        state = EpistemicState()
        state.uu_estimate = 0.8

        quadrant = state.compute_primary_quadrant()
        assert quadrant == RumsfeldQuadrant.UU

    def test_update_primary_quadrant(self):
        """Test updating primary quadrant."""
        state = EpistemicState()
        state.kk_confidence = 0.9
        state.uu_estimate = 0.1

        new_quadrant = state.update_primary_quadrant()
        assert new_quadrant == RumsfeldQuadrant.KK
        assert state.primary_quadrant == RumsfeldQuadrant.KK

    def test_summary(self):
        """Test state summary string."""
        state = EpistemicState()
        state.kk_confidence = 0.75
        summary = state.summary()

        assert "EpistemicState" in summary
        assert "KK=" in summary
        assert "0.75" in summary


class TestEpistemicTransition:
    """Tests for EpistemicTransition."""

    def test_transition_creation(self):
        """Test creating a transition."""
        transition = EpistemicTransition(
            from_quadrant=RumsfeldQuadrant.UU,
            to_quadrant=RumsfeldQuadrant.KU,
            trigger_rung="survey",
            trigger_reason="Found question",
            timestamp=10
        )

        assert transition.from_quadrant == RumsfeldQuadrant.UU
        assert transition.to_quadrant == RumsfeldQuadrant.KU
        assert transition.transition_key == "UU->KU"

    def test_is_progression(self):
        """Test progression detection."""
        # UU->KU is progression
        t1 = EpistemicTransition(
            from_quadrant=RumsfeldQuadrant.UU,
            to_quadrant=RumsfeldQuadrant.KU,
            trigger_rung="test",
            trigger_reason="test",
            timestamp=0
        )
        assert t1.is_progression
        assert not t1.is_regression

        # KU->KK is progression
        t2 = EpistemicTransition(
            from_quadrant=RumsfeldQuadrant.KU,
            to_quadrant=RumsfeldQuadrant.KK,
            trigger_rung="test",
            trigger_reason="test",
            timestamp=0
        )
        assert t2.is_progression

    def test_is_regression(self):
        """Test regression detection."""
        # KK->UU is regression
        t1 = EpistemicTransition(
            from_quadrant=RumsfeldQuadrant.KK,
            to_quadrant=RumsfeldQuadrant.UU,
            trigger_rung="test",
            trigger_reason="contradiction",
            timestamp=0
        )
        assert t1.is_regression
        assert not t1.is_progression

        # KK->KU is regression
        t2 = EpistemicTransition(
            from_quadrant=RumsfeldQuadrant.KK,
            to_quadrant=RumsfeldQuadrant.KU,
            trigger_rung="test",
            trigger_reason="mild contradiction",
            timestamp=0
        )
        assert t2.is_regression

    def test_is_stagnation(self):
        """Test stagnation detection."""
        t = EpistemicTransition(
            from_quadrant=RumsfeldQuadrant.UU,
            to_quadrant=RumsfeldQuadrant.UU,
            trigger_rung="test",
            trigger_reason="still exploring",
            timestamp=0
        )
        assert t.is_stagnation


class TestEpistemicSnapshot:
    """Tests for EpistemicSnapshot."""

    def test_from_state(self):
        """Test creating snapshot from state."""
        state = EpistemicState()
        state.primary_quadrant = RumsfeldQuadrant.KU
        state.kk_confidence = 0.5
        state.ku_urgency = 0.7
        state.known_unknowns = {"q1": Question("q1", "test", [])}
        state.timestamp = 42

        snapshot = EpistemicSnapshot.from_state(state)

        assert snapshot.quadrant == RumsfeldQuadrant.KU
        assert snapshot.kk_confidence == 0.5
        assert snapshot.ku_urgency == 0.7
        assert snapshot.ku_count == 1
        assert snapshot.timestamp == 42


# =============================================================================
# EPISTEMIC TRACKER TESTS
# =============================================================================

class TestRungResult:
    """Tests for RungResult protocol."""

    def test_rung_result_properties(self):
        """Test RungResult computed properties."""
        result = RungResult(
            rung_name="test",
            slot_name="control_object",
            value="blue_square",
            confidence=0.9
        )

        assert result.is_confident
        assert not result.is_uncertain
        assert not result.raised_questions
        assert not result.answered_questions

    def test_rung_result_with_questions(self):
        """Test RungResult with questions."""
        result = RungResult(
            rung_name="survey",
            confidence=0.3,  # Below 0.4 threshold for is_uncertain
            raises_questions=[
                Question("q1", "What do I control?", ["control_tracker"])
            ]
        )

        assert result.raised_questions
        assert not result.is_confident
        assert result.is_uncertain


class TestEpistemicTracker:
    """Tests for EpistemicTracker."""

    @pytest.fixture
    def tracker(self):
        """Create a fresh tracker."""
        return EpistemicTracker()

    @pytest.fixture
    def blackboard(self):
        """Create a blackboard for testing."""
        return Blackboard()

    def test_initial_state(self, tracker):
        """Test tracker initial state."""
        assert tracker.current_state.primary_quadrant == RumsfeldQuadrant.UU
        assert len(tracker.transitions) == 0
        assert len(tracker.history) == 0

    def test_reset(self, tracker):
        """Test tracker reset."""
        tracker._tick = 100
        tracker.transitions.append(
            EpistemicTransition(
                RumsfeldQuadrant.UU, RumsfeldQuadrant.KU,
                "test", "test", 0
            )
        )

        tracker.reset()

        assert tracker._tick == 0
        assert len(tracker.transitions) == 0
        assert len(tracker.history) == 0

    def test_update_kk(self, tracker, blackboard):
        """Test KK update from high confidence result."""
        result = RungResult(
            rung_name="control_tracker",
            slot_name="control_object",
            value="blue_square",
            confidence=0.9
        )

        transitions = tracker.update_from_rung_result(
            rung_name="control_tracker",
            result=result,
            blackboard=blackboard,
            all_rungs={"control_tracker", "survey"},
            visited_rungs={"control_tracker"}
        )

        # Should have added to KK
        assert "control_object" in tracker.current_state.known_knowns
        assert tracker.current_state.kk_confidence > 0

    def test_transition_uu_to_ku(self, tracker, blackboard):
        """Test transition from UU to KU when question is raised."""
        # Start in UU (default)
        assert tracker.current_state.primary_quadrant == RumsfeldQuadrant.UU

        # Raise a question
        question = Question(
            question_id="q1",
            description="What do I control?",
            answerable_by=["control_tracker"],
            priority=0.8
        )
        result = RungResult(
            rung_name="survey",
            confidence=0.5,
            raises_questions=[question]
        )

        # Need to manually set up for KU transition
        tracker.current_state.uu_estimate = 0.4  # Lower UU to allow KU

        transitions = tracker.update_from_rung_result(
            rung_name="survey",
            result=result,
            blackboard=blackboard,
            all_rungs={"survey", "control_tracker"},
            visited_rungs={"survey"}
        )

        # Should have added question to KU
        assert "q1" in tracker.current_state.known_unknowns
        assert tracker.current_state.ku_urgency > 0

    def test_transition_ku_to_kk(self, tracker, blackboard):
        """Test transition from KU to KK when question answered."""
        # Set up KU state with a question
        tracker.current_state.primary_quadrant = RumsfeldQuadrant.KU
        tracker.current_state.uu_estimate = 0.3
        tracker.current_state.known_unknowns["q1"] = Question(
            question_id="q1",
            description="What do I control?",
            answerable_by=["control_tracker"],
            priority=0.8
        )
        tracker.current_state.ku_urgency = 0.6
        tracker._last_quadrant = RumsfeldQuadrant.KU

        # Answer the question with high confidence
        result = RungResult(
            rung_name="control_tracker",
            slot_name="control_object",
            value="blue_square",
            confidence=0.9,
            answers_questions=["q1"]
        )

        transitions = tracker.update_from_rung_result(
            rung_name="control_tracker",
            result=result,
            blackboard=blackboard,
            all_rungs={"survey", "control_tracker"},
            visited_rungs={"survey", "control_tracker"}
        )

        # Question should be answered
        assert "q1" not in tracker.current_state.known_unknowns
        # Should have high KK
        assert "control_object" in tracker.current_state.known_knowns

    def test_history_tracking(self, tracker, blackboard):
        """Test that history is tracked."""
        result = RungResult(rung_name="test", confidence=0.5)

        for i in range(5):
            tracker.update_from_rung_result(
                rung_name="test",
                result=result,
                blackboard=blackboard,
                all_rungs={"test"},
                visited_rungs={"test"}
            )

        assert len(tracker.history) == 5

    def test_history_pruning(self, tracker, blackboard):
        """Test that history is pruned when too large."""
        tracker.MAX_HISTORY_SIZE = 10
        result = RungResult(rung_name="test", confidence=0.5)

        for i in range(20):
            tracker.update_from_rung_result(
                rung_name="test",
                result=result,
                blackboard=blackboard,
                all_rungs={"test"},
                visited_rungs={"test"}
            )

        assert len(tracker.history) <= 10

    def test_get_transition_pattern(self, tracker):
        """Test transition pattern string."""
        tracker.transitions = [
            EpistemicTransition(RumsfeldQuadrant.UU, RumsfeldQuadrant.KU, "a", "a", 0),
            EpistemicTransition(RumsfeldQuadrant.KU, RumsfeldQuadrant.KK, "b", "b", 1),
        ]

        pattern = tracker.get_transition_pattern()
        assert pattern == "KU->KK"

    def test_stagnation_detection(self, tracker, blackboard):
        """Test stagnation detection."""
        result = RungResult(rung_name="test", confidence=0.3)

        # Stay in UU for multiple ticks
        for i in range(10):
            tracker.update_from_rung_result(
                rung_name="test",
                result=result,
                blackboard=blackboard,
                all_rungs={"test"},
                visited_rungs={"test"}
            )

        assert tracker.is_stagnating(threshold=5)

    def test_get_current_algorithm(self, tracker):
        """Test getting current algorithm for quadrant."""
        tracker.current_state.primary_quadrant = RumsfeldQuadrant.KK
        assert tracker.get_current_algorithm() == "GreedyExploitation"

        tracker.current_state.primary_quadrant = RumsfeldQuadrant.KU
        assert tracker.get_current_algorithm() == "TargetedQuestionSearch"


# =============================================================================
# CONTRADICTION DETECTOR TESTS
# =============================================================================

class TestContradictionDetector:
    """Tests for ContradictionDetector."""

    @pytest.fixture
    def detector(self):
        """Create a fresh detector."""
        return ContradictionDetector()

    def test_no_contradiction_no_old_fact(self, detector):
        """Test no contradiction when no old fact exists."""
        result = detector.check_contradiction(
            slot_name="test",
            old_fact=None,
            new_value="value",
            new_confidence=0.9,
            new_source_rung="test_rung"
        )

        assert result is None

    def test_no_contradiction_same_value(self, detector):
        """Test no contradiction when values are the same."""
        old_fact = KnownFact(
            slot_name="test",
            value="same_value",
            confidence=0.9,
            source_rung="old_rung",
            verified_at=0
        )

        result = detector.check_contradiction(
            slot_name="test",
            old_fact=old_fact,
            new_value="same_value",
            new_confidence=0.9,
            new_source_rung="new_rung"
        )

        assert result is None

    def test_no_contradiction_low_old_confidence(self, detector):
        """Test no contradiction when old confidence was low."""
        old_fact = KnownFact(
            slot_name="test",
            value="old_value",
            confidence=0.4,  # Low confidence
            source_rung="old_rung",
            verified_at=0
        )

        result = detector.check_contradiction(
            slot_name="test",
            old_fact=old_fact,
            new_value="new_value",
            new_confidence=0.9,
            new_source_rung="new_rung"
        )

        assert result is None

    def test_mild_contradiction(self, detector):
        """Test mild contradiction detection."""
        old_fact = KnownFact(
            slot_name="control_object",
            value="blue_square",
            confidence=0.85,
            source_rung="control_tracker",
            verified_at=0
        )

        result = detector.check_contradiction(
            slot_name="control_object",
            old_fact=old_fact,
            new_value="red_circle",
            new_confidence=0.5,  # Lower confidence = mild
            new_source_rung="new_tracker"
        )

        assert result is not None
        assert result.severity == ContradictionSeverity.MILD
        assert result.contradicted_slot == "control_object"

    def test_severe_contradiction(self, detector):
        """Test severe contradiction detection."""
        old_fact = KnownFact(
            slot_name="physics_game",
            value=False,
            confidence=0.9,
            source_rung="frame_interp",
            verified_at=0
        )

        result = detector.check_contradiction(
            slot_name="physics_game",
            old_fact=old_fact,
            new_value=True,
            new_confidence=0.95,  # High confidence = severe
            new_source_rung="event_understanding"
        )

        assert result is not None
        assert result.severity == ContradictionSeverity.SEVERE

    def test_exclusion_list_updated(self, detector):
        """Test that exclusion list is updated on severe contradiction."""
        old_fact = KnownFact(
            slot_name="test",
            value="old",
            confidence=0.9,
            source_rung="bad_rung",
            verified_at=0
        )

        detector.check_contradiction(
            slot_name="test",
            old_fact=old_fact,
            new_value="new",
            new_confidence=0.95,
            new_source_rung="good_rung",
            path_so_far=["rung1", "bad_rung"]
        )

        exclusions = detector.get_exclusion_list()
        assert "bad_rung" in exclusions

    def test_catastrophic_threshold(self, detector):
        """Test catastrophic contradiction threshold."""
        old_fact = KnownFact(
            slot_name="test",
            value="old",
            confidence=0.9,
            source_rung="rung",
            verified_at=0
        )

        # Trigger multiple contradictions
        for i in range(4):
            detector.check_contradiction(
                slot_name=f"test_{i}",
                old_fact=old_fact,
                new_value=f"new_{i}",
                new_confidence=0.95,
                new_source_rung=f"rung_{i}"
            )

        assert detector.is_catastrophic()

    def test_get_target_quadrant_mild(self, detector):
        """Test target quadrant for mild contradiction."""
        record = ContradictionRecord(
            contradicted_slot="test",
            old_value="old",
            old_confidence=0.8,
            old_source_rung="old_rung",
            new_value="new",
            new_confidence=0.5,
            new_source_rung="new_rung",
            severity=ContradictionSeverity.MILD,
            detected_at=0
        )

        target = detector.get_target_quadrant(record)
        assert target == RumsfeldQuadrant.KU

    def test_get_target_quadrant_severe(self, detector):
        """Test target quadrant for severe contradiction."""
        record = ContradictionRecord(
            contradicted_slot="test",
            old_value="old",
            old_confidence=0.9,
            old_source_rung="old_rung",
            new_value="new",
            new_confidence=0.95,
            new_source_rung="new_rung",
            severity=ContradictionSeverity.SEVERE,
            detected_at=0
        )

        target = detector.get_target_quadrant(record)
        assert target == RumsfeldQuadrant.UU

    def test_reset(self, detector):
        """Test partial reset."""
        detector._contradiction_count_this_decision = 5
        detector.reset()
        assert detector._contradiction_count_this_decision == 0

    def test_full_reset(self, detector):
        """Test full reset."""
        detector.contradictions.append(
            ContradictionRecord(
                contradicted_slot="test",
                old_value="old",
                old_confidence=0.9,
                old_source_rung="old",
                new_value="new",
                new_confidence=0.9,
                new_source_rung="new",
                severity=ContradictionSeverity.SEVERE,
                detected_at=0
            )
        )
        detector.excluded_rungs.add("bad_rung")

        detector.full_reset()

        assert len(detector.contradictions) == 0
        assert len(detector.excluded_rungs) == 0


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestEpistemicIntegration:
    """Integration tests for epistemic components."""

    def test_full_epistemic_flow(self):
        """Test a complete epistemic flow through discovery to exploitation."""
        tracker = EpistemicTracker()
        detector = ContradictionDetector()
        blackboard = Blackboard()

        all_rungs = {"survey", "control_tracker", "action_selection"}
        visited: Set[str] = set()

        # Step 1: Start in UU, survey finds objects
        result1 = RungResult(
            rung_name="survey",
            slot_name="objects_found",
            value=5,
            confidence=0.6,
            raises_questions=[
                Question("q_control", "What do I control?", ["control_tracker"], priority=0.8)
            ]
        )
        visited.add("survey")

        transitions1 = tracker.update_from_rung_result(
            "survey", result1, blackboard, all_rungs, visited
        )

        # Should have question in KU
        assert "q_control" in tracker.current_state.known_unknowns

        # Step 2: Control tracker answers the question with high confidence
        tracker.current_state.uu_estimate = 0.3  # Simulate learning reduced UU
        result2 = RungResult(
            rung_name="control_tracker",
            slot_name="control_object",
            value="blue_square",
            confidence=0.9,
            answers_questions=["q_control"]
        )
        visited.add("control_tracker")

        transitions2 = tracker.update_from_rung_result(
            "control_tracker", result2, blackboard, all_rungs, visited
        )

        # Question should be answered, high KK
        assert "q_control" not in tracker.current_state.known_unknowns
        assert "control_object" in tracker.current_state.known_knowns

        # Step 3: Verify current algorithm
        if tracker.current_state.kk_confidence > 0.7:
            assert tracker.get_current_algorithm() == "GreedyExploitation"

    def test_contradiction_triggers_exclusion(self):
        """Test that contradiction properly updates detector and affects tracker."""
        tracker = EpistemicTracker()
        detector = ContradictionDetector()
        blackboard = Blackboard()

        # Set up initial high-confidence fact
        tracker.current_state.known_knowns["control_object"] = KnownFact(
            slot_name="control_object",
            value="blue_square",
            confidence=0.9,
            source_rung="control_tracker",
            verified_at=0
        )
        tracker.current_state.kk_confidence = 0.9
        tracker.current_state.primary_quadrant = RumsfeldQuadrant.KK

        # Detect contradiction
        contradiction = detector.check_contradiction(
            slot_name="control_object",
            old_fact=tracker.current_state.known_knowns["control_object"],
            new_value="red_circle",
            new_confidence=0.95,
            new_source_rung="new_tracker",
            path_so_far=["survey", "control_tracker"]
        )

        assert contradiction is not None
        assert contradiction.severity == ContradictionSeverity.SEVERE

        # Exclusions should include the failed path
        exclusions = detector.get_exclusion_list()
        assert "control_tracker" in exclusions

        # Target quadrant should be UU
        target = detector.get_target_quadrant(contradiction)
        assert target == RumsfeldQuadrant.UU


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
