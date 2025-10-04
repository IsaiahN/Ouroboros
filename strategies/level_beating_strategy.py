"""
LevelBeatingStrategy - Combines all components into single strategy.
Implements Prompt 7 from Claude-Code Ready Prompts.
"""
from disable_pycache import *

import logging
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime
import json

from .utils.strategy_base import StrategyBase
from .utils.game_context import GameContext
from .game_state_analyzer import GameStateAnalyzer
from .simple_heuristics_engine import SimpleHeuristicsEngine
from .action_feedback_learner import ActionFeedbackLearner
from .emergency_recovery import EmergencyRecovery
from .pattern_matcher import PatternMatcher

logger = logging.getLogger(__name__)

class LevelBeatingStrategy(StrategyBase):
    """Integrated strategy that combines all components for optimal level beating"""

    def __init__(self, db_interface):
        super().__init__(db_interface)

        # Initialize all components
        self.analyzer = GameStateAnalyzer(db_interface)
        self.heuristics = SimpleHeuristicsEngine(db_interface)
        self.feedback_learner = ActionFeedbackLearner(db_interface)
        self.emergency_recovery = EmergencyRecovery(db_interface)
        self.pattern_matcher = PatternMatcher(db_interface)

        # Strategy state
        self.game_context = None
        self.last_action = None
        self.last_state = None
        self.action_sequence = []
        self.strategy_mode = "balanced"

    async def get_next_action(self, game_state, action_handler) -> Union[str, Callable]:
        """
        Main strategy method that integrates all components.

        Flow:
        1. Analyze current game state
        2. Check for emergency conditions → use recovery if needed
        3. Apply pattern matching for action selection
        4. Use simple heuristics based on score/moves context
        5. Learn from each action's results

        Args:
            game_state: Current game state
            action_handler: Action handler for executing actions

        Returns:
            Action string or callable for ACTION6
        """
        try:
            self.logger.debug("Level-beating strategy selecting action")

            # Learn from previous action if available
            if self.last_action and self.last_state:
                await self._learn_from_previous_action(game_state)

            # Update game context
            self.game_context = GameContext()
            self.game_context.update_from_game_state(game_state)
            self.game_context.game_type = self.get_game_type_from_id(self.game_context.game_id)

            # Store current state for next iteration
            self.last_state = game_state

            # STEP 1: Analyze current game state
            analysis = await self.analyzer.analyze_game_state(game_state, action_handler, self.game_context)

            # Update context with analysis results
            self.game_context.score_momentum = analysis['score_momentum']
            self.game_context.risk_level = analysis['risk_level']
            self.game_context.emergency_detected = analysis['emergency_detected']

            # STEP 2: Check for emergency conditions
            emergency_assessment = await self.emergency_recovery.check_emergency_conditions(self.game_context)

            if emergency_assessment['is_emergency']:
                action = await self.emergency_recovery.execute_recovery_action(
                    emergency_assessment['recommended_recovery'],
                    self.game_context,
                    action_handler
                )
                self.strategy_mode = "emergency"
                self.last_action = action
                self._add_to_sequence(action)
                return action

            # STEP 3: Try pattern matching for action selection
            pattern_action = await self._try_pattern_based_action()
            if pattern_action:
                self.strategy_mode = "pattern"
                self.last_action = pattern_action
                self._add_to_sequence(pattern_action)
                return pattern_action

            # STEP 4: Use simple heuristics
            heuristic_action = await self.heuristics.get_next_action(game_state, action_handler)
            self.strategy_mode = "heuristic"
            self.last_action = heuristic_action
            self._add_to_sequence(heuristic_action)

            return heuristic_action

        except Exception as e:
            self.logger.error(f"Error in level-beating strategy: {e}")
            # Safe fallback
            fallback_action = "ACTION1"
            self.last_action = fallback_action
            return fallback_action

    async def _learn_from_previous_action(self, current_state):
        """Learn from the previous action's results"""
        try:
            if self.last_action and self.last_state:
                # Use feedback learner to learn from action
                learning_result = await self.feedback_learner.learn_from_action(
                    str(self.last_action),
                    self.last_state,
                    current_state
                )

                # Update heuristic success if it was a heuristic action
                if self.strategy_mode == "heuristic" and hasattr(self.heuristics, 'update_heuristic_success'):
                    score_change = learning_result.get('score_change', 0.0)
                    success = learning_result.get('success', False)

                    # Estimate which heuristic was used (simplified)
                    heuristic_name = self._estimate_heuristic_used()
                    self.heuristics.update_heuristic_success(heuristic_name, score_change, success)

                # If we have a completed successful sequence, learn it
                if (learning_result.get('success', False) and
                    len(self.action_sequence) >= 3 and
                    self.game_context and
                    self.game_context.score_momentum in ['increasing', 'strongly_increasing']):

                    await self.pattern_matcher.learn_successful_sequence(
                        self.action_sequence[-3:],  # Last 3 actions
                        self.game_context,
                        {
                            'score_change': learning_result.get('score_change', 0.0),
                            'win': self.game_context.game_state == 'WIN',
                            'actions_taken': self.game_context.actions_taken
                        }
                    )

        except Exception as e:
            self.logger.error(f"Error learning from previous action: {e}")

    async def _try_pattern_based_action(self) -> Optional[Union[str, Callable]]:
        """Try to use pattern matching for action selection"""
        try:
            if not self.game_context:
                return None

            # Get success probability for available actions
            action_probabilities = []

            for action_num in self.game_context.available_actions:
                action_str = f"ACTION{action_num}"
                probability = await self.feedback_learner.get_success_probability(action_str, self.game_context)
                action_probabilities.append((action_num, probability))

            # Sort by probability
            action_probabilities.sort(key=lambda x: x[1], reverse=True)

            # If best action has high probability, use it
            if action_probabilities and action_probabilities[0][1] > 0.7:
                best_action = action_probabilities[0][0]

                if best_action == 6:
                    # For ACTION6, use pattern-based coordinates
                    coords = await self._get_pattern_based_coordinates()
                    return lambda: self._get_action_handler().send_action_6(coords['x'], coords['y'])
                else:
                    return f"ACTION{best_action}"

            # Try to get a recommended sequence
            recommended_sequence = await self.pattern_matcher.recommend_action_sequence(self.game_context)

            if recommended_sequence and len(recommended_sequence) > 0:
                # Return the first action from the sequence
                first_action = recommended_sequence[0]

                if first_action.startswith('ACTION6'):
                    coords = await self._get_pattern_based_coordinates()
                    return lambda: self._get_action_handler().send_action_6(coords['x'], coords['y'])
                else:
                    return first_action

            return None

        except Exception as e:
            self.logger.error(f"Error in pattern-based action selection: {e}")
            return None

    async def _get_pattern_based_coordinates(self) -> Dict[str, int]:
        """Get coordinates for ACTION6 based on patterns"""
        try:
            # Use context to determine coordinate strategy
            if not self.game_context:
                return {'x': 32, 'y': 32}

            # Choose strategy based on game context
            if self.game_context.emergency_detected:
                strategy = 'center'
            elif self.game_context.score_progress < 0.3:
                strategy = 'exploration'
            elif self.game_context.score_progress > 0.7:
                strategy = 'center'
            elif self.game_context.time_pressure:
                strategy = 'corner'
            else:
                strategy = 'exploration'

            return self.create_coordinate_strategy(strategy, self.game_context.to_dict())

        except Exception as e:
            self.logger.error(f"Error getting pattern-based coordinates: {e}")
            return {'x': 32, 'y': 32}

    def _add_to_sequence(self, action: Union[str, Callable]):
        """Add action to current sequence"""
        try:
            action_str = str(action)
            if callable(action):
                action_str = "ACTION6_pattern"

            self.action_sequence.append(action_str)

            # Keep sequence manageable
            if len(self.action_sequence) > 10:
                self.action_sequence.pop(0)

            # Update game context if available
            if self.game_context:
                self.game_context.add_action(action_str)

        except Exception as e:
            self.logger.error(f"Error adding to sequence: {e}")

    def _estimate_heuristic_used(self) -> str:
        """Estimate which heuristic was used (simplified)"""
        try:
            if not self.game_context:
                return "unknown"

            if self.game_context.emergency_detected:
                return "emergency"
            elif self.game_context.score_progress > 0.7:
                return "conservative"
            elif self.game_context.current_score < 30:
                return "aggressive_exploration"
            elif self.game_context.time_pressure:
                return "high_value"
            elif self.game_context.score_momentum == 'stable':
                return "breakthrough"
            else:
                return "balanced"

        except Exception as e:
            return "unknown"

    def _get_action_handler(self):
        """Get action handler reference (placeholder)"""
        # This would be passed in or injected in a real implementation
        return None

    async def adapt_to_game_type(self, game_type: str):
        """Adapt strategy based on detected game type"""
        try:
            self.logger.info(f"Adapting strategy to game type: {game_type}")

            # Adjust strategy parameters based on game type
            if game_type == 'puzzle':
                # Puzzle games - methodical, systematic
                self.strategy_mode = "methodical"
                # Reduce emergency thresholds (more patient)
                self.emergency_recovery.trigger_thresholds['low_progress_high_actions'] = 30

            elif game_type == 'action':
                # Action games - quick, reactive
                self.strategy_mode = "reactive"
                # Increase emergency sensitivity
                self.emergency_recovery.trigger_thresholds['low_progress_high_actions'] = 15

            elif game_type == 'strategy':
                # Strategy games - long-term planning
                self.strategy_mode = "planning"
                # Focus more on pattern matching
                self.pattern_matcher.pattern_weights['exact_match'] = 1.2

            elif game_type == 'visual_challenge':
                # Visual challenge - exploration focused
                self.strategy_mode = "exploration"
                # Increase exploration weight

            else:
                # Unknown - adaptive approach
                self.strategy_mode = "adaptive"

        except Exception as e:
            self.logger.error(f"Error adapting to game type: {e}")

    async def get_strategy_performance(self) -> Dict[str, Any]:
        """Get performance metrics for this strategy"""
        try:
            # Get component performance
            heuristic_performance = self.heuristics.get_heuristic_performance_summary()
            pattern_stats = self.pattern_matcher.get_pattern_statistics()
            recovery_stats = self.emergency_recovery.get_recovery_stats()
            learning_summary = self.feedback_learner.get_learning_summary()

            return {
                'strategy_name': 'LevelBeatingStrategy',
                'current_mode': self.strategy_mode,
                'action_sequence_length': len(self.action_sequence),
                'heuristic_performance': heuristic_performance,
                'pattern_stats': pattern_stats,
                'recovery_stats': recovery_stats,
                'learning_summary': learning_summary,
                'last_action': str(self.last_action) if self.last_action else None
            }

        except Exception as e:
            self.logger.error(f"Error getting strategy performance: {e}")
            return {'error': str(e)}

    def reset_strategy_state(self):
        """Reset strategy state for new game"""
        try:
            self.game_context = None
            self.last_action = None
            self.last_state = None
            self.action_sequence = []
            self.strategy_mode = "balanced"

            self.logger.debug("Strategy state reset for new game")

        except Exception as e:
            self.logger.error(f"Error resetting strategy state: {e}")

    async def save_game_session_results(self, game_results: Dict[str, Any]):
        """Save results from completed game session"""
        try:
            # Extract key metrics
            final_score = game_results.get('final_score', 0.0)
            win_detected = game_results.get('win', False)
            actions_taken = game_results.get('actions_taken', 0)

            # Save overall strategy performance
            await self.save_performance_metrics({
                'metric_name': 'game_completion',
                'metric_value': final_score,
                'measurement_context': {
                    'win': win_detected,
                    'actions_taken': actions_taken,
                    'strategy_mode': self.strategy_mode,
                    'sequence_length': len(self.action_sequence),
                    'game_type': self.game_context.game_type if self.game_context else 'unknown'
                }
            })

            # If successful, learn the entire sequence
            if win_detected or final_score > 70:
                if self.action_sequence and self.game_context:
                    await self.pattern_matcher.learn_successful_sequence(
                        self.action_sequence,
                        self.game_context,
                        {
                            'score_change': final_score,
                            'win': win_detected,
                            'actions_taken': actions_taken
                        }
                    )

            self.logger.info(f"Saved game session results: score={final_score}, win={win_detected}")

        except Exception as e:
            self.logger.error(f"Error saving game session results: {e}")

    def get_current_analysis(self) -> Dict[str, Any]:
        """Get current analysis state"""
        try:
            if not self.game_context:
                return {'status': 'no_context'}

            return {
                'game_context': self.game_context.to_dict(),
                'strategy_mode': self.strategy_mode,
                'action_sequence': self.action_sequence,
                'last_action': str(self.last_action) if self.last_action else None
            }

        except Exception as e:
            self.logger.error(f"Error getting current analysis: {e}")
            return {'error': str(e)}

    async def update_from_external_feedback(self, feedback: Dict[str, Any]):
        """Update strategy based on external feedback"""
        try:
            # Update component configurations based on feedback
            if 'emergency_sensitivity' in feedback:
                sensitivity = feedback['emergency_sensitivity']
                if sensitivity == 'high':
                    # Make more sensitive to emergencies
                    for key in self.emergency_recovery.trigger_thresholds:
                        self.emergency_recovery.trigger_thresholds[key] = int(
                            self.emergency_recovery.trigger_thresholds[key] * 0.8
                        )
                elif sensitivity == 'low':
                    # Make less sensitive to emergencies
                    for key in self.emergency_recovery.trigger_thresholds:
                        self.emergency_recovery.trigger_thresholds[key] = int(
                            self.emergency_recovery.trigger_thresholds[key] * 1.2
                        )

            if 'pattern_weight_adjustment' in feedback:
                adjustment = feedback['pattern_weight_adjustment']
                for pattern_type, weight in self.pattern_matcher.pattern_weights.items():
                    self.pattern_matcher.pattern_weights[pattern_type] *= adjustment

            self.logger.info(f"Updated strategy from external feedback: {feedback}")

        except Exception as e:
            self.logger.error(f"Error updating from external feedback: {e}")