"""
Phase 7: Select - "Final weighted decision"
===========================================

The I-Thread weaver. Combines ALL phase outputs into final action.
NO early returns reach here (except emergency). ALL phases have contributed.

This is the SINGLE point where an action is chosen.

Weight calculation:
    final_weight = (
        proposal_confidence *
        safety_multiplier *
        (1 + resonance_bonus) *
        stream_weight_factor *
        (1 + mortality_urgency_bonus if high_stakes else 1)
    )
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import random
import logging
from typing import Dict, List, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from engines.registry import EngineRegistry
    from engines.decision.phase_contracts import (
        GameState, AgentContext, FilteredContext
    )

from engines.decision.phase_contracts import FinalDecision, Proposal

logger = logging.getLogger(__name__)


class SelectPhase:
    """
    Phase 7: Final action selection - the I-Thread weaver.
    
    Combines:
    - Proposal confidence (from Phase 5)
    - Safety multipliers (from Phase 6)
    - Resonance bonus (from Phase 4)
    - Stream weight factor (from Phase 3)
    - Mortality urgency (from Phase 1)
    """
    
    # Selection thresholds
    CONFIDENCE_THRESHOLD = 0.4  # Below this -> weighted random
    MIN_CONFIDENCE = 0.1  # Minimum confidence floor
    
    # All actions for fallback
    ALL_ACTIONS = [f"ACTION{i}" for i in range(1, 8)]
    
    def __init__(self, engines: 'EngineRegistry'):
        self.engines = engines
    
    def execute(
        self,
        game_state: 'GameState',
        agent_context: 'AgentContext',
        filtered_ctx: 'FilteredContext',
        audit: Dict[str, Any],
    ) -> FinalDecision:
        """
        Final weighted selection.
        
        This is the ONLY place where action is chosen.
        Returns FinalDecision with full audit trail.
        """
        # Handle empty proposals
        if not filtered_ctx.filtered_proposals:
            logger.warning("[SELECT] No proposals survived filtering, using fallback")
            return self._fallback_decision(game_state, audit)
        
        # Calculate final weights
        final_weights = self._calculate_final_weights(
            filtered_ctx, audit, agent_context
        )
        
        # Get gut instinct (top proposal before weighting)
        gut_instinct = filtered_ctx.filtered_proposals[0].action
        
        # Select action
        selected_action, selection_method = self._select_action(final_weights)
        
        # Did deliberation change the answer?
        deliberation_changed = (selected_action != gut_instinct)
        
        # Build reasoning
        reasoning = self._build_reasoning(
            selected_action,
            final_weights,
            selection_method,
            audit,
            deliberation_changed,
        )
        
        decision = FinalDecision(
            action=selected_action,
            confidence=final_weights.get(selected_action, 0.0),
            reasoning=reasoning,
            audit_trail=audit,
            gut_instinct=gut_instinct,
            deliberation_changed=deliberation_changed,
            selection_method=selection_method,
        )
        
        # Validate contract
        decision.validate()
        
        logger.info(
            f"[SELECT] {selected_action} (conf={final_weights.get(selected_action, 0):.2f}, "
            f"method={selection_method}, changed={deliberation_changed})"
        )
        
        return decision
    
    def _calculate_final_weights(
        self,
        filtered_ctx: 'FilteredContext',
        audit: Dict[str, Any],
        agent_context: 'AgentContext',
    ) -> Dict[str, float]:
        """Calculate final weights for all proposals."""
        final_weights: Dict[str, float] = {}
        
        # Extract phase contexts from audit
        orient = audit.get('phases', {}).get('orient', {})
        reason = audit.get('phases', {}).get('reason', {})
        pattern = audit.get('phases', {}).get('pattern', {})
        
        # Get contextual factors
        mortality = orient.get('mortality_pressure', 0.0)
        resonance = pattern.get('resonance_score', 0.0)
        winning_stream = reason.get('winning_stream', 'none')
        
        for proposal in filtered_ctx.filtered_proposals:
            action = proposal.action
            
            # Base: proposal confidence
            weight = max(self.MIN_CONFIDENCE, proposal.confidence)
            
            # Factor 1: Safety multiplier
            safety = filtered_ctx.safety_multipliers.get(action, 1.0)
            weight *= safety
            
            # Factor 2: Resonance bonus (up to 20% boost)
            weight *= (1.0 + resonance * 0.2)
            
            # Factor 3: Stream alignment bonus
            if winning_stream == "A" and "stream_a" in proposal.source:
                weight *= 1.1
            elif winning_stream == "B" and ("stream_b" in proposal.source or
                                            "network" in proposal.source or
                                            "proven" in proposal.source):
                weight *= 1.1
            
            # Factor 4: Mortality urgency
            if mortality > 0.7:
                # High stakes - boost proven/safe actions
                if proposal.source in ("proven_sequence", "network_wisdom"):
                    weight *= (1.0 + mortality * 0.3)
                # Penalize exploration when dying
                elif proposal.source in ("discovery", "random"):
                    weight *= (1.0 - mortality * 0.3)
            
            # Factor 5: Agent type adjustment
            if agent_context.agent_type == "Pioneer":
                # Pioneers favor exploration
                if proposal.source in ("discovery", "pattern_universal"):
                    weight *= 1.1
            elif agent_context.agent_type == "Optimizer":
                # Optimizers favor proven paths
                if proposal.source in ("proven_sequence", "network_wisdom"):
                    weight *= 1.1
            elif agent_context.agent_type == "Exploiter":
                # Exploiters ignore social norms
                if agent_context.social_rule_adherence < 0.5:
                    # Sociopathic - discount network wisdom
                    if "network" in proposal.source:
                        weight *= 0.8
            
            final_weights[action] = weight
        
        return final_weights
    
    def _select_action(
        self, final_weights: Dict[str, float]
    ) -> tuple[str, str]:
        """Select action from weighted proposals."""
        if not final_weights:
            return random.choice(self.ALL_ACTIONS), "empty_fallback"
        
        # Find max weight
        max_action = max(final_weights, key=final_weights.get)
        max_weight = final_weights[max_action]
        
        # High confidence -> deterministic
        if max_weight >= self.CONFIDENCE_THRESHOLD:
            return max_action, "max_confidence"
        
        # Low confidence -> weighted random from top 3
        sorted_actions = sorted(final_weights.items(), key=lambda x: -x[1])[:3]
        selected = self._weighted_random(sorted_actions)
        return selected, "weighted_random"
    
    def _weighted_random(
        self, weighted_actions: List[tuple[str, float]]
    ) -> str:
        """Select action with probability proportional to weight."""
        if not weighted_actions:
            return random.choice(self.ALL_ACTIONS)
        
        # Normalize weights
        total = sum(w for _, w in weighted_actions)
        if total <= 0:
            return weighted_actions[0][0]
        
        # Random selection
        r = random.random() * total
        cumulative = 0.0
        for action, weight in weighted_actions:
            cumulative += weight
            if r <= cumulative:
                return action
        
        return weighted_actions[-1][0]
    
    def _fallback_decision(
        self,
        game_state: 'GameState',
        audit: Dict[str, Any],
    ) -> FinalDecision:
        """Create fallback decision when no proposals available."""
        # Try to avoid recent actions
        recent = []
        if game_state.previous_action:
            recent.append(game_state.previous_action)
        
        available = [a for a in self.ALL_ACTIONS if a not in recent]
        if not available:
            available = self.ALL_ACTIONS
        
        action = random.choice(available)
        
        return FinalDecision(
            action=action,
            confidence=0.1,
            reasoning="FALLBACK: No proposals survived filtering",
            audit_trail=audit,
            gut_instinct="none",
            deliberation_changed=True,
            selection_method="fallback_random",
        )
    
    def _build_reasoning(
        self,
        action: str,
        weights: Dict[str, float],
        method: str,
        audit: Dict[str, Any],
        deliberation_changed: bool,
    ) -> str:
        """Build human-readable reasoning for the decision."""
        parts = [f"Selected {action} via {method}"]
        
        # Add confidence
        parts.append(f"weight={weights.get(action, 0):.3f}")
        
        # Note if deliberation changed answer
        if deliberation_changed:
            parts.append("(deliberation changed gut instinct)")
        
        # Add phase highlights
        reason = audit.get('phases', {}).get('reason', {})
        if reason.get('stream_conflict'):
            parts.append(f"stream_conflict->winner={reason.get('winning_stream')}")
        
        pattern = audit.get('phases', {}).get('pattern', {})
        if pattern.get('cods_suggestion'):
            parts.append("CODS_suggested")
        if pattern.get('resonance_score', 0) > 0.3:
            parts.append(f"resonance={pattern.get('resonance_score', 0):.2f}")
        
        orient = audit.get('phases', {}).get('orient', {})
        if orient.get('mortality_pressure', 0) > 0.5:
            parts.append(f"mortality={orient.get('mortality_pressure', 0):.2f}")
        
        return " | ".join(parts)
