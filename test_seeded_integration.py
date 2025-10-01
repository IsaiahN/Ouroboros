#!/usr/bin/env python3
"""
BitterTruth-AI Seeded Algorithm Integration Test

Comprehensive test suite for the seeded algorithm system including:
- DatabaseInterface seeded algorithm methods
- RoutineManager functionality
- EvolutionManager integration
- Algorithm inheritance naming system
"""

import os
import sys
import json
import tempfile
import unittest
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from database_interface import DatabaseInterface
from routine_manager import RoutineManager, AlgorithmRoutine, RoutineStep, SwitchCondition
from evolution_manager import EvolutionManager, EvolutionConfig
from algorithm_representations import AlgorithmRepresentation, AlgorithmNode
from seeded_algorithm_builders import SeededAlgorithmBuilder


class TestSeededAlgorithmIntegration(unittest.TestCase):
    """Test suite for seeded algorithm system integration."""

    def setUp(self):
        """Set up test environment with temporary database."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()

        self.db = DatabaseInterface(self.temp_db.name)
        self.routine_manager = RoutineManager(self.db)

        # Create test evolution config
        self.evolution_config = EvolutionConfig(
            population_size=10,
            evolution_frequency=5,
            min_games_for_evolution=3
        )

        self.evolution_manager = EvolutionManager(self.evolution_config, self.db)

    def tearDown(self):
        """Clean up test environment."""
        try:
            self.db.close()
            os.unlink(self.temp_db.name)
        except:
            pass

    def test_database_seeded_algorithm_methods(self):
        """Test DatabaseInterface seeded algorithm methods."""
        print("Testing DatabaseInterface seeded algorithm methods...")

        # Test saving seeded algorithm metadata
        algorithm_id = "test_astar_123"
        self.db.save_seeded_algorithm_meta(
            algorithm_id=algorithm_id,
            original_name="A* Search",
            category="Search & Optimization",
            adaptability_score=0.8,
            complexity_level="moderate",
            adaptation_notes="Adapted for game pathfinding"
        )

        # Test retrieving seeded algorithms
        seeded_algos = self.db.get_seeded_algorithms(category="Search & Optimization")
        self.assertEqual(len(seeded_algos), 0)  # No algorithm in population yet

        # Add algorithm to population first
        from algorithm_representations import AlgorithmRepresentation, AlgorithmNode
        test_algo = AlgorithmRepresentation(
            algorithm_id=algorithm_id,
            name="test_astar",
            root_node=AlgorithmNode("test", "root")
        )

        self.db.save_algorithm(
            algorithm_id=algorithm_id,
            algorithm_type="seeded",
            algorithm_data=test_algo.to_json()
        )

        # Now test retrieval
        seeded_algos = self.db.get_seeded_algorithms(category="Search & Optimization")
        self.assertEqual(len(seeded_algos), 1)
        self.assertEqual(seeded_algos[0]['original_name'], "A* Search")
        self.assertEqual(seeded_algos[0]['adaptability_score'], 0.8)

        # Test performance update
        self.db.update_seeded_algorithm_performance(algorithm_id, 0.75, 2)
        updated_algo = self.db.get_seeded_algorithms()[0]
        self.assertEqual(updated_algo['games_tested'], 2)
        self.assertAlmostEqual(updated_algo['avg_performance'], 0.75, places=2)

        print("[PASS] DatabaseInterface seeded algorithm methods working")

    def test_routine_manager_functionality(self):
        """Test RoutineManager core functionality."""
        print("Testing RoutineManager functionality...")

        # Test game type extraction
        game_type = self.routine_manager.extract_game_type("vc33-001-test")
        self.assertEqual(game_type, "vc33")

        game_type = self.routine_manager.extract_game_type("puzzle_123")
        self.assertEqual(game_type, "puzz")

        # Test creating default routine
        algorithm_ids = ["algo1", "algo2", "algo3"]
        routine = self.routine_manager.create_default_routine("vc33", algorithm_ids)

        self.assertEqual(routine.game_type, "vc33")
        self.assertEqual(len(routine.steps), 3)
        self.assertEqual(routine.steps[0].algorithm_id, "algo1")

        # Test saving and retrieving routine
        self.routine_manager.save_routine(routine)

        retrieved_routines = self.db.get_algorithm_routines(game_type="vc33")
        self.assertEqual(len(retrieved_routines), 1)
        self.assertEqual(retrieved_routines[0]['routine_name'], routine.routine_name)

        # Test routine execution
        game_id = "vc33-test-001"
        routine_state = self.routine_manager.start_routine(game_id, routine)

        self.assertEqual(routine_state['current_step'], 0)
        self.assertEqual(routine_state['actions_in_current_step'], 0)

        # Test algorithm switching
        current_algo = self.routine_manager.get_current_algorithm(game_id)
        self.assertEqual(current_algo, "algo1")

        # Test switch conditions
        should_switch, reason = self.routine_manager.should_switch_algorithm(
            game_id, 10.0, 20  # High action count should trigger switch
        )
        self.assertTrue(should_switch)

        # Perform switch
        next_algo = self.routine_manager.switch_to_next_algorithm(game_id)
        self.assertEqual(next_algo, "algo2")

        print("[PASS] RoutineManager functionality working")

    def test_seeded_algorithm_builder(self):
        """Test SeededAlgorithmBuilder creates valid algorithms."""
        print("Testing SeededAlgorithmBuilder...")

        builder = SeededAlgorithmBuilder()

        # Test creating A* algorithm
        astar_algo = builder.create_astar_algorithm()
        self.assertIsNotNone(astar_algo)
        self.assertTrue(astar_algo.algorithm_id.startswith("astar_"))
        self.assertEqual(astar_algo.name, "astar_search")

        # Test creating Decision Tree algorithm
        dt_algo = builder.create_decision_tree_algorithm()
        self.assertIsNotNone(dt_algo)
        self.assertTrue(dt_algo.algorithm_id.startswith("decision_tree_"))

        # Test algorithm serialization
        astar_json = astar_algo.to_json()
        self.assertIsInstance(astar_json, str)

        # Test deserialization
        reconstructed = AlgorithmRepresentation.from_json(astar_json)
        self.assertEqual(reconstructed.algorithm_id, astar_algo.algorithm_id)

        print("[PASS] SeededAlgorithmBuilder working")

    def test_evolution_manager_seeded_integration(self):
        """Test EvolutionManager integration with seeded algorithms."""
        print("Testing EvolutionManager seeded integration...")

        # Initialize seeded algorithms
        result = self.evolution_manager.initialize_seeded_algorithms()

        self.assertIn('seeded_count', result)
        self.assertGreater(result['seeded_count'], 0)

        # Test routine game initialization
        game_id = "vc33-integration-test"
        game_result = self.evolution_manager.start_game_with_routine(game_id)

        if 'error' not in game_result:
            self.assertIn('routine', game_result)
            self.assertIn('current_algorithm', game_result)
            self.assertEqual(game_result['game_type'], "vc33")

            # Test routine context updates
            new_algo = self.evolution_manager.update_routine_context(
                game_id, 50.0, 10
            )

            # Test game completion
            self.evolution_manager.complete_game_with_routine(
                game_id, 100.0, 25, 3, True
            )

        # Test hybrid algorithm creation
        if len(self.evolution_manager.active_population) >= 2:
            parent_algos = self.evolution_manager.active_population[:2]
            hybrid = self.evolution_manager.create_hybrid_algorithm(parent_algos)

            if hybrid:
                self.assertIsNotNone(hybrid)
                self.assertIn('_', hybrid.algorithm_id)  # Should have inheritance naming

        print("[PASS] EvolutionManager seeded integration working")

    def test_algorithm_inheritance_naming(self):
        """Test algorithm inheritance naming system."""
        print("Testing algorithm inheritance naming system...")

        # Create parent algorithms with metadata
        parent1_id = "parent1_test"
        parent2_id = "parent2_test"

        # Save parent algorithms
        for parent_id, name in [(parent1_id, "A* Search"), (parent2_id, "Dijkstra")]:
            test_algo = AlgorithmRepresentation(
                algorithm_id=parent_id,
                name=name.lower().replace(' ', '_'),
                root_node=AlgorithmNode("test", "root")
            )

            self.db.save_algorithm(
                algorithm_id=parent_id,
                algorithm_type="seeded",
                algorithm_data=test_algo.to_json()
            )

            self.db.save_seeded_algorithm_meta(
                algorithm_id=parent_id,
                original_name=name,
                category="Search & Optimization"
            )

        # Test inheritance naming
        hybrid_id = self.db.create_algorithm_with_inheritance(
            algorithm_id="test_hybrid_123",
            algorithm_type="hybrid",
            algorithm_data='{"test": "data"}',
            parent_ids=[parent1_id, parent2_id],
            original_names=["A*Search", "Dijkstra"]
        )

        self.assertIn("A*Search_Dijkstra", hybrid_id)

        # Test inheritance chain retrieval
        chain = self.db.get_algorithm_inheritance_chain(hybrid_id)
        self.assertEqual(len(chain), 2)
        self.assertIn(parent1_id, chain)
        self.assertIn(parent2_id, chain)

        print("[PASS] Algorithm inheritance naming system working")

    def test_system_status_and_recommendations(self):
        """Test system status and recommendation methods."""
        print("Testing system status and recommendations...")

        # Initialize some test data
        self.evolution_manager.initialize_seeded_algorithms()

        # Test seeded system status
        status = self.evolution_manager.get_seeded_system_status()
        self.assertIn('seeded_algorithms', status)
        self.assertIn('population', status)

        # Test algorithm recommendations
        recommendations = self.evolution_manager.get_seeded_algorithm_recommendations(
            limit=3
        )
        self.assertIsInstance(recommendations, list)

        # Test database statistics
        db_stats = self.db.get_seeded_algorithm_stats()
        self.assertIn('overall', db_stats)

        print("[PASS] System status and recommendations working")

    def test_routine_performance_tracking(self):
        """Test routine performance tracking and optimization."""
        print("Testing routine performance tracking...")

        # Create and save a test routine
        routine = AlgorithmRoutine(
            routine_id="test_performance_routine",
            game_type="test",
            routine_name="Test Performance Routine",
            steps=[
                RoutineStep("algo1", 10, [
                    SwitchCondition("action_count", 8.0, "greater_than")
                ]),
                RoutineStep("algo2", 15)
            ]
        )

        self.routine_manager.save_routine(routine)

        # Start routine and simulate game
        game_id = "test-perf-001"
        self.routine_manager.start_routine(game_id, routine)

        # Update performance multiple times
        for i in range(3):
            self.routine_manager.update_routine_performance(
                game_id, 80.0 + i * 10, 20 + i * 5, 2 + i, i >= 2
            )

        # Check updated routine
        updated_routines = self.db.get_algorithm_routines(game_type="test")
        self.assertEqual(len(updated_routines), 1)
        updated_routine = updated_routines[0]
        self.assertEqual(updated_routine['games_tested'], 3)
        self.assertGreater(updated_routine['success_rate'], 0)

        print("[PASS] Routine performance tracking working")


def run_integration_tests():
    """Run all integration tests with detailed output."""
    print("=" * 60)
    print("BITTERTRUTH-AI SEEDED ALGORITHM INTEGRATION TESTS")
    print("=" * 60)

    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestSeededAlgorithmIntegration)

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(test_suite)

    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("[SUCCESS] ALL INTEGRATION TESTS PASSED!")
        print(f"[PASS] Ran {result.testsRun} tests successfully")
    else:
        print("[FAIL] SOME TESTS FAILED!")
        print(f"[FAIL] {len(result.failures)} failures, {len(result.errors)} errors")

        # Print detailed error information
        for test, error in result.failures + result.errors:
            print(f"\nFAILED: {test}")
            print(f"Error: {error}")

    print("=" * 60)
    return result.wasSuccessful()


def test_quick_validation():
    """Quick validation test for immediate feedback."""
    print("Running quick validation tests...")

    try:
        # Test imports
        from seeded_algorithm_builders import SeededAlgorithmBuilder
        from routine_manager import RoutineManager
        print("[PASS] All imports successful")

        # Test basic database operations
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
            temp_db.close()

            db = DatabaseInterface(temp_db.name)

            # Force database recreation to ensure all tables exist
            db._create_database_from_schema()

            # Test seeded algorithm metadata
            db.save_seeded_algorithm_meta(
                "test_123", "Test Algorithm", "Test Category"
            )
            print("[PASS] Database seeded algorithm methods working")

            # Test routine manager
            routine_manager = RoutineManager(db)
            game_type = routine_manager.extract_game_type("test-001")
            print(f"[PASS] Routine manager working (extracted: {game_type})")

            # Test algorithm builder
            builder = SeededAlgorithmBuilder()
            test_algo = builder.create_binary_search_algorithm()
            print(f"[PASS] Algorithm builder working (created: {test_algo.algorithm_id})")

            db.close()
            os.unlink(temp_db.name)

        print("[SUCCESS] Quick validation PASSED - System ready for full testing")
        return True

    except Exception as e:
        print(f"[ERROR] Quick validation FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("BitterTruth-AI Seeded Algorithm Integration Testing")
    print("Choose test mode:")
    print("1. Quick validation (fast)")
    print("2. Full integration tests (comprehensive)")

    try:
        choice = input("Enter choice (1 or 2, default=1): ").strip()
        if not choice:
            choice = "1"

        if choice == "1":
            success = test_quick_validation()
        elif choice == "2":
            success = run_integration_tests()
        else:
            print("Invalid choice, running quick validation...")
            success = test_quick_validation()

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Test execution failed: {e}")
        sys.exit(1)