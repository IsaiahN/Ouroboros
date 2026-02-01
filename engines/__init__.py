"""
Engines Package - Modular Engine Architecture
=============================================

This package contains small, focused engine modules that the
Decision Rung System uses to make action decisions.

Architecture:
- interfaces.py: Protocol definitions for all engines
- registry.py: Lazy-loading engine registry

Sub-packages:
- self_model/: Agent self-model components
- cognition/: Higher-level reasoning
- perception/: Frame/visual analysis
- memory/: Knowledge storage
- planning/: Action planning
- regulation/: System-level control
- social/: Network/viral systems
- consciousness/: Two Streams / I-Thread

Usage:
    from engines import EngineRegistry

    registry = EngineRegistry(db_path="core_data.db")

    # Access engines via properties
    self_model = registry.self_model
    visual = registry.visual_analyzer

    # Or by name
    engine = registry.get('scientific_method')
"""

import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from engines.interfaces import (  # Self Model; Perception; Cognition; Memory/Planning; Regulation; Social; Consciousness; Analysis; Registry
    AbstractionEngineInterface,
    ActionHandlerInterface,
    BudgetAllocatorInterface,
    CODSEngineInterface,
    CounterfactualAnalyzerInterface,
    EngineRegistryInterface,
    FrustrationDetectorInterface,
    ImaginationBudgetInterface,
    IThreadInterface,
    MultiStagePipelineInterface,
    NearMissAnalyzerInterface,
    NetworkExplorationInterface,
    PrimitiveHelperInterface,
    QuestioningEngineInterface,
    RegulatorySignalInterface,
    ReplayLearningInterface,
    ResonanceDetectorInterface,
    ScientificMethodInterface,
    SelfModelInterface,
    SensationEngineInterface,
    SubgoalPlannerInterface,
    TerminalPatternInterface,
    ViralPackageInterface,
    VisualAnalyzerInterface,
)
from engines.registry import EngineRegistry, get_registry

__all__ = [
    # Interfaces
    'SelfModelInterface',
    'VisualAnalyzerInterface',
    'TerminalPatternInterface',
    'ScientificMethodInterface',
    'QuestioningEngineInterface',
    'CODSEngineInterface',
    'CounterfactualAnalyzerInterface',
    'ViralPackageInterface',
    'MultiStagePipelineInterface',
    'AbstractionEngineInterface',
    'ReplayLearningInterface',
    'FrustrationDetectorInterface',
    'BudgetAllocatorInterface',
    'ImaginationBudgetInterface',
    'RegulatorySignalInterface',
    'NetworkExplorationInterface',
    'ResonanceDetectorInterface',
    'SensationEngineInterface',
    'IThreadInterface',
    'NearMissAnalyzerInterface',
    'SubgoalPlannerInterface',
    'ActionHandlerInterface',
    'PrimitiveHelperInterface',
    'EngineRegistryInterface',

    # Registry
    'EngineRegistry',
    'get_registry',

    # Self Model Components
    'SymbolicStateTracker',
    'CompletionPredictor',
    'EmbeddingMatcher',
    'FewShotRelations',
    'NetworkSharingEngine',
    'Action6BehaviorEngine',

    # Consciousness Components
    'WeavingReporter',

    # Cognition Components
    'CognitiveStageSystem',
    'MetacognitiveReasoningEngine',

    # Memory Components
    'EpisodicMemorySystem',

    # Social Components
    'AgentNetworkContributor',
    'AgentHypothesisSystem',
]

# Import cognition components
from engines.cognition import CognitiveStageSystem, MetacognitiveReasoningEngine

# Import consciousness components
from engines.consciousness import WeavingReporter

# Import memory components
from engines.memory import EpisodicMemorySystem

# Import self_model components for convenience
from engines.self_model import (
    Action6BehaviorEngine,
    CompletionPredictor,
    EmbeddingMatcher,
    FewShotRelations,
    NetworkSharingEngine,
    SymbolicStateTracker,
)

# Import social components
from engines.social import AgentHypothesisSystem, AgentNetworkContributor
