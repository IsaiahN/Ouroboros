# Decision and Cognitive Architecture

**Version**: 1.4
**Date**: 2026-02-03
**Purpose**: Complete documentation of how the Decision Rung System, Cognitive Stage System, CognitiveCore facade, and Evolution-level engines work together from game start to post-game learning.

**Recent Changes (v1.4)**:
- **Evolution Runner Integration**: Documented 10 evolution-level engines now integrated into evolution_runner.py
- Added new section: Evolution-Level Engine Orchestration
- Updated System Overview diagram to show evolution layer
- Added: NetworkIntelligenceEngine, HorizontalTransferEngine, MetaLearningCurriculum, AgentLifecycleManager, CollectiveReasoningEngine, ConceptDiscoveryEngine, UniversalPatternEngine, GamesAsTeachersEngine

**Previous Changes (v1.3)**:
- **Integration Complete**: Full event detection pipeline wired through OutcomeProcessor → ContextBuilder → DecisionRungSystem
- Added `notify_action_complete()` hook for rung learning callbacks (enables SpatialRelationshipRung)
- OutcomeProcessor now detects events via EventDetector when `frame_delta_count > 10`
- ContextBuilder tracks `recent_events` and `frame_delta_count` for rung consumption
- DecisionContext.to_dict() now includes `recent_events` and `frame_delta_count`

**Previous Changes (v1.2)**:
- Added three new world model rungs: `frame_interpretation`, `event_understanding`, `spatial_relationship`
- Added new tables: `detected_events`, `causal_links`, `process_classifications`, `spatial_effects`, `goal_configurations`
- Updated rung count to 52
- Added ObjectTracker and EventDetector modules in engines/perception/
- Added SpatialEffectLearner and MultiObjectGoalTracker in engines/perception/spatial_learning.py

**Previous Changes (v1.1)**:
- Added `state_matching` rung (Symbolic Reasoning Phase 4)
- Added new tables: `property_transformations`, `goal_requirements`, `player_state_history`
- CODS/Oracle fully deprecated - replaced by `primitive_suggester` rung
- Added section: Dynamic Priority Modulation (comprehension-based runtime modulation)

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Component Architecture](#component-architecture)
3. [Evolution-Level Engine Orchestration](#evolution-level-engine-orchestration)
4. [The Decision Rung System](#the-decision-rung-system)
5. [The Cognitive Stage System](#the-cognitive-stage-system)
6. [The CognitiveCore Facade](#the-cognitivecore-facade)
7. [Complete Game Flow](#complete-game-flow)
8. [Rung Reference](#rung-reference)
9. [Integration Points](#integration-points)

---

## System Overview

The BitterTruth-AI system uses a modular, layered architecture to make action decisions. At its core are three complementary systems:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       EVOLUTION ORCHESTRATION                           │
│                                                                         │
│   EvolutionRunner  ──►  (manages generations, population, learning)    │
│        │                                                                │
│        ├── EvolutionaryEngine (genetic evolution, crossover, mutation) │
│        ├── NetworkIntelligenceEngine (ecosystem health snapshots)      │
│        ├── HorizontalTransferEngine (viral knowledge spread)           │
│        ├── MetaLearningCurriculum (4-stage game selection)             │
│        ├── AgentLifecycleManager (birth/retirement/deletion)           │
│        ├── CollectiveReasoningEngine (multi-agent consensus)           │
│        ├── ConceptDiscoveryEngine (cross-game concept emergence)       │
│        ├── UniversalPatternEngine (pattern transfer)                   │
│        └── GamesAsTeachersEngine (lesson extraction from wins)         │
│                                                                         │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │ spawns agents for
                                   ▼
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

**Current Rung Count**: 52 rungs across 6 categories

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

## Evolution-Level Engine Orchestration

The `EvolutionRunner` orchestrates 10 specialized engines that operate at the **population/generation level** rather than the per-action level. These engines manage cross-agent learning, network health, and evolutionary dynamics.

### Engine Integration Summary

| Engine | Frequency | Purpose |
|--------|-----------|---------|
| `EvolutionaryEngine` | Every generation | Genetic evolution: crossover, mutation, selection |
| `ViralPackageEngine` | On wins | Create viral packages from winning sequences |
| `NetworkIntelligenceEngine` | Every 5 generations | Ecosystem health snapshots, network metrics |
| `HorizontalTransferEngine` | Every generation | Spread knowledge virally between agents |
| `MetaLearningCurriculum` | Per agent-game | 4-stage curriculum: specialization → generalization |
| `AgentLifecycleManager` | Every 50 generations | Retire/delete ancient inactive agents |
| `CollectiveReasoningEngine` | For stuck games | Multi-agent ensemble reasoning |
| `ConceptDiscoveryEngine` | Every 10 generations | Detect cross-game concept emergence |
| `UniversalPatternEngine` | Passive | Cross-game pattern matching |
| `GamesAsTeachersEngine` | On wins | Extract lessons from winning games |

### Engine Execution Timeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    GENERATION N LIFECYCLE                               │
│                                                                         │
│  PHASE 1: PRE-GAME                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  MetaLearningCurriculum.select_games_for_agent()                │   │
│  │    └── 4-stage curriculum: specialization → near_transfer       │   │
│  │                           → diversification → generalization    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                │                                        │
│                                ▼                                        │
│  PHASE 2: GAMEPLAY (per agent-game)                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  CoreGameplay.play_single_game()                                │   │
│  │    └── (see Complete Game Flow section)                         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                │                                        │
│                                ▼                                        │
│  PHASE 3: POST-GAME LEARNING                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  IF stuck_on_game:                                              │   │
│  │    CollectiveReasoningEngine.start_collective_session()         │   │
│  │      └── Multi-agent voting on what to try                      │   │
│  │                                                                  │   │
│  │  IF is_win:                                                     │   │
│  │    ViralPackageEngine.create_viral_package_from_sequence()      │   │
│  │    GamesAsTeachersEngine.extract_lesson()                       │   │
│  │      └── Extract generalizable lesson from win                  │   │
│  │                                                                  │   │
│  │  MetaLearningCurriculum.update_stage_progress()                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                │                                        │
│                                ▼                                        │
│  PHASE 4: EVOLUTION                                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  EvolutionaryEngine.evolve_population()                         │   │
│  │    ├── Fitness evaluation                                       │   │
│  │    ├── Selection (keep top performers)                          │   │
│  │    ├── Crossover (breed new agents)                             │   │
│  │    └── Mutation (random variation)                              │   │
│  │                                                                  │   │
│  │  HorizontalTransferEngine.execute_generation_transfers()        │   │
│  │    └── Spread viral packages to other agents                    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                │                                        │
│                                ▼                                        │
│  PHASE 5: PERIODIC MAINTENANCE                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  IF generation % 5 == 0:                                        │   │
│  │    NetworkIntelligenceEngine.capture_ecosystem_snapshot()       │   │
│  │      └── Record network health, diversity, knowledge metrics    │   │
│  │                                                                  │   │
│  │  IF generation % 10 == 0:                                       │   │
│  │    ConceptDiscoveryEngine.check_concept_emergence()             │   │
│  │      └── Detect patterns appearing across multiple games        │   │
│  │                                                                  │   │
│  │  IF generation % 50 == 0:                                       │   │
│  │    AgentLifecycleManager.cleanup_ancient_inactive_agents()      │   │
│  │      └── Delete zero-score agents >50 generations old           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Engine Details

#### 1. MetaLearningCurriculum

Implements a 4-stage developmental curriculum:

| Stage | Name | Focus | Exit Criteria |
|-------|------|-------|---------------|
| 1 | Specialization | Master one game type | Win rate ≥ 30% |
| 2 | Near Transfer | Similar games | Transfer rate ≥ 20% |
| 3 | Diversification | Variety of games | Cross-domain win |
| 4 | Generalization | Any game | Maintained performance |

#### 2. NetworkIntelligenceEngine

Tracks ecosystem health via `ecosystem_health_snapshots` table:
- Knowledge metrics (sequences, patterns, rules)
- Information flow (creation rate, validation rate)
- Resilience (critical sequences, redundancy)
- Population metrics (diversity, turnover)

#### 3. CollectiveReasoningEngine

Activates when games are stuck (many failures, no progress):
- Recruits agents who've played the game
- Runs voting or debate reasoning mode
- Produces consensus recommendations

#### 4. ConceptDiscoveryEngine

Detects abstract concepts emerging across games:
- Monitors for patterns proven in multiple games
- Links to primitive unlock system (CODS)
- Creates sharable concept definitions

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
    temporal_spread_generations: float = 0.0  # Generation spread of observations (hardware-agnostic)
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

Nine built-in orderings optimized for different scenarios:

1. **efficiency** (15 rungs) - Fast, production default
2. **llm_optimal** (44 rungs) - Understanding-first, all features
3. **human_brain** (18 rungs) - Parallel attention + fear interrupt
4. **comprehensive** (46 rungs) - Full coverage, organized by category
5. **minimal** (6 rungs) - Fastest possible
6. **frontier_exploration** (17 rungs) - Heavy exploration for unbeaten games
7. **phased_orientation** (11 rungs) - Phase-specific orientation
8. **phased_hypothesis** (11 rungs) - Phase-specific hypothesis testing
9. **phased_exploitation** (13 rungs) - Phase-specific exploitation

### Dynamic Priority Modulation (Comprehension-Based)

Beyond static orderings, rung priorities are **dynamically modulated** at runtime based on agent comprehension confidence. This is implemented via `TemporalIntegrator.get_rung_modulation()`.

**How It Works**:

1. **Track Predictions**: Agent predicts outcome before each action
2. **Measure Surprise**: Compare prediction to actual outcome
3. **Update Confidence**: Low surprise → confidence UP, high surprise → confidence DOWN
4. **Modulate Categories**: Confidence level drives category priority multipliers

**Category Mapping**:

| Rung Category | Modulation Group | Effect |
|---------------|------------------|--------|
| `hypothesis` | exploration | Boosted when confused, suppressed when confident |
| `orientation` | exploration | Boosted when confused, suppressed when confident |
| `exploitation` | exploitation | Boosted when confident, suppressed when confused |
| `filter` | safety | Boosted at extremes (very high/low confidence) |
| `emergency` | safety | Always high priority |
| `fallback` | neutral | Not modulated |

**Modulation by Confidence Level**:

| Confidence | Exploration Mult | Exploitation Mult | Interpretation |
|------------|------------------|-------------------|----------------|
| 0.0 (lost) | 1.30 (boost) | 0.50 (suppress) | "I don't understand - explore more" |
| 0.5 (partial) | 0.90 | 0.90 | Balanced |
| 1.0 (understands) | 0.50 (suppress) | 1.30 (boost) | "I understand - exploit knowledge" |

**Key Insight**: This inverts the naive approach. When struggling, the system boosts **exploration** (need to find what works), not exploitation. When succeeding, it boosts **exploitation** (keep doing what works).

**Implementation**:
- `DecisionRungSystem._get_category_modulation()` - Queries temporal integrator
- `DecisionRungSystem._get_modulated_priority()` - Applies multiplier to rung priority
- Priority adjustment: `modulated_priority = base_priority / multiplier`
- Higher multiplier → lower priority number → fires earlier in ladder

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
│  │    ├── IF frame_delta_count > 10:                           │   │
│  │    │     └── _detect_events() via EventDetector             │   │
│  │    │         ├── Track objects between frames               │   │
│  │    │         ├── Detect MOVEMENT, COLLISION, FUSION events  │   │
│  │    │         └── Classify process (PHYSICS, ANIMATION, etc) │   │
│  │    ├── Record action_trace to database                      │   │
│  │    └─► Return ActionOutcome (with detected_events)          │   │
│  └────────────────────────────────┬────────────────────────────┘   │
│                                   │                                  │
│                                   ▼                                  │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  STEP 4.5: Notify Rungs (Action Complete Hooks)              │   │
│  │                                                              │   │
│  │  DecisionRungSystem.notify_action_complete(...)              │   │
│  │    └── FOR each rung with on_action_complete:               │   │
│  │          └── rung.on_action_complete(action, frames, ctx)   │   │
│  │              Example: SpatialRelationshipRung learns         │   │
│  │              click effect patterns from frame changes        │   │
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

> **Note**: Priorities shown are `default_priority` values. Rungs may share priorities; in LADDER strategy, rungs with equal priority are evaluated in registration order. Categories are logical groupings but do NOT constrain priority ranges - a rung's category describes its cognitive function, not its execution order.

### Category: EMERGENCY (Priority 1-3)

| Rung | Priority | Purpose |
|------|----------|---------|
| `infinite_loop_breaker` | 1 | Break stuck loops after 15+ repeated actions |
| `coordinate_oscillation` | 3 | Detect bouncing between coordinates |

### Category: ORIENTATION (Priority 3-47)

| Rung | Priority | Purpose |
|------|----------|---------|
| `self_trust_boost` | 3 | Manage wA (self-trust) on frontier entry/exit |
| `frame_interpretation` | 4 | Interpret dramatic frame changes, set context flags |
| `imagination_budget` | 4 | Allocate compute based on novelty |
| `survey` | 5 | What's salient in this frame? |
| `breakthrough_budget` | 6 | Dynamic action allocation for breakthrough potential |
| `regulatory_signal` | 7 | Network homeostasis signals |
| `network_exploration_stats` | 9 | Coverage tracking, coldspot identification |
| `questioning_engine` | 10 | What don't I understand? |
| `frustration_detection` | 13 | Detect stuck agents, trigger network signals |
| `exploration_phase` | 22 | Phase-based exploration forcing |
| `grid_exploration` | 47 | Systematic 8x8 grid walking |

### Category: FILTER (Priority 14-55)

| Rung | Priority | Purpose |
|------|----------|---------|
| `contextual_failure` | 14 | Context-aware failure avoidance (position/direction) |
| `terminal_pattern` | 14 | Recognize approaching terminal states |
| `death_avoidance` | 15 | Avoid actions that led to death |
| `prior_lessons` | 16 | Apply graduated weights from game_lessons_learned |
| `pariah_avoidance` | 17 | Avoid network-marked bad patterns |
| `theory_contradiction` | 17 | Filter actions contradicted by failed theories |
| `three_layer_filter` | 55 | Meta-learning filter preventing waste |

### Category: HYPOTHESIS (Priority 12-34)

| Rung | Priority | Purpose |
|------|----------|---------|
| `scientific_method` | 12 | Theory formation and testing |
| `assumption_formation` | 16 | Form testable assumptions from observations |
| `metacognitive_prediction` | 18 | Make predictions, learn from errors |
| `hypothesis_testing` | 19 | Test untested assumptions to validate/disprove |
| `event_understanding` | 23 | Use causal world model (detected events) to inform decisions |
| `deliberation_system` | 29 | TRM-inspired iterative refinement |
| `two_streams` | 30 | Stream A vs Stream B conflict detection |
| `i_thread` | 31 | Persistent identity, stream weighting |
| `theory_gate` | 32 | Working theory validation |
| `sensation_engine` | 33 | Emotional context for actions |
| `resonance_detector` | 34 | Cross-role pattern discovery |

### Category: EXPLOITATION (Priority 6-48)

| Rung | Priority | Purpose |
|------|----------|---------|
| `frontier_checkpoint` | 6 | Replay best frontier progress |
| `three_try_sequence` | 8 | Try ranked sequences before exploration |
| `discovery_exploitation` | 20 | Exploit recent discoveries |
| `map_intel_collision` | 24 | Obstacle avoidance |
| `embedding_suggestion` | 25 | Cross-game neural similarity |
| `rule_transfer` | 25 | Apply learned rules from other games |
| `state_matching` | 26 | Symbolic reasoning - compare player properties to goal |
| `frontier_topology` | 28 | Network-level topology aggregation |
| `network_wisdom` | 35 | Historical action traces from network |
| `visual_analyzer` | 36 | Priority targets for clicks |
| `network_object_inventory` | 37 | Query network about objects |
| `subgoal_planning` | 38 | Decompose into subgoals |
| `completion_prediction` | 39 | Estimate steps to completion |
| `primitive_suggester` | 40 | Seed primitive to action mapping |
| `multi_stage_matching` | 42 | Cascading sequence matching |
| `replay_learning` | 43 | Learn during sequence replay |
| `spatial_relationship` | 44 | Learn click effect patterns, suggest clicks toward goal |
| `abstraction_templates` | 45 | Pattern templates from wins |
| `few_shot_invariants` | 46 | Relational bias from few examples |
| `near_miss_analyzer` | 48 | Learn from high-score failures |

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

**Gameplay Tables**:
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
| `player_state_history` | Per-action player properties (symbolic reasoning) |
| `property_transformations` | Learned object-property change mappings |
| `goal_requirements` | Learned goal state requirements |

**Evolution-Level Tables**:
| Table | Purpose |
|-------|---------|
| `ecosystem_health_snapshots` | Network intelligence health metrics |
| `horizontal_transfer_events` | Viral knowledge transfer records |
| `curriculum_progress` | MetaLearningCurriculum stage tracking |
| `collective_reasoning_sessions` | Multi-agent reasoning sessions |
| `collective_proposals` | Proposals from collective reasoning |
| `knowledge_redundancy` | Knowledge backup tracking |
| `game_lessons` | Lessons extracted by GamesAsTeachersEngine |
| `detected_events` | **NEW** Events detected between frames (MOVEMENT, COLLISION, etc.) |
| `causal_links` | **NEW** Links between actions and detected events |
| `process_classifications` | **NEW** Process type classifications (PHYSICS_SIMULATION, etc.) |
| `spatial_effects` | **NEW** Learned click effect patterns (relative positions) |
| `goal_configurations` | **NEW** Known winning grid configurations |
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
    ├── Cognitive: cognitive_stage, cull_distance, stream_weights
    │
    └── Event Understanding: recent_events, frame_delta_count
        (populated from ActionOutcome.detected_events via update())
```

### 4. Event Understanding Data Flow

```
OutcomeProcessor.process()
    │
    ├── _detect_events(frame_before, frame_after, action)
    │       ├── EventDetector.detect_events_from_frames()
    │       └── EventDetector.classify_process()
    │
    └── ActionOutcome.detected_events = [event_dicts]
            │
            ▼
ContextBuilder.update(action, outcome)
    │
    ├── _recent_events.extend(outcome.detected_events)
    └── _last_frame_delta_count = outcome.frame_delta_count
            │
            ▼
DecisionRungSystem.decide(frame, context.to_dict())
    │
    ├── FrameInterpretationRung reads context['frame_delta_count']
    ├── EventUnderstandingRung reads context['recent_events']
    └── Sets context flags: likely_physics_game, physics_game_confirmed
            │
            ▼
DecisionRungSystem.notify_action_complete()
    │
    └── SpatialRelationshipRung.on_action_complete()
            └── SpatialEffectLearner.record_click_effect()
```

### 5. Learning Feedback Loop

```
Action → Outcome → Learning → Knowledge → Decision
   │        │                      │
   │        │ detected_events      ▼
   │        │               ┌──────────────┐
   │        └──────────────►│ Database     │
   │                        │  - events    │
   │                        │  - spatial   │
   │                        │  - goals     │
   │                        └──────────────┘
   │                               │
   └───────────────────────────────┘
```

---

## Design Principles

1. **Modularity**: Each rung is independent and can be added/removed/reordered
2. **Lazy Loading**: Engines loaded on-demand to minimize startup overhead
3. **Provenance Tracking**: All knowledge tracks its epistemological source
4. **Role-Aware**: Decisions consider agent role (Pioneer, Optimizer, Generalist, Exploiter)
5. **Stage-Aware**: Cognitive capabilities gate available strategies
6. **Network-Centric**: Knowledge flows bidirectionally with the network database
7. **Two-Level Architecture**: Evolution-level engines manage populations; gameplay engines manage actions

---

**END OF DOCUMENT**

*For implementation details, see the source files:*

*Evolution-level orchestration:*
- [evolution_runner.py](../evolution_runner.py)
- [evolutionary_engine.py](../evolutionary_engine.py)
- [network_intelligence_engine.py](../network_intelligence_engine.py)
- [horizontal_transfer_engine.py](../horizontal_transfer_engine.py)
- [meta_learning_curriculum.py](../meta_learning_curriculum.py)
- [agent_lifecycle_manager.py](../agent_lifecycle_manager.py)
- [collective_reasoning_engine.py](../collective_reasoning_engine.py)
- [concept_discovery_engine.py](../concept_discovery_engine.py)
- [engines/self_model/universal_patterns.py](../engines/self_model/universal_patterns.py)
- [engines/postgame/games_as_teachers.py](../engines/postgame/games_as_teachers.py)

*Gameplay-level decision making:*
- [decision_rung_system.py](../decision_rung_system.py)
- [engines/cognition/cognitive_stages.py](../engines/cognition/cognitive_stages.py)
- [engines/self_model/cognitive_core.py](../engines/self_model/cognitive_core.py)
- [game_loop.py](../game_loop.py)
- [outcome_processor.py](../outcome_processor.py)
- [context_builder.py](../context_builder.py)
- [learning_systems.py](../learning_systems.py)

*Event Understanding modules:*
- [engines/perception/object_tracker.py](../engines/perception/object_tracker.py)
- [engines/perception/event_detector.py](../engines/perception/event_detector.py)
- [engines/perception/spatial_learning.py](../engines/perception/spatial_learning.py)
