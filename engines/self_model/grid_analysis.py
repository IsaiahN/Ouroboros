"""
Grid Analysis - Frame Differencing and Grid Operations
=======================================================

Provides tools for analyzing grid frames:
- Frame differencing (what changed between frames)
- Collision detection
- Rotation detection  
- Object property analysis
- Grid region classification

Design Principles:
- Pure functions where possible (no side effects)
- Explicit return types (never ambiguous None)
- Detailed logging for debugging
- Input validation with clear errors
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set, Any
from enum import Enum
import math

logger = logging.getLogger(__name__)


class ChangeType(Enum):
    """Types of frame changes."""
    NONE = "none"
    APPEARED = "appeared"
    DISAPPEARED = "disappeared"
    MOVED = "moved"
    COLOR_CHANGED = "color_changed"
    SHAPE_CHANGED = "shape_changed"


class RegionType(Enum):
    """Types of grid regions."""
    EMPTY = "empty"
    PLAYER_AREA = "player_area"
    OBSTACLE_AREA = "obstacle_area"
    GOAL_AREA = "goal_area"
    HAZARD_AREA = "hazard_area"
    BOUNDARY = "boundary"


@dataclass
class CellChange:
    """A change at a specific cell."""
    y: int
    x: int
    old_color: int
    new_color: int
    
    @property
    def change_type(self) -> ChangeType:
        if self.old_color == 0 and self.new_color > 0:
            return ChangeType.APPEARED
        elif self.old_color > 0 and self.new_color == 0:
            return ChangeType.DISAPPEARED
        elif self.old_color != self.new_color:
            return ChangeType.COLOR_CHANGED
        return ChangeType.NONE


@dataclass
class ObjectMovement:
    """Movement of an object between frames."""
    object_id: str
    color: int
    old_positions: Set[Tuple[int, int]]
    new_positions: Set[Tuple[int, int]]
    
    @property
    def old_centroid(self) -> Tuple[float, float]:
        if not self.old_positions:
            return (0.0, 0.0)
        return (
            sum(p[0] for p in self.old_positions) / len(self.old_positions),
            sum(p[1] for p in self.old_positions) / len(self.old_positions)
        )
    
    @property
    def new_centroid(self) -> Tuple[float, float]:
        if not self.new_positions:
            return (0.0, 0.0)
        return (
            sum(p[0] for p in self.new_positions) / len(self.new_positions),
            sum(p[1] for p in self.new_positions) / len(self.new_positions)
        )
    
    @property
    def displacement(self) -> Tuple[float, float]:
        old = self.old_centroid
        new = self.new_centroid
        return (new[0] - old[0], new[1] - old[1])
    
    @property
    def moved(self) -> bool:
        dy, dx = self.displacement
        return abs(dy) > 0.1 or abs(dx) > 0.1
    
    @property 
    def direction(self) -> Optional[str]:
        dy, dx = self.displacement
        if abs(dy) < 0.1 and abs(dx) < 0.1:
            return None
        if abs(dy) >= abs(dx):
            return 'down' if dy > 0 else 'up'
        return 'right' if dx > 0 else 'left'


@dataclass
class FrameDiff:
    """Difference between two frames."""
    cell_changes: List[CellChange]
    object_movements: List[ObjectMovement]
    appeared_objects: List[str]
    disappeared_objects: List[str]
    is_identical: bool
    
    @property
    def change_count(self) -> int:
        return len(self.cell_changes)
    
    @property
    def any_movement(self) -> bool:
        return any(m.moved for m in self.object_movements)


@dataclass
class CollisionInfo:
    """Information about a collision."""
    collider_id: str
    target_id: str
    collision_point: Tuple[int, int]
    collision_type: str  # 'overlap', 'adjacent', 'blocked'


@dataclass
class RotationInfo:
    """Information about detected rotation."""
    object_id: str
    rotation_degrees: int  # 90, 180, 270
    center: Tuple[float, float]
    confidence: float


class GridAnalyzer:
    """
    Analyzes grid frames for changes, collisions, and patterns.
    
    Usage:
        analyzer = GridAnalyzer()
        
        # Get frame difference
        diff = analyzer.get_diff(frame_before, frame_after)
        print(f"Changed cells: {diff.change_count}")
        
        for movement in diff.object_movements:
            if movement.moved:
                print(f"{movement.object_id} moved {movement.direction}")
        
        # Detect collision
        collision = analyzer.detect_collision(frame, object_id='player')
        if collision:
            print(f"Player collided with {collision.target_id}")
        
        # Check for rotation
        rotation = analyzer.detect_rotation(positions_before, positions_after)
        if rotation:
            print(f"Rotated {rotation.rotation_degrees} degrees")
    """
    
    def __init__(self):
        """Initialize grid analyzer."""
        self._cache: Dict[str, Any] = {}
        logger.debug("[GRID] Initialized")
    
    def get_diff(
        self,
        frame_before: List[List[int]],
        frame_after: List[List[int]],
        threshold: int = 0
    ) -> FrameDiff:
        """
        Get difference between two frames.
        
        Args:
            frame_before: Previous frame state
            frame_after: Current frame state
            threshold: Minimum color difference to count as change
            
        Returns:
            FrameDiff with all changes detected
            
        Raises:
            ValueError: If frames have different dimensions
        """
        # Validate inputs
        if not frame_before or not frame_after:
            raise ValueError("[GRID] Cannot diff empty frames")
        
        h1, w1 = len(frame_before), len(frame_before[0]) if frame_before else 0
        h2, w2 = len(frame_after), len(frame_after[0]) if frame_after else 0
        
        if h1 != h2 or w1 != w2:
            raise ValueError(f"[GRID] Frame dimensions differ: ({h1}x{w1}) vs ({h2}x{w2})")
        
        # Find cell changes
        cell_changes = []
        for y in range(h1):
            for x in range(w1):
                old = frame_before[y][x]
                new = frame_after[y][x]
                if abs(old - new) > threshold:
                    cell_changes.append(CellChange(y, x, old, new))
        
        if not cell_changes:
            return FrameDiff(
                cell_changes=[],
                object_movements=[],
                appeared_objects=[],
                disappeared_objects=[],
                is_identical=True
            )
        
        # Find object positions in both frames
        objects_before = self._find_objects(frame_before)
        objects_after = self._find_objects(frame_after)
        
        # Determine movements
        object_movements = []
        appeared = []
        disappeared = []
        
        all_colors = set(objects_before.keys()) | set(objects_after.keys())
        
        for color in all_colors:
            obj_id = f"color_{color}"
            old_pos = objects_before.get(color, set())
            new_pos = objects_after.get(color, set())
            
            if not old_pos and new_pos:
                appeared.append(obj_id)
            elif old_pos and not new_pos:
                disappeared.append(obj_id)
            else:
                movement = ObjectMovement(
                    object_id=obj_id,
                    color=color,
                    old_positions=old_pos,
                    new_positions=new_pos
                )
                object_movements.append(movement)
        
        logger.debug(
            f"[GRID] Diff: {len(cell_changes)} cells, "
            f"{len([m for m in object_movements if m.moved])} moved, "
            f"{len(appeared)} appeared, {len(disappeared)} disappeared"
        )
        
        return FrameDiff(
            cell_changes=cell_changes,
            object_movements=object_movements,
            appeared_objects=appeared,
            disappeared_objects=disappeared,
            is_identical=False
        )
    
    def detect_collision(
        self,
        frame: List[List[int]],
        object_color: int,
        check_adjacent: bool = True
    ) -> Optional[CollisionInfo]:
        """
        Detect if object is colliding with another object.
        
        Args:
            frame: Current frame
            object_color: Color of object to check
            check_adjacent: Include adjacent cells as potential collisions
            
        Returns:
            CollisionInfo if collision detected, None otherwise
        """
        positions = set()
        height, width = len(frame), len(frame[0]) if frame else 0
        
        for y in range(height):
            for x in range(width):
                if frame[y][x] == object_color:
                    positions.add((y, x))
        
        if not positions:
            logger.debug(f"[GRID] No positions found for color {object_color}")
            return None
        
        # Check each position for adjacent different-colored cells
        for y, x in positions:
            neighbors = [(y-1, x), (y+1, x), (y, x-1), (y, x+1)]
            
            for ny, nx in neighbors:
                if 0 <= ny < height and 0 <= nx < width:
                    neighbor_color = frame[ny][nx]
                    if neighbor_color != 0 and neighbor_color != object_color:
                        return CollisionInfo(
                            collider_id=f"color_{object_color}",
                            target_id=f"color_{neighbor_color}",
                            collision_point=(ny, nx),
                            collision_type='adjacent'
                        )
        
        return None
    
    def detect_rotation(
        self,
        positions_before: Set[Tuple[int, int]],
        positions_after: Set[Tuple[int, int]],
        tolerance: float = 0.5
    ) -> Optional[RotationInfo]:
        """
        Detect if positions rotated around center.
        
        Args:
            positions_before: Set of (y, x) positions before
            positions_after: Set of (y, x) positions after  
            tolerance: Max deviation to consider as rotation
            
        Returns:
            RotationInfo if rotation detected, None otherwise
        """
        if len(positions_before) != len(positions_after):
            return None
        
        if len(positions_before) < 3:
            return None  # Need at least 3 points for reliable rotation detection
        
        # Find centroids
        cy_before = sum(p[0] for p in positions_before) / len(positions_before)
        cx_before = sum(p[1] for p in positions_before) / len(positions_before)
        cy_after = sum(p[0] for p in positions_after) / len(positions_after)
        cx_after = sum(p[1] for p in positions_after) / len(positions_after)
        
        # Centroids should be approximately the same for rotation
        if abs(cy_before - cy_after) > tolerance or abs(cx_before - cx_after) > tolerance:
            return None
        
        center = ((cy_before + cy_after) / 2, (cx_before + cx_after) / 2)
        
        # Try each rotation angle
        for degrees in [90, 180, 270]:
            rotated = self._rotate_positions(positions_before, center, degrees)
            
            # Check if rotated matches after
            match_count = 0
            for pos in rotated:
                rounded = (round(pos[0]), round(pos[1]))
                if rounded in positions_after:
                    match_count += 1
            
            confidence = match_count / len(positions_before)
            
            if confidence >= 0.8:  # 80% match threshold
                logger.info(f"[GRID] Detected {degrees}° rotation, confidence={confidence:.2f}")
                return RotationInfo(
                    object_id="unknown",
                    rotation_degrees=degrees,
                    center=center,
                    confidence=confidence
                )
        
        return None
    
    def classify_regions(
        self,
        frame: List[List[int]],
        player_colors: Optional[Set[int]] = None,
        goal_colors: Optional[Set[int]] = None,
        hazard_colors: Optional[Set[int]] = None
    ) -> Dict[Tuple[int, int], RegionType]:
        """
        Classify each cell into region types.
        
        Args:
            frame: Current frame
            player_colors: Known player object colors
            goal_colors: Known goal object colors
            hazard_colors: Known hazard colors
            
        Returns:
            Dict mapping (y,x) to RegionType
        """
        player_colors = player_colors or set()
        goal_colors = goal_colors or set()
        hazard_colors = hazard_colors or set()
        
        regions: Dict[Tuple[int, int], RegionType] = {}
        height, width = len(frame), len(frame[0]) if frame else 0
        
        for y in range(height):
            for x in range(width):
                color = frame[y][x]
                
                if color == 0:
                    regions[(y, x)] = RegionType.EMPTY
                elif color in player_colors:
                    regions[(y, x)] = RegionType.PLAYER_AREA
                elif color in goal_colors:
                    regions[(y, x)] = RegionType.GOAL_AREA
                elif color in hazard_colors:
                    regions[(y, x)] = RegionType.HAZARD_AREA
                elif self._is_boundary(y, x, height, width, frame, color):
                    regions[(y, x)] = RegionType.BOUNDARY
                else:
                    regions[(y, x)] = RegionType.OBSTACLE_AREA
        
        return regions
    
    def find_autonomous_objects(
        self,
        frame_before: List[List[int]],
        frame_after: List[List[int]],
        player_action: Optional[str] = None
    ) -> List[ObjectMovement]:
        """
        Find objects that moved without player action.
        
        Args:
            frame_before: Frame before player action
            frame_after: Frame after player action
            player_action: The action player took (to exclude player movement)
            
        Returns:
            List of ObjectMovement for objects that moved autonomously
        """
        diff = self.get_diff(frame_before, frame_after)
        
        autonomous = []
        for movement in diff.object_movements:
            if not movement.moved:
                continue
            
            # If player moved, exclude objects moving in expected direction
            if player_action:
                expected_dir = self._action_to_direction(player_action)
                if expected_dir and movement.direction == expected_dir:
                    continue
            
            autonomous.append(movement)
        
        if autonomous:
            logger.debug(
                f"[GRID] Found {len(autonomous)} autonomous movements: "
                f"{[m.object_id for m in autonomous]}"
            )
        
        return autonomous
    
    def get_object_shape(
        self,
        frame: List[List[int]],
        color: int
    ) -> Dict[str, Any]:
        """
        Analyze shape of an object.
        
        Args:
            frame: Current frame
            color: Color of object to analyze
            
        Returns:
            Dict with shape properties:
            - positions: Set of (y, x) positions
            - size: Number of cells
            - bounding_box: (min_y, min_x, max_y, max_x)
            - centroid: (y, x) center point
            - is_rectangular: Whether shape is a rectangle
            - is_connected: Whether all cells are connected
        """
        positions = set()
        
        for y, row in enumerate(frame):
            for x, c in enumerate(row):
                if c == color:
                    positions.add((y, x))
        
        if not positions:
            return {
                'positions': set(),
                'size': 0,
                'bounding_box': None,
                'centroid': None,
                'is_rectangular': False,
                'is_connected': False
            }
        
        min_y = min(p[0] for p in positions)
        max_y = max(p[0] for p in positions)
        min_x = min(p[1] for p in positions)
        max_x = max(p[1] for p in positions)
        
        centroid_y = sum(p[0] for p in positions) / len(positions)
        centroid_x = sum(p[1] for p in positions) / len(positions)
        
        # Check if rectangular
        bbox_size = (max_y - min_y + 1) * (max_x - min_x + 1)
        is_rectangular = len(positions) == bbox_size
        
        # Check if connected (simple check)
        is_connected = self._check_connectivity(positions)
        
        return {
            'positions': positions,
            'size': len(positions),
            'bounding_box': (min_y, min_x, max_y, max_x),
            'centroid': (centroid_y, centroid_x),
            'is_rectangular': is_rectangular,
            'is_connected': is_connected
        }
    
    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================
    
    def _find_objects(
        self,
        frame: List[List[int]]
    ) -> Dict[int, Set[Tuple[int, int]]]:
        """Find all objects (by color) in frame."""
        objects: Dict[int, Set[Tuple[int, int]]] = {}
        
        for y, row in enumerate(frame):
            for x, color in enumerate(row):
                if color > 0:
                    if color not in objects:
                        objects[color] = set()
                    objects[color].add((y, x))
        
        return objects
    
    def _rotate_positions(
        self,
        positions: Set[Tuple[int, int]],
        center: Tuple[float, float],
        degrees: int
    ) -> List[Tuple[float, float]]:
        """Rotate positions around center."""
        radians = math.radians(degrees)
        cos_theta = math.cos(radians)
        sin_theta = math.sin(radians)
        cy, cx = center
        
        rotated = []
        for y, x in positions:
            # Translate to origin
            dy = y - cy
            dx = x - cx
            # Rotate
            new_dy = dy * cos_theta - dx * sin_theta
            new_dx = dy * sin_theta + dx * cos_theta
            # Translate back
            rotated.append((cy + new_dy, cx + new_dx))
        
        return rotated
    
    def _is_boundary(
        self,
        y: int,
        x: int,
        height: int,
        width: int,
        frame: List[List[int]],
        color: int
    ) -> bool:
        """Check if cell is part of boundary."""
        # Edge cells are boundary
        if y == 0 or y == height - 1 or x == 0 or x == width - 1:
            return True
        
        # Check if this color forms a continuous edge
        edge_count = 0
        for ey in range(height):
            if frame[ey][0] == color or frame[ey][width-1] == color:
                edge_count += 1
        for ex in range(width):
            if frame[0][ex] == color or frame[height-1][ex] == color:
                edge_count += 1
        
        # If this color appears a lot on edges, it's probably boundary
        return edge_count > (height + width) // 2
    
    def _action_to_direction(self, action: str) -> Optional[str]:
        """Convert action to expected direction."""
        mapping = {
            'ACTION1': 'up',
            'ACTION2': 'down',
            'ACTION3': 'left',
            'ACTION4': 'right'
        }
        return mapping.get(action)
    
    def _check_connectivity(self, positions: Set[Tuple[int, int]]) -> bool:
        """Check if all positions are connected (4-connectivity)."""
        if not positions:
            return True
        
        # BFS from first position
        visited = set()
        queue = [next(iter(positions))]
        
        while queue:
            y, x = queue.pop(0)
            if (y, x) in visited:
                continue
            visited.add((y, x))
            
            for ny, nx in [(y-1, x), (y+1, x), (y, x-1), (y, x+1)]:
                if (ny, nx) in positions and (ny, nx) not in visited:
                    queue.append((ny, nx))
        
        return len(visited) == len(positions)


# =============================================================================
# STANDALONE UTILITY FUNCTIONS
# =============================================================================

def quick_diff(
    frame_before: List[List[int]],
    frame_after: List[List[int]]
) -> int:
    """
    Quick count of changed cells between frames.
    
    Args:
        frame_before: Previous frame
        frame_after: Current frame
        
    Returns:
        Number of cells that changed
    """
    if not frame_before or not frame_after:
        return 0
    
    count = 0
    for row_a, row_b in zip(frame_before, frame_after):
        for a, b in zip(row_a, row_b):
            if a != b:
                count += 1
    
    return count


def frames_identical(
    frame_a: List[List[int]],
    frame_b: List[List[int]]
) -> bool:
    """
    Check if two frames are identical.
    
    Args:
        frame_a: First frame
        frame_b: Second frame
        
    Returns:
        True if frames are identical
    """
    if len(frame_a) != len(frame_b):
        return False
    
    for row_a, row_b in zip(frame_a, frame_b):
        if row_a != row_b:
            return False
    
    return True


def find_moved_object(
    frame_before: List[List[int]],
    frame_after: List[List[int]],
    direction: str
) -> Optional[int]:
    """
    Find which object color moved in the expected direction.
    
    Args:
        frame_before: Frame before action
        frame_after: Frame after action
        direction: Expected direction ('up', 'down', 'left', 'right')
        
    Returns:
        Color of object that moved, or None
    """
    analyzer = GridAnalyzer()
    diff = analyzer.get_diff(frame_before, frame_after)
    
    for movement in diff.object_movements:
        if movement.moved and movement.direction == direction:
            return movement.color
    
    return None
