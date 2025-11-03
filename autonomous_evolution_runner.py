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
from adaptive_action_limits import AdaptiveActionLimits
from network_intelligence_engine import NetworkIntelligenceEngine, display_network_intelligence_dashboard

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
        health_check_interval: int = 10,
        agi_mode: bool = False,  # Enable diversity-focused evolution
        specialist_mode: bool = False  # NEW: Enable specialist-focused evolution
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
            agi_mode: Enable diversity-focused generalization and anti-overfitting
            specialist_mode: Enable specialist-focused deep mastery (NEW)
        """
        self.db = DatabaseInterface(db_path)
        self.coordinator = OuroborosCoordinator(self.db)
        self.analyzer = PerformanceAnalyzer(self.db)
        self.factory = AgentFactory(self.db)
        self.adaptive_limits = AdaptiveActionLimits(self.db)  # Adaptive action limit manager
        self.network_intelligence = NetworkIntelligenceEngine(self.db)  # Network health tracking
        
        # META-LEARNING COMPONENTS (AGI MODE)
        if agi_mode:
            from meta_learning_curriculum import MetaLearningCurriculum
            from rule_induction_engine import RuleInductionEngine
            from visual_reasoning_engine import VisualReasoningEngine
            
            self.curriculum = MetaLearningCurriculum(self.db)
            self.rule_engine = RuleInductionEngine(self.db)
            self.visual_engine = VisualReasoningEngine(self.db)
            print("[*] Meta-learning components initialized")
        else:
            self.curriculum = None
            self.rule_engine = None
            self.visual_engine = None
        
        # SPECIALIST COORDINATOR (SPECIALIST MODE)
        if specialist_mode:
            from specialist_coordinator import SpecialistCoordinator
            
            self.specialist_coordinator = SpecialistCoordinator(self.db)
            print("[>] Specialist coordinator initialized")
        else:
            self.specialist_coordinator = None
        
        self.initial_population_size = initial_population_size
        self.games_per_generation = games_per_generation
        self.max_generations = max_generations
        self.target_win_rate = target_win_rate
        self.evolution_interval = timedelta(minutes=evolution_interval_minutes)
        self.health_check_interval = health_check_interval
        self.agi_mode = agi_mode  # Diversity mode flag
        self.specialist_mode = specialist_mode  # NEW: Specialist mode flag
        
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
            print(f"\n\n[WARN]️  Received {signal_name}")
            print("[?] Initiating graceful shutdown...")
            print("   (Press Ctrl+C again to force quit)\n")
            self.shutdown_requested = True
            self.running = False
        else:
            print(f"\n\n[X] Forced shutdown requested")
            print("   Terminating immediately (data may be incomplete)\n")
            sys.exit(1)
    
    async def _cleanup(self):
        """Perform cleanup operations before shutdown."""
        print("\n[?] Performing cleanup...")
        
        try:
            # Cancel current task if running
            if self.current_task and not self.current_task.done():
                print("  - Cancelling current task...")
                self.current_task.cancel()
                try:
                    await asyncio.wait_for(self.current_task, timeout=5.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
            
            # Force WAL checkpoint to save all pending writes
            print("  - Checkpointing database WAL...")
            if hasattr(self.db, 'checkpoint_wal'):
                self.db.checkpoint_wal()
            
            # Close database connections
            print("  - Closing database connections...")
            if hasattr(self.db, 'close'):
                self.db.close()
            
            # Save final state
            print("  - Saving final state...")
            self._save_checkpoint()
            
            print("[OK] Cleanup complete")
            
        except Exception as e:
            print(f"[WARN]️  Cleanup error (non-critical): {e}")
    
    def _cleanup_old_logs(self):
        """
        Clean up old system logs to prevent database bloat.
        Keeps only the last 10,000 most recent log entries.
        """
        try:
            # Get current log count
            count_result = self.db.execute_query("SELECT COUNT(*) as count FROM system_logs")
            total_logs = count_result[0]['count'] if count_result else 0
            
            if total_logs > 10000:
                # Delete old logs, keep newest 10,000
                deleted = self.db.execute_query("""
                    DELETE FROM system_logs 
                    WHERE id NOT IN (
                        SELECT id FROM system_logs 
                        ORDER BY timestamp DESC 
                        LIMIT 10000
                    )
                """)
                
                # Vacuum to reclaim space
                self.db.execute_query("VACUUM")
                
                logs_removed = total_logs - 10000
                print(f"  [?]  Cleaned up {logs_removed:,} old log entries (kept 10K most recent)")
                
        except Exception as e:
            print(f"  [WARN]️  Log cleanup failed (non-critical): {e}")
    
    def _save_checkpoint(self):
        """Save checkpoint data for resume capability."""
        try:
            # Checkpoint WAL first to ensure data is persisted
            if hasattr(self.db, 'checkpoint_wal'):
                self.db.checkpoint_wal()
            
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
                self.total_games_played = checkpoint.get('total_games_played', 0)  # NEW: Load game counter
                
                last_evo = checkpoint.get('last_evolution_time')
                if last_evo:
                    from dateutil import parser
                    self.last_evolution_time = parser.parse(last_evo)
                
                # ADDITIVE MAX GENERATIONS: If resuming from checkpoint, add configured generations to current
                # This makes --quick mean "5 MORE generations" instead of "max 5 total"
                if self.current_generation > 0:
                    original_max = self.max_generations
                    self.max_generations = self.current_generation + self.max_generations
                    print(f"[CHECKPOINT] Resuming from Generation {self.current_generation}")
                    print(f"[CHECKPOINT] Adjusted max_generations: {original_max} → {self.max_generations} (current + {original_max})")
                
                return checkpoint
            
        except Exception:
            pass
        
        return None
    
    def print_banner(self):
        """Print startup banner."""
        print("\n" + "="*80)
        print("[DNA] AUTONOMOUS EVOLUTION RUNNER")
        print("="*80)
        print(f"Started: {self.start_time}")
        print(f"Initial Population: {self.initial_population_size} agents")
        print(f"Games per Generation: {self.games_per_generation}")
        print(f"Max Generations: {self.max_generations}")
        print(f"Target Win Rate: {self.target_win_rate:.1%}")
        print(f"Evolution Interval: {self.evolution_interval.total_seconds()/60:.0f} minutes")
        print()
        
        # Specialist Mode indicator (NEW)
        if self.specialist_mode:
            print("[>] SPECIALIST MODE: ENABLED")
            print("   Focus: Deep mastery over generalization")
            print("   Strategy: Each agent masters 2-3 specific games")
            print("   Fitness: 100% performance on assigned games")
            print("   Goal: Achieve high scores (2.0-3.0+) through focused training")
            print()
        
        # Diversity Mode indicator
        elif self.agi_mode:
            print("[?] DIVERSITY MODE: ENABLED")
            print("   Focus: Generalization over specialization")
            print("   Strategy: Diverse games, anti-overfitting, novel game priority")
            print("   Fitness: 50% novel games + 30% few-shot + 20% diversity")
            print()
            print("[?] META-LEARNING: ENABLED")
            print("   Visual Reasoning: Analyzes grids for symmetry, patterns, shapes")
            print("   Rule Induction: Learns abstract IF-THEN rules from wins")
            print("   Curriculum: 4-stage progression (specialization [?] generalization)")
            print("   Fitness: 30% standard + 40% diversity + 30% meta-learning")
            print()
        
        print("[>] Adaptive Action Limits: ENABLED")
        print(f"   Adjusts per-level and total actions based on generation performance")
        print(f"   Hard floor: {self.adaptive_limits.MIN_ACTIONS_PER_LEVEL} actions/level")
        print(f"   Range: {self.adaptive_limits.MIN_TOTAL_ACTIONS}-{self.adaptive_limits.MAX_TOTAL_ACTIONS} total actions")
        print("="*80 + "\n")
    
    def print_status(self, generation: int, games_played: int, win_rate: float, 
                    avg_score: float, population_size: int):
        """Print current status."""
        runtime = datetime.now() - self.start_time
        hours = runtime.total_seconds() / 3600
        
        print(f"\n{'='*80}")
        print(f"[CHART] STATUS UPDATE - Generation {generation}")
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
            print(f"[OK] Found {agent_count} existing agents, skipping initialization")
            return True
        
        print(f"\n[DNA] Creating initial population ({self.initial_population_size} agents)...")
        
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
            
            print(f"[OK] Created {len(agents_created)} agents")
            
            # Initialize specialist assignments if in specialist mode
            if self.specialist_mode and self.specialist_coordinator:
                print(f"\n[>] Initializing specialist game assignments...")
                # Get available games
                try:
                    from arc_api_client import ARCAPIClient
                    api_key = os.getenv('ARC_API_KEY')
                    if api_key:
                        client = ARCAPIClient(api_key)
                        available_games = client.get_available_games()
                        game_ids = [g.get('id', g.get('game_id')) for g in available_games if g.get('id') or g.get('game_id')]
                        
                        if game_ids:
                            # Assign 2 games per specialist for focused training
                            self.specialist_coordinator.initialize_specialist_assignments(
                                [a.to_dict() for a in agents_created],
                                game_ids,
                                games_per_specialist=2
                            )
                except Exception as e:
                    print(f"[WARN]️  Could not initialize specialist assignments: {e}")
            
            return True
            
        except Exception as e:
            print(f"[?] Failed to create population: {e}")
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
        print(f"\n[?] Running {num_games} evaluation games...")
        
        # Get adaptive action limits for current generation
        actions_per_level, total_actions = self.adaptive_limits.adjust_limits(self.current_generation)
        self.adaptive_limits.print_status()
        
        try:
            import random
            
            api_key = os.getenv('ARC_API_KEY')
            if not api_key:
                print("[?] ARC_API_KEY not found in environment")
                return {'games_played': 0, 'wins': 0, 'win_rate': 0.0, 'avg_score': 0.0}
            
            # Get active agents
            agents = self.db.get_active_agents()
            if not agents:
                print("[?] No active agents found")
                return {'games_played': 0, 'wins': 0, 'win_rate': 0.0, 'avg_score': 0.0}
            
            # CRITICAL FIX: Distribute games_per_generation ACROSS all agents, not per agent
            # Old logic: games_per_agent = num_games // len(agents) meant 419 agents × 1 game = 419 games (70+ hours!)
            # New logic: Select subset of agents to play the total num_games
            # This ensures evolution completes in reasonable time (30-60 min)
            
            if len(agents) > num_games:
                # More agents than games: sample a subset of agents
                import random
                selected_agents = random.sample(agents, num_games)
                games_per_agent = 1  # Each selected agent plays 1 game
                print(f"  [NETWORK] Selected {len(selected_agents)} agents from {len(agents)} to play {num_games} games")
            else:
                # Fewer agents than games: each agent plays multiple games
                selected_agents = agents
                games_per_agent = max(1, num_games // len(agents))
                print(f"  [NETWORK] All {len(agents)} agents playing {games_per_agent} games each")
            
            async with GameplayEngine(api_key, db_path=self.db.db_path) as engine:
                
                # Get available games
                available_games = await engine.session_manager.get_available_games()
                
                if not available_games:
                    print("[?] No games available from API")
                    return {'games_played': 0, 'wins': 0, 'win_rate': 0.0, 'avg_score': 0.0}
                
                # SPECIALIST MODE: Auto-assign games if not already assigned (for resumed checkpoints)
                if self.specialist_mode and self.specialist_coordinator:
                    # Check if assignments exist
                    first_agent = selected_agents[0] if selected_agents else None
                    if first_agent:
                        assignments = self.specialist_coordinator.get_games_for_specialist(first_agent['agent_id'])
                        if not assignments:
                            print(f"\n[>] Auto-assigning specialists (resuming from checkpoint)...")
                            game_ids = [g.get('id', g.get('game_id')) for g in available_games if g.get('id') or g.get('game_id')]
                            self.specialist_coordinator.initialize_specialist_assignments(
                                selected_agents,  # FIXED: Use selected_agents
                                game_ids,
                                games_per_specialist=2
                            )
                            print(f"[OK] Assigned {len(game_ids)} games across {len(selected_agents)} specialists")
                
                results = []
                total_wins = 0
                total_score = 0
                rules_learned = 0  # NEW: Track rule learning
                
                for agent_idx, agent in enumerate(selected_agents):  # FIXED: Use selected_agents
                    agent_id = agent['agent_id']
                    
                    # SPECIALIST MODE: Use specialist coordinator for game selection (NEW)
                    if self.specialist_mode and self.specialist_coordinator:
                        # Select only assigned games for this specialist
                        agent_games = self.specialist_coordinator.select_games_for_agent(
                            agent_id,
                            [g.get('id', g.get('game_id')) for g in available_games],
                            games_per_agent
                        )
                        assigned = self.specialist_coordinator.get_games_for_specialist(agent_id)
                        print(f"  [>] Agent {agent_id[:8]} - Specialist on {assigned}: {len(agent_games)} games")
                    
                    # META-LEARNING: Use curriculum for game selection
                    elif self.curriculum:
                        # Initialize agent in curriculum if needed
                        if self.curriculum.get_agent_current_stage(agent_id) == 1 and \
                           not self.db.execute_query("SELECT 1 FROM curriculum_progress WHERE agent_id = ?", (agent_id,)):
                            self.curriculum.initialize_agent_curriculum(agent_id, self.current_generation)
                        
                        # Select games based on curriculum stage
                        agent_games = self.curriculum.select_games_for_agent(
                            agent_id, 
                            [g.get('id', g.get('game_id')) for g in available_games],
                            games_per_agent
                        )
                        print(f"  [?] Agent {agent_id[:8]} - Stage {self.curriculum.get_agent_current_stage(agent_id)}: {len(agent_games)} games")
                    else:
                        # Standard game selection
                        agent_games = [available_games[i % len(available_games)].get('id', available_games[i % len(available_games)].get('game_id')) 
                                      for i in range(games_per_agent)]
                    
                    # Run games for this agent
                    for game_idx, game_id in enumerate(agent_games):
                        if self.shutdown_requested:
                            print("[PAUSE]️  Shutdown requested, stopping evaluation")
                            break
                        
                        # Use adaptive action limits (adjusted per generation)
                        # Configure engine with current adaptive limits
                        engine.configure(
                            strategy='balanced',
                            max_actions_per_level=actions_per_level,  # Adaptive: adjusts based on performance
                            max_total_actions=total_actions,          # FIXED: was max_actions_per_game (wrong key!)
                            enable_random_exploration=True,
                            enable_pattern_learning=True,
                            # Diversity Mode settings (Rule 10: enhance existing)
                            diversity_mode=self.agi_mode,  # CHANGED: use diversity_mode instead of agi_mode
                            enforce_game_diversity=self.agi_mode,
                            max_repeats_per_game=5 if self.agi_mode else 999,
                            # Specialist Mode settings (NEW)
                            specialist_mode=self.specialist_mode
                        )
                        
                        # Play game - REAL ARC API CALL
                        # Wrap in cancellable task for graceful shutdown
                        try:
                            game_task = asyncio.create_task(engine.play_single_game(game_id, agent_id=agent_id))
                            result = await game_task
                        except asyncio.CancelledError:
                            # Game was cancelled during shutdown
                            print(f"[PAUSE]️  Game {game_id[:8]} cancelled")
                            if self.shutdown_requested:
                                break
                            raise
                        
                        # Process ARC rewards
                        rlvr = ARCRLVRFramework(self.db)
                        game_session_results = {
                            'game_id': game_id,
                            'session_id': engine.session_manager.current_session_id,
                            'win_detected': result.get('win', False),
                            'final_score': result.get('final_score', 0),
                            'win_score': 1.0,
                            'total_actions': result.get('actions_taken', 0),
                            'level_completions': int(result.get('final_score', 0)),  # Score = levels completed!
                            'frame_changes': 0
                        }
                        
                        reward_data = rlvr.process_arc_rewards(agent_id, game_session_results)
                        
                        # CRITICAL FIX: Store reward data so agents get credited for their games!
                        self.db.store_arc_reward_data(agent_id, reward_data)
                        
                        if result.get('win', False):
                            total_wins += 1
                            
                            # Extract rules from winning games for meta-learning
                            if self.rule_engine and hasattr(engine, 'session_manager'):
                                try:
                                    game_session_data = {
                                        'game_id': game_id,
                                        'agent_id': agent_id,
                                        'session_id': engine.session_manager.current_session_id,
                                        'initial_frame': result.get('initial_frame'),
                                        'action_sequence': result.get('action_sequence', []),
                                        'frame_states': result.get('frame_states', []),
                                        'won': True,
                                        'score_achieved': result.get('final_score', 0)
                                    }
                                    new_rule = self.rule_engine.extract_rule_from_game_session(game_session_data)
                                    if new_rule:
                                        print(f"  [?] Learned new rule: {new_rule['rule_name']}")
                                except Exception as e:
                                    print(f"  [WARN]️  Failed to extract rule: {e}")
                        
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
                
                # Update curriculum progress for this agent if meta-learning enabled
                if self.curriculum:
                    try:
                        self.curriculum.update_stage_progress(agent_id)
                    except Exception as e:
                        print(f"  [WARN]️  Failed to update curriculum: {e}")
                
                # Auto-cleanup logs every 50 games to prevent database bloat
                if self.total_games_played % 50 == 0:
                    print(f"\n[?]  Auto-cleanup triggered (every 50 games)...")
                    self._cleanup_old_logs()
                
                # CRITICAL: Sync agent performance from agent_arc_performance to agents table
                # This updates total_games_played, total_games_won, avg_score_per_game, score_efficiency
                agents_updated = self.db.sync_agent_performance_to_agents_table()
                print(f"[OK] Synced performance for {agents_updated} agents")
                
                # Calculate summary stats
                summary = {
                    'games_played': len(results),
                    'wins': total_wins,
                    'win_rate': total_wins / max(len(results), 1),
                    'avg_score': total_score / max(len(results), 1),
                    'timestamp': datetime.now()
                }
                
                print(f"[OK] Completed {len(results)} games")
                print(f"  Wins: {total_wins}/{len(results)} ({summary['win_rate']:.1%})")
                print(f"  Avg Score: {summary['avg_score']:.2f}")
                
                return summary
            
        except asyncio.CancelledError:
            # Task was cancelled during shutdown - this is expected
            print("[PAUSE]️  Evaluation cancelled during shutdown")
            raise  # Re-raise to propagate cancellation
            
        except Exception as e:
            if self.shutdown_requested:
                # Errors during shutdown are expected, just log briefly
                print(f"[WARN]️  Error during shutdown evaluation (ignored): {type(e).__name__}")
                return {'games_played': 0, 'wins': 0, 'win_rate': 0.0, 'avg_score': 0.0}
            else:
                # Real error - log details
                print(f"[?] Evaluation games failed: {e}")
                import traceback
                traceback.print_exc()
                return {'games_played': 0, 'wins': 0, 'win_rate': 0.0, 'avg_score': 0.0}
    
    async def analyze_and_evolve(self) -> bool:
        """
        Analyze population performance and evolve new generation.
        Rule 4: Claude Code analyzes and makes evolution decisions
        Uses comprehensive success rate (game wins + level completions + score achievements)
        
        Returns:
            True if evolution successful
        """
        print(f"\n[?] Analyzing population performance...")
        
        try:
            # Analyze current population
            analysis = self.analyzer.analyze_population_performance()
            
            pop_stats = analysis.get('population_stats', {})
            
            # Use comprehensive success rate (not just game wins)
            avg_success_rate = pop_stats.get('average_comprehensive_success', 0)
            avg_win_rate = pop_stats.get('average_win_rate', 0)
            population_size = pop_stats.get('population_size', 0)
            
            print(f"  Population: {population_size} agents")
            print(f"  Comprehensive Success Rate: {avg_success_rate:.2%} (wins + levels + scores)")
            print(f"  Game Win Rate: {avg_win_rate:.2%} (wins only)")
            print(f"  Best Win Rate: {pop_stats.get('best_win_rate', 0):.2%}")
            
            # Check if we should evolve
            if self.current_generation >= self.max_generations:
                print(f"[WARN]️  Reached max generations ({self.max_generations})")
                return False
            
            # Use comprehensive success rate for target check
            if avg_success_rate >= self.target_win_rate:
                print(f"[?] Reached target success rate ({self.target_win_rate:.1%})!")
                return False
            
            # Evolve new generation using EvolutionaryEngine
            print(f"\n[DNA] Evolving Generation {self.current_generation + 1}...")
            
            evolution_engine = EvolutionaryEngine(self.db)
            
            # Get top performers for breeding
            top_performers = analysis.get('top_performers', [])[:5]
            
            if not top_performers:
                print("[WARN]️  No agents with performance data, cannot evolve")
                return False
            
            # Determine evolution strategy based on comprehensive success
            if avg_success_rate < 0.1:
                strategy_focus = 'exploration'
            elif avg_success_rate < 0.3:
                strategy_focus = 'diversification'
            else:
                strategy_focus = 'exploitation'
            
            print(f"  Strategy: {strategy_focus} (based on {avg_success_rate:.1%} success rate)")
            
            # Create evolution strategy dict with diversity mode flag
            evolution_strategy = {
                'focus': strategy_focus,
                'diversity_mode': self.agi_mode,  # Pass diversity mode to evolutionary engine
                'specialist_mode': self.specialist_mode,  # Pass specialist mode to evolutionary engine (NEW)
                'generation': self.current_generation,
                'mutation_rate': 0.3 if strategy_focus == 'exploration' else 0.15,
                'crossover_rate': 0.7,
                'selection_pressure': 0.5,
                'elite_size': 2,
                'offspring_size': 5
            }
            
            # Use EvolutionaryEngine's evolve_population for proper fitness calculation
            # This applies meta-learning fitness (30/40/30 split) when diversity_mode=True
            print(f"\n[DNA] Calling evolve_population with diversity_mode={self.agi_mode}...")
            evolution_engine = EvolutionaryEngine(self.db)
            
            try:
                new_population = evolution_engine.evolve_population(evolution_strategy)
                new_agents_created = len(new_population)
                
                print(f"[OK] Evolution cycle complete")
                print(f"  New population size: {new_agents_created}")
                if self.agi_mode:
                    print(f"  Fitness calculation: 30% standard + 40% diversity + 30% meta-learning")
                
            except Exception as e:
                print(f"[WARN]️  Evolution failed: {e}")
                print(f"  Falling back to previous generation")
                return False
            
            self.current_generation += 1
            self.last_evolution_time = datetime.now()
            
            print(f"[OK] Evolution complete - Created {new_agents_created} new agents")
            
            # PHASE 0: CAPTURE NETWORK INTELLIGENCE SNAPSHOT
            print(f"\n[NETWORK] Capturing ecosystem snapshot for generation {self.current_generation}...")
            try:
                snapshot = self.network_intelligence.capture_ecosystem_snapshot(self.current_generation)
                print(f"[OK] Network snapshot captured: {snapshot['health_status']} (score: {snapshot['health_score']:.3f})")
                
                # Display network intelligence dashboard
                print()
                display_network_intelligence_dashboard(self.current_generation)
                
            except Exception as e:
                print(f"[WARN]️  Network snapshot failed: {e}")
                import traceback
                traceback.print_exc()
            
            # Optionally prune worst performers
            if population_size > self.initial_population_size * 2:
                print(f"\n[?] Population too large ({population_size}), pruning worst performers...")
                worst_performers = analysis.get('top_performers', [])[-3:]  # Get worst 3
                
                for agent in worst_performers:
                    self.db.execute_query(
                        "UPDATE agents SET is_active = 0 WHERE agent_id = ?",
                        (agent['agent_id'],)
                    )
                    print(f"  Deactivated: {agent['agent_id']}")
            
            return True
            
        except Exception as e:
            print(f"[?] Evolution failed: {e}")
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
        # Check for shutdown at start of cycle
        if self.shutdown_requested:
            print("[?] Shutdown requested - skipping cycle")
            return False
        
        # Health check
        health = self.check_system_health()
        if not health['healthy']:
            print(f"\n[WARN]️  System Health Issues:")
            for warning in health['warnings']:
                print(f"  - {warning}")
            
            if health['agent_count'] == 0:
                print("  Attempting to reinitialize population...")
                if not await self.initialize_population():
                    return False
        
        # Run evaluation games
        eval_results = await self.run_evaluation_games(self.games_per_generation)
        
        # CRITICAL: Force WAL checkpoint after every generation to prevent data loss
        try:
            self.db.checkpoint_wal()
            print(f"[?] WAL checkpoint after generation {self.current_generation}")
        except Exception as e:
            print(f"[WARN] Failed to checkpoint WAL: {e}")
        
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
                # Check if we hit targets (comprehensive success)
                if eval_results['win_rate'] >= self.target_win_rate:
                    print(f"\n[?] TARGET ACHIEVED! Win Rate: {eval_results['win_rate']:.1%}")
                    return False
                
                if self.current_generation >= self.max_generations:
                    print(f"\n[?]  Max generations reached")
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
            print(f"\n[DIR] Resuming from checkpoint:")
            print(f"   Generation: {checkpoint.get('current_generation', 0)}")
            print(f"   Games Played: {checkpoint.get('total_games_played', 0)}")
            print(f"   Last shutdown: {checkpoint.get('shutdown_time', 'unknown')}")
        
        self.print_banner()
        
        # Cleanup old logs on startup to prevent bloat from previous runs
        print("\n[?]  Performing startup database cleanup...")
        self._cleanup_old_logs()
        
        try:
            # Initialize population
            if not await self.initialize_population():
                print("[?] Failed to initialize - exiting")
                return
            
            print("\n[>>] Starting autonomous evolution...")
            print("Press Ctrl+C for graceful shutdown\n")
            
            cycle_count = 0
            
            while self.running and not self.shutdown_requested:
                cycle_count += 1
                print(f"\n{'='*80}")
                print(f"[CYCLE] EVOLUTION CYCLE #{cycle_count}")
                print(f"{'='*80}")
                
                # Check for shutdown request before starting cycle
                if self.shutdown_requested:
                    print("\n[?] Shutdown requested before cycle start")
                    break
                
                # Run cycle with task tracking for cancellation
                try:
                    self.current_task = asyncio.create_task(self.run_cycle())
                    should_continue = await self.current_task
                    
                    if not should_continue:
                        break
                    
                except asyncio.CancelledError:
                    print("\n[WARN]️  Current cycle cancelled - shutting down gracefully")
                    break
                
                except Exception as e:
                    if self.shutdown_requested:
                        # Ignore errors during shutdown - they're expected
                        print(f"\n[WARN]️  Error during shutdown (ignored): {type(e).__name__}")
                        break
                    else:
                        # Real error - log and continue
                        print(f"\n[WARN]️  Cycle error: {e}")
                        import traceback
                        traceback.print_exc()
                        # Continue to next cycle unless shutdown requested
                        if not self.shutdown_requested:
                            continue
                        break
                
                # Check shutdown between cycles
                if self.shutdown_requested:
                    print("\n[?] Shutdown requested between cycles")
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
            print("\n\n[PAUSE]️  Keyboard interrupt received")
            await self._cleanup()
            self.print_final_summary()
        
        except Exception as e:
            print(f"\n\n[?] Fatal error: {e}")
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
        print("[?] FINAL SUMMARY")
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
            # CRITICAL: Sync agent performance before final analysis
            agents_updated = self.db.sync_agent_performance_to_agents_table()
            print(f"\n[SYNC] Synced performance for {agents_updated} agents before final analysis")
            
            analysis = self.analyzer.analyze_population_performance()
            pop_stats = analysis.get('population_stats', {})
            
            print(f"\nFinal Performance:")
            print(f"  Comprehensive Success: {pop_stats.get('average_comprehensive_success', 0):.2%} (wins + levels + scores)")
            print(f"  Game Win Rate: {pop_stats.get('average_win_rate', 0):.2%} (wins only)")
            print(f"  Best Win Rate: {pop_stats.get('best_win_rate', 0):.2%}")
            print(f"  Avg Score: {pop_stats.get('average_score', 0):.2f}")
            print(f"  Population: {pop_stats.get('population_size', 0)} agents")
            
            # Top performers
            top = analysis.get('top_performers', [])[:3]
            if top:
                print(f"\nTop 3 Agents:")
                for i, agent in enumerate(top, 1):
                    agent_id = agent.get('agent_id', 'unknown')
                    win_rate = agent.get('win_rate', 0)
                    avg_score = agent.get('avg_score_per_game', agent.get('avg_score', 0))
                    total_games = agent.get('total_games_played', 0)
                    total_wins = agent.get('total_games_won', 0)
                    score_efficiency = agent.get('score_efficiency', 0)
                    
                    print(f"  {i}. {agent_id}:")
                    print(f"     Win Rate: {win_rate:.2%} ({total_wins}/{total_games} games)")
                    print(f"     Avg Score: {avg_score:.2f}, Efficiency: {score_efficiency:.4f}")
        
        except Exception as e:
            print(f"  (Could not load final stats: {e})")
            import traceback
            traceback.print_exc()
        
        print("="*80)
        print("\n[OK] Autonomous evolution runner stopped")
        print(f"Database: {self.db.db_path}")
        
        if self.shutdown_requested or not self.running:
            print("\n[SAVE] Checkpoint saved - progress preserved")
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
    
    parser.add_argument(
        '--diversity-mode',
        action='store_true',
        help='Enable diversity-focused evolution (diverse games, anti-overfitting, novel game priority)'
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
        evolution_interval_minutes=args.evolution_interval,
        agi_mode=args.diversity_mode  # NEW: Pass diversity mode flag
    )
    
    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
