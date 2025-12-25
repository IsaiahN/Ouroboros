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
    OBJECT_INTERACTION = "object_interaction"  # Fundamental object-agent interaction
    # === NEW BABY-DERIVED PRIMITIVES (Phase 1-3) ===
    ATTENTION = "attention"           # What to process (novelty, change, contingency)
    AFFORDANCE = "affordance"         # What objects are FOR (movable, container, obstacle)
    SOCIAL_LEARNING = "social_learning"  # Learning from others (trust, imitation)
    MOTIVATION = "motivation"         # Explore/exploit drive (curiosity, competence)
    PHYSICS_PRIOR = "physics_prior"   # Weak expectations about physics (adjustable)
    QUANTITATIVE = "quantitative"     # Approximate numerosity (counting, comparing)
    METACOGNITION = "metacognition"   # Know what you know (confidence, stuck detection)
    NEGATIVE_SPACE = "negative_space" # Absence detection (holes, missing things)


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
    # === NEW: Unlock and Prior System ===
    unlock_level: str = "seed"  # "seed", "early", "late" (maps to Piaget stages)
    prior_strength: float = 1.0  # For physics priors: 0.0-1.0, adjustable
    piaget_stage: str = "sensorimotor"  # Stage where this unlocks
    
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
        
        # ==================================================================
        # OBJECT INTERACTION (6 primitives) - Fundamental object-agent sensing
        # ==================================================================
        # These are SEED primitives because even babies can:
        # - Pick up objects to see if they can control them
        # - Notice which objects move when they push
        # - Learn what they can and cannot control
        # This is pre-verbal, pre-learned fundamental cognition.
        # ==================================================================
        
        self._register(Primitive(
            name="test_object_control",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Test if an action causes a specific object to move. Returns (moved: bool, direction: str)",
            func=self._test_object_control,
            input_types=["object_position", "action", "frame_before", "frame_after"],
            output_type="tuple"
        ))
        
        self._register(Primitive(
            name="find_distinct_objects",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Find visually distinct objects in frame. Returns list of {color, positions, centroid}",
            func=self._find_distinct_objects,
            input_types=["frame"],
            output_type="list"
        ))
        
        self._register(Primitive(
            name="did_object_move",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Check if object at position moved between frames",
            func=self._did_object_move,
            input_types=["object_id", "frame_before", "frame_after"],
            output_type="bool"
        ))
        
        self._register(Primitive(
            name="get_object_movement",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Get movement direction of object between frames (up/down/left/right/none)",
            func=self._get_object_movement,
            input_types=["object_id", "frame_before", "frame_after"],
            output_type="string"
        ))
        
        self._register(Primitive(
            name="action_matches_movement",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Check if action direction matches object movement (e.g., ACTION1=up, object moved up)",
            func=self._action_matches_movement,
            input_types=["action", "movement_direction"],
            output_type="bool"
        ))
        
        self._register(Primitive(
            name="get_click_target",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Get object at click coordinates, if any",
            func=self._get_click_target,
            input_types=["frame", "x", "y"],
            output_type="object_id"
        ))
        
        # ==================================================================
        # PHASE 1: ATTENTION PRIMITIVES (5 primitives) - SEED
        # ==================================================================
        # Babies don't process everything equally - they have built-in
        # attention biases that direct learning toward informative signals.
        # Without attention primitives, agents treat all input equally.
        # ==================================================================
        
        self._register(Primitive(
            name="detect_change",
            category=PrimitiveCategory.ATTENTION,
            description="Detect regions that differ between two frames. Returns list of changed positions.",
            func=self._detect_change,
            input_types=["frame_before", "frame_after"],
            output_type="list",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_motion",
            category=PrimitiveCategory.ATTENTION,
            description="Detect objects that moved between frames. Returns list of moving object_ids.",
            func=self._detect_motion,
            input_types=["frame_before", "frame_after"],
            output_type="list",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_contingency",
            category=PrimitiveCategory.ATTENTION,
            description="Detect if action caused an observable effect. Critical for agency learning.",
            func=self._detect_contingency,
            input_types=["action", "frame_before", "frame_after"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="surprise_magnitude",
            category=PrimitiveCategory.ATTENTION,
            description="Measure how much observation violates prediction (0-1 scale).",
            func=self._surprise_magnitude,
            input_types=["predicted_frame", "actual_frame"],
            output_type="float",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="information_gain",
            category=PrimitiveCategory.ATTENTION,
            description="Estimate information value of an observation (novelty vs redundancy).",
            func=self._information_gain,
            input_types=["observation", "history"],
            output_type="float",
            unlock_level="early",
            piaget_stage="concrete_operational"
        ))
        
        # ==================================================================
        # PHASE 1: AFFORDANCE PRIMITIVES (7 primitives) - SEED/EARLY
        # ==================================================================
        # Babies perceive what objects are FOR, not just what they look like.
        # Affordances bridge perception and action.
        # ==================================================================
        
        self._register(Primitive(
            name="is_movable",
            category=PrimitiveCategory.AFFORDANCE,
            description="Check if object can be moved (responds to movement actions).",
            func=self._is_movable,
            input_types=["object_id", "control_history"],
            output_type="bool",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="is_obstacle",
            category=PrimitiveCategory.AFFORDANCE,
            description="Check if object blocks movement of other objects.",
            func=self._is_obstacle,
            input_types=["object_id", "frame"],
            output_type="bool",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="is_interactive",
            category=PrimitiveCategory.AFFORDANCE,
            description="Check if object responds to any action (click, movement, etc).",
            func=self._is_interactive,
            input_types=["object_id", "interaction_history"],
            output_type="bool",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="is_container",
            category=PrimitiveCategory.AFFORDANCE,
            description="Check if object can hold other objects (has enclosed space).",
            func=self._is_container,
            input_types=["object_id", "frame"],
            output_type="bool",
            unlock_level="early",
            piaget_stage="preoperational"
        ))
        
        self._register(Primitive(
            name="is_support",
            category=PrimitiveCategory.AFFORDANCE,
            description="Check if object can support other objects on top.",
            func=self._is_support,
            input_types=["object_id", "frame"],
            output_type="bool",
            unlock_level="early",
            piaget_stage="preoperational"
        ))
        
        self._register(Primitive(
            name="is_reference",
            category=PrimitiveCategory.AFFORDANCE,
            description="Check if object defines rules for other objects (template/pattern).",
            func=self._is_reference,
            input_types=["object_id", "frame", "rule_history"],
            output_type="bool",
            unlock_level="late",
            piaget_stage="formal_operational"
        ))
        
        self._register(Primitive(
            name="is_tool",
            category=PrimitiveCategory.AFFORDANCE,
            description="Check if object can be used to affect other objects.",
            func=self._is_tool,
            input_types=["object_id", "effect_history"],
            output_type="bool",
            unlock_level="late",
            piaget_stage="formal_operational"
        ))
        
        # ==================================================================
        # PHASE 1: SOCIAL LEARNING PRIMITIVES (4 primitives) - SEED
        # ==================================================================
        # Babies are social learning machines. Your viral package system
        # IS social learning - these primitives make it efficient.
        # ==================================================================
        
        self._register(Primitive(
            name="credibility_weighting",
            category=PrimitiveCategory.SOCIAL_LEARNING,
            description="Weight information by source reliability (prestige, success rate).",
            func=self._credibility_weighting,
            input_types=["source_id", "prestige", "success_rate"],
            output_type="float",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="demonstration_bias",
            category=PrimitiveCategory.SOCIAL_LEARNING,
            description="Prioritize trying actions that were demonstrated by successful agents.",
            func=self._demonstration_bias,
            input_types=["action", "demonstrated_actions", "demonstrator_success"],
            output_type="float",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="attention_following",
            category=PrimitiveCategory.SOCIAL_LEARNING,
            description="Attend to what successful agents attended to (shared attention).",
            func=self._attention_following,
            input_types=["focus_areas", "source_prestige"],
            output_type="list",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="teaching_detection",
            category=PrimitiveCategory.SOCIAL_LEARNING,
            description="Detect when information is intentionally pedagogical (Oracle hints).",
            func=self._teaching_detection,
            input_types=["information", "source_type"],
            output_type="bool",
            unlock_level="early",
            piaget_stage="concrete_operational"
        ))
        
        # ==================================================================
        # PHASE 1: MOTIVATION PRIMITIVES (4 primitives) - SEED
        # ==================================================================
        # Babies have intrinsic motivation systems - curiosity, competence.
        # This is the foundation of your dual-economy system.
        # ==================================================================
        
        self._register(Primitive(
            name="novelty_bonus",
            category=PrimitiveCategory.MOTIVATION,
            description="Calculate intrinsic reward for encountering new states.",
            func=self._novelty_bonus,
            input_types=["state", "state_history"],
            output_type="float",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="competence_signal",
            category=PrimitiveCategory.MOTIVATION,
            description="Calculate intrinsic reward for mastering difficult tasks.",
            func=self._competence_signal,
            input_types=["task_difficulty", "performance", "improvement_rate"],
            output_type="float",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="exploration_value",
            category=PrimitiveCategory.MOTIVATION,
            description="Estimate expected value of exploring unknown action/state.",
            func=self._exploration_value,
            input_types=["action", "uncertainty", "potential_reward"],
            output_type="float",
            unlock_level="early",
            piaget_stage="preoperational"
        ))
        
        self._register(Primitive(
            name="boredom_threshold",
            category=PrimitiveCategory.MOTIVATION,
            description="Detect when familiar activity becomes unrewarding (time to try something new).",
            func=self._boredom_threshold,
            input_types=["activity", "repetition_count", "reward_history"],
            output_type="bool",
            unlock_level="late",
            piaget_stage="concrete_operational"
        ))
        
        # ==================================================================
        # PHASE 1: QUANTITATIVE PRIMITIVES (4 primitives) - SEED/EARLY
        # ==================================================================
        # Babies have approximate number sense - not arithmetic, but
        # "more/less" and rough counting of small quantities.
        # ==================================================================
        
        self._register(Primitive(
            name="count_objects",
            category=PrimitiveCategory.QUANTITATIVE,
            description="Count distinct objects in region (approximate for large counts).",
            func=self._count_objects,
            input_types=["frame", "region"],
            output_type="int",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="compare_quantities",
            category=PrimitiveCategory.QUANTITATIVE,
            description="Compare two quantities: returns 'more', 'less', or 'equal'.",
            func=self._compare_quantities,
            input_types=["quantity_a", "quantity_b"],
            output_type="string",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_one_vs_many",
            category=PrimitiveCategory.QUANTITATIVE,
            description="Distinguish single object from multiple (singular vs plural).",
            func=self._detect_one_vs_many,
            input_types=["object_list"],
            output_type="string",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="one_to_one_match",
            category=PrimitiveCategory.QUANTITATIVE,
            description="Check if two sets have same count (foundation for pattern matching).",
            func=self._one_to_one_match,
            input_types=["set_a", "set_b"],
            output_type="bool",
            unlock_level="early",
            piaget_stage="preoperational"
        ))
        
        # ==================================================================
        # PHASE 2: PHYSICS PRIORS (5 primitives) - WEAK PRIORS
        # ==================================================================
        # Babies have expectations about physics that help them learn, but
        # ARC games can violate these. These are WEAK priors that can be
        # overridden by evidence - not hard constraints.
        # ==================================================================
        
        self._register(Primitive(
            name="solidity_bias",
            category=PrimitiveCategory.PHYSICS_PRIOR,
            description="Expect objects don't pass through each other (can be violated).",
            func=self._solidity_bias,
            input_types=["object_a", "object_b", "frame"],
            output_type="float",
            unlock_level="seed",
            prior_strength=0.3,  # Weak prior - many ARC games violate this
            piaget_stage="preoperational"
        ))
        
        self._register(Primitive(
            name="continuity_bias",
            category=PrimitiveCategory.PHYSICS_PRIOR,
            description="Expect objects move on continuous paths (not teleport).",
            func=self._continuity_bias,
            input_types=["object_id", "frame_before", "frame_after"],
            output_type="float",
            unlock_level="seed",
            prior_strength=0.4,  # Moderate - teleportation exists
            piaget_stage="preoperational"
        ))
        
        self._register(Primitive(
            name="gravity_bias",
            category=PrimitiveCategory.PHYSICS_PRIOR,
            description="Expect unsupported objects fall down.",
            func=self._gravity_bias,
            input_types=["object_id", "has_support", "frame"],
            output_type="float",
            unlock_level="seed",
            prior_strength=0.2,  # Very weak - many ARC games have no gravity
            piaget_stage="preoperational"
        ))
        
        self._register(Primitive(
            name="persistence_bias",
            category=PrimitiveCategory.PHYSICS_PRIOR,
            description="Expect objects continue to exist when not visible.",
            func=self._persistence_bias,
            input_types=["object_id", "last_seen_frame", "current_frame"],
            output_type="float",
            unlock_level="seed",
            prior_strength=0.5,  # Moderate - objects can disappear in games
            piaget_stage="preoperational"
        ))
        
        self._register(Primitive(
            name="contact_causality",
            category=PrimitiveCategory.PHYSICS_PRIOR,
            description="Expect objects only affect each other through contact.",
            func=self._contact_causality,
            input_types=["action_object", "affected_object", "distance"],
            output_type="float",
            unlock_level="early",
            prior_strength=0.4,  # Can be violated by action-at-distance
            piaget_stage="concrete_operational"
        ))
        
        # ==================================================================
        # PHASE 3: METACOGNITION PRIMITIVES (5 primitives) - STAGED UNLOCK
        # ==================================================================
        # Awareness of own knowing - maps directly to Piaget stages.
        # Formal Operational agents can reason about their reasoning.
        # ==================================================================
        
        self._register(Primitive(
            name="get_confidence",
            category=PrimitiveCategory.METACOGNITION,
            description="Estimate confidence in a prediction or decision (0-1).",
            func=self._get_confidence,
            input_types=["prediction", "evidence_count", "contradiction_count"],
            output_type="float",
            unlock_level="early",
            piaget_stage="preoperational"
        ))
        
        self._register(Primitive(
            name="detect_stuck",
            category=PrimitiveCategory.METACOGNITION,
            description="Detect if making progress or stuck in a loop.",
            func=self._detect_stuck,
            input_types=["progress_history", "action_history"],
            output_type="bool",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="strategy_effectiveness",
            category=PrimitiveCategory.METACOGNITION,
            description="Evaluate if current strategy is working (meta-reasoning).",
            func=self._strategy_effectiveness,
            input_types=["strategy", "outcomes", "time_invested"],
            output_type="float",
            unlock_level="late",
            piaget_stage="formal_operational"
        ))
        
        self._register(Primitive(
            name="get_knowledge_state",
            category=PrimitiveCategory.METACOGNITION,
            description="Assess what agent knows vs doesn't know about game.",
            func=self._get_knowledge_state,
            input_types=["game_type", "learned_rules", "uncertain_areas"],
            output_type="dict",
            unlock_level="late",
            piaget_stage="formal_operational"
        ))
        
        self._register(Primitive(
            name="estimate_learning_curve",
            category=PrimitiveCategory.METACOGNITION,
            description="Estimate how fast agent is learning this game.",
            func=self._estimate_learning_curve,
            input_types=["performance_history", "time_invested"],
            output_type="float",
            unlock_level="late",
            piaget_stage="formal_operational"
        ))
        
        # ==================================================================
        # PHASE 3: NEGATIVE SPACE PRIMITIVES (4 primitives) - EARLY UNLOCK
        # ==================================================================
        # Babies detect what's NOT there - holes, absences, missing things.
        # SP80 failed because system didn't perceive the HOLE.
        # ==================================================================
        
        self._register(Primitive(
            name="detect_enclosed_empty",
            category=PrimitiveCategory.NEGATIVE_SPACE,
            description="Find empty regions bounded by objects (container interiors).",
            func=self._detect_enclosed_empty,
            input_types=["frame"],
            output_type="list",
            unlock_level="early",
            piaget_stage="preoperational"
        ))
        
        self._register(Primitive(
            name="detect_open_edge",
            category=PrimitiveCategory.NEGATIVE_SPACE,
            description="Find container boundaries with missing walls (where things escape).",
            func=self._detect_open_edge,
            input_types=["container_positions", "frame"],
            output_type="list",
            unlock_level="early",
            piaget_stage="preoperational"
        ))
        
        self._register(Primitive(
            name="detect_absence",
            category=PrimitiveCategory.NEGATIVE_SPACE,
            description="Detect when expected object is missing from expected location.",
            func=self._detect_absence,
            input_types=["expected_object", "expected_position", "frame"],
            output_type="bool",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="negative_space_volume",
            category=PrimitiveCategory.NEGATIVE_SPACE,
            description="Calculate volume of empty space in a region.",
            func=self._negative_space_volume,
            input_types=["region", "frame"],
            output_type="int",
            unlock_level="late",
            piaget_stage="concrete_operational"
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
    # OBJECT INTERACTION IMPLEMENTATIONS
    # ======================================================================
    # These implement the fundamental "can I control this?" cognition
    # ======================================================================
    
    def _find_distinct_objects(self, frame: List[List[int]]) -> List[Dict[str, Any]]:
        """
        Find visually distinct objects in a frame.
        
        Objects are defined as connected regions of the same non-background color.
        Background is assumed to be color 0 (black).
        
        Returns list of objects with:
        - color: int (the color value)
        - positions: list of (x, y) tuples
        - centroid: (x, y) center of mass
        - object_id: unique identifier based on color
        """
        if not frame or not frame[0]:
            return []
        
        height = len(frame)
        width = len(frame[0])
        
        # Group pixels by color (excluding background 0)
        color_groups: Dict[int, List[Tuple[int, int]]] = {}
        
        for y in range(height):
            for x in range(width):
                color = frame[y][x]
                if color != 0:  # Skip background
                    if color not in color_groups:
                        color_groups[color] = []
                    color_groups[color].append((x, y))
        
        objects = []
        for color, positions in color_groups.items():
            if positions:
                # Calculate centroid
                cx = sum(p[0] for p in positions) / len(positions)
                cy = sum(p[1] for p in positions) / len(positions)
                
                objects.append({
                    'color': color,
                    'object_id': f"obj_{color}",
                    'positions': positions,
                    'centroid': (cx, cy),
                    'size': len(positions)
                })
        
        return objects
    
    def _did_object_move(
        self,
        object_id: str,
        frame_before: List[List[int]],
        frame_after: List[List[int]]
    ) -> bool:
        """Check if an object moved between frames."""
        # Extract color from object_id
        try:
            color = int(object_id.replace('obj_', ''))
        except:
            return False
        
        objects_before = self._find_distinct_objects(frame_before)
        objects_after = self._find_distinct_objects(frame_after)
        
        # Find object by color in both frames
        obj_before = next((o for o in objects_before if o['color'] == color), None)
        obj_after = next((o for o in objects_after if o['color'] == color), None)
        
        if not obj_before or not obj_after:
            return False  # Object appeared/disappeared
        
        # Check if centroid moved
        dx = abs(obj_after['centroid'][0] - obj_before['centroid'][0])
        dy = abs(obj_after['centroid'][1] - obj_before['centroid'][1])
        
        return dx > 0.5 or dy > 0.5  # Moved more than half a pixel
    
    def _get_object_movement(
        self,
        object_id: str,
        frame_before: List[List[int]],
        frame_after: List[List[int]]
    ) -> str:
        """
        Get the movement direction of an object.
        
        Returns: 'up', 'down', 'left', 'right', or 'none'
        """
        try:
            color = int(object_id.replace('obj_', ''))
        except:
            return 'none'
        
        objects_before = self._find_distinct_objects(frame_before)
        objects_after = self._find_distinct_objects(frame_after)
        
        obj_before = next((o for o in objects_before if o['color'] == color), None)
        obj_after = next((o for o in objects_after if o['color'] == color), None)
        
        if not obj_before or not obj_after:
            return 'none'
        
        dx = obj_after['centroid'][0] - obj_before['centroid'][0]
        dy = obj_after['centroid'][1] - obj_before['centroid'][1]
        
        # Determine primary direction
        if abs(dx) > abs(dy):
            return 'right' if dx > 0.5 else ('left' if dx < -0.5 else 'none')
        else:
            return 'down' if dy > 0.5 else ('up' if dy < -0.5 else 'none')
    
    def _action_matches_movement(self, action: int, movement_direction: str) -> bool:
        """
        Check if action direction matches object movement.
        
        ACTION1 = up (y decreases)
        ACTION2 = down (y increases)
        ACTION3 = left (x decreases)
        ACTION4 = right (x increases)
        """
        action_to_direction = {
            1: 'up',
            2: 'down',
            3: 'left',
            4: 'right'
        }
        
        expected = action_to_direction.get(action)
        return expected == movement_direction
    
    def _test_object_control(
        self,
        object_position: Tuple[int, int],
        action: int,
        frame_before: List[List[int]],
        frame_after: List[List[int]]
    ) -> Tuple[bool, str]:
        """
        Test if an action caused an object at position to move in the expected direction.
        
        This is THE fundamental "can I control this?" test:
        1. I see an object at position (x, y)
        2. I take action (e.g., ACTION1 = up)
        3. Did the object move up?
        4. If yes -> I control this object!
        
        Returns:
            (is_controlled: bool, movement_direction: str)
        """
        x, y = object_position
        
        # Get object at position before action
        if not frame_before or not frame_before[0]:
            return (False, 'none')
        
        if y >= len(frame_before) or x >= len(frame_before[0]):
            return (False, 'none')
        
        color = frame_before[y][x]
        if color == 0:
            return (False, 'none')  # Background, not an object
        
        object_id = f"obj_{color}"
        
        # Get movement
        movement = self._get_object_movement(object_id, frame_before, frame_after)
        
        # Check if action matches movement
        is_controlled = self._action_matches_movement(action, movement)
        
        return (is_controlled, movement)
    
    def _get_click_target(
        self,
        frame: List[List[int]],
        x: int,
        y: int
    ) -> Optional[str]:
        """
        Get the object at click coordinates.
        
        Returns object_id if there's a non-background object, None otherwise.
        """
        if not frame or not frame[0]:
            return None
        
        if y >= len(frame) or x >= len(frame[0]):
            return None
        
        color = frame[y][x]
        if color == 0:
            return None  # Background
        
        return f"obj_{color}"
    
    # ======================================================================
    # ATTENTION PRIMITIVE IMPLEMENTATIONS
    # ======================================================================
    
    def _detect_change(
        self,
        frame_before: List[List[int]],
        frame_after: List[List[int]]
    ) -> List[Tuple[int, int]]:
        """Detect positions where pixels changed between frames."""
        if not frame_before or not frame_after:
            return []
        
        changed = []
        height = min(len(frame_before), len(frame_after))
        width = min(len(frame_before[0]) if frame_before else 0,
                   len(frame_after[0]) if frame_after else 0)
        
        for y in range(height):
            for x in range(width):
                if frame_before[y][x] != frame_after[y][x]:
                    changed.append((x, y))
        
        return changed
    
    def _detect_motion(
        self,
        frame_before: List[List[int]],
        frame_after: List[List[int]]
    ) -> List[str]:
        """Detect objects that moved between frames."""
        objects_before = self._find_distinct_objects(frame_before)
        objects_after = self._find_distinct_objects(frame_after)
        
        moving_objects = []
        for obj_b in objects_before:
            color = obj_b['color']
            obj_a = next((o for o in objects_after if o['color'] == color), None)
            
            if obj_a:
                # Check if centroid moved
                dx = abs(obj_a['centroid'][0] - obj_b['centroid'][0])
                dy = abs(obj_a['centroid'][1] - obj_b['centroid'][1])
                if dx > 0.5 or dy > 0.5:
                    moving_objects.append(obj_b['object_id'])
        
        return moving_objects
    
    def _detect_contingency(
        self,
        action: int,
        frame_before: List[List[int]],
        frame_after: List[List[int]]
    ) -> Dict[str, Any]:
        """
        Detect if action caused an observable effect.
        
        Returns dict with:
        - caused_change: bool
        - affected_objects: list of object_ids
        - change_magnitude: float (0-1)
        """
        changed_positions = self._detect_change(frame_before, frame_after)
        moving_objects = self._detect_motion(frame_before, frame_after)
        
        # Calculate change magnitude (proportion of frame changed)
        if not frame_before or not frame_before[0]:
            magnitude = 0.0
        else:
            total_pixels = len(frame_before) * len(frame_before[0])
            magnitude = len(changed_positions) / total_pixels if total_pixels > 0 else 0.0
        
        return {
            'caused_change': len(changed_positions) > 0,
            'affected_objects': moving_objects,
            'change_magnitude': magnitude,
            'action': action
        }
    
    def _surprise_magnitude(
        self,
        predicted_frame: List[List[int]],
        actual_frame: List[List[int]]
    ) -> float:
        """
        Measure how much observation violates prediction.
        Returns 0-1 scale where 1 is maximum surprise.
        """
        if not predicted_frame or not actual_frame:
            return 0.5  # Uncertain
        
        changed = self._detect_change(predicted_frame, actual_frame)
        
        if not predicted_frame or not predicted_frame[0]:
            return 0.0
        
        total_pixels = len(predicted_frame) * len(predicted_frame[0])
        return min(1.0, len(changed) / max(total_pixels * 0.1, 1))  # Normalize
    
    def _information_gain(
        self,
        observation: Any,
        history: List[Any]
    ) -> float:
        """
        Estimate information value of observation.
        Novel observations have high information gain.
        """
        if not history:
            return 1.0  # First observation is maximally informative
        
        obs_sig = self._signature(observation)
        history_sigs = [self._signature(h) for h in history[-50:]]  # Last 50
        
        # Count how many times we've seen similar observations
        similar_count = sum(1 for h in history_sigs if h == obs_sig)
        
        # Diminishing returns for repeated observations
        return max(0.0, 1.0 - (similar_count / len(history_sigs)))
    
    # ======================================================================
    # AFFORDANCE PRIMITIVE IMPLEMENTATIONS
    # ======================================================================
    
    def _is_movable(
        self,
        object_id: str,
        control_history: List[Dict[str, Any]]
    ) -> bool:
        """Check if object has been observed to move in response to actions."""
        if not control_history:
            return False  # Unknown - needs testing
        
        for record in control_history:
            if record.get('object_id') == object_id and record.get('moved', False):
                return True
        return False
    
    def _is_obstacle(
        self,
        object_id: str,
        frame: List[List[int]]
    ) -> bool:
        """
        Heuristic: non-background objects that are large and static
        are likely obstacles.
        """
        objects = self._find_distinct_objects(frame)
        obj = next((o for o in objects if o['object_id'] == object_id), None)
        
        if not obj:
            return False
        
        # Large objects relative to frame are often obstacles
        if frame and frame[0]:
            total_pixels = len(frame) * len(frame[0])
            size_ratio = obj['size'] / total_pixels
            return size_ratio > 0.05  # More than 5% of frame
        return False
    
    def _is_interactive(
        self,
        object_id: str,
        interaction_history: List[Dict[str, Any]]
    ) -> bool:
        """Check if object has responded to any interaction."""
        if not interaction_history:
            return False
        
        for record in interaction_history:
            if record.get('object_id') == object_id:
                if record.get('responded', False):
                    return True
        return False
    
    def _is_container(
        self,
        object_id: str,
        frame: List[List[int]]
    ) -> bool:
        """
        Check if object forms a container (encloses empty space).
        Simple heuristic: check if object forms a U or O shape.
        """
        objects = self._find_distinct_objects(frame)
        obj = next((o for o in objects if o['object_id'] == object_id), None)
        
        if not obj or len(obj['positions']) < 3:
            return False
        
        positions = set(obj['positions'])
        
        # Check for enclosed empty space
        min_x = min(p[0] for p in positions)
        max_x = max(p[0] for p in positions)
        min_y = min(p[1] for p in positions)
        max_y = max(p[1] for p in positions)
        
        # Count interior empty pixels
        interior_empty = 0
        for y in range(min_y + 1, max_y):
            for x in range(min_x + 1, max_x):
                if (x, y) not in positions:
                    # Check if surrounded by object pixels
                    if ((x-1, y) in positions or (x+1, y) in positions) and \
                       ((x, y-1) in positions or (x, y+1) in positions):
                        interior_empty += 1
        
        return interior_empty > 0
    
    def _is_support(
        self,
        object_id: str,
        frame: List[List[int]]
    ) -> bool:
        """Check if object could support other objects (horizontal surface)."""
        objects = self._find_distinct_objects(frame)
        obj = next((o for o in objects if o['object_id'] == object_id), None)
        
        if not obj or len(obj['positions']) < 2:
            return False
        
        positions = obj['positions']
        
        # Check for horizontal alignment (multiple pixels at same y)
        y_counts = {}
        for x, y in positions:
            y_counts[y] = y_counts.get(y, 0) + 1
        
        max_horizontal = max(y_counts.values())
        return max_horizontal >= 2  # At least 2 pixels horizontally aligned
    
    def _is_reference(
        self,
        object_id: str,
        frame: List[List[int]],
        rule_history: List[Dict[str, Any]]
    ) -> bool:
        """
        Check if object defines rules for other objects.
        This is a sophisticated check - requires formal operational thinking.
        """
        if not rule_history:
            return False
        
        # Look for patterns where this object's properties predict other behaviors
        for record in rule_history:
            if record.get('reference_object') == object_id:
                if record.get('rule_confidence', 0) > 0.7:
                    return True
        return False
    
    def _is_tool(
        self,
        object_id: str,
        effect_history: List[Dict[str, Any]]
    ) -> bool:
        """Check if object has been used to affect other objects."""
        if not effect_history:
            return False
        
        for record in effect_history:
            if record.get('tool_object') == object_id:
                if record.get('caused_effect', False):
                    return True
        return False
    
    # ======================================================================
    # SOCIAL LEARNING PRIMITIVE IMPLEMENTATIONS
    # ======================================================================
    
    def _credibility_weighting(
        self,
        source_id: str,
        prestige: float,
        success_rate: float
    ) -> float:
        """Weight information by source reliability."""
        # Combine prestige and success rate
        # Prestige is social capital, success_rate is track record
        return (prestige * 0.4 + success_rate * 0.6)
    
    def _demonstration_bias(
        self,
        action: int,
        demonstrated_actions: List[int],
        demonstrator_success: float
    ) -> float:
        """
        Calculate bias toward demonstrated actions.
        Higher bias if action was demonstrated by successful agent.
        """
        if action not in demonstrated_actions:
            return 0.0
        
        # Count how many times action was demonstrated
        demo_count = demonstrated_actions.count(action)
        
        # Weight by demonstrator success
        return min(1.0, demo_count * 0.2 * demonstrator_success)
    
    def _attention_following(
        self,
        focus_areas: List[Tuple[int, int]],
        source_prestige: float
    ) -> List[Tuple[int, int]]:
        """
        Return focus areas weighted by source prestige.
        Higher prestige = more attention to those areas.
        """
        if source_prestige < 0.3:
            return []  # Ignore low-prestige sources
        
        return focus_areas  # Follow high-prestige attention
    
    def _teaching_detection(
        self,
        information: Dict[str, Any],
        source_type: str
    ) -> bool:
        """Detect if information is intentionally pedagogical."""
        # Oracle hints are always pedagogical
        if source_type == 'oracle':
            return True
        
        # Viral packages with high success are pedagogical
        if source_type == 'viral_package':
            return information.get('success_rate', 0) > 0.7
        
        # Network rules with high confidence are pedagogical
        if source_type == 'network_rule':
            return information.get('confidence', 0) > 0.8
        
        return False
    
    # ======================================================================
    # MOTIVATION PRIMITIVE IMPLEMENTATIONS
    # ======================================================================
    
    def _novelty_bonus(
        self,
        state: Any,
        state_history: List[Any]
    ) -> float:
        """Calculate intrinsic reward for novelty."""
        if not state_history:
            return 1.0  # First state is maximally novel
        
        state_sig = self._signature(state)
        
        # Count similar states in history
        similar = sum(1 for s in state_history[-100:] 
                     if self._signature(s) == state_sig)
        
        # Exponential decay with repetition
        return max(0.0, 1.0 * (0.8 ** similar))
    
    def _competence_signal(
        self,
        task_difficulty: float,
        performance: float,
        improvement_rate: float
    ) -> float:
        """
        Calculate intrinsic reward for competence.
        High reward when: difficult task + good performance + improving.
        """
        # Scale: difficulty * performance gives base competence
        base = task_difficulty * performance
        
        # Bonus for improvement
        improvement_bonus = max(0, improvement_rate) * 0.5
        
        return min(1.0, base + improvement_bonus)
    
    def _exploration_value(
        self,
        action: int,
        uncertainty: float,
        potential_reward: float
    ) -> float:
        """Estimate value of exploring an action."""
        # UCB-like: balance uncertainty and potential
        exploration_bonus = uncertainty * 0.5
        exploitation_value = potential_reward * 0.5
        
        return exploration_bonus + exploitation_value
    
    def _boredom_threshold(
        self,
        activity: str,
        repetition_count: int,
        reward_history: List[float]
    ) -> bool:
        """Detect when activity becomes unrewarding (bored)."""
        if repetition_count < 5:
            return False  # Need at least 5 repetitions
        
        if not reward_history:
            return repetition_count > 10
        
        # Check if recent rewards are declining
        recent = reward_history[-5:]
        if len(recent) < 3:
            return False
        
        avg_recent = sum(recent) / len(recent)
        return avg_recent < 0.2 and repetition_count > 10
    
    # ======================================================================
    # QUANTITATIVE PRIMITIVE IMPLEMENTATIONS
    # ======================================================================
    
    def _count_objects(
        self,
        frame: List[List[int]],
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> int:
        """
        Count distinct objects in frame or region.
        Region is (x1, y1, x2, y2) bounding box.
        """
        objects = self._find_distinct_objects(frame)
        
        if region is None:
            return len(objects)
        
        x1, y1, x2, y2 = region
        count = 0
        for obj in objects:
            cx, cy = obj['centroid']
            if x1 <= cx <= x2 and y1 <= cy <= y2:
                count += 1
        
        return count
    
    def _compare_quantities(
        self,
        quantity_a: int,
        quantity_b: int
    ) -> str:
        """Compare two quantities."""
        if quantity_a > quantity_b:
            return 'more'
        elif quantity_a < quantity_b:
            return 'less'
        else:
            return 'equal'
    
    def _detect_one_vs_many(
        self,
        object_list: List[Any]
    ) -> str:
        """Distinguish single from multiple."""
        if not object_list:
            return 'none'
        elif len(object_list) == 1:
            return 'one'
        else:
            return 'many'
    
    def _one_to_one_match(
        self,
        set_a: List[Any],
        set_b: List[Any]
    ) -> bool:
        """Check if two sets have same count."""
        return len(set_a) == len(set_b)
    
    # ======================================================================
    # PHYSICS PRIOR PRIMITIVE IMPLEMENTATIONS
    # ======================================================================
    
    def _solidity_bias(
        self,
        object_a: str,
        object_b: str,
        frame: List[List[int]]
    ) -> float:
        """
        Return expectation that objects don't overlap.
        Returns prior strength (0.3) if objects are separate,
        0.0 if they overlap (prior violated).
        """
        objects = self._find_distinct_objects(frame)
        obj_a = next((o for o in objects if o['object_id'] == object_a), None)
        obj_b = next((o for o in objects if o['object_id'] == object_b), None)
        
        if not obj_a or not obj_b:
            return 0.3  # Default prior
        
        # Check for position overlap
        pos_a = set(obj_a['positions'])
        pos_b = set(obj_b['positions'])
        
        if pos_a.intersection(pos_b):
            return 0.0  # Prior violated - objects overlap
        
        return 0.3  # Prior holds
    
    def _continuity_bias(
        self,
        object_id: str,
        frame_before: List[List[int]],
        frame_after: List[List[int]]
    ) -> float:
        """
        Return expectation that objects move continuously.
        Returns prior strength if movement is small,
        lower if object teleported.
        """
        objects_before = self._find_distinct_objects(frame_before)
        objects_after = self._find_distinct_objects(frame_after)
        
        obj_b = next((o for o in objects_before if o['object_id'] == object_id), None)
        obj_a = next((o for o in objects_after if o['object_id'] == object_id), None)
        
        if not obj_b or not obj_a:
            return 0.4  # Default prior
        
        # Calculate movement distance
        dx = abs(obj_a['centroid'][0] - obj_b['centroid'][0])
        dy = abs(obj_a['centroid'][1] - obj_b['centroid'][1])
        distance = (dx**2 + dy**2) ** 0.5
        
        # Large jumps violate continuity
        if distance > 5:  # More than 5 pixels = teleport
            return 0.1  # Prior weakly violated
        elif distance > 10:
            return 0.0  # Prior strongly violated
        
        return 0.4  # Prior holds
    
    def _gravity_bias(
        self,
        object_id: str,
        has_support: bool,
        frame: List[List[int]]
    ) -> float:
        """
        Return expectation that unsupported objects fall.
        Very weak prior (0.2) because many games have no gravity.
        """
        if has_support:
            return 0.2  # Supported = no expectation of falling
        
        # Unsupported = weak expectation of downward movement
        return 0.2  # Return prior strength (can be checked later)
    
    def _persistence_bias(
        self,
        object_id: str,
        last_seen_frame: List[List[int]],
        current_frame: List[List[int]]
    ) -> float:
        """
        Return expectation that objects persist.
        Returns prior strength if object still exists,
        lower if object disappeared.
        """
        objects_last = self._find_distinct_objects(last_seen_frame)
        objects_current = self._find_distinct_objects(current_frame)
        
        obj_last = next((o for o in objects_last if o['object_id'] == object_id), None)
        obj_current = next((o for o in objects_current if o['object_id'] == object_id), None)
        
        if obj_last and not obj_current:
            return 0.1  # Object disappeared - prior violated
        
        return 0.5  # Prior holds
    
    def _contact_causality(
        self,
        action_object: str,
        affected_object: str,
        distance: float
    ) -> float:
        """
        Return expectation that effects require contact.
        Lower if action-at-distance observed.
        """
        if distance < 2:  # Objects are in contact
            return 0.4  # Prior holds
        elif distance < 5:
            return 0.2  # Weak action-at-distance
        else:
            return 0.0  # Prior violated - action at distance
    
    # ======================================================================
    # METACOGNITION PRIMITIVE IMPLEMENTATIONS
    # ======================================================================
    
    def _get_confidence(
        self,
        prediction: Any,
        evidence_count: int,
        contradiction_count: int
    ) -> float:
        """Estimate confidence in prediction."""
        if evidence_count == 0:
            return 0.5  # No evidence = uncertain
        
        # Confidence increases with evidence, decreases with contradictions
        support_ratio = evidence_count / (evidence_count + contradiction_count + 1)
        
        # More evidence = more certainty (diminishing returns)
        certainty = 1 - (1 / (evidence_count + 1))
        
        return support_ratio * certainty
    
    def _detect_stuck(
        self,
        progress_history: List[float],
        action_history: List[int]
    ) -> bool:
        """Detect if agent is stuck (not making progress)."""
        if len(progress_history) < 5:
            return False
        
        # Check if progress has stalled
        recent_progress = progress_history[-5:]
        progress_variance = max(recent_progress) - min(recent_progress)
        
        # Check for action cycling
        if len(action_history) >= 10:
            recent_actions = action_history[-10:]
            unique_actions = len(set(recent_actions))
            if unique_actions <= 2 and progress_variance < 0.01:
                return True  # Cycling between same actions with no progress
        
        return progress_variance < 0.001  # Very low variance = stuck
    
    def _strategy_effectiveness(
        self,
        strategy: str,
        outcomes: List[float],
        time_invested: int
    ) -> float:
        """Evaluate if strategy is working."""
        if not outcomes or time_invested == 0:
            return 0.5  # Unknown
        
        avg_outcome = sum(outcomes) / len(outcomes)
        efficiency = avg_outcome / max(time_invested, 1)
        
        # Check trend
        if len(outcomes) >= 3:
            early = sum(outcomes[:len(outcomes)//2]) / max(len(outcomes)//2, 1)
            late = sum(outcomes[len(outcomes)//2:]) / max(len(outcomes) - len(outcomes)//2, 1)
            trend = late - early
        else:
            trend = 0
        
        return min(1.0, max(0.0, efficiency + trend * 0.5))
    
    def _get_knowledge_state(
        self,
        game_type: str,
        learned_rules: List[Dict[str, Any]],
        uncertain_areas: List[str]
    ) -> Dict[str, Any]:
        """Assess what agent knows vs doesn't know."""
        return {
            'game_type': game_type,
            'known_rules_count': len(learned_rules),
            'uncertain_count': len(uncertain_areas),
            'knowledge_coverage': len(learned_rules) / max(len(learned_rules) + len(uncertain_areas), 1),
            'uncertain_areas': uncertain_areas[:5]  # Top 5 uncertainties
        }
    
    def _estimate_learning_curve(
        self,
        performance_history: List[float],
        time_invested: int
    ) -> float:
        """Estimate learning speed."""
        if len(performance_history) < 2 or time_invested == 0:
            return 0.5  # Unknown
        
        # Calculate improvement rate
        if len(performance_history) >= 5:
            early = sum(performance_history[:3]) / 3
            late = sum(performance_history[-3:]) / 3
            improvement = late - early
        else:
            improvement = performance_history[-1] - performance_history[0]
        
        # Normalize by time
        learning_rate = improvement / max(time_invested, 1) * 100
        
        return min(1.0, max(0.0, 0.5 + learning_rate))
    
    # ======================================================================
    # NEGATIVE SPACE PRIMITIVE IMPLEMENTATIONS
    # ======================================================================
    
    def _detect_enclosed_empty(
        self,
        frame: List[List[int]]
    ) -> List[Dict[str, Any]]:
        """
        Find empty regions bounded by objects.
        Returns list of enclosed regions with positions.
        """
        if not frame or not frame[0]:
            return []
        
        height = len(frame)
        width = len(frame[0])
        
        # Find all background (0) pixels
        background = set()
        for y in range(height):
            for x in range(width):
                if frame[y][x] == 0:
                    background.add((x, y))
        
        # Flood fill from edges to find "outside" background
        outside = set()
        queue = []
        
        # Add edge pixels to queue
        for x in range(width):
            if (x, 0) in background:
                queue.append((x, 0))
            if (x, height-1) in background:
                queue.append((x, height-1))
        for y in range(height):
            if (0, y) in background:
                queue.append((0, y))
            if (width-1, y) in background:
                queue.append((width-1, y))
        
        # Flood fill
        while queue:
            x, y = queue.pop(0)
            if (x, y) in outside:
                continue
            if (x, y) not in background:
                continue
            
            outside.add((x, y))
            
            # Add neighbors
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    if (nx, ny) in background and (nx, ny) not in outside:
                        queue.append((nx, ny))
        
        # Enclosed = background - outside
        enclosed = background - outside
        
        if not enclosed:
            return []
        
        return [{'positions': list(enclosed), 'size': len(enclosed)}]
    
    def _detect_open_edge(
        self,
        container_positions: List[Tuple[int, int]],
        frame: List[List[int]]
    ) -> List[Dict[str, Any]]:
        """
        Find edges of container with gaps (where things can escape).
        """
        if not container_positions or not frame:
            return []
        
        positions = set(container_positions)
        
        # Find bounding box
        min_x = min(p[0] for p in positions)
        max_x = max(p[0] for p in positions)
        min_y = min(p[1] for p in positions)
        max_y = max(p[1] for p in positions)
        
        open_edges = []
        
        # Check bottom edge for gaps
        bottom_y = max_y
        bottom_row = [(x, bottom_y) for x in range(min_x, max_x + 1)]
        gaps_in_bottom = [(x, y) for x, y in bottom_row if (x, y) not in positions]
        if gaps_in_bottom:
            open_edges.append({
                'edge': 'bottom',
                'gaps': gaps_in_bottom,
                'gap_count': len(gaps_in_bottom)
            })
        
        # Check left edge
        left_col = [(min_x, y) for y in range(min_y, max_y + 1)]
        gaps_in_left = [(x, y) for x, y in left_col if (x, y) not in positions]
        if gaps_in_left:
            open_edges.append({
                'edge': 'left',
                'gaps': gaps_in_left,
                'gap_count': len(gaps_in_left)
            })
        
        # Check right edge
        right_col = [(max_x, y) for y in range(min_y, max_y + 1)]
        gaps_in_right = [(x, y) for x, y in right_col if (x, y) not in positions]
        if gaps_in_right:
            open_edges.append({
                'edge': 'right',
                'gaps': gaps_in_right,
                'gap_count': len(gaps_in_right)
            })
        
        return open_edges
    
    def _detect_absence(
        self,
        expected_object: str,
        expected_position: Tuple[int, int],
        frame: List[List[int]]
    ) -> bool:
        """Detect if expected object is missing from expected location."""
        if not frame:
            return True
        
        x, y = expected_position
        if y >= len(frame) or x >= len(frame[0]):
            return True  # Out of bounds = absent
        
        # Extract expected color from object_id
        try:
            expected_color = int(expected_object.replace('obj_', ''))
        except:
            return True  # Can't parse = assume absent
        
        actual_color = frame[y][x]
        
        return actual_color != expected_color
    
    def _negative_space_volume(
        self,
        region: Tuple[int, int, int, int],
        frame: List[List[int]]
    ) -> int:
        """Calculate empty space in region."""
        if not frame:
            return 0
        
        x1, y1, x2, y2 = region
        empty_count = 0
        
        for y in range(max(0, y1), min(len(frame), y2 + 1)):
            for x in range(max(0, x1), min(len(frame[0]), x2 + 1)):
                if frame[y][x] == 0:
                    empty_count += 1
        
        return empty_count
    
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
    
    def set_episode_context(self, episode_id: str, action_space: Optional[List[int]] = None):
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
    
    # ======================================================================
    # PIAGET STAGE INTEGRATION
    # ======================================================================
    
    def list_by_unlock_level(self, unlock_level: str) -> List[str]:
        """
        List primitives by unlock level.
        
        Args:
            unlock_level: "seed", "early", or "late"
            
        Returns:
            List of primitive names at that unlock level
        """
        return [
            name for name, p in self.primitives.items()
            if getattr(p, 'unlock_level', 'seed') == unlock_level
        ]
    
    def list_by_piaget_stage(self, stage: str) -> List[str]:
        """
        List primitives available at a Piaget cognitive stage.
        
        Args:
            stage: "sensorimotor", "preoperational", "concrete_operational", "formal_operational"
            
        Returns:
            List of primitive names available at or before that stage
        """
        stage_order = {
            'sensorimotor': 0,
            'preoperational': 1,
            'concrete_operational': 2,
            'formal_operational': 3
        }
        
        target_level = stage_order.get(stage, 0)
        
        return [
            name for name, p in self.primitives.items()
            if stage_order.get(getattr(p, 'piaget_stage', 'sensorimotor'), 0) <= target_level
        ]
    
    def get_primitives_for_agent(
        self,
        cognitive_stage: str,
        unlocked_primitives: Optional[List[str]] = None
    ) -> List[str]:
        """
        Get all primitives available to an agent based on cognitive stage
        and any specifically unlocked primitives.
        
        Args:
            cognitive_stage: Agent's current Piaget stage
            unlocked_primitives: Additional primitives explicitly unlocked
            
        Returns:
            List of available primitive names
        """
        # Start with stage-appropriate primitives
        available = set(self.list_by_piaget_stage(cognitive_stage))
        
        # Add explicitly unlocked
        if unlocked_primitives:
            available.update(unlocked_primitives)
        
        return list(available)
    
    def get_unlock_requirements(self, primitive_name: str) -> Dict[str, Any]:
        """
        Get the unlock requirements for a primitive.
        
        Returns:
            Dict with unlock_level, piaget_stage, prior_strength (for physics priors)
        """
        p = self.get(primitive_name)
        if not p:
            return {}
        
        return {
            'name': p.name,
            'unlock_level': getattr(p, 'unlock_level', 'seed'),
            'piaget_stage': getattr(p, 'piaget_stage', 'sensorimotor'),
            'prior_strength': getattr(p, 'prior_strength', 1.0),
            'category': p.category.value
        }
    
    def get_physics_priors(self) -> List[Dict[str, Any]]:
        """
        Get all physics prior primitives with their current strengths.
        These are weak priors that can be adjusted based on evidence.
        
        Returns:
            List of {name, prior_strength, description}
        """
        physics_primitives = self.list_by_category(PrimitiveCategory.PHYSICS_PRIOR)
        
        result = []
        for name in physics_primitives:
            p = self.get(name)
            if p:
                result.append({
                    'name': name,
                    'prior_strength': getattr(p, 'prior_strength', 0.5),
                    'description': p.description
                })
        return result
    
    def adjust_physics_prior(self, primitive_name: str, new_strength: float) -> bool:
        """
        Adjust the strength of a physics prior based on evidence.
        
        Args:
            primitive_name: Name of physics prior primitive
            new_strength: New strength value (0.0 to 1.0)
            
        Returns:
            True if adjusted, False if not a physics prior
        """
        p = self.get(primitive_name)
        if not p or p.category != PrimitiveCategory.PHYSICS_PRIOR:
            return False
        
        # Clamp to valid range
        p.prior_strength = max(0.0, min(1.0, new_strength))
        return True
    
    def get_primitive_inventory_by_stage(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Get a complete inventory organized by Piaget stage.
        
        Returns:
            {
                'sensorimotor': [{'name': 'x', 'category': 'y', 'description': 'z'}, ...],
                'preoperational': [...],
                'concrete_operational': [...],
                'formal_operational': [...]
            }
        """
        inventory = {
            'sensorimotor': [],
            'preoperational': [],
            'concrete_operational': [],
            'formal_operational': []
        }
        
        for name, p in self.primitives.items():
            stage = getattr(p, 'piaget_stage', 'sensorimotor')
            if stage in inventory:
                inventory[stage].append({
                    'name': name,
                    'category': p.category.value,
                    'description': p.description,
                    'unlock_level': getattr(p, 'unlock_level', 'seed')
                })
        
        return inventory
    
    def get_seed_primitive_count(self) -> int:
        """Get count of seed primitives (available at birth)."""
        return len(self.list_by_unlock_level('seed'))
    
    def get_early_unlock_count(self) -> int:
        """Get count of early unlock primitives (preoperational)."""
        return len(self.list_by_unlock_level('early'))
    
    def get_late_unlock_count(self) -> int:
        """Get count of late unlock primitives (formal operational)."""
        return len(self.list_by_unlock_level('late'))


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

def P(name: str) -> Optional[Primitive]:
    """Get primitive by name (shorthand)."""
    return get_seed_primitives().get(name)


def call(name: str, *args, **kwargs) -> Any:
    """Call primitive by name (shorthand)."""
    return get_seed_primitives().call(name, *args, **kwargs)
