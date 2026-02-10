"""
Exploration & Fallback Rungs - Systematic search and defaults
=============================================================
Extracted from decision_rung_system.py Phase 4.2.
"""

import logging
import random
from typing import Any, Dict, List, Optional, Tuple

from rungs.base import (
    Action6CoordinateProvider,
    DecisionRung,
    KnowledgeProvenance,
    RungResult,
    filter_available_actions,
    get_available_action_weights,
    get_available_actions_list,
    get_random_available_action,
    is_action_available,
    validate_action,
)

logger = logging.getLogger(__name__)


class SmartActionSelectionRung(DecisionRung):
    """Fallback: strategy-based random selection - FALLBACK"""
    name = "smart_action_selection"
    category = "fallback"
    default_priority = 99  # Always last
    confidence_threshold = 0.0  # Always provides answer

    def _get_action6_coordinates(self) -> Dict[str, int]:
        """Get coordinates for ACTION6 from visual_analyzer or random fallback."""
        va = self.engines.visual_analyzer if self.engines else None
        if va and hasattr(va, 'get_grid_exploration_targets'):
            targets = va.get_grid_exploration_targets()
            if targets:
                target = targets[0]
                return {'x': target.get('x', 32), 'y': target.get('y', 32), 'grid_target': target}
        # Fallback: random position
        return {'x': random.randint(4, 60), 'y': random.randint(4, 60)}

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        try:
            strategy = context.get('fallback_strategy', 'balanced')
            available = context.get('available_actions', [1, 2, 3, 4, 5, 6, 7])
            available_strs = {f'ACTION{a}' for a in available}

            if strategy == 'exploration':
                all_weights = {'ACTION1': 1.2, 'ACTION2': 1.2, 'ACTION3': 1.2, 'ACTION4': 1.2,
                          'ACTION5': 0.5, 'ACTION6': 1.0, 'ACTION7': 0.3}
            elif strategy == 'exploitation':
                all_weights = {'ACTION1': 0.8, 'ACTION2': 0.8, 'ACTION3': 0.8, 'ACTION4': 0.8,
                          'ACTION5': 1.5, 'ACTION6': 1.2, 'ACTION7': 1.0}
            else:  # balanced
                all_weights = get_available_action_weights(context, 1.0)

            # Filter to only available actions
            weights = {k: v for k, v in all_weights.items() if k in available_strs}
            if not weights:
                weights = get_available_action_weights(context, 1.0)

            # Weighted random choice
            total = sum(weights.values())
            r = random.random() * total
            cumulative = 0
            for action, weight in weights.items():
                cumulative += weight
                if r <= cumulative:
                    # Add coordinates if ACTION6
                    metadata: Dict[str, Any] = {'strategy': strategy}
                    if action == 'ACTION6':
                        metadata.update(self._get_action6_coordinates())
                    return RungResult(
                        action=action,
                        confidence=0.1,
                        reason=f"Fallback ({strategy}): {action}",
                        weights=weights,
                        metadata=metadata
                    )

            fallback_action = get_random_available_action(context)
            # Add coordinates if ACTION6
            metadata = {'strategy': 'ultimate_fallback'}
            if fallback_action == 'ACTION6':
                metadata.update(self._get_action6_coordinates())
            return RungResult(action=fallback_action, confidence=0.1, reason="Ultimate fallback", metadata=metadata)
        except Exception as e:
            fallback_action = get_random_available_action(context)
            metadata = {'error': str(e)}
            if fallback_action == 'ACTION6':
                metadata.update({'x': random.randint(4, 60), 'y': random.randint(4, 60)})
            return RungResult(action=fallback_action, confidence=0.1, reason=f"Fallback error: {e}", metadata=metadata)


class Action6ObjectExplorationRung(DecisionRung):
    """
    Use Action6BehaviorEngine to find clickable objects - EXPLORATION

    This rung uses the sophisticated pseudobutton/object selection system to:
    1. Find objects in the current frame that match known selectable shapes
    2. Prioritize unexplored objects for frontier exploration
    3. Return specific click coordinates for ACTION6

    This is critical for ACTION6-only games like vc33.

    CONFIDENCE DECAY (2025-01-13):
    Tracks recent (x,y) positions per game. When the same coordinates are
    produced repeatedly, confidence decays so the cognitive router yields
    to other rungs instead of committing to stale exploration.
    """
    name = "action6_object_exploration"
    category = "exploration"
    default_priority = 38  # Higher priority than GridExplorationRung (47)
    confidence_threshold = 0.35

    # Class-level position history: game_key -> list of recent (x, y)
    _position_history: Dict[str, List[Tuple[int, int]]] = {}
    _HISTORY_WINDOW = 8  # Track last 8 positions per game

    @classmethod
    def _get_repetition_decay(cls, game_key: str, x: int, y: int, proximity: int = 4) -> float:
        """
        Calculate confidence decay based on positional repetition.

        Returns a decay value (0.0 = no decay, up to ~0.50 for heavy repetition).
        Positions within ``proximity`` pixels of each other count as repeats.
        """
        history = cls._position_history.get(game_key, [])
        if not history:
            return 0.0

        # Count how many of the last N positions are near (x, y)
        recent = history[-6:]  # Check last 6 positions
        repeat_count = sum(
            1 for px, py in recent
            if abs(px - x) <= proximity and abs(py - y) <= proximity
        )

        # 0.10 decay per repeat, so 5 repeats -> 0.50 decay (drops below commit threshold)
        return min(0.50, repeat_count * 0.10)

    @classmethod
    def _record_position(cls, game_key: str, x: int, y: int) -> None:
        """Record a position in the history for this game."""
        if game_key not in cls._position_history:
            cls._position_history[game_key] = []
        cls._position_history[game_key].append((x, y))
        # Trim to window size
        if len(cls._position_history[game_key]) > cls._HISTORY_WINDOW:
            cls._position_history[game_key] = cls._position_history[game_key][-cls._HISTORY_WINDOW:]

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        # Check if ACTION6 is available
        available = context.get('available_actions', [1, 2, 3, 4, 5, 6, 7])
        if 6 not in available:
            return RungResult()

        # Get the action6_behavior engine
        a6e = self.engines.action6_behavior
        if a6e is None:
            return RungResult()

        try:
            game_type = context.get('game_type', '')
            level = context.get('level', 1)
            game_key = f"{game_type}_L{level}"

            # Get current frame from game_state
            frame = None
            if hasattr(game_state, 'frame'):
                frame = game_state.frame
            elif isinstance(game_state, dict):
                frame = game_state.get('frame')

            if not frame:
                return RungResult()

            # First try: Get objects matching known selectable shapes for this game
            if hasattr(a6e, 'get_untried_objects_for_frontier'):
                tried_colors = context.get('tried_colors', [])
                objects = a6e.get_untried_objects_for_frontier(
                    game_type=game_type,
                    level=level,
                    frame=frame,
                    tried_colors=tried_colors
                )
                if objects:
                    obj = objects[0]  # Highest confidence match
                    # Get center coordinates of the object
                    x = obj.get('center_x', obj.get('x', 32))
                    y = obj.get('center_y', obj.get('y', 32))
                    base_conf = 0.55 + (obj.get('shape_confidence', 0) * 0.2)
                    decay = self._get_repetition_decay(game_key, x, y)
                    confidence = max(0.10, base_conf - decay)
                    self._record_position(game_key, x, y)
                    decay_note = f" [decay={decay:.2f}]" if decay > 0 else ""
                    return RungResult(
                        action='ACTION6',
                        confidence=confidence,
                        reason=f"Object exploration: color={obj.get('color')} shape={obj.get('shape_signature')} at ({x},{y}){decay_note}",
                        metadata={
                            'x': x,
                            'y': y,
                            'target_object': obj,
                            'source': 'shape_matching',
                            'repetition_decay': decay
                        }
                    )

            # Second try: Get known pseudo-buttons for this game/level
            if hasattr(a6e, 'get_all_pseudo_buttons'):
                buttons = a6e.get_all_pseudo_buttons(game_type, level)
                if buttons:
                    # Find highest-confidence button that produces useful action
                    for button in buttons:
                        if button.get('confidence', 0) >= 0.5:
                            # Region coords are 0-7, convert to pixel coords (center of 8x8 region)
                            region_x = button.get('region_x', 4)
                            region_y = button.get('region_y', 4)
                            x = region_x * 8 + 4  # Center of region
                            y = region_y * 8 + 4
                            base_conf = 0.50 + button.get('confidence', 0) * 0.3
                            decay = self._get_repetition_decay(game_key, x, y)
                            confidence = max(0.10, base_conf - decay)
                            self._record_position(game_key, x, y)
                            decay_note = f" [decay={decay:.2f}]" if decay > 0 else ""
                            return RungResult(
                                action='ACTION6',
                                confidence=confidence,
                                reason=f"Pseudo-button at region ({region_x},{region_y}) -> ({x},{y}){decay_note}",
                                metadata={
                                    'x': x,
                                    'y': y,
                                    'pseudo_button': button,
                                    'source': 'pseudo_button',
                                    'repetition_decay': decay
                                }
                            )

            # Third try: Get selectable objects from network knowledge
            if hasattr(a6e, 'get_selectable_objects'):
                objects = a6e.get_selectable_objects(game_type, level, min_confidence=0.4)
                if objects:
                    obj = objects[0]
                    coords = obj.get('coordinates', '')
                    # Parse coordinates like "(32,45)"
                    if coords:
                        import re
                        match = re.match(r'\((\d+),(\d+)\)', coords)
                        if match:
                            x, y = int(match.group(1)), int(match.group(2))
                            base_conf = 0.45 + obj.get('confidence', 0) * 0.3
                            decay = self._get_repetition_decay(game_key, x, y)
                            confidence = max(0.10, base_conf - decay)
                            self._record_position(game_key, x, y)
                            decay_note = f" [decay={decay:.2f}]" if decay > 0 else ""
                            return RungResult(
                                action='ACTION6',
                                confidence=confidence,
                                reason=f"Selectable object color={obj.get('object_color')} at ({x},{y}){decay_note}",
                                metadata={
                                    'x': x,
                                    'y': y,
                                    'selectable_object': obj,
                                    'source': 'network_knowledge',
                                    'repetition_decay': decay
                                }
                            )

            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Action6 object exploration failed: {e}")



# Registry of rungs in this module
RUNGS = {
    'smart_action_selection': SmartActionSelectionRung,
    'action6_object_exploration': Action6ObjectExplorationRung,
}
