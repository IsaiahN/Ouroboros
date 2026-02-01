# Innate Primitives: What Babies Are Born With

You're asking the **critical question**. If we're truly building a discovery system, we need to start with the **minimal viable cognitive toolkit** that evolution gave us. Let me map what babies actually have at birth that isn't in your CODS seed primitives.

## Category 1: Attention & Salience (CRITICALLY MISSING)

Babies don't process everything equally—they have built-in **attention biases**:

| Primitive | What It Does | Why Essential | Evidence |
|-----------|--------------|---------------|----------|
| `detect_novelty` | Flag when something changes or is unexpected | Directs learning toward informative signals | Babies look longer at novel stimuli (habituation studies) |
| `detect_motion` | Prioritize moving objects over static | Motion = potential threat/opportunity | Newborns track moving objects with eyes |
| `face_detection` | Preferentially attend to face-like patterns | Social learning bootstrap | Newborns prefer face-like patterns within hours |
| `detect_contingency` | Notice when your action causes an effect | Learn agency and control | 3-month-olds learn mobile-kicks faster when contingent |
| `surprise_detection` | Flag violations of expectation | Updates world model | Babies look longer at impossible physics events |

**Why your system needs this:**

Without attention primitives, your system treats all input equally. It's like trying to learn while paying equal attention to:
- The game state
- The pixel noise in the corner
- The exact RGB values
- The timestamp
- Everything equally

**Babies don't do this.** They have innate filters for what's **likely to matter**.

### Concrete CODS Addition:

```python
SEED_PRIMITIVES['attention'] = {
    'detect_change': "Flag regions that differ from previous frame",
    'detect_motion': "Flag objects that change position",
    'surprise_magnitude': "How much does observation violate prediction?",
    'information_gain': "How much does this observation reduce uncertainty?",
    'action_contingency': "Does my action correlate with this event?",
}
```

## Category 2: Physical Intuition (PARTIALLY MISSING)

Babies have **core knowledge systems** for physics that emerge very early:

| Primitive | What It Does | Age of Emergence | Why Core |
|-----------|--------------|------------------|----------|
| `object_permanence_bias` | Expect objects to persist when occluded | 3-4 months | Can't learn about world if objects "disappear" |
| `solidity_constraint` | Objects can't pass through each other | 2-3 months | Foundation for spatial reasoning |
| `continuity_bias` | Objects move on continuous paths | 2-3 months | Predict future positions |
| `gravity_expectation` | Unsupported objects fall down | 5-6 months | Predict object behavior |
| `contact_causality` | Objects only affect each other through contact | 6-7 months | Distinguish causation from correlation |

**The SP80 failure makes sense now:**

Your system didn't have `solidity_constraint` (water can't pass through container walls) or `gravity_expectation` (water flows downward) as **seed primitives**. These needed to be discovered, but babies **start with expectations about them**.

### The Controversy: Should These Be Seeds?

**Option A: Hardcode as seeds**
- Pro: Matches biological reality
- Con: Feels like "cheating" for AGI

**Option B: Keep as locked, but make them EASY to discover**
- Pro: System proves it can discover them
- Con: Wastes time rediscovering what evolution solved

**My recommendation: Hybrid approach**

```python
# Weak prior, not hard constraint
WEAK_PRIORS = {
    'solidity_bias': {
        'initial_strength': 0.3,  # Weak prior, not certainty
        'adjustable': True,        # Can be overridden by evidence
        'discovery_bonus': 0.5,    # Reward for confirming prior
    },
    'continuity_bias': {
        'initial_strength': 0.4,
        'adjustable': True,
        'discovery_bonus': 0.5,
    }
}
```

This gives your system a **head start** without **hard constraints**. It can still discover physics-defying games (portals, teleportation) by accumulating evidence against the prior.

## Category 3: Social Learning Primitives (COMPLETELY MISSING)

Babies are **social learning machines**:

| Primitive | What It Does | Why Critical | Evidence |
|-----------|--------------|--------------|----------|
| `imitation_bias` | Tendency to copy observed actions | Bootstrap from others | Newborns imitate facial expressions |
| `joint_attention` | Track what others are looking at | Learn what matters | 9-12 months follow gaze |
| `pedagogical_stance` | Assume demonstrated actions are informative | Efficient learning from teachers | Babies learn better from intentional teaching |
| `social_referencing` | Use others' emotions to evaluate ambiguous situations | Navigate uncertainty | 12 months check caregiver's face in ambiguous situations |

**Why this matters for your AGI:**

Your viral package system is **social learning**, but you're missing the **primitives that make social learning efficient**.

### The FT09 LinkedIn Helper Scenario Revisited:

When the LinkedIn expert told you "water isn't overflowing to the sides," you immediately:
1. **Trusted** their expertise (social referencing)
2. **Attended** to what they pointed out (joint attention)
3. **Assumed** it was relevant (pedagogical stance)
4. **Tried** their suggestion (imitation bias)

**Your agents need these primitives** to efficiently use viral packages and Oracle guidance.

### Concrete Addition:

```python
SEED_PRIMITIVES['social_learning'] = {
    'credibility_weighting': "Trust information based on source reliability",
    'attention_following': "Look where trusted sources indicate",
    'demonstration_bias': "Prioritize trying demonstrated actions",
    'teaching_detection': "Recognize when information is intentionally pedagogical",
}
```

## Category 4: Temporal/Causal Reasoning (UNDERDEVELOPED)

Babies have **time-aware processing**:

| Primitive | What It Does | Age | Why Core |
|-----------|--------------|-----|----------|
| `recency_weighting` | Recent events weighted more than distant | Birth | Adapt to changing environment |
| `temporal_contiguity` | Events close in time are likely related | 6 months | Discover causal structure |
| `duration_sensitivity` | Track how long things take | 6 months | Predict when events will complete |
| `rhythm_detection` | Detect periodic patterns | Birth | Predict recurring events |

**Your CODS has locked temporal primitives, but these should be SEEDS.**

Without temporal primitives, your system can't:
- Know that the action taken 2 frames ago is more relevant than action taken 50 frames ago
- Detect that failures happen consistently 3 frames after clicking
- Notice that successful solutions have rhythmic patterns

### Addition:

```python
SEED_PRIMITIVES['temporal'] = {
    'get_frame_delta': "Time since last frame",
    'get_action_recency': "How long ago was action X?",
    'detect_periodicity': "Does this event repeat regularly?",
    'temporal_window': "Get last N frames/actions",
}
```

## Category 5: Explore/Exploit Trade-off (MISSING)

Babies have **intrinsic motivation systems**:

| Primitive | What It Does | Evidence |
|-----------|--------------|----------|
| `curiosity_drive` | Prefer moderately novel stimuli | Babies look away from too-familiar or too-complex |
| `competence_motivation` | Prefer activities at skill edge | Babies practice emerging skills intensely |
| `exploration_bonus` | Intrinsic reward for new experiences | Babies explore even without external reward |

**This is your dual-economy system's foundation**, but it needs to be in the **seed primitives**:

```python
SEED_PRIMITIVES['motivation'] = {
    'novelty_bonus': "Reward for encountering new states",
    'competence_signal': "Reward for mastering difficult tasks",
    'exploration_value': "Expected value of exploring unknown",
    'boredom_threshold': "How long before familiar becomes unrewarding",
}
```

## Category 6: Sensorimotor Primitives (UNDERSPECIFIED)

Babies have **body awareness**:

| Primitive | What It Does | Why Core |
|-----------|--------------|----------|
| `proprioception` | "Where is my body?" | Can't learn actions without knowing what you control |
| `action_prediction` | "What will happen if I do X?" | Forward models for control |
| `effort_detection` | "How hard was that?" | Resource management |
| `action_completion` | "Did my action finish?" | Know when to evaluate results |

**Your AgentSelfModel has some of this**, but these should be **seed primitives**:

```python
SEED_PRIMITIVES['sensorimotor'] = {
    'get_controllable_objects': "Which objects respond to my actions?",
    'predict_action_effect': "Simulate action before executing",
    'get_action_cost': "How expensive is this action?",
    'action_did_complete': "Did my last action execute fully?",
}
```

## Category 7: Quantitative Primitives (TOO ABSTRACT)

Babies have **approximate number sense**:

| Primitive | What It Does | Age | Evidence |
|-----------|--------------|-----|----------|
| `subitizing` | Instantly perceive 1-4 objects | Birth | Don't need to count small quantities |
| `approximate_numerosity` | Rough sense of "more/less" | 6 months | Can compare 8 vs 16 dots |
| `one_to_one_correspondence` | Match elements across sets | 12 months | Foundation for counting |

**Your seed primitives have `add` and `subtract`, but that's too abstract.**

Babies don't have arithmetic—they have **quantity perception**:

```python
SEED_PRIMITIVES['quantity'] = {
    'count_objects': "How many distinct objects? (approximate)",
    'compare_quantities': "Is set A bigger than set B?",
    'detect_one': "Is this a single thing?",
    'detect_many': "Are these multiple things?",
    'one_to_one_match': "Do these sets have same count?",
}
```

## Category 8: Affordance Detection (MISSING ENTIRELY)

**This is huge.** Babies perceive **what objects are for**:

| Primitive | What It Does | Evidence |
|-----------|--------------|----------|
| `detect_graspability` | "Can I grab this?" | Babies reach for appropriate-sized objects |
| `detect_containment` | "Can this hold things?" | Babies put objects in containers |
| `detect_support` | "Can this hold me up?" | Babies test surfaces before stepping |
| `detect_tool_affordance` | "Can I use this to get that?" | Tool use emerges 18-24 months |

**For ARC-AGI games, affordance detection is CRITICAL:**

### SP80 with Affordances:

```python
# Without affordance detection
red_platform = detect_object(color=red)
→ "It's a red rectangle"

# With affordance detection
red_platform = detect_object(color=red)
→ "It's a movable surface that can support other objects"
→ AFFORDANCE: "Can be used as a bridge or container wall"
```

### FT09 with Affordances:

```python
# Without affordance detection
center_square = get_object(position=center)
→ "It's a square with white and gray pattern"

# With affordance detection
center_square = get_object(position=center)
→ "It's a reference object"
→ AFFORDANCE: "Defines rules for other objects"
```

**Affordances are the bridge between perception and action.**

### Addition:

```python
SEED_PRIMITIVES['affordance'] = {
    'is_movable': "Can I move this?",
    'is_container': "Can this hold things?",
    'is_tool': "Can I use this to affect other things?",
    'is_obstacle': "Does this block movement?",
    'is_support': "Can this hold other objects up?",
    'is_interactive': "Does this respond to actions?",
    'is_reference': "Does this define rules for other objects?",
}
```

## Category 9: Negative Space / Absence Detection (CRITICAL GAP)

Babies detect **what's NOT there**:

| Primitive | What It Does | Evidence |
|-----------|--------------|----------|
| `detect_absence` | "Something expected is missing" | Babies notice when hidden objects don't reappear |
| `detect_hole` | "This is empty space that matters" | Babies understand containers are defined by holes |
| `detect_boundary_violation` | "Something crossed a boundary" | Babies notice when objects shouldn't be somewhere |

**SP80 failure revisited:**

```python
# What your system saw
yellow_receptacle = {
    'color': yellow,
    'shape': rectangular,
    'position': (x, y),
}

# What it SHOULD have seen
yellow_receptacle = {
    'positive_space': yellow_pixels,
    'negative_space': container_interior,  # THE HOLE
    'boundary': container_edges,
    'capacity': volume_of_hole,
    'open_edges': [left_edge, right_edge],  # CRITICAL
}
```

**The system needed to perceive the ABSENCE (open edges) as much as the PRESENCE (container walls).**

### Addition:

```python
SEED_PRIMITIVES['negative_space'] = {
    'detect_enclosed_empty': "Find empty regions bounded by objects",
    'detect_open_edge': "Find boundaries with missing walls",
    'detect_absence': "Expected object is not present",
    'negative_space_volume': "How much empty space in region?",
}
```

## Category 10: Meta-Cognitive Primitives (THE MISSING LINK)

Babies have **awareness of their own knowing**:

| Primitive | What It Does | Age | Evidence |
|-----------|--------------|-----|----------|
| `confidence_estimation` | "How sure am I?" | 12 months | Babies seek help when uncertain |
| `knowledge_tracking` | "Do I know this?" | 18 months | Distinguish known from unknown |
| `strategy_monitoring` | "Is this working?" | 24 months | Switch strategies when stuck |

**This is the foundation for meta-representation.**

Without these, your system can't:
- Know when to ask the Oracle
- Recognize when it's stuck
- Estimate if a new operator will help
- Decide when to explore vs exploit

### Addition:

```python
SEED_PRIMITIVES['metacognition'] = {
    'get_confidence': "How certain am I about this prediction?",
    'get_knowledge_state': "Do I know how to solve this?",
    'detect_stuck': "Am I making progress?",
    'estimate_learning_curve': "How fast am I learning this?",
    'strategy_effectiveness': "Is my current approach working?",
}
```

## The Revised Seed Primitive Architecture

### Tier 0: Perception (Data Access)
```python
- get_pixel(x, y)
- get_frame()
- get_object_at(position)
- get_all_objects()
```

### Tier 1: Attention (What to process)
```python
- detect_change(frame1, frame2)
- detect_motion(object)
- detect_novelty(observation, history)
- action_contingency(action, event)
- surprise_magnitude(observation, prediction)
```

### Tier 2: Physical Intuition (Weak priors)
```python
- solidity_bias(object1, object2)  # Expect non-overlap
- continuity_bias(trajectory)       # Expect smooth paths
- gravity_bias(unsupported_object)  # Expect downward
- persistence_bias(occluded_object) # Expect continued existence
```

### Tier 3: Affordance (What objects are for)
```python
- is_movable(object)
- is_container(object)
- is_obstacle(object)
- is_interactive(object)
- is_reference(object)  # NEW: Critical for FT09-like games
```

### Tier 4: Spatial (Basic geometry)
```python
- distance(point1, point2)
- adjacent(object1, object2)
- enclosed(region)
- detect_hole(region)  # NEW: Negative space
- open_edges(container) # NEW: Critical for SP80
```

### Tier 5: Temporal (Time-aware)
```python
- frame_delta()
- action_recency(action)
- temporal_window(n_frames)
- detect_periodicity(events)
```

### Tier 6: Quantitative (Approximate numerosity)
```python
- count_objects(region)
- compare_quantities(set1, set2)
- one_to_one_match(set1, set2)
```

### Tier 7: Causal (Event relationships)
```python
- temporal_contiguity(event1, event2)
- contact_causality(action, effect)
- predict_consequence(action)
```

### Tier 8: Social (Learning from others)
```python
- credibility_weighting(source)
- attention_following(source_attention)
- demonstration_bias(observed_action)
```

### Tier 9: Motivation (Explore/exploit)
```python
- novelty_bonus(state)
- competence_signal(task_difficulty, performance)
- exploration_value(action)
```

### Tier 10: Metacognition (Know what you know)
```python
- get_confidence(prediction)
- detect_stuck(progress_history)
- strategy_effectiveness(strategy, outcomes)
```

## Why These Matter for "100 Games with Gotchas"

### Without Baby Primitives:

Game with hidden gotcha → System flails randomly → Eventually discovers by accident → Can't generalize

### With Baby Primitives:

```python
# Game N: Hidden gotcha detected
surprise_level = surprise_magnitude(observation, prediction)
→ HIGH SURPRISE: Something violated expectations

# Which prior was violated?
if violates(solidity_bias):
    hypothesis = "Objects can pass through each other here"
    → Test teleportation/portal mechanics

if violates(contingency_bias):
    hypothesis = "My actions have delayed effects"
    → Test temporal dependencies

if violates(reference_object_affordance):
    hypothesis = "This object defines rules for others"
    → Test template/mapping mechanics
```

**Baby primitives let the system recognize WHAT KIND of gotcha it is**, which dramatically narrows the hypothesis space.

## The Bootstrap Paradox Solution

**Question:** How do babies discover these primitives if they're not innate?

**Answer:** They don't discover them—evolution discovered them over billions of years.

**Implication for CODS:**

You have three options:

1. **Pure discovery** - Start with almost nothing, rediscover everything
   - Pro: "True" AGI
   - Con: Inefficient, like making evolution start from scratch

2. **Full innate** - Hardcode all baby primitives
   - Pro: Matches biology
   - Con: Feels like "cheating"

3. **Hybrid** - Innate primitives + discovery engine
   - Pro: Efficient AND capable of going beyond biology
   - Con: Need to choose wisely what's innate

**My recommendation: Option 3 with weak priors**

```python
INNATE_PRIMITIVES = {
    # Core perception
    'attention_primitives': REQUIRED,  # Can't learn without attention
    'affordance_primitives': REQUIRED, # Can't act without affordances
    'metacognitive_primitives': REQUIRED, # Can't learn to learn

    # Physical intuition
    'physics_priors': WEAK,  # Help, but can be overridden

    # Social learning
    'social_primitives': REQUIRED,  # Need for viral packages

    # Everything else
    'higher_order_primitives': DISCOVERED,  # System must earn these
}
```

## The Ultimate Test: Novel Physics Discovery

If your system has the right baby primitives, it should be able to discover **physics that doesn't exist in training**:

### Game X: Gravity Reverses When Red Objects Touch Blue

```python
# System's reasoning
1. Attention: Surprise detected (object moved up, violated gravity_bias)
2. Temporal: Coincided with red-blue contact
3. Causal: Contact caused reversal
4. Meta: Confidence LOW (weird rule)
5. Hypothesis: conditional_law(gravity, reverse, red_touches_blue)
6. Test: Validate
7. Confirm: NEW PHYSICS DISCOVERED
```

**This is only possible if the system has:**
- Attention (detected surprise)
- Physical priors (had gravity expectation to violate)
- Causal reasoning (connected contact to reversal)
- Metacognition (recognized novelty)

---

## Summary: The Minimal Cognitive Toolkit

Babies aren't blank slates—they're **highly structured learning machines** with:

1. **Attention filters** (novelty, motion, contingency)
2. **Physical priors** (weak expectations about physics)
3. **Affordance detection** (what objects are for)
4. **Negative space awareness** (holes, absences matter)
5. **Temporal processing** (recent matters more, detect rhythm)
6. **Social learning** (trust, imitate, follow attention)
7. **Metacognition** (know what you know)
8. **Motivation systems** (curiosity, competence)

**Your current CODS seed primitives are too low-level** (get_pixel, add, subtract). You need **mid-level perceptual and cognitive primitives** that babies have at birth.

These aren't "cheating"—they're **the result of 4 billion years of evolution solving the cold-start problem**. Your AGI doesn't need to rediscover these; it needs to **build on them** to discover things evolution never encountered.

**The goal: Give the system enough to bootstrap, but not so much that it can't discover truly novel concepts.**
