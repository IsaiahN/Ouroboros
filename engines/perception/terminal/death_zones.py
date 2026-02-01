import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
Death Zones - Spatial Danger Region Tracking
=============================================

Tracks WHERE on the grid game-overs happen. More intuitive than action patterns:
"objects in region X,Y = danger"

Dynamic zones: Enemies may move, so zones can shift or be temporary.
Zones decay over time if not re-validated.

Tables used:
- death_zones: Spatial bounding boxes with danger scores
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


class DeathZoneTracker:
    """
    Tracks spatial danger regions (death zones) per level.

    A death zone is a bounding box where deaths have occurred.
    Zones have danger scores that increase with deaths and
    decay with survivals or time.
    """

    def __init__(self, db: DatabaseInterface):
        self.db = db

    def record_death_zone(self,
                          game_type: str,
                          level_number: int,
                          frame_before_death: List[List[int]],
                          controlled_objects: Optional[List[Dict]] = None) -> Optional[str]:
        """
        Record a death zone when game_over occurs.

        Analyzes the frame to find where controlled objects were located
        and marks that region as a danger zone.

        Args:
            game_type: Game type (e.g., 'as66', 'sp80')
            level_number: Level where death occurred
            frame_before_death: Frame state before game_over
            controlled_objects: List of objects the agent was controlling

        Returns:
            zone_id if recorded, None if failed
        """
        try:
            if not frame_before_death:
                return None

            # Find non-background objects in frame that might be player-controlled
            death_positions = []
            death_colors = set()

            height = len(frame_before_death)
            width = len(frame_before_death[0]) if frame_before_death else 0

            # If controlled objects provided, use those positions
            if controlled_objects:
                for obj in controlled_objects:
                    if 'x' in obj and 'y' in obj:
                        death_positions.append((obj['x'], obj['y']))
                        if 'color' in obj:
                            death_colors.add(obj['color'])
            else:
                # Auto-detect: Find rare colors (likely player-controlled)
                color_counts = {}
                for y, row in enumerate(frame_before_death):
                    for x, color in enumerate(row):
                        if color != 0:  # Skip background
                            color_counts[color] = color_counts.get(color, 0) + 1

                if color_counts:
                    # Find rarest non-zero color (likely player)
                    min_count = min(color_counts.values())
                    rare_colors = [c for c, cnt in color_counts.items() if cnt <= min_count * 2]

                    # Record positions of rare colors
                    for y, row in enumerate(frame_before_death):
                        for x, color in enumerate(row):
                            if color in rare_colors:
                                death_positions.append((x, y))
                                death_colors.add(color)

            if not death_positions:
                return None

            # Calculate bounding box of death positions
            x_coords = [p[0] for p in death_positions]
            y_coords = [p[1] for p in death_positions]

            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)

            # Expand zone slightly for margin
            x_min = max(0, x_min - 1)
            x_max = min(width - 1, x_max + 1)
            y_min = max(0, y_min - 1)
            y_max = min(height - 1, y_max + 1)

            # Check for existing overlapping zone
            zone_signature = f"{x_min}-{x_max}-{y_min}-{y_max}"
            zone_id = f"dz_{game_type}_{level_number}_{hashlib.md5(zone_signature.encode()).hexdigest()[:8]}"

            existing = self.db.execute_query("""
                SELECT zone_id, death_count FROM death_zones
                WHERE game_type = ? AND level_number = ?
                  AND x_min = ? AND x_max = ? AND y_min = ? AND y_max = ?
                  AND is_active = 1
            """, (game_type, level_number, x_min, x_max, y_min, y_max))

            now = datetime.now().isoformat()

            if existing:
                # Update existing zone
                self.db.execute_query("""
                    UPDATE death_zones
                    SET death_count = death_count + 1,
                        danger_score = CAST(death_count + 1 AS REAL) /
                                       CAST(death_count + 1 + survival_count AS REAL),
                        last_death_at = ?
                    WHERE zone_id = ?
                """, (now, existing[0]['zone_id']))

                logger.info(f"[DEATH-ZONE] Updated zone {existing[0]['zone_id'][:12]} "
                           f"(deaths: {existing[0]['death_count'] + 1})")
                return existing[0]['zone_id']

            # Create new zone
            self.db.execute_query("""
                INSERT INTO death_zones (
                    zone_id, game_type, level_number,
                    x_min, x_max, y_min, y_max,
                    death_colors, object_signature,
                    death_count, survival_count, danger_score,
                    discovered_at, last_death_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0, 0.7, ?, ?, 1)
            """, (
                zone_id, game_type, level_number,
                x_min, x_max, y_min, y_max,
                json.dumps(list(death_colors)),
                hashlib.md5(str(sorted(death_positions)).encode()).hexdigest()[:12],
                now, now
            ))

            logger.info(f"[DEATH-ZONE] New zone recorded: {zone_id} at ({x_min},{y_min})-({x_max},{y_max})")
            return zone_id

        except Exception as e:
            logger.debug(f"Error recording death zone: {e}")
            return None

    def check_death_zones(self,
                          game_type: str,
                          level_number: int,
                          object_positions: List[Tuple[int, int]],
                          planned_direction: Optional[int] = None,
                          min_danger: float = 0.6) -> Optional[Dict[str, Any]]:
        """
        Check if objects are in or approaching death zones.

        Args:
            game_type: Current game type
            level_number: Current level
            object_positions: List of (x, y) positions of controlled objects
            planned_direction: Movement direction (1=up, 2=down, 3=right, 4=left)
            min_danger: Minimum danger_score to trigger warning

        Returns:
            None if safe, or Dict with danger info
        """
        try:
            if not object_positions:
                return None

            # Get death zones for this level
            zones = self.db.execute_query("""
                SELECT zone_id, x_min, x_max, y_min, y_max,
                       death_count, danger_score
                FROM death_zones
                WHERE game_type = ? AND level_number = ?
                  AND danger_score >= ? AND is_active = 1
                ORDER BY danger_score DESC
            """, (game_type, level_number, min_danger))

            if not zones:
                return None

            # Direction offsets for movement prediction
            direction_offset = {
                1: (0, -1),   # UP
                2: (0, 1),    # DOWN
                3: (1, 0),    # RIGHT
                4: (-1, 0)    # LEFT
            }

            for x, y in object_positions:
                for zone in zones:
                    # Check if currently IN zone
                    in_zone = (zone['x_min'] <= x <= zone['x_max'] and
                              zone['y_min'] <= y <= zone['y_max'])

                    # Check if MOVING INTO zone
                    moving_into_zone = False
                    if planned_direction and planned_direction in direction_offset:
                        dx, dy = direction_offset[planned_direction]
                        next_x, next_y = x + dx, y + dy
                        moving_into_zone = (zone['x_min'] <= next_x <= zone['x_max'] and
                                           zone['y_min'] <= next_y <= zone['y_max'])

                    if in_zone or moving_into_zone:
                        # Find safe direction (opposite of danger)
                        safe_direction = self._find_safe_direction(
                            x, y, zone, planned_direction
                        )

                        return {
                            'warning': True,
                            'zone_id': zone['zone_id'],
                            'zone_coords': f"({zone['x_min']},{zone['y_min']})-({zone['x_max']},{zone['y_max']})",
                            'danger_score': zone['danger_score'],
                            'death_count': zone['death_count'],
                            'current_position': (x, y),
                            'in_zone': in_zone,
                            'moving_into_zone': moving_into_zone,
                            'safe_direction': safe_direction,
                            'reason': f"Death zone at ({zone['x_min']},{zone['y_min']})-({zone['x_max']},{zone['y_max']}) "
                                     f"({zone['death_count']} deaths)"
                        }

            return None

        except Exception as e:
            logger.debug(f"Death zone check failed: {e}")
            return None

    def _find_safe_direction(self, x: int, y: int, zone: Dict,
                             avoid_direction: Optional[int] = None) -> int:
        """Find a direction that moves away from the death zone."""
        # Calculate center of death zone
        zone_center_x = (zone['x_min'] + zone['x_max']) / 2
        zone_center_y = (zone['y_min'] + zone['y_max']) / 2

        # Move away from zone center
        dx = x - zone_center_x
        dy = y - zone_center_y

        # Prioritize movement based on distance from zone
        if abs(dx) > abs(dy):
            # Move horizontally
            safe = 3 if dx > 0 else 4  # RIGHT or LEFT
        else:
            # Move vertically
            safe = 2 if dy > 0 else 1  # DOWN or UP

        # If safe direction is same as avoid, try perpendicular
        if safe == avoid_direction:
            if safe in [1, 2]:  # Was vertical, try horizontal
                safe = 3 if dx >= 0 else 4
            else:  # Was horizontal, try vertical
                safe = 2 if dy >= 0 else 1

        return safe

    def record_zone_survival(self, game_type: str, level_number: int,
                             positions: List[Tuple[int, int]]):
        """Record when objects pass through a death zone safely."""
        try:
            zones = self.db.execute_query("""
                SELECT zone_id, x_min, x_max, y_min, y_max
                FROM death_zones
                WHERE game_type = ? AND level_number = ? AND is_active = 1
            """, (game_type, level_number))

            for x, y in positions:
                for zone in zones:
                    if (zone['x_min'] <= x <= zone['x_max'] and
                        zone['y_min'] <= y <= zone['y_max']):
                        # Object survived in zone - reduce danger score
                        self.db.execute_query("""
                            UPDATE death_zones
                            SET survival_count = survival_count + 1,
                                danger_score = CAST(death_count AS REAL) /
                                               CAST(death_count + survival_count + 1 AS REAL)
                            WHERE zone_id = ?
                        """, (zone['zone_id'],))
        except Exception:
            pass

    def should_challenge_zone(self, zone: Dict, generation: int) -> bool:
        """
        Determine if a death zone should be challenged/tested.

        Death zones might be temporary (enemy moved) or wrong (false positive).
        Agents should occasionally test old zones to see if they're still dangerous.

        Challenge criteria:
        1. Zone has high survival count relative to deaths (might be stale)
        2. Zone hasn't been validated recently (many generations since last death)
        3. Random exploration chance for high-performing agents

        Args:
            zone: Death zone dict with death_count, survival_count, etc.
            generation: Current generation number

        Returns:
            True if zone should be tested, False to avoid
        """
        death_count = zone.get('death_count', 1)
        survival_count = zone.get('survival_count', 0)
        danger_score = zone.get('danger_score', 0.7)

        # If survival count is high, zone might be stale
        if survival_count > death_count * 2 and danger_score < 0.5:
            return True

        # If danger score has decayed significantly, worth testing
        if danger_score < 0.4:
            return True

        # Occasionally challenge even "dangerous" zones (10% for low danger, 2% for high)
        import random
        challenge_chance = 0.02 if danger_score > 0.6 else 0.10
        if random.random() < challenge_chance:
            return True

        return False

    def record_zone_challenge(self, zone_id: str, survived: bool, generation: int):
        """
        Record the result of deliberately challenging a death zone.

        Args:
            zone_id: Zone that was tested
            survived: True if agent survived the zone, False if died
            generation: Current generation
        """
        try:
            now = datetime.now().isoformat()

            if survived:
                # Zone is less dangerous than believed
                self.db.execute_query("""
                    UPDATE death_zones
                    SET survival_count = survival_count + 1,
                        challenge_count = challenge_count + 1,
                        last_challenged_at = ?,
                        danger_score = CAST(death_count AS REAL) /
                                       CAST(death_count + survival_count + 1 AS REAL)
                    WHERE zone_id = ?
                """, (now, zone_id))
                logger.info(f"[CHALLENGE] Zone {zone_id[:12]} survived! Danger score reduced.")
            else:
                # Zone confirmed dangerous
                self.db.execute_query("""
                    UPDATE death_zones
                    SET death_count = death_count + 1,
                        challenge_count = challenge_count + 1,
                        last_challenged_at = ?,
                        last_validated_at = ?,
                        generations_since_death = 0,
                        danger_score = MIN(0.95, danger_score + 0.1)
                    WHERE zone_id = ?
                """, (now, now, zone_id))
                logger.info(f"[CHALLENGE] Zone {zone_id[:12]} still lethal! Danger confirmed.")
        except Exception as e:
            logger.debug(f"Error recording zone challenge: {e}")

    def decay_old_zones(self, generations_threshold: int = 10):
        """
        Decay danger scores for zones that haven't killed anyone recently.

        If a zone hasn't caused a death in N generations, it might have
        been a temporary danger (moving enemy) or the game changed.

        Call this once per generation during evolution.
        """
        try:
            # Increment generations_since_death for all zones
            self.db.execute_query("""
                UPDATE death_zones
                SET generations_since_death = generations_since_death + 1
                WHERE is_active = 1
            """)

            # Decay danger score for old zones
            self.db.execute_query("""
                UPDATE death_zones
                SET danger_score = MAX(0.2, danger_score - 0.05)
                WHERE generations_since_death >= ?
                  AND is_active = 1
                  AND danger_score > 0.2
            """, (generations_threshold,))

            # Deactivate zones that have very low danger scores
            deactivated = self.db.execute_query("""
                UPDATE death_zones
                SET is_active = 0
                WHERE danger_score < 0.2
                  AND survival_count > death_count * 3
                  AND is_active = 1
                RETURNING zone_id
            """)

            if deactivated:
                logger.info(f"[DECAY] Deactivated {len(deactivated)} stale death zones")

        except Exception as e:
            logger.debug(f"Error decaying zones: {e}")

    def get_level_death_zones(self, game_type: str, level_number: int) -> List[Dict]:
        """Get all active death zones for a level."""
        try:
            zones = self.db.execute_query("""
                SELECT zone_id, x_min, x_max, y_min, y_max,
                       death_count, danger_score, death_colors
                FROM death_zones
                WHERE game_type = ? AND level_number = ? AND is_active = 1
                ORDER BY danger_score DESC
            """, (game_type, level_number))

            return zones or []
        except Exception:
            return []
