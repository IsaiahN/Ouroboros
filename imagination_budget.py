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
