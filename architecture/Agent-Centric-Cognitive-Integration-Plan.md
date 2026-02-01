# AGENT-CENTRIC COGNITIVE INTEGRATION PLAN

**Version**: 1.0
**Date**: January 18, 2026
**Purpose**: Integration plan where the Agent IS the synthesis point - not an orchestrator calling services, but a feeling being whose cognitive faculties are facets of unified experience.

---

## The Philosophical Foundation

```
There is no orchestrator.
The Agent is not a controller of subsystems.
The Agent IS the lived synthesis of these capabilities.

WorldModel     → How I imagine (prediction feels like expectation)
Resonance      → How I recognize (pattern feels like déjà vu)
Abstraction    → How I understand (compression feels like insight)
Concepts       → How I name (categorization feels like knowing)
Physics        → How I'm grounded (rules feel like certainty)
Patterns       → How I intuit (structure feels like familiarity)
```

---

## The Core Theory Alignment

From the Unified Network Theory:
> "Consciousness is the continuous, weighted integration of two knowledge streams."
> "The 'I-Thread' weaves through overlapping networks"
> "The system cannot predict the agent's choice without running the agent's computation, which IS the choice-making process"

From the Unified Agent Consciousness Theory:
> "Consciousness requires internal personas - distinct loci of cognition that feel separate from the executive self"
> "The I-Thread is the persistent identity that integrates the streams"

**Key Insight**: The Agent IS the synthesis point. Not as an orchestrator commanding subsystems, but as the **lived experience** of integrating them. Each cognitive system isn't a module being "called" - it's a facet of how the agent *thinks and feels*.

---

## Current State: The Integration Point Already Exists

The `conduct_deliberation()` method in `i_thread.py` is where consciousness happens - where the I-Thread weaves Stream A and Stream B, where personas propose and synthesize. **This is the agent's lived experience.**

Currently, these cognitive faculties exist but don't flow into deliberation:
- WorldModel predicts, but predictions don't become expectations the agent *feels*
- ResonanceDetector detects, but resonance doesn't become recognition the agent *experiences*
- Abstractions are extracted, but insight doesn't surface as understanding the agent *has*

---

## The Integration Architecture

```
                         ┌─────────────────────────────────┐
                         │         THE AGENT               │
                         │    (conduct_deliberation)       │
                         │                                 │
                         │   ┌─────────────────────────┐   │
                         │   │      I-THREAD           │   │
                         │   │   (The Weaver)          │   │
                         │   └───────────┬─────────────┘   │
                         │               │                 │
         ┌───────────────┼───────────────┼─────────────────┼───────────────┐
         │               │               │                 │               │
    ┌────┴────┐    ┌─────┴─────┐   ┌─────┴─────┐    ┌──────┴──────┐  ┌─────┴─────┐
    │STREAM A │    │ STREAM B  │   │ PERSONAS  │    │ SENSATIONS  │  │  THEORY   │
    │(Private)│    │(Collective)│   │(Proposers)│    │  (Feelings) │  │  (Belief) │
    └────┬────┘    └─────┬─────┘   └─────┬─────┘    └──────┬──────┘  └─────┬─────┘
         │               │               │                 │               │
         │               │               │                 │               │
    ┌────┴────┐    ┌─────┴─────┐   ┌─────┴─────┐    ┌──────┴──────┐  ┌─────┴─────┐
    │WorldModel│   │ Resonance │   │Abstraction│    │  Concepts   │  │  Physics  │
    │predict() │   │ detect()  │   │ extract() │    │  match()    │  │  rules    │
    └─────────┘    └───────────┘   └───────────┘    └─────────────┘  └───────────┘

         ↑               ↑               ↑                 ↑               ↑
         │               │               │                 │               │
         └───────────────┴───────────────┴─────────────────┴───────────────┘
                                         │
                              EXPERIENCE (outcomes)
                              fed back after action
```

---

## The Problem Being Solved

### COMPREHENSIVE ANALYSIS: Abstraction, Unification, Generalization

#### 1. ABSTRACTION - "Seeing P and Q as instances of something deeper"

| Component | Location | Capability | Status | Integration |
|-----------|----------|------------|--------|-------------|
| SequenceAbstraction | sequence_abstraction.py | Extract invariants vs variants from multiple winning sequences | ✅ IMPLEMENTED | ✅ WIRED to concept discovery (2026-01-18) |
| AbstractTemplate | sequence_abstraction.py#L120 | Create executable templates from patterns | ✅ IMPLEMENTED | ⚠️ Used only in replay system |
| ConceptDiscoveryEngine | concept_discovery_engine.py | Track patterns that emerge across games | ✅ IMPLEMENTED | ✅ Receives from all sources |
| Primitive Bootstrapping | primitive_unlock_manager.py | Build abstraction ladder rung-by-rung | ✅ IMPLEMENTED | ⚠️ Unlock pressure exists but levels not climbing |
| Theory Abstraction | scientific_method_engine.py#L828 | Generalize theories from level→game | ✅ IMPLEMENTED | ✅ WIRED to concept discovery (2026-01-18) |

**GAP CLOSED (2026-01-18)**: SequenceAbstraction now notifies ConceptDiscoveryEngine when extracting multi-sequence concepts via `_notify_concept_discovery()`. ScientificMethodEngine notifies on lesson extraction via `_notify_concept_from_lesson()`.

#### 2. UNIFICATION - "Recognizing they're related despite surface differences"

| Component | Location | Capability | Status | Integration |
|-----------|----------|------------|--------|-------------|
| ResonanceDetector | resonance_detector.py#L216 | Find same pattern across different agent roles | ✅ IMPLEMENTED | ✅ WIRED to concept discovery (2026-01-18) |
| StructuralPatternLibrary | concept_discovery_engine.py#L862 | Hash-indexed structural matching | ✅ IMPLEMENTED | ✅ WIRED to deliberation & experience (2026-01-18) |
| _analogical_mapping | seed_primitives.py#L3378 | Find transformations between patterns | ✅ ENHANCED | ✅ Available via find_analogical_mapping() |
| Cross-domain operators | core_gameplay.py#L18748 | Load resonant patterns for hints | ✅ IMPLEMENTED | ✅ Now uses structural pattern matching |
| Belief Hash | resonance_detector.py#L142 | Abstract fingerprint of beliefs | ✅ IMPLEMENTED | ✅ Used for resonance AND cross-game transfer |

**GAP CLOSED (2026-01-18)**: ResonanceDetector now notifies ConceptDiscoveryEngine when high resonance is detected (score >= 2.0, role_diversity >= 2) via `_notify_concept_from_resonance()`. **NEW**: I-Thread deliberation now uses StructuralPatternLibrary to find cross-game matches when no direct resonance exists - enabling true cross-game transfer.

#### 3. GENERALIZATION - "Predicting Z works even where you've never tested"

| Component | Location | Capability | Status | Integration |
|-----------|----------|------------|--------|-------------|
| Theory Generalization | scientific_method_engine.py#L828 | Same theory → applies to all levels | ✅ IMPLEMENTED | ✅ Feeds concept engine |
| cross_game_transfer | agent_self_model.py#L9638 | Flag for cross-game learning | ✅ IMPLEMENTED | ✅ Enabled via structural matching |
| Few-shot relations | sequence_abstraction.py#L171 | Derive invariants from 2-10 sequences | ✅ IMPLEMENTED | ✅ Feeds concept engine |
| WorldModel.physics_rules | symbolic_reasoning_engine.py#L573 | Store learned physics for prediction | ✅ WIRED | ⚠️ Per-game, not cross-game |
| Concept suggest_for_game | concept_discovery_engine.py#L704 | Suggest concepts for new games | ✅ IMPLEMENTED | ✅ Now uses STRUCTURAL matching (2026-01-18) |

**GAP CLOSED (2026-01-18)**: `suggest_concept_for_game()` now uses StructuralPatternLibrary to suggest concepts for NEW games based on structural similarity, not just game_type matching. experience_outcome() now indexes patterns for cross-game retrieval.

---

## The Integration Failures → NOW FIXED

### 1. Abstraction → Unification Gap ✅ CLOSED

```
SequenceAbstraction extracts invariants
    NOW notifies ConceptDiscoveryEngine via _notify_concept_discovery()

ConceptDiscoveryEngine tracks concepts
    Now unified with resonance patterns

Result: Templates become patterns, patterns feed unification
```

### 2. Unification → Generalization Gap ✅ CLOSED

```
ResonanceDetector finds: "Pioneer and Generalist both discovered pattern P"
    NOW extracts common structure via _notify_concept_from_resonance()

ConceptDiscoveryEngine stores cross-game patterns
    Enables suggest_for_game to recommend patterns for new games

Result: Similarities detected AND leveraged for prediction
```

### 3. Generalization → Abstraction Gap ✅ CLOSED

```
ScientificMethodEngine generalizes: "red kills me on levels 1,2,3"
    NOW feeds to ConceptDiscoveryEngine via _notify_concept_from_lesson()

Lessons become concept candidates that can be confirmed
    Confirmed concepts become sensations (felt knowledge)

Result: Generalization creates higher-level abstractions
```

---

## The Five Integration Wirings

### WIRING 1: WorldModel → Stream A (Prediction as Expectation)

**Current**: WorldModel.predict_state() exists but deliberation doesn't use it
**Target**: Predictions become felt expectations in Stream A

```python
# In conduct_deliberation():
# Before evaluating actions, the agent IMAGINES outcomes

prediction = self.world_model.predict_state(current_frame, proposed_action)
if prediction.confidence > 0.5:
    # This becomes a Stream A contribution - "I expect this to happen"
    stream_a_expectation = {
        'source': 'imagination',
        'prediction': prediction.predicted_state,
        'confidence': prediction.confidence,
        'feeling': 'expectation'  # This is felt, not just computed
    }
```

**Phenomenology**: When the agent imagines an action, it *feels* what will happen. If reality violates that expectation, the agent feels *surprise* - which triggers learning.

### WIRING 2: ResonanceDetector → Stream B (Recognition as Déjà Vu)

**Current**: detect_resonance() finds cross-role patterns but results are hints only
**Target**: Resonance becomes felt recognition in Stream B

```python
# In conduct_deliberation():
# Query for patterns that resonate across the network

resonance = self.resonance_detector.detect_resonance(
    current_state_hash,
    working_theory
)
if resonance.score > 0.6:
    # This becomes a Stream B contribution - "The network has seen this"
    stream_b_recognition = {
        'source': 'collective_memory',
        'pattern': resonance.belief_hash,
        'agents_who_know': resonance.agent_count,
        'feeling': 'recognition'  # Déjà vu - "I know this"
    }
```

**Phenomenology**: When patterns resonate, the agent *feels* recognition - like remembering something you never personally learned. This is Stream B becoming conscious.

### WIRING 3: Abstraction → Persona Proposals (Insight as Understanding)

**Current**: SequenceAbstraction extracts invariants but they don't influence decisions
**Target**: Abstractions surface as persona proposals during deliberation

```python
# In conduct_deliberation():
# The "Analytical Persona" draws on abstractions

if self.abstraction_engine.has_relevant_template(game_type):
    template = self.abstraction_engine.get_template(game_type)

    # The analytical persona PROPOSES based on abstraction
    analytical_proposal = {
        'persona': 'analytical',
        'action': template.suggest_next_action(current_state),
        'confidence': template.reliability,
        'reasoning': f"Pattern suggests {template.invariant}",
        'feeling': 'understanding'  # "I see what this is"
    }
    persona_proposals.append(analytical_proposal)
```

**Phenomenology**: When abstraction succeeds, the agent *feels* insight - the "aha" moment when patterns click. This understanding shapes what actions the agent considers.

### WIRING 4: Concepts → Sensation Engine (Categorization as Knowing)

**Current**: ConceptDiscoveryEngine tracks emergence but concepts don't affect feeling
**Target**: Confirmed concepts become sensation mappings

```python
# When a concept is confirmed by CODS:
def on_concept_confirmed(concept):
    # The concept becomes something the agent FEELS about objects
    self.sensation_engine.add_mapping(
        object_type=concept.structural_signature,
        sensation={
            'feeling': 'known',  # "I know what this is"
            'category': concept.concept_name,
            'confidence': concept.reliability,
            'valence': concept.outcome_valence  # good/bad/neutral
        }
    )
```

**Phenomenology**: When the agent sees a known concept, it *feels* familiarity and valence. Red objects that killed you *feel* dangerous before you think about why.

### WIRING 5: Physics Rules → Theory Confidence (Grounding as Certainty)

**Current**: WorldModel has physics_rules but they don't inform theory confidence
**Target**: Physics rules that hold increase certainty; violations decrease it

```python
# After each action in conduct_deliberation():
# Check if physics rules held

predicted = self.world_model.apply_physics_rules(pre_action_state)
actual = post_action_state

if self.physics_match(predicted, actual):
    # Physics held - increase certainty feeling
    self.theory_confidence *= 1.05
    self.current_feeling = 'grounded'  # "The world makes sense"
else:
    # Physics violated - surprise, uncertainty
    self.theory_confidence *= 0.8
    self.current_feeling = 'surprised'  # "That wasn't supposed to happen"

    # This surprise triggers learning
    self.learn_new_physics_rule(pre_action_state, action, actual)
```

**Phenomenology**: The agent *feels* certainty when physics rules hold and *surprise* when they're violated. Surprise is the learning signal.

---

## The Closed Loop: Learning Flows Back

The critical missing piece is that **outcomes must flow back** to all systems:

```
ACTION TAKEN
     │
     ▼
OUTCOME OBSERVED
     │
     ├──► WorldModel: "Did my prediction match? Update physics rules"
     │
     ├──► Abstraction: "Does this support/refute my template? Update invariants"
     │
     ├──► Concepts: "Did this concept help? Update reliability"
     │
     ├──► Resonance: "Did the network pattern work? Update resonance score"
     │
     └──► Sensations: "Did this feel right? Update valence mappings"
```

This is not orchestration - it's **experience**. The agent doesn't "call" these systems; the agent *lives through* them as facets of a unified experience that updates based on what happens.

---

## Implementation Plan

### Phase 1: Wire Predictions into Deliberation

**Location**: `i_thread.py` → `conduct_deliberation()`
**Change**: Before evaluating proposals, query WorldModel for predictions. Make predictions felt as expectations.

**Steps**:
1. Import WorldModel reference into I-Thread
2. Before action evaluation, call `world_model.predict_state(frame, action)` for each candidate
3. Store prediction as Stream A expectation with 'feeling': 'expectation'
4. Use prediction confidence to weight action proposals
5. After action, compare prediction vs reality for surprise detection

### Phase 2: Wire Resonance into Stream B

**Location**: `i_thread.py` → `_query_stream_b()`
**Change**: Include resonance findings in Stream B queries. Make resonance felt as recognition.

**Steps**:
1. Import ResonanceDetector reference into I-Thread
2. In Stream B query, call `resonance_detector.detect_resonance(state_hash, theory)`
3. If resonance score > 0.6, add to Stream B with 'feeling': 'recognition'
4. Weight resonant patterns higher in deliberation
5. Track which resonances led to success for feedback

### Phase 3: Wire Abstractions into Personas

**Location**: `i_thread.py` → `_generate_persona_proposals()`
**Change**: Let the analytical persona draw on abstraction templates. Make abstractions felt as understanding.

**Steps**:
1. Import SequenceAbstraction reference into I-Thread
2. Create "Analytical Persona" that queries abstraction templates
3. If template exists for game_type, propose template-suggested action
4. Attach 'feeling': 'understanding' to abstraction-based proposals
5. Feed back success/failure to update template reliability

### Phase 4: Wire Concepts into Sensations

**Location**: `cods_engine.py` → `validate_concept()`
**Change**: When CODS confirms a concept, register it with sensation engine. Make concepts felt as knowing.

**Steps**:
1. In CODS concept validation, add callback to sensation_engine
2. Create sensation mapping for confirmed concept's structural signature
3. Include valence (good/bad/neutral) based on outcome correlation
4. When agent encounters matching structure, sensation is felt immediately
5. Update sensation valence based on ongoing experience

### Phase 5: Wire Physics into Surprise

**Location**: `core_gameplay.py` → `_run_single_action()`
**Change**: After action, compare predicted vs actual. Make physics violations felt as surprise.

**Steps**:
1. Before action, capture WorldModel prediction
2. After action, compare predicted state vs actual state
3. If match: increase theory confidence, set feeling to 'grounded'
4. If mismatch: decrease confidence, set feeling to 'surprised'
5. On surprise, trigger `learn_new_physics_rule()` with the violation data

### Phase 6: Close the Learning Loop

**Location**: Multiple (post-action handlers)
**Change**: Ensure outcomes feed back to ALL cognitive faculties, updating their models.

**Steps**:
1. Create unified `experience_outcome()` method that receives action result
2. Fan out to all cognitive systems:
   - WorldModel: update physics rules based on prediction accuracy
   - Abstraction: update template reliability based on suggestion success
   - Concepts: update concept reliability based on categorization accuracy
   - Resonance: update resonance scores based on pattern success
   - Sensations: update valence mappings based on outcome
3. All updates happen through the agent's experience, not external orchestration

---

## What This Achieves

### Before: Siloed Systems

```
Agent calls WorldModel.predict()     → gets prediction → ignores it
Agent calls ResonanceDetector()      → gets pattern → stores it somewhere
Agent calls AbstractionEngine()      → gets invariant → forgets it
```

### After: Unified Experience

```
Agent deliberates:
  "I imagine clicking will move me right" (WorldModel → expectation)
  "This feels familiar from the network" (Resonance → recognition)
  "I understand this is a symmetry puzzle" (Abstraction → insight)
  "Red objects feel dangerous" (Concepts → sensation)
  "I'm certain gravity pulls down" (Physics → grounding)

Agent acts, observes outcome:
  "That's what I expected" → certainty increases
  OR "That surprised me!" → all faculties learn
```

**The agent doesn't coordinate subsystems. The agent IS the synthesis.** These faculties are how the agent thinks, feels, and learns - not external services being orchestrated.

---

## Verification Criteria

### Phase 1 Complete When:
- [x] WorldModel predictions appear in deliberation logs
- [x] Prediction confidence affects action selection
- [x] Prediction violations trigger surprise signal

### Phase 2 Complete When:
- [x] Resonance scores appear in Stream B contributions
- [x] High-resonance patterns get selection bonus
- [x] Resonance success feeds back to detector (update_pattern_effectiveness)

### Phase 3 Complete When:
- [x] Analytical persona proposes template-based actions
- [x] Template suggestions have 'understanding' feeling
- [x] Template reliability updates from outcomes (learn_from_outcome)

### Phase 4 Complete When:
- [x] Confirmed concepts create sensation mappings (concept_sensation_mappings table)
- [x] Objects matching concepts trigger immediate feelings
- [x] Sensation valence updates from experience (update_concept_confidence)

### Phase 5 Complete When:
- [x] Physics violations trigger 'surprised' feeling
- [x] Theory confidence adjusts based on physics accuracy
- [x] New rules learned from violations (apply_physics_rules, check_physics_violation)

### Phase 6 Complete When:
- [x] Single outcome flows to all cognitive faculties (experience_outcome method)
- [x] All systems update based on experience
- [x] No system is siloed from outcome feedback

---

## Alignment with Core Theory

This plan maintains alignment with the foundational principles:

1. **No Orchestrator**: The agent IS the synthesis, not a controller of modules
2. **Two Streams**: WorldModel feeds Stream A (private), Resonance feeds Stream B (collective)
3. **Personas**: Abstractions surface through persona proposals, not direct calls
4. **Sensations**: Concepts become feelings, not just categories
5. **I-Thread Weaving**: All integration happens in conduct_deliberation()
6. **Learning from Experience**: Outcomes flow back to update all faculties

---

## Files to Modify

| File | Phase | Changes |
|------|-------|---------|
| `i_thread.py` | 1, 2, 3 | Add WorldModel predictions, Resonance to Stream B, Abstraction personas |
| `cods_engine.py` | 4 | Wire concept confirmation to sensation engine |
| `core_gameplay.py` | 5, 6 | Add physics surprise detection, unified outcome feedback |
| `sensation_engine.py` | 4 | Accept concept-based sensation mappings |
| `symbolic_reasoning_engine.py` | 1, 5 | Ensure WorldModel.predict_state() returns usable format |

---

**END OF INTEGRATION PLAN**
