"""
ACTION6 Behavior Module
=======================

Handles all ACTION6-specific behavior tracking and learning:

1. **Pseudo Buttons**: Screen regions that trigger effects when clicked
   - save_pseudo_button_behavior, get_pseudo_button_behavior, get_all_pseudo_buttons
   - classify_pseudo_button_effects

2. **Object Selection**: Clicking objects to select them for ACTION1-4 control
   - track_selection_change, verify_selection_controls_movement
   - get_current_selection, discover_selectable_objects

3. **Shape Generalization**: Learn "horizontal bars are selectable" not just "color 9"
   - compute_shape_signature, get_selectable_shapes_for_game
   - find_objects_matching_shape, get_untried_objects_for_frontier

4. **Availability Tracking**: When ACTION6 appears/disappears (signals selectability)
   - track_action6_availability, detect_action6_state_change
   - get_selectability_triggers

ACTION6 is the most complex action in ARC-AGI-3:
- Uses x,y coordinates (0-63 range) like a touchscreen
- Can click "buttons" that trigger game events
- Can click "objects" to SELECT them for control by ACTION1-4
- Availability changes signal game state transitions

This module extracts all ACTION6 logic from agent_self_model.py for modularity.
"""

import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import hashlib
import json
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


class Action6BehaviorEngine:
    """
    Manages ACTION6 behavior learning: pseudobuttons, selection, availability.

    ACTION6 is unique among ARC actions because it uses coordinates
    to click on screen regions or objects. This engine tracks:
    - What happens when you click different screen regions
    - Which objects can be selected for movement control
    - When ACTION6 becomes available/unavailable
    """

    def __init__(self, db_path: str = "core_data.db"):
        """
        Initialize ACTION6 behavior engine.

        Args:
            db_path: Path to database
        """
        from database_interface import DatabaseInterface
        self.db = DatabaseInterface(db_path)
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        """Ensure required tables exist."""
        # Tables should already exist from complete_database_schema.sql
        pass

    # =========================================================================
    # PSEUDO BUTTON BEHAVIOR
    # =========================================================================

    def save_pseudo_button_behavior(
        self,
        game_type: str,
        level: int,
        region_x: int,
        region_y: int,
        produces_action: str,
        movement_direction: str,
        affected_objects: List[str],
        effect_description: str,
        confidence: float
    ) -> None:
        """
        Save discovered pseudo button behavior to network-level knowledge.

        When agents discover what clicking a screen region does,
        share it so other agents can use the pseudo buttons effectively.

        Args:
            game_type: The game type
            level: Level number
            region_x, region_y: Screen region (0-7 each, dividing 64x64 into 8x8)
            produces_action: Equivalent action (e.g., 'up', 'down', 'toggle')
            movement_direction: Direction of movement if any
            affected_objects: Object IDs affected by this button
            effect_description: Human-readable description
            confidence: Confidence level (0.0 to 1.0)
        """
        existing = self.db.execute_query("""
            SELECT confidence, discovery_count FROM pseudo_button_behavior
            WHERE game_type = ? AND level_number = ? AND region_x = ? AND region_y = ?
        """, (game_type, level, region_x, region_y))

        affected_str = ",".join(str(o) for o in affected_objects) if affected_objects else ""

        if existing:
            row = existing[0]
            old_conf = row['confidence']
            count = row['discovery_count']
            new_count = count + 1
            new_conf = (old_conf * count + confidence) / new_count

            self.db.execute_query("""
                UPDATE pseudo_button_behavior
                SET produces_action = ?,
                    movement_direction = ?,
                    affected_objects = ?,
                    effect_description = ?,
                    confidence = ?,
                    discovery_count = ?,
                    last_observed = CURRENT_TIMESTAMP
                WHERE game_type = ? AND level_number = ? AND region_x = ? AND region_y = ?
            """, (produces_action, movement_direction, affected_str, effect_description,
                  new_conf, new_count, game_type, level, region_x, region_y))

            logger.debug(
                f"[BUTTON] Updated region ({region_x},{region_y}) for "
                f"{game_type} L{level}: {produces_action}"
            )
        else:
            self.db.execute_query("""
                INSERT INTO pseudo_button_behavior
                (game_type, level_number, region_x, region_y, produces_action,
                 movement_direction, affected_objects, effect_description, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (game_type, level, region_x, region_y, produces_action,
                  movement_direction, affected_str, effect_description, confidence))

            logger.info(
                f"[BUTTON] New pseudo button at ({region_x},{region_y}) for "
                f"{game_type} L{level}: {produces_action}"
            )

    def get_pseudo_button_behavior(
        self,
        game_type: str,
        level: int,
        region_x: int,
        region_y: int
    ) -> Optional[Dict]:
        """
        Retrieve known pseudo button behavior for a specific screen region.

        Returns:
            Dict with produces_action, movement_direction, affected_objects, confidence
            or None if no behavior known
        """
        result = self.db.execute_query("""
            SELECT produces_action, movement_direction, affected_objects,
                   effect_description, confidence
            FROM pseudo_button_behavior
            WHERE game_type = ? AND level_number = ? AND region_x = ? AND region_y = ?
        """, (game_type, level, region_x, region_y))

        if result:
            row = result[0]
            return {
                'produces_action': row['produces_action'],
                'movement_direction': row['movement_direction'],
                'affected_objects': row['affected_objects'].split(",")
                    if row['affected_objects'] else [],
                'effect_description': row['effect_description'],
                'confidence': row['confidence']
            }
        return None

    def get_all_pseudo_buttons(
        self,
        game_type: str,
        level: int,
        min_confidence: float = 0.5
    ) -> List[Dict]:
        """
        Get all known pseudo buttons for a game/level.

        Args:
            game_type: Game type to query
            level: Level number
            min_confidence: Minimum confidence threshold

        Returns:
            List of pseudo button dicts with region coords and behavior
        """
        results = self.db.execute_query("""
            SELECT region_x, region_y, produces_action, movement_direction,
                   affected_objects, effect_description, confidence
            FROM pseudo_button_behavior
            WHERE game_type = ? AND level_number = ? AND confidence >= ?
            ORDER BY confidence DESC
        """, (game_type, level, min_confidence))

        buttons = []
        for row in results or []:
            buttons.append({
                'region_x': row['region_x'],
                'region_y': row['region_y'],
                'screen_x_range': (row['region_x'] * 8, row['region_x'] * 8 + 7),
                'screen_y_range': (row['region_y'] * 8, row['region_y'] * 8 + 7),
                'produces_action': row['produces_action'],
                'movement_direction': row['movement_direction'],
                'affected_objects': row['affected_objects'].split(",")
                    if row['affected_objects'] else [],
                'effect_description': row['effect_description'],
                'confidence': row['confidence']
            })
        return buttons

    def classify_pseudo_button_effects(
        self,
        action6_region_effects: Dict,
        game_type: str,
        level: int
    ) -> Dict[Tuple[int, int], str]:
        """
        Classify and save pseudo button behaviors based on tracked effects.

        Analyzes what each screen region does when clicked and saves
        the discoveries to network knowledge.

        Args:
            action6_region_effects: Dict from identify_controlled_objects tracking
            game_type: Game type for storing
            level: Level number

        Returns:
            Dict mapping (region_x, region_y) -> behavior description
        """
        classified = {}

        for region_key, effects in action6_region_effects.items():
            region_x, region_y = region_key

            if effects['total'] < 2:
                continue  # Not enough samples

            # Determine dominant effect
            directions = {
                'up': effects['up'],
                'down': effects['down'],
                'left': effects['left'],
                'right': effects['right']
            }

            max_direction = max(directions.items(), key=lambda x: x[1])
            toggle_count = effects['toggle']
            no_effect_count = effects['no_effect']
            total = effects['total']

            # Determine what this button does
            if no_effect_count > total * 0.7:
                continue  # Mostly no effect - not a useful button

            affected_list = list(effects['affected_objects'])

            if toggle_count > max_direction[1] and toggle_count > total * 0.3:
                produces_action = 'toggle'
                movement_direction = 'none'
                effect_desc = f"Clicking region ({region_x},{region_y}) toggles/spawns objects"
            elif max_direction[1] > total * 0.4:
                produces_action = f'move_{max_direction[0]}'
                movement_direction = max_direction[0]
                effect_desc = f"Clicking region ({region_x},{region_y}) moves objects {max_direction[0]}"
            else:
                produces_action = 'interact'
                movement_direction = 'mixed'
                effect_desc = f"Clicking region ({region_x},{region_y}) has mixed effects"

            confidence = min(0.9, effects['total'] / 10)

            self.save_pseudo_button_behavior(
                game_type=game_type,
                level=level,
                region_x=region_x,
                region_y=region_y,
                produces_action=produces_action,
                movement_direction=movement_direction,
                affected_objects=affected_list,
                effect_description=effect_desc,
                confidence=confidence
            )

            classified[region_key] = produces_action

        return classified

    # =========================================================================
    # OBJECT SELECTION TRACKING
    # =========================================================================

    def track_selection_change(
        self,
        session_id: str,
        game_id: str,
        level: int,
        action_index: int,
        click_x: Optional[int],
        click_y: Optional[int],
        frame_before: Dict
    ) -> Optional[Dict[str, Any]]:
        """
        Track if an ACTION6 click selected a new object for control.

        Args:
            session_id: Current game session
            game_id: Game identifier
            level: Level number
            action_index: Which action in sequence
            click_x, click_y: Where was clicked (0-63 range)
            frame_before: Frame data before action

        Returns:
            Selection info dict if selection detected, None otherwise
        """
        if click_x is None or click_y is None:
            return None

        game_type = game_id.split('-')[0] if '-' in game_id else game_id
        grid = frame_before.get('grid', [])

        if not grid:
            return None

        clicked_object = self._get_object_at_coords(grid, click_x, click_y)

        if clicked_object is None or clicked_object == 0:
            return None  # Clicked on background

        self._update_current_selection(
            session_id=session_id,
            game_id=game_id,
            level=level,
            object_color=clicked_object,
            object_coords=f"({click_x},{click_y})",
            action_index=action_index
        )

        logger.debug(
            f"[SELECTION] Clicked on object color {clicked_object} at ({click_x},{click_y}) "
            f"- may now be selected for control"
        )

        return {
            'selected_object_color': clicked_object,
            'selected_coords': (click_x, click_y),
            'action_index': action_index,
            'game_type': game_type,
            'level': level
        }

    def verify_selection_controls_movement(
        self,
        session_id: str,
        game_id: str,
        level: int,
        movement_action: str,
        frame_before: Dict,
        frame_after: Dict
    ) -> Optional[Dict[str, Any]]:
        """
        Verify if the currently selected object moved in response to ACTION1-4.

        If the previously selected object (via ACTION6) moved when we used
        ACTION1-4, then we've confirmed the selection mechanism.

        Args:
            session_id: Current game session
            game_id: Game identifier
            level: Level number
            movement_action: The action used (ACTION1, ACTION2, etc.)
            frame_before, frame_after: Frame data

        Returns:
            Verification result dict if selection was confirmed, None otherwise
        """
        current_selection = self.get_current_selection(session_id, game_id, level)

        if not current_selection:
            return None

        selected_color = current_selection.get('selected_object_color')
        if selected_color is None:
            return None

        game_type = game_id.split('-')[0] if '-' in game_id else game_id

        grid_before = frame_before.get('grid', [])
        grid_after = frame_after.get('grid', [])

        if not grid_before or not grid_after:
            return None

        objects_before = self._find_objects_in_grid(grid_before)
        objects_after = self._find_objects_in_grid(grid_after)

        if selected_color not in objects_before or selected_color not in objects_after:
            return None

        positions_before = objects_before[selected_color]
        positions_after = objects_after[selected_color]

        cx_before = sum(p[0] for p in positions_before) / len(positions_before)
        cy_before = sum(p[1] for p in positions_before) / len(positions_before)
        cx_after = sum(p[0] for p in positions_after) / len(positions_after)
        cy_after = sum(p[1] for p in positions_after) / len(positions_after)

        dx = cx_after - cx_before
        dy = cy_after - cy_before

        if abs(dx) < 0.5 and abs(dy) < 0.5:
            return None  # Object didn't move

        if abs(dy) > abs(dx):
            movement_direction = 'up' if dy < 0 else 'down'
        else:
            movement_direction = 'left' if dx < 0 else 'right'

        action_to_expected_direction = {
            'ACTION1': 'up', 'action_1': 'up',
            'ACTION2': 'down', 'action_2': 'down',
            'ACTION3': 'left', 'action_3': 'left',
            'ACTION4': 'right', 'action_4': 'right',
        }

        expected = action_to_expected_direction.get(movement_action)
        movement_matches = (expected == movement_direction)

        if movement_matches:
            shape_info = None
            if positions_before:
                xs = [p[0] for p in positions_before]
                ys = [p[1] for p in positions_before]
                bbox_width = max(xs) - min(xs) + 1
                bbox_height = max(ys) - min(ys) + 1
                bbox_area = bbox_width * bbox_height
                density = len(positions_before) / bbox_area if bbox_area > 0 else 1.0
                shape_info = {
                    'width': bbox_width,
                    'height': bbox_height,
                    'density': density
                }

            self._save_selectable_object(
                game_type=game_type,
                level=level,
                object_color=selected_color,
                object_coords=current_selection.get('selected_object_coords'),
                is_moveable=True,
                control_actions=[movement_action],
                confidence=0.8,
                shape_info=shape_info
            )

            logger.info(
                f"[SELECTION CONFIRMED] Object color {selected_color} "
                f"moved {movement_direction} on {movement_action} after selection"
            )

            return {
                'confirmed': True,
                'object_color': selected_color,
                'movement_direction': movement_direction,
                'action_used': movement_action,
                'game_type': game_type,
                'level': level
            }

        return None

    def get_current_selection(
        self,
        session_id: str,
        game_id: str,
        level: int
    ) -> Optional[Dict[str, Any]]:
        """Get the currently selected object for this session/game/level."""
        result = self.db.execute_query("""
            SELECT selected_object_color, selected_object_coords, selection_action_index
            FROM current_selection_tracking
            WHERE session_id = ? AND game_id = ? AND level_number = ?
        """, (session_id, game_id, level))

        if result and result[0]['selected_object_color'] is not None:
            return {
                'selected_object_color': result[0]['selected_object_color'],
                'selected_object_coords': result[0]['selected_object_coords'],
                'selection_action_index': result[0]['selection_action_index']
            }
        return None

    def _update_current_selection(
        self,
        session_id: str,
        game_id: str,
        level: int,
        object_color: int,
        object_coords: str,
        action_index: int
    ) -> None:
        """Update the currently selected object."""
        self.db.execute_query("""
            INSERT OR REPLACE INTO current_selection_tracking
            (session_id, game_id, level_number, selected_object_color,
             selected_object_coords, selection_action_index, selection_time)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (session_id, game_id, level, object_color, object_coords, action_index))

    def clear_selection(self, session_id: str, game_id: str, level: int) -> None:
        """Clear the current selection (e.g., when level ends)."""
        self.db.execute_query("""
            DELETE FROM current_selection_tracking
            WHERE session_id = ? AND game_id = ? AND level_number = ?
        """, (session_id, game_id, level))

    # =========================================================================
    # SHAPE-BASED GENERALIZATION
    # =========================================================================

    def compute_shape_signature(
        self,
        width: int,
        height: int,
        density: float = 1.0
    ) -> str:
        """
        Compute a shape signature from bounding box dimensions.

        Shape signatures allow generalization across colors:
        - "horizontal_bar": width >= 3 * height (wide and thin)
        - "vertical_bar": height >= 3 * width (tall and thin)
        - "square": 0.7 <= aspect <= 1.4 (roughly square)
        - "wide_rect": 1.4 < aspect < 3.0 (moderately wide)
        - "tall_rect": 0.33 < aspect < 0.7 (moderately tall)
        - "blob": density < 0.5 (sparse, non-rectangular)
        - "small": size < 4 pixels (too small to classify)
        """
        if width <= 0 or height <= 0:
            return "unknown"

        if width * height < 4:
            return "small"

        if density < 0.5:
            return "blob"

        aspect = width / height

        if aspect >= 3.0:
            return "horizontal_bar"
        elif aspect <= 0.33:
            return "vertical_bar"
        elif 0.7 <= aspect <= 1.4:
            return "square"
        elif aspect > 1.4:
            return "wide_rect"
        else:
            return "tall_rect"

    def get_selectable_shapes_for_game(
        self,
        game_type: str,
        min_confidence: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        Get all shape signatures that are known to be selectable for a game type.

        This is the KEY method for generalization:
        - Query across ALL levels to find what shapes work
        - Returns shape signatures, not specific colors
        - Agents use this to enumerate objects on frontier levels
        """
        results = self.db.execute_query("""
            SELECT
                shape_signature,
                COUNT(*) as occurrence_count,
                AVG(confidence) as avg_confidence,
                MAX(confidence) as max_confidence,
                GROUP_CONCAT(DISTINCT object_color) as colors_seen
            FROM object_selection_state
            WHERE game_type = ?
                  AND is_selectable = TRUE
                  AND shape_signature IS NOT NULL
                  AND confidence >= ?
            GROUP BY shape_signature
            ORDER BY avg_confidence DESC, occurrence_count DESC
        """, (game_type, min_confidence))

        shapes = []
        for row in results or []:
            if row['shape_signature']:
                shapes.append({
                    'shape_signature': row['shape_signature'],
                    'occurrence_count': row['occurrence_count'],
                    'avg_confidence': row['avg_confidence'],
                    'max_confidence': row['max_confidence'],
                    'colors_seen': row['colors_seen'].split(',') if row['colors_seen'] else []
                })
        return shapes

    def find_objects_matching_shape(
        self,
        frame: List[List[int]],
        target_shapes: List[str],
        exclude_colors: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find all objects in the current frame that match target shape signatures.

        This is used on FRONTIER levels to enumerate all objects the agent
        should TRY clicking, based on shape generalization from previous levels.
        """
        if not frame or not target_shapes:
            return []

        exclude_colors = exclude_colors or [0]

        try:
            import numpy as np
            grid = np.array(frame) if not isinstance(frame, np.ndarray) else frame
        except ImportError:
            # Fallback without numpy
            grid = frame
            height = len(grid)
            width = len(grid[0]) if grid else 0
        else:
            height, width = grid.shape

        visited = [[False] * width for _ in range(height)]
        matching_objects = []

        def flood_fill(start_y, start_x, color):
            """Find connected component of same color."""
            stack = [(start_y, start_x)]
            cells = []

            while stack:
                y, x = stack.pop()
                if y < 0 or y >= height or x < 0 or x >= width:
                    continue
                if visited[y][x]:
                    continue
                cell_val = grid[y][x] if hasattr(grid, '__getitem__') else grid[y][x]
                if cell_val != color:
                    continue

                visited[y][x] = True
                cells.append((y, x))

                stack.extend([(y+1, x), (y-1, x), (y, x+1), (y, x-1)])

            return cells

        for y in range(height):
            for x in range(width):
                if visited[y][x]:
                    continue

                color = int(grid[y][x])
                if color in exclude_colors:
                    visited[y][x] = True
                    continue

                cells = flood_fill(y, x, color)

                if len(cells) < 2:
                    continue

                rows = [c[0] for c in cells]
                cols = [c[1] for c in cells]
                min_row, max_row = min(rows), max(rows)
                min_col, max_col = min(cols), max(cols)

                bbox_width = max_col - min_col + 1
                bbox_height = max_row - min_row + 1
                bbox_area = bbox_width * bbox_height
                density = len(cells) / bbox_area if bbox_area > 0 else 0

                shape_sig = self.compute_shape_signature(bbox_width, bbox_height, density)

                if shape_sig in target_shapes:
                    center_y = sum(rows) // len(rows)
                    center_x = sum(cols) // len(cols)

                    matching_objects.append({
                        'color': color,
                        'shape_signature': shape_sig,
                        'center': (center_x, center_y),
                        'bounding_box': {
                            'left': min_col,
                            'top': min_row,
                            'width': bbox_width,
                            'height': bbox_height
                        },
                        'size': len(cells),
                        'density': density
                    })

        return matching_objects

    def get_untried_objects_for_frontier(
        self,
        game_type: str,
        level: int,
        frame: List[List[int]],
        tried_colors: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get objects the agent should try clicking on a frontier level.

        This is the main entry point for frontier exploration with shape generalization.
        """
        tried_colors = tried_colors or []

        selectable_shapes = self.get_selectable_shapes_for_game(game_type, min_confidence=0.5)

        if not selectable_shapes:
            logger.debug(f"[SHAPE] No selectable shapes known for {game_type}")
            return []

        target_shapes = [s['shape_signature'] for s in selectable_shapes]
        logger.info(f"[SHAPE] {game_type} known selectable shapes: {target_shapes}")

        exclude = [0] + tried_colors
        matching = self.find_objects_matching_shape(frame, target_shapes, exclude)

        if not matching:
            return []

        shape_confidence = {s['shape_signature']: s['avg_confidence'] for s in selectable_shapes}

        for obj in matching:
            obj['shape_confidence'] = shape_confidence.get(obj['shape_signature'], 0.5)

        matching.sort(key=lambda x: x['shape_confidence'], reverse=True)

        logger.info(
            f"[SHAPE] Found {len(matching)} objects to try on {game_type} L{level}: "
            f"{[(o['color'], o['shape_signature']) for o in matching[:5]]}"
        )

        return matching

    def get_selectable_objects(
        self,
        game_type: str,
        level: int,
        min_confidence: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Get all known selectable objects for a game/level."""
        results = self.db.execute_query("""
            SELECT object_color, object_coordinates, is_moveable,
                   control_actions, confidence
            FROM object_selection_state
            WHERE game_type = ? AND level_number = ?
                  AND is_selectable = TRUE AND confidence >= ?
            ORDER BY confidence DESC
        """, (game_type, level, min_confidence))

        objects = []
        for row in results or []:
            objects.append({
                'object_color': row['object_color'],
                'coordinates': row['object_coordinates'],
                'is_moveable': bool(row['is_moveable']),
                'control_actions': json.loads(row['control_actions'] or '[]'),
                'confidence': row['confidence']
            })
        return objects

    def _save_selectable_object(
        self,
        game_type: str,
        level: int,
        object_color: int,
        object_coords: Optional[str],
        is_moveable: bool,
        control_actions: List[str],
        confidence: float,
        shape_info: Optional[Dict[str, Any]] = None
    ) -> None:
        """Save a discovered selectable object to network knowledge."""
        shape_signature = None
        shape_width = None
        shape_height = None
        shape_density = None

        if shape_info:
            shape_width = shape_info.get('width')
            shape_height = shape_info.get('height')
            shape_density = shape_info.get('density', 1.0)

            if shape_width and shape_height:
                shape_signature = self.compute_shape_signature(
                    shape_width, shape_height, shape_density
                )

        existing = self.db.execute_query("""
            SELECT discovery_count, confidence, control_actions
            FROM object_selection_state
            WHERE game_type = ? AND level_number = ? AND object_color = ?
        """, (game_type, level, object_color))

        if existing:
            old_count = existing[0]['discovery_count']
            old_confidence = existing[0]['confidence']
            old_actions = json.loads(existing[0]['control_actions'] or '[]')

            merged_actions = list(set(old_actions + control_actions))
            new_confidence = (old_confidence * old_count + confidence) / (old_count + 1)

            if shape_signature:
                self.db.execute_query("""
                    UPDATE object_selection_state
                    SET is_selectable = TRUE,
                        is_moveable = ?,
                        object_coordinates = COALESCE(?, object_coordinates),
                        control_actions = ?,
                        confidence = ?,
                        discovery_count = discovery_count + 1,
                        last_observed = CURRENT_TIMESTAMP,
                        shape_signature = COALESCE(?, shape_signature),
                        shape_width = COALESCE(?, shape_width),
                        shape_height = COALESCE(?, shape_height),
                        shape_density = COALESCE(?, shape_density)
                    WHERE game_type = ? AND level_number = ? AND object_color = ?
                """, (is_moveable, object_coords, json.dumps(merged_actions),
                      new_confidence, shape_signature, shape_width, shape_height,
                      shape_density, game_type, level, object_color))
            else:
                self.db.execute_query("""
                    UPDATE object_selection_state
                    SET is_selectable = TRUE,
                        is_moveable = ?,
                        object_coordinates = COALESCE(?, object_coordinates),
                        control_actions = ?,
                        confidence = ?,
                        discovery_count = discovery_count + 1,
                        last_observed = CURRENT_TIMESTAMP
                    WHERE game_type = ? AND level_number = ? AND object_color = ?
                """, (is_moveable, object_coords, json.dumps(merged_actions),
                      new_confidence, game_type, level, object_color))
        else:
            self.db.execute_query("""
                INSERT INTO object_selection_state
                (game_type, level_number, object_color, object_coordinates,
                 is_selectable, is_moveable, is_button, control_actions, confidence,
                 shape_signature, shape_width, shape_height, shape_density)
                VALUES (?, ?, ?, ?, TRUE, ?, FALSE, ?, ?, ?, ?, ?, ?)
            """, (game_type, level, object_color, object_coords,
                  is_moveable, json.dumps(control_actions), confidence,
                  shape_signature, shape_width, shape_height, shape_density))

        shape_msg = f" shape={shape_signature}" if shape_signature else ""
        logger.info(
            f"[NETWORK] Saved selectable object: {game_type} L{level} "
            f"color={object_color} moveable={is_moveable}{shape_msg}"
        )

    # =========================================================================
    # ACTION6 AVAILABILITY TRACKING
    # =========================================================================

    def track_action6_availability(
        self,
        agent_id: str,
        game_id: str,
        level: int,
        action_number: int,
        available_actions: List[str],
        previous_action: Optional[str] = None,
        previous_action_coords: Optional[str] = None,
        grid: Optional[List] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Track when ACTION6 becomes available or unavailable.

        This is called after every action to detect availability changes.
        When ACTION6 appears/disappears, it signals a change in selectability state.
        """
        action6_available = 1 if 'ACTION6' in available_actions or 'action_6' in available_actions else 0

        grid_hash = None
        if grid:
            grid_str = str(grid)
            grid_hash = hashlib.md5(grid_str.encode()).hexdigest()[:16]

        self.db.execute_query("""
            INSERT INTO action6_availability_events
            (agent_id, game_id, level_number, action_number, action6_available,
             previous_action, previous_action_coords, grid_hash, available_actions_list)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (agent_id, game_id, level, action_number, action6_available,
              previous_action, previous_action_coords, grid_hash,
              json.dumps(available_actions)))

        return {
            'action6_available': bool(action6_available),
            'action_number': action_number,
            'previous_action': previous_action,
            'grid_hash': grid_hash
        }

    def detect_action6_state_change(
        self,
        agent_id: str,
        game_id: str,
        level: int
    ) -> List[Dict[str, Any]]:
        """
        Analyze action history to detect when ACTION6 availability changed.

        Returns list of state change events with context about what triggered them.
        """
        results = self.db.execute_query("""
            SELECT action_number, action6_available, previous_action,
                   previous_action_coords, grid_hash
            FROM action6_availability_events
            WHERE agent_id = ? AND game_id = ? AND level_number = ?
            ORDER BY action_number ASC
        """, (agent_id, game_id, level))

        if not results or len(results) < 2:
            return []

        state_changes = []
        prev_available = results[0]['action6_available']

        for row in results[1:]:
            current_available = row['action6_available']

            if current_available != prev_available:
                game_type = game_id.split('-')[0] if '-' in game_id else game_id

                state_changes.append({
                    'action_number': row['action_number'],
                    'became_available': current_available == 1,
                    'trigger_action': row['previous_action'],
                    'trigger_coords': row['previous_action_coords'],
                    'grid_hash': row['grid_hash']
                })

                self._save_selectability_condition(
                    game_type=game_type,
                    level=level,
                    trigger_action=row['previous_action'],
                    trigger_coords=row['previous_action_coords'],
                    action6_became_available=current_available
                )

            prev_available = current_available

        return state_changes

    def _save_selectability_condition(
        self,
        game_type: str,
        level: int,
        trigger_action: Optional[str],
        trigger_coords: Optional[str],
        action6_became_available: int
    ) -> None:
        """Save a discovered selectability condition to network knowledge."""
        if not trigger_action:
            return

        existing = self.db.execute_query("""
            SELECT condition_id, occurrence_count, confidence
            FROM selectability_conditions
            WHERE game_type = ? AND level_number = ?
                  AND trigger_action = ? AND COALESCE(trigger_coords, '') = COALESCE(?, '')
                  AND action6_became_available = ?
        """, (game_type, level, trigger_action, trigger_coords or '', action6_became_available))

        if existing:
            old_count = existing[0]['occurrence_count']
            new_confidence = min(0.95, 0.5 + (old_count * 0.1))

            self.db.execute_query("""
                UPDATE selectability_conditions
                SET occurrence_count = occurrence_count + 1,
                    confidence = ?,
                    last_observed = CURRENT_TIMESTAMP
                WHERE condition_id = ?
            """, (new_confidence, existing[0]['condition_id']))
        else:
            desc = f"{trigger_action}"
            if trigger_coords:
                desc += f" at {trigger_coords}"
            desc += f" -> ACTION6 {'appears' if action6_became_available else 'disappears'}"

            self.db.execute_query("""
                INSERT OR IGNORE INTO selectability_conditions
                (game_type, level_number, trigger_action, trigger_coords,
                 trigger_description, action6_became_available, confidence)
                VALUES (?, ?, ?, ?, ?, ?, 0.5)
            """, (game_type, level, trigger_action, trigger_coords, desc, action6_became_available))

        logger.debug(
            f"[SELECTABILITY] Learned: {trigger_action} "
            f"{'enables' if action6_became_available else 'disables'} ACTION6 in {game_type} L{level}"
        )

    def get_selectability_triggers(
        self,
        game_type: str,
        level: int,
        want_available: bool = True,
        min_confidence: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Get known conditions that make ACTION6 available/unavailable.

        Args:
            game_type: Game type to query
            level: Level number
            want_available: If True, get conditions that ENABLE ACTION6
            min_confidence: Minimum confidence threshold
        """
        target = 1 if want_available else 0

        results = self.db.execute_query("""
            SELECT trigger_action, trigger_coords, trigger_description,
                   occurrence_count, confidence
            FROM selectability_conditions
            WHERE game_type = ? AND level_number = ?
                  AND action6_became_available = ? AND confidence >= ?
            ORDER BY confidence DESC
        """, (game_type, level, target, min_confidence))

        return [
            {
                'trigger_action': row['trigger_action'],
                'trigger_coords': row['trigger_coords'],
                'description': row['trigger_description'],
                'occurrence_count': row['occurrence_count'],
                'confidence': row['confidence']
            }
            for row in (results or [])
        ]

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _get_object_at_coords(self, grid: List, x: int, y: int) -> Optional[int]:
        """Get the object color at specific coordinates."""
        if not grid:
            return None

        if 0 <= y < len(grid) and 0 <= x < len(grid[0] if grid else []):
            return grid[y][x]
        return None

    def _find_objects_in_grid(self, grid: List) -> Dict[int, List[Tuple[int, int]]]:
        """
        Find all distinct objects in a grid by color/value.

        Returns dict mapping object_id (color value) -> list of (x, y) positions.
        """
        objects = {}

        if not grid:
            return objects

        height = len(grid)
        width = len(grid[0]) if grid else 0
        total_cells = height * width

        for y, row in enumerate(grid):
            for x, cell in enumerate(row):
                if cell == 0:
                    continue
                if cell not in objects:
                    objects[cell] = []
                objects[cell].append((x, y))

        # Filter out "background" colors that cover >50% of non-zero cells
        filtered = {}
        for color, positions in objects.items():
            if len(positions) < total_cells * 0.5:
                filtered[color] = positions

        return filtered


__all__ = ['Action6BehaviorEngine']
