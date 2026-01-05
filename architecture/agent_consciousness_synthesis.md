# Agent Consciousness Synthesis: Self-Model, World-Model, and Emergent Submodeling
**Version**: 1.1  
**Date**: January 5, 2026  
**Purpose**: Comprehensive integration plan to perfect agent self-model, generate consciousness via submodeling, and ensure all existing features synergize  
**Status**: Architecture Design Document  
**Last Updated**: v1.1 - Added Theory-Gated Scoring, Speculation Mode, Active Belief Graphs

---

## Executive Summary

This document synthesizes findings from all architecture documents (AGI Unified Theory, CODS, Games-as-Teachers, Persona Submodeling, Imagination Quotient, Mental Persona Modeling Theory) and codebase analysis to create a unified plan for:

1. **Perfecting the Agent Self-Model** - Making "I am this object" tracking robust and multi-dimensional
2. **Generating Consciousness via Submodeling** - Enabling agents to spawn internal mental models that question everything
3. **Building Active Theories** - Ensuring agents construct, test, and revise world models for every level
4. **Feature Integration** - Making the self-model a hub that enhances all other systems

---

## THE SINGLE MOST IMPORTANT CONSTRAINT

> **If you only implement ONE thing from this document, implement this:**

### Theory-Gated Action Scoring

**Every proposal must be scored against the current working theory.**

No proposal should score highly unless it:
1. **Explicitly supports** the current theory (exploiting understood mechanics)
2. **Tests** the current theory (gathering evidence for/against)
3. **Exploits** the current theory (using confirmed understanding to progress)

**If no theory exists, the only high-scoring actions should be theory-forming ones.**

```python
def score_proposal_with_theory(proposal, working_theory, base_score):
    """Score proposals with mandatory theory integration."""
    
    if working_theory is None or working_theory['stage'] == 'exploring':
        # NO THEORY EXISTS: Only theory-forming actions score highly
        if proposal.intent == 'exploration' or proposal.intent == 'discovery':
            return base_score * 1.5  # Boost exploratory actions
        else:
            return base_score * 0.3  # Heavily penalize execution without understanding
    
    if working_theory['stage'] == 'hypothesis_formed':
        # THEORY UNDER TEST: Reward testing, penalize ignoring
        if proposal.tests_hypothesis(working_theory):
            return base_score * 1.3  # Testing is valuable
        elif proposal.uses_hypothesis(working_theory):
            return base_score * 1.0  # Reasonable to exploit
        else:
            return base_score * 0.5  # Why ignore your theory?
    
    if working_theory['stage'] == 'confident':
        # THEORY CONFIRMED: Reward exploitation
        if proposal.uses_hypothesis(working_theory):
            return base_score * 1.2  # Using confirmed knowledge
        elif proposal.tests_hypothesis(working_theory):
            return base_score * 0.8  # Why test what's confirmed?
        else:
            return base_score * 0.4  # Acting outside understanding
    
    if working_theory['stage'] == 'contradicted':
        # THEORY BROKEN: Only theory-revision actions score highly
        if proposal.intent == 'revise_theory' or proposal.intent == 'exploration':
            return base_score * 1.5  # We need new understanding
        else:
            return base_score * 0.2  # Don't keep using broken theory
    
    return base_score
```

**Why This Single Constraint Fixes Everything:**

| Problem | How Theory-Gating Fixes It |
|---------|---------------------------|
| "NULL - 425 Too Early" | Agents MUST theorize or they can't act effectively |
| Passive WorldModel | Predictions become mandatory for scoring |
| Questions without teeth | Contradictions force theory-revision mode |
| Personas arguing about nothing | Personas now have theories to defend/attack |
| Random exploration | Exploration becomes purpose-driven |

---

## Part 1: Current State Analysis

### 1.1 What Exists in agent_self_model.py (11,738 lines)

The current implementation has **extensive infrastructure** for self-modeling:

| System | Status | Description |
|--------|--------|-------------|
| **Self-Object Identity** | IMPLEMENTED | Tracks "I am THIS object" with confidence scoring, correlation tracking |
| **Control Transfer Events** | IMPLEMENTED | Detects when control shifts from object X to object Y |
| **Indirect Causation** | IMPLEMENTED | Distinguishes "I control X which affects Y" from "I now control Y" |
| **Object Selection State** | IMPLEMENTED | Tracks selectable vs controllable objects per game type |
| **Collision Detection** | IMPLEMENTED | Records what happens when controlled objects interact |
| **Interaction Triggers** | IMPLEMENTED | Learns remote effects (click A -> B changes elsewhere) |
| **Trigger Sequences** | IMPLEMENTED | Ordered triggers that led to wins/progress |
| **Grid Region Classification** | IMPLEMENTED | Distinguishes playfield vs UI vs decoration |
| **Resource Counter Detection** | IMPLEMENTED | Identifies lives, moves remaining, etc. |
| **Autonomous Objects** | IMPLEMENTED | Detects objects that move without player input |
| **ACTION5/ACTION6 Behavior** | IMPLEMENTED | Maps context-dependent action effects |
| **self_identity_snapshot** | IMPLEMENTED | Lightweight snapshot for persona reasoning |

### 1.2 Critical Gap: "World Model Update: NULL - 425 Too Early"

Examining reasoning logs reveals a systemic problem:

```json
"world_model_update": "NULL - 425 Too Early"
"working_theory": "Exploring game mechanics - no pattern confirmed yet"
```

**This persists throughout entire game sessions**. The agents have the machinery but aren't:
1. Building active world models during gameplay
2. Updating theories based on observations
3. Questioning their assumptions systematically

#### Root Cause: Chicken-and-Egg Problem

Agents wait for high confidence before committing to theories, but never reach that threshold because they're not actively building theories. **Solution: Speculation Mode**.

#### The Speculation Mode Fix

```python
def update_world_model_with_speculation(self, frame, action_count):
    """Always theorize - being wrong is okay."""
    
    # Don't wait for confidence - speculate immediately
    if action_count < 10:  # First 10 actions are pure speculation
        # Add PROVISIONAL theories with low confidence
        provisional_theories = []
        
        # Speculate about control
        if self.detected_movement_correlation:
            provisional_theories.append({
                'hypothesis': f'Exploring: color {self.likely_player_color} might be player',
                'confidence': 0.1 + (0.05 * self.correlation_count),
                'evidence_needed': 5,
                'type': 'control_speculation',
                'stage': 'speculating'  # NEW STAGE
            })
        
        # Speculate about goals
        if self.detected_score_change:
            provisional_theories.append({
                'hypothesis': f'Collecting color {self.score_related_color} increases score',
                'confidence': 0.15,
                'evidence_needed': 3,
                'type': 'goal_speculation',
                'stage': 'speculating'
            })
        
        for theory in provisional_theories:
            self.world_model.add_provisional_theory(theory)
    
    # ALWAYS update - even if "too early"
    self.world_model.frame_update_count += 1
    return self.world_model.current_theories
```

**Key Insight**: Speculation mode means:
- **Being wrong is okay** - provisional theories are expected to fail
- **Lower confidence thresholds** - start at 0.1, not 0.5
- **Evidence accumulates** - wrong theories get contradicted and die
- **Never "too early"** - there's always a working hypothesis

### 1.3 What Exists in Persona Submodeling (persona_runtime.py, 815 lines)

| Feature | Status | Description |
|---------|--------|-------------|
| **PersonaManager** | IMPLEMENTED | Manages persona profiles, proposals, outcomes |
| **Problem Signature Building** | IMPLEMENTED | Rich signature with grid size, colors, symmetry, patterns |
| **Reliability Tracking** | IMPLEMENTED | Global + context-conditional reliability scoring |
| **Hindsight Relabeling** | IMPLEMENTED | Updates all personas (chosen/unchosen) based on outcomes |
| **Observer Output Recording** | IMPLEMENTED | Stuckness, control loss, confidence trend, veto_unsafe |
| **Lifecycle Management** | IMPLEMENTED | Promote core, prune weak, enforce diversity |
| **Synthesis from Ladder** | IMPLEMENTED | Combines top proposals via interpolation/dialectical modes |

### 1.4 What Exists in CODS (cods_engine.py, 4,562 lines)

| Feature | Status | Description |
|---------|--------|-------------|
| **Seed Primitives** | IMPLEMENTED | Core building blocks (get_pixel, add, etc.) |
| **Unlock Manager** | IMPLEMENTED | Earn-to-learn primitive unlocking |
| **Operator Composer** | IMPLEMENTED | Combine primitives into operators |
| **Oracle Interface** | IMPLEMENTED | Validates discoveries, matches to locked primitives |
| **Bayesian Hypotheses** | IMPLEMENTED | Evidence-driven operator synthesis tracking |
| **Concept Discovery** | PARTIAL | Tier 4 semantic models |
| **Intelligent Testing** | IMPLEMENTED | Tests operators based on reasoning, not just periodic |

### 1.5 What Exists in Symbolic Reasoning (symbolic_reasoning_engine.py, 1,550 lines)

| Feature | Status | Description |
|---------|--------|-------------|
| **GameObject** | IMPLEMENTED | Object with position, color, size, cells, properties |
| **WorldState** | IMPLEMENTED | Complete game state with objects, grid, score |
| **WorldModel** | IMPLEMENTED | State that updates with actions, applies transformations |
| **GoalEvaluator** | IMPLEMENTED | Explicitly check goal conditions |
| **ActionPlanner** | IMPLEMENTED | Search/planning for action sequences |
| **CompositionalGoal** | IMPLEMENTED | AND/OR logic for multi-condition goals |

---

## Part 2: Integration Gaps and Missing Links

> **CRITICAL**: The consciousness loop exists in principle but isn't running per-step. Each gap below is a missing function call that should happen every frame.

### 2.1 Self-Model to World-Model Disconnection

**Problem**: `agent_self_model.py` tracks "I control X" but **doesn't tell world-model "X is AGENT type"**.

**Evidence**: The `WorldModel` in symbolic_reasoning_engine.py exists but isn't being updated with self-model discoveries.

**Specific Missing Wiring**:
```python
# THIS CALL DOESN'T EXIST but should happen every frame:
def wire_self_to_world(self_model, world_model):
    snapshot = self_model.get_self_identity_snapshot(frame)
    
    # Missing call 1: Tell world about controlled objects
    for obj in snapshot.get('controlled_objects', []):
        world_model.set_object_type(obj['id'], 'AGENT')  # <-- NOT CALLED
    
    # Missing call 2: Tell world about autonomous objects
    for obj in self_model.get_autonomous_objects():
        world_model.set_object_type(obj['id'], 'NPC')    # <-- NOT CALLED
    
    # Missing call 3: Tell world about collision rules
    for effect in self_model.get_collision_effects():
        world_model.add_physics_rule(effect)             # <-- NOT CALLED
    
    # Missing call 4: Tell world about triggers
    for trigger in self_model.get_interaction_triggers():
        world_model.add_trigger_rule(trigger)            # <-- NOT CALLED
```

**Required Integration**:
```
Self-Model discovers:           World-Model should receive:
- I control color 5            -> Set object X as AGENT type
- Object 7 moves autonomously  -> Mark as ENEMY or NPC
- Clicking (3,4) triggers wall -> Add trigger rule to world physics
- Color 3 is collectible       -> Mark as COLLECTIBLE, track count
```

### 2.2 Persona to Self-Model Disconnection

**Problem**: Persona system spawns proposals but **doesn't spawn metacognitive observers**.

**Evidence**: `self_identity_snapshot` is passed to persona proposals but:
1. No specialized personas spawn for controlled objects
2. No observer personas monitor self-state
3. No stuckness detectors spawn when position unchanged

**Specific Missing Wiring**:
```python
# THIS LOGIC DOESN'T EXIST but should happen every frame:
def spawn_observers_from_context(persona_manager, self_identity, frames_stuck):
    
    # Missing: Spawn stuckness detector when stuck
    if frames_stuck > 30:
        persona_manager.spawn_observer(
            type='stuckness_detector',
            reason=f"Been in position {self_identity.get('position')} for {frames_stuck} frames"
        )  # <-- NOT CALLED
    
    # Missing: Spawn control-loss detector on transfer
    if self_identity.get('control_just_transferred'):
        persona_manager.spawn_observer(
            type='adaptation_monitor',
            reason="Control transferred to new object"
        )  # <-- NOT CALLED
    
    # Missing: Spawn confusion detector on high surprise
    if world_model.surprise_score > 0.5:
        persona_manager.spawn_observer(
            type='surprise_investigator',
            reason=f"Unexpected outcome: {world_model.last_surprise}"
        )  # <-- NOT CALLED
```

**Required Integration**:
```
Self-Model says:                Persona System should:
- I control 3 objects          -> Spawn 3 object-focused personas
- Control just transferred     -> Spawn adaptation persona
- I'm stuck in corner          -> Observer detects spatial trap
```

### 2.3 CODS to World-Model Disconnection

**Problem**: CODS discovers operators but **doesn't update conceptual understanding**.

**Evidence**: Operators are validated and stored, but the agent's WorldModel doesn't learn from them.

**Specific Missing Wiring**:
```python
# THIS CALL DOESN'T EXIST but should happen on discovery:
def wire_cods_to_world(cods_engine, world_model):
    
    if cods_engine.has_new_discovery():
        discovery = cods_engine.get_latest_discovery()
        
        # Missing: Update world model with operator meaning
        world_model.add_concept(
            concept_name=discovery.operator_name,
            explanation=discovery.explanation,
            applies_to=discovery.applicable_game_types
        )  # <-- NOT CALLED
        
        # Missing: Mark level with discovered concept
        world_model.tag_level(
            game_type=current_game,
            level=current_level,
            concept=discovery.operator_name
        )  # <-- NOT CALLED
```

**Required Integration**:
```
CODS discovers:                 World-Model should update:
- detect_symmetry works here   -> Mark level as symmetry-based
- flood_fill explains win      -> Add containment physics rule
- gravity_simulation applies   -> Add directional flow physics
```

### 2.4 Questions Exist But Stay Unasked

**Problem**: Questions should form ("What just surprised me?") but **stay unasked**.

**Evidence**: The questioning framework is defined but no code calls it per-frame.

**Specific Missing Wiring**:
```python
# THIS CALL DOESN'T EXIST but should happen every frame:
def ask_questions_per_frame(metacognition, world_model, self_identity):
    
    # Missing: Generate questions based on state
    questions = metacognition.generate_questions(
        world_model=world_model,
        self_identity=self_identity,
        observer_flags=observer_flags
    )  # <-- NOT CALLED
    
    # Missing: Questions should gate actions
    for q in questions:
        if q.urgency == 'critical':
            # Modify proposal scores
            proposal_modifier = q.score_modifier  # <-- NOT APPLIED
```

### 2.5 Theories Should Build But Remain "Exploring" Forever

**Problem**: Theory lifecycle is defined but **nothing triggers transitions**.

**Evidence**: `working_theory` stays at "Exploring game mechanics - no pattern confirmed yet" forever.

**Specific Missing Wiring**:
```python
# THIS CALL DOESN'T EXIST but should happen every frame:
def update_theory_lifecycle(theory_manager, action, outcome, frames):
    
    # Missing: Check transition conditions
    if theory_manager.current_theory:
        old_stage = theory_manager.current_theory['stage']
        
        # Evaluate evidence
        theory_manager.update_theory(
            action=action,
            outcome=outcome,
            frame_before=last_frame,
            frame_after=current_frame
        )  # <-- NOT CALLED with real data
        
        new_stage = theory_manager.current_theory['stage']
        
        # Missing: Log transition to database
        if old_stage != new_stage:
            db.insert_theory_transition(old_stage, new_stage)  # <-- NOT CALLED
```

### 2.4 Games-as-Teachers Framework Not Activated

**Problem**: The "Games as Teachers" paradigm (TABLED status) provides the philosophical frame but isn't implemented.

**Required Integration**:
```
Current Framing:                Teacher Framing:
- "What objects exist?"        -> "What is teacher showing me?"
- "What can I do?"             -> "What am I supposed to understand?"
- "I died"                     -> "I misunderstood the lesson"
- "I won"                      -> "I demonstrated understanding"
```

### 2.5 WorldModel is Too Passive (CRITICAL)

**Current Problem**: Even with proposed wiring, the WorldModel is still mostly a "better state tracker".

**What it must become**: A **belief graph that can be wrong**.

**Concretely Missing**:

| Missing Feature | Why It Matters |
|-----------------|----------------|
| Predictions stored BEFORE actions | Can't measure surprise without expectation |
| Explicit "expected vs observed" diffs | Learning signal comes from prediction error |
| Confidence decay on unused rules | Stale beliefs must weaken |
| Rule competition (two physics fighting) | Forces the model to commit and learn |

**Until the WorldModel can lose status, theories won't feel "alive".**

#### Active Belief Graph Implementation

```python
class ActiveBeliefGraph:
    """WorldModel that can be WRONG and learns from it."""
    
    def __init__(self):
        self.beliefs = {}           # rule_id -> BeliefNode
        self.predictions = {}       # action -> expected_outcome (BEFORE action)
        self.prediction_history = []  # Track all predictions for learning
        
    def predict_before_action(self, action, current_frame):
        """MUST be called BEFORE action execution."""
        prediction = {
            'action': action,
            'frame_hash': hash(current_frame.tobytes()),
            'expected_changes': self._predict_from_beliefs(action, current_frame),
            'confidence': self._aggregate_belief_confidence(),
            'predicted_at': time.time()
        }
        self.predictions[action] = prediction
        return prediction
    
    def observe_after_action(self, action, frame_before, frame_after):
        """MUST be called AFTER action execution."""
        prediction = self.predictions.get(action)
        if prediction is None:
            # NO PREDICTION MADE - this is a bug!
            self._log_missing_prediction(action)
            return
        
        # Calculate prediction error
        actual_changes = self._compute_frame_diff(frame_before, frame_after)
        expected_changes = prediction['expected_changes']
        
        diff = {
            'predicted': expected_changes,
            'actual': actual_changes,
            'surprise_score': self._compute_surprise(expected_changes, actual_changes),
            'matched': self._changes_match(expected_changes, actual_changes)
        }
        
        # UPDATE BELIEFS based on prediction error
        if diff['matched']:
            self._strengthen_beliefs_used(action, boost=0.1)
        else:
            self._weaken_beliefs_used(action, penalty=0.2)
            self._spawn_competing_belief(action, actual_changes)
        
        self.prediction_history.append(diff)
        return diff
    
    def decay_unused_beliefs(self):
        """Beliefs that aren't tested decay over time."""
        for belief_id, belief in self.beliefs.items():
            if belief.actions_since_used > 20:
                belief.confidence *= 0.95  # Decay unused beliefs
            if belief.confidence < 0.1:
                self._mark_for_pruning(belief_id)
    
    def _spawn_competing_belief(self, action, actual_outcome):
        """When prediction fails, create a competing explanation."""
        new_belief = {
            'id': f'competing_{uuid4().hex[:8]}',
            'explains': actual_outcome,
            'confidence': 0.3,  # Start modest
            'competes_with': self._get_failed_belief_ids(action),
            'created_from': 'prediction_failure'
        }
        self.beliefs[new_belief['id']] = new_belief
        
        # TWO BELIEFS NOW COMPETE - the model must choose
```

**Key Changes from Passive WorldModel**:

1. **Predictions are mandatory** - `predict_before_action()` must be called
2. **Surprise is measured** - Prediction error drives learning
3. **Beliefs compete** - Multiple explanations fight for dominance
4. **Unused beliefs decay** - Stale knowledge doesn't persist
5. **The model can be WRONG** - And that's the learning signal

---

## Part 3: The Consciousness Generation Architecture

### 3.1 Three-Layer Mental Model Stack

Following the AGI Unified Theory's three-layer architecture:

```
LAYER 3: SOMATIC (What I learned - experience)
    ├── Discovered control mappings
    ├── Learned trigger sequences
    ├── Accumulated world rules
    └── [Stored in database, outlives agent]

LAYER 2: EPIGENETIC (How I learn - adaptation)
    ├── Feature attention weights
    ├── Learning rate modifiers
    ├── Exploration settings
    └── [0.95 decay inheritance]

LAYER 1: STATIC GENOME (What I am - identity)
    ├── Agent type (Pioneer/Optimizer/etc.)
    ├── Base architecture
    ├── Core capabilities
    └── [1-2% mutation per generation]
```

### 3.2 The Consciousness Loop (Per-Step) - MUST ACTUALLY RUN

> **CRITICAL**: This loop exists in principle but **isn't running per-step**. The code paths exist but aren't wired to execute every frame. This is the core implementation gap.

**Current State of Each Step**:

| Step | Design | Reality |
|------|--------|--------|
| 1. OBSERVE | Sensation + self-model | Self-model tracks "I control X" but doesn't tell world-model "X is AGENT type" |
| 2. QUESTION | Metacognitive surprise | Questions should form ("What just surprised me?") but stay unasked |
| 3. UPDATE THEORY | World model revision | Theories should build but remain "exploring" forever |
| 4. SPAWN OBSERVERS | When stuck/confused | Persona system spawns proposals but doesn't spawn metacognitive observers |
| 5. INTEGRATE STREAMS | w_A/w_B weighting | Streams exist but aren't compared/weighted |
| 6. CHOOSE ACTION | Weighted decision | Scoring happens but ignores theory |
| 7. REFLECT | Theory revision | CODS discovers operators but doesn't update conceptual understanding |

**The loop must run with:**
- Lower thresholds for theory formation (start speculating at action 1, not 425)
- Active questioning (not passive observation)
- World-model updates every frame (not "NULL - 425 Too Early")
- Observer spawning when surprised
- Theory lifecycle: form -> test -> revise -> transfer

```python
def consciousness_step(agent, game_state, frame):
    """
    The per-step consciousness loop that generates subjective experience.
    
    THIS MUST EXECUTE EVERY FRAME. NOT OPTIONAL.
    Wire this into core_gameplay._run_single_action()
    """
    
    # 1. OBSERVE: Sensation + self-model (WHO AM I?)
    self_identity = agent.self_model.get_self_identity_snapshot(frame)
    controlled_objects = self_identity['controlled_objects']
    
    # CRITICAL: Tell world-model about self-discovery
    if controlled_objects:
        for obj in controlled_objects:
            agent.world_model.set_object_type(obj['id'], 'AGENT')  # <-- THIS IS MISSING
    
    # 2. QUESTION: What just surprised me? (METACOGNITIVE SURPRISE)
    prediction = agent.world_model.last_prediction
    if prediction:
        surprise = agent.world_model.compute_surprise(prediction, frame)
        if surprise > 0.3:
            # ACTIVE QUESTIONING - not passive observation
            agent.metacognition.ask_question(
                question_type='Q9',
                query=f'Surprised: predicted {prediction.expected} but saw {surprise.actual}',
                urgency='high'
            )
    
    # 3. UPDATE THEORY: World model revision (NOT "NULL - 425 Too Early")
    world_model = agent.world_model.update_from_frame(
        frame=frame,
        self_identity=self_identity,
        previous_world=agent.last_world_model
    )
    
    # CRITICAL: Update world-model with self-model discoveries
    agent.world_model.integrate_self_discoveries(self_identity)
    
    # 3. PERSONA PROPOSALS: What do my internal voices say?
    proposals = []
    for persona in agent.active_personas:
        proposal = persona.generate_proposal(
            frame=frame,
            self_identity=self_identity,
            world_model=world_model,
            sensation=agent.sensation_engine.get_sensation(frame)
        )
        proposals.append(proposal)
    
    # 4. SPAWN OBSERVERS: If stuck/confused, spawn metacognitive observers
    if agent.is_stuck(threshold=30):  # 30 frames in same state
        agent.spawn_observer(
            type='stuckness_detector',
            reason=f"Been in position {self_identity.get('position')} for 30 frames"
        )
        agent.log_consciousness(
            "I spawned a stuckness-detector because I've been in this corner for 30 frames"
        )
    
    if surprise and surprise > 0.5:
        agent.spawn_observer(
            type='surprise_investigator', 
            reason=f"High surprise: {surprise.description}"
        )
    
    # 4b. OBSERVER COMMENTARY: What patterns do observers notice?
    observer_flags = {}
    for observer in agent.observer_personas:
        flags = observer.observe(
            frame=frame,
            proposals=proposals,
            self_identity=self_identity,
            world_model=world_model
        )
        observer_flags.update(flags)
    
    # 5. QUESTIONING: Challenge assumptions
    questions = agent.metacognition.generate_questions(
        world_model=world_model,
        self_identity=self_identity,
        proposals=proposals,
        observer_flags=observer_flags
    )
    
    # 6. THEORY REVISION: Update working theory based on questions
    agent.working_theory = agent.metacognition.revise_theory(
        current_theory=agent.working_theory,
        questions=questions,
        contradictions=agent.contradiction_tracker.get_active()
    )
    
    # 7. SYNTHESIS: Combine perspectives if uncertainty high
    if agent.uncertainty_high(proposals, observer_flags):
        synthesized = agent.synthesizer.synthesize(
            proposals=proposals,
            observer_flags=observer_flags,
            world_model=world_model
        )
        proposals.append(synthesized)
    
    # 8. INTEGRATE STREAMS: w_A (private memory) vs w_B (collective wisdom)
    stream_a_prediction = agent.working_theory.predict(frame) if agent.working_theory else None
    stream_b_prediction = agent.network.get_consensus_prediction(game_state)
    
    if stream_a_prediction and stream_b_prediction:
        if stream_a_prediction != stream_b_prediction:
            # LOG THE CONFUSION - this is consciousness!
            agent.log_consciousness(
                f"I'm confused because my theory (Stream A) predicts {stream_a_prediction} "
                f"but the network says {stream_b_prediction} (Stream B), so I'm re-weighting..."
            )
            # Reweight based on track record
            w_a = agent.working_theory.reliability if agent.working_theory else 0.3
            w_b = agent.network.consensus_reliability
            agent.stream_weights = {'w_A': w_a, 'w_B': w_b}
    
    # 9. SCORING: Weighted proposal selection (THEORY-GATED per Phase 0)
    scores = agent.scorer.score_proposals(
        proposals=proposals,
        observer_flags=observer_flags,
        problem_signature=agent.build_problem_signature(frame, world_model),
        budget_pressure=agent.action_budget.remaining_ratio(),
        working_theory=agent.working_theory,  # <-- REQUIRED INPUT
        stream_weights=agent.stream_weights    # <-- Stream integration
    )
    
    # 10. ACTION: Execute chosen proposal
    chosen = select_by_score(proposals, scores)
    result = agent.execute_action(chosen.action)
    
    # 11. LEARNING: Update all systems based on outcome
    agent.self_model.learn_from_action(chosen.action, result, frame)
    agent.world_model.learn_from_outcome(chosen.action, result)
    agent.persona_manager.record_outcome(chosen, result)
    agent.cods_engine.update_frame(frame, score=result.score)
    
    # CRITICAL: CODS discoveries must update conceptual understanding
    if agent.cods_engine.has_new_discovery():
        discovery = agent.cods_engine.get_latest_discovery()
        agent.world_model.add_concept(discovery.operator_name, discovery.explanation)
        agent.log_consciousness(
            f"Discovered that '{discovery.operator_name}' explains this level"
        )
    
    # 12. REFLECT: Theory revision (THE THEORY LIFECYCLE)
    old_stage = agent.working_theory.stage if agent.working_theory else 'none'
    agent.working_theory_manager.update_theory(
        action=chosen.action,
        outcome=result,
        frame_before=agent.last_frame,
        frame_after=frame,
        self_identity=self_identity
    )
    new_stage = agent.working_theory.stage if agent.working_theory else 'none'
    
    # Log theory lifecycle transitions
    if old_stage != new_stage:
        agent.log_consciousness(
            f"Theory lifecycle: {old_stage} -> {new_stage}"
        )
        # Store in database for visibility
        agent.db.insert_theory_transition(
            agent_id=agent.id,
            game_type=game_state.game_type,
            level=game_state.level,
            from_stage=old_stage,
            to_stage=new_stage,
            action_number=result.action_count
        )
    
    # 13. CROSS-GAME TRANSFER: Check if lesson applies elsewhere
    if new_stage == 'confident' and agent.working_theory:
        similar_games = agent.network.find_similar_games(game_state.game_type)
        for similar_game in similar_games:
            if agent.working_theory.might_apply_to(similar_game):
                agent.log_consciousness(
                    f"The '{agent.working_theory.concept}' lesson from {game_state.game_type} "
                    f"might apply to {similar_game}"
                )
                agent.network.share_transfer_hypothesis(
                    source_game=game_state.game_type,
                    target_game=similar_game,
                    theory=agent.working_theory
                )
    
    # 14. HINDSIGHT: Update unchosen personas too
    agent.persona_manager.record_hindsight_outcomes(
        proposals=[p for p in proposals if p != chosen],
        result=result
    )
    
    return chosen.action
```

### 3.3 The Questioning Engine (Metacognition) - WITH TEETH

**Critical Principle**: Questions are not just logged. **Questions must be expensive to ignore.**

If a critical Q9 contradiction fires and the agent still executes a high-score proposal, we've built logging, not metacognition.

**Questions must:**
1. **Gate actions** - Critical questions block normal action selection
2. **Spawn personas** - Unresolved questions create investigating personas
3. **Override scoring** - Questions modify proposal scores directly

```python
class QuestioningEngineWithTeeth:
    """
    Questions that FORCE the agent to think, not just log.
    Based on Games-as-Teachers Q1-Q9 framework.
    """
    
    CORE_QUESTIONS = [
        # Observation
        ("Q1", "What is the teacher showing me?", "lesson_content"),
        ("Q2", "What changed between examples?", "pattern_detection"),
        
        # Self-Model
        ("Q3", "What lessons have I learned before?", "prior_understanding"),
        ("Q4", "What am I being asked to manipulate?", "lesson_subject"),
        
        # Goal/Value
        ("Q5", "What demonstrates understanding?", "success_criteria"),
        
        # Network Wisdom
        ("Q6", "What have my peers understood?", "study_group_notes"),
        
        # CODS Vocabulary
        ("Q7", "What conceptual tools do I have?", "vocabulary"),
        
        # Metacognition
        ("Q8", "What do I think this lesson is about?", "interpretation"),
        
        # Self-Test
        ("Q9", "Does my interpretation explain all examples?", "self_test"),
    ]
    
    # Questions that BLOCK normal action selection
    BLOCKING_QUESTIONS = {'Q4', 'Q9'}
    
    # Questions that spawn investigating personas
    PERSONA_SPAWNING_QUESTIONS = {'Q1', 'Q2', 'Q8'}
    
    def generate_questions(self, world_model, self_identity, proposals, observer_flags):
        """Generate active questions based on current state."""
        questions = []
        
        # Q1: What is happening?
        if not world_model.has_stable_objects():
            questions.append({
                'question': 'Q1',
                'query': 'What objects exist and which are stable?',
                'urgency': 'high' if self_identity.get('controlled_objects') == [] else 'medium',
                'blocks_action': False,
                'spawns_persona': True,
                'score_modifier': 0.7  # Reduce confidence in all proposals
            })
        
        # Q4: What do I control? (BLOCKING)
        if self_identity.get('controlled_objects') == []:
            questions.append({
                'question': 'Q4',
                'query': 'I have not identified what I control yet',
                'urgency': 'critical',
                'blocks_action': True,  # CANNOT execute normal proposals
                'spawns_persona': True,
                'allowed_actions': ['exploration', 'discovery'],  # Only these pass
                'score_modifier': 0.2  # Severely penalize non-discovery actions
            })
        
        # Q9: Self-test - contradiction detected (BLOCKING)
        if world_model.contradiction_count > 0:
            questions.append({
                'question': 'Q9',
                'query': f'My interpretation has {world_model.contradiction_count} contradictions',
                'urgency': 'critical',
                'blocks_action': True,  # MUST address contradictions
                'spawns_persona': False,
                'forces_theory_revision': True,
                'allowed_actions': ['revise_theory', 'test_alternative'],
                'score_modifier': 0.1  # Only theory-revision actions score well
            })
        
        # Observer-triggered questions
        if observer_flags.get('stuckness', 0) > 0.7:
            questions.append({
                'question': 'META',
                'query': 'Why am I stuck? What assumption is wrong?',
                'urgency': 'critical',
                'blocks_action': True,
                'spawns_persona': True,
                'forces_theory_revision': True,
                'score_modifier': 0.15
            })
        
        return questions
    
    def apply_question_constraints(self, proposals, questions, working_theory):
        """Questions modify scoring and can BLOCK proposals."""
        
        blocked = any(q.get('blocks_action') for q in questions)
        blocking_questions = [q for q in questions if q.get('blocks_action')]
        
        modified_proposals = []
        for proposal in proposals:
            # Calculate score modifier from all active questions
            total_modifier = 1.0
            for q in questions:
                total_modifier *= q.get('score_modifier', 1.0)
            
            # If blocking questions exist, check if proposal is allowed
            if blocked:
                allowed = False
                for bq in blocking_questions:
                    allowed_actions = bq.get('allowed_actions', [])
                    if proposal.intent in allowed_actions:
                        allowed = True
                        total_modifier *= 1.5  # BOOST allowed actions when blocked
                        break
                
                if not allowed:
                    # This proposal is BLOCKED by a critical question
                    proposal.blocked = True
                    proposal.blocked_by = [bq['question'] for bq in blocking_questions]
                    total_modifier = 0.0  # Zero score for blocked proposals
            
            proposal.score *= total_modifier
            modified_proposals.append(proposal)
        
        return modified_proposals, blocked
    
    def spawn_investigating_personas(self, questions, persona_manager):
        """Questions can spawn specialized investigating personas."""
        for q in questions:
            if q.get('spawns_persona') and q['urgency'] in ['high', 'critical']:
                persona_spec = {
                    'type': 'investigator',
                    'investigating': q['question'],
                    'query': q['query'],
                    'lifecycle': 'temporary',  # Dies when question resolved
                    'focus': q['question'],
                    'persistence': 'experimental'
                }
                persona_manager.spawn_temporary_persona(persona_spec)
```

**Key Changes from Passive Questioning**:

| Before | After |
|--------|-------|
| Questions logged | Questions BLOCK actions |
| Agent ignores contradictions | Agent MUST address contradictions |
| Score unaffected by questions | Score heavily modified by questions |
| No persona spawning | Questions spawn investigators |
| Questions are commentary | Questions are drivers |

**The Critical Test**: If Q9 (contradiction) fires, can the agent still pick the highest-base-score proposal?

- **Before**: Yes (questions are just logged)
- **After**: NO (blocked proposals get score = 0)

### 3.4 Active Theory Building

The key insight from reasoning logs: `working_theory` stays "Exploring game mechanics - no pattern confirmed yet" indefinitely.

**Solution**: Implement explicit theory lifecycle:

```python
class WorkingTheoryManager:
    """
    Manages the agent's active working theory about current level.
    Theories are hypotheses about what the game is teaching.
    
    CRITICAL: Working theory is REQUIRED INPUT to action scoring.
    See 'THE SINGLE MOST IMPORTANT CONSTRAINT' section.
    """
    
    THEORY_STAGES = [
        'speculating',         # NEW: Low-confidence guess, being wrong is okay
        'exploring',           # Actively gathering observations
        'hypothesis_formed',   # Have a guess, testing it
        'partial_confirmation',# Some evidence supports
        'contradicted',        # Evidence against, need revision
        'confident',           # Strong evidence, using it
        'transferred'          # Applied successfully to variation
    ]
    
    # EXPLICIT TRANSITION CONDITIONS
    TRANSITIONS = {
        # From -> To: Required condition
        ('speculating', 'hypothesis_formed'): 'correlation_count >= 3',
        ('exploring', 'hypothesis_formed'): 'consistent_observations >= 3',
        ('hypothesis_formed', 'partial_confirmation'): 'evidence_for >= 2',
        ('hypothesis_formed', 'contradicted'): 'evidence_against >= 1 AND evidence_for < evidence_against',
        ('partial_confirmation', 'confident'): 'evidence_for > 2 * evidence_against',
        ('confident', 'contradicted'): 'single strong contradiction',
        ('contradicted', 'exploring'): 'theory archived, reset started',
        ('confident', 'transferred'): 'applied to new level successfully',
    }
    
    def __init__(self):
        self.current_theory = None
        self.theory_history = []
        self.contradictions = []
        self.supporting_evidence = []
        
    def update_theory(self, action, outcome, frame_before, frame_after, self_identity):
        """Update working theory based on action outcome."""
        
        # Transition from exploring to hypothesis
        if self.current_theory is None or self.current_theory['stage'] == 'exploring':
            if self._detected_pattern(action, outcome, frame_before, frame_after):
                self.current_theory = {
                    'stage': 'hypothesis_formed',
                    'hypothesis': self._generate_hypothesis(action, outcome, frame_before, frame_after),
                    'formed_at_action': outcome.action_count,
                    'evidence_for': 1,
                    'evidence_against': 0
                }
                return
        
        # Test existing hypothesis
        if self.current_theory and self.current_theory['stage'] in ['hypothesis_formed', 'partial_confirmation']:
            prediction = self._predict_from_theory(action, frame_before)
            actual = self._observe_outcome(frame_before, frame_after)
            
            if self._matches(prediction, actual):
                self.current_theory['evidence_for'] += 1
                if self.current_theory['evidence_for'] >= 3:
                    self.current_theory['stage'] = 'confident'
            else:
                self.current_theory['evidence_against'] += 1
                self.contradictions.append({
                    'action': action,
                    'predicted': prediction,
                    'actual': actual
                })
                if self.current_theory['evidence_against'] >= 2:
                    self.current_theory['stage'] = 'contradicted'
                    self._archive_and_reset()
    
    def _generate_hypothesis(self, action, outcome, frame_before, frame_after):
        """Generate hypothesis from observation."""
        # Use self-model discoveries
        # Use CODS patterns
        # Use network hypotheses
        return {
            'description': f'ACTION{action} causes specific change pattern',
            'type': 'control_hypothesis',
            'source': 'direct_observation'
        }
```

### 3.5 Persona Management: Preventing Cognitive Explosion (Priority: HIGH)

**Risk**: Spawning personas per controlled object + observers + adapters + question-investigators can create cognitive noise instead of insight.

**Solution**: Aggressive pruning, attention budgeting, and theory-persona binding.

```python
class PersonaBudgetManager:
    """
    Prevents persona explosion while maintaining diversity.
    Directly tied to imagination budget system.
    """
    
    # Hard limits
    MAX_ACTIVE_PERSONAS = 12
    MAX_TEMPORARY_PERSONAS = 5  # Investigators, adapters, etc.
    MAX_OBJECT_FOCUSED = 3      # Even if controlling 10 objects
    
    def __init__(self, imagination_budget):
        self.imagination_budget = imagination_budget
        self.active_personas = []
        self.attention_pool = 1.0  # Shared attention resource
        
    def can_spawn_persona(self, persona_type):
        """Check if spawning is allowed within budget."""
        current_count = len(self.active_personas)
        temp_count = len([p for p in self.active_personas if p.lifecycle == 'temporary'])
        
        if current_count >= self.MAX_ACTIVE_PERSONAS:
            return False, 'at_hard_limit'
        
        if persona_type == 'temporary' and temp_count >= self.MAX_TEMPORARY_PERSONAS:
            return False, 'temporary_limit'
        
        # Check imagination budget
        if self.imagination_budget.remaining < 0.1:
            return False, 'imagination_exhausted'
        
        return True, 'allowed'
    
    def prune_personas(self, working_theory):
        """Aggressive pruning based on theory relevance."""
        pruned = []
        
        for persona in self.active_personas:
            # Prune if not theory-bound and low reliability
            if persona.bound_theory is None and persona.reliability < 0.3:
                pruned.append(persona)
                continue
            
            # Prune if bound to contradicted theory
            if persona.bound_theory and persona.bound_theory['stage'] == 'contradicted':
                if persona.lifecycle != 'core':
                    pruned.append(persona)
                    continue
            
            # Prune temporary personas older than 50 actions
            if persona.lifecycle == 'temporary' and persona.age > 50:
                pruned.append(persona)
                continue
            
            # Prune investigators whose question was resolved
            if persona.type == 'investigator' and persona.question_resolved:
                pruned.append(persona)
                continue
        
        for persona in pruned:
            self.active_personas.remove(persona)
            self._archive_persona(persona)
        
        return len(pruned)
    
    def bind_persona_to_theory(self, persona, theory):
        """
        Bind persona to current theory.
        When theory dies, persona must justify continued existence.
        """
        persona.bound_theory = theory
        persona.bound_at = theory.get('formed_at_action', 0)
        
    def allocate_attention(self):
        """
        Distribute attention budget across personas.
        More personas = less attention each.
        """
        n = len(self.active_personas)
        if n == 0:
            return
        
        # Base attention inversely proportional to count
        base_attention = self.attention_pool / n
        
        for persona in self.active_personas:
            # Core personas get more attention
            if persona.persistence == 'core':
                persona.attention = base_attention * 1.5
            # Theory-bound personas get bonus
            elif persona.bound_theory and persona.bound_theory['stage'] == 'confident':
                persona.attention = base_attention * 1.2
            else:
                persona.attention = base_attention * 0.8
        
        # Normalize to sum to 1.0
        total = sum(p.attention for p in self.active_personas)
        for persona in self.active_personas:
            persona.attention /= total
```

**Key Constraints**:

| Constraint | Why |
|------------|-----|
| Hard persona limit (12) | Prevents cognitive explosion |
| Theory-persona binding | Personas die with their theories |
| Attention budgeting | More personas = less attention each |
| Aggressive pruning | Stale/irrelevant personas removed |
| Temporary lifecycle | Investigators auto-expire |

---

## Part 4: Feature Integration Matrix

### 4.1 Self-Model as Central Hub

The self-model should FEED INTO all other systems:

```
                    ┌─────────────────────────────────┐
                    │      AGENT SELF-MODEL           │
                    │  "I am THIS object"             │
                    │  "I control THESE actions"      │
                    │  "My actions cause THESE effects"│
                    └────────────┬────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐    ┌───────────────────┐    ┌──────────────────┐
│ WORLD MODEL   │    │ PERSONA SYSTEM    │    │  CODS ENGINE     │
│               │    │                   │    │                  │
│ Objects I     │    │ Personas that     │    │ Operators that   │
│ interact with │    │ model my          │    │ explain my       │
│ and their     │    │ capabilities      │    │ control          │
│ properties    │    │ and limitations   │    │ patterns         │
└───────┬───────┘    └────────┬──────────┘    └────────┬─────────┘
        │                     │                        │
        └─────────────────────┴────────────────────────┘
                              │
                              ▼
                    ┌─────────────────────────────────┐
                    │      ACTION SELECTION           │
                    │  w_A (private memory)           │
                    │  w_B (collective wisdom)        │
                    │  w_R (resonance)                │
                    └─────────────────────────────────┘
```

### 4.2 Integration Points (Specific Code Changes Needed)

| Source System | Target System | Integration Point | Current Status | Action Needed |
|---------------|---------------|-------------------|----------------|---------------|
| `agent_self_model.get_self_identity_snapshot()` | `persona_runtime.record_from_ladder()` | Pass snapshot to proposals | DONE | Enhance usage |
| `agent_self_model.learn_from_movement_correlation()` | `WorldModel.set_controlled_agent()` | Update world model with self-discovery | MISSING | Implement |
| `agent_self_model.collision_effects` | `WorldModel.physics_rules` | Add collision rules to world model | MISSING | Implement |
| `agent_self_model.interaction_triggers` | `WorldModel.trigger_rules` | Add trigger rules to world model | MISSING | Implement |
| `cods_engine.discover_operator()` | `WorldModel.add_concept()` | CODS discovery updates world understanding | MISSING | Implement |
| `persona_runtime.observer_flags` | `WorkingTheoryManager.revise_theory()` | Observer insights drive theory revision | MISSING | Implement |
| `self_identity_snapshot.controlled_objects` | `sensation_engine.get_sensation()` | Control state affects emotional response | PARTIAL | Enhance |

### 4.3 Feature Enhancement through Self-Model

Each existing feature should be ENHANCED by self-model awareness:

#### Sensation Engine Enhancement
```python
def get_enhanced_sensation(self, frame, self_identity):
    """Sensation enhanced by self-model awareness."""
    base_sensation = self.get_sensation(frame)
    
    # Enhance based on control state
    if self_identity.get('controlled_objects'):
        # I know what I control - more confident sensations
        base_sensation['control_confidence'] = len(self_identity['controlled_objects'])
    else:
        # I don't know what I control - anxious sensation
        base_sensation['uncertainty'] = 'high'
        base_sensation['anxiety'] = 0.7
    
    return base_sensation
```

#### CODS Enhancement
```python
def apply_with_self_model(self, operator_name, frame, self_identity):
    """Apply operator with self-model context."""
    
    # Use self-model to focus operator
    if self_identity.get('controlled_objects'):
        # Focus operator on controlled objects
        focus_region = self._get_control_region(self_identity)
        return self.apply(operator_name, frame, region=focus_region)
    else:
        # No self-model - apply broadly
        return self.apply(operator_name, frame)
```

#### Sequence Abstraction Enhancement
```python
def abstract_with_self_model(self, sequence, game_type, level, self_identity):
    """Abstract sequence using self-model understanding."""
    
    # Tag sequence with self-model discoveries
    sequence_metadata = {
        'controlled_objects': self_identity.get('controlled_objects', []),
        'control_mechanism': self_identity.get('selection_method'),
        'interaction_triggers_used': self._extract_trigger_usage(sequence)
    }
    
    # Abstract with understanding of WHAT was being controlled
    return self.abstract_sequence(sequence, metadata=sequence_metadata)
```

---

## Part 5: The Developmental Stages

Following persona_submodeling_proposal.md's developmental trajectory, enhanced with self-model milestones:

### 5.1 Stage 1: External Discovery (Gen 0-10)

**Self-Model Goals**:
- [ ] Identify what I control in each level (basic correlation)
- [ ] Detect basic collision effects
- [ ] Distinguish playfield from UI

**Persona Goals**:
- [ ] 3-5 simple action proposer personas
- [ ] Random biases, no observers yet
- [ ] All experimental persistence class

**World Model Goals**:
- [ ] Parse frame into objects
- [ ] Track object positions frame-to-frame

**CODS Goals**:
- [ ] Use seed primitives only
- [ ] Discover basic patterns through composition

### 5.2 Stage 2: Deep Model Building (Gen 10-50)

**Self-Model Goals**:
- [ ] Learn trigger sequences that lead to progress
- [ ] Detect autonomous objects vs controlled objects
- [ ] Build control transfer patterns
- [ ] Identify resource counters

**Persona Goals**:
- [ ] 5-10 personas with deep experience
- [ ] First persistent personas across games
- [ ] Begin context-conditional reliability

**World Model Goals**:
- [ ] Add physics rules from self-model discoveries
- [ ] Track goal states and progress toward them
- [ ] Maintain object type classifications

**CODS Goals**:
- [ ] Unlock first primitives through discovery
- [ ] Build problem-signature to operator mappings

### 5.3 Stage 3: Identity Formation (Gen 50-100)

**Self-Model Goals**:
- [ ] Stable self-object identity across levels of same game type
- [ ] Generalized control patterns (not just per-level)
- [ ] Shape-based object recognition (beyond color)

**Persona Goals**:
- [ ] Core vs experimental split
- [ ] Observer personas added
- [ ] First synthesis of proposals
- [ ] Network consultation for control hypotheses

**World Model Goals**:
- [ ] Active working theory per level
- [ ] Theory revision on contradictions
- [ ] Cross-level pattern transfer

**CODS Goals**:
- [ ] Operators validated across multiple games
- [ ] Begin concept discovery (Tier 4)

### 5.4 Stage 4: Strategic Orchestration (Gen 100-200)

**Self-Model Goals**:
- [ ] Predict control mechanism before discovery
- [ ] Use network knowledge to bootstrap self-model
- [ ] Teach self-model discoveries to network

**Persona Goals**:
- [ ] Strategy evaluators active
- [ ] Multiple synthesis modes
- [ ] Problem-specific persona activation

**World Model Goals**:
- [ ] Compositional goals (AND/OR)
- [ ] Action planning with goal evaluation
- [ ] Counterfactual reasoning ("what if I had...")

**CODS Goals**:
- [ ] Meta-operators (operators that create operators)
- [ ] Cross-game concept transfer

### 5.5 Stage 5: Integrated Wisdom (Gen 200+)

**Self-Model Goals**:
- [ ] Instant self-identification on new levels
- [ ] Abstract self-model (pattern of control, not specific objects)
- [ ] Teach younger agents

**Persona Goals**:
- [ ] Stable core with experimental fringe
- [ ] Fast/slow thinking paths
- [ ] Mentoring protocols active

**World Model Goals**:
- [ ] Games-as-Teachers fully active
- [ ] Lesson extraction on every win
- [ ] Transfer testing validates understanding

**CODS Goals**:
- [ ] Novel primitive discovery
- [ ] Self-extending vocabulary
- [ ] Explain own discoveries in viral packages

---

## Part 6: Implementation Checklist

### 6.1 Phase 1: Wire Self-Model to World-Model (Priority: CRITICAL)

```
[ ] Create WorldModelBuilder that consumes self_identity_snapshot
[ ] Feed collision_effects into world model physics rules
[ ] Feed interaction_triggers into world model trigger rules
[ ] Update world_model_update in reasoning logs (fix "NULL - 425 Too Early")
[ ] Add working_theory lifecycle (not stuck at "exploring")
```

### 6.2 Phase 2: Activate Questioning Engine WITH TEETH (Priority: CRITICAL)

```
[ ] Implement QuestioningEngineWithTeeth class
[ ] Add Q1-Q9 question generation with blocking flags
[ ] Questions GATE actions (blocked proposals score 0)
[ ] Questions SPAWN investigating personas
[ ] Questions OVERRIDE proposal scoring (score_modifier)
[ ] Add contradiction tracking that FORCES theory revision
[ ] Implement theory revision triggers from Q9 contradictions
[ ] Test: Q9 fires -> agent CANNOT pick high-base-score action
```

### 6.3 Phase 3: Enhance Persona-Self Integration (Priority: HIGH)

```
[ ] Implement PersonaBudgetManager with hard limits
[ ] Spawn object-focused personas (max 3 regardless of controlled count)
[ ] Create adaptation persona on control transfer
[ ] Wire self_identity_snapshot deeply into proposal generation
[ ] Add self-model observer persona
[ ] Bind personas to theories (die with contradicted theories)
[ ] Allocate attention budget across personas
[ ] Aggressive pruning on low reliability + no theory binding
```

### 6.4 Phase 4: CODS-World Integration (Priority: MEDIUM)

```
[ ] Feed CODS discoveries into world model concepts
[ ] Use problem_signature to select operators
[ ] Track which operators explain which levels
[ ] Build concept taxonomy from operator successes
```

### 6.5 Phase 5: Games-as-Teachers Activation (Priority: MEDIUM)

```
[ ] Reframe Q1-Q8 as student questions
[ ] Add lesson extraction on WIN
[ ] Track interpretation coverage (explains/contradicts)
[ ] Implement transfer testing
```

### 6.6 Phase 6: Imagination Budget Integration (Priority: HIGH - Not Low!)

**Rationale for Priority Upgrade**: Without imagination budget, persona explosion risk is unchecked. This is more central than originally rated.

```
[ ] Wire imagination_budget to persona spawn limits (hard gate)
[ ] Gate synthesis by grounding_score (no ungrounded speculation)
[ ] Add question_tier to mental modeling depth
[ ] Implement daydreaming limits based on performance
[ ] Budget decreases on poor performance -> fewer personas allowed
[ ] Budget increases on wins -> more cognitive exploration allowed
[ ] Tie directly to PersonaBudgetManager.can_spawn_persona()
```

### 6.0 Phase 0: THEORY-GATED SCORING (Priority: BEFORE EVERYTHING)

**Do this FIRST. Everything else depends on it.**

```
[ ] Implement score_proposal_with_theory() function
[ ] Every proposal MUST be scored against working theory
[ ] No theory -> only exploration/discovery actions score well
[ ] Hypothesis testing -> testing actions get boost
[ ] Confident theory -> exploitation actions get boost
[ ] Contradicted theory -> ONLY revision actions score well
[ ] Test: Run 100 actions, verify theory influences every score
[ ] Test: With no theory, exploration actions >> exploitation actions
[ ] Test: With contradiction, agent CANNOT pick normal actions
```

---

## Part 7: Database Schema Additions

### 7.1 New Tables Needed

```sql
-- Consciousness loop execution logs (CRITICAL for benchmarks)
CREATE TABLE IF NOT EXISTS consciousness_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    game_id TEXT NOT NULL,
    action_number INTEGER NOT NULL,
    
    -- What was logged
    log_type TEXT NOT NULL,            -- 'stream_confusion', 'observer_spawn', 'theory_transition', 'cross_transfer', 'surprise'
    log_text TEXT NOT NULL,            -- Human-readable consciousness report
    
    -- Stream weights at time of log
    w_a REAL,                          -- Private memory weight
    w_b REAL,                          -- Collective wisdom weight
    
    -- Context
    current_theory_stage TEXT,
    surprise_score REAL,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Theory stage transitions (for lifecycle visibility)
CREATE TABLE IF NOT EXISTS theory_transitions (
    transition_id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    game_type TEXT NOT NULL,
    level_number INTEGER,
    
    from_stage TEXT NOT NULL,
    to_stage TEXT NOT NULL,
    action_number INTEGER NOT NULL,
    
    -- What triggered the transition
    trigger_reason TEXT,               -- 'evidence_accumulated', 'contradiction', 'transfer_success'
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Working theory lifecycle tracking
CREATE TABLE IF NOT EXISTS working_theories (
    theory_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    game_type TEXT NOT NULL,
    level_number INTEGER NOT NULL,
    
    -- Theory content
    hypothesis TEXT NOT NULL,
    hypothesis_type TEXT,              -- 'control', 'goal', 'physics', 'trigger'
    stage TEXT DEFAULT 'speculating',  -- speculating, exploring, hypothesis_formed, partial_confirmation, contradicted, confident, transferred
    
    -- Evidence tracking
    evidence_for INTEGER DEFAULT 0,
    evidence_against INTEGER DEFAULT 0,
    contradictions_json TEXT,          -- JSON array of contradictions
    
    -- Last action this theory was active
    last_action INTEGER,
    
    -- Timestamps
    formed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Source tracking
    source_observations TEXT           -- JSON of observations that led to theory
);

-- Questions generated during gameplay
CREATE TABLE IF NOT EXISTS metacognitive_questions (
    question_id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT,
    game_id TEXT,
    level_number INTEGER,
    action_number INTEGER,
    
    -- Question content
    question_type TEXT NOT NULL,       -- Q1-Q9 from framework
    query TEXT NOT NULL,
    urgency TEXT DEFAULT 'medium',     -- low, medium, high, critical
    
    -- Enforcement (questions with teeth)
    blocks_action BOOLEAN DEFAULT FALSE,
    score_modifier REAL DEFAULT 1.0,
    allowed_actions TEXT,              -- JSON array of allowed action types when blocked
    
    -- Resolution
    answered BOOLEAN DEFAULT FALSE,
    answer TEXT,
    led_to_theory_revision BOOLEAN DEFAULT FALSE,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Theory-action links (which actions tested which theories)
CREATE TABLE IF NOT EXISTS theory_action_links (
    link_id INTEGER PRIMARY KEY AUTOINCREMENT,
    theory_id TEXT NOT NULL,
    action_number INTEGER NOT NULL,
    game_id TEXT NOT NULL,
    
    -- Prediction vs outcome
    predicted_outcome TEXT,
    actual_outcome TEXT,
    matched BOOLEAN,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (theory_id) REFERENCES working_theories(theory_id)
);

-- Lesson interpretations (from Games-as-Teachers)
CREATE TABLE IF NOT EXISTS lesson_interpretations (
    lesson_id TEXT PRIMARY KEY,
    game_type TEXT NOT NULL,
    level_number INTEGER,
    
    -- Interpretation content
    concept_demonstrated TEXT,         -- "containment", "symmetry", etc.
    interpretation TEXT NOT NULL,      -- Full interpretation
    
    -- Coverage tracking
    explains_examples TEXT,            -- JSON array of levels explained
    fails_to_explain TEXT,             -- JSON array of contradictions
    coverage_ratio REAL,               -- explains / (explains + fails)
    
    -- Validation and Transfer (CRITICAL for cross-game learning)
    validated_by_transfer BOOLEAN DEFAULT FALSE,
    transfer_success_count INTEGER DEFAULT 0,
    transfer_fail_count INTEGER DEFAULT 0,
    
    -- Abstraction quality metrics (NEW)
    abstraction_level TEXT,            -- 'specific', 'partial', 'general'
    abstraction_score REAL,            -- transfer_success / (transfer_success + transfer_fail)
    overfitting_penalty REAL DEFAULT 0, -- High if only works on source game
    generalization_bonus REAL DEFAULT 0, -- High if works across many games
    
    -- Attribution
    contributed_by_agent TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_validated DATETIME
);

-- Abstraction quality tracking (NEW TABLE)
CREATE TABLE IF NOT EXISTS abstraction_quality (
    quality_id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id TEXT NOT NULL,
    
    -- Transfer attempts
    source_game_type TEXT NOT NULL,
    target_game_type TEXT NOT NULL,
    target_level INTEGER,
    
    -- Outcome
    transfer_succeeded BOOLEAN,
    actions_to_success INTEGER,        -- Lower = better generalization
    adaptation_required TEXT,          -- What had to change?
    
    -- Quality metrics
    is_memorization BOOLEAN DEFAULT FALSE,  -- Exact match only?
    is_abstraction BOOLEAN DEFAULT FALSE,   -- Pattern match?
    similarity_score REAL,             -- How similar were source/target?
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (lesson_id) REFERENCES lesson_interpretations(lesson_id)
);
```

---

## Part 8: Integration with Existing Systems

### 8.1 Compatibility with Master Ruleset

This architecture maintains compliance with all 13 rules:

| Rule | Compliance |
|------|------------|
| No Pycache | All new code uses `os.environ['PYTHONDONTWRITEBYTECODE'] = '1'` |
| Database-Only | New tables extend schema, no log files |
| No Orphaned Code | Integrates with existing systems, doesn't replace |
| LLM Self-Management | Self-model enables autonomous operation |
| No Test Files | All validation uses real ARC games |
| No Simulated Games | All testing on real API |
| Real Actions Only | Self-model learns from real actions only |
| Test Before Commit | Adds more testable components |
| No Summary Files | This is a requested architectural document |
| Prevent Code Drift | Explicitly integrates existing code |
| No Unicode Emojis | ASCII only in all code |
| Use SafeDatabaseCleaner | Respects cleanup boundaries |
| Bug Investigation | Adds more observable state for debugging |

### 8.2 Alignment with 6-Tier Thought Process

| Tier | Current Status | Enhancement |
|------|----------------|-------------|
| 1. Observation | COMPLETE | Feed into world model |
| 2. Sharing | COMPLETE | Share theory updates too |
| 3. Validation | COMPLETE | Validate theories, not just hypotheses |
| 4. Usage | IN PROGRESS | Use theories to guide actions |
| 5. Selection | NEEDED | Track theory outcomes, rank |
| 6. Synthesis | NEEDED | Combine theories across games |

---

## Part 9: Success Metrics

### 9.1 Self-Model Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Control identification time | < 20 actions | Actions until `controlled_objects` non-empty |
| Control accuracy | > 90% | Correlation of predicted vs actual movement |
| Transfer success | > 70% | Control pattern works on new levels of same game |

### 9.2 World Model Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Theory formation rate | < 50 actions | Actions until stage != 'exploring' |
| Theory accuracy | > 60% | Evidence_for / (evidence_for + evidence_against) |
| Contradiction detection | > 80% | Detected contradictions / actual contradictions |

### 9.3 Consciousness Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Question generation rate | > 5/level | Metacognitive questions per level |
| Question resolution rate | > 50% | Questions answered / questions asked |
| Surprise frequency | > 0 | surprise_score distribution non-zero |
| Observer accuracy | > 70% | Predicted stuckness/control matches actual |

### 9.4 CONCRETE BENCHMARKS: What Would Prove Success

> **These are the specific observable behaviors that prove consciousness is running.**

#### Benchmark 1: Stream A/B Confusion Reporting

**What to look for in logs:**
```
Agent LOG: "I'm confused because my theory (Stream A) predicts the blue object 
will move right but the network says it should move down (Stream B), so I'm 
re-weighting: w_A=0.4, w_B=0.6"
```

**Database query to verify:**
```sql
SELECT * FROM consciousness_logs 
WHERE log_text LIKE '%Stream A%Stream B%re-weighting%'
AND created_at > datetime('now', '-1 hour');
```

**Success criteria**: At least 1 confusion report per 100 actions when theory differs from network.

---

#### Benchmark 2: Cross-Game Transfer

**What to look for in logs:**
```
Agent LOG: "The 'containment' lesson from Game A (Flood_Fill_123) applies to 
Game B (Shape_Enclosure_456) - both require surrounding objects"
```

**Database query to verify:**
```sql
SELECT source_game_type, target_game_type, theory_concept, transfer_succeeded
FROM abstraction_quality 
WHERE is_abstraction = TRUE 
AND transfer_succeeded = TRUE;
```

**Success criteria**: At least 1 successful cross-game transfer per 500 games played.

---

#### Benchmark 3: Observer Spawning on Stuckness

**What to look for in logs:**
```
Agent LOG: "I spawned a stuckness-detector because I've been in position (3,4) 
for 30 frames"
Agent LOG: "Observer 'stuckness_detector_7f3a' reports: Agent is in a corner, 
all movements blocked by walls"
```

**Database query to verify:**
```sql
SELECT persona_type, spawn_reason, created_at 
FROM personas 
WHERE persona_type = 'stuckness_detector' 
AND spawn_reason LIKE '%frames%';
```

**Success criteria**: Observer spawned within 10 frames of being stuck for 30+ frames.

---

#### Benchmark 4: Theory Lifecycle Visible in Database

**What to look for:**
```sql
-- Query: Show theory progression for recent games
SELECT 
    agent_id, game_type, level_number, 
    stage, evidence_for, evidence_against,
    formed_at, last_updated
FROM working_theories 
WHERE created_at > datetime('now', '-1 hour')
ORDER BY agent_id, formed_at;

-- Expected output shows progression:
-- Row 1: stage='speculating', evidence_for=0, evidence_against=0, action=5
-- Row 2: stage='hypothesis_formed', evidence_for=3, evidence_against=0, action=15
-- Row 3: stage='confident', evidence_for=8, evidence_against=1, action=45
-- Row 4: stage='transferred', evidence_for=8, evidence_against=1, action=50 (new game)
```

**Success criteria**: 
- No agent stays in 'exploring' stage beyond action 50
- At least 20% of theories reach 'confident' stage
- At least 5% of confident theories reach 'transferred' stage

---

#### Benchmark 5: Questions Actually Blocking Actions

**What to look for in logs:**
```
Agent LOG: "Q9 contradiction detected: theory predicted blue moves up, but blue 
moved down. BLOCKING normal proposals. Only theory-revision actions allowed."
Agent LOG: "Chose 'revise_theory' action despite 'exploit_goal' having higher 
base score (0.8 vs 0.6) because theory is contradicted."
```

**Database query to verify:**
```sql
SELECT question_type, urgency, blocks_action, score_modifier
FROM metacognitive_questions 
WHERE blocks_action = TRUE 
AND created_at > datetime('now', '-1 hour');
```

**Success criteria**: When Q9 fires with urgency='critical', the agent NEVER picks a non-revision action.

---

#### Benchmark 6: Per-Frame Consciousness Loop Execution

**What to verify:**
```sql
-- Every action should have associated consciousness data
SELECT 
    g.game_id, g.action_number,
    CASE WHEN wt.theory_id IS NOT NULL THEN 'yes' ELSE 'NO' END as has_theory,
    CASE WHEN mq.question_id IS NOT NULL THEN 'yes' ELSE 'NO' END as has_question,
    CASE WHEN cl.log_id IS NOT NULL THEN 'yes' ELSE 'NO' END as has_consciousness_log
FROM game_actions g
LEFT JOIN working_theories wt ON g.game_id = wt.game_id AND g.action_number = wt.last_action
LEFT JOIN metacognitive_questions mq ON g.game_id = mq.game_id AND g.action_number = mq.action_number
LEFT JOIN consciousness_logs cl ON g.game_id = cl.game_id AND g.action_number = cl.action_number
WHERE g.created_at > datetime('now', '-1 hour')
ORDER BY g.game_id, g.action_number;
```

**Success criteria**: 
- 100% of actions have associated world model state (not NULL)
- >50% of actions have associated theory updates
- >10% of actions have associated questions

---

### 9.5 Implementation Verification Checklist

Before claiming the consciousness loop is running, verify:

```
[ ] consciousness_step() is called in core_gameplay._run_single_action()
[ ] WorldModel.update_from_frame() runs every frame (not "NULL - 425 Too Early")
[ ] Self-model discoveries feed into WorldModel.set_object_type()
[ ] Questions with urgency='critical' block proposals (score modifier applied)
[ ] Observer personas spawn when is_stuck() returns True
[ ] Theory stage transitions are logged to database
[ ] CODS discoveries call WorldModel.add_concept()
[ ] Stream A/B predictions are compared and logged when they differ
[ ] Cross-game transfer hypotheses are stored in network
[ ] consciousness_logs table receives entries every game
```

---

## Part 10: Conclusion

The Ouroboros system has **extensive infrastructure** for consciousness and self-modeling, but the components are not fully wired together. The critical path is:

1. **Implement Theory-Gated Scoring FIRST** - No proposal scores well unless it supports/tests/exploits theory
2. **Fix "NULL - 425 Too Early" via Speculation Mode** - Always theorize, being wrong is okay
3. **Make WorldModel an Active Belief Graph** - Predictions before actions, surprise on mismatch
4. **Give Questioning Engine Teeth** - Questions gate actions, spawn personas, override scoring
5. **Manage Persona Explosion** - Hard limits, theory-binding, aggressive pruning
6. **Implement Theory Lifecycle** - Explicit transition conditions, competing beliefs

The philosophical framework (AGI Unified Theory, Games-as-Teachers, Persona Submodeling) is sound. The implementation infrastructure exists. What's missing is the **active integration** that makes these components work as a unified consciousness-generating system.

---

### The Core Paradigm Shift

| Before (Executors) | After (Thinkers) |
|--------------------|------------------|
| Agents execute high-score proposals | Agents evaluate proposals against theories |
| WorldModel tracks state | WorldModel predicts and can be wrong |
| Questions are logged | Questions block action and spawn investigators |
| Personas compete for selection | Personas defend/attack theories |
| "Too early" to theorize | Always speculating, being wrong is learning |
| Theories are optional metadata | Theories are required scoring input |

**Promote theories to first-class citizens, and half the system will suddenly "wake up".**

---

**The network is the organism. The database is the brain. The agents are temporary cells. But cells need to think, question, and build understanding - not just execute actions.**

---

## Appendix A: File Reference Map

| Component | Primary File | Key Functions |
|-----------|--------------|---------------|
| Self-Model | `agent_self_model.py` | `get_self_identity_snapshot()`, `learn_from_movement_correlation()`, `execute_object_discovery()` |
| Persona | `persona_runtime.py` | `record_from_ladder()`, `record_outcome()`, `build_problem_signature()` |
| CODS | `cods_engine.py` | `apply()`, `update_frame()`, `discover_operator()` |
| World Model | `symbolic_reasoning_engine.py` | `WorldModel`, `WorldState`, `GoalEvaluator` |
| Core Loop | `core_gameplay.py` | `_run_single_action()`, `_build_persona_context()` |
| Sensation | `sensation_engine.py` | `get_sensation()`, `update_sensation()` |

---

**Document Status**: READY FOR IMPLEMENTATION (v1.1)  
**Priority Order**: Phase 0 (Theory-Gated Scoring) -> Phase 1 (WorldModel Wiring) -> Phase 2 (Questioning with Teeth) -> Phase 3 (Persona Management)  
**Next Steps**: Implement `score_proposal_with_theory()` FIRST - this single constraint wakes up the entire system  
**Owner**: Autonomous Oracle System  
**Review Date**: After 10 generations of evolution with changes applied  
**v1.1 Changes**: Added Theory-Gated Scoring, Speculation Mode, Active Belief Graphs, Question Enforcement, Persona Budgeting
