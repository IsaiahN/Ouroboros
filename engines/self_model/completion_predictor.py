#!/usr/bin/env python3
"""
Completion Predictor
====================

Predicts steps to completion for symbolic transformation puzzles.

SYMBOLIC MECHANICS - Phase 3.4 of LS20 Defeat Plan

Given current key state + known tool effects, this class:
1. Calculates minimum tool uses needed to match key to lock
2. Plans optimal tool visit order based on agent position
3. Estimates total actions required for completion

Uses network knowledge from tool_effect_hypotheses table.

Module size: ~400 lines (within 300-700 target)
"""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import time
import logging
from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .symbolic_tracker import SymbolicStateTracker

logger = logging.getLogger(__name__)


class CompletionPredictor:
    """
    Predicts minimum steps needed to transform key to match lock.
    
    Uses network knowledge from tool_effect_hypotheses table to make
    informed predictions about which tools produce which effects.
    """
    
    def __init__(self, db_path: str = "core_data.db"):
        self.db_path = db_path
        self._tool_effect_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._cache_expiry: float = 0.0
        self.CACHE_TTL = 60.0  # Refresh cache every 60 seconds
    
    def _get_tool_effects(self, game_type: str) -> List[Dict[str, Any]]:
        """
        Get known tool effects for a game type from network.
        
        Returns list of:
        {
            'tool_signature': 'color_5',
            'effect_type': 'shape_change' | 'color_change',
            'state_before_signature': str,
            'state_after_signature': str,
            'observation_count': int,
            'confidence': float
        }
        """
        current_time = time.time()
        
        # Check cache
        if game_type in self._tool_effect_cache and current_time < self._cache_expiry:
            return self._tool_effect_cache[game_type]
        
        effects: List[Dict[str, Any]] = []
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT tool_signature, effect_type, state_before_signature,
                       state_after_signature, observation_count, confidence
                FROM tool_effect_hypotheses
                WHERE game_type = ? AND is_active = TRUE AND confidence > 0.3
                ORDER BY observation_count DESC, confidence DESC
            """, (game_type,))
            
            for row in cursor.fetchall():
                effects.append({
                    'tool_signature': row['tool_signature'],
                    'effect_type': row['effect_type'],
                    'state_before_signature': row['state_before_signature'],
                    'state_after_signature': row['state_after_signature'],
                    'observation_count': row['observation_count'],
                    'confidence': row['confidence']
                })
            
            conn.close()
            
            # Update cache
            self._tool_effect_cache[game_type] = effects
            self._cache_expiry = current_time + self.CACHE_TTL
            
        except Exception as e:
            logger.debug(f"Failed to get tool effects: {e}")
        
        return effects
    
    def predict_steps_to_completion(
        self,
        game_type: str,
        key_state: Dict[str, Any],
        lock_state: Dict[str, Any],
        known_tool_effects: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Predict minimum steps needed to transform key to match lock.
        
        Args:
            game_type: Game type for querying tool effects
            key_state: Current key object state (from SymbolicStateTracker)
            lock_state: Target lock object state
            known_tool_effects: Optional override of tool effects (otherwise queries DB)
            
        Returns:
            {
                'steps_needed': int,  # Minimum tool uses estimated
                'transformations_required': List[str],  # What needs to change
                'tools_to_use': List[str],  # Which tools to use
                'confidence': float,  # How confident in this prediction
                'achievable': bool,  # Whether we have tools to achieve this
                'reasoning': str  # Explanation of prediction
            }
        """
        result: Dict[str, Any] = {
            'steps_needed': 0,
            'transformations_required': [],
            'tools_to_use': [],
            'confidence': 0.0,
            'achievable': False,
            'reasoning': ''
        }
        
        if not key_state or not lock_state:
            result['reasoning'] = 'Missing key or lock state'
            return result
        
        # Get tool effects from network if not provided
        if known_tool_effects is None:
            known_tool_effects = self._get_tool_effects(game_type)
        
        # Determine what transformations are needed
        transformations_needed: List[Dict[str, Any]] = []
        
        # Check shape difference
        key_shape = key_state.get('shape_signature')
        lock_shape = lock_state.get('shape_signature')
        if key_shape != lock_shape:
            transformations_needed.append({
                'type': 'shape_change',
                'from': key_shape,
                'to': lock_shape
            })
        
        # Check color difference
        key_color = key_state.get('color')
        lock_color = lock_state.get('color')
        if key_color != lock_color:
            transformations_needed.append({
                'type': 'color_change',
                'from': key_color,
                'to': lock_color
            })
        
        # Check aspect ratio difference
        key_aspect = key_state.get('aspect_ratio', 1.0)
        lock_aspect = lock_state.get('aspect_ratio', 1.0)
        transform_types = [t['type'] for t in transformations_needed]
        if abs(key_aspect - lock_aspect) > 0.2 and 'shape_change' not in transform_types:
            transformations_needed.append({
                'type': 'shape_change',
                'from': f'aspect_{key_aspect:.1f}',
                'to': f'aspect_{lock_aspect:.1f}'
            })
        
        result['transformations_required'] = [
            f"{t['type']}: {t['from']} -> {t['to']}" 
            for t in transformations_needed
        ]
        
        if not transformations_needed:
            result['steps_needed'] = 0
            result['achievable'] = True
            result['confidence'] = 1.0
            result['reasoning'] = 'Key already matches lock - no transformation needed'
            return result
        
        # Match transformations to known tool effects
        tools_for_transform: Dict[str, List[Dict[str, Any]]] = {
            'shape_change': [],
            'color_change': []
        }
        
        for effect in known_tool_effects:
            effect_type = effect.get('effect_type', '')
            tool_sig = effect.get('tool_signature', '')
            confidence = effect.get('confidence', 0.0)
            
            if effect_type in tools_for_transform:
                tools_for_transform[effect_type].append({
                    'tool': tool_sig,
                    'confidence': confidence,
                    'observations': effect.get('observation_count', 1)
                })
        
        # Calculate steps needed
        steps = 0
        tools_to_use: List[str] = []
        total_confidence = 0.0
        confidence_samples = 0
        
        for transform in transformations_needed:
            transform_type = transform['type']
            available_tools = tools_for_transform.get(transform_type, [])
            
            if available_tools:
                # Use the most confident tool for this transformation
                best_tool = max(available_tools, key=lambda t: t['confidence'])
                tools_to_use.append(best_tool['tool'])
                total_confidence += best_tool['confidence']
                confidence_samples += 1
                steps += 1  # Each transformation requires at least one tool use
            else:
                # No known tool - estimate 2 steps (find + use)
                tools_to_use.append(f'unknown_{transform_type}_tool')
                steps += 2  # Need to discover the tool first
                total_confidence += 0.3  # Low confidence
                confidence_samples += 1
        
        result['steps_needed'] = steps
        result['tools_to_use'] = tools_to_use
        
        # Check if achievable
        known_effect_types = {e.get('effect_type') for e in known_tool_effects}
        all_covered = all(
            t['type'] in known_effect_types for t in transformations_needed
        )
        result['achievable'] = all_covered or len(known_tool_effects) > 0
        result['confidence'] = total_confidence / max(confidence_samples, 1)
        
        # Build reasoning
        if result['achievable']:
            result['reasoning'] = f"Need {steps} tool use(s): {', '.join(tools_to_use)}"
        else:
            missing = [t['type'] for t in transformations_needed if t['type'] not in known_effect_types]
            result['reasoning'] = f"Need {steps} step(s) but missing tools for: {missing}"
        
        return result
    
    def plan_tool_visit_order(
        self,
        agent_position: Tuple[int, int],
        tool_locations: Dict[str, Dict[str, Any]],
        required_tools: List[str],
        frame_width: int = 64,
        frame_height: int = 64
    ) -> Dict[str, Any]:
        """
        Plan optimal order to visit tools based on agent position.
        
        Args:
            agent_position: Current (x, y) position of agent
            tool_locations: Dict of tool_id -> {centroid, color, ...}
            required_tools: List of tool signatures needed
            frame_width: Frame width for distance calculations
            frame_height: Frame height for distance calculations
            
        Returns:
            {
                'visit_order': List[str],  # Tool IDs in order to visit
                'estimated_actions': int,  # Total movement actions estimated
                'path_segments': List[Dict],  # Each segment with from/to/distance
                'total_distance': int  # Manhattan distance total
            }
        """
        result: Dict[str, Any] = {
            'visit_order': [],
            'estimated_actions': 0,
            'path_segments': [],
            'total_distance': 0
        }
        
        if not agent_position or not tool_locations or not required_tools:
            return result
        
        # Match required tools to available tool locations
        available_tools: List[Dict[str, Any]] = []
        for tool_id, tool_state in tool_locations.items():
            tool_color = tool_state.get('color', 0)
            tool_sig = f"color_{tool_color}"
            
            # Check if this tool is one we need
            if tool_sig in required_tools or any(req in tool_id for req in required_tools):
                centroid = tool_state.get('centroid')
                if centroid:
                    available_tools.append({
                        'tool_id': tool_id,
                        'tool_sig': tool_sig,
                        'position': centroid
                    })
        
        if not available_tools:
            return result
        
        # Greedy nearest-neighbor ordering
        current_pos: Tuple[float, float] = (float(agent_position[0]), float(agent_position[1]))
        remaining_tools = available_tools.copy()
        visit_order: List[str] = []
        path_segments: List[Dict[str, Any]] = []
        total_distance = 0
        
        while remaining_tools:
            # Find nearest tool
            nearest: Optional[Dict[str, Any]] = None
            nearest_dist = float('inf')
            
            for tool in remaining_tools:
                pos = tool['position']
                tx, ty = float(pos[0]), float(pos[1])
                dist = abs(tx - current_pos[0]) + abs(ty - current_pos[1])  # Manhattan
                if dist < nearest_dist:
                    nearest_dist = dist
                    nearest = tool
            
            if nearest:
                # Add to visit order
                visit_order.append(nearest['tool_id'])
                path_segments.append({
                    'from': current_pos,
                    'to': nearest['position'],
                    'tool_id': nearest['tool_id'],
                    'distance': int(nearest_dist)
                })
                total_distance += int(nearest_dist)
                pos = nearest['position']
                current_pos = (float(pos[0]), float(pos[1]))
                remaining_tools.remove(nearest)
        
        # Estimate actions: distance + overhead for tool interaction
        estimated_actions = total_distance + len(visit_order) * 2
        
        result['visit_order'] = visit_order
        result['estimated_actions'] = estimated_actions
        result['path_segments'] = path_segments
        result['total_distance'] = total_distance
        
        return result
    
    def get_completion_estimate(
        self,
        game_type: str,
        symbolic_tracker: "SymbolicStateTracker",
        agent_position: Optional[Tuple[int, int]] = None
    ) -> Dict[str, Any]:
        """
        Get full completion estimate combining step prediction and path planning.
        
        This is the main entry point for completion prediction.
        
        Args:
            game_type: Game type for tool effect lookup
            symbolic_tracker: SymbolicStateTracker with current key/lock state
            agent_position: Optional agent position for path planning
            
        Returns:
            {
                'completion_possible': bool,
                'steps_to_match': int,  # Tool uses needed
                'actions_estimated': int,  # Total actions including movement
                'transformations': List[str],
                'tool_visit_order': List[str],
                'confidence': float,
                'match_progress': float,  # Current match score
                'summary': str
            }
        """
        result: Dict[str, Any] = {
            'completion_possible': False,
            'steps_to_match': 0,
            'actions_estimated': 0,
            'transformations': [],
            'tool_visit_order': [],
            'confidence': 0.0,
            'match_progress': 0.0,
            'summary': ''
        }
        
        if not symbolic_tracker:
            result['summary'] = 'No symbolic tracker available'
            return result
        
        # Get current match progress
        result['match_progress'] = symbolic_tracker.current_match_score
        
        # If already matched, no steps needed
        if result['match_progress'] >= 0.95:
            result['completion_possible'] = True
            result['confidence'] = 1.0
            result['summary'] = 'Key matches lock - seek gate to complete'
            return result
        
        # Get key and lock states
        key_state = (
            next(iter(symbolic_tracker.key_objects.values()), None) 
            if symbolic_tracker.key_objects else None
        )
        lock_state = (
            next(iter(symbolic_tracker.lock_objects.values()), None) 
            if symbolic_tracker.lock_objects else None
        )
        
        if not key_state or not lock_state:
            result['summary'] = 'Key or lock not yet identified'
            return result
        
        # Predict steps needed
        step_prediction = self.predict_steps_to_completion(
            game_type=game_type,
            key_state=key_state,
            lock_state=lock_state
        )
        
        result['steps_to_match'] = step_prediction['steps_needed']
        result['transformations'] = step_prediction['transformations_required']
        result['confidence'] = step_prediction['confidence']
        result['completion_possible'] = step_prediction['achievable']
        
        # Plan tool visit order if we have position and tools
        if agent_position and symbolic_tracker.tool_objects:
            path_plan = self.plan_tool_visit_order(
                agent_position=agent_position,
                tool_locations=symbolic_tracker.tool_objects,
                required_tools=step_prediction['tools_to_use']
            )
            
            result['tool_visit_order'] = path_plan['visit_order']
            result['actions_estimated'] = path_plan['estimated_actions']
        else:
            # Estimate without path: assume 10 actions per tool use average
            result['actions_estimated'] = step_prediction['steps_needed'] * 10
        
        # Build summary
        if result['completion_possible']:
            result['summary'] = (
                f"Need {result['steps_to_match']} tool use(s), "
                f"~{result['actions_estimated']} actions. "
                f"Match at {result['match_progress']:.0%}. "
                f"Confidence: {result['confidence']:.0%}"
            )
        else:
            result['summary'] = (
                f"Completion uncertain - need to discover tools. "
                f"Transformations needed: {', '.join(result['transformations'])}"
            )
        
        return result
