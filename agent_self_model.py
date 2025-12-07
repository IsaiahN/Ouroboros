#!/usr/bin/env python3
"""
Agent Self-Model System
=======================

Implements "I am this object" tracking for agents.
Identifies which objects/pixels agents control in each game/level.

This addresses the agent self-model requirement from operational philosophy.
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import json
import uuid
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from database_interface import DatabaseInterface
import logging

logger = logging.getLogger(__name__)


class AgentSelfModel:
    """
    Tracks which objects agents control in games.
    
    Builds a "self-model" for each agent by analyzing:
    - Which pixels/objects respond to agent actions
    - Correlation between actions and frame changes
    - Controlled vs environmental objects
    
    Network Knowledge Sharing:
    - Agents share "I am this object" discoveries to network_object_control_hypotheses
    - Other agents validate/refute these hypotheses during gameplay
    - Bayesian reputation scoring determines reliability
    """
    
    def __init__(self, db_path: str = "core_data.db"):
        """Initialize self-model system."""
        self.db = DatabaseInterface(db_path)
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Create agent_object_control and network hypothesis tables if needed."""
        # Individual agent control maps
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS agent_object_control (
                agent_id TEXT,
                game_id TEXT,
                level_number INTEGER,
                controlled_objects TEXT,
                confidence REAL,
                learned_at TEXT,
                PRIMARY KEY (agent_id, game_id, level_number)
            )
        """)
        
        # Network-level "I am this object" hypotheses - shared across agents
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS network_object_control_hypotheses (
                hypothesis_id TEXT PRIMARY KEY,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                
                -- The hypothesis: "I control object at these coordinates"
                control_pattern TEXT NOT NULL,
                action_response_map TEXT NOT NULL,
                
                -- Discovery context
                discovered_by_agent TEXT NOT NULL,
                discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                discovery_generation INTEGER DEFAULT 0,
                
                -- Validation tracking (Bayesian reputation)
                validation_attempts INTEGER DEFAULT 0,
                validation_successes INTEGER DEFAULT 0,
                validation_failures INTEGER DEFAULT 0,
                reliability_score REAL DEFAULT 0.5,
                
                -- Status
                is_active BOOLEAN DEFAULT TRUE,
                last_validated DATETIME,
                validated_by_win BOOLEAN DEFAULT FALSE
            )
        """)
        
        # Index for fast lookup by game type
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_object_hypotheses_game 
            ON network_object_control_hypotheses(game_type, level_number, is_active)
        """)
        
        # ACTION5 behavior mapping - what does ACTION5 do in each game type?
        # This is crucial because ACTION5 is context-dependent (rotate, toggle, interact, etc.)
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS action5_behavior_map (
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                behavior_type TEXT NOT NULL,
                affected_objects TEXT,
                effect_description TEXT,
                confidence REAL DEFAULT 0.5,
                discovery_count INTEGER DEFAULT 1,
                last_observed DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (game_type, level_number)
            )
        """)
        
        # ACTION6 pseudo button behavior - what do clicks at specific regions do?
        # ACTION6 uses x,y coordinates (0-63 range) like a touchscreen
        # Clicking pseudo buttons often produces movement similar to ACTION1-4
        # We divide screen into regions and track what clicking each region does
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS pseudo_button_behavior (
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                region_x INTEGER NOT NULL,
                region_y INTEGER NOT NULL,
                
                -- What does clicking this region do?
                produces_action TEXT,
                movement_direction TEXT,
                affected_objects TEXT,
                effect_description TEXT,
                
                -- Confidence tracking
                confidence REAL DEFAULT 0.5,
                discovery_count INTEGER DEFAULT 1,
                last_observed DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                PRIMARY KEY (game_type, level_number, region_x, region_y)
            )
        """)
        
        # Index for fast pseudo button lookup
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_pseudo_button_game 
            ON pseudo_button_behavior(game_type, level_number)
        """)
    
    def identify_controlled_objects(
        self, 
        game_id: str, 
        level: int, 
        action_sequence: List[Dict],
        frame_sequence: List[Dict]
    ) -> Tuple[List[str], float]:
        """
        Identify which objects respond to actions using action-movement correlation.
        
        FIXED (2025-12-06): Previous implementation tracked ALL changed coordinates,
        resulting in 600+ "controlled" objects (the entire screen). 
        
        New approach: Correlate action DIRECTION with object MOVEMENT direction.
        - ACTION1 (up) -> object moves up (y decreases)
        - ACTION2 (down) -> object moves down (y increases)
        - ACTION3 (left) -> object moves left (x decreases)
        - ACTION4 (right) -> object moves right (x increases)
        
        Only objects that consistently move in the action's direction are "controlled".
        
        Args:
            game_id: Game identifier
            level: Level number
            action_sequence: List of actions taken (with 'action_type' field)
            frame_sequence: List of frames (before/after each action, with 'grid' field)
        
        Returns:
            (controlled_objects, confidence) - controlled objects as list of "x:N,y:M" strings
        """
        if not action_sequence or not frame_sequence:
            return ([], 0.0)
        
        # Map action types to expected movement directions
        # ARC games: ACTION1=up, ACTION2=down, ACTION3=left, ACTION4=right
        # ACTION5 is CONTEXT-DEPENDENT (rotate, toggle, interact, etc.) - we learn what it does
        # ACTION6=click, ACTION7=submit are coordinate-based, handled separately
        ACTION_DIRECTION = {
            'ACTION1': (0, -1),  # up: y decreases
            'ACTION2': (0, 1),   # down: y increases  
            'ACTION3': (-1, 0),  # left: x decreases
            'ACTION4': (1, 0),   # right: x increases
            'action_1': (0, -1),
            'action_2': (0, 1),
            'action_3': (-1, 0),
            'action_4': (1, 0),
        }
        
        # ACTION5 variants - we don't know direction, but we track if it causes changes
        ACTION5_VARIANTS = {'ACTION5', 'action_5', 'ACTION 5'}
        
        # ACTION6 is coordinate-based clicking (0-63 range) - pseudo buttons
        ACTION6_VARIANTS = {'ACTION6', 'action_6', 'ACTION 6'}
        
        # Track object movement correlation: object_signature -> {correct_moves, total_moves}
        object_control_score = {}  # {object_id: {'correct': int, 'total': int, 'positions': [(x,y)]}}
        
        # Track ACTION5 effects separately (non-directional but may indicate control)
        action5_effects = {}  # {object_id: {'changes': int, 'total': int}}
        
        # Track ACTION6 (pseudo button) effects by screen region
        # Divides 64x64 screen into 8x8 regions (8 pixels each)
        action6_region_effects = {}  # {(region_x, region_y): {'direction': counts, 'objects': set}}
        
        for i, action in enumerate(action_sequence):
            if i >= len(frame_sequence) - 1:
                break
            
            frame_before = frame_sequence[i]
            frame_after = frame_sequence[i + 1]
            
            action_type = action.get('action_type', '')
            
            # Handle ACTION5 specially - it's context-dependent per game type
            if action_type in ACTION5_VARIANTS:
                self._track_action5_effects(
                    frame_before, frame_after, action5_effects, game_id, level
                )
                continue
            
            # Handle ACTION6 (pseudo button clicks) - coordinate-based
            if action_type in ACTION6_VARIANTS:
                click_x = action.get('x', action.get('click_x', 0))
                click_y = action.get('y', action.get('click_y', 0))
                self._track_action6_effects(
                    frame_before, frame_after, action6_region_effects,
                    click_x, click_y, game_id, level
                )
                continue
            
            # Get action direction (skip click/submit which are coordinate-based)
            expected_direction = ACTION_DIRECTION.get(action_type)
            if not expected_direction:
                continue  # Skip ACTION6=click, ACTION7=submit (coordinate-based)
            
            dx_expected, dy_expected = expected_direction
            
            # Find objects that MOVED in the expected direction
            grid_before = frame_before.get('grid', [])
            grid_after = frame_after.get('grid', [])
            
            if not grid_before or not grid_after:
                continue
            
            # Find objects in before and after frames (non-zero, non-background cells)
            objects_before = self._find_objects_in_grid(grid_before)
            objects_after = self._find_objects_in_grid(grid_after)
            
            # Match objects and check movement direction
            for obj_id, positions_before in objects_before.items():
                if obj_id not in objects_after:
                    continue  # Object disappeared
                
                positions_after = objects_after[obj_id]
                
                # Calculate centroid movement
                cx_before = sum(p[0] for p in positions_before) / len(positions_before)
                cy_before = sum(p[1] for p in positions_before) / len(positions_before)
                cx_after = sum(p[0] for p in positions_after) / len(positions_after)
                cy_after = sum(p[1] for p in positions_after) / len(positions_after)
                
                dx_actual = cx_after - cx_before
                dy_actual = cy_after - cy_before
                
                # Did object move at all?
                if abs(dx_actual) < 0.5 and abs(dy_actual) < 0.5:
                    continue  # Object didn't move
                
                # Initialize tracking for this object
                if obj_id not in object_control_score:
                    object_control_score[obj_id] = {'correct': 0, 'total': 0, 'positions': []}
                
                object_control_score[obj_id]['total'] += 1
                object_control_score[obj_id]['positions'] = list(positions_after)[:5]  # Store sample positions
                
                # Check if movement matches expected direction
                movement_matches = False
                if dx_expected != 0:  # Horizontal action
                    movement_matches = (dx_expected > 0 and dx_actual > 0.5) or (dx_expected < 0 and dx_actual < -0.5)
                if dy_expected != 0:  # Vertical action
                    movement_matches = (dy_expected > 0 and dy_actual > 0.5) or (dy_expected < 0 and dy_actual < -0.5)
                
                if movement_matches:
                    object_control_score[obj_id]['correct'] += 1
        
        # Identify controlled objects: >60% correct movement correlation with at least 2 samples
        controlled = []
        best_score = 0.0
        
        for obj_id, scores in object_control_score.items():
            if scores['total'] < 2:
                continue  # Not enough samples
            
            correlation = scores['correct'] / scores['total']
            if correlation >= 0.6:  # 60% threshold for "controlled"
                # Store representative position(s) of this object
                for pos in scores['positions'][:3]:  # Max 3 positions per controlled object
                    controlled.append(f"x:{pos[0]},y:{pos[1]}")
                best_score = max(best_score, correlation)
        
        # Also check ACTION5 effects - objects that consistently change on ACTION5
        # may be "controlled" even if not directionally
        for obj_id, effects in action5_effects.items():
            if effects['total'] < 2:
                continue
            
            change_rate = effects['changes'] / effects['total']
            if change_rate >= 0.7:  # 70% threshold for ACTION5 control (higher since non-directional)
                # This object responds to ACTION5 - mark as controlled
                if obj_id not in object_control_score:
                    # Get positions from the effects tracking
                    for pos in effects.get('positions', [])[:3]:
                        controlled.append(f"x:{pos[0]},y:{pos[1]}")
                    best_score = max(best_score, change_rate)
                    logger.debug(f"[SELF-MODEL] ACTION5 controls object {obj_id} (change rate: {change_rate:.2f})")
        
        # Confidence is the best correlation score, or 0 if nothing found
        confidence = best_score if controlled else 0.0
        
        # Limit to max 50 controlled coordinates (prevent bloat)
        controlled = controlled[:50]
        
        return (controlled, confidence)
    
    def _track_action5_effects(
        self,
        frame_before: Dict,
        frame_after: Dict,
        action5_effects: Dict,
        game_id: str,
        level: int
    ) -> None:
        """
        Track what ACTION5 does in this game/level.
        
        ACTION5 is context-dependent: rotate, toggle, interact, select, etc.
        We learn empirically by tracking which objects change when ACTION5 is used.
        
        Args:
            frame_before: Frame before ACTION5
            frame_after: Frame after ACTION5
            action5_effects: Dict tracking {object_id: {changes, total, positions}}
            game_id: Current game (for logging)
            level: Current level
        """
        grid_before = frame_before.get('grid', [])
        grid_after = frame_after.get('grid', [])
        
        if not grid_before or not grid_after:
            return
        
        objects_before = self._find_objects_in_grid(grid_before)
        objects_after = self._find_objects_in_grid(grid_after)
        
        # Check each object for ANY change (position, size, color transformation)
        for obj_id, positions_before in objects_before.items():
            if obj_id not in action5_effects:
                action5_effects[obj_id] = {'changes': 0, 'total': 0, 'positions': []}
            
            action5_effects[obj_id]['total'] += 1
            
            if obj_id not in objects_after:
                # Object disappeared - that's a change!
                action5_effects[obj_id]['changes'] += 1
                action5_effects[obj_id]['positions'] = list(positions_before)[:5]
                continue
            
            positions_after = objects_after[obj_id]
            
            # Check for position change
            cx_before = sum(p[0] for p in positions_before) / len(positions_before)
            cy_before = sum(p[1] for p in positions_before) / len(positions_before)
            cx_after = sum(p[0] for p in positions_after) / len(positions_after)
            cy_after = sum(p[1] for p in positions_after) / len(positions_after)
            
            position_changed = abs(cx_after - cx_before) > 0.3 or abs(cy_after - cy_before) > 0.3
            
            # Check for size/shape change
            size_changed = abs(len(positions_after) - len(positions_before)) > 0
            
            # Check for rotation/transformation (positions differ but centroid same)
            positions_set_before = set(positions_before)
            positions_set_after = set(positions_after)
            shape_changed = positions_set_before != positions_set_after
            
            if position_changed or size_changed or shape_changed:
                action5_effects[obj_id]['changes'] += 1
                action5_effects[obj_id]['positions'] = list(positions_after)[:5]
        
        # Also check for NEW objects that appeared (ACTION5 might create things)
        for obj_id, positions_after in objects_after.items():
            if obj_id not in objects_before:
                if obj_id not in action5_effects:
                    action5_effects[obj_id] = {'changes': 0, 'total': 0, 'positions': []}
                action5_effects[obj_id]['changes'] += 1
                action5_effects[obj_id]['total'] += 1
                action5_effects[obj_id]['positions'] = list(positions_after)[:5]
    
    def _track_action6_effects(
        self,
        frame_before: Dict,
        frame_after: Dict,
        action6_region_effects: Dict,
        click_x: int,
        click_y: int,
        game_id: str,
        level: int
    ) -> None:
        """
        Track what ACTION6 (pseudo button clicks) do at specific screen regions.
        
        ACTION6 uses x,y coordinates (0-63 range) like a touchscreen.
        Clicking on pseudo buttons often produces movement effects similar to ACTION1-4.
        We divide the screen into 8x8 regions and track what clicking each region does.
        
        Args:
            frame_before: Frame before click
            frame_after: Frame after click
            action6_region_effects: Dict tracking effects by region
            click_x, click_y: Click coordinates (0-63)
            game_id: Current game
            level: Current level
        """
        grid_before = frame_before.get('grid', [])
        grid_after = frame_after.get('grid', [])
        
        if not grid_before or not grid_after:
            return
        
        # Convert click coords to region (divide into 8x8 grid of regions)
        # Each region is 8 pixels (64 / 8 = 8)
        region_x = min(click_x // 8, 7)  # 0-7
        region_y = min(click_y // 8, 7)  # 0-7
        region_key = (region_x, region_y)
        
        if region_key not in action6_region_effects:
            action6_region_effects[region_key] = {
                'up': 0, 'down': 0, 'left': 0, 'right': 0,
                'toggle': 0, 'no_effect': 0,
                'affected_objects': set(),
                'total': 0
            }
        
        action6_region_effects[region_key]['total'] += 1
        
        objects_before = self._find_objects_in_grid(grid_before)
        objects_after = self._find_objects_in_grid(grid_after)
        
        # Track what direction objects moved (if any)
        movement_detected = False
        for obj_id, positions_before in objects_before.items():
            if obj_id not in objects_after:
                # Object disappeared - that's a toggle/change
                action6_region_effects[region_key]['toggle'] += 1
                action6_region_effects[region_key]['affected_objects'].add(obj_id)
                movement_detected = True
                continue
            
            positions_after = objects_after[obj_id]
            
            # Calculate movement
            cx_before = sum(p[0] for p in positions_before) / len(positions_before)
            cy_before = sum(p[1] for p in positions_before) / len(positions_before)
            cx_after = sum(p[0] for p in positions_after) / len(positions_after)
            cy_after = sum(p[1] for p in positions_after) / len(positions_after)
            
            dx = cx_after - cx_before
            dy = cy_after - cy_before
            
            # Determine movement direction
            if abs(dy) > 0.5 and dy < 0:
                action6_region_effects[region_key]['up'] += 1
                action6_region_effects[region_key]['affected_objects'].add(obj_id)
                movement_detected = True
            elif abs(dy) > 0.5 and dy > 0:
                action6_region_effects[region_key]['down'] += 1
                action6_region_effects[region_key]['affected_objects'].add(obj_id)
                movement_detected = True
            elif abs(dx) > 0.5 and dx < 0:
                action6_region_effects[region_key]['left'] += 1
                action6_region_effects[region_key]['affected_objects'].add(obj_id)
                movement_detected = True
            elif abs(dx) > 0.5 and dx > 0:
                action6_region_effects[region_key]['right'] += 1
                action6_region_effects[region_key]['affected_objects'].add(obj_id)
                movement_detected = True
        
        # Check for new objects (button might spawn things)
        for obj_id in objects_after:
            if obj_id not in objects_before:
                action6_region_effects[region_key]['toggle'] += 1
                action6_region_effects[region_key]['affected_objects'].add(obj_id)
                movement_detected = True
        
        if not movement_detected:
            action6_region_effects[region_key]['no_effect'] += 1
    
    def _find_objects_in_grid(self, grid: List) -> Dict[int, List[Tuple[int, int]]]:
        """
        Find all distinct objects in a grid by color/value.
        
        Returns dict mapping object_id (color value) -> list of (x, y) positions.
        Ignores background (value 0) and very common values (>50% of grid = background).
        """
        objects = {}  # color -> [(x, y), ...]
        
        if not grid:
            return objects
        
        height = len(grid)
        width = len(grid[0]) if grid else 0
        total_cells = height * width
        
        for y, row in enumerate(grid):
            for x, cell in enumerate(row):
                if cell == 0:  # Skip background
                    continue
                if cell not in objects:
                    objects[cell] = []
                objects[cell].append((x, y))
        
        # Filter out "background" colors that cover >50% of non-zero cells
        filtered = {}
        for color, positions in objects.items():
            if len(positions) < total_cells * 0.5:  # Not background
                filtered[color] = positions
        
        return filtered
    
    def _find_changed_coordinates(
        self, 
        frame_before: Dict, 
        frame_after: Dict
    ) -> List[str]:
        """
        Find coordinates that changed between frames.
        
        Args:
            frame_before: Frame state before action
            frame_after: Frame state after action
        
        Returns:
            List of changed coordinate strings (e.g., "x:5,y:10")
        """
        changed = []
        
        # Simple pixel-level comparison
        # In real implementation, would compare grid states
        grid_before = frame_before.get('grid', [])
        grid_after = frame_after.get('grid', [])
        
        if not grid_before or not grid_after:
            return changed
        
        for y in range(min(len(grid_before), len(grid_after))):
            for x in range(min(len(grid_before[y]), len(grid_after[y]))):
                if grid_before[y][x] != grid_after[y][x]:
                    changed.append(f"x:{x},y:{y}")
        
        return changed
    
    def store_control_map(
        self,
        agent_id: str,
        game_id: str,
        level: int,
        controlled_objects: List[str],
        confidence: float
    ):
        """
        Store agent's control map in database.
        
        Args:
            agent_id: Agent identifier
            game_id: Game identifier
            level: Level number
            controlled_objects: List of controlled object coordinates
            confidence: Confidence score (0.0-1.0)
        """
        from datetime import datetime
        
        self.db.execute_query("""
            INSERT OR REPLACE INTO agent_object_control
            (agent_id, game_id, level_number, controlled_objects, confidence, learned_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            agent_id,
            game_id,
            level,
            json.dumps(controlled_objects),
            confidence,
            datetime.now().isoformat()
        ))
        
        logger.info(
            f"Stored control map for {agent_id} on {game_id} L{level}: "
            f"{len(controlled_objects)} objects (confidence: {confidence:.2f})"
        )
    
    def get_controlled_objects(
        self,
        agent_id: str,
        game_id: str,
        level: int
    ) -> Optional[List[str]]:
        """
        Retrieve agent's known controlled objects.
        
        Args:
            agent_id: Agent identifier
            game_id: Game identifier
            level: Level number
        
        Returns:
            List of controlled object coordinates, or None if not learned
        """
        result = self.db.execute_query("""
            SELECT controlled_objects, confidence
            FROM agent_object_control
            WHERE agent_id = ? AND game_id = ? AND level_number = ?
        """, (agent_id, game_id, level))
        
        if result and result[0]['controlled_objects']:
            return json.loads(result[0]['controlled_objects'])
        
        return None
    
    def build_control_map(
        self,
        agent_id: str,
        game_id: str,
        gameplay_data: Dict
    ) -> Dict[int, List[str]]:
        """
        Build complete control map for all levels in a game.
        
        Args:
            agent_id: Agent identifier
            game_id: Game identifier
            gameplay_data: Complete gameplay data with actions and frames
        
        Returns:
            Dictionary mapping level -> controlled objects
        """
        control_map = {}
        
        for level_data in gameplay_data.get('levels', []):
            level = level_data.get('level_number')
            actions = level_data.get('actions', [])
            frames = level_data.get('frames', [])
            
            if level is None or not actions or not frames:
                continue
            
            controlled, confidence = self.identify_controlled_objects(
                game_id, level, actions, frames
            )
            
            if controlled and confidence > 0.5:
                control_map[level] = controlled
                self.store_control_map(agent_id, game_id, level, controlled, confidence)
        
        return control_map
    
    # ========================================================================
    # NETWORK KNOWLEDGE SHARING: "I AM THIS OBJECT" HYPOTHESES
    # ========================================================================
    
    def share_control_discovery_to_network(
        self,
        agent_id: str,
        game_id: str,
        level: int,
        controlled_objects: List[str],
        action_response_map: Dict[str, List[str]],
        confidence: float,
        generation: int = 0
    ) -> Optional[str]:
        """
        Share "I am this object" discovery to network for other agents to validate.
        
        This is the core of network-level self-model learning:
        - Agent discovers which objects it controls
        - Shares hypothesis to network
        - Other agents validate during their gameplay
        - High-reliability patterns become network knowledge
        
        Args:
            agent_id: Discovering agent
            game_id: Game where discovery was made
            level: Level number
            controlled_objects: Coordinates of controlled objects
            action_response_map: Maps action types to responding coordinates
            confidence: Discovery confidence
            generation: Current evolution generation
        
        Returns:
            hypothesis_id if shared, None if already exists or low confidence
        """
        if confidence < 0.6 or not controlled_objects:
            return None
        
        # Extract game type (e.g., 'ft09' from 'ft09-abc123')
        game_type = game_id.split('-')[0] if '-' in game_id else game_id
        
        # Create control pattern signature for deduplication
        pattern_signature = self._create_pattern_signature(controlled_objects, action_response_map)
        
        # Check if similar hypothesis already exists
        existing = self.db.execute_query("""
            SELECT hypothesis_id, validation_attempts, reliability_score
            FROM network_object_control_hypotheses
            WHERE game_type = ? AND level_number = ? AND control_pattern = ? AND is_active = TRUE
        """, (game_type, level, pattern_signature))
        
        if existing:
            # Update existing with validation attempt
            return existing[0]['hypothesis_id']
        
        # Create new hypothesis
        hypothesis_id = f"oc_{game_type}_L{level}_{uuid.uuid4().hex[:8]}"
        
        self.db.execute_query("""
            INSERT INTO network_object_control_hypotheses
            (hypothesis_id, game_type, level_number, control_pattern, action_response_map,
             discovered_by_agent, discovery_generation, reliability_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            hypothesis_id,
            game_type,
            level,
            pattern_signature,
            json.dumps(action_response_map),
            agent_id,
            generation,
            confidence  # Initial reliability = discovery confidence
        ))
        
        logger.info(
            f"[NETWORK] Agent {agent_id[:8]} shared 'I am object' hypothesis: "
            f"{hypothesis_id} for {game_type} L{level} ({len(controlled_objects)} objects)"
        )
        
        return hypothesis_id
    
    def get_network_control_hypotheses(
        self,
        game_id: str,
        level: int,
        min_reliability: float = 0.3
    ) -> List[Dict]:
        """
        Get network-validated "I am this object" hypotheses for a game/level.
        
        Use this to bootstrap agent self-model with network knowledge.
        
        Args:
            game_id: Game identifier
            level: Level number
            min_reliability: Minimum reliability score to return
        
        Returns:
            List of hypothesis dictionaries with control patterns and reliability
        """
        game_type = game_id.split('-')[0] if '-' in game_id else game_id
        
        results = self.db.execute_query("""
            SELECT 
                hypothesis_id,
                control_pattern,
                action_response_map,
                reliability_score,
                validation_attempts,
                validation_successes,
                validated_by_win
            FROM network_object_control_hypotheses
            WHERE game_type = ? AND level_number = ? 
                  AND is_active = TRUE AND reliability_score >= ?
            ORDER BY reliability_score DESC, validated_by_win DESC
            LIMIT 5
        """, (game_type, level, min_reliability))
        
        hypotheses = []
        for row in results or []:
            hypotheses.append({
                'hypothesis_id': row['hypothesis_id'],
                'controlled_objects': json.loads(row['control_pattern']) if row['control_pattern'].startswith('[') else row['control_pattern'].split(','),
                'action_response_map': json.loads(row['action_response_map']) if row['action_response_map'] else {},
                'reliability': row['reliability_score'],
                'validation_count': row['validation_attempts'],
                'success_rate': row['validation_successes'] / max(1, row['validation_attempts']),
                'validated_by_win': row['validated_by_win']
            })
        
        return hypotheses
    
    def validate_control_hypothesis(
        self,
        hypothesis_id: str,
        success: bool,
        validated_by_win: bool = False
    ):
        """
        Record validation result for a network control hypothesis.
        
        Called when an agent uses a network hypothesis and succeeds/fails.
        Updates Bayesian reliability score.
        
        Args:
            hypothesis_id: Hypothesis being validated
            success: Whether the hypothesis helped (True) or failed (False)
            validated_by_win: Whether validation came from level/game win
        """
        # Get current stats
        current = self.db.execute_query("""
            SELECT validation_attempts, validation_successes, validation_failures, reliability_score
            FROM network_object_control_hypotheses
            WHERE hypothesis_id = ?
        """, (hypothesis_id,))
        
        if not current:
            return
        
        row = current[0]
        attempts = row['validation_attempts'] + 1
        successes = row['validation_successes'] + (1 if success else 0)
        failures = row['validation_failures'] + (0 if success else 1)
        
        # Bayesian reliability update with prior
        prior_successes = 1  # Weak prior
        prior_total = 2
        reliability = (successes + prior_successes) / (attempts + prior_total)
        
        # Mark validated_by_win if this validation was from a win
        win_flag = validated_by_win or row.get('validated_by_win', False)
        
        # Deactivate if reliability drops too low
        is_active = reliability >= 0.2
        
        self.db.execute_query("""
            UPDATE network_object_control_hypotheses
            SET validation_attempts = ?,
                validation_successes = ?,
                validation_failures = ?,
                reliability_score = ?,
                validated_by_win = ?,
                is_active = ?,
                last_validated = CURRENT_TIMESTAMP
            WHERE hypothesis_id = ?
        """, (attempts, successes, failures, reliability, win_flag, is_active, hypothesis_id))
        
        if not is_active:
            logger.info(f"[NETWORK] Control hypothesis {hypothesis_id} deactivated (reliability: {reliability:.2f})")
    
    def _create_pattern_signature(self, controlled_objects: List[str], action_map: Dict) -> str:
        """
        Create a signature for deduplication of similar patterns.
        
        Uses sorted coordinates to ensure consistent comparison.
        """
        sorted_objects = sorted(controlled_objects)
        return json.dumps(sorted_objects)
    
    # =========================================================================
    # ACTION5 BEHAVIOR MAPPING (Network-Level Knowledge)
    # =========================================================================
    
    def save_action5_behavior(
        self,
        game_type: str,
        level: int,
        behavior_type: str,
        affected_objects: List[str],
        effect_description: str,
        confidence: float
    ) -> None:
        """
        Save discovered ACTION5 behavior to network-level knowledge.
        
        This allows all agents to benefit from one agent's discovery
        of what ACTION5 does in a particular game type.
        
        Args:
            game_type: The game type (e.g., "tetris_variant")
            level: Level number where behavior was observed
            behavior_type: Type of behavior (rotation, toggle, interact, select, etc.)
            affected_objects: List of object color IDs affected
            effect_description: Human-readable description of the effect
            confidence: Confidence level (0.0 to 1.0)
        """
        existing = self.db.execute_query("""
            SELECT confidence, discovery_count FROM action5_behavior_map
            WHERE game_type = ? AND level_number = ?
        """, (game_type, level))
        
        affected_str = ",".join(str(o) for o in affected_objects) if affected_objects else ""
        
        if existing:
            # Update with weighted average confidence
            row = existing[0]
            old_conf = row['confidence']
            count = row['discovery_count']
            new_count = count + 1
            new_conf = (old_conf * count + confidence) / new_count
            
            self.db.execute_query("""
                UPDATE action5_behavior_map
                SET behavior_type = ?,
                    affected_objects = ?,
                    effect_description = ?,
                    confidence = ?,
                    discovery_count = ?,
                    last_observed = CURRENT_TIMESTAMP
                WHERE game_type = ? AND level_number = ?
            """, (behavior_type, affected_str, effect_description, new_conf, new_count, game_type, level))
            
            logger.debug(f"[ACTION5] Updated behavior for {game_type} L{level}: {behavior_type} (conf: {new_conf:.2f}, count: {new_count})")
        else:
            # Insert new discovery
            self.db.execute_query("""
                INSERT INTO action5_behavior_map
                (game_type, level_number, behavior_type, affected_objects, effect_description, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (game_type, level, behavior_type, affected_str, effect_description, confidence))
            
            logger.info(f"[ACTION5] New behavior discovered for {game_type} L{level}: {behavior_type}")
    
    def get_action5_behavior(self, game_type: str, level: int) -> Optional[Dict]:
        """
        Retrieve known ACTION5 behavior for a game type and level.
        
        Returns:
            Dict with behavior_type, affected_objects, effect_description, confidence
            or None if no behavior known
        """
        result = self.db.execute_query("""
            SELECT behavior_type, affected_objects, effect_description, confidence
            FROM action5_behavior_map
            WHERE game_type = ? AND level_number = ?
        """, (game_type, level))
        
        if result:
            row = result[0]
            return {
                'behavior_type': row['behavior_type'],
                'affected_objects': row['affected_objects'].split(",") if row['affected_objects'] else [],
                'effect_description': row['effect_description'],
                'confidence': row['confidence']
            }
        return None
    
    def classify_action5_effect(self, action5_effects: Dict, game_type: str, level: int) -> str:
        """
        Classify what ACTION5 does based on observed effects.
        
        Analyzes the tracked effects and determines the behavior type.
        Also saves the discovery to network knowledge.
        
        Args:
            action5_effects: Dict from identify_controlled_objects tracking
            game_type: Game type for storing
            level: Level number
        
        Returns:
            Behavior type string (rotation, toggle, interact, select, unknown)
        """
        if not action5_effects:
            return "unknown"
        
        # Analyze the effects
        total_observations = 0
        position_changes = 0
        affected_ids = []
        
        for obj_id, effects in action5_effects.items():
            if effects['total'] < 1:
                continue
            
            total_observations += effects['total']
            
            if effects['changes'] > 0:
                affected_ids.append(str(obj_id))
                
                # Analyze what kind of changes occurred
                if effects.get('positions'):
                    # If object moved significantly, it's position change
                    position_changes += 1
                
        if total_observations < 2:
            return "unknown"
        
        # Determine behavior type based on patterns
        behavior_type = "interact"  # Default
        effect_description = "ACTION5 affects objects in this level"
        
        change_rate = len(affected_ids) / len(action5_effects) if action5_effects else 0
        
        if change_rate > 0.5:
            # Most objects change - likely global effect
            behavior_type = "toggle"
            effect_description = f"ACTION5 toggles/transforms multiple objects (affects {len(affected_ids)} objects)"
        elif change_rate > 0.0 and len(affected_ids) <= 2:
            # One or two objects change - likely rotation or select
            if position_changes > 0:
                behavior_type = "rotation"
                effect_description = f"ACTION5 rotates object {affected_ids[0] if affected_ids else 'unknown'}"
            else:
                behavior_type = "select"
                effect_description = f"ACTION5 selects or activates object {affected_ids[0] if affected_ids else 'unknown'}"
        
        # Save to network knowledge
        confidence = min(0.9, total_observations / 10)  # More observations = higher confidence
        self.save_action5_behavior(
            game_type=game_type,
            level=level,
            behavior_type=behavior_type,
            affected_objects=affected_ids,
            effect_description=effect_description,
            confidence=confidence
        )
        
        return behavior_type
    
    # =========================================================================
    # ACTION6 PSEUDO BUTTON BEHAVIOR (Network-Level Knowledge)
    # =========================================================================
    
    def save_pseudo_button_behavior(
        self,
        game_type: str,
        level: int,
        region_x: int,
        region_y: int,
        produces_action: str,
        movement_direction: str,
        affected_objects: List[str],
        effect_description: str,
        confidence: float
    ) -> None:
        """
        Save discovered pseudo button behavior to network-level knowledge.
        
        When agents discover what clicking a screen region does,
        share it so other agents can use the pseudo buttons effectively.
        
        Args:
            game_type: The game type
            level: Level number
            region_x, region_y: Screen region (0-7 each, dividing 64x64 into 8x8)
            produces_action: Equivalent action (e.g., 'up', 'down', 'toggle')
            movement_direction: Direction of movement if any
            affected_objects: Object IDs affected by this button
            effect_description: Human-readable description
            confidence: Confidence level (0.0 to 1.0)
        """
        existing = self.db.execute_query("""
            SELECT confidence, discovery_count FROM pseudo_button_behavior
            WHERE game_type = ? AND level_number = ? AND region_x = ? AND region_y = ?
        """, (game_type, level, region_x, region_y))
        
        affected_str = ",".join(str(o) for o in affected_objects) if affected_objects else ""
        
        if existing:
            row = existing[0]
            old_conf = row['confidence']
            count = row['discovery_count']
            new_count = count + 1
            new_conf = (old_conf * count + confidence) / new_count
            
            self.db.execute_query("""
                UPDATE pseudo_button_behavior
                SET produces_action = ?,
                    movement_direction = ?,
                    affected_objects = ?,
                    effect_description = ?,
                    confidence = ?,
                    discovery_count = ?,
                    last_observed = CURRENT_TIMESTAMP
                WHERE game_type = ? AND level_number = ? AND region_x = ? AND region_y = ?
            """, (produces_action, movement_direction, affected_str, effect_description,
                  new_conf, new_count, game_type, level, region_x, region_y))
            
            logger.debug(f"[BUTTON] Updated region ({region_x},{region_y}) for {game_type} L{level}: {produces_action}")
        else:
            self.db.execute_query("""
                INSERT INTO pseudo_button_behavior
                (game_type, level_number, region_x, region_y, produces_action,
                 movement_direction, affected_objects, effect_description, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (game_type, level, region_x, region_y, produces_action,
                  movement_direction, affected_str, effect_description, confidence))
            
            logger.info(f"[BUTTON] New pseudo button at ({region_x},{region_y}) for {game_type} L{level}: {produces_action}")
    
    def get_pseudo_button_behavior(self, game_type: str, level: int, region_x: int, region_y: int) -> Optional[Dict]:
        """
        Retrieve known pseudo button behavior for a specific screen region.
        
        Returns:
            Dict with produces_action, movement_direction, affected_objects, confidence
            or None if no behavior known
        """
        result = self.db.execute_query("""
            SELECT produces_action, movement_direction, affected_objects, effect_description, confidence
            FROM pseudo_button_behavior
            WHERE game_type = ? AND level_number = ? AND region_x = ? AND region_y = ?
        """, (game_type, level, region_x, region_y))
        
        if result:
            row = result[0]
            return {
                'produces_action': row['produces_action'],
                'movement_direction': row['movement_direction'],
                'affected_objects': row['affected_objects'].split(",") if row['affected_objects'] else [],
                'effect_description': row['effect_description'],
                'confidence': row['confidence']
            }
        return None
    
    def get_all_pseudo_buttons(self, game_type: str, level: int, min_confidence: float = 0.5) -> List[Dict]:
        """
        Get all known pseudo buttons for a game/level.
        
        Args:
            game_type: Game type to query
            level: Level number
            min_confidence: Minimum confidence threshold
        
        Returns:
            List of pseudo button dicts with region coords and behavior
        """
        results = self.db.execute_query("""
            SELECT region_x, region_y, produces_action, movement_direction, 
                   affected_objects, effect_description, confidence
            FROM pseudo_button_behavior
            WHERE game_type = ? AND level_number = ? AND confidence >= ?
            ORDER BY confidence DESC
        """, (game_type, level, min_confidence))
        
        buttons = []
        for row in results or []:
            buttons.append({
                'region_x': row['region_x'],
                'region_y': row['region_y'],
                'screen_x_range': (row['region_x'] * 8, row['region_x'] * 8 + 7),
                'screen_y_range': (row['region_y'] * 8, row['region_y'] * 8 + 7),
                'produces_action': row['produces_action'],
                'movement_direction': row['movement_direction'],
                'affected_objects': row['affected_objects'].split(",") if row['affected_objects'] else [],
                'effect_description': row['effect_description'],
                'confidence': row['confidence']
            })
        return buttons
    
    def classify_pseudo_button_effects(
        self,
        action6_region_effects: Dict,
        game_type: str,
        level: int
    ) -> Dict[Tuple[int, int], str]:
        """
        Classify and save pseudo button behaviors based on tracked effects.
        
        Analyzes what each screen region does when clicked and saves
        the discoveries to network knowledge.
        
        Args:
            action6_region_effects: Dict from identify_controlled_objects tracking
            game_type: Game type for storing
            level: Level number
        
        Returns:
            Dict mapping (region_x, region_y) -> behavior description
        """
        classified = {}
        
        for region_key, effects in action6_region_effects.items():
            region_x, region_y = region_key
            
            if effects['total'] < 2:
                continue  # Not enough samples
            
            # Determine dominant effect
            directions = {
                'up': effects['up'],
                'down': effects['down'],
                'left': effects['left'],
                'right': effects['right']
            }
            
            max_direction = max(directions.items(), key=lambda x: x[1])
            toggle_count = effects['toggle']
            no_effect_count = effects['no_effect']
            total = effects['total']
            
            # Determine what this button does
            if no_effect_count > total * 0.7:
                # Mostly no effect - not a useful button
                continue
            
            affected_list = list(effects['affected_objects'])
            
            if toggle_count > max_direction[1] and toggle_count > total * 0.3:
                # Toggle behavior dominates
                produces_action = 'toggle'
                movement_direction = 'none'
                effect_desc = f"Clicking region ({region_x},{region_y}) toggles/spawns objects"
            elif max_direction[1] > total * 0.4:
                # Directional movement dominates
                produces_action = f'move_{max_direction[0]}'
                movement_direction = max_direction[0]
                effect_desc = f"Clicking region ({region_x},{region_y}) moves objects {max_direction[0]}"
            else:
                # Mixed or unclear effect
                produces_action = 'interact'
                movement_direction = 'mixed'
                effect_desc = f"Clicking region ({region_x},{region_y}) has mixed effects"
            
            confidence = min(0.9, effects['total'] / 10)
            
            # Save to network
            self.save_pseudo_button_behavior(
                game_type=game_type,
                level=level,
                region_x=region_x,
                region_y=region_y,
                produces_action=produces_action,
                movement_direction=movement_direction,
                affected_objects=affected_list,
                effect_description=effect_desc,
                confidence=confidence
            )
            
            classified[region_key] = produces_action
        
        return classified


# ============================================================================
# TWO-STREAMS CONSCIOUSNESS: WEAVING REPORTER
# ============================================================================

class WeavingReporter:
    """
    Generates self-reflection "weaving reports" for every action.
    
    Philosophy: Every action sent to ARC API includes full self_reflection weaving data.
    This is the agent's introspection visible in every API call.
    
    Local Database Storage: Uses sampling to prevent bloat:
    - Sampling Rate: Store 1 in 10 decisions locally (10%)
    - Exception: Always store if conflict_detected = True
    - Exception: Always store level completion / game end decisions
    """
    
    # Sampling rate for local storage (10% of non-exceptional decisions)
    SAMPLING_RATE = 0.1
    
    def __init__(self, db: DatabaseInterface):
        """Initialize weaving reporter."""
        self.db = db
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure decision_weaving_reports table exists."""
        # Table should be created in Phase 1, but ensure it exists
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS decision_weaving_reports (
                report_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                game_id TEXT NOT NULL,
                level_number INTEGER,
                action_number INTEGER,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                emotional_input REAL,
                semantic_input REAL,
                identity_input REAL,
                private_memory_strength REAL,
                network_recommendation_strength REAL,
                self_network_bias REAL,
                final_decision_weight REAL,
                chosen_action TEXT,
                alternative_action TEXT,
                conflict_detected BOOLEAN DEFAULT FALSE,
                outcome_correct BOOLEAN,
                FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
            )
        """)
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_weaving_agent_game 
            ON decision_weaving_reports(agent_id, game_id)
        """)
    
    def generate_report(
        self,
        agent_id: str,
        game_id: str,
        level_number: int,
        action_number: int,
        chosen_action: str,
        private_memory_strength: float,
        network_recommendation_strength: float,
        self_network_bias: float,
        navigation_state: float,
        role_confidence: float,
        role_fit_score: float,
        sensation_profile: Dict,
        alternative_action: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a weaving report for an action decision.
        
        This is called for EVERY action to produce API-ready self-reflection.
        
        Args:
            agent_id: Agent making the decision
            game_id: Current game
            level_number: Current level
            action_number: Action counter in this game
            chosen_action: The action being taken
            private_memory_strength: How strong agent's own memory signal is (0-1)
            network_recommendation_strength: How strong network's recommendation is (0-1)
            self_network_bias: Agent's bias toward self (0=network, 1=self)
            navigation_state: Agent's emotional state (-1 to 1)
            role_confidence: Agent's confidence in their role (0-1)
            role_fit_score: How well agent fits their role (0-1)
            sensation_profile: Agent's sensation mappings
            alternative_action: What network recommended (if different)
            
        Returns:
            Complete weaving report dictionary for API
        """
        import uuid
        from datetime import datetime
        
        # Calculate internal network inputs
        # Emotional: Map navigation_state from [-1,1] to [0,1]
        emotional_input = (navigation_state + 1.0) / 2.0
        
        # Semantic: Average of top sensation scores (if any)
        object_sensations = sensation_profile.get('object_sensations', {})
        if object_sensations:
            top_sensations = sorted(object_sensations.values(), reverse=True)[:3]
            semantic_input = sum(top_sensations) / len(top_sensations) if top_sensations else 0.5
            # Normalize to 0-1 range (sensations are -1 to 1)
            semantic_input = (semantic_input + 1.0) / 2.0
        else:
            semantic_input = 0.5  # Neutral if no sensations
        
        # Identity: Average of role_confidence and role_fit_score
        identity_input = (role_confidence + role_fit_score) / 2.0
        
        # Calculate final decision weight using Two-Streams formula
        # final_weight = private * bias + network * (1 - bias)
        alpha = self_network_bias
        final_decision_weight = (
            private_memory_strength * alpha + 
            network_recommendation_strength * (1.0 - alpha)
        )
        
        # Detect conflict (significant difference between private and network)
        conflict_detected = abs(private_memory_strength - network_recommendation_strength) > 0.3
        
        # Build human-readable summary
        emotion_label = self._get_emotion_label(navigation_state)
        
        report = {
            'report_id': f"weave_{uuid.uuid4().hex[:12]}",
            'agent_id': agent_id,
            'game_id': game_id,
            'level_number': level_number,
            'action_number': action_number,
            'timestamp': datetime.now().isoformat(),
            
            # Internal networks (Three Streams)
            'emotional_input': round(emotional_input, 3),
            'semantic_input': round(semantic_input, 3),
            'identity_input': round(identity_input, 3),
            
            # Two-Streams weighting
            'private_memory_strength': round(private_memory_strength, 3),
            'network_recommendation_strength': round(network_recommendation_strength, 3),
            'self_network_bias': round(self_network_bias, 3),
            'final_decision_weight': round(final_decision_weight, 3),
            
            # Decision
            'chosen_action': chosen_action,
            'alternative_action': alternative_action,
            'conflict_detected': conflict_detected,
            
            # Narrative summary
            'narrative': self._build_narrative(
                emotion_label, private_memory_strength, network_recommendation_strength,
                alpha, chosen_action, alternative_action, conflict_detected
            ),
            
            # Outcome (to be filled in later)
            'outcome_correct': None
        }
        
        return report
    
    def _get_emotion_label(self, navigation_state: float) -> str:
        """Get human-readable emotion label from navigation state."""
        if navigation_state < -0.5:
            return 'frustrated'
        elif navigation_state < -0.1:
            return 'cautious'
        elif navigation_state < 0.1:
            return 'neutral'
        elif navigation_state < 0.5:
            return 'curious'
        else:
            return 'confident'
    
    def _build_narrative(
        self,
        emotion: str,
        private_strength: float,
        network_strength: float,
        alpha: float,
        chosen_action: str,
        alternative: Optional[str],
        conflict: bool
    ) -> str:
        """Build human-readable narrative of decision."""
        parts = []
        
        # Emotional state
        parts.append(f"Feeling {emotion}")
        
        # Stream preference
        if alpha > 0.6:
            parts.append("trusting own experience")
        elif alpha < 0.4:
            parts.append("following network wisdom")
        else:
            parts.append("balancing self and network")
        
        # Conflict
        if conflict:
            if alternative:
                parts.append(f"(conflicted: network suggested {alternative})")
            else:
                parts.append("(internal conflict detected)")
        
        # Decision
        parts.append(f"-> {chosen_action}")
        
        return " | ".join(parts)
    
    def format_for_api(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format weaving report for inclusion in API reasoning payload.
        
        Returns a compact version suitable for the 16KB limit.
        """
        return {
            'emotional_network': report['emotional_input'],
            'semantic_network': report['semantic_input'],
            'identity_network': report['identity_input'],
            'private_memory': report['private_memory_strength'],
            'network_wisdom': report['network_recommendation_strength'],
            'self_trust_bias': report['self_network_bias'],
            'decision_weight': report['final_decision_weight'],
            'conflict': report['conflict_detected'],
            'narrative': report['narrative']
        }
    
    def should_store_locally(self, report: Dict[str, Any], is_terminal: bool = False) -> bool:
        """
        Determine if this report should be stored in local database.
        
        Storage criteria (to prevent bloat):
        - Always store if conflict_detected = True
        - Always store if is_terminal (level/game end)
        - Otherwise, sample at 10% rate
        """
        import random
        
        # Always store conflicts
        if report.get('conflict_detected'):
            return True
        
        # Always store terminal decisions
        if is_terminal:
            return True
        
        # Otherwise, sample
        return random.random() < self.SAMPLING_RATE
    
    def store_report(self, report: Dict[str, Any]) -> None:
        """Store a weaving report in the database."""
        self.db.execute_query("""
            INSERT INTO decision_weaving_reports
            (report_id, agent_id, game_id, level_number, action_number, timestamp,
             emotional_input, semantic_input, identity_input,
             private_memory_strength, network_recommendation_strength,
             self_network_bias, final_decision_weight,
             chosen_action, alternative_action, conflict_detected, outcome_correct)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            report['report_id'], report['agent_id'], report['game_id'],
            report['level_number'], report['action_number'], report['timestamp'],
            report['emotional_input'], report['semantic_input'], report['identity_input'],
            report['private_memory_strength'], report['network_recommendation_strength'],
            report['self_network_bias'], report['final_decision_weight'],
            report['chosen_action'], report['alternative_action'],
            report['conflict_detected'], report.get('outcome_correct')
        ))
    
    def update_outcome(self, report_id: str, outcome_correct: bool) -> None:
        """Update the outcome for a stored report (for meta-learning)."""
        self.db.execute_query("""
            UPDATE decision_weaving_reports
            SET outcome_correct = ?
            WHERE report_id = ?
        """, (outcome_correct, report_id))


if __name__ == "__main__":
    # Test self-model system
    print("=" * 70)
    print("AGENT SELF-MODEL SYSTEM TEST")
    print("=" * 70)
    
    asm = AgentSelfModel()
    
    # Test table creation
    result = asm.db.execute_query("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='agent_object_control'
    """)
    
    if result:
        print("[OK] agent_object_control table exists")
    else:
        print("[FAIL] Table creation failed")
    
    # Test ACTION5 behavior table
    result = asm.db.execute_query("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='action5_behavior_map'
    """)
    
    if result:
        print("[OK] action5_behavior_map table exists")
    else:
        print("[FAIL] ACTION5 behavior table creation failed")
    
    # Test basic functionality
    test_controlled = ["x:5,y:10", "x:6,y:10"]
    asm.store_control_map("test_agent", "test_game", 1, test_controlled, 0.85)
    
    retrieved = asm.get_controlled_objects("test_agent", "test_game", 1)
    if retrieved == test_controlled:
        print("[OK] Store and retrieve working")
    else:
        print(f"[FAIL] Mismatch: {retrieved} != {test_controlled}")
    
    # Test ACTION5 behavior storage
    asm.save_action5_behavior(
        game_type="test_game_type",
        level=1,
        behavior_type="rotation",
        affected_objects=["3", "5"],
        effect_description="ACTION5 rotates object 3",
        confidence=0.75
    )
    
    behavior = asm.get_action5_behavior("test_game_type", 1)
    if behavior and behavior['behavior_type'] == "rotation":
        print("[OK] ACTION5 behavior storage working")
    else:
        print(f"[FAIL] ACTION5 behavior mismatch: {behavior}")
    
    # Test pseudo button behavior storage
    result = asm.db.execute_query("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='pseudo_button_behavior'
    """)
    
    if result:
        print("[OK] pseudo_button_behavior table exists")
    else:
        print("[FAIL] Pseudo button table creation failed")
    
    # Test pseudo button storage
    asm.save_pseudo_button_behavior(
        game_type="test_game_type",
        level=1,
        region_x=7,
        region_y=0,
        produces_action="move_up",
        movement_direction="up",
        affected_objects=["3"],
        effect_description="Clicking top-right moves object up",
        confidence=0.8
    )
    
    button = asm.get_pseudo_button_behavior("test_game_type", 1, 7, 0)
    if button and button['produces_action'] == "move_up":
        print("[OK] Pseudo button behavior storage working")
    else:
        print(f"[FAIL] Pseudo button behavior mismatch: {button}")
    
    # Test get all buttons
    all_buttons = asm.get_all_pseudo_buttons("test_game_type", 1)
    if len(all_buttons) >= 1:
        print(f"[OK] Get all pseudo buttons working ({len(all_buttons)} buttons)")
    else:
        print("[FAIL] Get all pseudo buttons failed")
    
    print("\n[OK] Agent Self-Model system operational")
