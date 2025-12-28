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
4. SPATIAL DEATH ZONES - where on the grid game-overs happen

OPTIMIZATION (Dec 2025):
- Only check terminal patterns in LAST 30% of sequence (or when stuck)
- Track death ZONES (spatial regions) not just action patterns
- Visual foresight: "object in region X = danger"

Before taking any action, check:
- Am I in a state similar to one that led to game_over?
- Is the action I'm about to take the same as the fatal action?
- Is my controlled object approaching a known death zone?
- If yes, suggest an alternative

IMPLEMENTATION:
1. On game_over: Record (frame_hash, last_5_actions, fatal_action) as "terminal signature"
2. On game_over: Record object positions as "death zones" (spatial)
3. On action selection (near sequence end): Check if planned action leads to death zone
4. If match: Return alternative action and reasoning
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
        """Create terminal_patterns and death_zones tables if they don't exist."""
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
            
            # ================================================================
            # DEATH ZONES TABLE - Spatial danger regions per level
            # ================================================================
            # Tracks WHERE on the grid game-overs happen
            # More intuitive: "objects in region X,Y = danger"
            # ================================================================
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS death_zones (
                    zone_id TEXT PRIMARY KEY,
                    game_type TEXT NOT NULL,
                    level_number INTEGER NOT NULL,
                    
                    -- Spatial bounding box (grid coordinates)
                    x_min INTEGER NOT NULL,
                    x_max INTEGER NOT NULL,
                    y_min INTEGER NOT NULL,
                    y_max INTEGER NOT NULL,
                    
                    -- What was at this location during death?
                    death_colors TEXT,              -- JSON: colors of objects at death location
                    object_signature TEXT,          -- Hash of object pattern that died here
                    
                    -- Reliability tracking
                    death_count INTEGER DEFAULT 1,
                    survival_count INTEGER DEFAULT 0,  -- Times objects passed through safely
                    danger_score REAL DEFAULT 0.7,     -- death_count / (death_count + survival_count)
                    
                    -- Metadata
                    discovered_at TEXT,
                    last_death_at TEXT,
                    is_active INTEGER DEFAULT 1
                )
            """)
            
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_death_zones_lookup
                ON death_zones (game_type, level_number, is_active)
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
    # ========================================================================
    # DEATH ZONE METHODS - Spatial danger tracking
    # ========================================================================
    
    def record_death_zone(self,
                          game_type: str,
                          level_number: int,
                          frame_before_death: List[List[int]],
                          controlled_objects: Optional[List[Dict]] = None) -> Optional[str]:
        """
        Record a death zone when game_over occurs.
        
        Analyzes the frame to find where controlled objects were located
        and marks that region as a danger zone.
        
        Args:
            game_type: Game type (e.g., 'as66', 'sp80')
            level_number: Level where death occurred
            frame_before_death: Frame state before game_over
            controlled_objects: List of objects the agent was controlling
            
        Returns:
            zone_id if recorded, None if failed
        """
        try:
            if not frame_before_death:
                return None
            
            # Find non-background objects in frame that might be player-controlled
            # Look for rare colors (likely player) or objects near edges (common death zones)
            death_positions = []
            death_colors = set()
            
            height = len(frame_before_death)
            width = len(frame_before_death[0]) if frame_before_death else 0
            
            # If controlled objects provided, use those positions
            if controlled_objects:
                for obj in controlled_objects:
                    if 'x' in obj and 'y' in obj:
                        death_positions.append((obj['x'], obj['y']))
                        if 'color' in obj:
                            death_colors.add(obj['color'])
            else:
                # Auto-detect: Find rare colors (likely player-controlled)
                color_counts = {}
                for y, row in enumerate(frame_before_death):
                    for x, color in enumerate(row):
                        if color != 0:  # Skip background
                            color_counts[color] = color_counts.get(color, 0) + 1
                
                if color_counts:
                    # Find rarest non-zero color (likely player)
                    min_count = min(color_counts.values())
                    rare_colors = [c for c, cnt in color_counts.items() if cnt <= min_count * 2]
                    
                    # Record positions of rare colors
                    for y, row in enumerate(frame_before_death):
                        for x, color in enumerate(row):
                            if color in rare_colors:
                                death_positions.append((x, y))
                                death_colors.add(color)
            
            if not death_positions:
                return None
            
            # Calculate bounding box of death positions
            x_coords = [p[0] for p in death_positions]
            y_coords = [p[1] for p in death_positions]
            
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)
            
            # Expand zone slightly for margin
            x_min = max(0, x_min - 1)
            x_max = min(width - 1, x_max + 1)
            y_min = max(0, y_min - 1)
            y_max = min(height - 1, y_max + 1)
            
            # Check for existing overlapping zone
            zone_signature = f"{x_min}-{x_max}-{y_min}-{y_max}"
            zone_id = f"dz_{game_type}_{level_number}_{hashlib.md5(zone_signature.encode()).hexdigest()[:8]}"
            
            existing = self.db.execute_query("""
                SELECT zone_id, death_count FROM death_zones
                WHERE game_type = ? AND level_number = ?
                  AND x_min = ? AND x_max = ? AND y_min = ? AND y_max = ?
                  AND is_active = 1
            """, (game_type, level_number, x_min, x_max, y_min, y_max))
            
            now = datetime.now().isoformat()
            
            if existing:
                # Update existing zone
                self.db.execute_query("""
                    UPDATE death_zones
                    SET death_count = death_count + 1,
                        danger_score = CAST(death_count + 1 AS REAL) / 
                                       CAST(death_count + 1 + survival_count AS REAL),
                        last_death_at = ?
                    WHERE zone_id = ?
                """, (now, existing[0]['zone_id']))
                
                logger.info(f"[DEATH-ZONE] Updated zone {existing[0]['zone_id'][:12]} "
                           f"(deaths: {existing[0]['death_count'] + 1})")
                return existing[0]['zone_id']
            
            # Create new zone
            self.db.execute_query("""
                INSERT INTO death_zones (
                    zone_id, game_type, level_number,
                    x_min, x_max, y_min, y_max,
                    death_colors, object_signature,
                    death_count, survival_count, danger_score,
                    discovered_at, last_death_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0, 0.7, ?, ?, 1)
            """, (
                zone_id, game_type, level_number,
                x_min, x_max, y_min, y_max,
                json.dumps(list(death_colors)),
                hashlib.md5(str(sorted(death_positions)).encode()).hexdigest()[:12],
                now, now
            ))
            
            logger.info(f"[DEATH-ZONE] New zone recorded: {zone_id} at ({x_min},{y_min})-({x_max},{y_max})")
            return zone_id
            
        except Exception as e:
            logger.debug(f"Error recording death zone: {e}")
            return None
    
    def check_death_zones(self,
                          game_type: str,
                          level_number: int,
                          object_positions: List[Tuple[int, int]],
                          planned_direction: Optional[int] = None,
                          min_danger: float = 0.6) -> Optional[Dict[str, Any]]:
        """
        Check if objects are in or approaching death zones.
        
        Args:
            game_type: Current game type
            level_number: Current level
            object_positions: List of (x, y) positions of controlled objects
            planned_direction: Movement direction (1=up, 2=down, 3=right, 4=left)
            min_danger: Minimum danger_score to trigger warning
            
        Returns:
            None if safe, or Dict with danger info
        """
        try:
            if not object_positions:
                return None
            
            # Get death zones for this level
            zones = self.db.execute_query("""
                SELECT zone_id, x_min, x_max, y_min, y_max, 
                       death_count, danger_score
                FROM death_zones
                WHERE game_type = ? AND level_number = ?
                  AND danger_score >= ? AND is_active = 1
                ORDER BY danger_score DESC
            """, (game_type, level_number, min_danger))
            
            if not zones:
                return None
            
            # Direction offsets for movement prediction
            direction_offset = {
                1: (0, -1),   # UP
                2: (0, 1),    # DOWN
                3: (1, 0),    # RIGHT
                4: (-1, 0)    # LEFT
            }
            
            for x, y in object_positions:
                for zone in zones:
                    # Check if currently IN zone
                    in_zone = (zone['x_min'] <= x <= zone['x_max'] and 
                              zone['y_min'] <= y <= zone['y_max'])
                    
                    # Check if MOVING INTO zone
                    moving_into_zone = False
                    if planned_direction and planned_direction in direction_offset:
                        dx, dy = direction_offset[planned_direction]
                        next_x, next_y = x + dx, y + dy
                        moving_into_zone = (zone['x_min'] <= next_x <= zone['x_max'] and
                                           zone['y_min'] <= next_y <= zone['y_max'])
                    
                    if in_zone or moving_into_zone:
                        # Find safe direction (opposite of danger)
                        safe_direction = self._find_safe_direction(
                            x, y, zone, planned_direction
                        )
                        
                        return {
                            'warning': True,
                            'zone_id': zone['zone_id'],
                            'danger_score': zone['danger_score'],
                            'death_count': zone['death_count'],
                            'current_position': (x, y),
                            'in_zone': in_zone,
                            'moving_into_zone': moving_into_zone,
                            'safe_direction': safe_direction,
                            'reason': f"Death zone at ({zone['x_min']},{zone['y_min']})-({zone['x_max']},{zone['y_max']}) "
                                     f"({zone['death_count']} deaths)"
                        }
            
            return None
            
        except Exception as e:
            logger.debug(f"Death zone check failed: {e}")
            return None
    
    def _find_safe_direction(self, x: int, y: int, zone: Dict, 
                             avoid_direction: Optional[int] = None) -> int:
        """Find a direction that moves away from the death zone."""
        # Calculate center of death zone
        zone_center_x = (zone['x_min'] + zone['x_max']) / 2
        zone_center_y = (zone['y_min'] + zone['y_max']) / 2
        
        # Move away from zone center
        dx = x - zone_center_x
        dy = y - zone_center_y
        
        # Prioritize movement based on distance from zone
        if abs(dx) > abs(dy):
            # Move horizontally
            safe = 3 if dx > 0 else 4  # RIGHT or LEFT
        else:
            # Move vertically
            safe = 2 if dy > 0 else 1  # DOWN or UP
        
        # If safe direction is same as avoid, try perpendicular
        if safe == avoid_direction:
            if safe in [1, 2]:  # Was vertical, try horizontal
                safe = 3 if dx >= 0 else 4
            else:  # Was horizontal, try vertical
                safe = 2 if dy >= 0 else 1
        
        return safe
    
    def record_zone_survival(self, game_type: str, level_number: int,
                             positions: List[Tuple[int, int]]):
        """Record when objects pass through a death zone safely."""
        try:
            zones = self.db.execute_query("""
                SELECT zone_id, x_min, x_max, y_min, y_max
                FROM death_zones
                WHERE game_type = ? AND level_number = ? AND is_active = 1
            """, (game_type, level_number))
            
            for x, y in positions:
                for zone in zones:
                    if (zone['x_min'] <= x <= zone['x_max'] and 
                        zone['y_min'] <= y <= zone['y_max']):
                        # Object survived in zone - reduce danger score
                        self.db.execute_query("""
                            UPDATE death_zones
                            SET survival_count = survival_count + 1,
                                danger_score = CAST(death_count AS REAL) / 
                                               CAST(death_count + survival_count + 1 AS REAL)
                            WHERE zone_id = ?
                        """, (zone['zone_id'],))
        except Exception:
            pass
    
    def should_check_foresight(self, 
                                sequence_progress: float, 
                                actions_since_progress: int,
                                stuck_threshold: int = 15) -> bool:
        """
        Determine if we should check terminal foresight.
        
        Optimization: Only check in last 5-10% of sequence or when stuck.
        
        Args:
            sequence_progress: How far through sequence (0.0 to 1.0)
            actions_since_progress: Actions since last score increase
            stuck_threshold: Actions without progress to consider "stuck"
            
        Returns:
            True if should check foresight, False to skip
        """
        # Check in last 10% of sequence (game-overs happen at very end)
        if sequence_progress >= 0.90:
            return True
        
        # Check if stuck (no progress for a while)
        if actions_since_progress >= stuck_threshold:
            return True
        
        # Check if very close to end (last 5 actions regardless of length)
        # This is handled by caller knowing remaining actions
        
        return False
    
    def get_level_death_zones(self, game_type: str, level_number: int) -> List[Dict]:
        """Get all active death zones for a level."""
        try:
            zones = self.db.execute_query("""
                SELECT zone_id, x_min, x_max, y_min, y_max,
                       death_count, danger_score, death_colors
                FROM death_zones
                WHERE game_type = ? AND level_number = ? AND is_active = 1
                ORDER BY danger_score DESC
            """, (game_type, level_number))
            
            return zones or []
        except Exception:
            return []