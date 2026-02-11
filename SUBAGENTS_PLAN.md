# SUBAGENTS EXECUTION PLAN
**Generated**: 2026-02-10
**Based on**: Copilot Instructions v3.0 + Full Codebase Audit
**Purpose**: Actionable subagent task breakdown to close all remaining gaps

---

## CURRENT STATE SUMMARY

| Phase | Tasks | Done | Partial | Not Done |
|-------|-------|------|---------|----------|
| Phase 0 (Heal Wiring) | 4 | 3 | 1 | 0 |
| Phase 1 (Feedback Loops) | 4 | 4 | 0 | 0 |
| Phase 2 (Compression) | 4 | 4 | 0 | 0 |
| Phase 3 (Resonance) | 4 | 3 | 1 | 0 |
| Phase 4 (Decompose) | 3 | 2 | 1 | 0 |
| Phase 5 (Self-Tuning) | 4 | 1 | 0 | 3 unknown |
| Phase 6 (Health) | 3 | 3 | 0 | 0 |
| **Part 7 Cognitive** | **5** | **0** | **3** | **2** |
| **TOTAL** | **31** | **20** | **5** | **5+** |

### Critical Remaining Gaps (Priority Order)
1. **Part 7 Cognitive Capabilities** — The most impactful work. Without these, the system cannot learn from games.
2. **Phase 0.2** — Epistemic signals may still be synthetic
3. **Phase 3.1** — `record_resonance_pattern()` write path missing from main loop
4. **Phase 4.3** — Two game-playing paths not unified
5. **Phase 5.1/5.2/5.4** — Self-tuning unknowns (may be done, need verification)
6. **Copilot Instructions Update** — Document is stale, many facts wrong

---

## EXECUTION PRIORITY

The subagents are ordered by **impact on alignment velocity** (levels_completed / actions_taken):

```
Priority 1: WIRE THE BRAIN (Part 7) — Without cognitive capabilities, 0 levels completed
Priority 2: VERIFY & FIX REMAINING PHASE GAPS — Ensure foundation is solid
Priority 3: SELF-TUNING VERIFICATION — Determine if Phase 5 items are done
Priority 4: UPDATE DOCUMENTATION — Keep copilot-instructions accurate
```

---

## SUBAGENT 1: Wire Persistent World Model into Context
**Priority**: P0 (Highest — blocks all cognitive progress)
**Estimated Effort**: Large
**Dependencies**: None
**Theory Alignment**: Seal 2 (Amnesia) — knowledge built but lost every action

### Problem
`SymbolicReasoningEngine` in `engines/reasoning/symbolic_reasoning_engine.py` has a full `WorldModel` with beliefs, predictions, action effects, and collision rules. But:
- `DecisionContext` has NO `world_model` field
- `ContextBuilder` never populates world model data
- No rung can access world model through context
- `world_model_states` DB table has zero writers
- 4 rungs build causal maps independently in memory, never persisting or sharing

### Task
1. **Add `world_model` field to `DecisionContext`** in `context_builder.py`
   - Type: dict with keys `cell_states`, `causal_map`, `goal_state`, `delta`, `rules_learned`, `level_diffs`, `action_history`
   - Populate from `SymbolicReasoningEngine` if available, else empty dict
2. **Wire `SymbolicReasoningEngine` into `evolution_runner.py`**
   - Instantiate per-game-session (not per-action)
   - Pass to `ContextBuilder` so it can populate `world_model`
   - Call `update()` after each action with pre/post frames
3. **Persist causal map to database** after game completion
   - Write to `world_model_states` table (schema exists, zero writers)
   - Read from DB on new game with same game_id prefix (transfer learning)
4. **Unify the 4 fragmented causal map implementations**
   - `CausalClickMappingRung`, `ConstraintSatisfactionSolverRung`, `TileDiscoveryRung`, `SymbolicTrackerRung` all build causal maps independently
   - They should READ from `context['world_model']['causal_map']` instead of maintaining private copies
   - They should WRITE observations back to the shared world model

### Files to Touch
- `context_builder.py` — Add world_model field to DecisionContext
- `evolution_runner.py` — Wire SymbolicReasoningEngine per game session
- `engines/reasoning/symbolic_reasoning_engine.py` — Verify interface
- `rungs/exploitation.py` — CausalClickMappingRung, ConstraintSatisfactionSolverRung → read shared causal_map
- `rungs/hypothesis.py` — TileDiscoveryRung, SymbolicTrackerRung → read shared causal_map
- `result_recorder.py` — Persist world model to DB after game
- `database_interface.py` — Write to world_model_states table

### Validation
- [ ] `context.world_model` is not None during gameplay
- [ ] `causal_map` grows as actions produce frame changes
- [ ] `world_model_states` table has new rows after games
- [ ] Rungs read from shared world model (grep for `context.*world_model`)
- [ ] No rung maintains private causal map (only reads/contributes to shared)

### Anti-Patterns to Avoid
- Don't create a NEW WorldModel class — use the existing `SymbolicReasoningEngine`
- Don't break existing rung evaluate() signatures
- Don't make world_model required — graceful degradation if engine unavailable

---

## SUBAGENT 2: Implement Goal-State Differencing
**Priority**: P0 (Highest — without goals, no purposeful action)
**Estimated Effort**: Medium
**Dependencies**: None (can run parallel with Subagent 1)
**Theory Alignment**: Section 7.4 — "3 cells need to change from blue to red" is actionable

### Problem
The visual cortex detects reference panels (`_detect_reference_panel`), but:
- Nobody reads the reference panel's pixel content to extract the goal state
- No `goal_state` or `delta` field in DecisionContext
- `ConstraintSatisfactionSolverRung` guesses targets as "most common color" instead of reading reference
- `inferred_goal_states` DB table has zero writers
- `seed_primitives.py` has `_detect_goal_achievement()` and `_measure_goal_distance()` but they're never called

### Task
1. **Extract goal state from reference panel** in visual cortex or context builder
   - After `_detect_reference_panel()` identifies the reference, read its cell colors
   - Map reference panel cells to workspace panel cells (spatial correspondence)
   - Compute `goal_state: dict[(x,y), color]` and `delta: dict[(x,y), (current, target)]`
2. **Add `goal_state` and `goal_delta` fields to DecisionContext**
   - Populated by ContextBuilder using visual cortex's reference panel analysis
3. **Wire ConstraintSatisfactionSolverRung to use goal_state**
   - Replace "most common color" heuristic with `context.goal_delta`
   - Solve for: "which clicks transform current → goal?"
4. **Write to `inferred_goal_states` table** when goal state is computed
   - Enables cross-session goal state caching
5. **Add goal progress tracking** — after each action, recompute delta and track convergence

### Files to Touch
- `engines/perception/visual_cortex.py` — Extract reference panel cell content
- `context_builder.py` — Add goal_state, goal_delta to DecisionContext
- `rungs/exploitation.py` — ConstraintSatisfactionSolverRung reads goal_state
- `database_interface.py` — Write to inferred_goal_states table

### Validation
- [ ] `context.goal_state` populated for games with reference panels
- [ ] `context.goal_delta` shows which cells differ from goal
- [ ] `inferred_goal_states` table has new rows
- [ ] ConstraintSatisfactionSolverRung uses goal_state instead of color-majority heuristic
- [ ] Goal delta decreases when correct actions are taken

---

## SUBAGENT 3: Implement Deliberate Experimentation Mode
**Priority**: P0 (Highest — Level 1 is the tutorial, must learn here)
**Estimated Effort**: Medium
**Dependencies**: Subagent 1 (world model to record learnings), Subagent 2 (goal state)
**Theory Alignment**: Section 7.2 — "Level 1 is the quickstart guide"

### Problem
No code treats levels 1-2 as "learning phase" vs levels 3+ as "exploitation phase":
- `BudgetAwarePlanningRung` phases by budget % within a level, NOT across levels
- No "click each distinct object once" systematic exploration
- No information-gain-maximizing action selection
- The system wastes early levels trying to win instead of trying to LEARN

### Task
1. **Add level-aware phasing to cognitive strategy selection**
   - `CognitiveRouter` (or a pre-routing rung) should check `context.current_level`
   - Levels 1-2: prioritize exploration/hypothesis rungs, suppress exploitation rungs
   - Levels 3+: prioritize exploitation rungs, reduce exploration budget
2. **Create systematic first-contact protocol**
   - On level 1, action 1: analyze the scene (panels, objects, grid structure)
   - Actions 2-N: click each distinct object type once, record frame diff
   - Track "explored objects" set — don't re-explore known effects
   - By end of level 1: causal_map should have one entry per clickable object type
3. **Add information gain scoring to exploration rungs**
   - An action targeting an unexplored object has HIGH information value
   - An action repeating a known-effect position has LOW information value
   - Weight action selection by information gain during learning phase
4. **Wire into BudgetAwarePlanningRung**
   - Cross-level budget: spend MORE actions on levels 1-2 (learning), FEWER on levels 3+ (exploit)
   - Level 1-2 "failure" is acceptable if causal map is populated

### Files to Touch
- `rungs/filter_rungs.py` — BudgetAwarePlanningRung: add level-aware cross-level phasing
- `rungs/exploration.py` — SmartActionSelectionRung: add information-gain scoring
- `rungs/orientation.py` — Add first-contact protocol rung or modify SurveyRung
- `engines/cognition/cognitive_router.py` — Level-aware rung priority adjustment
- `context_builder.py` — Ensure current_level is in DecisionContext (may already be)

### Validation
- [ ] On level 1, exploration rungs are selected ≥70% of the time
- [ ] On level 3+, exploitation rungs are selected ≥50% of the time
- [ ] By end of level 1, `causal_map` has entries for ≥3 distinct positions
- [ ] Number of unique click positions on level 1 ≥ 5 (for click games)
- [ ] Level 2 actions show exploitation of level 1 learnings (fewer random clicks)

---

## SUBAGENT 4: Implement Level-to-Level Differencing
**Priority**: P1 (High — the game teaches through progressive difficulty)
**Estimated Effort**: Small-Medium
**Dependencies**: Subagent 1 (world model stores level_diffs)
**Theory Alignment**: Section 7.3 — "The delta IS the lesson the game is teaching"

### Problem
No code compares previous level's visual scene to current level's scene:
- `context_builder.py` `handle_level_transition()` only clears checkpoints
- `visual_cortex.compare_frames()` exists but is used for action diffs, not level diffs
- No `level_diffs` field in DecisionContext
- The system starts each level from scratch, ignoring the curriculum

### Task
1. **Snapshot visual scene at level end**
   - Before transitioning to new level, save current `VisualScene` (or key features)
   - Store in game-session state (not per-action)
2. **Compare scenes on level transition**
   - When new level detected, run `compare_frames()` between old and new initial frames
   - Extract: grid_size_change, new_colors, object_count_change, new_panel_types, structural_changes
3. **Add `level_diffs` to DecisionContext**
   - List of diffs from all previous level transitions in this game
   - Most recent diff prominently available
4. **Wire hypothesis rungs to read level_diffs**
   - New colors → "test what new colors do"
   - More objects → "the rule applies to more targets now"
   - Larger grid → "same rule, bigger scale"

### Files to Touch
- `context_builder.py` — Add level_diffs field, snapshot previous level scene
- `game_player.py` or `game_loop.py` — Detect level transition, trigger snapshot
- `engines/perception/visual_cortex.py` — May need `compare_scenes()` method
- `rungs/hypothesis.py` — Read level_diffs for hypothesis generation

### Validation
- [ ] `context.level_diffs` populated after level transitions
- [ ] Each diff contains meaningful structural comparisons
- [ ] Hypothesis rungs adjust behavior based on level_diffs
- [ ] System identifies new elements introduced at each level

---

## SUBAGENT 5: Implement Puzzle-Type Classification
**Priority**: P1 (High — don't waste actions figuring out what kind of game this is)
**Estimated Effort**: Small-Medium
**Dependencies**: None
**Theory Alignment**: Section 7.5 — "Classify before the first action"

### Problem
Game type classification is implicit and crude:
- Only a binary `is_click_game` flag based on available_actions containing 6
- `game_type` is just first 4 chars of game_id (string prefix, not semantic)
- No pre-first-action classification from visual analysis
- No structured taxonomy like {click_toggle, movement_maze, transformation, hybrid}
- No strategy selection based on classification

### Task
1. **Create PuzzleTypeClassifier** (or add to ContextBuilder)
   - Input: available_actions, initial frame analysis, game_id prefix, previous experience with this game
   - Output: structured classification with confidence
   - Taxonomy: `click_toggle`, `click_transform`, `movement_maze`, `pattern_completion`, `hybrid`, `unknown`
2. **Classification signals**:
   - `available_actions=[6]` → click game
   - `available_actions=[1,2,3,4]` → movement game
   - `available_actions=[1,2,3,4,5,6]` → hybrid
   - Panel count 4 with clear input/output → transformation game
   - Grid of same-sized cells → toggle/constraint game
   - Single agent marker → movement/navigation game
3. **Add `puzzle_type` field to DecisionContext**
4. **Wire CognitiveRouter to use puzzle_type for strategy selection**
   - Click toggle → prioritize CausalClickMapping, ConstraintSatisfaction rungs
   - Movement maze → prioritize WallNavigation, SpatialMap rungs
   - Pattern completion → prioritize Transformation hypothesis rungs
5. **Persist classification** — store in DB for reuse when same game_id encountered again

### Files to Touch
- `context_builder.py` — Add puzzle_type classification logic and field
- `engines/cognition/cognitive_router.py` — Use puzzle_type for rung selection
- `config/rung_orderings.json` — May need per-puzzle-type orderings
- `database_interface.py` — Store/retrieve game classifications

### Validation
- [ ] `context.puzzle_type` is non-None before first action
- [ ] FT09 classified as `click_toggle`
- [ ] LS20 classified as `movement_maze`
- [ ] VC33 classified as `click_transform`
- [ ] CognitiveRouter selects different rung sets for different puzzle types
- [ ] Returning to a known game uses cached classification

---

## SUBAGENT 6: Fix Epistemic Signals (Phase 0.2)
**Priority**: P2 (Medium — needed for real learning, not just confidence-threshold transitions)
**Estimated Effort**: Small
**Dependencies**: None
**Theory Alignment**: Phase 0.2 — KU→KK transitions must be based on real question resolution

### Problem
The copilot instructions flag that epistemic state transitions (Known-Unknown → Known-Known) may be based on confidence thresholds rather than actual question resolution. This means the system "thinks" it knows things it hasn't actually verified.

### Task
1. **Audit epistemic tracking** in `engines/cognition/epistemic_tracking.py`
   - Find where KU→KK transitions are triggered
   - Determine if they're based on: (a) confidence threshold, (b) actual verified observation, or (c) question explicitly answered
2. **If synthetic**: Fix transitions to require evidence
   - A question moves to KK only when an action produces a frame change that answers it
   - Example: "Does clicking (3,5) toggle neighbors?" → KK only after clicking (3,5) and observing neighbor change
3. **Wire to feedback loop** — `on_action_complete` should trigger epistemic state transitions

### Files to Touch
- `engines/cognition/epistemic_tracking.py` — Fix transition conditions
- `rungs/hypothesis.py` — Ensure hypothesis resolution updates epistemic state
- `outcome_processor.py` — May need to trigger epistemic updates on action feedback

### Validation
- [ ] KU→KK transitions only happen after corresponding frame change evidence
- [ ] No epistemic state changes without an action being taken
- [ ] Epistemic state count grows as the game is explored

---

## SUBAGENT 7: Wire Resonance Pattern Writing (Phase 3.1)
**Priority**: P2 (Medium — needed for cross-game transfer)
**Estimated Effort**: Small
**Dependencies**: None
**Theory Alignment**: Seal 6 (Isolation) — games solved independently, no shared patterns

### Problem
`resonance_detector.record_resonance_pattern()` exists but is only called from side-engines (`i_thread`, `deliberation_engine`), never from the main game loop. The event bus subscriber calls `find_resonance_patterns()` (reads) but not `record_resonance_pattern()` (writes).

### Task
1. **Add resonance pattern recording** to the main game loop
   - After each game completion, check if the game's solution patterns resemble any other game's patterns
   - Call `record_resonance_pattern()` when structural similarity detected
2. **Wire to event bus** — GAME_WON event should trigger resonance recording
3. **Verify write path** — confirm data appears in `resonance_patterns` table

### Files to Touch
- `evolution_runner.py` — Add resonance recording on game completion
- `engines/social/resonance_detector.py` — Verify record_resonance_pattern() interface
- `result_recorder.py` — May be better home for post-game resonance check

### Validation
- [ ] `resonance_patterns` table has new rows after multi-game generations
- [ ] Patterns link structurally similar games
- [ ] Scheduler reads resonance patterns for game assignment (already wired)

---

## SUBAGENT 8: Unify Game-Playing Paths (Phase 4.3)
**Priority**: P2 (Medium — prevents feature divergence)
**Estimated Effort**: Medium
**Dependencies**: Subagents 1-5 (want unified path to have all new capabilities)

### Problem
`core_gameplay.py` (530 lines) and `game_player.py`/`evolution_runner.py` are TWO independent game-playing implementations. `core_gameplay.py` lacks:
- Cognitive router
- Viral packages
- Horizontal transfer
- Event bus integration
- Most engine integrations

### Task
1. **Audit `core_gameplay.py` callers** — who uses this path and why?
2. **Determine if `core_gameplay.py` can be replaced** by `game_player.py` for all use cases
3. **If unique functionality exists**: migrate it into `game_player.py`
4. **Deprecate or delete `core_gameplay.py`** (Rule 3: No Orphaned Code)
5. **Update all references** to point to unified path

### Files to Touch
- `core_gameplay.py` — Audit, migrate unique features, then deprecate
- `game_player.py` — Absorb any missing capabilities
- Any files that import core_gameplay — Update references

### Validation
- [ ] Single game-playing path through `game_player.py`
- [ ] All features from both paths available in unified path
- [ ] `core_gameplay.py` deleted or marked deprecated with clear reason
- [ ] All tests pass
- [ ] No behavior regression

---

## SUBAGENT 9: Verify Phase 5 Self-Tuning Status
**Priority**: P3 (Lower — verify before building)
**Estimated Effort**: Small (research only)
**Dependencies**: None

### Problem
Three Phase 5 tasks have UNKNOWN status:
- 5.1: Adaptive transfer rates (hardcoded 0.15/0.45/0.75?)
- 5.2: Emergent concept targets (limited to 7 hardcoded?)
- 5.4: Adaptive cleanup thresholds (static retention limits?)

### Task
1. **Read `horizontal_transfer_engine.py`** — check if transfer rates adapt based on evidence or are hardcoded
2. **Read `concept_discovery_engine.py`** — check if concept targets can be dynamically discovered or limited to hardcoded set
3. **Read `safe_cleanup.py`** — check if retention thresholds adapt based on system health or are static
4. **Report findings** — for each: DONE (adaptive), NOT DONE (static), or PARTIALLY (some adaptive, some not)
5. **If NOT DONE**: create specific task descriptions for what needs to change

### Files to Read
- `horizontal_transfer_engine.py` — Search for transfer rate logic
- `concept_discovery_engine.py` — Search for concept target list and discovery mechanism
- `safe_cleanup.py` — Search for retention threshold values and adaptation logic

### Validation
- Report only — no code changes. Output a clear status for each task.

---

## SUBAGENT 10: Update Copilot Instructions
**Priority**: P3 (Important for future sessions — prevents LLM catastrophic forgetting)
**Estimated Effort**: Medium
**Dependencies**: After Subagents 1-9 complete (reflects final state)

### Problem
The copilot-instructions.md is stale. Many facts no longer match the codebase:
- Says `evolution_runner.py` is ~2,400 lines (now 1,539)
- Says `decision_rung_system.py` is ~10,600 lines (now 1,638)
- Says `primitive_unlock_manager` was "never created" (it exists, 519 lines)
- Phase status table is outdated (most phases now complete)
- Doesn't reflect rungs/ package decomposition
- Doesn't reflect engines sub-package current structure
- Missing new files: `result_recorder.py`, `schema_auto_maintenance.py`, etc.

### Task
1. **Update PART 2 Architecture Map** — correct line counts, add new files, remove stale entries
2. **Update Phase status** — mark completed phases, add remaining gaps accurately
3. **Update file/role table** — reflect current decomposition
4. **Update engine sub-packages list** — add new sub-packages, correct file counts
5. **Add Part 7 status** — document which cognitive capabilities are implemented
6. **Update Appendix A commands** — verify all commands still work
7. **Update version and date**

### Files to Touch
- `.github/copilot-instructions.md` — Full update

### Validation
- [ ] All file references match actual files
- [ ] All line counts within 10% of actual
- [ ] Phase status accurately reflects implementation
- [ ] No references to files that don't exist
- [ ] Version bumped to 4.0

---

## SUBAGENT 11: Unify Fragmented Causal Map Building
**Priority**: P1 (High — foundational for world model)
**Estimated Effort**: Medium
**Dependencies**: Subagent 1 (shared world model in context)
**Theory Alignment**: Seal 1 (Monolith avoidance) + Seal 6 (Isolation)

### Problem
4 rungs build causal maps independently:
| Rung | File | What it tracks | Persistence |
|------|------|---------------|-------------|
| CausalClickMappingRung | rungs/exploitation.py | Click position → pixel changes | Instance-only |
| ConstraintSatisfactionSolverRung | rungs/exploitation.py | Same data, independently | Instance-only |
| TileDiscoveryRung | rungs/hypothesis.py | Tile position → state changes | Instance-only |
| SymbolicTrackerRung | rungs/hypothesis.py | Click position → object movement | Instance-only |

Plus `causal_model` slot in `slot_registry.py` (zero readers) and `causal_chains` DB table (zero writers).

### Task
1. **Define shared causal map protocol** — all rungs contribute observations to one shared structure
2. **Each rung contributes observations** — when it takes an action and observes a result, it writes to the shared causal map
3. **Each rung reads from shared causal map** — instead of building its own
4. **Persist to DB** — `causal_chains` table should receive writes
5. **Wire `causal_model` slot** — add readers in the rungs that consume causal knowledge

### Files to Touch
- `rungs/exploitation.py` — CausalClickMappingRung, ConstraintSatisfactionSolverRung
- `rungs/hypothesis.py` — TileDiscoveryRung, SymbolicTrackerRung
- `engines/cognition/slot_registry.py` — Add readers for causal_model slot
- `context_builder.py` — Populate causal_model from DB/session state

### Validation
- [ ] `causal_chains` table has new rows after games
- [ ] All 4 rungs read from shared causal map
- [ ] All 4 rungs contribute to shared causal map
- [ ] No rung maintains private-only causal data
- [ ] `causal_model` slot has both writers and readers

---

## EXECUTION ORDER & DEPENDENCY GRAPH

```
                    ┌──────────────┐
                    │  SUBAGENT 9  │ (Verify Phase 5 - research only)
                    │  P3: Verify  │
                    └──────────────┘

   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
   │  SUBAGENT 1  │  │  SUBAGENT 2  │  │  SUBAGENT 5  │
   │ P0: World    │  │ P0: Goal     │  │ P1: Puzzle   │
   │ Model        │  │ Differencing │  │ Classify     │
   └──────┬───────┘  └──────┬───────┘  └──────────────┘
          │                 │
          ├─────────────────┤   ┌──────────────┐  ┌──────────────┐
          │                 │   │  SUBAGENT 6  │  │  SUBAGENT 7  │
          ▼                 ▼   │ P2: Epistemic│  │ P2: Resonance│
   ┌──────────────┐             │ Signals      │  │ Write Path   │
   │  SUBAGENT 11 │             └──────────────┘  └──────────────┘
   │ P1: Unify    │
   │ Causal Maps  │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │  SUBAGENT 3  │
   │ P0: Deliber. │
   │ Experiment   │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │  SUBAGENT 4  │
   │ P1: Level    │
   │ Differencing │
   └──────────────┘

   ┌──────────────┐
   │  SUBAGENT 8  │ (After 1-5 — want unified path to have all new capabilities)
   │ P2: Unify    │
   │ Game Paths   │
   └──────────────┘

   ┌──────────────┐
   │  SUBAGENT 10 │ (LAST — reflects final state)
   │ P3: Update   │
   │ Docs         │
   └──────────────┘
```

### Parallel Execution Groups

**Wave 1** (no dependencies — run in parallel):
- Subagent 1: Wire Persistent World Model
- Subagent 2: Implement Goal-State Differencing
- Subagent 5: Implement Puzzle-Type Classification
- Subagent 6: Fix Epistemic Signals
- Subagent 7: Wire Resonance Pattern Writing
- Subagent 9: Verify Phase 5 Self-Tuning Status

**Wave 2** (depends on Wave 1):
- Subagent 11: Unify Fragmented Causal Maps (needs Subagent 1)
- Subagent 3: Deliberate Experimentation Mode (needs Subagents 1 + 2)

**Wave 3** (depends on Wave 2):
- Subagent 4: Level-to-Level Differencing (needs Subagent 1)
- Subagent 8: Unify Game-Playing Paths (needs all capabilities wired)

**Wave 4** (final):
- Subagent 10: Update Copilot Instructions (reflects all changes)

---

## POST-EXECUTION VALIDATION PROTOCOL

After ALL subagents complete, run the full integration check:

```bash
# 1. All tests pass
python -m pytest tests/ -v

# 2. Run one generation
python evolution_runner.py --mode offline --max-generations=1 --verbose

# 3. Verify new context fields populated
# Check logs for: world_model, goal_state, goal_delta, puzzle_type, level_diffs

# 4. Verify database writes
python -c "
import sqlite3
conn = sqlite3.connect('core_data.db')
c = conn.cursor()
for table in ['world_model_states', 'inferred_goal_states', 'causal_chains', 'resonance_patterns']:
    try:
        count = c.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
        print(f'{table}: {count} rows')
    except:
        print(f'{table}: TABLE MISSING')
conn.close()
"

# 5. Check alignment velocity
# Did any level get completed? Even level 1 completion = massive progress.
```

### Success Criteria (Alignment Velocity Targets)
| Metric | Current | After Plan | Target |
|--------|---------|-----------|--------|
| Levels completed per game | 0 | ≥0.2 | ≥1.0 |
| Unique positions per click game | ~1 (fixation) | ≥5 | ≥9 |
| Causal map entries after level 1 | 0 | ≥3 | ≥5 |
| Goal state identified | Never | On reference panel games | Always |
| Rung diversity per game | ~1-2 | ≥3 | ≥5 |
| Alignment velocity | 0.00 | >0.01 | 0.05 |

---

## CRITICAL RULES FOR ALL SUBAGENTS

Every subagent MUST follow these rules from the copilot instructions:

1. **Rule 1**: Set `PYTHONDONTWRITEBYTECODE=1` — no .pyc files
2. **Rule 2**: All data in SQLite `core_data.db` — no .log files
3. **Rule 3**: No orphaned code — delete/integrate old code when refactoring
4. **Rule 8**: Test before commit — run one generation, scan for errors
5. **Rule 10**: Prevent code drift — enhance existing files, don't create new standalone files
6. **Rule 11**: No Unicode emojis — use ASCII alternatives `[OK]`, `[FAIL]`, etc.
7. **Rule 16**: Always use `.venv` — activate before ANY Python execution

### Mandatory Post-Change Checks
- [ ] `python -m pytest tests/ -v` passes
- [ ] Pylance shows 0 errors
- [ ] One generation runs without crashes
- [ ] Pipeline assertions produce 0 CRITICAL findings
- [ ] `notify_action_complete` still fires for every action
- [ ] Game results still written to database after each game

---

**END OF SUBAGENTS PLAN**
