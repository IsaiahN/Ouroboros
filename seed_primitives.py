"""
Seed Primitives - The ~50 atomic operations given at birth
==========================================================

These are the ONLY primitives the system starts with. All higher-level
operators must be DISCOVERED through composition and validated by RLVR.

Philosophy: A child doesn't learn gravity by being told "F = ma" - they drop
things, notice patterns, and EARN understanding. Same principle here.

Categories:
1. Raw Data Access - Get pixel/frame data
2. Basic Math - Arithmetic operations
3. Comparison - Boolean comparisons
4. Control Flow - Branching (if/else)
5. Data Structures - Lists and operations
6. Iteration - Loops and maps
7. Aggregation - Sum, max, min
8. Time/Episode - Temporal access
9. Action Introspection - Action space queries
10. RNG - Randomness
11. Hashing - Signatures

Rule 1: Disable pycache
Rule 10: Leverages existing structures where possible
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import random
import hashlib
import json
import numpy as np
from typing import List, Any, Dict, Optional, Callable, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum


class PrimitiveCategory(Enum):
    """Categories of seed primitives."""
    RAW_DATA = "raw_data"
    MATH = "math"
    COMPARISON = "comparison"
    CONTROL_FLOW = "control_flow"
    DATA_STRUCTURE = "data_structure"
    ITERATION = "iteration"
    AGGREGATION = "aggregation"
    TEMPORAL = "temporal"
    ACTION = "action"
    RNG = "rng"
    HASHING = "hashing"


@dataclass
class Primitive:
    """Represents a single primitive operation."""
    name: str
    category: PrimitiveCategory
    description: str
    func: Callable
    input_types: List[str]
    output_type: str
    is_seed: bool = True  # Seed primitives are always True
    
    def __call__(self, *args, **kwargs):
        """Execute the primitive."""
        return self.func(*args, **kwargs)
    
    def signature(self) -> str:
        """Get type signature as string."""
        inputs = ", ".join(self.input_types)
        return f"({inputs}) -> {self.output_type}"


class SeedPrimitiveRegistry:
    """
    Registry of all seed primitives.
    
    These are the ~50 atomic operations the system starts with.
    All must be present for the system to function - no unlocking needed.
    """
    
    def __init__(self):
        self.primitives: Dict[str, Primitive] = {}
        self._frame_cache: Dict[str, List[List[int]]] = {}
        self._action_history: List[int] = []
        self._step_index: int = 0
        self._episode_id: str = ""
        self._action_space: List[int] = [1, 2, 3, 4, 5, 6, 7]
        self._rng_seed: Optional[int] = None
        
        # Register all seed primitives
        self._register_all_primitives()
    
    def _register_all_primitives(self):
        """Register all ~50 seed primitives."""
        
        # ==================================================================
        # RAW DATA ACCESS (5 primitives)
        # ==================================================================
        
        self._register(Primitive(
            name="get_pixel",
            category=PrimitiveCategory.RAW_DATA,
            description="Get pixel value at (x, y) from frame",
            func=self._get_pixel,
            input_types=["frame", "int", "int"],
            output_type="int"
        ))
        
        self._register(Primitive(
            name="get_frame",
            category=PrimitiveCategory.RAW_DATA,
            description="Get current frame as 2D list",
            func=self._get_frame,
            input_types=[],
            output_type="frame"
        ))
        
        self._register(Primitive(
            name="get_previous_frame",
            category=PrimitiveCategory.RAW_DATA,
            description="Get previous frame for comparison",
            func=self._get_previous_frame,
            input_types=[],
            output_type="frame"
        ))
        
        self._register(Primitive(
            name="get_frame_size",
            category=PrimitiveCategory.RAW_DATA,
            description="Get frame dimensions (height, width)",
            func=self._get_frame_size,
            input_types=["frame"],
            output_type="tuple"
        ))
        
        self._register(Primitive(
            name="set_frame",
            category=PrimitiveCategory.RAW_DATA,
            description="Set current frame (for testing/simulation)",
            func=self._set_frame,
            input_types=["frame"],
            output_type="none"
        ))
        
        # ==================================================================
        # BASIC MATH (8 primitives)
        # ==================================================================
        
        self._register(Primitive(
            name="add",
            category=PrimitiveCategory.MATH,
            description="Add two numbers",
            func=lambda a, b: a + b,
            input_types=["number", "number"],
            output_type="number"
        ))
        
        self._register(Primitive(
            name="subtract",
            category=PrimitiveCategory.MATH,
            description="Subtract two numbers",
            func=lambda a, b: a - b,
            input_types=["number", "number"],
            output_type="number"
        ))
        
        self._register(Primitive(
            name="multiply",
            category=PrimitiveCategory.MATH,
            description="Multiply two numbers",
            func=lambda a, b: a * b,
            input_types=["number", "number"],
            output_type="number"
        ))
        
        self._register(Primitive(
            name="divide",
            category=PrimitiveCategory.MATH,
            description="Divide two numbers (safe division)",
            func=lambda a, b: a / b if b != 0 else 0,
            input_types=["number", "number"],
            output_type="number"
        ))
        
        self._register(Primitive(
            name="modulo",
            category=PrimitiveCategory.MATH,
            description="Modulo operation",
            func=lambda a, b: a % b if b != 0 else 0,
            input_types=["number", "number"],
            output_type="number"
        ))
        
        self._register(Primitive(
            name="abs",
            category=PrimitiveCategory.MATH,
            description="Absolute value",
            func=lambda x: abs(x),
            input_types=["number"],
            output_type="number"
        ))
        
        self._register(Primitive(
            name="neg",
            category=PrimitiveCategory.MATH,
            description="Negate a number",
            func=lambda x: -x,
            input_types=["number"],
            output_type="number"
        ))
        
        self._register(Primitive(
            name="floor",
            category=PrimitiveCategory.MATH,
            description="Floor of a number",
            func=lambda x: int(x) if x >= 0 else int(x) - 1,
            input_types=["number"],
            output_type="int"
        ))
        
        # ==================================================================
        # COMPARISON (7 primitives)
        # ==================================================================
        
        self._register(Primitive(
            name="equals",
            category=PrimitiveCategory.COMPARISON,
            description="Check equality",
            func=lambda a, b: a == b,
            input_types=["any", "any"],
            output_type="bool"
        ))
        
        self._register(Primitive(
            name="not_equals",
            category=PrimitiveCategory.COMPARISON,
            description="Check inequality",
            func=lambda a, b: a != b,
            input_types=["any", "any"],
            output_type="bool"
        ))
        
        self._register(Primitive(
            name="greater_than",
            category=PrimitiveCategory.COMPARISON,
            description="Check if a > b",
            func=lambda a, b: a > b,
            input_types=["number", "number"],
            output_type="bool"
        ))
        
        self._register(Primitive(
            name="less_than",
            category=PrimitiveCategory.COMPARISON,
            description="Check if a < b",
            func=lambda a, b: a < b,
            input_types=["number", "number"],
            output_type="bool"
        ))
        
        self._register(Primitive(
            name="greater_eq",
            category=PrimitiveCategory.COMPARISON,
            description="Check if a >= b",
            func=lambda a, b: a >= b,
            input_types=["number", "number"],
            output_type="bool"
        ))
        
        self._register(Primitive(
            name="less_eq",
            category=PrimitiveCategory.COMPARISON,
            description="Check if a <= b",
            func=lambda a, b: a <= b,
            input_types=["number", "number"],
            output_type="bool"
        ))
        
        self._register(Primitive(
            name="between",
            category=PrimitiveCategory.COMPARISON,
            description="Check if a is between b and c (inclusive)",
            func=lambda a, b, c: b <= a <= c,
            input_types=["number", "number", "number"],
            output_type="bool"
        ))
        
        # ==================================================================
        # CONTROL FLOW (3 primitives)
        # ==================================================================
        
        self._register(Primitive(
            name="if_else",
            category=PrimitiveCategory.CONTROL_FLOW,
            description="Return true_val if condition else false_val",
            func=lambda cond, true_val, false_val: true_val if cond else false_val,
            input_types=["bool", "any", "any"],
            output_type="any"
        ))
        
        self._register(Primitive(
            name="select",
            category=PrimitiveCategory.CONTROL_FLOW,
            description="Select from list by index",
            func=lambda lst, idx: lst[idx] if 0 <= idx < len(lst) else None,
            input_types=["list", "int"],
            output_type="any"
        ))
        
        self._register(Primitive(
            name="coalesce",
            category=PrimitiveCategory.CONTROL_FLOW,
            description="Return first non-None value",
            func=lambda *args: next((x for x in args if x is not None), None),
            input_types=["any..."],
            output_type="any"
        ))
        
        # ==================================================================
        # DATA STRUCTURES (9 primitives)
        # ==================================================================
        
        self._register(Primitive(
            name="make_list",
            category=PrimitiveCategory.DATA_STRUCTURE,
            description="Create a list from arguments",
            func=lambda *args: list(args),
            input_types=["any..."],
            output_type="list"
        ))
        
        self._register(Primitive(
            name="append",
            category=PrimitiveCategory.DATA_STRUCTURE,
            description="Append item to list (returns new list)",
            func=lambda lst, item: lst + [item],
            input_types=["list", "any"],
            output_type="list"
        ))
        
        self._register(Primitive(
            name="len",
            category=PrimitiveCategory.DATA_STRUCTURE,
            description="Get length of list",
            func=lambda lst: len(lst) if lst else 0,
            input_types=["list"],
            output_type="int"
        ))
        
        self._register(Primitive(
            name="get_at",
            category=PrimitiveCategory.DATA_STRUCTURE,
            description="Get item at index",
            func=lambda lst, idx: lst[idx] if lst and 0 <= idx < len(lst) else None,
            input_types=["list", "int"],
            output_type="any"
        ))
        
        self._register(Primitive(
            name="slice",
            category=PrimitiveCategory.DATA_STRUCTURE,
            description="Slice list from start to end",
            func=lambda lst, start, end: lst[start:end] if lst else [],
            input_types=["list", "int", "int"],
            output_type="list"
        ))
        
        self._register(Primitive(
            name="concat",
            category=PrimitiveCategory.DATA_STRUCTURE,
            description="Concatenate two lists",
            func=lambda a, b: (a or []) + (b or []),
            input_types=["list", "list"],
            output_type="list"
        ))
        
        self._register(Primitive(
            name="contains",
            category=PrimitiveCategory.DATA_STRUCTURE,
            description="Check if item is in list",
            func=lambda lst, item: item in lst if lst else False,
            input_types=["list", "any"],
            output_type="bool"
        ))
        
        self._register(Primitive(
            name="index_of",
            category=PrimitiveCategory.DATA_STRUCTURE,
            description="Find index of item in list (-1 if not found)",
            func=lambda lst, item: lst.index(item) if lst and item in lst else -1,
            input_types=["list", "any"],
            output_type="int"
        ))
        
        self._register(Primitive(
            name="unique",
            category=PrimitiveCategory.DATA_STRUCTURE,
            description="Get unique items from list",
            func=lambda lst: list(dict.fromkeys(lst)) if lst else [],
            input_types=["list"],
            output_type="list"
        ))
        
        # ==================================================================
        # ITERATION (7 primitives)
        # ==================================================================
        
        self._register(Primitive(
            name="for_each_pixel",
            category=PrimitiveCategory.ITERATION,
            description="Apply function to each pixel, return list of results",
            func=self._for_each_pixel,
            input_types=["frame", "function"],
            output_type="list"
        ))
        
        self._register(Primitive(
            name="for_range",
            category=PrimitiveCategory.ITERATION,
            description="Apply function to each number in range",
            func=lambda start, end, func: [func(i) for i in range(start, end)],
            input_types=["int", "int", "function"],
            output_type="list"
        ))
        
        self._register(Primitive(
            name="map",
            category=PrimitiveCategory.ITERATION,
            description="Apply function to each item in list",
            func=lambda lst, func: [func(x) for x in lst] if lst else [],
            input_types=["list", "function"],
            output_type="list"
        ))
        
        self._register(Primitive(
            name="filter",
            category=PrimitiveCategory.ITERATION,
            description="Filter list by predicate",
            func=lambda lst, pred: [x for x in lst if pred(x)] if lst else [],
            input_types=["list", "function"],
            output_type="list"
        ))
        
        self._register(Primitive(
            name="reduce",
            category=PrimitiveCategory.ITERATION,
            description="Reduce list with binary function",
            func=self._reduce,
            input_types=["list", "function", "any"],
            output_type="any"
        ))
        
        self._register(Primitive(
            name="any",
            category=PrimitiveCategory.ITERATION,
            description="Check if any item satisfies predicate",
            func=lambda lst, pred: any(pred(x) for x in lst) if lst else False,
            input_types=["list", "function"],
            output_type="bool"
        ))
        
        self._register(Primitive(
            name="all",
            category=PrimitiveCategory.ITERATION,
            description="Check if all items satisfy predicate",
            func=lambda lst, pred: all(pred(x) for x in lst) if lst else True,
            input_types=["list", "function"],
            output_type="bool"
        ))
        
        # ==================================================================
        # AGGREGATION (5 primitives)
        # ==================================================================
        
        self._register(Primitive(
            name="sum",
            category=PrimitiveCategory.AGGREGATION,
            description="Sum of list",
            func=lambda lst: sum(lst) if lst else 0,
            input_types=["list"],
            output_type="number"
        ))
        
        self._register(Primitive(
            name="max",
            category=PrimitiveCategory.AGGREGATION,
            description="Maximum of list",
            func=lambda lst: max(lst) if lst else None,
            input_types=["list"],
            output_type="number"
        ))
        
        self._register(Primitive(
            name="min",
            category=PrimitiveCategory.AGGREGATION,
            description="Minimum of list",
            func=lambda lst: min(lst) if lst else None,
            input_types=["list"],
            output_type="number"
        ))
        
        self._register(Primitive(
            name="average",
            category=PrimitiveCategory.AGGREGATION,
            description="Average of list",
            func=lambda lst: sum(lst) / len(lst) if lst else 0,
            input_types=["list"],
            output_type="number"
        ))
        
        self._register(Primitive(
            name="median",
            category=PrimitiveCategory.AGGREGATION,
            description="Median of list",
            func=self._median,
            input_types=["list"],
            output_type="number"
        ))
        
        # ==================================================================
        # TEMPORAL / EPISODE (4 primitives)
        # ==================================================================
        
        self._register(Primitive(
            name="get_step_index",
            category=PrimitiveCategory.TEMPORAL,
            description="Get current step/action index",
            func=lambda: self._step_index,
            input_types=[],
            output_type="int"
        ))
        
        self._register(Primitive(
            name="get_episode_id",
            category=PrimitiveCategory.TEMPORAL,
            description="Get current episode/game ID",
            func=lambda: self._episode_id,
            input_types=[],
            output_type="string"
        ))
        
        self._register(Primitive(
            name="get_action_count",
            category=PrimitiveCategory.TEMPORAL,
            description="Get number of actions taken so far",
            func=lambda: len(self._action_history),
            input_types=[],
            output_type="int"
        ))
        
        self._register(Primitive(
            name="get_elapsed_actions",
            category=PrimitiveCategory.TEMPORAL,
            description="Get actions taken since start",
            func=lambda: self._action_history.copy(),
            input_types=[],
            output_type="list"
        ))
        
        # ==================================================================
        # ACTION INTROSPECTION (4 primitives)
        # ==================================================================
        
        self._register(Primitive(
            name="get_action_space",
            category=PrimitiveCategory.ACTION,
            description="Get available actions [1-7]",
            func=lambda: self._action_space.copy(),
            input_types=[],
            output_type="list"
        ))
        
        self._register(Primitive(
            name="get_last_action",
            category=PrimitiveCategory.ACTION,
            description="Get the last action taken",
            func=lambda: self._action_history[-1] if self._action_history else None,
            input_types=[],
            output_type="int"
        ))
        
        self._register(Primitive(
            name="get_action_history",
            category=PrimitiveCategory.ACTION,
            description="Get full action history",
            func=lambda: self._action_history.copy(),
            input_types=[],
            output_type="list"
        ))
        
        self._register(Primitive(
            name="record_action",
            category=PrimitiveCategory.ACTION,
            description="Record an action taken",
            func=self._record_action,
            input_types=["int"],
            output_type="none"
        ))
        
        # ==================================================================
        # RANDOM NUMBER GENERATION (4 primitives)
        # ==================================================================
        
        self._register(Primitive(
            name="rand",
            category=PrimitiveCategory.RNG,
            description="Random float between 0 and 1",
            func=lambda: random.random(),
            input_types=[],
            output_type="float"
        ))
        
        self._register(Primitive(
            name="rand_int",
            category=PrimitiveCategory.RNG,
            description="Random integer between a and b (inclusive)",
            func=lambda a, b: random.randint(a, b),
            input_types=["int", "int"],
            output_type="int"
        ))
        
        self._register(Primitive(
            name="rand_choice",
            category=PrimitiveCategory.RNG,
            description="Random choice from list",
            func=lambda lst: random.choice(lst) if lst else None,
            input_types=["list"],
            output_type="any"
        ))
        
        self._register(Primitive(
            name="seed_rng",
            category=PrimitiveCategory.RNG,
            description="Seed the random number generator",
            func=self._seed_rng,
            input_types=["int"],
            output_type="none"
        ))
        
        # ==================================================================
        # HASHING / SIGNATURES (3 primitives)
        # ==================================================================
        
        self._register(Primitive(
            name="hash",
            category=PrimitiveCategory.HASHING,
            description="Hash any value to integer",
            func=lambda x: hash(str(x)) % (2**32),
            input_types=["any"],
            output_type="int"
        ))
        
        self._register(Primitive(
            name="hash_frame",
            category=PrimitiveCategory.HASHING,
            description="Hash a frame to signature",
            func=self._hash_frame,
            input_types=["frame"],
            output_type="string"
        ))
        
        self._register(Primitive(
            name="signature",
            category=PrimitiveCategory.HASHING,
            description="Create compact signature of value",
            func=self._signature,
            input_types=["any"],
            output_type="string"
        ))
    
    # ======================================================================
    # PRIMITIVE IMPLEMENTATION HELPERS
    # ======================================================================
    
    def _register(self, primitive: Primitive):
        """Register a primitive."""
        self.primitives[primitive.name] = primitive
    
    def _get_pixel(self, frame: List[List[int]], x: int, y: int) -> int:
        """Get pixel value at (x, y)."""
        if not frame or not frame[0]:
            return 0
        height = len(frame)
        width = len(frame[0])
        if 0 <= y < height and 0 <= x < width:
            return frame[y][x]
        return 0  # Out of bounds
    
    def _get_frame(self) -> List[List[int]]:
        """Get current frame."""
        return self._frame_cache.get('current', [[]])
    
    def _get_previous_frame(self) -> List[List[int]]:
        """Get previous frame."""
        return self._frame_cache.get('previous', [[]])
    
    def _get_frame_size(self, frame: List[List[int]]) -> Tuple[int, int]:
        """Get (height, width) of frame."""
        if not frame or not frame[0]:
            return (0, 0)
        return (len(frame), len(frame[0]))
    
    def _set_frame(self, frame: List[List[int]]) -> None:
        """Set current frame and move old to previous."""
        if 'current' in self._frame_cache:
            self._frame_cache['previous'] = self._frame_cache['current']
        self._frame_cache['current'] = frame
    
    def _for_each_pixel(self, frame: List[List[int]], func: Callable) -> List:
        """Apply function to each pixel."""
        if not frame or not frame[0]:
            return []
        results = []
        for y, row in enumerate(frame):
            for x, pixel in enumerate(row):
                results.append(func(x, y, pixel))
        return results
    
    def _reduce(self, lst: List, func: Callable, initial: Any) -> Any:
        """Reduce list with binary function."""
        if not lst:
            return initial
        result = initial
        for item in lst:
            result = func(result, item)
        return result
    
    def _median(self, lst: List) -> float:
        """Calculate median."""
        if not lst:
            return 0
        sorted_lst = sorted(lst)
        n = len(sorted_lst)
        mid = n // 2
        if n % 2 == 0:
            return (sorted_lst[mid - 1] + sorted_lst[mid]) / 2
        return sorted_lst[mid]
    
    def _record_action(self, action: int) -> None:
        """Record an action."""
        self._action_history.append(action)
        self._step_index += 1
    
    def _seed_rng(self, seed: int) -> None:
        """Seed the RNG."""
        self._rng_seed = seed
        random.seed(seed)
    
    def _hash_frame(self, frame: List[List[int]]) -> str:
        """Create hash signature for frame."""
        if not frame:
            return "empty"
        frame_bytes = json.dumps(frame, sort_keys=True).encode()
        return hashlib.md5(frame_bytes).hexdigest()[:16]
    
    def _signature(self, value: Any) -> str:
        """Create compact signature."""
        value_bytes = json.dumps(value, sort_keys=True, default=str).encode()
        return hashlib.md5(value_bytes).hexdigest()[:12]
    
    # ======================================================================
    # PUBLIC API
    # ======================================================================
    
    def get(self, name: str) -> Optional[Primitive]:
        """Get a primitive by name."""
        return self.primitives.get(name)
    
    def call(self, name: str, *args, **kwargs) -> Any:
        """Call a primitive by name."""
        primitive = self.get(name)
        if not primitive:
            raise ValueError(f"Unknown primitive: {name}")
        return primitive(*args, **kwargs)
    
    def list_all(self) -> List[str]:
        """List all primitive names."""
        return list(self.primitives.keys())
    
    def list_by_category(self, category: PrimitiveCategory) -> List[str]:
        """List primitives by category."""
        return [name for name, p in self.primitives.items() if p.category == category]
    
    def count(self) -> int:
        """Get total number of primitives."""
        return len(self.primitives)
    
    def set_episode_context(self, episode_id: str, action_space: List[int] = None):
        """Set episode context for temporal primitives."""
        self._episode_id = episode_id
        if action_space:
            self._action_space = action_space
    
    def reset_episode(self):
        """Reset episode state."""
        self._step_index = 0
        self._action_history = []
        self._frame_cache = {}
    
    def update_frame(self, frame: List[List[int]]):
        """Update current frame (convenience method)."""
        self.call('set_frame', frame)
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics about registered primitives."""
        stats = {'total': self.count()}
        for category in PrimitiveCategory:
            stats[category.value] = len(self.list_by_category(category))
        return stats


# ============================================================================
# GLOBAL SINGLETON
# ============================================================================

_registry: Optional[SeedPrimitiveRegistry] = None


def get_seed_primitives() -> SeedPrimitiveRegistry:
    """Get the global seed primitive registry."""
    global _registry
    if _registry is None:
        _registry = SeedPrimitiveRegistry()
    return _registry


def reset_seed_primitives():
    """Reset the global registry (useful for testing)."""
    global _registry
    _registry = None


# ============================================================================
# CONVENIENCE FUNCTIONS FOR DIRECT PRIMITIVE ACCESS
# ============================================================================

def P(name: str) -> Primitive:
    """Get primitive by name (shorthand)."""
    return get_seed_primitives().get(name)


def call(name: str, *args, **kwargs) -> Any:
    """Call primitive by name (shorthand)."""
    return get_seed_primitives().call(name, *args, **kwargs)
