"""
Phase 6: Filter - "Remove bad options"
======================================

Applies safety filters to proposals:
1. ThreeLayerFilter: Cache/proven/danger checks
2. PariahFilter: Remove pariah-matching actions
3. TerminalFilter: Suppress death-approaching actions
4. OscillationFilter: Break coordinate oscillation cycles
5. TheoryGate: Final theory compliance check

This phase answers: "Which proposals are actually safe to execute?"
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import logging
from typing import Dict, List, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from engines.registry import EngineRegistry
    from engines.decision.phase_contracts import (
        GameState, AgentContext, GroundTruthContext, ReasonContext, ProposalContext
    )

from engines.decision.phase_contracts import FilteredContext, Proposal

logger = logging.getLogger(__name__)


class FilterPhase:
    """
    Phase 6: Apply safety filters to proposals.
    
    Filters (in order):
    1. Pariah filter - remove actions marked as pariah
    2. Terminal filter - reduce confidence for death-approaching actions
    3. Oscillation filter - detect and break cycles
    4. Theory gate - ensure theory compliance
    
    Also calculates safety multipliers for Phase 7 weighting.
    """
    
    def __init__(self, engines: 'EngineRegistry'):
        self.engines = engines
        self._recent_positions: List[tuple] = []
        self._recent_actions: List[str] = []
    
    def execute(
        self,
        game_state: 'GameState',
        agent_context: 'AgentContext',
        ground_ctx: 'GroundTruthContext',
        reason_ctx: 'ReasonContext',
        proposal_ctx: 'ProposalContext',
    ) -> FilteredContext:
        """
        Filter proposals through safety gates.
        
        Returns filtered proposals with removal reasons and safety multipliers.
        """
        # Track recent actions for oscillation detection
        self._update_tracking(game_state)
        
        proposals = list(proposal_ctx.ranked_proposals)
        removed: Dict[str, str] = {}
        safety_multipliers: Dict[str, float] = {}
        
        # Initialize safety multipliers from ground truth
        for action in [f"ACTION{i}" for i in range(1, 8)]:
            safety_multipliers[action] = ground_ctx.action_safety_weights.get(action, 1.0)
        
        # === Filter 1: Pariah Filter ===
        proposals, removed_pariah = self._filter_pariahs(
            proposals, ground_ctx.pariah_actions
        )
        removed.update(removed_pariah)
        
        # === Filter 2: Terminal Filter ===
        proposals, safety_adj = self._filter_terminal(
            proposals, ground_ctx, game_state
        )
        for action, adj in safety_adj.items():
            safety_multipliers[action] = safety_multipliers.get(action, 1.0) * adj
        
        # === Filter 3: Oscillation Filter ===
        proposals, removed_osc = self._filter_oscillation(proposals, game_state)
        removed.update(removed_osc)
        
        # === Filter 4: Theory Gate ===
        proposals, removed_theory = self._filter_theory_gate(
            proposals, reason_ctx.theory_allowed_actions
        )
        removed.update(removed_theory)
        
        # Ensure at least one proposal survives
        if not proposals and proposal_ctx.ranked_proposals:
            # Restore lowest-risk proposal
            best = min(
                proposal_ctx.ranked_proposals,
                key=lambda p: ground_ctx.action_safety_weights.get(p.action, 1.0)
            )
            proposals = [best]
            logger.warning(
                f"[FILTER] All proposals filtered, restoring: {best.action}"
            )
        
        # Build context
        ctx = FilteredContext(
            filtered_proposals=proposals,
            removed_actions=removed,
            safety_multipliers=safety_multipliers,
        )
        
        # Validate contract
        ctx.validate()
        
        original_count = len(proposal_ctx.ranked_proposals)
        filtered_count = len(proposals)
        logger.debug(
            f"[FILTER] {original_count} -> {filtered_count} proposals, "
            f"removed={len(removed)}"
        )
        
        return ctx
    
    def _update_tracking(self, game_state: 'GameState') -> None:
        """Update tracking for oscillation detection."""
        if game_state.position:
            self._recent_positions.append(game_state.position)
            if len(self._recent_positions) > 10:
                self._recent_positions.pop(0)
        
        if game_state.previous_action:
            self._recent_actions.append(game_state.previous_action)
            if len(self._recent_actions) > 10:
                self._recent_actions.pop(0)
    
    def _filter_pariahs(
        self,
        proposals: List[Proposal],
        pariah_actions: Set[str],
    ) -> tuple[List[Proposal], Dict[str, str]]:
        """Remove proposals that match pariah patterns."""
        filtered: List[Proposal] = []
        removed: Dict[str, str] = {}
        
        for p in proposals:
            if p.action in pariah_actions:
                removed[p.action] = "pariah_pattern"
                logger.debug(f"[FILTER] Removed {p.action}: pariah pattern")
            else:
                filtered.append(p)
        
        return filtered, removed
    
    def _filter_terminal(
        self,
        proposals: List[Proposal],
        ground_ctx: 'GroundTruthContext',
        game_state: 'GameState',
    ) -> tuple[List[Proposal], Dict[str, float]]:
        """Adjust confidence for death-approaching actions."""
        filtered: List[Proposal] = []
        safety_adjustments: Dict[str, float] = {}
        
        # Get position death risk
        current_risk = 0.0
        if game_state.position and game_state.position in ground_ctx.death_risk_by_position:
            current_risk = ground_ctx.death_risk_by_position[game_state.position]
        
        for p in proposals:
            # Get action-specific safety weight
            safety = ground_ctx.action_safety_weights.get(p.action, 1.0)
            
            # If position is risky, reduce confidence for all actions
            if current_risk > 0.5:
                safety *= (1.0 - current_risk * 0.5)
            
            safety_adjustments[p.action] = safety
            
            # Only remove if extremely dangerous (safety < 0.1)
            if safety < 0.1:
                logger.debug(f"[FILTER] Suppressed {p.action}: terminal risk (safety={safety:.2f})")
                # Don't remove, just heavily penalize
                filtered.append(Proposal(
                    action=p.action,
                    confidence=p.confidence * safety,
                    source=p.source,
                    reasoning=f"{p.reasoning} [RISK: {safety:.2f}]",
                ))
            else:
                filtered.append(p)
        
        return filtered, safety_adjustments
    
    def _filter_oscillation(
        self,
        proposals: List[Proposal],
        game_state: 'GameState',
    ) -> tuple[List[Proposal], Dict[str, str]]:
        """Detect and break oscillation patterns."""
        filtered: List[Proposal] = []
        removed: Dict[str, str] = {}
        
        # Detect oscillation: same position repeating
        oscillating_actions: Set[str] = set()
        
        if len(self._recent_positions) >= 4:
            # Check for A-B-A-B pattern
            if (self._recent_positions[-1] == self._recent_positions[-3] and
                self._recent_positions[-2] == self._recent_positions[-4]):
                # We're oscillating - find the actions that cause this
                if len(self._recent_actions) >= 2:
                    oscillating_actions.add(self._recent_actions[-1])
                    oscillating_actions.add(self._recent_actions[-2])
        
        # Also use action handler for oscillation detection
        action_handler = self.engines.get('action_handler')
        if action_handler:
            try:
                if hasattr(action_handler, 'detect_oscillation'):
                    osc_result = action_handler.detect_oscillation(
                        recent_actions=self._recent_actions,
                        recent_positions=self._recent_positions,
                    )
                    if osc_result and osc_result.get('oscillating_actions'):
                        oscillating_actions.update(osc_result['oscillating_actions'])
            except Exception as e:
                logger.debug(f"[FILTER] Oscillation detection error: {e}")
        
        for p in proposals:
            if p.action in oscillating_actions:
                removed[p.action] = "oscillation_detected"
                logger.debug(f"[FILTER] Removed {p.action}: oscillation")
            else:
                filtered.append(p)
        
        return filtered, removed
    
    def _filter_theory_gate(
        self,
        proposals: List[Proposal],
        allowed_actions: Set[str],
    ) -> tuple[List[Proposal], Dict[str, str]]:
        """Final theory compliance check."""
        if not allowed_actions:
            # No restrictions
            return proposals, {}
        
        filtered: List[Proposal] = []
        removed: Dict[str, str] = {}
        
        for p in proposals:
            if p.action in allowed_actions:
                filtered.append(p)
            else:
                removed[p.action] = "theory_gate_violation"
                logger.debug(f"[FILTER] Removed {p.action}: theory gate")
        
        return filtered, removed
    
    def reset(self) -> None:
        """Reset tracking state for new game/level."""
        self._recent_positions.clear()
        self._recent_actions.clear()
