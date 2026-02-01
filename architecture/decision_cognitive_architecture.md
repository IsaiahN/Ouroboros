# Decision and Cognitive Architecture

**Version**: 1.0
**Date**: 2026-02-01
**Purpose**: Complete documentation of how the Decision Rung System, Cognitive Stage System, and CognitiveCore facade work together from game start to post-game learning.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Component Architecture](#component-architecture)
3. [The Decision Rung System](#the-decision-rung-system)
4. [The Cognitive Stage System](#the-cognitive-stage-system)
5. [The CognitiveCore Facade](#the-cognitivecore-facade)
6. [Complete Game Flow](#complete-game-flow)
7. [Rung Reference](#rung-reference)
8. [Integration Points](#integration-points)

---

## System Overview

The BitterTruth-AI system uses a modular, layered architecture to make action decisions. At its core are three complementary systems:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          GAMEPLAY ORCHESTRATION                         │
│                                                                         │
│   CoreGameplay  ──►  GameLoop  ──►  (per-action cycle)                 │
│        │                │                    │                          │
│        ▼                ▼                    ▼                          │
│   ┌─────────────────────────────────────────────────────────────┐      │
│   │               DECISION RUNG SYSTEM                           │      │
│   │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐             │      │
│   │  │Rung 1│►│Rung 2│►│Rung 3│►│ ... │►│Rung N│             │      │
│   │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘             │      │
│   │         (Ladder strategy: first confident answer wins)       │      │
│   └─────────────────────────────────────────────────────────────┘      │
│                                │                                        │
│                                ▼                                        │
│   ┌─────────────────────────────────────────────────────────────┐      │
│   │                      ENGINE REGISTRY                         │      │
│   │                                                              │      │
│   │  CognitiveCore      CognitiveStageSystem     SensationEngine │      │
│   │  IThread            ViralPackageEngine       SelfModel       │      │
│   │  ...many more engines...                                     │      │
│   └─────────────────────────────────────────────────────────────┘      │
│                                │                                        │
│                                ▼                                        │
│   ┌─────────────────────────────────────────────────────────────┐      │
│   │                     DATABASE (SQLite)                        │      │
│   │    action_traces, winning_sequences, agent_cognitive_stages  │      │
│   │    game_lessons_learned, viral_packages, ...                 │      │
│   └─────────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### 1. Decision Rung System (`decision_rung_system.py`)

**Purpose**: Modular action selection via pluggable "rungs" that can be reordered like LEGO bricks.

**Key Classes**:
- `DecisionRung` - Abstract base class for all rungs
- `RungResult` - Standard output from a rung (action, confidence, reason, weights)
- `KnowledgeProvenance` - Tracks HOW knowledge became knowable (epistemological provenance)
- `DecisionRungSystem` - Orchestrates rung execution with strategy selection

**Current Rung Count**: 44 rungs across 6 categories

### 2. Cognitive Stage System (`engines/cognition/cognitive_stages.py`)

**Purpose**: Tracks agent developmental progression through Piaget-inspired cognitive stages.

**Stages**:
1. **PREOPERATIONAL** - Reactive exploration, learning cause-effect
2. **CONCRETE_OPERATIONAL** - Can apply learned sequences, understands reversibility
3. **FORMAL_OPERATIONAL** - Hypothetical-deductive reasoning, abstract generalization

### 3. CognitiveCore Facade (`engines/self_model/cognitive_core.py`)

**Purpose**: Unified cognitive interface composing multiple engines into a clean SelfModelInterface.

**Composed Engines**:
- `EmbeddingMatcher` - Cross-game neural similarity
- `FewShotRelations` - Relational invariants from few examples
- `NetworkSharingEngine` - Network knowledge exchange
- `ControlTracker` - "I am this object" tracking

---

## The Decision Rung System

### Core Concept: Rungs as Cognitive Modules

Each rung is a self-contained decision module that:
1. Receives the current `game_state` and `context`
2. Returns a `RungResult` with optional action suggestion and confidence
3. Can modify action weights without suggesting a specific action (filter rungs)

### Rung Result Structure

```python
@dataclass
class RungResult:
    action: Optional[str] = None          # e.g., "ACTION1" or None
    confidence: float = 0.0               # 0.0 to 1.0
    reason: str = ""                      # Human-readable explanation
    weights: Optional[Dict[str, float]] = None  # Per-action weight modifiers
    metadata: Dict[str, Any] = {}         # Debug info
    primitives_used: List[str] = []       # Which seed primitives contributed
    provenance: Optional[KnowledgeProvenance] = None  # Epistemological source
```

### Knowledge Provenance (Epistemological Tracking)

**Why it matters**: Prevents the "amplification != validity" trap where frequently-tried patterns gain unwarranted confidence.

```python
@dataclass
class KnowledgeProvenance:
    detection_source: str = "unknown"     # 'action_traces', 'winning_sequences', etc.
    sample_size: int = 0                  # Data points supporting this
    agent_diversity: int = 0              # Different agents that contributed
    temporal_spread_hours: float = 0.0    # Time spread of observations
    validation_type: str = "frequency"    # 'frequency', 'outcome_based', 'win_validated', 'cross_game'
    positive_outcomes: int = 0            # Actions leading to good results
    negative_outcomes: int = 0            # Actions leading to deaths
    crystallization_stage: int = 1        # 1=detected, 2=classified, 3=amplified, 4=normalized
    resonance_games: int = 0              # Cross-game pattern matches
    resonance_score: float = 0.0          # Structural similarity (0-1)
```

### Decision Strategies

The system supports five strategies for combining rung outputs:

| Strategy | Description | When to Use |
|----------|-------------|-------------|
| **CONTEXT_ADAPTIVE** | Selects strategy based on context | **Default** - recommended for production |
| **LADDER** | First confident answer wins | Fast, deterministic replay |
| **WEIGHTED** | All rungs vote, weighted sum | Complex decisions needing consensus |
| **PHASED** | Different ordering by budget phase | Adaptive exploration/exploitation |
| **PARALLEL** | Run all, pick highest confidence | When order shouldn't matter |

### Context-Adaptive Strategy (Default)

**Problem Solved**: The original LADDER strategy had an "early exit problem" - when a suggestion rung fires with high confidence, it discards all accumulated filter weights and ignores rungs below it. This meant `network_wisdom`, `theory_gate`, and the carefully accumulated weights from `death_avoidance` could be discarded.

**Solution**: CONTEXT_ADAPTIVE selects the appropriate sub-strategy based on game context:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     CONTEXT_ADAPTIVE DECISION FLOW                       │
│                                                                          │
│  Phase 1: EMERGENCY CHECK (always LADDER semantics)                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Check: infinite_loop_breaker, coordinate_oscillation            │   │
│  │  If triggered → RETURN immediately (emergencies override all)    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                │                                         │
│                                ▼                                         │
│  Phase 2: CONTEXT ANALYSIS                                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  IF replay_mode:                                                 │   │
│  │      → Use LADDER (explicit replay)                              │   │
│  │                                                                   │   │
│  │  ELIF active_sequence AND sequence_position < len(sequence):     │   │
│  │      → Use LADDER (still replaying checkpoint prefix)            │   │
│  │      Note: Once position >= len, falls through to frontier check │   │
│  │                                                                   │   │
│  │  ELIF frontier_mode (unbeaten level):                            │   │
│  │      → Use WEIGHTED (all rungs vote, nothing discarded)          │   │
│  │                                                                   │   │
│  │  ELIF optimization_mode (refining beaten game):                  │   │
│  │      → Use WEIGHTED (find improvements)                          │   │
│  │                                                                   │   │
│  │  ELIF game_state_mode == 'exploration':                          │   │
│  │      → Use WEIGHTED                                              │   │
│  │                                                                   │   │
│  │  ELIF has_winning_sequence AND NOT active_sequence:              │   │
│  │      → Use WEIGHTED (beaten level, fresh attempt)                │   │
│  │                                                                   │   │
│  │  ELSE:                                                            │   │
│  │      → Use LADDER (backwards compatibility)                      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                │                                         │
│                                ▼                                         │
│  Phase 3: EXECUTE with selected strategy (excluding emergency rungs)    │
└─────────────────────────────────────────────────────────────────────────┘
```

**Edge Case Handling**:

1. **Frontier Checkpoint Replay**: When replaying a checkpoint prefix on an unbeaten level:
   - Phase 1 (replaying prefix): LADDER - follow known-good path
   - Phase 2 (prefix exhausted, `sequence_position >= len`): Falls through to `frontier_mode` → WEIGHTED
   - This correctly transitions from deterministic replay to exploration at the right moment

2. **Beaten Level Fresh Attempt**: When a winning sequence exists but isn't being actively replayed:
   - Routes to WEIGHTED so discovery_exploitation can't short-circuit network_wisdom
   - Allows finding improvements even without explicit optimization_mode flag

**Key Benefits**:
1. **Graduated Safety Preserved**: On frontier levels, `death_avoidance` weights are multiplied into the final decision, not discarded
2. **All Rungs Vote**: `network_wisdom`, `theory_gate`, and other rungs all contribute to weighted selection
3. **Deterministic Replay**: When following a winning sequence, LADDER ensures exact replay
4. **Emergency Override**: Loop breakers always fire first regardless of mode
5. **Clean Phase Transitions**: Checkpoint prefix exhaustion automatically switches to exploration

### Ordering Presets

Seven built-in orderings optimized for different scenarios:

1. **efficiency** (15 rungs) - Fast, production default
2. **llm_optimal** (40 rungs) - Understanding-first, all features
3. **human_brain** (18 rungs) - Parallel attention + fear interrupt
4. **comprehensive** (42 rungs) - Full coverage, organized by category
5. **minimal** (6 rungs) - Fastest possible
6. **frontier_exploration** (12 rungs) - Heavy exploration for unbeaten games
7. **phased_\*** (3 variants) - Phase-specific subsets

---

## The Cognitive Stage System

### Stage Progression Model

Agents develop through three Piaget-inspired cognitive stages:

```
┌───────────────────────────────────────────────────────────────────────┐
│                        PREOPERATIONAL                                  │
│  • Explores through action-effect observation                          │
│  • No planning, reactive behavior                                      │
│  • Learning object permanence and causation                           │
│                                                                        │
│  Capabilities: action_exploration, object_observation, pattern_recog  │
│                                                                        │
│  Exit Requirements:                                                    │
│    - games_played >= 5                                                │
│    - sequences_discovered >= 1                                         │
│    - object_control_learned = true                                    │
│    - action_effect_pairs >= 3                                         │
└────────────────────────────────┬──────────────────────────────────────┘
                                 │
                                 ▼
┌───────────────────────────────────────────────────────────────────────┐
│                      CONCRETE_OPERATIONAL                              │
│  • Can apply learned sequences                                        │
│  • Understands conservation and reversibility                         │
│  • Logical thinking about concrete objects                            │
│                                                                        │
│  Capabilities: + sequence_following, reversibility, conservation      │
│                                                                        │
│  Exit Requirements:                                                    │
│    - games_played >= 20                                               │
│    - sequences_discovered >= 5                                         │
│    - hypotheses_created >= 2                                          │
│    - cross_game_transfer = true                                       │
│    - validation_success_rate >= 0.6                                   │
└────────────────────────────────┬──────────────────────────────────────┘
                                 │
                                 ▼
┌───────────────────────────────────────────────────────────────────────┐
│                      FORMAL_OPERATIONAL                                │
│  • Hypothetical-deductive reasoning                                   │
│  • Can create and test hypotheses                                     │
│  • Abstract pattern generalization                                    │
│                                                                        │
│  Capabilities: + hypothesis_generation, abstract_generalization,      │
│                  hypothetical_reasoning, cross_domain_transfer        │
│                                                                        │
│  This is the highest stage - no further progression                   │
└───────────────────────────────────────────────────────────────────────┘
```

### Stage-Based Capabilities

```python
def get_stage_capabilities(self, agent_id: str) -> Dict[str, bool]:
    """What cognitive capabilities an agent has based on their stage."""
    stage = self.get_stage(agent_id)

    return {
        # All agents (PREOPERATIONAL+)
        'action_exploration': True,
        'object_observation': True,
        'pattern_recognition': True,

        # CONCRETE_OPERATIONAL+
        'sequence_following': stage in ['concrete_operational', 'formal_operational'],
        'reversibility_understanding': stage in ['concrete_operational', 'formal_operational'],
        'conservation_of_state': stage in ['concrete_operational', 'formal_operational'],

        # FORMAL_OPERATIONAL only
        'hypothesis_generation': stage == 'formal_operational',
        'abstract_generalization': stage == 'formal_operational',
        'hypothetical_reasoning': stage == 'formal_operational',
        'cross_domain_transfer': stage == 'formal_operational',
    }
```

---

## The CognitiveCore Facade

### Purpose

The `CognitiveCore` replaces the deprecated 10,000+ line `AgentSelfModel` monolith with clean delegation to focused engines.

### Composed Engines

```
CognitiveCore (Facade)
    │
    ├── EmbeddingMatcher
    │   └── get_embedding_suggested_action() - Cross-game neural similarity
    │
    ├── FewShotRelations
    │   └── get_few_shot_control_relations() - Relational invariants
    │
    ├── NetworkSharingEngine
    │   └── get_network_object_inventory() - Query network knowledge
    │   └── share_control_discovery_to_network() - Publish discoveries
    │
    └── ControlTracker
        └── "I am this object" correlation tracking
```

### Interface Methods

```python
class CognitiveCore:
    """Unified cognitive interface for agent self-awareness."""

    # Action suggestions based on frame embeddings
    def get_embedding_suggested_action(
        self, game_type, level, current_frame, action_scores, top_k
    ) -> Optional[Dict[str, Any]]

    # Current hypothesis being tested
    def get_current_prediction(self) -> Optional[Dict[str, Any]]
    def set_current_prediction(self, prediction: Optional[Dict[str, Any]]) -> None

    # Few-shot learning from sequence abstraction
    def get_few_shot_control_relations(
        self, game_id, level, min_confidence
    ) -> Optional[Dict[str, Any]]

    # Network knowledge about interactable objects
    def get_network_object_inventory(
        self, game_type, level
    ) -> Dict[str, Any]

    # Share discoveries with the network
    def share_control_discovery_to_network(
        self, agent_id, game_id, level, ...
    ) -> bool
```

---

## Complete Game Flow

### Phase 1: Game Initialization

```
┌─────────────────────────────────────────────────────────────────────┐
│                         GAME START                                   │
│                                                                      │
│  1. CoreGameplay.play_single_game(game_id, agent_config)            │
│           │                                                          │
│           ▼                                                          │
│  2. Create DecisionRungSystem with ordering preset                  │
│     └─► Load rungs by priority (e.g., 'efficiency' = 15 rungs)      │
│           │                                                          │
│           ▼                                                          │
│  3. Create ContextBuilder with agent state                          │
│     └─► Load prior_lessons from game_lessons_learned                │
│     └─► Load winning_sequences if available                          │
│     └─► Query cognitive_stage for agent                             │
│           │                                                          │
│           ▼                                                          │
│  4. Create GameEnvironment via ArcApiAdapter                        │
│     └─► Authenticate with ARC AGI 3 API                             │
│     └─► Get initial observation (frame, state, level)               │
│           │                                                          │
│           ▼                                                          │
│  5. GameLoop enters PLAYING phase                                   │
└─────────────────────────────────────────────────────────────────────┘
```

### Phase 2: Action Loop (Per-Action Cycle)

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PER-ACTION CYCLE                                 │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  STEP 1: Build Context                                       │   │
│  │                                                              │   │
│  │  ContextBuilder.build_context(observation, loop_state)       │   │
│  │    ├── game_type, level, action_count                        │   │
│  │    ├── frontier_mode (true if no winning sequence)          │   │
│  │    ├── prior_lessons (from game_lessons_learned)            │   │
│  │    ├── active_sequence (if replaying)                        │   │
│  │    ├── frame_hash (for network queries)                      │   │
│  │    └── agent_role, cull_distance, cognitive_stage            │   │
│  └────────────────────────────────┬────────────────────────────┘   │
│                                   │                                  │
│                                   ▼                                  │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  STEP 2: Decision Rung System                                │   │
│  │                                                              │   │
│  │  DecisionRungSystem.decide(game_state, context)              │   │
│  │                                                              │   │
│  │  LADDER STRATEGY (default):                                  │   │
│  │  ┌──────────────────────────────────────────────────────┐   │   │
│  │  │  FOR each rung in priority order:                     │   │   │
│  │  │    result = rung.evaluate(game_state, context)        │   │   │
│  │  │                                                        │   │   │
│  │  │    IF result.weights:                                  │   │   │
│  │  │      accumulated_weights *= result.weights             │   │   │
│  │  │                                                        │   │   │
│  │  │    IF result.has_suggestion(threshold):               │   │   │
│  │  │      RETURN (result.action, result.reason)            │   │   │
│  │  │                                                        │   │   │
│  │  │  END FOR                                               │   │   │
│  │  │  RETURN weighted_random_choice(accumulated_weights)    │   │   │
│  │  └──────────────────────────────────────────────────────┘   │   │
│  └────────────────────────────────┬────────────────────────────┘   │
│                                   │                                  │
│                                   ▼                                  │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  STEP 3: Execute Action                                      │   │
│  │                                                              │   │
│  │  GameEnvironment.step(action)                                │   │
│  │    └─► Send ACTION1-ACTION7 to ARC AGI 3 API                │   │
│  │    └─► Receive new Observation (frame, state, level)        │   │
│  └────────────────────────────────┬────────────────────────────┘   │
│                                   │                                  │
│                                   ▼                                  │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  STEP 4: Process Outcome                                     │   │
│  │                                                              │   │
│  │  OutcomeProcessor.process(before_state, action, observation) │   │
│  │    ├── Detect frame_changed (visual diff)                   │   │
│  │    ├── Detect level_changed, score_changed                  │   │
│  │    ├── Detect is_death, is_level_complete, is_game_win     │   │
│  │    ├── Record action_trace to database                      │   │
│  │    └─► Return ActionOutcome                                 │   │
│  └────────────────────────────────┬────────────────────────────┘   │
│                                   │                                  │
│                                   ▼                                  │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  STEP 5: Update Learning Systems                             │   │
│  │                                                              │   │
│  │  LearningSystems.update(loop_state, action, outcome)         │   │
│  │    ├── Update self_model (control tracking)                 │   │
│  │    ├── Update terminal_patterns (if death)                  │   │
│  │    ├── Update sensation_engine (object feelings)            │   │
│  │    └── Update cognitive_stage competencies                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  IF outcome.is_terminal:                                            │
│    EXIT to Phase 3                                                  │
│  ELSE:                                                              │
│    CONTINUE to next action                                          │
└─────────────────────────────────────────────────────────────────────┘
```

### Phase 3: Post-Game Processing

```
┌─────────────────────────────────────────────────────────────────────┐
│                        POST-GAME PROCESSING                          │
│                                                                      │
│  1. GameLoop creates GameResult                                     │
│     ├── final_score, levels_completed, total_actions                │
│     ├── is_win, is_full_win                                         │
│     └── action_sequence (full replay)                               │
│           │                                                          │
│           ▼                                                          │
│  2. LearningSystems.on_game_end(result)                             │
│     │                                                                │
│     ├── IF is_full_win:                                             │
│     │     Store in winning_sequences_full_game                      │
│     │     Mark game as OPTIMIZED mode                               │
│     │                                                                │
│     ├── IF is_level_complete (partial):                             │
│     │     Store in winning_sequences (per-level)                    │
│     │     Update frontier_checkpoints (best partial progress)       │
│     │                                                                │
│     ├── Extract game_lessons_learned                                │
│     │     ├── Which actions caused deaths (with severity)          │
│     │     ├── Which actions led to wins (with confidence)          │
│     │     └── Frame patterns before terminal states                 │
│     │                                                                │
│     ├── Update cognitive_stage competencies                         │
│     │     ├── games_played += 1                                    │
│     │     ├── sequences_discovered += (new sequences)              │
│     │     └── Evaluate stage transition                            │
│     │                                                                │
│     ├── Update agent prestige (network contribution)                │
│     │     ├── network_enrichment (new knowledge)                   │
│     │     ├── viral_spread (knowledge adoption)                    │
│     │     └── validation_value (quality control)                   │
│     │                                                                │
│     └── Create/update viral_packages (horizontal transfer)         │
│           ├── Package winning strategies                            │
│           ├── Package death avoidance patterns                      │
│           └── Mark failed patterns as pariahs                       │
│           │                                                          │
│           ▼                                                          │
│  3. Return GameResult to caller                                     │
│     └─► EvolutionRunner records to database                        │
│     └─► Agent lifecycle updated (prestige, fitness)                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Rung Reference

### Category: EMERGENCY (Priority 1-5)

| Rung | Priority | Purpose |
|------|----------|---------|
| `infinite_loop_breaker` | 1 | Break stuck loops after 15+ repeated actions |
| `coordinate_oscillation` | 2-3 | Detect bouncing between coordinates |

### Category: ORIENTATION (Priority 5-20)

| Rung | Priority | Purpose |
|------|----------|---------|
| `imagination_budget` | 4 | Allocate compute based on novelty |
| `breakthrough_budget` | 6 | Dynamic action allocation for breakthrough potential |
| `regulatory_signal` | 7 | Network homeostasis signals |
| `survey` | 8 | What's salient in this frame? |
| `network_exploration_stats` | 9 | Coverage tracking, coldspot identification |
| `questioning_engine` | 10 | What don't I understand? |
| `exploration_phase` | 12-22 | Phase-based exploration forcing |
| `frustration_detection` | 13 | Detect stuck agents, trigger network signals |

### Category: FILTER (Priority 15-25)

| Rung | Priority | Purpose |
|------|----------|---------|
| `death_avoidance` | 15 | Avoid actions that led to death |
| `prior_lessons` | 16 | Apply graduated weights from game_lessons_learned |
| `pariah_avoidance` | 17 | Avoid network-marked bad patterns |
| `terminal_pattern` | 14-17 | Recognize approaching terminal states |
| `three_layer_filter` | 18-55 | Meta-learning filter preventing waste |

### Category: HYPOTHESIS (Priority 25-40)

| Rung | Priority | Purpose |
|------|----------|---------|
| `scientific_method` | 10-25 | Theory formation and testing |
| `theory_gate` | 24-32 | Working theory validation |
| `metacognitive_prediction` | 18-27 | Make predictions, learn from errors |
| `deliberation_system` | 22-29 | TRM-inspired iterative refinement |
| `two_streams` | 16-35 | Stream A vs Stream B conflict detection |
| `i_thread` | 18-31 | Persistent identity, stream weighting |
| `sensation_engine` | 26-33 | Emotional context for actions |
| `resonance_detector` | 28-34 | Cross-role pattern discovery |

### Category: EXPLOITATION (Priority 40-80)

| Rung | Priority | Purpose |
|------|----------|---------|
| `frontier_checkpoint` | 4-6 | Replay best frontier progress |
| `three_try_sequence` | 5-40 | Try ranked sequences before exploration |
| `discovery_exploitation` | 10-42 | Exploit recent discoveries |
| `embedding_suggestion` | 20-44 | Cross-game neural similarity |
| `multi_stage_matching` | 42-46 | Cascading sequence matching |
| `replay_learning` | 43-48 | Learn during sequence replay |
| `primitive_suggester` | 35-50 | Seed primitive to action mapping |
| `network_wisdom` | 30-47 | Historical action traces from network |
| `abstraction_templates` | 45-48 | Pattern templates from wins |
| `few_shot_invariants` | 46-49 | Relational bias from few examples |
| `subgoal_planning` | 38-50 | Decompose into subgoals |
| `visual_analyzer` | 36-51 | Priority targets for clicks |
| `network_object_inventory` | 37-52 | Query network about objects |
| `near_miss_analyzer` | 48-53 | Learn from high-score failures |
| `completion_prediction` | 39-54 | Estimate steps to completion |
| `frontier_topology` | 25-68 | Network-level topology aggregation |
| `map_intel_collision` | 24-70 | Obstacle avoidance |
| `grid_exploration` | 47-74 | Systematic 8x8 grid walking |

### Category: FALLBACK (Priority 99)

| Rung | Priority | Purpose |
|------|----------|---------|
| `smart_action_selection` | 99 | Weighted random fallback |

---

## Integration Points

### 1. Engine Registry

Rungs access engines via a unified registry:

```python
class DecisionRung(ABC):
    @property
    def engines(self) -> "EngineRegistry":
        """Access modular engines via registry."""
        # Provides: self_model, i_thread, sensation_engine,
        # viral_package_engine, scientific_method_engine, etc.
```

### 2. Database Integration

All knowledge flows through SQLite:

| Table | Purpose |
|-------|---------|
| `action_traces` | Every action taken with outcome |
| `winning_sequences` | Per-level winning sequences |
| `winning_sequences_full_game` | Complete game wins |
| `frontier_checkpoints` | Best partial progress on frontier |
| `game_lessons_learned` | Extracted lessons per game |
| `agent_cognitive_stages` | Stage progression tracking |
| `viral_packages` | Horizontal knowledge transfer |
| `pariah_patterns` | Failed patterns to avoid |

### 3. Context Flow

Context is built incrementally and passed through:

```
ContextBuilder.build_context()
    │
    ├── Static: game_type, level, agent_id, agent_role
    │
    ├── Dynamic: action_count, budget_used_percent, frame_hash
    │
    ├── Network: prior_lessons, active_sequence, frontier_mode
    │
    └── Cognitive: cognitive_stage, cull_distance, stream_weights
```

### 4. Learning Feedback Loop

```
Action → Outcome → Learning → Knowledge → Decision
   │                            │
   │                            ▼
   │                     ┌──────────────┐
   │                     │ Database     │
   │                     └──────────────┘
   │                            │
   └────────────────────────────┘
```

---

## Design Principles

1. **Modularity**: Each rung is independent and can be added/removed/reordered
2. **Lazy Loading**: Engines loaded on-demand to minimize startup overhead
3. **Provenance Tracking**: All knowledge tracks its epistemological source
4. **Role-Aware**: Decisions consider agent role (Pioneer, Optimizer, Generalist, Exploiter)
5. **Stage-Aware**: Cognitive capabilities gate available strategies
6. **Network-Centric**: Knowledge flows bidirectionally with the network database

---

**END OF DOCUMENT**

*For implementation details, see the source files:*
- [decision_rung_system.py](../decision_rung_system.py)
- [engines/cognition/cognitive_stages.py](../engines/cognition/cognitive_stages.py)
- [engines/self_model/cognitive_core.py](../engines/self_model/cognitive_core.py)
- [game_loop.py](../game_loop.py)
- [outcome_processor.py](../outcome_processor.py)
- [learning_systems.py](../learning_systems.py)
