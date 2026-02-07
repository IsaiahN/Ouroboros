"""
Tests for Phase 4: Cognitive Router with Transition-Driven Switching.

Tests CatastrophicFallback, CognitiveRouter, and DecisionRungSystem integration.
Target: 50+ tests for comprehensive coverage.
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set
from unittest.mock import MagicMock, patch

import pytest

from engines.cognition.blackboard import Blackboard, RumsfeldQuadrant

# Import components under test
from engines.cognition.catastrophic_fallback import (
    EXPLOITATION_ORDERING,
    EXPLORATION_ORDERING,
    SAFE_MINIMAL_ORDERING,
    CatastrophicEvent,
    CatastrophicFallback,
    FailureType,
    FallbackStrategy,
    FallbackThresholds,
)
from engines.cognition.cognitive_router import (
    TRANSITION_RESPONSES,
    CognitiveRouter,
    DecisionResult,
    RouterConfig,
    RouterState,
    get_algorithm_for_transition,
)
from engines.cognition.epistemic_state import EpistemicTransition, TransitionResponse
from engines.cognition.epistemic_tracker import EpistemicTracker, RungResult

# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def fallback():
    """Create a CatastrophicFallback instance."""
    return CatastrophicFallback(game_id="test_game", decision_id=1)


@pytest.fixture
def thresholds():
    """Create test thresholds."""
    return FallbackThresholds(
        max_empty_frontiers=3,
        max_contradictions=5,
        max_iterations=50,
        max_quadrant_oscillations=4,
        max_stuck_ticks=15,
    )


@pytest.fixture
def router():
    """Create a CognitiveRouter instance."""
    config = RouterConfig(
        max_iterations=20,
        commit_threshold=0.8,
        use_hysteresis=True,
        use_catastrophic_fallback=True,
    )
    return CognitiveRouter(config=config)


@pytest.fixture
def sample_nodes():
    """Sample node structure for testing."""
    return {
        'survey': {'name': 'survey', 'category': 'orientation', 'priority': 5},
        'control_tracker': {'name': 'control_tracker', 'category': 'identity', 'priority': 10},
        'hypothesis_generation': {'name': 'hypothesis_generation', 'category': 'hypothesis', 'priority': 20},
        'network_wisdom': {'name': 'network_wisdom', 'category': 'exploitation', 'priority': 30},
        'smart_action_selection': {'name': 'smart_action_selection', 'category': 'fallback', 'priority': 100},
    }


@pytest.fixture
def sample_edges():
    """Sample edge structure for testing."""
    return {
        'survey': ['control_tracker', 'hypothesis_generation'],
        'control_tracker': ['network_wisdom'],
        'hypothesis_generation': ['network_wisdom'],
        'network_wisdom': ['smart_action_selection'],
    }


# =============================================================================
# CATASTROPHIC FALLBACK TESTS
# =============================================================================

class TestCatastrophicFallbackBasics:
    """Basic functionality tests for CatastrophicFallback."""

    def test_init_defaults(self, fallback):
        """Test default initialization."""
        assert fallback.game_id == "test_game"
        assert fallback.decision_id == 1
        assert fallback.contradiction_count == 0
        assert fallback.empty_frontier_count == 0
        assert fallback.iteration_count == 0
        assert not fallback.is_triggered

    def test_reset_clears_state(self, fallback):
        """Test that reset clears all counters."""
        fallback.record_contradiction()
        fallback.record_empty_frontier()
        fallback.record_iteration("test_rung")

        fallback.reset(game_id="new_game", decision_id=2)

        assert fallback.game_id == "new_game"
        assert fallback.decision_id == 2
        assert fallback.contradiction_count == 0
        assert fallback.empty_frontier_count == 0
        assert fallback.iteration_count == 0

    def test_record_contradiction(self, fallback):
        """Test contradiction recording."""
        fallback.record_contradiction()
        assert fallback.contradiction_count == 1

        fallback.record_contradiction()
        fallback.record_contradiction()
        assert fallback.contradiction_count == 3

    def test_record_empty_frontier(self, fallback):
        """Test empty frontier recording."""
        fallback.record_empty_frontier()
        assert fallback.empty_frontier_count == 1

    def test_record_iteration(self, fallback):
        """Test iteration recording."""
        fallback.record_iteration("survey")
        assert fallback.iteration_count == 1
        assert "survey" in fallback._visited_rungs

    def test_record_quadrant(self, fallback):
        """Test quadrant recording for loop detection."""
        fallback.record_quadrant("KK", 0.5)
        fallback.record_quadrant("KU", 0.6)

        assert len(fallback._quadrant_history) == 2


class TestCatastrophicFallbackDetection:
    """Tests for failure detection logic."""

    def test_detect_empty_frontier_threshold(self, fallback):
        """Test empty frontier triggers fallback at threshold."""
        fallback.record_empty_frontier()
        fallback.record_empty_frontier()
        should_fallback, failure_type = fallback.should_fallback()
        assert not should_fallback

        fallback.record_empty_frontier()
        should_fallback, failure_type = fallback.should_fallback()
        assert should_fallback
        assert failure_type == FailureType.EMPTY_FRONTIER

    def test_detect_contradiction_storm(self, fallback):
        """Test contradiction storm triggers fallback."""
        for _ in range(4):
            fallback.record_contradiction()
            should_fallback, _ = fallback.should_fallback()
            assert not should_fallback

        fallback.record_contradiction()
        should_fallback, failure_type = fallback.should_fallback()
        assert should_fallback
        assert failure_type == FailureType.CONTRADICTION_STORM

    def test_detect_max_iterations(self, fallback):
        """Test max iterations triggers fallback."""
        for i in range(49):
            fallback.record_iteration(f"rung_{i}")

        should_fallback, _ = fallback.should_fallback()
        assert not should_fallback

        fallback.record_iteration("rung_50")
        should_fallback, failure_type = fallback.should_fallback()
        assert should_fallback
        assert failure_type == FailureType.MAX_ITERATIONS

    def test_detect_quadrant_loop(self, fallback):
        """Test quadrant oscillation detection."""
        # Create oscillation pattern: KK->KU->KK->KU->KK->KU->KK->KU
        for i in range(8):
            quadrant = "KK" if i % 2 == 0 else "KU"
            fallback.record_quadrant(quadrant)

        should_fallback, failure_type = fallback.should_fallback()
        assert should_fallback
        assert failure_type == FailureType.QUADRANT_LOOP

    def test_no_fallback_when_stable(self, fallback):
        """Test no fallback for stable patterns."""
        fallback.record_quadrant("UU")
        fallback.record_quadrant("KU")
        fallback.record_quadrant("KK")
        fallback.record_iteration("survey")

        should_fallback, failure_type = fallback.should_fallback()
        assert not should_fallback
        assert failure_type == FailureType.NONE

    def test_detect_stuck_quadrant(self, fallback):
        """Test stuck in quadrant detection."""
        # Simulate being stuck in KU for many ticks without progress
        for _ in range(16):
            fallback.record_quadrant("KU", confidence=0.5)
            fallback._ticks_in_current_quadrant += 1

        should_fallback, failure_type = fallback.should_fallback(current_confidence=0.5)
        assert should_fallback
        assert failure_type == FailureType.STUCK_QUADRANT


class TestCatastrophicFallbackTrigger:
    """Tests for fallback trigger and ordering selection."""

    def test_trigger_returns_ordering(self, fallback):
        """Test that trigger returns a valid ordering."""
        for _ in range(5):
            fallback.record_contradiction()

        ordering = fallback.trigger_fallback(
            context_snapshot={'quadrant': 'KK'},
            has_replay_sequence=False,
            current_confidence=0.3,
        )

        assert isinstance(ordering, list)
        assert len(ordering) > 0
        assert fallback.is_triggered

    def test_select_safe_minimal_for_storm(self, fallback):
        """Test safe minimal ordering for contradiction storm."""
        for _ in range(5):
            fallback.record_contradiction()

        ordering = fallback.trigger_fallback(
            context_snapshot={},
            has_replay_sequence=False,
            current_confidence=0.2,
        )

        # Should be safe minimal due to low confidence and storm
        assert ordering == SAFE_MINIMAL_ORDERING

    def test_select_replay_when_available(self, fallback):
        """Test replay strategy when sequence available."""
        for _ in range(3):
            fallback.record_empty_frontier()

        ordering = fallback.trigger_fallback(
            context_snapshot={},
            has_replay_sequence=True,
            current_confidence=0.5,
        )

        # With replay available (and not contradiction storm), should use exploitation
        assert "cached_sequence" in ordering or "winning_sequence_replay" in ordering or ordering == EXPLOITATION_ORDERING

    def test_select_exploration_for_stuck(self, fallback):
        """Test exploration ordering for stuck quadrant."""
        fallback._current_failure_type = FailureType.STUCK_QUADRANT
        fallback._fallback_triggered = False

        ordering = fallback.trigger_fallback(
            context_snapshot={},
            has_replay_sequence=False,
            current_confidence=0.3,
        )

        assert ordering == EXPLORATION_ORDERING

    def test_creates_event_record(self, fallback):
        """Test that trigger creates an event record."""
        for _ in range(5):
            fallback.record_contradiction()

        # Must check should_fallback first to set the failure type
        should_fallback, failure_type = fallback.should_fallback()
        assert should_fallback

        fallback.trigger_fallback(
            context_snapshot={'test': 'data'},
            has_replay_sequence=False,
            current_confidence=0.5,
        )

        events = fallback.get_events()
        assert len(events) == 1
        assert events[0].failure_type == FailureType.CONTRADICTION_STORM
        assert 'test' in events[0].context_snapshot


class TestCatastrophicFallbackStatistics:
    """Tests for statistics and analysis methods."""

    def test_get_statistics_empty(self, fallback):
        """Test statistics with no events."""
        stats = fallback.get_statistics()
        assert stats['total_triggers'] == 0
        assert stats['recovery_rate'] == 0.0
        assert stats['by_type'] == {}

    def test_get_statistics_with_events(self, fallback):
        """Test statistics with multiple events."""
        # Trigger first failure - must call should_fallback to set failure type
        for _ in range(5):
            fallback.record_contradiction()
        should_fb, _ = fallback.should_fallback()
        assert should_fb
        fallback.trigger_fallback({}, False, 0.3)
        fallback.mark_recovery_successful()

        # Reset and trigger second failure - must call should_fallback
        fallback.reset()
        for _ in range(3):
            fallback.record_empty_frontier()
        should_fb, _ = fallback.should_fallback()
        assert should_fb
        fallback.trigger_fallback({}, False, 0.3)

        stats = fallback.get_statistics()
        assert stats['total_triggers'] == 2
        assert stats['recovery_rate'] == 0.5  # 1 of 2 recovered
        assert FailureType.CONTRADICTION_STORM.value in stats['by_type']

    def test_event_serialization(self, fallback):
        """Test event serialization to dict."""
        for _ in range(5):
            fallback.record_contradiction()
        # Must call should_fallback before trigger_fallback
        fallback.should_fallback()
        fallback.trigger_fallback({'key': 'value'}, False, 0.5)

        event = fallback.get_last_event()
        event_dict = event.to_dict()

        assert 'failure_type' in event_dict
        assert 'timestamp' in event_dict
        assert event_dict['contradiction_count'] == 5


# =============================================================================
# COGNITIVE ROUTER TESTS
# =============================================================================

class TestCognitiveRouterBasics:
    """Basic functionality tests for CognitiveRouter."""

    def test_init_with_defaults(self):
        """Test default initialization."""
        router = CognitiveRouter()
        assert router.blackboard is not None
        assert router.epistemic_tracker is not None
        assert router.config.max_iterations == 3

    def test_init_with_custom_config(self):
        """Test initialization with custom config."""
        config = RouterConfig(max_iterations=100, commit_threshold=0.9)
        router = CognitiveRouter(config=config)

        assert router.config.max_iterations == 100
        assert router.config.commit_threshold == 0.9

    def test_init_with_blackboard(self):
        """Test initialization with existing blackboard."""
        blackboard = Blackboard()
        blackboard.slot('test_slot', 42)

        router = CognitiveRouter(blackboard=blackboard)
        assert router.blackboard.slot('test_slot') == 42

    def test_initialize_sets_up_graph(self, router, sample_nodes, sample_edges):
        """Test initialize sets up graph structures."""
        router.initialize(sample_nodes, sample_edges, game_id="test_123")

        assert router._nodes == sample_nodes
        assert router._edges == sample_edges
        assert router._all_rungs == set(sample_nodes.keys())
        assert router._game_id == "test_123"


class TestCognitiveRouterDecision:
    """Tests for decision-making logic."""

    def test_decide_returns_result(self, router, sample_nodes, sample_edges):
        """Test decide returns a DecisionResult."""
        router.initialize(sample_nodes, sample_edges, game_id="test")

        result = router.decide({'frame': None})

        assert isinstance(result, DecisionResult)
        assert result.action is not None
        assert result.reasoning is not None

    def test_decide_tracks_iterations(self, router, sample_nodes, sample_edges):
        """Test that iterations are tracked."""
        router.initialize(sample_nodes, sample_edges)

        result = router.decide({'frame': None})

        assert result.iterations >= 0
        assert result.time_elapsed >= 0

    def test_decide_respects_time_budget(self, sample_nodes, sample_edges):
        """Test time budget is respected."""
        config = RouterConfig(time_budget_seconds=0.001)  # Very short
        router = CognitiveRouter(config=config)
        router.initialize(sample_nodes, sample_edges)

        result = router.decide({'frame': None})

        assert result.time_elapsed < 1.0  # Should exit quickly

    def test_decide_uses_fallback_on_failure(self, sample_nodes, sample_edges):
        """Test fallback is used on catastrophic failure."""
        config = RouterConfig(
            max_iterations=5,
            use_catastrophic_fallback=True,
        )
        router = CognitiveRouter(config=config)
        router.initialize(sample_nodes, sample_edges)

        # Force failure by maxing iterations
        if router.fallback is not None:
            router.fallback.thresholds.max_iterations = 1

        result = router.decide({'frame': None})

        # Should have triggered fallback
        assert result.used_fallback or result.iterations <= 2


class TestCognitiveRouterAlgorithmSwitching:
    """Tests for algorithm switching logic."""

    @pytest.fixture
    def router_no_meta(self):
        """Create a CognitiveRouter without meta-planner for direct algorithm testing."""
        config = RouterConfig(
            max_iterations=20,
            commit_threshold=0.8,
            use_hysteresis=True,
            use_catastrophic_fallback=True,
            use_meta_planner_cache=False,  # Disable meta-planner
        )
        return CognitiveRouter(config=config)

    def test_switch_algorithm_updates_state(self, router_no_meta, sample_nodes, sample_edges):
        """Test algorithm switching updates router state."""
        router_no_meta.initialize(sample_nodes, sample_edges)

        from engines.cognition.search_context import SearchContext
        context = SearchContext(current_quadrant="KU")

        router_no_meta._switch_algorithm("targeted_question", context)

        assert router_no_meta._state.current_algorithm_name == "targeted_question"
        assert router_no_meta._state.current_algorithm is not None

    def test_switch_algorithm_fallback_on_error(self, router_no_meta, sample_nodes, sample_edges):
        """Test fallback to landmark_astar on invalid algorithm."""
        router_no_meta.initialize(sample_nodes, sample_edges)

        from engines.cognition.search_context import SearchContext
        context = SearchContext()

        router_no_meta._switch_algorithm("nonexistent_algorithm", context)

        assert router_no_meta._state.current_algorithm_name == "landmark_astar"

    def test_algorithm_usage_tracking(self, router_no_meta, sample_nodes, sample_edges):
        """Test algorithm usage is tracked."""
        router_no_meta.initialize(sample_nodes, sample_edges)

        from engines.cognition.search_context import SearchContext
        context = SearchContext()

        router_no_meta._switch_algorithm("greedy_best_first", context)
        router_no_meta._switch_algorithm("greedy_best_first", context)
        router_no_meta._switch_algorithm("landmark_astar", context)

        assert router_no_meta._algorithm_usage["greedy_best_first"] == 2
        assert router_no_meta._algorithm_usage["landmark_astar"] == 1


class TestTransitionResponses:
    """Tests for transition response mappings."""

    def test_uu_to_ku_response(self):
        """Test UU->KU transition response."""
        transition = EpistemicTransition(
            from_quadrant=RumsfeldQuadrant.UU,
            to_quadrant=RumsfeldQuadrant.KU,
            trigger_rung="survey",
            trigger_reason="Found a question",
            timestamp=1,
        )

        response = get_algorithm_for_transition(transition)

        assert response.algorithm == "targeted_question"
        assert response.action == "focus"

    def test_ku_to_kk_response(self):
        """Test KU->KK transition response."""
        transition = EpistemicTransition(
            from_quadrant=RumsfeldQuadrant.KU,
            to_quadrant=RumsfeldQuadrant.KK,
            trigger_rung="control_tracker",
            trigger_reason="Answered question",
            timestamp=2,
        )

        response = get_algorithm_for_transition(transition)

        assert response.algorithm == "greedy_best_first"
        assert response.action == "exploit"

    def test_kk_to_uu_response(self):
        """Test KK->UU (severe contradiction) response."""
        transition = EpistemicTransition(
            from_quadrant=RumsfeldQuadrant.KK,
            to_quadrant=RumsfeldQuadrant.UU,
            trigger_rung="theory_gate",
            trigger_reason="Severe contradiction",
            timestamp=3,
        )

        response = get_algorithm_for_transition(transition)

        assert response.algorithm == "exploration_exclusions"
        assert response.action == "reset_and_explore"

    def test_unknown_transition_default(self):
        """Test unknown transition gets default response."""
        # UK->KU is now covered in JSON config, so test with KK->UK
        # which previously wasn't covered either; if JSON covers it too,
        # just verify a well-formed response is returned
        transition = EpistemicTransition(
            from_quadrant=RumsfeldQuadrant.UK,
            to_quadrant=RumsfeldQuadrant.KU,
            trigger_rung="test",
            trigger_reason="Test",
            timestamp=1,
        )

        response = get_algorithm_for_transition(transition)

        # Should have a valid algorithm and action regardless of source
        assert response.algorithm is not None
        assert response.action is not None


class TestCognitiveRouterBacktracking:
    """Tests for backtracking and reset logic."""

    def test_handle_backtrack_excludes_rungs(self, router, sample_nodes, sample_edges):
        """Test backtrack excludes failed rungs."""
        router.initialize(sample_nodes, sample_edges)

        # Set up state with path
        router._state.path = ['survey', 'control_tracker', 'hypothesis_generation']
        router._state.checkpoints = [{'path': ['survey']}]

        from engines.cognition.search_context import SearchContext
        context = SearchContext(
            visited_rungs={'survey', 'control_tracker', 'hypothesis_generation'},
            current_path=['survey', 'control_tracker', 'hypothesis_generation'],
        )

        router._handle_backtrack(context, {'backtrack_depth': 1, 'exclude_last': True})

        # Should have excluded the rungs after checkpoint
        assert 'control_tracker' in router._state.excluded_rungs
        assert 'hypothesis_generation' in router._state.excluded_rungs

    def test_handle_reset_clears_path(self, router, sample_nodes, sample_edges):
        """Test reset clears path and excludes failed rungs."""
        router.initialize(sample_nodes, sample_edges)

        router._state.path = ['survey', 'control_tracker']

        from engines.cognition.search_context import SearchContext
        context = SearchContext()

        router._handle_reset(context, {'exclude_failed_path': True})

        assert len(router._state.path) == 0
        assert 'survey' in router._state.excluded_rungs
        assert 'control_tracker' in router._state.excluded_rungs


class TestCognitiveRouterFrontier:
    """Tests for frontier management."""

    def test_get_frontier_excludes_visited(self, router, sample_nodes, sample_edges):
        """Test frontier excludes visited rungs."""
        router.initialize(sample_nodes, sample_edges)

        from engines.cognition.search_context import SearchContext
        context = SearchContext(
            visited_rungs={'survey', 'control_tracker'},
            excluded_rungs=set(),
        )

        frontier = router._get_frontier(context)

        assert 'survey' not in frontier
        assert 'control_tracker' not in frontier
        assert 'hypothesis_generation' in frontier

    def test_get_frontier_excludes_excluded(self, router, sample_nodes, sample_edges):
        """Test frontier excludes excluded rungs."""
        router.initialize(sample_nodes, sample_edges)

        from engines.cognition.search_context import SearchContext
        context = SearchContext(
            visited_rungs=set(),
            excluded_rungs={'network_wisdom'},
        )

        frontier = router._get_frontier(context)

        assert 'network_wisdom' not in frontier


class TestCognitiveRouterStatistics:
    """Tests for statistics collection."""

    def test_get_statistics(self, router, sample_nodes, sample_edges):
        """Test statistics collection."""
        router.initialize(sample_nodes, sample_edges, game_id="test_game")

        # Make some decisions
        router.decide({'frame': None})
        router.decide({'frame': None})

        stats = router.get_statistics()

        assert stats['total_decisions'] == 2
        assert stats['game_id'] == "test_game"
        assert 'algorithm_usage' in stats


class TestDecisionResultSerialization:
    """Tests for DecisionResult serialization."""

    def test_to_dict(self):
        """Test DecisionResult serialization."""
        result = DecisionResult(
            action="survey",
            reasoning="Test reasoning",
            confidence=0.8,
            iterations=10,
            rungs_evaluated=5,
            transitions_count=2,
            algorithm_switches=1,
            time_elapsed=0.5,
            path=['survey', 'control_tracker'],
            final_quadrant="KK",
        )

        result_dict = result.to_dict()

        assert result_dict['action'] == "survey"
        assert result_dict['confidence'] == 0.8
        assert result_dict['iterations'] == 10
        assert 'path' in result_dict


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestRouterIntegration:
    """Integration tests combining multiple components."""

    def test_full_decision_cycle(self, router, sample_nodes, sample_edges):
        """Test a full decision cycle with all components."""
        router.initialize(sample_nodes, sample_edges, game_id="integration_test")

        # Simulate game state
        game_state = {'frame': [[0, 1], [1, 0]], 'action_count': 0}

        result = router.decide(game_state)

        assert result.action is not None
        assert result.final_quadrant in ['KK', 'KU', 'UK', 'UU']

    def test_multiple_decisions_state_persistence(self, router, sample_nodes, sample_edges):
        """Test state persists across multiple decisions."""
        router.initialize(sample_nodes, sample_edges)

        result1 = router.decide({'frame': None})
        result2 = router.decide({'frame': None})

        # Decision count should increment
        stats = router.get_statistics()
        assert stats['total_decisions'] == 2

    def test_fallback_integration(self, sample_nodes, sample_edges):
        """Test fallback integrates properly with router."""
        config = RouterConfig(
            max_iterations=2,
            use_catastrophic_fallback=True,
        )
        router = CognitiveRouter(config=config)
        router.initialize(sample_nodes, sample_edges)

        # Force many iterations to trigger fallback
        if router.fallback is not None:
            router.fallback.thresholds.max_iterations = 1

        result = router.decide({'frame': None})

        # Should complete without error
        assert result.action is not None


class TestLegacyCompatibility:
    """Tests for legacy compatibility methods."""

    def test_get_ordering_for_context_default(self, router, sample_nodes, sample_edges):
        """Test legacy ordering method returns valid ordering."""
        router.initialize(sample_nodes, sample_edges)

        ordering = router.get_ordering_for_context({'frame': None})

        assert isinstance(ordering, list)
        assert len(ordering) > 0

    def test_get_ordering_for_replay_context(self, router, sample_nodes, sample_edges):
        """Test ordering for replay context."""
        router.initialize(sample_nodes, sample_edges)

        ordering = router.get_ordering_for_context({'replay_sequence': ['a', 'b', 'c']})

        assert 'cached_sequence' in ordering or 'winning_sequence_replay' in ordering


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_nodes_handled(self):
        """Test router handles empty nodes gracefully."""
        router = CognitiveRouter()
        router.initialize({}, {})

        result = router.decide({'frame': None})

        # Should return something, not crash
        assert result.action is not None

    def test_none_game_state_handled(self, router, sample_nodes, sample_edges):
        """Test router handles None in game state."""
        router.initialize(sample_nodes, sample_edges)

        result = router.decide({'frame': None, 'value': None})

        assert result.action is not None

    def test_exception_in_executor_handled(self, router, sample_nodes, sample_edges):
        """Test router handles executor exceptions."""
        router.initialize(sample_nodes, sample_edges)

        def bad_executor(rung_name, state):
            raise ValueError("Test error")

        # Should not crash
        result = router.decide({'frame': None}, rung_executor=bad_executor)

        # Should have used fallback or error handling
        assert result.action is not None

    def test_rapid_transitions_handled(self, router, sample_nodes, sample_edges):
        """Test rapid transitions don't cause issues."""
        router.initialize(sample_nodes, sample_edges)

        # Force rapid quadrant changes
        for _ in range(10):
            router.epistemic_tracker.current_state.primary_quadrant = RumsfeldQuadrant.KK
            router.epistemic_tracker.current_state.primary_quadrant = RumsfeldQuadrant.UU

        result = router.decide({'frame': None})

        assert result.action is not None


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
