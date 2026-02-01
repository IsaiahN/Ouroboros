"""
Control Tracker - "I am this object" tracking
==============================================

Tracks which objects the agent controls based on action-movement correlation.

Design Principles:
- EXPLICIT error messages (no silent failures)
- All operations logged at appropriate levels
- Input validation with clear error messages
- Type hints on all public methods

Core Concept:
When agent presses ACTION1 (up) and object X moves up consistently,
we infer: "I control object X" or "I AM object X"
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import logging
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set
from enum import Enum

logger = logging.getLogger(__name__)


class ControlConfidence(Enum):
    """Confidence levels for control detection."""
    UNKNOWN = "unknown"
    SUSPECTED = "suspected"  # 1-2 observations
    LIKELY = "likely"        # 3-5 observations
    CONFIRMED = "confirmed"  # 6+ observations, consistent


@dataclass
class ControlledObject:
    """Represents an object the agent controls."""
    object_id: str  # e.g., "color_5" or "object_at_3_4"
    control_type: str  # "movement", "selection", "toggle"
    confidence: ControlConfidence
    action_map: Dict[str, str]  # ACTION1 -> "up", ACTION2 -> "down", etc.
    observation_count: int = 0
    last_verified_action: int = 0  # Action number when last verified
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'object_id': self.object_id,
            'control_type': self.control_type,
            'confidence': self.confidence.value,
            'action_map': self.action_map,
            'observation_count': self.observation_count,
            'last_verified_action': self.last_verified_action,
        }


@dataclass 
class ControlObservation:
    """A single observation of action -> movement correlation."""
    action: str
    object_id: str
    movement_direction: Optional[str]  # up/down/left/right/none
    position_before: Tuple[int, int]
    position_after: Tuple[int, int]
    action_number: int
    
    @property
    def moved(self) -> bool:
        return self.position_before != self.position_after


class ControlTracker:
    """
    Tracks which objects the agent controls.
    
    Usage:
        tracker = ControlTracker(db_path)
        
        # Record observation
        tracker.record_observation(
            game_id="sp80-abc",
            level=1,
            action="ACTION1",
            frame_before=[[...]],
            frame_after=[[...]],
            action_number=5
        )
        
        # Get controlled objects
        controlled = tracker.get_controlled_objects(game_id, level)
        for obj in controlled:
            print(f"Control {obj.object_id} via {obj.action_map}")
    """
    
    def __init__(self, db_path: str = "core_data.db"):
        """
        Initialize control tracker.
        
        Args:
            db_path: Path to database
            
        Raises:
            RuntimeError: If database connection fails
        """
        try:
            from database_interface import DatabaseInterface
            self.db = DatabaseInterface(db_path)
        except Exception as e:
            raise RuntimeError(f"[CONTROL_TRACKER] Failed to connect to database: {e}")
        
        self._observations: Dict[str, List[ControlObservation]] = {}  # game_level -> observations
        self._ensure_tables()
        logger.info("[CONTROL_TRACKER] Initialized")
    
    def _ensure_tables(self) -> None:
        """Ensure required tables exist."""
        try:
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS control_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_type TEXT NOT NULL,
                    level INTEGER NOT NULL,
                    object_id TEXT NOT NULL,
                    control_type TEXT NOT NULL,
                    confidence TEXT NOT NULL,
                    action_map TEXT NOT NULL,
                    observation_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(game_type, level, object_id)
                )
            """)
            logger.debug("[CONTROL_TRACKER] Tables verified")
        except Exception as e:
            logger.error(f"[CONTROL_TRACKER] Table creation failed: {e}")
            raise
    
    def record_observation(
        self,
        game_id: str,
        level: int,
        action: str,
        frame_before: List[List[int]],
        frame_after: List[List[int]],
        action_number: int
    ) -> List[ControlObservation]:
        """
        Record an action and resulting frame change.
        
        Args:
            game_id: Game identifier (e.g., "sp80-abc123")
            level: Level number
            action: Action taken (ACTION1-ACTION7)
            frame_before: Frame state before action
            frame_after: Frame state after action
            action_number: Sequential action number in this game
            
        Returns:
            List of observations (movements detected)
            
        Raises:
            ValueError: If inputs are invalid
        """
        # Input validation
        if not game_id:
            raise ValueError("[CONTROL_TRACKER] game_id cannot be empty")
        if level < 0:
            raise ValueError(f"[CONTROL_TRACKER] level must be >= 0, got {level}")
        if not action.startswith("ACTION"):
            raise ValueError(f"[CONTROL_TRACKER] action must start with 'ACTION', got {action}")
        if not frame_before or not frame_after:
            raise ValueError("[CONTROL_TRACKER] frame_before and frame_after cannot be empty")
        
        game_type = self._extract_game_type(game_id)
        key = f"{game_type}_{level}"
        
        if key not in self._observations:
            self._observations[key] = []
        
        # Find objects and their movements
        objects_before = self._find_objects(frame_before)
        objects_after = self._find_objects(frame_after)
        
        observations = []
        movement_direction = self._action_to_direction(action)
        
        # Track which objects moved
        for obj_id, positions_before in objects_before.items():
            positions_after = objects_after.get(obj_id, [])
            
            if not positions_before or not positions_after:
                continue
            
            # Use centroid for position comparison
            centroid_before = self._calculate_centroid(positions_before)
            centroid_after = self._calculate_centroid(positions_after)
            
            obs = ControlObservation(
                action=action,
                object_id=obj_id,
                movement_direction=movement_direction,
                position_before=centroid_before,
                position_after=centroid_after,
                action_number=action_number
            )
            
            if obs.moved:
                actual_direction = self._detect_movement_direction(centroid_before, centroid_after)
                
                # Check if movement matches expected direction
                if actual_direction == movement_direction:
                    observations.append(obs)
                    self._observations[key].append(obs)
                    logger.debug(
                        f"[CONTROL_TRACKER] {obj_id} moved {actual_direction} on {action} "
                        f"(action #{action_number})"
                    )
        
        # Update control map if we have enough observations
        self._update_control_map(game_type, level)
        
        return observations
    
    def get_controlled_objects(
        self,
        game_id: str,
        level: int,
        min_confidence: ControlConfidence = ControlConfidence.SUSPECTED
    ) -> List[ControlledObject]:
        """
        Get objects the agent controls at this game/level.
        
        Args:
            game_id: Game identifier
            level: Level number
            min_confidence: Minimum confidence level to include
            
        Returns:
            List of ControlledObject instances
        """
        game_type = self._extract_game_type(game_id)
        
        try:
            rows = self.db.execute_query("""
                SELECT object_id, control_type, confidence, action_map, observation_count
                FROM control_tracking
                WHERE game_type = ? AND level = ?
            """, (game_type, level))
        except Exception as e:
            logger.error(f"[CONTROL_TRACKER] Query failed for {game_type} level {level}: {e}")
            return []
        
        result = []
        confidence_order = [c.value for c in ControlConfidence]
        min_idx = confidence_order.index(min_confidence.value)
        
        for row in rows:
            conf = ControlConfidence(row['confidence'])
            conf_idx = confidence_order.index(conf.value)
            
            if conf_idx >= min_idx:
                result.append(ControlledObject(
                    object_id=row['object_id'],
                    control_type=row['control_type'],
                    confidence=conf,
                    action_map=json.loads(row['action_map']),
                    observation_count=row['observation_count']
                ))
        
        logger.debug(f"[CONTROL_TRACKER] Found {len(result)} controlled objects for {game_type} L{level}")
        return result
    
    def verify_still_controlled(
        self,
        game_id: str,
        level: int,
        object_id: str,
        action: str,
        frame_before: List[List[int]],
        frame_after: List[List[int]]
    ) -> bool:
        """
        Verify an object is still controlled by checking if it responds to action.
        
        Args:
            game_id: Game identifier
            level: Level number
            object_id: Object to verify (e.g., "color_5")
            action: Action to test
            frame_before: Frame before action
            frame_after: Frame after action
            
        Returns:
            True if object responded as expected, False otherwise
        """
        game_type = self._extract_game_type(game_id)
        
        # Get expected action map
        controlled = self.get_controlled_objects(game_id, level)
        obj_control = next((c for c in controlled if c.object_id == object_id), None)
        
        if not obj_control:
            logger.warning(f"[CONTROL_TRACKER] {object_id} not in control list for {game_type} L{level}")
            return False
        
        expected_direction = obj_control.action_map.get(action)
        if not expected_direction:
            logger.debug(f"[CONTROL_TRACKER] No expected response for {action} on {object_id}")
            return True  # No expectation = passes
        
        # Check actual movement
        objects_before = self._find_objects(frame_before)
        objects_after = self._find_objects(frame_after)
        
        positions_before = objects_before.get(object_id, [])
        positions_after = objects_after.get(object_id, [])
        
        if not positions_before:
            logger.warning(f"[CONTROL_TRACKER] {object_id} not found in frame_before")
            return False
        if not positions_after:
            logger.warning(f"[CONTROL_TRACKER] {object_id} disappeared after action")
            return False
        
        centroid_before = self._calculate_centroid(positions_before)
        centroid_after = self._calculate_centroid(positions_after)
        
        actual_direction = self._detect_movement_direction(centroid_before, centroid_after)
        
        if actual_direction == expected_direction:
            logger.debug(f"[CONTROL_TRACKER] {object_id} verified: moved {actual_direction}")
            return True
        else:
            logger.info(
                f"[CONTROL_TRACKER] {object_id} control LOST: expected {expected_direction}, "
                f"got {actual_direction or 'no movement'}"
            )
            return False
    
    def store_control_map(
        self,
        game_id: str,
        level: int,
        controlled_objects: List[str],
        action_response_map: Dict[str, str],
        confidence: float = 0.5
    ) -> bool:
        """
        Store a control map from external source (e.g., network hypothesis).
        
        Args:
            game_id: Game identifier
            level: Level number  
            controlled_objects: List of object IDs
            action_response_map: Map of action -> direction
            confidence: Confidence score 0.0-1.0
            
        Returns:
            True if stored successfully
        """
        game_type = self._extract_game_type(game_id)
        conf_level = self._score_to_confidence(confidence)
        
        stored_count = 0
        for obj_id in controlled_objects:
            try:
                self.db.execute_query("""
                    INSERT INTO control_tracking 
                    (game_type, level, object_id, control_type, confidence, action_map, observation_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(game_type, level, object_id) DO UPDATE SET
                        confidence = CASE WHEN excluded.confidence > confidence THEN excluded.confidence ELSE confidence END,
                        action_map = excluded.action_map,
                        observation_count = observation_count + 1,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    game_type, level, obj_id, 'movement',
                    conf_level.value, json.dumps(action_response_map), 1
                ))
                stored_count += 1
            except Exception as e:
                logger.error(f"[CONTROL_TRACKER] Failed to store {obj_id}: {e}")
        
        logger.info(f"[CONTROL_TRACKER] Stored {stored_count}/{len(controlled_objects)} control entries")
        return stored_count > 0
    
    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================
    
    def _extract_game_type(self, game_id: str) -> str:
        """Extract game type from game_id (e.g., 'sp80-abc' -> 'sp80')."""
        if '-' in game_id:
            return game_id.split('-')[0]
        return game_id[:4] if len(game_id) >= 4 else game_id
    
    def _find_objects(self, frame: List[List[int]]) -> Dict[str, List[Tuple[int, int]]]:
        """
        Find all objects in frame.
        
        Returns:
            Dict mapping object_id (e.g., "color_5") to list of (y, x) positions
        """
        objects: Dict[str, List[Tuple[int, int]]] = {}
        
        for y, row in enumerate(frame):
            for x, color in enumerate(row):
                if color > 0:  # Non-background
                    obj_id = f"color_{color}"
                    if obj_id not in objects:
                        objects[obj_id] = []
                    objects[obj_id].append((y, x))
        
        return objects
    
    def _calculate_centroid(self, positions: List[Tuple[int, int]]) -> Tuple[int, int]:
        """Calculate centroid of positions."""
        if not positions:
            return (0, 0)
        avg_y = sum(p[0] for p in positions) // len(positions)
        avg_x = sum(p[1] for p in positions) // len(positions)
        return (avg_y, avg_x)
    
    def _action_to_direction(self, action: str) -> Optional[str]:
        """Map action to expected movement direction."""
        mapping = {
            'ACTION1': 'up',
            'ACTION2': 'down',
            'ACTION3': 'left',
            'ACTION4': 'right',
        }
        return mapping.get(action)
    
    def _detect_movement_direction(
        self,
        pos_before: Tuple[int, int],
        pos_after: Tuple[int, int]
    ) -> Optional[str]:
        """Detect movement direction from position change."""
        dy = pos_after[0] - pos_before[0]
        dx = pos_after[1] - pos_before[1]
        
        if dy == 0 and dx == 0:
            return None
        
        # Determine dominant direction
        if abs(dy) >= abs(dx):
            return 'down' if dy > 0 else 'up'
        else:
            return 'right' if dx > 0 else 'left'
    
    def _score_to_confidence(self, score: float) -> ControlConfidence:
        """Convert numeric score to confidence level."""
        if score >= 0.8:
            return ControlConfidence.CONFIRMED
        elif score >= 0.5:
            return ControlConfidence.LIKELY
        elif score >= 0.2:
            return ControlConfidence.SUSPECTED
        return ControlConfidence.UNKNOWN
    
    def _update_control_map(self, game_type: str, level: int) -> None:
        """Update control map based on accumulated observations."""
        key = f"{game_type}_{level}"
        observations = self._observations.get(key, [])
        
        if len(observations) < 2:
            return  # Need multiple observations
        
        # Count action -> object -> direction correlations
        correlations: Dict[str, Dict[str, Dict[str, int]]] = {}  # obj -> action -> direction -> count
        
        for obs in observations:
            if not obs.moved:
                continue
            
            direction = self._detect_movement_direction(obs.position_before, obs.position_after)
            if not direction:
                continue
            
            if obs.object_id not in correlations:
                correlations[obs.object_id] = {}
            if obs.action not in correlations[obs.object_id]:
                correlations[obs.object_id][obs.action] = {}
            
            correlations[obs.object_id][obs.action][direction] = \
                correlations[obs.object_id][obs.action].get(direction, 0) + 1
        
        # Find consistent control patterns
        for obj_id, action_dirs in correlations.items():
            action_map = {}
            total_obs = 0
            
            for action, dirs in action_dirs.items():
                if dirs:
                    # Most common direction for this action
                    best_dir = max(dirs, key=dirs.get)
                    action_map[action] = best_dir
                    total_obs += dirs[best_dir]
            
            if action_map:
                confidence = self._score_to_confidence(min(1.0, total_obs / 5))
                
                try:
                    self.db.execute_query("""
                        INSERT INTO control_tracking 
                        (game_type, level, object_id, control_type, confidence, action_map, observation_count)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(game_type, level, object_id) DO UPDATE SET
                            confidence = excluded.confidence,
                            action_map = excluded.action_map,
                            observation_count = excluded.observation_count,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        game_type, level, obj_id, 'movement',
                        confidence.value, json.dumps(action_map), total_obs
                    ))
                    logger.info(
                        f"[CONTROL_TRACKER] Updated {obj_id}: {action_map} "
                        f"(confidence={confidence.value}, obs={total_obs})"
                    )
                except Exception as e:
                    logger.error(f"[CONTROL_TRACKER] Failed to update {obj_id}: {e}")
