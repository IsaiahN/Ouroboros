"""
Spatial Effect Learning - Learn click effect patterns and goal configurations.

This module tracks which positions affect which other positions in click-based
puzzles, enabling the system to learn effect patterns and goal states.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


@dataclass
class SpatialEffect:
    """A learned spatial effect from a click action."""
    game_type: str
    click_rel_x: int  # Relative X from click position
    click_rel_y: int  # Relative Y from click position
    effect_type: str  # 'color_change', 'toggle', etc.
    observation_count: int = 1


@dataclass
class GoalConfiguration:
    """A known winning grid configuration."""
    game_type: str
    level_number: int
    grid_state: Dict[Tuple[int, int], int]  # {(x, y): color}
    success_count: int = 0
    failure_count: int = 0


class SpatialEffectLearner:
    """
    Learn spatial effect patterns from click observations.

    Tracks which grid positions change when specific positions are clicked,
    allowing the system to learn patterns like "clicking X affects X, X+1, X-1".
    """

    def __init__(self, db_interface):
        """
        Initialize the spatial effect learner.

        Args:
            db_interface: Database interface for persistence
        """
        self.db = db_interface
        self._effect_cache: Dict[str, List[Tuple[int, int]]] = {}

    def record_click_effect(
        self,
        game_type: str,
        click_grid_pos: Tuple[int, int],
        changes: List[Tuple[int, int, int, int]],  # [(x, y, color_before, color_after), ...]
    ) -> None:
        """
        Record that clicking at click_grid_pos caused changes at other positions.

        Args:
            game_type: The game type identifier
            click_grid_pos: (x, y) grid position that was clicked
            changes: List of (x, y, color_before, color_after) tuples
        """
        if not changes:
            return

        click_x, click_y = click_grid_pos

        for (cx, cy, color_before, color_after) in changes:
            # Calculate relative position from click
            rel_x = cx - click_x
            rel_y = cy - click_y

            try:
                self.db.execute_insert("""
                    INSERT INTO spatial_effects (
                        game_type, click_rel_x, click_rel_y,
                        effect_type, observation_count
                    ) VALUES (?, ?, ?, 'color_change', 1)
                    ON CONFLICT(game_type, click_rel_x, click_rel_y)
                    DO UPDATE SET observation_count = observation_count + 1
                """, (game_type, rel_x, rel_y))
            except Exception:
                # Fallback for databases that don't support ON CONFLICT
                existing = self.db.execute_query("""
                    SELECT observation_count FROM spatial_effects
                    WHERE game_type = ? AND click_rel_x = ? AND click_rel_y = ?
                """, (game_type, rel_x, rel_y))

                if existing:
                    self.db.execute_update("""
                        UPDATE spatial_effects
                        SET observation_count = observation_count + 1
                        WHERE game_type = ? AND click_rel_x = ? AND click_rel_y = ?
                    """, (game_type, rel_x, rel_y))
                else:
                    self.db.execute_insert("""
                        INSERT INTO spatial_effects (
                            game_type, click_rel_x, click_rel_y, effect_type, observation_count
                        ) VALUES (?, ?, ?, 'color_change', 1)
                    """, (game_type, rel_x, rel_y))

        # Invalidate cache
        self._effect_cache.pop(game_type, None)

    def get_effect_pattern(
        self,
        game_type: str,
        min_observations: int = 3,
    ) -> List[Tuple[int, int]]:
        """
        Get the learned effect pattern for this game.

        Args:
            game_type: The game type identifier
            min_observations: Minimum observations required

        Returns:
            List of (rel_x, rel_y) positions affected by a click
        """
        # Check cache
        if game_type in self._effect_cache:
            return self._effect_cache[game_type]

        results = self.db.execute_query("""
            SELECT click_rel_x, click_rel_y, observation_count
            FROM spatial_effects
            WHERE game_type = ?
            AND observation_count >= ?
            ORDER BY observation_count DESC
        """, (game_type, min_observations))

        pattern = [(r['click_rel_x'], r['click_rel_y']) for r in results]

        # Cache the result
        self._effect_cache[game_type] = pattern

        return pattern

    def get_effect_pattern_with_confidence(
        self,
        game_type: str,
    ) -> List[Tuple[int, int, float]]:
        """
        Get effect pattern with confidence scores.

        Returns:
            List of (rel_x, rel_y, confidence) tuples
        """
        results = self.db.execute_query("""
            SELECT click_rel_x, click_rel_y, observation_count
            FROM spatial_effects
            WHERE game_type = ?
            ORDER BY observation_count DESC
        """, (game_type,))

        if not results:
            return []

        # Calculate confidence based on observation count
        max_obs = max(r['observation_count'] for r in results)

        return [
            (
                r['click_rel_x'],
                r['click_rel_y'],
                r['observation_count'] / max_obs
            )
            for r in results
        ]

    def describe_effect_pattern(self, game_type: str) -> str:
        """Get a human-readable description of the effect pattern."""
        pattern = self.get_effect_pattern(game_type)

        if not pattern:
            return "No effect pattern learned yet"

        if len(pattern) == 1 and pattern[0] == (0, 0):
            return "Click affects only the clicked cell"

        # Check for common patterns
        if set(pattern) == {(0, 0), (0, 1), (0, -1), (1, 0), (-1, 0)}:
            return "Plus/cross pattern (center + 4 neighbors)"

        if all(abs(x) <= 1 and abs(y) <= 1 for x, y in pattern) and len(pattern) == 9:
            return "3x3 square pattern"

        return f"Custom pattern affecting {len(pattern)} cells: {pattern}"


class MultiObjectGoalTracker:
    """
    Track goal requirements for multi-object puzzles.

    Records winning and losing configurations to learn what
    the goal state looks like for each level.
    """

    def __init__(self, db_interface):
        """
        Initialize the goal tracker.

        Args:
            db_interface: Database interface for persistence
        """
        self.db = db_interface
        self._goal_cache: Dict[Tuple[str, int], Dict] = {}

    def record_outcome(
        self,
        game_type: str,
        level_number: int,
        grid_state: Dict[Tuple[int, int], int],
        was_success: bool,
    ) -> None:
        """
        Record a grid state that led to success/failure.

        Args:
            game_type: The game type identifier
            level_number: Level within the game
            grid_state: {(x, y): color} mapping
            was_success: Whether this state led to level completion
        """
        state_hash = self._hash_grid_state(grid_state)
        state_json = json.dumps({f"{k[0]},{k[1]}": v for k, v in grid_state.items()})

        if was_success:
            try:
                self.db.execute_insert("""
                    INSERT INTO goal_configurations (
                        game_type, level_number, state_hash, grid_state, success_count
                    ) VALUES (?, ?, ?, ?, 1)
                    ON CONFLICT(game_type, level_number, state_hash)
                    DO UPDATE SET success_count = success_count + 1
                """, (game_type, level_number, state_hash, state_json))
            except Exception:
                # Fallback
                self._record_outcome_fallback(
                    game_type, level_number, state_hash, state_json, was_success
                )
        else:
            try:
                self.db.execute_insert("""
                    INSERT INTO goal_configurations (
                        game_type, level_number, state_hash, grid_state, failure_count
                    ) VALUES (?, ?, ?, ?, 1)
                    ON CONFLICT(game_type, level_number, state_hash)
                    DO UPDATE SET failure_count = failure_count + 1
                """, (game_type, level_number, state_hash, state_json))
            except Exception:
                self._record_outcome_fallback(
                    game_type, level_number, state_hash, state_json, was_success
                )

        # Invalidate cache
        self._goal_cache.pop((game_type, level_number), None)

    def _record_outcome_fallback(
        self,
        game_type: str,
        level_number: int,
        state_hash: str,
        state_json: str,
        was_success: bool,
    ) -> None:
        """Fallback method for databases without ON CONFLICT."""
        existing = self.db.execute_query("""
            SELECT success_count, failure_count FROM goal_configurations
            WHERE game_type = ? AND level_number = ? AND state_hash = ?
        """, (game_type, level_number, state_hash))

        if existing:
            if was_success:
                self.db.execute_update("""
                    UPDATE goal_configurations
                    SET success_count = success_count + 1
                    WHERE game_type = ? AND level_number = ? AND state_hash = ?
                """, (game_type, level_number, state_hash))
            else:
                self.db.execute_update("""
                    UPDATE goal_configurations
                    SET failure_count = failure_count + 1
                    WHERE game_type = ? AND level_number = ? AND state_hash = ?
                """, (game_type, level_number, state_hash))
        else:
            sc = 1 if was_success else 0
            fc = 0 if was_success else 1
            self.db.execute_insert("""
                INSERT INTO goal_configurations (
                    game_type, level_number, state_hash, grid_state,
                    success_count, failure_count
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (game_type, level_number, state_hash, state_json, sc, fc))

    def get_target_configuration(
        self,
        game_type: str,
        level_number: int,
        min_successes: int = 2,
    ) -> Optional[Dict[Tuple[int, int], int]]:
        """
        Get the known winning configuration for this level.

        Args:
            game_type: The game type identifier
            level_number: Level within the game
            min_successes: Minimum success observations required

        Returns:
            {(x, y): color} mapping or None if unknown
        """
        # Check cache
        cache_key = (game_type, level_number)
        if cache_key in self._goal_cache:
            return self._goal_cache[cache_key]

        result = self.db.execute_query("""
            SELECT grid_state
            FROM goal_configurations
            WHERE game_type = ? AND level_number = ?
            AND success_count >= ?
            ORDER BY success_count DESC
            LIMIT 1
        """, (game_type, level_number, min_successes))

        if result:
            state_json = result[0]['grid_state']
            parsed = json.loads(state_json)
            # Convert string keys back to tuples
            goal = {
                (int(k.split(',')[0]), int(k.split(',')[1])): v
                for k, v in parsed.items()
            }
            self._goal_cache[cache_key] = goal
            return goal

        return None

    def get_all_known_goals(self, game_type: str) -> Dict[int, Dict[Tuple[int, int], int]]:
        """
        Get all known goal configurations for a game.

        Returns:
            {level_number: {(x, y): color}} mapping
        """
        results = self.db.execute_query("""
            SELECT level_number, grid_state
            FROM goal_configurations
            WHERE game_type = ?
            AND success_count >= 2
            ORDER BY level_number, success_count DESC
        """, (game_type,))

        goals = {}
        for r in results:
            level = r['level_number']
            if level not in goals:  # Take first (highest success_count)
                parsed = json.loads(r['grid_state'])
                goals[level] = {
                    (int(k.split(',')[0]), int(k.split(',')[1])): v
                    for k, v in parsed.items()
                }

        return goals

    def _hash_grid_state(self, grid_state: Dict[Tuple[int, int], int]) -> str:
        """Create a stable hash of a grid state."""
        # Sort by position for consistent ordering
        sorted_items = sorted(grid_state.items())
        return str(hash(tuple(sorted_items)))


class PropertyExtractor:
    """
    Extract grid-level properties and detect position changes.

    Provides utilities for analyzing frame changes at the grid level.
    """

    def __init__(self):
        self._grid_size_cache: Dict[Tuple[int, int], int] = {}

    def detect_position_changes(
        self,
        frame_before: np.ndarray,
        frame_after: np.ndarray,
        grid_size: Optional[int] = None,
    ) -> List[Tuple[int, int, int, int]]:
        """
        Find which grid positions changed and how.

        Args:
            frame_before: Frame before action
            frame_after: Frame after action
            grid_size: Grid size (auto-detected if None)

        Returns:
            List of (x, y, color_before, color_after) tuples
        """
        if grid_size is None:
            grid_size = self._detect_grid_size(frame_before)

        if grid_size == 0:
            return []

        changes = []

        cell_height = frame_before.shape[0] // grid_size
        cell_width = frame_before.shape[1] // grid_size

        for gy in range(grid_size):
            for gx in range(grid_size):
                # Get cell region
                y1 = gy * cell_height
                x1 = gx * cell_width
                y2 = y1 + cell_height
                x2 = x1 + cell_width

                cell_before = frame_before[y1:y2, x1:x2]
                cell_after = frame_after[y1:y2, x1:x2]

                color_before = self._dominant_color(cell_before)
                color_after = self._dominant_color(cell_after)

                if color_before != color_after:
                    changes.append((gx, gy, color_before, color_after))

        return changes

    def extract_grid_state(
        self,
        frame: np.ndarray,
        grid_size: Optional[int] = None,
    ) -> Dict[Tuple[int, int], int]:
        """
        Extract the current grid state as a dictionary.

        Args:
            frame: Current frame
            grid_size: Grid size (auto-detected if None)

        Returns:
            {(x, y): color} mapping
        """
        if grid_size is None:
            grid_size = self._detect_grid_size(frame)

        if grid_size == 0:
            return {}

        state = {}

        cell_height = frame.shape[0] // grid_size
        cell_width = frame.shape[1] // grid_size

        for gy in range(grid_size):
            for gx in range(grid_size):
                y1 = gy * cell_height
                x1 = gx * cell_width
                y2 = y1 + cell_height
                x2 = x1 + cell_width

                cell = frame[y1:y2, x1:x2]
                state[(gx, gy)] = self._dominant_color(cell)

        return state

    def _detect_grid_size(self, frame: np.ndarray) -> int:
        """
        Auto-detect the grid size from frame dimensions.

        Tries common ARC grid sizes and returns the best fit.
        """
        height, width = frame.shape[:2]
        cache_key = (height, width)

        if cache_key in self._grid_size_cache:
            return self._grid_size_cache[cache_key]

        # Common ARC grid sizes
        candidates = [8, 10, 16, 6, 12, 32, 64, 4, 5, 7, 9, 11]

        for size in candidates:
            if height % size == 0 and width % size == 0:
                cell_h = height // size
                cell_w = width // size
                # Reasonable cell size check
                if 4 <= cell_h <= 32 and 4 <= cell_w <= 32:
                    self._grid_size_cache[cache_key] = size
                    return size

        # Fallback: find any divisor
        for size in range(3, 65):
            if height % size == 0 and width % size == 0:
                self._grid_size_cache[cache_key] = size
                return size

        # Last resort
        self._grid_size_cache[cache_key] = 8
        return 8

    def _dominant_color(self, cell: np.ndarray) -> int:
        """Get the dominant color in a cell region."""
        if cell.size == 0:
            return 0

        # Flatten and count
        flat = cell.flatten()
        counts = np.bincount(flat.astype(int), minlength=13)
        return int(np.argmax(counts))

    def find_differences(
        self,
        current_state: Dict[Tuple[int, int], int],
        target_state: Dict[Tuple[int, int], int],
    ) -> List[Tuple[int, int]]:
        """
        Find positions where current state differs from target.

        Returns:
            List of (x, y) positions that need to change
        """
        differences = []

        all_positions = set(current_state.keys()) | set(target_state.keys())

        for pos in all_positions:
            current_color = current_state.get(pos, 0)
            target_color = target_state.get(pos, 0)

            if current_color != target_color:
                differences.append(pos)

        return differences

    def pixel_to_grid(
        self,
        pixel_x: int,
        pixel_y: int,
        frame_width: int = 64,
        frame_height: int = 64,
        grid_size: int = 8,
    ) -> Tuple[int, int]:
        """Convert pixel coordinates to grid coordinates."""
        cell_width = frame_width // grid_size
        cell_height = frame_height // grid_size

        grid_x = pixel_x // cell_width
        grid_y = pixel_y // cell_height

        return (min(grid_x, grid_size - 1), min(grid_y, grid_size - 1))

    def grid_to_pixel(
        self,
        grid_x: int,
        grid_y: int,
        frame_width: int = 64,
        frame_height: int = 64,
        grid_size: int = 8,
    ) -> Tuple[int, int]:
        """Convert grid coordinates to pixel coordinates (center of cell)."""
        cell_width = frame_width // grid_size
        cell_height = frame_height // grid_size

        pixel_x = grid_x * cell_width + cell_width // 2
        pixel_y = grid_y * cell_height + cell_height // 2

        return (pixel_x, pixel_y)
