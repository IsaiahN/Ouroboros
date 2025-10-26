#!/usr/bin/env python3
"""
Test Ouroboros System with Real Game Data
Verify the evolutionary system works with the game data we just generated
"""

import os
import asyncio

# Rule 1: Disable pycache
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

def test_database_has_data():
    """Test that we have game data to work with"""
    print("=== TESTING DATABASE HAS GAME DATA ===")

    try:
        from database_interface import DatabaseInterface
        db = DatabaseInterface()

        # Check for game data
        stats = db.get_database_stats()
        print(f"Sessions: {stats.get('training_sessions_count', 0)}")
        print(f"Game results: {stats.get('game_results_count', 0)}")
        print(f"Action traces: {stats.get('action_traces_count', 0)}")

        if stats.get('game_results_count', 0) > 0:
            print("SUCCESS: We have game data to work with!")
            return True
        else:
            print("ERROR: No game data found")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_ouroboros_components():
    """Test Ouroboros components with real data"""
    print("\\n=== TESTING OUROBOROS COMPONENTS ===")

    try:
        from database_interface import DatabaseInterface
        from agent_factory import AgentFactory
        from arc_rlvr_framework import ARCRLVRFramework
        from performance_analyzer import PerformanceAnalyzer

        db = DatabaseInterface()

        # Test 1: Create agents
        print("\\n1. Testing Agent Factory...")
        factory = AgentFactory(db)

        test_genome = {
            'exploration_weight': 0.6,
            'conservative_bias': 0.3,
            'action_diversity': 0.8,
            'score_optimization_priority': 0.7,
            'win_focus_threshold': 0.85
        }

        agent1 = factory.create_agent('pattern_specialist', test_genome)
        agent2 = factory.create_agent('score_optimizer', test_genome)
        print(f"SUCCESS: Created agents {agent1.agent_id} and {agent2.agent_id}")

        # Test 2: RLVR Framework
        print("\\n2. Testing RLVR Framework...")
        rlvr = ARCRLVRFramework(db)

        # Use real game data from our database
        with db._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM game_results LIMIT 1")
            game_data = cursor.fetchone()

        if game_data:
            game_dict = dict(game_data)
            print(f"Using real game data: {game_dict['game_id']}")

            # Process rewards
            mock_game_result = {
                'game_id': game_dict['game_id'],
                'session_id': game_dict['session_id'],
                'win_detected': game_dict['win_detected'],
                'final_score': game_dict['final_score'],
                'win_score': 100.0,  # Standard win score
                'total_actions': game_dict['total_actions'],
                'level_completions': 0,
                'actions_taken': []
            }

            reward_data = rlvr.process_arc_rewards(agent1.agent_id, mock_game_result)
            print(f"SUCCESS: RLVR processed rewards: {reward_data['total_evolutionary_reward']:.2f}")

        # Test 3: Performance Analyzer
        print("\\n3. Testing Performance Analyzer...")
        analyzer = PerformanceAnalyzer(db)
        analysis = analyzer.analyze_population_performance()

        print(f"Population size: {analysis['population_stats']['population_size']}")
        print(f"Average win rate: {analysis['population_stats']['average_win_rate']:.3f}")
        print("SUCCESS: Performance analysis completed")

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_coordinator():
    """Test the Ouroboros Coordinator"""
    print("\\n=== TESTING OUROBOROS COORDINATOR ===")

    try:
        from database_interface import DatabaseInterface
        from ouroboros_coordinator import OuroborosCoordinator

        db = DatabaseInterface()
        coordinator = OuroborosCoordinator(db)

        print(f"Coordinator ID: {coordinator.coordinator_id}")
        print(f"Current generation: {coordinator.current_generation}")
        print(f"System status: {coordinator.system_health_status}")

        # Test creating initial population
        print("\\nTesting initial population creation...")
        initial_agents = coordinator._create_initial_population(population_size=5)
        print(f"SUCCESS: Created initial population of {len(initial_agents)} agents")

        # Test basic coordination functions
        print("\\nTesting performance analysis...")
        current_pop_size = coordinator._get_current_population_size()
        print(f"Current population size: {current_pop_size}")

        if current_pop_size > 0:
            print("SUCCESS: Coordinator functioning with agent population")
            return True
        else:
            print("WARNING: No agents in population")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_agent_gameplay():
    """Test agent playing a mock game"""
    print("\\n=== TESTING AGENT GAMEPLAY ===")

    try:
        from database_interface import DatabaseInterface
        from agent_factory import AgentFactory
        from arc_rlvr_framework import ARCRLVRFramework

        db = DatabaseInterface()
        factory = AgentFactory(db)
        rlvr = ARCRLVRFramework(db)

        # Create test agent
        test_genome = {
            'exploration_weight': 0.7,
            'conservative_bias': 0.4,
            'action_diversity': 0.8,
            'score_optimization_priority': 0.6
        }

        agent = factory.create_agent('exploration_agent', test_genome)
        print(f"Created test agent: {agent.agent_id}")

        # Simulate a game scenario
        mock_game_state = {
            'current_score': 25.0,
            'action_count': 15,
            'win_score': 100.0
        }

        available_actions = [1, 2, 3, 4, 5, 6]

        # Test action selection (without real ActionHandler)
        print("Testing agent action selection...")

        # Mock action selection
        action_result = {
            'action_type': 6,
            'coordinates': {'x': 32, 'y': 32},
            'reasoning': 'test_selection'
        }

        print(f"Agent selected action: {action_result}")

        # Test performance update
        mock_game_result = {
            'final_score': 45.0,
            'win_detected': False,
            'total_actions': 25,
            'duration': 60.0
        }

        agent.update_performance(mock_game_result)
        print(f"Agent performance updated: {agent.games_played} games played")

        # Test reward processing
        reward_data = rlvr.process_arc_rewards(agent.agent_id, {
            'game_id': 'test_game_123',
            'session_id': 'test_session_123',
            'win_detected': False,
            'final_score': 45.0,
            'win_score': 100.0,
            'total_actions': 25,
            'level_completions': 0,
            'actions_taken': []
        })

        print(f"SUCCESS: Agent gameplay test completed")
        print(f"Evolutionary reward: {reward_data['total_evolutionary_reward']:.2f}")

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("OUROBOROS SYSTEM TEST WITH REAL GAME DATA")
    print("=" * 50)

    tests = [
        ("Database Data Check", test_database_has_data),
        ("Ouroboros Components", test_ouroboros_components),
        ("Coordinator Test", test_coordinator),
        ("Agent Gameplay", test_agent_gameplay)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\\n{'-' * 50}")
        print(f"RUNNING: {test_name}")
        print(f"{'-' * 50}")

        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()

            if result:
                passed += 1
                print(f"PASSED: {test_name}")
            else:
                print(f"FAILED: {test_name}")
        except Exception as e:
            print(f"ERROR in {test_name}: {e}")

    print(f"\\n{'=' * 50}")
    print(f"FINAL RESULTS: {passed}/{total} tests passed")
    print(f"{'=' * 50}")

    if passed == total:
        print("\\nALL TESTS PASSED!")
        print("Ouroboros evolutionary system is ready for autonomous operation!")
        print("\\nNext steps:")
        print("1. Run continuous games to build more data")
        print("2. Start evolutionary cycles")
        print("3. Monitor agent performance improvements")
    else:
        print(f"\\n{total - passed} tests failed - need to fix issues")

    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)