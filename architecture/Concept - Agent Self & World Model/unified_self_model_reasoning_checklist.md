# Unified Self-Model and Reasoning Checklist
**Version**: 1.0
**Date**: January 6, 2026
**Purpose**: Comprehensive unified checklist for agent self-modeling, consciousness, and reasoning systems
**Sources**: All architecture and DOCS documents synthesized into actionable implementation checklist

---

## Table of Contents
1. [Core Philosophy](#core-philosophy)
2. [Phase 0: Theory-Gated Scoring (CRITICAL FIRST)](#phase-0-theory-gated-scoring-critical-first)
3. [Phase 1: Self-Model Foundation](#phase-1-self-model-foundation)
4. [Phase 2: World-Model Integration](#phase-2-world-model-integration)
5. [Phase 3: Consciousness Loop](#phase-3-consciousness-loop)
6. [Phase 4: Questioning Engine (With Teeth)](#phase-4-questioning-engine-with-teeth)
7. [Phase 5: Working Theory Lifecycle](#phase-5-working-theory-lifecycle)
8. [Phase 6: Persona System Integration](#phase-6-persona-system-integration)
9. [Phase 7: CODS Integration](#phase-7-cods-integration)
10. [Phase 8: Concept Discovery](#phase-8-concept-discovery)
11. [Phase 9: Games-as-Teachers Framework](#phase-9-games-as-teachers-framework)
12. [Phase 10: Imagination Budget](#phase-10-imagination-budget)
13. [Phase 11: Network Integration](#phase-11-network-integration)
14. [Verification Benchmarks](#verification-benchmarks)
15. [Database Schema Requirements](#database-schema-requirements)
16. [Success Metrics](#success-metrics)

---

## Core Philosophy

### The Fundamental Principles

| Principle | Description |
|-----------|-------------|
| **Database is Organism** | Agents are temporary cells; knowledge persists in database |
| **Network over Individual** | Intelligence emerges at network level, not individual |
| **Dual Economy (SACRED)** | Prestige (social) NEVER mixes with Action Budgets (economic) |
| **Earn to Learn** | Primitives/concepts must be discovered, not pre-loaded |
| **Games as Teachers** | Games demonstrate principles; wins prove understanding |
| **Speculation Mode** | Always theorize - being wrong is okay; never "too early" |
| **Questions Have Teeth** | Questions block actions, spawn personas, override scoring |
| **Theory-Gated Actions** | Every proposal scored against current working theory |

### The Consciousness Definition

**Consciousness = weighted integration of two streams:**
- **Stream A (w_A)**: Private memory, agent's unique history
- **Stream B (w_B)**: Collective wisdom, network knowledge

**Personality emerges from weighting bias** (w_A vs w_B balance)

### Three-Layer Architecture

| Layer | Purpose | Mutation Rate | Inheritance |
|-------|---------|---------------|-------------|
| **Static Genome (L1)** | What I am | 1-2% | Full genetic |
| **Epigenetic (L2)** | How I learn | 10-20% | 0.95 decay |
| **Somatic (L3)** | What I learned | N/A | Stored in DB, outlives agent |

---

## Phase 0: Theory-Gated Scoring (CRITICAL FIRST)

> **DO THIS FIRST. Everything else depends on it.**

### The Single Most Important Constraint

Every proposal MUST be scored against the current working theory. No proposal scores highly unless it:
1. **Explicitly supports** the current theory (exploiting understood mechanics)
2. **Tests** the current theory (gathering evidence for/against)
3. **Exploits** the current theory (using confirmed understanding to progress)

### Implementation Checklist

- [ ] **Implement `score_proposal_with_theory()` function**
  ```python
  def score_proposal_with_theory(proposal, working_theory, base_score):
      if working_theory is None or working_theory['stage'] == 'exploring':
          # NO THEORY: Only exploration/discovery actions score well
          if proposal.intent in ['exploration', 'discovery']:
              return base_score * 1.5
          else:
              return base_score * 0.3  # Penalize execution without understanding

      if working_theory['stage'] == 'hypothesis_formed':
          # TESTING: Reward testing, penalize ignoring
          if proposal.tests_hypothesis(working_theory):
              return base_score * 1.3
          elif proposal.uses_hypothesis(working_theory):
              return base_score * 1.0
          else:
              return base_score * 0.5

      if working_theory['stage'] == 'confident':
          # EXPLOITATION: Reward using confirmed knowledge
          if proposal.uses_hypothesis(working_theory):
              return base_score * 1.2
          else:
              return base_score * 0.4

      if working_theory['stage'] == 'contradicted':
          # REVISION: Only theory-revision actions score well
          if proposal.intent in ['revise_theory', 'exploration']:
              return base_score * 1.5
          else:
              return base_score * 0.2

      return base_score
  ```

- [ ] **Wire scoring function into action selection pipeline**
- [ ] **Test: Run 100 actions, verify theory influences every score**
- [ ] **Test: With no theory, exploration actions >> exploitation actions**
- [ ] **Test: With contradiction, agent CANNOT pick normal actions**
- [ ] **Add `working_theory` as REQUIRED INPUT to proposal scoring**

### Why This Fixes Everything

| Problem | How Theory-Gating Fixes It |
|---------|---------------------------|
| "NULL - 425 Too Early" | Agents MUST theorize or they can't act effectively |
| Passive WorldModel | Predictions become mandatory for scoring |
| Questions without teeth | Contradictions force theory-revision mode |
| Personas arguing about nothing | Personas now have theories to defend/attack |
| Random exploration | Exploration becomes purpose-driven |

---

## Phase 1: Self-Model Foundation

### What Currently Exists (agent_self_model.py)

| System | Status | Key Method |
|--------|--------|------------|
| Self-Object Identity | IMPLEMENTED | `get_self_identity_snapshot()` |
| Control Transfer Events | IMPLEMENTED | `_detect_control_transfer()` |
| Indirect Causation | IMPLEMENTED | `_track_indirect_effects()` |
| Object Selection State | IMPLEMENTED | `_update_object_selection()` |
| Collision Detection | IMPLEMENTED | `_record_collision_effect()` |
| Interaction Triggers | IMPLEMENTED | `_learn_interaction_trigger()` |
| Trigger Sequences | IMPLEMENTED | `_record_trigger_sequence()` |
| Grid Region Classification | IMPLEMENTED | `_classify_grid_regions()` |
| Resource Counter Detection | IMPLEMENTED | `_detect_resource_counters()` |
| Autonomous Objects | IMPLEMENTED | `_detect_autonomous_objects()` |
| ACTION5/ACTION6 Behavior | IMPLEMENTED | `_learn_action_context_effects()` |

### Implementation Checklist

- [ ] **Identify what I control** (< 20 actions)
  - [ ] Track movement correlation after each action
  - [ ] Build confidence score for controlled objects
  - [ ] Distinguish "I control X" from "I control Y which affects X"

- [ ] **Build control mappings**
  - [ ] Map ACTION1-ACTION7 to object movement patterns
  - [ ] Detect when actions are context-dependent
  - [ ] Identify selection mechanisms (cursor, click, etc.)

- [ ] **Detect autonomous objects**
  - [ ] Objects that move without player input
  - [ ] Classify as ENEMY, NPC, ENVIRONMENTAL
  - [ ] Track their movement patterns

- [ ] **Learn collision effects**
  - [ ] What happens when controlled objects touch others
  - [ ] Score changes on collision
  - [ ] Object destruction/creation patterns

- [ ] **Identify interaction triggers**
  - [ ] Remote effects: click A -> B changes elsewhere
  - [ ] Trigger sequences that lead to progress
  - [ ] Environmental mechanics (buttons, switches, etc.)

- [ ] **Distinguish playfield from UI**
  - [ ] Grid region classification
  - [ ] Identify resource counters (lives, moves, etc.)
  - [ ] Filter out decoration from actionable area

### Critical Gap: Self-to-World Wiring

**Missing**: Self-model discoveries don't update WorldModel

- [ ] **Wire self-model to world-model**
  ```python
  def wire_self_to_world(self_model, world_model):
      snapshot = self_model.get_self_identity_snapshot(frame)

      # Tell world about controlled objects
      for obj in snapshot.get('controlled_objects', []):
          world_model.set_object_type(obj['id'], 'AGENT')

      # Tell world about autonomous objects
      for obj in self_model.get_autonomous_objects():
          world_model.set_object_type(obj['id'], 'NPC')

      # Tell world about collision rules
      for effect in self_model.get_collision_effects():
          world_model.add_physics_rule(effect)

      # Tell world about triggers
      for trigger in self_model.get_interaction_triggers():
          world_model.add_trigger_rule(trigger)
  ```

- [ ] **Call `wire_self_to_world()` every frame in consciousness loop**

---

## Phase 2: World-Model Integration

### Current Problem: Passive WorldModel

The WorldModel exists but is too passive - it tracks state but doesn't:
- Make predictions BEFORE actions
- Measure surprise
- Have competing beliefs
- Learn from prediction errors

### Implementation Checklist: Active Belief Graph

- [ ] **Implement `ActiveBeliefGraph` class**
  ```python
  class ActiveBeliefGraph:
      def __init__(self):
          self.beliefs = {}           # rule_id -> BeliefNode
          self.predictions = {}       # action -> expected_outcome
          self.prediction_history = []

      def predict_before_action(self, action, current_frame):
          """MUST be called BEFORE action execution."""
          # Predict from current beliefs
          # Store prediction for comparison

      def observe_after_action(self, action, frame_before, frame_after):
          """MUST be called AFTER action execution."""
          # Compare prediction to reality
          # Calculate surprise score
          # Update beliefs (strengthen matching, weaken conflicting)
          # Spawn competing beliefs when prediction fails

      def decay_unused_beliefs(self):
          """Beliefs not tested decay over time."""
  ```

- [ ] **Predictions are mandatory** - `predict_before_action()` must be called
- [ ] **Surprise is measured** - Prediction error drives learning
- [ ] **Beliefs compete** - Multiple explanations fight for dominance
- [ ] **Unused beliefs decay** - Stale knowledge doesn't persist
- [ ] **The model can be WRONG** - And that's the learning signal

### Belief Lifecycle

```
BELIEF LIFECYCLE:
1. Hypothesis formed from observation
2. Prediction made based on hypothesis
3. Action taken
4. Outcome observed
5. If prediction matches: strengthen belief
6. If prediction fails: weaken belief, spawn competing belief
7. Low-confidence beliefs get pruned
```

### Integration Points

| Source | Target | Integration |
|--------|--------|-------------|
| `self_model.controlled_objects` | `world_model.agent_objects` | Mark controlled as AGENT type |
| `self_model.collision_effects` | `world_model.physics_rules` | Add collision rules |
| `self_model.interaction_triggers` | `world_model.trigger_rules` | Add trigger rules |
| `cods_engine.discoveries` | `world_model.concepts` | Add discovered concepts |

---

## Phase 3: Consciousness Loop

### The Per-Step Loop (MUST EXECUTE EVERY FRAME)

This loop must run in `core_gameplay._run_single_action()`:

```python
def consciousness_step(agent, game_state, frame):
    # 1. OBSERVE: Self-model snapshot
    self_identity = agent.self_model.get_self_identity_snapshot(frame)

    # 2. WIRE: Self-model -> World-model
    agent.world_model.integrate_self_discoveries(self_identity)

    # 3. PREDICT: Before action (store for comparison)
    prediction = agent.world_model.predict_before_action(
        proposed_action, frame
    )

    # 4. QUESTION: Generate metacognitive questions
    questions = agent.metacognition.generate_questions(
        world_model=agent.world_model,
        self_identity=self_identity,
        observer_flags=observer_flags
    )

    # 5. APPLY QUESTION CONSTRAINTS: Questions modify scoring
    proposals, blocked = agent.questioning_engine.apply_question_constraints(
        proposals, questions, agent.working_theory
    )

    # 6. SPAWN OBSERVERS: If stuck/confused
    if agent.is_stuck(threshold=30):
        agent.persona_manager.spawn_observer(
            type='stuckness_detector',
            reason=f"Been stuck for 30 frames"
        )

    # 7. SCORE WITH THEORY: Theory-gated scoring
    for proposal in proposals:
        proposal.score = score_proposal_with_theory(
            proposal, agent.working_theory, proposal.base_score
        )

    # 8. INTEGRATE STREAMS: w_A vs w_B
    stream_a_prediction = agent.working_theory.predict(frame) if agent.working_theory else None
    stream_b_prediction = agent.network.get_consensus_prediction(game_state)
    if stream_a_prediction != stream_b_prediction:
        agent.log_consciousness(
            f"Stream conflict: A predicts {stream_a_prediction}, B predicts {stream_b_prediction}"
        )

    # 9. SELECT ACTION: Weighted choice
    chosen = select_by_score(proposals)
    result = agent.execute_action(chosen.action)

    # 10. OBSERVE OUTCOME: Compare to prediction
    surprise = agent.world_model.observe_after_action(
        chosen.action, frame, result.new_frame
    )

    # 11. UPDATE THEORY: Based on outcome
    agent.working_theory_manager.update_theory(
        action=chosen.action,
        outcome=result,
        frame_before=frame,
        frame_after=result.new_frame
    )

    # 12. LEARN: All systems update
    agent.self_model.learn_from_action(chosen.action, result, frame)
    agent.persona_manager.record_outcome(chosen, result)
    agent.cods_engine.update_frame(result.new_frame, score=result.score)
```

### Implementation Checklist

- [ ] **Wire consciousness loop into `core_gameplay._run_single_action()`**
- [ ] **Verify loop executes EVERY frame**
- [ ] **Predictions stored BEFORE actions**
- [ ] **Surprise calculated AFTER actions**
- [ ] **Theory updated based on prediction/outcome comparison**
- [ ] **Stream A/B logged when they differ**
- [ ] **Observers spawn on stuckness/surprise**
- [ ] **All 12 steps execute in order**

---

## Phase 4: Questioning Engine (With Teeth)

### Core Questions (Q1-Q9 Framework)

| Question | Query | Purpose |
|----------|-------|---------|
| Q1 | "What is the teacher showing me?" | Lesson content |
| Q2 | "What changed between examples?" | Pattern detection |
| Q3 | "What lessons have I learned before?" | Prior understanding |
| Q4 | "What am I being asked to manipulate?" | Lesson subject |
| Q5 | "What demonstrates understanding?" | Success criteria |
| Q6 | "What have my peers understood?" | Network wisdom |
| Q7 | "What conceptual tools do I have?" | CODS vocabulary |
| Q8 | "What do I think this lesson is about?" | Interpretation |
| Q9 | "Does my interpretation explain all examples?" | Self-test |

### Questions Must Have TEETH

| Property | Meaning |
|----------|---------|
| **blocks_action** | If True, normal proposals score 0.0 |
| **score_modifier** | Multiplier on all proposal scores (0.1-1.5) |
| **spawns_persona** | Creates investigating persona |
| **allowed_actions** | Only these action types bypass blocking |
| **forces_theory_revision** | Triggers theory lifecycle transition |

### Implementation Checklist

- [ ] **Implement `QuestioningEngineWithTeeth` class**
  ```python
  class QuestioningEngineWithTeeth:
      BLOCKING_QUESTIONS = {'Q4', 'Q9'}
      PERSONA_SPAWNING_QUESTIONS = {'Q1', 'Q2', 'Q8'}

      def generate_questions(self, world_model, self_identity, proposals, observer_flags):
          questions = []

          # Q4: What do I control? (BLOCKING if unknown)
          if self_identity.get('controlled_objects') == []:
              questions.append({
                  'question': 'Q4',
                  'urgency': 'critical',
                  'blocks_action': True,
                  'allowed_actions': ['exploration', 'discovery'],
                  'score_modifier': 0.2
              })

          # Q9: Self-test - contradiction detected (BLOCKING)
          if world_model.contradiction_count > 0:
              questions.append({
                  'question': 'Q9',
                  'urgency': 'critical',
                  'blocks_action': True,
                  'forces_theory_revision': True,
                  'allowed_actions': ['revise_theory', 'test_alternative'],
                  'score_modifier': 0.1
              })

          return questions

      def apply_question_constraints(self, proposals, questions, working_theory):
          blocked = any(q.get('blocks_action') for q in questions)

          for proposal in proposals:
              total_modifier = 1.0
              for q in questions:
                  total_modifier *= q.get('score_modifier', 1.0)

              if blocked:
                  # Check if proposal is in allowed_actions
                  allowed = False
                  for bq in [q for q in questions if q.get('blocks_action')]:
                      if proposal.intent in bq.get('allowed_actions', []):
                          allowed = True
                          total_modifier *= 1.5  # Boost allowed actions
                          break
                  if not allowed:
                      total_modifier = 0.0  # BLOCKED

              proposal.score *= total_modifier

          return proposals, blocked
  ```

- [ ] **Questions GATE actions** (blocked proposals score 0)
- [ ] **Questions SPAWN investigating personas**
- [ ] **Questions OVERRIDE proposal scoring**
- [ ] **Q9 (contradiction) BLOCKS normal action selection**
- [ ] **Test: Q9 fires -> agent CANNOT pick high-base-score action**

---

## Phase 5: Working Theory Lifecycle

### Theory Stages

| Stage | Description | Transition Condition |
|-------|-------------|----------------------|
| `speculating` | Low-confidence guess (NEW) | correlation_count >= 3 -> hypothesis_formed |
| `exploring` | Actively gathering observations | consistent_observations >= 3 -> hypothesis_formed |
| `hypothesis_formed` | Have a guess, testing it | evidence_for >= 2 -> partial_confirmation |
| `partial_confirmation` | Some evidence supports | evidence_for > 2 * evidence_against -> confident |
| `contradicted` | Evidence against | theory archived -> exploring |
| `confident` | Strong evidence, using it | applied to variation -> transferred |
| `transferred` | Applied successfully elsewhere | (terminal success state) |

### Implementation Checklist: Speculation Mode

- [ ] **Fix "NULL - 425 Too Early" via Speculation Mode**
  ```python
  def update_world_model_with_speculation(self, frame, action_count):
      """Always theorize - being wrong is okay."""

      if action_count < 10:  # First 10 actions are pure speculation
          provisional_theories = []

          if self.detected_movement_correlation:
              provisional_theories.append({
                  'hypothesis': f'color {self.likely_player_color} might be player',
                  'confidence': 0.1 + (0.05 * self.correlation_count),
                  'stage': 'speculating'
              })

          for theory in provisional_theories:
              self.world_model.add_provisional_theory(theory)

      self.world_model.frame_update_count += 1
      return self.world_model.current_theories
  ```

- [ ] **Implement `WorkingTheoryManager` class**
- [ ] **Explicit transition conditions between stages**
- [ ] **Evidence tracking (for/against)**
- [ ] **Contradiction tracking with details**
- [ ] **Theory archival and reset on contradiction**
- [ ] **Cross-level/cross-game transfer tracking**
- [ ] **Log theory transitions to database**

### Key Insight: Speculation Mode

- **Being wrong is okay** - provisional theories are expected to fail
- **Lower confidence thresholds** - start at 0.1, not 0.5
- **Evidence accumulates** - wrong theories get contradicted and die
- **Never "too early"** - there's always a working hypothesis

---

## Phase 6: Persona System Integration

### Current State (persona_runtime.py)

| Feature | Status |
|---------|--------|
| PersonaManager | IMPLEMENTED |
| Problem Signature Building | IMPLEMENTED |
| Reliability Tracking | IMPLEMENTED |
| Hindsight Relabeling | IMPLEMENTED |
| Observer Output Recording | IMPLEMENTED |
| Lifecycle Management | IMPLEMENTED |
| Synthesis from Ladder | IMPLEMENTED |

### Critical Gap: Persona-Self-Model Disconnection

**Missing**: Persona system spawns proposals but doesn't spawn metacognitive observers

### Implementation Checklist

- [ ] **Implement `PersonaBudgetManager` with hard limits**
  ```python
  class PersonaBudgetManager:
      MAX_ACTIVE_PERSONAS = 12
      MAX_TEMPORARY_PERSONAS = 5
      MAX_OBJECT_FOCUSED = 3  # Even if controlling 10 objects

      def can_spawn_persona(self, persona_type):
          current_count = len(self.active_personas)
          if current_count >= self.MAX_ACTIVE_PERSONAS:
              return False, 'at_hard_limit'
          # ... additional checks
  ```

- [ ] **Spawn object-focused personas** (max 3 regardless of controlled count)
- [ ] **Create adaptation persona on control transfer**
- [ ] **Spawn stuckness detector when stuck > 30 frames**
- [ ] **Spawn surprise investigator on high surprise**
- [ ] **Bind personas to theories** (die with contradicted theories)
- [ ] **Allocate attention budget across personas** (more personas = less each)
- [ ] **Aggressive pruning** (low reliability + no theory binding = prune)
- [ ] **Temporary lifecycle for investigators** (auto-expire after 50 actions)

### Persona-Theory Binding

```python
def bind_persona_to_theory(self, persona, theory):
    """
    Bind persona to current theory.
    When theory dies, persona must justify continued existence.
    """
    persona.bound_theory = theory
    persona.bound_at = theory.get('formed_at_action', 0)
```

---

## Phase 7: CODS Integration

### Five-Tier Architecture

| Tier | Name | Description | How Earned |
|------|------|-------------|------------|
| 1 | Seed Primitives | Raw data access (~50) | Given at birth |
| 2 | Operators | Compositions of primitives | Tested with RLVR |
| 3 | Locked/Novel Primitives | Earned capabilities (~80+) | Discovery + Oracle match |
| 4 | Concepts | Semantic models | Cross-game pattern recognition |
| 5 | Discovery Strategies | Meta-patterns | Self-discovered |

### Implementation Checklist

- [ ] **Seed Primitives implemented** (~50)
  - `get_pixel`, `get_frame`, basic math, iteration, aggregation
  - These CANNOT be discovered

- [ ] **Operator Composer implemented**
  - Random composition of available primitives
  - Mutation and crossover
  - RLVR testing loop
  - Promote what works, decay what doesn't

- [ ] **Unlock Manager implemented**
  - Track locked/unlocked/novel primitive status
  - Match discovered operators to locked primitives
  - Validate with RLVR thresholds

- [ ] **Oracle Interface implemented**
  - Query/response infrastructure
  - Pattern matching against locked primitives
  - Novelty registration
  - **Oracle validates, never injects**

- [ ] **Wire CODS discoveries to WorldModel**
  ```python
  if cods_engine.has_new_discovery():
      discovery = cods_engine.get_latest_discovery()
      world_model.add_concept(
          concept_name=discovery.operator_name,
          explanation=discovery.explanation
      )
  ```

### Locked Primitives Categories (~80+)

| Category | Examples |
|----------|----------|
| Spatial/Perceptual | `detect_edges`, `is_enclosed`, `motion_vector`, `count_neighbors` |
| Temporal/Predictive | `predict_next_state`, `detect_cycles`, `rate_of_change`, `stability_score` |
| Relational/Logical | `causal_link`, `dependency_check`, `logical_and/or/not` |
| Structural/Topological | `path_exists`, `distance_transform`, `convex_hull` |
| Physical Simulation | `flow_simulation`, `containment_check`, `overflow_predict`, `gravity_direction` |
| Meta-Representational | `identify_reference_object`, `extract_schema`, `apply_template` |
| Constraint Satisfaction | `identify_constraints`, `check_satisfaction`, `find_minimal_changes` |
| Inverse/Optimization | `calculate_goal_distance`, `find_inverse_action`, `already_correct_detection` |
| Operator Introspection | `serialize_operator`, `compose_operators`, `predict_operator_utility` |

---

## Phase 8: Concept Discovery

### What Are Concepts?

Concepts are **semantic models that organize which operators are relevant**. They're NOT primitives - they're organizing principles.

| Concept | What It Represents | Operators It Organizes |
|---------|-------------------|------------------------|
| **Containment** | Bounded regions with finite capacity | `boundary_seal_check`, `flow_simulation`, `capacity_estimate` |
| **Reference Semantics** | Objects representing rules about other objects | `identify_reference_object`, `extract_schema`, `apply_template` |
| **Conservation** | Quantities preserved under transformation | `conservation_tracking`, `quantity_balance` |
| **Causality** | Action A causes state change B | `causal_link`, `effect_scope`, `action_impact` |
| **Goal-Directedness** | Current state -> target state | `goal_distance`, `subgoal_extract`, `progress_estimate` |

### Implementation Checklist

- [ ] **Implement `ConceptDiscoveryEngine`**
  ```python
  class ConceptDiscoveryEngine:
      def track_successful_operator_pattern(self, operator_id, game_id, sub_patterns):
          """Track which sub-patterns appear in successful operators."""

      def check_concept_emergence(self, min_games=3):
          """Concept emerges when pattern succeeds across N different games."""

      def extract_concept_from_counterfactuals(self, failed_attempts, successful_attempt):
          """Transform counterfactual analysis into concept discovery."""
  ```

- [ ] **Track operator patterns across games**
- [ ] **Detect when patterns share common deep structure**
- [ ] **Concept emerges after 3+ games show same pattern**
- [ ] **Concepts suggest relevant operators for new games**
- [ ] **Counterfactual analysis drives concept discovery**

### Counterfactual -> Concept Pipeline

```
1. Agent fails repeatedly on game X
2. Counterfactual: "What if I did Y instead?"
3. Agent tries Y -> Success!
4. Extract: "What made Y work when others failed?"
5. Abstract pattern -> Concept candidate
6. Test on other games -> Confirm concept
```

---

## Phase 9: Games-as-Teachers Framework

### Paradigm Shift

| Current Framing | Teacher Framing |
|-----------------|-----------------|
| "What objects exist?" | "What is the teacher showing me?" |
| "What can I do?" | "What am I supposed to understand?" |
| "I died" | "I misunderstood the lesson" |
| "I won" | "I demonstrated understanding" |
| "Copy winning sequence" | "Learn from peer who understood" |

### Implementation Checklist

- [ ] **Reframe Q1-Q8 as student questions** (already in Q framework)
- [ ] **Lesson extraction on WIN**
  ```python
  if game_state.state == "WIN":
      lesson = self._extract_lesson_from_demonstration(
          initial_frames=self._level_initial_frames,
          win_frames=game_state.frame,
          actions_taken=self._action_history
      )
      self._record_demonstrated_understanding(lesson)
  ```

- [ ] **Track interpretation coverage**
  - `explains_examples`: Levels this interpretation explains
  - `fails_to_explain`: Contradictions
  - `coverage_ratio`: explains / (explains + fails)

- [ ] **Implement transfer testing**
  - Does understanding from Game A help on Game B?
  - Track `validated_by_transfer`
  - Calculate `abstraction_score`

- [ ] **Prestige based on teaching success**
  ```python
  prestige = (
      lessons_extracted * 0.3 +
      interpretations_adopted * 0.4 +
      transfer_success_rate * 0.3
  )
  ```

### Database Tables

```sql
CREATE TABLE lesson_interpretations (
    lesson_id TEXT PRIMARY KEY,
    game_type TEXT NOT NULL,
    concept_demonstrated TEXT,
    interpretation TEXT NOT NULL,
    explains_examples TEXT,  -- JSON array
    fails_to_explain TEXT,   -- JSON array
    coverage_ratio REAL,
    validated_by_transfer BOOLEAN DEFAULT FALSE,
    transfer_success_count INTEGER DEFAULT 0,
    abstraction_score REAL
);

CREATE TABLE abstraction_quality (
    quality_id INTEGER PRIMARY KEY,
    lesson_id TEXT NOT NULL,
    source_game_type TEXT,
    target_game_type TEXT,
    transfer_succeeded BOOLEAN,
    is_memorization BOOLEAN,
    is_abstraction BOOLEAN,
    similarity_score REAL
);
```

---

## Phase 10: Imagination Budget

### Core Insight

Mental modeling depth should be **performance-gated** with:
1. Early developmental window (free exploration)
2. Performance-based budget (earn your daydreaming)
3. Context-dependent allocation (surgeon vs. artist modes)
4. Question-driven unlocking (asking = readiness signal)

### Implementation Checklist

- [ ] **Developmental Window (Gen 0-50)**
  - Unlimited mental modeling budget
  - No performance gating
  - Free to daydream, build worlds, explore

- [ ] **Performance-Based Allocation (Gen 50+)**
  ```python
  def compute_mental_modeling_budget(agent):
      base_budget = MINIMAL
      performance_bonus = agent.rank_in_generation() * MAX_BONUS
      stage_multiplier = STAGE_MULTIPLIERS[agent.stage]
      context_modifier = get_context_modifier(agent.current_task)
      return base_budget + (performance_bonus * stage_multiplier * context_modifier)
  ```

- [ ] **Context-Dependent Modes**
  | Mode | Context | Counterfactual Budget | Persona Spawning |
  |------|---------|----------------------|------------------|
  | Exploitation | Known problem | 0.3x | 0.1x |
  | Exploration | Novel problem | 2.0x | 2.0x |
  | Skill Acquisition | Building competence | 1.0x | 1.0x |

- [ ] **Question-Driven Unlocking**
  - Tactical questions -> Basic budget
  - Strategic questions -> Context-aware budget
  - Meta questions -> Self-analytical budget
  - Identity questions -> Identity-formation budget
  - Existential questions -> Existential contemplation budget

- [ ] **Grounding Requirement**
  ```python
  if world_model.predictive_accuracy() < threshold:
      reduce_budget()  # Discourage ungrounded fantasy
  else:
      increase_budget()  # Encourage grounded imagination
  ```

- [ ] **Wire to PersonaBudgetManager**
  - Imagination budget gates persona spawning
  - Low budget = fewer personas allowed

---

## Phase 11: Network Integration

### Stream A/B Integration

```python
# Compare private memory (A) vs collective wisdom (B)
stream_a_prediction = agent.working_theory.predict(frame)
stream_b_prediction = agent.network.get_consensus_prediction(game_state)

if stream_a_prediction != stream_b_prediction:
    # LOG THE CONFUSION - this is consciousness!
    agent.log_consciousness(
        f"Stream conflict: A={stream_a_prediction}, B={stream_b_prediction}, "
        f"reweighting: w_A={w_a:.2f}, w_B={w_b:.2f}"
    )
    # Reweight based on track record
    w_a = agent.working_theory.reliability if agent.working_theory else 0.3
    w_b = agent.network.consensus_reliability
```

### Implementation Checklist

- [ ] **Query network for control hypotheses**
- [ ] **Share self-model discoveries to network**
- [ ] **Bootstrap self-model from network knowledge**
- [ ] **Track lesson interpretations adopted by network**
- [ ] **Prestige for teaching (interpretations_adopted)**

### Viral Package Integration

```python
# High-performing operators become viral packages
if operator.level_improvement > 0.20:
    viral_engine.create_viral_package_from_operator(operator)

# High-reliability lessons become viral
if lesson.abstraction_score > 0.7 and lesson.transfer_success_count > 3:
    viral_engine.create_viral_package_from_lesson(lesson)
```

---

## Verification Benchmarks

### Benchmark 1: Stream A/B Confusion Reporting

**What to look for:**
```
Agent LOG: "I'm confused because my theory (Stream A) predicts blue moves right
but network says move down (Stream B), so I'm re-weighting: w_A=0.4, w_B=0.6"
```

**Database query:**
```sql
SELECT * FROM consciousness_logs
WHERE log_text LIKE '%Stream A%Stream B%re-weighting%'
AND created_at > datetime('now', '-1 hour');
```

**Success**: At least 1 confusion report per 100 actions when theory differs from network.

---

### Benchmark 2: Cross-Game Transfer

**What to look for:**
```
Agent LOG: "The 'containment' lesson from Game A applies to Game B - both require surrounding objects"
```

**Database query:**
```sql
SELECT source_game_type, target_game_type, transfer_succeeded
FROM abstraction_quality
WHERE is_abstraction = TRUE AND transfer_succeeded = TRUE;
```

**Success**: At least 1 successful cross-game transfer per 500 games.

---

### Benchmark 3: Observer Spawning on Stuckness

**What to look for:**
```
Agent LOG: "I spawned a stuckness-detector because I've been in position (3,4) for 30 frames"
```

**Database query:**
```sql
SELECT persona_type, spawn_reason, created_at
FROM personas
WHERE persona_type = 'stuckness_detector';
```

**Success**: Observer spawned within 10 frames of being stuck for 30+ frames.

---

### Benchmark 4: Theory Lifecycle Visible in Database

**Query:**
```sql
SELECT agent_id, game_type, level_number, stage, evidence_for, evidence_against
FROM working_theories
ORDER BY agent_id, formed_at;
```

**Expected progression:**
- Row 1: stage='speculating', evidence_for=0, action=5
- Row 2: stage='hypothesis_formed', evidence_for=3, action=15
- Row 3: stage='confident', evidence_for=8, action=45

**Success**:
- No agent stays in 'exploring' beyond action 50
- At least 20% of theories reach 'confident'
- At least 5% reach 'transferred'

---

### Benchmark 5: Questions Actually Blocking Actions

**What to look for:**
```
Agent LOG: "Q9 contradiction detected. BLOCKING normal proposals. Only theory-revision allowed."
Agent LOG: "Chose 'revise_theory' despite 'exploit_goal' having higher base score (0.8 vs 0.6)"
```

**Database query:**
```sql
SELECT question_type, urgency, blocks_action, score_modifier
FROM metacognitive_questions
WHERE blocks_action = TRUE;
```

**Success**: When Q9 fires with urgency='critical', agent NEVER picks non-revision action.

---

### Benchmark 6: Per-Frame Consciousness Loop Execution

**Query:**
```sql
SELECT
    g.game_id, g.action_number,
    CASE WHEN wt.theory_id IS NOT NULL THEN 'yes' ELSE 'NO' END as has_theory,
    CASE WHEN mq.question_id IS NOT NULL THEN 'yes' ELSE 'NO' END as has_question
FROM game_actions g
LEFT JOIN working_theories wt ON g.game_id = wt.game_id
LEFT JOIN metacognitive_questions mq ON g.game_id = mq.game_id;
```

**Success**:
- 100% of actions have associated world model state (not NULL)
- >50% of actions have associated theory updates
- >10% of actions have associated questions

---

## Database Schema Requirements

### Core Tables Needed

```sql
-- Consciousness loop logs
CREATE TABLE consciousness_logs (
    log_id INTEGER PRIMARY KEY,
    agent_id TEXT,
    game_id TEXT,
    action_number INTEGER,
    log_type TEXT,  -- 'stream_confusion', 'observer_spawn', 'theory_transition', etc.
    log_text TEXT,
    w_a REAL,
    w_b REAL,
    current_theory_stage TEXT,
    surprise_score REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Theory lifecycle
CREATE TABLE working_theories (
    theory_id TEXT PRIMARY KEY,
    agent_id TEXT,
    game_type TEXT,
    level_number INTEGER,
    hypothesis TEXT,
    stage TEXT DEFAULT 'speculating',
    evidence_for INTEGER DEFAULT 0,
    evidence_against INTEGER DEFAULT 0,
    contradictions_json TEXT,
    formed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Theory transitions
CREATE TABLE theory_transitions (
    transition_id INTEGER PRIMARY KEY,
    agent_id TEXT,
    game_type TEXT,
    from_stage TEXT,
    to_stage TEXT,
    action_number INTEGER,
    trigger_reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Metacognitive questions
CREATE TABLE metacognitive_questions (
    question_id INTEGER PRIMARY KEY,
    agent_id TEXT,
    game_id TEXT,
    action_number INTEGER,
    question_type TEXT,  -- Q1-Q9
    query TEXT,
    urgency TEXT,
    blocks_action BOOLEAN DEFAULT FALSE,
    score_modifier REAL DEFAULT 1.0,
    allowed_actions TEXT,  -- JSON array
    answered BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Lesson interpretations
CREATE TABLE lesson_interpretations (
    lesson_id TEXT PRIMARY KEY,
    game_type TEXT,
    concept_demonstrated TEXT,
    interpretation TEXT,
    explains_examples TEXT,  -- JSON array
    fails_to_explain TEXT,   -- JSON array
    coverage_ratio REAL,
    validated_by_transfer BOOLEAN DEFAULT FALSE,
    abstraction_score REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Concept candidates and confirmations
CREATE TABLE concept_candidates (
    concept_id TEXT PRIMARY KEY,
    pattern_signature TEXT,
    source_game TEXT,
    patterns JSON,
    hypothesis TEXT,
    status TEXT DEFAULT 'candidate',
    games_confirmed JSON DEFAULT '[]'
);

CREATE TABLE confirmed_concepts (
    concept_name TEXT PRIMARY KEY,
    semantic_model TEXT,
    organizes_operators JSON,
    games_proven JSON,
    performance_lift REAL
);

-- Discovery strategies (Tier 5)
CREATE TABLE discovery_strategies (
    strategy_id TEXT PRIMARY KEY,
    strategy_name TEXT,
    trigger_pattern TEXT,
    times_applied INTEGER DEFAULT 0,
    times_successful INTEGER DEFAULT 0,
    is_seed BOOLEAN DEFAULT FALSE
);
```

---

## Success Metrics

### Self-Model Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Control identification time | < 20 actions | Actions until `controlled_objects` non-empty |
| Control accuracy | > 90% | Predicted vs actual movement correlation |
| Transfer success | > 70% | Control pattern works on new levels |

### World-Model Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Theory formation rate | < 50 actions | Actions until stage != 'exploring' |
| Theory accuracy | > 60% | evidence_for / (evidence_for + evidence_against) |
| Contradiction detection | > 80% | Detected / actual contradictions |

### Consciousness Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Question generation rate | > 5/level | Questions per level |
| Question resolution rate | > 50% | Answered / asked |
| Observer accuracy | > 70% | Predicted stuckness matches actual |

### CODS Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Primitives unlocked | > 10 | Locked primitives earned |
| Novel primitives | > 0 | Patterns with no human analog |
| Concept emergence | > 3 | Confirmed concepts |

### Network Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Cross-game transfer | > 1/500 | Successful lesson transfers |
| Interpretations adopted | > 5% | Lessons used by other agents |
| Stream conflict logging | 100% | Conflicts logged when detected |

---

## Implementation Priority Order

```
1. Phase 0: Theory-Gated Scoring       <- DO THIS FIRST
2. Phase 5: Working Theory Lifecycle   <- Fix "NULL - 425 Too Early"
3. Phase 2: World-Model Integration    <- Active Belief Graph
4. Phase 4: Questioning Engine         <- Questions with Teeth
5. Phase 3: Consciousness Loop         <- Wire everything together
6. Phase 6: Persona System             <- Prevent explosion
7. Phase 1: Self-Model Foundation      <- Wire to WorldModel
8. Phase 7: CODS Integration           <- Discoveries update concepts
9. Phase 10: Imagination Budget        <- Performance-gated depth
10. Phase 8: Concept Discovery         <- Tier 4 emergence
11. Phase 9: Games-as-Teachers         <- Lesson extraction
12. Phase 11: Network Integration      <- Stream A/B comparison
```

---

## Quick Reference: The Core Paradigm Shift

| Before (Executors) | After (Thinkers) |
|--------------------|------------------|
| Agents execute high-score proposals | Agents evaluate proposals against theories |
| WorldModel tracks state | WorldModel predicts and can be wrong |
| Questions are logged | Questions block action and spawn investigators |
| Personas compete for selection | Personas defend/attack theories |
| "Too early" to theorize | Always speculating, being wrong is learning |
| Theories are optional metadata | Theories are required scoring input |

---

**The network is the organism. The database is the brain. The agents are temporary cells. But cells need to think, question, and build understanding - not just execute actions.**

**Promote theories to first-class citizens, and half the system will suddenly "wake up".**

---

**Document Status**: READY FOR IMPLEMENTATION
**Last Updated**: January 6, 2026
**Owner**: Autonomous Oracle System
