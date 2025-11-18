# PRIORITY TO-DO LIST - CRITICAL FIXES

**Date**: 2025-11-18  
**Context**: Fixes identified from historical analysis + user feedback  
**Status**: Ready for autonomous implementation

---

## 🚨 BLOCKING ISSUES (Fix Immediately - Generation 0)

### **#1: Optimizer Penultimate Checkpoint Bug** ⚠️ **BLOCKS ALL PROGRESS**
**Problem**: Optimizers save partial sequences without final "end subsequence" actions
**Impact**: Agents stuck on levels they should complete easily
**Root Cause**: Level resets don't append guaranteed-win ending before DB save

**Fix Steps**:
1. Identify where optimizer sequences are saved to database
2. Before saving, detect if it's a level-reset optimization
3. Query for "end subsequence" (last N actions that guarantee level win)
4. Auto-append end subsequence to optimizer's partial sequence
5. Save complete sequence to database

**Alternative**: Create `endsequences` table, join on retrieval (more efficient?)

**Test**: Optimizer sequence → replay → 100% completion rate on beaten levels

**Files to Modify**:
- `core_gameplay.py` (sequence storage logic)
- Database schema (potentially add `endsequences` table)

**Unit Test**: "Every optimizer sequence for beaten level ends with level win"

---

### **#2: Generalist Sensation Restoration**
**Problem**: Generalists have "feelings removed" (sensation engine disabled)
**Impact**: Reduced generalist effectiveness, no emotional intelligence

**Fix Steps**:
1. Find where Generalists have sensation disabled
2. Re-enable sensation/emotional intelligence for Generalists
3. Test performance difference

**Files to Modify**:
- Agent creation/configuration logic
- Potentially `sensation_engine.py` integration

**Test**: Generalist agents successfully use sensation-based navigation

---

## 🔥 HIGH PRIORITY (Fix in Generation 1-2)

### **#3: Full Game Sequence Table Separation**
**Problem**: Full game wins mixed with partial sequences
**Impact**: Holy grail sequences not protected, can be deleted

**Fix Steps**:
1. Create `winning_sequences_full_game` table
2. Migrate existing full game wins
3. Update sequence query logic to prioritize full game sequences
4. Implement "inactivate only, never delete" protection
5. Track least-action sequence as default reference

**Database Schema**:
```sql
CREATE TABLE winning_sequences_full_game (
    sequence_id TEXT PRIMARY KEY,
    game_id TEXT NOT NULL,
    total_actions INTEGER NOT NULL,
    total_levels_completed INTEGER NOT NULL,
    action_sequence TEXT NOT NULL,  -- JSON
    success_rate REAL DEFAULT 1.0,
    is_default_reference BOOLEAN DEFAULT FALSE,  -- Least action = default
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE  -- Inactivate, never delete
);
```

**Test**: Full game sequences never deleted, only inactivated

---

### **#4: Exploiter 50/50 Split (Social Rule Adherence Spectrum)**
**Problem**: All exploiters follow network wisdom uniformly
**Impact**: No A/B testing of social vs independent decision-making

**Fix Steps**:
1. Add `social_rule_adherence` to agent genome/epigenetics (0.0 to 1.0)
2. On agent creation:
   - 50% Exploiters: `social_rule_adherence = random(0.0, 0.3)` (sociopathic)
   - 50% Exploiters: `social_rule_adherence = random(0.7, 1.0)` (normal)
3. Update sequence selection logic to respect adherence level
4. Track performance by adherence category

**Files to Modify**:
- `agent_factory.py`
- `evolutionary_engine.py` (epigenetic inheritance)
- Sequence retrieval logic

**Test**: Exploiter population has bimodal `social_rule_adherence` distribution

---

### **#5: Database Schema Auto-Update System**
**Problem**: `complete_database_schema.sql` drifts out of sync with actual schema
**Impact**: LLM makes bad SQL queries, documentation lies

**Fix Steps**:
1. Create script to export current schema from live database
2. Auto-run after any schema modification
3. Update `complete_database_schema.sql`
4. Add schema version tracking
5. Optionally: Git hook to verify schema consistency before commit

**Script**: `export_schema.py` (already exists, needs automation)

**Test**: Schema file matches live database after schema changes

---

## ⚡ MEDIUM PRIORITY (Fix in Generation 3-5)

### **#6: Agent Self-Model Implementation**
**Problem**: Agents have no concept of "I am this object" 
**Impact**: Can't distinguish controlled objects from environment

**Fix Steps**:
1. Track correlation between actions and object movements
2. Identify which objects respond to which actions
3. Tag controlled objects as "self" in sequence metadata
4. Build object-action correlation matrix per level
5. Store "I control these objects" in agent memory

**Implementation Ideas**:
- `ObjectIdentificationEngine` class
- Per-level object tracking
- Action → movement correlation analysis

**Test**: Agents correctly identify controlled objects in multi-object games

---

### **#7: Sequence Validation Subroutine**
**Problem**: No automated system to detect stale/invalid sequences
**Impact**: Bad sequences accumulate, agents fail repeatedly

**Fix Steps**:
1. Create end-of-generation subroutine (before next assignment)
2. Compare stored sequence frames vs actual gameplay frames (multiple agents)
3. Distinguish real problems (movement changes) vs cosmetic (color changes)
4. Flag stale sequences for review
5. Implement voting: Agents petition to abandon bad sequences

**Files to Create**:
- `sequence_validation_subroutine.py`

**When to Run**: After generation completes, before next generation assignment

**Test**: Subroutine correctly flags invalid sequences, ignored cosmetic changes

---

### **#8: Comprehensive Unit Test Suite**
**Problem**: No automated testing, regressions happen frequently
**Impact**: Sequence system broken 10 times, prestige broken 6 times

**Test Coverage Needed**:
1. **Sequence System**:
   - Storage: Sequences saved correctly
   - Retrieval: Can retrieve by game

/level
   - Validation: Stale detection works
   - Matching: Frame matching logic
   - End subsequence: Optimizer append works

2. **Prestige System**:
   - Calculation: Edge cases (zero scores, division by zero)
   - Dampening: Population size scaling
   - Caps: Adaptive cap enforcement

3. **Agent Roles**:
   - Assignment: Correct game/level targeting
   - Transition: Exploration → optimization mode shift
   - Permissions: Pioneers don't touch optimized, etc.

4. **Database Schema**:
   - Integrity: Foreign keys work
   - Constraints: Required fields enforced

**Framework**: pytest (automated, run before every commit)

**Test**: 95%+ coverage on core systems

---

### **#9: Agent Revival Mechanism**
**Problem**: Good agents die too early, knowledge lost
**Impact**: Network loses valuable reasoning when elite agents sunset

**Fix Steps**:
1. Track agent performance history before deactivation
2. Store "reasoning style" metadata (genome + key epigenetics)
3. Implement two revival modes:
   - **Mode B**: Clone genome + inject current network knowledge
   - **Mode C**: "Spiritual successor" with same reasoning style, new implementation
4. Trigger: Network struggles on previously-solved games
5. Revive both modes simultaneously for comparison

**Files to Create**:
- `agent_revival_system.py`

**Database Tables**:
```sql
CREATE TABLE agent_graveyard (
    agent_id TEXT PRIMARY KEY,
    genome TEXT NOT NULL,
    epigenetics TEXT NOT NULL,
    reasoning_style TEXT,  -- Metadata description
    performance_summary TEXT,  -- JSON stats
    deactivated_at TIMESTAMP,
    deactivation_reason TEXT,
    revival_count INTEGER DEFAULT 0
);
```

**Test**: Revived agents outperform baseline on previously-solved games

---

### **#10: Optimization Saturation Tracking (Per-Level)**
**Problem**: No systematic way to detect when level is "optimized enough"
**Impact**: Wasted compute on diminishing returns

**Fix Steps**:
1. Track per-level improvement per generation
2. Calculate: `improvement_pct = (gen_N_actions - gen_N+1_actions) / gen_N_actions * 100`
3. If `improvement_pct < 2%` for 5 consecutive generations → mark OPTIMIZED
4. Exploiters can reset flag if they find better sequence
5. Optimizers skip optimized levels (unless flag reset)

**Database Schema**:
```sql
CREATE TABLE level_optimization_status (
    game_id TEXT NOT NULL,
    level_number INTEGER NOT NULL,
    is_optimized BOOLEAN DEFAULT FALSE,
    best_action_count INTEGER NOT NULL,
    generations_without_improvement INTEGER DEFAULT 0,
    last_improvement_generation INTEGER,
    optimization_history TEXT,  -- JSON: [gen1: 45 actions, gen2: 43, ...]
    PRIMARY KEY (game_id, level_number)
);
```

**Test**: Levels correctly marked optimized, flag reset when better sequence found

---

## 🔧 INFRASTRUCTURE (Ongoing)

### **#11: Pioneer Reassignment on Game Win**
**Problem**: Pioneers keep working on games after first full win
**Impact**: Wasted exploration capacity

**Fix Steps**:
1. Detect when game achieves first full win
2. After current generation completes:
   - Mark game as OPTIMIZATION MODE
   - Reassign ALL Pioneers to unbeaten games
   - Convert some to Optimizers/Exploiters if no unbeaten games available
3. Update agent operating mode tracking

**Trigger**: `winning_sequences_full_game` gets first entry for game_id

**Test**: Zero pioneers on games with full wins

---

### **#12: Agent Personal History Access**
**Problem**: Agents don't access their own past gameplay for decision-making
**Impact**: No continuity, agents don't learn from personal mistakes

**Fix Steps**:
1. Track per-agent action history
2. Store personal success/failure patterns
3. Provide agents with:
   - Personal history: "What did I try before?"
   - Network data: "What does collective wisdom say?"
4. Decision-making: Mix personal will + network intuition

**Database Tables**:
```sql
CREATE TABLE agent_personal_history (
    agent_id TEXT NOT NULL,
    game_id TEXT NOT NULL,
    level_number INTEGER NOT NULL,
    action_sequence TEXT,  -- JSON
    outcome TEXT,  -- 'success', 'failure', 'partial'
    score_achieved REAL,
    lessons_learned TEXT,  -- JSON
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (agent_id, game_id, level_number, timestamp)
);
```

**Test**: Agents query personal history before network sequences

---

### **#13: Sequence Abstraction Engine (Future)**
**Problem**: Agents use exact frame matching (brittle)
**Impact**: Sequences break on minor game changes

**Long-term Vision**:
- Pattern matching (lossy) like humans
- Abstract general path from sequences
- Sunset exact matching once abstraction works

**Status**: Research phase, not immediate priority
**Complexity**: High (may require separate AI model)

---

## 📝 DOCUMENTATION UPDATES

### **#14: Update `complete_database_schema.sql`**
**Problem**: Shows 70 tables, actually 73 tables
**Fix**: Regenerate from live database, add version tracking

---

### **#15: Update `ouroboros_final_implementation.md`**
**Problem**: No mention of Phase 4-5, sensation engine, specialist mode
**Fix**: Add missing phases, update implementation examples

---

### **#16: Mark Roadmap Phases Complete**
**Problem**: `Roadmap_Level_4_to_5.md` doesn't show completion status
**Fix**: Mark Phase 0-5 as ✅ COMPLETE with dates

---

## 🎯 VERIFICATION CHECKLIST

After each fix above:
- [ ] Unit tests pass
- [ ] Integration test with real evolution (2 generations minimum)
- [ ] Database schema updated if needed
- [ ] Documentation updated
- [ ] Git commit with clear message
- [ ] Email user with fix summary

---

## 📊 IMPLEMENTATION ORDER

**Week 1** (Blocking):
1. #1: Optimizer checkpoint bug
2. #2: Generalist sensation restoration

**Week 2** (High Priority):
3. #3: Full game sequence table
4. #4: Exploiter 50/50 split
5. #5: Database schema auto-update

**Week 3** (Medium Priority):
6. #6: Agent self-model
7. #7: Sequence validation subroutine
8. #8: Unit test suite

**Week 4** (Infrastructure):
9. #9: Agent revival mechanism
10. #10: Optimization saturation tracking
11. #11: Pioneer reassignment logic
12. #12: Agent personal history

**Ongoing**:
- #13: Sequence abstraction (research)
- #14-16: Documentation updates

---

## 🔔 DAILY CHECKLIST

Every day:
1. Check sequence validation success rate
2. Monitor prestige distribution (outliers?)
3. Track database size
4. Review stuck agents
5. Email user with updates

Every 2 generations:
1. Generate hypotheses for observed issues
2. Test hypotheses
3. Confirm or reject based on data

Before every git commit:
1. Run unit tests
2. Test with real evolution
3. Update documentation
4. Verify no regressions

---

**END OF TO-DO LIST**
**Update this as fixes completed and new issues discovered**
