"""
GameTypeRouter - Detects game type and applies appropriate strategy.
Implements Prompt 4 from Claude-Code Ready Prompts.
"""
from disable_pycache import *

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import re

from .utils.strategy_base import StrategyBase
from .utils.game_context import GameContext

logger = logging.getLogger(__name__)

class GameTypeRouter(StrategyBase):
    """Detects game type and routes to appropriate specialized strategies"""

    def __init__(self, db_interface):
        super().__init__(db_interface)
        self.game_type_cache = {}
        self.strategy_configs = self._initialize_strategy_configs()
        self.detection_patterns = self._initialize_detection_patterns()

    def _initialize_strategy_configs(self) -> Dict[str, Dict[str, Any]]:
        """Initialize strategy configurations for different game types"""
        return {
            'puzzle': {
                'name': 'Puzzle Strategy',
                'approach': 'methodical',
                'action_preferences': [1, 2, 3, 4, 5, 6, 7],  # Methodical order
                'emergency_threshold': 0.8,  # More patient
                'exploration_factor': 0.6,   # Less aggressive exploration
                'time_pressure_factor': 0.7, # Less rushed
                'pattern_weight': 1.2,       # High pattern matching weight
                'heuristic_weights': {
                    'conservative': 1.3,
                    'breakthrough': 1.1,
                    'balanced': 1.0,
                    'aggressive_exploration': 0.8,
                    'emergency': 1.0
                }
            },
            'action': {
                'name': 'Action Strategy',
                'approach': 'reactive',
                'action_preferences': [6, 7, 1, 5, 2, 3, 4],  # Quick actions first
                'emergency_threshold': 0.6,  # More reactive to emergencies
                'exploration_factor': 1.2,   # More aggressive
                'time_pressure_factor': 1.3, # More urgent
                'pattern_weight': 0.9,       # Less pattern dependence
                'heuristic_weights': {
                    'aggressive_exploration': 1.3,
                    'high_value': 1.2,
                    'balanced': 1.0,
                    'conservative': 0.8,
                    'emergency': 1.1
                }
            },
            'strategy': {
                'name': 'Strategy Planning',
                'approach': 'planning',
                'action_preferences': [1, 6, 2, 7, 3, 5, 4],  # Balanced planning
                'emergency_threshold': 0.7,  # Moderate emergency response
                'exploration_factor': 0.9,   # Balanced exploration
                'time_pressure_factor': 0.8, # Less time pressure
                'pattern_weight': 1.4,       # Very high pattern matching
                'heuristic_weights': {
                    'balanced': 1.3,
                    'conservative': 1.1,
                    'breakthrough': 1.0,
                    'aggressive_exploration': 0.9,
                    'emergency': 1.0
                }
            },
            'visual_challenge': {
                'name': 'Visual Challenge',
                'approach': 'exploration',
                'action_preferences': [6, 1, 7, 2, 5, 3, 4],  # Exploration focused
                'emergency_threshold': 0.7,
                'exploration_factor': 1.4,   # High exploration
                'time_pressure_factor': 1.0,
                'pattern_weight': 1.0,
                'heuristic_weights': {
                    'aggressive_exploration': 1.4,
                    'breakthrough': 1.2,
                    'balanced': 1.0,
                    'conservative': 0.7,
                    'emergency': 1.0
                }
            },
            'unknown': {
                'name': 'Adaptive Strategy',
                'approach': 'adaptive',
                'action_preferences': [1, 6, 2, 3, 7, 4, 5],  # Balanced approach
                'emergency_threshold': 0.7,
                'exploration_factor': 1.0,
                'time_pressure_factor': 1.0,
                'pattern_weight': 1.0,
                'heuristic_weights': {
                    'balanced': 1.2,
                    'conservative': 1.0,
                    'aggressive_exploration': 1.0,
                    'breakthrough': 1.0,
                    'emergency': 1.0
                }
            }
        }

    def _initialize_detection_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize patterns for game type detection"""
        return {
            'puzzle': {
                'id_patterns': [
                    r'puzzle', r'pz\d+', r'logic', r'riddle', r'brain',
                    r'think', r'solve', r'mental'
                ],
                'characteristics': {
                    'pace': 'slow',
                    'risk': 'low',
                    'complexity': 'high',
                    'pattern_importance': 'very_high'
                },
                'indicators': [
                    'methodical_approach_needed',
                    'pattern_recognition_key',
                    'time_not_critical'
                ]
            },
            'action': {
                'id_patterns': [
                    r'action', r'act\d+', r'fast', r'quick', r'speed',
                    r'reflex', r'rapid', r'rush'
                ],
                'characteristics': {
                    'pace': 'fast',
                    'risk': 'high',
                    'complexity': 'medium',
                    'pattern_importance': 'medium'
                },
                'indicators': [
                    'quick_decisions_needed',
                    'time_critical',
                    'high_risk_high_reward'
                ]
            },
            'strategy': {
                'id_patterns': [
                    r'strategy', r'str\d+', r'plan', r'tactic', r'strategic',
                    r'manage', r'resource', r'build'
                ],
                'characteristics': {
                    'pace': 'medium',
                    'risk': 'medium',
                    'complexity': 'very_high',
                    'pattern_importance': 'very_high'
                },
                'indicators': [
                    'long_term_planning',
                    'resource_management',
                    'complex_patterns'
                ]
            },
            'visual_challenge': {
                'id_patterns': [
                    r'vc\d+', r'vs\d+', r'vm\d+', r'visual', r'image',
                    r'picture', r'graphic', r'art'
                ],
                'characteristics': {
                    'pace': 'medium',
                    'risk': 'medium',
                    'complexity': 'high',
                    'pattern_importance': 'high'
                },
                'indicators': [
                    'visual_pattern_recognition',
                    'spatial_reasoning',
                    'exploration_important'
                ]
            }
        }

    async def detect_game_type(self, game_id: str, context: GameContext = None) -> Dict[str, Any]:
        """
        Detect game type based on game ID and context.

        Args:
            game_id: Game identifier
            context: Optional game context for additional analysis

        Returns:
            Detection results with game type and confidence
        """
        try:
            self.logger.debug(f"Detecting game type for: {game_id}")

            # Check cache first
            if game_id in self.game_type_cache:
                cached_result = self.game_type_cache[game_id]
                self.logger.debug(f"Using cached game type: {cached_result['detected_type']}")
                return cached_result

            # Analyze game ID patterns
            id_analysis = self._analyze_game_id_patterns(game_id)

            # Analyze context if available
            context_analysis = self._analyze_game_context(context) if context else {'type': 'unknown', 'confidence': 0.0}

            # Combine analyses
            combined_analysis = self._combine_analyses(id_analysis, context_analysis)

            # Determine final game type
            detected_type = combined_analysis['type']
            confidence = combined_analysis['confidence']

            # Get game characteristics
            characteristics = self._get_game_characteristics(detected_type)

            # Create detection result
            detection_result = {
                'game_id': game_id,
                'detected_type': detected_type,
                'type_confidence': confidence,
                'game_characteristics': characteristics,
                'strategy_mapping': self.strategy_configs.get(detected_type, self.strategy_configs['unknown']),
                'detection_details': {
                    'id_analysis': id_analysis,
                    'context_analysis': context_analysis,
                    'combined_score': combined_analysis
                },
                'detection_timestamp': datetime.now().isoformat()
            }

            # Cache result
            self.game_type_cache[game_id] = detection_result

            # Store in database
            await self._store_game_type_detection(detection_result)

            self.logger.info(f"Detected game type: {detected_type} (confidence: {confidence:.2f})")
            return detection_result

        except Exception as e:
            self.logger.error(f"Error detecting game type: {e}")
            return {
                'game_id': game_id,
                'detected_type': 'unknown',
                'type_confidence': 0.0,
                'strategy_mapping': self.strategy_configs['unknown'],
                'error': str(e)
            }

    def _analyze_game_id_patterns(self, game_id: str) -> Dict[str, Any]:
        """Analyze game ID for type patterns"""
        try:
            game_id_lower = game_id.lower()
            type_scores = {}

            # Check each game type pattern
            for game_type, patterns in self.detection_patterns.items():
                score = 0.0
                matched_patterns = []

                for pattern in patterns['id_patterns']:
                    if re.search(pattern, game_id_lower):
                        score += 1.0
                        matched_patterns.append(pattern)

                # Normalize score
                max_possible_score = len(patterns['id_patterns'])
                normalized_score = score / max_possible_score if max_possible_score > 0 else 0.0

                type_scores[game_type] = {
                    'score': normalized_score,
                    'matched_patterns': matched_patterns
                }

            # Find best match
            best_type = max(type_scores.keys(), key=lambda x: type_scores[x]['score'])
            best_score = type_scores[best_type]['score']

            return {
                'type': best_type if best_score > 0.0 else 'unknown',
                'confidence': best_score,
                'all_scores': type_scores
            }

        except Exception as e:
            self.logger.error(f"Error analyzing game ID patterns: {e}")
            return {'type': 'unknown', 'confidence': 0.0}

    def _analyze_game_context(self, context: GameContext) -> Dict[str, Any]:
        """Analyze game context for type indicators"""
        try:
            if not context:
                return {'type': 'unknown', 'confidence': 0.0}

            type_indicators = {}

            # Analyze action patterns
            if len(context.action_history) >= 5:
                action_variety = len(set(context.action_history)) / len(context.action_history)

                if action_variety < 0.4:  # Low variety - might be puzzle
                    type_indicators['puzzle'] = 0.6
                elif action_variety > 0.8:  # High variety - might be action game
                    type_indicators['action'] = 0.7

            # Analyze score progression
            if len(context.score_history) >= 5:
                # CRITICAL FIX: Ensure all scores in history are numeric before arithmetic
                numeric_scores = []
                for score in context.score_history:
                    if isinstance(score, (list, tuple)):
                        numeric_scores.append(score[0] if len(score) > 0 else 0.0)
                    elif isinstance(score, (int, float)):
                        numeric_scores.append(float(score))
                    else:
                        numeric_scores.append(0.0)

                score_variance = max(numeric_scores) - min(numeric_scores)
                avg_score = sum(numeric_scores) / len(numeric_scores)

                if score_variance > avg_score * 0.5:  # High variance - action game
                    type_indicators['action'] = type_indicators.get('action', 0.0) + 0.3
                elif score_variance < avg_score * 0.2:  # Low variance - puzzle game
                    type_indicators['puzzle'] = type_indicators.get('puzzle', 0.0) + 0.3

            # Analyze time pressure
            if context.time_pressure:
                type_indicators['action'] = type_indicators.get('action', 0.0) + 0.4
            elif context.actions_taken > 20 and context.score_progress > 0.5:
                type_indicators['strategy'] = type_indicators.get('strategy', 0.0) + 0.3

            # Find best match from context
            if type_indicators:
                best_type = max(type_indicators.keys(), key=lambda x: type_indicators[x])
                best_confidence = type_indicators[best_type]
            else:
                best_type = 'unknown'
                best_confidence = 0.0

            return {
                'type': best_type,
                'confidence': best_confidence,
                'indicators': type_indicators
            }

        except Exception as e:
            self.logger.error(f"Error analyzing game context: {e}")
            return {'type': 'unknown', 'confidence': 0.0}

    def _combine_analyses(self, id_analysis: Dict, context_analysis: Dict) -> Dict[str, Any]:
        """Combine ID and context analyses"""
        try:
            # Weight ID analysis higher than context analysis
            id_weight = 0.7
            context_weight = 0.3

            combined_scores = {}

            # Get all possible types
            all_types = set()
            all_types.add(id_analysis['type'])
            all_types.add(context_analysis['type'])
            all_types.update(self.detection_patterns.keys())

            # Calculate combined scores
            for game_type in all_types:
                if game_type == 'unknown':
                    continue

                id_score = id_analysis['confidence'] if id_analysis['type'] == game_type else 0.0
                context_score = context_analysis['confidence'] if context_analysis['type'] == game_type else 0.0

                combined_score = (id_score * id_weight) + (context_score * context_weight)
                combined_scores[game_type] = combined_score

            # Find best match
            if combined_scores:
                best_type = max(combined_scores.keys(), key=lambda x: combined_scores[x])
                best_confidence = combined_scores[best_type]

                # Minimum confidence threshold
                if best_confidence < 0.05:  # Very low threshold for better detection
                    best_type = 'unknown'
                    best_confidence = 0.0
            else:
                best_type = 'unknown'
                best_confidence = 0.0

            return {
                'type': best_type,
                'confidence': best_confidence,
                'combined_scores': combined_scores
            }

        except Exception as e:
            self.logger.error(f"Error combining analyses: {e}")
            return {'type': 'unknown', 'confidence': 0.0}

    def _get_game_characteristics(self, game_type: str) -> Dict[str, Any]:
        """Get characteristics for detected game type"""
        try:
            if game_type in self.detection_patterns:
                return self.detection_patterns[game_type]['characteristics']
            else:
                return {
                    'pace': 'medium',
                    'risk': 'medium',
                    'complexity': 'medium',
                    'pattern_importance': 'medium'
                }

        except Exception as e:
            self.logger.error(f"Error getting game characteristics: {e}")
            return {}

    async def get_strategy_for_game_type(self, game_type: str) -> Dict[str, Any]:
        """Get strategy configuration for specific game type"""
        try:
            if game_type in self.strategy_configs:
                return self.strategy_configs[game_type].copy()
            else:
                return self.strategy_configs['unknown'].copy()

        except Exception as e:
            self.logger.error(f"Error getting strategy for game type: {e}")
            return self.strategy_configs['unknown'].copy()

    async def route_to_specialized_strategy(self, game_type: str, context: GameContext) -> Dict[str, Any]:
        """Route to specialized strategy based on game type"""
        try:
            strategy_config = await self.get_strategy_for_game_type(game_type)

            # Customize strategy based on current context
            if context:
                # Adjust emergency threshold based on current situation
                if context.risk_level == 'high':
                    strategy_config['emergency_threshold'] *= 0.8

                # Adjust exploration factor based on progress
                if context.score_progress < 0.3:
                    strategy_config['exploration_factor'] *= 1.2
                elif context.score_progress > 0.7:
                    strategy_config['exploration_factor'] *= 0.8

                # Adjust time pressure factor based on remaining actions
                if context.time_pressure:
                    strategy_config['time_pressure_factor'] *= 1.3

            return {
                'game_type': game_type,
                'strategy_config': strategy_config,
                'routing_details': {
                    'base_strategy': strategy_config['name'],
                    'approach': strategy_config['approach'],
                    'customizations_applied': True if context else False
                }
            }

        except Exception as e:
            self.logger.error(f"Error routing to specialized strategy: {e}")
            return {
                'game_type': 'unknown',
                'strategy_config': self.strategy_configs['unknown'],
                'error': str(e)
            }

    async def _store_game_type_detection(self, detection_result: Dict[str, Any]):
        """Store game type detection in database"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO game_type_detection
                    (game_id, detected_type, type_confidence, game_characteristics, strategy_mapping)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    detection_result['game_id'],
                    detection_result['detected_type'],
                    detection_result['type_confidence'],
                    json.dumps(detection_result['game_characteristics']),
                    json.dumps(detection_result['strategy_mapping'])
                ))
                conn.commit()

        except Exception as e:
            self.logger.error(f"Error storing game type detection: {e}")

    def update_game_type_from_performance(self, game_id: str, performance_data: Dict[str, Any]):
        """Update game type classification based on performance data"""
        try:
            if game_id not in self.game_type_cache:
                return

            cached_detection = self.game_type_cache[game_id]
            current_type = cached_detection['detected_type']
            current_confidence = cached_detection['type_confidence']

            # Analyze performance indicators
            win_rate = performance_data.get('win_rate', 0.0)
            avg_score = performance_data.get('avg_score', 0.0)
            actions_per_game = performance_data.get('avg_actions_per_game', 20)

            # Adjust confidence based on performance
            if win_rate > 0.7:  # Good performance confirms type
                new_confidence = min(1.0, current_confidence * 1.1)
            elif win_rate < 0.3:  # Poor performance suggests wrong type
                new_confidence = max(0.0, current_confidence * 0.9)
            else:
                new_confidence = current_confidence

            # Update cache
            cached_detection['type_confidence'] = new_confidence

            self.logger.info(f"Updated game type confidence for {game_id}: {current_type} ({new_confidence:.2f})")

        except Exception as e:
            self.logger.error(f"Error updating game type from performance: {e}")

    def get_game_type_statistics(self) -> Dict[str, Any]:
        """Get statistics about game type detection"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT detected_type, COUNT(*) as count, AVG(type_confidence) as avg_confidence
                    FROM game_type_detection
                    GROUP BY detected_type
                    ORDER BY count DESC
                """)

                type_stats = {}
                for row in cursor.fetchall():
                    type_stats[row[0]] = {
                        'count': row[1],
                        'avg_confidence': row[2]
                    }

            return {
                'total_games_classified': len(self.game_type_cache),
                'type_distribution': type_stats,
                'cache_size': len(self.game_type_cache)
            }

        except Exception as e:
            self.logger.error(f"Error getting game type statistics: {e}")
            return {'error': str(e)}