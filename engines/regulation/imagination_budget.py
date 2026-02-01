#!/usr/bin/env python3
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
"""
Imagination/Mental Modeling Budget Helper

Computes a per-step budget for mental modeling based on:
- Developmental window (early generations free-play)
- Performance percentile
- Cognitive stage multiplier
- Context mode (exploration/exploitation/skill)
- Question sophistication bonus
- Grounding multiplier (from AgentSelfModel)

Outputs a tuple of (budget_total, components) where components capture
intermediate values for logging and reasoning payloads.
"""

from typing import Dict, Optional

MIN_GROUNDING = 0.3
MAX_GROUNDING = 1.5


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(value, upper))


def compute_mental_modeling_budget(
    generation: int,
    performance_percentile: float,
    stage: int,
    context_mode: str,
    question_tier: Optional[str] = None,
    grounding_score: Optional[float] = None,
    base_budget: float = 0.1,
    max_bonus: float = 1.0,
) -> Dict[str, float]:
    """Compute a mental modeling budget signal.

    Args:
        generation: Current generation number (developmental window gate).
        performance_percentile: 0.0-1.0 percentile in generation.
        stage: Cognitive stage (1-5 expected).
        context_mode: 'exploration' | 'exploitation' | 'skill_acquisition' | other.
        question_tier: Optional question class (tactical/strategic/meta/identity/existential).
        grounding_score: Optional grounding multiplier (AgentSelfModel derived).
        base_budget: Minimal budget for all agents.
        max_bonus: Max performance bonus scale.

    Returns:
        Dict with budget_total and component breakdown for logging.
    """

    if generation < 50:
        return {
            'budget_total': float('inf'),
            'base_budget': float('inf'),
            'performance_bonus': 0.0,
            'stage_multiplier': 1.0,
            'context_modifier': 1.0,
            'question_bonus': 0.0,
            'grounding_multiplier': 1.0,
        }

    perf_bonus = _clamp(performance_percentile, 0.0, 1.0) * max_bonus

    stage_multiplier = {
        1: 1.0,
        2: 1.2,
        3: 1.5,
        4: 2.0,
        5: 3.0,
    }.get(stage, 1.0)

    context_modifier = {
        'exploitation': 0.3,
        'exploration': 2.0,
        'skill_acquisition': 1.5,
    }.get(context_mode, 1.0)

    question_bonus_lookup = {
        'tactical': 0.0,
        'strategic': 0.1,
        'meta': 0.15,
        'identity': 0.25,
        'existential': 0.4,
    }
    question_bonus = question_bonus_lookup.get(question_tier or '', 0.0)

    grounding_multiplier = _clamp(
        grounding_score if grounding_score is not None else 1.0,
        MIN_GROUNDING,
        MAX_GROUNDING,
    )

    budget_total = (base_budget + perf_bonus) * stage_multiplier * context_modifier
    budget_total = (budget_total + question_bonus) * grounding_multiplier

    return {
        'budget_total': budget_total,
        'base_budget': base_budget,
        'performance_bonus': perf_bonus,
        'stage_multiplier': stage_multiplier,
        'context_modifier': context_modifier,
        'question_bonus': question_bonus,
        'grounding_multiplier': grounding_multiplier,
    }


# =============================================================================
# ENHANCED IMAGINATION BUDGET (from agent_consciousness_synthesis.md)
# =============================================================================
# Budget decreases on poor performance -> fewer personas allowed
# Budget increases on wins -> more cognitive exploration allowed
# =============================================================================

class ImaginationBudgetManager:
    """
    Manages imagination budget with performance-based adjustments.
    
    Key Features:
    - Budget decreases on poor performance (fewer personas allowed)
    - Budget increases on wins (more cognitive exploration allowed)
    - Gates synthesis by grounding_score
    - Tracks budget over time for adaptive control
    """
    
    def __init__(self, initial_budget: float = 1.0):
        self.current_budget = initial_budget
        self.base_budget = initial_budget
        self.min_budget = 0.1
        self.max_budget = 3.0
        
        # Performance tracking
        self.recent_outcomes: list = []  # List of (score, timestamp)
        self.max_history = 50
        
        # Win/loss tracking for adjustment
        self.consecutive_zeros = 0
        self.consecutive_wins = 0
    
    def update_from_outcome(self, score: int, is_win: bool = False) -> float:
        """
        Update budget based on game outcome.
        
        Args:
            score: Final score from game
            is_win: Whether this was a full win
            
        Returns:
            New budget value
        """
        import time
        
        # Track outcome
        self.recent_outcomes.append((score, time.time()))
        if len(self.recent_outcomes) > self.max_history:
            self.recent_outcomes = self.recent_outcomes[-self.max_history:]
        
        # Update streaks
        if score == 0:
            self.consecutive_zeros += 1
            self.consecutive_wins = 0
        elif is_win:
            self.consecutive_wins += 1
            self.consecutive_zeros = 0
        else:
            # Positive score but not win
            self.consecutive_zeros = 0
            self.consecutive_wins = 0
        
        # Adjust budget
        if self.consecutive_zeros >= 3:
            # Poor performance - reduce budget (fewer personas/speculation)
            decay = 0.9 ** (self.consecutive_zeros - 2)
            self.current_budget = max(self.min_budget, self.current_budget * decay)
        
        elif self.consecutive_wins >= 2:
            # Good performance - increase budget (more exploration allowed)
            boost = 1.1 ** min(self.consecutive_wins, 5)
            self.current_budget = min(self.max_budget, self.current_budget * boost)
        
        elif score > 0:
            # Positive progress - slight recovery
            self.current_budget = min(self.base_budget, self.current_budget * 1.05)
        
        return self.current_budget
    
    def get_persona_allowance(self) -> int:
        """
        Get how many personas are allowed given current budget.
        
        Budget -> Persona count mapping:
        - < 0.3: Only 3 personas (minimal)
        - 0.3-0.7: Up to 6 personas
        - 0.7-1.0: Up to 9 personas
        - > 1.0: Up to 12 personas (max)
        """
        if self.current_budget < 0.3:
            return 3
        elif self.current_budget < 0.7:
            return 6
        elif self.current_budget <= 1.0:
            return 9
        else:
            return 12
    
    def can_speculate(self, grounding_score: float = 1.0) -> bool:
        """
        Check if speculation (ungrounded thinking) is allowed.
        
        Low grounding + low budget = no speculation allowed.
        """
        if self.current_budget < 0.3:
            # Low budget - only allow well-grounded thinking
            return grounding_score >= 0.7
        elif self.current_budget < 0.7:
            return grounding_score >= 0.5
        else:
            # High budget - speculation allowed
            return True
    
    def can_spawn_investigator(self) -> bool:
        """Check if we have budget to spawn investigating personas."""
        return self.current_budget >= 0.5
    
    def get_synthesis_depth(self) -> int:
        """
        Get how many personas can participate in synthesis.
        
        More budget = deeper synthesis with more voices.
        """
        if self.current_budget < 0.3:
            return 2  # Minimal synthesis
        elif self.current_budget < 0.7:
            return 3
        elif self.current_budget <= 1.0:
            return 4
        else:
            return 5  # Full synthesis
    
    def reset_budget(self) -> None:
        """Reset budget to base value (e.g., on new level)."""
        self.current_budget = self.base_budget
        self.consecutive_zeros = 0
        self.consecutive_wins = 0
    
    def get_stats(self) -> Dict[str, float]:
        """Get current budget statistics."""
        avg_recent_score = 0.0
        if self.recent_outcomes:
            avg_recent_score = sum(o[0] for o in self.recent_outcomes) / len(self.recent_outcomes)
        
        return {
            'current_budget': self.current_budget,
            'base_budget': self.base_budget,
            'persona_allowance': self.get_persona_allowance(),
            'can_speculate': self.can_speculate(),
            'synthesis_depth': self.get_synthesis_depth(),
            'consecutive_zeros': self.consecutive_zeros,
            'consecutive_wins': self.consecutive_wins,
            'avg_recent_score': avg_recent_score
        }
