"""
ARC API Adapter - Wrapper around the official arc_agi SDK
=========================================================

This module provides a clean interface to the ARC-AGI-3 game environments
using the official arc_agi Python SDK.

Usage:
    from arc_api_adapter import ArcadeWrapper, GameConfig
    from arcengine import GameAction, GameState
    
    wrapper = ArcadeWrapper()
    games = wrapper.list_games()
    
    env = wrapper.create_environment(GameConfig(game_id="ls20"))
    obs = env.step(GameAction.ACTION1)
    
    if obs.state == GameState.WIN:
        print("Game won!")

Key Classes:
    - ArcadeWrapper: Main entry point, wraps arc_agi.Arcade
    - GameEnvironment: Wraps arc_agi.EnvironmentWrapper
    - GameConfig: Configuration for creating environments
    - GameInfo: Information about available games
    - Observation: Processed observation from game step
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable, Set
import logging

# Import from official arc_agi SDK (no stubs available)
import arc_agi  # type: ignore
from arc_agi import Arcade, OperationMode  # type: ignore
from arcengine import GameAction, GameState, FrameDataRaw  # type: ignore


# Re-export key types for convenience
__all__ = [
    'ArcadeWrapper',
    'GameEnvironment', 
    'GameConfig',
    'GameInfo',
    'Observation',
    'GameAction',
    'GameState',
    'OperationMode',
]


@dataclass
class GameConfig:
    """Configuration for creating a game environment."""
    game_id: str
    seed: int = 0
    scorecard_id: Optional[str] = None
    save_recording: bool = False
    render_mode: Optional[str] = None  # "terminal", "terminal-fast", "human", None
    custom_renderer: Optional[Callable[[int, FrameDataRaw], None]] = None
    
    def __post_init__(self):
        # Validate render_mode
        valid_modes: Set[Optional[str]] = {None, "terminal", "terminal-fast", "human"}
        if self.render_mode not in valid_modes:
            raise ValueError(f"render_mode must be one of {valid_modes}, got '{self.render_mode}'")


@dataclass
class GameInfo:
    """Information about an available game."""
    game_id: str
    title: str
    tags: List[str] = field(default_factory=lambda: [])
    
    @classmethod
    def from_environment_info(cls, env_info: Any) -> 'GameInfo':
        """Create from arc_agi EnvironmentInfo object."""
        return cls(
            game_id=str(getattr(env_info, 'game_id', '')),
            title=str(getattr(env_info, 'title', getattr(env_info, 'game_id', ''))),
            tags=list(getattr(env_info, 'tags', [])),
        )


@dataclass
class Observation:
    """
    Processed observation from a game step.
    
    Wraps FrameDataRaw with convenient accessors.
    
    FrameDataRaw fields:
        - game_id: str
        - state: GameState
        - levels_completed: int
        - win_levels: int (levels needed to win)
        - action_input: ActionInput
        - guid: Optional[str]
        - full_reset: bool
        - available_actions: list[int]
        - frame: list[list[int]] (added dynamically by game)
    """
    raw: FrameDataRaw
    
    @property
    def frame(self) -> Optional[List[List[int]]]:
        """Get the game frame as 2D list."""
        # Frame is added dynamically by games, may not always exist
        return getattr(self.raw, 'frame', None) if self.raw else None
    
    @property
    def state(self) -> GameState:
        """Get the current game state."""
        return self.raw.state if self.raw else GameState.NOT_PLAYED
    
    @property
    def game_id(self) -> str:
        """Get the game ID."""
        return self.raw.game_id if self.raw else ""
    
    @property
    def levels_completed(self) -> int:
        """Get number of levels completed."""
        return self.raw.levels_completed if self.raw else 0
    
    @property
    def win_levels(self) -> int:
        """Get number of levels needed to win."""
        return self.raw.win_levels if self.raw else 0
    
    @property
    def score(self) -> float:
        """
        Get the current score.
        
        Score is calculated as levels_completed / win_levels.
        Returns 0.0 if win_levels is 0 to avoid division by zero.
        """
        if not self.raw or self.win_levels == 0:
            return 0.0
        return self.levels_completed / self.win_levels
    
    @property
    def available_actions(self) -> List[int]:
        """Get list of available action indices."""
        return self.raw.available_actions if self.raw else []
    
    @property
    def full_reset(self) -> bool:
        """Check if this was a full reset."""
        return self.raw.full_reset if self.raw else False
    
    @property
    def guid(self) -> Optional[str]:
        """Get the unique identifier for this frame."""
        return self.raw.guid if self.raw else None
    
    @property
    def is_win(self) -> bool:
        """Check if game is won."""
        return self.state == GameState.WIN
    
    @property
    def is_game_over(self) -> bool:
        """Check if game is over (death/failure)."""
        return self.state == GameState.GAME_OVER
    
    @property
    def is_terminal(self) -> bool:
        """Check if game has ended (win or game over)."""
        return self.state in (GameState.WIN, GameState.GAME_OVER)
    
    @property
    def is_playing(self) -> bool:
        """Check if game is still in progress."""
        return self.state == GameState.NOT_FINISHED
    
    @property
    def is_level_complete(self) -> bool:
        """
        Check if a level was just completed.
        
        Note: This is a heuristic - compare with previous observation
        to detect actual level completion.
        """
        return self.levels_completed > 0 and not self.is_terminal
    
    @property
    def is_full_win(self) -> bool:
        """
        Check if the game is fully won (all levels completed).
        
        This is the "Holy Grail" - complete game victory.
        """
        return self.state == GameState.WIN and self.levels_completed >= self.win_levels


class GameEnvironment:
    """
    Wrapper around arc_agi EnvironmentWrapper.
    
    Provides a clean interface for interacting with a single game environment.
    """
    
    def __init__(self, env: Any, game_id: str):
        """
        Initialize with an arc_agi EnvironmentWrapper.
        
        Args:
            env: The arc_agi EnvironmentWrapper instance
            game_id: The game identifier
        """
        self._env: Any = env
        self._game_id = game_id
        self._step_count = 0
        self._last_observation: Optional[Observation] = None
    
    @property
    def game_id(self) -> str:
        """Get the game identifier."""
        return self._game_id
    
    @property
    def step_count(self) -> int:
        """Get the number of steps taken."""
        return self._step_count
    
    @property
    def action_space(self) -> List[GameAction]:
        """Get available actions for current state."""
        return list(self._env.action_space) if self._env else []
    
    @property
    def observation(self) -> Optional[Observation]:
        """Get the last observation."""
        return self._last_observation
    
    @property
    def info(self) -> Any:
        """Get environment info."""
        return self._env.info if self._env else None
    
    def reset(self) -> Optional[Observation]:
        """
        Reset the environment to initial state.
        
        Returns:
            Observation with initial game state, or None if reset failed.
        """
        raw = self._env.reset()
        if raw:
            self._step_count = 0
            self._last_observation = Observation(raw)
            return self._last_observation
        return None
    
    def step(
        self,
        action: GameAction,
        data: Optional[Dict[str, Any]] = None,
        reasoning: Optional[Dict[str, Any]] = None,
    ) -> Optional[Observation]:
        """
        Take an action in the environment.
        
        Args:
            action: The GameAction to take (ACTION1, ACTION2, etc.)
            data: Optional data dict for complex actions (x, y coordinates)
            reasoning: Optional reasoning dict for recordings
        
        Returns:
            Observation with updated game state, or None if step failed.
        
        Example:
            # Simple action
            obs = env.step(GameAction.ACTION1)
            
            # Complex action with coordinates
            obs = env.step(GameAction.ACTION6, data={"x": 32, "y": 32})
        """
        # Handle complex actions that require coordinates
        if action.is_complex() and data is None:
            raise ValueError(
                f"Action {action.name} is complex and requires data with 'x' and 'y' coordinates"
            )
        
        raw = self._env.step(action, data=data, reasoning=reasoning)
        if raw:
            self._step_count += 1
            self._last_observation = Observation(raw)
            return self._last_observation
        return None
    
    def get_available_actions(self) -> List[str]:
        """Get list of available action names."""
        return [a.name for a in self.action_space]
    
    def is_action_available(self, action: GameAction) -> bool:
        """Check if a specific action is available."""
        return action in self.action_space
    
    def is_action_complex(self, action: GameAction) -> bool:
        """Check if an action requires coordinate data."""
        return action.is_complex()


class ArcadeWrapper:
    """
    Main entry point for ARC-AGI-3 game interactions.
    
    Wraps the official arc_agi.Arcade class with a clean interface
    for our system's needs.
    
    Usage:
        wrapper = ArcadeWrapper()
        
        # List available games
        games = wrapper.list_games()
        
        # Create an environment
        config = GameConfig(game_id="ls20", render_mode="terminal")
        env = wrapper.create_environment(config)
        
        # Play the game
        obs = env.reset()
        while not obs.is_terminal:
            action = choose_action(obs)
            obs = env.step(action)
        
        # Get results
        scorecard = wrapper.get_scorecard()
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        operation_mode: str = "NORMAL",
        environments_dir: str = "environment_files",
        recordings_dir: str = "recordings",
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the ARC-AGI wrapper.
        
        Args:
            api_key: API key for remote games. If None, uses ARC_API_KEY env var
                     or anonymous key.
            operation_mode: One of "NORMAL", "OFFLINE", "ONLINE"
                - NORMAL: Both local and remote games (default)
                - OFFLINE: Local games only (fast, no rate limits)
                - ONLINE: Remote games only (enables scorecards/replays)
            environments_dir: Directory for local game files
            recordings_dir: Directory for saving game recordings
            logger: Optional logger instance
        """
        # Convert string operation mode to enum
        try:
            mode = OperationMode[operation_mode.upper()]
        except KeyError:
            valid = [m.name for m in OperationMode]
            raise ValueError(f"operation_mode must be one of {valid}, got '{operation_mode}'")
        
        # Create the underlying Arcade instance
        self._arcade = Arcade(
            operation_mode=mode,
            arc_api_key=api_key or "",
            environments_dir=environments_dir,
            recordings_dir=recordings_dir,
            logger=logger,
        )
        
        self._operation_mode = mode
        self._current_scorecard_id: Optional[str] = None
        self._logger = logger or logging.getLogger(__name__)
    
    @property
    def operation_mode(self) -> OperationMode:
        """Get the current operation mode."""
        return self._operation_mode
    
    @property
    def is_offline(self) -> bool:
        """Check if running in offline mode."""
        return self._operation_mode == OperationMode.OFFLINE
    
    @property
    def is_online(self) -> bool:
        """Check if running in online mode."""
        return self._operation_mode == OperationMode.ONLINE
    
    def list_games(self) -> List[GameInfo]:
        """
        Get all available games.
        
        Returns:
            List of GameInfo objects with game_id, title, and tags.
        """
        envs = self._arcade.get_environments()
        return [GameInfo.from_environment_info(e) for e in envs]
    
    def list_game_ids(self) -> List[str]:
        """
        Get just the game IDs of all available games.
        
        Returns:
            List of game ID strings.
        """
        return [g.game_id for g in self.list_games()]
    
    def create_environment(self, config: GameConfig) -> Optional[GameEnvironment]:
        """
        Create a game environment.
        
        Args:
            config: GameConfig with game_id and optional settings
        
        Returns:
            GameEnvironment ready to play, or None if creation failed.
        
        Example:
            config = GameConfig(
                game_id="ls20",
                render_mode="terminal",
                save_recording=True
            )
            env = wrapper.create_environment(config)
        """
        try:
            # In OFFLINE mode, use empty string for scorecard_id to avoid validation error
            scorecard_id = config.scorecard_id
            if self.is_offline and scorecard_id is None:
                scorecard_id = ''
            
            env = self._arcade.make(
                game_id=config.game_id,
                seed=config.seed,
                scorecard_id=scorecard_id,
                save_recording=config.save_recording,
                render_mode=config.render_mode,
                renderer=config.custom_renderer,
            )
            
            if env:
                return GameEnvironment(env, config.game_id)
            return None
            
        except Exception as e:
            self._logger.error(f"Failed to create environment for {config.game_id}: {e}")
            return None
    
    def make(
        self,
        game_id: str,
        seed: int = 0,
        render_mode: Optional[str] = None,
        save_recording: bool = False,
    ) -> Optional[GameEnvironment]:
        """
        Convenience method to create an environment with minimal config.
        
        Args:
            game_id: Game identifier (e.g., "ls20")
            seed: Random seed (default 0)
            render_mode: "terminal", "terminal-fast", "human", or None
            save_recording: Whether to save recording
        
        Returns:
            GameEnvironment ready to play.
        """
        config = GameConfig(
            game_id=game_id,
            seed=seed,
            render_mode=render_mode,
            save_recording=save_recording,
        )
        return self.create_environment(config)
    
    # -------------------------------------------------------------------------
    # Scorecard Management
    # -------------------------------------------------------------------------
    
    def create_scorecard(
        self,
        source_url: Optional[str] = None,
        tags: Optional[List[str]] = None,
        opaque: Optional[Any] = None,
    ) -> Optional[str]:
        """
        Create a new scorecard for tracking game runs.
        
        Args:
            source_url: Optional URL (e.g., your repo)
            tags: Optional list of tags for filtering
            opaque: Optional arbitrary data
        
        Returns:
            Scorecard ID string, or None if creation failed.
        """
        if self.is_offline:
            self._logger.warning("Scorecards not available in OFFLINE mode")
            return None
        
        try:
            scorecard_id = self._arcade.create_scorecard(
                source_url=source_url,
                tags=tags or ["ouroboros"],
                opaque=opaque,
            )
            self._current_scorecard_id = scorecard_id
            return scorecard_id
        except Exception as e:
            self._logger.error(f"Failed to create scorecard: {e}")
            return None
    
    def get_scorecard(self, scorecard_id: Optional[str] = None):
        """
        Get scorecard results.
        
        Args:
            scorecard_id: Specific scorecard ID, or None for default/current
        
        Returns:
            Scorecard object with results, or None if not available.
        """
        if self.is_offline:
            return None
        
        try:
            return self._arcade.get_scorecard(scorecard_id=scorecard_id)
        except Exception as e:
            self._logger.error(f"Failed to get scorecard: {e}")
            return None
    
    def close_scorecard(self, scorecard_id: Optional[str] = None):
        """
        Close and finalize a scorecard.
        
        Args:
            scorecard_id: Specific scorecard ID, or None for default/current
        
        Returns:
            Final scorecard with results, or None if not available.
        """
        if self.is_offline:
            return None
        
        try:
            result = self._arcade.close_scorecard(scorecard_id=scorecard_id)
            if scorecard_id == self._current_scorecard_id:
                self._current_scorecard_id = None
            return result
        except Exception as e:
            self._logger.error(f"Failed to close scorecard: {e}")
            return None


# =============================================================================
# Utility Functions
# =============================================================================

def action_from_string(action_str: str) -> GameAction:
    """
    Convert action string to GameAction enum.
    
    Args:
        action_str: Action name like "ACTION1", "RESET", etc.
    
    Returns:
        Corresponding GameAction enum value.
    
    Raises:
        ValueError: If action_str is not a valid action name.
    """
    try:
        return GameAction[action_str.upper()]
    except KeyError:
        valid = [a.name for a in GameAction]
        raise ValueError(f"Invalid action '{action_str}'. Valid actions: {valid}")


def action_to_string(action: GameAction) -> str:
    """Convert GameAction enum to string."""
    return action.name


def get_all_actions() -> List[GameAction]:
    """Get list of all possible actions."""
    return list(GameAction)


def get_simple_actions() -> List[GameAction]:
    """Get list of simple actions (no coordinates needed)."""
    return [a for a in GameAction if not a.is_complex()]


def get_complex_actions() -> List[GameAction]:
    """Get list of complex actions (require coordinates)."""
    return [a for a in GameAction if a.is_complex()]


# =============================================================================
# Quick Test
# =============================================================================

if __name__ == "__main__":
    import sys
    
    print("ARC API Adapter - Quick Test")
    print("=" * 50)
    
    # Determine mode from args
    mode = "OFFLINE"
    if len(sys.argv) > 1:
        mode = sys.argv[1].upper()
    
    wrapper = ArcadeWrapper(operation_mode=mode)
    
    print(f"\nOperation Mode: {wrapper.operation_mode.name}")
    print(f"Is Offline: {wrapper.is_offline}")
    
    # List games
    games = wrapper.list_games()
    print(f"\nAvailable Games: {len(games)}")
    for g in games[:5]:
        print(f"  - {g.game_id}: {g.title}")
    if len(games) > 5:
        print(f"  ... and {len(games) - 5} more")
    
    # Test action utilities
    print(f"\nAll Actions: {[a.name for a in get_all_actions()]}")
    print(f"Simple Actions: {[a.name for a in get_simple_actions()]}")
    print(f"Complex Actions: {[a.name for a in get_complex_actions()]}")
    
    # Test action conversion
    action = action_from_string("ACTION1")
    print(f"\naction_from_string('ACTION1'): {action}")
    print(f"action_to_string(GameAction.ACTION1): {action_to_string(GameAction.ACTION1)}")
    
    # Play a quick game if games are available
    if games:
        print(f"\n--- Playing quick game: {games[0].game_id} ---")
        env = wrapper.make(games[0].game_id)
        
        if env:
            print(f"  Environment created")
            print(f"  Available actions: {env.get_available_actions()}")
            
            # Take a few actions
            for i in range(3):
                actions = env.action_space
                if not actions:
                    break
                
                action = actions[i % len(actions)]
                
                # Handle complex actions
                data = None
                if action.is_complex():
                    # Provide default coordinates for testing
                    data = {"x": 32, "y": 32}
                    print(f"  Step {env.step_count + 1}: {action.name} (complex, coords=32,32)")
                
                try:
                    obs = env.step(action, data=data)
                    
                    if obs:
                        print(f"  Step {env.step_count}: {action.name} -> "
                              f"state={obs.state.name}, levels={obs.levels_completed}/{obs.win_levels}")
                        if obs.is_terminal:
                            print(f"    Game ended! win={obs.is_win}")
                            break
                except Exception as e:
                    print(f"  Step failed: {e}")
                    break
        else:
            print("  [WARN] Could not create environment")
    
    print("\n[OK] All tests passed!")
