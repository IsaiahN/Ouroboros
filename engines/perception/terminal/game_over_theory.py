import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
Game-Over Theory System - Human-Readable Failure Hypotheses
============================================================

Generates human-readable theories about WHY the game ended in game-over.
Agents can learn from these theories and actively test/avoid them.

Theory types:
- boundary_collision: Object hit edge of grid
- oscillation_trap: Repeated A-B-A-B action pattern punished
- repeated_failure: Same action keeps failing at location
- death_zone: Known dangerous region
- action_state_mismatch: Default/unknown cause
"""

import logging
from typing import Dict, List, Optional, Any

from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


class GameOverTheoryGenerator:
    """
    Generates theories about why game-overs occurred.
    
    Creates human-readable, testable hypotheses that agents
    can learn from and use to avoid similar failures.
    """
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
        
    def generate_game_over_theory(self, 
                                   game_id: str,
                                   level_number: int,
                                   frame_before_death: List[List[int]],
                                   fatal_action: int,
                                   pre_death_actions: List[int],
                                   controlled_objects: Optional[List[Dict]] = None,
                                   death_zones: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Generate a THEORY about why the game ended in game-over.
        
        Creates human-readable hypotheses that agents can learn from
        and actively test/avoid in future games.
        
        Args:
            game_id: Game where death occurred
            level_number: Level where death occurred
            frame_before_death: Frame state before fatal action
            fatal_action: The action that caused game_over
            pre_death_actions: Last N actions before death
            controlled_objects: Objects the agent was controlling
            death_zones: Pre-fetched death zones for this level (optional)
            
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
            
            # Check for similar past patterns from position_death_patterns (single source of truth)
            existing_patterns = self.db.execute_query("""
                SELECT fatal_action, death_count, danger_score, bucket_x, bucket_y, bucket_size
                FROM position_death_patterns
                WHERE game_type = ? AND level_number = ? AND is_active = 1
                ORDER BY death_count DESC
                LIMIT 5
            """, (game_type, level_number))
            
            if existing_patterns:
                most_common = existing_patterns[0]
                if most_common['death_count'] >= 3:
                    # Build position context for actionable theory
                    position_str = ""
                    bucket_x = most_common.get('bucket_x', 0)
                    bucket_y = most_common.get('bucket_y', 0)
                    bucket_size = most_common.get('bucket_size', 8)
                    position_str = f" near position ({bucket_x * bucket_size}, {bucket_y * bucket_size})"
                    
                    theory['theory'] = f"[{game_type.upper()}] ACTION{most_common['fatal_action']}{position_str} has caused game-over {most_common['death_count']} times at L{level_number}. This action is dangerous in this region."
                    theory['hypothesis_type'] = 'repeated_failure'
                    theory['avoidance_strategy'] = f"In {game_type} L{level_number}, avoid ACTION{most_common['fatal_action']}{position_str}. Try alternative actions or approach from different angle."
                    theory['confidence'] = min(0.9, most_common['danger_score'])
                    theory['testable_prediction'] = f"In {game_type} L{level_number}, ACTION{most_common['fatal_action']} from similar position should reproduce failure."
                    return theory
            
            # Check death zones (use provided or query)
            zones = death_zones
            if zones is None:
                zones = self._get_level_death_zones(game_type, level_number)
                
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
    
    def _get_level_death_zones(self, game_type: str, level_number: int) -> List[Dict]:
        """Get death zones for a level (helper for theory generation)."""
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
    
    def get_game_over_theories(self, game_id: str, level_number: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get existing game-over theories for a game/level.
        
        Returns theories from past failures that agents can learn from.
        Uses position_death_patterns as the single source of truth.
        """
        try:
            game_type = game_id.split('-')[0] if '-' in game_id else game_id
            
            # Query position_death_patterns (single source of truth)
            patterns = self.db.execute_query("""
                SELECT pattern_id, fatal_action, death_count, danger_score,
                       bucket_x, bucket_y, bucket_size
                FROM position_death_patterns
                WHERE game_type = ? AND level_number = ? AND is_active = 1
                ORDER BY death_count DESC, danger_score DESC
                LIMIT ?
            """, (game_type, level_number, limit))
            
            theories = []
            for pattern in (patterns or []):
                bucket_x = pattern.get('bucket_x', 0)
                bucket_y = pattern.get('bucket_y', 0)
                bucket_size = pattern.get('bucket_size', 8)
                position_str = f"near ({bucket_x * bucket_size}, {bucket_y * bucket_size})"
                
                theories.append({
                    'pattern_id': pattern['pattern_id'],
                    'fatal_action': pattern['fatal_action'],
                    'confirmed_deaths': pattern['death_count'],
                    'confidence': pattern['danger_score'],
                    'pre_death_sequence': [],  # Not tracked in position_death_patterns
                    'theory': f"ACTION{pattern['fatal_action']} caused {pattern['death_count']} deaths at level {level_number} {position_str}",
                    'avoidance_strategy': f"Avoid ACTION{pattern['fatal_action']} {position_str}"
                })
            
            return theories
            
        except Exception as e:
            logger.debug(f"Failed to get game-over theories: {e}")
            return []
