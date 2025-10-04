"""
SimpleHeuristicsEngine - Rule-based strategies that can beat easy levels.
Implements Prompt 3 from Claude-Code Ready Prompts.
"""
from disable_pycache import *

import logging
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from datetime import datetime
import json
import random

from .utils.strategy_base import StrategyBase
from .utils.game_context import GameContext
from .game_state_analyzer import GameStateAnalyzer

logger = logging.getLogger(__name__)

class SimpleHeuristicsEngine(StrategyBase):
    """Rule-based strategy engine with simple heuristics for beating easy levels"""

    def __init__(self, db_interface):
        super().__init__(db_interface)
        self.analyzer = GameStateAnalyzer(db_interface)
        self.heuristic_stats = {}

    async def get_next_action(self, game_state, action_handler) -> Union[str, Callable]:
        """
        Main method to get next action using simple heuristics.

        Args:
            game_state: Current game state
            action_handler: Action handler for executing actions

        Returns:
            Action string or callable for ACTION6
        """
        try:
            self.logger.debug("Simple heuristics engine selecting action")

            # Create and update game context
            context = GameContext()
            context.update_from_game_state(game_state)

            # Get analysis from game state analyzer
            analysis = await self.analyzer.analyze_game_state(game_state, action_handler, context)

            # Update context with analysis results
            context.score_momentum = analysis['score_momentum']
            context.risk_level = analysis['risk_level']
            context.emergency_detected = analysis['emergency_detected']

            # Apply heuristics in priority order
            selected_action, heuristic_used = await self._apply_heuristics(context, action_handler)

            # Track heuristic performance
            await self._track_heuristic_usage(selected_action, heuristic_used, context)

            return selected_action

        except Exception as e:
            self.logger.error(f"Error in simple heuristics engine: {e}")
            # Safe fallback
            return await self._safe_fallback_action(game_state, action_handler)

    async def _apply_heuristics(self, context: GameContext, action_handler) -> Tuple[Union[str, Callable], str]:
        """Apply heuristics based on game context"""

        # HEURISTIC 1: Emergency Recovery - Highest Priority
        if context.emergency_detected or context.risk_level in ['high', 'very_high']:
            action = await self._emergency_heuristic(context, action_handler)
            return action, "emergency"

        # HEURISTIC 2: Near Victory - Conservative Protection
        if context.score_progress > 0.7:
            action = await self._conservative_heuristic(context, action_handler)
            return action, "conservative"

        # HEURISTIC 3: Early Game - Aggressive Exploration
        if context.current_score < 30 or context.actions_taken < 8:
            action = await self._aggressive_exploration_heuristic(context, action_handler)
            return action, "aggressive_exploration"

        # HEURISTIC 4: Time Pressure - High-Value Focus
        if context.time_pressure or context.actions_remaining_estimate < 10:
            action = await self._high_value_heuristic(context, action_handler)
            return action, "high_value"

        # HEURISTIC 5: Stagnation - Breakthrough Actions
        if context.score_momentum == 'stable' and context.actions_taken >= 5:
            action = await self._breakthrough_heuristic(context, action_handler)
            return action, "breakthrough"

        # HEURISTIC 6: Score Decline - Recovery Pattern
        if context.score_momentum in ['decreasing', 'strongly_decreasing']:
            action = await self._recovery_heuristic(context, action_handler)
            return action, "recovery"

        # DEFAULT: Balanced approach
        action = await self._balanced_heuristic(context, action_handler)
        return action, "balanced"

    async def _emergency_heuristic(self, context: GameContext, action_handler) -> Union[str, Callable]:
        """Emergency heuristic - avoid high-risk actions"""
        self.logger.info("Applying emergency heuristic")

        # Ultra-conservative approach
        # Prefer ACTION1 (usually safest)
        if 1 in context.available_actions:
            return "ACTION1"

        # Avoid ACTION6 completely in emergency
        safe_actions = [a for a in context.available_actions if a != 6]
        if safe_actions:
            # Prefer lower-numbered actions (typically safer)
            return f"ACTION{min(safe_actions)}"

        # Last resort - even ACTION6 if no choice
        if 6 in context.available_actions:
            coords = self.create_coordinate_strategy('center', {})
            return lambda: action_handler.send_action_6(coords['x'], coords['y'])

        return "ACTION1"  # Ultimate fallback

    async def _conservative_heuristic(self, context: GameContext, action_handler) -> Union[str, Callable]:
        """Conservative heuristic for when score > 70% - protect lead"""
        self.logger.info("Applying conservative heuristic (protecting lead)")

        # Proven safe actions in order of preference
        preferred_order = [1, 2, 3, 4, 5, 7, 6]  # ACTION6 last

        for action_num in preferred_order:
            if action_num in context.available_actions:
                if action_num == 6:
                    # If forced to use ACTION6, use safest coordinates
                    coords = self.create_coordinate_strategy('center', {})
                    return lambda: action_handler.send_action_6(coords['x'], coords['y'])
                else:
                    return f"ACTION{action_num}"

        return "ACTION1"

    async def _aggressive_exploration_heuristic(self, context: GameContext, action_handler) -> Union[str, Callable]:
        """Aggressive exploration for early game (score < 30 or actions < 8)"""
        self.logger.info("Applying aggressive exploration heuristic")

        # Prefer ACTION6 for exploration if available
        if 6 in context.available_actions:
            coords = await self._generate_exploration_coordinates(context)
            return lambda: action_handler.send_action_6(coords['x'], coords['y'])

        # Try other exploration actions
        exploration_order = [7, 5, 4, 3, 2, 1]
        for action_num in exploration_order:
            if action_num in context.available_actions:
                return f"ACTION{action_num}"

        return "ACTION1"

    async def _high_value_heuristic(self, context: GameContext, action_handler) -> Union[str, Callable]:
        """High-value heuristic when time pressure is high"""
        self.logger.info("Applying high-value heuristic (time pressure)")

        # Focus on actions that typically give highest scores
        high_value_order = [6, 7, 5, 1, 2, 3, 4]

        for action_num in high_value_order:
            if action_num in context.available_actions:
                if action_num == 6:
                    coords = await self._generate_high_value_coordinates(context)
                    return lambda: action_handler.send_action_6(coords['x'], coords['y'])
                else:
                    return f"ACTION{action_num}"

        return "ACTION1"

    async def _breakthrough_heuristic(self, context: GameContext, action_handler) -> Union[str, Callable]:
        """Breakthrough heuristic when score is stagnant"""
        self.logger.info("Applying breakthrough heuristic (score stagnant)")

        # Try different approach - randomize to break patterns
        all_actions = [1, 2, 3, 4, 5, 6, 7]
        available = [a for a in all_actions if a in context.available_actions]

        # Avoid recent actions to break repetitive patterns
        if len(context.action_history) >= 2:
            recent_action_nums = []
            for action_str in context.action_history[-2:]:
                try:
                    if action_str.startswith('ACTION'):
                        num = int(action_str.replace('ACTION', '').split('(')[0])
                        recent_action_nums.append(num)
                except:
                    pass

            # Filter out recently used actions
            fresh_actions = [a for a in available if a not in recent_action_nums]
            if fresh_actions:
                available = fresh_actions

        # Shuffle to try different combinations
        random.shuffle(available)

        if available:
            action_num = available[0]
            if action_num == 6:
                coords = await self._generate_breakthrough_coordinates(context)
                return lambda: action_handler.send_action_6(coords['x'], coords['y'])
            else:
                return f"ACTION{action_num}"

        return "ACTION1"

    async def _recovery_heuristic(self, context: GameContext, action_handler) -> Union[str, Callable]:
        """Recovery heuristic for declining scores"""
        self.logger.info("Applying recovery heuristic (score declining)")

        # Try to reverse negative trend
        # If previous actions were high-numbered, try low-numbered
        if len(context.action_history) >= 2:
            recent_nums = []
            for action_str in context.action_history[-2:]:
                try:
                    if action_str.startswith('ACTION'):
                        num = int(action_str.replace('ACTION', '').split('(')[0])
                        recent_nums.append(num)
                except:
                    pass

            if recent_nums and statistics.mean(recent_nums) > 4:
                # Recent actions were high-numbered, try lower
                recovery_order = [1, 2, 3, 4, 5, 6, 7]
            else:
                # Recent actions were low-numbered, try higher
                recovery_order = [7, 6, 5, 4, 3, 2, 1]
        else:
            # Default recovery - start with safe actions
            recovery_order = [1, 3, 5, 2, 4, 7, 6]

        for action_num in recovery_order:
            if action_num in context.available_actions:
                if action_num == 6:
                    coords = self.create_coordinate_strategy('center', {})
                    return lambda: action_handler.send_action_6(coords['x'], coords['y'])
                else:
                    return f"ACTION{action_num}"

        return "ACTION1"

    async def _balanced_heuristic(self, context: GameContext, action_handler) -> Union[str, Callable]:
        """Balanced heuristic for normal gameplay"""
        self.logger.info("Applying balanced heuristic")

        # Balanced action priority based on momentum
        if context.score_momentum in ['increasing', 'strongly_increasing']:
            # Keep doing what's working
            preferred_order = [1, 6, 2, 3, 7, 4, 5]
        elif context.score_momentum in ['decreasing', 'strongly_decreasing']:
            # Try to change momentum
            preferred_order = [6, 7, 1, 5, 2, 3, 4]
        else:
            # Stable - balanced exploration
            preferred_order = [1, 6, 7, 2, 5, 3, 4]

        for action_num in preferred_order:
            if action_num in context.available_actions:
                if action_num == 6:
                    coords = await self._generate_balanced_coordinates(context)
                    return lambda: action_handler.send_action_6(coords['x'], coords['y'])
                else:
                    return f"ACTION{action_num}"

        return "ACTION1"

    async def _generate_exploration_coordinates(self, context: GameContext) -> Dict[str, int]:
        """Generate coordinates for exploration"""
        # Exploration strategy based on what's been tried
        exploration_strategies = ['center', 'corner', 'edge', 'exploration']

        # Simple round-robin based on actions taken
        strategy_index = context.actions_taken % len(exploration_strategies)
        strategy = exploration_strategies[strategy_index]

        return self.create_coordinate_strategy(strategy, {'context': context.to_dict()})

    async def _generate_high_value_coordinates(self, context: GameContext) -> Dict[str, int]:
        """Generate coordinates for high-value targeting"""
        # Target key positions that often yield high scores
        high_value_positions = [
            {'x': 32, 'y': 32},  # Center
            {'x': 16, 'y': 16},  # Quarter points
            {'x': 48, 'y': 48},
            {'x': 16, 'y': 48},
            {'x': 48, 'y': 16},
        ]

        # Choose based on context
        if context.score_progress < 0.3:
            # Low progress - try center first
            return high_value_positions[0]
        else:
            # Rotating through positions
            index = context.actions_taken % len(high_value_positions)
            return high_value_positions[index]

    async def _generate_breakthrough_coordinates(self, context: GameContext) -> Dict[str, int]:
        """Generate coordinates for breakthrough attempts"""
        # Try edge positions for breakthrough
        return self.create_coordinate_strategy('edge', {'breakthrough': True})

    async def _generate_balanced_coordinates(self, context: GameContext) -> Dict[str, int]:
        """Generate coordinates for balanced play"""
        # Choose strategy based on score momentum
        if context.score_momentum == 'increasing':
            return self.create_coordinate_strategy('center', {})
        elif context.score_momentum == 'decreasing':
            return self.create_coordinate_strategy('exploration', {})
        else:
            return self.create_coordinate_strategy('corner', {})

    async def _safe_fallback_action(self, game_state, action_handler) -> str:
        """Safe fallback when heuristics fail"""
        try:
            available = getattr(game_state, 'available_actions', [1])
            if available:
                # Prefer ACTION1 as safest
                if 1 in available:
                    return "ACTION1"
                else:
                    return f"ACTION{min(available)}"  # Lowest number (typically safest)
            return "ACTION1"
        except:
            return "ACTION1"

    async def _track_heuristic_usage(self, action: Union[str, Callable], heuristic_name: str, context: GameContext):
        """Track which heuristic was used for performance analysis"""
        try:
            # Convert action to string for tracking
            action_str = str(action)
            if callable(action):
                action_str = "ACTION6_callable"

            # Update local stats
            if heuristic_name not in self.heuristic_stats:
                self.heuristic_stats[heuristic_name] = {
                    'usage_count': 0,
                    'total_score_impact': 0.0,
                    'success_count': 0
                }

            self.heuristic_stats[heuristic_name]['usage_count'] += 1

            # Save to database
            await self.save_performance_metrics({
                'heuristic_name': heuristic_name,
                'condition_met': {
                    'score': context.current_score,
                    'progress': context.score_progress,
                    'actions_taken': context.actions_taken,
                    'momentum': context.score_momentum,
                    'risk_level': context.risk_level,
                    'emergency_detected': context.emergency_detected,
                    'time_pressure': context.time_pressure
                },
                'action_taken': action_str,
                'usage_count': 1,
                'success_rate': self._calculate_heuristic_success_rate(heuristic_name),
                'avg_score_impact': self._calculate_avg_score_impact(heuristic_name)
            })

        except Exception as e:
            self.logger.error(f"Error tracking heuristic usage: {e}")

    def _calculate_heuristic_success_rate(self, heuristic_name: str) -> float:
        """Calculate success rate for a heuristic"""
        try:
            stats = self.heuristic_stats.get(heuristic_name, {})
            usage_count = stats.get('usage_count', 0)
            success_count = stats.get('success_count', 0)

            if usage_count == 0:
                return 0.5  # Neutral for new heuristics

            return success_count / usage_count

        except Exception as e:
            self.logger.error(f"Error calculating success rate: {e}")
            return 0.5

    def _calculate_avg_score_impact(self, heuristic_name: str) -> float:
        """Calculate average score impact for a heuristic"""
        try:
            stats = self.heuristic_stats.get(heuristic_name, {})
            usage_count = stats.get('usage_count', 0)
            total_impact = stats.get('total_score_impact', 0.0)

            if usage_count == 0:
                return 0.0

            return total_impact / usage_count

        except Exception as e:
            self.logger.error(f"Error calculating score impact: {e}")
            return 0.0

    def update_heuristic_success(self, heuristic_name: str, score_change: float, success: bool):
        """Update heuristic success metrics"""
        try:
            if heuristic_name not in self.heuristic_stats:
                self.heuristic_stats[heuristic_name] = {
                    'usage_count': 0,
                    'total_score_impact': 0.0,
                    'success_count': 0
                }

            stats = self.heuristic_stats[heuristic_name]
            stats['total_score_impact'] += score_change
            if success:
                stats['success_count'] += 1

        except Exception as e:
            self.logger.error(f"Error updating heuristic success: {e}")

    def get_heuristic_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary of all heuristics"""
        try:
            summary = {}
            for heuristic_name, stats in self.heuristic_stats.items():
                usage_count = stats['usage_count']
                if usage_count > 0:
                    summary[heuristic_name] = {
                        'usage_count': usage_count,
                        'success_rate': stats['success_count'] / usage_count,
                        'avg_score_impact': stats['total_score_impact'] / usage_count
                    }

            return summary

        except Exception as e:
            self.logger.error(f"Error getting performance summary: {e}")
            return {}