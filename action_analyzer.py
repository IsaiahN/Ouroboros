#!/usr/bin/env python3
"""
Action Analyzer - Phase 2
==========================

Analyzes action-object correlations and builds causal chains.
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import json
import uuid
from typing import Dict, List, Optional
from datetime import datetime
from database_interface import DatabaseInterface
from abstraction_config import is_abstraction_enabled
from object_detector import ObjectDetector
import logging

logger = logging.getLogger(__name__)


class ActionAnalyzer:
    """Analyzes relationships between actions and object effects."""
    
    def __init__(self, db_path: str = "core_data.db"):
        self.db = DatabaseInterface(db_path)
        self.enabled = is_abstraction_enabled()
        self.object_detector = ObjectDetector(db_path)
    
    def analyze_action_effects(
        self,
        action: Dict,
        frame_before: Dict,
        frame_after: Dict,
        game_id: str,
        level: int,
        frame_index: int
    ) -> Optional[Dict]:
        """Analyze what effect an action had on objects."""
        if not self.enabled:
            return None
        
        # Detect objects before and after
        objects_before = self.object_detector.detect_objects_in_frame(
            frame_before, game_id, level, frame_index
        )
        objects_after = self.object_detector.detect_objects_in_frame(
            frame_after, game_id, level, frame_index + 1
        )
        
        # Identify affected objects
        affected = self._identify_affected_objects(objects_before, objects_after)
        
        if not affected:
            return None
        
        effect_id = f"effect_{uuid.uuid4().hex[:12]}"
        
        return {
            'effect_id': effect_id,
            'game_id': game_id,
            'level_number': level,
            'action_type': action.get('action', 'unknown'),
            'affected_objects': json.dumps(affected),
            'frame_before': frame_index,
            'frame_after': frame_index + 1,
            'analyzed_at': datetime.now().isoformat()
        }
    
    def _identify_affected_objects(
        self,
        objects_before: List[Dict],
        objects_after: List[Dict]
    ) -> List[Dict]:
        """Identify which objects were affected by the action."""
        affected = []
        
        #  Check for moved/changed objects
        for obj_after in objects_after:
            props_after = json.loads(obj_after['properties'])
            
            # Find corresponding object before
            for obj_before in objects_before:
                props_before = json.loads(obj_before['properties'])
                
                # Same color, but different position = moved
                if props_after['color'] == props_before['color']:
                    if props_after['center'] != props_before['center']:
                        affected.append({
                            'object_id': obj_after['object_id'],
                            'effect_type': 'move',
                            'from': props_before['center'],
                            'to': props_after['center']
                        })
                        break
        
        # Check for created objects
        before_colors = {json.loads(o['properties'])['color'] for o in objects_before}
        for obj_after in objects_after:
            props_after = json.loads(obj_after['properties'])
            if props_after['color'] not in before_colors:
                affected.append({
                    'object_id': obj_after['object_id'],
                    'effect_type': 'create',
                    'at': props_after['center']
                })
        
        return affected
    
    def build_causal_chain(
        self,
        actions: List[Dict],  
        outcome: str,
        game_id: str,
        level: int
    ) -> Optional[Dict]:
        """Build causal chain from action sequence to outcome."""
        if not self.enabled or not actions:
            return None
        
        chain_id = f"chain_{uuid.uuid4().hex[:12]}"
        
        return {
            'chain_id': chain_id,
            'game_id': game_id,
            'level_number': level,
            'action_sequence': json.dumps([a.get('action', 'unknown') for a in actions]),
            'outcome': outcome,
            'confidence': 1.0 if outcome == 'level_complete' else 0.5,
            'learned_at': datetime.now().isoformat()
        }
    
    def store_effects(self, effects: List[Dict]):
        """Store action effects in database."""
        if not self.enabled or not effects:
            return
        
        for effect in effects:
            try:
                self.db.execute_query("""
                    INSERT OR REPLACE INTO action_effects
                    (effect_id, game_id, level_number, action_type, affected_objects, 
                     frame_before, frame_after, analyzed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    effect['effect_id'], effect['game_id'], effect['level_number'],
                    effect['action_type'], effect['affected_objects'],
                    effect['frame_before'], effect['frame_after'], effect['analyzed_at']
                ))
            except Exception as e:
                logger.error(f"Failed to store effect: {e}")
    
    def store_causal_chain(self, chain: Dict):
        """Store causal chain in database."""
        if not self.enabled or not chain:
            return
        
        try:
            self.db.execute_query("""
                INSERT OR REPLACE INTO causal_chains
                (chain_id, game_id, level_number, action_sequence, outcome, confidence, learned_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                chain['chain_id'], chain['game_id'], chain['level_number'],
                chain['action_sequence'], chain['outcome'],
                chain['confidence'], chain['learned_at']
            ))
        except Exception as e:
            logger.error(f"Failed to store causal chain: {e}")
