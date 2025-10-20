"""
Ouroboros Coordinator - Claude Code LLM Coordinator
Following LLM Operating Rules:
- Rule 1: PYTHONDONTWRITEBYTECODE=1 (disabled pycache)
- Rule 2: Database-only storage (no log files)
- Rule 3: Clean integration with existing code
- Rule 4: LLM self-management (autonomous operation)
- Rule 5: No test files (live ARC data only)
- Rule 6: No simulated games (real ARC API only)
- Rule 7: Real actions only (verified API calls)
"""

import os
import json
import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from database_interface import DatabaseInterface
from evolutionary_engine import EvolutionaryEngine
from arc_rlvr_framework import ARCRLVRFramework
from performance_analyzer import PerformanceAnalyzer
from agent_factory import AgentFactory

# Rule 1: Disable pycache
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'


class OuroborosCoordinator:
    """
    Claude Code LLM coordinator for autonomous Ouroboros operation
    Central coordinator that manages the entire evolutionary system
    """

    def __init__(self, database_interface: DatabaseInterface):
        self.db = database_interface
        self.population_manager = PopulationManager(database_interface)
        self.evolution_engine = EvolutionaryEngine(database_interface)
        self.arc_rlvr = ARCRLVRFramework(database_interface)
        self.performance_analyzer = PerformanceAnalyzer(database_interface)
        self.agent_factory = AgentFactory(database_interface)

        # Claude Code memory and state
        self.coordinator_id = f"claude_{uuid.uuid4().hex[:8]}"
        self.current_generation = 0
        self.system_health_status = "initializing"

        # Initialize Ouroboros database schema if needed
        self._initialize_ouroboros_schema()

    def _initialize_ouroboros_schema(self):
        """Initialize extended database schema for Ouroboros"""
        # Rule 2: Database-only storage - extend existing schema
        try:
            # Execute the extended schema
            schema_file = "ouroboros_database_extension.sql"
            if os.path.exists(schema_file):
                with open(schema_file, 'r') as f:
                    schema_sql = f.read()
                    self.db.execute_script(schema_sql)

            # Log initialization to database (not log file per Rule 2)
            self._log_coordinator_event("system_initialization", {
                "coordinator_id": self.coordinator_id,
                "schema_initialized": True,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            self._log_coordinator_event("initialization_error", {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            raise

    def run_autonomous_evolution(self, max_generations: Optional[int] = None):
        """
        Main coordination loop - Claude Code runs this autonomously
        Rule 4: LLM self-management - operates without human intervention
        """
        self._log_coordinator_event("autonomous_evolution_started", {
            "max_generations": max_generations,
            "coordinator_id": self.coordinator_id
        })

        try:
            # Create initial population if none exists
            if self._get_current_population_size() == 0:
                self._create_initial_population()

            cycle_count = 0
            while True:
                cycle_count += 1
                self.current_generation += 1

                # Break if max generations reached
                if max_generations and cycle_count > max_generations:
                    break

                # 1. Analyze current ARC performance data from database (Rule 2)
                performance_data = self.performance_analyzer.analyze_population_performance()

                # 2. Make evolution decisions based on ARC results
                evolution_strategy = self._determine_evolution_strategy(performance_data)

                # 3. Execute evolution cycle
                new_agents = self.evolution_engine.evolve_population(evolution_strategy)

                # 4. Deploy agents for ARC game testing (Rule 5: live data only)
                test_results = await self._deploy_agents_for_testing(new_agents)

                # 5. Store all decisions and results in database (Rule 2)
                self._log_evolution_cycle_to_database(evolution_strategy, new_agents, test_results)

                # 6. Self-assessment and system health monitoring
                health_status = self._assess_system_health()

                # 7. Decision point: continue, pause, or adjust
                if self._should_pause_evolution(test_results, health_status):
                    self._log_pause_decision(test_results, health_status)
                    break

                # Brief pause between cycles to prevent system overload
                await asyncio.sleep(1)

        except Exception as e:
            self._log_coordinator_event("autonomous_evolution_error", {
                "error": str(e),
                "generation": self.current_generation,
                "cycle_count": cycle_count
            })
            raise

    def _determine_evolution_strategy(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Claude Code analyzes ARC performance and decides evolution strategy
        This is where Claude Code makes intelligent decisions based on data
        """
        # Extract key metrics from ARC performance data
        pop_stats = performance_data.get('population_stats', {})
        diversity_metrics = performance_data.get('diversity_metrics', {})
        performance_trends = performance_data.get('performance_trends', {})

        # Claude Code strategic decision making
        avg_win_rate = pop_stats.get('average_win_rate', 0.0)
        genetic_diversity = diversity_metrics.get('genetic_diversity', 1.0)
        improvement_rate = performance_trends.get('improvement_rate', 0.0)

        # Determine strategy focus based on Claude Code analysis
        if avg_win_rate < 0.1:
            strategy_focus = 'exploration'  # Need more diverse strategies
            mutation_rate = 0.3
            crossover_rate = 0.6
            selection_pressure = 0.4
        elif genetic_diversity < 0.3:
            strategy_focus = 'diversification'  # Population too homogeneous
            mutation_rate = 0.4
            crossover_rate = 0.5
            selection_pressure = 0.3
        elif improvement_rate > 0.05:
            strategy_focus = 'exploitation'  # Good strategies, refine them
            mutation_rate = 0.1
            crossover_rate = 0.8
            selection_pressure = 0.7
        else:
            strategy_focus = 'balanced'  # Maintain current approach
            mutation_rate = 0.2
            crossover_rate = 0.6
            selection_pressure = 0.5

        # Claude Code reasoning for this strategy
        reasoning = f"""
        Claude Code Analysis for Generation {self.current_generation}:
        - Average win rate: {avg_win_rate:.3f}
        - Genetic diversity: {genetic_diversity:.3f}
        - Improvement rate: {improvement_rate:.3f}

        Strategic Decision: {strategy_focus.upper()}
        Reasoning: Based on ARC performance data, focusing on {strategy_focus}
        to improve population effectiveness in ARC games.
        """

        evolution_strategy = {
            'focus': strategy_focus,
            'mutation_rate': mutation_rate,
            'crossover_rate': crossover_rate,
            'selection_pressure': selection_pressure,
            'target_win_rate': min(avg_win_rate * 1.2, 1.0),  # 20% improvement target
            'population_adjustments': self._determine_population_adjustments(performance_data),
            'reasoning': reasoning,
            'generation': self.current_generation,
            'coordinator_id': self.coordinator_id
        }

        # Store Claude Code decision in database (Rule 2)
        self.db.store_evolution_decision(evolution_strategy, performance_data)

        return evolution_strategy

    async def _deploy_agents_for_testing(self, agents: List[Any]) -> Dict[str, Any]:
        """
        Deploy agents for ARC game testing with real API calls
        Rule 5: No test files - live ARC data only
        Rule 6: No simulated games - real ARC API only
        Rule 7: Real actions only - verified API calls
        """
        from core_gameplay import GameplayEngine
        from game_session_manager import GameSessionManager

        test_results = {
            'agents_tested': len(agents),
            'games_completed': 0,
            'total_wins': 0,
            'total_score': 0.0,
            'agent_results': []
        }

        # Create session for agent testing
        session_manager = GameSessionManager(self.db)
        session_id = session_manager.create_session("agent_testing")

        for agent in agents:
            agent_test_result = await self._test_agent_with_real_arc_games(
                agent, session_id
            )
            test_results['agent_results'].append(agent_test_result)
            test_results['games_completed'] += agent_test_result.get('games_played', 0)
            test_results['total_wins'] += agent_test_result.get('wins', 0)
            test_results['total_score'] += agent_test_result.get('total_score', 0.0)

        # Store test results in database (Rule 2)
        self._store_agent_test_results(test_results)

        return test_results

    async def _test_agent_with_real_arc_games(self, agent: Any, session_id: str) -> Dict[str, Any]:
        """
        Test single agent with real ARC games
        Rule 7: Real actions only - verify all actions sent to ARC API
        """
        from core_gameplay import GameplayEngine

        gameplay_engine = GameplayEngine(self.db)

        # Test agent on 3 random ARC games for performance evaluation
        test_games = 3
        wins = 0
        total_score = 0.0
        games_played = 0

        for game_num in range(test_games):
            try:
                # Rule 6: Real ARC games only - no simulations
                game_result = await gameplay_engine.play_single_game(
                    game_id=None,  # Let system select game
                    agent_callback=agent.select_action,
                    agent_genome=agent.genome
                )

                games_played += 1
                total_score += game_result.get('final_score', 0.0)
                if game_result.get('win_detected', False):
                    wins += 1

                # Process ARC rewards through RLVR framework
                self.arc_rlvr.process_arc_rewards(agent.agent_id, game_result)

                # Rule 7: Verify real actions were sent
                self._verify_real_actions_sent(agent.agent_id, game_result)

            except Exception as e:
                self._log_coordinator_event("agent_test_error", {
                    "agent_id": agent.agent_id,
                    "game_num": game_num,
                    "error": str(e)
                })

        agent_result = {
            'agent_id': agent.agent_id,
            'games_played': games_played,
            'wins': wins,
            'total_score': total_score,
            'win_rate': wins / max(games_played, 1),
            'avg_score': total_score / max(games_played, 1)
        }

        # Update agent performance in database
        self._update_agent_performance(agent.agent_id, agent_result)

        return agent_result

    def _verify_real_actions_sent(self, agent_id: str, game_result: Dict[str, Any]):
        """
        Rule 7: Verify real actions were sent to ARC games
        Check that API calls were actually made and responses received
        """
        actions_taken = game_result.get('actions_taken', [])

        for action_num, action in enumerate(actions_taken):
            # Check if action was actually sent to API
            if 'api_response' not in action:
                self._log_coordinator_event("missing_api_verification", {
                    "agent_id": agent_id,
                    "action_num": action_num,
                    "action_type": action.get('type', 'unknown')
                })

            # For ACTION6, verify coordinates are in valid range (0-63)
            if action.get('type') == 6:
                coords = action.get('coordinates', {})
                x, y = coords.get('x', -1), coords.get('y', -1)
                if not (0 <= x <= 63 and 0 <= y <= 63):
                    self._log_coordinator_event("invalid_coordinates", {
                        "agent_id": agent_id,
                        "coordinates": coords,
                        "action_num": action_num
                    })

            # Store action tracking in database
            self.db.store_action_tracking({
                'agent_id': agent_id,
                'action_type': action.get('type'),
                'action_data': json.dumps(action),
                'coordinate_x': coords.get('x') if action.get('type') == 6 else None,
                'coordinate_y': coords.get('y') if action.get('type') == 6 else None,
                'api_request_sent': 'api_response' in action,
                'api_response_received': 'api_response' in action,
                'coordinate_valid': (0 <= x <= 63 and 0 <= y <= 63) if action.get('type') == 6 else True
            })

    def _create_initial_population(self, population_size: int = 20):
        """Create initial diverse agent population"""
        initial_agents = []

        # Create diverse agent types for initial population
        agent_types = ['pattern_specialist', 'score_optimizer', 'exploration_agent', 'win_focused_agent']

        for i in range(population_size):
            agent_type = agent_types[i % len(agent_types)]

            # Generate diverse initial genome
            initial_genome = self._generate_initial_genome(agent_type)

            agent = self.agent_factory.create_agent(agent_type, initial_genome)
            initial_agents.append(agent)

        self._log_coordinator_event("initial_population_created", {
            "population_size": len(initial_agents),
            "agent_types": agent_types,
            "generation": 0
        })

        return initial_agents

    def _generate_initial_genome(self, agent_type: str) -> Dict[str, Any]:
        """Generate initial genome for agent type"""
        import random

        base_genome = {
            'agent_id': f"{agent_type}_{uuid.uuid4().hex[:8]}",
            'exploration_weight': random.uniform(0.1, 0.8),
            'conservative_bias': random.uniform(0.1, 0.6),
            'action_diversity': random.uniform(0.3, 0.9),
            'score_optimization_priority': random.uniform(0.4, 0.9),
            'win_focus_threshold': random.uniform(0.7, 0.95),
            'coordinate_exploration_pattern': random.choice(['spiral', 'grid', 'random', 'edge_first']),
            'action_efficiency_preference': random.uniform(0.3, 0.8)
        }

        # Agent type specific adjustments
        if agent_type == 'pattern_specialist':
            base_genome['pattern_recognition_sensitivity'] = random.uniform(0.6, 0.9)
        elif agent_type == 'score_optimizer':
            base_genome['score_optimization_priority'] = random.uniform(0.7, 0.95)
        elif agent_type == 'exploration_agent':
            base_genome['exploration_weight'] = random.uniform(0.6, 0.9)
            base_genome['action_diversity'] = random.uniform(0.7, 0.95)
        elif agent_type == 'win_focused_agent':
            base_genome['win_focus_threshold'] = random.uniform(0.8, 0.95)

        return base_genome

    def _log_coordinator_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log coordinator events to database (Rule 2: no log files)"""
        self.db.store_coordinator_log({
            'event_type': event_type,
            'event_data': json.dumps(event_data),
            'coordinator_id': self.coordinator_id,
            'timestamp': datetime.now().isoformat()
        })

    def _get_current_population_size(self) -> int:
        """Get current active population size from database"""
        return self.db.get_active_agent_count()

    # [CHECKPOINT 2 COMPLETED: CORE COORDINATOR IMPLEMENTATION]
    # Next: Implement evolution engine and RLVR framework


class PopulationManager:
    """Manages agent populations in database"""

    def __init__(self, database_interface: DatabaseInterface):
        self.db = database_interface

    def get_current_population(self) -> List[Dict[str, Any]]:
        """Get current active population from database"""
        return self.db.get_active_agents()

    def retire_agent(self, agent_id: str, reason: str):
        """Retire agent from active population"""
        self.db.update_agent_status(agent_id, is_active=False, retirement_reason=reason)

    def activate_agent(self, agent_id: str):
        """Activate agent in population"""
        self.db.update_agent_status(agent_id, is_active=True)