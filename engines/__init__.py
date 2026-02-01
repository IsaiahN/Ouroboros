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

from engines.interfaces import (
    # Self Model
    SelfModelInterface,
    
    # Perception
    VisualAnalyzerInterface,
    TerminalPatternInterface,
    
    # Cognition
    ScientificMethodInterface,
    QuestioningEngineInterface,
    CODSEngineInterface,
    CounterfactualAnalyzerInterface,
    
    # Memory/Planning
    ViralPackageInterface,
    MultiStagePipelineInterface,
    AbstractionEngineInterface,
    ReplayLearningInterface,
    
    # Regulation
    FrustrationDetectorInterface,
    BudgetAllocatorInterface,
    ImaginationBudgetInterface,
    RegulatorySignalInterface,
    NetworkExplorationInterface,
    
    # Social
    ResonanceDetectorInterface,
    
    # Consciousness
    SensationEngineInterface,
    IThreadInterface,
    
    # Analysis
    NearMissAnalyzerInterface,
    SubgoalPlannerInterface,
    ActionHandlerInterface,
    PrimitiveHelperInterface,
    
    # Registry
    EngineRegistryInterface,
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

# Import self_model components for convenience
from engines.self_model import (
    SymbolicStateTracker, 
    CompletionPredictor,
    EmbeddingMatcher,
    FewShotRelations,
    NetworkSharingEngine,
    Action6BehaviorEngine,
)

# Import consciousness components
from engines.consciousness import WeavingReporter

# Import cognition components
from engines.cognition import CognitiveStageSystem, MetacognitiveReasoningEngine

# Import memory components
from engines.memory import EpisodicMemorySystem

# Import social components
from engines.social import AgentNetworkContributor, AgentHypothesisSystem
