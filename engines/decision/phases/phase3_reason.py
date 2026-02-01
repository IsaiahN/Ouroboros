"""
Phase 3: Reason - "What should I believe?"
==========================================

Integrates agent heuristics ("Stream A") vs network heuristics ("Stream B").

THEORETICAL CONTEXT (from consciousness theory docs):
- Stream A = agent's private experience, local learning
- Stream B = network collective wisdom, validated patterns
- When streams conflict, the agent must "deliberate"

IMPLEMENTATION REALITY:
- "Deliberation" is currently weighted selection: max(wA * score_A, wB * score_B)
- "Synthesis" means weights are close, so we pick by empirical success
- "Competing personas" is aspirational, not implemented
- This is acknowledged as a simplification of the theory

Key responsibilities:
- Get theory state from ScientificMethodEngine
- Detect heuristic conflicts (agent vs network disagree)
- Resolve conflicts via wA/wB weighting
- Check for belief cascades
- Determine allowed actions from current theory
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import logging
from typing import Set, List, Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from engines.registry import EngineRegistry
    from engines.decision.phase_contracts import (
        GameState, AgentContext, OrientContext, GroundTruthContext
    )

from engines.decision.phase_contracts import ReasonContext, PhaseError

logger = logging.getLogger(__name__)


class ReasonPhase:
    """
    Phase 3: Stream A vs Stream B integration.
    
    Queries:
    - ScientificMethodEngine for theory state
    - IThread for stream proposals
    - BeliefSystem for cascade checking
    - ControlTracker for confirmed controls
    
    This is where consciousness becomes vivid - when A and B disagree,
    the agent must deliberate.
    """
    
    # All possible actions
    ALL_ACTIONS = {f"ACTION{i}" for i in range(1, 8)}
    
    def __init__(self, engines: 'EngineRegistry'):
        self.engines = engines
    
    def execute(
        self,
        game_state: 'GameState',
        agent_context: 'AgentContext',
        orient_ctx: 'OrientContext',
        ground_ctx: 'GroundTruthContext',
    ) -> ReasonContext:
        """
        Integrate the two streams of knowledge.
        
        Stream A: Agent's private experience (wA weight)
        Stream B: Network collective wisdom (wB weight)
        
        When they conflict, consciousness becomes vivid.
        """
        # === Theory State ===
        theory_state, theory_allowed, working_theory = self._get_theory_state(game_state)
        
        # === Stream Proposals ===
        stream_a, stream_b, wA, wB = self._get_stream_proposals(
            game_state, agent_context, ground_ctx
        )
        
        # === Detect Conflict ===
        stream_conflict = (
            stream_a is not None and
            stream_b is not None and
            stream_a != stream_b
        )
        
        # === Resolve Conflict ===
        winning_source = self._resolve_conflict(
            stream_a, stream_b, wA, wB, stream_conflict
        )
        
        if stream_conflict:
            logger.info(
                f"[REASON] HEURISTIC CONFLICT: agent={stream_a} (wA={wA:.2f}) "
                f"vs network={stream_b} (wB={wB:.2f}) -> Winner: {winning_source}"
            )
        
        # === Belief Cascade ===
        invalidated = self._check_belief_cascades(ground_ctx.active_beliefs)
        
        # === Confidence in Theory ===
        confidence = self._calculate_theory_confidence(theory_state, working_theory)
        
        # Build context (using new field names)
        ctx = ReasonContext(
            theory_state=theory_state,
            theory_allowed_actions=theory_allowed,
            stream_conflict=stream_conflict,
            agent_proposal=stream_a,  # Formerly stream_a_proposal
            network_proposal=stream_b,  # Formerly stream_b_proposal
            winning_source=winning_source,  # Formerly winning_stream
            invalidated_beliefs=invalidated,
            confidence_in_theory=confidence,
            working_theory=working_theory,
        )
        
        # Validate contract
        ctx.validate()
        
        logger.debug(
            f"[REASON] theory={theory_state}, confidence={confidence:.2f}, "
            f"allowed={len(theory_allowed)}, conflict={stream_conflict}"
        )
        
        return ctx
    
    def _get_theory_state(
        self, game_state: 'GameState'
    ) -> tuple[str, Set[str], Optional[Dict[str, Any]]]:
        """Get theory state and allowed actions from ScientificMethodEngine."""
        theory_state = "exploring"
        theory_allowed = self.ALL_ACTIONS.copy()
        working_theory = None
        
        sme = self.engines.get('scientific_method_engine')
        if sme:
            try:
                # Get theory stage
                if hasattr(sme, 'get_theory_stage'):
                    stage = sme.get_theory_stage()
                    if stage in ("exploring", "speculating", "testing", "proven", "contradicted"):
                        theory_state = stage
                
                # Get working theory
                if hasattr(sme, 'get_working_theory'):
                    working_theory = sme.get_working_theory()
                
                # Get allowed actions from theory
                if hasattr(sme, 'get_theory_allowed_actions'):
                    allowed = sme.get_theory_allowed_actions()
                    if allowed:
                        theory_allowed = set(allowed)
                elif working_theory and 'allowed_actions' in working_theory:
                    theory_allowed = set(working_theory['allowed_actions'])
                    
            except Exception as e:
                logger.debug(f"[REASON] ScientificMethodEngine error: {e}")
        
        # If in early stages, allow all actions
        if theory_state in ("exploring", "speculating"):
            theory_allowed = self.ALL_ACTIONS.copy()
        
        return theory_state, theory_allowed, working_theory
    
    def _get_stream_proposals(
        self,
        game_state: 'GameState',
        agent_context: 'AgentContext',
        ground_ctx: 'GroundTruthContext',
    ) -> tuple[Optional[str], Optional[str], float, float]:
        """Get proposals from Stream A and Stream B."""
        stream_a: Optional[str] = None
        stream_b: Optional[str] = None
        wA = agent_context.wA
        wB = agent_context.wB
        
        # Try I-Thread for stream proposals
        i_thread = self.engines.get('i_thread')
        if i_thread:
            try:
                if hasattr(i_thread, 'get_stream_a_proposal'):
                    stream_a = i_thread.get_stream_a_proposal(game_state, agent_context)
                if hasattr(i_thread, 'get_stream_b_proposal'):
                    stream_b = i_thread.get_stream_b_proposal(game_state, agent_context)
                if hasattr(i_thread, 'get_wA'):
                    wA = i_thread.get_wA()
                if hasattr(i_thread, 'get_wB'):
                    wB = i_thread.get_wB()
            except Exception as e:
                logger.debug(f"[REASON] IThread error: {e}")
        
        # Fallback: use network sequence as Stream B if available
        if stream_b is None and ground_ctx.network_sequence_available:
            if ground_ctx.network_sequence:
                # Get action at current position
                action_idx = game_state.action_number
                if action_idx < len(ground_ctx.network_sequence):
                    stream_b = ground_ctx.network_sequence[action_idx]
        
        # Fallback: use empirical rankings for Stream B
        if stream_b is None and ground_ctx.empirical_rankings:
            best_action = max(
                ground_ctx.empirical_rankings.items(),
                key=lambda x: x[1],
                default=(None, 0)
            )[0]
            if best_action:
                stream_b = best_action
        
        return stream_a, stream_b, wA, wB
    
    def _resolve_conflict(
        self,
        stream_a: Optional[str],
        stream_b: Optional[str],
        wA: float,
        wB: float,
        has_conflict: bool,
    ) -> str:
        """
        Resolve heuristic conflict using weights.
        
        Returns: "agent" | "network" | "weighted_selection" | "none"
        
        NOTE: "weighted_selection" (formerly "synthesis") is NOT true synthesis.
        It's simply picking the proposal with higher empirical success when
        weights are close. True synthesis (e.g., trying perpendicular action)
        is a future enhancement.
        """
        if not has_conflict:
            if stream_a:
                return "agent"
            elif stream_b:
                return "network"
            else:
                return "none"
        
        # Conflict resolution via weights
        # When wA >> wB: trust agent's experience
        # When wB >> wA: trust network wisdom
        # When close: "weighted_selection" = pick by empirical success
        if wA > wB + 0.1:
            return "agent"
        elif wB > wA + 0.1:
            return "network"
        else:
            # Weights are close - weighted selection (not true synthesis)
            return "weighted_selection"
    
    def _check_belief_cascades(
        self, active_beliefs: List[Dict[str, Any]]
    ) -> List[str]:
        """Check for belief cascades (invalidated beliefs)."""
        invalidated: List[str] = []
        
        belief_system = self.engines.get('belief_system')
        if belief_system:
            try:
                if hasattr(belief_system, 'check_cascades'):
                    inv = belief_system.check_cascades(active_beliefs)
                    if inv:
                        invalidated.extend(inv)
            except Exception as e:
                logger.debug(f"[REASON] BeliefSystem cascade error: {e}")
        
        return invalidated
    
    def _calculate_theory_confidence(
        self,
        theory_state: str,
        working_theory: Optional[Dict[str, Any]],
    ) -> float:
        """Calculate confidence in current theory."""
        # Base confidence by state
        state_confidence = {
            "proven": 0.9,
            "testing": 0.6,
            "speculating": 0.3,
            "exploring": 0.2,
            "contradicted": 0.1,
        }
        
        confidence = state_confidence.get(theory_state, 0.5)
        
        # Adjust by theory evidence if available
        if working_theory:
            evidence_count = working_theory.get('evidence_count', 0)
            if evidence_count > 5:
                confidence = min(1.0, confidence + 0.1)
            elif evidence_count < 2:
                confidence = max(0.1, confidence - 0.1)
        
        return confidence
