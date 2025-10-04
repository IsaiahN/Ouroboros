"""
EmergencyRecovery - Prevents game over in critical situations.
Implements Prompt 5 from Claude-Code Ready Prompts.
"""
from disable_pycache import *

import logging
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime
import json

from .utils.strategy_base import StrategyBase
from .utils.game_context import GameContext

logger = logging.getLogger(__name__)

class EmergencyRecovery(StrategyBase):
    """Emergency recovery system that prevents game over in critical situations"""

    def _ensure_numeric(self, value):
        """Ensure a value is numeric, handle lists and non-numeric types"""
        if isinstance(value, (list, tuple)):
            return float(value[0]) if len(value) > 0 else 0.0
        elif not isinstance(value, (int, float)):
            return 0.0
        return float(value)

    def __init__(self, db_interface):
        super().__init__(db_interface)
        self.emergency_history = []
        self.recovery_strategies = {}
        self.trigger_thresholds = {
            'rapid_score_decrease': 3,  # 3+ consecutive drops
            'low_progress_high_actions': 20,  # 20+ actions with <20% progress
            'repeated_failures': 4,  # 4+ failed actions in a row
            'time_critical': 5  # <5 actions remaining
        }

    async def check_emergency_conditions(self, context: GameContext) -> Dict[str, Any]:
        """
        Check for emergency conditions that require immediate intervention.

        Args:
            context: Current game context

        Returns:
            Emergency assessment with triggers and recommended actions
        """
        try:
            self.logger.debug("Checking emergency conditions")

            emergency_triggers = []
            severity_score = 0

            # Check each emergency condition
            score_decline = await self._check_rapid_score_decrease(context)
            if score_decline['triggered']:
                emergency_triggers.append(score_decline)
                severity_score += score_decline['severity']

            poor_progress = await self._check_poor_progress(context)
            if poor_progress['triggered']:
                emergency_triggers.append(poor_progress)
                severity_score += poor_progress['severity']

            repeated_failures = await self._check_repeated_failures(context)
            if repeated_failures['triggered']:
                emergency_triggers.append(repeated_failures)
                severity_score += repeated_failures['severity']

            time_critical = await self._check_time_critical(context)
            if time_critical['triggered']:
                emergency_triggers.append(time_critical)
                severity_score += time_critical['severity']

            game_over_risk = await self._check_game_over_risk(context)
            if game_over_risk['triggered']:
                emergency_triggers.append(game_over_risk)
                severity_score += game_over_risk['severity']

            # Determine emergency level
            is_emergency = len(emergency_triggers) >= 2 or severity_score >= 8

            emergency_assessment = {
                'is_emergency': is_emergency,
                'severity_score': severity_score,
                'emergency_level': self._determine_emergency_level(severity_score),
                'triggers': emergency_triggers,
                'recommended_recovery': await self._recommend_recovery_action(emergency_triggers, context) if is_emergency else None,
                'confidence': min(1.0, severity_score / 10.0)
            }

            if is_emergency:
                self.logger.warning(f"EMERGENCY DETECTED: level={emergency_assessment['emergency_level']}, triggers={len(emergency_triggers)}")

            return emergency_assessment

        except Exception as e:
            self.logger.error(f"Error checking emergency conditions: {e}")
            return {
                'is_emergency': False,
                'error': str(e),
                'confidence': 0.0
            }

    async def execute_recovery_action(self, recovery_plan: Dict[str, Any], context: GameContext, action_handler) -> Union[str, Callable]:
        """
        Execute emergency recovery action.

        Args:
            recovery_plan: Recovery plan from emergency assessment
            context: Current game context
            action_handler: Action handler for executing actions

        Returns:
            Recovery action to execute
        """
        try:
            self.logger.info(f"Executing emergency recovery: {recovery_plan['strategy']}")

            pre_recovery_score = context.current_score
            recovery_strategy = recovery_plan['strategy']

            # Execute recovery based on strategy type
            if recovery_strategy == 'ultra_safe':
                action = await self._execute_ultra_safe_recovery(context, action_handler)
            elif recovery_strategy == 'conservative_reset':
                action = await self._execute_conservative_reset(context, action_handler)
            elif recovery_strategy == 'pattern_break':
                action = await self._execute_pattern_break(context, action_handler)
            elif recovery_strategy == 'time_critical_focus':
                action = await self._execute_time_critical_focus(context, action_handler)
            elif recovery_strategy == 'last_resort':
                action = await self._execute_last_resort(context, action_handler)
            else:
                action = await self._execute_default_recovery(context, action_handler)

            # Log recovery attempt
            await self._log_recovery_attempt(recovery_strategy, context, pre_recovery_score)

            return action

        except Exception as e:
            self.logger.error(f"Error executing recovery action: {e}")
            return await self._execute_default_recovery(context, action_handler)

    async def _check_rapid_score_decrease(self, context: GameContext) -> Dict[str, Any]:
        """Check for rapid score decrease"""
        try:
            if len(context.score_history) < self.trigger_thresholds['rapid_score_decrease']:
                return {'triggered': False, 'severity': 0}

            # CRITICAL FIX: Ensure all scores are numeric before comparison
            raw_recent_scores = context.score_history[-self.trigger_thresholds['rapid_score_decrease']:]
            recent_scores = [self._ensure_numeric(s) for s in raw_recent_scores]

            # Check for consecutive decreases
            consecutive_drops = 0
            for i in range(1, len(recent_scores)):
                if recent_scores[i] < recent_scores[i-1]:
                    consecutive_drops += 1
                else:
                    break

            # Calculate severity based on drop magnitude and consistency
            triggered = consecutive_drops >= self.trigger_thresholds['rapid_score_decrease'] - 1

            if triggered:
                # Calculate percentage drop
                first_score = self._ensure_numeric(recent_scores[0])
                last_score = self._ensure_numeric(recent_scores[-1])
                score_drop = (first_score - last_score) / max(first_score, 1.0)
                severity = min(5, int(consecutive_drops * 1.5 + score_drop * 10))
            else:
                severity = 0

            return {
                'triggered': triggered,
                'severity': severity,
                'condition': 'rapid_score_decrease',
                'details': {
                    'consecutive_drops': consecutive_drops,
                    'score_drop_percent': score_drop if triggered else 0,
                    'recent_scores': recent_scores
                }
            }

        except Exception as e:
            self.logger.error(f"Error checking rapid score decrease: {e}")
            return {'triggered': False, 'severity': 0}

    async def _check_poor_progress(self, context: GameContext) -> Dict[str, Any]:
        """Check for poor progress with many actions"""
        try:
            triggered = (context.actions_taken >= self.trigger_thresholds['low_progress_high_actions'] and
                        context.score_progress < 0.2)

            if triggered:
                # Severity increases with more actions and lower progress
                progress_penalty = (0.2 - context.score_progress) * 10
                action_penalty = max(0, (context.actions_taken - 20) * 0.1)
                severity = min(5, int(progress_penalty + action_penalty))
            else:
                severity = 0

            return {
                'triggered': triggered,
                'severity': severity,
                'condition': 'poor_progress',
                'details': {
                    'actions_taken': context.actions_taken,
                    'score_progress': context.score_progress,
                    'efficiency': context.score_progress / max(context.actions_taken, 1)
                }
            }

        except Exception as e:
            self.logger.error(f"Error checking poor progress: {e}")
            return {'triggered': False, 'severity': 0}

    async def _check_repeated_failures(self, context: GameContext) -> Dict[str, Any]:
        """Check for repeated failures (same actions not working)"""
        try:
            if len(context.action_history) < self.trigger_thresholds['repeated_failures']:
                return {'triggered': False, 'severity': 0}

            recent_actions = context.action_history[-self.trigger_thresholds['repeated_failures']:]

            # Check for repetitive patterns
            unique_actions = len(set(recent_actions))
            repetition_score = 1.0 - (unique_actions / len(recent_actions))

            # Check score stagnation during these actions
            if len(context.score_history) >= len(recent_actions):
                recent_scores = [self._ensure_numeric(s) for s in context.score_history[-len(recent_actions):]]
                score_variance = max(recent_scores) - min(recent_scores)
                stagnation = score_variance < 5.0  # Very little score change
            else:
                stagnation = False

            triggered = repetition_score > 0.6 and (stagnation or context.score_momentum == 'decreasing')

            if triggered:
                severity = min(4, int(repetition_score * 5 + (2 if stagnation else 0)))
            else:
                severity = 0

            return {
                'triggered': triggered,
                'severity': severity,
                'condition': 'repeated_failures',
                'details': {
                    'repetition_score': repetition_score,
                    'unique_actions': unique_actions,
                    'total_actions': len(recent_actions),
                    'score_stagnation': stagnation
                }
            }

        except Exception as e:
            self.logger.error(f"Error checking repeated failures: {e}")
            return {'triggered': False, 'severity': 0}

    async def _check_time_critical(self, context: GameContext) -> Dict[str, Any]:
        """Check for time critical situations"""
        try:
            remaining_actions = context.actions_remaining_estimate
            triggered = remaining_actions <= self.trigger_thresholds['time_critical'] and context.score_progress < 0.8

            if triggered:
                # Higher severity with fewer remaining actions and lower progress
                time_pressure = (self.trigger_thresholds['time_critical'] - remaining_actions) * 2
                progress_pressure = (0.8 - context.score_progress) * 5
                severity = min(5, int(time_pressure + progress_pressure))
            else:
                severity = 0

            return {
                'triggered': triggered,
                'severity': severity,
                'condition': 'time_critical',
                'details': {
                    'actions_remaining': remaining_actions,
                    'score_progress': context.score_progress,
                    'urgency_level': 'critical' if remaining_actions <= 2 else 'high'
                }
            }

        except Exception as e:
            self.logger.error(f"Error checking time critical: {e}")
            return {'triggered': False, 'severity': 0}

    async def _check_game_over_risk(self, context: GameContext) -> Dict[str, Any]:
        """Check for immediate game over risk"""
        try:
            # High risk indicators
            risk_factors = []

            if context.score_momentum == 'strongly_decreasing':
                risk_factors.append('score_plummeting')

            if context.risk_level == 'very_high':
                risk_factors.append('high_risk_state')

            if context.actions_taken > 25 and context.score_progress < 0.15:
                risk_factors.append('low_efficiency')

            triggered = len(risk_factors) >= 2

            if triggered:
                severity = len(risk_factors) * 2
            else:
                severity = 0

            return {
                'triggered': triggered,
                'severity': severity,
                'condition': 'game_over_risk',
                'details': {
                    'risk_factors': risk_factors,
                    'risk_count': len(risk_factors)
                }
            }

        except Exception as e:
            self.logger.error(f"Error checking game over risk: {e}")
            return {'triggered': False, 'severity': 0}

    def _determine_emergency_level(self, severity_score: int) -> str:
        """Determine emergency level based on severity score"""
        if severity_score >= 12:
            return 'critical'
        elif severity_score >= 8:
            return 'high'
        elif severity_score >= 5:
            return 'medium'
        elif severity_score >= 2:
            return 'low'
        else:
            return 'none'

    async def _recommend_recovery_action(self, triggers: List[Dict], context: GameContext) -> Dict[str, Any]:
        """Recommend recovery action based on emergency triggers"""
        try:
            # Analyze triggers to determine best recovery strategy
            trigger_types = [t['condition'] for t in triggers]
            max_severity = max([t['severity'] for t in triggers]) if triggers else 0

            # Critical situations
            if max_severity >= 5 or 'game_over_risk' in trigger_types:
                strategy = 'last_resort'
            elif 'time_critical' in trigger_types:
                strategy = 'time_critical_focus'
            elif 'repeated_failures' in trigger_types:
                strategy = 'pattern_break'
            elif 'rapid_score_decrease' in trigger_types:
                strategy = 'conservative_reset'
            else:
                strategy = 'ultra_safe'

            return {
                'strategy': strategy,
                'priority': 'critical' if max_severity >= 5 else 'high',
                'triggers_addressed': trigger_types,
                'confidence': min(1.0, max_severity / 10.0)
            }

        except Exception as e:
            self.logger.error(f"Error recommending recovery action: {e}")
            return {
                'strategy': 'ultra_safe',
                'priority': 'medium',
                'confidence': 0.5
            }

    async def _execute_ultra_safe_recovery(self, context: GameContext, action_handler) -> str:
        """Execute ultra-safe recovery (ACTION1 only)"""
        self.logger.info("Executing ultra-safe recovery")

        if 1 in context.available_actions:
            return "ACTION1"
        else:
            # If ACTION1 not available, choose lowest numbered action
            if context.available_actions:
                return f"ACTION{min(context.available_actions)}"
            return "ACTION1"  # Fallback

    async def _execute_conservative_reset(self, context: GameContext, action_handler) -> str:
        """Execute conservative reset (safe actions only, no ACTION6)"""
        self.logger.info("Executing conservative reset recovery")

        safe_actions = [a for a in context.available_actions if a != 6]
        if safe_actions:
            # Prefer ACTION1, then others in order
            for preferred in [1, 2, 3, 4, 5, 7]:
                if preferred in safe_actions:
                    return f"ACTION{preferred}"
            return f"ACTION{safe_actions[0]}"
        else:
            # Only ACTION6 available - use safest coordinates
            coords = self.create_coordinate_strategy('center', {})
            return lambda: action_handler.send_action_6(coords['x'], coords['y'])

    async def _execute_pattern_break(self, context: GameContext, action_handler) -> Union[str, Callable]:
        """Execute pattern break (try completely different action)"""
        self.logger.info("Executing pattern break recovery")

        # Avoid recently used actions
        if len(context.action_history) >= 3:
            recent_action_nums = set()
            for action_str in context.action_history[-3:]:
                try:
                    if action_str.startswith('ACTION'):
                        num = int(action_str.replace('ACTION', '').split('(')[0])
                        recent_action_nums.add(num)
                except:
                    pass

            # Find actions not recently used
            fresh_actions = [a for a in context.available_actions if a not in recent_action_nums]
            if fresh_actions:
                # Choose safest from fresh actions
                safe_fresh = [a for a in fresh_actions if a != 6]
                if safe_fresh:
                    return f"ACTION{min(safe_fresh)}"
                elif 6 in fresh_actions:
                    coords = self.create_coordinate_strategy('center', {})
                    return lambda: action_handler.send_action_6(coords['x'], coords['y'])

        # Default to ACTION1 if pattern analysis fails
        return "ACTION1"

    async def _execute_time_critical_focus(self, context: GameContext, action_handler) -> Union[str, Callable]:
        """Execute time critical focus (high-value actions only)"""
        self.logger.info("Executing time critical focus recovery")

        # Focus on potentially high-scoring actions
        high_value_actions = [6, 7, 5, 1]

        for action_num in high_value_actions:
            if action_num in context.available_actions:
                if action_num == 6:
                    # Use center coordinates for safety
                    coords = self.create_coordinate_strategy('center', {})
                    return lambda: action_handler.send_action_6(coords['x'], coords['y'])
                else:
                    return f"ACTION{action_num}"

        # Fallback to any available action
        if context.available_actions:
            return f"ACTION{context.available_actions[0]}"
        return "ACTION1"

    async def _execute_last_resort(self, context: GameContext, action_handler) -> str:
        """Execute last resort recovery (most conservative possible)"""
        self.logger.warning("Executing LAST RESORT recovery")

        # Absolute priority on ACTION1
        if 1 in context.available_actions:
            return "ACTION1"

        # If not available, choose the lowest numbered action
        if context.available_actions:
            return f"ACTION{min(context.available_actions)}"

        return "ACTION1"  # Ultimate fallback

    async def _execute_default_recovery(self, context: GameContext, action_handler) -> str:
        """Execute default recovery action"""
        self.logger.info("Executing default recovery")
        return await self._execute_ultra_safe_recovery(context, action_handler)

    async def _log_recovery_attempt(self, strategy: str, context: GameContext, pre_recovery_score: float):
        """Log recovery attempt for analysis"""
        try:
            recovery_event = {
                'game_id': context.game_id,
                'session_id': context.session_id,
                'trigger_condition': strategy,
                'recovery_action_taken': strategy,
                'pre_recovery_score': pre_recovery_score,
                'post_recovery_score': context.current_score,  # Will be updated later
                'recovery_successful': False  # Will be updated based on results
            }

            self.save_emergency_recovery_event(recovery_event)

            # Store in history for analysis
            self.emergency_history.append({
                'strategy': strategy,
                'timestamp': datetime.now(),
                'context': context.to_dict(),
                'pre_score': pre_recovery_score
            })

            # Keep history manageable
            if len(self.emergency_history) > 50:
                self.emergency_history.pop(0)

        except Exception as e:
            self.logger.error(f"Error logging recovery attempt: {e}")

    def update_recovery_success(self, strategy: str, success: bool, score_change: float):
        """Update recovery strategy success rate"""
        try:
            if strategy not in self.recovery_strategies:
                self.recovery_strategies[strategy] = {
                    'attempts': 0,
                    'successes': 0,
                    'total_score_change': 0.0
                }

            stats = self.recovery_strategies[strategy]
            stats['attempts'] += 1
            stats['total_score_change'] += score_change

            if success:
                stats['successes'] += 1

        except Exception as e:
            self.logger.error(f"Error updating recovery success: {e}")

    def get_recovery_stats(self) -> Dict[str, Any]:
        """Get recovery strategy performance statistics"""
        try:
            stats = {}
            for strategy, data in self.recovery_strategies.items():
                if data['attempts'] > 0:
                    stats[strategy] = {
                        'attempts': data['attempts'],
                        'success_rate': data['successes'] / data['attempts'],
                        'avg_score_change': data['total_score_change'] / data['attempts']
                    }

            return {
                'strategy_stats': stats,
                'total_emergencies': sum(data['attempts'] for data in self.recovery_strategies.values()),
                'overall_success_rate': sum(data['successes'] for data in self.recovery_strategies.values()) /
                                       max(sum(data['attempts'] for data in self.recovery_strategies.values()), 1)
            }

        except Exception as e:
            self.logger.error(f"Error getting recovery stats: {e}")
            return {'error': str(e)}