"""
ActionFeedbackLearner - Learns from each action's immediate consequences.
Implements Prompt 2 from Claude-Code Ready Prompts.
"""
from disable_pycache import *

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import hashlib
import statistics

from .utils.strategy_base import StrategyBase
from .utils.game_context import GameContext

logger = logging.getLogger(__name__)

class ActionFeedbackLearner(StrategyBase):
    """Learns from each action's immediate consequences and builds success/failure patterns"""

    def _safe_score_subtract(self, score1, score2):
        """Safely subtract two scores, handling lists and non-numeric types"""
        # Ensure first score is numeric
        if isinstance(score1, (list, tuple)):
            score1 = score1[0] if len(score1) > 0 else 0.0
        elif not isinstance(score1, (int, float)):
            score1 = 0.0

        # Ensure second score is numeric
        if isinstance(score2, (list, tuple)):
            score2 = score2[0] if len(score2) > 0 else 0.0
        elif not isinstance(score2, (int, float)):
            score2 = 0.0

        return float(score1) - float(score2)

    def __init__(self, db_interface):
        super().__init__(db_interface)
        self.pattern_cache = {}
        self.recent_patterns = []

    async def learn_from_action(self, action: str, pre_state: Any, post_state: Any) -> Dict[str, Any]:
        """
        Learn from an action's immediate consequences.

        Args:
            action: Action that was taken
            pre_state: Game state before action
            post_state: Game state after action

        Returns:
            Learning results and insights
        """
        try:
            self.logger.debug(f"Learning from action: {action}")

            # Extract meaningful data from states
            pre_context = self._extract_state_context(pre_state)
            post_context = self._extract_state_context(post_state)

            # Calculate immediate impact
            score_change = self._safe_score_subtract(post_context['score'], pre_context['score'])
            success_indicator = self._determine_success(pre_context, post_context, score_change)

            # Create action pattern
            pattern = self._create_action_pattern(action, pre_context, post_context)

            # Store pattern in database
            await self._store_pattern(pattern, success_indicator, score_change)

            # Update local cache
            self._update_pattern_cache(pattern, success_indicator, score_change)

            # Generate insights
            insights = await self._generate_learning_insights(action, pattern, success_indicator, score_change)

            self.logger.info(f"Learned from {action}: score_change={score_change:.2f}, success={success_indicator}")

            return {
                'action': action,
                'score_change': score_change,
                'success': success_indicator,
                'pattern_signature': pattern['signature'],
                'insights': insights,
                'confidence': insights.get('confidence', 0.5)
            }

        except Exception as e:
            self.logger.error(f"Error learning from action {action}: {e}")
            return {
                'action': action,
                'error': str(e),
                'success': False,
                'confidence': 0.0
            }

    async def get_success_probability(self, action: str, context: GameContext) -> float:
        """
        Get success probability for an action in given context.

        Args:
            action: Action to evaluate
            context: Current game context

        Returns:
            Probability of success (0.0 to 1.0)
        """
        try:
            # Create pattern signature for current context
            current_pattern = self._create_context_pattern(action, context)
            pattern_signature = current_pattern['signature']

            # Check cache first
            if pattern_signature in self.pattern_cache:
                cached_data = self.pattern_cache[pattern_signature]
                return cached_data.get('success_probability', 0.5)

            # Query database for similar patterns
            similar_patterns = await self._get_similar_patterns(pattern_signature, action)

            if not similar_patterns:
                return 0.5  # Neutral probability for unknown patterns

            # Calculate weighted success probability
            total_weight = 0
            weighted_success = 0

            for pattern in similar_patterns:
                # Weight based on pattern frequency and recency
                weight = pattern['frequency'] * pattern['recency_weight']
                total_weight += weight

                if pattern['success_indicator']:
                    weighted_success += weight

            success_probability = weighted_success / total_weight if total_weight > 0 else 0.5

            # Store in cache
            self.pattern_cache[pattern_signature] = {
                'success_probability': success_probability,
                'last_updated': datetime.now(),
                'sample_size': len(similar_patterns)
            }

            return success_probability

        except Exception as e:
            self.logger.error(f"Error calculating success probability for {action}: {e}")
            return 0.5

    async def avoid_recent_failure_patterns(self, available_actions: List[int], context: GameContext) -> List[int]:
        """
        Filter out actions that match recent failure patterns.

        Args:
            available_actions: List of available action numbers
            context: Current game context

        Returns:
            Filtered list of actions avoiding known failure patterns
        """
        try:
            filtered_actions = []

            for action_num in available_actions:
                action_str = f"ACTION{action_num}"

                # Get success probability
                success_prob = await self.get_success_probability(action_str, context)

                # Check against recent failure patterns
                is_recent_failure = await self._is_recent_failure_pattern(action_str, context)

                # Include action if it has decent success rate and isn't a recent failure
                if success_prob >= 0.3 and not is_recent_failure:
                    filtered_actions.append(action_num)

            # If all actions filtered out, return safest available actions
            if not filtered_actions:
                # Return actions with highest success probabilities
                action_probs = []
                for action_num in available_actions:
                    action_str = f"ACTION{action_num}"
                    prob = await self.get_success_probability(action_str, context)
                    action_probs.append((action_num, prob))

                # Sort by probability and take top half
                action_probs.sort(key=lambda x: x[1], reverse=True)
                filtered_actions = [action_num for action_num, _ in action_probs[:max(1, len(action_probs)//2)]]

            return filtered_actions

        except Exception as e:
            self.logger.error(f"Error filtering failure patterns: {e}")
            return available_actions  # Return original list on error

    def _extract_state_context(self, state: Any) -> Dict[str, Any]:
        """Extract relevant context from game state"""
        try:
            # Handle different state formats
            if hasattr(state, 'score'):
                score = state.score
            elif isinstance(state, dict) and 'score' in state:
                score = state['score']
            else:
                score = 0.0

            # Ensure score is numeric
            if isinstance(score, (list, tuple)):
                score = score[0] if len(score) > 0 else 0.0
            score = float(score)

            # Extract other relevant data
            game_state = getattr(state, 'state', 'NOT_FINISHED')
            available_actions = getattr(state, 'available_actions', [])
            frame_data = getattr(state, 'frame', {})

            return {
                'score': score,
                'game_state': game_state,
                'available_actions': available_actions,
                'frame_hash': self._hash_frame_data(frame_data),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error extracting state context: {e}")
            return {
                'score': 0.0,
                'game_state': 'UNKNOWN',
                'available_actions': [],
                'frame_hash': 'unknown',
                'timestamp': datetime.now().isoformat()
            }

    def _determine_success(self, pre_context: Dict, post_context: Dict, score_change: float) -> bool:
        """Determine if an action was successful"""
        try:
            # Primary success indicator: positive score change
            if score_change > 0:
                return True

            # Secondary indicators
            # Game state progression
            if (pre_context['game_state'] == 'NOT_FINISHED' and
                post_context['game_state'] == 'WIN'):
                return True

            # No negative consequences with neutral score
            if (score_change == 0 and
                post_context['game_state'] != 'GAME_OVER' and
                pre_context['game_state'] != 'GAME_OVER'):
                return True  # Neutral but safe

            # Frame change (something happened)
            if (score_change >= 0 and
                pre_context['frame_hash'] != post_context['frame_hash']):
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error determining success: {e}")
            return False

    def _create_action_pattern(self, action: str, pre_context: Dict, post_context: Dict) -> Dict[str, Any]:
        """Create a pattern representation of the action and context"""
        try:
            # Normalize action
            action_normalized = action.replace('_callable', '').split('(')[0]

            # Create pattern data
            pattern_data = {
                'action': action_normalized,
                'pre_score_range': self._score_to_range(pre_context['score']),
                'available_actions': sorted(pre_context['available_actions']),
                'game_state': pre_context['game_state'],
                'frame_context': pre_context['frame_hash'][:8],  # First 8 chars of hash
                'score_change_range': self._score_change_to_range(self._safe_score_subtract(post_context['score'], pre_context['score']))
            }

            # Create signature
            pattern_str = json.dumps(pattern_data, sort_keys=True)
            signature = hashlib.md5(pattern_str.encode()).hexdigest()[:16]

            return {
                'signature': signature,
                'data': pattern_data,
                'full_pattern': pattern_str
            }

        except Exception as e:
            self.logger.error(f"Error creating action pattern: {e}")
            return {
                'signature': 'error_pattern',
                'data': {},
                'full_pattern': '{}'
            }

    def _create_context_pattern(self, action: str, context: GameContext) -> Dict[str, Any]:
        """Create pattern from current context for prediction"""
        try:
            pattern_data = {
                'action': action.replace('_callable', '').split('(')[0],
                'pre_score_range': self._score_to_range(context.current_score),
                'available_actions': sorted(context.available_actions),
                'game_state': context.game_state,
                'momentum': context.score_momentum,
                'risk_level': context.risk_level
            }

            pattern_str = json.dumps(pattern_data, sort_keys=True)
            signature = hashlib.md5(pattern_str.encode()).hexdigest()[:16]

            return {
                'signature': signature,
                'data': pattern_data
            }

        except Exception as e:
            self.logger.error(f"Error creating context pattern: {e}")
            return {
                'signature': 'error_pattern',
                'data': {}
            }

    def _score_to_range(self, score: float) -> str:
        """Convert score to range category"""
        try:
            if score < 10:
                return 'very_low'
            elif score < 30:
                return 'low'
            elif score < 60:
                return 'medium'
            elif score < 80:
                return 'high'
            else:
                return 'very_high'
        except:
            return 'unknown'

    def _score_change_to_range(self, change: float) -> str:
        """Convert score change to range category"""
        try:
            if change < -10:
                return 'large_decrease'
            elif change < -2:
                return 'decrease'
            elif change <= 2:
                return 'neutral'
            elif change <= 10:
                return 'increase'
            else:
                return 'large_increase'
        except:
            return 'unknown'

    def _hash_frame_data(self, frame_data: Any) -> str:
        """Create hash of frame data for comparison"""
        try:
            if not frame_data:
                return 'empty_frame'

            # Convert to string representation
            frame_str = json.dumps(frame_data, sort_keys=True) if isinstance(frame_data, dict) else str(frame_data)
            return hashlib.md5(frame_str.encode()).hexdigest()[:16]

        except Exception as e:
            return 'error_frame'

    async def _store_pattern(self, pattern: Dict, success_indicator: bool, score_change: float):
        """Store pattern in database"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()

                # Check if pattern already exists
                cursor.execute("""
                    SELECT pattern_frequency, confidence_score
                    FROM action_feedback_patterns
                    WHERE action_sequence = ?
                """, (pattern['signature'],))

                existing = cursor.fetchone()

                if existing:
                    # Update existing pattern
                    old_frequency, old_confidence = existing
                    new_frequency = old_frequency + 1

                    # Update confidence based on success
                    confidence_adjustment = 0.1 if success_indicator else -0.1
                    new_confidence = max(0.0, min(1.0, old_confidence + confidence_adjustment))

                    cursor.execute("""
                        UPDATE action_feedback_patterns
                        SET pattern_frequency = ?, confidence_score = ?, last_seen = ?
                        WHERE action_sequence = ?
                    """, (new_frequency, new_confidence, datetime.now(), pattern['signature']))

                else:
                    # Insert new pattern
                    cursor.execute("""
                        INSERT INTO action_feedback_patterns
                        (action_sequence, pre_state_context, post_state_context,
                         success_indicator, score_change, pattern_frequency, confidence_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        pattern['signature'],
                        json.dumps(pattern['data']),
                        json.dumps({'score_change': score_change}),
                        success_indicator,
                        score_change,
                        1,
                        0.6 if success_indicator else 0.4
                    ))

                conn.commit()

        except Exception as e:
            self.logger.error(f"Error storing pattern: {e}")

    def _update_pattern_cache(self, pattern: Dict, success_indicator: bool, score_change: float):
        """Update local pattern cache"""
        try:
            signature = pattern['signature']

            if signature in self.pattern_cache:
                cached = self.pattern_cache[signature]
                # Update running averages
                old_prob = cached.get('success_probability', 0.5)
                old_samples = cached.get('sample_size', 0)

                new_samples = old_samples + 1
                new_prob = (old_prob * old_samples + (1.0 if success_indicator else 0.0)) / new_samples

                self.pattern_cache[signature] = {
                    'success_probability': new_prob,
                    'sample_size': new_samples,
                    'avg_score_change': score_change,
                    'last_updated': datetime.now()
                }
            else:
                self.pattern_cache[signature] = {
                    'success_probability': 1.0 if success_indicator else 0.0,
                    'sample_size': 1,
                    'avg_score_change': score_change,
                    'last_updated': datetime.now()
                }

            # Keep cache size manageable
            if len(self.pattern_cache) > 1000:
                # Remove oldest entries
                sorted_items = sorted(self.pattern_cache.items(),
                                    key=lambda x: x[1]['last_updated'])
                for key, _ in sorted_items[:100]:  # Remove oldest 100
                    del self.pattern_cache[key]

        except Exception as e:
            self.logger.error(f"Error updating pattern cache: {e}")

    async def _get_similar_patterns(self, pattern_signature: str, action: str) -> List[Dict]:
        """Get similar patterns from database"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()

                # First try exact match
                cursor.execute("""
                    SELECT action_sequence, pre_state_context, success_indicator,
                           score_change, pattern_frequency, confidence_score
                    FROM action_feedback_patterns
                    WHERE action_sequence = ?
                """, (pattern_signature,))

                exact_matches = cursor.fetchall()

                if exact_matches:
                    results = []
                    for row in exact_matches:
                        results.append({
                            'signature': row[0],
                            'context': json.loads(row[1]),
                            'success_indicator': row[2],
                            'score_change': row[3],
                            'frequency': row[4],
                            'recency_weight': 1.0  # Exact matches get full weight
                        })
                    return results

                # If no exact matches, try action-based similarity
                cursor.execute("""
                    SELECT action_sequence, pre_state_context, success_indicator,
                           score_change, pattern_frequency, confidence_score
                    FROM action_feedback_patterns
                    WHERE pre_state_context LIKE ?
                    ORDER BY confidence_score DESC
                    LIMIT 10
                """, (f'%{action}%',))

                similar_matches = cursor.fetchall()
                results = []

                for row in similar_matches:
                    results.append({
                        'signature': row[0],
                        'context': json.loads(row[1]),
                        'success_indicator': row[2],
                        'score_change': row[3],
                        'frequency': row[4],
                        'recency_weight': 0.7  # Similar matches get reduced weight
                    })

            return results

        except Exception as e:
            self.logger.error(f"Error getting similar patterns: {e}")
            return []

    async def _is_recent_failure_pattern(self, action: str, context: GameContext) -> bool:
        """Check if action matches recent failure patterns"""
        try:
            # Check recent patterns (last 5 actions in history)
            if len(context.action_history) < 2:
                return False

            recent_actions = context.action_history[-5:]

            # Count recent failures of this action
            action_failures = 0
            for hist_action in recent_actions:
                if hist_action.startswith(action.split('(')[0]):
                    # This is a pattern we should check
                    success_prob = await self.get_success_probability(hist_action, context)
                    if success_prob < 0.3:
                        action_failures += 1

            # If more than 50% of recent uses failed, consider it a failure pattern
            return action_failures > len(recent_actions) * 0.5

        except Exception as e:
            self.logger.error(f"Error checking recent failure patterns: {e}")
            return False

    async def _generate_learning_insights(self, action: str, pattern: Dict, success: bool, score_change: float) -> Dict[str, Any]:
        """Generate insights from the learning process"""
        try:
            insights = {
                'pattern_novelty': pattern['signature'] not in self.pattern_cache,
                'score_impact': 'positive' if score_change > 0 else 'negative' if score_change < 0 else 'neutral',
                'action_effectiveness': 'effective' if success else 'ineffective',
                'confidence': 0.7 if success else 0.3
            }

            # Check for patterns in recent learning
            if len(self.recent_patterns) >= 3:
                recent_successes = [p['success'] for p in self.recent_patterns[-3:]]
                insights['recent_trend'] = 'improving' if sum(recent_successes) >= 2 else 'declining'

            # Store this pattern for trend analysis
            self.recent_patterns.append({
                'action': action,
                'success': success,
                'score_change': score_change,
                'timestamp': datetime.now()
            })

            # Keep only recent patterns
            if len(self.recent_patterns) > 20:
                self.recent_patterns.pop(0)

            return insights

        except Exception as e:
            self.logger.error(f"Error generating insights: {e}")
            return {'confidence': 0.5}

    def get_learning_summary(self) -> Dict[str, Any]:
        """Get summary of learning progress"""
        try:
            if not self.recent_patterns:
                return {'status': 'no_data'}

            recent = self.recent_patterns[-10:]  # Last 10 patterns

            success_rate = sum(1 for p in recent if p['success']) / len(recent)
            avg_score_change = statistics.mean([p['score_change'] for p in recent])

            return {
                'total_patterns_learned': len(self.pattern_cache),
                'recent_success_rate': success_rate,
                'avg_recent_score_change': avg_score_change,
                'learning_trend': 'positive' if success_rate > 0.5 else 'negative',
                'cache_size': len(self.pattern_cache)
            }

        except Exception as e:
            self.logger.error(f"Error getting learning summary: {e}")
            return {'status': 'error', 'error': str(e)}