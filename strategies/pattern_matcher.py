"""
PatternMatcher - Finds successful action sequences from game history.
Implements Prompt 6 from Claude-Code Ready Prompts.
"""
from disable_pycache import *

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import hashlib
import statistics

from .utils.strategy_base import StrategyBase
from .utils.game_context import GameContext

logger = logging.getLogger(__name__)

class PatternMatcher(StrategyBase):
    """Finds and reuses successful action sequences from game history"""

    def __init__(self, db_interface):
        super().__init__(db_interface)
        self.pattern_cache = {}
        self.successful_sequences = []
        self.pattern_weights = {
            'exact_match': 1.0,
            'similar_context': 0.8,
            'same_game_type': 0.6,
            'general_pattern': 0.4
        }

    async def find_successful_patterns(self, context: GameContext, sequence_length: int = 3) -> List[Dict[str, Any]]:
        """
        Find successful action sequences for similar game situations.

        Args:
            context: Current game context
            sequence_length: Length of action sequences to find

        Returns:
            List of successful patterns with confidence scores
        """
        try:
            self.logger.debug(f"Finding successful patterns for context: {context.game_type}")

            # Generate pattern signature for current context
            current_signature = context.get_pattern_signature()

            # Search for patterns in multiple ways
            patterns = []

            # 1. Exact context matches
            exact_patterns = await self._find_exact_context_patterns(current_signature, sequence_length)
            patterns.extend(self._weight_patterns(exact_patterns, 'exact_match'))

            # 2. Similar context matches
            similar_patterns = await self._find_similar_context_patterns(context, sequence_length)
            patterns.extend(self._weight_patterns(similar_patterns, 'similar_context'))

            # 3. Game type specific patterns
            game_type_patterns = await self._find_game_type_patterns(context.game_type, sequence_length)
            patterns.extend(self._weight_patterns(game_type_patterns, 'same_game_type'))

            # 4. General successful patterns
            general_patterns = await self._find_general_patterns(sequence_length)
            patterns.extend(self._weight_patterns(general_patterns, 'general_pattern'))

            # Deduplicate and sort by weighted score
            unique_patterns = self._deduplicate_patterns(patterns)
            sorted_patterns = sorted(unique_patterns, key=lambda x: x['weighted_score'], reverse=True)

            # Apply recency weighting
            weighted_patterns = self._apply_recency_weighting(sorted_patterns)

            self.logger.info(f"Found {len(weighted_patterns)} successful patterns")
            return weighted_patterns[:10]  # Return top 10 patterns

        except Exception as e:
            self.logger.error(f"Error finding successful patterns: {e}")
            return []

    async def recommend_action_sequence(self, context: GameContext) -> Optional[List[str]]:
        """
        Recommend action sequence based on successful patterns.

        Args:
            context: Current game context

        Returns:
            Recommended action sequence or None if no good patterns found
        """
        try:
            patterns = await self.find_successful_patterns(context, sequence_length=5)

            if not patterns:
                return None

            # Get the best pattern
            best_pattern = patterns[0]

            # Check if confidence is high enough
            if best_pattern['confidence'] < 0.6:
                self.logger.debug(f"Best pattern confidence too low: {best_pattern['confidence']}")
                return None

            # Extract action sequence
            action_sequence = best_pattern['action_sequence']

            # Validate that actions are available
            validated_sequence = self._validate_action_sequence(action_sequence, context)

            if validated_sequence:
                self.logger.info(f"Recommending pattern-based sequence: {validated_sequence}")
                return validated_sequence

            return None

        except Exception as e:
            self.logger.error(f"Error recommending action sequence: {e}")
            return None

    async def learn_successful_sequence(self, action_sequence: List[str], context: GameContext, success_metrics: Dict[str, Any]):
        """
        Learn from a successful action sequence.

        Args:
            action_sequence: The successful action sequence
            context: Game context when sequence was executed
            success_metrics: Metrics indicating success (score_change, win, etc.)
        """
        try:
            self.logger.debug(f"Learning successful sequence: {action_sequence}")

            # Calculate pattern signature
            pattern_signature = self._calculate_sequence_signature(action_sequence, context)

            # Calculate success score
            success_score = self._calculate_success_score(success_metrics)

            # Store pattern in database
            await self._store_successful_pattern(
                pattern_signature=pattern_signature,
                action_sequence=action_sequence,
                context=context,
                success_score=success_score,
                win_rate=1.0 if success_metrics.get('win', False) else 0.0,
                avg_score_improvement=success_metrics.get('score_change', 0.0)
            )

            # Update local cache
            self._update_local_cache(pattern_signature, action_sequence, success_score)

            self.logger.info(f"Learned successful pattern: {pattern_signature[:8]}...")

        except Exception as e:
            self.logger.error(f"Error learning successful sequence: {e}")

    async def avoid_failure_sequences(self, context: GameContext) -> List[str]:
        """
        Get list of action sequences to avoid based on failure patterns.

        Args:
            context: Current game context

        Returns:
            List of action sequences to avoid
        """
        try:
            # Query recent failures
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT action_sequence, win_rate, avg_score_improvement
                    FROM successful_patterns
                    WHERE win_rate < 0.3 AND avg_score_improvement < 0
                    ORDER BY last_successful DESC
                    LIMIT 20
                """)

                failure_patterns = []
                for row in cursor.fetchall():
                    try:
                        action_sequence = json.loads(row[0])
                        if len(action_sequence) <= 3:  # Focus on short failure patterns
                            failure_patterns.append(action_sequence)
                    except:
                        continue

            self.logger.debug(f"Found {len(failure_patterns)} failure patterns to avoid")
            return failure_patterns

        except Exception as e:
            self.logger.error(f"Error getting failure sequences: {e}")
            return []

    async def _find_exact_context_patterns(self, signature: str, sequence_length: int) -> List[Dict[str, Any]]:
        """Find patterns with exact context match"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT pattern_signature, action_sequence, success_context,
                           win_rate, avg_score_improvement, recency_weight
                    FROM successful_patterns
                    WHERE pattern_signature = ? AND pattern_length = ?
                    ORDER BY win_rate DESC, avg_score_improvement DESC
                    LIMIT 5
                """, (signature, sequence_length))

                patterns = []
                for row in cursor.fetchall():
                    try:
                        patterns.append({
                            'pattern_signature': row[0],
                            'action_sequence': json.loads(row[1]),
                            'success_context': json.loads(row[2]),
                            'win_rate': row[3],
                            'avg_score_improvement': row[4],
                            'recency_weight': row[5],
                            'match_type': 'exact'
                        })
                    except Exception as e:
                        self.logger.warning(f"Error parsing pattern row: {e}")
                        continue

            return patterns

        except Exception as e:
            self.logger.error(f"Error finding exact context patterns: {e}")
            return []

    async def _find_similar_context_patterns(self, context: GameContext, sequence_length: int) -> List[Dict[str, Any]]:
        """Find patterns with similar context"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()

                # Search by similar context characteristics
                score_range = self._score_to_range(context.current_score)
                momentum = context.score_momentum

                cursor.execute("""
                    SELECT pattern_signature, action_sequence, success_context,
                           win_rate, avg_score_improvement, recency_weight
                    FROM successful_patterns
                    WHERE success_context LIKE ? OR success_context LIKE ?
                    ORDER BY win_rate DESC, avg_score_improvement DESC
                    LIMIT 10
                """, (f'%{score_range}%', f'%{momentum}%'))

                patterns = []
                for row in cursor.fetchall():
                    try:
                        patterns.append({
                            'pattern_signature': row[0],
                            'action_sequence': json.loads(row[1]),
                            'success_context': json.loads(row[2]),
                            'win_rate': row[3],
                            'avg_score_improvement': row[4],
                            'recency_weight': row[5],
                            'match_type': 'similar'
                        })
                    except Exception as e:
                        continue

            return patterns

        except Exception as e:
            self.logger.error(f"Error finding similar context patterns: {e}")
            return []

    async def _find_game_type_patterns(self, game_type: str, sequence_length: int) -> List[Dict[str, Any]]:
        """Find patterns for specific game type"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT pattern_signature, action_sequence, success_context,
                           win_rate, avg_score_improvement, recency_weight
                    FROM successful_patterns
                    WHERE success_context LIKE ?
                    ORDER BY win_rate DESC, avg_score_improvement DESC
                    LIMIT 8
                """, (f'%{game_type}%',))

                patterns = []
                for row in cursor.fetchall():
                    try:
                        patterns.append({
                            'pattern_signature': row[0],
                            'action_sequence': json.loads(row[1]),
                            'success_context': json.loads(row[2]),
                            'win_rate': row[3],
                            'avg_score_improvement': row[4],
                            'recency_weight': row[5],
                            'match_type': 'game_type'
                        })
                    except Exception as e:
                        continue

            return patterns

        except Exception as e:
            self.logger.error(f"Error finding game type patterns: {e}")
            return []

    async def _find_general_patterns(self, sequence_length: int) -> List[Dict[str, Any]]:
        """Find generally successful patterns"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT pattern_signature, action_sequence, success_context,
                           win_rate, avg_score_improvement, recency_weight
                    FROM successful_patterns
                    WHERE win_rate > 0.6 AND avg_score_improvement > 5
                    ORDER BY win_rate DESC, avg_score_improvement DESC
                    LIMIT 5
                """)

                patterns = []
                for row in cursor.fetchall():
                    try:
                        patterns.append({
                            'pattern_signature': row[0],
                            'action_sequence': json.loads(row[1]),
                            'success_context': json.loads(row[2]),
                            'win_rate': row[3],
                            'avg_score_improvement': row[4],
                            'recency_weight': row[5],
                            'match_type': 'general'
                        })
                    except Exception as e:
                        continue

            return patterns

        except Exception as e:
            self.logger.error(f"Error finding general patterns: {e}")
            return []

    def _weight_patterns(self, patterns: List[Dict[str, Any]], match_type: str) -> List[Dict[str, Any]]:
        """Apply weights to patterns based on match type"""
        weight = self.pattern_weights.get(match_type, 0.5)

        for pattern in patterns:
            # Calculate base confidence
            base_confidence = (pattern['win_rate'] * 0.6 +
                             min(pattern['avg_score_improvement'] / 20.0, 1.0) * 0.4)

            # Apply match type weight
            pattern['weighted_score'] = base_confidence * weight
            pattern['confidence'] = base_confidence
            pattern['match_weight'] = weight

        return patterns

    def _deduplicate_patterns(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate patterns, keeping the best weighted score"""
        seen_signatures = {}
        unique_patterns = []

        for pattern in patterns:
            signature = pattern['pattern_signature']
            if signature not in seen_signatures or pattern['weighted_score'] > seen_signatures[signature]['weighted_score']:
                seen_signatures[signature] = pattern

        return list(seen_signatures.values())

    def _apply_recency_weighting(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply recency weighting to patterns"""
        for pattern in patterns:
            recency_weight = pattern.get('recency_weight', 1.0)
            pattern['final_score'] = pattern['weighted_score'] * recency_weight
            pattern['confidence'] = min(1.0, pattern['confidence'] * recency_weight)

        return sorted(patterns, key=lambda x: x['final_score'], reverse=True)

    def _validate_action_sequence(self, action_sequence: List[str], context: GameContext) -> Optional[List[str]]:
        """Validate that action sequence can be executed in current context"""
        try:
            validated_sequence = []

            for action in action_sequence:
                # Extract action number
                if action.startswith('ACTION'):
                    try:
                        action_num = int(action.replace('ACTION', '').split('(')[0])
                        if action_num in context.available_actions:
                            validated_sequence.append(action)
                        else:
                            # Try to find substitute action
                            substitute = self._find_substitute_action(action_num, context.available_actions)
                            if substitute:
                                validated_sequence.append(f"ACTION{substitute}")
                            else:
                                break  # Can't continue sequence
                    except:
                        break
                else:
                    # Unknown action format
                    break

            # Return sequence if we got at least 2 valid actions
            return validated_sequence if len(validated_sequence) >= 2 else None

        except Exception as e:
            self.logger.error(f"Error validating action sequence: {e}")
            return None

    def _find_substitute_action(self, desired_action: int, available_actions: List[int]) -> Optional[int]:
        """Find substitute action if desired action not available"""
        try:
            # Simple substitution rules
            substitutes = {
                1: [2, 3, 4],
                2: [1, 3, 4],
                3: [1, 2, 4],
                4: [1, 2, 3],
                5: [7, 1, 2],
                6: [7, 5, 1],
                7: [5, 6, 1]
            }

            if desired_action in substitutes:
                for substitute in substitutes[desired_action]:
                    if substitute in available_actions:
                        return substitute

            # If no specific substitute, return any available action
            return available_actions[0] if available_actions else None

        except Exception as e:
            return None

    def _calculate_sequence_signature(self, action_sequence: List[str], context: GameContext) -> str:
        """Calculate signature for action sequence"""
        try:
            signature_data = {
                'actions': action_sequence,
                'game_type': context.game_type,
                'score_range': self._score_to_range(context.current_score),
                'momentum': context.score_momentum,
                'sequence_length': len(action_sequence)
            }

            signature_str = json.dumps(signature_data, sort_keys=True)
            return hashlib.md5(signature_str.encode()).hexdigest()[:16]

        except Exception as e:
            self.logger.error(f"Error calculating sequence signature: {e}")
            return 'error_signature'

    def _calculate_success_score(self, success_metrics: Dict[str, Any]) -> float:
        """Calculate success score from metrics"""
        try:
            score = 0.0

            # Win bonus
            if success_metrics.get('win', False):
                score += 10.0

            # Score improvement
            score_change = success_metrics.get('score_change', 0.0)
            score += max(0, score_change)

            # Efficiency bonus (less actions taken)
            actions_taken = success_metrics.get('actions_taken', 20)
            efficiency_bonus = max(0, (25 - actions_taken) * 0.5)
            score += efficiency_bonus

            return score

        except Exception as e:
            self.logger.error(f"Error calculating success score: {e}")
            return 0.0

    async def _store_successful_pattern(self, pattern_signature: str, action_sequence: List[str],
                                      context: GameContext, success_score: float,
                                      win_rate: float, avg_score_improvement: float):
        """Store successful pattern in database"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()

                # Check if pattern exists
                cursor.execute("""
                    SELECT win_rate, avg_score_improvement, pattern_length
                    FROM successful_patterns
                    WHERE pattern_signature = ?
                """, (pattern_signature,))

                existing = cursor.fetchone()

                success_context = {
                    'game_type': context.game_type,
                    'score_range': self._score_to_range(context.current_score),
                    'momentum': context.score_momentum,
                    'actions_taken': context.actions_taken
                }

                if existing:
                    # Update existing pattern
                    old_win_rate, old_avg_improvement, pattern_length = existing
                    new_win_rate = (old_win_rate + win_rate) / 2
                    new_avg_improvement = (old_avg_improvement + avg_score_improvement) / 2

                    cursor.execute("""
                        UPDATE successful_patterns
                        SET win_rate = ?, avg_score_improvement = ?, recency_weight = ?, last_successful = ?
                        WHERE pattern_signature = ?
                    """, (new_win_rate, new_avg_improvement, 1.0, datetime.now(), pattern_signature))

                else:
                    # Insert new pattern
                    cursor.execute("""
                        INSERT INTO successful_patterns
                        (pattern_signature, action_sequence, success_context, win_rate,
                         avg_score_improvement, pattern_length, recency_weight)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        pattern_signature,
                        json.dumps(action_sequence),
                        json.dumps(success_context),
                        win_rate,
                        avg_score_improvement,
                        len(action_sequence),
                        1.0
                    ))

                conn.commit()

        except Exception as e:
            self.logger.error(f"Error storing successful pattern: {e}")

    def _update_local_cache(self, pattern_signature: str, action_sequence: List[str], success_score: float):
        """Update local pattern cache"""
        try:
            self.pattern_cache[pattern_signature] = {
                'action_sequence': action_sequence,
                'success_score': success_score,
                'last_updated': datetime.now()
            }

            # Keep cache size manageable
            if len(self.pattern_cache) > 200:
                # Remove oldest entries
                sorted_items = sorted(self.pattern_cache.items(),
                                    key=lambda x: x[1]['last_updated'])
                for key, _ in sorted_items[:50]:  # Remove oldest 50
                    del self.pattern_cache[key]

        except Exception as e:
            self.logger.error(f"Error updating local cache: {e}")

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

    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get pattern matching statistics"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) as total_patterns,
                           AVG(win_rate) as avg_win_rate,
                           AVG(avg_score_improvement) as avg_improvement,
                           MAX(last_successful) as latest_pattern
                    FROM successful_patterns
                """)

                row = cursor.fetchone()
                if row:
                    return {
                        'total_patterns': row[0],
                        'avg_win_rate': row[1] or 0.0,
                        'avg_improvement': row[2] or 0.0,
                        'latest_pattern': row[3],
                        'cache_size': len(self.pattern_cache)
                    }

            return {'total_patterns': 0, 'cache_size': len(self.pattern_cache)}

        except Exception as e:
            self.logger.error(f"Error getting pattern statistics: {e}")
            return {'error': str(e)}