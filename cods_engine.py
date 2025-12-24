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
        self.composer = OperatorComposer(db=self.db, seed_registry=self.seeds)
        self.oracle = OracleInterface(db=self.db, unlock_manager=self.unlock_manager)
        
        # Initialize existing engines as wrappers
        self._init_existing_engines()
        
        # Grandfather existing primitives
        grandfather_existing_primitives(self.unlock_manager)
        
        # Current game context
        self._context: Optional[CODSGameContext] = None
        
        # Operator execution stats
        self._execution_stats: Dict[str, Dict] = {}
        
        logger.info(f"[CODS] Engine initialized with {self.seeds.count()} seed primitives")
    
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
    
    def update_frame(self, frame: List[List[int]]):
        """Update current frame in context."""
        if self._context:
            self._context.update_frame(frame)
        self.seeds.update_frame(frame)
    
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
            
            # 3. Check if it's a composed operator
            composed_op = self.composer.get_operator(operator_name)
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
        
        Creates operators from seed primitives based on common patterns
        found in winning sequences. This seeds the CODS system so
        evolve_operators and check_for_potential_unlocks have something to work with.
        
        Args:
            limit: Maximum number of operators to create
            
        Returns:
            Number of operators created
        """
        created_count = 0
        
        # Check if we already have operators
        existing = self.db.execute_query("SELECT COUNT(*) as cnt FROM composed_operators")
        if existing and existing[0]['cnt'] >= 10:
            logger.debug(f"[CODS] Already have {existing[0]['cnt']} operators, skipping bootstrap")
            return 0
        
        # Define common operator patterns from seed primitives
        operator_patterns = [
            # Spatial analysis operators
            (['get_pixel', 'equals'], 'pixel_compare'),
            (['for_each_pixel', 'sum'], 'pixel_sum'),
            (['get_frame', 'len'], 'frame_size'),
            (['get_at', 'equals'], 'element_match'),
            
            # Temporal operators
            (['get_previous_frame', 'get_frame', 'equals'], 'frame_unchanged'),
            (['get_action_history', 'len'], 'action_count'),
            
            # Aggregation operators
            (['filter', 'len'], 'count_matching'),
            (['map', 'sum'], 'mapped_sum'),
            (['for_range', 'any'], 'range_check'),
            
            # Comparison operators
            (['subtract', 'greater_than'], 'delta_positive'),
        ]
        
        for primitives, name in operator_patterns:
            if created_count >= limit:
                break
            
            # Check if all primitives are available (seed primitives)
            all_available = all(self.seeds.get(p) is not None for p in primitives)
            if not all_available:
                continue
            
            try:
                # Create the composed operator (cast for type checker)
                ops: List[Any] = list(primitives)  # type: ignore[misc]
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
