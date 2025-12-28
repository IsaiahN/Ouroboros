"""
Oracle Health Monitor - Self-Diagnostic System for Autonomous Evolution
========================================================================

The Oracle's meta-cognitive layer that:
1. Monitors network health after each generation
2. Diagnoses root causes of stagnation
3. Runs autonomous experiments to escape stuck states
4. Learns which interventions work over time

This is the "immune system" that detects and responds to pathologies.

Rule 1: Disable pycache
Rule 2: All data in database
Rule 11: No unicode emojis
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """System health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"


class PathologyType(Enum):
    """Types of system dysfunction."""
    STAGNATION = "stagnation"           # No level progress for N generations
    BLIND_PLAY = "blind_play"           # Q1-Q5 not populating
    CODS_INACTIVE = "cods_inactive"     # CODS not suggesting actions
    SEQUENCES_UNUSED = "sequences_unused"  # Have sequences but not using them
    PREMATURE_TERMINATION = "premature_termination"  # Games ending too early
    NO_UNLOCKS = "no_unlocks"           # Primitives not unlocking
    ACTION_WASTE = "action_waste"       # High actions, low results


class ExperimentType(Enum):
    """Types of experiments Oracle can run."""
    UNLOCK_PRIMITIVE = "unlock_primitive"
    LOWER_CODS_THRESHOLD = "lower_cods_threshold"
    INCREASE_BUDGET = "increase_budget"
    FORCE_EXPLORATION = "force_exploration"
    BOOST_ESCAPE_ATTEMPTS = "boost_escape_attempts"


@dataclass
class HealthReport:
    """Health check result."""
    generation: int
    status: HealthStatus
    pathologies: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    diagnosis: str
    recommendations: List[str]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Experiment:
    """An Oracle experiment."""
    experiment_id: str
    experiment_type: ExperimentType
    hypothesis: str
    target: str  # What we're changing
    old_value: Any
    new_value: Any
    baseline_metrics: Dict[str, Any]
    duration_generations: int = 2
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_generation: int = 0


class OracleHealthMonitor:
    """
    The Oracle's self-diagnostic and experimentation system.
    
    Runs after each generation to:
    1. Check if the system is healthy
    2. Diagnose problems if not
    3. Run experiments to fix issues
    4. Learn what works over time
    """
    
    # Thresholds for health checks
    MIN_AVG_ACTIONS = 100  # Below this = premature termination
    MIN_LEVEL_COMPLETION_RATE = 0.05  # Below this for 3+ gens = stagnation
    MIN_CODS_ACTIVATION_RATE = 0.10  # Below this = CODS inactive
    MIN_SEQUENCE_UTILIZATION = 0.20  # Below this = sequences unused
    STAGNATION_GENERATIONS = 3  # Gens with no progress = stagnation
    
    # Experiment configurations
    EXPERIMENTS = {
        ExperimentType.UNLOCK_PRIMITIVE: {
            'description': 'Unlock a primitive that might help',
            'duration': 2,
            'rollback_capable': True,
        },
        ExperimentType.LOWER_CODS_THRESHOLD: {
            'description': 'Lower CODS confidence threshold for more suggestions',
            'duration': 2,
            'rollback_capable': True,
        },
        ExperimentType.INCREASE_BUDGET: {
            'description': 'Increase action budget for stuck games',
            'duration': 1,
            'rollback_capable': True,
        },
        ExperimentType.FORCE_EXPLORATION: {
            'description': 'Disable sequence replay temporarily',
            'duration': 1,
            'rollback_capable': True,
        },
        ExperimentType.BOOST_ESCAPE_ATTEMPTS: {
            'description': 'Increase escape attempts when stuck',
            'duration': 1,
            'rollback_capable': True,
        },
    }
    
    def __init__(
        self,
        db: Optional[DatabaseInterface] = None,
        db_path: str = "core_data.db"
    ):
        self.db = db or DatabaseInterface(db_path)
        self._initialize_schema()
        self._observation_cache = {}
        
    def _initialize_schema(self):
        """Create Oracle health monitoring tables."""
        
        # Oracle observations (health snapshots)
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS oracle_observations (
                observation_id TEXT PRIMARY KEY,
                generation INTEGER NOT NULL,
                health_status TEXT NOT NULL,
                metrics_json TEXT,
                pathologies_json TEXT,
                diagnosis TEXT,
                recommendations_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Oracle experiments
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS oracle_experiments (
                experiment_id TEXT PRIMARY KEY,
                experiment_type TEXT NOT NULL,
                hypothesis TEXT,
                target TEXT,
                old_value TEXT,
                new_value TEXT,
                baseline_metrics_json TEXT,
                final_metrics_json TEXT,
                improvement REAL,
                verdict TEXT,  -- 'success', 'failure', 'inconclusive'
                duration_generations INTEGER DEFAULT 2,
                started_generation INTEGER,
                completed_generation INTEGER,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                rolled_back BOOLEAN DEFAULT FALSE
            )
        """)
        
        # Oracle interventions (atomic changes)
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS oracle_interventions (
                intervention_id TEXT PRIMARY KEY,
                experiment_id TEXT,
                intervention_type TEXT NOT NULL,
                target TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                was_helpful BOOLEAN,
                improvement REAL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                rolled_back_at TIMESTAMP,
                FOREIGN KEY (experiment_id) REFERENCES oracle_experiments(experiment_id)
            )
        """)
        
        # Oracle meta-learning patterns
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS oracle_patterns (
                pattern_id TEXT PRIMARY KEY,
                pathology_type TEXT NOT NULL,
                intervention_type TEXT NOT NULL,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                total_improvement REAL DEFAULT 0.0,
                avg_improvement REAL DEFAULT 0.0,
                confidence REAL DEFAULT 0.5,
                last_used_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Index for fast lookups
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_oracle_obs_gen 
            ON oracle_observations(generation)
        """)
        
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_oracle_exp_active 
            ON oracle_experiments(verdict)
        """)
    
    # =========================================================================
    # HEALTH CHECKS
    # =========================================================================
    
    def check_generation_health(
        self,
        generation: int,
        console_metrics: Optional[Dict[str, Any]] = None
    ) -> HealthReport:
        """
        Run all health checks for a generation.
        
        Args:
            generation: Current generation number
            console_metrics: Metrics captured from console output
            
        Returns:
            HealthReport with status, pathologies, and recommendations
        """
        pathologies = []
        recommendations = []
        
        # Get metrics from database if not provided
        if console_metrics is None:
            console_metrics = self._get_metrics_from_db(generation)
        
        # Check 1: Learning progression (stagnation detection)
        stagnation = self._check_stagnation(generation)
        if stagnation:
            pathologies.append(stagnation)
            recommendations.extend(stagnation.get('recommendations', []))
        
        # Check 2: Game completion (premature termination)
        termination = self._check_premature_termination(generation, console_metrics)
        if termination:
            pathologies.append(termination)
            recommendations.extend(termination.get('recommendations', []))
        
        # Check 3: CODS activation
        cods_issue = self._check_cods_activation(generation)
        if cods_issue:
            pathologies.append(cods_issue)
            recommendations.extend(cods_issue.get('recommendations', []))
        
        # Check 4: Sequence utilization
        seq_issue = self._check_sequence_utilization(generation)
        if seq_issue:
            pathologies.append(seq_issue)
            recommendations.extend(seq_issue.get('recommendations', []))
        
        # Check 5: Primitive unlocks
        unlock_issue = self._check_primitive_unlocks(generation)
        if unlock_issue:
            pathologies.append(unlock_issue)
            recommendations.extend(unlock_issue.get('recommendations', []))
        
        # Determine overall status
        if any(p.get('severity') == 'critical' for p in pathologies):
            status = HealthStatus.CRITICAL
        elif pathologies:
            status = HealthStatus.WARNING
        else:
            status = HealthStatus.HEALTHY
        
        # Generate diagnosis
        diagnosis = self._generate_diagnosis(pathologies, console_metrics)
        
        # Create report
        report = HealthReport(
            generation=generation,
            status=status,
            pathologies=pathologies,
            metrics=console_metrics,
            diagnosis=diagnosis,
            recommendations=recommendations
        )
        
        # Store observation
        self._store_observation(report)
        
        return report
    
    def _check_stagnation(self, generation: int) -> Optional[Dict[str, Any]]:
        """Check if system is stagnating (no level progress)."""
        
        if generation < self.STAGNATION_GENERATIONS:
            return None
        
        # Get level completion counts for recent generations
        results = self.db.execute_query("""
            SELECT 
                g.generation,
                COUNT(*) as games,
                SUM(CASE WHEN g.level_completions > 0 THEN 1 ELSE 0 END) as with_progress,
                AVG(g.level_completions) as avg_levels,
                MAX(g.level_completions) as max_levels
            FROM game_results g
            WHERE g.generation >= ?
            GROUP BY g.generation
            ORDER BY g.generation
        """, (generation - self.STAGNATION_GENERATIONS,))
        
        if not results:
            return None
        
        # Check if any generation had level progress
        gens_with_progress = sum(1 for r in results if r['with_progress'] > 0)
        total_gens = len(results)
        
        # Also check for new level completions vs previous best
        new_completions = self.db.execute_query("""
            SELECT COUNT(DISTINCT game_id || '-' || CAST(level_number AS TEXT)) as unique_levels
            FROM winning_sequences
            WHERE created_at >= datetime('now', '-3 hours')
            AND is_active = 1
        """)
        new_level_count = new_completions[0]['unique_levels'] if new_completions else 0
        
        if gens_with_progress == 0 and new_level_count == 0:
            return {
                'type': PathologyType.STAGNATION.value,
                'severity': 'critical',
                'evidence': {
                    'generations_checked': total_gens,
                    'generations_with_progress': gens_with_progress,
                    'new_level_completions': new_level_count,
                    'recent_results': [dict(r) for r in results]
                },
                'diagnosis': f'No level progress for {total_gens} generations',
                'recommendations': [
                    'Consider unlocking stuck-related primitives',
                    'Lower CODS threshold to get more action suggestions',
                    'Increase escape attempts in stuck detection',
                    'Analyze stuck points for capability gaps'
                ]
            }
        
        return None
    
    def _check_premature_termination(
        self,
        generation: int,
        metrics: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check if games are ending too early."""
        
        avg_actions = metrics.get('avg_actions', 0)
        
        if avg_actions > 0 and avg_actions < self.MIN_AVG_ACTIONS:
            return {
                'type': PathologyType.PREMATURE_TERMINATION.value,
                'severity': 'critical',
                'evidence': {
                    'avg_actions': avg_actions,
                    'threshold': self.MIN_AVG_ACTIONS
                },
                'diagnosis': f'Games ending too early (avg {avg_actions:.0f} actions)',
                'recommendations': [
                    'Check win detection logic for false positives',
                    'Verify action budget is being applied',
                    'Check for infinite loop detection killing games early'
                ]
            }
        
        return None
    
    def _check_cods_activation(self, generation: int) -> Optional[Dict[str, Any]]:
        """Check if CODS is activating."""
        
        if generation < 5:
            return None  # Too early to check
        
        # Check composed_operators usage
        cods_usage = self.db.execute_query("""
            SELECT 
                COUNT(*) as total_operators,
                SUM(CASE WHEN times_used > 0 THEN 1 ELSE 0 END) as operators_used,
                SUM(times_used) as total_uses
            FROM composed_operators
            WHERE status != 'pruned'
        """)
        
        if not cods_usage or cods_usage[0]['total_operators'] == 0:
            return {
                'type': PathologyType.CODS_INACTIVE.value,
                'severity': 'high',
                'evidence': {
                    'operators_available': 0
                },
                'diagnosis': 'No CODS operators available',
                'recommendations': [
                    'Bootstrap operators from win patterns',
                    'Check if CODS engine is being initialized'
                ]
            }
        
        total_ops = cods_usage[0]['total_operators']
        ops_used = cods_usage[0]['operators_used'] or 0
        total_uses = cods_usage[0]['total_uses'] or 0
        
        usage_rate = ops_used / total_ops if total_ops > 0 else 0
        
        if usage_rate < self.MIN_CODS_ACTIVATION_RATE:
            return {
                'type': PathologyType.CODS_INACTIVE.value,
                'severity': 'high',
                'evidence': {
                    'operators_available': total_ops,
                    'operators_used': ops_used,
                    'total_uses': total_uses,
                    'usage_rate': usage_rate
                },
                'diagnosis': f'CODS operators rarely used ({usage_rate:.1%})',
                'recommendations': [
                    'Lower CODS confidence threshold',
                    'Check if operators match current game states',
                    'Verify CODS is being called in action selection'
                ]
            }
        
        return None
    
    def _check_sequence_utilization(self, generation: int) -> Optional[Dict[str, Any]]:
        """Check if winning sequences are being used."""
        
        # Count available sequences
        seq_count = self.db.execute_query("""
            SELECT COUNT(*) as count FROM winning_sequences WHERE is_active = 1
        """)
        available = seq_count[0]['count'] if seq_count else 0
        
        if available < 10:
            return None  # Not enough sequences to worry about
        
        # Check usage in recent games (via game_results or similar)
        # This is tricky since we don't have a sequence_used column
        # We'll check if games are reaching levels where sequences exist
        
        games_result = self.db.execute_query("""
            SELECT 
                COUNT(*) as total_games,
                SUM(CASE WHEN levels_completed > 0 THEN 1 ELSE 0 END) as with_progress
            FROM game_results
            WHERE generation = ?
        """, (generation,))
        
        if not games_result:
            return None
        
        total = games_result[0]['total_games'] or 0
        with_progress = games_result[0]['with_progress'] or 0
        
        if total == 0:
            return None
        
        utilization = with_progress / total
        
        if utilization < self.MIN_SEQUENCE_UTILIZATION and available > 20:
            return {
                'type': PathologyType.SEQUENCES_UNUSED.value,
                'severity': 'medium',
                'evidence': {
                    'sequences_available': available,
                    'games_with_progress': with_progress,
                    'total_games': total,
                    'utilization_rate': utilization
                },
                'diagnosis': f'{available} sequences available but only {utilization:.1%} games progressing',
                'recommendations': [
                    'Check sequence retrieval logic',
                    'Verify agents are entering 3-TRY mode',
                    'Check if game_id format matches between storage and retrieval'
                ]
            }
        
        return None
    
    def _check_primitive_unlocks(self, generation: int) -> Optional[Dict[str, Any]]:
        """Check if primitives are unlocking."""
        
        if generation < 10:
            return None  # Too early
        
        recent_unlocks = self.db.execute_query("""
            SELECT COUNT(*) as count 
            FROM primitive_status 
            WHERE status = 'unlocked'
            AND unlocked_at >= datetime('now', '-24 hours')
        """)
        
        unlock_count = recent_unlocks[0]['count'] if recent_unlocks else 0
        
        # Also check total unlocked vs locked
        status_counts = self.db.execute_query("""
            SELECT status, COUNT(*) as count 
            FROM primitive_status 
            GROUP BY status
        """)
        
        status_map = {r['status']: r['count'] for r in status_counts} if status_counts else {}
        locked = status_map.get('locked', 0)
        unlocked = status_map.get('unlocked', 0) + status_map.get('seed', 0)
        
        if unlock_count == 0 and locked > 5:
            return {
                'type': PathologyType.NO_UNLOCKS.value,
                'severity': 'medium',
                'evidence': {
                    'recent_unlocks': unlock_count,
                    'locked_primitives': locked,
                    'unlocked_primitives': unlocked
                },
                'diagnosis': f'No primitives unlocked recently ({locked} still locked)',
                'recommendations': [
                    'Run stuck point analysis for capability gaps',
                    'Check if unlock pressure is accumulating',
                    'Manually trigger experimental unlock'
                ]
            }
        
        return None
    
    def _get_metrics_from_db(self, generation: int) -> Dict[str, Any]:
        """Get metrics from database for a generation."""
        
        results = self.db.execute_query("""
            SELECT 
                COUNT(*) as games_played,
                AVG(final_score) as avg_score,
                AVG(levels_completed) as avg_levels,
                AVG(total_actions) as avg_actions,
                MAX(final_score) as max_score,
                MAX(levels_completed) as max_levels,
                SUM(CASE WHEN levels_completed > 0 THEN 1 ELSE 0 END) as level_completions
            FROM game_results
            WHERE generation = ?
        """, (generation,))
        
        if not results:
            return {
                'games_played': 0,
                'avg_score': 0,
                'avg_levels': 0,
                'avg_actions': 0,
                'max_score': 0,
                'max_levels': 0,
                'level_completions': 0
            }
        
        r = results[0]
        return {
            'games_played': r['games_played'] or 0,
            'avg_score': r['avg_score'] or 0,
            'avg_levels': r['avg_levels'] or 0,
            'avg_actions': r['avg_actions'] or 0,
            'max_score': r['max_score'] or 0,
            'max_levels': r['max_levels'] or 0,
            'level_completions': r['level_completions'] or 0
        }
    
    def _generate_diagnosis(
        self,
        pathologies: List[Dict[str, Any]],
        metrics: Dict[str, Any]
    ) -> str:
        """Generate human-readable diagnosis."""
        
        if not pathologies:
            return f"System healthy. Avg score: {metrics.get('avg_score', 0):.2f}, " \
                   f"Avg levels: {metrics.get('avg_levels', 0):.2f}"
        
        critical = [p for p in pathologies if p.get('severity') == 'critical']
        if critical:
            return f"CRITICAL: {critical[0]['diagnosis']}. " \
                   f"Games played: {metrics.get('games_played', 0)}"
        
        return f"WARNING: {pathologies[0]['diagnosis']}. " \
               f"Games played: {metrics.get('games_played', 0)}"
    
    def _store_observation(self, report: HealthReport):
        """Store health observation in database."""
        
        obs_id = str(uuid.uuid4())[:12]
        
        self.db.execute_query("""
            INSERT INTO oracle_observations 
            (observation_id, generation, health_status, metrics_json, 
             pathologies_json, diagnosis, recommendations_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            obs_id,
            report.generation,
            report.status.value,
            json.dumps(report.metrics),
            json.dumps(report.pathologies),
            report.diagnosis,
            json.dumps(report.recommendations)
        ))
    
    # =========================================================================
    # EXPERIMENTATION SYSTEM
    # =========================================================================
    
    def get_active_experiment(self) -> Optional[Dict[str, Any]]:
        """Get currently running experiment if any."""
        
        result = self.db.execute_query("""
            SELECT * FROM oracle_experiments
            WHERE verdict IS NULL
            ORDER BY started_at DESC
            LIMIT 1
        """)
        
        return dict(result[0]) if result else None
    
    def should_evaluate_experiment(
        self,
        experiment: Dict[str, Any],
        current_generation: int
    ) -> bool:
        """Check if experiment has run long enough to evaluate."""
        
        started_gen = experiment.get('started_generation', 0)
        duration = experiment.get('duration_generations', 2)
        
        return current_generation >= started_gen + duration
    
    def select_experiment(
        self,
        pathologies: List[Dict[str, Any]],
        current_generation: int
    ) -> Optional[Experiment]:
        """Select best experiment to run based on pathologies."""
        
        if not pathologies:
            return None
        
        # Check meta-learning patterns for what has worked before
        best_intervention = self._get_best_intervention_for_pathology(
            pathologies[0]['type']
        )
        
        if best_intervention and best_intervention['confidence'] > 0.6:
            # Use proven intervention
            return self._create_experiment_from_pattern(
                best_intervention,
                pathologies[0],
                current_generation
            )
        
        # Otherwise, select based on pathology type
        primary_pathology = pathologies[0]['type']
        
        if primary_pathology == PathologyType.STAGNATION.value:
            # Try unlocking a stuck-related primitive
            return self._create_unlock_experiment(current_generation)
        
        elif primary_pathology == PathologyType.CODS_INACTIVE.value:
            # Lower CODS threshold
            return self._create_threshold_experiment(current_generation)
        
        elif primary_pathology == PathologyType.PREMATURE_TERMINATION.value:
            # Increase budget
            return self._create_budget_experiment(current_generation)
        
        elif primary_pathology == PathologyType.NO_UNLOCKS.value:
            # Force an unlock
            return self._create_unlock_experiment(current_generation)
        
        return None
    
    def start_experiment(self, experiment: Experiment) -> bool:
        """Start an experiment."""
        
        try:
            # Store experiment
            self.db.execute_query("""
                INSERT INTO oracle_experiments
                (experiment_id, experiment_type, hypothesis, target, old_value, 
                 new_value, baseline_metrics_json, duration_generations, 
                 started_generation, started_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                experiment.experiment_id,
                experiment.experiment_type.value,
                experiment.hypothesis,
                experiment.target,
                json.dumps(experiment.old_value),
                json.dumps(experiment.new_value),
                json.dumps(experiment.baseline_metrics),
                experiment.duration_generations,
                experiment.started_generation,
                experiment.started_at
            ))
            
            # Apply the experiment change
            self._apply_experiment(experiment)
            
            print(f"[ORACLE-EXP] Started experiment {experiment.experiment_id[:8]}")
            print(f"  Type: {experiment.experiment_type.value}")
            print(f"  Hypothesis: {experiment.hypothesis}")
            print(f"  Duration: {experiment.duration_generations} generations")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start experiment: {e}")
            return False
    
    def evaluate_experiment(
        self,
        experiment: Dict[str, Any],
        current_generation: int
    ) -> Dict[str, Any]:
        """Evaluate experiment results."""
        
        exp_id = experiment['experiment_id']
        started_gen = experiment['started_generation']
        
        # Get baseline metrics
        baseline = json.loads(experiment['baseline_metrics_json'])
        
        # Get current metrics (average over experiment duration)
        current_metrics = self._get_average_metrics(
            started_gen,
            current_generation
        )
        
        # Calculate improvement
        baseline_score = baseline.get('avg_score', 0)
        current_score = current_metrics.get('avg_score', 0)
        
        baseline_levels = baseline.get('avg_levels', 0)
        current_levels = current_metrics.get('avg_levels', 0)
        
        # Weighted improvement (levels matter more than score)
        if baseline_score > 0:
            score_improvement = (current_score - baseline_score) / baseline_score
        else:
            score_improvement = current_score
        
        if baseline_levels > 0:
            level_improvement = (current_levels - baseline_levels) / baseline_levels
        else:
            level_improvement = current_levels
        
        improvement = 0.3 * score_improvement + 0.7 * level_improvement
        
        # Determine verdict
        if improvement > 0.05:
            verdict = 'success'
        elif improvement < -0.05:
            verdict = 'failure'
        else:
            verdict = 'inconclusive'
        
        # Update experiment record
        self.db.execute_query("""
            UPDATE oracle_experiments
            SET final_metrics_json = ?,
                improvement = ?,
                verdict = ?,
                completed_generation = ?,
                completed_at = ?
            WHERE experiment_id = ?
        """, (
            json.dumps(current_metrics),
            improvement,
            verdict,
            current_generation,
            datetime.now().isoformat(),
            exp_id
        ))
        
        # Handle rollback for failures
        if verdict == 'failure':
            self._rollback_experiment(experiment)
        
        # Update meta-learning patterns
        self._update_patterns(experiment, verdict, improvement)
        
        result = {
            'experiment_id': exp_id,
            'verdict': verdict,
            'improvement': improvement,
            'baseline_metrics': baseline,
            'final_metrics': current_metrics
        }
        
        print(f"[ORACLE-EXP] Experiment {exp_id[:8]} completed: {verdict}")
        print(f"  Improvement: {improvement:+.1%}")
        print(f"  Baseline score: {baseline_score:.2f} -> {current_score:.2f}")
        print(f"  Baseline levels: {baseline_levels:.2f} -> {current_levels:.2f}")
        
        return result
    
    def _create_unlock_experiment(self, generation: int) -> Optional[Experiment]:
        """Create experiment to unlock a primitive."""
        
        # Find locked primitives related to stuck patterns
        locked = self.db.execute_query("""
            SELECT primitive_name, description
            FROM primitive_status
            WHERE status = 'locked'
            ORDER BY RANDOM()
            LIMIT 1
        """)
        
        if not locked:
            return None
        
        primitive = locked[0]['primitive_name']
        
        return Experiment(
            experiment_id=str(uuid.uuid4())[:12],
            experiment_type=ExperimentType.UNLOCK_PRIMITIVE,
            hypothesis=f"Unlocking {primitive} will help agents escape stuck points",
            target=primitive,
            old_value={'status': 'locked'},
            new_value={'status': 'unlocked'},
            baseline_metrics=self._get_metrics_from_db(generation),
            duration_generations=2,
            started_generation=generation
        )
    
    def _create_threshold_experiment(self, generation: int) -> Experiment:
        """Create experiment to lower CODS threshold."""
        
        # Get current threshold from global_counters or default
        current = self.db.execute_query("""
            SELECT counter_value FROM global_counters
            WHERE counter_name = 'cods_confidence_threshold'
        """)
        
        old_threshold = float(current[0]['counter_value']) if current else 0.55
        new_threshold = max(0.25, old_threshold - 0.1)  # Lower by 0.1
        
        return Experiment(
            experiment_id=str(uuid.uuid4())[:12],
            experiment_type=ExperimentType.LOWER_CODS_THRESHOLD,
            hypothesis=f"Lowering CODS threshold from {old_threshold} to {new_threshold} will increase operator suggestions",
            target='cods_confidence_threshold',
            old_value=old_threshold,
            new_value=new_threshold,
            baseline_metrics=self._get_metrics_from_db(generation),
            duration_generations=2,
            started_generation=generation
        )
    
    def _create_budget_experiment(self, generation: int) -> Experiment:
        """Create experiment to increase action budget."""
        
        current = self.db.execute_query("""
            SELECT counter_value FROM global_counters
            WHERE counter_name = 'action_budget_multiplier'
        """)
        
        old_mult = float(current[0]['counter_value']) if current else 1.0
        new_mult = old_mult * 1.5  # Increase by 50%
        
        return Experiment(
            experiment_id=str(uuid.uuid4())[:12],
            experiment_type=ExperimentType.INCREASE_BUDGET,
            hypothesis=f"Increasing action budget by 50% will allow agents to escape stuck states",
            target='action_budget_multiplier',
            old_value=old_mult,
            new_value=new_mult,
            baseline_metrics=self._get_metrics_from_db(generation),
            duration_generations=1,
            started_generation=generation
        )
    
    def _apply_experiment(self, experiment: Experiment):
        """Apply experiment change to system."""
        
        exp_type = experiment.experiment_type
        
        if exp_type == ExperimentType.UNLOCK_PRIMITIVE:
            # Unlock the primitive
            self.db.execute_query("""
                UPDATE primitive_status
                SET status = 'unlocked',
                    unlocked_at = CURRENT_TIMESTAMP,
                    unlocked_by = 'oracle_experiment'
                WHERE primitive_name = ?
            """, (experiment.target,))
            print(f"  [APPLY] Unlocked primitive: {experiment.target}")
        
        elif exp_type == ExperimentType.LOWER_CODS_THRESHOLD:
            # Store new threshold
            self.db.execute_query("""
                INSERT OR REPLACE INTO global_counters 
                (counter_name, counter_value, description)
                VALUES (?, ?, ?)
            """, (
                'cods_confidence_threshold',
                experiment.new_value,
                f'Oracle experiment: lowered from {experiment.old_value}'
            ))
            print(f"  [APPLY] CODS threshold: {experiment.old_value} -> {experiment.new_value}")
        
        elif exp_type == ExperimentType.INCREASE_BUDGET:
            self.db.execute_query("""
                INSERT OR REPLACE INTO global_counters 
                (counter_name, counter_value, description)
                VALUES (?, ?, ?)
            """, (
                'action_budget_multiplier',
                experiment.new_value,
                f'Oracle experiment: increased from {experiment.old_value}'
            ))
            print(f"  [APPLY] Budget multiplier: {experiment.old_value} -> {experiment.new_value}")
        
        # Record intervention
        self.db.execute_query("""
            INSERT INTO oracle_interventions
            (intervention_id, experiment_id, intervention_type, target, old_value, new_value)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4())[:12],
            experiment.experiment_id,
            exp_type.value,
            experiment.target,
            json.dumps(experiment.old_value),
            json.dumps(experiment.new_value)
        ))
    
    def _rollback_experiment(self, experiment: Dict[str, Any]):
        """Rollback a failed experiment."""
        
        exp_type = experiment['experiment_type']
        target = experiment['target']
        old_value = json.loads(experiment['old_value'])
        
        if exp_type == ExperimentType.UNLOCK_PRIMITIVE.value:
            # Re-lock the primitive
            self.db.execute_query("""
                UPDATE primitive_status
                SET status = 'locked',
                    unlocked_at = NULL,
                    unlocked_by = NULL
                WHERE primitive_name = ?
            """, (target,))
            print(f"  [ROLLBACK] Re-locked primitive: {target}")
        
        elif exp_type == ExperimentType.LOWER_CODS_THRESHOLD.value:
            self.db.execute_query("""
                UPDATE global_counters
                SET counter_value = ?
                WHERE counter_name = ?
            """, (old_value, target))
            print(f"  [ROLLBACK] CODS threshold restored to {old_value}")
        
        elif exp_type == ExperimentType.INCREASE_BUDGET.value:
            self.db.execute_query("""
                UPDATE global_counters
                SET counter_value = ?
                WHERE counter_name = ?
            """, (old_value, target))
            print(f"  [ROLLBACK] Budget multiplier restored to {old_value}")
        
        # Mark experiment as rolled back
        self.db.execute_query("""
            UPDATE oracle_experiments
            SET rolled_back = TRUE
            WHERE experiment_id = ?
        """, (experiment['experiment_id'],))
        
        # Update intervention record
        self.db.execute_query("""
            UPDATE oracle_interventions
            SET rolled_back_at = CURRENT_TIMESTAMP
            WHERE experiment_id = ?
        """, (experiment['experiment_id'],))
    
    def _get_average_metrics(
        self,
        start_gen: int,
        end_gen: int
    ) -> Dict[str, Any]:
        """Get average metrics over generation range."""
        
        results = self.db.execute_query("""
            SELECT 
                AVG(final_score) as avg_score,
                AVG(levels_completed) as avg_levels,
                AVG(total_actions) as avg_actions,
                COUNT(*) as games_played,
                SUM(CASE WHEN levels_completed > 0 THEN 1 ELSE 0 END) as level_completions
            FROM game_results
            WHERE generation BETWEEN ? AND ?
        """, (start_gen, end_gen))
        
        if not results:
            return {'avg_score': 0, 'avg_levels': 0, 'avg_actions': 0}
        
        r = results[0]
        return {
            'avg_score': r['avg_score'] or 0,
            'avg_levels': r['avg_levels'] or 0,
            'avg_actions': r['avg_actions'] or 0,
            'games_played': r['games_played'] or 0,
            'level_completions': r['level_completions'] or 0
        }
    
    # =========================================================================
    # META-LEARNING
    # =========================================================================
    
    def _get_best_intervention_for_pathology(
        self,
        pathology_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get best known intervention for a pathology type."""
        
        result = self.db.execute_query("""
            SELECT 
                intervention_type,
                success_count,
                failure_count,
                avg_improvement,
                confidence
            FROM oracle_patterns
            WHERE pathology_type = ?
            ORDER BY confidence DESC, avg_improvement DESC
            LIMIT 1
        """, (pathology_type,))
        
        return dict(result[0]) if result else None
    
    def _update_patterns(
        self,
        experiment: Dict[str, Any],
        verdict: str,
        improvement: float
    ):
        """Update meta-learning patterns based on experiment result."""
        
        # Infer pathology type from experiment type
        exp_type = experiment['experiment_type']
        
        pathology_map = {
            ExperimentType.UNLOCK_PRIMITIVE.value: PathologyType.STAGNATION.value,
            ExperimentType.LOWER_CODS_THRESHOLD.value: PathologyType.CODS_INACTIVE.value,
            ExperimentType.INCREASE_BUDGET.value: PathologyType.PREMATURE_TERMINATION.value,
        }
        
        pathology_type = pathology_map.get(exp_type, PathologyType.STAGNATION.value)
        
        # Check if pattern exists
        existing = self.db.execute_query("""
            SELECT * FROM oracle_patterns
            WHERE pathology_type = ? AND intervention_type = ?
        """, (pathology_type, exp_type))
        
        if existing:
            # Update existing pattern
            pattern = dict(existing[0])
            
            if verdict == 'success':
                new_success = pattern['success_count'] + 1
                new_failure = pattern['failure_count']
            else:
                new_success = pattern['success_count']
                new_failure = pattern['failure_count'] + 1
            
            total = new_success + new_failure
            new_confidence = new_success / total if total > 0 else 0.5
            
            new_total_improvement = pattern['total_improvement'] + improvement
            new_avg_improvement = new_total_improvement / total
            
            self.db.execute_query("""
                UPDATE oracle_patterns
                SET success_count = ?,
                    failure_count = ?,
                    total_improvement = ?,
                    avg_improvement = ?,
                    confidence = ?,
                    last_used_at = CURRENT_TIMESTAMP
                WHERE pattern_id = ?
            """, (
                new_success, new_failure,
                new_total_improvement, new_avg_improvement,
                new_confidence, pattern['pattern_id']
            ))
        else:
            # Create new pattern
            success = 1 if verdict == 'success' else 0
            failure = 0 if verdict == 'success' else 1
            confidence = success / (success + failure)
            
            self.db.execute_query("""
                INSERT INTO oracle_patterns
                (pattern_id, pathology_type, intervention_type, 
                 success_count, failure_count, total_improvement, 
                 avg_improvement, confidence, last_used_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                str(uuid.uuid4())[:12],
                pathology_type,
                exp_type,
                success, failure,
                improvement, improvement,
                confidence
            ))
    
    def _create_experiment_from_pattern(
        self,
        pattern: Dict[str, Any],
        pathology: Dict[str, Any],
        generation: int
    ) -> Optional[Experiment]:
        """Create experiment based on learned pattern."""
        
        intervention_type = pattern['intervention_type']
        
        if intervention_type == ExperimentType.UNLOCK_PRIMITIVE.value:
            return self._create_unlock_experiment(generation)
        elif intervention_type == ExperimentType.LOWER_CODS_THRESHOLD.value:
            return self._create_threshold_experiment(generation)
        elif intervention_type == ExperimentType.INCREASE_BUDGET.value:
            return self._create_budget_experiment(generation)
        
        return None
    
    # =========================================================================
    # REPORTING
    # =========================================================================
    
    def get_health_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent health observations."""
        
        results = self.db.execute_query("""
            SELECT * FROM oracle_observations
            ORDER BY generation DESC
            LIMIT ?
        """, (limit,))
        
        return [dict(r) for r in results] if results else []
    
    def get_experiment_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent experiments."""
        
        results = self.db.execute_query("""
            SELECT * FROM oracle_experiments
            ORDER BY started_at DESC
            LIMIT ?
        """, (limit,))
        
        return [dict(r) for r in results] if results else []
    
    def get_pattern_summary(self) -> Dict[str, Any]:
        """Get summary of learned patterns."""
        
        results = self.db.execute_query("""
            SELECT 
                pathology_type,
                intervention_type,
                success_count,
                failure_count,
                avg_improvement,
                confidence
            FROM oracle_patterns
            ORDER BY confidence DESC
        """)
        
        if not results:
            return {'patterns': [], 'total': 0}
        
        return {
            'patterns': [dict(r) for r in results],
            'total': len(results)
        }
    
    def print_status(self):
        """Print current Oracle status."""
        
        print("\n" + "="*60)
        print("[ORACLE] Health Monitor Status")
        print("="*60)
        
        # Recent observations
        recent = self.get_health_history(3)
        if recent:
            print("\nRecent Health Checks:")
            for obs in recent:
                status = obs['health_status']
                gen = obs['generation']
                icon = "[OK]" if status == 'healthy' else "[WARN]" if status == 'warning' else "[X]"
                print(f"  {icon} Gen {gen}: {obs['diagnosis'][:60]}...")
        
        # Active experiment
        active = self.get_active_experiment()
        if active:
            print(f"\nActive Experiment:")
            print(f"  Type: {active['experiment_type']}")
            print(f"  Started: Gen {active['started_generation']}")
            print(f"  Hypothesis: {active['hypothesis'][:50]}...")
        else:
            print("\nNo active experiment")
        
        # Learned patterns
        patterns = self.get_pattern_summary()
        if patterns['total'] > 0:
            print(f"\nLearned Patterns: {patterns['total']}")
            for p in patterns['patterns'][:3]:
                success_rate = p['confidence'] * 100
                print(f"  - {p['pathology_type']} -> {p['intervention_type']}: "
                      f"{success_rate:.0f}% success, {p['avg_improvement']:+.1%} avg improvement")
        
        print("="*60 + "\n")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def run_health_check(generation: int, db_path: str = "core_data.db") -> HealthReport:
    """Run a health check for a generation."""
    monitor = OracleHealthMonitor(db_path=db_path)
    return monitor.check_generation_health(generation)


def get_oracle_status(db_path: str = "core_data.db"):
    """Print Oracle status."""
    monitor = OracleHealthMonitor(db_path=db_path)
    monitor.print_status()


if __name__ == "__main__":
    # Quick test
    import sys
    
    generation = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    
    monitor = OracleHealthMonitor()
    report = monitor.check_generation_health(generation)
    
    print(f"\nHealth Status: {report.status.value}")
    print(f"Diagnosis: {report.diagnosis}")
    
    if report.pathologies:
        print(f"\nPathologies Found: {len(report.pathologies)}")
        for p in report.pathologies:
            print(f"  - [{p['severity']}] {p['type']}: {p['diagnosis']}")
    
    if report.recommendations:
        print(f"\nRecommendations:")
        for r in report.recommendations:
            print(f"  - {r}")
    
    monitor.print_status()
