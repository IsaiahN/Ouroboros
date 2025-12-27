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
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import sys
# Force UTF-8 encoding for stdout/stderr to prevent UnicodeEncodeError on Windows
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')  # type: ignore[union-attr]
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')  # type: ignore[union-attr]

import asyncio
from safe_cleanup import SafeDatabaseCleaner  # Primary cleanup routine
import time
import argparse
import signal
import subprocess
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
from enhanced_database_interface import EnhancedDatabaseInterface as DatabaseInterface
from evolution_with_vampires import check_for_vampires  # Vampire detection
from ouroboros_coordinator import OuroborosCoordinator
from agent_factory import AgentFactory
from performance_analyzer import PerformanceAnalyzer
from disk_space_monitor import DiskSpaceMonitor
from evolutionary_engine import EvolutionaryEngine
from arc_rlvr_framework import ARCRLVRFramework
from core_gameplay import GameplayEngine
from adaptive_action_limits import AdaptiveActionLimits
from network_intelligence_engine import NetworkIntelligenceEngine, display_network_intelligence_dashboard
from prestige_engine import PrestigeEngine, display_prestige_leaderboard
from viral_package_engine import ViralPackageEngine, display_viral_ecosystem_dashboard  # Phase 3
from evolution_game_scheduler import EvolutionGameScheduler  # NEW: Prevent duplicate game plays
from regulatory_signal_engine import RegulatorySignalEngine  # Phase 4: Distributed Regulation
from sequence_pruning_system import SequencePruningSystem  # NEW: Automatic bad sequence removal
from optimization_threshold_system import OptimizationThresholdSystem  # NEW: Track optimized levels
from breakthrough_budget_allocator import BreakthroughBudgetAllocator  # Tier 1: Dynamic budgets (+50%)
from automated_assessment_runner import AutomatedAssessmentRunner  # Other AI #3: Auto-metrics
# GameDiversityPreserver import removed - prestige-only protection now

# Autopoiesis Monitor - system health and emergence tracking
try:
    from autopoiesis_monitor import AutopoiesisMonitor
    AUTOPOIESIS_AVAILABLE = True
except ImportError:
    AUTOPOIESIS_AVAILABLE = False
    AutopoiesisMonitor = None

# CODS - Cognitive Operator Discovery System (post-generation unlock checks)
try:
    from cods_engine import check_for_potential_unlocks, CODSEngine
    CODS_AVAILABLE = True
except ImportError:
    CODS_AVAILABLE = False
    check_for_potential_unlocks = None
    CODSEngine = None

# Schema Auto-Maintenance - sync on startup to catch tables created by other modules
try:
    from schema_auto_maintenance import SchemaAutoMaintenance
    SCHEMA_MAINTENANCE_AVAILABLE = True
except ImportError:
    SCHEMA_MAINTENANCE_AVAILABLE = False
    SchemaAutoMaintenance = None

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
        evolution_interval_minutes: int = 60,
        health_check_interval: int = 10,
        agi_mode: bool = False,  # Enable diversity-focused evolution
        specialist_mode: bool = False,  # NEW: Enable specialist-focused evolution
        skip_cleanup: bool = False,  # Skip database cleanup on startup (for test mode)
        ensure_game_type_coverage: bool = False,  # Force one game per unique game type
        target_game: str | None = None  # NEW: Focus on specific game (e.g., "as66")
    ):
        """
        Initialize autonomous runner.
        
        Args:
            db_path: Database file path
            initial_population_size: Starting number of agents
            games_per_generation: Games to run per generation
            max_generations: Maximum generations to evolve
            evolution_interval_minutes: Minutes between evolution cycles
            health_check_interval: Games between health checks
            agi_mode: Enable diversity-focused generalization and anti-overfitting
            specialist_mode: Enable specialist-focused deep mastery (NEW)
            ensure_game_type_coverage: Force one game per unique game type (good when games_per_gen = num_types)
            target_game: Focus all agents on specific game prefix (e.g., "as66")
        """
        self.db = DatabaseInterface(db_path)
        self.coordinator = OuroborosCoordinator(self.db)
        self.analyzer = PerformanceAnalyzer(self.db)
        self.factory = AgentFactory(self.db)
        self.adaptive_limits = AdaptiveActionLimits(self.db)  # Adaptive action limit manager
        self.disk_monitor = DiskSpaceMonitor(db_path)  # Disk space monitoring
        self.network_intelligence = NetworkIntelligenceEngine(self.db)  # Network health tracking
        self.prestige_engine = PrestigeEngine(self.db)  # PHASE 1: Network contribution prestige
        self.viral_engine = ViralPackageEngine(self.db)  # PHASE 3: Viral packages & pariahs
        self.regulatory_engine = RegulatorySignalEngine(self.db)  # PHASE 4: Distributed regulation
        self.game_scheduler = EvolutionGameScheduler(self.db)  # NEW: Prevent duplicate game plays
        self.sequence_pruner = SequencePruningSystem(self.db)  # NEW: Automatic bad sequence removal
        self.optimization_tracker = OptimizationThresholdSystem(self.db)  # NEW: Track optimized levels
        self.budget_allocator = BreakthroughBudgetAllocator(self.db)  # TIER 1: Dynamic budgets (+50% gain)
        self.assessment_runner = AutomatedAssessmentRunner(self.db.db_path)  # OTHER AI #3: Auto-metrics
        # DIVERSITY PRESERVER DISABLED - prestige-only protection now
        
        # PHASE 5: Horizontal Gene Transfer with Emotional Intelligence
        from horizontal_transfer_engine import HorizontalTransferEngine
        self.transfer_engine = HorizontalTransferEngine(self.db)
        
        # NEW BREAKTHROUGH SYSTEMS (Tier 1-3)
        from subgoal_planner import SubgoalPlanner
        from frustration_detector import FrustrationDetector
        from near_miss_analyzer import NearMissAnalyzer
        from collective_reasoning_engine import CollectiveReasoningEngine
        from counterfactual_analyzer import CounterfactualAnalyzer
        
        self.subgoal_planner = SubgoalPlanner(self.db)  # Hierarchical planning
        self.frustration_detector = FrustrationDetector(self.db)  # Frustration quorum sensing
        self.near_miss_analyzer = NearMissAnalyzer(self.db)  # Learn from 15-18/20 scores
        self.collective_reasoner = CollectiveReasoningEngine(self.db)  # Multi-agent collaboration
        self.counterfactual_analyzer = CounterfactualAnalyzer(self.db)  # "What if?" analysis
        
        print("[OK] Breakthrough systems initialized (Subgoal Planning, Frustration Detection, Near-Miss Analysis, Collective Reasoning, Counterfactual Analysis)")
        
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
        
        # SPECIALIST COORDINATOR - DISABLED (replaced by prestige + operating modes)
        # Specialist system removed - prestige provides survival protection (0-80%)
        # Operating modes (pioneer/optimizer/generalist) handle mutation adaptation
        self.specialist_coordinator = None
        
        self.initial_population_size = initial_population_size
        self.games_per_generation = games_per_generation
        self.max_generations = max_generations
        self.evolution_interval = timedelta(minutes=evolution_interval_minutes)
        self.health_check_interval = health_check_interval
        self.agi_mode = agi_mode  # Diversity mode flag
        self.specialist_mode = specialist_mode  # NEW: Specialist mode flag
        self.skip_cleanup = skip_cleanup  # Skip database cleanup on startup
        self.ensure_game_type_coverage = ensure_game_type_coverage  # Force one game per type
        self.target_game = target_game  # Focus on specific game (e.g., "as66")
        
        self.current_generation = 0
        self.total_games_played = 0
        self.start_time = datetime.now()
        self.last_evolution_time = None
        
        self.running = False
        self.paused = False
        self.shutdown_requested = False
        self.shutdown_press_count = 0
        self.shutdown_last_press_time = None
        self.current_task = None
        
        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()
    
    def _calculate_target_population_from_db(self):
        """
        Calculate target population using dynamic performance-based formula.
        
        Formula (Option C - Dynamic Performance-Based):
            Base: 60 agents (minimum for role diversity)
            Bonus: +5 agents per unbeaten game (to assign pioneers)
            Max: 150 agents (to keep generation time ~1 hour)
        
        Returns:
            int: Target population (60 + unbeaten_games * 5, capped at 150)
        """
        BASE_POPULATION = 60  # Minimum for role diversity
        BONUS_PER_UNBEATEN = 5  # Extra agents per unbeaten game
        MAX_POPULATION = 150  # Cap to keep generation time reasonable
        
        try:
            # Count unbeaten games (games without full game win sequences)
            unbeaten_result = self.db.execute_query("""
                SELECT COUNT(DISTINCT SUBSTR(game_id, 1, 4)) as unbeaten_types
                FROM agent_arc_performance
                WHERE game_id IS NOT NULL
                AND SUBSTR(game_id, 1, 4) NOT IN (
                    SELECT DISTINCT SUBSTR(game_id, 1, 4)
                    FROM winning_sequences_full_game
                    WHERE is_active = 1
                )
            """)
            
            unbeaten_games = unbeaten_result[0]['unbeaten_types'] if unbeaten_result else 0
            
            # Calculate target: base + bonus for each unbeaten game
            target = BASE_POPULATION + (unbeaten_games * BONUS_PER_UNBEATEN)
            target = min(target, MAX_POPULATION)  # Cap at max
            
            print(f"  [POP] Dynamic population: {BASE_POPULATION} base + ({unbeaten_games} unbeaten * {BONUS_PER_UNBEATEN}) = {target} agents (max {MAX_POPULATION})")
            return target
            
        except Exception as e:
            # Fallback if query fails (e.g., table doesn't exist yet)
            print(f"  [WARN] Population calc failed ({e}), using base {BASE_POPULATION}")
            return BASE_POPULATION
    
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
        
        Uses sys.stderr.write instead of print() to avoid reentrant I/O errors
        on Windows when signal handler is called while another I/O operation
        is in progress.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        import sys
        
        signal_names = {
            signal.SIGINT: 'SIGINT (Ctrl+C)',
            signal.SIGTERM: 'SIGTERM (Termination)',
        }
        if hasattr(signal, 'SIGBREAK'):
            signal_names[signal.SIGBREAK] = 'SIGBREAK (Ctrl+Break)'
        
        signal_name = signal_names.get(signum, f'Signal {signum}')
        
        # Check if press is within time window (2 seconds)
        current_time = time.time()
        if self.shutdown_last_press_time is None or (current_time - self.shutdown_last_press_time) > 2.0:
            # Reset counter if too much time passed
            self.shutdown_press_count = 0
        
        # Increment press count
        self.shutdown_press_count += 1
        self.shutdown_last_press_time = current_time
        
        # Use sys.stderr.write to avoid reentrant print() issues on Windows
        try:
            if self.shutdown_press_count < 3:
                msg = (f"\n[WARNING] Ctrl+C press {self.shutdown_press_count}/3\n"
                       f"{'='*80}\n"
                       f"   Press {3 - self.shutdown_press_count} more time(s) within 2 seconds to shutdown\n"
                       f"   (Or press Ctrl+Break for immediate force quit)\n"
                       f"{'='*80}\n\n")
                sys.stderr.write(msg)
                sys.stderr.flush()
            else:
                # Third press - confirm shutdown
                msg = (f"\n\n[X] Ctrl+C pressed 3 times - Confirmed shutdown\n"
                       f"   Initiating graceful shutdown...\n"
                       f"   - ALL games will END IMMEDIATELY and save their scorecards\n"
                       f"   - No new games will start\n"
                       f"   - Database will be checkpointed\n\n")
                sys.stderr.write(msg)
                sys.stderr.flush()
                self.running = False
                self.shutdown_requested = True
                self.game_scheduler.shutdown()
                
                # CRITICAL: Also set shutdown flag on current engine if available
                # This ensures games in progress exit immediately
                if hasattr(self, '_current_engine') and self._current_engine:
                    self._current_engine.session_manager.is_shutting_down = True
                
                # Reset counter
                self.shutdown_press_count = 0
                self.shutdown_last_press_time = None
        except Exception:
            # If even stderr fails, just set shutdown flags silently
            self.running = False
            self.shutdown_requested = True
            try:
                self.game_scheduler.shutdown()
            except Exception:
                pass
    
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
            print(f"[WARN]  Cleanup error (non-critical): {e}")
    
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
            print(f"  [WARN]  Log cleanup failed (non-critical): {e}")
    
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
                # Specialist assignments disabled - prestige + modes handle selection
                # Prestige system provides earned survival protection (0-80%)
                # Operating modes (pioneer/optimizer/generalist) guide mutation rates
            
            return True
            
        except Exception as e:
            print(f"[?] Failed to create population: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _assign_agent_to_optimal_task(
        self,
        agent_id: str,
        agent_mode: str,
        available_games: list,
        games_per_agent: int
    ) -> list:
        """
        Smart agent-to-task assignment based on operating mode and WIN state.
        
        This addresses user concerns #1 and #2:
        - Knowledge distribution: Agents use community sequences automatically
        - Continuous optimization: Optimizers focus on reducing action counts
        
        Strategy (Win-state driven, not hardcoded thresholds):
        - Pioneer agents (10%): Games WITHOUT win state (frontier discovery)
          * Use best sequences until hitting unbeaten level, then explore
          * Prioritize games with partial progress (70%) over completely new (30%)
          
        - Optimizer agents (60%): ALL games, prioritize games with beaten levels
          * Focus on reducing action counts for ALREADY-BEATEN levels
          * Prioritize: max_level (more beaten levels) × avg_actions (more improvement room)
          * Will also work on unbeaten games, optimizing whatever levels exist
          
        - Generalist agents (30%): Balanced 50/50 split
          * 50% unbeaten games (frontier)
          * 50% beaten games (optimization)
        
        Once assigned, core_gameplay.py handles sequence selection automatically:
        - Queries best sequences by reliability → efficiency → actions
        - Uses community validation and Bayesian reputation
        - Pattern learning and sequence replay unchanged
        
        Args:
            agent_id: Agent identifier
            agent_mode: Operating mode ('pioneer', 'optimizer', 'generalist')
            available_games: List of available game objects
            games_per_agent: Number of games this agent should play
        
        Returns:
            List of game IDs assigned to this agent
        """
        import random
        
        # Get all game IDs
        all_game_ids = [g.get('id', g.get('game_id')) for g in available_games]
        
        if not all_game_ids:
            return []
        
        # Query community knowledge about each game
        game_stats = {}
        for game_id in all_game_ids:
            stats = self.db.execute_query("""
                SELECT 
                    MAX(level_progressions) as max_level,
                    COUNT(*) as attempts,
                    AVG(total_actions) as avg_actions,
                    MAX(CASE WHEN win_achieved = 1 THEN 1 ELSE 0 END) as has_win
                FROM agent_arc_performance
                WHERE game_id = ?
            """, (game_id,))
            
            if stats and stats[0]:
                game_stats[game_id] = {
                    'max_level': stats[0]['max_level'] or 0,
                    'attempts': stats[0]['attempts'] or 0,
                    'avg_actions': stats[0]['avg_actions'] or 0,
                    'has_win': bool(stats[0]['has_win'])  # True if community has won this game
                }
            else:
                game_stats[game_id] = {
                    'max_level': 0,
                    'attempts': 0,
                    'avg_actions': 0,
                    'has_win': False
                }
        
        # Also check winning_sequences table for known sequences
        sequences_by_game = {}
        for game_id in all_game_ids:
            sequences = self.db.execute_query("""
                SELECT 
                    COUNT(*) as sequence_count,
                    AVG(total_actions) as avg_sequence_actions
                FROM winning_sequences
                WHERE game_id = ?
            """, (game_id,))
            
            if sequences and sequences[0] and sequences[0]['sequence_count']:
                sequences_by_game[game_id] = {
                    'count': sequences[0]['sequence_count'],
                    'avg_actions': sequences[0]['avg_sequence_actions']
                }
        
        # PIONEER MODE: Focus on games WITHOUT WIN state (frontier discovery)
        if agent_mode == 'pioneer':
            # Find games where community hasn't won yet
            unbeaten_games = [
                game_id for game_id, stats in game_stats.items()
                if not stats['has_win']
            ]
            
            if unbeaten_games:
                # Prioritize games with some progress over completely untried games
                # This helps pioneers build on partial knowledge
                tried_unbeaten = [g for g in unbeaten_games if game_stats[g]['attempts'] > 0]
                untried_unbeaten = [g for g in unbeaten_games if game_stats[g]['attempts'] == 0]
                
                # 70% tried (with partial knowledge), 30% completely new
                num_tried = int(games_per_agent * 0.7)
                num_untried = games_per_agent - num_tried
                
                selected = []
                if tried_unbeaten:
                    selected.extend(random.sample(tried_unbeaten, min(num_tried, len(tried_unbeaten))))
                if untried_unbeaten and len(selected) < games_per_agent:
                    selected.extend(random.sample(untried_unbeaten, min(num_untried, len(untried_unbeaten))))
                
                # Fill remaining with any unbeaten games
                while len(selected) < games_per_agent and unbeaten_games:
                    game = random.choice(unbeaten_games)
                    if game not in selected:
                        selected.append(game)
                
                if len(selected) >= games_per_agent:
                    return selected[:games_per_agent]
            
            # Fallback: if all games are beaten, work on optimization
            # (pioneers become temporary optimizers when frontier is exhausted)
            games_with_wins = [g for g, s in game_stats.items() if s['has_win']]
            if games_with_wins:
                return random.sample(games_with_wins, min(games_per_agent, len(games_with_wins)))
            
            # Ultimate fallback: random games
            return random.sample(all_game_ids, min(games_per_agent, len(all_game_ids)))
        
        # OPTIMIZER MODE: Focus on BEATEN games/levels ONLY - reduce action counts
        elif agent_mode == 'optimizer':
            # CRITICAL: Optimizers REQUIRE sequences to optimize
            # Without sequences, there's nothing to improve - skip the agent
            
            # Get games where community has proven sequences
            games_with_sequences = [
                game_id for game_id in all_game_ids
                if game_id in sequences_by_game and sequences_by_game[game_id]['count'] > 0
            ]
            
            if not games_with_sequences:
                # No sequences available - optimizer cannot operate
                print(f"  [OPTIMIZER] No games with sequences available, skipping agent")
                return []
            
            # Use optimization threshold system for games with sequences
            optimization_targets = self.optimization_tracker.get_optimization_targets(
                agent_mode='optimizer',
                limit=games_per_agent * 2  # Get extra targets for filtering
            )
            
            # Filter targets to ONLY games with sequences
            sequence_targets = [t for t in optimization_targets 
                              if t['game_id'] in games_with_sequences and t['priority_class'] != 'unbeaten']
            
            # Extract game IDs from sequence targets
            target_games = list(set(t['game_id'] for t in sequence_targets))
            
            # Prioritize unoptimized games with sequences
            unoptimized_targets = [t['game_id'] for t in sequence_targets if t['priority_class'] == 'unoptimized']
            
            selected = []
            
            # Priority: Unoptimized games with sequences (can still improve)
            if unoptimized_targets:
                selected.extend(random.sample(unoptimized_targets, min(games_per_agent, len(unoptimized_targets))))
            
            # If we have enough targets, return them
            if len(selected) >= games_per_agent:
                return selected[:games_per_agent]
            
            # Fallback: If optimization tracker has no targets, use games with sequences
            # (this happens on first generation before tracking is populated)
            if len(selected) < games_per_agent:
                print(f"  [OPTIMIZER] Using fallback assignment - games with sequences only")
                
                # Prioritize games with more sequences (more data to optimize from)
                sequence_priority = [
                    {
                        'game_id': game_id,
                        'sequence_count': sequences_by_game[game_id]['count'],
                        'avg_actions': sequences_by_game[game_id]['avg_actions']
                    }
                    for game_id in games_with_sequences
                ]
                
                # Sort by sequence count
                sequence_priority.sort(key=lambda x: x['sequence_count'], reverse=True)
                
                # Fill remaining slots
                remaining = games_per_agent - len(selected)
                for item in sequence_priority:
                    if item['game_id'] not in selected:
                        selected.append(item['game_id'])
                        remaining -= 1
                        if remaining <= 0:
                            break
            
            if selected:
                print(f"  [OPTIMIZER] Assigned {len(selected)} games with sequences to optimize")
                return selected
            
            # Ultimate fallback: no viable games
            print(f"  [OPTIMIZER] No viable optimization targets, skipping agent")
            return []
        
        
        # EXPLOITER MODE: ONLY games with proven sequences (harvest wins efficiently)
        elif agent_mode == 'exploiter':
            # Exploiters REQUIRE proven sequences - filter to games with sequences only
            games_with_sequences = [
                game_id for game_id in all_game_ids
                if game_id in sequences_by_game and sequences_by_game[game_id]['count'] > 0
            ]
            
            if not games_with_sequences:
                # No sequences available - exploiter cannot operate
                # Return empty list to skip this agent (better than 0-action waste)
                print(f"  [EXPLOITER] No games with sequences available, skipping agent")
                return []
            
            # Prioritize games with MORE sequences (more proven = more reliable)
            sequence_priority = [
                {
                    'game_id': game_id,
                    'sequence_count': sequences_by_game[game_id]['count'],
                    'avg_actions': sequences_by_game[game_id]['avg_actions']
                }
                for game_id in games_with_sequences
            ]
            
            # Sort by sequence count (more sequences = more reliable)
            sequence_priority.sort(key=lambda x: x['sequence_count'], reverse=True)
            
            # Select top games with most sequences
            selected = [g['game_id'] for g in sequence_priority[:games_per_agent]]
            
            print(f"  [EXPLOITER] Assigned {len(selected)} games with proven sequences (avg {sum(g['sequence_count'] for g in sequence_priority[:len(selected)]) / max(len(selected), 1):.1f} sequences/game)")
            
            return selected
        
        # GENERALIST MODE: Balanced mix of unbeaten and optimization targets
        else:
            # 50% unbeaten games (frontier), 50% beaten games (optimization)
            unbeaten_games = [g for g, s in game_stats.items() if not s['has_win']]
            beaten_games = [g for g, s in game_stats.items() if s['has_win']]
            
            num_frontier = int(games_per_agent * 0.5)
            num_optimize = games_per_agent - num_frontier
            
            selected = []
            
            # Add frontier games (unbeaten)
            if unbeaten_games:
                selected.extend(random.sample(unbeaten_games, min(num_frontier, len(unbeaten_games))))
            
            # Add optimization targets (beaten games)
            if beaten_games:
                selected.extend(random.sample(beaten_games, min(num_optimize, len(beaten_games))))
            
            # Fill remaining with random games if we don't have enough
            while len(selected) < games_per_agent:
                game = random.choice(all_game_ids)
                if game not in selected:
                    selected.append(game)
            
            return selected[:games_per_agent]
    
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
            
            # DYNAMIC ROLE ASSIGNMENT: Assign operating modes for this generation
            # ADAPTIVE POPULATION: Distribution changes based on whether games have been beaten
            # EXPLORATION: 40% PIONEER, 40% OPTIMIZER, 20% GENERALIST (no full wins yet)
            # OPTIMIZATION: 10% PIONEER, 60% OPTIMIZER, 30% GENERALIST (at least one full win)
            from agent_operating_mode_system import AgentOperatingModeSystem
            mode_system = AgentOperatingModeSystem(self.db)
            
            # Check if we should transition phases (exploration → optimization)
            phase_changed = mode_system.check_and_update_phase()
            if phase_changed:
                print(f"[PHASE] Transitioned to {mode_system.phase} phase!")
            
            agent_ids = [a['agent_id'] for a in agents]
            mode_assignments = mode_system.assign_population_modes(self.current_generation, agent_ids)
            distribution = mode_system.get_population_mode_distribution(self.current_generation)
            print(f"[MODE] {mode_system.phase} phase - Dynamic roles: {distribution['pioneer']} pioneers, {distribution['optimizer']} optimizers, {distribution['generalist']} generalists, {distribution['exploiter']} exploiters")
            
            # CRITICAL FIX: Distribute games_per_generation ACROSS all agents, not per agent
            # Old logic: games_per_agent = num_games // len(agents) meant 419 agents × 1 game = 419 games (70+ hours!)
            # New logic: Select subset of agents to play the total num_games
            # This ensures evolution completes in reasonable time (30-60 min)
            
            # YOUTH BONUS: Newer agents get more opportunities to prove themselves
            # Philosophy: Network gets stronger each generation, so newer agents have better DNA
            # This is OPPORTUNITY (more chances), not unearned PRESTIGE (credibility)
            from evolutionary_engine import calculate_youth_bonus
            
            if len(agents) > num_games:
                # More agents than games: weighted sampling favoring younger agents
                # Calculate youth-weighted selection probabilities
                weights = []
                for agent in agents:
                    agent_gen = agent.get('generation', 0)
                    youth_bonus = calculate_youth_bonus(agent_gen, self.current_generation)
                    weights.append(youth_bonus)
                
                # Normalize weights to probabilities
                total_weight = sum(weights)
                probabilities = [w / total_weight for w in weights]
                
                # Weighted sampling without replacement
                import random
                import numpy as np
                try:
                    # Use numpy for efficient weighted sampling without replacement
                    indices = np.random.choice(
                        len(agents), 
                        size=num_games, 
                        replace=False, 
                        p=probabilities
                    )
                    selected_agents = [agents[i] for i in indices]
                except ImportError:
                    # Fallback: simple weighted sampling (less efficient but works)
                    selected_agents = []
                    remaining = list(zip(agents, weights))
                    for _ in range(num_games):
                        if not remaining:
                            break
                        total = sum(w for _, w in remaining)
                        r = random.random() * total
                        cumulative = 0
                        for i, (agent, weight) in enumerate(remaining):
                            cumulative += weight
                            if r <= cumulative:
                                selected_agents.append(agent)
                                remaining.pop(i)
                                break
                
                games_per_agent = 1  # Each selected agent plays 1 game
                
                # Log youth bonus effect
                avg_bonus = sum(weights) / len(weights) if weights else 1.0
                young_count = sum(1 for a in selected_agents if self.current_generation - a.get('generation', 0) <= 2)
                print(f"  [YOUTH] Selected {len(selected_agents)} agents (avg youth bonus: {avg_bonus:.2f}x, {young_count} young agents)")
            else:
                # Fewer agents than games: each agent plays multiple games
                selected_agents = agents
                games_per_agent = max(1, num_games // len(agents))
                print(f"  [NETWORK] All {len(agents)} agents playing {games_per_agent} games each")
            
            async with GameplayEngine(api_key, db_path=self.db.db_path) as engine:
                
                # Store engine reference for shutdown handler access
                self._current_engine = engine
                
                # If shutdown was requested before entering this context, set flag immediately
                if self.shutdown_requested:
                    engine.session_manager.is_shutting_down = True
                    print("[PAUSE]  Shutdown requested before generation started, exiting")
                    return {'games_played': 0, 'wins': 0, 'win_rate': 0.0, 'avg_score': 0.0}
                
                # Get available games
                available_games = await engine.session_manager.get_available_games()
                
                if not available_games:
                    print("[?] No games available from API")
                    return {'games_played': 0, 'wins': 0, 'win_rate': 0.0, 'avg_score': 0.0}
                
                # FOCUSED GAME MASTERY: Filter to target game if specified
                if self.target_game:
                    original_count = len(available_games)
                    available_games = [
                        g for g in available_games 
                        if (g.get('id', g.get('game_id', '')) or '').startswith(self.target_game)
                    ]
                    if not available_games:
                        print(f"[!] No games matching '{self.target_game}' found (had {original_count} games)")
                        return {'games_played': 0, 'wins': 0, 'win_rate': 0.0, 'avg_score': 0.0}
                    print(f"[TARGET] Focused on {len(available_games)} game(s) matching '{self.target_game}'")
                
                # ADAPTIVE SCALING: Extract unique game types from available games
                # Dynamically determine game types instead of hardcoding
                game_ids = [g.get('id', g.get('game_id')) for g in available_games if g.get('id') or g.get('game_id')]
                game_type_prefixes = set()
                for game_id in game_ids:
                    if game_id and len(game_id) >= 4:
                        game_type_prefixes.add(game_id[:4])
                
                game_types = sorted(list(game_type_prefixes))  # Sort for consistency
                
                # DYNAMIC PERFORMANCE-BASED POPULATION (Option C)
                # Formula: Base 60 + 5 per unbeaten game, capped at 150
                # This scales with difficulty while keeping generation time ~1 hour
                BASE_POPULATION = 60
                BONUS_PER_UNBEATEN = 5
                MAX_POPULATION = 150
                
                # Count unbeaten game types (no full game win sequence)
                try:
                    beaten_types = set()
                    beaten_result = self.db.execute_query("""
                        SELECT DISTINCT SUBSTR(game_id, 1, 4) as game_type
                        FROM winning_sequences_full_game
                        WHERE is_active = 1
                    """)
                    if beaten_result:
                        beaten_types = {r['game_type'] for r in beaten_result if r.get('game_type')}
                    
                    unbeaten_types = [gt for gt in game_types if gt not in beaten_types]
                    unbeaten_count = len(unbeaten_types)
                except Exception:
                    unbeaten_count = len(game_types)  # Assume all unbeaten if query fails
                
                ADAPTIVE_TARGET_POPULATION = min(
                    BASE_POPULATION + (unbeaten_count * BONUS_PER_UNBEATEN),
                    MAX_POPULATION
                )
                print(f"  [POP] {len(game_types)} game types, {unbeaten_count} unbeaten → Target: {ADAPTIVE_TARGET_POPULATION} agents (base {BASE_POPULATION} + {unbeaten_count}*{BONUS_PER_UNBEATEN}, max {MAX_POPULATION})")
                
                # Store for pruning logic later
                self._current_target_population = ADAPTIVE_TARGET_POPULATION
                self._current_game_types = game_types  # Store game types for specialist protection
                
                # SPECIALIST MODE: Auto-assign games if not already assigned (for resumed checkpoints)
                if self.specialist_mode and self.specialist_coordinator:
                    # Check if assignments exist
                    first_agent = selected_agents[0] if selected_agents else None
                    if first_agent:
                        assignments = self.specialist_coordinator.get_games_for_specialist(first_agent['agent_id'])
                        if not assignments:
                            print(f"\n[>] Auto-assigning specialists (resuming from checkpoint)...")
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
                
                # NEW: Use GameScheduler to prevent duplicate game plays
                # This prevents the inefficiency where multiple agents play same game type sequentially
                print("\n GAME SCHEDULER: Assigning games to prevent duplicate plays...")
                
                # Prepare agents for scheduler (need mode from mode_assignments)
                agents_with_modes = []
                for agent in selected_agents:
                    agent_id = agent['agent_id']
                    agent_mode = mode_assignments.get(agent_id, 'generalist')
                    agents_with_modes.append({
                        'agent_id': agent_id,
                        'mode': agent_mode,
                        'generation': self.current_generation
                    })
                
                # Assign games using scheduler (prevents duplicate game types)
                game_assignments = self.game_scheduler.assign_games_to_agents(
                    agents=agents_with_modes,
                    total_games_to_play=num_games,
                    available_game_ids=game_ids,
                    ensure_game_type_coverage=self.ensure_game_type_coverage
                )
                
                if not game_assignments:
                    print("[?] No games could be assigned (all games may be in use)")
                    return {'games_played': 0, 'wins': 0, 'win_rate': 0.0, 'avg_score': 0.0}
                
                print(f" Assigned {sum(len(g) for g in game_assignments.values())} games to {len(game_assignments)} agents\n")
                
                # ================================================================
                # ERROR DETECTION: Stop evolution early if API is broken
                # ================================================================
                # Track consecutive failures to detect system-wide issues
                # This prevents wasting compute when API is down or games aren't working
                # 
                # IMPORTANT: Only count TRUE errors, not normal game endings:
                # - GAME_OVER with score 0 = hard game (not an error)
                # - NO_SEQUENCE_AVAILABLE = pioneer on frontier (not an error)
                # - ERROR, API_ERROR, TIMEOUT = true errors
                # ================================================================
                consecutive_zero_score_games = 0  # Games with 0 score
                consecutive_error_games = 0  # Games that threw TRUE errors
                ZERO_SCORE_THRESHOLD = 20  # Warn after 20 consecutive zero-score games (don't stop)
                ERROR_THRESHOLD = 15  # Stop after 15 consecutive TRUE errors (was 5, too aggressive)
                total_zero_score_games = 0  # Track total for reporting
                total_error_games = 0
                
                # Define what counts as a TRUE error vs normal game ending
                TRUE_ERROR_STATES = {'ERROR', 'API_ERROR', 'TIMEOUT', 'CONNECTION_ERROR'}
                NORMAL_END_STATES = {'GAME_OVER', 'WIN', 'NO_SEQUENCE_AVAILABLE', 'NOT_FINISHED'}
                
                for agent_idx, agent in enumerate(selected_agents):  # FIXED: Use selected_agents
                    agent_id = agent['agent_id']
                    
                    # Get games assigned by scheduler
                    agent_games = game_assignments.get(agent_id, [])
                    
                    if not agent_games:
                        # Agent didn't get any games (all games in use or not selected)
                        continue
                    
                    # Get agent's operating mode (pioneer/optimizer/generalist)
                    agent_mode = mode_assignments.get(agent_id, 'generalist')
                    
                    # Log assignment
                    game_types_assigned = list(set(g[:4] for g in agent_games))
                    print(f"  [SCHEDULED] {agent_mode.upper()} {agent_id[:8]} → {', '.join(game_types_assigned)} ({len(agent_games)} games)")
                    
                    # Check for shutdown before starting this agent's games
                    if self.shutdown_requested:
                        print(f"[PAUSE]  Shutdown requested, skipping agent {agent_id[:8]} and remaining agents")
                        break
                    
                    # Run games for this agent
                    for game_idx, game_id in enumerate(agent_games):
                        if self.shutdown_requested:
                            print("[PAUSE]  Shutdown requested during game, stopping evaluation")
                            break
                        
                        # PERSISTENT MODE MEMORY: Assign mode for this specific game
                        # Agent remembers which mode (pioneer/optimizer/generalist) works best per game
                        agent_mode = mode_system.get_best_mode_for_game(agent_id, game_id)
                        if not agent_mode:
                            # No history - use population assignment
                            agent_mode = mode_assignments.get(agent_id, 'generalist')
                            mode_system._record_mode_assignment(
                                agent_id, game_id, self.current_generation, 
                                agent_mode, "First attempt - using population role"
                            )
                        
                        # === NEW: Collective reasoning for difficult games ===
                        # Trigger ensemble intelligence when game attempted 3+ times without win
                        if self.collective_reasoner:
                            try:
                                # Check game difficulty (attempts without win)
                                attempts = self.db.execute_query("""
                                    SELECT COUNT(*) as attempt_count
                                    FROM agent_arc_performance
                                    WHERE game_id = ? AND win_achieved = FALSE
                                """, (game_id,))
                                
                                if attempts and attempts[0]['attempt_count'] >= 3:
                                    # Start collective session (auto-selects top agents)
                                    session_id = self.collective_reasoner.start_collective_session(
                                        game_id=game_id,
                                        generation=self.current_generation,
                                        reasoning_mode='consensus'  # Use consensus for difficult games
                                    )
                                    if session_id:
                                        print(f"  [ENSEMBLE] Collective reasoning session started for difficult game")
                            except Exception as e:
                                print(f"  [WARN] Collective reasoning setup failed: {e}")
                        
                        # Determine target level for optimizers
                        optimizer_target_level = None
                        if agent_mode == 'optimizer':
                            # Get optimization targets for this game
                            all_targets = self.optimization_tracker.get_optimization_targets(
                                agent_mode='optimizer',
                                limit=100
                            )
                            # Filter to this game
                            game_targets = [t for t in all_targets if t['game_id'] == game_id]
                            if game_targets:
                                optimizer_target_level = game_targets[0]['level_number']
                        
                        # Use BREAKTHROUGH BUDGET ALLOCATOR (Tier 1: +50% gain)
                        # Dynamic per-game budgets: 800 (unbeaten), 400 (partial), 150 (beaten)
                        game_budget_dict = self.budget_allocator.calculate_game_budget(game_id)
                        game_budget = game_budget_dict['action_allowance_total']
                        actions_per_level = game_budget_dict['action_allowance_per_level']
                        print(f"[BUDGET] Game {game_id[:8]}: {game_budget} total actions allocated")
                        
                        # Use adaptive action limits (adjusted per generation)
                        # Configure engine with current adaptive limits
                        engine.configure(
                            strategy='balanced',
                            max_actions_per_level=actions_per_level,  # Adaptive: adjusts based on performance
                            max_total_actions=game_budget,  # BREAKTHROUGH: Dynamic per-game budget
                            enable_random_exploration=True,
                            enable_pattern_learning=True,
                            # Diversity Mode settings (Rule 10: enhance existing)
                            diversity_mode=self.agi_mode,  # CHANGED: use diversity_mode instead of agi_mode
                            enforce_game_diversity=self.agi_mode,
                            max_repeats_per_game=5 if self.agi_mode else 999,
                            # Specialist Mode settings (NEW)
                            specialist_mode=self.specialist_mode,
                            # Agent role settings (NEW)
                            agent_operating_mode=agent_mode,
                            optimizer_target_level=optimizer_target_level,
                            # Generation tracking for scorecard tags
                            current_generation=self.current_generation
                        )
                        
                        # Play game - REAL ARC API CALL
                        # Wrap in cancellable task for graceful shutdown
                        try:
                            game_task = asyncio.create_task(engine.play_single_game(game_id, agent_id=agent_id))
                            result = await game_task
                        except asyncio.CancelledError:
                            # Game was cancelled during shutdown
                            print(f"[PAUSE]  Game {game_id[:8]} cancelled")
                            if self.shutdown_requested:
                                # Propagate shutdown to session manager to prevent new actions
                                engine.session_manager.is_shutting_down = True
                                break
                            raise
                        
                        # Check for shutdown after game completes
                        if self.shutdown_requested:
                            # Propagate shutdown signal to prevent any new games
                            engine.session_manager.is_shutting_down = True
                            print(f"[PAUSE]  Shutdown detected after game {game_id[:8]}, ending generation early")
                            break
                        
                        # ================================================================
                        # ERROR DETECTION: Track game failures
                        # ================================================================
                        # Only count TRUE errors (API failures, timeouts, etc.)
                        # NOT normal game endings like GAME_OVER or NO_SEQUENCE_AVAILABLE
                        # ================================================================
                        game_score = result.get('final_score', 0)
                        final_state = result.get('final_state', 'UNKNOWN')
                        explicit_error = result.get('error')
                        
                        # Determine if this is a TRUE error vs normal game ending
                        is_true_error = (
                            explicit_error is not None or 
                            final_state in TRUE_ERROR_STATES
                        )
                        is_normal_zero = (
                            game_score == 0 and 
                            final_state in NORMAL_END_STATES
                        )
                        
                        if is_true_error:
                            # TRUE error - API failure, timeout, etc.
                            consecutive_error_games += 1
                            total_error_games += 1
                            consecutive_zero_score_games = 0  # Reset other counter
                            
                            # Check threshold
                            if consecutive_error_games >= ERROR_THRESHOLD:
                                print(f"\n[STOP] CRITICAL: {consecutive_error_games} consecutive TRUE errors detected!")
                                print(f"   Stopping evolution to prevent wasted compute.")
                                print(f"   Last error: {explicit_error or final_state}")
                                print(f"   Total errors this generation: {total_error_games}")
                                self.shutdown_requested = True
                                engine.session_manager.is_shutting_down = True
                                break
                        elif is_normal_zero:
                            # Normal game ending with 0 score (hard game or frontier pioneer)
                            consecutive_zero_score_games += 1
                            total_zero_score_games += 1
                            consecutive_error_games = 0  # Reset - this isn't an error
                            
                            # Only warn, never stop for zero scores - could be hard games
                            if consecutive_zero_score_games >= ZERO_SCORE_THRESHOLD:
                                print(f"\n[WARN] {consecutive_zero_score_games} consecutive zero-score games")
                                print(f"   This may indicate hard games or exploration on frontier.")
                                print(f"   Total zero-score games: {total_zero_score_games}")
                                consecutive_zero_score_games = 0  # Reset to give more chances
                        else:
                            # Game succeeded with score > 0
                            consecutive_zero_score_games = 0
                            consecutive_error_games = 0
                        
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
                        
                        # === NEW BREAKTHROUGH SYSTEMS: Post-game analysis ===
                        
                        # 1. Update frustration state (detect stuck agents)
                        if self.frustration_detector:
                            try:
                                # Get agent's previous best score on this game
                                prev_best = self.db.execute_query("""
                                    SELECT MAX(final_score) as best_score
                                    FROM agent_arc_performance
                                    WHERE agent_id = ? AND game_id = ?
                                """, (agent_id, game_id))
                                previous_best_score = prev_best[0]['best_score'] if prev_best and prev_best[0]['best_score'] else 0.0
                                
                                self.frustration_detector.update_agent_frustration(
                                    agent_id=agent_id,
                                    game_id=game_id,
                                    score_achieved=result.get('final_score', 0),
                                    previous_best_score=previous_best_score,
                                    actions_taken=result.get('actions_taken', 0),
                                    generation=self.current_generation
                                )
                                
                                # Check if network-wide frustration threshold reached
                                quorum_reached = self.frustration_detector.check_frustration_quorum(
                                    generation=self.current_generation
                                )
                                if quorum_reached:
                                    print(f"  [!] Frustration quorum reached - desperation signals emitted")
                            except Exception as e:
                                print(f"  [WARN] Frustration detection failed: {e}")
                        
                        # 2. Analyze near-misses (high score failures)
                        final_score = result.get('final_score', 0)
                        if self.near_miss_analyzer and final_score >= 15 and not result.get('win', False):
                            try:
                                session_id = engine.session_manager.current_session_id or "unknown"
                                insights_id = self.near_miss_analyzer.analyze_near_miss(
                                    agent_id=agent_id,
                                    game_id=game_id,
                                    session_id=session_id,
                                    final_score=final_score,
                                    total_actions=result.get('actions_taken', 0),
                                    generation=self.current_generation
                                )
                                if insights_id:
                                    print(f"  [>] Near-miss analysis recorded (ID: {insights_id[:8]})")
                                    
                                    # CODS: Process near-miss patterns for primitive gap detection
                                    if hasattr(engine, 'cods_engine') and engine.cods_engine:
                                        try:
                                            engine.cods_engine.process_near_miss_patterns(insights_id)
                                        except Exception as cods_e:
                                            pass  # Non-critical
                            except Exception as e:
                                print(f"  [WARN] Near-miss analysis failed: {e}")
                        
                        # 3. Counterfactual analysis on failures (learn from mistakes)
                        if self.counterfactual_analyzer and not result.get('win', False) and final_score < 15:
                            try:
                                session_id = engine.session_manager.current_session_id or "unknown"
                                learning_ids = self.counterfactual_analyzer.analyze_failure(
                                    agent_id=agent_id,
                                    game_id=game_id,
                                    session_id=session_id,
                                    final_score=final_score,
                                    generation=self.current_generation
                                )
                                if learning_ids:
                                    print(f"  [?] Counterfactual: {len(learning_ids)} alternative strategies identified")
                                    
                                    # CODS: Process counterfactual insights for primitive gap detection
                                    if hasattr(engine, 'cods_engine') and engine.cods_engine:
                                        try:
                                            engine.cods_engine.process_counterfactual_insights(learning_ids)
                                        except Exception as cods_e:
                                            pass  # Non-critical
                            except Exception as e:
                                print(f"  [WARN] Counterfactual analysis failed: {e}")
                        
                        # 4. CODS: Record game outcome for failure-driven learning
                        if hasattr(engine, 'cods_engine') and engine.cods_engine:
                            try:
                                cods_result = engine.cods_engine.record_game_outcome(
                                    game_id=game_id,
                                    final_score=final_score,
                                    max_level_reached=result.get('levels_completed', 0) + 1,
                                    total_actions=result.get('actions_taken', 0),
                                    won=result.get('win', False)
                                )
                                if cods_result.get('primitive_gaps'):
                                    print(f"  [CODS] Detected {len(cods_result['primitive_gaps'])} primitive gaps")
                            except Exception as e:
                                pass  # Non-critical
                        
                        # PERSISTENT MODE MEMORY: Record mode effectiveness for this game
                        mode_system.update_mode_effectiveness(
                            agent_id=agent_id,
                            generation=self.current_generation,
                            score=result.get('final_score', 0),
                            win=result.get('win', False),
                            actions=result.get('actions_taken', 0)
                        )
                        
                        # PHASE 3: Track viral package usage and effectiveness
                        try:
                            from viral_package_engine import ViralPackageEngine
                            viral_engine = ViralPackageEngine(self.db)
                            
                            # Get packages this agent carries
                            infections = self.db.execute_query("""
                                SELECT package_id 
                                FROM agent_viral_infections 
                                WHERE agent_id = ? AND is_active = TRUE
                            """, (agent_id,))
                            
                            # Record usage for each package
                            success = result.get('win', False) or result.get('final_score', 0) > 0
                            score_change = result.get('final_score', 0)
                            current_gen = self.db.execute_query(
                                "SELECT generation FROM agents WHERE agent_id = ?", 
                                (agent_id,)
                            )
                            generation = current_gen[0]['generation'] if current_gen else self.current_generation
                            
                            for infection in infections:
                                viral_engine.record_package_usage(
                                    agent_id=agent_id,
                                    package_id=infection['package_id'],
                                    success=success,
                                    score_change=score_change,
                                    generation=generation
                                )
                        except Exception as e:
                            # Non-critical - don't break evolution if Phase 3 fails
                            pass
                        
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
                                    print(f"  [WARN]  Failed to extract rule: {e}")
                        
                        total_score += result.get('final_score', 0)
                        
                        results.append({
                            'agent_id': agent_id,
                            'game_id': game_id,
                            'result': result,
                            'reward': reward_data
                        })
                        
                        # NEW: Release game so another agent can use it
                        self.game_scheduler.release_game(game_id, agent_id=agent_id)
                        
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
                        print(f"  [WARN]  Failed to update curriculum: {e}")
                
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
                
                # Clear engine reference on normal exit
                self._current_engine = None
                
                return summary
            
        except asyncio.CancelledError:
            # Task was cancelled during shutdown - this is expected
            self._current_engine = None  # Clear reference
            print("[PAUSE]  Evaluation cancelled during shutdown")
            raise  # Re-raise to propagate cancellation
            
        except Exception as e:
            if self.shutdown_requested:
                # Errors during shutdown are expected, just log briefly
                print(f"[WARN]  Error during shutdown evaluation (ignored): {type(e).__name__}")
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
                print(f"[WARN]  Reached max generations ({self.max_generations})")
                return False
            
            # Evolve new generation using EvolutionaryEngine
            print(f"\n[DNA] Evolving Generation {self.current_generation + 1}...")
            
            # Check for prestige vampires before breeding
            try:
                vampires_sunset = check_for_vampires(self.current_generation, self.db.db_path)
                if vampires_sunset > 0:
                    print(f"  [VAMPIRE] Sunset {vampires_sunset} prestige vampires before breeding")
            except Exception as e:
                print(f"  [WARN] Vampire detection failed (non-critical): {e}")
            
            evolution_engine = EvolutionaryEngine(self.db)
            
            # Get top performers for breeding
            top_performers = analysis.get('top_performers', [])[:5]
            
            if not top_performers:
                print("[WARN]  No agents with performance data, cannot evolve")
                return False
            
            # Determine evolution strategy based on comprehensive success
            if avg_success_rate < 0.1:
                strategy_focus = 'exploration'
            elif avg_success_rate < 0.3:
                strategy_focus = 'diversification'
            else:
                strategy_focus = 'exploitation'
            
            print(f"  Strategy: {strategy_focus} (based on {avg_success_rate:.1%} success rate)")
            
            # ADAPTIVE OFFSPRING: Scale with target population
            # Create enough offspring to maintain target population
            TARGET_POPULATION = getattr(self, '_current_target_population', None)
            if TARGET_POPULATION is None:
                TARGET_POPULATION = self._calculate_target_population_from_db()
            adaptive_offspring_size = max(5, TARGET_POPULATION // 10)  # At least 5, scales with target
            
            print(f"  Adaptive offspring: {adaptive_offspring_size} (based on target population {TARGET_POPULATION})")
            
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
                'offspring_size': adaptive_offspring_size  # ADAPTIVE: was hardcoded to 5
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
                print(f"[WARN]  Evolution failed: {e}")
                print(f"  Falling back to previous generation")
                return False
            
            self.current_generation += 1
            self.last_evolution_time = datetime.now()
            
            print(f"[OK] Evolution complete - Created {new_agents_created} new agents")
            
            # DISK SPACE CHECK: Monitor disk space before continuing
            print(f"\n[DISK SPACE] Checking disk space...")
            try:
                safe, message, stats = self.disk_monitor.check_disk_space()
                if not safe:
                    print(f"[CRITICAL] {message}")
                    print(f"[CRITICAL] STOPPING EVOLUTION: Disk space critical!")
                    print(f"[CRITICAL] Run historical_data_cleanup.py or safe_cleanup.py")
                    return False  # Stop evolution
                else:
                    print(f"[OK] {message}")
            except Exception as e:
                print(f"[WARN] Disk space check failed: {e}")
            
            # SEQUENCE PRUNING: Remove bad sequences after each generation
            print(f"\n[SEQUENCE PRUNING] Cleaning up failed sequences for generation {self.current_generation}...")
            try:
                pruning_results = self.sequence_pruner.prune_bad_sequences(
                    self.current_generation,
                    dry_run=False
                )
                
                if pruning_results['total_pruned'] > 0:
                    print(f"[OK] Pruned {pruning_results['total_pruned']} bad sequences:")
                    print(f"  - Excessive actions (>10K): {pruning_results['excessive_actions']}")
                    print(f"  - Low success rate (<10%): {pruning_results['low_success_rate']}")
                    print(f"  - Low score (<2 pts): {pruning_results['low_score']}")
                    print(f"  - Kept: {pruning_results['total_kept']} good sequences")
                else:
                    print(f"[OK] No sequences needed pruning - {pruning_results['total_kept']} sequences active")
                    
            except Exception as e:
                print(f"[WARN] Sequence pruning failed: {e}")
                import traceback
                traceback.print_exc()
            
            # OPTIMIZATION TRACKING: Update which levels are optimized vs need work
            print(f"\n[OPTIMIZATION] Updating level optimization status for generation {self.current_generation}...")
            try:
                opt_summary = self.optimization_tracker.update_optimization_status(self.current_generation)
                
                if opt_summary['newly_optimized'] > 0:
                    print(f"[OK] {opt_summary['newly_optimized']} levels newly optimized!")
                
                print(f"[OK] Optimization status: {opt_summary['optimized']} optimized, "
                      f"{opt_summary['still_optimizing']} still need work")
                print(f"     → Optimizers will use best sequences for optimized levels")
                print(f"     → Optimizers will focus on unoptimized/unbeaten levels")
                
            except Exception as e:
                print(f"[WARN] Optimization tracking failed: {e}")
                import traceback
                traceback.print_exc()
            
            # PHASE 0: CAPTURE NETWORK INTELLIGENCE SNAPSHOT
            print(f"\n[NETWORK] Capturing ecosystem snapshot for generation {self.current_generation}...")
            try:
                snapshot = self.network_intelligence.capture_ecosystem_snapshot(self.current_generation)
                print(f"[OK] Network snapshot captured: {snapshot['health_status']} (score: {snapshot['health_score']:.3f})")
                
                # Display network intelligence dashboard
                print()
                display_network_intelligence_dashboard(self.current_generation)
                
            except Exception as e:
                print(f"[WARN]  Network snapshot failed: {e}")
                import traceback
                traceback.print_exc()
            
            # PHASE 0.5: AUTOPOIESIS HEALTH CHECK (system self-regulation)
            print(f"\n[AUTOPOIESIS] Checking system health for generation {self.current_generation}...")
            try:
                if AUTOPOIESIS_AVAILABLE and AutopoiesisMonitor:
                    autopoiesis = AutopoiesisMonitor(self.db)
                    health = autopoiesis.get_system_health(self.current_generation)
                    
                    print(f"[OK] System Health: {health['status']} (score: {health['overall_health']:.2f})")
                    print(f"     Emergence Gain: {health['emergence_gain']:.2f} "
                          f"({'network > individuals' if health['emergence_gain'] > 1.0 else 'needs improvement'})")
                    print(f"     Identity Drift: {health['identity_drift']:.2f} "
                          f"({'aligned' if health['identity_drift'] < 0.3 else 'drifting from goals'})")
                    print(f"     Control Error: {health['control_error']:.2f} "
                          f"({'calibrated' if abs(health['control_error']) < 0.2 else 'needs tuning'})")
                    print(f"     Loop Detection: {health['loop_detection_score']:.2f} "
                          f"({'no loops' if health['loop_detection_score'] < 0.3 else 'oscillation detected'})")
                    
                    # Display warnings if any
                    if health.get('warnings'):
                        for warning in health['warnings']:
                            print(f"[WARN] {warning}")
                else:
                    print(f"[INFO] Autopoiesis monitor not available")
                    
            except Exception as e:
                print(f"[WARN] Autopoiesis health check failed: {e}")
                import traceback
                traceback.print_exc()
            
            # PHASE 1: UPDATE PRESTIGE & STATUS BENEFITS
            print(f"\n[PRESTIGE] Calculating network contribution prestige for generation {self.current_generation}...")
            try:
                benefits_map = self.prestige_engine.update_all_agent_prestige(self.current_generation)
                print(f"[OK] Updated prestige for {len(benefits_map)} agents")
                
                # Display top 5 prestige leaders
                print()
                display_prestige_leaderboard(self.db, limit=5)
                
            except Exception as e:
                print(f"[WARN]  Prestige calculation failed: {e}")
                import traceback
                traceback.print_exc()
            
            # PHASE 3: VIRAL ECOSYSTEM STATUS
            print(f"\n[VIRAL] Checking viral packages & pariahs...")
            try:
                # Check for obsolete packages/pariahs
                self.viral_engine.check_package_obsolescence(self.current_generation, threshold_generations=20)
                self.viral_engine.check_pariah_obsolescence(self.current_generation, threshold_generations=30)
                
                # Display viral ecosystem dashboard
                print()
                display_viral_ecosystem_dashboard(self.db, self.current_generation)
                
            except Exception as e:
                print(f"[WARN]  Viral ecosystem check failed: {e}")
                import traceback
                traceback.print_exc()
            
            # PHASE 4: DISTRIBUTED REGULATION (Network Homeostasis)
            print(f"\n[ REGULATION] Processing distributed network signals...")
            try:
                # Step 1: Agent signal emission (quorum sensing)
                signals_emitted = self.regulatory_engine.emit_agent_signals(self.current_generation)
                print(f"[OK] {len(signals_emitted)} regulatory signals emitted")
                
                # Step 2: Process signal responses and calculate net adjustments
                net_adjustments = self.regulatory_engine.process_signal_responses(self.current_generation)
                print(f"[OK] Processed signal responses, {len(net_adjustments)} parameter adjustments calculated")
                
                # Step 3: Apply network regulation (emergent homeostasis)
                if net_adjustments:
                    applied_changes = self.regulatory_engine.apply_network_regulation(self.current_generation, net_adjustments)
                    
                    if applied_changes:
                        print(f"[HOMEOSTASIS] Applied {len(applied_changes)} parameter adjustments:")
                        for param, (old_val, new_val) in applied_changes.items():
                            direction = "↑" if new_val > old_val else "↓"
                            change_pct = ((new_val - old_val) / old_val) * 100 if old_val != 0 else 0
                            print(f"  {direction} {param}: {old_val:.4f} → {new_val:.4f} ({change_pct:+.1f}%)")
                    else:
                        print("[INFO] No significant parameter changes needed")
                else:
                    print("[INFO] No regulatory signals strong enough for parameter adjustments")
                
                # Step 4: Cleanup expired signals
                self.regulatory_engine.cleanup_expired_signals(self.current_generation)
                
                # Step 5: Display regulation summary
                regulation_summary = self.regulatory_engine.get_regulation_summary(self.current_generation)
                active_signals = regulation_summary.get('active_signals', {})
                recent_regulations = regulation_summary.get('recent_regulations', {})
                
                if active_signals:
                    print(f"[SIGNALS] Active regulatory signals:")
                    for signal_type, data in active_signals.items():
                        print(f"   {signal_type}: {data['count']} signals (avg strength: {data['strength']:.2f})")
                
                if recent_regulations:
                    print(f"[HISTORY] Recent parameter adjustments:")
                    for param, data in recent_regulations.items():
                        print(f"    {param}: {data['changes']} changes (avg: {data['avg_change']:+.3f})")
                
            except Exception as e:
                print(f"[WARN]  Distributed regulation failed: {e}")
                import traceback
                traceback.print_exc()
            
            # ISSUE 3 FIX: Aggressive pruning to maintain target population
            # ADAPTIVE: Scale target with available game count (game_types * 10)
            TARGET_POPULATION = getattr(self, '_current_target_population', None)
            if TARGET_POPULATION is None:
                TARGET_POPULATION = self._calculate_target_population_from_db()
            
            if population_size > TARGET_POPULATION:
                print(f"\n[] Population too large ({population_size}), pruning to {TARGET_POPULATION}...")
                print(f"      (Adaptive target based on {TARGET_POPULATION // 10} available game types)")
                
                # STEP 1: PRESTIGE-BASED PROTECTION ONLY (specialist system disabled)
                # Get survival_protection for all agents (0-80% protection based on prestige)
                agents_with_prestige = self.db.execute_query("""
                    SELECT agent_id, survival_protection
                    FROM agents
                    WHERE is_active = TRUE
                """)
                
                # Build protection map: agent_id -> survival_protection (0.0 to 0.8)
                protection_map = {
                    agent['agent_id']: agent.get('survival_protection', 0.0) or 0.0
                    for agent in agents_with_prestige
                }
                
                print(f"  [] Using prestige-based protection (0-80% survival chance)")
                
                # STEP 2: Identify top 10 performers for each game type (ABSOLUTE PROTECTION)
                # Get available game types from earlier in generation
                game_types = getattr(self, '_current_game_types', ['sp80', 'ls20', 'lp85', 'ft09', 'as66', 'vc33'])
                
                top_performers_by_game = set()
                for game_type in game_types:
                    # Get top 10 agents for this game type based on their performance
                    top_agents = self.db.execute_query("""
                        SELECT DISTINCT aap.agent_id, 
                               AVG(aap.final_score) as avg_score,
                               COUNT(*) as games_played
                        FROM agent_arc_performance aap
                        WHERE aap.game_id LIKE ?
                          AND aap.agent_id IN (SELECT agent_id FROM agents WHERE is_active = TRUE)
                        GROUP BY aap.agent_id
                        HAVING games_played >= 1
                        ORDER BY avg_score DESC, games_played DESC
                        LIMIT 10
                    """, (f"{game_type}-%",))
                    
                    for agent in top_agents:
                        top_performers_by_game.add(agent['agent_id'])
                
                print(f"  [] Protected top 10 performers per game type: {len(top_performers_by_game)} specialists")
                
                # CRITICAL FIX: Get ALL agents sorted by performance (worst first)
                # Don't use top_performers list which is limited to top 5!
                all_agents_sorted = self.db.execute_query("""
                    SELECT agent_id, avg_score_per_game, total_games_won, score_efficiency
                    FROM agents
                    WHERE is_active = TRUE
                    ORDER BY avg_score_per_game ASC, total_games_won ASC, score_efficiency ASC
                """)
                
                pruned_count = 0
                protected_by_prestige = 0
                protected_by_specialist = 0
                target_pruned = population_size - TARGET_POPULATION  # Prune down to target
                
                # ADAPTIVE PRESTIGE DAMPENING
                # Scale down prestige protection when population is way over target
                overpopulation_ratio = population_size / TARGET_POPULATION
                if overpopulation_ratio > 10:
                    # Severe overpopulation: reduce prestige to 10% effectiveness
                    prestige_dampening = 0.1
                elif overpopulation_ratio > 5:
                    # Heavy overpopulation: reduce prestige to 30% effectiveness
                    prestige_dampening = 0.3
                elif overpopulation_ratio > 2:
                    # Moderate overpopulation: reduce prestige to 60% effectiveness
                    prestige_dampening = 0.6
                else:
                    # Normal or slight overpopulation: full prestige effectiveness
                    prestige_dampening = 1.0
                
                print(f"  [TARGET] Attempting to prune {target_pruned} worst performers from {len(all_agents_sorted)} active agents...")
                print(f"  [DAMPEN] Population ratio: {overpopulation_ratio:.1f}x target, prestige dampening: {prestige_dampening:.0%}")
                
                import random
                for agent in all_agents_sorted:
                    agent_id = agent['agent_id']
                    
                    # ABSOLUTE PROTECTION: Top 10 performers per game type
                    if agent_id in top_performers_by_game:
                        protected_by_specialist += 1
                        continue
                    
                    # Check prestige protection (probabilistic with adaptive dampening)
                    base_protection = protection_map.get(agent_id, 0.0)
                    effective_protection = base_protection * prestige_dampening
                    if random.random() < effective_protection:
                        # Agent protected by prestige - skip pruning
                        protected_by_prestige += 1
                        continue
                    
                    # Deactivate agent (not deleted - just marked inactive)
                    # Agent data preserved in database for analysis
                    self.db.execute_query(
                        "UPDATE agents SET is_active = 0 WHERE agent_id = ?",
                        (agent_id,)
                    )
                    pruned_count += 1
                    
                    # Stop after reaching target
                    if pruned_count >= target_pruned:
                        break
                
                if pruned_count == 0:
                    print(f"  [WARN] No agents pruned - all protected!")
                    print(f"        Protected by specialist status: {protected_by_specialist} agents")
                    print(f"        Protected by prestige: {protected_by_prestige} agents")
                    print(f"        Consider adjusting protection thresholds")
                else:
                    print(f"  [OK] Pruned {pruned_count} agents (target: {target_pruned})")
                    print(f"       Protected specialists (top 10/game): {protected_by_specialist} agents")
                    print(f"       Protected by prestige: {protected_by_prestige} agents")
                    print(f"       New population size: {population_size - pruned_count}")
            
            # CLEANUP: Historical data garbage collection (prevent database bloat)
            print(f"\n[CLEANUP] Running historical data garbage collection...")
            
            # Agent lifecycle management (Net Navi philosophy: good players live on)
            try:
                from agent_lifecycle_manager import AgentLifecycleManager
                lifecycle_mgr = AgentLifecycleManager(self.db)
                
                # Only run cleanup every 10 generations (not every generation)
                if self.current_generation % 10 == 0:
                    print(f"\n[DNA AGENTS] Cleaning up ancient inactive agents...")
                    agent_cleanup = lifecycle_mgr.cleanup_ancient_inactive_agents(self.current_generation, dry_run=False)
                    
                    if agent_cleanup['total_deleted'] > 0:
                        print(f"  [OK] Permanently deleted {agent_cleanup['total_deleted']} ancient agents")
                        print(f"       Zero-score (50+ gen): {agent_cleanup['zero_score_deleted']}")
                        print(f"       Low-score (200+ gen): {agent_cleanup['low_score_deleted']}")
                        print(f"       Good players (500+ gen): {agent_cleanup['good_player_deleted']}")
                        print(f"       High prestige preserved: {agent_cleanup['high_prestige_archived']}")
                    else:
                        print(f"  [INFO] No agents old enough for deletion")
                else:
                    print(f"  [SKIP] Agent cleanup (only runs every 10 generations)")
                    
            except NameError as ne:
                # NameError typically means a variable/module is not defined
                print(f"  [WARN] Agent lifecycle cleanup NameError: {ne}")
                import traceback
                traceback.print_exc()
            except Exception as e:
                print(f"  [WARN] Agent lifecycle cleanup failed: {type(e).__name__}: {e}")
            
            # Phase 1: Agent Revival System (Biome Theory)
            # Check if any agents should be revived based on triggers
            if self.current_generation % 5 == 0:  # Check every 5 generations
                try:
                    from revive_agents import AgentRevivalSystem
                    revival_system = AgentRevivalSystem()
                    
                    triggers = revival_system.detect_revival_triggers(self.current_generation)
                    revived_count = 0
                    
                    for trigger in triggers:
                        if trigger.get('candidates'):
                            # Try to revive the best candidate
                            candidate = trigger['candidates'][0]
                            revived = revival_system.revive_agent(
                                candidate if isinstance(candidate, dict) else {'agent_id': candidate},
                                revival_mode='hybrid',  # Option B from Master Ruleset
                                generation=self.current_generation
                            )
                            if revived:
                                revived_count += 1
                                print(f"  [REVIVAL] Revived agent due to {trigger['trigger']}: {revived[:12]}")
                    
                    if revived_count > 0:
                        print(f"  [OK] Revival system resurrected {revived_count} agents")
                    else:
                        print(f"  [SKIP] No revival triggers detected")
                        
                except ImportError:
                    print(f"  [SKIP] Revival system not available (revive_agents.py not found)")
                except Exception as e:
                    print(f"  [WARN] Revival system failed: {e}")
            
            # Frontier package cleanup (remove temp packages when sequences exist)
            try:
                from viral_package_engine import ViralPackageEngine
                viral_engine = ViralPackageEngine(self.db)
                cleaned = viral_engine.cleanup_obsolete_frontier_packages(min_sequences_to_cleanup=3)
                if cleaned > 0:
                    print(f"  [OK] Cleaned {cleaned} obsolete frontier packages (sequences now exist)")
                
                # Also cleanup obsolete pariahs (soft retirement)
                pariah_retired = viral_engine.cleanup_obsolete_pariahs(self.current_generation)
                if pariah_retired > 0:
                    print(f"  [OK] Soft-retired {pariah_retired} obsolete pariahs")
            except Exception as e:
                print(f"  [WARN] Frontier package cleanup failed: {e}")
            
            # Safe database cleanup (comprehensive - replaces HistoricalDataCleaner)
            try:
                cleaner = SafeDatabaseCleaner()
                cleanup_results = cleaner.cleanup(dry_run=False, verbose=False)
                
                total_deleted = cleanup_results['total_deleted']
                if total_deleted > 0:
                    print(f"  [OK] Safe cleanup deleted {total_deleted:,} rows:")
                    for table, stats in cleanup_results['tables_cleaned'].items():
                        if stats.get('deleted', 0) > 0:
                            print(f"       - {table}: {stats['deleted']:,}")
                else:
                    print(f"  [SKIP] No cleanup needed (all tables within limits)")
                
            except Exception as e:
                print(f"  [WARN] Safe cleanup failed: {e}")
            
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
            print(f"\n[WARN]  System Health Issues:")
            for warning in health['warnings']:
                print(f"  - {warning}")
            
            if health['agent_count'] == 0:
                print("  Attempting to reinitialize population...")
                if not await self.initialize_population():
                    return False
        
        # Run evaluation games
        # ADAPTIVE: Use target population if available, otherwise use configured value
        adaptive_games = getattr(self, '_current_target_population', self.games_per_generation)
        print(f"  [ADAPTIVE] Running {adaptive_games} games (target population: {getattr(self, '_current_target_population', 'not set')})")
        eval_results = await self.run_evaluation_games(adaptive_games)
        
        # CRITICAL: Force WAL checkpoint after every generation to prevent data loss
        try:
            self.db.checkpoint_wal()
            print(f"[?] WAL checkpoint after generation {self.current_generation}")
        except Exception as e:
            print(f"[WARN] Failed to checkpoint WAL: {e}")
        
        # AUTOMATED ASSESSMENT: Run metrics tracking (Other AI #3)
        try:
            assessment = self.assessment_runner.run_post_generation_assessment(
                generation_number=self.current_generation,
                games_played=self.total_games_played,
                agents_active=health['agent_count']
            )
            print(f"[ASSESSMENT] Completion: {assessment['level_completion']['completion_rate']:.1f}%, "
                  f"Breakthroughs: {assessment['breakthrough_momentum']['breakthrough_detections']}, "
                  f"Status: {assessment['level_completion']['status']}")
            
            # Print recommendations if any
            if assessment['recommendations']:
                print(f"[ASSESSMENT] Recommendations:")
                for rec in assessment['recommendations'][:3]:  # Show top 3
                    print(f"  - {rec}")
        except Exception as e:
            print(f"[WARN] Automated assessment failed: {e}")
        
        # CODS: Check for potential primitive unlocks (post-generation)
        if CODS_AVAILABLE and check_for_potential_unlocks:
            try:
                # Bootstrap operators if none exist (seed the system)
                from cods_engine import get_cods_engine
                cods_engine = get_cods_engine(self.db.db_path)
                bootstrap_count = cods_engine.bootstrap_operators_from_patterns(limit=10)
                if bootstrap_count > 0:
                    print(f"[CODS] Bootstrapped {bootstrap_count} initial operators")
                
                # Evolve existing operators
                evolved = cods_engine.evolve_operators(n_generations=1, population_size=10)
                if evolved:
                    print(f"[CODS] Evolved {len(evolved)} operator variants")
                
                # Now check for unlocks
                cods_results = check_for_potential_unlocks(
                    db_path=self.db.db_path,
                    min_success_rate=0.70,
                    min_cross_game_rate=0.50,
                    min_tests=5
                )
                if cods_results['unlock_attempts'] > 0:
                    print(f"[CODS] Checked {cods_results['operators_checked']} operators, "
                          f"{cods_results['unlock_attempts']} attempts, "
                          f"{cods_results['unlocks_approved']} unlocked, "
                          f"{cods_results['novel_discoveries']} novel")
                    
                    # Show details for any unlocks
                    for detail in cods_results.get('details', []):
                        if detail.get('verdict') == 'approved':
                            print(f"  [UNLOCK] {detail['matched_primitive']} unlocked via {detail['operator']}")
                        elif detail.get('verdict') == 'novel':
                            print(f"  [NOVEL] {detail['operator']} registered as novel discovery")
                
                # STRATEGY-DRIVEN UNLOCK: Process agent strategy signals
                # This is the "Teacher Model" - CODS listens to what agents say they need
                # and unlocks primitives when the network expresses a capability gap
                try:
                    cods_instance = CODSEngine() if CODSEngine else None
                    if cods_instance:
                        # ADAPTIVE: threshold = 10% of active agents (floor 15, cap 100)
                        strategy_results = cods_instance.process_agent_strategy_signals(
                            min_frequency=10,
                            unlock_threshold=None,  # Use adaptive
                            unlock_percentage=0.10  # 10% of network must express need
                        )
                        if strategy_results.get('needs_detected'):
                            top_needs = sorted(
                                strategy_results['needs_detected'].items(),
                                key=lambda x: x[1]['total_frequency'],
                                reverse=True
                            )[:3]
                            print(f"[CODS-TEACHER] Network needs: " + 
                                  ", ".join(f"{p}({d['total_frequency']}x)" for p, d in top_needs))
                        
                        if strategy_results.get('unlocks_triggered'):
                            for unlock in strategy_results['unlocks_triggered']:
                                print(f"  [NEED-UNLOCK] {unlock['primitive']} "
                                      f"(expressed {unlock['frequency']}x by network)")
                except Exception as e:
                    pass  # Silently skip on error (strategy unlock is supplemental)
                
                # STUCK POINT ANALYSIS (Gap #2): Identify primitive gaps from stuck patterns
                try:
                    cods_instance = CODSEngine() if CODSEngine else None
                    if cods_instance:
                        stuck_analysis = cods_instance.analyze_stuck_points_for_unlocks(
                            min_stuck_count=10,
                            min_confidence=0.5
                        )
                        if stuck_analysis.get('gaps_identified'):
                            print(f"[STUCK-ANALYSIS] Found {len(stuck_analysis['gaps_identified'])} "
                                  f"capability gaps from {stuck_analysis['hotspots_analyzed']} hotspots")
                            # Show top gaps
                            for gap in stuck_analysis['gaps_identified'][:3]:
                                prims = ', '.join(gap['suggested_primitives'][:3])
                                print(f"  [GAP] {gap['game_type']} L{gap['level']}: "
                                      f"{gap['stuck_count']} stuck -> needs [{prims}]")
                        if stuck_analysis.get('unlocks_triggered'):
                            for unlock in stuck_analysis['unlocks_triggered']:
                                print(f"  [STUCK-UNLOCK] {unlock['primitive']} "
                                      f"({unlock['stuck_count']} agents stuck)")
                except Exception as e:
                    pass  # Supplemental analysis
                
                # CONCEPT-DRIVEN UNLOCK (Gap #3): Check concepts for games with stuck points
                try:
                    cods_instance = CODSEngine() if CODSEngine else None
                    if cods_instance:
                        # Get game types with most stuck agents
                        stuck_games = self.db.execute_query("""
                            SELECT game_type, SUM(times_hit) as total_stuck
                            FROM network_stuck_points
                            GROUP BY game_type
                            ORDER BY total_stuck DESC
                            LIMIT 5
                        """)
                        if stuck_games:
                            for game in stuck_games:
                                game_type = game['game_type']
                                concept_results = cods_instance.check_all_relevant_concepts(game_type)
                                if concept_results.get('unlocks'):
                                    for unlock in concept_results['unlocks']:
                                        print(f"  [CONCEPT-UNLOCK] {unlock['primitive']} "
                                              f"(concept '{unlock.get('reason', 'unknown')}' for {game_type})")
                except Exception as e:
                    pass  # Supplemental analysis
                
                # PRIMITIVE INVENTORY: Show what network has access to
                try:
                    cods_instance = CODSEngine() if CODSEngine else None
                    if cods_instance:
                        inventory = cods_instance.get_primitive_inventory()
                        summary = inventory.get('summary', {})
                        print(f"[CODS-INVENTORY] Available: {summary.get('total_available', 0)} primitives "
                              f"(seed={summary.get('seed_count', 0)}, "
                              f"grandfathered={summary.get('grandfathered_count', 0)}, "
                              f"unlocked={summary.get('unlocked_count', 0)}, "
                              f"novel={summary.get('novel_count', 0)}) | "
                              f"Locked: {summary.get('locked_count', 0)}")
                        
                        # Show most used if any usage
                        most_used = summary.get('most_used', [])
                        if most_used:
                            top_3 = most_used[:3]
                            usage_str = ", ".join(f"{name}({data['calls']})" for name, data in top_3)
                            print(f"[CODS-INVENTORY] Most used: {usage_str}")
                except Exception as e:
                    pass  # Silently skip inventory display on error
            except Exception as e:
                print(f"[CODS] Unlock check skipped: {e}")
        
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
            
            # Phase 5: Horizontal Gene Transfer with Emotional Intelligence
            try:
                transfer_count = self.transfer_engine.execute_generation_transfers(
                    self.current_generation, max_transfers_per_agent=2
                )
                if transfer_count > 0:
                    print(f"[PHASE 5] 🧬 Horizontal transfers: {transfer_count} knowledge injections")
                else:
                    print(f"[PHASE 5] 🧬 No compatible transfers found this generation")
            except Exception as e:
                print(f"[PHASE 5]  Horizontal transfer error: {e}")
            
            if not success:
                # Check if we hit max generations
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
        # Skip in test mode for faster startup
        if self.skip_cleanup:
            print("\n[SKIP] Skipping database cleanup (test mode)")
        else:
            print("\n[?]  Performing startup database cleanup...")
            self._cleanup_old_logs()
        
        # Sync schema file with actual database (catches tables created by other modules)
        if SCHEMA_MAINTENANCE_AVAILABLE and SchemaAutoMaintenance:
            try:
                schema_maint = SchemaAutoMaintenance(self.db.db_path)
                schema_maint.regenerate_schema_file()
                print("[OK] Schema file synced with database")
            except Exception as e:
                print(f"[WARN] Schema sync failed: {e}")
        
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
                    print("\n[WARN]  Current cycle cancelled - shutting down gracefully")
                    break
                
                except Exception as e:
                    if self.shutdown_requested:
                        # Ignore errors during shutdown - they're expected
                        print(f"\n[WARN]  Error during shutdown (ignored): {type(e).__name__}")
                        break
                    else:
                        # Real error - log and continue
                        print(f"\n[WARN]  Cycle error: {e}")
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
            print("\n\n[PAUSE]  Keyboard interrupt received")
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
        
        # ======================================================================
        # DETAILED GAMEPLAY METRICS (Run automatically when all games finish)
        # ======================================================================
        print("\n" + "-"*80)
        print("[METRICS] DETAILED GAMEPLAY ANALYSIS")
        print("-"*80)
        
        try:
            import sqlite3
            conn = sqlite3.connect(self.db.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 1. Recent game results (last 3 hours or this session)
            cursor.execute("""
                SELECT 
                    gr.game_id,
                    gr.game_type,
                    gr.final_score,
                    gr.levels_completed,
                    gr.total_actions,
                    gr.agent_id,
                    gr.ended_at
                FROM game_results gr
                WHERE gr.ended_at >= datetime('now', '-3 hours')
                ORDER BY gr.ended_at DESC
                LIMIT 25
            """)
            recent_games = cursor.fetchall()
            
            if recent_games:
                print(f"\nRecent Games (last 3 hours): {len(recent_games)}")
                
                # Calculate stats
                scores = [g['final_score'] or 0 for g in recent_games]
                levels = [g['levels_completed'] or 0 for g in recent_games]
                actions = [g['total_actions'] or 0 for g in recent_games]
                
                positive_scores = sum(1 for s in scores if s > 0)
                level_wins = sum(1 for l in levels if l > 0)
                
                print(f"  Positive Scores: {positive_scores}/{len(recent_games)} ({100*positive_scores/len(recent_games):.1f}%)")
                print(f"  Level Completions: {level_wins}/{len(recent_games)} ({100*level_wins/len(recent_games):.1f}%)")
                print(f"  Avg Score: {sum(scores)/len(scores):.2f}")
                print(f"  Avg Levels: {sum(levels)/len(levels):.2f}")
                print(f"  Avg Actions: {sum(actions)/len(actions):.1f}")
                print(f"  Best Score: {max(scores):.1f}, Best Levels: {max(levels)}")
                
                # Game type distribution
                game_types = {}
                for g in recent_games:
                    gt = g['game_type'] or 'unknown'
                    if gt not in game_types:
                        game_types[gt] = {'count': 0, 'total_score': 0, 'total_levels': 0}
                    game_types[gt]['count'] += 1
                    game_types[gt]['total_score'] += g['final_score'] or 0
                    game_types[gt]['total_levels'] += g['levels_completed'] or 0
                
                print(f"\n  By Game Type:")
                for gt, stats in sorted(game_types.items(), key=lambda x: -x[1]['count']):
                    avg_score = stats['total_score'] / stats['count']
                    avg_levels = stats['total_levels'] / stats['count']
                    print(f"    {gt}: {stats['count']} games, avg score {avg_score:.2f}, avg levels {avg_levels:.2f}")
            
            # 2. Winning sequences status
            cursor.execute("""
                SELECT COUNT(*) as total FROM winning_sequences WHERE is_active = 1
            """)
            seq_count = cursor.fetchone()['total']
            
            cursor.execute("""
                SELECT COUNT(DISTINCT game_id) as games FROM winning_sequences WHERE is_active = 1
            """)
            seq_games = cursor.fetchone()['games']
            
            cursor.execute("""
                SELECT COUNT(*) as new_seqs FROM winning_sequences 
                WHERE is_active = 1 AND created_at >= datetime('now', '-3 hours')
            """)
            new_seqs = cursor.fetchone()['new_seqs']
            
            print(f"\nWinning Sequences:")
            print(f"  Total Active: {seq_count} sequences across {seq_games} games")
            print(f"  New (last 3h): {new_seqs}")
            
            # 3. CODS Status (if available)
            if CODS_AVAILABLE:
                try:
                    cursor.execute("""
                        SELECT status, COUNT(*) as cnt FROM primitive_status GROUP BY status
                    """)
                    prim_status = cursor.fetchall()
                    
                    if prim_status:
                        print(f"\nCODS Primitives:")
                        for row in prim_status:
                            print(f"  {row['status']}: {row['cnt']}")
                    
                    cursor.execute("""
                        SELECT COUNT(*) as cnt FROM composed_operators WHERE status != 'pruned'
                    """)
                    comp_ops = cursor.fetchone()
                    if comp_ops:
                        print(f"  Composed Operators: {comp_ops['cnt']}")
                    
                    cursor.execute("""
                        SELECT COUNT(*) as cnt FROM oracle_decisions WHERE verdict = 'approved'
                    """)
                    unlocks = cursor.fetchone()
                    if unlocks:
                        print(f"  Oracle Unlocks: {unlocks['cnt']}")
                except Exception as e:
                    print(f"  (CODS stats unavailable: {e})")
            
            conn.close()
            
        except Exception as e:
            print(f"  (Could not load detailed metrics: {e})")
        
        print("-"*80)
        
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
        evolution_interval_minutes=args.evolution_interval,
        agi_mode=args.diversity_mode  # NEW: Pass diversity mode flag
    )
    
    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
