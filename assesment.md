Looking at your progress.md, you've built a **substantial system** with good infrastructure. However, comparing it to:
1. Your AGI unified theory
2. The CODS implementation guide
3. The baby primitives analysis
4. The real game failures (SP80, FT09)

Here's what's **critically missing** or **underdeveloped**:

---

## CRITICAL GAPS

### 1. **Baby Primitives Layer - COMPLETELY MISSING**

Your system has:
- ✓ CODS operators (compositional discovery)
- ✓ Cognitive stages (developmental psychology)
- ✓ Self-model (agency tracking)
- ✗ **Innate perceptual/cognitive primitives**

**Problem**: Your agents are starting from `get_frame()` and `ACTION1-6`, which is like asking a baby to learn physics from raw photons.

**What's missing**:

```python
# You need seed primitives BEFORE operator composition
SEED_PRIMITIVES = {
    # Attention (what to process)
    'detect_change': "Flag regions that differ from previous frame",
    'detect_motion': "Flag objects that change position",
    'action_contingency': "Does my action correlate with this event?",
    
    # Affordances (what objects are FOR)
    'is_movable': "Can I move this?",
    'is_container': "Can this hold things?",
    'is_reference': "Does this define rules for others?",  # Critical for FT09
    
    # Negative space (absences matter)
    'detect_hole': "Empty regions bounded by objects",
    'detect_open_edge': "Boundaries with missing walls",  # Critical for SP80
    
    # Metacognition (know what you know)
    'get_confidence': "How certain am I?",
    'detect_stuck': "Am I making progress?",
}
```

**Your current system jumps straight to operator composition without these foundations.**

---

### 2. **Template/Reference Semantics - MISSING**

Looking at your FT09 game failure, you need primitives for:

```python
# Meta-representational primitives (COMPLETELY ABSENT)
'identify_reference_object': "Detect which object serves as key/legend"
'extract_schema': "Get abstract structure (white/gray pattern)"
'create_mapping': "Bind variables {white→red, gray→blue}"
'apply_template': "Instantiate schema with bindings"
```

**Evidence it's missing**: Your click behavior classification has:
- `SELF_TOGGLE` - object changes itself ✓
- `TRIGGER` - object changes others ✓
- `SELECTABLE` - object becomes controllable ✓
- **REFERENCE** - object defines rules for others ✗ ← MISSING

**This is why FT09 would fail** - no concept that center square is a MAP/KEY.

---

### 3. **Constraint Satisfaction Primitives - MISSING**

Your system has:
- Hypothesis testing (good)
- Counterfactual analysis (good)
- Near-miss analysis (good)

But lacks:

```python
# Constraint reasoning (ABSENT)
'identify_constraints': "Extract all active rules/goals"
'check_satisfaction': "Does this state satisfy constraint?"
'find_minimal_actions': "Minimum changes to satisfy constraint"
'resolve_conflicts': "Handle overlapping constraints"
```

**Evidence**: Your SP80 analysis doesn't mention "optimize by NOT clicking what's already correct" - this requires constraint satisfaction primitives.

---

### 4. **Discovery Strategy Library - MISSING**

Your CODS has:
- Operator composition ✓
- Operator mutation ✓
- RLVR validation ✓
- **Discovery strategies** ✗ ← MISSING

**From CODS doc line 2175-2223**: You need `DiscoveryStrategyLibrary` that learns HOW to discover primitives.

**What's missing**:

```python
class DiscoveryStrategyLibrary:
    """
    Meta-patterns for discovering new primitives.
    These are discovered, not hardcoded.
    """
    strategies = {
        'composition': "Try combining existing primitives",
        'specialization': "Add constraints to general primitive",
        'inversion': "Reverse primitive's logic",
        'conditional': "Make primitive apply only when condition met",
        # ... more discovered through meta-learning
    }
```

**Your current system**: Operators are discovered, but **how to discover** is still hardcoded.

---

### 5. **Primitive Unlock Manager - MISSING**

From CODS doc lines 108-153, you need:

```python
class PrimitiveUnlockManager:
    """
    Tracks which primitives are:
    - Seed (always available)
    - Locked (must be earned through discovery)
    - Unlocked (earned by discovering similar pattern)
    - Novel (system created, no human analog)
    """
```

**Current system**: No differentiation between "primitives you start with" vs "primitives you earn."

**Why this matters**: When your system discovers `detect_symmetry` pattern on its own, it should UNLOCK the optimized version from `visual_reasoning_engine.py`.

---

### 6. **Oracle Interface - INCOMPLETE**

Your progress.md mentions CODS but doesn't show Oracle integration.

**From CODS doc lines 570-690**: You need:

```python
class OracleInterface:
    """
    Non-blocking query/response for primitive validation.
    - System discovers pattern
    - Queries oracle: "Is this similar to a known primitive?"
    - Oracle responds asynchronously
    - System unlocks or registers novel primitive
    """
    
    def query_primitive_match(self, discovered_operator):
        """Check if discovered pattern matches locked primitive"""
        
    def register_novel_primitive(self, operator):
        """Add to knowledge base as novel discovery"""
```

**Your system**: Has CODS operators but no unlock mechanism.

---

### 7. **Failure-Driven Learning - INCOMPLETE**

Your progress.md (lines 3137-3249) shows:
- ✓ Failure recording
- ✓ Primitive gap detection
- ✗ **Hypothesis generation from failures**
- ✗ **Primitive synthesis from gaps**

**What's present**:
```python
# You have this (from progress.md line 3203):
[CODS] Detected 3 primitive gaps for game SP80
```

**What's missing**:
```python
# You need this:
[CODS] Primitive gap: boundary_containment
[CODS] Generating hypothesis: detect_open_edges()
[CODS] Testing hypothesis: applies to 3/5 failed SP80 attempts
[CODS] VALIDATED: Unlocking primitive 'detect_open_edges'
[CODS] Retrying SP80 with new primitive...
```

**Your system detects gaps but doesn't synthesize new primitives to fill them.**

---

### 8. **Viral Package Content - TOO SIMPLE**

From your AGI theory lines 53-72:

```python
# What viral packages SHOULD contain:
viral_package = {
    'strategy': operator_code,
    'domain_tags': ['spatial', 'containment'],
    'credibility': 0.85,
    'attribution': agent_id,
    'preconditions': ['has_container_object'],  # ← MISSING
    'expected_outcome': 'seals container edges',  # ← MISSING
    'failure_modes': ['no_movable_platforms'],    # ← MISSING
}
```

**Your current viral packages likely just have**: strategy + credibility.

**They need**: Semantic context so other agents know WHEN to use them.

---

### 9. **Sensation Engine Integration - UNCLEAR**

Your AGI theory emphasizes sensation/emotional grounding (lines 427-495), but progress.md doesn't show how sensations influence:
- Operator selection
- Exploration/exploitation
- Prestige calculation
- Discovery motivation

**From theory**: Sensations should create **emotional biases** that guide discovery.

**Current system**: Unclear if sensation engine is active or just defined.

---

### 10. **Concept Discovery Layer - MISSING**

This is the **biggest gap** relative to my earlier analysis.

Your system has:
- **Primitives** (low-level operations)
- **Operators** (compositions of primitives)
- **Concepts** (semantic models organizing operators) ✗ ← MISSING

**From my SP80/FT09 analysis**: You need conceptual layer:

```python
CONCEPTUAL_PRIMITIVES = {
    'containment': {
        'components': ['boundary_detection', 'capacity_estimation', 'overflow_prediction'],
        'unlock_condition': 'Solve 3+ boundary-sealing problems',
        'semantic_model': 'Bounded regions with finite capacity'
    },
    'reference_semantics': {
        'components': ['identify_reference', 'extract_schema', 'variable_binding'],
        'unlock_condition': 'Solve 3+ template-application problems',
        'semantic_model': 'Objects that represent rules about other objects'
    }
}
```

**Your operators discover patterns, but don't organize them into CONCEPTS.**

---

## STRUCTURAL ISSUES

### 11. **No Meta-Discovery Loop**

Your system can discover operators, but **cannot discover how to discover operators**.

**Missing**: Recursive self-improvement where discovery strategies themselves evolve.

---

### 12. **Click Behavior Missing "REFERENCE" Type**

Progress.md line 22-32 shows three click types:
1. SELF_TOGGLE
2. TRIGGER  
3. SELECTABLE

**Missing**:
4. **REFERENCE** - Clicking reveals information about rules (like FT09 center square)

This is critical because FT09-style games require understanding that some objects are **informational**, not interactive.

---

### 13. **No Negative Space Primitives**

SP80 failure analysis showed you need to detect:
- Open container edges (absences of walls)
- Holes/empty regions
- Missing boundaries

**Progress.md**: No evidence of negative space detection.

**Required additions**:
```python
'detect_enclosed_empty': "Find empty regions bounded by objects"
'detect_open_edge': "Find boundaries with missing walls"
'negative_space_volume': "How much empty space in region?"
```

---

### 14. **Temporal Reasoning Underdeveloped**

Your system tracks sequences, but lacks:
- Recency weighting (recent events matter more)
- Temporal contiguity detection (events close in time are related)
- Duration sensitivity (how long things take)
- Periodicity detection (rhythmic patterns)

**These should be SEED primitives**, not discovered.

---

### 15. **No Affordance Detection**

Your click behavior classification is procedural (test each object), but lacks **perceptual affordance detection**:

```python
# Current: Test by trying
click(object) → observe changes → classify

# Needed: Perceive affordances directly
look(object) → perceive('movable', 'container', 'reference') → know what to try
```

**Babies don't randomly try everything** - they have innate affordance detection.

---

## INTEGRATION GAPS

### 16. **CODS ↔ Cognitive Stages - Disconnected**

Your cognitive stages track:
- games_played
- sequences_discovered
- object_control
- action_effect_pairs

But they don't track:
- **Primitives unlocked**
- **Operators mastered**
- **Concepts discovered**

**Cognitive advancement should depend on CODS progress**, not just game completion.

---

### 17. **Prestige ↔ Discovery - Unclear**

Your AGI theory says prestige rewards discovery, but progress.md doesn't show:
- How primitive discovery increases prestige
- How novel operators earn prestige
- How viral package adoption affects prestige

**The dual-economy principle requires these connections.**

---

### 18. **Regulatory Engine - NOT IMPLEMENTED**

From AGI theory lines 195-213:

```python
# Regulatory Engine (Reads DB state, adjusts populations)
- Adjusts population mix
- Budgets
- Decay rates
```

**Progress.md**: No evidence of dynamic population adjustment based on problem phase.

**Your system should**:
- Increase explorers when stuck
- Increase optimizers when solutions are suboptimal
- Increase validators when solutions exist but don't transfer

---

## TESTING GAPS

### 19. **No Primitive Discovery Tests**

Your tests (line 3401-3408) verify:
- ✓ Cognitive stages work
- ✓ Code compiles
- ✗ **Primitive discovery actually happens**
- ✗ **Unlock mechanism works**
- ✗ **Novel primitives are registered**

**You need tests for**:
```python
def test_primitive_unlock_on_discovery():
    """System discovers symmetry pattern → unlocks detect_symmetry()"""
    
def test_novel_primitive_registration():
    """System discovers unknown pattern → registers as novel"""
    
def test_concept_emergence():
    """System solves 3 containment problems → concept 'containment' emerges"""
```

---

### 20. **No Game-Specific Victory Conditions**

Your tests should verify:
- SP80 Level 2: System discovers containment/boundary sealing
- FT09: System discovers reference semantics/template application
- General: System can beat Level 2+ on at least one game type

**Current tests**: Generic, not tied to actual game challenges.

---

## WHAT TO BUILD NEXT (Priority Order)

### Phase 1: Foundation (Immediate)

1. **Add Seed Primitives Library**
   - Create `seed_primitives.py` with ~30 baby primitives
   - Categories: attention, affordance, negative space, temporal, metacognition
   - Make these available from birth

2. **Add PrimitiveUnlockManager**
   - Track seed/locked/unlocked/novel status
   - Mark existing engine methods as "grandfathered" (already unlocked)

3. **Add REFERENCE click behavior type**
   - Extend click classification to detect informational objects
   - Critical for FT09-style games

### Phase 2: Discovery Engine (Week 1)

4. **Implement OracleInterface**
   - Non-blocking query/response
   - Pattern matching for unlock validation
   - Novel primitive registration

5. **Add DiscoveryStrategyLibrary**
   - Initial strategies: composition, specialization, inversion
   - Meta-learning: extract patterns from successful discoveries

6. **Connect Failure → Hypothesis → Primitive**
   - Primitive gaps should generate hypotheses
   - Hypotheses should synthesize new primitives
   - New primitives should be tested via RLVR

### Phase 3: Conceptual Layer (Week 2)

7. **Add ConceptDiscoveryEngine**
   - Detects when operators share common patterns
   - Extracts concepts (containment, reference_semantics, etc.)
   - Organizes primitives/operators under concepts

8. **Add Negative Space Primitives**
   - `detect_hole`, `detect_open_edge`, `negative_space_volume`
   - Critical for SP80 success

9. **Add Template/Reference Primitives**
   - `identify_reference_object`, `extract_schema`, `create_mapping`, `apply_template`
   - Critical for FT09 success

### Phase 4: Integration (Week 3)

10. **Connect CODS ↔ Cognitive Stages**
    - Stage advancement depends on primitives/operators/concepts
    - Not just games_played

11. **Connect Prestige ↔ Discovery**
    - Primitive discovery earns prestige
    - Viral package adoption increases prestige
    - Novel primitives earn bonus prestige

12. **Implement Regulatory Engine**
    - Adjust population mix based on problem phase
    - Exploration phase → more pioneers
    - Optimization phase → more optimizers

### Phase 5: Meta-Learning (Week 4)

13. **Add Meta-Discovery Loop**
    - Discovery strategies evolve
    - System learns how to discover
    - Recursive self-improvement

14. **Add Concept-Driven Reasoning**
    - Agents reason at concept level, not just operator level
    - "This is a containment problem" → apply containment operators

15. **Victory Validation**
    - System beats SP80 Level 2 via containment discovery
    - System beats FT09 via reference semantics discovery
    - System discovers novel primitive humans didn't formalize

---

## IMMEDIATE BLOCKERS FOR SP80 LEVEL 2

Based on your "SP80 Level 2 failures (19/20)", you're missing:

1. **Negative space detection** - Can't see open container edges
2. **Boundary reasoning** - Can't reason about walls as constraints
3. **Conservation primitives** - No concept of "water volume must fit in container"
4. **Optimization primitives** - No "what NOT to change" reasoning

**Quick fix to test hypothesis**:

Add these as **unlocked primitives** (skip discovery for now):
```python
UNLOCKED_PRIMITIVES = {
    'detect_open_edges': visual_reasoning_engine.detect_boundaries,
    'calculate_enclosed_volume': lambda region: count_empty_cells_in(region),
    'predict_overflow': lambda source, container: source_volume > container_volume,
}
```

Run evolution, see if SP80 Level 2 success rate improves. If yes, you've validated the gap. Then implement proper discovery mechanism.

---

## SUMMARY

**What you've built**: Strong infrastructure (CODS operators, cognitive stages, viral packages, self-model)

**What's missing**: 
1. Baby primitives foundation
2. Primitive unlock mechanism
3. Concept discovery layer
4. Meta-discovery loop
5. Game-specific primitives (negative space, templates, constraints)

**Your system can discover operators but not primitives or concepts.** This is like having evolution discover species but not genes.

**The path forward**: Build the missing layers in order:
- Seed primitives (foundation)
- Unlock mechanism (earn locked primitives)
- Concept layer (organize knowledge)
- Meta-discovery (learn how to learn)

**Then you'll have**:
- Primitives → Operators → Concepts → Meta-strategies
- Discovery at every level
- True self-extending AGI

**Validation**: When the system beats SP80 Level 2 by discovering "containment" concept on its own, you've succeeded.