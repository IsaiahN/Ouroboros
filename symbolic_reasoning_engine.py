import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
Symbolic Reasoning Engine for Complex ARC Games
================================================
Provides world modeling and goal-directed planning for games like lp85 
that require symbolic reasoning rather than pattern matching.

Core Capabilities:
1. Scene Parsing: Convert visual frame to structured object representation
2. World Model: Maintain state that updates with each action
3. Goal Evaluation: Explicitly check goal conditions
4. Action Planning: Use search/planning to find action sequences

This is the foundation for games requiring:
- Multi-object tracking
- Compositional goals ("A AND B must both be satisfied")
- Causal simulation (understanding action effects)
- State-space search

Created: 2025-12-02
Status: FULLY IMPLEMENTED
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Must be FIRST before other imports
import sys
sys.dont_write_bytecode = True

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from enum import Enum
import numpy as np
from collections import deque
from datetime import datetime
import json
import logging
import sqlite3
from pathlib import Path
import hashlib

# Database path
DB_PATH = Path(__file__).parent / "core_data.db"

logger = logging.getLogger(__name__)


class ObjectType(Enum):
    """Types of objects that can appear in ARC games."""
    AGENT = "agent"           # Controllable object
    GOAL = "goal"             # Target to reach
    OBSTACLE = "obstacle"     # Blocking object
    COLLECTIBLE = "collectible"  # Item to collect
    BUTTON = "button"         # Interactive element
    PORTAL = "portal"         # Teleportation
    MOVABLE = "movable"       # Can be pushed/pulled
    ENEMY = "enemy"           # Harmful object
    KEY = "key"               # Unlocks something
    DOOR = "door"             # Blocking until unlocked
    UNKNOWN = "unknown"       # Unclassified


@dataclass
class GameObject:
    """Represents a single object in the game world."""
    object_id: str
    object_type: ObjectType
    position: Tuple[int, int]  # (row, col)
    color: int                 # Color index
    size: int = 1              # Number of cells
    cells: List[Tuple[int, int]] = field(default_factory=list)  # All cells occupied
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def distance_to(self, other: 'GameObject') -> int:
        """Manhattan distance to another object."""
        return abs(self.position[0] - other.position[0]) + abs(self.position[1] - other.position[1])
    
    def overlaps(self, other: 'GameObject') -> bool:
        """Check if this object overlaps with another."""
        return self.position == other.position or bool(set(self.cells) & set(other.cells))
    
    def is_adjacent(self, other: 'GameObject') -> bool:
        """Check if objects are adjacent (Manhattan distance = 1)."""
        return self.distance_to(other) == 1
    
    def get_bounding_box(self) -> Tuple[int, int, int, int]:
        """Get bounding box (min_row, min_col, max_row, max_col)."""
        if not self.cells:
            return (self.position[0], self.position[1], self.position[0], self.position[1])
        rows = [c[0] for c in self.cells]
        cols = [c[1] for c in self.cells]
        return (min(rows), min(cols), max(rows), max(cols))


@dataclass
class WorldState:
    """Complete state of the game world at a point in time."""
    objects: Dict[str, GameObject]  # object_id -> GameObject
    grid: np.ndarray                # Raw grid representation
    step: int = 0
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_agent(self) -> Optional[GameObject]:
        """Get the controllable agent object."""
        for obj in self.objects.values():
            if obj.object_type == ObjectType.AGENT:
                return obj
        return None
    
    def get_agents(self) -> List[GameObject]:
        """Get all controllable agent objects (for multi-agent games)."""
        return [obj for obj in self.objects.values() if obj.object_type == ObjectType.AGENT]
    
    def get_goals(self) -> List[GameObject]:
        """Get all goal objects."""
        return [obj for obj in self.objects.values() if obj.object_type == ObjectType.GOAL]
    
    def get_obstacles(self) -> List[GameObject]:
        """Get all obstacle objects."""
        return [obj for obj in self.objects.values() if obj.object_type == ObjectType.OBSTACLE]
    
    def get_collectibles(self) -> List[GameObject]:
        """Get all collectible objects."""
        return [obj for obj in self.objects.values() if obj.object_type == ObjectType.COLLECTIBLE]
    
    def get_objects_at(self, position: Tuple[int, int]) -> List[GameObject]:
        """Get all objects at a specific position."""
        return [obj for obj in self.objects.values() if obj.position == position]
    
    def get_objects_by_type(self, obj_type: ObjectType) -> List[GameObject]:
        """Get all objects of a specific type."""
        return [obj for obj in self.objects.values() if obj.object_type == obj_type]
    
    def get_objects_by_color(self, color: int) -> List[GameObject]:
        """Get all objects of a specific color."""
        return [obj for obj in self.objects.values() if obj.color == color]
    
    def clone(self) -> 'WorldState':
        """Create a deep copy of this state."""
        cloned_objects = {}
        for k, v in self.objects.items():
            cloned_objects[k] = GameObject(
                object_id=v.object_id,
                object_type=v.object_type,
                position=v.position,
                color=v.color,
                size=v.size,
                cells=list(v.cells),
                properties=dict(v.properties)
            )
        return WorldState(
            objects=cloned_objects,
            grid=self.grid.copy(),
            step=self.step,
            score=self.score,
            metadata=dict(self.metadata)
        )
    
    def get_state_hash(self) -> str:
        """Get a hash of the current state for deduplication."""
        # Hash based on object positions
        positions = sorted([
            (obj.object_id, obj.position, obj.object_type.value)
            for obj in self.objects.values()
        ])
        return hashlib.md5(str(positions).encode()).hexdigest()[:16]
    
    def is_valid_position(self, pos: Tuple[int, int]) -> bool:
        """Check if position is within grid bounds."""
        return 0 <= pos[0] < self.grid.shape[0] and 0 <= pos[1] < self.grid.shape[1]


@dataclass
class Goal:
    """Represents a goal condition that must be satisfied."""
    goal_type: str
    target_objects: List[str]  # Object IDs involved
    condition: str             # e.g., "reach", "collect", "avoid", "push_to"
    target_position: Optional[Tuple[int, int]] = None  # For position-based goals
    satisfied: bool = False
    priority: int = 1          # Higher = more important
    
    def __hash__(self):
        return hash((self.goal_type, tuple(self.target_objects), self.condition))


@dataclass
class CompositionalGoal:
    """
    Compositional goal with AND/OR logic.
    For lp85-type games where multiple conditions must be satisfied.
    """
    subgoals: List[Goal]
    logic: str = "AND"  # "AND" or "OR"
    
    def is_satisfied(self) -> bool:
        if self.logic == "AND":
            return all(g.satisfied for g in self.subgoals)
        else:  # OR
            return any(g.satisfied for g in self.subgoals)
    
    def get_progress(self) -> float:
        """Return progress as fraction of satisfied subgoals."""
        if not self.subgoals:
            return 1.0
        return sum(1 for g in self.subgoals if g.satisfied) / len(self.subgoals)
    
    def get_unsatisfied(self) -> List[Goal]:
        """Return list of unsatisfied subgoals."""
        return [g for g in self.subgoals if not g.satisfied]


class ActionEffect:
    """Represents the effect of an action on the world state."""
    
    def __init__(self, action_id: int, name: str, delta: Tuple[int, int],
                 precondition: Optional[Callable[['WorldState', GameObject], bool]] = None,
                 effect: Optional[Callable[['WorldState', GameObject], 'WorldState']] = None):
        self.action_id = action_id
        self.name = name
        self.delta = delta  # Movement delta (row, col)
        self.precondition = precondition
        self.effect = effect
    
    def can_apply(self, state: WorldState, agent: GameObject) -> bool:
        """Check if action can be applied."""
        if self.precondition:
            return self.precondition(state, agent)
        return True
    
    def apply(self, state: WorldState, agent: GameObject) -> WorldState:
        """Apply the action effect to get new state."""
        if self.effect:
            return self.effect(state, agent)
        # Default: just move agent by delta
        new_state = state.clone()
        new_agent = new_state.objects.get(agent.object_id)
        if new_agent:
            new_row = new_agent.position[0] + self.delta[0]
            new_col = new_agent.position[1] + self.delta[1]
            if new_state.is_valid_position((new_row, new_col)):
                new_agent.position = (new_row, new_col)
        new_state.step += 1
        return new_state


class SceneParser(ABC):
    """Abstract base for parsing visual frames into structured representations."""
    
    @abstractmethod
    def parse(self, frame: np.ndarray) -> WorldState:
        """Convert raw frame to WorldState with identified objects."""
        pass
    
    @abstractmethod
    def identify_object_type(self, cells: List[Tuple[int, int]], color: int, 
                             context: Optional[Dict] = None) -> ObjectType:
        """Determine the type of an object based on visual features."""
        pass


class ConnectedComponentParser(SceneParser):
    """
    Scene parser using connected component analysis.
    
    Uses proper flood-fill to identify distinct objects.
    More robust than simple color grouping.
    """
    
    def __init__(self, color_mappings: Optional[Dict[int, ObjectType]] = None,
                 min_object_size: int = 1, background_colors: Optional[Set[int]] = None):
        # Default color mappings (can be learned/customized per game)
        self.color_mappings = color_mappings or {}
        self.min_object_size = min_object_size
        self.background_colors = background_colors or {0}
        self.learned_agent_colors: Set[int] = set()
    
    def parse(self, frame: np.ndarray) -> WorldState:
        """Parse frame into WorldState using connected components."""
        if isinstance(frame, list):
            frame = np.array(frame, dtype=int)
        
        objects = {}
        visited = np.zeros_like(frame, dtype=bool)
        object_counter = 0
        
        for row in range(frame.shape[0]):
            for col in range(frame.shape[1]):
                if visited[row, col]:
                    continue
                
                color = int(frame[row, col])
                if color in self.background_colors:
                    visited[row, col] = True
                    continue
                
                # Flood fill to get connected component
                cells = self._flood_fill(frame, row, col, color, visited)
                
                if len(cells) < self.min_object_size:
                    continue
                
                # Calculate centroid
                rows = [c[0] for c in cells]
                cols = [c[1] for c in cells]
                centroid = (int(np.mean(rows)), int(np.mean(cols)))
                
                obj_type = self.identify_object_type(cells, color)
                obj_id = f"obj_{object_counter}"
                
                objects[obj_id] = GameObject(
                    object_id=obj_id,
                    object_type=obj_type,
                    position=centroid,
                    color=color,
                    size=len(cells),
                    cells=cells
                )
                object_counter += 1
        
        return WorldState(objects=objects, grid=frame)
    
    def _flood_fill(self, grid: np.ndarray, start_row: int, start_col: int,
                    target_color: int, visited: np.ndarray) -> List[Tuple[int, int]]:
        """Flood fill to find connected component."""
        cells = []
        stack = [(start_row, start_col)]
        
        while stack:
            row, col = stack.pop()
            
            if row < 0 or row >= grid.shape[0] or col < 0 or col >= grid.shape[1]:
                continue
            if visited[row, col]:
                continue
            if grid[row, col] != target_color:
                continue
            
            visited[row, col] = True
            cells.append((row, col))
            
            # 4-connected neighbors
            stack.extend([
                (row - 1, col), (row + 1, col),
                (row, col - 1), (row, col + 1)
            ])
        
        return cells
    
    def identify_object_type(self, cells: List[Tuple[int, int]], color: int,
                             context: Optional[Dict] = None) -> ObjectType:
        """Identify object type from color, size, and position."""
        # Use color mapping if available
        if color in self.color_mappings:
            return self.color_mappings[color]
        
        # Check if this is a learned agent color
        if color in self.learned_agent_colors:
            return ObjectType.AGENT
        
        # Heuristics based on size
        size = len(cells)
        if size == 1:
            return ObjectType.AGENT  # Single cell often controllable
        elif size <= 4:
            return ObjectType.COLLECTIBLE
        elif size > 20:
            return ObjectType.OBSTACLE  # Large objects often walls
        else:
            return ObjectType.UNKNOWN
    
    def learn_agent_color(self, color: int):
        """Mark a color as the agent color (learned from action correlation)."""
        self.learned_agent_colors.add(color)
        self.color_mappings[color] = ObjectType.AGENT


class SimpleSceneParser(ConnectedComponentParser):
    """
    Alias for backward compatibility.
    Uses ConnectedComponentParser with default settings.
    """
    
    def __init__(self, color_mappings: Optional[Dict[int, ObjectType]] = None):
        super().__init__(color_mappings=color_mappings)


class AgentIdentifier:
    """
    Identifies which object the player controls by correlating actions with movements.
    
    The key insight: "When I press UP, which object moves up?"
    """
    
    def __init__(self, parser: SceneParser):
        self.parser = parser
        self.action_history: List[Tuple[int, np.ndarray, np.ndarray]] = []  # (action, before, after)
        self.movement_correlations: Dict[str, Dict[int, int]] = {}  # obj_id -> {action: count}
        self.identified_agent: Optional[str] = None
        self.confidence: float = 0.0
    
    def record_action(self, action: int, frame_before: np.ndarray, frame_after: np.ndarray):
        """Record an action and its effect on frames."""
        self.action_history.append((action, frame_before, frame_after))
        
        # Parse both frames
        state_before = self.parser.parse(frame_before)
        state_after = self.parser.parse(frame_after)
        
        # Find objects that moved in expected direction
        expected_delta = self._get_expected_delta(action)
        
        for obj_id, obj_before in state_before.objects.items():
            # Find matching object in after state
            obj_after = self._find_matching_object(obj_before, state_after)
            
            if obj_after:
                actual_delta = (
                    obj_after.position[0] - obj_before.position[0],
                    obj_after.position[1] - obj_before.position[1]
                )
                
                if actual_delta == expected_delta:
                    if obj_id not in self.movement_correlations:
                        self.movement_correlations[obj_id] = {}
                    if action not in self.movement_correlations[obj_id]:
                        self.movement_correlations[obj_id][action] = 0
                    self.movement_correlations[obj_id][action] += 1
        
        # Update agent identification
        self._update_agent_identification()
    
    def _get_expected_delta(self, action: int) -> Tuple[int, int]:
        """Get expected movement delta for an action."""
        deltas = {
            1: (-1, 0),  # UP
            2: (1, 0),   # DOWN
            3: (0, -1),  # LEFT
            4: (0, 1),   # RIGHT
            5: (0, 0),   # STAY/INTERACT
            6: (0, 0),   # SPECIAL
            7: (0, 0),   # SPECIAL
        }
        return deltas.get(action, (0, 0))
    
    def _find_matching_object(self, obj: GameObject, state: WorldState) -> Optional[GameObject]:
        """Find the matching object in another state (by color and proximity)."""
        best_match = None
        best_distance = float('inf')
        
        for candidate in state.objects.values():
            if candidate.color != obj.color:
                continue
            
            distance = abs(candidate.position[0] - obj.position[0]) + \
                       abs(candidate.position[1] - obj.position[1])
            
            if distance < best_distance and distance <= 3:  # Max movement threshold
                best_distance = distance
                best_match = candidate
        
        return best_match
    
    def _update_agent_identification(self):
        """Update agent identification based on correlations."""
        if not self.movement_correlations:
            return
        
        # Find object that responds to most action types
        best_obj = None
        best_score = 0
        
        for obj_id, action_counts in self.movement_correlations.items():
            # Score = number of different actions this object responds to
            score = len(action_counts)
            total_responses = sum(action_counts.values())
            
            if score > best_score or (score == best_score and total_responses > best_score):
                best_score = score
                best_obj = obj_id
        
        if best_obj and best_score >= 2:  # At least 2 different action types
            self.identified_agent = best_obj
            self.confidence = min(1.0, best_score / 4)  # Up to 4 movement actions
    
    def get_agent_id(self) -> Optional[str]:
        """Get identified agent object ID."""
        return self.identified_agent if self.confidence > 0.5 else None
    
    def get_agent_color(self, state: WorldState) -> Optional[int]:
        """Get the color of the identified agent."""
        if self.identified_agent and self.identified_agent in state.objects:
            return state.objects[self.identified_agent].color
        return None


@dataclass
class BeliefNode:
    """A single belief about the world that can be tested and decay."""
    belief_id: str
    belief_type: str  # 'physics', 'trigger', 'control', 'object_type'
    content: Dict[str, Any]
    confidence: float = 0.5
    last_tested_step: int = 0
    test_count: int = 0
    success_count: int = 0
    created_step: int = 0


@dataclass
class Prediction:
    """A prediction made before an action, to be compared after."""
    action: int
    expected_agent_position: Optional[Tuple[int, int]] = None
    expected_score_change: int = 0
    expected_object_changes: Dict[str, Any] = field(default_factory=dict)
    expected_collisions: List[str] = field(default_factory=list)
    timestamp: float = 0.0


class WorldModel:
    """
    Maintains and updates world state based on actions.
    
    The key insight: Instead of just seeing pixels, we simulate
    what happens when actions are taken, building a mental model.
    
    Enhanced with Active Belief Graph (from agent_consciousness_synthesis.md):
    - Predictions before actions (mandatory)
    - Surprise scoring after actions
    - Competing beliefs that can be wrong
    - Belief decay for unused rules
    """
    
    def __init__(self, initial_state: WorldState, agent_id: Optional[str] = None):
        self.state = initial_state
        self.history: List[WorldState] = [initial_state.clone()]
        self.agent_id = agent_id or self._auto_detect_agent()
        
        # Action effects (can be customized per game)
        self.action_effects: Dict[int, ActionEffect] = {
            1: ActionEffect(1, "UP", (-1, 0)),
            2: ActionEffect(2, "DOWN", (1, 0)),
            3: ActionEffect(3, "LEFT", (0, -1)),
            4: ActionEffect(4, "RIGHT", (0, 1)),
            5: ActionEffect(5, "STAY", (0, 0)),
            6: ActionEffect(6, "SPECIAL_A", (0, 0)),
            7: ActionEffect(7, "SPECIAL_B", (0, 0)),
        }
        
        # Collision rules
        self.collision_types: Set[ObjectType] = {ObjectType.OBSTACLE}
        self.collectible_types: Set[ObjectType] = {ObjectType.COLLECTIBLE, ObjectType.KEY}
        self.interactive_types: Set[ObjectType] = {ObjectType.BUTTON, ObjectType.PORTAL, ObjectType.DOOR}
        
        # =====================================================================
        # ACTIVE BELIEF GRAPH (from agent_consciousness_synthesis.md)
        # =====================================================================
        self.beliefs: Dict[str, BeliefNode] = {}
        self.last_prediction: Optional[Prediction] = None
        self.prediction_history: List[Dict[str, Any]] = []
        self.surprise_history: List[float] = []
        self.total_predictions: int = 0
        self.correct_predictions: int = 0
        
        # Object type classifications (fed from self-model)
        self.object_type_beliefs: Dict[str, ObjectType] = {}  # object_id -> type
        
        # Physics rules (fed from self-model collision effects)
        self.physics_rules: List[Dict[str, Any]] = []
        
        # Trigger rules (fed from self-model interaction triggers)
        self.trigger_rules: List[Dict[str, Any]] = []
        
        # Concepts from CODS discoveries
        self.concepts: Dict[str, Dict[str, Any]] = {}
    
    def _auto_detect_agent(self) -> Optional[str]:
        """Auto-detect agent from initial state."""
        agent = self.state.get_agent()
        return agent.object_id if agent else None
    
    def apply_action(self, action: int) -> WorldState:
        """
        Apply action to current state and return new state.
        
        This is where causal simulation happens:
        - Predict movement effects
        - Update object positions
        - Check for interactions (collisions, pickups, etc.)
        """
        new_state = self.state.clone()
        new_state.step += 1
        
        agent = new_state.objects.get(self.agent_id) if self.agent_id else new_state.get_agent()
        if not agent:
            return new_state
        
        # Get action effect
        effect = self.action_effects.get(action)
        if not effect:
            return new_state
        
        # Calculate new position
        new_row = agent.position[0] + effect.delta[0]
        new_col = agent.position[1] + effect.delta[1]
        
        # Check bounds
        if not new_state.is_valid_position((new_row, new_col)):
            # Hit boundary, stay in place
            self.state = new_state
            self.history.append(new_state.clone())
            return new_state
        
        # Check for obstacles
        if not self._is_blocked(new_state, (new_row, new_col)):
            # Update agent cells
            if agent.cells:
                delta = (new_row - agent.position[0], new_col - agent.position[1])
                agent.cells = [(c[0] + delta[0], c[1] + delta[1]) for c in agent.cells]
            agent.position = (new_row, new_col)
        
        # Handle interactions at new position
        self._handle_interactions(new_state, agent)
        
        # Update grid based on new object positions
        self._update_grid(new_state)
        
        # Update state
        self.state = new_state
        self.history.append(new_state.clone())
        
        return new_state
    
    def _is_blocked(self, state: WorldState, position: Tuple[int, int]) -> bool:
        """Check if position is blocked by obstacle."""
        for obj in state.objects.values():
            if obj.object_type in self.collision_types:
                if obj.position == position or position in obj.cells:
                    return True
        return False
    
    def _handle_interactions(self, state: WorldState, agent: GameObject):
        """Handle interactions between agent and other objects."""
        to_remove = []
        
        for obj_id, obj in state.objects.items():
            if obj.object_id == agent.object_id:
                continue
            
            # Check for overlap
            if agent.position == obj.position or agent.overlaps(obj):
                if obj.object_type in self.collectible_types:
                    to_remove.append(obj_id)
                    state.score += 1
                elif obj.object_type == ObjectType.BUTTON:
                    obj.properties['activated'] = True
                elif obj.object_type == ObjectType.PORTAL:
                    # Teleport to linked portal
                    linked = obj.properties.get('linked_portal')
                    if linked and linked in state.objects:
                        agent.position = state.objects[linked].position
                elif obj.object_type == ObjectType.GOAL:
                    obj.properties['reached'] = True
        
        for obj_id in to_remove:
            del state.objects[obj_id]
    
    def _update_grid(self, state: WorldState):
        """Update grid to reflect current object positions."""
        # Clear grid (keep obstacles)
        for row in range(state.grid.shape[0]):
            for col in range(state.grid.shape[1]):
                # Only clear non-obstacle cells
                if state.grid[row, col] != 0:
                    is_obstacle = False
                    for obj in state.objects.values():
                        if obj.object_type == ObjectType.OBSTACLE and (row, col) in obj.cells:
                            is_obstacle = True
                            break
                    if not is_obstacle:
                        state.grid[row, col] = 0
        
        # Redraw objects
        for obj in state.objects.values():
            for cell in obj.cells if obj.cells else [obj.position]:
                if state.is_valid_position(cell):
                    state.grid[cell[0], cell[1]] = obj.color
    
    def predict_state(self, actions: List[int]) -> WorldState:
        """Predict state after a sequence of actions (lookahead)."""
        temp_model = WorldModel(self.state.clone(), self.agent_id)
        for action in actions:
            temp_model.apply_action(action)
        return temp_model.state
    
    def get_reachable_positions(self, max_steps: int = 10) -> Set[Tuple[int, int]]:
        """Get all positions reachable within max_steps."""
        agent = self.state.get_agent()
        initial_pos = agent.position if agent else (0, 0)
        reachable: Set[Tuple[int, int]] = {initial_pos}
        frontier = list(reachable)
        
        for _ in range(max_steps):
            new_frontier = []
            for pos in frontier:
                for action in [1, 2, 3, 4]:  # Movement actions
                    delta = self.action_effects[action].delta
                    new_pos = (pos[0] + delta[0], pos[1] + delta[1])
                    if new_pos not in reachable and self.state.is_valid_position(new_pos):
                        if not self._is_blocked(self.state, new_pos):
                            reachable.add(new_pos)
                            new_frontier.append(new_pos)
            frontier = new_frontier
            if not frontier:
                break
        
        return reachable

    # =========================================================================
    # ACTIVE BELIEF GRAPH METHODS (from agent_consciousness_synthesis.md)
    # These enable the WorldModel to PREDICT and BE WRONG - the learning signal
    # =========================================================================
    
    def predict_before_action(self, action: int) -> Prediction:
        """
        MUST be called BEFORE action execution.
        
        Creates a prediction about what will happen, so we can
        measure surprise afterward. This is mandatory for learning.
        """
        import time
        
        agent = self.state.get_agent()
        prediction = Prediction(
            action=action,
            timestamp=time.time()
        )
        
        if agent:
            # Predict agent movement based on action effects
            effect = self.action_effects.get(action)
            if effect:
                new_row = agent.position[0] + effect.delta[0]
                new_col = agent.position[1] + effect.delta[1]
                
                # Check if movement would be blocked
                if self.state.is_valid_position((new_row, new_col)):
                    if not self._is_blocked(self.state, (new_row, new_col)):
                        prediction.expected_agent_position = (new_row, new_col)
                    else:
                        prediction.expected_agent_position = agent.position
                        prediction.expected_collisions.append('obstacle')
                else:
                    prediction.expected_agent_position = agent.position
                    prediction.expected_collisions.append('boundary')
            else:
                prediction.expected_agent_position = agent.position
            
            # Predict collectible pickups
            for obj_id, obj in self.state.objects.items():
                if obj.object_type in self.collectible_types:
                    if prediction.expected_agent_position == obj.position:
                        prediction.expected_score_change += 1
                        prediction.expected_object_changes[obj_id] = 'collected'
        
        self.last_prediction = prediction
        self.total_predictions += 1
        return prediction
    
    def observe_after_action(self, action: int, frame_before: Any, frame_after: Any) -> Dict[str, Any]:
        """
        MUST be called AFTER action execution.
        
        Compares prediction to reality and computes surprise.
        This is where the model learns by being wrong.
        """
        if self.last_prediction is None:
            return {'surprise': 0.0, 'prediction_made': False}
        
        prediction = self.last_prediction
        surprise = 0.0
        diffs = []
        
        # Get actual agent position from current state
        agent = self.state.get_agent()
        actual_position = agent.position if agent else None
        
        # Compare predicted vs actual position
        if prediction.expected_agent_position and actual_position:
            if prediction.expected_agent_position != actual_position:
                surprise += 0.5
                diffs.append({
                    'type': 'position',
                    'expected': prediction.expected_agent_position,
                    'actual': actual_position
                })
                # Spawn competing belief - our physics model was wrong
                self._spawn_competing_belief(action, 'position_mismatch', {
                    'expected': prediction.expected_agent_position,
                    'actual': actual_position
                })
        
        # Compare predicted vs actual score change
        actual_score = self.state.score
        previous_score = self.history[-2].score if len(self.history) >= 2 else 0
        actual_score_change = actual_score - previous_score
        
        if prediction.expected_score_change != actual_score_change:
            surprise += 0.3
            diffs.append({
                'type': 'score',
                'expected': prediction.expected_score_change,
                'actual': actual_score_change
            })
        
        # Check for unexpected object changes
        if frame_before is not None and frame_after is not None:
            try:
                before_arr = np.array(frame_before) if not isinstance(frame_before, np.ndarray) else frame_before
                after_arr = np.array(frame_after) if not isinstance(frame_after, np.ndarray) else frame_after
                if before_arr.shape == after_arr.shape:
                    changed_pixels = np.sum(before_arr != after_arr)
                    total_pixels = before_arr.size
                    change_ratio = changed_pixels / max(total_pixels, 1)
                    
                    # High change with low expectation = surprise
                    if change_ratio > 0.1 and not prediction.expected_object_changes:
                        surprise += 0.2 * change_ratio
                        diffs.append({
                            'type': 'unexpected_changes',
                            'change_ratio': change_ratio
                        })
            except Exception:
                pass
        
        # =============================================================================
        # PHYSICS RULE VIOLATION CHECK (Phase 5: Physics -> Surprise)
        # Compare outcome against learned physics rules
        # =============================================================================
        physics_violation = None
        if prediction.expected_agent_position and actual_position:
            # Check if physics rules were violated
            physics_violation = self.check_physics_violation(
                predicted_position=prediction.expected_agent_position,
                actual_position=actual_position,
                action=action
            )
            
            if physics_violation.get('violated'):
                # Add physics violation surprise
                surprise += physics_violation['surprise_amount']
                diffs.append({
                    'type': 'physics_violation',
                    'violation_type': physics_violation['violation_type'],
                    'learn_from': physics_violation['learn_from']
                })
                
                # Trigger learning from the violation
                if physics_violation.get('learn_from'):
                    learn_data = physics_violation['learn_from']
                    if learn_data['type'] == 'weaken_rule':
                        # Reduce confidence in the rule that was wrong
                        rule = learn_data.get('rule')
                        if rule and 'confidence' in rule:
                            rule['confidence'] = max(0.1, rule['confidence'] * 0.7)
                    elif learn_data['type'] == 'new_collision_rule':
                        # Learn new blocking rule
                        self.add_physics_rule({
                            'type': 'collision',
                            'object_a': 'agent',
                            'object_b': 'unknown',
                            'position': learn_data['position'],
                            'effect': 'blocked',
                            'confidence': 0.5
                        })
        
        # Normalize surprise to 0-1
        surprise = min(surprise, 1.0)
        
        # Track prediction accuracy
        if surprise < 0.2:
            self.correct_predictions += 1
        
        # Store in history
        result = {
            'surprise': surprise,
            'prediction_made': True,
            'diffs': diffs,
            'prediction_accuracy': self.correct_predictions / max(self.total_predictions, 1),
            'physics_violated': physics_violation.get('violated', False) if physics_violation else False
        }
        self.prediction_history.append(result)
        self.surprise_history.append(surprise)
        
        # Keep history bounded
        if len(self.prediction_history) > 1000:
            self.prediction_history = self.prediction_history[-500:]
        if len(self.surprise_history) > 1000:
            self.surprise_history = self.surprise_history[-500:]
        
        return result
    
    def compute_surprise(self, prediction: Prediction, current_frame: Any) -> float:
        """Compute surprise score between prediction and current reality."""
        if not self.surprise_history:
            return 0.0
        return self.surprise_history[-1] if self.surprise_history else 0.0
    
    def decay_unused_beliefs(self, current_step: int, decay_threshold: int = 50) -> int:
        """
        Beliefs that aren't tested decay over time.
        
        This prevents stale knowledge from persisting.
        Returns number of beliefs decayed.
        """
        decayed = 0
        to_remove = []
        
        for belief_id, belief in self.beliefs.items():
            steps_since_test = current_step - belief.last_tested_step
            if steps_since_test > decay_threshold:
                # Apply confidence decay
                decay_factor = 0.95 ** (steps_since_test / decay_threshold)
                old_confidence = belief.confidence
                belief.confidence *= decay_factor
                
                if belief.confidence < 0.1:
                    to_remove.append(belief_id)
                elif belief.confidence < old_confidence:
                    decayed += 1
        
        for belief_id in to_remove:
            del self.beliefs[belief_id]
        
        return decayed
    
    def _spawn_competing_belief(self, action: int, mismatch_type: str, evidence: Dict[str, Any]) -> None:
        """
        When prediction fails, create a competing explanation.
        
        TWO BELIEFS NOW COMPETE - the model must choose.
        """
        belief_id = f"belief_{mismatch_type}_{len(self.beliefs)}"
        
        # Create alternative hypothesis
        new_belief = BeliefNode(
            belief_id=belief_id,
            belief_type='physics_correction',
            content={
                'trigger_action': action,
                'mismatch_type': mismatch_type,
                'evidence': evidence,
                'hypothesis': f"Action {action} does not work as expected"
            },
            confidence=0.3,  # Start with low confidence
            created_step=self.state.step
        )
        
        self.beliefs[belief_id] = new_belief
        
        # Limit total beliefs to prevent explosion
        if len(self.beliefs) > 100:
            # Remove lowest confidence beliefs
            sorted_beliefs = sorted(self.beliefs.items(), key=lambda x: x[1].confidence)
            for belief_id, _ in sorted_beliefs[:20]:
                del self.beliefs[belief_id]
    
    # =========================================================================
    # SELF-MODEL INTEGRATION METHODS (from agent_consciousness_synthesis.md)
    # Feed discoveries from agent_self_model into world understanding
    # =========================================================================
    
    def set_object_type(self, object_id: str, object_type: str) -> None:
        """
        Tell world model what type an object is.
        
        Called by self-model when it discovers:
        - "I control this object" -> set as AGENT
        - "This object moves autonomously" -> set as ENEMY/NPC
        """
        try:
            obj_type = ObjectType(object_type.lower())
        except ValueError:
            obj_type = ObjectType.UNKNOWN
        
        self.object_type_beliefs[object_id] = obj_type
        
        # Update actual object if it exists in state
        if object_id in self.state.objects:
            self.state.objects[object_id].object_type = obj_type
    
    def add_physics_rule(self, rule: Dict[str, Any]) -> None:
        """
        Add a physics rule discovered by self-model collision effects.
        
        Example: {'type': 'collision', 'object_a': 'player', 'object_b': 'wall', 'effect': 'blocked'}
        """
        # Avoid duplicates
        for existing in self.physics_rules:
            if existing.get('type') == rule.get('type') and \
               existing.get('object_a') == rule.get('object_a') and \
               existing.get('object_b') == rule.get('object_b'):
                return
        
        self.physics_rules.append(rule)
    
    def apply_physics_rules(self, action: int, current_position: Tuple[int, int], target_position: Tuple[int, int]) -> Dict[str, Any]:
        """
        Apply learned physics rules to predict outcome of movement.
        
        This is where the agent's learned knowledge is USED to inform predictions.
        Returns dict with predictions based on learned physics.
        
        Args:
            action: The action being considered
            current_position: Agent's current position
            target_position: Where agent would move without physics
            
        Returns:
            Dict with physics predictions:
            - 'blocked': bool if movement should be blocked
            - 'expected_effect': what should happen
            - 'confidence': how certain we are
            - 'rule_used': which physics rule applies
        """
        result = {
            'blocked': False,
            'expected_effect': 'move',
            'confidence': 0.0,  # 0 means no physics rule applies
            'rule_used': None
        }
        
        # Check each learned physics rule
        for rule in self.physics_rules:
            rule_type = rule.get('type', '')
            
            if rule_type == 'collision':
                # Check if target position contains the collision object
                object_b_type = rule.get('object_b', '').lower()
                effect = rule.get('effect', '')
                
                # Look for objects of this type at target position
                for obj_id, obj in self.state.objects.items():
                    obj_type_str = str(obj.object_type.value) if hasattr(obj.object_type, 'value') else str(obj.object_type)
                    if obj_type_str.lower() == object_b_type or object_b_type in obj_type_str.lower():
                        if target_position in (obj.cells if obj.cells else [obj.position]):
                            if effect == 'blocked':
                                result['blocked'] = True
                                result['expected_effect'] = 'blocked'
                                result['confidence'] = rule.get('confidence', 0.8)
                                result['rule_used'] = rule
                                return result
                            elif effect == 'push':
                                result['expected_effect'] = 'push'
                                result['confidence'] = rule.get('confidence', 0.8)
                                result['rule_used'] = rule
            
            elif rule_type == 'boundary':
                # Learned that boundaries block
                if not self.state.is_valid_position(target_position):
                    result['blocked'] = True
                    result['expected_effect'] = 'blocked_boundary'
                    result['confidence'] = rule.get('confidence', 1.0)
                    result['rule_used'] = rule
                    return result
            
            elif rule_type == 'teleport':
                # Learned about teleportation
                trigger_pos = rule.get('trigger_position')
                dest_pos = rule.get('destination')
                if target_position == trigger_pos and dest_pos:
                    result['expected_effect'] = 'teleport'
                    result['teleport_destination'] = dest_pos
                    result['confidence'] = rule.get('confidence', 0.7)
                    result['rule_used'] = rule
        
        return result
    
    def check_physics_violation(self, predicted_position: Tuple[int, int], actual_position: Tuple[int, int], 
                                 action: int) -> Dict[str, Any]:
        """
        Check if the actual outcome violates our learned physics rules.
        
        This is the SURPRISE detector - when reality differs from what 
        our physics understanding predicted.
        
        Returns:
            Dict with violation info:
            - 'violated': bool - did physics rules fail
            - 'surprise_amount': float 0-1 
            - 'violation_type': what kind of surprise
            - 'learn_from': data for updating physics rules
        """
        result = {
            'violated': False,
            'surprise_amount': 0.0,
            'violation_type': None,
            'learn_from': None
        }
        
        # What did physics rules predict?
        effect = self.action_effects.get(action)
        if not effect:
            return result
            
        # Calculate expected target
        expected_delta = effect.delta
        expected_target = (predicted_position[0] + expected_delta[0], 
                          predicted_position[1] + expected_delta[1])
        
        # Apply our learned physics
        physics_prediction = self.apply_physics_rules(action, predicted_position, expected_target)
        
        if physics_prediction['confidence'] > 0.5:  # We had a physics-based prediction
            physics_expected_blocked = physics_prediction['blocked']
            actual_blocked = (actual_position == predicted_position)  # Didn't move
            
            # Check for violation
            if physics_expected_blocked != actual_blocked:
                result['violated'] = True
                result['surprise_amount'] = 0.7 * physics_prediction['confidence']
                
                if physics_expected_blocked and not actual_blocked:
                    # Physics said blocked but we moved - need to UNLEARN rule
                    result['violation_type'] = 'false_block_prediction'
                    result['learn_from'] = {
                        'type': 'weaken_rule',
                        'rule': physics_prediction['rule_used'],
                        'evidence': {'could_move': True, 'position': actual_position}
                    }
                else:
                    # Physics said clear but we were blocked - need to LEARN new rule
                    result['violation_type'] = 'missed_block'
                    result['learn_from'] = {
                        'type': 'new_collision_rule',
                        'position': expected_target,
                        'action': action,
                        'was_blocked': True
                    }
        
        return result
    
    def add_trigger_rule(self, trigger: Dict[str, Any]) -> None:
        """
        Add an interaction trigger discovered by self-model.
        
        Example: {'trigger_position': (3,4), 'effect': 'wall_opens', 'target_position': (5,6)}
        """
        # Avoid duplicates
        for existing in self.trigger_rules:
            if existing.get('trigger_position') == trigger.get('trigger_position'):
                return
        
        self.trigger_rules.append(trigger)
    
    def integrate_self_discoveries(self, self_identity: Dict[str, Any]) -> None:
        """
        Integrate all discoveries from self-model into world understanding.
        
        Called after self_identity_snapshot is obtained.
        """
        # Mark controlled objects as AGENT type
        for obj in self_identity.get('controlled_objects', []):
            obj_id = obj.get('id') or obj.get('object_id')
            if obj_id:
                self.set_object_type(obj_id, 'AGENT')
        
        # Mark autonomous objects as NPC/ENEMY
        for obj in self_identity.get('autonomous_objects', []):
            obj_id = obj.get('id') or obj.get('object_id')
            if obj_id:
                self.set_object_type(obj_id, 'ENEMY')
        
        # Add collision effects as physics rules
        for effect in self_identity.get('collision_effects', []):
            self.add_physics_rule(effect)
        
        # Add interaction triggers
        for trigger in self_identity.get('interaction_triggers', []):
            self.add_trigger_rule(trigger)
    
    # =========================================================================
    # CODS INTEGRATION METHODS (from agent_consciousness_synthesis.md)
    # Feed operator discoveries into conceptual understanding
    # =========================================================================
    
    def add_concept(self, operator_name: str, explanation: str, evidence: Optional[Dict] = None) -> None:
        """
        Add a concept discovered by CODS engine.
        
        Example: add_concept('detect_symmetry', 'Level has vertical symmetry')
        """
        self.concepts[operator_name] = {
            'name': operator_name,
            'explanation': explanation,
            'evidence': evidence or {},
            'discovered_step': self.state.step,
            'usage_count': 0
        }
    
    def get_applicable_concepts(self) -> List[str]:
        """Get concepts that might apply to current state."""
        return list(self.concepts.keys())


class GoalEvaluator:
    """
    Explicitly evaluates goal conditions against world state.
    
    This replaces implicit reward signals with explicit checking:
    "Is goal A satisfied? Is goal B satisfied? Are both satisfied?"
    """
    
    def __init__(self, goals: CompositionalGoal):
        self.goals = goals
        self.evaluation_history: List[Dict] = []
    
    def evaluate(self, state: WorldState) -> bool:
        """Check if all goals are satisfied in current state."""
        agent = state.get_agent()
        if not agent:
            return False
        
        for goal in self.goals.subgoals:
            goal.satisfied = self._check_goal(state, agent, goal)
        
        # Record evaluation
        self.evaluation_history.append({
            'step': state.step,
            'satisfied': [g.goal_type for g in self.goals.subgoals if g.satisfied],
            'unsatisfied': [g.goal_type for g in self.goals.subgoals if not g.satisfied],
            'progress': self.goals.get_progress()
        })
        
        return self.goals.is_satisfied()
    
    def _check_goal(self, state: WorldState, agent: GameObject, goal: Goal) -> bool:
        """Check a single goal condition."""
        if goal.condition == "reach":
            # Agent must reach target position or target object
            for target_id in goal.target_objects:
                if target_id in state.objects:
                    target = state.objects[target_id]
                    if agent.position == target.position or agent.overlaps(target):
                        return True
            # Also check target_position if specified
            if goal.target_position and agent.position == goal.target_position:
                return True
            return False
        
        elif goal.condition == "collect":
            # Target objects must be removed (collected)
            for target_id in goal.target_objects:
                if target_id in state.objects:
                    return False  # Still exists = not collected
            return True
        
        elif goal.condition == "collect_all":
            # All collectibles must be removed
            collectibles = state.get_collectibles()
            return len(collectibles) == 0
        
        elif goal.condition == "avoid":
            # Agent must NOT be at target positions
            for target_id in goal.target_objects:
                if target_id in state.objects:
                    target = state.objects[target_id]
                    if agent.position == target.position:
                        return False  # At forbidden position
            return True
        
        elif goal.condition == "push_to":
            # A movable object must be at target position
            if not goal.target_position:
                return False
            for target_id in goal.target_objects:
                if target_id in state.objects:
                    target = state.objects[target_id]
                    if target.position == goal.target_position:
                        return True
            return False
        
        elif goal.condition == "activate":
            # Button/switch must be activated
            for target_id in goal.target_objects:
                if target_id in state.objects:
                    target = state.objects[target_id]
                    if target.properties.get('activated', False):
                        return True
            return False
        
        elif goal.condition == "survive":
            # Agent must still exist (not dead)
            return agent is not None
        
        return False
    
    def get_progress(self, state: WorldState) -> float:
        """Get progress toward goals (0.0 to 1.0)."""
        self.evaluate(state)
        return self.goals.get_progress()
    
    def get_distance_to_goal(self, state: WorldState) -> float:
        """Get estimated distance to nearest goal (heuristic for planning)."""
        agent = state.get_agent()
        if not agent:
            return float('inf')
        
        min_distance = float('inf')
        
        for goal in self.goals.get_unsatisfied():
            for target_id in goal.target_objects:
                if target_id in state.objects:
                    target = state.objects[target_id]
                    distance = agent.distance_to(target)
                    min_distance = min(min_distance, distance)
            
            if goal.target_position:
                distance = abs(agent.position[0] - goal.target_position[0]) + \
                           abs(agent.position[1] - goal.target_position[1])
                min_distance = min(min_distance, distance)
        
        return min_distance if min_distance != float('inf') else 0
    
    # =========================================================================
    # NETWORK PERSISTENCE (LS20 Defeat Plan Gap Fix)
    # =========================================================================
    # Share discovered goal structures to network so other agents can learn
    # what kind of goals exist in this game type (match, reach, collect, etc.)
    # =========================================================================
    
    def save_goal_structure_to_network(
        self,
        game_type: str,
        db_path: str = "core_data.db",
        win_validated: bool = False
    ) -> bool:
        """
        Save the discovered goal structure to the network.
        
        Called when:
        1. A game is won (win_validated=True)
        2. Significant goal progress is detected
        
        Args:
            game_type: The game type (first 4 chars of game_id)
            db_path: Path to database
            win_validated: Whether this goal structure led to a win
            
        Returns:
            True if saved successfully
        """
        import sqlite3
        import json
        
        if not self.goals or not self.goals.subgoals:
            return False
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Determine goal type from subgoals
            goal_types = [g.goal_type for g in self.goals.subgoals]
            primary_goal_type = goal_types[0] if goal_types else 'unknown'
            
            # Check if this is a compound goal
            is_compound = len(self.goals.subgoals) > 1
            
            # Serialize sub-goals
            sub_goals_json = json.dumps([
                {
                    'type': g.goal_type,
                    'condition': g.condition,
                    'target_objects': g.target_objects,
                    'target_position': g.target_position
                }
                for g in self.goals.subgoals
            ])
            
            # Completion condition
            completion_condition = json.dumps({
                'composition_type': self.goals.composition_type,
                'all_required': self.goals.composition_type == 'AND'
            })
            
            # Dependency order (subgoal sequence)
            dependency_order = json.dumps([g.goal_type for g in self.goals.subgoals])
            
            # Save or update - use SELECT first since table may not have unique constraint
            cursor.execute("""
                SELECT id, observation_count, confidence, win_validated 
                FROM goal_structure_hypotheses 
                WHERE game_type = ? AND goal_type = ? AND is_active = TRUE
            """, (game_type, primary_goal_type))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing
                existing_id, obs_count, old_confidence, old_win = existing
                new_confidence = min(0.95, old_confidence + (0.2 if win_validated else 0.05))
                cursor.execute("""
                    UPDATE goal_structure_hypotheses SET
                        is_compound = ?,
                        sub_goals = ?,
                        completion_condition = ?,
                        dependency_order = ?,
                        confidence = ?,
                        win_validated = ? OR win_validated,
                        observation_count = observation_count + 1
                    WHERE id = ?
                """, (
                    is_compound,
                    sub_goals_json,
                    completion_condition,
                    dependency_order,
                    new_confidence,
                    win_validated,
                    existing_id
                ))
            else:
                # Insert new
                cursor.execute("""
                    INSERT INTO goal_structure_hypotheses (
                        game_type, goal_type, is_compound, sub_goals,
                        completion_condition, dependency_order, confidence,
                        win_validated, observation_count, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, TRUE)
                """, (
                    game_type,
                    primary_goal_type,
                    is_compound,
                    sub_goals_json,
                    completion_condition,
                    dependency_order,
                    0.7 if win_validated else 0.4,
                    win_validated
                ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"Goal structure save failed: {e}")
            return False
    
    @staticmethod
    def load_goal_structure_from_network(
        game_type: str,
        db_path: str = "core_data.db"
    ) -> Optional[Dict[str, Any]]:
        """
        Load known goal structure for a game type from network.
        
        Returns:
            Dict with goal structure info, or None if not found
        """
        import sqlite3
        import json
        
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT goal_type, is_compound, sub_goals, completion_condition,
                       dependency_order, confidence, win_validated
                FROM goal_structure_hypotheses
                WHERE game_type = ? AND is_active = TRUE
                ORDER BY win_validated DESC, confidence DESC
                LIMIT 1
            """, (game_type,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'goal_type': row['goal_type'],
                    'is_compound': bool(row['is_compound']),
                    'sub_goals': json.loads(row['sub_goals']),
                    'completion_condition': json.loads(row['completion_condition']),
                    'dependency_order': json.loads(row['dependency_order']),
                    'confidence': row['confidence'],
                    'win_validated': bool(row['win_validated'])
                }
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"Goal structure load failed: {e}")
        
        return None


class ActionPlanner:
    """
    Plans action sequences using search.
    
    Even simple BFS can solve many puzzles when you have:
    - Accurate world model
    - Explicit goal conditions
    
    Also supports A* for efficiency.
    """
    
    def __init__(self, world_model: WorldModel, goal_evaluator: GoalEvaluator,
                 max_depth: int = 50, use_astar: bool = True):
        self.world_model = world_model
        self.goal_evaluator = goal_evaluator
        self.max_depth = max_depth
        self.use_astar = use_astar
        self.actions = [1, 2, 3, 4]  # Movement actions (up, down, left, right)
        self.nodes_explored = 0
        self.solution_found = False
    
    def find_plan(self) -> Optional[List[int]]:
        """Find action sequence that achieves goal."""
        self.nodes_explored = 0
        self.solution_found = False
        
        if self.use_astar:
            return self._astar_search()
        else:
            return self._bfs_search()
    
    def _bfs_search(self) -> Optional[List[int]]:
        """Use BFS to find action sequence that achieves goal."""
        initial_state = self.world_model.state.clone()
        
        # BFS queue: (state, action_sequence)
        queue = deque([(initial_state, [])])
        visited = set()
        
        while queue:
            state, actions = queue.popleft()
            self.nodes_explored += 1
            
            # Create state hash for visited check
            state_hash = state.get_state_hash()
            if state_hash in visited:
                continue
            visited.add(state_hash)
            
            # Check if goal achieved
            if self.goal_evaluator.evaluate(state):
                self.solution_found = True
                return actions
            
            # Check depth limit
            if len(actions) >= self.max_depth:
                continue
            
            # Try each action
            for action in self.actions:
                temp_model = WorldModel(state.clone(), self.world_model.agent_id)
                new_state = temp_model.apply_action(action)
                new_actions = actions + [action]
                queue.append((new_state, new_actions))
        
        return None  # No solution found within depth limit
    
    def _astar_search(self) -> Optional[List[int]]:
        """Use A* search for more efficient pathfinding."""
        import heapq
        
        initial_state = self.world_model.state.clone()
        initial_h = self.goal_evaluator.get_distance_to_goal(initial_state)
        
        # Priority queue: (f_score, tie_breaker, state, actions)
        counter = 0
        heap = [(initial_h, counter, initial_state, [])]
        visited = {}  # state_hash -> best g_score
        
        while heap:
            f_score, _, state, actions = heapq.heappop(heap)
            self.nodes_explored += 1
            
            state_hash = state.get_state_hash()
            g_score = len(actions)
            
            # Skip if we've seen this state with better g_score
            if state_hash in visited and visited[state_hash] <= g_score:
                continue
            visited[state_hash] = g_score
            
            # Check if goal achieved
            if self.goal_evaluator.evaluate(state):
                self.solution_found = True
                return actions
            
            # Check depth limit
            if g_score >= self.max_depth:
                continue
            
            # Try each action
            for action in self.actions:
                temp_model = WorldModel(state.clone(), self.world_model.agent_id)
                new_state = temp_model.apply_action(action)
                new_actions = actions + [action]
                
                new_g = len(new_actions)
                new_h = self.goal_evaluator.get_distance_to_goal(new_state)
                new_f = new_g + new_h
                
                counter += 1
                heapq.heappush(heap, (new_f, counter, new_state, new_actions))
        
        return None
    
    def _heuristic(self, state: WorldState) -> float:
        """Calculate heuristic for A* (distance to goal)."""
        return self.goal_evaluator.get_distance_to_goal(state)
    
    def mcts_search(self, budget: int = 100, exploration_constant: float = 1.414) -> Optional[List[int]]:
        """
        Monte Carlo Tree Search for probabilistic planning.
        
        Better than A* when:
        - Outcomes are uncertain/stochastic
        - Action space is large
        - Need to balance exploration vs exploitation
        
        Uses UCB1 for selection and random rollouts for evaluation.
        
        Args:
            budget: Number of simulations to run
            exploration_constant: UCB1 exploration parameter (sqrt(2) is standard)
            
        Returns:
            Best action sequence found, or None
        """
        import math
        import random
        
        class MCTSNode:
            """Node in the MCTS tree."""
            __slots__ = ['state', 'parent', 'action', 'children', 'visits', 'value', 'untried_actions']
            
            def __init__(self, state: WorldState, parent=None, action: Optional[int] = None):
                self.state = state
                self.parent = parent
                self.action = action
                self.children: Dict[int, 'MCTSNode'] = {}
                self.visits = 0
                self.value = 0.0
                self.untried_actions = [1, 2, 3, 4]  # Movement actions
        
        def ucb1(node: MCTSNode, parent_visits: int, c: float) -> float:
            """Upper Confidence Bound for Trees."""
            if node.visits == 0:
                return float('inf')
            exploitation = node.value / node.visits
            exploration = c * math.sqrt(math.log(parent_visits) / node.visits)
            return exploitation + exploration
        
        def select(node: MCTSNode) -> MCTSNode:
            """Select best child using UCB1."""
            while node.untried_actions == [] and node.children:
                node = max(node.children.values(), key=lambda n: ucb1(n, node.visits, exploration_constant))
            return node
        
        def expand(node: MCTSNode) -> MCTSNode:
            """Expand a new child node."""
            if not node.untried_actions:
                return node
            action = random.choice(node.untried_actions)
            node.untried_actions.remove(action)
            
            # Use world model to predict next state
            temp_model = WorldModel(node.state.clone(), self.world_model.agent_id)
            new_state = temp_model.apply_action(action)
            
            child = MCTSNode(new_state, parent=node, action=action)
            node.children[action] = child
            return child
        
        def rollout(state: WorldState, max_rollout_depth: int = 20) -> float:
            """Random rollout to estimate value."""
            temp_state = state.clone()
            
            for _ in range(max_rollout_depth):
                # Check if goal reached
                if self.goal_evaluator.evaluate(temp_state):
                    return 1.0  # Win!
                
                # Random action
                action = random.choice([1, 2, 3, 4])
                temp_model = WorldModel(temp_state, self.world_model.agent_id)
                temp_state = temp_model.apply_action(action)
            
            # Return heuristic value (closer to goal = higher value)
            distance = self.goal_evaluator.get_distance_to_goal(temp_state)
            return 1.0 / (1.0 + distance)  # Normalize to [0, 1]
        
        def backpropagate(node: MCTSNode, value: float):
            """Backpropagate value up the tree."""
            while node:
                node.visits += 1
                node.value += value
                node = node.parent
        
        # Initialize root
        root = MCTSNode(self.world_model.state.clone())
        
        # Run simulations
        for _ in range(budget):
            # Selection
            node = select(root)
            
            # Expansion
            if node.untried_actions and node.visits > 0:
                node = expand(node)
            
            # Simulation (rollout)
            value = rollout(node.state)
            
            # Backpropagation
            backpropagate(node, value)
            
            self.nodes_explored += 1
        
        # Extract best path
        if not root.children:
            return None
        
        # Build action sequence by following most-visited children
        actions = []
        node = root
        while node.children:
            # Select child with most visits (most robust)
            best_child = max(node.children.values(), key=lambda n: n.visits)
            actions.append(best_child.action)
            node = best_child
            
            # Check if this path leads to goal
            if self.goal_evaluator.evaluate(node.state):
                self.solution_found = True
                break
            
            if len(actions) >= self.max_depth:
                break
        
        return actions if actions else None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get planning statistics."""
        return {
            'nodes_explored': self.nodes_explored,
            'solution_found': self.solution_found,
            'max_depth': self.max_depth,
            'use_astar': self.use_astar
        }


class SymbolicReasoningDatabase:
    """Database interface for symbolic reasoning system."""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(DB_PATH)
        self._ensure_tables()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _ensure_tables(self):
        """Create necessary tables if they don't exist."""
        conn = self._get_connection()
        try:
            # Store learned color mappings per game
            conn.execute("""
                CREATE TABLE IF NOT EXISTS symbolic_color_mappings (
                    game_type TEXT,
                    color INTEGER,
                    object_type TEXT,
                    confidence REAL,
                    learned_at TEXT,
                    PRIMARY KEY (game_type, color)
                )
            """)
            
            # Store successful plans
            conn.execute("""
                CREATE TABLE IF NOT EXISTS symbolic_plans (
                    plan_id TEXT PRIMARY KEY,
                    game_type TEXT,
                    level_number INTEGER,
                    initial_state_hash TEXT,
                    action_sequence TEXT,
                    steps INTEGER,
                    success INTEGER,
                    created_at TEXT
                )
            """)
            
            # Store goal inference patterns
            conn.execute("""
                CREATE TABLE IF NOT EXISTS symbolic_goal_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    game_type TEXT,
                    pattern_type TEXT,
                    pattern_data TEXT,
                    success_rate REAL,
                    uses INTEGER DEFAULT 0,
                    created_at TEXT
                )
            """)
            
            # Store agent identification history
            conn.execute("""
                CREATE TABLE IF NOT EXISTS symbolic_agent_identifications (
                    game_type TEXT,
                    level_number INTEGER,
                    agent_color INTEGER,
                    agent_size INTEGER,
                    confidence REAL,
                    identified_at TEXT,
                    PRIMARY KEY (game_type, level_number)
                )
            """)
            
            conn.commit()
        finally:
            conn.close()
    
    def save_color_mapping(self, game_type: str, color: int, obj_type: ObjectType, confidence: float):
        """Save learned color mapping."""
        conn = self._get_connection()
        try:
            conn.execute("""
                INSERT OR REPLACE INTO symbolic_color_mappings
                (game_type, color, object_type, confidence, learned_at)
                VALUES (?, ?, ?, ?, ?)
            """, (game_type, color, obj_type.value, confidence, datetime.now().isoformat()))
            conn.commit()
        finally:
            conn.close()
    
    def get_color_mappings(self, game_type: str) -> Dict[int, ObjectType]:
        """Get learned color mappings for a game type."""
        conn = self._get_connection()
        try:
            rows = conn.execute("""
                SELECT color, object_type FROM symbolic_color_mappings
                WHERE game_type = ? AND confidence > 0.5
            """, (game_type,)).fetchall()
            
            mappings = {}
            for row in rows:
                try:
                    mappings[row['color']] = ObjectType(row['object_type'])
                except ValueError:
                    pass
            return mappings
        finally:
            conn.close()
    
    def save_successful_plan(self, game_type: str, level: int, initial_hash: str, 
                             actions: List[int], success: bool):
        """Save a successful plan for reuse."""
        import uuid
        plan_id = f"plan_{uuid.uuid4().hex[:12]}"
        
        conn = self._get_connection()
        try:
            conn.execute("""
                INSERT INTO symbolic_plans
                (plan_id, game_type, level_number, initial_state_hash, action_sequence, 
                 steps, success, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (plan_id, game_type, level, initial_hash, json.dumps(actions),
                  len(actions), 1 if success else 0, datetime.now().isoformat()))
            conn.commit()
        finally:
            conn.close()
    
    def get_cached_plan(self, game_type: str, level: int, state_hash: str) -> Optional[List[int]]:
        """Get a cached plan if available."""
        conn = self._get_connection()
        try:
            row = conn.execute("""
                SELECT action_sequence FROM symbolic_plans
                WHERE game_type = ? AND level_number = ? AND initial_state_hash = ?
                AND success = 1
                ORDER BY steps ASC LIMIT 1
            """, (game_type, level, state_hash)).fetchone()
            
            if row:
                return json.loads(row['action_sequence'])
            return None
        finally:
            conn.close()
    
    def save_agent_identification(self, game_type: str, level: int, color: int, 
                                  size: int, confidence: float):
        """Save agent identification for a game/level."""
        conn = self._get_connection()
        try:
            conn.execute("""
                INSERT OR REPLACE INTO symbolic_agent_identifications
                (game_type, level_number, agent_color, agent_size, confidence, identified_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (game_type, level, color, size, confidence, datetime.now().isoformat()))
            conn.commit()
        finally:
            conn.close()
    
    def get_agent_color(self, game_type: str, level: int) -> Optional[int]:
        """Get known agent color for a game/level."""
        conn = self._get_connection()
        try:
            row = conn.execute("""
                SELECT agent_color FROM symbolic_agent_identifications
                WHERE game_type = ? AND level_number = ? AND confidence > 0.5
            """, (game_type, level)).fetchone()
            return row['agent_color'] if row else None
        finally:
            conn.close()


class SymbolicReasoningEngine:
    """
    Main interface for symbolic reasoning in complex games.
    
    Usage:
        engine = SymbolicReasoningEngine('lp85')
        engine.initialize(initial_frame)
        
        while not done:
            action = engine.get_next_action()
            new_frame = env.step(action)
            engine.update(action, new_frame)
    """
    
    def __init__(self, game_type: str = "unknown", level: int = 1):
        self.game_type = game_type
        self.level = level
        self.db = SymbolicReasoningDatabase()
        
        # Initialize parser with learned mappings
        color_mappings = self.db.get_color_mappings(game_type)
        self.parser = ConnectedComponentParser(color_mappings=color_mappings)
        
        # Agent identifier for learning which object we control
        self.agent_identifier = AgentIdentifier(self.parser)
        
        self.world_model: Optional[WorldModel] = None
        self.goal_evaluator: Optional[GoalEvaluator] = None
        self.planner: Optional[ActionPlanner] = None
        self.current_plan: List[int] = []
        self.plan_index = 0
        
        # State tracking
        self.initialized = False
        self.last_frame: Optional[np.ndarray] = None
        self.action_count = 0
        self.goal_achieved = False
        
        # Learning mode
        self.learning_mode = True  # Start in learning mode to identify agent
        self.min_learning_actions = 8  # Minimum actions before planning
    
    def initialize(self, initial_frame: np.ndarray, goals: Optional[CompositionalGoal] = None):
        """Initialize from first frame of game."""
        if isinstance(initial_frame, list):
            initial_frame = np.array(initial_frame, dtype=int)
        
        self.last_frame = initial_frame
        
        # Check for cached agent identification
        known_agent_color = self.db.get_agent_color(self.game_type, self.level)
        if known_agent_color is not None:
            self.parser.learn_agent_color(known_agent_color)
            self.learning_mode = False
        
        # Parse scene
        initial_state = self.parser.parse(initial_frame)
        
        # Try to find cached plan
        state_hash = initial_state.get_state_hash()
        cached_plan = self.db.get_cached_plan(self.game_type, self.level, state_hash)
        if cached_plan:
            self.current_plan = cached_plan
            self.plan_index = 0
            logger.info(f"Using cached plan with {len(cached_plan)} actions")
        
        # Create world model
        self.world_model = WorldModel(initial_state)
        
        # Set up goals (may need to be inferred)
        if goals is None:
            goals = self._infer_goals(initial_state)
        
        self.goal_evaluator = GoalEvaluator(goals)
        
        # Create planner
        self.planner = ActionPlanner(self.world_model, self.goal_evaluator, max_depth=50)
        
        self.initialized = True
        
        # If not in learning mode and no cached plan, generate new plan
        if not self.learning_mode and not self.current_plan:
            self._generate_plan()
    
    def _infer_goals(self, state: WorldState) -> CompositionalGoal:
        """
        Infer goals from initial state.
        
        First checks network for known goal structures (Phase 4.4 LS20 Defeat Plan),
        then falls back to heuristics.
        
        Heuristics:
        - Goal objects should be reached
        - Collectibles should be collected
        - If no explicit goals, reach opposite corner
        """
        # First, try to load known goal structure from network
        known_goals = GoalEvaluator.load_goal_structure_from_network(self.game_type)
        if known_goals and known_goals.get('win_validated'):
            # Reconstruct goals from network knowledge
            subgoals = []
            for sub in known_goals.get('sub_goals', []):
                subgoals.append(Goal(
                    goal_type=sub.get('type', 'reach'),
                    target_objects=sub.get('targets', []),
                    condition=sub.get('condition', 'reach')
                ))
            if subgoals:
                logic = 'AND' if known_goals.get('is_compound') else 'AND'
                logger.info(f"Loaded {len(subgoals)} goal(s) from network for {self.game_type}")
                return CompositionalGoal(subgoals=subgoals, logic=logic)
        
        # Fall back to heuristic inference
        subgoals = []
        
        for obj in state.objects.values():
            if obj.object_type == ObjectType.GOAL:
                subgoals.append(Goal(
                    goal_type="reach",
                    target_objects=[obj.object_id],
                    condition="reach"
                ))
            elif obj.object_type == ObjectType.COLLECTIBLE:
                subgoals.append(Goal(
                    goal_type="collect",
                    target_objects=[obj.object_id],
                    condition="collect"
                ))
        
        # If no goals found, create default goal (reach bottom-right)
        if not subgoals:
            grid_shape = state.grid.shape
            subgoals.append(Goal(
                goal_type="reach_corner",
                target_objects=[],
                condition="reach",
                target_position=(grid_shape[0] - 2, grid_shape[1] - 2)
            ))
        
        # Default to AND logic (all goals must be satisfied)
        return CompositionalGoal(subgoals=subgoals, logic="AND")
    
    def _generate_plan(self):
        """Generate action plan using search."""
        if self.planner and self.world_model:
            plan = self.planner.find_plan()
            if plan:
                self.current_plan = plan
                self.plan_index = 0
                logger.info(f"Generated plan with {len(plan)} actions "
                           f"({self.planner.nodes_explored} nodes explored)")
                
                # Cache successful plan
                state_hash = self.world_model.state.get_state_hash()
                self.db.save_successful_plan(
                    self.game_type, self.level, state_hash, plan, True
                )
            else:
                # No plan found - fall back to exploration
                self.current_plan = []
                logger.warning(f"No plan found after {self.planner.nodes_explored} nodes")
    
    def get_next_action(self) -> int:
        """Get next action from plan, or explore if no plan."""
        self.action_count += 1
        
        # In learning mode, explore to identify agent
        if self.learning_mode:
            # Cycle through movement actions
            action = (self.action_count % 4) + 1
            
            # Check if we've learned enough
            if self.action_count >= self.min_learning_actions:
                if self.agent_identifier.confidence > 0.5:
                    self.learning_mode = False
                    if self.world_model:
                        agent_color = self.agent_identifier.get_agent_color(self.world_model.state)
                    else:
                        agent_color = None
                    if agent_color is not None:
                        self.parser.learn_agent_color(agent_color)
                        self.db.save_agent_identification(
                            self.game_type, self.level, agent_color, 1, 
                            self.agent_identifier.confidence
                        )
                    # Now generate plan
                    self._generate_plan()
            
            return action
        
        # Use plan if available
        if self.plan_index < len(self.current_plan):
            action = self.current_plan[self.plan_index]
            self.plan_index += 1
            return action
        else:
            # No plan or plan exhausted - use network-informed exploration
            # METATHEORY: Even during exploration, query network for guidance
            try:
                from multi_stage_matching_pipeline import get_network_informed_action
                from database_interface import DatabaseInterface
                db = DatabaseInterface()
                game_id = getattr(self, 'current_game_id', 'unknown')
                level = getattr(self, 'current_level', 1)
                return get_network_informed_action(db, game_id, level)
            except Exception:
                import random
                return random.choice([1, 2, 3, 4])
    
    def update(self, action: int, new_frame: np.ndarray):
        """Update world model with action result and observed frame."""
        if isinstance(new_frame, list):
            new_frame = np.array(new_frame, dtype=int)
        
        # Record action for agent identification
        if self.learning_mode and self.last_frame is not None:
            self.agent_identifier.record_action(action, self.last_frame, new_frame)
        
        self.last_frame = new_frame
        
        if self.world_model is None:
            return
        
        # Apply action to model
        predicted_state = self.world_model.apply_action(action)
        
        # Parse actual frame
        observed_state = self.parser.parse(new_frame)
        
        # Check for model discrepancy and correct if needed
        self._check_and_correct_model(predicted_state, observed_state)
        
        # Check if goal achieved
        if self.goal_evaluator and self.goal_evaluator.evaluate(self.world_model.state):
            self.goal_achieved = True
            logger.info(f"Goal achieved after {self.world_model.state.step} steps!")
            
            # Save learned color mappings
            agent = self.world_model.state.get_agent()
            if agent:
                self.db.save_color_mapping(
                    self.game_type, agent.color, ObjectType.AGENT, 0.9
                )
    
    def _check_and_correct_model(self, predicted: WorldState, observed: WorldState):
        """Compare predicted vs observed state and correct model if needed."""
        # Simple check: if agent positions don't match, resync
        pred_agent = predicted.get_agent()
        obs_agent = observed.get_agent()
        
        if pred_agent and obs_agent:
            if pred_agent.position != obs_agent.position:
                # Model is wrong, resync to observed state
                logger.debug(f"Model correction: predicted {pred_agent.position} "
                            f"vs observed {obs_agent.position}")
                if self.world_model:
                    self.world_model.state = observed
                    self.world_model.history.append(observed.clone())
                
                # Invalidate current plan
                self.current_plan = []
                self.plan_index = 0
    
    def get_agent_identity(self) -> Optional[str]:
        """Get the ID of the object the agent controls."""
        if self.world_model:
            agent = self.world_model.state.get_agent()
            return agent.object_id if agent else None
        return None
    
    def get_state(self) -> Optional[WorldState]:
        """Get current world state."""
        return self.world_model.state if self.world_model else None
    
    def get_goal_progress(self) -> float:
        """Get progress toward goals."""
        if self.goal_evaluator and self.world_model:
            return self.goal_evaluator.get_progress(self.world_model.state)
        return 0.0
    
    def is_goal_achieved(self) -> bool:
        """Check if goal has been achieved."""
        return self.goal_achieved
    
    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            'game_type': self.game_type,
            'level': self.level,
            'action_count': self.action_count,
            'learning_mode': self.learning_mode,
            'has_plan': len(self.current_plan) > 0,
            'plan_length': len(self.current_plan),
            'plan_progress': self.plan_index,
            'goal_achieved': self.goal_achieved,
            'goal_progress': self.get_goal_progress(),
            'agent_confidence': self.agent_identifier.confidence,
            'planner_stats': self.planner.get_stats() if self.planner else {}
        }


# Integration with existing system
def create_symbolic_engine_for_game(game_type: str, level: int = 1) -> SymbolicReasoningEngine:
    """
    Factory function to create appropriate symbolic engine for game type.
    
    Different games may need different:
    - Color mappings
    - Goal inference heuristics
    - Action effect mappings
    """
    engine = SymbolicReasoningEngine(game_type, level)
    
    # Game-specific configuration
    if game_type == "lp85":
        # lp85 specific settings - multi-object tracking game
        engine.parser = ConnectedComponentParser(color_mappings={
            1: ObjectType.AGENT,
            2: ObjectType.GOAL,
            3: ObjectType.OBSTACLE,
            4: ObjectType.COLLECTIBLE,
            5: ObjectType.MOVABLE,
        })
        engine.min_learning_actions = 12  # Need more learning for complex games
    
    return engine


class SymbolicGameplayIntegration:
    """
    Integration layer for using symbolic reasoning within the main gameplay loop.
    
    This bridges the gap between the existing core_gameplay.py and 
    the new symbolic reasoning engine.
    """
    
    def __init__(self, game_type: str):
        self.game_type = game_type
        self.engines: Dict[int, SymbolicReasoningEngine] = {}  # level -> engine
        self.enabled = game_type in ['lp85']  # Only enabled for complex games
    
    def should_use_symbolic(self, level: int) -> bool:
        """Check if symbolic reasoning should be used for this level."""
        return self.enabled
    
    def get_engine(self, level: int) -> SymbolicReasoningEngine:
        """Get or create engine for a specific level."""
        if level not in self.engines:
            self.engines[level] = create_symbolic_engine_for_game(self.game_type, level)
        return self.engines[level]
    
    def initialize_level(self, level: int, initial_frame: np.ndarray):
        """Initialize symbolic reasoning for a level."""
        engine = self.get_engine(level)
        engine.initialize(initial_frame)
    
    def get_action(self, level: int, current_frame: np.ndarray) -> Optional[int]:
        """Get next action from symbolic reasoning."""
        if not self.enabled:
            return None
        
        engine = self.get_engine(level)
        if not engine.initialized:
            engine.initialize(current_frame)
        
        return engine.get_next_action()
    
    def update(self, level: int, action: int, new_frame: np.ndarray):
        """Update symbolic state after action."""
        if not self.enabled:
            return
        
        engine = self.get_engine(level)
        if engine.initialized:
            engine.update(action, new_frame)
    
    def is_goal_achieved(self, level: int) -> bool:
        """Check if symbolic goal achieved."""
        if not self.enabled or level not in self.engines:
            return False
        return self.engines[level].is_goal_achieved()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get stats for all engines."""
        return {
            'game_type': self.game_type,
            'enabled': self.enabled,
            'engines': {
                level: engine.get_stats() 
                for level, engine in self.engines.items()
            }
        }


if __name__ == "__main__":
    # Demo and test
    print("=" * 60)
    print("SYMBOLIC REASONING ENGINE - FULLY IMPLEMENTED")
    print("=" * 60)
    print()
    
    # Test basic functionality
    print("Testing components:")
    print()
    
    # 1. Test scene parser
    test_frame = np.array([
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 3, 0, 0, 0, 0, 2, 0],
        [0, 0, 0, 1, 1, 0, 0, 0],
        [0, 0, 0, 1, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 4, 4, 0, 0, 0, 0, 0],
        [0, 4, 4, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ], dtype=int)
    
    parser = ConnectedComponentParser()
    state = parser.parse(test_frame)
    print(f"1. Scene Parser: Found {len(state.objects)} objects")
    for obj_id, obj in state.objects.items():
        print(f"   - {obj_id}: {obj.object_type.value} at {obj.position}, color={obj.color}, size={obj.size}")
    
    # 2. Test goal inference
    engine = SymbolicReasoningEngine('test_game')
    engine.initialize(test_frame)
    if engine.goal_evaluator:
        print(f"\n2. Goal Inference: {len(engine.goal_evaluator.goals.subgoals)} goals identified")
        for goal in engine.goal_evaluator.goals.subgoals:
            print(f"   - {goal.goal_type}: {goal.condition}")
    else:
        print("\n2. Goal Inference: No goal evaluator")
    
    # 3. Test planner
    if engine.planner:
        plan = engine.planner.find_plan()
        if plan:
            print(f"\n3. Action Planner: Found plan with {len(plan)} actions")
            print(f"   Actions: {plan[:10]}{'...' if len(plan) > 10 else ''}")
            print(f"   Nodes explored: {engine.planner.nodes_explored}")
        else:
            print(f"\n3. Action Planner: No plan found ({engine.planner.nodes_explored} nodes explored)")
    
    # 4. Test world model
    print(f"\n4. World Model:")
    if engine.world_model:
        agent = engine.world_model.state.get_agent()
        print(f"   Agent: {agent.object_id if agent else 'None'}")
        print(f"   Goals: {len(engine.world_model.state.get_goals())}")
        print(f"   Obstacles: {len(engine.world_model.state.get_obstacles())}")
    else:
        print("   Not initialized")
    
    # 5. Test database
    db = SymbolicReasoningDatabase()
    print(f"\n5. Database: Connected to {db.db_path}")
    
    # 6. Test integration
    integration = SymbolicGameplayIntegration('lp85')
    print(f"\n6. Integration: Enabled={integration.enabled}")
    
    print()
    print("=" * 60)
    print("STATUS: FULLY IMPLEMENTED")
    print("=" * 60)
    print()
    print("This module provides:")
    print("  1. ConnectedComponentParser - Robust scene parsing")
    print("  2. AgentIdentifier - Learn which object we control")
    print("  3. WorldModel - Simulate action effects")
    print("  4. GoalEvaluator - Explicit goal checking")
    print("  5. ActionPlanner - A* and BFS search")
    print("  6. SymbolicReasoningDatabase - Persist learned knowledge")
    print("  7. SymbolicReasoningEngine - Main interface")
    print("  8. SymbolicGameplayIntegration - Integration with core_gameplay.py")
    print()
    print("For lp85 and other complex games requiring:")
    print("  - Multi-object tracking")
    print("  - Compositional goals")
    print("  - Causal simulation")
    print("  - State-space search")
