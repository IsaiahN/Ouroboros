"""
Phase 5: Propose - "What's my best move?"
=========================================

Generates action proposals from all sources:
- DiscoveryEngine for exploration actions
- NearMissAnalyzer for near-miss insights
- SubgoalPlanner for subgoal actions
- MultiStagePipeline for sequence following
- NetworkWisdom for proven actions

This phase answers: "Given everything I know, what should I do?"
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import logging
from typing import List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from engines.registry import EngineRegistry
    from engines.decision.phase_contracts import (
        GameState, AgentContext, OrientContext, GroundTruthContext,
        ReasonContext, PatternContext
    )

from engines.decision.phase_contracts import ProposalContext, Proposal, PatternMatch

logger = logging.getLogger(__name__)


class ProposePhase:
    """
    Phase 5: Generate action proposals.
    
    Sources:
    - DiscoveryEngine (if in discovery phase)
    - NearMissAnalyzer
    - SubgoalPlanner
    - MultiStagePipeline (proven sequences)
    - Pattern matches from Phase 4
    - NetworkWisdom
    
    All proposals are filtered by theory_allowed_actions.
    """
    
    # All possible actions
    ALL_ACTIONS = [f"ACTION{i}" for i in range(1, 8)]
    
    def __init__(self, engines: 'EngineRegistry'):
        self.engines = engines
    
    def execute(
        self,
        game_state: 'GameState',
        agent_context: 'AgentContext',
        orient_ctx: 'OrientContext',
        ground_ctx: 'GroundTruthContext',
        reason_ctx: 'ReasonContext',
        pattern_ctx: 'PatternContext',
    ) -> ProposalContext:
        """
        Generate ranked action proposals.
        
        Combines proposals from all sources, filters by theory, ranks by confidence.
        """
        proposals: List[Proposal] = []
        discovery_override: Optional[str] = None
        subgoal_active = False
        current_subgoal: Optional[str] = None
        
        # Get allowed actions from theory
        allowed = reason_ctx.theory_allowed_actions
        if not allowed:
            allowed = set(self.ALL_ACTIONS)
        
        # === Discovery Override (highest priority if in discovery phase) ===
        if orient_ctx.discovery_phase in ("movement_test", "click_survey"):
            discovery_action = self._get_discovery_action(game_state, orient_ctx)
            if discovery_action and discovery_action in allowed:
                discovery_override = discovery_action
                proposals.append(Proposal(
                    action=discovery_action,
                    confidence=0.9,  # High confidence for discovery
                    source="discovery",
                    reasoning=f"Discovery phase: {orient_ctx.discovery_phase}",
                ))
        
        # === Proven Sequence (if available) ===
        if ground_ctx.network_sequence_available and ground_ctx.network_sequence:
            seq_action = self._get_sequence_action(game_state, ground_ctx)
            if seq_action and seq_action in allowed:
                proposals.append(Proposal(
                    action=seq_action,
                    confidence=0.85,
                    source="proven_sequence",
                    reasoning="Following proven network sequence",
                ))
        
        # === Pattern Matches from Phase 4 ===
        for pm in pattern_ctx.pattern_suggestions:
            if pm.action in allowed:
                proposals.append(Proposal(
                    action=pm.action,
                    confidence=pm.confidence * 0.9,  # Slight discount vs proven
                    source=f"pattern_{pm.source}",
                    reasoning=pm.evidence,
                ))
        
        # === Subgoal Action ===
        subgoal_action, subgoal_name = self._get_subgoal_action(game_state)
        if subgoal_action and subgoal_action in allowed:
            subgoal_active = True
            current_subgoal = subgoal_name
            proposals.append(Proposal(
                action=subgoal_action,
                confidence=0.7,
                source="subgoal",
                reasoning=f"Working toward subgoal: {subgoal_name}",
            ))
        
        # === Near-Miss Insights ===
        near_miss_action = self._get_near_miss_action(game_state)
        if near_miss_action and near_miss_action in allowed:
            proposals.append(Proposal(
                action=near_miss_action,
                confidence=0.65,
                source="near_miss",
                reasoning="Near-miss analysis suggests this action",
            ))
        
        # === Stream Winner Proposal ===
        stream_action = self._get_stream_winner_action(reason_ctx)
        if stream_action and stream_action in allowed:
            # Check if already proposed
            existing = [p for p in proposals if p.action == stream_action]
            if not existing:
                proposals.append(Proposal(
                    action=stream_action,
                    confidence=0.6,
                    source=f"stream_{reason_ctx.winning_stream.lower()}",
                    reasoning=f"Stream {reason_ctx.winning_stream} suggests this",
                ))
        
        # === Network Wisdom (empirical rankings) ===
        wisdom_proposals = self._get_wisdom_proposals(ground_ctx, allowed)
        for wp in wisdom_proposals:
            # Check if already proposed
            existing = [p for p in proposals if p.action == wp.action]
            if not existing:
                proposals.append(wp)
        
        # === Fallback: random from allowed ===
        if not proposals:
            import random
            fallback = random.choice(list(allowed) if allowed else self.ALL_ACTIONS)
            proposals.append(Proposal(
                action=fallback,
                confidence=0.3,
                source="random_fallback",
                reasoning="No confident proposals, using random from allowed",
            ))
        
        # === Sort by confidence ===
        proposals.sort(key=lambda x: -x.confidence)
        
        # === Deduplicate (keep highest confidence for each action) ===
        seen_actions: Set[str] = set()
        unique_proposals: List[Proposal] = []
        for p in proposals:
            if p.action not in seen_actions:
                seen_actions.add(p.action)
                unique_proposals.append(p)
        
        # Build context
        ctx = ProposalContext(
            ranked_proposals=unique_proposals,
            discovery_override=discovery_override,
            subgoal_active=subgoal_active,
            current_subgoal=current_subgoal,
        )
        
        # Validate contract
        ctx.validate()
        
        logger.debug(
            f"[PROPOSE] proposals={len(unique_proposals)}, "
            f"discovery_override={discovery_override}, subgoal={subgoal_active}"
        )
        
        return ctx
    
    def _get_discovery_action(
        self,
        game_state: 'GameState',
        orient_ctx: 'OrientContext',
    ) -> Optional[str]:
        """Get next action from discovery engine."""
        discovery_engine = self.engines.get('discovery_engine')
        if discovery_engine:
            try:
                if hasattr(discovery_engine, 'get_next_target'):
                    result = discovery_engine.get_next_target(
                        game_id=game_state.game_id,
                        level=game_state.level,
                        phase=orient_ctx.discovery_phase,
                    )
                    if result:
                        return result.get('action') or result.get('next_action')
            except Exception as e:
                logger.debug(f"[PROPOSE] DiscoveryEngine error: {e}")
        
        return None
    
    def _get_sequence_action(
        self,
        game_state: 'GameState',
        ground_ctx: 'GroundTruthContext',
    ) -> Optional[str]:
        """Get action from proven sequence."""
        if ground_ctx.network_sequence:
            idx = game_state.action_number
            if 0 <= idx < len(ground_ctx.network_sequence):
                return ground_ctx.network_sequence[idx]
        return None
    
    def _get_subgoal_action(
        self, game_state: 'GameState'
    ) -> tuple[Optional[str], Optional[str]]:
        """Get action toward current subgoal."""
        subgoal_planner = self.engines.get('subgoal_planner')
        if subgoal_planner:
            try:
                if hasattr(subgoal_planner, 'get_current_subgoal'):
                    result = subgoal_planner.get_current_subgoal(
                        game_id=game_state.game_id,
                        level=game_state.level,
                    )
                    if result:
                        action = result.get('next_action') or result.get('action')
                        name = result.get('subgoal_name', 'unknown')
                        return action, name
            except Exception as e:
                logger.debug(f"[PROPOSE] SubgoalPlanner error: {e}")
        
        return None, None
    
    def _get_near_miss_action(self, game_state: 'GameState') -> Optional[str]:
        """Get action from near-miss analysis."""
        near_miss = self.engines.get('near_miss_analyzer')
        if near_miss:
            try:
                if hasattr(near_miss, 'get_insights'):
                    result = near_miss.get_insights(
                        game_id=game_state.game_id,
                        level=game_state.level,
                    )
                    if result and result.get('suggested_action'):
                        return result['suggested_action']
            except Exception as e:
                logger.debug(f"[PROPOSE] NearMissAnalyzer error: {e}")
        
        return None
    
    def _get_stream_winner_action(self, reason_ctx: 'ReasonContext') -> Optional[str]:
        """Get action from winning stream."""
        if reason_ctx.winning_stream == "A":
            return reason_ctx.stream_a_proposal
        elif reason_ctx.winning_stream == "B":
            return reason_ctx.stream_b_proposal
        elif reason_ctx.winning_stream == "synthesis":
            # Return whichever is available, prefer B (network) for synthesis
            return reason_ctx.stream_b_proposal or reason_ctx.stream_a_proposal
        return None
    
    def _get_wisdom_proposals(
        self,
        ground_ctx: 'GroundTruthContext',
        allowed: Set[str],
    ) -> List[Proposal]:
        """Get proposals from empirical rankings."""
        proposals: List[Proposal] = []
        
        # Sort by ranking, take top 3
        sorted_rankings = sorted(
            ground_ctx.empirical_rankings.items(),
            key=lambda x: -x[1]
        )
        
        for action, rank in sorted_rankings[:3]:
            if action in allowed and rank > 0.3:  # Only include if decent ranking
                proposals.append(Proposal(
                    action=action,
                    confidence=rank * 0.7,  # Discount vs other sources
                    source="network_wisdom",
                    reasoning=f"Network empirical ranking: {rank:.2f}",
                ))
        
        return proposals
