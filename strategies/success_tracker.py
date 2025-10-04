"""
SuccessTracker - Measures what actually works.
Implements Prompt 9 from Claude-Code Ready Prompts.
"""
from disable_pycache import *

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import statistics

from .utils.strategy_base import StrategyBase
from .utils.game_context import GameContext

logger = logging.getLogger(__name__)

class SuccessTracker(StrategyBase):
    """Tracks success metrics and measures what strategies actually work"""

    def __init__(self, db_interface):
        super().__init__(db_interface)
        self.metric_cache = {}
        self.performance_trends = {}
        self.tracked_metrics = [
            'win_rate',
            'average_score',
            'actions_efficiency',
            'strategy_effectiveness',
            'learning_curve',
            'adaptation_speed',
            'emergency_recovery_rate',
            'pattern_match_success'
        ]

    async def track_strategy_performance(self, strategy_name: str, game_type: str,
                                       game_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track performance of a specific strategy.

        Args:
            strategy_name: Name of the strategy used
            game_type: Type of game played
            game_results: Results from the completed game

        Returns:
            Performance tracking results
        """
        try:
            self.logger.debug(f"Tracking performance for {strategy_name} on {game_type}")

            # Extract key metrics from game results
            metrics = self._extract_metrics(game_results)

            # Store individual metrics
            for metric_name, metric_value in metrics.items():
                await self._store_metric(strategy_name, game_type, metric_name, metric_value, game_results)

            # Calculate running averages and trends
            performance_summary = await self._calculate_performance_summary(strategy_name, game_type)

            # Update cache
            cache_key = f"{strategy_name}:{game_type}"
            self.metric_cache[cache_key] = {
                'last_updated': datetime.now(),
                'performance_summary': performance_summary,
                'latest_metrics': metrics
            }

            win_rate_data = performance_summary.get('win_rate', {'average': 0.0})
            win_rate = win_rate_data.get('average', 0.0) if isinstance(win_rate_data, dict) else win_rate_data
            self.logger.info(f"Tracked performance: {strategy_name} - win_rate: {win_rate:.2f}")

            return {
                'strategy_name': strategy_name,
                'game_type': game_type,
                'metrics_tracked': metrics,
                'performance_summary': performance_summary,
                'tracking_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error tracking strategy performance: {e}")
            return {'error': str(e)}

    async def get_best_performing_strategies(self, game_type: str = None,
                                           metric: str = 'win_rate',
                                           limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get best performing strategies based on specified metric.

        Args:
            game_type: Optional game type filter
            metric: Metric to rank by (default: win_rate)
            limit: Maximum number of strategies to return

        Returns:
            List of top performing strategies
        """
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()

                # Build query based on filters
                base_query = """
                    SELECT strategy_name, game_type, metric_name, AVG(metric_value) as avg_value,
                           COUNT(*) as sample_size, MAX(timestamp) as latest_measurement
                    FROM success_metrics
                    WHERE metric_name = ?
                """
                params = [metric]

                if game_type:
                    base_query += " AND game_type = ?"
                    params.append(game_type)

                base_query += """
                    GROUP BY strategy_name, game_type
                    HAVING sample_size >= 3
                    ORDER BY avg_value DESC
                    LIMIT ?
                """
                params.append(limit)

                cursor.execute(base_query, params)
                results = cursor.fetchall()

                top_strategies = []
                for row in results:
                    strategy_info = {
                        'strategy_name': row[0],
                        'game_type': row[1],
                        'metric_name': row[2],
                        'avg_value': row[3],
                        'sample_size': row[4],
                        'latest_measurement': row[5],
                        'confidence': min(1.0, row[4] / 10.0)  # Confidence based on sample size
                    }

                    # Get additional metrics for this strategy
                    additional_metrics = await self._get_additional_metrics(row[0], row[1])
                    strategy_info.update(additional_metrics)

                    top_strategies.append(strategy_info)

            return top_strategies

        except Exception as e:
            self.logger.error(f"Error getting best performing strategies: {e}")
            return []

    async def analyze_learning_curve(self, strategy_name: str, game_type: str = None,
                                   days: int = 30) -> Dict[str, Any]:
        """
        Analyze learning curve and adaptation speed.

        Args:
            strategy_name: Strategy to analyze
            game_type: Optional game type filter
            days: Number of days to analyze

        Returns:
            Learning curve analysis
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            with self.db._get_connection() as conn:
                cursor = conn.cursor()

                # Get time-series data
                query = """
                    SELECT DATE(timestamp) as date, metric_name, AVG(metric_value) as daily_avg
                    FROM success_metrics
                    WHERE strategy_name = ? AND timestamp >= ?
                """
                params = [strategy_name, cutoff_date]

                if game_type:
                    query += " AND game_type = ?"
                    params.append(game_type)

                query += """
                    GROUP BY DATE(timestamp), metric_name
                    ORDER BY date ASC
                """

                cursor.execute(query, params)
                time_series_data = cursor.fetchall()

            # Organize data by metric
            metrics_over_time = {}
            for row in time_series_data:
                date, metric_name, daily_avg = row
                if metric_name not in metrics_over_time:
                    metrics_over_time[metric_name] = []
                metrics_over_time[metric_name].append((date, daily_avg))

            # Calculate learning trends
            learning_analysis = {}
            for metric_name, data_points in metrics_over_time.items():
                if len(data_points) >= 3:
                    values = [point[1] for point in data_points]
                    trend = self._calculate_trend(values)
                    improvement_rate = self._calculate_improvement_rate(values)

                    learning_analysis[metric_name] = {
                        'trend': trend,
                        'improvement_rate': improvement_rate,
                        'data_points': len(data_points),
                        'latest_value': values[-1],
                        'improvement_detected': improvement_rate > 0.05
                    }

            # Overall learning assessment
            overall_assessment = self._assess_overall_learning(learning_analysis)

            return {
                'strategy_name': strategy_name,
                'game_type': game_type,
                'analysis_period_days': days,
                'metrics_analyzed': learning_analysis,
                'overall_assessment': overall_assessment,
                'learning_detected': overall_assessment.get('learning_detected', False)
            }

        except Exception as e:
            self.logger.error(f"Error analyzing learning curve: {e}")
            return {'error': str(e)}

    async def get_optimization_recommendations(self, strategy_name: str = None,
                                             game_type: str = None) -> List[Dict[str, Any]]:
        """
        Get optimization recommendations based on performance data.

        Args:
            strategy_name: Optional strategy filter
            game_type: Optional game type filter

        Returns:
            List of optimization recommendations
        """
        try:
            recommendations = []

            # Analyze underperforming areas
            underperforming = await self._identify_underperforming_areas(strategy_name, game_type)
            for area in underperforming:
                recommendations.append({
                    'type': 'improvement',
                    'priority': 'high',
                    'area': area['metric'],
                    'current_performance': area['performance'],
                    'target_performance': area['target'],
                    'recommendation': area['suggestion']
                })

            # Analyze successful patterns
            successful_patterns = await self._identify_successful_patterns(strategy_name, game_type)
            for pattern in successful_patterns:
                recommendations.append({
                    'type': 'amplify',
                    'priority': 'medium',
                    'area': pattern['area'],
                    'success_rate': pattern['success_rate'],
                    'recommendation': f"Amplify {pattern['area']} - showing {pattern['success_rate']:.2f} success rate"
                })

            # Analyze evolution triggers
            evolution_recommendations = await self._suggest_evolution_triggers()
            recommendations.extend(evolution_recommendations)

            # Sort by priority
            priority_order = {'high': 3, 'medium': 2, 'low': 1}
            recommendations.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)

            return recommendations

        except Exception as e:
            self.logger.error(f"Error getting optimization recommendations: {e}")
            return []

    def _extract_metrics(self, game_results: Dict[str, Any]) -> Dict[str, float]:
        """Extract metrics from game results"""
        try:
            metrics = {}

            # Basic performance metrics
            final_score = game_results.get('final_score', 0.0)
            actions_taken = game_results.get('actions_taken', 20)
            win = game_results.get('win', False)
            duration = game_results.get('duration_seconds', 60.0)

            metrics['win_rate'] = 1.0 if win else 0.0
            metrics['average_score'] = final_score
            metrics['actions_efficiency'] = final_score / max(actions_taken, 1)
            metrics['time_efficiency'] = final_score / max(duration, 1)

            # Strategy-specific metrics
            if 'strategy_mode' in game_results:
                strategy_mode = game_results['strategy_mode']
                metrics[f'{strategy_mode}_usage'] = 1.0

            # Emergency and recovery metrics
            if 'emergency_recoveries' in game_results:
                recoveries = game_results['emergency_recoveries']
                metrics['emergency_recovery_rate'] = recoveries / max(actions_taken, 1)

            # Pattern matching metrics
            if 'pattern_matches' in game_results:
                pattern_matches = game_results['pattern_matches']
                metrics['pattern_match_success'] = pattern_matches / max(actions_taken, 1)

            # Learning metrics
            if 'learning_events' in game_results:
                learning_events = game_results['learning_events']
                metrics['learning_rate'] = learning_events / max(actions_taken, 1)

            return metrics

        except Exception as e:
            self.logger.error(f"Error extracting metrics: {e}")
            return {}

    async def _store_metric(self, strategy_name: str, game_type: str, metric_name: str,
                          metric_value: float, context: Dict[str, Any]):
        """Store metric in database"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO success_metrics
                    (strategy_name, game_type, metric_name, metric_value, measurement_context)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    strategy_name,
                    game_type,
                    metric_name,
                    metric_value,
                    json.dumps({
                        'game_id': context.get('game_id', ''),
                        'session_id': context.get('session_id', ''),
                        'timestamp': datetime.now().isoformat()
                    })
                ))
                conn.commit()

        except Exception as e:
            self.logger.error(f"Error storing metric: {e}")

    async def _calculate_performance_summary(self, strategy_name: str, game_type: str) -> Dict[str, Any]:
        """Calculate performance summary for strategy/game_type combination"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()

                # Get recent performance data (last 30 days)
                cutoff_date = datetime.now() - timedelta(days=30)
                cursor.execute("""
                    SELECT metric_name, AVG(metric_value) as avg_value, COUNT(*) as sample_size,
                           MIN(metric_value) as min_value, MAX(metric_value) as max_value
                    FROM success_metrics
                    WHERE strategy_name = ? AND game_type = ? AND timestamp >= ?
                    GROUP BY metric_name
                """, (strategy_name, game_type, cutoff_date))

                performance_summary = {}
                for row in cursor.fetchall():
                    metric_name, avg_value, sample_size, min_value, max_value = row
                    performance_summary[metric_name] = {
                        'average': avg_value,
                        'min': min_value,
                        'max': max_value,
                        'sample_size': sample_size,
                        'confidence': min(1.0, sample_size / 10.0)
                    }

            # Calculate overall performance score
            win_rate = performance_summary.get('win_rate', {}).get('average', 0.0)
            avg_score = performance_summary.get('average_score', {}).get('average', 0.0)
            efficiency = performance_summary.get('actions_efficiency', {}).get('average', 0.0)

            overall_score = (win_rate * 0.5) + (min(avg_score / 100.0, 1.0) * 0.3) + (min(efficiency / 10.0, 1.0) * 0.2)
            performance_summary['overall_performance'] = overall_score

            return performance_summary

        except Exception as e:
            self.logger.error(f"Error calculating performance summary: {e}")
            return {}

    async def _get_additional_metrics(self, strategy_name: str, game_type: str) -> Dict[str, Any]:
        """Get additional metrics for a strategy"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT metric_name, AVG(metric_value) as avg_value
                    FROM success_metrics
                    WHERE strategy_name = ? AND game_type = ?
                    GROUP BY metric_name
                """, (strategy_name, game_type))

                additional_metrics = {}
                for row in cursor.fetchall():
                    metric_name, avg_value = row
                    if metric_name not in ['win_rate']:  # Don't duplicate primary metric
                        additional_metrics[metric_name] = avg_value

            return additional_metrics

        except Exception as e:
            self.logger.error(f"Error getting additional metrics: {e}")
            return {}

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from list of values"""
        try:
            if len(values) < 2:
                return 'insufficient_data'

            # Simple linear trend
            x = list(range(len(values)))
            n = len(values)

            # Calculate slope using least squares
            sum_x = sum(x)
            sum_y = sum(values)
            sum_xy = sum(x[i] * values[i] for i in range(n))
            sum_x2 = sum(x[i] ** 2 for i in range(n))

            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)

            if slope > 0.01:
                return 'increasing'
            elif slope < -0.01:
                return 'decreasing'
            else:
                return 'stable'

        except Exception as e:
            return 'unknown'

    def _calculate_improvement_rate(self, values: List[float]) -> float:
        """Calculate improvement rate from first to last value"""
        try:
            if len(values) < 2:
                return 0.0

            first_value = values[0]
            last_value = values[-1]

            if first_value == 0:
                return 1.0 if last_value > 0 else 0.0

            return (last_value - first_value) / first_value

        except Exception as e:
            return 0.0

    def _assess_overall_learning(self, learning_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall learning from metric analysis"""
        try:
            improving_metrics = []
            declining_metrics = []

            for metric_name, analysis in learning_analysis.items():
                if analysis.get('improvement_detected', False):
                    improving_metrics.append(metric_name)
                elif analysis.get('improvement_rate', 0) < -0.05:
                    declining_metrics.append(metric_name)

            learning_detected = len(improving_metrics) > len(declining_metrics)
            learning_strength = len(improving_metrics) / max(len(learning_analysis), 1)

            return {
                'learning_detected': learning_detected,
                'learning_strength': learning_strength,
                'improving_metrics': improving_metrics,
                'declining_metrics': declining_metrics,
                'overall_trend': 'improving' if learning_detected else 'stable_or_declining'
            }

        except Exception as e:
            self.logger.error(f"Error assessing overall learning: {e}")
            return {'learning_detected': False}

    async def _identify_underperforming_areas(self, strategy_name: str = None,
                                            game_type: str = None) -> List[Dict[str, Any]]:
        """Identify areas that are underperforming"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()

                # Define performance thresholds
                thresholds = {
                    'win_rate': 0.4,
                    'average_score': 50.0,
                    'actions_efficiency': 2.0,
                    'emergency_recovery_rate': 0.8
                }

                underperforming = []

                for metric, threshold in thresholds.items():
                    query = """
                        SELECT strategy_name, game_type, AVG(metric_value) as avg_performance
                        FROM success_metrics
                        WHERE metric_name = ?
                    """
                    params = [metric]

                    if strategy_name:
                        query += " AND strategy_name = ?"
                        params.append(strategy_name)

                    if game_type:
                        query += " AND game_type = ?"
                        params.append(game_type)

                    query += " GROUP BY strategy_name, game_type HAVING avg_performance < ?"
                    params.append(threshold)

                    cursor.execute(query, params)
                    results = cursor.fetchall()

                    for row in results:
                        underperforming.append({
                            'strategy': row[0],
                            'game_type': row[1],
                            'metric': metric,
                            'performance': row[2],
                            'target': threshold,
                            'suggestion': f"Improve {metric} - currently {row[2]:.2f}, target {threshold}"
                        })

            return underperforming

        except Exception as e:
            self.logger.error(f"Error identifying underperforming areas: {e}")
            return []

    async def _identify_successful_patterns(self, strategy_name: str = None,
                                          game_type: str = None) -> List[Dict[str, Any]]:
        """Identify successful patterns to amplify"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()

                # Find high-performing combinations
                query = """
                    SELECT strategy_name, game_type, metric_name, AVG(metric_value) as avg_performance,
                           COUNT(*) as sample_size
                    FROM success_metrics
                    WHERE metric_value > (
                        SELECT AVG(metric_value) * 1.2
                        FROM success_metrics s2
                        WHERE s2.metric_name = success_metrics.metric_name
                    )
                """
                params = []

                if strategy_name:
                    query += " AND strategy_name = ?"
                    params.append(strategy_name)

                if game_type:
                    query += " AND game_type = ?"
                    params.append(game_type)

                query += """
                    GROUP BY strategy_name, game_type, metric_name
                    HAVING sample_size >= 3
                    ORDER BY avg_performance DESC
                """

                cursor.execute(query, params)
                results = cursor.fetchall()

                successful_patterns = []
                for row in results:
                    successful_patterns.append({
                        'strategy': row[0],
                        'game_type': row[1],
                        'area': row[2],
                        'success_rate': row[3],
                        'sample_size': row[4]
                    })

            return successful_patterns[:10]  # Top 10 patterns

        except Exception as e:
            self.logger.error(f"Error identifying successful patterns: {e}")
            return []

    async def _suggest_evolution_triggers(self) -> List[Dict[str, Any]]:
        """Suggest when to trigger evolution based on performance stagnation"""
        try:
            recommendations = []

            # Check for performance stagnation
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT strategy_name, game_type, metric_name,
                           AVG(CASE WHEN timestamp >= datetime('now', '-7 days') THEN metric_value END) as recent_avg,
                           AVG(CASE WHEN timestamp < datetime('now', '-7 days') AND timestamp >= datetime('now', '-14 days') THEN metric_value END) as older_avg
                    FROM success_metrics
                    WHERE timestamp >= datetime('now', '-14 days')
                    GROUP BY strategy_name, game_type, metric_name
                    HAVING recent_avg IS NOT NULL AND older_avg IS NOT NULL
                """)

            stagnation_threshold = 0.05  # 5% improvement threshold

            for row in cursor.fetchall():
                strategy, game_type, metric, recent_avg, older_avg = row

                if older_avg > 0:
                    improvement = (recent_avg - older_avg) / older_avg

                    if improvement < stagnation_threshold:
                        recommendations.append({
                            'type': 'evolution_trigger',
                            'priority': 'medium',
                            'area': 'algorithm_evolution',
                            'reason': f'Performance stagnation detected in {metric} for {strategy}',
                            'recommendation': 'Consider triggering algorithm evolution to break through performance plateau'
                        })

            return recommendations[:3]  # Top 3 evolution recommendations

        except Exception as e:
            self.logger.error(f"Error suggesting evolution triggers: {e}")
            return []

    def get_success_tracking_summary(self) -> Dict[str, Any]:
        """Get overall success tracking summary"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()

                # Get total metrics tracked
                cursor.execute("SELECT COUNT(*) FROM success_metrics")
                total_metrics = cursor.fetchone()[0]

                # Get unique strategies
                cursor.execute("SELECT COUNT(DISTINCT strategy_name) FROM success_metrics")
                unique_strategies = cursor.fetchone()[0]

                # Get unique game types
                cursor.execute("SELECT COUNT(DISTINCT game_type) FROM success_metrics")
                unique_game_types = cursor.fetchone()[0]

                # Get recent performance trends
                cursor.execute("""
                    SELECT metric_name, AVG(metric_value) as avg_value
                    FROM success_metrics
                    WHERE timestamp >= datetime('now', '-7 days')
                    GROUP BY metric_name
                """)

                recent_trends = {}
                for row in cursor.fetchall():
                    recent_trends[row[0]] = row[1]

            return {
                'total_metrics_tracked': total_metrics,
                'unique_strategies': unique_strategies,
                'unique_game_types': unique_game_types,
                'recent_performance_trends': recent_trends,
                'cache_size': len(self.metric_cache),
                'tracked_metric_types': self.tracked_metrics
            }

        except Exception as e:
            self.logger.error(f"Error getting success tracking summary: {e}")
            return {'error': str(e)}