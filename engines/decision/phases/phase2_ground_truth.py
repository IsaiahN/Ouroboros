"""
Phase 2: Ground Truth - "What do I empirically know?"
=====================================================

Queries the DATABASE for validated facts:
- Network wisdom (what actions worked historically)
- Terminal patterns (what leads to death)
- Object valences (positive/negative/neutral)
- Active beliefs
- Pariah patterns (what to avoid)

This is EMPIRICAL knowledge from the network, not guesses.
The database is the AGI - this phase queries it.
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import logging
from typing import Dict, List, Set, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from engines.registry import EngineRegistry
    from engines.decision.phase_contracts import GameState, AgentContext, OrientContext

from engines.decision.phase_contracts import GroundTruthContext, PhaseError

logger = logging.getLogger(__name__)


class GroundTruthPhase:
    """
    Phase 2: Gather empirical ground truth from database.
    
    Queries:
    - NetworkWisdom for action history
    - TerminalPatternDetector for death weights
    - ValenceGoalEngine for object valences
    - BeliefSystem for active beliefs
    - ViralPackageEngine for pariahs
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
    ) -> GroundTruthContext:
        """
        Gather ground truth from database.
        
        NEVER returns None. ALWAYS returns valid GroundTruthContext.
        Missing data -> explicit defaults with warnings logged.
        """
        # === Action Safety Weights (from terminal patterns) ===
        action_safety = self._get_action_safety(game_state)
        
        # === Empirical Rankings (from network wisdom) ===
        empirical_rankings = self._get_empirical_rankings(game_state)
        
        # === Object Valences ===
        object_valences = self._get_object_valences(game_state)
        
        # === Active Beliefs ===
        active_beliefs = self._get_active_beliefs(game_state, agent_context)
        
        # === Pariah Actions ===
        pariah_actions = self._get_pariah_actions(game_state)
        
        # === Death Risk by Position ===
        death_risk = self._get_death_risk(game_state)
        
        # === Network Sequence ===
        has_sequence, sequence = self._get_network_sequence(game_state)
        
        # Build context
        ctx = GroundTruthContext(
            action_safety_weights=action_safety,
            empirical_rankings=empirical_rankings,
            object_valences=object_valences,
            active_beliefs=active_beliefs,
            pariah_actions=pariah_actions,
            death_risk_by_position=death_risk,
            network_sequence_available=has_sequence,
            network_sequence=sequence,
        )
        
        # Validate contract
        ctx.validate()
        
        logger.debug(
            f"[GROUND_TRUTH] pariahs={len(pariah_actions)}, "
            f"beliefs={len(active_beliefs)}, has_sequence={has_sequence}"
        )
        
        return ctx
    
    def _get_action_safety(self, game_state: 'GameState') -> Dict[str, float]:
        """Get per-action safety weights from terminal pattern detector."""
        # Default: all actions safe
        safety = {action: 1.0 for action in self.ALL_ACTIONS}
        
        terminal_detector = self.engines.get('terminal_pattern_detector')
        if terminal_detector:
            try:
                # Get graduated weights (0.0 = death, 1.0 = safe)
                if hasattr(terminal_detector, 'get_graduated_action_weights'):
                    weights = terminal_detector.get_graduated_action_weights(
                        game_type=game_state.game_type,
                        level=game_state.level,
                        position=game_state.position,
                    )
                    if weights:
                        for action, weight in weights.items():
                            if action in safety:
                                safety[action] = max(0.0, min(1.0, float(weight)))
            except Exception as e:
                logger.debug(f"[GROUND_TRUTH] TerminalDetector error: {e}")
        
        return safety
    
    def _get_empirical_rankings(self, game_state: 'GameState') -> Dict[str, float]:
        """Get action rankings from network wisdom."""
        # Default: neutral rankings
        rankings = {action: 0.5 for action in self.ALL_ACTIONS}
        
        # Try network wisdom via self_model
        self_model = self.engines.get('self_model')
        if self_model:
            try:
                if hasattr(self_model, 'get_network_action_wisdom'):
                    wisdom = self_model.get_network_action_wisdom(
                        game_type=game_state.game_type,
                        level=game_state.level,
                    )
                    if wisdom:
                        for action, rank in wisdom.items():
                            if action in rankings:
                                rankings[action] = max(0.0, min(1.0, float(rank)))
            except Exception as e:
                logger.debug(f"[GROUND_TRUTH] NetworkWisdom error: {e}")
        
        return rankings
    
    def _get_object_valences(self, game_state: 'GameState') -> Dict[str, str]:
        """Get object valences (positive/negative/neutral)."""
        valences: Dict[str, str] = {}
        
        valence_engine = self.engines.get('valence_goals')
        if valence_engine:
            try:
                if hasattr(valence_engine, 'get_valences'):
                    v = valence_engine.get_valences(
                        game_id=game_state.game_id,
                        level=game_state.level,
                    )
                    if v:
                        valences.update(v)
            except Exception as e:
                logger.debug(f"[GROUND_TRUTH] ValenceEngine error: {e}")
        
        return valences
    
    def _get_active_beliefs(
        self,
        game_state: 'GameState',
        agent_context: 'AgentContext',
    ) -> List[Dict[str, Any]]:
        """Get agent's active beliefs."""
        beliefs: List[Dict[str, Any]] = []
        
        belief_system = self.engines.get('belief_system')
        if belief_system:
            try:
                if hasattr(belief_system, 'get_active_beliefs'):
                    b = belief_system.get_active_beliefs(
                        agent_id=agent_context.agent_id,
                        game_id=game_state.game_id,
                    )
                    if b:
                        beliefs.extend(b)
            except Exception as e:
                logger.debug(f"[GROUND_TRUTH] BeliefSystem error: {e}")
        
        return beliefs
    
    def _get_pariah_actions(self, game_state: 'GameState') -> Set[str]:
        """Get actions marked as pariah (to avoid)."""
        pariahs: Set[str] = set()
        
        viral_engine = self.engines.get('viral_package_engine')
        if viral_engine:
            try:
                if hasattr(viral_engine, 'get_pariahs'):
                    p = viral_engine.get_pariahs(
                        game_type=game_state.game_type,
                        level=game_state.level,
                    )
                    if p:
                        pariahs.update(p)
            except Exception as e:
                logger.debug(f"[GROUND_TRUTH] ViralPackageEngine pariahs error: {e}")
        
        return pariahs
    
    def _get_death_risk(self, game_state: 'GameState') -> Dict[tuple, float]:
        """Get death risk by position."""
        risk: Dict[tuple, float] = {}
        
        terminal_detector = self.engines.get('terminal_pattern_detector')
        if terminal_detector and game_state.position:
            try:
                if hasattr(terminal_detector, 'get_position_death_risk'):
                    r = terminal_detector.get_position_death_risk(
                        game_type=game_state.game_type,
                        level=game_state.level,
                    )
                    if r:
                        risk.update(r)
            except Exception as e:
                logger.debug(f"[GROUND_TRUTH] Death risk error: {e}")
        
        return risk
    
    def _get_network_sequence(
        self, game_state: 'GameState'
    ) -> tuple[bool, Optional[List[str]]]:
        """Check if proven network sequence exists."""
        multi_stage = self.engines.get('multi_stage_pipeline')
        if multi_stage:
            try:
                if hasattr(multi_stage, 'get_sequence_with_fallback'):
                    result = multi_stage.get_sequence_with_fallback(
                        game_id=game_state.game_id,
                        level=game_state.level,
                        action_number=game_state.action_number,
                    )
                    if result and result.get('sequence'):
                        return True, result['sequence']
            except Exception as e:
                logger.debug(f"[GROUND_TRUTH] MultiStage error: {e}")
        
        return False, None
