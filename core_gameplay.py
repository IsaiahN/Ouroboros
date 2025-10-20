"""
Core Gameplay Logic

Provides the fundamental gameplay loop and decision-making logic.
Contains only essential game mechanics without architect/governor/director complexity.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
import random
from datetime import datetime

from game_session_manager import GameSessionManager
from action_handler import ActionHandler
from arc_api_client import GameState

logger = logging.getLogger(__name__)


class GameplayEngine:
    """Core engine for playing ARC games."""

    def __init__(self, api_key: str = None, db_path: str = "core_data.db"):
        """Initialize gameplay engine.

        Args:
            api_key: ARC API key
            db_path: Database file path
        """
        self.session_manager = GameSessionManager(api_key, db_path)
        self.action_handler = ActionHandler(self.session_manager)
        self.game_config = {
            'max_actions_per_game': 100,
            'action_timeout': 30.0,
            'strategy': 'balanced',
            'enable_random_exploration': True,
            'coordinate_retry_limit': 3
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
        """Play a single game to completion.

        Args:
            game_id: Game ID to play
            action_callback: Optional callback function for custom action selection

        Returns:
            Game results dictionary
        """
        logger.info(f"Starting game: {game_id}")

        try:
            # Start session if not already running
            if not self.session_manager.is_running:
                await self.session_manager.start_session(game_id=game_id)
            
            # Create game
            game_data = await self.session_manager.create_game(game_id)
            game_state = GameState.from_dict(game_data)

            action_count = 0
            start_time = datetime.now()

            # Game loop
            while (game_state.state == "NOT_FINISHED" and
                   action_count < self.game_config['max_actions_per_game']):

                try:
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
                    logger.debug(f"Action {action_count}: State={game_state.state}, Score={game_state.score}")

                    # Check for completion
                    if game_state.state in ["WIN", "GAME_OVER"]:
                        break

                except Exception as e:
                    logger.error(f"Error in action {action_count}: {e}")
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
                'start_time': start_time,
                'end_time': end_time
            }

            # Finish game in session manager
            await self.session_manager.finish_game(game_state.state, game_state.score)

            logger.info(f"Game {game_id} completed: {game_state.state}, Score: {game_state.score}, Actions: {action_count}")
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
            return await self.action_handler.send_action_6(x, y, game_state.frame)
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

    def get_performance_stats(self, session_id: str = None) -> Dict[str, Any]:
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