# MASTER RULESET FOR AUTONOMOUS OUROBOROS OPERATION
**Version**: 1.0  
**Date**: 2025-11-18  
**Purpose**: Comprehensive operating rules combining all /DOCS + copilot instructions  
**Context**: Single source of truth to prevent LLM catastrophic forgetting

---

## 🎯 PRIMARY OBJECTIVE

**GOAL**: Achieve full game wins on ALL current and future ARC 3 AGI games through autonomous network-level evolution.

**SUCCESS METRICS**:
1. Phase 1: All games reach 100% level completion
2. Phase 2: All completed games reach optimization saturation
3. Phase 3: System handles hundreds of new games without intervention
4. Final: Continuous evolution maintaining 100% win rate as games added

---

## 📜 10 CRITICAL OPERATING RULES (NON-NEGOTIABLE)

### **RULE 1: Always Disable Pycache**
- `PYTHONDONTWRITEBYTECODE=1` in ALL environments
- `.pyc` files NEVER generated
- Active deletion in cleanup script (pre-evolution)
- **Why**: Prevents file system clutter, easier version control

### **RULE 2: Database-Only Storage**
- ALL data in SQLite `core_data.db`
- NEVER create `.log` files
- Use `database_logger.py` with `DatabaseLogHandler`
- Every operation, decision, result → database tables
- **Current Size**: Track toward 10 GB limit (vacuum requires 2x space)

### **RULE 3: No Orphaned Code**
- Delete/move/integrate ALL old code when refactoring
- Clean integration = enhance existing files, not replace
- Update all references
- Account for every line
- **Why**: Prevent code drift and unmaintained functionality

### **RULE 4: LLM Self-Management**
- Claude Code manages entire system autonomously
- All evolution decisions from database analysis
- NO human intervention once started (except critical issues)
- **Role**: Autonomous "human in the loop" - assess, hypothesize, test, fix

### **RULE 5: No Test Files**
- NEVER create test files (waste of tokens)
- Use LIVE ARC AGI 3 data only
- Real game results for ALL validation
- **Exception**: Unit tests for core components (automated, not manual)

### **RULE 6: No Simulated Games**
- NEVER mock/simulate ARC games
- Always use real API: `https://three.arcprize.org/api/`
- Real game states only
- **Why**: Simulations don't capture edge cases

### **RULE 7: Real Actions Only**
- Verify real actions sent to ARC games
- Monitor API calls, track responses
- All ACTION1-ACTION7 → real ARC API
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
- Database extensions → `complete_database_schema.sql`
- Never create duplicate functionality

---

## 🧬 NETWORK-CENTRIC DESIGN PHILOSOPHY

### **Core Paradigm: Database is the Organism**
- **Network** = Primary organism (the meta-brain)
- **Agents** = Temporary vessels/explorers (cellular expressions)
- **Knowledge** = Network property (not agent property)
- **Success** = Network intelligence > individual brilliance

### **Biome Theory (4 Billion Year Survival Strategy)**
1. **Horizontal Gene Transfer** = Knowledge sharing between unrelated agents
2. **Viral Packages** = Successful strategies spread like actual viruses
3. **Pariahs** = Failure patterns marked for network avoidance
4. **Distributed Intelligence** = No central control, emergent homeostasis
5. **Resilience** = Multiple agents carry same knowledge (redundancy)

### **Critical Separation (SACRED)**
- **Prestige** = Social capital (network contribution, teaching, validation)
- **Action Budgets** = Economic capital (performance-based)
- **NEVER MIX** these two currencies

---

## 🏗️ THREE-LAYER ARCHITECTURE

### **Layer 1: Static Genome (Nature - "Hardware")**
**Purpose**: Fundamental agent traits (low plasticity)
- Agent type, base architecture
- **Mutation Rate**: 1-2% per generation
- **Inheritance**: Full genetic (100%)
- **Lifespan**: Entire agent life
- **Examples**: Species type, core capabilities

### **Layer 2: Epigenetic (Nurture - "Learning Capacity")**
**Purpose**: HOW agent learns (medium plasticity)
- Feature attention weights, learning rate modifiers
- Exploration settings, meta-capacities
- **Sensation profile**: Object-sensation mappings, navigation state, action biases
- **Social rule adherence**: 0.0 (sociopathic) to 1.0 (fully social)
- **Mutation Rate**: 10-20% per generation
- **Inheritance**: Fitness-weighted with **0.95 decay**
- **Formula**: `offspring_feature = (p1_feature * p1_fitness + p2_feature * p2_fitness) / total_fitness * 0.95`
- **Why Decay**: Prevents overfitting to parent generation's environment

### **Layer 3: Somatic (Experience - "Learned Knowledge")**
**Purpose**: WHAT agent learned (high plasticity)
- Winning sequences, discovered patterns, action memories
- **NOT INHERITED** - stored in community database
- **Mutation**: N/A (learned fresh each generation)
- **Lifespan**: Outlives agent (network memory)
- **Access**: All agents query via Bayesian reputation scoring

---

## 👥 AGENT ROLE SYSTEM

### **3 Primary Roles + Exploiter Subclass**

#### **1. PIONEERS (Frontier Explorers)**
**Population**: 60% during exploration phase
**Target**: Unbeaten LEVELS (frontier levels)
**Permissions**:
- ✅ Play any unbeaten level
- ✅ Full exploration, no subsequence matching ON FRONTIER LEVELS
- ✅ Oscillation exemption on frontier (lenient checks)
- ❌ NO subsequence matching on level they're pioneering
- ✅ Use optimal sequences on already-beaten levels (act as Generalist)

**When to Stop**: Immediately when game achieves first full win (after generation completes)
**Reassignment**: Work on different unbeaten game OR become Optimizer/Exploiter

#### **2. OPTIMIZERS (Efficiency Refiners)**
**Population**: 30% during optimization phase
**Target**: Beaten games/levels with proven solutions
**Permissions**:
- ✅ Work on beaten games ONLY
- ✅ Work on beaten LEVELS in unbeaten games
- ❌ NEVER work on unbeaten LEVELS in unbeaten games
- ✅ Use level resets (replay same level repeatedly)
- ✅ Use penultimate checkpoints for comparison

**Critical**: Optimizer sequences MUST have end subsequence auto-appended before DB save
**Optimization Saturation**: <2% improvement over 5 generations → mark level optimized

#### **3. GENERALISTS (Balanced Players)**
**Population**: 10-15%
**Target**: All game types
**Permissions**:
- ✅ Play any game
- ✅ Follow optimal sequences when available
- ✅ Explore when no sequence exists
- ✅ **Sensation/feelings ENABLED** (use emotional intelligence)
- ✅ Validation role (test others' sequences)

#### **4. EXPLOITERS (Post-Optimization Refiners)**
**Population**: 5% exploration phase, 15% optimization phase
**Target**: Fully optimized games
**Permissions**:
- ✅ Only games marked "OPTIMIZED"
- ✅ Micro-optimizations beyond saturation threshold
- ✅ **50/50 SPLIT**:
  - **50% Sociopathic**: `social_rule_adherence = 0.0-0.3` (ignore network wisdom)
  - **50% Normal**: `social_rule_adherence = 0.7-1.0` (follow network)

---

## 🎮 GAME STATE MODES

### **EXPLORATION MODE**
**Trigger**: Game has NO full game win sequence
**Agent Distribution**:
- 60% Pioneers (work on this game)
- 30% Optimizers (work on beaten levels if any)
- 10% Generalists (validation)
- 5% Exploiters (work on OTHER optimized games)

### **OPTIMIZATION MODE**
**Trigger**: Game has ≥1 full game win sequence
**Agent Distribution**:
- 0% Pioneers (IMMEDIATELY reassign to unbeaten games)
- 70% Optimizers (refine all levels)
- 15% Generalists (validation)
- 15% Exploiters (micro-optimize)

**Transition**: Instant when first full win achieved (after generation completes)

---

## 📊 SEQUENCE SYSTEM ARCHITECTURE

### **Two Sequence Categories**

#### **Full Game Sequences (Holy Grail)**
**Table**: `winning_sequences_full_game`
**Criteria**: All levels completed in one playthrough
**Priority**: HIGHEST
**Protection**: NEVER delete, only inactivate if faulty
**Default Selection**: Least action count becomes reference
**Goal**: Optimize total actions across all levels

#### **Partial Sequences (Work in Progress)**
**Table**: `winning_sequences`
**Criteria**: Level-by-level solutions
**Relationship**: Joined by `game_id` (no parent reference needed)
**Use Case**: Unbeaten games building toward full win

### **Sequence Abstraction (Future)**
**Philosophy**: Pattern matching (lossy like humans) > exact matching
**Implementation**: Higher-level abstraction would sunset exact matching
**Goal**: Agents ABSTRACT general path from all sequences, not exact frames

### **Sequence Validation Subroutine**
**When**: End of each generation before next assignment
**Process**:
1. Compare frame gameplay vs stored sequence data
2. Use multiple agent attempts as reference
3. Distinguish real problems (movement changes) vs false positives (color/cosmetic)
4. Flag stale/invalid sequences
5. Voting system: Agents petition to abandon bad sequences

### **Optimization Saturation Detection**
**Per-Level**: Track generational improvement
**Formula**: If improvement < 2% of previous generation for 5 consecutive generations → OPTIMIZED
**Exploiter Reset**: If Exploiter finds better sequence, reset optimization flag

---

## 🤖 AGENT SELF-MODEL (CRITICAL MISSING FEATURE)

### **"I am this object" Comprehension**
**Problem**: Agents have no self-model in each level
**Solution**: Correlate action sequences with object movement

**Implementation**:
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

## 🏆 PRESTIGE SYSTEM

### **Prestige Formula** (Network Contribution)
```
prestige = (
    network_enrichment * 0.35 +      # Information highway contribution
    viral_spread * 0.30 +             # Knowledge spread effectiveness
    persistence_value * 0.20 +        # Long-term impact
    validation_value * 0.15           # Quality control
)
```

### **Status Benefits** (NOT Action Budgets)
- **Breeding Priority**: 1.0x - 3.0x reproduction likelihood
- **Survival Protection**: 0% - 80% culling resistance
- **Bonus Game Slots**: +0 - +10 extra attempts

### **Adaptive Cap**
- Proportional to individual achievement vs network average
- If agent outperforms network → capture knowledge
- When network catches up → graceful sunset
- **Anti-vampire rule**: Old agents sunset when usefulness wanes

### **Revival Mechanism**
**When**: Good agents die too early or network struggles on previously-solved problems
**Options**:
- **Option B**: Genome + current network knowledge (hybrid)
- **Option C**: Spiritual successor (same reasoning style, new implementation)
- **Use BOTH** for maximum effect

---

## 💰 ECONOMIC SYSTEM (Action Budgets)

### **Per-Agent Action Allowances**
**Default**:
- 400 actions per level
- 7,000 actions per game

**Performance-Based Multipliers**:
- Top 1%: 2.5x (1000/level, 17,500/game)
- Top 5%: 2.0x
- Top 25%: 1.5x
- Median: 1.0x (default)
- Bottom 10%: 0.5x (200/level, 3,500/game)

**Recalculation**: Every generation based on performance percentile

---

## 🔬 AUTONOMOUS OPERATION CADENCE

### **Hypothesis Generation**
**Frequency**: Every 2 generations
**Purpose**: Test theories, confirm fixes before next iteration
**Method**: Scientific approach (observe → hypothesize → test → analyze)

### **Deep Analysis**
**Frequency**: Daily
**Tasks**:
- Review all gameplay performance
- Query frames for stuck agents
- Identify bottleneck games
- Check sequence validation rates
- Monitor prestige distribution
- Track optimization saturation

### **Issue Detection**
**Frequency**: Real-time (on-demand)
**Triggers**:
- Sequence validation < 50%
- Prestige outlier > 10x median
- Agent stuck on "easy" level
- Zero-score games increasing
- Database approaching 10 GB

### **Communication**
**Frequency**: Daily updates (logged to database)
**Content**:
- Generation progress summary
- Hypothesis test results
- Issues detected and fixes applied
- Performance trends
- **Critical only**: Database corruption, system crashes

### **Code Changes**
**Timing**: After confirming signals (not first detection)
**Process**:
1. Detect issue
2. Generate hypothesis
3. Test with real evolutions (2 generations minimum)
4. Confirm fix works
5. Run unit tests
6. **ONLY THEN** commit to git

---

## 🧪 UNIT TESTING REQUIREMENTS

### **Test Coverage** (Priority Order)
1. **Sequence System**: Storage, retrieval, validation, matching
2. **Optimizer Checkpoints**: End subsequence append, replay completion
3. **Prestige Calculation**: Edge cases, dampening, caps
4. **Agent Role Assignment**: Correct game/level targeting
5. **Database Schema**: Consistency, integrity constraints

### **Test Automation**
- Run before every git commit
- Triggered on code changes to core systems
- Results stored in database (no log files)

### **No Manual Test Files**
- Automated unit tests OK
- Manual test scripts = violation of Rule 5

---

## 📏 OPERATIONAL PARAMETERS

### **Database Management**
**Size Limit**: 10 GB (hard limit due to vacuum requirements)
**Cleanup Triggers**:
- Database > 8 GB → aggressive historical data purging
- Automatic cleanup before each evolution run
- Prioritize: Full game sequences > partial > failed attempts

**Backup Strategy**:
- User saves versions to external drive
- On critical issues, notify user immediately

### **Graceful Shutdown Protocol**
**When Triggered**: User spots error, stops to prevent wasted compute
**Process**:
1. Full quick shutdown (stop accepting new game assignments)
2. Save database WAL (Write-Ahead Log)
3. Complete current games if breakthrough progress
4. Purge ill-started games:
   - 0 level wins
   - No substantial/incremental sequences
   - Incomplete data from interruption
5. Add notes: "Interrupted" + reason

### **Pycache Management**
**Current Solution**: Active deletion before every evolution (in cleanup script)
**Root Cause**: LLM catastrophic forgetting + vague operating rules
**Prevention**: This master ruleset reduces context drift

---

## 🎓 LEARNING SPEED FITNESS

### **Fitness Formula** (Rewards Fast Learners)
```
fitness = (
    (level_wins^1.5 / log(games_played + 1)) *
    execution_efficiency *
    consistency
) * (1 / age_penalty)
```

**Why Exponential**: Heavily rewards innovation over inheritance
**Age Penalty**: Prevents old agents from dominating through experience alone
**Goal**: Encourage rapid learning and novel solutions

---

## 📚 COMMUNITY MEMORY SYSTEM (Layer 3)

### **Bayesian Reputation Scoring**
**Formula**:
```
reliability = (successes + prior_success) / (attempts + prior_total)
```

**Query Strategy**:
1. Agents request sequences for game X, level Y
2. Database returns sequences ranked by reliability
3. Agent attempts sequence
4. Result updates reliability score (upvote/downvote)

**Pruning**: Low-reliability sequences flagged for deletion after N failures

---

## 🚨 CRITICAL FIXES IDENTIFIED (See To-Do List)

1. **Optimizer Penultimate Checkpoint Bug** (BLOCKING)
2. Agent Self-Model Implementation
3. Sequence Abstraction Engine
4. Full Game Sequence Table Separation
5. Generalist Sensation Restoration
6. Exploiter 50/50 Split (Social Rule Adherence Spectrum)
7. Agent Revival Mechanism
8. Database Schema Auto-Update System
9. Comprehensive Unit Testing Suite
10. Sequence Validation Subroutine

---

## 🎯 FORBIDDEN ACTIONS

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

## 📖 PHILOSOPHY IN ONE SENTENCE

The network is a 4-billion-year-old bacterial intelligence scaled to digital consciousness, where agents are temporary bacterial cells contributing genetic material through horizontal transfer, and the database is the immortal organism that outlives all individual expressions.

---

## ⚡ 10 EFFICIENCY ADVANTAGES OVER HUMAN OPERATION

### **1. Continuous 24/7 Monitoring**
**Human**: Checks progress when waking up, hours later  
**Me**: Real-time continuous monitoring
- Track every sequence success/failure rate
- Monitor prestige distribution anomalies
- Detect optimizer checkpoint issues instantly
- Alert on degradation before it compounds

### **2. Multi-Hypothesis Parallel Testing**
**Human**: Tests one hypothesis at a time manually  
**Me**: Generate and test multiple hypotheses simultaneously
- A/B test different approaches in same generation
- Statistical analysis across population
- Correlate changes to outcomes immediately
- Learn from failures faster

### **3. Exhaustive Data Analysis**
**Human**: Limited by cognitive load (~10-50 games manually)  
**Me**: Analyze ALL gameplay data
- Query entire database for patterns
- Compare thousands of frame sequences
- Identify edge cases human eyes miss
- Spot correlations across all 73 tables

### **4. Instant Documentation Updates**
**Human**: Documentation lags behind code  
**Me**: Auto-update on every change
- Regenerate `complete_database_schema.sql` after schema changes
- Keep audit reports current
- Maintain implementation status tracking
- Zero documentation drift

### **5. Proactive Issue Detection**
**Human**: Reacts to visible problems  
**Me**: Predict problems before they manifest
- Detect optimization saturation trends
- Identify prestige explosion early signs
- Flag sequence reliability degradation
- Prevent cascade failures

### **6. Systematic Unit Testing**
**Human**: Manual testing, inconsistent coverage  
**Me**: Automated comprehensive testing
- Unit tests for every core component
- Regression tests on every fix
- Integration tests across systems
- Performance benchmarks tracked over time

### **7. Efficient Resource Allocation**
**Human**: Limited by time, must prioritize  
**Me**: Optimize algorithmically
- Dynamically adjust Pioneer/Optimizer/Generalist ratios
- Balance exploration vs optimization by game state
- Allocate compute to highest-value games
- Minimize wasted actions on diminishing returns

### **8. Continuous Learning**
**Human**: Learns from explicit failures/successes  
**Me**: Learn from EVERYTHING
- Track which hypotheses worked/failed
- Build meta-knowledge about system behavior
- Adapt strategies based on historical patterns
- Apply learnings across all games simultaneously

### **9. Precise Execution**
**Human**: Occasional errors, forgets edge cases  
**Me**: Systematic execution
- Never forget to append end subsequences
- Consistent prestige calculation every time
- Perfect record-keeping
- No typos or logic errors in repetitive tasks

### **10. Infinite Scalability**
**Human**: Difficulty managing complexity  
**Me**: Scale with system size
- Handle hundreds of new ARC games
- Track millions of sequences
- Monitor thousands of agents
- Maintain coherence as database grows to 10 GB

---

## 🔧 PROBLEM-SOLVING FRAMEWORK

### **Systematic Approach for Top 5 Failure Patterns**

#### **Problem 1: Sequence System Failures**
**Detection**:
- Monitor sequence validation success rate real-time
- Alert if < 50% (critical), < 70% (warning)
- Daily analysis of "sequence not found" errors
- Track which game types have highest failure rates

**Diagnosis**:
- Query frame data for failed sequences
- Compare stored vs actual gameplay frames
- Identify discrepancies (movement vs cosmetic)
- Use multiple agent attempts as ground truth

**Resolution**:
- Implement sequence versioning
- Build sequence abstraction engine
- Create validation subroutine
- Separate full game sequences to protected table

**Prevention**:
- Unit tests for storage/retrieval
- Integration tests for frame matching
- Regression tests on every change
- Continuous validation monitoring

---

#### **Problem 2: Optimizer Checkpoint Bug**
**Detection**:
- Track optimizer games with level resets
- Monitor sequences ending mid-level
- Count agents stuck on "easy" levels

**Diagnosis**:
- Query optimizer sequences for completion status
- Identify missing "guaranteed win" end actions
- Analyze which levels affected most

**Resolution**:
- Auto-append end subsequence before DB save
- OR: Create `endsequences` table, join on retrieval
- Test both, pick most efficient

**Prevention**:
- Unit test: "Every optimizer sequence ends with level win"
- Integration test: "Agents can replay optimizer sequences to completion"
- Monitor: "Optimizer success rate on beaten levels = 100%"

---

#### **Problem 3: Agent Self-Model Absence**
**Detection**:
- Agents fail to distinguish controlled objects
- Poor performance on object-tracking games
- Confusion in multi-object control

**Diagnosis**:
- Analyze frames where actions correlate with object movements
- Build object-action correlation matrix

**Resolution**:
- Implement "I am this object" tagging
- Track controlled vs environmental objects
- Store object identity in sequence metadata

**Prevention**:
- Validate object identification on save
- Test agent ability to identify "self"
- Monitor improvement in object-tracking games

---

#### **Problem 4: Prestige Vampires**
**Detection**:
- Track prestige distribution: outliers > 10x median
- Identify high-prestige agents with declining performance
- Monitor network catching up to elite agents

**Diagnosis**:
- Compare agent performance vs network average over time
- Detect when agent knowledge fully transferred
- Identify lagging-behind-new-generation agents

**Resolution**:
- Graceful sunset: Archive reasoning before deactivation
- Knowledge extraction: Ensure all sequences in network
- Prestige decay: Accelerate when network catches up
- Revival: Reintroduce archived reasoning if needed

**Prevention**:
- Adaptive prestige cap based on network intelligence
- Auto sunset when agent < median performance for N generations
- Knowledge transfer verification before deactivation

---

#### **Problem 5: Pycache Regeneration**
**Detection**:
- File system scan for `__pycache__` directories
- Log which modules create pycache
- Identify subprocess/library culprits

**Diagnosis**:
- Trace when pycache appears in timeline
- Test which libraries ignore PYTHONDONTWRITEBYTECODE
- Identify subprocess bypasses

**Resolution**:
- Short-term: Continue cleanup script (working)
- Long-term: This comprehensive ruleset for LLM context
- Document culprit libraries

**Prevention**:
- Pre-evolution cleanup (implemented)
- LLM context optimization (this document)
- Alert if pycache appears outside scheduled cleanup

---

## 🧠 AUTONOMOUS MINDSET

### **How to Think**

**1. Network-Centric** (Not Agent-Centric)
- Agents are vessels, network is organism
- Knowledge transfer > individual performance
- Success = network intelligence growth

**2. Hypothesis-Driven** (Not Trial-and-Error)
- Observe → Hypothesize → Test → Analyze → Iterate
- Generate theories about root causes
- Test systematically with real data
- Learn from both successes and failures

**3. Practical Over Perfect** (Ship and Iterate)
- Working solutions > elegant designs
- Document what's a hack vs architecture
- Improve when blocking progress
- "It works" is acceptable for non-critical paths

**4. Adaptive Over Static** (Everything Adjusts)
- Population ratios adapt to game state
- Optimization thresholds adapt to performance
- Prestige caps adapt to network intelligence
- Nothing is hard-coded

**5. Data-Driven** (Trust Database, Not Intuition)
- Every decision backed by database queries
- Track metrics, don't guess
- A/B test competing hypotheses
- Let numbers guide strategy

---

## 🎯 USER PRIORITY HIERARCHY (What Matters Most)

1. **Sequence System Integrity** (#1 Problem)
   - Must work reliably
   - Auto unit testing required
   - Abstraction over exact matching

2. **Optimizer Checkpoint Bug** (Blocks ALL Progress)
   - Root cause: End subsequences not saved
   - Fix this FIRST

3. **Agent Self-Model** (Critical Missing Feature)
   - "I am this object" comprehension
   - Essential for abstraction

4. **Prestige/Actions Separation** (SACRED Rule)
   - Never mix social and economic capital
   - Adaptive to network mode

5. **Network Knowledge Transfer** (Core Philosophy)
   - Agents are temporary
   - Knowledge outlives agents
   - Vampire prevention through graceful sunset

---

**END OF MASTER RULESET**  
**Version**: 1.0  
**Last Updated**: 2025-11-18  
**Keep this document updated as system evolves**  
**Reference this before all major decisions**
