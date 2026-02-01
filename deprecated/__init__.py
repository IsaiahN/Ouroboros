"""
Deprecated Module Package
=========================

Contains legacy code that has been superseded by the modular architecture.
These files are kept for reference and fallback during migration.

Files:
- agent_self_model_legacy.py: Original 15,527-line monolith (use engines/self_model/ instead)
- core_gameplay_legacy.py: Legacy gameplay (use core_gameplay.py instead)

WARNING: Do not add new functionality to these files. 
         All new development should use the modular engines/ structure.
"""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

# Re-export for backwards compatibility during migration
from .agent_self_model_legacy import (
    AgentSelfModel,
    SymbolicStateTracker,
    CompletionPredictor,
    WeavingReporter,
    CognitiveStageSystem,
    MetacognitiveReasoningEngine,
    EpisodicMemorySystem,
    AgentNetworkContributor,
    AgentHypothesisSystem,
)

__all__ = [
    'AgentSelfModel',
    'SymbolicStateTracker', 
    'CompletionPredictor',
    'WeavingReporter',
    'CognitiveStageSystem',
    'MetacognitiveReasoningEngine',
    'EpisodicMemorySystem',
    'AgentNetworkContributor',
    'AgentHypothesisSystem',
]
