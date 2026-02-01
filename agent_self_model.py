"""
Agent Self Model - Compatibility Shim

This module re-exports all classes from their canonical engine locations.
The original monolith (15,513 lines, 9 classes) was refactored into:

- engines/self_model/symbolic_tracker.py -> SymbolicStateTracker
- engines/self_model/completion_predictor.py -> CompletionPredictor
- engines/self_model/cognitive_core.py -> CognitiveCore (replaces AgentSelfModel)
- engines/consciousness/weaving_reporter.py -> WeavingReporter
- engines/cognition/cognitive_stages.py -> CognitiveStageSystem
- engines/cognition/metacognition.py -> MetacognitiveReasoningEngine
- engines/memory/episodic_memory.py -> EpisodicMemorySystem
- engines/social/network_contributor.py -> AgentNetworkContributor
- engines/social/hypothesis_system.py -> AgentHypothesisSystem

Import pattern: from agent_self_model import AgentSelfModel
(AgentSelfModel is now an alias for SelfModelFacade)
"""
import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

# CognitiveCore replaces the deprecated AgentSelfModel monolith
# Alias for backward compatibility
from engines.self_model.cognitive_core import CognitiveCore
from engines.self_model.completion_predictor import CompletionPredictor

# Self-model components
from engines.self_model.symbolic_tracker import SymbolicStateTracker

AgentSelfModel = CognitiveCore  # Backward compatibility alias

# Cognition components
from engines.cognition.cognitive_stages import CognitiveStageSystem
from engines.cognition.metacognition import MetacognitiveReasoningEngine

# Consciousness components
from engines.consciousness.weaving_reporter import WeavingReporter

# Memory components
from engines.memory.episodic_memory import EpisodicMemorySystem
from engines.social.hypothesis_system import AgentHypothesisSystem

# Social/network components
from engines.social.network_contributor import AgentNetworkContributor

__all__ = [
    # Self-model
    'SymbolicStateTracker',
    'CompletionPredictor',
    'AgentSelfModel',
    # Consciousness
    'WeavingReporter',
    # Cognition
    'CognitiveStageSystem',
    'MetacognitiveReasoningEngine',
    # Memory
    'EpisodicMemorySystem',
    # Social
    'AgentNetworkContributor',
    'AgentHypothesisSystem',
]
