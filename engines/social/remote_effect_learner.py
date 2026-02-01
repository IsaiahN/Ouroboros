import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
Remote Effect Learner - Action-at-Distance Causal Relationship Discovery
=========================================================================

Extracted from cods_engine.py - a standalone component for learning
remote causation patterns (when touching object A causes change at location B).

SYMBOLIC MECHANICS - Universal Component

In many puzzle games, touching object A causes change at distant location B.
This is "action-at-distance" or "remote causation" - fundamentally different
from direct contact effects.

This learner:
1. Detects when actions cause remote changes (distance > 3 cells)
2. Correlates trigger objects with effect types
3. Builds a causal model: trigger_signature -> effect_description
4. Shares validated effects to the network database

Applicable to ALL games, not just specific game types.
"""

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


class RemoteEffectLearner:
    """
    Learns action-at-distance causal relationships.
    
    SYMBOLIC MECHANICS - Universal Component
    
    In many puzzle games, touching object A causes change at distant location B.
    This is "action-at-distance" or "remote causation" - fundamentally different
    from direct contact effects.
    
    This learner:
    1. Detects when actions cause remote changes (distance > 3 cells)
    2. Correlates trigger objects with effect types
    3. Builds a causal model: trigger_signature -> effect_description
    4. Shares validated effects to the network database
    
    Applicable to ALL games, not just specific game types.
    """
    
    def __init__(
        self, 
        game_type: Optional[str] = None, 
        db: Optional[DatabaseInterface] = None, 
        db_path: str = "core_data.db"
    ):
        self.game_type = game_type
        self.db = db or DatabaseInterface(db_path)
        
        # Local observation tracking
        self.observations: List[Dict[str, Any]] = []
        self.trigger_effect_map: Dict[str, List[Dict[str, Any]]] = {}
        
        # Validated hypotheses
        self.validated_effects: Dict[str, Dict[str, Any]] = {}
        
    def observe_action(
        self,
        frame_before: List[List[int]],
        frame_after: List[List[int]],
        action_position: Tuple[int, int],
        action_type: int,
        overlap_color: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Observe the effect of an action and detect remote changes.
        
        Args:
            frame_before: Frame before action
            frame_after: Frame after action
            action_position: Where agent was when action occurred
            action_type: Action taken (1-7)
            overlap_color: Color of object overlapped (if any)
            
        Returns:
            Dict describing any detected remote effect
        """
        result = {
            'remote_effect_detected': False,
            'trigger_position': action_position,
            'effect_region': None,
            'effect_type': None,
            'trigger_signature': None,
            'distance': 0
        }
        
        if not frame_before or not frame_after:
            return result
        
        # Find all changes between frames
        changes = self._find_frame_changes(frame_before, frame_after)
        if not changes:
            return result
        
        # Filter to remote changes (distance > 3 from action position)
        remote_changes = []
        ax, ay = action_position
        
        for change in changes:
            cx, cy = change['position']
            distance = math.sqrt((cx - ax) ** 2 + (cy - ay) ** 2)
            if distance > 3:
                change['distance'] = distance
                remote_changes.append(change)
        
        if not remote_changes:
            return result
        
        # We have remote effects!
        result['remote_effect_detected'] = True
        
        # Characterize the effect
        effect_type = self._characterize_effect(remote_changes)
        result['effect_type'] = effect_type
        
        # Calculate effect region (bounding box of changes)
        xs = [c['position'][0] for c in remote_changes]
        ys = [c['position'][1] for c in remote_changes]
        result['effect_region'] = {
            'x_min': min(xs), 'x_max': max(xs),
            'y_min': min(ys), 'y_max': max(ys)
        }
        result['distance'] = min(c['distance'] for c in remote_changes)
        
        # Create trigger signature based on overlap color or position
        if overlap_color is not None:
            trigger_sig = f"color_{overlap_color}"
        else:
            # Use bucketed position
            bx, by = ax // 4, ay // 4
            trigger_sig = f"pos_{bx}_{by}"
        result['trigger_signature'] = trigger_sig
        
        # Store observation
        observation = {
            'trigger': trigger_sig,
            'effect_type': effect_type,
            'effect_region': result['effect_region'],
            'distance': result['distance'],
            'action_type': action_type
        }
        self.observations.append(observation)
        
        # Add to trigger-effect map
        if trigger_sig not in self.trigger_effect_map:
            self.trigger_effect_map[trigger_sig] = []
        self.trigger_effect_map[trigger_sig].append(observation)
        
        return result
    
    def _find_frame_changes(
        self, 
        frame_before: List[List[int]], 
        frame_after: List[List[int]]
    ) -> List[Dict[str, Any]]:
        """Find all pixel changes between frames."""
        changes = []
        
        height = min(len(frame_before), len(frame_after))
        width = min(
            len(frame_before[0]) if frame_before else 0,
            len(frame_after[0]) if frame_after else 0
        )
        
        for y in range(height):
            for x in range(width):
                before = frame_before[y][x]
                after = frame_after[y][x]
                if before != after:
                    changes.append({
                        'position': (x, y),
                        'before': before,
                        'after': after
                    })
        
        return changes
    
    def _characterize_effect(self, changes: List[Dict[str, Any]]) -> str:
        """
        Characterize the type of remote effect.
        
        Returns one of: 'appear', 'disappear', 'transform', 'spread', 'shift'
        """
        appearances = sum(1 for c in changes if c['before'] == 0 and c['after'] != 0)
        disappearances = sum(1 for c in changes if c['before'] != 0 and c['after'] == 0)
        transforms = sum(1 for c in changes if c['before'] != 0 and c['after'] != 0)
        
        total = len(changes)
        
        if appearances > total * 0.7:
            return 'appear'
        elif disappearances > total * 0.7:
            return 'disappear'
        elif transforms > total * 0.7:
            return 'transform'
        elif appearances > 0 and disappearances > 0 and abs(appearances - disappearances) <= 2:
            return 'shift'
        else:
            return 'spread'
    
    def validate_hypotheses(self, min_observations: int = 3) -> int:
        """
        Validate trigger-effect relationships and share to network.
        
        Returns number of hypotheses shared to network.
        """
        shared_count = 0
        
        for trigger_key, observations in self.trigger_effect_map.items():
            if len(observations) < min_observations:
                continue
            
            # Count effect types for this trigger
            effect_counts: Dict[str, int] = {}
            for obs in observations:
                effect_type = obs['effect_type']
                effect_counts[effect_type] = effect_counts.get(effect_type, 0) + 1
            
            # Check for consistent effect
            total = len(observations)
            for effect_type, count in effect_counts.items():
                if count >= min_observations and count / total >= 0.7:
                    # This effect is consistent enough to share
                    self._share_to_network(trigger_key, effect_type, count, total)
                    shared_count += 1
                    
                    # Mark as validated
                    self.validated_effects[trigger_key] = {
                        'effect_type': effect_type,
                        'confidence': count / total,
                        'observations': count
                    }
        
        return shared_count
    
    def _share_to_network(
        self, 
        trigger_key: str, 
        effect_type: str, 
        count: int, 
        total: int
    ):
        """Share a validated remote effect to the network database."""
        try:
            # Extract trigger info from key
            if trigger_key.startswith('color_'):
                trigger_color = int(trigger_key.replace('color_', ''))
                trigger_position = None
            else:
                trigger_color = None
                parts = trigger_key.replace('pos_', '').split('_')
                trigger_position = f"[{parts[0]}, {parts[1]}]"
            
            self.db.execute_query("""
                INSERT OR REPLACE INTO remote_effect_hypotheses (
                    game_type, level_number, trigger_position, trigger_object,
                    effect_region, effect_type, observation_count, reliability, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, TRUE)
            """, (
                self.game_type or 'unknown',
                0,  # Level 0 means game-wide
                trigger_position,
                str(trigger_color) if trigger_color else None,
                '[]',  # Effect region varies
                effect_type,
                count,
                count / total
            ))
        except Exception as e:
            logger.warning(f"Failed to share remote effect: {e}")
    
    def query_network_effects(
        self, 
        game_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Query the network for known remote effects."""
        game = game_type or self.game_type or 'unknown'
        
        try:
            results = self.db.execute_query("""
                SELECT trigger_object, effect_type, observation_count, reliability
                FROM remote_effect_hypotheses
                WHERE game_type = ? AND is_active = TRUE
                ORDER BY reliability DESC
            """, (game,))
            
            return [
                {
                    'trigger_color': int(r['trigger_object']) if r.get('trigger_object') and str(r['trigger_object']).isdigit() else None,
                    'effect_type': r.get('effect_type'),
                    'observation_count': r.get('observation_count'),
                    'reliability': r.get('reliability')
                }
                for r in results
            ]
        except Exception as e:
            logger.warning(f"Failed to query network effects: {e}")
            return []
    
    def reset(self):
        """Reset learner for new game."""
        self.observations = []
        self.trigger_effect_map = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize learner state."""
        return {
            'game_type': self.game_type,
            'observation_count': len(self.observations),
            'trigger_count': len(self.trigger_effect_map),
            'validated_effects': self.validated_effects
        }


__all__ = ['RemoteEffectLearner']
