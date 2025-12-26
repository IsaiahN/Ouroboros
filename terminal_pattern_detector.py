import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
Terminal Pattern Detector - Foresight to Avoid Game Over
==========================================================

Gives agents the ability to recognize when they're approaching a terminal state
(game_over) and avoid taking the fatal action.

THE PROBLEM:
- Agents learn "ACTION X led to game_over" but this is too generic
- The SAME action might be safe in other contexts
- What matters is: CONTEXT (state) + ACTION = terminal

THE SOLUTION:
Track the "pre-death signature":
1. Hash of frame state before fatal action
2. Last N actions leading up to game_over
3. The fatal action itself

Before taking any action, check:
- Am I in a state similar to one that led to game_over?
- Is the action I'm about to take the same as the fatal action?
- If yes, suggest an alternative

IMPLEMENTATION:
1. On game_over: Record (frame_hash, last_5_actions, fatal_action) as "terminal signature"
2. On action selection: Check if (current_frame_hash, recent_actions, planned_action) matches any signature
3. If match: Return alternative action and reasoning
"""

import json
import hashlib
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


class TerminalPatternDetector:
    """
    Provides foresight to avoid game_over by pattern matching against
    previously observed terminal states.
    
    KEY INSIGHT: It's not just the action that kills you - it's the
    combination of STATE + ACTION that leads to terminal.
    """
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
        self._ensure_tables_exist()
        
        # Cache for faster lookups
        self._terminal_patterns_cache: Dict[str, List[Dict]] = {}
        self._cache_generation: int = -1
        
    def _ensure_tables_exist(self):
        """Create terminal_patterns table if it doesn't exist."""
        try:
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS terminal_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    game_id TEXT NOT NULL,
                    level_number INTEGER NOT NULL,
                    
                    -- Pre-death state signature
                    frame_hash TEXT NOT NULL,         -- Hash of frame before fatal action
                    pre_death_actions TEXT NOT NULL,  -- JSON: Last 5 actions before death
                    fatal_action INTEGER NOT NULL,    -- The action that caused game_over
                    
                    -- Pattern reliability
                    occurrence_count INTEGER DEFAULT 1,
                    confirmed_lethal INTEGER DEFAULT 0,    -- Times this pattern led to game_over
                    false_positive_count INTEGER DEFAULT 0, -- Times it was avoided but didn't matter
                    
                    -- Metadata
                    discovery_generation INTEGER,
                    discovered_by_agent TEXT,
                    last_occurrence_generation INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Confidence that this pattern reliably predicts game_over
                    confidence REAL DEFAULT 0.7,
                    
                    is_active INTEGER DEFAULT 1
                )
            """)
            
            # Index for fast lookups
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_terminal_patterns_lookup
                ON terminal_patterns (game_id, level_number, frame_hash, is_active)
            """)
            
        except Exception as e:
            logger.debug(f"Terminal patterns table setup: {e}")
    
    def compute_frame_hash(self, frame: List[List[int]], 
                           sensitivity: str = 'exact') -> str:
        """
        Compute a hash of the frame for pattern matching.
        
        Args:
            frame: 2D grid of pixels
            sensitivity: 'exact' (full match) or 'fuzzy' (ignore minor differences)
            
        Returns:
            Hash string for comparison
        """
        if not frame:
            return "empty"
        
        if sensitivity == 'exact':
            # Full grid hash
            flat = [str(cell) for row in frame for cell in row]
            return hashlib.md5(''.join(flat).encode()).hexdigest()[:16]
        else:
            # Fuzzy: Hash grid dimensions + non-zero cell positions
            # This allows matching "similar" states
            height = len(frame)
            width = len(frame[0]) if frame else 0
            non_zero = [(r, c, frame[r][c]) for r in range(height) 
                        for c in range(width) if frame[r][c] != 0]
            signature = f"{height}x{width}:" + str(sorted(non_zero)[:20])
            return hashlib.md5(signature.encode()).hexdigest()[:16]
    
    def record_terminal_pattern(self,
                                 game_id: str,
                                 level_number: int,
                                 frame_before_death: List[List[int]],
                                 pre_death_actions: List[int],
                                 fatal_action: int,
                                 agent_id: str,
                                 generation: int) -> Optional[str]:
        """
        Record a terminal pattern after game_over occurs.
        
        This creates a "death signature" that future agents can check against
        to avoid making the same fatal mistake.
        
        Args:
            game_id: Game where death occurred
            level_number: Level where death occurred
            frame_before_death: The frame state right before the fatal action
            pre_death_actions: Last 5 actions taken before death
            fatal_action: The action that caused game_over
            agent_id: Agent who died
            generation: Current generation
            
        Returns:
            pattern_id if recorded, None if failed
        """
        try:
            frame_hash = self.compute_frame_hash(frame_before_death)
            
            # Check if this exact pattern already exists
            existing = self.db.execute_query("""
                SELECT pattern_id, occurrence_count, confirmed_lethal
                FROM terminal_patterns
                WHERE game_id = ? AND level_number = ? 
                  AND frame_hash = ? AND fatal_action = ?
                  AND is_active = 1
            """, (game_id, level_number, frame_hash, fatal_action))
            
            if existing:
                # Pattern already known - increment counts
                pattern = existing[0]
                self.db.execute_query("""
                    UPDATE terminal_patterns
                    SET occurrence_count = occurrence_count + 1,
                        confirmed_lethal = confirmed_lethal + 1,
                        confidence = MIN(0.95, confidence + 0.05),
                        last_occurrence_generation = ?
                    WHERE pattern_id = ?
                """, (generation, pattern['pattern_id']))
                
                logger.info(f"[TERMINAL] Updated known pattern {pattern['pattern_id'][:8]} "
                           f"(now {pattern['occurrence_count']+1} occurrences)")
                return pattern['pattern_id']
            
            # Create new pattern
            pattern_id = f"term_{game_id[:8]}_{level_number}_{hashlib.md5(f'{frame_hash}{fatal_action}'.encode()).hexdigest()[:8]}"
            
            self.db.execute_query("""
                INSERT INTO terminal_patterns (
                    pattern_id, game_id, level_number,
                    frame_hash, pre_death_actions, fatal_action,
                    occurrence_count, confirmed_lethal,
                    discovery_generation, discovered_by_agent,
                    last_occurrence_generation, confidence, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, 1, 1, ?, ?, ?, 0.7, 1)
            """, (
                pattern_id, game_id, level_number,
                frame_hash, json.dumps(pre_death_actions[-5:]), fatal_action,
                generation, agent_id,
                generation
            ))
            
            logger.info(f"[TERMINAL] NEW pattern recorded: {pattern_id} "
                       f"(ACTION{fatal_action} at frame {frame_hash[:8]})")
            
            # Clear cache
            self._cache_generation = -1
            
            return pattern_id
            
        except Exception as e:
            logger.debug(f"Error recording terminal pattern: {e}")
            return None
    
    def check_for_terminal_danger(self,
                                   game_id: str,
                                   level_number: int,
                                   current_frame: List[List[int]],
                                   recent_actions: List[int],
                                   planned_action: int,
                                   min_confidence: float = 0.6) -> Optional[Dict[str, Any]]:
        """
        Check if the planned action might lead to game_over.
        
        This is the FORESIGHT mechanism - checking BEFORE taking action.
        
        Args:
            game_id: Current game
            level_number: Current level
            current_frame: Current game state
            recent_actions: Last few actions taken
            planned_action: Action we're about to take
            min_confidence: Minimum pattern confidence to trigger warning
            
        Returns:
            None if safe, or Dict with warning info and alternative suggestion
        """
        try:
            frame_hash = self.compute_frame_hash(current_frame)
            fuzzy_hash = self.compute_frame_hash(current_frame, sensitivity='fuzzy')
            
            # Check for matching terminal patterns
            patterns = self.db.execute_query("""
                SELECT 
                    pattern_id, frame_hash, pre_death_actions, fatal_action,
                    occurrence_count, confirmed_lethal, confidence
                FROM terminal_patterns
                WHERE game_id = ? AND level_number = ?
                  AND (frame_hash = ? OR frame_hash = ?)
                  AND fatal_action = ?
                  AND confidence >= ?
                  AND is_active = 1
                ORDER BY confidence DESC, confirmed_lethal DESC
                LIMIT 5
            """, (game_id, level_number, frame_hash, fuzzy_hash, 
                  planned_action, min_confidence))
            
            if not patterns:
                return None  # No danger detected
            
            best_match = patterns[0]
            
            # Additional check: Do recent actions match pre-death sequence?
            # (This reduces false positives - same frame + same action, 
            #  but different approach might be safe)
            pre_death_seq = json.loads(best_match['pre_death_actions'])
            
            # Match score: How similar is our recent action sequence?
            match_score = 0
            if recent_actions and pre_death_seq:
                # Compare last N actions
                for i, (recent, pre_death) in enumerate(zip(
                    reversed(recent_actions[-5:]), 
                    reversed(pre_death_seq[-5:])
                )):
                    if recent == pre_death:
                        match_score += 1
            
            # Require at least 2 matching actions to trigger warning
            # (unless pattern is very high confidence)
            if match_score < 2 and best_match['confidence'] < 0.85:
                return None
            
            # DANGER DETECTED! Suggest alternative
            alternative = self._suggest_alternative_action(
                planned_action, 
                [p['fatal_action'] for p in patterns],
                recent_actions
            )
            
            return {
                'warning': True,
                'pattern_id': best_match['pattern_id'],
                'confidence': best_match['confidence'],
                'fatal_action': planned_action,
                'occurrence_count': best_match['occurrence_count'],
                'confirmed_lethal': best_match['confirmed_lethal'],
                'match_score': match_score,
                'alternative_action': alternative,
                'reason': f"ACTION{planned_action} caused game_over {best_match['confirmed_lethal']} times in this situation"
            }
            
        except Exception as e:
            logger.debug(f"Terminal pattern check failed: {e}")
            return None
    
    def _suggest_alternative_action(self,
                                     avoid_action: int,
                                     all_fatal_actions: List[int],
                                     recent_actions: List[int]) -> int:
        """
        Suggest an alternative action to avoid death.
        
        Strategy:
        1. Avoid all known fatal actions for this state
        2. Prefer actions not recently taken (exploration)
        3. Fall back to opposite direction if movement action
        """
        # All 7 actions
        all_actions = [1, 2, 3, 4, 5, 6, 7]
        
        # Remove fatal actions
        safe_actions = [a for a in all_actions if a not in all_fatal_actions]
        
        if not safe_actions:
            # All actions fatal? Try UNDO (ACTION7) or opposite direction
            if avoid_action <= 4:  # Movement action
                opposite = {1: 2, 2: 1, 3: 4, 4: 3}
                return opposite.get(avoid_action, 7)
            return 7  # ACTION7 = UNDO
        
        # Prefer actions not recently taken
        recent_set = set(recent_actions[-3:]) if recent_actions else set()
        unexplored = [a for a in safe_actions if a not in recent_set]
        
        if unexplored:
            return unexplored[0]
        
        return safe_actions[0]
    
    def record_false_positive(self, pattern_id: str):
        """
        Record when a pattern warning was heeded but game_over didn't happen anyway.
        
        This helps reduce confidence in patterns that aren't reliable predictors.
        """
        try:
            self.db.execute_query("""
                UPDATE terminal_patterns
                SET false_positive_count = false_positive_count + 1,
                    confidence = MAX(0.3, confidence - 0.02)
                WHERE pattern_id = ?
            """, (pattern_id,))
        except Exception:
            pass
    
    def get_game_terminal_stats(self, game_id: str) -> Dict[str, Any]:
        """Get terminal pattern statistics for a game."""
        try:
            stats = self.db.execute_query("""
                SELECT 
                    COUNT(*) as total_patterns,
                    SUM(confirmed_lethal) as total_deaths,
                    AVG(confidence) as avg_confidence,
                    MAX(occurrence_count) as max_occurrences
                FROM terminal_patterns
                WHERE game_id = ? AND is_active = 1
            """, (game_id,))
            
            if stats:
                return {
                    'total_patterns': stats[0]['total_patterns'] or 0,
                    'total_deaths': stats[0]['total_deaths'] or 0,
                    'avg_confidence': stats[0]['avg_confidence'] or 0,
                    'max_occurrences': stats[0]['max_occurrences'] or 0
                }
            return {}
        except Exception:
            return {}
    
    def cleanup_low_confidence_patterns(self, 
                                         min_confidence: float = 0.4,
                                         min_occurrences: int = 3):
        """Remove patterns that haven't proven reliable."""
        try:
            self.db.execute_query("""
                UPDATE terminal_patterns
                SET is_active = 0
                WHERE confidence < ?
                  AND occurrence_count >= ?
                  AND false_positive_count > confirmed_lethal
            """, (min_confidence, min_occurrences))
        except Exception:
            pass
