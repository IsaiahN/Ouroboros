"""
Universal Patterns - Cross-Game Pattern Transfer
================================================

Manages patterns that transfer across games:
- Universal rules (gravity, collision)
- Cross-game pattern matching
- Transferable knowledge packaging

Design Principles:
- Explicit pattern abstraction levels
- Clear evidence tracking for confidence
- Patterns must prove themselves before transfer
"""

import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class PatternScope(Enum):
    """Scope of pattern applicability."""
    GAME_SPECIFIC = "game_specific"     # Only this game
    GAME_TYPE = "game_type"             # This type of game (sp80, gd87, etc)
    UNIVERSAL = "universal"             # All games
    CONDITIONAL = "conditional"         # Depends on conditions


class PatternType(Enum):
    """Types of patterns."""
    CONTROL = "control"           # How to control objects
    NAVIGATION = "navigation"     # How to navigate
    INTERACTION = "interaction"   # Object interactions
    SEQUENCE = "sequence"         # Action sequences
    SPATIAL = "spatial"          # Spatial relationships
    TEMPORAL = "temporal"        # Timing patterns
    RULE = "rule"                # Game rules


@dataclass
class UniversalPattern:
    """A pattern that may transfer across games."""
    pattern_id: str
    pattern_type: PatternType
    scope: PatternScope

    # Pattern definition
    description: str
    conditions: Dict[str, Any]  # When pattern applies
    predictions: Dict[str, Any]  # What pattern predicts

    # Evidence tracking
    success_count: int = 0
    failure_count: int = 0
    games_verified: Set[str] = field(default_factory=set)
    games_failed: Set[str] = field(default_factory=set)

    # Metadata
    created_at: str = ""
    last_used: str = ""
    creator_game: str = ""

    @property
    def confidence(self) -> float:
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.5
        return self.success_count / total

    @property
    def is_universal(self) -> bool:
        return len(self.games_verified) >= 3 and self.confidence >= 0.7

    def to_dict(self) -> Dict[str, Any]:
        return {
            'pattern_id': self.pattern_id,
            'pattern_type': self.pattern_type.value,
            'scope': self.scope.value,
            'description': self.description,
            'conditions': self.conditions,
            'predictions': self.predictions,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'games_verified': list(self.games_verified),
            'games_failed': list(self.games_failed),
            'created_at': self.created_at,
            'creator_game': self.creator_game
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UniversalPattern':
        return cls(
            pattern_id=data['pattern_id'],
            pattern_type=PatternType(data.get('pattern_type', 'rule')),
            scope=PatternScope(data.get('scope', 'game_specific')),
            description=data.get('description', ''),
            conditions=data.get('conditions', {}),
            predictions=data.get('predictions', {}),
            success_count=data.get('success_count', 0),
            failure_count=data.get('failure_count', 0),
            games_verified=set(data.get('games_verified', [])),
            games_failed=set(data.get('games_failed', [])),
            created_at=data.get('created_at', ''),
            creator_game=data.get('creator_game', '')
        )


@dataclass
class TransferableKnowledge:
    """Knowledge package for a new game."""
    game_type: str
    patterns: List[UniversalPattern]
    confidence_weighted_score: float
    applicable_rules: List[str]
    warnings: List[str]


class UniversalPatternEngine:
    """
    Manages universal patterns and cross-game transfer.

    Usage:
        engine = UniversalPatternEngine(db_path)

        # Store a pattern discovered in a game
        engine.store_pattern(
            pattern_type=PatternType.CONTROL,
            description="ACTION1 moves player up",
            conditions={'has_player': True},
            predictions={'direction': 'up', 'object': 'player'},
            game_type="sp80"
        )

        # When pattern works in another game
        engine.verify_pattern(pattern_id, game_type="gd87", success=True)

        # Get transferable knowledge for new game
        knowledge = engine.get_transferable_knowledge("new_game")
        print(f"Found {len(knowledge.patterns)} applicable patterns")
    """

    # Thresholds
    MIN_CONFIDENCE_FOR_TRANSFER = 0.6
    MIN_GAMES_FOR_UNIVERSAL = 3

    def __init__(self, db_path: str = "core_data.db"):
        """
        Initialize universal pattern engine.

        Args:
            db_path: Path to database
        """
        try:
            from database_interface import DatabaseInterface
            self.db = DatabaseInterface(db_path)
        except Exception as e:
            raise RuntimeError(f"[UNIVERSAL] Failed to connect to database: {e}")

        self._cache: Dict[str, UniversalPattern] = {}
        self._ensure_tables()
        self._load_core_patterns()
        logger.info("[UNIVERSAL] Initialized")

    def _ensure_tables(self) -> None:
        """Ensure required tables exist."""
        try:
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS universal_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    pattern_type TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    description TEXT,
                    conditions_json TEXT,
                    predictions_json TEXT,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    games_verified_json TEXT,
                    games_failed_json TEXT,
                    creator_game TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP
                )
            """)

            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_universal_patterns_type
                ON universal_patterns(pattern_type)
            """)

            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_universal_patterns_scope
                ON universal_patterns(scope)
            """)

            logger.debug("[UNIVERSAL] Tables verified")
        except Exception as e:
            logger.error(f"[UNIVERSAL] Table creation failed: {e}")
            raise

    def _load_core_patterns(self) -> None:
        """Load/create core universal patterns."""
        core_patterns = [
            {
                'pattern_id': 'core_movement_up',
                'pattern_type': PatternType.CONTROL,
                'scope': PatternScope.UNIVERSAL,
                'description': 'ACTION1 typically moves controlled object up',
                'conditions': {'has_controllable_object': True},
                'predictions': {'movement_direction': 'up'}
            },
            {
                'pattern_id': 'core_movement_down',
                'pattern_type': PatternType.CONTROL,
                'scope': PatternScope.UNIVERSAL,
                'description': 'ACTION2 typically moves controlled object down',
                'conditions': {'has_controllable_object': True},
                'predictions': {'movement_direction': 'down'}
            },
            {
                'pattern_id': 'core_movement_left',
                'pattern_type': PatternType.CONTROL,
                'scope': PatternScope.UNIVERSAL,
                'description': 'ACTION3 typically moves controlled object left',
                'conditions': {'has_controllable_object': True},
                'predictions': {'movement_direction': 'left'}
            },
            {
                'pattern_id': 'core_movement_right',
                'pattern_type': PatternType.CONTROL,
                'scope': PatternScope.UNIVERSAL,
                'description': 'ACTION4 typically moves controlled object right',
                'conditions': {'has_controllable_object': True},
                'predictions': {'movement_direction': 'right'}
            },
            {
                'pattern_id': 'core_click_interaction',
                'pattern_type': PatternType.INTERACTION,
                'scope': PatternScope.UNIVERSAL,
                'description': 'ACTION7 at coordinates interacts with object at that position',
                'conditions': {'has_clickable_objects': True},
                'predictions': {'interaction_type': 'click'}
            },
            {
                'pattern_id': 'core_collision_boundary',
                'pattern_type': PatternType.SPATIAL,
                'scope': PatternScope.UNIVERSAL,
                'description': 'Objects cannot move through solid boundaries',
                'conditions': {'has_boundaries': True},
                'predictions': {'blocked_by_boundary': True}
            }
        ]

        for pattern_data in core_patterns:
            pattern_id = pattern_data['pattern_id']
            if pattern_id not in self._cache:
                existing = self._load_pattern(pattern_id)
                if not existing:
                    pattern = UniversalPattern(
                        pattern_id=pattern_id,
                        pattern_type=pattern_data['pattern_type'],
                        scope=pattern_data['scope'],
                        description=pattern_data['description'],
                        conditions=pattern_data['conditions'],
                        predictions=pattern_data['predictions'],
                        success_count=10,  # Core patterns start with high confidence
                        failure_count=0,
                        created_at=datetime.now().isoformat()
                    )
                    self._save_pattern(pattern)
                    self._cache[pattern_id] = pattern
                else:
                    self._cache[pattern_id] = existing

    def store_pattern(
        self,
        pattern_type: PatternType,
        description: str,
        conditions: Dict[str, Any],
        predictions: Dict[str, Any],
        game_type: str
    ) -> UniversalPattern:
        """
        Store a new pattern discovered in gameplay.

        Args:
            pattern_type: Type of pattern
            description: Human-readable description
            conditions: When pattern applies
            predictions: What pattern predicts
            game_type: Game where pattern was discovered

        Returns:
            Created UniversalPattern
        """
        # Generate pattern ID based on content
        pattern_id = self._generate_pattern_id(pattern_type, conditions, predictions)

        # Check if similar pattern exists
        existing = self._find_similar_pattern(conditions, predictions)
        if existing:
            existing.success_count += 1
            existing.games_verified.add(game_type)
            existing.last_used = datetime.now().isoformat()
            self._update_scope(existing)
            self._save_pattern(existing)
            logger.debug(f"[UNIVERSAL] Updated existing pattern {existing.pattern_id}")
            return existing

        # Create new pattern
        pattern = UniversalPattern(
            pattern_id=pattern_id,
            pattern_type=pattern_type,
            scope=PatternScope.GAME_SPECIFIC,
            description=description,
            conditions=conditions,
            predictions=predictions,
            success_count=1,
            failure_count=0,
            games_verified={game_type},
            created_at=datetime.now().isoformat(),
            last_used=datetime.now().isoformat(),
            creator_game=game_type
        )

        self._cache[pattern_id] = pattern
        self._save_pattern(pattern)

        logger.info(f"[UNIVERSAL] Stored pattern {pattern_id}: {description}")
        return pattern

    def verify_pattern(
        self,
        pattern_id: str,
        game_type: str,
        success: bool
    ) -> None:
        """
        Verify a pattern's applicability in a game.

        Args:
            pattern_id: Pattern to verify
            game_type: Game where verification happened
            success: Whether pattern held true
        """
        pattern = self._get_pattern(pattern_id)
        if not pattern:
            logger.warning(f"[UNIVERSAL] Pattern {pattern_id} not found for verification")
            return

        if success:
            pattern.success_count += 1
            pattern.games_verified.add(game_type)
        else:
            pattern.failure_count += 1
            pattern.games_failed.add(game_type)

        pattern.last_used = datetime.now().isoformat()
        self._update_scope(pattern)
        self._save_pattern(pattern)

        logger.debug(
            f"[UNIVERSAL] Verified {pattern_id} in {game_type}: "
            f"success={success}, confidence={pattern.confidence:.2f}"
        )

    def get_transferable_knowledge(
        self,
        game_type: str,
        min_confidence: float = 0.6
    ) -> TransferableKnowledge:
        """
        Get transferable knowledge for a new game.

        Args:
            game_type: New game to get knowledge for
            min_confidence: Minimum pattern confidence

        Returns:
            TransferableKnowledge package
        """
        # Load all patterns
        all_patterns = self._load_all_patterns()

        applicable = []
        warnings = []
        total_score = 0.0

        for pattern in all_patterns:
            # Skip patterns that failed in this game type
            if game_type in pattern.games_failed:
                warnings.append(
                    f"Pattern '{pattern.description}' previously failed in {game_type}"
                )
                continue

            # Include universal patterns and high-confidence patterns
            if pattern.scope == PatternScope.UNIVERSAL:
                applicable.append(pattern)
                total_score += pattern.confidence
            elif pattern.confidence >= min_confidence:
                # Check if same game type prefix
                pattern_prefix = pattern.creator_game[:2] if pattern.creator_game else ""
                game_prefix = game_type[:2] if game_type else ""

                if pattern_prefix == game_prefix:
                    applicable.append(pattern)
                    total_score += pattern.confidence * 0.8  # Discount for same-family

        # Generate applicable rules
        rules = []
        for pattern in applicable:
            if pattern.confidence >= 0.8:
                rules.append(pattern.description)

        avg_score = total_score / len(applicable) if applicable else 0.0

        logger.info(
            f"[UNIVERSAL] Transfer to {game_type}: "
            f"{len(applicable)} patterns, avg_conf={avg_score:.2f}"
        )

        return TransferableKnowledge(
            game_type=game_type,
            patterns=applicable,
            confidence_weighted_score=avg_score,
            applicable_rules=rules,
            warnings=warnings
        )

    def get_patterns_by_type(
        self,
        pattern_type: PatternType,
        min_confidence: float = 0.5
    ) -> List[UniversalPattern]:
        """
        Get patterns of a specific type.

        Args:
            pattern_type: Type to filter by
            min_confidence: Minimum confidence

        Returns:
            List of matching patterns
        """
        try:
            rows = self.db.execute_query("""
                SELECT * FROM universal_patterns
                WHERE pattern_type = ?
                AND CAST(success_count AS REAL) / (success_count + failure_count + 1) >= ?
                ORDER BY success_count DESC
            """, (pattern_type.value, min_confidence))

            patterns = []
            for row in rows:
                pattern = self._row_to_pattern(row)
                if pattern:
                    patterns.append(pattern)

            return patterns

        except Exception as e:
            logger.error(f"[UNIVERSAL] Failed to get patterns by type: {e}")
            return []

    def get_universal_patterns(self) -> List[UniversalPattern]:
        """
        Get all patterns that have achieved universal status.

        Returns:
            List of universal patterns
        """
        try:
            rows = self.db.execute_query("""
                SELECT * FROM universal_patterns
                WHERE scope = 'universal'
                ORDER BY success_count DESC
            """)

            patterns = []
            for row in rows:
                pattern = self._row_to_pattern(row)
                if pattern:
                    patterns.append(pattern)

            return patterns

        except Exception as e:
            logger.error(f"[UNIVERSAL] Failed to get universal patterns: {e}")
            return []

    def predict_action_outcome(
        self,
        action: str,
        game_type: str,
        _frame_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Predict outcome of action based on universal patterns.

        Args:
            action: Action to predict
            game_type: Current game
            frame_context: Optional context about current frame

        Returns:
            Dict with predictions and confidence
        """
        predictions = {
            'expected_outcome': None,
            'confidence': 0.0,
            'patterns_used': []
        }

        # Map action to movement
        action_to_direction = {
            'ACTION1': 'up',
            'ACTION2': 'down',
            'ACTION3': 'left',
            'ACTION4': 'right'
        }

        if action in action_to_direction:
            direction = action_to_direction[action]
            pattern_id = f'core_movement_{direction}'

            pattern = self._get_pattern(pattern_id)
            if pattern:
                predictions['expected_outcome'] = {
                    'type': 'movement',
                    'direction': direction
                }
                predictions['confidence'] = pattern.confidence
                predictions['patterns_used'].append(pattern.pattern_id)

        elif action == 'ACTION7':
            pattern = self._get_pattern('core_click_interaction')
            if pattern:
                predictions['expected_outcome'] = {
                    'type': 'interaction',
                    'effect': 'click'
                }
                predictions['confidence'] = pattern.confidence
                predictions['patterns_used'].append(pattern.pattern_id)

        return predictions

    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================

    def _get_pattern(self, pattern_id: str) -> Optional[UniversalPattern]:
        """Get pattern from cache or database."""
        if pattern_id in self._cache:
            return self._cache[pattern_id]

        pattern = self._load_pattern(pattern_id)
        if pattern:
            self._cache[pattern_id] = pattern
        return pattern

    def _load_pattern(self, pattern_id: str) -> Optional[UniversalPattern]:
        """Load pattern from database."""
        try:
            rows = self.db.execute_query("""
                SELECT * FROM universal_patterns WHERE pattern_id = ?
            """, (pattern_id,))

            if rows:
                return self._row_to_pattern(rows[0])
            return None

        except Exception as e:
            logger.warning(f"[UNIVERSAL] Failed to load pattern {pattern_id}: {e}")
            return None

    def _row_to_pattern(self, row: Dict[str, Any]) -> Optional[UniversalPattern]:
        """Convert database row to UniversalPattern."""
        try:
            return UniversalPattern(
                pattern_id=row['pattern_id'],
                pattern_type=PatternType(row['pattern_type']),
                scope=PatternScope(row['scope']),
                description=row.get('description', ''),
                conditions=json.loads(row.get('conditions_json') or '{}'),
                predictions=json.loads(row.get('predictions_json') or '{}'),
                success_count=row.get('success_count', 0),
                failure_count=row.get('failure_count', 0),
                games_verified=set(json.loads(row.get('games_verified_json') or '[]')),
                games_failed=set(json.loads(row.get('games_failed_json') or '[]')),
                created_at=row.get('created_at', ''),
                creator_game=row.get('creator_game', '')
            )
        except Exception as e:
            logger.warning(f"[UNIVERSAL] Failed to parse pattern row: {e}")
            return None

    def _save_pattern(self, pattern: UniversalPattern) -> None:
        """Save pattern to database."""
        try:
            self.db.execute_query("""
                INSERT INTO universal_patterns
                (pattern_id, pattern_type, scope, description, conditions_json,
                 predictions_json, success_count, failure_count, games_verified_json,
                 games_failed_json, creator_game, created_at, last_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(pattern_id) DO UPDATE SET
                    scope = excluded.scope,
                    success_count = excluded.success_count,
                    failure_count = excluded.failure_count,
                    games_verified_json = excluded.games_verified_json,
                    games_failed_json = excluded.games_failed_json,
                    last_used = excluded.last_used
            """, (
                pattern.pattern_id,
                pattern.pattern_type.value,
                pattern.scope.value,
                pattern.description,
                json.dumps(pattern.conditions),
                json.dumps(pattern.predictions),
                pattern.success_count,
                pattern.failure_count,
                json.dumps(list(pattern.games_verified)),
                json.dumps(list(pattern.games_failed)),
                pattern.creator_game,
                pattern.created_at,
                pattern.last_used
            ))
        except Exception as e:
            logger.error(f"[UNIVERSAL] Failed to save pattern: {e}")

    def _load_all_patterns(self) -> List[UniversalPattern]:
        """Load all patterns from database."""
        try:
            rows = self.db.execute_query("""
                SELECT * FROM universal_patterns
                ORDER BY success_count DESC
            """)

            patterns = []
            for row in rows:
                pattern = self._row_to_pattern(row)
                if pattern:
                    patterns.append(pattern)
                    self._cache[pattern.pattern_id] = pattern

            return patterns

        except Exception as e:
            logger.error(f"[UNIVERSAL] Failed to load all patterns: {e}")
            return []

    def _generate_pattern_id(
        self,
        pattern_type: PatternType,
        conditions: Dict[str, Any],
        predictions: Dict[str, Any]
    ) -> str:
        """Generate unique pattern ID."""
        content_hash = hash(str(sorted(conditions.items())) + str(sorted(predictions.items())))
        return f"pat_{pattern_type.value}_{abs(content_hash) % 100000:05d}"

    def _find_similar_pattern(
        self,
        conditions: Dict[str, Any],
        predictions: Dict[str, Any]
    ) -> Optional[UniversalPattern]:
        """Find existing pattern with similar conditions/predictions."""
        for pattern in self._cache.values():
            if pattern.conditions == conditions and pattern.predictions == predictions:
                return pattern
        return None

    def _update_scope(self, pattern: UniversalPattern) -> None:
        """Update pattern scope based on evidence."""
        verified_count = len(pattern.games_verified)

        if verified_count >= self.MIN_GAMES_FOR_UNIVERSAL and pattern.confidence >= 0.7:
            pattern.scope = PatternScope.UNIVERSAL
        elif verified_count >= 2 and pattern.confidence >= 0.6:
            pattern.scope = PatternScope.GAME_TYPE
        elif len(pattern.games_failed) > verified_count:
            pattern.scope = PatternScope.CONDITIONAL
