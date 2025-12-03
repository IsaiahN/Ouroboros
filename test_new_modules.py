"""
Unit Tests for New Modules Created During Deep Analysis
========================================================
Tests hypothesis_monitoring.py, symbolic_reasoning_engine.py, 
and emergency_sequence_cleanup.py

Created: 2025-12-02
"""

import sys
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.dont_write_bytecode = True

import unittest
import sqlite3
import numpy as np
from pathlib import Path
from datetime import datetime


class TestHypothesisMonitoring(unittest.TestCase):
    """Tests for hypothesis_monitoring.py"""
    
    def test_import(self):
        """Verify module can be imported."""
        from hypothesis_monitoring import HypothesisMonitor, HypothesisResult
        self.assertTrue(True)
    
    def test_monitor_initialization(self):
        """Verify HypothesisMonitor initializes correctly."""
        from hypothesis_monitoring import HypothesisMonitor
        monitor = HypothesisMonitor()
        self.assertIsNotNone(monitor.db_path)
    
    def test_monitoring_tables_created(self):
        """Verify monitoring tables are created."""
        from hypothesis_monitoring import HypothesisMonitor
        monitor = HypothesisMonitor()
        
        conn = sqlite3.connect(str(monitor.db_path))
        cursor = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN 
            ('frontier_discoveries', 'hypothesis_validations', 'budget_usage_log', 'role_distribution_log')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        expected_tables = {'frontier_discoveries', 'hypothesis_validations', 
                          'budget_usage_log', 'role_distribution_log'}
        self.assertEqual(set(tables), expected_tables)
    
    def test_run_all_checks(self):
        """Verify run_all_checks returns results for all hypotheses."""
        from hypothesis_monitoring import HypothesisMonitor
        monitor = HypothesisMonitor()
        results = monitor.run_all_checks()
        
        # Should have results for 8 hypotheses
        self.assertEqual(len(results), 8)
        
        # Each result should have required fields
        for result in results:
            self.assertIsNotNone(result.hypothesis_id)
            self.assertIsNotNone(result.status)
            self.assertIsInstance(result.confidence, float)
            self.assertIsInstance(result.evidence, dict)
            self.assertIsInstance(result.recommendations, list)
    
    def test_get_summary_stats(self):
        """Verify summary stats returns expected keys."""
        from hypothesis_monitoring import HypothesisMonitor
        monitor = HypothesisMonitor()
        stats = monitor.get_summary_stats()
        
        required_keys = ['total_agents', 'total_generations', 'total_sequences', 
                        'total_game_attempts', 'games_progress']
        for key in required_keys:
            self.assertIn(key, stats)
    
    def test_hypothesis_result_dataclass(self):
        """Verify HypothesisResult dataclass works correctly."""
        from hypothesis_monitoring import HypothesisResult
        
        result = HypothesisResult(
            hypothesis_id='TEST',
            hypothesis_name='Test Hypothesis',
            status='CONFIRMED',
            confidence=0.9,
            evidence={'test': 'data'},
            recommendations=['Fix it'],
            checked_at=datetime.now().isoformat()
        )
        
        self.assertEqual(result.hypothesis_id, 'TEST')
        self.assertEqual(result.status, 'CONFIRMED')
        self.assertEqual(result.confidence, 0.9)


class TestSymbolicReasoningEngine(unittest.TestCase):
    """Tests for symbolic_reasoning_engine.py"""
    
    def test_import(self):
        """Verify module can be imported."""
        from symbolic_reasoning_engine import (
            SymbolicReasoningEngine, WorldState, GameObject, 
            ObjectType, SimpleSceneParser, WorldModel, 
            Goal, CompositionalGoal, GoalEvaluator, ActionPlanner
        )
        self.assertTrue(True)
    
    def test_object_type_enum(self):
        """Verify ObjectType enum has expected values."""
        from symbolic_reasoning_engine import ObjectType
        
        # Core types that must exist
        required = {'AGENT', 'GOAL', 'OBSTACLE', 'COLLECTIBLE', 
                   'BUTTON', 'PORTAL', 'UNKNOWN'}
        actual = {e.name for e in ObjectType}
        
        # All required types must be present
        self.assertTrue(required.issubset(actual), 
                       f"Missing required types: {required - actual}")
        
        # Extended types (added in full implementation)
        extended = {'MOVABLE', 'ENEMY', 'KEY', 'DOOR'}
        self.assertTrue(extended.issubset(actual),
                       f"Missing extended types: {extended - actual}")
    
    def test_game_object_creation(self):
        """Verify GameObject can be created with required fields."""
        from symbolic_reasoning_engine import GameObject, ObjectType
        
        obj = GameObject(
            object_id='test_1',
            object_type=ObjectType.AGENT,
            position=(5, 5),
            color=3
        )
        
        self.assertEqual(obj.object_id, 'test_1')
        self.assertEqual(obj.object_type, ObjectType.AGENT)
        self.assertEqual(obj.position, (5, 5))
    
    def test_game_object_distance(self):
        """Verify distance calculation between objects."""
        from symbolic_reasoning_engine import GameObject, ObjectType
        
        obj1 = GameObject('a', ObjectType.AGENT, (0, 0), 1)
        obj2 = GameObject('b', ObjectType.GOAL, (3, 4), 2)
        
        # Manhattan distance: |3-0| + |4-0| = 7
        self.assertEqual(obj1.distance_to(obj2), 7)
    
    def test_world_state_creation(self):
        """Verify WorldState can be created."""
        from symbolic_reasoning_engine import WorldState, GameObject, ObjectType
        import numpy as np
        
        grid = np.zeros((10, 10), dtype=int)
        objects = {
            'agent': GameObject('agent', ObjectType.AGENT, (5, 5), 3)
        }
        
        state = WorldState(objects=objects, grid=grid, step=0)
        
        self.assertEqual(len(state.objects), 1)
        self.assertIsNotNone(state.get_agent())
    
    def test_world_state_clone(self):
        """Verify WorldState clone creates independent copy."""
        from symbolic_reasoning_engine import WorldState, GameObject, ObjectType
        import numpy as np
        
        grid = np.zeros((10, 10), dtype=int)
        objects = {'agent': GameObject('agent', ObjectType.AGENT, (5, 5), 3)}
        state = WorldState(objects=objects, grid=grid, step=0)
        
        clone = state.clone()
        
        # Modify clone
        clone.step = 10
        clone.objects['agent'].position = (0, 0)
        
        # Original should be unchanged
        self.assertEqual(state.step, 0)
        self.assertEqual(state.objects['agent'].position, (5, 5))
    
    def test_simple_scene_parser(self):
        """Verify SimpleSceneParser can parse a basic frame."""
        from symbolic_reasoning_engine import SimpleSceneParser
        import numpy as np
        
        # Create simple frame with one colored object
        frame = np.zeros((10, 10), dtype=int)
        frame[5, 5] = 3  # Single pixel of color 3
        
        parser = SimpleSceneParser()
        state = parser.parse(frame)
        
        # Should detect one object
        self.assertGreater(len(state.objects), 0)
    
    def test_world_model_action(self):
        """Verify WorldModel can apply actions."""
        from symbolic_reasoning_engine import WorldModel, WorldState, GameObject, ObjectType
        import numpy as np
        
        grid = np.zeros((10, 10), dtype=int)
        objects = {'agent': GameObject('agent', ObjectType.AGENT, (5, 5), 3)}
        initial_state = WorldState(objects=objects, grid=grid, step=0)
        
        model = WorldModel(initial_state)
        
        # Apply action 1 (up)
        new_state = model.apply_action(1)
        
        # Agent should have moved up
        self.assertEqual(new_state.step, 1)
        agent = new_state.get_agent()
        self.assertIsNotNone(agent)
        if agent:
            self.assertEqual(agent.position, (4, 5))  # Moved up from (5,5)
    
    def test_goal_evaluation(self):
        """Verify GoalEvaluator correctly checks goals."""
        from symbolic_reasoning_engine import (
            GoalEvaluator, Goal, CompositionalGoal,
            WorldState, GameObject, ObjectType
        )
        import numpy as np
        
        # Create state with agent at goal position
        grid = np.zeros((10, 10), dtype=int)
        objects = {
            'agent': GameObject('agent', ObjectType.AGENT, (5, 5), 3),
            'goal': GameObject('goal', ObjectType.GOAL, (5, 5), 2)
        }
        state = WorldState(objects=objects, grid=grid, step=0)
        
        # Create goal: agent must reach goal
        goal = Goal(
            goal_type='reach',
            target_objects=['goal'],
            condition='reach'
        )
        composite = CompositionalGoal(subgoals=[goal], logic='AND')
        
        evaluator = GoalEvaluator(composite)
        result = evaluator.evaluate(state)
        
        # Agent is at goal position, should be satisfied
        self.assertTrue(result)
    
    def test_engine_initialization(self):
        """Verify SymbolicReasoningEngine initializes correctly."""
        from symbolic_reasoning_engine import SymbolicReasoningEngine
        
        engine = SymbolicReasoningEngine('lp85')
        
        self.assertEqual(engine.game_type, 'lp85')
        self.assertIsNotNone(engine.parser)
    
    def test_factory_function(self):
        """Verify create_symbolic_engine_for_game works."""
        from symbolic_reasoning_engine import create_symbolic_engine_for_game
        
        engine = create_symbolic_engine_for_game('lp85')
        
        self.assertEqual(engine.game_type, 'lp85')


class TestEmergencySequenceCleanup(unittest.TestCase):
    """Tests for emergency_sequence_cleanup.py"""
    
    def test_import(self):
        """Verify module can be imported."""
        from emergency_sequence_cleanup import (
            get_connection, backup_sequences_to_archive,
            get_pre_cleanup_stats, get_post_cleanup_stats
        )
        self.assertTrue(True)
    
    def test_get_connection(self):
        """Verify database connection works."""
        from emergency_sequence_cleanup import get_connection
        
        conn = get_connection()
        self.assertIsNotNone(conn)
        conn.close()
    
    def test_get_pre_cleanup_stats(self):
        """Verify stats function returns expected keys."""
        from emergency_sequence_cleanup import get_pre_cleanup_stats
        
        stats = get_pre_cleanup_stats()
        
        required_keys = ['total_sequences', 'lp85_sequences', 'sequences_by_game',
                        'avg_actions_by_level', 'bloated_count', 'max_bloat_ratio']
        for key in required_keys:
            self.assertIn(key, stats)
    
    def test_archive_table_exists(self):
        """Verify archived_sequences table was created."""
        from emergency_sequence_cleanup import get_connection
        
        conn = get_connection()
        cursor = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='archived_sequences'
        """)
        result = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(result)
    
    def test_lp85_sequences_removed(self):
        """Verify lp85 sequences were cleaned."""
        from emergency_sequence_cleanup import get_pre_cleanup_stats
        
        stats = get_pre_cleanup_stats()
        
        # lp85 sequences should be 0 after cleanup
        self.assertEqual(stats['lp85_sequences'], 0)
    
    def test_no_bloated_sequences_remain(self):
        """Verify no bloated sequences remain after cleanup."""
        from emergency_sequence_cleanup import get_pre_cleanup_stats
        
        stats = get_pre_cleanup_stats()
        
        # No sequences with >10x bloat should remain
        self.assertEqual(stats['bloated_count'], 0)


class TestIntegration(unittest.TestCase):
    """Integration tests across modules."""
    
    def test_monitoring_reflects_cleanup(self):
        """Verify hypothesis monitoring reflects cleanup results."""
        from hypothesis_monitoring import HypothesisMonitor
        
        monitor = HypothesisMonitor()
        results = monitor.run_all_checks()
        
        # Find H4 (lp85) result
        h4_result = next((r for r in results if r.hypothesis_id == 'H4'), None)
        self.assertIsNotNone(h4_result)
        
        # Should be acknowledged (not corrupt) since sequences were deleted
        if h4_result:
            self.assertEqual(h4_result.status, 'ACKNOWLEDGED')
    
    def test_test_suite_reflects_cleanup(self):
        """Verify critical tests pass after cleanup."""
        from test_critical_systems import (
            TestSequenceQuality, TestValidationRates
        )
        import unittest
        
        # Run just the quality tests
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestSequenceQuality)
        runner = unittest.TextTestRunner(verbosity=0)
        result = runner.run(suite)
        
        self.assertEqual(len(result.failures), 0)
        self.assertEqual(len(result.errors), 0)


def run_all_tests():
    """Run all tests and return results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    test_classes = [
        TestHypothesisMonitoring,
        TestSymbolicReasoningEngine,
        TestEmergencySequenceCleanup,
        TestIntegration,
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    print("=" * 60)
    print("UNIT TESTS FOR NEW MODULES")
    print("=" * 60)
    print()
    
    result = run_all_tests()
    
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n[OK] ALL TESTS PASSED")
    else:
        print("\n[FAIL] SOME TESTS FAILED")
        if result.failures:
            print("\nFailed tests:")
            for test, _ in result.failures:
                print(f"  - {test}")
        if result.errors:
            print("\nErrors:")
            for test, _ in result.errors:
                print(f"  - {test}")
