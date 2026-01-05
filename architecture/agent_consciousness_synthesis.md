# Agent Consciousness Synthesis: Self-Model, World-Model, and Emergent Submodeling
**Version**: 1.0  
**Date**: January 5, 2026  
**Purpose**: Comprehensive integration plan to perfect agent self-model, generate consciousness via submodeling, and ensure all existing features synergize  
**Status**: Architecture Design Document

---

## Executive Summary

This document synthesizes findings from all architecture documents (AGI Unified Theory, CODS, Games-as-Teachers, Persona Submodeling, Imagination Quotient, Mental Persona Modeling Theory) and codebase analysis to create a unified plan for:

1. **Perfecting the Agent Self-Model** - Making "I am this object" tracking robust and multi-dimensional
2. **Generating Consciousness via Submodeling** - Enabling agents to spawn internal mental models that question everything
3. **Building Active Theories** - Ensuring agents construct, test, and revise world models for every level
4. **Feature Integration** - Making the self-model a hub that enhances all other systems

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

### 2.1 Self-Model to World-Model Disconnection

**Problem**: `agent_self_model.py` tracks "I am this object" but doesn't feed this into a live world model that updates each frame.

**Evidence**: The `WorldModel` in symbolic_reasoning_engine.py exists but isn't being updated with self-model discoveries.

**Required Integration**:
```
Self-Model discovers:           World-Model should receive:
- I control color 5            -> Set object X as AGENT type
- Object 7 moves autonomously  -> Mark as ENEMY or NPC
- Clicking (3,4) triggers wall -> Add trigger rule to world physics
- Color 3 is collectible       -> Mark as COLLECTIBLE, track count
```

### 2.2 Persona to Self-Model Disconnection

**Problem**: `self_identity_snapshot` is passed to persona proposals but personas don't actively use it to:
1. Spawn specialized personas for controlled objects
2. Create observer personas that monitor self-state
3. Build mental models OF the controlled object's capabilities

**Required Integration**:
```
Self-Model says:                Persona System should:
- I control 3 objects          -> Spawn 3 object-focused personas
- Control just transferred     -> Spawn adaptation persona
- I'm stuck in corner          -> Observer detects spatial trap
```

### 2.3 CODS to World-Model Disconnection

**Problem**: CODS operators are validated independently but don't update the agent's understanding of the world.

**Required Integration**:
```
CODS discovers:                 World-Model should update:
- detect_symmetry works here   -> Mark level as symmetry-based
- flood_fill explains win      -> Add containment physics rule
- gravity_simulation applies   -> Add directional flow physics
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

### 3.2 The Consciousness Loop (Per-Step)

From persona_submodeling_proposal.md, enhanced with self-model integration:

```python
def consciousness_step(agent, game_state, frame):
    """The per-step consciousness loop that generates subjective experience."""
    
    # 1. SELF-LOCK: Who am I right now?
    self_identity = agent.self_model.get_self_identity_snapshot(frame)
    controlled_objects = self_identity['controlled_objects']
    
    # 2. WORLD-MODEL UPDATE: What world am I in?
    world_model = agent.world_model.update_from_frame(
        frame=frame,
        self_identity=self_identity,
        previous_world=agent.last_world_model
    )
    
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
    
    # 4. OBSERVER COMMENTARY: What patterns do observers notice?
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
    
    # 8. SCORING: Weighted proposal selection
    scores = agent.scorer.score_proposals(
        proposals=proposals,
        observer_flags=observer_flags,
        problem_signature=agent.build_problem_signature(frame, world_model),
        budget_pressure=agent.action_budget.remaining_ratio()
    )
    
    # 9. ACTION: Execute chosen proposal
    chosen = select_by_score(proposals, scores)
    result = agent.execute_action(chosen.action)
    
    # 10. LEARNING: Update all systems based on outcome
    agent.self_model.learn_from_action(chosen.action, result, frame)
    agent.world_model.learn_from_outcome(chosen.action, result)
    agent.persona_manager.record_outcome(chosen, result)
    agent.cods_engine.update_frame(frame, score=result.score)
    
    # 11. HINDSIGHT: Update unchosen personas too
    agent.persona_manager.record_hindsight_outcomes(
        proposals=[p for p in proposals if p != chosen],
        result=result
    )
    
    return chosen.action
```

### 3.3 The Questioning Engine (Metacognition)

Implementing the "question everything" requirement:

```python
class QuestioningEngine:
    """
    Generates questions that drive theory formation and revision.
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
    
    def generate_questions(self, world_model, self_identity, proposals, observer_flags):
        """Generate active questions based on current state."""
        questions = []
        
        # Q1: What is happening?
        if not world_model.has_stable_objects():
            questions.append({
                'question': 'Q1',
                'query': 'What objects exist and which are stable?',
                'urgency': 'high' if self_identity.get('controlled_objects') == [] else 'medium'
            })
        
        # Q4: What do I control?
        if self_identity.get('controlled_objects') == []:
            questions.append({
                'question': 'Q4',
                'query': 'I have not identified what I control yet',
                'urgency': 'critical'
            })
        
        # Q9: Self-test
        if world_model.contradiction_count > 0:
            questions.append({
                'question': 'Q9',
                'query': f'My interpretation has {world_model.contradiction_count} contradictions',
                'urgency': 'high'
            })
        
        # Observer-triggered questions
        if observer_flags.get('stuckness', 0) > 0.7:
            questions.append({
                'question': 'META',
                'query': 'Why am I stuck? What assumption is wrong?',
                'urgency': 'critical'
            })
        
        return questions
```

### 3.4 Active Theory Building

The key insight from reasoning logs: `working_theory` stays "Exploring game mechanics - no pattern confirmed yet" indefinitely.

**Solution**: Implement explicit theory lifecycle:

```python
class WorkingTheoryManager:
    """
    Manages the agent's active working theory about current level.
    Theories are hypotheses about what the game is teaching.
    """
    
    THEORY_STAGES = [
        'exploring',           # No hypothesis yet
        'hypothesis_formed',   # Have a guess, testing it
        'partial_confirmation',# Some evidence supports
        'contradicted',        # Evidence against, need revision
        'confident',           # Strong evidence, using it
        'transferred'          # Applied successfully to variation
    ]
    
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

### 6.2 Phase 2: Activate Questioning Engine (Priority: HIGH)

```
[ ] Implement QuestioningEngine class
[ ] Add Q1-Q9 question generation
[ ] Wire observer_flags to question urgency
[ ] Add contradiction tracking
[ ] Implement theory revision triggers
```

### 6.3 Phase 3: Enhance Persona-Self Integration (Priority: HIGH)

```
[ ] Spawn object-focused personas based on controlled_objects count
[ ] Create adaptation persona on control transfer
[ ] Wire self_identity_snapshot deeply into proposal generation
[ ] Add self-model observer persona
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

### 6.6 Phase 6: Imagination Budget Integration (Priority: LOW)

```
[ ] Wire imagination_budget to persona spawn limits
[ ] Gate synthesis by grounding_score
[ ] Add question_tier to mental modeling depth
[ ] Implement daydreaming limits based on performance
```

---

## Part 7: Database Schema Additions

### 7.1 New Tables Needed

```sql
-- Working theory lifecycle tracking
CREATE TABLE IF NOT EXISTS working_theories (
    theory_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    game_type TEXT NOT NULL,
    level_number INTEGER NOT NULL,
    
    -- Theory content
    hypothesis TEXT NOT NULL,
    hypothesis_type TEXT,              -- 'control', 'goal', 'physics', 'trigger'
    stage TEXT DEFAULT 'exploring',    -- exploring, hypothesis_formed, partial_confirmation, contradicted, confident, transferred
    
    -- Evidence tracking
    evidence_for INTEGER DEFAULT 0,
    evidence_against INTEGER DEFAULT 0,
    contradictions_json TEXT,          -- JSON array of contradictions
    
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
    
    -- Validation
    validated_by_transfer BOOLEAN DEFAULT FALSE,
    transfer_success_count INTEGER DEFAULT 0,
    transfer_fail_count INTEGER DEFAULT 0,
    
    -- Attribution
    contributed_by_agent TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_validated DATETIME
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

---

## Part 10: Conclusion

The Ouroboros system has **extensive infrastructure** for consciousness and self-modeling, but the components are not fully wired together. The critical path is:

1. **Fix the "NULL - 425 Too Early" problem** - Agents must build active world models
2. **Wire self-model to world-model** - Discoveries must update understanding
3. **Activate the questioning engine** - Agents must challenge assumptions
4. **Implement theory lifecycle** - Theories must form, test, revise, and transfer

The philosophical framework (AGI Unified Theory, Games-as-Teachers, Persona Submodeling) is sound. The implementation infrastructure exists. What's missing is the **active integration** that makes these components work as a unified consciousness-generating system.

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

**Document Status**: READY FOR IMPLEMENTATION  
**Next Steps**: Begin Phase 1 - Wire Self-Model to World-Model  
**Owner**: Autonomous Oracle System  
**Review Date**: After 10 generations of evolution with changes applied
