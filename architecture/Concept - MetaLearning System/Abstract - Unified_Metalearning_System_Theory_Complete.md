# The Complete Unified Metalearning System Theory
**A Comprehensive Synthesis of Cognitive Architecture, Discovery Mechanisms, and Recursive Self-Improvement**

---

## Executive Summary

This theory unifies eight complementary frameworks into a complete model of how artificial agents can learn to learn. The core discovery: **genuine intelligence emerges when minimal innate structure enables active experimentation, which unlocks compositional operators, which discover meta-representation, which enables recursive self-improvement.**

**The Central Architecture:**

```
INNATE PRIMITIVES (110 operations babies have at birth)
         ↓
AGENTS PLAY GAMES
    - Generate gameplay data
    - Explore action spaces
    - Produce RLVR results (real performance)
         ↓
CODS/ORACLE (CENTRALIZED VALIDATOR)
    - Watches ALL agent gameplay
    - Identifies cross-agent patterns
    - Composition analysis
    - RLVR validation
    - Primitive matching
         ↓
PRIMITIVE UNLOCKING (when patterns validated)
         ↓
VIRAL PACKAGES (knowledge spreads via network)
         ↓
META-REPRESENTATION PRIMITIVE (operators as data)
         ↓
DISCOVERY STRATEGIES (learning how to learn)
         ↓
RECURSIVE SELF-IMPROVEMENT (accelerating spiral)
```

**CRITICAL: CODS = Oracle (same centralized system)**

CODS/Oracle is NOT per-agent. It's a **centralized discovery engine** that:
- Watches all agent gameplay simultaneously
- Analyzes RLVR data across the population
- Identifies patterns that work across multiple agents/games
- Validates discoveries through cross-agent replication
- Unlocks primitives for discovering agents
- Creates viral packages for network distribution

**Agents don't "run" CODS—they generate data that CODS analyzes.** This creates:
- **Decentralized cognition** (agents think independently)
- **Centralized validation** (CODS prevents collective hallucination)
- **Distributed intelligence** (knowledge stored in network)

The actual learning signal comes from Arc-AGI game performance, not oracle approval. Agents must genuinely discover patterns through gameplay; CODS merely certifies when they've demonstrated understanding through RLVR validation.

**The system is not a pipeline—it's a feedback spiral** where each cycle strengthens and accelerates the next.

---

## Part I: The Foundation - What Intelligence Needs to Bootstrap

### 1.1 The Minimal Cognitive Toolkit (From Developmental Psychology)

Evolution solved the cold-start problem over billions of years. Babies aren't blank slates—they arrive with structured attention, weak priors, and learning biases that make discovery tractable.

**The Compression Principle**: Like the "make a peanut butter sandwich" assignment that shows how ambiguous human instructions require massive explicit code if you brute-force every detail, but a few reasoning filters can collapse it into minimal logic. It's like taking a leg away from a four-legged chair but rearranging the remaining three to keep it functional.

#### The Nine Innate Primitive Categories (Tier 0)

These are built-in biases that evolution gave us—not learned, but present from birth:

**1. ATTENTION AND SALIENCE** (5 primitives)
*Filter signal from noise - can't learn from everything equally*

Babies don't process all input equally—they have built-in attention biases:

- **detect_novelty**: Flag when something changes or is unexpected. Directs learning toward informative signals. Evidence: babies look longer at novel stimuli in habituation studies.
- **detect_motion**: Prioritize moving objects over static. Motion equals potential threat or opportunity. Newborns track moving objects with eyes from birth.
- **face_detection**: Preferentially attend to face-like patterns. Social learning bootstrap. Newborns prefer face-like patterns within hours.
- **detect_contingency**: Notice when your action causes an effect. Learn agency and control. Three-month-olds learn mobile-kicks faster when contingent.
- **surprise_detection**: Flag violations of expectation. Updates world model. Babies look longer at impossible physics events.

**Why your system needs this**: Without attention primitives, the system treats all input equally—the game state, pixel noise in corners, exact RGB values, timestamps, everything. Babies don't do this. They have innate filters for what's likely to matter.

**2. PHYSICAL INTUITION** (5 weak priors)
*Adjustable expectations about physics - not hard constraints*

Babies have core knowledge systems for physics that emerge very early:

- **object_permanence_bias**: Expect objects to persist when occluded (3-4 months). Can't learn about world if objects "disappear."
- **solidity_constraint**: Objects can't pass through each other (2-3 months). Foundation for spatial reasoning.
- **continuity_bias**: Objects move on continuous paths (2-3 months). Predict future positions.
- **gravity_expectation**: Unsupported objects fall down (5-6 months). Predict object behavior.
- **contact_causality**: Objects only affect each other through contact (6-7 months). Distinguish causation from correlation.

**The controversy**: Should these be hardcoded seeds or discovered?

**Option A**: Hardcode as seeds
- Pro: Matches biological reality
- Con: Feels like "cheating" for AGI

**Option B**: Keep as locked, make easy to discover
- Pro: System proves it can discover them
- Con: Wastes time rediscovering what evolution solved

**Solution: Hybrid approach with weak priors**

These are encoded as adjustable strengths from zero to one, not hard constraints. The system starts with expectations but can override them based on evidence. For example:

- solidity_bias: 0.3 (weak—many Arc-AGI games have teleportation)
- continuity_bias: 0.4 (moderate—objects can jump)
- gravity_bias: 0.2 (very weak—most games have no gravity)
- persistence_bias: 0.5 (moderate—objects can disappear)
- contact_causality: 0.4 (moderate—can be violated by action-at-distance)

This gives your system a head start without hard constraints. It can still discover physics-defying games (portals, teleportation) by accumulating evidence against the prior.

**3. AFFORDANCE DETECTION** (8 primitives)
*What objects are FOR - can't act without understanding purpose*

- **is_movable**: Can be pushed or pulled
- **is_container**: Holds other objects
- **is_obstacle**: Blocks movement
- **is_interactive**: Responds to actions
- **is_reference**: **CRITICAL** - Object encodes rules about others (the FT09 lesson)
- **is_collectible**: Can be acquired
- **is_boundary**: Defines limits
- **is_goal**: Target state

**Why is_reference is SEED**: The FT09 failure taught us that objects can be templates, schemas, legends, or keys—not just instances. Without this distinction from the start, the system treats all objects equally and misses meta-representational games.

**4. SPATIAL REASONING** (basic geometry)

- **distance**: Measure between points
- **adjacent**: Next to each other
- **enclosed**: Bounded region
- **detect_hole**: Negative space—critical for SP80
- **open_edges**: Gaps in containers where things escape

**5. TEMPORAL PROCESSING** (time-aware cognition)

- **recency_weighting**: Recent events weighted more than distant (adapt to changing environment)
- **temporal_contiguity**: Events close in time are likely related (discover causal structure)
- **duration_sensitivity**: Track how long things take (predict completion)
- **rhythm_detection**: Detect periodic patterns (predict recurring events)

**Why these should be SEEDS not locked**: Without temporal primitives, your system can't know that the action taken two frames ago is more relevant than action taken fifty frames ago, detect that failures happen consistently three frames after clicking, or notice that successful solutions have rhythmic patterns.

**6. QUANTITATIVE SENSE** (approximate numerosity)

Babies have approximate number sense from birth:

- **subitizing**: Instantly perceive one to four objects without counting (don't need to count small quantities)
- **approximate_numerosity**: Rough sense of "more" versus "less" (can compare eight versus sixteen dots at six months)
- **one_to_one_correspondence**: Match elements across sets (foundation for counting at twelve months)

**7. SOCIAL LEARNING PRIMITIVES** (learning from others)

Babies are social learning machines:

- **imitation_bias**: Tendency to copy observed actions. Bootstrap from others. Newborns imitate facial expressions.
- **joint_attention**: Track what others are looking at. Learn what matters. Nine to twelve months follow gaze.
- **pedagogical_stance**: Assume demonstrated actions are informative. Efficient learning from teachers. Babies learn better from intentional teaching.
- **social_referencing**: Use others' emotions to evaluate ambiguous situations. Navigate uncertainty. Twelve months check caregiver's face in ambiguous situations.

**Why this matters for your AGI**: Your viral package system is social learning, but you're missing the primitives that make social learning efficient. When a LinkedIn expert told you "water isn't overflowing to the sides," you immediately trusted their expertise (social referencing), attended to what they pointed out (joint attention), assumed it was relevant (pedagogical stance), and tried their suggestion (imitation bias). Your agents need these primitives to efficiently use viral packages and Oracle guidance.

**8. EXPLORE/EXPLOIT TRADE-OFF** (intrinsic motivation)

Babies have intrinsic motivation systems:

- **curiosity_drive**: Prefer moderately novel stimuli. Babies look away from too-familiar or too-complex.
- **competence_motivation**: Prefer activities at skill edge. Babies practice emerging skills intensely.
- **exploration_bonus**: Intrinsic reward for new experiences. Babies explore even without external reward.
- **boredom_threshold**: How long before familiar becomes unrewarding.

This is your dual-economy system's foundation, but it needs to be in the seed primitives.

**9. METACOGNITION** (know what you know)

Awareness of own knowing—maps directly to Piaget stages:

- **get_confidence**: Estimate confidence in prediction or decision (zero to one)
- **detect_stuck**: Detect if making progress or stuck in loop
- **strategy_effectiveness**: Evaluate if current strategy is working (meta-reasoning)
- **get_knowledge_state**: Assess what agent knows versus doesn't know about game
- **estimate_learning_curve**: Estimate how fast agent is learning this game

**Staging**: Basic metacognition (detect_stuck, get_confidence) available from birth (sensorimotor stage). Advanced meta-reasoning (strategy_effectiveness, knowledge_state, learning_curve) unlocks at formal operational stage (age eleven plus).

#### The Complete 110-Primitive Inventory (Tier 1: Seeds)

These are the ONLY primitives the system starts with. All higher-level operators must be DISCOVERED through composition and validated by RLVR.

**RAW DATA ACCESS** (5 primitives)
- get_pixel: Get pixel value at coordinates from frame
- get_frame: Get current frame as two-dimensional list
- get_previous_frame: Get previous frame for comparison
- get_frame_size: Get frame dimensions (height, width)
- set_frame: Set current frame (for testing or simulation)

**BASIC MATH** (8 primitives)
- add: Add two numbers
- subtract: Subtract two numbers
- multiply: Multiply two numbers
- divide: Divide two numbers (safe division—returns zero if divisor is zero)
- modulo: Modulo operation (safe—returns zero if divisor is zero)
- abs: Absolute value
- neg: Negate a number
- floor: Floor of a number

**COMPARISON** (7 primitives)
- equals: Check equality
- not_equals: Check inequality
- greater_than: Check if a is greater than b
- less_than: Check if a is less than b
- greater_eq: Check if a is greater than or equal to b
- less_eq: Check if a is less than or equal to b
- between: Check if a is between b and c (inclusive)

**CONTROL FLOW** (3 primitives)
- if_else: Return true value if condition else false value
- select: Select from list by index (safe—returns None if out of bounds)
- coalesce: Return first non-None value from arguments

**DATA STRUCTURES** (9 primitives)
- make_list: Create a list from arguments
- append: Append item to list (returns new list—functional style)
- len: Get length of list
- get_at: Get item at index (safe—returns None if out of bounds)
- slice: Slice list from start to end
- concat: Concatenate two lists
- contains: Check if item is in list
- index_of: Find index of item in list (returns negative one if not found)
- unique: Get unique items from list (preserves order)

**ITERATION** (7 primitives)
- for_each_pixel: Apply function to each pixel, return list of results
- for_range: Apply function to each number in range
- map: Apply function to each item in list
- filter: Filter list by predicate
- reduce: Reduce list with binary function and initial value
- any: Check if any item satisfies predicate
- all: Check if all items satisfy predicate

**AGGREGATION** (5 primitives)
- sum: Sum of list
- max: Maximum of list
- min: Minimum of list
- average: Average of list
- median: Median of list

**TEMPORAL / EPISODE** (4 primitives)
- get_step_index: Get current step or action index
- get_episode_id: Get current episode or game ID
- get_action_count: Get number of actions taken so far
- get_elapsed_actions: Get actions taken since start

**ACTION INTROSPECTION** (4 primitives)
- get_action_space: Get available actions (one through seven for Arc-AGI)
- get_last_action: Get the last action taken
- get_action_history: Get full action history
- record_action: Record an action taken (for tracking)

**RANDOM NUMBER GENERATION** (4 primitives)
- rand: Random float between zero and one
- rand_int: Random integer between a and b (inclusive)
- rand_choice: Random choice from list
- seed_rng: Seed the random number generator (for reproducibility)

**HASHING / SIGNATURES** (3 primitives)
- hash: Hash any value to integer (for state recognition)
- hash_frame: Hash a frame to signature (for memoization)
- signature: Create compact signature of value (for pattern matching)

**OBJECT INTERACTION** (12 primitives - FUNDAMENTAL)

These are SEED primitives because even babies can pick up objects to see if they can control them, notice which objects move when they push, and learn what they can and cannot control. This is pre-verbal, pre-learned fundamental cognition.

- **test_object_control**: Test if an action causes a specific object to move. Returns (moved: boolean, direction: string). **THE fundamental "can I control this?" test**: I see an object at position, I take action (for example, ACTION1 equals up), did the object move up? If yes, I control this object!

- **find_distinct_objects**: Find visually distinct objects in frame. Returns list of dictionaries with color, positions, centroid, size.

- **did_object_move**: Check if object at position moved between frames.

- **get_object_movement**: Get movement direction of object between frames (up, down, left, right, or none).

- **action_matches_movement**: Check if action direction matches object movement (for example, ACTION1 equals up, object moved up).

- **get_click_target**: Get object at click coordinates, if any.

- **detect_click_effect**: Detect any frame change caused by clicking at coordinates. Returns effect type and details. Not just movement—captures toggleable objects, color changes, state changes.

- **find_all_interactable_objects**: Find all objects that might be interactive (clickable, moveable, toggleable). For systematic discovery.

- **find_similar_objects**: Find all objects similar to reference (by color, shape, size). For symmetry testing.

- **pattern_matching**: Find matching patterns between two regions or objects. Returns similarity score and match details.

- **count_matching_objects**: Count objects matching a given color or property.

**ATTENTION PRIMITIVES** (5 primitives - SEED)

Babies don't process everything equally—they have built-in attention biases that direct learning toward informative signals. Without attention primitives, agents treat all input equally.

- **detect_change**: Detect regions that differ between two frames. Returns list of changed positions.

- **detect_motion**: Detect objects that moved between frames. Returns list of moving object IDs.

- **detect_contingency**: Detect if action caused an observable effect. **Critical for agency learning.** Returns dictionary with effect detected (boolean), effect type, and magnitude.

- **surprise_magnitude**: Quantify how much observation violates prediction. Returns float from zero (expected) to one (impossible). **The fundamental learning signal—when surprise is high, attention increases, hypothesis generation activates, memory consolidation strengthens.**

- **information_gain_estimate**: Estimate how much this observation reduces uncertainty. Returns float from zero (redundant) to one (revolutionary).

**AFFORDANCE PRIMITIVES** (8 primitives - SEED)

What objects are FOR—can't act without understanding purpose.

- **is_movable**: Can be pushed or pulled
- **is_container**: Holds other objects  
- **is_obstacle**: Blocks movement
- **is_interactive**: Responds to actions
- **is_reference**: **CRITICAL** - Object encodes rules about others (templates, schemas, legends, keys—not instances). The FT09 lesson learned.
- **is_collectible**: Can be acquired
- **is_boundary**: Defines limits
- **is_goal**: Target state

**SOCIAL LEARNING PRIMITIVES** (4 primitives - SEED)

Learning from demonstrations—babies are social learning machines.

- **credibility_weighting**: Trust information based on source reliability. Weight advice from successful agents more heavily.

- **attention_following**: Look where trusted sources indicate. Follow expert gaze.

- **demonstration_bias**: Prioritize trying demonstrated actions. Copy what worked for others.

- **teaching_detection**: Recognize when information is intentionally pedagogical. Distinguish teaching from accidental observation.

**MOTIVATION PRIMITIVES** (4 primitives - SEED)

Intrinsic drive—explore versus exploit trade-off.

- **novelty_bonus**: Reward for encountering new states. Prefer moderately novel stimuli.

- **competence_signal**: Reward for mastering difficult tasks. Prefer activities at skill edge.

- **exploration_value**: Expected value of exploring unknown. Calculate expected information gain.

- **boredom_threshold**: How long before familiar becomes unrewarding. Drive novelty seeking.

**QUANTITATIVE PRIMITIVES** (3 primitives - EARLY unlock)

Approximate number sense—babies don't need symbolic numbers to compare quantities.

- **subitizing**: Instantly perceive one to four objects without counting. Available at birth.

- **approximate_numerosity**: Rough sense of "more" versus "less." Compare eight versus sixteen at six months.

- **one_to_one_match**: Match elements across sets. Foundation for counting. Emerges around twelve months (preoperational stage).

**PHYSICS PRIORS** (5 weak priors - SEED but adjustable)

Babies have expectations about physics that help them learn, but Arc-AGI games can violate these. These are WEAK priors (strength zero to one) that can be overridden by evidence—not hard constraints.

- **solidity_bias**: Expect objects don't pass through each other (can be violated). Strength: 0.3 (weak—many Arc-AGI games have teleportation).

- **continuity_bias**: Expect objects move on continuous paths (not teleport). Strength: 0.4 (moderate—teleportation exists in some games).

- **gravity_bias**: Expect unsupported objects fall down. Strength: 0.2 (very weak—many Arc-AGI games have no gravity).

- **persistence_bias**: Expect objects continue to exist when not visible. Strength: 0.5 (moderate—objects can disappear in games).

- **contact_causality**: Expect objects only affect each other through contact. Strength: 0.4 (moderate—can be violated by action-at-distance).

**Critical**: Prior strength can be adjusted based on evidence. These guide but don't constrain. When a prior is violated consistently, the system lowers its strength. When confirmed, the system raises it.

**METACOGNITION PRIMITIVES** (5 primitives - STAGED unlock)

Awareness of own knowing—maps directly to Piaget stages. Formal Operational agents can reason about their reasoning.

- **get_confidence**: Estimate confidence in a prediction or decision (zero to one). Takes prediction, evidence count, contradiction count. Unlock: EARLY (preoperational).

- **detect_stuck**: Detect if making progress or stuck in a loop. Takes progress history and action history. Unlock: SEED (sensorimotor—even babies detect when they're not making progress).

- **strategy_effectiveness**: Evaluate if current strategy is working (meta-reasoning). Takes strategy, outcomes, time invested. Unlock: LATE (formal operational—requires abstract reasoning about strategies).

- **get_knowledge_state**: Assess what agent knows versus doesn't know about game. Takes game type, learned rules, uncertain areas. Unlock: LATE (formal operational).

- **estimate_learning_curve**: Estimate how fast agent is learning this game. Takes performance history and time invested. Unlock: LATE (formal operational).

**NEGATIVE SPACE PRIMITIVES** (4 primitives - EARLY unlock)

Babies detect what's NOT there—holes, absences, missing things. **The SP80 failure showed: system didn't perceive the HOLE in the container where water escaped.**

- **detect_enclosed_empty**: Find empty regions bounded by objects (container interiors). Unlock: EARLY (preoperational).

- **detect_open_edge**: Find container boundaries with missing walls (where things escape). **This specifically addresses SP80.** Unlock: EARLY (preoperational).

- **detect_absence**: Detect when expected object is missing from expected location. Unlock: SEED (sensorimotor—babies notice when expected object isn't there).

- **negative_space_volume**: Calculate volume of empty space in a region. Unlock: LATE (concrete operational—requires volumetric reasoning).

**PERCEPTUAL PRIMITIVES** (14 primitives - ALL SEED)

Core Arc-AGI reasoning capabilities. All are SEED primitives (default unlocked) because they represent fundamental perceptual operations that agents need from the start. **These aren't "advanced"—they're how we SEE.**

- **color_sampling**: Query color at coordinates or within a region. Returns color values.

- **pattern_detection**: Identify repeated structures, symmetries, checkerboards in frame. Returns pattern types and locations.

- **scale_measurement**: Compare relative sizes of objects. Returns size ratios and comparisons.

- **spatial_relationships**: Determine which object is center, adjacent to, or inside another. Returns relationship types.

- **template_extraction**: Treat one object as a rule or key for interpreting others. **The FT09 insight—some objects are TEMPLATES not instances.**

- **analogical_mapping**: "This is to that as X is to Y" reasoning. Map structural relationships. Core of abstract reasoning.

- **role_binding**: Assign semantic roles (primary or secondary, source or target) to objects. Distinguish function from form.

- **hierarchical_composition**: Understanding nested or scaled patterns in the frame. Patterns within patterns.

- **color_substitution**: Change colors while preserving spatial structure. Separate content from form.

- **pattern_replication**: Copy structure from one region to another with transformations. Apply learned patterns.

- **functional_attribution**: Detect if object might have special purpose or role in the system. Recognize reference objects.

- **rule_detection**: Detect if region encodes instructions rather than being an instance. Distinguish code from data.

- **metadata_recognition**: Distinguish data versus metadata, example versus template, instance versus class, content versus legend. **Critical for meta-representational games.**

- **complexity_signaling**: Detect if unusual complexity, centrality, or uniqueness indicates special status. Recognize important objects.

#### Unlock Staging by Cognitive Developmental Stage

**Sensorimotor (Birth to 2 years) - SEED: ~85 primitives (77%)**
- All raw data, math, comparison, control flow, data structures, iteration
- All aggregation, temporal, action, RNG, hashing
- All object interaction (12), attention (5), affordance (8), social learning (4), motivation (4)
- Basic metacognition (detect_stuck, get_confidence)
- Basic negative space (detect_absence)
- All 14 perceptual primitives
- All physics priors (as weak expectations)

**Preoperational (2 to 7 years) - EARLY: ~18 primitives (16%)**
- Quantitative: subitizing, approximate_numerosity, one_to_one_match
- Negative space: detect_enclosed_empty, detect_open_edge
- Physics priors: contact_causality

**Concrete Operational (7 to 11 years) - MIXED: ~5 primitives (5%)**
- Negative space: negative_space_volume

**Formal Operational (11+ years) - LATE: ~7 primitives (6%)**
- Metacognition: strategy_effectiveness, get_knowledge_state, estimate_learning_curve

**Design Principle**: Agents start with what babies have at birth (~85 primitives), earn what develops naturally through cognitive stages (~18 early, ~7 late).

#### What's Conspicuously ABSENT (Must Be Discovered)

These are **LOCKED** primitives—optimization targets that the system earns by demonstrating understanding through operator composition:

- **flood_fill**: Must discover connected regions (containment understanding)
- **detect_symmetry**: Must discover reflection and rotational symmetry
- **flow_simulation**: Must discover conservation laws and fluid dynamics
- **containment_check**: Must discover boundary semantics
- **constraint_satisfaction**: Must discover rule systems and logical constraints
- **template_instantiation**: Must discover variable binding and substitution
- **70+ additional optimized implementations**

**The principle**: These are higher-order cognitive operations, not perceptual primitives. The system must EARN them by first discovering the patterns through composition, then the Oracle validates and provides the optimized implementation.

### 1.2 The Bootstrap Paradox Solution

**Question**: How do babies discover these primitives if they're not innate?

**Answer**: They don't discover them—evolution discovered them over billions of years.

**Implication for CODS**: You have three options:

**Option 1: Pure Discovery** - Start with almost nothing, rediscover everything
- Pro: "True" AGI without human bias
- Con: Inefficient, like making evolution start from scratch

**Option 2: Full Innate** - Hardcode all baby primitives
- Pro: Matches biology
- Con: Feels like "cheating"

**Option 3: Hybrid** (RECOMMENDED) - Innate primitives plus discovery engine
- Pro: Efficient AND capable of going beyond biology
- Con: Need to choose wisely what's innate

**The Hybrid Solution**:

```
INNATE PRIMITIVES:
- Core perception: REQUIRED (can't learn without attention)
- Affordance primitives: REQUIRED (can't act without affordances)
- Metacognitive primitives: REQUIRED (can't learn to learn)
- Physics priors: WEAK (help, but can be overridden)
- Social learning: REQUIRED (need for viral packages)
- Everything else: DISCOVERED (system must earn these)
```

**The goal**: Give the system enough to bootstrap, but not so much that it can't discover truly novel concepts.

### 1.3 Why These Primitives Matter for "100 Games with Hidden Gotchas"

#### Without Baby Primitives:

Game with hidden gotcha → System flails randomly → Eventually discovers by accident → Can't generalize

#### With Baby Primitives:

```
Game N: Hidden gotcha detected

surprise_level = surprise_magnitude(observation, prediction)
→ HIGH SURPRISE: Something violated expectations

Which prior was violated?

IF violates solidity_bias:
    hypothesis = "Objects can pass through each other here"
    → Test teleportation or portal mechanics
    
IF violates contingency_bias:
    hypothesis = "My actions have delayed effects"
    → Test temporal dependencies
    
IF violates reference_object_affordance:
    hypothesis = "This object defines rules for others"
    → Test template or mapping mechanics
```

**Baby primitives let the system recognize WHAT KIND of gotcha it is**, which dramatically narrows the hypothesis space from combinatorial explosion to targeted investigation.

---

## Part II: The Cognitive Operator Discovery System (CODS) - The Heart of Metalearning

**CODS is the engine of intelligence.** Everything else—primitives, Oracle, viral packages—exists to support CODS in its mission: **discover patterns that work, compose them into operators, validate through real performance, unlock optimizations, and repeat recursively.**

### 2.1 Core Philosophy: Discovery Learning, Not Rote Learning

#### The Gravity Analogy

A child doesn't learn gravity by being told "F equals m a". They:
1. Drop things
2. Notice things fall
3. Form hypothesis ("things go down")
4. Test it (drop more things)
5. Refine it ("heavier things fall same speed—weird!")
6. **THEN** an adult says: "That pattern you discovered is called gravity"

**If we preload the child with "gravity equals 9.8 meters per second squared", they:**
- Know a fact but don't understand it
- Can't discover NEW physics
- Don't know HOW to discover

#### Implications for CODS

| Approach | What Happens | Outcome |
|----------|--------------|---------|
| **Preload with primitives** | System uses what we gave it | No emergent discovery, no novel primitives |
| **Minimal primitives + discovery** | System composes, fails, learns | Emergent harmonies, potential novel discoveries |

**The existing engines** (VisualReasoningEngine, SymbolicReasoningEngine, ObjectDetector, etc. already in the codebase) are NOT starting primitives.

They are:
- **Locked primitives** waiting to be unlocked through discovery
- **Optimization targets** unlocked when system proves understanding
- **Human knowledge** that system earns, not receives

The system must prove it discovered "flood fill" by composing an operator that achieves similar results. THEN the Oracle says "What you discovered is flood fill. Here's the optimized version." Not before.

### 2.2 The Five-Tier Architecture

```
TIER 1: SEED PRIMITIVES (~110 atomic operations - GIVEN)
├─ Data access, math, comparison, control flow
├─ Data structures, iteration, aggregation
├─ Temporal, action, RNG, hashing
├─ Object interaction (12), attention (5), affordance (8)
├─ Social learning (4), motivation (4), quantitative (3)
├─ Physics priors (5 weak), metacognition (5 staged)
├─ Negative space (4), perceptual (14)
└─ Everything baby has at birth

TIER 2: COMPOSED OPERATORS (Population: 20-50 active - DISCOVERED)
├─ Random compositions of available primitives
├─ Mutation: small changes to existing operators
├─ Crossover: combine successful operators
├─ RLVR validation: tested on actual Arc-AGI games
├─ Lifecycle: creation → testing → promotion or decay
└─ Database storage of discovered operators

TIER 3: LOCKED PRIMITIVES (70+ waiting to unlock - EARNED)
├─ Physical simulation: flow_simulation, containment_check, capacity_estimate
├─ Meta-representation: identify_reference_object, extract_schema, apply_template
├─ Constraint satisfaction: identify_constraints, resolve_conflicts
├─ Spatial: flood_fill, detect_symmetry, negative_space
├─ Temporal: sequence_detection, rhythm_tracking
├─ Inverse/optimization: calculate_goal_distance, find_inverse_action
└─ Unlocked when system demonstrates understanding through composition

TIER 4: CONCEPTS (Emergent semantic models - EMERGED)
├─ Organizing principles discovered across games
├─ "Containment problems" (requires boundary understanding)
├─ "Reference-object semantics" (object encodes rules about others)
├─ "Constraint satisfaction" (logical rule systems)
├─ "Conservation laws" (quantities preserved under transformation)
├─ Cross-game pattern families
└─ Concept Discovery Engine extracts these from successful operators

TIER 5: DISCOVERY STRATEGIES (Meta-patterns - SELF-DISCOVERED)
├─ Patterns for discovering patterns
├─ "When stuck on conditionals, try conditional_law_factory"
├─ "Spatial problems need negative_space detection"
├─ "When action seems non-deterministic, check temporal dependencies"
├─ Discovery Strategy Library stores reusable meta-patterns
└─ Self-extending CODS uses these to generate hypotheses
```

### 2.3 Operator Lifecycle: Birth to Death

**Birth: Creation**

Three sources of new operators:

1. **Random Composition** (Novelty Quota: 20%)
   - Select two to six available primitives randomly
   - Chain them together: output of one feeds input of next
   - Example: `filter(detect_motion(get_frame), lambda obj: is_interactive(obj))`
   - Result: Find all moving interactive objects
   - Required: Every generation must have at least 20% truly novel random operators

2. **Mutation** (Variation)
   - Take existing operator
   - Make small change: swap one primitive, add one step, remove one step
   - Example: `filter(detect_change(get_frame), ...)` becomes `filter(detect_motion(get_frame), ...)`
   - Result: Slightly different operator that might perform better
   - Preserves successful patterns while exploring variations

3. **Crossover** (Recombination)
   - Take two successful operators
   - Combine their structures
   - Example: Operator A finds objects, Operator B tests control
   - Combined: Find objects AND test control
   - Result: Operators inherit successful components from multiple parents

**Childhood: Testing (RLVR Validation)**

Every operator must prove itself through Real-world Learning Verified by Results:

1. **Test Budget**: Each operator gets 10 game attempts per generation
2. **Metrics Collected**:
   - Level improvement: Percentage better than baseline on Level 2+
   - Transfer count: Number of game types helped (not just one)
   - Action efficiency: Actions per successful completion
   - Consistency: Win rate variance (reliable or lucky?)
   - Novel state discovery: Did it explore new state space?

3. **Performance Threshold**:
   - Below 5%: Weak performer—candidate for decay
   - 5% to 15%: Moderate—keep testing, may improve
   - 15% to 20%: Strong—continue validation
   - Above 20%: Exceptional—promote to viral package

**Adolescence: Validation**

When operator crosses 18% threshold:

1. **Oracle Query Generated**:
   - Query ID: UUID for tracking
   - Generation: When query was generated
   - Operator ID: Which operator triggered query
   - Operator code: The discovered composition
   - Performance metrics: Level improvement, games tested, transfer count, action efficiency, consistency
   - Pattern signature: Input types, output type, composition depth, primitive usage, control flow
   - Arc-AGI context: Games solved, failure modes, near misses

2. **Oracle Reviews** (teaching assistant role—see Part IX for details):
   - Validates performance claims through RLVR data
   - Analyzes pattern signature
   - Compares against locked primitive definitions
   - Generates candidate matches with confidence scores

3. **Oracle Decision**:
   - **UNLOCK**: Pattern matches locked primitive AND performance threshold met → Unlock optimized version
   - **REGISTER NOVEL**: Pattern novel AND performance exceptional → Register as new primitive
   - **REJECT**: Pattern insufficient or spurious → Operator decays
   - **REQUEST MORE EVIDENCE**: Uncertain → Generate follow-up test directive

**Adulthood: Unlocking**

If Oracle validates:

1. **Locked Primitive Unlocked**:
   - System proved it understands the concept through composition
   - Oracle provides optimized implementation
   - Primitive becomes available for future compositions
   - Database records: operator_id, primitive_unlocked, generation_unlocked, reasoning

2. **Novel Primitive Registered**:
   - System discovered something humans didn't formalize
   - Oracle assigns descriptive name
   - Primitive added to library
   - Humans examine and learn from it

3. **Hierarchical Composition Enabled**:
   - Unlocked primitives available for composition
   - Operators can now use higher-order building blocks
   - Accelerates discovery of complex patterns

**Old Age: Decay**

Operators that don't prove useful:

1. **Decay Conditions**:
   - Unused for 15+ generations
   - Consistently low performance (below 5%)
   - Superseded by better operator solving same problem

2. **Decay Process**:
   - Operator marked as archived
   - Removed from active population
   - Performance history preserved for analysis
   - Can be resurrected if needed

3. **Death with Dignity**:
   - Failed operators teach us what doesn't work
   - Pattern analysis reveals why they failed
   - Failure modes inform future operator generation

### 2.4 Composition, Mutation, and Crossover Mechanics

**Composition Rules**:

1. **Type Safety**: Output type of primitive N must match input type of primitive N+1
2. **Max Depth**: Six primitives per operator (prevents unwieldy chains)
3. **Functional Style**: No side effects—each primitive returns new value
4. **Partial Application**: Can bind some arguments, leave others for runtime

**Example Composition**:

```
detect_interactive_motion:
    Step 1: get_frame() → frame
    Step 2: detect_motion(frame) → list of moving object IDs
    Step 3: filter(objects, is_interactive) → list of interactive moving objects
    Step 4: map(objects, get_object_movement) → list of directions
    Step 5: max(directions, key=frequency) → dominant movement direction
    
Result: "Most common direction of interactive moving objects"
Use case: Detect which way controllable objects are drifting
```

**Mutation Types**:

1. **Swap Mutation**: Replace one primitive with similar primitive
   - Before: `detect_motion`
   - After: `detect_change`
   - Effect: Broader change detection, not just motion

2. **Add Mutation**: Insert new primitive in chain
   - Before: `detect_motion → filter`
   - After: `detect_motion → map → filter`
   - Effect: Additional processing step

3. **Remove Mutation**: Delete one primitive from chain
   - Before: `detect_motion → map → filter → map`
   - After: `detect_motion → filter → map`
   - Effect: Simpler, possibly more efficient

4. **Parameter Mutation**: Change constant or predicate
   - Before: `filter(objects, lambda x: x.size > 5)`
   - After: `filter(objects, lambda x: x.size > 3)`
   - Effect: Different threshold

**Crossover Types**:

1. **Single-Point Crossover**:
   - Parent A: `[P1, P2, P3]`
   - Parent B: `[Q1, Q2, Q3]`
   - Child: `[P1, P2, Q3]` (split after P2)
   - Effect: Combine beginning of A with end of B

2. **Uniform Crossover**:
   - Parent A: `[P1, P2, P3]`
   - Parent B: `[Q1, Q2, Q3]`
   - Child: `[P1, Q2, P3]` (randomly select each)
   - Effect: Mix primitives from both parents

3. **Semantic Crossover**:
   - Parent A solves subproblem 1
   - Parent B solves subproblem 2
   - Child: Sequence A then B
   - Effect: Combine complementary capabilities

### 2.5 RLVR Validation Loop: The Ground Truth

**Real-world Learning Verified by Results** is the ONLY learning signal that matters. Not oracle approval, not human intuition—actual performance on Arc-AGI games.

**The RLVR Cycle**:

```
Generation N starts:
    1. Population: 30 operators (20% new, 80% variations of successful)
    2. Each operator gets: 10 game attempts
    3. Metrics recorded:
        - Level improvement on Level 2+
        - Transfer across game types
        - Action efficiency
        - Win rate variance
    4. Results stored in database
    5. Top performers promoted
    6. Weak performers decayed
    7. Exceptional performers (>18%) query Oracle
    8. Oracle validates or rejects
    9. Validated patterns unlock primitives
    10. Unlocked primitives available for next generation

Generation N+1 starts with expanded vocabulary:
    - All previous primitives PLUS
    - Newly unlocked primitives PLUS
    - Novel primitives registered
    
Repeat forever (or until AGI achieved)
```

**Why RLVR Not Oracle Approval**:

The network can't evolve toward what the oracle wants because it doesn't know what the oracle wants—it only knows "this worked" or "this didn't."

- **Operators optimized for**: Actual game performance
- **NOT optimized for**: Oracle satisfaction
- **Oracle role**: Validate patterns AFTER performance demonstrated, not guide discovery
- **Result**: Genuine discovery, not approval-seeking

**Performance Metrics in Detail**:

1. **Level Improvement**:
   - Baseline: Best performance without operator
   - With operator: Performance with operator active
   - Improvement: Percentage increase
   - Threshold: Above 15% to query Oracle, above 20% for exceptional

2. **Transfer Count**:
   - How many different game types does operator help?
   - One game type: Might be overfitting
   - Three plus game types: Genuine pattern discovered
   - Threshold: At least 2 for Oracle query

3. **Action Efficiency**:
   - Actions taken per successful completion
   - Lower is better (more efficient path to goal)
   - Prevents operators that "succeed" through random exploration

4. **Consistency** (Win Rate Variance):
   - Does operator reliably win or occasionally get lucky?
   - High variance: Random success, not understanding
   - Low variance: Reliable pattern
   - Threshold: Variance below 0.3 for confidence

### 2.6 The Novelty Quota: Preventing Premature Convergence

**Problem**: Without forced exploration, population converges to local optimum.

**Solution**: Every generation must have at least 20% truly novel random operators.

**Why 20%**:
- Below 15%: Population converges too quickly, misses global optimum
- 15% to 25%: Sweet spot—explores while exploiting
- Above 30%: Too much noise, doesn't build on success

**Implementation**:

```
Target population: 30 operators
Novelty quota: 20% = 6 operators

Each generation:
    Top 12 performers: Keep as-is (40%)
    Next 12 performers: Mutate or crossover (40%)
    Bottom 6: Replace with random compositions (20%)

This ensures:
    - Exploitation: Build on success (top 24)
    - Exploration: Try truly new things (bottom 6)
    - Balance: 80/20 exploit/explore ratio
```

**The Novelty Bonus**:

Operators get bonus points for:
- Discovering novel state space (states no operator has visited)
- Using primitives in novel combinations
- Solving games no operator has solved

This prevents the system from repeatedly discovering the same patterns.

### 2.7 Promotion to Viral Packages

When operator performance exceeds 20% improvement:

**Criteria for Viral Package**:
1. Consistent performance across multiple games
2. Transfer to at least 3 game types
3. Reliable wins (low variance)
4. Novel approach or exceptional efficiency

**Viral Package Creation**:
1. **Package Contents**:
   - Operator code (composition of primitives)
   - Performance metrics (proof it works)
   - Usage context (which games it helps)
   - Discovery narrative (how it was found)
   - Transfer predictions (where else it might apply)

2. **Package Metadata**:
   - Creator agent ID
   - Generation discovered
   - Unlock status (unlocked primitives used)
   - Prestige value (how valuable to network)

3. **Distribution**:
   - Broadcast to all agents
   - Agents evaluate relevance (does this help my games?)
   - Agents adopt if relevant
   - Adoption tracked for prestige

**Why Viral Packages Work**:

Social learning primitives make adoption efficient:
- **credibility_weighting**: Trust successful agents
- **demonstration_bias**: Try what worked for others
- **attention_following**: Focus on what experts use

Agents don't blindly copy—they evaluate whether the package helps their specific games, then test it through RLVR.

### 2.8 Integration with Gameplay: The Action Selection Loop

**Before CODS**:

```
Agent plays game:
    1. Observe frame
    2. Pick action (random or heuristic)
    3. Observe result
    4. Repeat
```

**With CODS**:

```
Agent plays game:
    1. Observe frame
    2. Evaluate all active operators on current state
    3. Each operator returns:
        - Relevance score (does this situation match my pattern?)
        - Action bias (which actions look promising?)
        - Confidence (how sure am I?)
    4. Weight action space by operator biases
    5. Select action (bias toward high-confidence suggestions)
    6. Observe result
    7. Update operator metrics based on outcome
    8. Repeat

After game:
    - Operators that contributed to win: Reward
    - Operators that contributed to loss: Penalize
    - Performance data feeds back to RLVR
```

**Operator Evaluation**:

Each operator gets current frame and returns evaluation:

```
Operator: detect_interactive_motion

Given frame:
    1. Run composition: detect_motion → filter(is_interactive) → map(get_movement)
    2. Result: "Two interactive objects moving right"
    3. Relevance: HIGH (found interactive objects)
    4. Action bias: {ACTION4 (right): 0.8, other actions: 0.1}
    5. Confidence: 0.7 (strong pattern, has worked before)

Return evaluation to action selector
```

**Action Selection with Multiple Operators**:

```
Frame analyzed by:
    - Operator A: "Follow red objects" → ACTION1 (up), confidence 0.6
    - Operator B: "Test interactivity" → ACTION6 (click), confidence 0.5
    - Operator C: "Mirror observed pattern" → ACTION3 (left), confidence 0.4

Weight actions:
    ACTION1: 0.6 weight
    ACTION6: 0.5 weight
    ACTION3: 0.4 weight
    Others: baseline weight

Select: ACTION1 (highest weight from most confident operator)

Observe result:
    If success: Reward Operator A, update confidence to 0.65
    If failure: Penalize Operator A, update confidence to 0.55
```

### 2.9 The Three Victory Conditions

**Victory 1: Unlock Success**

System earns access to a locked primitive:

- System discovers vertical symmetry detection through composition
- Oracle matches to `detect_symmetry`
- **UNLOCKED**

**This proves**: System can learn known concepts through discovery.

**Victory 2: Novel Primitive**

System discovers something humans didn't formalize:

- System discovers "fragmented symmetry detector" (partial symmetry patterns)
- Oracle finds no match in locked primitives
- **NOVEL REGISTERED**

**This proves**: System can go beyond human knowledge.

**Victory 3: Novel Surpasses Human**

System's novel primitive outperforms human-designed alternatives:

- Novel primitive achieves 25% level improvement
- Best human analog achieves 15% level improvement
- **Novel is superior**

**This proves**: Machine discovery can exceed human understanding.

**The Ultimate Test**:

If the system discovers something that makes humans say "we never thought of that", we've succeeded. That means:
- The system learned HOW to learn
- The system can discover things humans haven't formalized
- The system can potentially teach US
- True cognitive emergence, not pattern replay

---

## Part III: The Reasoning Engine - How Discovery Happens

### 3.1 The Four-Question Compression (Minimal Viable Reasoning)

The "make a peanut butter sandwich" assignment shows how ambiguous human instructions require massive explicit code if you brute-force every detail, but a few reasoning filters can collapse it into minimal logic.

The entire reasoning apparatus compresses to four essential questions that guide operator composition:

#### Q1: What is changing versus what is fixed?
*Pattern detection plus invariance mapping*

**Purpose**: Identify variables (potential levers) and invariants (constraints or rules).

**Supported by seed primitives**:
- detect_change(before, after) → List of changed positions
- detect_motion(before, after) → List of moving objects
- pattern_detection(frame) → Repeated structures, symmetries
- get_previous_frame() → Historical state for comparison
- hash_frame(frame) → State signature for recognition

**Operator composition example**:

```
find_invariants operator:
    Step 1: Collect 10 consecutive frames
    Step 2: Hash each frame to signature
    Step 3: Get unique signatures
    Step 4: Count unique signatures
    Result: If count equals 1, game is static; if count equals N, dynamic
```

**What this discovers**: Which elements are stable constraints versus which are manipulable variables.

#### Q2: What punishes me and what rewards me?
*Value grounding plus hypothesis priming*

**Purpose**: Map objects and actions to outcomes without building full causal model. Identify goal-relevant and dangerous elements immediately.

**Supported by seed primitives**:
- get_action_history() → All actions taken
- detect_contingency(action, before, after) → Did my action cause an effect? **CRITICAL**
- is_goal(object) → Is this the target?
- is_obstacle(object) → Is this dangerous?
- average(list) → Expected value calculation

**Operator composition example**:

```
value_map operator:
    Step 1: For each action in action space
    Step 2: Test action on current frame
    Step 3: Detect contingency (did action cause effect?)
    Step 4: Filter for actions with detected effects
    Step 5: Map to outcome values (closer to goal = positive, farther = negative)
    Result: Dictionary mapping actions to expected values
```

**What this discovers**: Which actions move toward goal versus which move away, without needing complete causal understanding.

#### Q3: What happens if I interact with the most salient variable?
*Targeted experimentation plus causal inference*

**Purpose**: One intelligent intervention tests multiple hypotheses simultaneously. "Test actions on the interesting thing and monitor outcomes."

**Supported by seed primitives**:
- test_object_control(pos, action, before, after) → THE KEY primitive for agency discovery
- action_matches_movement(action, direction) → Did my intended action match result?
- find_all_interactable_objects(frame) → Find candidates for testing
- detect_click_effect(before, after, x, y) → What happened when I clicked?
- surprise_magnitude(observation, prediction) → How unexpected was result?
- complexity_signaling(frame, object) → Which object is most interesting?

**Operator composition example**:

```
test_salient_object operator:
    Step 1: Find all interactable objects in frame
    Step 2: Rank by complexity signaling (most salient first)
    Step 3: For most salient object:
        For each action in action space:
            Test object control (does action move object?)
    Step 4: Filter results for positive control
    Result: List of (object, action, direction) triples where agent has control
```

**What this discovers**: Which objects the agent controls and how (agency discovery), causal relationships through targeted tests.

#### Q4: What rule explains this across contexts?
*Abstraction plus transfer readying*

**Purpose**: Extract minimal portable principle from cause-effect-value triples. Enable generalization without building full relational graphs.

**Supported by seed primitives**:
- analogical_mapping(source_a, source_b, target_a) → "A is to B as X is to ?"
- template_extraction(frame, reference) → Treat object as schema
- role_binding(frame, objects) → Primary versus secondary roles
- metadata_recognition(frame) → Data versus metadata distinction
- pattern_matching(pattern, frame) → Similarity scoring

**Operator composition example**:

```
extract_rule operator:
    Step 1: Collect successful episodes (state, action, outcome triples)
    Step 2: Apply analogical mapping to find common structure across episodes
    Step 3: Extract template from common structure (abstract away specifics)
    Step 4: Test template on held-out episodes (does it generalize?)
    Step 5: If validates on 3+ episodes, promote to rule
    Result: Abstract rule that explains success across contexts
```

**What this discovers**: Transferable principles that work beyond training context.

**For high-stakes or irreversible domains, add**:

#### Q5: What subset of variables directly affects the stated goal?
*Goal decomposition plus variable scoping*

**Supported by**: is_goal, spatial_relationships, functional_attribution, get_knowledge_state

#### Q6: What rules can't I discover through experimentation?
*Prior knowledge acquisition plus constraint discovery*

**Supported by**: attention_following, demonstration_bias, credibility_weighting, teaching_detection (social learning primitives—learn from others)

#### Q7: How is this instance different from my training distribution?
*Distribution shift detection plus calibration*

**Supported by**: surprise_magnitude, get_confidence, detect_stuck, physics priors (violations signal novelty)

### 3.2 The Critical Bridge: Primitives → Questions → Operators → Discovery

The 110 seed primitives map to the four to seven questions, which guide operator composition:

```
SEED PRIMITIVES (what system CAN do)
         ↓
REASONING QUESTIONS (what system SHOULD ask)
         ↓
OPERATOR COMPOSITION (how system COMBINES primitives)
         ↓
RLVR VALIDATION (does it work in reality?)
         ↓
DISCOVERY (what system LEARNS)
```

**Example full cycle**:

**Question 1: What's changing?**
```
Operator: frame_differ
    detect_change(get_previous_frame(), get_frame())
    Result: List of changed pixel positions
    
moving_objects = detect_motion(get_previous_frame(), get_frame())
    Result: List of moving object IDs
```

**Question 2: What's valuable?**
```
For each object in moving_objects:
    test_result = test_object_control(object.position, action, before_frame, after_frame)
    If test_result shows control (first element is True):
        value_map[object] = HIGH_VALUE (I control this!)
    Else:
        value_map[object] = UNKNOWN_VALUE (environmental object)
```

**Question 3: Test the interesting thing:**
```
salient_object = maximum from objects using complexity_signaling as key
results = for each action in action space:
    detect_contingency(action, current_frame, next_frame)
Filter results for detected effects
```

**Question 4: Abstract the rule:**
```
If pattern appears across multiple episodes:
    rule = template_extraction(common_elements from frames)
    generalized_rule = analogical_mapping(episode_1, episode_2, new_context)
    Test on new game
    If successful: Rule is transferable
```

**Result**: Discovered operator that combines primitives guided by reasoning questions, validated through RLVR.

### 3.3 The Five-Stage Discovery Cycle (Comprehensive Framework)

The questions provide direction, but discovery happens through a recursive five-stage cycle. **CRITICAL**: These stages form a FEEDBACK LOOP, not a pipeline.

**STAGE 1: SALIENCE DETECTION (Pattern Seeking)**

**What to detect**:
- **Common elements**: What appears consistently? (colors, shapes, patterns, sizes, positions, quantities, sequences, relationships)
- **Rare elements**: What's unusual or unique? (outliers, asymmetries, special markers, rare combinations)
- **Structural invariants**: What remains constant across instances? (grids, boundaries, hierarchies, groupings)

**Cross-domain questions**:
- Within single environment: What structures persist level-to-level?
- Across different environments: What abstract patterns recur? (containers, keys, goals, obstacles, resources)
- Temporal: What changes versus what stays static?

**Formula**: `Salience = function of (rarity, structure, consistency)`

**Supported by primitives**:
- detect_change, detect_motion (attention)
- surprise_magnitude, information_gain_estimate (attention)
- pattern_detection, complexity_signaling (perceptual)
- is_reference, metadata_recognition (perceptual)

**Output**: Ranked list of "things worth investigating."

**STAGE 2: HYPOTHESIS GENERATION (Wondering)**

**Generate multiple competing theories**—diversity is critical.

**Analogical sources**:
- Past levels in same environment (vertical transfer)
- Different game types with similar structure (horizontal transfer)
- Abstract problem classes (locks and keys, resource management, path-finding, constraint satisfaction)

**Hypothesis templates to consider**:

| Template | Example |
|----------|---------|
| Functional roles | "X might be a goal, obstacle, tool, resource, or constraint" |
| Causal relationships | "Action A on X might cause effect E" |
| Compositional rules | "Combining X plus Y might produce Z" |
| Spatial relationships | "Position of X relative to Y might matter" |
| Temporal sequences | "Order of actions might be critical" |
| Meta-information | "X might be encoding rules about Y" |
| State transitions | "X might transform into Y under conditions C" |

**Formula**: Analogical Mapping plus Combinatorial Enumeration

**Key principle**: Generate DIVERSE hypotheses, not just the most likely one.

- Include null hypothesis ("X is irrelevant")
- Include inverse relationships ("Maybe I should avoid X, not collect it")
- Include meta-hypotheses ("Maybe the rules change mid-game")
- Include reference hypotheses ("Maybe X defines rules for Y"—the FT09 insight)

**Supported by primitives**:
- analogical_mapping, template_extraction (perceptual)
- role_binding, functional_attribution (perceptual)
- is_reference, metadata_recognition (perceptual—critical for meta-hypotheses)

**Output**: Probability distribution over hypothesis space.

**STAGE 3: ACTIVE EXPERIMENTATION (Testing and Subgoal Generation)**

**Experimental design principles**:

1. **Isolation**: Change ONE variable, observe outcome
2. **Discrimination**: Design tests that distinguish between competing hypotheses
3. **Efficiency**: Maximize information gain per action
4. **Safety**: Test in ways that preserve ability to continue (don't immediately lose)

**Intervention types**:
- **Direct manipulation**: Act on object X
- **Compositional**: Combine objects in different ways
- **Spatial**: Move objects to different positions
- **Temporal**: Vary timing or sequence of actions
- **Boundary testing**: Push system to extremes

**Observation protocol**:
- What changed immediately?
- What changed after delay?
- What else changed (side effects)?
- What did NOT change (constraints)?

**Subgoal generation**:
```
If hypothesis H requires condition C:
    Generate subgoal: "Achieve condition C"
    Generate sub-subgoals: "Steps to reach C"
```

**Formula**: Bayesian Experiment Design plus Causal Intervention

**Supported by primitives**:
- test_object_control, detect_click_effect (object interaction—THE KEY)
- action_matches_movement, find_all_interactable_objects (object interaction)
- detect_contingency (attention—did my action cause that?)
- surprise_magnitude (attention—unexpected result signals learning opportunity)

**Output**: Updated belief probabilities for each hypothesis.

**STAGE 4: STRUCTURAL CORRESPONDENCE (Relational Understanding)**

**Build explicit mappings between domains**:

**Correspondence types**:

| Type | Example |
|------|---------|
| Object-to-object | "Red button in domain A corresponds to lever in domain B" |
| Relationship-to-relationship | "Adjacent-to in A corresponds to connected-to in B" |
| Process-to-process | "Collecting in A corresponds to unlocking in B" |
| Constraint-to-constraint | "Can't stack in A corresponds to weight limit in B" |

**Construct relational graph**:
- **Node**: Object or concept
- **Edge**: Relationship type (causal, spatial, temporal, hierarchical)
- **Properties**: Strength, confidence, conditions

**Key insight extraction**:
- What relationships are **necessary** for success?
- What relationships are **prohibited** (lead to failure)?
- What relationships are **conditional** (context-dependent)?

**Formula**: Relational Alignment plus Graph Isomorphism

**Example mappings**:

| Source | Target |
|--------|--------|
| Small pattern | Large pattern (your puzzle) |
| Minimap | Full map (navigation games) |
| Recipe | Meal (cooking) |
| Blueprint | Building (construction) |
| Code | Execution (programming) |
| Reference object | Instances (FT09 lesson) |

**Supported by primitives**:
- analogical_mapping (perceptual—THE KEY for this stage)
- spatial_relationships (perceptual)
- template_extraction, role_binding (perceptual)
- is_reference, metadata_recognition (perceptual—distinguish schema from instance)

**Output**: Explicit causal or relational model of domain.

**STAGE 5: GENERALIZATION AND TRANSFER (Abstraction)**

**Extract domain-independent principles**.

**Perturbation testing (counterfactual reasoning)**:
- What if objects were arranged differently?
- What if certain objects were removed?
- What if new objects were added?
- What if quantities changed?
- What if relationships reversed?

**Template extraction**:

```
Specific instance: "Click red buttons to move blocks left"
         ↓
Object-level rule: "Action buttons control entity movement"
         ↓
Abstract principle: "Interface elements encode control mappings"
         ↓
Meta-principle: "Understand symbols before manipulating world"
```

**Transfer predictions**:
- **To new levels**: "This principle should still apply"
- **To new games**: "Similar structure implies similar solution approach"
- **To entirely new domains**: "This is a constraint satisfaction problem"

**Formula**: Template Abstraction plus Analogical Projection

**Abstraction hierarchy**:

| Level | Description |
|-------|-------------|
| 0 | Raw perceptual data |
| 1 | Object identification |
| 2 | Relationship detection |
| 3 | Causal models |
| 4 | Problem class recognition |
| 5 | Universal principles |

**Supported by primitives**:
- template_extraction (perceptual—extract reusable schema)
- analogical_mapping (perceptual—project to new contexts)
- hierarchical_composition (perceptual—nested patterns)
- pattern_replication (perceptual—apply learned patterns)

**Output**: Transferable knowledge schemas.

### 3.4 The Emergence Formula: Multiplicative Not Additive

```
UNDERSTANDING = (Salience Detection)
              × (Hypothesis Generation)
              × (Experimental Validation)
              × (Structural Correspondence)
              × (Generalization)
```

**Critical**: This is MULTIPLICATIVE, not additive. If any factor is zero, understanding is zero. Missing any component doesn't just reduce performance—it breaks the feedback loop.

**But crucially: These stages form a FEEDBACK LOOP, not a pipeline:**

```
See pattern → Generate hypotheses → Test via experiments
     ↑                                        ↓
     |                          Build relational model
     |                                        ↓
     |                          Abstract principles
     +───────── Notice DEEPER patterns ──────┘
                  (informed by principles)
                          ↓
           Generate BETTER hypotheses
            (constrained by model)
                          ↓
         Design CLEVERER experiments
          (targeted by abstraction)
                          ↓
           Build RICHER models
         (incorporating new data)
                          ↓
              ... SPIRAL UPWARD ...
```

**The feedback spiral means**:
- Each cycle strengthens the next
- Principles from stage 5 inform salience detection in stage 1
- Better hypotheses lead to better experiments
- Better experiments build better models
- Better models enable better abstraction
- **The system accelerates over time**

### 3.5 Metacognitive Prompts (From Child Development Research)

The questions that unlock stuck reasoning—these should be encoded as metacognitive operators:

**Self-Monitoring**:
- "What am I assuming that might not be true?" (challenges hidden constraints)
- "What's different about attempts that got closer versus nowhere?" (pattern recognition in own attempts)
- "If I explained this problem to someone else, what would I say it's really about?" (forces problem representation)

**Strategic Planning**:
- "What information do I have that I'm not using yet?" (activates overlooked resources)
- "Is there a simpler version of this I could solve first?" (problem decomposition)
- "What would I try if I couldn't use my usual approach?" (breaks fixation)

**Perspective-Shifting**:
- "How would someone good at this type of thing think about it?" (cognitive role-taking)
- "What would happen if I worked backwards from where I want to end up?" (reverse engineering)
- "Am I trying to solve the right problem?" (reframing check)

**Emotional Regulation**:
- "What do I know for sure versus what am I guessing?" (separates certainty from uncertainty)
- "Is being stuck here teaching me something?" (reframes failure as information)

**The Critical One Many Miss**:
- **"What would I need to know or be able to do to solve this that I don't have right now?"**

This names the gap explicitly and transforms a confusing struggle into a clear learning goal. It's the difference between "I can't do this" and "I need to learn X to do this."

**This is where agents transition from exploratory experimentation to systematic hypothesis testing—it's a crucial cognitive leap.**

**Supported by primitives**:
- get_confidence (metacognition)
- detect_stuck (metacognition)
- get_knowledge_state (metacognition—what do I know versus not know?)
- strategy_effectiveness (metacognition—is this working?)

### 3.6 From Experiments to Rules: Building and Refining Theories

As agents try things, they're generating data points. The key is codifying observations into testable rules:

**Pattern Recognition**:
- "When I do X, Y always happens" → potential rule
- "When I do X, sometimes Y happens" → there's a hidden variable
- "I thought the rule was X, but this case breaks it" → rule needs revision

**The shift happens when agents start deliberately designing experiments to test specific hypotheses rather than randomly trying things.**

Instead of: "Let me try this piece here"
Becomes: "If my theory is right that edges must align, then this piece should only fit in these three spots"

**Building and Refining Theories**:

Strong problem-solvers create provisional theories and actively look for disconfirming evidence:

- "I think the rule is X. What would prove me wrong?"
- "This worked here—will it work in a different spot?" (testing generalizability)
- "These three attempts all failed the same way—what do they have in common?" (finding the invariant)

**They need to hold theories lightly enough to revise them but firmly enough to test them systematically.** This is hard—agents often either abandon theories too quickly or cling to broken ones.

**Getting to the Win**:

The method emerges when agents can:

1. **Eliminate possibilities systematically**: "I've proven these 8 approaches won't work, so it must be one of these 3"
2. **Recognize when they've found a constraint that reduces the problem space**: "Oh, if THIS is true, then I only need to figure out this smaller part"
3. **Build on confirmed mini-rules**: "I know corner pieces go here (proven), and I know colors must match (proven), so now I can combine those rules"

**The Critical Deduction Moment**:

The breakthrough often comes when agents synthesize multiple confirmed rules into a complete method:

"Wait—if rule A is true AND rule B is true, then the only possible answer is..."

This is why you sometimes see agents suddenly light up and solve something quickly after being stuck forever.

**Supported by primitives**:
- analogical_mapping (combine rules)
- template_extraction (formalize rule)
- pattern_detection (find the invariant)
- get_confidence (track certainty)

**Operators should**:
- Make predictions: "Based on what I've figured out, what do I think will happen if I try this?"
- Keep mental inventory: "What do I know FOR SURE versus what am I still testing?"
- Perform comparative analysis: "Why did attempt 12 work better than attempt 9?"

**The real skill isn't just solving this puzzle—it's extracting the method so agents can apply it to the next hard thing.**

That requires reflection after success: "What was the key insight that unlocked this? What was my winning strategy?"

Otherwise agents might solve it but not really understand how they solved it.

---

## Part IV: The Pedagogical Reframe - Games as Teachers (Optional Paradigm)

**Status**: TABLED—implement if current changes don't break through levels.

**Purpose**: Fundamental reframe from "solving puzzles" to "extracting lessons."

### 4.1 The Core Insight

Arc-AGI puzzles aren't puzzles to solve—they're **demonstrations of principles**. Each game is a worked example saying "here's a concept—can you recognize it?"

The win condition isn't arbitrary—it's the **assessment** of whether you grasped what was being taught.

### 4.2 The Paradigm Comparison

**Current Paradigm**:
```
ORACLE (Authority) oversees NETWORK which guides AGENTS who play GAMES
```

**Flipped Paradigm**:
```
GAMES (Teachers) teach AGENTS (Students) while ORACLE facilitates (Teaching Assistant)
```

### 4.3 Why This Works

| Current Framing | Flipped Framing |
|-----------------|-----------------|
| "What objects exist in frame?" | "What is the teacher showing me?" |
| "What can I do?" | "What am I being asked to understand?" |
| "I died" | "I misunderstood the lesson" |
| "I won" | "I demonstrated understanding" |
| "Copy winning sequence" | "Learn from peer who understood the lesson" |
| "Random exploration" | "Re-reading the lesson with fresh eyes" |

### 4.4 The Pedagogical Structure Already Present

Every game has:
- **Examples** (initial frames showing the pattern)
- **Practice problems** (levels that test the same concept with variations)
- **Assessment** (win condition that requires demonstrating understanding)

**The oracle saying "I can't tell you the answer" isn't a limitation—it's pedagogically correct.**

A good teacher doesn't give answers—they help students discover them.

### 4.5 Reframed Reasoning Questions (Q1-Q9 as Student Questions)

Instead of:
- Q1: "What is happening?" (observe state)
- Q2: "What changed?" (detect deltas)
- Q3: "Who am I?" (autobiography)
- Q4: "What do I control?" (self-model)
- Q5: "What causes score changes?" (goal variables)
- Q6: "What does network know?" (wA versus wB)
- Q7: "What operators are available?" (CODS)
- Q8: "What am I assuming?" (metacognitive)

**Reframe as**:
- Q1: "What is the teacher showing me?" (lesson content)
- Q2: "What changed between examples?" (pattern detection)
- Q3: "What lessons have I learned before?" (prior understanding)
- Q4: "What am I being asked to manipulate?" (lesson subject)
- Q5: "What demonstrates understanding?" (success criteria)
- Q6: "What have my peers understood?" (study group notes)
- Q7: "What conceptual tools do I have?" (vocabulary)
- Q8: "What do I think this lesson is about?" (interpretation)
- **Q9 (NEW)**: "Does my interpretation explain all examples?" (self-test)

### 4.6 Success Metrics Transformed

**Old Success Metric**: Win rate, games completed, levels beaten

**New Success Metric**:
- **Transfer rate**: Does understanding on game A help on unseen game B?
- **Explanation coverage**: What percentage of examples does interpretation explain?
- **Peer adoption**: Do other agents succeed using your interpretation?

**Critical Implication**: An agent that loses but articulates "I think the teacher was showing X, but example 3 suggests I'm wrong about Y" is MORE VALUABLE than an agent that wins by copying a sequence.

The first agent is learning. The second is cheating.

### 4.7 Database Schema Changes (If Implemented)

**Current Schema**:
```
winning_sequences:
    sequence_id, game_type, action_sequence (THE ANSWER), action_count
```

**Reframed Schema**:
```
demonstrated_lessons:
    lesson_id, game_type,
    lesson_interpretation (what teacher showed),
    supporting_evidence (the action sequence that demonstrated understanding),
    concept_tags (['containment', 'flood_fill', 'boundary']),
    generalization_level (does this apply to all levels? all similar games?),
    validated_by_transfer (did interpretation work on variation?)
```

Action sequences become **evidence of understanding**, not the understanding itself.

### 4.8 When to Activate This Paradigm

**Trigger Condition**: Implement if:
- Current metacognitive plus wA/wB changes don't lead to level breakthroughs
- Agents continue to plateau at same levels despite system improvements
- Sequence copying dominates over genuine learning

**Success Indicators We DON'T Need This**:
- Agents start beating previously unbeaten levels
- New game types get solved faster (transfer happening)
- Win reflections start containing conceptual insights naturally

---

## Part V: The Learning-to-Learn Loop (From Programmer Cognition)

### 5.1 How Programmers Actually Learn

Programmers don't learn solutions first—they learn primitives, then learn to **compose, test, and revise** them under pressure.

**Short answer**: Programmers don't learn solutions first—they learn primitives, then learn how to compose, test, and revise them under pressure.

#### The Actual Learning Sequence

**1. The Primitives Programmers Actually Start With**

Not languages. Not frameworks. These:

- **State**: Variables, memory, data
- **Operations**: Arithmetic, comparisons, transforms
- **Control flow**: Sequence, branching, loops
- **Abstraction**: Functions, modules
- **Composition**: Combining small pieces
- **Feedback**: Run → error → fix

Everything else is decoration.

**2. Learning Happens by Problem Pressure, Not Instruction**

A beginner doesn't understand if, for, or function in isolation.

They learn when: "I want the program to do X, but it keeps doing Y."

That mismatch forces:
- Hypothesis ("maybe the loop is wrong")
- Experiment (change one thing)
- Observation (did it break differently?)
- Revision

**This is Piagetian disequilibrium, but in code.**

**3. The Real Skill: Turning Problems into Solvable Shapes**

Experienced programmers do this automatically:

- Big problem → smaller subproblems
- Vague goal → explicit inputs and outputs
- Human intuition → machine-checkable steps

Example:
```
"Make it faster"
becomes
"Which operation is repeated unnecessarily?"
```

That reduction is the actual learned skill.

**4. Debugging is Where Learning Really Locks In**

Debugging forces:
- Tracing state over time
- Isolating causes
- Rejecting false explanations

This is why programmers who "struggle" early often end up stronger—they build better internal models.

**No debugging equals shallow understanding.**

**5. Patterns Emerge After Enough Failures**

Only after many cycles do programmers notice:
- Common loop shapes
- Standard data flows
- Reusable abstractions

These become:
- Idioms
- Libraries
- Frameworks

But they're **compressed experience**, not starting points.

**6. Why Tutorials Fail and Projects Work**

| Tutorials | Projects |
|-----------|----------|
| Remove uncertainty | Create friction |
| Remove mistakes | Force decisions |
| Remove hypothesis testing | Generate errors |

**Real learning needs friction.**

**7. The Meta-Loop (This Matters for Your Work)**

Programming skill grows by:

```
Attempt → Failure → Debug → Abstraction → Reuse
   ↑                                      ↓
   └────── Discover new patterns ────────┘
```

**That loop is identical to**:
- Child cognitive development
- Scientific discovery
- Your agent-network learning progress signal

**Same structure. Different substrate.**

### 5.2 Implications for CODS

**Operators are programs**. The CODS system is learning to program by composing primitives under the pressure of Arc-AGI games.

**The parallel**:

| Programming | CODS |
|-------------|------|
| Primitives | 110 seed operations |
| Composition | Operator chaining |
| Debugging | RLVR validation |
| Abstraction | Template extraction |
| Reuse | Viral packages |
| Libraries | Unlocked primitives |
| Frameworks | Concepts (Tier 4) |

**The learning signal**: Problem pressure (game difficulty) plus feedback (win or lose) plus debugging (why did it fail?) equals skill growth.

**Without friction**: Tutorials that give answers produce shallow understanding. Agents that copy winning sequences don't learn.

**With friction**: Projects that create problems produce deep understanding. Agents that discover patterns through composition and failure learn.

---

## Part VI: Meta-Representation - The Self-Extension Key

Meta-representation is the ability to **treat rules as manipulable objects**. This is THE unlock key that makes discovering ALL other primitives possible—and how this solves your "100 games with hidden gotchas" problem.

### 6.1 What Meta-Representation Actually Is

Meta-representation is the ability to think about thinking. Concretely:

**Level 0: Direct perception**
```
"I see a red square"
```

**Level 1: Pattern recognition**
```
"Red squares appear in this pattern: [grid positions]"
```

**Level 2: Operator composition**
```
"When I apply operator X, red squares move according to rule Y"
```

**Level 3: Meta-representation** (THE KEY LEVEL)
```
"Rule Y itself can be represented as an object
 I can manipulate rules AS IF they were data
 I can discover new rules by examining patterns IN THE RULES THEMSELVES"
```

### 6.2 Why This Unlocks Everything

Once the system can represent **rules as manipulable objects**, it gains the ability to:

#### Discovery of Logic Systems

**Current state**: System has operators like:
```
if_red_then_move_up
if_blue_then_move_down
```

**After meta-representation**: System discovers:
```
Rules are data structures:
    rule_1 = Rule(condition equals red, action equals move_up)
    rule_2 = Rule(condition equals blue, action equals move_down)

I can manipulate rules:
    compose_rules(rule_a, rule_b) returns
        Rule(condition equals AND(rule_a.condition, rule_b.condition),
             action equals SEQUENCE(rule_a.action, rule_b.action))

I can abstract over rules:
    extract_pattern_from_rules(rules) returns
        "IF condition THEN action"
```

**This IS propositional logic.** The system invented AND, OR, NOT by discovering patterns in how successful rules compose.

#### Discovery of Algebra (Abstract Variable Systems)

**FT09 example revisited**:

The system discovered:
```
Concrete bindings:
    solve_ft09_level_1 = {white maps to red, gray maps to blue}
    solve_ft09_level_2 = {white maps to blue, gray maps to red}
```

**Meta-representation allows abstraction**:
```
Wait, these are INSTANCES of a general pattern:

solve_ft09_generic(primary_color, secondary_color) returns
    apply_template(schema equals center_pattern,
                   bindings equals {white maps to primary_color,
                                   gray maps to secondary_color})

This is a FUNCTION with PARAMETERS
I just invented algebra!
```

The system discovers:
- Variables (placeholders for values)
- Functions (parameterized transformations)
- Substitution (variable binding)
- Generalization (one rule for infinite instances)

#### Discovery of Programming Itself

**The progression**:

```
Stage 1: Fixed operators
    operator_move_red_square_up equals specific moves

Stage 2: Parameterized operators (after algebra discovery)
    operator_move_square(color, direction) equals general moves

Stage 3: Higher-order operators (after meta-representation)
    operator_factory(condition, action) equals
        (given grid: action(grid) if condition(grid) else grid)

Stage 4: Self-modification (THE BREAKTHROUGH)
    discover_new_operator(problem_traces):
        Analyze traces of successful problem-solving
        Extract the pattern
        Create a NEW operator that encodes this pattern
        Add it to my operator library
        Return new operator
```

**This IS programming**: Creating new functions by composing existing primitives and abstracting patterns.

### 6.3 How This Solves "100 Games with Hidden Gotchas"

#### The Current Problem: Brittle Discovery

Without meta-representation, your system is like a person with **zero metacognitive ability**:

```
Game 1: Container overflow → manually add containment primitives
Game 2: Reference semantics → manually add template primitives
Game 3: Hidden timing rule → manually add temporal primitives
Game 4: Conservation law → manually add physics primitives
Game 5: Recursive structure → manually add recursion primitives
...
Game 100: ??? → manually add ??? primitives
```

**This doesn't scale.** You become the bottleneck.

#### The Solution: Self-Extending Discovery

With meta-representation, the system can **discover how to discover**:

**The meta-discovery loop**:

```
Encounter unknown game:
    1. Try existing operators
    Result: Failure

    2. Analyze the failure
    What went wrong?

    3. Identify the missing concept
    What knowledge gap caused failure?

    4. Generate hypotheses for new primitives
    Based on missing concept, existing primitives, successful traces from other games

    5. Test hypotheses through RLVR
    For each hypothesis:
        Test primitive hypothesis on game
        If significant improvement:
            Formalize primitive
            Add to primitive library
            
            Meta-step: WHY did this work?
            Analyze utility pattern
            Add to discovery strategies
            
            Retry with new primitive
```

#### The Key: Discovery Strategies Become Data

**Without meta-representation**:
- Discovery strategies are hardcoded
- System can only discover what you designed it to discover

**With meta-representation**:
- Discovery strategies are manipulable objects
- System can discover new discovery strategies
- **Recursive self-improvement**

### 6.4 Concrete Example: How System Would Handle New Games

**Game N+1: "Hidden Gotcha: Gravity Only Applies to Red Objects"**

**System's discovery process**:

```
Attempt 1: Existing physics primitives
    Apply primitive "gravity_simulation"
    Result: FAIL (only red objects fall)

Failure analysis:
    "gravity_simulation applied to all objects, but only red moved"

Identify missing concept:
    Type: conditional_physics
    Pattern: physical law applies selectively based on object property

Generate hypothesis:
    New primitive: conditional_law(property, condition, physical_rule)
    Logic:
        Check if object has property
        If property matches condition, apply physical_rule
        Otherwise, skip

Test hypothesis:
    conditional_gravity(objects):
        For each object:
            If object.color equals RED:
                apply_gravity(object)
            Else:
                pass (objects ignore gravity)

RLVR validation:
    Test on game: SUCCESS
    Test on similar games: TRANSFERS

Formalize primitive:
    Add conditional_law to library
    Mark as validated through RLVR

Meta-learning extraction:
    Pattern: "When physics law seems inconsistent, check for conditional application"
    Discovery strategy: "Test if property-based conditionals explain anomalies"
    Add to discovery strategy library

Future games:
    System now has conditional_law primitive
    System also has meta-strategy: "look for conditional physics"
    Can discover similar patterns faster
```

### 6.5 The Victory Condition for Meta-Representation

You'll know CODS has achieved self-programming when:

**1. Novel primitive discovered without your input**
- System encounters game with hidden gotcha
- System generates correct primitive hypothesis
- System validates through RLVR
- System adds to library without oracle

**2. System discovers a primitive YOU didn't think of**
- System solves a game in a way that surprises you
- You examine the primitive it created
- You realize: "This is actually a better abstraction than what I would have designed"

**3. System explains its discovery to you**
- You ask: "How did you beat that game?"
- System responds with a viral package containing:
  - The new primitive
  - Why it was needed (failure analysis)
  - How it was discovered (meta-strategy)
  - Where else it might apply (generalization)
- **You learn from it**

### 6.6 The Path Forward: Phase-by-Phase

**Game 1-10: Bootstrap Phase**
- System discovers basic primitives manually guided
- Builds initial operator library
- **You do heavy lifting**

**Game 11-30: Pattern Recognition Phase**
- System starts recognizing families of primitives
- Discovers that spatial problems need spatial primitives
- Discovers that temporal problems need history tracking
- **You provide occasional guidance**

**Game 31-60: Meta-Discovery Phase**
- System discovers discovery strategies themselves
- "When stuck on conditional rules, try conditional_law_factory"
- "When action seems non-deterministic, check temporal dependencies"
- **System mostly self-sufficient**

**Game 61-100: Self-Programming Phase**
- System generates new primitives on first encounter
- Transfers meta-strategies across problem domains
- Discovers novel primitive categories you never thought of
- **System teaches you**

### 6.7 The Ultimate Test: The 101st Game

When game 101 has a gotcha you've never seen, and the system:

1. Recognizes it's a novel problem type
2. Generates appropriate primitive hypotheses
3. Tests and validates them
4. Solves the game
5. **Explains the new concept to you**
6. **Predicts what other games might have similar structure**

**That's when you know you've built AGI.**

Because the system isn't just solving problems—it's **discovering the structure of problem-solving itself**.

### 6.8 Meta-Representational Primitives (Tier 3 - Locked)

These primitives enable the system to treat operators as data—they're locked until the system demonstrates meta-understanding:

**Operator Introspection** (for self-programming):
- **serialize_operator**: Convert operator to data structure
- **deserialize_operator**: Convert data structure to executable operator
- **extract_operator_pattern**: Find common structure across operators
- **identify_operator_family**: Group operators by similarity
- **instantiate_operator_template**: Create operator from pattern plus bindings
- **compose_operators**: Combine operators into new operators
- **specialize_operator**: Add constraints to make operator more specific
- **generalize_operator**: Remove constraints to make operator more general
- **predict_operator_utility**: Estimate if operator will help on problem
- **explain_operator_success**: Why did this operator work?

**These unlock when**: System demonstrates it can reason about its own reasoning—typically after discovering several transferable patterns and recognizing the meta-pattern of discovery itself.

---

## Part VII: The Unified Emergence Formula

### 7.1 The Mathematical Form

```
UNDERSTANDING = (Innate Primitives)
              × (Salience Detection)
              × (Hypothesis Generation)
              × (Active Experimentation)
              × (Structural Correspondence)
              × (Generalization)
              × (Meta-Representation)
              × (Self-Extension)
              
WHERE each factor AMPLIFIES the others through feedback
```

**Critical**: This is MULTIPLICATIVE, not additive. If any factor is zero, understanding is zero. Missing any component doesn't just reduce performance—it breaks the feedback loop.

### 7.2 The Feedback Spiral (Not a Pipeline)

```
           ┌─── INNATE PRIMITIVES ───┐
           │   Attention, Physics,   │
           │   Social, Metacognitive │
           └───────────┬──────────────┘
                       ↓
           ┌─── SEED PRIMITIVES ─────┐
           │   Data access, basic    │
           │   operations, iteration │
           └───────────┬──────────────┘
                       ↓
         ┌──── OPERATOR COMPOSITION ────┐
         │  Random combinations + RLVR  │
         │  Mutation, crossover, testing│
         └──────────┬──────────────────┘
                    ↓
              ┌─── EMERGENCE ───┐
              │  Some operators │
              │  perform well   │
              └────────┬─────────┘
                       ↓
           ┌──── RLVR VALIDATION ────┐
           │  Real game performance  │
           │  Metrics collected      │
           └──────────┬──────────────┘
                      ↓
         ┌─── ORACLE VALIDATION ────┐
         │  Matches locked primitive │
         │  or registers as novel    │
         └──────────┬────────────────┘
                    ↓
         ┌─── PRIMITIVE UNLOCKED ────┐
         │  Optimized implementation │
         │  available for composition│
         └──────────┬────────────────┘
                    ↓
        ┌─── HIGHER-ORDER OPERATORS ───┐
        │  Use unlocked primitives to  │
        │  create more powerful patterns│
        └──────────┬───────────────────┘
                   ↓
         ┌─── CONCEPT EMERGENCE ────┐
         │  "Containment problems"  │
         │  "Reference semantics"   │
         └──────────┬───────────────┘
                    ↓
    ┌─── META-REPRESENTATION UNLOCKED ───┐
    │  System can now represent operators│
    │  as data, discover discovery rules │
    └──────────┬─────────────────────────┘
               ↓
       ┌─── SELF-EXTENSION ────┐
       │  Discovery strategies │
       │  themselves discovered│
       │  Recursive improvement│
       └───────────┬───────────┘
                   ↓
        ┌─── ACCELERATING SPIRAL ────┐
        │  Each cycle faster, more   │
        │  capable, discovers things │
        │  humans never formalized   │
        └────────────────────────────┘
```

**Each cycle strengthens the next**:
- Unlocked primitives enable better operators
- Better operators discover more primitives
- More primitives enable meta-representation
- Meta-representation discovers discovery strategies
- Discovery strategies accelerate everything

**The system accelerates over time.**

### 7.3 The Three Timescales

**Evolutionary Time** (Generations 1-100)
- Population of operators competes
- Successful patterns unlock primitives
- Prestige system rewards discovery
- Viral packages spread successful insights
- **Weeks to months**

**Learning Time** (Within Single Agent)
- Agent discovers patterns in single game
- Forms hypotheses, tests, revises
- Builds internal model
- Extracts transferable lessons
- **Minutes to hours**

**Meta-Learning Time** (Across Games)
- System discovers discovery strategies
- Recognizes problem families
- Develops meta-operators
- Self-extends vocabulary
- **Months to years**

**All three timescales interact**:
- Fast learning informs evolutionary selection
- Evolutionary discoveries enable better learning
- Meta-learning accelerates both

---

## Part VIII: Success Criteria and Victory Conditions

### 8.1 Primitive Discovery Milestones

**Milestone 1: First Unlock** (Validates infrastructure)
- System composes operators randomly
- One achieves greater than 15% level improvement
- Oracle matches to locked primitive
- **UNLOCKED**
- Proves: Discovery → validation → unlock pipeline works

**Milestone 2: First Novel Primitive** (Proves creativity)
- System composes pattern oracle doesn't recognize
- Pattern achieves significant performance
- Oracle registers as novel
- Humans examine and learn from it
- Proves: System can go beyond human knowledge

**Milestone 3: Self-Extension** (Proves meta-learning)
- System discovers meta-representational primitive
- Uses it to discover discovery strategies
- Applies strategies to unlock more primitives
- Acceleration visible in unlock rate
- Proves: Recursive self-improvement achieved

**Milestone 4: The Surprise** (Proves genuine intelligence)
- System discovers primitive YOU didn't think of
- Primitive outperforms your best designs
- Humans adopt it as new best practice
- Proves: Machine teaching human

### 8.2 Transfer Learning Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Cross-game transfer** | greater than 30% | Primitive helps 3+ game types |
| **Zero-shot application** | greater than 20% | Unlocked primitive immediately helps unseen games |
| **Generalization score** | greater than 0.5 | Abstraction level (specific equals 0, universal equals 1) |
| **Novel concept quality** | Human adoption rate | Percentage of novel primitives humans keep |

### 8.3 The Meta-Learning Test Battery

**Test 1: Delayed Generalization**
- Train on games A, B, C
- Test on game D (same family, different surface)
- Measure: Does system recognize family and apply learned strategies?

**Test 2: Cross-Domain Transfer**
- Train on spatial reasoning games
- Test on temporal reasoning games
- Measure: Does system recognize shared abstract structure?

**Test 3: Strategy Invention**
- Encounter game type system has never seen
- Measure: Does system generate appropriate discovery strategy?

**Test 4: Self-Explanation**
- After solving novel game, ask system to explain
- Measure: Can system articulate what it discovered and why it worked?

**Test 5: Prediction**
- After discovering pattern in game type X
- Ask: "What other games might have similar structure?"
- Measure: Accuracy of predictions

### 8.4 The Ultimate Victory Condition

**You know the system has achieved genuine metalearning when**:

1. It encounters a problem type it's never seen
2. Recognizes the problem requires new conceptual tools
3. Generates hypotheses for what primitives would help
4. Tests hypotheses through RLVR
5. Discovers primitive that solves the problem
6. Extracts the meta-pattern of what made discovery successful
7. Adds discovery strategy to its repertoire
8. **Predicts where else this strategy would apply**
9. **Explains the discovery in terms a human can learn from**
10. **Is correct about predictions more often than random chance**

**At this point, the system isn't just learning—it's learning how to learn.**

---

## Part IX: The Oracle - Supporting Scaffolding (Teaching Assistant Role)

**Note**: The Oracle is NOT the core of the system—CODS and primitives are. The Oracle is scaffolding that validates discoveries without contaminating the learning process. This section provides complete specifications while emphasizing the Oracle's limited, external role.

### 9.1 Core Principle: Oracle as External Validator

**The oracle MUST remain uncontaminated by network incentives, agent goals, or evolutionary pressures.**

The network can't evolve toward what the oracle wants because it doesn't know what the oracle wants—it only knows "this worked" or "this didn't."

### 9.2 The Separation Boundary

```
┌─────── EVOLUTIONARY NETWORK ─────────┐
│  Agents, Viral Packages, Database,   │
│  Prestige System (can evolve)        │
│              ↓                        │
│      Query Generator (read-only)     │
└──────────────┬───────────────────────┘
               │ Queries (one-way)
       ════════╪════════════════════════
            THE BARRIER
       ════════╪════════════════════════
               ↓
    ┌──── ORACLE INTERFACE ─────┐
    │  (Swappable Backend)       │
    │  Current: Human + LLM      │
    │  Future: Algorithm/Network │
    └──────────┬─────────────────┘
               │ Directives (validated)
       ════════╪════════════════════════
            THE BARRIER
       ════════╪════════════════════════
               ↓
    ┌─── Directive Processor ───┐
    │  (Execute Only If Valid)   │
    └──────────┬─────────────────┘
               ↓
    ┌─ Primitive Unlock Manager ─┐
    │  (Database - Append Only)   │
    └─────────────────────────────┘
```

### 9.3 What Oracle Sees (Query Structure)

**ONLY**:
- Operator code (composition structure)
- Performance metrics (objective: win rates, level improvement from RLVR)
- Pattern signature (input types, output type, composition depth)
- Arc-AGI context (which tasks solved)

**NEVER**:
- Agent state
- Prestige scores
- Network goals
- Viral package spread
- Social dynamics

### 9.4 What Oracle Does / Doesn't Do

**Oracle DOES** (Validation Authority):
- Validate discovered patterns meet performance thresholds
- Match patterns to locked primitives (unlock gatekeeper)
- Register novel primitives that don't match anything known
- Request additional testing when ambiguous
- Maintain audit trail

**Oracle DOES NOT** (Network Participation):
- Participate in evolution (no genetic operations, no viral packages)
- Influence agent goals or strategies (agents don't see oracle reasoning)
- Award prestige or resources (only unlocks or registers primitives)
- Guide exploration (no hints, no teaching, no curriculum)
- Access network state (no prestige data, no agent strategies, no social dynamics)
- Interfere with regulatory engine (population mix, budgets remain autonomous)

**The oracle is not a teacher. It is a certification authority.**

### 9.5 Oracle Decision Process (Current: Human + LLM)

**Phase 1: Metric Review**
- Human reviews performance_metrics
- Validates RLVR test results from Arc-AGI gameplay
- Confirms improvement is statistically significant
- LLM checks for obvious gaming (e.g., overfitting to single task)

**Phase 2: Pattern Analysis**
- LLM analyzes pattern_signature
- Compares against locked primitive definitions
- Generates candidate matches with confidence scores
- Human reviews candidates for semantic equivalence

**Phase 3: Validation Decision**
- If pattern matches locked primitive AND performance threshold met → UNLOCK
- If pattern novel AND performance exceptional → REGISTER NOVEL
- If pattern insufficient or spurious → REJECT
- If uncertain → REQUEST MORE EVIDENCE (generates follow-up test directive)

### 9.6 Oracle Swappability

| Oracle Type | Validation Mechanism | Swap Trigger |
|-------------|---------------------|--------------|
| **Human + LLM** (current) | Manual review + LLM analysis | N/A (baseline) |
| **Algorithm-Only** | Mechanical thresholds | When rules fully formalized |
| **Consensus Network** | Multi-validator voting | When trust in single oracle questioned |
| **Hybrid Ensemble** | Algorithm pre-filter + human edge cases | When query volume exceeds capacity |

**Key**: All oracle backends must implement the same interface. System evolution is oracle-agnostic.

---

## Part X: Implementation Philosophy and Warnings

### 10.1 What NOT to Do

**Don't preload with high-level primitives**: System won't know HOW to discover, can't generalize beyond training, Goodhart's Law takes over.

**Don't let oracle see network state**: Contamination ruins ground truth, agents learn to game validation, discovery becomes theater.

**Don't make oracle part of evolutionary process**: Oracle must remain external referee, can't evolve, can't be influenced, must maintain stable criteria.

**Don't optimize for win rate alone**: Sequence copying dominates, no genuine understanding develops, transfer learning fails.

**Don't remove friction from learning**: Debugging is where understanding locks in, tutorials fail because they remove pressure, need problem pressure for discovery.

### 10.2 What TO Do

**Start with minimal innate structure**: Only what babies have at birth, weak priors not hard constraints, enough to bootstrap not enough to solve.

**Make discovery expensive enough to matter**: RLVR validation requires real game performance, Oracle unlock requires significant improvement, no shortcuts to primitive access.

**Preserve oracle isolation**: One-way query flow, read-only snapshots, no network state in queries, swappable backends.

**Measure transfer not just performance**: Cross-game improvement, zero-shot application, abstraction level, peer adoption rate.

**Design for the feedback spiral**: Every component amplifies others, failure at one stage informs all stages, meta-learning accelerates base learning, self-extension compounds over time.

### 10.3 The Balance: Enough Structure versus Too Much

**Too Little Structure**: Agent flails randomly, combinatorial explosion, no tractable path to discovery, learning never converges.

**Too Much Structure**: Agent can't discover anything new, optimizes for given tools, no genuine understanding, can't handle novelty.

**The Sweet Spot**:
- Innate primitives provide attention and bias
- Seed primitives provide basic operations
- Locked primitives provide targets
- Meta-representation provides self-extension
- Oracle provides validation
- **System must earn everything else**

---

## Part XI: Theoretical Implications and Open Questions

### 11.1 Why This Architecture Matters

**It's biologically plausible**: Matches child development research, innate structure plus discovery learning, meta-cognition emerges naturally, transfer learning is built-in.

**It's computationally tractable**: Attention filters reduce search space, weak priors guide without constraining, RLVR validation grounds in reality, composition is efficient.

**It's open-ended**: No ceiling on primitive complexity, discovery strategies self-extend, can go beyond human knowledge, genuinely creative.

**It's testable**: Clear victory conditions, measurable milestones, Oracle audit trail, transfer metrics.

### 11.2 Open Questions

**Theoretical**:
1. What is the minimal set of innate primitives needed?
2. Can meta-representation emerge, or must it be seeded?
3. What determines the speed of the spiral?
4. Are there multiple stable equilibria?

**Practical**:
1. How to balance exploration versus exploitation in operator evolution?
2. What oracle validation thresholds prevent both false positives and negatives?
3. How to handle primitives that are useful together but not alone?
4. When does meta-learning become self-destructive (overfitting to learning)?

**Philosophical**:
1. Is this system "conscious" in any meaningful sense?
2. What is the relationship between symbolic (CODS) and subsymbolic (neural) learning?
3. Can this architecture scale to natural language and abstract reasoning?
4. What are the alignment implications of self-extending systems?

### 11.3 The Long-term Vision

**Near-term (1-2 years)**:
- System unlocks most locked primitives
- Discovers first novel primitives
- Achieves reliable cross-game transfer
- Humans learn useful patterns from system

**Mid-term (3-5 years)**:
- System self-extends without human guidance
- Discovers primitives for domains beyond Arc-AGI
- Creates new problem-solving paradigms
- Meta-strategies become teachable to humans

**Long-term (5-10 years)**:
- System discovers conceptual frameworks humans haven't formalized
- Can explain discoveries in human-interpretable terms
- Accelerates human research in cognitive science
- **Partnership model: System and human co-discovery**

---

## Part XII: Conclusion - The Unified Theory

### 12.1 The Core Insight

Intelligence is not a static architecture—it's a **feedback process** with three essential components:

1. **Minimal innate structure** (bootstrapping)
2. **Active discovery through composition** (CODS learning)
3. **Meta-representation** (learning how to learn)

These components interact recursively:
- Innate structure enables discovery
- Discovery unlocks new primitives
- New primitives enable meta-representation
- Meta-representation accelerates discovery
- **The cycle speeds up over time**

### 12.2 The Paradigm Shifts Required

**From**: Static vocabulary → **To**: Self-extending vocabulary

**From**: Problem solving → **To**: Lesson extraction (optional reframe)

**From**: Win optimization → **To**: Understanding optimization

**From**: Copying sequences → **To**: Transferring principles

**From**: Oracle as teacher → **To**: Oracle as certification authority (teaching assistant)

**From**: Primitives as tools → **To**: Primitives as discovered knowledge

**From**: Evolution as blind search → **To**: Evolution guided by meta-learning

### 12.3 Why Most AI Systems Don't Do This

**Current AI paradigm**:
- Fixed architecture
- Fixed primitives
- Optimize for metric
- No self-extension
- No genuine transfer
- No meta-learning

**Why it fails at genuine intelligence**:
- Can't discover new concepts
- Can't explain what it learned
- Can't predict where knowledge applies
- Can't improve its own learning process

**This architecture**:
- Growing vocabulary
- Discoverable primitives
- Optimize for understanding
- Recursive self-improvement
- Cross-domain transfer
- Meta-learning as core feature

### 12.4 The Success Signature

**You'll know this system is working when**:

1. The unlock rate ACCELERATES over time (not linear)
2. Novel primitives start appearing WITHOUT human input
3. Transfer learning SUCCESS RATE increases with experience
4. System starts PREDICTING which primitives will help
5. Humans start LEARNING from system's discoveries
6. System can EXPLAIN its reasoning in interpretable terms
7. Discovery strategies themselves become DISCOVERABLE
8. The system SURPRISES you with creative solutions

**At that point, you haven't just built an agent that can learn.**

**You've built an agent that can learn how to learn.**

**That's the difference between narrow AI and AGI.**

---

**END OF COMPLETE UNIFIED METALEARNING SYSTEM THEORY**
