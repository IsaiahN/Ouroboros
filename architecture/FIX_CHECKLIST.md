# CODEBASE FIX CHECKLIST
**Generated**: January 9, 2026  
**Based On**: Audit Report + Learning Failure Diagnostic Report  
**Goal**: Make agents actually LEARN, not just log
**Last Updated**: January 9, 2026 - Phase 1 Complete

---

## Priority Legend
- 🔴 **CRITICAL** - Agents cannot learn without this fix
- 🟠 **HIGH** - Major learning pathway broken
- 🟡 **MAJOR** - Significant architectural deviation from theory
- 🟢 **MODERATE** - Refinement needed
- ✅ **COMPLETED** - Fix implemented and verified

---

## PHASE 1: LEARNING ACTUATION (Fix Before Anything Else) ✅ COMPLETED

These fixes address the core problem: **"Logging vs Learning Confusion"** - the system observes but doesn't act on observations.

### ✅ 1. Discovery → Immediate Exploitation - COMPLETED
**Files**: `agent_self_model.py`, `core_gameplay.py`  
**Problem**: When `learn_from_movement_correlation()` finds control, it logs to database but returns nothing. Next action ignores discovery.  
**Fix Applied**:
1. ✅ `learn_from_movement_correlation()` now RETURNS discovery dict with action, color, reliability
2. ✅ Caller in `core_gameplay.py` stores discovery in `self._last_discovery`
3. ✅ `_select_action()` checks `_last_discovery` at TOP priority and exploits immediately
4. ✅ Discovery exploitation happens before any other decision logic

**Test**: After fix, console should show: `[DISCOVERY->ACTION] Exploiting: ACTION# (reliability X.XX)`

---

### ✅ 2. Connect Q1 to Self-Model Discoveries - COMPLETED
**Files**: `core_gameplay.py` lines 14600+  
**Problem**: Q1 says "no actions observed to change state" while discoveries are being made elsewhere.  
**Fix Applied**:
1. ✅ Q1 context building now queries `network_object_control_hypotheses` directly
2. ✅ Network hypotheses with validation_attempts >= 1 are included in Q1's "controlled_objects"
3. ✅ Q1 narrative includes both self-model discoveries AND network hypotheses

**Test**: Q1 should show actual object control after discoveries made

---

### ✅ 3. Fix Network Wisdom Query (Stream B Empty) - COMPLETED
**Files**: `database_interface.py`  
**Problem**: After 300+ generations, `get_network_wisdom()` returns "No agent data - using defaults". Query returns empty.  
**Fix Applied**:
1. ✅ Root cause: `store_agent()` was not saving Two-Streams columns
2. ✅ Added: `self_network_bias`, `navigation_state`, `role_confidence`, `sensation_profile` to INSERT
3. ✅ Also added: `sensation_learning_rate`, `state_update_sensitivity`, `emotional_intelligence_score`
4. ✅ Fallback network wisdom now computed properly

**Test**: `network_strength` should be > 0 for agents created after this fix

---

### ✅ 4. Prediction Failure → Strategy Revision - COMPLETED
**Files**: `agent_self_model.py`  
**Problem**: 143 consecutive wrong predictions. Suppression just skips prediction, doesn't revise theory.  
**Fix Applied**:
1. ✅ Added `_contradicted_actions` dict to track theory failures
2. ✅ `revise_theory()` now extracts ACTION from theory text and marks it as contradicted
3. ✅ `get_contradicted_actions()` returns dict mapping action → contradiction count
4. ✅ `_select_action()` in escape mode penalizes contradicted actions with scaling penalty

**Test**: After theory revision, contradicted actions get reduced scores

---

### ✅ 5. Stuck Detection → Recovery Mode - COMPLETED
**Files**: `core_gameplay.py` - `_select_action()`  
**Problem**: Agent knows it's stuck (0.9 confidence, 47 frames) but continues same behavior.  
**Fix Applied**:
    # Try actions NOT in recent history
    # Mark stuck state in network
    return random_unexplored_action()
1. ✅ Compute stuck_confidence from metacognitive summary (theory revisions + eliminations + failures)
2. ✅ When stuck_confidence > 0.7 OR primitive `_is_stuck = True`, enter recovery mode
3. ✅ Recovery mode selects untried actions (not in recent history)
4. ✅ Recovery mode lasts 10 actions then auto-exits
5. ✅ Clear contradicted actions to give fresh start

**Test**: Stuck agent should try different actions with `[FIX5-RECOVERY]` logging

---

### ✅ 6. Failure Hypotheses Must Filter Actions - COMPLETED
**Files**: `core_gameplay.py`  
**Problem**: 732 failure hypotheses exist but action is "Standard balanced strategy" ignoring them all.  
**Fix Applied**:
1. ✅ `peer_failures` now parsed and stored in `_peer_failures_to_avoid` list
2. ✅ Each failure entry contains: action number, reason, confidence
3. ✅ `_finalize_ladder_and_return()` checks proposed action against failures
4. ✅ If action matches high-confidence failure (conf > 0.4 after wB scaling), picks alternative
5. ✅ Uses wB (network trust) to scale failure confidence

**Test**: Reasoning should show `[FIX6-PEER-FILTER] Avoided ACTION# (failure reason)`

---

### ✅ 7. Make w_A/w_B Decision-Active - COMPLETED
**Files**: `core_gameplay.py`  
**Problem**: `w_A_weight` and `w_B_weight` exist but only used for logging. WeavingReporter creates reports but actions NOT weighted.  
**Fix Applied**:
1. ✅ Compute wA/wB at start of `_select_action()` from agent's `self_network_bias`
2. ✅ Also check autobiography's session_state for dynamic wA/wB
3. ✅ Store in `_current_wA` and `_current_wB` for use throughout
4. ✅ Track in ladder_trace as `two_streams.wA/wB`
5. ✅ Use wB to gate network trust in peer failure filtering

**Test**: Higher wB should make agents respect network failures more

---

## PHASE 2: STREAM ARCHITECTURE ACTIVATION

These fixes make the Two Streams architecture fully influence decisions.

### ✅ 8. Implement I-Thread Stream Weaver - COMPLETED (January 9, 2026)
**Files**: `core_gameplay.py` - `_select_action()`  
**Problem**: No I-Thread implementation exists. Theory says it weaves Stream A/B moment-by-moment.  
**Fix Applied**:
1. ✅ Added Stream A proposal collection (discoveries, contradicted actions)
2. ✅ Added Stream B proposal collection (network hypotheses, peer failures)
3. ✅ Added conflict detection when streams disagree
4. ✅ Added I-Thread synthesis using weighted scores (wA*A + wB*B)
5. ✅ When weighted score is negative (both want to avoid), find best alternative
6. ✅ Logs `[I-THREAD]` when conflict detected and synthesized

**Test**: Reasoning should show "I-Thread: Synthesized from streams (wA=X, wB=Y)"

---

### ✅ 9. Add stream_type to Personas - COMPLETED (January 9, 2026)
**Files**: `persona_runtime.py`, `database_interface.py`  
**Problem**: Personas exist but not stream-integrated. No categorization as proposers (Stream A) vs observers (Stream B).  
**Fix Applied**:
1. ✅ Added `stream_type` parameter to `ensure_persona()` ('A', 'B', or 'neutral')
2. ✅ Added auto-derivation from persona_type:
   - 'proposer', 'explorer', 'pioneer', 'investigator', 'discovery' → Stream A
   - 'observer', 'evaluator', 'validator', 'optimizer', 'network' → Stream B
   - 'counterfactual', 'scorer', 'classifier' → neutral
3. ✅ Updated `upsert_persona_profile()` to store stream_type
4. ✅ Added auto-migration: ALTER TABLE adds column if not exists
5. ✅ Stored in persona cache for runtime access

**Test**: Persona activation should show stream type in profile

---

## PHASE 3: THEORY-EVIDENCE ALIGNMENT

These fixes ensure internal state matches reality.

### ✅ 10. Theory Stage Must Match Evidence - COMPLETED (January 9, 2026)
**Files**: `core_gameplay.py` - `_classify_theory_stage()`  
**Problem**: `theory_stage="confident"` but `control_confidence=0.2`, `validation="UNVALIDATED"`. Contradiction.  
**Fix Applied**:
1. ✅ Rewrote `_classify_theory_stage()` to compute from actual evidence
2. ✅ Extracts `control_confidence` from `network_control_hypotheses` reliability
3. ✅ Checks `validation_status` from hypothesis validation_attempts and validated_by_win
4. ✅ Stages: exploring (low confidence), hypothesizing (unvalidated), testing (partial), revising (contradictions), confident (validated + high)

**Test**: Cannot have "confident" with < 50% confidence or UNVALIDATED

---

### ✅ 11. Optimizer Validation During Replay - COMPLETED (January 9, 2026)
**Files**: `core_gameplay.py` - `_replay_sequence_inline_impl_body()`  
**Problem**: Optimizer is pure playback machine. All 63 frames identical reasoning. No adaptation if replay diverges.  
**Fix Applied**:
1. ✅ Load `frame_transitions` at replay start for expected outcome comparison
2. ✅ Added `compare_frame_similarity()` function to compare actual vs expected frames
3. ✅ Track `divergence_score` that accumulates when frames don't match expectations
4. ✅ Added `consecutive_matches` counter to decay divergence on good matches
5. ✅ When divergence exceeds threshold (3.0), trigger early adaptation (forces stuck mode)
6. ✅ Logs `[OUTCOME-VALIDATION]` when divergence detected

**Test**: If replay diverges from expected, optimizer triggers early adaptation with logging

---

## PHASE 4: CODS/ORACLE UNIFICATION

### ✅ 12. Merge Oracle into CODS - COMPLETED (January 10, 2026)
**Files**: `cods_engine.py`, `tests/test_cods.py`  
**Problem**: Theory says CODS=Oracle (one unified system). Reality: separate files, Oracle imported by CODS.  
**Fix Applied**:
1. ✅ CODS now imports and re-exports `OracleInterface`, `OracleVerdict`, `OracleDecision`
2. ✅ Added `__all__` export list to cods_engine.py
3. ✅ Updated tests/test_cods.py to import from cods_engine instead of oracle_interface
4. ✅ External code should now use: `from cods_engine import OracleInterface, OracleVerdict`

**Test**: `from cods_engine import CODSEngine, OracleInterface, OracleVerdict` works

---

### ✅ 13. CODS Operators Must Generate Actions - COMPLETED (January 10, 2026)
**Files**: `cods_engine.py`, `core_gameplay.py`  
**Problem**: CODS contributes 5 operators but final action is "salience target" from fallback. Operators logged but not used.  
**Fix Applied**:
1. ✅ `suggest_action()` now returns multiple candidates with scores in 'candidates' list
2. ✅ Operators do spatial reasoning (shape center, goal direction) instead of hard-coded actions
3. ✅ Added symmetry-based action suggestions (horizontal → left/right, vertical → up/down)
4. ✅ Goal distance operator suggests movement toward goal
5. ✅ Shape detection suggests movement toward shape centers
6. ✅ CODS candidates added to Stream B for I-Thread consideration even below threshold
7. ✅ Returns 'reasoning' field explaining operator logic

**Test**: CODS returns candidates with spatial reasoning, not hard-coded "action 1"

---

### ✅ 13b. Universal Object Patterns (Knowledge Transfer) - COMPLETED (January 9, 2026)
**Files**: `agent_self_model.py`  
**Problem**: Object discoveries are stored per-game. No transfer learning between similar games.  
**Fix Applied**:
1. ✅ Created `universal_object_patterns` table (game-agnostic object behaviors)
2. ✅ Created `game_pattern_links` table (links universal to game-specific)
3. ✅ Added `store_universal_pattern()` - stores patterns by object color + action + response
4. ✅ Added `get_universal_patterns_for_color()` - query patterns for transfer
5. ✅ Added `get_transferable_knowledge_for_game()` - get applicable patterns for new game
6. ✅ Added `record_transfer_outcome()` - track transfer success/failure
7. ✅ Integrated into `learn_from_movement_correlation()` on validation

**Test**: Pattern learned in game A should apply to game B with same mechanics

---

## PHASE 5: ROLE EMERGENCE

### ✅ 14. Roles Emergent Not Fixed Assignment - COMPLETED (January 9, 2026)
**Files**: `agent_operating_mode_system.py`  
**Problem**: Roles assigned via fixed 60/30/10 quotas. Theory says roles emerge from w_A/w_B ratios.  
**Fix Applied**:
1. ✅ Added `derive_role_from_weights()` - derives role from agent's wA/wB
2. ✅ Added `get_game_context_for_role()` - checks is_novel, has_solutions, is_saturated
3. ✅ Role derivation logic:
   - wA > 0.7 + novel context = Pioneer
   - wB > 0.7 + has solutions = Optimizer
   - wA > 0.6 + saturated = Exploiter
   - Balanced (0.35-0.65) = Generalist
4. ✅ Integrated into `assign_population_modes()` with soft 10% quota overflow
5. ✅ Falls back to performance-based assignment if derivation unavailable
6. ✅ Logs `[FIX14-EMERGENT]` with count of emergent roles

**Test**: `[FIX14-EMERGENT] N roles derived from wA/wB weights` in logs

---

## PHASE 6: CLOSE FEEDBACK LOOPS

### ✅ 15. Fix Fallback Path Always Winning - COMPLETED (January 9, 2026)
**Files**: `core_gameplay.py`  
**Problem**: Every sophisticated path ends in try/except that swallows errors. Fallback always executes silently.  
**Fix Applied**:
1. ✅ Upgraded exception handler in intelligent escape to WARNING level
2. ✅ Added traceback capture for last 2 frames
3. ✅ Track `_fallback_count` in game_config for diagnostics
4. ✅ Track `_last_fallback_error` for debugging
5. ✅ Fallback reasoning now includes error type and count

**Test**: Run should show `[FALLBACK-TRIGGERED]` with error details when fallback used

---

### ✅ 16. Close Database → Query → Action Loop - COMPLETED (January 9, 2026)
**Files**: `database_interface.py`  
**Problem**: Knowledge flows one direction: Discovery → Database → (nothing). Writes not committed.  
**Fix Applied**:
1. ✅ `execute_query()` now auto-commits after INSERT/UPDATE/DELETE/REPLACE operations
2. ✅ Discoveries made in action N are immediately queryable in action N+1
3. ✅ Combined with Fix #1, this completes the learning loop

**Test**: Discovery in action N should influence action N+1

---

## PHASE 7: REFINEMENTS

### ✅ 17. Integrate Network Hypotheses into Q4/Q8 - COMPLETED (January 9, 2026)
**Files**: `core_gameplay.py`  
**Problem**: Q4 takes `hypothesis_biases` but network control hypotheses not integrated into action biasing.  
**Fix Applied**:
1. ✅ Added query to `get_network_control_hypotheses()` in action selection
2. ✅ Parse action_response_map from hypotheses
3. ✅ Apply biases to action scores based on control knowledge
4. ✅ Validated hypotheses get 1.5x boost to bias amount

**Test**: `[FIX17] Applied N control hypotheses to action biases` in logs

---

### ✅ 18. Implement w_R Resonance in Decisions - COMPLETED (January 10, 2026)
**Files**: `core_gameplay.py`  
**Problem**: `w_R_weight` exists but not used in decision formula.  
**Fix Applied**:
1. ✅ Added `wR` weight retrieval from `game_config.get('w_R_weight')`
2. ✅ Compute `resonance_score` by querying universal patterns for action support
3. ✅ Updated weighted score formula: `decision = wA*A + wB*B + wR*R`
4. ✅ Cross-domain patterns validated across multiple games boost resonance
5. ✅ Added `[FIX18-RESONANCE]` logging when resonance contributes to decision

**Test**: `[FIX18-RESONANCE]` appears when universal patterns influence action

---

### ✅ 19. Populate Imagination Context - COMPLETED (January 10, 2026)
**Files**: `core_gameplay.py`  
**Problem**: `_imagination_ctx` rarely populated.  
**Fix Applied**:
1. ✅ Call `_compute_imagination_context()` early in `_select_action()` (after frame sanity check)
2. ✅ Extract `imagination_budget` and `imagination_mode` for decision-making
3. ✅ Added `imagination` section to ladder_trace with budget/mode/remaining
4. ✅ Log `[FIX19-IMAGINATION]` when budget is limited (late generations)

**Test**: `ladder_trace['imagination']` populated in action selection

---

### ✅ 20. Add Prestige/Budget Separation Guards - COMPLETED (January 10, 2026)
**Files**: `prestige_engine.py`, `adaptive_action_limits.py`  
**Problem**: Sacred separation in docs but no enforcement.  
**Fix Applied**:
1. ✅ Added `PrestigeBudgetViolationError` exception class
2. ✅ Added `assert_no_budget_effect()` guard in prestige_engine.py
3. ✅ Added `validate_budget_inputs_no_prestige()` guard in adaptive_action_limits.py
4. ✅ Guard validates inputs don't contain prestige-related fields
5. ✅ Called in `calculate_agent_salary()` to enforce separation at runtime

**Test**: Raises ValueError if prestige fields in budget calculation inputs

---

## VERIFICATION PROTOCOL

After each fix:
1. Run 2-3 games manually
2. Check reasoning payload shows DIFFERENT behavior
3. Verify: 
   - Discovery → Used (not just logged)
   - Stuck → Recovery (not continue same)
   - Hypothesis → Action filtering (not ignored)
   - Prediction failure → Theory revision (not just suppress)
4. Only commit to git when verified

---

## ROOT CAUSE SUMMARY

| Symptom | Root Cause | Fix Phase |
|---------|------------|-----------|
| 143 wrong predictions, no change | Suppress ≠ Learn | Phase 1 |
| "Confident" but speculating | Stage not computed from evidence | Phase 3 |
| No agent data after 300 gens | Query returns empty | Phase 1 |
| Discovery not used | No return value, no override | Phase 1 |
| 732 hypotheses ignored | Fallback wins | Phase 1 |
| Stuck but continues | Detection not connected to action | Phase 1 |
| Optimizer blind replay | No validation during replay | Phase 3 |
| w_A/w_B only for logging | Streams not decision-active | Phase 2 |
| CODS operators unused | Not integrated into selection | Phase 4 |
| Roles fixed not emergent | Assignment not derivation | Phase 5 |

---

## ORDER OF OPERATIONS

**Week 1**: Phase 1 (Learning Actuation) - Make discoveries USABLE
**Week 2**: Phase 2 (Stream Architecture) - Make weights ACTIVE
**Week 3**: Phase 3 + 4 (Theory-Evidence + CODS) - Align internals
**Week 4**: Phase 5 + 6 (Roles + Loops) - Complete architecture
**Week 5**: Phase 7 (Refinements) - Polish

**After each phase**: Run evolution, check for improvements, document.

---

**END OF FIX CHECKLIST**
