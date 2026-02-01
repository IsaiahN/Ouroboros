import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
Post-Game Orchestrator - Single Entry Point for Post-Game Processing
====================================================================

This is THE entry point for all post-game processing.
Call this from game_loop.py when a game ends.

Coordinates in order:
1. Fitness Calculation - Evolutionary rewards from ARC performance
2. Lessons Extraction - What worked, what failed, why
3. Replay Learning Analysis - Summary of any replay learning that occurred
4. Sequence Storage - If this was a winning game
5. Database Updates - wA/wB persistence, agent stats, etc.

Usage:
    from engines.postgame import PostGameProcessor

    processor = PostGameProcessor(db)
    result = processor.process_game_end(
        game_result=result,
        agent_id=agent_id,
        action_sequence=actions,
        score_history=scores,
        frame_history=frames,  # Optional
    )

Following Rules:
- Rule 2: Database-only storage
- Rule 3: Clean integration
- Rule 10: Single source of truth for post-game processing
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from engines.engine_logger import get_engine_logger

logger = get_engine_logger("postgame_orchestrator")

from .fitness_calculator import FitnessCalculator, FitnessConfig, FitnessResult
from .lessons_extractor import LessonsExtractor, LessonsResult

if TYPE_CHECKING:
    from database_interface import DatabaseInterface


@dataclass
class GameEndResult:
    """Input for post-game processing."""
    game_id: str
    game_type: str
    agent_id: str

    # Scores
    final_score: float
    win_score: float

    # Completion
    is_win: bool
    is_full_win: bool
    levels_completed: int
    win_levels: int

    # Actions
    total_actions: int
    action_sequence: List[str] = field(default_factory=list)
    score_history: List[float] = field(default_factory=list)

    # Optional extra data
    frame_history: Optional[List[Any]] = None
    duration_seconds: float = 0.0
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for database storage or RLVR processing."""
        return {
            'game_id': self.game_id,
            'game_type': self.game_type,
            'agent_id': self.agent_id,
            'final_score': self.final_score,
            'win_score': self.win_score,
            'win_detected': self.is_win or self.is_full_win,
            'is_full_win': self.is_full_win,
            'level_completions': self.levels_completed,
            'win_levels': self.win_levels,
            'total_actions': self.total_actions,
            'actions_taken': [],  # Would need action-by-action data
            'score_history': self.score_history,
            'duration_seconds': self.duration_seconds,
            'session_id': self.session_id or f"session_{uuid.uuid4().hex[:8]}",
        }


@dataclass
class PostGameResult:
    """Result of all post-game processing."""
    # Fitness calculation result
    fitness: FitnessResult

    # Lessons extraction result
    lessons: LessonsResult

    # Summary stats
    total_evolutionary_reward: float
    lessons_learned: int
    processing_time_ms: float

    # Flags
    win_recorded: bool
    new_sequence_created: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            'fitness': self.fitness.to_dict(),
            'lessons_count': self.lessons.total_lessons,
            'total_reward': self.total_evolutionary_reward,
            'processing_time_ms': self.processing_time_ms,
            'win_recorded': self.win_recorded,
            'new_sequence_created': self.new_sequence_created,
        }


class PostGameProcessor:
    """
    Orchestrates all post-game processing.

    This is the single entry point for game_loop.py to call when
    a game ends. It coordinates:

    1. FitnessCalculator - Evolutionary rewards
    2. LessonsExtractor - Learning from outcome
    3. Sequence storage - If win
    4. Agent stat updates
    """

    def __init__(
        self,
        db: 'DatabaseInterface',
        fitness_config: Optional[FitnessConfig] = None,
    ):
        self.db = db
        self._processor_id = f"postgame_{uuid.uuid4().hex[:8]}"

        # Initialize sub-processors
        self.fitness_calculator = FitnessCalculator(db, fitness_config)
        self.lessons_extractor = LessonsExtractor(db)

    def process_game_end(
        self,
        game_result: GameEndResult,
        _replay_learning_context: Optional[Any] = None,
    ) -> PostGameResult:
        """
        Process all post-game activities.

        Args:
            game_result: The completed game's data
            replay_learning_context: Optional ReplayLearningContext if
                                     replay learning was active

        Returns:
            PostGameResult with all processing outcomes
        """
        start_time = datetime.now()

        # 1. Calculate fitness (RLVR rewards)
        fitness = self.fitness_calculator.calculate_fitness(
            agent_id=game_result.agent_id,
            game_results=game_result.to_dict(),
        )

        # 2. Extract lessons
        lessons = self.lessons_extractor.extract_lessons(
            game_id=game_result.game_id,
            game_type=game_result.game_type,
            agent_id=game_result.agent_id,
            action_sequence=game_result.action_sequence,
            score_history=game_result.score_history,
            is_win=game_result.is_win,
            is_full_win=game_result.is_full_win,
            levels_completed=game_result.levels_completed,
            frame_history=game_result.frame_history,
        )

        # 3. Store winning sequence if applicable
        win_recorded = False
        new_sequence_created = False

        if game_result.is_win or game_result.is_full_win:
            win_recorded = True
            new_sequence_created = self._store_winning_sequence(game_result)

        # 4. Update agent statistics
        self._update_agent_stats(game_result, fitness)

        # 5. Record game result
        self._record_game_result(game_result, fitness)

        # Calculate processing time
        processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000

        return PostGameResult(
            fitness=fitness,
            lessons=lessons,
            total_evolutionary_reward=fitness.total_reward,
            lessons_learned=lessons.total_lessons,
            processing_time_ms=processing_time_ms,
            win_recorded=win_recorded,
            new_sequence_created=new_sequence_created,
        )

    def _store_winning_sequence(self, game_result: GameEndResult) -> bool:
        """Store winning sequence if it's better than existing."""
        if not game_result.action_sequence:
            return False

        try:
            # Check if we have a better sequence already
            existing = self.db.execute_query("""
                SELECT sequence_id, action_count
                FROM winning_sequences
                WHERE game_id = ? AND level_number = ?
                AND is_active = 1
                ORDER BY action_count ASC
                LIMIT 1
            """, (game_result.game_id, game_result.levels_completed))

            action_count = len(game_result.action_sequence)

            # Only store if shorter or no existing
            should_store = True
            if existing and existing[0].get('action_count', 9999) <= action_count:
                should_store = False

            if should_store:
                import json
                sequence_id = f"seq_{uuid.uuid4().hex[:12]}"

                self.db.execute("""
                    INSERT INTO winning_sequences (
                        sequence_id, game_id, game_type, level_number,
                        action_sequence, action_count, agent_id,
                        final_score, is_full_win, is_active, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                """, (
                    sequence_id,
                    game_result.game_id,
                    game_result.game_type,
                    game_result.levels_completed,
                    json.dumps(game_result.action_sequence),
                    action_count,
                    game_result.agent_id,
                    game_result.final_score,
                    game_result.is_full_win,
                    datetime.now().isoformat(),
                ))
                return True

        except Exception as e:
            logger.warning("Failed to store winning sequence", exc=e)

        return False

    def _update_agent_stats(
        self,
        game_result: GameEndResult,
        fitness: FitnessResult
    ) -> None:
        """Update agent performance statistics."""
        try:
            self.db.execute("""
                UPDATE agents SET
                    games_played = games_played + 1,
                    total_score = total_score + ?,
                    total_wins = total_wins + ?,
                    total_actions = total_actions + ?,
                    last_played_at = ?
                WHERE agent_id = ?
            """, (
                fitness.total_reward,
                1 if game_result.is_win else 0,
                game_result.total_actions,
                datetime.now().isoformat(),
                game_result.agent_id,
            ))
        except Exception as e:
            # Agent table might have different schema
            logger.warning("Failed to update agent stats", exc=e)

    def _record_game_result(
        self,
        game_result: GameEndResult,
        fitness: FitnessResult
    ) -> None:
        """Record complete game result to database."""
        try:
            self.db.store_game_result({
                'result_id': f"result_{uuid.uuid4().hex[:12]}",
                'agent_id': game_result.agent_id,
                'game_id': game_result.game_id,
                'game_type': game_result.game_type,
                'final_score': game_result.final_score,
                'levels_completed': game_result.levels_completed,
                'is_win': game_result.is_win,
                'is_full_win': game_result.is_full_win,
                'total_actions': game_result.total_actions,
                'evolutionary_reward': fitness.total_reward,
                'duration_seconds': game_result.duration_seconds,
                'created_at': datetime.now().isoformat(),
            })
        except Exception as e:
            logger.warning("Failed to record game result", exc=e)

    # =========================================================================
    # Convenience Methods for Backwards Compatibility
    # =========================================================================

    def calculate_fitness_only(
        self,
        agent_id: str,
        game_results: Dict[str, Any]
    ) -> FitnessResult:
        """
        Calculate fitness without full post-game processing.

        Use this when you only need the RLVR reward calculation
        (e.g., from evolutionary_engine.py).
        """
        return self.fitness_calculator.calculate_fitness(agent_id, game_results)

    def get_population_fitness_summary(self, generation: int) -> Dict[str, Any]:
        """
        Get fitness summary for entire population.

        Use this from evolutionary_engine.py for selection decisions.
        """
        return self.fitness_calculator.calculate_population_fitness_summary(generation)


# =========================================================================
# Backwards Compatibility: ARCRLVRFramework Interface
# =========================================================================
# This allows existing code that uses ARCRLVRFramework to work unchanged
# while actually using the new consolidated module.

class ARCRLVRFramework:
    """
    DEPRECATED: Use PostGameProcessor or FitnessCalculator directly.

    This class provides backwards compatibility for code that imports
    ARCRLVRFramework from the old location.
    """

    def __init__(self, database_interface: 'DatabaseInterface'):
        self._processor = PostGameProcessor(database_interface)
        self.db = database_interface
        self.framework_id = self._processor._processor_id
        self.reward_weights = FitnessConfig().__dict__

    def process_arc_rewards(
        self,
        agent_id: str,
        game_session_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process ARC game results into evolutionary feedback."""
        result = self._processor.calculate_fitness_only(agent_id, game_session_results)
        return {
            'agent_id': agent_id,
            'game_id': game_session_results.get('game_id'),
            'session_id': game_session_results.get('session_id'),
            'arc_native_rewards': result.arc_rewards,
            'derived_metrics': result.derived_metrics,
            'evolutionary_feedback': {
                'total_reward': result.total_reward,
                'reward_breakdown': result.breakdown,
                'fitness_signals': result.fitness_signals,
            },
            'total_evolutionary_reward': result.total_reward,
            'processing_timestamp': datetime.now().isoformat(),
        }

    def calculate_population_fitness_summary(
        self,
        generation: int
    ) -> Dict[str, Any]:
        """Calculate fitness summary for entire population."""
        return self._processor.get_population_fitness_summary(generation)

    def validate_reward_calculation(
        self,
        agent_id: str,
        game_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate that reward calculations are correct."""
        return self._processor.fitness_calculator.validate_reward_calculation(
            agent_id, game_results
        )
