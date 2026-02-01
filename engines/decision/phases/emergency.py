"""
Emergency Check - Pre-Phase Safety Gates
========================================

Runs BEFORE all phases. The ONLY place where early-exit is allowed.

Two emergency conditions:
1. LoopBreaker: If stuck N+ actions -> random action (default: 15)
2. FrustrationOverride: If frustrated M+ actions -> force exploration (default: 20)

Thresholds are configurable per-game-type and can be learned from data.
If either triggers, we skip all 7 phases and return immediately.
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import random
import logging
from dataclasses import dataclass
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from engines.registry import EngineRegistry
    from engines.decision.phase_contracts import GameState, AgentContext, FinalDecision

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURABLE THRESHOLDS
# =============================================================================

@dataclass
class EmergencyThresholds:
    """
    Configurable emergency thresholds.
    
    Defaults are empirically chosen but can be learned per-game-type:
    - loop_detection: 15 = ~3 full movement cycles stuck on same position
    - frustration_override: 20 = ~5% of typical 400-action budget
    
    TODO: Learn these from database via game_session_manager data:
          SELECT AVG(actions_before_breakthrough) FROM game_results 
          GROUP BY game_type
    """
    loop_detection: int = 15
    frustration_override: int = 20
    
    @classmethod
    def for_game_type(cls, game_type: str, db=None) -> 'EmergencyThresholds':
        """
        Get thresholds tuned for a specific game type.
        
        Falls back to defaults if no learned data available.
        """
        if db is None:
            return cls()
        
        try:
            # Try to get learned thresholds from database
            # TODO: Implement actual learning query
            # avg_stuck = db.get_avg_stuck_threshold(game_type)
            # avg_frustration = db.get_avg_frustration_threshold(game_type)
            return cls()
        except Exception:
            return cls()


# =============================================================================
# EMERGENCY CHECK
# =============================================================================

class EmergencyCheck:
    """
    Pre-phase emergency detection.
    
    This is the ONLY place in the decision pipeline where early-exit is allowed.
    All other phases must complete and contribute weights.
    
    Thresholds can be configured per-game-type for better tuning.
    """
    
    # Default thresholds (class-level, for backwards compatibility)
    DEFAULT_LOOP_THRESHOLD = 15
    DEFAULT_FRUSTRATION_THRESHOLD = 20
    
    def __init__(
        self,
        engines: 'EngineRegistry',
        thresholds: Optional[EmergencyThresholds] = None,
    ):
        self.engines = engines
        self.thresholds = thresholds or EmergencyThresholds()
        self._recent_actions: List[str] = []
        self._recent_positions: List[tuple] = []
        self._no_change_count: int = 0
    
    def set_thresholds_for_game(self, game_type: str, db=None) -> None:
        """
        Update thresholds based on game type.
        
        Call this when switching to a new game type to use
        learned thresholds if available.
        """
        self.thresholds = EmergencyThresholds.for_game_type(game_type, db)
    
    def check(
        self,
        game_state: 'GameState',
        agent_context: 'AgentContext',
    ) -> Optional['FinalDecision']:
        """
        Check for emergency conditions.
        
        Returns:
            FinalDecision if emergency triggered, None otherwise
        """
        # Import here to avoid circular imports
        from engines.decision.phase_contracts import FinalDecision
        
        # Track state for loop detection
        self._update_tracking(game_state)
        
        # Check 1: Infinite loop detection
        loop_action = self._check_infinite_loop(game_state)
        if loop_action:
            logger.warning(
                f"[EMERGENCY] Infinite loop detected after {self._no_change_count} "
                f"no-change actions. Breaking with random action: {loop_action}"
            )
            return FinalDecision(
                action=loop_action,
                confidence=0.1,
                reasoning=f"EMERGENCY: Loop break after {self._no_change_count} stuck actions",
                audit_trail={'emergency': 'infinite_loop', 'stuck_count': self._no_change_count},
                gut_instinct="none",
                deliberation_changed=True,
                selection_method="emergency_loop_break",
            )
        
        # Check 2: Frustration override
        frustration_action = self._check_frustration(game_state, agent_context)
        if frustration_action:
            logger.warning(
                f"[EMERGENCY] Frustration override triggered. "
                f"Forcing exploration with: {frustration_action}"
            )
            return FinalDecision(
                action=frustration_action,
                confidence=0.2,
                reasoning="EMERGENCY: Frustration override - forcing exploration",
                audit_trail={'emergency': 'frustration_override'},
                gut_instinct="none",
                deliberation_changed=True,
                selection_method="emergency_frustration",
            )
        
        # No emergency - continue to phases
        return None
    
    def _update_tracking(self, game_state: 'GameState') -> None:
        """Update action/position tracking for loop detection."""
        # Track position changes
        if game_state.position:
            if self._recent_positions and game_state.position == self._recent_positions[-1]:
                self._no_change_count += 1
            else:
                self._no_change_count = 0
            self._recent_positions.append(game_state.position)
            # Keep last 20 positions
            if len(self._recent_positions) > 20:
                self._recent_positions.pop(0)
        
        # Track actions
        if game_state.previous_action:
            self._recent_actions.append(game_state.previous_action)
            # Keep last 20 actions
            if len(self._recent_actions) > 20:
                self._recent_actions.pop(0)
    
    def _check_infinite_loop(self, game_state: 'GameState') -> Optional[str]:
        """
        Detect infinite loops via repeated no-change states.
        
        Returns random action if loop detected, None otherwise.
        Threshold is configurable via self.thresholds.loop_detection.
        """
        if self._no_change_count >= self.thresholds.loop_detection:
            # Pick a random action that's NOT the last few we tried
            all_actions = [f"ACTION{i}" for i in range(1, 8)]
            recent_set = set(self._recent_actions[-5:]) if self._recent_actions else set()
            available = [a for a in all_actions if a not in recent_set]
            
            if not available:
                available = all_actions
            
            return random.choice(available)
        
        return None
    
    def _check_frustration(
        self,
        game_state: 'GameState',
        agent_context: 'AgentContext',
    ) -> Optional[str]:
        """
        Check if frustration threshold exceeded.
        
        Uses frustration_detector engine if available.
        Returns exploration action if frustrated, None otherwise.
        """
        frustration_detector = self.engines.get('frustration_detector')
        
        if frustration_detector:
            try:
                is_frustrated = frustration_detector.is_frustrated(
                    game_id=game_state.game_id,
                    level=game_state.level,
                    agent_id=agent_context.agent_id,
                    action_count=game_state.action_number,
                )
                
                if is_frustrated:
                    # Force exploration - try movement actions
                    exploration_actions = ["ACTION1", "ACTION2", "ACTION3", "ACTION4"]
                    return random.choice(exploration_actions)
            except Exception as e:
                logger.debug(f"[EMERGENCY] Frustration check failed: {e}")
        
        # Alternative: check action count directly
        if game_state.action_number >= self.thresholds.frustration_override:
            # Check if we're making progress via frame changes
            if game_state.previous_frame and game_state.frame == game_state.previous_frame:
                # No frame change for many actions - frustrated
                if self._no_change_count >= 10:
                    return random.choice(["ACTION1", "ACTION2", "ACTION3", "ACTION4"])
        
        return None
    
    def reset(self) -> None:
        """Reset tracking state for new game/level."""
        self._recent_actions.clear()
        self._recent_positions.clear()
        self._no_change_count = 0
