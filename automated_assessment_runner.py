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
        
        # Get recent level wins
        cursor.execute("""
            SELECT COUNT(*) FROM winning_sequences
            WHERE timestamp >= datetime('now', '-24 hours')
        """)
        recent_wins = cursor.fetchone()[0]
        
        # Get total games played recently
        cursor.execute("""
            SELECT COUNT(*) FROM game_sessions
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
    
    def _assess_abstraction_usage(self) -> Dict[str, Any]:
        """Track abstraction engine usage and effectiveness."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
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
    
    def _assess_breakthrough_momentum(self) -> Dict[str, Any]:
        """Track breakthrough momentum detections."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
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
    
    def _assess_sequence_validation(self) -> Dict[str, Any]:
        """Monitor sequence validation success rate."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get recent sequence validation attempts
        cursor.execute("""
            SELECT COUNT(*) FROM winning_sequences
            WHERE is_active = 1 AND timestamp >= datetime('now', '-7 days')
        """)
        active_sequences = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'active_sequences': active_sequences,
            'status': 'healthy' if active_sequences > 100 else 'needs_review'
        }
    
    def _assess_prestige_distribution(self) -> Dict[str, Any]:
        """Check for prestige vampires and distribution health."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get prestige statistics
        cursor.execute("""
            SELECT AVG(prestige), MAX(prestige), MIN(prestige) FROM agents
            WHERE is_alive = 1
        """)
        result = cursor.fetchone()
        
        conn.close()
        
        if not result or result[0] is None:
            return {'status': 'no_data'}
        
        avg_prestige, max_prestige, min_prestige = result
        
        # Check for vampires (>10x median)
        has_vampire = max_prestige > (avg_prestige * 10)
        
        return {
            'avg_prestige': avg_prestige,
            'max_prestige': max_prestige,
            'min_prestige': min_prestige,
            'has_vampire': has_vampire,
            'status': 'vampire_detected' if has_vampire else 'healthy'
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
        
        # Check for subgoal-related logs
        cursor.execute("""
            SELECT COUNT(*) FROM database_logs
            WHERE message LIKE '%subgoal%' AND timestamp >= datetime('now', '-24 hours')
        """)
        subgoal_logs = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'subgoal_activations': subgoal_logs,
            'status': 'active' if subgoal_logs > 0 else 'inactive',
            'recommendation': 'Integrate subgoal activator' if subgoal_logs == 0 else 'Working well'
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
