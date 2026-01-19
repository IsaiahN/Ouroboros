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
    # === FUNDAMENTAL RELATIONAL PRIMITIVES ===
    SPATIAL = "spatial"               # Topological relationships (adjacency, connectivity, paths)
    PHYSICS = "physics"               # Support, constraint, and control relationships
    # === ADVANCED STRUCTURAL PRIMITIVES ===
    TOPOLOGY = "topology"             # Holes, cavities, connected components, boundary closure
    ALIGNMENT = "alignment"           # Parallel, perpendicular, colinear, facing direction
    SYMMETRY = "symmetry"             # Reflection, rotational, translational symmetry
    BOUNDARY = "boundary"             # Inside/outside, enclosure, convexity
    HIERARCHY = "hierarchy"           # Parent/child objects, composition, decomposition
    PERSISTENCE = "persistence"       # Object tracking, identity, creation/destruction
    RELATIONAL = "relational"         # Meta-queries on relationships
    SCALE = "scale"                   # Aggregation, subdivision, granularity
    # === ABSTRACT PHYSICAL PRIMITIVES (abstracted for grid worlds) ===
    FLOW = "flow"                     # Flow, transfer, filling, draining (abstracted)
    TRANSFORMATION = "transformation" # State changes, phase transitions, growth/decay
    CONSTRAINT = "constraint"         # Binding, tethering, modulation
    MATERIAL = "material"             # Friction, elasticity, porosity (abstracted)
    FORCE = "force"                   # Momentum, pressure, tension (abstracted)
    MECHANICAL = "mechanical"         # Hinges, levers, gears (abstracted linkages)
    DEFORMATION = "deformation"       # Stretching, bending, breaking
    PROBABILITY = "probability"       # Uncertainty, risk, confidence
    GOAL = "goal"                     # Intention, subgoals, achievement
    RESOURCE = "resource"             # Inventory, depletion, generation
    # === ADDITIONAL ABSTRACT PHYSICAL PRIMITIVES ===
    PENETRATION = "penetration"       # Piercing, passing through, projectiles
    SENSING = "sensing"               # Visibility, transparency, layering, occlusion
    TEXTURE = "texture"               # Surface patterns, gradients, regularity


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
        # Object tracking for persistence primitives
        self._object_history: Dict[str, Dict[str, Any]] = {}
        # Relation tracking for relational query primitives
        self._relation_history: Dict[str, List[Dict[str, Any]]] = {}
        
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
        # PHASE 0: NAVIGATION PRIMITIVES (5 primitives) - BIRTHRIGHT SEED
        # ==================================================================
        # Babies innately orient toward goals and explore space systematically.
        # These are BIRTHRIGHT primitives - always active, always used.
        # Without navigation, an agent that can move is useless.
        # ==================================================================
        
        self._register(Primitive(
            name="direction_to_goal",
            category=PrimitiveCategory.MOTIVATION,
            description="Get the action that moves toward a goal position. BIRTHRIGHT primitive.",
            func=self._direction_to_goal,
            input_types=["self_position", "goal_position"],
            output_type="string",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="systematic_exploration_direction",
            category=PrimitiveCategory.MOTIVATION,
            description="Get next direction to explore based on visited regions. BIRTHRIGHT primitive.",
            func=self._systematic_exploration_direction,
            input_types=["visited_positions", "frame_bounds", "current_position"],
            output_type="string",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="explore_toward_unexplored",
            category=PrimitiveCategory.MOTIVATION,
            description="Bias movement toward regions not yet visited. BIRTHRIGHT primitive.",
            func=self._explore_toward_unexplored,
            input_types=["current_position", "visited_set", "frame_bounds"],
            output_type="string",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="edge_exploration_needed",
            category=PrimitiveCategory.MOTIVATION,
            description="Check if map edges/boundaries need exploration. BIRTHRIGHT primitive.",
            func=self._edge_exploration_needed,
            input_types=["visited_positions", "frame_bounds"],
            output_type="bool",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="exploration_coverage",
            category=PrimitiveCategory.MOTIVATION,
            description="Calculate what percentage of map has been explored.",
            func=self._exploration_coverage,
            input_types=["visited_positions", "frame_bounds"],
            output_type="float",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # ==================================================================
        # PHASE 0: OBJECT INTERACTION HYPOTHESIS PRIMITIVES - BIRTHRIGHT
        # ==================================================================
        # Babies naturally experiment: "What happens when THIS touches THAT?"
        # These are BIRTHRIGHT primitives - fundamental to learning causality.
        # Without these, an agent can move but never learns what interactions DO.
        #
        # Categories of object-object interactions:
        # 1. Contact & Force - collision, touching, resting, pressing
        # 2. Spatial Containment - overlap, engulf, nest, partial containment
        # 3. Wrapping & Deformation - wrap, coat, bind
        # 4. Penetration - pierce, embed, pass through
        # 5. Proximity Effects - hover, orbit, field interaction
        # 6. Joining & Merging - fuse, adhere, interlock, snap
        # ==================================================================
        
        # --- CONTACT & FORCE INTERACTIONS ---
        
        self._register(Primitive(
            name="detect_collision",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Detect if controlled object collided with another. Returns collision type and effect. BIRTHRIGHT.",
            func=self._detect_collision,
            input_types=["controlled_pos_before", "controlled_pos_after", "other_objects", "frame_before", "frame_after"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_contact",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Detect if objects are touching (adjacent pixels). Returns contact points. BIRTHRIGHT.",
            func=self._detect_contact,
            input_types=["object_a_positions", "object_b_positions"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_blocking",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Detect if object B blocked movement of object A. BIRTHRIGHT.",
            func=self._detect_blocking,
            input_types=["controlled_pos", "intended_direction", "frame"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_pushing",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Detect if controlled object pushed another object. Returns pushed object and direction. BIRTHRIGHT.",
            func=self._detect_pushing,
            input_types=["controlled_movement", "other_objects_before", "other_objects_after"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # --- SPATIAL CONTAINMENT INTERACTIONS ---
        
        self._register(Primitive(
            name="detect_overlap",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Detect if objects occupy the same pixels (overlap/intersection). BIRTHRIGHT.",
            func=self._detect_overlap,
            input_types=["object_a_positions", "object_b_positions"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_engulfing",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Detect if one object completely surrounds/contains another. BIRTHRIGHT.",
            func=self._detect_engulfing,
            input_types=["outer_object_positions", "inner_object_positions"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_partial_containment",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Detect if object A is partially inside object B's bounding region. BIRTHRIGHT.",
            func=self._detect_partial_containment,
            input_types=["object_a_positions", "container_bounds"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_nesting",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Detect nested containment structure (objects inside objects). BIRTHRIGHT.",
            func=self._detect_nesting,
            input_types=["objects_list", "frame"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # --- WRAPPING & COATING INTERACTIONS ---
        
        self._register(Primitive(
            name="detect_wrapping",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Detect if object A wraps around/conforms to object B's shape. BIRTHRIGHT.",
            func=self._detect_wrapping,
            input_types=["wrapper_positions", "wrapped_positions"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_coating",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Detect if object A forms a layer over object B (like paint on surface). BIRTHRIGHT.",
            func=self._detect_coating,
            input_types=["coating_positions", "base_positions", "frame"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # --- PENETRATION & PASS-THROUGH INTERACTIONS ---
        
        self._register(Primitive(
            name="detect_pass_through",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Detect if object passed through another without stopping (ghost/portal). BIRTHRIGHT.",
            func=self._detect_pass_through,
            input_types=["moving_obj_before", "moving_obj_after", "stationary_obj", "frame_before", "frame_after"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_embedding",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Detect if object A became lodged/embedded within object B. BIRTHRIGHT.",
            func=self._detect_embedding,
            input_types=["embedded_obj_positions", "host_obj_positions", "frame_before", "frame_after"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # --- PROXIMITY & FIELD INTERACTIONS ---
        
        self._register(Primitive(
            name="detect_proximity_effect",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Detect if being NEAR an object causes effects without touching. BIRTHRIGHT.",
            func=self._detect_proximity_effect,
            input_types=["object_a_pos", "object_b_pos", "frame_before", "frame_after", "distance_threshold"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_attraction_repulsion",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Detect if objects attract or repel each other at distance. BIRTHRIGHT.",
            func=self._detect_attraction_repulsion,
            input_types=["object_positions_history", "other_object_pos"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # --- JOINING & MERGING INTERACTIONS ---
        
        self._register(Primitive(
            name="detect_merging",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Detect if two objects combined into one (fusion/merging). BIRTHRIGHT.",
            func=self._detect_merging,
            input_types=["objects_before", "objects_after", "frame_before", "frame_after"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_adhesion",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Detect if objects stuck together and now move as one. BIRTHRIGHT.",
            func=self._detect_adhesion,
            input_types=["object_a_movement", "object_b_movement", "were_adjacent"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_snapping",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Detect if objects snapped/aligned to specific positions when near. BIRTHRIGHT.",
            func=self._detect_snapping,
            input_types=["object_pos_before", "object_pos_after", "snap_points"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # --- META: INTERACTION HYPOTHESIS TESTING ---
        
        self._register(Primitive(
            name="hypothesize_interaction_type",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Given two objects, hypothesize what interaction types are possible. BIRTHRIGHT.",
            func=self._hypothesize_interaction_type,
            input_types=["object_a", "object_b", "frame"],
            output_type="list",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="test_interaction_hypothesis",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Test a specific interaction hypothesis by analyzing frame changes. BIRTHRIGHT.",
            func=self._test_interaction_hypothesis,
            input_types=["hypothesis_type", "objects", "frame_before", "frame_after", "action_taken"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="get_interaction_effect",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Get the EFFECT of an interaction (score change, color change, disappear, etc). BIRTHRIGHT.",
            func=self._get_interaction_effect,
            input_types=["interaction_type", "frame_before", "frame_after", "score_before", "score_after"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # ==================================================================
        # PHASE 0: MOTION RELATIONSHIP PRIMITIVES - BIRTHRIGHT
        # ==================================================================
        # Understanding HOW objects move relative to each other is fundamental.
        # Without these, agents cannot perceive following, mirroring, chasing,
        # or synchronized movement - common patterns in games.
        # ==================================================================
        
        self._register(Primitive(
            name="detect_following",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Detect if one object follows/tracks another's movement. BIRTHRIGHT.",
            func=self._detect_following,
            input_types=["leader_positions_history", "follower_positions_history", "lag_frames"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_mirroring",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Detect if objects move in mirrored/symmetric patterns. BIRTHRIGHT.",
            func=self._detect_mirroring,
            input_types=["object_a_movements", "object_b_movements", "mirror_axis"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_chasing",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Detect goal-directed pursuit - one object moving toward another. BIRTHRIGHT.",
            func=self._detect_chasing,
            input_types=["chaser_positions_history", "target_positions_history"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_fleeing",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Detect if object is moving away from another (avoidance). BIRTHRIGHT.",
            func=self._detect_fleeing,
            input_types=["fleeing_positions_history", "threat_positions_history"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_synchronized_movement",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Detect if multiple objects move together in coordinated way. BIRTHRIGHT.",
            func=self._detect_synchronized_movement,
            input_types=["objects_movements_history"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_dragging",
            category=PrimitiveCategory.OBJECT_INTERACTION,
            description="Detect if moving object pulls another along through connection. BIRTHRIGHT.",
            func=self._detect_dragging,
            input_types=["dragger_movement", "dragged_movement", "were_connected"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # ==================================================================
        # PHASE 0: TOPOLOGICAL RELATIONSHIP PRIMITIVES - BIRTHRIGHT
        # ==================================================================
        # Fundamental spatial reasoning about how objects relate structurally.
        # Adjacency, connectivity, and separation are core to understanding space.
        # ==================================================================
        
        self._register(Primitive(
            name="detect_adjacency",
            category=PrimitiveCategory.SPATIAL,
            description="Detect if objects share boundary/edge without overlapping. BIRTHRIGHT.",
            func=self._detect_adjacency,
            input_types=["object_a_positions", "object_b_positions"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_connectivity",
            category=PrimitiveCategory.SPATIAL,
            description="Detect if objects form connected network through shared pixels/paths. BIRTHRIGHT.",
            func=self._detect_connectivity,
            input_types=["objects_list", "frame"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_path_between",
            category=PrimitiveCategory.SPATIAL,
            description="Detect if traversable path exists between two positions. BIRTHRIGHT.",
            func=self._detect_path_between,
            input_types=["start_pos", "end_pos", "frame", "passable_colors"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_separation",
            category=PrimitiveCategory.SPATIAL,
            description="Detect if objects are completely disconnected with space between. BIRTHRIGHT.",
            func=self._detect_separation,
            input_types=["object_a_positions", "object_b_positions"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_surrounding",
            category=PrimitiveCategory.SPATIAL,
            description="Detect if multiple objects collectively encircle another. BIRTHRIGHT.",
            func=self._detect_surrounding,
            input_types=["surrounding_objects", "center_object_positions"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # ==================================================================
        # PHASE 0: SUPPORT & DEPENDENCY PRIMITIVES - BIRTHRIGHT
        # ==================================================================
        # Understanding support relationships is fundamental to physics intuition.
        # Stacking, supporting, and leaning are common in puzzle games.
        # ==================================================================
        
        self._register(Primitive(
            name="detect_supporting",
            category=PrimitiveCategory.PHYSICS,
            description="Detect if object A is supporting/holding up object B. BIRTHRIGHT.",
            func=self._detect_supporting,
            input_types=["support_object_positions", "supported_object_positions", "gravity_direction"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_stacking",
            category=PrimitiveCategory.PHYSICS,
            description="Detect vertical arrangement where each level supports the one above. BIRTHRIGHT.",
            func=self._detect_stacking,
            input_types=["objects_list", "gravity_direction"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_hanging",
            category=PrimitiveCategory.PHYSICS,
            description="Detect if object is suspended/hanging from above. BIRTHRIGHT.",
            func=self._detect_hanging,
            input_types=["hanging_object_positions", "anchor_positions", "frame"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_leaning",
            category=PrimitiveCategory.PHYSICS,
            description="Detect if object relies on another for angular stability. BIRTHRIGHT.",
            func=self._detect_leaning,
            input_types=["leaning_object_positions", "support_object_positions"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # ==================================================================
        # PHASE 0: HIERARCHICAL & ORGANIZATIONAL PRIMITIVES - BIRTHRIGHT
        # ==================================================================
        # Understanding how objects group, layer, and attach is fundamental
        # to parsing complex visual scenes.
        # ==================================================================
        
        self._register(Primitive(
            name="detect_clustering",
            category=PrimitiveCategory.SPATIAL,
            description="Detect objects grouped by proximity or shared properties. BIRTHRIGHT.",
            func=self._detect_clustering,
            input_types=["objects_list", "grouping_threshold"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_layering",
            category=PrimitiveCategory.SPATIAL,
            description="Detect Z-order/depth relationships - what's in front of what. BIRTHRIGHT.",
            func=self._detect_layering,
            input_types=["objects_list", "frame"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_attachment",
            category=PrimitiveCategory.SPATIAL,
            description="Detect if objects are attached and move as a unit. BIRTHRIGHT.",
            func=self._detect_attachment,
            input_types=["object_a_movements", "object_b_movements", "were_adjacent"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_part_whole",
            category=PrimitiveCategory.SPATIAL,
            description="Detect part-whole relationships (component is part of larger object). BIRTHRIGHT.",
            func=self._detect_part_whole,
            input_types=["potential_part_positions", "potential_whole_positions"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # ==================================================================
        # PHASE 0: TEMPORAL RELATIONSHIP PRIMITIVES - BIRTHRIGHT
        # ==================================================================
        # Understanding time and causality is FUNDAMENTAL to learning.
        # Without temporal primitives, agents cannot understand sequences,
        # cause-effect, or timing - essential for all game mechanics.
        # ==================================================================
        
        self._register(Primitive(
            name="detect_causation",
            category=PrimitiveCategory.TEMPORAL,
            description="Detect if action/event A directly caused change B. BIRTHRIGHT.",
            func=self._detect_causation,
            input_types=["action_taken", "state_before", "state_after", "time_delta"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_precedence",
            category=PrimitiveCategory.TEMPORAL,
            description="Detect if event A must occur before event B can happen. BIRTHRIGHT.",
            func=self._detect_precedence,
            input_types=["event_sequence", "event_a", "event_b"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_simultaneity",
            category=PrimitiveCategory.TEMPORAL,
            description="Detect if multiple events/changes occur at the same time. BIRTHRIGHT.",
            func=self._detect_simultaneity,
            input_types=["events_with_timestamps"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_periodic",
            category=PrimitiveCategory.TEMPORAL,
            description="Detect repeating patterns/cycles in events or states. BIRTHRIGHT.",
            func=self._detect_periodic,
            input_types=["state_history", "min_period", "max_period"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_decay_persistence",
            category=PrimitiveCategory.TEMPORAL,
            description="Detect how long effects or relationships last after initial event. BIRTHRIGHT.",
            func=self._detect_decay_persistence,
            input_types=["effect_history", "initial_event_time"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_sequence_pattern",
            category=PrimitiveCategory.TEMPORAL,
            description="Detect ordered sequences that lead to specific outcomes. BIRTHRIGHT.",
            func=self._detect_sequence_pattern,
            input_types=["action_history", "outcome_history"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # ==================================================================
        # PHASE 0: CONSTRAINT & CONTROL PRIMITIVES - BIRTHRIGHT
        # ==================================================================
        # Understanding how objects constrain or control each other is
        # fundamental to learning game mechanics and physics.
        # ==================================================================
        
        self._register(Primitive(
            name="detect_guiding",
            category=PrimitiveCategory.PHYSICS,
            description="Detect if object constrains another to a specific path. BIRTHRIGHT.",
            func=self._detect_guiding,
            input_types=["guided_object_history", "potential_guide_positions"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_gating",
            category=PrimitiveCategory.PHYSICS,
            description="Detect if object controls whether passage/flow can occur. BIRTHRIGHT.",
            func=self._detect_gating,
            input_types=["gate_object_state", "passage_before", "passage_after"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_actuating",
            category=PrimitiveCategory.PHYSICS,
            description="Detect if one object causes motion in another (trigger/switch). BIRTHRIGHT.",
            func=self._detect_actuating,
            input_types=["actuator_state_change", "actuated_object_before", "actuated_object_after"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
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
        
        # ==================================================================
        # PHASE 0: TOPOLOGY & SHAPE PRIMITIVES - BIRTHRIGHT
        # ==================================================================
        # Understanding topological properties (holes, boundaries, connected
        # components) is FUNDAMENTAL to ARC reasoning. These are not learned.
        # ==================================================================
        
        self._register(Primitive(
            name="detect_hole",
            category=PrimitiveCategory.TOPOLOGY,
            description="Detect holes (through-holes vs pockets) in objects. BIRTHRIGHT.",
            func=self._detect_hole,
            input_types=["frame", "object_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_cavity",
            category=PrimitiveCategory.TOPOLOGY,
            description="Detect enclosed empty spaces within or between objects. BIRTHRIGHT.",
            func=self._detect_cavity,
            input_types=["frame", "region"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_protrusion",
            category=PrimitiveCategory.TOPOLOGY,
            description="Detect parts that stick out from main body of object. BIRTHRIGHT.",
            func=self._detect_protrusion,
            input_types=["frame", "object_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="count_connected_components",
            category=PrimitiveCategory.TOPOLOGY,
            description="Count separate connected regions of same color. BIRTHRIGHT.",
            func=self._count_connected_components,
            input_types=["frame", "color"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_boundary_closure",
            category=PrimitiveCategory.TOPOLOGY,
            description="Detect if object boundary is closed (forms complete loop). BIRTHRIGHT.",
            func=self._detect_boundary_closure,
            input_types=["frame", "object_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_euler_characteristic",
            category=PrimitiveCategory.TOPOLOGY,
            description="Compute topological invariant V - E + F (vertices - edges + faces). BIRTHRIGHT.",
            func=self._detect_euler_characteristic,
            input_types=["frame", "object_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_genus",
            category=PrimitiveCategory.TOPOLOGY,
            description="Detect number of topological holes (genus) in object. BIRTHRIGHT.",
            func=self._detect_genus,
            input_types=["frame", "object_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # ==================================================================
        # PHASE 0: ALIGNMENT & ORIENTATION PRIMITIVES - BIRTHRIGHT
        # ==================================================================
        # Understanding geometric alignment is FUNDAMENTAL to ARC pattern
        # matching. Parallel, perpendicular, colinear detection is innate.
        # ==================================================================
        
        self._register(Primitive(
            name="detect_parallel",
            category=PrimitiveCategory.ALIGNMENT,
            description="Detect if two lines/edges/objects are parallel. BIRTHRIGHT.",
            func=self._detect_parallel,
            input_types=["frame", "object_a", "object_b"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_perpendicular",
            category=PrimitiveCategory.ALIGNMENT,
            description="Detect if two lines/edges meet at right angles. BIRTHRIGHT.",
            func=self._detect_perpendicular,
            input_types=["frame", "object_a", "object_b"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_colinear",
            category=PrimitiveCategory.ALIGNMENT,
            description="Detect if points/objects lie on same line. BIRTHRIGHT.",
            func=self._detect_colinear,
            input_types=["positions"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_coplanar",
            category=PrimitiveCategory.ALIGNMENT,
            description="Detect if objects lie in same plane (for 2D: same alignment). BIRTHRIGHT.",
            func=self._detect_coplanar,
            input_types=["positions"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="measure_angle_between",
            category=PrimitiveCategory.ALIGNMENT,
            description="Measure angle between two lines/edges/directions. BIRTHRIGHT.",
            func=self._measure_angle_between,
            input_types=["line_a", "line_b"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_facing_direction",
            category=PrimitiveCategory.ALIGNMENT,
            description="Detect which direction an asymmetric object is facing. BIRTHRIGHT.",
            func=self._detect_facing_direction,
            input_types=["frame", "object_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_alignment",
            category=PrimitiveCategory.ALIGNMENT,
            description="Detect if objects are aligned (horizontal, vertical, diagonal). BIRTHRIGHT.",
            func=self._detect_alignment,
            input_types=["positions"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # ==================================================================
        # PHASE 0: SYMMETRY & PATTERN PRIMITIVES - BIRTHRIGHT
        # ==================================================================
        # Symmetry detection is CORE to ARC puzzles. These must be innate
        # because nearly every ARC task involves some form of symmetry.
        # ==================================================================
        
        self._register(Primitive(
            name="detect_reflection_symmetry",
            category=PrimitiveCategory.SYMMETRY,
            description="Detect mirror symmetry (horizontal, vertical, diagonal). BIRTHRIGHT.",
            func=self._detect_reflection_symmetry,
            input_types=["frame", "object_id", "axis"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_rotational_symmetry",
            category=PrimitiveCategory.SYMMETRY,
            description="Detect rotational symmetry (90, 180, 270 degrees). BIRTHRIGHT.",
            func=self._detect_rotational_symmetry,
            input_types=["frame", "object_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_translational_symmetry",
            category=PrimitiveCategory.SYMMETRY,
            description="Detect repeating patterns via translation. BIRTHRIGHT.",
            func=self._detect_translational_symmetry,
            input_types=["frame"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_self_similarity",
            category=PrimitiveCategory.SYMMETRY,
            description="Detect if pattern contains scaled copies of itself (fractal). BIRTHRIGHT.",
            func=self._detect_self_similarity,
            input_types=["frame", "object_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_periodicity_spatial",
            category=PrimitiveCategory.SYMMETRY,
            description="Detect spatial periodicity (repeating patterns in space). BIRTHRIGHT.",
            func=self._detect_periodicity_spatial,
            input_types=["frame"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # ==================================================================
        # PHASE 0: BOUNDARY OPERATIONS PRIMITIVES - BIRTHRIGHT
        # ==================================================================
        # Understanding inside/outside and boundaries is FUNDAMENTAL to
        # spatial reasoning. Essential for containment and enclosure.
        # ==================================================================
        
        self._register(Primitive(
            name="detect_inside_outside",
            category=PrimitiveCategory.BOUNDARY,
            description="Determine if point/object is inside or outside a boundary. BIRTHRIGHT.",
            func=self._detect_inside_outside,
            input_types=["frame", "position", "boundary_object"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="compute_distance_to_boundary",
            category=PrimitiveCategory.BOUNDARY,
            description="Compute shortest distance from point to boundary. BIRTHRIGHT.",
            func=self._compute_distance_to_boundary,
            input_types=["frame", "position", "boundary_object"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_boundary_crossing",
            category=PrimitiveCategory.BOUNDARY,
            description="Detect when object crosses a boundary. BIRTHRIGHT.",
            func=self._detect_boundary_crossing,
            input_types=["position_before", "position_after", "boundary_object"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_enclosure",
            category=PrimitiveCategory.BOUNDARY,
            description="Detect if one object completely encloses another. BIRTHRIGHT.",
            func=self._detect_enclosure,
            input_types=["frame", "outer_object", "inner_object"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="measure_convexity",
            category=PrimitiveCategory.BOUNDARY,
            description="Measure how convex vs concave an object's boundary is. BIRTHRIGHT.",
            func=self._measure_convexity,
            input_types=["frame", "object_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # ==================================================================
        # PHASE 0: HIERARCHY & COMPOSITION PRIMITIVES - BIRTHRIGHT
        # ==================================================================
        # Understanding part-whole relationships is FUNDAMENTAL to object
        # reasoning. Parent/child, composite objects are innate concepts.
        # ==================================================================
        
        self._register(Primitive(
            name="get_parent_object",
            category=PrimitiveCategory.HIERARCHY,
            description="Get the containing/parent object of a given object. BIRTHRIGHT.",
            func=self._get_parent_object,
            input_types=["frame", "object_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="get_child_objects",
            category=PrimitiveCategory.HIERARCHY,
            description="Get objects contained within a parent object. BIRTHRIGHT.",
            func=self._get_child_objects,
            input_types=["frame", "parent_object"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_composite_object",
            category=PrimitiveCategory.HIERARCHY,
            description="Detect if multiple colors/parts form a single composite object. BIRTHRIGHT.",
            func=self._detect_composite_object,
            input_types=["frame", "region"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="decompose_object",
            category=PrimitiveCategory.HIERARCHY,
            description="Break composite object into constituent parts. BIRTHRIGHT.",
            func=self._decompose_object,
            input_types=["frame", "object_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="find_root_object",
            category=PrimitiveCategory.HIERARCHY,
            description="Find topmost object in containment hierarchy. BIRTHRIGHT.",
            func=self._find_root_object,
            input_types=["frame", "object_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # ==================================================================
        # PHASE 0: PERSISTENCE & MEMORY PRIMITIVES - BIRTHRIGHT
        # ==================================================================
        # Object permanence and identity tracking are FUNDAMENTAL to learning.
        # Tracking object identity across frames is innate cognition.
        # ==================================================================
        
        self._register(Primitive(
            name="object_first_appearance",
            category=PrimitiveCategory.PERSISTENCE,
            description="Get frame index when object first appeared. BIRTHRIGHT.",
            func=self._object_first_appearance,
            input_types=["object_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="object_last_seen",
            category=PrimitiveCategory.PERSISTENCE,
            description="Get frame index when object was last seen. BIRTHRIGHT.",
            func=self._object_last_seen,
            input_types=["object_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_object_creation",
            category=PrimitiveCategory.PERSISTENCE,
            description="Detect when a new object appears. BIRTHRIGHT.",
            func=self._detect_object_creation,
            input_types=["frame_before", "frame_after"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_object_destruction",
            category=PrimitiveCategory.PERSISTENCE,
            description="Detect when an object disappears. BIRTHRIGHT.",
            func=self._detect_object_destruction,
            input_types=["frame_before", "frame_after"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="track_object_identity",
            category=PrimitiveCategory.PERSISTENCE,
            description="Maintain object identity across frames despite movement. BIRTHRIGHT.",
            func=self._track_object_identity,
            input_types=["frame_before", "frame_after", "object_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # ==================================================================
        # PHASE 0: RELATIONAL QUERIES PRIMITIVES - BIRTHRIGHT
        # ==================================================================
        # Meta-queries about relationships enable reasoning about reasoning.
        # These are foundational for introspection and planning.
        # ==================================================================
        
        self._register(Primitive(
            name="get_all_relations",
            category=PrimitiveCategory.RELATIONAL,
            description="Get all known relationships for an object. BIRTHRIGHT.",
            func=self._get_all_relations,
            input_types=["frame", "object_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="get_relation_strength",
            category=PrimitiveCategory.RELATIONAL,
            description="Get confidence/strength of a specific relationship. BIRTHRIGHT.",
            func=self._get_relation_strength,
            input_types=["relation_type", "object_a", "object_b"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_relation_change",
            category=PrimitiveCategory.RELATIONAL,
            description="Detect when relationship between objects changes. BIRTHRIGHT.",
            func=self._detect_relation_change,
            input_types=["frame_before", "frame_after", "object_a", "object_b"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="relation_history",
            category=PrimitiveCategory.RELATIONAL,
            description="Get history of relationships between two objects. BIRTHRIGHT.",
            func=self._relation_history,
            input_types=["object_a", "object_b"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # ==================================================================
        # PHASE 0: SCALE & AGGREGATION PRIMITIVES - BIRTHRIGHT
        # ==================================================================
        # Understanding how things combine or split is FUNDAMENTAL to
        # ARC reasoning about patterns and transformations.
        # ==================================================================
        
        self._register(Primitive(
            name="detect_aggregation",
            category=PrimitiveCategory.SCALE,
            description="Detect many objects combining into one (many -> one). BIRTHRIGHT.",
            func=self._detect_aggregation,
            input_types=["frame_before", "frame_after"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_subdivision",
            category=PrimitiveCategory.SCALE,
            description="Detect one object splitting into many (one -> many). BIRTHRIGHT.",
            func=self._detect_subdivision,
            input_types=["frame_before", "frame_after"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="measure_granularity",
            category=PrimitiveCategory.SCALE,
            description="Measure level of detail/granularity in a region. BIRTHRIGHT.",
            func=self._measure_granularity,
            input_types=["frame", "region"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="scale_invariance_check",
            category=PrimitiveCategory.SCALE,
            description="Check if pattern/object is scale invariant (same at different sizes). BIRTHRIGHT.",
            func=self._scale_invariance_check,
            input_types=["frame", "pattern"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # ==================================================================
        # PHASE 0: INFORMATION & SENSING PRIMITIVES - BIRTHRIGHT
        # ==================================================================
        # Understanding visibility and occlusion is FUNDAMENTAL to spatial
        # reasoning. Essential for planning and attention.
        # ==================================================================
        
        self._register(Primitive(
            name="detect_occluding",
            category=PrimitiveCategory.SPATIAL,
            description="Detect if one object blocks view of another. BIRTHRIGHT.",
            func=self._detect_occluding,
            input_types=["frame", "front_object", "back_object"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="compute_visibility",
            category=PrimitiveCategory.SPATIAL,
            description="Compute what is visible from a given viewpoint. BIRTHRIGHT.",
            func=self._compute_visibility,
            input_types=["frame", "viewpoint"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_casting",
            category=PrimitiveCategory.SPATIAL,
            description="Detect shadow or projection cast by an object. BIRTHRIGHT.",
            func=self._detect_casting,
            input_types=["frame", "object_id", "light_direction"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # ==================================================================
        # PHASE 0: FLOW & MATERIAL TRANSFER PRIMITIVES - BIRTHRIGHT
        # ==================================================================
        # Abstracted for grid worlds: colors flowing through channels,
        # containers being filled, propagation patterns. See vc33 for example.
        # ==================================================================
        
        self._register(Primitive(
            name="detect_flowing_through",
            category=PrimitiveCategory.FLOW,
            description="Detect if color/pattern is flowing through a channel or path. BIRTHRIGHT.",
            func=self._detect_flowing_through,
            input_types=["frame_before", "frame_after", "channel_positions"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_filling",
            category=PrimitiveCategory.FLOW,
            description="Detect if a container/region is being filled with color. BIRTHRIGHT.",
            func=self._detect_filling,
            input_types=["frame_before", "frame_after", "container_region"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_draining",
            category=PrimitiveCategory.FLOW,
            description="Detect if color is draining from a region. BIRTHRIGHT.",
            func=self._detect_draining,
            input_types=["frame_before", "frame_after", "region"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_transfer",
            category=PrimitiveCategory.FLOW,
            description="Detect transfer of color/pattern from one region to another. BIRTHRIGHT.",
            func=self._detect_transfer,
            input_types=["frame_before", "frame_after"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_propagation",
            category=PrimitiveCategory.FLOW,
            description="Detect spreading/propagation of color outward from source. BIRTHRIGHT.",
            func=self._detect_propagation,
            input_types=["frame_before", "frame_after"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="measure_fill_level",
            category=PrimitiveCategory.FLOW,
            description="Measure how full a container region is. BIRTHRIGHT.",
            func=self._measure_fill_level,
            input_types=["frame", "container_region", "fill_color"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_source_sink",
            category=PrimitiveCategory.FLOW,
            description="Detect source (emitting) and sink (absorbing) locations. BIRTHRIGHT.",
            func=self._detect_source_sink,
            input_types=["frame_before", "frame_after"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # ==================================================================
        # PHASE 0: TRANSFORMATION & STATE PRIMITIVES - BIRTHRIGHT
        # ==================================================================
        # Abstracted state changes: color transformations, growth/decay,
        # crystallization patterns, phase-like transitions in grids.
        # ==================================================================
        
        self._register(Primitive(
            name="detect_state_change",
            category=PrimitiveCategory.TRANSFORMATION,
            description="Detect when object changes to different state (color change). BIRTHRIGHT.",
            func=self._detect_state_change,
            input_types=["frame_before", "frame_after", "object_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_growth",
            category=PrimitiveCategory.TRANSFORMATION,
            description="Detect object/pattern growing larger over frames. BIRTHRIGHT.",
            func=self._detect_growth,
            input_types=["frame_before", "frame_after", "object_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_decay",
            category=PrimitiveCategory.TRANSFORMATION,
            description="Detect object/pattern shrinking or decaying. BIRTHRIGHT.",
            func=self._detect_decay,
            input_types=["frame_before", "frame_after", "object_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_crystallization",
            category=PrimitiveCategory.TRANSFORMATION,
            description="Detect ordered pattern emerging from disorder. BIRTHRIGHT.",
            func=self._detect_crystallization,
            input_types=["frame_before", "frame_after"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_dissolution",
            category=PrimitiveCategory.TRANSFORMATION,
            description="Detect ordered pattern dissolving into disorder. BIRTHRIGHT.",
            func=self._detect_dissolution,
            input_types=["frame_before", "frame_after"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_color_transformation",
            category=PrimitiveCategory.TRANSFORMATION,
            description="Detect systematic color changes (like phase transitions). BIRTHRIGHT.",
            func=self._detect_color_transformation,
            input_types=["frame_before", "frame_after"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_restoration",
            category=PrimitiveCategory.TRANSFORMATION,
            description="Detect object returning to previous state (elastic return). BIRTHRIGHT.",
            func=self._detect_restoration,
            input_types=["frame_history"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # ==================================================================
        # PHASE 0: CONSTRAINT & MODULATION PRIMITIVES - BIRTHRIGHT
        # ==================================================================
        # Objects that control, bind, or modulate other objects.
        # ==================================================================
        
        self._register(Primitive(
            name="detect_binding",
            category=PrimitiveCategory.CONSTRAINT,
            description="Detect if two objects are bound (move together). BIRTHRIGHT.",
            func=self._detect_binding,
            input_types=["frame_before", "frame_after", "object_a", "object_b"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_tethering",
            category=PrimitiveCategory.CONSTRAINT,
            description="Detect if object is tethered (limited range of motion). BIRTHRIGHT.",
            func=self._detect_tethering,
            input_types=["movement_history", "object_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_modulating",
            category=PrimitiveCategory.CONSTRAINT,
            description="Detect if one object modulates/controls rate of another. BIRTHRIGHT.",
            func=self._detect_modulating,
            input_types=["frame_history", "controller_id", "target_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="measure_constraint_strength",
            category=PrimitiveCategory.CONSTRAINT,
            description="Measure how strongly objects are constrained together. BIRTHRIGHT.",
            func=self._measure_constraint_strength,
            input_types=["movement_history", "object_a", "object_b"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # ==================================================================
        # PHASE 0: MATERIAL PROPERTIES PRIMITIVES - BIRTHRIGHT
        # ==================================================================
        # Abstracted: objects that "stick", "bounce", resist movement, etc.
        # ==================================================================
        
        self._register(Primitive(
            name="detect_stickiness",
            category=PrimitiveCategory.MATERIAL,
            description="Detect if objects stick when they touch (abstracted friction). BIRTHRIGHT.",
            func=self._detect_stickiness,
            input_types=["frame_before", "frame_after", "action_taken"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_bounciness",
            category=PrimitiveCategory.MATERIAL,
            description="Detect if object bounces off boundaries (abstracted elasticity). BIRTHRIGHT.",
            func=self._detect_bounciness,
            input_types=["movement_history", "object_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_permeability",
            category=PrimitiveCategory.MATERIAL,
            description="Detect if objects can pass through barriers (abstracted porosity). BIRTHRIGHT.",
            func=self._detect_permeability,
            input_types=["frame_before", "frame_after", "barrier_color"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_conductivity",
            category=PrimitiveCategory.MATERIAL,
            description="Detect if color/state propagates through object (abstracted conductivity). BIRTHRIGHT.",
            func=self._detect_conductivity,
            input_types=["frame_before", "frame_after", "object_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_resistance",
            category=PrimitiveCategory.MATERIAL,
            description="Detect movement resistance (some directions harder). BIRTHRIGHT.",
            func=self._detect_resistance,
            input_types=["action_history", "movement_history"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # ==================================================================
        # PHASE 0: FORCE & ENERGY PRIMITIVES - BIRTHRIGHT
        # ==================================================================
        # Abstracted: momentum in movement, pressure from crowding, etc.
        # ==================================================================
        
        self._register(Primitive(
            name="detect_momentum",
            category=PrimitiveCategory.FORCE,
            description="Detect if object continues moving after action stops. BIRTHRIGHT.",
            func=self._detect_momentum,
            input_types=["action_history", "movement_history"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_collision_effect",
            category=PrimitiveCategory.FORCE,
            description="Detect effect of collision between objects. BIRTHRIGHT.",
            func=self._detect_collision_effect,
            input_types=["frame_before", "frame_after", "object_a", "object_b"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_pushing",
            category=PrimitiveCategory.FORCE,
            description="Detect if one object pushes another. BIRTHRIGHT.",
            func=self._detect_pushing,
            input_types=["frame_before", "frame_after"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_pressure",
            category=PrimitiveCategory.FORCE,
            description="Detect crowding/pressure effects in region. BIRTHRIGHT.",
            func=self._detect_pressure,
            input_types=["frame", "region"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_tension",
            category=PrimitiveCategory.FORCE,
            description="Detect tension between connected objects. BIRTHRIGHT.",
            func=self._detect_tension,
            input_types=["frame_before", "frame_after", "connected_objects"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # ==================================================================
        # PHASE 0: MECHANICAL LINKAGES PRIMITIVES - BIRTHRIGHT
        # ==================================================================
        # Abstracted: hinge-like rotations, lever actions, connected movements.
        # ==================================================================
        
        self._register(Primitive(
            name="detect_hinging",
            category=PrimitiveCategory.MECHANICAL,
            description="Detect rotation around fixed pivot point. BIRTHRIGHT.",
            func=self._detect_hinging,
            input_types=["frame_before", "frame_after", "object_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_lever_action",
            category=PrimitiveCategory.MECHANICAL,
            description="Detect lever-like action (input on one end, output on other). BIRTHRIGHT.",
            func=self._detect_lever_action,
            input_types=["frame_before", "frame_after", "action_point", "effect_point"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_linked_movement",
            category=PrimitiveCategory.MECHANICAL,
            description="Detect mechanically linked movements (gears, chains). BIRTHRIGHT.",
            func=self._detect_linked_movement,
            input_types=["frame_before", "frame_after"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_ratchet",
            category=PrimitiveCategory.MECHANICAL,
            description="Detect one-way movement (can go forward, not back). BIRTHRIGHT.",
            func=self._detect_ratchet,
            input_types=["action_history", "movement_history"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # ==================================================================
        # PHASE 0: DEFORMATION PRIMITIVES - BIRTHRIGHT
        # ==================================================================
        # Objects that stretch, bend, break apart.
        # ==================================================================
        
        self._register(Primitive(
            name="detect_stretching",
            category=PrimitiveCategory.DEFORMATION,
            description="Detect object stretching (getting longer in one direction). BIRTHRIGHT.",
            func=self._detect_stretching,
            input_types=["frame_before", "frame_after", "object_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_compression",
            category=PrimitiveCategory.DEFORMATION,
            description="Detect object being compressed/squashed. BIRTHRIGHT.",
            func=self._detect_compression,
            input_types=["frame_before", "frame_after", "object_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_bending",
            category=PrimitiveCategory.DEFORMATION,
            description="Detect object bending (changing angle). BIRTHRIGHT.",
            func=self._detect_bending,
            input_types=["frame_before", "frame_after", "object_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_breaking",
            category=PrimitiveCategory.DEFORMATION,
            description="Detect object breaking into pieces. BIRTHRIGHT.",
            func=self._detect_breaking,
            input_types=["frame_before", "frame_after", "object_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_merging",
            category=PrimitiveCategory.DEFORMATION,
            description="Detect pieces merging into one object. BIRTHRIGHT.",
            func=self._detect_merging,
            input_types=["frame_before", "frame_after"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # ==================================================================
        # PHASE 0: PROBABILITY & UNCERTAINTY PRIMITIVES - BIRTHRIGHT
        # ==================================================================
        # Reasoning under uncertainty, confidence estimation.
        # ==================================================================
        
        self._register(Primitive(
            name="estimate_position_uncertainty",
            category=PrimitiveCategory.PROBABILITY,
            description="Estimate uncertainty in object position prediction. BIRTHRIGHT.",
            func=self._estimate_position_uncertainty,
            input_types=["movement_history", "object_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="predict_collision_probability",
            category=PrimitiveCategory.PROBABILITY,
            description="Estimate probability of collision given trajectories. BIRTHRIGHT.",
            func=self._predict_collision_probability,
            input_types=["object_a_trajectory", "object_b_trajectory"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="estimate_stability_risk",
            category=PrimitiveCategory.PROBABILITY,
            description="Estimate risk of unstable configuration. BIRTHRIGHT.",
            func=self._estimate_stability_risk,
            input_types=["frame", "object_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="confidence_in_pattern",
            category=PrimitiveCategory.PROBABILITY,
            description="Estimate confidence that detected pattern is real. BIRTHRIGHT.",
            func=self._confidence_in_pattern,
            input_types=["observations", "pattern_hypothesis"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # ==================================================================
        # PHASE 0: GOAL & INTENTION PRIMITIVES - BIRTHRIGHT
        # ==================================================================
        # Inferring goals, tracking progress toward objectives.
        # ==================================================================
        
        self._register(Primitive(
            name="infer_goal_from_behavior",
            category=PrimitiveCategory.GOAL,
            description="Infer what goal an object/agent might be pursuing. BIRTHRIGHT.",
            func=self._infer_goal_from_behavior,
            input_types=["movement_history", "frame"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_goal_achievement",
            category=PrimitiveCategory.GOAL,
            description="Detect when a goal state is achieved. BIRTHRIGHT.",
            func=self._detect_goal_achievement,
            input_types=["frame", "goal_state"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="measure_goal_distance",
            category=PrimitiveCategory.GOAL,
            description="Measure how far current state is from goal state. BIRTHRIGHT.",
            func=self._measure_goal_distance,
            input_types=["frame", "goal_state"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_subgoal",
            category=PrimitiveCategory.GOAL,
            description="Detect intermediate goal that enables final goal. BIRTHRIGHT.",
            func=self._detect_subgoal,
            input_types=["frame", "final_goal", "obstacles"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # ==================================================================
        # PHASE 0: RESOURCE & INVENTORY PRIMITIVES - BIRTHRIGHT
        # ==================================================================
        # Counting resources, tracking depletion/generation.
        # ==================================================================
        
        self._register(Primitive(
            name="count_resource",
            category=PrimitiveCategory.RESOURCE,
            description="Count instances of a resource type in frame. BIRTHRIGHT.",
            func=self._count_resource,
            input_types=["frame", "resource_color"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_resource_depletion",
            category=PrimitiveCategory.RESOURCE,
            description="Detect resources being consumed/depleted. BIRTHRIGHT.",
            func=self._detect_resource_depletion,
            input_types=["frame_before", "frame_after", "resource_color"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_resource_generation",
            category=PrimitiveCategory.RESOURCE,
            description="Detect new resources being generated. BIRTHRIGHT.",
            func=self._detect_resource_generation,
            input_types=["frame_before", "frame_after", "resource_color"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="measure_carrying_capacity",
            category=PrimitiveCategory.RESOURCE,
            description="Measure how much a container/region can hold. BIRTHRIGHT.",
            func=self._measure_carrying_capacity,
            input_types=["frame", "container_region"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # ==================================================================
        # PHASE 0: SCALE & AGGREGATION GAPS - BIRTHRIGHT
        # ==================================================================
        # Shattering, subdivision, counting pieces.
        # ==================================================================
        
        self._register(Primitive(
            name="detect_shattering",
            category=PrimitiveCategory.SCALE,
            description="Detect object exploding into many scattered pieces. BIRTHRIGHT.",
            func=self._detect_shattering,
            input_types=["frame_before", "frame_after", "object_id"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_subdivision",
            category=PrimitiveCategory.SCALE,
            description="Detect controlled division into regular parts. BIRTHRIGHT.",
            func=self._detect_subdivision,
            input_types=["frame_before", "frame_after"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="count_pieces",
            category=PrimitiveCategory.SCALE,
            description="Count number of distinct connected pieces of a color. BIRTHRIGHT.",
            func=self._count_pieces,
            input_types=["frame", "target_color"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_aggregation",
            category=PrimitiveCategory.SCALE,
            description="Detect pieces coming together into larger whole. BIRTHRIGHT.",
            func=self._detect_aggregation,
            input_types=["frame_before", "frame_after"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # ==================================================================
        # PHASE 0: PENETRATION & PIERCING PRIMITIVES - BIRTHRIGHT
        # ==================================================================
        # Objects passing through barriers, projectile motion.
        # ==================================================================
        
        self._register(Primitive(
            name="detect_piercing",
            category=PrimitiveCategory.PENETRATION,
            description="Detect object passing completely through barrier. BIRTHRIGHT.",
            func=self._detect_piercing,
            input_types=["frame_before", "frame_after", "barrier_color"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_partial_penetration",
            category=PrimitiveCategory.PENETRATION,
            description="Detect object partially inside another. BIRTHRIGHT.",
            func=self._detect_partial_penetration,
            input_types=["frame", "object_a_color", "object_b_color"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_projectile",
            category=PrimitiveCategory.PENETRATION,
            description="Detect fast-moving object crossing space. BIRTHRIGHT.",
            func=self._detect_projectile,
            input_types=["frame_before", "frame_after"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_passthrough",
            category=PrimitiveCategory.PENETRATION,
            description="Detect which barriers allow passage and which block. BIRTHRIGHT.",
            func=self._detect_passthrough,
            input_types=["movement_history", "frame"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # ==================================================================
        # PHASE 0: SENSING & VISIBILITY PRIMITIVES - BIRTHRIGHT
        # ==================================================================
        # Visibility, transparency, layering, occlusion, line of sight.
        # ==================================================================
        
        self._register(Primitive(
            name="detect_transparency",
            category=PrimitiveCategory.SENSING,
            description="Detect if one color can 'see through' to show underlying color. BIRTHRIGHT.",
            func=self._detect_transparency,
            input_types=["frame_history"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_layering",
            category=PrimitiveCategory.SENSING,
            description="Detect objects stacked in layers (z-order). BIRTHRIGHT.",
            func=self._detect_layering,
            input_types=["frame_history"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_occlusion",
            category=PrimitiveCategory.SENSING,
            description="Detect object hiding/revealing another object. BIRTHRIGHT.",
            func=self._detect_occlusion,
            input_types=["frame_before", "frame_after"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_line_of_sight",
            category=PrimitiveCategory.SENSING,
            description="Check if clear path exists between two points. BIRTHRIGHT.",
            func=self._detect_line_of_sight,
            input_types=["frame", "point_a", "point_b"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_visibility_change",
            category=PrimitiveCategory.SENSING,
            description="Detect what became visible/hidden between frames. BIRTHRIGHT.",
            func=self._detect_visibility_change,
            input_types=["frame_before", "frame_after"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # ==================================================================
        # PHASE 0: TEXTURE & SURFACE PATTERN PRIMITIVES - BIRTHRIGHT
        # ==================================================================
        # Pattern textures like stripes, checkers, gradients.
        # ==================================================================
        
        self._register(Primitive(
            name="detect_stripe_pattern",
            category=PrimitiveCategory.TEXTURE,
            description="Detect alternating stripe pattern (horizontal or vertical). BIRTHRIGHT.",
            func=self._detect_stripe_pattern,
            input_types=["frame", "region"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_checker_pattern",
            category=PrimitiveCategory.TEXTURE,
            description="Detect checkerboard/alternating grid pattern. BIRTHRIGHT.",
            func=self._detect_checker_pattern,
            input_types=["frame", "region"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_gradient",
            category=PrimitiveCategory.TEXTURE,
            description="Detect color value changing gradually across region. BIRTHRIGHT.",
            func=self._detect_gradient,
            input_types=["frame", "region"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="measure_pattern_regularity",
            category=PrimitiveCategory.TEXTURE,
            description="Measure how regular/repeated a pattern is. BIRTHRIGHT.",
            func=self._measure_pattern_regularity,
            input_types=["frame", "region"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_texture_boundary",
            category=PrimitiveCategory.TEXTURE,
            description="Detect where one texture pattern meets another. BIRTHRIGHT.",
            func=self._detect_texture_boundary,
            input_types=["frame"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        # ==================================================================
        # PHASE 0: GAME-SPECIFIC DETECTION PRIMITIVES - BIRTHRIGHT
        # ==================================================================
        # These help CODS identify what kind of game environment this is
        # and suggest appropriate primitive chains.
        # ==================================================================
        
        self._register(Primitive(
            name="detect_pipe_structure",
            category=PrimitiveCategory.SENSING,
            description="Identify pipe/channel/conduit layouts for flow games. BIRTHRIGHT.",
            func=self._detect_pipe_structure,
            input_types=["frame"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_valve",
            category=PrimitiveCategory.MECHANICAL,
            description="Find controllable flow points (valves, gates, switches). BIRTHRIGHT.",
            func=self._detect_valve,
            input_types=["frame", "frame_history"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="predict_flow_path",
            category=PrimitiveCategory.FLOW,
            description="Predict where fluid/color will flow next based on channels. BIRTHRIGHT.",
            func=self._predict_flow_path,
            input_types=["frame", "source_position", "channel_map"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_pour_target",
            category=PrimitiveCategory.FLOW,
            description="Identify where to pour/transfer material to achieve goal. BIRTHRIGHT.",
            func=self._detect_pour_target,
            input_types=["frame", "source_color", "goal_region"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_fitting",
            category=PrimitiveCategory.SPATIAL,
            description="Check if shape A fits into space B (puzzle piece fitting). BIRTHRIGHT.",
            func=self._detect_fitting,
            input_types=["shape_a", "space_b"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="measure_area",
            category=PrimitiveCategory.SCALE,
            description="Measure area of a shape or region in cells. BIRTHRIGHT.",
            func=self._measure_area,
            input_types=["frame", "target_color_or_region"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_complementary_shape",
            category=PrimitiveCategory.SPATIAL,
            description="Find shape that matches/fills negative space of another. BIRTHRIGHT.",
            func=self._detect_complementary_shape,
            input_types=["frame", "shape_color", "background_color"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="count_symmetry_axes",
            category=PrimitiveCategory.SYMMETRY,
            description="Count number of symmetry axes in pattern. BIRTHRIGHT.",
            func=self._count_symmetry_axes,
            input_types=["frame", "region"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="predict_symmetric_position",
            category=PrimitiveCategory.SYMMETRY,
            description="Predict where next element should be to maintain symmetry. BIRTHRIGHT.",
            func=self._predict_symmetric_position,
            input_types=["frame", "existing_positions", "symmetry_center"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="detect_game_signature",
            category=PrimitiveCategory.METACOGNITION,
            description="Analyze frame to determine game type signature for CODS. BIRTHRIGHT.",
            func=self._detect_game_signature,
            input_types=["frame"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="suggest_primitives_for_game",
            category=PrimitiveCategory.METACOGNITION,
            description="CODS helper: suggest primitives based on game signature. BIRTHRIGHT.",
            func=self._suggest_primitives_for_game,
            input_types=["game_signature"],
            output_type="dict",
            unlock_level="seed",
            piaget_stage="sensorimotor"
        ))
        
        self._register(Primitive(
            name="chain_primitives",
            category=PrimitiveCategory.METACOGNITION,
            description="Compose multiple primitives into a solution chain. BIRTHRIGHT.",
            func=self._chain_primitives,
            input_types=["primitive_list", "frame", "context"],
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
        # Full game memory - use all history for information gain (was [-50:] goldfish window)
        # Novelty detection is more accurate with complete history
        history_sigs = [self._signature(h) for h in history]
        
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
        
        # Full game memory - count similar states in ALL history (was [-100:] goldfish window)
        # Stuck detection needs complete game context
        similar = sum(1 for s in state_history 
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
    # NAVIGATION PRIMITIVE IMPLEMENTATIONS (BIRTHRIGHT)
    # ======================================================================
    # These are fundamental to any agent that can move. Without goal-directed
    # movement and systematic exploration, an agent is useless.
    # ======================================================================
    
    def _direction_to_goal(
        self,
        self_position: Tuple[int, int],
        goal_position: Tuple[int, int]
    ) -> str:
        """
        BIRTHRIGHT PRIMITIVE: Get the action to move toward a goal.
        
        This is fundamental - if you can move and you have a goal,
        you MUST be able to compute which direction to go.
        
        Returns: 'ACTION1' (up), 'ACTION2' (down), 'ACTION3' (left), 'ACTION4' (right)
        """
        if not self_position or not goal_position:
            return 'ACTION1'  # Default: try up
        
        sx, sy = self_position
        gx, gy = goal_position
        
        dx = gx - sx
        dy = gy - sy
        
        # Move in the direction of greatest difference
        if abs(dx) >= abs(dy):
            # Horizontal movement priority
            if dx > 0:
                return 'ACTION4'  # Right
            elif dx < 0:
                return 'ACTION3'  # Left
        else:
            # Vertical movement priority
            if dy > 0:
                return 'ACTION2'  # Down
            elif dy < 0:
                return 'ACTION1'  # Up
        
        # At goal position - try any direction
        return 'ACTION1'
    
    def _systematic_exploration_direction(
        self,
        visited_positions: set,
        frame_bounds: Tuple[int, int],  # (width, height)
        current_position: Tuple[int, int]
    ) -> str:
        """
        BIRTHRIGHT PRIMITIVE: Get the next direction for systematic exploration.
        
        Uses a spiral/sweep pattern to ensure complete map coverage.
        Babies naturally explore their environment systematically.
        
        Returns: Action string for best exploration direction
        """
        if not frame_bounds or not current_position:
            return 'ACTION4'  # Default: go right
        
        width, height = frame_bounds
        cx, cy = current_position
        
        # Define exploration regions (quadrants)
        mid_x, mid_y = width // 2, height // 2
        
        # Check which quadrants have been less explored
        quadrant_visits = {
            'top_left': 0, 'top_right': 0,
            'bottom_left': 0, 'bottom_right': 0
        }
        
        for vx, vy in visited_positions:
            if vx < mid_x:
                if vy < mid_y:
                    quadrant_visits['top_left'] += 1
                else:
                    quadrant_visits['bottom_left'] += 1
            else:
                if vy < mid_y:
                    quadrant_visits['top_right'] += 1
                else:
                    quadrant_visits['bottom_right'] += 1
        
        # Find least visited quadrant
        min_quadrant = min(quadrant_visits.keys(), key=lambda q: quadrant_visits[q])
        
        # Move toward the least visited quadrant
        if min_quadrant == 'top_left':
            if cx > mid_x:
                return 'ACTION3'  # Go left
            elif cy > mid_y:
                return 'ACTION1'  # Go up
            else:
                return 'ACTION3' if cx > 0 else 'ACTION1'
        elif min_quadrant == 'top_right':
            if cx < mid_x:
                return 'ACTION4'  # Go right
            elif cy > mid_y:
                return 'ACTION1'  # Go up
            else:
                return 'ACTION4' if cx < width - 1 else 'ACTION1'
        elif min_quadrant == 'bottom_left':
            if cx > mid_x:
                return 'ACTION3'  # Go left
            elif cy < mid_y:
                return 'ACTION2'  # Go down
            else:
                return 'ACTION3' if cx > 0 else 'ACTION2'
        else:  # bottom_right
            if cx < mid_x:
                return 'ACTION4'  # Go right
            elif cy < mid_y:
                return 'ACTION2'  # Go down
            else:
                return 'ACTION4' if cx < width - 1 else 'ACTION2'
    
    def _explore_toward_unexplored(
        self,
        current_position: Tuple[int, int],
        visited_set: set,
        frame_bounds: Tuple[int, int]
    ) -> str:
        """
        BIRTHRIGHT PRIMITIVE: Bias movement toward unexplored regions.
        
        Looks at adjacent cells and prefers directions that lead to
        areas that haven't been visited yet.
        
        Returns: Action string for unexplored direction
        """
        if not current_position or not frame_bounds:
            return 'ACTION4'  # Default: go right
        
        cx, cy = current_position
        width, height = frame_bounds
        
        # Check what's unexplored in each direction
        directions = [
            ('ACTION1', (cx, cy - 5)),      # Up
            ('ACTION2', (cx, cy + 5)),      # Down  
            ('ACTION3', (cx - 5, cy)),      # Left
            ('ACTION4', (cx + 5, cy)),      # Right
        ]
        
        unexplored_scores = []
        for action, (nx, ny) in directions:
            # Check bounds
            if nx < 0 or nx >= width or ny < 0 or ny >= height:
                unexplored_scores.append((action, -1))  # Out of bounds
                continue
            
            # Count unexplored cells in a 5x5 window around target
            unexplored = 0
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    check_pos = (nx + dx, ny + dy)
                    if check_pos not in visited_set:
                        unexplored += 1
            
            unexplored_scores.append((action, unexplored))
        
        # Return direction with most unexplored cells
        unexplored_scores.sort(key=lambda x: x[1], reverse=True)
        return unexplored_scores[0][0]
    
    def _edge_exploration_needed(
        self,
        visited_positions: set,
        frame_bounds: Tuple[int, int]
    ) -> bool:
        """
        BIRTHRIGHT PRIMITIVE: Check if map edges need exploration.
        
        Many ARC games have important objects/goals at the edges.
        Returns True if edges haven't been adequately explored.
        """
        if not frame_bounds:
            return True  # Can't tell, assume yes
        
        width, height = frame_bounds
        
        # Count edge positions visited
        edge_visits = 0
        total_edge = 0
        
        # Top edge
        for x in range(0, width, 3):
            total_edge += 1
            if (x, 0) in visited_positions or (x, 1) in visited_positions:
                edge_visits += 1
        
        # Bottom edge
        for x in range(0, width, 3):
            total_edge += 1
            if (x, height - 1) in visited_positions or (x, height - 2) in visited_positions:
                edge_visits += 1
        
        # Left edge
        for y in range(0, height, 3):
            total_edge += 1
            if (0, y) in visited_positions or (1, y) in visited_positions:
                edge_visits += 1
        
        # Right edge
        for y in range(0, height, 3):
            total_edge += 1
            if (width - 1, y) in visited_positions or (width - 2, y) in visited_positions:
                edge_visits += 1
        
        # Need exploration if less than 50% of edges visited
        if total_edge == 0:
            return True
        return (edge_visits / total_edge) < 0.5
    
    def _exploration_coverage(
        self,
        visited_positions: set,
        frame_bounds: Tuple[int, int]
    ) -> float:
        """
        BIRTHRIGHT PRIMITIVE: Calculate exploration coverage percentage.
        
        Returns 0.0-1.0 representing what fraction of the map has been explored.
        Uses grid sampling (not every pixel) for efficiency.
        """
        if not frame_bounds:
            return 0.0
        
        width, height = frame_bounds
        
        # Sample every 5th position for efficiency
        total_cells = 0
        visited_cells = 0
        
        for x in range(0, width, 5):
            for y in range(0, height, 5):
                total_cells += 1
                # Check if any position in a 3x3 window was visited
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        if (x + dx, y + dy) in visited_positions:
                            visited_cells += 1
                            break
                    else:
                        continue
                    break
        
        if total_cells == 0:
            return 0.0
        
        return visited_cells / total_cells
    
    # ======================================================================
    # OBJECT INTERACTION HYPOTHESIS IMPLEMENTATIONS (BIRTHRIGHT)
    # ======================================================================
    # These primitives help agents understand what happens when objects
    # interact in different ways. Fundamental to learning game mechanics.
    # ======================================================================
    
    def _detect_collision(
        self,
        controlled_pos_before: Tuple[int, int],
        controlled_pos_after: Tuple[int, int],
        other_objects: List[Dict],
        frame_before: List[List[int]],
        frame_after: List[List[int]]
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if controlled object collided with another.
        
        Returns:
            - collided: bool
            - collision_type: 'bounce', 'stop', 'pass_through', 'destroy'
            - other_object: the object we collided with
            - effect: what changed as a result
        """
        result = {
            'collided': False,
            'collision_type': None,
            'other_object': None,
            'effect': None
        }
        
        if not controlled_pos_before or not controlled_pos_after:
            return result
        
        # Calculate intended movement
        dx = controlled_pos_after[0] - controlled_pos_before[0]
        dy = controlled_pos_after[1] - controlled_pos_before[1]
        
        # Check each other object for collision
        for obj in other_objects:
            obj_positions = obj.get('positions', [])
            if not obj_positions:
                continue
            
            # Check if we would have moved through or into this object
            for pos in obj_positions:
                # Check adjacency/contact
                dist_before = abs(controlled_pos_before[0] - pos[0]) + abs(controlled_pos_before[1] - pos[1])
                dist_after = abs(controlled_pos_after[0] - pos[0]) + abs(controlled_pos_after[1] - pos[1])
                
                # We got closer and are now adjacent
                if dist_after <= 1 and dist_before > dist_after:
                    result['collided'] = True
                    result['other_object'] = obj
                    
                    # Determine collision type based on what happened
                    if dx == 0 and dy == 0:
                        result['collision_type'] = 'stop'  # We stopped
                    elif controlled_pos_after == controlled_pos_before:
                        result['collision_type'] = 'bounce'  # We bounced back
                    else:
                        result['collision_type'] = 'slide'  # We slid along
                    
                    return result
        
        return result
    
    def _detect_contact(
        self,
        object_a_positions: List[Tuple[int, int]],
        object_b_positions: List[Tuple[int, int]]
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if objects are touching (adjacent pixels).
        """
        result = {
            'touching': False,
            'contact_points': [],
            'contact_count': 0
        }
        
        if not object_a_positions or not object_b_positions:
            return result
        
        set_b = set(object_b_positions)
        
        for ax, ay in object_a_positions:
            # Check 4-connected adjacency
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                if (ax + dx, ay + dy) in set_b:
                    result['touching'] = True
                    result['contact_points'].append((ax, ay, ax + dx, ay + dy))
        
        result['contact_count'] = len(result['contact_points'])
        return result
    
    def _detect_blocking(
        self,
        controlled_pos: Tuple[int, int],
        intended_direction: str,
        frame: List[List[int]]
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if something blocked movement in intended direction.
        """
        result = {
            'blocked': False,
            'blocking_object_color': None,
            'blocking_position': None
        }
        
        if not controlled_pos or not frame:
            return result
        
        cx, cy = controlled_pos
        height = len(frame)
        width = len(frame[0]) if frame else 0
        
        # Map direction to delta
        direction_map = {
            'up': (0, -1), 'ACTION1': (0, -1),
            'down': (0, 1), 'ACTION2': (0, 1),
            'left': (-1, 0), 'ACTION3': (-1, 0),
            'right': (1, 0), 'ACTION4': (1, 0),
        }
        
        delta = direction_map.get(intended_direction, (0, 0))
        if delta == (0, 0):
            return result
        
        # Check position in intended direction
        nx, ny = cx + delta[0], cy + delta[1]
        
        # Out of bounds = blocked by wall
        if nx < 0 or nx >= width or ny < 0 or ny >= height:
            result['blocked'] = True
            result['blocking_object_color'] = -1  # Wall
            result['blocking_position'] = (nx, ny)
            return result
        
        # Check what's at that position
        blocking_color = frame[ny][nx]
        if blocking_color != 0:  # Non-empty (assuming 0 is background)
            result['blocked'] = True
            result['blocking_object_color'] = blocking_color
            result['blocking_position'] = (nx, ny)
        
        return result
    
    def _detect_pushing(
        self,
        controlled_movement: Tuple[int, int],
        other_objects_before: List[Dict],
        other_objects_after: List[Dict]
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if controlled object pushed another object.
        """
        result = {
            'pushed': False,
            'pushed_object': None,
            'push_direction': None,
            'push_distance': 0
        }
        
        if not controlled_movement or controlled_movement == (0, 0):
            return result
        
        dx, dy = controlled_movement
        
        # Compare object positions before and after
        for obj_before in other_objects_before:
            obj_id = obj_before.get('color') or obj_before.get('id')
            centroid_before = obj_before.get('centroid')
            
            if not centroid_before:
                continue
            
            # Find same object after
            for obj_after in other_objects_after:
                if (obj_after.get('color') or obj_after.get('id')) == obj_id:
                    centroid_after = obj_after.get('centroid')
                    if centroid_after:
                        # Did it move in same direction as us?
                        obj_dx = centroid_after[0] - centroid_before[0]
                        obj_dy = centroid_after[1] - centroid_before[1]
                        
                        # Same direction = pushed
                        if (dx != 0 and obj_dx * dx > 0) or (dy != 0 and obj_dy * dy > 0):
                            result['pushed'] = True
                            result['pushed_object'] = obj_before
                            result['push_direction'] = ('right' if obj_dx > 0 else 'left') if obj_dx != 0 else ('down' if obj_dy > 0 else 'up')
                            result['push_distance'] = abs(obj_dx) + abs(obj_dy)
                            return result
        
        return result
    
    def _detect_overlap(
        self,
        object_a_positions: List[Tuple[int, int]],
        object_b_positions: List[Tuple[int, int]]
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if objects occupy the same pixels.
        """
        result = {
            'overlapping': False,
            'overlap_positions': [],
            'overlap_percentage_a': 0.0,
            'overlap_percentage_b': 0.0
        }
        
        if not object_a_positions or not object_b_positions:
            return result
        
        set_a = set(object_a_positions)
        set_b = set(object_b_positions)
        
        overlap = set_a & set_b
        
        if overlap:
            result['overlapping'] = True
            result['overlap_positions'] = list(overlap)
            result['overlap_percentage_a'] = len(overlap) / len(set_a) if set_a else 0
            result['overlap_percentage_b'] = len(overlap) / len(set_b) if set_b else 0
        
        return result
    
    def _detect_engulfing(
        self,
        outer_object_positions: List[Tuple[int, int]],
        inner_object_positions: List[Tuple[int, int]]
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if one object completely surrounds another.
        """
        result = {
            'engulfed': False,
            'containment_ratio': 0.0
        }
        
        if not outer_object_positions or not inner_object_positions:
            return result
        
        # Get bounding boxes
        outer_xs = [p[0] for p in outer_object_positions]
        outer_ys = [p[1] for p in outer_object_positions]
        inner_xs = [p[0] for p in inner_object_positions]
        inner_ys = [p[1] for p in inner_object_positions]
        
        outer_bounds = (min(outer_xs), min(outer_ys), max(outer_xs), max(outer_ys))
        inner_bounds = (min(inner_xs), min(inner_ys), max(inner_xs), max(inner_ys))
        
        # Check if inner is completely within outer bounds
        if (inner_bounds[0] >= outer_bounds[0] and inner_bounds[1] >= outer_bounds[1] and
            inner_bounds[2] <= outer_bounds[2] and inner_bounds[3] <= outer_bounds[3]):
            result['engulfed'] = True
            result['containment_ratio'] = 1.0
        else:
            # Calculate partial containment
            contained = sum(1 for ix, iy in inner_object_positions 
                          if outer_bounds[0] <= ix <= outer_bounds[2] and 
                             outer_bounds[1] <= iy <= outer_bounds[3])
            result['containment_ratio'] = contained / len(inner_object_positions) if inner_object_positions else 0
        
        return result
    
    def _detect_partial_containment(
        self,
        object_a_positions: List[Tuple[int, int]],
        container_bounds: Tuple[int, int, int, int]
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect partial containment within a bounding region.
        """
        result = {
            'partially_contained': False,
            'fully_contained': False,
            'containment_ratio': 0.0,
            'positions_inside': [],
            'positions_outside': []
        }
        
        if not object_a_positions or not container_bounds:
            return result
        
        x1, y1, x2, y2 = container_bounds
        
        for pos in object_a_positions:
            if x1 <= pos[0] <= x2 and y1 <= pos[1] <= y2:
                result['positions_inside'].append(pos)
            else:
                result['positions_outside'].append(pos)
        
        total = len(object_a_positions)
        inside = len(result['positions_inside'])
        
        result['containment_ratio'] = inside / total if total > 0 else 0
        result['fully_contained'] = inside == total
        result['partially_contained'] = 0 < inside < total
        
        return result
    
    def _detect_nesting(
        self,
        objects_list: List[Dict],
        frame: List[List[int]]
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect nested containment structure.
        """
        result = {
            'has_nesting': False,
            'nesting_levels': 0,
            'nesting_structure': []
        }
        
        if not objects_list or len(objects_list) < 2:
            return result
        
        # Sort objects by area (larger objects might contain smaller)
        objects_by_area = sorted(objects_list, 
                                  key=lambda o: len(o.get('positions', [])), 
                                  reverse=True)
        
        # Check containment relationships
        for i, outer in enumerate(objects_by_area[:-1]):
            outer_bounds = self._get_bounding_box(outer.get('positions', []))
            if not outer_bounds:
                continue
            
            for inner in objects_by_area[i+1:]:
                inner_pos = inner.get('positions', [])
                if not inner_pos:
                    continue
                
                contained = self._detect_partial_containment(inner_pos, outer_bounds)
                if contained['fully_contained']:
                    result['has_nesting'] = True
                    result['nesting_structure'].append({
                        'outer': outer.get('color'),
                        'inner': inner.get('color'),
                        'ratio': contained['containment_ratio']
                    })
        
        result['nesting_levels'] = len(result['nesting_structure'])
        return result
    
    def _get_bounding_box(self, positions: List[Tuple[int, int]]) -> Optional[Tuple[int, int, int, int]]:
        """Helper: Get bounding box of positions."""
        if not positions:
            return None
        xs = [p[0] for p in positions]
        ys = [p[1] for p in positions]
        return (min(xs), min(ys), max(xs), max(ys))
    
    def _detect_wrapping(
        self,
        wrapper_positions: List[Tuple[int, int]],
        wrapped_positions: List[Tuple[int, int]]
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if object A wraps around object B's shape.
        """
        result = {
            'wrapping': False,
            'wrap_coverage': 0.0,
            'wrap_sides': []
        }
        
        if not wrapper_positions or not wrapped_positions:
            return result
        
        # Get bounding box of wrapped object
        wrapped_bounds = self._get_bounding_box(wrapped_positions)
        if not wrapped_bounds:
            return result
        
        x1, y1, x2, y2 = wrapped_bounds
        wrapper_set = set(wrapper_positions)
        
        # Check each side
        sides_covered = []
        
        # Top side
        top_covered = sum(1 for x in range(x1, x2+1) if (x, y1-1) in wrapper_set)
        if top_covered > 0:
            sides_covered.append('top')
        
        # Bottom side
        bottom_covered = sum(1 for x in range(x1, x2+1) if (x, y2+1) in wrapper_set)
        if bottom_covered > 0:
            sides_covered.append('bottom')
        
        # Left side
        left_covered = sum(1 for y in range(y1, y2+1) if (x1-1, y) in wrapper_set)
        if left_covered > 0:
            sides_covered.append('left')
        
        # Right side
        right_covered = sum(1 for y in range(y1, y2+1) if (x2+1, y) in wrapper_set)
        if right_covered > 0:
            sides_covered.append('right')
        
        result['wrap_sides'] = sides_covered
        result['wrap_coverage'] = len(sides_covered) / 4.0
        result['wrapping'] = len(sides_covered) >= 2  # At least 2 sides covered
        
        return result
    
    def _detect_coating(
        self,
        coating_positions: List[Tuple[int, int]],
        base_positions: List[Tuple[int, int]],
        frame: List[List[int]]
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if object A forms a layer over object B.
        """
        result = {
            'coating': False,
            'coverage_ratio': 0.0,
            'layer_thickness': 0
        }
        
        if not coating_positions or not base_positions:
            return result
        
        # Check if coating is adjacent to base on multiple sides
        base_set = set(base_positions)
        coating_set = set(coating_positions)
        
        adjacent_count = 0
        for cx, cy in coating_positions:
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                if (cx + dx, cy + dy) in base_set:
                    adjacent_count += 1
                    break
        
        result['coverage_ratio'] = adjacent_count / len(coating_positions) if coating_positions else 0
        result['coating'] = result['coverage_ratio'] > 0.5  # >50% adjacent to base
        
        return result
    
    def _detect_pass_through(
        self,
        moving_obj_before: Tuple[int, int],
        moving_obj_after: Tuple[int, int],
        stationary_obj: Dict,
        frame_before: List[List[int]],
        frame_after: List[List[int]]
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if object passed through another without stopping.
        """
        result = {
            'passed_through': False,
            'pass_type': None  # 'ghost', 'portal', 'phase'
        }
        
        if not moving_obj_before or not moving_obj_after:
            return result
        
        stationary_positions = stationary_obj.get('positions', [])
        if not stationary_positions:
            return result
        
        stat_set = set(stationary_positions)
        
        # Calculate movement vector
        dx = moving_obj_after[0] - moving_obj_before[0]
        dy = moving_obj_after[1] - moving_obj_before[1]
        
        if dx == 0 and dy == 0:
            return result
        
        # Check if path crossed through stationary object
        steps = max(abs(dx), abs(dy))
        for i in range(1, steps):
            interp_x = moving_obj_before[0] + int(dx * i / steps)
            interp_y = moving_obj_before[1] + int(dy * i / steps)
            
            if (interp_x, interp_y) in stat_set:
                result['passed_through'] = True
                result['pass_type'] = 'ghost'  # Passed through solid object
                return result
        
        return result
    
    def _detect_embedding(
        self,
        embedded_obj_positions: List[Tuple[int, int]],
        host_obj_positions: List[Tuple[int, int]],
        frame_before: List[List[int]],
        frame_after: List[List[int]]
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if object became lodged within another.
        """
        result = {
            'embedded': False,
            'embedding_ratio': 0.0
        }
        
        if not embedded_obj_positions or not host_obj_positions:
            return result
        
        overlap = self._detect_overlap(embedded_obj_positions, host_obj_positions)
        
        if overlap['overlapping'] and overlap['overlap_percentage_a'] > 0.3:
            result['embedded'] = True
            result['embedding_ratio'] = overlap['overlap_percentage_a']
        
        return result
    
    def _detect_proximity_effect(
        self,
        object_a_pos: Tuple[int, int],
        object_b_pos: Tuple[int, int],
        frame_before: List[List[int]],
        frame_after: List[List[int]],
        distance_threshold: int = 5
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if being near an object causes effects without touching.
        """
        result = {
            'proximity_effect': False,
            'effect_type': None,
            'distance': None,
            'frame_changed': False
        }
        
        if not object_a_pos or not object_b_pos:
            return result
        
        # Calculate distance
        dist = abs(object_a_pos[0] - object_b_pos[0]) + abs(object_a_pos[1] - object_b_pos[1])
        result['distance'] = dist
        
        # Check if within threshold
        if dist <= distance_threshold and dist > 1:  # Near but not touching
            # Check for frame changes around object B
            if frame_before and frame_after:
                bx, by = object_b_pos
                changes = 0
                for dx in range(-2, 3):
                    for dy in range(-2, 3):
                        ny, nx = by + dy, bx + dx
                        if 0 <= ny < len(frame_before) and 0 <= nx < len(frame_before[0]):
                            if frame_before[ny][nx] != frame_after[ny][nx]:
                                changes += 1
                
                if changes > 0:
                    result['proximity_effect'] = True
                    result['effect_type'] = 'field_interaction'
                    result['frame_changed'] = True
        
        return result
    
    def _detect_attraction_repulsion(
        self,
        object_positions_history: List[Tuple[int, int]],
        other_object_pos: Tuple[int, int]
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if objects attract or repel each other.
        """
        result = {
            'attraction': False,
            'repulsion': False,
            'neutral': True,
            'strength': 0.0
        }
        
        if not object_positions_history or len(object_positions_history) < 3 or not other_object_pos:
            return result
        
        # Calculate distance trend
        distances = [abs(p[0] - other_object_pos[0]) + abs(p[1] - other_object_pos[1]) 
                    for p in object_positions_history]
        
        # Check trend (getting closer or farther)
        if len(distances) >= 3:
            trend = distances[-1] - distances[0]
            avg_change = trend / len(distances)
            
            if avg_change < -0.5:  # Getting closer
                result['attraction'] = True
                result['neutral'] = False
                result['strength'] = abs(avg_change)
            elif avg_change > 0.5:  # Getting farther
                result['repulsion'] = True
                result['neutral'] = False
                result['strength'] = abs(avg_change)
        
        return result
    
    def _detect_merging(
        self,
        objects_before: List[Dict],
        objects_after: List[Dict],
        frame_before: List[List[int]],
        frame_after: List[List[int]]
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if two objects combined into one.
        """
        result = {
            'merged': False,
            'merged_objects': [],
            'result_object': None
        }
        
        if not objects_before or not objects_after:
            return result
        
        # Count objects by color before and after
        colors_before = set(o.get('color') for o in objects_before if o.get('color'))
        colors_after = set(o.get('color') for o in objects_after if o.get('color'))
        
        # Check if fewer distinct objects after
        count_before = len(objects_before)
        count_after = len(objects_after)
        
        if count_after < count_before:
            # Find which objects disappeared
            for obj in objects_before:
                obj_color = obj.get('color')
                # Check if this color still exists with same position
                still_exists = any(
                    o.get('color') == obj_color and o.get('centroid') == obj.get('centroid')
                    for o in objects_after
                )
                if not still_exists:
                    result['merged_objects'].append(obj)
            
            if len(result['merged_objects']) >= 2:
                result['merged'] = True
        
        return result
    
    def _detect_adhesion(
        self,
        object_a_movement: Tuple[int, int],
        object_b_movement: Tuple[int, int],
        were_adjacent: bool
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if objects stuck together and now move as one.
        """
        result = {
            'adhered': False,
            'movement_correlation': 0.0
        }
        
        if not object_a_movement or not object_b_movement:
            return result
        
        # If they were adjacent and now move the same way, they're stuck
        if were_adjacent:
            if object_a_movement == object_b_movement:
                result['adhered'] = True
                result['movement_correlation'] = 1.0
            elif (object_a_movement[0] * object_b_movement[0] > 0 or 
                  object_a_movement[1] * object_b_movement[1] > 0):
                # Same direction, different magnitude
                result['movement_correlation'] = 0.5
        
        return result
    
    def _detect_snapping(
        self,
        object_pos_before: Tuple[int, int],
        object_pos_after: Tuple[int, int],
        snap_points: List[Tuple[int, int]]
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if object snapped to a specific position.
        """
        result = {
            'snapped': False,
            'snap_point': None,
            'snap_distance': None
        }
        
        if not object_pos_before or not object_pos_after or not snap_points:
            return result
        
        # Check if after position is exactly on a snap point
        for snap in snap_points:
            if object_pos_after == snap:
                # Calculate how far we "jumped" to this point
                expected_dist = abs(object_pos_after[0] - object_pos_before[0]) + \
                               abs(object_pos_after[1] - object_pos_before[1])
                
                if expected_dist > 1:  # Moved more than 1 step = snapped
                    result['snapped'] = True
                    result['snap_point'] = snap
                    result['snap_distance'] = expected_dist
                    return result
        
        return result
    
    def _hypothesize_interaction_type(
        self,
        object_a: Dict,
        object_b: Dict,
        frame: List[List[int]]
    ) -> List[str]:
        """
        BIRTHRIGHT: Hypothesize what interaction types are possible between objects.
        """
        hypotheses = []
        
        if not object_a or not object_b:
            return hypotheses
        
        pos_a = object_a.get('positions', [])
        pos_b = object_b.get('positions', [])
        
        if not pos_a or not pos_b:
            return hypotheses
        
        # Calculate current relationship
        contact = self._detect_contact(pos_a, pos_b)
        overlap = self._detect_overlap(pos_a, pos_b)
        
        # Based on current state, hypothesize possible interactions
        if contact['touching']:
            hypotheses.extend(['collision', 'pushing', 'blocking', 'adhesion'])
        elif overlap['overlapping']:
            hypotheses.extend(['pass_through', 'embedding', 'merging'])
        else:
            # Not touching - proximity effects possible
            dist = self._get_min_distance(pos_a, pos_b)
            if dist < 5:
                hypotheses.extend(['proximity_effect', 'attraction', 'repulsion', 'snapping'])
            else:
                hypotheses.extend(['collision', 'contact', 'proximity_effect'])
        
        # Size-based hypotheses
        size_a = len(pos_a)
        size_b = len(pos_b)
        
        if size_a > size_b * 2:
            hypotheses.extend(['engulfing', 'containing'])
        elif size_b > size_a * 2:
            hypotheses.extend(['entering', 'being_engulfed'])
        
        return list(set(hypotheses))  # Remove duplicates
    
    def _get_min_distance(
        self,
        positions_a: List[Tuple[int, int]],
        positions_b: List[Tuple[int, int]]
    ) -> int:
        """Helper: Get minimum Manhattan distance between two position sets."""
        if not positions_a or not positions_b:
            return float('inf')
        
        min_dist = float('inf')
        for ax, ay in positions_a:
            for bx, by in positions_b:
                dist = abs(ax - bx) + abs(ay - by)
                min_dist = min(min_dist, dist)
        
        return min_dist
    
    def _test_interaction_hypothesis(
        self,
        hypothesis_type: str,
        objects: List[Dict],
        frame_before: List[List[int]],
        frame_after: List[List[int]],
        action_taken: str
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Test a specific interaction hypothesis.
        """
        result = {
            'hypothesis': hypothesis_type,
            'confirmed': False,
            'confidence': 0.0,
            'evidence': {}
        }
        
        if len(objects) < 2:
            return result
        
        obj_a, obj_b = objects[0], objects[1]
        pos_a = obj_a.get('positions', [])
        pos_b = obj_b.get('positions', [])
        
        # Test based on hypothesis type
        if hypothesis_type == 'collision':
            # Check if objects are now adjacent and one stopped moving
            contact = self._detect_contact(pos_a, pos_b)
            if contact['touching']:
                result['confirmed'] = True
                result['confidence'] = 0.8
                result['evidence'] = contact
        
        elif hypothesis_type == 'overlap':
            overlap = self._detect_overlap(pos_a, pos_b)
            if overlap['overlapping']:
                result['confirmed'] = True
                result['confidence'] = 0.9
                result['evidence'] = overlap
        
        elif hypothesis_type == 'engulfing':
            engulf = self._detect_engulfing(pos_a, pos_b)
            if engulf['engulfed']:
                result['confirmed'] = True
                result['confidence'] = 0.9
                result['evidence'] = engulf
        
        elif hypothesis_type in ['proximity_effect', 'attraction', 'repulsion']:
            centroid_a = obj_a.get('centroid', (0, 0))
            centroid_b = obj_b.get('centroid', (0, 0))
            prox = self._detect_proximity_effect(centroid_a, centroid_b, frame_before, frame_after)
            if prox['proximity_effect']:
                result['confirmed'] = True
                result['confidence'] = 0.7
                result['evidence'] = prox
        
        return result
    
    def _get_interaction_effect(
        self,
        interaction_type: str,
        frame_before: List[List[int]],
        frame_after: List[List[int]],
        score_before: float,
        score_after: float
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Get the EFFECT of an interaction.
        """
        result = {
            'interaction_type': interaction_type,
            'score_changed': score_after != score_before,
            'score_delta': score_after - score_before,
            'frame_changed': False,
            'effect_type': 'neutral'
        }
        
        # Check frame changes
        if frame_before and frame_after:
            changes = 0
            for y in range(min(len(frame_before), len(frame_after))):
                for x in range(min(len(frame_before[0]), len(frame_after[0]))):
                    if frame_before[y][x] != frame_after[y][x]:
                        changes += 1
            
            result['frame_changed'] = changes > 0
            result['pixels_changed'] = changes
        
        # Classify effect
        if result['score_delta'] > 0:
            result['effect_type'] = 'positive'  # Good interaction!
        elif result['score_delta'] < 0:
            result['effect_type'] = 'negative'  # Bad interaction
        elif result['frame_changed']:
            result['effect_type'] = 'state_change'  # Something happened
        else:
            result['effect_type'] = 'neutral'  # No visible effect
        
        return result
    
    # ======================================================================
    # MOTION RELATIONSHIP IMPLEMENTATIONS (BIRTHRIGHT)
    # ======================================================================
    
    def _detect_following(
        self,
        leader_positions_history: List[Tuple[int, int]],
        follower_positions_history: List[Tuple[int, int]],
        lag_frames: int = 1
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if one object follows/tracks another's movement.
        """
        result = {
            'following': False,
            'correlation': 0.0,
            'lag': lag_frames,
            'follow_type': None  # 'exact', 'delayed', 'approximate'
        }
        
        if not leader_positions_history or not follower_positions_history:
            return result
        
        if len(leader_positions_history) < 3 or len(follower_positions_history) < 3:
            return result
        
        # Calculate leader movements
        leader_movements = []
        for i in range(1, len(leader_positions_history)):
            dx = leader_positions_history[i][0] - leader_positions_history[i-1][0]
            dy = leader_positions_history[i][1] - leader_positions_history[i-1][1]
            leader_movements.append((dx, dy))
        
        # Calculate follower movements (with lag offset)
        follower_movements = []
        for i in range(1, len(follower_positions_history)):
            dx = follower_positions_history[i][0] - follower_positions_history[i-1][0]
            dy = follower_positions_history[i][1] - follower_positions_history[i-1][1]
            follower_movements.append((dx, dy))
        
        # Compare movements (accounting for lag)
        matches = 0
        comparisons = 0
        offset = lag_frames
        
        for i in range(len(leader_movements)):
            follower_idx = i + offset
            if follower_idx < len(follower_movements):
                if leader_movements[i] == follower_movements[follower_idx]:
                    matches += 1
                comparisons += 1
        
        if comparisons > 0:
            result['correlation'] = matches / comparisons
            if result['correlation'] > 0.7:
                result['following'] = True
                result['follow_type'] = 'exact' if result['correlation'] > 0.9 else 'approximate'
        
        return result
    
    def _detect_mirroring(
        self,
        object_a_movements: List[Tuple[int, int]],
        object_b_movements: List[Tuple[int, int]],
        mirror_axis: str = 'auto'  # 'x', 'y', 'auto'
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if objects move in mirrored/symmetric patterns.
        """
        result = {
            'mirroring': False,
            'mirror_axis': None,
            'correlation': 0.0,
            'mirror_type': None  # 'horizontal', 'vertical', 'inverse'
        }
        
        if not object_a_movements or not object_b_movements:
            return result
        
        min_len = min(len(object_a_movements), len(object_b_movements))
        if min_len < 2:
            return result
        
        # Check different mirror types
        x_mirror_matches = 0  # Movement mirrored on X axis (opposite X, same Y)
        y_mirror_matches = 0  # Movement mirrored on Y axis (same X, opposite Y)
        inverse_matches = 0   # Completely opposite movement
        
        for i in range(min_len):
            ax, ay = object_a_movements[i]
            bx, by = object_b_movements[i]
            
            if ax == -bx and ay == by:
                x_mirror_matches += 1
            if ax == bx and ay == -by:
                y_mirror_matches += 1
            if ax == -bx and ay == -by:
                inverse_matches += 1
        
        # Find best match
        x_corr = x_mirror_matches / min_len
        y_corr = y_mirror_matches / min_len
        inv_corr = inverse_matches / min_len
        
        best_corr = max(x_corr, y_corr, inv_corr)
        
        if best_corr > 0.6:
            result['mirroring'] = True
            result['correlation'] = best_corr
            if best_corr == x_corr:
                result['mirror_axis'] = 'y'  # Mirrored across Y axis
                result['mirror_type'] = 'horizontal'
            elif best_corr == y_corr:
                result['mirror_axis'] = 'x'  # Mirrored across X axis
                result['mirror_type'] = 'vertical'
            else:
                result['mirror_axis'] = 'both'
                result['mirror_type'] = 'inverse'
        
        return result
    
    def _detect_chasing(
        self,
        chaser_positions_history: List[Tuple[int, int]],
        target_positions_history: List[Tuple[int, int]]
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect goal-directed pursuit - one object moving toward another.
        """
        result = {
            'chasing': False,
            'approach_rate': 0.0,
            'chase_efficiency': 0.0
        }
        
        if not chaser_positions_history or not target_positions_history:
            return result
        
        if len(chaser_positions_history) < 3:
            return result
        
        # Calculate distances over time
        distances = []
        for i, chaser_pos in enumerate(chaser_positions_history):
            # Use corresponding target position or last known
            target_idx = min(i, len(target_positions_history) - 1)
            target_pos = target_positions_history[target_idx]
            dist = abs(chaser_pos[0] - target_pos[0]) + abs(chaser_pos[1] - target_pos[1])
            distances.append(dist)
        
        # Check if distance is decreasing (approaching)
        if len(distances) >= 3:
            decreasing = sum(1 for i in range(1, len(distances)) if distances[i] < distances[i-1])
            approach_ratio = decreasing / (len(distances) - 1)
            
            result['approach_rate'] = approach_ratio
            
            if approach_ratio > 0.6:
                result['chasing'] = True
                # Calculate efficiency (direct path vs actual path)
                if distances[0] > 0:
                    result['chase_efficiency'] = (distances[0] - distances[-1]) / distances[0]
        
        return result
    
    def _detect_fleeing(
        self,
        fleeing_positions_history: List[Tuple[int, int]],
        threat_positions_history: List[Tuple[int, int]]
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if object is moving away from another (avoidance).
        """
        result = {
            'fleeing': False,
            'retreat_rate': 0.0,
            'escape_efficiency': 0.0
        }
        
        if not fleeing_positions_history or not threat_positions_history:
            return result
        
        if len(fleeing_positions_history) < 3:
            return result
        
        # Calculate distances over time
        distances = []
        for i, flee_pos in enumerate(fleeing_positions_history):
            threat_idx = min(i, len(threat_positions_history) - 1)
            threat_pos = threat_positions_history[threat_idx]
            dist = abs(flee_pos[0] - threat_pos[0]) + abs(flee_pos[1] - threat_pos[1])
            distances.append(dist)
        
        # Check if distance is increasing (retreating)
        if len(distances) >= 3:
            increasing = sum(1 for i in range(1, len(distances)) if distances[i] > distances[i-1])
            retreat_ratio = increasing / (len(distances) - 1)
            
            result['retreat_rate'] = retreat_ratio
            
            if retreat_ratio > 0.6:
                result['fleeing'] = True
                if distances[0] > 0:
                    result['escape_efficiency'] = (distances[-1] - distances[0]) / distances[0]
        
        return result
    
    def _detect_synchronized_movement(
        self,
        objects_movements_history: List[List[Tuple[int, int]]]
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if multiple objects move together in coordinated way.
        """
        result = {
            'synchronized': False,
            'sync_ratio': 0.0,
            'sync_groups': [],
            'sync_type': None  # 'same_direction', 'formation', 'wave'
        }
        
        if not objects_movements_history or len(objects_movements_history) < 2:
            return result
        
        # Check if all objects move the same way at the same time
        num_objects = len(objects_movements_history)
        history_len = min(len(h) for h in objects_movements_history) if objects_movements_history else 0
        
        if history_len < 2:
            return result
        
        sync_frames = 0
        for t in range(history_len):
            movements_at_t = [h[t] for h in objects_movements_history]
            # Check if all movements are the same
            if len(set(movements_at_t)) == 1 and movements_at_t[0] != (0, 0):
                sync_frames += 1
        
        result['sync_ratio'] = sync_frames / history_len if history_len > 0 else 0
        
        if result['sync_ratio'] > 0.5:
            result['synchronized'] = True
            result['sync_type'] = 'same_direction'
            result['sync_groups'] = list(range(num_objects))
        
        return result
    
    def _detect_dragging(
        self,
        dragger_movement: Tuple[int, int],
        dragged_movement: Tuple[int, int],
        were_connected: bool
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if moving object pulls another along through connection.
        """
        result = {
            'dragging': False,
            'drag_direction': None,
            'drag_efficiency': 0.0
        }
        
        if not dragger_movement or not dragged_movement:
            return result
        
        if not were_connected:
            return result
        
        # If connected and both moved in same direction, dragging occurred
        dx_dragger, dy_dragger = dragger_movement
        dx_dragged, dy_dragged = dragged_movement
        
        if dx_dragger == 0 and dy_dragger == 0:
            return result  # Dragger didn't move
        
        # Check if dragged moved in same direction
        same_x_direction = (dx_dragger * dx_dragged > 0) or (dx_dragger == 0 and dx_dragged == 0)
        same_y_direction = (dy_dragger * dy_dragged > 0) or (dy_dragger == 0 and dy_dragged == 0)
        
        if same_x_direction and same_y_direction and (dx_dragged != 0 or dy_dragged != 0):
            result['dragging'] = True
            if dx_dragger > 0:
                result['drag_direction'] = 'right'
            elif dx_dragger < 0:
                result['drag_direction'] = 'left'
            elif dy_dragger > 0:
                result['drag_direction'] = 'down'
            else:
                result['drag_direction'] = 'up'
            
            # Efficiency: did dragged move same amount as dragger?
            dragger_dist = abs(dx_dragger) + abs(dy_dragger)
            dragged_dist = abs(dx_dragged) + abs(dy_dragged)
            result['drag_efficiency'] = min(dragged_dist, dragger_dist) / max(dragged_dist, dragger_dist) if dragger_dist > 0 else 0
        
        return result
    
    # ======================================================================
    # TOPOLOGICAL RELATIONSHIP IMPLEMENTATIONS (BIRTHRIGHT)
    # ======================================================================
    
    def _detect_adjacency(
        self,
        object_a_positions: List[Tuple[int, int]],
        object_b_positions: List[Tuple[int, int]]
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if objects share boundary/edge without overlapping.
        """
        result = {
            'adjacent': False,
            'shared_boundary_length': 0,
            'boundary_positions': []
        }
        
        if not object_a_positions or not object_b_positions:
            return result
        
        set_a = set(object_a_positions)
        set_b = set(object_b_positions)
        
        # Check for overlap first - adjacency means NO overlap
        if set_a & set_b:
            return result  # Objects overlap, not adjacent
        
        # Find boundary pixels (adjacent but not overlapping)
        for ax, ay in object_a_positions:
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                neighbor = (ax + dx, ay + dy)
                if neighbor in set_b:
                    result['adjacent'] = True
                    result['boundary_positions'].append((ax, ay, neighbor[0], neighbor[1]))
        
        result['shared_boundary_length'] = len(result['boundary_positions'])
        return result
    
    def _detect_connectivity(
        self,
        objects_list: List[Dict],
        frame: List[List[int]]
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if objects form connected network through shared pixels/paths.
        """
        result = {
            'connected': False,
            'connection_graph': {},
            'num_components': 0,
            'largest_component': []
        }
        
        if not objects_list or len(objects_list) < 2:
            return result
        
        # Build adjacency graph
        n = len(objects_list)
        adjacency = {i: [] for i in range(n)}
        
        for i in range(n):
            pos_i = objects_list[i].get('positions', [])
            for j in range(i + 1, n):
                pos_j = objects_list[j].get('positions', [])
                adj = self._detect_adjacency(pos_i, pos_j)
                if adj['adjacent']:
                    adjacency[i].append(j)
                    adjacency[j].append(i)
        
        # Find connected components using BFS
        visited = set()
        components = []
        
        for start in range(n):
            if start in visited:
                continue
            component = []
            queue = [start]
            while queue:
                node = queue.pop(0)
                if node in visited:
                    continue
                visited.add(node)
                component.append(node)
                queue.extend([neighbor for neighbor in adjacency[node] if neighbor not in visited])
            components.append(component)
        
        result['num_components'] = len(components)
        result['connected'] = len(components) == 1  # All objects in one component
        result['connection_graph'] = adjacency
        result['largest_component'] = max(components, key=len) if components else []
        
        return result
    
    def _detect_path_between(
        self,
        start_pos: Tuple[int, int],
        end_pos: Tuple[int, int],
        frame: List[List[int]],
        passable_colors: List[int] = None
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if traversable path exists between two positions.
        """
        result = {
            'path_exists': False,
            'path_length': -1,
            'path': []
        }
        
        if not frame or not start_pos or not end_pos:
            return result
        
        height = len(frame)
        width = len(frame[0]) if frame else 0
        
        if passable_colors is None:
            passable_colors = [0]  # Default: only background (0) is passable
        
        passable_set = set(passable_colors)
        
        # BFS to find path
        from collections import deque
        
        visited = set()
        queue = deque([(start_pos, [start_pos])])
        visited.add(start_pos)
        
        while queue:
            (x, y), path = queue.popleft()
            
            if (x, y) == end_pos:
                result['path_exists'] = True
                result['path_length'] = len(path)
                result['path'] = path
                return result
            
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in visited:
                    if frame[ny][nx] in passable_set or (nx, ny) == end_pos:
                        visited.add((nx, ny))
                        queue.append(((nx, ny), path + [(nx, ny)]))
        
        return result
    
    def _detect_separation(
        self,
        object_a_positions: List[Tuple[int, int]],
        object_b_positions: List[Tuple[int, int]]
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if objects are completely disconnected with space between.
        """
        result = {
            'separated': True,
            'min_distance': float('inf'),
            'separation_type': 'distant'  # 'distant', 'nearby', 'touching'
        }
        
        if not object_a_positions or not object_b_positions:
            return result
        
        # Find minimum distance between any two pixels
        min_dist = float('inf')
        for ax, ay in object_a_positions:
            for bx, by in object_b_positions:
                dist = abs(ax - bx) + abs(ay - by)
                min_dist = min(min_dist, dist)
                if dist == 0:  # Overlap
                    result['separated'] = False
                    result['min_distance'] = 0
                    result['separation_type'] = 'overlapping'
                    return result
                if dist == 1:  # Adjacent
                    result['separated'] = False
                    result['min_distance'] = 1
                    result['separation_type'] = 'touching'
                    return result
        
        result['min_distance'] = min_dist
        result['separation_type'] = 'nearby' if min_dist <= 3 else 'distant'
        return result
    
    def _detect_surrounding(
        self,
        surrounding_objects: List[Dict],
        center_object_positions: List[Tuple[int, int]]
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if multiple objects collectively encircle another.
        """
        result = {
            'surrounded': False,
            'encirclement_ratio': 0.0,
            'surrounding_directions': []
        }
        
        if not surrounding_objects or not center_object_positions:
            return result
        
        # Get center of the object being surrounded
        cx = sum(p[0] for p in center_object_positions) // len(center_object_positions)
        cy = sum(p[1] for p in center_object_positions) // len(center_object_positions)
        
        # Check 8 directions from center
        directions = {
            'N': (0, -1), 'S': (0, 1), 'E': (1, 0), 'W': (-1, 0),
            'NE': (1, -1), 'NW': (-1, -1), 'SE': (1, 1), 'SW': (-1, 1)
        }
        
        blocked_directions = set()
        
        for obj in surrounding_objects:
            obj_positions = set(obj.get('positions', []))
            
            for dir_name, (dx, dy) in directions.items():
                # Check along this direction
                for dist in range(1, 20):  # Check up to 20 pixels away
                    check_pos = (cx + dx * dist, cy + dy * dist)
                    if check_pos in obj_positions:
                        blocked_directions.add(dir_name)
                        break
        
        result['surrounding_directions'] = list(blocked_directions)
        result['encirclement_ratio'] = len(blocked_directions) / 8.0
        result['surrounded'] = len(blocked_directions) >= 6  # At least 6 of 8 directions blocked
        
        return result
    
    # ======================================================================
    # SUPPORT & DEPENDENCY IMPLEMENTATIONS (BIRTHRIGHT)
    # ======================================================================
    
    def _detect_supporting(
        self,
        support_object_positions: List[Tuple[int, int]],
        supported_object_positions: List[Tuple[int, int]],
        gravity_direction: str = 'down'
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if object A is supporting/holding up object B.
        """
        result = {
            'supporting': False,
            'support_points': [],
            'support_ratio': 0.0
        }
        
        if not support_object_positions or not supported_object_positions:
            return result
        
        support_set = set(support_object_positions)
        
        # Determine which direction is "below" based on gravity
        if gravity_direction == 'down':
            dy = 1  # Check below supported object
        elif gravity_direction == 'up':
            dy = -1
        else:
            dy = 1  # Default
        
        # Check if support object is directly below supported object
        support_count = 0
        for sx, sy in supported_object_positions:
            below_pos = (sx, sy + dy)
            if below_pos in support_set:
                result['support_points'].append((sx, sy))
                support_count += 1
        
        if support_count > 0:
            result['supporting'] = True
            result['support_ratio'] = support_count / len(supported_object_positions)
        
        return result
    
    def _detect_stacking(
        self,
        objects_list: List[Dict],
        gravity_direction: str = 'down'
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect vertical arrangement where each level supports the one above.
        """
        result = {
            'stacked': False,
            'stack_order': [],  # Bottom to top
            'stack_height': 0
        }
        
        if not objects_list or len(objects_list) < 2:
            return result
        
        # Sort objects by Y position (bottom to top for down gravity)
        if gravity_direction == 'down':
            sorted_objects = sorted(objects_list, 
                                   key=lambda o: max(p[1] for p in o.get('positions', [(0, 0)])),
                                   reverse=True)
        else:
            sorted_objects = sorted(objects_list,
                                   key=lambda o: min(p[1] for p in o.get('positions', [(0, 0)])))
        
        # Check for support chain
        stack = []
        for i, obj in enumerate(sorted_objects):
            if i == 0:
                stack.append(obj.get('color', i))
                continue
            
            # Check if this object is supported by previous one
            prev_obj = sorted_objects[i - 1]
            support = self._detect_supporting(
                prev_obj.get('positions', []),
                obj.get('positions', []),
                gravity_direction
            )
            
            if support['supporting']:
                stack.append(obj.get('color', i))
            else:
                break  # Stack broken
        
        if len(stack) >= 2:
            result['stacked'] = True
            result['stack_order'] = stack
            result['stack_height'] = len(stack)
        
        return result
    
    def _detect_hanging(
        self,
        hanging_object_positions: List[Tuple[int, int]],
        anchor_positions: List[Tuple[int, int]],
        frame: List[List[int]]
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if object is suspended/hanging from above.
        """
        result = {
            'hanging': False,
            'anchor_point': None,
            'hang_length': 0
        }
        
        if not hanging_object_positions or not anchor_positions:
            return result
        
        anchor_set = set(anchor_positions)
        
        # Find topmost point of hanging object
        top_y = min(p[1] for p in hanging_object_positions)
        top_points = [p for p in hanging_object_positions if p[1] == top_y]
        
        # Check if anchor is directly above
        for tx, ty in top_points:
            for check_y in range(ty - 1, -1, -1):
                if (tx, check_y) in anchor_set:
                    result['hanging'] = True
                    result['anchor_point'] = (tx, check_y)
                    result['hang_length'] = ty - check_y
                    return result
        
        return result
    
    def _detect_leaning(
        self,
        leaning_object_positions: List[Tuple[int, int]],
        support_object_positions: List[Tuple[int, int]]
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if object relies on another for angular stability.
        """
        result = {
            'leaning': False,
            'lean_angle': None,  # 'left', 'right'
            'contact_point': None
        }
        
        if not leaning_object_positions or not support_object_positions:
            return result
        
        # Get bounding boxes
        lean_xs = [p[0] for p in leaning_object_positions]
        lean_ys = [p[1] for p in leaning_object_positions]
        support_set = set(support_object_positions)
        
        # Check for contact on sides (not directly below)
        left_contact = False
        right_contact = False
        
        for lx, ly in leaning_object_positions:
            # Check left
            if (lx - 1, ly) in support_set:
                left_contact = True
                result['contact_point'] = (lx, ly)
            # Check right
            if (lx + 1, ly) in support_set:
                right_contact = True
                result['contact_point'] = (lx, ly)
        
        # Object is leaning if it touches support on side but not fully below
        if left_contact and not right_contact:
            result['leaning'] = True
            result['lean_angle'] = 'left'
        elif right_contact and not left_contact:
            result['leaning'] = True
            result['lean_angle'] = 'right'
        
        return result
    
    # ======================================================================
    # HIERARCHICAL & ORGANIZATIONAL IMPLEMENTATIONS (BIRTHRIGHT)
    # ======================================================================
    
    def _detect_clustering(
        self,
        objects_list: List[Dict],
        grouping_threshold: int = 3
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect objects grouped by proximity or shared properties.
        """
        result = {
            'has_clusters': False,
            'num_clusters': 0,
            'clusters': [],
            'cluster_sizes': []
        }
        
        if not objects_list or len(objects_list) < 2:
            return result
        
        # Calculate centroid distances between all objects
        n = len(objects_list)
        centroids = []
        for obj in objects_list:
            positions = obj.get('positions', [])
            if positions:
                cx = sum(p[0] for p in positions) // len(positions)
                cy = sum(p[1] for p in positions) // len(positions)
                centroids.append((cx, cy))
            else:
                centroids.append((0, 0))
        
        # Simple clustering: group objects within threshold distance
        assigned = [False] * n
        clusters = []
        
        for i in range(n):
            if assigned[i]:
                continue
            
            cluster = [i]
            assigned[i] = True
            
            for j in range(i + 1, n):
                if assigned[j]:
                    continue
                
                # Check distance to any object in current cluster
                for member in cluster:
                    dist = abs(centroids[j][0] - centroids[member][0]) + \
                           abs(centroids[j][1] - centroids[member][1])
                    if dist <= grouping_threshold:
                        cluster.append(j)
                        assigned[j] = True
                        break
            
            clusters.append(cluster)
        
        result['num_clusters'] = len(clusters)
        result['clusters'] = clusters
        result['cluster_sizes'] = [len(c) for c in clusters]
        result['has_clusters'] = any(len(c) > 1 for c in clusters)
        
        return result
    
    def _detect_layering(
        self,
        objects_list: List[Dict],
        frame: List[List[int]]
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect Z-order/depth relationships - what's in front of what.
        """
        result = {
            'has_layering': False,
            'layer_order': [],  # Back to front
            'overlaps': []
        }
        
        if not objects_list or len(objects_list) < 2:
            return result
        
        n = len(objects_list)
        
        # Find overlapping pairs and determine which is "on top"
        # In a 2D frame, the color that appears at a pixel is the "top" layer
        for i in range(n):
            pos_i = set(objects_list[i].get('positions', []))
            color_i = objects_list[i].get('color')
            
            for j in range(i + 1, n):
                pos_j = set(objects_list[j].get('positions', []))
                color_j = objects_list[j].get('color')
                
                overlap = pos_i & pos_j
                if overlap and frame:
                    # Check which color is visible at overlap positions
                    for ox, oy in list(overlap)[:1]:  # Check first overlap pixel
                        if 0 <= oy < len(frame) and 0 <= ox < len(frame[0]):
                            visible_color = frame[oy][ox]
                            if visible_color == color_i:
                                result['overlaps'].append({'top': i, 'bottom': j})
                            elif visible_color == color_j:
                                result['overlaps'].append({'top': j, 'bottom': i})
                            result['has_layering'] = True
        
        # Build layer order from overlaps
        if result['overlaps']:
            # Simple ordering: objects that are on top of others
            top_counts = {i: 0 for i in range(n)}
            for overlap in result['overlaps']:
                top_counts[overlap['top']] += 1
            
            result['layer_order'] = sorted(range(n), key=lambda x: top_counts[x])
        
        return result
    
    def _detect_attachment(
        self,
        object_a_movements: List[Tuple[int, int]],
        object_b_movements: List[Tuple[int, int]],
        were_adjacent: bool
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if objects are attached and move as a unit.
        """
        result = {
            'attached': False,
            'attachment_strength': 0.0
        }
        
        if not object_a_movements or not object_b_movements:
            return result
        
        if not were_adjacent:
            return result  # Can't be attached if not adjacent
        
        # Check if movements are identical
        min_len = min(len(object_a_movements), len(object_b_movements))
        if min_len == 0:
            return result
        
        matching = sum(1 for i in range(min_len) if object_a_movements[i] == object_b_movements[i])
        result['attachment_strength'] = matching / min_len
        result['attached'] = result['attachment_strength'] > 0.8
        
        return result
    
    def _detect_part_whole(
        self,
        potential_part_positions: List[Tuple[int, int]],
        potential_whole_positions: List[Tuple[int, int]]
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect part-whole relationships (component is part of larger object).
        """
        result = {
            'is_part': False,
            'containment_ratio': 0.0,
            'relationship': None  # 'contained', 'connected', 'separate'
        }
        
        if not potential_part_positions or not potential_whole_positions:
            return result
        
        part_set = set(potential_part_positions)
        whole_set = set(potential_whole_positions)
        
        # Check how much of part is within whole
        contained = part_set & whole_set
        result['containment_ratio'] = len(contained) / len(part_set) if part_set else 0
        
        if result['containment_ratio'] > 0.8:
            result['is_part'] = True
            result['relationship'] = 'contained'
        elif result['containment_ratio'] > 0:
            result['relationship'] = 'overlapping'
        else:
            # Check if adjacent (connected part)
            for px, py in potential_part_positions:
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    if (px + dx, py + dy) in whole_set:
                        result['is_part'] = True
                        result['relationship'] = 'connected'
                        return result
            result['relationship'] = 'separate'
        
        return result
    
    # ======================================================================
    # TEMPORAL RELATIONSHIP IMPLEMENTATIONS (BIRTHRIGHT)
    # ======================================================================
    
    def _detect_causation(
        self,
        action_taken: str,
        state_before: Dict,
        state_after: Dict,
        time_delta: int = 1
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if action/event A directly caused change B.
        """
        result = {
            'caused_change': False,
            'confidence': 0.0,
            'changes': [],
            'causation_type': None  # 'direct', 'indirect', 'coincidental'
        }
        
        if not state_before or not state_after:
            return result
        
        # Compare states to find changes
        changes = []
        
        # Check score change
        score_before = state_before.get('score', 0)
        score_after = state_after.get('score', 0)
        if score_before != score_after:
            changes.append({'type': 'score', 'delta': score_after - score_before})
        
        # Check position changes
        pos_before = state_before.get('position')
        pos_after = state_after.get('position')
        if pos_before and pos_after and pos_before != pos_after:
            changes.append({'type': 'position', 'from': pos_before, 'to': pos_after})
        
        # Check object count changes
        objects_before = state_before.get('object_count', 0)
        objects_after = state_after.get('object_count', 0)
        if objects_before != objects_after:
            changes.append({'type': 'object_count', 'delta': objects_after - objects_before})
        
        result['changes'] = changes
        
        if changes:
            result['caused_change'] = True
            # If immediate (time_delta=1), likely direct causation
            if time_delta == 1:
                result['causation_type'] = 'direct'
                result['confidence'] = 0.9
            else:
                result['causation_type'] = 'indirect'
                result['confidence'] = 0.6
        
        return result
    
    def _detect_precedence(
        self,
        event_sequence: List[Dict],
        event_a: str,
        event_b: str
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if event A must occur before event B can happen.
        """
        result = {
            'precedence_detected': False,
            'a_before_b_count': 0,
            'b_before_a_count': 0,
            'confidence': 0.0
        }
        
        if not event_sequence:
            return result
        
        # Count occurrences of A before B vs B before A
        last_a_idx = -1
        last_b_idx = -1
        
        for i, event in enumerate(event_sequence):
            event_type = event.get('type', event.get('name', ''))
            
            if event_type == event_a:
                last_a_idx = i
            elif event_type == event_b:
                if last_a_idx >= 0 and last_a_idx < i:
                    result['a_before_b_count'] += 1
                if last_b_idx >= 0:
                    result['b_before_a_count'] += 1
                last_b_idx = i
        
        total = result['a_before_b_count'] + result['b_before_a_count']
        if total > 0:
            ratio = result['a_before_b_count'] / total
            if ratio > 0.8:
                result['precedence_detected'] = True
                result['confidence'] = ratio
        
        return result
    
    def _detect_simultaneity(
        self,
        events_with_timestamps: List[Dict]
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if multiple events/changes occur at the same time.
        """
        result = {
            'simultaneous_events': False,
            'event_groups': [],
            'max_simultaneous': 0
        }
        
        if not events_with_timestamps:
            return result
        
        # Group events by timestamp
        by_time = {}
        for event in events_with_timestamps:
            t = event.get('timestamp', event.get('time', 0))
            if t not in by_time:
                by_time[t] = []
            by_time[t].append(event)
        
        # Find groups with multiple events
        for t, events in by_time.items():
            if len(events) > 1:
                result['event_groups'].append({
                    'time': t,
                    'events': events,
                    'count': len(events)
                })
        
        if result['event_groups']:
            result['simultaneous_events'] = True
            result['max_simultaneous'] = max(g['count'] for g in result['event_groups'])
        
        return result
    
    def _detect_periodic(
        self,
        state_history: List[Any],
        min_period: int = 2,
        max_period: int = 10
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect repeating patterns/cycles in events or states.
        """
        result = {
            'periodic': False,
            'period': None,
            'confidence': 0.0,
            'pattern': []
        }
        
        if not state_history or len(state_history) < min_period * 2:
            return result
        
        # Try different period lengths
        best_period = None
        best_confidence = 0
        
        for period in range(min_period, min(max_period + 1, len(state_history) // 2)):
            matches = 0
            comparisons = 0
            
            for i in range(len(state_history) - period):
                if state_history[i] == state_history[i + period]:
                    matches += 1
                comparisons += 1
            
            confidence = matches / comparisons if comparisons > 0 else 0
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_period = period
        
        if best_confidence > 0.7:
            result['periodic'] = True
            result['period'] = best_period
            result['confidence'] = best_confidence
            result['pattern'] = state_history[:best_period]
        
        return result
    
    def _detect_decay_persistence(
        self,
        effect_history: List[bool],
        initial_event_time: int
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect how long effects or relationships last after initial event.
        """
        result = {
            'persists': False,
            'duration': 0,
            'decay_type': None  # 'instant', 'gradual', 'permanent'
        }
        
        if not effect_history or initial_event_time >= len(effect_history):
            return result
        
        # Count how long effect persists after initial event
        duration = 0
        for i in range(initial_event_time, len(effect_history)):
            if effect_history[i]:
                duration += 1
            else:
                break
        
        result['duration'] = duration
        
        if duration == 0:
            result['decay_type'] = 'instant'
        elif duration >= len(effect_history) - initial_event_time:
            result['decay_type'] = 'permanent'
            result['persists'] = True
        else:
            result['decay_type'] = 'gradual'
            result['persists'] = duration > 1
        
        return result
    
    def _detect_sequence_pattern(
        self,
        action_history: List[str],
        outcome_history: List[Dict]
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect ordered sequences that lead to specific outcomes.
        """
        result = {
            'pattern_found': False,
            'sequence': [],
            'outcome': None,
            'confidence': 0.0
        }
        
        if not action_history or not outcome_history:
            return result
        
        # Look for action sequences that precede positive outcomes
        positive_outcomes = []
        for i, outcome in enumerate(outcome_history):
            if outcome.get('score_delta', 0) > 0 or outcome.get('success', False):
                positive_outcomes.append(i)
        
        if not positive_outcomes:
            return result
        
        # Check what actions preceded positive outcomes
        # Look for common sequences of 2-4 actions
        for seq_len in range(2, min(5, len(action_history))):
            sequences = {}
            
            for outcome_idx in positive_outcomes:
                if outcome_idx >= seq_len:
                    seq = tuple(action_history[outcome_idx - seq_len:outcome_idx])
                    sequences[seq] = sequences.get(seq, 0) + 1
            
            # Find most common sequence
            if sequences:
                best_seq = max(sequences.keys(), key=lambda s: sequences[s])
                count = sequences[best_seq]
                
                if count >= 2:  # At least 2 occurrences
                    result['pattern_found'] = True
                    result['sequence'] = list(best_seq)
                    result['confidence'] = count / len(positive_outcomes)
                    result['outcome'] = 'positive'
                    return result
        
        return result
    
    # ======================================================================
    # CONSTRAINT & CONTROL IMPLEMENTATIONS (BIRTHRIGHT)
    # ======================================================================
    
    def _detect_guiding(
        self,
        guided_object_history: List[Tuple[int, int]],
        potential_guide_positions: List[Tuple[int, int]]
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if object constrains another to a specific path.
        """
        result = {
            'guided': False,
            'guide_type': None,  # 'rail', 'channel', 'boundary'
            'constrained_axis': None
        }
        
        if not guided_object_history or not potential_guide_positions:
            return result
        
        guide_set = set(potential_guide_positions)
        
        # Check if guided object stays adjacent to guide
        adjacent_count = 0
        for pos in guided_object_history:
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                if (pos[0] + dx, pos[1] + dy) in guide_set:
                    adjacent_count += 1
                    break
        
        adjacency_ratio = adjacent_count / len(guided_object_history)
        
        if adjacency_ratio > 0.7:
            result['guided'] = True
            result['guide_type'] = 'rail'
            
            # Determine constrained axis
            x_values = [p[0] for p in guided_object_history]
            y_values = [p[1] for p in guided_object_history]
            
            x_range = max(x_values) - min(x_values)
            y_range = max(y_values) - min(y_values)
            
            if x_range > y_range * 2:
                result['constrained_axis'] = 'y'  # Moves mostly horizontally
            elif y_range > x_range * 2:
                result['constrained_axis'] = 'x'  # Moves mostly vertically
        
        return result
    
    def _detect_gating(
        self,
        gate_object_state: Dict,
        passage_before: bool,
        passage_after: bool
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if object controls whether passage/flow can occur.
        """
        result = {
            'gating': False,
            'gate_state': None,  # 'open', 'closed'
            'state_changed': False
        }
        
        if gate_object_state is None:
            return result
        
        # Check if passage changed
        result['state_changed'] = passage_before != passage_after
        
        if result['state_changed']:
            result['gating'] = True
            result['gate_state'] = 'open' if passage_after else 'closed'
        else:
            result['gate_state'] = 'open' if passage_after else 'closed'
        
        return result
    
    def _detect_actuating(
        self,
        actuator_state_change: Dict,
        actuated_object_before: Dict,
        actuated_object_after: Dict
    ) -> Dict[str, Any]:
        """
        BIRTHRIGHT: Detect if one object causes motion in another (trigger/switch).
        """
        result = {
            'actuating': False,
            'actuation_type': None,  # 'trigger', 'switch', 'lever'
            'effect': None
        }
        
        if not actuator_state_change or not actuated_object_before or not actuated_object_after:
            return result
        
        # Check if actuator changed
        actuator_changed = actuator_state_change.get('changed', False)
        
        # Check if actuated object changed
        pos_before = actuated_object_before.get('position') or actuated_object_before.get('centroid')
        pos_after = actuated_object_after.get('position') or actuated_object_after.get('centroid')
        
        actuated_moved = pos_before != pos_after if pos_before and pos_after else False
        
        state_before = actuated_object_before.get('state')
        state_after = actuated_object_after.get('state')
        
        actuated_state_changed = state_before != state_after if state_before is not None else False
        
        # If actuator changed and actuated object responded, it's actuation
        if actuator_changed and (actuated_moved or actuated_state_changed):
            result['actuating'] = True
            result['actuation_type'] = 'trigger'
            
            if actuated_moved:
                result['effect'] = 'movement'
            else:
                result['effect'] = 'state_change'
        
        return result
    
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
        'This is to that as X is to Y' reasoning with structural graph matching.
        
        Enhanced to support:
        1. Color transformations (numeric shift)
        2. Object property transformations (scale, position)
        3. Structural/relational transformations (graph isomorphism)
        4. Grid pattern transformations (rotate, flip, translate)
        
        Returns:
            {
                'inferred_target_b': Any,
                'transformation_type': str,
                'confidence': float,
                'mapping': Dict,
                'structural_match': bool
            }
        """
        result = {
            'inferred_target_b': None,
            'transformation_type': 'unknown',
            'confidence': 0.0,
            'mapping': {},
            'structural_match': False
        }
        
        # ==================================================================
        # CASE 1: Numeric/Color transformation
        # ==================================================================
        if isinstance(source_a, int) and isinstance(source_b, int):
            diff = source_b - source_a
            result['transformation_type'] = 'color_shift'
            result['mapping'] = {'shift': diff}
            result['inferred_target_b'] = target_a + diff if isinstance(target_a, int) else target_a
            result['confidence'] = 0.8
            return result
        
        # ==================================================================
        # CASE 2: Object/Dict transformation (property-based)
        # ==================================================================
        if isinstance(source_a, dict) and isinstance(source_b, dict):
            transformations = []
            
            # Size transformation
            if 'size' in source_a and 'size' in source_b:
                scale = source_b.get('size', 1) / max(source_a.get('size', 1), 1)
                if scale != 1.0:
                    transformations.append(('scale', {'factor': scale}))
            
            # Position transformation
            if 'position' in source_a and 'position' in source_b:
                pos_a, pos_b = source_a['position'], source_b['position']
                if isinstance(pos_a, (list, tuple)) and isinstance(pos_b, (list, tuple)):
                    dx = pos_b[0] - pos_a[0] if len(pos_b) > 0 and len(pos_a) > 0 else 0
                    dy = pos_b[1] - pos_a[1] if len(pos_b) > 1 and len(pos_a) > 1 else 0
                    if dx != 0 or dy != 0:
                        transformations.append(('translate', {'dx': dx, 'dy': dy}))
            
            # Color transformation
            if 'color' in source_a and 'color' in source_b:
                if source_a['color'] != source_b['color']:
                    transformations.append(('recolor', {'from': source_a['color'], 'to': source_b['color']}))
            
            # Apply transformations to target
            if transformations and isinstance(target_a, dict):
                result['transformation_type'] = 'multi_transform'
                result['mapping'] = {'transforms': transformations}
                result['inferred_target_b'] = self._apply_transforms(target_a, transformations)
                result['confidence'] = 0.7
                return result
        
        # ==================================================================
        # CASE 3: Grid/Pattern transformation (structural matching)
        # ==================================================================
        if isinstance(source_a, list) and isinstance(source_b, list):
            if source_a and isinstance(source_a[0], list):  # 2D grid
                structural_result = self._find_grid_transformation(source_a, source_b, target_a)
                if structural_result['found']:
                    result['transformation_type'] = structural_result['type']
                    result['mapping'] = structural_result['mapping']
                    result['inferred_target_b'] = structural_result['target_b']
                    result['confidence'] = structural_result['confidence']
                    result['structural_match'] = True
                    return result
        
        # ==================================================================
        # CASE 4: Relational/Graph structure matching
        # ==================================================================
        # Extract relational structure and find bijection
        if isinstance(source_a, (list, dict)) and isinstance(source_b, (list, dict)):
            graph_result = self._find_relational_mapping(source_a, source_b, target_a)
            if graph_result['found']:
                result['transformation_type'] = 'relational'
                result['mapping'] = graph_result['mapping']
                result['inferred_target_b'] = graph_result['target_b']
                result['confidence'] = graph_result['confidence']
                result['structural_match'] = True
                return result
        
        return result
    
    def _apply_transforms(self, obj: Dict, transforms: List[Tuple[str, Dict]]) -> Dict:
        """Apply a sequence of transformations to an object."""
        result = dict(obj)  # Shallow copy
        
        for transform_type, params in transforms:
            if transform_type == 'scale' and 'size' in result:
                result['size'] = int(result['size'] * params['factor'])
            elif transform_type == 'translate' and 'position' in result:
                pos = list(result['position'])
                if len(pos) >= 2:
                    pos[0] += params['dx']
                    pos[1] += params['dy']
                    result['position'] = tuple(pos)
            elif transform_type == 'recolor' and 'color' in result:
                if result['color'] == params['from']:
                    result['color'] = params['to']
        
        return result
    
    def _find_grid_transformation(self, source_a: List, source_b: List, target_a: Any) -> Dict:
        """Find transformation between two grids and apply to target."""
        result = {'found': False, 'type': 'unknown', 'mapping': {}, 'target_b': None, 'confidence': 0.0}
        
        if not source_a or not source_b:
            return result
        
        h_a, w_a = len(source_a), len(source_a[0]) if source_a else 0
        h_b, w_b = len(source_b), len(source_b[0]) if source_b else 0
        
        # Check for rotation (90, 180, 270 degrees)
        if h_a == w_b and w_a == h_b:  # Dimensions suggest rotation
            # Test 90-degree clockwise rotation
            rotated = [[source_a[h_a - 1 - j][i] for j in range(h_a)] for i in range(w_a)]
            if rotated == source_b:
                result['found'] = True
                result['type'] = 'rotate_90'
                result['mapping'] = {'angle': 90}
                result['confidence'] = 0.9
                if isinstance(target_a, list) and target_a and isinstance(target_a[0], list):
                    t_h, t_w = len(target_a), len(target_a[0]) if target_a else 0
                    result['target_b'] = [[target_a[t_h - 1 - j][i] for j in range(t_h)] for i in range(t_w)]
                return result
        
        # Check for horizontal flip
        if h_a == h_b and w_a == w_b:
            flipped_h = [row[::-1] for row in source_a]
            if flipped_h == source_b:
                result['found'] = True
                result['type'] = 'flip_horizontal'
                result['mapping'] = {'axis': 'horizontal'}
                result['confidence'] = 0.9
                if isinstance(target_a, list):
                    result['target_b'] = [row[::-1] if isinstance(row, list) else row for row in target_a]
                return result
            
            # Check for vertical flip
            flipped_v = source_a[::-1]
            if flipped_v == source_b:
                result['found'] = True
                result['type'] = 'flip_vertical'
                result['mapping'] = {'axis': 'vertical'}
                result['confidence'] = 0.9
                if isinstance(target_a, list):
                    result['target_b'] = target_a[::-1]
                return result
            
            # Check for color remapping
            color_map = {}
            match = True
            for y in range(h_a):
                for x in range(w_a):
                    c_a, c_b = source_a[y][x], source_b[y][x]
                    if c_a in color_map:
                        if color_map[c_a] != c_b:
                            match = False
                            break
                    else:
                        color_map[c_a] = c_b
                if not match:
                    break
            
            if match and color_map:
                result['found'] = True
                result['type'] = 'color_remap'
                result['mapping'] = {'color_map': color_map}
                result['confidence'] = 0.85
                if isinstance(target_a, list) and target_a and isinstance(target_a[0], list):
                    result['target_b'] = [
                        [color_map.get(c, c) for c in row]
                        for row in target_a
                    ]
                return result
        
        return result
    
    def _find_relational_mapping(self, source_a: Any, source_b: Any, target_a: Any) -> Dict:
        """Find relational/structural mapping between complex structures."""
        result = {'found': False, 'mapping': {}, 'target_b': None, 'confidence': 0.0}
        
        # Extract structural fingerprint (simplified graph isomorphism)
        def get_structure(obj, depth=0):
            """Extract structural fingerprint recursively."""
            if depth > 5:  # Prevent infinite recursion
                return ('leaf', type(obj).__name__)
            if isinstance(obj, dict):
                return ('dict', tuple(sorted((k, get_structure(v, depth+1)) for k, v in obj.items())))
            elif isinstance(obj, (list, tuple)):
                return ('seq', len(obj), tuple(get_structure(x, depth+1) for x in obj[:10]))  # Limit to 10
            elif isinstance(obj, (int, float)):
                return ('num', type(obj).__name__)
            else:
                return ('other', type(obj).__name__)
        
        struct_a = get_structure(source_a)
        struct_b = get_structure(source_b)
        
        # If structures match, we can find element-wise mapping
        if struct_a[0] == struct_b[0]:  # Same top-level type
            if struct_a[0] == 'dict' and len(struct_a[1]) == len(struct_b[1]):
                # Dict with same number of keys - try to find key mapping
                keys_a = sorted(source_a.keys())
                keys_b = sorted(source_b.keys())
                if len(keys_a) == len(keys_b):
                    key_map = dict(zip(keys_a, keys_b))
                    result['found'] = True
                    result['mapping'] = {'key_bijection': key_map}
                    result['confidence'] = 0.6
                    if isinstance(target_a, dict):
                        result['target_b'] = {key_map.get(k, k): v for k, v in target_a.items()}
            
            elif struct_a[0] == 'seq' and struct_a[1] == struct_b[1]:
                # Sequences of same length - element-wise mapping
                result['found'] = True
                result['mapping'] = {'element_wise': True, 'length': struct_a[1]}
                result['confidence'] = 0.5
        
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
    # TOPOLOGY & SHAPE PRIMITIVE IMPLEMENTATIONS
    # ======================================================================
    
    def _detect_hole(
        self,
        frame: List[List[int]],
        object_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect holes (through-holes vs pockets) in objects.
        
        A hole is a region of background completely surrounded by non-background.
        Through-holes go all the way through; pockets are partial indentations.
        """
        result = {
            'has_hole': False,
            'hole_count': 0,
            'holes': [],
            'hole_type': 'none'  # 'through', 'pocket', 'none'
        }
        
        if not frame or not frame[0]:
            return result
        
        height = len(frame)
        width = len(frame[0])
        
        # Find background pixels not connected to border
        visited = [[False] * width for _ in range(height)]
        
        # Flood fill from border to mark "outside" background
        def flood_fill_border():
            queue = []
            for x in range(width):
                if frame[0][x] == 0 and not visited[0][x]:
                    queue.append((x, 0))
                    visited[0][x] = True
                if frame[height-1][x] == 0 and not visited[height-1][x]:
                    queue.append((x, height-1))
                    visited[height-1][x] = True
            for y in range(height):
                if frame[y][0] == 0 and not visited[y][0]:
                    queue.append((0, y))
                    visited[y][0] = True
                if frame[y][width-1] == 0 and not visited[y][width-1]:
                    queue.append((width-1, y))
                    visited[y][width-1] = True
            
            while queue:
                x, y = queue.pop(0)
                for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        if frame[ny][nx] == 0 and not visited[ny][nx]:
                            visited[ny][nx] = True
                            queue.append((nx, ny))
        
        flood_fill_border()
        
        # Find remaining unvisited background = holes
        holes = []
        for y in range(height):
            for x in range(width):
                if frame[y][x] == 0 and not visited[y][x]:
                    # Found a hole - flood fill to get its extent
                    hole_pixels = []
                    queue = [(x, y)]
                    visited[y][x] = True
                    while queue:
                        hx, hy = queue.pop(0)
                        hole_pixels.append((hx, hy))
                        for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                            nx, ny = hx + dx, hy + dy
                            if 0 <= nx < width and 0 <= ny < height:
                                if frame[ny][nx] == 0 and not visited[ny][nx]:
                                    visited[ny][nx] = True
                                    queue.append((nx, ny))
                    if hole_pixels:
                        holes.append(hole_pixels)
        
        if holes:
            result['has_hole'] = True
            result['hole_count'] = len(holes)
            result['holes'] = [{'size': len(h), 'centroid': (sum(p[0] for p in h)/len(h), sum(p[1] for p in h)/len(h))} for h in holes[:5]]
            result['hole_type'] = 'through'  # In 2D, all internal holes are "through"
        
        return result
    
    def _detect_cavity(
        self,
        frame: List[List[int]],
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> Dict[str, Any]:
        """
        Detect enclosed empty spaces within or between objects.
        """
        result = {
            'has_cavity': False,
            'cavity_count': 0,
            'cavities': [],
            'total_cavity_area': 0
        }
        
        # Use hole detection as base
        hole_result = self._detect_hole(frame, None)
        
        if hole_result['has_hole']:
            result['has_cavity'] = True
            result['cavity_count'] = hole_result['hole_count']
            result['cavities'] = hole_result['holes']
            result['total_cavity_area'] = sum(c['size'] for c in hole_result['holes'])
        
        return result
    
    def _detect_protrusion(
        self,
        frame: List[List[int]],
        object_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect parts that stick out from main body of object.
        
        A protrusion is a narrow extension from the main mass.
        """
        result = {
            'has_protrusion': False,
            'protrusion_count': 0,
            'protrusions': []
        }
        
        if not frame or not frame[0]:
            return result
        
        # Get target color
        target_color = None
        if object_id:
            try:
                target_color = int(object_id.replace('obj_', ''))
            except:
                pass
        
        if target_color is None:
            # Find most common non-background color
            colors = {}
            for row in frame:
                for c in row:
                    if c != 0:
                        colors[c] = colors.get(c, 0) + 1
            if colors:
                target_color = max(colors, key=colors.get)
        
        if target_color is None:
            return result
        
        height = len(frame)
        width = len(frame[0])
        
        # Find object pixels
        obj_pixels = set()
        for y in range(height):
            for x in range(width):
                if frame[y][x] == target_color:
                    obj_pixels.add((x, y))
        
        if not obj_pixels:
            return result
        
        # Calculate centroid
        cx = sum(p[0] for p in obj_pixels) / len(obj_pixels)
        cy = sum(p[1] for p in obj_pixels) / len(obj_pixels)
        
        # Find pixels far from centroid with few neighbors = protrusions
        for px, py in obj_pixels:
            dist_from_center = ((px - cx)**2 + (py - cy)**2)**0.5
            
            # Count neighbors
            neighbor_count = 0
            for dx, dy in [(0,1), (0,-1), (1,0), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]:
                if (px + dx, py + dy) in obj_pixels:
                    neighbor_count += 1
            
            # Protrusion: far from center, few neighbors
            if dist_from_center > 3 and neighbor_count <= 3:
                result['protrusions'].append({
                    'position': (px, py),
                    'distance_from_center': dist_from_center,
                    'neighbor_count': neighbor_count
                })
        
        result['has_protrusion'] = len(result['protrusions']) > 0
        result['protrusion_count'] = len(result['protrusions'])
        
        return result
    
    def _count_connected_components(
        self,
        frame: List[List[int]],
        color: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Count separate connected regions of same color.
        """
        result = {
            'component_count': 0,
            'components': [],
            'largest_component_size': 0
        }
        
        if not frame or not frame[0]:
            return result
        
        height = len(frame)
        width = len(frame[0])
        visited = [[False] * width for _ in range(height)]
        
        def flood_fill(start_x, start_y, target_color):
            pixels = []
            queue = [(start_x, start_y)]
            visited[start_y][start_x] = True
            while queue:
                x, y = queue.pop(0)
                pixels.append((x, y))
                for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        if frame[ny][nx] == target_color and not visited[ny][nx]:
                            visited[ny][nx] = True
                            queue.append((nx, ny))
            return pixels
        
        components = []
        for y in range(height):
            for x in range(width):
                if not visited[y][x]:
                    c = frame[y][x]
                    if color is None or c == color:
                        if c != 0:  # Skip background
                            pixels = flood_fill(x, y, c)
                            components.append({
                                'color': c,
                                'size': len(pixels),
                                'centroid': (sum(p[0] for p in pixels)/len(pixels), sum(p[1] for p in pixels)/len(pixels))
                            })
                    else:
                        visited[y][x] = True
        
        result['component_count'] = len(components)
        result['components'] = components[:20]  # Limit
        if components:
            result['largest_component_size'] = max(c['size'] for c in components)
        
        return result
    
    def _detect_boundary_closure(
        self,
        frame: List[List[int]],
        object_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect if object boundary is closed (forms complete loop).
        """
        result = {
            'is_closed': False,
            'closure_ratio': 0.0,
            'boundary_length': 0
        }
        
        if not frame or not frame[0]:
            return result
        
        # Get target color
        target_color = None
        if object_id:
            try:
                target_color = int(object_id.replace('obj_', ''))
            except:
                pass
        
        if target_color is None:
            return result
        
        height = len(frame)
        width = len(frame[0])
        
        # Find boundary pixels (adjacent to non-object)
        boundary = []
        for y in range(height):
            for x in range(width):
                if frame[y][x] == target_color:
                    # Check if any neighbor is different
                    is_boundary = False
                    for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                        nx, ny = x + dx, y + dy
                        if nx < 0 or nx >= width or ny < 0 or ny >= height:
                            is_boundary = True
                        elif frame[ny][nx] != target_color:
                            is_boundary = True
                    if is_boundary:
                        boundary.append((x, y))
        
        result['boundary_length'] = len(boundary)
        
        if len(boundary) < 3:
            return result
        
        # Check if boundary forms a closed loop
        # Simple heuristic: if interior is fully surrounded
        hole_result = self._detect_hole(frame, object_id)
        
        # If object has holes and boundary is contiguous, it's closed
        result['is_closed'] = len(boundary) >= 4
        result['closure_ratio'] = 1.0 if result['is_closed'] else 0.0
        
        return result
    
    def _detect_euler_characteristic(
        self,
        frame: List[List[int]],
        object_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compute topological invariant V - E + F (vertices - edges + faces).
        For 2D shapes, this relates to holes.
        """
        result = {
            'euler_characteristic': 1,  # Default for simple connected shape
            'vertices': 0,
            'edges': 0,
            'faces': 1
        }
        
        # Count connected components and holes
        cc_result = self._count_connected_components(frame, None)
        hole_result = self._detect_hole(frame, object_id)
        
        # Euler characteristic = components - holes
        num_components = cc_result['component_count']
        num_holes = hole_result['hole_count']
        
        result['euler_characteristic'] = num_components - num_holes
        result['faces'] = num_components
        result['holes'] = num_holes
        
        return result
    
    def _detect_genus(
        self,
        frame: List[List[int]],
        object_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect number of topological holes (genus) in object.
        Genus 0 = sphere-like, genus 1 = torus-like (one hole), etc.
        """
        result = {
            'genus': 0,
            'hole_count': 0,
            'topology_class': 'simple'
        }
        
        hole_result = self._detect_hole(frame, object_id)
        
        result['genus'] = hole_result['hole_count']
        result['hole_count'] = hole_result['hole_count']
        
        if result['genus'] == 0:
            result['topology_class'] = 'simple'
        elif result['genus'] == 1:
            result['topology_class'] = 'torus'
        else:
            result['topology_class'] = f'genus_{result["genus"]}'
        
        return result
    
    # ======================================================================
    # ALIGNMENT & ORIENTATION PRIMITIVE IMPLEMENTATIONS
    # ======================================================================
    
    def _detect_parallel(
        self,
        frame: List[List[int]],
        object_a: Optional[str] = None,
        object_b: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect if two lines/edges/objects are parallel.
        """
        result = {
            'is_parallel': False,
            'angle_difference': 0.0,
            'confidence': 0.0
        }
        
        if not frame or not frame[0]:
            return result
        
        # Get object positions
        objects = self._find_distinct_objects(frame)
        if len(objects) < 2:
            return result
        
        # Get directions of objects (using bounding box diagonal)
        def get_direction(obj):
            positions = obj.get('positions', [])
            if len(positions) < 2:
                return None
            xs = [p[0] for p in positions]
            ys = [p[1] for p in positions]
            dx = max(xs) - min(xs)
            dy = max(ys) - min(ys)
            if dx == 0 and dy == 0:
                return None
            import math
            return math.atan2(dy, dx)
        
        dir_a = get_direction(objects[0])
        dir_b = get_direction(objects[1])
        
        if dir_a is not None and dir_b is not None:
            import math
            diff = abs(dir_a - dir_b)
            # Parallel if difference is 0 or 180 degrees
            diff_normalized = min(diff, math.pi - diff) if diff <= math.pi else min(diff - math.pi, 2*math.pi - diff)
            
            result['angle_difference'] = math.degrees(diff_normalized)
            result['is_parallel'] = diff_normalized < 0.1  # ~5.7 degrees tolerance
            result['confidence'] = 1.0 - diff_normalized / (math.pi / 2)
        
        return result
    
    def _detect_perpendicular(
        self,
        frame: List[List[int]],
        object_a: Optional[str] = None,
        object_b: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect if two lines/edges meet at right angles.
        """
        result = {
            'is_perpendicular': False,
            'angle': 0.0,
            'confidence': 0.0
        }
        
        parallel_result = self._detect_parallel(frame, object_a, object_b)
        
        if parallel_result['confidence'] > 0:
            import math
            # Perpendicular if angle difference is ~90 degrees
            angle_diff = abs(90 - parallel_result['angle_difference'])
            result['angle'] = parallel_result['angle_difference']
            result['is_perpendicular'] = angle_diff < 10  # 10 degree tolerance
            result['confidence'] = 1.0 - angle_diff / 90.0
        
        return result
    
    def _detect_colinear(
        self,
        positions: List[Tuple[int, int]]
    ) -> Dict[str, Any]:
        """
        Detect if points lie on same line.
        """
        result = {
            'is_colinear': False,
            'deviation': 0.0,
            'line_equation': None
        }
        
        if len(positions) < 2:
            result['is_colinear'] = True
            return result
        
        if len(positions) == 2:
            result['is_colinear'] = True
            return result
        
        # Use first two points to define a line
        x1, y1 = positions[0]
        x2, y2 = positions[1]
        
        # Check all other points against this line
        max_deviation = 0
        for x, y in positions[2:]:
            # Distance from point to line
            if x2 - x1 == 0 and y2 - y1 == 0:
                continue
            
            # Line: (y2-y1)x - (x2-x1)y + (x2-x1)y1 - (y2-y1)x1 = 0
            a = y2 - y1
            b = -(x2 - x1)
            c = (x2 - x1) * y1 - (y2 - y1) * x1
            
            dist = abs(a*x + b*y + c) / (a*a + b*b)**0.5 if (a*a + b*b) > 0 else 0
            max_deviation = max(max_deviation, dist)
        
        result['deviation'] = max_deviation
        result['is_colinear'] = max_deviation < 0.5  # Less than 0.5 pixel deviation
        
        return result
    
    def _detect_coplanar(
        self,
        positions: List[Tuple[int, int]]
    ) -> Dict[str, Any]:
        """
        Detect if objects lie in same plane.
        In 2D, this checks for alignment patterns.
        """
        result = {
            'is_coplanar': True,  # Always true in 2D
            'alignment_type': 'none',
            'alignment_score': 0.0
        }
        
        if len(positions) < 3:
            return result
        
        # Check for row/column alignment
        xs = [p[0] for p in positions]
        ys = [p[1] for p in positions]
        
        x_spread = max(xs) - min(xs)
        y_spread = max(ys) - min(ys)
        
        if x_spread == 0:
            result['alignment_type'] = 'vertical'
            result['alignment_score'] = 1.0
        elif y_spread == 0:
            result['alignment_type'] = 'horizontal'
            result['alignment_score'] = 1.0
        elif abs(x_spread - y_spread) < 2:
            result['alignment_type'] = 'diagonal'
            result['alignment_score'] = 0.8
        
        return result
    
    def _measure_angle_between(
        self,
        line_a: Tuple[Tuple[int, int], Tuple[int, int]],
        line_b: Tuple[Tuple[int, int], Tuple[int, int]]
    ) -> Dict[str, Any]:
        """
        Measure angle between two lines.
        """
        result = {
            'angle_degrees': 0.0,
            'angle_radians': 0.0,
            'is_acute': False,
            'is_right': False,
            'is_obtuse': False
        }
        
        import math
        
        # Get direction vectors
        dx1 = line_a[1][0] - line_a[0][0]
        dy1 = line_a[1][1] - line_a[0][1]
        dx2 = line_b[1][0] - line_b[0][0]
        dy2 = line_b[1][1] - line_b[0][1]
        
        # Calculate angle
        len1 = (dx1*dx1 + dy1*dy1)**0.5
        len2 = (dx2*dx2 + dy2*dy2)**0.5
        
        if len1 == 0 or len2 == 0:
            return result
        
        dot = dx1*dx2 + dy1*dy2
        cos_angle = dot / (len1 * len2)
        cos_angle = max(-1, min(1, cos_angle))  # Clamp for numerical stability
        
        angle_rad = math.acos(cos_angle)
        angle_deg = math.degrees(angle_rad)
        
        result['angle_radians'] = angle_rad
        result['angle_degrees'] = angle_deg
        result['is_acute'] = angle_deg < 90
        result['is_right'] = 85 < angle_deg < 95
        result['is_obtuse'] = angle_deg > 90
        
        return result
    
    def _detect_facing_direction(
        self,
        frame: List[List[int]],
        object_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect which direction an asymmetric object is facing.
        """
        result = {
            'direction': 'none',
            'angle': 0.0,
            'confidence': 0.0,
            'is_symmetric': True
        }
        
        if not frame or not frame[0]:
            return result
        
        # Get target color
        target_color = None
        if object_id:
            try:
                target_color = int(object_id.replace('obj_', ''))
            except:
                pass
        
        if target_color is None:
            objects = self._find_distinct_objects(frame)
            if objects:
                target_color = objects[0]['color']
        
        if target_color is None:
            return result
        
        height = len(frame)
        width = len(frame[0])
        
        # Get object positions
        positions = []
        for y in range(height):
            for x in range(width):
                if frame[y][x] == target_color:
                    positions.append((x, y))
        
        if len(positions) < 3:
            return result
        
        # Calculate centroid
        cx = sum(p[0] for p in positions) / len(positions)
        cy = sum(p[1] for p in positions) / len(positions)
        
        # Find point furthest from centroid (likely the "front")
        max_dist = 0
        front_point = (cx, cy)
        for px, py in positions:
            dist = (px - cx)**2 + (py - cy)**2
            if dist > max_dist:
                max_dist = dist
                front_point = (px, py)
        
        # Calculate direction
        import math
        dx = front_point[0] - cx
        dy = front_point[1] - cy
        
        if dx == 0 and dy == 0:
            return result
        
        angle = math.degrees(math.atan2(-dy, dx))  # -dy because y increases downward
        
        # Classify direction
        if -22.5 <= angle < 22.5:
            result['direction'] = 'right'
        elif 22.5 <= angle < 67.5:
            result['direction'] = 'up_right'
        elif 67.5 <= angle < 112.5:
            result['direction'] = 'up'
        elif 112.5 <= angle < 157.5:
            result['direction'] = 'up_left'
        elif angle >= 157.5 or angle < -157.5:
            result['direction'] = 'left'
        elif -157.5 <= angle < -112.5:
            result['direction'] = 'down_left'
        elif -112.5 <= angle < -67.5:
            result['direction'] = 'down'
        else:
            result['direction'] = 'down_right'
        
        result['angle'] = angle
        result['confidence'] = min(1.0, max_dist**0.5 / 5)
        result['is_symmetric'] = False
        
        return result
    
    def _detect_alignment(
        self,
        positions: List[Tuple[int, int]]
    ) -> Dict[str, Any]:
        """
        Detect if objects are aligned (horizontal, vertical, diagonal).
        """
        result = {
            'alignment_type': 'none',
            'is_aligned': False,
            'alignment_score': 0.0
        }
        
        if len(positions) < 2:
            return result
        
        xs = [p[0] for p in positions]
        ys = [p[1] for p in positions]
        
        x_var = max(xs) - min(xs)
        y_var = max(ys) - min(ys)
        
        if x_var == 0:
            result['alignment_type'] = 'vertical'
            result['is_aligned'] = True
            result['alignment_score'] = 1.0
        elif y_var == 0:
            result['alignment_type'] = 'horizontal'
            result['is_aligned'] = True
            result['alignment_score'] = 1.0
        elif x_var > 0 and y_var > 0:
            # Check for diagonal alignment
            colinear = self._detect_colinear(positions)
            if colinear['is_colinear']:
                result['alignment_type'] = 'diagonal'
                result['is_aligned'] = True
                result['alignment_score'] = 1.0 - colinear['deviation']
        
        return result
    
    # ======================================================================
    # SYMMETRY & PATTERN PRIMITIVE IMPLEMENTATIONS
    # ======================================================================
    
    def _detect_reflection_symmetry(
        self,
        frame: List[List[int]],
        object_id: Optional[str] = None,
        axis: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect mirror symmetry (horizontal, vertical, diagonal).
        """
        result = {
            'has_symmetry': False,
            'horizontal': False,
            'vertical': False,
            'diagonal_main': False,
            'diagonal_anti': False,
            'symmetry_score': 0.0
        }
        
        if not frame or not frame[0]:
            return result
        
        height = len(frame)
        width = len(frame[0])
        
        # Check horizontal (left-right) symmetry
        h_match = 0
        h_total = 0
        for y in range(height):
            for x in range(width // 2):
                mirror_x = width - 1 - x
                h_total += 1
                if frame[y][x] == frame[y][mirror_x]:
                    h_match += 1
        result['horizontal'] = h_total > 0 and h_match / h_total > 0.9
        
        # Check vertical (top-bottom) symmetry
        v_match = 0
        v_total = 0
        for y in range(height // 2):
            mirror_y = height - 1 - y
            for x in range(width):
                v_total += 1
                if frame[y][x] == frame[mirror_y][x]:
                    v_match += 1
        result['vertical'] = v_total > 0 and v_match / v_total > 0.9
        
        # Check main diagonal (top-left to bottom-right)
        if height == width:
            d_match = 0
            d_total = 0
            for y in range(height):
                for x in range(width):
                    if x != y:
                        d_total += 1
                        if frame[y][x] == frame[x][y]:
                            d_match += 1
            result['diagonal_main'] = d_total > 0 and d_match / d_total > 0.9
            
            # Check anti-diagonal
            ad_match = 0
            ad_total = 0
            for y in range(height):
                for x in range(width):
                    mirror_x = height - 1 - y
                    mirror_y = width - 1 - x
                    if x != mirror_x or y != mirror_y:
                        ad_total += 1
                        if frame[y][x] == frame[mirror_y][mirror_x]:
                            ad_match += 1
            result['diagonal_anti'] = ad_total > 0 and ad_match / ad_total > 0.9
        
        result['has_symmetry'] = any([result['horizontal'], result['vertical'], 
                                       result['diagonal_main'], result['diagonal_anti']])
        result['symmetry_score'] = sum([result['horizontal'], result['vertical'],
                                        result['diagonal_main'], result['diagonal_anti']]) / 4.0
        
        return result
    
    def _detect_rotational_symmetry(
        self,
        frame: List[List[int]],
        object_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect rotational symmetry (90, 180, 270 degrees).
        """
        result = {
            'has_symmetry': False,
            'rot_90': False,
            'rot_180': False,
            'rot_270': False,
            'order': 1
        }
        
        if not frame or not frame[0]:
            return result
        
        height = len(frame)
        width = len(frame[0])
        
        # For rotational symmetry, frame should be square
        if height != width:
            # Check 180 only
            match_180 = 0
            total = 0
            for y in range(height):
                for x in range(width):
                    ry = height - 1 - y
                    rx = width - 1 - x
                    total += 1
                    if frame[y][x] == frame[ry][rx]:
                        match_180 += 1
            result['rot_180'] = total > 0 and match_180 / total > 0.9
            result['has_symmetry'] = result['rot_180']
            result['order'] = 2 if result['rot_180'] else 1
            return result
        
        # Check 90 degree rotation
        match_90 = 0
        total = 0
        for y in range(height):
            for x in range(width):
                # 90 degree rotation: (x,y) -> (y, width-1-x)
                ry = x
                rx = width - 1 - y
                total += 1
                if frame[y][x] == frame[ry][rx]:
                    match_90 += 1
        result['rot_90'] = total > 0 and match_90 / total > 0.9
        
        # Check 180 degree rotation
        match_180 = 0
        for y in range(height):
            for x in range(width):
                ry = height - 1 - y
                rx = width - 1 - x
                if frame[y][x] == frame[ry][rx]:
                    match_180 += 1
        result['rot_180'] = match_180 / total > 0.9 if total > 0 else False
        
        # 270 is same as checking 90 the other way
        result['rot_270'] = result['rot_90']  # If 90 works, 270 works
        
        result['has_symmetry'] = result['rot_90'] or result['rot_180']
        
        if result['rot_90'] and result['rot_180']:
            result['order'] = 4
        elif result['rot_180']:
            result['order'] = 2
        else:
            result['order'] = 1
        
        return result
    
    def _detect_translational_symmetry(
        self,
        frame: List[List[int]]
    ) -> Dict[str, Any]:
        """
        Detect repeating patterns via translation.
        """
        result = {
            'has_symmetry': False,
            'period_x': 0,
            'period_y': 0,
            'tile_pattern': False
        }
        
        if not frame or not frame[0]:
            return result
        
        height = len(frame)
        width = len(frame[0])
        
        # Check for horizontal periodicity
        for period in range(1, width // 2 + 1):
            if width % period == 0:
                match = 0
                total = 0
                for y in range(height):
                    for x in range(width - period):
                        total += 1
                        if frame[y][x] == frame[y][x + period]:
                            match += 1
                if total > 0 and match / total > 0.95:
                    result['period_x'] = period
                    break
        
        # Check for vertical periodicity
        for period in range(1, height // 2 + 1):
            if height % period == 0:
                match = 0
                total = 0
                for y in range(height - period):
                    for x in range(width):
                        total += 1
                        if frame[y][x] == frame[y + period][x]:
                            match += 1
                if total > 0 and match / total > 0.95:
                    result['period_y'] = period
                    break
        
        result['has_symmetry'] = result['period_x'] > 0 or result['period_y'] > 0
        result['tile_pattern'] = result['period_x'] > 0 and result['period_y'] > 0
        
        return result
    
    def _detect_self_similarity(
        self,
        frame: List[List[int]],
        object_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect if pattern contains scaled copies of itself (fractal-like).
        """
        result = {
            'has_self_similarity': False,
            'scales_found': [],
            'similarity_score': 0.0
        }
        
        if not frame or not frame[0]:
            return result
        
        height = len(frame)
        width = len(frame[0])
        
        # Check if half-size pattern matches
        if height >= 4 and width >= 4 and height % 2 == 0 and width % 2 == 0:
            half_h = height // 2
            half_w = width // 2
            
            # Downsample frame
            downsampled = []
            for y in range(half_h):
                row = []
                for x in range(half_w):
                    # Take majority color from 2x2 block
                    colors = [
                        frame[y*2][x*2],
                        frame[y*2+1][x*2] if y*2+1 < height else 0,
                        frame[y*2][x*2+1] if x*2+1 < width else 0,
                        frame[y*2+1][x*2+1] if y*2+1 < height and x*2+1 < width else 0
                    ]
                    row.append(max(set(colors), key=colors.count))
                downsampled.append(row)
            
            # Check if downsampled matches any quadrant
            quadrants = [
                (0, 0, half_w, half_h),
                (half_w, 0, width, half_h),
                (0, half_h, half_w, height),
                (half_w, half_h, width, height)
            ]
            
            for i, (x1, y1, x2, y2) in enumerate(quadrants):
                match = 0
                total = 0
                for dy in range(min(half_h, y2-y1)):
                    for dx in range(min(half_w, x2-x1)):
                        if dy < len(downsampled) and dx < len(downsampled[0]):
                            total += 1
                            if y1+dy < height and x1+dx < width:
                                if downsampled[dy][dx] == frame[y1+dy][x1+dx]:
                                    match += 1
                if total > 0 and match / total > 0.8:
                    result['has_self_similarity'] = True
                    result['scales_found'].append(0.5)
                    result['similarity_score'] = match / total
                    break
        
        return result
    
    def _detect_periodicity_spatial(
        self,
        frame: List[List[int]]
    ) -> Dict[str, Any]:
        """
        Detect spatial periodicity (repeating patterns in space).
        """
        # Reuse translational symmetry detection
        trans_result = self._detect_translational_symmetry(frame)
        
        result = {
            'has_periodicity': trans_result['has_symmetry'],
            'period_x': trans_result['period_x'],
            'period_y': trans_result['period_y'],
            'is_tiled': trans_result['tile_pattern'],
            'frequency_x': 1.0 / trans_result['period_x'] if trans_result['period_x'] > 0 else 0,
            'frequency_y': 1.0 / trans_result['period_y'] if trans_result['period_y'] > 0 else 0
        }
        
        return result
    
    # ======================================================================
    # BOUNDARY OPERATIONS PRIMITIVE IMPLEMENTATIONS
    # ======================================================================
    
    def _detect_inside_outside(
        self,
        frame: List[List[int]],
        position: Tuple[int, int],
        boundary_object: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Determine if point is inside or outside a boundary.
        Uses flood fill from point - if it reaches frame edge, it's outside.
        """
        result = {
            'is_inside': False,
            'is_outside': True,
            'confidence': 0.0
        }
        
        if not frame or not frame[0]:
            return result
        
        x, y = position
        height = len(frame)
        width = len(frame[0])
        
        if x < 0 or x >= width or y < 0 or y >= height:
            return result  # Out of bounds = outside
        
        # If point is on non-background, it's "inside" an object
        if frame[y][x] != 0:
            result['is_inside'] = True
            result['is_outside'] = False
            result['confidence'] = 1.0
            return result
        
        # Flood fill from point - if we hit edge, we're outside
        visited = set()
        queue = [(x, y)]
        visited.add((x, y))
        hit_edge = False
        
        while queue and not hit_edge:
            cx, cy = queue.pop(0)
            
            # Check if at edge
            if cx == 0 or cx == width - 1 or cy == 0 or cy == height - 1:
                hit_edge = True
                break
            
            for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < width and 0 <= ny < height:
                    if (nx, ny) not in visited and frame[ny][nx] == 0:
                        visited.add((nx, ny))
                        queue.append((nx, ny))
        
        result['is_outside'] = hit_edge
        result['is_inside'] = not hit_edge
        result['confidence'] = 1.0
        
        return result
    
    def _compute_distance_to_boundary(
        self,
        frame: List[List[int]],
        position: Tuple[int, int],
        boundary_object: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compute shortest distance from point to boundary.
        """
        result = {
            'distance': float('inf'),
            'nearest_boundary_point': None,
            'boundary_color': None
        }
        
        if not frame or not frame[0]:
            return result
        
        x, y = position
        height = len(frame)
        width = len(frame[0])
        
        # Find nearest non-background pixel
        min_dist = float('inf')
        nearest = None
        nearest_color = None
        
        for by in range(height):
            for bx in range(width):
                if frame[by][bx] != 0:
                    dist = ((bx - x)**2 + (by - y)**2)**0.5
                    if dist < min_dist:
                        min_dist = dist
                        nearest = (bx, by)
                        nearest_color = frame[by][bx]
        
        result['distance'] = min_dist
        result['nearest_boundary_point'] = nearest
        result['boundary_color'] = nearest_color
        
        return result
    
    def _detect_boundary_crossing(
        self,
        position_before: Tuple[int, int],
        position_after: Tuple[int, int],
        boundary_object: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect when object crosses a boundary.
        """
        result = {
            'crossed_boundary': False,
            'crossing_type': 'none',  # 'enter', 'exit', 'none'
            'crossing_point': None
        }
        
        # This needs frame context - simplified version
        x1, y1 = position_before
        x2, y2 = position_after
        
        # Check if positions are significantly different
        dist = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
        
        if dist > 1:
            result['crossing_point'] = ((x1 + x2) / 2, (y1 + y2) / 2)
            # Without frame context, we can't determine if boundary was crossed
        
        return result
    
    def _detect_enclosure(
        self,
        frame: List[List[int]],
        outer_object: Optional[str] = None,
        inner_object: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect if one object completely encloses another.
        """
        result = {
            'is_enclosed': False,
            'enclosure_ratio': 0.0,
            'gap_count': 0
        }
        
        if not frame or not frame[0]:
            return result
        
        # Get objects
        objects = self._find_distinct_objects(frame)
        if len(objects) < 2:
            return result
        
        # Get bounding boxes
        outer_obj = objects[0]
        inner_obj = objects[1] if len(objects) > 1 else None
        
        if inner_obj is None:
            return result
        
        outer_pos = set(outer_obj.get('positions', []))
        inner_pos = inner_obj.get('positions', [])
        
        if not inner_pos or not outer_pos:
            return result
        
        # Check if all inner positions are "inside" the outer boundary
        # Using simple bounding box containment first
        outer_xs = [p[0] for p in outer_pos]
        outer_ys = [p[1] for p in outer_pos]
        inner_xs = [p[0] for p in inner_pos]
        inner_ys = [p[1] for p in inner_pos]
        
        bbox_enclosed = (
            min(inner_xs) > min(outer_xs) and
            max(inner_xs) < max(outer_xs) and
            min(inner_ys) > min(outer_ys) and
            max(inner_ys) < max(outer_ys)
        )
        
        result['is_enclosed'] = bbox_enclosed
        result['enclosure_ratio'] = 1.0 if bbox_enclosed else 0.0
        
        return result
    
    def _measure_convexity(
        self,
        frame: List[List[int]],
        object_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Measure how convex vs concave an object's boundary is.
        """
        result = {
            'convexity': 1.0,
            'is_convex': True,
            'concave_regions': 0
        }
        
        if not frame or not frame[0]:
            return result
        
        # Get target color
        target_color = None
        if object_id:
            try:
                target_color = int(object_id.replace('obj_', ''))
            except:
                pass
        
        if target_color is None:
            objects = self._find_distinct_objects(frame)
            if objects:
                target_color = objects[0]['color']
        
        if target_color is None:
            return result
        
        height = len(frame)
        width = len(frame[0])
        
        # Get object positions
        positions = set()
        for y in range(height):
            for x in range(width):
                if frame[y][x] == target_color:
                    positions.add((x, y))
        
        if len(positions) < 4:
            return result
        
        # Calculate convex hull area vs actual area
        xs = [p[0] for p in positions]
        ys = [p[1] for p in positions]
        
        # Simple bounding box as proxy for convex hull
        bbox_area = (max(xs) - min(xs) + 1) * (max(ys) - min(ys) + 1)
        actual_area = len(positions)
        
        result['convexity'] = actual_area / bbox_area if bbox_area > 0 else 1.0
        result['is_convex'] = result['convexity'] > 0.8
        result['concave_regions'] = 0 if result['is_convex'] else 1
        
        return result
    
    # ======================================================================
    # HIERARCHY & COMPOSITION PRIMITIVE IMPLEMENTATIONS
    # ======================================================================
    
    def _get_parent_object(
        self,
        frame: List[List[int]],
        object_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get the containing/parent object of a given object.
        """
        result = {
            'has_parent': False,
            'parent_id': None,
            'parent_color': None
        }
        
        if not frame or not frame[0] or not object_id:
            return result
        
        # Get target color
        try:
            target_color = int(object_id.replace('obj_', ''))
        except:
            return result
        
        height = len(frame)
        width = len(frame[0])
        
        # Get object positions
        positions = []
        for y in range(height):
            for x in range(width):
                if frame[y][x] == target_color:
                    positions.append((x, y))
        
        if not positions:
            return result
        
        # Check enclosure by other objects
        for obj in self._find_distinct_objects(frame):
            if obj['color'] == target_color:
                continue
            
            enclosure = self._detect_enclosure(frame, f"obj_{obj['color']}", object_id)
            if enclosure['is_enclosed']:
                result['has_parent'] = True
                result['parent_id'] = f"obj_{obj['color']}"
                result['parent_color'] = obj['color']
                break
        
        return result
    
    def _get_child_objects(
        self,
        frame: List[List[int]],
        parent_object: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get objects contained within a parent object.
        """
        result = {
            'has_children': False,
            'children': [],
            'child_count': 0
        }
        
        if not frame or not frame[0]:
            return result
        
        # Find all objects and check which are enclosed
        all_objects = self._find_distinct_objects(frame)
        
        if parent_object:
            # Find children of specific parent
            for obj in all_objects:
                child_id = f"obj_{obj['color']}"
                if child_id != parent_object:
                    enclosure = self._detect_enclosure(frame, parent_object, child_id)
                    if enclosure['is_enclosed']:
                        result['children'].append({
                            'object_id': child_id,
                            'color': obj['color'],
                            'size': obj.get('size', 0)
                        })
        else:
            # Find all parent-child relationships
            for potential_parent in all_objects:
                for potential_child in all_objects:
                    if potential_parent['color'] != potential_child['color']:
                        parent_id = f"obj_{potential_parent['color']}"
                        child_id = f"obj_{potential_child['color']}"
                        enclosure = self._detect_enclosure(frame, parent_id, child_id)
                        if enclosure['is_enclosed']:
                            result['children'].append({
                                'parent_id': parent_id,
                                'child_id': child_id
                            })
        
        result['has_children'] = len(result['children']) > 0
        result['child_count'] = len(result['children'])
        
        return result
    
    def _detect_composite_object(
        self,
        frame: List[List[int]],
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> Dict[str, Any]:
        """
        Detect if multiple colors/parts form a single composite object.
        """
        result = {
            'is_composite': False,
            'component_count': 0,
            'components': [],
            'composite_bbox': None
        }
        
        if not frame or not frame[0]:
            return result
        
        # Get objects in region (or whole frame)
        objects = self._find_distinct_objects(frame)
        
        if len(objects) < 2:
            return result
        
        # Check if objects are adjacent (touching)
        height = len(frame)
        width = len(frame[0])
        
        # Build adjacency graph
        adjacent_pairs = []
        for i, obj1 in enumerate(objects):
            for j, obj2 in enumerate(objects):
                if i >= j:
                    continue
                
                # Check if objects are adjacent
                pos1 = set(obj1.get('positions', []))
                pos2 = set(obj2.get('positions', []))
                
                for x, y in pos1:
                    for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                        if (x+dx, y+dy) in pos2:
                            adjacent_pairs.append((obj1['color'], obj2['color']))
                            break
                    else:
                        continue
                    break
        
        # If objects are adjacent, they might be composite
        if adjacent_pairs:
            result['is_composite'] = True
            result['component_count'] = len(objects)
            result['components'] = [{'color': o['color'], 'size': o.get('size', 0)} for o in objects]
            
            # Calculate combined bounding box
            all_positions = []
            for obj in objects:
                all_positions.extend(obj.get('positions', []))
            if all_positions:
                xs = [p[0] for p in all_positions]
                ys = [p[1] for p in all_positions]
                result['composite_bbox'] = (min(xs), min(ys), max(xs), max(ys))
        
        return result
    
    def _decompose_object(
        self,
        frame: List[List[int]],
        object_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Break composite object into constituent parts.
        """
        result = {
            'parts': [],
            'part_count': 0,
            'is_decomposable': False
        }
        
        # Get connected components for the target color
        if object_id:
            try:
                color = int(object_id.replace('obj_', ''))
                cc_result = self._count_connected_components(frame, color)
                if cc_result['component_count'] > 1:
                    result['is_decomposable'] = True
                    result['parts'] = cc_result['components']
                    result['part_count'] = cc_result['component_count']
            except:
                pass
        
        return result
    
    def _find_root_object(
        self,
        frame: List[List[int]],
        object_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Find topmost object in containment hierarchy.
        """
        result = {
            'root_id': object_id,
            'root_color': None,
            'hierarchy_depth': 0
        }
        
        if not object_id:
            return result
        
        current = object_id
        depth = 0
        max_depth = 10  # Prevent infinite loop
        
        while depth < max_depth:
            parent_result = self._get_parent_object(frame, current)
            if parent_result['has_parent']:
                current = parent_result['parent_id']
                depth += 1
            else:
                break
        
        result['root_id'] = current
        result['hierarchy_depth'] = depth
        
        try:
            result['root_color'] = int(current.replace('obj_', ''))
        except:
            pass
        
        return result
    
    # ======================================================================
    # PERSISTENCE & MEMORY PRIMITIVE IMPLEMENTATIONS
    # ======================================================================
    
    def _object_first_appearance(
        self,
        object_id: str
    ) -> Dict[str, Any]:
        """
        Get frame index when object first appeared.
        """
        result = {
            'first_frame': -1,
            'found': False
        }
        
        # Check object history
        history = self._object_history.get(object_id, {})
        if 'first_seen' in history:
            result['first_frame'] = history['first_seen']
            result['found'] = True
        elif object_id in self._object_history:
            # Use current frame as first seen
            result['first_frame'] = self._step_index
            result['found'] = True
        
        return result
    
    def _object_last_seen(
        self,
        object_id: str
    ) -> Dict[str, Any]:
        """
        Get frame index when object was last seen.
        """
        result = {
            'last_frame': -1,
            'found': False
        }
        
        history = self._object_history.get(object_id, {})
        if 'last_seen' in history:
            result['last_frame'] = history['last_seen']
            result['found'] = True
        
        return result
    
    def _detect_object_creation(
        self,
        frame_before: List[List[int]],
        frame_after: List[List[int]]
    ) -> Dict[str, Any]:
        """
        Detect when a new object appears.
        """
        result = {
            'objects_created': [],
            'creation_count': 0
        }
        
        before_objects = self._find_distinct_objects(frame_before)
        after_objects = self._find_distinct_objects(frame_after)
        
        before_colors = {o['color'] for o in before_objects}
        after_colors = {o['color'] for o in after_objects}
        
        new_colors = after_colors - before_colors
        
        for color in new_colors:
            for obj in after_objects:
                if obj['color'] == color:
                    result['objects_created'].append({
                        'object_id': f"obj_{color}",
                        'color': color,
                        'size': obj.get('size', 0),
                        'position': obj.get('centroid')
                    })
        
        result['creation_count'] = len(result['objects_created'])
        
        return result
    
    def _detect_object_destruction(
        self,
        frame_before: List[List[int]],
        frame_after: List[List[int]]
    ) -> Dict[str, Any]:
        """
        Detect when an object disappears.
        """
        result = {
            'objects_destroyed': [],
            'destruction_count': 0
        }
        
        before_objects = self._find_distinct_objects(frame_before)
        after_objects = self._find_distinct_objects(frame_after)
        
        before_colors = {o['color'] for o in before_objects}
        after_colors = {o['color'] for o in after_objects}
        
        destroyed_colors = before_colors - after_colors
        
        for color in destroyed_colors:
            for obj in before_objects:
                if obj['color'] == color:
                    result['objects_destroyed'].append({
                        'object_id': f"obj_{color}",
                        'color': color,
                        'last_size': obj.get('size', 0),
                        'last_position': obj.get('centroid')
                    })
        
        result['destruction_count'] = len(result['objects_destroyed'])
        
        return result
    
    def _track_object_identity(
        self,
        frame_before: List[List[int]],
        frame_after: List[List[int]],
        object_id: str
    ) -> Dict[str, Any]:
        """
        Maintain object identity across frames despite movement.
        """
        result = {
            'identity_maintained': False,
            'position_before': None,
            'position_after': None,
            'movement': None
        }
        
        try:
            color = int(object_id.replace('obj_', ''))
        except:
            return result
        
        # Find object in both frames
        before_objs = self._find_distinct_objects(frame_before)
        after_objs = self._find_distinct_objects(frame_after)
        
        before_obj = next((o for o in before_objs if o['color'] == color), None)
        after_obj = next((o for o in after_objs if o['color'] == color), None)
        
        if before_obj:
            result['position_before'] = before_obj.get('centroid')
        
        if after_obj:
            result['position_after'] = after_obj.get('centroid')
            result['identity_maintained'] = True
            
            if result['position_before'] and result['position_after']:
                bx, by = result['position_before']
                ax, ay = result['position_after']
                result['movement'] = (ax - bx, ay - by)
        
        # Update history
        if object_id not in self._object_history:
            self._object_history[object_id] = {'first_seen': self._step_index}
        self._object_history[object_id]['last_seen'] = self._step_index
        
        return result
    
    # ======================================================================
    # RELATIONAL QUERIES PRIMITIVE IMPLEMENTATIONS
    # ======================================================================
    
    def _get_all_relations(
        self,
        frame: List[List[int]],
        object_id: str
    ) -> Dict[str, Any]:
        """
        Get all known relationships for an object.
        """
        result = {
            'relations': [],
            'relation_count': 0
        }
        
        if not frame:
            return result
        
        all_objects = self._find_distinct_objects(frame)
        target_color = None
        
        try:
            target_color = int(object_id.replace('obj_', ''))
        except:
            return result
        
        target_obj = next((o for o in all_objects if o['color'] == target_color), None)
        if not target_obj:
            return result
        
        for obj in all_objects:
            if obj['color'] == target_color:
                continue
            
            other_id = f"obj_{obj['color']}"
            
            # Check spatial relationship
            target_centroid = target_obj.get('centroid', (0, 0))
            other_centroid = obj.get('centroid', (0, 0))
            
            dx = other_centroid[0] - target_centroid[0]
            dy = other_centroid[1] - target_centroid[1]
            
            direction = 'nearby'
            if abs(dx) > abs(dy):
                direction = 'right' if dx > 0 else 'left'
            elif abs(dy) > abs(dx):
                direction = 'below' if dy > 0 else 'above'
            
            result['relations'].append({
                'other_object': other_id,
                'relation_type': 'spatial',
                'direction': direction,
                'distance': (dx*dx + dy*dy)**0.5
            })
        
        result['relation_count'] = len(result['relations'])
        
        return result
    
    def _get_relation_strength(
        self,
        relation_type: str,
        object_a: str,
        object_b: str
    ) -> Dict[str, Any]:
        """
        Get confidence/strength of a specific relationship.
        """
        result = {
            'strength': 0.0,
            'confidence': 0.0,
            'evidence_count': 0
        }
        
        # Query relation history
        key = f"{object_a}_{relation_type}_{object_b}"
        history = self._relation_history.get(key, [])
        
        if history:
            result['evidence_count'] = len(history)
            result['strength'] = sum(h.get('strength', 0.5) for h in history) / len(history)
            result['confidence'] = min(1.0, len(history) / 5.0)  # More evidence = higher confidence
        
        return result
    
    def _detect_relation_change(
        self,
        frame_before: List[List[int]],
        frame_after: List[List[int]],
        object_a: str,
        object_b: str
    ) -> Dict[str, Any]:
        """
        Detect when relationship between objects changes.
        """
        result = {
            'relation_changed': False,
            'change_type': 'none',
            'before_relation': None,
            'after_relation': None
        }
        
        # Get relations before
        before_relations = self._get_all_relations(frame_before, object_a)
        after_relations = self._get_all_relations(frame_after, object_a)
        
        # Find relation to object_b before and after
        before_rel = next((r for r in before_relations['relations'] if r['other_object'] == object_b), None)
        after_rel = next((r for r in after_relations['relations'] if r['other_object'] == object_b), None)
        
        result['before_relation'] = before_rel
        result['after_relation'] = after_rel
        
        if before_rel and after_rel:
            if before_rel['direction'] != after_rel['direction']:
                result['relation_changed'] = True
                result['change_type'] = 'direction_changed'
            elif abs(before_rel.get('distance', 0) - after_rel.get('distance', 0)) > 2:
                result['relation_changed'] = True
                result['change_type'] = 'distance_changed'
        elif before_rel and not after_rel:
            result['relation_changed'] = True
            result['change_type'] = 'relation_lost'
        elif not before_rel and after_rel:
            result['relation_changed'] = True
            result['change_type'] = 'relation_gained'
        
        return result
    
    def _relation_history(
        self,
        object_a: str,
        object_b: str
    ) -> Dict[str, Any]:
        """
        Get history of relationships between two objects.
        """
        result = {
            'history': [],
            'history_length': 0,
            'most_common_relation': None
        }
        
        # Query all relation types between these objects
        relation_counts = {}
        
        for key, history in self._relation_history.items():
            if object_a in key and object_b in key:
                for entry in history:
                    rel_type = entry.get('relation_type', 'unknown')
                    relation_counts[rel_type] = relation_counts.get(rel_type, 0) + 1
                    result['history'].append(entry)
        
        result['history_length'] = len(result['history'])
        if relation_counts:
            result['most_common_relation'] = max(relation_counts, key=relation_counts.get)
        
        return result
    
    # ======================================================================
    # SCALE & AGGREGATION PRIMITIVE IMPLEMENTATIONS
    # ======================================================================
    
    def _detect_aggregation(
        self,
        frame_before: List[List[int]],
        frame_after: List[List[int]]
    ) -> Dict[str, Any]:
        """
        Detect many objects combining into one (many -> one).
        """
        result = {
            'aggregation_detected': False,
            'objects_before': 0,
            'objects_after': 0,
            'aggregated_into': None
        }
        
        before_cc = self._count_connected_components(frame_before, None)
        after_cc = self._count_connected_components(frame_after, None)
        
        result['objects_before'] = before_cc['component_count']
        result['objects_after'] = after_cc['component_count']
        
        if result['objects_before'] > result['objects_after'] and result['objects_after'] > 0:
            result['aggregation_detected'] = True
            # Find the largest component in after frame
            if after_cc['components']:
                largest = max(after_cc['components'], key=lambda c: c['size'])
                result['aggregated_into'] = f"obj_{largest['color']}"
        
        return result
    
    def _detect_subdivision(
        self,
        frame_before: List[List[int]],
        frame_after: List[List[int]]
    ) -> Dict[str, Any]:
        """
        Detect one object splitting into many (one -> many).
        """
        result = {
            'subdivision_detected': False,
            'objects_before': 0,
            'objects_after': 0,
            'subdivided_from': None
        }
        
        before_cc = self._count_connected_components(frame_before, None)
        after_cc = self._count_connected_components(frame_after, None)
        
        result['objects_before'] = before_cc['component_count']
        result['objects_after'] = after_cc['component_count']
        
        if result['objects_after'] > result['objects_before'] and result['objects_before'] > 0:
            result['subdivision_detected'] = True
            # Find the largest component that was in before frame
            if before_cc['components']:
                largest = max(before_cc['components'], key=lambda c: c['size'])
                result['subdivided_from'] = f"obj_{largest['color']}"
        
        return result
    
    def _measure_granularity(
        self,
        frame: List[List[int]],
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> Dict[str, Any]:
        """
        Measure level of detail/granularity in a region.
        """
        result = {
            'granularity': 0.0,
            'unique_colors': 0,
            'component_density': 0.0
        }
        
        if not frame or not frame[0]:
            return result
        
        height = len(frame)
        width = len(frame[0])
        
        # Count color changes
        color_changes = 0
        total_pairs = 0
        colors = set()
        
        for y in range(height):
            for x in range(width):
                colors.add(frame[y][x])
                if x > 0:
                    total_pairs += 1
                    if frame[y][x] != frame[y][x-1]:
                        color_changes += 1
                if y > 0:
                    total_pairs += 1
                    if frame[y][x] != frame[y-1][x]:
                        color_changes += 1
        
        result['unique_colors'] = len(colors)
        result['granularity'] = color_changes / total_pairs if total_pairs > 0 else 0
        
        cc_result = self._count_connected_components(frame, None)
        result['component_density'] = cc_result['component_count'] / (height * width) if height * width > 0 else 0
        
        return result
    
    def _scale_invariance_check(
        self,
        frame: List[List[int]],
        pattern: Optional[List[List[int]]] = None
    ) -> Dict[str, Any]:
        """
        Check if pattern is scale invariant (same at different sizes).
        """
        result = {
            'is_scale_invariant': False,
            'scales_checked': [],
            'matching_scales': []
        }
        
        # Use self-similarity detection
        self_sim = self._detect_self_similarity(frame, None)
        
        result['is_scale_invariant'] = self_sim['has_self_similarity']
        result['scales_checked'] = [0.5, 1.0, 2.0]
        result['matching_scales'] = self_sim['scales_found']
        
        return result
    
    # ======================================================================
    # INFORMATION & SENSING PRIMITIVE IMPLEMENTATIONS
    # ======================================================================
    
    def _detect_occluding(
        self,
        frame: List[List[int]],
        front_object: Optional[str] = None,
        back_object: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect if one object blocks view of another.
        In 2D, this means overlapping positions where one color takes precedence.
        """
        result = {
            'is_occluding': False,
            'occlusion_area': 0,
            'occlusion_ratio': 0.0
        }
        
        # In 2D grid world, we can't have true occlusion
        # But we can check if objects overlap bounding boxes
        if not frame or not frame[0]:
            return result
        
        objects = self._find_distinct_objects(frame)
        if len(objects) < 2:
            return result
        
        obj1 = objects[0]
        obj2 = objects[1]
        
        # Check bounding box overlap
        pos1 = obj1.get('positions', [])
        pos2 = obj2.get('positions', [])
        
        if not pos1 or not pos2:
            return result
        
        xs1 = [p[0] for p in pos1]
        ys1 = [p[1] for p in pos1]
        xs2 = [p[0] for p in pos2]
        ys2 = [p[1] for p in pos2]
        
        # Check if bounding boxes overlap
        overlap_x = not (max(xs1) < min(xs2) or max(xs2) < min(xs1))
        overlap_y = not (max(ys1) < min(ys2) or max(ys2) < min(ys1))
        
        result['is_occluding'] = overlap_x and overlap_y
        
        return result
    
    def _compute_visibility(
        self,
        frame: List[List[int]],
        viewpoint: Tuple[int, int]
    ) -> Dict[str, Any]:
        """
        Compute what is visible from a given viewpoint.
        In 2D, all non-background is "visible" if not blocked.
        """
        result = {
            'visible_objects': [],
            'visibility_ratio': 1.0,  # In 2D, everything visible by default
            'hidden_objects': []
        }
        
        if not frame:
            return result
        
        objects = self._find_distinct_objects(frame)
        
        # In 2D grid, all objects are visible
        result['visible_objects'] = [f"obj_{o['color']}" for o in objects]
        
        return result
    
    def _detect_casting(
        self,
        frame: List[List[int]],
        object_id: Optional[str] = None,
        light_direction: Optional[Tuple[int, int]] = None
    ) -> Dict[str, Any]:
        """
        Detect shadow or projection cast by an object.
        In 2D, this is a simplified concept - looking for darker regions adjacent to objects.
        """
        result = {
            'has_shadow': False,
            'shadow_direction': None,
            'shadow_length': 0
        }
        
        if not frame or not frame[0]:
            return result
        
        # Look for dark (color 0 or low value) regions adjacent to objects
        # This is a simplified shadow detection
        objects = self._find_distinct_objects(frame)
        
        if not objects:
            return result
        
        height = len(frame)
        width = len(frame[0])
        
        # Default light direction: from top-left
        if light_direction is None:
            light_direction = (1, 1)  # Shadow extends down-right
        
        # Check for consistent dark regions in shadow direction
        for obj in objects:
            positions = obj.get('positions', [])
            shadow_pixels = 0
            
            for x, y in positions:
                sx = x + light_direction[0]
                sy = y + light_direction[1]
                if 0 <= sx < width and 0 <= sy < height:
                    if frame[sy][sx] == 0:  # Background = potential shadow
                        shadow_pixels += 1
            
            if shadow_pixels > len(positions) * 0.5:
                result['has_shadow'] = True
                result['shadow_direction'] = light_direction
                result['shadow_length'] = shadow_pixels
                break
        
        return result
    
    # ======================================================================
    # FLOW & MATERIAL TRANSFER IMPLEMENTATIONS
    # ======================================================================
    
    def _detect_flowing_through(self, frame_before: List[List[int]], frame_after: List[List[int]], 
                                 channel_positions: List[tuple]) -> Dict[str, Any]:
        """Detect if color is flowing through a channel/path."""
        result = {
            'primitive': 'detect_flowing_through',
            'flow_detected': False,
            'flow_direction': None,
            'flow_color': None,
            'flow_speed': 0
        }
        
        if not frame_before or not frame_after or not channel_positions:
            return result
        
        # Track color changes along channel
        changes_along_channel = []
        for i, (x, y) in enumerate(channel_positions):
            if 0 <= y < len(frame_before) and 0 <= x < len(frame_before[0]):
                before_color = frame_before[y][x]
                after_color = frame_after[y][x] if y < len(frame_after) and x < len(frame_after[0]) else before_color
                if before_color != after_color:
                    changes_along_channel.append((i, before_color, after_color))
        
        # Flow = sequential color changes along channel
        if len(changes_along_channel) >= 2:
            result['flow_detected'] = True
            # Determine direction from indices
            indices = [c[0] for c in changes_along_channel]
            if indices == sorted(indices):
                result['flow_direction'] = 'forward'
            elif indices == sorted(indices, reverse=True):
                result['flow_direction'] = 'backward'
            else:
                result['flow_direction'] = 'mixed'
            result['flow_color'] = changes_along_channel[0][2]
            result['flow_speed'] = len(changes_along_channel)
        
        return result
    
    def _detect_filling(self, frame_before: List[List[int]], frame_after: List[List[int]], 
                        container_region: List[tuple]) -> Dict[str, Any]:
        """Detect if a container region is being filled with color."""
        result = {
            'primitive': 'detect_filling',
            'filling_detected': False,
            'fill_color': None,
            'fill_amount': 0,
            'fill_percentage': 0.0
        }
        
        if not frame_before or not frame_after or not container_region:
            return result
        
        # Count filled cells before and after
        filled_before = 0
        filled_after = 0
        fill_color = None
        
        for x, y in container_region:
            if 0 <= y < len(frame_before) and 0 <= x < len(frame_before[0]):
                if frame_before[y][x] != 0:
                    filled_before += 1
                if y < len(frame_after) and x < len(frame_after[0]):
                    if frame_after[y][x] != 0:
                        filled_after += 1
                        if fill_color is None:
                            fill_color = frame_after[y][x]
        
        if filled_after > filled_before:
            result['filling_detected'] = True
            result['fill_color'] = fill_color
            result['fill_amount'] = filled_after - filled_before
            result['fill_percentage'] = filled_after / max(1, len(container_region))
        
        return result
    
    def _detect_draining(self, frame_before: List[List[int]], frame_after: List[List[int]], 
                         region: List[tuple]) -> Dict[str, Any]:
        """Detect if color is draining from a region."""
        result = {
            'primitive': 'detect_draining',
            'draining_detected': False,
            'drain_color': None,
            'drain_amount': 0
        }
        
        if not frame_before or not frame_after or not region:
            return result
        
        filled_before = 0
        filled_after = 0
        drain_color = None
        
        for x, y in region:
            if 0 <= y < len(frame_before) and 0 <= x < len(frame_before[0]):
                if frame_before[y][x] != 0:
                    filled_before += 1
                    if drain_color is None:
                        drain_color = frame_before[y][x]
                if y < len(frame_after) and x < len(frame_after[0]):
                    if frame_after[y][x] != 0:
                        filled_after += 1
        
        if filled_after < filled_before:
            result['draining_detected'] = True
            result['drain_color'] = drain_color
            result['drain_amount'] = filled_before - filled_after
        
        return result
    
    def _detect_transfer(self, frame_before: List[List[int]], frame_after: List[List[int]]) -> Dict[str, Any]:
        """Detect transfer of color/pattern from one region to another."""
        result = {
            'primitive': 'detect_transfer',
            'transfer_detected': False,
            'from_region': None,
            'to_region': None,
            'transfer_color': None
        }
        
        if not frame_before or not frame_after:
            return result
        
        height = min(len(frame_before), len(frame_after))
        width = min(len(frame_before[0]) if frame_before else 0, len(frame_after[0]) if frame_after else 0)
        
        # Track where colors disappeared and appeared
        disappeared = []
        appeared = []
        
        for y in range(height):
            for x in range(width):
                before_color = frame_before[y][x]
                after_color = frame_after[y][x]
                if before_color != 0 and after_color == 0:
                    disappeared.append((x, y, before_color))
                elif before_color == 0 and after_color != 0:
                    appeared.append((x, y, after_color))
        
        # Check if same color disappeared and appeared
        for dx, dy, d_color in disappeared:
            for ax, ay, a_color in appeared:
                if d_color == a_color:
                    result['transfer_detected'] = True
                    result['from_region'] = (dx, dy)
                    result['to_region'] = (ax, ay)
                    result['transfer_color'] = d_color
                    return result
        
        return result
    
    def _detect_propagation(self, frame_before: List[List[int]], frame_after: List[List[int]]) -> Dict[str, Any]:
        """Detect spreading/propagation of color outward from source."""
        result = {
            'primitive': 'detect_propagation',
            'propagation_detected': False,
            'propagating_color': None,
            'source_position': None,
            'spread_amount': 0
        }
        
        if not frame_before or not frame_after:
            return result
        
        height = min(len(frame_before), len(frame_after))
        width = min(len(frame_before[0]) if frame_before else 0, len(frame_after[0]) if frame_after else 0)
        
        # Find new colored cells
        new_colored = []
        for y in range(height):
            for x in range(width):
                if frame_before[y][x] == 0 and frame_after[y][x] != 0:
                    new_colored.append((x, y, frame_after[y][x]))
        
        if not new_colored:
            return result
        
        # Check if new cells are adjacent to existing same-colored cells
        for nx, ny, color in new_colored:
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                adj_x, adj_y = nx + dx, ny + dy
                if 0 <= adj_y < height and 0 <= adj_x < width:
                    if frame_before[adj_y][adj_x] == color:
                        result['propagation_detected'] = True
                        result['propagating_color'] = color
                        result['source_position'] = (adj_x, adj_y)
                        result['spread_amount'] = len(new_colored)
                        return result
        
        return result
    
    def _measure_fill_level(self, frame: List[List[int]], container_region: List[tuple], 
                            fill_color: int) -> Dict[str, Any]:
        """Measure how full a container region is."""
        result = {
            'primitive': 'measure_fill_level',
            'fill_level': 0.0,
            'filled_cells': 0,
            'total_cells': len(container_region) if container_region else 0
        }
        
        if not frame or not container_region:
            return result
        
        filled = 0
        for x, y in container_region:
            if 0 <= y < len(frame) and 0 <= x < len(frame[0]):
                if frame[y][x] == fill_color:
                    filled += 1
        
        result['filled_cells'] = filled
        result['fill_level'] = filled / max(1, len(container_region))
        
        return result
    
    def _detect_source_sink(self, frame_before: List[List[int]], frame_after: List[List[int]]) -> Dict[str, Any]:
        """Detect source (emitting) and sink (absorbing) locations."""
        result = {
            'primitive': 'detect_source_sink',
            'sources': [],
            'sinks': [],
            'has_source': False,
            'has_sink': False
        }
        
        if not frame_before or not frame_after:
            return result
        
        height = min(len(frame_before), len(frame_after))
        width = min(len(frame_before[0]) if frame_before else 0, len(frame_after[0]) if frame_after else 0)
        
        # Sources: positions where color exists before AND more color appears adjacent
        # Sinks: positions where color exists before AND adjacent color disappears
        
        for y in range(height):
            for x in range(width):
                before_color = frame_before[y][x]
                after_color = frame_after[y][x]
                
                if before_color != 0 and after_color == before_color:
                    # Check if this cell is emitting (adjacent cells gained same color)
                    adjacent_gained = 0
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        ax, ay = x + dx, y + dy
                        if 0 <= ay < height and 0 <= ax < width:
                            if frame_before[ay][ax] == 0 and frame_after[ay][ax] == before_color:
                                adjacent_gained += 1
                    if adjacent_gained > 0:
                        result['sources'].append((x, y, before_color, adjacent_gained))
                        result['has_source'] = True
                    
                    # Check if this cell is absorbing (adjacent cells lost color)
                    adjacent_lost = 0
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        ax, ay = x + dx, y + dy
                        if 0 <= ay < height and 0 <= ax < width:
                            if frame_before[ay][ax] != 0 and frame_after[ay][ax] == 0:
                                adjacent_lost += 1
                    if adjacent_lost > 0:
                        result['sinks'].append((x, y, before_color, adjacent_lost))
                        result['has_sink'] = True
        
        return result
    
    # ======================================================================
    # TRANSFORMATION & STATE IMPLEMENTATIONS
    # ======================================================================
    
    def _detect_state_change(self, frame_before: List[List[int]], frame_after: List[List[int]], 
                             object_id: Any) -> Dict[str, Any]:
        """Detect when object changes to different state (color change)."""
        result = {
            'primitive': 'detect_state_change',
            'state_changed': False,
            'from_state': None,
            'to_state': None,
            'change_locations': []
        }
        
        if not frame_before or not frame_after:
            return result
        
        height = min(len(frame_before), len(frame_after))
        width = min(len(frame_before[0]) if frame_before else 0, len(frame_after[0]) if frame_after else 0)
        
        # Track color changes at same positions
        for y in range(height):
            for x in range(width):
                before_color = frame_before[y][x]
                after_color = frame_after[y][x]
                if before_color != 0 and after_color != 0 and before_color != after_color:
                    result['state_changed'] = True
                    result['from_state'] = before_color
                    result['to_state'] = after_color
                    result['change_locations'].append((x, y))
        
        return result
    
    def _detect_growth(self, frame_before: List[List[int]], frame_after: List[List[int]], 
                       object_id: Any) -> Dict[str, Any]:
        """Detect object/pattern growing larger over frames."""
        result = {
            'primitive': 'detect_growth',
            'growth_detected': False,
            'growth_amount': 0,
            'growth_direction': None,
            'size_before': 0,
            'size_after': 0
        }
        
        if not frame_before or not frame_after:
            return result
        
        # Count non-background cells
        count_before = sum(1 for row in frame_before for c in row if c != 0)
        count_after = sum(1 for row in frame_after for c in row if c != 0)
        
        result['size_before'] = count_before
        result['size_after'] = count_after
        
        if count_after > count_before:
            result['growth_detected'] = True
            result['growth_amount'] = count_after - count_before
            
            # Determine growth direction
            height_b = len(frame_before)
            width_b = len(frame_before[0]) if frame_before else 0
            height_a = len(frame_after)
            width_a = len(frame_after[0]) if frame_after else 0
            
            if width_a > width_b:
                result['growth_direction'] = 'horizontal'
            elif height_a > height_b:
                result['growth_direction'] = 'vertical'
            else:
                result['growth_direction'] = 'internal'
        
        return result
    
    def _detect_decay(self, frame_before: List[List[int]], frame_after: List[List[int]], 
                      object_id: Any) -> Dict[str, Any]:
        """Detect object/pattern shrinking or decaying."""
        result = {
            'primitive': 'detect_decay',
            'decay_detected': False,
            'decay_amount': 0,
            'decay_pattern': None
        }
        
        if not frame_before or not frame_after:
            return result
        
        count_before = sum(1 for row in frame_before for c in row if c != 0)
        count_after = sum(1 for row in frame_after for c in row if c != 0)
        
        if count_after < count_before:
            result['decay_detected'] = True
            result['decay_amount'] = count_before - count_after
            
            # Check if decay is from edges or internal
            height = min(len(frame_before), len(frame_after))
            width = min(len(frame_before[0]) if frame_before else 0, len(frame_after[0]) if frame_after else 0)
            
            edge_decay = 0
            internal_decay = 0
            for y in range(height):
                for x in range(width):
                    if frame_before[y][x] != 0 and frame_after[y][x] == 0:
                        if x == 0 or x == width - 1 or y == 0 or y == height - 1:
                            edge_decay += 1
                        else:
                            internal_decay += 1
            
            result['decay_pattern'] = 'edge' if edge_decay > internal_decay else 'internal'
        
        return result
    
    def _detect_crystallization(self, frame_before: List[List[int]], frame_after: List[List[int]]) -> Dict[str, Any]:
        """Detect ordered pattern emerging from disorder."""
        result = {
            'primitive': 'detect_crystallization',
            'crystallization_detected': False,
            'order_increase': 0.0,
            'symmetry_gained': False
        }
        
        if not frame_before or not frame_after:
            return result
        
        # Measure "order" as regularity of color distribution
        def measure_regularity(frame):
            """Higher regularity = more structured pattern."""
            if not frame:
                return 0
            
            # Count color frequencies
            color_counts = {}
            for row in frame:
                for c in row:
                    color_counts[c] = color_counts.get(c, 0) + 1
            
            # Check for alignment (same colors in rows/columns)
            row_uniformity = 0
            for row in frame:
                if len(set(row)) <= 2:  # 2 or fewer colors in row = ordered
                    row_uniformity += 1
            
            return row_uniformity / max(1, len(frame))
        
        reg_before = measure_regularity(frame_before)
        reg_after = measure_regularity(frame_after)
        
        if reg_after > reg_before:
            result['crystallization_detected'] = True
            result['order_increase'] = reg_after - reg_before
        
        return result
    
    def _detect_dissolution(self, frame_before: List[List[int]], frame_after: List[List[int]]) -> Dict[str, Any]:
        """Detect ordered pattern dissolving into disorder."""
        result = {
            'primitive': 'detect_dissolution',
            'dissolution_detected': False,
            'disorder_increase': 0.0
        }
        
        if not frame_before or not frame_after:
            return result
        
        def measure_disorder(frame):
            """Higher = more disordered."""
            if not frame:
                return 0
            total_transitions = 0
            for y in range(len(frame)):
                for x in range(len(frame[0]) - 1):
                    if frame[y][x] != frame[y][x + 1]:
                        total_transitions += 1
            return total_transitions
        
        disorder_before = measure_disorder(frame_before)
        disorder_after = measure_disorder(frame_after)
        
        if disorder_after > disorder_before:
            result['dissolution_detected'] = True
            result['disorder_increase'] = disorder_after - disorder_before
        
        return result
    
    def _detect_color_transformation(self, frame_before: List[List[int]], frame_after: List[List[int]]) -> Dict[str, Any]:
        """Detect systematic color changes (like phase transitions)."""
        result = {
            'primitive': 'detect_color_transformation',
            'transformation_detected': False,
            'color_map': {},
            'is_systematic': False
        }
        
        if not frame_before or not frame_after:
            return result
        
        height = min(len(frame_before), len(frame_after))
        width = min(len(frame_before[0]) if frame_before else 0, len(frame_after[0]) if frame_after else 0)
        
        # Build color transformation map
        color_map = {}
        for y in range(height):
            for x in range(width):
                before_color = frame_before[y][x]
                after_color = frame_after[y][x]
                if before_color != after_color:
                    key = before_color
                    if key not in color_map:
                        color_map[key] = {}
                    color_map[key][after_color] = color_map[key].get(after_color, 0) + 1
        
        if color_map:
            result['transformation_detected'] = True
            result['color_map'] = color_map
            
            # Check if transformation is systematic (one-to-one mapping)
            is_systematic = True
            for from_color, to_colors in color_map.items():
                if len(to_colors) > 1:
                    is_systematic = False
                    break
            result['is_systematic'] = is_systematic
        
        return result
    
    def _detect_restoration(self, frame_history: List[List[List[int]]]) -> Dict[str, Any]:
        """Detect object returning to previous state (elastic return)."""
        result = {
            'primitive': 'detect_restoration',
            'restoration_detected': False,
            'restored_to_frame': None,
            'restoration_completeness': 0.0
        }
        
        if not frame_history or len(frame_history) < 3:
            return result
        
        current_frame = frame_history[-1]
        
        # Check if current frame matches any previous frame
        for i, past_frame in enumerate(frame_history[:-1]):
            if past_frame == current_frame:
                result['restoration_detected'] = True
                result['restored_to_frame'] = i
                result['restoration_completeness'] = 1.0
                return result
        
        # Check partial restoration
        for i, past_frame in enumerate(frame_history[:-1]):
            if not past_frame or not current_frame:
                continue
            
            height = min(len(past_frame), len(current_frame))
            width = min(len(past_frame[0]) if past_frame else 0, len(current_frame[0]) if current_frame else 0)
            
            matching = 0
            total = 0
            for y in range(height):
                for x in range(width):
                    total += 1
                    if past_frame[y][x] == current_frame[y][x]:
                        matching += 1
            
            similarity = matching / max(1, total)
            if similarity > 0.9 and similarity > result['restoration_completeness']:
                result['restoration_detected'] = True
                result['restored_to_frame'] = i
                result['restoration_completeness'] = similarity
        
        return result
    
    # ======================================================================
    # CONSTRAINT & MODULATION IMPLEMENTATIONS
    # ======================================================================
    
    def _detect_binding(self, frame_before: List[List[int]], frame_after: List[List[int]], 
                        object_a: Any, object_b: Any) -> Dict[str, Any]:
        """Detect if two objects are bound (move together)."""
        result = {
            'primitive': 'detect_binding',
            'binding_detected': False,
            'binding_type': None,
            'binding_strength': 0.0
        }
        
        # Would need object tracking to implement fully
        # Simplified: check if non-background cells maintain relative positions
        
        return result
    
    def _detect_tethering(self, movement_history: List[dict], object_id: Any) -> Dict[str, Any]:
        """Detect if object is tethered (limited range of motion)."""
        result = {
            'primitive': 'detect_tethering',
            'tethering_detected': False,
            'tether_point': None,
            'max_distance': 0
        }
        
        if not movement_history:
            return result
        
        # Extract positions from history
        positions = []
        for entry in movement_history:
            if isinstance(entry, dict) and 'position' in entry:
                positions.append(entry['position'])
        
        if len(positions) < 3:
            return result
        
        # Find if there's a point all positions are within limited distance of
        first_pos = positions[0]
        max_dist = 0
        for pos in positions:
            dist = abs(pos[0] - first_pos[0]) + abs(pos[1] - first_pos[1])
            max_dist = max(max_dist, dist)
        
        # If max distance is limited, might be tethered
        if max_dist < 5 and len(positions) > 5:
            result['tethering_detected'] = True
            result['tether_point'] = first_pos
            result['max_distance'] = max_dist
        
        return result
    
    def _detect_modulating(self, frame_history: List[List[List[int]]], controller_id: Any, 
                           target_id: Any) -> Dict[str, Any]:
        """Detect if one object modulates/controls rate of another."""
        result = {
            'primitive': 'detect_modulating',
            'modulation_detected': False,
            'modulation_type': None,
            'correlation': 0.0
        }
        
        # Would need sophisticated correlation analysis
        return result
    
    def _measure_constraint_strength(self, movement_history: List[dict], object_a: Any, 
                                     object_b: Any) -> Dict[str, Any]:
        """Measure how strongly objects are constrained together."""
        result = {
            'primitive': 'measure_constraint_strength',
            'constraint_strength': 0.0,
            'always_together': False
        }
        
        return result
    
    # ======================================================================
    # MATERIAL PROPERTIES IMPLEMENTATIONS
    # ======================================================================
    
    def _detect_stickiness(self, frame_before: List[List[int]], frame_after: List[List[int]], 
                           action_taken: Any) -> Dict[str, Any]:
        """Detect if objects stick when they touch (abstracted friction)."""
        result = {
            'primitive': 'detect_stickiness',
            'stickiness_detected': False,
            'sticky_pair': None,
            'stick_strength': 0.0
        }
        
        # Check if two objects that touched now move together
        if not frame_before or not frame_after:
            return result
        
        height = min(len(frame_before), len(frame_after))
        width = min(len(frame_before[0]) if frame_before else 0, len(frame_after[0]) if frame_after else 0)
        
        # Find adjacent different colors before
        adjacent_pairs_before = set()
        for y in range(height):
            for x in range(width - 1):
                if frame_before[y][x] != 0 and frame_before[y][x + 1] != 0:
                    if frame_before[y][x] != frame_before[y][x + 1]:
                        adjacent_pairs_before.add((frame_before[y][x], frame_before[y][x + 1]))
        
        # Check if those pairs both moved in same direction
        # Simplified implementation
        if adjacent_pairs_before:
            result['stickiness_detected'] = len(adjacent_pairs_before) > 0
        
        return result
    
    def _detect_bounciness(self, movement_history: List[dict], object_id: Any) -> Dict[str, Any]:
        """Detect if object bounces off boundaries (abstracted elasticity)."""
        result = {
            'primitive': 'detect_bounciness',
            'bounciness_detected': False,
            'bounce_count': 0,
            'bounce_coefficient': 0.0
        }
        
        if not movement_history or len(movement_history) < 3:
            return result
        
        # Look for direction reversals (sign of bouncing)
        bounce_count = 0
        for i in range(2, len(movement_history)):
            if isinstance(movement_history[i], dict) and 'velocity' in movement_history[i]:
                v_curr = movement_history[i]['velocity']
                v_prev = movement_history[i-1].get('velocity', (0, 0))
                
                # Direction reversal = bounce
                if v_curr[0] * v_prev[0] < 0 or v_curr[1] * v_prev[1] < 0:
                    bounce_count += 1
        
        if bounce_count > 0:
            result['bounciness_detected'] = True
            result['bounce_count'] = bounce_count
            result['bounce_coefficient'] = min(1.0, bounce_count / len(movement_history))
        
        return result
    
    def _detect_permeability(self, frame_before: List[List[int]], frame_after: List[List[int]], 
                             barrier_color: int) -> Dict[str, Any]:
        """Detect if objects can pass through barriers (abstracted porosity)."""
        result = {
            'primitive': 'detect_permeability',
            'permeability_detected': False,
            'permeable_barrier': None,
            'passed_through': False
        }
        
        if not frame_before or not frame_after:
            return result
        
        height = min(len(frame_before), len(frame_after))
        width = min(len(frame_before[0]) if frame_before else 0, len(frame_after[0]) if frame_after else 0)
        
        # Check if any non-barrier color appeared on opposite side of barrier
        for y in range(height):
            for x in range(width):
                if frame_before[y][x] == barrier_color:
                    # Check both sides
                    for dx in [-1, 1]:
                        nx = x + dx
                        if 0 <= nx < width:
                            # Different color on one side before, appeared on other side after
                            pass  # Simplified - would need more tracking
        
        return result
    
    def _detect_conductivity(self, frame_before: List[List[int]], frame_after: List[List[int]], 
                             object_id: Any) -> Dict[str, Any]:
        """Detect if color/state propagates through object (abstracted conductivity)."""
        result = {
            'primitive': 'detect_conductivity',
            'conductivity_detected': False,
            'conducted_color': None,
            'propagation_speed': 0
        }
        
        if not frame_before or not frame_after:
            return result
        
        height = min(len(frame_before), len(frame_after))
        width = min(len(frame_before[0]) if frame_before else 0, len(frame_after[0]) if frame_after else 0)
        
        # Look for color spreading through connected cells
        for y in range(height):
            for x in range(width):
                if frame_before[y][x] == 0 and frame_after[y][x] != 0:
                    # New color appeared - check if it came from adjacent
                    new_color = frame_after[y][x]
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= ny < height and 0 <= nx < width:
                            if frame_before[ny][nx] == new_color:
                                result['conductivity_detected'] = True
                                result['conducted_color'] = new_color
                                result['propagation_speed'] += 1
        
        return result
    
    def _detect_resistance(self, action_history: List[Any], movement_history: List[dict]) -> Dict[str, Any]:
        """Detect movement resistance (some directions harder)."""
        result = {
            'primitive': 'detect_resistance',
            'resistance_detected': False,
            'resistant_direction': None,
            'resistance_ratio': {}
        }
        
        if not action_history or not movement_history:
            return result
        
        # Compare action commands to actual movement
        # If action was taken but movement was less than expected, there's resistance
        direction_success = {'up': 0, 'down': 0, 'left': 0, 'right': 0}
        direction_attempts = {'up': 0, 'down': 0, 'left': 0, 'right': 0}
        
        action_map = {1: 'up', 2: 'down', 3: 'left', 4: 'right'}
        
        for i, action in enumerate(action_history):
            if action in action_map and i < len(movement_history):
                direction = action_map[action]
                direction_attempts[direction] += 1
                
                if isinstance(movement_history[i], dict) and movement_history[i].get('moved'):
                    direction_success[direction] += 1
        
        # Calculate resistance ratio
        for direction in direction_success:
            if direction_attempts[direction] > 0:
                ratio = direction_success[direction] / direction_attempts[direction]
                result['resistance_ratio'][direction] = 1.0 - ratio
                if ratio < 0.5:  # Less than 50% success
                    result['resistance_detected'] = True
                    result['resistant_direction'] = direction
        
        return result
    
    # ======================================================================
    # FORCE & ENERGY IMPLEMENTATIONS
    # ======================================================================
    
    def _detect_momentum(self, action_history: List[Any], movement_history: List[dict]) -> Dict[str, Any]:
        """Detect if object continues moving after action stops."""
        result = {
            'primitive': 'detect_momentum',
            'momentum_detected': False,
            'momentum_direction': None,
            'momentum_duration': 0
        }
        
        if not movement_history or len(movement_history) < 3:
            return result
        
        # Look for continued movement after no action
        for i in range(len(movement_history) - 1):
            current = movement_history[i]
            next_m = movement_history[i + 1]
            
            if isinstance(current, dict) and isinstance(next_m, dict):
                # Check if still moving after action stopped
                action = action_history[i] if i < len(action_history) else None
                if action is None or action == 0:  # No action
                    if next_m.get('moved', False):
                        result['momentum_detected'] = True
                        result['momentum_direction'] = next_m.get('direction')
                        result['momentum_duration'] += 1
        
        return result
    
    def _detect_collision_effect(self, frame_before: List[List[int]], frame_after: List[List[int]], 
                                 object_a: Any, object_b: Any) -> Dict[str, Any]:
        """Detect effect of collision between objects."""
        result = {
            'primitive': 'detect_collision_effect',
            'collision_detected': False,
            'effect_type': None,
            'affected_objects': []
        }
        
        # Would need object tracking
        return result
    
    def _detect_pushing(self, frame_before: List[List[int]], frame_after: List[List[int]]) -> Dict[str, Any]:
        """Detect if one object pushes another."""
        result = {
            'primitive': 'detect_pushing',
            'pushing_detected': False,
            'pusher_color': None,
            'pushed_color': None,
            'push_direction': None
        }
        
        if not frame_before or not frame_after:
            return result
        
        height = min(len(frame_before), len(frame_after))
        width = min(len(frame_before[0]) if frame_before else 0, len(frame_after[0]) if frame_after else 0)
        
        # Look for cases where two colors both moved in same direction
        # with one "behind" the other
        
        # Find movement vectors for each color
        color_movements = {}
        for y in range(height):
            for x in range(width):
                if frame_before[y][x] != 0:
                    color = frame_before[y][x]
                    # Find where this color went
                    for ny in range(height):
                        for nx in range(width):
                            if frame_after[ny][nx] == color:
                                if color not in color_movements:
                                    color_movements[color] = []
                                color_movements[color].append((nx - x, ny - y))
        
        # If multiple colors moved in same direction, could be pushing
        directions = set()
        for color, moves in color_movements.items():
            if moves:
                avg_move = (sum(m[0] for m in moves) / len(moves),
                           sum(m[1] for m in moves) / len(moves))
                if avg_move != (0, 0):
                    directions.add((round(avg_move[0]), round(avg_move[1])))
        
        if len(color_movements) >= 2 and len(directions) == 1:
            result['pushing_detected'] = True
            result['push_direction'] = list(directions)[0]
        
        return result
    
    def _detect_pressure(self, frame: List[List[int]], region: List[tuple]) -> Dict[str, Any]:
        """Detect crowding/pressure effects in region."""
        result = {
            'primitive': 'detect_pressure',
            'pressure_detected': False,
            'pressure_level': 0.0,
            'density': 0.0
        }
        
        if not frame or not region:
            return result
        
        # Calculate density of non-background cells in region
        occupied = 0
        for x, y in region:
            if 0 <= y < len(frame) and 0 <= x < len(frame[0]):
                if frame[y][x] != 0:
                    occupied += 1
        
        density = occupied / max(1, len(region))
        result['density'] = density
        
        if density > 0.8:  # High density = pressure
            result['pressure_detected'] = True
            result['pressure_level'] = density
        
        return result
    
    def _detect_tension(self, frame_before: List[List[int]], frame_after: List[List[int]], 
                        connected_objects: List[Any]) -> Dict[str, Any]:
        """Detect tension between connected objects."""
        result = {
            'primitive': 'detect_tension',
            'tension_detected': False,
            'tension_level': 0.0,
            'tension_direction': None
        }
        
        # Would need object connectivity tracking
        return result
    
    # ======================================================================
    # MECHANICAL LINKAGES IMPLEMENTATIONS
    # ======================================================================
    
    def _detect_hinging(self, frame_before: List[List[int]], frame_after: List[List[int]], 
                        object_id: Any) -> Dict[str, Any]:
        """Detect rotation around fixed pivot point."""
        result = {
            'primitive': 'detect_hinging',
            'hinging_detected': False,
            'pivot_point': None,
            'rotation_angle': 0
        }
        
        if not frame_before or not frame_after:
            return result
        
        # Look for cells that stayed in place (potential pivot)
        height = min(len(frame_before), len(frame_after))
        width = min(len(frame_before[0]) if frame_before else 0, len(frame_after[0]) if frame_after else 0)
        
        stationary = []
        moved = []
        
        for y in range(height):
            for x in range(width):
                if frame_before[y][x] != 0 and frame_before[y][x] == frame_after[y][x]:
                    stationary.append((x, y))
                elif frame_before[y][x] != 0 and frame_after[y][x] == 0:
                    moved.append((x, y))
        
        # If there's a stationary point and surrounding points moved, could be hinge
        if stationary and moved:
            result['hinging_detected'] = True
            result['pivot_point'] = stationary[0]
        
        return result
    
    def _detect_lever_action(self, frame_before: List[List[int]], frame_after: List[List[int]], 
                             action_point: tuple, effect_point: tuple) -> Dict[str, Any]:
        """Detect lever-like action (input on one end, output on other)."""
        result = {
            'primitive': 'detect_lever_action',
            'lever_detected': False,
            'fulcrum': None,
            'mechanical_advantage': 0.0
        }
        
        # Simplified implementation
        return result
    
    def _detect_linked_movement(self, frame_before: List[List[int]], frame_after: List[List[int]]) -> Dict[str, Any]:
        """Detect mechanically linked movements (gears, chains)."""
        result = {
            'primitive': 'detect_linked_movement',
            'linked_movement_detected': False,
            'link_type': None,
            'linked_objects': []
        }
        
        if not frame_before or not frame_after:
            return result
        
        # Look for objects that moved in coordinated ways
        height = min(len(frame_before), len(frame_after))
        width = min(len(frame_before[0]) if frame_before else 0, len(frame_after[0]) if frame_after else 0)
        
        # Group movement by color
        color_movements = {}
        for y in range(height):
            for x in range(width):
                before_color = frame_before[y][x]
                if before_color != 0:
                    # Find where this cell went
                    found = False
                    for ny in range(max(0, y-2), min(height, y+3)):
                        for nx in range(max(0, x-2), min(width, x+3)):
                            if frame_after[ny][nx] == before_color and not found:
                                if before_color not in color_movements:
                                    color_movements[before_color] = []
                                color_movements[before_color].append((nx - x, ny - y))
                                found = True
        
        # Check if different colors moved in related ways (opposite, perpendicular)
        colors = list(color_movements.keys())
        if len(colors) >= 2:
            for i, c1 in enumerate(colors):
                for c2 in colors[i+1:]:
                    m1 = color_movements[c1][0] if color_movements[c1] else (0, 0)
                    m2 = color_movements[c2][0] if color_movements[c2] else (0, 0)
                    
                    # Opposite movement (gear-like)
                    if m1[0] == -m2[0] and m1[1] == -m2[1]:
                        result['linked_movement_detected'] = True
                        result['link_type'] = 'gear_opposite'
                        result['linked_objects'] = [c1, c2]
                    
                    # Perpendicular (chain-like)
                    elif (m1[0] == m2[1] and m1[1] == -m2[0]) or \
                         (m1[0] == -m2[1] and m1[1] == m2[0]):
                        result['linked_movement_detected'] = True
                        result['link_type'] = 'perpendicular'
                        result['linked_objects'] = [c1, c2]
        
        return result
    
    def _detect_ratchet(self, action_history: List[Any], movement_history: List[dict]) -> Dict[str, Any]:
        """Detect one-way movement (can go forward, not back)."""
        result = {
            'primitive': 'detect_ratchet',
            'ratchet_detected': False,
            'allowed_direction': None,
            'blocked_direction': None
        }
        
        if not action_history or not movement_history:
            return result
        
        # Track success rate by direction
        direction_success = {1: [], 2: [], 3: [], 4: []}  # action codes
        
        for i, action in enumerate(action_history):
            if action in direction_success and i < len(movement_history):
                moved = movement_history[i].get('moved', False) if isinstance(movement_history[i], dict) else False
                direction_success[action].append(moved)
        
        # Find asymmetry (one direction works, opposite doesn't)
        pairs = [(1, 2), (3, 4)]  # up/down, left/right
        for d1, d2 in pairs:
            s1 = sum(direction_success[d1]) / max(1, len(direction_success[d1])) if direction_success[d1] else 0.5
            s2 = sum(direction_success[d2]) / max(1, len(direction_success[d2])) if direction_success[d2] else 0.5
            
            if s1 > 0.8 and s2 < 0.2:
                result['ratchet_detected'] = True
                result['allowed_direction'] = d1
                result['blocked_direction'] = d2
            elif s2 > 0.8 and s1 < 0.2:
                result['ratchet_detected'] = True
                result['allowed_direction'] = d2
                result['blocked_direction'] = d1
        
        return result
    
    # ======================================================================
    # DEFORMATION IMPLEMENTATIONS
    # ======================================================================
    
    def _detect_stretching(self, frame_before: List[List[int]], frame_after: List[List[int]], 
                           object_id: Any) -> Dict[str, Any]:
        """Detect object stretching (getting longer in one direction)."""
        result = {
            'primitive': 'detect_stretching',
            'stretching_detected': False,
            'stretch_direction': None,
            'stretch_amount': 0
        }
        
        if not frame_before or not frame_after:
            return result
        
        # Find bounding boxes of non-background content
        def get_bounds(frame):
            min_x, max_x, min_y, max_y = float('inf'), -1, float('inf'), -1
            for y, row in enumerate(frame):
                for x, c in enumerate(row):
                    if c != 0:
                        min_x = min(min_x, x)
                        max_x = max(max_x, x)
                        min_y = min(min_y, y)
                        max_y = max(max_y, y)
            return (min_x, max_x, min_y, max_y)
        
        b_before = get_bounds(frame_before)
        b_after = get_bounds(frame_after)
        
        if b_before[1] < 0 or b_after[1] < 0:
            return result
        
        width_before = b_before[1] - b_before[0] + 1
        width_after = b_after[1] - b_after[0] + 1
        height_before = b_before[3] - b_before[2] + 1
        height_after = b_after[3] - b_after[2] + 1
        
        if width_after > width_before and height_after <= height_before:
            result['stretching_detected'] = True
            result['stretch_direction'] = 'horizontal'
            result['stretch_amount'] = width_after - width_before
        elif height_after > height_before and width_after <= width_before:
            result['stretching_detected'] = True
            result['stretch_direction'] = 'vertical'
            result['stretch_amount'] = height_after - height_before
        
        return result
    
    def _detect_compression(self, frame_before: List[List[int]], frame_after: List[List[int]], 
                            object_id: Any) -> Dict[str, Any]:
        """Detect object being compressed/squashed."""
        result = {
            'primitive': 'detect_compression',
            'compression_detected': False,
            'compression_direction': None,
            'compression_amount': 0
        }
        
        if not frame_before or not frame_after:
            return result
        
        def get_bounds(frame):
            min_x, max_x, min_y, max_y = float('inf'), -1, float('inf'), -1
            for y, row in enumerate(frame):
                for x, c in enumerate(row):
                    if c != 0:
                        min_x = min(min_x, x)
                        max_x = max(max_x, x)
                        min_y = min(min_y, y)
                        max_y = max(max_y, y)
            return (min_x, max_x, min_y, max_y)
        
        b_before = get_bounds(frame_before)
        b_after = get_bounds(frame_after)
        
        if b_before[1] < 0 or b_after[1] < 0:
            return result
        
        width_before = b_before[1] - b_before[0] + 1
        width_after = b_after[1] - b_after[0] + 1
        height_before = b_before[3] - b_before[2] + 1
        height_after = b_after[3] - b_after[2] + 1
        
        if width_after < width_before:
            result['compression_detected'] = True
            result['compression_direction'] = 'horizontal'
            result['compression_amount'] = width_before - width_after
        elif height_after < height_before:
            result['compression_detected'] = True
            result['compression_direction'] = 'vertical'
            result['compression_amount'] = height_before - height_after
        
        return result
    
    def _detect_bending(self, frame_before: List[List[int]], frame_after: List[List[int]], 
                        object_id: Any) -> Dict[str, Any]:
        """Detect object bending (changing angle)."""
        result = {
            'primitive': 'detect_bending',
            'bending_detected': False,
            'bend_angle': 0,
            'bend_point': None
        }
        
        # Would need line/shape detection to detect bending
        return result
    
    def _detect_breaking(self, frame_before: List[List[int]], frame_after: List[List[int]], 
                         object_id: Any) -> Dict[str, Any]:
        """Detect object breaking into pieces."""
        result = {
            'primitive': 'detect_breaking',
            'breaking_detected': False,
            'pieces_before': 0,
            'pieces_after': 0
        }
        
        if not frame_before or not frame_after:
            return result
        
        def count_connected_components(frame):
            """Count distinct connected regions."""
            if not frame:
                return 0
            
            height = len(frame)
            width = len(frame[0]) if frame else 0
            visited = [[False] * width for _ in range(height)]
            count = 0
            
            def flood_fill(y, x, color):
                if y < 0 or y >= height or x < 0 or x >= width:
                    return
                if visited[y][x] or frame[y][x] != color:
                    return
                visited[y][x] = True
                for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    flood_fill(y + dy, x + dx, color)
            
            for y in range(height):
                for x in range(width):
                    if frame[y][x] != 0 and not visited[y][x]:
                        flood_fill(y, x, frame[y][x])
                        count += 1
            
            return count
        
        result['pieces_before'] = count_connected_components(frame_before)
        result['pieces_after'] = count_connected_components(frame_after)
        
        if result['pieces_after'] > result['pieces_before']:
            result['breaking_detected'] = True
        
        return result
    
    def _detect_merging(self, frame_before: List[List[int]], frame_after: List[List[int]]) -> Dict[str, Any]:
        """Detect pieces merging into one object."""
        result = {
            'primitive': 'detect_merging',
            'merging_detected': False,
            'pieces_before': 0,
            'pieces_after': 0
        }
        
        if not frame_before or not frame_after:
            return result
        
        def count_connected_components(frame):
            if not frame:
                return 0
            
            height = len(frame)
            width = len(frame[0]) if frame else 0
            visited = [[False] * width for _ in range(height)]
            count = 0
            
            def flood_fill(y, x, color):
                stack = [(y, x)]
                while stack:
                    cy, cx = stack.pop()
                    if cy < 0 or cy >= height or cx < 0 or cx >= width:
                        continue
                    if visited[cy][cx] or frame[cy][cx] != color:
                        continue
                    visited[cy][cx] = True
                    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        stack.append((cy + dy, cx + dx))
            
            for y in range(height):
                for x in range(width):
                    if frame[y][x] != 0 and not visited[y][x]:
                        flood_fill(y, x, frame[y][x])
                        count += 1
            
            return count
        
        result['pieces_before'] = count_connected_components(frame_before)
        result['pieces_after'] = count_connected_components(frame_after)
        
        if result['pieces_after'] < result['pieces_before']:
            result['merging_detected'] = True
        
        return result
    
    # ======================================================================
    # PROBABILITY & UNCERTAINTY IMPLEMENTATIONS
    # ======================================================================
    
    def _estimate_position_uncertainty(self, movement_history: List[dict], object_id: Any) -> Dict[str, Any]:
        """Estimate uncertainty in object position prediction."""
        result = {
            'primitive': 'estimate_position_uncertainty',
            'uncertainty': 1.0,
            'variance_x': 0.0,
            'variance_y': 0.0
        }
        
        if not movement_history or len(movement_history) < 2:
            return result
        
        # Calculate variance in movement
        movements = []
        for entry in movement_history:
            if isinstance(entry, dict) and 'delta' in entry:
                movements.append(entry['delta'])
        
        if not movements:
            return result
        
        mean_x = sum(m[0] for m in movements) / len(movements)
        mean_y = sum(m[1] for m in movements) / len(movements)
        
        var_x = sum((m[0] - mean_x) ** 2 for m in movements) / len(movements)
        var_y = sum((m[1] - mean_y) ** 2 for m in movements) / len(movements)
        
        result['variance_x'] = var_x
        result['variance_y'] = var_y
        result['uncertainty'] = (var_x + var_y) ** 0.5
        
        return result
    
    def _predict_collision_probability(self, object_a_trajectory: List[tuple], 
                                        object_b_trajectory: List[tuple]) -> Dict[str, Any]:
        """Estimate probability of collision given trajectories."""
        result = {
            'primitive': 'predict_collision_probability',
            'probability': 0.0,
            'collision_time': None,
            'collision_point': None
        }
        
        if not object_a_trajectory or not object_b_trajectory:
            return result
        
        # Extrapolate trajectories and check for intersection
        # Simplified: check if trajectories are converging
        if len(object_a_trajectory) >= 2 and len(object_b_trajectory) >= 2:
            # Calculate velocities
            va = (object_a_trajectory[-1][0] - object_a_trajectory[-2][0],
                  object_a_trajectory[-1][1] - object_a_trajectory[-2][1])
            vb = (object_b_trajectory[-1][0] - object_b_trajectory[-2][0],
                  object_b_trajectory[-1][1] - object_b_trajectory[-2][1])
            
            # Current positions
            pa = object_a_trajectory[-1]
            pb = object_b_trajectory[-1]
            
            # Current distance
            dist = abs(pa[0] - pb[0]) + abs(pa[1] - pb[1])
            
            # Relative velocity toward each other
            rel_v = ((pb[0] - pa[0]) * (va[0] - vb[0]) + 
                     (pb[1] - pa[1]) * (va[1] - vb[1]))
            
            if rel_v > 0 and dist > 0:
                # Objects converging
                time_to_collision = dist / max(1, abs(rel_v))
                result['probability'] = min(1.0, 1.0 / max(1, time_to_collision))
                result['collision_time'] = time_to_collision
        
        return result
    
    def _estimate_stability_risk(self, frame: List[List[int]], object_id: Any) -> Dict[str, Any]:
        """Estimate risk of unstable configuration."""
        result = {
            'primitive': 'estimate_stability_risk',
            'risk': 0.0,
            'unstable_factors': []
        }
        
        if not frame:
            return result
        
        height = len(frame)
        width = len(frame[0]) if frame else 0
        
        # Check for "floating" objects (not connected to bottom or edges)
        floating_objects = 0
        grounded_objects = 0
        
        for y in range(height):
            for x in range(width):
                if frame[y][x] != 0:
                    # Check if touching bottom
                    if y == height - 1:
                        grounded_objects += 1
                    else:
                        # Check if supported
                        if y + 1 < height and frame[y + 1][x] != 0:
                            grounded_objects += 1
                        else:
                            floating_objects += 1
        
        total = floating_objects + grounded_objects
        if total > 0:
            result['risk'] = floating_objects / total
            if floating_objects > 0:
                result['unstable_factors'].append('floating_objects')
        
        return result
    
    def _confidence_in_pattern(self, observations: List[Any], pattern_hypothesis: Any) -> Dict[str, Any]:
        """Estimate confidence that detected pattern is real."""
        result = {
            'primitive': 'confidence_in_pattern',
            'confidence': 0.5,
            'supporting_observations': 0,
            'contradicting_observations': 0
        }
        
        if not observations:
            return result
        
        # Count how many observations support vs contradict
        supporting = 0
        contradicting = 0
        
        for obs in observations:
            if isinstance(obs, dict):
                if obs.get('matches_pattern', False):
                    supporting += 1
                elif obs.get('contradicts_pattern', False):
                    contradicting += 1
        
        total = supporting + contradicting
        if total > 0:
            result['confidence'] = supporting / total
            result['supporting_observations'] = supporting
            result['contradicting_observations'] = contradicting
        
        return result
    
    # ======================================================================
    # GOAL & INTENTION IMPLEMENTATIONS
    # ======================================================================
    
    def _infer_goal_from_behavior(self, movement_history: List[dict], frame: List[List[int]]) -> Dict[str, Any]:
        """Infer what goal an object/agent might be pursuing."""
        result = {
            'primitive': 'infer_goal_from_behavior',
            'inferred_goal': None,
            'goal_type': None,
            'confidence': 0.0
        }
        
        if not movement_history or not frame:
            return result
        
        # Analyze movement direction consistency
        directions = []
        for entry in movement_history:
            if isinstance(entry, dict) and 'direction' in entry:
                directions.append(entry['direction'])
        
        if not directions:
            return result
        
        # If consistent direction, might be moving toward something
        direction_counts = {}
        for d in directions:
            direction_counts[d] = direction_counts.get(d, 0) + 1
        
        if direction_counts:
            most_common = max(direction_counts, key=direction_counts.get)
            consistency = direction_counts[most_common] / len(directions)
            
            if consistency > 0.7:
                result['inferred_goal'] = f'moving_{most_common}'
                result['goal_type'] = 'directional_movement'
                result['confidence'] = consistency
        
        return result
    
    def _detect_goal_achievement(self, frame: List[List[int]], goal_state: Any) -> Dict[str, Any]:
        """Detect when a goal state is achieved."""
        result = {
            'primitive': 'detect_goal_achievement',
            'achieved': False,
            'match_percentage': 0.0
        }
        
        if not frame or not goal_state:
            return result
        
        if isinstance(goal_state, list) and isinstance(goal_state[0], list):
            # Goal is a frame
            height = min(len(frame), len(goal_state))
            width = min(len(frame[0]) if frame else 0, len(goal_state[0]) if goal_state else 0)
            
            matching = 0
            total = 0
            for y in range(height):
                for x in range(width):
                    total += 1
                    if frame[y][x] == goal_state[y][x]:
                        matching += 1
            
            result['match_percentage'] = matching / max(1, total)
            result['achieved'] = result['match_percentage'] == 1.0
        
        return result
    
    def _measure_goal_distance(self, frame: List[List[int]], goal_state: Any) -> Dict[str, Any]:
        """Measure how far current state is from goal state."""
        result = {
            'primitive': 'measure_goal_distance',
            'distance': float('inf'),
            'cells_different': 0
        }
        
        if not frame or not goal_state:
            return result
        
        if isinstance(goal_state, list) and isinstance(goal_state[0], list):
            height = min(len(frame), len(goal_state))
            width = min(len(frame[0]) if frame else 0, len(goal_state[0]) if goal_state else 0)
            
            different = 0
            for y in range(height):
                for x in range(width):
                    if frame[y][x] != goal_state[y][x]:
                        different += 1
            
            result['cells_different'] = different
            result['distance'] = different
        
        return result
    
    def _detect_subgoal(self, frame: List[List[int]], final_goal: Any, obstacles: List[Any]) -> Dict[str, Any]:
        """Detect intermediate goal that enables final goal."""
        result = {
            'primitive': 'detect_subgoal',
            'subgoal_detected': False,
            'subgoal': None,
            'subgoal_type': None
        }
        
        if not obstacles:
            return result
        
        # If there are obstacles between current state and goal,
        # removing/bypassing obstacle is a subgoal
        if obstacles:
            result['subgoal_detected'] = True
            result['subgoal'] = 'remove_obstacle'
            result['subgoal_type'] = 'obstacle_removal'
        
        return result
    
    # ======================================================================
    # RESOURCE & INVENTORY IMPLEMENTATIONS
    # ======================================================================
    
    def _count_resource(self, frame: List[List[int]], resource_color: int) -> Dict[str, Any]:
        """Count instances of a resource type in frame."""
        result = {
            'primitive': 'count_resource',
            'count': 0,
            'positions': []
        }
        
        if not frame:
            return result
        
        for y, row in enumerate(frame):
            for x, c in enumerate(row):
                if c == resource_color:
                    result['count'] += 1
                    result['positions'].append((x, y))
        
        return result
    
    def _detect_resource_depletion(self, frame_before: List[List[int]], frame_after: List[List[int]], 
                                   resource_color: int) -> Dict[str, Any]:
        """Detect resources being consumed/depleted."""
        result = {
            'primitive': 'detect_resource_depletion',
            'depletion_detected': False,
            'amount_depleted': 0,
            'depletion_locations': []
        }
        
        if not frame_before or not frame_after:
            return result
        
        height = min(len(frame_before), len(frame_after))
        width = min(len(frame_before[0]) if frame_before else 0, len(frame_after[0]) if frame_after else 0)
        
        for y in range(height):
            for x in range(width):
                if frame_before[y][x] == resource_color and frame_after[y][x] != resource_color:
                    result['depletion_detected'] = True
                    result['amount_depleted'] += 1
                    result['depletion_locations'].append((x, y))
        
        return result
    
    def _detect_resource_generation(self, frame_before: List[List[int]], frame_after: List[List[int]], 
                                    resource_color: int) -> Dict[str, Any]:
        """Detect new resources being generated."""
        result = {
            'primitive': 'detect_resource_generation',
            'generation_detected': False,
            'amount_generated': 0,
            'generation_locations': []
        }
        
        if not frame_before or not frame_after:
            return result
        
        height = min(len(frame_before), len(frame_after))
        width = min(len(frame_before[0]) if frame_before else 0, len(frame_after[0]) if frame_after else 0)
        
        for y in range(height):
            for x in range(width):
                if frame_before[y][x] != resource_color and frame_after[y][x] == resource_color:
                    result['generation_detected'] = True
                    result['amount_generated'] += 1
                    result['generation_locations'].append((x, y))
        
        return result
    
    def _measure_carrying_capacity(self, frame: List[List[int]], container_region: List[tuple]) -> Dict[str, Any]:
        """Measure how much a container/region can hold."""
        result = {
            'primitive': 'measure_carrying_capacity',
            'capacity': 0,
            'current_fill': 0,
            'remaining': 0
        }
        
        if not frame or not container_region:
            return result
        
        result['capacity'] = len(container_region)
        
        filled = 0
        for x, y in container_region:
            if 0 <= y < len(frame) and 0 <= x < len(frame[0]):
                if frame[y][x] != 0:
                    filled += 1
        
        result['current_fill'] = filled
        result['remaining'] = result['capacity'] - filled
        
        return result
    
    # ======================================================================
    # SCALE & AGGREGATION GAP IMPLEMENTATIONS
    # ======================================================================
    
    def _detect_shattering(self, frame_before: List[List[int]], frame_after: List[List[int]], 
                           object_id: Any) -> Dict[str, Any]:
        """Detect object exploding into many scattered pieces."""
        result = {
            'primitive': 'detect_shattering',
            'shattering_detected': False,
            'pieces_before': 0,
            'pieces_after': 0,
            'scatter_radius': 0
        }
        
        if not frame_before or not frame_after:
            return result
        
        def count_components_and_centroid(frame):
            """Count connected components and find centroids."""
            height = len(frame)
            width = len(frame[0]) if frame else 0
            visited = [[False] * width for _ in range(height)]
            components = []
            
            def flood_fill(y, x, color):
                if y < 0 or y >= height or x < 0 or x >= width:
                    return []
                if visited[y][x] or frame[y][x] != color or color == 0:
                    return []
                visited[y][x] = True
                cells = [(x, y)]
                for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    cells.extend(flood_fill(y + dy, x + dx, color))
                return cells
            
            for y in range(height):
                for x in range(width):
                    if frame[y][x] != 0 and not visited[y][x]:
                        cells = flood_fill(y, x, frame[y][x])
                        if cells:
                            cx = sum(c[0] for c in cells) / len(cells)
                            cy = sum(c[1] for c in cells) / len(cells)
                            components.append({'cells': cells, 'centroid': (cx, cy), 'color': frame[y][x]})
            
            return components
        
        comp_before = count_components_and_centroid(frame_before)
        comp_after = count_components_and_centroid(frame_after)
        
        result['pieces_before'] = len(comp_before)
        result['pieces_after'] = len(comp_after)
        
        # Shattering = many more pieces after, scattered
        if result['pieces_after'] > result['pieces_before'] * 2:
            result['shattering_detected'] = True
            
            # Calculate scatter radius
            if comp_after:
                centroids = [c['centroid'] for c in comp_after]
                avg_x = sum(c[0] for c in centroids) / len(centroids)
                avg_y = sum(c[1] for c in centroids) / len(centroids)
                scatter = sum(((c[0] - avg_x)**2 + (c[1] - avg_y)**2)**0.5 for c in centroids) / len(centroids)
                result['scatter_radius'] = scatter
        
        return result
    
    def _detect_subdivision(self, frame_before: List[List[int]], frame_after: List[List[int]]) -> Dict[str, Any]:
        """Detect controlled division into regular parts."""
        result = {
            'primitive': 'detect_subdivision',
            'subdivision_detected': False,
            'division_type': None,
            'num_divisions': 0,
            'parts_equal_size': False
        }
        
        if not frame_before or not frame_after:
            return result
        
        def get_component_sizes(frame):
            height = len(frame)
            width = len(frame[0]) if frame else 0
            visited = [[False] * width for _ in range(height)]
            sizes = []
            
            def flood_fill(y, x, color):
                if y < 0 or y >= height or x < 0 or x >= width:
                    return 0
                if visited[y][x] or frame[y][x] != color or color == 0:
                    return 0
                visited[y][x] = True
                count = 1
                for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    count += flood_fill(y + dy, x + dx, color)
                return count
            
            for y in range(height):
                for x in range(width):
                    if frame[y][x] != 0 and not visited[y][x]:
                        size = flood_fill(y, x, frame[y][x])
                        if size > 0:
                            sizes.append(size)
            return sizes
        
        sizes_before = get_component_sizes(frame_before)
        sizes_after = get_component_sizes(frame_after)
        
        if len(sizes_after) > len(sizes_before):
            result['subdivision_detected'] = True
            result['num_divisions'] = len(sizes_after) - len(sizes_before) + 1
            
            # Check if parts are equal size
            if sizes_after:
                avg_size = sum(sizes_after) / len(sizes_after)
                variance = sum((s - avg_size)**2 for s in sizes_after) / len(sizes_after)
                result['parts_equal_size'] = variance < avg_size * 0.1  # 10% tolerance
                
                if result['parts_equal_size']:
                    result['division_type'] = 'regular'
                else:
                    result['division_type'] = 'irregular'
        
        return result
    
    def _count_pieces(self, frame: List[List[int]], target_color: int) -> Dict[str, Any]:
        """Count number of distinct connected pieces of a color."""
        result = {
            'primitive': 'count_pieces',
            'count': 0,
            'sizes': [],
            'centroids': []
        }
        
        if not frame:
            return result
        
        height = len(frame)
        width = len(frame[0]) if frame else 0
        visited = [[False] * width for _ in range(height)]
        
        def flood_fill(y, x):
            if y < 0 or y >= height or x < 0 or x >= width:
                return []
            if visited[y][x] or frame[y][x] != target_color:
                return []
            visited[y][x] = True
            cells = [(x, y)]
            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                cells.extend(flood_fill(y + dy, x + dx))
            return cells
        
        for y in range(height):
            for x in range(width):
                if frame[y][x] == target_color and not visited[y][x]:
                    cells = flood_fill(y, x)
                    if cells:
                        result['count'] += 1
                        result['sizes'].append(len(cells))
                        cx = sum(c[0] for c in cells) / len(cells)
                        cy = sum(c[1] for c in cells) / len(cells)
                        result['centroids'].append((cx, cy))
        
        return result
    
    def _detect_aggregation(self, frame_before: List[List[int]], frame_after: List[List[int]]) -> Dict[str, Any]:
        """Detect pieces coming together into larger whole."""
        result = {
            'primitive': 'detect_aggregation',
            'aggregation_detected': False,
            'pieces_before': 0,
            'pieces_after': 0,
            'aggregation_ratio': 0.0
        }
        
        if not frame_before or not frame_after:
            return result
        
        def count_components(frame):
            height = len(frame)
            width = len(frame[0]) if frame else 0
            visited = [[False] * width for _ in range(height)]
            count = 0
            
            def flood_fill(y, x, color):
                if y < 0 or y >= height or x < 0 or x >= width:
                    return
                if visited[y][x] or frame[y][x] != color or color == 0:
                    return
                visited[y][x] = True
                for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    flood_fill(y + dy, x + dx, color)
            
            for y in range(height):
                for x in range(width):
                    if frame[y][x] != 0 and not visited[y][x]:
                        flood_fill(y, x, frame[y][x])
                        count += 1
            return count
        
        result['pieces_before'] = count_components(frame_before)
        result['pieces_after'] = count_components(frame_after)
        
        if result['pieces_after'] < result['pieces_before']:
            result['aggregation_detected'] = True
            result['aggregation_ratio'] = result['pieces_before'] / max(1, result['pieces_after'])
        
        return result
    
    # ======================================================================
    # PENETRATION & PIERCING IMPLEMENTATIONS
    # ======================================================================
    
    def _detect_piercing(self, frame_before: List[List[int]], frame_after: List[List[int]], 
                         barrier_color: int) -> Dict[str, Any]:
        """Detect object passing completely through barrier."""
        result = {
            'primitive': 'detect_piercing',
            'piercing_detected': False,
            'piercing_color': None,
            'barrier_color': barrier_color,
            'entry_point': None,
            'exit_point': None
        }
        
        if not frame_before or not frame_after:
            return result
        
        height = min(len(frame_before), len(frame_after))
        width = min(len(frame_before[0]) if frame_before else 0, len(frame_after[0]) if frame_after else 0)
        
        # Find barrier cells
        barrier_cells = set()
        for y in range(height):
            for x in range(width):
                if frame_before[y][x] == barrier_color:
                    barrier_cells.add((x, y))
        
        # Check if any non-barrier color appeared on opposite side
        for y in range(height):
            for x in range(width):
                if (x, y) in barrier_cells:
                    continue
                
                after_color = frame_after[y][x]
                if after_color != 0 and after_color != barrier_color:
                    # Check if this color was on opposite side of barrier before
                    for bx, by in barrier_cells:
                        # Check opposite direction from barrier
                        dx = x - bx
                        dy = y - by
                        opp_x = bx - dx
                        opp_y = by - dy
                        if 0 <= opp_y < height and 0 <= opp_x < width:
                            if frame_before[opp_y][opp_x] == after_color:
                                result['piercing_detected'] = True
                                result['piercing_color'] = after_color
                                result['entry_point'] = (opp_x, opp_y)
                                result['exit_point'] = (x, y)
                                return result
        
        return result
    
    def _detect_partial_penetration(self, frame: List[List[int]], object_a_color: int, 
                                    object_b_color: int) -> Dict[str, Any]:
        """Detect object partially inside another."""
        result = {
            'primitive': 'detect_partial_penetration',
            'penetration_detected': False,
            'overlap_cells': 0,
            'overlap_region': []
        }
        
        if not frame:
            return result
        
        height = len(frame)
        width = len(frame[0]) if frame else 0
        
        # Find cells where both colors are adjacent (overlapping boundary)
        for y in range(height):
            for x in range(width):
                if frame[y][x] == object_a_color:
                    # Check if adjacent to object_b
                    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < height and 0 <= nx < width:
                            if frame[ny][nx] == object_b_color:
                                result['penetration_detected'] = True
                                result['overlap_cells'] += 1
                                result['overlap_region'].append((x, y))
        
        return result
    
    def _detect_projectile(self, frame_before: List[List[int]], frame_after: List[List[int]]) -> Dict[str, Any]:
        """Detect fast-moving object crossing space."""
        result = {
            'primitive': 'detect_projectile',
            'projectile_detected': False,
            'projectile_color': None,
            'start_position': None,
            'end_position': None,
            'distance_traveled': 0
        }
        
        if not frame_before or not frame_after:
            return result
        
        height = min(len(frame_before), len(frame_after))
        width = min(len(frame_before[0]) if frame_before else 0, len(frame_after[0]) if frame_after else 0)
        
        # Find colors that moved significantly
        color_positions_before = {}
        color_positions_after = {}
        
        for y in range(height):
            for x in range(width):
                c_before = frame_before[y][x]
                c_after = frame_after[y][x]
                if c_before != 0:
                    if c_before not in color_positions_before:
                        color_positions_before[c_before] = []
                    color_positions_before[c_before].append((x, y))
                if c_after != 0:
                    if c_after not in color_positions_after:
                        color_positions_after[c_after] = []
                    color_positions_after[c_after].append((x, y))
        
        # Check for significant movement
        for color in color_positions_before:
            if color in color_positions_after:
                before_pos = color_positions_before[color]
                after_pos = color_positions_after[color]
                
                if before_pos and after_pos:
                    # Calculate centroid movement
                    before_cx = sum(p[0] for p in before_pos) / len(before_pos)
                    before_cy = sum(p[1] for p in before_pos) / len(before_pos)
                    after_cx = sum(p[0] for p in after_pos) / len(after_pos)
                    after_cy = sum(p[1] for p in after_pos) / len(after_pos)
                    
                    distance = ((after_cx - before_cx)**2 + (after_cy - before_cy)**2)**0.5
                    
                    # Projectile = moved more than 3 cells
                    if distance > 3:
                        result['projectile_detected'] = True
                        result['projectile_color'] = color
                        result['start_position'] = (before_cx, before_cy)
                        result['end_position'] = (after_cx, after_cy)
                        result['distance_traveled'] = distance
                        return result
        
        return result
    
    def _detect_passthrough(self, movement_history: List[dict], frame: List[List[int]]) -> Dict[str, Any]:
        """Detect which barriers allow passage and which block."""
        result = {
            'primitive': 'detect_passthrough',
            'passthrough_colors': [],
            'blocking_colors': [],
            'analysis_complete': False
        }
        
        if not movement_history or not frame:
            return result
        
        # Analyze movement history to find colors that blocked vs allowed passage
        blocking = set()
        passthrough = set()
        
        for entry in movement_history:
            if isinstance(entry, dict):
                if entry.get('blocked_by'):
                    blocking.add(entry['blocked_by'])
                if entry.get('passed_through'):
                    passthrough.add(entry['passed_through'])
        
        result['blocking_colors'] = list(blocking)
        result['passthrough_colors'] = list(passthrough)
        result['analysis_complete'] = len(blocking) > 0 or len(passthrough) > 0
        
        return result
    
    # ======================================================================
    # SENSING & VISIBILITY IMPLEMENTATIONS
    # ======================================================================
    
    def _detect_transparency(self, frame_history: List[List[List[int]]]) -> Dict[str, Any]:
        """Detect if one color can 'see through' to show underlying color."""
        result = {
            'primitive': 'detect_transparency',
            'transparency_detected': False,
            'transparent_color': None,
            'underlying_colors': []
        }
        
        if not frame_history or len(frame_history) < 2:
            return result
        
        # Look for cases where a color moves over another and the underlying color
        # remains visible or reappears
        for i in range(1, len(frame_history)):
            before = frame_history[i-1]
            after = frame_history[i]
            
            if not before or not after:
                continue
            
            height = min(len(before), len(after))
            width = min(len(before[0]) if before else 0, len(after[0]) if after else 0)
            
            for y in range(height):
                for x in range(width):
                    # If color A was here, now color B is here, but A is still visible nearby
                    before_color = before[y][x]
                    after_color = after[y][x]
                    
                    if before_color != 0 and after_color != 0 and before_color != after_color:
                        # Check if the before_color is still visible adjacent
                        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            ny, nx = y + dy, x + dx
                            if 0 <= ny < height and 0 <= nx < width:
                                if after[ny][nx] == before_color:
                                    # Possible transparency - after_color "on top" of before_color
                                    result['transparency_detected'] = True
                                    result['transparent_color'] = after_color
                                    if before_color not in result['underlying_colors']:
                                        result['underlying_colors'].append(before_color)
        
        return result
    
    def _detect_layering(self, frame_history: List[List[List[int]]]) -> Dict[str, Any]:
        """Detect objects stacked in layers (z-order)."""
        result = {
            'primitive': 'detect_layering',
            'layering_detected': False,
            'layer_order': [],
            'overlap_regions': []
        }
        
        if not frame_history or len(frame_history) < 2:
            return result
        
        # Track which colors appear "on top" of others based on occlusion patterns
        on_top_of = {}  # color -> set of colors it's on top of
        
        for i in range(1, len(frame_history)):
            before = frame_history[i-1]
            after = frame_history[i]
            
            if not before or not after:
                continue
            
            height = min(len(before), len(after))
            width = min(len(before[0]) if before else 0, len(after[0]) if after else 0)
            
            for y in range(height):
                for x in range(width):
                    before_color = before[y][x]
                    after_color = after[y][x]
                    
                    if before_color != 0 and after_color != 0 and before_color != after_color:
                        # after_color is now "on top" of where before_color was
                        if after_color not in on_top_of:
                            on_top_of[after_color] = set()
                        on_top_of[after_color].add(before_color)
        
        if on_top_of:
            result['layering_detected'] = True
            # Simple layer order (top to bottom)
            for top_color, bottom_colors in on_top_of.items():
                result['layer_order'].append({'top': top_color, 'below': list(bottom_colors)})
        
        return result
    
    def _detect_occlusion(self, frame_before: List[List[int]], frame_after: List[List[int]]) -> Dict[str, Any]:
        """Detect object hiding/revealing another object."""
        result = {
            'primitive': 'detect_occlusion',
            'occlusion_detected': False,
            'hidden_color': None,
            'occluding_color': None,
            'revealed_color': None
        }
        
        if not frame_before or not frame_after:
            return result
        
        height = min(len(frame_before), len(frame_after))
        width = min(len(frame_before[0]) if frame_before else 0, len(frame_after[0]) if frame_after else 0)
        
        for y in range(height):
            for x in range(width):
                before_color = frame_before[y][x]
                after_color = frame_after[y][x]
                
                # Something was hidden (color disappeared, replaced by another)
                if before_color != 0 and after_color != 0 and before_color != after_color:
                    result['occlusion_detected'] = True
                    result['hidden_color'] = before_color
                    result['occluding_color'] = after_color
                    return result
                
                # Something was revealed (background became color, or different color)
                if before_color != 0 and after_color == 0:
                    # Check nearby for what might have moved away
                    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < height and 0 <= nx < width:
                            if frame_after[ny][nx] == before_color and frame_before[ny][nx] != before_color:
                                result['occlusion_detected'] = True
                                result['revealed_color'] = frame_after[y][x] if frame_after[y][x] != 0 else 'background'
                                return result
        
        return result
    
    def _detect_line_of_sight(self, frame: List[List[int]], point_a: tuple, point_b: tuple) -> Dict[str, Any]:
        """Check if clear path exists between two points."""
        result = {
            'primitive': 'detect_line_of_sight',
            'clear_path': True,
            'blocking_cells': [],
            'path_length': 0
        }
        
        if not frame or not point_a or not point_b:
            return result
        
        x1, y1 = point_a
        x2, y2 = point_b
        
        # Bresenham's line algorithm
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        x, y = x1, y1
        path_cells = []
        
        while True:
            if 0 <= y < len(frame) and 0 <= x < len(frame[0]):
                path_cells.append((x, y))
                if frame[y][x] != 0 and (x, y) != point_a and (x, y) != point_b:
                    result['clear_path'] = False
                    result['blocking_cells'].append((x, y))
            
            if x == x2 and y == y2:
                break
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
        
        result['path_length'] = len(path_cells)
        
        return result
    
    def _detect_visibility_change(self, frame_before: List[List[int]], frame_after: List[List[int]]) -> Dict[str, Any]:
        """Detect what became visible/hidden between frames."""
        result = {
            'primitive': 'detect_visibility_change',
            'became_visible': [],
            'became_hidden': [],
            'visibility_changed': False
        }
        
        if not frame_before or not frame_after:
            return result
        
        height = min(len(frame_before), len(frame_after))
        width = min(len(frame_before[0]) if frame_before else 0, len(frame_after[0]) if frame_after else 0)
        
        became_visible = set()
        became_hidden = set()
        
        for y in range(height):
            for x in range(width):
                before_color = frame_before[y][x]
                after_color = frame_after[y][x]
                
                if before_color == 0 and after_color != 0:
                    became_visible.add(after_color)
                elif before_color != 0 and after_color == 0:
                    became_hidden.add(before_color)
        
        result['became_visible'] = list(became_visible)
        result['became_hidden'] = list(became_hidden)
        result['visibility_changed'] = len(became_visible) > 0 or len(became_hidden) > 0
        
        return result
    
    # ======================================================================
    # TEXTURE & SURFACE PATTERN IMPLEMENTATIONS
    # ======================================================================
    
    def _detect_stripe_pattern(self, frame: List[List[int]], region: List[tuple] = None) -> Dict[str, Any]:
        """Detect alternating stripe pattern (horizontal or vertical)."""
        result = {
            'primitive': 'detect_stripe_pattern',
            'stripe_detected': False,
            'orientation': None,
            'stripe_colors': [],
            'stripe_width': 0
        }
        
        if not frame:
            return result
        
        height = len(frame)
        width = len(frame[0]) if frame else 0
        
        # Check horizontal stripes (rows of same color)
        row_colors = []
        for y in range(height):
            row_unique = set(frame[y])
            if len(row_unique) == 1 and 0 not in row_unique:
                row_colors.append(list(row_unique)[0])
            elif len(row_unique) == 2 and 0 in row_unique:
                row_colors.append([c for c in row_unique if c != 0][0])
            else:
                row_colors.append(None)
        
        # Check for alternating pattern in rows
        if len(row_colors) >= 2:
            alternating = True
            prev_color = row_colors[0]
            for i in range(1, len(row_colors)):
                if row_colors[i] is None:
                    alternating = False
                    break
                if row_colors[i] == prev_color:
                    alternating = False
                    break
                prev_color = row_colors[i]
            
            if alternating:
                result['stripe_detected'] = True
                result['orientation'] = 'horizontal'
                result['stripe_colors'] = list(set(c for c in row_colors if c is not None))
                result['stripe_width'] = 1
                return result
        
        # Check vertical stripes (columns of same color)
        col_colors = []
        for x in range(width):
            col_unique = set(frame[y][x] for y in range(height))
            if len(col_unique) == 1 and 0 not in col_unique:
                col_colors.append(list(col_unique)[0])
            else:
                col_colors.append(None)
        
        if len(col_colors) >= 2:
            alternating = True
            prev_color = col_colors[0]
            for i in range(1, len(col_colors)):
                if col_colors[i] is None:
                    alternating = False
                    break
                if col_colors[i] == prev_color:
                    alternating = False
                    break
                prev_color = col_colors[i]
            
            if alternating:
                result['stripe_detected'] = True
                result['orientation'] = 'vertical'
                result['stripe_colors'] = list(set(c for c in col_colors if c is not None))
                result['stripe_width'] = 1
        
        return result
    
    def _detect_checker_pattern(self, frame: List[List[int]], region: List[tuple] = None) -> Dict[str, Any]:
        """Detect checkerboard/alternating grid pattern."""
        result = {
            'primitive': 'detect_checker_pattern',
            'checker_detected': False,
            'checker_colors': [],
            'cell_size': 1
        }
        
        if not frame:
            return result
        
        height = len(frame)
        width = len(frame[0]) if frame else 0
        
        # Check for 1x1 checkerboard: (x+y) % 2 determines color
        colors_even = set()
        colors_odd = set()
        
        for y in range(height):
            for x in range(width):
                color = frame[y][x]
                if color != 0:
                    if (x + y) % 2 == 0:
                        colors_even.add(color)
                    else:
                        colors_odd.add(color)
        
        # Perfect checkerboard: exactly one color for even, one for odd
        if len(colors_even) == 1 and len(colors_odd) == 1 and colors_even != colors_odd:
            result['checker_detected'] = True
            result['checker_colors'] = list(colors_even | colors_odd)
            result['cell_size'] = 1
        
        return result
    
    def _detect_gradient(self, frame: List[List[int]], region: List[tuple] = None) -> Dict[str, Any]:
        """Detect color value changing gradually across region."""
        result = {
            'primitive': 'detect_gradient',
            'gradient_detected': False,
            'gradient_direction': None,
            'color_sequence': []
        }
        
        if not frame:
            return result
        
        height = len(frame)
        width = len(frame[0]) if frame else 0
        
        # Check horizontal gradient (color changes left to right)
        row_avg_colors = []
        for x in range(width):
            colors = [frame[y][x] for y in range(height) if frame[y][x] != 0]
            if colors:
                row_avg_colors.append(sum(colors) / len(colors))
        
        if len(row_avg_colors) >= 3:
            # Check if monotonically increasing or decreasing
            increasing = all(row_avg_colors[i] <= row_avg_colors[i+1] for i in range(len(row_avg_colors)-1))
            decreasing = all(row_avg_colors[i] >= row_avg_colors[i+1] for i in range(len(row_avg_colors)-1))
            
            if increasing and row_avg_colors[0] != row_avg_colors[-1]:
                result['gradient_detected'] = True
                result['gradient_direction'] = 'horizontal_increasing'
                result['color_sequence'] = row_avg_colors
            elif decreasing and row_avg_colors[0] != row_avg_colors[-1]:
                result['gradient_detected'] = True
                result['gradient_direction'] = 'horizontal_decreasing'
                result['color_sequence'] = row_avg_colors
        
        # Check vertical gradient
        if not result['gradient_detected']:
            col_avg_colors = []
            for y in range(height):
                colors = [frame[y][x] for x in range(width) if frame[y][x] != 0]
                if colors:
                    col_avg_colors.append(sum(colors) / len(colors))
            
            if len(col_avg_colors) >= 3:
                increasing = all(col_avg_colors[i] <= col_avg_colors[i+1] for i in range(len(col_avg_colors)-1))
                decreasing = all(col_avg_colors[i] >= col_avg_colors[i+1] for i in range(len(col_avg_colors)-1))
                
                if increasing and col_avg_colors[0] != col_avg_colors[-1]:
                    result['gradient_detected'] = True
                    result['gradient_direction'] = 'vertical_increasing'
                    result['color_sequence'] = col_avg_colors
                elif decreasing and col_avg_colors[0] != col_avg_colors[-1]:
                    result['gradient_detected'] = True
                    result['gradient_direction'] = 'vertical_decreasing'
                    result['color_sequence'] = col_avg_colors
        
        return result
    
    def _measure_pattern_regularity(self, frame: List[List[int]], region: List[tuple] = None) -> Dict[str, Any]:
        """Measure how regular/repeated a pattern is."""
        result = {
            'primitive': 'measure_pattern_regularity',
            'regularity_score': 0.0,
            'repeat_period': None,
            'is_regular': False
        }
        
        if not frame:
            return result
        
        height = len(frame)
        width = len(frame[0]) if frame else 0
        
        # Check for horizontal repetition
        best_period = None
        best_score = 0.0
        
        for period in range(1, width // 2 + 1):
            matches = 0
            total = 0
            for y in range(height):
                for x in range(width - period):
                    total += 1
                    if frame[y][x] == frame[y][x + period]:
                        matches += 1
            
            if total > 0:
                score = matches / total
                if score > best_score:
                    best_score = score
                    best_period = period
        
        result['regularity_score'] = best_score
        result['repeat_period'] = best_period
        result['is_regular'] = best_score > 0.8
        
        return result
    
    def _detect_texture_boundary(self, frame: List[List[int]]) -> Dict[str, Any]:
        """Detect where one texture pattern meets another."""
        result = {
            'primitive': 'detect_texture_boundary',
            'boundary_detected': False,
            'boundary_cells': [],
            'texture_regions': []
        }
        
        if not frame:
            return result
        
        height = len(frame)
        width = len(frame[0]) if frame else 0
        
        # Find cells where local pattern changes
        boundary_cells = []
        
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                # Get 3x3 neighborhood pattern
                center = frame[y][x]
                neighbors = [
                    frame[y-1][x-1], frame[y-1][x], frame[y-1][x+1],
                    frame[y][x-1], frame[y][x+1],
                    frame[y+1][x-1], frame[y+1][x], frame[y+1][x+1]
                ]
                
                # Count color transitions
                transitions = 0
                for i in range(len(neighbors) - 1):
                    if neighbors[i] != neighbors[i + 1]:
                        transitions += 1
                
                # High transitions = boundary
                if transitions > 4:
                    boundary_cells.append((x, y))
        
        result['boundary_cells'] = boundary_cells
        result['boundary_detected'] = len(boundary_cells) > 0
        
        return result
    
    # ==================================================================
    # GAME-SPECIFIC DETECTION IMPLEMENTATIONS
    # ==================================================================
    
    def _detect_pipe_structure(self, frame: List[List[int]]) -> Dict[str, Any]:
        """Identify pipe/channel/conduit layouts for flow games (SP80, VC33)."""
        result = {
            'primitive': 'detect_pipe_structure',
            'has_pipes': False,
            'pipe_cells': [],
            'pipe_color': None,
            'channel_map': {},  # Maps source positions to reachable destinations
            'endpoints': [],    # Open ends where flow can enter/exit
            'junctions': []     # Where pipes branch
        }
        
        if not frame:
            return result
        
        height = len(frame)
        width = len(frame[0]) if frame else 0
        
        # Find potential pipe structures (connected same-color paths)
        # Pipes are typically narrow channels (1-2 cells wide)
        visited = set()
        
        for y in range(height):
            for x in range(width):
                color = frame[y][x]
                if color == 0 or (x, y) in visited:
                    continue
                
                # Check if this looks like a pipe (narrow, elongated)
                # Count same-color neighbors
                neighbors = []
                for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < height and 0 <= nx < width:
                        if frame[ny][nx] == color:
                            neighbors.append((nx, ny))
                
                # Pipe characteristic: 1-2 neighbors in line (not blob)
                if 1 <= len(neighbors) <= 2:
                    result['pipe_cells'].append((x, y))
                    visited.add((x, y))
                    
                    # Endpoint: only 1 neighbor
                    if len(neighbors) == 1:
                        result['endpoints'].append((x, y))
                    
                    if result['pipe_color'] is None:
                        result['pipe_color'] = color
        
        result['has_pipes'] = len(result['pipe_cells']) > 5
        return result
    
    def _detect_valve(self, frame: List[List[int]], frame_history: List[List[List[int]]] = None) -> Dict[str, Any]:
        """Find controllable flow points (valves, gates, switches)."""
        result = {
            'primitive': 'detect_valve',
            'has_valves': False,
            'valve_positions': [],
            'valve_states': {}  # position -> 'open'/'closed'
        }
        
        if not frame:
            return result
        
        height = len(frame)
        width = len(frame[0]) if frame else 0
        
        # Valves are typically single cells that block/allow flow
        # Look for cells that changed between frames (if history available)
        if frame_history and len(frame_history) >= 2:
            prev_frame = frame_history[-2]
            for y in range(height):
                for x in range(width):
                    if frame[y][x] != prev_frame[y][x]:
                        # This cell changed - potential valve/gate
                        result['valve_positions'].append((x, y))
                        # If went from non-zero to zero, valve opened
                        if prev_frame[y][x] != 0 and frame[y][x] == 0:
                            result['valve_states'][(x, y)] = 'opened'
                        elif prev_frame[y][x] == 0 and frame[y][x] != 0:
                            result['valve_states'][(x, y)] = 'closed'
        
        # Also look for isolated single cells that could be toggleable
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                color = frame[y][x]
                if color == 0:
                    continue
                
                # Check if this is a "gate" cell (different from surroundings)
                neighbors = [
                    frame[y-1][x], frame[y+1][x],
                    frame[y][x-1], frame[y][x+1]
                ]
                unique_neighbors = set(neighbors)
                
                # Single cell of one color surrounded by different color(s)
                if color not in unique_neighbors and len(unique_neighbors) <= 2:
                    if (x, y) not in result['valve_positions']:
                        result['valve_positions'].append((x, y))
        
        result['has_valves'] = len(result['valve_positions']) > 0
        return result
    
    def _predict_flow_path(self, frame: List[List[int]], source_position: tuple = None, channel_map: dict = None) -> Dict[str, Any]:
        """Predict where fluid/color will flow next based on channels."""
        result = {
            'primitive': 'predict_flow_path',
            'predicted_path': [],
            'destination': None,
            'blocked': False,
            'flow_direction': None
        }
        
        if not frame or not source_position:
            return result
        
        height = len(frame)
        width = len(frame[0]) if frame else 0
        x, y = source_position
        
        if not (0 <= y < height and 0 <= x < width):
            return result
        
        # Simple flow prediction: follow empty cells or same-color cells
        # Priority: down (gravity), then horizontal spread
        flow_priority = [(1, 0), (0, -1), (0, 1), (-1, 0)]  # down, left, right, up
        
        visited = {(x, y)}
        path = [(x, y)]
        current = (x, y)
        source_color = frame[y][x]
        
        for _ in range(50):  # Max flow distance
            cx, cy = current
            moved = False
            
            for dy, dx in flow_priority:
                ny, nx = cy + dy, cx + dx
                if 0 <= ny < height and 0 <= nx < width:
                    if (nx, ny) not in visited:
                        next_color = frame[ny][nx]
                        # Can flow into empty space or same color
                        if next_color == 0 or next_color == source_color:
                            path.append((nx, ny))
                            visited.add((nx, ny))
                            current = (nx, ny)
                            result['flow_direction'] = ('down' if dy > 0 else 'up' if dy < 0 else 'left' if dx < 0 else 'right')
                            moved = True
                            break
            
            if not moved:
                result['blocked'] = True
                break
        
        result['predicted_path'] = path
        if len(path) > 1:
            result['destination'] = path[-1]
        
        return result
    
    def _detect_pour_target(self, frame: List[List[int]], source_color: int = None, goal_region: List[tuple] = None) -> Dict[str, Any]:
        """Identify where to pour/transfer material to achieve goal (VC33)."""
        result = {
            'primitive': 'detect_pour_target',
            'target_found': False,
            'target_position': None,
            'target_container': [],
            'pour_from': None,
            'confidence': 0.0
        }
        
        if not frame:
            return result
        
        height = len(frame)
        width = len(frame[0]) if frame else 0
        
        # Find containers (enclosed regions that can hold liquid)
        # A container has walls on sides and bottom, open on top
        containers = []
        
        for x in range(1, width - 1):
            for y in range(1, height - 1):
                if frame[y][x] == 0:  # Empty space
                    # Check if this could be inside a container
                    # Need walls on left, right, and bottom
                    has_left_wall = any(frame[cy][x-1] != 0 for cy in range(y, height))
                    has_right_wall = any(frame[cy][x+1] != 0 for cy in range(y, height))
                    has_bottom = y == height - 1 or frame[y+1][x] != 0
                    
                    if has_left_wall and has_right_wall and has_bottom:
                        containers.append((x, y))
        
        if containers:
            result['target_found'] = True
            # Prefer the topmost container position (pour target)
            containers.sort(key=lambda p: p[1])
            result['target_position'] = containers[0]
            result['target_container'] = containers
            result['confidence'] = min(1.0, len(containers) / 5)
        
        return result
    
    def _detect_fitting(self, shape_a: List[tuple], space_b: List[tuple]) -> Dict[str, Any]:
        """Check if shape A fits into space B (puzzle piece fitting for AS66)."""
        result = {
            'primitive': 'detect_fitting',
            'fits': False,
            'rotation_needed': 0,
            'translation': (0, 0),
            'overlap_cells': [],
            'fit_quality': 0.0
        }
        
        if not shape_a or not space_b:
            return result
        
        # Normalize shapes to origin
        def normalize(shape):
            if not shape:
                return []
            min_x = min(p[0] for p in shape)
            min_y = min(p[1] for p in shape)
            return [(p[0] - min_x, p[1] - min_y) for p in shape]
        
        def rotate_90(shape):
            return [(-p[1], p[0]) for p in shape]
        
        norm_a = normalize(shape_a)
        norm_b = set(normalize(space_b))
        
        # Try all rotations
        current = norm_a
        for rotation in range(4):
            norm_current = set(normalize(current))
            
            # Check if shapes match
            if norm_current == norm_b:
                result['fits'] = True
                result['rotation_needed'] = rotation * 90
                result['fit_quality'] = 1.0
                return result
            
            # Check overlap percentage
            overlap = norm_current & norm_b
            if len(overlap) > 0:
                quality = len(overlap) / max(len(norm_current), len(norm_b))
                if quality > result['fit_quality']:
                    result['fit_quality'] = quality
                    result['overlap_cells'] = list(overlap)
                    result['rotation_needed'] = rotation * 90
            
            current = rotate_90(current)
        
        result['fits'] = result['fit_quality'] > 0.8
        return result
    
    def _measure_area(self, frame: List[List[int]], target_color_or_region = None) -> Dict[str, Any]:
        """Measure area of a shape or region in cells."""
        result = {
            'primitive': 'measure_area',
            'area': 0,
            'cells': [],
            'bounding_box': None,
            'density': 0.0  # Area / bounding box area
        }
        
        if not frame:
            return result
        
        height = len(frame)
        width = len(frame[0]) if frame else 0
        
        cells = []
        
        if isinstance(target_color_or_region, int):
            # Count cells of specific color
            color = target_color_or_region
            for y in range(height):
                for x in range(width):
                    if frame[y][x] == color:
                        cells.append((x, y))
        elif isinstance(target_color_or_region, list):
            # Use provided region
            cells = target_color_or_region
        else:
            # Count all non-zero cells
            for y in range(height):
                for x in range(width):
                    if frame[y][x] != 0:
                        cells.append((x, y))
        
        result['area'] = len(cells)
        result['cells'] = cells
        
        if cells:
            min_x = min(p[0] for p in cells)
            max_x = max(p[0] for p in cells)
            min_y = min(p[1] for p in cells)
            max_y = max(p[1] for p in cells)
            result['bounding_box'] = (min_x, min_y, max_x, max_y)
            bb_area = (max_x - min_x + 1) * (max_y - min_y + 1)
            result['density'] = len(cells) / bb_area if bb_area > 0 else 0
        
        return result
    
    def _detect_complementary_shape(self, frame: List[List[int]], shape_color: int = None, background_color: int = 0) -> Dict[str, Any]:
        """Find shape that matches/fills negative space of another (AS66)."""
        result = {
            'primitive': 'detect_complementary_shape',
            'found': False,
            'shape_cells': [],
            'negative_space': [],
            'complementary_cells': [],
            'match_quality': 0.0
        }
        
        if not frame or shape_color is None:
            return result
        
        height = len(frame)
        width = len(frame[0]) if frame else 0
        
        # Find the shape
        shape_cells = []
        for y in range(height):
            for x in range(width):
                if frame[y][x] == shape_color:
                    shape_cells.append((x, y))
        
        result['shape_cells'] = shape_cells
        
        if not shape_cells:
            return result
        
        # Find bounding box
        min_x = min(p[0] for p in shape_cells)
        max_x = max(p[0] for p in shape_cells)
        min_y = min(p[1] for p in shape_cells)
        max_y = max(p[1] for p in shape_cells)
        
        # Negative space = bounding box minus shape
        shape_set = set(shape_cells)
        negative_space = []
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                if (x, y) not in shape_set:
                    negative_space.append((x, y))
        
        result['negative_space'] = negative_space
        
        # Look for another shape that matches negative space
        other_colors = set()
        for y in range(height):
            for x in range(width):
                c = frame[y][x]
                if c != 0 and c != shape_color:
                    other_colors.add(c)
        
        for other_color in other_colors:
            other_cells = [(x, y) for y in range(height) for x in range(width) if frame[y][x] == other_color]
            
            # Normalize and compare
            if len(other_cells) == len(negative_space):
                result['complementary_cells'] = other_cells
                result['found'] = True
                result['match_quality'] = 1.0
                break
        
        return result
    
    def _count_symmetry_axes(self, frame: List[List[int]], region: List[tuple] = None) -> Dict[str, Any]:
        """Count number of symmetry axes in pattern (LP55)."""
        result = {
            'primitive': 'count_symmetry_axes',
            'axes_count': 0,
            'has_horizontal': False,
            'has_vertical': False,
            'has_diagonal': False,
            'symmetry_center': None
        }
        
        if not frame:
            return result
        
        height = len(frame)
        width = len(frame[0]) if frame else 0
        
        # Use region or full frame
        if region:
            cells = set(region)
            min_x = min(p[0] for p in region)
            max_x = max(p[0] for p in region)
            min_y = min(p[1] for p in region)
            max_y = max(p[1] for p in region)
        else:
            cells = set((x, y) for y in range(height) for x in range(width) if frame[y][x] != 0)
            min_x, max_x = 0, width - 1
            min_y, max_y = 0, height - 1
        
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        result['symmetry_center'] = (center_x, center_y)
        
        # Check horizontal symmetry (reflect across horizontal axis)
        h_symmetric = True
        for x, y in cells:
            reflected_y = int(2 * center_y - y)
            if 0 <= reflected_y < height:
                if frame[y][x] != frame[reflected_y][x]:
                    h_symmetric = False
                    break
        
        if h_symmetric:
            result['has_horizontal'] = True
            result['axes_count'] += 1
        
        # Check vertical symmetry
        v_symmetric = True
        for x, y in cells:
            reflected_x = int(2 * center_x - x)
            if 0 <= reflected_x < width:
                if frame[y][x] != frame[y][reflected_x]:
                    v_symmetric = False
                    break
        
        if v_symmetric:
            result['has_vertical'] = True
            result['axes_count'] += 1
        
        return result
    
    def _predict_symmetric_position(self, frame: List[List[int]], existing_positions: List[tuple] = None, symmetry_center: tuple = None) -> Dict[str, Any]:
        """Predict where next element should be to maintain symmetry (LP55)."""
        result = {
            'primitive': 'predict_symmetric_position',
            'predicted_positions': [],
            'symmetry_type': None,
            'confidence': 0.0
        }
        
        if not frame or not existing_positions:
            return result
        
        height = len(frame)
        width = len(frame[0]) if frame else 0
        
        # Determine symmetry center
        if symmetry_center:
            cx, cy = symmetry_center
        else:
            cx = (width - 1) / 2
            cy = (height - 1) / 2
        
        predictions = set()
        
        for x, y in existing_positions:
            # Horizontal reflection
            ry = int(2 * cy - y)
            if 0 <= ry < height and (x, ry) not in existing_positions:
                predictions.add((x, ry))
            
            # Vertical reflection
            rx = int(2 * cx - x)
            if 0 <= rx < width and (rx, y) not in existing_positions:
                predictions.add((rx, y))
            
            # Point reflection (180 degree)
            rx, ry = int(2 * cx - x), int(2 * cy - y)
            if 0 <= rx < width and 0 <= ry < height and (rx, ry) not in existing_positions:
                predictions.add((rx, ry))
        
        result['predicted_positions'] = list(predictions)
        result['confidence'] = 0.8 if predictions else 0.0
        
        return result
    
    def _detect_game_signature(self, frame: List[List[int]]) -> Dict[str, Any]:
        """Analyze frame to determine game type signature for CODS querying."""
        result = {
            'primitive': 'detect_game_signature',
            'signature': {},
            'suggested_game_types': [],
            'features': {}
        }
        
        if not frame:
            return result
        
        height = len(frame)
        width = len(frame[0]) if frame else 0
        
        # Gather features that characterize game types
        features = {
            'frame_size': (width, height),
            'color_count': 0,
            'has_symmetry': False,
            'has_pipes': False,
            'has_containers': False,
            'has_maze': False,
            'has_shapes': False,
            'density': 0.0,
            'dominant_color': None
        }
        
        # Count colors
        color_counts = {}
        non_zero_cells = 0
        for y in range(height):
            for x in range(width):
                c = frame[y][x]
                color_counts[c] = color_counts.get(c, 0) + 1
                if c != 0:
                    non_zero_cells += 1
        
        features['color_count'] = len([c for c in color_counts if c != 0])
        features['density'] = non_zero_cells / (width * height)
        
        if color_counts:
            features['dominant_color'] = max((c for c in color_counts if c != 0), key=lambda c: color_counts.get(c, 0), default=None)
        
        # Check for pipes (narrow channels)
        pipe_result = self._detect_pipe_structure(frame)
        features['has_pipes'] = pipe_result.get('has_pipes', False)
        
        # Check for symmetry
        sym_result = self._count_symmetry_axes(frame)
        features['has_symmetry'] = sym_result.get('axes_count', 0) > 0
        
        # Check for containers (enclosed spaces)
        pour_result = self._detect_pour_target(frame)
        features['has_containers'] = pour_result.get('target_found', False)
        
        # Suggest game types based on features
        suggestions = []
        
        if features['has_pipes']:
            suggestions.append(('SP80', 0.8, 'pipe structures detected'))
            suggestions.append(('VC33', 0.6, 'flow channels present'))
        
        if features['has_containers']:
            suggestions.append(('VC33', 0.9, 'containers for pouring'))
        
        if features['has_symmetry']:
            suggestions.append(('LP55', 0.8, 'symmetric pattern'))
        
        if features['density'] < 0.3 and features['color_count'] <= 3:
            suggestions.append(('LS20', 0.7, 'sparse maze-like'))
        
        if features['color_count'] >= 3 and not features['has_pipes']:
            suggestions.append(('AS66', 0.6, 'multiple colors, shape fitting'))
            suggestions.append(('FT09', 0.5, 'template matching possible'))
        
        # Sort by confidence
        suggestions.sort(key=lambda x: x[1], reverse=True)
        
        result['features'] = features
        result['suggested_game_types'] = suggestions
        result['signature'] = {
            'size': f"{width}x{height}",
            'colors': features['color_count'],
            'density': round(features['density'], 2),
            'has_pipes': features['has_pipes'],
            'has_symmetry': features['has_symmetry'],
            'has_containers': features['has_containers']
        }
        
        return result
    
    def _suggest_primitives_for_game(self, game_signature: Dict[str, Any]) -> Dict[str, Any]:
        """CODS helper: suggest primitives based on game signature."""
        result = {
            'primitive': 'suggest_primitives_for_game',
            'suggested_primitives': [],
            'primitive_chains': [],
            'confidence': 0.0
        }
        
        if not game_signature:
            return result
        
        suggestions = []
        chains = []
        
        features = game_signature.get('features', {})
        sig = game_signature.get('signature', {})
        
        # Always useful primitives
        base_primitives = [
            'detect_objects', 'track_movement', 'detect_novelty',
            'get_confidence', 'detect_stuck'
        ]
        suggestions.extend(base_primitives)
        
        # Pipe/flow games (SP80, VC33)
        if features.get('has_pipes') or sig.get('has_pipes'):
            flow_primitives = [
                'detect_pipe_structure', 'detect_valve', 'predict_flow_path',
                'detect_pour_target', 'detect_flow_source', 'detect_flow_sink',
                'detect_channel', 'measure_flow_rate'
            ]
            suggestions.extend(flow_primitives)
            chains.append({
                'name': 'flow_analysis',
                'primitives': ['detect_pipe_structure', 'detect_valve', 'predict_flow_path'],
                'description': 'Analyze pipe layout, find controls, predict liquid movement'
            })
        
        # Container games (VC33)
        if features.get('has_containers') or sig.get('has_containers'):
            container_primitives = [
                'detect_pour_target', 'measure_area', 'detect_containment',
                'detect_reservoir'
            ]
            suggestions.extend(container_primitives)
            chains.append({
                'name': 'container_fill',
                'primitives': ['detect_pour_target', 'measure_area', 'detect_containment'],
                'description': 'Find containers, measure capacity, track fill level'
            })
        
        # Symmetry games (LP55)
        if features.get('has_symmetry') or sig.get('has_symmetry'):
            sym_primitives = [
                'count_symmetry_axes', 'predict_symmetric_position',
                'detect_reflection', 'detect_rotation_symmetry'
            ]
            suggestions.extend(sym_primitives)
            chains.append({
                'name': 'symmetry_completion',
                'primitives': ['count_symmetry_axes', 'predict_symmetric_position'],
                'description': 'Identify symmetry type, predict missing elements'
            })
        
        # Shape fitting games (AS66)
        if features.get('color_count', 0) >= 3:
            shape_primitives = [
                'detect_fitting', 'detect_complementary_shape', 'measure_area',
                'detect_rotation', 'detect_shape'
            ]
            suggestions.extend(shape_primitives)
            chains.append({
                'name': 'shape_matching',
                'primitives': ['detect_shape', 'detect_fitting', 'detect_complementary_shape'],
                'description': 'Identify shapes, check fitting, find complementary pieces'
            })
        
        # Maze games (LS20)
        if features.get('density', 1.0) < 0.4:
            maze_primitives = [
                'detect_hole', 'adjacent', 'detect_obstacle',
                'is_boundary', 'is_goal'
            ]
            suggestions.extend(maze_primitives)
            chains.append({
                'name': 'maze_navigation',
                'primitives': ['detect_hole', 'adjacent', 'detect_obstacle', 'is_goal'],
                'description': 'Find paths, identify walls, locate goal'
            })
        
        # Remove duplicates while preserving order
        seen = set()
        unique_suggestions = []
        for p in suggestions:
            if p not in seen:
                seen.add(p)
                unique_suggestions.append(p)
        
        result['suggested_primitives'] = unique_suggestions
        result['primitive_chains'] = chains
        result['confidence'] = 0.7 if chains else 0.3
        
        return result
    
    def _chain_primitives(self, primitive_list: List[str], frame: List[List[int]], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Compose multiple primitives into a solution chain."""
        result = {
            'primitive': 'chain_primitives',
            'chain_results': [],
            'final_output': None,
            'success': False,
            'accumulated_context': {}
        }
        
        if not primitive_list or not frame:
            return result
        
        accumulated = context.copy() if context else {}
        accumulated['frame'] = frame
        chain_results = []
        
        for primitive_name in primitive_list:
            primitive = self.get(primitive_name)
            if not primitive:
                chain_results.append({
                    'primitive': primitive_name,
                    'error': f'Primitive not found: {primitive_name}'
                })
                continue
            
            try:
                # Call primitive with accumulated context
                if 'frame' in primitive.input_types:
                    prim_result = primitive(frame)
                else:
                    prim_result = primitive(**{k: v for k, v in accumulated.items() if k in primitive.input_types})
                
                chain_results.append({
                    'primitive': primitive_name,
                    'result': prim_result,
                    'success': True
                })
                
                # Accumulate results for next primitive
                if isinstance(prim_result, dict):
                    accumulated.update(prim_result)
                    
            except Exception as e:
                chain_results.append({
                    'primitive': primitive_name,
                    'error': str(e),
                    'success': False
                })
        
        result['chain_results'] = chain_results
        result['accumulated_context'] = accumulated
        result['final_output'] = chain_results[-1] if chain_results else None
        result['success'] = all(r.get('success', False) for r in chain_results)
        
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
