"""
Core Gameplay Logic

Provides the fundamental gameplay loop and decision-making logic.
Contains only essential game mechanics without architect/governor/director complexity.

Enhanced with pattern learning (Rule 10: integrated, not new files):
- Captures winning sequences
- Discovers and reuses patterns
- Learns from every game
"""

import asyncio
import logging
import json
import uuid
import numpy as np
from typing import Dict, Any, List, Optional, Callable, Tuple
from collections import Counter
import random
from datetime import datetime

from game_session_manager import GameSessionManager
from action_handler import ActionHandler
from arc_api_client import GameState
from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


class GameplayEngine:
    """Core engine for playing ARC games with integrated pattern learning."""

    def __init__(self, api_key: Optional[str] = None, db_path: str = "core_data.db"):
        """Initialize gameplay engine.

        Args:
            api_key: ARC API key
            db_path: Database file path
        """
        self.session_manager = GameSessionManager(api_key, db_path)
        self.action_handler = ActionHandler(self.session_manager)
        self.db = DatabaseInterface(db_path)  # Pattern learning database access
        self.game_config = {
            'max_actions_per_level': 100,  # Max actions per level (game can have multiple levels)
            'max_total_actions': 1500,  # Max total actions across all levels
            'action_timeout': 30.0,
            'strategy': 'balanced',
            'enable_random_exploration': True,
            'coordinate_retry_limit': 3,
            'enable_pattern_learning': True,  # Toggle pattern learning
            'learning_mode': 'smart_exploration',  # 'exploit', 'explore', 'smart_exploration'
            
            # Diversity-focused settings (generalization over specialization)
            'diversity_mode': False,              # Enable diversity and generalization focus
            'max_repeats_per_game': 5,            # Limit game repetition (diversity mode)
            'enforce_game_diversity': False,       # Prevent game overfitting
            'novel_game_priority': 1.0,           # Priority weight for unseen games
        }

    def configure(self, **config):
        """Update game configuration.

        Args:
            **config: Configuration parameters to update
        """
        self.game_config.update(config)
        logger.info(f"Updated game config: {config}")

    async def play_single_game(self, game_id: str,
                              action_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Play a single game to completion with optional pattern learning.

        Args:
            game_id: Game ID to play
            action_callback: Optional callback function for custom action selection

        Returns:
            Game results dictionary
        """
        logger.info(f"Starting game: {game_id}")

        # Start session if not already running
        if not self.session_manager.is_running:
            await self.session_manager.start_session(game_id=game_id)
        
        # Create game
        game_data = await self.session_manager.create_game(game_id)
        game_state = GameState.from_dict(game_data)
        
        # Pattern Learning: Check for known winning sequence (Rule 10: integrated)
        # Check AFTER game creation so we have the initial frame
        known_sequence = None
        if self.game_config.get('enable_pattern_learning', True):
            learning_mode = self.game_config.get('learning_mode', 'smart_exploration')
            
            if learning_mode in ['exploit', 'smart_exploration']:
                try:
                    known_sequence = self._get_best_sequence_for_game(
                        game_id, 
                        level_number=1, 
                        current_frame=game_state.frame
                    )
                    
                    if known_sequence:
                        logger.info(f"🎯 Found known winning sequence for {game_id} level 1, will attempt inline replay")
                except Exception as e:
                    logger.debug(f"Pattern learning lookup error: {e}")
        
        try:
            # If we have a known sequence, try to replay it INLINE (no separate game)
            if known_sequence:
                replay_result = await self._replay_sequence_inline(
                    game_state, 
                    known_sequence
                )
                
                # Update game_state from replay result
                if replay_result:
                    game_state = replay_result['game_state']
                    replay_success = replay_result['success']
                    
                    if replay_success and game_state.state == "WIN":
                        # Full win from replay! Finish and return
                        await self.session_manager.finish_game(game_state.state, game_state.score)
                        
                        return {
                            'game_id': game_id,
                            'final_state': game_state.state,
                            'final_score': game_state.score,
                            'actions_taken': len(json.loads(known_sequence['action_sequence'])),
                            'win': True,
                            'method': 'pattern_replay',
                            'sequence_id': known_sequence['sequence_id']
                        }
                    elif replay_success:
                        logger.info(f"✅ Partial replay success, continuing to next level")
                    else:
                        logger.info(f"⚠️ Sequence replay failed, falling back to exploration")
                        # Continue with normal exploration below

            action_count = 0
            level_action_count = 0  # Track actions per level
            start_time = datetime.now()
            previous_score = 0.0  # Track score for level completion detection
            level_completions = 0  # Track how many levels completed
            current_level = 1
            level_start_action = 0  # Track where each level starts

            # Game loop
            while (game_state.state == "NOT_FINISHED" and
                   action_count < self.game_config['max_total_actions']):

                # Check if session is still active (graceful shutdown detection)
                if not self.session_manager.is_running:
                    logger.info(f"⚠️ Session no longer running, ending game gracefully")
                    break

                try:
                    # Update action handler with level progress for dynamic spam tolerance
                    self.action_handler.update_level_progress(
                        level_action_count, 
                        self.game_config['max_actions_per_level']
                    )
                    
                    # Store previous score before action
                    previous_score = game_state.score
                    
                    # Select action
                    if action_callback:
                        action_result = await action_callback(game_state, self.action_handler)
                        if isinstance(action_result, GameState):
                            game_state = action_result
                        elif isinstance(action_result, str):
                            game_state = await self._execute_action(action_result, game_state)
                        else:
                            raise ValueError(f"Invalid action callback result: {action_result}")
                    else:
                        # Use default action selection
                        action = await self._select_action(game_state)
                        game_state = await self._execute_action(action, game_state)

                    action_count += 1
                    level_action_count += 1
                    
                    # Check for significant score increase (level completion)
                    score_increase = game_state.score - previous_score
                    if score_increase >= 0.5:  # Significant score increase (usually +1.0 per level)
                        level_completions += 1
                        logger.info(f"🎉 Level {current_level} completed! Score: {previous_score} → {game_state.score} (+{score_increase})")
                        logger.info(f"📊 Level {current_level} stats: {level_action_count} actions")
                        
                        # Pattern Learning: ONLY capture if this is a VERIFIED level win
                        # (score increased AND game is still running, meaning level truly completed)
                        if (self.game_config.get('enable_pattern_learning', True) and 
                            game_state.state == "NOT_FINISHED" and 
                            score_increase >= 1.0):  # Full level completion
                            
                            sequence_id = self._capture_winning_sequence(
                                game_id, 
                                game_state.score, 
                                level_number=current_level,
                                reason=f"level_{current_level}_win"
                            )
                            if sequence_id:
                                logger.info(f"✅ Captured level {current_level} winning sequence: {sequence_id}")
                        
                        # Move to next level
                        current_level += 1
                        level_action_count = 0  # Reset level action counter
                        level_start_action = action_count  # Mark where this level starts
                        
                        # Check if we have a winning sequence for the NEW level
                        if self.game_config.get('enable_pattern_learning', True):
                            next_level_sequence = self._get_best_sequence_for_game(game_id, current_level)
                            if next_level_sequence:
                                logger.info(f"🎯 Found winning sequence for level {current_level}, attempting replay...")
                                # Try to replay just this level's sequence
                                # Note: This would need frame state management for mid-game replay
                                # For now, log that we have it available for next full game
                    
                    # Check if exceeded max actions for this level
                    if level_action_count >= self.game_config['max_actions_per_level']:
                        logger.warning(f"⏱️ Reached max actions ({self.game_config['max_actions_per_level']}) for level {current_level}")
                        logger.info(f"Level {current_level} timed out - continuing with remaining game actions if available")
                        
                        # Don't break! Just reset level counter and continue trying
                        # The game should only end when:
                        # 1. Total action limit reached (max_total_actions)
                        # 2. Game state is WIN or GAME_OVER
                        # 3. API returns finished state
                        
                        # Reset level action counter to allow continued play
                        level_action_count = 0
                        current_level += 1  # Move to "next level" tracking (even if not truly completed)
                    
                    logger.debug(f"Action {action_count} (Level {current_level}-{level_action_count}): State={game_state.state}, Score={game_state.score}")

                    # Check for completion
                    if game_state.state in ["WIN", "GAME_OVER"]:
                        break

                except RuntimeError as e:
                    # Handle session shutdown gracefully
                    if "No active session" in str(e) or "No active" in str(e):
                        logger.info(f"⚠️ Session shutdown detected during action {action_count}, ending game gracefully")
                        break
                    else:
                        logger.error(f"Runtime error in action {action_count}: {e}", exc_info=True)
                        break
                except Exception as e:
                    logger.error(f"Error in action {action_count}: {e}", exc_info=True)
                    # Continue with next action unless it's a critical error
                    if "authentication" in str(e).lower() or "api_key" in str(e).lower():
                        break
                    # Also break on session/client errors
                    if "session" in str(e).lower() or "client" in str(e).lower():
                        logger.info(f"⚠️ Session/client error detected, ending game gracefully")
                        break

            # Calculate results
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            results = {
                'game_id': game_id,
                'final_state': game_state.state,
                'final_score': game_state.score,
                'actions_taken': action_count,
                'duration_seconds': duration,
                'win': game_state.state == "WIN",
                'level_completions': level_completions,
                'levels_attempted': current_level,
                'start_time': start_time,
                'end_time': end_time
            }

            # Diversity Mode: Track game diversity (Rule 10: integrated, Rule 2: database-only)
            if self.game_config.get('diversity_mode'):
                self._track_game_diversity(game_id, game_state.score, action_count)

            # Finish game in session manager
            await self.session_manager.finish_game(game_state.state, game_state.score)

            # Pattern Learning: Capture final WIN sequence (Rule 2: Database-only)
            if results['win'] and self.game_config.get('enable_pattern_learning', True):
                # ONLY capture on actual WIN state
                if game_state.state == "WIN":
                    sequence_id = self._capture_winning_sequence(
                        game_id, 
                        game_state.score,
                        level_number=current_level,
                        reason="full_game_win"
                    )
                    if sequence_id:
                        results['learned_sequence_id'] = sequence_id
                        logger.info(f"✅ Captured full game winning sequence: {sequence_id}")

            logger.info(f"Game {game_id} completed: {game_state.state}, Score: {game_state.score}, "
                       f"Actions: {action_count}, Levels Completed: {level_completions}/{current_level}")
            return results

        except Exception as e:
            logger.error(f"Error playing game {game_id}: {e}")
            # Still try to finish the game gracefully
            try:
                await self.session_manager.finish_game("ERROR", 0.0)
            except:
                pass
            raise

    async def _select_action(self, game_state: GameState) -> str:
        """Select the next action to take.
        
        Uses meta-learning to discover patterns before falling back to default strategy.

        Args:
            game_state: Current game state

        Returns:
            Action to take
        """
        # Try meta-learning pattern detection first
        if (self.game_config.get('enable_pattern_learning', True) and 
            game_state.frame is not None):
            
            try:
                # Convert frame to numpy array if needed
                frame = game_state.frame
                if not isinstance(frame, np.ndarray):
                    frame = np.array(frame)
                
                pattern_result = self._meta_learn_pattern_from_frame(frame)
                
                if pattern_result and pattern_result.get('confidence', 0) > 0.5:
                    logger.info(f"🧠 Meta-learner detected pattern: {pattern_result['pattern_type']}")
                    logger.info(f"   Rule: {pattern_result['rule']['type']}, Confidence: {pattern_result['confidence']:.2f}")
                    
                    actions = pattern_result.get('actions', [])
                    if actions:
                        # Store the discovered pattern for future use
                        self._store_discovered_pattern(pattern_result)
                        
                        # Execute first action from the pattern
                        first_action = actions[0]
                        if first_action['type'] == 'ACTION6':
                            coord = first_action['coordinate']
                            logger.info(f"🎯 Applying meta-learned pattern: ACTION6 at {coord}")
                            logger.info(f"   Reason: {first_action['reason']}")
                            
                            # Store remaining actions for next iterations
                            if not hasattr(self, '_pattern_action_queue'):
                                self._pattern_action_queue = []
                            self._pattern_action_queue = actions[1:]  # Queue remaining actions
                            
                            return "ACTION6"  # Will be executed with stored coordinates
                            
            except Exception as e:
                logger.debug(f"Meta-learning error (falling back to default): {e}")
        
        # Check if we have queued pattern actions
        if hasattr(self, '_pattern_action_queue') and self._pattern_action_queue:
            next_action = self._pattern_action_queue.pop(0)
            if next_action['type'] == 'ACTION6':
                logger.info(f"🎯 Continuing pattern execution: ACTION6 at {next_action['coordinate']}")
                return "ACTION6"
        
        # Fall back to default action selection
        strategy = self.game_config.get('strategy', 'balanced')
        return await self.action_handler.smart_action_selection(game_state, strategy)

    async def _execute_action(self, action: str, game_state: GameState) -> GameState:
        """Execute an action.

        Args:
            action: Action to execute (string like "ACTION1" or int like 1)
            game_state: Current game state

        Returns:
            New game state
        """
        # Normalize action to string format if it's an integer
        if isinstance(action, int):
            action = f"ACTION{action}"
        
        if action == "ACTION6":
            # Check if we have meta-learned coordinates to use
            if hasattr(self, '_pattern_action_queue') and self._pattern_action_queue:
                # Use coordinates from meta-learning
                next_action = self._pattern_action_queue[0]  # Peek at next action
                if next_action['type'] == 'ACTION6':
                    x, y = next_action['coordinate']
                    reason = next_action['reason']
                    logger.info(f"ACTION6 at ({x}, {y}): {reason}")
                else:
                    # Fall back to smart coordinates
                    x, y, reason = self.action_handler.get_smart_coordinates(
                        game_state.frame,
                        strategy="visual"
                    )
                    logger.info(f"ACTION6 at ({x}, {y}): {reason}")
            else:
                # Use smart coordinate selection
                x, y, reason = self.action_handler.get_smart_coordinates(
                    game_state.frame,
                    strategy="visual"
                )
                logger.info(f"ACTION6 at ({x}, {y}): {reason}")
            
            new_state = await self.action_handler.send_action_6(x, y, game_state.frame)
            
            # Track frame changes to detect productive actions
            if new_state and new_state.frame:
                # Pass current score to help adaptive exploration
                current_score = new_state.score if hasattr(new_state, 'score') else None
                frame_changed = self.action_handler.visual_analyzer.update_frame_change_tracking(
                    new_state.frame, 
                    current_score
                )
                if not frame_changed:
                    logger.debug(f"ACTION6 at ({x}, {y}) did not change frame")
                    
            return new_state
        else:
            # Execute regular action - convert ACTION1 to send_action_1 format
            # Extract number from ACTION string (e.g., "ACTION1" -> "1")
            action_num = action.replace("ACTION", "")
            method_name = f"send_action_{action_num}"
            if hasattr(self.action_handler, method_name):
                method = getattr(self.action_handler, method_name)
                return await method()
            else:
                raise ValueError(f"Unknown action: {action}")

    async def play_multiple_games(self, game_ids: List[str],
                                max_games: Optional[int] = None) -> List[Dict[str, Any]]:
        """Play multiple games sequentially.

        Args:
            game_ids: List of game IDs to play
            max_games: Maximum number of games to play

        Returns:
            List of game results
        """
        if max_games:
            game_ids = game_ids[:max_games]

        results = []
        for i, game_id in enumerate(game_ids):
            logger.info(f"Playing game {i+1}/{len(game_ids)}: {game_id}")

            try:
                result = await self.play_single_game(game_id)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to play game {game_id}: {e}")
                results.append({
                    'game_id': game_id,
                    'final_state': 'ERROR',
                    'final_score': 0.0,
                    'actions_taken': 0,
                    'error': str(e)
                })

        return results

    async def run_session(self, mode: str = "gameplay",
                         max_games: Optional[int] = None) -> Dict[str, Any]:
        """Run a complete gaming session.

        Args:
            mode: Session mode
            max_games: Maximum number of games to play

        Returns:
            Session summary
        """
        logger.info(f"Starting {mode} session")

        # Start session
        session_id = await self.session_manager.start_session(mode)

        try:
            # Get available games
            available_games = await self.session_manager.get_available_games()
            logger.info(f"Found {len(available_games)} available games")

            if not available_games:
                raise ValueError("No games available")

            # Extract game IDs
            game_ids = [game.get('id', game.get('game_id', str(i)))
                       for i, game in enumerate(available_games)]

            # Apply diversity-focused game selection if enabled
            if self.game_config.get('diversity_mode') and self.game_config.get('enforce_game_diversity'):
                game_ids = self._select_diverse_games(game_ids, max_games)
            elif max_games:
                # Standard mode: just limit count
                game_ids = game_ids[:max_games]

            results = await self.play_multiple_games(game_ids)

            # Calculate session statistics
            total_games = len(results)
            wins = sum(1 for r in results if r.get('win', False))
            total_score = sum(r.get('final_score', 0) for r in results)
            total_actions = sum(r.get('actions_taken', 0) for r in results)

            session_summary = {
                'session_id': session_id,
                'mode': mode,
                'total_games': total_games,
                'wins': wins,
                'win_rate': wins / total_games if total_games > 0 else 0.0,
                'total_score': total_score,
                'avg_score': total_score / total_games if total_games > 0 else 0.0,
                'total_actions': total_actions,
                'avg_actions_per_game': total_actions / total_games if total_games > 0 else 0.0,
                'game_results': results
            }

            logger.info(f"Session completed: {wins}/{total_games} wins, avg score: {session_summary['avg_score']:.2f}")
            return session_summary

        finally:
            # Ensure session is properly closed
            await self.session_manager.shutdown()

    def get_performance_stats(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get performance statistics.

        Args:
            session_id: Optional session ID filter

        Returns:
            Performance statistics
        """
        # Get data from database
        game_results = self.session_manager.db.get_game_results(session_id=session_id)

        if not game_results:
            return {"message": "No game results found"}

        total_games = len(game_results)
        wins = sum(1 for r in game_results if r.get('win_detected', False))
        total_score = sum(r.get('final_score', 0) for r in game_results)
        total_actions = sum(r.get('total_actions', 0) for r in game_results)

        stats = {
            'total_games': total_games,
            'wins': wins,
            'losses': total_games - wins,
            'win_rate': wins / total_games if total_games > 0 else 0.0,
            'total_score': total_score,
            'avg_score': total_score / total_games if total_games > 0 else 0.0,
            'total_actions': total_actions,
            'avg_actions_per_game': total_actions / total_games if total_games > 0 else 0.0
        }

        # Add recent performance
        recent_games = game_results[:10]  # Last 10 games
        if recent_games:
            recent_wins = sum(1 for r in recent_games if r.get('win_detected', False))
            stats['recent_win_rate'] = recent_wins / len(recent_games)
            stats['recent_avg_score'] = sum(r.get('final_score', 0) for r in recent_games) / len(recent_games)

        return stats

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session_manager.is_running:
            await self.session_manager.shutdown()

    # ========================================================================
    # DIVERSITY-FOCUSED GAME SELECTION (Rule 10: Integrated)
    # ========================================================================

    def _select_diverse_games(self, game_ids: List[str], max_games: int) -> List[str]:
        """
        Select games with diversity focus to prevent overfitting.
        
        Prioritizes:
        1. Novel games (never played by current agent)
        2. Under-exposed games (played <max_repeats times)
        3. Random selection from remaining games
        
        Args:
            game_ids: Available game IDs
            max_games: Maximum games to select
            
        Returns:
            List of selected game IDs optimized for diversity
        """
        if not max_games or max_games <= 0:
            return game_ids
        
        # Get current agent ID if available (from callbacks)
        agent_id = getattr(self, '_current_agent_id', None)
        if not agent_id:
            # No agent context, fallback to random selection
            import random
            return random.sample(game_ids, min(max_games, len(game_ids)))
        
        max_repeats = self.game_config.get('max_repeats_per_game', 5)
        
        # Query game exposure for this agent
        game_exposure = self.db.execute_query("""
            SELECT game_id, attempts, is_novel_game
            FROM agent_game_diversity
            WHERE agent_id = ?
        """, (agent_id,))
        
        exposure_map = {row['game_id']: row for row in game_exposure} if game_exposure else {}
        
        # Categorize games
        novel_games = []
        under_exposed = []
        over_exposed = []
        
        for game_id in game_ids:
            if game_id not in exposure_map:
                # Never played by this agent = novel
                novel_games.append(game_id)
            elif exposure_map[game_id]['attempts'] < max_repeats:
                # Played but not too much
                under_exposed.append((game_id, exposure_map[game_id]['attempts']))
            else:
                # Played too many times, avoid (anti-overfitting)
                over_exposed.append(game_id)
        
        # Build selection priority: novel > under_exposed > over_exposed
        import random
        
        selected = []
        
        # Priority 1: Novel games (shuffle for randomness)
        random.shuffle(novel_games)
        selected.extend(novel_games[:max_games])
        
        # Priority 2: Under-exposed games (prefer least played)
        if len(selected) < max_games:
            under_exposed.sort(key=lambda x: x[1])  # Sort by attempts (ascending)
            remaining = max_games - len(selected)
            selected.extend([g[0] for g in under_exposed[:remaining]])
        
        # Priority 3: Over-exposed games (only if necessary)
        if len(selected) < max_games:
            random.shuffle(over_exposed)
            remaining = max_games - len(selected)
            selected.extend(over_exposed[:remaining])
        
        logger.info(f"Diversity game selection: {len(novel_games)} novel, {len(under_exposed)} under-exposed, {len(over_exposed)} over-exposed")
        logger.info(f"Selected: {len([g for g in selected if g in novel_games])} novel games")
        
        return selected[:max_games]

    def _track_game_diversity(self, game_id: str, final_score: float, actions_taken: int):
        """
        Track game diversity metrics (Rule 2: database-only).
        
        Args:
            game_id: Game ID that was played
            final_score: Final score achieved
            actions_taken: Total actions taken
        """
        agent_id = getattr(self, '_current_agent_id', None)
        if not agent_id:
            return  # No agent context, skip tracking
        
        try:
            # Check if this is a novel game for this agent
            existing = self.db.execute_query("""
                SELECT attempts, first_attempt_score, best_score
                FROM agent_game_diversity
                WHERE agent_id = ? AND game_id = ?
            """, (agent_id, game_id))
            
            if not existing or len(existing) == 0:
                # Novel game - first time seeing it
                self.db.execute_query("""
                    INSERT INTO agent_game_diversity 
                    (agent_id, game_id, attempts, first_attempt_score, best_score, 
                     last_attempt_score, is_novel_game, few_shot_improvement, last_played)
                    VALUES (?, ?, 1, ?, ?, ?, TRUE, 0.0, CURRENT_TIMESTAMP)
                """, (agent_id, game_id, final_score, final_score, final_score))
                
                logger.info(f"📊 Diversity: Novel game tracked - {game_id} (score: {final_score})")
            else:
                # Repeated game - update metrics
                first_score = existing[0]['first_attempt_score']
                best_score = max(existing[0]['best_score'], final_score)
                attempts = existing[0]['attempts'] + 1
                few_shot_improvement = final_score - first_score if attempts == 2 else existing[0].get('few_shot_improvement', 0.0)
                
                self.db.execute_query("""
                    UPDATE agent_game_diversity
                    SET attempts = ?,
                        best_score = ?,
                        last_attempt_score = ?,
                        few_shot_improvement = ?,
                        is_novel_game = FALSE,
                        last_played = CURRENT_TIMESTAMP
                    WHERE agent_id = ? AND game_id = ?
                """, (attempts, best_score, final_score, few_shot_improvement, agent_id, game_id))
                
                if attempts == 2:
                    improvement = few_shot_improvement
                    logger.info(f"📊 Diversity: Few-shot learning - {game_id} improvement: {improvement:+.3f}")
                elif attempts > self.game_config.get('max_repeats_per_game', 5):
                    logger.warning(f"⚠️ Diversity: Overfitting risk - {game_id} played {attempts} times")
                    
        except Exception as e:
            logger.error(f"Error tracking game diversity: {e}")

    # ========================================================================
    # PATTERN LEARNING METHODS (Rule 10: Integrated into existing file)
    # ========================================================================

    def _capture_winning_sequence(self, game_id: str, final_score: float, 
                                 level_number: int = 1, reason: str = "win") -> Optional[str]:
        """
        Capture winning sequence for pattern learning (Rule 2: Database-only).
        Called automatically after wins OR level completions when enable_pattern_learning=True.
        
        Args:
            game_id: Game that was won
            final_score: Final score achieved
            level_number: Level number that was completed (default 1)
            reason: Reason for capture ("win", "level_1_completion", etc.)
            
        Returns:
            sequence_id if captured, None otherwise
        """
        if not self.game_config.get('enable_pattern_learning', True):
            return None
            
        try:
            session_id = self.session_manager.current_session_id
            if not session_id:
                return None
            
            # Get action traces from database
            action_traces = self.db.execute_query("""
                SELECT action_number, coordinates, frame_before, frame_after
                FROM action_traces
                WHERE game_id = ? AND session_id = ?
                ORDER BY timestamp ASC
            """, (game_id, session_id))
            
            if not action_traces or len(action_traces) == 0:
                return None
            
            # Extract sequence
            actions = [t['action_number'] for t in action_traces]
            coordinates = []
            for t in action_traces:
                if t['action_number'] == 6 and t.get('coordinates'):
                    try:
                        coord = json.loads(t['coordinates'])
                        coordinates.append(coord)
                    except:
                        pass
            
            efficiency = final_score / len(actions) if len(actions) > 0 else 0.0
            
            # Get frames
            initial_frame = json.loads(action_traces[0]['frame_before']) if action_traces[0].get('frame_before') else []
            final_frame = json.loads(action_traces[-1]['frame_after']) if action_traces[-1].get('frame_after') else []
            
            # Detect pattern tags and abstract pattern signature
            pattern_tags = self._detect_pattern_tags(actions, coordinates)
            game_type = self._classify_game_type(actions)
            pattern_signature = self._detect_frame_pattern(initial_frame, final_frame)
            
            # Check if we already have a winning sequence for this game/level
            existing = self.db.execute_query("""
                SELECT sequence_id, total_actions, efficiency_score 
                FROM winning_sequences
                WHERE game_id = ? AND level_number = ?
                ORDER BY efficiency_score DESC
                LIMIT 1
            """, (game_id, level_number))
            
            # Only store if this is MORE EFFICIENT than existing, or if no existing sequence
            should_store = False
            sequence_id = None
            
            if not existing:
                # First win for this level - always store
                should_store = True
                sequence_id = f"seq_{uuid.uuid4().hex[:16]}"
                logger.info(f"🆕 First winning sequence for {game_id} level {level_number}")
            else:
                existing_seq = existing[0]
                existing_actions = existing_seq['total_actions']
                existing_efficiency = existing_seq['efficiency_score']
                
                # Store if we improved (fewer actions OR better efficiency)
                if len(actions) < existing_actions:
                    should_store = True
                    sequence_id = f"seq_{uuid.uuid4().hex[:16]}"
                    logger.info(f"⚡ Optimized sequence: {existing_actions} → {len(actions)} actions "
                              f"(efficiency: {existing_efficiency:.4f} → {efficiency:.4f})")
                elif efficiency > existing_efficiency * 1.1:  # 10% efficiency improvement
                    should_store = True
                    sequence_id = f"seq_{uuid.uuid4().hex[:16]}"
                    logger.info(f"📈 Improved efficiency: {existing_efficiency:.4f} → {efficiency:.4f}")
                else:
                    logger.info(f"Existing sequence is still optimal ({existing_actions} actions, "
                              f"efficiency {existing_efficiency:.4f})")
            
            # Store in database (Rule 2) only if improved or first win
            if should_store and sequence_id:
                # Calculate frame transitions for pattern matching
                frame_transitions = self._extract_frame_transitions(action_traces)
                
                self.db.execute_query("""
                    INSERT INTO winning_sequences (
                        sequence_id, game_id, level_number, agent_id, session_id,
                        action_sequence, coordinate_sequence, total_actions, total_score,
                        efficiency_score, initial_frame, final_frame, frame_transitions,
                        pattern_tags, game_type, discovered_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sequence_id, game_id, level_number, 'core_agent', session_id,
                    json.dumps(actions), json.dumps(coordinates), len(actions),
                    final_score, efficiency, json.dumps(initial_frame),
                    json.dumps(final_frame), json.dumps(frame_transitions),
                    json.dumps(pattern_tags), game_type, datetime.now().isoformat()
                ))
                
                # Try to detect and store abstract pattern
                self._detect_and_store_abstract_pattern(
                    sequence_id, game_id, level_number, pattern_signature, 
                    pattern_tags, efficiency
                )
                
                logger.info(f"✅ Captured winning sequence {sequence_id}: "
                           f"{len(actions)} actions, efficiency {efficiency:.4f}, "
                           f"tags: {pattern_tags}, pattern: {pattern_signature.get('transformation_type', 'unknown')}")
            
            return sequence_id
            
        except Exception as e:
            logger.error(f"Error capturing winning sequence: {e}")
            return None

    def _detect_pattern_tags(self, actions: List[int], coordinates: List) -> List[str]:
        """Detect pattern tags in action sequence."""
        tags = []
        if not actions:
            return tags
            
        action_counts = Counter(actions)
        
        # Action composition patterns
        if action_counts.get(6, 0) / len(actions) > 0.8:
            tags.append('action6_heavy')
        if len(set(actions)) <= 2:
            tags.append('action_repetition')
            
        # Coordinate patterns
        if coordinates and len(coordinates) > 1:
            # coordinates are lists [x, y], not dicts
            try:
                x_coords = [c[0] if isinstance(c, list) and len(c) > 0 else 0 for c in coordinates]
                y_coords = [c[1] if isinstance(c, list) and len(c) > 1 else 0 for c in coordinates]
                if x_coords and y_coords and max(x_coords) - min(x_coords) < 10 and max(y_coords) - min(y_coords) < 10:
                    tags.append('coordinate_clustering')
            except Exception as e:
                logger.debug(f"Error processing coordinates for pattern tags: {e}")
                
        return tags

    def _classify_game_type(self, actions: List[int]) -> str:
        """Classify game type based on actions."""
        if not actions:
            return 'unknown'
        action_counts = Counter(actions)
        if action_counts.get(6, 0) == len(actions):
            return 'action6_only'
        elif len(action_counts) >= 5:
            return 'diverse_actions'
        else:
            return 'mixed_actions'

    def _get_best_sequence_for_game(self, game_id: str, level_number: int = 1, 
                                   current_frame=None) -> Optional[Dict]:
        """
        Get best known winning sequence for a specific game level (Rule 2: from database).
        Prioritizes sequences with high reliability scores (community validation).
        Uses reputation system to filter out sequences that fail often (Task 4).
        
        Args:
            game_id: Game to check
            level_number: Specific level to get sequence for
            current_frame: Optional current frame for pattern matching
            
        Returns:
            Sequence dict or None
        """
        if not self.game_config.get('enable_pattern_learning', True):
            return None
            
        try:
            # Query sequences with reputation scores (community memory)
            # Prioritize: reliability_score, then efficiency, then fewest actions
            sequences = self.db.execute_query("""
                SELECT ws.*, 
                       COALESCE(sr.reliability_score, 0.5) as reliability,
                       COALESCE(sr.success_rate, 0.5) as community_success_rate,
                       COALESCE(sr.agent_diversity, 0) as validators,
                       COALESCE(sr.trending, 'stable') as trend
                FROM winning_sequences ws
                LEFT JOIN sequence_reputation sr ON ws.sequence_id = sr.sequence_id
                WHERE ws.game_id = ? AND ws.level_number = ?
                ORDER BY reliability DESC, ws.efficiency_score DESC, ws.total_actions ASC
                LIMIT 5
            """, (game_id, level_number))
            
            if sequences:
                # Filter out sequences with very low reliability (< 0.3)
                reliable_sequences = [s for s in sequences if s['reliability'] >= 0.3]
                
                if reliable_sequences:
                    seq = reliable_sequences[0]
                    logger.info(f"📖 Found winning sequence for {game_id} level {level_number}: "
                               f"{seq['total_actions']} actions, efficiency {seq['efficiency_score']:.4f}, "
                               f"community reliability {seq['reliability']:.2f} "
                               f"({seq['validators']} agents validated, trend: {seq['trend']})")
                    return seq
                else:
                    logger.info(f"⚠️ Found sequences for {game_id} but all have low reliability (<0.3)")
            
            # No reliable exact match - try pattern matching if we have current frame
            if current_frame is not None:
                similar_pattern = self._find_similar_patterns(current_frame)
                
                if similar_pattern:
                    # Get one of the concrete examples
                    examples = json.loads(similar_pattern['concrete_examples'])
                    if examples:
                        # Get the most efficient example
                        example_seq = self.db.execute_query("""
                            SELECT ws.*, 
                                   COALESCE(sr.reliability_score, 0.5) as reliability
                            FROM winning_sequences ws
                            LEFT JOIN sequence_reputation sr ON ws.sequence_id = sr.sequence_id
                            WHERE ws.sequence_id = ?
                        """, (examples[0],))
                        
                        if example_seq and example_seq[0]['reliability'] >= 0.3:
                            logger.info(f"🔍 Using similar pattern {similar_pattern['pattern_id']} "
                                      f"as starting point (reliability: {example_seq[0]['reliability']:.2f})")
                            return example_seq[0]
            
            logger.debug(f"No reliable winning sequence found for {game_id} level {level_number}")
                
        except Exception as e:
            logger.debug(f"Error retrieving winning sequence for {game_id}: {e}")
            
        return None

    async def _replay_sequence_inline(self, game_state: GameState, sequence: Dict) -> Optional[Dict]:
        """
        Replay a sequence INLINE within the existing game session.
        Does NOT create a new game or finish the game.
        
        Args:
            game_state: Current game state (starting state)
            sequence: Winning sequence to replay
            
        Returns:
            Dict with 'game_state' (updated) and 'success' (bool), or None if error
        """
        try:
            sequence_id = sequence['sequence_id']
            logger.info(f"🔄 Replaying sequence {sequence_id} inline (level {sequence['level_number']})")
            
            # Verify initial frame matches (critical for replay success)
            expected_initial_frame = json.loads(sequence['initial_frame'])
            current_frame = game_state.frame
            
            # Simple frame comparison
            frames_match = self._compare_frames(expected_initial_frame, current_frame)
            if not frames_match:
                logger.warning(f"⚠️ Initial frame mismatch - aborting replay for {sequence_id}")
                return {'game_state': game_state, 'success': False}
            
            # Track that we're referencing this sequence
            self.db.execute_query("""
                UPDATE winning_sequences 
                SET times_referenced = times_referenced + 1,
                    last_referenced = ?
                WHERE sequence_id = ?
            """, (datetime.now().isoformat(), sequence_id))
            
            # Parse sequence
            actions = json.loads(sequence['action_sequence'])
            coordinates = json.loads(sequence.get('coordinate_sequence', '[]'))
            
            action_count = 0
            coord_index = 0
            
            # Execute actions
            for action_num in actions:
                if game_state.state != "NOT_FINISHED":
                    break
                
                # Execute action
                if action_num == 6 and coord_index < len(coordinates):
                    coord = coordinates[coord_index]
                    # Handle both dict and list formats
                    if isinstance(coord, dict):
                        x, y = coord.get('x', 0), coord.get('y', 0)
                    elif isinstance(coord, (list, tuple)) and len(coord) >= 2:
                        x, y = coord[0], coord[1]
                    else:
                        logger.warning(f"Invalid coordinate format: {coord}, skipping")
                        coord_index += 1
                        continue
                    
                    game_state = await self.action_handler.send_action_6(x, y, game_state.frame)
                    coord_index += 1
                else:
                    action = f"ACTION{action_num}"
                    game_state = await self._execute_action(action, game_state)
                
                action_count += 1
                
                logger.debug(f"Replay action {action_count}/{len(actions)}: ACTION{action_num}, "
                           f"Score: {game_state.score}, State: {game_state.state}")
            
            # Check if replay was successful
            replay_success = (game_state.state == "WIN" or 
                            game_state.score >= sequence['total_score'])
            
            # Record validation attempt for community memory (Task 4)
            failure_reason = None
            if not replay_success:
                if not frames_match:
                    failure_reason = 'initial_frame_mismatch'
                elif action_count < len(actions):
                    failure_reason = 'incomplete_sequence'
                else:
                    failure_reason = 'insufficient_score'
            
            # Get agent information from config or session
            agent_id = self.game_config.get('agent_id', 'unknown')
            session_id = self.session_manager.current_session_id if self.session_manager and self.session_manager.current_session_id else 'unknown'
            
            # Get agent epigenetics if available from config
            agent_epigenetics = self.game_config.get('agent_epigenetics')
            
            self._record_sequence_validation(
                sequence_id=sequence_id,
                agent_id=agent_id,
                game_id=sequence['game_id'],
                session_id=session_id,
                success=replay_success,
                actions_completed=action_count,
                total_actions=len(actions),
                score_achieved=game_state.score,
                original_efficiency=sequence['efficiency_score'],
                agent_epigenetics=agent_epigenetics,
                failure_reason=failure_reason
            )
            
            if replay_success:
                logger.info(f"✅ Inline replay successful for {sequence_id}! Score: {game_state.score}")
            else:
                logger.warning(f"❌ Inline replay failed for {sequence_id}. "
                             f"Expected score: {sequence['total_score']}, Got: {game_state.score}")
            
            return {'game_state': game_state, 'success': replay_success}
            
        except Exception as e:
            logger.error(f"Error in inline replay: {e}", exc_info=True)
            return None

    async def _try_replay_sequence(self, game_id: str, sequence: Dict) -> Optional[Dict[str, Any]]:
        """
        Try to replay a known winning sequence (Rule 7: Real actions).
        Verifies initial frame matches and tracks replay attempts.
        
        Args:
            game_id: Game to play
            sequence: Winning sequence to replay
            
        Returns:
            Game results or None if failed
        """
        try:
            sequence_id = sequence['sequence_id']
            logger.info(f"🔄 Attempting to replay sequence {sequence_id} for {game_id} level {sequence['level_number']}")
            
            if not self.session_manager.is_running:
                await self.session_manager.start_session(game_id=game_id)
            
            game_data = await self.session_manager.create_game(game_id)
            game_state = GameState.from_dict(game_data)
            
            # Verify initial frame matches (critical for replay success)
            expected_initial_frame = json.loads(sequence['initial_frame'])
            current_frame = game_state.frame
            
            # Simple frame comparison (can be enhanced with fuzzy matching)
            frames_match = self._compare_frames(expected_initial_frame, current_frame)
            if not frames_match:
                logger.warning(f"⚠️ Initial frame mismatch - replay may fail for {sequence_id}")
                # Continue anyway but track this
            
            actions = json.loads(sequence['action_sequence'])
            coordinates = json.loads(sequence.get('coordinate_sequence', '[]'))
            
            start_time = datetime.now()
            action_count = 0
            coord_index = 0
            replay_success = False
            
            # Track that we're referencing this sequence
            self.db.execute_query("""
                UPDATE winning_sequences 
                SET times_referenced = times_referenced + 1,
                    last_referenced = ?
                WHERE sequence_id = ?
            """, (datetime.now().isoformat(), sequence_id))
            
            for action_num in actions:
                if game_state.state != "NOT_FINISHED":
                    break
                
                # Execute action and track it (Rule 2: Database tracking)
                if action_num == 6 and coord_index < len(coordinates):
                    coord = coordinates[coord_index]
                    # Handle both dict and list formats
                    if isinstance(coord, dict):
                        x, y = coord.get('x', 0), coord.get('y', 0)
                    elif isinstance(coord, (list, tuple)) and len(coord) >= 2:
                        x, y = coord[0], coord[1]
                    else:
                        logger.warning(f"Invalid coordinate format: {coord}, skipping")
                        coord_index += 1
                        continue
                    
                    game_state = await self.action_handler.send_action_6(x, y, game_state.frame)
                    coord_index += 1
                else:
                    action = f"ACTION{action_num}"
                    game_state = await self._execute_action(action, game_state)
                
                action_count += 1
                
                # Log to system_logs for debugging
                logger.debug(f"Replay action {action_count}/{len(actions)}: ACTION{action_num}, "
                           f"Score: {game_state.score}, State: {game_state.state}")
            
            await self.session_manager.finish_game(game_state.state, game_state.score)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Check if replay was successful
            replay_success = (game_state.state == "WIN" or 
                            game_state.score >= sequence['total_score'])
            
            # Update success rate in database
            if replay_success:
                logger.info(f"✅ Replay successful for {sequence_id}! Score: {game_state.score}")
                # Note: success_rate_when_reused calculation would need existing value
                # For now, just increment a success counter (schema may need update)
            else:
                logger.warning(f"❌ Replay failed for {sequence_id}. "
                             f"Expected score: {sequence['total_score']}, Got: {game_state.score}")
            
            result = {
                'game_id': game_id,
                'final_state': game_state.state,
                'final_score': game_state.score,
                'actions_taken': action_count,
                'duration_seconds': duration,
                'win': game_state.state == "WIN",
                'method': 'replay_sequence',
                'sequence_id': sequence_id,
                'replay_success': replay_success,
                'frame_match': frames_match
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error replaying sequence: {e}", exc_info=True)
            return None
    
    def _record_sequence_validation(self, sequence_id: str, agent_id: str, 
                                   game_id: str, session_id: str,
                                   success: bool, actions_completed: int,
                                   total_actions: int, score_achieved: float,
                                   original_efficiency: float,
                                   agent_epigenetics: Optional[Dict] = None,
                                   failure_reason: Optional[str] = None):
        """
        Record sequence validation attempt for community memory (Task 4).
        Tracks which agents tried which sequences and whether they worked.
        
        Args:
            sequence_id: Sequence that was attempted
            agent_id: Agent that attempted it
            game_id: Game where it was attempted
            session_id: Session ID
            success: Did the sequence work completely?
            actions_completed: How many actions from sequence worked
            total_actions: Total actions in sequence
            score_achieved: Score achieved by this agent
            original_efficiency: Original sequence's efficiency score
            agent_epigenetics: Agent's epigenetic state (for analysis)
            failure_reason: If failed, why?
        """
        try:
            import uuid
            validation_id = f"val_{uuid.uuid4().hex[:12]}"
            
            partial_success = (actions_completed > 0 and 
                             actions_completed < total_actions and 
                             not success)
            
            # Calculate efficiency vs original
            if score_achieved > 0 and actions_completed > 0:
                agent_efficiency = score_achieved / actions_completed
                efficiency_ratio = agent_efficiency / original_efficiency if original_efficiency > 0 else 0.0
            else:
                efficiency_ratio = 0.0
            
            # Store validation attempt
            self.db.execute_query("""
                INSERT INTO sequence_validation_attempts
                (validation_id, sequence_id, agent_id, game_id, session_id,
                 validation_success, partial_success, actions_completed, 
                 total_actions_in_sequence, score_achieved, efficiency_vs_original,
                 agent_epigenetics, failure_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (validation_id, sequence_id, agent_id, game_id, session_id,
                  success, partial_success, actions_completed, total_actions,
                  score_achieved, efficiency_ratio,
                  json.dumps(agent_epigenetics) if agent_epigenetics else None,
                  failure_reason))
            
            # Update sequence reputation
            self._update_sequence_reputation(sequence_id)
            
            logger.info(f"📊 Recorded validation: {sequence_id} by {agent_id} - "
                       f"{'✓ Success' if success else '✗ Failed'} "
                       f"({actions_completed}/{total_actions} actions)")
            
        except Exception as e:
            logger.error(f"Error recording sequence validation: {e}")
    
    def _update_sequence_reputation(self, sequence_id: str):
        """
        Update reputation score for a sequence based on all validation attempts.
        Uses Bayesian approach with prior to handle small sample sizes.
        
        This implements the "downvoting" mechanism - sequences that fail often
        get lower reputation scores and are less likely to be selected.
        """
        try:
            # Get all validation attempts for this sequence
            attempts = self.db.execute_query("""
                SELECT 
                    COUNT(*) as total_attempts,
                    SUM(CASE WHEN validation_success = 1 THEN 1 ELSE 0 END) as successes,
                    SUM(CASE WHEN validation_success = 0 THEN 1 ELSE 0 END) as failures,
                    SUM(CASE WHEN partial_success = 1 THEN 1 ELSE 0 END) as partials,
                    COUNT(DISTINCT agent_id) as unique_agents
                FROM sequence_validation_attempts
                WHERE sequence_id = ?
            """, (sequence_id,))
            
            if not attempts or attempts[0]['total_attempts'] == 0:
                # No validation attempts yet, use default values
                self.db.execute_query("""
                    INSERT OR REPLACE INTO sequence_reputation
                    (sequence_id, total_validation_attempts, successful_validations,
                     failed_validations, partial_validations, success_rate,
                     reliability_score, agent_diversity, recent_success_rate, trending)
                    VALUES (?, 0, 0, 0, 0, 0.5, 0.5, 1, 0.5, 'stable')
                """, (sequence_id,))
                return
            
            stats = attempts[0]
            total = stats['total_attempts']
            successes = stats['successes'] or 0
            failures = stats['failures'] or 0
            partials = stats['partials'] or 0
            unique_agents = stats['unique_agents'] or 1
            
            # Calculate raw success rate
            raw_success_rate = successes / total if total > 0 else 0.5
            
            # Bayesian reliability score (adds prior of 2 successes, 2 failures)
            # This prevents new sequences from having extreme scores
            reliability_score = (successes + 2) / (total + 4)
            
            # Calculate recent success rate (last 10 attempts)
            recent_attempts = self.db.execute_query("""
                SELECT validation_success
                FROM sequence_validation_attempts
                WHERE sequence_id = ?
                ORDER BY attempted_at DESC
                LIMIT 10
            """, (sequence_id,))
            
            recent_successes = sum(1 for a in recent_attempts if a['validation_success'])
            recent_success_rate = recent_successes / len(recent_attempts) if recent_attempts else 0.5
            
            # Determine trend
            if len(recent_attempts) >= 5:
                if recent_success_rate > raw_success_rate + 0.1:
                    trending = 'improving'
                elif recent_success_rate < raw_success_rate - 0.1:
                    trending = 'declining'
                else:
                    trending = 'stable'
            else:
                trending = 'stable'
            
            # Update reputation
            self.db.execute_query("""
                INSERT OR REPLACE INTO sequence_reputation
                (sequence_id, total_validation_attempts, successful_validations,
                 failed_validations, partial_validations, success_rate,
                 reliability_score, agent_diversity, recent_success_rate, trending,
                 last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (sequence_id, total, successes, failures, partials,
                  raw_success_rate, reliability_score, unique_agents,
                  recent_success_rate, trending, datetime.now().isoformat()))
            
            logger.debug(f"📈 Updated reputation for {sequence_id}: "
                        f"reliability={reliability_score:.2f}, "
                        f"success_rate={raw_success_rate:.2f}, "
                        f"trend={trending}")
            
        except Exception as e:
            logger.error(f"Error updating sequence reputation: {e}")
    
    def _compare_frames(self, frame1, frame2) -> bool:
        """
        Compare two frames for similarity.
        Returns True if frames match closely enough for replay.
        """
        try:
            # Handle nested lists from ARC API
            if isinstance(frame1, list) and len(frame1) > 0:
                if isinstance(frame1[0], list) and len(frame1[0]) > 0:
                    if isinstance(frame1[0][0], list):
                        frame1 = frame1[0][0]  # Unwrap [[[data]]]
            
            if isinstance(frame2, list) and len(frame2) > 0:
                if isinstance(frame2[0], list) and len(frame2[0]) > 0:
                    if isinstance(frame2[0][0], list):
                        frame2 = frame2[0][0]  # Unwrap [[[data]]]
            
            # Simple equality check
            if frame1 == frame2:
                return True
            
            # If frames are different lengths, definitely don't match
            if len(frame1) != len(frame2):
                return False
            
            # Check if at least 95% of cells match
            total_cells = 0
            matching_cells = 0
            
            for row1, row2 in zip(frame1, frame2):
                if not isinstance(row1, list) or not isinstance(row2, list):
                    continue
                for cell1, cell2 in zip(row1, row2):
                    total_cells += 1
                    if cell1 == cell2:
                        matching_cells += 1
            
            if total_cells == 0:
                return False
            
            match_ratio = matching_cells / total_cells
            return match_ratio >= 0.95
            
        except Exception as e:
            logger.debug(f"Frame comparison error: {e}")
            return False
    
    def _detect_frame_pattern(self, initial_frame, final_frame) -> Dict[str, Any]:
        """
        Detect abstract patterns between initial and final frames.
        This helps identify pattern-based transformations rather than literal sequences.
        
        Returns:
            Dict with pattern characteristics for matching similar problems
        """
        pattern_info = {
            'grid_size': None,
            'color_distribution_change': {},
            'symmetry_detected': False,
            'repetition_detected': False,
            'transformation_type': 'unknown'
        }
        
        try:
            # Unwrap nested frames
            initial = initial_frame
            final = final_frame
            
            if isinstance(initial, list) and len(initial) > 0:
                if isinstance(initial[0], list) and len(initial[0]) > 0:
                    if isinstance(initial[0][0], list):
                        initial = initial[0][0]
            
            if isinstance(final, list) and len(final) > 0:
                if isinstance(final[0], list) and len(final[0]) > 0:
                    if isinstance(final[0][0], list):
                        final = final[0][0]
            
            if not initial or not final:
                return pattern_info
            
            # Grid size
            if isinstance(initial, list) and len(initial) > 0 and isinstance(initial[0], list):
                pattern_info['grid_size'] = (len(initial), len(initial[0]))
            
            # Color distribution changes
            from collections import Counter
            
            initial_colors = Counter()
            final_colors = Counter()
            
            for row in initial:
                if isinstance(row, list):
                    for cell in row:
                        if isinstance(cell, int):
                            initial_colors[cell] += 1
            
            for row in final:
                if isinstance(row, list):
                    for cell in row:
                        if isinstance(cell, int):
                            final_colors[cell] += 1
            
            # Detect transformation patterns
            if initial_colors == final_colors:
                pattern_info['transformation_type'] = 'rearrangement'
            elif len(final_colors) < len(initial_colors):
                pattern_info['transformation_type'] = 'color_reduction'
            elif len(final_colors) > len(initial_colors):
                pattern_info['transformation_type'] = 'color_expansion'
            else:
                pattern_info['transformation_type'] = 'color_transformation'
            
            # Store color changes
            for color in set(list(initial_colors.keys()) + list(final_colors.keys())):
                pattern_info['color_distribution_change'][color] = {
                    'before': initial_colors.get(color, 0),
                    'after': final_colors.get(color, 0),
                    'delta': final_colors.get(color, 0) - initial_colors.get(color, 0)
                }
            
            # Detect symmetry in final frame
            if isinstance(final, list) and len(final) > 1:
                # Check horizontal symmetry
                is_symmetric = True
                for i in range(len(final) // 2):
                    if final[i] != final[-(i+1)]:
                        is_symmetric = False
                        break
                pattern_info['symmetry_detected'] = is_symmetric
            
            # Detect repetition patterns
            if isinstance(final, list) and len(final) > 0:
                # Check if rows repeat
                row_counts = Counter([tuple(row) if isinstance(row, list) else row for row in final])
                if max(row_counts.values()) > 1:
                    pattern_info['repetition_detected'] = True
            
        except Exception as e:
            logger.debug(f"Pattern detection error: {e}")
        
        return pattern_info
    
    def _extract_frame_transitions(self, action_traces: List[Dict]) -> List[Dict]:
        """
        Extract key frame transitions where significant changes occurred.
        This helps identify critical moments in winning sequences.
        """
        transitions = []
        
        try:
            for i, trace in enumerate(action_traces):
                # Record transitions where frame actually changed
                if trace.get('frame_changed'):
                    transition = {
                        'action_index': i,
                        'action_number': trace.get('action_number'),
                        'score_before': trace.get('score_before', 0),
                        'score_after': trace.get('score_after', 0),
                        'score_delta': trace.get('score_change', 0)
                    }
                    
                    # Include coordinates if ACTION6
                    if trace.get('action_number') == 6 and trace.get('coordinates'):
                        try:
                            transition['coordinates'] = json.loads(trace['coordinates'])
                        except:
                            pass
                    
                    transitions.append(transition)
        
        except Exception as e:
            logger.debug(f"Frame transition extraction error: {e}")
        
        return transitions
    
    def _detect_and_store_abstract_pattern(self, sequence_id: str, game_id: str, 
                                          level_number: int, pattern_signature: Dict,
                                          pattern_tags: List[str], efficiency: float):
        """
        Detect and store abstract patterns that can be reused across similar problems.
        This enables pattern-based matching rather than just literal sequence replay.
        """
        try:
            # Create pattern signature hash for matching
            sig_str = json.dumps({
                'transformation_type': pattern_signature.get('transformation_type'),
                'grid_size': pattern_signature.get('grid_size'),
                'symmetry': pattern_signature.get('symmetry_detected'),
                'repetition': pattern_signature.get('repetition_detected'),
                'tags': sorted(pattern_tags)
            }, sort_keys=True)
            
            import hashlib
            pattern_hash = hashlib.md5(sig_str.encode()).hexdigest()[:16]
            pattern_id = f"pat_{pattern_hash}"
            
            # Check if this pattern already exists
            existing_pattern = self.db.execute_query("""
                SELECT pattern_id, occurrence_count, success_count, 
                       concrete_examples, avg_efficiency
                FROM discovered_patterns
                WHERE pattern_id = ?
            """, (pattern_id,))
            
            if existing_pattern:
                # Update existing pattern
                pat = existing_pattern[0]
                examples = json.loads(pat['concrete_examples'])
                
                if sequence_id not in examples:
                    examples.append(sequence_id)
                    new_count = pat['occurrence_count'] + 1
                    new_success = pat['success_count'] + 1
                    
                    # Update average efficiency
                    new_avg_eff = (pat['avg_efficiency'] * pat['occurrence_count'] + efficiency) / new_count
                    
                    self.db.execute_query("""
                        UPDATE discovered_patterns
                        SET occurrence_count = ?,
                            success_count = ?,
                            concrete_examples = ?,
                            avg_efficiency = ?,
                            success_rate = ?
                        WHERE pattern_id = ?
                    """, (
                        new_count, new_success, json.dumps(examples),
                        new_avg_eff, new_success / new_count,
                        pattern_id
                    ))
                    
                    logger.info(f"📊 Updated pattern {pattern_id}: {new_count} occurrences")
            else:
                # Create new pattern
                pattern_name = f"{pattern_signature.get('transformation_type', 'unknown')}_{pattern_tags[0] if pattern_tags else 'generic'}"
                
                self.db.execute_query("""
                    INSERT INTO discovered_patterns (
                        pattern_id, pattern_name, pattern_type, pattern_signature,
                        concrete_examples, occurrence_count, success_count,
                        success_rate, avg_score_achieved, avg_efficiency,
                        confidence_score, discovered_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pattern_id, pattern_name, 'transformation',
                    json.dumps(pattern_signature), json.dumps([sequence_id]),
                    1, 1, 1.0, 1.0, efficiency, 0.5,
                    datetime.now().isoformat()
                ))
                
                logger.info(f"🆕 Discovered new pattern {pattern_id}: {pattern_name}")
        
        except Exception as e:
            logger.debug(f"Abstract pattern detection error: {e}")
    
    def _find_similar_patterns(self, current_frame) -> Optional[Dict]:
        """
        Find patterns that might apply to the current game state.
        Uses abstract pattern matching rather than exact frame matching.
        """
        try:
            # Get current frame characteristics
            dummy_final = current_frame  # We don't know final yet
            current_sig = self._detect_frame_pattern(current_frame, dummy_final)
            
            # Query patterns with similar characteristics
            all_patterns = self.db.execute_query("""
                SELECT pattern_id, pattern_name, pattern_signature, 
                       concrete_examples, success_rate, avg_efficiency,
                       confidence_score
                FROM discovered_patterns
                WHERE success_rate >= 0.5
                ORDER BY confidence_score DESC, success_rate DESC
                LIMIT 10
            """)
            
            best_match = None
            best_score = 0.0
            
            for pat in all_patterns:
                try:
                    sig = json.loads(pat['pattern_signature'])
                    
                    # Calculate similarity score
                    similarity = 0.0
                    
                    # Grid size match
                    if sig.get('grid_size') == current_sig.get('grid_size'):
                        similarity += 0.3
                    
                    # Transformation type match
                    if sig.get('transformation_type') == current_sig.get('transformation_type'):
                        similarity += 0.3
                    
                    # Pattern features
                    if sig.get('symmetry_detected') == current_sig.get('symmetry_detected'):
                        similarity += 0.2
                    
                    if sig.get('repetition_detected') == current_sig.get('repetition_detected'):
                        similarity += 0.2
                    
                    # Weight by pattern success rate and confidence
                    weighted_score = similarity * pat['success_rate'] * pat['confidence_score']
                    
                    if weighted_score > best_score:
                        best_score = weighted_score
                        best_match = pat
                
                except Exception as e:
                    logger.debug(f"Pattern matching error: {e}")
                    continue
            
            if best_match and best_score >= 0.3:
                logger.info(f"🎯 Found similar pattern {best_match['pattern_id']} "
                           f"(similarity: {best_score:.2f})")
                return best_match
            
        except Exception as e:
            logger.debug(f"Pattern search error: {e}")
        
        return None
    
    # ========== META-LEARNING METHODS (Rule 10: Integrated into core_gameplay.py) ==========
    
    def _meta_learn_pattern_from_frame(self, frame: np.ndarray) -> Optional[Dict[str, Any]]:
        """
        Meta-learning: Analyzes frame and discovers pattern rules without hardcoding.
        
        Discovers:
        - Anomalies (odd one out)
        - Templates/Keys (transformation examples)
        - Spatial significance (center, corners, edges)
        - Transformation rules (what to apply)
        
        Args:
            frame: Current game frame (numpy array)
            
        Returns:
            Dictionary with discovered pattern and transformation actions, or None
        """
        if frame is None or frame.size == 0:
            return None
            
        try:
            # Step 1: Find what's special (anomalies)
            anomalies = self._meta_detect_anomalies(frame)
            logger.info(f"🧠 Meta: Detected {len(anomalies)} anomalies")
            
            # Step 2: Check spatial significance
            spatial_features = self._meta_analyze_spatial_significance(frame, anomalies)
            logger.info(f"🧠 Meta: {len(spatial_features.get('center_anomalies', []))} center, "
                       f"{len(spatial_features.get('corner_anomalies', []))} corner, "
                       f"{len(spatial_features.get('edge_anomalies', []))} edge")
            
            # Step 3: Look for templates/transformation examples
            templates = self._meta_find_transformation_templates(frame, anomalies, spatial_features)
            logger.info(f"🧠 Meta: Found {len(templates)} potential templates")
            
            # Step 4: Extract transformation rules
            if templates:
                rule = self._meta_extract_transformation_rule(frame, templates[0])
                logger.info(f"🧠 Meta: Extracted rule: {rule}")
                
                if rule:
                    # Step 5: Find where to apply the rule
                    targets = self._meta_find_application_targets(frame, rule)
                    
                    # Step 6: Generate actions
                    actions = self._meta_generate_transformation_actions(frame, targets, rule)
                    
                    return {
                        'pattern_type': 'template_transformation',
                        'rule': rule,
                        'template_region': templates[0],
                        'target_regions': targets,
                        'actions': actions,
                        'confidence': self._meta_calculate_confidence(rule, targets)
                    }
            
            # Try other pattern types
            symmetry_pattern = self._meta_detect_symmetry_completion(frame)
            if symmetry_pattern:
                return symmetry_pattern
                
            return None
            
        except Exception as e:
            logger.error(f"Error in pattern meta-learning: {e}")
            return None
    
    def _meta_detect_anomalies(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Finds regions that are different from others (odd one out)."""
        anomalies = []
        regions = self._meta_segment_into_regions(frame)
        
        if len(regions) < 2:
            return anomalies
        
        # Calculate complexity scores
        complexity_scores = []
        for region in regions:
            score = {
                'region': region,
                'unique_colors': len(np.unique(region['pixels'])),
                'color_changes': self._meta_count_color_boundaries(region['pixels']),
                'entropy': self._meta_calculate_entropy(region['pixels']),
                'has_substructure': self._meta_has_nested_structure(region['pixels'])
            }
            complexity_scores.append(score)
        
        # Find statistical outliers
        avg_colors = np.mean([s['unique_colors'] for s in complexity_scores])
        avg_changes = np.mean([s['color_changes'] for s in complexity_scores])
        
        for score in complexity_scores:
            if (score['unique_colors'] > avg_colors * 1.5 or 
                score['color_changes'] > avg_changes * 1.5 or
                score['has_substructure']):
                anomalies.append({
                    'region': score['region'],
                    'complexity': score,
                    'reason': 'Higher complexity than peers'
                })
        
        return anomalies
    
    def _meta_analyze_spatial_significance(self, frame: np.ndarray, 
                                          anomalies: List[Dict]) -> Dict[str, Any]:
        """Checks if anomalies are in significant positions."""
        height, width = frame.shape[:2]
        frame_center = (height // 2, width // 2)
        
        features = {
            'center_anomalies': [],
            'corner_anomalies': [],
            'edge_anomalies': []
        }
        
        for anomaly in anomalies:
            region = anomaly['region']
            region_center = region['center']
            
            distance = np.sqrt((region_center[0] - frame_center[0])**2 + 
                             (region_center[1] - frame_center[1])**2)
            normalized_distance = distance / np.sqrt(height**2 + width**2)
            
            if normalized_distance < 0.2:  # Very close to center
                features['center_anomalies'].append({
                    'anomaly': anomaly,
                    'distance': distance,
                    'weight': 2.0  # Center gets higher weight
                })
            elif self._meta_is_near_corner(region_center, (height, width)):
                features['corner_anomalies'].append(anomaly)
            elif self._meta_is_near_edge(region_center, (height, width)):
                features['edge_anomalies'].append(anomaly)
        
        return features
    
    def _meta_find_transformation_templates(self, frame: np.ndarray, 
                                           anomalies: List[Dict],
                                           spatial_features: Dict) -> List[Dict]:
        """Identifies regions that demonstrate transformations."""
        templates = []
        
        # Central anomalies are most likely to be templates
        for center_anomaly in spatial_features.get('center_anomalies', []):
            anomaly = center_anomaly['anomaly']
            region = anomaly['region']
            
            if self._meta_has_nested_structure(region['pixels']):
                layers = self._meta_extract_layers(region['pixels'])
                
                if layers and len(layers) >= 2:
                    templates.append({
                        'region': region,
                        'layers': layers,
                        'type': 'nested_transformation',
                        'weight': center_anomaly['weight']
                    })
        
        # Also check regular anomalies
        for anomaly in anomalies:
            region = anomaly['region']
            if self._meta_shows_color_transformation(region['pixels']):
                templates.append({
                    'region': region,
                    'type': 'color_transformation',
                    'weight': 1.0
                })
        
        templates.sort(key=lambda x: x['weight'], reverse=True)
        return templates
    
    def _meta_extract_transformation_rule(self, frame: np.ndarray, 
                                         template: Dict) -> Optional[Dict[str, Any]]:
        """Extracts the transformation rule from a template region."""
        region = template['region']
        pixels = region['pixels']
        
        logger.debug(f"Extracting rule from template type: {template['type']}")
        
        if template['type'] == 'nested_transformation':
            layers = template['layers']
            
            if len(layers) >= 2:
                outer_layer = layers[0]  # Border
                inner_layer = layers[-1]  # Center (most inner)
                
                outer_color = self._meta_get_dominant_color(outer_layer)
                inner_color = self._meta_get_dominant_color(inner_layer)
                
                if outer_color != inner_color:
                    center_ratio = self._meta_calculate_center_ratio(layers)
                    
                    return {
                        'type': 'add_center_pattern',
                        'border_color': int(outer_color),
                        'center_color': int(inner_color),
                        'center_ratio': center_ratio,
                        'template_position': region['center']
                    }
        
        elif template['type'] == 'color_transformation':
            color_freq = Counter(pixels.flatten())
            
            if len(color_freq) >= 2:
                colors = sorted(color_freq.items(), key=lambda x: x[1], reverse=True)
                return {
                    'type': 'color_replacement',
                    'from_color': int(colors[1][0]),
                    'to_color': int(colors[0][0])
                }
        
        return None
    
    def _meta_find_application_targets(self, frame: np.ndarray, 
                                      rule: Dict) -> List[Dict[str, Any]]:
        """Finds regions where the transformation rule should be applied."""
        targets = []
        regions = self._meta_segment_into_regions(frame)
        
        if rule['type'] == 'add_center_pattern':
            border_color = rule['border_color']
            template_pos = rule['template_position']
            
            for region in regions:
                # Skip the template itself
                if self._meta_regions_overlap(region['center'], template_pos, threshold=5):
                    continue
                
                dominant_color = self._meta_get_dominant_color(region['pixels'])
                
                if dominant_color == border_color:
                    targets.append({
                        'region': region,
                        'reason': 'Matches border color pattern'
                    })
        
        elif rule['type'] == 'color_replacement':
            from_color = rule['from_color']
            
            for region in regions:
                if np.any(region['pixels'] == from_color):
                    targets.append({
                        'region': region,
                        'reason': 'Contains color to replace'
                    })
        
        return targets
    
    def _meta_generate_transformation_actions(self, frame: np.ndarray, 
                                             targets: List[Dict],
                                             rule: Dict) -> List[Dict[str, Any]]:
        """Generates ACTION6 coordinates to execute the transformation."""
        actions = []
        
        if rule['type'] == 'add_center_pattern':
            center_color = rule['center_color']
            center_ratio = rule['center_ratio']
            
            for target in targets:
                region = target['region']
                region_center = region['center']
                region_size = region['size']
                
                center_size = int(region_size * center_ratio)
                center_radius = int(np.sqrt(center_size) / 2)
                
                for dy in range(-center_radius, center_radius + 1):
                    for dx in range(-center_radius, center_radius + 1):
                        y = region_center[0] + dy
                        x = region_center[1] + dx
                        
                        if 0 <= y < frame.shape[0] and 0 <= x < frame.shape[1]:
                            actions.append({
                                'type': 'ACTION6',
                                'coordinate': (x, y),
                                'color': center_color,
                                'reason': 'Applying template pattern to center',
                                'rule_type': 'add_center_pattern'
                            })
        
        return actions
    
    def _meta_calculate_confidence(self, rule: Dict, targets: List[Dict]) -> float:
        """Calculates confidence score for the discovered pattern."""
        base_confidence = 0.5
        target_bonus = min(len(targets) * 0.1, 0.3)
        
        if rule['type'] in ['add_center_pattern', 'color_replacement']:
            type_bonus = 0.2
        else:
            type_bonus = 0.0
        
        return min(base_confidence + target_bonus + type_bonus, 1.0)
    
    def _meta_detect_symmetry_completion(self, frame: np.ndarray) -> Optional[Dict]:
        """Detects if pattern requires symmetry completion."""
        height, width = frame.shape[:2]
        
        left_half = frame[:, :width//2]
        right_half = frame[:, width//2:]
        
        if right_half.shape[1] > 0 and left_half.shape == right_half.shape:
            right_unique = len(np.unique(right_half))
            left_unique = len(np.unique(left_half))
            
            if right_unique < left_unique:
                return {
                    'pattern_type': 'symmetry_completion',
                    'rule': {'type': 'mirror_horizontal', 'source': 'left'},
                    'confidence': 0.6
                }
        
        return None
    
    # Helper methods for meta-learning
    
    def _meta_segment_into_regions(self, frame: np.ndarray) -> List[Dict]:
        """Segments frame into distinct rectangular regions."""
        regions = []
        height, width = frame.shape[:2]
        
        region_size = self._meta_detect_grid_size(frame)
        
        if region_size:
            rows = height // region_size
            cols = width // region_size
            
            for r in range(rows):
                for c in range(cols):
                    y1 = r * region_size
                    x1 = c * region_size
                    y2 = min(y1 + region_size, height)
                    x2 = min(x1 + region_size, width)
                    
                    region_pixels = frame[y1:y2, x1:x2]
                    
                    regions.append({
                        'pixels': region_pixels,
                        'bounds': (y1, x1, y2, x2),
                        'center': ((y1 + y2) // 2, (x1 + x2) // 2),
                        'size': region_pixels.size
                    })
        
        return regions
    
    def _meta_detect_grid_size(self, frame: np.ndarray) -> Optional[int]:
        """Attempts to detect if frame has a grid structure."""
        height, width = frame.shape[:2]
        
        common_sizes = [height // 3, height // 4, height // 5, 
                       width // 3, width // 4, width // 5]
        
        for size in common_sizes:
            if size > 5:
                h_rem = height % size
                w_rem = width % size
                
                if h_rem < 5 and w_rem < 5:
                    return size
        
        return None
    
    def _meta_count_color_boundaries(self, pixels: np.ndarray) -> int:
        """Counts number of color transitions in region."""
        if pixels.size < 2:
            return 0
        
        flat = pixels.flatten()
        boundaries = np.sum(flat[:-1] != flat[1:])
        return int(boundaries)
    
    def _meta_calculate_entropy(self, pixels: np.ndarray) -> float:
        """Calculates Shannon entropy of color distribution."""
        if pixels.size == 0:
            return 0.0
        
        _, counts = np.unique(pixels, return_counts=True)
        probs = counts / pixels.size
        entropy = -np.sum(probs * np.log2(probs + 1e-10))
        return float(entropy)
    
    def _meta_has_nested_structure(self, pixels: np.ndarray) -> bool:
        """Checks if region has nested/layered structure."""
        if pixels.size < 9:
            return False
        
        height, width = pixels.shape[:2]
        
        if height < 3 or width < 3:
            return False
        
        cy1, cy2 = height // 3, 2 * height // 3
        cx1, cx2 = width // 3, 2 * width // 3
        
        center = pixels[cy1:cy2, cx1:cx2]
        edges = np.concatenate([
            pixels[0, :], pixels[-1, :],
            pixels[:, 0], pixels[:, -1]
        ])
        
        center_color = self._meta_get_dominant_color(center)
        edge_color = self._meta_get_dominant_color(edges)
        
        return center_color != edge_color
    
    def _meta_extract_layers(self, pixels: np.ndarray) -> List[np.ndarray]:
        """Extracts concentric layers from region."""
        layers = []
        height, width = pixels.shape[:2]
        
        if height < 3 or width < 3:
            return [pixels]
        
        # Outer layer (edges)
        outer = np.concatenate([
            pixels[0, :], pixels[-1, :],
            pixels[1:-1, 0], pixels[1:-1, -1]
        ])
        layers.append(outer)
        
        # Middle layer (if exists)
        if height >= 5 and width >= 5:
            middle = np.concatenate([
                pixels[1, 1:-1], pixels[-2, 1:-1],
                pixels[2:-2, 1], pixels[2:-2, -2]
            ])
            layers.append(middle)
        
        # Inner core
        center_margin = max(height // 4, width // 4)
        if center_margin > 0:
            inner = pixels[center_margin:-center_margin, center_margin:-center_margin]
            if inner.size > 0:
                layers.append(inner)
        
        return layers
    
    def _meta_get_dominant_color(self, pixels: np.ndarray) -> int:
        """Returns most common color in region."""
        if pixels.size == 0:
            return 0
        
        values, counts = np.unique(pixels.flatten(), return_counts=True)
        return int(values[np.argmax(counts)])
    
    def _meta_calculate_center_ratio(self, layers: List[np.ndarray]) -> float:
        """Calculates ratio of center size to total region."""
        if len(layers) < 2:
            return 0.25
        
        total_size = sum(layer.size for layer in layers)
        center_size = layers[-1].size
        
        return center_size / total_size if total_size > 0 else 0.25
    
    def _meta_shows_color_transformation(self, pixels: np.ndarray) -> bool:
        """Checks if region shows evidence of color transformation."""
        unique_colors = len(np.unique(pixels))
        return unique_colors >= 2 and unique_colors <= 4
    
    def _meta_regions_overlap(self, pos1: Tuple[int, int], 
                             pos2: Tuple[int, int], 
                             threshold: int = 5) -> bool:
        """Checks if two positions are close (same region)."""
        distance = np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
        return distance < threshold
    
    def _meta_is_near_corner(self, pos: Tuple[int, int], 
                            frame_size: Tuple[int, int]) -> bool:
        """Checks if position is near a corner."""
        y, x = pos
        h, w = frame_size
        
        threshold = min(h, w) * 0.2
        corners = [(0, 0), (0, w-1), (h-1, 0), (h-1, w-1)]
        
        for cy, cx in corners:
            distance = np.sqrt((y - cy)**2 + (x - cx)**2)
            if distance < threshold:
                return True
        
        return False
    
    def _meta_is_near_edge(self, pos: Tuple[int, int], 
                          frame_size: Tuple[int, int]) -> bool:
        """Checks if position is near an edge."""
        y, x = pos
        h, w = frame_size
        
        threshold = min(h, w) * 0.15
        
        return (y < threshold or y > h - threshold or 
                x < threshold or x > w - threshold)
    
    # ========== END META-LEARNING METHODS ==========
    
    def _store_discovered_pattern(self, pattern_result: Dict[str, Any]) -> None:
        """
        Stores a pattern discovered by the meta-learner for future use.
        
        Args:
            pattern_result: Pattern detection result from meta-learner
        """
        try:
            pattern_type = pattern_result.get('pattern_type', 'unknown')
            rule = pattern_result.get('rule', {})
            confidence = pattern_result.get('confidence', 0.5)
            
            # Generate unique pattern ID based on rule
            import hashlib
            rule_str = json.dumps(rule, sort_keys=True)
            pattern_id = f"meta_{hashlib.md5(rule_str.encode()).hexdigest()[:16]}"
            
            # Check if pattern already exists
            existing = self.db.execute_query("""
                SELECT pattern_id, occurrence_count, success_count
                FROM discovered_patterns
                WHERE pattern_id = ?
            """, (pattern_id,))
            
            if existing:
                # Update existing pattern
                old_count = existing[0]['occurrence_count']
                old_success = existing[0]['success_count']
                
                new_count = old_count + 1
                new_confidence = min((old_success + 1) / new_count, 1.0)
                
                self.db.execute_query("""
                    UPDATE discovered_patterns
                    SET occurrence_count = ?,
                        confidence_score = ?,
                        last_seen_at = ?
                    WHERE pattern_id = ?
                """, (new_count, new_confidence, datetime.now().isoformat(), pattern_id))
                
                logger.info(f"📊 Updated meta-pattern {pattern_id}: {new_count} occurrences")
            else:
                # Create new pattern
                pattern_name = f"meta_{pattern_type}_{rule['type']}"
                
                self.db.execute_query("""
                    INSERT INTO discovered_patterns (
                        pattern_id, pattern_name, pattern_type, pattern_signature,
                        occurrence_count, success_count, success_rate,
                        confidence_score, discovered_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pattern_id, pattern_name, pattern_type,
                    json.dumps(rule), 1, 0, 0.0, confidence,
                    datetime.now().isoformat()
                ))
                
                logger.info(f"🆕 Stored meta-learned pattern: {pattern_name}")
        
        except Exception as e:
            logger.error(f"Error storing discovered pattern: {e}")


# Simple gameplay strategies that can be used as action callbacks

async def random_strategy(game_state: GameState, action_handler: ActionHandler) -> str:
    """Random action selection strategy."""
    return action_handler.get_random_action(game_state.available_actions)

async def conservative_strategy(game_state: GameState, action_handler: ActionHandler) -> str:
    """Conservative strategy avoiding ACTION6."""
    safe_actions = [a for a in (game_state.available_actions or []) if a != "ACTION6"]
    if not safe_actions:
        safe_actions = ["ACTION1", "ACTION2", "ACTION3", "ACTION4", "ACTION5", "ACTION7"]
    return action_handler.get_random_action(safe_actions)

async def exploration_strategy(game_state: GameState, action_handler: ActionHandler) -> GameState:
    """Exploration strategy that tries different actions."""
    # Prefer ACTION6 for exploration
    if "ACTION6" in (game_state.available_actions or []):
        x, y = action_handler.get_random_coordinates(game_state.frame)
        return await action_handler.send_action_6(x, y, game_state.frame)
    else:
        action = action_handler.get_random_action(game_state.available_actions)
        method_name = f"send_{action.lower()}"
        method = getattr(action_handler, method_name)
        return await method()