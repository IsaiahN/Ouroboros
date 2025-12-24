"""
Operator Composer - Compose primitives into higher-level operators
=================================================================

The heart of CODS discovery: combines seed primitives into complex operators
through composition, evolution, and validation.

Lifecycle: cobbled -> tested -> validated -> solid -> canonical

Composition Operations:
- compose: Chain primitives (output of one feeds input of next)
- parallel: Run primitives in parallel, combine results  
- conditional: Branch based on predicate
- parameter_shift: Modify parameters systematically
- invert: Create inverse operation
- amplify: Strengthen/weaken effects
- threshold: Convert continuous to boolean
- delay: Time-shift operations
- diff: Compare across time
- accumulate: Aggregate over time

Rule 1: Disable pycache
Rule 2: All data in database
Rule 10: Leverage existing systems
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import json
import uuid
import copy
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

from database_interface import DatabaseInterface
from seed_primitives import get_seed_primitives, Primitive, SeedPrimitiveRegistry

logger = logging.getLogger(__name__)


class OperatorStatus(Enum):
    """Lifecycle status of a composed operator."""
    COBBLED = "cobbled"       # Just created, untested
    TESTED = "tested"         # Has some test results
    VALIDATED = "validated"   # Passed RLVR validation
    SOLID = "solid"           # Consistently performs well
    CANONICAL = "canonical"   # Reference implementation


class CompositionType(Enum):
    """Types of primitive composition."""
    COMPOSE = "compose"           # Sequential chaining
    PARALLEL = "parallel"         # Parallel execution
    CONDITIONAL = "conditional"   # Branching
    PARAMETER_SHIFT = "parameter_shift"
    INVERT = "invert"
    AMPLIFY = "amplify"
    THRESHOLD = "threshold"
    DELAY = "delay"
    DIFF = "diff"
    ACCUMULATE = "accumulate"


@dataclass
class ComposedOperator:
    """A composed operator made from primitives."""
    operator_id: str
    name: str
    composition_tree: Dict[str, Any]  # Tree structure of composition
    input_types: List[str]
    output_type: str
    status: OperatorStatus = OperatorStatus.COBBLED
    
    # Validation stats
    times_tested: int = 0
    successes: int = 0
    success_rate: float = 0.0
    cross_game_rate: float = 0.0
    
    # Metadata
    created_by_agent: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    parent_operators: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'operator_id': self.operator_id,
            'name': self.name,
            'composition_tree': self.composition_tree,
            'input_types': self.input_types,
            'output_type': self.output_type,
            'status': self.status.value,
            'times_tested': self.times_tested,
            'successes': self.successes,
            'success_rate': self.success_rate,
            'cross_game_rate': self.cross_game_rate,
            'created_by_agent': self.created_by_agent,
            'created_at': self.created_at,
            'parent_operators': self.parent_operators
        }


class OperatorComposer:
    """
    Composes primitives into higher-level operators.
    
    Core capabilities:
    1. Compose: Chain primitives sequentially
    2. Parallel: Run multiple primitives, combine results
    3. Conditional: Branch based on predicate results
    4. Remix: Generate variations of successful operators
    5. Simplify: Find minimal versions that still work
    """
    
    def __init__(
        self, 
        db: Optional[DatabaseInterface] = None, 
        db_path: str = "core_data.db",
        seed_registry: Optional[SeedPrimitiveRegistry] = None
    ):
        self.db = db or DatabaseInterface(db_path)
        self.seeds = seed_registry or get_seed_primitives()
        self._initialize_schema()
        
        # Cache of compiled operators
        self._operator_cache: Dict[str, Callable] = {}
    
    def _initialize_schema(self):
        """Create database tables for operator composition."""
        
        # Composed operators table
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS composed_operators (
                operator_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                composition_tree TEXT NOT NULL,  -- JSON
                composition_type TEXT NOT NULL,
                input_types TEXT,  -- JSON
                output_type TEXT,
                
                -- Lifecycle
                status TEXT DEFAULT 'cobbled',
                
                -- Validation stats
                times_tested INTEGER DEFAULT 0,
                successes INTEGER DEFAULT 0,
                failures INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                cross_game_rate REAL DEFAULT 0.0,
                games_tested_on TEXT,  -- JSON list
                
                -- Genealogy
                parent_operators TEXT,  -- JSON list of parent IDs
                created_by_agent TEXT,
                created_at_generation INTEGER DEFAULT 0,
                
                -- Competition
                competes_with TEXT,  -- Primitive name if competing
                wins_vs_primitive INTEGER DEFAULT 0,
                losses_vs_primitive INTEGER DEFAULT 0,
                
                -- Optimization
                complexity_score REAL DEFAULT 1.0,
                was_simplified_to TEXT,  -- ID of simplified version
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_tested_at TIMESTAMP,
                
                FOREIGN KEY (created_by_agent) REFERENCES agents(agent_id)
            )
        """)
        
        # Operator test results
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS operator_test_results (
                test_id TEXT PRIMARY KEY,
                operator_id TEXT NOT NULL,
                game_id TEXT NOT NULL,
                level_number INTEGER DEFAULT 1,
                
                -- Test context
                input_frame_hash TEXT,
                agent_id TEXT,
                generation INTEGER DEFAULT 0,
                
                -- Results
                success BOOLEAN,
                output_value TEXT,  -- JSON
                execution_time_ms REAL,
                error_message TEXT,
                
                -- Contribution to game outcome
                contributed_to_win BOOLEAN,
                score_before REAL,
                score_after REAL,
                
                tested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (operator_id) REFERENCES composed_operators(operator_id)
            )
        """)
        
        # Remix/mutation history
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS operator_remix_history (
                remix_id TEXT PRIMARY KEY,
                parent_operator_id TEXT NOT NULL,
                child_operator_id TEXT NOT NULL,
                remix_type TEXT NOT NULL,  -- 'compose', 'parallel', 'simplify', etc.
                
                -- What changed
                mutation_description TEXT,
                
                -- Outcome
                child_better BOOLEAN,
                improvement_amount REAL,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (parent_operator_id) REFERENCES composed_operators(operator_id),
                FOREIGN KEY (child_operator_id) REFERENCES composed_operators(operator_id)
            )
        """)
        
        # Create indexes
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_composed_operators_status 
            ON composed_operators(status, success_rate DESC)
        """)
    
    # ======================================================================
    # COMPOSITION OPERATIONS
    # ======================================================================
    
    def compose(
        self,
        operators: List[Union[str, ComposedOperator, Primitive]],
        name: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> ComposedOperator:
        """
        Compose operators sequentially (output of one feeds input of next).
        
        Args:
            operators: List of primitive names, operators, or Primitive objects
            name: Optional name for composed operator
            agent_id: Agent that created this composition
            
        Returns:
            New ComposedOperator
        """
        operator_refs = []
        
        for op in operators:
            if isinstance(op, str):
                # Primitive name or operator ID
                if self.seeds.get(op):
                    operator_refs.append({'type': 'primitive', 'name': op})
                else:
                    operator_refs.append({'type': 'operator', 'id': op})
            elif isinstance(op, Primitive):
                operator_refs.append({'type': 'primitive', 'name': op.name})
            elif isinstance(op, ComposedOperator):
                operator_refs.append({'type': 'operator', 'id': op.operator_id})
        
        composition_tree = {
            'composition_type': CompositionType.COMPOSE.value,
            'operators': operator_refs
        }
        
        operator_id = f"comp_{uuid.uuid4().hex[:12]}"
        if not name:
            name = self._generate_operator_name(composition_tree)
        
        composed = ComposedOperator(
            operator_id=operator_id,
            name=name,
            composition_tree=composition_tree,
            input_types=self._infer_input_types(operator_refs[0] if operator_refs else None),
            output_type=self._infer_output_type(operator_refs[-1] if operator_refs else None),
            created_by_agent=agent_id,
            parent_operators=[r.get('id') for r in operator_refs if r.get('type') == 'operator']
        )
        
        self._store_operator(composed)
        return composed
    
    def parallel(
        self,
        operators: List[Union[str, ComposedOperator]],
        combiner: str = "make_list",  # Primitive to combine results
        name: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> ComposedOperator:
        """
        Run operators in parallel and combine results.
        
        Args:
            operators: List of operators to run in parallel
            combiner: Primitive to combine parallel results
            name: Optional name
            agent_id: Creating agent
            
        Returns:
            New ComposedOperator
        """
        operator_refs = []
        for op in operators:
            if isinstance(op, str):
                if self.seeds.get(op):
                    operator_refs.append({'type': 'primitive', 'name': op})
                else:
                    operator_refs.append({'type': 'operator', 'id': op})
            elif isinstance(op, ComposedOperator):
                operator_refs.append({'type': 'operator', 'id': op.operator_id})
        
        composition_tree = {
            'composition_type': CompositionType.PARALLEL.value,
            'operators': operator_refs,
            'combiner': combiner
        }
        
        operator_id = f"par_{uuid.uuid4().hex[:12]}"
        if not name:
            name = f"parallel_{len(operators)}"
        
        composed = ComposedOperator(
            operator_id=operator_id,
            name=name,
            composition_tree=composition_tree,
            input_types=["any"],  # Parallel operators share input
            output_type="list",
            created_by_agent=agent_id
        )
        
        self._store_operator(composed)
        return composed
    
    def conditional(
        self,
        predicate: Union[str, ComposedOperator],
        if_true: Union[str, ComposedOperator],
        if_false: Union[str, ComposedOperator],
        name: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> ComposedOperator:
        """
        Create conditional operator (if predicate then true_branch else false_branch).
        
        Args:
            predicate: Operator that returns boolean
            if_true: Operator to run if predicate is true
            if_false: Operator to run if predicate is false
            name: Optional name
            agent_id: Creating agent
            
        Returns:
            New ComposedOperator
        """
        def to_ref(op):
            if isinstance(op, str):
                if self.seeds.get(op):
                    return {'type': 'primitive', 'name': op}
                return {'type': 'operator', 'id': op}
            elif isinstance(op, ComposedOperator):
                return {'type': 'operator', 'id': op.operator_id}
            return {'type': 'primitive', 'name': str(op)}
        
        composition_tree = {
            'composition_type': CompositionType.CONDITIONAL.value,
            'predicate': to_ref(predicate),
            'if_true': to_ref(if_true),
            'if_false': to_ref(if_false)
        }
        
        operator_id = f"cond_{uuid.uuid4().hex[:12]}"
        if not name:
            name = f"cond_{uuid.uuid4().hex[:6]}"
        
        composed = ComposedOperator(
            operator_id=operator_id,
            name=name,
            composition_tree=composition_tree,
            input_types=["any"],
            output_type="any",
            created_by_agent=agent_id
        )
        
        self._store_operator(composed)
        return composed
    
    def threshold(
        self,
        operator: Union[str, ComposedOperator],
        threshold_value: float,
        comparison: str = "greater_than",  # Primitive name
        name: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> ComposedOperator:
        """
        Create thresholded operator (convert continuous to boolean).
        
        Args:
            operator: Source operator
            threshold_value: Threshold to compare against
            comparison: Comparison primitive ('greater_than', 'less_than', etc.)
            name: Optional name
            agent_id: Creating agent
            
        Returns:
            New ComposedOperator
        """
        def to_ref(op):
            if isinstance(op, str):
                if self.seeds.get(op):
                    return {'type': 'primitive', 'name': op}
                return {'type': 'operator', 'id': op}
            elif isinstance(op, ComposedOperator):
                return {'type': 'operator', 'id': op.operator_id}
            return {'type': 'primitive', 'name': str(op)}
        
        composition_tree = {
            'composition_type': CompositionType.THRESHOLD.value,
            'operator': to_ref(operator),
            'threshold': threshold_value,
            'comparison': comparison
        }
        
        operator_id = f"thresh_{uuid.uuid4().hex[:12]}"
        if not name:
            name = f"thresh_{threshold_value}"
        
        composed = ComposedOperator(
            operator_id=operator_id,
            name=name,
            composition_tree=composition_tree,
            input_types=["any"],
            output_type="bool",
            created_by_agent=agent_id
        )
        
        self._store_operator(composed)
        return composed
    
    def diff(
        self,
        operator: Union[str, ComposedOperator],
        name: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> ComposedOperator:
        """
        Create differential operator (compare current vs previous frame).
        
        Args:
            operator: Source operator to diff
            name: Optional name
            agent_id: Creating agent
            
        Returns:
            New ComposedOperator that computes difference over time
        """
        def to_ref(op):
            if isinstance(op, str):
                if self.seeds.get(op):
                    return {'type': 'primitive', 'name': op}
                return {'type': 'operator', 'id': op}
            elif isinstance(op, ComposedOperator):
                return {'type': 'operator', 'id': op.operator_id}
            return {'type': 'primitive', 'name': str(op)}
        
        composition_tree = {
            'composition_type': CompositionType.DIFF.value,
            'operator': to_ref(operator)
        }
        
        operator_id = f"diff_{uuid.uuid4().hex[:12]}"
        if not name:
            name = f"diff_{uuid.uuid4().hex[:6]}"
        
        composed = ComposedOperator(
            operator_id=operator_id,
            name=name,
            composition_tree=composition_tree,
            input_types=["frame", "frame"],  # Current and previous
            output_type="any",
            created_by_agent=agent_id
        )
        
        self._store_operator(composed)
        return composed
    
    # ======================================================================
    # OPERATOR EXECUTION
    # ======================================================================
    
    def execute(
        self,
        operator: Union[str, ComposedOperator],
        *args,
        **kwargs
    ) -> Any:
        """
        Execute a composed operator.
        
        Args:
            operator: Operator ID or ComposedOperator
            *args: Input arguments
            **kwargs: Additional arguments
            
        Returns:
            Operator output
        """
        if isinstance(operator, str):
            op = self.get_operator(operator)
            if not op:
                # Try as primitive
                prim = self.seeds.get(operator)
                if prim:
                    return prim(*args, **kwargs)
                raise ValueError(f"Unknown operator: {operator}")
        else:
            op = operator
        
        return self._execute_tree(op.composition_tree, *args, **kwargs)
    
    def _execute_tree(
        self,
        tree: Dict[str, Any],
        *args,
        **kwargs
    ) -> Any:
        """Execute a composition tree."""
        comp_type = tree.get('composition_type')
        
        if comp_type == CompositionType.COMPOSE.value:
            return self._execute_compose(tree, *args, **kwargs)
        elif comp_type == CompositionType.PARALLEL.value:
            return self._execute_parallel(tree, *args, **kwargs)
        elif comp_type == CompositionType.CONDITIONAL.value:
            return self._execute_conditional(tree, *args, **kwargs)
        elif comp_type == CompositionType.THRESHOLD.value:
            return self._execute_threshold(tree, *args, **kwargs)
        elif comp_type == CompositionType.DIFF.value:
            return self._execute_diff(tree, *args, **kwargs)
        else:
            raise ValueError(f"Unknown composition type: {comp_type}")
    
    def _execute_compose(self, tree: Dict, *args, **kwargs) -> Any:
        """
        Execute sequential composition.
        
        For each operator in the chain:
        - If result is None and operator takes no args, call with no args
        - If result is not None, pass it as the first argument
        - Output becomes input for next operator
        """
        result = args[0] if args else None
        
        for op_ref in tree.get('operators', []):
            if result is None:
                # First operator or previous returned None - call with no args
                result = self._execute_ref(op_ref, **kwargs)
            else:
                # Pass previous result as input
                result = self._execute_ref(op_ref, result, **kwargs)
        
        return result
    
    def _execute_parallel(self, tree: Dict, *args, **kwargs) -> Any:
        """Execute parallel composition."""
        results = []
        
        for op_ref in tree.get('operators', []):
            result = self._execute_ref(op_ref, *args, **kwargs)
            results.append(result)
        
        # Combine results
        combiner_name = tree.get('combiner', 'make_list')
        combiner = self.seeds.get(combiner_name)
        if combiner:
            return combiner(*results)
        return results
    
    def _execute_conditional(self, tree: Dict, *args, **kwargs) -> Any:
        """Execute conditional composition."""
        predicate_result = self._execute_ref(tree['predicate'], *args, **kwargs)
        
        if predicate_result:
            return self._execute_ref(tree['if_true'], *args, **kwargs)
        else:
            return self._execute_ref(tree['if_false'], *args, **kwargs)
    
    def _execute_threshold(self, tree: Dict, *args, **kwargs) -> Any:
        """Execute threshold composition."""
        value = self._execute_ref(tree['operator'], *args, **kwargs)
        threshold = tree.get('threshold', 0)
        comparison = tree.get('comparison', 'greater_than')
        
        comp_prim = self.seeds.get(comparison)
        if comp_prim:
            return comp_prim(value, threshold)
        return value > threshold
    
    def _execute_diff(self, tree: Dict, *args, **kwargs) -> Any:
        """Execute differential composition (compare frames)."""
        # Get current and previous frames
        current_frame = self.seeds.call('get_frame')
        previous_frame = self.seeds.call('get_previous_frame')
        
        # Execute operator on both
        current_result = self._execute_ref(tree['operator'], current_frame, **kwargs)
        previous_result = self._execute_ref(tree['operator'], previous_frame, **kwargs)
        
        # Compute difference
        if isinstance(current_result, (int, float)) and isinstance(previous_result, (int, float)):
            return current_result - previous_result
        elif isinstance(current_result, list) and isinstance(previous_result, list):
            return [c for c in current_result if c not in previous_result]
        else:
            return current_result != previous_result
    
    def _execute_ref(self, ref: Dict, *args, **kwargs) -> Any:
        """Execute a reference (primitive or operator)."""
        ref_type = ref.get('type')
        
        if ref_type == 'primitive':
            prim_name = ref.get('name')
            if not prim_name:
                raise ValueError("Primitive reference missing 'name'")
            prim = self.seeds.get(str(prim_name))
            if prim:
                return prim(*args, **kwargs)
            raise ValueError(f"Unknown primitive: {prim_name}")
            
        elif ref_type == 'operator':
            op_id = ref.get('id')
            if not op_id:
                raise ValueError("Operator reference missing 'id'")
            op = self.get_operator(str(op_id))
            if op:
                return self._execute_tree(op.composition_tree, *args, **kwargs)
            raise ValueError(f"Unknown operator: {op_id}")
        
        else:
            raise ValueError(f"Unknown reference type: {ref_type}")
    
    # ======================================================================
    # REMIX / EVOLUTION
    # ======================================================================
    
    def remix(
        self,
        operator: Union[str, ComposedOperator],
        remix_type: str = "random",
        agent_id: Optional[str] = None
    ) -> Optional[ComposedOperator]:
        """
        Generate a variation of an operator.
        
        Remix types:
        - random: Apply random mutation
        - simplify: Try to remove steps
        - strengthen: Add amplification
        - weaken: Add dampening
        - combine: Combine with another random operator
        
        Args:
            operator: Base operator to remix
            remix_type: Type of remix
            agent_id: Creating agent
            
        Returns:
            New remixed operator or None if remix failed
        """
        if isinstance(operator, str):
            op = self.get_operator(operator)
            if not op:
                return None
        else:
            op = operator
        
        # Deep copy the composition tree
        new_tree = copy.deepcopy(op.composition_tree)
        mutation_desc = ""
        
        if remix_type == "simplify":
            new_tree, mutation_desc = self._simplify_tree(new_tree)
        elif remix_type == "strengthen":
            new_tree, mutation_desc = self._strengthen_tree(new_tree)
        elif remix_type == "weaken":
            new_tree, mutation_desc = self._weaken_tree(new_tree)
        elif remix_type == "combine":
            # Get a random successful operator to combine with
            other = self._get_random_successful_operator(exclude_id=op.operator_id)
            if other:
                new_tree, mutation_desc = self._combine_trees(new_tree, other.composition_tree)
        else:
            # Random mutation
            new_tree, mutation_desc = self._random_mutate_tree(new_tree)
        
        # Create new operator
        new_id = f"remix_{uuid.uuid4().hex[:12]}"
        new_name = f"{op.name}_remix_{uuid.uuid4().hex[:4]}"
        
        remixed = ComposedOperator(
            operator_id=new_id,
            name=new_name,
            composition_tree=new_tree,
            input_types=op.input_types,
            output_type=op.output_type,
            created_by_agent=agent_id,
            parent_operators=[op.operator_id]
        )
        
        self._store_operator(remixed)
        
        # Record remix history
        self.db.execute_query("""
            INSERT INTO operator_remix_history
            (remix_id, parent_operator_id, child_operator_id, remix_type, mutation_description)
            VALUES (?, ?, ?, ?, ?)
        """, (
            f"remix_{uuid.uuid4().hex[:8]}", op.operator_id, new_id,
            remix_type, mutation_desc
        ))
        
        logger.debug(f"[CODS] Remixed {op.operator_id[:8]} -> {new_id[:8]} ({remix_type}: {mutation_desc})")
        
        return remixed
    
    def spawn_simplified_variants(
        self,
        operator: Union[str, ComposedOperator],
        num_variants: int = 4,
        agent_id: Optional[str] = None
    ) -> List[ComposedOperator]:
        """
        Generate simplified variants of a successful operator.
        
        Called after operator has ~100 wins to find minimal working version.
        
        Args:
            operator: Base operator to simplify
            num_variants: Number of variants to generate
            agent_id: Creating agent
            
        Returns:
            List of simplified variants
        """
        variants = []
        
        for _ in range(num_variants):
            variant = self.remix(operator, remix_type="simplify", agent_id=agent_id)
            if variant:
                variants.append(variant)
        
        logger.info(f"[CODS] Spawned {len(variants)} simplified variants")
        return variants
    
    def _simplify_tree(self, tree: Dict) -> Tuple[Dict, str]:
        """Try to remove steps from composition tree."""
        operators = tree.get('operators', [])
        
        if len(operators) <= 1:
            return tree, "already_minimal"
        
        # Try removing one step
        import random
        idx = random.randint(0, len(operators) - 1)
        removed = operators.pop(idx)
        
        return tree, f"removed_step_{idx}"
    
    def _strengthen_tree(self, tree: Dict) -> Tuple[Dict, str]:
        """Add amplification to tree."""
        # Wrap in amplification (multiply output by factor)
        return {
            'composition_type': CompositionType.COMPOSE.value,
            'operators': [
                tree,
                {'type': 'primitive', 'name': 'multiply'},
            ],
            'amplification_factor': 1.5
        }, "amplified_1.5x"
    
    def _weaken_tree(self, tree: Dict) -> Tuple[Dict, str]:
        """Add dampening to tree."""
        return {
            'composition_type': CompositionType.COMPOSE.value,
            'operators': [
                tree,
                {'type': 'primitive', 'name': 'multiply'},
            ],
            'amplification_factor': 0.5
        }, "dampened_0.5x"
    
    def _combine_trees(self, tree1: Dict, tree2: Dict) -> Tuple[Dict, str]:
        """Combine two trees in parallel."""
        return {
            'composition_type': CompositionType.PARALLEL.value,
            'operators': [
                {'type': 'tree', 'tree': tree1},
                {'type': 'tree', 'tree': tree2}
            ],
            'combiner': 'make_list'
        }, "parallel_combined"
    
    def _random_mutate_tree(self, tree: Dict) -> Tuple[Dict, str]:
        """Apply random mutation to tree."""
        mutations = ['swap_operator', 'add_threshold', 'add_conditional']
        mutation = mutations[hash(str(tree)) % len(mutations)]
        
        if mutation == 'add_threshold':
            # Wrap in threshold
            import random
            threshold = random.uniform(0.3, 0.7)
            return {
                'composition_type': CompositionType.THRESHOLD.value,
                'operator': tree,
                'threshold': threshold,
                'comparison': 'greater_than'
            }, f"added_threshold_{threshold:.2f}"
        
        return tree, "no_mutation"
    
    def _get_random_successful_operator(
        self,
        min_success_rate: float = 0.6,
        exclude_id: Optional[str] = None
    ) -> Optional[ComposedOperator]:
        """Get a random successful operator."""
        query = """
            SELECT * FROM composed_operators
            WHERE status IN ('validated', 'solid', 'canonical')
            AND success_rate >= ?
        """
        params: list[Any] = [min_success_rate]
        
        if exclude_id:
            query += " AND operator_id != ?"
            params.append(exclude_id)
        
        query += " ORDER BY RANDOM() LIMIT 1"
        
        results = self.db.execute_query(query, tuple(params))
        if results:
            return self._row_to_operator(results[0])
        return None
    
    # ======================================================================
    # VALIDATION & TESTING
    # ======================================================================
    
    def record_test_result(
        self,
        operator_id: str,
        game_id: str,
        success: bool,
        output_value: Any = None,
        execution_time_ms: float = 0,
        error_message: Optional[str] = None,
        level_number: int = 1,
        agent_id: Optional[str] = None,
        generation: int = 0,
        contributed_to_win: bool = False,
        score_before: float = 0,
        score_after: float = 0
    ):
        """Record a test result for an operator."""
        test_id = f"test_{uuid.uuid4().hex[:12]}"
        
        self.db.execute_query("""
            INSERT INTO operator_test_results
            (test_id, operator_id, game_id, level_number, agent_id, generation,
             success, output_value, execution_time_ms, error_message,
             contributed_to_win, score_before, score_after)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            test_id, operator_id, game_id, level_number, agent_id, generation,
            success, json.dumps(output_value, default=str) if output_value else None,
            execution_time_ms, error_message, contributed_to_win,
            score_before, score_after
        ))
        
        # Update operator stats
        self._update_operator_stats(operator_id)
    
    def _update_operator_stats(self, operator_id: str):
        """Update operator statistics from test results."""
        results = self.db.execute_query("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes,
                COUNT(DISTINCT game_id) as games_tested
            FROM operator_test_results
            WHERE operator_id = ?
        """, (operator_id,))
        
        if results:
            total = results[0]['total'] or 0
            successes = results[0]['successes'] or 0
            games = results[0]['games_tested'] or 0
            success_rate = successes / total if total > 0 else 0.0
            
            # Calculate cross-game rate (unique games with success / total unique games)
            cross_game = self.db.execute_query("""
                SELECT 
                    COUNT(DISTINCT game_id) as games_with_success
                FROM operator_test_results
                WHERE operator_id = ? AND success = 1
            """, (operator_id,))
            
            cross_game_rate = 0.0
            if cross_game and games > 0:
                cross_game_rate = (cross_game[0]['games_with_success'] or 0) / games
            
            # Determine status
            status = 'cobbled'
            if total >= 5:
                status = 'tested'
            if total >= 20 and success_rate >= 0.7:
                status = 'validated'
            if total >= 50 and success_rate >= 0.8 and cross_game_rate >= 0.6:
                status = 'solid'
            if total >= 100 and success_rate >= 0.9 and cross_game_rate >= 0.7:
                status = 'canonical'
            
            self.db.execute_query("""
                UPDATE composed_operators
                SET times_tested = ?,
                    successes = ?,
                    success_rate = ?,
                    cross_game_rate = ?,
                    status = ?,
                    last_tested_at = CURRENT_TIMESTAMP
                WHERE operator_id = ?
            """, (total, successes, success_rate, cross_game_rate, status, operator_id))
    
    # ======================================================================
    # STORAGE & RETRIEVAL
    # ======================================================================
    
    def _store_operator(self, operator: ComposedOperator):
        """Store an operator in the database."""
        self.db.execute_query("""
            INSERT OR REPLACE INTO composed_operators
            (operator_id, name, composition_tree, composition_type, input_types,
             output_type, status, created_by_agent, parent_operators)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            operator.operator_id,
            operator.name,
            json.dumps(operator.composition_tree, default=str),
            operator.composition_tree.get('composition_type', 'compose'),
            json.dumps(operator.input_types),
            operator.output_type,
            operator.status.value,
            operator.created_by_agent,
            json.dumps(operator.parent_operators)
        ))
    
    def get_operator(self, operator_id: str) -> Optional[ComposedOperator]:
        """Get an operator by ID."""
        results = self.db.execute_query(
            "SELECT * FROM composed_operators WHERE operator_id = ?",
            (operator_id,)
        )
        if results:
            return self._row_to_operator(results[0])
        return None
    
    def get_operator_by_name(self, name: str) -> Optional[ComposedOperator]:
        """Get an operator by name."""
        results = self.db.execute_query(
            "SELECT * FROM composed_operators WHERE name = ?",
            (name,)
        )
        if results:
            return self._row_to_operator(results[0])
        return None
    
    def _row_to_operator(self, row) -> ComposedOperator:
        """Convert database row to ComposedOperator."""
        return ComposedOperator(
            operator_id=row['operator_id'],
            name=row['name'],
            composition_tree=json.loads(row['composition_tree']),
            input_types=json.loads(row['input_types']) if row['input_types'] else [],
            output_type=row['output_type'] or 'any',
            status=OperatorStatus(row['status']),
            times_tested=row['times_tested'] or 0,
            successes=row['successes'] or 0,
            success_rate=row['success_rate'] or 0.0,
            cross_game_rate=row['cross_game_rate'] or 0.0,
            created_by_agent=row['created_by_agent'],
            created_at=row['created_at']
        )
    
    def list_operators(
        self,
        status: Optional[OperatorStatus] = None,
        min_success_rate: float = 0.0,
        limit: int = 50
    ) -> List[ComposedOperator]:
        """List operators by criteria."""
        query = "SELECT * FROM composed_operators WHERE success_rate >= ?"
        params: list[Any] = [min_success_rate]
        
        if status:
            query += " AND status = ?"
            params.append(status.value)
        
        query += " ORDER BY success_rate DESC LIMIT ?"
        params.append(limit)
        
        results = self.db.execute_query(query, tuple(params))
        return [self._row_to_operator(r) for r in results] if results else []
    
    def get_best_operators(self, n: int = 10) -> List[ComposedOperator]:
        """Get the top N performing operators."""
        return self.list_operators(
            status=None,
            min_success_rate=0.5,
            limit=n
        )
    
    # ======================================================================
    # HELPERS
    # ======================================================================
    
    def _generate_operator_name(self, tree: Dict) -> str:
        """Generate a name from composition tree."""
        operators = tree.get('operators', [])
        parts = []
        for op in operators[:3]:
            if op.get('type') == 'primitive':
                parts.append(op['name'][:4])
            elif op.get('type') == 'operator':
                parts.append('op')
        
        comp_type = tree.get('composition_type', 'comp')[:4]
        return f"{comp_type}_{'_'.join(parts)}"
    
    def _infer_input_types(self, first_ref: Optional[Dict]) -> List[str]:
        """Infer input types from first operator in chain."""
        if not first_ref:
            return ["any"]
        
        if first_ref.get('type') == 'primitive':
            prim = self.seeds.get(first_ref['name'])
            if prim:
                return prim.input_types
        
        return ["any"]
    
    def _infer_output_type(self, last_ref: Optional[Dict]) -> str:
        """Infer output type from last operator in chain."""
        if not last_ref:
            return "any"
        
        if last_ref.get('type') == 'primitive':
            prim = self.seeds.get(last_ref['name'])
            if prim:
                return prim.output_type
        
        return "any"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about composed operators."""
        stats = {}
        
        # Count by status
        status_counts = self.db.execute_query("""
            SELECT status, COUNT(*) as cnt
            FROM composed_operators
            GROUP BY status
        """)
        stats['by_status'] = {r['status']: r['cnt'] for r in status_counts} if status_counts else {}
        
        # Top performers
        top = self.db.execute_query("""
            SELECT name, success_rate, cross_game_rate, times_tested
            FROM composed_operators
            WHERE status IN ('validated', 'solid', 'canonical')
            ORDER BY success_rate DESC
            LIMIT 5
        """)
        stats['top_performers'] = [{k: row[k] for k in row.keys()} for row in top] if top else []
        
        # Total tests
        tests = self.db.execute_query("SELECT COUNT(*) as cnt FROM operator_test_results")
        stats['total_tests'] = tests[0]['cnt'] if tests else 0
        
        return stats
