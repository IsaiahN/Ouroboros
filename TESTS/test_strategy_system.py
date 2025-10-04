"""
Comprehensive tests for the Level-Beating Strategy System.
Tests all components and integration points.
"""
import sys
import os
import asyncio
import tempfile
import unittest
from unittest.mock import Mock, AsyncMock, patch
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import disable_pycache from project root
from disable_pycache import *

# Import test dependencies
from database_interface import DatabaseInterface
from arc_api_client import GameState

# Import strategy components
from strategies import (
    GameStateAnalyzer,
    SimpleHeuristicsEngine,
    ActionFeedbackLearner,
    EmergencyRecovery,
    PatternMatcher,
    LevelBeatingStrategy,
    GameTypeRouter,
    DifficultyAdaptor,
    SuccessTracker
)
from strategies.utils import GameContext


class MockActionHandler:
    """Mock action handler for testing"""
    def __init__(self):
        self.calls = []

    async def send_action_1(self):
        self.calls.append("ACTION1")
        return self._mock_game_state()

    async def send_action_6(self, x, y):
        self.calls.append(f"ACTION6({x},{y})")
        return self._mock_game_state()

    def _mock_game_state(self):
        return GameState(
            game_id="test_game_123",
            guid="test_guid_456",
            state="NOT_FINISHED",
            score=50.0,
            win_score=100.0,
            available_actions=["1", "2", "3", "4", "5", "6", "7"],
            frame=[],
            action_input=None
        )


class TestStrategySystem(unittest.TestCase):
    """Test suite for strategy system components"""

    def setUp(self):
        """Set up test fixtures"""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()

        self.db = DatabaseInterface(self.temp_db.name)
        self.db.ensure_strategy_tables()

        self.mock_action_handler = MockActionHandler()

        # Create mock game state
        self.mock_game_state = GameState(
            game_id="test_game_main",
            guid="test_guid_main",
            state="NOT_FINISHED",
            score=25.0,
            win_score=100.0,
            available_actions=["1", "2", "3", "4", "5", "6", "7"],
            frame=[],
            action_input=None
        )

    def tearDown(self):
        """Clean up test fixtures"""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass

    def test_game_context_creation(self):
        """Test GameContext creation and methods"""
        context = GameContext()
        context.update_from_game_state(self.mock_game_state)

        self.assertEqual(context.current_score, 25.0)
        self.assertEqual(context.win_score, 100.0)
        self.assertEqual(context.score_progress, 0.25)
        self.assertFalse(context.is_near_victory)
        self.assertFalse(context.is_struggling)

    async def test_game_state_analyzer(self):
        """Test GameStateAnalyzer functionality"""
        analyzer = GameStateAnalyzer(self.db)

        context = GameContext()
        context.update_from_game_state(self.mock_game_state)
        context.score_history = [20.0, 22.0, 25.0]  # Increasing trend

        analysis = await analyzer.analyze_game_state(
            self.mock_game_state,
            self.mock_action_handler,
            context
        )

        # Check analysis structure
        self.assertIn('score_momentum', analysis)
        self.assertIn('risk_level', analysis)
        self.assertIn('emergency_detected', analysis)
        self.assertIn('recommended_actions', analysis)

        # Check momentum calculation
        self.assertEqual(analysis['score_momentum'], 'increasing')
        self.assertFalse(analysis['emergency_detected'])

    async def test_simple_heuristics_engine(self):
        """Test SimpleHeuristicsEngine functionality"""
        engine = SimpleHeuristicsEngine(self.db)

        action = await engine.get_next_action(self.mock_game_state, self.mock_action_handler)

        # Should return a valid action
        self.assertTrue(isinstance(action, (str, type(lambda: None))))

        # Test different scenarios
        # Low score scenario (should use aggressive exploration)
        low_score_state = GameState(
            game_id="test_low_score",
            guid="test_guid_low",
            state="NOT_FINISHED",
            score=10.0,
            win_score=100.0,
            available_actions=["1", "2", "3", "4", "5", "6", "7"],
            frame=[],
            action_input=None
        )

        action = await engine.get_next_action(low_score_state, self.mock_action_handler)
        self.assertIsNotNone(action)

    async def test_action_feedback_learner(self):
        """Test ActionFeedbackLearner functionality"""
        learner = ActionFeedbackLearner(self.db)

        # Mock pre and post states
        pre_state = GameState(game_id="test_pre", guid="test_guid_pre", state="NOT_FINISHED", score=20.0, win_score=100.0, available_actions=["1","2","3"], frame=[], action_input=None)
        post_state = GameState(game_id="test_post", guid="test_guid_post", state="NOT_FINISHED", score=25.0, win_score=100.0, available_actions=["1","2","3"], frame=[], action_input=None)

        # Test learning from action
        result = await learner.learn_from_action("ACTION1", pre_state, post_state)

        self.assertIn('action', result)
        self.assertIn('score_change', result)
        self.assertIn('success', result)
        self.assertEqual(result['score_change'], 5.0)
        self.assertTrue(result['success'])

        # Test success probability
        context = GameContext()
        context.update_from_game_state(self.mock_game_state)

        probability = await learner.get_success_probability("ACTION1", context)
        self.assertIsInstance(probability, float)
        self.assertGreaterEqual(probability, 0.0)
        self.assertLessEqual(probability, 1.0)

    async def test_emergency_recovery(self):
        """Test EmergencyRecovery functionality"""
        recovery = EmergencyRecovery(self.db)

        # Create emergency context
        emergency_context = GameContext()
        emergency_context.update_from_game_state(self.mock_game_state)
        emergency_context.score_history = [80.0, 60.0, 40.0, 20.0]  # Rapid decline
        emergency_context.actions_taken = 25
        emergency_context.score_momentum = 'decreasing'

        # Test emergency detection
        assessment = await recovery.check_emergency_conditions(emergency_context)

        self.assertIn('is_emergency', assessment)
        self.assertIn('severity_score', assessment)
        self.assertIn('triggers', assessment)

        # Should detect emergency due to rapid score decline
        self.assertTrue(assessment['is_emergency'])

        # Test recovery action
        if assessment['is_emergency'] and assessment['recommended_recovery']:
            action = await recovery.execute_recovery_action(
                assessment['recommended_recovery'],
                emergency_context,
                self.mock_action_handler
            )
            self.assertIsNotNone(action)

    async def test_pattern_matcher(self):
        """Test PatternMatcher functionality"""
        matcher = PatternMatcher(self.db)

        context = GameContext()
        context.update_from_game_state(self.mock_game_state)
        context.game_type = "puzzle"

        # Test pattern finding (should handle empty database gracefully)
        patterns = await matcher.find_successful_patterns(context)
        self.assertIsInstance(patterns, list)

        # Test learning a successful sequence
        action_sequence = ["ACTION1", "ACTION2", "ACTION6"]
        success_metrics = {
            'score_change': 15.0,
            'win': False,
            'actions_taken': 10
        }

        await matcher.learn_successful_sequence(action_sequence, context, success_metrics)

        # Test pattern recommendation
        recommendation = await matcher.recommend_action_sequence(context)
        # Should return None or a valid sequence
        if recommendation:
            self.assertIsInstance(recommendation, list)

    async def test_game_type_router(self):
        """Test GameTypeRouter functionality"""
        router = GameTypeRouter(self.db)

        # Test game type detection
        detection = await router.detect_game_type("puzzle_game_123")

        self.assertIn('detected_type', detection)
        self.assertIn('type_confidence', detection)
        self.assertIn('strategy_mapping', detection)

        # Should detect puzzle type from ID - pattern matches "puzzle"
        self.assertEqual(detection['detected_type'], 'puzzle')

        # Test strategy routing
        strategy_config = await router.get_strategy_for_game_type('puzzle')
        self.assertIn('name', strategy_config)
        self.assertIn('approach', strategy_config)

    async def test_difficulty_adaptor(self):
        """Test DifficultyAdaptor functionality"""
        adaptor = DifficultyAdaptor(self.db)

        context = GameContext()
        context.update_from_game_state(self.mock_game_state)

        # Test difficulty assessment
        assessment = await adaptor.assess_difficulty("test_game_123", context)

        self.assertIn('difficulty_level', assessment)
        self.assertIn('difficulty_score', assessment)
        self.assertIn('confidence', assessment)

        # Test strategy adaptation
        base_config = {
            'aggression_multiplier': 1.0,
            'exploration_factor': 1.0,
            'emergency_threshold': 0.7
        }

        adapted_config = await adaptor.adapt_strategy_to_difficulty(assessment, base_config)
        self.assertIn('aggression_multiplier', adapted_config)
        self.assertIn('adaptation_details', adapted_config)

    async def test_success_tracker(self):
        """Test SuccessTracker functionality"""
        tracker = SuccessTracker(self.db)

        # Test performance tracking
        game_results = {
            'final_score': 75.0,
            'actions_taken': 15,
            'win': True,
            'duration_seconds': 45.0
        }

        tracking_result = await tracker.track_strategy_performance(
            "level_beating", "puzzle", game_results
        )

        self.assertIn('strategy_name', tracking_result)
        self.assertIn('metrics_tracked', tracking_result)
        self.assertIn('performance_summary', tracking_result)

        # Test best performing strategies
        best_strategies = await tracker.get_best_performing_strategies()
        self.assertIsInstance(best_strategies, list)

    async def test_level_beating_strategy_integration(self):
        """Test LevelBeatingStrategy integration"""
        strategy = LevelBeatingStrategy(self.db)

        # Test action selection
        action = await strategy.get_next_action(self.mock_game_state, self.mock_action_handler)

        self.assertIsNotNone(action)
        self.assertTrue(isinstance(action, (str, type(lambda: None))))

        # Test performance tracking
        performance = await strategy.get_strategy_performance()

        self.assertIn('strategy_name', performance)
        self.assertIn('current_mode', performance)

        # Test game session results
        game_results = {
            'final_score': 80.0,
            'win': True,
            'actions_taken': 12
        }

        await strategy.save_game_session_results(game_results)

    def test_database_integration(self):
        """Test database integration for strategy system"""
        # Test saving strategy data
        self.db.save_strategy_data("test_strategy", {
            'heuristic_name': 'test_heuristic',
            'condition_met': {'score': 50},
            'action_taken': 'ACTION1',
            'success_rate': 0.75,
            'avg_score_impact': 5.0,
            'usage_count': 10
        })

        # Test getting performance summary
        summary = self.db.get_strategy_performance_summary()
        self.assertIn('heuristics', summary)


async def run_async_tests():
    """Run all async tests"""
    test_instance = TestStrategySystem()
    test_instance.setUp()

    async_tests = [
        test_instance.test_game_state_analyzer,
        test_instance.test_simple_heuristics_engine,
        test_instance.test_action_feedback_learner,
        test_instance.test_emergency_recovery,
        test_instance.test_pattern_matcher,
        test_instance.test_game_type_router,
        test_instance.test_difficulty_adaptor,
        test_instance.test_success_tracker,
        test_instance.test_level_beating_strategy_integration
    ]

    results = []
    for test_func in async_tests:
        try:
            await test_func()
            results.append(f"[PASS] {test_func.__name__}: PASSED")
        except Exception as e:
            results.append(f"[FAIL] {test_func.__name__}: FAILED - {e}")

    test_instance.tearDown()
    return results


def run_sync_tests():
    """Run synchronous tests"""
    test_instance = TestStrategySystem()
    test_instance.setUp()

    sync_tests = [
        test_instance.test_game_context_creation,
        test_instance.test_database_integration
    ]

    results = []
    for test_func in sync_tests:
        try:
            test_func()
            results.append(f"[PASS] {test_func.__name__}: PASSED")
        except Exception as e:
            results.append(f"[FAIL] {test_func.__name__}: FAILED - {e}")

    test_instance.tearDown()
    return results


if __name__ == "__main__":
    print("RUNNING Level-Beating Strategy System Tests...")
    print("=" * 60)

    # Run synchronous tests
    print("\nSYNCHRONOUS TESTS:")
    sync_results = run_sync_tests()
    for result in sync_results:
        print(result)

    # Run asynchronous tests
    print("\nASYNCHRONOUS TESTS:")
    async_results = asyncio.run(run_async_tests())
    for result in async_results:
        print(result)

    # Summary
    all_results = sync_results + async_results
    passed = len([r for r in all_results if "PASSED" in r])
    failed = len([r for r in all_results if "FAILED" in r])

    print("\n" + "=" * 60)
    print(f"TEST SUMMARY: {passed} PASSED, {failed} FAILED")

    if failed == 0:
        print("ALL TESTS PASSED! Strategy system is working correctly.")
    else:
        print("Some tests failed. Review the errors above.")