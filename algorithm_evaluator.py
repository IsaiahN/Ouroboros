"""
Algorithm Evaluator

Converts algorithm representations into executable strategies that can interface
with the existing ActionHandler system. Evaluates algorithm performance during
gameplay and provides fitness calculations.
"""

import logging
import random
import json
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass

from algorithm_representations import (
    AlgorithmRepresentation, AlgorithmNode, ActionNode, ConditionalNode,
    SequenceNode, ConditionNode, RandomChoiceNode, RepeatNode
)

logger = logging.getLogger(__name__)


@dataclass
class GameContext:
    """Context information about the current game state."""
    current_score: float = 0.0
    actions_taken: int = 0
    available_actions: List[str] = None
    frame_data: Dict[str, Any] = None
    frame_changed_history: List[bool] = None
    last_action_results: List[Dict[str, Any]] = None
    coordinate_success_rate: float = 0.0
    session_id: str = ""
    game_id: str = ""

    # Enhanced coordinate tracking
    algorithm_id: str = ""
    previous_score: float = 0.0
    frame: List[List[int]] = None
    last_action6_coordinates: Optional[Tuple[int, int]] = None
    successful_coordinates: List[Tuple[int, int]] = None
    coordinate_strategy_history: List[str] = None
    action6_attempts: int = 0
    successful_action6_attempts: int = 0

    # Meta strategy support
    previous_frame: List[List[int]] = None
    frame_changes: List = None  # List of FrameChange objects
    successful_actions: List[Dict[str, Any]] = None
    last_successful_coordinates: Optional[Tuple[int, int]] = None

    def __post_init__(self):
        if self.available_actions is None:
            self.available_actions = ["ACTION1", "ACTION2", "ACTION3", "ACTION4", "ACTION5", "ACTION6", "ACTION7"]
        if self.frame_changed_history is None:
            self.frame_changed_history = []
        if self.last_action_results is None:
            self.last_action_results = []
        if self.successful_coordinates is None:
            self.successful_coordinates = []
        if self.coordinate_strategy_history is None:
            self.coordinate_strategy_history = []
        if self.frame_changes is None:
            self.frame_changes = []
        if self.successful_actions is None:
            self.successful_actions = []

    def update_frame(self, new_frame: List[List[int]]):
        """Update frame and detect changes."""
        if self.frame and new_frame:
            # Detect frame changes for meta strategies
            from meta_strategies import meta_strategy_engine
            changes = meta_strategy_engine.detect_frame_changes(self.frame, new_frame)
            self.frame_changes.extend(changes)
            
            # Keep only recent changes (last 100)
            if len(self.frame_changes) > 100:
                self.frame_changes = self.frame_changes[-100:]

        self.previous_frame = self.frame
        self.frame = new_frame

    def track_action6_usage(self, coordinates: Tuple[int, int], strategy: str = None):
        """Track ACTION6 coordinate usage."""
        self.last_action6_coordinates = coordinates
        self.action6_attempts += 1
        if strategy:
            self.coordinate_strategy_history.append(strategy)
            # Keep only last 20 strategies
            if len(self.coordinate_strategy_history) > 20:
                self.coordinate_strategy_history = self.coordinate_strategy_history[-20:]

    def track_action6_success(self, score_improvement: float):
        """Track successful ACTION6 usage."""
        if self.last_action6_coordinates and score_improvement > 0:
            self.successful_coordinates.append(self.last_action6_coordinates)
            self.successful_action6_attempts += 1
            self.last_successful_coordinates = self.last_action6_coordinates

            # Add to successful actions list for meta strategies
            self.successful_actions.append({
                'action': 'ACTION6',
                'coordinates': self.last_action6_coordinates,
                'score_improvement': score_improvement,
                'actions_taken': self.actions_taken
            })

            # Keep only last 50 successful coordinates
            if len(self.successful_coordinates) > 50:
                self.successful_coordinates = self.successful_coordinates[-50:]

            # Keep only last 20 successful actions
            if len(self.successful_actions) > 20:
                self.successful_actions = self.successful_actions[-20:]

            # Update success rate
            if self.action6_attempts > 0:
                self.coordinate_success_rate = self.successful_action6_attempts / self.action6_attempts

    def get_coordinate_statistics(self) -> Dict[str, Any]:
        """Get coordinate usage statistics for this game context."""
        return {
            'total_action6_attempts': self.action6_attempts,
            'successful_action6_attempts': self.successful_action6_attempts,
            'coordinate_success_rate': self.coordinate_success_rate,
            'unique_successful_coordinates': len(set(self.successful_coordinates)),
            'last_coordinates': self.last_action6_coordinates,
            'recent_strategies': self.coordinate_strategy_history[-5:] if self.coordinate_strategy_history else [],
            'frame_changes_count': len(self.frame_changes),
            'successful_actions_count': len(self.successful_actions)
        }


@dataclass
class EvaluationResult:
    """Result of algorithm evaluation."""
    action: str
    coordinates: Optional[Dict[str, int]] = None
    confidence: float = 1.0
    reasoning: str = ""
    execution_path: List[str] = None

    def __post_init__(self):
        if self.execution_path is None:
            self.execution_path = []


class AlgorithmEvaluator:
    """Evaluates algorithm representations and converts them to executable actions."""

    def __init__(self):
        self.evaluation_cache = {}
        self.execution_history = []

    def evaluate_algorithm(self, algorithm: AlgorithmRepresentation,
                          context: GameContext) -> EvaluationResult:
        """Evaluate an algorithm against the current game context.

        Args:
            algorithm: Algorithm representation to evaluate
            context: Current game context

        Returns:
            EvaluationResult with action and metadata
        """
        try:
            # Reset execution path
            execution_path = []

            # Evaluate the root node
            result = self._evaluate_node(algorithm.root_node, context, execution_path)

            # Validate result
            if not result or not result.action:
                logger.warning("Algorithm evaluation returned no action, using fallback")
                result = EvaluationResult(
                    action=random.choice(context.available_actions),
                    confidence=0.1,
                    reasoning="Fallback due to evaluation failure"
                )

            result.execution_path = execution_path

            # Store evaluation in history
            self.execution_history.append({
                "algorithm_id": algorithm.algorithm_id,
                "context": context,
                "result": result,
                "timestamp": self._get_timestamp()
            })

            return result

        except Exception as e:
            logger.error(f"Error evaluating algorithm {algorithm.algorithm_id}: {e}")
            return EvaluationResult(
                action=random.choice(context.available_actions),
                confidence=0.0,
                reasoning=f"Evaluation error: {str(e)}"
            )

    def _evaluate_node(self, node: AlgorithmNode, context: GameContext,
                      execution_path: List[str]) -> EvaluationResult:
        """Evaluate a single algorithm node."""
        execution_path.append(f"{node.node_type}:{node.node_id}")

        if isinstance(node, ActionNode):
            return self._evaluate_action_node(node, context)

        elif isinstance(node, ConditionalNode):
            return self._evaluate_conditional_node(node, context, execution_path)

        elif isinstance(node, SequenceNode):
            return self._evaluate_sequence_node(node, context, execution_path)

        elif isinstance(node, RandomChoiceNode):
            return self._evaluate_random_choice_node(node, context, execution_path)

        elif isinstance(node, RepeatNode):
            return self._evaluate_repeat_node(node, context, execution_path)

        else:
            logger.warning(f"Unknown node type: {node.node_type}")
            return EvaluationResult(
                action=random.choice(context.available_actions),
                confidence=0.0,
                reasoning=f"Unknown node type: {node.node_type}"
            )

    def _evaluate_action_node(self, node: ActionNode, context: GameContext) -> EvaluationResult:
        """Evaluate an action node."""
        action = node.action_type

        # Check if action is available (fix type mismatch - convert action string to int)
        action_num = int(action.replace("ACTION", ""))
        if action_num not in context.available_actions:
            # Find a similar available action
            for alt_num in context.available_actions:
                action = f"ACTION{alt_num}"
                action_num = alt_num
                break
            else:
                # If no available actions, fallback to first available
                if context.available_actions:
                    action_num = context.available_actions[0]
                    action = f"ACTION{action_num}"

        coordinates = None
        confidence = 1.0

        if action == "ACTION6":
            # CRITICAL FIX: Ensure scores are numeric before passing to coordinate generation
            current_score = getattr(context, 'current_score', 0.0)
            previous_score = getattr(context, 'previous_score', 0.0)
            
            # Type check current_score
            if isinstance(current_score, (list, tuple)):
                logger.warning(f"[EVALUATOR] Current score is list/tuple: {current_score}, taking first element")
                current_score = current_score[0] if len(current_score) > 0 else 0.0
            elif not isinstance(current_score, (int, float)):
                logger.warning(f"[EVALUATOR] Current score is not numeric: {type(current_score)} {current_score}, using 0.0")
                current_score = 0.0
            current_score = float(current_score)
            
            # Type check previous_score
            if isinstance(previous_score, (list, tuple)):
                logger.warning(f"[EVALUATOR] Previous score is list/tuple: {previous_score}, taking first element")
                previous_score = previous_score[0] if len(previous_score) > 0 else 0.0
            elif not isinstance(previous_score, (int, float)):
                logger.warning(f"[EVALUATOR] Previous score is not numeric: {type(previous_score)} {previous_score}, using 0.0")
                previous_score = 0.0
            previous_score = float(previous_score)

            # Use dynamic coordinate generation if strategy specified
            if node.coordinate_strategy:
                try:
                    from coordinate_strategies import generate_action6_coordinates, CoordinateStrategy

                    # Parse strategy
                    strategy = CoordinateStrategy(node.coordinate_strategy)

                    # Generate base coordinates using advanced strategies with safe scores
                    x, y = generate_action6_coordinates(
                        algorithm_id=getattr(context, 'algorithm_id', ''),
                        current_score=current_score,
                        previous_score=previous_score,
                        actions_taken=context.actions_taken,
                        frame=getattr(context, 'frame', None),
                        strategy=strategy
                    )

                    # Apply meta strategy to enhance coordinates
                    try:
                        from meta_strategies import meta_strategy_engine
                        meta_strategy = meta_strategy_engine.select_meta_strategy(
                            context.algorithm_id, context
                        )
                        x, y = meta_strategy_engine.apply_meta_strategy(
                            meta_strategy, (x, y), context
                        )
                        confidence = 0.9  # Higher confidence for meta-enhanced coordinates
                    except Exception as e:
                        logger.warning(f"Meta strategy application failed: {e}")
                        confidence = 0.8  # Still good confidence for strategic coordinates

                    coordinates = {"x": x, "y": y}

                except Exception as e:
                    logger.warning(f"Dynamic coordinate generation failed: {e}")
                    # Fallback to static or random
                    if node.coordinates:
                        coordinates = node.coordinates.copy()
                    else:
                        coordinates = {"x": random.randint(0, 63), "y": random.randint(0, 63)}
                    confidence = 0.5

            elif node.coordinates:
                coordinates = node.coordinates.copy()
                
                # Apply meta strategy to static coordinates too
                try:
                    from meta_strategies import meta_strategy_engine
                    meta_strategy = meta_strategy_engine.select_meta_strategy(
                        context.algorithm_id, context
                    )
                    x, y = meta_strategy_engine.apply_meta_strategy(
                        meta_strategy, (coordinates["x"], coordinates["y"]), context
                    )
                    coordinates = {"x": x, "y": y}
                    confidence = 0.7  # Medium-high confidence for meta-enhanced static coordinates
                except Exception as e:
                    logger.warning(f"Meta strategy application to static coordinates failed: {e}")
                    confidence = 0.6  # Medium confidence for static coordinates
            else:
                # Fallback to intelligent random coordinates
                try:
                    from coordinate_strategies import generate_action6_coordinates

                    # Use safe scores for fallback coordinate generation
                    x, y = generate_action6_coordinates(
                        algorithm_id=getattr(context, 'algorithm_id', ''),
                        current_score=current_score,
                        previous_score=previous_score,
                        actions_taken=context.actions_taken
                    )
                    
                    # Apply meta strategy to fallback coordinates
                    try:
                        from meta_strategies import meta_strategy_engine
                        meta_strategy = meta_strategy_engine.select_meta_strategy(
                            context.algorithm_id, context
                        )
                        x, y = meta_strategy_engine.apply_meta_strategy(
                            meta_strategy, (x, y), context
                        )
                        confidence = 0.5  # Medium confidence for meta-enhanced fallback
                    except Exception:
                        confidence = 0.4  # Lower confidence for fallback

                    coordinates = {"x": x, "y": y}

                except Exception:
                    # Final fallback to random (FIXED BOUNDS)
                    coordinates = {"x": random.randint(0, 63), "y": random.randint(0, 63)}
                    confidence = 0.3

            # Adjust confidence based on coordinate success rate
            if hasattr(context, 'coordinate_success_rate'):
                confidence = max(confidence, context.coordinate_success_rate)

            # Track ACTION6 coordinate usage in context
            if coordinates and hasattr(context, 'track_action6_usage'):
                coord_tuple = (coordinates['x'], coordinates['y'])
                strategy = node.coordinate_strategy if hasattr(node, 'coordinate_strategy') else None
                context.track_action6_usage(coord_tuple, strategy)

        return EvaluationResult(
            action=action,
            coordinates=coordinates,
            confidence=confidence,
            reasoning=f"Direct action: {action}"
        )

    def _evaluate_conditional_node(self, node: ConditionalNode, context: GameContext,
                                  execution_path: List[str]) -> EvaluationResult:
        """Evaluate a conditional node."""
        condition_result = self._evaluate_condition(node.condition, context)

        if condition_result:
            execution_path.append("true_branch")
            result = self._evaluate_node(node.true_branch, context, execution_path)
            result.reasoning = f"Condition true: {result.reasoning}"
        else:
            execution_path.append("false_branch")
            result = self._evaluate_node(node.false_branch, context, execution_path)
            result.reasoning = f"Condition false: {result.reasoning}"

        # Adjust confidence based on condition certainty
        result.confidence *= 0.9  # Slight reduction for conditional logic

        return result

    def _evaluate_condition(self, condition: ConditionNode, context: GameContext) -> bool:
        """Evaluate a condition node."""
        condition_type = condition.condition_type
        parameters = condition.parameters

        try:
            if condition_type == "score_threshold":
                threshold = parameters.get("threshold", 50)
                operator = parameters.get("operator", "greater_than")

                if operator == "greater_than":
                    return context.current_score > threshold
                elif operator == "less_than":
                    return context.current_score < threshold
                elif operator == "equal":
                    # Ensure current_score is numeric for arithmetic
                    current_score = context.current_score
                    if isinstance(current_score, (list, tuple)):
                        current_score = current_score[0] if len(current_score) > 0 else 0.0
                    elif not isinstance(current_score, (int, float)):
                        current_score = 0.0
                    return abs(float(current_score) - threshold) < 1.0

            elif condition_type == "action_count":
                count = parameters.get("count", 10)
                operator = parameters.get("operator", "greater_than")

                if operator == "greater_than":
                    return context.actions_taken > count
                elif operator == "less_than":
                    return context.actions_taken < count
                elif operator == "equal":
                    return context.actions_taken == count

            elif condition_type == "frame_changed":
                within_last = parameters.get("within_last_actions", 3)
                if len(context.frame_changed_history) < within_last:
                    return False
                return any(context.frame_changed_history[-within_last:])

            elif condition_type == "available_actions":
                required_actions = parameters.get("required_actions", [])
                return all(action in context.available_actions for action in required_actions)

            elif condition_type == "coordinate_success":
                threshold = parameters.get("success_rate_threshold", 0.5)
                return context.coordinate_success_rate >= threshold

        except Exception as e:
            logger.warning(f"Error evaluating condition {condition_type}: {e}")

        return False  # Default to false if evaluation fails

    def _evaluate_sequence_node(self, node: SequenceNode, context: GameContext,
                               execution_path: List[str]) -> EvaluationResult:
        """Evaluate a sequence node (returns first executable action)."""
        if not node.children:
            return EvaluationResult(
                action=random.choice(context.available_actions),
                confidence=0.5,
                reasoning="Empty sequence"
            )

        # For now, execute the first child
        # In a more sophisticated implementation, this could plan multiple actions
        execution_path.append("sequence_first")
        result = self._evaluate_node(node.children[0], context, execution_path)
        result.reasoning = f"Sequence start: {result.reasoning}"

        return result

    def _evaluate_random_choice_node(self, node: RandomChoiceNode, context: GameContext,
                                    execution_path: List[str]) -> EvaluationResult:
        """Evaluate a random choice node."""
        if not node.choices:
            return EvaluationResult(
                action=random.choice(context.available_actions),
                confidence=0.5,
                reasoning="Empty choice set"
            )

        # Select choice based on weights if available
        if node.weights and len(node.weights) == len(node.choices):
            choice = random.choices(node.choices, weights=node.weights)[0]
        else:
            choice = random.choice(node.choices)

        choice_index = node.choices.index(choice)
        execution_path.append(f"choice_{choice_index}")

        result = self._evaluate_node(choice, context, execution_path)
        result.reasoning = f"Random choice {choice_index}: {result.reasoning}"
        result.confidence *= 0.8  # Reduce confidence for random choices

        return result

    def _evaluate_repeat_node(self, node: RepeatNode, context: GameContext,
                             execution_path: List[str]) -> EvaluationResult:
        """Evaluate a repeat node (executes child once for now)."""
        execution_path.append(f"repeat_1_of_{node.repeat_count}")

        # For now, just execute the child once
        # In a more sophisticated implementation, this could plan multiple actions
        result = self._evaluate_node(node.child, context, execution_path)
        result.reasoning = f"Repeat 1/{node.repeat_count}: {result.reasoning}"

        return result

    def calculate_fitness(self, algorithm: AlgorithmRepresentation,
                         game_results: List[Dict[str, Any]]) -> float:
        """Calculate fitness score for an algorithm based on game results.

        Args:
            algorithm: Algorithm to evaluate
            game_results: List of game result dictionaries

        Returns:
            Fitness score (higher is better)
        """
        if not game_results:
            return 0.0

        total_score = 0.0
        total_weight = 0.0

        for result in game_results:
            # Base fitness from game score
            game_score = result.get('final_score', 0.0)
            actions_taken = result.get('actions_taken', 1)
            win_detected = result.get('win_detected', False)

            # Calculate efficiency (score per action)
            efficiency = game_score / max(1, actions_taken)

            # Base fitness
            fitness = game_score * 0.5 + efficiency * 0.3

            # Bonus for wins
            if win_detected:
                fitness += 100.0

            # Penalty for very short or very long games
            if actions_taken < 3:
                fitness *= 0.5  # Penalty for too short games
            elif actions_taken > 50:
                fitness *= 0.8  # Penalty for too long games

            # Weight recent games more heavily
            weight = 1.0
            total_score += fitness * weight
            total_weight += weight

        average_fitness = total_score / total_weight if total_weight > 0 else 0.0

        # Add diversity bonus based on algorithm complexity
        complexity_bonus = min(10.0, algorithm.get_depth() * 2.0)
        node_count_bonus = min(5.0, len(algorithm.get_all_nodes()) * 0.5)

        final_fitness = average_fitness + complexity_bonus + node_count_bonus

        return max(0.0, final_fitness)

    def get_algorithm_signature(self, algorithm: AlgorithmRepresentation) -> str:
        """Get a signature string for algorithm comparison."""
        nodes = algorithm.get_all_nodes()
        signature_parts = []

        for node in nodes:
            if isinstance(node, ActionNode):
                signature_parts.append(f"A:{node.action_type}")
            elif isinstance(node, ConditionalNode):
                signature_parts.append("C")
            elif isinstance(node, SequenceNode):
                signature_parts.append(f"S:{len(node.children)}")
            elif isinstance(node, RandomChoiceNode):
                signature_parts.append(f"R:{len(node.choices)}")
            elif isinstance(node, ConditionNode):
                signature_parts.append(f"Cond:{node.condition_type}")

        return "|".join(signature_parts)

    def analyze_execution_patterns(self, algorithm_id: str) -> Dict[str, Any]:
        """Analyze execution patterns for a specific algorithm."""
        executions = [h for h in self.execution_history if h.get("algorithm_id") == algorithm_id]

        if not executions:
            return {"message": "No execution history found"}

        # Analyze action distribution
        actions = [e["result"].action for e in executions]
        action_counts = {}
        for action in actions:
            action_counts[action] = action_counts.get(action, 0) + 1

        # Analyze confidence levels
        confidences = [e["result"].confidence for e in executions]
        avg_confidence = sum(confidences) / len(confidences)

        # Analyze execution paths
        common_paths = {}
        for execution in executions:
            path_key = " -> ".join(execution["result"].execution_path[:3])  # First 3 steps
            common_paths[path_key] = common_paths.get(path_key, 0) + 1

        return {
            "total_executions": len(executions),
            "action_distribution": action_counts,
            "average_confidence": avg_confidence,
            "common_execution_paths": dict(sorted(common_paths.items(),
                                                key=lambda x: x[1], reverse=True)[:5]),
            "unique_paths": len(set(tuple(e["result"].execution_path) for e in executions))
        }

    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def clear_history(self):
        """Clear execution history."""
        self.execution_history = []
        self.evaluation_cache = {}


class StrategyAdapter:
    """Adapts algorithm evaluator to work with existing ActionHandler interface."""

    def __init__(self, evaluator: AlgorithmEvaluator):
        self.evaluator = evaluator
        self.current_algorithm = None
        self.current_context = None

    def set_algorithm(self, algorithm: AlgorithmRepresentation):
        """Set the current algorithm to use."""
        self.current_algorithm = algorithm

    def update_context(self, game_state, action_handler):
        """Update the game context from current game state."""
        # Extract context from game state (interface with existing system)
        from arc_api_client import GameState

        if isinstance(game_state, GameState):
            self.current_context = GameContext(
                current_score=game_state.score,
                actions_taken=getattr(game_state, 'actions_taken', 0),
                available_actions=game_state.available_actions or [],
                frame_data=game_state.frame
            )
        else:
            # Fallback for other game state formats
            self.current_context = GameContext(
                current_score=getattr(game_state, 'score', 0.0),
                available_actions=getattr(game_state, 'available_actions',
                                        ["ACTION1", "ACTION2", "ACTION3", "ACTION4", "ACTION5", "ACTION6", "ACTION7"])
            )

    async def get_next_action(self) -> str:
        """Get the next action from the current algorithm."""
        if not self.current_algorithm or not self.current_context:
            return "ACTION1"  # Fallback

        result = self.evaluator.evaluate_algorithm(
            self.current_algorithm,
            self.current_context
        )

        return result.action

    async def get_next_action_with_coordinates(self) -> Tuple[str, Optional[Dict[str, int]]]:
        """Get the next action with coordinates if applicable."""
        if not self.current_algorithm or not self.current_context:
            return "ACTION1", None

        result = self.evaluator.evaluate_algorithm(
            self.current_algorithm,
            self.current_context
        )

        return result.action, result.coordinates