"""
Discovery Engine - Systematic Object Discovery
===============================================

Manages the discovery phase where agents systematically click objects
to learn their behaviors and control relationships.

Design Principles:
- EXPLICIT logging of all discovery actions
- Clear state machine for discovery phases
- No silent failures - all errors logged with context
- Deterministic discovery order for reproducibility
"""

import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class DiscoveryPhase(Enum):
    """Phases of object discovery."""
    IDLE = "idle"
    MOVEMENT_TEST = "movement_test"      # Testing ACTION1-4 movement
    CLICK_SURVEY = "click_survey"        # Clicking each unique object
    SELECTION_TEST = "selection_test"    # Testing ACTION6 selection
    TOGGLE_TEST = "toggle_test"          # Testing toggleable objects
    COMPLETE = "complete"


class ObjectBehavior(Enum):
    """Discovered object behaviors."""
    UNKNOWN = "unknown"
    PLAYER_CONTROLLED = "player_controlled"
    SELECTABLE = "selectable"
    TOGGLEABLE = "toggleable"
    BUTTON = "button"
    OBSTACLE = "obstacle"
    COLLECTIBLE = "collectible"
    GOAL = "goal"
    HAZARD = "hazard"


@dataclass
class DiscoveryTarget:
    """An object to be discovered."""
    object_id: str
    color: int
    positions: List[Tuple[int, int]]
    discovered: bool = False
    behavior: ObjectBehavior = ObjectBehavior.UNKNOWN
    click_result: Optional[str] = None

    @property
    def centroid(self) -> Tuple[int, int]:
        if not self.positions:
            return (0, 0)
        avg_y = sum(p[0] for p in self.positions) // len(self.positions)
        avg_x = sum(p[1] for p in self.positions) // len(self.positions)
        return (avg_y, avg_x)


@dataclass
class DiscoveryState:
    """Current state of discovery for a game/level."""
    game_type: str
    level: int
    phase: DiscoveryPhase = DiscoveryPhase.IDLE
    targets: List[DiscoveryTarget] = field(default_factory=list)
    current_target_idx: int = 0
    actions_in_phase: int = 0
    total_actions: int = 0
    discoveries: Dict[str, ObjectBehavior] = field(default_factory=dict)

    def current_target(self) -> Optional[DiscoveryTarget]:
        if 0 <= self.current_target_idx < len(self.targets):
            return self.targets[self.current_target_idx]
        return None

    def advance_target(self) -> bool:
        """Move to next target. Returns True if more targets exist."""
        self.current_target_idx += 1
        return self.current_target_idx < len(self.targets)


class DiscoveryEngine:
    """
    Manages systematic object discovery during gameplay.

    Usage:
        engine = DiscoveryEngine(db_path)

        # Initialize discovery for a game
        engine.start_discovery("sp80-abc", level=1, frame=[[...]])

        # Get next discovery action
        action = engine.get_next_action(current_frame)
        if action:
            print(f"Discovery suggests: {action['action']} at ({action['x']}, {action['y']})")

        # Record result of action
        engine.record_result(action, frame_before, frame_after, score_delta)

        # Check if discovery complete
        if engine.is_complete():
            discoveries = engine.get_discoveries()
    """

    def __init__(self, db_path: str = "core_data.db"):
        """
        Initialize discovery engine.

        Args:
            db_path: Path to database

        Raises:
            RuntimeError: If database connection fails
        """
        try:
            from database_interface import DatabaseInterface
            self.db = DatabaseInterface(db_path)
        except Exception as e:
            raise RuntimeError(f"[DISCOVERY] Failed to connect to database: {e}")

        self._state: Optional[DiscoveryState] = None
        self._ensure_tables()
        logger.info("[DISCOVERY] Initialized")

    def _ensure_tables(self) -> None:
        """Ensure required tables exist."""
        try:
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS object_discoveries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_type TEXT NOT NULL,
                    level INTEGER NOT NULL,
                    object_id TEXT NOT NULL,
                    color INTEGER NOT NULL,
                    behavior TEXT NOT NULL,
                    click_result TEXT,
                    discovery_action_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(game_type, level, object_id)
                )
            """)
            logger.debug("[DISCOVERY] Tables verified")
        except Exception as e:
            logger.error(f"[DISCOVERY] Table creation failed: {e}")
            raise

    def start_discovery(
        self,
        game_id: str,
        level: int,
        frame: List[List[int]],
        max_actions: int = 50
    ) -> DiscoveryState:
        """
        Start discovery phase for a game/level.

        Args:
            game_id: Game identifier
            level: Level number
            frame: Current frame state
            max_actions: Maximum actions to spend on discovery

        Returns:
            DiscoveryState with targets identified
        """
        game_type = self._extract_game_type(game_id)

        # Find all unique objects in frame
        targets = self._identify_targets(frame)

        # Load any existing discoveries
        existing = self._load_existing_discoveries(game_type, level)
        for target in targets:
            if target.object_id in existing:
                target.discovered = True
                target.behavior = existing[target.object_id]

        self._state = DiscoveryState(
            game_type=game_type,
            level=level,
            phase=DiscoveryPhase.MOVEMENT_TEST,
            targets=targets,
            discoveries=existing
        )

        undiscovered = len([t for t in targets if not t.discovered])
        logger.info(
            f"[DISCOVERY] Started for {game_type} L{level}: "
            f"{len(targets)} objects, {undiscovered} undiscovered"
        )

        return self._state

    def get_next_action(
        self,
        current_frame: List[List[int]],
        controlled_objects: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get next discovery action to take.

        Args:
            current_frame: Current frame state
            controlled_objects: Objects already known to be controlled

        Returns:
            Action dict with 'action', 'x', 'y', 'reason' or None if complete
        """
        if not self._state:
            logger.warning("[DISCOVERY] No active discovery state")
            return None

        state = self._state

        # Phase: Movement Test (first few actions)
        if state.phase == DiscoveryPhase.MOVEMENT_TEST:
            if state.actions_in_phase < 8:  # Test each direction twice
                action = self._get_movement_test_action(state.actions_in_phase)
                return action
            else:
                state.phase = DiscoveryPhase.CLICK_SURVEY
                state.actions_in_phase = 0
                logger.info("[DISCOVERY] Phase -> CLICK_SURVEY")

        # Phase: Click Survey (click each unique object)
        if state.phase == DiscoveryPhase.CLICK_SURVEY:
            target = state.current_target()

            while target and target.discovered:
                if not state.advance_target():
                    state.phase = DiscoveryPhase.COMPLETE
                    break
                target = state.current_target()

            if target and not target.discovered:
                y, x = target.centroid
                return {
                    'action': 'ACTION7',  # Click
                    'x': x,
                    'y': y,
                    'reason': f'discover_{target.object_id}',
                    'target_object': target.object_id,
                    'phase': 'click_survey'
                }

        # Phase: Complete
        if state.phase == DiscoveryPhase.COMPLETE:
            logger.info(
                f"[DISCOVERY] Complete for {state.game_type} L{state.level}: "
                f"{len(state.discoveries)} behaviors discovered"
            )
            return None

        return None

    def record_result(
        self,
        action_info: Dict[str, Any],
        frame_before: List[List[int]],
        frame_after: List[List[int]],
        score_delta: float = 0.0
    ) -> Optional[ObjectBehavior]:
        """
        Record the result of a discovery action.

        Args:
            action_info: Action dict from get_next_action()
            frame_before: Frame before action
            frame_after: Frame after action
            score_delta: Change in score

        Returns:
            Discovered behavior or None
        """
        if not self._state:
            logger.warning("[DISCOVERY] No active state for recording")
            return None

        state = self._state
        state.actions_in_phase += 1
        state.total_actions += 1

        phase = action_info.get('phase', '')

        if phase == 'movement_test':
            return self._process_movement_result(action_info, frame_before, frame_after)

        elif phase == 'click_survey':
            return self._process_click_result(action_info, frame_before, frame_after, score_delta)

        return None

    def is_complete(self) -> bool:
        """Check if discovery phase is complete."""
        return self._state is not None and self._state.phase == DiscoveryPhase.COMPLETE

    def get_discoveries(self) -> Dict[str, ObjectBehavior]:
        """Get all discovered behaviors."""
        if not self._state:
            return {}
        return dict(self._state.discoveries)

    def get_state(self) -> Optional[DiscoveryState]:
        """Get current discovery state."""
        return self._state

    def reset(self) -> None:
        """Reset discovery state."""
        self._state = None
        logger.debug("[DISCOVERY] State reset")

    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================

    def _extract_game_type(self, game_id: str) -> str:
        """Extract game type from game_id."""
        if '-' in game_id:
            return game_id.split('-')[0]
        return game_id[:4] if len(game_id) >= 4 else game_id

    def _identify_targets(self, frame: List[List[int]]) -> List[DiscoveryTarget]:
        """Identify unique objects in frame."""
        objects: Dict[int, List[Tuple[int, int]]] = {}

        for y, row in enumerate(frame):
            for x, color in enumerate(row):
                if color > 0:  # Non-background
                    if color not in objects:
                        objects[color] = []
                    objects[color].append((y, x))

        targets = []
        for color, positions in sorted(objects.items()):
            targets.append(DiscoveryTarget(
                object_id=f"color_{color}",
                color=color,
                positions=positions
            ))

        logger.debug(f"[DISCOVERY] Identified {len(targets)} unique objects")
        return targets

    def _load_existing_discoveries(
        self,
        game_type: str,
        level: int
    ) -> Dict[str, ObjectBehavior]:
        """Load existing discoveries from database."""
        try:
            rows = self.db.execute_query("""
                SELECT object_id, behavior FROM object_discoveries
                WHERE game_type = ? AND level = ?
            """, (game_type, level))

            return {row['object_id']: ObjectBehavior(row['behavior']) for row in rows}
        except Exception as e:
            logger.warning(f"[DISCOVERY] Failed to load existing discoveries: {e}")
            return {}

    def _get_movement_test_action(self, action_idx: int) -> Dict[str, Any]:
        """Get movement test action (ACTION1-4)."""
        actions = ['ACTION1', 'ACTION2', 'ACTION3', 'ACTION4']
        action = actions[action_idx % 4]

        return {
            'action': action,
            'x': 0,
            'y': 0,
            'reason': 'movement_test',
            'phase': 'movement_test',
            'test_direction': ['up', 'down', 'left', 'right'][action_idx % 4]
        }

    def _process_movement_result(
        self,
        action_info: Dict[str, Any],
        frame_before: List[List[int]],
        frame_after: List[List[int]]
    ) -> Optional[ObjectBehavior]:
        """Process result of movement test action."""
        if not self._state:
            return None

        # Find objects that moved
        objects_before = self._find_object_positions(frame_before)
        objects_after = self._find_object_positions(frame_after)

        expected_direction = action_info.get('test_direction')

        for obj_id, pos_before in objects_before.items():
            pos_after = objects_after.get(obj_id)
            if pos_after and pos_before != pos_after:
                direction = self._detect_direction(pos_before, pos_after)

                if direction == expected_direction:
                    logger.info(f"[DISCOVERY] {obj_id} is PLAYER_CONTROLLED (moved {direction})")

                    self._state.discoveries[obj_id] = ObjectBehavior.PLAYER_CONTROLLED
                    self._save_discovery(obj_id, ObjectBehavior.PLAYER_CONTROLLED, f"moved_{direction}")

                    # Mark target as discovered
                    for target in self._state.targets:
                        if target.object_id == obj_id:
                            target.discovered = True
                            target.behavior = ObjectBehavior.PLAYER_CONTROLLED

                    return ObjectBehavior.PLAYER_CONTROLLED

        return None

    def _process_click_result(
        self,
        action_info: Dict[str, Any],
        frame_before: List[List[int]],
        frame_after: List[List[int]],
        score_delta: float
    ) -> Optional[ObjectBehavior]:
        """Process result of click action."""
        if not self._state:
            return None

        target_id = action_info.get('target_object', '')

        # Check if frame changed
        frame_changed = frame_before != frame_after

        # Analyze what happened
        behavior = ObjectBehavior.UNKNOWN
        click_result = "no_effect"

        if score_delta > 0:
            behavior = ObjectBehavior.COLLECTIBLE
            click_result = f"score_+{score_delta}"
            logger.info(f"[DISCOVERY] {target_id} is COLLECTIBLE (score +{score_delta})")

        elif score_delta < 0:
            behavior = ObjectBehavior.HAZARD
            click_result = f"score_{score_delta}"
            logger.info(f"[DISCOVERY] {target_id} is HAZARD (score {score_delta})")

        elif frame_changed:
            # Check if object toggled (changed color/state)
            if self._object_toggled(target_id, frame_before, frame_after):
                behavior = ObjectBehavior.TOGGLEABLE
                click_result = "toggled"
                logger.info(f"[DISCOVERY] {target_id} is TOGGLEABLE")
            else:
                # Check if it's a button (caused other changes)
                if self._other_objects_changed(target_id, frame_before, frame_after):
                    behavior = ObjectBehavior.BUTTON
                    click_result = "triggered_change"
                    logger.info(f"[DISCOVERY] {target_id} is BUTTON")
        else:
            behavior = ObjectBehavior.OBSTACLE
            click_result = "no_effect"
            logger.debug(f"[DISCOVERY] {target_id} appears to be OBSTACLE (no effect)")

        # Update state
        self._state.discoveries[target_id] = behavior

        # Mark target as discovered
        target = self._state.current_target()
        if target and target.object_id == target_id:
            target.discovered = True
            target.behavior = behavior
            target.click_result = click_result
            self._state.advance_target()

        # Save to database
        self._save_discovery(target_id, behavior, click_result)

        return behavior

    def _find_object_positions(
        self,
        frame: List[List[int]]
    ) -> Dict[str, Tuple[int, int]]:
        """Find centroid position of each object."""
        objects: Dict[int, List[Tuple[int, int]]] = {}

        for y, row in enumerate(frame):
            for x, color in enumerate(row):
                if color > 0:
                    if color not in objects:
                        objects[color] = []
                    objects[color].append((y, x))

        result = {}
        for color, positions in objects.items():
            avg_y = sum(p[0] for p in positions) // len(positions)
            avg_x = sum(p[1] for p in positions) // len(positions)
            result[f"color_{color}"] = (avg_y, avg_x)

        return result

    def _detect_direction(
        self,
        pos_before: Tuple[int, int],
        pos_after: Tuple[int, int]
    ) -> Optional[str]:
        """Detect movement direction."""
        dy = pos_after[0] - pos_before[0]
        dx = pos_after[1] - pos_before[1]

        if dy == 0 and dx == 0:
            return None

        if abs(dy) >= abs(dx):
            return 'down' if dy > 0 else 'up'
        else:
            return 'right' if dx > 0 else 'left'

    def _object_toggled(
        self,
        object_id: str,
        frame_before: List[List[int]],
        frame_after: List[List[int]]
    ) -> bool:
        """Check if object toggled (changed state in place)."""
        color = int(object_id.replace('color_', ''))

        # Find positions in before frame
        positions_before = set()
        for y, row in enumerate(frame_before):
            for x, c in enumerate(row):
                if c == color:
                    positions_before.add((y, x))

        # Check if those positions have different colors after
        for y, x in positions_before:
            if frame_after[y][x] != color:
                return True

        return False

    def _other_objects_changed(
        self,
        clicked_object: str,
        frame_before: List[List[int]],
        frame_after: List[List[int]]
    ) -> bool:
        """Check if clicking caused other objects to change."""
        clicked_color = int(clicked_object.replace('color_', ''))

        for y, (row_before, row_after) in enumerate(zip(frame_before, frame_after)):
            for x, (c_before, c_after) in enumerate(zip(row_before, row_after)):
                if c_before != c_after:
                    if c_before != clicked_color and c_after != clicked_color:
                        return True

        return False

    def _save_discovery(
        self,
        object_id: str,
        behavior: ObjectBehavior,
        click_result: str
    ) -> None:
        """Save discovery to database."""
        if not self._state:
            return

        color = int(object_id.replace('color_', '')) if 'color_' in object_id else 0

        try:
            self.db.execute_query("""
                INSERT INTO object_discoveries
                (game_type, level, object_id, color, behavior, click_result, discovery_action_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(game_type, level, object_id) DO UPDATE SET
                    behavior = excluded.behavior,
                    click_result = excluded.click_result,
                    discovery_action_count = discovery_action_count + 1
            """, (
                self._state.game_type,
                self._state.level,
                object_id,
                color,
                behavior.value,
                click_result,
                self._state.total_actions
            ))
        except Exception as e:
            logger.error(f"[DISCOVERY] Failed to save discovery for {object_id}: {e}")
