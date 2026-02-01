"""
Valence Goals - Good/Bad Valence and Goal Inference
====================================================

Manages emotional valence tracking:
- Good/bad associations with objects
- Goal inference from level endings
- Region classification (safe/danger)
- Reward prediction

Design Principles:
- Explicit confidence tracking
- Clear evidence chains
- No magic numbers - configurable thresholds
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


class Valence(Enum):
    """Emotional valence of objects/actions."""
    POSITIVE = "positive"   # Good - approach
    NEGATIVE = "negative"   # Bad - avoid
    NEUTRAL = "neutral"     # Unknown/irrelevant
    AMBIGUOUS = "ambiguous" # Context-dependent


class GoalType(Enum):
    """Types of goals that can be inferred."""
    REACH = "reach"              # Get to location
    COLLECT = "collect"          # Collect objects
    AVOID = "avoid"              # Avoid objects
    MATCH = "match"              # Match pattern
    CLEAR = "clear"              # Clear all of something
    SURVIVE = "survive"          # Stay alive
    MAXIMIZE = "maximize"        # Maximize score
    UNKNOWN = "unknown"


@dataclass
class ValenceAssociation:
    """Association between an object and valence."""
    object_id: str
    color: int
    valence: Valence
    confidence: float  # 0.0 to 1.0
    evidence_count: int
    evidence: List[str]  # List of evidence descriptions
    game_type: str
    created_at: str = ""
    updated_at: str = ""
    
    def update(self, new_valence: Valence, evidence_str: str) -> None:
        """Update with new evidence."""
        self.evidence_count += 1
        self.evidence.append(evidence_str)
        self.updated_at = datetime.now().isoformat()
        
        # Adjust confidence based on consistency
        if new_valence == self.valence:
            self.confidence = min(1.0, self.confidence + 0.1)
        elif new_valence == Valence.NEUTRAL:
            pass  # Neutral doesn't change much
        else:
            # Conflicting evidence
            self.confidence = max(0.0, self.confidence - 0.15)
            if self.confidence < 0.3:
                self.valence = Valence.AMBIGUOUS


@dataclass
class InferredGoal:
    """An inferred goal for a game/level."""
    goal_id: str
    game_type: str
    level: int
    goal_type: GoalType
    target_objects: List[str]
    target_regions: List[Tuple[int, int]]  # (y, x) coordinates
    confidence: float
    evidence: List[str]
    achieved_count: int = 0
    failed_count: int = 0
    
    @property
    def reliability(self) -> float:
        total = self.achieved_count + self.failed_count
        if total == 0:
            return self.confidence
        return (self.achieved_count / total) * self.confidence


@dataclass
class RegionClassification:
    """Classification of a grid region."""
    region_id: str
    bounds: Tuple[int, int, int, int]  # (min_y, min_x, max_y, max_x)
    dominant_valence: Valence
    contains_goal: bool
    contains_hazard: bool
    entry_score: float  # Avg score change when entering
    visit_count: int


class ValenceGoalEngine:
    """
    Manages valence associations and goal inference.
    
    Usage:
        engine = ValenceGoalEngine(db_path)
        
        # Record that touching red objects is bad
        engine.record_valence(
            object_id="color_3",
            valence=Valence.NEGATIVE,
            evidence="collision caused score decrease",
            game_type="sp80"
        )
        
        # Infer goal from level end
        goal = engine.infer_goal_from_end(
            game_type="sp80",
            level=1,
            win=True,
            final_frame=[[...]],
            score=100
        )
        
        # Get valence for decision making
        valence = engine.get_valence("color_3", "sp80")
        if valence.valence == Valence.NEGATIVE:
            print("Avoid this object!")
    """
    
    # Configurable thresholds
    CONFIDENCE_HIGH = 0.8
    CONFIDENCE_MEDIUM = 0.5
    CONFIDENCE_LOW = 0.3
    EVIDENCE_FOR_CERTAINTY = 5
    
    def __init__(self, db_path: str = "core_data.db"):
        """
        Initialize valence goal engine.
        
        Args:
            db_path: Path to database
        """
        try:
            from database_interface import DatabaseInterface
            self.db = DatabaseInterface(db_path)
        except Exception as e:
            raise RuntimeError(f"[VALENCE] Failed to connect to database: {e}")
        
        self._cache: Dict[str, ValenceAssociation] = {}
        self._goals: Dict[str, InferredGoal] = {}
        self._ensure_tables()
        logger.info("[VALENCE] Initialized")
    
    def _ensure_tables(self) -> None:
        """Ensure required tables exist."""
        try:
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS valence_associations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    object_id TEXT NOT NULL,
                    color INTEGER NOT NULL,
                    game_type TEXT NOT NULL,
                    valence TEXT NOT NULL,
                    confidence REAL DEFAULT 0.5,
                    evidence_count INTEGER DEFAULT 0,
                    evidence_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(object_id, game_type)
                )
            """)
            
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS inferred_goals (
                    goal_id TEXT PRIMARY KEY,
                    game_type TEXT NOT NULL,
                    level INTEGER NOT NULL,
                    goal_type TEXT NOT NULL,
                    target_objects_json TEXT,
                    target_regions_json TEXT,
                    confidence REAL DEFAULT 0.5,
                    evidence_json TEXT,
                    achieved_count INTEGER DEFAULT 0,
                    failed_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(game_type, level)
                )
            """)
            
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_valence_game
                ON valence_associations(game_type)
            """)
            
            logger.debug("[VALENCE] Tables verified")
        except Exception as e:
            logger.error(f"[VALENCE] Table creation failed: {e}")
            raise
    
    def record_valence(
        self,
        object_id: str,
        valence: Valence,
        evidence: str,
        game_type: str,
        color: Optional[int] = None
    ) -> ValenceAssociation:
        """
        Record a valence association.
        
        Args:
            object_id: Object identifier (e.g., "color_3")
            valence: The valence to associate
            evidence: Description of evidence
            game_type: Game type this applies to
            color: Optional explicit color value
            
        Returns:
            Updated ValenceAssociation
        """
        if color is None:
            color = int(object_id.replace('color_', '')) if 'color_' in object_id else 0
        
        cache_key = f"{object_id}_{game_type}"
        
        # Check cache
        if cache_key in self._cache:
            assoc = self._cache[cache_key]
            assoc.update(valence, evidence)
        else:
            # Check database
            existing = self._load_valence(object_id, game_type)
            if existing:
                existing.update(valence, evidence)
                assoc = existing
            else:
                # Create new
                assoc = ValenceAssociation(
                    object_id=object_id,
                    color=color,
                    valence=valence,
                    confidence=self.CONFIDENCE_MEDIUM,
                    evidence_count=1,
                    evidence=[evidence],
                    game_type=game_type,
                    created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat()
                )
        
        self._cache[cache_key] = assoc
        self._save_valence(assoc)
        
        logger.info(
            f"[VALENCE] {object_id} in {game_type}: "
            f"{valence.value} (conf={assoc.confidence:.2f})"
        )
        
        return assoc
    
    def get_valence(
        self,
        object_id: str,
        game_type: str
    ) -> Optional[ValenceAssociation]:
        """
        Get valence association for an object.
        
        Args:
            object_id: Object identifier
            game_type: Game type
            
        Returns:
            ValenceAssociation or None if unknown
        """
        cache_key = f"{object_id}_{game_type}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        assoc = self._load_valence(object_id, game_type)
        if assoc:
            self._cache[cache_key] = assoc
        return assoc
    
    def get_all_valences(
        self,
        game_type: str,
        min_confidence: float = 0.0
    ) -> List[ValenceAssociation]:
        """
        Get all valence associations for a game type.
        
        Args:
            game_type: Game type to query
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of ValenceAssociations
        """
        try:
            rows = self.db.execute_query("""
                SELECT * FROM valence_associations
                WHERE game_type = ? AND confidence >= ?
                ORDER BY confidence DESC
            """, (game_type, min_confidence))
            
            associations = []
            for row in rows:
                assoc = self._row_to_valence(row)
                if assoc:
                    associations.append(assoc)
            
            return associations
            
        except Exception as e:
            logger.error(f"[VALENCE] Failed to get valences: {e}")
            return []
    
    def infer_goal_from_end(
        self,
        game_type: str,
        level: int,
        win: bool,
        final_frame: List[List[int]],
        score: float,
        action_history: Optional[List[str]] = None
    ) -> Optional[InferredGoal]:
        """
        Infer goal from how a level ended.
        
        Args:
            game_type: Game type
            level: Level number
            win: Whether level was won
            final_frame: Frame at level end
            score: Final score
            action_history: Actions taken during level
            
        Returns:
            InferredGoal or None
        """
        if not win:
            # Can't infer goal from loss (yet)
            return None
        
        goal_id = f"goal_{game_type}_{level}"
        
        # Analyze final frame for clues
        evidence = []
        goal_type = GoalType.UNKNOWN
        target_objects = []
        target_regions = []
        
        # Check what's in final frame
        objects_present = self._find_objects_in_frame(final_frame)
        
        # Heuristics for goal type
        if score > 0:
            evidence.append(f"Positive score ({score}) at win")
            
            # If frame is mostly empty, might be "clear" goal
            total_cells = len(final_frame) * (len(final_frame[0]) if final_frame else 0)
            filled_cells = sum(1 for row in final_frame for c in row if c > 0)
            
            if filled_cells < total_cells * 0.1:
                goal_type = GoalType.CLEAR
                evidence.append("Frame mostly cleared at win")
            elif len(objects_present) <= 2:
                goal_type = GoalType.REACH
                evidence.append("Few objects remain - likely reached goal")
                target_objects = [f"color_{c}" for c in objects_present]
        
        # Check action patterns
        if action_history:
            click_count = sum(1 for a in action_history if a == "ACTION7")
            move_count = sum(1 for a in action_history if a in ["ACTION1", "ACTION2", "ACTION3", "ACTION4"])
            
            if click_count > move_count * 2:
                goal_type = GoalType.COLLECT
                evidence.append(f"Many click actions ({click_count}) suggests collect goal")
        
        # Create or update goal
        existing = self._load_goal(goal_id)
        if existing:
            existing.achieved_count += 1
            existing.confidence = min(1.0, existing.confidence + 0.1)
            existing.evidence.extend(evidence)
            goal = existing
        else:
            goal = InferredGoal(
                goal_id=goal_id,
                game_type=game_type,
                level=level,
                goal_type=goal_type,
                target_objects=target_objects,
                target_regions=target_regions,
                confidence=self.CONFIDENCE_MEDIUM,
                evidence=evidence,
                achieved_count=1
            )
        
        self._save_goal(goal)
        self._goals[goal_id] = goal
        
        logger.info(
            f"[VALENCE] Inferred goal for {game_type} L{level}: "
            f"{goal_type.value} (conf={goal.confidence:.2f})"
        )
        
        return goal
    
    def get_goal(
        self,
        game_type: str,
        level: int
    ) -> Optional[InferredGoal]:
        """
        Get inferred goal for a level.
        
        Args:
            game_type: Game type
            level: Level number
            
        Returns:
            InferredGoal or None
        """
        goal_id = f"goal_{game_type}_{level}"
        
        if goal_id in self._goals:
            return self._goals[goal_id]
        
        goal = self._load_goal(goal_id)
        if goal:
            self._goals[goal_id] = goal
        return goal
    
    def classify_frame_regions(
        self,
        frame: List[List[int]],
        game_type: str,
        grid_size: int = 3
    ) -> List[RegionClassification]:
        """
        Classify regions of a frame based on valence.
        
        Args:
            frame: Current frame
            game_type: Game type for valence lookup
            grid_size: Size of grid regions to classify
            
        Returns:
            List of RegionClassifications
        """
        height = len(frame)
        width = len(frame[0]) if frame else 0
        
        valences = {a.object_id: a for a in self.get_all_valences(game_type)}
        
        regions = []
        region_id = 0
        
        # Divide frame into grid
        step_y = max(1, height // grid_size)
        step_x = max(1, width // grid_size)
        
        for gy in range(grid_size):
            for gx in range(grid_size):
                min_y = gy * step_y
                max_y = min((gy + 1) * step_y, height)
                min_x = gx * step_x
                max_x = min((gx + 1) * step_x, width)
                
                # Analyze region
                positive_count = 0
                negative_count = 0
                has_goal = False
                has_hazard = False
                
                for y in range(min_y, max_y):
                    for x in range(min_x, max_x):
                        color = frame[y][x]
                        if color > 0:
                            obj_id = f"color_{color}"
                            if obj_id in valences:
                                v = valences[obj_id]
                                if v.valence == Valence.POSITIVE:
                                    positive_count += 1
                                    has_goal = True
                                elif v.valence == Valence.NEGATIVE:
                                    negative_count += 1
                                    has_hazard = True
                
                # Determine dominant valence
                if positive_count > negative_count:
                    dominant = Valence.POSITIVE
                elif negative_count > positive_count:
                    dominant = Valence.NEGATIVE
                else:
                    dominant = Valence.NEUTRAL
                
                regions.append(RegionClassification(
                    region_id=f"region_{region_id}",
                    bounds=(min_y, min_x, max_y, max_x),
                    dominant_valence=dominant,
                    contains_goal=has_goal,
                    contains_hazard=has_hazard,
                    entry_score=0.0,  # Would need tracking
                    visit_count=0
                ))
                region_id += 1
        
        return regions
    
    def predict_reward(
        self,
        action: str,
        target_object: Optional[str],
        game_type: str
    ) -> Tuple[float, float]:
        """
        Predict reward for an action.
        
        Args:
            action: Action to take
            target_object: Object being targeted
            game_type: Game type
            
        Returns:
            Tuple of (expected_reward, confidence)
        """
        if not target_object:
            return (0.0, 0.0)
        
        valence = self.get_valence(target_object, game_type)
        if not valence:
            return (0.0, 0.0)
        
        # Map valence to expected reward
        if valence.valence == Valence.POSITIVE:
            expected = 10.0
        elif valence.valence == Valence.NEGATIVE:
            expected = -10.0
        elif valence.valence == Valence.AMBIGUOUS:
            expected = 0.0
        else:
            expected = 0.0
        
        return (expected, valence.confidence)
    
    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================
    
    def _load_valence(
        self,
        object_id: str,
        game_type: str
    ) -> Optional[ValenceAssociation]:
        """Load valence from database."""
        try:
            rows = self.db.execute_query("""
                SELECT * FROM valence_associations
                WHERE object_id = ? AND game_type = ?
            """, (object_id, game_type))
            
            if rows:
                return self._row_to_valence(rows[0])
            return None
            
        except Exception as e:
            logger.warning(f"[VALENCE] Failed to load valence: {e}")
            return None
    
    def _row_to_valence(self, row: Dict[str, Any]) -> Optional[ValenceAssociation]:
        """Convert database row to ValenceAssociation."""
        try:
            evidence = json.loads(row['evidence_json']) if row.get('evidence_json') else []
            return ValenceAssociation(
                object_id=row['object_id'],
                color=row['color'],
                valence=Valence(row['valence']),
                confidence=row['confidence'],
                evidence_count=row['evidence_count'],
                evidence=evidence,
                game_type=row['game_type'],
                created_at=row.get('created_at', ''),
                updated_at=row.get('updated_at', '')
            )
        except Exception as e:
            logger.warning(f"[VALENCE] Failed to parse valence row: {e}")
            return None
    
    def _save_valence(self, assoc: ValenceAssociation) -> None:
        """Save valence to database."""
        try:
            self.db.execute_query("""
                INSERT INTO valence_associations
                (object_id, color, game_type, valence, confidence, evidence_count, 
                 evidence_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(object_id, game_type) DO UPDATE SET
                    valence = excluded.valence,
                    confidence = excluded.confidence,
                    evidence_count = excluded.evidence_count,
                    evidence_json = excluded.evidence_json,
                    updated_at = excluded.updated_at
            """, (
                assoc.object_id,
                assoc.color,
                assoc.game_type,
                assoc.valence.value,
                assoc.confidence,
                assoc.evidence_count,
                json.dumps(assoc.evidence[-10:]),  # Keep last 10 evidence
                assoc.created_at,
                assoc.updated_at
            ))
        except Exception as e:
            logger.error(f"[VALENCE] Failed to save valence: {e}")
    
    def _load_goal(self, goal_id: str) -> Optional[InferredGoal]:
        """Load goal from database."""
        try:
            rows = self.db.execute_query("""
                SELECT * FROM inferred_goals WHERE goal_id = ?
            """, (goal_id,))
            
            if rows:
                row = rows[0]
                return InferredGoal(
                    goal_id=row['goal_id'],
                    game_type=row['game_type'],
                    level=row['level'],
                    goal_type=GoalType(row['goal_type']),
                    target_objects=json.loads(row['target_objects_json'] or '[]'),
                    target_regions=[tuple(r) for r in json.loads(row['target_regions_json'] or '[]')],
                    confidence=row['confidence'],
                    evidence=json.loads(row['evidence_json'] or '[]'),
                    achieved_count=row['achieved_count'],
                    failed_count=row['failed_count']
                )
            return None
            
        except Exception as e:
            logger.warning(f"[VALENCE] Failed to load goal: {e}")
            return None
    
    def _save_goal(self, goal: InferredGoal) -> None:
        """Save goal to database."""
        try:
            self.db.execute_query("""
                INSERT INTO inferred_goals
                (goal_id, game_type, level, goal_type, target_objects_json,
                 target_regions_json, confidence, evidence_json, achieved_count, failed_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(goal_id) DO UPDATE SET
                    goal_type = excluded.goal_type,
                    target_objects_json = excluded.target_objects_json,
                    confidence = excluded.confidence,
                    evidence_json = excluded.evidence_json,
                    achieved_count = excluded.achieved_count,
                    failed_count = excluded.failed_count
            """, (
                goal.goal_id,
                goal.game_type,
                goal.level,
                goal.goal_type.value,
                json.dumps(goal.target_objects),
                json.dumps(goal.target_regions),
                goal.confidence,
                json.dumps(goal.evidence[-20:]),
                goal.achieved_count,
                goal.failed_count
            ))
        except Exception as e:
            logger.error(f"[VALENCE] Failed to save goal: {e}")
    
    def _find_objects_in_frame(self, frame: List[List[int]]) -> Set[int]:
        """Find all object colors in frame."""
        colors = set()
        for row in frame:
            for color in row:
                if color > 0:
                    colors.add(color)
        return colors
