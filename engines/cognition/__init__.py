"""
Cognition Engines Package

This package contains modules for cognitive tracking and metacognitive reasoning:
- CognitiveStageSystem: Piaget-inspired developmental stage tracking
- MetacognitiveReasoningEngine: Prediction, assumption tracking, theory revision
- AgentHypothesisSystem: Agent-initiated hypothesis creation (via engines.social)
- RuleInductionEngine: Learn transferable rules from successful games
"""

from engines.cognition.cognitive_stages import CognitiveStageSystem
from engines.cognition.metacognition import MetacognitiveReasoningEngine
from engines.cognition.rule_induction import RuleInductionEngine

# Re-export AgentHypothesisSystem from social for backward compatibility
# (it lives in social because it's primarily about network contribution)
from engines.social.hypothesis_system import AgentHypothesisSystem

__all__ = [
    'CognitiveStageSystem',
    'MetacognitiveReasoningEngine',
    'AgentHypothesisSystem',
    'RuleInductionEngine',
]
