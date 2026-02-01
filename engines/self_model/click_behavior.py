"""
Click Behavior - Click Action Classification
============================================

Classifies click behaviors and tracks click patterns:
- Toggle clicks (on/off state)
- Collect clicks (object disappears + score)
- Select clicks (object becomes selected)
- Trigger clicks (causes chain reactions)

Design Principles:
- Clear behavior categories with explicit criteria
- Evidence-based classification
- No ambiguous classifications
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import logging
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set, Any
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class ClickBehavior(Enum):
    """Classification of click behaviors."""
    UNKNOWN = "unknown"
    NO_EFFECT = "no_effect"        # Click did nothing
    TOGGLE = "toggle"              # Object toggled state
    COLLECT = "collect"            # Object collected (disappears, score+)
    DESTROY = "destroy"            # Object destroyed (disappears, score-)
    SELECT = "select"              # Object became selected
    DESELECT = "deselect"          # Object deselected
    TRIGGER = "trigger"            # Triggered chain reaction
    ACTIVATE = "activate"          # Activated something
    MOVE = "move"                  # Caused movement
    SPAWN = "spawn"                # Spawned new objects


@dataclass
class ClickResult:
    """Result of a click action."""
    behavior: ClickBehavior
    confidence: float
    target_object: str
    position: Tuple[int, int]
    
    # What changed
    score_delta: float = 0.0
    objects_disappeared: List[str] = field(default_factory=list)
    objects_appeared: List[str] = field(default_factory=list)
    objects_moved: List[str] = field(default_factory=list)
    state_changes: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    timestamp: str = ""
    frame_hash_before: str = ""
    frame_hash_after: str = ""


@dataclass
class ObjectClickProfile:
    """Profile of how an object responds to clicks."""
    object_id: str
    color: int
    game_type: str
    
    # Behavior statistics
    behavior_counts: Dict[str, int] = field(default_factory=dict)
    dominant_behavior: ClickBehavior = ClickBehavior.UNKNOWN
    
    # Score impact
    total_score_impact: float = 0.0
    click_count: int = 0
    avg_score_impact: float = 0.0
    
    # Temporal
    first_click: str = ""
    last_click: str = ""
    
    def update(self, result: ClickResult) -> None:
        """Update profile with click result."""
        behavior = result.behavior.value
        self.behavior_counts[behavior] = self.behavior_counts.get(behavior, 0) + 1
        
        self.total_score_impact += result.score_delta
        self.click_count += 1
        self.avg_score_impact = self.total_score_impact / self.click_count
        
        self.last_click = datetime.now().isoformat()
        if not self.first_click:
            self.first_click = self.last_click
        
        # Update dominant behavior
        if self.behavior_counts:
            max_behavior = max(self.behavior_counts.items(), key=lambda x: x[1])
            self.dominant_behavior = ClickBehavior(max_behavior[0])


class ClickBehaviorClassifier:
    """
    Classifies click behaviors and maintains click profiles.
    
    Usage:
        classifier = ClickBehaviorClassifier(db_path)
        
        # Classify a click action result
        result = classifier.classify_click(
            position=(5, 10),
            frame_before=[[...]],
            frame_after=[[...]],
            score_before=50,
            score_after=60,
            game_type="sp80"
        )
        
        print(f"Click behavior: {result.behavior.value}")
        print(f"Score delta: {result.score_delta}")
        
        # Get profile for an object
        profile = classifier.get_click_profile("color_3", "sp80")
        print(f"Dominant behavior: {profile.dominant_behavior}")
    """
    
    def __init__(self, db_path: str = "core_data.db"):
        """
        Initialize click behavior classifier.
        
        Args:
            db_path: Path to database
        """
        try:
            from database_interface import DatabaseInterface
            self.db = DatabaseInterface(db_path)
        except Exception as e:
            raise RuntimeError(f"[CLICK] Failed to connect to database: {e}")
        
        self._profiles: Dict[str, ObjectClickProfile] = {}
        self._ensure_tables()
        logger.info("[CLICK] Initialized")
    
    def _ensure_tables(self) -> None:
        """Ensure required tables exist."""
        try:
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS click_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_type TEXT NOT NULL,
                    target_object TEXT NOT NULL,
                    position_y INTEGER,
                    position_x INTEGER,
                    behavior TEXT NOT NULL,
                    confidence REAL,
                    score_delta REAL DEFAULT 0.0,
                    objects_disappeared_json TEXT,
                    objects_appeared_json TEXT,
                    objects_moved_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS click_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    object_id TEXT NOT NULL,
                    color INTEGER NOT NULL,
                    game_type TEXT NOT NULL,
                    behavior_counts_json TEXT,
                    dominant_behavior TEXT,
                    total_score_impact REAL DEFAULT 0.0,
                    click_count INTEGER DEFAULT 0,
                    first_click TIMESTAMP,
                    last_click TIMESTAMP,
                    UNIQUE(object_id, game_type)
                )
            """)
            
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_click_results_game
                ON click_results(game_type, target_object)
            """)
            
            logger.debug("[CLICK] Tables verified")
        except Exception as e:
            logger.error(f"[CLICK] Table creation failed: {e}")
            raise
    
    def classify_click(
        self,
        position: Tuple[int, int],
        frame_before: List[List[int]],
        frame_after: List[List[int]],
        score_before: float,
        score_after: float,
        game_type: str,
        selection_state: Optional[Dict[str, Any]] = None
    ) -> ClickResult:
        """
        Classify the behavior of a click action.
        
        Args:
            position: (y, x) position that was clicked
            frame_before: Frame before click
            frame_after: Frame after click
            score_before: Score before click
            score_after: Score after click
            game_type: Game type
            selection_state: Optional selection state info
            
        Returns:
            ClickResult with classification
        """
        y, x = position
        score_delta = score_after - score_before
        
        # Identify target object
        target_color = frame_before[y][x] if 0 <= y < len(frame_before) and 0 <= x < len(frame_before[0]) else 0
        target_object = f"color_{target_color}" if target_color > 0 else "empty"
        
        # Analyze changes
        objects_before = self._find_objects(frame_before)
        objects_after = self._find_objects(frame_after)
        
        disappeared = []
        appeared = []
        moved = []
        
        for color, positions in objects_before.items():
            obj_id = f"color_{color}"
            if color not in objects_after:
                disappeared.append(obj_id)
            elif positions != objects_after.get(color, set()):
                moved.append(obj_id)
        
        for color, positions in objects_after.items():
            obj_id = f"color_{color}"
            if color not in objects_before:
                appeared.append(obj_id)
        
        # Classify behavior
        behavior, confidence = self._determine_behavior(
            target_object=target_object,
            score_delta=score_delta,
            disappeared=disappeared,
            appeared=appeared,
            moved=moved,
            frame_changed=(frame_before != frame_after),
            selection_state=selection_state
        )
        
        result = ClickResult(
            behavior=behavior,
            confidence=confidence,
            target_object=target_object,
            position=position,
            score_delta=score_delta,
            objects_disappeared=disappeared,
            objects_appeared=appeared,
            objects_moved=moved,
            timestamp=datetime.now().isoformat(),
            frame_hash_before=str(hash(str(frame_before)))[:12],
            frame_hash_after=str(hash(str(frame_after)))[:12]
        )
        
        # Save result and update profile
        self._save_click_result(result, game_type)
        self._update_profile(target_object, result, game_type)
        
        logger.info(
            f"[CLICK] Classified click at ({y},{x}): "
            f"{behavior.value} on {target_object} "
            f"(score={score_delta:+.1f}, conf={confidence:.2f})"
        )
        
        return result
    
    def get_click_profile(
        self,
        object_id: str,
        game_type: str
    ) -> Optional[ObjectClickProfile]:
        """
        Get click profile for an object.
        
        Args:
            object_id: Object identifier
            game_type: Game type
            
        Returns:
            ObjectClickProfile or None if not found
        """
        cache_key = f"{object_id}_{game_type}"
        
        if cache_key in self._profiles:
            return self._profiles[cache_key]
        
        profile = self._load_profile(object_id, game_type)
        if profile:
            self._profiles[cache_key] = profile
        return profile
    
    def get_all_profiles(
        self,
        game_type: str,
        min_clicks: int = 1
    ) -> List[ObjectClickProfile]:
        """
        Get all click profiles for a game type.
        
        Args:
            game_type: Game type
            min_clicks: Minimum click count
            
        Returns:
            List of ObjectClickProfiles
        """
        try:
            rows = self.db.execute_query("""
                SELECT * FROM click_profiles
                WHERE game_type = ? AND click_count >= ?
                ORDER BY click_count DESC
            """, (game_type, min_clicks))
            
            profiles = []
            for row in rows:
                profile = self._row_to_profile(row)
                if profile:
                    profiles.append(profile)
            
            return profiles
            
        except Exception as e:
            logger.error(f"[CLICK] Failed to get profiles: {e}")
            return []
    
    def predict_click_behavior(
        self,
        object_id: str,
        game_type: str
    ) -> Tuple[ClickBehavior, float]:
        """
        Predict what will happen if we click an object.
        
        Args:
            object_id: Object to potentially click
            game_type: Game type
            
        Returns:
            Tuple of (predicted behavior, confidence)
        """
        profile = self.get_click_profile(object_id, game_type)
        
        if not profile or profile.click_count == 0:
            return (ClickBehavior.UNKNOWN, 0.0)
        
        # Confidence based on click count
        confidence = min(1.0, profile.click_count / 5)  # 5 clicks for full confidence
        
        return (profile.dominant_behavior, confidence)
    
    def get_collectible_objects(
        self,
        game_type: str,
        min_confidence: float = 0.5
    ) -> List[str]:
        """
        Get objects that are likely collectible (positive score on click).
        
        Args:
            game_type: Game type
            min_confidence: Minimum confidence
            
        Returns:
            List of object IDs
        """
        profiles = self.get_all_profiles(game_type, min_clicks=2)
        
        collectibles = []
        for profile in profiles:
            if profile.dominant_behavior == ClickBehavior.COLLECT:
                if profile.avg_score_impact > 0:
                    confidence = min(1.0, profile.click_count / 5)
                    if confidence >= min_confidence:
                        collectibles.append(profile.object_id)
        
        return collectibles
    
    def get_dangerous_objects(
        self,
        game_type: str,
        min_confidence: float = 0.5
    ) -> List[str]:
        """
        Get objects that are dangerous to click (negative score).
        
        Args:
            game_type: Game type
            min_confidence: Minimum confidence
            
        Returns:
            List of object IDs
        """
        profiles = self.get_all_profiles(game_type, min_clicks=2)
        
        dangerous = []
        for profile in profiles:
            if profile.avg_score_impact < 0:
                confidence = min(1.0, profile.click_count / 5)
                if confidence >= min_confidence:
                    dangerous.append(profile.object_id)
        
        return dangerous
    
    def get_trigger_objects(
        self,
        game_type: str
    ) -> List[str]:
        """
        Get objects that trigger chain reactions when clicked.
        
        Args:
            game_type: Game type
            
        Returns:
            List of object IDs
        """
        profiles = self.get_all_profiles(game_type, min_clicks=1)
        
        triggers = []
        for profile in profiles:
            if profile.dominant_behavior == ClickBehavior.TRIGGER:
                triggers.append(profile.object_id)
        
        return triggers
    
    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================
    
    def _determine_behavior(
        self,
        target_object: str,
        score_delta: float,
        disappeared: List[str],
        appeared: List[str],
        moved: List[str],
        frame_changed: bool,
        selection_state: Optional[Dict[str, Any]]
    ) -> Tuple[ClickBehavior, float]:
        """Determine click behavior from observations."""
        
        # Priority-based classification
        
        # 1. If target disappeared with positive score = COLLECT
        if target_object in disappeared and score_delta > 0:
            return (ClickBehavior.COLLECT, 0.95)
        
        # 2. If target disappeared with negative score = DESTROY
        if target_object in disappeared and score_delta < 0:
            return (ClickBehavior.DESTROY, 0.90)
        
        # 3. If score changed but target didn't disappear = might be TOGGLE
        if score_delta != 0 and target_object not in disappeared:
            return (ClickBehavior.TOGGLE, 0.70)
        
        # 4. If other things changed = TRIGGER
        if len(disappeared) > 0 or len(appeared) > 0:
            return (ClickBehavior.TRIGGER, 0.80)
        
        # 5. If things moved = MOVE
        if len(moved) > 0:
            return (ClickBehavior.MOVE, 0.75)
        
        # 6. Check selection state for SELECT/DESELECT
        if selection_state:
            if selection_state.get('newly_selected') == target_object:
                return (ClickBehavior.SELECT, 0.85)
            if selection_state.get('newly_deselected') == target_object:
                return (ClickBehavior.DESELECT, 0.85)
        
        # 7. Frame changed but can't classify = ACTIVATE
        if frame_changed:
            return (ClickBehavior.ACTIVATE, 0.50)
        
        # 8. Nothing happened = NO_EFFECT
        return (ClickBehavior.NO_EFFECT, 0.95)
    
    def _find_objects(
        self,
        frame: List[List[int]]
    ) -> Dict[int, Set[Tuple[int, int]]]:
        """Find all objects by color in frame."""
        objects: Dict[int, Set[Tuple[int, int]]] = {}
        
        for y, row in enumerate(frame):
            for x, color in enumerate(row):
                if color > 0:
                    if color not in objects:
                        objects[color] = set()
                    objects[color].add((y, x))
        
        return objects
    
    def _save_click_result(self, result: ClickResult, game_type: str) -> None:
        """Save click result to database."""
        try:
            self.db.execute_query("""
                INSERT INTO click_results
                (game_type, target_object, position_y, position_x, behavior,
                 confidence, score_delta, objects_disappeared_json,
                 objects_appeared_json, objects_moved_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                game_type,
                result.target_object,
                result.position[0],
                result.position[1],
                result.behavior.value,
                result.confidence,
                result.score_delta,
                json.dumps(result.objects_disappeared),
                json.dumps(result.objects_appeared),
                json.dumps(result.objects_moved)
            ))
        except Exception as e:
            logger.error(f"[CLICK] Failed to save click result: {e}")
    
    def _update_profile(
        self,
        object_id: str,
        result: ClickResult,
        game_type: str
    ) -> None:
        """Update click profile for object."""
        cache_key = f"{object_id}_{game_type}"
        
        # Get or create profile
        profile = self._profiles.get(cache_key)
        if not profile:
            profile = self._load_profile(object_id, game_type)
        if not profile:
            color = int(object_id.replace('color_', '')) if 'color_' in object_id else 0
            profile = ObjectClickProfile(
                object_id=object_id,
                color=color,
                game_type=game_type
            )
        
        profile.update(result)
        self._profiles[cache_key] = profile
        self._save_profile(profile)
    
    def _load_profile(
        self,
        object_id: str,
        game_type: str
    ) -> Optional[ObjectClickProfile]:
        """Load click profile from database."""
        try:
            rows = self.db.execute_query("""
                SELECT * FROM click_profiles
                WHERE object_id = ? AND game_type = ?
            """, (object_id, game_type))
            
            if rows:
                return self._row_to_profile(rows[0])
            return None
            
        except Exception as e:
            logger.warning(f"[CLICK] Failed to load profile: {e}")
            return None
    
    def _row_to_profile(self, row: Dict[str, Any]) -> Optional[ObjectClickProfile]:
        """Convert database row to ObjectClickProfile."""
        try:
            behavior_counts = json.loads(row.get('behavior_counts_json') or '{}')
            return ObjectClickProfile(
                object_id=row['object_id'],
                color=row['color'],
                game_type=row['game_type'],
                behavior_counts=behavior_counts,
                dominant_behavior=ClickBehavior(row.get('dominant_behavior', 'unknown')),
                total_score_impact=row.get('total_score_impact', 0.0),
                click_count=row.get('click_count', 0),
                first_click=row.get('first_click', ''),
                last_click=row.get('last_click', '')
            )
        except Exception as e:
            logger.warning(f"[CLICK] Failed to parse profile row: {e}")
            return None
    
    def _save_profile(self, profile: ObjectClickProfile) -> None:
        """Save click profile to database."""
        try:
            self.db.execute_query("""
                INSERT INTO click_profiles
                (object_id, color, game_type, behavior_counts_json, dominant_behavior,
                 total_score_impact, click_count, first_click, last_click)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(object_id, game_type) DO UPDATE SET
                    behavior_counts_json = excluded.behavior_counts_json,
                    dominant_behavior = excluded.dominant_behavior,
                    total_score_impact = excluded.total_score_impact,
                    click_count = excluded.click_count,
                    last_click = excluded.last_click
            """, (
                profile.object_id,
                profile.color,
                profile.game_type,
                json.dumps(profile.behavior_counts),
                profile.dominant_behavior.value,
                profile.total_score_impact,
                profile.click_count,
                profile.first_click,
                profile.last_click
            ))
        except Exception as e:
            logger.error(f"[CLICK] Failed to save profile: {e}")
