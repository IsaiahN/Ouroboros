"""
Game Loop - Clean state machine for game execution
===================================================

This module provides the core game loop that orchestrates:
- Environment interaction via arc_api_adapter
- Action selection via decision_rung_system  
- Outcome processing via outcome_processor
- Context building via context_builder
- Learning updates via learning_systems

The game loop is a simple state machine:
    STARTING -> PLAYING -> [LEVEL_COMPLETE] -> GAME_WON/GAME_OVER -> FINISHED

Usage:
    from game_loop import GameLoop
    
    loop = GameLoop(env, decision_system, context_builder, outcome_processor, learning)
    result = await loop.run(max_actions=2000)
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import asyncio
from dataclasses import dataclass
from typing import Optional, List, Tuple, Any
from datetime import datetime
from enum import Enum, auto

from arcengine import GameAction, GameState

# Import our modules
from arc_api_adapter import GameEnvironment, Observation
from outcome_processor import OutcomeProcessor, ActionOutcome, LoopState, OutcomeTracker
from context_builder import ContextBuilder, AgentConfig, DecisionContext
from learning_systems import LearningSystems, GameResult


class LoopPhase(Enum):
    """Phases of the game loop."""
    STARTING = auto()
    PLAYING = auto()
    LEVEL_COMPLETE = auto()
    GAME_WON = auto()
    GAME_OVER = auto()
    FINISHED = auto()


@dataclass
class LoopConfig:
    """Configuration for the game loop."""
    max_actions: int = 2000
    max_no_progress_actions: int = 100  # Stop if no progress for this many actions
    detect_oscillation: bool = True
    oscillation_threshold: int = 20  # Oscillation for this many actions = break
    render_mode: Optional[str] = None
    verbose: bool = False


class GameLoop:
    """
    Manages the game loop state machine.
    
    The loop follows these phases:
    1. STARTING: Initialize environment, get first observation
    2. PLAYING: Main game loop - decide, act, process, learn
    3. LEVEL_COMPLETE: Handle level transition (may return to PLAYING)
    4. GAME_WON: Full game victory
    5. GAME_OVER: Death/failure
    6. FINISHED: Cleanup and return result
    
    Usage:
        loop = GameLoop(env, decision_system, ...)
        result = await loop.run(max_actions=2000)
    """
    
    def __init__(
        self,
        env: GameEnvironment,
        decision_system: Any,  # DecisionRungSystem or similar
        context_builder: ContextBuilder,
        outcome_processor: OutcomeProcessor,
        learning_systems: LearningSystems,
        config: Optional[LoopConfig] = None,
    ):
        """
        Initialize the game loop.
        
        Args:
            env: The game environment
            decision_system: The decision rung system for action selection
            context_builder: Builds context for decisions
            outcome_processor: Processes action outcomes
            learning_systems: Coordinates learning
            config: Optional loop configuration
        """
        self._env = env
        self._decision_system: Any = decision_system
        self._context_builder = context_builder
        self._outcome_processor = outcome_processor
        self._learning = learning_systems
        self._config = config or LoopConfig()
        
        # State tracking
        self._phase = LoopPhase.STARTING
        self._action_count = 0
        self._current_level = 0
        self._levels_completed = 0
        self._win_levels = 0
        self._score = 0.0
        self._last_observation: Optional[Observation] = None
        self._action_sequence: List[str] = []
        
        # Outcome tracking
        self._tracker = OutcomeTracker()
        
        # Timing
        self._start_time: Optional[datetime] = None
        self._end_time: Optional[datetime] = None
        
        # No-progress tracking
        self._last_progress_action = 0
    
    @property
    def game_id(self) -> str:
        """Get the current game ID."""
        return self._env.game_id
    
    @property
    def phase(self) -> LoopPhase:
        """Get the current phase."""
        return self._phase
    
    @property
    def action_count(self) -> int:
        """Get the number of actions taken."""
        return self._action_count
    
    def _log(self, msg: str) -> None:
        """Log a message if verbose mode is enabled."""
        if self._config.verbose:
            print(f"[LOOP] {msg}")
    
    async def run(
        self,
        agent_config: Optional[AgentConfig] = None,
        max_actions: Optional[int] = None,
    ) -> GameResult:
        """
        Run the complete game loop.
        
        Args:
            agent_config: Optional agent configuration
            max_actions: Override max actions from config
        
        Returns:
            GameResult with final score and sequence
        """
        if max_actions is not None:
            self._config.max_actions = max_actions
        
        agent_config = agent_config or AgentConfig(agent_id="default")
        
        self._start_time = datetime.now()
        self._log(f"Starting game: {self.game_id}")
        
        # Initialize
        self._phase = LoopPhase.STARTING
        self._context_builder.reset(self.game_id)
        self._learning.on_game_start(self.game_id, agent_config.agent_id)
        
        # Get initial observation
        obs = self._env.reset()
        if obs is None:
            # Try step with RESET action
            obs = self._env.step(GameAction.RESET)
        
        if obs is None:
            self._log("Failed to get initial observation")
            return self._create_result(agent_config, success=False)
        
        self._last_observation = obs
        self._win_levels = obs.win_levels
        self._log(f"Initial state: levels_to_win={self._win_levels}")
        
        # Main game loop
        self._phase = LoopPhase.PLAYING
        
        while not self._is_terminal():
            # Check action limit
            if self._action_count >= self._config.max_actions:
                self._log(f"Action limit reached: {self._action_count}")
                break
            
            # Check for no progress
            if self._action_count - self._last_progress_action > self._config.max_no_progress_actions:
                self._log(f"No progress for {self._config.max_no_progress_actions} actions")
                break
            
            # Check for oscillation
            if self._config.detect_oscillation and self._tracker.detect_oscillation():
                self._log("Oscillation detected")
                # Don't break immediately, but could increase exploration
            
            # Run one step
            await self._run_step(agent_config)
            
            # Handle level completion (phase may have changed in _run_step)
            if self._phase == LoopPhase.LEVEL_COMPLETE:  # type: ignore[comparison-overlap]
                self._handle_level_complete()
        
        # Game ended
        self._end_time = datetime.now()
        self._log(f"Game ended: phase={self._phase.name}, levels={self._levels_completed}/{self._win_levels}")
        
        # Create result
        result = self._create_result(agent_config)
        
        # Notify learning systems
        self._learning.on_game_end(result)
        
        return result
    
    async def _run_step(self, agent_config: AgentConfig) -> None:
        """Run a single step of the game loop."""
        # Build current state
        state = self._build_loop_state()
        
        # Build decision context
        context = self._context_builder.build(state, agent_config, self._last_observation)
        
        # Get action from decision system
        action, _reason = self._decide(state, context)
        
        # Execute action
        new_obs = self._execute(action)
        
        if new_obs is None:
            self._log(f"Action {action.name} returned None")
            return
        
        # Process outcome
        outcome = self._outcome_processor.process(state, action, new_obs)
        
        # Track outcome
        self._tracker.add(outcome)
        
        # Update context builder
        self._context_builder.update(action.name, outcome)
        
        # Update learning systems
        self._learning.update(state, action, outcome)
        
        # Update state
        self._update_state(new_obs, outcome)
        
        self._action_count += 1
        self._action_sequence.append(action.name)
    
    def _build_loop_state(self) -> LoopState:
        """Build the current loop state."""
        frame = None
        if self._last_observation:
            frame = self._last_observation.frame
        
        return LoopState(
            game_id=self.game_id,
            current_level=self._current_level,
            action_count=self._action_count,
            score=self._score,
            state=self._last_observation.state if self._last_observation else GameState.NOT_PLAYED,
            frame=frame,
            levels_completed=self._levels_completed,
            win_levels=self._win_levels,
        )
    
    def _decide(
        self,
        state: LoopState,
        context: DecisionContext,
    ) -> Tuple[GameAction, str]:
        """
        Get action decision from the decision system.
        
        Returns:
            Tuple of (action, reason)
        """
        # Get available actions
        available = self._env.action_space
        if not available:
            return GameAction.ACTION1, "no_actions_available"
        
        # Convert context to dict for rung system
        context_dict = context.to_dict()
        context_dict['available_actions'] = [a.name for a in available]
        
        # Get frame for decision system
        frame = state.frame
        
        try:
            # Call decision system
            if hasattr(self._decision_system, 'decide'):
                result = self._decision_system.decide(frame, context_dict)
                
                if isinstance(result, tuple):
                    action_name: str = str(result[0])  # type: ignore[arg-type]
                    reason: str = str(result[1])  # type: ignore[arg-type]
                else:
                    action_name = str(result)
                    reason = "decision_system"
                
                # Convert action name to GameAction
                action = self._name_to_action(action_name, available)
                return action, reason
            else:
                # Fallback: random from available
                import random
                action = random.choice(available)
                return action, "random_fallback"
                
        except Exception as e:
            self._log(f"Decision error: {e}")
            # Fallback to first available action
            return available[0], f"error_fallback: {e}"
    
    def _name_to_action(
        self,
        action_name: str,
        available: List[GameAction],
    ) -> GameAction:
        """Convert action name to GameAction, constrained to available."""
        # Try exact match
        for action in available:
            if action.name == action_name:
                return action
        
        # Try case-insensitive
        for action in available:
            if action.name.upper() == action_name.upper():
                return action
        
        # Fallback to first available
        return available[0]
    
    def _execute(self, action: GameAction) -> Optional[Observation]:
        """Execute an action and return the new observation."""
        # Handle complex actions
        data = None
        if action.is_complex():
            # Get coordinates from context or use defaults
            # In full implementation, this would come from the decision system
            data = {"x": 32, "y": 32}
        
        return self._env.step(action, data=data)
    
    def _update_state(self, obs: Observation, outcome: ActionOutcome) -> None:
        """Update internal state based on outcome."""
        self._last_observation = obs
        
        # Update levels
        if outcome.level_changed:
            self._levels_completed = obs.levels_completed
            self._current_level = obs.levels_completed
            self._last_progress_action = self._action_count
            self._log(f"Level complete! Now at level {self._current_level}")
            self._phase = LoopPhase.LEVEL_COMPLETE
        
        # Update score
        self._score = obs.score
        
        # Check terminal states
        if outcome.is_game_win:
            self._phase = LoopPhase.GAME_WON
            self._log("Game won!")
        elif outcome.is_death:
            self._phase = LoopPhase.GAME_OVER
            self._log("Game over (death)")
        
        # Progress tracking - frame change counts as progress
        if outcome.frame_changed:
            self._last_progress_action = self._action_count
    
    def _handle_level_complete(self) -> None:
        """Handle level completion transition."""
        # For now, just return to playing
        # In full implementation, might reset self-model, update exploration, etc.
        self._phase = LoopPhase.PLAYING
    
    def _is_terminal(self) -> bool:
        """Check if the game loop should terminate."""
        if self._phase in (LoopPhase.GAME_WON, LoopPhase.GAME_OVER, LoopPhase.FINISHED):
            return True
        
        if self._last_observation and self._last_observation.is_terminal:
            return True
        
        return False
    
    def _create_result(
        self,
        agent_config: AgentConfig,
        success: bool = True,
    ) -> GameResult:
        """Create the final game result."""
        duration = 0.0
        if self._start_time and self._end_time:
            duration = (self._end_time - self._start_time).total_seconds()
        elif self._start_time:
            duration = (datetime.now() - self._start_time).total_seconds()
        
        is_win = self._phase == LoopPhase.GAME_WON
        is_full_win = is_win and self._levels_completed >= self._win_levels
        
        return GameResult(
            game_id=self.game_id,
            final_score=self._score,
            levels_completed=self._levels_completed,
            win_levels=self._win_levels,
            total_actions=self._action_count,
            is_win=is_win,
            is_full_win=is_full_win,
            action_sequence=self._action_sequence.copy(),
            agent_id=agent_config.agent_id,
            duration_seconds=duration,
        )


class SyncGameLoop:
    """
    Synchronous version of the game loop.
    
    Wraps the async GameLoop for use in non-async contexts.
    """
    
    def __init__(self, *args: Any, **kwargs: Any):
        self._loop = GameLoop(*args, **kwargs)  # type: ignore[arg-type]
    
    def run(
        self,
        agent_config: Optional[AgentConfig] = None,
        max_actions: Optional[int] = None,
    ) -> GameResult:
        """Run the game loop synchronously."""
        return asyncio.run(self._loop.run(agent_config, max_actions))
    
    @property
    def game_id(self) -> str:
        return self._loop.game_id
    
    @property
    def phase(self) -> LoopPhase:
        return self._loop.phase
    
    @property
    def action_count(self) -> int:
        return self._loop.action_count


# =============================================================================
# Quick Test
# =============================================================================

if __name__ == "__main__":
    print("Game Loop - Quick Test")
    print("=" * 50)
    
    # Test requires actual environment, so just test construction
    print("\nTest 1: Module imports")
    print("  All imports successful")
    
    print("\nTest 2: LoopConfig")
    config = LoopConfig(
        max_actions=1000,
        verbose=True,
    )
    print(f"  max_actions: {config.max_actions}")
    print(f"  verbose: {config.verbose}")
    
    print("\nTest 3: LoopPhase enum")
    for phase in LoopPhase:
        print(f"  {phase.name}: {phase.value}")
    
    print("\nTest 4: GameResult creation")
    result = GameResult(
        game_id="ls20",
        final_score=0.8,
        levels_completed=4,
        win_levels=5,
        total_actions=500,
        is_win=False,
        is_full_win=False,
        action_sequence=["ACTION1", "ACTION2", "ACTION1"],
        agent_id="test-agent",
    )
    print(f"  game_id: {result.game_id}")
    print(f"  win_rate: {result.win_rate:.1%}")
    print(f"  actions: {result.total_actions}")
    
    print("\n[OK] All tests passed!")
    print("\nNote: Full loop test requires arc_api_adapter environment.")
