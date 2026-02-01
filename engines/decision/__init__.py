"""
Decision Engine - 7-Phase Decision System
==========================================

Replaces the 42-rung ladder with 7 ordered phases:
1. ORIENT - "What world am I in?"
2. GROUND TRUTH - "What do I empirically know?"
3. REASON - "What should I believe?"
4. PATTERN MATCH - "Have I seen this before?"
5. PROPOSE - "What's my best move?"
6. FILTER - "Remove bad options"
7. SELECT - "Final weighted decision"

Usage:
    from engines.decision import PhaseExecutor
    
    executor = PhaseExecutor(engine_registry, db)
    decision = executor.decide(game_state, agent_context)
    print(decision.action, decision.reasoning)
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from engines.decision.phase_contracts import (
    PhaseError,
    GameState,
    AgentContext,
    DecisionContext,  # Accumulating context wrapper
    OrientContext,
    GroundTruthContext,
    ReasonContext,
    PatternMatch,
    PatternContext,
    Proposal,
    ProposalContext,
    FilteredContext,
    FinalDecision,
)

from engines.decision.phase_executor import PhaseExecutor

__all__ = [
    'PhaseExecutor',
    'PhaseError',
    'GameState',
    'AgentContext',
    'DecisionContext',
    'OrientContext',
    'GroundTruthContext',
    'ReasonContext',
    'PatternMatch',
    'PatternContext',
    'Proposal',
    'ProposalContext',
    'FilteredContext',
    'FinalDecision',
]
