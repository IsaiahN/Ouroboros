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
from typing import Dict, Any, List, Optional, Callable
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
            'max_total_actions': 500,  # Max total actions across all levels
            'action_timeout': 30.0,
            'strategy': 'balanced',
            'enable_random_exploration': True,
            'coordinate_retry_limit': 3,
            'enable_pattern_learning': True,  # Toggle pattern learning
            'learning_mode': 'smart_exploration'  # 'exploit', 'explore', 'smart_exploration'
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

        # Pattern Learning: Check for known winning sequence (Rule 10: integrated)
        if self.game_config.get('enable_pattern_learning', True):
            learning_mode = self.game_config.get('learning_mode', 'smart_exploration')
            
            if learning_mode in ['exploit', 'smart_exploration']:
                known_sequence = self._get_best_sequence_for_game(game_id)
                
                if known_sequence:
                    logger.info(f"Attempting to replay known winning sequence for {game_id}")
                    replay_result = await self._try_replay_sequence(game_id, known_sequence)
                    
                    if replay_result and replay_result['win']:
                        logger.info(f"Successfully replayed winning sequence!")
                        return replay_result
                    else:
                        logger.info(f"Sequence replay failed, falling back to normal gameplay")

        try:
            # Start session if not already running
            if not self.session_manager.is_running:
                await self.session_manager.start_session(game_id=game_id)
            
            # Create game
            game_data = await self.session_manager.create_game(game_id)
            game_state = GameState.from_dict(game_data)

            action_count = 0
            level_action_count = 0  # Track actions per level
            start_time = datetime.now()
            previous_score = 0.0  # Track score for level completion detection
            level_completions = 0  # Track how many levels completed
            current_level = 1

            # Game loop
            while (game_state.state == "NOT_FINISHED" and
                   action_count < self.game_config['max_total_actions']):

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
                        
                        # Pattern Learning: Capture level completion sequence
                        if self.game_config.get('enable_pattern_learning', True):
                            sequence_id = self._capture_winning_sequence(
                                game_id, 
                                game_state.score, 
                                level_number=current_level,
                                reason=f"level_{current_level}_completion"
                            )
                            if sequence_id:
                                logger.info(f"✅ Captured level {current_level} winning sequence: {sequence_id}")
                        
                        # Move to next level
                        current_level += 1
                        level_action_count = 0  # Reset level action counter
                    
                    # Check if exceeded max actions for this level
                    if level_action_count >= self.game_config['max_actions_per_level']:
                        logger.warning(f"⏱️ Reached max actions ({self.game_config['max_actions_per_level']}) for level {current_level}")
                        logger.info(f"Level {current_level} timed out. Ending game.")
                        # Break out - level timed out
                        break
                    
                    logger.debug(f"Action {action_count} (Level {current_level}-{level_action_count}): State={game_state.state}, Score={game_state.score}")

                    # Check for completion
                    if game_state.state in ["WIN", "GAME_OVER"]:
                        break

                except Exception as e:
                    logger.error(f"Error in action {action_count}: {e}", exc_info=True)
                    # Continue with next action unless it's a critical error
                    if "authentication" in str(e).lower() or "api_key" in str(e).lower():
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

            # Finish game in session manager
            await self.session_manager.finish_game(game_state.state, game_state.score)

            # Pattern Learning: Capture final WIN sequence (Rule 2: Database-only)
            if results['win'] and self.game_config.get('enable_pattern_learning', True):
                # Capture full game completion (all levels)
                sequence_id = self._capture_winning_sequence(
                    game_id, 
                    game_state.score,
                    level_number=current_level,
                    reason="full_game_win"
                )
                if sequence_id:
                    results['learned_sequence_id'] = sequence_id

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

        Args:
            game_state: Current game state

        Returns:
            Action to take
        """
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
            # CORRECT ACTION6 USAGE: Analyze frame and select intelligent coordinates
            # DO NOT use random coordinates - this is treating ACTION6 like a touchscreen
            x, y, reason = self.action_handler.get_smart_coordinates(
                game_state.frame,
                strategy="visual"  # Use visual analysis
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

            # Play games
            if max_games:
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
            sequence_id = f"seq_{uuid.uuid4().hex[:16]}"
            
            # Get frames
            initial_frame = json.loads(action_traces[0]['frame_before']) if action_traces[0].get('frame_before') else []
            final_frame = json.loads(action_traces[-1]['frame_after']) if action_traces[-1].get('frame_after') else []
            
            # Detect pattern tags
            pattern_tags = self._detect_pattern_tags(actions, coordinates)
            game_type = self._classify_game_type(actions)
            
            # Store in database (Rule 2)
            self.db.execute_query("""
                INSERT INTO winning_sequences (
                    sequence_id, game_id, level_number, agent_id, session_id,
                    action_sequence, coordinate_sequence, total_actions, total_score,
                    efficiency_score, initial_frame, final_frame, pattern_tags,
                    game_type, discovered_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sequence_id, game_id, level_number, 'core_agent', session_id,
                json.dumps(actions), json.dumps(coordinates), len(actions),
                final_score, efficiency, json.dumps(initial_frame),
                json.dumps(final_frame), json.dumps(pattern_tags),
                game_type, datetime.now().isoformat()
            ))
            
            logger.info(f"Captured winning sequence {sequence_id} for level {level_number} ({reason}): "
                       f"{len(actions)} actions, efficiency {efficiency:.2f}, tags: {pattern_tags}")
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

    def _get_best_sequence_for_game(self, game_id: str) -> Optional[Dict]:
        """
        Get best known winning sequence for a game (Rule 2: from database).
        
        Args:
            game_id: Game to check
            
        Returns:
            Sequence dict or None
        """
        if not self.game_config.get('enable_pattern_learning', True):
            return None
            
        try:
            sequences = self.db.execute_query("""
                SELECT * FROM winning_sequences
                WHERE game_id = ?
                ORDER BY efficiency_score DESC, total_score DESC
                LIMIT 1
            """, (game_id,))
            
            if sequences:
                seq = sequences[0]
                # Update reference counter
                self.db.execute_query("""
                    UPDATE winning_sequences
                    SET times_referenced = times_referenced + 1,
                        last_referenced = ?
                    WHERE sequence_id = ?
                """, (datetime.now().isoformat(), seq['sequence_id']))
                
                logger.info(f"Found known winning sequence for {game_id}: "
                           f"{seq['total_actions']} actions, efficiency {seq['efficiency_score']:.2f}")
                return seq
                
        except Exception as e:
            logger.debug(f"No winning sequence found for {game_id}: {e}")
            
        return None

    async def _try_replay_sequence(self, game_id: str, sequence: Dict) -> Optional[Dict[str, Any]]:
        """
        Try to replay a known winning sequence (Rule 7: Real actions).
        
        Args:
            game_id: Game to play
            sequence: Winning sequence to replay
            
        Returns:
            Game results or None if failed
        """
        try:
            if not self.session_manager.is_running:
                await self.session_manager.start_session(game_id=game_id)
            
            game_data = await self.session_manager.create_game(game_id)
            game_state = GameState.from_dict(game_data)
            
            actions = json.loads(sequence['action_sequence'])
            coordinates = json.loads(sequence.get('coordinate_sequence', '[]'))
            
            start_time = datetime.now()
            action_count = 0
            coord_index = 0
            
            for action_num in actions:
                if game_state.state != "NOT_FINISHED":
                    break
                
                if action_num == 6 and coord_index < len(coordinates):
                    coord = coordinates[coord_index]
                    x, y = coord.get('x', 0), coord.get('y', 0)
                    game_state = await self.action_handler.send_action_6(x, y, game_state.frame)
                    coord_index += 1
                else:
                    action = f"ACTION{action_num}"
                    game_state = await self._execute_action(action, game_state)
                
                action_count += 1
            
            await self.session_manager.finish_game(game_state.state, game_state.score)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result = {
                'game_id': game_id,
                'final_state': game_state.state,
                'final_score': game_state.score,
                'actions_taken': action_count,
                'duration_seconds': duration,
                'win': game_state.state == "WIN",
                'method': 'replay_sequence'
            }
            
            logger.info(f"Sequence replay result: {'WIN' if result['win'] else 'LOSS'}")
            return result
            
        except Exception as e:
            logger.error(f"Error replaying sequence: {e}")
            return None


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