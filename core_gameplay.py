import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
Core Gameplay Logic

Provides the fundamental gameplay loop and decision-making logic.
Contains only essential game mechanics without architect/governor/director complexity.

Enhanced with pattern learning (Rule 10: integrated, not new files):
- Captures winning sequences
- Discovers and reuses patterns
- Learns from every game

Refactored for maintainability (December 2025):
- Extracted logical sections into helper methods
- _handle_3_try_fallback() - The 3-try sequence system
- _handle_sequence_replay_result() - Processing replay success/failure
- _run_game_loop() - The main action loop
- _handle_level_completion() - Level completion logic
- _finalize_game() - End-of-game cleanup and results
"""

import asyncio
import logging
import json
import uuid
import numpy as np
from typing import Dict, Any, List, Optional, Callable, Tuple
from collections import Counter
from dataclasses import dataclass, field
import random
from datetime import datetime

from game_session_manager import GameSessionManager
from action_handler import ActionHandler
from arc_api_client import GameState
from database_interface import DatabaseInterface
from prestige_engine import PrestigeEngine
from sensation_engine import SensationEngine
from breakthrough_budget_allocator import BreakthroughBudgetAllocator
from breakthrough_detector import BreakthroughDetector
from multi_stage_matching_pipeline import MultiStageMatchingPipeline
from subgoal_planning_activator import SubgoalPlanningActivator
from agent_self_model import AgentSelfModel

# Abstraction engine imports
try:
    from sequence_abstraction import SequenceAbstraction
    from abstraction_config import is_abstraction_enabled
    ABSTRACTION_AVAILABLE = True
except ImportError:
    ABSTRACTION_AVAILABLE = False
    SequenceAbstraction = None
    def is_abstraction_enabled() -> bool:
        return False

logger = logging.getLogger(__name__)


@dataclass
class GameLoopState:
    """Mutable state tracked during the game loop.
    
    Extracted to reduce variable passing and improve readability.
    """
    action_count: int = 0
    level_action_count: int = 0
    previous_score: float = 0.0
    level_completions: int = 0
    current_level: int = 1
    level_start_action: int = 0
    level_api_resets: int = 0
    consecutive_no_frame_change: int = 0
    consecutive_api_errors: int = 0
    api_error_backoff: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    
    # Constants
    MAX_API_RESETS_PER_LEVEL: int = 2
    API_RESET_THRESHOLD: int = 1000
    STUCK_STATE_THRESHOLD: int = 100
    MAX_CONSECUTIVE_API_ERRORS: int = 5


@dataclass 
class SequenceFallbackResult:
    """Result from the 3-try sequence fallback system."""
    success: bool = False
    game_state: Any = None  # GameState, but typed as Any to avoid Optional issues
    successful_sequence: Any = None  # Dict or None
    all_failed: bool = False
    multi_stage_sequence: Any = None  # Dict or None
    abstraction_guidance: Any = None  # Dict or None


class GameplayEngine:
    """Core engine for playing ARC games with integrated pattern learning."""

    def __init__(self, api_key: Optional[str] = None, db_path: str = "core_data.db"):
        """Initialize gameplay engine.

        Args:
            api_key: ARC API key
            db_path: Database file path
        """
        self.session_manager = GameSessionManager(api_key, db_path)
        self.action_handler = ActionHandler(self.session_manager)
        self.db = DatabaseInterface(db_path)  # Pattern learning database access
        self.prestige_engine = PrestigeEngine(self.db)  # Phase 1: Prestige tracking
        self.sensation_engine = SensationEngine(self.db)  # Phase 4.5: Emotional intelligence
        self.budget_allocator = BreakthroughBudgetAllocator(self.db)  # Tier 1: Dynamic budgets
        self.breakthrough_detector = BreakthroughDetector()  # Tier 1: Momentum detection
        self.matching_pipeline = MultiStageMatchingPipeline(self.db)  # Tier 1: Multi-stage matching (+40%)
        self.subgoal_activator = SubgoalPlanningActivator(self.db)  # Tier 1: Subgoal planning (+30%)
        self.agent_self_model = AgentSelfModel(db_path)  # Self-model: Track controlled objects
        
        # Inject subgoal activator into action handler for real-time guidance
        self.action_handler.subgoal_activator = self.subgoal_activator  # type: ignore[attr-defined]
        
        # Abstraction engine for pattern-based sequence matching
        if ABSTRACTION_AVAILABLE and is_abstraction_enabled():
            try:
                self.abstraction_engine = SequenceAbstraction(db_path)  # type: ignore[misc]
                logger.info("Abstraction engine initialized")
            except Exception as e:
                self.abstraction_engine = None
                logger.warning(f"Failed to initialize abstraction engine: {e}")
        else:
            self.abstraction_engine = None
        
        # NEW: Breakthrough systems initialization
        try:
            from subgoal_planner import SubgoalPlanner
            self.subgoal_planner = SubgoalPlanner(self.db)  # Hierarchical planning
            # Inject into subgoal activator (Competitive #3: +30% gain)
            self.subgoal_activator.inject_subgoal_planner(self.subgoal_planner)
            logger.info("Subgoal planner injected into activator")
        except ImportError:
            self.subgoal_planner = None
            logger.debug("Subgoal planner not available")
        
        self.game_config = {
            'max_actions_per_level': 250,  # Max actions per level (REDUCED: force efficiency, prevent wandering)
            'max_total_actions': 2000,  # Max total actions across all levels (REDUCED: 7000→2000, fail fast not stuck loops)
            'action_timeout': 30.0,
            'strategy': 'balanced',
            'enable_random_exploration': True,
            'coordinate_retry_limit': 3,
            'enable_pattern_learning': True,  # Toggle pattern learning
            'learning_mode': 'smart_exploration',  # 'exploit', 'explore', 'smart_exploration'
            'enable_sensation_navigation': True,  # Phase 4.5: Toggle sensation-based emotional intelligence
            
            # Diversity-focused settings (generalization over specialization)
            'diversity_mode': False,              # Enable diversity and generalization focus
            'max_repeats_per_game': 5,            # Limit game repetition (diversity mode)
            'enforce_game_diversity': False,       # Prevent game overfitting
            'novel_game_priority': 1.0,           # Priority weight for unseen games
        }

    def configure(self, **config):
        """Update game configuration.

        Args:
            **config: Configuration parameters to update
        """
        self.game_config.update(config)
        logger.info(f"Updated game config: {config}")

    # =========================================================================
    # REFACTORED HELPER METHODS (December 2025)
    # Extracted from play_single_game to reduce complexity
    # =========================================================================

    async def _handle_3_try_fallback(
        self,
        game_state: 'GameState',
        ranked_sequences: List[Dict],
        game_id: str,
        agent_mode: Optional[str]
    ) -> SequenceFallbackResult:
        """Execute the 3-try sequence fallback system.
        
        Try up to 3 sequences in priority order. If one fails:
        1. Flag it as failing
        2. RESET THE ENTIRE GAME (sequences may target different levels)
        3. Try the next sequence from level 1
        4. After 3 failures, use multi-stage matching pipeline
        5. If pipeline fails, get abstraction guidance for exploration
        
        Args:
            game_state: Current game state
            ranked_sequences: List of sequences to try, ranked by priority
            game_id: Current game ID
            agent_mode: Agent operating mode (pioneer, optimizer, etc.)
            
        Returns:
            SequenceFallbackResult with success status and updated state
        """
        result = SequenceFallbackResult()
        result.game_state = game_state
        
        if not ranked_sequences:
            result.all_failed = True
            return result
            
        for try_num, candidate_sequence in enumerate(ranked_sequences[:3], start=1):
            sequence_id = candidate_sequence['sequence_id']
            logger.info(f"[3-TRY] Attempt {try_num}/3: Trying sequence {sequence_id[:12]} "
                       f"(score {candidate_sequence['total_score']}, {candidate_sequence['total_actions']} actions)")
            
            # Check reputation before trying
            validation_check = self.db.execute_query("""
                SELECT successful_validations, total_validation_attempts,
                       CAST(successful_validations AS FLOAT) / NULLIF(total_validation_attempts, 0) as success_rate
                FROM sequence_reputation
                WHERE sequence_id = ?
            """, (sequence_id,))
            
            if validation_check and validation_check[0]['total_validation_attempts'] >= 3:
                sr = validation_check[0]['success_rate'] or 0.0
                if sr > 0.5:
                    logger.info(f"  [PROVEN] {sr:.1%} success rate")
                elif sr < 0.3:
                    logger.warning(f"  [WARN] Low success rate: {sr:.1%}")
            
            # PARIAH ANALYSIS (for optimizer/exploiter)
            should_try = True
            if agent_mode in ['optimizer', 'exploiter']:
                current_network_level = self._get_network_max_level(game_id)
                sequence_level = int(candidate_sequence.get('total_score', 0))
                if sequence_level >= current_network_level:
                    pariah_worth = self._analyze_pariah_worthiness(candidate_sequence, game_id)
                    if not pariah_worth['worth_challenging']:
                        logger.info(f"  [SKIP] Pariah not worth challenging: {pariah_worth['reason']}")
                        should_try = False
            
            if not should_try:
                continue
            
            # Try replaying this sequence
            try:
                # game_state should always be set at this point
                assert result.game_state is not None, "game_state must be set before replay"
                
                replay_result = await self._replay_sequence_inline(
                    result.game_state, 
                    candidate_sequence
                )
                
                if replay_result and replay_result.get('success'):
                    # SUCCESS! This sequence worked
                    result.success = True
                    result.successful_sequence = candidate_sequence
                    result.game_state = replay_result['game_state']
                    logger.info(f"[3-TRY] SUCCESS on attempt {try_num}: {sequence_id[:12]} worked!")
                    
                    # Reset consecutive failures on success
                    self.db.execute_query("""
                        UPDATE winning_sequences SET consecutive_failures = 0 WHERE sequence_id = ?
                    """, (sequence_id,))
                    return result  # Exit early - we found a working sequence
                else:
                    # FAILURE - flag this sequence
                    failure_reason = f"replay_failed_attempt_{try_num}"
                    if replay_result and replay_result.get('game_state'):
                        result.game_state = replay_result['game_state']
                        failure_reason = f"reached_score_{result.game_state.score}_not_target"
                    self._flag_sequence_failure(sequence_id, failure_reason)
                    logger.warning(f"[3-TRY] FAILED attempt {try_num}: {sequence_id[:12]} - {failure_reason}")
                    
                    # FULL GAME RESET before trying next sequence
                    if try_num < min(3, len(ranked_sequences)):
                        try:
                            logger.info(f"[3-TRY] Resetting GAME for attempt {try_num + 1}...")
                            reset_data = await self.session_manager.reset_game()
                            result.game_state = GameState.from_dict(reset_data)
                            logger.info(f"[3-TRY] Game reset complete. New guid, Score: {result.game_state.score}")
                        except Exception as reset_error:
                            logger.warning(f"[3-TRY] Game reset failed: {reset_error} - continuing anyway")
                        
            except ValueError as e:
                if "frame corruption" in str(e).lower():
                    self._flag_sequence_failure(sequence_id, "frame_corruption")
                    logger.error(f"[3-TRY] Frame corruption on attempt {try_num}: {sequence_id[:12]}")
                    
                    if try_num < min(3, len(ranked_sequences)):
                        try:
                            reset_data = await self.session_manager.reset_game()
                            result.game_state = GameState.from_dict(reset_data)
                        except Exception:
                            pass
                    continue
                raise
            except Exception as e:
                self._flag_sequence_failure(sequence_id, f"exception: {str(e)[:50]}")
                logger.error(f"[3-TRY] Exception on attempt {try_num}: {e}")
                
                if try_num < min(3, len(ranked_sequences)):
                    try:
                        reset_data = await self.session_manager.reset_game()
                        result.game_state = GameState.from_dict(reset_data)
                    except Exception:
                        pass
                continue
        
        # All attempts failed - try multi-stage matching pipeline
        result.all_failed = True
        logger.warning(f"[3-TRY] All {min(3, len(ranked_sequences))} ranked sequence attempts failed")
        
        # STAGE 2: Multi-stage matching pipeline
        if hasattr(self, 'matching_pipeline') and self.matching_pipeline:
            try:
                logger.info(f"[MULTI-STAGE] Trying multi-stage matching pipeline...")
                
                try:
                    reset_data = await self.session_manager.reset_level()
                    result.game_state = GameState.from_dict(reset_data)
                except Exception:
                    pass
                
                current_actions = self.game_config.get('current_actions', [])
                agent_config = {
                    'risk_tolerance': self.game_config.get('risk_tolerance', 0.5),
                    'abstraction_threshold': self.game_config.get('abstraction_threshold', 0.7)
                }
                
                sequence_actions, stage_used, metadata = self.matching_pipeline.get_sequence_with_fallback(
                    game_id=game_id,
                    level_number=1,
                    current_actions=current_actions,
                    agent_config=agent_config
                )
                
                if sequence_actions and stage_used != 'random':
                    logger.info(f"[MULTI-STAGE] {stage_used.upper()} match found: {len(sequence_actions)} actions, "
                               f"confidence {metadata.get('confidence', 0):.2f}")
                    result.multi_stage_sequence = {
                        'actions': sequence_actions,
                        'stage': stage_used,
                        'confidence': metadata.get('confidence', 0)
                    }
                else:
                    logger.info(f"[MULTI-STAGE] Pipeline exhausted, falling back to exploration")
                    
            except Exception as e:
                logger.debug(f"Multi-stage pipeline error: {e}")
        
        # STAGE 3: Get abstraction guidance for pure exploration
        if not result.multi_stage_sequence and hasattr(self, 'abstraction_engine') and self.abstraction_engine:
            try:
                game_type = game_id.split('-')[0] if '-' in game_id else game_id
                result.abstraction_guidance = self.abstraction_engine.get_conceptual_hints(game_type)  # type: ignore[attr-defined]
                if result.abstraction_guidance:
                    logger.info(f"[ABSTRACTION] Using conceptual hints: {result.abstraction_guidance.get('hints', [])[:3]}")
            except Exception as e:
                logger.debug(f"Abstraction guidance error: {e}")
        
        return result

    async def _handle_sequence_replay_result(
        self,
        fallback_result: SequenceFallbackResult,
        game_id: str,
        agent_id: Optional[str],
        agent_mode: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Handle the result of sequence replay attempts.
        
        Returns early result dict if game should end, None to continue to game loop.
        
        Args:
            fallback_result: Result from _handle_3_try_fallback
            game_id: Current game ID
            agent_id: Agent ID
            agent_mode: Agent operating mode
            
        Returns:
            Dict with game results if game is done, None if should continue to loop
        """
        game_state = fallback_result.game_state
        known_sequence = fallback_result.successful_sequence
        
        if fallback_result.success and known_sequence:
            # game_state is guaranteed to exist if success is True
            assert game_state is not None, "game_state must exist on success"
            
            if game_state.state == "WIN":
                # Full win from replay! Finish and return
                level_completions = int(game_state.score)
                actions_taken = len(json.loads(known_sequence['action_sequence']))
                await self.session_manager.finish_game(game_state.state, game_state.score, level_completions, actions_taken)
                
                if agent_id:
                    self.session_manager.deduct_actions_used(agent_id, game_id)
                
                recombinations = []
                if agent_id:
                    recombinations = self._explore_sequence_recombination(agent_id, game_id, level_completions)
                
                logger.info(f" COMPLETE WIN via cumulative sequence replay!")
                return {
                    'game_id': game_id,
                    'final_state': game_state.state,
                    'final_score': game_state.score,
                    'actions_taken': actions_taken,
                    'win': True,
                    'method': 'cumulative_sequence_replay',
                    'sequence_id': known_sequence['sequence_id'],
                    'recombinations_created': len(recombinations)
                }
            else:
                # Replay succeeded but didn't win completely - at frontier
                frontier_level = int(game_state.score) + 1
                logger.info(f" Cumulative replay reached frontier (Level {frontier_level}, Score {game_state.score})")
                
                # EXPLOITER: STOP here
                if agent_mode == 'exploiter':
                    logger.info(f" EXPLOITER: Stopping at frontier (Level {frontier_level})")
                    await self.session_manager.finish_game(
                        game_state.state, game_state.score, 
                        int(game_state.score), len(json.loads(known_sequence['action_sequence']))
                    )
                    return {
                        'game_id': game_id,
                        'final_state': game_state.state,
                        'final_score': game_state.score,
                        'actions_taken': len(json.loads(known_sequence['action_sequence'])),
                        'win': game_state.state == 'WIN',
                        'method': 'exploiter_sequence_replay',
                        'sequence_id': known_sequence['sequence_id']
                    }
                
                # Force game state to NOT_FINISHED for continuation
                if game_state.state != "NOT_FINISHED":
                    logger.warning(f"[WARN] Game state is '{game_state.state}' at frontier - forcing to NOT_FINISHED")
                    game_state.state = "NOT_FINISHED"
                
                mode_name = (agent_mode or 'generalist').upper()
                logger.info(f" {mode_name}: At frontier (Level {frontier_level}), continuing until action budget exhausted")
                
        elif fallback_result.all_failed:
            # All sequences failed - set up fallback options
            if fallback_result.multi_stage_sequence:
                logger.info(f"[EXPLORATION FALLBACK] Using multi-stage {fallback_result.multi_stage_sequence['stage'].upper()} match")
                self.game_config['multi_stage_guidance'] = fallback_result.multi_stage_sequence
            elif fallback_result.abstraction_guidance:
                logger.info(f"[EXPLORATION FALLBACK] Using abstraction hints for guided exploration")
                self.game_config['abstraction_hints'] = fallback_result.abstraction_guidance
            else:
                logger.info(f"[EXPLORATION FALLBACK] Pure exploration mode (no guidance available)")
        
        return None  # Continue to game loop

    async def _run_single_action(
        self,
        game_state: 'GameState',
        loop_state: GameLoopState,
        action_callback: Optional[Callable],
        agent_id: Optional[str],
        game_id: str
    ) -> Tuple['GameState', bool, Optional[str]]:
        """Execute a single action in the game loop.
        
        Args:
            game_state: Current game state
            loop_state: Mutable loop state
            action_callback: Optional custom action callback
            agent_id: Agent ID
            game_id: Game ID
            
        Returns:
            Tuple of (updated game_state, action_succeeded, action_taken)
        """
        action = None
        action_succeeded = False
        
        # API error backoff
        if loop_state.api_error_backoff > 0:
            logger.info(f"[TIME] API error backoff: waiting {loop_state.api_error_backoff}s before next action")
            await asyncio.sleep(loop_state.api_error_backoff)
            loop_state.api_error_backoff = 0
        
        try:
            if action_callback:
                action_result = await action_callback(game_state, self.action_handler)
                if isinstance(action_result, GameState):
                    game_state = action_result
                elif isinstance(action_result, str):
                    action = action_result
                    game_state = await self._execute_action(action, game_state, "", loop_state.current_level)
                else:
                    raise ValueError(f"Invalid action callback result: {action_result}")
            else:
                action, reasoning = await self._select_action(game_state)
                game_state = await self._execute_action(action, game_state, reasoning, loop_state.current_level)
            
            loop_state.consecutive_api_errors = 0
            action_succeeded = True
            
        except Exception as action_error:
            error_msg = str(action_error).lower()
            is_api_error = any(indicator in error_msg for indicator in [
                '400', 'bad_request', 'bad request',
                '500', 'internal server error', 'non-json response',
                'server disconnected', 'connection', 'timeout'
            ])
            
            if is_api_error:
                loop_state.consecutive_api_errors += 1
                logger.warning(f"[WARN] API error #{loop_state.consecutive_api_errors}: {action_error}")
                
                is_session_dead = any(indicator in error_msg for indicator in ['400', 'bad_request', 'bad request'])
                if is_session_dead:
                    logger.error(f"[STOP] Game session terminated (400 BAD_REQUEST)")
                    raise RuntimeError("Session dead")
                
                if loop_state.consecutive_api_errors >= loop_state.MAX_CONSECUTIVE_API_ERRORS:
                    logger.error(f"[STOP] Too many consecutive API errors ({loop_state.consecutive_api_errors})")
                    raise RuntimeError("Too many API errors")
                
                loop_state.api_error_backoff = min(2 ** (loop_state.consecutive_api_errors - 1), 16)
                logger.info(f"   -> Will wait {loop_state.api_error_backoff}s before retry")
            else:
                raise
        
        return game_state, action_succeeded, action

    async def _handle_level_completion(
        self,
        game_state: 'GameState',
        loop_state: GameLoopState,
        game_id: str,
        agent_id: Optional[str],
        agent_mode: Optional[str]
    ) -> None:
        """Handle level completion logic including sequence capture.
        
        Args:
            game_state: Current game state
            loop_state: Mutable loop state
            game_id: Game ID
            agent_id: Agent ID
            agent_mode: Agent operating mode
        """
        loop_state.level_completions += 1
        logger.info(f" Level {loop_state.current_level} completed! Score: {loop_state.previous_score} -> {game_state.score}")
        logger.info(f" Level {loop_state.current_level} stats: {loop_state.level_action_count} actions, {loop_state.level_api_resets} API resets used")
        
        loop_state.level_api_resets = 0
        
        # Pattern Learning: Capture sequence on level completion
        if self.game_config.get('enable_pattern_learning', True):
            level_for_storage = int(game_state.score)
            
            if level_for_storage == 1:
                capture_reason = "level_1_win"
            else:
                capture_reason = f"partial_progress_{level_for_storage}_levels"
            
            sequence_id = self._capture_winning_sequence(
                game_id, 
                game_state.score, 
                level_number=level_for_storage,
                reason=capture_reason,
                level_completions=loop_state.level_completions
            )
            if sequence_id:
                if level_for_storage > 1:
                    logger.info(f"[PKG] Captured CUMULATIVE sequence for levels 1-{level_for_storage}: {sequence_id}")
                else:
                    logger.info(f" Captured level {level_for_storage} winning sequence: {sequence_id}")
        
        # Agent Self-Model: Track controlled objects
        if agent_id and hasattr(self, 'agent_self_model'):
            try:
                action_history = self.session_manager.action_history[-loop_state.level_action_count:] if hasattr(self.session_manager, 'action_history') else []  # type: ignore[attr-defined]
                frame_history = self.session_manager.frame_history[-loop_state.level_action_count:] if hasattr(self.session_manager, 'frame_history') else []  # type: ignore[attr-defined]
                
                if action_history and frame_history:
                    controlled, confidence = self.agent_self_model.identify_controlled_objects(
                        game_id, loop_state.current_level, action_history, frame_history
                    )
                    if controlled and confidence > 0.3:
                        self.agent_self_model.store_control_map(
                            agent_id, game_id, loop_state.current_level, controlled, confidence
                        )
            except Exception as e:
                logger.debug(f"Agent self-model tracking error: {e}")
        
        # Move to next level
        loop_state.previous_score = game_state.score
        loop_state.current_level += 1
        loop_state.level_action_count = 0
        loop_state.level_start_action = loop_state.action_count
        loop_state.consecutive_no_frame_change = 0

    async def _finalize_game(
        self,
        game_state: 'GameState',
        loop_state: GameLoopState,
        game_id: str,
        agent_id: Optional[str]
    ) -> Dict[str, Any]:
        """Finalize game and return results.
        
        Args:
            game_state: Final game state
            loop_state: Loop state with counters
            game_id: Game ID
            agent_id: Agent ID
            
        Returns:
            Game results dictionary
        """
        end_time = datetime.now()
        duration = (end_time - loop_state.start_time).total_seconds()

        results = {
            'game_id': game_id,
            'final_state': game_state.state,
            'final_score': game_state.score,
            'actions_taken': loop_state.action_count,
            'duration_seconds': duration,
            'win': game_state.state == "WIN",
            'level_completions': loop_state.level_completions,
            'levels_attempted': loop_state.current_level,
            'start_time': loop_state.start_time,
            'end_time': end_time
        }

        # Track agent performance
        if agent_id:
            self._track_agent_performance(
                agent_id=agent_id,
                game_id=game_id,
                final_score=game_state.score,
                actions_taken=loop_state.action_count,
                level_completions=loop_state.level_completions,
                win=(game_state.state == "WIN"),
                duration_seconds=duration
            )
        
        # Diversity tracking
        if self.game_config.get('diversity_mode'):
            self._track_game_diversity(game_id, game_state.score, loop_state.action_count)

        # Finish game in session manager
        await self.session_manager.finish_game(game_state.state, game_state.score, loop_state.level_completions, loop_state.action_count)
        
        # Deduct actions from budget
        if agent_id:
            self.session_manager.deduct_actions_used(agent_id, game_id)

        # Pattern Learning: Capture final sequence
        if self.game_config.get('enable_pattern_learning', True):
            if game_state.state == "WIN" and loop_state.level_completions > 0:
                sequence_id = self._capture_winning_sequence(
                    game_id, game_state.score,
                    level_number=loop_state.current_level,
                    reason="full_game_win",
                    level_completions=loop_state.level_completions
                )
                if sequence_id:
                    results['learned_sequence_id'] = sequence_id
                    logger.info(f" Captured full game winning sequence: {sequence_id}")
            elif game_state.score > 0 and loop_state.level_completions > 0:
                levels_completed_for_capture = int(game_state.score)
                sequence_id = self._capture_winning_sequence(
                    game_id, game_state.score,
                    level_number=levels_completed_for_capture,
                    reason=f"partial_progress_{levels_completed_for_capture}_levels",
                    level_completions=loop_state.level_completions
                )
                if sequence_id:
                    results['learned_sequence_id'] = sequence_id
                    logger.info(f" Captured partial progress sequence: {sequence_id}")

        # Knowledge Recombination
        if agent_id:
            recombinations = self._explore_sequence_recombination(agent_id, game_id, loop_state.current_level)
            if recombinations:
                results['recombinations_created'] = len(recombinations)

        # Viral Packages & Pariahs
        if agent_id:
            await self._handle_viral_evolution(results, game_state, game_id, agent_id)

        logger.info(f"Game {game_id} completed: {game_state.state}, Score: {game_state.score}, "
                   f"Actions: {loop_state.action_count}, Levels Completed: {loop_state.level_completions}/{loop_state.current_level}")
        return results

    async def _handle_viral_evolution(
        self,
        results: Dict[str, Any],
        game_state: 'GameState',
        game_id: str,
        agent_id: str
    ) -> None:
        """Handle viral package creation and pariah tracking.
        
        Args:
            results: Results dict to update
            game_state: Final game state
            game_id: Game ID
            agent_id: Agent ID
        """
        generation = self.game_config.get('generation', 0)
        
        from viral_package_engine import ViralPackageEngine
        viral_engine = ViralPackageEngine(self.db)
        
        if results['win'] and results.get('learned_sequence_id'):
            package_id = viral_engine.create_viral_package_from_sequence(
                results['learned_sequence_id'], agent_id, generation
            )
            if package_id:
                results['viral_package_created'] = package_id
                logger.info(f"[VIRAL] Created viral package {package_id[:12]}")
                
                nearby_agents = self.db.execute_query("""
                    SELECT agent_id FROM agents 
                    WHERE is_active = TRUE AND agent_id != ?
                    ORDER BY RANDOM() LIMIT 3
                """, (agent_id,))
                
                spread_count = 0
                for target in nearby_agents:
                    if viral_engine.spread_viral_package(package_id, agent_id, target['agent_id'], generation):
                        spread_count += 1
                if spread_count > 0:
                    logger.info(f"[VIRAL] Viral package spread to {spread_count} agents")
        
        elif not results['win'] and game_state.score < 1.0:
            action_traces = self.db.execute_query("""
                SELECT action_number, coordinates
                FROM action_traces
                WHERE game_id = ? AND session_id = ?
                ORDER BY timestamp ASC
            """, (game_id, self.session_manager.current_session_id))
            
            if action_traces:
                failed_actions = [t['action_number'] for t in action_traces]
                failed_coords = []
                for t in action_traces:
                    if t.get('coordinates'):
                        try:
                            coord = json.loads(t['coordinates'])
                            failed_coords.append(tuple(coord))
                        except:
                            pass
                
                pariah_id = viral_engine.create_pariah_from_failure(
                    game_id, agent_id, failed_actions, failed_coords, game_state.score, generation
                )
                
                if pariah_id:
                    results['pariah_created'] = pariah_id
                    
                    nearby_agents = self.db.execute_query("""
                        SELECT agent_id FROM agents 
                        WHERE is_active = TRUE AND agent_id != ?
                        ORDER BY RANDOM() LIMIT 3
                    """, (agent_id,))
                    
                    for target in nearby_agents:
                        viral_engine.spread_pariah_awareness(pariah_id, agent_id, target['agent_id'], generation)

    # =========================================================================
    # END OF REFACTORED HELPER METHODS
    # =========================================================================

    async def play_single_game(self, game_id: str,
                              action_callback: Optional[Callable] = None,
                              agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Play a single game to completion with optional pattern learning.

        Args:
            game_id: Game ID to play
            action_callback: Optional callback function for custom action selection
            agent_id: Optional agent ID for tracking performance

        Returns:
            Game results dictionary
        """
        logger.info(f"Starting game: {game_id}" + (f" (agent: {agent_id})" if agent_id else ""))
        
        # PHASE 2: Check if agent can afford to play this game
        if agent_id:
            can_afford, reason = self.session_manager.can_agent_afford_game(agent_id, game_id)
            if not can_afford:
                logger.warning(f"Agent {agent_id[:8]} cannot afford game: {reason}")
                return {
                    'game_id': game_id,
                    'final_state': 'BUDGET_EXHAUSTED',
                    'final_score': 0.0,
                    'actions_taken': 0,
                    'win': False,
                    'method': 'budget_denied',
                    'reason': reason
                }
        
        # Store agent_id in game_config for sequence capture (CRITICAL FIX)
        if agent_id:
            self.game_config['agent_id'] = agent_id

        # Start session if not already running
        if not self.session_manager.is_running:
            session_mode = f"agent_{agent_id}_gameplay" if agent_id else "gameplay"
            await self.session_manager.start_session(mode=session_mode, game_id=game_id)
        
        # Get agent mode BEFORE creating game (needed for tags)
        # Check if mode is forced in game_config (e.g., from mastery mode)
        agent_mode = self.game_config.get('agent_operating_mode')
        if not agent_mode and agent_id:
            agent_mode = self._get_agent_operating_mode(agent_id)
        
        # Get network max level for pioneer oscillation checks
        network_max_level = self._get_network_max_level(game_id) if game_id else 0
        
        # Set agent mode in action handler and visual analyzer for mode-specific behavior
        # Pass current_level=1 (starting level) and network_max_level for pioneer checks
        self.action_handler.set_agent_mode(agent_mode, current_level=1, network_max_level=network_max_level)
        self.action_handler.visual_analyzer.set_agent_mode(agent_mode)
        if agent_mode:
            logger.info(f" Agent mode set to: {agent_mode.upper()}")
            
            # For optimizers, set target level in arc_client for tagging
            if agent_mode == 'optimizer':
                target_level = self.game_config.get('optimizer_target_level', 1)
                if hasattr(self.session_manager, 'client') and self.session_manager.client:
                    self.session_manager.client._optimizer_target_level = target_level  # type: ignore[attr-defined]
        
        # Create game with agent info in tags
        game_data = await self.session_manager.create_game(
            game_id, 
            agent_id=agent_id,
            agent_mode=agent_mode
        )
        game_state = GameState.from_dict(game_data)
        
        # Initialize action history for abstraction engine (with memory leak protection)
        self.game_config['current_actions'] = []
        self.game_config['max_action_history'] = 1000  # Prevent memory leaks in long games
        
        # Set game context in action handler for subgoal planning (Tier 1: +30%)
        self.action_handler._current_game_id = game_id  # type: ignore[attr-defined]
        self.action_handler._current_level = 1  # type: ignore[attr-defined]
        self.action_handler._current_frame = game_state.frame  # type: ignore[attr-defined]
        
        # CRITICAL FIX: Initialize last_frame with the starting frame
        # This ensures frame_before is captured for the FIRST action of the game.
        # Without this, the first action's frame_before = None, causing winning sequences
        # to have empty initial_frame, breaking sequence replay matching.
        self.action_handler.last_frame = game_state.frame.copy() if game_state.frame else None
        self.action_handler.last_score = game_state.score  # Also initialize score
        
        # Trigger subgoal generation at game start (Tier 1: +30%)
        if self.subgoal_activator.should_generate_subgoals(
            game_id=game_id,
            level_number=1,
            action_count=0,
            score=int(game_state.score),
            game_state=game_state.state
        ):
            subgoals = self.subgoal_activator.generate_subgoals(
                game_id=game_id,
                level_number=1,
                frame_data=game_state.frame,
                current_score=int(game_state.score)
            )
            if subgoals:
                logger.info(f"[SUBGOAL] Generated {len(subgoals)} subgoals for {game_id} L1")
        
        # Pattern Learning: Check for known winning sequence (Rule 10: integrated)
        # Check AFTER game creation so we have the initial frame
        # MODE-AWARE: Behavior depends on agent operating mode
        known_sequence = None
        
        if self.game_config.get('enable_pattern_learning', True):
            learning_mode = self.game_config.get('learning_mode', 'smart_exploration')
            
            # OPTIMIZER: Always gets sequence (to try improving it)
            # GENERALIST: Gets sequence (follows it exactly)
            # PIONEER: Gets sequence (uses it to reach frontier, then explores)
            # EXPLOITER: REQUIRES sequence (fails if no sequence found)
            if learning_mode in ['exploit', 'smart_exploration'] or agent_mode in ['optimizer', 'generalist', 'pioneer', 'exploiter']:
                try:
                    logger.info(f"[SEQUENCE REPLAY DEBUG] Checking for sequences for game {game_id}, agent_mode={agent_mode}")
                    
                    # 3-TRY FALLBACK SYSTEM: Get top 3 sequences ranked by priority
                    # Try each in order, flag failures, fall back to exploration if all fail
                    ranked_sequences = self._get_ranked_cumulative_sequences(game_id, limit=3)
                    
                    if ranked_sequences:
                        logger.info(f"[3-TRY SYSTEM] Found {len(ranked_sequences)} candidate sequences for {game_id}")
                    else:
                        logger.warning(f"[SEQUENCE REPLAY DEBUG] No sequences found for game {game_id}")
                        if agent_mode == 'exploiter':
                            logger.error(f"[EXPLOITER FAILURE] Agent in exploiter mode but no sequences available for {game_id} - cannot proceed")
                    
                    # Try to use the best available sequence (will be set by 3-try loop below)
                    known_sequence = ranked_sequences[0] if ranked_sequences else None
                    
                    if known_sequence:
                        levels_completed_by_seq = int(known_sequence['total_score'])
                        if agent_mode == 'exploiter':
                            logger.info(f" EXPLOITER mode: Found {known_sequence['total_actions']}-action sequence "
                                      f"(completes {levels_completed_by_seq} levels), will replay to harvest proven results")
                        elif agent_mode == 'optimizer':
                            logger.info(f" OPTIMIZER mode: Found {known_sequence['total_actions']}-action sequence "
                                      f"(completes {levels_completed_by_seq} levels), will try to beat it")
                        elif agent_mode == 'pioneer':
                            logger.info(f" PIONEER mode: Found {known_sequence['total_actions']}-action sequence "
                                      f"(completes {levels_completed_by_seq} levels), will replay to frontier then explore")
                        else:
                            logger.info(f" GENERALIST mode: Found {known_sequence['total_actions']}-action sequence "
                                      f"(completes {levels_completed_by_seq} levels), will replay exactly")
                    else:
                        # No sequence available - exploiter/optimizer mode cannot proceed
                        if agent_mode == 'exploiter':
                            logger.error(f" EXPLOITER ABORT: No sequences available for {game_id} - exploiters only use proven sequences")
                            return {
                                'game_id': game_id,
                                'final_state': 'NO_SEQUENCE_AVAILABLE',
                                'final_score': 0.0,
                                'actions_taken': 0,
                                'win': False,
                                'method': 'exploiter_abort_no_sequence',
                                'error': 'Exploiter mode requires proven sequences but none available'
                            }
                        elif agent_mode == 'optimizer':
                            # RULE FIX: Optimizers ONLY work on levels WITH sequences
                            # Per Master Ruleset: "Work on beaten games ONLY" 
                            logger.error(f" OPTIMIZER ABORT: No sequences available for {game_id} - optimizers require sequences to improve")
                            return {
                                'game_id': game_id,
                                'final_state': 'NO_SEQUENCE_AVAILABLE',
                                'final_score': 0.0,
                                'actions_taken': 0,
                                'win': False,
                                'method': 'optimizer_abort_no_sequence',
                                'error': 'Optimizer mode requires existing sequences to optimize but none available'
                            }
                except Exception as e:
                    logger.debug(f"Pattern learning lookup error: {e}")
        
        try:
            # MODE-SPECIFIC SEQUENCE HANDLING
            # ALL MODES: Use best known sequence to progress efficiently
            # OPTIMIZER: Will try to beat the sequence with fewer actions
            # GENERALIST/PIONEER: Replay sequence to reach frontier quickly
            
            if known_sequence and agent_mode == 'optimizer':
                # Store target for optimization (try to beat this action count)
                target_actions = known_sequence['total_actions']
                logger.info(f" OPTIMIZER: Will use sequence and try to optimize (target: {target_actions} actions)")
                # Fall through to use the sequence like other agents
            
            # ================================================================
            # 3-TRY FALLBACK SYSTEM WITH FULL GAME RESET
            # Try up to 3 sequences in priority order. If one fails:
            # 1. Flag it as failing
            # 2. RESET THE ENTIRE GAME (sequences may target different levels)
            # 3. Try the next sequence from level 1
            # 4. After 3 failures, use multi-stage matching pipeline
            # 5. If pipeline fails, fall back to exploration with abstraction guidance
            # ================================================================
            replay_result = None
            replay_success = False
            successful_sequence = None
            all_sequences_failed = False
            abstraction_guidance = None  # Will store abstraction if all sequences fail
            multi_stage_sequence = None  # Will store result from multi-stage pipeline
            
            if ranked_sequences:
                for try_num, candidate_sequence in enumerate(ranked_sequences[:3], start=1):
                    sequence_id = candidate_sequence['sequence_id']
                    logger.info(f"[3-TRY] Attempt {try_num}/3: Trying sequence {sequence_id[:12]} "
                               f"(score {candidate_sequence['total_score']}, {candidate_sequence['total_actions']} actions)")
                    
                    # Check reputation before trying
                    validation_check = self.db.execute_query("""
                        SELECT successful_validations, total_validation_attempts,
                               CAST(successful_validations AS FLOAT) / NULLIF(total_validation_attempts, 0) as success_rate
                        FROM sequence_reputation
                        WHERE sequence_id = ?
                    """, (sequence_id,))
                    
                    if validation_check and validation_check[0]['total_validation_attempts'] >= 3:
                        sr = validation_check[0]['success_rate'] or 0.0
                        if sr > 0.5:
                            logger.info(f"  [PROVEN] {sr:.1%} success rate")
                        elif sr < 0.3:
                            logger.warning(f"  [WARN] Low success rate: {sr:.1%}")
                    
                    # PARIAH ANALYSIS (for optimizer/exploiter)
                    agent_mode = self.game_config.get('agent_operating_mode', 'generalist')
                    should_try = True
                    
                    if agent_mode in ['optimizer', 'exploiter']:
                        current_network_level = self._get_network_max_level(game_id)
                        sequence_level = int(candidate_sequence.get('total_score', 0))
                        if sequence_level >= current_network_level:
                            pariah_worth = self._analyze_pariah_worthiness(candidate_sequence, game_id)
                            if not pariah_worth['worth_challenging']:
                                logger.info(f"  [SKIP] Pariah not worth challenging: {pariah_worth['reason']}")
                                should_try = False
                    
                    if not should_try:
                        continue
                    
                    # Try replaying this sequence
                    try:
                        replay_result = await self._replay_sequence_inline(
                            game_state, 
                            candidate_sequence
                        )
                        
                        if replay_result and replay_result.get('success'):
                            # SUCCESS! This sequence worked
                            replay_success = True
                            successful_sequence = candidate_sequence
                            known_sequence = candidate_sequence  # Update for later use
                            game_state = replay_result['game_state']
                            logger.info(f"[3-TRY] SUCCESS on attempt {try_num}: {sequence_id[:12]} worked!")
                            
                            # Reset consecutive failures on success
                            self.db.execute_query("""
                                UPDATE winning_sequences SET consecutive_failures = 0 WHERE sequence_id = ?
                            """, (sequence_id,))
                            break  # Exit the loop - we found a working sequence
                        else:
                            # FAILURE - flag this sequence
                            failure_reason = f"replay_failed_attempt_{try_num}"
                            if replay_result:
                                game_state = replay_result['game_state']  # Update state even on failure
                                failure_reason = f"reached_score_{game_state.score}_not_target"
                            self._flag_sequence_failure(sequence_id, failure_reason)
                            logger.warning(f"[3-TRY] FAILED attempt {try_num}: {sequence_id[:12]} - {failure_reason}")
                            
                            # FULL GAME RESET before trying next sequence
                            # Each sequence may target different levels, so we reset to level 1
                            if try_num < min(3, len(ranked_sequences)):
                                try:
                                    logger.info(f"[3-TRY] Resetting GAME for attempt {try_num + 1}...")
                                    reset_data = await self.session_manager.reset_game()
                                    game_state = GameState.from_dict(reset_data)
                                    logger.info(f"[3-TRY] Game reset complete. New guid, Score: {game_state.score}")
                                except Exception as reset_error:
                                    logger.warning(f"[3-TRY] Game reset failed: {reset_error} - continuing anyway")
                            
                    except ValueError as e:
                        if "frame corruption" in str(e).lower():
                            # Frame corruption - flag and reset game before next try
                            self._flag_sequence_failure(sequence_id, "frame_corruption")
                            logger.error(f"[3-TRY] Frame corruption on attempt {try_num}: {sequence_id[:12]}")
                            
                            # Full game reset for next attempt
                            if try_num < min(3, len(ranked_sequences)):
                                try:
                                    reset_data = await self.session_manager.reset_game()
                                    game_state = GameState.from_dict(reset_data)
                                except Exception:
                                    pass
                            continue  # Try next sequence
                        raise
                    except Exception as e:
                        self._flag_sequence_failure(sequence_id, f"exception: {str(e)[:50]}")
                        logger.error(f"[3-TRY] Exception on attempt {try_num}: {e}")
                        
                        # Full game reset for next attempt
                        if try_num < min(3, len(ranked_sequences)):
                            try:
                                reset_data = await self.session_manager.reset_game()
                                game_state = GameState.from_dict(reset_data)
                            except Exception:
                                pass
                        continue
                
                # After loop: check if all attempts failed
                if not replay_success:
                    all_sequences_failed = True
                    logger.warning(f"[3-TRY] All {min(3, len(ranked_sequences))} ranked sequence attempts failed")
                    
                    # STAGE 2: Try multi-stage matching pipeline as fallback
                    # This uses looser matching strategies (prefix, suffix, subsequence, conceptual)
                    if hasattr(self, 'matching_pipeline') and self.matching_pipeline:
                        try:
                            logger.info(f"[MULTI-STAGE] Trying multi-stage matching pipeline...")
                            
                            # Reset level one more time for fresh start
                            try:
                                reset_data = await self.session_manager.reset_level()
                                game_state = GameState.from_dict(reset_data)
                            except Exception:
                                pass
                            
                            game_type = game_id.split('-')[0] if '-' in game_id else game_id
                            current_actions = self.game_config.get('current_actions', [])
                            agent_config = {
                                'risk_tolerance': self.game_config.get('risk_tolerance', 0.5),
                                'abstraction_threshold': self.game_config.get('abstraction_threshold', 0.7)
                            }
                            
                            sequence_actions, stage_used, metadata = self.matching_pipeline.get_sequence_with_fallback(
                                game_id=game_id,
                                level_number=1,  # Start from level 1
                                current_actions=current_actions,
                                agent_config=agent_config
                            )
                            
                            if sequence_actions and stage_used != 'random':
                                logger.info(f"[MULTI-STAGE] {stage_used.upper()} match found: {len(sequence_actions)} actions, "
                                           f"confidence {metadata.get('confidence', 0):.2f}")
                                # Store for use in exploration phase
                                multi_stage_sequence = {
                                    'actions': sequence_actions,
                                    'stage': stage_used,
                                    'confidence': metadata.get('confidence', 0)
                                }
                            else:
                                logger.info(f"[MULTI-STAGE] Pipeline exhausted, falling back to exploration")
                                
                        except Exception as e:
                            logger.debug(f"Multi-stage pipeline error: {e}")
                    
                    # STAGE 3: Get abstraction guidance for pure exploration
                    if not multi_stage_sequence and hasattr(self, 'abstraction_engine') and self.abstraction_engine:
                        try:
                            game_type = game_id.split('-')[0] if '-' in game_id else game_id
                            abstraction_guidance = self.abstraction_engine.get_conceptual_hints(game_type)  # type: ignore[attr-defined]
                            if abstraction_guidance:
                                logger.info(f"[ABSTRACTION] Using conceptual hints: {abstraction_guidance.get('hints', [])[:3]}")
                        except Exception as e:
                            logger.debug(f"Abstraction guidance error: {e}")
            
            # Handle replay results (success, partial success, or all failed)
            if replay_success and successful_sequence:
                known_sequence = successful_sequence
                
                if game_state.state == "WIN":
                    # Full win from replay! Finish and return
                    level_completions = int(game_state.score)  # Each level = 1 point
                    actions_taken = len(json.loads(known_sequence['action_sequence']))
                    await self.session_manager.finish_game(game_state.state, game_state.score, level_completions, actions_taken)
                    
                    # PHASE 2: Deduct actions from agent's budget
                    if agent_id:
                        self.session_manager.deduct_actions_used(agent_id, game_id)
                    
                    # PHASE 2.5: Knowledge Recombination (AUTOMATIC)
                    recombinations = []
                    if agent_id:
                        recombinations = self._explore_sequence_recombination(
                            agent_id, game_id, level_completions
                        )
                    
                    logger.info(f" COMPLETE WIN via cumulative sequence replay!")
                    return {
                        'game_id': game_id,
                        'final_state': game_state.state,
                        'final_score': game_state.score,
                        'actions_taken': actions_taken,
                        'win': True,
                        'method': 'cumulative_sequence_replay',
                        'sequence_id': known_sequence['sequence_id'],
                        'recombinations_created': len(recombinations)
                    }
                else:
                    # Replay succeeded but didn't win completely
                    # We're now at the frontier (highest known level)
                    frontier_level = int(game_state.score) + 1  # Score 2 = completed 2 levels, now on level 3
                    logger.info(f" Cumulative replay reached frontier (Level {frontier_level}, Score {game_state.score})")
                    
                    # ROLE-SPECIFIC FRONTIER BEHAVIOR
                    # EXPLOITER: STOP here - exploiters ONLY use proven sequences, never explore
                    if agent_mode == 'exploiter':
                        logger.info(f" EXPLOITER: Stopping at frontier (Level {frontier_level}) - exploiters only use proven sequences")
                        await self.session_manager.finish_game(game_state.state, game_state.score, int(game_state.score), len(json.loads(known_sequence['action_sequence'])))
                        return {
                            'game_id': game_id,
                            'final_state': game_state.state,
                            'final_score': game_state.score,
                            'actions_taken': len(json.loads(known_sequence['action_sequence'])),
                            'win': game_state.state == 'WIN',
                            'method': 'exploiter_sequence_replay',
                            'sequence_id': known_sequence['sequence_id']
                        }
                    
                    # CRITICAL FIX: Force game state to NOT_FINISHED for PIONEERS and GENERALISTS
                    # Some games (like ls20) incorrectly report WIN/GAME_OVER after partial completion
                    # Pioneers and Generalists should continue playing until action budget exhausted
                    if game_state.state != "NOT_FINISHED":
                        logger.warning(f"[WARN] Game state is '{game_state.state}' at frontier - forcing to NOT_FINISHED for continuation")
                        game_state.state = "NOT_FINISHED"
                    
                    # PIONEER/GENERALIST/OPTIMIZER: Continue playing until action budget exhausted
                    mode_name = (agent_mode or 'generalist').upper()
                    logger.info(f" {mode_name}: At frontier (Level {frontier_level}), continuing until action budget exhausted")
                    # Continue to game loop below
            
            elif all_sequences_failed:
                # All 3 ranked sequences failed - check fallback options
                if multi_stage_sequence:
                    # Multi-stage pipeline found a match (prefix/suffix/subsequence/conceptual)
                    logger.info(f"[EXPLORATION FALLBACK] Using multi-stage {multi_stage_sequence['stage'].upper()} match "
                               f"({len(multi_stage_sequence['actions'])} actions, confidence {multi_stage_sequence['confidence']:.2f})")
                    self.game_config['multi_stage_guidance'] = multi_stage_sequence
                elif abstraction_guidance:
                    # Use abstraction hints for guided exploration
                    logger.info(f"[EXPLORATION FALLBACK] Using abstraction hints for guided exploration")
                    self.game_config['abstraction_hints'] = abstraction_guidance
                else:
                    logger.info(f"[EXPLORATION FALLBACK] Pure exploration mode (no guidance available)")
                # Continue to game loop for exploration
            
            elif not ranked_sequences:
                # No sequences available at all - pure exploration
                logger.info(f"[EXPLORATION] No sequences available, pure exploration mode")
                # Continue to game loop for exploration

            action_count = 0
            level_action_count = 0  # Track actions per level
            start_time = datetime.now()
            previous_score = 0.0  # Track score for level completion detection
            level_completions = 0  # Track how many levels completed
            current_level = 1  # Start at level 1 (first challenge to complete)
            level_start_action = 0  # Track where each level starts
            
            # API RESET tracking (NEW - hybrid approach)
            level_api_resets = 0  # Track resets used on current level
            MAX_API_RESETS_PER_LEVEL = 2  # Max 2 API resets per level
            API_RESET_THRESHOLD = 1000  # API reset after 1000 no-progress actions (OPTIMIZER only, increased for more exploration)
            
            # STUCK STATE DETECTION (for games like ls20 that finish but don't report it)
            consecutive_no_frame_change = 0  # Track actions with no frame change
            STUCK_STATE_THRESHOLD = 100  # If 100 consecutive actions have no frame change and no score increase, game is likely stuck/finished (only applies to pioneers at frontier)

            # API ERROR TRACKING (to prevent spam when API is having issues)
            consecutive_api_errors = 0  # Track consecutive API errors
            MAX_CONSECUTIVE_API_ERRORS = 5  # Break out after 5 consecutive errors
            api_error_backoff = 0  # Seconds to wait after API error (exponential backoff)

            # Game loop - continue until action budget exhausted
            # BUGFIX: Don't trust game_state.state - some games report WIN prematurely
            # Only stop on action limit or explicit session shutdown
            while action_count < self.game_config['max_total_actions']:

                # Check if session is still active (graceful shutdown detection)
                # Check BOTH is_running AND is_shutting_down
                # When shutdown is requested, we should exit immediately and save current state
                if not self.session_manager.is_running:
                    logger.info(f"[END] Session stopped, ending game gracefully")
                    break
                
                if self.session_manager.is_shutting_down:
                    logger.info(f"[STOP] SHUTDOWN REQUESTED - ending game immediately to save state")
                    logger.info(f"   Current score: {game_state.score}, Actions: {action_count}")
                    # Break immediately - the finally block will save results
                    break
                
                # CRITICAL: If game reports WIN/GAME_OVER but we have actions left, keep trying
                # Some games report completion prematurely (e.g., ls20 after level 1)
                if game_state.state != "NOT_FINISHED":
                    logger.warning(f"[WARN] Game reports '{game_state.state}' but actions remain ({action_count}/{self.game_config['max_total_actions']}) - forcing continuation")
                    game_state.state = "NOT_FINISHED"

                try:
                    # Update action handler with level progress for dynamic spam tolerance
                    self.action_handler.update_level_progress(
                        level_action_count, 
                        self.game_config['max_actions_per_level']
                    )
                    
                    # Store previous score before action
                    previous_score = game_state.score
                    
                    # CRITICAL FIX: Synchronize current_level with actual score
                    # After level completion, score = 1, 2, 3, etc.
                    # But current_level might still be at old value if we're past the score-increase detection
                    actual_level_from_score = int(game_state.score) + 1  # Score 1 = completed level 1, now on level 2
                    if actual_level_from_score > current_level:
                        logger.info(f" Level sync: current_level was {current_level}, updating to {actual_level_from_score} (score={game_state.score})")
                        current_level = actual_level_from_score
                        level_action_count = 0  # Reset level counter
                        level_start_action = action_count
                        consecutive_no_frame_change = 0
                    
                    # Optimizer-specific: Save more efficient sequences when found
                    # (This happens naturally through normal gameplay and sequence capture)
                    
                    # API error backoff - wait if we had recent errors
                    if api_error_backoff > 0:
                        logger.info(f"[TIME] API error backoff: waiting {api_error_backoff}s before next action")
                        await asyncio.sleep(api_error_backoff)
                        api_error_backoff = 0  # Reset after waiting
                    
                    # Select action
                    action_succeeded = False
                    try:
                        if action_callback:
                            action_result = await action_callback(game_state, self.action_handler)
                            if isinstance(action_result, GameState):
                                game_state = action_result
                            elif isinstance(action_result, str):
                                # BUGFIX: Pass current_level to ensure action traces are logged with correct level
                                game_state = await self._execute_action(action_result, game_state, "", current_level)
                            else:
                                raise ValueError(f"Invalid action callback result: {action_result}")
                        else:
                            # Use default action selection
                            action, reasoning = await self._select_action(game_state)
                            game_state = await self._execute_action(action, game_state, reasoning, current_level)
                        
                        # Action succeeded - reset error counter
                        consecutive_api_errors = 0
                        action_succeeded = True
                        
                    except Exception as action_error:
                        # Check if this is an API error (400, 500, connection issue, etc.)
                        error_msg = str(action_error).lower()
                        is_api_error = any(indicator in error_msg for indicator in [
                            '400', 'bad_request', 'bad request',  # Game session ended/invalid
                            '500', 'internal server error', 'non-json response',
                            'server disconnected', 'connection', 'timeout'
                        ])
                        
                        if is_api_error:
                            consecutive_api_errors += 1
                            logger.warning(f"[WARN] API error #{consecutive_api_errors}: {action_error}")
                            
                            # 400 BAD_REQUEST means game session is DEAD - exit immediately
                            # No point retrying, the game has ended on the server side
                            is_session_dead = any(indicator in error_msg for indicator in [
                                '400', 'bad_request', 'bad request'
                            ])
                            
                            if is_session_dead:
                                logger.error(f"[STOP] Game session terminated (400 BAD_REQUEST) - game has ended on server")
                                break  # Exit game loop immediately
                            
                            if consecutive_api_errors >= MAX_CONSECUTIVE_API_ERRORS:
                                logger.error(f"[STOP] Too many consecutive API errors ({consecutive_api_errors}), ending game")
                                break  # Exit game loop
                            
                            # Exponential backoff: 1s, 2s, 4s, 8s, 16s
                            api_error_backoff = min(2 ** (consecutive_api_errors - 1), 16)
                            logger.info(f"   → Will wait {api_error_backoff}s before retry")
                            continue  # Skip rest of loop, retry action after backoff
                        else:
                            # Not an API error, re-raise to be caught by outer handlers
                            raise

                    # Only increment counters if action succeeded
                    if action_succeeded:
                        action_count += 1
                        level_action_count += 1
                    
                    # Phase 4.5: Learn from action outcome for sensation system
                    if agent_id and self.game_config.get('enable_sensation_navigation', True):
                        self._learn_from_action_outcome(action, previous_score, game_state, agent_id)
                    
                    # Check for significant score increase (level completion)
                    score_increase = game_state.score - previous_score
                    
                    # STUCK STATE DETECTION: Only for FRONTIER exploration (pioneers on highest known level)
                    # Not needed for known levels - those should use sequences or optimizer strategies
                    # This prevents false positives during sequence replay while helping pioneers detect truly stuck games
                    frame_changed = False
                    
                    # Check if this level is at the frontier (no known sequences)
                    is_frontier_level = False
                    if agent_mode == 'pioneer' and self.game_config.get('enable_pattern_learning', True):
                        # Quick check if any ACTIVE sequences exist for this level
                        # (Inactive sequences are trash - don't count them as "covered")
                        game_type = game_id.split('-')[0] if '-' in game_id else game_id
                        frontier_check = self.db.execute_query("""
                            SELECT COUNT(*) as seq_count
                            FROM winning_sequences
                            WHERE game_id LIKE ? AND level_number = ? AND is_active = 1
                        """, (f"{game_type}-%", current_level))
                        is_frontier_level = (not frontier_check or frontier_check[0]['seq_count'] == 0)
                    
                    # Only apply stuck state detection at the frontier
                    if is_frontier_level and hasattr(self.action_handler, 'visual_analyzer') and game_state.frame:
                        frame_changed = self.action_handler.visual_analyzer.update_frame_change_tracking(
                            game_state.frame,
                            game_state.score
                        )
                        
                        if not frame_changed and score_increase == 0:
                            consecutive_no_frame_change += 1
                            
                            if consecutive_no_frame_change >= STUCK_STATE_THRESHOLD:
                                logger.warning(
                                    f" FRONTIER STUCK STATE: {consecutive_no_frame_change} consecutive actions with "
                                    f"no frame change and no score increase on FRONTIER level {current_level}."
                                )
                                logger.info(
                                    f"   Current score: {game_state.score:.1f}, Actions taken: {action_count}, "
                                    f"Level {current_level} actions: {level_action_count}"
                                )
                                logger.info(f"   Terminating pioneer exploration to avoid wasting actions")
                                break  # Exit game loop
                        else:
                            # Reset counter if we had a frame change or score increase
                            consecutive_no_frame_change = 0
                    elif not is_frontier_level:
                        # Not at frontier, don't track stuck state (sequences should handle this)
                        consecutive_no_frame_change = 0
                    
                    # Track score improvements (no destructive resets - removed to preserve pattern learning)
                    
                    # Calculate score increase to detect level completion
                    score_increase = game_state.score - previous_score
                    
                    # BUGFIX: Only increment level_completions on full level completion (score increase >= 1.0)
                    # Previously incremented on >= 0.5 which caused overcounting with partial progress
                    if score_increase >= 1.0:  # Full level completion (ARC levels give 1.0 point each)
                        level_completions += 1
                        logger.info(f" Level {current_level} completed! Score: {previous_score} → {game_state.score} (+{score_increase})")
                        logger.info(f" Level {current_level} stats: {level_action_count} actions, {level_api_resets} API resets used")
                        
                        # Reset level-specific counters for next level
                        level_api_resets = 0  # Fresh reset budget for new level
                        
                        # Pattern Learning: Capture sequence on level completion
                        # BUGFIX: Don't check game_state.state - some games report WIN prematurely
                        # Just verify score increased (which we already did above)
                        if self.game_config.get('enable_pattern_learning', True):
                            
                            # SIMPLE MAPPING: level_number = score
                            # Score 1.0 = level 1 (first challenge completed)
                            # Score 2.0 = level 2 (second challenge completed)
                            # Score N.0 = level N (Nth challenge completed)
                            level_for_storage = int(game_state.score)
                            
                            # ================================================================
                            # BUG FIX (2024-12-03): Use CUMULATIVE capture for L2+
                            # ================================================================
                            # PROBLEM: "level_X_win" triggered level-specific capture, which
                            # only saved the actions for THAT level. This created L2 sequences
                            # that couldn't be replayed (missing L1 actions to get there first).
                            # 
                            # FIX: For L2+, use "partial_progress" reason which triggers 
                            # cumulative capture (L1 through current level). This creates
                            # complete sequences that can be replayed from game start.
                            # 
                            # L1 still uses level-specific (no cumulative needed - it IS L1)
                            # ================================================================
                            if level_for_storage == 1:
                                capture_reason = "level_1_win"  # L1: level-specific is fine
                            else:
                                capture_reason = f"partial_progress_{level_for_storage}_levels"  # L2+: CUMULATIVE
                            
                            sequence_id = self._capture_winning_sequence(
                                game_id, 
                                game_state.score, 
                                level_number=level_for_storage,
                                reason=capture_reason,
                                level_completions=level_completions  # Pass actual completions
                            )
                            if sequence_id:
                                if level_for_storage > 1:
                                    logger.info(f"[PKG] Captured CUMULATIVE sequence for levels 1-{level_for_storage} (score={game_state.score}): {sequence_id}")
                                else:
                                    logger.info(f" Captured level {level_for_storage} winning sequence (score={game_state.score}): {sequence_id}")
                        
                        # Agent Self-Model: Track controlled objects on level completion
                        if agent_id and hasattr(self, 'agent_self_model'):
                            try:
                                # Build action/frame history for this level
                                action_history = self.session_manager.action_history[-level_action_count:] if hasattr(self.session_manager, 'action_history') else []  # type: ignore[attr-defined]
                                frame_history = self.session_manager.frame_history[-level_action_count:] if hasattr(self.session_manager, 'frame_history') else []  # type: ignore[attr-defined]
                                
                                if action_history and frame_history:
                                    controlled, confidence = self.agent_self_model.identify_controlled_objects(
                                        game_id, current_level, action_history, frame_history
                                    )
                                    if controlled and confidence > 0.3:
                                        self.agent_self_model.store_control_map(
                                            agent_id, game_id, current_level, controlled, confidence
                                        )
                            except Exception as e:
                                logger.debug(f"Agent self-model tracking error: {e}")
                        
                        # Move to next level
                        previous_score = game_state.score  # Update for next level detection
                        current_level += 1
                        level_action_count = 0  # Reset level action counter
                        level_start_action = action_count  # Mark where this level starts
                        consecutive_no_frame_change = 0  # CRITICAL FIX: Reset stuck state counter on level completion
                        
                        # DEPRECATED: Old level-by-level sequence chaining loop
                        # Now using cumulative sequence approach (replay best sequence ONCE to frontier)
                        # This entire loop is DISABLED in favor of the cleaner approach above
                        # Keeping code for reference but it should NOT execute
                        # 
                        # The new approach:
                        # 1. Get BEST cumulative sequence (highest score)
                        # 2. Replay it ONCE (reaches frontier)
                        # 3. Generalist stops, Pioneer continues exploring
                        #
                        # OLD APPROACH (DISABLED):
                        if False:  # DISABLED - using cumulative approach instead
                            # Try partial sequence matching first
                            partial_match = self._find_partial_sequence_match(
                                game_id, game_state.frame, current_level
                            )
                            
                            if partial_match:
                                logger.info(f" CHECKPOINT FOUND: Resuming from known sequence, "
                                          f"skipping {partial_match['actions_skipped']} actions!")
                                
                                # Replay from checkpoint
                                try:
                                    replay_result = await self._replay_sequence_inline(
                                        game_state,
                                        partial_match['sequence'],
                                        start_index=partial_match['start_index']
                                    )
                                except ValueError as e:
                                    if "frame corruption" in str(e).lower():
                                        logger.error(f"[FAIL] FRAME CORRUPTION during checkpoint replay - aborting game")
                                        await self.session_manager.finish_game("GAME_OVER", 0.0, 0, 0)
                                        return {
                                            'game_id': game_id,
                                            'final_state': 'GAME_OVER',
                                            'final_score': 0.0,
                                            'actions_taken': 0,
                                            'win': False,
                                            'method': 'aborted_frame_corruption'
                                        }
                                    raise
                                
                                if replay_result and replay_result['success']:
                                    game_state = replay_result['game_state']
                                    logger.info(f" Checkpoint replay successful! State: {game_state.state}, Score: {game_state.score}")
                                    consecutive_no_frame_change = 0  # Reset stuck state counter after successful replay
                                    
                                    # If we won, break out of sequence chain loop
                                    if game_state.state == "WIN":
                                        logger.info(f" WON via checkpoint replay!")
                                        break
                                    # Otherwise update tracking and continue to check for next level
                                    previous_score = game_state.score
                                else:
                                    # Partial match replay failed, try complete sequence
                                    break
                            else:
                                # No partial match, check for complete sequence for new level
                                # MODE-AWARE: Behavior depends on agent mode
                                next_level_sequence = self._get_best_sequence_for_game(game_id, current_level)
                                
                                # Check if Pioneer has reached frontier (highest known level for this game)
                                if agent_mode == 'pioneer' and next_level_sequence is None:
                                    logger.info(f" PIONEER: Reached frontier (Level {current_level}), no known sequences - EXPLORING NEW TERRITORY!")
                                    break  # Exit sequence chain loop, continue with exploration
                                
                                if next_level_sequence:
                                    # OPTIMIZER: Don't replay, just note target and break
                                    if agent_mode == 'optimizer':
                                        target_actions = next_level_sequence['total_actions']
                                        logger.info(f" OPTIMIZER: Level {current_level} target = {target_actions} actions, trying to beat it")
                                        # Store target but don't replay - optimizer explores
                                        self.game_config[f'level_{current_level}_target'] = target_actions
                                        break  # Exit sequence chain, optimizer explores
                                    else:
                                        # GENERALIST/PIONEER: Replay sequence
                                        logger.info(f" Found winning sequence for level {current_level}, attempting replay...")
                                        
                                        # FIX: Actually replay the sequence instead of just logging it!
                                        # This enables knowledge sharing for Level 2+
                                        try:
                                            replay_result = await self._replay_sequence_inline(
                                                game_state,
                                                next_level_sequence,
                                                start_index=0
                                            )
                                        except ValueError as e:
                                            if "frame corruption" in str(e).lower():
                                                logger.error(f"[FAIL] FRAME CORRUPTION during level sequence replay - aborting game")
                                                await self.session_manager.finish_game("GAME_OVER", 0.0, 0, 0)
                                                return {
                                                    'game_id': game_id,
                                                    'final_state': 'GAME_OVER',
                                                    'final_score': 0.0,
                                                    'actions_taken': 0,
                                                    'win': False,
                                                    'method': 'aborted_frame_corruption'
                                                }
                                            raise
                                        
                                        if replay_result and replay_result['success']:
                                            replay_initial_score = previous_score
                                            game_state = replay_result['game_state']
                                            replay_final_score = game_state.score
                                            logger.info(f" Level {current_level} sequence replay successful! Score: {replay_initial_score} → {replay_final_score}, State: {game_state.state}")
                                            consecutive_no_frame_change = 0  # Reset stuck state counter after successful replay
                                            
                                            # Update tracking with replay results
                                            previous_score = replay_final_score
                                            
                                            # If we won completely, exit main loop
                                            if game_state.state == "WIN":
                                                logger.info(f"� WON via level {current_level} sequence replay!")
                                                break
                                            
                                            # Check if replay completed one or more levels
                                            levels_completed = int(replay_final_score - replay_initial_score)
                                            if levels_completed > 0:
                                                level_completions += levels_completed
                                                current_level += levels_completed
                                                level_action_count = 0
                                                level_start_action = action_count
                                                level_api_resets = 0
                                                logger.info(f" PIONEER/GENERALIST: Replay completed {levels_completed} level(s), now at level {current_level}")
                                                # Loop continues to check for next level sequence
                                            else:
                                                # Replay didn't complete a level, break out
                                                logger.warning(f" Level {current_level} sequence replay didn't complete level, continuing with exploration")
                                                break
                                        else:
                                            logger.info(f" Level {current_level} sequence replay failed, continuing with exploration")
                                            break  # Exit sequence chain, continue with exploration
                                else:
                                    # No sequence found for this level - track exploration
                                    if agent_mode == 'generalist':
                                        logger.info(f" GENERALIST: No sequence for level {current_level}, exploring")
                                    
                                    # Log that agent is exploring this level (no sequence used)
                                    agent_id = self.game_config.get('agent_id', 'unknown')
                                    session_id = self.session_manager.current_session_id
                                    game_id = self.game_config.get('game_id', 'unknown')
                                    
                                    if session_id and game_id:
                                        self.db.log_level_sequence_usage(
                                            session_id=session_id,
                                            game_id=game_id,
                                            agent_id=agent_id,
                                            level_number=current_level,
                                            used_sequence=False,
                                            exploration_mode='smart_exploration'
                                        )
                                    
                                    break  # Exit sequence chain
                        
                        # If we broke out of sequence chain due to WIN, exit main game loop
                        if game_state.state == "WIN":
                            break

                    
                    # Check if exceeded max actions for this level
                    if level_action_count >= self.game_config['max_actions_per_level']:
                        logger.warning(f"[TIME] Reached max actions ({self.game_config['max_actions_per_level']}) for level {current_level}")
                        
                        # BUGFIX: Move to next level instead of ending game
                        # Agent may have made progress but not completed level
                        # Only end if no score progress at all
                        if game_state.score > previous_score:
                            logger.info(f"Score improved ({previous_score} → {game_state.score}), moving to next level")
                            current_level += 1
                            level_action_count = 0
                            level_start_action = action_count
                            previous_score = game_state.score
                        else:
                            logger.info(f"No score progress on level {current_level}, trying next level anyway")
                            current_level += 1
                            level_action_count = 0
                            level_start_action = action_count
                        # Continue until total action budget exhausted
                    
                    logger.debug(f"Action {action_count} (Level {current_level}-{level_action_count}): State={game_state.state}, Score={game_state.score}")

                    # REMOVED: Don't break on WIN/GAME_OVER - these are unreliable
                    # Games may report WIN after partial completion (e.g., ls20 after level 1)
                    # Only stop when action budget exhausted

                except ValueError as e:
                    # Handle frame corruption - only breaks if recovery failed
                    error_msg = str(e).lower()
                    if "frame corruption" in error_msg:
                        if "recovery failed" in error_msg:
                            logger.error(f"[FAIL] FRAME CORRUPTION: Recovery attempted but failed - ending game")
                        else:
                            logger.error(f"[FAIL] FRAME CORRUPTION detected - ending game")
                        break
                    else:
                        logger.error(f"ValueError in action {action_count}: {e}")
                        break
                except RuntimeError as e:
                    # Handle session shutdown gracefully
                    error_msg = str(e).lower()
                    if ("shutting down" in error_msg or 
                        "no active session" in error_msg or 
                        "no active" in error_msg or
                        "client session closed" in error_msg):
                        logger.info(f" Session no longer running, ending game gracefully")
                        break
                    else:
                        logger.error(f"Runtime error in action {action_count}: {e}")
                        break
                except AttributeError as e:
                    # Handle NoneType errors during shutdown (API client session is None)
                    if "'NoneType' object has no attribute" in str(e):
                        logger.info(f" API client unavailable (shutdown in progress), ending game gracefully")
                        break
                    else:
                        logger.error(f"Attribute error in action {action_count}: {e}")
                        break
                except Exception as e:
                    error_msg = str(e).lower()
                    # Check for shutdown-related errors
                    if ("shutting down" in error_msg or 
                        "session" in error_msg or 
                        "client" in error_msg or
                        "nonetype" in error_msg):
                        logger.info(f" Session/client error detected, ending game gracefully")
                        break
                    # Critical errors that should stop
                    if "authentication" in error_msg or "api_key" in error_msg:
                        logger.error(f"Critical error in action {action_count}: {e}")
                        break
                    # Log other errors but don't show full traceback during shutdown
                    logger.error(f"Error in action {action_count}: {e}")

            # Calculate results
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            results = {
                'game_id': game_id,
                'final_state': game_state.state,
                'final_score': game_state.score,
                'actions_taken': action_count,
                'duration_seconds': duration,
                'win': game_state.state == "WIN",
                'level_completions': level_completions,
                'levels_attempted': current_level,
                'start_time': start_time,
                'end_time': end_time
            }

            # TASK #6: Agent Self-Model - Track performance metrics
            if agent_id:
                self._track_agent_performance(
                    agent_id=agent_id,
                    game_id=game_id,
                    final_score=game_state.score,
                    actions_taken=action_count,
                    level_completions=level_completions,
                    win=(game_state.state == "WIN"),
                    duration_seconds=duration
                )
            
            # Diversity Mode: Track game diversity (Rule 10: integrated, Rule 2: database-only)
            if self.game_config.get('diversity_mode'):
                self._track_game_diversity(game_id, game_state.score, action_count)

            # Finish game in session manager (CRITICAL FIX: Pass level_completions AND actions_taken!)
            await self.session_manager.finish_game(game_state.state, game_state.score, level_completions, action_count)
            
            # PHASE 2: Deduct actions from agent's budget
            if agent_id:
                self.session_manager.deduct_actions_used(agent_id, game_id)

            # Pattern Learning: Capture final sequence (Rule 2: Database-only)
            if self.game_config.get('enable_pattern_learning', True):
                # CRITICAL: Capture ANY progress made (not just WINs)
                # This ensures we save sequences for score 3.0 even if agent fails level 4
                # Future agents can replay this to guarantee the same minimum score
                if game_state.state == "WIN":
                    # Full game win - capture complete sequence
                    # Only if we actually completed levels in THIS session
                    if level_completions > 0:
                        sequence_id = self._capture_winning_sequence(
                            game_id, 
                            game_state.score,
                            level_number=current_level,
                            reason="full_game_win",
                            level_completions=level_completions
                        )
                        if sequence_id:
                            results['learned_sequence_id'] = sequence_id
                            logger.info(f" Captured full game winning sequence: {sequence_id}")
                    else:
                        logger.info(f"[WARN] WIN state but no level_completions in this session - skipping sequence capture")
                
                elif game_state.score > 0 and level_completions > 0:
                    # Partial progress - capture what we achieved
                    # Score 3.0 = completed 3 levels, future agents should replay this
                    # CRITICAL: Only if we completed levels in THIS session (not from replay)
                    levels_completed_for_capture = int(game_state.score)
                    sequence_id = self._capture_winning_sequence(
                        game_id,
                        game_state.score,
                        level_number=levels_completed_for_capture,
                        reason=f"partial_progress_{levels_completed_for_capture}_levels",
                        level_completions=level_completions
                    )
                    if sequence_id:
                        results['learned_sequence_id'] = sequence_id
                        logger.info(f" Captured partial progress sequence (score {game_state.score}): {sequence_id}")
                        logger.info(f"   → Future agents can replay this to guarantee {levels_completed_for_capture} level(s) minimum")
                elif game_state.score > 0 and level_completions == 0:
                    logger.debug(f"Score {game_state.score} but no NEW level_completions - skipping sequence capture (likely from replay or shutdown)")
            
            # PHASE 2.5: Knowledge Recombination (AUTOMATIC - runs after EVERY game)
            # This is the viral evolution accelerator - opportunistic recombination
            if agent_id:
                recombinations = self._explore_sequence_recombination(
                    agent_id, 
                    game_id,
                    current_level
                )
                if recombinations:
                    results['recombinations_created'] = len(recombinations)
                    logger.info(f"🧬 Agent {agent_id[:8]} created {len(recombinations)} sequence recombinations")
            
            # PHASE 3: Viral Packages & Pariahs (AUTOMATIC - runs after EVERY game)
            # Bidirectional evolution: extract success patterns AND failure patterns
            if agent_id:
                generation = self.game_config.get('generation', 0)
                
                # Import viral engine (lazy load to avoid circular dependencies)
                from viral_package_engine import ViralPackageEngine
                viral_engine = ViralPackageEngine(self.db)
                
                # If WIN: Create viral package from winning sequence
                if results['win'] and results.get('learned_sequence_id'):
                    package_id = viral_engine.create_viral_package_from_sequence(
                        results['learned_sequence_id'],
                        agent_id,
                        generation
                    )
                    if package_id:
                        results['viral_package_created'] = package_id
                        logger.info(f"[VIRAL] Created viral package {package_id[:12]} from winning sequence")
                        
                        # Spread to nearby agents (horizontal transfer opportunity)
                        # Get 3 random other agents for potential infection
                        nearby_agents = self.db.execute_query("""
                            SELECT agent_id FROM agents 
                            WHERE is_active = TRUE AND agent_id != ?
                            ORDER BY RANDOM()
                            LIMIT 3
                        """, (agent_id,))
                        
                        spread_count = 0
                        for target in nearby_agents:
                            if viral_engine.spread_viral_package(package_id, agent_id, target['agent_id'], generation):
                                spread_count += 1
                        
                        if spread_count > 0:
                            logger.info(f"[VIRAL] Viral package spread to {spread_count} agents")
                
                # If LOSS: Create pariah from failure pattern
                elif not results['win'] and game_state.score < 1.0:
                    # Get failed action sequence
                    action_traces = self.db.execute_query("""
                        SELECT action_number, coordinates
                        FROM action_traces
                        WHERE game_id = ? AND session_id = ?
                        ORDER BY timestamp ASC
                    """, (game_id, self.session_manager.current_session_id))
                    
                    if action_traces:
                        failed_actions = [t['action_number'] for t in action_traces]
                        failed_coords = []
                        for t in action_traces:
                            if t.get('coordinates'):
                                try:
                                    coord = json.loads(t['coordinates'])
                                    failed_coords.append(tuple(coord))
                                except:
                                    pass
                        
                        pariah_id = viral_engine.create_pariah_from_failure(
                            game_id,
                            agent_id,
                            failed_actions,
                            failed_coords,
                            game_state.score,
                            generation
                        )
                        
                        if pariah_id:
                            results['pariah_created'] = pariah_id
                            logger.info(f"  Created pariah {pariah_id[:12]} from failure (score: {game_state.score:.2f})")
                            
                            # Spread awareness to nearby agents (horizontal transfer)
                            nearby_agents = self.db.execute_query("""
                                SELECT agent_id FROM agents 
                                WHERE is_active = TRUE AND agent_id != ?
                                ORDER BY RANDOM()
                                LIMIT 3
                            """, (agent_id,))
                            
                            aware_count = 0
                            for target in nearby_agents:
                                if viral_engine.spread_pariah_awareness(pariah_id, agent_id, target['agent_id'], generation):
                                    aware_count += 1
                            
                            if aware_count > 0:
                                logger.info(f"  Pariah awareness spread to {aware_count} agents")

            logger.info(f"Game {game_id} completed: {game_state.state}, Score: {game_state.score}, "
                       f"Actions: {action_count}, Levels Completed: {level_completions}/{current_level}")
            return results

        except Exception as e:
            logger.error(f"Error playing game {game_id}: {e}")
            # Still try to finish the game gracefully
            try:
                # Try to get current level_completions if available
                level_completions = int(game_state.score) if 'game_state' in locals() and game_state else 0
                action_count_fallback = action_count if 'action_count' in locals() else 0
                await self.session_manager.finish_game("ERROR", 0.0, level_completions, action_count_fallback)
            except:
                pass
            raise

    async def _select_action(self, game_state: GameState) -> tuple[str, str]:
        """Select the next action to take with reasoning.
        
        Uses:
        1. NEW: Hierarchical subgoal planning (multi-step strategy)
        2. PHASE 4.5: Sensation-based navigation (emotional intelligence for actions 1-7)
        3. PHASE 3: Viral package influence (prefer successful patterns)
        4. PHASE 3: Pariah avoidance (avoid known failures)
        5. Meta-learning pattern detection
        6. Default strategy

        Args:
            game_state: Current game state

        Returns:
            Tuple of (action, reasoning) where reasoning explains why this action was chosen
        """
        agent_id = self.game_config.get('agent_id')
        
        # === NEW: Check for active subgoal plan ===
        if agent_id and hasattr(self, 'subgoal_planner') and self.subgoal_planner:
            try:
                current_game_id = self.session_manager.current_game_id
                session_id = self.session_manager.current_session_id
                
                if current_game_id and session_id:
                    # Check if we have an active plan
                    active_plan = self.db.execute_query("""
                        SELECT plan_id, current_subgoal
                        FROM subgoal_plans
                        WHERE agent_id = ? AND game_id = ? AND session_id = ? 
                          AND status = 'active'
                        ORDER BY created_at DESC
                        LIMIT 1
                    """, (agent_id, current_game_id, session_id))
                    
                    if active_plan and active_plan[0]:
                        # Get actions for current subgoal
                        plan_id = active_plan[0]['plan_id']
                        
                        # Convert frame to list format
                        frame_list = game_state.frame if isinstance(game_state.frame, list) else []
                        available_actions = list(range(1, 8))  # ACTION1-ACTION7
                        
                        if frame_list:
                            subgoal_action_ids = self.subgoal_planner.get_next_subgoal_actions(
                                plan_id=plan_id,
                                current_frame=frame_list,
                                available_actions=available_actions
                            )
                            
                            if subgoal_action_ids:
                                action_id = subgoal_action_ids[0]
                                reasoning = f"Following hierarchical subgoal plan (plan_id: {plan_id[:8]})"
                                logger.info(f" {reasoning}: ACTION{action_id}")
                                return f"ACTION{action_id}", reasoning
                    
                    # No active plan - create one if game is making progress
                    elif game_state.score > 0 and game_state.score < 20:
                        frame_list = game_state.frame if isinstance(game_state.frame, list) else []
                        if frame_list:
                            plan_id = self.subgoal_planner.create_plan(
                                agent_id=agent_id,
                                game_id=current_game_id,
                                session_id=session_id,
                                current_frame=frame_list,
                                current_score=game_state.score,
                                generation=self.game_config.get('generation', 0)
                            )
                            if plan_id:
                                logger.info(f" Created hierarchical plan for game {current_game_id[:8]}")
                            
            except Exception as e:
                logger.debug(f"Subgoal planning error: {e}")
        
        # PHASE 4.5: Sensation-based analysis for navigation actions
        sensation_biases = {}
        navigation_state = 0.0
        
        # Get agent mode to determine if sensation is allowed
        agent_mode = self._get_agent_operating_mode(agent_id) if agent_id else None
        
        # SENSATION ACCESS BY ROLE (Phase 4.5 - per Master Ruleset):
        # - Pioneers: NO (pure exploration, no emotional biases)
        # - Optimizers: YES (need sensation to make efficiency decisions)
        # - Generalists: YES (feelings restored - need emotional intelligence)
        # - Exploiters: YES (can use sensation when replaying sequences)
        sensation_allowed = (agent_mode != 'pioneer')
        
        if agent_id and self.game_config.get('enable_sensation_navigation', True):
            if not sensation_allowed:
                # Pioneers restricted from sensation - must use pure exploration
                logger.debug(f" Pioneer mode: Sensation navigation disabled (pure exploration)")
            else:
                try:
                    # Analyze frame for emotional context
                    frame_data = self._convert_game_state_for_sensation_analysis(game_state)
                    
                    # Update agent's navigation state based on perceptions
                    sensation_context = self._analyze_sensation_context(frame_data, agent_id)
                    navigation_state = self.sensation_engine.update_navigation_state(
                        agent_id, 
                        sensation_context.get('dominant_sensation', 0.0),
                        {
                            'game_id': self.session_manager.current_game_id,
                            'generation': self.game_config.get('generation', 0),
                            'game_score': game_state.score,
                            'recent_success_rate': self._calculate_recent_success_rate_from_game_state(game_state)
                        }
                    )
                    
                    # Get sensation-based action biases for navigation actions (1-7)
                    available_navigation_actions = [1, 2, 3, 4, 5, 6, 7]  # All navigation actions
                    biased_actions = self.sensation_engine.bias_action_selection(
                        agent_id, available_navigation_actions, navigation_state
                    )
                    
                    sensation_biases = {action: bias for action, bias in biased_actions}
                    
                    # Store perceived objects for learning
                    self._last_perceived_objects = sensation_context.get('perceived_objects', [])
                    
                    if sensation_biases:
                        emotion = self._get_emotion_label(navigation_state)
                        logger.debug(f"🧠 Agent feeling {emotion} (state: {navigation_state:.2f})")
                        logger.debug(f"   Action biases: {sensation_biases}")
                        logger.debug(f"   Perceived objects: {self._last_perceived_objects}")
                    
                except Exception as e:
                    logger.debug(f"Phase 4.5 sensation error: {e}")
        
        # PHASE 3: Get viral package and pariah influence
        action_weights = {}
        action_penalties = {}
        
        if agent_id:
            try:
                from viral_package_engine import ViralPackageEngine
                viral_engine = ViralPackageEngine(self.db)
                
                # Get positive influence from viral packages
                action_weights = viral_engine.get_package_action_weights(agent_id)
                
                # Get negative influence from pariahs
                action_penalties = viral_engine.get_pariah_action_penalties(agent_id)
                
                if action_weights:
                    logger.debug(f"[VIRAL] Viral packages suggest: {list(action_weights.keys())[:3]}")
                if action_penalties:
                    logger.debug(f"  Pariahs warn against: {list(action_penalties.keys())[:3]}")
                    
            except Exception as e:
                logger.debug(f"Phase 3 influence error: {e}")
        
        # Try meta-learning pattern detection
        if (self.game_config.get('enable_pattern_learning', True) and 
            game_state.frame is not None):
            
            try:
                # Convert frame to numpy array if needed
                frame = game_state.frame
                if not isinstance(frame, np.ndarray):
                    frame = np.array(frame)
                
                pattern_result = self._meta_learn_pattern_from_frame(frame)
                
                if pattern_result and pattern_result.get('confidence', 0) > 0.5:
                    logger.info(f"🧠 Meta-learner detected pattern: {pattern_result['pattern_type']}")
                    logger.info(f"   Rule: {pattern_result['rule']['type']}, Confidence: {pattern_result['confidence']:.2f}")
                    
                    actions = pattern_result.get('actions', [])
                    if actions:
                        # Store the discovered pattern for future use
                        self._store_discovered_pattern(pattern_result)
                        
                        # Execute first action from the pattern
                        first_action = actions[0]
                        if first_action['type'] == 'ACTION6':
                            coord = first_action['coordinate']
                            logger.info(f" Applying meta-learned pattern: ACTION6 at {coord}")
                            logger.info(f"   Reason: {first_action['reason']}")
                            
                            # Store remaining actions for next iterations
                            if not hasattr(self, '_pattern_action_queue'):
                                self._pattern_action_queue = []
                            self._pattern_action_queue = actions[1:]  # Queue remaining actions
                            
                            reasoning = f"Meta-learned {pattern_result['pattern_type']} pattern (confidence: {pattern_result['confidence']:.2f})"
                            return "ACTION6", reasoning  # Will be executed with stored coordinates
                            
            except Exception as e:
                logger.debug(f"Meta-learning error (falling back to default): {e}")
        
        # Check if we have queued pattern actions
        if hasattr(self, '_pattern_action_queue') and self._pattern_action_queue:
            next_action = self._pattern_action_queue.pop(0)
            if next_action['type'] == 'ACTION6':
                reasoning = f"Continuing meta-learned pattern: {next_action['reason']}"
                logger.info(f" {reasoning}: ACTION6 at {next_action['coordinate']}")
                return "ACTION6", reasoning
        
        # Fall back to default action selection WITH viral/pariah influence
        strategy = self.game_config.get('strategy', 'balanced')
        
        # Check if this is an unbeaten game (no level completions by any agent)
        current_game_id = self.session_manager.current_game_id
        if current_game_id:
            is_unbeaten_game = self._is_unbeaten_game(current_game_id)
            if is_unbeaten_game:
                logger.info(f" UNBEATEN GAME DETECTED: {current_game_id} - using full exploration mode")
                strategy = "unbeaten_exploration"
        else:
            is_unbeaten_game = False
        
        # ===================================================================
        # CRITICAL: NETWORK HISTORY ABSTRACTION FOR FRONTIER EXPLORATION
        # When at frontier (no proven sequences), use collective wisdom from
        # network's historical gameplay on this game type + level combination.
        # This implements the user's requirement: "abstract the history of 
        # their own gameplay as agents on this level from previous games"
        # ===================================================================
        network_suggested_action = None
        base_action: str = "ACTION1"  # Default, will be overwritten
        current_level = int(game_state.score) + 1  # Score 2 = completed 2 levels, now on level 3
        
        if current_game_id and agent_id:
            network_suggestion = self._get_network_action_wisdom(
                game_id=current_game_id,
                level_number=current_level,
                agent_id=agent_id,
                current_frame=game_state.frame
            )
            
            if network_suggestion:
                network_suggested_action = network_suggestion.get('action')
                confidence = network_suggestion.get('confidence', 0.0)
                reasoning_detail = network_suggestion.get('reasoning', 'Network history')
                
                # Use network suggestion if confidence is high enough
                if confidence >= 0.4:
                    logger.info(f"🌐 NETWORK WISDOM: ACTION{network_suggested_action} (confidence: {confidence:.2f}) - {reasoning_detail}")
                    base_action = f"ACTION{network_suggested_action}"
                    # Skip to applying biases below
                else:
                    logger.debug(f"Network suggestion (ACTION{network_suggested_action}) confidence too low ({confidence:.2f})")
                    # Low confidence - fall back to smart action selection
                    base_action = await self.action_handler.smart_action_selection(game_state, strategy, is_unbeaten_game)
        
        # If no network suggestion at all, use smart action selection
        if network_suggested_action is None:
            base_action = await self.action_handler.smart_action_selection(game_state, strategy, is_unbeaten_game)
        
        # PHASE 4.5: Apply sensation-based biasing for navigation actions (1-7)
        if sensation_biases and agent_id:
            action_num = int(base_action.replace("ACTION", "")) if isinstance(base_action, str) else base_action
            
            # Check if current action has sensation bias
            if action_num in sensation_biases:
                current_bias = sensation_biases[action_num]
                
                # If current action has strong negative bias, consider alternatives
                if current_bias < -0.4:
                    emotion = self._get_emotion_label(navigation_state)
                    logger.info(f"🧠 {emotion.capitalize()} agent avoiding {base_action} (sensation bias: {current_bias:.2f})")
                    
                    # Find best sensation-biased alternative
                    alternatives = [(act, bias) for act, bias in sensation_biases.items() if bias > 0.1]
                    
                    if alternatives:
                        best_alt, best_bias = max(alternatives, key=lambda x: x[1])
                        logger.info(f"🧠 Switching to ACTION{best_alt} (positive sensation bias: {best_bias:.2f})")
                        base_action = f"ACTION{best_alt}"
                        sensation_reasoning = f"{emotion.capitalize()} state (nav: {navigation_state:.2f}) - switched from negative bias to positive alternative (bias: {best_bias:.2f})"
                    else:
                        sensation_reasoning = f"{emotion.capitalize()} state (nav: {navigation_state:.2f}) - avoiding negative bias (bias: {current_bias:.2f})"
                
                # If current action has positive bias, reinforce it
                elif current_bias > 0.2:
                    emotion = self._get_emotion_label(navigation_state)
                    logger.info(f"🧠 {emotion.capitalize()} agent reinforcing {base_action} (positive sensation: {current_bias:.2f})")
                    sensation_reasoning = f"{emotion.capitalize()} state (nav: {navigation_state:.2f}) - positive sensation bias (bias: {current_bias:.2f})"
                else:
                    sensation_reasoning = None
            else:
                sensation_reasoning = None
        else:
            sensation_reasoning = None
        
        # PHASE 3: Apply viral package / pariah influence to action selection
        viral_reasoning = None  # Initialize before conditional blocks
        if action_weights or action_penalties:
            # Convert base_action to int
            action_num = int(base_action.replace("ACTION", "")) if isinstance(base_action, str) else base_action
            
            # Calculate net influence
            weight = action_weights.get(action_num, 0.0)
            penalty = action_penalties.get(action_num, 0.0)
            net_influence = weight - penalty
            
            # If net influence is strongly negative (pariah > package), try alternative
            if net_influence < -0.3:
                logger.info(f"  Avoiding {base_action} (pariah warning: {penalty:.2f})")
                
                # Find best alternative action (highest weight, lowest penalty)
                alternatives = []
                for act_num in range(1, 8):  # ACTION1-ACTION7
                    alt_weight = action_weights.get(act_num, 0.0)
                    alt_penalty = action_penalties.get(act_num, 0.0)
                    alternatives.append((act_num, alt_weight - alt_penalty))
                
                # Sort by net influence
                alternatives.sort(key=lambda x: x[1], reverse=True)
                
                if alternatives and alternatives[0][1] > net_influence:
                    best_alt = alternatives[0][0]
                    alt_influence = alternatives[0][1]
                    reasoning = f"Viral package suggested ACTION{best_alt} (net influence: {alt_influence:.2f}) - avoiding pariah penalty on {base_action} (penalty: {penalty:.2f})"
                    logger.info(f"[VIRAL] Switching to ACTION{best_alt} (viral package suggestion)")
                    
                    # Include sensation reasoning if available
                    if sensation_reasoning:
                        reasoning = f"{reasoning} | {sensation_reasoning}"
                    
                    return f"ACTION{best_alt}", reasoning
            
            elif net_influence > 0.3:
                logger.info(f"[VIRAL] Reinforcing {base_action} (viral package boost: {weight:.2f})")
                viral_reasoning = f"Viral package reinforcement (weight: {weight:.2f})"
            else:
                viral_reasoning = None
        else:
            viral_reasoning = None
        
        # Build final reasoning from all sources
        reasoning_parts = []
        if is_unbeaten_game:
            reasoning_parts.append("Unbeaten game - full exploration")
        if sensation_reasoning:
            reasoning_parts.append(sensation_reasoning)
        if viral_reasoning:
            reasoning_parts.append(viral_reasoning)
        if not reasoning_parts:
            reasoning_parts.append(f"Standard {strategy} strategy")
        
        final_reasoning = " | ".join(reasoning_parts)
        
        return base_action, final_reasoning

    async def _execute_action(self, action: str, game_state: GameState, reasoning: str = "", current_level: int = 1) -> GameState:
        """Execute an action with reasoning sent to ARC API.

        Args:
            action: Action to execute (string like "ACTION1" or int like 1)
            game_state: Current game state
            reasoning: Human-readable explanation of why this action was chosen
            current_level: Current level number (for trace logging)

        Returns:
            New game state
        """
        # Normalize action to string format if it's an integer
        if isinstance(action, int):
            action = f"ACTION{action}"
        
        # Generate default reasoning if not provided
        if not reasoning:
            agent_mode = self._get_agent_operating_mode(self.game_config.get('agent_id'))
            score = game_state.score
            
            # Build context-aware reasoning
            reasoning_parts = []
            if agent_mode:
                reasoning_parts.append(f"{agent_mode.upper()} mode")
            reasoning_parts.append(f"Score: {score}")
            reasoning = " | ".join(reasoning_parts) if reasoning_parts else f"Exploring with {action}"
        
        # Format reasoning as JSON object (≤16 KB) for ARC API
        reasoning_json = self._format_reasoning_for_api(
            action=action,
            reasoning_text=reasoning,
            game_state=game_state,
            current_level=current_level
        )
        
        if action == "ACTION6":
            # Check if we have meta-learned coordinates to use
            if hasattr(self, '_pattern_action_queue') and self._pattern_action_queue:
                # Use coordinates from meta-learning
                next_action = self._pattern_action_queue[0]  # Peek at next action
                if next_action['type'] == 'ACTION6':
                    x, y = next_action['coordinate']
                    reason = next_action['reason']
                    full_reasoning = f"{reasoning} | Meta-pattern: {reason}"
                    logger.info(f"ACTION6 at ({x}, {y}): {full_reasoning}")
                else:
                    # Fall back to smart coordinates
                    x, y, reason = self.action_handler.get_smart_coordinates(
                        game_state.frame,
                        strategy="visual"
                    )
                    full_reasoning = f"{reasoning} | Visual: {reason}"
                    logger.info(f"ACTION6 at ({x}, {y}): {full_reasoning}")
            else:
                # Use smart coordinate selection
                x, y, reason = self.action_handler.get_smart_coordinates(
                    game_state.frame,
                    strategy="visual"
                )
                full_reasoning = f"{reasoning} | Visual: {reason}"
                logger.info(f"ACTION6 at ({x}, {y}): {full_reasoning}")
            
            # Update reasoning JSON with coordinate info
            if reasoning_json:
                reasoning_json['coordinate'] = {'x': x, 'y': y}
                reasoning_json['visual_reason'] = reason
            
            # Send ACTION6 with reasoning JSON
            new_state = await self.action_handler.send_action_6(x, y, game_state.frame, reasoning=reasoning_json, level_number=current_level)
            
            # Track frame changes to detect productive actions
            if new_state and new_state.frame:
                # Pass current score to help adaptive exploration
                current_score = new_state.score if hasattr(new_state, 'score') else None
                frame_changed = self.action_handler.visual_analyzer.update_frame_change_tracking(
                    new_state.frame, 
                    current_score
                )
                if not frame_changed:
                    logger.debug(f"ACTION6 at ({x}, {y}) did not change frame")
                    
            return new_state
        else:
            # Execute regular action - convert ACTION1 to send_action_1 format
            # Extract number from ACTION string (e.g., "ACTION1" -> "1")
            action_num = action.replace("ACTION", "")
            method_name = f"send_action_{action_num}"
            if hasattr(self.action_handler, method_name):
                method = getattr(self.action_handler, method_name)
                # Pass reasoning JSON and level_number to action handler
                return await method(reasoning=reasoning_json, level_number=current_level)
            else:
                raise ValueError(f"Unknown action: {action}")

    async def play_multiple_games(self, game_ids: List[str],
                                max_games: Optional[int] = None) -> List[Dict[str, Any]]:
        """Play multiple games sequentially.

        Args:
            game_ids: List of game IDs to play
            max_games: Maximum number of games to play

        Returns:
            List of game results
        """
        if max_games:
            game_ids = game_ids[:max_games]

        results = []
        for i, game_id in enumerate(game_ids):
            logger.info(f"Playing game {i+1}/{len(game_ids)}: {game_id}")

            try:
                result = await self.play_single_game(game_id)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to play game {game_id}: {e}")
                results.append({
                    'game_id': game_id,
                    'final_state': 'ERROR',
                    'final_score': 0.0,
                    'actions_taken': 0,
                    'error': str(e)
                })

        return results

    async def run_session(self, mode: str = "gameplay",
                         max_games: Optional[int] = None) -> Dict[str, Any]:
        """Run a complete gaming session.

        Args:
            mode: Session mode
            max_games: Maximum number of games to play

        Returns:
            Session summary
        """
        logger.info(f"Starting {mode} session")

        # Start session
        session_id = await self.session_manager.start_session(mode)

        try:
            # Get available games
            available_games = await self.session_manager.get_available_games()
            logger.info(f"Found {len(available_games)} available games")

            if not available_games:
                raise ValueError("No games available")

            # Extract game IDs
            game_ids = [game.get('id', game.get('game_id', str(i)))
                       for i, game in enumerate(available_games)]

            # Apply diversity-focused game selection if enabled
            if self.game_config.get('diversity_mode') and self.game_config.get('enforce_game_diversity') and max_games:
                game_ids = self._select_diverse_games(game_ids, max_games)
            elif max_games:
                # Standard mode: just limit count
                game_ids = game_ids[:max_games]

            results = await self.play_multiple_games(game_ids)

            # Calculate session statistics
            total_games = len(results)
            wins = sum(1 for r in results if r.get('win', False))
            total_score = sum(r.get('final_score', 0) for r in results)
            total_actions = sum(r.get('actions_taken', 0) for r in results)

            session_summary = {
                'session_id': session_id,
                'mode': mode,
                'total_games': total_games,
                'wins': wins,
                'win_rate': wins / total_games if total_games > 0 else 0.0,
                'total_score': total_score,
                'avg_score': total_score / total_games if total_games > 0 else 0.0,
                'total_actions': total_actions,
                'avg_actions_per_game': total_actions / total_games if total_games > 0 else 0.0,
                'game_results': results
            }

            logger.info(f"Session completed: {wins}/{total_games} wins, avg score: {session_summary['avg_score']:.2f}")
            return session_summary

        finally:
            # Ensure session is properly closed
            await self.session_manager.shutdown()

    def get_performance_stats(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get performance statistics.

        Args:
            session_id: Optional session ID filter

        Returns:
            Performance statistics
        """
        # Get data from database
        game_results = self.session_manager.db.get_game_results(session_id=session_id)

        if not game_results:
            return {"message": "No game results found"}

        total_games = len(game_results)
        wins = sum(1 for r in game_results if r.get('win_detected', False))
        total_score = sum(r.get('final_score', 0) for r in game_results)
        total_actions = sum(r.get('total_actions', 0) for r in game_results)

        stats = {
            'total_games': total_games,
            'wins': wins,
            'losses': total_games - wins,
            'win_rate': wins / total_games if total_games > 0 else 0.0,
            'total_score': total_score,
            'avg_score': total_score / total_games if total_games > 0 else 0.0,
            'total_actions': total_actions,
            'avg_actions_per_game': total_actions / total_games if total_games > 0 else 0.0
        }

        # Add recent performance
        recent_games = game_results[:10]  # Last 10 games
        if recent_games:
            recent_wins = sum(1 for r in recent_games if r.get('win_detected', False))
            stats['recent_win_rate'] = recent_wins / len(recent_games)
            stats['recent_avg_score'] = sum(r.get('final_score', 0) for r in recent_games) / len(recent_games)

        return stats

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session_manager.is_running:
            await self.session_manager.shutdown()

    # ========================================================================
    # DIVERSITY-FOCUSED GAME SELECTION (Rule 10: Integrated)
    # ========================================================================

    def _select_diverse_games(self, game_ids: List[str], max_games: int) -> List[str]:
        """
        Select games with diversity focus to prevent overfitting.
        
        Prioritizes:
        1. Novel games (never played by current agent)
        2. Under-exposed games (played <max_repeats times)
        3. Random selection from remaining games
        
        Args:
            game_ids: Available game IDs
            max_games: Maximum games to select
            
        Returns:
            List of selected game IDs optimized for diversity
        """
        if not max_games or max_games <= 0:
            return game_ids
        
        # Get current agent ID if available (from callbacks)
        agent_id = getattr(self, '_current_agent_id', None)
        if not agent_id:
            # No agent context, fallback to random selection
            import random
            return random.sample(game_ids, min(max_games, len(game_ids)))
        
        max_repeats = self.game_config.get('max_repeats_per_game', 5)
        
        # Query game exposure for this agent
        game_exposure = self.db.execute_query("""
            SELECT game_id, attempts, is_novel_game
            FROM agent_game_diversity
            WHERE agent_id = ?
        """, (agent_id,))
        
        exposure_map = {row['game_id']: row for row in game_exposure} if game_exposure else {}
        
        # Categorize games
        novel_games = []
        under_exposed = []
        over_exposed = []
        
        for game_id in game_ids:
            if game_id not in exposure_map:
                # Never played by this agent = novel
                novel_games.append(game_id)
            elif exposure_map[game_id]['attempts'] < max_repeats:
                # Played but not too much
                under_exposed.append((game_id, exposure_map[game_id]['attempts']))
            else:
                # Played too many times, avoid (anti-overfitting)
                over_exposed.append(game_id)
        
        # Build selection priority: novel > under_exposed > over_exposed
        import random
        
        selected = []
        
        # Priority 1: Novel games (shuffle for randomness)
        random.shuffle(novel_games)
        selected.extend(novel_games[:max_games])
        
        # Priority 2: Under-exposed games (prefer least played)
        if len(selected) < max_games:
            under_exposed.sort(key=lambda x: x[1])  # Sort by attempts (ascending)
            remaining = max_games - len(selected)
            selected.extend([g[0] for g in under_exposed[:remaining]])
        
        # Priority 3: Over-exposed games (only if necessary)
        if len(selected) < max_games:
            random.shuffle(over_exposed)
            remaining = max_games - len(selected)
            selected.extend(over_exposed[:remaining])
        
        logger.info(f"Diversity game selection: {len(novel_games)} novel, {len(under_exposed)} under-exposed, {len(over_exposed)} over-exposed")
        logger.info(f"Selected: {len([g for g in selected if g in novel_games])} novel games")
        
        return selected[:max_games]

    def _track_game_diversity(self, game_id: str, final_score: float, actions_taken: int):
        """
        Track game diversity metrics (Rule 2: database-only).
        
        Args:
            game_id: Game ID that was played
            final_score: Final score achieved
            actions_taken: Total actions taken
        """
        agent_id = getattr(self, '_current_agent_id', None)
        if not agent_id:
            return  # No agent context, skip tracking
        
        try:
            # Check if this is a novel game for this agent
            existing = self.db.execute_query("""
                SELECT attempts, first_attempt_score, best_score
                FROM agent_game_diversity
                WHERE agent_id = ? AND game_id = ?
            """, (agent_id, game_id))
            
            if not existing or len(existing) == 0:
                # Novel game - first time seeing it
                self.db.execute_query("""
                    INSERT INTO agent_game_diversity 
                    (agent_id, game_id, attempts, first_attempt_score, best_score, 
                     last_attempt_score, is_novel_game, few_shot_improvement, last_played)
                    VALUES (?, ?, 1, ?, ?, ?, TRUE, 0.0, CURRENT_TIMESTAMP)
                """, (agent_id, game_id, final_score, final_score, final_score))
                
                logger.info(f" Diversity: Novel game tracked - {game_id} (score: {final_score})")
            else:
                # Repeated game - update metrics
                first_score = existing[0]['first_attempt_score']
                best_score = max(existing[0]['best_score'], final_score)
                attempts = existing[0]['attempts'] + 1
                few_shot_improvement = final_score - first_score if attempts == 2 else existing[0].get('few_shot_improvement', 0.0)
                
                self.db.execute_query("""
                    UPDATE agent_game_diversity
                    SET attempts = ?,
                        best_score = ?,
                        last_attempt_score = ?,
                        few_shot_improvement = ?,
                        is_novel_game = FALSE,
                        last_played = CURRENT_TIMESTAMP
                    WHERE agent_id = ? AND game_id = ?
                """, (attempts, best_score, final_score, few_shot_improvement, agent_id, game_id))
                
                if attempts == 2:
                    improvement = few_shot_improvement
                    logger.info(f" Diversity: Few-shot learning - {game_id} improvement: {improvement:+.3f}")
                elif attempts > self.game_config.get('max_repeats_per_game', 5):
                    logger.warning(f" Diversity: Overfitting risk - {game_id} played {attempts} times")
                    
        except Exception as e:
            logger.error(f"Error tracking game diversity: {e}")



    def _track_agent_performance(self, agent_id: str, game_id: str, 
                                final_score: float, actions_taken: int,
                                level_completions: int, win: bool,
                                duration_seconds: float):
        """
        Track agent performance metrics for self-model (Task #6).
        Records performance to agent_performance_history table.
        
        Args:
            agent_id: Agent ID
            game_id: Game that was played
            final_score: Final score achieved
            actions_taken: Total actions taken
            level_completions: Levels completed
            win: Whether the game was won
            duration_seconds: Game duration
        """
        try:
            # Get current performance snapshot
            current = self.db.execute_query("""
                SELECT games_played, total_score, total_actions, 
                       total_levels_completed, wins, best_score, worst_score
                FROM agent_performance_history
                WHERE agent_id = ?
                ORDER BY recorded_at DESC
                LIMIT 1
            """, (agent_id,))
            
            if current:
                # Update cumulative metrics
                games_played = current[0]['games_played'] + 1
                total_score = current[0]['total_score'] + final_score
                total_actions = current[0]['total_actions'] + actions_taken
                total_levels = current[0]['total_levels_completed'] + level_completions
                wins = current[0]['wins'] + (1 if win else 0)
                best_score = max(current[0]['best_score'], final_score)
                worst_score = min(current[0]['worst_score'], final_score) if current[0]['worst_score'] > 0 else final_score
            else:
                # First game for this agent
                games_played = 1
                total_score = final_score
                total_actions = actions_taken
                total_levels = level_completions
                wins = 1 if win else 0
                best_score = final_score
                worst_score = final_score
            
            # Calculate averages
            avg_score = total_score / games_played
            avg_actions = total_actions / games_played
            avg_levels = total_levels / games_played
            avg_efficiency = total_score / total_actions if total_actions > 0 else 0.0
            win_rate = wins / games_played
            
            # Get prestige score (discovery_prestige in agents table)
            prestige_data = self.db.execute_query("""
                SELECT discovery_prestige as prestige_score
                FROM agents
                WHERE agent_id = ?
            """, (agent_id,))
            prestige_score = prestige_data[0]['prestige_score'] if prestige_data else 0.0
            
            # Get sequence contribution
            sequences_discovered = self.db.execute_query("""
                SELECT COUNT(*) as cnt
                FROM winning_sequences
                WHERE agent_id = ?
            """, (agent_id,))[0]['cnt']
            
            sequences_validated = self.db.execute_query("""
                SELECT COUNT(*) as cnt
                FROM sequence_validation_attempts
                WHERE agent_id = ?
            """, (agent_id,))[0]['cnt'] if self.db.execute_query("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='sequence_validation_attempts'
            """) else 0
            
            # Insert performance snapshot
            self.db.execute_query("""
                INSERT INTO agent_performance_history (
                    agent_id, games_played, total_score, avg_score,
                    best_score, worst_score, total_levels_completed,
                    avg_levels_per_game, total_actions, avg_actions_per_game,
                    avg_efficiency, wins, win_rate, sequences_discovered,
                    sequences_validated, prestige_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (agent_id, games_played, total_score, avg_score,
                  best_score, worst_score, total_levels, avg_levels,
                  total_actions, avg_actions, avg_efficiency, wins,
                  win_rate, sequences_discovered, sequences_validated,
                  prestige_score))
            
            self.db.checkpoint_wal()
            
            logger.debug(f" Agent {agent_id} performance: {games_played} games, "
                        f"avg score {avg_score:.2f}, win rate {win_rate:.1%}")
            
        except Exception as e:
            logger.error(f"Error tracking agent performance: {e}")



    def _get_agent_self_awareness(self, agent_id: str) -> Dict[str, Any]:
        """
        Get agent's self-awareness data from performance history (Task #6).
        Allows agents to know their own performance and adjust behavior.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Dict with performance metrics and self-awareness insights
        """
        try:
            # Get latest performance snapshot
            perf_data = self.db.execute_query("""
                SELECT *
                FROM agent_performance_history
                WHERE agent_id = ?
                ORDER BY recorded_at DESC
                LIMIT 1
            """, (agent_id,))
            
            if not perf_data:
                return {
                    'has_history': False,
                    'confidence': 0.5,  # Neutral confidence for new agents
                    'strategy_adjustment': 'explore'  # Default to exploration
                }
            
            perf = perf_data[0]
            
            # Calculate self-awareness metrics
            confidence = min(1.0, perf['win_rate'] + (perf['avg_score'] / 10.0))
            
            # Determine strategy based on performance
            if perf['win_rate'] > 0.7:
                strategy = 'exploit'  # High win rate - exploit what works
            elif perf['win_rate'] < 0.3:
                strategy = 'explore'  # Low win rate - try new approaches
            else:
                strategy = 'balanced'  # Moderate - balance exploration/exploitation
            
            # Check if improving or declining
            if perf['games_played'] >= 5:
                # Get previous snapshot for trend
                prev_data = self.db.execute_query("""
                    SELECT avg_score, win_rate
                    FROM agent_performance_history
                    WHERE agent_id = ?
                    ORDER BY recorded_at DESC
                    LIMIT 1 OFFSET 1
                """, (agent_id,))
                
                if prev_data:
                    score_trend = perf['avg_score'] - prev_data[0]['avg_score']
                    win_trend = perf['win_rate'] - prev_data[0]['win_rate']
                    
                    if score_trend > 0.5 or win_trend > 0.1:
                        trend = 'improving'
                    elif score_trend < -0.5 or win_trend < -0.1:
                        trend = 'declining'
                    else:
                        trend = 'stable'
                else:
                    trend = 'unknown'
            else:
                trend = 'insufficient_data'
            
            return {
                'has_history': True,
                'games_played': perf['games_played'],
                'avg_score': perf['avg_score'],
                'best_score': perf['best_score'],
                'win_rate': perf['win_rate'],
                'avg_efficiency': perf['avg_efficiency'],
                'confidence': confidence,
                'strategy_adjustment': strategy,
                'performance_trend': trend,
                'prestige': perf['prestige_score'],
                'sequences_discovered': perf['sequences_discovered']
            }
            
        except Exception as e:
            logger.error(f"Error getting agent self-awareness: {e}")
            return {
                'has_history': False,
                'confidence': 0.5,
                'strategy_adjustment': 'explore'
            }
    
    def _apply_self_awareness_to_strategy(self, agent_id: str, base_config: Dict) -> Dict:
        """
        Apply self-awareness insights to adjust agent strategy.
        
        Args:
            agent_id: Agent ID
            base_config: Base game configuration
            
        Returns:
            Modified configuration based on self-awareness
        """
        awareness = self._get_agent_self_awareness(agent_id)
        
        if not awareness['has_history']:
            return base_config  # No history, use base config
        
        # Adjust exploration rate based on performance
        if awareness['strategy_adjustment'] == 'explore':
            base_config['exploration_rate'] = min(1.0, base_config.get('exploration_rate', 0.3) * 1.5)
            logger.debug(f"Agent {agent_id}: Increasing exploration (low win rate)")
        elif awareness['strategy_adjustment'] == 'exploit':
            base_config['exploration_rate'] = max(0.1, base_config.get('exploration_rate', 0.3) * 0.5)
            logger.debug(f"Agent {agent_id}: Decreasing exploration (high win rate)")
        
        # Adjust confidence-based parameters
        base_config['confidence_level'] = awareness['confidence']
        
        # Log self-awareness
        if awareness['games_played'] > 0:
            logger.info(f"🧠 Agent {agent_id} self-awareness: "
                       f"Win rate {awareness['win_rate']:.1%}, "
                       f"Avg score {awareness['avg_score']:.2f}, "
                       f"Strategy: {awareness['strategy_adjustment']}, "
                       f"Trend: {awareness['performance_trend']}")
        
        return base_config

    # ========================================================================
    # AGENT OPERATING MODE HELPERS
    # ========================================================================
    
    def _format_reasoning_for_api(self, action: str, reasoning_text: str, 
                                  game_state: GameState, current_level: int) -> Dict[str, Any]:
        """
        Format reasoning as JSON object for ARC API (≤16 KB).
        
        Converts human-readable reasoning text into structured JSON metadata
        for transmission to ARC API. Includes agent context, game state,
        and decision factors.
        
        Args:
            action: Action being taken (e.g., "ACTION6")
            reasoning_text: Human-readable reasoning string
            game_state: Current game state
            current_level: Current level number
            
        Returns:
            Dictionary with reasoning metadata (JSON-serializable, ≤16 KB)
        """
        agent_id = self.game_config.get('agent_id')
        agent_mode = self._get_agent_operating_mode(agent_id) if agent_id else None
        
        reasoning_obj = {
            'action': action,
            'reasoning': reasoning_text,
            'level': current_level,
            'score': game_state.score,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add agent context if available
        if agent_id:
            reasoning_obj['agent_id'] = agent_id
        if agent_mode:
            reasoning_obj['agent_mode'] = agent_mode
        
        # Add genome config if available
        genome = self.game_config.get('genome')
        if genome:
            # Include key genome parameters (not full genome to stay under 16 KB)
            reasoning_obj['genome'] = {
                'agent_type': genome.get('agent_type'),
                'exploration_rate': genome.get('exploration_rate'),
                'learning_rate': genome.get('learning_rate')
            }
        
        # Add strategy context
        reasoning_obj['strategy'] = self.game_config.get('strategy', 'balanced')
        reasoning_obj['learning_mode'] = self.game_config.get('learning_mode', 'smart_exploration')
        
        # Ensure JSON is ≤16 KB
        reasoning_json = json.dumps(reasoning_obj)
        if len(reasoning_json) > 16384:  # 16 KB limit
            # Truncate reasoning text if too large
            max_reasoning_len = len(reasoning_text) - (len(reasoning_json) - 16384) - 100
            reasoning_obj['reasoning'] = reasoning_text[:max_reasoning_len] + '...[truncated]'
            reasoning_json = json.dumps(reasoning_obj)
        
        return reasoning_obj

    def _get_agent_operating_mode(self, agent_id: Optional[str]) -> Optional[str]:
        """
        Get the current operating mode for an agent.
        
        Args:
            agent_id: Agent ID to check
            
        Returns:
            'pioneer', 'optimizer', 'generalist', or None if not set
        """
        if not agent_id:
            return None
            
        try:
            # Query most recent mode assignment for this agent
            mode_data = self.db.execute_query("""
                SELECT operating_mode
                FROM agent_operating_modes
                WHERE agent_id = ?
                ORDER BY assigned_timestamp DESC
                LIMIT 1
            """, (agent_id,))
            
            if mode_data:
                return mode_data[0]['operating_mode']
        except Exception as e:
            logger.debug(f"Error getting agent operating mode: {e}")
        
        return None

    # ========================================================================
    # PATTERN LEARNING METHODS (Rule 10: Integrated into existing file)
    # ========================================================================

    def _capture_winning_sequence(self, game_id: str, final_score: float, 
                                 level_number: int = 1, reason: str = "win",
                                 level_completions: int = 0) -> Optional[str]:
        """
        Capture winning sequence for pattern learning (Rule 2: Database-only).
        Called automatically after wins OR level completions when enable_pattern_learning=True.
        
        CRITICAL: For full_game_win, captures ALL actions from level 1 through final level.
        This creates a CUMULATIVE sequence that can be replayed to reach the same state.
        
        VALIDATION: Only saves sequences if level_completions > 0, preventing graceful
        shutdown garbage from polluting the sequence database.
        
        Args:
            game_id: Game that was won
            final_score: Final score achieved
            level_number: Level number that was completed (default 1)
            reason: Reason for capture ("win", "level_1_completion", "full_game_win", etc.)
            level_completions: Number of levels actually completed in THIS session (CRITICAL)
            
        Returns:
            sequence_id if captured, None otherwise
        """
        if not self.game_config.get('enable_pattern_learning', True):
            return None
        
        # ================================================================
        # CRITICAL FIX: Prevent garbage sequences from polluting database
        # ================================================================
        # Multiple validation layers to ensure only USEFUL sequences are saved:
        # 1. Must have completed at least 1 level in THIS session
        # 2. Score must be > 0 (actual progress made)
        # 3. Minimum action threshold to filter out glitches/errors
        # ================================================================
        
        # Validation 1: Level completions check
        if level_completions < 1:
            logger.debug(f"Skipping sequence capture - no levels completed (level_completions={level_completions})")
            return None
        
        # Validation 2: Score check
        if final_score <= 0:
            logger.debug(f"Skipping sequence capture - score is 0 or negative (score={final_score})")
            return None
        
        # VALIDATION 3: Minimum action check
        # Allow ANY action count - if the agent completed a level, the sequence is valid
        MIN_ACTIONS_FOR_VALID_SEQUENCE = 3  # Allow action >= 3 wins
        
        try:
            session_id = self.session_manager.current_session_id
            if not session_id:
                return None
            
            # Pre-check action count before doing full capture
            action_count_check = self.db.execute_query("""
                SELECT COUNT(*) as cnt FROM action_traces
                WHERE game_id = ? AND session_id = ?
            """, (game_id, session_id))
            
            action_count = action_count_check[0]['cnt'] if action_count_check else 0
            
            if action_count < MIN_ACTIONS_FOR_VALID_SEQUENCE:
                logger.debug(f"Skipping sequence capture - no actions recorded")
                return None
            
            # ================================================================
            # CRITICAL: Cumulative vs Level-Specific Capture
            # ================================================================
            # For "full_game_win" or multi-level captures: Get ALL actions from level 1 onwards
            # For level-specific captures: Get only actions for that specific level
            # This ensures cumulative sequences contain the COMPLETE path to that state
            # ================================================================
            
            if reason == "full_game_win" or (reason.startswith("partial_progress") and level_number > 1):
                # CUMULATIVE CAPTURE: Get ALL actions from level 1 through current level
                # This is the "stacked sequence" that can replay the entire journey
                action_traces = self.db.execute_query("""
                    SELECT action_number, coordinates, frame_before, frame_after, level_number
                    FROM action_traces
                    WHERE game_id = ? AND session_id = ? AND level_number <= ?
                    ORDER BY timestamp ASC
                """, (game_id, session_id, level_number))
                logger.info(f"[PKG] CUMULATIVE CAPTURE: {len(action_traces) if action_traces else 0} actions from levels 1-{level_number}")
            else:
                # LEVEL-SPECIFIC CAPTURE: Get only actions for this specific level
                # Used for individual level discoveries
                action_traces = self.db.execute_query("""
                    SELECT action_number, coordinates, frame_before, frame_after, level_number
                    FROM action_traces
                    WHERE game_id = ? AND session_id = ? AND level_number = ?
                    ORDER BY timestamp ASC
                """, (game_id, session_id, level_number))
                logger.info(f"[PKG] LEVEL-SPECIFIC CAPTURE: {len(action_traces) if action_traces else 0} actions for level {level_number}")
            
            if not action_traces or len(action_traces) == 0:
                return None
            
            # Extract sequence
            actions = [t['action_number'] for t in action_traces]
            coordinates = []
            for t in action_traces:
                if t['action_number'] == 6 and t.get('coordinates'):
                    try:
                        coord = json.loads(t['coordinates'])
                        coordinates.append(coord)
                    except:
                        pass
            
            efficiency = final_score / len(actions) if len(actions) > 0 else 0.0
            
            # NO ACTION CEILING: Even very long sequences can contain valuable subroutines
            # that agents can pattern-match and extract for optimization
            # Validation will determine if sequences are useful
            
            # Get frames
            initial_frame = json.loads(action_traces[0]['frame_before']) if action_traces[0].get('frame_before') else []
            final_frame = json.loads(action_traces[-1]['frame_after']) if action_traces[-1].get('frame_after') else []
            
            # Detect pattern tags and abstract pattern signature
            pattern_tags = self._detect_pattern_tags(actions, coordinates)
            game_type = self._classify_game_type(actions)
            pattern_signature = self._detect_frame_pattern(initial_frame, final_frame)
            
            # Check if we already have a winning sequence for this game/level
            # ANTI-GAMING: Check BEST sequence globally (not just by this agent)
            # ================================================================
            # BUG FIX (2024-01): Only compare against ACTIVE sequences!
            # ================================================================
            # Previously, this query included ALL sequences (active + inactive).
            # This caused a silent capture failure:
            # 1. Game has 11 sequences, all INACTIVE (deactivated as trash)
            # 2. Diversity check says "0 active, diversity bonus applies!"
            # 3. But existing check found an inactive sequence with efficiency 1.0
            # 4. New sequence couldn't beat efficiency 1.0, so REJECTED
            # 5. Result: Game-level with 0 active sequences, but new ones blocked!
            #
            # FIX: Only compare against ACTIVE sequences. If all sequences are
            # inactive, treat it like a new game-level and store the new sequence.
            # ================================================================
            existing = self.db.execute_query("""
                SELECT sequence_id, total_actions, efficiency_score, agent_id
                FROM winning_sequences
                WHERE game_id = ? AND level_number = ? AND is_active = 1
                ORDER BY efficiency_score DESC
                LIMIT 1
            """, (game_id, level_number))
            
            # ================================================================
            # DUPLICATE PREVENTION FIX (2024-12-03, UPDATED 2024-12-04)
            # ================================================================
            # Check if this EXACT action sequence already exists (same actions AND same count)
            # This prevents saving identical sequences that differ only in metadata
            # But allows different-length sequences that happen to share a prefix
            # ================================================================
            action_sequence_json = json.dumps(actions)
            duplicate_check = self.db.execute_query("""
                SELECT sequence_id, total_actions FROM winning_sequences
                WHERE game_id = ? AND level_number = ? AND action_sequence = ? AND total_actions = ?
                LIMIT 1
            """, (game_id, level_number, action_sequence_json, len(actions)))
            
            if duplicate_check:
                logger.debug(f"Duplicate sequence exists ({duplicate_check[0]['sequence_id'][:12]}, {duplicate_check[0]['total_actions']} actions), skipping save")
                return duplicate_check[0]['sequence_id']  # Return existing ID
            
            # Only store if this is MORE EFFICIENT than existing, or if no existing sequence
            should_store = False
            sequence_id = None
            
            # Get current agent_id from config
            current_agent_id = self.game_config.get('agent_id', 'unknown')
            
            if not existing:
                # First win for this level - always store
                should_store = True
                sequence_id = f"seq_{uuid.uuid4().hex[:16]}"
                logger.info(f"[NEW] First winning sequence for {game_id} level {level_number}")
            else:
                existing_seq = existing[0]
                existing_actions = existing_seq['total_actions']
                existing_efficiency = existing_seq['efficiency_score']
                existing_agent = existing_seq.get('agent_id', 'unknown')
                
                # ANTI-GAMING: Require improvement to store another sequence
                # Thresholds to prevent spam while allowing diversity (UPDATED 2024-12-04)
                # - If same agent: Must improve by 5+ actions OR 10% efficiency
                # - If different agent: Must improve by 3+ actions OR 5% efficiency
                # - DIVERSITY BONUS: If <= 3 active sequences, allow storage to ensure coverage
                
                is_same_agent = (current_agent_id == existing_agent)
                min_action_improvement = 5 if is_same_agent else 3
                min_efficiency_multiplier = 1.10 if is_same_agent else 1.05
                
                # Check sequence count for diversity bonus (per game type, not game_id)
                game_type_prefix = game_id.split('-')[0] if '-' in game_id else game_id[:4]
                seq_count = self.db.execute_query("""
                    SELECT COUNT(*) as cnt FROM winning_sequences
                    WHERE game_id LIKE ? AND level_number = ? AND is_active = 1
                """, (f"{game_type_prefix}%", level_number))[0]['cnt']
                
                # DIVERSITY BONUS: Allow if <= 10 active sequences for this game TYPE
                if seq_count <= 10:
                    should_store = True
                    sequence_id = f"seq_{uuid.uuid4().hex[:16]}"
                    logger.info(f"[DIVERSITY] Storing sequence for under-represented game-level (only {seq_count} active)")
                # Store if we improved (fewer actions OR better efficiency)
                elif len(actions) <= existing_actions - min_action_improvement:
                    should_store = True
                    sequence_id = f"seq_{uuid.uuid4().hex[:16]}"
                    logger.info(f" Optimized sequence: {existing_actions} → {len(actions)} actions "
                              f"(efficiency: {existing_efficiency:.4f} → {efficiency:.4f})")
                elif efficiency > existing_efficiency * min_efficiency_multiplier:
                    should_store = True
                    sequence_id = f"seq_{uuid.uuid4().hex[:16]}"
                    logger.info(f" Improved efficiency: {existing_efficiency:.4f} → {efficiency:.4f}")
                else:
                    logger.info(f"Existing sequence is still optimal ({existing_actions} actions, "
                              f"efficiency {existing_efficiency:.4f}) - "
                              f"Need {min_action_improvement}+ action improvement or {min_efficiency_multiplier}x efficiency")
            
            # Store in database (Rule 2) only if improved or first win
            if should_store and sequence_id:
                # Calculate frame transitions for pattern matching
                frame_transitions = self._extract_frame_transitions(action_traces)
                
                # Get actual agent_id and generation (not hardcoded 'core_agent')
                agent_id = self.game_config.get('agent_id', 'unknown')
                
                # Get agent's generation from database
                generation = 0
                if agent_id != 'unknown':
                    agent_data = self.db.execute_query(
                        "SELECT generation FROM agents WHERE agent_id = ?", (agent_id,)
                    )
                    if agent_data:
                        generation = agent_data[0]['generation']
                
                # Get agent operating mode for tracking
                agent_mode = self._get_agent_operating_mode(agent_id)
                # Get scorecard_id from game_results for tracking
                scorecard_id = None
                try:
                    scorecard_data = self.db.execute_query("""
                        SELECT scorecard_id FROM game_results 
                        WHERE game_id = ? AND session_id = ?
                        LIMIT 1
                    """, (game_id, session_id))
                    if scorecard_data:
                        scorecard_id = scorecard_data[0]['scorecard_id']
                except Exception:
                    pass  # scorecard_id is optional
                
                self.db.execute_query("""
                    INSERT INTO winning_sequences (
                        sequence_id, game_id, level_number, agent_id, session_id, scorecard_id,
                        action_sequence, coordinate_sequence, total_actions, total_score,
                        efficiency_score, initial_frame, final_frame, frame_transitions,
                        pattern_tags, game_type, discovered_at, generation_discovered
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sequence_id, game_id, level_number, agent_id, session_id, scorecard_id,
                    json.dumps(actions), json.dumps(coordinates), len(actions),
                    final_score, efficiency, json.dumps(initial_frame),
                    json.dumps(final_frame), json.dumps(frame_transitions),
                    json.dumps(pattern_tags), game_type, datetime.now().isoformat(),
                    generation
                ))
                
                # CRITICAL: Force immediate commit to ensure sequence is saved
                self.db.checkpoint_wal()
                logger.info(f" Sequence {sequence_id} committed to database immediately")
                
                # Try to detect and store abstract pattern (only if we have valid sequence_id)
                self._detect_and_store_abstract_pattern(
                    sequence_id, game_id, level_number, pattern_signature, 
                    pattern_tags, efficiency
                )
                
                # Phase 1: Record discovery for prestige tracking
                if agent_id != 'unknown':
                    try:
                        innovation_value = 0.5 if not existing else 0.8  # Higher for improvements
                        enrichment_score = efficiency * 2.0  # Efficiency-based enrichment
                        
                        self.prestige_engine.record_discovery(
                            agent_id=agent_id,
                            discovery_type='winning_sequence',
                            sequence_id=sequence_id,
                            innovation_value=innovation_value,
                            network_enrichment_score=enrichment_score
                        )
                        logger.debug(f"Recorded prestige discovery for agent {agent_id[:8]}")
                    except Exception as e:
                        logger.warning(f"Failed to record prestige discovery: {e}")
                
                logger.info(f" Captured winning sequence {sequence_id}: "
                           f"{len(actions)} actions, efficiency {efficiency:.4f}, "
                           f"tags: {pattern_tags}, pattern: {pattern_signature.get('transformation_type', 'unknown')}")
                
                # AUTO-CLEANUP: If we now have 4+ sequences for this game-level, deactivate worst one
                # PRIORITY ORDER (UPDATED 2024-12-04):
                # 1. success_rate_when_reused (proven working > unproven)
                # 2. times_referenced (heavily used > unused)
                # 3. total_actions ASC (fewer actions = more efficient)
                # 4. total_score DESC (higher score = further progress)
                current_sequences = self.db.execute_query("""
                    SELECT sequence_id, total_actions, total_score, efficiency_score,
                           COALESCE(success_rate_when_reused, 0) as success_rate,
                           COALESCE(times_referenced, 0) as refs
                    FROM winning_sequences
                    WHERE game_id = ? AND level_number = ? AND is_active = 1
                    ORDER BY 
                        COALESCE(success_rate_when_reused, 0) DESC,
                        COALESCE(times_referenced, 0) DESC,
                        total_actions ASC,
                        total_score DESC
                """, (game_id, level_number))
                
                if len(current_sequences) > 3:
                    # Deactivate the worst sequence (last in sorted list = lowest priority)
                    worst_seq = current_sequences[-1]
                    self.db.execute_query("""
                        UPDATE winning_sequences
                        SET is_active = 0, flag_reason = 'auto_cleanup_low_priority'
                        WHERE sequence_id = ?
                    """, (worst_seq['sequence_id'],))
                    logger.info(f"[CLEANUP] Auto-deactivated low-priority sequence {worst_seq['sequence_id'][:8]} "
                              f"({worst_seq['total_actions']} actions, success={worst_seq['success_rate']:.2f}, refs={worst_seq['refs']}, keeping top 3)")
            
            return sequence_id
            
        except Exception as e:
            logger.error(f"Error capturing winning sequence: {e}")
            return None
    
    def _explore_sequence_recombination(self, agent_id: str, game_id: str, 
                                       level_index: int) -> List[str]:
        """
        Explore sequence recombination after EVERY game (AUTOMATIC - Phase 2.5).
        
        This is the viral evolution accelerator - attempts to combine known sequences
        into new hypothetical sequences for the network to test.
        
        CRITICAL: This is OPPORTUNISTIC and runs automatically, not optional.
        The roadmap explicitly states this should happen after every game.
        
        Args:
            agent_id: Agent that just finished playing
            game_id: Game context
            level_index: Level reached (use this to target recombination)
        
        Returns:
            List of newly created sequence_ids
        """
        try:
            from knowledge_recombination_engine import KnowledgeRecombinationEngine
            
            # Get current generation for tracking
            agent_data = self.db.execute_query(
                "SELECT generation FROM agents WHERE agent_id = ?", (agent_id,)
            )
            generation = agent_data[0]['generation'] if agent_data else 0
            
            # Create recombination engine
            engine = KnowledgeRecombinationEngine(self.db)
            
            # Attempt recombination for all levels up to current level
            all_new_sequences = []
            
            for level in range(1, level_index + 1):
                new_sequences = engine.discover_sequence_combinations(
                    agent_id=agent_id,
                    game_id=game_id,
                    level_index=level - 1,  # 0-based for database
                    generation=generation,
                    max_attempts=5  # Limit to prevent exponential blowup
                )
                all_new_sequences.extend(new_sequences)
            
            return all_new_sequences
            
        except ImportError:
            # Knowledge recombination engine not available
            logger.warning("KnowledgeRecombinationEngine not found, skipping recombination")
            return []
        except Exception as e:
            logger.error(f"Error during sequence recombination: {e}")
            return []

    def _detect_pattern_tags(self, actions: List[int], coordinates: List) -> List[str]:
        """Detect pattern tags in action sequence."""
        tags = []
        if not actions:
            return tags
            
        action_counts = Counter(actions)
        
        # Action composition patterns
        if action_counts.get(6, 0) / len(actions) > 0.8:
            tags.append('action6_heavy')
        if len(set(actions)) <= 2:
            tags.append('action_repetition')
            
        # Coordinate patterns
        if coordinates and len(coordinates) > 1:
            # coordinates are lists [x, y], not dicts
            try:
                x_coords = [c[0] if isinstance(c, list) and len(c) > 0 else 0 for c in coordinates]
                y_coords = [c[1] if isinstance(c, list) and len(c) > 1 else 0 for c in coordinates]
                if x_coords and y_coords and max(x_coords) - min(x_coords) < 10 and max(y_coords) - min(y_coords) < 10:
                    tags.append('coordinate_clustering')
            except Exception as e:
                logger.debug(f"Error processing coordinates for pattern tags: {e}")
                
        return tags

    def _classify_game_type(self, actions: List[int]) -> str:
        """Classify game type based on actions."""
        if not actions:
            return 'unknown'
        action_counts = Counter(actions)
        if action_counts.get(6, 0) == len(actions):
            return 'action6_only'
        elif len(action_counts) >= 5:
            return 'diverse_actions'
        else:
            return 'mixed_actions'
    def _find_partial_sequence_match(self, game_id: str, current_frame, level_number: int = 1) -> Optional[Dict]:
        """
        Find sequences where current frame matches ANY point in the sequence.
        Returns the sequence and the starting index (checkpoint) to continue from.
        
        This enables "jumping in" to known winning sequences mid-game, significantly
        reducing actions needed by skipping the early exploration phase.
        
        Args:
            game_id: Current game ID
            current_frame: Current game frame state
            level_number: Current level number
            
        Returns:
            Dict with 'sequence', 'start_index', 'actions_skipped' or None
        """
        if not current_frame or len(current_frame) == 0:
            return None
            
        try:
            game_type = game_id.split('-')[0] if '-' in game_id else game_id
            
            # Get all ACTIVE sequences for this game type and level with frame transitions
            # (Don't try to match against inactive/deactivated sequences)
            sequences = self.db.execute_query("""
                SELECT ws.*, 
                       COALESCE(sr.reliability_score, 0.5) as reliability
                FROM winning_sequences ws
                LEFT JOIN sequence_reputation sr ON ws.sequence_id = sr.sequence_id
                WHERE ws.game_id LIKE ? AND ws.level_number = ? AND ws.is_active = 1
                  AND ws.frame_transitions IS NOT NULL
                ORDER BY reliability DESC, ws.efficiency_score DESC
                LIMIT 10
            """, (f"{game_type}-%", level_number))
            
            if not sequences:
                return None
            
            best_match = None
            latest_index = -1
            
            # Search each sequence for matching frames
            for seq in sequences:
                if seq['reliability'] < 0.3:
                    continue
                    
                # Parse frame transitions (list of frames at each step)
                try:
                    frame_transitions = json.loads(seq.get('frame_transitions', '[]'))
                    if not frame_transitions:
                        continue
                    
                    # Search for current frame in this sequence
                    # Start from the END to find latest occurrence (closest to victory)
                    for idx in range(len(frame_transitions) - 1, -1, -1):
                        if self._compare_frames(current_frame, frame_transitions[idx]):
                            # Found a match! Calculate how many actions we can skip
                            actions_skipped = idx
                            actions_remaining = len(frame_transitions) - idx
                            
                            # Prefer matches that:
                            # 1. Are later in the sequence (more actions skipped)
                            # 2. Have higher reliability
                            # 3. Are more efficient
                            match_score = actions_skipped + (seq['reliability'] * 10)
                            
                            if best_match is None or match_score > best_match['match_score']:
                                best_match = {
                                    'sequence': seq,
                                    'start_index': idx,
                                    'actions_skipped': actions_skipped,
                                    'actions_remaining': actions_remaining,
                                    'match_score': match_score,
                                    'reliability': seq['reliability']
                                }
                                logger.info(f" Found partial match in {seq['sequence_id']}: "
                                          f"Skip {actions_skipped} actions, {actions_remaining} remaining "
                                          f"(reliability: {seq['reliability']:.2f})")
                            break  # Found match in this sequence, check next sequence
                            
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    logger.debug(f"Error parsing frame transitions for {seq['sequence_id']}: {e}")
                    continue
            
            if best_match:
                logger.info(f" PARTIAL MATCH: {best_match['sequence']['sequence_id']} - "
                          f"Resuming from action {best_match['start_index']}, "
                          f"skipping {best_match['actions_skipped']} actions!")
                return best_match
                
        except Exception as e:
            logger.debug(f"Error in partial sequence matching: {e}")
            
        return None

    def _get_best_cumulative_sequence(self, game_id: str) -> Optional[Dict]:
        """
        Get the SINGLE BEST cumulative sequence for a game (highest score = most levels).
        This is what Generalists and Pioneers should replay to efficiently reach the frontier.
        
        Unlike _get_best_sequence_for_game() which gets a sequence for a SPECIFIC level,
        this returns the sequence that completes the MOST levels in total.
        
        Args:
            game_id: Game to check
            
        Returns:
            Best cumulative sequence (highest total_score) or None
        """
        if not self.game_config.get('enable_pattern_learning', True):
            return None
            
        try:
            # Extract game type prefix
            game_type = game_id.split('-')[0] if '-' in game_id else game_id
            logger.info(f"[SEQUENCE REPLAY DEBUG] _get_best_cumulative_sequence: game_id={game_id}, game_type={game_type}")
            
            # Get sequence with HIGHEST score (completes most levels)
            # Priority:
            # 1. PROVEN sequences (successful_validations > 0) with highest score
            # 2. UNTESTED sequences with highest score
            # 3. Among ties, prefer fewer actions (more efficient)
            sequences = self.db.execute_query("""
                SELECT ws.*, 
                       COALESCE(sr.reliability_score, 0.5) as reliability,
                       COALESCE(sr.success_rate, 0.5) as community_success_rate,
                       COALESCE(sr.agent_diversity, 0) as validators,
                       COALESCE(sr.successful_validations, 0) as validation_count,
                       COALESCE(sr.total_validation_attempts, 0) as total_attempts,
                       COALESCE(sr.trending, 'stable') as trend
                FROM winning_sequences ws
                LEFT JOIN sequence_reputation sr ON ws.sequence_id = sr.sequence_id
                WHERE ws.game_id LIKE ? 
                  AND ws.is_active = 1
                ORDER BY 
                    ws.total_score DESC,  -- Highest score first (most levels)
                    CASE 
                        WHEN COALESCE(sr.successful_validations, 0) > 0 THEN 0  -- Proven
                        WHEN COALESCE(sr.total_validation_attempts, 0) = 0 THEN 1  -- Untested
                        ELSE 2  -- Failed validations
                    END,
                    ws.total_actions ASC  -- Fewer actions = more efficient
                LIMIT 1
            """, (f"{game_type}-%",))
            
            logger.info(f"[SEQUENCE REPLAY DEBUG] Query returned {len(sequences) if sequences else 0} sequences")
            
            if sequences:
                seq = sequences[0]
                reliability_indicator = "" if seq['reliability'] >= 0.5 else "?"
                logger.info(f" {reliability_indicator} Best cumulative sequence for {game_type}: "
                           f"Score {seq['total_score']:.1f} (Level {int(seq['total_score'])}), "
                           f"{seq['total_actions']} actions, reliability {seq['reliability']:.2f}")
                logger.info(f"[SEQUENCE REPLAY DEBUG] Returning sequence {seq.get('sequence_id', 'UNKNOWN')}")
                return seq
            
            logger.warning(f"[SEQUENCE REPLAY DEBUG] No cumulative sequence found for game type {game_type}")
                
        except Exception as e:
            logger.debug(f"Error retrieving cumulative sequence for {game_type}: {e}")
            
        return None

    def _get_ranked_cumulative_sequences(self, game_id: str, limit: int = 3) -> List[Dict]:
        """
        Get TOP N cumulative sequences for a game, ranked by priority.
        Used for 3-try fallback system: try best sequence, if fails try 2nd, then 3rd.
        
        Priority order:
        1. PROVEN sequences (successful_validations > 0) with highest score
        2. UNTESTED sequences with highest score  
        3. Among ties, prefer fewer actions (more efficient)
        
        Args:
            game_id: Game to check
            limit: Max sequences to return (default 3)
            
        Returns:
            List of sequence dicts, ranked by priority (may be empty)
        """
        if not self.game_config.get('enable_pattern_learning', True):
            return []
            
        try:
            game_type = game_id.split('-')[0] if '-' in game_id else game_id
            
            sequences = self.db.execute_query("""
                SELECT ws.*, 
                       COALESCE(sr.reliability_score, 0.5) as reliability,
                       COALESCE(sr.success_rate, 0.5) as community_success_rate,
                       COALESCE(sr.successful_validations, 0) as validation_count,
                       COALESCE(sr.total_validation_attempts, 0) as total_attempts,
                       COALESCE(sr.trending, 'stable') as trend
                FROM winning_sequences ws
                LEFT JOIN sequence_reputation sr ON ws.sequence_id = sr.sequence_id
                WHERE ws.game_id LIKE ? 
                  AND ws.is_active = 1
                ORDER BY 
                    ws.total_score DESC,
                    CASE 
                        WHEN COALESCE(sr.successful_validations, 0) > 0 THEN 0
                        WHEN COALESCE(sr.total_validation_attempts, 0) = 0 THEN 1
                        ELSE 2
                    END,
                    ws.total_actions ASC
                LIMIT ?
            """, (f"{game_type}-%", limit))
            
            if sequences:
                logger.info(f"[RANKED SEQ] Found {len(sequences)} candidate sequences for {game_type}")
                for i, seq in enumerate(sequences):
                    logger.debug(f"  #{i+1}: {seq['sequence_id'][:12]} - score {seq['total_score']}, "
                               f"{seq['total_actions']} actions, reliability {seq['reliability']:.2f}")
            return sequences or []
            
        except Exception as e:
            logger.debug(f"Error retrieving ranked sequences for {game_id}: {e}")
            return []

    def _flag_sequence_failure(self, sequence_id: str, failure_reason: str) -> None:
        """
        Flag a sequence as failing during replay attempt.
        Increments consecutive_failures and may deactivate if threshold reached.
        
        Args:
            sequence_id: Sequence that failed
            failure_reason: Why it failed
        """
        try:
            # Get current failure count
            current = self.db.execute_query("""
                SELECT consecutive_failures, quick_flagged 
                FROM winning_sequences WHERE sequence_id = ?
            """, (sequence_id,))
            
            if current:
                failures = (current[0].get('consecutive_failures') or 0) + 1
                
                # Deactivate after 3 consecutive failures (more aggressive for 3-try system)
                if failures >= 3:
                    self.db.execute_query("""
                        UPDATE winning_sequences 
                        SET is_active = 0, quick_flagged = 1, 
                            consecutive_failures = ?, flag_reason = ?
                        WHERE sequence_id = ?
                    """, (failures, f"3try_deactivate: {failure_reason}", sequence_id))
                    logger.warning(f"[DEACTIVATE] {sequence_id[:12]} after {failures} consecutive failures: {failure_reason}")
                else:
                    # Just increment failure count
                    self.db.execute_query("""
                        UPDATE winning_sequences 
                        SET consecutive_failures = ?, flag_reason = ?
                        WHERE sequence_id = ?
                    """, (failures, failure_reason, sequence_id))
                    logger.info(f"[FLAG] {sequence_id[:12]} failure #{failures}: {failure_reason}")
                    
        except Exception as e:
            logger.debug(f"Error flagging sequence failure: {e}")

    def _get_best_sequence_for_game(self, game_id: str, level_number: int = 1, 
                                   current_frame=None) -> Optional[Dict]:
        """
        Get best known winning sequence for a specific game level (Rule 2: from database).
        Prioritizes sequences with high reliability scores (community validation).
        Uses reputation system to filter out sequences that fail often (Task 4).
        
        NOTE: For Generalists/Pioneers replaying to frontier, use _get_best_cumulative_sequence() instead.
        This method is for level-specific lookups (e.g., when at a specific level and need targeted sequence).
        
        Args:
            game_id: Game to check
            level_number: Specific level to get sequence for
            current_frame: Optional current frame for pattern matching
            
        Returns:
            Sequence dict or None
        """
        if not self.game_config.get('enable_pattern_learning', True):
            return None
            
        try:
            # Extract game type prefix (e.g., 'vc33' from 'vc33-6ae7bf49eea5')
            game_type = game_id.split('-')[0] if '-' in game_id else game_id
            
            # TASK #4: Exploiter 50/50 Split Logic
            # Check if current agent is an exploiter and their social rule adherence
            agent_id = self.game_config.get('agent_id')
            agent_mode = self._get_agent_operating_mode(agent_id) if agent_id else None
            is_sociopath_exploiter = False
            
            if agent_mode == 'exploiter' and agent_id:
                # Query agent's social_rule_adherence
                agent_data = self.db.execute_query("""
                    SELECT social_rule_adherence
                    FROM agents
                    WHERE agent_id = ?
                """, (agent_id,))
                
                if agent_data and agent_data[0]['social_rule_adherence'] is not None:
                    social_adherence = agent_data[0]['social_rule_adherence']
                    is_sociopath_exploiter = (social_adherence < 0.5)
                    logger.debug(f"Agent {agent_id} social_rule_adherence: {social_adherence:.2f} ({'sociopath' if is_sociopath_exploiter else 'social'})")
            
            # Build ORDER BY clause based on agent type
            if is_sociopath_exploiter:
                # Sociopath exploiters: IGNORE community validation, prioritize efficiency only
                order_by_clause = """
                    ORDER BY 
                        ws.total_actions ASC,  -- Most efficient (fewest actions)
                        ws.total_score DESC    -- Highest score as tiebreaker
                """
                logger.debug(f"🦹 Sociopath exploiter mode: ignoring community validation")
            else:
                # Social exploiters, generalists, pioneers: RESPECT community validation
                order_by_clause = """
                    ORDER BY 
                        CASE 
                            WHEN COALESCE(sr.successful_validations, 0) > 0 THEN 0  -- Proven
                            WHEN COALESCE(sr.total_validation_attempts, 0) = 0 THEN 1  -- Untested
                            ELSE 2  -- Failed validations
                        END,
                        ws.total_actions ASC,
                        ws.total_score DESC
                """
            
            # Query sequences with reputation scores (community memory)
            # FIXED: Match by game TYPE prefix, not exact session ID
            # This allows sequences from previous sessions to be reused
            # 
            # LEVEL MAPPING (SIMPLE):
            # level_number = score (when sequence was captured)
            # Level 1 = score 1.0 (first challenge completed)
            # Level 2 = score 2.0 (second challenge completed)
            # Level N = score N.0 (Nth challenge completed)
            # 
            # WHERE clause: total_score >= level_number means sequence achieved at least that level
            # ORDER BY: Highest score first (completes most levels), then fewest actions (most efficient)
            # ACTIVE ONLY: Only query active sequences (top 3 per game-level)
            # CRITICAL FIX: Smart ordering to avoid failed sequences
            # Priority tiers:
            # 1. PROVEN: successful_validations > 0 (these definitely work)
            # 2. UNTESTED: total_validation_attempts = 0 (never tried, might work)
            # 3. FAILED: failed_validations > 0 but successful_validations = 0 (tried and failed)
            # Within each tier, prefer shorter sequences (more efficient)
            sequences = self.db.execute_query("""
                SELECT ws.*, 
                       COALESCE(sr.reliability_score, 0.5) as reliability,
                       COALESCE(sr.success_rate, 0.5) as community_success_rate,
                       COALESCE(sr.agent_diversity, 0) as validators,
                       COALESCE(sr.successful_validations, 0) as validation_count,
                       COALESCE(sr.total_validation_attempts, 0) as total_attempts,
                       COALESCE(sr.trending, 'stable') as trend
                FROM winning_sequences ws
                LEFT JOIN sequence_reputation sr ON ws.sequence_id = sr.sequence_id
                WHERE ws.game_id LIKE ? 
                  AND ws.level_number = ?
                  AND ws.total_score >= ?
                  AND ws.is_active = 1
                ORDER BY 
                    CASE 
                        WHEN COALESCE(sr.successful_validations, 0) > 0 THEN 0  -- Proven
                        WHEN COALESCE(sr.total_validation_attempts, 0) = 0 THEN 1  -- Untested
                        ELSE 2  -- Failed validations
                    END,
                    ws.total_actions ASC,
                    ws.total_score DESC
                LIMIT 10
            """, (f"{game_type}-%", level_number, level_number))
            
            if sequences:
                # NO FILTERING: Even long sequences can contain valuable subroutines
                # Agents can pattern-match and extract optimal sub-sequences
                # Validation and real gameplay will determine usefulness
                seq = sequences[0]
                reliability_indicator = "" if seq['reliability'] >= 0.5 else "?"
                logger.info(f" {reliability_indicator} Found winning sequence for game type {game_type} level {level_number}: "
                           f"{seq['total_actions']} actions, efficiency {seq['efficiency_score']:.4f}, "
                           f"reliability {seq['reliability']:.2f} ({seq['validators']} validations)")
                return seq
            
            # MULTI-STAGE MATCHING PIPELINE: Cascade through 5 fallback strategies (Competitive #2, +40% gain)
            # Stages: Exact → Prefix → Suffix → Subsequence → Conceptual → Random
            logger.debug(f"No exact sequence, trying multi-stage pipeline for {game_type} level {level_number}...")
            try:
                # Get current action history for pattern matching
                current_actions = self.game_config.get('current_actions', [])
                
                # Get agent configuration for threshold tuning
                agent_config = {
                    'risk_tolerance': self.game_config.get('risk_tolerance', 0.5),
                    'abstraction_threshold': self.game_config.get('abstraction_threshold', 0.7)
                }
                
                # Run through cascading fallback stages
                sequence_actions, stage_used, metadata = self.matching_pipeline.get_sequence_with_fallback(
                    game_id=game_id,
                    level_number=level_number,
                    current_actions=current_actions,
                    agent_config=agent_config
                )
                
                if sequence_actions and stage_used != 'random':
                    logger.info(f"[TARGET] Multi-stage match [{stage_used.upper()}]: {len(sequence_actions)} actions, "
                               f"confidence {metadata.get('confidence', 0):.2f}")
                    # Convert to sequence dict format
                    return {
                        'sequence_id': f"multi_stage_{stage_used}_{game_id}",
                        'actions': ','.join(map(str, sequence_actions)),
                        'total_actions': len(sequence_actions),
                        'stage': stage_used,
                        'confidence': metadata.get('confidence', 0)
                    }
                else:
                    logger.debug(f"Multi-stage pipeline exhausted for {game_type} level {level_number}, using exploration")
            except Exception as e:
                logger.debug(f"Multi-stage matching failed: {e}")
            
            logger.debug(f"No sequence found for game type {game_type} level {level_number} (all stages exhausted)")
                
        except Exception as e:
            logger.debug(f"Error retrieving winning sequence for game type {game_type}: {e}")
            
        return None

    async def _replay_sequence_inline(self, game_state: GameState, sequence: Dict, 
                                      start_index: int = 0) -> Optional[Dict]:
        """
        Replay a sequence INLINE within the existing game session.
        Does NOT create a new game or finish the game.
        
        Args:
            game_state: Current game state (starting state)
            sequence: Winning sequence to replay
            start_index: Index to start replay from (for partial matches, default 0)
            
        Returns:
            Dict with 'game_state' (updated) and 'success' (bool), or None if error
        """
        try:
            sequence_id = sequence['sequence_id']
            level_number = sequence.get('level_number') or 1
            logger.info(f" Replaying sequence {sequence_id} inline (level {level_number})")
            
            # Track that this agent is using a sequence for this level
            agent_id = self.game_config.get('agent_id', 'unknown')
            session_id = self.session_manager.current_session_id
            game_id = self.game_config.get('game_id', 'unknown')
            
            if session_id and game_id:
                self.db.log_level_sequence_usage(
                    session_id=session_id,
                    game_id=game_id,
                    agent_id=agent_id,
                    level_number=level_number,
                    used_sequence=True,
                    sequence_id=sequence_id
                )
            
            # NEW: Partial sequence matching support
            if start_index > 0:
                logger.info(f" CHECKPOINT REPLAY: Starting from action {start_index} "
                          f"(skipping {start_index} actions)")
            else:
                # Multi-stage frame matching for games with moving elements
                # Stage 1: Try direct comparison
                # Stage 2: Try all frames (for multi-frame sequences)
                # Stage 3: Try subsequence matching (partial match)
                # Stage 4: Proceed anyway (validation will catch failures)
                expected_initial_frame = json.loads(sequence['initial_frame'])
                current_frame = game_state.frame
                
                frames_match = False
                match_method = None
                
                # Determine if this is a proven sequence (>50% validation success)
                validation_successes = sequence.get('validation_successes', 0)
                validation_attempts = sequence.get('validation_attempts', 0)
                strict_replay = False
                if validation_attempts > 0:
                    success_rate = validation_successes / validation_attempts
                    strict_replay = success_rate > 0.5
                
                # Skip frame comparison if no frame data was captured
                if not expected_initial_frame or len(expected_initial_frame) == 0:
                    logger.debug(f" No frame data available, allowing replay based on game type match")
                    frames_match = True
                    match_method = "no_frame_data"
                else:
                    # Stage 1: Direct comparison (handles both single and multi-grid formats)
                    frames_match = self._compare_frames(expected_initial_frame, current_frame)
                    if frames_match:
                        match_method = "direct_match"
                        logger.debug(f" Frame matched via direct comparison")
                    
                    # STRICT REPLAY MODE: For proven sequences, fail hard if frames don't match
                    elif strict_replay:
                        logger.error(f" STRICT REPLAY FAILED: Frame mismatch for proven sequence {sequence_id}")
                        logger.error(f"   This sequence has >50% validation success rate but frames don't match")
                        logger.error(f"   Game state may have changed or sequence is corrupted")
                        return {'game_state': game_state, 'success': False}
                    else:
                        # Stage 2: For multi-frame sequences, try comparing against ALL frames
                        # Structure: [[[grid1]], [[grid2]], ...] for moving elements
                        if isinstance(expected_initial_frame, list) and len(expected_initial_frame) > 1:
                            if isinstance(expected_initial_frame[0], list) and isinstance(expected_initial_frame[0][0], list):
                                # This is a multi-frame sequence, try each frame
                                for frame_idx, stored_frame in enumerate(expected_initial_frame):
                                    if self._compare_frames(stored_frame, current_frame):
                                        frames_match = True
                                        match_method = f"multi_frame_match_{frame_idx}"
                                        logger.info(f" Frame matched via multi-frame comparison (frame {frame_idx}/{len(expected_initial_frame)})")
                                        break
                        
                        # Stage 3: Try subsequence/partial matching (90% similarity)
                        if not frames_match:
                            similarity = self._calculate_frame_similarity(expected_initial_frame, current_frame)
                            if similarity >= 0.90:
                                frames_match = True
                                match_method = f"partial_match_{similarity:.2f}"
                                logger.info(f" Frame matched via partial similarity ({similarity:.1%})")
                        
                        # Stage 4: Proceed anyway - let validation track success/failure
                        if not frames_match:
                            frames_match = True  # Allow replay to proceed
                            match_method = "validation_fallback"
                            logger.warning(f" Frame mismatch for {sequence_id}, proceeding with replay (validation will track)")
                            logger.debug(f"   Expected: type={type(expected_initial_frame)}, len={len(expected_initial_frame)}")
                            logger.debug(f"   Current: type={type(current_frame)}, len={len(current_frame) if isinstance(current_frame, list) else 'N/A'}")
            
            # Track that we're referencing this sequence
            logger.info(f"[SEQUENCE REPLAY DEBUG] Incrementing times_referenced for sequence {sequence_id}")
            self.db.execute_query("""
                UPDATE winning_sequences 
                SET times_referenced = times_referenced + 1,
                    last_referenced = ?
                WHERE sequence_id = ?
            """, (datetime.now().isoformat(), sequence_id))
            logger.info(f"[SEQUENCE REPLAY DEBUG] Successfully incremented times_referenced for sequence {sequence_id}")
            
            # Parse sequence
            actions = json.loads(sequence['action_sequence'])
            coordinates = json.loads(sequence.get('coordinate_sequence', '[]'))
            
            action_count = 0
            coord_index = start_index  # Start from checkpoint for coordinates
            
            # Execute actions starting from checkpoint
            for idx, action_num in enumerate(actions[start_index:], start=start_index):
                if game_state.state != "NOT_FINISHED":
                    break
                
                # ================================================================
                # BUG FIX: Use ACTUAL level (from score) not sequence's level_number
                # ================================================================
                # Previously, actions during replay were logged with the sequence's
                # level_number (e.g., L2 or L3), even when score was 0 (L1).
                # This caused capture to fail because:
                # 1. Agent wins L1 (score 0→1)
                # 2. Capture queries WHERE level_number = 1
                # 3. But all replay actions were logged as L2 → no matches!
                # 
                # FIX: Use score-based level_number: int(score) + 1
                # Score 0 = on level 1, Score 1 = on level 2, etc.
                # ================================================================
                actual_level = int(game_state.score) + 1
                
                # Execute action
                if action_num == 6 and coord_index < len(coordinates):
                    coord = coordinates[coord_index]
                    # Handle both dict and list formats
                    if isinstance(coord, dict):
                        x, y = coord.get('x', 0), coord.get('y', 0)
                    elif isinstance(coord, (list, tuple)) and len(coord) >= 2:
                        x, y = coord[0], coord[1]
                    else:
                        logger.warning(f"Invalid coordinate format: {coord}, skipping")
                        coord_index += 1
                        continue
                    
                    # Add reasoning for sequence replay with role-based context
                    agent_mode = self.game_config.get('agent_operating_mode', 'unknown')
                    target_level = self.game_config.get('optimizer_target_level', 'N/A')
                    
                    replay_reasoning = {
                        'action': 'ACTION6',
                        'reasoning': f'{agent_mode.upper()} replaying proven sequence {sequence_id[:8]} (target: L{target_level})',
                        'agent_role': agent_mode,
                        'optimizer_target_level': target_level if agent_mode == 'optimizer' else None,
                        'sequence_id': sequence_id,
                        'replay_step': action_count + 1,
                        'total_steps': len(actions),
                        'coordinate': {'x': x, 'y': y},
                        'checkpoint_validation': True,
                        'role_compliance': f'{agent_mode} following sequence script'
                    }
                    game_state = await self.action_handler.send_action_6(x, y, game_state.frame, reasoning=replay_reasoning, level_number=actual_level)
                    coord_index += 1
                else:
                    action = f"ACTION{action_num}"
                    # Use actual_level (score-based) not sequence's level_number
                    game_state = await self._execute_action(action, game_state, "", actual_level)
                
                # Track action for abstraction engine WITH MEMORY LEAK PROTECTION
                if 'current_actions' in self.game_config:
                    current_actions = self.game_config['current_actions']
                    max_history = self.game_config.get('max_action_history', 1000)
                    
                    # Truncate if exceeds limit (Other AI suggestion #4)
                    if len(current_actions) >= max_history:
                        current_actions = current_actions[-max_history//2:]  # Keep last 50%
                        logger.debug(f"Action history truncated to {len(current_actions)} (max: {max_history})")
                    
                    current_actions.append(action_num)
                    self.game_config['current_actions'] = current_actions
                
                action_count += 1
                
                # Memory leak protection: Check for momentum breakthrough (Competitive #4)
                if hasattr(self, 'breakthrough_detector') and len(self.game_config.get('current_actions', [])) >= 50:
                    # Build action history in the format expected by detect_micro_progress
                    action_history = [{'action': a, 'frame': None} for a in self.game_config['current_actions'][-50:]]
                    momentum = self.breakthrough_detector.detect_micro_progress(
                        game_state=game_state,
                        action_history=action_history
                    )
                    if momentum and momentum > 0.6:  # momentum is a float, not dict
                        logger.info(f"[LAUNCH] BREAKTHROUGH MOMENTUM detected during replay: {momentum:.2f}")
                
                logger.debug(f"Replay action {action_count}/{len(actions)}: ACTION{action_num}, "
                           f"Score: {game_state.score}, State: {game_state.state}")
            
            # Check if replay was successful
            # SUCCESS CRITERIA (per Master Ruleset):
            # - For a level N sequence: agent must reach level N (score >= N-1)
            # - score = number of levels COMPLETED, so:
            #   - Score 0 = on level 1 (no levels completed)
            #   - Score 1 = completed level 1, now on level 2
            #   - Score 2 = completed levels 1+2, now on level 3
            # - A sequence for level N is valid if agent reaches level N
            #   which means score >= (N-1) since score N-1 means level N-1 completed = ON level N
            # NOTE: target_level comes from DB's level_number column (the level this sequence completes)
            # Using 'or 1' handles both missing key AND None value (belt + suspenders)
            target_level = sequence.get('level_number') or 1
            current_level = int(game_state.score) + 1  # Score 0 = level 1, Score 1 = level 2, etc.
            
            # Success = reached target level OR better (including WIN)
            replay_success = (game_state.state == "WIN" or 
                            current_level >= target_level)
            
            logger.debug(f"Sequence validation: target_level={target_level}, current_level={current_level}, "
                        f"score={game_state.score}, success={replay_success}")
            
            # Record validation attempt for community memory (Task 4)
            failure_reason = None
            if not replay_success:
                # Note: frames_match is always True now (we proceed regardless)
                # Use match_method to determine if frame matching was questionable
                if match_method == "validation_fallback":
                    failure_reason = 'frame_mismatch_proceeded'
                elif action_count < len(actions):
                    failure_reason = 'incomplete_sequence'
                elif current_level < target_level:
                    failure_reason = f'reached_level_{current_level}_not_{target_level}'
                else:
                    failure_reason = 'insufficient_score'
            
            # Get agent information from config or session
            agent_id = self.game_config.get('agent_id', 'unknown')
            session_id = self.session_manager.current_session_id if self.session_manager and self.session_manager.current_session_id else 'unknown'
            
            # Get agent epigenetics if available from config
            agent_epigenetics = self.game_config.get('agent_epigenetics')
            
            self._record_sequence_validation(
                sequence_id=sequence_id,
                agent_id=agent_id,
                game_id=sequence['game_id'],
                session_id=session_id,
                success=replay_success,
                actions_completed=action_count,
                total_actions=len(actions),
                score_achieved=game_state.score,
                original_efficiency=sequence['efficiency_score'],
                agent_epigenetics=agent_epigenetics,
                failure_reason=failure_reason
            )
            
            if replay_success:
                logger.info(f"[OK] Inline replay successful for {sequence_id}! Reached level {current_level} (target: {target_level}), Score: {game_state.score}")
            else:
                logger.warning(f"[FAIL] Inline replay failed for {sequence_id}. "
                             f"Reached level {current_level} (target: {target_level}), Score: {game_state.score}")
            
            return {'game_state': game_state, 'success': replay_success}
            
        except ValueError as e:
            # Frame corruption or other critical errors - re-raise to abort game
            if "frame corruption" in str(e).lower():
                logger.error(f"Frame corruption during replay - aborting game: {e}")
                raise  # Re-raise to propagate to game loop
            logger.error(f"ValueError in inline replay: {e}")
            return None
        except Exception as e:
            logger.error(f"Error in inline replay: {e}")
            return None

    async def _try_replay_sequence(self, game_id: str, sequence: Dict) -> Optional[Dict[str, Any]]:
        """
        Try to replay a known winning sequence (Rule 7: Real actions).
        Verifies initial frame matches and tracks replay attempts.
        
        Args:
            game_id: Game to play
            sequence: Winning sequence to replay
            
        Returns:
            Game results or None if failed
        """
        try:
            sequence_id = sequence['sequence_id']
            level_number = sequence.get('level_number') or 1
            logger.info(f" Attempting to replay sequence {sequence_id} for {game_id} level {level_number}")
            
            if not self.session_manager.is_running:
                await self.session_manager.start_session(game_id=game_id)
            
            game_data = await self.session_manager.create_game(game_id)
            game_state = GameState.from_dict(game_data)
            
            # Verify initial frame matches (critical for replay success)
            expected_initial_frame = json.loads(sequence['initial_frame'])
            current_frame = game_state.frame
            
            # Simple frame comparison (can be enhanced with fuzzy matching)
            frames_match = self._compare_frames(expected_initial_frame, current_frame)
            if not frames_match:
                logger.warning(f" Initial frame mismatch - replay may fail for {sequence_id}")
                # Continue anyway but track this
            
            actions = json.loads(sequence['action_sequence'])
            coordinates = json.loads(sequence.get('coordinate_sequence', '[]'))
            
            start_time = datetime.now()
            action_count = 0
            coord_index = 0
            replay_success = False
            
            # Track that we're referencing this sequence
            self.db.execute_query("""
                UPDATE winning_sequences 
                SET times_referenced = times_referenced + 1,
                    last_referenced = ?
                WHERE sequence_id = ?
            """, (datetime.now().isoformat(), sequence_id))
            
            for action_num in actions:
                if game_state.state != "NOT_FINISHED":
                    break
                
                # Execute action and track it (Rule 2: Database tracking)
                if action_num == 6 and coord_index < len(coordinates):
                    coord = coordinates[coord_index]
                    # Handle both dict and list formats
                    if isinstance(coord, dict):
                        x, y = coord.get('x', 0), coord.get('y', 0)
                    elif isinstance(coord, (list, tuple)) and len(coord) >= 2:
                        x, y = coord[0], coord[1]
                    else:
                        logger.warning(f"Invalid coordinate format: {coord}, skipping")
                        coord_index += 1
                        continue
                    
                    # Add reasoning for sequence replay
                    replay_reasoning = {
                        'action': 'ACTION6',
                        'reasoning': f'Replaying known winning sequence {sequence_id[:8]}',
                        'sequence_id': sequence_id,
                        'replay_step': action_count + 1,
                        'total_steps': len(actions),
                        'coordinate': {'x': x, 'y': y}
                    }
                    game_state = await self.action_handler.send_action_6(x, y, game_state.frame, reasoning=replay_reasoning, level_number=level_number)
                    coord_index += 1
                else:
                    action = f"ACTION{action_num}"
                    # BUGFIX: Pass level_number to ensure action traces are logged with correct level
                    game_state = await self._execute_action(action, game_state, "", level_number)
                
                action_count += 1
                
                # Log to system_logs for debugging
                logger.debug(f"Replay action {action_count}/{len(actions)}: ACTION{action_num}, "
                           f"Score: {game_state.score}, State: {game_state.state}")
            
            level_completions = int(game_state.score)  # Each level = 1 point
            await self.session_manager.finish_game(game_state.state, game_state.score, level_completions, action_count)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Check if replay was successful using level-based validation
            # (Same logic as _try_inline_replay_sequence)
            target_level = sequence.get('level_number') or 1
            current_level = int(game_state.score) + 1  # Score 0 = level 1, etc.
            
            replay_success = (game_state.state == "WIN" or 
                            current_level >= target_level)
            
            logger.debug(f"Replay validation: target_level={target_level}, current_level={current_level}, "
                        f"score={game_state.score}, success={replay_success}")
            
            # Update success rate in database
            if replay_success:
                logger.info(f"[OK] Replay successful for {sequence_id}! Reached level {current_level} (target: {target_level}), Score: {game_state.score}")
                # Note: success_rate_when_reused calculation would need existing value
                # For now, just increment a success counter (schema may need update)
            else:
                logger.warning(f"[FAIL] Replay failed for {sequence_id}. "
                             f"Reached level {current_level} (target: {target_level}), Score: {game_state.score}")
            
            result = {
                'game_id': game_id,
                'final_state': game_state.state,
                'final_score': game_state.score,
                'actions_taken': action_count,
                'duration_seconds': duration,
                'win': game_state.state == "WIN",
                'method': 'replay_sequence',
                'sequence_id': sequence_id,
                'replay_success': replay_success,
                'frame_match': frames_match
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error replaying sequence: {e}", exc_info=True)
            return None
    
    def _record_sequence_validation(self, sequence_id: str, agent_id: str, 
                                   game_id: str, session_id: str,
                                   success: bool, actions_completed: int,
                                   total_actions: int, score_achieved: float,
                                   original_efficiency: float,
                                   agent_epigenetics: Optional[Dict] = None,
                                   failure_reason: Optional[str] = None):
        """
        Record sequence validation attempt for community memory (Task 4).
        Tracks which agents tried which sequences and whether they worked.
        
        Args:
            sequence_id: Sequence that was attempted
            agent_id: Agent that attempted it
            game_id: Game where it was attempted
            session_id: Session ID
            success: Did the sequence work completely?
            actions_completed: How many actions from sequence worked
            total_actions: Total actions in sequence
            score_achieved: Score achieved by this agent
            original_efficiency: Original sequence's efficiency score
            agent_epigenetics: Agent's epigenetic state (for analysis)
            failure_reason: If failed, why?
        """
        try:
            import uuid
            validation_id = f"val_{uuid.uuid4().hex[:12]}"
            
            partial_success = (actions_completed > 0 and 
                             actions_completed < total_actions and 
                             not success)
            
            # Calculate efficiency vs original
            if score_achieved > 0 and actions_completed > 0:
                agent_efficiency = score_achieved / actions_completed
                efficiency_ratio = agent_efficiency / original_efficiency if original_efficiency > 0 else 0.0
            else:
                efficiency_ratio = 0.0
            
            # Store validation attempt
            self.db.execute_query("""
                INSERT INTO sequence_validation_attempts
                (validation_id, sequence_id, agent_id, game_id, session_id,
                 validation_success, partial_success, actions_completed, 
                 total_actions_in_sequence, score_achieved, efficiency_vs_original,
                 agent_epigenetics, failure_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (validation_id, sequence_id, agent_id, game_id, session_id,
                  success, partial_success, actions_completed, total_actions,
                  score_achieved, efficiency_ratio,
                  json.dumps(agent_epigenetics) if agent_epigenetics else None,
                  failure_reason))
            
            # Update sequence reputation
            self._update_sequence_reputation(sequence_id)
            
            # QUICK VALIDATION: Flag bad sequences immediately (don't wait for pruning)
            # This prevents wasting resources on obviously broken sequences
            # Implemented inline per Rule 10 (integrate into existing files)
            try:
                # Detect frame mismatch (first action failed = likely frame corruption)
                frame_mismatch = (actions_completed == 0 and not success and 
                                 failure_reason and 'frame' in failure_reason.lower())
                
                # Get current failure stats
                current_stats = self.db.execute_query("""
                    SELECT consecutive_failures, quick_flagged 
                    FROM winning_sequences 
                    WHERE sequence_id = ?
                """, (sequence_id,))
                
                if current_stats:
                    current_failures = current_stats[0].get('consecutive_failures', 0) or 0
                    already_flagged = current_stats[0].get('quick_flagged', 0) or 0
                    
                    if success:
                        # Reset consecutive failures on success
                        self.db.execute_query("""
                            UPDATE winning_sequences 
                            SET consecutive_failures = 0 
                            WHERE sequence_id = ?
                        """, (sequence_id,))
                    else:
                        # Increment consecutive failures
                        new_failures = current_failures + 1
                        
                        # Deactivate if frame mismatch (immediate) or 5+ consecutive failures
                        if frame_mismatch or new_failures >= 5:
                            flag_reason = 'frame_mismatch' if frame_mismatch else f'{new_failures}_consecutive_failures'
                            self.db.execute_query("""
                                UPDATE winning_sequences 
                                SET is_active = 0, 
                                    quick_flagged = 1,
                                    consecutive_failures = ?,
                                    flag_reason = ?
                                WHERE sequence_id = ?
                            """, (new_failures, flag_reason, sequence_id))
                            logger.warning(f"[QUICK DEACTIVATE] {sequence_id[:12]} - {flag_reason}")
                        elif new_failures >= 3 and not already_flagged:
                            # Flag for review at 3+ failures
                            self.db.execute_query("""
                                UPDATE winning_sequences 
                                SET quick_flagged = 1,
                                    consecutive_failures = ?,
                                    flag_reason = ?
                                WHERE sequence_id = ?
                            """, (new_failures, f'{new_failures}_failures_review', sequence_id))
                            logger.info(f"[WARN] QUICK FLAG: {sequence_id[:12]} - {new_failures} consecutive failures")
                        else:
                            # Just increment failures
                            self.db.execute_query("""
                                UPDATE winning_sequences 
                                SET consecutive_failures = ?
                                WHERE sequence_id = ?
                            """, (new_failures, sequence_id))
            except Exception as qv_error:
                logger.debug(f"Quick validation error (non-critical): {qv_error}")
            
            # Phase 1: Record validation attempt for prestige tracking
            if agent_id and agent_id != 'unknown':
                try:
                    self.prestige_engine.record_validation_attempt(
                        agent_id=agent_id,
                        sequence_id=sequence_id,
                        success=success,
                        efficiency_vs_original=efficiency_ratio
                    )
                    logger.debug(f"Recorded prestige validation for agent {agent_id[:8]}")
                except Exception as e:
                    logger.warning(f"Failed to record prestige validation: {e}")
            
            logger.info(f" Recorded validation: {sequence_id} by {agent_id} - "
                       f"{' Success' if success else ' Failed'} "
                       f"({actions_completed}/{total_actions} actions)")
            
        except Exception as e:
            logger.error(f"Error recording sequence validation: {e}")
    
    def _update_sequence_reputation(self, sequence_id: str):
        """
        Update reputation score for a sequence based on all validation attempts.
        Uses Bayesian approach with prior to handle small sample sizes.
        
        This implements the "downvoting" mechanism - sequences that fail often
        get lower reputation scores and are less likely to be selected.
        """
        try:
            # Get all validation attempts for this sequence
            attempts = self.db.execute_query("""
                SELECT 
                    COUNT(*) as total_attempts,
                    SUM(CASE WHEN validation_success = 1 THEN 1 ELSE 0 END) as successes,
                    SUM(CASE WHEN validation_success = 0 THEN 1 ELSE 0 END) as failures,
                    SUM(CASE WHEN partial_success = 1 THEN 1 ELSE 0 END) as partials,
                    COUNT(DISTINCT agent_id) as unique_agents
                FROM sequence_validation_attempts
                WHERE sequence_id = ?
            """, (sequence_id,))
            
            if not attempts or attempts[0]['total_attempts'] == 0:
                # No validation attempts yet, use default values
                self.db.execute_query("""
                    INSERT OR REPLACE INTO sequence_reputation
                    (sequence_id, total_validation_attempts, successful_validations,
                     failed_validations, partial_validations, success_rate,
                     reliability_score, agent_diversity, recent_success_rate, trending)
                    VALUES (?, 0, 0, 0, 0, 0.5, 0.5, 1, 0.5, 'stable')
                """, (sequence_id,))
                return
            
            stats = attempts[0]
            total = stats['total_attempts']
            successes = stats['successes'] or 0
            failures = stats['failures'] or 0
            partials = stats['partials'] or 0
            unique_agents = stats['unique_agents'] or 1
            
            # Calculate raw success rate
            raw_success_rate = successes / total if total > 0 else 0.5
            
            # Bayesian reliability score (adds prior of 2 successes, 2 failures)
            # This prevents new sequences from having extreme scores
            reliability_score = (successes + 2) / (total + 4)
            
            # Calculate recent success rate (last 10 attempts)
            recent_attempts = self.db.execute_query("""
                SELECT validation_success
                FROM sequence_validation_attempts
                WHERE sequence_id = ?
                ORDER BY attempted_at DESC
                LIMIT 10
            """, (sequence_id,))
            
            recent_successes = sum(1 for a in recent_attempts if a['validation_success'])
            recent_success_rate = recent_successes / len(recent_attempts) if recent_attempts else 0.5
            
            # Determine trend
            if len(recent_attempts) >= 5:
                if recent_success_rate > raw_success_rate + 0.1:
                    trending = 'improving'
                elif recent_success_rate < raw_success_rate - 0.1:
                    trending = 'declining'
                else:
                    trending = 'stable'
            else:
                trending = 'stable'
            
            # Update reputation
            self.db.execute_query("""
                INSERT OR REPLACE INTO sequence_reputation
                (sequence_id, total_validation_attempts, successful_validations,
                 failed_validations, partial_validations, success_rate,
                 reliability_score, agent_diversity, recent_success_rate, trending,
                 last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (sequence_id, total, successes, failures, partials,
                  raw_success_rate, reliability_score, unique_agents,
                  recent_success_rate, trending, datetime.now().isoformat()))
            
            # CRITICAL FIX: Also update winning_sequences.success_rate_when_reused
            # This is what the pruning system checks, so it must be kept in sync!
            self.db.execute_query("""
                UPDATE winning_sequences
                SET success_rate_when_reused = ?,
                    times_referenced = ?
                WHERE sequence_id = ?
            """, (raw_success_rate, total, sequence_id))
            
            logger.debug(f" Updated reputation for {sequence_id}: "
                        f"reliability={reliability_score:.2f}, "
                        f"success_rate={raw_success_rate:.2f}, "
                        f"trend={trending}")
            
        except Exception as e:
            logger.error(f"Error updating sequence reputation: {e}")
    
    def _calculate_frame_similarity(self, frame1, frame2) -> float:
        """
        Calculate similarity ratio between two frames (0.0 to 1.0).
        Used for fuzzy matching when exact frame match fails.
        """
        try:
            # Use same unwrapping logic as _compare_frames
            def unwrap_frame(frame):
                if not isinstance(frame, list) or len(frame) == 0:
                    return frame
                if isinstance(frame[0], list) and len(frame[0]) > 0:
                    if isinstance(frame[0][0], list):
                        if len(frame) > 1 and isinstance(frame[1], list) and isinstance(frame[1][0], list):
                            return unwrap_frame(frame[0])
                        else:
                            return unwrap_frame(frame[0])
                return frame
            
            frame1 = unwrap_frame(frame1)
            frame2 = unwrap_frame(frame2)
            
            if not isinstance(frame1, list) or not isinstance(frame2, list):
                return 0.0
            if len(frame1) != len(frame2):
                return 0.0
            
            # Calculate cell-by-cell similarity
            total_cells = 0
            matching_cells = 0
            
            for row1, row2 in zip(frame1, frame2):
                if not isinstance(row1, list) or not isinstance(row2, list):
                    continue
                for cell1, cell2 in zip(row1, row2):
                    total_cells += 1
                    if cell1 == cell2:
                        matching_cells += 1
            
            if total_cells == 0:
                return 0.0
            
            return matching_cells / total_cells
            
        except Exception as e:
            logger.debug(f"Frame similarity calculation error: {e}")
            return 0.0
    
    def _compare_frames(self, frame1, frame2) -> bool:
        """
        Compare two frames for similarity.
        Returns True if frames match closely enough for replay.
        
        Handles various frame formats from ARC API:
        - Single grid: [[row1], [row2], ...]
        - Multiple grids (moving elements): [[[grid1]], [[grid2]], ...]
        - Unwrapped format from GameState: [[row1], [row2], ...]
        """
        try:
            # Normalize both frames to unwrapped grid format
            def unwrap_frame(frame):
                """Recursively unwrap frame to get the actual grid data."""
                if not isinstance(frame, list) or len(frame) == 0:
                    return frame
                
                # If this is a list of multiple grids (moving elements), take the first one
                # Structure: [[[grid1]], [[grid2]], ...] -> [[grid1]] -> [grid1]
                if isinstance(frame[0], list) and len(frame[0]) > 0:
                    if isinstance(frame[0][0], list):
                        # Check if this is multiple grids or nested single grid
                        if len(frame) > 1 and isinstance(frame[1], list) and isinstance(frame[1][0], list):
                            # Multiple grids: [[[grid1]], [[grid2]], ...] - take first
                            return unwrap_frame(frame[0])
                        else:
                            # Single nested grid: [[[data]]] - unwrap
                            return unwrap_frame(frame[0])
                
                # This is already a grid: [[row1], [row2], ...]
                return frame
            
            frame1_orig_len = len(frame1) if isinstance(frame1, list) else 0
            frame2_orig_len = len(frame2) if isinstance(frame2, list) else 0
            
            frame1 = unwrap_frame(frame1)
            frame2 = unwrap_frame(frame2)
            
            # Log unwrapping results for debugging
            frame1_unwrapped_len = len(frame1) if isinstance(frame1, list) else 0
            frame2_unwrapped_len = len(frame2) if isinstance(frame2, list) else 0
            if frame1_orig_len != frame1_unwrapped_len or frame2_orig_len != frame2_unwrapped_len:
                logger.debug(f"   Frame unwrapping: {frame1_orig_len}->{frame1_unwrapped_len}, {frame2_orig_len}->{frame2_unwrapped_len}")
            
            # Simple equality check
            if frame1 == frame2:
                return True
            
            # If frames are different lengths, definitely don't match
            if not isinstance(frame1, list) or not isinstance(frame2, list):
                logger.debug(f"   Frame comparison failed: not both lists (f1={type(frame1)}, f2={type(frame2)})")
                return False
            if len(frame1) != len(frame2):
                logger.debug(f"   Frame comparison failed: length mismatch ({len(frame1)} vs {len(frame2)})")
                return False
            
            # Check if at least 95% of cells match
            total_cells = 0
            matching_cells = 0
            
            for row1, row2 in zip(frame1, frame2):
                if not isinstance(row1, list) or not isinstance(row2, list):
                    continue
                for cell1, cell2 in zip(row1, row2):
                    total_cells += 1
                    if cell1 == cell2:
                        matching_cells += 1
            
            if total_cells == 0:
                return False
            
            match_ratio = matching_cells / total_cells
            return match_ratio >= 0.90  # Lowered from 0.95 to allow more "slip into sequence" opportunities
            
        except Exception as e:
            logger.debug(f"Frame comparison error: {e}")
            return False
    
    def _detect_frame_pattern(self, initial_frame, final_frame) -> Dict[str, Any]:
        """
        Detect abstract patterns between initial and final frames.
        This helps identify pattern-based transformations rather than literal sequences.
        
        Returns:
            Dict with pattern characteristics for matching similar problems
        """
        pattern_info = {
            'grid_size': None,
            'color_distribution_change': {},
            'symmetry_detected': False,
            'repetition_detected': False,
            'transformation_type': 'unknown'
        }
        
        try:
            # Unwrap nested frames
            initial = initial_frame
            final = final_frame
            
            if isinstance(initial, list) and len(initial) > 0:
                if isinstance(initial[0], list) and len(initial[0]) > 0:
                    if isinstance(initial[0][0], list):
                        initial = initial[0][0]
            
            if isinstance(final, list) and len(final) > 0:
                if isinstance(final[0], list) and len(final[0]) > 0:
                    if isinstance(final[0][0], list):
                        final = final[0][0]
            
            if not initial or not final:
                return pattern_info
            
            # Grid size
            if isinstance(initial, list) and len(initial) > 0 and isinstance(initial[0], list):
                pattern_info['grid_size'] = (len(initial), len(initial[0]))
            
            # Color distribution changes
            from collections import Counter
            
            initial_colors = Counter()
            final_colors = Counter()
            
            for row in initial:
                if isinstance(row, list):
                    for cell in row:
                        if isinstance(cell, int):
                            initial_colors[cell] += 1
            
            for row in final:
                if isinstance(row, list):
                    for cell in row:
                        if isinstance(cell, int):
                            final_colors[cell] += 1
            
            # Detect transformation patterns
            if initial_colors == final_colors:
                pattern_info['transformation_type'] = 'rearrangement'
            elif len(final_colors) < len(initial_colors):
                pattern_info['transformation_type'] = 'color_reduction'
            elif len(final_colors) > len(initial_colors):
                pattern_info['transformation_type'] = 'color_expansion'
            else:
                pattern_info['transformation_type'] = 'color_transformation'
            
            # Store color changes
            for color in set(list(initial_colors.keys()) + list(final_colors.keys())):
                pattern_info['color_distribution_change'][color] = {
                    'before': initial_colors.get(color, 0),
                    'after': final_colors.get(color, 0),
                    'delta': final_colors.get(color, 0) - initial_colors.get(color, 0)
                }
            
            # Detect symmetry in final frame
            if isinstance(final, list) and len(final) > 1:
                # Check horizontal symmetry
                is_symmetric = True
                for i in range(len(final) // 2):
                    if final[i] != final[-(i+1)]:
                        is_symmetric = False
                        break
                pattern_info['symmetry_detected'] = is_symmetric
            
            # Detect repetition patterns
            if isinstance(final, list) and len(final) > 0:
                # Check if rows repeat
                row_counts = Counter([tuple(row) if isinstance(row, list) else row for row in final])
                if max(row_counts.values()) > 1:
                    pattern_info['repetition_detected'] = True
            
        except Exception as e:
            logger.debug(f"Pattern detection error: {e}")
        
        return pattern_info
    
    def _extract_frame_transitions(self, action_traces: List[Dict]) -> List[Dict]:
        """
        Extract frame states at each action for partial sequence matching.
        Returns list of frame states that can be used to find checkpoints.
        
        This is CRITICAL for partial sequence matching - allows agents to "jump in"
        to known sequences by matching current frame to any point in the sequence.
        """
        frame_states = []
        
        try:
            for i, trace in enumerate(action_traces):
                # Extract the actual frame state after this action
                frame_after = trace.get('frame_after')
                
                if frame_after:
                    try:
                        # Parse frame and store it
                        frame_data = json.loads(frame_after) if isinstance(frame_after, str) else frame_after
                        frame_states.append(frame_data)
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.debug(f"Failed to parse frame at action {i}: {e}")
                        # Store empty frame placeholder to maintain index alignment
                        frame_states.append([])
                else:
                    # No frame data available for this action
                    frame_states.append([])
        
        except Exception as e:
            logger.debug(f"Frame transition extraction error: {e}")
        
        return frame_states
    
    def _detect_and_store_abstract_pattern(self, sequence_id: str, game_id: str, 
                                          level_number: int, pattern_signature: Dict,
                                          pattern_tags: List[str], efficiency: float):
        """
        Detect and store abstract patterns that can be reused across similar problems.
        This enables pattern-based matching rather than just literal sequence replay.
        """
        try:
            # Create pattern signature hash for matching
            sig_str = json.dumps({
                'transformation_type': pattern_signature.get('transformation_type'),
                'grid_size': pattern_signature.get('grid_size'),
                'symmetry': pattern_signature.get('symmetry_detected'),
                'repetition': pattern_signature.get('repetition_detected'),
                'tags': sorted(pattern_tags)
            }, sort_keys=True)
            
            import hashlib
            pattern_hash = hashlib.md5(sig_str.encode()).hexdigest()[:16]
            pattern_id = f"pat_{pattern_hash}"
            
            # Check if this pattern already exists
            existing_pattern = self.db.execute_query("""
                SELECT pattern_id, occurrence_count, success_count, 
                       concrete_examples, avg_efficiency
                FROM discovered_patterns
                WHERE pattern_id = ?
            """, (pattern_id,))
            
            if existing_pattern:
                # Update existing pattern
                pat = existing_pattern[0]
                examples = json.loads(pat['concrete_examples'])
                
                if sequence_id not in examples:
                    examples.append(sequence_id)
                    new_count = pat['occurrence_count'] + 1
                    new_success = pat['success_count'] + 1
                    
                    # Update average efficiency
                    new_avg_eff = (pat['avg_efficiency'] * pat['occurrence_count'] + efficiency) / new_count
                    
                    self.db.execute_query("""
                        UPDATE discovered_patterns
                        SET occurrence_count = ?,
                            success_count = ?,
                            concrete_examples = ?,
                            avg_efficiency = ?,
                            success_rate = ?
                        WHERE pattern_id = ?
                    """, (
                        new_count, new_success, json.dumps(examples),
                        new_avg_eff, new_success / new_count,
                        pattern_id
                    ))
                    
                    logger.info(f" Updated pattern {pattern_id}: {new_count} occurrences")
            else:
                # Create new pattern
                pattern_name = f"{pattern_signature.get('transformation_type', 'unknown')}_{pattern_tags[0] if pattern_tags else 'generic'}"
                
                self.db.execute_query("""
                    INSERT INTO discovered_patterns (
                        pattern_id, pattern_name, pattern_type, pattern_signature,
                        concrete_examples, occurrence_count, success_count,
                        success_rate, avg_score_achieved, avg_efficiency,
                        confidence_score, discovered_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pattern_id, pattern_name, 'transformation',
                    json.dumps(pattern_signature), json.dumps([sequence_id]),
                    1, 1, 1.0, 1.0, efficiency, 0.5,
                    datetime.now().isoformat()
                ))
                
                logger.info(f"🆕 Discovered new pattern {pattern_id}: {pattern_name}")
        
        except Exception as e:
            logger.debug(f"Abstract pattern detection error: {e}")
    
    def _find_similar_patterns(self, current_frame) -> Optional[Dict]:
        """
        Find patterns that might apply to the current game state.
        Uses abstract pattern matching rather than exact frame matching.
        """
        try:
            # Get current frame characteristics
            dummy_final = current_frame  # We don't know final yet
            current_sig = self._detect_frame_pattern(current_frame, dummy_final)
            
            # Query patterns with similar characteristics
            all_patterns = self.db.execute_query("""
                SELECT pattern_id, pattern_name, pattern_signature, 
                       concrete_examples, success_rate, avg_efficiency,
                       confidence_score
                FROM discovered_patterns
                WHERE success_rate >= 0.5
                ORDER BY confidence_score DESC, success_rate DESC
                LIMIT 10
            """)
            
            best_match = None
            best_score = 0.0
            
            for pat in all_patterns:
                try:
                    sig = json.loads(pat['pattern_signature'])
                    
                    # Calculate similarity score
                    similarity = 0.0
                    
                    # Grid size match
                    if sig.get('grid_size') == current_sig.get('grid_size'):
                        similarity += 0.3
                    
                    # Transformation type match
                    if sig.get('transformation_type') == current_sig.get('transformation_type'):
                        similarity += 0.3
                    
                    # Pattern features
                    if sig.get('symmetry_detected') == current_sig.get('symmetry_detected'):
                        similarity += 0.2
                    
                    if sig.get('repetition_detected') == current_sig.get('repetition_detected'):
                        similarity += 0.2
                    
                    # Weight by pattern success rate and confidence
                    weighted_score = similarity * pat['success_rate'] * pat['confidence_score']
                    
                    if weighted_score > best_score:
                        best_score = weighted_score
                        best_match = pat
                
                except Exception as e:
                    logger.debug(f"Pattern matching error: {e}")
                    continue
            
            if best_match and best_score >= 0.3:
                logger.info(f" Found similar pattern {best_match['pattern_id']} "
                           f"(similarity: {best_score:.2f})")
                return best_match
            
        except Exception as e:
            logger.debug(f"Pattern search error: {e}")
        
        return None
    
    # ========== META-LEARNING METHODS (Rule 10: Integrated into core_gameplay.py) ==========
    
    def _meta_learn_pattern_from_frame(self, frame: np.ndarray) -> Optional[Dict[str, Any]]:
        """
        Meta-learning: Analyzes frame and discovers pattern rules without hardcoding.
        
        Discovers:
        - Anomalies (odd one out)
        - Templates/Keys (transformation examples)
        - Spatial significance (center, corners, edges)
        - Transformation rules (what to apply)
        
        Args:
            frame: Current game frame (numpy array)
            
        Returns:
            Dictionary with discovered pattern and transformation actions, or None
        """
        if frame is None or frame.size == 0:
            return None
            
        try:
            # Step 1: Find what's special (anomalies)
            anomalies = self._meta_detect_anomalies(frame)
            logger.info(f"🧠 Meta: Detected {len(anomalies)} anomalies")
            
            # Step 2: Check spatial significance
            spatial_features = self._meta_analyze_spatial_significance(frame, anomalies)
            logger.info(f"🧠 Meta: {len(spatial_features.get('center_anomalies', []))} center, "
                       f"{len(spatial_features.get('corner_anomalies', []))} corner, "
                       f"{len(spatial_features.get('edge_anomalies', []))} edge")
            
            # Step 3: Look for templates/transformation examples
            templates = self._meta_find_transformation_templates(frame, anomalies, spatial_features)
            logger.info(f"🧠 Meta: Found {len(templates)} potential templates")
            
            # Step 4: Extract transformation rules
            if templates:
                rule = self._meta_extract_transformation_rule(frame, templates[0])
                logger.info(f"🧠 Meta: Extracted rule: {rule}")
                
                if rule:
                    # Step 5: Find where to apply the rule
                    targets = self._meta_find_application_targets(frame, rule)
                    
                    # Step 6: Generate actions
                    actions = self._meta_generate_transformation_actions(frame, targets, rule)
                    
                    return {
                        'pattern_type': 'template_transformation',
                        'rule': rule,
                        'template_region': templates[0],
                        'target_regions': targets,
                        'actions': actions,
                        'confidence': self._meta_calculate_confidence(rule, targets)
                    }
            
            # Try other pattern types
            symmetry_pattern = self._meta_detect_symmetry_completion(frame)
            if symmetry_pattern:
                return symmetry_pattern
                
            return None
            
        except Exception as e:
            logger.error(f"Error in pattern meta-learning: {e}")
            return None
    
    def _meta_detect_anomalies(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Finds regions that are different from others (odd one out)."""
        anomalies = []
        regions = self._meta_segment_into_regions(frame)
        
        if len(regions) < 2:
            return anomalies
        
        # Calculate complexity scores
        complexity_scores = []
        for region in regions:
            score = {
                'region': region,
                'unique_colors': len(np.unique(region['pixels'])),
                'color_changes': self._meta_count_color_boundaries(region['pixels']),
                'entropy': self._meta_calculate_entropy(region['pixels']),
                'has_substructure': self._meta_has_nested_structure(region['pixels'])
            }
            complexity_scores.append(score)
        
        # Find statistical outliers
        avg_colors = np.mean([s['unique_colors'] for s in complexity_scores])
        avg_changes = np.mean([s['color_changes'] for s in complexity_scores])
        
        for score in complexity_scores:
            if (score['unique_colors'] > avg_colors * 1.5 or 
                score['color_changes'] > avg_changes * 1.5 or
                score['has_substructure']):
                anomalies.append({
                    'region': score['region'],
                    'complexity': score,
                    'reason': 'Higher complexity than peers'
                })
        
        return anomalies
    
    def _meta_analyze_spatial_significance(self, frame: np.ndarray, 
                                          anomalies: List[Dict]) -> Dict[str, Any]:
        """Checks if anomalies are in significant positions."""
        height, width = frame.shape[:2]
        frame_center = (height // 2, width // 2)
        
        features = {
            'center_anomalies': [],
            'corner_anomalies': [],
            'edge_anomalies': []
        }
        
        for anomaly in anomalies:
            region = anomaly['region']
            region_center = region['center']
            
            distance = np.sqrt((region_center[0] - frame_center[0])**2 + 
                             (region_center[1] - frame_center[1])**2)
            normalized_distance = distance / np.sqrt(height**2 + width**2)
            
            if normalized_distance < 0.2:  # Very close to center
                features['center_anomalies'].append({
                    'anomaly': anomaly,
                    'distance': distance,
                    'weight': 2.0  # Center gets higher weight
                })
            elif self._meta_is_near_corner(region_center, (height, width)):
                features['corner_anomalies'].append(anomaly)
            elif self._meta_is_near_edge(region_center, (height, width)):
                features['edge_anomalies'].append(anomaly)
        
        return features
    
    def _meta_find_transformation_templates(self, frame: np.ndarray, 
                                           anomalies: List[Dict],
                                           spatial_features: Dict) -> List[Dict]:
        """Identifies regions that demonstrate transformations."""
        templates = []
        
        # Central anomalies are most likely to be templates
        for center_anomaly in spatial_features.get('center_anomalies', []):
            anomaly = center_anomaly['anomaly']
            region = anomaly['region']
            
            if self._meta_has_nested_structure(region['pixels']):
                layers = self._meta_extract_layers(region['pixels'])
                
                if layers and len(layers) >= 2:
                    templates.append({
                        'region': region,
                        'layers': layers,
                        'type': 'nested_transformation',
                        'weight': center_anomaly['weight']
                    })
        
        # Also check regular anomalies
        for anomaly in anomalies:
            region = anomaly['region']
            if self._meta_shows_color_transformation(region['pixels']):
                templates.append({
                    'region': region,
                    'type': 'color_transformation',
                    'weight': 1.0
                })
        
        templates.sort(key=lambda x: x['weight'], reverse=True)
        return templates
    
    def _meta_extract_transformation_rule(self, frame: np.ndarray, 
                                         template: Dict) -> Optional[Dict[str, Any]]:
        """Extracts the transformation rule from a template region."""
        region = template['region']
        pixels = region['pixels']
        
        logger.debug(f"Extracting rule from template type: {template['type']}")
        
        if template['type'] == 'nested_transformation':
            layers = template['layers']
            
            if len(layers) >= 2:
                outer_layer = layers[0]  # Border
                inner_layer = layers[-1]  # Center (most inner)
                
                outer_color = self._meta_get_dominant_color(outer_layer)
                inner_color = self._meta_get_dominant_color(inner_layer)
                
                if outer_color != inner_color:
                    center_ratio = self._meta_calculate_center_ratio(layers)
                    
                    return {
                        'type': 'add_center_pattern',
                        'border_color': int(outer_color),
                        'center_color': int(inner_color),
                        'center_ratio': center_ratio,
                        'template_position': region['center']
                    }
        
        elif template['type'] == 'color_transformation':
            color_freq = Counter(pixels.flatten())
            
            if len(color_freq) >= 2:
                colors = sorted(color_freq.items(), key=lambda x: x[1], reverse=True)
                return {
                    'type': 'color_replacement',
                    'from_color': int(colors[1][0]),
                    'to_color': int(colors[0][0])
                }
        
        return None
    
    def _meta_find_application_targets(self, frame: np.ndarray, 
                                      rule: Dict) -> List[Dict[str, Any]]:
        """Finds regions where the transformation rule should be applied."""
        targets = []
        regions = self._meta_segment_into_regions(frame)
        
        if rule['type'] == 'add_center_pattern':
            border_color = rule['border_color']
            template_pos = rule['template_position']
            
            for region in regions:
                # Skip the template itself
                if self._meta_regions_overlap(region['center'], template_pos, threshold=5):
                    continue
                
                dominant_color = self._meta_get_dominant_color(region['pixels'])
                
                if dominant_color == border_color:
                    targets.append({
                        'region': region,
                        'reason': 'Matches border color pattern'
                    })
        
        elif rule['type'] == 'color_replacement':
            from_color = rule['from_color']
            
            for region in regions:
                if np.any(region['pixels'] == from_color):
                    targets.append({
                        'region': region,
                        'reason': 'Contains color to replace'
                    })
        
        return targets
    
    def _meta_generate_transformation_actions(self, frame: np.ndarray, 
                                             targets: List[Dict],
                                             rule: Dict) -> List[Dict[str, Any]]:
        """Generates ACTION6 coordinates to execute the transformation."""
        actions = []
        
        if rule['type'] == 'add_center_pattern':
            center_color = rule['center_color']
            center_ratio = rule['center_ratio']
            
            for target in targets:
                region = target['region']
                region_center = region['center']
                region_size = region['size']
                
                center_size = int(region_size * center_ratio)
                center_radius = int(np.sqrt(center_size) / 2)
                
                for dy in range(-center_radius, center_radius + 1):
                    for dx in range(-center_radius, center_radius + 1):
                        y = region_center[0] + dy
                        x = region_center[1] + dx
                        
                        if 0 <= y < frame.shape[0] and 0 <= x < frame.shape[1]:
                            actions.append({
                                'type': 'ACTION6',
                                'coordinate': (x, y),
                                'color': center_color,
                                'reason': 'Applying template pattern to center',
                                'rule_type': 'add_center_pattern'
                            })
        
        return actions
    
    def _meta_calculate_confidence(self, rule: Dict, targets: List[Dict]) -> float:
        """Calculates confidence score for the discovered pattern."""
        base_confidence = 0.5
        target_bonus = min(len(targets) * 0.1, 0.3)
        
        if rule['type'] in ['add_center_pattern', 'color_replacement']:
            type_bonus = 0.2
        else:
            type_bonus = 0.0
        
        return min(base_confidence + target_bonus + type_bonus, 1.0)
    
    def _meta_detect_symmetry_completion(self, frame: np.ndarray) -> Optional[Dict]:
        """Detects if pattern requires symmetry completion."""
        height, width = frame.shape[:2]
        
        left_half = frame[:, :width//2]
        right_half = frame[:, width//2:]
        
        if right_half.shape[1] > 0 and left_half.shape == right_half.shape:
            right_unique = len(np.unique(right_half))
            left_unique = len(np.unique(left_half))
            
            if right_unique < left_unique:
                return {
                    'pattern_type': 'symmetry_completion',
                    'rule': {'type': 'mirror_horizontal', 'source': 'left'},
                    'confidence': 0.6
                }
        
        return None
    
    # Helper methods for meta-learning
    
    def _meta_segment_into_regions(self, frame: np.ndarray) -> List[Dict]:
        """Segments frame into distinct rectangular regions."""
        regions = []
        height, width = frame.shape[:2]
        
        region_size = self._meta_detect_grid_size(frame)
        
        if region_size:
            rows = height // region_size
            cols = width // region_size
            
            for r in range(rows):
                for c in range(cols):
                    y1 = r * region_size
                    x1 = c * region_size
                    y2 = min(y1 + region_size, height)
                    x2 = min(x1 + region_size, width)
                    
                    region_pixels = frame[y1:y2, x1:x2]
                    
                    regions.append({
                        'pixels': region_pixels,
                        'bounds': (y1, x1, y2, x2),
                        'center': ((y1 + y2) // 2, (x1 + x2) // 2),
                        'size': region_pixels.size
                    })
        
        return regions
    
    def _meta_detect_grid_size(self, frame: np.ndarray) -> Optional[int]:
        """Attempts to detect if frame has a grid structure."""
        height, width = frame.shape[:2]
        
        common_sizes = [height // 3, height // 4, height // 5, 
                       width // 3, width // 4, width // 5]
        
        for size in common_sizes:
            if size > 5:
                h_rem = height % size
                w_rem = width % size
                
                if h_rem < 5 and w_rem < 5:
                    return size
        
        return None
    
    def _meta_count_color_boundaries(self, pixels: np.ndarray) -> int:
        """Counts number of color transitions in region."""
        if pixels.size < 2:
            return 0
        
        flat = pixels.flatten()
        boundaries = np.sum(flat[:-1] != flat[1:])
        return int(boundaries)
    
    def _meta_calculate_entropy(self, pixels: np.ndarray) -> float:
        """Calculates Shannon entropy of color distribution."""
        if pixels.size == 0:
            return 0.0
        
        _, counts = np.unique(pixels, return_counts=True)
        probs = counts / pixels.size
        entropy = -np.sum(probs * np.log2(probs + 1e-10))
        return float(entropy)
    
    def _meta_has_nested_structure(self, pixels: np.ndarray) -> bool:
        """Checks if region has nested/layered structure."""
        if pixels.size < 9:
            return False
        
        height, width = pixels.shape[:2]
        
        if height < 3 or width < 3:
            return False
        
        cy1, cy2 = height // 3, 2 * height // 3
        cx1, cx2 = width // 3, 2 * width // 3
        
        center = pixels[cy1:cy2, cx1:cx2]
        edges = np.concatenate([
            pixels[0, :], pixels[-1, :],
            pixels[:, 0], pixels[:, -1]
        ])
        
        center_color = self._meta_get_dominant_color(center)
        edge_color = self._meta_get_dominant_color(edges)
        
        return center_color != edge_color
    
    def _meta_extract_layers(self, pixels: np.ndarray) -> List[np.ndarray]:
        """Extracts concentric layers from region."""
        layers = []
        height, width = pixels.shape[:2]
        
        if height < 3 or width < 3:
            return [pixels]
        
        # Outer layer (edges)
        outer = np.concatenate([
            pixels[0, :], pixels[-1, :],
            pixels[1:-1, 0], pixels[1:-1, -1]
        ])
        layers.append(outer)
        
        # Middle layer (if exists)
        if height >= 5 and width >= 5:
            middle = np.concatenate([
                pixels[1, 1:-1], pixels[-2, 1:-1],
                pixels[2:-2, 1], pixels[2:-2, -2]
            ])
            layers.append(middle)
        
        # Inner core
        center_margin = max(height // 4, width // 4)
        if center_margin > 0:
            inner = pixels[center_margin:-center_margin, center_margin:-center_margin]
            if inner.size > 0:
                layers.append(inner)
        
        return layers
    
    def _meta_get_dominant_color(self, pixels: np.ndarray) -> int:
        """Returns most common color in region."""
        if pixels.size == 0:
            return 0
        
        values, counts = np.unique(pixels.flatten(), return_counts=True)
        return int(values[np.argmax(counts)])
    
    def _meta_calculate_center_ratio(self, layers: List[np.ndarray]) -> float:
        """Calculates ratio of center size to total region."""
        if len(layers) < 2:
            return 0.25
        
        total_size = sum(layer.size for layer in layers)
        center_size = layers[-1].size
        
        return center_size / total_size if total_size > 0 else 0.25
    
    def _meta_shows_color_transformation(self, pixels: np.ndarray) -> bool:
        """Checks if region shows evidence of color transformation."""
        unique_colors = len(np.unique(pixels))
        return unique_colors >= 2 and unique_colors <= 4
    
    def _meta_regions_overlap(self, pos1: Tuple[int, int], 
                             pos2: Tuple[int, int], 
                             threshold: int = 5) -> bool:
        """Checks if two positions are close (same region)."""
        distance = np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
        return distance < threshold
    
    def _meta_is_near_corner(self, pos: Tuple[int, int], 
                            frame_size: Tuple[int, int]) -> bool:
        """Checks if position is near a corner."""
        y, x = pos
        h, w = frame_size
        
        threshold = min(h, w) * 0.2
        corners = [(0, 0), (0, w-1), (h-1, 0), (h-1, w-1)]
        
        for cy, cx in corners:
            distance = np.sqrt((y - cy)**2 + (x - cx)**2)
            if distance < threshold:
                return True
        
        return False
    
    def _meta_is_near_edge(self, pos: Tuple[int, int], 
                          frame_size: Tuple[int, int]) -> bool:
        """Checks if position is near an edge."""
        y, x = pos
        h, w = frame_size
        
        threshold = min(h, w) * 0.15
        
        return (y < threshold or y > h - threshold or 
                x < threshold or x > w - threshold)
    
    # ========== END META-LEARNING METHODS ==========
    
    def _store_discovered_pattern(self, pattern_result: Dict[str, Any]) -> None:
        """
        Stores a pattern discovered by the meta-learner for future use.
        
        Args:
            pattern_result: Pattern detection result from meta-learner
        """
        try:
            pattern_type = pattern_result.get('pattern_type', 'unknown')
            rule = pattern_result.get('rule', {})
            confidence = pattern_result.get('confidence', 0.5)
            
            # Generate unique pattern ID based on rule
            import hashlib
            rule_str = json.dumps(rule, sort_keys=True)
            pattern_id = f"meta_{hashlib.md5(rule_str.encode()).hexdigest()[:16]}"
            
            # Check if pattern already exists
            existing = self.db.execute_query("""
                SELECT pattern_id, occurrence_count, success_count
                FROM discovered_patterns
                WHERE pattern_id = ?
            """, (pattern_id,))
            
            if existing:
                # Update existing pattern
                old_count = existing[0]['occurrence_count']
                old_success = existing[0]['success_count']
                
                new_count = old_count + 1
                new_confidence = min((old_success + 1) / new_count, 1.0)
                
                self.db.execute_query("""
                    UPDATE discovered_patterns
                    SET occurrence_count = ?,
                        confidence_score = ?,
                        last_validated = ?
                    WHERE pattern_id = ?
                """, (new_count, new_confidence, datetime.now().isoformat(), pattern_id))
                
                logger.info(f" Updated meta-pattern {pattern_id}: {new_count} occurrences")
            else:
                # Create new pattern
                pattern_name = f"meta_{pattern_type}_{rule['type']}"
                
                self.db.execute_query("""
                    INSERT INTO discovered_patterns (
                        pattern_id, pattern_name, pattern_type, pattern_signature,
                        concrete_examples, occurrence_count, success_count, success_rate,
                        avg_score_achieved, avg_efficiency, confidence_score, discovered_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pattern_id, pattern_name, pattern_type,
                    json.dumps(rule), json.dumps([]),  # Empty examples for meta-patterns
                    1, 0, 0.0, 0.0, 0.0, confidence,
                    datetime.now().isoformat()
                ))
                
                logger.info(f"🆕 Stored meta-learned pattern: {pattern_name}")
        
        except Exception as e:
            logger.error(f"Error storing discovered pattern: {e}")

    def _is_unbeaten_game(self, game_id: str) -> bool:
        """
        Check if a game has never had any level completions by any agent.
        
        Args:
            game_id: Game ID to check
            
        Returns:
            True if no agent has ever completed a level in this game
        """
        try:
            level_completions = self.db.execute_query("""
                SELECT COUNT(*) as completions
                FROM agent_arc_performance 
                WHERE game_id = ? AND level_progressions > 0
            """, (game_id,))
            
            if level_completions and level_completions[0]:
                return level_completions[0]['completions'] == 0
            else:
                return True  # No data means unbeaten
                
        except Exception as e:
            logger.warning(f"Error checking unbeaten game status for {game_id}: {e}")
            return False  # Safe default

    def _get_network_action_wisdom(self, game_id: str, level_number: int, 
                                    agent_id: str, current_frame: Any) -> Optional[Dict]:
        """
        CRITICAL: Get network's collective action wisdom for frontier exploration.
        
        Abstracts historical gameplay from all agents on this game type + level
        to suggest the best action when no proven sequences exist.
        
        This implements the user's requirement:
        "abstract the history of their own gameplay as agents on this level 
        from previous games, and decide what to do next"
        
        Args:
            game_id: Current game ID
            level_number: Current level being played
            agent_id: Current agent ID
            current_frame: Current game frame for context
            
        Returns:
            Dict with 'action', 'confidence', 'reasoning' or None
        """
        try:
            # Extract game type prefix for cross-session learning
            game_type = game_id.split('-')[0] if '-' in game_id else game_id
            
            # ===================================================================
            # STAGE 1: Query historical action traces for this game type + level
            # Find which actions led to score improvements at this level
            # ===================================================================
            action_success = self.db.execute_query("""
                SELECT 
                    action_number,
                    COUNT(*) as total_attempts,
                    SUM(CASE WHEN score_change > 0 THEN 1 ELSE 0 END) as successes,
                    AVG(score_change) as avg_score_change
                FROM action_traces
                WHERE game_id LIKE ? 
                  AND level_number = ?
                  AND action_number IS NOT NULL
                GROUP BY action_number
                HAVING total_attempts >= 3
                ORDER BY avg_score_change DESC, successes DESC
            """, (f"{game_type}-%", level_number))
            
            if action_success and len(action_success) > 0:
                # Calculate success rates
                best_action = None
                best_confidence = 0.0
                action_analysis = []
                
                for row in action_success:
                    action_num = row['action_number']
                    total = row['total_attempts']
                    successes = row['successes'] or 0
                    avg_change = row['avg_score_change'] or 0.0
                    
                    success_rate = successes / total if total > 0 else 0.0
                    
                    # Confidence = weighted combination of success rate and sample size
                    sample_weight = min(total / 50.0, 1.0)  # More samples = more confident
                    confidence = success_rate * 0.6 + avg_change * 0.2 + sample_weight * 0.2
                    
                    action_analysis.append({
                        'action': action_num,
                        'confidence': confidence,
                        'success_rate': success_rate,
                        'total_attempts': total,
                        'avg_score_change': avg_change
                    })
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_action = action_num
                
                if best_action and best_confidence >= 0.3:
                    # Get agent's social rule adherence for bias adjustment
                    agent_data = self.db.execute_query("""
                        SELECT social_rule_adherence
                        FROM agents
                        WHERE agent_id = ?
                    """, (agent_id,))
                    
                    social_adherence = 0.7  # Default to social
                    if agent_data and agent_data[0]['social_rule_adherence'] is not None:
                        social_adherence = agent_data[0]['social_rule_adherence']
                    
                    # Sociopaths (low adherence) may ignore network wisdom
                    if social_adherence < 0.3:
                        # 30% chance sociopath ignores network wisdom
                        import random
                        if random.random() < 0.3:
                            logger.debug(f"🦹 Sociopath agent ignoring network wisdom (adherence: {social_adherence:.2f})")
                            return None
                    
                    reasoning = f"Network history: ACTION{best_action} has {action_analysis[0]['success_rate']:.1%} success rate at L{level_number} ({action_analysis[0]['total_attempts']} attempts)"
                    
                    return {
                        'action': best_action,
                        'confidence': min(best_confidence * social_adherence, 1.0),
                        'reasoning': reasoning,
                        'analysis': action_analysis
                    }
            
            # ===================================================================
            # STAGE 2: If no level-specific data, try game type patterns
            # ===================================================================
            game_type_patterns = self.db.execute_query("""
                SELECT 
                    action_number,
                    COUNT(*) as total,
                    SUM(CASE WHEN score_change > 0 THEN 1 ELSE 0 END) as wins
                FROM action_traces
                WHERE game_id LIKE ?
                  AND action_number IS NOT NULL
                GROUP BY action_number
                HAVING total >= 10
                ORDER BY (wins * 1.0 / total) DESC
                LIMIT 3
            """, (f"{game_type}-%",))
            
            if game_type_patterns and len(game_type_patterns) > 0:
                best = game_type_patterns[0]
                action_num = best['action_number']
                success_rate = best['wins'] / best['total'] if best['total'] > 0 else 0.0
                
                if success_rate >= 0.1:  # Lower threshold for game type fallback
                    return {
                        'action': action_num,
                        'confidence': success_rate * 0.5,  # Lower confidence for general pattern
                        'reasoning': f"Game type pattern: ACTION{action_num} works {success_rate:.1%} of time on {game_type} games"
                    }
            
            return None
            
        except Exception as e:
            logger.debug(f"Error getting network action wisdom: {e}")
            return None

    # Phase 4.5: Sensation-based navigation helper methods
    
    def _convert_game_state_for_sensation_analysis(self, game_state: GameState) -> Dict[str, Any]:
        """Convert GameState to format suitable for sensation analysis."""
        
        frame_data = {
            'current_frame': {},
            'game_id': self.session_manager.current_game_id or '',
            'generation': self.game_config.get('generation', 0),
            'current_score': game_state.score
        }
        
        # Extract grid data from frame
        if game_state.frame is not None:
            frame = game_state.frame
            if isinstance(frame, (list, np.ndarray)):
                frame_data['current_frame']['grid'] = frame
            else:
                frame_data['current_frame']['grid'] = []
        else:
            frame_data['current_frame']['grid'] = []
        
        return frame_data

    def _analyze_sensation_context(self, frame_data: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """Analyze frame data for sensation context."""
        
        sensation_context = {
            'dominant_sensation': 0.0,
            'perceived_objects': [],
            'complexity_score': 0.0
        }
        
        grid = frame_data.get('current_frame', {}).get('grid', [])
        
        if not grid:
            return sensation_context
        
        try:
            # Convert to numpy array for analysis
            if not isinstance(grid, np.ndarray):
                grid = np.array(grid)
            
            if grid.size == 0:
                return sensation_context
            
            # Analyze grid properties
            unique_colors = len(np.unique(grid))
            non_zero_cells = np.count_nonzero(grid)
            total_cells = grid.size
            
            # Determine perceived objects based on grid analysis
            perceived_objects = []
            
            if unique_colors > 1:
                perceived_objects.append('multi_color_pattern')
            if unique_colors > 3:
                perceived_objects.append('complex_color_pattern')
            if non_zero_cells > total_cells * 0.5:
                perceived_objects.append('dense_pattern')
            if non_zero_cells < total_cells * 0.1:
                perceived_objects.append('sparse_pattern')
            if grid.shape[0] > 10 or grid.shape[1] > 10:
                perceived_objects.append('large_grid')
            
            # Calculate complexity score
            complexity_score = (unique_colors / 10.0) + (non_zero_cells / total_cells)
            
            # Calculate dominant sensation from perceived objects
            total_sensation = 0.0
            sensation_count = 0
            
            for obj_type in perceived_objects:
                obj_sensation = self.sensation_engine.perceive_object(
                    agent_id, obj_type, {'complexity': complexity_score}
                )
                total_sensation += obj_sensation
                sensation_count += 1
            
            if sensation_count > 0:
                sensation_context['dominant_sensation'] = total_sensation / sensation_count
            
            sensation_context['perceived_objects'] = perceived_objects
            sensation_context['complexity_score'] = complexity_score
        
        except Exception as e:
            logger.debug(f"Error in sensation analysis: {e}")
        
        return sensation_context

    def _calculate_recent_success_rate_from_game_state(self, game_state: GameState) -> float:
        """Calculate recent success rate from current game context."""
        
        try:
            # Use current score as proxy for recent success
            current_score = game_state.score
            
            # Simple heuristic: higher score = higher success rate
            # This can be enhanced with more sophisticated tracking
            if current_score >= 3.0:  # Multiple levels completed
                return 0.8
            elif current_score >= 1.0:  # At least one level completed
                return 0.6
            elif current_score > 0.0:  # Some progress
                return 0.4
            else:  # No progress yet
                return 0.2
        
        except Exception as e:
            logger.debug(f"Error calculating recent success rate: {e}")
            return 0.5  # Neutral default

    def _get_emotion_label(self, navigation_state: float) -> str:
        """Get emotion label from navigation state."""
        
        if navigation_state > 0.5:
            return 'confident'
        elif navigation_state > 0.1:
            return 'curious'
        elif navigation_state > -0.1:
            return 'neutral'
        elif navigation_state > -0.5:
            return 'cautious'
        else:
            return 'frustrated'

    def _learn_from_action_outcome(self, action: str, previous_score: float, 
                                 current_game_state: GameState, agent_id: str) -> None:
        """Learn from action outcome using sensation system."""
        
        try:
            # Extract action number
            if isinstance(action, str) and action.startswith('ACTION'):
                action_num = int(action.replace('ACTION', ''))
            elif isinstance(action, int):
                action_num = action
            else:
                return  # Can't process this action format
            
            # Only learn from navigation actions (1-7)
            if action_num not in {1, 2, 3, 4, 5, 6, 7}:
                return
            
            # Calculate reward from score change
            score_change = current_game_state.score - previous_score
            
            # Create outcome dictionary
            outcome = {
                'game_id': self.session_manager.current_game_id or '',
                'generation': self.game_config.get('generation', 0),
                'score_change': score_change,
                'action_success': score_change > 0,  # Positive score change = success
                'game_won': current_game_state.state in ['FINISHED', 'WON'],
                'game_state': current_game_state.state
            }
            
            # Get perceived objects from last sensation analysis
            perceived_objects = getattr(self, '_last_perceived_objects', ['unknown_object'])
            if not perceived_objects:
                perceived_objects = ['unknown_object']
            
            # Get current navigation state
            agent_result = self.db.execute_query(
                "SELECT navigation_state FROM agents WHERE agent_id = ?",
                (agent_id,)
            )
            navigation_state = agent_result[0]['navigation_state'] if agent_result else 0.0
            
            # Learn from each perceived object
            learning_occurred = False
            for obj_type in perceived_objects:
                if self.sensation_engine.learn_from_outcome(
                    agent_id, obj_type, action_num, outcome, navigation_state
                ):
                    learning_occurred = True
            
            if learning_occurred:
                logger.debug(f"🧠 Agent learned from action {action_num} outcome (score change: {score_change:+.1f})")
        
        except Exception as e:
            logger.debug(f"Error in sensation learning: {e}")
    
    def _get_network_max_level(self, game_id: str) -> int:
        """
        Get the maximum level the NETWORK has reached for this game type.
        Used to determine if a pariah is on an unbeaten level.
        
        Returns:
            Maximum level reached by any agent, or 0 if none
        """
        try:
            game_type = game_id.split('-')[0] if '-' in game_id else game_id
            
            result = self.db.execute_query("""
                SELECT MAX(level_progressions) as max_level
                FROM agent_arc_performance
                WHERE game_id LIKE ?
            """, (f"{game_type}-%",))
            
            if result and result[0]['max_level']:
                return int(result[0]['max_level'])
                
        except Exception as e:
            logger.debug(f"Error getting network max level: {e}")
        
        return 0
    
    def _analyze_pariah_worthiness(self, sequence: Dict[str, Any], game_id: str) -> Dict[str, Any]:
        """
        Analyze if a pariah sequence is worth challenging for optimizers/exploiters.
        
        Optimizers/Exploiters should:
        - SKIP pariahs with <30% validation success (unreliable)
        - SKIP pariahs from OLD levels (network has moved past)
        - CHALLENGE pariahs from CURRENT frontier level (worth testing)
        - CHALLENGE pariahs with >70% validation but unoptimized actions
        
        Args:
            sequence: The sequence to analyze
            game_id: Current game ID
            
        Returns:
            Dict with 'worth_challenging' (bool) and 'reason' (str)
        """
        try:
            sequence_id = sequence['sequence_id']
            sequence_level = int(sequence.get('total_score', 0))
            sequence_actions = sequence.get('total_actions', 0)
            
            # Get validation stats
            validation = self.db.execute_query("""
                SELECT successful_validations, total_validation_attempts,
                       CAST(successful_validations AS FLOAT) / NULLIF(total_validation_attempts, 0) as success_rate,
                       reliability_score
                FROM sequence_reputation
                WHERE sequence_id = ?
            """, (sequence_id,))
            
            if not validation or validation[0]['total_validation_attempts'] == 0:
                # Untested pariah - worth one try for exploiters
                return {
                    'worth_challenging': True,
                    'reason': 'Untested pariah - validating reliability'
                }
            
            val = validation[0]
            success_rate = val['success_rate'] or 0.0
            reliability = val['reliability_score'] or 0.0
            
            # Rule 1: Skip if reliability is terrible (<30%)
            if success_rate < 0.3:
                return {
                    'worth_challenging': False,
                    'reason': f'Low reliability ({success_rate:.1%}) - likely broken'
                }
            
            # Rule 2: Check if this is from an OLD level
            network_max = self._get_network_max_level(game_id)
            if sequence_level < network_max - 1:
                return {
                    'worth_challenging': False,
                    'reason': f'Old level (L{sequence_level} vs network L{network_max}) - network moved past'
                }
            
            # Rule 3: Check if sequence is from CURRENT frontier
            if sequence_level >= network_max - 1:
                return {
                    'worth_challenging': True,
                    'reason': f'Frontier level (L{sequence_level}, network L{network_max}) - worth testing'
                }
            
            # Rule 4: High reliability (>70%) but many actions - worth optimizing
            if success_rate > 0.7 and sequence_actions > 50:
                return {
                    'worth_challenging': True,
                    'reason': f'Reliable ({success_rate:.1%}) but unoptimized ({sequence_actions} actions) - can improve'
                }
            
            # Rule 5: Medium reliability (30-70%) - worth testing
            if 0.3 <= success_rate <= 0.7:
                return {
                    'worth_challenging': True,
                    'reason': f'Moderate reliability ({success_rate:.1%}) - needs more validation'
                }
            
            # Default: challenge it
            return {
                'worth_challenging': True,
                'reason': f'Standard pariah (L{sequence_level}, {success_rate:.1%} success) - testing'
            }
            
        except Exception as e:
            logger.error(f"Error analyzing pariah worthiness: {e}")
            # Default to challenging on error
            return {
                'worth_challenging': True,
                'reason': 'Analysis error - defaulting to challenge'
            }


# Simple gameplay strategies that can be used as action callbacks

async def random_strategy(game_state: GameState, action_handler: ActionHandler) -> str:
    """Random action selection strategy."""
    return action_handler.get_random_action(game_state.available_actions)

async def conservative_strategy(game_state: GameState, action_handler: ActionHandler) -> str:
    """Conservative strategy avoiding ACTION6."""
    safe_actions = [a for a in (game_state.available_actions or []) if a != "ACTION6"]
    if not safe_actions:
        safe_actions = ["ACTION1", "ACTION2", "ACTION3", "ACTION4", "ACTION5", "ACTION7"]
    return action_handler.get_random_action(safe_actions)

async def exploration_strategy(game_state: GameState, action_handler: ActionHandler) -> GameState:
    """Exploration strategy that tries different actions."""
    # Prefer ACTION6 for exploration
    if "ACTION6" in (game_state.available_actions or []):
        x, y = action_handler.get_random_coordinates(game_state.frame)
        exploration_reasoning = {
            'action': 'ACTION6',
            'reasoning': 'Random exploration strategy',
            'coordinate': {'x': x, 'y': y},
            'strategy': 'exploration'
        }
        return await action_handler.send_action_6(x, y, game_state.frame, reasoning=exploration_reasoning)
    else:
        action = action_handler.get_random_action(game_state.available_actions)
        method_name = f"send_{action.lower()}"
        method = getattr(action_handler, method_name)
        exploration_reasoning = {
            'action': action,
            'reasoning': 'Random exploration strategy (non-ACTION6)',
            'strategy': 'exploration'
        }
        return await method(reasoning=exploration_reasoning)