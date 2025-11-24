"""
Automated Assessment Runner (Other AI Suggestion #3)

PURPOSE:
Automatically run assess_results.py after every evolution batch to track:
- Abstraction engine metrics
- Level completion trends
- Breakthrough detection
- System health

PROBLEM SOLVED:
Currently: Manual assessment required to track system performance
New: Automatic metrics collection after each generation

INTEGRATION:
Called from autonomous_evolution_runner.py after each generation completes
"""

import logging
import subprocess
import sqlite3
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)


class AutomatedAssessmentRunner:
    """
    Runs automated system assessment after each evolution generation.
    """
    
    def __init__(self, db_path: str = "core_data.db"):
        self.db_path = db_path
        self.assessment_history: List[Dict[str, Any]] = []
    
    def run_post_generation_assessment(
        self,
        generation_number: int,
        games_played: int,
        agents_active: int
    ) -> Dict[str, Any]:
        """
        Run comprehensive assessment after generation completes.
        
        Returns:
            Dictionary with assessment results:
            - level_completion_rate
            - abstraction_usage_rate
            - breakthrough_count
            - sequence_validation_rate
            - prestige_distribution
            - recommendations
        """
        logger.info(f"[AutoAssessment] Running post-generation assessment for Gen {generation_number}")
        
        assessment = {
            'generation_number': generation_number,
            'timestamp': datetime.now().isoformat(),
            'games_played': games_played,
            'agents_active': agents_active
        }
        
        # Metric 1: Level completion rate
        assessment['level_completion'] = self._assess_level_completion()
        
        # Metric 2: Abstraction engine usage
        assessment['abstraction_usage'] = self._assess_abstraction_usage()
        
        # Metric 3: Breakthrough momentum detection
        assessment['breakthrough_momentum'] = self._assess_breakthrough_momentum()
        
        # Metric 4: Sequence validation rate
        assessment['sequence_validation'] = self._assess_sequence_validation()
        
        # Metric 5: Prestige distribution
        assessment['prestige_distribution'] = self._assess_prestige_distribution()
        
        # Metric 6: Multi-stage matching effectiveness
        assessment['matching_pipeline'] = self._assess_matching_pipeline()
        
        # Metric 7: Subgoal planning effectiveness
        assessment['subgoal_planning'] = self._assess_subgoal_planning()
        
        # Generate recommendations
        assessment['recommendations'] = self._generate_recommendations(assessment)
        
        # Store assessment in database
        self._store_assessment(assessment)
        
        # Store in memory
        self.assessment_history.append(assessment)
        
        logger.info(f"[AutoAssessment] Completed for Gen {generation_number}")
        return assessment
    
    def _assess_level_completion(self) -> Dict[str, Any]:
        """Measure level completion rate trends."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get recent level wins
            cursor.execute("""
                SELECT COUNT(*) FROM winning_sequences
                WHERE discovered_at >= datetime('now', '-24 hours')
            """)
            recent_wins = cursor.fetchone()[0]
            
            # Get total games played recently (use agent_arc_performance table which definitely exists)
            cursor.execute("""
                SELECT COUNT(*) FROM agent_arc_performance
                WHERE timestamp >= datetime('now', '-24 hours')
            """)
            recent_games = cursor.fetchone()[0]
            
            conn.close()
            
            rate = (recent_wins / recent_games * 100) if recent_games > 0 else 0
            
            return {
                'recent_wins': recent_wins,
                'recent_games': recent_games,
                'completion_rate': rate,
                'status': 'improving' if rate > 40 else 'needs_attention'
            }
        except sqlite3.OperationalError as e:
            conn.close()
            return {
                'recent_wins': 0,
                'recent_games': 0,
                'completion_rate': 0,
                'status': 'insufficient_data',
                'error': str(e)
            }
    
    def _assess_abstraction_usage(self) -> Dict[str, Any]:
        """Track abstraction engine usage and effectiveness."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if abstraction usage is logged
            cursor.execute("""
                SELECT COUNT(*) FROM database_logs
                WHERE message LIKE '%abstraction%' AND timestamp >= datetime('now', '-24 hours')
            """)
            abstraction_attempts = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'abstraction_attempts': abstraction_attempts,
                'status': 'active' if abstraction_attempts > 0 else 'inactive',
                'recommendation': 'Lower threshold to 0.6' if abstraction_attempts < 10 else 'Working well'
            }
        except sqlite3.OperationalError:
            conn.close()
            return {
                'abstraction_attempts': 0,
                'status': 'no_data',
                'recommendation': 'Database logs not available'
            }
    
    def _assess_breakthrough_momentum(self) -> Dict[str, Any]:
        """Track breakthrough momentum detections."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Count breakthrough momentum logs
            cursor.execute("""
                SELECT COUNT(*) FROM database_logs
                WHERE message LIKE '%BREAKTHROUGH MOMENTUM%' AND timestamp >= datetime('now', '-24 hours')
            """)
            breakthrough_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'breakthrough_detections': breakthrough_count,
                'status': 'excellent' if breakthrough_count > 50 else 'moderate' if breakthrough_count > 10 else 'low'
            }
        except sqlite3.OperationalError:
            conn.close()
            return {
                'breakthrough_detections': 0,
                'status': 'no_data'
            }
    
    def _assess_sequence_validation(self) -> Dict[str, Any]:
        """Monitor sequence validation success rate."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get recent sequence validation attempts
            cursor.execute("""
                SELECT COUNT(*) FROM winning_sequences
                WHERE is_active = 1 AND discovered_at >= datetime('now', '-7 days')
            """)
            active_sequences = cursor.fetchone()[0]
            
            # Get validation success rate
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
                FROM sequence_validation_attempts
                WHERE validation_timestamp >= datetime('now', '-7 days')
            """)
            validation_data = cursor.fetchone()
            total_validations = validation_data[0] if validation_data else 0
            successful_validations = validation_data[1] if validation_data else 0
            
            conn.close()
            
            success_rate = (successful_validations / total_validations * 100) if total_validations > 0 else 0
            
            return {
                'active_sequences': active_sequences,
                'total_validations': total_validations,
                'successful_validations': successful_validations,
                'validation_success_rate': success_rate,
                'status': 'healthy' if success_rate > 70 else 'needs_review'
            }
        except sqlite3.OperationalError as e:
            conn.close()
            return {
                'active_sequences': 0,
                'status': 'no_data',
                'error': str(e)
            }
    
    def _assess_prestige_distribution(self) -> Dict[str, Any]:
        """Check for prestige vampires and distribution health."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get prestige statistics (using discovery_prestige column)
            cursor.execute("""
                SELECT AVG(discovery_prestige), MAX(discovery_prestige), MIN(discovery_prestige) 
                FROM agents
                WHERE is_active = 1
            """)
            result = cursor.fetchone()
            
            conn.close()
            
            if not result or result[0] is None:
                return {'status': 'no_data', 'avg_prestige': 0, 'has_vampire': False}
            
            avg_prestige, max_prestige, min_prestige = result
            
            # Check for vampires (>10x average)
            has_vampire = max_prestige > (avg_prestige * 10) if avg_prestige > 0 else False
            
            return {
                'avg_prestige': avg_prestige,
                'max_prestige': max_prestige,
                'min_prestige': min_prestige,
                'has_vampire': has_vampire,
                'status': 'vampire_detected' if has_vampire else 'healthy'
            }
        except sqlite3.OperationalError as e:
            conn.close()
            return {
                'status': 'no_data',
                'avg_prestige': 0,
                'has_vampire': False,
                'error': str(e)
            }
    
    def _assess_matching_pipeline(self) -> Dict[str, Any]:
        """Evaluate multi-stage matching pipeline effectiveness."""
        # This would query logs or pipeline statistics
        # For now, return placeholder
        return {
            'status': 'needs_logging',
            'recommendation': 'Add pipeline statistics logging'
        }
    
    def _assess_subgoal_planning(self) -> Dict[str, Any]:
        """Evaluate subgoal planning activation and success."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check for subgoal-related logs
            cursor.execute("""
                SELECT COUNT(*) FROM database_logs
                WHERE message LIKE '%subgoal%' AND timestamp >= datetime('now', '-24 hours')
            """)
            subgoal_logs = cursor.fetchone()[0]
            
            # Check for actual subgoal plans in database
            cursor.execute("""
                SELECT COUNT(*) as total_plans,
                       SUM(CASE WHEN plan_status = 'completed' THEN 1 ELSE 0 END) as completed
                FROM subgoal_plans
                WHERE created_at >= datetime('now', '-24 hours')
            """)
            plan_data = cursor.fetchone()
            total_plans = plan_data[0] if plan_data else 0
            completed_plans = plan_data[1] if plan_data else 0
            
            conn.close()
            
            completion_rate = (completed_plans / total_plans * 100) if total_plans > 0 else 0
            
            return {
                'subgoal_activations': subgoal_logs,
                'total_plans': total_plans,
                'completed_plans': completed_plans,
                'completion_rate': completion_rate,
                'status': 'active' if total_plans > 0 else 'inactive',
                'recommendation': 'Integrate subgoal activator' if total_plans == 0 else 'Working well'
            }
        except sqlite3.OperationalError:
            conn.close()
            return {
                'subgoal_activations': 0,
                'total_plans': 0,
                'status': 'no_data',
                'recommendation': 'Subgoal tables not available'
            }
    
    def _generate_recommendations(self, assessment: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on assessment."""
        recommendations = []
        
        # Level completion
        if assessment['level_completion']['completion_rate'] < 40:
            recommendations.append("CRITICAL: Level completion rate below 40%. Review budget allocation and sequence matching.")
        
        # Abstraction usage
        if assessment['abstraction_usage']['status'] == 'inactive':
            recommendations.append("WARNING: Abstraction engine not active. Check configuration and lower threshold.")
        
        # Breakthrough momentum
        if assessment['breakthrough_momentum']['status'] == 'low':
            recommendations.append("INFO: Low breakthrough detections. Consider adjusting detection thresholds.")
        
        # Prestige vampires
        if assessment['prestige_distribution'].get('has_vampire'):
            recommendations.append("ACTION REQUIRED: Prestige vampire detected. Review prestige dampening system.")
        
        # Subgoal planning
        if assessment['subgoal_planning']['status'] == 'inactive':
            recommendations.append("INTEGRATION NEEDED: Subgoal planning not active. Integrate subgoal_planning_activator.py")
        
        if not recommendations:
            recommendations.append("EXCELLENT: All systems operating within normal parameters.")
        
        return recommendations
    
    def _store_assessment(self, assessment: Dict[str, Any]):
        """Store assessment results in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS automated_assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                generation_number INTEGER,
                timestamp TEXT,
                level_completion_rate REAL,
                breakthrough_count INTEGER,
                abstraction_active INTEGER,
                prestige_has_vampire INTEGER,
                recommendations TEXT,
                full_data TEXT
            )
        """)
        
        # Insert assessment
        cursor.execute("""
            INSERT INTO automated_assessments (
                generation_number, timestamp, level_completion_rate,
                breakthrough_count, abstraction_active, prestige_has_vampire,
                recommendations, full_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            assessment['generation_number'],
            assessment['timestamp'],
            assessment['level_completion'].get('completion_rate', 0),
            assessment['breakthrough_momentum'].get('breakthrough_detections', 0),
            1 if assessment['abstraction_usage']['status'] == 'active' else 0,
            1 if assessment['prestige_distribution'].get('has_vampire') else 0,
            '\n'.join(assessment['recommendations']),
            str(assessment)
        ))
        
        conn.commit()
        conn.close()
    
    def get_trend_analysis(self, last_n_generations: int = 10) -> Dict[str, Any]:
        """Analyze trends over last N generations."""
        if len(self.assessment_history) < 2:
            return {'status': 'insufficient_data'}
        
        recent = self.assessment_history[-last_n_generations:]
        
        # Track completion rate trend
        completion_rates = [a['level_completion'].get('completion_rate', 0) for a in recent]
        
        trend = {
            'completion_rate_trend': 'improving' if completion_rates[-1] > completion_rates[0] else 'declining',
            'avg_completion_rate': sum(completion_rates) / len(completion_rates),
            'best_generation': max(recent, key=lambda x: x['level_completion'].get('completion_rate', 0))['generation_number'],
            'total_breakthroughs': sum(a['breakthrough_momentum'].get('breakthrough_detections', 0) for a in recent)
        }
        
        return trend


# Module-level test function (Rule 5 compliant)
if __name__ == "__main__":
    # Quick verification
    runner = AutomatedAssessmentRunner()
    
    # Run test assessment
    assessment = runner.run_post_generation_assessment(
        generation_number=1,
        games_played=100,
        agents_active=50
    )
    
    print(f"Assessment complete:")
    print(f"  Level completion: {assessment['level_completion']['completion_rate']:.1f}%")
    print(f"  Breakthroughs: {assessment['breakthrough_momentum']['breakthrough_detections']}")
    print(f"  Recommendations: {len(assessment['recommendations'])}")
    
    for rec in assessment['recommendations']:
        print(f"    - {rec}")
