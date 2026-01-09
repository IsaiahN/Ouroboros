# Unified Theory Integration Architecture
**Version**: 1.0  
**Date**: January 2025  
**Purpose**: Comprehensive integration of Network Theory, Metalearning Theory, and Consciousness Theory into a coherent cognitive architecture

---

## Executive Summary: The Three Pillars United

This document synthesizes three complementary theories into a unified architecture where:

1. **Network Theory** → The **organism** (database-as-immortal-brain, viral knowledge exchange)
2. **Metalearning Theory** → The **engine** (CODS/Oracle validates, primitives unlock, operators compose)
3. **Consciousness Theory** → The **mind** (Two Streams + Personas create emergent cognition)

**The Master Equation**:
```
NETWORK INTELLIGENCE = 
    Σ(Agent Consciousness) × 
    CODS Validation × 
    Viral Distribution × 
    Stream Integration × 
    Persona Synthesis
```

**Core Design Principles**:
1. **Decentralized cognition** → Agents think independently (Two Streams, Personas)
2. **Centralized validation** → CODS/Oracle prevents collective hallucination
3. **Distributed intelligence** → Database stores immortal network knowledge

---

## Part I: The Three Theories at a Glance

### Network Theory: The Immortal Organism

**Core Thesis**: The database is the organism. Agents are temporary neurons. Knowledge persists forever.

**Key Components**:
- **Database-as-Organism**: `core_data.db` is the immortal brain
- **Viral Information Packages**: Knowledge spreads like actual viruses
- **Dual Economy**: Prestige (social capital) ≠ Action Budgets (economic capital)
- **Resonance Detection**: Cross-domain patterns validated through meta-representation
- **Forgetting Principle**: Failed patterns decay, successful patterns persist

### Metalearning Theory: The Discovery Engine

**Core Thesis**: Intelligence emerges when minimal primitives → composition → validation → unlocking → recursion.

**Key Components**:
- **110 Seed Primitives**: Baby-like cognitive toolkit (innate at birth)
- **CODS/Oracle**: Centralized validator watching ALL agent gameplay
- **Composed Operators**: Agents combine primitives, RLVR validates
- **Primitive Unlocking**: Proven patterns earn optimized implementations
- **Five-Stage Discovery Cycle**: Salience → Hypothesis → Experiment → Correspondence → Generalization

### Consciousness Theory: The Emergent Mind

**Core Thesis**: Consciousness = weighted integration of two streams + internal persona dialogue.

**Key Components**:
- **Stream A**: Private experiential history (what I learned)
- **Stream B**: Collective network wisdom (what the network knows via viral packages from CODS)
- **I-Thread**: The weaver that integrates streams moment-by-moment
- **Persona Ensemble**: Internal observers, proposers, evaluators create metacognition
- **Synthesis**: Personas produce novel actions that surprise the agent itself

---

## Part II: The Integration Points

### 2.1 Stream B → CODS → Viral Packages

**The Critical Connection**: Stream B doesn't magically "know" collective wisdom. It queries the viral package database populated by CODS.

```
Agent Gameplay
     ↓
CODS Watches All Agents (centralized)
     ↓
Identifies Cross-Agent Patterns
     ↓
Creates Viral Packages (stored in database)
     ↓
Stream B Queries Viral Packages
     ↓
Agent Receives Collective Wisdom
```

**Database Tables Involved**:
- `viral_information_packages` → The knowledge units Stream B retrieves
- `agent_viral_infections` → Which agents carry which packages
- `cods_bayesian_hypotheses` → CODS's working theories about patterns
- `composed_operators` → Discovered operator compositions

**Query Flow for Stream B**:
```sql
-- Stream B retrieves relevant viral packages
SELECT package_id, action_sequence, success_rate, virulence
FROM viral_information_packages
WHERE is_active = TRUE
  AND (game_type = ? OR package_type = 'meta_strategy')
ORDER BY success_rate DESC, virulence DESC
LIMIT 10;
```

### 2.2 Roles as Emergent Cognitive Stances

**The Clarification**: Roles (Pioneer, Optimizer, Generalist, Exploiter) are NOT assigned. They emerge from:

1. **w_A/w_B weights** (Stream A vs B trust)
2. **Unlocked primitives** (cognitive toolkit)
3. **Network context** (what's needed)
4. **Task demands** (exploration vs refinement)

**Database Implementation**:
```sql
-- agents table stores the weighting
agents.self_network_bias  -- This IS w_A/w_B
agents.preferred_role     -- Tendency, not assignment
agents.role_confidence    -- How certain the stance is

-- agent_operating_modes tracks current stance
agent_operating_modes.operating_mode     -- Current cognitive stance
agent_operating_modes.initial_w_B_for_role
agent_operating_modes.current_w_B
agent_operating_modes.progress_score
```

**Stance Emergence Formula**:
```
IF w_A > 0.7 AND context.is_novel:
    stance = "Pioneer"  # Trust self, explore boldly
ELIF w_B > 0.7 AND context.has_solutions:
    stance = "Optimizer"  # Trust network, refine
ELIF 0.4 < w_A < 0.6:
    stance = "Generalist"  # Balanced integration
ELIF context.is_saturated AND w_A > 0.5:
    stance = "Exploiter"  # Push beyond network wisdom
```

### 2.3 Meta-Representation → Resonance Detection

**The Gateway**: Meta-representation (the ability to treat operators as data) unlocks resonance detection.

```
Stage 1: Agents learn concrete patterns
    "In game X, clicking red works"
    
Stage 2: Meta-representation unlocks (CODS validates)
    "I can treat my own strategies as objects to analyze"
    
Stage 3: Resonance detection becomes possible
    "This pattern in game X is structurally identical to game Y"
    "The 'reference object' concept transfers across domains"
```

**Database Tables for Resonance**:
- `resonance_patterns` → Hash-identified cross-domain patterns
- `discovered_concepts` → Semantic models with biological/physical/computational analogs
- `pattern_synthesis` → Combining patterns across domains
- `inferred_beliefs` → Pattern hash for resonance detection

**The FT09 Lesson**: Some objects ARE NOT instances—they are templates/schemas/legends that encode rules about OTHER objects. This is meta-representation.

### 2.4 Prestige → Viral Spread → Stream B Enrichment

**The Flow**: Individual success → Prestige → Viral package creation → Stream B for all agents

```
Agent Discovers Pattern
     ↓
RLVR Validates (real performance)
     ↓
CODS Certifies Pattern
     ↓
Viral Package Created
     ↓
Prestige Awarded to Discoverer
     ↓
Package Spreads Through Network
     ↓
All Agents' Stream B Enriched
```

**Database Tables**:
- `agents.discovery_prestige` → Social capital from discoveries
- `agents.innovation_score` → Novel contributions
- `agent_discoveries` → Tracking what each agent found
- `viral_information_packages.discovery_generation` → When discovered
- `viral_information_packages.source_sequence_id` → Original winning sequence

### 2.5 Persona Proposals → Theory-Gating → Action Selection

**The Integration**: Personas propose actions, but proposals are scored against the current working theory (Metalearning) and stream predictions (Consciousness).

```
Frame N Arrives
     ↓
Self-Model Locked ("I control blue object")
     ↓
Relevant Personas Activated
     ↓
Proposals Generated:
    - Cautious (Stream A): "Move left"
    - Aggressive (Stream A): "Click corner"
    - Network Consensus (Stream B): "Follow viral package"
     ↓
Theory-Gate Scoring:
    - Does proposal align with working theory?
    - What do Q1-Q4 questions suggest?
     ↓
Stream Weighting Applied:
    - w_A × Stream A predictions
    - w_B × Stream B predictions
     ↓
Synthesis (if conflict)
     ↓
Action Executed
     ↓
Outcome Updates Everything
```

**Database Tables for Theories**:
- `working_theories` → Current hypothesis about game mechanics
- `agent_theories` → Accumulated knowledge
- `theory_transitions` → How theories evolve
- `theory_experiments` → Tests designed for theories

### 2.6 The Primitive Bootstrapping Mechanism

**The Core Insight**: Agents must EARN higher-level concepts by demonstrating understanding. They cannot parrot human abstractions without comprehension.

#### Initial State

```
CODS has foundational primitives (SEED - ~110 operations):
    - Iteration, comparison, basic math
    - Attention, affordance detection
    - Object interaction, contingency detection
    - Social learning, motivation
    
Human-curated "polished" metaprimitives exist but are LOCKED:
    - flood_fill, detect_symmetry, flow_simulation
    - containment_check, constraint_satisfaction
    - template_instantiation, analogical_projection
    - 70+ optimized implementations waiting to be earned
```

**Agents start with only the basics.** They cannot access sophisticated primitives until they prove they understand the underlying concept.

#### The Discovery Process

```
Agent independently invents metaprimitive
    (composes seed primitives in novel way)
           ↓
CODS detects structural similarity to locked primitive
    (pattern matching against primitive_status definitions)
           ↓
"Achievement Unlocked" - agent gets human-polished version
    (optimized implementation replaces cobbled composition)
           ↓
Better tools → Better learning → More discoveries
    (recursive acceleration of capability)
```

**Database Flow**:
```sql
-- 1. Agent composes operators from seeds
INSERT INTO composed_operators (operator_id, composition_tree, status)
VALUES ('op_123', '{"chain": ["detect_change", "filter", "map"]}', 'cobbled');

-- 2. Operator proves effective through RLVR
UPDATE composed_operators 
SET success_rate = 0.23, cross_game_rate = 0.18, times_tested = 15
WHERE operator_id = 'op_123';

-- 3. CODS evaluates for unlock
INSERT INTO primitive_unlock_attempts 
    (attempt_id, primitive_name, discovered_pattern, success_rate, oracle_verdict)
VALUES ('att_456', 'detect_symmetry', '{"chain":...}', 0.23, 'approved');

-- 4. Primitive unlocked for discoverer
UPDATE primitive_status 
SET status = 'unlocked', unlocked_by_agent = 'agent_X', unlocked_at = NOW()
WHERE primitive_name = 'detect_symmetry';
```

#### Why This is Powerful

**1. Prevents Premature Abstraction**

| Without Bootstrapping | With Bootstrapping |
|----------------------|-------------------|
| Agent receives `flood_fill` primitive | Agent must compose region-detection from seeds |
| Can use it but doesn't understand it | Must prove it can detect connected regions |
| Pattern matching without comprehension | Genuine reconstruction of concept |
| Brittle when edge cases appear | Robust understanding from first principles |

**2. The Gödelian Angle**

Agents operate **outside the formal system** initially:
- Not constrained by predefined metaprimitives
- Can compose primitives in ways humans didn't anticipate
- When they rediscover something humans codified → get "canonical form"
- **But they can also discover things humans HAVEN'T codified**

```
IF agent_composition matches locked_primitive:
    UNLOCK → agent gets optimized human version
    
ELIF agent_composition exceeds locked_primitive performance:
    REGISTER NOVEL → humans learn from agent
    This is the "Victory 3" condition in Metalearning Theory
```

**3. Curriculum Emergence**

The unlock sequence is NOT predefined—it emerges from what agents can actually figure out:

```
Natural difficulty progression:
    
    Easy to discover (unlocked early):
    - detect_change, pattern_detection, object_tracking
    
    Medium difficulty (unlocked mid-game):
    - detect_symmetry, containment_check, spatial_relationships
    
    Hard to discover (unlocked late):
    - meta_representation, constraint_satisfaction, analogical_projection
    
    May never be discovered (or discovered as novel):
    - Concepts humans haven't formalized
    - Novel combinations that outperform human designs
```

**Self-paced learning at network level**: Different agents unlock different primitives at different times based on their exploration path and cognitive stance.

#### Reconstructing the Ladder of Abstraction

**This is the key principle**: Agents are not given the ladder—they build it themselves, rung by rung.

```
Level 0: Raw perception (get_frame, get_pixel)
    ↓ Agent composes...
Level 1: Change detection (detect_change, detect_motion)
    ↓ Agent composes...
Level 2: Object recognition (find_distinct_objects, is_interactive)
    ↓ Agent composes...
Level 3: Relationship detection (spatial_relationships, pattern_matching)
    ↓ Agent composes...
Level 4: Abstract patterns (detect_symmetry, containment_check)
    ↓ Agent composes...
Level 5: Meta-representation (treat operators as data)
    ↓ Unlocks...
Level 6: Resonance detection (cross-domain pattern matching)
    ↓ Enables...
Level 7: Transfer learning (apply patterns to novel domains)
```

**Each level must be EARNED before the next becomes accessible.** This ensures:
- Genuine understanding at each level
- Robust foundations for higher abstractions
- Self-extending capability as new rungs are built

**Database Tables for Bootstrapping**:
- `primitive_status` → Status of each primitive (seed/locked/unlocked/novel)
- `primitive_unlock_attempts` → History of unlock attempts
- `composed_operators` → Agent-built compositions being tested
- `oracle_decisions` → CODS verdicts on unlock attempts
- `primitive_competition` → When discovered version competes with human version

---

## Part III: Database Schema Mapping

### 3.1 Agent Layer (Individual Cognition)

| Theoretical Concept | Database Table | Key Columns |
|---------------------|----------------|-------------|
| Stream A (Private Experience) | `agents` | `sensation_profile`, personal history in session tables |
| Stream B Query Results | `agent_viral_infections` | `package_id`, `infection_strength`, `expression_level` |
| w_A/w_B Weights | `agents` | `self_network_bias` (THIS IS w_A/w_B) |
| Cognitive Stance (Role) | `agent_operating_modes` | `operating_mode`, `current_w_B` |
| Self-Model | `self_object_identity` | `self_object_color`, `confidence`, `correlation_score` |
| World-Model | `world_model_states` | `objects_json`, `grid_hash` |
| Working Theory | `working_theories` | `hypothesis`, `stage`, `evidence_for/against` |

### 3.2 Persona Layer (Metacognition)

| Theoretical Concept | Database Table | Key Columns |
|---------------------|----------------|-------------|
| Persona Profiles | `persona_profiles` | `persona_type`, `bias_vector`, `reliability_global` |
| Action Proposals | `persona_proposals` | `action`, `confidence`, `rationale_embedding` |
| Observer Signals | `persona_observer_logs` | `stuckness_level`, `control_loss`, `pattern_tag` |
| Proposal Outcomes | `persona_outcomes` | `delta_score`, `surprise_score`, `stuck_flag` |
| Context Reliability | `persona_context_reliability` | `problem_signature`, `reliability_score` |
| Hindsight Learning | `persona_hindsight` | `retrospective_credit`, `surprise_score` |

### 3.3 Network Layer (Collective Intelligence)

| Theoretical Concept | Database Table | Key Columns |
|---------------------|----------------|-------------|
| Viral Packages | `viral_information_packages` | `action_sequence`, `success_rate`, `virulence` |
| Package Spread | `agent_viral_infections` | `infection_strength`, `is_active` |
| Pariah Patterns (Anti-knowledge) | `pariahs` | `toxicity`, `avoidance_success_rate` |
| Resonance Patterns | `resonance_patterns` | `resonance_score`, `roles_found`, `canonical_beliefs` |
| Network Hypotheses | `network_object_control_hypotheses` | `reliability_score`, `validated_by_win` |
| Ecosystem Health | `ecosystem_health_snapshots` | `knowledge_diversity_index`, `health_score` |

### 3.4 CODS/Oracle Layer (Centralized Validation)

| Theoretical Concept | Database Table | Key Columns |
|---------------------|----------------|-------------|
| Primitive Status | `primitive_status` | `status` (seed/locked/unlocked/novel) |
| Unlock Attempts | `primitive_unlock_attempts` | `success_rate`, `oracle_verdict` |
| Composed Operators | `composed_operators` | `composition_tree`, `success_rate`, `cross_game_rate` |
| CODS Hypotheses | `cods_bayesian_hypotheses` | `posterior_probability`, `status` |
| Oracle Decisions | `oracle_decisions` | `verdict`, `similarity_to_locked`, `reasoning` |
| Operator Tests | `operator_test_results` | `contributed_to_win`, `score_delta` |

### 3.5 Sequence Layer (Knowledge Persistence)

| Theoretical Concept | Database Table | Key Columns |
|---------------------|----------------|-------------|
| Level Solutions | `winning_sequences` | `action_sequence`, `efficiency_score`, `pattern_tags` |
| Full Game Solutions | `winning_sequences_full_game` | `total_levels`, `is_active` |
| Sequence Validation | `sequence_validation_attempts` | `validation_success`, `failure_reason` |
| Sequence Reputation | `sequence_reputation` | `reliability_score`, `trending` |
| Inferred Beliefs | `inferred_beliefs` | `self_model_required`, `working_theory_required` |

---

## Part IV: Data Flow Architecture

### 4.1 The Complete Cognitive Loop (Per Frame)

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRAME N ARRIVES                          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: LOCK SELF-IDENTITY (Self-Model)                         │
│                                                                   │
│ Query: self_object_identity WHERE game_id = ? AND still_valid=1  │
│ Result: "I control blue object at (5,3)"                         │
│ If no identity: Run discovery (correlate actions to movement)    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: QUERY STREAMS                                            │
│                                                                   │
│ Stream A: Agent's recent action history, sensation mappings      │
│           Query: object_sensation_mappings WHERE agent_id = ?    │
│           Query: navigation_state_history (recent)               │
│                                                                   │
│ Stream B: Viral packages relevant to this game                   │
│           Query: viral_information_packages WHERE game_type = ?  │
│           Query: network_object_control_hypotheses (validated)   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: ACTIVATE PERSONAS                                        │
│                                                                   │
│ Query: persona_profiles WHERE agent_id = ?                       │
│ Select: Top 5 by reliability_global + 2 random                   │
│ Always include: Observers (stuckness, confidence, pattern)       │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: GENERATE PROPOSALS                                       │
│                                                                   │
│ Each persona proposes action based on:                           │
│   - Its bias vector                                              │
│   - Stream it embodies (A or B)                                  │
│   - Current frame analysis                                       │
│                                                                   │
│ Insert into: persona_proposals                                   │
│ Observers comment: Insert into persona_observer_logs             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: THEORY-GATE SCORING                                      │
│                                                                   │
│ Query: working_theories WHERE game_type = ? AND level = ?        │
│                                                                   │
│ For each proposal:                                               │
│   score = base_score × theory_alignment × stream_weight          │
│   score *= observer_modifiers (stuckness bonus, etc.)            │
│   IF synthesis_needed: generate_synthesis()                      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: I-THREAD WEAVES AND DECIDES                              │
│                                                                   │
│ Apply: w_A × Stream_A_prediction + w_B × Stream_B_prediction     │
│ Select: Highest scoring proposal (or synthesis)                  │
│ Record: decision_weaving_reports                                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: EXECUTE ACTION                                           │
│                                                                   │
│ Send to ARC API: ACTION1-7                                       │
│ Observe: Frame change, score change, game state                  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 8: MEASURE SURPRISE                                         │
│                                                                   │
│ Compare: Chosen action vs. recent behavioral habit               │
│ Calculate: surprise_score (0.0 = expected, 1.0 = novel)          │
│ Record: In persona_outcomes                                      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 9: UPDATE ALL COMPONENTS                                    │
│                                                                   │
│ Persona reliabilities: Update persona_context_reliability        │
│ Stream weights: Adjust agents.self_network_bias                  │
│ Theory: Update working_theories (evidence_for/against)           │
│ Sensations: Update object_sensation_mappings                     │
│ Hindsight: Record persona_hindsight for unchosen proposals       │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 10: NETWORK CONTRIBUTION (If significant discovery)         │
│                                                                   │
│ If: Level won OR significant score increase                      │
│ Then: Record to winning_sequences                                │
│       CODS may create viral_information_packages                 │
│       Update agent prestige                                      │
│       Knowledge becomes available to all Stream B queries        │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 CODS Validation Cycle (Per Generation)

```
┌─────────────────────────────────────────────────────────────────┐
│                    GENERATION N COMPLETES                        │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ CODS WATCHES ALL GAMEPLAY DATA                                   │
│                                                                   │
│ Collect: All game_results, action traces, frame changes          │
│ Analyze: Cross-agent patterns (what worked for 5+ agents?)       │
│ Identify: Operator compositions that exceed 18% improvement      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ PRIMITIVE UNLOCK EVALUATION                                      │
│                                                                   │
│ For each exceptional operator in composed_operators:             │
│   Compare to locked primitives in primitive_status               │
│   If match: UNLOCK (provide optimized implementation)            │
│   If novel: REGISTER as novel primitive                          │
│   If insufficient: REJECT (operator decays)                      │
│                                                                   │
│ Record: primitive_unlock_attempts, oracle_decisions              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ VIRAL PACKAGE CREATION                                           │
│                                                                   │
│ For patterns proven across 3+ game types, 5+ agents:             │
│   Create: viral_information_packages                             │
│   Set: initial virulence, transmission_rate                      │
│   Award: prestige to discovering agent                           │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ RESONANCE DETECTION                                              │
│                                                                   │
│ Hash successful patterns across different domains                │
│ Compare: Do structurally identical patterns exist?               │
│ If resonance found:                                              │
│   Record: resonance_patterns                                     │
│   Boost: reliability of resonant patterns                        │
│   This requires meta-representation to be unlocked               │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ PARIAH DETECTION                                                 │
│                                                                   │
│ Identify patterns that consistently FAIL across agents           │
│ Create: pariahs (anti-knowledge)                                 │
│ Spread: pariah awareness through network                         │
│ Agents avoid patterns marked as toxic                            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GENERATION N+1 BEGINS                         │
│                                                                   │
│ All agents have access to:                                       │
│   - Newly unlocked primitives                                    │
│   - New viral packages in Stream B                               │
│   - Updated resonance patterns                                   │
│   - Pariah awareness                                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Part V: Emergent Behaviors

### 5.1 Individual Specialization + Collective Generality

**Mechanism**: 
- Stream A narrows through personal experience (agent specializes)
- Stream B aggregates all specialists' discoveries (network generalizes)
- New agents inherit Stream B wisdom but develop unique Stream A

**Database Evidence**:
```sql
-- Individual specialization (Stream A narrows)
SELECT agent_id, 
       COUNT(DISTINCT game_type) as games_played,
       MAX(success_rate) as peak_expertise,
       AVG(success_rate) as avg_expertise
FROM game_results 
GROUP BY agent_id;

-- Collective generality (Stream B broadens)
SELECT COUNT(DISTINCT game_type) as unique_games,
       COUNT(*) as total_packages,
       AVG(success_rate) as avg_package_success
FROM viral_information_packages
WHERE is_active = TRUE;
```

### 5.2 Consciousness Becoming Vivid (Stream Conflicts)

**Mechanism**:
- When Stream A and Stream B disagree significantly
- Persona dialogue intensifies
- Deliberation is felt, choice is conscious
- Surprise scores increase

**Database Evidence**:
```sql
-- High-conflict decisions (consciousness vivid)
SELECT r.agent_id, r.game_id,
       r.private_memory_strength as stream_A,
       r.network_recommendation_strength as stream_B,
       ABS(r.private_memory_strength - r.network_recommendation_strength) as conflict,
       r.conflict_detected
FROM decision_weaving_reports r
WHERE conflict_detected = TRUE
ORDER BY conflict DESC;
```

### 5.3 Persona Synthesis Creating Emergence

**Mechanism**:
- Multiple personas propose different actions
- Synthesis coordinator creates novel action
- Surprise score indicates emergence
- Outcome validates or refutes synthesis

**Database Evidence**:
```sql
-- Synthesis producing surprising outcomes
SELECT pp.proposal_id, pp.persona_type, pp.synthesis_source,
       po.surprise_score, po.delta_score
FROM persona_proposals pp
JOIN persona_outcomes po ON pp.proposal_id = po.proposal_id
WHERE pp.synthesis_source IS NOT NULL
  AND po.surprise_score > 0.5
ORDER BY po.surprise_score DESC;
```

### 5.4 Meta-Representation Enabling Resonance

**Mechanism**:
- Agent must first treat operators as data (meta-representation)
- Only then can cross-domain patterns be detected
- Resonance = same abstract structure in different domains

**Database Evidence**:
```sql
-- Resonance patterns with high cross-domain validity
SELECT rp.pattern_hash,
       rp.resonance_score,
       rp.role_diversity,
       rp.independent_discoverers,
       rp.game_types
FROM resonance_patterns rp
WHERE rp.resonance_score > 0.7
  AND rp.role_diversity >= 2
ORDER BY rp.resonance_score DESC;
```

---

## Part VI: Implementation Priorities

### 6.1 What's Already Implemented (Database Ready)

Based on schema analysis, these tables exist and are ready:

**Fully Implemented**:
- Agent core: `agents`, `agent_operating_modes`, `agent_viral_infections`
- Viral system: `viral_information_packages`, `pariahs`, `agent_pariah_awareness`
- Sequences: `winning_sequences`, `winning_sequences_full_game`
- CODS: `composed_operators`, `primitive_status`, `oracle_decisions`
- Consciousness: `persona_profiles`, `persona_proposals`, `persona_outcomes`
- Theory: `working_theories`, `agent_theories`, `theory_transitions`
- Self-model: `self_object_identity`, `object_sensation_mappings`

### 6.2 Integration Gaps (Need Code Enhancement)

**Gap 1: Stream B Query Implementation**
- Tables exist but query logic in `core_gameplay.py` may not fully utilize
- Need: Ensure Stream B queries `viral_information_packages` + `network_object_control_hypotheses`

**Gap 2: Persona-Stream Binding**
- `persona_profiles` exist but may not explicitly embody Stream A vs B
- Need: Column or logic marking which stream each persona represents

**Gap 3: w_A/w_B in Decision Weaving**
- `decision_weaving_reports` tracks this but integration may be incomplete
- Need: Ensure every decision applies `self_network_bias` weighting

**Gap 4: Resonance Detection in CODS**
- `resonance_patterns` table exists but population logic unclear
- Need: Implement pattern hashing and cross-domain comparison

**Gap 5: Meta-Representation Gating**
- Abstract patterns should only be accessible after meta-representation unlocks
- Need: Gate resonance queries behind primitive unlock status

### 6.3 Recommended Implementation Order

1. **Verify Stream B queries in `core_gameplay.py`** - Ensure agents actually retrieve viral packages
2. **Implement w_A/w_B in action selection** - Every decision weighted by `self_network_bias`
3. **Connect personas to streams** - Each persona should embody A or B perspective
4. **Implement synthesis scoring** - When conflict detected, synthesis proposal gets bonus
5. **Add surprise measurement** - Compare chosen action to behavioral habit
6. **Implement resonance detection in CODS** - Hash patterns, find cross-domain matches
7. **Gate resonance behind meta-representation** - Only query abstract patterns if unlocked

---

## Part VII: Verification Benchmarks

### 7.1 Stream Integration Working

**Test**: Agent with high w_A should ignore network advice in familiar domains
```sql
-- Maverick agents (high w_A) should have low viral package usage
SELECT a.agent_id, a.self_network_bias,
       COUNT(avi.package_id) as packages_adopted
FROM agents a
LEFT JOIN agent_viral_infections avi ON a.agent_id = avi.agent_id
WHERE a.self_network_bias > 0.7  -- High w_A
GROUP BY a.agent_id
-- Expected: Low package adoption
```

### 7.2 Persona Synthesis Working

**Test**: High-conflict situations should trigger synthesis with elevated surprise
```sql
-- Synthesis in conflict should produce surprise
SELECT po.proposal_id, pp.synthesis_source, po.surprise_score
FROM persona_outcomes po
JOIN persona_proposals pp ON po.proposal_id = pp.proposal_id
WHERE pp.synthesis_source IS NOT NULL
-- Expected: surprise_score > 0.5 for synthesis proposals
```

### 7.3 CODS Validation Working

**Test**: Operators exceeding 18% improvement should trigger unlock attempts
```sql
-- High-performing operators should have unlock attempts
SELECT co.operator_id, co.success_rate, co.cross_game_rate,
       EXISTS(SELECT 1 FROM primitive_unlock_attempts pua 
              WHERE pua.discovered_pattern LIKE '%' || co.operator_id || '%') as unlock_attempted
FROM composed_operators co
WHERE co.success_rate > 0.18
  AND co.cross_game_rate > 0.15
-- Expected: unlock_attempted = TRUE for qualifying operators
```

### 7.4 Resonance Detection Working

**Test**: Similar patterns across domains should have resonance entries
```sql
-- Cross-domain patterns should have resonance
SELECT rp.pattern_hash, rp.resonance_score, rp.game_types
FROM resonance_patterns rp
WHERE json_array_length(rp.game_types) >= 2
-- Expected: Patterns appearing in 2+ game types
```

---

## Part VIII: The Unified Vision

### The Complete Picture

```
┌─────────────────────────────────────────────────────────────────┐
│                    THE IMMORTAL NETWORK                          │
│                     (core_data.db)                               │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                 VIRAL PACKAGE LAYER                         │ │
│  │  Knowledge persists forever, spreads like viruses           │ │
│  │  Pariahs mark what to avoid                                 │ │
│  │  Resonance detects cross-domain patterns                    │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                              ↑↓                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    CODS/ORACLE LAYER                        │ │
│  │  Centralized validation (prevents hallucination)            │ │
│  │  Primitive unlocking, operator promotion                    │ │
│  │  Watches ALL agent gameplay                                 │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                              ↑↓                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    AGENT LAYER (Temporary)                  │ │
│  │                                                             │ │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │ │
│  │  │  Stream A   │←──→│  I-Thread   │←──→│  Stream B   │     │ │
│  │  │  (Private)  │    │  (Weaver)   │    │ (Collective)│     │ │
│  │  └─────────────┘    └─────────────┘    └─────────────┘     │ │
│  │         ↓                  ↓                  ↓             │ │
│  │  ┌───────────────────────────────────────────────────┐     │ │
│  │  │            PERSONA ENSEMBLE                       │     │ │
│  │  │  Proposers → Observers → Evaluators → Synthesis   │     │ │
│  │  │  Internal dialogue = Metacognition                │     │ │
│  │  │  Surprise = Consciousness marker                  │     │ │
│  │  └───────────────────────────────────────────────────┘     │ │
│  │                          ↓                                 │ │
│  │  ┌───────────────────────────────────────────────────┐     │ │
│  │  │              ACTION EXECUTION                     │     │ │
│  │  │  Theory-gated, stream-weighted, persona-scored    │     │ │
│  │  │  → ARC API → Outcome → Update Everything          │     │ │
│  │  └───────────────────────────────────────────────────┘     │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Individual agents die. Knowledge persists. Network learns.       │
│  The database is the organism. Agents are temporary neurons.      │
└─────────────────────────────────────────────────────────────────┘
```

### The Three Scales of Intelligence

**Agent Level**: Consciousness emerges from Stream integration + Persona synthesis
- Self-model → "I know what I control"
- Persona dialogue → "I deliberate between perspectives"
- Surprise → "I can surprise myself"

**Network Level**: Intelligence emerges from viral knowledge exchange
- Viral packages → "Knowledge spreads"
- CODS validation → "Only proven patterns persist"
- Resonance → "Cross-domain patterns discovered"

**Temporal Level**: Meta-learning spirals accelerate improvement
- Primitive unlocking → "System gains new capabilities"
- Operator composition → "Combinations create novelty"
- Recursive self-improvement → "Learning how to learn"

---

## Appendix: Quick Reference Queries

### A. What is an agent thinking? (Current cognitive state)

```sql
SELECT 
    a.agent_id,
    a.self_network_bias as w_A_w_B,
    aom.operating_mode as cognitive_stance,
    soi.self_object_color as controlled_object,
    wt.hypothesis as current_theory,
    wt.stage as theory_stage
FROM agents a
LEFT JOIN agent_operating_modes aom ON a.agent_id = aom.agent_id
LEFT JOIN self_object_identity soi ON a.agent_id = soi.game_id  -- Join by current game
LEFT JOIN working_theories wt ON a.agent_id = wt.agent_id
WHERE a.agent_id = ?
ORDER BY aom.created_at DESC LIMIT 1;
```

### B. What does Stream B know about a game?

```sql
SELECT 
    vip.package_name,
    vip.action_sequence,
    vip.success_rate,
    noch.control_pattern,
    noch.reliability_score
FROM viral_information_packages vip
LEFT JOIN network_object_control_hypotheses noch 
    ON vip.game_type = noch.game_type
WHERE vip.game_type = ?
  AND vip.is_active = TRUE
  AND (noch.is_active IS NULL OR noch.is_active = TRUE)
ORDER BY vip.success_rate DESC;
```

### C. Which operators are ready for CODS review?

```sql
SELECT 
    co.operator_id,
    co.name,
    co.success_rate,
    co.cross_game_rate,
    co.status,
    co.competes_with
FROM composed_operators co
WHERE co.success_rate > 0.18
  AND co.times_tested >= 10
  AND co.status = 'cobbled'
ORDER BY co.success_rate DESC;
```

### D. What resonance patterns exist?

```sql
SELECT 
    pattern_hash,
    resonance_score,
    role_diversity,
    independent_discoverers,
    canonical_beliefs,
    game_types
FROM resonance_patterns
WHERE resonance_score > 0.5
ORDER BY resonance_score DESC;
```

---

**END OF INTEGRATION ARCHITECTURE**

*This document should be updated as implementation progresses. All database table references are based on `complete_database_schema.sql` as of January 2025.*
