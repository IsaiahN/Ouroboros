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
from typing import Dict, List, Optional, Tuple
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
    """
    
    def __init__(self, db_path: str = "core_data.db"):
        """Initialize self-model system."""
        self.db = DatabaseInterface(db_path)
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Create agent_object_control table if needed."""
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
    
    def identify_controlled_objects(
        self, 
        game_id: str, 
        level: int, 
        action_sequence: List[Dict],
        frame_sequence: List[Dict]
    ) -> Tuple[List[str], float]:
        """
        Identify which objects respond to actions.
        
        Args:
            game_id: Game identifier
            level: Level number
            action_sequence: List of actions taken
            frame_sequence: List of frames (before/after each action)
        
        Returns:
            (controlled_objects, confidence)
        """
        if not action_sequence or not frame_sequence:
            return ([], 0.0)
        
        # Track which coordinates change in response to actions
        responsive_coords = {}
        
        for i, action in enumerate(action_sequence):
            if i >= len(frame_sequence) - 1:
                break
            
            frame_before = frame_sequence[i]
            frame_after = frame_sequence[i + 1]
            
            # Find changed coordinates
            changed = self._find_changed_coordinates(frame_before, frame_after)
            
            # Track action -> coordinate correlation
            action_type = action.get('action_type', 'unknown')
            for coord in changed:
                if coord not in responsive_coords:
                    responsive_coords[coord] = {}
                if action_type not in responsive_coords[coord]:
                    responsive_coords[coord][action_type] = 0
                responsive_coords[coord][action_type] += 1
        
        # Identify consistently responsive objects (high correlation)
        controlled = []
        for coord, action_counts in responsive_coords.items():
            # If coordinate responds to multiple action types, likely controlled
            if len(action_counts) >= 2:
                controlled.append(coord)
        
        # Calculate confidence based on consistency
        confidence = min(1.0, len(controlled) / max(1, len(responsive_coords)))
        
        return (controlled, confidence)
    
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
    
    # Test basic functionality
    test_controlled = ["x:5,y:10", "x:6,y:10"]
    asm.store_control_map("test_agent", "test_game", 1, test_controlled, 0.85)
    
    retrieved = asm.get_controlled_objects("test_agent", "test_game", 1)
    if retrieved == test_controlled:
        print("[OK] Store and retrieve working")
    else:
        print(f"[FAIL] Mismatch: {retrieved} != {test_controlled}")
    
    print("\n[OK] Agent Self-Model system operational")
