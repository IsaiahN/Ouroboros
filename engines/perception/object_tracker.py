"""
Object Tracker - Track object identity across frame transitions.

This module provides the foundation for event understanding by matching
objects between before/after frames even when they've moved significantly.

Uses scipy.ndimage.label() for connected component analysis and the
Hungarian algorithm for optimal object matching.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    from scipy import ndimage
    from scipy.optimize import linear_sum_assignment
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


@dataclass
class TrackedObject:
    """An object tracked across frames."""
    object_id: str  # Stable ID across frames
    color: int
    position_before: Optional[Tuple[float, float]]  # Centroid (y, x)
    position_after: Optional[Tuple[float, float]]  # Centroid (y, x)
    movement_vector: Tuple[float, float] = (0.0, 0.0)  # (dy, dx)
    size_before: int = 0
    size_after: int = 0
    still_exists: bool = True
    is_new: bool = False
    shape_signature: str = ""  # For shape matching


@dataclass
class SegmentedObject:
    """An object segmented from a single frame."""
    color: int
    centroid: Tuple[float, float]  # (y, x)
    size: int  # Number of pixels
    positions: np.ndarray  # Array of (y, x) positions
    bounding_box: Tuple[int, int, int, int]  # (min_y, min_x, max_y, max_x)
    shape_signature: str = ""


class ObjectTracker:
    """
    Track object identity across frame transitions.

    Uses connected component analysis to segment objects and the Hungarian
    algorithm to optimally match objects between frames based on color,
    position, and shape similarity.
    """

    def __init__(
        self,
        color_mismatch_penalty: float = 1000.0,
        max_match_distance: float = 50.0,
        min_object_size: int = 4,
    ):
        """
        Initialize the object tracker.

        Args:
            color_mismatch_penalty: Cost penalty for matching objects of different colors
            max_match_distance: Maximum distance for considering a match
            min_object_size: Minimum pixels for an object to be tracked
        """
        self.color_mismatch_penalty = color_mismatch_penalty
        self.max_match_distance = max_match_distance
        self.min_object_size = min_object_size
        self._object_counter = 0

    def track_objects(
        self,
        frame_before: np.ndarray,
        frame_after: np.ndarray,
    ) -> List[TrackedObject]:
        """
        Match objects between frames.

        Args:
            frame_before: Frame before action (64x64 int8 grid)
            frame_after: Frame after action (64x64 int8 grid)

        Returns:
            List of TrackedObject with movement and lifecycle data
        """
        if not SCIPY_AVAILABLE:
            return []

        # Segment objects in both frames
        objects_before = self._segment_objects(frame_before)
        objects_after = self._segment_objects(frame_after)

        if not objects_before and not objects_after:
            return []

        # Match objects between frames
        matches, unmatched_before, unmatched_after = self._match_objects(
            objects_before, objects_after
        )

        # Build tracked objects
        return self._build_tracked_objects(
            objects_before, objects_after,
            matches, unmatched_before, unmatched_after
        )

    def _segment_objects(self, frame: np.ndarray) -> List[SegmentedObject]:
        """
        Find distinct objects in frame using connected components.

        Uses scipy.ndimage.label() for efficient connected component analysis.
        Processes each color separately to maintain color identity.
        """
        if not SCIPY_AVAILABLE:
            return []

        objects = []

        # Process each ARC color (0-12)
        for color in range(13):
            mask = (frame == color).astype(np.uint8)

            # Skip if no pixels of this color
            if not mask.any():
                continue

            # Find connected components
            # ndimage.label returns (labeled_array, num_features) tuple
            result = ndimage.label(mask)
            labeled, num_features = result[0], result[1]

            for i in range(1, num_features + 1):
                positions = np.argwhere(labeled == i)

                if len(positions) < self.min_object_size:
                    continue

                # Calculate centroid
                centroid = tuple(positions.mean(axis=0))

                # Calculate bounding box
                min_y, min_x = positions.min(axis=0)
                max_y, max_x = positions.max(axis=0)

                # Calculate shape signature (simple hash of relative positions)
                shape_sig = self._compute_shape_signature(positions, centroid)

                objects.append(SegmentedObject(
                    color=color,
                    centroid=centroid,
                    size=len(positions),
                    positions=positions,
                    bounding_box=(min_y, min_x, max_y, max_x),
                    shape_signature=shape_sig
                ))

        return objects

    def _compute_shape_signature(
        self,
        positions: np.ndarray,
        centroid: Tuple[float, float]
    ) -> str:
        """
        Compute a simple shape signature for object matching.

        Uses relative positions from centroid, quantized to reduce noise.
        """
        if len(positions) == 0:
            return ""

        # Get relative positions from centroid
        relative = positions - np.array(centroid)

        # Quantize to reduce noise (round to nearest 2 pixels)
        quantized = (relative / 2).astype(int)

        # Sort for consistent ordering
        sorted_pos = sorted([tuple(p) for p in quantized])

        # Create hash string
        return str(hash(tuple(sorted_pos)))[:8]

    def _match_objects(
        self,
        objects_before: List[SegmentedObject],
        objects_after: List[SegmentedObject],
    ) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        """
        Match objects between frames using Hungarian algorithm.

        Returns:
            matches: List of (before_idx, after_idx) pairs
            unmatched_before: Indices of objects that disappeared
            unmatched_after: Indices of new objects
        """
        if not objects_before or not objects_after:
            return (
                [],
                list(range(len(objects_before))),
                list(range(len(objects_after)))
            )

        n_before = len(objects_before)
        n_after = len(objects_after)

        # Build cost matrix
        cost_matrix = np.full((n_before, n_after), np.inf)

        for i, obj_before in enumerate(objects_before):
            for j, obj_after in enumerate(objects_after):
                cost = self._compute_match_cost(obj_before, obj_after)
                cost_matrix[i, j] = cost

        # Solve assignment problem
        row_indices, col_indices = linear_sum_assignment(cost_matrix)

        # Filter out high-cost matches
        matches = []
        matched_before = set()
        matched_after = set()

        for i, j in zip(row_indices, col_indices):
            if cost_matrix[i, j] < self.max_match_distance + self.color_mismatch_penalty:
                matches.append((i, j))
                matched_before.add(i)
                matched_after.add(j)

        unmatched_before = [i for i in range(n_before) if i not in matched_before]
        unmatched_after = [j for j in range(n_after) if j not in matched_after]

        return matches, unmatched_before, unmatched_after

    def _compute_match_cost(
        self,
        obj_before: SegmentedObject,
        obj_after: SegmentedObject,
    ) -> float:
        """
        Compute cost of matching two objects.

        Cost is based on:
        1. Euclidean distance between centroids
        2. Color mismatch penalty
        3. Size difference (minor factor)
        """
        # Distance between centroids
        dist = np.sqrt(
            (obj_before.centroid[0] - obj_after.centroid[0]) ** 2 +
            (obj_before.centroid[1] - obj_after.centroid[1]) ** 2
        )

        # Color mismatch penalty
        color_penalty = 0.0 if obj_before.color == obj_after.color else self.color_mismatch_penalty

        # Size difference (normalized)
        size_diff = abs(obj_before.size - obj_after.size) / max(obj_before.size, obj_after.size, 1)
        size_penalty = size_diff * 10  # Minor factor

        return dist + color_penalty + size_penalty

    def _build_tracked_objects(
        self,
        objects_before: List[SegmentedObject],
        objects_after: List[SegmentedObject],
        matches: List[Tuple[int, int]],
        unmatched_before: List[int],
        unmatched_after: List[int],
    ) -> List[TrackedObject]:
        """
        Build TrackedObject list from matching results.
        """
        tracked = []

        # Matched objects (existed before and after)
        for before_idx, after_idx in matches:
            obj_before = objects_before[before_idx]
            obj_after = objects_after[after_idx]

            movement = (
                obj_after.centroid[0] - obj_before.centroid[0],
                obj_after.centroid[1] - obj_before.centroid[1]
            )

            tracked.append(TrackedObject(
                object_id=self._generate_object_id(),
                color=obj_before.color,
                position_before=obj_before.centroid,
                position_after=obj_after.centroid,
                movement_vector=movement,
                size_before=obj_before.size,
                size_after=obj_after.size,
                still_exists=True,
                is_new=False,
                shape_signature=obj_before.shape_signature
            ))

        # Disappeared objects
        for before_idx in unmatched_before:
            obj_before = objects_before[before_idx]
            tracked.append(TrackedObject(
                object_id=self._generate_object_id(),
                color=obj_before.color,
                position_before=obj_before.centroid,
                position_after=None,
                movement_vector=(0.0, 0.0),
                size_before=obj_before.size,
                size_after=0,
                still_exists=False,
                is_new=False,
                shape_signature=obj_before.shape_signature
            ))

        # New objects
        for after_idx in unmatched_after:
            obj_after = objects_after[after_idx]
            tracked.append(TrackedObject(
                object_id=self._generate_object_id(),
                color=obj_after.color,
                position_before=None,
                position_after=obj_after.centroid,
                movement_vector=(0.0, 0.0),
                size_before=0,
                size_after=obj_after.size,
                still_exists=True,
                is_new=True,
                shape_signature=obj_after.shape_signature
            ))

        return tracked

    def _generate_object_id(self) -> str:
        """Generate a unique object ID."""
        self._object_counter += 1
        return f"obj_{self._object_counter}"

    def get_movement_summary(
        self,
        tracked_objects: List[TrackedObject]
    ) -> Dict[str, Any]:
        """
        Get summary statistics about object movements.
        """
        movements = [obj for obj in tracked_objects if obj.movement_vector != (0.0, 0.0)]
        disappeared = [obj for obj in tracked_objects if not obj.still_exists]
        created = [obj for obj in tracked_objects if obj.is_new]

        avg_movement = (0.0, 0.0)
        if movements:
            avg_dy = sum(m.movement_vector[0] for m in movements) / len(movements)
            avg_dx = sum(m.movement_vector[1] for m in movements) / len(movements)
            avg_movement = (avg_dy, avg_dx)

        return {
            'total_objects': len(tracked_objects),
            'moved_count': len(movements),
            'disappeared_count': len(disappeared),
            'created_count': len(created),
            'average_movement': avg_movement,
            'movements_aligned': self._check_movements_aligned(movements),
        }

    def _check_movements_aligned(
        self,
        movements: List[TrackedObject],
        angle_threshold: float = 30.0
    ) -> bool:
        """
        Check if movements are roughly aligned (physics signature).
        """
        if len(movements) < 2:
            return False

        # Get movement angles
        angles = []
        for m in movements:
            dy, dx = m.movement_vector
            if dy != 0 or dx != 0:
                angle = np.arctan2(dy, dx) * 180 / np.pi
                angles.append(angle)

        if len(angles) < 2:
            return False

        # Check if angles are within threshold of each other
        for i in range(len(angles)):
            for j in range(i + 1, len(angles)):
                diff = abs(angles[i] - angles[j])
                diff = min(diff, 360 - diff)  # Handle wraparound
                if diff > angle_threshold:
                    return False

        return True


# Module-level convenience function
def track_objects_between_frames(
    frame_before: np.ndarray,
    frame_after: np.ndarray,
) -> List[TrackedObject]:
    """
    Convenience function to track objects between two frames.

    Args:
        frame_before: Frame before action
        frame_after: Frame after action

    Returns:
        List of TrackedObject with movement data
    """
    tracker = ObjectTracker()
    return tracker.track_objects(frame_before, frame_after)
