"""
Tests for Phase 5: Validation & Testing.

Tests cover:
- Shadow testing infrastructure
- Routing metrics tracker
- A/B testing framework
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

import time
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from engines.cognition.ab_testing import (
    ABTestManager,
    PhaseConfig,
    PhaseMetrics,
    RolloutPhase,
    Variant,
)
from engines.cognition.routing_metrics import (
    AggregateMetrics,
    DecisionMetrics,
    MetricStatus,
    MetricTargets,
    RoutingMetricsTracker,
)
from engines.cognition.shadow_testing import (
    DivergenceRecord,
    DivergenceType,
    ShadowTestConfig,
    ShadowTester,
    ShadowTestResult,
)

# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def shadow_config():
    """Create shadow test config."""
    return ShadowTestConfig(
        confidence_delta_threshold=0.15,
        timing_ratio_threshold=3.0,
        log_all_divergences=True,
        store_to_database=False,
    )


@pytest.fixture
def shadow_tester(shadow_config):
    """Create shadow tester instance."""
    return ShadowTester(config=shadow_config)


@pytest.fixture
def metrics_tracker():
    """Create metrics tracker instance."""
    return RoutingMetricsTracker(window_size=100)


@pytest.fixture
def ab_manager():
    """Create A/B test manager instance."""
    return ABTestManager(initial_phase=RolloutPhase.PHASE_5A)


# =============================================================================
# SHADOW TESTING TESTS
# =============================================================================

class TestShadowTestConfig:
    """Tests for ShadowTestConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ShadowTestConfig()
        assert config.confidence_delta_threshold == 0.15
        assert config.timing_ratio_threshold == 3.0
        assert config.log_all_divergences is True
        assert config.store_to_database is True

    def test_custom_config(self, shadow_config):
        """Test custom configuration."""
        assert shadow_config.store_to_database is False


class TestDivergenceRecord:
    """Tests for DivergenceRecord."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        record = DivergenceRecord(
            timestamp="2026-02-04T12:00:00",
            game_id="test_game",
            agent_id="agent_1",
            divergence_type=DivergenceType.ACTION_MISMATCH,
            static_action="ACTION1",
            static_confidence=0.8,
            static_rungs_evaluated=20,
            static_latency_ms=50.0,
            cognitive_action="ACTION2",
            cognitive_confidence=0.9,
            cognitive_rungs_evaluated=10,
            cognitive_latency_ms=30.0,
            cognitive_algorithm="targeted_question",
            cognitive_quadrant="KU",
            severity="high",
            notes="Test divergence",
        )

        d = record.to_dict()
        assert d['game_id'] == "test_game"
        assert d['divergence_type'] == "action_mismatch"
        assert d['severity'] == "high"


class TestShadowTester:
    """Tests for ShadowTester."""

    def test_initialization(self, shadow_tester):
        """Test shadow tester initializes correctly."""
        assert shadow_tester._test_count == 0
        assert shadow_tester._divergence_count == 0
        assert len(shadow_tester._divergences) == 0

    def test_statistics_empty(self, shadow_tester):
        """Test statistics with no tests."""
        stats = shadow_tester.get_statistics()
        assert stats['test_count'] == 0
        assert stats['divergence_count'] == 0
        assert stats['divergence_rate'] == 0.0

    def test_analyze_divergence_no_divergence(self, shadow_tester):
        """Test divergence analysis when systems agree."""
        record = shadow_tester._analyze_divergence(
            game_id="test",
            agent_id="agent_1",
            static_action="ACTION1",
            static_confidence=0.8,
            static_rungs=15,
            static_latency=40.0,
            cognitive_result={
                'action': 'ACTION1',
                'confidence': 0.82,
                'iterations': 12,
                'algorithm': 'greedy',
                'quadrant': 'KK',
            },
            cognitive_latency=35.0,
        )

        assert record.divergence_type == DivergenceType.NO_DIVERGENCE

    def test_analyze_divergence_action_mismatch(self, shadow_tester):
        """Test divergence analysis with action mismatch."""
        record = shadow_tester._analyze_divergence(
            game_id="test",
            agent_id="agent_1",
            static_action="ACTION1",
            static_confidence=0.8,
            static_rungs=15,
            static_latency=40.0,
            cognitive_result={
                'action': 'ACTION2',  # Different action
                'confidence': 0.82,
                'iterations': 12,
                'algorithm': 'greedy',
                'quadrant': 'KK',
            },
            cognitive_latency=35.0,
        )

        assert record.divergence_type == DivergenceType.ACTION_MISMATCH
        assert record.severity == "high"

    def test_analyze_divergence_confidence_delta(self, shadow_tester):
        """Test divergence analysis with confidence delta."""
        record = shadow_tester._analyze_divergence(
            game_id="test",
            agent_id="agent_1",
            static_action="ACTION1",
            static_confidence=0.8,
            static_rungs=15,
            static_latency=40.0,
            cognitive_result={
                'action': 'ACTION1',
                'confidence': 0.5,  # 0.3 delta > 0.15 threshold
                'iterations': 12,
                'algorithm': 'greedy',
                'quadrant': 'KK',
            },
            cognitive_latency=35.0,
        )

        assert record.divergence_type == DivergenceType.CONFIDENCE_DELTA
        assert record.severity == "medium"

    def test_analyze_divergence_timing_anomaly(self, shadow_tester):
        """Test divergence analysis with timing anomaly."""
        record = shadow_tester._analyze_divergence(
            game_id="test",
            agent_id="agent_1",
            static_action="ACTION1",
            static_confidence=0.8,
            static_rungs=15,
            static_latency=10.0,
            cognitive_result={
                'action': 'ACTION1',
                'confidence': 0.8,
                'iterations': 15,
                'algorithm': 'greedy',
                'quadrant': 'KK',
            },
            cognitive_latency=100.0,  # 10x slower > 3x threshold
        )

        assert record.divergence_type == DivergenceType.TIMING_ANOMALY
        assert record.severity == "low"

    def test_reset_statistics(self, shadow_tester):
        """Test resetting statistics."""
        # Manually add some data
        shadow_tester._test_count = 10
        shadow_tester._divergence_count = 2

        shadow_tester.reset_statistics()

        assert shadow_tester._test_count == 0
        assert shadow_tester._divergence_count == 0

    def test_get_recent_divergences(self, shadow_tester):
        """Test getting recent divergences."""
        # Add some divergences
        for i in range(15):
            record = DivergenceRecord(
                timestamp=f"2026-02-04T12:{i:02d}:00",
                game_id=f"game_{i}",
                agent_id="agent_1",
                divergence_type=DivergenceType.ACTION_MISMATCH,
                static_action="ACTION1",
                static_confidence=0.8,
                static_rungs_evaluated=20,
                static_latency_ms=50.0,
                cognitive_action="ACTION2",
                cognitive_confidence=0.9,
                cognitive_rungs_evaluated=10,
                cognitive_latency_ms=30.0,
                cognitive_algorithm="greedy",
                cognitive_quadrant="KK",
            )
            shadow_tester._divergences.append(record)

        recent = shadow_tester.get_recent_divergences(5)
        assert len(recent) == 5
        assert recent[-1].game_id == "game_14"


# =============================================================================
# ROUTING METRICS TESTS
# =============================================================================

class TestMetricTargets:
    """Tests for MetricTargets."""

    def test_default_targets(self):
        """Test default target values."""
        targets = MetricTargets()
        assert targets.avg_rungs_evaluated == 15.0
        assert targets.decision_latency_ms == 50.0
        assert targets.first_win_rate == 0.60
        assert targets.backtracking_rate == 0.05
        assert targets.contradiction_detection == 0.80


class TestRoutingMetricsTracker:
    """Tests for RoutingMetricsTracker."""

    def test_initialization(self, metrics_tracker):
        """Test metrics tracker initializes correctly."""
        assert metrics_tracker._total_decisions == 0
        assert len(metrics_tracker._decisions) == 0

    def test_record_decision(self, metrics_tracker):
        """Test recording a decision."""
        metrics_tracker.record_decision(
            rungs_evaluated=12,
            latency_ms=35.0,
            first_win=True,
            backtracked=False,
            game_id="test_game",
            algorithm_used="greedy",
        )

        assert metrics_tracker._total_decisions == 1
        assert len(metrics_tracker._decisions) == 1
        assert metrics_tracker._first_wins == 1

    def test_get_metrics_empty(self, metrics_tracker):
        """Test getting metrics with no data."""
        metrics = metrics_tracker.get_metrics()
        assert metrics.decision_count == 0
        assert metrics.avg_rungs_evaluated == 0

    def test_get_metrics_with_data(self, metrics_tracker):
        """Test getting metrics with data."""
        # Record 10 decisions
        for i in range(10):
            metrics_tracker.record_decision(
                rungs_evaluated=10 + i,
                latency_ms=30.0 + i * 2,
                first_win=(i % 2 == 0),  # 50% first wins
                backtracked=(i % 5 == 0),  # 20% backtracking
                game_id=f"game_{i}",
            )

        metrics = metrics_tracker.get_metrics()
        assert metrics.decision_count == 10
        assert metrics.avg_rungs_evaluated == 14.5  # mean of 10-19
        assert metrics.first_win_rate == 0.5
        assert metrics.backtracking_rate == 0.2

    def test_rungs_histogram(self, metrics_tracker):
        """Test rungs histogram computation."""
        # Add decisions with various rung counts
        for rungs in [3, 7, 12, 18, 25]:
            metrics_tracker.record_decision(
                rungs_evaluated=rungs,
                latency_ms=30.0,
            )

        metrics = metrics_tracker.get_metrics()
        assert metrics.rungs_histogram["1-5"] == 1
        assert metrics.rungs_histogram["6-10"] == 1
        assert metrics.rungs_histogram["11-15"] == 1
        assert metrics.rungs_histogram["16-20"] == 1
        assert metrics.rungs_histogram["21+"] == 1

    def test_latency_histogram(self, metrics_tracker):
        """Test latency histogram computation."""
        for latency in [5.0, 15.0, 35.0, 75.0, 150.0]:
            metrics_tracker.record_decision(
                rungs_evaluated=10,
                latency_ms=latency,
            )

        metrics = metrics_tracker.get_metrics()
        assert metrics.latency_histogram["0-10"] == 1
        assert metrics.latency_histogram["10-25"] == 1
        assert metrics.latency_histogram["25-50"] == 1
        assert metrics.latency_histogram["50-100"] == 1
        assert metrics.latency_histogram["100+"] == 1

    def test_metric_status_excellent(self, metrics_tracker):
        """Test metric status when excellent."""
        # Record decisions with very good metrics
        for _ in range(10):
            metrics_tracker.record_decision(
                rungs_evaluated=5,  # Way below 15 target
                latency_ms=10.0,    # Way below 50ms target
                first_win=True,
            )

        assert metrics_tracker.get_metric_status('rungs') == MetricStatus.EXCELLENT
        assert metrics_tracker.get_metric_status('latency') == MetricStatus.EXCELLENT

    def test_metric_status_critical(self, metrics_tracker):
        """Test metric status when critical."""
        for _ in range(10):
            metrics_tracker.record_decision(
                rungs_evaluated=25,   # Way above 15 target
                latency_ms=100.0,     # Way above 50ms target
                first_win=False,
            )

        assert metrics_tracker.get_metric_status('rungs') == MetricStatus.CRITICAL
        assert metrics_tracker.get_metric_status('latency') == MetricStatus.CRITICAL

    def test_is_ready_for_rollout_yes(self, metrics_tracker):
        """Test rollout readiness when metrics are good."""
        for _ in range(10):
            metrics_tracker.record_decision(
                rungs_evaluated=10,
                latency_ms=30.0,
                first_win=True,
                backtracked=False,
                contradictions_detected=1,
                contradictions_actual=1,
            )

        ready, issues = metrics_tracker.is_ready_for_rollout()
        assert ready is True
        assert len(issues) == 0

    def test_is_ready_for_rollout_no(self, metrics_tracker):
        """Test rollout readiness when metrics are bad."""
        for _ in range(10):
            metrics_tracker.record_decision(
                rungs_evaluated=25,     # Too high
                latency_ms=100.0,       # Too slow
                first_win=False,        # No first wins
                backtracked=True,       # Always backtracking
            )

        ready, issues = metrics_tracker.is_ready_for_rollout()
        assert ready is False
        assert len(issues) > 0

    def test_per_game_metrics(self, metrics_tracker):
        """Test per-game metrics."""
        # Record decisions for two games
        for i in range(5):
            metrics_tracker.record_decision(
                rungs_evaluated=10,
                latency_ms=30.0,
                game_id="game_a",
            )
            metrics_tracker.record_decision(
                rungs_evaluated=20,
                latency_ms=60.0,
                game_id="game_b",
            )

        metrics_a = metrics_tracker.get_game_metrics("game_a")
        metrics_b = metrics_tracker.get_game_metrics("game_b")

        assert metrics_a.avg_rungs_evaluated == 10
        assert metrics_b.avg_rungs_evaluated == 20

    def test_per_algorithm_metrics(self, metrics_tracker):
        """Test per-algorithm metrics."""
        for i in range(5):
            metrics_tracker.record_decision(
                rungs_evaluated=8,
                latency_ms=20.0,
                algorithm_used="greedy",
            )
            metrics_tracker.record_decision(
                rungs_evaluated=15,
                latency_ms=50.0,
                algorithm_used="landmark_astar",
            )

        greedy_metrics = metrics_tracker.get_algorithm_metrics("greedy")
        astar_metrics = metrics_tracker.get_algorithm_metrics("landmark_astar")

        assert greedy_metrics.avg_rungs_evaluated == 8
        assert astar_metrics.avg_rungs_evaluated == 15

    def test_reset(self, metrics_tracker):
        """Test resetting tracker."""
        for _ in range(5):
            metrics_tracker.record_decision(
                rungs_evaluated=10,
                latency_ms=30.0,
            )

        metrics_tracker.reset()

        assert metrics_tracker._total_decisions == 0
        assert len(metrics_tracker._decisions) == 0


# =============================================================================
# A/B TESTING TESTS
# =============================================================================

class TestPhaseConfig:
    """Tests for PhaseConfig."""

    def test_phase_5a_config(self):
        """Test Phase 5a configuration."""
        config = PhaseConfig.phase_5a()
        assert config.phase == RolloutPhase.PHASE_5A
        assert config.cognitive_percentage == 0.10
        assert config.min_games_before_promotion == 100

    def test_phase_5b_config(self):
        """Test Phase 5b configuration."""
        config = PhaseConfig.phase_5b()
        assert config.phase == RolloutPhase.PHASE_5B
        assert config.cognitive_percentage == 0.50
        assert config.min_games_before_promotion == 500

    def test_phase_5c_config(self):
        """Test Phase 5c configuration."""
        config = PhaseConfig.phase_5c()
        assert config.phase == RolloutPhase.PHASE_5C
        assert config.cognitive_percentage == 1.00


class TestABTestManager:
    """Tests for ABTestManager."""

    def test_initialization(self, ab_manager):
        """Test A/B manager initializes correctly."""
        assert ab_manager._current_phase == RolloutPhase.PHASE_5A
        assert ab_manager._killed is False

    def test_hash_deterministic(self, ab_manager):
        """Test game_id hashing is deterministic."""
        hash1 = ab_manager._hash_game_id("test_game_123")
        hash2 = ab_manager._hash_game_id("test_game_123")
        assert hash1 == hash2

    def test_hash_in_range(self, ab_manager):
        """Test hash values are in [0, 1] range."""
        for i in range(100):
            hash_val = ab_manager._hash_game_id(f"game_{i}")
            assert 0 <= hash_val <= 1

    def test_use_cognitive_deterministic(self, ab_manager):
        """Test variant assignment is deterministic."""
        game_id = "test_game_xyz"
        result1 = ab_manager.use_cognitive(game_id)
        result2 = ab_manager.use_cognitive(game_id)
        assert result1 == result2

    def test_use_cognitive_distribution(self, ab_manager):
        """Test roughly 10% get cognitive in phase 5a."""
        cognitive_count = 0
        total = 1000

        for i in range(total):
            if ab_manager.use_cognitive(f"game_{i}"):
                cognitive_count += 1

        # Should be around 10% (allow 5-15% range)
        rate = cognitive_count / total
        assert 0.05 <= rate <= 0.15

    def test_get_variant(self, ab_manager):
        """Test get_variant returns correct enum."""
        game_id = "test_game"
        variant = ab_manager.get_variant(game_id)
        assert variant in [Variant.STATIC, Variant.COGNITIVE]

    def test_record_game_result(self, ab_manager):
        """Test recording game result."""
        ab_manager.record_game_result(
            game_id="test",
            variant=Variant.COGNITIVE,
            rungs_evaluated=10,
            latency_ms=30.0,
            first_win=True,
            backtracked=False,
        )

        assert ab_manager._games_this_phase == 1
        assert ab_manager._cognitive_games == 1

    def test_get_phase_metrics(self, ab_manager):
        """Test getting phase metrics."""
        # Record some results
        for i in range(10):
            ab_manager.record_game_result(
                game_id=f"game_{i}",
                variant=Variant.COGNITIVE,
                rungs_evaluated=10,
                latency_ms=30.0,
                first_win=(i < 7),  # 70% first wins
                backtracked=False,
            )

        metrics = ab_manager.get_phase_metrics()
        assert metrics.games_played == 10
        assert metrics.cognitive_games == 10
        assert metrics.cognitive_first_win_rate == 0.7

    def test_maybe_promote_not_enough_games(self, ab_manager):
        """Test promotion blocked by insufficient games."""
        promoted, reason = ab_manager.maybe_promote()
        assert promoted is False
        assert "more games" in reason

    def test_maybe_promote_metrics_not_met(self, ab_manager):
        """Test promotion blocked by bad metrics."""
        # Record 100 games with bad metrics
        for i in range(100):
            ab_manager.record_game_result(
                game_id=f"game_{i}",
                variant=Variant.COGNITIVE,
                rungs_evaluated=25,  # Too high
                latency_ms=100.0,    # Too slow
                first_win=False,
                backtracked=True,
            )

        promoted, reason = ab_manager.maybe_promote()
        assert promoted is False
        assert "Metrics not met" in reason

    def test_maybe_promote_success(self, ab_manager):
        """Test successful promotion."""
        # Record 100 games with good metrics
        for i in range(100):
            ab_manager.record_game_result(
                game_id=f"game_{i}",
                variant=Variant.COGNITIVE,
                rungs_evaluated=10,
                latency_ms=30.0,
                first_win=True,
                backtracked=False,
                had_divergence=False,
            )

        promoted, reason = ab_manager.maybe_promote()
        assert promoted is True
        assert ab_manager._current_phase == RolloutPhase.PHASE_5B

    def test_force_promote(self, ab_manager):
        """Test force promotion."""
        ab_manager.force_promote(RolloutPhase.PHASE_5C)
        assert ab_manager._current_phase == RolloutPhase.PHASE_5C

    def test_rollback(self, ab_manager):
        """Test rollback."""
        ab_manager.force_promote(RolloutPhase.PHASE_5B)
        ab_manager.rollback("Test rollback")
        assert ab_manager._current_phase == RolloutPhase.PHASE_5A

    def test_rollback_at_initial_phase(self, ab_manager):
        """Test rollback at initial phase does nothing."""
        ab_manager.rollback()
        assert ab_manager._current_phase == RolloutPhase.PHASE_5A

    def test_kill_switch(self, ab_manager):
        """Test kill switch."""
        ab_manager.kill("Emergency!")

        assert ab_manager._killed is True
        assert ab_manager._current_phase == RolloutPhase.KILLED
        assert ab_manager.use_cognitive("any_game") is False

    def test_resurrect(self, ab_manager):
        """Test resurrection after kill."""
        ab_manager.kill("Emergency!")
        ab_manager.resurrect(RolloutPhase.PHASE_5A)

        assert ab_manager._killed is False
        assert ab_manager._current_phase == RolloutPhase.PHASE_5A

    def test_get_status(self, ab_manager):
        """Test getting status."""
        status = ab_manager.get_status()

        assert 'current_phase' in status
        assert 'cognitive_percentage' in status
        assert 'is_killed' in status
        assert 'metrics' in status


class TestPhaseMetrics:
    """Tests for PhaseMetrics."""

    def test_meets_thresholds_pass(self):
        """Test thresholds met."""
        metrics = PhaseMetrics(
            phase=RolloutPhase.PHASE_5A,
            games_played=100,
            cognitive_games=10,
            static_games=90,
            cognitive_avg_rungs=10.0,
            cognitive_avg_latency=30.0,
            cognitive_first_win_rate=0.7,
            cognitive_backtrack_rate=0.02,
            divergence_rate=0.05,
            cognitive_better_count=0,
            static_better_count=0,
        )

        thresholds = {
            'avg_rungs_evaluated': 15.0,
            'avg_latency_ms': 50.0,
            'first_win_rate': 0.60,
            'backtracking_rate': 0.05,
            'divergence_rate': 0.10,
        }

        meets, issues = metrics.meets_thresholds(thresholds)
        assert meets is True
        assert len(issues) == 0

    def test_meets_thresholds_fail(self):
        """Test thresholds not met."""
        metrics = PhaseMetrics(
            phase=RolloutPhase.PHASE_5A,
            games_played=100,
            cognitive_games=10,
            static_games=90,
            cognitive_avg_rungs=20.0,  # Too high
            cognitive_avg_latency=60.0,  # Too slow
            cognitive_first_win_rate=0.5,  # Too low
            cognitive_backtrack_rate=0.1,  # Too high
            divergence_rate=0.15,  # Too high
            cognitive_better_count=0,
            static_better_count=0,
        )

        thresholds = {
            'avg_rungs_evaluated': 15.0,
            'avg_latency_ms': 50.0,
            'first_win_rate': 0.60,
            'backtracking_rate': 0.05,
            'divergence_rate': 0.10,
        }

        meets, issues = metrics.meets_thresholds(thresholds)
        assert meets is False
        assert len(issues) == 5


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestPhase5Integration:
    """Integration tests for Phase 5 components."""

    def test_shadow_with_metrics(self, shadow_tester, metrics_tracker):
        """Test shadow testing integrated with metrics."""
        # Simulate a divergence being recorded
        record = shadow_tester._analyze_divergence(
            game_id="test",
            agent_id="agent",
            static_action="ACTION1",
            static_confidence=0.8,
            static_rungs=15,
            static_latency=40.0,
            cognitive_result={
                'action': 'ACTION1',
                'confidence': 0.85,
                'iterations': 10,
                'algorithm': 'greedy',
                'quadrant': 'KK',
            },
            cognitive_latency=30.0,
        )

        # Record in metrics
        metrics_tracker.record_decision(
            rungs_evaluated=10,
            latency_ms=30.0,
            first_win=True,
            backtracked=False,
            game_id="test",
            algorithm_used="greedy",
        )

        metrics = metrics_tracker.get_metrics()
        assert metrics.decision_count == 1

    def test_ab_with_metrics_promotion(self, ab_manager, metrics_tracker):
        """Test A/B manager uses metrics for promotion."""
        # Record good results
        for i in range(100):
            variant = ab_manager.get_variant(f"game_{i}")

            metrics_tracker.record_decision(
                rungs_evaluated=10,
                latency_ms=30.0,
                first_win=True,
                game_id=f"game_{i}",
            )

            ab_manager.record_game_result(
                game_id=f"game_{i}",
                variant=variant,
                rungs_evaluated=10,
                latency_ms=30.0,
                first_win=True,
                backtracked=False,
            )

        # Both should show good status
        ready, _ = metrics_tracker.is_ready_for_rollout()
        promoted, _ = ab_manager.maybe_promote()

        assert ready is True
        assert promoted is True

    def test_full_workflow(self, shadow_tester, metrics_tracker, ab_manager):
        """Test full Phase 5 workflow."""
        # Simulate 10 games
        for i in range(10):
            game_id = f"game_{i}"

            # Get variant
            use_cognitive = ab_manager.use_cognitive(game_id)
            variant = Variant.COGNITIVE if use_cognitive else Variant.STATIC

            # Simulate decision
            rungs = 10 if use_cognitive else 20
            latency = 30.0 if use_cognitive else 50.0

            # Record metrics
            metrics_tracker.record_decision(
                rungs_evaluated=rungs,
                latency_ms=latency,
                first_win=True,
                game_id=game_id,
            )

            # Record A/B result
            ab_manager.record_game_result(
                game_id=game_id,
                variant=variant,
                rungs_evaluated=rungs,
                latency_ms=latency,
                first_win=True,
                backtracked=False,
            )

        # Verify everything recorded
        assert metrics_tracker._total_decisions == 10
        assert ab_manager._games_this_phase == 10

        # Get combined status
        status = ab_manager.get_status()
        metrics = metrics_tracker.get_metrics()

        assert status['games_this_phase'] == 10
        assert metrics.decision_count == 10
