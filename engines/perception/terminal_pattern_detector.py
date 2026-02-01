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

REFACTORED (Jan 2026):
- Subsystems extracted to engines/perception/terminal/:
  - death_zones.py: Spatial danger region tracking
  - dangerous_objects.py: Color/pattern-based danger detection
  - game_over_theory.py: Human-readable failure hypotheses
- This file remains the main entry point for backward compatibility
"""

import json
import hashlib
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from database_interface import DatabaseInterface

# Import extracted subsystems
from engines.perception.terminal.death_zones import DeathZoneTracker
from engines.perception.terminal.dangerous_objects import DangerousObjectTracker
from engines.perception.terminal.game_over_theory import GameOverTheoryGenerator

logger = logging.getLogger(__name__)


class TerminalPatternDetector:
    """
    Provides foresight to avoid game_over by pattern matching against
    previously observed terminal states.
    
    KEY INSIGHT: It's not just the action that kills you - it's the
    combination of STATE + ACTION (position) that leads to terminal.
    
    CONSOLIDATION (Jan 2026):
    All death tracking uses position_death_patterns table exclusively.
    Position-bucket fuzzy matching (8x8 pixel regions) is more robust than
    exact frame_hash matching.
    
    REFACTORED (Jan 2026):
    Delegates to specialized subsystems:
    - DeathZoneTracker: Spatial danger regions
    - DangerousObjectTracker: Color/pattern danger
    - GameOverTheoryGenerator: Human-readable theories
    """
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
        self._ensure_tables_exist()
        self._cache_generation: int = -1
        
        # Initialize subsystems
        self._death_zones = DeathZoneTracker(db)
        self._dangerous_objects = DangerousObjectTracker(db)
        self._theory_generator = GameOverTheoryGenerator(db)
        
    def _ensure_tables_exist(self):
        """Create position_death_patterns and death_zones tables if they don't exist."""
        try:
            # ================================================================
            # DEATH ZONES TABLE - Spatial danger regions per level
            # ================================================================
            # Tracks WHERE on the grid game-overs happen
            # More intuitive: "objects in region X,Y = danger"
            # Dynamic zones: Enemies may move, so zones can shift or be temporary
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
                    
                    -- Challenge/validation tracking
                    last_challenged_at TEXT,        -- When an agent last tested this zone
                    challenge_count INTEGER DEFAULT 0, -- Times zone was deliberately tested
                    last_validated_at TEXT,         -- When zone was last confirmed dangerous
                    generations_since_death INTEGER DEFAULT 0, -- For decay/challenge timing
                    
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
            
            # ================================================================
            # DANGEROUS OBJECTS TABLE - Pattern-based danger detection
            # ================================================================
            # Tracks WHAT (color/shape) killed the agent, not just WHERE
            # If red enemy at (15,23) kills you, ALL red enemies are suspect
            # ================================================================
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS dangerous_objects (
                    object_id TEXT PRIMARY KEY,
                    game_type TEXT NOT NULL,
                    level_number INTEGER NOT NULL,
                    
                    -- Object characteristics
                    object_color INTEGER NOT NULL,           -- The color that caused death
                    object_size INTEGER DEFAULT 1,           -- Approximate pixel count
                    contact_type TEXT DEFAULT 'collision',   -- collision, proximity, spawn
                    
                    -- What was the player doing when killed?
                    fatal_action INTEGER,                    -- Action that led to death
                    player_color INTEGER,                    -- Color of player object
                    
                    -- Reliability tracking
                    kill_count INTEGER DEFAULT 1,
                    safe_contact_count INTEGER DEFAULT 0,    -- Times touched safely
                    danger_score REAL DEFAULT 0.8,
                    
                    -- Propagation tracking
                    suspected_instances INTEGER DEFAULT 0,   -- Other locations marked suspicious
                    confirmed_kills INTEGER DEFAULT 0,       -- Kills at other suspected locations
                    
                    -- Metadata
                    discovered_at TEXT,
                    last_kill_at TEXT,
                    is_active INTEGER DEFAULT 1
                )
            """)
            
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_dangerous_objects_lookup
                ON dangerous_objects (game_type, level_number, object_color, is_active)
            """)
            
            # ================================================================
            # ACTION-TRIGGERED DANGERS - Actions that spawn threats
            # ================================================================
            # Tracks when an action CREATES a dangerous situation
            # e.g., pressing ACTION5 spawns an enemy, clicking spawns a trap
            # ================================================================
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS action_triggered_dangers (
                    trigger_id TEXT PRIMARY KEY,
                    game_type TEXT NOT NULL,
                    level_number INTEGER NOT NULL,
                    
                    -- What action triggered the danger?
                    trigger_action INTEGER NOT NULL,
                    trigger_x INTEGER,                       -- Click coordinates if ACTION6
                    trigger_y INTEGER,
                    
                    -- What appeared after the action?
                    spawned_color INTEGER,                   -- Color of spawned danger
                    spawned_positions TEXT,                  -- JSON: [(x,y), ...] where things appeared
                    
                    -- How quickly did death follow?
                    actions_until_death INTEGER DEFAULT 1,
                    
                    -- Reliability
                    occurrence_count INTEGER DEFAULT 1,
                    danger_score REAL DEFAULT 0.7,
                    
                    -- Metadata
                    discovered_at TEXT,
                    is_active INTEGER DEFAULT 1
                )
            """)
            
            # ================================================================
            # RELATIVE THREAT PATTERNS - Context-dependent action safety
            # ================================================================
            # KEY INSIGHT: Deaths should be encoded with RELATIVE spatial context
            # "ACTION4 killed when threat was at relative position (-1, 0)"
            # NOT "ACTION4 is always dangerous" (blanket avoidance)
            # 
            # This enables agents to learn:
            # - "Don't move LEFT when enemy is to my left"
            # - "Moving LEFT is safe when enemy is above me"
            # ================================================================
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS relative_threat_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    game_type TEXT NOT NULL,
                    level_number INTEGER NOT NULL,
                    
                    -- The fatal action
                    fatal_action INTEGER NOT NULL,
                    
                    -- Threat context at time of death (relative to agent)
                    -- JSON: [{"color": 7, "rel_x": -1, "rel_y": 0, "distance": 1}, ...]
                    -- rel_x/rel_y: threat position relative to agent (negative = left/up)
                    threat_relative_positions TEXT NOT NULL,
                    
                    -- What color was the threat that likely killed us?
                    threat_color INTEGER,
                    
                    -- Agent's movement direction (1=up, 2=down, 3=right, 4=left)
                    -- Helps identify "moved toward threat" patterns
                    movement_direction TEXT,
                    
                    -- Pattern reliability
                    occurrence_count INTEGER DEFAULT 1,
                    confirmed_lethal INTEGER DEFAULT 1,
                    
                    -- Metadata
                    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_occurrence TIMESTAMP,
                    discovered_by_agent TEXT,
                    
                    -- Confidence that this relative pattern predicts danger
                    confidence REAL DEFAULT 0.6,
                    
                    is_active INTEGER DEFAULT 1
                )
            """)
            
            # Index for fast relative threat lookups
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_relative_threat_lookup
                ON relative_threat_patterns (game_type, level_number, fatal_action, is_active)
            """)
            
            # ================================================================
            # POSITION-BUCKET DEATH PATTERNS - Simple fuzzy position tracking
            # ================================================================
            # The simplest and most robust approach:
            # Divide grid into buckets (e.g., 8x8 regions)
            # Track: At bucket (X,Y) on level L, action A killed N times
            # This generalizes across similar positions without exact matching
            # 
            # Key: bucket_size determines granularity (8 = 64x64 becomes 8x8)
            # ================================================================
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS position_death_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    game_type TEXT NOT NULL,
                    level_number INTEGER NOT NULL,
                    
                    -- Position bucket (grid divided by bucket_size)
                    bucket_x INTEGER NOT NULL,
                    bucket_y INTEGER NOT NULL,
                    bucket_size INTEGER DEFAULT 8,
                    
                    -- The fatal action at this position
                    fatal_action INTEGER NOT NULL,
                    
                    -- Death/survival tracking
                    death_count INTEGER DEFAULT 1,
                    survival_count INTEGER DEFAULT 0,
                    
                    -- Calculated danger: death_count / (death_count + survival_count)
                    danger_score REAL DEFAULT 0.8,
                    
                    -- Decay support: If proven wrong, weaken over time
                    last_death_at TEXT,
                    last_survival_at TEXT,
                    generations_since_update INTEGER DEFAULT 0,
                    
                    -- Metadata
                    discovered_at TEXT,
                    discovered_by_agent TEXT,
                    is_active INTEGER DEFAULT 1,
                    
                    UNIQUE(game_type, level_number, bucket_x, bucket_y, fatal_action)
                )
            """)
            
            # Index for fast position-based lookups
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_position_death_lookup
                ON position_death_patterns (game_type, level_number, bucket_x, bucket_y, is_active)
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
                                 generation: int,
                                 position: Optional[Tuple[int, int]] = None) -> Optional[str]:
        """
        Record a terminal pattern after game_over occurs.
        
        DEPRECATED: This method now redirects to record_position_death().
        Use record_position_death() directly for new code.
        
        Args:
            game_id: Game where death occurred
            level_number: Level where death occurred
            frame_before_death: The frame state right before the fatal action (unused)
            pre_death_actions: Last 5 actions taken before death (unused)
            fatal_action: The action that caused game_over
            agent_id: Agent who died
            generation: Current generation (unused)
            position: (x, y) position - if not provided, uses (0, 0)
            
        Returns:
            pattern_id if recorded, None if failed
        """
        # Extract game_type from game_id
        game_type = game_id.split('-')[0] if '-' in game_id else game_id
        
        # Use provided position or default to (0, 0) for level-wide tracking
        pos = position if position else (0, 0)
        
        # Redirect to position_death_patterns
        return self.record_position_death(
            game_type=game_type,
            level_number=level_number,
            position=pos,
            fatal_action=fatal_action,
            agent_id=agent_id,
            bucket_size=8
        )
    
    # ========================================================================
    # RELATIVE THREAT PATTERN SYSTEM
    # ========================================================================
    # Context-dependent action safety: "ACTION4 is dangerous when enemy is to my left"
    # NOT blanket avoidance: "ACTION4 is always dangerous"
    # ========================================================================
    
    def record_relative_threat_pattern(
        self,
        game_id: str,
        level_number: int,
        fatal_action: int,
        agent_position: Tuple[int, int],  # (x, y)
        frame_before_death: List[List[int]],
        agent_color: int,
        agent_id: str
    ) -> Optional[str]:
        """
        Record a death with RELATIVE threat positions.
        
        Instead of storing "ACTION4 at frame X killed me", this stores:
        "ACTION4 when threats were at relative positions [(−1,0), (0,−1)] killed me"
        
        This enables context-aware danger checking:
        - "Enemy to my left" + "I pressed LEFT" = danger
        - "Enemy above me" + "I pressed LEFT" = safe
        
        Args:
            game_id: Game where death occurred
            level_number: Level where death occurred  
            fatal_action: The action that caused game_over (1-7)
            agent_position: Agent's (x, y) position at time of death
            frame_before_death: Grid state before fatal action
            agent_color: Color of agent's controlled object
            agent_id: ID of agent who died
            
        Returns:
            pattern_id if recorded, None on failure
        """
        try:
            game_type = game_id.split('-')[0] if '-' in game_id else game_id
            
            if not frame_before_death or not agent_position:
                return None
            
            agent_x, agent_y = agent_position
            frame_arr = np.asarray(frame_before_death) if frame_before_death else None
            
            if frame_arr is None or frame_arr.size == 0:
                return None
            
            # Find all non-background, non-agent objects and compute relative positions
            threat_relatives = []
            height, width = frame_arr.shape
            
            for y in range(height):
                for x in range(width):
                    color = int(frame_arr[y, x])
                    # Skip background (0) and agent's own color
                    if color == 0 or color == agent_color:
                        continue
                    
                    # Compute relative position to agent
                    rel_x = x - agent_x  # Positive = right of agent
                    rel_y = y - agent_y  # Positive = below agent
                    distance = abs(rel_x) + abs(rel_y)  # Manhattan distance
                    
                    # Only track nearby threats (within 5 cells)
                    if distance <= 5:
                        threat_relatives.append({
                            'color': color,
                            'rel_x': rel_x,
                            'rel_y': rel_y,
                            'distance': distance
                        })
            
            # Sort by distance (closest threats first)
            threat_relatives.sort(key=lambda t: t['distance'])
            
            # Take the 3 closest threats
            closest_threats = threat_relatives[:3]
            
            if not closest_threats:
                # No threats nearby - this death wasn't threat-related
                return None
            
            # Determine likely killer (closest threat)
            threat_color = closest_threats[0]['color'] if closest_threats else None
            
            # Determine movement direction from action
            direction_map = {1: 'up', 2: 'down', 3: 'right', 4: 'left', 5: 'wait', 6: 'click', 7: 'undo'}
            movement_direction = direction_map.get(fatal_action, 'unknown')
            
            # Create pattern signature for deduplication
            # Group similar relative positions together
            threat_sig = json.dumps(sorted([
                (t['rel_x'], t['rel_y'], t['color']) 
                for t in closest_threats
            ]))
            pattern_hash = hashlib.md5(
                f"{game_type}_{level_number}_{fatal_action}_{threat_sig}".encode()
            ).hexdigest()[:12]
            
            pattern_id = f"relthreat_{game_type}_{level_number}_{pattern_hash}"
            
            # Check for existing similar pattern
            existing = self.db.execute_query("""
                SELECT pattern_id, occurrence_count
                FROM relative_threat_patterns
                WHERE pattern_id = ? AND is_active = 1
            """, (pattern_id,))
            
            if existing:
                # Update existing pattern
                self.db.execute_query("""
                    UPDATE relative_threat_patterns
                    SET occurrence_count = occurrence_count + 1,
                        confirmed_lethal = confirmed_lethal + 1,
                        confidence = MIN(0.95, confidence + 0.05),
                        last_occurrence = CURRENT_TIMESTAMP
                    WHERE pattern_id = ?
                """, (pattern_id,))
                
                new_count = existing[0]['occurrence_count'] + 1
                logger.info(f"[REL-THREAT] Updated pattern: ACTION{fatal_action} + {movement_direction} "
                           f"with threat at rel({closest_threats[0]['rel_x']},{closest_threats[0]['rel_y']}) "
                           f"(now {new_count}x)")
                return pattern_id
            
            # Create new pattern
            self.db.execute_query("""
                INSERT INTO relative_threat_patterns (
                    pattern_id, game_type, level_number, fatal_action,
                    threat_relative_positions, threat_color, movement_direction,
                    occurrence_count, confirmed_lethal, discovered_by_agent, confidence, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1, ?, 0.6, 1)
            """, (
                pattern_id, game_type, level_number, fatal_action,
                json.dumps(closest_threats), threat_color, movement_direction,
                agent_id
            ))
            
            logger.info(f"[REL-THREAT] NEW: ACTION{fatal_action} ({movement_direction}) killed when "
                       f"color {threat_color} was at rel({closest_threats[0]['rel_x']},{closest_threats[0]['rel_y']})")
            
            return pattern_id
            
        except Exception as e:
            logger.debug(f"Error recording relative threat pattern: {e}")
            return None
    
    def check_relative_threat_danger(
        self,
        game_type: str,
        level_number: int,
        planned_action: int,
        agent_position: Tuple[int, int],  # (x, y)
        current_frame: List[List[int]],
        agent_color: int,
        min_confidence: float = 0.5
    ) -> Optional[Dict[str, Any]]:
        """
        Check if planned action is dangerous given CURRENT relative threat positions.
        
        This is the key insight: don't avoid ACTION4 everywhere, avoid it
        only when there's a threat in the direction you'd be moving.
        
        Args:
            game_type: Current game type
            level_number: Current level
            planned_action: Action about to be taken (1-7)
            agent_position: Agent's current (x, y) position
            current_frame: Current grid state
            agent_color: Agent's controlled object color
            min_confidence: Minimum confidence to trigger warning
            
        Returns:
            None if safe, or Dict with danger info and suggested alternatives
        """
        try:
            if not current_frame or not agent_position:
                return None
            
            agent_x, agent_y = agent_position
            frame_arr = np.asarray(current_frame)
            
            if frame_arr.size == 0:
                return None
            
            # Compute current relative threat positions
            current_threats = []
            height, width = frame_arr.shape
            
            for y in range(height):
                for x in range(width):
                    color = int(frame_arr[y, x])
                    if color == 0 or color == agent_color:
                        continue
                    
                    rel_x = x - agent_x
                    rel_y = y - agent_y
                    distance = abs(rel_x) + abs(rel_y)
                    
                    if distance <= 5:
                        current_threats.append({
                            'color': color,
                            'rel_x': rel_x,
                            'rel_y': rel_y,
                            'distance': distance
                        })
            
            if not current_threats:
                return None  # No nearby threats, action is safe
            
            # Query for matching relative threat patterns
            patterns = self.db.execute_query("""
                SELECT pattern_id, fatal_action, threat_relative_positions, 
                       threat_color, movement_direction, occurrence_count, confidence
                FROM relative_threat_patterns
                WHERE game_type = ? AND level_number = ? 
                  AND fatal_action = ?
                  AND confidence >= ?
                  AND is_active = 1
                ORDER BY confidence DESC, occurrence_count DESC
                LIMIT 10
            """, (game_type, level_number, planned_action, min_confidence))
            
            if not patterns:
                return None  # No patterns for this action
            
            # Check if current threat configuration matches any known deadly pattern
            for pattern in patterns:
                try:
                    recorded_threats = json.loads(pattern['threat_relative_positions'])
                except (json.JSONDecodeError, TypeError):
                    continue
                
                # Check if any recorded threat position matches current situation
                for rec_threat in recorded_threats:
                    rec_rel_x = rec_threat.get('rel_x', 999)
                    rec_rel_y = rec_threat.get('rel_y', 999)
                    rec_color = rec_threat.get('color')
                    
                    # Look for matching current threat
                    for cur_threat in current_threats:
                        # Match if same relative position (±1 tolerance) and same color
                        if (abs(cur_threat['rel_x'] - rec_rel_x) <= 1 and
                            abs(cur_threat['rel_y'] - rec_rel_y) <= 1 and
                            (rec_color is None or cur_threat['color'] == rec_color)):
                            
                            # DANGER: Current situation matches a known deadly pattern!
                            direction_map = {1: 'up', 2: 'down', 3: 'right', 4: 'left'}
                            movement = direction_map.get(planned_action, 'move')
                            
                            # Suggest alternative: opposite direction or wait
                            opposite = {1: 2, 2: 1, 3: 4, 4: 3, 5: 5, 6: 5, 7: 5}
                            suggested_alternative = opposite.get(planned_action, 5)
                            
                            return {
                                'danger': True,
                                'pattern_id': pattern['pattern_id'],
                                'reason': f"Moving {movement} with color {cur_threat['color']} at relative ({cur_threat['rel_x']},{cur_threat['rel_y']}) has killed {pattern['occurrence_count']}x",
                                'confidence': pattern['confidence'],
                                'threat_color': cur_threat['color'],
                                'threat_relative_pos': (cur_threat['rel_x'], cur_threat['rel_y']),
                                'suggested_alternative': suggested_alternative,
                                'suggestion': f"Try ACTION{suggested_alternative} instead (move away or wait)"
                            }
            
            return None  # No matching dangerous patterns
            
        except Exception as e:
            logger.debug(f"Error checking relative threat danger: {e}")
            return None
    
    def check_for_terminal_danger(self,
                                   game_id: str,
                                   level_number: int,
                                   current_frame: List[List[int]],
                                   recent_actions: List[int],
                                   planned_action: int,
                                   min_confidence: float = 0.6,
                                   position: Optional[Tuple[int, int]] = None) -> Optional[Dict[str, Any]]:
        """
        Check if the planned action might lead to game_over.
        
        DEPRECATED: This method now redirects to check_position_danger().
        Use check_position_danger() directly for new code.
        
        Args:
            game_id: Current game
            level_number: Current level
            current_frame: Current game state (unused - position-bucket based now)
            recent_actions: Last few actions taken (unused)
            planned_action: Action we're about to take
            min_confidence: Minimum pattern confidence to trigger warning
            position: (x, y) position - required for position-bucket lookup
            
        Returns:
            None if safe, or Dict with warning info and alternative suggestion
        """
        # Extract game_type from game_id
        game_type = game_id.split('-')[0] if '-' in game_id else game_id
        
        # If no position provided, cannot do position-bucket lookup
        if not position:
            return None
        
        # Redirect to position_death_patterns via check_position_danger
        danger = self.check_position_danger(
            game_type=game_type,
            level_number=level_number,
            position=position,
            planned_action=planned_action,
            min_danger=min_confidence,
            bucket_size=8
        )
        
        if not danger:
            return None
        
        # Convert check_position_danger result format to old format for compatibility
        return {
            'warning': True,
            'pattern_id': danger.get('pattern_id', 'position_bucket'),
            'confidence': danger.get('danger_score', 0.7),
            'fatal_action': planned_action,
            'occurrence_count': danger.get('death_count', 0),
            'confirmed_lethal': danger.get('death_count', 0),
            'match_score': 0,  # Not used in position-bucket system
            'alternative_action': danger.get('suggested_alternative', 5),
            'reason': danger.get('reason', f"ACTION{planned_action} dangerous at this position")
        }
    
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
    
    def record_false_positive(self, pattern_id: str, 
                              game_type: Optional[str] = None,
                              level_number: Optional[int] = None,
                              position: Optional[Tuple[int, int]] = None,
                              action: Optional[int] = None):
        """
        Record when a pattern warning was heeded but game_over didn't happen anyway.
        
        DEPRECATED: Now uses position_death_patterns via record_position_survival.
        
        Args:
            pattern_id: Original pattern ID (for logging only)
            game_type: Game type for position lookup
            level_number: Level for position lookup
            position: (x, y) position where survival occurred
            action: Action that was taken and survived
        """
        # If we have position data, record survival to weaken the danger signal
        if game_type and level_number is not None and position and action:
            self.record_position_survival(
                game_type=game_type,
                level_number=level_number,
                position=position,
                action_taken=action,
                bucket_size=8
            )
    
    def get_game_terminal_stats(self, game_id: str) -> Dict[str, Any]:
        """
        Get terminal pattern statistics for a game.
        
        Now uses position_death_patterns as the single source of truth.
        """
        try:
            game_type = game_id.split('-')[0] if '-' in game_id else game_id
            
            stats = self.db.execute_query("""
                SELECT 
                    COUNT(*) as total_patterns,
                    SUM(death_count) as total_deaths,
                    AVG(danger_score) as avg_confidence,
                    MAX(death_count) as max_occurrences
                FROM position_death_patterns
                WHERE game_type = ? AND is_active = 1
            """, (game_type,))
            
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
        """
        Remove patterns that haven't proven reliable.
        
        Now uses position_death_patterns: deactivates patterns with
        low danger_score and high survival relative to deaths.
        """
        try:
            self.db.execute_query("""
                UPDATE position_death_patterns
                SET is_active = 0
                WHERE danger_score < ?
                  AND death_count >= ?
                  AND survival_count > death_count
            """, (min_confidence, min_occurrences))
        except Exception:
            pass
    # ========================================================================
    # DEATH ZONE METHODS - Delegated to DeathZoneTracker
    # ========================================================================
    
    def record_death_zone(self,
                          game_type: str,
                          level_number: int,
                          frame_before_death: List[List[int]],
                          controlled_objects: Optional[List[Dict]] = None) -> Optional[str]:
        """Record a death zone when game_over occurs. Delegates to DeathZoneTracker."""
        return self._death_zones.record_death_zone(
            game_type, level_number, frame_before_death, controlled_objects
        )
    
    def check_death_zones(self,
                          game_type: str,
                          level_number: int,
                          object_positions: List[Tuple[int, int]],
                          planned_direction: Optional[int] = None,
                          min_danger: float = 0.6) -> Optional[Dict[str, Any]]:
        """Check if objects are in or approaching death zones. Delegates to DeathZoneTracker."""
        return self._death_zones.check_death_zones(
            game_type, level_number, object_positions, planned_direction, min_danger
        )
    
    def record_zone_survival(self, game_type: str, level_number: int,
                             positions: List[Tuple[int, int]]):
        """Record when objects pass through a death zone safely. Delegates to DeathZoneTracker."""
        self._death_zones.record_zone_survival(game_type, level_number, positions)
    
    def should_check_foresight(self, 
                                sequence_progress: float, 
                                actions_since_progress: int,
                                stuck_threshold: int = 15) -> bool:
        """
        Determine if we should check terminal foresight.
        
        Optimization: Only check in last 5-10% of sequence or when stuck.
        """
        # Check in last 10% of sequence (game-overs happen at very end)
        if sequence_progress >= 0.90:
            return True
        
        # Check if stuck (no progress for a while)
        if actions_since_progress >= stuck_threshold:
            return True
        
        return False
    
    def get_level_death_zones(self, game_type: str, level_number: int) -> List[Dict]:
        """Get all active death zones for a level. Delegates to DeathZoneTracker."""
        return self._death_zones.get_level_death_zones(game_type, level_number)
    
    def should_challenge_zone(self, zone: Dict, generation: int) -> bool:
        """Determine if a death zone should be challenged. Delegates to DeathZoneTracker."""
        return self._death_zones.should_challenge_zone(zone, generation)
    
    def record_zone_challenge(self, zone_id: str, survived: bool, generation: int):
        """Record the result of challenging a death zone. Delegates to DeathZoneTracker."""
        self._death_zones.record_zone_challenge(zone_id, survived, generation)
    
    def decay_old_zones(self, generations_threshold: int = 10):
        """Decay danger scores for old zones. Delegates to DeathZoneTracker."""
        self._death_zones.decay_old_zones(generations_threshold)

    # ========================================================================
    # DANGEROUS OBJECT DETECTION - Delegated to DangerousObjectTracker
    # ========================================================================
    
    def record_dangerous_object(self,
                                 game_type: str,
                                 level_number: int,
                                 frame_before_death: List[List[int]],
                                 controlled_objects: List[Dict],
                                 fatal_action: int) -> Optional[str]:
        """Record dangerous object by color/pattern. Delegates to DangerousObjectTracker."""
        return self._dangerous_objects.record_dangerous_object(
            game_type, level_number, frame_before_death, controlled_objects, fatal_action
        )
    
    def check_dangerous_objects(self,
                                 game_type: str,
                                 level_number: int,
                                 current_frame: List[List[int]],
                                 object_positions: List[Tuple[int, int]],
                                 planned_action: int) -> Optional[Dict[str, Any]]:
        """Check if action would contact dangerous object. Delegates to DangerousObjectTracker."""
        return self._dangerous_objects.check_dangerous_objects(
            game_type, level_number, current_frame, object_positions, planned_action
        )
    
    def record_action_triggered_danger(self,
                                        game_type: str,
                                        level_number: int,
                                        trigger_action: int,
                                        frame_before: List[List[int]],
                                        frame_after: List[List[int]],
                                        actions_until_death: int,
                                        click_coords: Optional[Tuple[int, int]] = None) -> Optional[str]:
        """Record action that spawns threats. Delegates to DangerousObjectTracker."""
        return self._dangerous_objects.record_action_triggered_danger(
            game_type, level_number, trigger_action, frame_before, frame_after,
            actions_until_death, click_coords
        )

    # ========================================================================
    # GAME-OVER THEORY SYSTEM - Delegated to GameOverTheoryGenerator
    # ========================================================================
    
    def generate_game_over_theory(self, 
                                   game_id: str,
                                   level_number: int,
                                   frame_before_death: List[List[int]],
                                   fatal_action: int,
                                   pre_death_actions: List[int],
                                   controlled_objects: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Generate theory about why game-over occurred. Delegates to GameOverTheoryGenerator."""
        death_zones = self.get_level_death_zones(
            game_id.split('-')[0] if '-' in game_id else game_id, 
            level_number
        )
        return self._theory_generator.generate_game_over_theory(
            game_id, level_number, frame_before_death, fatal_action,
            pre_death_actions, controlled_objects, death_zones
        )
    
    def get_game_over_theories(self, game_id: str, level_number: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get existing game-over theories for a level. Delegates to GameOverTheoryGenerator."""
        return self._theory_generator.get_game_over_theories(game_id, level_number, limit)

    # ========================================================================
    # POSITION-BUCKET DEATH PATTERNS - Simple fuzzy position-based avoidance
    # ========================================================================
    # This is the simplest, most robust approach to position-based death tracking:
    # - Divide grid into buckets (default: 8 pixel buckets)
    # - Track deaths per (game_type, level, bucket, action)
    # - Strengthen on death, weaken on survival
    # ========================================================================
    
    def record_position_death(
        self,
        game_type: str,
        level_number: int,
        position: Tuple[int, int],
        fatal_action: int,
        agent_id: str = 'unknown',
        bucket_size: int = 8
    ) -> Optional[str]:
        """
        Record a death at a specific position bucket.
        
        This is the simplest form of position-based learning:
        - Bucket the position (e.g., (23, 15) with bucket_size=8 -> (2, 1))
        - Record that ACTION at this bucket on this level caused death
        - Future agents can check before taking same action
        
        Args:
            game_type: Game type (e.g., 'as66')
            level_number: Level where death occurred
            position: (x, y) position of agent at death
            fatal_action: Action that caused death (1-7)
            agent_id: Agent that discovered this
            bucket_size: Bucket granularity (8 = divide position by 8)
            
        Returns:
            Pattern ID if recorded
        """
        try:
            if not position or len(position) < 2:
                return None
            
            x, y = position
            bucket_x = x // bucket_size
            bucket_y = y // bucket_size
            
            # Unique pattern ID
            pattern_id = f"posdeath_{game_type}_{level_number}_{bucket_x}_{bucket_y}_{fatal_action}"
            now = datetime.now().isoformat()
            
            # Try to update existing pattern
            existing = self.db.execute_query("""
                SELECT pattern_id, death_count, survival_count
                FROM position_death_patterns
                WHERE game_type = ? AND level_number = ? 
                  AND bucket_x = ? AND bucket_y = ? AND fatal_action = ?
            """, (game_type, level_number, bucket_x, bucket_y, fatal_action))
            
            if existing:
                # Update existing pattern
                new_death_count = existing[0]['death_count'] + 1
                new_survival_count = existing[0]['survival_count']
                new_danger_score = new_death_count / (new_death_count + new_survival_count + 0.1)
                
                self.db.execute_query("""
                    UPDATE position_death_patterns
                    SET death_count = ?,
                        danger_score = ?,
                        last_death_at = ?,
                        generations_since_update = 0
                    WHERE pattern_id = ?
                """, (new_death_count, new_danger_score, now, existing[0]['pattern_id']))
                
                logger.info(f"[POS-DEATH] Updated: ({bucket_x*bucket_size},{bucket_y*bucket_size}) L{level_number} "
                           f"ACTION{fatal_action} deaths={new_death_count} danger={new_danger_score:.2f}")
                return existing[0]['pattern_id']
            
            # Create new pattern
            self.db.execute_query("""
                INSERT OR REPLACE INTO position_death_patterns (
                    pattern_id, game_type, level_number,
                    bucket_x, bucket_y, bucket_size, fatal_action,
                    death_count, survival_count, danger_score,
                    last_death_at, discovered_at, discovered_by_agent, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, 0, 0.8, ?, ?, ?, 1)
            """, (pattern_id, game_type, level_number, bucket_x, bucket_y, bucket_size,
                  fatal_action, now, now, agent_id))
            
            logger.info(f"[POS-DEATH] NEW: ({bucket_x*bucket_size},{bucket_y*bucket_size}) L{level_number} "
                       f"ACTION{fatal_action} - first recorded death in this position bucket")
            return pattern_id
            
        except Exception as e:
            logger.debug(f"Error recording position death: {e}")
            return None
    
    def record_position_survival(
        self,
        game_type: str,
        level_number: int,
        position: Tuple[int, int],
        action_taken: int,
        bucket_size: int = 8
    ):
        """
        Record that an action was taken at a position and the agent SURVIVED.
        
        This weakens the danger signal - if agents survive taking ACTION at POSITION,
        maybe it's not as deadly as we thought.
        
        Args:
            game_type: Game type
            level_number: Current level
            position: (x, y) agent position
            action_taken: Action that was taken (and survived)
            bucket_size: Bucket granularity (must match recording)
        """
        try:
            if not position or len(position) < 2:
                return
            
            x, y = position
            bucket_x = x // bucket_size
            bucket_y = y // bucket_size
            
            now = datetime.now().isoformat()
            
            # Update survival count for this position+action
            result = self.db.execute_query("""
                UPDATE position_death_patterns
                SET survival_count = survival_count + 1,
                    danger_score = CAST(death_count AS REAL) / 
                                   CAST(death_count + survival_count + 1 + 0.1 AS REAL),
                    last_survival_at = ?
                WHERE game_type = ? AND level_number = ?
                  AND bucket_x = ? AND bucket_y = ? AND fatal_action = ?
                  AND is_active = 1
            """, (now, game_type, level_number, bucket_x, bucket_y, action_taken))
            
            # Log significant updates (when danger score drops below threshold)
            if result:
                updated = self.db.execute_query("""
                    SELECT danger_score, death_count, survival_count
                    FROM position_death_patterns
                    WHERE game_type = ? AND level_number = ?
                      AND bucket_x = ? AND bucket_y = ? AND fatal_action = ?
                """, (game_type, level_number, bucket_x, bucket_y, action_taken))
                
                if updated and updated[0]['danger_score'] < 0.5:
                    logger.info(f"[POS-SURVIVAL] Weakening: ({bucket_x*bucket_size},{bucket_y*bucket_size}) L{level_number} "
                               f"ACTION{action_taken} danger={updated[0]['danger_score']:.2f} "
                               f"(deaths={updated[0]['death_count']}, survives={updated[0]['survival_count']})")
                    
        except Exception as e:
            logger.debug(f"Error recording position survival: {e}")
    
    def check_position_danger(
        self,
        game_type: str,
        level_number: int,
        position: Tuple[int, int],
        planned_action: int,
        min_danger: float = 0.6,
        bucket_size: int = 8,
        min_deaths: int = 1
    ) -> Optional[Dict[str, Any]]:
        """
        Check if planned action is dangerous at this position bucket.
        
        This is the FORESIGHT mechanism for position-based avoidance.
        
        Args:
            game_type: Current game type
            level_number: Current level  
            position: (x, y) agent position
            planned_action: Action agent wants to take
            min_danger: Minimum danger_score to trigger warning (default 0.6)
            bucket_size: Bucket granularity
            min_deaths: Minimum death count required (default 1, FIX 2026-01-29: recommend 5)
            
        Returns:
            None if safe, or Dict with danger info and alternative suggestion
        """
        try:
            if not position or len(position) < 2:
                return None
            
            x, y = position
            bucket_x = x // bucket_size
            bucket_y = y // bucket_size
            
            # Check for deadly pattern at this position
            # FIX (2026-01-29): Added min_deaths filter to require pattern confirmation
            pattern = self.db.execute_query("""
                SELECT pattern_id, death_count, survival_count, danger_score, last_death_at
                FROM position_death_patterns
                WHERE game_type = ? AND level_number = ?
                  AND bucket_x = ? AND bucket_y = ? AND fatal_action = ?
                  AND danger_score >= ?
                  AND death_count >= ?
                  AND is_active = 1
                ORDER BY danger_score DESC
                LIMIT 1
            """, (game_type, level_number, bucket_x, bucket_y, planned_action, min_danger, min_deaths))
            
            if not pattern:
                return None  # No danger at this position for this action
            
            p = pattern[0]
            
            # Suggest alternative action (opposite direction or wait)
            opposite = {1: 2, 2: 1, 3: 4, 4: 3, 5: 5, 6: 5, 7: 5}
            suggested_alternative = opposite.get(planned_action, 5)  # Default to wait
            
            action_names = {1: 'UP', 2: 'DOWN', 3: 'RIGHT', 4: 'LEFT', 5: 'WAIT', 6: 'CLICK', 7: 'NOOP'}
            
            return {
                'danger': True,
                'pattern_id': p['pattern_id'],
                'position_bucket': (bucket_x * bucket_size, bucket_y * bucket_size),
                'death_count': p['death_count'],
                'survival_count': p['survival_count'],
                'danger_score': p['danger_score'],
                'reason': f"ACTION{planned_action} ({action_names.get(planned_action, '?')}) killed {p['death_count']}x "
                         f"at position bucket ({bucket_x*bucket_size},{bucket_y*bucket_size}) on level {level_number}",
                'suggested_alternative': suggested_alternative,
                'suggestion': f"Try ACTION{suggested_alternative} ({action_names.get(suggested_alternative, '?')}) instead"
            }
            
        except Exception as e:
            logger.debug(f"Error checking position danger: {e}")
            return None
    
    def get_graduated_action_weights(
        self,
        game_type: str,
        level_number: int,
        position: Optional[Tuple[int, int]],
        bucket_size: int = 8,
        generations_since_threshold: int = 50,
        frontier_mode: bool = False
    ) -> Dict[int, float]:
        """
        Get GRADUATED safety weights for all 7 actions at once.
        
        This replaces binary "dangerous/safe" with continuous weights:
        - 1.0 = fully safe (no deaths, or many survivals)
        - 0.0 = extremely dangerous (many deaths, no survivals)
        
        NEVER returns 0.0 - worst case is 0.05 so action is still possible.
        
        Formula per action:
            base_danger = death_count / (death_count + survival_count + 1)
            time_decay = 0.5 ** (generations_since_update / 10)
            survival_boost = 1.0 / (1.0 + survivals * 0.2)
            sample_confidence = min(1.0, total_samples / 10)
            
            danger = base_danger * time_decay * survival_boost * sample_confidence
            safety_weight = 1.0 - danger
            
        Args:
            game_type: Current game type
            level_number: Current level
            position: (x, y) or None for level-wide aggregation
            bucket_size: Bucket granularity
            generations_since_threshold: Ignore patterns older than this
            frontier_mode: If True, heavily favor exploration (reduce danger signals)
            
        Returns:
            Dict mapping action (1-7) to safety weight (0.05-1.0)
        """
        # Start with all actions at weight 1.0 (fully safe)
        weights: Dict[int, float] = {i: 1.0 for i in range(1, 8)}
        
        try:
            if position and len(position) >= 2:
                x, y = position
                bucket_x = x // bucket_size
                bucket_y = y // bucket_size
                
                # Query ALL death patterns at this position bucket
                patterns = self.db.execute_query("""
                    SELECT fatal_action, death_count, survival_count, danger_score,
                           generations_since_update
                    FROM position_death_patterns
                    WHERE game_type = ? AND level_number = ?
                      AND bucket_x BETWEEN ? AND ?
                      AND bucket_y BETWEEN ? AND ?
                      AND is_active = 1
                      AND generations_since_update < ?
                """, (game_type, level_number, 
                      bucket_x - 1, bucket_x + 1,  # Adjacent buckets for fuzzy matching
                      bucket_y - 1, bucket_y + 1,
                      generations_since_threshold))
            else:
                # No position - aggregate level-wide deaths
                patterns = self.db.execute_query("""
                    SELECT fatal_action, 
                           SUM(death_count) as death_count,
                           SUM(survival_count) as survival_count,
                           AVG(danger_score) as danger_score,
                           MIN(generations_since_update) as generations_since_update
                    FROM position_death_patterns
                    WHERE game_type = ? AND level_number = ?
                      AND is_active = 1
                      AND generations_since_update < ?
                    GROUP BY fatal_action
                """, (game_type, level_number, generations_since_threshold))
            
            if not patterns:
                return weights  # No data = all safe
            
            # Calculate graduated danger for each action
            for p in patterns:
                action = p['fatal_action']
                if not action or action < 1 or action > 7:
                    continue
                    
                deaths = p['death_count'] or 0
                survivals = p['survival_count'] or 0
                gens_since = p['generations_since_update'] or 0
                
                total = deaths + survivals
                if total == 0:
                    continue  # No data for this action
                
                # ============================================================
                # GRADUATED DANGER CALCULATION
                # ============================================================
                
                # 1. Base danger: death ratio
                base_danger = deaths / (total + 1)
                
                # 2. Time decay: old patterns matter less
                # Halves every 10 generations without new data
                time_decay = 0.5 ** (gens_since / 10.0)
                
                # 3. Survival boost: survivals reduce danger significantly
                # Each survival reduces effective danger by 20%
                survival_dampening = 1.0 / (1.0 + survivals * 0.2)
                
                # 4. Sample confidence: low samples = lower confidence in danger
                # Need at least 10 samples to be confident
                sample_confidence = min(1.0, total / 10.0)
                
                # Combined danger score
                danger = base_danger * time_decay * survival_dampening * sample_confidence
                
                # 5. Frontier mode: heavily reduce danger signals to encourage exploration
                if frontier_mode:
                    danger = danger * 0.3  # 70% reduction in danger on frontier
                
                # Convert danger to safety weight
                # Minimum safety = 0.05 (action is ALWAYS possible, just weighted low)
                safety_weight = max(0.05, 1.0 - danger)
                
                # Keep the LOWEST weight for each action (most dangerous pattern wins)
                if safety_weight < weights.get(action, 1.0):
                    weights[action] = safety_weight
                    
            return weights
            
        except Exception as e:
            logger.debug(f"Error calculating graduated weights: {e}")
            return weights  # Return default safe weights on error
    
    def record_survival_feedback(
        self,
        game_type: str,
        level_number: int,
        position: Tuple[int, int],
        action: int,
        bucket_size: int = 8
    ) -> bool:
        """
        Record that an action SURVIVED at this position.
        
        This is the FEEDBACK mechanism - when an action doesn't kill,
        we strengthen the survival signal which dampens the danger.
        
        Called after each successful (non-death) action.
        
        Returns True if updated an existing pattern, False if no pattern existed.
        """
        try:
            if not position or len(position) < 2:
                return False
                
            x, y = position
            bucket_x = x // bucket_size
            bucket_y = y // bucket_size
            
            # Update survival count for this action at this position
            # Note: SQLite uses CAST(x AS REAL), not PostgreSQL-style ::REAL
            result = self.db.execute_query("""
                UPDATE position_death_patterns
                SET survival_count = survival_count + 1,
                    danger_score = CAST(death_count AS REAL) / (death_count + survival_count + 2),
                    generations_since_update = 0
                WHERE game_type = ? AND level_number = ?
                  AND bucket_x = ? AND bucket_y = ? AND fatal_action = ?
                  AND is_active = 1
            """, (game_type, level_number, bucket_x, bucket_y, action))
            
            # Check if any rows were updated
            # Note: execute_query may not return affected rows, so we just return True
            return True
            
        except Exception as e:
            logger.debug(f"Error recording survival feedback: {e}")
            return False
    
    def get_position_death_summary(
        self,
        game_type: str,
        level_number: int,
        min_deaths: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get summary of position-based death patterns for a level.
        Useful for debugging and understanding where deaths cluster.
        """
        try:
            patterns = self.db.execute_query("""
                SELECT bucket_x, bucket_y, bucket_size, fatal_action,
                       death_count, survival_count, danger_score
                FROM position_death_patterns
                WHERE game_type = ? AND level_number = ?
                  AND death_count >= ?
                  AND is_active = 1
                ORDER BY death_count DESC, danger_score DESC
            """, (game_type, level_number, min_deaths))
            
            return [dict(p) for p in (patterns or [])]
            
        except Exception:
            return []