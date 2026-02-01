#!/usr/bin/env python3
"""
Symbolic State Tracker
======================

Tracks symbolic state of key/lock objects across frames for transformation puzzles.

SYMBOLIC MECHANICS - Universal Component

In symbolic transformation puzzles, the agent must:
1. Identify "key" objects (controllable) and "lock" objects (target)
2. Track their symbolic properties: shape, color, orientation
3. Understand that key must MATCH lock to win
4. Detect when touching tools changes key's symbolic state

Applicable to ALL games, not just specific game types.

Module size: ~500 lines (within 300-700 target)
"""
import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import json
import time
from typing import Any, Dict, List, Optional, Tuple

from engines.engine_logger import get_engine_logger

logger = get_engine_logger("symbolic_tracker")


class SymbolicStateTracker:
    """
    Tracks symbolic state of key/lock objects across frames.

    Maintains symbolic state over time and detects meaningful changes
    (transformations) vs. noise (movement).
    """

    def __init__(self, game_type: Optional[str] = None, db_path: str = "core_data.db"):
        self.game_type = game_type
        self.db_path = db_path

        # Current state tracking
        self.key_objects: Dict[str, Dict[str, Any]] = {}  # object_id -> symbolic state
        self.lock_objects: Dict[str, Dict[str, Any]] = {}
        self.tool_objects: Dict[str, Dict[str, Any]] = {}

        # State history for change detection
        self.state_history: List[Dict[str, Any]] = []
        self.transformation_log: List[Dict[str, Any]] = []

        # Match tracking
        self.current_match_score: float = 0.0
        self.match_history: List[float] = []

        # Tool effects to save (batch)
        self._tool_effects_to_save: List[Dict[str, Any]] = []

    def identify_symbolic_objects(
        self,
        frame: List[List[int]],
        controlled_colors: Optional[List[int]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Identify key, lock, and tool objects in the frame.

        Key objects: Objects controlled by the agent
        Lock objects: Static objects the key must match
        Tool objects: Small objects that transform the key when touched

        Args:
            frame: 2D grid of color values
            controlled_colors: Colors the agent controls

        Returns:
            Dict with 'keys', 'locks', 'tools' sub-dicts
        """
        result: Dict[str, Dict[str, Any]] = {'keys': {}, 'locks': {}, 'tools': {}}

        if not frame or not frame[0]:
            return result

        height = len(frame)
        width = len(frame[0])
        controlled = set(controlled_colors or [])

        # Find all connected objects by color
        visited: set[Tuple[int, int]] = set()
        objects: List[Dict[str, Any]] = []

        for y in range(height):
            for x in range(width):
                c = frame[y][x]
                if c != 0 and (x, y) not in visited:
                    # Flood fill to find connected component
                    obj_cells: List[Tuple[int, int]] = []
                    stack = [(x, y)]
                    while stack:
                        px, py = stack.pop()
                        if (px, py) in visited:
                            continue
                        if px < 0 or py < 0 or px >= width or py >= height:
                            continue
                        if frame[py][px] != c:
                            continue
                        visited.add((px, py))
                        obj_cells.append((px, py))
                        stack.extend([(px+1, py), (px-1, py), (px, py+1), (px, py-1)])

                    if obj_cells:
                        objects.append({
                            'color': c,
                            'cells': obj_cells,
                            'cell_count': len(obj_cells)
                        })

        # Classify objects
        for obj in objects:
            obj_id = f"obj_{obj['color']}_{len(obj['cells'])}"

            # Extract symbolic state
            cells = obj['cells']
            min_x = min(c[0] for c in cells)
            max_x = max(c[0] for c in cells)
            min_y = min(c[1] for c in cells)
            max_y = max(c[1] for c in cells)

            symbolic_state: Dict[str, Any] = {
                'color': obj['color'],
                'cell_count': obj['cell_count'],
                'bbox': [min_x, min_y, max_x + 1, max_y + 1],
                'centroid': (
                    sum(c[0] for c in cells) / len(cells),
                    sum(c[1] for c in cells) / len(cells)
                ),
                'aspect_ratio': (max_x - min_x + 1) / max((max_y - min_y + 1), 1),
                'shape_signature': self._compute_shape_signature(cells)
            }

            # Classify based on size and control
            if obj['color'] in controlled:
                result['keys'][obj_id] = symbolic_state
            elif obj['cell_count'] <= 4:
                result['tools'][obj_id] = symbolic_state
            else:
                result['locks'][obj_id] = symbolic_state

        # Update internal state
        self.key_objects = result['keys']
        self.lock_objects = result['locks']
        self.tool_objects = result['tools']

        return result

    def _compute_shape_signature(self, cells: List[Tuple[int, int]]) -> int:
        """Compute a hash signature for the shape (position-independent)."""
        if not cells:
            return 0

        # Normalize to origin
        min_x = min(c[0] for c in cells)
        min_y = min(c[1] for c in cells)
        normalized = sorted((c[0] - min_x, c[1] - min_y) for c in cells)

        return hash(tuple(normalized))

    def update_state(
        self,
        frame: List[List[int]],
        controlled_colors: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Update symbolic state tracking with new frame.

        Returns dict indicating what changed.
        """
        previous_keys = dict(self.key_objects)

        # Identify current objects
        current_objects = self.identify_symbolic_objects(frame, controlled_colors)

        changes: Dict[str, bool] = {
            'key_changed': False,
            'lock_changed': False,
            'key_shape_changed': False,
            'key_color_changed': False,
            'match_improved': False,
            'match_decreased': False
        }

        # Compare key objects
        for key_id, key_state in current_objects['keys'].items():
            if key_id in previous_keys:
                prev = previous_keys[key_id]
                if key_state['shape_signature'] != prev['shape_signature']:
                    changes['key_changed'] = True
                    changes['key_shape_changed'] = True
                    self.transformation_log.append({
                        'type': 'shape_change',
                        'object': key_id,
                        'before': prev['shape_signature'],
                        'after': key_state['shape_signature'],
                        'timestamp': time.time()
                    })
                if key_state['color'] != prev['color']:
                    changes['key_changed'] = True
                    changes['key_color_changed'] = True

        # Calculate match score
        new_match_score = self.calculate_match_score()
        if new_match_score > self.current_match_score + 0.1:
            changes['match_improved'] = True
        elif new_match_score < self.current_match_score - 0.1:
            changes['match_decreased'] = True

        self.current_match_score = new_match_score
        self.match_history.append(new_match_score)

        # Store in history
        self.state_history.append({
            'keys': dict(self.key_objects),
            'locks': dict(self.lock_objects),
            'match_score': new_match_score,
            'timestamp': time.time()
        })

        # Limit history size
        if len(self.state_history) > 100:
            self.state_history = self.state_history[-100:]

        return changes

    def calculate_match_score(self) -> float:
        """
        Calculate how well key objects match lock objects.

        Returns:
            1.0 = perfect match (key shape == lock shape)
            0.0 = no match
        """
        if not self.key_objects or not self.lock_objects:
            return 0.0

        best_match = 0.0

        for key_state in self.key_objects.values():
            for lock_state in self.lock_objects.values():
                # Compare shape signatures
                shape_match = 1.0 if key_state['shape_signature'] == lock_state['shape_signature'] else 0.0

                # Compare colors (some puzzles require color match too)
                color_match = 1.0 if key_state['color'] == lock_state['color'] else 0.0

                # Compare aspect ratios
                aspect_diff = abs(key_state['aspect_ratio'] - lock_state['aspect_ratio'])
                aspect_match = max(0.0, 1.0 - aspect_diff)

                # Weighted combination
                match_score = shape_match * 0.6 + aspect_match * 0.3 + color_match * 0.1
                best_match = max(best_match, match_score)

        return best_match

    def get_transformation_needed(self) -> Dict[str, Any]:
        """
        Determine what transformation is needed to match key to lock.

        Returns information about what needs to change.
        """
        result: Dict[str, Any] = {
            'transformation_needed': False,
            'target_shape': None,
            'current_shape': None,
            'steps_estimate': 0
        }

        if not self.key_objects or not self.lock_objects:
            return result

        # Get first key and lock (simplification)
        key_state = next(iter(self.key_objects.values()))
        lock_state = next(iter(self.lock_objects.values()))

        if key_state['shape_signature'] != lock_state['shape_signature']:
            result['transformation_needed'] = True
            result['current_shape'] = key_state['shape_signature']
            result['target_shape'] = lock_state['shape_signature']

            # Estimate steps based on transformations needed
            steps_estimate = 0

            # Shape mismatch: typically 1-3 tool uses needed
            steps_estimate += 15  # ~3 tool uses at 5 actions each

            # Color mismatch (if applicable)
            if key_state.get('color') != lock_state.get('color'):
                steps_estimate += 10  # ~2 tool uses for color change

            # Add navigation overhead based on number of tools
            num_tools = len(self.tool_objects)
            if num_tools > 0:
                steps_estimate += num_tools * 8  # Navigation to each tool
            else:
                steps_estimate += 20  # Exploration to find tools

            # Cap at reasonable maximum (most levels solvable in ~60 actions)
            result['steps_estimate'] = min(steps_estimate, 60)

        return result

    def detect_tool_effect(
        self,
        frame_before: List[List[int]],
        frame_after: List[List[int]],
        tool_position: Tuple[int, int],
        controlled_colors: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Detect what effect a tool had on the key object.

        Call this after agent touched a tool to learn the tool's effect.
        """
        result: Dict[str, Any] = {
            'effect_detected': False,
            'effect_type': None,
            'tool_position': tool_position,
            'before_state': None,
            'after_state': None,
            'tool_color': None
        }

        # Try to get tool color at position
        if tool_position and frame_before:
            try:
                tx, ty = tool_position
                if 0 <= ty < len(frame_before) and 0 <= tx < len(frame_before[0]):
                    result['tool_color'] = frame_before[ty][tx]
            except (TypeError, IndexError):
                # Invalid tool position or frame data - skip
                pass

        # Get states before and after
        before_objects = self.identify_symbolic_objects(frame_before, controlled_colors)
        after_objects = self.identify_symbolic_objects(frame_after, controlled_colors)

        # Compare key objects
        before: Optional[Dict[str, Any]] = None
        after: Optional[Dict[str, Any]] = None

        for key_id in before_objects['keys']:
            if key_id in after_objects['keys']:
                before = before_objects['keys'][key_id]
                after = after_objects['keys'][key_id]

                result['before_state'] = before
                result['after_state'] = after

                # Type guard: both before and after are now set
                if before is not None and after is not None:
                    if before['shape_signature'] != after['shape_signature']:
                        result['effect_detected'] = True
                        result['effect_type'] = 'shape_change'
                    elif before['color'] != after['color']:
                        result['effect_detected'] = True
                        result['effect_type'] = 'color_change'

        if result['effect_detected'] and before and after:
            # Log this tool effect
            self.transformation_log.append({
                'type': 'tool_effect',
                'tool_position': tool_position,
                'tool_color': result.get('tool_color'),
                'effect_type': result['effect_type'],
                'before': result['before_state'],
                'after': result['after_state'],
                'timestamp': time.time()
            })

            # Track unique tool effects for network sharing
            self._tool_effects_to_save.append({
                'tool_color': result.get('tool_color'),
                'effect_type': result['effect_type'],
                'tool_position': tool_position,
                'state_before_signature': before.get('shape_signature'),
                'state_after_signature': after.get('shape_signature'),
            })

        return result

    def get_match_progress(self) -> Dict[str, Any]:
        """Get progress toward matching key to lock."""
        return {
            'current_match_score': self.current_match_score,
            'match_history': self.match_history[-10:] if self.match_history else [],
            'improving': (
                len(self.match_history) >= 2 and
                self.match_history[-1] > self.match_history[-2]
            ),
            'transformations_made': len(self.transformation_log),
            'transformation_needed': self.get_transformation_needed(),
            'key_count': len(self.key_objects),
            'lock_count': len(self.lock_objects),
            'tool_count': len(self.tool_objects)
        }

    def reset(self) -> None:
        """Reset tracker for new level."""
        self.key_objects = {}
        self.lock_objects = {}
        self.tool_objects = {}
        self.state_history = []
        self.transformation_log = []
        self.current_match_score = 0.0
        self.match_history = []
        self._tool_effects_to_save = []

    def to_dict(self) -> Dict[str, Any]:
        """Serialize tracker state."""
        return {
            'game_type': self.game_type,
            'key_objects': self.key_objects,
            'lock_objects': self.lock_objects,
            'tool_objects': self.tool_objects,
            'current_match_score': self.current_match_score,
            'transformations_made': len(self.transformation_log)
        }

    def save_discoveries_to_network(
        self,
        agent_id: Optional[str] = None,
        generation: Optional[int] = None
    ) -> int:
        """
        Save key/lock/tool discoveries to the network database.

        Allows other agents to benefit from symbolic object identification.

        Returns:
            Number of discoveries saved
        """
        if not self.game_type:
            return 0

        saved = 0

        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Save key objects
            for obj_id, state in self.key_objects.items():
                cursor.execute("""
                    INSERT OR REPLACE INTO symbolic_state_hypotheses (
                        game_type, object_id, object_role, region_bbox,
                        shape_signature, dominant_color, discovered_by_agent,
                        discovery_generation, confidence, is_active
                    ) VALUES (?, ?, 'key', ?, ?, ?, ?, ?, 0.7, TRUE)
                """, (
                    self.game_type,
                    obj_id,
                    json.dumps(state.get('bbox', [])),
                    str(state.get('shape_signature', '')),
                    state.get('color'),
                    agent_id,
                    generation
                ))
                saved += 1

            # Save lock objects
            for obj_id, state in self.lock_objects.items():
                cursor.execute("""
                    INSERT OR REPLACE INTO symbolic_state_hypotheses (
                        game_type, object_id, object_role, region_bbox,
                        shape_signature, dominant_color, discovered_by_agent,
                        discovery_generation, confidence, is_active
                    ) VALUES (?, ?, 'lock', ?, ?, ?, ?, ?, 0.7, TRUE)
                """, (
                    self.game_type,
                    obj_id,
                    json.dumps(state.get('bbox', [])),
                    str(state.get('shape_signature', '')),
                    state.get('color'),
                    agent_id,
                    generation
                ))
                saved += 1

            # Save tool objects
            for obj_id, state in self.tool_objects.items():
                cursor.execute("""
                    INSERT OR REPLACE INTO symbolic_state_hypotheses (
                        game_type, object_id, object_role, region_bbox,
                        shape_signature, dominant_color, discovered_by_agent,
                        discovery_generation, confidence, is_active
                    ) VALUES (?, ?, 'tool', ?, ?, ?, ?, ?, 0.6, TRUE)
                """, (
                    self.game_type,
                    obj_id,
                    json.dumps(state.get('bbox', [])),
                    str(state.get('shape_signature', '')),
                    state.get('color'),
                    agent_id,
                    generation
                ))
                saved += 1

            # Save tool effects
            for effect in self._tool_effects_to_save:
                try:
                    tool_sig = f"color_{effect.get('tool_color', 'unknown')}"
                    cursor.execute("""
                        INSERT OR REPLACE INTO tool_effect_hypotheses (
                            game_type, tool_signature, effect_type,
                            state_before_signature, state_after_signature,
                            observation_count, confidence, discovered_by_agent,
                            discovery_generation, is_active
                        ) VALUES (?, ?, ?, ?, ?,
                                  COALESCE((SELECT observation_count + 1 FROM tool_effect_hypotheses
                                            WHERE game_type = ? AND tool_signature = ?), 1),
                                  0.6, ?, ?, TRUE)
                    """, (
                        self.game_type,
                        tool_sig,
                        effect.get('effect_type'),
                        str(effect.get('state_before_signature', ''))[:50],
                        str(effect.get('state_after_signature', ''))[:50],
                        self.game_type,
                        tool_sig,
                        agent_id,
                        generation
                    ))
                    saved += 1
                except Exception as te:
                    logger.debug(f"Failed to save tool effect: {te}")

            # Clear saved effects
            self._tool_effects_to_save = []

            conn.commit()
            conn.close()

        except Exception as e:
            logger.warning(f"Failed to save symbolic discoveries: {e}")

        return saved
