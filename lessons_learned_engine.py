import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Must be FIRST before other imports

"""
Lessons Learned System - Post-Game Reflection for Future Games
==============================================================

Replaces the old counterfactual analyzer that generated 155K+ unused scenarios.

New approach:
1. After each game, agent generates max 3 "lessons learned"
2. These are stored with game_type context
3. When playing the same game_type again, agent retrieves relevant lessons
4. Lessons are actionable insights, not theoretical counterfactuals

Following Rule 2: All lessons stored in database
Following Rule 3: Enhances existing learning systems
"""

import json
import uuid
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


# Maximum lessons per game to prevent bloat
MAX_LESSONS_PER_GAME = 3

# Maximum lessons to retrieve when starting a new game
MAX_LESSONS_TO_RETRIEVE = 20


class LessonsLearnedEngine:
    """
    Lessons Learned System - Network Knowledge from Game Outcomes.
    
    After each game, generates max 3 actionable lessons.
    Before each game, retrieves relevant lessons from past games of same type.
    Lessons gain/lose confidence based on whether they help.
    
    Key methods:
    - record_game_lessons(): Call after game with score data
    - get_lessons_for_game(): Call before game to get prior knowledge
    - mark_lesson_helped(): Update confidence when lesson was useful
    """
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self._initialize_schema()
    
    def _initialize_schema(self):
        """Create lessons learned table (simpler than old schema)."""
        try:
            # New simplified lessons table
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS game_lessons_learned (
                    lesson_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    game_type TEXT NOT NULL,
                    game_id TEXT NOT NULL,
                    generation INTEGER DEFAULT 0,
                    
                    -- The lesson
                    lesson_text TEXT NOT NULL,  -- Human-readable lesson
                    lesson_type TEXT NOT NULL,  -- 'avoid', 'try', 'pattern', 'strategy'
                    
                    -- Context
                    final_score REAL NOT NULL,
                    was_win BOOLEAN DEFAULT FALSE,
                    action_count INTEGER DEFAULT 0,
                    key_action TEXT,  -- The action this lesson relates to (if any)
                    
                    -- Validation
                    times_retrieved INTEGER DEFAULT 0,
                    times_helped INTEGER DEFAULT 0,  -- Did following this lesson help?
                    confidence REAL DEFAULT 0.5,
                    
                    -- Timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_retrieved_at TIMESTAMP,
                    
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                )
            """)
            
            # Index for fast retrieval by game_type
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_lessons_game_type 
                ON game_lessons_learned(game_type, confidence DESC)
            """)
            
            self.logger.info("Lessons learned schema initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize lessons schema: {e}")
    
    def record_game_lessons(
        self,
        agent_id: str,
        game_id: str,
        game_type: str,
        final_score: float,
        actions_taken: int,
        levels_completed: int = 0,
        was_win: bool = False,
        generation: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Record lessons from a completed game using outcome data only.
        
        This is the SIMPLE version that works with data we always have.
        No need for detailed action history with score_before/score_after.
        
        Args:
            agent_id: The agent that played
            game_id: The specific game instance
            game_type: Game type for future retrieval
            final_score: Final score achieved
            actions_taken: Total actions in the game
            levels_completed: How many levels were beaten
            was_win: Whether the game was won
            generation: Current evolution generation
            
        Returns:
            List of lesson dicts that were stored
        """
        lessons = []
        
        # Only generate lessons for non-trivial games
        if actions_taken < 10:
            return lessons
        
        # Lesson based on efficiency (score per action)
        efficiency = final_score / max(1, actions_taken)
        
        if was_win:
            # Winning lesson - note what worked
            lesson_text = f"Won with {actions_taken} actions. Efficiency: {efficiency:.2f} score/action."
            lesson_type = "strategy"
            lesson = self._store_lesson(
                agent_id, game_type, game_id, generation,
                lesson_text, lesson_type,
                final_score, was_win, actions_taken, None
            )
            if lesson:
                lessons.append(lesson)
        elif final_score > 0:
            # Partial success - note progress
            lesson_text = f"Scored {final_score} but didn't win. Completed {levels_completed} levels."
            lesson_type = "pattern"
            lesson = self._store_lesson(
                agent_id, game_type, game_id, generation,
                lesson_text, lesson_type,
                final_score, was_win, actions_taken, None
            )
            if lesson:
                lessons.append(lesson)
        else:
            # Zero score - note to try different approach
            lesson_text = f"Zero score after {actions_taken} actions. Need fundamentally different approach."
            lesson_type = "avoid"
            lesson = self._store_lesson(
                agent_id, game_type, game_id, generation,
                lesson_text, lesson_type,
                final_score, was_win, actions_taken, None
            )
            if lesson:
                lessons.append(lesson)
        
        return lessons

    def analyze_failure(
        self,
        agent_id: str,
        game_id: str,
        game_type: str,
        final_score: float,
        action_history: List[Dict[str, Any]],
        session_id: str = "",
        generation: int = 0,
        max_counterfactuals: Optional[int] = None  # Ignored, kept for backward compat
    ) -> List[Dict[str, Any]]:
        """
        Generate lessons from a completed game (win or loss).
        
        Returns list of lessons for backward compatibility with callers
        that expect counterfactual_scenarios.
        """
        lessons = []
        
        if not action_history or len(action_history) < 3:
            return lessons
        
        was_win = final_score > 0
        
        # Generate up to MAX_LESSONS_PER_GAME lessons
        generated = 0
        
        # Lesson 1: Score trajectory analysis
        score_lesson = self._analyze_score_trajectory(action_history, final_score, was_win)
        if score_lesson and generated < MAX_LESSONS_PER_GAME:
            lesson = self._store_lesson(
                agent_id, game_type, game_id, generation,
                score_lesson['text'], score_lesson['type'],
                final_score, was_win, len(action_history),
                score_lesson.get('key_action')
            )
            if lesson:
                lessons.append(lesson)
                generated += 1
        
        # Lesson 2: Stuck detection
        stuck_lesson = self._analyze_stuck_periods(action_history)
        if stuck_lesson and generated < MAX_LESSONS_PER_GAME:
            lesson = self._store_lesson(
                agent_id, game_type, game_id, generation,
                stuck_lesson['text'], stuck_lesson['type'],
                final_score, was_win, len(action_history),
                stuck_lesson.get('key_action')
            )
            if lesson:
                lessons.append(lesson)
                generated += 1
        
        # Lesson 3: What worked (if any score increases)
        success_lesson = self._analyze_what_worked(action_history, was_win)
        if success_lesson and generated < MAX_LESSONS_PER_GAME:
            lesson = self._store_lesson(
                agent_id, game_type, game_id, generation,
                success_lesson['text'], success_lesson['type'],
                final_score, was_win, len(action_history),
                success_lesson.get('key_action')
            )
            if lesson:
                lessons.append(lesson)
                generated += 1
        
        if lessons:
            self.logger.info(
                f"[LESSONS] Generated {len(lessons)} lessons for {game_type} "
                f"(score={final_score}, win={was_win})"
            )
        
        return lessons
    
    def _analyze_score_trajectory(
        self, 
        actions: List[Dict[str, Any]], 
        final_score: float,
        was_win: bool
    ) -> Optional[Dict[str, Any]]:
        """Analyze the score trajectory to generate a lesson."""
        if not actions:
            return None
        
        # Find score changes
        score_increases = []
        score_decreases = []
        
        for i, action in enumerate(actions):
            score_before = action.get('score_before', 0) or 0
            score_after = action.get('score_after', 0) or 0
            delta = score_after - score_before
            
            if delta > 0:
                score_increases.append((i, action, delta))
            elif delta < 0:
                score_decreases.append((i, action, delta))
        
        # Generate lesson based on trajectory
        if was_win and score_increases:
            # Winning game - note what worked
            best_increase = max(score_increases, key=lambda x: x[2])
            action_info = best_increase[1]
            return {
                'text': f"Score increased by {best_increase[2]} at action {best_increase[0]+1}. This action pattern led to success.",
                'type': 'try',
                'key_action': str(action_info.get('action_type', 'unknown'))
            }
        elif not was_win and not score_increases:
            return {
                'text': "No score increases throughout game. Need different approach entirely.",
                'type': 'strategy',
                'key_action': None
            }
        elif score_decreases and len(score_decreases) > len(score_increases):
            worst_decrease = min(score_decreases, key=lambda x: x[2])
            return {
                'text': f"Score decreased {len(score_decreases)} times. Avoid action at position {worst_decrease[0]+1}.",
                'type': 'avoid',
                'key_action': str(worst_decrease[1].get('action_type', 'unknown'))
            }
        
        return None
    
    def _analyze_stuck_periods(self, actions: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Detect periods where score didn't change (stuck)."""
        if len(actions) < 10:
            return None
        
        # Find longest streak of no score change
        current_streak = 0
        max_streak = 0
        max_streak_start = 0
        
        for i, action in enumerate(actions):
            score_before = action.get('score_before', 0) or 0
            score_after = action.get('score_after', 0) or 0
            
            if score_before == score_after:
                current_streak += 1
                if current_streak > max_streak:
                    max_streak = current_streak
                    max_streak_start = i - current_streak + 1
            else:
                current_streak = 0
        
        # If stuck for more than 20% of game, generate lesson
        if max_streak > len(actions) * 0.2 and max_streak >= 5:
            return {
                'text': f"Got stuck for {max_streak} actions starting at action {max_streak_start+1}. Try different action types when stuck.",
                'type': 'pattern',
                'key_action': None
            }
        
        return None
    
    def _analyze_what_worked(
        self, 
        actions: List[Dict[str, Any]], 
        was_win: bool
    ) -> Optional[Dict[str, Any]]:
        """Identify patterns in successful actions."""
        if not actions:
            return None
        
        # Count action types that led to score increases
        action_success = {}
        
        for action in actions:
            score_before = action.get('score_before', 0) or 0
            score_after = action.get('score_after', 0) or 0
            action_type = str(action.get('action_type', 'unknown'))
            
            if action_type not in action_success:
                action_success[action_type] = {'increases': 0, 'total': 0}
            
            action_success[action_type]['total'] += 1
            if score_after > score_before:
                action_success[action_type]['increases'] += 1
        
        # Find most successful action type
        best_action = None
        best_rate = 0
        
        for action_type, stats in action_success.items():
            if stats['total'] >= 3:  # Need enough samples
                rate = stats['increases'] / stats['total']
                if rate > best_rate:
                    best_rate = rate
                    best_action = action_type
        
        if best_action and best_rate > 0.2:
            return {
                'text': f"Action type {best_action} led to score increases {int(best_rate*100)}% of the time.",
                'type': 'try',
                'key_action': best_action
            }
        
        return None
    
    def _store_lesson(
        self,
        agent_id: str,
        game_type: str,
        game_id: str,
        generation: int,
        lesson_text: str,
        lesson_type: str,
        final_score: float,
        was_win: bool,
        action_count: int,
        key_action: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Store a lesson in the database."""
        try:
            lesson_id = f"lesson_{uuid.uuid4().hex[:12]}"
            
            self.db.execute_query("""
                INSERT INTO game_lessons_learned (
                    lesson_id, agent_id, game_type, game_id, generation,
                    lesson_text, lesson_type, final_score, was_win,
                    action_count, key_action, confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lesson_id, agent_id, game_type, game_id, generation,
                lesson_text, lesson_type, final_score, was_win,
                action_count, key_action, 0.5
            ))
            
            return {
                'lesson_id': lesson_id,
                'lesson_text': lesson_text,
                'lesson_type': lesson_type,
                'game_type': game_type
            }
            
        except Exception as e:
            self.logger.debug(f"Failed to store lesson: {e}")
            return None
    
    def get_lessons_for_game(
        self,
        agent_id: str,
        game_type: str,
        limit: int = MAX_LESSONS_TO_RETRIEVE
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant lessons before starting a game.
        
        Called at game start to give agent prior knowledge.
        """
        try:
            # Get lessons from same game_type, ordered by confidence
            results = self.db.execute_query("""
                SELECT lesson_id, lesson_text, lesson_type, key_action,
                       confidence, times_helped, was_win
                FROM game_lessons_learned
                WHERE game_type = ?
                ORDER BY confidence DESC, times_helped DESC
                LIMIT ?
            """, (game_type, limit))
            
            if not results:
                return []
            
            lessons = []
            for row in results:
                lesson = {
                    'lesson_id': row['lesson_id'],
                    'text': row['lesson_text'],
                    'type': row['lesson_type'],
                    'key_action': row['key_action'],
                    'confidence': row['confidence'],
                    'from_win': row['was_win']
                }
                lessons.append(lesson)
                
                # Mark as retrieved
                self.db.execute_query("""
                    UPDATE game_lessons_learned 
                    SET times_retrieved = times_retrieved + 1,
                        last_retrieved_at = CURRENT_TIMESTAMP
                    WHERE lesson_id = ?
                """, (row['lesson_id'],))
            
            if lessons:
                self.logger.info(
                    f"[LESSONS] Retrieved {len(lessons)} lessons for {game_type}"
                )
            
            return lessons
            
        except Exception as e:
            self.logger.debug(f"Failed to retrieve lessons: {e}")
            return []
    
    def mark_lesson_helped(self, lesson_id: str, helped: bool = True) -> None:
        """Mark whether following a lesson helped in the current game."""
        try:
            if helped:
                self.db.execute_query("""
                    UPDATE game_lessons_learned 
                    SET times_helped = times_helped + 1,
                        confidence = MIN(1.0, confidence + 0.1)
                    WHERE lesson_id = ?
                """, (lesson_id,))
            else:
                self.db.execute_query("""
                    UPDATE game_lessons_learned 
                    SET confidence = MAX(0.0, confidence - 0.05)
                    WHERE lesson_id = ?
                """, (lesson_id,))
        except Exception as e:
            self.logger.debug(f"Failed to update lesson: {e}")
    
    def get_lesson_stats(self) -> Dict[str, Any]:
        """Get statistics about the lessons learned system."""
        try:
            total = self.db.execute_query(
                "SELECT COUNT(*) as cnt FROM game_lessons_learned"
            )
            by_type = self.db.execute_query("""
                SELECT lesson_type, COUNT(*) as cnt 
                FROM game_lessons_learned 
                GROUP BY lesson_type
            """)
            high_conf = self.db.execute_query(
                "SELECT COUNT(*) as cnt FROM game_lessons_learned WHERE confidence > 0.7"
            )
            
            return {
                'total_lessons': total[0]['cnt'] if total else 0,
                'by_type': {r['lesson_type']: r['cnt'] for r in (by_type or [])},
                'high_confidence': high_conf[0]['cnt'] if high_conf else 0
            }
        except Exception as e:
            return {'error': str(e)}
