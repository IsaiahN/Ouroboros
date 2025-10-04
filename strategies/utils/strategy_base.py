"""
Base class providing common functionality for all strategies.
"""
from disable_pycache import *

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import hashlib

logger = logging.getLogger(__name__)

class StrategyBase:
    """Base class providing common functionality for all strategies"""

    def __init__(self, db_interface):
        self.db = db_interface
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def save_performance_metrics(self, metrics: dict):
        """Save performance data to database"""
        try:
            # Add timestamp and strategy info
            metrics.update({
                'strategy_name': self.__class__.__name__,
                'timestamp': datetime.now().isoformat()
            })

            # Save to appropriate table based on metrics type
            if 'heuristic_name' in metrics:
                self._save_heuristic_performance(metrics)
            elif 'pattern_signature' in metrics:
                self._save_pattern_data(metrics)
            elif 'metric_name' in metrics:
                self._save_success_metric(metrics)
            else:
                self.logger.debug(f"Saved metrics: {metrics}")

        except Exception as e:
            self.logger.error(f"Failed to save performance metrics: {e}")

    def _save_heuristic_performance(self, metrics: dict):
        """Save heuristic performance to database"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()

                # Check if heuristic already exists
                cursor.execute("""
                    SELECT usage_count, success_rate, avg_score_impact
                    FROM heuristic_performance
                    WHERE heuristic_name = ?
                """, (metrics['heuristic_name'],))

                existing = cursor.fetchone()

                if existing:
                    # Update existing record
                    old_count, old_success_rate, old_avg_impact = existing
                    new_count = old_count + 1

                    # Calculate new averages
                    new_success_rate = ((old_success_rate * old_count) + metrics.get('success_rate', 0.0)) / new_count
                    new_avg_impact = ((old_avg_impact * old_count) + metrics.get('avg_score_impact', 0.0)) / new_count

                    cursor.execute("""
                        UPDATE heuristic_performance
                        SET usage_count = ?, success_rate = ?, avg_score_impact = ?, last_used = ?
                        WHERE heuristic_name = ?
                    """, (new_count, new_success_rate, new_avg_impact, datetime.now(), metrics['heuristic_name']))
                else:
                    # Insert new record
                    cursor.execute("""
                        INSERT INTO heuristic_performance
                        (heuristic_name, condition_met, action_taken, success_rate,
                         avg_score_impact, usage_count, last_used)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        metrics['heuristic_name'],
                        json.dumps(metrics.get('condition_met', {})),
                        metrics.get('action_taken', ''),
                        metrics.get('success_rate', 0.0),
                        metrics.get('avg_score_impact', 0.0),
                        1,
                        datetime.now()
                    ))

                conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to save heuristic performance: {e}")

    def _save_pattern_data(self, metrics: dict):
        """Save pattern data to database"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO successful_patterns
                    (pattern_signature, action_sequence, success_context, win_rate,
                     avg_score_improvement, pattern_length, recency_weight, last_successful)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metrics['pattern_signature'],
                    json.dumps(metrics.get('action_sequence', [])),
                    json.dumps(metrics.get('success_context', {})),
                    metrics.get('win_rate', 0.0),
                    metrics.get('avg_score_improvement', 0.0),
                    metrics.get('pattern_length', 0),
                    metrics.get('recency_weight', 1.0),
                    datetime.now()
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to save pattern data: {e}")

    def _save_success_metric(self, metrics: dict):
        """Save success metric to database"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO success_metrics
                    (strategy_name, game_type, metric_name, metric_value, measurement_context)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    metrics.get('strategy_name', self.__class__.__name__),
                    metrics.get('game_type', 'unknown'),
                    metrics['metric_name'],
                    metrics['metric_value'],
                    json.dumps(metrics.get('measurement_context', {}))
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to save success metric: {e}")

    def calculate_confidence_score(self, factors: dict) -> float:
        """Calculate confidence in strategy decisions"""
        try:
            # Simple confidence calculation based on multiple factors
            confidence = 0.5  # Base confidence

            # Increase confidence based on positive factors
            if factors.get('score_trend') == 'increasing':
                confidence += 0.2
            if factors.get('recent_success', False):
                confidence += 0.15
            if factors.get('familiar_pattern', False):
                confidence += 0.1
            if factors.get('pattern_match_quality', 0) > 0.7:
                confidence += 0.1

            # Decrease confidence based on negative factors
            if factors.get('score_trend') == 'decreasing':
                confidence -= 0.3
            if factors.get('emergency_detected', False):
                confidence -= 0.2
            if factors.get('unknown_game_type', False):
                confidence -= 0.1

            # Clamp between 0 and 1
            return max(0.0, min(1.0, confidence))

        except Exception as e:
            self.logger.error(f"Error calculating confidence: {e}")
            return 0.5  # Return neutral confidence on error

    def get_historical_patterns(self, pattern_signature: str, limit: int = 5) -> List[dict]:
        """Get historical patterns similar to current signature"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT pattern_signature, action_sequence, success_context,
                           win_rate, avg_score_improvement, recency_weight
                    FROM successful_patterns
                    WHERE pattern_signature = ? OR pattern_signature LIKE ?
                    ORDER BY win_rate DESC, last_successful DESC
                    LIMIT ?
                """, (pattern_signature, f"{pattern_signature[:8]}%", limit))

                results = []
                for row in cursor.fetchall():
                    results.append({
                        'pattern_signature': row[0],
                        'action_sequence': json.loads(row[1]),
                        'success_context': json.loads(row[2]),
                        'win_rate': row[3],
                        'avg_score_improvement': row[4],
                        'recency_weight': row[5]
                    })
                return results

        except Exception as e:
            self.logger.error(f"Error getting historical patterns: {e}")
            return []

    def save_game_state_analysis(self, analysis_data: dict):
        """Save game state analysis results"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO game_state_analysis
                    (game_id, session_id, action_number, score_momentum, risk_level,
                     opportunity_zones, emergency_detected, analysis_context, recommended_actions)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    analysis_data.get('game_id', ''),
                    analysis_data.get('session_id', ''),
                    analysis_data.get('action_number', 0),
                    analysis_data.get('score_momentum', 'stable'),
                    analysis_data.get('risk_level', 'medium'),
                    json.dumps(analysis_data.get('opportunity_zones', [])),
                    analysis_data.get('emergency_detected', False),
                    json.dumps(analysis_data.get('analysis_context', {})),
                    json.dumps(analysis_data.get('recommended_actions', []))
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to save game state analysis: {e}")

    def save_emergency_recovery_event(self, event_data: dict):
        """Save emergency recovery event"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO emergency_recovery_events
                    (game_id, session_id, trigger_condition, recovery_action_taken,
                     pre_recovery_score, post_recovery_score, recovery_successful)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    event_data.get('game_id', ''),
                    event_data.get('session_id', ''),
                    event_data.get('trigger_condition', ''),
                    event_data.get('recovery_action_taken', ''),
                    event_data.get('pre_recovery_score', 0.0),
                    event_data.get('post_recovery_score', 0.0),
                    event_data.get('recovery_successful', False)
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to save emergency recovery event: {e}")

    def get_game_type_from_id(self, game_id: str) -> str:
        """Extract game type from game ID"""
        try:
            # Simple game type detection from ID patterns
            game_id_lower = game_id.lower()

            if 'puzzle' in game_id_lower or 'pz' in game_id_lower:
                return 'puzzle'
            elif 'action' in game_id_lower or 'act' in game_id_lower:
                return 'action'
            elif 'strategy' in game_id_lower or 'str' in game_id_lower:
                return 'strategy'
            elif any(prefix in game_id_lower for prefix in ['vc', 'vs', 'vm']):
                return 'visual_challenge'
            else:
                return 'unknown'
        except:
            return 'unknown'

    def create_coordinate_strategy(self, strategy_type: str, context_data: dict) -> dict:
        """Create coordinate strategy for ACTION6"""
        try:
            if strategy_type == 'center':
                return {'x': 32, 'y': 32}
            elif strategy_type == 'exploration':
                import random
                return {
                    'x': 32 + random.randint(-16, 16),
                    'y': 32 + random.randint(-16, 16)
                }
            elif strategy_type == 'corner':
                corners = [{'x': 16, 'y': 16}, {'x': 48, 'y': 48}, {'x': 16, 'y': 48}, {'x': 48, 'y': 16}]
                import random
                return random.choice(corners)
            elif strategy_type == 'edge':
                import random
                return {
                    'x': random.choice([8, 24, 40, 56]),
                    'y': random.choice([8, 24, 40, 56])
                }
            else:
                return {'x': 32, 'y': 32}  # Default to center
        except:
            return {'x': 32, 'y': 32}