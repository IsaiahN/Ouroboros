"""
Cognition Engines Package

This package contains modules for cognitive tracking and metacognitive reasoning:
- CognitiveStageSystem: Piaget-inspired developmental stage tracking
- MetacognitiveReasoningEngine: Prediction, assumption tracking, theory revision
"""

from engines.cognition.cognitive_stages import CognitiveStageSystem
from engines.cognition.metacognition import MetacognitiveReasoningEngine

__all__ = [
    'CognitiveStageSystem',
    'MetacognitiveReasoningEngine',
]
