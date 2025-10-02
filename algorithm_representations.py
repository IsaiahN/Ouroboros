"""
Algorithm Representation Structures

Defines the core data structures for representing algorithms as Abstract Syntax Trees (ASTs)
and Directed Acyclic Graphs (DAGs) that can be evolved through genetic programming operations.
"""

import json
import uuid
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
import random


@dataclass
class AlgorithmNode:
    """Base class for algorithm AST nodes."""
    node_type: str
    node_id: str = None

    def __post_init__(self):
        if self.node_id is None:
            self.node_id = str(uuid.uuid4())[:8]


@dataclass
class ActionNode(AlgorithmNode):
    """Represents a specific game action."""
    action_type: str = "ACTION1"  # Default to ACTION1, can be "ACTION1"-"ACTION7"
    coordinates: Optional[Dict[str, int]] = None  # For ACTION6 - static coordinates
    coordinate_strategy: Optional[str] = None  # For ACTION6 - dynamic coordinate strategy
    coordinate_params: Optional[Dict[str, Any]] = None  # Parameters for coordinate generation

    def __post_init__(self):
        super().__post_init__()
        self.node_type = "action"


@dataclass
class ConditionalNode(AlgorithmNode):
    """Represents a conditional branch in the algorithm."""
    condition: 'ConditionNode' = None
    true_branch: 'AlgorithmNode' = None
    false_branch: 'AlgorithmNode' = None

    def __post_init__(self):
        super().__post_init__()
        self.node_type = "conditional"


@dataclass
class SequenceNode(AlgorithmNode):
    """Represents a sequence of actions or operations."""
    children: List['AlgorithmNode'] = None

    def __post_init__(self):
        super().__post_init__()
        if self.children is None:
            self.children = []
        self.node_type = "sequence"


@dataclass
class ConditionNode(AlgorithmNode):
    """Represents various types of conditions."""
    condition_type: str = "score_threshold"
    parameters: Dict[str, Any] = None

    def __post_init__(self):
        super().__post_init__()
        if self.parameters is None:
            self.parameters = {}
        self.node_type = "condition"


@dataclass
class RandomChoiceNode(AlgorithmNode):
    """Represents random selection from multiple options."""
    choices: List['AlgorithmNode'] = None
    weights: Optional[List[float]] = None

    def __post_init__(self):
        super().__post_init__()
        if self.choices is None:
            self.choices = []
        self.node_type = "random_choice"


@dataclass
class RepeatNode(AlgorithmNode):
    """Represents repetition of actions."""
    child: 'AlgorithmNode' = None
    repeat_count: int = 1

    def __post_init__(self):
        super().__post_init__()
        self.node_type = "repeat"


class AlgorithmRepresentation:
    """Main class for representing complete algorithms."""

    def __init__(self, root_node: AlgorithmNode, algorithm_id: str = None, name: str = None):
        self.algorithm_id = algorithm_id or str(uuid.uuid4())
        self.root_node = root_node
        self.name = name or "algorithm"
        self.generation = 0
        self.parent_ids = []
        self.fitness_score = 0.0
        self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert algorithm to dictionary for serialization."""
        return {
            'algorithm_id': self.algorithm_id,
            'name': self.name,
            'root_node': self._node_to_dict(self.root_node),
            'generation': self.generation,
            'parent_ids': self.parent_ids,
            'fitness_score': self.fitness_score,
            'metadata': self.metadata
        }

    def _node_to_dict(self, node: AlgorithmNode) -> Dict[str, Any]:
        """Convert a node to dictionary representation."""
        result = {
            'node_type': node.node_type,
            'node_id': node.node_id
        }

        if isinstance(node, ActionNode):
            result['action_type'] = node.action_type
            if node.coordinates:
                result['coordinates'] = node.coordinates

        elif isinstance(node, ConditionalNode):
            result['condition'] = self._node_to_dict(node.condition)
            result['true_branch'] = self._node_to_dict(node.true_branch)
            result['false_branch'] = self._node_to_dict(node.false_branch)

        elif isinstance(node, SequenceNode):
            result['children'] = [self._node_to_dict(child) for child in node.children]

        elif isinstance(node, ConditionNode):
            result['condition_type'] = node.condition_type
            result['parameters'] = node.parameters

        elif isinstance(node, RandomChoiceNode):
            result['choices'] = [self._node_to_dict(choice) for choice in node.choices]
            if node.weights:
                result['weights'] = node.weights

        elif isinstance(node, RepeatNode):
            result['child'] = self._node_to_dict(node.child)
            result['repeat_count'] = node.repeat_count

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AlgorithmRepresentation':
        """Create algorithm from dictionary representation."""
        algorithm = cls(
            cls._dict_to_node(data['root_node']), 
            data['algorithm_id'],
            data.get('name', 'algorithm')
        )
        algorithm.generation = data.get('generation', 0)
        algorithm.parent_ids = data.get('parent_ids', [])
        algorithm.fitness_score = data.get('fitness_score', 0.0)
        algorithm.metadata = data.get('metadata', {})
        return algorithm

    @classmethod
    def _dict_to_node(cls, data: Dict[str, Any]) -> AlgorithmNode:
        """Convert dictionary to node representation."""
        node_type = data['node_type']
        node_id = data['node_id']

        if node_type == 'action':
            return ActionNode(
                node_type=node_type,
                node_id=node_id,
                action_type=data['action_type'],
                coordinates=data.get('coordinates')
            )

        elif node_type == 'conditional':
            return ConditionalNode(
                node_type=node_type,
                node_id=node_id,
                condition=cls._dict_to_node(data['condition']) if data.get('condition') else None,
                true_branch=cls._dict_to_node(data['true_branch']) if data.get('true_branch') else None,
                false_branch=cls._dict_to_node(data['false_branch']) if data.get('false_branch') else None
            )

        elif node_type == 'sequence':
            return SequenceNode(
                node_type=node_type,
                node_id=node_id,
                children=[cls._dict_to_node(child) for child in data.get('children', [])]
            )

        elif node_type == 'condition':
            return ConditionNode(
                node_type=node_type,
                node_id=node_id,
                condition_type=data['condition_type'],
                parameters=data['parameters']
            )

        elif node_type == 'random_choice':
            return RandomChoiceNode(
                node_type=node_type,
                node_id=node_id,
                choices=[cls._dict_to_node(choice) for choice in data.get('choices', [])],
                weights=data.get('weights')
            )

        elif node_type == 'repeat':
            return RepeatNode(
                node_type=node_type,
                node_id=node_id,
                child=cls._dict_to_node(data['child']) if data.get('child') else None,
                repeat_count=data['repeat_count']
            )

        else:
            raise ValueError(f"Unknown node type: {node_type}")

    def to_json(self) -> str:
        """Convert algorithm to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'AlgorithmRepresentation':
        """Create algorithm from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def get_all_nodes(self) -> List[AlgorithmNode]:
        """Get all nodes in the algorithm tree."""
        nodes = []
        self._collect_nodes(self.root_node, nodes)
        return nodes

    def _collect_nodes(self, node: AlgorithmNode, nodes: List[AlgorithmNode]):
        """Recursively collect all nodes."""
        nodes.append(node)

        if isinstance(node, ConditionalNode):
            self._collect_nodes(node.condition, nodes)
            self._collect_nodes(node.true_branch, nodes)
            self._collect_nodes(node.false_branch, nodes)

        elif isinstance(node, SequenceNode):
            for child in node.children:
                self._collect_nodes(child, nodes)

        elif isinstance(node, RandomChoiceNode):
            for choice in node.choices:
                self._collect_nodes(choice, nodes)

        elif isinstance(node, RepeatNode):
            self._collect_nodes(node.child, nodes)

    def get_depth(self) -> int:
        """Calculate the maximum depth of the algorithm tree."""
        return self._calculate_depth(self.root_node)

    def _calculate_depth(self, node: AlgorithmNode) -> int:
        """Recursively calculate tree depth."""
        if isinstance(node, ConditionalNode):
            return 1 + max(
                self._calculate_depth(node.condition),
                self._calculate_depth(node.true_branch),
                self._calculate_depth(node.false_branch)
            )

        elif isinstance(node, SequenceNode):
            if not node.children:
                return 1
            return 1 + max(self._calculate_depth(child) for child in node.children)

        elif isinstance(node, RandomChoiceNode):
            if not node.choices:
                return 1
            return 1 + max(self._calculate_depth(choice) for choice in node.choices)

        elif isinstance(node, RepeatNode):
            return 1 + self._calculate_depth(node.child)

        else:
            return 1


class AlgorithmBuilder:
    """Utility class for building common algorithm patterns."""

    @staticmethod
    def create_random_action_algorithm() -> AlgorithmRepresentation:
        """Create a simple random action algorithm."""
        actions = [f"ACTION{i}" for i in range(1, 8)]
        action_nodes = [ActionNode(node_type="action", action_type=action) for action in actions]

        random_choice = RandomChoiceNode(node_type="random_choice", choices=action_nodes)
        return AlgorithmRepresentation(random_choice)

    @staticmethod
    def create_score_based_algorithm() -> AlgorithmRepresentation:
        """Create an algorithm that changes behavior based on score."""
        import random
        
        # High score actions
        high_score_actions = [
            ActionNode(
                node_type="action", 
                action_type="ACTION6",
                coordinates={"x": random.randint(0, 63), "y": random.randint(0, 63)}
            ),
            ActionNode(node_type="action", action_type="ACTION7")
        ]
        high_score_sequence = SequenceNode(node_type="sequence", children=high_score_actions)

        # Low score actions
        low_score_actions = [
            ActionNode(node_type="action", action_type="ACTION1"),
            ActionNode(node_type="action", action_type="ACTION2"),
            ActionNode(node_type="action", action_type="ACTION3")
        ]
        low_score_choice = RandomChoiceNode(node_type="random_choice", choices=low_score_actions)

        # Condition: score > 50
        condition = ConditionNode(
            node_type="condition",
            condition_type="score_threshold",
            parameters={"threshold": 50, "operator": "greater_than"}
        )

        # Main conditional
        main_conditional = ConditionalNode(
            node_type="conditional",
            condition=condition,
            true_branch=high_score_sequence,
            false_branch=low_score_choice
        )

        return AlgorithmRepresentation(main_conditional)

    @staticmethod
    def create_adaptive_algorithm() -> AlgorithmRepresentation:
        """Create an algorithm that adapts based on multiple game state factors."""
        import random
        
        # ACTION6 with random coordinates
        action6_node = ActionNode(
            node_type="action",
            action_type="ACTION6",
            coordinates={"x": random.randint(0, 63), "y": random.randint(0, 63)}
        )

        # Safe actions
        safe_actions = [
            ActionNode(node_type="action", action_type="ACTION1"),
            ActionNode(node_type="action", action_type="ACTION2"),
            ActionNode(node_type="action", action_type="ACTION3")
        ]
        safe_choice = RandomChoiceNode(node_type="random_choice", choices=safe_actions)

        # Frame change condition
        frame_condition = ConditionNode(
            node_type="condition",
            condition_type="frame_changed",
            parameters={"within_last_actions": 3}
        )

        # Nested conditional based on frame changes
        frame_conditional = ConditionalNode(
            node_type="conditional",
            condition=frame_condition,
            true_branch=action6_node,
            false_branch=safe_choice
        )

        # Score condition
        score_condition = ConditionNode(
            node_type="condition",
            condition_type="score_threshold",
            parameters={"threshold": 30, "operator": "greater_than"}
        )

        # Main conditional
        main_conditional = ConditionalNode(
            node_type="conditional",
            condition=score_condition,
            true_branch=frame_conditional,
            false_branch=safe_choice
        )

        return AlgorithmRepresentation(main_conditional)


# Predefined condition types for algorithm construction
CONDITION_TYPES = {
    "score_threshold": {
        "parameters": ["threshold", "operator"],
        "description": "Compare current score to threshold"
    },
    "action_count": {
        "parameters": ["count", "operator"],
        "description": "Compare number of actions taken"
    },
    "frame_changed": {
        "parameters": ["within_last_actions"],
        "description": "Check if frame changed recently"
    },
    "available_actions": {
        "parameters": ["required_actions"],
        "description": "Check if specific actions are available"
    },
    "coordinate_success": {
        "parameters": ["success_rate_threshold"],
        "description": "Check coordinate action success rate"
    }
}

# Available action types
ACTION_TYPES = [
    "ACTION1", "ACTION2", "ACTION3", "ACTION4",
    "ACTION5", "ACTION6", "ACTION7"
]