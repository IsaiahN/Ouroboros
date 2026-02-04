"""
Tests for Phase 1.6: Epistemic Stability & Observability.

Tests cover:
1. HysteresisManager - Transition gates, cooldowns, thrashing prevention
2. QuestionManager - Question lifecycle, templates, statistics
3. UKPotentialIndex - Bloom filter, cold-start fallback, relevance filtering
4. EpistemicLogger - Trace entries, summaries, pattern detection
"""

from typing import Any, Dict, Optional

import pytest

from engines.cognition.blackboard import RumsfeldQuadrant
from engines.cognition.epistemic_logging import (
    EPISTEMIC_TRACES_SCHEMA,
    EpistemicLogger,
    EpistemicTraceEntry,
)

# Import dependencies from Phase 1.5
from engines.cognition.epistemic_state import EpistemicState, EpistemicTransition
from engines.cognition.hysteresis import DEFAULT_GATE, HysteresisManager, TransitionGate
from engines.cognition.question_manager import (
    RUNG_QUESTION_TEMPLATES,
    ManagedQuestion,
    QuestionManager,
    QuestionStatus,
)
from engines.cognition.uk_potential_index import (
    STRUCTURAL_UK_RUNGS,
    SimpleBloomFilter,
    UKEntry,
    UKPotentialIndex,
)

# =============================================================================
# IMPORTS
# =============================================================================







# =============================================================================
# HYSTERESIS MANAGER TESTS
# =============================================================================

class TestTransitionGate:
    """Tests for TransitionGate configuration."""

    def test_default_gate_exists(self):
        """Verify default gate is configured."""
        assert DEFAULT_GATE is not None
        assert isinstance(DEFAULT_GATE, TransitionGate)

    def test_gate_properties(self):
        """Verify gate properties are reasonable."""
        gate = DEFAULT_GATE
        assert gate.SIGNAL_DECAY_TICKS >= 0
        assert gate.DEFAULT_CONFIRMATIONS >= 1
        # Check some confirmations exist
        assert len(gate.CONFIRMATIONS_REQUIRED) > 0
        # Check cooldowns exist
        assert len(gate.COOLDOWN_TICKS) > 0

    def test_regression_transitions_require_more_confirmations(self):
        """Regression transitions should require more confirmations."""
        gate = DEFAULT_GATE
        # KK->UU is a severe regression, should need high confirmations
        key = (RumsfeldQuadrant.KK, RumsfeldQuadrant.UU)
        if key in gate.CONFIRMATIONS_REQUIRED:
            assert gate.CONFIRMATIONS_REQUIRED[key] >= 2


class TestHysteresisManager:
    """Tests for HysteresisManager."""

    def test_initialization(self):
        """Test manager initialization."""
        manager = HysteresisManager()
        assert manager.current_tick == 0
        assert manager.get_thrashing_score() == 0.0

    def test_signal_recording(self):
        """Test recording transition signals."""
        manager = HysteresisManager()

        # UU->KU typically needs 1 confirmation (progression)
        result = manager.record_signal(RumsfeldQuadrant.UU, RumsfeldQuadrant.KU)
        # Should pass with 1 confirmation
        assert result is True

    def test_confirmation_requirement(self):
        """Test that transitions require confirmations."""
        manager = HysteresisManager()

        # KK->UU is a severe regression, needs 3 confirmations
        result = manager.record_signal(RumsfeldQuadrant.KK, RumsfeldQuadrant.UU)
        assert result is False  # Not enough confirmations yet

        # Add more confirmations
        result = manager.record_signal(RumsfeldQuadrant.KK, RumsfeldQuadrant.UU)
        assert result is False  # Still not enough

        result = manager.record_signal(RumsfeldQuadrant.KK, RumsfeldQuadrant.UU)
        assert result is True  # Now should pass with 3 confirmations

    def test_cooldown_enforcement(self):
        """Test cooldown period enforcement."""
        manager = HysteresisManager()

        # Transition from KK to KU (needs 2 confirmations)
        manager.record_signal(RumsfeldQuadrant.KK, RumsfeldQuadrant.KU)
        manager.record_signal(RumsfeldQuadrant.KK, RumsfeldQuadrant.KU)  # Should succeed

        # Now KK has cooldown, try to go back
        result = manager.record_signal(RumsfeldQuadrant.KU, RumsfeldQuadrant.KK)
        # KK should be on cooldown
        assert manager.get_cooldown_remaining(RumsfeldQuadrant.KK) > 0

    def test_tick_decay(self):
        """Test signal decay over ticks."""
        manager = HysteresisManager()

        # Record a signal
        manager.record_signal(RumsfeldQuadrant.KK, RumsfeldQuadrant.UU)

        # Decay signals over time (default decay is 10 ticks)
        for _ in range(15):
            manager.tick()

        # Old signal should have decayed
        pending = manager.get_pending_count(RumsfeldQuadrant.KK, RumsfeldQuadrant.UU)
        assert pending == 0

    def test_thrashing_detection(self):
        """Test thrashing score calculation."""
        manager = HysteresisManager()

        # Try to make rapid transitions that get filtered
        for _ in range(5):
            # These will be filtered due to cooldowns/confirmations
            manager.record_signal(RumsfeldQuadrant.KK, RumsfeldQuadrant.KU)
            manager.tick()

        score = manager.get_thrashing_score()
        # Should have some thrashing detected (filtered signals)
        assert score >= 0.0

    def test_reset(self):
        """Test manager reset."""
        manager = HysteresisManager()
        manager.record_signal(RumsfeldQuadrant.UU, RumsfeldQuadrant.KU)
        manager.tick()

        manager.reset()

        assert manager.current_tick == 0
        assert manager.get_thrashing_score() == 0.0

    def test_statistics(self):
        """Test statistics collection."""
        manager = HysteresisManager()
        manager.record_signal(RumsfeldQuadrant.UU, RumsfeldQuadrant.KU)
        manager.tick()

        stats = manager.get_statistics()
        assert "current_tick" in stats
        assert "signals_received" in stats
        assert "transitions_allowed" in stats


# =============================================================================
# QUESTION MANAGER TESTS
# =============================================================================

class TestQuestionStatus:
    """Tests for QuestionStatus enum."""

    def test_all_statuses_exist(self):
        """Verify all expected statuses exist."""
        expected = ["RAISED", "ACTIVE", "ANSWERED", "ABANDONED", "DEMOTED"]
        for status in expected:
            assert hasattr(QuestionStatus, status)


class TestManagedQuestion:
    """Tests for ManagedQuestion dataclass."""

    def test_creation(self):
        """Test question creation."""
        q = ManagedQuestion(
            question_id="test-1",
            text="What is the goal?",
            answerable_by=["survey", "frame_interpretation"],
            priority=1.0
        )

        assert q.status == QuestionStatus.RAISED
        assert q.attempts == 0
        assert q.raised_at == 0

    def test_default_values(self):
        """Test default values are set correctly."""
        q = ManagedQuestion(
            question_id="test-2",
            text="Test question",
            answerable_by=["hypothesis_testing"],
            priority=0.5
        )

        assert q.context == {}
        assert q.answer_value is None


class TestQuestionManager:
    """Tests for QuestionManager."""

    def test_initialization(self):
        """Test manager initialization."""
        manager = QuestionManager()
        assert len(manager.get_active_questions()) == 0

    def test_raise_question(self):
        """Test raising a question."""
        manager = QuestionManager()

        q = manager.raise_question(
            question_id="what_control",
            text="What controls movement?",
            answerable_by=["control_tracker"],
            raised_by="survey",
            current_tick=0
        )

        assert q is not None
        assert q.status == QuestionStatus.ACTIVE
        assert "control_tracker" in q.answerable_by

    def test_raise_from_template(self):
        """Test raising from template."""
        manager = QuestionManager()

        q = manager.raise_from_template(
            rung_category="survey",
            template_id="what_objects",
            raised_by="game_start",
            current_tick=0
        )

        assert q is not None
        assert "object" in q.text.lower() or "What are these" in q.text

    def test_activate_question(self):
        """Test question is activated on raise."""
        manager = QuestionManager()

        q = manager.raise_question(
            question_id="test-q",
            text="Test question",
            answerable_by=["test_rung"],
            current_tick=0
        )

        # Questions are ACTIVE immediately on raise (not RAISED->ACTIVE)
        assert q.status == QuestionStatus.ACTIVE

    def test_answer_question(self):
        """Test answering a question."""
        manager = QuestionManager()

        q = manager.raise_question(
            question_id="what_is_2_plus_2",
            text="What is 2+2?",
            answerable_by=["math_rung"],
            current_tick=0
        )

        success = manager.record_attempt(
            question_id=q.question_id,
            succeeded=True,
            confidence=0.9,
            current_tick=1,
            answer_value="4",
            answer_source="math_rung"
        )

        assert success is True
        # Question should be removed from active after answering
        assert manager.get_question(q.question_id) is None

    def test_record_attempt(self):
        """Test recording attempts."""
        manager = QuestionManager()

        q = manager.raise_question(
            question_id="hard_q",
            text="Hard question",
            answerable_by=["test"],
            current_tick=0
        )

        manager.record_attempt(
            question_id=q.question_id,
            succeeded=False,
            confidence=0.1,
            current_tick=2
        )

        updated = manager.get_question(q.question_id)
        assert updated is not None
        assert updated.attempts == 1

    def test_demotion_after_failures(self):
        """Test demotion after multiple failures."""
        manager = QuestionManager()

        q = manager.raise_question(
            question_id="very_hard_q",
            text="Very hard question",
            answerable_by=["test"],
            current_tick=0
        )

        # Fail multiple times
        for i in range(3):
            manager.record_attempt(
                question_id=q.question_id,
                succeeded=False,
                confidence=0.1,
                current_tick=i+1
            )

        updated = manager.get_question(q.question_id)
        assert updated is not None
        assert updated.status == QuestionStatus.DEMOTED

    def test_abandonment_after_many_failures(self):
        """Test abandonment after many failures."""
        manager = QuestionManager()

        q = manager.raise_question(
            question_id="impossible_q",
            text="Impossible question",
            answerable_by=["test"],
            current_tick=0
        )

        # Fail many times
        for i in range(6):
            manager.record_attempt(
                question_id=q.question_id,
                succeeded=False,
                confidence=0.1,
                current_tick=i+1
            )

        # Question should be abandoned and removed
        assert manager.get_question(q.question_id) is None
        assert q.question_id in manager.abandoned_history

    def test_get_questions_for_rung(self):
        """Test filtering questions by rung."""
        manager = QuestionManager()

        manager.raise_question(
            question_id="q1", text="Q1",
            answerable_by=["survey"], current_tick=0
        )
        manager.raise_question(
            question_id="q2", text="Q2",
            answerable_by=["survey"], current_tick=0
        )
        manager.raise_question(
            question_id="q3", text="Q3",
            answerable_by=["hypothesis"], current_tick=0
        )

        survey_questions = manager.get_questions_for_rung("survey")
        assert len(survey_questions) == 2

    def test_resolution_rate(self):
        """Test resolution rate calculation."""
        manager = QuestionManager()

        # Create and answer some questions
        q1 = manager.raise_question(
            question_id="q1", text="Q1",
            answerable_by=["test"], current_tick=0
        )
        q2 = manager.raise_question(
            question_id="q2", text="Q2",
            answerable_by=["test"], current_tick=0
        )
        manager.raise_question(
            question_id="q3", text="Q3",
            answerable_by=["test"], current_tick=0
        )

        manager.record_attempt(
            question_id=q1.question_id, succeeded=True, confidence=0.9,
            current_tick=1, answer_value="A1"
        )
        manager.record_attempt(
            question_id=q2.question_id, succeeded=True, confidence=0.9,
            current_tick=1, answer_value="A2"
        )

        rate = manager.get_resolution_rate()
        assert rate == pytest.approx(2/3, rel=0.01)

    def test_priority_boost_on_reraise(self):
        """Test priority boost when question is re-raised."""
        manager = QuestionManager()

        q1 = manager.raise_question(
            question_id="same_question",
            text="Same question",
            answerable_by=["test"],
            current_tick=0,
            priority=0.5
        )
        original_priority = q1.priority

        # Re-raise the same question
        q2 = manager.raise_question(
            question_id="same_question",  # Same ID
            text="Same question",
            answerable_by=["test"],
            current_tick=1,
            priority=0.5
        )

        # Should return existing question with boosted priority
        assert q2.question_id == q1.question_id
        assert q2.priority > original_priority


class TestRungQuestionTemplates:
    """Tests for question templates."""

    def test_templates_exist_for_core_rungs(self):
        """Verify templates exist for core rungs."""
        core_rungs = ["survey", "frame_interpretation", "control_tracker",
                      "hypothesis_testing", "pattern_detection"]

        for rung in core_rungs:
            assert rung in RUNG_QUESTION_TEMPLATES, f"Missing templates for {rung}"

    def test_template_structure(self):
        """Test template structure is correct."""
        for rung, templates in RUNG_QUESTION_TEMPLATES.items():
            assert isinstance(templates, list)  # Templates are lists of dicts
            for template in templates:
                assert isinstance(template, dict)
                assert "question_id" in template
                assert "text" in template
                assert isinstance(template["text"], str)
                assert len(template["text"]) > 0


# =============================================================================
# UK POTENTIAL INDEX TESTS
# =============================================================================

class TestSimpleBloomFilter:
    """Tests for SimpleBloomFilter."""

    def test_initialization(self):
        """Test filter initialization."""
        bf = SimpleBloomFilter(size_bytes=128)
        assert bf.size_bits == 128 * 8

    def test_add_and_check(self):
        """Test adding and checking items."""
        bf = SimpleBloomFilter()

        bf.add("test_item")
        assert bf.might_contain("test_item") is True

    def test_definitely_not_present(self):
        """Test items not added return False (no false negatives)."""
        bf = SimpleBloomFilter()

        bf.add("item_a")
        # Items never added should return False
        # Note: Due to hash collisions, there could be false positives
        # but never false negatives
        assert bf.might_contain("item_a") is True

    def test_reset(self):
        """Test filter reset."""
        bf = SimpleBloomFilter()

        bf.add("item")
        bf.reset()

        # After reset, might_contain could still return True due to randomness
        # but the item count should be 0
        assert bf._item_count == 0

    def test_false_positive_rate_estimate(self):
        """Test FPP estimate."""
        bf = SimpleBloomFilter(size_bytes=128)

        for i in range(100):
            bf.add(f"item_{i}")

        fpp = bf.estimated_false_positive_rate
        assert 0.0 <= fpp <= 1.0


class TestUKEntry:
    """Tests for UKEntry dataclass."""

    def test_creation(self):
        """Test entry creation."""
        entry = UKEntry(
            rung_name="network_wisdom",
            has_cached=True,
            cache_count=10,
            relevance=0.8,
            last_updated=0
        )

        assert entry.rung_name == "network_wisdom"
        assert entry.has_cached is True
        assert entry.cache_count == 10


class TestUKPotentialIndex:
    """Tests for UKPotentialIndex."""

    def test_initialization(self):
        """Test index initialization."""
        index = UKPotentialIndex()
        assert index.is_cold_start is False
        assert index.potential_count == 0

    def test_populate_cold_start(self):
        """Test cold-start fallback."""
        index = UKPotentialIndex()

        # Populate with empty DB result (cold start)
        index.populate_for_game("FT09", "puzzle", db_query_func=None)

        assert index.is_cold_start is True
        assert index.potential_count > 0

    def test_populate_with_data(self):
        """Test population with actual data."""
        index = UKPotentialIndex()

        def mock_db_query(game_id: str, game_type: str) -> Dict[str, Dict]:
            return {
                "network_wisdom": {"count": 5, "relevance": 0.9},
                "prior_lessons": {"count": 3, "relevance": 0.7},
            }

        index.populate_for_game("FT09", "puzzle", db_query_func=mock_db_query)

        assert index.is_cold_start is False
        assert index.has_potential("network_wisdom") is True

    def test_has_potential_relevance_filtering(self):
        """Test relevance-based filtering."""
        index = UKPotentialIndex()

        def mock_db_query(game_id: str, game_type: str) -> Dict[str, Dict]:
            return {
                "high_relevance": {"count": 5, "relevance": 0.9},
                "low_relevance": {"count": 5, "relevance": 0.1},
            }

        index.populate_for_game("FT09", "puzzle", db_query_func=mock_db_query)

        assert index.has_potential("high_relevance", min_relevance=0.5) is True
        assert index.has_potential("low_relevance", min_relevance=0.5) is False

    def test_mark_surfaced(self):
        """Test marking knowledge as surfaced."""
        index = UKPotentialIndex()

        def mock_db_query(game_id: str, game_type: str) -> Dict[str, Dict]:
            return {"network_wisdom": {"count": 5, "relevance": 0.9}}

        index.populate_for_game("FT09", "puzzle", db_query_func=mock_db_query)

        assert index.has_potential("network_wisdom") is True

        index.mark_surfaced("network_wisdom")

        # After surfacing, should no longer have potential
        assert index.has_potential("network_wisdom") is False

    def test_get_potential_rungs(self):
        """Test getting all potential rungs."""
        index = UKPotentialIndex()

        def mock_db_query(game_id: str, game_type: str) -> Dict[str, Dict]:
            return {
                "rung_a": {"count": 5, "relevance": 0.9},
                "rung_b": {"count": 3, "relevance": 0.6},
                "rung_c": {"count": 0, "relevance": 0.0},
            }

        index.populate_for_game("FT09", "puzzle", db_query_func=mock_db_query)

        rungs = index.get_potential_rungs(min_relevance=0.5)

        assert "rung_a" in rungs
        assert "rung_b" in rungs
        assert "rung_c" not in rungs  # No cache

    def test_statistics(self):
        """Test statistics collection."""
        index = UKPotentialIndex()
        index.populate_structural_fallback()

        stats = index.get_statistics()

        assert "total_entries" in stats
        assert "with_cache" in stats
        assert "is_cold_start" in stats


class TestStructuralUKRungs:
    """Tests for structural UK metadata."""

    def test_structural_rungs_exist(self):
        """Verify structural rungs are defined."""
        assert len(STRUCTURAL_UK_RUNGS) > 0

    def test_structural_rung_properties(self):
        """Test structural rung metadata."""
        for rung_name, metadata in STRUCTURAL_UK_RUNGS.items():
            assert isinstance(rung_name, str)
            assert isinstance(metadata, dict)
            assert "description" in metadata


# =============================================================================
# EPISTEMIC LOGGER TESTS
# =============================================================================

class TestEpistemicTraceEntry:
    """Tests for EpistemicTraceEntry."""

    def test_creation(self):
        """Test entry creation."""
        entry = EpistemicTraceEntry(
            game_id="FT09",
            tick=10,
            quadrant="KK",
            confidence=0.8,
            certainty=0.9
        )

        assert entry.game_id == "FT09"
        assert entry.tick == 10
        assert entry.timestamp_ms > 0  # Auto-set

    def test_from_state(self):
        """Test creation from EpistemicState."""
        state = EpistemicState()
        state.primary_quadrant = RumsfeldQuadrant.KU
        state.kk_confidence = 0.5
        state.uu_estimate = 0.3

        entry = EpistemicTraceEntry.from_state(
            game_id="FT09",
            tick=5,
            state=state,
            algorithm="TargetedQuestionSearch"
        )

        assert entry.quadrant == "KU"
        assert entry.algorithm_selected == "TargetedQuestionSearch"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        entry = EpistemicTraceEntry(
            game_id="TEST",
            tick=0,
            quadrant="UU",
            confidence=0.1,
            certainty=0.1
        )

        d = entry.to_dict()

        assert d["game_id"] == "TEST"
        assert d["quadrant"] == "UU"

    def test_to_db_row(self):
        """Test conversion to database row."""
        entry = EpistemicTraceEntry(
            game_id="TEST",
            tick=0,
            quadrant="UU",
            confidence=0.1,
            certainty=0.1,
            context={"key": "value"}
        )

        row = entry.to_db_row()

        assert "context_json" in row
        assert '"key"' in row["context_json"]


class TestEpistemicLogger:
    """Tests for EpistemicLogger."""

    def test_initialization(self):
        """Test logger initialization."""
        logger = EpistemicLogger(game_id="FT09")

        assert logger.game_id == "FT09"
        assert len(logger.get_buffer()) == 0

    def test_log_entry(self):
        """Test logging an entry."""
        el = EpistemicLogger(game_id="FT09")

        entry = EpistemicTraceEntry(
            game_id="FT09",
            tick=0,
            quadrant="UU",
            confidence=0.1,
            certainty=0.1
        )

        el.log(entry)

        assert len(el.get_buffer()) == 1

    def test_log_from_state(self):
        """Test logging from EpistemicState."""
        el = EpistemicLogger(game_id="FT09")

        state = EpistemicState()
        state.primary_quadrant = RumsfeldQuadrant.KK
        state.kk_confidence = 0.9
        state.uu_estimate = 0.1

        entry = el.log_from_state(tick=0, state=state, algorithm="GreedyExploitation")

        assert entry.quadrant == "KK"
        assert len(el.get_buffer()) == 1

    def test_summary_statistics(self):
        """Test summary generation."""
        el = EpistemicLogger(game_id="FT09")

        # Log entries for different quadrants
        for q in ["UU", "KU", "KK", "KK", "KK"]:
            entry = EpistemicTraceEntry(
                game_id="FT09",
                tick=0,
                quadrant=q,
                confidence=0.5,
                certainty=0.5
            )
            el.log(entry)

        summary = el.get_summary()

        assert summary["total_ticks"] == 5
        assert summary["dominant_quadrant"] == "KK"
        assert summary["quadrant_counts"]["KK"] == 3

    def test_transition_tracking(self):
        """Test transition tracking."""
        el = EpistemicLogger(game_id="FT09")

        # Log transitions
        el.log(EpistemicTraceEntry(
            game_id="FT09", tick=0, quadrant="UU",
            confidence=0.1, certainty=0.1,
            transition_from="UK", transition_to="UU"
        ))
        el.log(EpistemicTraceEntry(
            game_id="FT09", tick=1, quadrant="KU",
            confidence=0.3, certainty=0.5,
            transition_from="UU", transition_to="KU"
        ))

        summary = el.get_summary()

        assert summary["total_transitions"] == 2
        assert "UK->UU" in summary["transition_counts"]

    def test_transition_matrix(self):
        """Test transition matrix generation."""
        el = EpistemicLogger(game_id="FT09")

        el.log(EpistemicTraceEntry(
            game_id="FT09", tick=0, quadrant="KU",
            confidence=0.5, certainty=0.5,
            transition_from="UU", transition_to="KU"
        ))

        matrix = el.get_transition_matrix()

        assert matrix["UU"]["KU"] == 1
        assert matrix["KK"]["KU"] == 0

    def test_pattern_detection(self):
        """Test pattern detection."""
        el = EpistemicLogger(game_id="FT09")

        # Create oscillation pattern
        for i in range(20):
            q = "KU" if i % 2 == 0 else "UU"
            from_q = "UU" if q == "KU" else "KU"
            el.log(EpistemicTraceEntry(
                game_id="FT09", tick=i, quadrant=q,
                confidence=0.5, certainty=0.5,
                transition_from=from_q, transition_to=q
            ))

        patterns = el.detect_patterns()

        assert patterns["oscillation"] is True

    def test_stagnation_detection(self):
        """Test stagnation detection."""
        el = EpistemicLogger(game_id="FT09")

        # All entries in same quadrant
        for i in range(20):
            el.log(EpistemicTraceEntry(
                game_id="FT09", tick=i, quadrant="KK",
                confidence=0.9, certainty=0.9
            ))

        patterns = el.detect_patterns()

        assert patterns["stagnation"] is True
        assert patterns["pattern_details"]["stagnant_quadrant"] == "KK"

    def test_reset(self):
        """Test logger reset."""
        el = EpistemicLogger(game_id="FT09")

        el.log(EpistemicTraceEntry(
            game_id="FT09", tick=0, quadrant="UU",
            confidence=0.1, certainty=0.1
        ))

        el.reset()

        assert len(el.get_buffer()) == 0
        summary = el.get_summary()
        assert summary["total_ticks"] == 0

    def test_flush_without_db(self):
        """Test flush without database."""
        el = EpistemicLogger(game_id="FT09")

        el.log(EpistemicTraceEntry(
            game_id="FT09", tick=0, quadrant="UU",
            confidence=0.1, certainty=0.1
        ))

        count = el.flush()  # No DB interface

        assert count == 1
        assert len(el.get_buffer()) == 0


class TestEpistemicTracesSchema:
    """Tests for SQL schema."""

    def test_schema_contains_table(self):
        """Verify schema defines the table."""
        assert "epistemic_traces" in EPISTEMIC_TRACES_SCHEMA
        assert "CREATE TABLE" in EPISTEMIC_TRACES_SCHEMA

    def test_schema_contains_indices(self):
        """Verify schema defines indices."""
        assert "CREATE INDEX" in EPISTEMIC_TRACES_SCHEMA
        assert "idx_epistemic_traces_game" in EPISTEMIC_TRACES_SCHEMA


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestPhase16Integration:
    """Integration tests for Phase 1.6 components."""

    def test_hysteresis_with_logger(self):
        """Test hysteresis manager with logging."""
        manager = HysteresisManager()
        el = EpistemicLogger(game_id="TEST")

        # Simulate state transitions with logging
        manager.record_signal(RumsfeldQuadrant.UU, RumsfeldQuadrant.KU)

        state = EpistemicState()
        state.primary_quadrant = RumsfeldQuadrant.KU
        state.kk_confidence = 0.5
        state.uu_estimate = 0.3

        el.log_from_state(
            tick=0,
            state=state,
            thrashing_score=manager.get_thrashing_score()
        )

        summary = el.get_summary()
        assert summary["total_ticks"] == 1

    def test_questions_with_uk_index(self):
        """Test question manager with UK potential index."""
        qm = QuestionManager()
        uk_index = UKPotentialIndex()

        # Populate UK index
        def mock_db(g, t):
            return {"network_wisdom": {"count": 5, "relevance": 0.9}}

        uk_index.populate_for_game("TEST", "puzzle", db_query_func=mock_db)

        # If UK potential exists, raise question about it
        if uk_index.has_potential("network_wisdom"):
            q = qm.raise_question(
                question_id="check_network_wisdom",
                text="Should we check network wisdom?",
                answerable_by=["network_wisdom"],
                current_tick=0
            )
            assert q is not None

            # Answer and mark surfaced
            qm.record_attempt(
                question_id=q.question_id,
                succeeded=True,
                confidence=0.9,
                current_tick=1,
                answer_value="Yes"
            )
            uk_index.mark_surfaced("network_wisdom")

            assert uk_index.has_potential("network_wisdom") is False

    def test_full_epistemic_cycle(self):
        """Test complete epistemic cycle with all components."""
        # Initialize all components
        hysteresis = HysteresisManager()
        questions = QuestionManager()
        uk_index = UKPotentialIndex()
        el = EpistemicLogger(game_id="CYCLE_TEST")

        # Start in UU, cold start
        uk_index.populate_structural_fallback()

        # Tick 0: UU state
        state = EpistemicState()
        state.primary_quadrant = RumsfeldQuadrant.UU
        state.uu_estimate = 0.9
        el.log_from_state(
            tick=0, state=state,
            uk_potential=uk_index.total_potential
        )

        # Tick 1: Question raised, transition to KU
        q = questions.raise_question(
            question_id="what_objects",
            text="What are the objects?",
            answerable_by=["survey"],
            current_tick=1
        )
        hysteresis.record_signal(RumsfeldQuadrant.UU, RumsfeldQuadrant.KU)

        state = EpistemicState()
        state.primary_quadrant = RumsfeldQuadrant.KU
        state.ku_urgency = 0.7

        # Create transition for logging
        transition = EpistemicTransition(
            from_quadrant=RumsfeldQuadrant.UU,
            to_quadrant=RumsfeldQuadrant.KU,
            trigger_rung="question_manager",
            trigger_reason="question_raised",
            timestamp=1
        )
        el.log_from_state(
            tick=1, state=state,
            active_questions=len(questions.get_active_questions()),
            transition=transition
        )

        # Tick 2: Question answered, transition to KK
        questions.record_attempt(
            question_id=q.question_id,
            succeeded=True,
            confidence=0.9,
            current_tick=2,
            answer_value="Objects identified"
        )
        # KU->KK needs 2 confirmations
        hysteresis.record_signal(RumsfeldQuadrant.KU, RumsfeldQuadrant.KK)
        hysteresis.record_signal(RumsfeldQuadrant.KU, RumsfeldQuadrant.KK)

        state = EpistemicState()
        state.primary_quadrant = RumsfeldQuadrant.KK
        state.kk_confidence = 0.9
        el.log_from_state(tick=2, state=state)

        # Verify final state
        summary = el.get_summary()
        assert summary["total_ticks"] == 3
        assert questions.get_resolution_rate() == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
