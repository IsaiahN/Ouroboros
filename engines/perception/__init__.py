# engines/perception/__init__.py
"""Perception engines - visual analysis, pattern detection, and object identification."""

from engines.perception.player_localizer import PlayerLocalizer
from engines.perception.property_extractor import (
    PropertyExtractor,
    properties_from_json,
    properties_to_json,
)
from engines.perception.terminal_pattern_detector import TerminalPatternDetector
from engines.perception.visual_analyzer import VisualAnalyzer
from engines.perception.visual_reasoning import VisualReasoningEngine


def get_object_detector():
    from engines.perception.object_detector import ObjectDetector
    return ObjectDetector


def get_object_tracker():
    """Lazy-load ObjectTracker to avoid import issues."""
    from engines.perception.object_tracker import ObjectTracker
    return ObjectTracker


def get_event_detector():
    """Lazy-load EventDetector to avoid import issues."""
    from engines.perception.event_detector import EventDetector
    return EventDetector


def get_spatial_effect_learner():
    """Lazy-load SpatialEffectLearner to avoid import issues."""
    from engines.perception.spatial_learning import SpatialEffectLearner
    return SpatialEffectLearner


def get_multi_object_goal_tracker():
    """Lazy-load MultiObjectGoalTracker to avoid import issues."""
    from engines.perception.spatial_learning import MultiObjectGoalTracker
    return MultiObjectGoalTracker


def get_visual_cortex():
    """Lazy-load VisualCortex for scene understanding."""
    from engines.perception.visual_cortex import VisualCortex
    return VisualCortex


__all__ = [
    'VisualAnalyzer',
    'TerminalPatternDetector',
    'get_object_detector',
    'get_object_tracker',
    'get_event_detector',
    'get_spatial_effect_learner',
    'get_multi_object_goal_tracker',
    'get_visual_cortex',
    'VisualReasoningEngine',
    'PlayerLocalizer',
    'PropertyExtractor',
    'properties_to_json',
    'properties_from_json',
]
