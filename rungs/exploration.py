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

    def _avoid_tried_positions(
        self, coords: Dict[str, int], context: Dict[str, Any], max_attempts: int = 10
    ) -> Dict[str, int]:
        """Part 7.2: During learning phase, avoid re-clicking previously tried positions.

        Reads the world_model action_history to find positions already clicked,
        then picks a different random position if the proposed one was already tried.
        Falls back to the original coords if no novel position can be found.
        """
        wm = context.get('world_model') or {}
        history = wm.get('action_history', [])
        tried_positions: set = set()
        for entry in history[-30:]:
            if isinstance(entry, dict) and 'x' in entry and 'y' in entry:
                tried_positions.add((entry['x'], entry['y']))

        if not tried_positions:
            return coords

        # If proposed position already tried, try to find a novel one
        proposed = (coords.get('x', 32), coords.get('y', 32))
        if proposed not in tried_positions:
            return coords

        for _ in range(max_attempts):
            x = random.randint(4, 60)
            y = random.randint(4, 60)
            if (x, y) not in tried_positions:
                return {'x': x, 'y': y}

        # Couldn't find novel position; return original
        return coords

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        try:
            # Part 7.2: Level-aware strategy - learning phases use exploration,
            # applying phases use exploitation, otherwise use fallback_strategy
            level_phase = context.get('level_phase', '')
            if level_phase == 'learning':
                strategy = 'exploration'
            elif level_phase == 'applying':
                strategy = 'exploitation'
            else:
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
                    metadata: Dict[str, Any] = {'strategy': strategy, 'level_phase': level_phase}
                    if action == 'ACTION6':
                        coords = self._get_action6_coordinates()
                        # Part 7.2: During learning phase, avoid re-clicking same positions
                        if level_phase == 'learning':
                            coords = self._avoid_tried_positions(coords, context)
                        metadata.update(coords)
                    return RungResult(
                        action=action,
                        confidence=0.1,
                        reason=f"Fallback ({strategy}): {action}",
                        weights=weights,
                        metadata=metadata
                    )

            fallback_action = get_random_available_action(context)
            # Add coordinates if ACTION6
            metadata = {'strategy': 'ultimate_fallback', 'level_phase': level_phase}
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

    ANTI-MONOPOLY (2026-02-10):
    Per-game evaluation counter decays confidence by 0.02 per evaluate() call,
    regardless of coordinate diversity. This prevents the rung from holding
    98% of all actions by cycling through objects — after ~15 evaluations,
    confidence drops low enough for exploitation rungs to compete.
    Resets on level change (progress = fresh exploration budget).
    """
    name = "action6_object_exploration"
    category = "exploration"
    default_priority = 38  # Higher priority than GridExplorationRung (47)
    confidence_threshold = 0.35

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._consecutive_no_change = 0
        self._position_history: List[Tuple[int, int]] = []
        self._HISTORY_WINDOW = 8
        # Per-game evaluation counter: decays confidence even when coordinates
        # are diverse (prevents monopoly through object cycling).
        self._game_eval_count: Dict[str, int] = {}
        self._last_game_level: Optional[str] = None

    def _get_repetition_decay(self, x: int, y: int, proximity: int = 4) -> float:
        """
        Calculate confidence decay based on positional repetition.

        Returns a decay value (0.0 = no decay, up to ~0.50 for heavy repetition).
        Positions within ``proximity`` pixels of each other count as repeats.
        """
        if not self._position_history:
            return 0.0

        recent = self._position_history[-6:]
        repeat_count = sum(
            1 for px, py in recent
            if abs(px - x) <= proximity and abs(py - y) <= proximity
        )

        return min(0.50, repeat_count * 0.10)

    def _record_position(self, x: int, y: int) -> None:
        """Record a position in the history."""
        self._position_history.append((x, y))
        if len(self._position_history) > self._HISTORY_WINDOW:
            self._position_history = self._position_history[-self._HISTORY_WINDOW:]

    def _should_abstain(self, x: int, y: int, proximity: int = 4) -> bool:
        """Abstain if last 3+ recorded positions are all near proposed coords.

        This uses position history only -- no dependency on on_action_complete.
        After clicking the same spot 3 times, the rung yields entirely so the
        router's coordinate fallback can try different positions.
        """
        if len(self._position_history) < 3:
            return False
        recent = self._position_history[-3:]
        return all(
            abs(px - x) <= proximity and abs(py - y) <= proximity
            for px, py in recent
        )

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

            # Get current frame from game_state
            frame = None
            if hasattr(game_state, 'frame'):
                frame = game_state.frame
            elif isinstance(game_state, dict):
                frame = game_state.get('frame')

            if frame is None:
                return RungResult()
            # Convert numpy to list for safe iteration
            if hasattr(frame, 'tolist'):
                frame = frame.tolist()
            if not isinstance(frame, list) or len(frame) == 0:
                return RungResult()

            # ANTI-MONOPOLY: Per-game eval counter — decays confidence
            # even when coordinates are diverse (object cycling).
            game_key = f"{game_type}_L{level}"
            eval_count = self._game_eval_count.get(game_key, 0)
            self._game_eval_count[game_key] = eval_count + 1

            # Reset counter on level change (same game, new level = progress)
            if self._last_game_level and self._last_game_level != game_key:
                old_type = self._last_game_level.split('_L')[0]
                if old_type == game_type:
                    self._game_eval_count[game_key] = 0
                    eval_count = 0
            self._last_game_level = game_key

            eval_decay = eval_count * 0.02

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
                    if self._should_abstain(x, y):
                        return RungResult(reason="Abstaining: repeated no-change at same position")
                    base_conf = min(0.50, 0.45 + obj.get('shape_confidence', 0) * 0.15)
                    decay = self._get_repetition_decay(x, y)
                    no_change_decay = self._consecutive_no_change * 0.08
                    confidence = max(0.10, base_conf - decay - no_change_decay - eval_decay)
                    self._record_position(x, y)
                    decay_note = f" [decay={decay:.2f}+nc={no_change_decay:.2f}+ev={eval_decay:.2f}]" if (decay > 0 or no_change_decay > 0 or eval_decay > 0) else ""
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
                            if self._should_abstain(x, y):
                                continue  # Skip this button, try next
                            base_conf = min(0.50, 0.40 + button.get('confidence', 0) * 0.20)
                            decay = self._get_repetition_decay(x, y)
                            no_change_decay = self._consecutive_no_change * 0.08
                            confidence = max(0.10, base_conf - decay - no_change_decay - eval_decay)
                            self._record_position(x, y)
                            decay_note = f" [decay={decay:.2f}+nc={no_change_decay:.2f}+ev={eval_decay:.2f}]" if (decay > 0 or no_change_decay > 0 or eval_decay > 0) else ""
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
                            if self._should_abstain(x, y):
                                return RungResult(reason="Abstaining: repeated no-change at same position")
                            base_conf = min(0.50, 0.35 + obj.get('confidence', 0) * 0.25)
                            decay = self._get_repetition_decay(x, y)
                            no_change_decay = self._consecutive_no_change * 0.08
                            confidence = max(0.10, base_conf - decay - no_change_decay - eval_decay)
                            self._record_position(x, y)
                            decay_note = f" [decay={decay:.2f}+nc={no_change_decay:.2f}+ev={eval_decay:.2f}]" if (decay > 0 or no_change_decay > 0 or eval_decay > 0) else ""
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

    def on_action_complete(self, action: str,
                           action_data: Any = None,
                           frame_before: Any = None,
                           frame_after: Any = None,
                           context: Any = None,
                           **kwargs: Any) -> None:
        """Track whether actions produce frame changes.

        Signature must match DecisionRungSystem.notify_action_complete caller:
            action, action_data, frame_before, frame_after, context
        """
        try:
            if frame_before is not None and frame_after is not None:
                import numpy as np
                pre = np.array(frame_before) if not isinstance(frame_before, np.ndarray) else frame_before
                post = np.array(frame_after) if not isinstance(frame_after, np.ndarray) else frame_after
                if pre.shape == post.shape and np.array_equal(pre, post):
                    self._consecutive_no_change += 1
                else:
                    self._consecutive_no_change = 0
            else:
                # No frame data -- assume no change (conservative)
                self._consecutive_no_change += 1
        except Exception:
            self._consecutive_no_change += 1


# Registry of rungs in this module
RUNGS = {
    'smart_action_selection': SmartActionSelectionRung,
    'action6_object_exploration': Action6ObjectExplorationRung,
}
