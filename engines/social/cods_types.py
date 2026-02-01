import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
CODS Types - Dataclasses and Types for Cognitive Operator Discovery System
===========================================================================

Extracted from cods_engine.py to reduce file size and improve organization.
These are pure data structures with no dependencies on other CODS components.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CODSGameContext:
    """Context for CODS operations during a game."""
    game_id: str
    level_number: int
    agent_id: Optional[str]
    generation: int = 0
    current_frame: Optional[List[List[int]]] = None
    previous_frame: Optional[List[List[int]]] = None
    action_history: List[int] = field(default_factory=list)
    score: float = 0.0
    persona_id: Optional[str] = None
    world_model: Optional[str] = None
    problem_signature: Optional[str] = None
    is_frontier: bool = False  # True if this level is unexplored territory
    
    def update_frame(self, frame: List[List[int]]):
        """Update current frame, moving old to previous."""
        self.previous_frame = self.current_frame
        self.current_frame = frame


@dataclass
class OperatorResult:
    """Result of applying an operator."""
    success: bool
    output: Any
    execution_time_ms: float
    error: Optional[str] = None
    operator_id: Optional[str] = None


@dataclass
class BayesianHypothesis:
    """
    Represents a hypothesis with Bayesian probability tracking.
    
    The core of evidence-driven operator synthesis:
    - Hypotheses are created from failure patterns
    - Evidence accumulates from game outcomes
    - When posterior exceeds threshold, synthesis is triggered
    """
    hypothesis_id: str
    hypothesis_type: str  # 'PRIMITIVE_NEED', 'OPERATOR_SYNTHESIS', 'PATTERN_DISCOVERY'
    game_type: str
    level_number: Optional[int]
    description: str
    
    # What this hypothesis suggests
    target_primitive: Optional[str] = None  # Primitive to unlock
    suggested_composition: Optional[List[str]] = None  # Primitives to compose
    
    # Bayesian tracking
    prior: float = 0.5
    posterior: float = 0.5
    evidence_for: int = 0
    evidence_against: int = 0
    
    # Confidence interval (Wilson score)
    confidence_low: float = 0.0
    confidence_high: float = 1.0
    
    # Thresholds
    confirmation_threshold: float = 0.85
    refutation_threshold: float = 0.15
    
    # Status
    status: str = 'active'  # 'active', 'confirmed', 'refuted', 'synthesized'
    source_type: Optional[str] = None  # 'failure_analysis', 'counterfactual', 'near_miss'
    
    def is_confirmed(self) -> bool:
        """Check if hypothesis has enough evidence to act on."""
        return self.posterior >= self.confirmation_threshold
    
    def is_refuted(self) -> bool:
        """Check if hypothesis should be abandoned."""
        return self.posterior <= self.refutation_threshold
    
    def sample_size(self) -> int:
        """Total evidence collected."""
        return self.evidence_for + self.evidence_against


__all__ = [
    'CODSGameContext',
    'OperatorResult',
    'BayesianHypothesis',
]
