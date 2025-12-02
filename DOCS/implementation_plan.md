# Implementation Plan: Fixing BitterTruth-AI System

**Created**: 2025-12-02  
**Updated**: 2025-12-02 (after Phase 0 cleanup)
**Priority**: CRITICAL - System has been running months with 0 game wins  
**Goal**: Achieve full game wins on all 6 ARC-AGI games  

---

## ✅ PHASE 0: COMPLETED - Emergency Sequence Cleanup

### Results
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Total sequences | 172 | 71 | -101 (garbage removed) |
| lp85 sequences | 21 | 0 | Deleted (corrupt) |
| Bloated (>10x) | 86 | 0 | All pruned |
| Max bloat ratio | 47,166x | ~2x | 99.99% reduction |
| Unit tests passing | 16/20 | 20/20 | All green |

### lp85 Deferred - Requires Symbolic Reasoning
lp85 is fundamentally different from other games:
- **Object tracking**: Multiple objects must be tracked independently
- **Compositional goals**: "A AND B must both be satisfied"
- **Causal simulation**: Actions affect all objects creating dependencies
- **State-space search**: Not a classification task

**Solution (future)**: Implement symbolic reasoning layer:
1. Parse visual scene into structured representation
2. Maintain world model that updates with each action
3. Evaluate goal conditions explicitly
4. Plan sequences using lookahead/search (BFS)

---

## 📊 Current Status (Post-Cleanup)

### Confirmed Issues Remaining
| Priority | Issue | Confidence | Next Action |
|----------|-------|------------|-------------|
| 🟠 P1 | Frame matching <75% for 3 games | 75% | Implement fuzzy matching |
| 🟠 P1 | Budget tight (<500 remaining) | 70% | Consider separate replay budget |
| 🟡 P2 | 26.8% exploration capacity | 60% | Increase pioneer ratio |

### Game Status (5 active games)
| Game | Max Level | Sequences | Validation | Priority |
|------|-----------|-----------|------------|----------|
| as66 | 4 | 11 | 92.5% | HIGH |
| vc33 | 3 | 14 | 99.9% | HIGH |
| ft09 | 2 | 11 | 72.8% | MEDIUM |
| sp80 | 1 | 11 | 74.1% | LOW |
| ls20 | 1 | 24 | 64.3% | LOW |

---

## 🔧 PHASE 1: FIX SEQUENCE CAPTURE (Days 2-3)

### Problem Statement
Sequences are capturing ALL exploration actions, not just the winning solution.

### Action Items

#### 1.1: Modify `_capture_winning_sequence()` in core_gameplay.py

**Current Behavior**: Captures all actions from session start
**Target Behavior**: Capture only actions from last checkpoint to win

```python
# BEFORE (pseudocode)
def _capture_winning_sequence(self, game_id, level, actions):
    # Captures ALL actions since game start
    sequence = self.action_history  # Problem: includes exploration
    self._save_sequence(sequence)

# AFTER (pseudocode)  
def _capture_winning_sequence(self, game_id, level, actions):
    # Only capture actions from last validated checkpoint
    checkpoint_frame = self._get_last_validated_checkpoint(game_id, level)
    if checkpoint_frame:
        # Extract only the winning subroutine
        winning_actions = self._extract_actions_since_checkpoint(checkpoint_frame)
        self._save_sequence(winning_actions)
    else:
        # No checkpoint, use heuristic to find solution
        winning_actions = self._extract_minimal_solution(self.action_history)
        self._save_sequence(winning_actions)
```

#### 1.2: Add sequence optimization pass

Create `optimize_sequence()` function:
1. Take raw action sequence
2. Remove oscillations (up-down-up-down patterns)
3. Remove dead-end explorations
4. Extract minimal path from start to win

#### 1.3: Add capture validation

Before saving any sequence:
1. Verify actions < 3x minimum for that level
2. If > 3x, mark as "unoptimized" for later compression
3. Add logging to track capture quality

**Success Criteria**:
- New sequences have bloat ratio < 3x
- Logging shows capture decisions

---

## 🔧 PHASE 2: FIX BUDGET SYSTEM (Days 4-5)

### Problem Statement
Agents run out of actions before reaching frontier levels.

### Action Items

#### 2.1: Increase max_total_actions

**Location**: `core_gameplay.py` game_config

```python
# BEFORE
self.game_config = {
    'max_actions_per_level': 250,
    'max_total_actions': 2000,  # Too low!
}

# AFTER
self.game_config = {
    'max_actions_per_level': 500,  # Doubled for exploration
    'max_total_actions': 7000,     # Restored to original
}
```

#### 2.2: Separate replay budget from exploration budget

**Concept**: Replay to frontier shouldn't count against exploration budget

```python
def play_game(self, game_id, agent):
    # Phase 1: Replay (free actions)
    replay_actions = self._replay_to_frontier(game_id)
    
    # Phase 2: Explore (budgeted)
    exploration_budget = self.game_config['max_total_actions']
    while exploration_budget > 0:
        action = self._get_exploration_action(agent)
        exploration_budget -= 1
        # ...
```

#### 2.3: Add budget tracking to monitoring

Log budget usage per agent/game to `budget_usage_log` table.

**Success Criteria**:
- Agents reach frontier with budget remaining
- Monitoring shows exploration budget usage

---

## 🔧 PHASE 3: FIX VALIDATION SYSTEM (Days 6-7)

### Problem Statement
4 games have <75% validation rate (ft09: 72.8%, lp85: 21.5%, ls20: 64.3%, sp80: 74.1%)

### Action Items

#### 3.1: Implement fuzzy frame matching

**Current**: Pixel-perfect comparison
**Target**: Allow small differences for dynamic elements

```python
def _compare_frames(self, frame1, frame2, tolerance=0.02):
    """
    Compare frames with tolerance for minor differences.
    
    Args:
        tolerance: Maximum fraction of different pixels allowed (0.02 = 2%)
    """
    if frame1 == frame2:
        return True
    
    # Calculate pixel difference
    diff_ratio = self._calculate_diff_ratio(frame1, frame2)
    return diff_ratio <= tolerance
```

#### 3.2: Add game-specific tolerance

Some games may have more dynamic elements:

```python
GAME_TOLERANCES = {
    'as66': 0.01,  # Low tolerance (static game)
    'vc33': 0.01,
    'ft09': 0.05,  # Higher tolerance (may have animations)
    'sp80': 0.05,
    'ls20': 0.05,
    'lp85': 0.10,  # Highest tolerance (most dynamic?)
}
```

#### 3.3: Track validation failure reasons

Add logging to identify WHY validations fail:
- Frame mismatch
- Action count exceeded
- Wrong level reached

**Success Criteria**:
- All games achieve >75% validation rate
- Failure reasons logged for analysis

---

## 🔧 PHASE 4: BALANCE AGENT ROLES (Week 2)

### Problem Statement
Only 26.8% exploration capacity (pioneers + partial generalists)

### Action Items

#### 4.1: Audit role assignment logic

Check `agent_operating_mode_system.py`:
- When are pioneers assigned?
- What triggers optimization mode?
- How is game state detected (exploration vs optimization)?

#### 4.2: Force pioneer ratio during exploration

```python
def assign_roles(self, agents, game_state):
    if game_state == 'EXPLORATION':
        # Game has no full win yet
        pioneer_target = 0.40  # 40% pioneers
        optimizer_target = 0.20
        generalist_target = 0.30
        exploiter_target = 0.10
    else:
        # Game has full win (optimization mode)
        pioneer_target = 0.0
        optimizer_target = 0.50
        generalist_target = 0.30
        exploiter_target = 0.20
```

#### 4.3: Ensure pioneers target unbeaten levels

Pioneers should ONLY work on:
- Games with no full win
- Levels with no proven sequence

**Success Criteria**:
- 40%+ exploration capacity during exploration phase
- Monitoring shows pioneers on frontier levels

---

## 📋 Questions for User

Before proceeding, please clarify:

### Critical Questions

1. **Win Condition**: What score/level = WIN for each game?
   - Assumed: Score 20.0 = full win
   - Need confirmation to set proper targets

2. **Budget Reduction**: Why was `max_total_actions` reduced from 7000 to 2000?
   - Was there a performance issue?
   - Can we restore to 7000?

3. **lp85 Game Type**: What is special about lp85?
   - 21.5% validation rate suggests fundamental issue
   - Does it have moving elements?
   - Should we approach it differently?

4. **Current Priorities**: Which is more important?
   - A) Fix existing 6 games first
   - B) Prepare for "hundreds of new games" (Phase 3 from ruleset)

### Informational Questions

5. **Baseline Performance**: What was performance before 257 generations of training?
   - Are we regressing or improving slowly?

6. **Leaderboard Details**: The competitor has:
   - Games Completed: 3
   - Levels: 27
   - Total Actions: 656
   - Which 3 games? What's their level distribution?

7. **Time Constraints**: Is there a deadline for the competition?

---

## 🚀 Recommended Immediate Actions

### If user approves, execute in order:

1. **TODAY**: Run Phase 0 (emergency sequence cleanup)
   - Delete lp85 sequences
   - Prune bloated sequences
   - Run tests to verify

2. **TOMORROW**: Start Phase 1 (fix sequence capture)
   - Modify `_capture_winning_sequence()`
   - Add capture validation

3. **DAY 3**: Phase 2 (fix budgets)
   - Increase max_total_actions
   - Add budget tracking

4. **DAY 4-5**: Phase 3 (fix validation)
   - Implement fuzzy matching
   - Add per-game tolerance

5. **WEEK 2**: Phase 4 (balance roles)
   - Audit role assignment
   - Force pioneer targets

---

## 📊 Success Metrics

### Short-term (1 week)
- [ ] Average bloat ratio < 5x
- [ ] All games validation rate > 70%
- [ ] Unit tests passing (currently 3 failures)

### Medium-term (2 weeks)
- [ ] At least 1 game reaches full win
- [ ] Best game reaches level 10+
- [ ] Action efficiency improves 50%

### Long-term (1 month)
- [ ] All 6 games achieve full wins
- [ ] Total actions competitive with leaderboard
- [ ] System ready for new games

---

**End of Implementation Plan**

Please review and let me know:
1. Answers to the questions above
2. Approval to proceed with Phase 0 (emergency cleanup)
3. Any modifications to the prioritization
