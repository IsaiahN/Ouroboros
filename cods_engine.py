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
        
        # Current game context
        self._context: Optional[CODSGameContext] = None
        
        # Operator execution stats
        self._execution_stats: Dict[str, Dict] = {}
        
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
        generation: int = 0
    ):
        """Set the current game context."""
        self._context = CODSGameContext(
            game_id=game_id,
            level_number=level_number,
            agent_id=agent_id,
            generation=generation
        )
        
        # Set episode context in seed primitives
        self.seeds.set_episode_context(game_id)
        self.seeds.reset_episode()
    
    def update_frame(
        self,
        frame: List[List[int]],
        score: Optional[float] = None,
        action_count: Optional[int] = None
    ):
        """
        Update current frame in context and test composed operators.
        
        Args:
            frame: Current game frame
            score: Current score (optional, for success evaluation)
            action_count: Current action count (optional)
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
        
        # Test composed operators on this frame (critical for unlock system)
        # Only test every 10 actions to avoid overhead
        if action_count is None or action_count % 10 == 0:
            game_id = self._context.game_id if self._context else 'unknown'
            logger.info(f"[CODS] Testing operators at action_count={action_count} for game {game_id}")
            try:
                results = self.test_composed_operators(
                    frame=frame,
                    previous_frame=previous_frame,
                    score_delta=score_delta
                )
                if results:
                    successes = sum(1 for v in results.values() if v)
                    logger.info(f"[CODS] Tested {len(results)} operators: {successes} success")
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
    # COMPOSED OPERATOR TESTING
    # ======================================================================
    
    def test_composed_operators(
        self,
        frame: Optional[List[List[int]]] = None,
        previous_frame: Optional[List[List[int]]] = None,
        score_delta: float = 0.0
    ) -> Dict[str, bool]:
        """
        Test all cobbled/solid composed operators on the current frame.
        
        This is CRITICAL for the unlock system - operators must be tested
        to accumulate success/failure data for unlock evaluation.
        
        Args:
            frame: Current frame
            previous_frame: Previous frame (for delta operators)
            score_delta: Change in score (for success evaluation)
            
        Returns:
            Dict of {operator_name: success}
        """
        frame = frame or (self._context.current_frame if self._context else None)
        if not frame:
            return {}
        
        results = {}
        
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
                
                logger.debug(f"[CODS] Tested {op_name}: {'SUCCESS' if success else 'FAIL'}")
                
            except Exception as e:
                results[op_name] = False
                logger.debug(f"[CODS] Operator {op_name} test failed: {e}")
        
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
    ) -> Optional[int]:
        """
        Use cognitive operators to suggest an action.
        
        This is a placeholder for more sophisticated action selection.
        Currently just demonstrates operator application.
        
        Args:
            frame: Current frame
            
        Returns:
            Suggested action (1-7) or None
        """
        frame = frame or (self._context.current_frame if self._context else None)
        if not frame:
            return None
        
        # Analyze frame
        analysis = self.analyze_frame(frame)
        
        # Simple heuristic based on analysis
        # (This would be replaced by learned action selection)
        
        if 'detect_symmetry' in analysis:
            symmetry = analysis['detect_symmetry']
            if symmetry.get('horizontal'):
                return 1  # ACTION1 - up
            if symmetry.get('vertical'):
                return 3  # ACTION3 - left
        
        if 'detect_shapes' in analysis:
            shapes = analysis['detect_shapes']
            if shapes:
                # Move toward first detected shape
                return 1  # Placeholder
        
        # Default to random action
        return self.seeds.call('rand_int', 1, 7)
    
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
            
        except Exception as e:
            logger.error(f"[CODS] Error recording game outcome: {e}")
            results['error'] = str(e)
        
        return results
    
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
        
        if failure_history and failure_history[0]['fail_count'] >= 3:
            avg_level = failure_history[0]['avg_level'] or 1
            
            # If agents consistently fail at same level, there's likely a primitive gap
            if max_level <= avg_level + 0.5:
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
            
            # Create indexes
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_cods_level_game 
                ON cods_level_outcomes(game_id, level_number)
            """)
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_cods_hints_game 
                ON cods_primitive_hints(game_type, confidence DESC)
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
            score_after=self._context.score
        )


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
