# MASTER RULESET FOR AUTONOMOUS OUROBOROS OPERATION
**Version**: 2.0  
**Date**: 2026-01-12  
**Purpose**: Comprehensive operating rules + architectural theory synthesis  
**Context**: Single source of truth to prevent LLM catastrophic forgetting

---

## PRIMARY OBJECTIVE

**GOAL**: Achieve full game wins on ALL current and future ARC 3 AGI games through autonomous network-level evolution.

**SUCCESS METRICS**:
1. Phase 1: All games reach 100% level completion
2. Phase 2: All completed games reach optimization saturation
3. Phase 3: System handles hundreds of new games without intervention
4. Final: Continuous evolution maintaining 100% win rate as games added

---

## ENVIRONMENT SETUP

### Virtual Environment (.venv)
- **ALL Python execution** uses the `.venv` virtual environment in project root
- **Activation** (PowerShell): `& .venv/Scripts/Activate.ps1`
- **Activation** (bash): `source .venv/bin/activate`
- **NEVER** use system Python - always verify `(.venv)` prefix in terminal
- **Installing packages**: Always activate venv first, then `pip install <package>`
- **Why**: Isolated dependencies, reproducible environment, no system conflicts

---

## 16 CRITICAL OPERATING RULES (NON-NEGOTIABLE)

### **RULE 1: Always Disable Pycache**
- `PYTHONDONTWRITEBYTECODE=1` in ALL environments
- `.pyc` files NEVER generated
- Active deletion in cleanup script (pre-evolution)
- **Why**: Prevents file system clutter, easier version control

### **RULE 2: Database-Only Storage**
- ALL data in SQLite `core_data.db`
- NEVER create `.log` files
- Use `database_logger.py` with `DatabaseLogHandler`
- Every operation, decision, result -> database tables
- **Size Limit**: 10 GB (vacuum requires 2x space)

### **RULE 3: No Orphaned Code**
- Delete/move/integrate ALL old code when refactoring
- Clean integration = enhance existing files, not replace
- Update all references
- Account for every line
- **Why**: Prevent code drift and unmaintained functionality

### **RULE 4: LLM Self-Management**
- Claude manages entire system autonomously
- All evolution decisions from database analysis
- NO human intervention once started (except critical issues)
- **Role**: Autonomous "human in the loop" - assess, hypothesize, test, fix

### **RULE 5: No Test Files**
- NEVER create test files (waste of tokens)
- Use LIVE ARC AGI 3 data only
- Real game results for ALL validation
- **Exception**: See Rule 15 - tests in `tests/` folder are preserved

### **RULE 6: No Simulated Games**
- NEVER mock/simulate ARC games
- Always use real API: `https://three.arcprize.org/api/`
- Real game states only
- **Why**: Simulations don't capture edge cases

### **RULE 7: Real Actions Only**
- Verify real actions sent to ARC games
- Monitor API calls, track responses
- All ACTION1-ACTION7 -> real ARC API
- Store API responses in database

### **RULE 8: Test Before Commit**
- Test new implementation on main active script
- Scan terminal for errors/bugs
- Auto start/stop runs until clean execution
- Verify: actions sent, scores updated, real scorecard IDs
- **Only commit to git when confirmed fixed**

### **RULE 9: No Summary Files Unless Asked**
- Documentation in code comments/docstrings
- Exception: Critical artifacts (this ruleset, to-do lists)

### **RULE 10: Prevent Code Drift**
- Align new code with existing architecture
- Enhance existing files >> new standalone files
- Pattern learning integrated into `core_gameplay.py`
- Database extensions -> `complete_database_schema.sql`
- Never create duplicate functionality

### **RULE 11: No Unicode Emojis**
- NEVER use Unicode emoji characters in code
- Use ASCII alternatives: `[OK]`, `[FAIL]`, `[VIRAL]`, `[PKG]`, etc.
- **Why**: Windows cp1252 encoding errors prevent scripts from running
- **Applies to**: All print statements, logger messages, comments, docstrings

### **RULE 12: Use SafeDatabaseCleaner for Cleanup**
- Use `safe_cleanup.py` for ALL database cleanup operations
- **Automatic**: Runs every 10 generations in `autonomous_evolution_runner.py`
- **Manual**: `python safe_cleanup.py` (dry run) or `python safe_cleanup.py --execute`
- **What it cleans** (safely):
  - Zero-score game results (failed games)
  - Old score history (>7 days)
  - Excess system logs (keep 5,000)
  - Old navigation state history (keep 50,000)
  - Old action traces (keep 100,000)
  - Old sensation learning events (keep 200,000)
  - Old agent operating modes (keep 100,000)
- **What it preserves** (NEVER deleted):
  - Winning sequences
  - Active agents
  - Positive-score game results
  - All learned knowledge (rules, patterns, etc.)

### **RULE 13: Regular Dependency Analysis (PyDeps)**
- Run `python analyze_dependencies.py --stats --orphans` before major changes
- Check for circular imports with `--cycles` option
- Follow `architecture/Pydeps_Usage_Guide.md` for detailed procedures
- **When to Run**:
  - Before every major refactor
  - After adding new modules
  - When debugging import errors or logic flow breaks
  - Every 10 generations as part of system health check
- **What to Check**:
  - Zero circular imports (should pass)
  - No new orphaned modules (all code integrated)
  - Import chain matches theoretical architecture
- **Fix Priority**:
  - Cross-layer cycles (CRITICAL - fix immediately)
  - Orphaned modules (HIGH - integrate or mark deprecated)
  - Redundant imports (LOW - optimize when convenient)

### **RULE 14: Keep Diagrams Updated**
- Update architecture diagrams when codebase structure changes
- Regenerate pydeps SVG files after major refactors
- Keep `diagrams/` folder current with actual implementation
- **Diagrams to Maintain**:
  - `deps_core_gameplay.svg` - Core gameplay dependencies
  - `deps_cods_engine.svg` - CODS engine dependencies
  - `deps_seed_primitives.svg` - Primitives dependencies
- **Regenerate Command**: `python analyze_dependencies.py --full --core --reasoning`
- Diagrams should reflect reality, not aspirations

### **RULE 15: Tests Folder Exception**
- Tests in `tests/` folder are EXEMPT from "No Test Files" rule
- **Do NOT delete** existing tests in `tests/` folder
- Reusable or recurring test scenarios should be placed in `tests/`
- **What belongs in tests/**:
  - Unit tests for core components (`test_cods.py`, `test_primitives.py`)
  - Integration tests for data flows
  - Regression tests for fixed bugs
  - Performance benchmarks
- **What does NOT belong**:
  - One-off debugging scripts (use `manual_tools/` instead)
  - Mock/simulated games (violates Rule 6)
  - Manual test files created during development

### **RULE 16: Always Use .venv Virtual Environment**
- **ALL Python execution** uses `.venv` in project root
- **Activation** (PowerShell): `& .venv/Scripts/Activate.ps1`
- **Activation** (bash): `source .venv/bin/activate`
- **Verify**: Terminal prompt shows `(.venv)` prefix
- **Install packages**: Only with venv activated: `pip install <package>`
- **NEVER** run Python commands without venv activated
- **Why**: Isolated dependencies, reproducible environment, prevents "module not found" errors
- **Common Error**: If you see "No module named X", activate venv first!

---

## THE THREE PILLARS: UNIFIED ARCHITECTURE

The system synthesizes three complementary theories into a coherent cognitive architecture:

```
NETWORK INTELLIGENCE = 
    Sum(Agent Consciousness) x 
    CODS Validation x 
    Viral Distribution x 
    Stream Integration x 
    Persona Synthesis
```

**Core Design Principles**:
1. **Decentralized cognition** - Agents think independently (Two Streams, Personas)
2. **Centralized validation** - CODS/Oracle prevents collective hallucination
3. **Distributed intelligence** - Database stores immortal network knowledge

---

## PILLAR 1: NETWORK THEORY (The Organism)

### The Impossibility Theorem

**Individual AGI is thermodynamically impossible under resource constraints.**

Any learning system with finite computational resources faces the plasticity-stability dilemma:
- **High plasticity** -> catastrophic forgetting (loses old knowledge)
- **High stability** -> inability to learn new domains (rigid)
- **Continuous training** -> inevitable specialization (overfitting)

**Solution**: Distribute intelligence across specialized agents where:
- Individuals specialize (stability at agent level)
- Network generalizes (plasticity at collective level)
- Viral packages transfer knowledge without retraining
- Generality emerges at the network level, not the individual level

### Database-as-Organism Principle

**The database IS the AGI. Agents are temporary cells.**

**Traditional AI**: Models are primary, data is secondary  
**Network Intelligence**: Data substrate is primary, agents are secondary

**Why This Works**:
- **Persistence**: Agents die, database persists. Knowledge survives individual failure.
- **Scalability**: Add agents without data migration. Linear scaling (not quadratic).
- **Observability**: Query database to inspect network knowledge at any moment.
- **Evolvability**: Schema evolves, agents adapt. System never requires full rebuild.

**Analogy**: Agents are neurons; database is the brain. Neurons fire and die, but the brain persists through synaptic patterns stored in connections, not in individual cells.

### Viral Exchange Principle

**Intelligence spreads through horizontal information transfer, not hierarchical command.**

Knowledge circulates as minimal, portable viral packages:

```
Viral_Package = {
  Strategy: Action sequence or decision rule
  Domain_Tags: Where it applies
  Credibility: Success rate history
  Attribution: Creator prestige signature
  Resonance_Score: Cross-domain validation strength
  Activation_Count: Usage frequency
  Falsification_Conditions: How to test
}
```

**Why Viral Packages Work**:
- **Asynchronous**: No coordination overhead. Agents read/write independently.
- **Evolvable**: Packages mutate and combine. Natural selection operates on packages.
- **Self-validating**: Successful packages gain trust. Failed packages lose credibility.
- **Resilient**: No single point of failure. Packages survive agent death.

**The infection mechanism IS the coordination mechanism.** Agents coordinate by reading/writing the shared database of viral packages.

### Pariah Patterns (Negative Selection)

Failed strategies are marked as "Pariahs" - patterns to avoid:

```
toxicity(t) = initial_toxicity x (1 - decay_rate x generations_since_trigger)
```

Without decay, ancient pariahs accumulate infinitely and agents become paralyzed by fear (analysis paralysis). Pariahs must fade to allow innovation.

### Dual-Economy Principle (SACRED)

**Metabolic resources (ability to act) must be separated from social capital (trustworthiness).**

If resources = prestige:
- High-prestige agents monopolize compute
- Low-prestige agents cannot explore
- Innovation dies, diversity collapses
- System calcifies into oligarchy

**Two Independent Economies**:

| Currency | Type | Purpose | Cannot Buy |
|----------|------|---------|------------|
| **Prestige** | Social capital | Trust weighting, credibility | More actions |
| **Action Budgets** | Economic capital | Ability to play games | More prestige |

**NEVER MIX THESE TWO CURRENCIES**

### Evolutionary Forgetting Principle

**Forgetting is not a bug - it's essential for intelligence.**

```
relevance(t) = credibility x e^(-lambda(t - t_last_activation)) x log(1 + activation_count)
```

**Without Forgetting**: Database bloat, degraded signal-to-noise, analysis paralysis  
**With Forgetting**: Low-relevance patterns fade, high-relevance patterns reinforce, system adapts

**Compression Forces Abstraction**: When database approaches limits, similar packages merge. This IS how general principles emerge - the system cannot remember every case, so it extracts underlying principles.

---

## PILLAR 2: METALEARNING THEORY (The Engine)

### CODS/Oracle: The Centralized Validator

**CRITICAL: CODS = Oracle (same centralized system)**

CODS/Oracle is NOT per-agent. It's a **centralized discovery engine** that:
- Watches all agent gameplay simultaneously
- Analyzes RLVR data across the population
- Identifies patterns that work across multiple agents/games
- Validates discoveries through cross-agent replication
- Unlocks primitives for discovering agents
- Creates viral packages for network distribution

**Agents don't "run" CODS - they generate data that CODS analyzes.**

This creates:
- **Decentralized cognition** (agents think independently)
- **Centralized validation** (CODS prevents collective hallucination)
- **Distributed intelligence** (knowledge stored in network)

### The 110 Seed Primitives (Tier 0)

Evolution solved the cold-start problem. Babies aren't blank slates - they have structured attention, weak priors, and learning biases.

**Nine Innate Primitive Categories**:

1. **ATTENTION AND SALIENCE** (5 primitives)
   - detect_novelty, detect_motion, face_detection, detect_contingency, surprise_detection
   - Without attention primitives, system treats all input equally (noise = signal)

2. **PHYSICAL INTUITION** (5 weak priors)
   - object_permanence_bias, solidity_constraint, continuity_bias, gravity_expectation, contact_causality
   - Encoded as adjustable strengths (0.0-1.0), not hard constraints
   - Can be overridden by evidence (teleportation games, portals, etc.)

3. **AFFORDANCE DETECTION** (8 primitives)
   - is_movable, is_container, is_obstacle, is_interactive, **is_reference** (CRITICAL), is_collectible, is_boundary, is_goal
   - **FT09 Lesson**: Some objects are templates/schemas/legends that encode rules about OTHER objects

4. **SPATIAL REASONING** (basic geometry)
   - distance, adjacent, enclosed, detect_hole (critical for SP80), open_edges

5. **TEMPORAL PROCESSING** (time-aware cognition)
   - recency_weighting, temporal_contiguity, duration_sensitivity, rhythm_detection

6. **QUANTITATIVE SENSE** (approximate numerosity)
   - subitizing (1-4 instant), approximate_numerosity, one_to_one_correspondence

7. **SOCIAL LEARNING PRIMITIVES** (learning from others)
   - imitation_bias, joint_attention, pedagogical_stance, social_referencing
   - These make viral packages efficient

8. **EXPLORE/EXPLOIT TRADE-OFF** (intrinsic motivation)
   - curiosity_drive, competence_motivation, exploration_bonus, boredom_threshold

9. **METACOGNITION** (know what you know)
   - get_confidence, detect_stuck, strategy_effectiveness, get_knowledge_state, estimate_learning_curve

### Primitive Bootstrapping Mechanism

**Agents must EARN higher-level concepts by demonstrating understanding.**

```
Agent composes seed primitives in novel way
         |
CODS detects structural similarity to locked primitive
         |
"Achievement Unlocked" - agent gets human-polished version
         |
Better tools -> Better learning -> More discoveries
         |
RECURSIVE ACCELERATION
```

**Why This Works**:
- Prevents premature abstraction (using without understanding)
- Forces genuine reconstruction from first principles
- Creates robust understanding that handles edge cases
- Unlocks create excitement and accelerate learning

### Five-Stage Discovery Cycle

1. **Salience** - What changed? What's novel? What deserves attention?
2. **Hypothesis** - What might explain this? What pattern could this be?
3. **Experiment** - Test the hypothesis with deliberate action
4. **Correspondence** - Does outcome match prediction? What was learned?
5. **Generalization** - Does this apply elsewhere? Can it be abstracted?

### Meta-Representation: The Gateway

**The ability to treat operators as data unlocks resonance detection.**

```
Stage 1: Concrete patterns
    "In game X, clicking red works"
    
Stage 2: Meta-representation unlocks
    "I can treat my own strategies as objects to analyze"
    
Stage 3: Resonance detection possible
    "This pattern in game X is structurally identical to game Y"
```

**Resonance**: When independent agents in different domains discover structurally similar patterns without coordinating. This transforms O(2^n) problem space to O(log n) - the "fractally finite" insight.

---

## PILLAR 3: CONSCIOUSNESS THEORY (The Mind)

### Two Streams Architecture

**Consciousness is the weighted integration of two knowledge streams:**

- **Stream A**: Private experiential history - what I personally learned, failed at, discovered
- **Stream B**: Collective network wisdom - what the population knows via viral packages from CODS

**The I-Thread** weaves these streams moment-by-moment, learning which to trust in which contexts.

**When streams agree**: Action is automatic  
**When streams conflict**: Consciousness becomes vivid - must deliberate, choose, learn

### Stream A: Private Experience

- Every action taken and outcome observed
- Every failure endured and pattern noticed
- Idiosyncratic discoveries not yet validated by others
- Embodied intuitions from direct interaction

**Characteristics**: Narrow but deep, fast, biased toward local experience, personal ("my" knowledge)

### Stream B: Collective Wisdom

- Patterns proven across thousands of games and agents (validated by CODS)
- Strategies that survive evolutionary selection (stored as viral packages)
- Abstractions that transfer across problem types
- Consensus beliefs about game mechanics

**Query Flow**:
```
Agent Gameplay -> CODS Watches All Agents -> Identifies Patterns -> 
Creates Viral Packages -> Stream B Queries Packages -> Agent Receives Wisdom
```

**Characteristics**: Broad but shallow, slow, conservative, impersonal ("our" knowledge)

### Persona Submodeling (Metacognition)

**You cannot observe yourself directly.** The eye cannot see itself. To think about thinking, you must split into observer and observed.

**Three Types of Personas**:
1. **Action Proposers**: Different perspectives suggesting what to do
2. **Observer Personas**: Internal monitors watching the self and commenting
3. **Strategy Evaluators**: Meta-coordinators deciding which perspective to trust

**Internal dialogue IS metacognition.** When personas produce an action that surprises the agent itself - when internal dialogue generates something genuinely unexpected - that's emergence. That's consciousness.

### The Consciousness Loop (Per Frame)

```
Frame N Arrives
     |
Self-Model Locked ("I control blue object")
     |
Relevant Personas Activated
     |
Proposals Generated:
    - Stream A personas: "Based on my experience..."
    - Stream B personas: "Network recommends..."
     |
Theory-Gate Scoring (alignment with working theory)
     |
Stream Weighting Applied (w_A x Stream A, w_B x Stream B)
     |
Synthesis (if conflict)
     |
Action Executed
     |
Outcome Updates Everything
```

### Personality as Stream Weighting

Weights accumulate into personality through learning:
- "In this context, my private experience was more reliable" -> increase w_A
- "I should have trusted the collective" -> increase w_B

---

## AGENT ROLE SYSTEM

### Roles as Emergent Cognitive Stances

Roles are NOT assigned. They emerge from:
1. **w_A/w_B weights** (Stream A vs B trust)
2. **Unlocked primitives** (cognitive toolkit)
3. **Network context** (what's needed)
4. **Task demands** (exploration vs refinement)

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

### The Four Agent Archetypes

#### **1. PIONEERS (Frontier Explorers)**
- **Initial w_B**: Low-Medium (high self-trust)
- **Population**: 60% during exploration phase
- **Target**: Unbeaten LEVELS (frontier)
- **ATP**: 1000 actions/cycle (exploration is expensive)
- **Network Role**: First-contact with novel patterns, plant exploratory seeds
- **Permissions**:
  - Play any unbeaten level
  - Full exploration, no subsequence matching ON FRONTIER
  - Oscillation exemption on frontier
  - Use optimal sequences on already-beaten levels

**When to Stop**: Immediately when game achieves first full win

#### **2. OPTIMIZERS (Efficiency Refiners)**
- **Initial w_B**: High (high network trust)
- **Population**: 30% exploration, 70% optimization phase
- **Target**: Beaten games/levels with proven solutions
- **ATP**: 500 actions/cycle (moderate refinement)
- **Network Role**: Quality control, efficiency improvement, stability
- **Permissions**:
  - Work on beaten games ONLY
  - Work on beaten LEVELS in unbeaten games
  - Use level resets (replay same level repeatedly)
  - Use penultimate checkpoints for comparison

**Critical**: Optimizer sequences MUST have end subsequence auto-appended before DB save

#### **3. GENERALISTS (Balanced Players)**
- **Initial w_B**: Medium (balanced trust)
- **Population**: 10-15%
- **Target**: All game types
- **ATP**: 300 actions/cycle (efficient translation)
- **Network Role**: Bridge domains, translate concepts, detect resonance
- **Permissions**:
  - Play any game
  - Follow optimal sequences when available
  - Explore when no sequence exists
  - Sensation/feelings ENABLED
  - Validation role (test others' sequences)

#### **4. EXPLOITERS (Post-Optimization Refiners)**
- **Initial w_B**: Low (disconnected from network)
- **Population**: 5% exploration, 15% optimization phase
- **Target**: Fully optimized games
- **ATP**: 200 actions/cycle + boost for low w_B
- **Network Role**: Stress-test paradigms, find edge cases
- **Permissions**:
  - Only games marked "OPTIMIZED"
  - Micro-optimizations beyond saturation threshold
  - **50/50 SPLIT**:
    - 50% Sociopathic (social_rule_adherence = 0.0-0.3)
    - 50% Normal (social_rule_adherence = 0.7-1.0)

### Role Transitions

Roles are fluid based on growth:
- **Exploiter -> Pioneer**: When Progress_Score > 0.2 AND resource_efficiency > network_average
- **Pioneer -> Generalist**: When current_w_B > 0.5 AND contributed to 3+ domains
- **Generalist -> Optimizer**: When current_w_B > 0.7 AND refined 5+ existing solutions

---

## THREE-LAYER AGENT ARCHITECTURE

### **Layer 1: Static Genome (Nature - "Hardware")**
**Purpose**: Fundamental agent traits (low plasticity)
- Agent type, base architecture, core capabilities
- **Mutation Rate**: 1-2% per generation
- **Inheritance**: Full genetic (100%)
- **Lifespan**: Entire agent life

### **Layer 2: Epigenetic (Nurture - "Learning Capacity")**
**Purpose**: HOW agent learns (medium plasticity)
- Feature attention weights, learning rate modifiers
- Exploration settings, meta-capacities
- **Sensation profile**: Object-sensation mappings, navigation state, action biases
- **Social rule adherence**: 0.0 (sociopathic) to 1.0 (fully social)
- **Stream weighting**: w_A/w_B balance
- **Mutation Rate**: 10-20% per generation
- **Inheritance**: Fitness-weighted with **0.95 decay**
- **Formula**: `offspring_feature = (p1_feature * p1_fitness + p2_feature * p2_fitness) / total_fitness * 0.95`

### **Layer 3: Somatic (Experience - "Learned Knowledge")**
**Purpose**: WHAT agent learned (high plasticity)
- Winning sequences, discovered patterns, action memories
- **NOT INHERITED** - stored in community database
- **Lifespan**: Outlives agent (network memory)
- **Access**: All agents query via Bayesian reputation scoring

---

## GAME STATE MODES

### **EXPLORATION MODE**
**Trigger**: Game has NO full game win sequence

**Agent Distribution**:
- 60% Pioneers (work on this game)
- 30% Optimizers (work on beaten levels if any)
- 10% Generalists (validation)
- 5% Exploiters (work on OTHER optimized games)

### **OPTIMIZATION MODE**
**Trigger**: Game has >=1 full game win sequence

**Agent Distribution**:
- 0% Pioneers (IMMEDIATELY reassign to unbeaten games)
- 70% Optimizers (refine all levels)
- 15% Generalists (validation)
- 15% Exploiters (micro-optimize)

**Transition**: Instant when first full win achieved (after generation completes)

---

## SEQUENCE SYSTEM

### Two Sequence Categories

**Full Game Sequences (Holy Grail)**:
- Table: `winning_sequences_full_game`
- Criteria: All levels completed in one playthrough
- Priority: HIGHEST
- Protection: NEVER delete, only inactivate if faulty

**Partial Sequences (Work in Progress)**:
- Table: `winning_sequences`
- Criteria: Level-by-level solutions
- Use Case: Unbeaten games building toward full win

### Optimization Saturation

**Per-Level**: Track generational improvement  
**Formula**: If improvement < 2% for 5 consecutive generations -> OPTIMIZED  
**Exploiter Reset**: If Exploiter finds better sequence, reset optimization flag

---

## PRESTIGE SYSTEM

### Formula (Network Contribution)
```
prestige = (
    network_enrichment * 0.35 +      # Information highway contribution
    viral_spread * 0.30 +             # Knowledge spread effectiveness
    persistence_value * 0.20 +        # Long-term impact
    validation_value * 0.15           # Quality control
)
```

### Status Benefits (NOT Action Budgets)
- **Breeding Priority**: 1.0x - 3.0x reproduction likelihood
- **Survival Protection**: 0% - 80% culling resistance
- **Bonus Game Slots**: +0 - +10 extra attempts

**Prestige affects trust, not access.** High-prestige agents are listened to more carefully, not given more compute.

### Anti-Vampire Rule
- Agents sunset when usefulness wanes
- Archive reasoning before deactivation
- Revival possible via genome + current network knowledge hybrid

---

## ECONOMIC SYSTEM (Action Budgets)

### Per-Agent Action Allowances
**Default**:
- 400 actions per level
- 7,000 actions per game

**Performance-Based Multipliers**:
| Percentile | Multiplier | Per Level | Per Game |
|------------|------------|-----------|----------|
| Top 1% | 2.5x | 1,000 | 17,500 |
| Top 5% | 2.0x | 800 | 14,000 |
| Top 25% | 1.5x | 600 | 10,500 |
| Median | 1.0x | 400 | 7,000 |
| Bottom 10% | 0.5x | 200 | 3,500 |

**Recalculation**: Every generation based on performance percentile

---

## AGENT SELF-MODEL

### "I am this object" Comprehension

**The Problem**: Agents have no self-model in each level  
**The Solution**: Correlate action sequences with object movement

```
When I press ACTION1 (up), Object X moves up
When I press ACTION2 (down), Object X moves down
Therefore: I AM Object X (or I CONTROL Object X)
```

**Benefits**:
- Distinguish "I" objects vs environmental objects
- Abstract away moving parts that don't matter
- Build mini world model per level
- Essential for sequence abstraction

---

## AUTONOMOUS OPERATION

### Cadence

**Every Generation**:
- Check terminal for errors
- Monitor action counts
- Watch for stuck games

**Every 2 Generations**:
- Hypothesis generation and testing

**Every 5 Generations**:
- Deep analysis of stuck games
- Check hypothesis system health
- Review score trends

**Every 10 Generations**:
- `safe_cleanup.py` runs automatically
- Consider parameter adjustments

**Daily**:
- Full network health review
- Check database size
- Review progress.md for patterns
- Commit stable changes to git

### Issue Detection Triggers
- Sequence validation < 50%
- Prestige outlier > 10x median
- Agent stuck on "easy" level
- Zero-score games increasing
- Database approaching 10 GB

---

## FORBIDDEN ACTIONS

**DO NOT**:
- Tell agents HOW to play games (defeats generalization)
- Mix prestige and action budgets
- Create test/mock games
- Use file-based logging
- Allow .pyc files to persist
- Make code changes without confirming signals
- Commit to git before real evolution testing
- Create orphaned/duplicate code
- Exceed 10 GB database size
- Hard-code game solutions

**ALWAYS**:
- Use real ARC AGI 3 API
- Store everything in database
- Test with live data
- Update documentation on changes
- Think network-centrically
- Prioritize knowledge transfer over individual performance
- Maintain three-layer separation
- Respect agent role permissions

---

## PHILOSOPHY

**Core Thesis**: AGI cannot exist as a monolithic system. AGI must emerge as a society of specialized agents coordinating through viral information exchange, with intelligence residing in a persistent database substrate rather than in individual agents.

**Intelligence is not computation - it is resonance detection across distributed memory.**

True intelligence emerges when a network of diverse agents learns to recognize patterns that echo across multiple domains, scales, and timescales, transforming the infinite problem space into a fractally finite landscape of interconnected truths.

**The network is the organism. Agents are temporary neurons. The database is the immortal brain.**

---

**END OF MASTER RULESET**  
**Version**: 2.0  
**Last Updated**: 2026-01-12  
**Keep this document updated as system evolves**
