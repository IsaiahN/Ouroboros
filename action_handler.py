"""
Action Handler

Provides clean interfaces for sending actions to the ARC-AGI-3 API.
Handles action validation, coordinate processing, and response parsing.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
import random

try:
    from .arc_api_client import GameState
except ImportError:
    # Fallback for standalone execution
    from arc_api_client import GameState

# Import algorithm evaluator for evolved strategies
try:
    from algorithm_evaluator import AlgorithmEvaluator, StrategyAdapter, GameContext
    from algorithm_representations import AlgorithmRepresentation
    EVOLUTION_AVAILABLE = True
except ImportError:
    logger.warning("Algorithm evolution components not available")
    AlgorithmEvaluator = None
    StrategyAdapter = None
    GameContext = None
    AlgorithmRepresentation = None
    EVOLUTION_AVAILABLE = False

logger = logging.getLogger(__name__)


class ActionHandler:
    """Handles action sending and validation for ARC games."""

    def __init__(self, session_manager):
        """Initialize action handler.

        Args:
            session_manager: GameSessionManager instance
        """
        self.session_manager = session_manager
        self.last_frame = None
        self.last_score = 0.0

        # Initialize algorithm evaluation components
        if EVOLUTION_AVAILABLE:
            self.algorithm_evaluator = AlgorithmEvaluator()
            self.strategy_adapter = StrategyAdapter(self.algorithm_evaluator)
            self.current_algorithm = None
        else:
            self.algorithm_evaluator = None
            self.strategy_adapter = None
            self.current_algorithm = None

    def _validate_coordinates(self, x: int, y: int, frame: List[List[int]]) -> bool:
        """Validate that coordinates are within frame bounds.

        Args:
            x: X coordinate
            y: Y coordinate
            frame: Current game frame

        Returns:
            True if coordinates are valid
        """
        if not frame or not frame[0]:
            return False

        return 0 <= y < len(frame) and 0 <= x < len(frame[0])

    def _detect_frame_changes(self, old_frame: List[List[int]],
                            new_frame: List[List[int]]) -> Tuple[bool, int]:
        """Detect changes between two frames.

        Args:
            old_frame: Previous frame
            new_frame: Current frame

        Returns:
            Tuple of (changed, num_changes)
        """
        if not old_frame or not new_frame:
            return False, 0

        if len(old_frame) != len(new_frame):
            return True, -1  # Structural change

        changes = 0
        for y in range(len(old_frame)):
            if len(old_frame[y]) != len(new_frame[y]):
                return True, -1  # Structural change

            for x in range(len(old_frame[y])):
                if old_frame[y][x] != new_frame[y][x]:
                    changes += 1

        return changes > 0, changes

    async def send_action_1(self, reasoning: str = "Action 1") -> GameState:
        """Send ACTION1 to the game.

        Args:
            reasoning: Optional reasoning for the action

        Returns:
            New game state
        """
        return await self._send_action_with_context("ACTION1", reasoning=reasoning)

    async def send_action_2(self, reasoning: str = "Action 2") -> GameState:
        """Send ACTION2 to the game.

        Args:
            reasoning: Optional reasoning for the action

        Returns:
            New game state
        """
        return await self._send_action_with_context("ACTION2", reasoning=reasoning)

    async def send_action_3(self, reasoning: str = "Action 3") -> GameState:
        """Send ACTION3 to the game.

        Args:
            reasoning: Optional reasoning for the action

        Returns:
            New game state
        """
        return await self._send_action_with_context("ACTION3", reasoning=reasoning)

    async def send_action_4(self, reasoning: str = "Action 4") -> GameState:
        """Send ACTION4 to the game.

        Args:
            reasoning: Optional reasoning for the action

        Returns:
            New game state
        """
        return await self._send_action_with_context("ACTION4", reasoning=reasoning)

    async def send_action_5(self, reasoning: str = "Action 5") -> GameState:
        """Send ACTION5 to the game.

        Args:
            reasoning: Optional reasoning for the action

        Returns:
            New game state
        """
        return await self._send_action_with_context("ACTION5", reasoning=reasoning)

    async def send_action_6(self, x: int, y: int, frame: List[List[int]] = None) -> GameState:
        """Send ACTION6 (coordinate-based action) to the game.

        Args:
            x: X coordinate
            y: Y coordinate
            frame: Current frame for validation (optional)

        Returns:
            New game state
        """
        # Validate coordinates if frame is provided
        if frame and not self._validate_coordinates(x, y, frame):
            logger.warning(f"Invalid coordinates ({x}, {y}) for frame size {len(frame)}x{len(frame[0]) if frame else 0}")
            raise ValueError(f"Coordinates ({x}, {y}) are outside frame bounds")

        return await self._send_action_with_context("ACTION6", x=x, y=y, coordinates=[x, y])

    async def send_action_7(self, reasoning: str = "Action 7") -> GameState:
        """Send ACTION7 to the game.

        Args:
            reasoning: Optional reasoning for the action

        Returns:
            New game state
        """
        return await self._send_action_with_context("ACTION7", reasoning=reasoning)

    async def _send_action_with_context(self, action: str, **kwargs) -> GameState:
        """Send action with context tracking.

        Args:
            action: Action name
            **kwargs: Action parameters

        Returns:
            New game state with context
        """
        # Prepare context for database logging
        context = {
            'frame_before': self.last_frame,
            'score_before': self.last_score
        }
        context.update(kwargs)

        # Send action
        game_state = await self.session_manager.send_action(action, **context)

        # Detect frame changes
        if self.last_frame:
            frame_changed, num_changes = self._detect_frame_changes(self.last_frame, game_state.frame)
            context['frame_changed'] = frame_changed
            context['num_changes'] = num_changes
            logger.debug(f"Frame changes detected: {frame_changed} ({num_changes} pixels)")

        # Update tracking
        self.last_frame = game_state.frame.copy() if game_state.frame else None
        self.last_score = game_state.score

        return game_state

    def get_random_action(self, available_actions: List[str] = None,
                         exclude_actions: List[str] = None) -> str:
        """Get a random action from available actions.

        Args:
            available_actions: List of available actions
            exclude_actions: Actions to exclude from selection

        Returns:
            Random action name
        """
        if not available_actions:
            available_actions = ["ACTION1", "ACTION2", "ACTION3", "ACTION4", "ACTION5", "ACTION7"]

        if exclude_actions:
            available_actions = [a for a in available_actions if a not in exclude_actions]

        if not available_actions:
            raise ValueError("No actions available after exclusions")

        return random.choice(available_actions)

    def get_random_coordinates(self, frame: List[List[int]]) -> Tuple[int, int]:
        """Get random valid coordinates within the frame.

        Args:
            frame: Current game frame

        Returns:
            Tuple of (x, y) coordinates
        """
        if not frame or not frame[0]:
            raise ValueError("Invalid frame for coordinate generation")

        height = len(frame)
        width = len(frame[0])

        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)

        return x, y

    async def send_random_action(self, available_actions: List[str] = None,
                               exclude_actions: List[str] = None,
                               frame: List[List[int]] = None) -> GameState:
        """Send a random action.

        Args:
            available_actions: List of available actions
            exclude_actions: Actions to exclude
            frame: Current frame for ACTION6 coordinates

        Returns:
            New game state
        """
        action = self.get_random_action(available_actions, exclude_actions)

        if action == "ACTION6":
            if not frame:
                raise ValueError("Frame required for ACTION6")
            x, y = self.get_random_coordinates(frame)
            return await self.send_action_6(x, y, frame)
        else:
            method_name = f"send_{action.lower()}"
            method = getattr(self, method_name)
            return await method()

    def analyze_action_effectiveness(self, game_id: str) -> Dict[str, Any]:
        """Analyze action effectiveness for a game.

        Args:
            game_id: Game ID to analyze

        Returns:
            Action effectiveness analysis
        """
        effectiveness_data = self.session_manager.db.get_action_effectiveness(game_id)

        if not effectiveness_data:
            return {"message": "No action effectiveness data found"}

        analysis = {
            "game_id": game_id,
            "total_actions": len(effectiveness_data),
            "actions": {}
        }

        for data in effectiveness_data:
            action_num = data['action_number']
            analysis["actions"][f"ACTION{action_num}"] = {
                "attempts": data['attempts'],
                "successes": data['successes'],
                "success_rate": data['success_rate'],
                "avg_score_impact": data['avg_score_impact']
            }

        # Find best and worst actions
        if effectiveness_data:
            best_action = max(effectiveness_data, key=lambda x: x['success_rate'])
            worst_action = min(effectiveness_data, key=lambda x: x['success_rate'])

            analysis["best_action"] = f"ACTION{best_action['action_number']}"
            analysis["best_success_rate"] = best_action['success_rate']
            analysis["worst_action"] = f"ACTION{worst_action['action_number']}"
            analysis["worst_success_rate"] = worst_action['success_rate']

        return analysis

    def get_action_traces(self, game_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get action traces for analysis.

        Args:
            game_id: Optional game ID filter
            limit: Maximum number of traces to return

        Returns:
            List of action traces
        """
        return self.session_manager.db.get_action_traces(
            game_id=game_id,
            limit=limit
        )

    def get_score_progression(self, game_id: str) -> List[Dict[str, Any]]:
        """Get score progression for a game.

        Args:
            game_id: Game ID

        Returns:
            List of score progression data
        """
        return self.session_manager.db.get_score_history(game_id=game_id)

    async def smart_action_selection(self, game_state: GameState,
                                   strategy: str = "balanced") -> str:
        """Select action using basic strategy.

        Args:
            game_state: Current game state
            strategy: Selection strategy ('random', 'balanced', 'conservative')

        Returns:
            Selected action
        """
        available = game_state.available_actions or [
            "ACTION1", "ACTION2", "ACTION3", "ACTION4", "ACTION5", "ACTION6", "ACTION7"
        ]

        if strategy == "random":
            return self.get_random_action(available)

        elif strategy == "conservative":
            # Prefer actions 1-5, avoid ACTION6 unless specifically needed
            safe_actions = [a for a in available if a != "ACTION6"]
            return self.get_random_action(safe_actions if safe_actions else available)

        elif strategy == "balanced":
            # Use effectiveness data if available
            if self.session_manager.current_game_id:
                effectiveness = self.session_manager.db.get_action_effectiveness(
                    self.session_manager.current_game_id
                )

                if effectiveness:
                    # Weight actions by success rate
                    weights = {}
                    for data in effectiveness:
                        action_name = f"ACTION{data['action_number']}"
                        if action_name in available:
                            weights[action_name] = max(0.1, data['success_rate'])

                    if weights:
                        # Weighted random selection
                        actions = list(weights.keys())
                        weight_values = list(weights.values())
                        return random.choices(actions, weights=weight_values)[0]

            # Fall back to random if no effectiveness data
            return self.get_random_action(available)

        elif strategy == "evolved":
            # Use evolved algorithm for action selection
            if EVOLUTION_AVAILABLE and self.current_algorithm and self.strategy_adapter:
                try:
                    # Update strategy adapter with current game state
                    self.strategy_adapter.update_context(game_state, self)

                    # Get action from evolved algorithm
                    action = await self.strategy_adapter.get_next_action()

                    # Validate action is available
                    if action in available:
                        return action
                    else:
                        logger.warning(f"Evolved algorithm suggested unavailable action: {action}")
                        return self.get_random_action(available)

                except Exception as e:
                    logger.error(f"Error in evolved strategy: {e}")
                    return self.get_random_action(available)
            else:
                # Fall back to balanced strategy if evolution not available
                logger.warning("Evolved strategy requested but not available, using balanced")
                return await self.smart_action_selection(game_state, "balanced")

        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def set_evolved_algorithm(self, algorithm: 'AlgorithmRepresentation'):
        """Set the algorithm to use for evolved strategy.

        Args:
            algorithm: Algorithm representation to use
        """
        if EVOLUTION_AVAILABLE and self.strategy_adapter:
            self.current_algorithm = algorithm
            self.strategy_adapter.set_algorithm(algorithm)
            logger.info(f"Set evolved algorithm: {algorithm.algorithm_id}")
        else:
            logger.warning("Cannot set evolved algorithm: evolution components not available")

    def get_current_algorithm(self) -> Optional['AlgorithmRepresentation']:
        """Get the currently set algorithm.

        Returns:
            Current algorithm or None
        """
        return self.current_algorithm

    def update_algorithm_context(self, game_state: GameState):
        """Update the algorithm context with current game state.

        Args:
            game_state: Current game state
        """
        if EVOLUTION_AVAILABLE and self.strategy_adapter:
            self.strategy_adapter.update_context(game_state, self)

    def get_algorithm_performance_data(self) -> Dict[str, Any]:
        """Get performance analysis data for the current algorithm.

        Returns:
            Performance analysis dictionary
        """
        if (EVOLUTION_AVAILABLE and self.algorithm_evaluator and
            self.current_algorithm):
            return self.algorithm_evaluator.analyze_execution_patterns(
                self.current_algorithm.algorithm_id
            )
        else:
            return {"message": "No algorithm evaluation data available"}