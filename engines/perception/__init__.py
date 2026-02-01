# engines/perception/__init__.py
"""Perception engines - visual analysis, pattern detection, and object identification."""

from engines.perception.terminal_pattern_detector import TerminalPatternDetector
from engines.perception.visual_analyzer import VisualAnalyzer
from engines.perception.visual_reasoning import VisualReasoningEngine


def get_object_detector():
    from engines.perception.object_detector import ObjectDetector
    return ObjectDetector

__all__ = ['VisualAnalyzer', 'TerminalPatternDetector', 'get_object_detector', 'VisualReasoningEngine']
