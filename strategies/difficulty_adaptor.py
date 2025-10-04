"""
DifficultyAdaptor - Adjusts strategy based on game difficulty.
Implements Prompt 8 from Claude-Code Ready Prompts.
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

class DifficultyAdaptor(StrategyBase):
    """Adjusts strategy parameters based on detected game difficulty"""

    def __init__(self, db_interface):
        super().__init__(db_interface)
        self.difficulty_cache = {}
        self.performance_history = {}
        self.adaptation_rules = self._initialize_adaptation_rules()

    def _initialize_adaptation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize adaptation rules for different difficulty levels"""
        return {
            'very_easy': {
                'name': 'Very Easy Games',
                'strategy_adjustments': {
                    'aggression_multiplier': 1.4,      # More aggressive
                    'exploration_factor': 1.3,         # More exploration
                    'emergency_threshold': 0.9,        # Less emergency sensitive
                    'time_pressure_tolerance': 1.2,    # Less time pressure
                    'pattern_reliance': 0.8,           # Less pattern dependent
                    'heuristic_confidence': 1.2        # More confident in heuristics
                },
                'action_preferences': {
                    'preferred_actions': [6, 7, 1, 5, 2, 3, 4],  # Exploration first
                    'avoid_actions': [],
                    'action6_frequency': 1.3  # Use ACTION6 more often
                },
                'completion_strategy': 'aggressive_fast'
            },
            'easy': {
                'name': 'Easy Games',
                'strategy_adjustments': {
                    'aggression_multiplier': 1.2,
                    'exploration_factor': 1.1,
                    'emergency_threshold': 0.8,
                    'time_pressure_tolerance': 1.1,
                    'pattern_reliance': 0.9,
                    'heuristic_confidence': 1.1
                },
                'action_preferences': {
                    'preferred_actions': [1, 6, 7, 2, 3, 5, 4],
                    'avoid_actions': [],
                    'action6_frequency': 1.1
                },
                'completion_strategy': 'balanced_aggressive'
            },
            'medium': {
                'name': 'Medium Games',
                'strategy_adjustments': {
                    'aggression_multiplier': 1.0,
                    'exploration_factor': 1.0,
                    'emergency_threshold': 0.7,
                    'time_pressure_tolerance': 1.0,
                    'pattern_reliance': 1.0,
                    'heuristic_confidence': 1.0
                },
                'action_preferences': {
                    'preferred_actions': [1, 6, 2, 3, 7, 4, 5],
                    'avoid_actions': [],
                    'action6_frequency': 1.0
                },
                'completion_strategy': 'balanced'
            },
            'hard': {
                'name': 'Hard Games',
                'strategy_adjustments': {
                    'aggression_multiplier': 0.8,
                    'exploration_factor': 0.9,
                    'emergency_threshold': 0.6,
                    'time_pressure_tolerance': 0.9,
                    'pattern_reliance': 1.2,
                    'heuristic_confidence': 0.9
                },
                'action_preferences': {
                    'preferred_actions': [1, 2, 3, 6, 4, 5, 7],  # More conservative
                    'avoid_actions': [],
                    'action6_frequency': 0.9
                },
                'completion_strategy': 'careful_methodical'
            },
            'very_hard': {
                'name': 'Very Hard Games',
                'strategy_adjustments': {
                    'aggression_multiplier': 0.6,
                    'exploration_factor': 0.7,
                    'emergency_threshold': 0.5,
                    'time_pressure_tolerance': 0.8,
                    'pattern_reliance': 1.4,
                    'heuristic_confidence': 0.8
                },
                'action_preferences': {
                    'preferred_actions': [1, 2, 3, 4, 5, 6, 7],  # Very conservative
                    'avoid_actions': [],
                    'action6_frequency': 0.7
                },
                'completion_strategy': 'ultra_conservative'
            },
            'unknown': {
                'name': 'Unknown Difficulty',
                'strategy_adjustments': {
                    'aggression_multiplier': 1.0,
                    'exploration_factor': 1.0,
                    'emergency_threshold': 0.7,
                    'time_pressure_tolerance': 1.0,
                    'pattern_reliance': 1.0,
                    'heuristic_confidence': 1.0
                },
                'action_preferences': {
                    'preferred_actions': [1, 6, 2, 3, 7, 4, 5],
                    'avoid_actions': [],
                    'action6_frequency': 1.0
                },
                'completion_strategy': 'adaptive'
            }
        }

    async def assess_difficulty(self, game_id: str, context: GameContext = None) -> Dict[str, Any]:
        """
        Assess game difficulty based on historical data and current context.

        Args:
            game_id: Game identifier
            context: Optional current game context

        Returns:
            Difficulty assessment with level and confidence
        """
        try:
            self.logger.debug(f"Assessing difficulty for game: {game_id}")

            # Check cache first
            if game_id in self.difficulty_cache:
                cached_assessment = self.difficulty_cache[game_id]
                # Update with current context if available
                if context:
                    cached_assessment = await self._update_assessment_with_context(cached_assessment, context)
                return cached_assessment

            # Get historical performance data
            historical_data = await self._get_historical_performance(game_id)

            # Analyze current context if available
            context_analysis = await self._analyze_current_context(context) if context else {}

            # Combine analyses to determine difficulty
            difficulty_assessment = await self._calculate_difficulty(historical_data, context_analysis)

            # Store in cache and database
            self.difficulty_cache[game_id] = difficulty_assessment
            await self._store_difficulty_assessment(game_id, difficulty_assessment)

            self.logger.info(f"Assessed difficulty: {difficulty_assessment['difficulty_level']} "
                           f"(score: {difficulty_assessment['difficulty_score']:.2f})")

            return difficulty_assessment

        except Exception as e:
            self.logger.error(f"Error assessing difficulty: {e}")
            return {
                'difficulty_level': 'unknown',
                'difficulty_score': 0.5,
                'confidence': 0.0,
                'error': str(e)
            }

    async def adapt_strategy_to_difficulty(self, difficulty_assessment: Dict[str, Any],
                                         base_strategy_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adapt strategy configuration based on difficulty assessment.

        Args:
            difficulty_assessment: Result from assess_difficulty
            base_strategy_config: Base strategy configuration to adapt

        Returns:
            Adapted strategy configuration
        """
        try:
            difficulty_level = difficulty_assessment.get('difficulty_level', 'unknown')
            confidence = difficulty_assessment.get('confidence', 0.0)

            self.logger.debug(f"Adapting strategy for difficulty: {difficulty_level}")

            # Get adaptation rules for this difficulty
            adaptation_rules = self.adaptation_rules.get(difficulty_level, self.adaptation_rules['unknown'])

            # Create adapted configuration
            adapted_config = base_strategy_config.copy()

            # Apply strategy adjustments
            strategy_adjustments = adaptation_rules['strategy_adjustments']

            for adjustment_name, multiplier in strategy_adjustments.items():
                if adjustment_name in adapted_config:
                    # Apply multiplier with confidence weighting
                    effective_multiplier = 1.0 + (multiplier - 1.0) * confidence
                    adapted_config[adjustment_name] *= effective_multiplier

            # Update action preferences
            action_preferences = adaptation_rules['action_preferences']
            adapted_config['action_preferences'] = action_preferences['preferred_actions']
            adapted_config['avoid_actions'] = action_preferences['avoid_actions']
            adapted_config['action6_frequency'] = action_preferences['action6_frequency']

            # Set completion strategy
            adapted_config['completion_strategy'] = adaptation_rules['completion_strategy']

            # Add difficulty-specific heuristic weights
            if 'heuristic_weights' in adapted_config:
                confidence_multiplier = strategy_adjustments.get('heuristic_confidence', 1.0)
                for heuristic, weight in adapted_config['heuristic_weights'].items():
                    adapted_config['heuristic_weights'][heuristic] *= confidence_multiplier

            # Store adaptation details
            adapted_config['adaptation_details'] = {
                'original_difficulty': difficulty_level,
                'adaptation_applied': True,
                'confidence': confidence,
                'adjustments': strategy_adjustments
            }

            self.logger.info(f"Strategy adapted for {difficulty_level} difficulty")
            return adapted_config

        except Exception as e:
            self.logger.error(f"Error adapting strategy to difficulty: {e}")
            return base_strategy_config  # Return original on error

    async def _get_historical_performance(self, game_id: str) -> Dict[str, Any]:
        """Get historical performance data for this game"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()

                # Get game results for this specific game ID
                cursor.execute("""
                    SELECT final_score, total_actions, win_detected, status
                    FROM game_results
                    WHERE game_id = ?
                    ORDER BY start_time DESC
                    LIMIT 20
                """, (game_id,))

                game_results = cursor.fetchall()

                if not game_results:
                    return {'data_available': False}

                # Calculate performance metrics
                scores = [row[0] for row in game_results if row[0] is not None]
                actions = [row[1] for row in game_results if row[1] is not None]
                wins = [row[2] for row in game_results if row[2] is not None]

            performance_data = {
                'data_available': True,
                'games_played': len(game_results),
                'avg_score': statistics.mean(scores) if scores else 0.0,
                'max_score': max(scores) if scores else 0.0,
                'min_score': min(scores) if scores else 0.0,
                'score_std': statistics.stdev(scores) if len(scores) > 1 else 0.0,
                'avg_actions': statistics.mean(actions) if actions else 20.0,
                'win_rate': sum(wins) / len(wins) if wins else 0.0,
                'completion_rate': sum(1 for row in game_results if row[3] == 'completed') / len(game_results)
            }

            return performance_data

        except Exception as e:
            self.logger.error(f"Error getting historical performance: {e}")
            return {'data_available': False}

    async def _analyze_current_context(self, context: GameContext) -> Dict[str, Any]:
        """Analyze current game context for difficulty indicators"""
        try:
            indicators = {}

            # Score progression difficulty
            if context.score_progress < 0.2 and context.actions_taken > 10:
                indicators['slow_progress'] = 1.0
            elif context.score_progress > 0.6 and context.actions_taken < 10:
                indicators['fast_progress'] = 1.0

            # Score momentum difficulty
            if context.score_momentum == 'decreasing' and context.actions_taken > 5:
                indicators['declining_performance'] = 1.0
            elif context.score_momentum == 'increasing':
                indicators['improving_performance'] = 1.0

            # Risk level indicators
            if context.risk_level == 'high':
                indicators['high_risk_situation'] = 1.0
            elif context.risk_level == 'low':
                indicators['low_risk_situation'] = 1.0

            # Emergency frequency
            if context.emergency_detected:
                indicators['emergency_situation'] = 1.0

            # Action efficiency
            if context.actions_taken > 0:
                efficiency = context.score_progress / context.actions_taken
                if efficiency < 0.02:  # Very low efficiency
                    indicators['low_efficiency'] = 1.0
                elif efficiency > 0.1:  # High efficiency
                    indicators['high_efficiency'] = 1.0

            return {
                'indicators': indicators,
                'context_score': context.score_progress,
                'context_actions': context.actions_taken,
                'context_momentum': context.score_momentum
            }

        except Exception as e:
            self.logger.error(f"Error analyzing current context: {e}")
            return {}

    async def _calculate_difficulty(self, historical_data: Dict[str, Any],
                                  context_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate difficulty level from historical and context data"""
        try:
            difficulty_score = 0.5  # Base difficulty (medium)
            confidence = 0.0

            # Historical data analysis
            if historical_data.get('data_available', False):
                historical_weight = 0.7
                confidence += 0.5

                # Win rate indicators
                win_rate = historical_data['win_rate']
                if win_rate < 0.2:
                    difficulty_score += 0.3  # Very hard
                elif win_rate < 0.4:
                    difficulty_score += 0.2  # Hard
                elif win_rate > 0.8:
                    difficulty_score -= 0.3  # Easy
                elif win_rate > 0.6:
                    difficulty_score -= 0.2  # Somewhat easy

                # Score consistency indicators
                score_std = historical_data.get('score_std', 0.0)
                avg_score = historical_data.get('avg_score', 0.0)
                if avg_score > 0:
                    cv = score_std / avg_score  # Coefficient of variation
                    if cv > 0.5:  # High variability = more difficult
                        difficulty_score += 0.1
                    elif cv < 0.2:  # Low variability = more predictable
                        difficulty_score -= 0.1

                # Actions per game
                avg_actions = historical_data.get('avg_actions', 20.0)
                if avg_actions > 25:  # Many actions needed
                    difficulty_score += 0.1
                elif avg_actions < 15:  # Few actions needed
                    difficulty_score -= 0.1

                # Completion rate
                completion_rate = historical_data.get('completion_rate', 1.0)
                if completion_rate < 0.7:  # Low completion rate
                    difficulty_score += 0.2

            # Context analysis
            if context_analysis:
                context_weight = 0.3
                confidence += 0.3

                indicators = context_analysis.get('indicators', {})

                # Difficulty indicators from context
                if 'slow_progress' in indicators:
                    difficulty_score += 0.2
                if 'declining_performance' in indicators:
                    difficulty_score += 0.15
                if 'high_risk_situation' in indicators:
                    difficulty_score += 0.1
                if 'emergency_situation' in indicators:
                    difficulty_score += 0.1
                if 'low_efficiency' in indicators:
                    difficulty_score += 0.15

                # Easy indicators from context
                if 'fast_progress' in indicators:
                    difficulty_score -= 0.2
                if 'improving_performance' in indicators:
                    difficulty_score -= 0.15
                if 'low_risk_situation' in indicators:
                    difficulty_score -= 0.1
                if 'high_efficiency' in indicators:
                    difficulty_score -= 0.15

            # Clamp difficulty score
            difficulty_score = max(0.0, min(1.0, difficulty_score))

            # Determine difficulty level
            if difficulty_score < 0.2:
                difficulty_level = 'very_easy'
            elif difficulty_score < 0.4:
                difficulty_level = 'easy'
            elif difficulty_score < 0.6:
                difficulty_level = 'medium'
            elif difficulty_score < 0.8:
                difficulty_level = 'hard'
            else:
                difficulty_level = 'very_hard'

            return {
                'difficulty_level': difficulty_level,
                'difficulty_score': difficulty_score,
                'confidence': confidence,
                'assessment_factors': {
                    'historical_data': historical_data,
                    'context_analysis': context_analysis
                },
                'assessment_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error calculating difficulty: {e}")
            return {
                'difficulty_level': 'unknown',
                'difficulty_score': 0.5,
                'confidence': 0.0
            }

    async def _update_assessment_with_context(self, cached_assessment: Dict[str, Any],
                                            context: GameContext) -> Dict[str, Any]:
        """Update cached assessment with current context"""
        try:
            # Analyze current context
            context_analysis = await self._analyze_current_context(context)

            # Adjust difficulty score based on current performance
            original_score = cached_assessment['difficulty_score']
            context_indicators = context_analysis.get('indicators', {})

            score_adjustment = 0.0

            # Real-time difficulty indicators
            if context.score_momentum == 'decreasing' and context.actions_taken > 10:
                score_adjustment += 0.1  # Game seems harder than expected
            elif context.score_momentum == 'increasing' and context.score_progress > 0.5:
                score_adjustment -= 0.1  # Game seems easier than expected

            if context.emergency_detected:
                score_adjustment += 0.05

            # Update assessment
            updated_assessment = cached_assessment.copy()
            updated_assessment['difficulty_score'] = max(0.0, min(1.0, original_score + score_adjustment))
            updated_assessment['context_updated'] = True
            updated_assessment['last_context_update'] = datetime.now().isoformat()

            return updated_assessment

        except Exception as e:
            self.logger.error(f"Error updating assessment with context: {e}")
            return cached_assessment

    async def _store_difficulty_assessment(self, game_id: str, assessment: Dict[str, Any]):
        """Store difficulty assessment in database"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO difficulty_assessments
                    (game_id, difficulty_level, difficulty_score, assessment_factors, strategy_adjustments)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    game_id,
                    assessment['difficulty_level'],
                    assessment['difficulty_score'],
                    json.dumps(assessment.get('assessment_factors', {})),
                    json.dumps(self.adaptation_rules.get(assessment['difficulty_level'], {}))
                ))
                conn.commit()

        except Exception as e:
            self.logger.error(f"Error storing difficulty assessment: {e}")

    def update_difficulty_from_results(self, game_id: str, game_results: Dict[str, Any]):
        """Update difficulty assessment based on game results"""
        try:
            if game_id not in self.difficulty_cache:
                return

            assessment = self.difficulty_cache[game_id]
            current_score = assessment['difficulty_score']

            # Analyze results
            final_score = game_results.get('final_score', 0.0)
            actions_taken = game_results.get('actions_taken', 20)
            win = game_results.get('win', False)

            # Calculate performance indicators
            efficiency = final_score / max(actions_taken, 1)

            score_adjustment = 0.0

            # Adjust based on performance vs expectations
            if win and efficiency > 5.0:  # Performed better than expected
                score_adjustment = -0.1
            elif not win and efficiency < 1.0:  # Performed worse than expected
                score_adjustment = 0.1

            # Update cached assessment
            new_score = max(0.0, min(1.0, current_score + score_adjustment))
            assessment['difficulty_score'] = new_score
            assessment['updated_from_results'] = True

            self.logger.debug(f"Updated difficulty for {game_id}: {new_score:.2f}")

        except Exception as e:
            self.logger.error(f"Error updating difficulty from results: {e}")

    def get_difficulty_statistics(self) -> Dict[str, Any]:
        """Get difficulty assessment statistics"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT difficulty_level, COUNT(*) as count, AVG(difficulty_score) as avg_score
                    FROM difficulty_assessments
                    GROUP BY difficulty_level
                    ORDER BY count DESC
                """)

                difficulty_stats = {}
                for row in cursor.fetchall():
                    difficulty_stats[row[0]] = {
                        'count': row[1],
                        'avg_score': row[2]
                    }

            return {
                'total_assessments': len(self.difficulty_cache),
                'difficulty_distribution': difficulty_stats,
                'cache_size': len(self.difficulty_cache),
                'adaptation_rules_count': len(self.adaptation_rules)
            }

        except Exception as e:
            self.logger.error(f"Error getting difficulty statistics: {e}")
            return {'error': str(e)}