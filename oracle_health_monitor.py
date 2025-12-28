import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
Oracle Health Monitor - Self-Diagnostic System for Autonomous Evolution
========================================================================

The Oracle's meta-cognitive layer that:
1. Monitors network health after each generation
2. Diagnoses root causes of stagnation
3. Runs autonomous experiments to escape stuck states
4. Learns which interventions work over time

This is the "immune system" that detects and responds to pathologies.

ADDED: Reasoning log analysis for detecting observation->hypothesis loop bugs

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

# Reasoning log capture for automated bug detection
try:
    from console_metrics_capture import get_reasoning_diagnostics, get_reasoning_capture
    REASONING_CAPTURE_AVAILABLE = True
except ImportError:
    REASONING_CAPTURE_AVAILABLE = False
    get_reasoning_diagnostics = None
    get_reasoning_capture = None

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
        
        # Reasoning bugs table - for LLM investigation workflow
        # Stores detected reasoning system bugs for autonomous debugging
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS oracle_reasoning_bugs (
                bug_id TEXT PRIMARY KEY,
                generation INTEGER NOT NULL,
                bug_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT,
                evidence_json TEXT,
                affected_games_json TEXT,
                occurrence_count INTEGER DEFAULT 1,
                first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'open',
                fix_attempted BOOLEAN DEFAULT FALSE,
                fix_commit TEXT,
                fix_description TEXT,
                resolved_at TIMESTAMP,
                resolution_notes TEXT
            )
        """)
        
        # Index for reasoning bugs
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_reasoning_bugs_status
            ON oracle_reasoning_bugs(status, severity)
        """)
        
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_reasoning_bugs_type
            ON oracle_reasoning_bugs(bug_type, generation)
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
        
        # Check 6: Reasoning log diagnostics (NEW)
        # Detects bugs like "Q1 says no actions but frame_changes has 20+ items"
        reasoning_issues = self._check_reasoning_diagnostics(generation)
        if reasoning_issues:
            pathologies.extend(reasoning_issues)
            for issue in reasoning_issues:
                recommendations.extend(issue.get('recommendations', []))
        
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
    
    def _check_reasoning_diagnostics(self, generation: int) -> List[Dict[str, Any]]:
        """
        Check reasoning log capture for bugs in the observation->hypothesis loop.
        
        This is the Oracle's ability to automatically detect the bugs that used to
        require manual reasoning log analysis, such as:
        - Q1 says "no actions observed" but frame_changes has 20+ items
        - Working theory stuck as "425 Too Early" for 400+ frames
        - Hypotheses formed but never tested
        - Decision contributors showing no system influence
        
        Returns:
            List of pathology dicts for any reasoning bugs detected
        """
        issues = []
        
        if not REASONING_CAPTURE_AVAILABLE or not get_reasoning_diagnostics:
            logger.debug("Reasoning capture not available for diagnostics")
            return issues
        
        try:
            diagnostics = get_reasoning_diagnostics()
            if not diagnostics:
                return issues
            
            # Check for critical reasoning bugs
            critical_count = diagnostics.get('critical_count', 0)
            warning_count = diagnostics.get('warning_count', 0)
            by_type = diagnostics.get('by_type', {})
            
            # BUG TYPE 1: Q1 disconnected from frame changes
            if 'Q1_DISCONNECT' in by_type:
                q1_info = by_type['Q1_DISCONNECT']
                if q1_info['count'] > 10:  # More than 10 occurrences = systematic bug
                    issues.append({
                        'type': PathologyType.BLIND_PLAY.value,
                        'severity': 'critical',
                        'evidence': {
                            'bug_type': 'Q1_DISCONNECT',
                            'occurrences': q1_info['count'],
                            'affected_games': q1_info.get('affected_games', []),
                            'sample': q1_info.get('sample_description', '')
                        },
                        'diagnosis': (
                            f"Q1 observation system disconnected: {q1_info['count']} times "
                            f"Q1 reported no actions despite significant frame changes. "
                            f"The observation->hypothesis loop is broken."
                        ),
                        'recommendations': [
                            'Check _analyze_emergent_q1() is using delta_frame_changes',
                            'Verify _cache_delta_frame_changes() is being called before Q1',
                            'Review hypothesis formation from frame changes'
                        ]
                    })
            
            # BUG TYPE 2: Working theory stuck 
            if 'WORKING_THEORY_STUCK' in by_type:
                theory_info = by_type['WORKING_THEORY_STUCK']
                if theory_info['count'] > 5:
                    issues.append({
                        'type': 'theory_formation_failure',
                        'severity': 'warning',
                        'evidence': {
                            'bug_type': 'WORKING_THEORY_STUCK',
                            'occurrences': theory_info['count'],
                            'affected_games': theory_info.get('affected_games', [])
                        },
                        'diagnosis': (
                            f"Working theory not forming: {theory_info['count']} games have "
                            f"theory stuck as '425 Too Early' after 50+ actions"
                        ),
                        'recommendations': [
                            'Check _build_self_model_context() working_theory generation',
                            'Verify fallback theory formation from network hypotheses',
                            'Review GAP FIX 2 implementation'
                        ]
                    })
            
            # BUG TYPE 3: Hypotheses not used in decisions
            if 'HYPOTHESIS_UNUSED' in by_type:
                hyp_info = by_type['HYPOTHESIS_UNUSED']
                if hyp_info['count'] > 20:
                    issues.append({
                        'type': 'hypothesis_integration_failure',
                        'severity': 'warning',
                        'evidence': {
                            'bug_type': 'HYPOTHESIS_UNUSED',
                            'occurrences': hyp_info['count'],
                            'affected_games': hyp_info.get('affected_games', [])
                        },
                        'diagnosis': (
                            f"Hypotheses not influencing decisions: {hyp_info['count']} times "
                            f"hypotheses were available but DM-3 didn't activate"
                        ),
                        'recommendations': [
                            'Check DM-3 hypothesis-driven action selection',
                            'Verify _apply_hypothesis_driven_selection() is called',
                            'Review decision_contributors population'
                        ]
                    })
            
            # BUG TYPE 4: Emergent cognition dead
            if 'EMERGENT_COGNITION_DEAD' in by_type:
                ec_info = by_type['EMERGENT_COGNITION_DEAD']
                if ec_info['count'] > 5:
                    issues.append({
                        'type': PathologyType.BLIND_PLAY.value,
                        'severity': 'critical',
                        'evidence': {
                            'bug_type': 'EMERGENT_COGNITION_DEAD',
                            'occurrences': ec_info['count'],
                            'affected_games': ec_info.get('affected_games', [])
                        },
                        'diagnosis': (
                            f"Emergent cognition system not activating: {ec_info['count']} games "
                            f"have 4+/5 Q-fields empty/null after 20+ actions"
                        ),
                        'recommendations': [
                            'Check _analyze_emergent_q1() through _analyze_emergent_q5()',
                            'Verify sensation_context is being built',
                            'Review agent operating mode for sensation suppression'
                        ]
                    })
            
            # BUG TYPE 5: No self-model forming
            if 'NO_SELF_MODEL' in by_type:
                sm_info = by_type['NO_SELF_MODEL']
                if sm_info['count'] > 5:
                    issues.append({
                        'type': 'self_model_failure',
                        'severity': 'warning',
                        'evidence': {
                            'bug_type': 'NO_SELF_MODEL',
                            'occurrences': sm_info['count'],
                            'affected_games': sm_info.get('affected_games', [])
                        },
                        'diagnosis': (
                            f"Self-model not forming: {sm_info['count']} games have no "
                            f"controlled objects or goals identified after 100+ actions"
                        ),
                        'recommendations': [
                            'Check agent_self_model.py track_action_effect()',
                            'Verify objects_agent_controls is being populated',
                            'Review network control hypotheses fallback'
                        ]
                    })
            
            # Log summary if any issues found
            if issues:
                logger.warning(
                    f"[ORACLE] Reasoning diagnostics found {len(issues)} issues: "
                    f"{[i['type'] for i in issues]}"
                )
                # Save bugs to database for LLM investigation
                self._save_reasoning_bugs(generation, issues)
            
        except Exception as e:
            logger.debug(f"Reasoning diagnostics check failed: {e}")
        
        return issues
    
    def _save_reasoning_bugs(self, generation: int, issues: List[Dict[str, Any]]):
        """
        Save detected reasoning bugs to database for LLM investigation.
        
        Upserts bugs - if same bug type already exists and is open,
        increments occurrence count. Otherwise creates new record.
        """
        for issue in issues:
            bug_type = issue.get('evidence', {}).get('bug_type', issue.get('type', 'unknown'))
            severity = issue.get('severity', 'warning')
            description = issue.get('diagnosis', issue.get('description', ''))
            evidence = issue.get('evidence', {})
            affected_games = evidence.get('affected_games', [])
            
            # Check if this bug type is already open
            existing = self.db.execute_query("""
                SELECT bug_id, occurrence_count FROM oracle_reasoning_bugs
                WHERE bug_type = ? AND status = 'open'
                ORDER BY last_seen_at DESC LIMIT 1
            """, (bug_type,))
            
            if existing:
                # Update existing bug
                bug_id = existing[0]['bug_id']
                new_count = existing[0]['occurrence_count'] + evidence.get('occurrences', 1)
                self.db.execute_query("""
                    UPDATE oracle_reasoning_bugs
                    SET occurrence_count = ?,
                        last_seen_at = CURRENT_TIMESTAMP,
                        evidence_json = ?,
                        affected_games_json = ?
                    WHERE bug_id = ?
                """, (
                    new_count,
                    json.dumps(evidence),
                    json.dumps(affected_games),
                    bug_id
                ))
            else:
                # Create new bug record
                bug_id = str(uuid.uuid4())[:12]
                self.db.execute_query("""
                    INSERT INTO oracle_reasoning_bugs
                    (bug_id, generation, bug_type, severity, description,
                     evidence_json, affected_games_json, occurrence_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    bug_id,
                    generation,
                    bug_type,
                    severity,
                    description,
                    json.dumps(evidence),
                    json.dumps(affected_games),
                    evidence.get('occurrences', 1)
                ))
    
    # =========================================================================
    # LLM INVESTIGATION WORKFLOW
    # =========================================================================
    
    def get_open_bugs(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all open reasoning bugs for LLM investigation.
        
        Args:
            severity: Filter by severity ('critical', 'warning', or None for all)
            
        Returns:
            List of bug records with evidence and fix suggestions
        """
        if severity:
            results = self.db.execute_query("""
                SELECT * FROM oracle_reasoning_bugs
                WHERE status = 'open' AND severity = ?
                ORDER BY 
                    CASE severity WHEN 'critical' THEN 1 WHEN 'warning' THEN 2 ELSE 3 END,
                    occurrence_count DESC
            """, (severity,))
        else:
            results = self.db.execute_query("""
                SELECT * FROM oracle_reasoning_bugs
                WHERE status = 'open'
                ORDER BY 
                    CASE severity WHEN 'critical' THEN 1 WHEN 'warning' THEN 2 ELSE 3 END,
                    occurrence_count DESC
            """)
        
        bugs = []
        for r in results or []:
            bug = dict(r)
            bug['evidence'] = json.loads(bug.get('evidence_json', '{}'))
            bug['affected_games'] = json.loads(bug.get('affected_games_json', '[]'))
            bug['fix_suggestions'] = self._get_fix_suggestions(bug['bug_type'])
            bugs.append(bug)
        
        return bugs
    
    def get_bug_investigation_prompt(self, bug_id: Optional[str] = None) -> str:
        """
        Generate an LLM-ready investigation prompt for reasoning bugs.
        
        This is what the LLM (Claude) uses to understand and fix bugs.
        
        Args:
            bug_id: Specific bug to investigate, or None for highest priority
            
        Returns:
            Formatted investigation prompt for the LLM
        """
        if bug_id:
            bugs = self.db.execute_query("""
                SELECT * FROM oracle_reasoning_bugs WHERE bug_id = ?
            """, (bug_id,))
        else:
            bugs = self.db.execute_query("""
                SELECT * FROM oracle_reasoning_bugs
                WHERE status = 'open'
                ORDER BY 
                    CASE severity WHEN 'critical' THEN 1 WHEN 'warning' THEN 2 ELSE 3 END,
                    occurrence_count DESC
                LIMIT 1
            """)
        
        if not bugs:
            return "No open reasoning bugs to investigate."
        
        bug = dict(bugs[0])
        evidence = json.loads(bug.get('evidence_json', '{}'))
        affected_games = json.loads(bug.get('affected_games_json', '[]'))
        fix_suggestions = self._get_fix_suggestions(bug['bug_type'])
        
        prompt = f"""
# REASONING BUG INVESTIGATION

## Bug Details
- **Bug ID**: {bug['bug_id']}
- **Type**: {bug['bug_type']}
- **Severity**: {bug['severity'].upper()}
- **First Seen**: Generation {bug['generation']}
- **Occurrences**: {bug['occurrence_count']}

## Description
{bug['description']}

## Evidence
```json
{json.dumps(evidence, indent=2)}
```

## Affected Games
{', '.join(affected_games[:10]) if affected_games else 'Not tracked'}

## Fix Suggestions
{chr(10).join(f'- {s}' for s in fix_suggestions)}

## Investigation Steps
1. Search codebase for the relevant functions mentioned in fix suggestions
2. Check if the data flow is correct (data exists but not used vs data not collected)
3. Add logging to verify hypothesis
4. Implement fix
5. Mark bug as fixed with: oracle.mark_bug_fixed('{bug['bug_id']}', 'description of fix')

## Files to Check
{self._get_files_to_check(bug['bug_type'])}
"""
        return prompt
    
    def _get_fix_suggestions(self, bug_type: str) -> List[str]:
        """Get fix suggestions based on bug type."""
        suggestions = {
            'Q1_DISCONNECT': [
                "Check _analyze_emergent_q1() is using _last_delta_frame_changes",
                "Verify _cache_delta_frame_changes() called before Q1 analysis",
                "Ensure hypothesis formation from frame changes is triggered",
                "Check if Q1 text template uses frame change count"
            ],
            'WORKING_THEORY_STUCK': [
                "Check _build_self_model_context() working_theory generation",
                "Verify GAP FIX 2 fallback theory formation",
                "Check network hypothesis query for theory building",
                "Ensure score-based theory formation triggers"
            ],
            'HYPOTHESIS_UNUSED': [
                "Check DM-3 _apply_hypothesis_driven_selection() is called",
                "Verify hypotheses are passed to action selection",
                "Check decision_contributors population",
                "Ensure hypothesis action mapping works"
            ],
            'EMERGENT_COGNITION_DEAD': [
                "Check _analyze_emergent_q1() through _analyze_emergent_q5()",
                "Verify sensation_context is being built",
                "Check agent operating mode for sensation suppression",
                "Ensure sensation engine is initialized"
            ],
            'NO_SELF_MODEL': [
                "Check agent_self_model.py track_action_effect()",
                "Verify objects_agent_controls population",
                "Check network control hypotheses fallback",
                "Ensure ACTION6 selection tracking works"
            ]
        }
        return suggestions.get(bug_type, ["No specific suggestions - investigate manually"])
    
    def _get_files_to_check(self, bug_type: str) -> str:
        """Get relevant files for bug type."""
        files = {
            'Q1_DISCONNECT': """
- core_gameplay.py: _analyze_emergent_q1(), _cache_delta_frame_changes()
- core_gameplay.py: Lines around 7680-7740 (Q1 analysis)
- agent_self_model.py: hypothesis formation methods""",
            'WORKING_THEORY_STUCK': """
- core_gameplay.py: _build_self_model_context() 
- core_gameplay.py: GAP FIX 2 section (around line 8173-8210)
- core_gameplay.py: _format_reasoning_for_api()""",
            'HYPOTHESIS_UNUSED': """
- core_gameplay.py: _apply_hypothesis_driven_selection()
- core_gameplay.py: DM-3 section (around line 4390-4422)
- core_gameplay.py: _select_action_with_dm_integration()""",
            'EMERGENT_COGNITION_DEAD': """
- core_gameplay.py: _analyze_emergent_q1() through _analyze_emergent_q5()
- sensation_engine.py: SensationEngine class
- core_gameplay.py: _analyze_sensation_context()""",
            'NO_SELF_MODEL': """
- agent_self_model.py: track_action_effect(), get_controlled_objects()
- core_gameplay.py: _build_self_model_context()
- core_gameplay.py: GAP FIX 1 section (bootstrap from network)"""
        }
        return files.get(bug_type, "- core_gameplay.py: Search for bug_type keyword")
    
    def mark_bug_fixed(
        self,
        bug_id: str,
        fix_description: str,
        fix_commit: Optional[str] = None
    ):
        """
        Mark a bug as fixed after LLM implements the fix.
        
        Args:
            bug_id: The bug ID to mark as fixed
            fix_description: Description of what was fixed
            fix_commit: Optional git commit hash
        """
        self.db.execute_query("""
            UPDATE oracle_reasoning_bugs
            SET status = 'fixed',
                fix_attempted = TRUE,
                fix_description = ?,
                fix_commit = ?,
                resolved_at = CURRENT_TIMESTAMP
            WHERE bug_id = ?
        """, (fix_description, fix_commit, bug_id))
        
        logger.info(f"[ORACLE] Bug {bug_id} marked as fixed: {fix_description}")
    
    def mark_bug_wont_fix(self, bug_id: str, reason: str):
        """Mark a bug as won't fix with reason."""
        self.db.execute_query("""
            UPDATE oracle_reasoning_bugs
            SET status = 'wont_fix',
                resolution_notes = ?,
                resolved_at = CURRENT_TIMESTAMP
            WHERE bug_id = ?
        """, (reason, bug_id))
    
    def get_bug_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get history of all bugs (open and resolved)."""
        results = self.db.execute_query("""
            SELECT * FROM oracle_reasoning_bugs
            ORDER BY 
                CASE status WHEN 'open' THEN 0 ELSE 1 END,
                last_seen_at DESC
            LIMIT ?
        """, (limit,))
        
        return [dict(r) for r in results] if results else []
    
    def print_bug_report(self):
        """Print a summary of all reasoning bugs for console."""
        open_bugs = self.get_open_bugs()
        
        print("\n" + "=" * 60)
        print("ORACLE REASONING BUG REPORT")
        print("=" * 60)
        
        if not open_bugs:
            print("[OK] No open reasoning bugs")
            print("=" * 60)
            return
        
        critical = [b for b in open_bugs if b['severity'] == 'critical']
        warnings = [b for b in open_bugs if b['severity'] == 'warning']
        
        print(f"Open Bugs: {len(open_bugs)} ({len(critical)} critical, {len(warnings)} warnings)")
        print("-" * 60)
        
        for bug in open_bugs:
            severity_tag = "[CRIT]" if bug['severity'] == 'critical' else "[WARN]"
            print(f"\n{severity_tag} {bug['bug_type']} (ID: {bug['bug_id']})")
            print(f"    Occurrences: {bug['occurrence_count']}")
            print(f"    First seen: Gen {bug['generation']}")
            print(f"    {bug['description'][:80]}...")
            if bug['fix_suggestions']:
                print(f"    Fix: {bug['fix_suggestions'][0]}")
        
        print("\n" + "=" * 60)
        print("Run: oracle.get_bug_investigation_prompt() for detailed investigation")
        print("=" * 60)
    
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
