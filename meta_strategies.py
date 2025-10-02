#!/usr/bin/env python3
"""
Meta strategies for enhancing coordinate selection based on frame changes and algorithm types.
"""

import random
import math
from typing import Tuple, List, Dict, Optional
from enum import Enum
from dataclasses import dataclass


class MetaStrategy(Enum):
    """Meta strategy types for frame change response."""
    FRAME_AVOID = "frame_avoid"
    FRAME_TARGET = "frame_target"
    ACTION_REPEAT = "action_repeat"
    ACTION_NEARBY = "action_nearby"


@dataclass
class FrameChange:
    """Represents a detected frame change."""
    x: int
    y: int
    old_value: int
    new_value: int
    magnitude: int  # abs(new_value - old_value)


class MetaStrategyEngine:
    """Engine for applying meta strategies to coordinate generation."""

    def __init__(self):
        self.algorithm_strategy_mapping = {
            # Pathfinding algorithms - target changes to explore new areas
            "astar": MetaStrategy.FRAME_TARGET,
            "dijkstra": MetaStrategy.FRAME_TARGET,
            "bfs": MetaStrategy.FRAME_AVOID,  # Systematic exploration avoiding noise
            "dfs": MetaStrategy.FRAME_TARGET,

            # Optimization algorithms - exploit successful patterns
            "gradient_ascent": MetaStrategy.ACTION_NEARBY,
            "gradient_descent": MetaStrategy.ACTION_NEARBY,
            "hill_climbing": MetaStrategy.ACTION_REPEAT,
            "simulated_annealing": MetaStrategy.ACTION_NEARBY,

            # Search algorithms - mix of exploration and exploitation
            "binary_search": MetaStrategy.FRAME_AVOID,
            "quick_sort": MetaStrategy.ACTION_REPEAT,
            "decision_tree": MetaStrategy.FRAME_TARGET,
            "knn": MetaStrategy.ACTION_NEARBY,
            "pagerank": MetaStrategy.FRAME_TARGET,
        }

    def select_meta_strategy(self, algorithm_id: str, context) -> MetaStrategy:
        """Select appropriate meta strategy based on algorithm type."""
        # Extract algorithm base name (remove seed suffix)
        base_algorithm = algorithm_id.lower().replace("_seed_001", "")

        # Check for exact matches first
        for alg_key, strategy in self.algorithm_strategy_mapping.items():
            if alg_key in base_algorithm:
                return strategy

        # Default fallback - use frame targeting for exploration
        return MetaStrategy.FRAME_TARGET

    def detect_frame_changes(self, previous_frame: List[List[int]],
                           current_frame: List[List[int]]) -> List[FrameChange]:
        """Detect changes between two frames."""
        if not previous_frame or not current_frame:
            return []

        if len(previous_frame) != len(current_frame):
            return []

        changes = []
        frame_height = len(current_frame)
        frame_width = len(current_frame[0]) if frame_height > 0 else 0

        for y in range(frame_height):
            if y >= len(previous_frame):
                break

            prev_row = previous_frame[y]
            curr_row = current_frame[y]

            row_width = min(len(prev_row), len(curr_row), frame_width)

            for x in range(row_width):
                old_val = prev_row[x]
                new_val = curr_row[x]

                if old_val != new_val:
                    changes.append(FrameChange(
                        x=x, y=y,
                        old_value=old_val,
                        new_value=new_val,
                        magnitude=abs(new_val - old_val)
                    ))

        return changes

    def apply_meta_strategy(self, strategy: MetaStrategy, base_coordinates: Tuple[int, int],
                          context) -> Tuple[int, int]:
        """Apply meta strategy to modify base coordinates."""

        if strategy == MetaStrategy.FRAME_AVOID:
            return self._apply_frame_avoid(base_coordinates, context)
        elif strategy == MetaStrategy.FRAME_TARGET:
            return self._apply_frame_target(base_coordinates, context)
        elif strategy == MetaStrategy.ACTION_REPEAT:
            return self._apply_action_repeat(base_coordinates, context)
        elif strategy == MetaStrategy.ACTION_NEARBY:
            return self._apply_action_nearby(base_coordinates, context)
        else:
            return base_coordinates

    def _apply_frame_avoid(self, base_coords: Tuple[int, int], context) -> Tuple[int, int]:
        """Avoid areas that recently changed."""
        if not hasattr(context, 'frame_changes') or not context.frame_changes:
            return base_coords

        x, y = base_coords
        avoidance_radius = 8  # Avoid within 8 units of changes

        # Check if base coordinates are too close to frame changes
        for change in context.frame_changes[-10:]:  # Consider last 10 changes
            # Scale frame coordinates to ACTION6 space (0-63)
            if hasattr(context, 'frame') and context.frame:
                frame_height = len(context.frame)
                frame_width = len(context.frame[0]) if frame_height > 0 else 0

                if frame_width > 0 and frame_height > 0:
                    scaled_x = int((change.x / frame_width) * 63)
                    scaled_y = int((change.y / frame_height) * 63)

                    distance = math.sqrt((x - scaled_x)**2 + (y - scaled_y)**2)

                    if distance < avoidance_radius:
                        # Move away from the change
                        angle = math.atan2(y - scaled_y, x - scaled_x)
                        x = scaled_x + int(avoidance_radius * math.cos(angle))
                        y = scaled_y + int(avoidance_radius * math.sin(angle))

                        # Clamp to bounds
                        x = min(max(x, 0), 63)
                        y = min(max(y, 0), 63)
                        break

        return x, y

    def _apply_frame_target(self, base_coords: Tuple[int, int], context) -> Tuple[int, int]:
        """Target areas near recent frame changes."""
        if not hasattr(context, 'frame_changes') or not context.frame_changes:
            return base_coords

        # Find the most recent significant change
        recent_changes = context.frame_changes[-5:]  # Last 5 changes
        if not recent_changes:
            return base_coords

        # Select change with highest magnitude
        target_change = max(recent_changes, key=lambda c: c.magnitude)

        # Scale frame coordinates to ACTION6 space
        if hasattr(context, 'frame') and context.frame:
            frame_height = len(context.frame)
            frame_width = len(context.frame[0]) if frame_height > 0 else 0

            if frame_width > 0 and frame_height > 0:
                scaled_x = int((target_change.x / frame_width) * 63)
                scaled_y = int((target_change.y / frame_height) * 63)

                # Add small random variation around the target
                variation = 4
                x = scaled_x + random.randint(-variation, variation)
                y = scaled_y + random.randint(-variation, variation)

                # Clamp to bounds
                x = min(max(x, 0), 63)
                y = min(max(y, 0), 63)

                return x, y

        return base_coords

    def _apply_action_repeat(self, base_coords: Tuple[int, int], context) -> Tuple[int, int]:
        """Repeat the exact same action that previously caused frame change."""
        if (hasattr(context, 'last_successful_coordinates') and
            context.last_successful_coordinates):
            return context.last_successful_coordinates

        return base_coords

    def _apply_action_nearby(self, base_coords: Tuple[int, int], context) -> Tuple[int, int]:
        """Try coordinates near previously successful actions."""
        if (hasattr(context, 'successful_actions') and
            context.successful_actions and len(context.successful_actions) > 0):

            # Get the most recent successful action
            last_success = context.successful_actions[-1]
            if 'coordinates' in last_success:
                base_x, base_y = last_success['coordinates']

                # Generate coordinates within small radius of last success
                radius = 6  # 6-unit radius for local optimization
                offset_x = random.randint(-radius, radius)
                offset_y = random.randint(-radius, radius)

                x = base_x + offset_x
                y = base_y + offset_y

                # Clamp to bounds
                x = min(max(x, 0), 63)
                y = min(max(y, 0), 63)

                return x, y

        return base_coords


# Global instance for easy access
meta_strategy_engine = MetaStrategyEngine()