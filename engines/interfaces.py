"""
Engine Interfaces - Protocol Definitions for Decision Rung System
=================================================================

This module defines the interfaces (Protocols) that the 42 decision rungs
expect from their engine dependencies. Each Protocol specifies:
- What methods the rung will call
- What parameters are expected
- What return types are expected

Using Protocols (structural subtyping) instead of ABC allows:
- Existing classes to conform without modification
- Easier testing with mock objects
- Clear documentation of rung dependencies

Usage:
    from engines.interfaces import SelfModelInterface
    
    class MySelfModel:
        # Implement all methods from SelfModelInterface
        def get_embedding_suggested_action(...) -> ...:
            ...
    
    # Type checker will verify MySelfModel conforms to SelfModelInterface
    model: SelfModelInterface = MySelfModel()
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from typing import Protocol, Dict, List, Any, Optional, Tuple


# =============================================================================
# SELF MODEL INTERFACES
# Used by: EmbeddingSuggestionRung, MetacognitivePredictionRung, 
#          FewShotInvariantsRung, NetworkObjectInventoryRung
# =============================================================================

class SelfModelInterface(Protocol):
    """
    Interface for agent self-model system.
    
    Provides:
    - Object control tracking ("I am this object")
    - Embedding-based frame matching
    - Network hypothesis sharing
    - Few-shot relation learning
    """
    
    def get_embedding_suggested_action(
        self,
        game_type: Optional[str],
        level: Optional[int],
        current_frame: Optional[List[List[int]]],
        action_scores: Optional[Dict[int, float]] = None,
        top_k: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Get action suggestion based on learned frame embeddings.
        
        Finds similar past situations and returns what action worked best.
        
        Returns:
            Dict with 'action', 'confidence', 'similar_count' or None
        """
        ...
    
    def get_current_prediction(self) -> Optional[Dict[str, Any]]:
        """
        Get the current hypothesis being tested.
        
        Returns:
            Dict with 'test_action', 'confidence', 'hypothesis' or None
        """
        ...
    
    def get_few_shot_control_relations(
        self,
        game_id: str,
        level: int,
        min_confidence: float = 0.5
    ) -> Optional[Dict[str, Any]]:
        """
        Get few-shot invariants/variants from sequence abstraction.
        
        Returns:
            Dict with 'suggested_action', 'sample_size', 'confidence' or None
        """
        ...
    
    def get_network_object_inventory(
        self,
        game_type: str,
        level: int
    ) -> Dict[str, Any]:
        """
        Query network knowledge about interactable objects.
        
        Returns:
            Dict with 'total_unique', 'interactable', etc.
        """
        ...
    
    def share_control_discovery_to_network(
        self,
        agent_id: str,
        game_id: str,
        level: int,
        controlled_objects: List[str],
        action_response_map: Dict[str, List[str]],
        confidence: float,
        generation: int = 0
    ) -> Optional[str]:
        """
        Share "I am this object" discovery to network.
        
        Returns:
            hypothesis_id if shared, None otherwise
        """
        ...


# =============================================================================
# VISUAL ANALYZER INTERFACES
# Used by: VisualAnalyzerRung, GridExplorationRung
# =============================================================================

class VisualAnalyzerInterface(Protocol):
    """
    Interface for visual frame analysis.
    
    Provides:
    - Priority target identification for ACTION6 clicks
    - Grid-based systematic exploration
    - Salient feature detection
    """
    
    def get_priority_targets(
        self,
        frame: Optional[List[List[int]]]
    ) -> List[Dict[str, Any]]:
        """
        Get prioritized click targets from frame analysis.
        
        Returns:
            List of dicts with 'x', 'y', 'confidence', 'reason'
        """
        ...
    
    def get_grid_exploration_targets(self) -> List[Dict[str, Any]]:
        """
        Get systematic grid walk targets when stuck.
        
        Returns:
            List of dicts with 'x', 'y', 'grid_index'
        """
        ...
    
    def set_priority_color(self, color: int, reason: str = "") -> None:
        """Set a priority color to target based on learning."""
        ...
    
    def record_color_success(self, color: int) -> None:
        """Record that clicking a color led to success."""
        ...


# =============================================================================
# SCIENTIFIC METHOD INTERFACES
# Used by: ScientificMethodRung, QuestioningRung, TheoryGateRung
# =============================================================================

class QuestioningEngineInterface(Protocol):
    """Interface for Q1-Q9 questioning system."""
    
    def get_blocking_questions(self) -> List[str]:
        """Get questions that are blocking action selection."""
        ...
    
    def get_allowed_actions(self, blocking_questions: List[str]) -> List[str]:
        """Get actions allowed given blocking questions."""
        ...


class ScientificMethodInterface(Protocol):
    """
    Interface for theory formation and testing.
    
    Provides:
    - Theory stage tracking
    - Working theory management
    - Questioning engine access
    """
    
    def get_theory_stage(self) -> str:
        """
        Get current theory stage.
        
        Returns:
            One of: 'exploring', 'speculating', 'confirmed', 'contradicted'
        """
        ...
    
    def get_working_theory(self) -> Optional[Dict[str, Any]]:
        """
        Get the current working theory.
        
        Returns:
            Dict with 'stage', 'hypothesis', 'evidence', etc.
        """
        ...
    
    @property
    def questioning_engine(self) -> QuestioningEngineInterface:
        """Access the questioning engine."""
        ...


# =============================================================================
# TERMINAL PATTERN INTERFACES
# Used by: DeathAvoidanceRung, TerminalPatternRung
# =============================================================================

class TerminalPatternInterface(Protocol):
    """
    Interface for death/danger pattern detection.
    
    Provides:
    - Graduated action weights based on danger
    - Terminal state approach detection
    """
    
    def get_graduated_action_weights(
        self,
        game_type: str,
        level: int,
        position: Tuple[int, int],
        frontier_mode: bool = False
    ) -> Dict[str, float]:
        """
        Get safety weights for each action based on historical death patterns.
        
        Returns:
            Dict mapping action name to weight (0.0-1.0, lower = more dangerous)
        """
        ...
    
    def detect_terminal_approach(
        self,
        frame: Optional[List[List[int]]],
        recent_actions: List[str]
    ) -> Dict[str, Any]:
        """
        Detect if approaching a terminal (death) state.
        
        Returns:
            Dict with 'approaching_terminal', 'fatal_action', 'confidence'
        """
        ...


# =============================================================================
# PRIMITIVE SUGGESTER INTERFACE (replaces CODS)
# Used by: PrimitiveSuggesterRung
# =============================================================================

class PrimitiveSuggesterInterface(Protocol):
    """
    Interface for direct primitive-to-action mapping.
    
    Replaces the deprecated CODSEngine with simpler approach:
    - Apply primitives to frames
    - Map outputs to actions
    - Track effectiveness via RLVR
    """
    
    def suggest_action(
        self,
        frame: List[List[int]],
        game_type: Optional[str] = None,
        recent_actions: Optional[List[int]] = None
    ) -> Any:
        """
        Suggest action based on primitive analysis.
        
        Returns:
            SuggestionResult with action, confidence, primitive, reasoning
        """
        ...
    
    def record_outcome(
        self,
        game_type: str,
        primitive: str,
        action: int,
        success: bool
    ) -> None:
        """Record outcome for RLVR learning."""
        ...


# Legacy alias for backward compatibility
class CODSEngineInterface(Protocol):
    """
    DEPRECATED: Use PrimitiveSuggesterInterface instead.
    
    Kept for backward compatibility with existing code.
    """
    
    def suggest_action(
        self,
        game_context: Dict[str, Any],
        available_actions: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Get action suggestion."""
        ...


# =============================================================================
# VIRAL PACKAGE INTERFACE
# Used by: PariahAvoidanceRung
# =============================================================================

class ViralPackageInterface(Protocol):
    """
    Interface for viral knowledge spread system.
    
    Provides:
    - Pariah pattern queries (failed strategies)
    - Package creation and distribution
    """
    
    def get_pariahs(
        self,
        game_type: str,
        level: int
    ) -> List[Dict[str, Any]]:
        """
        Get failed patterns (pariahs) for this game/level.
        
        Returns:
            List of dicts with 'failed_action', 'toxicity', etc.
        """
        ...


# =============================================================================
# FRUSTRATION DETECTOR INTERFACE
# Used by: FrustrationDetectionRung
# =============================================================================

class FrustrationDetectorInterface(Protocol):
    """Interface for stuck/frustration detection."""
    
    def is_frustrated(self) -> Dict[str, Any]:
        """
        Check if agent is frustrated (stuck).
        
        Returns:
            Dict with 'is_frustrated', 'reason', 'severity'
        """
        ...


# =============================================================================
# SENSATION ENGINE INTERFACE
# Used by: SensationEngineRung
# =============================================================================

class SensationEngineInterface(Protocol):
    """
    Interface for emotional/sensation-based decision biasing.
    
    Provides:
    - Tetrahedral sensation model (approach/avoid/curiosity/threat)
    """
    
    def get_tetrahedral_sensation(
        self,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get emotional coloring for current situation.
        
        Returns:
            Dict with 'approach_score', 'threat_level', 'threat_direction', etc.
        """
        ...


# =============================================================================
# I-THREAD INTERFACE
# Used by: IThreadRung, TwoStreamsRung
# =============================================================================

class IThreadInterface(Protocol):
    """
    Interface for persistent agent identity.
    
    Provides:
    - Stream weight management (wA/wB)
    - Death persona spawning
    """
    
    def get_wA(self) -> float:
        """Get Stream A (private experience) weight."""
        ...
    
    def get_wB(self) -> float:
        """Get Stream B (network wisdom) weight."""
        ...
    
    def spawn_death_persona(
        self,
        role: str
    ) -> Optional[Dict[str, Any]]:
        """
        Spawn a death persona when near culling.
        
        Returns:
            Dict with 'name', 'suggested_action', 'reason' or None
        """
        ...


# =============================================================================
# NEAR MISS ANALYZER INTERFACE
# Used by: NearMissAnalyzerRung
# =============================================================================

class NearMissAnalyzerInterface(Protocol):
    """Interface for learning from high-score failures."""
    
    def get_insights(
        self,
        game_type: str,
        level: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get insights from near-miss analysis.
        
        Returns:
            Dict with 'suggested_action', 'confidence', 'category' or None
        """
        ...


# =============================================================================
# SUBGOAL PLANNER INTERFACE
# Used by: SubgoalPlanningRung
# =============================================================================

class SubgoalPlannerInterface(Protocol):
    """Interface for subgoal decomposition."""
    
    def get_current_subgoal(self) -> Optional[Dict[str, Any]]:
        """
        Get the current subgoal being pursued.
        
        Returns:
            Dict with 'next_action', 'confidence', 'description', 'index', 'total'
        """
        ...


# =============================================================================
# BUDGET ALLOCATOR INTERFACE
# Used by: BreakthroughBudgetRung
# =============================================================================

class BudgetAllocatorInterface(Protocol):
    """Interface for dynamic action budget allocation."""
    
    def get_budget(
        self,
        game_type: str
    ) -> Dict[str, Any]:
        """
        Get action budget for this game type.
        
        Returns:
            Dict with 'per_level', 'total', 'phase'
        """
        ...


# =============================================================================
# REGULATORY SIGNAL INTERFACE
# Used by: RegulatorySignalRung
# =============================================================================

class RegulatorySignalInterface(Protocol):
    """Interface for network homeostasis signals."""
    
    def get_active_signals(self) -> List[Dict[str, Any]]:
        """
        Get currently active regulatory signals.
        
        Returns:
            List of dicts with 'type', 'strength', etc.
        """
        ...


# =============================================================================
# RESONANCE DETECTOR INTERFACE
# Used by: ResonanceDetectorRung
# =============================================================================

class ResonanceDetectorInterface(Protocol):
    """Interface for cross-agent pattern discovery."""
    
    def get_resonant_patterns(
        self,
        game_type: str
    ) -> List[Dict[str, Any]]:
        """
        Get patterns that resonate across agents.
        
        Returns:
            List of dicts with 'suggested_action', 'resonance_score', 'description'
        """
        ...


# =============================================================================
# COUNTERFACTUAL ANALYZER INTERFACE
# Used by: MicroCounterfactualRung
# =============================================================================

class CounterfactualAnalyzerInterface(Protocol):
    """Interface for lightweight what-if analysis."""
    
    def generate_micro_rollouts(
        self,
        game_state: Any,
        max_rollouts: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate micro counterfactual rollouts.
        
        Returns:
            List of dicts with 'action', 'expected_value', 'reason'
        """
        ...


# =============================================================================
# ACTION HANDLER INTERFACE
# Used by: CoordinateOscillationRung, ThreeLayerFilterRung
# =============================================================================

class ActionHandlerInterface(Protocol):
    """Interface for action execution and tracking."""
    
    def detect_oscillation(self) -> Dict[str, Any]:
        """
        Detect coordinate oscillation patterns.
        
        Returns:
            Dict with 'oscillation_detected', 'oscillating_coords'
        """
        ...


# =============================================================================
# MULTI-STAGE PIPELINE INTERFACE
# Used by: MultiStageMatchingRung
# =============================================================================

class MultiStagePipelineInterface(Protocol):
    """Interface for cascading sequence matching."""
    
    def get_sequence_with_fallback(
        self,
        game_type: str,
        level: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get sequence using multi-stage fallback.
        
        Returns:
            Dict with 'sequence', 'confidence', 'stage' or None
        """
        ...


# =============================================================================
# ABSTRACTION ENGINE INTERFACE
# Used by: AbstractionTemplatesRung
# =============================================================================

class AbstractionEngineInterface(Protocol):
    """Interface for pattern template abstraction."""
    
    def should_use_template(
        self,
        game_type: str,
        level: int
    ) -> bool:
        """Check if a template should be used for this game/level."""
        ...
    
    def get_template_for_replay(
        self,
        game_type: str,
        level: int
    ) -> Optional[List[str]]:
        """Get template sequence for replay."""
        ...


# =============================================================================
# REPLAY LEARNING INTERFACE
# Used by: ReplayLearningRung
# =============================================================================

class ReplayLearningInterface(Protocol):
    """Interface for prediction-based replay learning."""
    
    def get_current_prediction(self) -> Optional[Dict[str, Any]]:
        """
        Get current prediction during replay.
        
        Returns:
            Dict with 'action', 'confidence', 'hypothesis' or None
        """
        ...


# =============================================================================
# IMAGINATION BUDGET INTERFACE
# Used by: ImaginationBudgetRung
# =============================================================================

class ImaginationBudgetInterface(Protocol):
    """Interface for cognitive budget allocation."""
    
    def calculate_budget(
        self,
        is_novel: bool,
        is_frontier: bool,
        surprise_score: float
    ) -> Dict[str, Any]:
        """
        Calculate imagination budget based on novelty.
        
        Returns:
            Dict with 'total', 'tier', etc.
        """
        ...


# =============================================================================
# NETWORK EXPLORATION TRACKER INTERFACE
# Used by: NetworkExplorationStatsRung
# =============================================================================

class NetworkExplorationInterface(Protocol):
    """Interface for exploration coverage tracking."""
    
    def get_exploration_stats(
        self,
        game_type: str,
        level: int
    ) -> Dict[str, Any]:
        """
        Get exploration statistics.
        
        Returns:
            Dict with 'coverage_percent', 'coldspots', 'recommended_direction'
        """
        ...


# =============================================================================
# PRIMITIVE HELPER INTERFACE
# Used by: PrimitiveStuckDetectionRung
# =============================================================================

class PrimitiveHelperInterface(Protocol):
    """Interface for seed primitive orchestration."""
    
    def detect_stuck_pattern(
        self,
        recent_frames: List[Any],
        recent_actions: List[str]
    ) -> Dict[str, Any]:
        """
        Use primitives to detect stuck state.
        
        Returns:
            Dict with 'is_stuck', 'reason'
        """
        ...


# =============================================================================
# COMBINED ENGINE REGISTRY INTERFACE
# =============================================================================

class EngineRegistryInterface(Protocol):
    """
    Interface for the central engine registry.
    
    Provides lazy-loaded access to all engines via properties.
    """
    
    @property
    def self_model(self) -> Optional[SelfModelInterface]: ...
    
    @property
    def visual_analyzer(self) -> Optional[VisualAnalyzerInterface]: ...
    
    @property
    def scientific_method(self) -> Optional[ScientificMethodInterface]: ...
    
    @property
    def terminal_pattern_detector(self) -> Optional[TerminalPatternInterface]: ...
    
    @property
    def cods_engine(self) -> Optional[CODSEngineInterface]: 
        """DEPRECATED: Use primitive_suggester instead."""
        ...
    
    @property
    def primitive_suggester(self) -> Optional[PrimitiveSuggesterInterface]: ...
    
    @property
    def viral_package_engine(self) -> Optional[ViralPackageInterface]: ...
    
    @property
    def frustration_detector(self) -> Optional[FrustrationDetectorInterface]: ...
    
    @property
    def sensation_engine(self) -> Optional[SensationEngineInterface]: ...
    
    @property
    def i_thread(self) -> Optional[IThreadInterface]: ...
    
    @property
    def near_miss_analyzer(self) -> Optional[NearMissAnalyzerInterface]: ...
    
    @property
    def subgoal_planner(self) -> Optional[SubgoalPlannerInterface]: ...
    
    @property
    def breakthrough_allocator(self) -> Optional[BudgetAllocatorInterface]: ...
    
    @property
    def regulatory_engine(self) -> Optional[RegulatorySignalInterface]: ...
    
    @property
    def resonance_detector(self) -> Optional[ResonanceDetectorInterface]: ...
    
    @property
    def counterfactual_analyzer(self) -> Optional[CounterfactualAnalyzerInterface]: ...
    
    @property
    def action_handler(self) -> Optional[ActionHandlerInterface]: ...
    
    @property
    def multi_stage_pipeline(self) -> Optional[MultiStagePipelineInterface]: ...
    
    @property
    def abstraction_engine(self) -> Optional[AbstractionEngineInterface]: ...
    
    @property
    def replay_learning_engine(self) -> Optional[ReplayLearningInterface]: ...
    
    @property
    def imagination_budget(self) -> Optional[ImaginationBudgetInterface]: ...
    
    @property
    def network_exploration_tracker(self) -> Optional[NetworkExplorationInterface]: ...
    
    @property
    def primitive_helper(self) -> Optional[PrimitiveHelperInterface]: ...


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Self Model
    'SelfModelInterface',
    
    # Perception
    'VisualAnalyzerInterface',
    'TerminalPatternInterface',
    
    # Cognition
    'ScientificMethodInterface',
    'QuestioningEngineInterface',
    'CODSEngineInterface',
    'CounterfactualAnalyzerInterface',
    
    # Memory/Planning
    'ViralPackageInterface',
    'MultiStagePipelineInterface',
    'AbstractionEngineInterface',
    'ReplayLearningInterface',
    
    # Regulation
    'FrustrationDetectorInterface',
    'BudgetAllocatorInterface',
    'ImaginationBudgetInterface',
    'RegulatorySignalInterface',
    'NetworkExplorationInterface',
    
    # Social
    'ResonanceDetectorInterface',
    
    # Consciousness
    'SensationEngineInterface',
    'IThreadInterface',
    
    # Analysis
    'NearMissAnalyzerInterface',
    'SubgoalPlannerInterface',
    'ActionHandlerInterface',
    'PrimitiveHelperInterface',
    
    # Registry
    'EngineRegistryInterface',
]
