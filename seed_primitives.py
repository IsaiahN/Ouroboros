import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

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
    # === ARC-SPECIFIC PERCEPTUAL PRIMITIVES ===
    PERCEPTUAL = "perceptual"         # Core ARC reasoning (templates, analogies, roles)


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
        
        # NEW: Detect ANY frame change at click location (not just movement)
        # This captures toggleable objects, color changes, state changes, etc.
        self._register(Primitive(
            name="detect_click_effect",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Detect any frame change caused by clicking at coordinates. Returns effect type and details.",
            func=self._detect_click_effect,
            input_types=["frame_before", "frame_after", "x", "y"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # NEW: Find all potentially controllable objects (for systematic discovery)
        self._register(Primitive(
            name="find_all_interactable_objects",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Find all objects that might be interactive (clickable, moveable, toggleable)",
            func=self._find_all_interactable_objects,
            input_types=["frame"],
            output_type="list",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # NEW: Find similar objects for symmetry testing
        self._register(Primitive(
            name="find_similar_objects",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Find all objects similar to reference (by color, shape, size)",
            func=self._find_similar_objects,
            input_types=["reference_obj", "frame", "criteria"],
            output_type="list",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # ==================================================================
        # PATTERN MATCHING PRIMITIVES - SEED (Core capability)
        # ==================================================================
        # Pattern matching is fundamental to intelligence - recognizing
        # similarities, differences, and regularities. Should always be available.
        # ==================================================================
        
        self._register(Primitive(
            name="pattern_matching",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Find matching patterns between two regions or objects. Returns similarity score and match details.",
            func=self._pattern_matching,
            input_types=["pattern", "frame"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="find_similar_objects",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Find all objects in frame similar to a reference object (same color, size, or shape).",
            func=self._find_similar_objects,
            input_types=["reference_object", "frame"],
            output_type="list",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="count_matching_objects",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Count objects matching a given color or property.",
            func=self._count_matching_objects,
            input_types=["frame", "color"],
            output_type="int",
            unlock_level="seed",
            piaget_stage="sensorimotor"
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
        
        # ==================================================================
        # ARC-SPECIFIC PERCEPTUAL PRIMITIVES (15 primitives) - ALL SEED
        # ==================================================================
        # These are the core perceptual capabilities needed for ARC reasoning.
        # All are seed primitives (default unlocked) because they represent
        # fundamental perceptual operations that agents need from the start.
        # ==================================================================
        
        self._register(Primitive(
            name="color_sampling",
            category=PrimitiveCategory.PERCEPTUAL,
            description="Query color at (x,y) or within a region. Returns color value(s).",
            func=self._color_sampling,
            input_types=["frame", "x", "y", "region"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="pattern_detection",
            category=PrimitiveCategory.PERCEPTUAL,
            description="Identify repeated structures, symmetries, checkerboards in frame.",
            func=self._pattern_detection,
            input_types=["frame"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="scale_measurement",
            category=PrimitiveCategory.PERCEPTUAL,
            description="Compare relative sizes of objects. Returns size ratios and comparisons.",
            func=self._scale_measurement,
            input_types=["frame", "object_a", "object_b"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="spatial_relationships",
            category=PrimitiveCategory.PERCEPTUAL,
            description="Determine which object is center/adjacent/inside another.",
            func=self._spatial_relationships,
            input_types=["frame", "object_a", "object_b"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="template_extraction",
            category=PrimitiveCategory.PERCEPTUAL,
            description="Treat one object as a rule/key for interpreting others.",
            func=self._template_extraction,
            input_types=["frame", "reference_region"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="analogical_mapping",
            category=PrimitiveCategory.PERCEPTUAL,
            description="'This is to that as X is to Y' reasoning. Map structural relationships.",
            func=self._analogical_mapping,
            input_types=["source_a", "source_b", "target_a"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="role_binding",
            category=PrimitiveCategory.PERCEPTUAL,
            description="Assign semantic roles (primary/secondary, source/target) to objects.",
            func=self._role_binding,
            input_types=["frame", "objects"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="hierarchical_composition",
            category=PrimitiveCategory.PERCEPTUAL,
            description="Understanding nested or scaled patterns in the frame.",
            func=self._hierarchical_composition,
            input_types=["frame"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="color_substitution",
            category=PrimitiveCategory.PERCEPTUAL,
            description="Change colors while preserving spatial structure.",
            func=self._color_substitution,
            input_types=["frame", "color_map"],
            output_type="frame",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="pattern_replication",
            category=PrimitiveCategory.PERCEPTUAL,
            description="Copy structure from one region to another with transformations.",
            func=self._pattern_replication,
            input_types=["frame", "source_region", "target_region", "transform"],
            output_type="frame",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="functional_attribution",
            category=PrimitiveCategory.PERCEPTUAL,
            description="Detect if object might have special purpose/role in the system.",
            func=self._functional_attribution,
            input_types=["frame", "object_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="rule_detection",
            category=PrimitiveCategory.PERCEPTUAL,
            description="Detect if region encodes instructions rather than being an instance.",
            func=self._rule_detection,
            input_types=["frame", "region"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="metadata_recognition",
            category=PrimitiveCategory.PERCEPTUAL,
            description="Distinguish data vs metadata, example vs template, instance vs class, content vs legend.",
            func=self._metadata_recognition,
            input_types=["frame"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="complexity_signaling",
            category=PrimitiveCategory.PERCEPTUAL,
            description="Detect if unusual complexity/centrality/uniqueness indicates special status.",
            func=self._complexity_signaling,
            input_types=["frame", "object_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
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
    
    def _find_similar_objects(
        self,
        reference_obj: Dict[str, Any],
        frame: List[List[int]],
        criteria: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find all objects in frame similar to reference object.
        
        Used for property symmetry testing: If object A has property P,
        do all similar objects also have property P?
        
        Args:
            reference_obj: Object dict with 'color', 'shape', 'size', etc.
            frame: Frame to search
            criteria: Which properties to match (default: ['color'])
        
        Returns:
            List of similar object dicts with positions
        """
        if criteria is None:
            criteria = ['color']  # Default to color matching
        
        try:
            import numpy as np
            frame_arr = np.array(frame) if not isinstance(frame, np.ndarray) else frame
            
            # Get all distinct objects
            all_objects = self._find_distinct_objects(frame)
            
            ref_color = reference_obj.get('color')
            ref_shape = reference_obj.get('shape')
            ref_size = reference_obj.get('size')
            
            similar = []
            for obj in all_objects:
                is_similar = True
                
                if 'color' in criteria and ref_color is not None:
                    if obj.get('color') != ref_color:
                        is_similar = False
                
                if 'shape' in criteria and ref_shape is not None:
                    # Shape matching - check aspect ratio similarity
                    if abs(obj.get('aspect_ratio', 1.0) - ref_shape.get('aspect_ratio', 1.0)) > 0.3:
                        is_similar = False
                
                if 'size' in criteria and ref_size is not None:
                    # Size within 30% tolerance
                    obj_size = obj.get('size', 0)
                    if abs(obj_size - ref_size) / max(ref_size, 1) > 0.3:
                        is_similar = False
                
                if is_similar:
                    similar.append(obj)
            
            return similar
            
        except Exception as e:
            logger.debug(f"find_similar_objects failed: {e}")
            return []
    
    def _detect_click_effect(
        self,
        frame_before: List[List[int]],
        frame_after: List[List[int]],
        x: int,
        y: int
    ) -> Dict[str, Any]:
        """
        Detect any frame change caused by clicking at coordinates.
        
        This captures:
        - Color toggles (object changes color when clicked)
        - State changes (object appears/disappears)
        - Size changes (object grows/shrinks)
        - Movement (object moves when clicked)
        - Remote effects (clicking here changes something elsewhere)
        
        Returns:
            {
                'effect_detected': bool,
                'effect_type': 'toggle'|'move'|'appear'|'disappear'|'remote'|'none',
                'clicked_object': str or None,
                'color_before': int,
                'color_after': int,
                'affected_positions': List[Tuple[int, int]],
                'confidence': float
            }
        """
        result = {
            'effect_detected': False,
            'effect_type': 'none',
            'clicked_object': None,
            'color_before': 0,
            'color_after': 0,
            'affected_positions': [],
            'confidence': 0.0
        }
        
        if not frame_before or not frame_after:
            return result
        
        height = len(frame_before)
        width = len(frame_before[0]) if frame_before else 0
        
        if y >= height or x >= width:
            return result
        
        # Get color at click position before and after
        color_before = frame_before[y][x]
        color_after = frame_after[y][x]
        
        result['color_before'] = color_before
        result['color_after'] = color_after
        result['clicked_object'] = f"obj_{color_before}" if color_before != 0 else None
        
        # Detect all changed positions
        changed_positions = []
        for cy in range(height):
            for cx in range(width):
                if frame_before[cy][cx] != frame_after[cy][cx]:
                    changed_positions.append((cx, cy))
        
        result['affected_positions'] = changed_positions
        
        if not changed_positions:
            return result
        
        result['effect_detected'] = True
        
        # Determine effect type
        if color_before != color_after and color_before != 0 and color_after != 0:
            # Color changed at click position - this is a TOGGLE!
            result['effect_type'] = 'toggle'
            result['confidence'] = 0.9
        elif color_before != 0 and color_after == 0:
            # Object disappeared
            result['effect_type'] = 'disappear'
            result['confidence'] = 0.8
        elif color_before == 0 and color_after != 0:
            # Object appeared
            result['effect_type'] = 'appear'
            result['confidence'] = 0.8
        elif (x, y) not in changed_positions:
            # Click position didn't change but something else did - remote effect
            result['effect_type'] = 'remote'
            result['confidence'] = 0.7
        else:
            # Check for movement (same color at click position but object moved)
            obj_id = f"obj_{color_before}"
            movement = self._get_object_movement(obj_id, frame_before, frame_after)
            if movement != 'none':
                result['effect_type'] = 'move'
                result['confidence'] = 0.8
            else:
                result['effect_type'] = 'unknown'
                result['confidence'] = 0.5
        
        return result
    
    def _find_all_interactable_objects(
        self,
        frame: List[List[int]]
    ) -> List[Dict[str, Any]]:
        """
        Find all objects that might be interactive in the frame.
        
        This is the foundation for systematic object discovery.
        All non-background objects are potentially interactive until proven otherwise.
        
        Returns list of:
            {
                'object_id': str,
                'color': int,
                'centroid': Tuple[float, float],
                'positions': List[Tuple[int, int]],
                'size': int,
                'bounding_box': (min_x, min_y, max_x, max_y),
                'tested': False  # Will be updated during discovery
            }
        """
        objects = self._find_distinct_objects(frame)
        
        interactables = []
        for obj in objects:
            # Calculate bounding box
            positions = obj.get('positions', [])
            if not positions:
                continue
            
            xs = [p[0] for p in positions]
            ys = [p[1] for p in positions]
            bbox = (min(xs), min(ys), max(xs), max(ys))
            
            interactables.append({
                'object_id': obj['object_id'],
                'color': obj['color'],
                'centroid': obj['centroid'],
                'positions': positions[:20],  # Limit to save memory
                'size': len(positions),
                'bounding_box': bbox,
                'tested': False
            })
        
        return interactables
    
    # ======================================================================
    # PATTERN MATCHING PRIMITIVE IMPLEMENTATIONS
    # ======================================================================
    
    def _pattern_matching(
        self,
        pattern: Any,
        frame: List[List[int]]
    ) -> Dict[str, Any]:
        """
        Find matching patterns in a frame.
        
        Pattern can be:
        - A color (int): Find all occurrences of that color
        - A small grid (List[List[int]]): Find exact matches
        - An object dict: Find objects with matching properties
        
        Returns:
            {
                'matches': List of match locations,
                'similarity': float (0-1),
                'match_count': int,
                'match_type': 'color'|'grid'|'object'
            }
        """
        result = {
            'matches': [],
            'similarity': 0.0,
            'match_count': 0,
            'match_type': 'unknown'
        }
        
        if not frame:
            return result
        
        height = len(frame)
        width = len(frame[0]) if frame else 0
        
        # Pattern is a color (int)
        if isinstance(pattern, int):
            result['match_type'] = 'color'
            matches = []
            for y in range(height):
                for x in range(width):
                    if frame[y][x] == pattern:
                        matches.append((x, y))
            result['matches'] = matches
            result['match_count'] = len(matches)
            result['similarity'] = 1.0 if matches else 0.0
            return result
        
        # Pattern is a small grid (exact matching)
        if isinstance(pattern, list) and pattern and isinstance(pattern[0], list):
            result['match_type'] = 'grid'
            p_height = len(pattern)
            p_width = len(pattern[0]) if pattern else 0
            
            matches = []
            for start_y in range(height - p_height + 1):
                for start_x in range(width - p_width + 1):
                    # Check if pattern matches at this position
                    is_match = True
                    for py in range(p_height):
                        for px in range(p_width):
                            if frame[start_y + py][start_x + px] != pattern[py][px]:
                                is_match = False
                                break
                        if not is_match:
                            break
                    if is_match:
                        matches.append((start_x, start_y))
            
            result['matches'] = matches
            result['match_count'] = len(matches)
            result['similarity'] = 1.0 if matches else 0.0
            return result
        
        # Pattern is an object dict (match by properties)
        if isinstance(pattern, dict):
            result['match_type'] = 'object'
            target_color = pattern.get('color')
            target_size = pattern.get('size')
            
            objects = self._find_distinct_objects(frame)
            matches = []
            
            for obj in objects:
                score = 0.0
                checks = 0
                
                if target_color is not None:
                    checks += 1
                    if obj['color'] == target_color:
                        score += 1.0
                
                if target_size is not None:
                    checks += 1
                    # Allow 20% size variance
                    size_ratio = min(len(obj.get('positions', [])), target_size) / max(len(obj.get('positions', [])), target_size, 1)
                    if size_ratio > 0.8:
                        score += size_ratio
                
                if checks > 0 and score / checks > 0.8:
                    matches.append({
                        'object_id': obj['object_id'],
                        'centroid': obj['centroid'],
                        'similarity': score / checks
                    })
            
            result['matches'] = matches
            result['match_count'] = len(matches)
            result['similarity'] = max([m['similarity'] for m in matches]) if matches else 0.0
            return result
        
        return result
    
    def _find_similar_objects(
        self,
        reference_object: Dict[str, Any],
        frame: List[List[int]]
    ) -> List[Dict[str, Any]]:
        """
        Find all objects similar to a reference object.
        
        Similarity based on color, size, shape approximation.
        Useful for finding "all objects like this one" for puzzles.
        
        Returns list of similar objects with similarity scores.
        """
        if not frame or not reference_object:
            return []
        
        ref_color = reference_object.get('color')
        ref_size = len(reference_object.get('positions', []))
        
        objects = self._find_distinct_objects(frame)
        similar = []
        
        for obj in objects:
            # Skip if same object
            if obj.get('object_id') == reference_object.get('object_id'):
                continue
            
            similarity = 0.0
            
            # Color match (most important)
            if ref_color is not None and obj['color'] == ref_color:
                similarity += 0.5
            
            # Size similarity
            if ref_size > 0:
                obj_size = len(obj.get('positions', []))
                size_ratio = min(obj_size, ref_size) / max(obj_size, ref_size, 1)
                similarity += 0.3 * size_ratio
            
            # Aspect ratio similarity (shape approximation)
            ref_positions = reference_object.get('positions', [])
            obj_positions = obj.get('positions', [])
            
            if ref_positions and obj_positions:
                ref_xs = [p[0] for p in ref_positions]
                ref_ys = [p[1] for p in ref_positions]
                obj_xs = [p[0] for p in obj_positions]
                obj_ys = [p[1] for p in obj_positions]
                
                ref_aspect = (max(ref_xs) - min(ref_xs) + 1) / max(max(ref_ys) - min(ref_ys) + 1, 1)
                obj_aspect = (max(obj_xs) - min(obj_xs) + 1) / max(max(obj_ys) - min(obj_ys) + 1, 1)
                
                aspect_ratio = min(ref_aspect, obj_aspect) / max(ref_aspect, obj_aspect, 0.1)
                similarity += 0.2 * aspect_ratio
            
            if similarity > 0.3:
                similar.append({
                    'object_id': obj['object_id'],
                    'color': obj['color'],
                    'centroid': obj['centroid'],
                    'size': len(obj.get('positions', [])),
                    'similarity': similarity
                })
        
        # Sort by similarity
        similar.sort(key=lambda x: x['similarity'], reverse=True)
        return similar
    
    def _count_matching_objects(
        self,
        frame: List[List[int]],
        color: int
    ) -> int:
        """
        Count distinct objects of a specific color.
        
        This is useful for puzzle games where you need to count
        how many tiles/objects of a certain type exist.
        """
        if not frame:
            return 0
        
        objects = self._find_distinct_objects(frame)
        count = 0
        
        for obj in objects:
            if obj['color'] == color:
                count += 1
        
        return count
    
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
    # ARC-SPECIFIC PERCEPTUAL PRIMITIVE IMPLEMENTATIONS
    # ======================================================================
    # These implement the core perceptual operations for ARC reasoning.
    # All are seed primitives - available by default to all agents.
    # ======================================================================
    
    def _color_sampling(
        self,
        frame: List[List[int]],
        x: Optional[int] = None,
        y: Optional[int] = None,
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> Dict[str, Any]:
        """
        Query color at (x,y) or within a region.
        
        Returns:
            {
                'point_color': int if x,y provided,
                'region_colors': Dict[int, int] if region provided (color -> count),
                'dominant_color': int (most common),
                'unique_colors': List[int]
            }
        """
        result = {
            'point_color': None,
            'region_colors': {},
            'dominant_color': None,
            'unique_colors': []
        }
        
        if not frame or not frame[0]:
            return result
        
        height = len(frame)
        width = len(frame[0])
        
        # Point sampling
        if x is not None and y is not None:
            if 0 <= y < height and 0 <= x < width:
                result['point_color'] = frame[y][x]
        
        # Region sampling
        if region is not None:
            x1, y1, x2, y2 = region
            color_counts: Dict[int, int] = {}
            for ry in range(max(0, y1), min(height, y2 + 1)):
                for rx in range(max(0, x1), min(width, x2 + 1)):
                    c = frame[ry][rx]
                    color_counts[c] = color_counts.get(c, 0) + 1
            result['region_colors'] = color_counts
            if color_counts:
                result['dominant_color'] = max(color_counts, key=color_counts.get)
                result['unique_colors'] = list(color_counts.keys())
        else:
            # Sample whole frame
            color_counts: Dict[int, int] = {}
            for row in frame:
                for c in row:
                    color_counts[c] = color_counts.get(c, 0) + 1
            result['region_colors'] = color_counts
            if color_counts:
                result['dominant_color'] = max(color_counts, key=color_counts.get)
                result['unique_colors'] = list(color_counts.keys())
        
        return result
    
    def _pattern_detection(
        self,
        frame: List[List[int]]
    ) -> Dict[str, Any]:
        """
        Identify repeated structures, symmetries, checkerboards in frame.
        
        Returns:
            {
                'has_horizontal_symmetry': bool,
                'has_vertical_symmetry': bool,
                'has_rotational_symmetry': bool,
                'has_checkerboard': bool,
                'repeating_units': List[Dict],
                'periodicity': Optional[Tuple[int, int]]
            }
        """
        result = {
            'has_horizontal_symmetry': False,
            'has_vertical_symmetry': False,
            'has_rotational_symmetry': False,
            'has_checkerboard': False,
            'repeating_units': [],
            'periodicity': None
        }
        
        if not frame or not frame[0]:
            return result
        
        height = len(frame)
        width = len(frame[0])
        
        # Check horizontal symmetry (left-right mirror)
        h_sym = True
        for y in range(height):
            for x in range(width // 2):
                if frame[y][x] != frame[y][width - 1 - x]:
                    h_sym = False
                    break
            if not h_sym:
                break
        result['has_horizontal_symmetry'] = h_sym
        
        # Check vertical symmetry (top-bottom mirror)
        v_sym = True
        for y in range(height // 2):
            if frame[y] != frame[height - 1 - y]:
                v_sym = False
                break
        result['has_vertical_symmetry'] = v_sym
        
        # Check 180-degree rotational symmetry
        rot_sym = True
        for y in range(height):
            for x in range(width):
                if frame[y][x] != frame[height - 1 - y][width - 1 - x]:
                    rot_sym = False
                    break
            if not rot_sym:
                break
        result['has_rotational_symmetry'] = rot_sym
        
        # Check for checkerboard pattern
        if height >= 2 and width >= 2:
            colors = set()
            is_checker = True
            for y in range(height):
                for x in range(width):
                    colors.add(frame[y][x])
                    expected_parity = (x + y) % 2
                    if len(colors) == 2:
                        c1, c2 = list(colors)
                        expected_color = c1 if expected_parity == 0 else c2
                        if frame[y][x] != expected_color and frame[y][x] != (c2 if expected_parity == 0 else c1):
                            is_checker = False
                            break
                if not is_checker:
                    break
            result['has_checkerboard'] = is_checker and len(colors) == 2
        
        # Detect periodicity (repeating pattern in x and y)
        for period_x in range(1, width // 2 + 1):
            if width % period_x == 0:
                is_periodic = True
                for y in range(height):
                    for x in range(width):
                        if frame[y][x] != frame[y][x % period_x]:
                            is_periodic = False
                            break
                    if not is_periodic:
                        break
                if is_periodic:
                    result['periodicity'] = (period_x, None)
                    break
        
        return result
    
    def _scale_measurement(
        self,
        frame: List[List[int]],
        object_a: Optional[Dict[str, Any]] = None,
        object_b: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Compare relative sizes of objects.
        
        Returns:
            {
                'size_a': int,
                'size_b': int,
                'ratio': float (a/b),
                'comparison': str ('larger', 'smaller', 'equal'),
                'scale_factor': float (approximate scaling)
            }
        """
        result = {
            'size_a': 0,
            'size_b': 0,
            'ratio': 1.0,
            'comparison': 'equal',
            'scale_factor': 1.0
        }
        
        if object_a:
            result['size_a'] = object_a.get('size', len(object_a.get('positions', [])))
        if object_b:
            result['size_b'] = object_b.get('size', len(object_b.get('positions', [])))
        
        if result['size_b'] > 0:
            result['ratio'] = result['size_a'] / result['size_b']
            result['scale_factor'] = result['ratio'] ** 0.5  # Square root for 2D scaling
            
            if result['ratio'] > 1.1:
                result['comparison'] = 'larger'
            elif result['ratio'] < 0.9:
                result['comparison'] = 'smaller'
            else:
                result['comparison'] = 'equal'
        
        return result
    
    def _spatial_relationships(
        self,
        frame: List[List[int]],
        object_a: Optional[Dict[str, Any]] = None,
        object_b: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Determine which object is center/adjacent/inside another.
        
        Returns:
            {
                'a_position': str ('center', 'corner', 'edge'),
                'relative_position': str ('above', 'below', 'left', 'right', 'inside', 'outside', 'overlapping'),
                'distance': float,
                'is_adjacent': bool,
                'is_contained': bool
            }
        """
        result = {
            'a_position': 'unknown',
            'relative_position': 'unknown',
            'distance': float('inf'),
            'is_adjacent': False,
            'is_contained': False
        }
        
        if not frame:
            return result
        
        height = len(frame)
        width = len(frame[0]) if frame else 0
        
        if object_a and 'centroid' in object_a:
            cx, cy = object_a['centroid']
            # Determine if center, corner, or edge
            center_x, center_y = width / 2, height / 2
            dist_to_center = ((cx - center_x) ** 2 + (cy - center_y) ** 2) ** 0.5
            max_dist = ((width/2) ** 2 + (height/2) ** 2) ** 0.5
            
            if dist_to_center < max_dist * 0.3:
                result['a_position'] = 'center'
            elif cx <= 1 or cx >= width - 2 or cy <= 1 or cy >= height - 2:
                if (cx <= 1 or cx >= width - 2) and (cy <= 1 or cy >= height - 2):
                    result['a_position'] = 'corner'
                else:
                    result['a_position'] = 'edge'
            else:
                result['a_position'] = 'interior'
        
        if object_a and object_b and 'centroid' in object_a and 'centroid' in object_b:
            ax, ay = object_a['centroid']
            bx, by = object_b['centroid']
            
            result['distance'] = ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5
            result['is_adjacent'] = result['distance'] < 3
            
            # Relative position
            dx = ax - bx
            dy = ay - by
            
            if abs(dx) > abs(dy):
                result['relative_position'] = 'right' if dx > 0 else 'left'
            else:
                result['relative_position'] = 'below' if dy > 0 else 'above'
            
            # Check containment
            if 'positions' in object_a and 'positions' in object_b:
                a_pos = set(object_a['positions'])
                b_pos = set(object_b['positions'])
                if a_pos.issubset(b_pos):
                    result['is_contained'] = True
                    result['relative_position'] = 'inside'
        
        return result
    
    def _template_extraction(
        self,
        frame: List[List[int]],
        reference_region: Optional[Tuple[int, int, int, int]] = None
    ) -> Dict[str, Any]:
        """
        Treat one object/region as a rule/key for interpreting others.
        
        Returns:
            {
                'template': List[List[int]] (extracted pattern),
                'template_size': Tuple[int, int],
                'color_mapping': Dict[int, str] (colors to roles),
                'structural_pattern': str
            }
        """
        result = {
            'template': [],
            'template_size': (0, 0),
            'color_mapping': {},
            'structural_pattern': 'unknown'
        }
        
        if not frame:
            return result
        
        if reference_region:
            x1, y1, x2, y2 = reference_region
            template = []
            for y in range(max(0, y1), min(len(frame), y2 + 1)):
                row = []
                for x in range(max(0, x1), min(len(frame[0]), x2 + 1)):
                    row.append(frame[y][x])
                template.append(row)
            result['template'] = template
            result['template_size'] = (len(template[0]) if template else 0, len(template))
            
            # Extract color roles
            colors_found = set()
            for row in template:
                colors_found.update(row)
            
            colors_sorted = sorted(colors_found)
            for i, c in enumerate(colors_sorted):
                if c == 0:
                    result['color_mapping'][c] = 'background'
                elif i == 1:
                    result['color_mapping'][c] = 'primary'
                elif i == 2:
                    result['color_mapping'][c] = 'secondary'
                else:
                    result['color_mapping'][c] = f'role_{i}'
        
        return result
    
    def _analogical_mapping(
        self,
        source_a: Any,
        source_b: Any,
        target_a: Any
    ) -> Dict[str, Any]:
        """
        'This is to that as X is to Y' reasoning.
        
        Returns:
            {
                'inferred_target_b': Any,
                'transformation_type': str,
                'confidence': float,
                'mapping': Dict
            }
        """
        result = {
            'inferred_target_b': None,
            'transformation_type': 'unknown',
            'confidence': 0.0,
            'mapping': {}
        }
        
        # Detect transformation between source_a and source_b
        if isinstance(source_a, int) and isinstance(source_b, int):
            # Color transformation
            diff = source_b - source_a
            result['transformation_type'] = 'color_shift'
            result['mapping'] = {'shift': diff}
            result['inferred_target_b'] = target_a + diff if isinstance(target_a, int) else target_a
            result['confidence'] = 0.8
        
        elif isinstance(source_a, dict) and isinstance(source_b, dict):
            # Object transformation
            if 'size' in source_a and 'size' in source_b:
                scale = source_b.get('size', 1) / max(source_a.get('size', 1), 1)
                result['transformation_type'] = 'scale'
                result['mapping'] = {'scale_factor': scale}
                result['confidence'] = 0.7
        
        return result
    
    def _role_binding(
        self,
        frame: List[List[int]],
        objects: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Assign semantic roles (primary/secondary, source/target) to objects.
        
        Returns:
            {
                'primary': object_id or None,
                'secondary': List[object_id],
                'source': object_id or None,
                'target': object_id or None,
                'reference': object_id or None,
                'roles': Dict[object_id, List[str]]
            }
        """
        result = {
            'primary': None,
            'secondary': [],
            'source': None,
            'target': None,
            'reference': None,
            'roles': {}
        }
        
        if not objects:
            objects = self._find_distinct_objects(frame) if frame else []
        
        if not objects:
            return result
        
        # Assign roles based on properties
        # Primary = largest or most central
        # Reference = smallest distinct object (might be legend/key)
        
        sorted_by_size = sorted(objects, key=lambda o: o.get('size', 0), reverse=True)
        
        if sorted_by_size:
            result['primary'] = sorted_by_size[0].get('color', 0)
            result['roles'][sorted_by_size[0].get('color', 0)] = ['primary']
            
            if len(sorted_by_size) > 1:
                result['secondary'] = [o.get('color', 0) for o in sorted_by_size[1:]]
                for o in sorted_by_size[1:]:
                    result['roles'][o.get('color', 0)] = ['secondary']
            
            # Smallest might be reference/legend
            smallest = sorted_by_size[-1]
            if smallest.get('size', 0) < sorted_by_size[0].get('size', 0) * 0.2:
                result['reference'] = smallest.get('color', 0)
                result['roles'][smallest.get('color', 0)].append('reference')
        
        return result
    
    def _hierarchical_composition(
        self,
        frame: List[List[int]]
    ) -> Dict[str, Any]:
        """
        Understanding nested or scaled patterns in the frame.
        
        Returns:
            {
                'nesting_levels': int,
                'nested_objects': List[Dict],
                'scaling_pattern': Optional[float],
                'composition_type': str ('nested', 'tiled', 'scaled', 'none')
            }
        """
        result = {
            'nesting_levels': 0,
            'nested_objects': [],
            'scaling_pattern': None,
            'composition_type': 'none'
        }
        
        if not frame or not frame[0]:
            return result
        
        objects = self._find_distinct_objects(frame)
        
        if len(objects) < 2:
            return result
        
        # Check for containment relationships
        for obj_a in objects:
            for obj_b in objects:
                if obj_a == obj_b:
                    continue
                a_pos = set(obj_a.get('positions', []))
                b_pos = set(obj_b.get('positions', []))
                
                # Check if b's bounding box contains a
                if 'bounding_box' in obj_b:
                    bx1, by1, bx2, by2 = obj_b['bounding_box']
                    a_centroid = obj_a.get('centroid', (0, 0))
                    if bx1 <= a_centroid[0] <= bx2 and by1 <= a_centroid[1] <= by2:
                        result['nesting_levels'] += 1
                        result['nested_objects'].append({
                            'outer': obj_b.get('color'),
                            'inner': obj_a.get('color')
                        })
        
        if result['nesting_levels'] > 0:
            result['composition_type'] = 'nested'
        
        # Check for tiling
        height = len(frame)
        width = len(frame[0])
        for tile_h in range(2, height // 2 + 1):
            for tile_w in range(2, width // 2 + 1):
                if height % tile_h == 0 and width % tile_w == 0:
                    # Check if tiles repeat
                    first_tile = [row[:tile_w] for row in frame[:tile_h]]
                    is_tiled = True
                    for ty in range(0, height, tile_h):
                        for tx in range(0, width, tile_w):
                            tile = [row[tx:tx+tile_w] for row in frame[ty:ty+tile_h]]
                            if tile != first_tile:
                                is_tiled = False
                                break
                        if not is_tiled:
                            break
                    if is_tiled:
                        result['composition_type'] = 'tiled'
                        result['scaling_pattern'] = (tile_w, tile_h)
                        return result
        
        return result
    
    def _color_substitution(
        self,
        frame: List[List[int]],
        color_map: Dict[int, int]
    ) -> List[List[int]]:
        """
        Change colors while preserving spatial structure.
        
        Returns: New frame with substituted colors.
        """
        if not frame:
            return frame
        
        new_frame = []
        for row in frame:
            new_row = [color_map.get(c, c) for c in row]
            new_frame.append(new_row)
        
        return new_frame
    
    def _pattern_replication(
        self,
        frame: List[List[int]],
        source_region: Tuple[int, int, int, int],
        target_region: Tuple[int, int, int, int],
        transform: Optional[str] = None
    ) -> List[List[int]]:
        """
        Copy structure from one region to another with optional transformations.
        
        Transform options: 'none', 'flip_h', 'flip_v', 'rotate_90', 'rotate_180'
        
        Returns: New frame with replicated pattern.
        """
        if not frame:
            return frame
        
        # Deep copy frame
        new_frame = [row[:] for row in frame]
        
        sx1, sy1, sx2, sy2 = source_region
        tx1, ty1, tx2, ty2 = target_region
        
        # Extract source pattern
        pattern = []
        for y in range(max(0, sy1), min(len(frame), sy2 + 1)):
            row = []
            for x in range(max(0, sx1), min(len(frame[0]), sx2 + 1)):
                row.append(frame[y][x])
            pattern.append(row)
        
        if not pattern:
            return new_frame
        
        # Apply transformation
        if transform == 'flip_h':
            pattern = [row[::-1] for row in pattern]
        elif transform == 'flip_v':
            pattern = pattern[::-1]
        elif transform == 'rotate_180':
            pattern = [row[::-1] for row in pattern[::-1]]
        elif transform == 'rotate_90':
            pattern = [[pattern[len(pattern)-1-j][i] for j in range(len(pattern))] for i in range(len(pattern[0]))]
        
        # Apply to target region
        ph = len(pattern)
        pw = len(pattern[0]) if pattern else 0
        
        for dy in range(min(ph, ty2 - ty1 + 1)):
            for dx in range(min(pw, tx2 - tx1 + 1)):
                ty = ty1 + dy
                tx = tx1 + dx
                if 0 <= ty < len(new_frame) and 0 <= tx < len(new_frame[0]):
                    new_frame[ty][tx] = pattern[dy][dx]
        
        return new_frame
    
    def _functional_attribution(
        self,
        frame: List[List[int]],
        object_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect if object might have special purpose/role in the system.
        
        Returns:
            {
                'is_special': bool,
                'possible_roles': List[str],
                'uniqueness_score': float,
                'centrality_score': float,
                'complexity_score': float
            }
        """
        result = {
            'is_special': False,
            'possible_roles': [],
            'uniqueness_score': 0.0,
            'centrality_score': 0.0,
            'complexity_score': 0.0
        }
        
        if not frame:
            return result
        
        objects = self._find_distinct_objects(frame)
        
        # Find the target object
        target_obj = None
        for obj in objects:
            if object_id and str(obj.get('color')) == object_id.replace('obj_', ''):
                target_obj = obj
                break
        
        if not target_obj:
            target_obj = objects[0] if objects else None
        
        if not target_obj:
            return result
        
        # Calculate uniqueness (how different from others)
        if len(objects) > 1:
            target_size = target_obj.get('size', 0)
            other_sizes = [o.get('size', 0) for o in objects if o != target_obj]
            avg_other_size = sum(other_sizes) / len(other_sizes) if other_sizes else target_size
            result['uniqueness_score'] = abs(target_size - avg_other_size) / max(avg_other_size, 1)
        
        # Calculate centrality
        if 'centroid' in target_obj:
            cx, cy = target_obj['centroid']
            center_x = len(frame[0]) / 2
            center_y = len(frame) / 2
            max_dist = ((center_x ** 2) + (center_y ** 2)) ** 0.5
            dist = ((cx - center_x) ** 2 + (cy - center_y) ** 2) ** 0.5
            result['centrality_score'] = 1.0 - (dist / max_dist)
        
        # Estimate complexity (edge count relative to size)
        if 'positions' in target_obj:
            positions = set(target_obj['positions'])
            edge_count = 0
            for x, y in positions:
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    if (x + dx, y + dy) not in positions:
                        edge_count += 1
            size = len(positions)
            result['complexity_score'] = edge_count / max(size * 4, 1)
        
        # Determine if special
        if result['uniqueness_score'] > 0.5 or result['centrality_score'] > 0.8:
            result['is_special'] = True
            if result['centrality_score'] > 0.8:
                result['possible_roles'].append('primary')
            if result['uniqueness_score'] > 0.7:
                result['possible_roles'].append('reference')
                result['possible_roles'].append('legend')
        
        return result
    
    def _rule_detection(
        self,
        frame: List[List[int]],
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> Dict[str, Any]:
        """
        Detect if region encodes instructions rather than being an instance.
        
        Returns:
            {
                'is_rule': bool,
                'rule_type': str ('legend', 'example', 'instruction', 'data'),
                'confidence': float,
                'indicators': List[str]
            }
        """
        result = {
            'is_rule': False,
            'rule_type': 'data',
            'confidence': 0.0,
            'indicators': []
        }
        
        if not frame:
            return result
        
        # Extract region or use whole frame
        if region:
            x1, y1, x2, y2 = region
            analysis_frame = [row[x1:x2+1] for row in frame[y1:y2+1]]
        else:
            analysis_frame = frame
        
        if not analysis_frame:
            return result
        
        # Indicators that suggest this is a rule/template:
        # 1. Small size relative to total
        # 2. Contains all colors present elsewhere
        # 3. Separated/isolated from main content
        # 4. High information density
        
        total_size = len(frame) * len(frame[0])
        region_size = len(analysis_frame) * len(analysis_frame[0]) if analysis_frame[0] else 0
        
        if region_size < total_size * 0.25:
            result['indicators'].append('small_relative_size')
            result['confidence'] += 0.2
        
        # Check color coverage
        region_colors = set()
        for row in analysis_frame:
            region_colors.update(row)
        
        frame_colors = set()
        for row in frame:
            frame_colors.update(row)
        
        if region_colors == frame_colors or frame_colors - region_colors == {0}:
            result['indicators'].append('contains_all_colors')
            result['confidence'] += 0.3
        
        # Check for isolation (surrounded by background)
        if region:
            x1, y1, x2, y2 = region
            is_isolated = True
            # Check borders
            if y1 > 0:
                for x in range(max(0, x1-1), min(len(frame[0]), x2+2)):
                    if frame[y1-1][x] != 0:
                        is_isolated = False
                        break
            if is_isolated:
                result['indicators'].append('isolated')
                result['confidence'] += 0.2
        
        if result['confidence'] >= 0.5:
            result['is_rule'] = True
            if 'contains_all_colors' in result['indicators']:
                result['rule_type'] = 'legend'
            elif 'small_relative_size' in result['indicators']:
                result['rule_type'] = 'example'
            else:
                result['rule_type'] = 'instruction'
        
        return result
    
    def _metadata_recognition(
        self,
        frame: List[List[int]]
    ) -> Dict[str, Any]:
        """
        Distinguish data vs metadata, example vs template, instance vs class.
        
        Returns:
            {
                'metadata_regions': List[Tuple[int, int, int, int]],
                'data_regions': List[Tuple[int, int, int, int]],
                'has_legend': bool,
                'has_example': bool,
                'classification': Dict[region -> type]
            }
        """
        result = {
            'metadata_regions': [],
            'data_regions': [],
            'has_legend': False,
            'has_example': False,
            'classification': {}
        }
        
        if not frame or not frame[0]:
            return result
        
        height = len(frame)
        width = len(frame[0])
        
        # Find connected regions
        objects = self._find_distinct_objects(frame)
        
        for obj in objects:
            if 'bounding_box' not in obj:
                continue
            
            bbox = obj['bounding_box']
            region = (bbox[0], bbox[1], bbox[2], bbox[3])
            
            # Analyze this region
            rule_info = self._rule_detection(frame, region)
            
            if rule_info['is_rule']:
                result['metadata_regions'].append(region)
                result['classification'][region] = rule_info['rule_type']
                if rule_info['rule_type'] == 'legend':
                    result['has_legend'] = True
                elif rule_info['rule_type'] == 'example':
                    result['has_example'] = True
            else:
                result['data_regions'].append(region)
                result['classification'][region] = 'data'
        
        return result
    
    def _complexity_signaling(
        self,
        frame: List[List[int]],
        object_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect if unusual complexity/centrality/uniqueness indicates special status.
        
        Returns:
            {
                'is_complex': bool,
                'complexity_rank': int (1 = most complex),
                'is_central': bool,
                'is_unique': bool,
                'signals_special_status': bool,
                'suggested_role': str
            }
        """
        result = {
            'is_complex': False,
            'complexity_rank': 0,
            'is_central': False,
            'is_unique': False,
            'signals_special_status': False,
            'suggested_role': 'normal'
        }
        
        if not frame:
            return result
        
        objects = self._find_distinct_objects(frame)
        
        if not objects:
            return result
        
        # Calculate complexity for each object
        complexities = []
        for obj in objects:
            func_attr = self._functional_attribution(frame, f"obj_{obj.get('color', 0)}")
            complexities.append({
                'object': obj,
                'complexity': func_attr['complexity_score'],
                'centrality': func_attr['centrality_score'],
                'uniqueness': func_attr['uniqueness_score']
            })
        
        # Sort by complexity
        complexities.sort(key=lambda x: x['complexity'], reverse=True)
        
        # Find target object
        target_idx = 0
        if object_id:
            for i, c in enumerate(complexities):
                if str(c['object'].get('color')) == object_id.replace('obj_', ''):
                    target_idx = i
                    break
        
        target = complexities[target_idx]
        result['complexity_rank'] = target_idx + 1
        result['is_complex'] = target['complexity'] > 0.5
        result['is_central'] = target['centrality'] > 0.7
        result['is_unique'] = target['uniqueness'] > 0.5
        
        # Determine if signals special status
        if result['is_complex'] and result['is_central']:
            result['signals_special_status'] = True
            result['suggested_role'] = 'primary'
        elif result['is_unique'] and not result['is_central']:
            result['signals_special_status'] = True
            result['suggested_role'] = 'reference'
        elif result['complexity_rank'] == 1:
            result['signals_special_status'] = True
            result['suggested_role'] = 'key'
        
        return result
    
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
