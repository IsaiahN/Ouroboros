# Cognitive Operator Discovery System (CODS)

**Version**: 1.0  
**Date**: 2025-12-23  
**Purpose**: Self-evolving cognitive vocabulary through compositional primitives and RLVR validation  
**Status**: Implementation Guide

---

## Existing Infrastructure (Already in Codebase)

Before building new primitives, we must leverage what already exists. The codebase has extensive cognitive infrastructure that should be wrapped, not replaced.

### Existing Engines (High-Level Cognitive Systems)

| Engine | File | Purpose | Key Methods |
|--------|------|---------|-------------|
| **VisualReasoningEngine** | `visual_reasoning_engine.py` | Visual semantics from grids | `detect_symmetry()`, `find_repeating_patterns()`, `detect_shapes()`, `analyze_spatial_relations()` |
| **VisualAnalyzer** | `visual_analyzer.py` | Frame analysis for ACTION6 targets | `analyze_frame()`, `find_color_clusters()`, `find_changed_regions()` |
| **ObjectDetector** | `object_detector.py` | Detect distinct objects in frames | `detect_objects_in_frame()`, `_flood_fill()` |
| **SymbolicReasoningEngine** | `symbolic_reasoning_engine.py` | World modeling, goal-directed planning | `parse_scene()`, `evaluate_goals()`, `find_plan()` |
| **AgentSelfModel** | `agent_self_model.py` | "I am this object" tracking | `learn_control_mapping()`, `identify_controlled_objects()` |
| **SensationEngine** | `sensation_engine.py` | Emotional/feeling biases | `get_sensation()`, `update_sensation()` |
| **SequenceAbstraction** | `sequence_abstraction.py` | Pattern matching for sequences | `get_sequence_by_concept()`, `_pattern_similarity()` |
| **CounterfactualAnalyzer** | `counterfactual_analyzer.py` | "What if?" reasoning | `analyze_failure()`, `generate_counterfactuals()` |
| **RuleInductionEngine** | `rule_induction_engine.py` | Extract rules from gameplay | `extract_rule_from_game_session()` |
| **ResonanceDetector** | `resonance_detector.py` | Cross-role pattern agreement | `detect_resonance()` |
| **FrustrationDetector** | `frustration_detector.py` | Detect stuck agents | `detect_frustration()` |
| **NearMissAnalyzer** | `near_miss_analyzer.py` | Almost-win analysis | `analyze_near_miss()` |

### Existing Low-Level Primitives (Already Implemented)

| Primitive | Location | Description |
|-----------|----------|-------------|
| **flood_fill** | `visual_reasoning_engine.py:223`, `object_detector.py:83` | Find connected regions |
| **detect_symmetry** | `visual_reasoning_engine.py:66` | Horizontal, vertical, rotational symmetry |
| **find_repeating_patterns** | `visual_reasoning_engine.py:135` | Detect 2x2, 3x3 repeating motifs |
| **analyze_color_distribution** | `visual_reasoning_engine.py:175` | Color histogram, entropy, sparsity |
| **detect_shapes** | `visual_reasoning_engine.py:212` | Connected component detection with properties |
| **analyze_spatial_relations** | `visual_reasoning_engine.py:281` | Pairwise object relationships |
| **calculate_complexity** | `visual_reasoning_engine.py:389` | Grid complexity metrics |
| **_pattern_similarity** | `sequence_abstraction.py:105` | LCS-based pattern matching |
| **_coords_to_region** | `sequence_abstraction.py:36` | 3x3 region discretization |

### Existing Object Types (from symbolic_reasoning_engine.py)

```python
class ObjectType(Enum):
    AGENT = "agent"           # Controllable object
    GOAL = "goal"             # Target to reach
    OBSTACLE = "obstacle"     # Blocking object
    COLLECTIBLE = "collectible"  # Item to collect
    BUTTON = "button"         # Interactive element
    PORTAL = "portal"         # Teleportation
    MOVABLE = "movable"       # Can be pushed/pulled
    ENEMY = "enemy"           # Harmful object
    KEY = "key"               # Unlocks something
    DOOR = "door"             # Blocking until unlocked
    UNKNOWN = "unknown"       # Unclassified
```

### Existing Data Structures (from symbolic_reasoning_engine.py)

| Structure | Purpose |
|-----------|---------|
| `GameObject` | Object with position, color, size, cells, properties |
| `WorldState` | Complete game state with objects, grid, score, metadata |
| `Goal` | Goal condition (reach, collect, avoid, push_to) |
| `CompositionalGoal` | AND/OR logic for multi-condition goals |

**IMPORTANT**: These existing systems are **reference implementations**, not starting primitives. The CODS system should discover its own patterns first, then the Oracle can recognize "what you discovered is similar to detect_symmetry()" and offer the optimized version.

---

## Core Philosophy: Discovery Learning, Not Rote Learning

### The Gravity Analogy

A child doesn't learn gravity by being told "F = ma". They:
1. Drop things
2. Notice things fall
3. Form a hypothesis ("things go down")
4. Test it (drop more things)
5. Refine it ("heavier things fall same speed - weird!")
6. **THEN** an adult says: "That pattern you discovered is called gravity"

**If we preload the child with "gravity = 9.8 m/s²", they:**
- Know a fact but don't understand it
- Can't discover NEW physics
- Don't know HOW to discover

### Implications for CODS

| Approach | What Happens | Outcome |
|----------|--------------|---------|
| **Preload with primitives** | System uses what we gave it | No emergent discovery, no novel primitives |
| **Minimal primitives + discovery** | System composes, fails, learns | Emergent harmonies, potential novel discoveries |

**The existing engines (VisualReasoningEngine, etc.) are NOT starting primitives.**

They are:
- **Locked primitives** waiting to be unlocked through discovery
- **Optimization targets** unlocked when system proves understanding
- **Human knowledge** that system earns, not receives

---

## The Unlock Mechanism

### Philosophy: Earn to Learn

The system doesn't get handed knowledge. It must **earn** it through verifiable discovery.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PRIMITIVE UNLOCK FLOW                             │
│                                                                       │
│  1. System composes seed primitives                                  │
│  2. System discovers pattern that correlates with success            │
│  3. RLVR validates: pattern actually helps (not coincidence)         │
│  4. Oracle checks: does this match a known primitive?                │
│     ├─ YES → UNLOCK the optimized human version                      │
│     └─ NO  → NOVEL DISCOVERY → add to knowledge base                 │
│  5. System can now use the unlocked/novel primitive in compositions  │
└─────────────────────────────────────────────────────────────────────┘
```

### Three Categories of Primitives

| Category | Status | Examples | How System Gets Access |
|----------|--------|----------|----------------------|
| **Seed** | Always available | `get_pixel`, `add`, `for_each` | Given at birth (can't be discovered) |
| **Locked** | Must be earned | `detect_symmetry`, `flood_fill`, `find_patterns` | Discover similar pattern → unlock |
| **Novel** | System-created | `???` | Discover pattern with no human analog |

### Grandfathered Primitives (Already Earned)

The following primitives are considered **already unlocked** because the user (acting as Oracle) added them based on observed system needs:

| Primitive | Source | Unlock Reason |
|-----------|--------|---------------|
| `detect_symmetry` | `visual_reasoning_engine.py` | Oracle observed system needed this |
| `flood_fill` | `object_detector.py` | Oracle observed system needed this |
| `detect_shapes` | `visual_reasoning_engine.py` | Oracle observed system needed this |
| `find_repeating_patterns` | `visual_reasoning_engine.py` | Oracle observed system needed this |
| `analyze_color_distribution` | `visual_reasoning_engine.py` | Oracle observed system needed this |
| `analyze_spatial_relations` | `visual_reasoning_engine.py` | Oracle observed system needed this |
| `detect_objects_in_frame` | `object_detector.py` | Oracle observed system needed this |
| `parse_scene` | `symbolic_reasoning_engine.py` | Oracle observed system needed this |
| `_pattern_similarity` | `sequence_abstraction.py` | Oracle observed system needed this |

**These are UNLOCKED and available in the primitive library.**

### Locked Primitives (Must Be Earned)

Future primitives that humans know about but system hasn't earned yet:

#### Spatial/Perceptual (Original)
| Primitive | What It Does | Unlock Condition |
|-----------|--------------|------------------|
| `detect_edges` | Find color boundaries | System discovers edge-detection pattern |
| `is_enclosed` | Check if region is bounded | System discovers enclosure pattern |
| `motion_vector` | Track movement direction | System discovers motion tracking |
| `gravity_simulation` | Objects fall down | System discovers gravity-like pattern |
| `count_neighbors` | Count adjacent cells | System discovers neighbor counting |
| `direction_vector` | Direction between points | System discovers directional pattern |

#### Temporal/Predictive
| Primitive | What It Does | Unlock Condition |
|-----------|--------------|------------------|
| `predict_next_state` | Predict most likely next frame given sequence | System builds Markov model over grid transitions |
| `detect_cycles` | Identify repeating state sequences | System discovers periodicity in sequence abstraction |
| `rate_of_change` | Measure velocity of change in region | System correlates frame-to-frame deltas |
| `stability_score` | How stable/unchanging a region is over time | System tracks variance over N frames |

#### Relational/Logical
| Primitive | What It Does | Unlock Condition |
|-----------|--------------|------------------|
| `causal_link` | Test if A precedes B consistently | System discovers temporal correlation patterns |
| `dependency_check` | Test if presence/state of A affects B | System discovers conditional probability pattern |
| `logical_and` | Boolean AND on conditions | System combines primitive outputs with AND logic |
| `logical_or` | Boolean OR on conditions | System combines primitive outputs with OR logic |
| `logical_not` | Boolean NOT on condition | System discovers negation pattern |
| `count_condition` | Count cells/objects satisfying condition | System composes filter + count |

#### Structural/Topological
| Primitive | What It Does | Unlock Condition |
|-----------|--------------|------------------|
| `path_exists` | Check connectivity between points | System discovers flood-fill connectivity |
| `distance_transform` | Distance from each cell to nearest feature | System computes Euclidean distance map |
| `convex_hull` | Find minimal convex boundary | System discovers computational geometry pattern |
| `skeletonize` | Reduce region to 1-pixel wide skeleton | System discovers morphological thinning |

#### Statistical/Probabilistic
| Primitive | What It Does | Unlock Condition |
|-----------|--------------|------------------|
| `entropy_calc` | Information entropy of region | System discovers Shannon entropy on colors/patterns |
| `correlation` | Correlation between two regions/features | System discovers Pearson/Spearman pattern |
| `outlier_detection` | Identify statistically unusual cells/objects | System discovers Z-score or IQR analysis |
| `distribution_fit` | Test if distribution matches pattern | System discovers Chi-square or K-S pattern |

#### Comparative/Analogical
| Primitive | What It Does | Unlock Condition |
|-----------|--------------|------------------|
| `structural_alignment` | Find correspondences between two scenes | System discovers graph matching pattern |
| `analogy_score` | How analogous are two situations | System builds multi-feature similarity metric |
| `transfer_mapping` | Map structures from source to target | System discovers isomorphism detection |

#### Goal-Oriented
| Primitive | What It Does | Unlock Condition |
|-----------|--------------|------------------|
| `goal_distance` | Estimate steps/distance to goal | System discovers heuristic path planning |
| `subgoal_extract` | Extract intermediate objectives | System discovers backward chaining from goal |
| `progress_estimate` | Estimate completion percentage | System discovers current vs. goal comparison |
| `dead_end_detect` | Identify unreachable/blocked states | System discovers connectivity from current state |

#### Meta-Cognitive
| Primitive | What It Does | Unlock Condition |
|-----------|--------------|------------------|
| `uncertainty_estimate` | Measure confidence in detection | System tracks variance across multiple methods |
| `complexity_estimate` | Estimate cognitive load of region | System combines entropy, symmetry, patterns |
| `novelty_score` | How novel/unexpected a pattern is | System compares against known patterns DB |
| `learning_progress` | Rate of improvement on task | System computes slope of performance over trials |

#### Agent-Centric
| Primitive | What It Does | Unlock Condition |
|-----------|--------------|------------------|
| `control_test` | Test if agent can affect region | System simulates actions, checks changes |
| `effect_scope` | Determine what agent's actions affect | System discovers action-consequence correlation |
| `self_location` | Locate agent in frame | System matches against known agent signature |
| `action_impact` | Predict effect of specific action | System builds forward model simulation |

#### Compositional Building Blocks
| Primitive | What It Does | Unlock Condition |
|-----------|--------------|------------------|
| `pipe_output` | Chain primitives automatically | System discovers function composition pattern |
| `conditional_execute` | Execute if condition met | System discovers if-then-else pattern |
| `loop_until` | Repeat until condition satisfied | System discovers while-loop pattern |
| `parallel_execute` | Run multiple primitives simultaneously | System discovers parallel execution pattern |

**Total Locked Primitives: 40+**

**These exist in human knowledge but system can't use them until earned.**

### Novel Primitives (System Discoveries)

When system discovers something Oracle can't match:

```python
{
    "operator_id": "op_347",
    "composition": [...complex composition...],
    "performance": {"level_improvement": 0.31},
    "oracle_response": {
        "recognition": None,
        "confidence": 0.0,
        "known_analog": False,
        "novelty": True,
        "notes": "No known human analog. Appears to detect 'fragmented symmetry' - partial symmetry with controlled breaks."
    }
}
```

This becomes a **novel primitive** that:
1. Gets added to the primitive library
2. Can be used in future compositions
3. Gets documented for human review
4. Might be named by humans later
5. **Might surpass human understanding**

---

## Unlock Verification Process

### Step 1: Pattern Emergence
System discovers operator that helps:
```python
operator_89 = [
    ('for_each_pixel', ...),
    ('get_neighbors', ...),  # Composed from get_pixel calls
    ('count_if', {'predicate': 'same_color'}),
    ('threshold', {'value': 3}),
]
# This operator correlates with level 2+ success in game X
```

### Step 2: RLVR Validation
- Test operator across multiple games
- Require statistically significant improvement
- Minimum N successful uses before unlock consideration

```python
UNLOCK_THRESHOLDS = {
    'min_tests': 50,
    'min_success_rate': 0.60,
    'min_games': 3,  # Must help in at least 3 different games
    'min_level_improvement': 0.10,  # 10% level 2+ improvement
}
```

### Step 3: Oracle Pattern Matching
Oracle compares discovered operator to locked primitives:

```python
def match_to_locked_primitive(operator: Operator) -> Optional[str]:
    """Check if operator matches a locked primitive's behavior."""
    for locked_name, locked_impl in LOCKED_PRIMITIVES.items():
        similarity = compare_behavior(operator, locked_impl)
        if similarity > 0.85:
            return locked_name
    return None  # Novel discovery
```

### Step 4: Unlock or Register Novel

```python
if matched_primitive:
    # UNLOCK: System earned access to optimized human version
    unlock_primitive(matched_primitive)
    log(f"UNLOCKED: {matched_primitive} - system discovered equivalent")
else:
    # NOVEL: System created something new
    register_novel_primitive(operator)
    log(f"NOVEL: {operator.id} - no human analog, added to knowledge base")
```

---

## Remix Engine: From Cobbled to Solid

### The Theory Evolution Pipeline

Primitives aren't born solid - they evolve through testing:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PRIMITIVE LIFECYCLE                                   │
│                                                                          │
│  COBBLED        TESTED         VALIDATED       SOLID          CANONICAL │
│  (random)   →   (works?)   →   (works!)    →   (proven)   →   (named)   │
│                                                                          │
│  ┌──────┐      ┌──────┐       ┌──────┐       ┌──────┐       ┌──────┐   │
│  │remix │  →   │ test │   →   │repeat│   →   │cross │   →   │oracle│   │
│  │spawn │      │ game │       │tests │       │game  │       │match │   │
│  └──────┘      └──────┘       └──────┘       └──────┘       └──────┘   │
│                                                                          │
│  Confidence:  0.0         0.3          0.6         0.8         1.0      │
└─────────────────────────────────────────────────────────────────────────┘
```

### Remix Operations

The system can **remix** existing primitives to spawn new test candidates:

```python
REMIX_OPERATIONS = {
    # Combine two primitives
    'compose': lambda a, b: [a, b],                    # A then B
    'parallel': lambda a, b: (a(), b()),              # A and B simultaneously
    'conditional': lambda cond, a, b: a if cond else b,  # A or B based on condition
    
    # Mutate single primitive
    'parameter_shift': lambda p, delta: p.with_params(p.params + delta),
    'invert': lambda p: not p(),                       # Negate output
    'amplify': lambda p, k: p() * k,                   # Scale output
    'threshold': lambda p, t: p() > t,                 # Binarize output
    
    # Temporal remix
    'delay': lambda p, n: p.at_step(step - n),        # Use past value
    'diff': lambda p: p() - p.at_step(step - 1),      # Rate of change
    'accumulate': lambda p: sum(p.history()),          # Running sum
    
    # Structural remix
    'slice_region': lambda p, region: p.over(region), # Apply to subframe
    'rotate_input': lambda p, angle: p.rotated(angle), # Rotated perception
    'mirror_input': lambda p, axis: p.mirrored(axis),  # Mirrored perception
}
```

### Theory Solidification Process

A "cobbled" primitive becomes a "solid theory" through repeated validation:

```python
class PrimitiveTheory:
    def __init__(self, composition):
        self.composition = composition
        self.confidence = 0.0
        self.test_history = []
        self.games_helped = set()
        self.status = 'cobbled'  # cobbled → tested → validated → solid → canonical
    
    def record_test(self, game_id: str, success: bool, level_improvement: float):
        self.test_history.append({
            'game_id': game_id,
            'success': success,
            'level_improvement': level_improvement,
            'timestamp': now()
        })
        
        if success:
            self.games_helped.add(game_id)
        
        # Update confidence based on test history
        self.confidence = self._calculate_confidence()
        self._update_status()
    
    def _calculate_confidence(self) -> float:
        if len(self.test_history) < 10:
            return 0.0
        
        success_rate = sum(1 for t in self.test_history if t['success']) / len(self.test_history)
        game_diversity = len(self.games_helped) / 10  # Normalize to ~10 games
        avg_improvement = sum(t['level_improvement'] for t in self.test_history) / len(self.test_history)
        
        # Cross-game transfer is heavily weighted
        return (
            success_rate * 0.3 +
            min(game_diversity, 1.0) * 0.4 +  # Cross-game transfer is critical
            min(avg_improvement * 5, 1.0) * 0.3
        )
    
    def _update_status(self):
        if self.confidence >= 0.8 and len(self.games_helped) >= 3:
            self.status = 'solid'
        elif self.confidence >= 0.6:
            self.status = 'validated'
        elif self.confidence >= 0.3:
            self.status = 'tested'
        else:
            self.status = 'cobbled'
```

### Oracle Unlock Decision

When a primitive reaches "solid" status, Oracle checks for unlock:

```python
def oracle_unlock_check(theory: PrimitiveTheory) -> dict:
    """Oracle checks if solid theory matches a locked primitive."""
    
    if theory.status != 'solid':
        return {'action': 'WAIT', 'reason': 'Not yet solid'}
    
    # Check cross-game transfer (critical for unlock)
    if len(theory.games_helped) < 3:
        return {'action': 'WAIT', 'reason': 'Needs more cross-game validation'}
    
    # Try to match against locked primitives
    for locked_name, locked_impl in LOCKED_PRIMITIVES.items():
        similarity = compare_behavior(theory.composition, locked_impl)
        
        if similarity > 0.85:
            return {
                'action': 'UNLOCK_WITH_COMPETITION',
                'matched_primitive': locked_name,
                'similarity': similarity,
                'keep_discovered': True,  # Both compete!
            }
    
    # No match - register as novel
    return {
        'action': 'REGISTER_NOVEL',
        'matched_primitive': None,
        'novelty_score': calculate_novelty(theory),
    }
```

---

## Competition: Discovered vs Human-Refined

### Why Let Them Compete?

When Oracle unlocks a human primitive, **DON'T replace the discovered version**:

| Scenario | Discovered Primitive | Human Primitive | Winner |
|----------|---------------------|-----------------|--------|
| Speed | Cobbled from 5 seed ops | Optimized C code | Human (10x faster) |
| Generalization | Learned from games A,B,C | Designed for general case | Depends! |
| Edge cases | Handles weird case X | Misses weird case X | Discovered |
| Novel context | Adapted to ARC quirks | General purpose | Discovered |

**The discovered version might be BETTER in some contexts because:**
1. It learned from actual gameplay, not theory
2. It might handle ARC-specific edge cases
3. It might have emergent properties the human version lacks
4. It's adapted to the system's internal representation

### Dual-Track Primitive System

```python
class PrimitiveRegistry:
    def __init__(self):
        self.primitives = {}  # name → list of implementations
    
    def register_unlock(self, name: str, discovered: Operator, human_impl: callable):
        """Register both discovered and human versions."""
        self.primitives[name] = {
            'discovered': {
                'impl': discovered,
                'origin': 'system_discovery',
                'performance': discovered.confidence,
                'uses': 0,
                'successes': 0,
            },
            'human': {
                'impl': human_impl,
                'origin': 'human_knowledge',
                'performance': 1.0,  # Assumed optimal initially
                'uses': 0,
                'successes': 0,
            }
        }
    
    def get_primitive(self, name: str, context: dict) -> callable:
        """Select best version based on performance history."""
        if name not in self.primitives:
            return None
        
        versions = self.primitives[name]
        
        # Thompson sampling for exploration/exploitation
        discovered_score = self._thompson_sample(versions['discovered'])
        human_score = self._thompson_sample(versions['human'])
        
        winner = 'discovered' if discovered_score > human_score else 'human'
        return versions[winner]['impl']
    
    def record_outcome(self, name: str, version: str, success: bool):
        """Update performance stats after use."""
        v = self.primitives[name][version]
        v['uses'] += 1
        if success:
            v['successes'] += 1
        v['performance'] = v['successes'] / v['uses'] if v['uses'] > 0 else 0.5
```

### Simplification Pressure: Occam's Razor for Operators

When an operator keeps winning, spawn simplified versions that compete:

```python
class OperatorSimplifier:
    """Spawn simplified versions of winning operators."""
    
    SIMPLIFICATION_THRESHOLD = 100  # Wins before attempting simplification
    MIN_COMPOSITION_LENGTH = 2      # Can't simplify below this
    
    def check_for_simplification(self, operator: Operator) -> list[Operator]:
        """If operator is winning consistently, try to simplify it."""
        
        if operator.wins < self.SIMPLIFICATION_THRESHOLD:
            return []  # Not enough evidence yet
        
        if len(operator.composition) <= self.MIN_COMPOSITION_LENGTH:
            return []  # Already minimal
        
        simplified_variants = []
        
        # Strategy 1: Remove each step one at a time
        for i in range(len(operator.composition)):
            variant = self._remove_step(operator, i)
            if variant:
                simplified_variants.append(variant)
        
        # Strategy 2: Remove consecutive step pairs
        for i in range(len(operator.composition) - 1):
            variant = self._remove_steps(operator, i, i+1)
            if variant:
                simplified_variants.append(variant)
        
        # Strategy 3: Replace sub-compositions with single primitives
        for i in range(len(operator.composition)):
            variant = self._collapse_subcomposition(operator, i)
            if variant:
                simplified_variants.append(variant)
        
        # Strategy 4: Parameter simplification (round to nice numbers)
        variant = self._simplify_parameters(operator)
        if variant:
            simplified_variants.append(variant)
        
        return simplified_variants
    
    def _remove_step(self, operator: Operator, index: int) -> Optional[Operator]:
        """Create variant with one step removed."""
        new_composition = operator.composition[:index] + operator.composition[index+1:]
        return Operator(
            composition=new_composition,
            parent_id=operator.id,
            simplification_of=operator.id,
            simplification_type='step_removal',
            removed_steps=[index],
        )
    
    def _collapse_subcomposition(self, operator: Operator, start: int) -> Optional[Operator]:
        """Try to replace a multi-step pattern with equivalent single primitive."""
        # Look for known patterns that can be collapsed
        # e.g., [get_pixel, get_pixel, equals] -> pixel_equals
        subpattern = operator.composition[start:start+3]
        
        equivalent = find_equivalent_primitive(subpattern)
        if equivalent:
            new_composition = (
                operator.composition[:start] + 
                [equivalent] + 
                operator.composition[start+3:]
            )
            return Operator(
                composition=new_composition,
                parent_id=operator.id,
                simplification_of=operator.id,
                simplification_type='collapse',
            )
        return None
    
    def _simplify_parameters(self, operator: Operator) -> Optional[Operator]:
        """Round parameters to simpler values."""
        new_composition = []
        simplified = False
        
        for step in operator.composition:
            name, params = step
            new_params = {}
            for k, v in params.items():
                if isinstance(v, float):
                    # Round to nearest 0.1
                    rounded = round(v, 1)
                    if rounded != v:
                        simplified = True
                    new_params[k] = rounded
                else:
                    new_params[k] = v
            new_composition.append((name, new_params))
        
        if simplified:
            return Operator(
                composition=new_composition,
                parent_id=operator.id,
                simplification_of=operator.id,
                simplification_type='parameter_simplification',
            )
        return None
```

### Multi-Version Competition

All versions compete in a tournament:

```python
class PrimitiveArena:
    """All versions of a primitive compete for selection."""
    
    def __init__(self, primitive_name: str):
        self.name = primitive_name
        self.versions = {}  # version_id -> VersionStats
    
    def add_version(self, version_id: str, operator: Operator, origin: str):
        """Add a new competing version."""
        self.versions[version_id] = {
            'operator': operator,
            'origin': origin,  # 'discovered', 'human', 'simplified', 'remix'
            'uses': 0,
            'successes': 0,
            'performance': 0.5,
            'complexity': len(operator.composition) if hasattr(operator, 'composition') else 1,
            'parent_version': operator.simplification_of if hasattr(operator, 'simplification_of') else None,
        }
    
    def select_version(self, context: dict) -> str:
        """Select best version using Thompson sampling with complexity penalty."""
        
        scores = {}
        for vid, stats in self.versions.items():
            # Base score from performance
            base_score = self._thompson_sample(stats['successes'], stats['uses'])
            
            # Complexity penalty (prefer simpler operators)
            complexity_penalty = 0.01 * stats['complexity']
            
            # Context bonus (some versions might excel in specific games)
            context_bonus = self._context_affinity(vid, context)
            
            scores[vid] = base_score - complexity_penalty + context_bonus
        
        # Select highest scoring version
        return max(scores, key=scores.get)
    
    def get_competition_summary(self) -> dict:
        """Summary of how all versions are performing."""
        return {
            vid: {
                'origin': stats['origin'],
                'performance': stats['performance'],
                'complexity': stats['complexity'],
                'uses': stats['uses'],
                'rank': None,  # Filled in below
            }
            for vid, stats in self.versions.items()
        }

# Example: After simplification attempts
arena_state = {
    'detect_symmetry': {
        'versions': {
            'human_v1': {'origin': 'human', 'performance': 0.698, 'complexity': 1},
            'discovered_v1': {'origin': 'discovered', 'performance': 0.723, 'complexity': 7},
            'simplified_v1': {'origin': 'simplified', 'performance': 0.718, 'complexity': 5},  # Removed 2 steps, nearly same perf!
            'simplified_v2': {'origin': 'simplified', 'performance': 0.711, 'complexity': 4},  # Even simpler
            'simplified_v3': {'origin': 'simplified', 'performance': 0.452, 'complexity': 3},  # Too simple, broke
        },
        'insight': 'simplified_v2 is the sweet spot: 98% of discovered performance with 43% less complexity'
    }
}
```

### Simplification Insights

When a simplified version matches the original's performance:

```python
def analyze_simplification_success(original: Operator, simplified: Operator) -> dict:
    """Extract insight when simplification preserves performance."""
    
    removed_steps = set(range(len(original.composition))) - set(range(len(simplified.composition)))
    
    return {
        'original_id': original.id,
        'simplified_id': simplified.id,
        'steps_removed': list(removed_steps),
        'removed_operations': [original.composition[i] for i in removed_steps],
        'complexity_reduction': f"{(1 - len(simplified.composition)/len(original.composition))*100:.0f}%",
        'performance_delta': simplified.performance - original.performance,
        'insight': f"Steps {removed_steps} were not essential - possible redundancy or noise",
        'recommendation': 'Consider these steps as optional/context-dependent'
    }
```

### Performance Tracking

Over time, RLVR reveals which version is actually better:

```python
# Example: After 1000 uses each
primitive_stats = {
    'detect_symmetry': {
        'discovered': {'uses': 1000, 'successes': 723, 'performance': 0.723},
        'human': {'uses': 1000, 'successes': 698, 'performance': 0.698},
        # Discovered version is actually better! (learned ARC-specific patterns)
    },
    'flood_fill': {
        'discovered': {'uses': 1000, 'successes': 612, 'performance': 0.612},
        'human': {'uses': 1000, 'successes': 891, 'performance': 0.891},
        # Human version is better (optimized algorithm)
    }
}
```

### Emergent Insights

When discovered version outperforms human:
1. **Log for human review** - What did the system learn that we missed?
2. **Analyze the composition** - Extract the insight
3. **Update human knowledge** - System teaches us

```python
def analyze_superior_discovery(name: str, discovered: Operator, human: callable):
    """When discovered outperforms human, extract the insight."""
    
    # Find where they differ
    test_cases = generate_edge_cases()
    differences = []
    
    for test in test_cases:
        d_result = discovered(test)
        h_result = human(test)
        if d_result != h_result:
            differences.append({
                'input': test,
                'discovered_output': d_result,
                'human_output': h_result,
            })
    
    # Report for human learning
    return {
        'primitive': name,
        'discovered_performance': discovered.performance,
        'human_performance': human.performance,
        'key_differences': differences,
        'hypothesis': f"Discovered version handles {len(differences)} edge cases differently",
        'recommendation': 'Review for potential human knowledge update'
    }
```

---

## Database Schema for Unlock System

```sql
-- Track primitive unlock status
CREATE TABLE IF NOT EXISTS primitive_unlock_status (
    primitive_id TEXT PRIMARY KEY,
    primitive_name TEXT NOT NULL,
    category TEXT NOT NULL,  -- 'seed', 'locked', 'unlocked', 'novel'
    source_implementation TEXT,  -- Reference to human implementation if exists
    
    -- Unlock tracking
    unlock_status TEXT DEFAULT 'locked',  -- 'seed', 'locked', 'unlocked', 'novel'
    unlocked_by_operator TEXT,  -- Operator that earned the unlock
    unlocked_at_generation INTEGER,
    unlock_validation JSON,  -- RLVR stats that justified unlock
    
    -- For novel primitives
    discovered_composition JSON,
    is_novel BOOLEAN DEFAULT FALSE,
    human_name TEXT,  -- Assigned later by oracle/human
    
    -- Usage tracking
    times_used INTEGER DEFAULT 0,
    last_used_generation INTEGER
);

-- Track unlock attempts (for learning)
CREATE TABLE IF NOT EXISTS unlock_attempts (
    attempt_id TEXT PRIMARY KEY,
    operator_id TEXT NOT NULL,
    target_primitive TEXT,  -- NULL if novel
    generation INTEGER,
    
    -- Validation metrics at time of attempt
    tests_passed INTEGER,
    success_rate REAL,
    games_helped INTEGER,
    level_improvement REAL,
    
    -- Outcome
    outcome TEXT,  -- 'unlocked', 'novel', 'rejected'
    rejection_reason TEXT,  -- If rejected, why?
    
    attempt_timestamp TEXT
);

-- Track primitive theories as they solidify
CREATE TABLE IF NOT EXISTS primitive_theories (
    theory_id TEXT PRIMARY KEY,
    composition JSON NOT NULL,  -- The composed operators
    composition_hash TEXT NOT NULL,  -- For deduplication
    
    -- Theory status lifecycle
    status TEXT DEFAULT 'cobbled',  -- cobbled, tested, validated, solid, canonical
    confidence REAL DEFAULT 0.0,
    
    -- Testing history
    total_tests INTEGER DEFAULT 0,
    successful_tests INTEGER DEFAULT 0,
    games_tested TEXT,  -- JSON array of game_ids
    games_helped TEXT,  -- JSON array of game_ids where it actually helped
    avg_level_improvement REAL DEFAULT 0.0,
    
    -- Cross-game transfer (critical for unlock)
    cross_game_transfer_score REAL DEFAULT 0.0,
    
    -- Lifecycle tracking
    created_generation INTEGER,
    last_tested_generation INTEGER,
    solidified_at_generation INTEGER,
    
    -- If matched to locked primitive
    matched_primitive TEXT,  -- NULL until matched
    unlock_triggered BOOLEAN DEFAULT FALSE
);

-- Track competition between discovered and human primitives
CREATE TABLE IF NOT EXISTS primitive_competition (
    primitive_name TEXT NOT NULL,
    version TEXT NOT NULL,  -- 'discovered' or 'human'
    
    -- Performance tracking
    total_uses INTEGER DEFAULT 0,
    successful_uses INTEGER DEFAULT 0,
    performance_score REAL DEFAULT 0.5,
    
    -- Context-specific performance
    games_used TEXT,  -- JSON array
    best_game TEXT,  -- Game where this version excels
    worst_game TEXT,  -- Game where this version struggles
    
    -- Comparison stats
    head_to_head_wins INTEGER DEFAULT 0,  -- When both tested on same input
    
    PRIMARY KEY (primitive_name, version)
);

-- Track when discovered outperforms human (learning opportunity)
CREATE TABLE IF NOT EXISTS discovery_insights (
    insight_id TEXT PRIMARY KEY,
    primitive_name TEXT NOT NULL,
    
    -- Performance comparison
    discovered_performance REAL,
    human_performance REAL,
    performance_delta REAL,  -- discovered - human
    
    -- Edge case analysis
    edge_cases_found INTEGER,
    edge_case_examples JSON,  -- Sample inputs where they differ
    
    -- Human learning
    hypothesis TEXT,
    reviewed_by_human BOOLEAN DEFAULT FALSE,
    human_knowledge_updated BOOLEAN DEFAULT FALSE,
    
    discovered_at TEXT
);

-- Track remix operations that spawned theories
CREATE TABLE IF NOT EXISTS remix_history (
    remix_id TEXT PRIMARY KEY,
    parent_a TEXT,  -- First parent primitive/operator
    parent_b TEXT,  -- Second parent (NULL for mutations)
    remix_operation TEXT,  -- 'compose', 'mutate', 'crossover', etc.
    
    -- Result
    child_theory_id TEXT,
    child_viable BOOLEAN,  -- Did it survive initial testing?
    
    -- Genealogy tracking
    generation INTEGER,
    created_at TEXT
);

-- Track simplification attempts and their outcomes
CREATE TABLE IF NOT EXISTS simplification_attempts (
    simplification_id TEXT PRIMARY KEY,
    original_operator_id TEXT NOT NULL,
    simplified_operator_id TEXT NOT NULL,
    
    -- Simplification details
    simplification_type TEXT,  -- 'step_removal', 'collapse', 'parameter_simplification'
    steps_removed TEXT,  -- JSON array of removed step indices
    original_complexity INTEGER,
    simplified_complexity INTEGER,
    complexity_reduction REAL,  -- Percentage reduction
    
    -- Performance comparison
    original_performance REAL,
    simplified_performance REAL,
    performance_delta REAL,  -- simplified - original
    performance_preserved BOOLEAN,  -- Did simplification maintain performance?
    
    -- Outcome
    outcome TEXT,  -- 'success' (same perf, less complex), 'degraded', 'improved' (rare but possible)
    is_new_champion BOOLEAN DEFAULT FALSE,  -- Did simplified version become the best?
    
    -- Tracking
    generation INTEGER,
    created_at TEXT
);

-- Track multi-version arena competition
CREATE TABLE IF NOT EXISTS primitive_arena (
    arena_id TEXT PRIMARY KEY,
    primitive_name TEXT NOT NULL,
    
    -- All competing versions
    versions JSON,  -- Array of version_ids with their stats
    
    -- Current champion
    champion_version TEXT,
    champion_origin TEXT,  -- 'discovered', 'human', 'simplified', 'remix'
    champion_since_generation INTEGER,
    
    -- Arena stats
    total_selections INTEGER DEFAULT 0,
    last_competition_generation INTEGER,
    
    -- Insights
    best_by_context JSON  -- {game_id: best_version} mapping
);
```

---

## Design Principle: Minimal Seed, Maximum Discovery

### What the System Starts With (Absolute Minimum)

Only primitives that are **impossible to discover** - raw data access and foundational computation:

```python
SEED_PRIMITIVES = {
    # ═══════════════════════════════════════════════════════════════════
    # RAW DATA ACCESS (can't be discovered, must be given)
    # ═══════════════════════════════════════════════════════════════════
    'get_pixel': lambda frame, x, y: frame[y][x],
    'get_frame_size': lambda frame: (len(frame), len(frame[0])),
    'get_frame': lambda context: context['frame'],
    'get_previous_frame': lambda context: context.get('previous_frame'),
    
    # ═══════════════════════════════════════════════════════════════════
    # BASIC MATH (universal, not domain-specific)
    # ═══════════════════════════════════════════════════════════════════
    'add': lambda a, b: a + b,
    'subtract': lambda a, b: a - b,
    'multiply': lambda a, b: a * b,
    'divide': lambda a, b: a / b if b != 0 else 0,
    'modulo': lambda a, b: a % b if b != 0 else 0,
    'abs': lambda a: abs(a),
    'equals': lambda a, b: a == b,
    'not_equals': lambda a, b: a != b,
    'greater_than': lambda a, b: a > b,
    'less_than': lambda a, b: a < b,
    'greater_or_equal': lambda a, b: a >= b,
    'less_or_equal': lambda a, b: a <= b,
    
    # ═══════════════════════════════════════════════════════════════════
    # CONTROL FLOW (essential for clean composition, not domain knowledge)
    # ═══════════════════════════════════════════════════════════════════
    'if_else': lambda cond, a, b: a if cond else b,  # Branching primitive
    'select': lambda cond, a, b: a if cond else b,   # Alias for if_else
    
    # ═══════════════════════════════════════════════════════════════════
    # BASIC DATA STRUCTURES (for building intermediate artifacts)
    # ═══════════════════════════════════════════════════════════════════
    'make_list': lambda: [],
    'append': lambda lst, item: lst + [item],  # Immutable append
    'len': lambda lst: len(lst) if hasattr(lst, '__len__') else 0,
    'get_at': lambda lst, i: lst[i] if 0 <= i < len(lst) else None,  # Bounds-safe
    'set_at': lambda lst, i, v: [v if j == i else x for j, x in enumerate(lst)],  # Immutable set
    'slice': lambda lst, start, end: lst[start:end],
    'concat': lambda a, b: a + b,  # Concatenate lists
    'contains': lambda lst, item: item in lst,
    'index_of': lambda lst, item: lst.index(item) if item in lst else -1,
    'unique': lambda lst: list(set(lst)),
    
    # ═══════════════════════════════════════════════════════════════════
    # BASIC ITERATION (can't discover loops without loops)
    # ═══════════════════════════════════════════════════════════════════
    'for_each_pixel': lambda frame, func: [[func(x, y, frame[y][x]) for x in range(len(frame[0]))] for y in range(len(frame))],
    'for_range': lambda start, end, func: [func(i) for i in range(start, end)],
    'map': lambda lst, func: [func(x) for x in lst],
    'filter': lambda lst, pred: [x for x in lst if pred(x)],
    'reduce': lambda lst, func, init: functools.reduce(func, lst, init),
    'count_if': lambda frame, predicate: sum(1 for row in frame for pixel in row if predicate(pixel)),
    'any': lambda lst, pred: any(pred(x) for x in lst),
    'all': lambda lst, pred: all(pred(x) for x in lst),
    
    # ═══════════════════════════════════════════════════════════════════
    # BASIC AGGREGATION
    # ═══════════════════════════════════════════════════════════════════
    'sum': lambda values: sum(values),
    'max': lambda values: max(values) if values else None,
    'min': lambda values: min(values) if values else None,
    'average': lambda values: sum(values) / len(values) if values else 0,
    'median': lambda values: sorted(values)[len(values)//2] if values else None,
    
    # ═══════════════════════════════════════════════════════════════════
    # TIME + EPISODE IDENTITY (for temporal learning without hidden privileges)
    # ═══════════════════════════════════════════════════════════════════
    'get_step_index': lambda context: context.get('step_index', 0),
    'get_episode_id': lambda context: context.get('episode_id', ''),
    'get_action_count': lambda context: context.get('action_count', 0),
    
    # ═══════════════════════════════════════════════════════════════════
    # ACTION/CHANNEL INTROSPECTION (sensor input, not strategy)
    # ═══════════════════════════════════════════════════════════════════
    'get_action_space': lambda context: context.get('action_space', []),
    'get_last_action': lambda context: context.get('last_action'),
    'get_action_history': lambda context, k: context.get('action_history', [])[-k:],
    'get_score': lambda context: context.get('score', 0),
    'get_level': lambda context: context.get('level', 0),
    
    # ═══════════════════════════════════════════════════════════════════
    # RNG AS EXPLICIT PRIMITIVE (for reproducibility and audit)
    # ═══════════════════════════════════════════════════════════════════
    'rand': lambda: random.random(),
    'rand_int': lambda low, high: random.randint(low, high),
    'rand_choice': lambda lst: random.choice(lst) if lst else None,
    'seed_rng': lambda seed: random.seed(seed),  # For reproducibility
    
    # ═══════════════════════════════════════════════════════════════════
    # DETERMINISTIC HASHING (for caching, novelty tracking, deduplication)
    # ═══════════════════════════════════════════════════════════════════
    'hash': lambda value: hash(str(value)),  # Stable within run
    'hash_frame': lambda frame: hash(tuple(tuple(row) for row in frame)),
    'signature': lambda *args: hash(str(args)),  # Multi-value signature
}
```

**Seed primitives expanded to ~50 to enable clean composition.**

These are all **foundational computation** - none inject domain knowledge:
- Control flow (`if_else`) lets operators branch cleanly
- Data structures (`make_list`, `append`) let operators build intermediate artifacts
- Time identity (`get_step_index`) enables temporal learning without side channels
- Action introspection (`get_action_space`, `get_last_action`) is sensor input
- RNG (`rand`) makes stochasticity auditable
- Hashing (`hash`) enables deduplication and novelty tracking

Everything else - symmetry, flood_fill, patterns, shapes - must be **DISCOVERED** by composing these.

### What the System Discovers (Examples)

The system might compose:
```python
# System discovers this pattern works
operator_47 = [
    ('for_each_pixel', {'func': 'get_pixel'}),
    ('count_if', {'predicate': 'equals(pixel, 3)'}),  # Count color 3
]
# This is essentially count_color(frame, 3) - but discovered, not given
```

Or more complex:
```python
# System discovers this helps level 2+
operator_183 = [
    ('get_frame_size', {}),
    ('divide', {'a': 'width', 'b': 2}),
    ('for_range', {'start': 0, 'end': 'half_width'}),
    ('get_pixel', {'x': 'i', 'y': 'j'}),
    ('get_pixel', {'x': 'width - 1 - i', 'y': 'j'}),
    ('equals', {}),
    ('count_if', {'predicate': 'result'}),
    ('divide', {'a': 'count', 'b': 'total_pixels'}),
    ('greater_than', {'b': 0.9}),
]
# Oracle recognizes: "This is vertical symmetry detection!"
```

### The Oracle's Role (Unlock Gatekeeper)

The Oracle does NOT inject knowledge. It:

1. **Validates** that the system genuinely discovered the pattern (not random luck)
2. **Matches** to locked primitives (if match found → UNLOCK)
3. **Registers novelty** (if no match → add to knowledge base)
4. **Offers optimized implementation** (system can accept or reject)

```python
# Oracle response to operator_183 - UNLOCK CASE
{
    "action": "UNLOCK",
    "matched_primitive": "vertical_symmetry",
    "validation": {
        "tests_passed": 67,
        "success_rate": 0.73,
        "games_helped": 4,
        "level_improvement": 0.19
    },
    "unlock_details": {
        "primitive_name": "detect_vertical_symmetry",
        "source": "visual_reasoning_engine.detect_symmetry()",
        "performance_gain": "~10x faster than composed version",
        "now_available": True
    },
    "message": "System earned access to detect_vertical_symmetry through verifiable discovery."
}
```

Or for something truly novel:
```python
# Oracle response to operator_347 - NOVEL CASE
{
    "action": "REGISTER_NOVEL",
    "matched_primitive": None,
    "validation": {
        "tests_passed": 52,
        "success_rate": 0.68,
        "games_helped": 3,
        "level_improvement": 0.24
    },
    "novel_details": {
        "temporary_id": "novel_primitive_347",
        "awaiting_human_name": True,
        "composition_hash": "a7f3c2...",
        "description_attempt": "Detects regions where symmetry is 'broken' by exactly one cell"
    },
    "message": "Novel discovery! No human analog found. Added to knowledge base for potential human naming."
}
```

### Mutation and Combination

Once primitives are unlocked (or novel ones registered), the system can:

1. **Compose with unlocked primitives** - Use `detect_symmetry` as a building block
2. **Mutate primitives** - Create variations of known patterns
3. **Combine unlocked + novel** - Mix human knowledge with system discoveries

```python
# Example: System combines unlocked + novel
operator_512 = [
    ('detect_vertical_symmetry', {}),  # UNLOCKED primitive
    ('novel_primitive_347', {}),        # NOVEL discovery (broken symmetry)
    ('and', {}),                        # Both must be true
]
# Result: "Symmetric but with intentional break" - possibly useful for puzzles!
```

---

## Emergent Harmonies

### Why Minimal Seeding Enables Emergence

When the system composes primitives freely, unexpected combinations emerge:

| What System Composes | What It Discovers | Unlock Status |
|---------------------|-------------------|---------------|
| `count_if(pixel == X) / total > 0.5` | "Dominant color detection" | → UNLOCK `dominant_color` |
| `for_each + equals(left, right_flipped)` | "Symmetry" | → UNLOCK `detect_symmetry` |
| `diff(frame_t, frame_t-1) + count_if` | "Motion detection" | → UNLOCK `motion_vector` |
| `cluster(colors) + centroid` | "Object center finding" | → UNLOCK `center_of_mass` |
| `??? + ??? + ???` | **NOVEL** | → REGISTER as novel primitive |

The last row is the goal. Novel discoveries might surpass human understanding.

### Harmonic Combinations

Operators can compose with OTHER operators (not just primitives):

```
Operator A: "Find symmetric regions"
Operator B: "Find changed pixels"
Operator C = A + B: "Find where symmetry broke" (novel!)
```

This emergent combination might discover:
- "The agent broke the symmetry" → self-model insight
- "Symmetry-breaking correlates with score increase" → strategy insight
- Something humans never thought of

---

## Updated Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SEED PRIMITIVES (Minimal)                         │
│                                                                       │
│  get_pixel, get_frame, basic math, iteration, aggregation           │
│  ~15-20 primitives - just enough to compose anything                │
│  CANNOT be discovered (raw data access)                              │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    OPERATOR COMPOSER (Discovery Engine)              │
│                                                                       │
│  Composes seed primitives into operators                             │
│  Composes operators into higher-order operators                      │
│  Tests with RLVR - promotes what works                               │
│  NO KNOWLEDGE OF WHAT "SHOULD" WORK                                  │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ORACLE (Post-Discovery Interpreter)               │
│                                                                       │
│  Observes what system discovered                                     │
│  Recognizes: "This is similar to human concept X"                    │
│  Names: Gives human-readable label                                   │
│  Offers (optional): "Here's an optimized version"                    │
│  Flags novelty: "This doesn't match any known pattern"              │
│  NEVER INJECTS - ONLY INTERPRETS                                    │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    EXISTING ENGINES (Reference Library)              │
│                                                                       │
│  VisualReasoningEngine, ObjectDetector, SymbolicReasoningEngine...   │
│  NOT used for seeding - used for:                                    │
│    - Oracle pattern matching ("this looks like detect_symmetry")     │
│    - Optimization offers ("use this faster implementation")          │
│    - Validation ("your operator matches known-good implementation")  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## What This Enables

1. **True Discovery**: System learns HOW to learn, not just WHAT to learn
2. **Novel Primitives**: Can discover things humans haven't formalized
3. **Emergent Harmonies**: Unexpected operator combinations
4. **Deep Understanding**: System understands primitives because it built them
5. **Transfer Learning**: Discovered primitives might transfer to non-ARC domains
6. **Human Learning**: We learn from what the system discovers

---

## Overview

The Cognitive Operator Discovery System enables Ouroboros to **evolve its own cognitive vocabulary** by:
1. Composing low-level primitives into higher-level operators
2. Testing operators with RLVR (real game performance)
3. Promoting/decaying operators based on effectiveness
4. Querying an Oracle for interpretation (human/LLM/automated - system doesn't know or care)

### The Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    COGNITIVE PRIMITIVES LIBRARY                      │
│                                                                       │
│  Low-level operations on frames: split, compare, transform, count   │
│  Domain-agnostic, composable, measurable                            │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    OPERATOR COMPOSER                                 │
│                                                                       │
│  Combines primitives into operators (compositions)                   │
│  Evolutionary search over composition space                          │
│  Tests operators against stuck games with RLVR                       │
│  Promotes what works, decays what doesn't                            │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ORACLE INTERFACE                                  │
│                                                                       │
│  Queries for interpretation (system-agnostic)                        │
│  Receives optimizations from external knowledge                      │
│  Handles admin directives as environmental signals                   │
│  System doesn't know what's behind the Oracle                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Core Principles

### 1. Oracle-Agnostic Design
The system queries an Oracle but doesn't know or care if it's:
- Human reviewing reports
- LLM interpreting compositions
- Automated knowledge matcher
- Any combination

The Oracle is just an API. Today it's you + me. Tomorrow it could be fully automated.

### 2. RLVR as Sole Validator
Operators are judged **only** by real game performance:
- Does this operator help level 2+ completion?
- Does it reduce action count?
- Does it transfer to other games?

No operator survives based on "looking good" - only empirical results.

### 3. Anti-Goodhart Protections
Per the RLVR safety framework:
- Operators get pre-allocated testing budgets (not earned)
- Success in Game A doesn't buy priority in Game B
- Failed operators decay, don't permanently stigmatize
- Forced novelty quotas (must test N new compositions per M generations)

---

## Database Schema Additions

```sql
-- Cognitive primitives library (static, admin-managed)
CREATE TABLE IF NOT EXISTS cognitive_primitives (
    primitive_id TEXT PRIMARY KEY,
    primitive_name TEXT NOT NULL,
    category TEXT NOT NULL,  -- 'spatial', 'color', 'topology', 'geometry', 'temporal', 'relational'
    description TEXT,
    input_spec JSON,         -- Expected inputs
    output_spec JSON,        -- What it returns
    implementation_ref TEXT, -- Function reference in cognitive_primitives.py
    is_active BOOLEAN DEFAULT TRUE,
    added_generation INTEGER
);

-- Discovered operators (compositions of primitives)
CREATE TABLE IF NOT EXISTS discovered_operators (
    operator_id TEXT PRIMARY KEY,
    composition JSON NOT NULL,       -- Array of {primitive_id, args}
    discovery_generation INTEGER,
    discovered_by_agent TEXT,        -- Agent that first used this successfully
    
    -- Performance metrics (RLVR results)
    games_tested JSON,               -- Array of game_ids
    total_tests INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    level_improvement REAL DEFAULT 0.0,
    action_efficiency REAL DEFAULT 1.0,
    transfer_score REAL DEFAULT 0.0, -- How well it transfers to other games
    
    -- Lifecycle
    status TEXT DEFAULT 'TESTING',   -- TESTING, VALIDATED, PROMOTED, DECAYED, RETIRED
    is_active BOOLEAN DEFAULT TRUE,
    activation_count INTEGER DEFAULT 0,
    last_used_generation INTEGER,
    decay_score REAL DEFAULT 0.0,
    
    -- Oracle interpretation (filled asynchronously)
    interpretation_status TEXT DEFAULT 'PENDING',  -- PENDING, QUERIED, ANSWERED, VALIDATED
    oracle_query_id TEXT,
    interpretation TEXT,
    known_analog BOOLEAN,
    optimized_composition JSON,
    novelty_flag BOOLEAN DEFAULT FALSE,
    
    FOREIGN KEY (oracle_query_id) REFERENCES oracle_queries(query_id)
);

-- Oracle queries (system-generated, oracle-answered)
CREATE TABLE IF NOT EXISTS oracle_queries (
    query_id TEXT PRIMARY KEY,
    query_type TEXT NOT NULL,        -- 'interpret', 'optimize', 'validate_novelty', 'guidance'
    target_operator_id TEXT,
    query_data JSON NOT NULL,
    priority TEXT DEFAULT 'normal',  -- 'low', 'normal', 'high', 'critical'
    
    -- Query lifecycle
    created_generation INTEGER,
    created_timestamp TEXT,
    status TEXT DEFAULT 'PENDING',   -- PENDING, ANSWERED, TIMEOUT, CANCELLED
    
    -- Response (filled by oracle - human/LLM/automated)
    response_data JSON,
    response_timestamp TEXT,
    responder_id TEXT DEFAULT 'oracle',  -- System doesn't interpret this
    
    FOREIGN KEY (target_operator_id) REFERENCES discovered_operators(operator_id)
);

-- Admin directives (environmental signals)
CREATE TABLE IF NOT EXISTS admin_directives (
    directive_id TEXT PRIMARY KEY,
    directive_type TEXT NOT NULL,    -- 'focus', 'pause', 'inject', 'retire', 'boost', 'guide'
    target TEXT,                     -- operator_id, primitive_id, game_type, or 'global'
    directive_data JSON,
    priority INTEGER DEFAULT 5,      -- 1-10, higher = more urgent
    
    -- Lifecycle
    issued_timestamp TEXT,
    expires_timestamp TEXT,          -- NULL = never expires
    executed BOOLEAN DEFAULT FALSE,
    executed_timestamp TEXT,
    execution_result JSON
);

-- Operator test results (detailed RLVR logs)
CREATE TABLE IF NOT EXISTS operator_test_results (
    test_id TEXT PRIMARY KEY,
    operator_id TEXT NOT NULL,
    game_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    generation INTEGER,
    
    -- Test conditions
    level_before INTEGER,
    score_before REAL,
    
    -- Results
    level_after INTEGER,
    score_after REAL,
    actions_used INTEGER,
    operator_fired BOOLEAN,          -- Did the operator's condition trigger?
    operator_influenced_action BOOLEAN,  -- Did firing change the action taken?
    
    -- Outcome
    success BOOLEAN,                 -- Did level improve?
    improvement_delta REAL,
    
    test_timestamp TEXT,
    
    FOREIGN KEY (operator_id) REFERENCES discovered_operators(operator_id)
);

-- Indices for performance
CREATE INDEX IF NOT EXISTS idx_operators_status ON discovered_operators(status, is_active);
CREATE INDEX IF NOT EXISTS idx_operators_performance ON discovered_operators(level_improvement DESC);
CREATE INDEX IF NOT EXISTS idx_oracle_pending ON oracle_queries(status) WHERE status = 'PENDING';
CREATE INDEX IF NOT EXISTS idx_directives_pending ON admin_directives(executed) WHERE executed = FALSE;
CREATE INDEX IF NOT EXISTS idx_test_results_operator ON operator_test_results(operator_id, generation);
```

---

## Module Specifications

### 1. cognitive_primitives.py

**Purpose**: Minimal seed primitives for composition + discovery

**Design Philosophy**: 
- **Seed primitives**: Only what CANNOT be discovered (raw data access, basic math)
- **Discovered primitives**: Everything else emerges through composition
- **Reference library**: Existing engines used for Oracle pattern-matching, NOT for seeding

### Seed Primitives (The Only Starting Vocabulary)

These are primitives the system CANNOT discover - they provide raw access to data:

| Category | Primitive | Description | Why It Can't Be Discovered |
|----------|-----------|-------------|---------------------------|
| **Data Access** | `get_pixel` | Get value at (x, y) | Fundamental data access |
| **Data Access** | `get_frame` | Get current frame | Fundamental data access |
| **Data Access** | `get_frame_size` | Get (height, width) | Fundamental data access |
| **Data Access** | `get_previous_frame` | Get frame from t-1 | Fundamental data access |
| **Data Access** | `get_score` | Get current score | Fundamental data access |
| **Math** | `add`, `subtract`, `multiply`, `divide` | Basic arithmetic | Universal, not domain-specific |
| **Math** | `equals`, `greater_than`, `less_than` | Comparisons | Universal, not domain-specific |
| **Math** | `and`, `or`, `not` | Boolean logic | Universal, not domain-specific |
| **Iteration** | `for_each_pixel` | Iterate over all pixels | Can't discover loops without loops |
| **Iteration** | `for_range` | Iterate over range | Can't discover loops without loops |
| **Aggregation** | `count_if` | Count matching elements | Basic building block |
| **Aggregation** | `sum`, `max`, `min`, `average` | Basic aggregation | Basic building blocks |
| **Collection** | `filter` | Keep matching elements | Basic building block |
| **Collection** | `map` | Transform each element | Basic building block |
| **Storage** | `store` | Save value to context | Memory access |
| **Storage** | `retrieve` | Get value from context | Memory access |

**Total: ~20 seed primitives**

### What the System Will Discover (Not Pre-Loaded)

These are patterns that SHOULD emerge from composition:

| Pattern | How System Might Discover It | Human Name (Oracle Provides Later) |
|---------|------------------------------|-----------------------------------|
| `for_each_pixel + count_if(color == X)` | Notices counting colors helps | "count_color" |
| `for_range(0, width/2) + compare(left, right_flipped)` | Notices left-right matching helps | "vertical_symmetry" |
| `for_each_pixel + if(neighbors_differ) + count` | Notices edge pixels matter | "detect_edges" |
| `for_each_pixel + cluster(same_color_adjacent)` | Notices grouping helps | "flood_fill" |
| `get_frame - get_previous_frame` | Notices change detection helps | "diff" |
| `cluster + centroid` | Notices object centers matter | "center_of_mass" |
| `??? + ??? + ???` | Novel combination | **NOVEL - NO HUMAN NAME** |

### Reference Library (For Oracle Pattern-Matching Only)

These exist in the codebase but are NOT exposed to the system as primitives:

| Engine | Purpose in CODS |
|--------|-----------------|
| `VisualReasoningEngine.detect_symmetry()` | Oracle recognizes "your operator is doing symmetry detection" |
| `ObjectDetector.detect_objects_in_frame()` | Oracle recognizes "your operator is doing object detection" |
| `SequenceAbstraction._pattern_similarity()` | Oracle recognizes "your operator is doing pattern matching" |

The system never calls these directly. The Oracle uses them to **interpret** what the system discovered.

### Class Interface

```python
class SeedPrimitives:
    """Minimal primitives the system starts with."""
    
    def execute(self, primitive_name: str, args: dict, context: dict) -> Any:
        """Execute a seed primitive."""
        
    def list_primitives(self) -> List[str]:
        """List all available seed primitives (~20)."""
        
    def get_spec(self, primitive_name: str) -> dict:
        """Get input/output specification for a primitive."""


class DiscoveredPrimitiveRegistry:
    """Registry of primitives the system has discovered through composition."""
    
    def register(self, operator: Operator, name: Optional[str] = None) -> str:
        """Register a discovered operator as a reusable primitive."""
        
    def get(self, primitive_id: str) -> Operator:
        """Get a discovered primitive by ID."""
        
    def promote_to_primitive(self, operator_id: str) -> str:
        """Promote a successful operator to primitive status (composable by other operators)."""
```

### 2. operator_composer.py

**Purpose**: Combine primitives into operators, evolve compositions, test with RLVR

**Key Classes**:

```python
class Operator:
    """A composition of primitives that produces a decision signal."""
    operator_id: str
    composition: List[dict]  # [{primitive_id, args}, ...]
    
    def execute(self, context: dict) -> OperatorResult
    def mutate(self) -> 'Operator'
    def crossover(self, other: 'Operator') -> 'Operator'

class OperatorComposer:
    """Manages operator lifecycle: creation, testing, promotion, decay."""
    
    def generate_random_operator(self, max_depth: int = 5) -> Operator
    def test_operator(self, operator: Operator, game_context: dict) -> TestResult
    def evolve_operators(self, generation: int, population_size: int = 20)
    def promote_successful(self, threshold: float = 0.15)
    def decay_unused(self, generations_threshold: int = 10)
    def get_active_operators(self, game_type: Optional[str] = None) -> List[Operator]

class OperatorIntegration:
    """Integrates operators into gameplay decision-making."""
    
    def evaluate_operators(self, frame: np.ndarray, context: dict) -> List[OperatorSignal]
    def apply_operator_biases(self, action_weights: dict, signals: List[OperatorSignal]) -> dict
```

**Evolution Strategy**:
1. Each generation, allocate N test slots to operators
2. Randomly generate new operators (forced novelty quota)
3. Mutate/crossover existing operators
4. Test all in RLVR conditions
5. Promote high performers, decay low performers
6. Query Oracle for top performers interpretation

### 3. oracle_interface.py

**Purpose**: Oracle-agnostic API for interpretation and directives

**Key Classes**:

```python
class OracleInterface:
    """System-facing interface to the Oracle. System doesn't know what's behind it."""
    
    def query_interpretation(self, operator: Operator, metrics: dict) -> str  # Returns query_id
    def query_optimization(self, operator_id: str) -> str
    def query_novelty_validation(self, operator_id: str) -> str
    def get_pending_responses(self) -> List[OracleResponse]
    def process_response(self, query_id: str, response: OracleResponse)

class DirectiveProcessor:
    """Processes admin directives as environmental signals."""
    
    def get_pending_directives(self) -> List[Directive]
    def execute_directive(self, directive: Directive) -> ExecutionResult
    def check_expired_directives(self)

class OracleQueryGenerator:
    """Auto-generates queries when operators cross thresholds."""
    
    def check_query_conditions(self, operator: Operator) -> bool
    def generate_query(self, operator: Operator, query_type: str) -> OracleQuery
```

---

## Integration Points

### 1. With core_gameplay.py

Operators influence action selection:

```python
# In GameplayEngine.select_action()
if self.operator_integration:
    signals = self.operator_integration.evaluate_operators(frame, context)
    action_weights = self.operator_integration.apply_operator_biases(action_weights, signals)
```

### 2. With autonomous_evolution_runner.py

Operator evolution runs each generation:

```python
# In AutonomousEvolutionRunner._run_generation()
if self.operator_composer and generation % self.operator_evolution_interval == 0:
    self.operator_composer.evolve_operators(generation)
    self.oracle_interface.process_pending_queries()
    self.directive_processor.execute_pending()
```

### 3. With viral_package_engine.py

High-performing operators can become viral packages:

```python
# When operator crosses promotion threshold
if operator.level_improvement > 0.20:
    viral_engine.create_viral_package_from_operator(operator)
```

---

## Testing Strategy

### Unit Tests (tests/test_cognitive_*.py)

| Test File | Coverage |
|-----------|----------|
| `test_cognitive_primitives.py` | All primitives execute correctly, edge cases handled |
| `test_operator_composer.py` | Composition, mutation, crossover, lifecycle |
| `test_oracle_interface.py` | Query generation, response processing, directives |

### Integration Tests

| Test | What It Validates |
|------|-------------------|
| Operator-gameplay integration | Operators influence action selection |
| RLVR feedback loop | Test results update operator metrics |
| Oracle async flow | System continues without oracle response |
| Directive execution | Admin signals modify system behavior |

### RLVR Validation

| Metric | Target | Measurement |
|--------|--------|-------------|
| Level 2+ improvement | >10% after 20 generations | Compare before/after operator introduction |
| Action efficiency | No degradation | Actions per level should not increase |
| Transfer learning | >0 on at least 2 game types | Same operator helps multiple games |

---

## Configuration

```python
# In autonomous_evolution_runner.py or config
OPERATOR_CONFIG = {
    'evolution_interval': 5,         # Evolve operators every N generations
    'population_size': 30,           # Operators under test
    'max_composition_depth': 6,      # Max primitives per operator
    'novelty_quota': 0.20,           # 20% must be new random compositions
    'promotion_threshold': 0.15,     # Level improvement to promote
    'decay_generations': 15,         # Generations unused before decay
    'oracle_query_threshold': 0.18,  # Performance threshold to query oracle
    'test_budget_per_operator': 10,  # Games per operator per generation
}
```

---

## Rollout Phases

### Phase 1: Seed Primitives + Unlock Infrastructure
- Implement ~20 seed primitives (data access, math, iteration, aggregation)
- Implement unlock status tracking (grandfathered, locked, unlocked, novel)
- Mark existing engine primitives as "grandfathered" (already earned)
- **System starts with seed + grandfathered primitives only**

### Phase 2: Operator Composer (Discovery Engine)
- Random composition of available primitives
- Mutation and crossover
- RLVR testing loop
- Database storage of discovered operators
- **System discovers patterns on its own**

### Phase 3: Oracle Interface (Unlock Gatekeeper)
- Query/response infrastructure
- Pattern matching against LOCKED primitives
- Unlock verification (RLVR thresholds)
- Novelty registration
- **Oracle validates, never injects**

### Phase 4: Primitive Unlocking
- Successful operators unlock matching locked primitives
- Unlocked primitives become available for composition
- Novel primitives registered and available
- **Earned vocabulary grows**

### Phase 5: Gameplay Integration
- Operators influence action selection
- RLVR feedback strengthens good operators
- Full end-to-end testing
- **Level 2+ breakthrough expected**

### Phase 6: Novel Primitive Review (Human Learning)
- Periodic review of novel primitives
- Human names assigned to valuable discoveries
- Optimization implementations created for novel patterns
- **Humans learn from what system discovered**

---

## Files to Create

| File | Purpose |
|------|---------|
| `seed_primitives.py` | Minimal seed primitives (~20) |
| `primitive_unlock_manager.py` | Track locked/unlocked/novel primitive status |
| `operator_composer.py` | Composition, evolution, and discovery |
| `oracle_interface.py` | Oracle-agnostic unlock gatekeeper |
| `tests/test_seed_primitives.py` | Seed primitive tests |
| `tests/test_unlock_manager.py` | Unlock mechanism tests |
| `tests/test_operator_composer.py` | Composer tests |
| `tests/test_oracle_interface.py` | Oracle tests |

---

## Success Criteria

1. **Primitives unlocked** - System earns access to locked primitives through discovery
2. **Novel primitives discovered** - Patterns that don't match any locked primitive
3. **Operators emerge** that correlate with level 2+ success
4. **Hierarchical composition** - Using unlocked primitives in new operators
5. **Mutation works** - System creates variations of known patterns
6. **Transfer learning** visible (operators/primitives help multiple games)
7. **No blocking on oracle** - System continues without oracle responses
8. **Human learning** - We discover something new from system's novel primitives

---

## The Three Victory Conditions

### Victory 1: Unlock Success
**System earns access to a locked primitive.**

Example: System discovers vertical symmetry detection → Oracle matches to `detect_symmetry` → UNLOCKED

This proves: System can learn known concepts through discovery.

### Victory 2: Novel Primitive
**System discovers something humans didn't formalize.**

Example: System discovers "fragmented symmetry detector" → Oracle finds no match → NOVEL REGISTERED

This proves: System can go beyond human knowledge.

### Victory 3: Novel Surpasses Human
**System's novel primitive outperforms human-designed alternatives.**

Example: Novel primitive achieves 25% level improvement vs 15% for closest human analog.

This proves: Machine discovery can exceed human understanding.

---

## The Ultimate Test

**If the system discovers something that makes humans say "we never thought of that", we've succeeded.**

That means:
- The system learned HOW to learn
- The system can discover things humans haven't formalized
- The system can potentially teach US
- True cognitive emergence, not pattern replay

---

**END OF IMPLEMENTATION GUIDE**
