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
import numpy as np
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
                    game_id TEXT NOT NULL,          -- Original game_id (for reference)
                    game_type TEXT NOT NULL,        -- Game type for cross-session matching (e.g. 'sp80')
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
            
            # Index for fast lookups - use game_type for cross-session matching
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_terminal_patterns_lookup_v2
                ON terminal_patterns (game_type, level_number, frame_hash, is_active)
            """)
            
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
            
            # Extract game_type from game_id (e.g., 'sp80' from 'sp80-abc123')
            game_type = game_id.split('-')[0] if '-' in game_id else game_id
            
            # Check if this exact pattern already exists (match by game_type for cross-session learning)
            existing = self.db.execute_query("""
                SELECT pattern_id, occurrence_count, confirmed_lethal
                FROM terminal_patterns
                WHERE game_type = ? AND level_number = ? 
                  AND frame_hash = ? AND fatal_action = ?
                  AND is_active = 1
            """, (game_type, level_number, frame_hash, fatal_action))
            
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
            
            # Create new pattern - use game_type in pattern_id for consistency
            pattern_id = f"term_{game_type}_{level_number}_{hashlib.md5(f'{frame_hash}{fatal_action}'.encode()).hexdigest()[:8]}"
            
            self.db.execute_query("""
                INSERT INTO terminal_patterns (
                    pattern_id, game_id, game_type, level_number,
                    frame_hash, pre_death_actions, fatal_action,
                    occurrence_count, confirmed_lethal,
                    discovery_generation, discovered_by_agent,
                    last_occurrence_generation, confidence, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1, ?, ?, ?, 0.7, 1)
            """, (
                pattern_id, game_id, game_type, level_number,
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
            
            # Extract game_type from game_id for cross-session pattern matching
            game_type = game_id.split('-')[0] if '-' in game_id else game_id
            
            # Check for matching terminal patterns (by game_type, not game_id)
            # This allows patterns learned in one session to protect all future sessions
            patterns = self.db.execute_query("""
                SELECT 
                    pattern_id, frame_hash, pre_death_actions, fatal_action,
                    occurrence_count, confirmed_lethal, confidence
                FROM terminal_patterns
                WHERE game_type = ? AND level_number = ?
                  AND (frame_hash = ? OR frame_hash = ?)
                  AND fatal_action = ?
                  AND confidence >= ?
                  AND is_active = 1
                ORDER BY confidence DESC, confirmed_lethal DESC
                LIMIT 5
            """, (game_type, level_number, frame_hash, fuzzy_hash, 
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
                            'zone_coords': f"({zone['x_min']},{zone['y_min']})-({zone['x_max']},{zone['y_max']})",
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
    
    def should_challenge_zone(self, zone: Dict, generation: int) -> bool:
        """
        Determine if a death zone should be challenged/tested.
        
        Death zones might be temporary (enemy moved) or wrong (false positive).
        Agents should occasionally test old zones to see if they're still dangerous.
        
        Challenge criteria:
        1. Zone has high survival count relative to deaths (might be stale)
        2. Zone hasn't been validated recently (many generations since last death)
        3. Random exploration chance for high-performing agents
        
        Args:
            zone: Death zone dict with death_count, survival_count, etc.
            generation: Current generation number
            
        Returns:
            True if zone should be tested, False to avoid
        """
        death_count = zone.get('death_count', 1)
        survival_count = zone.get('survival_count', 0)
        danger_score = zone.get('danger_score', 0.7)
        
        # If survival count is high, zone might be stale
        if survival_count > death_count * 2 and danger_score < 0.5:
            return True
        
        # If danger score has decayed significantly, worth testing
        if danger_score < 0.4:
            return True
        
        # Occasionally challenge even "dangerous" zones (10% for low danger, 2% for high)
        import random
        challenge_chance = 0.02 if danger_score > 0.6 else 0.10
        if random.random() < challenge_chance:
            return True
        
        return False
    
    def record_zone_challenge(self, zone_id: str, survived: bool, generation: int):
        """
        Record the result of deliberately challenging a death zone.
        
        Args:
            zone_id: Zone that was tested
            survived: True if agent survived the zone, False if died
            generation: Current generation
        """
        try:
            now = datetime.now().isoformat()
            
            if survived:
                # Zone is less dangerous than believed
                self.db.execute_query("""
                    UPDATE death_zones
                    SET survival_count = survival_count + 1,
                        challenge_count = challenge_count + 1,
                        last_challenged_at = ?,
                        danger_score = CAST(death_count AS REAL) / 
                                       CAST(death_count + survival_count + 1 AS REAL)
                    WHERE zone_id = ?
                """, (now, zone_id))
                logger.info(f"[CHALLENGE] Zone {zone_id[:12]} survived! Danger score reduced.")
            else:
                # Zone confirmed dangerous
                self.db.execute_query("""
                    UPDATE death_zones
                    SET death_count = death_count + 1,
                        challenge_count = challenge_count + 1,
                        last_challenged_at = ?,
                        last_validated_at = ?,
                        generations_since_death = 0,
                        danger_score = MIN(0.95, danger_score + 0.1)
                    WHERE zone_id = ?
                """, (now, now, zone_id))
                logger.info(f"[CHALLENGE] Zone {zone_id[:12]} still lethal! Danger confirmed.")
        except Exception as e:
            logger.debug(f"Error recording zone challenge: {e}")
    
    def decay_old_zones(self, generations_threshold: int = 10):
        """
        Decay danger scores for zones that haven't killed anyone recently.
        
        If a zone hasn't caused a death in N generations, it might have
        been a temporary danger (moving enemy) or the game changed.
        
        Call this once per generation during evolution.
        """
        try:
            # Increment generations_since_death for all zones
            self.db.execute_query("""
                UPDATE death_zones
                SET generations_since_death = generations_since_death + 1
                WHERE is_active = 1
            """)
            
            # Decay danger score for old zones
            self.db.execute_query("""
                UPDATE death_zones
                SET danger_score = MAX(0.2, danger_score - 0.05)
                WHERE generations_since_death >= ?
                  AND is_active = 1
                  AND danger_score > 0.2
            """, (generations_threshold,))
            
            # Deactivate zones that have very low danger scores
            deactivated = self.db.execute_query("""
                UPDATE death_zones
                SET is_active = 0
                WHERE danger_score < 0.2
                  AND survival_count > death_count * 3
                  AND is_active = 1
                RETURNING zone_id
            """)
            
            if deactivated:
                logger.info(f"[DECAY] Deactivated {len(deactivated)} stale death zones")
                
        except Exception as e:
            logger.debug(f"Error decaying zones: {e}")

    # ========================================================================
    # DANGEROUS OBJECT DETECTION - Pattern-based danger awareness
    # ========================================================================
    
    def record_dangerous_object(self,
                                 game_type: str,
                                 level_number: int,
                                 frame_before_death: List[List[int]],
                                 controlled_objects: List[Dict],
                                 fatal_action: int) -> Optional[str]:
        """
        Identify and record the OBJECT (by color/pattern) that killed the agent.
        
        If blue dot touched red enemy and died, record "red = dangerous".
        Then find ALL red objects on the grid and mark them as suspected dangers.
        
        Args:
            game_type: Game type
            level_number: Level where death occurred
            frame_before_death: Frame state before death
            controlled_objects: Player's objects (to identify player color)
            fatal_action: Action that caused death
            
        Returns:
            object_id if recorded
        """
        try:
            if not frame_before_death or not controlled_objects:
                return None
            
            # Get player position and color
            player_positions = []
            player_color = None
            for obj in controlled_objects:
                if 'x' in obj and 'y' in obj:
                    player_positions.append((obj['x'], obj['y']))
                if 'color' in obj and player_color is None:
                    player_color = obj['color']
            
            if not player_positions:
                return None
            
            # Find what the player was ADJACENT to when they died
            # These are the candidate "killers"
            height = len(frame_before_death)
            width = len(frame_before_death[0]) if frame_before_death else 0
            
            adjacent_colors = set()
            for px, py in player_positions:
                # Check all 8 neighbors
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = px + dx, py + dy
                        if 0 <= nx < width and 0 <= ny < height:
                            neighbor_color = frame_before_death[ny][nx]
                            if neighbor_color != 0 and neighbor_color != player_color:
                                adjacent_colors.add(neighbor_color)
            
            if not adjacent_colors:
                return None
            
            now = datetime.now().isoformat()
            recorded_ids = []
            
            for danger_color in adjacent_colors:
                object_id = f"dobj_{game_type}_{level_number}_{danger_color}"
                
                # Check if already known
                existing = self.db.execute_query("""
                    SELECT object_id, kill_count FROM dangerous_objects
                    WHERE game_type = ? AND level_number = ? AND object_color = ?
                """, (game_type, level_number, danger_color))
                
                if existing:
                    # Increment kill count
                    self.db.execute_query("""
                        UPDATE dangerous_objects
                        SET kill_count = kill_count + 1,
                            danger_score = MIN(0.95, danger_score + 0.05),
                            last_kill_at = ?
                        WHERE object_id = ?
                    """, (now, existing[0]['object_id']))
                    recorded_ids.append(existing[0]['object_id'])
                else:
                    # Count how many of this color exist on the grid
                    color_count = sum(1 for row in frame_before_death 
                                     for c in row if c == danger_color)
                    
                    self.db.execute_query("""
                        INSERT INTO dangerous_objects (
                            object_id, game_type, level_number,
                            object_color, object_size, fatal_action, player_color,
                            kill_count, danger_score, discovered_at, last_kill_at, is_active
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, 0.8, ?, ?, 1)
                    """, (
                        object_id, game_type, level_number,
                        danger_color, color_count, fatal_action, player_color,
                        now, now
                    ))
                    recorded_ids.append(object_id)
                    
                    logger.info(f"[DANGER-OBJ] Color {danger_color} marked dangerous "
                               f"({color_count} instances on grid)")
            
            # Now propagate: Find all locations of dangerous colors and create suspected zones
            self._propagate_danger_to_similar_objects(
                game_type, level_number, frame_before_death, adjacent_colors
            )
            
            return recorded_ids[0] if recorded_ids else None
            
        except Exception as e:
            logger.debug(f"Error recording dangerous object: {e}")
            return None
    
    def _propagate_danger_to_similar_objects(self,
                                              game_type: str,
                                              level_number: int,
                                              frame: List[List[int]],
                                              danger_colors: set):
        """
        Find all instances of dangerous colors and create suspected death zones.
        
        If red killed us at (15,23), mark ALL red objects as suspected dangers.
        These are "soft" zones that can be quickly invalidated if proven safe.
        """
        try:
            height = len(frame)
            width = len(frame[0]) if frame else 0
            
            # Find all positions of dangerous colors
            danger_positions = []
            for y, row in enumerate(frame):
                for x, color in enumerate(row):
                    if color in danger_colors:
                        danger_positions.append((x, y, color))
            
            if not danger_positions:
                return
            
            now = datetime.now().isoformat()
            suspected_count = 0
            
            # Group nearby positions into zones (cluster detection)
            # Simple approach: create zones around each dangerous object
            for x, y, color in danger_positions:
                # Create a small zone around each dangerous object
                zone_id = f"susp_{game_type}_{level_number}_{x}_{y}"
                
                # Check if zone already exists
                existing = self.db.execute_query("""
                    SELECT zone_id FROM death_zones
                    WHERE game_type = ? AND level_number = ?
                      AND x_min <= ? AND x_max >= ? AND y_min <= ? AND y_max >= ?
                """, (game_type, level_number, x, x, y, y))
                
                if not existing:
                    # Create a suspected zone with lower initial danger score
                    # Expand by 1 in each direction to account for contact
                    x_min = max(0, x - 1)
                    x_max = min(width - 1, x + 1)
                    y_min = max(0, y - 1)
                    y_max = min(height - 1, y + 1)
                    
                    self.db.execute_query("""
                        INSERT OR IGNORE INTO death_zones (
                            zone_id, game_type, level_number,
                            x_min, x_max, y_min, y_max,
                            death_colors, death_count, survival_count, danger_score,
                            discovered_at, last_death_at, is_active
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0.5, ?, ?, 1)
                    """, (
                        zone_id, game_type, level_number,
                        x_min, x_max, y_min, y_max,
                        json.dumps([color]),
                        now, now
                    ))
                    suspected_count += 1
            
            if suspected_count > 0:
                logger.info(f"[PROPAGATE] Created {suspected_count} suspected death zones "
                           f"from dangerous color pattern")
                
                # Update the dangerous_objects record with propagation count
                for color in danger_colors:
                    self.db.execute_query("""
                        UPDATE dangerous_objects
                        SET suspected_instances = ?
                        WHERE game_type = ? AND level_number = ? AND object_color = ?
                    """, (suspected_count, game_type, level_number, color))
                    
        except Exception as e:
            logger.debug(f"Error propagating danger: {e}")
    
    def check_dangerous_objects(self,
                                 game_type: str,
                                 level_number: int,
                                 current_frame: List[List[int]],
                                 object_positions: List[Tuple[int, int]],
                                 planned_action: int) -> Optional[Dict[str, Any]]:
        """
        Check if planned action would bring player into contact with dangerous objects.
        
        This checks by COLOR, not just position - so if any red object is on the
        path, it triggers a warning.
        """
        try:
            if not object_positions or not current_frame:
                return None
            
            # Get known dangerous colors for this level
            dangers = self.db.execute_query("""
                SELECT object_color, danger_score, kill_count
                FROM dangerous_objects
                WHERE game_type = ? AND level_number = ?
                  AND danger_score >= 0.5 AND is_active = 1
            """, (game_type, level_number))
            
            if not dangers:
                return None
            
            danger_colors = {d['object_color']: d for d in dangers}
            
            height = len(current_frame)
            width = len(current_frame[0]) if current_frame else 0
            
            # Direction offsets
            direction_offset = {
                1: (0, -1),   # UP
                2: (0, 1),    # DOWN
                3: (1, 0),    # RIGHT
                4: (-1, 0)    # LEFT
            }
            
            for x, y in object_positions:
                # Check where we'd move to
                if planned_action in direction_offset:
                    dx, dy = direction_offset[planned_action]
                    next_x, next_y = x + dx, y + dy
                    
                    if 0 <= next_x < width and 0 <= next_y < height:
                        next_color = current_frame[next_y][next_x]
                        
                        if next_color in danger_colors:
                            danger_info = danger_colors[next_color]
                            # Find a safe direction
                            safe_dir = self._find_safe_direction_from_color(
                                x, y, current_frame, danger_colors.keys(), planned_action
                            )
                            
                            return {
                                'warning': True,
                                'danger_type': 'dangerous_object',
                                'object_color': next_color,
                                'danger_score': danger_info['danger_score'],
                                'kill_count': danger_info['kill_count'],
                                'next_position': (next_x, next_y),
                                'safe_direction': safe_dir,
                                'reason': f"Color {next_color} has killed {danger_info['kill_count']} times"
                            }
            
            return None
            
        except Exception as e:
            logger.debug(f"Error checking dangerous objects: {e}")
            return None
    
    def _find_safe_direction_from_color(self, x: int, y: int,
                                         frame: List[List[int]],
                                         danger_colors: set,
                                         avoid_direction: int) -> int:
        """Find a direction that doesn't lead to a dangerous color."""
        height = len(frame)
        width = len(frame[0]) if frame else 0
        
        direction_offset = {
            1: (0, -1),   # UP
            2: (0, 1),    # DOWN
            3: (1, 0),    # RIGHT
            4: (-1, 0)    # LEFT
        }
        
        safe_directions = []
        for direction, (dx, dy) in direction_offset.items():
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                if frame[ny][nx] not in danger_colors:
                    safe_directions.append(direction)
        
        # Prefer opposite of avoid_direction
        opposite = {1: 2, 2: 1, 3: 4, 4: 3}
        if opposite.get(avoid_direction) in safe_directions:
            return opposite[avoid_direction]
        
        if safe_directions:
            return safe_directions[0]
        
        return 7  # ACTION7 = UNDO as last resort
    
    def record_action_triggered_danger(self,
                                        game_type: str,
                                        level_number: int,
                                        trigger_action: int,
                                        frame_before: List[List[int]],
                                        frame_after: List[List[int]],
                                        actions_until_death: int,
                                        click_coords: Optional[Tuple[int, int]] = None):
        """
        Record when an action CREATES a dangerous situation.
        
        Compares frames before/after action to detect spawned objects,
        then records the action as potentially dangerous.
        """
        try:
            if not frame_before or not frame_after:
                return None
            
            # Find what NEW things appeared after the action
            spawned_positions = []
            spawned_colors = set()
            
            height = min(len(frame_before), len(frame_after))
            width = min(len(frame_before[0]), len(frame_after[0])) if frame_before and frame_after else 0
            
            for y in range(height):
                for x in range(width):
                    before = frame_before[y][x]
                    after = frame_after[y][x]
                    
                    # New non-background object appeared
                    if before == 0 and after != 0:
                        spawned_positions.append((x, y))
                        spawned_colors.add(after)
                    # Object changed to something new
                    elif before != after and after != 0:
                        spawned_positions.append((x, y))
                        spawned_colors.add(after)
            
            if not spawned_positions:
                return None
            
            now = datetime.now().isoformat()
            trigger_id = f"atd_{game_type}_{level_number}_{trigger_action}_{hashlib.md5(str(spawned_positions[:5]).encode()).hexdigest()[:8]}"
            
            # Check if this trigger pattern already known
            existing = self.db.execute_query("""
                SELECT trigger_id, occurrence_count FROM action_triggered_dangers
                WHERE game_type = ? AND level_number = ? AND trigger_action = ?
            """, (game_type, level_number, trigger_action))
            
            if existing:
                self.db.execute_query("""
                    UPDATE action_triggered_dangers
                    SET occurrence_count = occurrence_count + 1,
                        danger_score = MIN(0.95, danger_score + 0.05)
                    WHERE trigger_id = ?
                """, (existing[0]['trigger_id'],))
                
                logger.info(f"[ACTION-DANGER] ACTION{trigger_action} confirmed dangerous "
                           f"(spawned threats {existing[0]['occurrence_count'] + 1} times)")
                return existing[0]['trigger_id']
            
            # Record new trigger
            self.db.execute_query("""
                INSERT INTO action_triggered_dangers (
                    trigger_id, game_type, level_number,
                    trigger_action, trigger_x, trigger_y,
                    spawned_color, spawned_positions,
                    actions_until_death, occurrence_count, danger_score,
                    discovered_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0.7, ?, 1)
            """, (
                trigger_id, game_type, level_number,
                trigger_action, 
                click_coords[0] if click_coords else None,
                click_coords[1] if click_coords else None,
                list(spawned_colors)[0] if spawned_colors else None,
                json.dumps(spawned_positions[:20]),
                actions_until_death,
                now
            ))
            
            logger.info(f"[ACTION-DANGER] ACTION{trigger_action} spawned {len(spawned_positions)} new objects "
                       f"({actions_until_death} actions before death)")
            
            return trigger_id
            
        except Exception as e:
            logger.debug(f"Error recording action-triggered danger: {e}")
            return None

    # ========================================================================
    # GAME-OVER THEORY SYSTEM - Why did the game end?
    # ========================================================================
    
    def generate_game_over_theory(self, 
                                   game_id: str,
                                   level_number: int,
                                   frame_before_death: List[List[int]],
                                   fatal_action: int,
                                   pre_death_actions: List[int],
                                   controlled_objects: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Generate a THEORY about why the game ended in game-over.
        
        This creates human-readable hypotheses that agents can learn from
        and actively test/avoid in future games.
        
        Args:
            game_id: Game where death occurred
            level_number: Level where death occurred
            frame_before_death: Frame state before fatal action
            fatal_action: The action that caused game_over
            pre_death_actions: Last N actions before death
            controlled_objects: Objects the agent was controlling
            
        Returns:
            Dict with:
                - theory: Human-readable explanation
                - hypothesis_type: Category (boundary, collision, trap, etc.)
                - avoidance_strategy: What to do differently
                - confidence: How sure we are about this theory
                - testable_prediction: How to test if theory is correct
        """
        theory = {
            'theory': 'Unknown cause of game-over',
            'hypothesis_type': 'unknown',
            'avoidance_strategy': 'Avoid the fatal action in this state',
            'confidence': 0.3,
            'testable_prediction': None,
            'fatal_action': fatal_action,
            'pre_death_sequence': pre_death_actions[-5:] if pre_death_actions else []
        }
        
        try:
            game_type = game_id.split('-')[0] if '-' in game_id else game_id
            
            # Analyze frame for boundary/edge death
            height = len(frame_before_death) if frame_before_death else 0
            width = len(frame_before_death[0]) if frame_before_death and frame_before_death[0] else 0
            
            # Check if controlled objects are near edges (boundary death theory)
            if controlled_objects and height > 0 and width > 0:
                for obj in controlled_objects:
                    x, y = obj.get('x', -1), obj.get('y', -1)
                    near_edge = (x <= 1 or x >= width - 2 or y <= 1 or y >= height - 2)
                    
                    if near_edge:
                        action_meaning = {1: 'UP (toward edge)', 2: 'DOWN (toward edge)', 
                                         3: 'RIGHT (toward edge)', 4: 'LEFT (toward edge)',
                                         5: 'WAIT', 6: 'CLICK', 7: 'UNDO'}
                        theory['theory'] = f"[{game_type.upper()} L{level_number}] Boundary collision at ({x},{y}). ACTION{fatal_action} ({action_meaning.get(fatal_action, '?')}) pushed object out of bounds."
                        theory['hypothesis_type'] = 'boundary_collision'
                        theory['avoidance_strategy'] = f"In {game_type} L{level_number}, when near ({x},{y}), avoid ACTION{fatal_action}. Try opposite direction."
                        theory['confidence'] = 0.7
                        theory['testable_prediction'] = f"In {game_type} L{level_number}, ACTION{fatal_action} near ({x},{y}) should cause game-over."
                        return theory
            
            # Check for oscillation death (same actions repeated before death)
            if len(pre_death_actions) >= 4:
                # Check for A-B-A-B pattern
                last_four = pre_death_actions[-4:]
                if len(set(last_four)) == 2 and last_four[0] == last_four[2] and last_four[1] == last_four[3]:
                    # Include position context for oscillation
                    pos_str = ""
                    if controlled_objects:
                        positions = [(obj.get('x', -1), obj.get('y', -1)) for obj in controlled_objects if obj.get('x', -1) >= 0]
                        if positions:
                            pos_str = f" at {positions[0]}" if len(positions) == 1 else f" near {positions[:2]}"
                    
                    theory['theory'] = f"[{game_type.upper()} L{level_number}] Oscillation death{pos_str}. ACTION{last_four[0]}<->ACTION{last_four[1]} pattern punished."
                    theory['hypothesis_type'] = 'oscillation_trap'
                    theory['avoidance_strategy'] = f"In {game_type} L{level_number}{pos_str}, break oscillation. After ACTION{last_four[0]}, try different action."
                    theory['confidence'] = 0.6
                    theory['testable_prediction'] = f"In {game_type} L{level_number}, avoid oscillating ACTION{last_four[0]}<->ACTION{last_four[1]} more than twice."
                    return theory
            
            # Check for similar past patterns
            existing_patterns = self.db.execute_query("""
                SELECT fatal_action, occurrence_count, pre_death_actions, confidence
                FROM terminal_patterns
                WHERE game_id LIKE ? AND level_number = ? AND is_active = 1
                ORDER BY occurrence_count DESC
                LIMIT 5
            """, (f"{game_type}%", level_number))
            
            if existing_patterns:
                most_common = existing_patterns[0]
                if most_common['occurrence_count'] >= 3:
                    # Build position context for actionable theory
                    position_str = ""
                    if controlled_objects:
                        positions = [(obj.get('x', -1), obj.get('y', -1)) for obj in controlled_objects if obj.get('x', -1) >= 0]
                        if positions:
                            if len(positions) == 1:
                                position_str = f" from position ({positions[0][0]},{positions[0][1]})"
                            else:
                                position_str = f" with objects at {positions[:3]}"  # Show up to 3 positions
                    
                    theory['theory'] = f"[{game_type.upper()}] ACTION{most_common['fatal_action']}{position_str} has caused game-over {most_common['occurrence_count']} times at L{level_number}. This action is dangerous in this region."
                    theory['hypothesis_type'] = 'repeated_failure'
                    theory['avoidance_strategy'] = f"In {game_type} L{level_number}, avoid ACTION{most_common['fatal_action']}{position_str}. Try alternative actions or approach from different angle."
                    theory['confidence'] = min(0.9, 0.5 + most_common['occurrence_count'] * 0.1)
                    theory['testable_prediction'] = f"In {game_type} L{level_number}, ACTION{most_common['fatal_action']} from similar position should reproduce failure."
                    return theory
            
            # Check death zones
            zones = self.get_level_death_zones(game_type, level_number)
            if zones and controlled_objects:
                for obj in controlled_objects:
                    x, y = obj.get('x', -1), obj.get('y', -1)
                    for zone in zones:
                        if (zone['x_min'] <= x <= zone['x_max'] and 
                            zone['y_min'] <= y <= zone['y_max']):
                            theory['theory'] = f"[{game_type.upper()} L{level_number}] Death zone ({zone['x_min']}-{zone['x_max']}, {zone['y_min']}-{zone['y_max']}) at ({x},{y}). {zone['death_count']} recorded deaths here."
                            theory['hypothesis_type'] = 'death_zone'
                            theory['avoidance_strategy'] = f"In {game_type} L{level_number}, avoid region ({zone['x_min']}-{zone['x_max']}, {zone['y_min']}-{zone['y_max']})."
                            theory['confidence'] = zone.get('danger_score', 0.5)
                            theory['testable_prediction'] = f"In {game_type} L{level_number}, entering zone ({zone['x_min']}-{zone['x_max']}, {zone['y_min']}-{zone['y_max']}) causes game-over."
                            return theory
            
            # Default theory based on fatal action
            action_meanings = {
                1: 'up movement', 2: 'down movement', 
                3: 'right movement', 4: 'left movement',
                5: 'wait/special', 6: 'click/select', 7: 'undo'
            }
            
            # Build position context for actionable theory
            position_str = ""
            if controlled_objects:
                positions = [(obj.get('x', -1), obj.get('y', -1)) for obj in controlled_objects if obj.get('x', -1) >= 0]
                if positions:
                    if len(positions) == 1:
                        position_str = f" at position ({positions[0][0]},{positions[0][1]})"
                    else:
                        position_str = f" with objects at {positions[:3]}"
            
            theory['theory'] = f"[{game_type.upper()} L{level_number}] Game-over caused by ACTION{fatal_action} ({action_meanings.get(fatal_action, 'unknown')}){position_str}. Exact trigger unclear."
            theory['hypothesis_type'] = 'action_state_mismatch'
            theory['avoidance_strategy'] = f"In {game_type} L{level_number}{position_str}, avoid ACTION{fatal_action}. Try alternative actions."
            theory['confidence'] = 0.4
            theory['testable_prediction'] = f"In {game_type} L{level_number}, ACTION{fatal_action} from similar position should reproduce failure."
            
        except Exception as e:
            logger.debug(f"Theory generation failed: {e}")
            theory['error'] = str(e)[:100]
        
        return theory
    
    def get_game_over_theories(self, game_id: str, level_number: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get existing game-over theories for a game/level.
        
        Returns theories from past failures that agents can learn from.
        """
        try:
            game_type = game_id.split('-')[0] if '-' in game_id else game_id
            
            patterns = self.db.execute_query("""
                SELECT pattern_id, fatal_action, pre_death_actions, 
                       occurrence_count, confirmed_lethal, confidence
                FROM terminal_patterns
                WHERE game_id LIKE ? AND level_number = ? AND is_active = 1
                ORDER BY confirmed_lethal DESC, confidence DESC
                LIMIT ?
            """, (f"{game_type}%", level_number, limit))
            
            theories = []
            for pattern in (patterns or []):
                try:
                    pre_death = json.loads(pattern['pre_death_actions']) if pattern.get('pre_death_actions') else []
                except:
                    pre_death = []
                
                theories.append({
                    'pattern_id': pattern['pattern_id'],
                    'fatal_action': pattern['fatal_action'],
                    'confirmed_deaths': pattern['confirmed_lethal'],
                    'confidence': pattern['confidence'],
                    'pre_death_sequence': pre_death,
                    'theory': f"ACTION{pattern['fatal_action']} caused {pattern['confirmed_lethal']} deaths at level {level_number}",
                    'avoidance_strategy': f"Avoid ACTION{pattern['fatal_action']} in similar states"
                })
            
            return theories
            
        except Exception as e:
            logger.debug(f"Failed to get game-over theories: {e}")
            return []

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
        bucket_size: int = 8
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
            pattern = self.db.execute_query("""
                SELECT pattern_id, death_count, survival_count, danger_score, last_death_at
                FROM position_death_patterns
                WHERE game_type = ? AND level_number = ?
                  AND bucket_x = ? AND bucket_y = ? AND fatal_action = ?
                  AND danger_score >= ?
                  AND is_active = 1
                ORDER BY danger_score DESC
                LIMIT 1
            """, (game_type, level_number, bucket_x, bucket_y, planned_action, min_danger))
            
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