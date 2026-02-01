import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
Lessons Extractor - Learn from Game Outcomes
============================================

Extracts transferable lessons from completed games:
- What worked well (for viral package creation)
- What failed (for pariah pattern detection)
- Rule inductions (why things worked)
- Efficiency insights (optimizer feedback)

This replaces the deprecated lessons_learned_engine.py with a
cleaner implementation that integrates with the postgame module.

Key Responsibilities:
1. Analyze action sequences to find effective patterns
2. Identify failures and their causes
3. Extract rule hypotheses from successful plays
4. Generate lessons for network knowledge sharing

Following Rules:
- Rule 2: Database-only storage
- Rule 3: Clean integration
- Rule 11: No Unicode emojis
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from engines.engine_logger import get_engine_logger

logger = get_engine_logger("lessons_extractor")

if TYPE_CHECKING:
    from database_interface import DatabaseInterface


@dataclass
class Lesson:
    """A transferable lesson learned from gameplay."""
    lesson_id: str
    lesson_type: str  # 'success', 'failure', 'rule', 'optimization'
    game_id: str
    game_type: str
    level_number: int

    # What was learned
    description: str
    pattern: str  # Action pattern or condition
    confidence: float  # 0.0-1.0

    # Context
    action_sequence: List[str] = field(default_factory=list)
    triggering_actions: List[int] = field(default_factory=list)  # Indices
    score_impact: float = 0.0

    # Transferability
    domain_tags: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'lesson_id': self.lesson_id,
            'lesson_type': self.lesson_type,
            'game_id': self.game_id,
            'game_type': self.game_type,
            'level_number': self.level_number,
            'description': self.description,
            'pattern': self.pattern,
            'confidence': self.confidence,
            'action_sequence': self.action_sequence,
            'triggering_actions': self.triggering_actions,
            'score_impact': self.score_impact,
            'domain_tags': self.domain_tags,
            'prerequisites': self.prerequisites,
        }


@dataclass
class LessonsResult:
    """Result of lessons extraction."""
    success_lessons: List[Lesson]
    failure_lessons: List[Lesson]
    rule_lessons: List[Lesson]
    optimization_lessons: List[Lesson]
    total_lessons: int

    @property
    def all_lessons(self) -> List[Lesson]:
        return (
            self.success_lessons +
            self.failure_lessons +
            self.rule_lessons +
            self.optimization_lessons
        )


class LessonsExtractor:
    """
    Extracts transferable lessons from game outcomes.

    This is the "wisdom extraction system" - it converts raw game
    experience into structured knowledge that can spread virally.
    """

    def __init__(self, db: 'DatabaseInterface'):
        self.db = db
        self._extractor_id = f"lessons_{uuid.uuid4().hex[:8]}"

    def extract_lessons(
        self,
        game_id: str,
        game_type: str,
        agent_id: str,
        action_sequence: List[str],
        score_history: List[float],
        is_win: bool,
        is_full_win: bool,
        levels_completed: int,
        frame_history: Optional[List[Any]] = None,
    ) -> LessonsResult:
        """
        Extract all lessons from a completed game.

        Args:
            game_id: The game identifier
            game_type: Type of game (e.g., 'SP80')
            agent_id: Agent that played
            action_sequence: List of actions taken
            score_history: Score after each action
            is_win: Whether agent won
            is_full_win: Whether all levels completed
            levels_completed: Number of levels finished
            frame_history: Optional frame data for deeper analysis

        Returns:
            LessonsResult with all extracted lessons
        """
        success_lessons = []
        failure_lessons = []
        rule_lessons = []
        optimization_lessons = []

        # Extract success patterns
        if is_win or is_full_win:
            success_lessons.extend(
                self._extract_success_patterns(
                    game_id, game_type, action_sequence, score_history, levels_completed
                )
            )

        # Extract failure patterns (even from wins - some sub-patterns may have failed)
        failure_lessons.extend(
            self._extract_failure_patterns(
                game_id, game_type, action_sequence, score_history
            )
        )

        # Induce rules from patterns
        rule_lessons.extend(
            self._induce_rules(
                game_id, game_type, action_sequence, score_history, frame_history
            )
        )

        # Extract optimization insights
        optimization_lessons.extend(
            self._extract_optimization_insights(
                game_id, game_type, action_sequence, score_history
            )
        )

        result = LessonsResult(
            success_lessons=success_lessons,
            failure_lessons=failure_lessons,
            rule_lessons=rule_lessons,
            optimization_lessons=optimization_lessons,
            total_lessons=len(success_lessons) + len(failure_lessons) +
                          len(rule_lessons) + len(optimization_lessons),
        )

        # Store lessons in database (Rule 2)
        self._store_lessons(agent_id, result)

        return result

    def _extract_success_patterns(
        self,
        game_id: str,
        game_type: str,
        action_sequence: List[str],
        score_history: List[float],
        levels_completed: int,
    ) -> List[Lesson]:
        """Extract patterns that led to success."""
        lessons = []

        # Find score increases
        score_increases = self._find_score_increases(score_history)

        for idx, increase in score_increases:
            # Get context around the successful action
            start_idx = max(0, idx - 3)
            end_idx = min(len(action_sequence), idx + 2)
            context = action_sequence[start_idx:end_idx]

            lesson = Lesson(
                lesson_id=f"suc_{uuid.uuid4().hex[:8]}",
                lesson_type='success',
                game_id=game_id,
                game_type=game_type,
                level_number=self._estimate_level(idx, action_sequence, score_history),
                description=f"Action sequence led to +{increase:.1f} score",
                pattern=self._create_pattern_signature(context),
                confidence=min(0.9, 0.3 + (increase / 100.0)),
                action_sequence=context,
                triggering_actions=[idx - start_idx],
                score_impact=increase,
                domain_tags=[game_type[:2]],  # First 2 chars as domain
            )
            lessons.append(lesson)

        # Extract full-game success pattern if won
        if levels_completed > 0:
            lesson = Lesson(
                lesson_id=f"win_{uuid.uuid4().hex[:8]}",
                lesson_type='success',
                game_id=game_id,
                game_type=game_type,
                level_number=levels_completed,
                description=f"Complete win sequence ({len(action_sequence)} actions)",
                pattern=f"FULL_WIN:{game_type}",
                confidence=0.95,
                action_sequence=action_sequence[:50],  # Store first 50 actions
                triggering_actions=[],
                score_impact=score_history[-1] if score_history else 0.0,
                domain_tags=[game_type[:2], 'full_win'],
            )
            lessons.append(lesson)

        return lessons

    def _extract_failure_patterns(
        self,
        game_id: str,
        game_type: str,
        action_sequence: List[str],
        score_history: List[float],
    ) -> List[Lesson]:
        """Extract patterns that led to failure or wasted actions."""
        lessons = []

        # Find score plateaus (wasted actions)
        plateaus = self._find_plateaus(score_history, min_length=5)

        for start_idx, length in plateaus:
            end_idx = min(start_idx + length, len(action_sequence))
            wasted = action_sequence[start_idx:end_idx]

            lesson = Lesson(
                lesson_id=f"fail_{uuid.uuid4().hex[:8]}",
                lesson_type='failure',
                game_id=game_id,
                game_type=game_type,
                level_number=self._estimate_level(start_idx, action_sequence, score_history),
                description=f"No progress for {length} consecutive actions",
                pattern=self._create_pattern_signature(wasted),
                confidence=0.6 + (0.04 * min(length, 10)),  # More confident with longer plateaus
                action_sequence=wasted,
                triggering_actions=list(range(len(wasted))),
                score_impact=0.0,
                domain_tags=[game_type[:2], 'wasted'],
            )
            lessons.append(lesson)

        # Find score decreases (negative actions)
        decreases = self._find_score_decreases(score_history)

        for idx, decrease in decreases:
            if idx >= len(action_sequence):
                continue

            context_start = max(0, idx - 2)
            context = action_sequence[context_start:idx + 1]

            lesson = Lesson(
                lesson_id=f"neg_{uuid.uuid4().hex[:8]}",
                lesson_type='failure',
                game_id=game_id,
                game_type=game_type,
                level_number=self._estimate_level(idx, action_sequence, score_history),
                description=f"Action caused -{abs(decrease):.1f} score loss",
                pattern=self._create_pattern_signature(context),
                confidence=min(0.85, 0.4 + (abs(decrease) / 50.0)),
                action_sequence=context,
                triggering_actions=[len(context) - 1],
                score_impact=decrease,
                domain_tags=[game_type[:2], 'harmful'],
            )
            lessons.append(lesson)

        return lessons

    def _induce_rules(
        self,
        game_id: str,
        game_type: str,
        action_sequence: List[str],
        score_history: List[float],
        frame_history: Optional[List[Any]] = None,
    ) -> List[Lesson]:
        """Induce rules from repeated patterns."""
        lessons = []

        # Find repeated action sequences that consistently score
        patterns = self._find_repeated_patterns(action_sequence, score_history)

        for pattern, occurrences, avg_score_change in patterns:
            if len(occurrences) < 2:
                continue

            consistency = self._calculate_consistency(occurrences, score_history)

            lesson = Lesson(
                lesson_id=f"rule_{uuid.uuid4().hex[:8]}",
                lesson_type='rule',
                game_id=game_id,
                game_type=game_type,
                level_number=0,  # Rules are level-agnostic
                description=f"Pattern '{pattern}' repeats {len(occurrences)}x with avg +{avg_score_change:.1f}",
                pattern=pattern,
                confidence=min(0.9, 0.3 + (consistency * 0.4) + (len(occurrences) * 0.1)),
                action_sequence=pattern.split(','),
                triggering_actions=occurrences,
                score_impact=avg_score_change,
                domain_tags=[game_type[:2], 'rule_induced'],
            )
            lessons.append(lesson)

        return lessons

    def _extract_optimization_insights(
        self,
        game_id: str,
        game_type: str,
        action_sequence: List[str],
        score_history: List[float],
    ) -> List[Lesson]:
        """Extract insights for optimization (fewer actions)."""
        lessons = []

        # Find redundant action pairs (A-B-A patterns)
        redundants = self._find_redundant_patterns(action_sequence)

        for idx, pattern in redundants:
            lesson = Lesson(
                lesson_id=f"opt_{uuid.uuid4().hex[:8]}",
                lesson_type='optimization',
                game_id=game_id,
                game_type=game_type,
                level_number=self._estimate_level(idx, action_sequence, score_history),
                description=f"Redundant pattern '{pattern}' could be eliminated",
                pattern=pattern,
                confidence=0.7,
                action_sequence=pattern.split(','),
                triggering_actions=[idx],
                score_impact=0.0,
                domain_tags=[game_type[:2], 'optimize'],
            )
            lessons.append(lesson)

        # Find fastest score increases (most efficient actions)
        if score_history and len(score_history) > 1:
            best_actions = self._find_most_efficient_actions(score_history, top_n=3)

            for idx, efficiency in best_actions:
                if idx >= len(action_sequence):
                    continue

                lesson = Lesson(
                    lesson_id=f"eff_{uuid.uuid4().hex[:8]}",
                    lesson_type='optimization',
                    game_id=game_id,
                    game_type=game_type,
                    level_number=self._estimate_level(idx, action_sequence, score_history),
                    description=f"High-efficiency action (score/action ratio: {efficiency:.2f})",
                    pattern=action_sequence[idx],
                    confidence=0.8,
                    action_sequence=[action_sequence[idx]],
                    triggering_actions=[idx],
                    score_impact=efficiency,
                    domain_tags=[game_type[:2], 'efficient'],
                )
                lessons.append(lesson)

        return lessons

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _find_score_increases(
        self,
        score_history: List[float]
    ) -> List[Tuple[int, float]]:
        """Find indices where score increased."""
        increases = []
        for i in range(1, len(score_history)):
            delta = score_history[i] - score_history[i - 1]
            if delta > 0:
                increases.append((i, delta))
        return increases

    def _find_score_decreases(
        self,
        score_history: List[float]
    ) -> List[Tuple[int, float]]:
        """Find indices where score decreased."""
        decreases = []
        for i in range(1, len(score_history)):
            delta = score_history[i] - score_history[i - 1]
            if delta < 0:
                decreases.append((i, delta))
        return decreases

    def _find_plateaus(
        self,
        score_history: List[float],
        min_length: int = 5
    ) -> List[Tuple[int, int]]:
        """Find sequences where score didn't change."""
        plateaus = []
        if not score_history:
            return plateaus

        start = 0
        for i in range(1, len(score_history)):
            if score_history[i] != score_history[start]:
                length = i - start
                if length >= min_length:
                    plateaus.append((start, length))
                start = i

        # Check final plateau
        length = len(score_history) - start
        if length >= min_length:
            plateaus.append((start, length))

        return plateaus

    def _find_repeated_patterns(
        self,
        action_sequence: List[str],
        score_history: List[float],
        pattern_length: int = 3
    ) -> List[Tuple[str, List[int], float]]:
        """Find action patterns that repeat with consistent scores."""
        patterns: Dict[str, List[Tuple[int, float]]] = {}

        for i in range(len(action_sequence) - pattern_length + 1):
            pattern = ','.join(action_sequence[i:i + pattern_length])

            # Calculate score change for this pattern
            if i + pattern_length < len(score_history):
                score_change = score_history[i + pattern_length] - score_history[i]
            else:
                score_change = 0.0

            if pattern not in patterns:
                patterns[pattern] = []
            patterns[pattern].append((i, score_change))

        # Filter to repeated patterns with positive effect
        results = []
        for pattern, occurrences in patterns.items():
            if len(occurrences) >= 2:
                avg_change = sum(sc for _, sc in occurrences) / len(occurrences)
                if avg_change > 0:
                    indices = [idx for idx, _ in occurrences]
                    results.append((pattern, indices, avg_change))

        return sorted(results, key=lambda x: x[2], reverse=True)[:5]

    def _find_redundant_patterns(
        self,
        action_sequence: List[str]
    ) -> List[Tuple[int, str]]:
        """Find A-B-A type patterns that waste actions."""
        redundants = []
        for i in range(len(action_sequence) - 2):
            a, b, c = action_sequence[i:i + 3]
            if a == c and a != b:
                # A-B-A pattern (possibly redundant)
                redundants.append((i, f"{a},{b},{a}"))
        return redundants

    def _find_most_efficient_actions(
        self,
        score_history: List[float],
        top_n: int = 3
    ) -> List[Tuple[int, float]]:
        """Find actions with highest score impact."""
        efficiencies = []
        for i in range(1, len(score_history)):
            delta = score_history[i] - score_history[i - 1]
            if delta > 0:
                efficiencies.append((i, delta))

        return sorted(efficiencies, key=lambda x: x[1], reverse=True)[:top_n]

    def _create_pattern_signature(self, actions: List[str]) -> str:
        """Create a compact signature for an action sequence."""
        return ','.join(actions)

    def _estimate_level(
        self,
        action_idx: int,
        action_sequence: List[str],
        score_history: List[float]
    ) -> int:
        """Estimate which level an action occurred in."""
        # Simple heuristic: major score jumps indicate level transitions
        level = 1
        for i in range(1, min(action_idx + 1, len(score_history))):
            if i < len(score_history):
                delta = score_history[i] - score_history[i - 1]
                if delta > 50:  # Large jump suggests level completion
                    level += 1
        return level

    def _calculate_consistency(
        self,
        occurrences: List[int],
        score_history: List[float]
    ) -> float:
        """Calculate how consistent a pattern's effect is."""
        if len(occurrences) < 2:
            return 0.0

        effects = []
        for idx in occurrences:
            if idx + 1 < len(score_history):
                effects.append(score_history[idx + 1] - score_history[idx])

        if not effects:
            return 0.0

        mean = sum(effects) / len(effects)
        variance = sum((e - mean) ** 2 for e in effects) / len(effects)

        # Lower variance = higher consistency
        return max(0.0, 1.0 - (variance / 100.0))

    def _store_lessons(self, agent_id: str, result: LessonsResult) -> None:
        """Store lessons in database (Rule 2)."""
        try:
            for lesson in result.all_lessons:
                self.db.execute("""
                    INSERT INTO lessons_learned (
                        lesson_id, lesson_type, game_id, game_type, level_number,
                        agent_id, description, pattern, confidence, score_impact,
                        domain_tags, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    lesson.lesson_id,
                    lesson.lesson_type,
                    lesson.game_id,
                    lesson.game_type,
                    lesson.level_number,
                    agent_id,
                    lesson.description,
                    lesson.pattern,
                    lesson.confidence,
                    lesson.score_impact,
                    json.dumps(lesson.domain_tags),
                    datetime.now().isoformat(),
                ))
        except Exception as e:
            # Table may not exist yet - log but don't fail
            logger.warning("Failed to store lessons", exc=e)
