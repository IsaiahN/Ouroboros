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
import re
import math
import hashlib
from typing import Dict, List, Optional, Any, Tuple
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
        """Create lessons learned table with dedup and salience support."""
        try:
            # Lessons table with occurrence counting and severity
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS game_lessons_learned (
                    lesson_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    game_type TEXT NOT NULL,
                    game_id TEXT NOT NULL,
                    generation INTEGER DEFAULT 0,
                    
                    -- The lesson (normalized for dedup)
                    lesson_text TEXT NOT NULL,  -- Human-readable lesson
                    lesson_type TEXT NOT NULL,  -- 'avoid', 'try', 'pattern', 'strategy', 'death'
                    lesson_hash TEXT,           -- Hash for dedup (game_type + type + key content)
                    
                    -- Salience factors (for ranking)
                    occurrence_count INTEGER DEFAULT 1,  -- How many times this exact lesson observed
                    severity INTEGER DEFAULT 1,          -- 1=low, 2=medium, 3=high (death=3)
                    caused_death BOOLEAN DEFAULT FALSE,  -- Did this cause game over?
                    caused_early_end BOOLEAN DEFAULT FALSE,  -- Game ended quickly?
                    
                    -- Context
                    final_score REAL NOT NULL,
                    was_win BOOLEAN DEFAULT FALSE,
                    action_count INTEGER DEFAULT 0,
                    key_action TEXT,  -- The action this lesson relates to (if any)
                    
                    -- Validation
                    times_retrieved INTEGER DEFAULT 0,
                    times_helped INTEGER DEFAULT 0,  -- Did following this lesson help?
                    confidence REAL DEFAULT 0.5,
                    
                    -- CODS integration
                    reported_to_cods BOOLEAN DEFAULT FALSE,  -- Has CODS seen this pattern?
                    cods_primitive_unlocked TEXT,            -- Primitive unlocked (if any)
                    
                    -- Timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_retrieved_at TIMESTAMP,
                    last_occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                )
            """)
            
            # IMPORTANT: Run migration BEFORE creating indexes that depend on new columns
            # This ensures lesson_hash column exists before idx_lessons_hash is created
            self._migrate_schema()
            
            # Index for fast retrieval by game_type with salience ranking
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_lessons_game_type 
                ON game_lessons_learned(game_type, severity DESC, occurrence_count DESC)
            """)
            
            # Index for dedup lookup (requires lesson_hash column from migration)
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_lessons_hash
                ON game_lessons_learned(game_type, lesson_hash)
            """)
            
            self.logger.info("Lessons learned schema initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize lessons schema: {e}")
    
    def _migrate_schema(self):
        """Add new columns to existing tables (safe migration)."""
        new_columns = [
            ("occurrence_count", "INTEGER DEFAULT 1"),
            ("severity", "INTEGER DEFAULT 1"),
            ("caused_death", "BOOLEAN DEFAULT FALSE"),
            ("caused_early_end", "BOOLEAN DEFAULT FALSE"),
            ("lesson_hash", "TEXT"),
            ("reported_to_cods", "BOOLEAN DEFAULT FALSE"),
            ("cods_primitive_unlocked", "TEXT"),
            ("last_occurred_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ]
        
        for col_name, col_type in new_columns:
            try:
                self.db.execute_query(f"""
                    ALTER TABLE game_lessons_learned ADD COLUMN {col_name} {col_type}
                """)
            except Exception:
                pass  # Column already exists
    
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
        was_game_over: bool = False,  # Did game end in GAME_OVER (death)?
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
            was_game_over: Whether game ended in GAME_OVER (death)
            
        Returns:
            List of lesson dicts that were stored
        """
        lessons = []
        
        # Only generate lessons for non-trivial games
        if actions_taken < 10:
            return lessons
        
        # Detect early end (game ended much faster than expected)
        is_early_end = actions_taken < 50 and not was_win
        
        # Lesson based on efficiency (score per action)
        efficiency = final_score / max(1, actions_taken)
        
        if was_win:
            # Winning lesson - note what worked
            lesson_text = f"Won with {actions_taken} actions. Efficiency: {efficiency:.2f} score/action."
            lesson_type = "strategy"
            lesson = self._store_lesson(
                agent_id, game_type, game_id, generation,
                lesson_text, lesson_type,
                final_score, was_win, actions_taken, None,
                caused_death=False, caused_early_end=False
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
                final_score, was_win, actions_taken, None,
                caused_death=was_game_over, caused_early_end=is_early_end
            )
            if lesson:
                lessons.append(lesson)
        else:
            # Zero score - note to try different approach
            if was_game_over:
                lesson_text = f"Died after {actions_taken} actions with zero score. Avoid dangerous objects."
                lesson_type = "death"
            else:
                lesson_text = f"Zero score after {actions_taken} actions. Need fundamentally different approach."
                lesson_type = "avoid"
            lesson = self._store_lesson(
                agent_id, game_type, game_id, generation,
                lesson_text, lesson_type,
                final_score, was_win, actions_taken, None,
                caused_death=was_game_over, caused_early_end=is_early_end
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
        key_action: Optional[str],
        caused_death: bool = False,
        caused_early_end: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Store a lesson in the database WITH DEDUPLICATION.
        
        If the same lesson already exists (same game_type, type, key content),
        we increment occurrence_count instead of creating a new row.
        """
        try:
            # Create a hash for dedup (game_type + lesson_type + normalized key content)
            # Normalize lesson text by extracting key parts
            normalized = self._normalize_lesson_for_hash(lesson_text, lesson_type, key_action)
            hash_input = f"{game_type}:{lesson_type}:{normalized}"
            lesson_hash = hashlib.md5(hash_input.encode()).hexdigest()[:16]
            
            # Calculate severity
            severity = 1  # Default low
            if caused_death or lesson_type == 'death':
                severity = 3  # High - death is critical
            elif caused_early_end or lesson_type == 'avoid':
                severity = 2  # Medium - worth paying attention to
            elif was_win:
                severity = 2  # Medium - winning strategies are valuable
            
            # Check if this lesson already exists (dedup)
            existing = self.db.execute_query("""
                SELECT lesson_id, occurrence_count, confidence, severity
                FROM game_lessons_learned
                WHERE game_type = ? AND lesson_hash = ?
                LIMIT 1
            """, (game_type, lesson_hash))
            
            if existing and len(existing) > 0:
                # UPDATE existing lesson - increment count, update timestamp
                existing_id = existing[0]['lesson_id']
                old_count = existing[0]['occurrence_count'] or 1
                old_severity = existing[0]['severity'] or 1
                old_confidence = existing[0]['confidence'] or 0.5
                
                # Confidence grows with occurrences (log scale to prevent runaway)
                new_count = old_count + 1
                new_confidence = min(0.95, old_confidence + 0.05 * math.log(new_count + 1))
                new_severity = max(old_severity, severity)  # Keep highest severity seen
                
                self.db.execute_query("""
                    UPDATE game_lessons_learned
                    SET occurrence_count = ?,
                        confidence = ?,
                        severity = ?,
                        last_occurred_at = CURRENT_TIMESTAMP,
                        caused_death = caused_death OR ?,
                        caused_early_end = caused_early_end OR ?
                    WHERE lesson_id = ?
                """, (new_count, new_confidence, new_severity, 
                      caused_death, caused_early_end, existing_id))
                
                self.logger.debug(f"[LESSON-DEDUP] Updated existing lesson (count={new_count}): {lesson_text[:50]}...")
                
                return {
                    'lesson_id': existing_id,
                    'lesson_text': lesson_text,
                    'lesson_type': lesson_type,
                    'game_type': game_type,
                    'is_update': True,
                    'occurrence_count': new_count
                }
            
            # CREATE new lesson
            lesson_id = f"lesson_{uuid.uuid4().hex[:12]}"
            
            self.db.execute_query("""
                INSERT INTO game_lessons_learned (
                    lesson_id, agent_id, game_type, game_id, generation,
                    lesson_text, lesson_type, lesson_hash,
                    final_score, was_win, action_count, key_action,
                    confidence, severity, occurrence_count,
                    caused_death, caused_early_end
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lesson_id, agent_id, game_type, game_id, generation,
                lesson_text, lesson_type, lesson_hash,
                final_score, was_win, action_count, key_action,
                0.5, severity, 1,
                caused_death, caused_early_end
            ))
            
            self.logger.debug(f"[LESSON-NEW] Created new lesson: {lesson_text[:50]}...")
            
            return {
                'lesson_id': lesson_id,
                'lesson_text': lesson_text,
                'lesson_type': lesson_type,
                'game_type': game_type,
                'is_update': False,
                'occurrence_count': 1
            }
            
        except Exception as e:
            self.logger.debug(f"Failed to store lesson: {e}")
            return None
    
    def _normalize_lesson_for_hash(
        self, 
        lesson_text: str, 
        lesson_type: str, 
        key_action: Optional[str]
    ) -> str:
        """
        Normalize lesson content for hash-based dedup.
        
        Extract the semantic key from the lesson, ignoring variable details
        like specific counts or scores that might differ between occurrences.
        """
        # For action-specific lessons, the key is the action
        if key_action:
            return f"action:{key_action}"
        
        # For pattern lessons, extract the pattern type
        if lesson_type == 'avoid':
            # "Zero score after X actions" -> "zero_score"
            if 'zero score' in lesson_text.lower():
                return "zero_score"
            # "Avoid action at position X" -> "avoid_action"
            if 'avoid action' in lesson_text.lower():
                return "avoid_action"
        
        if lesson_type == 'pattern':
            # "Got stuck for X actions" -> "stuck_pattern"
            if 'stuck' in lesson_text.lower():
                return "stuck_pattern"
        
        if lesson_type == 'strategy':
            # "Won with X actions" -> "win_strategy"
            if 'won' in lesson_text.lower():
                return "win_strategy"
            # "No score increases" -> "no_progress"
            if 'no score increase' in lesson_text.lower():
                return "no_progress"
        
        if lesson_type == 'death':
            # Extract object type if present
            match = re.search(r'object[:\s]+(\w+)', lesson_text.lower())
            if match:
                return f"death:{match.group(1)}"
            return "death:unknown"
        
        # Fallback: use first 30 chars normalized
        normalized = re.sub(r'\d+', 'N', lesson_text.lower())
        normalized = re.sub(r'\s+', '_', normalized[:30])
        return normalized
    
    def get_lessons_for_game(
        self,
        agent_id: str,
        game_type: str,
        limit: int = MAX_LESSONS_TO_RETRIEVE
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant lessons before starting a game.
        
        SALIENCE-BASED RANKING:
        1. Severity (death-causing lessons first)
        2. Occurrence count (frequently observed = more reliable)
        3. Recency (recently occurred = more relevant)
        4. Confidence (validated lessons preferred)
        
        Called at game start to give agent prior knowledge.
        """
        try:
            # Salience-ranked query:
            # - severity DESC: death/critical lessons first
            # - occurrence_count DESC: frequently seen lessons are more reliable
            # - last_occurred_at DESC: recent lessons more relevant
            # - confidence DESC: validated lessons preferred
            results = self.db.execute_query("""
                SELECT lesson_id, lesson_text, lesson_type, key_action,
                       confidence, times_helped, was_win,
                       COALESCE(severity, 1) as severity,
                       COALESCE(occurrence_count, 1) as occurrence_count,
                       COALESCE(caused_death, FALSE) as caused_death,
                       last_occurred_at
                FROM game_lessons_learned
                WHERE game_type = ?
                ORDER BY 
                    COALESCE(severity, 1) DESC,           -- Death lessons first
                    COALESCE(caused_death, 0) DESC,       -- Explicit death markers
                    COALESCE(occurrence_count, 1) DESC,   -- Frequent = reliable
                    last_occurred_at DESC,                 -- Recent = relevant
                    confidence DESC                        -- Validated = trusted
                LIMIT ?
            """, (game_type, limit))
            
            if not results:
                return []
            
            lessons = []
            lesson_ids = []
            
            for row in results:
                # Calculate a salience score for transparency
                salience = (
                    (row['severity'] or 1) * 0.4 +           # 40% severity
                    min((row['occurrence_count'] or 1), 10) * 0.3 +  # 30% occurrence (capped)
                    (row['confidence'] or 0.5) * 0.2 +       # 20% confidence
                    (0.1 if row['caused_death'] else 0)      # 10% death bonus
                )
                
                lesson = {
                    'lesson_id': row['lesson_id'],
                    'text': row['lesson_text'],
                    'type': row['lesson_type'],
                    'key_action': row['key_action'],
                    'confidence': row['confidence'] or 0.5,
                    'from_win': row['was_win'],
                    'severity': row['severity'] or 1,
                    'occurrence_count': row['occurrence_count'] or 1,
                    'caused_death': row['caused_death'] or False,
                    'salience': round(salience, 2)
                }
                lessons.append(lesson)
                lesson_ids.append(row['lesson_id'])
            
            # Batch update retrieval counts (more efficient)
            if lesson_ids:
                placeholders = ','.join(['?' for _ in lesson_ids])
                self.db.execute_query(f"""
                    UPDATE game_lessons_learned 
                    SET times_retrieved = times_retrieved + 1,
                        last_retrieved_at = CURRENT_TIMESTAMP
                    WHERE lesson_id IN ({placeholders})
                """, tuple(lesson_ids))
            
            if lessons:
                death_count = sum(1 for l in lessons if l['caused_death'])
                high_occ = sum(1 for l in lessons if l['occurrence_count'] >= 3)
                self.logger.info(
                    f"[LESSONS] Retrieved {len(lessons)} lessons for {game_type} "
                    f"(death={death_count}, high_occurrence={high_occ})"
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

    # =========================================================================
    # CODS INTEGRATION: Pattern Detection for Primitive Unlocks
    # =========================================================================
    # When lessons reach critical thresholds, they represent "discovered knowledge"
    # that CODS should validate and potentially unlock as primitives.
    #
    # Thresholds:
    # - occurrence_count >= 5: Pattern is reliable (seen multiple times)
    # - confidence >= 0.7: Pattern has been validated as helpful
    # - caused_death = TRUE: Critical survival knowledge
    #
    # Primitive candidates:
    # - "threat_recognition": Agent learned to identify death-causing objects
    # - "efficiency_strategy": Agent learned optimal action patterns
    # - "stuck_detection": Agent learned when it's making no progress
    # =========================================================================
    
    def get_patterns_for_cods(self, game_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get lessons that have reached threshold for CODS review.
        
        These are high-occurrence, high-confidence patterns that may
        represent genuine discoveries worthy of primitive unlock.
        
        Args:
            game_type: Filter to specific game type (None = all)
            
        Returns:
            List of pattern candidates for CODS validation
        """
        try:
            where_clause = "WHERE reported_to_cods = FALSE OR reported_to_cods IS NULL"
            params = []
            
            if game_type:
                where_clause += " AND game_type = ?"
                params.append(game_type)
            
            # Find patterns meeting CODS threshold
            results = self.db.execute_query(f"""
                SELECT lesson_id, game_type, lesson_text, lesson_type, key_action,
                       COALESCE(occurrence_count, 1) as occurrence_count,
                       confidence, COALESCE(caused_death, FALSE) as caused_death,
                       times_helped, times_retrieved
                FROM game_lessons_learned
                {where_clause}
                AND (
                    -- High occurrence patterns (seen 5+ times)
                    COALESCE(occurrence_count, 1) >= 5
                    OR
                    -- High confidence patterns (validated helpful)
                    confidence >= 0.7
                    OR
                    -- Critical survival patterns (death-causing with any occurrence)
                    (COALESCE(caused_death, FALSE) = TRUE AND COALESCE(occurrence_count, 1) >= 2)
                )
                ORDER BY 
                    COALESCE(caused_death, 0) DESC,  -- Death patterns first
                    COALESCE(occurrence_count, 1) DESC,
                    confidence DESC
                LIMIT 50
            """, tuple(params))
            
            if not results:
                return []
            
            patterns = []
            for row in results:
                # Determine primitive candidate type
                primitive_candidate = self._infer_primitive_type(row)
                
                # Calculate discovery strength
                discovery_strength = (
                    min((row['occurrence_count'] or 1), 10) / 10 * 0.4 +  # Occurrence
                    (row['confidence'] or 0.5) * 0.3 +                    # Confidence
                    (0.3 if row['caused_death'] else 0)                   # Death bonus
                )
                
                patterns.append({
                    'lesson_id': row['lesson_id'],
                    'game_type': row['game_type'],
                    'lesson_text': row['lesson_text'],
                    'lesson_type': row['lesson_type'],
                    'key_action': row['key_action'],
                    'occurrence_count': row['occurrence_count'] or 1,
                    'confidence': row['confidence'] or 0.5,
                    'caused_death': row['caused_death'] or False,
                    'primitive_candidate': primitive_candidate,
                    'discovery_strength': round(discovery_strength, 2)
                })
            
            return patterns
            
        except Exception as e:
            self.logger.debug(f"Failed to get patterns for CODS: {e}")
            return []
    
    def _infer_primitive_type(self, row: Dict[str, Any]) -> str:
        """Infer what primitive this pattern might unlock."""
        lesson_type = row.get('lesson_type', '')
        lesson_text = (row.get('lesson_text', '') or '').lower()
        caused_death = row.get('caused_death', False)
        
        # Death patterns -> threat_recognition primitive
        if caused_death or 'death' in lesson_text or 'died' in lesson_text:
            return 'threat_recognition'
        
        # Avoid patterns -> hazard_avoidance primitive
        if lesson_type == 'avoid' or 'avoid' in lesson_text:
            return 'hazard_avoidance'
        
        # Stuck patterns -> stuck_detection primitive
        if 'stuck' in lesson_text or 'no progress' in lesson_text:
            return 'stuck_detection'
        
        # Win patterns -> efficiency_strategy primitive
        if lesson_type == 'strategy' or 'won' in lesson_text or 'win' in lesson_text:
            return 'efficiency_strategy'
        
        # Action success patterns -> action_selection primitive
        if lesson_type == 'try' and row.get('key_action'):
            return 'action_selection'
        
        return 'general_pattern'
    
    def mark_reported_to_cods(
        self, 
        lesson_ids: List[str], 
        primitive_unlocked: Optional[str] = None
    ) -> None:
        """
        Mark lessons as reported to CODS.
        
        Called after CODS has reviewed patterns and (optionally) unlocked primitives.
        
        Args:
            lesson_ids: Lessons that were reported
            primitive_unlocked: Name of primitive unlocked (if any)
        """
        try:
            if not lesson_ids:
                return
            
            placeholders = ','.join(['?' for _ in lesson_ids])
            
            if primitive_unlocked:
                self.db.execute_query(f"""
                    UPDATE game_lessons_learned
                    SET reported_to_cods = TRUE,
                        cods_primitive_unlocked = ?
                    WHERE lesson_id IN ({placeholders})
                """, (primitive_unlocked, *lesson_ids))
                
                self.logger.info(
                    f"[CODS] Marked {len(lesson_ids)} lessons as reported, "
                    f"primitive unlocked: {primitive_unlocked}"
                )
            else:
                self.db.execute_query(f"""
                    UPDATE game_lessons_learned
                    SET reported_to_cods = TRUE
                    WHERE lesson_id IN ({placeholders})
                """, tuple(lesson_ids))
                
        except Exception as e:
            self.logger.debug(f"Failed to mark CODS report: {e}")

# =============================================================================
# DEATH CAUSE HYPOTHESIS SYSTEM
# =============================================================================
# Tracks WHY agents die on specific levels to identify threats
# 
# Key insight: If multiple agents die when adjacent to the same object type,
# that object is likely a "death trap" or "enemy" that should be avoided.
#
# Hypothesis types:
# - collision: Agent touched/overlapped with object → death
# - proximity: Agent was within N pixels of object → death  
# - timeout: Agent ran out of actions
# - score_condition: Game ended due to score rule
# =============================================================================

class DeathCauseHypothesis:
    """Tracks and validates hypotheses about what kills agents."""
    
    # Minimum observations before a hypothesis is considered reliable
    MIN_OBSERVATIONS = 3
    
    # Confidence thresholds
    HIGH_CONFIDENCE = 0.8
    MEDIUM_CONFIDENCE = 0.5
    
    def __init__(self, db: 'DatabaseInterface'):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Create death hypothesis tables."""
        try:
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS death_cause_hypotheses (
                    hypothesis_id TEXT PRIMARY KEY,
                    game_type TEXT NOT NULL,
                    level_number INTEGER NOT NULL,
                    
                    -- What we think caused the death
                    cause_type TEXT NOT NULL,  -- 'collision', 'proximity', 'timeout', 'score', 'unknown'
                    object_color INTEGER,      -- Color of suspected death object
                    object_pattern TEXT,       -- Shape signature or pattern description
                    object_position TEXT,      -- JSON: approximate position or region
                    
                    -- Evidence
                    times_observed INTEGER DEFAULT 1,
                    times_survived INTEGER DEFAULT 0,  -- Times agent was near but lived
                    confidence REAL DEFAULT 0.3,
                    
                    -- Context
                    avg_death_distance REAL,   -- Average distance to object at death
                    last_death_position TEXT,  -- JSON: where agent was when it died
                    contributing_agents TEXT,  -- JSON: list of agents that contributed data
                    
                    -- Timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    UNIQUE(game_type, level_number, cause_type, object_color, object_pattern)
                )
            """)
            
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_death_hypotheses_lookup
                ON death_cause_hypotheses(game_type, level_number, confidence DESC)
            """)
            
            # Track individual death events for learning
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS death_events (
                    event_id TEXT PRIMARY KEY,
                    game_type TEXT NOT NULL,
                    level_number INTEGER NOT NULL,
                    agent_id TEXT NOT NULL,
                    generation INTEGER DEFAULT 0,
                    
                    -- Death context
                    agent_position TEXT,       -- JSON: [x, y]
                    nearby_objects TEXT,       -- JSON: list of objects within death radius
                    action_before_death TEXT,  -- What action triggered death
                    frames_on_level INTEGER,   -- How long agent survived on this level
                    
                    -- Classification
                    inferred_cause TEXT,       -- 'collision', 'timeout', 'unknown'
                    death_object_color INTEGER,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_death_events_game
                ON death_events(game_type, level_number)
            """)
            
            self.logger.debug("Death hypothesis tables initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to create death hypothesis tables: {e}")
    
    def record_death(
        self,
        game_type: str,
        level_number: int,
        agent_id: str,
        agent_position: Tuple[int, int],
        nearby_objects: List[Dict[str, Any]],
        last_action: str,
        frames_on_level: int,
        generation: int = 0
    ) -> Optional[str]:
        """
        Record a death event and update hypotheses.
        
        Args:
            game_type: Game type prefix (e.g., 'as66')
            level_number: Level where death occurred
            agent_id: Agent that died
            agent_position: (x, y) position at death
            nearby_objects: List of objects near agent at death, each with:
                - color: int
                - position: [x, y]
                - distance: float (from agent)
                - size: int (pixel count)
            last_action: The action that was taken before death
            frames_on_level: How many frames agent survived on this level
            generation: Current evolution generation
            
        Returns:
            Inferred cause type or None
        """
        if not nearby_objects:
            # No objects nearby - likely timeout or other cause
            inferred_cause = 'timeout' if frames_on_level > 50 else 'unknown'
            death_color = None
            closest = None
        else:
            # Find closest object - likely the killer
            closest = min(nearby_objects, key=lambda o: o.get('distance', 999))
            
            if closest.get('distance', 999) <= 3:  # Within collision range
                inferred_cause = 'collision'
                death_color = closest.get('color')
            elif closest.get('distance', 999) <= 10:
                inferred_cause = 'proximity'
                death_color = closest.get('color')
            else:
                inferred_cause = 'unknown'
                death_color = None
        
        try:
            # Record the death event
            event_id = f"death_{uuid.uuid4().hex[:12]}"
            
            # Safely serialize agent_position
            position_json = json.dumps(list(agent_position)) if agent_position else '[]'
            
            self.db.execute_query("""
                INSERT INTO death_events (
                    event_id, game_type, level_number, agent_id, generation,
                    agent_position, nearby_objects, action_before_death,
                    frames_on_level, inferred_cause, death_object_color
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_id, game_type, level_number, agent_id, generation,
                position_json,
                json.dumps(nearby_objects[:10]),  # Limit stored objects
                last_action,
                frames_on_level,
                inferred_cause,
                death_color
            ))
            
            # Update or create hypothesis if we have a suspected object
            if inferred_cause in ('collision', 'proximity') and death_color is not None and closest:
                self._update_death_hypothesis(
                    game_type, level_number, inferred_cause, death_color,
                    closest, agent_position, agent_id
                )
            
            self.logger.debug(
                f"[DEATH] Recorded {inferred_cause} death on {game_type} L{level_number} "
                f"near color {death_color}"
            )
            
            return inferred_cause
            
        except Exception as e:
            self.logger.debug(f"Failed to record death: {e}")
            return None
    
    def _update_death_hypothesis(
        self,
        game_type: str,
        level_number: int,
        cause_type: str,
        object_color: int,
        death_object: Dict[str, Any],
        agent_position: Tuple[int, int],
        agent_id: str
    ):
        """Update or create a death cause hypothesis."""
        try:
            # Generate pattern signature from object shape if available
            pattern = death_object.get('shape_signature', 'unknown')
            if isinstance(pattern, (int, float)):
                pattern = str(pattern)[:20]
            
            # Check for existing hypothesis
            existing = self.db.execute_query("""
                SELECT hypothesis_id, times_observed, times_survived, 
                       confidence, contributing_agents
                FROM death_cause_hypotheses
                WHERE game_type = ? AND level_number = ? 
                  AND cause_type = ? AND object_color = ?
                LIMIT 1
            """, (game_type, level_number, cause_type, object_color))
            
            if existing:
                row = existing[0]
                new_observed = row['times_observed'] + 1
                
                # Confidence increases with more observations
                # Formula: confidence = observed / (observed + survived + 1)
                new_confidence = new_observed / (new_observed + row['times_survived'] + 1)
                new_confidence = min(0.95, new_confidence)  # Cap at 95%
                
                # Track contributing agents
                agents = json.loads(row['contributing_agents'] or '[]')
                if agent_id not in agents:
                    agents.append(agent_id)
                    agents = agents[-20:]  # Keep last 20
                
                self.db.execute_query("""
                    UPDATE death_cause_hypotheses
                    SET times_observed = ?,
                        confidence = ?,
                        last_death_position = ?,
                        contributing_agents = ?,
                        last_updated_at = CURRENT_TIMESTAMP
                    WHERE hypothesis_id = ?
                """, (
                    new_observed, new_confidence,
                    json.dumps(list(agent_position)) if agent_position else '[]',
                    json.dumps(agents),
                    row['hypothesis_id']
                ))
                
                if new_confidence >= self.HIGH_CONFIDENCE:
                    self.logger.info(
                        f"[THREAT] HIGH confidence: Color {object_color} kills on "
                        f"{game_type} L{level_number} ({new_observed} observations)"
                    )
            else:
                # Create new hypothesis
                hypothesis_id = f"dh_{game_type}_{level_number}_{object_color}_{uuid.uuid4().hex[:6]}"
                self.db.execute_query("""
                    INSERT INTO death_cause_hypotheses (
                        hypothesis_id, game_type, level_number, cause_type,
                        object_color, object_pattern, object_position,
                        times_observed, confidence, last_death_position,
                        contributing_agents
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, 0.3, ?, ?)
                """, (
                    hypothesis_id, game_type, level_number, cause_type,
                    object_color, pattern,
                    json.dumps(death_object.get('position', [])),
                    json.dumps(list(agent_position)) if agent_position else '[]',
                    json.dumps([agent_id])
                ))
                
        except Exception as e:
            self.logger.debug(f"Failed to update death hypothesis: {e}")
    
    def record_survival(
        self,
        game_type: str,
        level_number: int,
        objects_passed: List[Dict[str, Any]]
    ):
        """
        Record that agent survived near objects (reduces death confidence).
        
        Call this when agent passes near a suspected death object but lives.
        """
        if not objects_passed:
            return
        
        for obj in objects_passed:
            color = obj.get('color')
            if color is None:
                continue
            
            try:
                self.db.execute_query("""
                    UPDATE death_cause_hypotheses
                    SET times_survived = times_survived + 1,
                        confidence = times_observed / (times_observed + times_survived + 2),
                        last_updated_at = CURRENT_TIMESTAMP
                    WHERE game_type = ? AND level_number = ? AND object_color = ?
                """, (game_type, level_number, color))
            except Exception:
                pass
    
    def get_threat_objects(
        self,
        game_type: str,
        level_number: int,
        min_confidence: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Get objects that are suspected to cause death on this level.
        
        Args:
            game_type: Game type
            level_number: Level to query
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of threat objects with color, confidence, pattern
        """
        try:
            results = self.db.execute_query("""
                SELECT object_color, object_pattern, cause_type,
                       confidence, times_observed, object_position
                FROM death_cause_hypotheses
                WHERE game_type = ? AND level_number = ?
                  AND confidence >= ?
                ORDER BY confidence DESC
                LIMIT 10
            """, (game_type, level_number, min_confidence))
            
            threats = []
            for row in (results or []):
                threats.append({
                    'color': row['object_color'],
                    'pattern': row['object_pattern'],
                    'cause_type': row['cause_type'],
                    'confidence': row['confidence'],
                    'observations': row['times_observed'],
                    'position': json.loads(row['object_position'] or '[]')
                })
            
            return threats
            
        except Exception as e:
            self.logger.debug(f"Failed to get threat objects: {e}")
            return []
    
    def get_death_summary(self, game_type: str) -> Dict[str, Any]:
        """Get summary of death patterns for a game type."""
        try:
            by_level = self.db.execute_query("""
                SELECT level_number, 
                       COUNT(*) as total_deaths,
                       COUNT(DISTINCT agent_id) as unique_agents,
                       AVG(frames_on_level) as avg_survival
                FROM death_events
                WHERE game_type = ?
                GROUP BY level_number
                ORDER BY level_number
            """, (game_type,))
            
            high_conf = self.db.execute_query("""
                SELECT level_number, object_color, confidence, times_observed
                FROM death_cause_hypotheses
                WHERE game_type = ? AND confidence >= ?
                ORDER BY confidence DESC
                LIMIT 5
            """, (game_type, self.HIGH_CONFIDENCE))
            
            return {
                'by_level': [dict(r) for r in (by_level or [])],
                'high_confidence_threats': [dict(r) for r in (high_conf or [])]
            }
        except Exception as e:
            return {'error': str(e)}
    
    def record_responsive_object(
        self,
        game_type: str,
        level_number: int,
        object_color: int,
        trigger_action: str,
        agent_id: str
    ) -> None:
        """
        Record that an object moved in response to agent movement.
        
        BIRTHRIGHT THREAT DETECTION: Objects that move when you move but that
        you don't control are potential threats (chasers/enemies).
        
        This is called from birthright perception when:
        1. Agent takes a movement action
        2. An object moves that the agent doesn't control
        
        Multiple observations build confidence that this is a chaser/threat.
        
        Args:
            game_type: Game type prefix (e.g., 'as66')
            level_number: Level where observed
            object_color: Color of the object that moved
            trigger_action: Action that triggered the movement (e.g., 'ACTION1')
            agent_id: Agent that observed this
        """
        try:
            # Check for existing responsive object record
            existing = self.db.execute_query("""
                SELECT hypothesis_id, times_observed, confidence
                FROM death_cause_hypotheses
                WHERE game_type = ? AND level_number = ? 
                  AND object_color = ? AND cause_type = 'responsive'
                LIMIT 1
            """, (game_type, level_number, object_color))
            
            if existing:
                row = existing[0]
                new_observed = row['times_observed'] + 1
                
                # Confidence increases with repeated observations
                # Objects that consistently move when you move are likely threats
                # Formula: confidence = min(0.8, 0.2 + 0.1 * observations)
                new_confidence = min(0.8, 0.2 + 0.1 * new_observed)
                
                self.db.execute_query("""
                    UPDATE death_cause_hypotheses
                    SET times_observed = ?,
                        confidence = ?,
                        object_pattern = ?,
                        last_updated_at = CURRENT_TIMESTAMP
                    WHERE hypothesis_id = ?
                """, (
                    new_observed, new_confidence,
                    f"responsive_to_{trigger_action}",
                    row['hypothesis_id']
                ))
                
                if new_confidence >= 0.5:
                    self.logger.info(
                        f"[RESPONSIVE] Color {object_color} is likely a CHASER on "
                        f"{game_type} L{level_number} ({new_observed} observations, conf={new_confidence:.2f})"
                    )
            else:
                # Create new responsive object hypothesis
                hypothesis_id = f"resp_{game_type}_{level_number}_{object_color}_{uuid.uuid4().hex[:6]}"
                self.db.execute_query("""
                    INSERT INTO death_cause_hypotheses (
                        hypothesis_id, game_type, level_number, cause_type,
                        object_color, object_pattern, times_observed, 
                        confidence, contributing_agents
                    ) VALUES (?, ?, ?, 'responsive', ?, ?, 1, 0.3, ?)
                """, (
                    hypothesis_id, game_type, level_number,
                    object_color, f"responsive_to_{trigger_action}",
                    json.dumps([agent_id])
                ))
                
                self.logger.debug(
                    f"[RESPONSIVE] First observation: Color {object_color} moved when "
                    f"agent moved on {game_type} L{level_number}"
                )
                
        except Exception as e:
            self.logger.debug(f"Failed to record responsive object: {e}")