# ORPHANED SYSTEMS AUDIT
**Date**: February 3, 2026 (Updated - Final Wiring Complete)
**Status**: ALL ENGINES WIRED - Only context/table orphans remain

---

## Executive Summary

A comprehensive audit revealed significant architectural issues where sophisticated engines, context keys, and database tables exist but are **never used** in the actual execution path.

**Current Status** (after Feb 3 complete wiring session):
- **0 registered engines orphaned** (all 11 previously orphaned engines now wired)
- **~25 context keys** read by rungs but never set by anyone
- **131 database tables** defined in schema but never written to
- All critical engines like `action6_behavior`, `control_tracker`, and `valence_goals` now connected

---

## FIXED ITEMS (February 3, 2026)

### Engines NOW WIRED (11 total):
| Engine | Rung Created | Category | Priority |
|--------|--------------|----------|----------|
| `click_behavior` | ClickBehaviorLearningRung | exploitation | 60 |
| `control_tracker` | ControlTrackerRung | orientation | 8 |
| `belief_system` | BeliefSystemRung | hypothesis | 25 |
| `hypothesis_system` | HypothesisSystemRung | hypothesis | 27 |
| `trigger_sequences` | TriggerSequencesRung | exploitation | 43 |
| `symbolic_tracker` | SymbolicTrackerRung | hypothesis | 24 |
| `embedding_matcher` | EmbeddingMatcherRung | exploitation | 45 |
| `few_shot_relations` | FewShotRelationsRung | exploitation | 54 |
| `network_sharing` | NetworkSharingRung | exploitation | 50 |
| `primitive_suggester` | PrimitiveSuggesterRung | exploitation | 49 |
| `valence_goals` | ValenceGoalsRung | hypothesis | 35 |

### Context Keys - NOW POPULATED
Added to evolution_runner.py:
- `action_count` - number of actions taken this game
- `level_number` - current level
- `last_actions` - recent action history
- `player_position` - (x, y) tuple from game state
- `score` - current score
- `score_delta` - change from last action
- `last_outcome` - 'positive', 'negative', 'neutral'
- `frontier_mode` - True if no full game win exists
- `is_frontier` - alias for frontier_mode
- `is_novel_game` - True if first time playing this game
- `session_id`, `scorecard_id` - tracking IDs

---

## 1. ORPHANED ENGINES - ALL FIXED!

~~These engines are registered in `engines/registry.py` but **never accessed**:~~

**All 11 orphaned engines have been wired to the decision system!**

Note: `engine_name` shown in audit is just a comment in registry.py (line 53 says "# Format: 'engine_name': EngineConfig(...)") - not a real engine.

### Previously Orphaned - NOW WIRED:
- ~~**belief_system**~~ - BeliefSystemRung (priority 25)
- ~~**click_behavior**~~ - ClickBehaviorLearningRung (priority 60)
- ~~**control_tracker**~~ - ControlTrackerRung (priority 8)
- ~~**embedding_matcher**~~ - EmbeddingMatcherRung (priority 45)
- ~~**few_shot_relations**~~ - FewShotRelationsRung (priority 54)
- ~~**hypothesis_system**~~ - HypothesisSystemRung (priority 27)
- ~~**network_sharing**~~ - NetworkSharingRung (priority 50)
- ~~**primitive_suggester**~~ - PrimitiveSuggesterRung (priority 49)
- ~~**symbolic_tracker**~~ - SymbolicTrackerRung (priority 24)
- ~~**trigger_sequences**~~ - TriggerSequencesRung (priority 43)
- ~~**valence_goals**~~ - ValenceGoalsRung (priority 35)

---

## 2. ORPHANED CONTEXT KEYS (Reduced from 35)

These keys are read by rungs via `context.get('key')` but **nobody ever sets them**:

### FIXED - Now populated in evolution_runner.py
- ~~`available_actions`~~ - already was set
- ~~`frontier_mode`~~ - NOW SET
- ~~`last_action`~~ - check if part of `last_actions`
- ~~`position`~~ - via `player_position`
- ~~`score_delta`~~ - NOW SET

### Still Orphaned (High-Priority)

| Key | Read By | Should Be Set By |
|-----|---------|------------------|
| `active_sequence` | MultiStageMatchingRung, AssumptionFormationRung | Sequence tracking system |

### Medium-Priority (Single rung usage)

| Key | Should Be Set By |
|-----|------------------|
| `completion_prediction` | CompletionPredictionRung (self-reference?) |
| `cull_distance` | Game geometry analyzer |
| `deliberation_result` | DeliberationEngine |
| `failed_actions` | Failure tracking |
| `frame_change` | Frame diff system |
| `game_state_mode` | Game state manager |
| `last_discovery` | Discovery engine |
| `nearby_objects` | Object detection |
| `next_sequence_action` | Sequence system |
| `replay_mode` | Replay system |
| `sequence_position` | Sequence tracking |
| `stream_a_proposals` | Two-streams system |
| `stream_b_proposals` | Two-streams system |

---

## 3. ORPHANED DATABASE TABLES (131 total)

Tables defined in `complete_database_schema.sql` with **no INSERT or UPDATE** statements found:

### CRITICAL - Should Have Data

| Table | Purpose | Fix Priority |
|-------|---------|--------------|
| `world_model_states` | World model snapshots | HIGH - self model needs this |
| `self_object_identity` | "I am this object" tracking | HIGH - agent identity |
| `control_transfer_events` | Control changes | HIGH - self model |
| `object_property_snapshots` | Object state history | MEDIUM |
| `detected_objects` | Object detection results | MEDIUM |
| `collision_events` | Collision tracking | MEDIUM |
| `movement_patterns` | Movement learning | MEDIUM |

### MEDIUM PRIORITY

| Table | Purpose |
|-------|---------|
| `attention_windows` | Attention tracking |
| `causal_chains` | Causal reasoning |
| `consciousness_logs` | Consciousness state |
| `hypothesis_validations` | Hypothesis testing |
| `inferred_beliefs` | Belief inference |
| `inferred_goal_states` | Goal inference |
| `metacognitive_questions` | Q1-Q8 tracking |

### LOW PRIORITY (CODS leftovers, deprecated)

| Table | Note |
|-------|------|
| `cods_*` tables (5) | CODS deprecated Jan 2026 |
| `oracle_*` tables (3) | Part of deprecated CODS |
| `composed_operators` | CODS composer |
| `primitive_unlock_attempts` | CODS unlock |

---

## 4. SPECIFIC ISSUES BY SYSTEM

### A. ACTION6/Click System - PARTIALLY FIXED

**Status**: Improved but incomplete

**What Works**:
- `GridExplorationRung` exists and calls `get_grid_exploration_targets()`
- `visual_analyzer.get_grid_exploration_targets()` exists
- `Action6ObjectExplorationRung` added (Feb 3, 2026)
- `evolution_runner.py` now extracts `grid_target` from metadata

**What's Still Broken**:
- `click_behavior` engine NOT connected
- `get_click_targets_for_level()` NEVER called
- No feedback loop to learn which clicks work

**Fix Required**:
1. Create `ClickBehaviorRung` that uses `click_behavior` engine
2. Call `save_pseudo_button_behavior()` after click outcomes
3. Use `classify_pseudo_button_effects()` for learning

### B. Self-Model System - PARTIALLY CONNECTED

**Status**: Core connected, details orphaned

**What Works**:
- `self_model` (CognitiveCore) is used
- `get_embedding_suggested_action()` called

**What's Broken**:
- `control_tracker` - never used
- `world_model_states` table - never written
- `self_object_identity` table - never written
- Agent doesn't track "I control object X"

### C. Hypothesis System - MIXED

**What Works**:
- `scientific_method_engine` connected
- `agent_theories` table written

**What's Broken**:
- `hypothesis_system` engine orphaned
- `hypothesis_validations` table never written
- Theories aren't properly validated

### D. Context Population - INCOMPLETE

Many rungs expect context keys that are never populated:

```
Rung reads context.get('frontier_mode')
  -> Nobody sets context['frontier_mode']
  -> Rung always gets None/default
  -> Rung logic never triggers
```

---

## 5. FIX PRIORITY LIST

### CRITICAL (Fix Now)

1. **Wire `action6_behavior` learning loop**
   - After ACTION6 outcome, call `save_pseudo_button_behavior()`
   - Use learned behaviors in future decisions

2. **Populate `last_action` in context**
   - Add to `ContextBuilder` or `evolution_runner.py`
   - Multiple rungs need this for learning

3. **Wire `control_tracker` engine**
   - Create `SelfModelControlRung`
   - Track "I am this object" identity

### HIGH (Fix This Week)

4. **Connect `click_behavior` engine**
   - Create ClickBehaviorRung
   - Use for click pattern learning

5. **Populate `frontier_mode` context key**
   - Set based on game state (exploring vs optimizing)

6. **Wire `hypothesis_system` engine**
   - Connect to rungs for hypothesis validation

### MEDIUM (Fix Soon)

7. Write to `world_model_states` table
8. Connect `belief_system` engine
9. Wire `symbolic_tracker` engine
10. Populate stream_a/stream_b proposal keys

### LOW (Eventually)

- Clean up unused CODS tables (deprecate in schema)
- Remove `engine_name` from registry (appears to be error)
- Document intentionally unused tables

---

## 6. ARCHITECTURE LESSON

**Problem Pattern**: "Build it and they will come"

The codebase has extensive infrastructure:
- 35 engines registered
- 272 database tables
- 52+ rungs

But the **wiring** between components is incomplete. Engines exist but aren't accessed. Tables exist but aren't written. Rungs exist but depend on context keys nobody sets.

**Solution Pattern**: "Wire before you build"

1. Before adding new engines: verify they're called
2. Before adding new tables: verify something writes to them
3. Before adding context.get() calls: verify something sets the key
4. Audit regularly with `audit_orphaned_systems.py`

---

## 7. VERIFICATION

Run audit script to verify fixes:
```bash
python manual_tools/audit_orphaned_systems.py
```

Target metrics:
- Orphaned engines: 0 (currently 12)
- Orphaned context keys: <10 (currently 35)
- Critical orphaned tables: 0 (currently ~20)

---

## Appendix: Full Orphan Lists

### All Orphaned Engines
```
belief_system
click_behavior
control_tracker
embedding_matcher
engine_name
few_shot_relations
hypothesis_system
network_sharing
primitive_suggester
symbolic_tracker
trigger_sequences
valence_goals
```

### All Orphaned Context Keys
```
active_sequence, available_actions, completion_prediction, cull_distance,
deliberation_result, failed_actions, fallback_strategy, frame_change,
frame_changed, frontier_mode, game_state_mode, is_novel_game, is_replay,
last_action, last_actions, last_discovery, last_outcome, level_number,
nearby_objects, next_sequence_action, optimization_mode, player_position,
player_properties, position, recent_stuck_count, replay_mode, score_delta,
scorecard_id, sequence_position, session_id, stream_a_proposals,
stream_b_proposals, surprise_score, template_position, tried_colors
```

### Critical Orphaned Tables
```
world_model_states, self_object_identity, control_transfer_events,
control_transfer_patterns, object_property_snapshots, detected_objects,
collision_events, movement_patterns, attention_windows, causal_chains
```

---

**Last Updated**: February 3, 2026
**Author**: Automated Audit + Manual Analysis
