#!/usr/bin/env python3
"""
Autonomous Evolution Runner
===========================

Fully automated evolution system that runs continuously:
1. Creates initial population if needed
2. Runs evaluation games
3. Analyzes performance
4. Evolves new generations
5. Repeats until stopped or target achieved

Following Rule 4: LLM Self-Management - Claude Code coordinates everything
Following Rule 2: All data in database
Following Rules 5-7: Real games, real actions only
"""

import os
import sys
import asyncio
import time
import argparse
import signal
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

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
from performance_analyzer import PerformanceAnalyzer
from evolutionary_engine import EvolutionaryEngine
from arc_rlvr_framework import ARCRLVRFramework
from core_gameplay import GameplayEngine

# Rule 2: Database-only logging
logger = setup_database_logging(level='INFO')


class AutonomousEvolutionRunner:
    """
    Autonomous runner that manages the entire evolution lifecycle.
    
    This runner orchestrates:
    - Population initialization
    - Game evaluation cycles
    - Performance analysis
    - Evolution decisions
    - Continuous improvement loops
    """
    
    def __init__(
        self,
        db_path: str = "core_data.db",
        initial_population_size: int = 10,
        games_per_generation: int = 20,
        max_generations: int = 50,
        target_win_rate: float = 0.50,
        evolution_interval_minutes: int = 60,
        health_check_interval: int = 10
    ):
        """
        Initialize autonomous runner.
        
        Args:
            db_path: Database file path
            initial_population_size: Starting number of agents
            games_per_generation: Games to run per generation
            max_generations: Maximum generations to evolve
            target_win_rate: Stop when this win rate achieved
            evolution_interval_minutes: Minutes between evolution cycles
            health_check_interval: Games between health checks
        """
        self.db = DatabaseInterface(db_path)
        self.coordinator = OuroborosCoordinator(self.db)
        self.analyzer = PerformanceAnalyzer(self.db)
        self.factory = AgentFactory(self.db)
        
        self.initial_population_size = initial_population_size
        self.games_per_generation = games_per_generation
        self.max_generations = max_generations
        self.target_win_rate = target_win_rate
        self.evolution_interval = timedelta(minutes=evolution_interval_minutes)
        self.health_check_interval = health_check_interval
        
        self.current_generation = 0
        self.total_games_played = 0
        self.start_time = datetime.now()
        self.last_evolution_time = None
        
        self.running = False
        self.paused = False
        self.shutdown_requested = False
        self.current_task = None
        
        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        # Handle Ctrl+C (SIGINT) and termination (SIGTERM)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # On Windows, also handle CTRL_BREAK_EVENT
        if sys.platform == 'win32':
            try:
                signal.signal(signal.SIGBREAK, self._signal_handler)
            except AttributeError:
                pass  # SIGBREAK not available on all Windows versions
    
    def _signal_handler(self, signum, frame):
        """
        Handle shutdown signals gracefully.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        signal_names = {
            signal.SIGINT: 'SIGINT (Ctrl+C)',
            signal.SIGTERM: 'SIGTERM (Termination)',
        }
        if hasattr(signal, 'SIGBREAK'):
            signal_names[signal.SIGBREAK] = 'SIGBREAK (Ctrl+Break)'
        
        signal_name = signal_names.get(signum, f'Signal {signum}')
        
        if not self.shutdown_requested:
            print(f"\n\n⚠️  Received {signal_name}")
            print("🛑 Initiating graceful shutdown...")
            print("   (Press Ctrl+C again to force quit)\n")
            self.shutdown_requested = True
            self.running = False
        else:
            print(f"\n\n❌ Forced shutdown requested")
            print("   Terminating immediately (data may be incomplete)\n")
            sys.exit(1)
    
    async def _cleanup(self):
        """Perform cleanup operations before shutdown."""
        print("\n🧹 Performing cleanup...")
        
        try:
            # Cancel current task if running
            if self.current_task and not self.current_task.done():
                print("  - Cancelling current task...")
                self.current_task.cancel()
                try:
                    await asyncio.wait_for(self.current_task, timeout=5.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
            
            # Close database connections
            print("  - Closing database connections...")
            if hasattr(self.db, 'close'):
                self.db.close()
            
            # Save final state
            print("  - Saving final state...")
            self._save_checkpoint()
            
            print("✓ Cleanup complete")
            
        except Exception as e:
            print(f"⚠️  Cleanup error (non-critical): {e}")
    
    def _save_checkpoint(self):
        """Save checkpoint data for resume capability."""
        try:
            checkpoint = {
                'current_generation': self.current_generation,
                'total_games_played': self.total_games_played,
                'last_evolution_time': self.last_evolution_time.isoformat() if self.last_evolution_time else None,
                'shutdown_time': datetime.now().isoformat(),
                'shutdown_reason': 'graceful' if not self.shutdown_requested else 'forced'
            }
            
            # Store in database
            import json
            self.db.execute_query(
                "INSERT OR REPLACE INTO global_counters (counter_name, counter_value, description) "
                "VALUES (?, ?, ?)",
                ('evolution_checkpoint', self.current_generation, json.dumps(checkpoint))
            )
            
        except Exception as e:
            # Non-critical, just log
            pass
    
    def _load_checkpoint(self) -> Optional[Dict[str, Any]]:
        """Load checkpoint data if available."""
        try:
            result = self.db.execute_query(
                "SELECT counter_value, description FROM global_counters "
                "WHERE counter_name = ?",
                ('evolution_checkpoint',)
            )
            
            if result:
                import json
                checkpoint = json.loads(result[0]['description'])
                self.current_generation = checkpoint.get('current_generation', 0)
                
                last_evo = checkpoint.get('last_evolution_time')
                if last_evo:
                    from dateutil import parser
                    self.last_evolution_time = parser.parse(last_evo)
                
                return checkpoint
            
        except Exception:
            pass
        
        return None
    
    def print_banner(self):
        """Print startup banner."""
        print("\n" + "="*80)
        print("🧬 AUTONOMOUS EVOLUTION RUNNER")
        print("="*80)
        print(f"Started: {self.start_time}")
        print(f"Initial Population: {self.initial_population_size} agents")
        print(f"Games per Generation: {self.games_per_generation}")
        print(f"Max Generations: {self.max_generations}")
        print(f"Target Win Rate: {self.target_win_rate:.1%}")
        print(f"Evolution Interval: {self.evolution_interval.total_seconds()/60:.0f} minutes")
        print("="*80 + "\n")
    
    def print_status(self, generation: int, games_played: int, win_rate: float, 
                    avg_score: float, population_size: int):
        """Print current status."""
        runtime = datetime.now() - self.start_time
        hours = runtime.total_seconds() / 3600
        
        print(f"\n{'='*80}")
        print(f"📊 STATUS UPDATE - Generation {generation}")
        print(f"{'='*80}")
        print(f"Runtime: {hours:.1f} hours")
        print(f"Total Games: {games_played}")
        print(f"Active Agents: {population_size}")
        print(f"Win Rate: {win_rate:.2%}")
        print(f"Avg Score: {avg_score:.2f}")
        print(f"Games/Hour: {games_played/max(hours, 0.01):.1f}")
        print(f"{'='*80}\n")
    
    async def initialize_population(self) -> bool:
        """
        Initialize population if needed.
        Rule 3: Clean integration - using existing AgentFactory
        
        Returns:
            True if initialization successful or not needed
        """
        agent_count = self.db.get_active_agent_count()
        
        if agent_count > 0:
            print(f"✓ Found {agent_count} existing agents, skipping initialization")
            return True
        
        print(f"\n🧬 Creating initial population ({self.initial_population_size} agents)...")
        
        try:
            import random
            
            # Define agent types to create
            agent_types = [
                'pattern_specialist',
                'score_optimizer',
                'exploration_agent',
                'win_focused_agent'
            ]
            
            agents_created = []
            
            for i in range(self.initial_population_size):
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
                
                agent = self.factory.create_agent(agent_type, genome)
                agents_created.append(agent)
                
                print(f"  Agent {i+1}/{self.initial_population_size}: {agent.agent_type} - {agent.agent_id}")
            
            print(f"✓ Created {len(agents_created)} agents")
            return True
            
        except Exception as e:
            print(f"✗ Failed to create population: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def run_evaluation_games(self, num_games: int) -> Dict[str, Any]:
        """
        Run evaluation games with current population.
        Rule 6 & 7: Real ARC games only, real actions
        
        Args:
            num_games: Number of games to run
            
        Returns:
            Dictionary with game results summary
        """
        print(f"\n🎮 Running {num_games} evaluation games...")
        
        try:
            import random
            
            api_key = os.getenv('ARC_API_KEY')
            if not api_key:
                print("✗ ARC_API_KEY not found in environment")
                return {'games_played': 0, 'wins': 0, 'win_rate': 0.0, 'avg_score': 0.0}
            
            # Get active agents
            agents = self.db.get_active_agents()
            if not agents:
                print("✗ No active agents found")
                return {'games_played': 0, 'wins': 0, 'win_rate': 0.0, 'avg_score': 0.0}
            
            games_per_agent = max(1, num_games // len(agents))
            
            async with GameplayEngine(api_key, db_path=self.db.db_path) as engine:
                
                # Get available games
                available_games = await engine.session_manager.get_available_games()
                
                if not available_games:
                    print("✗ No games available from API")
                    return {'games_played': 0, 'wins': 0, 'win_rate': 0.0, 'avg_score': 0.0}
                
                results = []
                total_wins = 0
                total_score = 0
                
                for agent_idx, agent in enumerate(agents):
                    agent_id = agent['agent_id']
                    
                    # Run games for this agent
                    for game_num in range(games_per_agent):
                        if self.shutdown_requested:
                            print("⏸️  Shutdown requested, stopping evaluation")
                            break
                        
                        game_idx = (agent_idx * games_per_agent + game_num) % len(available_games)
                        game = available_games[game_idx]
                        game_id = game.get('id', game.get('game_id'))
                        
                        # Rule 8: max_actions_per_level = 200 as requested
                        max_actions = random.randint(400, 600)  # Total actions per game
                        
                        # Configure engine with agent-specific strategy
                        engine.configure(
                            strategy='balanced',
                            max_actions_per_level=200,  # Rule 8: Set to 200 as requested
                            max_actions_per_game=max_actions,
                            enable_random_exploration=True,
                            enable_pattern_learning=True
                        )
                        
                        # Play game - REAL ARC API CALL
                        result = await engine.play_single_game(game_id)
                        
                        # Process ARC rewards
                        rlvr = ARCRLVRFramework(self.db)
                        game_session_results = {
                            'game_id': game_id,
                            'session_id': engine.session_manager.current_session_id,
                            'win_detected': result.get('win', False),
                            'final_score': result.get('final_score', 0),
                            'win_score': 1.0,
                            'total_actions': result.get('actions_taken', 0),
                            'level_completions': 0,
                            'frame_changes': 0
                        }
                        
                        reward_data = rlvr.process_arc_rewards(agent_id, game_session_results)
                        
                        if result.get('win', False):
                            total_wins += 1
                        total_score += result.get('final_score', 0)
                        
                        results.append({
                            'agent_id': agent_id,
                            'game_id': game_id,
                            'result': result,
                            'reward': reward_data
                        })
                        
                        # Brief pause between games
                        await asyncio.sleep(0.5)
                    
                    if self.shutdown_requested:
                        break
                
                self.total_games_played += len(results)
                
                # Calculate summary stats
                summary = {
                    'games_played': len(results),
                    'wins': total_wins,
                    'win_rate': total_wins / max(len(results), 1),
                    'avg_score': total_score / max(len(results), 1),
                    'timestamp': datetime.now()
                }
                
                print(f"✓ Completed {len(results)} games")
                print(f"  Wins: {total_wins}/{len(results)} ({summary['win_rate']:.1%})")
                print(f"  Avg Score: {summary['avg_score']:.2f}")
                
                return summary
            
        except Exception as e:
            print(f"✗ Evaluation games failed: {e}")
            import traceback
            traceback.print_exc()
            return {'games_played': 0, 'wins': 0, 'win_rate': 0.0, 'avg_score': 0.0}
    
    async def analyze_and_evolve(self) -> bool:
        """
        Analyze population performance and evolve new generation.
        Rule 4: Claude Code analyzes and makes evolution decisions
        
        Returns:
            True if evolution successful
        """
        print(f"\n🧠 Analyzing population performance...")
        
        try:
            # Analyze current population
            analysis = self.analyzer.analyze_population_performance()
            
            pop_stats = analysis.get('population_stats', {})
            avg_win_rate = pop_stats.get('average_win_rate', 0)
            population_size = pop_stats.get('population_size', 0)
            
            print(f"  Population: {population_size} agents")
            print(f"  Avg Win Rate: {avg_win_rate:.2%}")
            print(f"  Best Win Rate: {pop_stats.get('best_win_rate', 0):.2%}")
            
            # Check if we should evolve
            if self.current_generation >= self.max_generations:
                print(f"⚠️  Reached max generations ({self.max_generations})")
                return False
            
            if avg_win_rate >= self.target_win_rate:
                print(f"🎉 Reached target win rate ({self.target_win_rate:.1%})!")
                return False
            
            # Evolve new generation using EvolutionaryEngine
            print(f"\n🧬 Evolving Generation {self.current_generation + 1}...")
            
            evolution_engine = EvolutionaryEngine(self.db)
            
            # Get top performers for breeding
            top_performers = analysis.get('top_performers', [])[:5]
            
            if not top_performers:
                print("⚠️  No agents with performance data, cannot evolve")
                return False
            
            # Determine evolution strategy based on performance
            if avg_win_rate < 0.1:
                strategy_focus = 'exploration'
            elif avg_win_rate < 0.3:
                strategy_focus = 'diversification'
            else:
                strategy_focus = 'exploitation'
            
            print(f"  Strategy: {strategy_focus}")
            
            # Create next generation through breeding
            new_agents_created = 0
            import random
            
            # Get crossover and mutation operators
            from evolutionary_engine import CrossoverOperations, MutationStrategies
            crossover_ops = CrossoverOperations()
            mutator = MutationStrategies()
            
            for i in range(3):  # Create 3 new agents per generation
                # Select two parents from top performers
                if len(top_performers) >= 2:
                    parent1 = random.choice(top_performers)
                    parent2 = random.choice(top_performers)
                    
                    # Get parent agent data
                    parent1_data = self.db.execute_query(
                        "SELECT * FROM agents WHERE agent_id = ?",
                        (parent1['agent_id'],)
                    )
                    parent2_data = self.db.execute_query(
                        "SELECT * FROM agents WHERE agent_id = ?",
                        (parent2['agent_id'],)
                    )
                    
                    if parent1_data and parent2_data:
                        # Crossover to create child genome
                        child_genome = crossover_ops.crossover_genomes(
                            parent1_data[0],
                            parent2_data[0]
                        )
                        
                        # Mutate child based on strategy
                        mutated_data = mutator.mutate_genome(
                            {'genome': child_genome},
                            strategy_focus=strategy_focus
                        )
                        
                        # Create new agent
                        agent_type = random.choice([
                            'pattern_specialist',
                            'score_optimizer',
                            'exploration_agent',
                            'win_focused_agent'
                        ])
                        
                        new_agent = self.factory.create_agent(agent_type, mutated_data['genome'])
                        new_agents_created += 1
                        
                        print(f"  Created agent: {new_agent.agent_id} (from {parent1['agent_id']} x {parent2['agent_id']})")
            
            self.current_generation += 1
            self.last_evolution_time = datetime.now()
            
            print(f"✓ Evolution complete - Created {new_agents_created} new agents")
            
            # Optionally prune worst performers
            if population_size > self.initial_population_size * 2:
                print(f"\n🌿 Population too large ({population_size}), pruning worst performers...")
                worst_performers = analysis.get('top_performers', [])[-3:]  # Get worst 3
                
                for agent in worst_performers:
                    self.db.execute_query(
                        "UPDATE agents SET is_active = 0 WHERE agent_id = ?",
                        (agent['agent_id'],)
                    )
                    print(f"  Deactivated: {agent['agent_id']}")
            
            return True
            
        except Exception as e:
            print(f"✗ Evolution failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def check_system_health(self) -> Dict[str, Any]:
        """
        Check system health metrics.
        
        Returns:
            Health status dictionary
        """
        try:
            db_stats = self.db.get_database_stats()
            agent_count = self.db.get_active_agent_count()
            
            # Check database size
            import os
            db_size_mb = os.path.getsize(self.db.db_path) / (1024 * 1024)
            
            health = {
                'healthy': True,
                'agent_count': agent_count,
                'db_size_mb': db_size_mb,
                'total_games': db_stats.get('game_results_count', 0),
                'log_count': db_stats.get('system_logs_count', 0),
                'warnings': []
            }
            
            # Health checks
            if agent_count == 0:
                health['healthy'] = False
                health['warnings'].append('No active agents')
            
            if db_size_mb > 1000:  # > 1 GB
                health['warnings'].append(f'Database large: {db_size_mb:.0f} MB')
            
            if db_stats.get('system_logs_count', 0) > 200000:
                health['warnings'].append('High log count - cleanup may be needed')
            
            return health
            
        except Exception as e:
            return {
                'healthy': False,
                'warnings': [f'Health check failed: {e}']
            }
    
    async def run_cycle(self) -> bool:
        """
        Run one complete evolution cycle.
        
        Returns:
            True if should continue, False if should stop
        """
        # Health check
        health = self.check_system_health()
        if not health['healthy']:
            print(f"\n⚠️  System Health Issues:")
            for warning in health['warnings']:
                print(f"  - {warning}")
            
            if health['agent_count'] == 0:
                print("  Attempting to reinitialize population...")
                if not await self.initialize_population():
                    return False
        
        # Run evaluation games
        eval_results = await self.run_evaluation_games(self.games_per_generation)
        
        # Print status
        self.print_status(
            generation=self.current_generation,
            games_played=self.total_games_played,
            win_rate=eval_results['win_rate'],
            avg_score=eval_results['avg_score'],
            population_size=health['agent_count']
        )
        
        # Check if we should evolve
        should_evolve = False
        
        if self.last_evolution_time is None:
            should_evolve = True  # First evolution
        elif datetime.now() - self.last_evolution_time >= self.evolution_interval:
            should_evolve = True  # Time for next evolution
        
        if should_evolve:
            success = await self.analyze_and_evolve()
            if not success:
                # Check if we hit targets
                if eval_results['win_rate'] >= self.target_win_rate:
                    print(f"\n🎉 TARGET ACHIEVED! Win Rate: {eval_results['win_rate']:.1%}")
                    return False
                
                if self.current_generation >= self.max_generations:
                    print(f"\n⏹️  Max generations reached")
                    return False
        
        # Continue running
        return True
    
    async def run(self):
        """Main autonomous evolution loop with graceful shutdown support."""
        self.running = True
        self.shutdown_requested = False
        
        # Try to load previous checkpoint
        checkpoint = self._load_checkpoint()
        if checkpoint:
            print(f"\n📂 Resuming from checkpoint:")
            print(f"   Generation: {checkpoint.get('current_generation', 0)}")
            print(f"   Last shutdown: {checkpoint.get('shutdown_time', 'unknown')}")
        
        self.print_banner()
        
        try:
            # Initialize population
            if not await self.initialize_population():
                print("✗ Failed to initialize - exiting")
                return
            
            print("\n🚀 Starting autonomous evolution...")
            print("Press Ctrl+C for graceful shutdown\n")
            
            cycle_count = 0
            
            while self.running and not self.shutdown_requested:
                cycle_count += 1
                print(f"\n{'='*80}")
                print(f"🔄 EVOLUTION CYCLE #{cycle_count}")
                print(f"{'='*80}")
                
                # Check for shutdown request before starting cycle
                if self.shutdown_requested:
                    print("\n🛑 Shutdown requested before cycle start")
                    break
                
                # Run cycle with task tracking for cancellation
                try:
                    self.current_task = asyncio.create_task(self.run_cycle())
                    should_continue = await self.current_task
                    
                    if not should_continue:
                        break
                    
                except asyncio.CancelledError:
                    print("\n⚠️  Current cycle cancelled")
                    break
                
                # Check shutdown between cycles
                if self.shutdown_requested:
                    print("\n🛑 Shutdown requested between cycles")
                    break
                
                # Brief pause between cycles (check for shutdown during pause)
                for _ in range(5):
                    if self.shutdown_requested:
                        break
                    await asyncio.sleep(1)
            
            # Cleanup before exit
            await self._cleanup()
            
            # Final summary
            self.print_final_summary()
            
        except KeyboardInterrupt:
            # Should be caught by signal handler, but just in case
            print("\n\n⏸️  Keyboard interrupt received")
            await self._cleanup()
            self.print_final_summary()
        
        except Exception as e:
            print(f"\n\n✗ Fatal error: {e}")
            import traceback
            traceback.print_exc()
            
            # Still try to cleanup
            try:
                await self._cleanup()
            except:
                pass
        
        finally:
            self.running = False
            
            # Ensure database connections are closed
            try:
                if hasattr(self.db, 'close'):
                    self.db.close()
            except:
                pass
    
    def print_final_summary(self):
        """Print final summary statistics."""
        runtime = datetime.now() - self.start_time
        hours = runtime.total_seconds() / 3600
        
        print("\n" + "="*80)
        print("📈 FINAL SUMMARY")
        print("="*80)
        
        # Shutdown reason
        if self.shutdown_requested:
            print("Shutdown Reason: User requested (graceful)")
        elif not self.running:
            print("Shutdown Reason: Target reached or max generations")
        else:
            print("Shutdown Reason: Normal completion")
        
        print(f"Total Runtime: {hours:.2f} hours ({runtime})")
        print(f"Total Games: {self.total_games_played}")
        print(f"Final Generation: {self.current_generation}")
        print(f"Games/Hour: {self.total_games_played/max(hours, 0.01):.1f}")
        
        # Get final stats
        try:
            analysis = self.analyzer.analyze_population_performance()
            pop_stats = analysis.get('population_stats', {})
            
            print(f"\nFinal Performance:")
            print(f"  Win Rate: {pop_stats.get('average_win_rate', 0):.2%}")
            print(f"  Best Win Rate: {pop_stats.get('best_win_rate', 0):.2%}")
            print(f"  Avg Score: {pop_stats.get('average_score', 0):.2f}")
            print(f"  Population: {pop_stats.get('population_size', 0)} agents")
            
            # Top performers
            top = analysis.get('top_performers', [])[:3]
            if top:
                print(f"\nTop 3 Agents:")
                for i, agent in enumerate(top, 1):
                    print(f"  {i}. {agent['agent_id']}: "
                          f"{agent.get('win_rate', 0):.2%} win rate, "
                          f"{agent.get('avg_score', 0):.2f} avg score")
        
        except Exception as e:
            print(f"  (Could not load final stats: {e})")
        
        print("="*80)
        print("\n✓ Autonomous evolution runner stopped")
        print(f"Database: {self.db.db_path}")
        
        if self.shutdown_requested or not self.running:
            print("\n💾 Checkpoint saved - progress preserved")
            print("To resume from this point:")
            print("  python autonomous_evolution_runner.py")
            print("  python run_evolution.py")
        else:
            print("\nEvolution complete!")
        
        print("="*80 + "\n")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Autonomous Evolution Runner for ARC AGI 3'
    )
    
    parser.add_argument(
        '--population', '-p',
        type=int,
        default=10,
        help='Initial population size (default: 10)'
    )
    
    parser.add_argument(
        '--games-per-gen', '-g',
        type=int,
        default=20,
        help='Games to run per generation (default: 20)'
    )
    
    parser.add_argument(
        '--max-generations', '-m',
        type=int,
        default=50,
        help='Maximum generations to evolve (default: 50)'
    )
    
    parser.add_argument(
        '--target-win-rate', '-t',
        type=float,
        default=0.50,
        help='Target win rate to achieve (default: 0.50)'
    )
    
    parser.add_argument(
        '--evolution-interval', '-i',
        type=int,
        default=60,
        help='Minutes between evolution cycles (default: 60)'
    )
    
    parser.add_argument(
        '--db-path',
        type=str,
        default='core_data.db',
        help='Database file path (default: core_data.db)'
    )
    
    args = parser.parse_args()
    
    # Validate API key
    api_key = os.getenv('ARC_API_KEY')
    if not api_key or api_key == 'your_api_key_here':
        print("ERROR: Need valid ARC_API_KEY in .env file")
        return
    
    # Create and run autonomous runner
    runner = AutonomousEvolutionRunner(
        db_path=args.db_path,
        initial_population_size=args.population,
        games_per_generation=args.games_per_gen,
        max_generations=args.max_generations,
        target_win_rate=args.target_win_rate,
        evolution_interval_minutes=args.evolution_interval
    )
    
    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
