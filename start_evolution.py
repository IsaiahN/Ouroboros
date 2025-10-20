#!/usr/bin/env python3
"""
Ouroboros Evolution Starter
Initializes and runs the autonomous evolutionary system
Following all Ouroboros rules - Claude Code as autonomous coordinator
"""

import os
import sys
import asyncio
import json
import uuid
import random
from datetime import datetime

# Rule 1: Disable pycache
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from database_logger import setup_database_logging
from database_interface import DatabaseInterface
from ouroboros_coordinator import OuroborosCoordinator
from agent_factory import AgentFactory
from evolutionary_engine import EvolutionaryEngine
from arc_rlvr_framework import ARCRLVRFramework
from performance_analyzer import PerformanceAnalyzer

# Rule 2: Database-only logging
db_handler = setup_database_logging(level='INFO')


def initialize_ouroboros_system():
    """
    Initialize the complete Ouroboros evolutionary system
    Rule 4: LLM Self-Management - Claude Code runs autonomously
    """
    
    print("=" * 70)
    print("OUROBOROS SYSTEM INITIALIZATION")
    print("Autonomous Evolution Framework for ARC AGI 3")
    print("=" * 70)
    print(f"Time: {datetime.now()}")
    print()
    
    # Check API key
    api_key = os.getenv('ARC_API_KEY')
    if not api_key or api_key == 'your_api_key_here':
        print("ERROR: Need valid API key in .env file")
        return None
    
    print(f"✓ API Key configured: {api_key[:8]}...")
    
    # Initialize database
    db_path = os.getenv('DATABASE_PATH', 'core_data.db')
    db = DatabaseInterface(db_path)
    
    print(f"✓ Database loaded: {db_path}")
    
    # Check existing data
    db_stats = db.get_database_stats()
    print(f"✓ Existing sessions: {db_stats.get('training_sessions_count', 0)}")
    print(f"✓ Existing game results: {db_stats.get('game_results_count', 0)}")
    print(f"✓ Existing action traces: {db_stats.get('action_traces_count', 0)}")
    
    # Check for Ouroboros tables
    agent_count = db.get_active_agent_count()
    print(f"✓ Active agents: {agent_count}")
    print()
    
    # Initialize coordinator
    print("Initializing Ouroboros Coordinator...")
    coordinator = OuroborosCoordinator(db)
    print(f"✓ Coordinator initialized: {coordinator.coordinator_id}")
    print()
    
    return coordinator, db


def create_initial_population(db: DatabaseInterface, population_size: int = 10):
    """
    Create initial agent population for evolution
    Rule 3: Clean integration - using existing agent system
    """
    
    print("=" * 70)
    print(f"CREATING INITIAL POPULATION ({population_size} agents)")
    print("=" * 70)
    print()
    
    factory = AgentFactory(db)
    
    # Define agent types to create
    agent_types = [
        'pattern_specialist',
        'score_optimizer',
        'exploration_agent',
        'win_focused_agent'
    ]
    
    agents_created = []
    
    for i in range(population_size):
        # Cycle through agent types
        agent_type = agent_types[i % len(agent_types)]
        
        # Generate random genome for initial population
        genome = {
            'agent_id': f"gen0_agent_{i}",
            'generation': 0,
            'pattern_sensitivity': random.uniform(0.5, 0.9),
            'coord_pattern': random.choice(['spiral', 'linear', 'random', 'grid']),
            'action_diversity': random.uniform(0.4, 0.8),
            'score_priority': random.uniform(0.6, 0.9),
            'efficiency_pref': random.uniform(0.5, 0.85),
            'win_threshold': random.uniform(0.7, 0.95),
            'exploration_rate': random.uniform(0.2, 0.6),
            'action_weights': {
                'ACTION1': random.uniform(0.1, 1.0),
                'ACTION2': random.uniform(0.1, 1.0),
                'ACTION3': random.uniform(0.1, 1.0),
                'ACTION4': random.uniform(0.1, 1.0),
                'ACTION6': random.uniform(0.1, 1.0),
                'ACTION7': random.uniform(0.1, 1.0),
            }
        }
        
        agent = factory.create_agent(agent_type, genome)
        agents_created.append(agent)
        
        print(f"  Agent {i+1}/{population_size}: {agent.agent_type} - {agent.agent_id}")
    
    print()
    print(f"✓ Created {len(agents_created)} agents")
    print()
    
    return agents_created


async def run_agent_evaluation_games(coordinator: OuroborosCoordinator, 
                                     db: DatabaseInterface,
                                     games_per_agent: int = 2):
    """
    Run evaluation games for all agents to gather performance data
    Rule 6 & 7: Real ARC games only, real actions
    """
    
    print("=" * 70)
    print("AGENT EVALUATION - Real ARC Games")
    print("=" * 70)
    print()
    
    from core_gameplay import GameplayEngine
    import random
    
    api_key = os.getenv('ARC_API_KEY')
    
    # Get active agents
    agents = db.get_active_agents()
    print(f"Agents to evaluate: {len(agents)}")
    print(f"Games per agent: {games_per_agent}")
    print()
    
    try:
        async with GameplayEngine(api_key, db_path=db.db_path) as engine:
            
            # Get available games
            available_games = await engine.session_manager.get_available_games()
            
            if not available_games:
                print("ERROR: No games available")
                return []
            
            print(f"Available games: {len(available_games)}")
            print()
            
            results = []
            
            for agent_idx, agent in enumerate(agents):
                agent_id = agent['agent_id']
                agent_type = agent['agent_type']
                
                print(f"{'='*70}")
                print(f"Agent {agent_idx + 1}/{len(agents)}: {agent_id}")
                print(f"Type: {agent_type}")
                print(f"{'='*70}")
                
                # Run games for this agent
                for game_num in range(games_per_agent):
                    game_idx = (agent_idx * games_per_agent + game_num) % len(available_games)
                    game = available_games[game_idx]
                    game_id = game.get('id', game.get('game_id'))
                    
                    # Random actions (200-300 for faster evaluation)
                    max_actions = random.randint(200, 300)
                    
                    print(f"\n  Game {game_num + 1}/{games_per_agent}: {game_id} ({max_actions} actions)")
                    
                    # Configure with agent-specific strategy
                    engine.configure(
                        strategy='balanced',
                        max_actions_per_game=max_actions,
                        enable_random_exploration=True
                    )
                    
                    # Play game
                    start_time = datetime.now()
                    result = await engine.play_single_game(game_id)
                    duration = (datetime.now() - start_time).total_seconds()
                    
                    print(f"    Score: {result['final_score']}, "
                          f"Actions: {result['actions_taken']}, "
                          f"Duration: {duration:.1f}s")
                    
                    # Process ARC rewards for this agent
                    rlvr = ARCRLVRFramework(db)
                    game_session_results = {
                        'game_id': game_id,
                        'session_id': engine.session_manager.current_session_id,
                        'win_detected': result['win'],
                        'final_score': result['final_score'],
                        'win_score': 1.0,  # Placeholder
                        'total_actions': result['actions_taken'],
                        'level_completions': 0,
                        'frame_changes': 0
                    }
                    
                    reward_data = rlvr.process_arc_rewards(agent_id, game_session_results)
                    
                    results.append({
                        'agent_id': agent_id,
                        'game_id': game_id,
                        'result': result,
                        'reward': reward_data
                    })
                    
                    # Brief pause
                    await asyncio.sleep(1)
                
                print(f"\n  Agent {agent_id} evaluation complete")
                print()
            
            print("=" * 70)
            print("EVALUATION COMPLETE")
            print("=" * 70)
            print(f"Total games played: {len(results)}")
            print()
            
            return results
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return []


def analyze_population_performance(db: DatabaseInterface):
    """
    Analyze current population performance
    Rule 4: Claude Code analyzes data for evolution decisions
    """
    
    print("=" * 70)
    print("POPULATION PERFORMANCE ANALYSIS")
    print("=" * 70)
    print()
    
    analyzer = PerformanceAnalyzer(db)
    
    try:
        analysis = analyzer.analyze_population_performance()
        
        print("Population Statistics:")
        pop_stats = analysis.get('population_stats', {})
        print(f"  Average Win Rate: {pop_stats.get('average_win_rate', 0):.3f}")
        print(f"  Best Win Rate: {pop_stats.get('best_win_rate', 0):.3f}")
        print(f"  Average Score: {pop_stats.get('average_score', 0):.2f}")
        print(f"  Population Size: {pop_stats.get('population_size', 0)}")
        print()
        
        print("Top Performers:")
        top_performers = analysis.get('top_performers', [])
        for i, agent in enumerate(top_performers[:5]):
            print(f"  {i+1}. {agent.get('agent_id', 'unknown')}: "
                  f"Win Rate {agent.get('win_rate', 0):.3f}, "
                  f"Score {agent.get('avg_score', 0):.2f}")
        print()
        
        return analysis
        
    except Exception as e:
        print(f"Analysis error: {e}")
        return None


async def main():
    """Main entry point for Ouroboros system"""
    
    import random
    random.seed()
    
    print()
    print("█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + "  OUROBOROS - Autonomous Evolution for ARC AGI 3".center(68) + "█")
    print("█" + "  Following All Implementation Rules".center(68) + "█")
    print("█" + " " * 68 + "█")
    print("█" * 70)
    print()
    
    # Step 1: Initialize system
    result = initialize_ouroboros_system()
    if not result:
        return
    
    coordinator, db = result
    
    # Step 2: Create initial population if needed
    agent_count = db.get_active_agent_count()
    
    if agent_count == 0:
        print("No agents found. Creating initial population...")
        print()
        agents = create_initial_population(db, population_size=5)  # Start with 5 agents
    else:
        print(f"Found {agent_count} existing agents. Skipping creation.")
        print()
    
    # Step 3: Run evaluation games
    print("Starting agent evaluation with real ARC games...")
    print()
    
    evaluation_results = await run_agent_evaluation_games(
        coordinator, 
        db, 
        games_per_agent=2  # 2 games per agent
    )
    
    print(f"Evaluation complete: {len(evaluation_results)} games played")
    print()
    
    # Step 4: Analyze performance
    analysis = analyze_population_performance(db)
    
    # Step 5: Summary
    print("=" * 70)
    print("OUROBOROS INITIALIZATION COMPLETE")
    print("=" * 70)
    print()
    print("System Status:")
    print(f"  ✓ Coordinator: {coordinator.coordinator_id}")
    print(f"  ✓ Active Agents: {db.get_active_agent_count()}")
    print(f"  ✓ Games Played: {len(evaluation_results)}")
    print(f"  ✓ Database: All data stored (Rule 2)")
    print()
    print("Next Steps:")
    print("  1. Run more evaluation games to build data")
    print("  2. Start evolution cycles with coordinator")
    print("  3. Monitor performance improvements")
    print()
    print("=" * 70)
    print()


if __name__ == "__main__":
    asyncio.run(main())
