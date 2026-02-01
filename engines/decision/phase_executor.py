"""
Phase Executor - 7-Phase Decision Orchestration
================================================

Runs all phases in order, passing contracts between them.
NEVER swallows errors. ALWAYS produces audit trail.

Design Principles:
1. NO early returns except emergencies
2. ALL phases contribute to final weights
3. Phase 7 is the ONLY action selector
4. Full audit trail for debugging

Usage:
    from engines.decision import PhaseExecutor
    
    executor = PhaseExecutor(engine_registry, db)
    decision = executor.decide(game_state, agent_context)
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import time
import logging
from typing import Dict, Any, Optional, TYPE_CHECKING
from dataclasses import asdict

if TYPE_CHECKING:
    from engines.registry import EngineRegistry
    from database_interface import DatabaseInterface

from engines.decision.phase_contracts import (
    PhaseError,
    GameState,
    AgentContext,
    OrientContext,
    GroundTruthContext,
    ReasonContext,
    PatternContext,
    ProposalContext,
    FilteredContext,
    FinalDecision,
    create_empty_orient_context,
    create_empty_ground_truth_context,
    create_empty_reason_context,
    create_empty_pattern_context,
    create_empty_proposal_context,
    create_empty_filtered_context,
)

from engines.decision.phases import (
    EmergencyCheck,
    OrientPhase,
    GroundTruthPhase,
    ReasonPhase,
    PatternPhase,
    ProposePhase,
    FilterPhase,
    SelectPhase,
)

logger = logging.getLogger(__name__)


class PhaseExecutor:
    """
    Executes the 7-phase decision pipeline.
    
    Phases:
    1. ORIENT - "What world am I in?"
    2. GROUND TRUTH - "What do I empirically know?"
    3. REASON - "What should I believe?"
    4. PATTERN MATCH - "Have I seen this before?"
    5. PROPOSE - "What's my best move?"
    6. FILTER - "Remove bad options"
    7. SELECT - "Final weighted decision"
    
    Plus a pre-phase emergency check for loop breaking.
    """
    
    def __init__(
        self,
        engine_registry: 'EngineRegistry',
        db: Optional['DatabaseInterface'] = None,
    ):
        """
        Initialize the phase executor.
        
        Args:
            engine_registry: Registry for accessing all engines
            db: Optional database interface for logging decisions
        """
        self.engines = engine_registry
        self.db = db
        
        # Initialize all phases
        self._emergency = EmergencyCheck(engine_registry)
        self._phase1_orient = OrientPhase(engine_registry)
        self._phase2_ground_truth = GroundTruthPhase(engine_registry)
        self._phase3_reason = ReasonPhase(engine_registry)
        self._phase4_pattern = PatternPhase(engine_registry)
        self._phase5_propose = ProposePhase(engine_registry)
        self._phase6_filter = FilterPhase(engine_registry)
        self._phase7_select = SelectPhase(engine_registry)
        
        # Statistics
        self._decision_count = 0
        self._emergency_count = 0
        self._total_time_ms = 0.0
    
    def decide(
        self,
        game_state: GameState,
        agent_context: AgentContext,
    ) -> FinalDecision:
        """
        Execute full decision pipeline.
        
        Args:
            game_state: Current frame, score, game_id, level
            agent_context: Agent ID, wA/wB, urgency, role
            
        Returns:
            FinalDecision with action and full audit trail
            
        Raises:
            PhaseError: If any phase fails critically (NEVER silently)
        """
        start_time = time.time()
        audit: Dict[str, Any] = {
            'start_time': start_time,
            'game_id': game_state.game_id,
            'level': game_state.level,
            'action_number': game_state.action_number,
            'agent_id': agent_context.agent_id,
            'phases': {},
        }
        
        try:
            # Validate inputs
            agent_context.validate()
            
            # === EMERGENCY CHECK (Pre-Phase) ===
            emergency_decision = self._emergency.check(game_state, agent_context)
            if emergency_decision:
                self._emergency_count += 1
                audit['emergency'] = True
                audit['total_time_ms'] = (time.time() - start_time) * 1000
                emergency_decision.audit_trail = audit
                self._log_decision(emergency_decision)
                return emergency_decision
            
            # === PHASE 1: ORIENT ===
            orient_ctx = self._run_phase1(game_state, agent_context, audit)
            
            # === PHASE 2: GROUND TRUTH ===
            ground_ctx = self._run_phase2(game_state, agent_context, orient_ctx, audit)
            
            # === PHASE 3: REASON ===
            reason_ctx = self._run_phase3(
                game_state, agent_context, orient_ctx, ground_ctx, audit
            )
            
            # === PHASE 4: PATTERN MATCH ===
            pattern_ctx = self._run_phase4(
                game_state, agent_context, orient_ctx, ground_ctx, reason_ctx, audit
            )
            
            # === PHASE 5: PROPOSE ===
            proposal_ctx = self._run_phase5(
                game_state, agent_context, orient_ctx, ground_ctx,
                reason_ctx, pattern_ctx, audit
            )
            
            # === PHASE 6: FILTER ===
            filtered_ctx = self._run_phase6(
                game_state, agent_context, ground_ctx, reason_ctx, proposal_ctx, audit
            )
            
            # === PHASE 7: SELECT ===
            decision = self._run_phase7(
                game_state, agent_context, filtered_ctx, audit
            )
            
            # Finalize audit
            audit['total_time_ms'] = (time.time() - start_time) * 1000
            audit['emergency'] = False
            decision.audit_trail = audit
            
            # Update statistics
            self._decision_count += 1
            self._total_time_ms += audit['total_time_ms']
            
            # Log decision
            self._log_decision(decision)
            
            return decision
            
        except PhaseError:
            # Re-raise phase errors (they're explicit)
            raise
        except Exception as e:
            # Wrap unexpected errors
            logger.error(f"[EXECUTOR] Unexpected error: {e}", exc_info=True)
            raise PhaseError("EXECUTOR", f"Unexpected error: {e}")
    
    def _run_phase1(
        self,
        game_state: GameState,
        agent_context: AgentContext,
        audit: Dict[str, Any],
    ) -> OrientContext:
        """Run Phase 1: Orient with error handling."""
        try:
            ctx = self._phase1_orient.execute(game_state, agent_context)
            audit['phases']['orient'] = self._context_to_dict(ctx)
            return ctx
        except PhaseError:
            raise
        except Exception as e:
            logger.warning(f"[PHASE1] Error: {e}, using empty context")
            ctx = create_empty_orient_context(agent_context)
            audit['phases']['orient'] = self._context_to_dict(ctx)
            audit['phases']['orient']['error'] = str(e)
            return ctx
    
    def _run_phase2(
        self,
        game_state: GameState,
        agent_context: AgentContext,
        orient_ctx: OrientContext,
        audit: Dict[str, Any],
    ) -> GroundTruthContext:
        """Run Phase 2: Ground Truth with error handling."""
        try:
            ctx = self._phase2_ground_truth.execute(
                game_state, agent_context, orient_ctx
            )
            audit['phases']['ground_truth'] = self._context_to_dict(ctx)
            return ctx
        except PhaseError:
            raise
        except Exception as e:
            logger.warning(f"[PHASE2] Error: {e}, using empty context")
            ctx = create_empty_ground_truth_context()
            audit['phases']['ground_truth'] = self._context_to_dict(ctx)
            audit['phases']['ground_truth']['error'] = str(e)
            return ctx
    
    def _run_phase3(
        self,
        game_state: GameState,
        agent_context: AgentContext,
        orient_ctx: OrientContext,
        ground_ctx: GroundTruthContext,
        audit: Dict[str, Any],
    ) -> ReasonContext:
        """Run Phase 3: Reason with error handling."""
        try:
            ctx = self._phase3_reason.execute(
                game_state, agent_context, orient_ctx, ground_ctx
            )
            audit['phases']['reason'] = self._context_to_dict(ctx)
            return ctx
        except PhaseError:
            raise
        except Exception as e:
            logger.warning(f"[PHASE3] Error: {e}, using empty context")
            ctx = create_empty_reason_context()
            audit['phases']['reason'] = self._context_to_dict(ctx)
            audit['phases']['reason']['error'] = str(e)
            return ctx
    
    def _run_phase4(
        self,
        game_state: GameState,
        agent_context: AgentContext,
        orient_ctx: OrientContext,
        ground_ctx: GroundTruthContext,
        reason_ctx: ReasonContext,
        audit: Dict[str, Any],
    ) -> PatternContext:
        """Run Phase 4: Pattern Match with error handling."""
        try:
            ctx = self._phase4_pattern.execute(
                game_state, agent_context, orient_ctx, ground_ctx, reason_ctx
            )
            audit['phases']['pattern'] = self._context_to_dict(ctx)
            return ctx
        except PhaseError:
            raise
        except Exception as e:
            logger.warning(f"[PHASE4] Error: {e}, using empty context")
            ctx = create_empty_pattern_context()
            audit['phases']['pattern'] = self._context_to_dict(ctx)
            audit['phases']['pattern']['error'] = str(e)
            return ctx
    
    def _run_phase5(
        self,
        game_state: GameState,
        agent_context: AgentContext,
        orient_ctx: OrientContext,
        ground_ctx: GroundTruthContext,
        reason_ctx: ReasonContext,
        pattern_ctx: PatternContext,
        audit: Dict[str, Any],
    ) -> ProposalContext:
        """Run Phase 5: Propose with error handling."""
        try:
            ctx = self._phase5_propose.execute(
                game_state, agent_context, orient_ctx, ground_ctx,
                reason_ctx, pattern_ctx
            )
            audit['phases']['propose'] = self._context_to_dict(ctx)
            return ctx
        except PhaseError:
            raise
        except Exception as e:
            logger.warning(f"[PHASE5] Error: {e}, using empty context")
            ctx = create_empty_proposal_context()
            audit['phases']['propose'] = self._context_to_dict(ctx)
            audit['phases']['propose']['error'] = str(e)
            return ctx
    
    def _run_phase6(
        self,
        game_state: GameState,
        agent_context: AgentContext,
        ground_ctx: GroundTruthContext,
        reason_ctx: ReasonContext,
        proposal_ctx: ProposalContext,
        audit: Dict[str, Any],
    ) -> FilteredContext:
        """Run Phase 6: Filter with error handling."""
        try:
            ctx = self._phase6_filter.execute(
                game_state, agent_context, ground_ctx, reason_ctx, proposal_ctx
            )
            audit['phases']['filter'] = self._context_to_dict(ctx)
            return ctx
        except PhaseError:
            raise
        except Exception as e:
            logger.warning(f"[PHASE6] Error: {e}, using empty context")
            ctx = create_empty_filtered_context()
            audit['phases']['filter'] = self._context_to_dict(ctx)
            audit['phases']['filter']['error'] = str(e)
            return ctx
    
    def _run_phase7(
        self,
        game_state: GameState,
        agent_context: AgentContext,
        filtered_ctx: FilteredContext,
        audit: Dict[str, Any],
    ) -> FinalDecision:
        """Run Phase 7: Select - MUST produce a decision."""
        # Phase 7 should never fail - it has fallback logic
        return self._phase7_select.execute(
            game_state, agent_context, filtered_ctx, audit
        )
    
    def _context_to_dict(self, ctx: Any) -> Dict[str, Any]:
        """Convert context to dictionary for audit trail."""
        try:
            if hasattr(ctx, '__dict__'):
                result = {}
                for key, value in ctx.__dict__.items():
                    if isinstance(value, set):
                        result[key] = list(value)
                    elif isinstance(value, (list, dict, str, int, float, bool, type(None))):
                        result[key] = value
                    elif hasattr(value, '__dict__'):
                        result[key] = self._context_to_dict(value)
                    else:
                        result[key] = str(value)
                return result
            return {'value': str(ctx)}
        except Exception:
            return {'error': 'serialization_failed'}
    
    def _log_decision(self, decision: FinalDecision) -> None:
        """Log decision to database if available."""
        if self.db is None:
            return
        
        try:
            # Log to decision_audit table if it exists
            if hasattr(self.db, 'log_decision'):
                self.db.log_decision(
                    action=decision.action,
                    confidence=decision.confidence,
                    reasoning=decision.reasoning,
                    audit_trail=decision.audit_trail,
                )
        except Exception as e:
            logger.debug(f"[EXECUTOR] Failed to log decision: {e}")
    
    def reset(self) -> None:
        """Reset state for new game/level."""
        self._emergency.reset()
        self._phase6_filter.reset()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get executor statistics."""
        return {
            'decision_count': self._decision_count,
            'emergency_count': self._emergency_count,
            'avg_time_ms': (
                self._total_time_ms / self._decision_count
                if self._decision_count > 0 else 0
            ),
        }
