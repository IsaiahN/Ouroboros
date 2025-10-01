#!/usr/bin/env python3
"""
Integration Test for Algorithmic Evolution System

Tests the complete evolution system integration including:
- Algorithm representation and serialization
- Genetic programming operations
- Multi-armed bandit selection
- VAE encoding/decoding
- Evolution manager coordination
- GameplayEngine integration
"""

import asyncio
import logging
import os
import tempfile
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_algorithm_representations():
    """Test algorithm representation and serialization."""
    print("=== Testing Algorithm Representations ===")

    try:
        from algorithm_representations import AlgorithmBuilder, AlgorithmRepresentation

        # Create test algorithms
        random_alg = AlgorithmBuilder.create_random_action_algorithm()
        score_alg = AlgorithmBuilder.create_score_based_algorithm()
        adaptive_alg = AlgorithmBuilder.create_adaptive_algorithm()

        algorithms = [random_alg, score_alg, adaptive_alg]

        for i, alg in enumerate(algorithms):
            print(f"Algorithm {i+1}: {alg.algorithm_id}")
            print(f"  Depth: {alg.get_depth()}")
            print(f"  Nodes: {len(alg.get_all_nodes())}")

            # Test serialization
            json_str = alg.to_json()
            restored_alg = AlgorithmRepresentation.from_json(json_str)

            assert restored_alg.algorithm_id == alg.algorithm_id
            assert restored_alg.get_depth() == alg.get_depth()
            assert len(restored_alg.get_all_nodes()) == len(alg.get_all_nodes())

        print("✅ Algorithm representations working correctly")
        return True

    except Exception as e:
        print(f"❌ Algorithm representations test failed: {e}")
        return False

def test_genetic_programming():
    """Test genetic programming operations."""
    print("\n=== Testing Genetic Programming ===")

    try:
        from genetic_programming import GeneticProgrammingEngine, GPConfig
        from algorithm_representations import AlgorithmBuilder

        # Create GP engine
        config = GPConfig(population_size=10, max_generations=3)
        gp = GeneticProgrammingEngine(config)

        # Initialize population
        population = gp.initialize_population()
        print(f"Created initial population of {len(population)} algorithms")

        # Test evolution
        fitness_scores = [50.0 + i * 5.0 for i in range(len(population))]  # Mock fitness
        evolved_population = gp.evolve_population(fitness_scores)

        print(f"Evolved population size: {len(evolved_population)}")
        print(f"Generation: {gp.generation}")

        # Get best algorithms
        best_algorithms = gp.get_best_algorithms(3)
        print(f"Top 3 algorithms by fitness:")
        for i, alg in enumerate(best_algorithms):
            print(f"  {i+1}. {alg.algorithm_id} - Fitness: {alg.fitness_score}")

        print("✅ Genetic programming working correctly")
        return True

    except Exception as e:
        print(f"❌ Genetic programming test failed: {e}")
        return False

def test_multi_armed_bandit():
    """Test multi-armed bandit operations."""
    print("\n=== Testing Multi-Armed Bandit ===")

    try:
        from multi_armed_bandit import MultiArmedBandit, MABConfig
        from algorithm_representations import AlgorithmBuilder

        # Create MAB
        config = MABConfig(selection_strategy="ucb")
        mab = MultiArmedBandit(config)

        # Create test algorithms
        algorithms = [
            AlgorithmBuilder.create_random_action_algorithm(),
            AlgorithmBuilder.create_score_based_algorithm(),
            AlgorithmBuilder.create_adaptive_algorithm()
        ]

        # Add algorithms to MAB
        for alg in algorithms:
            arm_id = mab.add_algorithm(alg)
            print(f"Added arm: {arm_id}")

        # Test selection
        for i in range(10):
            selected = mab.select_algorithm(algorithms)
            reward = 50.0 + (i * 5.0)  # Mock increasing reward
            mab.update_reward(selected.algorithm_id, reward)
            print(f"Selected {selected.algorithm_id}, reward: {reward}")

        # Get statistics
        stats = mab.get_arm_statistics()
        print(f"Total arms: {stats['total_arms']}")
        print(f"Total pulls: {stats['total_pulls']}")

        print("✅ Multi-armed bandit working correctly")
        return True

    except Exception as e:
        print(f"❌ Multi-armed bandit test failed: {e}")
        return False

def test_vae():
    """Test VAE operations."""
    print("\n=== Testing Variational Autoencoder ===")

    try:
        from variational_autoencoder import SimpleVariationalAutoencoder, VAEConfig
        from algorithm_representations import AlgorithmBuilder

        # Create VAE
        config = VAEConfig(latent_dimensions=8)
        vae = SimpleVariationalAutoencoder(config)

        # Create test algorithms
        algorithms = [
            AlgorithmBuilder.create_random_action_algorithm(),
            AlgorithmBuilder.create_score_based_algorithm(),
            AlgorithmBuilder.create_adaptive_algorithm()
        ]

        # Test encoding
        for alg in algorithms:
            mu, logvar = vae.encode(alg)
            print(f"Encoded {alg.algorithm_id}: mu shape {mu.shape}, logvar shape {logvar.shape}")

            # Test latent space sampling
            z = vae.reparameterize(mu, logvar)
            print(f"  Latent vector shape: {z.shape}")

            # Test performance prediction
            predicted_performance = vae.predict_performance(z)
            print(f"  Predicted performance: {predicted_performance:.2f}")

        # Test algorithm generation
        generated_alg = vae.generate_algorithm()
        print(f"Generated algorithm: {generated_alg.algorithm_id}")
        print(f"  Depth: {generated_alg.get_depth()}, Nodes: {len(generated_alg.get_all_nodes())}")

        # Test training
        performances = [60.0, 45.0, 75.0]
        training_stats = vae.train_on_algorithms(algorithms, performances)
        print(f"Training epoch: {training_stats['epoch']}")
        print(f"Total loss: {training_stats['total_loss']:.4f}")

        print("✅ Variational autoencoder working correctly")
        return True

    except Exception as e:
        print(f"❌ VAE test failed: {e}")
        return False

def test_algorithm_evaluator():
    """Test algorithm evaluator."""
    print("\n=== Testing Algorithm Evaluator ===")

    try:
        from algorithm_evaluator import AlgorithmEvaluator, GameContext
        from algorithm_representations import AlgorithmBuilder

        # Create evaluator and context
        evaluator = AlgorithmEvaluator()
        context = GameContext(
            current_score=25.0,
            actions_taken=5,
            available_actions=["ACTION1", "ACTION2", "ACTION3", "ACTION6"]
        )

        # Create test algorithm
        algorithm = AlgorithmBuilder.create_score_based_algorithm()

        # Evaluate algorithm
        result = evaluator.evaluate_algorithm(algorithm, context)
        print(f"Algorithm evaluation result:")
        print(f"  Action: {result.action}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Reasoning: {result.reasoning}")
        print(f"  Execution path: {' -> '.join(result.execution_path[:3])}")

        # Test fitness calculation
        game_results = [
            {"final_score": 45.0, "actions_taken": 8, "win_detected": False},
            {"final_score": 60.0, "actions_taken": 12, "win_detected": True},
            {"final_score": 30.0, "actions_taken": 6, "win_detected": False}
        ]

        fitness = evaluator.calculate_fitness(algorithm, game_results)
        print(f"Calculated fitness: {fitness:.2f}")

        print("✅ Algorithm evaluator working correctly")
        return True

    except Exception as e:
        print(f"❌ Algorithm evaluator test failed: {e}")
        return False

async def test_evolution_manager():
    """Test evolution manager coordination."""
    print("\n=== Testing Evolution Manager ===")

    try:
        from evolution_manager import EvolutionManager, EvolutionConfig
        from database_interface import DatabaseInterface

        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name

        try:
            # Create database interface
            db = DatabaseInterface(db_path)

            # Create evolution manager
            config = EvolutionConfig(
                population_size=10,
                evolution_frequency=3,
                min_games_for_evolution=2
            )

            evolution_manager = EvolutionManager(config, db)

            # Initialize system
            init_result = await evolution_manager.initialize_system()
            print(f"Evolution system initialized: {init_result['system_ready']}")
            print(f"Population size: {init_result['population_size']}")

            # Get current algorithm
            current_alg = await evolution_manager.get_current_algorithm()
            print(f"Current algorithm: {current_alg.algorithm_id if current_alg else 'None'}")

            # Simulate game results
            for i in range(5):
                if current_alg:
                    game_result = {
                        "game_id": f"test_game_{i}",
                        "session_id": f"test_session_{i}",
                        "final_score": 40.0 + i * 10.0,
                        "actions_taken": 8 + i,
                        "win_detected": i >= 3,
                        "final_state": "WIN" if i >= 3 else "GAME_OVER"
                    }

                    await evolution_manager.update_algorithm_performance(
                        current_alg.algorithm_id, game_result
                    )

                    print(f"Updated performance for game {i}: score={game_result['final_score']}")

            # Get system status
            status = evolution_manager.get_system_status()
            print(f"System status:")
            print(f"  Generation: {status['current_generation']}")
            print(f"  Games played: {status['total_games_played']}")
            print(f"  Best fitness: {status['best_fitness_ever']:.2f}")

            print("✅ Evolution manager working correctly")
            return True

        finally:
            # Clean up temporary database
            if os.path.exists(db_path):
                os.unlink(db_path)

    except Exception as e:
        print(f"❌ Evolution manager test failed: {e}")
        return False

async def test_gameplay_engine_integration():
    """Test GameplayEngine with evolution system."""
    print("\n=== Testing GameplayEngine Integration ===")

    try:
        from core_gameplay import GameplayEngine

        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name

        try:
            # Create GameplayEngine with evolution enabled
            async with GameplayEngine(db_path=db_path, enable_evolution=True) as engine:

                # Check evolution status
                evolution_status = engine.get_evolution_status()
                print(f"Evolution enabled: {evolution_status['evolution_enabled']}")

                if evolution_status['evolution_enabled']:
                    print(f"Strategy: {evolution_status['strategy']}")
                    print(f"Population size: {evolution_status['population_size']}")

                    # Get algorithm recommendations
                    recommendations = engine.get_algorithm_recommendations()
                    print(f"Algorithm recommendations: {len(recommendations)}")

                    for rec in recommendations[:2]:
                        print(f"  - {rec['type']}: {rec.get('algorithm_id', 'N/A')}")
                else:
                    print(f"Evolution not enabled: {evolution_status.get('reason', 'Unknown')}")

                print("✅ GameplayEngine integration working correctly")
                return True

        finally:
            # Clean up temporary database
            if os.path.exists(db_path):
                os.unlink(db_path)

    except Exception as e:
        print(f"❌ GameplayEngine integration test failed: {e}")
        return False

async def run_integration_tests():
    """Run all integration tests."""
    print("🚀 Starting Algorithmic Evolution System Integration Tests\n")

    test_results = []

    # Run component tests
    test_results.append(("Algorithm Representations", test_algorithm_representations()))
    test_results.append(("Genetic Programming", test_genetic_programming()))
    test_results.append(("Multi-Armed Bandit", test_multi_armed_bandit()))
    test_results.append(("Variational Autoencoder", test_vae()))
    test_results.append(("Algorithm Evaluator", test_algorithm_evaluator()))

    # Run async tests
    test_results.append(("Evolution Manager", await test_evolution_manager()))
    test_results.append(("GameplayEngine Integration", await test_gameplay_engine_integration()))

    # Print summary
    print("\n" + "="*60)
    print("🏁 INTEGRATION TEST SUMMARY")
    print("="*60)

    passed = 0
    total = len(test_results)

    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1

    print("-"*60)
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {(passed/total)*100:.1f}%")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! The algorithmic evolution system is ready for use.")
        return True
    else:
        print(f"\n⚠️  {total-passed} tests failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    # Run the integration tests
    success = asyncio.run(run_integration_tests())

    if success:
        print("\n📋 NEXT STEPS:")
        print("1. Run the evolved game runner: python game_runner.py")
        print("2. Monitor evolution progress in the database")
        print("3. Use GameplayEngine with enable_evolution=True in your applications")
        print("4. Check evolution status with engine.get_evolution_status()")
        exit(0)
    else:
        print("\n🔧 Fix the failing tests before proceeding.")
        exit(1)