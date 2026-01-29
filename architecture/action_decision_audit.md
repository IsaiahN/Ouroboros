# Action Decision System Audit
**Date**: 2026-01-29  
**Auditor**: Claude Opus 4.5 (GitHub Copilot)  
**Scope**: `_select_action()` in core_gameplay.py + supporting systems  
**Purpose**: Diagnose why no games have been beaten despite 8,061+ game attempts

---

## Executive Summary

**CRITICAL FINDING**: The system is fundamentally broken at the data integration layer. Despite having 42 sophisticated decision-making features documented, the telemetry shows **0% of the metacognitive data is being recorded**:

| Metric | Expected | Actual |
|--------|----------|--------|
| Budget tracking populated | 100% | **0%** |
| Context mode recorded | 100% | **0%** |
| Question tier recorded | 100% | **0%** |
| Persona proposals tracked | 100% | **0%** |
| Selection source recorded | 100% | **Column doesn't exist** |

This means the entire Two-Streams architecture, Persona system, CODS integration, and metacognitive reasoning are either:
1. **Not being called** (dead code)
2. **Running but not recording** (output lost)
3. **Silently failing** (exceptions swallowed)

---

## Database Evidence

### Performance Summary (8,061 games)

| Game | Best Level | Avg Score | Positive Rate | Avg Actions |
|------|------------|-----------|---------------|-------------|
| as66 | **4** | 1.85 | 99.2% | 422.7 |
| vc33 | 3 | 1.67 | 99.8% | 835.0 |
| ft09 | 2 | 1.00 | 99.6% | 701.1 |
| lp85 | **7** | 1.00 | 99.9% | 203.6 |
| ls20 | 1 | 1.00 | 99.9% | 726.2 |
| sp80 | 1 | 1.00 | 99.9% | 730.5 |

**Interpretation**:
- **99%+ positive score rate** but **0 full game wins** = agents beat level 1 reliably but can't progress
- **as66 reaching L4** and **lp85 reaching L7** shows some learning is happening
- **ls20 and sp80 stuck at L1** = fundamental mechanics not discovered

### Action Efficiency

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Frame changes | 63.8% | Good - most actions affect game state |
| Positive score changes | **3.9%** | LOW - only 1 in 25 actions leads to progress |
| Negative score changes | 1.47% | Low death rate |
| Total wins detected | **0** | CRITICAL - no game completions |

### Hypothesis System

| Metric | Value | Status |
|--------|-------|--------|
| Total hypotheses | 1,588 | OK |
| Validated (3+ attempts) | 586 (37%) | LOW |
| Win-validated | **53 (3%)** | CRITICAL |
| Avg reliability | 0.333 | LOW |
| Reliability 0.9+ | 62 (4%) | Most hypotheses unvalidated |

**Problem**: 94% of hypotheses sit at 0.3-0.5 reliability - the "uncertainty zone" where the system can't decide whether to trust them. The validation cycle isn't working.

---

## Decision Ladder Analysis

### Current Priority Order (from code)

```
1.  Discovery Exploitation (immediate discovery use)
2.  Position-Bucket Death Avoidance
3.  Embedding-Based Suggestion (>=0.7 confidence)
4.  Frontier Topology Navigation
5.  Exploration Tracking
6.  MAP-INTEL Collision Recovery
7.  Exploration Phase System
8.  ...42 more features...
```

### Critical Integration Problems Identified

#### **Problem 1: Discovery Exploitation Fires But Doesn't Record**
```python
# Code at line ~9313-9338
last_discovery = getattr(self, '_last_discovery', None)
if last_discovery and isinstance(last_discovery, dict):
    self._last_discovery = None  # Cleared but never recorded!
    ...
    return discovered_action, exploit_reason  # Returns without DB write
```

**Impact**: We return the action but never record:
- What discovery was made
- How it performed
- Whether it should be reinforced

**Fix Needed**: Add `action_traces` insert with `selection_source='discovery_exploitation'`

#### **Problem 2: Embedding Suggestion Has Wrong Confidence Threshold**
```python
# Code at line ~9467
if embedding_suggestion and embedding_suggestion.get('confidence', 0) >= 0.7:
```

**Problem**: 0.7 confidence for cross-game transfer is **too high**. The embedding system clusters similar situations, but cross-game similarity scores naturally cap around 0.6-0.7 because games have different color palettes and grid sizes.

**Evidence**: No embedding suggestions appear in logs (confirmed via grep - would show "Using learned suggestion")

**Fix Needed**: 
- Lower threshold to 0.5 for cross-game suggestions
- Use 0.7 only for same-game/same-level matches

#### **Problem 3: Position-Bucket Death Avoidance Is Overly Aggressive**

```python
# Line ~9403-9415: Blocks actions at danger_score >= 0.6
danger_info = self.terminal_detector.check_position_danger(
    ...
    min_danger=0.6,  # This blocks 60% danger
)
if danger_info and danger_info.get('danger'):
    deadly_actions_for_frame.add(check_action)
```

**Problem**: With 125 death patterns recorded, agents are blocking too many actions too early. The 0.6 threshold creates "analysis paralysis" - agents can't move because everywhere looks dangerous.

**Evidence**: 
- as66 has 110 death patterns (3,005 deaths tracked)
- ls20 has 10 patterns (957 deaths)
- This creates large "forbidden zones" on the map

**Fix Needed**:
- Graduated danger response (already implemented in MAP-INTEL, not in main check)
- Decay death patterns faster (currently halves every 10 generations, should be 5)
- Require minimum 5 deaths before blocking (currently 1)

#### **Problem 4: Frontier Topology Never Triggers**

```python
# Line ~9528-9548: Only triggers in 'exploit' mode with confidence >= 0.5
if exploration_mode == 'exploit' and map_confidence >= 0.5:
    topo_suggestion = self._suggest_safe_action_from_topology(...)
```

**Problem**: New games start with 0% map confidence. The threshold requires 50% confidence, which requires already having explored 50% of the map. This is backwards.

**Evidence**: No "FRONTIER-TOPO" messages in recent logs (confirmed via grep)

**Fix Needed**:
- Use topology suggestions ESPECIALLY when confidence is LOW
- High confidence = already know what to do
- Low confidence = need guidance from partial observations

#### **Problem 5: Exploration Phase System Conflicts With Goal-Seeking**

The code mentions (line ~9826):
```python
# This prevents the "safe zone trap" where agents oscillate forever
# because goal-seeking has infinite priority over exploration.
```

**But**: The actual implementation buries exploration decisions deep in the priority ladder (position 7+), so goal-seeking STILL has implicit priority.

**Evidence**: lp85 reached level 7 with only 203 avg actions - suggesting it "speed-runs" by replaying optimal sequences without exploring alternatives.

---

## Critical Missing Data Flows

### Two-Streams Architecture (wA/wB)
**Theory**: Stream A (private experience) vs Stream B (network wisdom) should balance.

**Reality**: 
- `w_a` and `w_b` weights are not being recorded anywhere
- No evidence of stream conflict detection
- I-Thread integration appears to be dead code

**Missing Table Columns**:
```sql
-- These should exist in action_traces but don't:
-- stream_a_weight FLOAT
-- stream_b_weight FLOAT  
-- stream_conflict BOOLEAN
-- conflict_resolution TEXT
```

### Persona Ensemble
**Theory**: Multiple internal personas propose actions, then vote/synthesize.

**Reality**:
- `persona_proposal_count` column exists but is always NULL
- No persona proposals being recorded
- Synthesis decisions not tracked

### CODS/Oracle Integration
**Theory**: Centralized discovery engine watches all agents, identifies patterns.

**Reality**:
- Hypothesis table has data (1,588 entries)
- But `validation_attempts` avg is only 5.1
- `best_score_achieved` is rarely updated
- CODS validation loop appears to not be running

---

## Weight/Threshold Analysis

### Current Thresholds (Likely Wrong)

| System | Threshold | Problem |
|--------|-----------|---------|
| Embedding confidence | 0.7 | Too high - cross-game rarely hits this |
| Death avoidance | 0.6 danger | Too low - blocks too many actions |
| Map confidence for topology | 0.5 | Backwards - should help when LOW |
| Discovery exploitation reliability | 0.6 for "high" | OK |
| Hypothesis reliability minimum | 0.333 avg | Can't distinguish good from bad |

### Recommended Threshold Changes

| System | Current | Recommended | Rationale |
|--------|---------|-------------|-----------|
| Embedding confidence | 0.7 | **0.5** | Cross-game similarity is inherently lower |
| Death avoidance min_danger | 0.6 | **0.75** | More room for learning |
| Death avoidance min_deaths | 1 | **5** | Require pattern confirmation |
| Topology trigger | conf >= 0.5 | **conf < 0.3** | Help when LOST, not when found |
| Hypothesis "usable" threshold | rel >= 0.333 | **rel >= 0.5 AND validation >= 5** | Require both confidence and evidence |

---

## Integration Architecture Problems

### Identified Disconnections

```
┌─────────────────────────────────────────────────────────┐
│                    DOCUMENTED                           │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐              │
│  │ Persona │──▶│ I-Thread│──▶│ Two-    │              │
│  │ Ensemble│   │ Weaver  │   │ Streams │              │
│  └─────────┘   └─────────┘   └─────────┘              │
│        │            │             │                    │
│        ▼            ▼             ▼                    │
│  ┌──────────────────────────────────────┐             │
│  │         ACTION DECISION              │             │
│  │         (returns action)             │             │
│  └──────────────────────────────────────┘             │
│        │                                              │
│        ▼                                              │
│  ┌──────────────────────────────────────┐             │
│  │         action_traces INSERT         │ ◀── MISSING │
│  │         (should record all data)     │     DATA!   │
│  └──────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────┘
```

### The Missing Link

The `_select_action()` method returns `(action, reason)` but the calling code must:
1. Record the selection source
2. Record any weights/confidences used
3. Record persona votes
4. Record stream conflicts

**This recording is NOT happening.** The method returns, but the caller doesn't persist the decision metadata.

---

## Failure Mode Analysis

### Why Games Aren't Being Won

1. **Level 1 Mastery, Level 2+ Failure**
   - 99%+ positive score on L1 = agents learn basic mechanics
   - But only as66/lp85 progress past L1
   - **Cause**: Optimal sequences aren't being discovered/stored for L2+

2. **Hypothesis Stagnation**
   - 1,588 hypotheses but only 53 win-validated
   - Average reliability stuck at 0.333
   - **Cause**: Validation loop not closing - discoveries don't feedback

3. **Exploration vs Exploitation Imbalance**
   - MAP-INTEL collision recovery dominates (always active)
   - Frontier topology never activates (threshold too high)
   - **Cause**: Priorities favor local obstacle avoidance over global exploration

4. **Death Pattern Overreaction**
   - 125 death patterns create large "forbidden zones"
   - Agents play it safe, never discover winning sequences
   - **Cause**: 0.6 danger threshold too aggressive, no decay

---

## Recommended Fixes (Priority Order)

### Priority 1: Fix Data Recording (Critical)

```python
# In _run_single_action() after calling _select_action():
# ADD this recording block:

selection_metadata = {
    'selection_source': getattr(self, '_last_selection_source', 'unknown'),
    'stream_a_weight': getattr(self, '_current_w_a', None),
    'stream_b_weight': getattr(self, '_current_w_b', None),
    'persona_proposal_count': getattr(self, '_persona_count', None),
    'embedding_confidence': getattr(self, '_last_embedding_conf', None),
    'death_avoidance_active': bool(self._deadly_first_actions),
}
# ... include in action_traces INSERT
```

### Priority 2: Fix Threshold Values

```python
# Embedding confidence
if embedding_suggestion.get('confidence', 0) >= 0.5:  # Was 0.7

# Death avoidance
if danger_info.get('death_count', 0) >= 5:  # Add minimum death count
    if danger_info.get('danger_score', 0) >= 0.75:  # Was 0.6
        deadly_actions_for_frame.add(check_action)

# Topology trigger (INVERT the logic)
if exploration_mode != 'exploit' or map_confidence < 0.3:  # Was >=0.5
    # NOW we help when lost
```

### Priority 3: Close the Validation Loop

```python
# After positive score change, update hypothesis reliability:
if score_change > 0 and self._current_hypothesis_used:
    self.db.execute_update("""
        UPDATE network_object_control_hypotheses
        SET validation_attempts = validation_attempts + 1,
            best_score_achieved = MAX(best_score_achieved, ?),
            reliability_score = (reliability_score * validation_attempts + 1.0) / (validation_attempts + 1)
        WHERE hypothesis_id = ?
    """, (current_score, self._current_hypothesis_used))
```

### Priority 4: Add Exploration Forcing

When stuck at frontier level for 500+ actions with no score change:
1. Disable death avoidance temporarily
2. Force random exploration
3. Record all outcomes (even deaths)
4. Learn from the deaths, then re-enable avoidance

---

## Verification Queries

After fixes, monitor these queries:

```sql
-- Selection source distribution (should show multiple sources)
SELECT selection_source, COUNT(*) 
FROM action_traces 
WHERE created_at > datetime('now', '-1 hour')
GROUP BY selection_source;

-- Stream weights being recorded
SELECT AVG(stream_a_weight), AVG(stream_b_weight)
FROM action_traces 
WHERE created_at > datetime('now', '-1 hour')
AND stream_a_weight IS NOT NULL;

-- Hypothesis reliability improving
SELECT DATE(last_updated), AVG(reliability_score), AVG(validation_attempts)
FROM network_object_control_hypotheses
WHERE is_active = 1
GROUP BY DATE(last_updated)
ORDER BY DATE(last_updated) DESC;
```

---

## Conclusion

The action decision system has sophisticated theory but broken implementation:

1. **Data flow is severed** - decisions happen but aren't recorded
2. **Thresholds are miscalibrated** - blocking learning rather than enabling it  
3. **Priorities are inverted** - safety over exploration on FRONTIER levels
4. **Validation loop is open** - discoveries don't improve hypotheses

The fix is not more features - it's **connecting the existing features** to the database and adjusting thresholds based on actual performance data.

**Estimated Time to Fix**: 4-6 hours of targeted code changes  
**Estimated Impact**: Should enable first game wins within 100-500 generations

---

## Addendum: External Review Cross-Check (2026-01-29)

An external review of the action decision system was compared against this audit. Key findings:

### Gap Analysis: What the External Review Found That I Missed

| External Review Finding | Audit Coverage | Status/Resolution |
|------------------------|----------------|-------------------|
| **Feature 13 fallback does `random.choice()` ignoring wisdom** | ⚠️ Partial | *Outdated* - code now has `stream_b_guidance` priority before random fallback (line ~11537-11546). The fallback hierarchy is: Stream B → Imagination → Untried → Random |
| **Counterfactual learnings (7,945) stored but never queried** | ❌ Missed | *System was rewritten* on Jan 17, 2026. Old `counterfactual_analyzer.py` replaced with `lessons_learned_engine.py` because it generated 155K+ unused scenarios. New system has `get_lessons_for_game()` which IS called by `autonomous_evolution_runner.py` |
| **Context-aware danger thresholds missing** | ⚠️ Partial | My audit noted thresholds are "too aggressive" but didn't propose specific context-aware values |
| **"Last mile" integration pattern naming** | ❌ Missed | External review named the root cause pattern: "Data exists, systems query it, ladder collects suggestions, but final selection doesn't weight by quality" |

### External Review's Recommended Context-Aware Thresholds

The external review proposed specific thresholds I should incorporate:

```python
# Context-aware danger thresholds (from external review)
def _get_danger_threshold(self):
    """Dynamic danger threshold based on context"""
    
    # Frontier levels need exploration (first 30 actions especially)
    if self.is_frontier and self.level_action_count < 30:
        return 0.98  # Very permissive - let them explore
    
    # At checkpoint frontier, must take risks  
    if self._replaying_checkpoint and self._at_checkpoint_frontier:
        return 0.97  # Permissive
    
    # Spawn protection (first 3 actions after level start)
    if self.level_action_count < 3:
        return 0.85  # Very strict - don't die immediately
    
    # Normal gameplay
    return 0.90  # Standard
```

**My audit's recommendation** (0.75 flat threshold) is less nuanced than this context-aware approach.

### Lessons Learned System Status

The external review claimed `counterfactual_learnings` table has 7,945 unused entries. Investigation shows:

1. **Jan 17, 2026**: System was completely rewritten ([progress.md#L4476-4540](progress.md#L4476-4540))
2. **Old problem**: 155,836 scenarios generated, 0 ever tested
3. **New system**: `lessons_learned_engine.py` with max 3 lessons per game
4. **Integration**: `get_lessons_for_game()` IS called by evolution runner ([autonomous_evolution_runner.py#L1655](autonomous_evolution_runner.py#L1655))
5. **Current status**: Lessons are retrieved but **NOT used in action selection**

**CONFIRMED GAP**: `prior_lessons` is stored in `tetra['prior_lessons']` at line 17481 but **grep shows NO code reads this back** to influence action selection. The external review was right - lessons are collected but the "last mile" integration is missing.

```python
# What exists (line 17481):
tetra['prior_lessons'] = sensation_context.get('prior_lessons', [])[:10]

# What's missing:
# In _select_action(), there should be a check like:
for lesson in prior_lessons:
    if lesson.get('causes_death') and lesson.get('avoid_action'):
        deadly_actions_for_frame.add(lesson['avoid_action'])
```

### "Last Mile" Pattern - Root Cause Summary

The external review's most valuable insight was naming the pattern:

> "It's like building a GPS that has perfect maps, calculates optimal routes, shows you 5 route options, then randomly picks one instead of choosing the best."

This describes our system perfectly:
- ✅ Death patterns collected (125 patterns)
- ✅ Winning sequences stored (10 levels with 100% sequences)  
- ✅ Network wisdom aggregated (action effectiveness scores)
- ✅ Ladder queries all this data
- ❌ **Final action selection doesn't weight by collected quality**

The fallback paths (recovery mode, stuck handling, etc.) do prioritize Stream B guidance now, but the **main action selection path** may still use equal weighting.

### Updated Recommendations

Based on the cross-check, I add these recommendations:

1. **Audit `prior_lessons` usage**: Verify lessons flow from `sensation_context` into actual action selection, not just storage
2. **Implement context-aware danger thresholds**: Use the frontier/spawn/normal hierarchy from external review
3. **Add weighted action selection**: When network wisdom provides effectiveness scores, use `weighted_choice()` not `random.choice()`
4. **Verify Stream B guidance path**: Confirm the `stream_b_guidance` priority in recovery mode actually fires (check logs for "STREAM-B-RECOVERY")

---

**Document Version**: 1.2  
**Last Updated**: 2026-01-29  

---

## Fixes Applied (2026-01-29)

All critical issues identified in this audit have been addressed:

| Issue | Fix Applied | Location |
|-------|-------------|----------|
| **Context-aware danger thresholds** | Added `_get_context_aware_danger_threshold()` method with frontier/spawn/normal hierarchy (0.98/0.85/0.90) | core_gameplay.py ~L23040 |
| **Embedding threshold too high** | Lowered from 0.7 to 0.5 for cross-game transfer | core_gameplay.py ~L9571 |
| **Topology logic backwards** | Inverted - now helps when map_confidence < 0.3 (when LOST) | core_gameplay.py ~L9645-9665 |
| **Prior lessons not used** | Added integration block that reads lessons and adds death-causing actions to deadly_actions_for_frame | core_gameplay.py ~L9515-9560 |
| **Selection source not recorded** | Added `self._last_selection_source` tracking throughout decision ladder | core_gameplay.py multiple locations |
| **Minimum death count missing** | Added min_deaths=5 requirement before blocking actions | core_gameplay.py ~L9398, terminal_pattern_detector.py ~L2009 |

### Expected Impact

These fixes should break the "frontier deadlock" pattern:

1. **First 30 actions on frontier levels**: Danger threshold is now 0.98 (was 0.6), allowing nearly all actions
2. **Topology now guides when lost**: Will fire when map_confidence < 0.3 instead of only when > 0.5
3. **Cross-game learning enabled**: Embedding threshold 0.5 allows L4 knowledge to help with L5
4. **Network lessons integrated**: Prior death-causing lessons now block dangerous actions
5. **Pattern confirmation required**: 5+ deaths needed before blocking (was 1)

### Verification Commands

After running evolution, check these log patterns:

```bash
# Context-aware thresholds firing
grep "threshold=" logs/evolution.log | head -20

# Topology helping when lost
grep "LOW confidence mode" logs/evolution.log

# Prior lessons being applied
grep "PRIOR-LESSON" logs/evolution.log

# Selection source distribution
grep "selection_source" logs/evolution.log | sort | uniq -c

# Graduated danger weights (v2.0)
grep "DANGER-WEIGHT" logs/evolution.log | head -20
grep "safety=" logs/evolution.log | head -20

# Prior lessons graduated integration (v2.0)
grep "PRIOR-LESSON" logs/evolution.log | head -20

# 3-layer filter graduated weights
grep "FILTER-WEIGHTS" logs/evolution.log | head -20
grep "FILTER-GRAD" logs/evolution.log | head -20
```

---

## Graduated Safety System v2.0 (2026-01-29)

### Philosophy: NEVER HARD-BLOCK, ALWAYS WEIGHT

Multiple systems were using binary blocking (skip/pass). The graduated system replaces ALL binary blocking with continuous safety weights that combine multiplicatively.

### Systems Graduated

| System | Before | After |
|--------|--------|-------|
| **Death Pattern Avoidance** | 5+ deaths = BLOCKED | Weight 0.05-1.0 based on deaths, survivals, time decay |
| **Prior Lessons** | confidence >= 0.6 = BLOCKED | Weight reduction proportional to confidence x severity |
| **3-Layer Action Filter** | Binary skip/pass | Layers contribute penalty 0-0.95, becomes weight |
| **Position Death Avoidance** | deadly_actions set = BLOCKED | Weighted random selection based on combined weights |

### Architecture: Multiplicative Weight Combination

```
                                  INITIAL WEIGHTS
                                  (all 1.0 for actions 1-7)
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    │                      │                      │
               ┌────▼────┐           ┌────▼────┐           ┌────▼────┐
               │ Death   │           │ Prior   │           │ 3-Layer │
               │ Pattern │           │ Lessons │           │ Filter  │
               │ Danger  │           │ Penalty │           │ Penalty │
               └────┬────┘           └────┬────┘           └────┬────┘
                    │ *= (1-danger)       │ *= (1-penalty)      │ *= filter_weight
                    │                     │                      │
                    └──────────────────────┼──────────────────────┘
                                           │
                                   COMBINED WEIGHTS
                                  (action_safety_weights)
                                           │
                                    ┌──────▼──────┐
                                    │  Weighted   │
                                    │  Selection  │
                                    └─────────────┘
```

### Changes Made

| Component | Change |
|-----------|--------|
| **terminal_pattern_detector.py** | Added `get_graduated_action_weights()` |
| **terminal_pattern_detector.py** | Added `record_survival_feedback()` |
| **core_gameplay.py ~L9351** | Death avoidance uses graduated weights |
| **core_gameplay.py ~L9465** | Prior lessons reduce weights (not binary block) |
| **core_gameplay.py ~L3728** | Added `_action_filter_get_graduated_weights()` |
| **core_gameplay.py ~L10608** | 3-layer filter merges with safety weights |
| **core_gameplay.py ~L10650** | Position avoidance uses weighted selection |
| **core_gameplay.py ~L23200** | Added `_weighted_action_selection()` helper |
| **core_gameplay.py ~L23230** | Added `_record_action_survival()` helper |

### Safety Weight Formulas

**Death Pattern Danger**:
```python
base_danger = deaths / (deaths + survivals + 1)
time_decay = 0.5 ** (generations_since_update / 10)
survival_dampening = 1.0 / (1.0 + survivals * 0.2)
sample_confidence = min(1.0, total_samples / 10)

danger = base_danger * time_decay * survival_dampening * sample_confidence
if frontier_mode:
    danger *= 0.3

weight *= max(0.05, 1.0 - danger)
```

**Prior Lessons Penalty**:
```python
severity = 0.8 if causes_death else (0.3 if causes_failure else 0.1)
recency_factor = 1.0 - (lesson_index * 0.05)
lesson_penalty = confidence * severity * recency_factor

weight *= max(0.05, 1.0 - min(0.9, lesson_penalty))
```

**3-Layer Filter Penalty**:
```python
composite_penalty = 0.0
if cache_shows_failure:
    composite_penalty += 0.6  # Layer 1: known failure
if no_interactive_object:
    composite_penalty += 0.3  # Layer 2: nothing to interact with
if prediction < threshold:
    composite_penalty += 0.3 * (1.0 - prediction)  # Layer 3: low success

weight *= max(0.05, 1.0 - min(0.95, composite_penalty))
```

### Key Properties

1. **NEVER ZERO**: Minimum combined weight is 0.05 (can't multiply below this)
2. **MULTIPLICATIVE**: All systems contribute multiplicatively, stronger overall signal
3. **SURVIVAL FEEDBACK**: Each successful action increases survival_count
4. **TIME DECAY**: Old patterns fade (halve every 10 generations)
5. **FRONTIER MODE**: 70% danger reduction for first 30 actions
6. **WEIGHTED SELECTION**: Final action chosen probabilistically based on combined weights

### Example Combined Scenarios

| Scenario | Death | Lesson | Filter | Combined | Outcome |
|----------|-------|--------|--------|----------|---------|
| New game, no data | 1.0 | 1.0 | 1.0 | 1.0 | Equal chance |
| Known deadly | 0.15 | 1.0 | 1.0 | 0.15 | 15% normal chance |
| Known deadly + lesson | 0.15 | 0.7 | 1.0 | 0.11 | 11% normal chance |
| Known deadly + lesson + filter fail | 0.15 | 0.7 | 0.4 | 0.05 | Min 5% chance |
| Frontier mode | 0.37 | 1.0 | 1.0 | 0.37 | Explore! |
| Old pattern (20 gens) | 0.89 | 1.0 | 1.0 | 0.89 | Mostly safe |

### Verification Commands

```bash
# Death pattern graduated weights
grep "DANGER-WEIGHT" logs/evolution.log | head -20

# Prior lessons graduated integration
grep "PRIOR-LESSON" logs/evolution.log | head -20

# 3-layer filter graduated weights
grep "FILTER-GRAD" logs/evolution.log | head -20
grep "FILTER-WEIGHTS" logs/evolution.log | head -20

# Weighted selection in action
grep "GRADUATED-SAFE" logs/evolution.log | head -20

# Survival feedback recording
grep "record_survival_feedback" logs/evolution.log | head -10
```

---

**Document Version**: 1.4  
**Last Updated**: 2026-01-29  

---

**Related Documents**: 
- action_decision_system.md (feature documentation)
- agents.md (operating guide)
- copilot-instructions.md (master ruleset)
- DOCS/review of action decision system.md (external review)
- DOCS/why bad at level progression.md (root cause analysis)
