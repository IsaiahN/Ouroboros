"""
Event Detector - Detect discrete events from object tracking data.

This module identifies discrete events (MOVEMENT, COLLISION, FUSION, etc.)
from object tracking data and performs causal attribution to link events
to actions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from engines.perception.object_tracker import ObjectTracker, TrackedObject


class EventType(Enum):
    """Types of events that can be detected between frames."""
    MOVEMENT = "MOVEMENT"           # Object position changed
    COLLISION = "COLLISION"         # Two objects converged
    FUSION = "FUSION"              # Two objects merged into one
    DESTRUCTION = "DESTRUCTION"     # Object disappeared
    CREATION = "CREATION"          # New object appeared
    TRANSFORMATION = "TRANSFORMATION"  # Object changed in place
    COLLECTION = "COLLECTION"      # Object collected at goal
    SPLIT = "SPLIT"                # One object became multiple


class ProcessType(Enum):
    """Types of processes that can occur."""
    PHYSICS_SIMULATION = "PHYSICS_SIMULATION"   # Multiple objects moved, settled
    ANIMATION_SEQUENCE = "ANIMATION_SEQUENCE"   # Single object state changes
    TRANSFORMATION = "TRANSFORMATION"           # Objects changed on contact
    CHAIN_REACTION = "CHAIN_REACTION"          # Event triggered other events
    DIRECT_CONTROL = "DIRECT_CONTROL"          # Object moved as action specified


@dataclass
class DetectedEvent:
    """A discrete event detected between frames."""
    event_type: EventType
    objects_involved: List[str]  # Object IDs
    positions: List[Tuple[float, float]]  # Relevant positions (y, x)
    timestamp: int  # Action number
    confidence: float
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for database storage."""
        return {
            'event_type': self.event_type.value,
            'objects_involved': self.objects_involved,
            'positions': self.positions,
            'timestamp': self.timestamp,
            'confidence': self.confidence,
            'details': self.details
        }


@dataclass
class CausalLink:
    """Link between an action and an event."""
    action_name: str
    action_data: Dict[str, Any]  # x, y for clicks, direction for moves
    event: DetectedEvent
    confidence: float
    link_type: str = "direct"  # direct, indirect, coincidental


@dataclass
class ProcessClassification:
    """Classification of the overall process that occurred."""
    process_type: ProcessType
    confidence: float
    description: str
    event_count: int
    supporting_evidence: List[str] = field(default_factory=list)


class EventDetector:
    """
    Detect discrete events from object tracking data.

    Analyzes TrackedObject lists to identify higher-level events like
    collisions, fusions, and chain reactions.
    """

    def __init__(
        self,
        collision_distance_threshold: float = 8.0,
        min_movement_threshold: float = 2.0,
    ):
        """
        Initialize the event detector.

        Args:
            collision_distance_threshold: Max distance to consider as collision
            min_movement_threshold: Min movement to register as MOVEMENT event
        """
        self.collision_distance_threshold = collision_distance_threshold
        self.min_movement_threshold = min_movement_threshold
        self.object_tracker = ObjectTracker()

    def detect_events(
        self,
        tracked_objects: List[TrackedObject],
        frame_before: np.ndarray,
        frame_after: np.ndarray,
        action_number: int = 0,
    ) -> List[DetectedEvent]:
        """
        Analyze tracked objects to identify discrete events.

        Args:
            tracked_objects: Objects tracked between frames
            frame_before: Frame before action
            frame_after: Frame after action
            action_number: Current action count (for timestamp)

        Returns:
            List of detected events
        """
        events = []

        # Detect movement events
        events.extend(self._detect_movements(tracked_objects, action_number))

        # Detect collision events
        events.extend(self._detect_collisions(tracked_objects, action_number))

        # Detect fusion events (collisions where objects merge)
        events.extend(self._detect_fusions(tracked_objects, action_number))

        # Detect lifecycle events (creation/destruction)
        events.extend(self._detect_lifecycle_events(tracked_objects, action_number))

        # Detect transformations (in-place changes)
        events.extend(self._detect_transformations(
            tracked_objects, frame_before, frame_after, action_number
        ))

        return events

    def detect_events_from_frames(
        self,
        frame_before: np.ndarray,
        frame_after: np.ndarray,
        action_number: int = 0,
    ) -> Tuple[List[TrackedObject], List[DetectedEvent]]:
        """
        Convenience method: track objects and detect events in one call.
        """
        tracked_objects = self.object_tracker.track_objects(frame_before, frame_after)
        events = self.detect_events(tracked_objects, frame_before, frame_after, action_number)
        return tracked_objects, events

    def _detect_movements(
        self,
        tracked_objects: List[TrackedObject],
        action_number: int,
    ) -> List[DetectedEvent]:
        """Detect MOVEMENT events."""
        events = []

        for obj in tracked_objects:
            # Check if object moved significantly
            dy, dx = obj.movement_vector
            distance = np.sqrt(dy**2 + dx**2)

            if distance >= self.min_movement_threshold and obj.still_exists:
                events.append(DetectedEvent(
                    event_type=EventType.MOVEMENT,
                    objects_involved=[obj.object_id],
                    positions=[obj.position_before, obj.position_after],
                    timestamp=action_number,
                    confidence=0.9,
                    details={
                        'movement_vector': obj.movement_vector,
                        'distance': distance,
                        'color': obj.color
                    }
                ))

        return events

    def _detect_collisions(
        self,
        tracked_objects: List[TrackedObject],
        action_number: int,
    ) -> List[DetectedEvent]:
        """Detect COLLISION events where objects converged."""
        events = []
        moving_objects = [obj for obj in tracked_objects
                         if obj.movement_vector != (0.0, 0.0) and obj.still_exists]

        # Check pairs of moving objects
        for i, obj1 in enumerate(moving_objects):
            for obj2 in moving_objects[i+1:]:
                if obj1.position_after is None or obj2.position_after is None:
                    continue

                # Distance after movement
                dist_after = self._distance(obj1.position_after, obj2.position_after)

                # Distance before movement
                if obj1.position_before and obj2.position_before:
                    dist_before = self._distance(obj1.position_before, obj2.position_before)
                else:
                    dist_before = float('inf')

                # Objects converged if they got closer and are now close
                if dist_after < self.collision_distance_threshold and dist_after < dist_before:
                    events.append(DetectedEvent(
                        event_type=EventType.COLLISION,
                        objects_involved=[obj1.object_id, obj2.object_id],
                        positions=[obj1.position_after, obj2.position_after],
                        timestamp=action_number,
                        confidence=0.8,
                        details={
                            'distance_before': dist_before,
                            'distance_after': dist_after,
                            'colors': [obj1.color, obj2.color]
                        }
                    ))

        return events

    def _detect_fusions(
        self,
        tracked_objects: List[TrackedObject],
        action_number: int,
    ) -> List[DetectedEvent]:
        """
        Detect FUSION events where objects merged.

        Signature: Multiple objects disappeared, one new object appeared
        at approximately the same location.
        """
        events = []

        disappeared = [obj for obj in tracked_objects if not obj.still_exists]
        created = [obj for obj in tracked_objects if obj.is_new]

        if len(disappeared) >= 2 and len(created) >= 1:
            # Check if created object is near disappeared objects
            for new_obj in created:
                nearby_disappeared = []
                for gone_obj in disappeared:
                    if gone_obj.position_before:
                        dist = self._distance(gone_obj.position_before, new_obj.position_after)
                        if dist < self.collision_distance_threshold * 2:
                            nearby_disappeared.append(gone_obj)

                if len(nearby_disappeared) >= 2:
                    positions = [obj.position_before for obj in nearby_disappeared]
                    positions.append(new_obj.position_after)

                    events.append(DetectedEvent(
                        event_type=EventType.FUSION,
                        objects_involved=[obj.object_id for obj in nearby_disappeared] + [new_obj.object_id],
                        positions=[p for p in positions if p is not None],
                        timestamp=action_number,
                        confidence=0.7,
                        details={
                            'fused_from_colors': [obj.color for obj in nearby_disappeared],
                            'result_color': new_obj.color,
                            'result_size': new_obj.size_after
                        }
                    ))

        return events

    def _detect_lifecycle_events(
        self,
        tracked_objects: List[TrackedObject],
        action_number: int,
    ) -> List[DetectedEvent]:
        """Detect CREATION and DESTRUCTION events."""
        events = []

        for obj in tracked_objects:
            if not obj.still_exists and not obj.is_new:
                # Object was destroyed
                events.append(DetectedEvent(
                    event_type=EventType.DESTRUCTION,
                    objects_involved=[obj.object_id],
                    positions=[obj.position_before] if obj.position_before else [],
                    timestamp=action_number,
                    confidence=0.85,
                    details={
                        'color': obj.color,
                        'size': obj.size_before
                    }
                ))

            elif obj.is_new and obj.still_exists:
                # Object was created (and not part of a fusion)
                events.append(DetectedEvent(
                    event_type=EventType.CREATION,
                    objects_involved=[obj.object_id],
                    positions=[obj.position_after] if obj.position_after else [],
                    timestamp=action_number,
                    confidence=0.85,
                    details={
                        'color': obj.color,
                        'size': obj.size_after
                    }
                ))

        return events

    def _detect_transformations(
        self,
        tracked_objects: List[TrackedObject],
        frame_before: np.ndarray,
        frame_after: np.ndarray,
        action_number: int,
    ) -> List[DetectedEvent]:
        """
        Detect TRANSFORMATION events where object properties changed in place.

        This catches color changes that aren't movement-based.
        """
        events = []

        # Look for stationary objects with size changes
        for obj in tracked_objects:
            if obj.still_exists and not obj.is_new:
                # Object exists in both frames
                dy, dx = obj.movement_vector
                distance = np.sqrt(dy**2 + dx**2)

                # Stationary but size changed significantly
                if distance < self.min_movement_threshold:
                    size_change = abs(obj.size_after - obj.size_before)
                    if size_change > 0 and size_change / max(obj.size_before, 1) > 0.1:
                        events.append(DetectedEvent(
                            event_type=EventType.TRANSFORMATION,
                            objects_involved=[obj.object_id],
                            positions=[obj.position_before, obj.position_after],
                            timestamp=action_number,
                            confidence=0.7,
                            details={
                                'size_before': obj.size_before,
                                'size_after': obj.size_after,
                                'color': obj.color
                            }
                        ))

        return events

    def attribute_causality(
        self,
        action_name: str,
        action_data: Dict[str, Any],
        events: List[DetectedEvent],
        action_history: Optional[List[Tuple[str, Dict, List[DetectedEvent]]]] = None,
    ) -> List[CausalLink]:
        """
        Determine which events were caused by the action.

        Args:
            action_name: Name of the action taken (ACTION1-ACTION7)
            action_data: Action parameters (x, y for clicks)
            events: Events detected after the action
            action_history: Previous (action, data, events) for statistical correlation

        Returns:
            Causal links with confidence scores
        """
        links = []

        for event in events:
            # Temporal proximity (always 1.0 for immediate events)
            temporal_score = 1.0

            # Spatial proximity (for click actions)
            if action_name == 'ACTION6' and 'x' in action_data and 'y' in action_data:
                click_pos = (action_data['y'], action_data['x'])  # Convert to (y, x)
                spatial_score = self._compute_spatial_proximity(click_pos, event.positions)
            else:
                spatial_score = 0.5  # Direction actions affect whole frame

            # Statistical correlation from history
            if action_history:
                stat_score = self._compute_statistical_correlation(
                    action_name, event.event_type, action_history
                )
            else:
                stat_score = 0.5  # No history, neutral score

            # Combined confidence
            confidence = (temporal_score * 0.3 + spatial_score * 0.4 + stat_score * 0.3)

            # Determine link type
            if spatial_score > 0.7:
                link_type = "direct"
            elif confidence > 0.5:
                link_type = "indirect"
            else:
                link_type = "coincidental"

            links.append(CausalLink(
                action_name=action_name,
                action_data=action_data,
                event=event,
                confidence=confidence,
                link_type=link_type
            ))

        return links

    def classify_process(
        self,
        events: List[DetectedEvent],
        _causal_links: Optional[List[CausalLink]] = None,
    ) -> ProcessClassification:
        """
        Classify the overall process that occurred.

        Analyzes event patterns to determine the type of game mechanic.
        """
        if not events:
            return ProcessClassification(
                process_type=ProcessType.DIRECT_CONTROL,
                confidence=0.5,
                description="No events detected",
                event_count=0
            )

        # Count event types
        movement_count = sum(1 for e in events if e.event_type == EventType.MOVEMENT)
        collision_count = sum(1 for e in events if e.event_type == EventType.COLLISION)
        fusion_count = sum(1 for e in events if e.event_type == EventType.FUSION)
        transform_count = sum(1 for e in events if e.event_type == EventType.TRANSFORMATION)

        evidence = []

        # Check for physics signature
        if movement_count >= 3 and self._movements_aligned(events):
            evidence.append(f"{movement_count} aligned movements")
            return ProcessClassification(
                process_type=ProcessType.PHYSICS_SIMULATION,
                confidence=0.8,
                description="Multiple objects moved in consistent direction",
                event_count=len(events),
                supporting_evidence=evidence
            )

        # Check for chain reaction
        if collision_count >= 1 and (fusion_count >= 1 or movement_count >= 3):
            evidence.append(f"{collision_count} collisions, {movement_count} movements")
            return ProcessClassification(
                process_type=ProcessType.CHAIN_REACTION,
                confidence=0.7,
                description="Collision triggered additional events",
                event_count=len(events),
                supporting_evidence=evidence
            )

        # Check for transformation
        if transform_count >= 1:
            evidence.append(f"{transform_count} transformations")
            return ProcessClassification(
                process_type=ProcessType.TRANSFORMATION,
                confidence=0.7,
                description="Objects changed properties in place",
                event_count=len(events),
                supporting_evidence=evidence
            )

        # Check for animation sequence (single object, multiple state changes)
        if movement_count == 1 and len(events) == 1:
            evidence.append("Single object movement")
            return ProcessClassification(
                process_type=ProcessType.DIRECT_CONTROL,
                confidence=0.85,
                description="Object moved exactly as action specified",
                event_count=len(events),
                supporting_evidence=evidence
            )

        # Default
        return ProcessClassification(
            process_type=ProcessType.DIRECT_CONTROL,
            confidence=0.5,
            description="Could not classify process type",
            event_count=len(events),
            supporting_evidence=evidence
        )

    def _movements_aligned(
        self,
        events: List[DetectedEvent],
        angle_threshold: float = 30.0
    ) -> bool:
        """Check if movement events are roughly aligned (physics signature)."""
        movement_events = [e for e in events if e.event_type == EventType.MOVEMENT]

        if len(movement_events) < 2:
            return False

        angles = []
        for e in movement_events:
            vec = e.details.get('movement_vector', (0, 0))
            dy, dx = vec
            if dy != 0 or dx != 0:
                angle = np.arctan2(dy, dx) * 180 / np.pi
                angles.append(angle)

        if len(angles) < 2:
            return False

        # Check if angles are within threshold
        for i in range(len(angles)):
            for j in range(i + 1, len(angles)):
                diff = abs(angles[i] - angles[j])
                diff = min(diff, 360 - diff)
                if diff > angle_threshold:
                    return False

        return True

    def _distance(
        self,
        pos1: Tuple[float, float],
        pos2: Tuple[float, float]
    ) -> float:
        """Euclidean distance between two positions."""
        return np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

    def _compute_spatial_proximity(
        self,
        action_pos: Tuple[float, float],
        event_positions: List[Tuple[float, float]],
    ) -> float:
        """Compute spatial proximity score between action and event."""
        if not event_positions:
            return 0.5

        # Find minimum distance to any event position
        min_dist = min(self._distance(action_pos, pos) for pos in event_positions)

        # Convert distance to 0-1 score (closer = higher)
        # 0 pixels = 1.0, 32 pixels = 0.5, 64+ pixels = ~0.0
        return max(0.0, 1.0 - min_dist / 64.0)

    def _compute_statistical_correlation(
        self,
        action_name: str,
        event_type: EventType,
        action_history: List[Tuple[str, Dict, List[DetectedEvent]]],
    ) -> float:
        """
        Compute how often this action type produces this event type.
        """
        if not action_history:
            return 0.5

        # Count occurrences
        action_count = 0
        event_after_action_count = 0

        for hist_action, hist_data, hist_events in action_history:
            if hist_action == action_name:
                action_count += 1
                if any(e.event_type == event_type for e in hist_events):
                    event_after_action_count += 1

        if action_count == 0:
            return 0.5

        return event_after_action_count / action_count


# Module-level convenience function
def detect_events_between_frames(
    frame_before: np.ndarray,
    frame_after: np.ndarray,
    action_number: int = 0,
) -> Tuple[List[TrackedObject], List[DetectedEvent]]:
    """
    Convenience function to detect events between frames.
    """
    detector = EventDetector()
    return detector.detect_events_from_frames(frame_before, frame_after, action_number)
