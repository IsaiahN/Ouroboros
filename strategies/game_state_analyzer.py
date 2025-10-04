"""
GameStateAnalyzer - Analyzes current game state to provide actionable insights.
Implements Prompt 1 from Claude-Code Ready Prompts.
"""
from disable_pycache import *

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import statistics

from .utils.strategy_base import StrategyBase
from .utils.game_context import GameContext

logger = logging.getLogger(__name__)

class GameStateAnalyzer(StrategyBase):
    """Analyzes current game state to provide actionable insights"""

    def _ensure_numeric(self, value):
        """Ensure a value is numeric, handle lists and non-numeric types"""
        if isinstance(value, (list, tuple)):
            return float(value[0]) if len(value) > 0 else 0.0
        elif not isinstance(value, (int, float)):
            return 0.0
        return float(value)

    def __init__(self, db_interface):
        super().__init__(db_interface)
        self.analysis_history = []

    async def analyze_game_state(self, game_state, action_handler, context: GameContext = None) -> Dict[str, Any]:
        """
        Main analysis method that provides comprehensive game state insights.

        Args:
            game_state: Current game state object
            action_handler: Action handler for context
            context: Optional pre-built game context

        Returns:
            dict with analysis metrics and recommended actions
        """
        try:
            self.logger.debug("Starting game state analysis")

            # Extract or use provided game context
            if context is None:
                context = GameContext()
                context.update_from_game_state(game_state)

            # Perform analysis components
            score_momentum = await self._calculate_score_momentum(context)
            risk_level = await self._assess_risk_level(context)
            opportunity_zones = await self._identify_opportunity_zones(context)
            emergency_detected = await self._detect_emergency_situation(context)
            recommended_actions = await self._prioritize_actions(context)

            # Update context with analysis results
            context.score_momentum = score_momentum
            context.risk_level = risk_level
            context.emergency_detected = emergency_detected

            # Compile analysis results
            analysis = {
                'game_id': context.game_id,
                'session_id': context.session_id,
                'action_number': context.actions_taken,
                'score_momentum': score_momentum,
                'risk_level': risk_level,
                'opportunity_zones': opportunity_zones,
                'emergency_detected': emergency_detected,
                'recommended_actions': recommended_actions,
                'analysis_context': {
                    'current_score': context.current_score,
                    'win_score': context.win_score,
                    'score_progress': context.score_progress,
                    'available_actions': context.available_actions,
                    'time_pressure': context.time_pressure,
                    'confidence_score': self.calculate_confidence_score({
                        'score_trend': score_momentum,
                        'emergency_detected': emergency_detected,
                        'recent_success': score_momentum == 'increasing',
                        'familiar_pattern': len(context.action_history) > 3
                    })
                },
                'timestamp': datetime.now().isoformat()
            }

            # Save analysis to database
            await self._save_analysis(analysis)

            # Store in history
            self.analysis_history.append(analysis)
            if len(self.analysis_history) > 50:  # Keep last 50 analyses
                self.analysis_history.pop(0)

            self.logger.info(f"Analysis completed: momentum={score_momentum}, risk={risk_level}, emergency={emergency_detected}")
            return analysis

        except Exception as e:
            self.logger.error(f"Error in game state analysis: {e}")
            return {
                'error': str(e),
                'score_momentum': 'stable',
                'risk_level': 'medium',
                'emergency_detected': False,
                'recommended_actions': [1] if 1 in getattr(game_state, 'available_actions', []) else [],
                'confidence_score': 0.3
            }

    async def _calculate_score_momentum(self, context: GameContext) -> str:
        """Calculate if score is increasing, decreasing, or stable"""
        try:
            # Use context's built-in momentum calculation
            momentum = context.calculate_score_momentum()

            # Additional analysis if we have sufficient history
            if len(context.score_history) >= 5:
                recent_5 = context.score_history[-5:]

                # Calculate trend strength
                increases = sum(1 for i in range(1, len(recent_5)) if recent_5[i] > recent_5[i-1])
                decreases = sum(1 for i in range(1, len(recent_5)) if recent_5[i] < recent_5[i-1])

                # Strong trend detection
                if increases >= 3:
                    return 'strongly_increasing'
                elif decreases >= 3:
                    return 'strongly_decreasing'

            return momentum

        except Exception as e:
            self.logger.error(f"Error calculating score momentum: {e}")
            return 'stable'

    async def _assess_risk_level(self, context: GameContext) -> str:
        """Assess risk level based on recent actions and performance"""
        try:
            risk_factors = 0

            # High risk factors
            if context.score_momentum in ['decreasing', 'strongly_decreasing']:
                risk_factors += 2
            if context.actions_taken > 15 and context.score_progress < 0.3:
                risk_factors += 2
            if len(context.action_history) >= 3:
                recent_actions = context.action_history[-3:]
                if len(set(recent_actions)) == 1:  # Repetitive actions
                    risk_factors += 1
            if context.time_pressure:
                risk_factors += 1

            # Medium risk factors
            if context.score_progress < 0.5 and context.actions_taken > 10:
                risk_factors += 1
            if 'ACTION6' in context.action_history[-2:]:  # Recent risky actions
                risk_factors += 1

            # Low risk factors (reduce risk)
            if context.score_momentum in ['increasing', 'strongly_increasing']:
                risk_factors -= 2
            if context.score_progress > 0.7:
                risk_factors -= 1
            if context.actions_taken < 5:  # Early game
                risk_factors -= 1

            # Determine risk level
            if risk_factors >= 4:
                return 'very_high'
            elif risk_factors >= 2:
                return 'high'
            elif risk_factors <= -1:
                return 'low'
            else:
                return 'medium'

        except Exception as e:
            self.logger.error(f"Error assessing risk: {e}")
            return 'medium'

    async def _identify_opportunity_zones(self, context: GameContext) -> List[Dict[str, Any]]:
        """Identify high-value opportunity zones for ACTION6"""
        try:
            opportunity_zones = []

            # If ACTION6 is available, suggest strategic coordinates
            if 6 in context.available_actions:

                # Center zone - always a good starting point
                opportunity_zones.append({
                    'x': 32, 'y': 32,
                    'priority': 'high',
                    'reason': 'center_exploration',
                    'confidence': 0.8
                })

                # Early game exploration
                if context.actions_taken < 10:
                    opportunity_zones.extend([
                        {'x': 16, 'y': 16, 'priority': 'medium', 'reason': 'early_corner_exploration', 'confidence': 0.6},
                        {'x': 48, 'y': 48, 'priority': 'medium', 'reason': 'opposite_corner_exploration', 'confidence': 0.6}
                    ])

                # Score-based strategies
                if context.score_progress < 0.3:
                    # Low score - try more exploration
                    opportunity_zones.extend([
                        {'x': 24, 'y': 40, 'priority': 'high', 'reason': 'breakthrough_attempt', 'confidence': 0.7},
                        {'x': 40, 'y': 24, 'priority': 'high', 'reason': 'alternative_breakthrough', 'confidence': 0.7}
                    ])
                elif context.score_progress > 0.7:
                    # High score - conservative zones
                    opportunity_zones.append({
                        'x': 32, 'y': 32,
                        'priority': 'highest',
                        'reason': 'conservative_center',
                        'confidence': 0.9
                    })

                # Emergency situations - safe zones
                if context.emergency_detected:
                    opportunity_zones = [{
                        'x': 32, 'y': 32,
                        'priority': 'emergency_safe',
                        'reason': 'emergency_center_safe',
                        'confidence': 0.95
                    }]

            return opportunity_zones

        except Exception as e:
            self.logger.error(f"Error identifying opportunity zones: {e}")
            return []

    async def _detect_emergency_situation(self, context: GameContext) -> bool:
        """Detect emergency situations needing immediate recovery"""
        try:
            emergency_indicators = 0

            # Rapid score decline
            if len(context.score_history) >= 3:
                recent = [self._ensure_numeric(s) for s in context.score_history[-3:]]
                if len(recent) >= 3 and recent[0] > recent[1] > recent[2]:
                    score_decline = (recent[0] - recent[2]) / recent[0] if recent[0] > 0 else 0
                    if score_decline > 0.2:  # 20% decline
                        emergency_indicators += 2

            # Poor progress with many actions
            if context.actions_taken > 20 and context.score_progress < 0.2:
                emergency_indicators += 2

            # High risk situation
            if context.risk_level in ['high', 'very_high']:
                emergency_indicators += 1

            # Time pressure with low score
            if context.time_pressure and context.score_progress < 0.5:
                emergency_indicators += 1

            # Repetitive failing pattern
            if len(context.action_history) >= 4:
                recent_actions = context.action_history[-4:]
                if len(set(recent_actions)) <= 2 and context.score_momentum == 'decreasing':
                    emergency_indicators += 1

            # Threshold for emergency
            return emergency_indicators >= 2

        except Exception as e:
            self.logger.error(f"Error detecting emergency: {e}")
            return False

    async def _prioritize_actions(self, context: GameContext) -> List[int]:
        """Prioritize actions based on current game context"""
        try:
            if not context.available_actions:
                return []

            prioritized = []

            # Emergency situation - ultra-conservative
            if context.emergency_detected:
                # ACTION1 first (usually safest)
                if 1 in context.available_actions:
                    prioritized.append(1)
                # Other non-ACTION6 actions
                safe_actions = [a for a in context.available_actions if a != 6 and a not in prioritized]
                prioritized.extend(sorted(safe_actions))
                # ACTION6 absolute last in emergency
                if 6 in context.available_actions:
                    prioritized.append(6)

            # High risk - conservative
            elif context.risk_level in ['high', 'very_high']:
                # Prefer proven safe actions
                safe_order = [1, 2, 3, 4, 5, 7, 6]
                for action in safe_order:
                    if action in context.available_actions:
                        prioritized.append(action)

            # Near victory - protect lead
            elif context.is_near_victory:
                # Very conservative approach
                conservative_order = [1, 2, 3, 4, 5, 7, 6]
                for action in conservative_order:
                    if action in context.available_actions:
                        prioritized.append(action)

            # Early game - exploration
            elif context.actions_taken < 10:
                # Balanced exploration
                if context.score_momentum == 'increasing':
                    # Continue successful approach
                    exploration_order = [1, 6, 2, 7, 3, 4, 5]
                else:
                    # Try different approach
                    exploration_order = [6, 7, 1, 5, 2, 3, 4]

                for action in exploration_order:
                    if action in context.available_actions:
                        prioritized.append(action)

            # Time pressure - high value actions
            elif context.time_pressure:
                # Focus on potentially high-scoring actions
                high_value_order = [6, 7, 5, 1, 2, 3, 4]
                for action in high_value_order:
                    if action in context.available_actions:
                        prioritized.append(action)

            # Normal situation - balanced approach
            else:
                if context.score_momentum == 'increasing':
                    # Keep momentum
                    balanced_order = [1, 6, 2, 3, 7, 4, 5]
                elif context.score_momentum == 'decreasing':
                    # Change approach
                    balanced_order = [6, 7, 1, 5, 2, 3, 4]
                else:
                    # Stable - try to improve
                    balanced_order = [6, 1, 7, 2, 5, 3, 4]

                for action in balanced_order:
                    if action in context.available_actions:
                        prioritized.append(action)

            # Ensure all available actions are included
            for action in context.available_actions:
                if action not in prioritized:
                    prioritized.append(action)

            return prioritized

        except Exception as e:
            self.logger.error(f"Error prioritizing actions: {e}")
            return list(context.available_actions) if context.available_actions else []

    async def _save_analysis(self, analysis: dict):
        """Save analysis results to database"""
        try:
            self.save_game_state_analysis(analysis)
            self.logger.debug("Analysis saved to database")

        except Exception as e:
            self.logger.error(f"Failed to save analysis to database: {e}")

    def get_recent_analysis(self, count: int = 5) -> List[dict]:
        """Get recent analysis results"""
        return self.analysis_history[-count:] if len(self.analysis_history) >= count else self.analysis_history

    def get_trend_analysis(self) -> Dict[str, Any]:
        """Analyze trends across recent analyses"""
        try:
            if len(self.analysis_history) < 3:
                return {'insufficient_data': True}

            recent = self.analysis_history[-5:]  # Last 5 analyses

            # Momentum trends
            momentums = [a.get('score_momentum', 'stable') for a in recent]
            risk_levels = [a.get('risk_level', 'medium') for a in recent]
            emergency_count = sum(1 for a in recent if a.get('emergency_detected', False))

            return {
                'momentum_trend': momentums,
                'risk_trend': risk_levels,
                'emergency_frequency': emergency_count / len(recent),
                'trend_stability': len(set(momentums[-3:])) == 1 if len(momentums) >= 3 else False,
                'consistent_improvement': all(m in ['increasing', 'strongly_increasing'] for m in momentums[-3:])
            }

        except Exception as e:
            self.logger.error(f"Error in trend analysis: {e}")
            return {'error': str(e)}