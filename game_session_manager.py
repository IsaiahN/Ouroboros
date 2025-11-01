"""
Game Session Manager

Handles the lifecycle of game sessions including:
- Starting new sessions
- Managing game state
- Graceful shutdown
- Session persistence

Clean implementation focused only on core game mechanics.
"""

import asyncio
import logging
import signal
import sys
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import uuid

from arc_api_client import ARCClient, GameState
from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


class GameSessionManager:
    """Manages game sessions and handles graceful shutdown."""

    def __init__(self, api_key: Optional[str] = None, db_path: str = "core_data.db"):
        """Initialize the session manager.

        Args:
            api_key: ARC API key
            db_path: Path to database file
        """
        self.api_key = api_key
        self.db = DatabaseInterface(db_path)
        self.client = None
        self.current_session_id = None
        self.current_game_id = None
        self.is_running = False
        self.shutdown_handlers = []

        # Statistics
        self.session_stats = {
            'total_actions': 0,
            'total_games': 0,
            'total_wins': 0,
            'total_score': 0.0,
            'games_played': []
        }

        # Setup graceful shutdown
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.shutdown())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def add_shutdown_handler(self, handler: Callable):
        """Add a custom shutdown handler.

        Args:
            handler: Async function to call during shutdown
        """
        self.shutdown_handlers.append(handler)

    async def start_session(self, mode: str = "gameplay", game_id: Optional[str] = None) -> str:
        """Start a new game session.

        Args:
            mode: Session mode
            game_id: Optional specific game ID for the session

        Returns:
            Session ID
        """
        if self.is_running:
            raise RuntimeError("Session already running")

        # Generate session ID
        self.current_session_id = f"session_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"

        # Initialize database session
        self.db.create_session(
            session_id=self.current_session_id,
            mode=mode,
            game_id=game_id
        )

        # Initialize ARC client
        self.client = ARCClient(api_key=self.api_key)

        self.is_running = True
        logger.info(f"Started session: {self.current_session_id}")

        return self.current_session_id

    async def create_game(self, game_id: str, tags: Optional[list] = None) -> Dict[str, Any]:
        """Create and initialize a new game.

        Args:
            game_id: Game ID to create
            tags: Optional tags for the scorecard

        Returns:
            Game initialization data
        """
        if not self.is_running:
            raise RuntimeError("No active session")

        if not self.client:
            self.client = ARCClient(api_key=self.api_key)

        # Ensure client session is active
        if not self.client.session:
            await self.client.__aenter__()

        # Generate tags if not provided
        if not tags:
            tags = self.client.generate_tags(
                game_id=game_id,
                session_id=self.current_session_id
            )

        # Create game via API
        game_data = await self.client.create_game(game_id, tags)

        # Store game start in database
        self.db.save_game_result({
            'game_id': game_id,
            'session_id': self.current_session_id,
            'start_time': datetime.now(),
            'status': 'started',
            'final_score': game_data.get('score', 0.0),
            'total_actions': 0,
            'available_actions': game_data.get('available_actions', [])
        })

        self.current_game_id = game_id
        logger.info(f"Created game: {game_id} with actions: {game_data.get('available_actions', [])}")

        return game_data

    async def send_action(self, action: str, **kwargs) -> GameState:
        """Send an action to the current game.

        Args:
            action: Action to send (ACTION1, ACTION2, etc.)
            **kwargs: Additional action parameters

        Returns:
            New game state
        """
        if not self.is_running or not self.client:
            raise RuntimeError("No active session or client")

        if not self.current_game_id:
            raise RuntimeError("No active game")
        
        # Check if client session is still valid, recreate if needed
        if self.client and not self.client.session:
            logger.warning("Client session lost, recreating...")
            await self.client.__aenter__()

        # Record action details for tracing
        action_start_time = datetime.now()
        
        # Normalize action to string format
        if isinstance(action, int):
            action = f"ACTION{action}"
        
        # Extract action number (ACTION1 -> 1, ACTION6 -> 6, etc.)
        if isinstance(action, str) and action.startswith('ACTION'):
            action_number = int(action.replace('ACTION', ''))
        else:
            logger.warning(f"Invalid action format: {action}, defaulting to action 1")
            action = "ACTION1"
            action_number = 1

        try:
            # Send action via API
            game_state = await self.client.send_action(action, **kwargs)

            # Update session statistics
            self.session_stats['total_actions'] += 1

            # Save action trace (DO NOT save frames - they are too large and unhashable)
            self.db.save_action_trace({
                'session_id': self.current_session_id,
                'game_id': self.current_game_id,
                'action_number': action_number,
                'coordinates': kwargs.get('coordinates') if action == 'ACTION6' else None,
                'timestamp': action_start_time,
                'frame_before': None,  # Don't save frame - too large
                'frame_after': None,   # Don't save frame - too large
                'frame_changed': kwargs.get('frame_changed', False),
                'score_before': kwargs.get('score_before', 0.0),
                'score_after': game_state.score,
                'score_change': game_state.score - kwargs.get('score_before', 0.0),
                'response_data': {
                    'action': action,
                    'state': game_state.state,
                    'available_actions': game_state.available_actions
                }
            })

            # Save score
            if self.current_session_id and self.current_game_id:
                self.db.save_score(
                    self.current_session_id,
                    self.current_game_id,
                    self.session_stats['total_actions'],
                    game_state.score
                )

            # Update action effectiveness
            score_change = game_state.score - kwargs.get('score_before', 0.0)
            success = score_change > 0 or kwargs.get('frame_changed', False)

            self.db.update_action_effectiveness(
                self.current_game_id,
                action_number,
                success,
                score_change
            )

            logger.debug(f"Action {action} -> State: {game_state.state}, Score: {game_state.score}")

            return game_state

        except Exception as e:
            logger.error(f"Error sending action {action}: {e}")
            raise

    async def finish_game(self, final_state: str, final_score: float, level_completions: int = 0, actions_taken: int = 0):
        """Finish the current game and save results.

        Args:
            final_state: Final game state ('WIN', 'GAME_OVER', etc.)
            final_score: Final score achieved
            level_completions: Number of levels completed (CRITICAL for evolution)
            actions_taken: Actual actions taken THIS GAME (not session total)
        """
        if not self.current_game_id:
            return

        # Update session statistics
        self.session_stats['total_games'] += 1
        self.session_stats['total_score'] += final_score

        if final_state == 'WIN':
            self.session_stats['total_wins'] += 1

        self.session_stats['games_played'].append({
            'game_id': self.current_game_id,
            'final_state': final_state,
            'final_score': final_score,
            'end_time': datetime.now()
        })

        # Save final game result
        self.db.save_game_result({
            'game_id': self.current_game_id,
            'session_id': self.current_session_id,
            'end_time': datetime.now(),
            'status': 'completed' if final_state == 'WIN' else 'failed',
            'final_score': final_score,
            'total_actions': actions_taken if actions_taken > 0 else self.session_stats['total_actions'],  # CRITICAL FIX: Use per-game count!
            'win_detected': final_state == 'WIN',
            'level_completions': level_completions  # CRITICAL FIX: Store level completions!
        })
        
        # CRITICAL: Force WAL checkpoint after EVERY game to prevent data loss on force-close
        try:
            self.db.checkpoint_wal()
            logger.debug(f"WAL checkpoint after game {self.current_game_id}")
        except Exception as e:
            logger.warning(f"Failed to checkpoint WAL after game: {e}")

        # Close scorecard if client is available
        if self.client and self.client.current_scorecard_id:
            try:
                await self.client.close_scorecard()
            except Exception as e:
                logger.warning(f"Error closing scorecard: {e}")

        logger.info(f"Finished game {self.current_game_id}: {final_state}, Score: {final_score}")
        self.current_game_id = None

    async def get_available_games(self) -> list:
        """Get list of available games from the API.

        Returns:
            List of available games
        """
        if not self.client:
            self.client = ARCClient(api_key=self.api_key)

        if not self.client.session:
            await self.client.__aenter__()

        return await self.client.get_available_games()

    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics.

        Returns:
            Dictionary of session statistics
        """
        stats = self.session_stats.copy()
        stats['session_id'] = self.current_session_id
        stats['win_rate'] = (
            self.session_stats['total_wins'] / self.session_stats['total_games']
            if self.session_stats['total_games'] > 0 else 0.0
        )
        stats['avg_score'] = (
            self.session_stats['total_score'] / self.session_stats['total_games']
            if self.session_stats['total_games'] > 0 else 0.0
        )
        return stats

    async def update_session_in_db(self):
        """Update session statistics in database."""
        if not self.current_session_id:
            return

        stats = self.get_session_stats()
        self.db.update_session_stats(self.current_session_id, {
            'total_actions': stats['total_actions'],
            'total_wins': stats['total_wins'],
            'total_games': stats['total_games'],
            'win_rate': stats['win_rate'],
            'avg_score': stats['avg_score']
        })

    async def shutdown(self):
        """Gracefully shutdown the session."""
        if not self.is_running:
            return

        logger.info("Shutting down game session...")

        try:
            # Finish current game if active
            if self.current_game_id:
                await self.finish_game('CANCELLED', 0.0, 0, 0)  # No levels/actions for cancelled games

            # Update session in database
            await self.update_session_in_db()

            # End session
            if self.current_session_id:
                self.db.end_session(self.current_session_id)

            # Close ARC client
            if self.client:
                await self.client.close()

            # Call custom shutdown handlers
            for handler in self.shutdown_handlers:
                try:
                    await handler()
                except Exception as e:
                    logger.error(f"Error in shutdown handler: {e}")

            # Close database
            self.db.close()

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

        finally:
            self.is_running = False
            logger.info("Session shutdown complete")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.shutdown()


class SessionContext:
    """Context manager for game sessions."""

    def __init__(self, manager: GameSessionManager):
        self.manager = manager

    async def __aenter__(self):
        await self.manager.start_session()
        return self.manager

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.manager.shutdown()