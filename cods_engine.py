import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
CODS Engine - Main Orchestrator for Cognitive Operator Discovery System
========================================================================

The central coordinator for the earn-to-learn cognitive operator system.
Integrates all CODS components:
- Seed Primitives (always available)
- Primitive Unlock Manager (track earned primitives)
- Operator Composer (combine primitives)
- Oracle Interface (validate discoveries)

This engine provides the main interface for:
1. Applying operators to game states
2. Testing and validating operators
3. Discovering and unlocking primitives
4. Tracking the evolution of cognitive vocabulary

Rule 1: Disable pycache
Rule 2: All data in database
Rule 10: Leverage existing systems
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import json
import uuid
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Tuple, Union
from dataclasses import dataclass, field

from database_interface import DatabaseInterface
from seed_primitives import get_seed_primitives, SeedPrimitiveRegistry, Primitive
from primitive_unlock_manager import PrimitiveUnlockManager, grandfather_existing_primitives, PrimitiveStatus
from operator_composer import OperatorComposer, ComposedOperator, OperatorStatus
from oracle_interface import OracleInterface, OracleVerdict

# Concept Discovery Engine (Tier 4 - Semantic Models)
try:
    from concept_discovery_engine import ConceptDiscoveryEngine, get_concept_engine
    CONCEPT_ENGINE_AVAILABLE = True
except ImportError:
    CONCEPT_ENGINE_AVAILABLE = False
    ConceptDiscoveryEngine = None  # type: ignore
    get_concept_engine = None  # type: ignore

# Optional imports for existing engines
try:
    from visual_reasoning_engine import VisualReasoningEngine
    VISUAL_ENGINE_AVAILABLE = True
except ImportError:
    VISUAL_ENGINE_AVAILABLE = False
    VisualReasoningEngine = None

try:
    from object_detector import ObjectDetector
    OBJECT_DETECTOR_AVAILABLE = True
except ImportError:
    OBJECT_DETECTOR_AVAILABLE = False
    ObjectDetector = None

try:
    from symbolic_reasoning_engine import SymbolicReasoningEngine
    SYMBOLIC_ENGINE_AVAILABLE = True
except ImportError:
    SYMBOLIC_ENGINE_AVAILABLE = False
    SymbolicReasoningEngine = None

logger = logging.getLogger(__name__)


@dataclass
class CODSGameContext:
    """Context for CODS operations during a game."""
    game_id: str
    level_number: int
    agent_id: Optional[str]
    generation: int = 0
    current_frame: Optional[List[List[int]]] = None
    previous_frame: Optional[List[List[int]]] = None
    action_history: List[int] = field(default_factory=list)
    score: float = 0.0
    persona_id: Optional[str] = None
    world_model: Optional[str] = None
    problem_signature: Optional[str] = None
    is_frontier: bool = False  # True if this level is unexplored territory
    
    def update_frame(self, frame: List[List[int]]):
        """Update current frame, moving old to previous."""
        self.previous_frame = self.current_frame
        self.current_frame = frame


@dataclass
class OperatorResult:
    """Result of applying an operator."""
    success: bool
    output: Any
    execution_time_ms: float
    error: Optional[str] = None
    operator_id: Optional[str] = None


@dataclass
class BayesianHypothesis:
    """
    Represents a hypothesis with Bayesian probability tracking.
    
    The core of evidence-driven operator synthesis:
    - Hypotheses are created from failure patterns
    - Evidence accumulates from game outcomes
    - When posterior exceeds threshold, synthesis is triggered
    """
    hypothesis_id: str
    hypothesis_type: str  # 'PRIMITIVE_NEED', 'OPERATOR_SYNTHESIS', 'PATTERN_DISCOVERY'
    game_type: str
    level_number: Optional[int]
    description: str
    
    # What this hypothesis suggests
    target_primitive: Optional[str] = None  # Primitive to unlock
    suggested_composition: Optional[List[str]] = None  # Primitives to compose
    
    # Bayesian tracking
    prior: float = 0.5
    posterior: float = 0.5
    evidence_for: int = 0
    evidence_against: int = 0
    
    # Confidence interval (Wilson score)
    confidence_low: float = 0.0
    confidence_high: float = 1.0
    
    # Thresholds
    confirmation_threshold: float = 0.85
    refutation_threshold: float = 0.15
    
    # Status
    status: str = 'active'  # 'active', 'confirmed', 'refuted', 'synthesized'
    source_type: Optional[str] = None  # 'failure_analysis', 'counterfactual', 'near_miss'
    
    def is_confirmed(self) -> bool:
        """Check if hypothesis has enough evidence to act on."""
        return self.posterior >= self.confirmation_threshold
    
    def is_refuted(self) -> bool:
        """Check if hypothesis should be abandoned."""
        return self.posterior <= self.refutation_threshold
    
    def sample_size(self) -> int:
        """Total evidence collected."""
        return self.evidence_for + self.evidence_against
    error: Optional[str] = None
    operator_id: Optional[str] = None


class CODSEngine:
    """
    Main orchestrator for the Cognitive Operator Discovery System.
    
    This is the primary interface for:
    1. Using cognitive operators during gameplay
    2. Discovering new operators through composition
    3. Validating and unlocking primitives
    4. Evolving the cognitive vocabulary
    """
    
    def __init__(
        self,
        db: Optional[DatabaseInterface] = None,
        db_path: str = "core_data.db"
    ):
        self.db = db or DatabaseInterface(db_path)
        
        # Initialize components
        self.seeds = get_seed_primitives()
        self.unlock_manager = PrimitiveUnlockManager(db=self.db)
        self.composer = OperatorComposer(
            db=self.db, 
            seed_registry=self.seeds,
            primitive_callback=self._primitive_callback  # Allows composer to call grandfathered primitives
        )
        self.oracle = OracleInterface(db=self.db, unlock_manager=self.unlock_manager)
        
        # Initialize existing engines as wrappers
        self._init_existing_engines()
        
        # Grandfather existing primitives
        grandfather_existing_primitives(self.unlock_manager)
        
        # Tier 4: Concept Discovery Engine (semantic models)
        if CONCEPT_ENGINE_AVAILABLE and get_concept_engine:
            try:
                self.concept_engine = get_concept_engine(db_path)
                logger.info(f"[CODS] Concept discovery engine initialized (Tier 4)")
            except Exception as e:
                self.concept_engine = None
                logger.warning(f"[CODS] Concept engine init failed: {e}")
        else:
            self.concept_engine = None
        
        # Current game context
        self._context: Optional[CODSGameContext] = None
        
        # Operator execution stats
        self._execution_stats: Dict[str, Dict] = {}
        
        # =====================================================================
        # WORLD-MODEL INTEGRATION (from agent_consciousness_synthesis.md)
        # Track discoveries for world-model updates
        # =====================================================================
        self._latest_discovery: Optional[Dict[str, Any]] = None
        self._pending_discoveries: List[Dict[str, Any]] = []
        
        # Ensure failure-driven learning tables exist
        self._ensure_failure_tables()
        
        logger.info(f"[CODS] Engine initialized with {self.seeds.count()} seed primitives")
    
    def _primitive_callback(self, name: str, args: tuple, kwargs: dict) -> Any:
        """
        Callback for OperatorComposer to execute grandfathered/unlocked primitives.
        
        This allows composed operators to use primitives beyond just seed primitives.
        
        Args:
            name: Primitive name
            args: Positional arguments
            kwargs: Keyword arguments
            
        Returns:
            Primitive output
            
        Raises:
            NotImplementedError: If primitive is not available
        """
        # Check if it's an unlocked or grandfathered primitive
        status = self.unlock_manager.get_status(name)
        if status in [PrimitiveStatus.UNLOCKED, PrimitiveStatus.GRANDFATHERED]:
            return self._apply_unlocked_primitive(name, *args, **kwargs)
        
        raise NotImplementedError(f"Primitive '{name}' not available via callback")
    
    def _init_existing_engines(self):
        """Initialize wrappers for existing engine implementations."""
        self._visual_engine = None
        self._object_detector = None
        self._symbolic_engine = None
        
        if VISUAL_ENGINE_AVAILABLE and VisualReasoningEngine is not None:
            try:
                self._visual_engine = VisualReasoningEngine(self.db)  # type: ignore[misc]
                logger.debug("[CODS] VisualReasoningEngine available")
            except Exception as e:
                logger.debug(f"[CODS] VisualReasoningEngine init failed: {e}")
        
        if OBJECT_DETECTOR_AVAILABLE and ObjectDetector is not None:
            try:
                self._object_detector = ObjectDetector()  # type: ignore[misc]
                logger.debug("[CODS] ObjectDetector available")
            except Exception as e:
                logger.debug(f"[CODS] ObjectDetector init failed: {e}")
        
        if SYMBOLIC_ENGINE_AVAILABLE and SymbolicReasoningEngine is not None:
            try:
                self._symbolic_engine = SymbolicReasoningEngine()  # type: ignore[misc]
                logger.debug("[CODS] SymbolicReasoningEngine available")
            except Exception as e:
                logger.debug(f"[CODS] SymbolicReasoningEngine init failed: {e}")
    
    # ======================================================================
    # CONTEXT MANAGEMENT
    # ======================================================================
    
    def set_context(
        self,
        game_id: str,
        level_number: int = 1,
        agent_id: Optional[str] = None,
        generation: int = 0,
        persona_id: Optional[str] = None,
        world_model: Optional[str] = None,
        problem_signature: Optional[str] = None,
        is_frontier: bool = False,
    ):
        """Set the current game context."""
        self._context = CODSGameContext(
            game_id=game_id,
            level_number=level_number,
            agent_id=agent_id,
            generation=generation,
            persona_id=persona_id,
            world_model=world_model,
            problem_signature=problem_signature,
            is_frontier=is_frontier,
        )
        
        # Set episode context in seed primitives
        self.seeds.set_episode_context(game_id)
        self.seeds.reset_episode()
    
    def update_frame(
        self,
        frame: List[List[int]],
        score: Optional[float] = None,
        action_count: Optional[int] = None,
        reasoning: Optional[str] = None,
        hypothesis_id: Optional[str] = None
    ):
        """
        Update current frame in context and test composed operators.
        
        Args:
            frame: Current game frame
            score: Current score (optional, for success evaluation)
            action_count: Current action count (optional)
            reasoning: Agent's reasoning for current action (triggers smart testing)
            hypothesis_id: ID of hypothesis being tested (for tracking)
        """
        previous_frame = None
        previous_score = 0.0
        
        if self._context:
            previous_frame = self._context.current_frame
            previous_score = self._context.score or 0.0
            self._context.update_frame(frame)
            if score is not None:
                self._context.score = score
        
        self.seeds.update_frame(frame)
        
        # Calculate score delta for operator success evaluation
        score_delta = (score or 0.0) - previous_score
        
        # ======================================================================
        # INTELLIGENT OPERATOR TESTING (Updated 2025-12-25)
        # ======================================================================
        # Instead of testing every 10 actions blindly, test based on:
        # 1. Agent reasoning mentions patterns/operators (trigger relevant tests)
        # 2. Score increased (test all operators to capture successful state)
        # 3. Level transition (test to capture state)
        # 4. Hypothesis testing mode (agent is explicitly testing something)
        # 5. Fallback: periodic testing every 20 actions (reduced from 10)
        # ======================================================================
        
        should_test = False
        test_reason = "periodic"
        relevant_operators = None  # None means test all
        
        # Trigger 1: Agent reasoning mentions patterns we have operators for
        if reasoning:
            reasoning_lower = reasoning.lower()
            
            # Check if reasoning mentions visual patterns
            pattern_triggers = {
                'symmetry': ['op_detect_symmetry'],
                'pattern': ['op_find_patterns'],
                'shape': ['op_detect_shapes'],
                'spatial': ['op_spatial_relations'],
                'color': ['op_analyze_colors'],
                'object': ['op_detect_objects'],
            }
            
            for pattern, ops in pattern_triggers.items():
                if pattern in reasoning_lower:
                    should_test = True
                    test_reason = f"reasoning_mentions_{pattern}"
                    relevant_operators = ops
                    logger.info(f"[CODS] Testing triggered by reasoning mention: '{pattern}'")
                    break
            
            # Check for discovery/exploration keywords
            if not should_test:
                discovery_keywords = ['discover', 'explore', 'test', 'hypothesis', 'try']
                if any(kw in reasoning_lower for kw in discovery_keywords):
                    should_test = True
                    test_reason = "discovery_mode"
                    logger.debug("[CODS] Testing triggered by discovery reasoning")
        
        # Trigger 2: Score increased (capture successful state)
        if score_delta > 0:
            should_test = True
            test_reason = "score_increase"
            logger.info(f"[CODS] Testing triggered by score increase: +{score_delta}")
        
        # Trigger 3: Agent is explicitly testing a hypothesis
        if hypothesis_id:
            should_test = True
            test_reason = "hypothesis_test"
            logger.debug(f"[CODS] Testing triggered by hypothesis: {hypothesis_id}")
        
        # Trigger 4: Fallback periodic testing (every 20 actions, reduced overhead)
        if not should_test and action_count is not None:
            if action_count % 20 == 0 and action_count > 0:
                should_test = True
                test_reason = "periodic_20"
        
        # Execute testing
        if should_test:
            game_id = self._context.game_id if self._context else 'unknown'
            logger.info(f"[CODS] Testing operators: reason={test_reason}, game={game_id}")
            
            try:
                results = self.test_composed_operators(
                    frame=frame,
                    previous_frame=previous_frame,
                    score_delta=score_delta,
                    operator_ids=relevant_operators  # Filter to relevant operators if specified
                )
                if results:
                    successes = sum(1 for v in results.values() if v)
                    logger.info(f"[CODS] Tested {len(results)} operators: {successes} success")
                    
                    # Store test context for learning
                    self._store_test_context(
                        game_id=game_id,
                        test_reason=test_reason,
                        reasoning=reasoning,
                        hypothesis_id=hypothesis_id,
                        score_delta=score_delta,
                        results=results
                    )
            except Exception as e:
                logger.warning(f"[CODS] Operator testing failed: {e}")
    
    def record_action(self, action: int):
        """Record an action taken."""
        if self._context:
            self._context.action_history.append(action)
        self.seeds.call('record_action', action)
    
    def update_score(self, score: float):
        """Update current score."""
        if self._context:
            self._context.score = score
    
    # ======================================================================
    # OPERATOR APPLICATION
    # ======================================================================
    
    def apply(
        self,
        operator_name: str,
        *args,
        **kwargs
    ) -> OperatorResult:
        """
        Apply an operator to the current context.
        
        First checks seed primitives, then unlocked primitives,
        then composed operators.
        
        Args:
            operator_name: Name of operator to apply
            *args: Arguments to pass to operator
            **kwargs: Keyword arguments
            
        Returns:
            OperatorResult with output and metadata
        """
        start_time = time.time()
        
        try:
            # 1. Check if it's a seed primitive
            seed_prim = self.seeds.get(operator_name)
            if seed_prim:
                output = seed_prim(*args, **kwargs)
                exec_time = (time.time() - start_time) * 1000
                
                self._record_usage(operator_name, True, exec_time)
                return OperatorResult(
                    success=True,
                    output=output,
                    execution_time_ms=exec_time,
                    operator_id=f"seed:{operator_name}"
                )
            
            # 2. Check if it's an unlocked/grandfathered primitive
            status = self.unlock_manager.get_status(operator_name)
            if status in [PrimitiveStatus.UNLOCKED, PrimitiveStatus.GRANDFATHERED]:
                output = self._apply_unlocked_primitive(operator_name, *args, **kwargs)
                exec_time = (time.time() - start_time) * 1000
                
                self._record_usage(operator_name, True, exec_time)
                return OperatorResult(
                    success=True,
                    output=output,
                    execution_time_ms=exec_time,
                    operator_id=f"unlocked:{operator_name}"
                )
            
            # 3. Check if it's a composed operator (by ID or by name)
            composed_op = self.composer.get_operator(operator_name)
            if not composed_op:
                # Try by name instead of ID
                composed_op = self.composer.get_operator_by_name(operator_name)
            
            if composed_op:
                output = self.composer.execute(composed_op, *args, **kwargs)
                exec_time = (time.time() - start_time) * 1000
                
                self._record_test_result(
                    composed_op.operator_id,
                    success=True,
                    output=output,
                    exec_time=exec_time
                )
                
                return OperatorResult(
                    success=True,
                    output=output,
                    execution_time_ms=exec_time,
                    operator_id=composed_op.operator_id
                )
            
            # 4. Operator not found - it might be locked
            if status == PrimitiveStatus.LOCKED:
                return OperatorResult(
                    success=False,
                    output=None,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    error=f"Primitive '{operator_name}' is locked. Must be earned through discovery."
                )
            
            return OperatorResult(
                success=False,
                output=None,
                execution_time_ms=(time.time() - start_time) * 1000,
                error=f"Unknown operator: {operator_name}"
            )
            
        except Exception as e:
            exec_time = (time.time() - start_time) * 1000
            self._record_usage(operator_name, False, exec_time)
            
            return OperatorResult(
                success=False,
                output=None,
                execution_time_ms=exec_time,
                error=str(e)
            )
    
    def _apply_unlocked_primitive(
        self,
        name: str,
        *args,
        **kwargs
    ) -> Any:
        """Apply an unlocked primitive using existing engine implementations."""
        
        # Map to existing implementations
        if name == 'detect_symmetry' and self._visual_engine:
            frame = args[0] if args else self._context.current_frame if self._context else None
            if frame:
                import numpy as np
                return self._visual_engine.detect_symmetry(np.array(frame))
        
        elif name == 'flood_fill' and self._object_detector:
            # Simplified flood fill wrapper
            frame, x, y, color = args[:4] if len(args) >= 4 else (None, 0, 0, 0)
            if frame:
                visited: set[tuple[int, int]] = set()
                return self._object_detector._flood_fill(frame, x, y, color, visited)
        
        elif name == 'detect_shapes' and self._visual_engine:
            frame = args[0] if args else self._context.current_frame if self._context else None
            if frame:
                import numpy as np
                return self._visual_engine.detect_shapes(np.array(frame))
        
        elif name == 'find_repeating_patterns' and self._visual_engine:
            frame = args[0] if args else self._context.current_frame if self._context else None
            if frame:
                import numpy as np
                return self._visual_engine.find_repeating_patterns(np.array(frame))
        
        elif name == 'analyze_color_distribution' and self._visual_engine:
            frame = args[0] if args else self._context.current_frame if self._context else None
            if frame:
                import numpy as np
                return self._visual_engine.analyze_color_distribution(np.array(frame))
        
        elif name == 'analyze_spatial_relations' and self._visual_engine:
            frame = args[0] if args else self._context.current_frame if self._context else None
            if frame:
                import numpy as np
                return self._visual_engine.analyze_spatial_relations(np.array(frame))
        
        elif name == 'detect_objects_in_frame' and self._object_detector:
            frame = args[0] if args else None
            if frame and self._context:
                return self._object_detector.detect_objects_in_frame(
                    {'grid': frame},
                    self._context.game_id,
                    self._context.level_number,
                    len(self._context.action_history)
                )
        
        # Fallback: try to find in composed operators
        composed = self.composer.get_operator(name)
        if composed:
            return self.composer.execute(composed, *args, **kwargs)
        
        raise NotImplementedError(f"Unlocked primitive '{name}' has no implementation")
    
    # ======================================================================
    # DISCOVERY & COMPOSITION
    # ======================================================================
    
    def compose_operator(
        self,
        primitives: List[str],
        name: Optional[str] = None
    ) -> ComposedOperator:
        """
        Compose a new operator from primitives.
        
        Args:
            primitives: List of primitive/operator names to compose
            name: Optional name for the new operator
            
        Returns:
            New ComposedOperator
        """
        agent_id = self._context.agent_id if self._context else None
        # Cast to expected type - List[str] is compatible at runtime
        from typing import cast, List as TList, Union as TUnion
        from operator_composer import Primitive as _Primitive, ComposedOperator as _ComposedOperator
        ops: TList[TUnion[str, _ComposedOperator, _Primitive]] = list(primitives)  # type: ignore[assignment]
        return self.composer.compose(ops, name=name, agent_id=agent_id)
    
    def test_operator(
        self,
        operator: Union[str, ComposedOperator],
        test_frame: Optional[List[List[int]]] = None,
        expected_result: Any = None
    ) -> Tuple[bool, Any]:
        """
        Test an operator and record the result.
        
        Args:
            operator: Operator to test
            test_frame: Frame to test on (uses current frame if None)
            expected_result: Expected output for validation
            
        Returns:
            (success, actual_output)
        """
        frame = test_frame or (self._context.current_frame if self._context else None)
        
        if isinstance(operator, str):
            result = self.apply(operator, frame)
        else:
            result = self.apply(operator.operator_id, frame)
        
        success = result.success
        if success and expected_result is not None:
            success = result.output == expected_result
        
        return success, result.output
    
    def attempt_unlock(
        self,
        primitive_name: str,
        discovered_pattern: Dict[str, Any],
        test_games: List[str],
        test_results: Dict[str, bool]
    ) -> str:
        """
        Attempt to unlock a locked primitive.
        
        Args:
            primitive_name: Target primitive to unlock
            discovered_pattern: Composition tree that mimics the primitive
            test_games: Games used for testing
            test_results: {game_id: success} mapping
            
        Returns:
            attempt_id
        """
        # Calculate rates
        total = len(test_results)
        successes = sum(1 for s in test_results.values() if s)
        success_rate = successes / total if total > 0 else 0.0
        
        # Calculate cross-game rate (unique games with success)
        games_with_success = len([g for g, s in test_results.items() if s])
        unique_games = len(set(g.split('-')[0] for g in test_games))
        cross_game_rate = games_with_success / unique_games if unique_games > 0 else 0.0
        
        # Record attempt
        attempt_id = self.unlock_manager.record_unlock_attempt(
            primitive_name=primitive_name,
            discovered_pattern=discovered_pattern,
            game_ids_tested=test_games,
            success_rate=success_rate,
            cross_game_success_rate=cross_game_rate,
            agent_id=self._context.agent_id if self._context else None,
            generation=self._context.generation if self._context else 0
        )
        
        # Get oracle verdict
        decision = self.oracle.evaluate_unlock_attempt(attempt_id)
        
        logger.info(f"[CODS] Unlock attempt for '{primitive_name}': "
                   f"{decision.verdict.value} (confidence={decision.confidence:.2f})")
        
        return attempt_id
    
    def discover_novel_operator(
        self,
        composition: List[str],
        validation_games: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Discover a novel operator through composition.
        
        Validates the composition and, if successful, records it
        as a novel primitive or triggers unlock if similar to locked.
        
        Args:
            composition: List of primitives to compose
            validation_games: Games to validate on
            
        Returns:
            operator_id if successful, None otherwise
        """
        # Create the composition
        operator = self.compose_operator(composition)
        
        # Test on available frames
        if self._context and self._context.current_frame:
            success, output = self.test_operator(operator, self._context.current_frame)
            
            # Record test
            self._record_test_result(
                operator.operator_id,
                success=success,
                output=output,
                exec_time=0.0
            )
            
            if success:
                logger.info(f"[CODS] Novel operator discovered: {operator.name}")
                return operator.operator_id
        
        return None
    
    def bootstrap_operators_from_patterns(self, limit: int = 10) -> int:
        """
        Bootstrap initial operators from successful game patterns.
        
        Creates operators from seed primitives AND grandfathered primitives based on 
        common patterns found in winning sequences. This seeds the CODS system so
        evolve_operators and check_for_potential_unlocks have something to work with.
        
        CRITICAL: Operators must be executable! Each primitive in a chain must
        be able to accept the output of the previous one. Single-primitive
        operators are always valid. Multi-primitive operators must have
        compatible type signatures.
        
        CRITICAL v2: We must bootstrap operators that actually try to discover
        higher-level concepts like containment, boundary detection, etc.
        The grandfathered primitives (flood_fill, detect_shapes, etc.) should
        be composed into operators that could match locked primitives.
        
        Args:
            limit: Maximum number of operators to create
            
        Returns:
            Number of operators created
        """
        created_count = 0
        
        # Check if we already have operators (but not too many - allow gradual expansion)
        existing = self.db.execute_query("SELECT COUNT(*) as cnt FROM composed_operators")
        if existing and existing[0]['cnt'] >= 30:
            logger.debug(f"[CODS] Already have {existing[0]['cnt']} operators, skipping bootstrap")
            return 0
        
        # Get list of already created operator names
        existing_names = self.db.execute_query("SELECT name FROM composed_operators")
        existing_name_set = {r['name'] for r in existing_names} if existing_names else set()
        
        # Define ACTUALLY EXECUTABLE operator patterns
        # 
        # Type 1: Single-primitive wrappers (always work)
        # Type 2: Compositions where output feeds correctly to next input
        # Type 3: Operators using grandfathered primitives (for discovery!)
        #
        # Format: (primitives, name, description, uses_grandfathered)
        operator_patterns = [
            # === Single-primitive wrappers (guaranteed to work) ===
            (['get_frame'], 'op_get_frame', 'Get current frame state', False),
            (['get_previous_frame'], 'op_get_previous_frame', 'Get previous frame', False),
            (['get_action_history'], 'op_get_action_history', 'Get action history list', False),
            (['get_step_index'], 'op_get_step_index', 'Get current step index', False),
            (['get_action_count'], 'op_action_count', 'Get total action count', False),
            (['random_choice'], 'op_random_action', 'Choose random action', False),
            
            # === Frame size analysis (get_frame -> len = height) ===
            (['get_frame', 'len'], 'op_frame_height', 'Get frame height (rows)', False),
            
            # === Action history analysis ===
            (['get_action_history', 'len'], 'op_history_length', 'Count actions in history', False),
            (['get_last_action'], 'op_last_action', 'Get the last action taken', False),
            
            # === Random number generator ===
            (['random_float'], 'op_random_float', 'Generate random 0.0-1.0', False),
            
            # ===================================================================
            # GRANDFATHERED PRIMITIVE WRAPPERS - Critical for discovery!
            # These primitives are already unlocked and should be composed
            # into operators that could potentially discover locked primitives
            # ===================================================================
            
            # Visual analysis operators (single-primitive wrappers)
            # These read from context and work with no extra arguments
            (['detect_symmetry'], 'op_detect_symmetry', 'Detect symmetry in current frame', True),
            (['detect_shapes'], 'op_detect_shapes', 'Detect distinct shapes/objects', True),
            (['find_repeating_patterns'], 'op_find_patterns', 'Find repeating patterns in frame', True),
            (['analyze_color_distribution'], 'op_color_distribution', 'Analyze color distribution', True),
            (['analyze_spatial_relations'], 'op_spatial_relations', 'Analyze spatial relationships', True),
            
            # NOTE: detect_objects_in_frame and flood_fill are excluded because they
            # require special arguments that can't be auto-provided in this context.
            # They should be composed into higher-level operators that provide args.
            
            # These operators are designed to discover containment-like behavior
            # When they succeed consistently, they may unlock locked primitives
        ]
        
        for primitives, name, description, uses_grandfathered in operator_patterns:
            if created_count >= limit:
                break
            
            # Skip if already exists
            if name in existing_name_set:
                continue
            
            # Check if primitives are available
            all_available = True
            for p in primitives:
                # Check seed primitives first
                if self.seeds.get(p) is not None:
                    continue
                # Then check grandfathered primitives
                status = self.unlock_manager.get_status(p)
                if status in [PrimitiveStatus.UNLOCKED, PrimitiveStatus.GRANDFATHERED]:
                    continue
                all_available = False
                break
            
            if not all_available:
                logger.debug(f"[CODS] Bootstrap: Missing primitive in {primitives}")
                continue
            
            try:
                # Create the composed operator
                ops: List[Any] = list(primitives)
                operator = self.composer.compose(
                    ops,
                    name=name
                )
                
                if operator:
                    created_count += 1
                    logger.info(f"[CODS] Bootstrap: Created operator '{name}' from {primitives}")
            except Exception as e:
                logger.debug(f"[CODS] Bootstrap failed for {name}: {e}")
        
        if created_count > 0:
            logger.info(f"[CODS] Bootstrap complete: Created {created_count} initial operators")
        
        return created_count

    # ======================================================================
    # EVOLUTION & OPTIMIZATION
    # ======================================================================
    
    def evolve_operators(
        self,
        n_generations: int = 1,
        population_size: int = 10
    ) -> List[ComposedOperator]:
        """
        Evolve operators through remix and selection.
        
        Args:
            n_generations: Number of evolution generations
            population_size: Number of operators per generation
            
        Returns:
            List of evolved operators
        """
        evolved = []
        
        # Get best current operators
        population = self.composer.get_best_operators(population_size)
        
        for gen in range(n_generations):
            new_population = []
            
            for op in population:
                # Generate variants through remix
                variant = self.composer.remix(op, remix_type="random")
                if variant:
                    new_population.append(variant)
                
                # Also try simplification
                if op.successes >= 100:
                    simplified = self.composer.remix(op, remix_type="simplify")
                    if simplified:
                        new_population.append(simplified)
            
            # Add new variants to population
            population.extend(new_population)
            
            # Keep best operators
            population = sorted(
                population,
                key=lambda x: x.success_rate,
                reverse=True
            )[:population_size]
            
            evolved.extend(new_population)
            
            logger.debug(f"[CODS] Evolution gen {gen+1}: {len(new_population)} new variants")
        
        return evolved
    
    def prune_operators(
        self,
        min_success_rate: float = 0.3,
        min_tests: int = 10
    ) -> int:
        """
        Prune poorly performing operators.
        
        Args:
            min_success_rate: Minimum success rate to keep
            min_tests: Minimum tests required before pruning
            
        Returns:
            Number of operators pruned
        """
        pruned = self.db.execute_query("""
            UPDATE composed_operators
            SET status = 'pruned'
            WHERE times_tested >= ?
            AND success_rate < ?
            AND status NOT IN ('canonical', 'solid')
        """, (min_tests, min_success_rate))
        
        count = self.db.execute_query("""
            SELECT COUNT(*) as cnt FROM composed_operators WHERE status = 'pruned'
        """)
        
        pruned_count = count[0]['cnt'] if count else 0
        logger.info(f"[CODS] Pruned {pruned_count} underperforming operators")
        
        return pruned_count
    
    # ======================================================================
    # OPERATOR SURVIVAL & COMPETITION SYSTEM
    # ======================================================================
    # Operators must fight to survive like viral packages and pariahs.
    # Good operators get promoted, bad operators die.
    # ======================================================================
    
    def run_operator_lifecycle(self) -> Dict[str, Any]:
        """
        Run the full operator lifecycle: promote, demote, and kill operators.
        
        Called periodically (e.g., every generation) to apply evolutionary pressure.
        
        Returns:
            Summary of lifecycle actions taken
        """
        results = {
            'promoted': 0,
            'demoted': 0,
            'killed': 0,
            'spared': 0
        }
        
        try:
            # 1. Promote strong operators to canonical
            results['promoted'] = self._promote_strong_operators()
            
            # 2. Kill weak operators (not just prune - actually delete)
            results['killed'] = self._kill_weak_operators()
            
            # 3. Track competition stats
            self._update_competition_rankings()
            
            logger.info(f"[CODS] Operator lifecycle: {results['promoted']} promoted, "
                       f"{results['killed']} killed")
            
        except Exception as e:
            logger.error(f"[CODS] Operator lifecycle error: {e}")
            results['error'] = str(e)
        
        return results
    
    def _promote_strong_operators(
        self,
        min_success_rate: float = 0.9,
        min_tests: int = 10,
        min_games: int = 2
    ) -> int:
        """
        Promote operators that consistently succeed to 'canonical' status.
        
        Canonical operators are:
        - Protected from pruning/killing
        - Prioritized in operator selection
        - Shared network-wide as validated solutions
        """
        try:
            # Find operators that deserve promotion
            candidates = self.db.execute_query("""
                SELECT operator_id, name, success_rate, times_tested, games_tested_on
                FROM composed_operators
                WHERE status = 'tested'
                  AND success_rate >= ?
                  AND times_tested >= ?
            """, (min_success_rate, min_tests))
            
            promoted = 0
            for op in (candidates or []):
                # Check game diversity (tested on multiple games)
                games = op['games_tested_on'] or ''
                unique_games = len(set(g for g in games.split(',') if g.strip('"')))
                
                if unique_games >= min_games:
                    self.db.execute_query("""
                        UPDATE composed_operators
                        SET status = 'canonical'
                        WHERE operator_id = ?
                    """, (op['operator_id'],))
                    promoted += 1
                    logger.info(f"[CODS] Promoted operator to canonical: {op['name']} "
                               f"(rate={op['success_rate']:.2f}, tests={op['times_tested']})")
            
            return promoted
            
        except Exception as e:
            logger.error(f"[CODS] Error promoting operators: {e}")
            return 0
    
    def _kill_weak_operators(
        self,
        max_failure_rate: float = 0.9,
        min_tests: int = 5,
        kill_old_unused: bool = True,
        unused_days: int = 14
    ) -> int:
        """
        Permanently DELETE operators that consistently fail.
        
        Unlike pruning (status change), this removes them from the database.
        Dead operators free up space for new experiments.
        
        Note: Thresholds are aggressive - operators must prove value quickly
        or be replaced by better alternatives.
        """
        killed = 0
        
        try:
            # Temporarily disable foreign keys for batch deletion
            self.db.execute_query("PRAGMA foreign_keys=OFF")
            
            # Kill high-failure operators (success_rate < 10% after 5+ tests)
            failures = self.db.execute_query("""
                SELECT operator_id, name, success_rate, times_tested
                FROM composed_operators
                WHERE status NOT IN ('canonical', 'solid')
                  AND times_tested >= ?
                  AND success_rate < ?
            """, (min_tests, 1 - max_failure_rate))
            
            for op in (failures or []):
                op_id = op['operator_id']
                op_name = op['name']
                
                # Delete from ALL referencing tables FIRST (foreign key order)
                self.db.execute_query("""
                    DELETE FROM operator_test_results WHERE operator_id = ?
                """, (op_id,))
                self.db.execute_query("""
                    DELETE FROM concept_operator_map WHERE operator_id = ?
                """, (op_id,))
                self.db.execute_query("""
                    DELETE FROM gametype_primitive_theory WHERE primitive_or_operator = ?
                """, (op_name,))
                # Now delete the operator itself
                self.db.execute_query("""
                    DELETE FROM composed_operators WHERE operator_id = ?
                """, (op_id,))
                killed += 1
                logger.debug(f"[CODS] Killed failing operator: {op_name} "
                           f"(rate={op['success_rate']:.2f})")
            
            # Kill old unused operators (stale ideas that never caught on)
            if kill_old_unused:
                old_unused = self.db.execute_query("""
                    SELECT operator_id, name, times_tested
                    FROM composed_operators
                    WHERE status NOT IN ('canonical', 'solid')
                      AND times_tested < 3
                      AND created_at < datetime('now', ? || ' days')
                """, (f"-{unused_days}",))
                
                for op in (old_unused or []):
                    op_id = op['operator_id']
                    op_name = op['name']
                    
                    # Delete from ALL referencing tables FIRST
                    self.db.execute_query("""
                        DELETE FROM operator_test_results WHERE operator_id = ?
                    """, (op_id,))
                    self.db.execute_query("""
                        DELETE FROM concept_operator_map WHERE operator_id = ?
                    """, (op_id,))
                    self.db.execute_query("""
                        DELETE FROM gametype_primitive_theory WHERE primitive_or_operator = ?
                    """, (op_name,))
                    self.db.execute_query("""
                        DELETE FROM composed_operators WHERE operator_id = ?
                    """, (op_id,))
                    killed += 1
                    logger.debug(f"[CODS] Killed unused operator: {op_name}")
            
            # Re-enable foreign keys
            self.db.execute_query("PRAGMA foreign_keys=ON")
            return killed
            
        except Exception as e:
            # Re-enable foreign keys even on error
            try:
                self.db.execute_query("PRAGMA foreign_keys=ON")
            except:
                pass
            logger.error(f"[CODS] Error killing operators: {e}")
            return killed  # Return what we killed so far
    
    def _update_competition_rankings(self) -> None:
        """
        Update competition stats between operators targeting similar goals.
        
        Operators that solve the same problem compete for survival.
        The winner gets used more, the loser eventually dies.
        
        CRITICAL: Uses weighted_competition_score, NOT raw success_rate!
        This ensures frontier performance matters more than replay grinding.
        """
        try:
            # Group operators by their composition type and find competitors
            # Use weighted_competition_score for ranking (frontier-weighted)
            operators = self.db.execute_query("""
                SELECT operator_id, name, composition_type, 
                       success_rate, times_tested,
                       COALESCE(weighted_competition_score, success_rate) as competition_score,
                       COALESCE(frontier_tests, 0) as frontier_tests
                FROM composed_operators
                WHERE status NOT IN ('pruned')
                  AND times_tested >= 5
                ORDER BY composition_type, competition_score DESC
            """)
            
            if not operators:
                return
            
            # Group by composition type
            by_type = {}
            for op in operators:
                comp_type = op['composition_type'] or 'unknown'
                if comp_type not in by_type:
                    by_type[comp_type] = []
                by_type[comp_type].append(op)
            
            # Within each type, mark competition
            for comp_type, ops in by_type.items():
                if len(ops) < 2:
                    continue
                
                # Best performer vs rest (based on weighted_competition_score)
                best = ops[0]
                for competitor in ops[1:]:
                    best_score = best.get('competition_score', 0) or 0
                    comp_score = competitor.get('competition_score', 0) or 0
                    
                    # Require meaningful difference (10% gap)
                    if best_score > comp_score + 0.1:
                        # Best wins - but weight by frontier experience
                        # Operators with frontier experience earn more decisive wins
                        frontier_bonus = 1 + min(best.get('frontier_tests', 0) or 0, 10) * 0.1
                        
                        self.db.execute_query("""
                            UPDATE composed_operators
                            SET wins_vs_primitive = wins_vs_primitive + ?
                            WHERE operator_id = ?
                        """, (int(frontier_bonus), best['operator_id']))
                        self.db.execute_query("""
                            UPDATE composed_operators
                            SET losses_vs_primitive = losses_vs_primitive + 1
                            WHERE operator_id = ?
                        """, (competitor['operator_id'],))
            
        except Exception as e:
            logger.error(f"[CODS] Error updating competition rankings: {e}")
    
    def get_operator_survival_stats(self) -> Dict[str, Any]:
        """Get statistics on operator population and survival."""
        try:
            stats = {}
            
            # Population by status
            status_counts = self.db.execute_query("""
                SELECT status, COUNT(*) as count
                FROM composed_operators
                GROUP BY status
            """)
            stats['by_status'] = {r['status']: r['count'] for r in (status_counts or [])}
            
            # Success rate distribution
            rate_dist = self.db.execute_query("""
                SELECT 
                    CASE 
                        WHEN success_rate >= 0.8 THEN 'excellent'
                        WHEN success_rate >= 0.5 THEN 'good'
                        WHEN success_rate >= 0.3 THEN 'poor'
                        ELSE 'failing'
                    END as tier,
                    COUNT(*) as count
                FROM composed_operators
                WHERE times_tested >= 5
                GROUP BY tier
            """)
            stats['by_performance'] = {r['tier']: r['count'] for r in (rate_dist or [])}
            
            # Competition leaders (by weighted_competition_score, not raw success)
            leaders = self.db.execute_query("""
                SELECT name, wins_vs_primitive, losses_vs_primitive, success_rate,
                       COALESCE(frontier_tests, 0) as frontier_tests,
                       COALESCE(frontier_successes, 0) as frontier_successes,
                       COALESCE(weighted_competition_score, 0) as weighted_score
                FROM composed_operators
                WHERE wins_vs_primitive > 0
                ORDER BY weighted_competition_score DESC, wins_vs_primitive DESC
                LIMIT 10
            """)
            stats['competition_leaders'] = [dict(r) for r in (leaders or [])]
            
            # At-risk (likely to die next lifecycle - matches _kill_weak_operators thresholds)
            at_risk = self.db.execute_query("""
                SELECT COUNT(*) as count
                FROM composed_operators
                WHERE status NOT IN ('canonical', 'solid')
                  AND times_tested >= 5
                  AND success_rate < 0.1
            """)
            stats['at_risk'] = at_risk[0]['count'] if at_risk else 0
            
            # Frontier-specific stats (the REAL measure of value)
            frontier_stats = self.db.execute_query("""
                SELECT 
                    COUNT(*) as operators_with_frontier_experience,
                    SUM(COALESCE(frontier_tests, 0)) as total_frontier_tests,
                    SUM(COALESCE(frontier_successes, 0)) as total_frontier_successes,
                    AVG(CASE WHEN COALESCE(frontier_tests, 0) > 0 
                        THEN CAST(frontier_successes AS REAL) / frontier_tests 
                        ELSE NULL END) as avg_frontier_success_rate
                FROM composed_operators
                WHERE COALESCE(frontier_tests, 0) > 0
            """)
            if frontier_stats and frontier_stats[0]:
                stats['frontier'] = {
                    'operators': frontier_stats[0]['operators_with_frontier_experience'] or 0,
                    'total_tests': frontier_stats[0]['total_frontier_tests'] or 0,
                    'total_successes': frontier_stats[0]['total_frontier_successes'] or 0,
                    'avg_success_rate': round(frontier_stats[0]['avg_frontier_success_rate'] or 0, 3)
                }
            else:
                stats['frontier'] = {'operators': 0, 'total_tests': 0, 'total_successes': 0, 'avg_success_rate': 0}
            
            return stats
            
        except Exception as e:
            logger.error(f"[CODS] Error getting survival stats: {e}")
            return {'error': str(e)}

    # ======================================================================
    # COMPOSED OPERATOR TESTING
    # ======================================================================
    
    def test_composed_operators(
        self,
        frame: Optional[List[List[int]]] = None,
        previous_frame: Optional[List[List[int]]] = None,
        score_delta: float = 0.0,
        operator_ids: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        Test all cobbled/solid composed operators on the current frame.
        
        This is CRITICAL for the unlock system - operators must be tested
        to accumulate success/failure data for unlock evaluation.
        
        Args:
            frame: Current frame
            previous_frame: Previous frame (for delta operators)
            score_delta: Change in score (for success evaluation)
            operator_ids: Optional list of specific operator IDs/names to test
            
        Returns:
            Dict of {operator_name: success}
        """
        frame = frame or (self._context.current_frame if self._context else None)
        if not frame:
            return {}
        
        results = {}
        
        # Get operators to test
        if operator_ids:
            # Test specific operators requested
            placeholders = ','.join(['?' for _ in operator_ids])
            params = tuple(operator_ids + operator_ids)
            operators = self.db.execute_query(f"""
                SELECT operator_id, name, composition_tree, composition_type
                FROM composed_operators
                WHERE (name IN ({placeholders}) OR operator_id IN ({placeholders}))
                  AND status IN ('cobbled', 'solid', 'tested')
            """, params)
        else:
            # Get all operators that need testing (cobbled or solid, not yet canonical)
            operators = self.db.execute_query("""
                SELECT operator_id, name, composition_tree, composition_type
                FROM composed_operators
                WHERE status IN ('cobbled', 'solid')
                ORDER BY times_tested ASC
                LIMIT 10
            """)
        
        if not operators:
            return {}
        
        for op in operators:
            op_name = op['name']
            op_id = op['operator_id']
            
            try:
                # Apply the operator (no args - operators read from context set by update_frame)
                # FIXED: Previously passed frame as arg, but seed primitives like get_frame()
                # take no arguments and read from internal context
                start_time = time.time()
                result = self.apply(op_name)
                exec_time_ms = (time.time() - start_time) * 1000
                
                # Determine success based on operator execution (not score delta)
                # Score-based evaluation was marking data-access operators as failures
                # when score didn't change, which is wrong - get_frame() is always successful
                # if it returns data without error.
                # 
                # Future: For operators that suggest ACTIONS (not just data access),
                # we could evaluate based on score_delta, but that requires tracking
                # which operators influenced which actions.
                success = result.success
                
                results[op_name] = success
                
                # Record test result in operator_test_results table (CRITICAL for unlock system)
                # BUG FIX: Previously only updated composed_operators but check_for_potential_unlocks
                # queries operator_test_results for cross-game validation
                self._record_test_result(
                    operator_id=op_id,
                    success=success,
                    output=result.output,
                    exec_time=exec_time_ms
                )
                
                # Also update the composed_operators summary stats
                game_id = self._context.game_id if self._context else 'unknown'
                self.db.execute_query("""
                    UPDATE composed_operators
                    SET times_tested = times_tested + 1,
                        successes = successes + ?,
                        failures = failures + ?,
                        success_rate = CAST(successes + ? AS REAL) / CAST(times_tested + 1 AS REAL),
                        games_tested_on = COALESCE(games_tested_on, '[]') || ?,
                        last_tested_at = CURRENT_TIMESTAMP
                    WHERE operator_id = ?
                """, (
                    1 if success else 0,
                    0 if success else 1,
                    1 if success else 0,
                    f',"{game_id}"' if game_id != 'unknown' else '',
                    op_id
                ))
                
                logger.debug(f"[CODS] Tested {op_name}: {'SUCCESS' if success else 'FAIL'}" + 
                             (f" (error: {result.error})" if not success and result.error else ""))
                
            except Exception as e:
                results[op_name] = False
                logger.warning(f"[CODS] Operator {op_name} test threw exception: {e}")
        
        # FIX #6: Log warning when ALL operators fail - helps diagnose systemic issues
        if results and not any(results.values()):
            logger.warning(f"[CODS] All {len(results)} operators failed! Check operator composition or context setup")
        
        return results
    
    # ======================================================================
    # ANALYSIS & INSIGHT
    # ======================================================================
    
    def analyze_frame(
        self,
        frame: Optional[List[List[int]]] = None
    ) -> Dict[str, Any]:
        """
        Apply all available visual analysis operators to a frame.
        
        Args:
            frame: Frame to analyze (uses current if None)
            
        Returns:
            Dictionary of analysis results
        """
        frame = frame or (self._context.current_frame if self._context else None)
        if not frame:
            return {}
        
        results = {}
        
        # Apply each unlocked visual primitive
        visual_primitives = [
            'detect_symmetry', 'detect_shapes', 'find_repeating_patterns',
            'analyze_color_distribution', 'analyze_spatial_relations'
        ]
        
        for prim in visual_primitives:
            if self.unlock_manager.is_available(prim):
                result = self.apply(prim, frame)
                if result.success:
                    results[prim] = result.output
        
        # Also apply composed operators that are solid/canonical
        try:
            composed_ops = self.db.execute_query("""
                SELECT name FROM composed_operators
                WHERE status IN ('solid', 'canonical')
                AND success_rate >= 0.5
                ORDER BY success_rate DESC
                LIMIT 5
            """)
            
            for op in (composed_ops or []):
                op_name = op['name']
                result = self.apply(op_name, frame)
                if result.success:
                    results[f"composed:{op_name}"] = result.output
        except Exception as e:
            logger.debug(f"[CODS] Composed operator analysis failed: {e}")
        
        return results
    
    def suggest_action(
        self,
        frame: Optional[List[List[int]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Use cognitive operators to suggest an action.
        
        Tier 4: Uses concept discovery to find relevant operators for this game.
        
        Args:
            frame: Current frame
            
        Returns:
            Dict with 'action', 'confidence', 'operator', 'concept' or None
        """
        frame = frame or (self._context.current_frame if self._context else None)
        if not frame:
            return None
        
        game_type = self._context.game_id.split('-')[0] if self._context and self._context.game_id else None
        
        # Tier 4: Check if we have a concept that applies to this game
        if self.concept_engine and game_type:
            suggested_concept = self.concept_engine.suggest_concept_for_game(
                game_type=game_type,
                frame=frame
            )
            
            if suggested_concept:
                # Get operators organized by this concept
                relevant_ops = self.concept_engine.get_relevant_operators_for_concept(
                    concept_id=suggested_concept.concept_id,
                    min_relevance=0.4
                )
                
                if relevant_ops:
                    # Use the most relevant operator
                    best_op = relevant_ops[0]
                    operator_id = best_op['operator_id']
                    
                    # Try to apply the operator
                    result = self.apply(operator_id, frame)
                    
                    if result.success:
                        logger.info(
                            f"[CODS-CONCEPT] Using concept '{suggested_concept.name}' "
                            f"suggests operator '{operator_id[:8]}'"
                        )
                        
                        # Extract action from operator result if possible
                        action = self._extract_action_from_output(result.output)
                        if action:
                            return {
                                'action': action,
                                'confidence': best_op['relevance'],
                                'operator': operator_id,
                                'operators': [operator_id, suggested_concept.name],  # FIX #25: Track all operators consulted
                                'concept': suggested_concept.name
                            }
        
        # Analyze frame with available operators
        analysis = self.analyze_frame(frame)
        
        # FIX #25: Track all operators that were consulted for diversity logging
        operators_consulted = list(analysis.keys()) if analysis else []
        
        # Simple heuristic based on analysis
        # (This would be replaced by learned action selection)
        
        if 'detect_symmetry' in analysis:
            symmetry = analysis['detect_symmetry']
            if symmetry.get('horizontal'):
                return {'action': 1, 'confidence': 0.3, 'operator': 'detect_symmetry', 
                        'operators': operators_consulted, 'concept': None}
            if symmetry.get('vertical'):
                return {'action': 3, 'confidence': 0.3, 'operator': 'detect_symmetry', 
                        'operators': operators_consulted, 'concept': None}
        
        if 'detect_shapes' in analysis:
            shapes = analysis['detect_shapes']
            if shapes:
                # Move toward first detected shape
                return {'action': 1, 'confidence': 0.2, 'operator': 'detect_shapes', 
                        'operators': operators_consulted, 'concept': None}
        
        # Default to random action - still log operators consulted
        return {'action': self.seeds.call('rand_int', 1, 7), 'confidence': 0.1, 'operator': 'random', 
                'operators': operators_consulted if operators_consulted else ['random'], 'concept': None}
    
    def _extract_action_from_output(self, output: Any) -> Optional[int]:
        """Extract an action number from operator output."""
        if isinstance(output, int) and 1 <= output <= 7:
            return output
        if isinstance(output, dict):
            if 'action' in output:
                return int(output['action'])
            if 'suggested_action' in output:
                return int(output['suggested_action'])
        return None
    
    # ======================================================================
    # STATISTICS & REPORTING
    # ======================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive CODS statistics."""
        stats = {
            'seed_primitives': self.seeds.get_stats(),
            'unlock_manager': self.unlock_manager.get_unlock_stats(),
            'composer': self.composer.get_stats(),
            'oracle': self.oracle.get_oracle_stats()
        }
        
        # Tier 4: Concept discovery stats
        if self.concept_engine:
            stats['concepts'] = self.concept_engine.get_concept_stats()
        
        # Execution stats
        stats['execution'] = {
            'total_calls': sum(
                s.get('calls', 0) 
                for s in self._execution_stats.values()
            ),
            'total_successes': sum(
                s.get('successes', 0) 
                for s in self._execution_stats.values()
            ),
            'avg_execution_time_ms': sum(
                s.get('total_time', 0) 
                for s in self._execution_stats.values()
            ) / max(1, sum(s.get('calls', 0) for s in self._execution_stats.values()))
        }
        
        return stats
    
    def get_available_operators(self) -> Dict[str, List[str]]:
        """Get all available operators by category."""
        available = {
            'seed': self.seeds.list_all(),
            'unlocked': [p['primitive_name'] for p in self.unlock_manager.list_unlocked()],
            'novel': [p['discovered_name'] for p in self.unlock_manager.list_novel()],
            'composed': [
                op.name for op in self.composer.list_operators(
                    min_success_rate=0.5, limit=50
                )
            ]
        }
        
        return available
    
    def get_locked_primitives(self) -> List[Dict[str, Any]]:
        """Get all locked primitives awaiting discovery."""
        return self.unlock_manager.list_locked()
    
    # ======================================================================
    # WORLD-MODEL INTEGRATION (from agent_consciousness_synthesis.md)
    # Feed discoveries into world understanding
    # ======================================================================
    
    def has_new_discovery(self) -> bool:
        """
        Check if there's a pending discovery for world-model integration.
        
        Called by consciousness_step to check if CODS found something.
        """
        return self._latest_discovery is not None or len(self._pending_discoveries) > 0
    
    def get_latest_discovery(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent discovery for world-model update.
        
        Returns discovery with:
        - operator_name: str
        - explanation: str  
        - discovery_type: 'operator', 'primitive', 'pattern'
        - evidence: dict
        
        Clears the discovery after retrieval.
        """
        if self._latest_discovery:
            discovery = self._latest_discovery
            self._latest_discovery = None
            return discovery
        
        if self._pending_discoveries:
            return self._pending_discoveries.pop(0)
        
        return None
    
    def get_all_pending_discoveries(self) -> List[Dict[str, Any]]:
        """Get all pending discoveries and clear the queue."""
        discoveries = list(self._pending_discoveries)
        self._pending_discoveries.clear()
        if self._latest_discovery:
            discoveries.insert(0, self._latest_discovery)
            self._latest_discovery = None
        return discoveries
    
    def record_discovery(
        self,
        operator_name: str,
        explanation: str,
        discovery_type: str = 'operator',
        evidence: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record a new discovery for world-model integration.
        
        Called when CODS validates a new operator or unlocks a primitive.
        """
        discovery = {
            'operator_name': operator_name,
            'explanation': explanation,
            'discovery_type': discovery_type,
            'evidence': evidence or {},
            'discovered_at_step': self._context.step_idx if self._context else 0,
            'game_type': self._context.game_id.split('-')[0] if self._context and self._context.game_id else 'unknown'
        }
        
        self._latest_discovery = discovery
        self._pending_discoveries.append(discovery)
        
        # Keep pending list bounded
        if len(self._pending_discoveries) > 20:
            self._pending_discoveries = self._pending_discoveries[-10:]
        
        logger.info(f"[CODS] Recorded discovery: {operator_name} ({discovery_type})")
    
    def get_operators_for_game(self, game_type: str) -> List[str]:
        """
        Get operators that have worked well for a specific game type.
        
        Uses problem-signature to operator mapping.
        """
        operators = []
        
        try:
            # Query operator success by game type
            rows = self.db.execute_query(
                """SELECT operator_name, success_count, failure_count
                   FROM operator_game_stats
                   WHERE game_type = ?
                   ORDER BY success_count DESC
                   LIMIT 10""",
                (game_type,)
            )
            if rows:
                for row in rows:
                    if row.get('success_count', 0) > row.get('failure_count', 0):
                        operators.append(row['operator_name'])
        except Exception:
            # Table might not exist - return available operators
            available = self.get_available_operators()
            operators = available.get('seed', [])[:5]
        
        return operators
    
    # ======================================================================
    # FAILURE-DRIVEN LEARNING (Post-Game Analysis)
    # ======================================================================
    
    def record_level_outcome(
        self,
        level: int,
        passed: bool,
        actions_used: int,
        score_gained: float = 0.0
    ) -> None:
        """
        Record level outcome for failure-driven learning.
        
        Called when a level completes or times out. This is a key learning
        point - we can analyze what operators were/weren't used and whether
        they might have helped.
        
        Args:
            level: Level number (1-based)
            passed: Whether level was completed
            actions_used: Number of actions taken on this level
            score_gained: Score earned on this level
        """
        if not self._context:
            logger.warning("[CODS] record_level_outcome called without context")
            return
        
        try:
            # Record level outcome
            outcome_id = str(uuid.uuid4())[:12]
            
            self.db.execute_query("""
                INSERT INTO cods_level_outcomes (
                    outcome_id, game_id, agent_id, level_number,
                    passed, actions_used, score_gained,
                    generation, recorded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                outcome_id,
                self._context.game_id,
                self._context.agent_id,
                level,
                passed,
                actions_used,
                score_gained,
                self._context.generation,
                datetime.now().isoformat()
            ))
            
            # On failure, analyze what primitives might have helped
            if not passed:
                self._analyze_level_failure(level, actions_used)
            else:
                # ==> BAYESIAN: Record success as counter-evidence
                game_type = self._context.game_id.split('-')[0] if '-' in self._context.game_id else self._context.game_id
                self.observe_success_pattern(
                    game_type=game_type,
                    level_number=level
                )
                
            logger.debug(f"[CODS] Level {level} outcome: {'PASS' if passed else 'FAIL'} "
                        f"({actions_used} actions, {score_gained} score)")
                        
        except Exception as e:
            logger.error(f"[CODS] Error recording level outcome: {e}")
    
    def record_game_outcome(
        self,
        game_id: str,
        final_score: float,
        max_level_reached: int,
        total_actions: int,
        won: bool = False
    ) -> Dict[str, Any]:
        """
        Record game outcome - MAIN LEARNING POINT.
        
        This is where we analyze the full game to understand:
        1. What operators were used and did they help?
        2. What primitives might have been missing?
        3. Are there patterns across failed games?
        
        Args:
            game_id: Game that was played
            final_score: Final score achieved
            max_level_reached: Highest level reached
            total_actions: Total actions taken
            won: Whether game was won
            
        Returns:
            Analysis results including primitive gap suggestions
        """
        if not self._context:
            logger.warning("[CODS] record_game_outcome called without context")
            return {'error': 'no_context'}
        
        results = {
            'game_id': game_id,
            'won': won,
            'max_level': max_level_reached,
            'operators_tested': 0,
            'operators_helpful': 0,
            'primitive_gaps': [],
            'concept_signals': []
        }
        
        try:
            # Get operator test results for this game
            test_results = self.db.execute_query("""
                SELECT operator_id, success, level_number
                FROM operator_test_results
                WHERE game_id = ?
                ORDER BY tested_at
            """, (game_id,))
            
            if test_results:
                results['operators_tested'] = len(test_results)
                results['operators_helpful'] = sum(1 for t in test_results if t['success'])
            
            # If game failed, analyze what was missing
            if not won:
                gaps = self._analyze_game_failure(
                    game_id, final_score, max_level_reached, total_actions
                )
                results['primitive_gaps'] = gaps
                
                # Check for recurring failure patterns
                concept_signals = self._detect_concept_signals(game_id, max_level_reached)
                results['concept_signals'] = concept_signals
            
            # Record outcome to database
            self.db.execute_query("""
                INSERT OR REPLACE INTO cods_game_outcomes (
                    game_id, agent_id, final_score, max_level_reached,
                    total_actions, won, operators_tested, operators_helpful,
                    primitive_gaps, concept_signals, generation, recorded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                game_id,
                self._context.agent_id,
                final_score,
                max_level_reached,
                total_actions,
                won,
                results['operators_tested'],
                results['operators_helpful'],
                json.dumps(results['primitive_gaps']),
                json.dumps(results['concept_signals']),
                self._context.generation,
                datetime.now().isoformat()
            ))
            
            logger.info(f"[CODS] Game outcome: {'WIN' if won else 'FAIL'} L{max_level_reached} "
                       f"- {len(results['primitive_gaps'])} primitive gaps detected")
            
            # If game was successful, record which primitives/operators contributed
            if final_score > 0:
                self._record_gametype_primitive_success(game_id, final_score, max_level_reached)
            
        except Exception as e:
            logger.error(f"[CODS] Error recording game outcome: {e}")
            results['error'] = str(e)
        
        return results
    
    def _record_gametype_primitive_success(
        self, 
        game_id: str, 
        final_score: float, 
        max_level_reached: int
    ) -> None:
        """
        Record which primitives/operators contributed to success for this game_type.
        
        Called when a game scores positive. Updates the gametype_primitive_theory table
        so the network learns which primitives work for which game types.
        """
        try:
            # Extract game_type from game_id (e.g., "sp80-xxx" -> "sp80")
            game_type = game_id.split('-')[0] if '-' in game_id else game_id
            
            # Get operators that were tested in this game
            tested_operators = self.db.execute_query("""
                SELECT DISTINCT operator_id, success
                FROM operator_test_results
                WHERE game_id = ?
            """, (game_id,))
            
            if not tested_operators:
                return
            
            updated = 0
            for op_record in tested_operators:
                operator_id = op_record['operator_id']
                was_successful = op_record['success']
                
                # Get operator details to find primitive names
                op_details = self.db.execute_query("""
                    SELECT name, composition_tree FROM composed_operators
                    WHERE operator_id = ?
                """, (operator_id,))
                
                if not op_details:
                    continue
                
                op = op_details[0]
                
                # Record the operator itself
                self._update_gametype_theory(
                    game_type, op['name'], is_operator=True,
                    was_successful=was_successful, score=final_score,
                    level=max_level_reached
                )
                updated += 1
                
                # Also record the underlying primitives
                if op['composition_tree']:
                    try:
                        tree = json.loads(op['composition_tree'])
                        primitives = self._extract_primitives_from_tree(tree)
                        for prim in primitives:
                            self._update_gametype_theory(
                                game_type, prim, is_operator=False,
                                was_successful=was_successful, score=final_score,
                                level=max_level_reached
                            )
                            updated += 1
                    except json.JSONDecodeError:
                        pass
            
            if updated > 0:
                logger.debug(f"[CODS] Updated {updated} primitive theories for {game_type}")
                
        except Exception as e:
            logger.error(f"[CODS] Error recording gametype primitive success: {e}")
    
    def _update_gametype_theory(
        self,
        game_type: str,
        primitive_or_operator: str,
        is_operator: bool,
        was_successful: bool,
        score: float,
        level: int
    ) -> None:
        """Update a single entry in the gametype_primitive_theory table."""
        try:
            theory_id = f"{game_type}_{primitive_or_operator}"
            
            # Check if exists
            existing = self.db.execute_query("""
                SELECT times_used, times_successful, total_score_contribution, levels_effective
                FROM gametype_primitive_theory
                WHERE theory_id = ?
            """, (theory_id,))
            
            if existing:
                record = existing[0]
                new_times_used = record['times_used'] + 1
                new_times_successful = record['times_successful'] + (1 if was_successful else 0)
                new_score_contribution = record['total_score_contribution'] + (score if was_successful else 0)
                new_success_rate = new_times_successful / new_times_used if new_times_used > 0 else 0
                
                # Update levels_effective
                levels = json.loads(record['levels_effective']) if record['levels_effective'] else []
                if was_successful and level not in levels:
                    levels.append(level)
                
                self.db.execute_query("""
                    UPDATE gametype_primitive_theory
                    SET times_used = ?,
                        times_successful = ?,
                        success_rate = ?,
                        total_score_contribution = ?,
                        levels_effective = ?,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE theory_id = ?
                """, (new_times_used, new_times_successful, new_success_rate,
                      new_score_contribution, json.dumps(levels), theory_id))
            else:
                # Insert new
                self.db.execute_query("""
                    INSERT INTO gametype_primitive_theory (
                        theory_id, game_type, primitive_or_operator, is_operator,
                        times_used, times_successful, success_rate, total_score_contribution,
                        levels_effective
                    ) VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?)
                """, (
                    theory_id, game_type, primitive_or_operator, is_operator,
                    1 if was_successful else 0,
                    1.0 if was_successful else 0.0,
                    score if was_successful else 0,
                    json.dumps([level]) if was_successful else '[]'
                ))
                
        except Exception as e:
            logger.error(f"[CODS] Error updating gametype theory: {e}")
    
    def get_recommended_primitives_for_gametype(
        self, 
        game_type: str, 
        limit: int = 10,
        min_success_rate: float = 0.5,
        min_uses: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Get the best primitives/operators for a game_type based on network experience.
        
        Called when an agent starts a game to know which primitives to prioritize.
        
        Args:
            game_type: The game type (e.g., 'sp80', 'ft09')
            limit: Maximum number of recommendations
            min_success_rate: Minimum success rate to include
            min_uses: Minimum times_used to include (higher = more confident)
            
        Returns:
            List of recommended primitives/operators with their stats
        """
        try:
            results = self.db.execute_query("""
                SELECT 
                    primitive_or_operator,
                    is_operator,
                    times_used,
                    times_successful,
                    success_rate,
                    total_score_contribution,
                    levels_effective,
                    network_confidence
                FROM gametype_primitive_theory
                WHERE game_type = ?
                  AND success_rate >= ?
                  AND times_used >= ?
                ORDER BY success_rate DESC, times_successful DESC
                LIMIT ?
            """, (game_type, min_success_rate, min_uses, limit))
            
            if not results:
                # Return general high-performing primitives if no game-specific data
                return self._get_general_primitive_recommendations(limit)
            
            recommendations = []
            for r in results:
                recommendations.append({
                    'name': r['primitive_or_operator'],
                    'is_operator': r['is_operator'],
                    'success_rate': r['success_rate'],
                    'times_used': r['times_used'],
                    'score_contribution': r['total_score_contribution'],
                    'effective_levels': json.loads(r['levels_effective']) if r['levels_effective'] else [],
                    'confidence': r['network_confidence']
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"[CODS] Error getting recommended primitives: {e}")
            return []
    
    def _get_general_primitive_recommendations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get generally useful primitives when no game-specific data exists."""
        try:
            results = self.db.execute_query("""
                SELECT 
                    primitive_or_operator,
                    is_operator,
                    SUM(times_used) as total_uses,
                    SUM(times_successful) as total_successes,
                    AVG(success_rate) as avg_success_rate
                FROM gametype_primitive_theory
                WHERE times_used >= 5
                GROUP BY primitive_or_operator, is_operator
                HAVING avg_success_rate >= 0.5
                ORDER BY avg_success_rate DESC, total_uses DESC
                LIMIT ?
            """, (limit,))
            
            return [{
                'name': r['primitive_or_operator'],
                'is_operator': r['is_operator'],
                'success_rate': r['avg_success_rate'],
                'times_used': r['total_uses'],
                'score_contribution': 0,
                'effective_levels': [],
                'confidence': 0.5
            } for r in results] if results else []
            
        except Exception as e:
            logger.error(f"[CODS] Error getting general primitive recommendations: {e}")
            return []

    def _analyze_level_failure(self, level: int, actions_used: int) -> None:
        """Analyze a level failure to identify primitive gaps."""
        if not self._context:
            return
        
        # Get frame characteristics at failure point
        frame = self._context.current_frame
        if not frame:
            return
        
        # Run available operators on the failed frame to see what insights we get
        operators = self.composer.list_operators(min_success_rate=0.3, limit=20)
        
        insights = []
        for op in operators:
            try:
                result = self.apply(op.operator_id)
                if result.success and result.output:
                    insights.append({
                        'operator': op.name,
                        'output': str(result.output)[:100]  # Truncate for storage
                    })
            except Exception:
                pass
        
        # Store failure analysis
        if insights:
            self.db.execute_query("""
                INSERT INTO cods_failure_analyses (
                    analysis_id, game_id, level_number, agent_id,
                    actions_at_failure, operator_insights, generation, analyzed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4())[:12],
                self._context.game_id,
                level,
                self._context.agent_id,
                actions_used,
                json.dumps(insights),
                self._context.generation,
                datetime.now().isoformat()
            ))
        
        # ==> BAYESIAN: Record failure pattern for hypothesis tracking
        game_type = self._context.game_id.split('-')[0] if '-' in self._context.game_id else self._context.game_id
        failure_pattern = f"level_failure_at_L{level}"
        
        # Look for specific patterns from insights
        if insights:
            pattern_keywords = ['boundary', 'overflow', 'stuck', 'loop', 'collision']
            for insight in insights:
                output_lower = insight.get('output', '').lower()
                for keyword in pattern_keywords:
                    if keyword in output_lower:
                        failure_pattern = f"{keyword}_pattern_L{level}"
                        break
        
        self.observe_failure_pattern(
            game_type=game_type,
            level_number=level,
            failure_pattern=failure_pattern
        )
    
    def _analyze_game_failure(
        self,
        game_id: str,
        final_score: float,
        max_level: int,
        total_actions: int
    ) -> List[Dict[str, Any]]:
        """
        Analyze a failed game to identify potential primitive gaps.
        
        Returns list of primitive gaps with confidence scores.
        """
        gaps = []
        
        # Get game type from game_id (e.g., "sp80" from "sp80-abc123")
        game_type = game_id.split('-')[0] if '-' in game_id else game_id
        
        # Check historical failures for this game type
        failure_history = self.db.execute_query("""
            SELECT COUNT(*) as fail_count, AVG(max_level_reached) as avg_level
            FROM cods_game_outcomes
            WHERE game_id LIKE ? AND won = FALSE
        """, (f"{game_type}%",))
        
        # FIXED: Lower threshold from 3 to 1 for earlier detection
        # Even a single failure can suggest primitive gaps based on frame analysis
        # NOTE: Add 1 to include THIS current failure (not yet inserted into DB)
        fail_count = (failure_history[0]['fail_count'] if failure_history else 0) + 1
        
        if fail_count >= 1:
            avg_level = failure_history[0]['avg_level'] or 1
            
            # Check which locked primitives might help
            locked = self.unlock_manager.list_locked()
            
            for prim in locked:
                # Score each primitive by relevance to this failure pattern
                relevance = self._score_primitive_relevance(
                    prim['primitive_name'], game_type, max_level
                )
                
                if relevance >= 0.3:
                    gaps.append({
                        'primitive_name': prim['primitive_name'],
                        'category': prim.get('category', 'unknown'),
                        'relevance_score': relevance,
                        'failure_pattern': f"{game_type}_level{max_level}",
                        'suggested_reason': self._get_unlock_reason(
                            prim['primitive_name'], game_type
                        )
                    })
                    
                    # ==> BAYESIAN: Create hypothesis for each gap
                    self.observe_failure_pattern(
                        game_type=game_type,
                        level_number=max_level,
                        failure_pattern=f"gap_{prim['primitive_name']}",
                        suggested_primitive=prim['primitive_name']
                    )
        
        # Sort by relevance
        gaps.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return gaps[:5]  # Top 5 gaps
    
    def _score_primitive_relevance(
        self,
        primitive_name: str,
        game_type: str,
        failed_level: int
    ) -> float:
        """Score how relevant a locked primitive might be for a failure pattern."""
        score = 0.0
        prim_lower = primitive_name.lower()
        
        # Containment-related primitives for games with boundary patterns
        containment_prims = ['containment_check', 'boundary_seal_check', 'flow_simulation',
                           'is_enclosed', 'capacity_estimate', 'overflow_predict']
        
        # Reference/template primitives for pattern-matching games
        reference_prims = ['identify_reference_object', 'extract_schema', 'apply_template',
                          'create_variable_mapping', 'detect_legend_object']
        
        # Spatial primitives for navigation games
        spatial_prims = ['path_exists', 'distance_transform', 'detect_edges',
                        'motion_vector', 'gravity_simulation']
        
        # Check if primitive category matches game patterns
        # (This is a heuristic - real matching would analyze frames)
        if any(p in prim_lower for p in ['contain', 'bound', 'seal', 'flow', 'enclos']):
            score += 0.4
        
        if any(p in prim_lower for p in ['path', 'distance', 'motion', 'gravity']):
            score += 0.3
        
        if any(p in prim_lower for p in ['reference', 'schema', 'template', 'mapping']):
            score += 0.3
        
        # Higher relevance for level 2+ failures (level 1 usually has simpler mechanics)
        if failed_level >= 2:
            score += 0.2
        
        return min(1.0, score)
    
    def _get_unlock_reason(self, primitive_name: str, game_type: str) -> str:
        """Get a human-readable reason for why this primitive might help."""
        reasons = {
            'containment_check': 'Detect if regions are fully bounded/sealed',
            'boundary_seal_check': 'Verify all edges of containers are blocked',
            'flow_simulation': 'Predict where dynamic content will flow',
            'is_enclosed': 'Check if a region is completely surrounded',
            'path_exists': 'Find if there is a valid path between points',
            'detect_edges': 'Find boundaries between different regions',
            'identify_reference_object': 'Detect objects that define rules for others',
            'extract_schema': 'Get abstract pattern independent of specific values',
        }
        return reasons.get(primitive_name, f'May help with {game_type} patterns')
    
    def _detect_concept_signals(
        self,
        game_id: str,
        max_level: int
    ) -> List[Dict[str, Any]]:
        """
        Detect signals that a higher-level concept might be needed.
        
        Concepts are semantic models that organize which operators are relevant.
        """
        signals = []
        game_type = game_id.split('-')[0] if '-' in game_id else game_id
        
        # Check if multiple primitives from same category would help
        gaps = self._analyze_game_failure(game_id, 0, max_level, 0)
        
        if gaps:
            # Group by category
            categories = {}
            for gap in gaps:
                cat = gap.get('category', 'unknown')
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(gap['primitive_name'])
            
            # If 2+ primitives from same category, it's a concept signal
            for cat, prims in categories.items():
                if len(prims) >= 2:
                    signals.append({
                        'concept_type': cat,
                        'related_primitives': prims,
                        'confidence': min(0.9, 0.3 * len(prims)),
                        'game_type': game_type,
                        'level': max_level
                    })
        
        return signals
    
    def process_counterfactual_insights(
        self,
        scenario_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Process counterfactual analysis results to inform CODS.
        
        Connects the CounterfactualAnalyzer output to primitive gap detection.
        
        Args:
            scenario_ids: IDs from counterfactual_scenarios table
            
        Returns:
            Processing results
        """
        results = {
            'scenarios_processed': 0,
            'operator_hypotheses': [],
            'primitive_hints': []
        }
        
        if not scenario_ids:
            return results
        
        try:
            # Get counterfactual scenarios
            placeholders = ','.join('?' * len(scenario_ids))
            scenarios = self.db.execute_query(f"""
                SELECT scenario_id, game_id, decision_point_index,
                       divergence_reason, predicted_outcome, learning_value
                FROM counterfactual_scenarios
                WHERE scenario_id IN ({placeholders})
                ORDER BY learning_value DESC
            """, tuple(scenario_ids))
            
            for scenario in scenarios:
                results['scenarios_processed'] += 1
                
                # High-value counterfactuals suggest we need better decision-making
                if scenario['learning_value'] >= 0.7:
                    game_type = scenario['game_id'].split('-')[0]
                    
                    # Record as a signal that we need better primitives for this game
                    self.db.execute_query("""
                        INSERT INTO cods_primitive_hints (
                            hint_id, game_type, source, hint_type,
                            confidence, details, recorded_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(uuid.uuid4())[:12],
                        game_type,
                        'counterfactual',
                        'decision_point',
                        scenario['learning_value'],
                        json.dumps({
                            'scenario_id': scenario['scenario_id'],
                            'reason': scenario['divergence_reason']
                        }),
                        datetime.now().isoformat()
                    ))
                    
                    results['primitive_hints'].append({
                        'game_type': game_type,
                        'hint': scenario['divergence_reason'][:100]
                    })
            
            logger.info(f"[CODS] Processed {results['scenarios_processed']} counterfactual scenarios")
            
        except Exception as e:
            logger.error(f"[CODS] Error processing counterfactuals: {e}")
            results['error'] = str(e)
        
        return results
    
    def process_near_miss_patterns(
        self,
        near_miss_id: str
    ) -> Dict[str, Any]:
        """
        Process near-miss analysis to inform CODS.
        
        Near-misses (15-18/20 scores) are especially valuable because
        they show what ALMOST worked - small gaps in understanding.
        
        Args:
            near_miss_id: ID from near_miss_games table
            
        Returns:
            Processing results
        """
        results = {
            'processed': False,
            'gap_identified': None,
            'suggested_primitive': None
        }
        
        try:
            # Get near-miss details
            near_miss = self.db.execute_query("""
                SELECT game_id, final_score, score_gap, near_miss_category,
                       what_failed, missing_elements
                FROM near_miss_games
                WHERE near_miss_id = ?
            """, (near_miss_id,))
            
            if not near_miss:
                return results
            
            nm = near_miss[0]
            results['processed'] = True
            
            game_type = nm['game_id'].split('-')[0]
            
            # Parse what failed
            what_failed = json.loads(nm['what_failed']) if nm['what_failed'] else []
            missing = json.loads(nm['missing_elements']) if nm['missing_elements'] else []
            
            # Near-misses suggest specific primitive gaps
            if nm['score_gap'] <= 3:  # Very close to winning
                # Check which locked primitives might close this gap
                locked = self.unlock_manager.list_locked()
                
                for prim in locked:
                    relevance = self._score_primitive_relevance(
                        prim['primitive_name'], game_type, 2
                    )
                    
                    if relevance >= 0.5:
                        results['gap_identified'] = f"Near-win on {game_type}"
                        results['suggested_primitive'] = prim['primitive_name']
                        
                        # Record as high-confidence hint
                        self.db.execute_query("""
                            INSERT INTO cods_primitive_hints (
                                hint_id, game_type, source, hint_type,
                                confidence, details, recorded_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            str(uuid.uuid4())[:12],
                            game_type,
                            'near_miss',
                            'almost_won',
                            0.8,  # High confidence for near-wins
                            json.dumps({
                                'near_miss_id': near_miss_id,
                                'score_gap': nm['score_gap'],
                                'suggested': prim['primitive_name']
                            }),
                            datetime.now().isoformat()
                        ))
                        break
            
            logger.info(f"[CODS] Processed near-miss {near_miss_id}: gap={results['gap_identified']}")
            
        except Exception as e:
            logger.error(f"[CODS] Error processing near-miss: {e}")
            results['error'] = str(e)
        
        return results
    
    def get_primitive_gap_summary(self, min_confidence: float = 0.5) -> Dict[str, Any]:
        """
        Get summary of detected primitive gaps across all games.
        
        This is the main interface for understanding what primitives
        the system needs to discover/unlock.
        
        Args:
            min_confidence: Minimum confidence threshold
            
        Returns:
            Summary of gaps by game type and primitive
        """
        summary = {
            'total_hints': 0,
            'by_game_type': {},
            'by_primitive': {},
            'top_suggestions': []
        }
        
        try:
            # Get all hints above threshold
            hints = self.db.execute_query("""
                SELECT game_type, hint_type, confidence, details
                FROM cods_primitive_hints
                WHERE confidence >= ?
                ORDER BY confidence DESC
            """, (min_confidence,))
            
            if not hints:
                return summary
            
            summary['total_hints'] = len(hints)
            
            for hint in hints:
                game_type = hint['game_type']
                if game_type not in summary['by_game_type']:
                    summary['by_game_type'][game_type] = []
                summary['by_game_type'][game_type].append(hint)
                
                # Extract primitive from details if present
                try:
                    details = json.loads(hint['details']) if hint['details'] else {}
                    if 'suggested' in details:
                        prim = details['suggested']
                        if prim not in summary['by_primitive']:
                            summary['by_primitive'][prim] = 0
                        summary['by_primitive'][prim] += hint['confidence']
                except Exception:
                    pass
            
            # Get top suggestions
            for prim, score in sorted(
                summary['by_primitive'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]:
                summary['top_suggestions'].append({
                    'primitive': prim,
                    'cumulative_confidence': score
                })
            
        except Exception as e:
            logger.error(f"[CODS] Error getting gap summary: {e}")
            summary['error'] = str(e)
        
        return summary
    
    # ======================================================================
    # STRATEGY-DRIVEN UNLOCK SYSTEM (Teacher Model)
    # ======================================================================
    # CODS acts as a teacher observing agents express capability needs
    # When agents say "need to find object to interact with", CODS diagnoses
    # this as a need for control_test or systematic_explore primitives
    # ======================================================================
    
    # Expression-to-primitive mapping
    # Maps natural language patterns in agent strategies to locked primitives
    STRATEGY_TO_PRIMITIVE_MAP = {
        # Agent-centric primitives
        'find.*object.*interact': ['control_test', 'effect_scope'],
        'starting move': ['self_location', 'control_test'],
        'click.*different': ['control_test', 'effect_scope'],
        'try.*each.*object': ['control_test', 'effect_scope'],
        'what.*control': ['self_location', 'effect_scope'],
        'which.*move': ['self_location', 'control_test'],
        
        # Exploration primitives
        'explor': ['effect_scope', 'control_test'],
        'discover': ['control_test', 'effect_scope'],
        'find.*pattern': ['detect_cycles', 'correlation'],
        
        # Spatial/structural primitives
        'path|route|way': ['path_exists', 'distance_transform'],
        'edge|boundary|wall': ['detect_edges', 'containment_check'],
        'enclosed|sealed|contain': ['containment_check', 'boundary_seal_check'],
        'flow|fill|overflow': ['flow_simulation', 'containment_check'],
        
        # Goal-oriented primitives
        'goal|target|objective': ['goal_distance', 'progress_estimate'],
        'stuck|blocked|dead.?end': ['dead_end_detect', 'path_exists'],
        'progress|closer|further': ['progress_estimate', 'goal_distance'],
        
        # Temporal/predictive primitives
        'repeat|cycle|loop|oscillat': ['detect_cycles', 'rate_of_change'],
        'stable|unchang|constant': ['stability_score', 'rate_of_change'],
        'predict|expect|anticipate': ['rate_of_change', 'stability_score'],
        
        # Meta-cognitive primitives
        'uncertain|unsure|maybe': ['uncertainty_estimate', 'novelty_score'],
        'confiden|certain|sure': ['uncertainty_estimate', 'learning_progress'],
        'learn|improv|better': ['learning_progress', 'novelty_score'],
        
        # Constraint primitives
        'constraint|rule|must': ['identify_constraints', 'check_constraint_satisfaction'],
        'satisfy|meet|fulfill': ['check_constraint_satisfaction', 'find_minimal_changes'],
        'minimal|fewest|least': ['find_minimal_changes', 'optimize_action_sequence'],
        
        # Relational primitives
        'cause|effect|trigger': ['causal_link', 'dependency_check'],
        'depend|require|need.*first': ['dependency_check', 'causal_link'],
        
        # Reference/template primitives
        'template|pattern|example': ['extract_schema', 'apply_template'],
        'reference|key|legend': ['identify_reference_object', 'extract_schema'],
    }
    
    def parse_strategy_for_needs(self, strategy_text: str) -> List[Dict[str, Any]]:
        """
        Parse agent strategy text to identify capability needs.
        
        This is the "teacher listening" phase - CODS observes what agents
        say they need and maps it to locked primitives.
        
        Args:
            strategy_text: The win_strategy or failure_reason text from agents
            
        Returns:
            List of identified needs with primitive mappings and confidence
        """
        import re
        
        needs = []
        text_lower = strategy_text.lower()
        
        for pattern, primitives in self.STRATEGY_TO_PRIMITIVE_MAP.items():
            if re.search(pattern, text_lower):
                for prim in primitives:
                    # Check if this primitive is locked
                    status = self.unlock_manager.get_status(prim)
                    if status == PrimitiveStatus.LOCKED:
                        needs.append({
                            'primitive': prim,
                            'pattern_matched': pattern,
                            'strategy_text': strategy_text[:100],
                            'confidence': 0.7 if primitives.index(prim) == 0 else 0.5
                        })
        
        return needs
    
    def process_agent_strategy_signals(
        self,
        min_frequency: int = 10,
        unlock_threshold: Optional[int] = None,
        unlock_percentage: float = 0.10
    ) -> Dict[str, Any]:
        """
        Process all agent strategy signals to identify network-wide needs.
        
        This is the main entry point for strategy-driven unlock.
        Scans network_failure_hypotheses for capability needs.
        
        ADAPTIVE THRESHOLD:
        - If unlock_threshold is None, calculates based on active agent count
        - unlock_percentage (default 10%) of active agents must express need
        - Minimum floor of 15 to prevent noise-based unlocks
        - Maximum cap of 100 to prevent very large networks from being too slow
        
        Args:
            min_frequency: Minimum times a need must be expressed to track (default 10)
            unlock_threshold: Fixed threshold (if None, uses adaptive)
            unlock_percentage: Percentage of active agents for adaptive threshold (default 10%)
            
        Returns:
            Summary of needs detected and any unlocks triggered
        """
        results = {
            'strategies_scanned': 0,
            'needs_detected': {},
            'unlocks_triggered': [],
            'unlock_threshold_used': 0,
            'active_agents': 0,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            # Calculate adaptive threshold if not provided
            if unlock_threshold is None:
                # Get active agent count
                agent_count = self.db.execute_query("""
                    SELECT COUNT(*) as cnt FROM agents WHERE is_active = 1
                """)
                active_agents = agent_count[0]['cnt'] if agent_count else 100
                results['active_agents'] = active_agents
                
                # Adaptive: unlock_percentage of active agents, with floor/ceiling
                calculated = int(active_agents * unlock_percentage)
                unlock_threshold = max(15, min(100, calculated))  # Floor 15, cap 100
                
                logger.info(f"[CODS-TEACHER] Adaptive threshold: {unlock_threshold} "
                           f"({unlock_percentage:.0%} of {active_agents} agents)")
            
            results['unlock_threshold_used'] = unlock_threshold
            
            # Get all unique strategies from the network
            strategies = self.db.execute_query("""
                SELECT win_strategy, COUNT(*) as frequency
                FROM network_failure_hypotheses
                WHERE win_strategy IS NOT NULL
                GROUP BY win_strategy
                ORDER BY frequency DESC
                LIMIT 100
            """)
            
            if not strategies:
                logger.info("[CODS-TEACHER] No agent strategies found to analyze")
                return results
            
            results['strategies_scanned'] = len(strategies)
            
            # Parse each strategy for needs
            for strat in strategies:
                text = strat['win_strategy']
                frequency = strat['frequency']
                
                needs = self.parse_strategy_for_needs(text)
                
                for need in needs:
                    prim = need['primitive']
                    if prim not in results['needs_detected']:
                        results['needs_detected'][prim] = {
                            'total_frequency': 0,
                            'patterns': [],
                            'status': 'locked'
                        }
                    
                    results['needs_detected'][prim]['total_frequency'] += frequency
                    if need['pattern_matched'] not in results['needs_detected'][prim]['patterns']:
                        results['needs_detected'][prim]['patterns'].append(need['pattern_matched'])
            
            # Check for unlock threshold
            for prim, data in results['needs_detected'].items():
                if data['total_frequency'] >= unlock_threshold:
                    # Try to unlock this primitive
                    success = self._attempt_need_based_unlock(
                        prim, 
                        data['total_frequency'],
                        data['patterns']
                    )
                    if success:
                        results['unlocks_triggered'].append({
                            'primitive': prim,
                            'frequency': data['total_frequency'],
                            'reason': 'network_need_threshold'
                        })
            
            # Record primitive needs to hints table for tracking
            self._record_strategy_needs(results['needs_detected'])
            
            # Log summary
            if results['needs_detected']:
                top_needs = sorted(
                    results['needs_detected'].items(),
                    key=lambda x: x[1]['total_frequency'],
                    reverse=True
                )[:5]
                logger.info(f"[CODS-TEACHER] Top needs: " + 
                           ", ".join(f"{p}({d['total_frequency']}x)" for p, d in top_needs))
            
            if results['unlocks_triggered']:
                logger.info(f"[CODS-TEACHER] Unlocked {len(results['unlocks_triggered'])} primitives!")
            
        except Exception as e:
            logger.error(f"[CODS-TEACHER] Error processing strategies: {e}")
            results['error'] = str(e)
        
        return results
    
    def _attempt_need_based_unlock(
        self,
        primitive_name: str,
        frequency: int,
        patterns: List[str]
    ) -> bool:
        """
        Attempt to unlock a primitive based on expressed network need.
        
        Unlike discovery-based unlock, this is triggered by high frequency
        of agents expressing a capability need in their strategies.
        
        Args:
            primitive_name: Primitive to unlock
            frequency: How many times agents expressed need
            patterns: What patterns were matched
            
        Returns:
            True if unlock successful
        """
        try:
            # Verify primitive exists and is locked
            status = self.unlock_manager.get_status(primitive_name)
            if status != PrimitiveStatus.LOCKED:
                logger.debug(f"[CODS-TEACHER] {primitive_name} not locked (status={status})")
                return False
            
            # Record the unlock attempt
            attempt_id = self.unlock_manager.record_unlock_attempt(
                primitive_name=primitive_name,
                discovered_pattern={'type': 'need_based', 'patterns': patterns},
                game_ids_tested=['network_aggregate'],
                success_rate=1.0,  # Need-based = 100% valid
                cross_game_success_rate=1.0,  # Network-wide = cross-game
                agent_id='network_collective',
                generation=self._context.generation if self._context else 0
            )
            
            # Approve the unlock - network need is sufficient
            reasoning = (f"Network expressed need {frequency} times via patterns: "
                        f"{', '.join(patterns[:3])}")
            
            success = self.unlock_manager.approve_unlock(
                attempt_id=attempt_id,
                oracle_reasoning=reasoning,
                similarity=0.95  # High similarity for need-based
            )
            
            if success:
                logger.info(f"[CODS-TEACHER] NETWORK UNLOCKED: {primitive_name} "
                           f"(expressed {frequency}x)")
                
                # Note: The unlock is already recorded by approve_unlock
                # No separate record_decision call needed
            
            return success
            
        except Exception as e:
            logger.error(f"[CODS-TEACHER] Unlock attempt failed for {primitive_name}: {e}")
            return False
    
    def _record_strategy_needs(self, needs: Dict[str, Dict]) -> None:
        """Record detected needs to primitive hints table."""
        try:
            for prim, data in needs.items():
                hint_id = f"need_{prim}_{uuid.uuid4().hex[:8]}"
                details = json.dumps({
                    'suggested': prim,
                    'frequency': data['total_frequency'],
                    'patterns': data['patterns']
                })
                
                self.db.execute_query("""
                    INSERT OR REPLACE INTO cods_primitive_hints
                    (hint_id, game_type, source, hint_type, confidence, details, recorded_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    hint_id,
                    'network_aggregate',
                    'strategy_expression',
                    'capability_need',
                    min(1.0, data['total_frequency'] / 100.0),
                    details,
                    datetime.utcnow().isoformat()
                ))
        except Exception as e:
            logger.debug(f"[CODS-TEACHER] Error recording needs: {e}")
    
    # ======================================================================
    # AGENT HELP REQUEST SYSTEM
    # ======================================================================
    # Agents can actively request specific capabilities they need.
    # This is different from passive strategy analysis - it's an explicit
    # "I need X to solve this problem" request.
    # ======================================================================
    
    def request_help(
        self,
        agent_id: str,
        game_id: str,
        level: int,
        need_description: str,
        requested_capability: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Agent actively requests help by describing what they need.
        
        This is the "student asking for help" interface. Agents can describe
        what they're struggling with and optionally request specific primitives.
        
        Args:
            agent_id: Agent making the request
            game_id: Game they're struggling with
            level: Level they're stuck on
            need_description: Natural language description of what they need
            requested_capability: Optional specific primitive they think they need
            
        Returns:
            Response with available help, suggested primitives, or cohort wisdom
        """
        response = {
            'help_provided': False,
            'available_primitives': [],
            'suggested_actions': [],
            'cohort_wisdom': None,
            'unlock_triggered': False,
            'message': ''
        }
        
        try:
            # 1. Parse what the agent needs
            needs = self.parse_strategy_for_needs(need_description)
            
            # 2. Check if any needed primitives are already available
            available = []
            locked_needs = []
            
            for need in needs:
                prim_name = need['primitive']
                status = self.unlock_manager.get_status(prim_name)
                if status in [PrimitiveStatus.UNLOCKED, PrimitiveStatus.GRANDFATHERED]:
                    available.append({
                        'primitive': prim_name,
                        'status': str(status),
                        'description': self._get_primitive_description(prim_name)
                    })
                elif status == PrimitiveStatus.LOCKED:
                    locked_needs.append(prim_name)
            
            response['available_primitives'] = available
            
            if available:
                response['help_provided'] = True
                response['message'] = f"You already have access to: {', '.join([p['primitive'] for p in available])}"
            
            # 3. Record the help request (contributes to unlock threshold)
            self._record_help_request(agent_id, game_id, level, need_description, locked_needs)
            
            # 4. If specific capability requested and it's locked, record that need
            if requested_capability:
                status = self.unlock_manager.get_status(requested_capability)
                if status == PrimitiveStatus.LOCKED:
                    self._record_help_request(
                        agent_id, game_id, level, 
                        f"Explicit request: {requested_capability}", 
                        [requested_capability]
                    )
                    response['message'] += f" Request for '{requested_capability}' recorded."
            
            # 5. Suggest actions based on available primitives
            if available:
                for prim in available:
                    suggestion = self._primitive_to_action_suggestion(prim['primitive'])
                    if suggestion:
                        response['suggested_actions'].append(suggestion)
            
            logger.info(f"[CODS-HELP] Agent {agent_id[:8]} requested help on {game_id}/{level}: "
                       f"needs={len(needs)}, available={len(available)}, locked={len(locked_needs)}")
            
        except Exception as e:
            logger.warning(f"[CODS-HELP] Help request processing error: {e}")
            response['message'] = f"Error processing help request: {e}"
        
        return response
    
    def _record_help_request(
        self, 
        agent_id: str, 
        game_id: str, 
        level: int, 
        description: str,
        locked_needs: List[str]
    ) -> None:
        """Record agent help request to database for unlock threshold tracking."""
        try:
            for prim in locked_needs:
                self.db.execute_query("""
                    INSERT INTO cods_primitive_hints
                    (hint_id, game_type, source, hint_type, confidence, details, recorded_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"help_{agent_id[:8]}_{prim}_{uuid.uuid4().hex[:6]}",
                    game_id,
                    f"agent_request:{agent_id}",
                    'explicit_help_request',
                    0.9,  # High confidence for explicit requests
                    json.dumps({
                        'agent_id': agent_id,
                        'game_id': game_id,
                        'level': level,
                        'description': description[:200],
                        'primitive_requested': prim
                    }),
                    datetime.utcnow().isoformat()
                ))
        except Exception as e:
            logger.debug(f"[CODS-HELP] Failed to record help request: {e}")
    
    def _get_primitive_description(self, primitive_name: str) -> str:
        """Get human-readable description of a primitive."""
        descriptions = {
            'flood_fill': 'Fill connected regions with a color',
            'count_objects': 'Count distinct objects by color',
            'detect_symmetry': 'Detect horizontal/vertical symmetry',
            'get_bounding_box': 'Find the bounding rectangle of an object',
            'extract_objects': 'Separate individual objects from background',
            'apply_transformation': 'Apply rotation, flip, or scale',
            'find_pattern': 'Identify repeating patterns',
            'measure_distance': 'Calculate distances between objects',
            'trace_path': 'Follow a path between points',
            'identify_goal': 'Identify goal/target objects',
        }
        return descriptions.get(primitive_name, f'Primitive: {primitive_name}')
    
    def _primitive_to_action_suggestion(self, primitive_name: str) -> Optional[Dict[str, Any]]:
        """Convert a primitive to an action suggestion for the agent."""
        suggestions = {
            'flood_fill': {'action': 6, 'reasoning': 'Click to fill connected region'},
            'detect_symmetry': {'action': 5, 'reasoning': 'Wait to analyze symmetry'},
            'trace_path': {'action': 1, 'reasoning': 'Move along detected path'},
            'identify_goal': {'action': 6, 'reasoning': 'Click on identified goal'},
        }
        return suggestions.get(primitive_name)
    
    # ======================================================================
    # STUCK POINT ANALYSIS (Gap #2)
    # ======================================================================
    # Analyze where agents get stuck and infer what primitives would help.
    # Cross-references stuck points with winner/loser strategies.
    # ======================================================================
    
    # Mapping of stuck patterns to primitives that would help
    STUCK_PATTERN_TO_PRIMITIVE = {
        # Boundary/containment issues
        r'boundary|edge|seal|overflow': ['boundary_detection', 'flood_fill', 'detect_containment'],
        # Repetition/oscillation (agent going in circles)
        r'repeat|cycle|oscillat|loop': ['detect_symmetry', 'find_repeating_patterns', 'cycle_detection'],
        # Object identification issues
        r'shape|object|region|blob': ['detect_shapes', 'detect_objects_in_frame', 'extract_objects'],
        # Hidden/discovery issues
        r'hidden|reveal|uncover|find': ['analyze_spatial_relations', 'detect_containment', 'systematic_explore'],
        # Navigation/movement issues
        r'path|move|block|stuck|wall': ['is_movable', 'is_obstacle', 'pathfinding', 'trace_path'],
        # Goal identification
        r'goal|target|destination|end': ['goal_identification', 'distance_estimation', 'identify_goal'],
        # Pattern matching
        r'pattern|match|template|reference': ['find_pattern', 'reference_detection', 'schema_extraction'],
        # Counting/quantity
        r'count|number|quantity|total': ['count_objects', 'quantity_tracking'],
        # Transformation
        r'rotate|flip|transform|mirror': ['apply_transformation', 'detect_symmetry'],
        # Control/interaction
        r'click|control|interact|which': ['control_test', 'effect_scope', 'self_location'],
    }
    
    def analyze_stuck_points_for_unlocks(
        self,
        min_stuck_count: int = 10,
        min_confidence: float = 0.5
    ) -> Dict[str, Any]:
        """
        Analyze stuck points to identify primitive gaps and trigger unlocks.
        
        This is Gap #2: Using stuck point data to infer what capabilities
        agents are missing. Cross-references with winner strategies to see
        what successful agents did differently.
        
        Args:
            min_stuck_count: Minimum times agents hit a stuck point to consider
            min_confidence: Minimum confidence to trigger unlock pressure
            
        Returns:
            Analysis results with suggested unlocks
        """
        import re
        
        results = {
            'hotspots_analyzed': 0,
            'gaps_identified': [],
            'unlocks_triggered': [],
            'primitives_with_pressure': {},
            'error': None
        }
        
        try:
            # Step 1: Get high-frequency stuck points
            hotspots = self.db.execute_query("""
                SELECT game_type, level_number, stuck_signature,
                       times_hit, times_escaped,
                       (times_hit - COALESCE(times_escaped, 0)) as still_stuck_count,
                       CASE WHEN times_hit > 0 
                            THEN 1.0 * COALESCE(times_escaped, 0) / times_hit 
                            ELSE 0 END as escape_rate,
                       escape_strategy
                FROM network_stuck_points
                WHERE times_hit >= ?
                ORDER BY still_stuck_count DESC
                LIMIT 30
            """, (min_stuck_count,))
            
            if not hotspots:
                logger.debug("[STUCK-ANALYSIS] No stuck points meet threshold")
                return results
            
            results['hotspots_analyzed'] = len(hotspots)
            
            for hotspot in hotspots:
                game_type = hotspot['game_type']
                level = hotspot['level_number']
                escape_rate = hotspot['escape_rate'] or 0
                
                # Step 2: Get winner/loser comparison for this level
                comparison = self.compare_winners_vs_losers(game_type, level)
                
                if comparison.get('gap_keywords'):
                    # Step 3: Map gap keywords to primitives
                    suggested_primitives = self._map_keywords_to_primitives(
                        comparison['gap_keywords']
                    )
                    
                    if suggested_primitives:
                        gap = {
                            'game_type': game_type,
                            'level': level,
                            'stuck_count': hotspot['times_hit'],
                            'escape_rate': escape_rate,
                            'gap_keywords': comparison['gap_keywords'],
                            'suggested_primitives': suggested_primitives,
                            'confidence': min(1.0, (1 - escape_rate) * 0.8 + 0.2)
                        }
                        results['gaps_identified'].append(gap)
                        
                        # Accumulate unlock pressure
                        for prim in suggested_primitives:
                            if prim not in results['primitives_with_pressure']:
                                results['primitives_with_pressure'][prim] = {
                                    'total_stuck': 0,
                                    'confidence_sum': 0,
                                    'sources': []
                                }
                            results['primitives_with_pressure'][prim]['total_stuck'] += hotspot['times_hit']
                            results['primitives_with_pressure'][prim]['confidence_sum'] += gap['confidence']
                            results['primitives_with_pressure'][prim]['sources'].append(
                                f"{game_type}:L{level}"
                            )
            
            # Step 4: Trigger unlocks for high-pressure primitives
            for prim, data in results['primitives_with_pressure'].items():
                avg_confidence = data['confidence_sum'] / len(data['sources']) if data['sources'] else 0
                
                if avg_confidence >= min_confidence and data['total_stuck'] >= min_stuck_count * 2:
                    # Check if primitive is locked
                    status = self.unlock_manager.get_status(prim)
                    if status == PrimitiveStatus.LOCKED:
                        success = self._attempt_need_based_unlock(
                            prim,
                            data['total_stuck'],
                            [f"stuck_point:{src}" for src in data['sources'][:5]]
                        )
                        if success:
                            results['unlocks_triggered'].append({
                                'primitive': prim,
                                'stuck_count': data['total_stuck'],
                                'sources': data['sources'],
                                'reason': 'stuck_point_pressure'
                            })
            
            # Log summary
            if results['gaps_identified']:
                logger.info(f"[STUCK-ANALYSIS] Found {len(results['gaps_identified'])} gaps "
                           f"across {results['hotspots_analyzed']} hotspots")
            if results['unlocks_triggered']:
                logger.info(f"[STUCK-ANALYSIS] Triggered {len(results['unlocks_triggered'])} unlocks!")
                
        except Exception as e:
            logger.error(f"[STUCK-ANALYSIS] Error: {e}")
            results['error'] = str(e)
        
        return results
    
    def compare_winners_vs_losers(
        self,
        game_type: str,
        level: int
    ) -> Dict[str, Any]:
        """
        Compare what winners did vs what losers tried (Gap #4).
        
        The key insight: What can winners do that losers can't?
        This comparison reveals capability gaps that primitives could fill.
        
        Args:
            game_type: Game type to analyze
            level: Level number
            
        Returns:
            Comparison results with gap keywords
        """
        import re
        
        results = {
            'winner_keywords': set(),
            'loser_keywords': set(),
            'gap_keywords': [],
            'winner_count': 0,
            'loser_count': 0,
            'winner_strategies': [],
            'loser_reasons': []
        }
        
        try:
            # Get winner strategies (from network_failure_hypotheses with win_strategy)
            winners = self.db.execute_query("""
                SELECT win_strategy
                FROM network_failure_hypotheses
                WHERE game_type = ? 
                  AND level_number = ?
                  AND win_strategy IS NOT NULL
                  AND win_strategy != ''
                LIMIT 50
            """, (game_type, level))
            
            # Get loser reasons (from game_results with failure status)
            losers = self.db.execute_query("""
                SELECT failure_reason, reasoning
                FROM game_results
                WHERE game_id LIKE ?
                  AND level = ?
                  AND status IN ('STUCK', 'TERMINATED', 'FAILED', 'NOT FINISHED')
                LIMIT 50
            """, (f"{game_type}%", level))
            
            results['winner_count'] = len(winners) if winners else 0
            results['loser_count'] = len(losers) if losers else 0
            
            # Extract keywords from winners
            if winners:
                for w in winners:
                    strategy = w.get('win_strategy', '') or ''
                    results['winner_strategies'].append(strategy[:100])
                    # Extract meaningful keywords (3+ chars, no common words)
                    words = set(re.findall(r'\b[a-z]{3,}\b', strategy.lower()))
                    words -= {'the', 'and', 'for', 'that', 'with', 'this', 'from', 'have', 'was', 'are'}
                    results['winner_keywords'].update(words)
            
            # Extract keywords from losers
            if losers:
                for l in losers:
                    reason = (l.get('failure_reason', '') or '') + ' ' + (l.get('reasoning', '') or '')
                    results['loser_reasons'].append(reason[:100])
                    words = set(re.findall(r'\b[a-z]{3,}\b', reason.lower()))
                    words -= {'the', 'and', 'for', 'that', 'with', 'this', 'from', 'have', 'was', 'are'}
                    results['loser_keywords'].update(words)
            
            # Gap = what winners mention that losers don't
            gap = results['winner_keywords'] - results['loser_keywords']
            results['gap_keywords'] = list(gap)[:20]  # Top 20 gap keywords
            
            # Convert sets to lists for JSON serialization
            results['winner_keywords'] = list(results['winner_keywords'])[:30]
            results['loser_keywords'] = list(results['loser_keywords'])[:30]
            
        except Exception as e:
            logger.debug(f"[WINNER-LOSER] Comparison error: {e}")
            results['error'] = str(e)
        
        return results
    
    def _map_keywords_to_primitives(self, keywords: List[str]) -> List[str]:
        """Map gap keywords to suggested primitives."""
        import re
        
        suggested = set()
        keyword_text = ' '.join(keywords).lower()
        
        for pattern, primitives in self.STUCK_PATTERN_TO_PRIMITIVE.items():
            if re.search(pattern, keyword_text):
                suggested.update(primitives)
        
        return list(suggested)
    
    # ======================================================================
    # CONCEPT-DRIVEN PRIMITIVE UNLOCK (Gap #3)
    # ======================================================================
    # When a concept is relevant, check if its required primitives are
    # unlocked. If not, apply unlock pressure.
    # ======================================================================
    
    def check_concept_primitive_needs(
        self,
        concept_name: str,
        game_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if a concept's required primitives are unlocked (Gap #3).
        
        When a concept like 'containment' is relevant for a game, this checks
        if the primitives that concept needs are available. If not, it applies
        unlock pressure.
        
        Args:
            concept_name: Name of the concept (e.g., 'containment')
            game_type: Optional game type for context
            
        Returns:
            Results showing needed primitives and any unlocks triggered
        """
        from concept_discovery_engine import CONCEPTUAL_PRIMITIVES
        
        results = {
            'concept': concept_name,
            'primitives_needed': [],
            'primitives_available': [],
            'primitives_locked': [],
            'unlocks_triggered': [],
            'error': None
        }
        
        try:
            concept_data = CONCEPTUAL_PRIMITIVES.get(concept_name)
            if not concept_data:
                results['error'] = f"Unknown concept: {concept_name}"
                return results
            
            # Get required components (primitives)
            components = concept_data.get('components', [])
            results['primitives_needed'] = components
            
            for prim in components:
                status = self.unlock_manager.get_status(prim)
                
                if status in [PrimitiveStatus.UNLOCKED, PrimitiveStatus.GRANDFATHERED]:
                    results['primitives_available'].append(prim)
                elif status == PrimitiveStatus.LOCKED:
                    results['primitives_locked'].append(prim)
                    
                    # Apply unlock pressure from concept need
                    success = self._attempt_need_based_unlock(
                        prim,
                        frequency=50,  # Concept-driven = high priority
                        patterns=[f"concept:{concept_name}", f"game:{game_type or 'any'}"]
                    )
                    if success:
                        results['unlocks_triggered'].append({
                            'primitive': prim,
                            'reason': f'concept_{concept_name}_needs',
                            'game_type': game_type
                        })
            
            # Log if unlocks happened
            if results['unlocks_triggered']:
                logger.info(f"[CONCEPT-UNLOCK] Concept '{concept_name}' triggered "
                           f"{len(results['unlocks_triggered'])} unlocks")
            
        except ImportError:
            results['error'] = "ConceptDiscoveryEngine not available"
        except Exception as e:
            logger.error(f"[CONCEPT-UNLOCK] Error: {e}")
            results['error'] = str(e)
        
        return results
    
    def check_all_relevant_concepts(
        self,
        game_type: str,
        level: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Check all concepts that might be relevant for a game and ensure
        their primitives are available.
        
        Args:
            game_type: Game type to check
            level: Optional level number
            
        Returns:
            Summary of concept checks and any unlocks
        """
        results = {
            'game_type': game_type,
            'concepts_checked': [],
            'total_unlocks': 0,
            'unlocks': []
        }
        
        try:
            # Try to get concept suggestions from the engine
            if CONCEPT_ENGINE_AVAILABLE and self.concept_engine:
                suggestions = self.concept_engine.suggest_concept_for_game(game_type)
                
                # Handle both dict and Concept object returns, or None
                if suggestions is None:
                    suggestions = {}
                elif hasattr(suggestions, 'name'):
                    # It's a Concept object, convert to expected format
                    suggestions = {'suggested_concepts': [{'name': suggestions.name}]}
                
                if suggestions.get('suggested_concepts'):
                    for concept in suggestions['suggested_concepts'][:5]:  # Top 5
                        concept_name = concept.get('name') or concept.get('concept_name')
                        if concept_name:
                            check_result = self.check_concept_primitive_needs(
                                concept_name, game_type
                            )
                            results['concepts_checked'].append({
                                'concept': concept_name,
                                'locked_primitives': check_result['primitives_locked'],
                                'unlocks': check_result['unlocks_triggered']
                            })
                            results['total_unlocks'] += len(check_result['unlocks_triggered'])
                            results['unlocks'].extend(check_result['unlocks_triggered'])
            else:
                # Fallback: Check common concepts based on game type
                from concept_discovery_engine import CONCEPTUAL_PRIMITIVES
                
                # Simple heuristic based on game prefix
                if game_type.startswith('ft'):
                    concepts_to_check = ['containment', 'reference_semantics']
                elif game_type.startswith('sp'):
                    concepts_to_check = ['goal_directedness', 'causality']
                elif game_type.startswith('as'):
                    concepts_to_check = ['symmetry', 'conservation']
                else:
                    concepts_to_check = ['causality', 'goal_directedness']
                
                for concept_name in concepts_to_check:
                    if concept_name in CONCEPTUAL_PRIMITIVES:
                        check_result = self.check_concept_primitive_needs(
                            concept_name, game_type
                        )
                        results['concepts_checked'].append({
                            'concept': concept_name,
                            'locked_primitives': check_result['primitives_locked'],
                            'unlocks': check_result['unlocks_triggered']
                        })
                        results['total_unlocks'] += len(check_result['unlocks_triggered'])
                        results['unlocks'].extend(check_result['unlocks_triggered'])
                        
        except Exception as e:
            logger.error(f"[CONCEPT-CHECK] Error: {e}")
            results['error'] = str(e)
        
        return results
    
    # ======================================================================
    # PRIMITIVE INVENTORY (Assessment Interface)
    # ======================================================================
    # Track what primitives the network has access to and is using
    # ======================================================================
    
    def get_primitive_inventory(self) -> Dict[str, Any]:
        """
        Get comprehensive inventory of all primitives.
        
        This provides visibility into what capabilities the network has:
        - Seed primitives (always available)
        - Grandfathered (given for free)
        - Unlocked (earned through discovery or need)
        - Locked (not yet available)
        - Novel (discovered, no human analog)
        - Usage statistics
        
        Returns:
            Complete primitive inventory for assessment
        """
        inventory = {
            'seed': [],
            'grandfathered': [],
            'unlocked': [],
            'locked': [],
            'novel': [],
            'usage_stats': {},
            'summary': {}
        }
        
        try:
            # Seed primitives - get list of names
            inventory['seed'] = self.seeds.list_all()
            
            # Note: Seed primitives are always available, no usage tracking needed
            # (they're internal Python functions, not database-tracked)
            
            # Grandfathered primitives
            grandfathered = self.db.execute_query("""
                SELECT primitive_name, category, description, 
                       COALESCE(times_used, 0) as times_used
                FROM primitive_status
                WHERE status = 'grandfathered'
                ORDER BY times_used DESC
            """)
            if grandfathered:
                for g in grandfathered:
                    inventory['grandfathered'].append({
                        'name': g['primitive_name'],
                        'category': g['category'],
                        'description': g['description']
                    })
                    if g['times_used'] > 0:
                        inventory['usage_stats'][g['primitive_name']] = {
                            'calls': g['times_used'],
                            'type': 'grandfathered'
                        }
            
            # Unlocked primitives
            unlocked = self.db.execute_query("""
                SELECT primitive_name, category, description, unlocked_at,
                       unlocked_by_agent, COALESCE(times_used, 0) as times_used
                FROM primitive_status
                WHERE status = 'unlocked'
                ORDER BY unlocked_at DESC
            """)
            if unlocked:
                for u in unlocked:
                    inventory['unlocked'].append({
                        'name': u['primitive_name'],
                        'category': u['category'],
                        'unlocked_at': u['unlocked_at'],
                        'unlocked_by': u['unlocked_by_agent']
                    })
                    if u['times_used'] > 0:
                        inventory['usage_stats'][u['primitive_name']] = {
                            'calls': u['times_used'],
                            'type': 'unlocked'
                        }
            
            # Locked primitives
            inventory['locked'] = self.unlock_manager.list_locked()
            
            # Novel primitives
            inventory['novel'] = self.unlock_manager.list_novel()
            for n in inventory['novel']:
                if n.get('times_used', 0) > 0:
                    inventory['usage_stats'][n['discovered_name']] = {
                        'calls': n['times_used'],
                        'type': 'novel',
                        'success_rate': n.get('success_rate', 0)
                    }
            
            # Summary
            inventory['summary'] = {
                'total_available': (len(inventory['seed']) + 
                                   len(inventory['grandfathered']) + 
                                   len(inventory['unlocked']) +
                                   len(inventory['novel'])),
                'seed_count': len(inventory['seed']),
                'grandfathered_count': len(inventory['grandfathered']),
                'unlocked_count': len(inventory['unlocked']),
                'locked_count': len(inventory['locked']),
                'novel_count': len(inventory['novel']),
                'total_usage_tracked': sum(
                    s['calls'] for s in inventory['usage_stats'].values()
                ),
                'most_used': sorted(
                    inventory['usage_stats'].items(),
                    key=lambda x: x[1]['calls'],
                    reverse=True
                )[:10]
            }
            
        except Exception as e:
            logger.error(f"[CODS] Error getting primitive inventory: {e}")
            inventory['error'] = str(e)
        
        return inventory
    
    def get_composed_operator_inventory(self) -> Dict[str, Any]:
        """
        Get inventory of composed operators created by the network.
        
        Returns:
            Operator inventory with usage and success stats
        """
        inventory = {
            'operators': [],
            'by_status': {},
            'most_successful': [],
            'most_used': [],
            'summary': {}
        }
        
        try:
            # Get all operators
            operators = self.db.execute_query("""
                SELECT operator_id, name, status, composition_tree,
                       times_tested, successes, success_rate,
                       created_by_agent, created_at
                FROM composed_operators
                WHERE status != 'pruned'
                ORDER BY success_rate DESC, times_tested DESC
            """)
            
            if operators:
                for op in operators:
                    op_dict = dict(op)
                    inventory['operators'].append(op_dict)
                    
                    # Group by status
                    status = op['status']
                    if status not in inventory['by_status']:
                        inventory['by_status'][status] = 0
                    inventory['by_status'][status] += 1
                
                # Most successful (min 5 tests, sorted by success rate)
                inventory['most_successful'] = [
                    {'name': op['name'], 'success_rate': op['success_rate'], 
                     'times_tested': op['times_tested']}
                    for op in operators
                    if op['times_tested'] >= 5
                ][:10]
                
                # Most used
                inventory['most_used'] = sorted(
                    [{'name': op['name'], 'times_tested': op['times_tested']}
                     for op in operators],
                    key=lambda x: x['times_tested'],
                    reverse=True
                )[:10]
            
            inventory['summary'] = {
                'total_operators': len(inventory['operators']),
                'by_status': inventory['by_status'],
                'with_success_rate_above_70': sum(
                    1 for op in inventory['operators']
                    if (op['success_rate'] or 0) >= 0.7 and op['times_tested'] >= 5
                )
            }
            
        except Exception as e:
            logger.error(f"[CODS] Error getting operator inventory: {e}")
            inventory['error'] = str(e)
        
        return inventory

    def _ensure_failure_tables(self) -> None:
        """Ensure failure-driven learning tables exist."""
        try:
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS cods_level_outcomes (
                    outcome_id TEXT PRIMARY KEY,
                    game_id TEXT NOT NULL,
                    agent_id TEXT,
                    level_number INTEGER NOT NULL,
                    passed BOOLEAN NOT NULL,
                    actions_used INTEGER NOT NULL,
                    score_gained REAL DEFAULT 0,
                    generation INTEGER DEFAULT 0,
                    recorded_at TEXT NOT NULL
                )
            """)
            
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS cods_game_outcomes (
                    game_id TEXT PRIMARY KEY,
                    agent_id TEXT,
                    final_score REAL NOT NULL,
                    max_level_reached INTEGER NOT NULL,
                    total_actions INTEGER NOT NULL,
                    won BOOLEAN NOT NULL,
                    operators_tested INTEGER DEFAULT 0,
                    operators_helpful INTEGER DEFAULT 0,
                    primitive_gaps TEXT,
                    concept_signals TEXT,
                    generation INTEGER DEFAULT 0,
                    recorded_at TEXT NOT NULL
                )
            """)
            
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS cods_failure_analyses (
                    analysis_id TEXT PRIMARY KEY,
                    game_id TEXT NOT NULL,
                    level_number INTEGER NOT NULL,
                    agent_id TEXT,
                    actions_at_failure INTEGER,
                    operator_insights TEXT,
                    generation INTEGER DEFAULT 0,
                    analyzed_at TEXT NOT NULL
                )
            """)
            
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS cods_primitive_hints (
                    hint_id TEXT PRIMARY KEY,
                    game_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    hint_type TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    details TEXT,
                    recorded_at TEXT NOT NULL
                )
            """)
            
            # ================================================================
            # GAME-TYPE -> PRIMITIVE THEORY TABLE
            # ================================================================
            # Network learns which primitives/operators work best for each game type.
            # When agents start a game, they query this to prioritize useful primitives.
            # Updated when games score positive - primitives used get credit.
            # ================================================================
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS gametype_primitive_theory (
                    theory_id TEXT PRIMARY KEY,
                    game_type TEXT NOT NULL,
                    primitive_or_operator TEXT NOT NULL,
                    is_operator BOOLEAN DEFAULT FALSE,
                    
                    -- Effectiveness tracking
                    times_used INTEGER DEFAULT 0,
                    times_successful INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 0.0,
                    total_score_contribution REAL DEFAULT 0.0,
                    
                    -- Context - which levels was this useful on?
                    levels_effective TEXT DEFAULT '[]',
                    
                    -- Network consensus
                    agents_validated INTEGER DEFAULT 0,
                    network_confidence REAL DEFAULT 0.5,
                    
                    -- Timestamps
                    first_observed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    UNIQUE(game_type, primitive_or_operator)
                )
            """)
            
            # Create indexes
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_gametype_theory_lookup
                ON gametype_primitive_theory(game_type, success_rate DESC)
            """)
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_cods_level_game 
                ON cods_level_outcomes(game_id, level_number)
            """)
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_cods_hints_game 
                ON cods_primitive_hints(game_type, confidence DESC)
            """)
            
            # ================================================================
            # BAYESIAN HYPOTHESIS TABLE (Evidence-Driven Synthesis)
            # ================================================================
            # This is the core of the evolution engine:
            # 1. Hypotheses created from failure patterns
            # 2. Evidence accumulates from game outcomes  
            # 3. When posterior > threshold -> trigger synthesis
            # ================================================================
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS cods_bayesian_hypotheses (
                    hypothesis_id TEXT PRIMARY KEY,
                    
                    -- Identity
                    hypothesis_type TEXT NOT NULL,
                    game_type TEXT NOT NULL,
                    level_number INTEGER,
                    description TEXT NOT NULL,
                    
                    -- What this hypothesis suggests
                    target_primitive TEXT,
                    suggested_composition TEXT,
                    
                    -- Bayesian tracking
                    prior_probability REAL DEFAULT 0.5,
                    evidence_for INTEGER DEFAULT 0,
                    evidence_against INTEGER DEFAULT 0,
                    posterior_probability REAL DEFAULT 0.5,
                    
                    -- Confidence interval (Wilson score)
                    confidence_low REAL DEFAULT 0.0,
                    confidence_high REAL DEFAULT 1.0,
                    
                    -- Thresholds
                    confirmation_threshold REAL DEFAULT 0.85,
                    refutation_threshold REAL DEFAULT 0.15,
                    
                    -- Status
                    status TEXT DEFAULT 'active',
                    source_type TEXT,
                    source_games TEXT,
                    
                    -- Synthesis tracking
                    synthesized_operator_id TEXT,
                    synthesis_generation INTEGER,
                    
                    -- Validation tracking
                    pre_synthesis_success_rate REAL,
                    post_synthesis_success_rate REAL,
                    validation_games INTEGER DEFAULT 0,
                    
                    -- Timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    confirmed_at TIMESTAMP,
                    synthesized_at TIMESTAMP
                )
            """)
            
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_cods_bayes_status 
                ON cods_bayesian_hypotheses(status, posterior_probability DESC)
            """)
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_cods_bayes_game 
                ON cods_bayesian_hypotheses(game_type, level_number)
            """)
            
        except Exception as e:
            logger.error(f"[CODS] Error creating failure tables: {e}")
    
    # ======================================================================
    # INTERNAL HELPERS
    # ======================================================================
    
    def _record_usage(self, name: str, success: bool, exec_time: float):
        """Record operator usage statistics."""
        if name not in self._execution_stats:
            self._execution_stats[name] = {
                'calls': 0, 'successes': 0, 'total_time': 0.0
            }
        
        self._execution_stats[name]['calls'] += 1
        if success:
            self._execution_stats[name]['successes'] += 1
        self._execution_stats[name]['total_time'] += exec_time
        
        # Also track in database
        self.unlock_manager.track_primitive_usage(name, success)
    
    def _extract_primitives_from_tree(self, tree: Dict[str, Any]) -> List[str]:
        """
        Recursively extract all primitive names from a composition tree.
        
        Args:
            tree: Composition tree dict with 'type' and 'components' or 'name'
            
        Returns:
            List of primitive names found in the tree
        """
        primitives = []
        
        if not tree:
            return primitives
        
        if isinstance(tree, str):
            # Direct primitive name
            primitives.append(tree)
        elif isinstance(tree, dict):
            # Check for 'name' field (leaf primitive)
            if 'name' in tree:
                primitives.append(tree['name'])
            
            # Check for 'components' (composed operator)
            if 'components' in tree:
                for component in tree['components']:
                    primitives.extend(self._extract_primitives_from_tree(component))
            
            # Check for 'left'/'right' (binary composition)
            if 'left' in tree:
                primitives.extend(self._extract_primitives_from_tree(tree['left']))
            if 'right' in tree:
                primitives.extend(self._extract_primitives_from_tree(tree['right']))
        
        return primitives

    def _record_test_result(
        self,
        operator_id: str,
        success: bool,
        output: Any,
        exec_time: float
    ):
        """Record a test result for a composed operator."""
        if not self._context:
            return
        
        # Determine if this is frontier or replay from context
        is_frontier = self._context.is_frontier if self._context else False
        
        self.composer.record_test_result(
            operator_id=operator_id,
            game_id=self._context.game_id,
            success=success,
            output_value=output,
            execution_time_ms=exec_time,
            level_number=self._context.level_number,
            agent_id=self._context.agent_id,
            generation=self._context.generation,
            score_before=self._context.score,
            score_after=self._context.score,
            is_frontier=is_frontier
        )
        
        # Tier 4: Track operator patterns for concept discovery
        if self.concept_engine:
            try:
                # Get the operator's sub-patterns (component primitives)
                composed_op = self.composer.get_operator(operator_id)
                if composed_op:
                    # Extract primitive names from operator's composition_tree
                    sub_patterns = self._extract_primitives_from_tree(composed_op.composition_tree)
                    
                    if success:
                        self.concept_engine.track_successful_operator_pattern(
                            operator_id=operator_id,
                            game_id=self._context.game_id,
                            sub_patterns=sub_patterns
                        )
                    else:
                        self.concept_engine.track_failed_operator_pattern(
                            operator_id=operator_id,
                            game_id=self._context.game_id,
                            sub_patterns=sub_patterns
                        )
                    
                    # Periodically check for concept emergence
                    if self._context and self._context.generation % 10 == 0:
                        emerging = self.concept_engine.check_concept_emergence()
                        for concept_data in emerging:
                            logger.info(
                                f"[CODS-CONCEPT] Potential concept: {concept_data['pattern'][:30]} "
                                f"({len(concept_data['games_proven'])} games)"
                            )
            except Exception as e:
                logger.debug(f"Concept tracking failed (non-critical): {e}")
    
    def _store_test_context(
        self,
        game_id: str,
        test_reason: str,
        reasoning: Optional[str],
        hypothesis_id: Optional[str],
        score_delta: float,
        results: Dict[str, bool]
    ):
        """
        Store context about why operators were tested (for learning).
        
        This enables:
        1. Correlation between reasoning patterns and operator success
        2. Learning which operators are relevant to which game situations
        3. Tracking hypothesis-driven testing outcomes
        
        Args:
            game_id: Game identifier
            test_reason: Why testing was triggered
            reasoning: Agent's reasoning text (if any)
            hypothesis_id: Hypothesis being tested (if any)
            score_delta: Change in score
            results: Dict of {operator_name: success}
        """
        # Create table if needed
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS cods_test_contexts (
                context_id TEXT PRIMARY KEY,
                game_id TEXT NOT NULL,
                level_number INTEGER,
                agent_id TEXT,
                generation INTEGER,
                test_reason TEXT NOT NULL,
                reasoning_text TEXT,
                hypothesis_id TEXT,
                score_delta REAL,
                operators_tested INTEGER,
                operators_succeeded INTEGER,
                operator_results TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        context_id = str(uuid.uuid4())
        operators_tested = len(results)
        operators_succeeded = sum(1 for v in results.values() if v)
        
        self.db.execute_query("""
            INSERT INTO cods_test_contexts
            (context_id, game_id, level_number, agent_id, generation,
             test_reason, reasoning_text, hypothesis_id, score_delta,
             operators_tested, operators_succeeded, operator_results)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            context_id,
            game_id,
            self._context.level_number if self._context else 1,
            self._context.agent_id if self._context else None,
            self._context.generation if self._context else 0,
            test_reason,
            reasoning[:500] if reasoning else None,  # Truncate long reasoning
            hypothesis_id,
            score_delta,
            operators_tested,
            operators_succeeded,
            json.dumps(results)
        ))
        
        logger.debug(
            f"[CODS] Stored test context: reason={test_reason}, "
            f"tested={operators_tested}, succeeded={operators_succeeded}"
        )

    # ======================================================================
    # BAYESIAN HYPOTHESIS SYSTEM (Evidence-Driven Synthesis)
    # ======================================================================
    # The core of operator evolution:
    # 1. Create hypotheses from failure patterns
    # 2. Accumulate evidence from game outcomes
    # 3. When posterior > threshold -> trigger synthesis
    # 4. Validate synthesized operators over generations
    # ======================================================================
    
    def _bayesian_update(self, prior: float, evidence_for: int, evidence_against: int) -> float:
        """
        Calculate posterior probability using Bayesian update.
        
        Uses Beta-Binomial conjugate prior for clean updates.
        
        Args:
            prior: Prior probability P(H)
            evidence_for: Count of supporting observations
            evidence_against: Count of contradicting observations
            
        Returns:
            Posterior probability P(H|E)
        """
        # Convert prior to pseudo-counts (Beta distribution parameters)
        # Prior of 0.5 = 2 pseudo-observations each way (weak prior)
        alpha_prior = 2 * prior
        beta_prior = 2 * (1 - prior)
        
        # Update with evidence
        alpha_post = alpha_prior + evidence_for
        beta_post = beta_prior + evidence_against
        
        # Posterior mean of Beta distribution
        posterior = alpha_post / (alpha_post + beta_post)
        
        return posterior
    
    def _wilson_confidence_interval(
        self, 
        successes: int, 
        total: int, 
        confidence: float = 0.95
    ) -> Tuple[float, float]:
        """
        Calculate Wilson score confidence interval.
        
        Better than normal approximation for small samples.
        
        Args:
            successes: Number of positive outcomes
            total: Total observations
            confidence: Confidence level (default 0.95)
            
        Returns:
            (lower_bound, upper_bound) tuple
        """
        import math
        
        if total == 0:
            return (0.0, 1.0)
        
        # Z-score for confidence level
        z = 1.96 if confidence == 0.95 else 2.576  # 95% or 99%
        
        p_hat = successes / total
        n = total
        
        # Wilson score interval
        denominator = 1 + z**2 / n
        center = (p_hat + z**2 / (2*n)) / denominator
        spread = z * math.sqrt((p_hat * (1 - p_hat) + z**2 / (4*n)) / n) / denominator
        
        lower = max(0.0, center - spread)
        upper = min(1.0, center + spread)
        
        return (lower, upper)
    
    def create_hypothesis(
        self,
        hypothesis_type: str,
        game_type: str,
        description: str,
        level_number: Optional[int] = None,
        target_primitive: Optional[str] = None,
        suggested_composition: Optional[List[str]] = None,
        source_type: Optional[str] = None,
        prior: float = 0.5
    ) -> Optional[str]:
        """
        Create a new Bayesian hypothesis for potential operator synthesis.
        
        Args:
            hypothesis_type: 'PRIMITIVE_NEED', 'OPERATOR_SYNTHESIS', 'PATTERN_DISCOVERY'
            game_type: Game type this hypothesis applies to (e.g., 'sp80')
            description: Human-readable description
            level_number: Specific level (optional)
            target_primitive: Primitive to unlock if confirmed
            suggested_composition: List of primitives to compose if confirmed
            source_type: How hypothesis was generated ('failure_analysis', 'counterfactual', etc.)
            prior: Initial probability (default 0.5 = maximum uncertainty)
            
        Returns:
            hypothesis_id if created, None on failure
        """
        try:
            # Check for existing similar hypothesis
            existing_rows = self.db.execute_query("""
                SELECT hypothesis_id, evidence_for, evidence_against, posterior_probability
                FROM cods_bayesian_hypotheses
                WHERE game_type = ? AND description = ? AND status = 'active'
            """, (game_type, description))
            existing = existing_rows[0] if existing_rows else None
            
            if existing:
                # Hypothesis already exists - just return its ID
                h_id = existing['hypothesis_id']
                logger.debug(f"[BAYES] Hypothesis already exists: {h_id[:12]}")
                return h_id
            
            hypothesis_id = str(uuid.uuid4())
            
            self.db.execute_query("""
                INSERT INTO cods_bayesian_hypotheses
                (hypothesis_id, hypothesis_type, game_type, level_number, description,
                 target_primitive, suggested_composition, prior_probability, 
                 posterior_probability, source_type, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
            """, (
                hypothesis_id,
                hypothesis_type,
                game_type,
                level_number,
                description,
                target_primitive,
                json.dumps(suggested_composition) if suggested_composition else None,
                prior,
                prior,  # Initially posterior = prior
                source_type
            ))
            
            logger.info(f"[BAYES] Created hypothesis: {description[:50]} (P={prior:.2f})")
            return hypothesis_id
            
        except Exception as e:
            logger.error(f"[BAYES] Failed to create hypothesis: {e}")
            return None
    
    def record_evidence(
        self,
        hypothesis_id: str,
        supports: bool,
        weight: float = 1.0,
        source_game: Optional[str] = None
    ) -> Optional[float]:
        """
        Record evidence for/against a hypothesis and update posterior.
        
        Args:
            hypothesis_id: ID of hypothesis to update
            supports: True if evidence supports hypothesis, False if contradicts
            weight: Evidence weight (default 1.0, can be higher for strong evidence)
            source_game: Game ID that provided this evidence
            
        Returns:
            Updated posterior probability, or None on failure
        """
        try:
            # Fetch current state
            current_rows = self.db.execute_query("""
                SELECT prior_probability, evidence_for, evidence_against, source_games
                FROM cods_bayesian_hypotheses
                WHERE hypothesis_id = ? AND status = 'active'
            """, (hypothesis_id,))
            current = current_rows[0] if current_rows else None
            
            if not current:
                logger.warning(f"[BAYES] Hypothesis not found or inactive: {hypothesis_id[:12]}")
                return None
            
            prior = current['prior_probability']
            evidence_for = current['evidence_for']
            evidence_against = current['evidence_against']
            source_games_json = current['source_games']
            
            # Update evidence counts
            evidence_weight = int(weight)  # Round to integer for counts
            if supports:
                evidence_for += evidence_weight
            else:
                evidence_against += evidence_weight
            
            # Calculate new posterior
            posterior = self._bayesian_update(prior, evidence_for, evidence_against)
            
            # Calculate confidence interval
            total_evidence = evidence_for + evidence_against
            conf_low, conf_high = self._wilson_confidence_interval(evidence_for, total_evidence)
            
            # Update source games
            source_games = json.loads(source_games_json) if source_games_json else []
            if source_game and source_game not in source_games:
                source_games.append(source_game)
                source_games = source_games[-50:]  # Keep last 50
            
            # Update database
            self.db.execute_query("""
                UPDATE cods_bayesian_hypotheses
                SET evidence_for = ?,
                    evidence_against = ?,
                    posterior_probability = ?,
                    confidence_low = ?,
                    confidence_high = ?,
                    source_games = ?,
                    last_updated = CURRENT_TIMESTAMP
                WHERE hypothesis_id = ?
            """, (
                evidence_for,
                evidence_against,
                posterior,
                conf_low,
                conf_high,
                json.dumps(source_games),
                hypothesis_id
            ))
            
            logger.debug(
                f"[BAYES] Updated: +{evidence_weight if supports else 0}/-{evidence_weight if not supports else 0} "
                f"-> P={posterior:.3f} (n={total_evidence})"
            )
            
            return posterior
            
        except Exception as e:
            logger.error(f"[BAYES] Failed to record evidence: {e}")
            return None
    
    def observe_failure_pattern(
        self,
        game_type: str,
        level_number: int,
        failure_pattern: str,
        suggested_primitive: Optional[str] = None,
        suggested_composition: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Record a failure pattern and create/update hypothesis.
        
        This is the main entry point for failure-driven learning.
        Called when agents fail at a level with a specific pattern.
        
        Args:
            game_type: Game type (e.g., 'sp80')
            level_number: Level where failure occurred
            failure_pattern: Description of what went wrong (e.g., 'boundary_overflow')
            suggested_primitive: Oracle's suggestion for what primitive might help
            suggested_composition: Oracle's suggestion for operator composition
            
        Returns:
            hypothesis_id (new or existing)
        """
        # Create descriptive hypothesis
        description = f"{failure_pattern} at {game_type} L{level_number}"
        
        hypothesis_type = 'OPERATOR_SYNTHESIS' if suggested_composition else 'PRIMITIVE_NEED'
        
        # Create or get existing hypothesis
        hypothesis_id = self.create_hypothesis(
            hypothesis_type=hypothesis_type,
            game_type=game_type,
            description=description,
            level_number=level_number,
            target_primitive=suggested_primitive,
            suggested_composition=suggested_composition,
            source_type='failure_analysis'
        )
        
        if hypothesis_id:
            # Record this as supporting evidence (failure happened again)
            self.record_evidence(
                hypothesis_id=hypothesis_id,
                supports=True,  # Failure pattern recurring = evidence we need this capability
                weight=1.0,
                source_game=f"{game_type}-failure-L{level_number}"
            )
        
        return hypothesis_id
    
    def observe_success_pattern(
        self,
        game_type: str,
        level_number: int,
        hypothesis_id: Optional[str] = None
    ):
        """
        Record when a level is successfully completed.
        
        This provides counter-evidence against "we need X to pass this level".
        
        Args:
            game_type: Game type
            level_number: Level completed
            hypothesis_id: Specific hypothesis to update (optional)
        """
        try:
            if hypothesis_id:
                # Direct update
                self.record_evidence(
                    hypothesis_id=hypothesis_id,
                    supports=False,  # Success without the capability = counter-evidence
                    weight=1.0,
                    source_game=f"{game_type}-success-L{level_number}"
                )
            else:
                # Update all active hypotheses for this game/level
                hypotheses = self.db.execute_query("""
                    SELECT hypothesis_id
                    FROM cods_bayesian_hypotheses
                    WHERE game_type = ? 
                    AND (level_number = ? OR level_number IS NULL)
                    AND status = 'active'
                """, (game_type, level_number))
                
                for h in (hypotheses or []):
                    h_id = h['hypothesis_id'] if isinstance(h, dict) else h[0]
                    self.record_evidence(
                        hypothesis_id=h_id,
                        supports=False,
                        weight=0.5,  # Weaker counter-evidence for indirect match
                        source_game=f"{game_type}-success-L{level_number}"
                    )
                    
        except Exception as e:
            logger.error(f"[BAYES] Failed to record success: {e}")
    
    def get_confirmed_hypotheses(self, min_posterior: float = 0.85) -> List[BayesianHypothesis]:
        """
        Get hypotheses that have accumulated enough evidence to act on.
        
        Args:
            min_posterior: Minimum posterior probability (default 0.85)
            
        Returns:
            List of BayesianHypothesis objects ready for synthesis
        """
        try:
            rows = self.db.execute_query("""
                SELECT hypothesis_id, hypothesis_type, game_type, level_number,
                       description, target_primitive, suggested_composition,
                       prior_probability, evidence_for, evidence_against,
                       posterior_probability, confidence_low, confidence_high,
                       confirmation_threshold, refutation_threshold, status, source_type
                FROM cods_bayesian_hypotheses
                WHERE status = 'active'
                AND posterior_probability >= ?
                AND (evidence_for + evidence_against) >= 5
                ORDER BY posterior_probability DESC
            """, (min_posterior,))
            
            hypotheses = []
            for row in (rows or []):
                h = BayesianHypothesis(
                    hypothesis_id=row['hypothesis_id'],
                    hypothesis_type=row['hypothesis_type'],
                    game_type=row['game_type'],
                    level_number=row['level_number'],
                    description=row['description'],
                    target_primitive=row['target_primitive'],
                    suggested_composition=json.loads(row['suggested_composition']) if row['suggested_composition'] else None,
                    prior=row['prior_probability'],
                    evidence_for=row['evidence_for'],
                    evidence_against=row['evidence_against'],
                    posterior=row['posterior_probability'],
                    confidence_low=row['confidence_low'],
                    confidence_high=row['confidence_high'],
                    confirmation_threshold=row['confirmation_threshold'],
                    refutation_threshold=row['refutation_threshold'],
                    status=row['status'],
                    source_type=row['source_type']
                )
                hypotheses.append(h)
            
            return hypotheses
            
        except Exception as e:
            logger.error(f"[BAYES] Failed to get confirmed hypotheses: {e}")
            return []
    
    def synthesize_from_hypothesis(
        self,
        hypothesis: BayesianHypothesis,
        generation: int = 0
    ) -> Optional[str]:
        """
        Synthesize a new operator from a confirmed hypothesis.
        
        This is where evolution happens: accumulated evidence
        triggers the creation of new cognitive capabilities.
        
        Args:
            hypothesis: Confirmed hypothesis to synthesize from
            generation: Current generation number
            
        Returns:
            operator_id if synthesis successful, None otherwise
        """
        try:
            if not hypothesis.is_confirmed():
                logger.warning(f"[SYNTH] Hypothesis not confirmed: P={hypothesis.posterior:.2f}")
                return None
            
            operator_id = None
            
            if hypothesis.suggested_composition:
                # Compose new operator from suggested primitives
                operator_name = f"synth_{hypothesis.game_type}_L{hypothesis.level_number or 'X'}_{uuid.uuid4().hex[:6]}"
                
                # Check that primitives are available
                available_primitives = []
                for prim_name in hypothesis.suggested_composition:
                    status = self.unlock_manager.get_status(prim_name)
                    if status in [PrimitiveStatus.UNLOCKED, PrimitiveStatus.GRANDFATHERED]:
                        available_primitives.append(prim_name)
                    elif self.seeds.get(prim_name):
                        available_primitives.append(prim_name)
                    else:
                        logger.warning(f"[SYNTH] Primitive not available: {prim_name}")
                
                if len(available_primitives) < 2:
                    logger.warning(f"[SYNTH] Not enough primitives for composition: {available_primitives}")
                    return None
                
                # Create the composed operator
                try:
                    composed_op = self.compose_operator(
                        primitives=available_primitives,
                        name=operator_name
                    )
                    if composed_op:
                        operator_id = composed_op.operator_id
                        logger.info(
                            f"[SYNTH] Created operator: {operator_name} "
                            f"from {available_primitives}"
                        )
                        
                        # ADDED 2025-12-28: Distribute operator via viral package system
                        # This bridges the gap between CODS synthesis and agent learning
                        try:
                            from viral_package_engine import ViralPackageEngine
                            viral_engine = ViralPackageEngine(self.db)
                            
                            # Get agent_id from context if available
                            agent_id = self._context.agent_id if self._context else "system"
                            
                            package_id = viral_engine.create_viral_package_from_operator(
                                operator_id=operator_id,
                                operator_name=operator_name,
                                primitives=available_primitives,
                                agent_id=agent_id,
                                generation=generation,
                                game_type=hypothesis.game_type,
                                level_number=hypothesis.level_number
                            )
                            if package_id:
                                logger.info(f"[SYNTH->VIRAL] Operator distributed as package: {package_id}")
                        except Exception as ve:
                            logger.warning(f"[SYNTH->VIRAL] Failed to distribute operator: {ve}")
                            
                except Exception as e:
                    logger.error(f"[SYNTH] Composition failed: {e}")
                    return None
                    
            elif hypothesis.target_primitive:
                # Unlock the suggested primitive
                sample_size = hypothesis.sample_size()
                success_rate = max(0.0, min(1.0, hypothesis.posterior))
                cross_game_rate = max(0.0, min(1.0, sample_size / 5.0))

                success = self.unlock_manager.attempt_unlock(
                    primitive_name=hypothesis.target_primitive,
                    pattern={
                        'source': 'bayesian_hypothesis',
                        'posterior': hypothesis.posterior,
                        'evidence_for': hypothesis.evidence_for,
                        'evidence_against': hypothesis.evidence_against,
                        'suggested_composition': hypothesis.suggested_composition,
                        'description': hypothesis.description
                    },
                    success_rate=success_rate,
                    cross_game_success_rate=cross_game_rate,
                    unlock_reason=f"Bayesian confirmation: {hypothesis.description}",
                    agent_id=self._context.agent_id if self._context else None,
                    generation=generation
                )
                if success:
                    operator_id = hypothesis.target_primitive
                    logger.info(f"[SYNTH] Unlocked primitive: {hypothesis.target_primitive}")
            
            if operator_id:
                # Mark hypothesis as synthesized
                self.db.execute_query("""
                    UPDATE cods_bayesian_hypotheses
                    SET status = 'synthesized',
                        synthesized_operator_id = ?,
                        synthesis_generation = ?,
                        synthesized_at = CURRENT_TIMESTAMP
                    WHERE hypothesis_id = ?
                """, (operator_id, generation, hypothesis.hypothesis_id))
                
                logger.info(
                    f"[SYNTH] Hypothesis synthesized: {hypothesis.description[:40]} "
                    f"-> {operator_id}"
                )
            
            return operator_id
            
        except Exception as e:
            logger.error(f"[SYNTH] Synthesis failed: {e}")
            return None
    
    def check_and_synthesize(self, generation: int = 0) -> Dict[str, Any]:
        """
        Check for confirmed hypotheses and synthesize operators.
        
        Call this at the end of each generation.
        
        Args:
            generation: Current generation number
            
        Returns:
            Summary of synthesis actions taken
        """
        results = {
            'hypotheses_checked': 0,
            'syntheses_triggered': 0,
            'operators_created': [],
            'primitives_unlocked': []
        }
        
        try:
            confirmed = self.get_confirmed_hypotheses()
            results['hypotheses_checked'] = len(confirmed)
            
            for hypothesis in confirmed:
                operator_id = self.synthesize_from_hypothesis(hypothesis, generation)
                
                if operator_id:
                    results['syntheses_triggered'] += 1
                    if hypothesis.suggested_composition:
                        results['operators_created'].append(operator_id)
                    else:
                        results['primitives_unlocked'].append(operator_id)
            
            if results['syntheses_triggered'] > 0:
                logger.info(
                    f"[SYNTH] Generation {generation}: "
                    f"{results['syntheses_triggered']} syntheses from "
                    f"{results['hypotheses_checked']} confirmed hypotheses"
                )
                
        except Exception as e:
            logger.error(f"[SYNTH] Check and synthesize failed: {e}")
            results['error'] = str(e)
        
        return results
    
    def get_hypothesis_summary(self) -> Dict[str, Any]:
        """Get summary of current hypothesis state for logging."""
        try:
            stats_rows = self.db.execute_query("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active,
                    SUM(CASE WHEN status = 'confirmed' THEN 1 ELSE 0 END) as confirmed,
                    SUM(CASE WHEN status = 'synthesized' THEN 1 ELSE 0 END) as synthesized,
                    SUM(CASE WHEN status = 'refuted' THEN 1 ELSE 0 END) as refuted,
                    AVG(posterior_probability) as avg_posterior,
                    MAX(posterior_probability) as max_posterior,
                    SUM(evidence_for + evidence_against) as total_evidence
                FROM cods_bayesian_hypotheses
            """)
            stats = stats_rows[0] if stats_rows else None
            
            if stats:
                # stats is a dict-like Row object, use column names
                return {
                    'total': stats['total'] or 0,
                    'active': stats['active'] or 0,
                    'confirmed': stats['confirmed'] or 0,
                    'synthesized': stats['synthesized'] or 0,
                    'refuted': stats['refuted'] or 0,
                    'avg_posterior': round(stats['avg_posterior'] or 0, 3),
                    'max_posterior': round(stats['max_posterior'] or 0, 3),
                    'total_evidence': stats['total_evidence'] or 0
                }
            return {}
            
        except Exception as e:
            logger.error(f"[BAYES] Failed to get summary: {e}")
            return {'error': str(e)}
    
    def prune_refuted_hypotheses(self, max_age_days: int = 30) -> int:
        """
        Clean up hypotheses that have been refuted or are too old.
        
        Args:
            max_age_days: Max age for inactive hypotheses
            
        Returns:
            Number of hypotheses removed
        """
        try:
            # Mark low-posterior hypotheses as refuted
            self.db.execute_query("""
                UPDATE cods_bayesian_hypotheses
                SET status = 'refuted'
                WHERE status = 'active'
                AND posterior_probability < refutation_threshold
                AND (evidence_for + evidence_against) >= 10
            """)
            
            # Delete old refuted hypotheses
            result = self.db.execute_query(f"""
                DELETE FROM cods_bayesian_hypotheses
                WHERE status = 'refuted'
                AND last_updated < datetime('now', '-{max_age_days} days')
            """)
            
            deleted = result.rowcount if hasattr(result, 'rowcount') else 0
            
            if deleted > 0:
                logger.info(f"[BAYES] Pruned {deleted} refuted hypotheses")
            
            return deleted
            
        except Exception as e:
            logger.error(f"[BAYES] Prune failed: {e}")
            return 0

    # ======================================================================
    # AGENT PATTERN ANALYZER (Evidence-Driven Discovery)
    # ======================================================================
    # The species writes its own cookbook through gameplay.
    # We analyze EXISTING data from agent exploration to find patterns.
    # No hardcoded recipes - patterns emerge from agent behavior.
    # ======================================================================
    
    # Keyword to primitive mapping for parsing win strategies
    KEYWORD_TO_PRIMITIVE = {
        # Boundary/containment
        'boundary': 'detect_edges',
        'edge': 'detect_edges',
        'border': 'detect_edges',
        'seal': 'is_enclosed',
        'enclosed': 'is_enclosed',
        'contain': 'detect_containment',
        'overflow': 'flood_fill',
        'fill': 'flood_fill',
        'flood': 'flood_fill',
        # Pattern/template
        'pattern': 'extract_schema',
        'template': 'apply_template',
        'schema': 'extract_schema',
        'reference': 'is_reference',
        'match': 'pattern_matching',
        # Navigation
        'path': 'pathfinding',
        'navigate': 'pathfinding',
        'move': 'is_movable',
        'obstacle': 'detect_obstacles',
        'block': 'detect_obstacles',
        # Objects
        'object': 'find_distinct_objects',
        'shape': 'detect_shapes',
        'color': 'detect_colors',
        'region': 'detect_regions',
        # Transformation
        'rotate': 'apply_transformation',
        'flip': 'apply_transformation',
        'mirror': 'detect_symmetry',
        'symmetr': 'detect_symmetry',
        # Control
        'control': 'control_test',
        'click': 'effect_scope',
    }
    
    def analyze_agent_patterns(
        self,
        generation: int,
        lookback_generations: int = 10,
        min_sample_size: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze agent gameplay data to discover emerging primitive patterns.
        
        This is the core of agent-driven evolution:
        1. Parse win strategies for primitive mentions
        2. Correlate with game outcomes
        3. Find primitive combinations that correlate with success
        4. Create hypotheses for patterns with sufficient evidence
        
        Args:
            generation: Current generation
            lookback_generations: How many generations to analyze
            min_sample_size: Minimum observations for a pattern to be considered
            
        Returns:
            Summary of discovered patterns and created hypotheses
        """
        results = {
            'strategies_analyzed': 0,
            'patterns_discovered': [],
            'hypotheses_created': 0,
            'generation': generation,
            'error': None
        }
        
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"[AGENT-PATTERNS] Analyzing agent gameplay (Gen {generation})")
            logger.info(f"{'='*60}")
            
            # Step 1: Get win strategies from successful games
            success_strategies = self._get_success_strategies(
                generation, lookback_generations
            )
            
            # Step 2: Get failure strategies for comparison
            failure_strategies = self._get_failure_strategies(
                generation, lookback_generations
            )
            
            results['strategies_analyzed'] = len(success_strategies) + len(failure_strategies)
            
            if len(success_strategies) < min_sample_size:
                logger.info(f"[AGENT-PATTERNS] Not enough success data yet "
                           f"({len(success_strategies)} < {min_sample_size})")
                return results
            
            # Step 3: Extract primitive mentions from strategies
            success_primitives = self._extract_primitives_from_strategies(success_strategies)
            failure_primitives = self._extract_primitives_from_strategies(failure_strategies)
            
            # Step 4: Find differential patterns (appear more in success than failure)
            patterns = self._find_differential_patterns(
                success_primitives,
                failure_primitives,
                len(success_strategies),
                len(failure_strategies) if failure_strategies else 1,
                min_sample_size
            )
            
            results['patterns_discovered'] = patterns
            
            # Step 5: Create Bayesian hypotheses for strong patterns
            for pattern in patterns:
                hypothesis_id = self._create_pattern_hypothesis(pattern, generation)
                if hypothesis_id:
                    results['hypotheses_created'] += 1
            
            if patterns:
                logger.info(f"[AGENT-PATTERNS] Discovered {len(patterns)} patterns, "
                           f"created {results['hypotheses_created']} hypotheses")
            else:
                logger.info(f"[AGENT-PATTERNS] No significant patterns found yet")
            
            return results
            
        except Exception as e:
            logger.error(f"[AGENT-PATTERNS] Analysis failed: {e}")
            results['error'] = str(e)
            return results
    
    def _get_success_strategies(
        self, 
        generation: int, 
        lookback: int
    ) -> List[Dict[str, Any]]:
        """Get win strategies from games that succeeded (level 2+)."""
        try:
            strategies = self.db.execute_query("""
                SELECT 
                    nfh.win_strategy,
                    nfh.game_type,
                    nfh.level_number,
                    nfh.generation,
                    nfh.final_score
                FROM network_failure_hypotheses nfh
                WHERE nfh.win_strategy IS NOT NULL
                AND nfh.win_strategy != ''
                AND nfh.level_number >= 2
                AND nfh.generation BETWEEN ? AND ?
                ORDER BY nfh.generation DESC
                LIMIT 500
            """, (generation - lookback, generation))
            
            return list(strategies) if strategies else []
            
        except Exception as e:
            logger.debug(f"[AGENT-PATTERNS] Error fetching success strategies: {e}")
            return []
    
    def _get_failure_strategies(
        self, 
        generation: int, 
        lookback: int
    ) -> List[Dict[str, Any]]:
        """Get strategies from games that failed (level 1 only)."""
        try:
            strategies = self.db.execute_query("""
                SELECT 
                    nfh.failure_reason,
                    nfh.game_type,
                    nfh.level_number,
                    nfh.generation
                FROM network_failure_hypotheses nfh
                WHERE nfh.level_number = 1
                AND nfh.generation BETWEEN ? AND ?
                ORDER BY nfh.generation DESC
                LIMIT 500
            """, (generation - lookback, generation))
            
            return list(strategies) if strategies else []
            
        except Exception as e:
            logger.debug(f"[AGENT-PATTERNS] Error fetching failure strategies: {e}")
            return []
    
    def _extract_primitives_from_strategies(
        self, 
        strategies: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract primitive mentions from strategy texts.
        
        Parses win_strategy or failure_reason fields for keywords
        that map to primitives.
        
        Returns:
            Dict mapping primitive names to usage stats
        """
        primitive_stats = {}
        
        for strategy in strategies:
            # Get text to parse
            text = strategy.get('win_strategy') or strategy.get('failure_reason') or ''
            text_lower = text.lower()
            game_type = strategy.get('game_type', 'unknown')
            
            # Find primitives mentioned in this strategy
            primitives_found = set()
            
            for keyword, primitive in self.KEYWORD_TO_PRIMITIVE.items():
                if keyword in text_lower:
                    primitives_found.add(primitive)
            
            # Track individual primitives
            for prim in primitives_found:
                if prim not in primitive_stats:
                    primitive_stats[prim] = {
                        'count': 0,
                        'game_types': set(),
                        'co_occurs_with': {}
                    }
                primitive_stats[prim]['count'] += 1
                primitive_stats[prim]['game_types'].add(game_type)
            
            # Track co-occurrence (primitive pairs)
            primitives_list = list(primitives_found)
            for i, p1 in enumerate(primitives_list):
                for p2 in primitives_list[i+1:]:
                    # Bi-directional tracking
                    if p2 not in primitive_stats[p1]['co_occurs_with']:
                        primitive_stats[p1]['co_occurs_with'][p2] = 0
                    primitive_stats[p1]['co_occurs_with'][p2] += 1
                    
                    if p1 not in primitive_stats[p2]['co_occurs_with']:
                        primitive_stats[p2]['co_occurs_with'][p1] = 0
                    primitive_stats[p2]['co_occurs_with'][p1] += 1
        
        # Convert sets to lists for JSON serialization
        for prim in primitive_stats:
            primitive_stats[prim]['game_types'] = list(primitive_stats[prim]['game_types'])
        
        return primitive_stats
    
    def _find_differential_patterns(
        self,
        success_primitives: Dict[str, Dict],
        failure_primitives: Dict[str, Dict],
        success_count: int,
        failure_count: int,
        min_sample_size: int
    ) -> List[Dict[str, Any]]:
        """
        Find primitive combinations that appear more in successes than failures.
        
        This is the key insight: patterns that correlate with success
        are candidates for operator synthesis.
        """
        patterns = []
        
        # Analyze primitive pairs from success data
        pair_success_rates = {}
        
        for prim1, stats in success_primitives.items():
            for prim2, co_count in stats['co_occurs_with'].items():
                pair = tuple(sorted([prim1, prim2]))
                
                if pair not in pair_success_rates:
                    # Calculate success rate (how often pair appears in successes)
                    success_rate = co_count / success_count if success_count > 0 else 0
                    
                    # Calculate failure rate
                    failure_rate = 0
                    if prim1 in failure_primitives and prim2 in failure_primitives.get(prim1, {}).get('co_occurs_with', {}):
                        failure_co_count = failure_primitives[prim1]['co_occurs_with'].get(prim2, 0)
                        failure_rate = failure_co_count / failure_count if failure_count > 0 else 0
                    
                    # Differential: how much more common in successes
                    differential = success_rate - failure_rate
                    
                    pair_success_rates[pair] = {
                        'primitives': list(pair),
                        'success_rate': round(success_rate, 3),
                        'failure_rate': round(failure_rate, 3),
                        'differential': round(differential, 3),
                        'success_count': co_count,
                        'game_types': list(set(
                            success_primitives[prim1].get('game_types', []) +
                            success_primitives.get(prim2, {}).get('game_types', [])
                        ))
                    }
        
        # Filter for significant patterns
        for pair, stats in pair_success_rates.items():
            # Pattern must:
            # 1. Appear in enough successes (min_sample_size)
            # 2. Have positive differential (more common in success than failure)
            # 3. Have at least 20% success rate
            if (stats['success_count'] >= min_sample_size and
                stats['differential'] > 0.1 and
                stats['success_rate'] >= 0.2):
                
                stats['evidence_strength'] = (
                    'strong' if stats['differential'] > 0.3 else
                    'moderate' if stats['differential'] > 0.2 else
                    'weak'
                )
                patterns.append(stats)
        
        # Sort by differential (strongest signal first)
        patterns.sort(key=lambda p: p['differential'], reverse=True)
        
        return patterns[:10]  # Return top 10 patterns
    
    def _create_pattern_hypothesis(
        self, 
        pattern: Dict[str, Any],
        generation: int
    ) -> Optional[str]:
        """
        Create a Bayesian hypothesis from an agent-discovered pattern.
        
        This feeds into the synthesis system - when evidence accumulates,
        the pattern can be synthesized into an operator.
        """
        primitives = pattern['primitives']
        game_types = pattern.get('game_types', ['unknown'])
        
        # Create descriptive hypothesis
        description = f"Agent pattern: {' + '.join(primitives)} (diff={pattern['differential']:.0%})"
        
        # Create hypothesis with suggested composition from agent data
        hypothesis_id = self.create_hypothesis(
            hypothesis_type='OPERATOR_SYNTHESIS',
            game_type=game_types[0] if game_types else 'multi',
            description=description,
            suggested_composition=primitives,
            source_type='agent_gameplay_analysis'
        )
        
        if hypothesis_id:
            # Record initial evidence based on the pattern strength
            evidence_count = pattern['success_count']
            for _ in range(min(evidence_count, 10)):  # Cap at 10 to avoid over-weighting
                self.record_evidence(
                    hypothesis_id=hypothesis_id,
                    supports=True,
                    weight=pattern['differential'],  # Stronger patterns = stronger evidence
                    source_game=f"pattern_gen{generation}"
                )
            
            logger.info(f"  [PATTERN] {' + '.join(primitives)}: "
                       f"success={pattern['success_rate']:.0%}, "
                       f"diff=+{pattern['differential']:.0%}, "
                       f"strength={pattern['evidence_strength']}")
        
        return hypothesis_id
    
    def process_generation_patterns(self, generation: int) -> Dict[str, Any]:
        """
        Main entry point for agent-driven pattern discovery.
        
        Call this at the end of each generation to:
        1. Analyze agent gameplay for emerging patterns
        2. Create/update Bayesian hypotheses
        3. Check for synthesis triggers
        
        Args:
            generation: Current generation number
            
        Returns:
            Combined results from pattern analysis and synthesis
        """
        results = {
            'patterns': {},
            'synthesis': {},
            'generation': generation
        }
        
        try:
            # Step 1: Analyze agent patterns
            pattern_results = self.analyze_agent_patterns(
                generation=generation,
                lookback_generations=10,
                min_sample_size=5
            )
            results['patterns'] = pattern_results
            
            # Step 2: Check for synthesis triggers (uses existing Bayesian system)
            synthesis_results = self.check_and_synthesize(generation=generation)
            results['synthesis'] = synthesis_results
            
            # Step 3: Log summary
            if pattern_results.get('patterns_discovered'):
                logger.info(f"\n[GEN-{generation} SUMMARY]")
                logger.info(f"  Patterns discovered: {len(pattern_results['patterns_discovered'])}")
                logger.info(f"  Hypotheses created: {pattern_results['hypotheses_created']}")
                logger.info(f"  Syntheses triggered: {synthesis_results.get('syntheses_triggered', 0)}")
            
            return results
            
        except Exception as e:
            logger.error(f"[AGENT-PATTERNS] Generation processing failed: {e}")
            results['error'] = str(e)
            return results


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

_engine: Optional[CODSEngine] = None


def get_cods_engine(db_path: str = "core_data.db") -> CODSEngine:
    """Get the global CODS engine instance."""
    global _engine
    if _engine is None:
        _engine = CODSEngine(db_path=db_path)
    return _engine


def check_for_potential_unlocks(
    db_path: str = "core_data.db",
    min_success_rate: float = 0.70,
    min_cross_game_rate: float = 0.50,
    min_tests: int = 5
) -> Dict[str, Any]:
    """
    Post-generation check for operators ready to unlock primitives.
    
    Scans high-performing composed operators and checks if they match
    any locked primitives. Called after each generation in evolution runner.
    
    Args:
        db_path: Database path
        min_success_rate: Minimum success rate for consideration (RLVR)
        min_cross_game_rate: Minimum cross-game success rate (RLVR)
        min_tests: Minimum test count before consideration
        
    Returns:
        Dictionary with unlock check results:
        - operators_checked: Number of operators evaluated
        - unlock_attempts: Number of unlock attempts made
        - unlocks_approved: Number of primitives unlocked
        - novel_discoveries: Number of novel primitives registered
        - details: List of detailed results per attempt
    """
    engine = get_cods_engine(db_path)
    
    results = {
        'operators_checked': 0,
        'unlock_attempts': 0,
        'unlocks_approved': 0,
        'novel_discoveries': 0,
        'details': []
    }
    
    try:
        # Get high-performing operators that might qualify for unlock
        candidates = engine.composer.db.execute_query("""
            SELECT 
                co.operator_id,
                co.name,
                co.composition_tree,
                co.success_rate,
                co.cross_game_rate,
                co.times_tested,
                co.status,
                COUNT(DISTINCT otr.game_id) as unique_games
            FROM composed_operators co
            LEFT JOIN operator_test_results otr ON co.operator_id = otr.operator_id
            WHERE co.success_rate >= ?
            AND co.times_tested >= ?
            AND co.status NOT IN ('canonical', 'pruned')
            GROUP BY co.operator_id
            HAVING unique_games >= ?
            ORDER BY co.success_rate DESC
            LIMIT 20
        """, (min_success_rate, min_tests, 3))
        
        if not candidates:
            logger.info("[CODS] No operators qualify for unlock check")
            return results
        
        results['operators_checked'] = len(candidates)
        logger.info(f"[CODS] Checking {len(candidates)} operators for potential unlocks")
        
        # Get locked primitives
        locked_primitives = engine.unlock_manager.list_locked()
        locked_names = {p['primitive_name'] for p in locked_primitives}
        
        for candidate in candidates:
            op_id = candidate['operator_id']
            op_name = candidate['name']
            success_rate = candidate['success_rate']
            cross_game_rate = candidate['cross_game_rate'] or 0.0
            
            # Skip if cross-game rate too low
            if cross_game_rate < min_cross_game_rate:
                continue
            
            # Try to match against locked primitives using oracle
            try:
                composition_tree = json.loads(candidate['composition_tree']) if isinstance(
                    candidate['composition_tree'], str
                ) else candidate['composition_tree']
            except (json.JSONDecodeError, TypeError):
                continue
            
            # Get test results for this operator
            test_results_rows = engine.db.execute_query("""
                SELECT game_id, success FROM operator_test_results
                WHERE operator_id = ?
                ORDER BY tested_at DESC
                LIMIT 50
            """, (op_id,))
            
            if not test_results_rows:
                continue
            
            test_games = [r['game_id'] for r in test_results_rows]
            test_results = {r['game_id']: bool(r['success']) for r in test_results_rows}
            
            # Check each locked primitive for similarity
            best_match = None
            best_similarity = 0.0
            
            for locked in locked_primitives:
                prim_name = locked['primitive_name']
                
                # Use oracle pattern matcher to check similarity
                similarity = engine.oracle._compute_similarity(
                    composition_tree, prim_name
                )
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = prim_name
            
            # If we found a good match, attempt unlock
            if best_match and best_similarity >= 0.60:
                results['unlock_attempts'] += 1
                
                attempt_id = engine.attempt_unlock(
                    primitive_name=best_match,
                    discovered_pattern=composition_tree,
                    test_games=test_games,
                    test_results=test_results
                )
                
                # Check the verdict
                decision = engine.db.execute_query("""
                    SELECT verdict, confidence, reasoning FROM oracle_decisions
                    WHERE attempt_id = ?
                    ORDER BY decided_at DESC LIMIT 1
                """, (attempt_id,))
                
                if decision:
                    verdict = decision[0]['verdict']
                    
                    detail = {
                        'operator': op_name,
                        'matched_primitive': best_match,
                        'similarity': best_similarity,
                        'success_rate': success_rate,
                        'cross_game_rate': cross_game_rate,
                        'verdict': verdict
                    }
                    results['details'].append(detail)
                    
                    if verdict == 'approved':
                        results['unlocks_approved'] += 1
                        logger.info(f"[CODS] UNLOCKED: {best_match} (via {op_name})")
                    elif verdict == 'novel':
                        results['novel_discoveries'] += 1
                        logger.info(f"[CODS] NOVEL: {op_name} registered as novel primitive")
            
            # Check if it's a completely novel pattern (no match to any locked)
            elif best_similarity < 0.30 and success_rate >= 0.80 and cross_game_rate >= 0.60:
                # This might be a novel discovery
                results['unlock_attempts'] += 1
                
                # Register as potential novel using record_novel_primitive
                novel_id = engine.unlock_manager.record_novel_primitive(
                    composition_tree=composition_tree,
                    discovered_by_agent=candidate.get('created_by_agent') or 'auto_discovery',
                    discovered_in_game=test_games[0] if test_games else 'batch_check',
                    generation=0,
                    success_rate=success_rate,
                    games_validated=len(test_games),
                    cross_game_rate=cross_game_rate
                )
                
                if novel_id:
                    results['novel_discoveries'] += 1
                    results['details'].append({
                        'operator': op_name,
                        'matched_primitive': None,
                        'similarity': best_similarity,
                        'success_rate': success_rate,
                        'cross_game_rate': cross_game_rate,
                        'verdict': 'novel'
                    })
                    logger.info(f"[CODS] NOVEL DISCOVERY: {op_name} -> {novel_id}")
        
        # Log summary
        if results['unlocks_approved'] > 0 or results['novel_discoveries'] > 0:
            logger.info(f"[CODS] Unlock check complete: "
                       f"{results['unlocks_approved']} unlocked, "
                       f"{results['novel_discoveries']} novel")
        
    except Exception as e:
        logger.warning(f"[CODS] Unlock check failed: {e}")
        results['error'] = str(e)
    
    return results


def reset_cods_engine():
    """Reset the global CODS engine."""
    global _engine
    _engine = None


def apply(operator: str, *args, **kwargs) -> OperatorResult:
    """Apply an operator (convenience function)."""
    return get_cods_engine().apply(operator, *args, **kwargs)


def compose(primitives: List[str], name: Optional[str] = None) -> ComposedOperator:
    """Compose an operator (convenience function)."""
    return get_cods_engine().compose_operator(primitives, name)


def analyze(frame: List[List[int]]) -> Dict[str, Any]:
    """Analyze a frame (convenience function)."""
    return get_cods_engine().analyze_frame(frame)
