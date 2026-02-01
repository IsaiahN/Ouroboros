import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
Dangerous Objects - Pattern-Based Danger Detection
===================================================

Tracks WHAT (color/shape) killed the agent, not just WHERE.
If red enemy at (15,23) kills you, ALL red enemies become suspect.

Key insight: Color-based danger propagation allows learning
"avoid red things" rather than just "avoid position (15,23)".

Tables used:
- dangerous_objects: Color/pattern danger tracking
- action_triggered_dangers: Actions that spawn threats
"""

import json
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


class DangerousObjectTracker:
    """
    Tracks dangerous objects by color/pattern.
    
    When an agent dies near a colored object, that color
    is marked as dangerous. This propagates to all instances
    of that color on the grid.
    """
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
        
    def record_dangerous_object(self,
                                 game_type: str,
                                 level_number: int,
                                 frame_before_death: List[List[int]],
                                 controlled_objects: List[Dict],
                                 fatal_action: int) -> Optional[str]:
        """
        Identify and record the OBJECT (by color/pattern) that killed the agent.
        
        If blue dot touched red enemy and died, record "red = dangerous".
        Then find ALL red objects on the grid and mark them as suspected dangers.
        
        Args:
            game_type: Game type
            level_number: Level where death occurred
            frame_before_death: Frame state before death
            controlled_objects: Player's objects (to identify player color)
            fatal_action: Action that caused death
            
        Returns:
            object_id if recorded
        """
        try:
            if not frame_before_death or not controlled_objects:
                return None
            
            # Get player position and color
            player_positions = []
            player_color = None
            for obj in controlled_objects:
                if 'x' in obj and 'y' in obj:
                    player_positions.append((obj['x'], obj['y']))
                if 'color' in obj and player_color is None:
                    player_color = obj['color']
            
            if not player_positions:
                return None
            
            # Find what the player was ADJACENT to when they died
            height = len(frame_before_death)
            width = len(frame_before_death[0]) if frame_before_death else 0
            
            adjacent_colors = set()
            for px, py in player_positions:
                # Check all 8 neighbors
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = px + dx, py + dy
                        if 0 <= nx < width and 0 <= ny < height:
                            neighbor_color = frame_before_death[ny][nx]
                            if neighbor_color != 0 and neighbor_color != player_color:
                                adjacent_colors.add(neighbor_color)
            
            if not adjacent_colors:
                return None
            
            now = datetime.now().isoformat()
            recorded_ids = []
            
            for danger_color in adjacent_colors:
                object_id = f"dobj_{game_type}_{level_number}_{danger_color}"
                
                # Check if already known
                existing = self.db.execute_query("""
                    SELECT object_id, kill_count FROM dangerous_objects
                    WHERE game_type = ? AND level_number = ? AND object_color = ?
                """, (game_type, level_number, danger_color))
                
                if existing:
                    # Increment kill count
                    self.db.execute_query("""
                        UPDATE dangerous_objects
                        SET kill_count = kill_count + 1,
                            danger_score = MIN(0.95, danger_score + 0.05),
                            last_kill_at = ?
                        WHERE object_id = ?
                    """, (now, existing[0]['object_id']))
                    recorded_ids.append(existing[0]['object_id'])
                else:
                    # Count how many of this color exist on the grid
                    color_count = sum(1 for row in frame_before_death 
                                     for c in row if c == danger_color)
                    
                    self.db.execute_query("""
                        INSERT INTO dangerous_objects (
                            object_id, game_type, level_number,
                            object_color, object_size, fatal_action, player_color,
                            kill_count, danger_score, discovered_at, last_kill_at, is_active
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, 0.8, ?, ?, 1)
                    """, (
                        object_id, game_type, level_number,
                        danger_color, color_count, fatal_action, player_color,
                        now, now
                    ))
                    recorded_ids.append(object_id)
                    
                    logger.info(f"[DANGER-OBJ] Color {danger_color} marked dangerous "
                               f"({color_count} instances on grid)")
            
            # Now propagate: Find all locations of dangerous colors and create suspected zones
            self._propagate_danger_to_similar_objects(
                game_type, level_number, frame_before_death, adjacent_colors
            )
            
            return recorded_ids[0] if recorded_ids else None
            
        except Exception as e:
            logger.debug(f"Error recording dangerous object: {e}")
            return None
    
    def _propagate_danger_to_similar_objects(self,
                                              game_type: str,
                                              level_number: int,
                                              frame: List[List[int]],
                                              danger_colors: set):
        """
        Find all instances of dangerous colors and create suspected death zones.
        
        If red killed us at (15,23), mark ALL red objects as suspected dangers.
        These are "soft" zones that can be quickly invalidated if proven safe.
        """
        try:
            height = len(frame)
            width = len(frame[0]) if frame else 0
            
            # Find all positions of dangerous colors
            danger_positions = []
            for y, row in enumerate(frame):
                for x, color in enumerate(row):
                    if color in danger_colors:
                        danger_positions.append((x, y, color))
            
            if not danger_positions:
                return
            
            now = datetime.now().isoformat()
            suspected_count = 0
            
            # Group nearby positions into zones (cluster detection)
            # Simple approach: create zones around each dangerous object
            for x, y, color in danger_positions:
                # Create a small zone around each dangerous object
                zone_id = f"susp_{game_type}_{level_number}_{x}_{y}"
                
                # Check if zone already exists
                existing = self.db.execute_query("""
                    SELECT zone_id FROM death_zones
                    WHERE game_type = ? AND level_number = ?
                      AND x_min <= ? AND x_max >= ? AND y_min <= ? AND y_max >= ?
                """, (game_type, level_number, x, x, y, y))
                
                if not existing:
                    # Create a suspected zone with lower initial danger score
                    # Expand by 1 in each direction to account for contact
                    x_min = max(0, x - 1)
                    x_max = min(width - 1, x + 1)
                    y_min = max(0, y - 1)
                    y_max = min(height - 1, y + 1)
                    
                    self.db.execute_query("""
                        INSERT OR IGNORE INTO death_zones (
                            zone_id, game_type, level_number,
                            x_min, x_max, y_min, y_max,
                            death_colors, death_count, survival_count, danger_score,
                            discovered_at, last_death_at, is_active
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0.5, ?, ?, 1)
                    """, (
                        zone_id, game_type, level_number,
                        x_min, x_max, y_min, y_max,
                        json.dumps([color]),
                        now, now
                    ))
                    suspected_count += 1
            
            if suspected_count > 0:
                logger.info(f"[PROPAGATE] Created {suspected_count} suspected death zones "
                           f"from dangerous color pattern")
                
                # Update the dangerous_objects record with propagation count
                for color in danger_colors:
                    self.db.execute_query("""
                        UPDATE dangerous_objects
                        SET suspected_instances = ?
                        WHERE game_type = ? AND level_number = ? AND object_color = ?
                    """, (suspected_count, game_type, level_number, color))
                    
        except Exception as e:
            logger.debug(f"Error propagating danger: {e}")
    
    def check_dangerous_objects(self,
                                 game_type: str,
                                 level_number: int,
                                 current_frame: List[List[int]],
                                 object_positions: List[Tuple[int, int]],
                                 planned_action: int) -> Optional[Dict[str, Any]]:
        """
        Check if planned action would bring player into contact with dangerous objects.
        
        This checks by COLOR, not just position - so if any red object is on the
        path, it triggers a warning.
        """
        try:
            if not object_positions or not current_frame:
                return None
            
            # Get known dangerous colors for this level
            dangers = self.db.execute_query("""
                SELECT object_color, danger_score, kill_count
                FROM dangerous_objects
                WHERE game_type = ? AND level_number = ?
                  AND danger_score >= 0.5 AND is_active = 1
            """, (game_type, level_number))
            
            if not dangers:
                return None
            
            danger_colors = {d['object_color']: d for d in dangers}
            
            height = len(current_frame)
            width = len(current_frame[0]) if current_frame else 0
            
            # Direction offsets
            direction_offset = {
                1: (0, -1),   # UP
                2: (0, 1),    # DOWN
                3: (1, 0),    # RIGHT
                4: (-1, 0)    # LEFT
            }
            
            for x, y in object_positions:
                # Check where we'd move to
                if planned_action in direction_offset:
                    dx, dy = direction_offset[planned_action]
                    next_x, next_y = x + dx, y + dy
                    
                    if 0 <= next_x < width and 0 <= next_y < height:
                        next_color = current_frame[next_y][next_x]
                        
                        if next_color in danger_colors:
                            danger_info = danger_colors[next_color]
                            # Find a safe direction
                            safe_dir = self._find_safe_direction_from_color(
                                x, y, current_frame, danger_colors.keys(), planned_action
                            )
                            
                            return {
                                'warning': True,
                                'danger_type': 'dangerous_object',
                                'object_color': next_color,
                                'danger_score': danger_info['danger_score'],
                                'kill_count': danger_info['kill_count'],
                                'next_position': (next_x, next_y),
                                'safe_direction': safe_dir,
                                'reason': f"Color {next_color} has killed {danger_info['kill_count']} times"
                            }
            
            return None
            
        except Exception as e:
            logger.debug(f"Error checking dangerous objects: {e}")
            return None
    
    def _find_safe_direction_from_color(self, x: int, y: int,
                                         frame: List[List[int]],
                                         danger_colors: set,
                                         avoid_direction: int) -> int:
        """Find a direction that doesn't lead to a dangerous color."""
        height = len(frame)
        width = len(frame[0]) if frame else 0
        
        direction_offset = {
            1: (0, -1),   # UP
            2: (0, 1),    # DOWN
            3: (1, 0),    # RIGHT
            4: (-1, 0)    # LEFT
        }
        
        safe_directions = []
        for direction, (dx, dy) in direction_offset.items():
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                if frame[ny][nx] not in danger_colors:
                    safe_directions.append(direction)
        
        # Prefer opposite of avoid_direction
        opposite = {1: 2, 2: 1, 3: 4, 4: 3}
        if opposite.get(avoid_direction) in safe_directions:
            return opposite[avoid_direction]
        
        if safe_directions:
            return safe_directions[0]
        
        return 7  # ACTION7 = UNDO as last resort
    
    def record_action_triggered_danger(self,
                                        game_type: str,
                                        level_number: int,
                                        trigger_action: int,
                                        frame_before: List[List[int]],
                                        frame_after: List[List[int]],
                                        actions_until_death: int,
                                        click_coords: Optional[Tuple[int, int]] = None) -> Optional[str]:
        """
        Record when an action CREATES a dangerous situation.
        
        Compares frames before/after action to detect spawned objects,
        then records the action as potentially dangerous.
        """
        try:
            if not frame_before or not frame_after:
                return None
            
            # Find what NEW things appeared after the action
            spawned_positions = []
            spawned_colors = set()
            
            height = min(len(frame_before), len(frame_after))
            width = min(len(frame_before[0]), len(frame_after[0])) if frame_before and frame_after else 0
            
            for y in range(height):
                for x in range(width):
                    before = frame_before[y][x]
                    after = frame_after[y][x]
                    
                    # New non-background object appeared
                    if before == 0 and after != 0:
                        spawned_positions.append((x, y))
                        spawned_colors.add(after)
                    # Object changed to something new
                    elif before != after and after != 0:
                        spawned_positions.append((x, y))
                        spawned_colors.add(after)
            
            if not spawned_positions:
                return None
            
            now = datetime.now().isoformat()
            trigger_id = f"atd_{game_type}_{level_number}_{trigger_action}_{hashlib.md5(str(spawned_positions[:5]).encode()).hexdigest()[:8]}"
            
            # Check if this trigger pattern already known
            existing = self.db.execute_query("""
                SELECT trigger_id, occurrence_count FROM action_triggered_dangers
                WHERE game_type = ? AND level_number = ? AND trigger_action = ?
            """, (game_type, level_number, trigger_action))
            
            if existing:
                self.db.execute_query("""
                    UPDATE action_triggered_dangers
                    SET occurrence_count = occurrence_count + 1,
                        danger_score = MIN(0.95, danger_score + 0.05)
                    WHERE trigger_id = ?
                """, (existing[0]['trigger_id'],))
                
                logger.info(f"[ACTION-DANGER] ACTION{trigger_action} confirmed dangerous "
                           f"(spawned threats {existing[0]['occurrence_count'] + 1} times)")
                return existing[0]['trigger_id']
            
            # Record new trigger
            self.db.execute_query("""
                INSERT INTO action_triggered_dangers (
                    trigger_id, game_type, level_number,
                    trigger_action, trigger_x, trigger_y,
                    spawned_color, spawned_positions,
                    actions_until_death, occurrence_count, danger_score,
                    discovered_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0.7, ?, 1)
            """, (
                trigger_id, game_type, level_number,
                trigger_action, 
                click_coords[0] if click_coords else None,
                click_coords[1] if click_coords else None,
                list(spawned_colors)[0] if spawned_colors else None,
                json.dumps(spawned_positions[:20]),
                actions_until_death,
                now
            ))
            
            logger.info(f"[ACTION-DANGER] ACTION{trigger_action} spawned {len(spawned_positions)} new objects "
                       f"({actions_until_death} actions before death)")
            
            return trigger_id
            
        except Exception as e:
            logger.debug(f"Error recording action-triggered danger: {e}")
            return None
    
    def get_dangerous_colors(self, game_type: str, level_number: int,
                              min_danger: float = 0.5) -> Dict[int, float]:
        """Get all dangerous colors for a level with their danger scores."""
        try:
            dangers = self.db.execute_query("""
                SELECT object_color, danger_score
                FROM dangerous_objects
                WHERE game_type = ? AND level_number = ?
                  AND danger_score >= ? AND is_active = 1
            """, (game_type, level_number, min_danger))
            
            return {d['object_color']: d['danger_score'] for d in (dangers or [])}
        except Exception:
            return {}
