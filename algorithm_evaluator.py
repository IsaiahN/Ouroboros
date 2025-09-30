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

    def __post_init__(self):
        if self.available_actions is None:
            self.available_actions = ["ACTION1", "ACTION2", "ACTION3", "ACTION4", "ACTION5", "ACTION6", "ACTION7"]
        if self.frame_changed_history is None:
            self.frame_changed_history = []
        if self.last_action_results is None:
            self.last_action_results = []


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

        # Check if action is available
        if action not in context.available_actions:
            # Find a similar available action
            action_num = int(action.replace("ACTION", ""))
            for alt_num in range(1, 8):
                alt_action = f"ACTION{alt_num}"
                if alt_action in context.available_actions:
                    action = alt_action
                    break

        coordinates = None
        confidence = 1.0

        if action == "ACTION6":
            if node.coordinates:
                coordinates = node.coordinates.copy()
            else:
                # Generate random coordinates
                coordinates = {
                    "x": random.randint(0, 63),
                    "y": random.randint(0, 63)
                }

            # Adjust confidence based on coordinate success rate
            confidence = max(0.3, context.coordinate_success_rate)

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
                    return abs(context.current_score - threshold) < 1.0

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