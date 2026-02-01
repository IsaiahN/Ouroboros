#!/usr/bin/env python3
"""
Self Model Engine Package
=========================

Modular components for agent self-model functionality.

Existing Modules:
- symbolic_tracker: SymbolicStateTracker for key/lock/tool tracking
- completion_predictor: CompletionPredictor for step estimation
- embedding_matcher: EmbeddingMatcher for similarity-based action suggestions
- few_shot_relations: FewShotRelations for control bootstrapping
- network_sharing: NetworkSharingEngine for hypothesis sharing
- action6_behavior: Action6BehaviorEngine for pseudobuttons, selection, availability

New Clean Modules (v2):
- control_tracker: ControlTracker for "I am this object" tracking
- discovery_engine: DiscoveryEngine for systematic object discovery
- grid_analysis: GridAnalyzer for frame differencing and grid operations
- trigger_sequences: TriggerSequenceTracker for interaction chains
- valence_goals: ValenceGoalEngine for good/bad associations and goals
- universal_patterns: UniversalPatternEngine for cross-game transfer
- click_behavior: ClickBehaviorClassifier for click action classification
- belief_system: BeliefSystem for belief dependencies and cascade invalidation
"""
import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from .action6_behavior import Action6BehaviorEngine
from .belief_system import Belief, BeliefStatus, BeliefSystem, BeliefType
from .click_behavior import ClickBehavior, ClickBehaviorClassifier, ClickResult
from .cognitive_core import CognitiveCore
from .completion_predictor import CompletionPredictor

# Export new clean modules (v2)
from .control_tracker import ControlledObject, ControlObservation, ControlTracker
from .discovery_engine import DiscoveryEngine, DiscoveryPhase, ObjectBehavior
from .embedding_matcher import EmbeddingMatcher
from .few_shot_relations import FewShotRelations
from .grid_analysis import (
    FrameDiff,
    GridAnalyzer,
    ObjectMovement,
    frames_identical,
    quick_diff,
)
from .network_sharing import NetworkSharingEngine

# Export existing classes
from .symbolic_tracker import SymbolicStateTracker
from .trigger_sequences import ProvenSequence, TriggerChain, TriggerSequenceTracker
from .universal_patterns import PatternScope, PatternType, UniversalPatternEngine
from .valence_goals import GoalType, Valence, ValenceGoalEngine

__all__ = [
    # Core (unified interface)
    'CognitiveCore',
    # Existing
    'SymbolicStateTracker',
    'CompletionPredictor',
    'EmbeddingMatcher',
    'FewShotRelations',
    'NetworkSharingEngine',
    'Action6BehaviorEngine',
    # New clean modules (v2)
    'ControlTracker',
    'ControlledObject',
    'ControlObservation',
    'DiscoveryEngine',
    'DiscoveryPhase',
    'ObjectBehavior',
    'GridAnalyzer',
    'FrameDiff',
    'ObjectMovement',
    'quick_diff',
    'frames_identical',
    'TriggerSequenceTracker',
    'TriggerChain',
    'ProvenSequence',
    'ValenceGoalEngine',
    'Valence',
    'GoalType',
    'UniversalPatternEngine',
    'PatternScope',
    'PatternType',
    'ClickBehaviorClassifier',
    'ClickBehavior',
    'ClickResult',
    'BeliefSystem',
    'Belief',
    'BeliefType',
    'BeliefStatus',
]
