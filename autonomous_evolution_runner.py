#!/usr/bin/env python3
import os
import sys

# Enforce no bytecode before any imports
sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

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
import json
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
from ouroboros_coordinator import OuroborosNetworkSteward
from agent_factory import AgentFactory
from performance_analyzer import PerformanceAnalyzer
from disk_space_monitor import DiskSpaceMonitor
from evolutionary_engine import EvolutionaryEngine
from arc_rlvr_framework import ARCRLVRFramework
from arc_api_client import ARCClient
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
from pariah_validator import PariahValidator, run_pariah_validation  # False pariah detection/cleanup
# GameDiversityPreserver import removed - prestige-only protection now

# Sequence Miner - retroactive learning from winning sequences
try:
    from sequence_miner import SequenceMiner
    SEQUENCE_MINER_AVAILABLE = True
except ImportError:
    SEQUENCE_MINER_AVAILABLE = False
    SequenceMiner = None

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

# Oracle Health Monitor - self-diagnostic and experimentation system
try:
    from oracle_health_monitor import OracleHealthMonitor, HealthStatus
    from console_metrics_capture import (
        ConsoleMetricsCapture, get_metrics_capture, reset_metrics_capture,
        record_game_start, record_game_end, record_cods, record_stuck,
        get_reasoning_capture, get_reasoning_diagnostics, ReasoningLogCapture
    )
    ORACLE_HEALTH_AVAILABLE = True
except ImportError:
    ORACLE_HEALTH_AVAILABLE = False
    OracleHealthMonitor = None
    HealthStatus = None
    ConsoleMetricsCapture = None
    get_reasoning_capture = None
    get_reasoning_diagnostics = None
    ReasoningLogCapture = None

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
        target_game: str | None = None,  # NEW: Focus on specific game (e.g., "as66")
        replay_validation_batch: bool = False,  # Run REPLAY_VALIDATION pass over replay_index (no live play)
        replay_validation_limit: Optional[int] = None,  # Optional cap on validations
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
        self.coordinator = OuroborosNetworkSteward(self.db)
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
        from oracle_stuck_game_diagnostics import OracleStuckGameDiagnostics
        
        self.subgoal_planner = SubgoalPlanner(self.db)  # Hierarchical planning
        self.frustration_detector = FrustrationDetector(self.db)  # Frustration tracking
        self.stuck_game_diagnostics = OracleStuckGameDiagnostics(self.db)  # DIAGNOSTIC ONLY - no interventions
        self.near_miss_analyzer = NearMissAnalyzer(self.db)  # Learn from 15-18/20 scores
        self.collective_reasoner = CollectiveReasoningEngine(self.db)  # Multi-agent collaboration
        self.counterfactual_analyzer = CounterfactualAnalyzer(self.db)  # "What if?" analysis
        
        print("[OK] Breakthrough systems initialized (Subgoal Planning, Stuck Game Diagnostics, Near-Miss Analysis, Collective Reasoning, Counterfactual Analysis)")
        
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
        self.replay_validation_batch = replay_validation_batch
        self.replay_validation_limit = replay_validation_limit
        
        self.current_generation = 0
        self.total_games_played = 0
        self.start_time = datetime.now()
        self.last_evolution_time = None
        
        self.running = False
        self.paused = False
        self.shutdown_requested = False
        self.shutdown_press_count = 0
        self.shutdown_last_press_time = None
        self._shutdown_listener_task = None
        
        # ORACLE HEALTH MONITOR - self-diagnostic and experimentation system
        if ORACLE_HEALTH_AVAILABLE and OracleHealthMonitor:
            self.oracle_health = OracleHealthMonitor(db=self.db)
            self.metrics_capture = ConsoleMetricsCapture(generation=0)
            # Initialize reasoning log capture for automated bug detection
            if get_reasoning_capture:
                try:
                    self.reasoning_capture = get_reasoning_capture(0)
                    print("[OK] Reasoning Log Capture initialized (automated reasoning bug detection)")
                except Exception as e:
                    self.reasoning_capture = None
                    print(f"[WARN] Reasoning capture init failed: {e}")
            else:
                self.reasoning_capture = None
            print("[OK] Oracle Health Monitor initialized (autonomous diagnostics enabled)")
        else:
            self.oracle_health = None
            self.metrics_capture = None
            self.reasoning_capture = None
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

    async def _verify_arc_api_live(self) -> bool:
        """Ensure we are using the real ARC API (no simulated games)."""
        api_key = os.getenv('ARC_API_KEY')
        if not api_key:
            print("[FATAL] ARC_API_KEY missing - refusing to run simulated games")
            return False
        try:
            async with ARCClient(api_key=api_key) as client:
                games = await client.get_available_games()
                if not games:
                    print("[FATAL] ARC API returned zero available games - aborting to avoid simulated runs")
                    return False
            return True
        except Exception as e:
            print(f"[FATAL] ARC API connectivity failed: {e}")
            return False

    async def _shutdown_listener(self):
        """Listen for manual shutdown via Function key + Enter (enter 'F12')."""
        import sys
        while self.running and not self.shutdown_requested:
            try:
                line = await asyncio.to_thread(sys.stdin.readline)
            except Exception:
                break
            if not line:
                break
            if line.strip().lower() == 'f12':
                try:
                    sys.stderr.write("\n[X] F12 shutdown requested\nInitiating graceful shutdown...\n\n")
                    sys.stderr.flush()
                except Exception:
                    pass
                self.running = False
                self.shutdown_requested = True
                try:
                    self.game_scheduler.shutdown()
                except Exception:
                    pass
                if hasattr(self, '_current_engine') and self._current_engine:
                    self._current_engine.session_manager.is_shutting_down = True
                break
    
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
                
                # Check disk space before vacuum (requires 2x database size)
                db_path = getattr(self.db, 'db_path', 'core_data.db')
                if os.path.exists(db_path):
                    db_size = os.path.getsize(db_path)
                    drive = os.path.splitdrive(os.path.abspath(db_path))[0] or '/'
                    try:
                        import shutil
                        free_space = shutil.disk_usage(drive).free
                        if free_space > db_size * 2:
                            self.db.execute_query("VACUUM")
                            print(f"  [DB] Vacuumed database (had {free_space/(1024**3):.1f}GB free)")
                        else:
                            print(f"  [SKIP] VACUUM skipped - need {db_size*2/(1024**3):.1f}GB, have {free_space/(1024**3):.1f}GB free")
                    except Exception as e:
                        print(f"  [SKIP] VACUUM skipped - disk check failed: {e}")
                
                logs_removed = total_logs - 10000
                print(f"  [DB] Cleaned up {logs_removed:,} old log entries (kept 10K most recent)")
                
        except Exception as e:
            print(f"[WARN]  Log cleanup failed (non-critical): {e}")

    def _enforce_no_pycache(self, root: Optional[str] = None) -> None:
        """Fail early if __pycache__ directories exist (rule: pycache off)."""
        base_dir = root or os.getcwd()
        forbidden = []
        for dirpath, dirnames, _ in os.walk(base_dir):
            parts = dirpath.split(os.sep)
            if any(part in {'.git', '.venv', 'env', 'node_modules'} for part in parts):
                dirnames[:] = []
                continue
            if os.path.basename(dirpath) == '__pycache__':
                forbidden.append(dirpath)
                dirnames[:] = []
        if forbidden:
            sample = "; ".join(sorted(forbidden)[:5])
            raise RuntimeError(f"__pycache__ present: {sample}")
    
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

    async def run_replay_validation_batch(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Run REPLAY_VALIDATION over stored replay_index pointers without live gameplay."""

        print("\n[?] Running replay validation batch (REPLAY_VALIDATION mode)...")

        api_key = os.getenv('ARC_API_KEY')
        if not api_key:
            print("[?] ARC_API_KEY not found in environment")
            return {'validated': 0, 'pointers_found': 0, 'missing': 0}

        params = []
        query = (
            """
            SELECT arc_game_id, MAX(id) as latest_id
            FROM replay_index
            WHERE arc_game_id IS NOT NULL
            """
        )

        if self.target_game:
            query += " AND arc_game_id LIKE ?"
            params.append(f"{self.target_game}%")

        query += " GROUP BY arc_game_id ORDER BY latest_id DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        replay_rows = self.db.execute_query(query, tuple(params)) if params else self.db.execute_query(query)

        if not replay_rows:
            scope = f" for target '{self.target_game}'" if self.target_game else ""
            print(f"[?] No replay_index entries found{scope}")
            return {'validated': 0, 'pointers_found': 0, 'missing': 0}

        replay_games = [row['arc_game_id'] for row in replay_rows if row.get('arc_game_id')]
        print(f"  Found {len(replay_games)} replay_index entries for validation" + (f" (limit {limit})" if limit else ""))

        # Use any active agent for provenance; optional in replay path
        agent_id = None
        try:
            active_agents = self.db.get_active_agents()
            if active_agents:
                agent_id = active_agents[0]['agent_id']
        except Exception as e:
            print(f"  [WARN] Unable to fetch active agents for replay provenance: {e}")

        validated = 0
        pointer_hits = 0
        missing = []
        guard_violations = 0

        async with GameplayEngine(api_key, db_path=self.db.db_path) as engine:
            # Keep config minimal: we only want REPLAY pointer reads
            engine.configure(
                mode='REPLAY_VALIDATION',
                strategy='balanced',
                enable_random_exploration=False,
                enable_pattern_learning=False,
                max_actions_per_level=1,
                max_total_actions=1,
                current_generation=self.current_generation,
                agent_operating_mode='generalist'
            )

            try:
                available_games = await engine.session_manager.get_available_games()
                available_ids = [g.get('id', g.get('game_id')) for g in available_games if g.get('id') or g.get('game_id')]
                available_ids = [gid for gid in available_ids if gid]
            except Exception as e:
                available_ids = []
                print(f"  [WARN] Unable to fetch available games for missing report: {e}")

            for entry in replay_rows:
                game_id = entry.get('arc_game_id') or "unknown"
                if self.shutdown_requested:
                    engine.session_manager.is_shutting_down = True
                    break
                try:
                    result = await engine.play_single_game(game_id, agent_id=agent_id)
                except asyncio.CancelledError:
                    engine.session_manager.is_shutting_down = True
                    raise
                validated += 1
                if result.get('final_state') == 'REPLAY_POINTER':
                    pointer_hits += 1
                else:
                    missing.append(game_id)

                # Validate ACTION6 coordinates for this replay entry
                try:
                    guard_stats = self._validate_action6_replay(entry)
                    guard_violations += guard_stats.get('violations', 0)
                    if guard_stats.get('violations', 0) > 0:
                        msg = guard_stats.get('message', 'ACTION6 validation failures')
                        print(f"  [WARN] {msg} for replay {entry.get('replay_id') or entry.get('attempt_id')}")
                except Exception as guard_err:
                    guard_violations += 1
                    print(f"  [WARN] ACTION6 validation error: {guard_err}")

        # Report coverage against available games (optional)
        coverage_gap = []
        if available_ids:
            filtered_available = [gid for gid in available_ids if not self.target_game or gid.startswith(self.target_game)]
            coverage_gap = [gid for gid in filtered_available if gid not in set(replay_games)]
            if coverage_gap:
                gap_display = ", ".join(coverage_gap[:5])
                if len(coverage_gap) > 5:
                    gap_display += f" ... (+{len(coverage_gap)-5} more)"
                print(f"  [GAP] Games without replay_index entries: {gap_display}")

        self.total_games_played += validated

        print(f"[OK] Replay validation complete: {pointer_hits}/{validated} pointers found")
        if missing:
            print(f"  [WARN] {len(missing)} replay entries returned missing pointers")
        if guard_violations:
            print(f"  [WARN] {guard_violations} ACTION6 coordinate validation failures")

        return {
            'validated': validated,
            'pointers_found': pointer_hits,
            'missing': len(missing),
            'coverage_gap': len(coverage_gap),
            'guard_violations': guard_violations
        }

    def _validate_action6_replay(self, replay_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Check recorded ACTION6 traces for coordinates and bounds; log guard failures if missing."""

        attempt_id = replay_entry.get('attempt_id')
        scorecard_id = replay_entry.get('scorecard_id')
        arc_game_id = replay_entry.get('arc_game_id')

        # Locate session via game_results using scorecard_id
        session_row = None
        if scorecard_id:
            rows = self.db.execute_query(
                "SELECT session_id, game_id FROM game_results WHERE scorecard_id = ? ORDER BY end_time DESC LIMIT 1",
                (scorecard_id,),
            )
            session_row = rows[0] if rows else None

        if not session_row:
            # Without session we cannot validate frames; record failure if attempt_id exists
            if attempt_id:
                self.db.execute_query(
                    "INSERT INTO hook_failures (attempt_id, hook_name, hook_phase, exception_type, message, stack_hash, auto_disabled_flag, game_id, level, agent_id, generation, guard_code) "
                    "VALUES (?, ?, 'guard', ?, ?, ?, 0, ?, ?, ?, ?, ?)",
                    (
                        attempt_id,
                        'action6_validation',
                        'action6_missing_session',
                        'No session for scorecard',
                        'action6_missing_session',
                        arc_game_id,
                        None,
                        None,
                        None,
                        'action6_missing_session',
                    ),
                )
            return {'checked': 0, 'violations': 1, 'message': 'No session found for scorecard'}

        session_id = session_row.get('session_id')
        game_id = session_row.get('game_id') or arc_game_id

        # Fetch agent/generation for provenance
        attempt_row = None
        if attempt_id:
            rows = self.db.execute_query(
                "SELECT agent_id, generation FROM attempts WHERE attempt_id = ? LIMIT 1",
                (attempt_id,),
            )
            attempt_row = rows[0] if rows else None
        agent_id = attempt_row.get('agent_id') if attempt_row else None
        generation = attempt_row.get('generation') if attempt_row else None

        traces = self.db.execute_query(
            "SELECT action_number, coordinates, frame_before, frame_after FROM action_traces WHERE session_id = ? AND action_number = 6",
            (session_id,),
        )
        if not traces:
            return {'checked': 0, 'violations': 0}

        # Cross-check proposals: ACTION6 should have an attention window id (salience source)
        attention_rows = self.db.execute_query(
            "SELECT chosen_action, attention_window_id FROM action_proposals_log WHERE attempt_id = ? AND chosen_action LIKE 'ACTION6%'",
            (attempt_id,),
        ) if attempt_id else []

        attention_missing = 0
        if traces and attempt_id:
            if not attention_rows:
                attention_missing = len(traces)
            else:
                for row in attention_rows:
                    aw = row.get('attention_window_id') if row else None
                    if not aw:
                        attention_missing += 1

        # Determine frame bounds from first available frame
        def _parse_frame(frame_blob: Any) -> Optional[list]:
            if not frame_blob:
                return None
            if isinstance(frame_blob, str):
                try:
                    return json.loads(frame_blob)
                except Exception:
                    return None
            return frame_blob if isinstance(frame_blob, list) else None

        sample_frame = None
        for t in traces:
            sample_frame = _parse_frame(t.get('frame_before')) or _parse_frame(t.get('frame_after'))
            if sample_frame:
                break

        height = len(sample_frame) if sample_frame else None
        width = len(sample_frame[0]) if sample_frame and sample_frame and sample_frame[0] else None

        violations = 0
        for t in traces:
            coord_raw = t.get('coordinates')
            try:
                coord = json.loads(coord_raw) if isinstance(coord_raw, str) else coord_raw
            except Exception:
                coord = None
            if not coord or 'x' not in coord or 'y' not in coord:
                violations += 1
                continue
            x, y = coord.get('x'), coord.get('y')
            if height is not None and width is not None:
                if x is None or y is None or x < 0 or y < 0 or y >= height or x >= width:
                    violations += 1

        violations += attention_missing

        if violations and attempt_id:
            self.db.execute_query(
                "INSERT INTO hook_failures (attempt_id, hook_name, hook_phase, exception_type, message, stack_hash, auto_disabled_flag, game_id, level, agent_id, generation, guard_code) "
                "VALUES (?, ?, 'guard', ?, ?, ?, 0, ?, ?, ?, ?, ?)",
                (
                    attempt_id,
                    'action6_validation',
                    'action6_missing_coords',
                    f'{violations} ACTION6 traces missing/invalid coordinates or salience windows',
                    'action6_missing_coords',
                    game_id,
                    None,
                    agent_id,
                    generation,
                    'action6_missing_coords',
                ),
            )

        return {
            'checked': len(traces),
            'violations': violations,
            'attention_missing': attention_missing,
        }
    
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
                mixed_domain_flag = bool(int(os.getenv("ENABLE_MIXED_DOMAIN", "0")))

                game_assignments = self.game_scheduler.assign_games_to_agents(
                    agents=agents_with_modes,
                    total_games_to_play=num_games,
                    available_game_ids=game_ids,
                    ensure_game_type_coverage=self.ensure_game_type_coverage,
                    mixed_domain=mixed_domain_flag,
                )

                if not game_assignments:
                    print("[?] No games could be assigned (all games may be in use)")
                    return {'games_played': 0, 'wins': 0, 'win_rate': 0.0, 'avg_score': 0.0}

                print(f" Assigned {sum(len(g) for g in game_assignments.values())} games to {len(game_assignments)} agents\n")

                # ------------------------------------------------------------------
                # SWARM EXECUTION: launch one task per game slot (concurrent per game)
                # ------------------------------------------------------------------
                swarm_slots = []
                for agent in selected_agents:
                    agent_id = agent['agent_id']
                    agent_games = game_assignments.get(agent_id, [])
                    if not agent_games:
                        continue
                    # Determine agent mode
                    agent_mode = mode_assignments.get(agent_id, 'generalist')
                    # Persist best mode for this game if known
                    for game_id in agent_games:
                        best_mode = mode_system.get_best_mode_for_game(agent_id, game_id)
                        if best_mode:
                            agent_mode = best_mode
                        # Optimizer target level per game
                        optimizer_target_level = None
                        if agent_mode == 'optimizer':
                            all_targets = self.optimization_tracker.get_optimization_targets(
                                agent_mode='optimizer',
                                limit=100
                            )
                            game_targets = [t for t in all_targets if t['game_id'] == game_id]
                            if game_targets:
                                optimizer_target_level = game_targets[0]['level_number']
                        # Dynamic budgets per game with role/w_B multipliers
                        agent_salary = self.adaptive_limits.calculate_agent_salary(agent_id, self.current_generation)
                        game_budget_dict = self.budget_allocator.calculate_game_budget(game_id)

                        budget_multiplier = agent_salary.get('budget_multiplier', 1.0)

                        scaled_per_level = int(game_budget_dict['action_allowance_per_level'] * budget_multiplier)
                        scaled_total = int(game_budget_dict['action_allowance_total'] * budget_multiplier)

                        # Clamp by global bounds and agent-specific ceilings (dual economies: ATP only)
                        final_per_level = min(
                            agent_salary.get('action_allowance_per_level', scaled_per_level),
                            max(
                                self.adaptive_limits.MIN_ACTIONS_PER_LEVEL,
                                min(self.adaptive_limits.MAX_ACTIONS_PER_LEVEL, scaled_per_level)
                            ),
                        )

                        final_total = min(
                            agent_salary.get('action_allowance_total', scaled_total),
                            max(
                                self.adaptive_limits.MIN_TOTAL_ACTIONS,
                                min(self.adaptive_limits.MAX_TOTAL_ACTIONS, scaled_total)
                            ),
                        )

                        # Ensure total budget can cover multi-level play (at least 3x per-level)
                        final_total = max(final_total, final_per_level * 3)

                        swarm_slots.append({
                            'agent_id': agent_id,
                            'agent_mode': agent_mode,
                            'game_id': game_id,
                            'optimizer_target_level': optimizer_target_level,
                            'game_budget': final_total,
                            'actions_per_level': final_per_level
                        })

                if not swarm_slots:
                    print("[?] No swarm slots after scheduling")
                    return {'games_played': 0, 'wins': 0, 'win_rate': 0.0, 'avg_score': 0.0}

                # Parallel mixed-domain encouragement: interleave slots by game_type prefix
                try:
                    buckets: Dict[str, List[Dict[str, Any]]] = {}
                    for slot in swarm_slots:
                        gpref = (slot.get('game_id') or 'unk')[:4]
                        buckets.setdefault(gpref, []).append(slot)
                    interleaved: List[Dict[str, Any]] = []
                    max_bucket = max(len(v) for v in buckets.values()) if buckets else 0
                    for idx in range(max_bucket):
                        for gpref, items in buckets.items():
                            if idx < len(items):
                                interleaved.append(items[idx])
                    if interleaved:
                        swarm_slots = interleaved
                except Exception as mix_err:
                    print(f"  [WARN] Domain interleave failed: {mix_err}")

                game_ids_for_slots = {slot.get('game_id') for slot in swarm_slots if slot.get('game_id')}
                target_single_game = bool(self.target_game) and len(game_ids_for_slots) == 1
                concurrency_limit = 1 if target_single_game else min(8, len(swarm_slots))
                semaphore = asyncio.Semaphore(concurrency_limit)

                async def run_swarm_slot(slot):
                    nonlocal rules_learned
                    async with semaphore:
                        agent_id = slot['agent_id']
                        agent_mode = slot['agent_mode']
                        game_id = slot['game_id']
                        optimizer_target_level = slot.get('optimizer_target_level')
                        game_budget = slot['game_budget']
                        actions_per_level = slot['actions_per_level']

                        async with GameplayEngine(api_key, db_path=self.db.db_path) as engine_slot:
                            # Propagate shutdown early
                            if self.shutdown_requested:
                                engine_slot.session_manager.is_shutting_down = True
                                return None

                            try:
                                # Configure engine per slot
                                engine_slot.configure(
                                    strategy='balanced',
                                    max_actions_per_level=actions_per_level,
                                    max_total_actions=game_budget,
                                    enable_random_exploration=True,
                                    enable_pattern_learning=True,
                                    diversity_mode=self.agi_mode,
                                    enforce_game_diversity=self.agi_mode,
                                    max_repeats_per_game=5 if self.agi_mode else 999,
                                    specialist_mode=self.specialist_mode,
                                    agent_operating_mode=agent_mode,
                                    optimizer_target_level=optimizer_target_level,
                                    current_generation=self.current_generation
                                )

                                # ORACLE metrics capture per slot
                                if self.metrics_capture:
                                    game_type = game_id[:4] if len(game_id) >= 4 else 'unknown'
                                    self.metrics_capture.start_game(game_id, game_type, agent_id)

                                try:
                                    result = await engine_slot.play_single_game(game_id, agent_id=agent_id)
                                except asyncio.CancelledError:
                                    if self.shutdown_requested:
                                        engine_slot.session_manager.is_shutting_down = True
                                    raise

                                # Metrics end
                                if self.metrics_capture:
                                    self.metrics_capture.end_game(
                                        game_id,
                                        result.get('final_score', 0),
                                        result.get('levels_completed', 0),
                                        result.get('actions_taken', 0)
                                    )

                                # Reward processing and bookkeeping (same as sequential path)
                                rlvr = ARCRLVRFramework(self.db)
                                game_session_results = {
                                    'game_id': game_id,
                                    'session_id': engine_slot.session_manager.current_session_id,
                                    'win_detected': result.get('win', False),
                                    'final_score': result.get('final_score', 0),
                                    'win_score': 1.0,
                                    'total_actions': result.get('actions_taken', 0),
                                    'level_completions': int(result.get('final_score', 0)),
                                    'frame_changes': 0
                                }
                                reward_data = rlvr.process_arc_rewards(agent_id, game_session_results)
                                self.db.store_arc_reward_data(agent_id, reward_data)

                                try:
                                    engine_slot.session_manager.deduct_actions_used(agent_id, game_id)
                                except Exception as deduct_e:
                                    logger.debug(f"Action deduction failed (non-critical): {deduct_e}")

                                # Frustration tracking
                                if self.frustration_detector:
                                    try:
                                        prev_best = self.db.execute_query(
                                            """
                                            SELECT MAX(final_score) as best_score
                                            FROM agent_arc_performance
                                            WHERE agent_id = ? AND game_id = ?
                                            """,
                                            (agent_id, game_id),
                                        )
                                        previous_best_score = prev_best[0]['best_score'] if prev_best and prev_best[0]['best_score'] else 0.0
                                        self.frustration_detector.update_agent_frustration(
                                            agent_id=agent_id,
                                            game_id=game_id,
                                            score_achieved=result.get('final_score', 0),
                                            previous_best_score=previous_best_score,
                                            actions_taken=result.get('actions_taken', 0),
                                            generation=self.current_generation,
                                        )
                                    except Exception as e:
                                        print(f"  [WARN] Frustration detection failed: {e}")

                                # Near-miss analysis
                                final_score = result.get('final_score', 0)
                                if self.near_miss_analyzer and final_score >= 15 and not result.get('win', False):
                                    try:
                                        session_id = engine_slot.session_manager.current_session_id or "unknown"
                                        insights_id = self.near_miss_analyzer.analyze_near_miss(
                                            agent_id=agent_id,
                                            game_id=game_id,
                                            session_id=session_id,
                                            final_score=final_score,
                                            total_actions=result.get('actions_taken', 0),
                                            generation=self.current_generation,
                                        )
                                        if insights_id and hasattr(engine_slot, 'cods_engine') and engine_slot.cods_engine:
                                            try:
                                                engine_slot.cods_engine.process_near_miss_patterns(insights_id)
                                            except Exception:
                                                pass
                                    except Exception as e:
                                        print(f"  [WARN] Near-miss analysis failed: {e}")

                                # Counterfactual analysis
                                if self.counterfactual_analyzer and not result.get('win', False) and final_score < 15:
                                    try:
                                        session_id = engine_slot.session_manager.current_session_id or "unknown"
                                        learning_ids = self.counterfactual_analyzer.analyze_failure(
                                            agent_id=agent_id,
                                            game_id=game_id,
                                            session_id=session_id,
                                            final_score=final_score,
                                            generation=self.current_generation,
                                        )
                                        if learning_ids and hasattr(engine_slot, 'cods_engine') and engine_slot.cods_engine:
                                            try:
                                                engine_slot.cods_engine.process_counterfactual_insights(learning_ids)
                                            except Exception:
                                                pass
                                    except Exception as e:
                                        print(f"  [WARN] Counterfactual analysis failed: {e}")

                                # CODS outcome logging
                                if hasattr(engine_slot, 'cods_engine') and engine_slot.cods_engine:
                                    try:
                                        cods_result = engine_slot.cods_engine.record_game_outcome(
                                            game_id=game_id,
                                            final_score=final_score,
                                            max_level_reached=result.get('level_completions', 0) + 1,
                                            total_actions=result.get('actions_taken', 0),
                                            won=result.get('win', False),
                                        )
                                        if cods_result.get('primitive_gaps'):
                                            print(f"  [CODS] Detected {len(cods_result['primitive_gaps'])} primitive gaps")
                                    except Exception:
                                        pass

                                # Mode effectiveness tracking
                                mode_system.update_mode_effectiveness(
                                    agent_id=agent_id,
                                    generation=self.current_generation,
                                    score=result.get('final_score', 0),
                                    win=result.get('win', False),
                                    actions=result.get('actions_taken', 0),
                                )

                                # Viral package usage tracking
                                try:
                                    from viral_package_engine import ViralPackageEngine
                                    viral_engine = ViralPackageEngine(self.db)
                                    infections = self.db.execute_query(
                                        """
                                        SELECT package_id 
                                        FROM agent_viral_infections 
                                        WHERE agent_id = ? AND is_active = TRUE
                                        """,
                                        (agent_id,),
                                    )
                                    success = result.get('win', False) or result.get('final_score', 0) > 0
                                    score_change = result.get('final_score', 0)
                                    current_gen = self.db.execute_query(
                                        "SELECT generation FROM agents WHERE agent_id = ?",
                                        (agent_id,),
                                    )
                                    generation = current_gen[0]['generation'] if current_gen else self.current_generation
                                    for infection in infections:
                                        viral_engine.record_package_usage(
                                            agent_id=agent_id,
                                            package_id=infection['package_id'],
                                            success=success,
                                            score_change=score_change,
                                            generation=generation,
                                        )
                                except Exception:
                                    pass

                                # Rule extraction on wins
                                if result.get('win', False) and self.rule_engine and hasattr(engine_slot, 'session_manager'):
                                    try:
                                        game_session_data = {
                                            'game_id': game_id,
                                            'agent_id': agent_id,
                                            'session_id': engine_slot.session_manager.current_session_id,
                                            'initial_frame': result.get('initial_frame'),
                                            'action_sequence': result.get('action_sequence', []),
                                            'frame_states': result.get('frame_states', []),
                                            'won': True,
                                            'score_achieved': result.get('final_score', 0),
                                        }
                                        new_rule = self.rule_engine.extract_rule_from_game_session(game_session_data)
                                        if new_rule:
                                            print(f"  [?] Learned new rule: {new_rule['rule_name']}")
                                            rules_learned += 1
                                    except Exception as e:
                                        print(f"  [WARN]  Failed to extract rule: {e}")

                                # Release game slot and return summary
                                return {
                                    'agent_id': agent_id,
                                    'game_id': game_id,
                                    'result': result,
                                    'reward': reward_data
                                }
                            finally:
                                # Ensure scheduler release even on early exit
                                self.game_scheduler.release_game(game_id, agent_id=agent_id)

                # Launch all swarm slots concurrently
                swarm_tasks = [asyncio.create_task(run_swarm_slot(slot)) for slot in swarm_slots]
                slot_results = await asyncio.gather(*swarm_tasks, return_exceptions=True)

                # Aggregate results, handling cancellations/errors
                for slot_res in slot_results:
                    if slot_res is None:
                        continue
                    if isinstance(slot_res, Exception):
                        print(f"  [WARN] Swarm slot failed: {slot_res}")
                        continue
                    result = slot_res['result']
                    agent_id = slot_res['agent_id']
                    game_id = slot_res['game_id']
                    reward_data = slot_res['reward']

                    final_score = result.get('final_score', 0)
                    if result.get('win', False):
                        total_wins += 1
                    total_score += final_score
                    results.append(slot_res)
                
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
            
            # PARIAH VALIDATION: Detect and remove false pariahs
            # False pariahs are as dangerous as prestige vampires - they block essential actions
            print(f"\n[PARIAH VALIDATION] Checking for false pariahs in generation {self.current_generation}...")
            try:
                pariah_results = run_pariah_validation(self.db, self.current_generation)
                
                if pariah_results['pariahs_deactivated'] > 0:
                    print(f"[OK] Deactivated {pariah_results['pariahs_deactivated']} false pariahs")
                if pariah_results['stale_pariahs_decayed'] > 0:
                    print(f"[OK] Decayed {pariah_results['stale_pariahs_decayed']} stale pariahs")
                if pariah_results['awareness_cleaned'] > 0:
                    print(f"[OK] Cleaned {pariah_results['awareness_cleaned']} stale awareness records")
                if (pariah_results['pariahs_deactivated'] == 0 and 
                    pariah_results['stale_pariahs_decayed'] == 0):
                    print(f"[OK] All {pariah_results['pariahs_checked']} pariahs validated - no false positives")
                    
            except Exception as e:
                print(f"[WARN] Pariah validation failed: {e}")
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
            
            # PHASE 4.5: ORACLE STUCK GAME DIAGNOSTICS (Health Monitoring)
            # Diagnostic only - identifies WHICH TIER is broken, does NOT intervene
            # Philosophy: If games stuck, fix the SYSTEM. Let network intelligence emerge.
            print(f"\n[ORACLE] Running stuck game diagnostics...")
            try:
                stuck_games = self.stuck_game_diagnostics.check_stuck_games(self.current_generation)
                
                if stuck_games:
                    print(f"[!] {len(stuck_games)} games with high failure rates detected")
                    for game_type in stuck_games:
                        diagnosis = self.stuck_game_diagnostics.diagnose_stuck_game(
                            game_type, self.current_generation
                        )
                        
                        if diagnosis.broken_tier:
                            print(f"    {game_type}: {diagnosis.broken_tier} - {diagnosis.diagnosis}")
                            print(f"        FIX: {diagnosis.suggested_fix[:80]}...")
                        else:
                            print(f"    {game_type}: All tiers healthy (game may be difficult)")
                else:
                    print("[OK] No stuck games detected - network is learning")
                    
            except Exception as e:
                print(f"[WARN] Stuck game diagnostics failed: {e}")
            
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
        
        # ORACLE METRICS: Reset for new generation
        if self.metrics_capture:
            self.metrics_capture.reset(self.current_generation)
        
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
        
        # SEQUENCE MINING: Backfill learning data from winning sequences
        # Runs once per cycle to extract any missing knowledge from existing sequences
        if SEQUENCE_MINER_AVAILABLE:
            try:
                miner = SequenceMiner(self.db.db_path)
                mining_result = miner.mine_all_sequences()
                if mining_result.get('total_changes', 0) > 0:
                    print(f"[MINER] Backfilled: {mining_result.get('breakpoints_updated', 0)} breakpoints, "
                          f"{mining_result.get('triggers_inserted', 0)} triggers, "
                          f"{mining_result.get('outcomes_inserted', 0)} outcomes")
                miner.close()
            except Exception as e:
                print(f"[WARN] Sequence mining failed: {e}")
        
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
                    # Reuse the cods_engine instance created earlier (don't create a new one)
                    if cods_engine:
                        # ADAPTIVE: threshold = 10% of active agents (floor 15, cap 100)
                        strategy_results = cods_engine.process_agent_strategy_signals(
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
                    # Reuse cods_engine instance
                    if cods_engine:
                        stuck_analysis = cods_engine.analyze_stuck_points_for_unlocks(
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
                    # Reuse cods_engine instance
                    if cods_engine:
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
                                concept_results = cods_engine.check_all_relevant_concepts(game_type)
                                if concept_results.get('unlocks'):
                                    for unlock in concept_results['unlocks']:
                                        print(f"  [CONCEPT-UNLOCK] {unlock['primitive']} "
                                              f"(concept '{unlock.get('reason', 'unknown')}' for {game_type})")
                except Exception as e:
                    pass  # Supplemental analysis
                
                # PRIMITIVE INVENTORY: Show what network has access to
                try:
                    # Reuse cods_engine instance
                    if cods_engine:
                        inventory = cods_engine.get_primitive_inventory()
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
                
                # AGENT PATTERN DISCOVERY: Analyze agent gameplay for emerging patterns
                # This is the species writing its own cookbook through gameplay
                try:
                    if cods_engine:
                        # Run the full pattern discovery + synthesis pipeline
                        pattern_results = cods_engine.process_generation_patterns(
                            generation=self.current_generation
                        )
                        
                        # Show pattern discovery results
                        patterns = pattern_results.get('patterns', {})
                        if patterns.get('patterns_discovered'):
                            print(f"[AGENT-PATTERNS] Discovered {len(patterns['patterns_discovered'])} "
                                  f"primitive combinations from agent gameplay")
                            for p in patterns['patterns_discovered'][:3]:  # Top 3
                                prims = ' + '.join(p['primitives'])
                                print(f"  [{p['evidence_strength'].upper()}] {prims}: "
                                      f"success={p['success_rate']:.0%}, diff=+{p['differential']:.0%}")
                        
                        # Show synthesis results (from patterns feeding Bayesian system)
                        synth = pattern_results.get('synthesis', {})
                        if synth.get('syntheses_triggered', 0) > 0:
                            print(f"[CODS-SYNTH] Synthesized {synth['syntheses_triggered']} "
                                  f"operators from {synth['hypotheses_checked']} confirmed hypotheses")
                            for op_id in synth.get('operators_created', []):
                                print(f"  [SYNTH] New operator: {op_id}")
                            for prim in synth.get('primitives_unlocked', []):
                                print(f"  [UNLOCK] Primitive unlocked: {prim}")
                        
                        # Show hypothesis summary
                        hyp_summary = cods_engine.get_hypothesis_summary()
                        if hyp_summary.get('active', 0) > 0:
                            print(f"[CODS-BAYES] Hypotheses: {hyp_summary.get('active', 0)} active, "
                                  f"{hyp_summary.get('synthesized', 0)} synthesized, "
                                  f"max P={hyp_summary.get('max_posterior', 0):.2f}")
                        
                        # Prune refuted hypotheses periodically
                        if self.current_generation % 5 == 0:
                            pruned = cods_engine.prune_refuted_hypotheses(max_age_days=14)
                            if pruned > 0:
                                print(f"[CODS-BAYES] Pruned {pruned} refuted hypotheses")
                except Exception as e:
                    pass  # Supplemental - pattern discovery is optional
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
                    print(f"[PHASE 5] [DNA] Horizontal transfers: {transfer_count} knowledge injections")
                else:
                    print(f"[PHASE 5] [DNA] No compatible transfers found this generation")
            except Exception as e:
                print(f"[PHASE 5]  Horizontal transfer error: {e}")
            
            # ================================================================
            # ORACLE HEALTH MONITOR: Self-diagnostic and experimentation
            # ================================================================
            if self.oracle_health and self.metrics_capture:
                print(f"\n[ORACLE] Running generation {self.current_generation} health check...")
                try:
                    # Get metrics from console capture
                    console_metrics = self.metrics_capture.get_generation_summary()
                    
                    # Run health check
                    health_report = self.oracle_health.check_generation_health(
                        generation=self.current_generation,
                        console_metrics=console_metrics
                    )
                    
                    # Report status
                    if health_report.status == HealthStatus.HEALTHY:
                        print(f"[ORACLE] [OK] System healthy - {health_report.diagnosis}")
                    elif health_report.status == HealthStatus.WARNING:
                        print(f"[ORACLE] [WARN] {health_report.diagnosis}")
                        for rec in health_report.recommendations[:3]:
                            print(f"  - {rec}")
                    elif health_report.status == HealthStatus.CRITICAL:
                        print(f"[ORACLE] [X] CRITICAL: {health_report.diagnosis}")
                        for pathology in health_report.pathologies[:2]:
                            print(f"  - [{pathology['severity']}] {pathology['type']}")
                        
                        # Check for active experiment
                        active_exp = self.oracle_health.get_active_experiment()
                        
                        if active_exp:
                            # Experiment in progress - check if time to evaluate
                            if self.oracle_health.should_evaluate_experiment(
                                active_exp, self.current_generation
                            ):
                                result = self.oracle_health.evaluate_experiment(
                                    active_exp, self.current_generation
                                )
                                print(f"[ORACLE-EXP] Experiment {result['verdict']}: "
                                      f"{result['improvement']:+.1%} improvement")
                            else:
                                gens_remaining = (active_exp['started_generation'] + 
                                                  active_exp['duration_generations'] - 
                                                  self.current_generation)
                                print(f"[ORACLE-EXP] Experiment in progress ({gens_remaining} gens remaining)")
                        else:
                            # No experiment - start one if critical
                            experiment = self.oracle_health.select_experiment(
                                health_report.pathologies,
                                self.current_generation
                            )
                            if experiment:
                                self.oracle_health.start_experiment(experiment)
                    
                    # Print metrics summary
                    self.metrics_capture.print_summary()
                    
                    # Print reasoning diagnostics summary (for automated bug detection)
                    if get_reasoning_capture:
                        try:
                            reasoning_capture = get_reasoning_capture(self.current_generation)
                            if reasoning_capture:
                                reasoning_capture.print_diagnostics_report()
                        except Exception as e:
                            print(f"[REASONING-DIAG] Report failed: {e}")
                    
                    # Reset metrics for next generation
                    self.metrics_capture.reset(self.current_generation + 1)
                    
                    # Reset reasoning capture for next generation
                    if get_reasoning_capture:
                        try:
                            get_reasoning_capture(self.current_generation + 1)
                        except Exception:
                            pass
                    
                except Exception as e:
                    print(f"[ORACLE] Health check failed: {e}")
                    import traceback
                    traceback.print_exc()
            
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

        # Start keyboard listener: type F12 then Enter to request shutdown
        self._shutdown_listener_task = asyncio.create_task(self._shutdown_listener())
        
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

        # Enforce pycache rule before any gameplay
        try:
            self._enforce_no_pycache()
        except Exception as e:
            print(f"[ERROR] __pycache__ detected: {e}")
            await self._cleanup()
            return

        # Verify ARC API connectivity to prevent simulated/offline runs
        api_live = await self._verify_arc_api_live()
        if not api_live:
            await self._cleanup()
            return

        # Optional replay validation batch (no live gameplay)
        if self.replay_validation_batch:
            try:
                summary = await self.run_replay_validation_batch(self.replay_validation_limit)
                print(f"\n[SUMMARY] Replay validation batch: {summary['pointers_found']} pointers, {summary['missing']} missing, {summary['coverage_gap']} coverage gaps")
            finally:
                await self._cleanup()
            return
        
        try:
            # Initialize population
            if not await self.initialize_population():
                print("[?] Failed to initialize - exiting")
                return
            
            print("\n[>>] Starting autonomous evolution...")
            print("Press F12 + Enter (or Ctrl+C) for graceful shutdown\n")
            
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

            # Cancel keyboard listener if still running
            if self._shutdown_listener_task and not self._shutdown_listener_task.done():
                self._shutdown_listener_task.cancel()
    
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
            # Note: game_type is extracted from game_id prefix, agent_id from session_id
            cursor.execute("""
                SELECT 
                    gr.game_id,
                    SUBSTR(gr.game_id, 1, INSTR(gr.game_id, '-') - 1) as game_type,
                    gr.final_score,
                    gr.level_completions,
                    gr.total_actions,
                    gr.session_id,
                    gr.end_time
                FROM game_results gr
                WHERE gr.end_time >= datetime('now', '-3 hours')
                ORDER BY gr.end_time DESC
                LIMIT 25
            """)
            recent_games = cursor.fetchall()
            
            if recent_games:
                print(f"\nRecent Games (last 3 hours): {len(recent_games)}")
                
                # Calculate stats
                scores = [g['final_score'] or 0 for g in recent_games]
                levels = [g['level_completions'] or 0 for g in recent_games]
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
                    game_types[gt]['total_levels'] += g['level_completions'] or 0
                
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
                WHERE is_active = 1 AND discovered_at >= datetime('now', '-3 hours')
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
