"""
Emergency Rungs - Hard safety constraints
=========================================
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


def _get_frame(game_state: Any) -> Any:
    """Extract frame from game_state whether it's a dict or object."""
    if isinstance(game_state, dict):
        return game_state.get('frame')
    return getattr(game_state, 'frame', None)


class InfiniteLoopBreakerRung(DecisionRung):
    """Emergency escape from stuck loops - EMERGENCY"""
    name = "infinite_loop_breaker"
    category = "emergency"
    default_priority = 1  # Highest priority when triggered
    confidence_threshold = 0.9

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        try:
            stuck_count = context.get('recent_stuck_count', 0)

            if stuck_count >= 15:
                # Emergency! Prefer movement actions (ACTION1-4) that haven't
                # already failed, since random ACTION6 clicks rarely unstick
                # the game and can create a self-reinforcing emergency loop.
                available = context.get('available_actions', [1, 2, 3, 4])
                failed = context.get('failed_actions', set())
                failed_nums = {int(a.replace('ACTION', '')) for a in failed if isinstance(a, str) and a.startswith('ACTION')}

                # Priority 1: untried movement actions
                movement = [a for a in available if a in (1, 2, 3, 4) and a not in failed_nums]
                if movement:
                    action = f'ACTION{random.choice(movement)}'
                # Priority 2: any untried action
                elif [a for a in available if a not in failed_nums]:
                    action = f'ACTION{random.choice([a for a in available if a not in failed_nums])}'
                # Priority 3: true last resort - anything available
                else:
                    action = get_random_available_action(context)

                return RungResult(
                    action=action,
                    confidence=0.95,
                    reason=f"EMERGENCY: Breaking infinite loop (stuck {stuck_count})",
                    metadata={'stuck_count': stuck_count, 'emergency': True}
                )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Loop breaker failed: {e}")


class CoordinateOscillationRung(DecisionRung):
    """Detect bouncing between coordinates and break loop - EMERGENCY"""
    name = "coordinate_oscillation"
    category = "emergency"
    default_priority = 3
    confidence_threshold = 0.8

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        ah = self.engines.action_handler
        if ah is None:
            return RungResult()

        try:
            if hasattr(ah, 'detect_oscillation'):
                oscillation = ah.detect_oscillation()
                if oscillation.get('oscillation_detected', False):
                    coords = oscillation.get('oscillating_coords', [])
                    if len(coords) >= 2:
                        available_list = get_available_actions_list(context)

                        # H33: For ACTION6-only games (click puzzles), pick a
                        # random unexplored coordinate instead of a different
                        # action type. The oscillation is in POSITION, not action.
                        if available_list == ['ACTION6'] or available_list == [6]:
                            frame = _get_frame(game_state)
                            if frame is not None:
                                osc_set = set()
                                for c in coords:
                                    if isinstance(c, (list, tuple)) and len(c) >= 2:
                                        osc_set.add((c[0], c[1]))
                                # Pick a random non-zero pixel NOT in oscillating set
                                candidates = []
                                try:
                                    raw = frame
                                    if hasattr(raw, 'tolist'):
                                        raw = raw.tolist()
                                    if isinstance(raw, list) and raw:
                                        while isinstance(raw[0], list) and isinstance(raw[0][0], list):
                                            raw = raw[0]
                                        for y, row in enumerate(raw):
                                            for x, val in enumerate(row):
                                                v = int(val) if hasattr(val, '__int__') else val
                                                if v > 0 and (x, y) not in osc_set:
                                                    candidates.append((x, y))
                                except Exception:
                                    pass
                                if candidates:
                                    cx, cy = random.choice(candidates)
                                    return RungResult(
                                        action='ACTION6',
                                        confidence=0.85,
                                        reason=f"H33: Breaking click oscillation, trying ({cx},{cy})",
                                        metadata={'x': cx, 'y': cy, 'oscillation': oscillation},
                                    )

                        # Original: try a different action type
                        current_action = context.get('last_action', 'ACTION1')
                        alternatives = [a for a in available_list if a != current_action]
                        if alternatives:
                            return RungResult(
                                action=random.choice(alternatives),
                                confidence=0.85,
                                reason=f"Breaking oscillation between {len(coords)} coords",
                                metadata={'oscillation': oscillation}
                            )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Coordinate oscillation failed: {e}")



# Registry of rungs in this module
RUNGS = {
    'infinite_loop_breaker': InfiniteLoopBreakerRung,
    'coordinate_oscillation': CoordinateOscillationRung,
}
