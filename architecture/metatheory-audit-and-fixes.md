# Metatheory Audit & Fixes Plan

**Date**: 2026-02-23
**Branch**: lab/mainline (post-H7/H8/H9 breakthrough)
**Context**: Cross-domain diagnostic using Serendipity Engine metatheory (Stream A/B, Seven Seals, Archetypes, Relationship Graph) applied to BitterTruth-AI codebase.

---

## Current State

| Game | L1 Completion | Status |
|------|---------------|--------|
| LS20 | 42.4% | BREAKTHROUGH (Phase A exit met) |
| FT09 | 0% | STUCK (150+ games, 0 wins) |
| VC33 | 0% | STUCK (150+ games, 0 wins) |

The H7/H8/H9 fix proved the metatheory correct: animation noise was corrupting epistemic feedback, violating the Amnesia seal. But this fix only helped LS20 (movement-based, capability axis). FT09 and VC33 remain at 0% because they have different structural problems.

---

## Methodology

10 questions were asked of the Serendipity Engine's LLM using the metatheory as a translation layer. Every answer mapped a narrative-domain diagnostic onto a code-domain intervention. The convergence across independently-asked questions validates the cross-domain isomorphism.

---

## TIER 1: CRITICAL (Blocking all FT09/VC33 progress)

### Fix 1.1: Wire Action6BehaviorEngine into Production Path

**Seal Violated**: AMNESIA (Seal 2) + ISOLATION (Seal 6)
**Q&A Source**: Q1 — "Character with rich inner life but no scenes"
**Diagnosis**: Action6BehaviorEngine has 1103 lines of click-learning logic. Its write methods (`save_pseudo_button_behavior`, `track_selection_change`, `track_action6_availability`, `classify_pseudo_button_effects`) are NEVER called in the production gameplay loop. Its read methods (`get_untried_objects_for_frontier`, `get_all_pseudo_buttons`) are called by rungs but always return empty because no data was ever written.

**Files**:
- `engines/self_model/action6_behavior.py` — the orphaned engine
- `game_player.py:1046-1160` — production gameplay loop (where writes should happen)
- `rungs/exploration.py:151-236` — Action6ObjectExplorationRung (reads empty data)
- `rungs/base.py:251-261` — also reads empty data

**Fix**:
After each ACTION6 in `game_player.py`, call:
```python
if action_num == 6 and hasattr(self, 'engines') and self.engines.action6_behavior:
    self.engines.action6_behavior.track_action6_availability(context)
    if meaningful_change:
        self.engines.action6_behavior.save_pseudo_button_behavior(
            x=action_data.get('x', 32), y=action_data.get('y', 32),
            frame_before=obs_before, frame_after=obs, context=context
        )
```

**Impact**: FT09/VC33 agents will accumulate click-effect knowledge across actions within a game session. Rungs will start returning non-empty frontiers.

---

### Fix 1.2: Game-Type-Specific `meaningful_change` Detection

**Seal Violated**: MONOLITH (Seal 1) + MONOCULTURE
**Q&A Source**: Q2 — "Three-Axis Progress Model (Knowledge / Want / Capability)"
**Diagnosis**: `meaningful_change` uses a 5% pixel threshold designed for LS20 (movement = large visual changes). FT09/VC33 progress is on the KNOWLEDGE axis — a single cell color change might affect 0.5% of pixels but represent critical puzzle state change. Current threshold says "nothing happened" when something crucial happened.

**Files**:
- `game_player.py:278-305` — `_is_meaningful_frame_change()` static method
- `game_player.py:1046-1047` — where meaningful_change is computed

**Fix**:
Replace single threshold with game-type-aware detection:
```python
def _is_meaningful_frame_change(self, obs_before, obs_after, game_type=None):
    # ... existing pixel diff computation ...
    if game_type in ('FT09', 'VC33'):
        # Knowledge axis: ANY localized change is meaningful
        # Check if change is concentrated (not ambient noise)
        threshold = 0.002  # 0.2% of pixels (a single cell changing)
        # Also: check if change is spatially concentrated vs distributed
        return change_ratio > threshold and is_concentrated(diff_mask)
    else:
        # Capability axis (LS20): large spatial displacement
        return change_ratio > 0.05
```

**Impact**: FT09/VC33 agents will correctly detect when their clicks change puzzle state, enabling epistemic feedback (H7) to actually function for click games.

---

### Fix 1.3: Re-enable `stuck_count` for ACTION6-Only Games

**Seal Violated**: AMNESIA (Seal 2)
**Q&A Source**: Q2 — "Wound-contact-per-scene metric"
**Diagnosis**: `stuck_count` is explicitly disabled for ACTION6-only games (`if not is_action6_only: stuck_count += 1`). This means H5 stuck-escape, emergency rungs, and confidence escalation NEVER fire for FT09/VC33. Agents repeat the same ineffective clicks forever with no mechanism to detect stuckness.

**Files**:
- `game_player.py:1050-1054` — the disabled increment
- `rungs/emergency.py:36-38` — `stuck_count >= 15` (never fires)
- `rungs/exploitation.py:1794-1795` — `stuck_count >= 3` (never fires)

**Fix**:
Remove the `is_action6_only` guard. Use the game-type-aware `meaningful_change` from Fix 1.2 to determine stuckness:
```python
if not meaningful_change and action.name.startswith('ACTION'):
    failed_actions.add(action.name)
    stuck_count += 1  # For ALL game types
```

With Fix 1.2 in place, `meaningful_change` will correctly detect FT09/VC33 stuckness (clicking same spot, or clicking with no effect), so stuck_count will increment appropriately.

**Impact**: Emergency and stuck-escape systems activate for FT09/VC33. Agents that are clicking ineffectively will escalate to different strategies.

---

### Fix 1.4: Add `action6_only` to ORDERING_PRESETS

**Seal Violated**: ISOLATION (Seal 6)
**Q&A Source**: Q8 — "Genre incompatibility"
**Diagnosis**: `decision_rung_system.py:823-834` returns `'action6_only'` for click-only games, but this ordering doesn't exist in `ORDERING_PRESETS`. The system silently falls back to whatever ordering the agent was initialized with (usually 'comprehensive', which prioritizes movement rungs over click-analysis rungs).

**Files**:
- `decision_rung_system.py:129+` — ORDERING_PRESETS definition
- `decision_rung_system.py:823-834` — `_select_ordering_for_context()`

**Fix**:
Add to ORDERING_PRESETS:
```python
'action6_only': [
    # Phase 1: Understand what's clickable
    'visual_analysis',
    'object_detection',
    'action6_object_exploration',
    # Phase 2: Apply learned click patterns
    'causal_click_mapping',
    'action6_behavior',
    # Phase 3: Constraint satisfaction
    'constraint_detection',
    'goal_state_proximity',
    # Phase 4: Emergency / fallback
    'grid_exploration',
    'random_frontier',
    'emergency',
]
```

**Impact**: FT09/VC33 agents get rungs specifically ordered for click-based puzzle solving instead of movement-oriented exploration.

---

## TIER 2: HIGH PRIORITY (Evolution signal quality)

### Fix 2.1: Reconnect FitnessCalculator to Evolution Pipeline

**Seal Violated**: ISOLATION (Seal 6) + AMNESIA (Seal 2)
**Q&A Source**: Q6 — "Role-assigned fitness partitioning"
**Diagnosis**: `engines/postgame/fitness_calculator.py` has a complete 7-component fitness calculation system that is 100% dead code. `evolutionary_engine.py` bypasses it entirely, reading raw metrics from `agent_arc_performance` directly. The FitnessCalculator was designed to provide nuanced reward signals (win_achievement, score_progress, score_efficiency, level_progression, consistency, exploration, path_efficiency) — exactly the kind of multi-component fitness the system needs.

**Files**:
- `engines/postgame/fitness_calculator.py` — dead code (never instantiated)
- `evolutionary_engine.py:290-340` — `_calculate_standard_fitness()` (ad-hoc replacement)
- `evolution_runner.py` — where FitnessCalculator should be instantiated

**Fix**:
1. Instantiate FitnessCalculator in evolution_runner
2. Route `_calculate_standard_fitness()` through FitnessCalculator instead of raw DB queries
3. Extend FitnessCalculator with game-type-specific components (puzzle progress for FT09, rail alignment for VC33)

**Impact**: Richer fitness signal with 7 components instead of 4. Enables future game-type-specific fitness tuning.

---

### Fix 2.2: EXPLORATION -> OPTIMIZATION Transition Must Be Dynamic

**Seal Violated**: STASIS (Seal 7)
**Q&A Source**: Q10 — "Phase model as modifiable character"
**Diagnosis**: `agent_operating_mode_system.py` checks for full wins to transition from EXPLORATION phase (60% pioneers) to OPTIMIZATION phase (10% pioneers). But `_update_population_distribution()` is only called at `__init__`. If the first win happens at generation 15, the population stays in EXPLORATION phase forever.

**Files**:
- `agent_operating_mode_system.py` — `_update_population_distribution()` and `assign_population_modes()`

**Fix**:
Call `_update_population_distribution()` at the start of each generation, not just at initialization. Additionally, support per-game phase transitions:
```python
def assign_population_modes(self, agent_ids, generation):
    self._update_population_distribution()  # Re-check phase every generation
    # ... existing assignment logic ...
```

**Impact**: Population role distribution adapts dynamically. When LS20 achieves wins, the system can shift toward optimization while keeping pioneers for FT09/VC33.

---

### Fix 2.3: Meta-Learning Fitness Bootstrap for Zero-Score Games

**Seal Violated**: HOARDING (Seal 5) + MONOPOLY (Seal 4)
**Q&A Source**: Q7 — "Endpoint-first declaration"
**Diagnosis**: Meta-learning fitness (30% of total) returns 0.0 for all FT09/VC33 agents because `_sync_meta_learning_from_performance()` uses "unique games scored on" as a proxy for "rules learned". When score = 0 for all games, rules_learned = 0, transfer_success = 0, everything = 0.

**Files**:
- `evolutionary_engine.py:495-566` — `_calculate_meta_learning_fitness()`
- `evolutionary_engine.py:568-642` — `_sync_meta_learning_from_performance()` (proxy computation)

**Fix**:
Bootstrap meta-learning from behavioral proxies when scores = 0:
```python
def _sync_meta_learning_from_performance(self, agent_id):
    # Existing score-based proxy...
    if scored_games == 0:
        # Use behavioral signals instead:
        # - unique_click_positions explored (from action_traces)
        # - distinct frame states observed (from frame_changes)
        # - causal patterns discovered (from action6_behavior data, if Fix 1.1 is in)
        behavioral_rules = self._count_behavioral_discoveries(agent_id)
        total_rules_learned = behavioral_rules
        learning_rate = behavioral_rules / max(total_games, 1)
```

**Impact**: 30% of fitness signal becomes alive for FT09/VC33. Evolution can now differentiate agents that explore differently even when neither scores.

---

### Fix 2.4: Wire `meaningful_change` into Rung Context

**Seal Violated**: AMNESIA (Seal 2)
**Q&A Source**: Q1 — "Load-bearing absence vs missing wire"
**Diagnosis**: `meaningful_change` is computed in `game_player.py:1046` and set in `context['meaningful_frame_changed']`, but rungs check `context.get('last_frame_changed')` (raw hash, always True) instead. The meaningful signal exists but is never consumed by the decision system.

**Files**:
- `game_player.py:1046-1047` — sets `context['meaningful_frame_changed']`
- `context_builder.py:388` — sets `'frame_changed': True` (always-true default)
- All rung files that check `frame_changed`

**Fix**:
1. In `context_builder.py`, replace the `frame_changed` default with `meaningful_frame_changed`
2. Audit all rung references to `frame_changed` and update to use `meaningful_frame_changed`
3. Or simpler: make `context_builder.update_runner_outcome()` overwrite `frame_changed` with the meaningful version

**Impact**: Rungs stop being fooled by animation noise. Stuck detection, confidence adjustment, and strategy switching all operate on real signal.

---

## TIER 3: STRUCTURAL (Architecture alignment with metatheory)

### Fix 3.1: Per-Game Fitness Functions (Genre Differentiation)

**Seal Violated**: MONOLITH (Seal 1)
**Q&A Source**: Q7 (endpoint-first), Q8 (genre incompatibility), Q10 (phase inversion)
**Diagnosis**: All three Q&A answers converged independently: FT09 is a constraint-satisfaction puzzle, not an incremental-improvement task. The fitness function treats all games identically. For FT09, "proximity to solution" should be measured, not "how far you walked."

**Approach** (for lab orchestrator to tune):
- LS20: Keep current fitness (movement exploration, level completions)
- FT09: Add constraint-satisfaction fitness component:
  - How many constraint sprites are currently satisfied?
  - Are cells cycling through colors systematically or randomly?
  - Has the agent discovered the click-effect mapping?
- VC33: Add spatial-alignment fitness component:
  - How many rail segments are in correct position?
  - Are colored people closer to their matching slots?

**Files**:
- `engines/postgame/fitness_calculator.py` — add game-type-specific components
- `evolutionary_engine.py` — pass game_id to fitness calculation
- `result_recorder.py` — store game-type-specific progress metrics

**Implementation Note**: This is where the lab orchestrator should have latitude. The fix is to ADD the infrastructure for per-game fitness. The orchestrator then tunes weights.

---

### Fix 3.2: Role-Based Rung Filtering (Archetype Assignment)

**Seal Violated**: HIERARCHY (Seal 3) + MONOCULTURE
**Q&A Source**: Q6 — "Archetype-specific fitness"
**Diagnosis**: All agents see the same rung sequence regardless of role. Pioneer agents should get exploration-heavy rungs; Optimizer agents should get exploitation-heavy rungs; Exploiter agents should get known-sequence rungs only.

**Files**:
- `decision_rung_system.py` — `_select_ordering_for_context()` and rung evaluation
- `agent_operating_mode_system.py` — role assignments

**Approach**:
Add role-based filtering in `_select_ordering_for_context()`:
```python
agent_role = context.get('agent_role', 'pioneer')
if agent_role == 'exploiter':
    return 'minimal'  # Only proven strategies
elif agent_role == 'optimizer':
    return 'efficiency'  # Exploit known patterns, some exploration
elif agent_role == 'pioneer':
    return 'comprehensive'  # Full exploration + all hypotheses
```

**Impact**: Different agents explore the strategy space differently. Pioneers try everything; Optimizers refine what works; Exploiters execute proven sequences. Natural division of labor.

---

### Fix 3.3: World Model Persistence Across Sessions

**Seal Violated**: AMNESIA (Seal 2)
**Q&A Source**: Q9 — "Cross-domain knowledge transfer"
**Diagnosis**: `context_builder._world_model` (causal map of click effects, spatial relationships, constraint states) is built during each game session but lost at session end. `evolution_runner.py` tries to extract it via `getattr(self.context_builder, '_world_model', None)` but this is fragile. The `result_recorder.py` has `_persist_world_model()` (lines 195-203) but the data reaching it is incomplete.

**Files**:
- `context_builder.py` — `self._world_model`
- `game_player.py:1174-1185` — world model extraction
- `result_recorder.py:195-203` — `_persist_world_model()`
- `world_model_states` DB table

**Fix**:
1. At game end, serialize full `_world_model` dict and pass to `result_recorder`
2. At game start, load previous world model from DB for this agent+game pair
3. Merge with fresh observations (don't overwrite — accumulate)

**Impact**: Agents build cumulative understanding of each game across sessions. An FT09 agent that discovered "clicking cell (3,4) turns it blue" retains this knowledge next game.

---

### Fix 3.4: Cross-Game Structural Transfer

**Seal Violated**: ISOLATION (Seal 6) + HOARDING (Seal 5)
**Q&A Source**: Q9 — "Architecture-level cross-domain transfer"
**Diagnosis**: Currently each game is completely isolated. But structural principles DO transfer: "clicking changes local state" (FT09) and "clicking changes global state" (VC33) share the same causal structure. An agent that learns click-effect causality in FT09 should bootstrap faster in VC33.

**Approach** (medium-term, lab orchestrator territory):
- Extract game-agnostic structural principles from world models
- "I click position X, pixels change at positions Y, Z" is transferable
- Store as agent-level meta-knowledge, not game-specific knowledge
- Genome evolution can select for structural learning ability

**Implementation Note**: This fix should be designed but NOT implemented until Fixes 1.1-1.4 and 2.1-2.4 are validated. The lab orchestrator should control when to enable cross-game transfer.

---

### Fix 3.5: Remove Dead Code Branches

**Seal Violated**: STASIS (Seal 7)
**Diagnosis**: Multiple dead code paths create confusion and maintenance burden:

1. `evolutionary_engine.py` — `_calculate_specialist_fitness()` (specialist_mode always False)
2. `engines/postgame/fitness_calculator.py` — entire module if not reconnected (Fix 2.1)
3. `engine_registry.py` — 40+ engines registered but never instantiated
4. `core_gameplay.py` — deprecated, replaced by GamePlayer

**Approach**: Mark each with `# DEPRECATED: [reason]` comment for now. Remove only after verifying no lab orchestrator code references them. Dead code removal is lower priority than fixing live wires.

---

## TIER 4: FUTURE (Lab Orchestrator Territory)

These are insights from the Q&A that should inform the lab orchestrator's hypothesis generation, NOT be hardcoded:

### 4.1: Endpoint-First Puzzle Solving (Q7)
For FT09: Pre-compute the solved state from level observation, then measure proximity to solution as fitness. This inverts the current "explore-then-evaluate" paradigm. The lab orchestrator should test this as a hypothesis.

### 4.2: Phase Model Inversion for Constraint Games (Q10)
The Matryoshka sequential phase model (explore → exploit → optimize) may need to be INVERTED for constraint-satisfaction games: start with the answer, work backward to find the path. The lab orchestrator should test this as an alternative phase ordering.

### 4.3: Genre-Specific Solver Architecture (Q8)
The deepest insight: FT09 may need a fundamentally different solving approach than evolutionary search. Constraint-satisfaction problems have known algorithmic solutions (backtracking, SAT solvers). The lab orchestrator should be able to hypothesize and test a solver swap.

---

## Implementation Order

```
Phase 1: Unblock FT09/VC33 (Tier 1, estimated: 4 fixes)
  1.1  Wire Action6BehaviorEngine writes into production loop
  1.2  Game-type-specific meaningful_change detection
  1.3  Re-enable stuck_count for ACTION6 games
  1.4  Add action6_only to ORDERING_PRESETS

Phase 2: Fix Evolution Signal (Tier 2, estimated: 4 fixes)
  2.1  Reconnect FitnessCalculator
  2.2  Dynamic EXPLORATION->OPTIMIZATION transition
  2.3  Meta-learning bootstrap for zero-score games
  2.4  Wire meaningful_change into rung context

Phase 3: Structural Alignment (Tier 3, after Phase 1+2 validated)
  3.1  Per-game fitness functions
  3.2  Role-based rung filtering
  3.3  World model persistence across sessions
  3.4  Cross-game structural transfer (design only)
  3.5  Dead code cleanup

Phase 4: Lab Orchestrator Hypotheses (Tier 4, orchestrator-driven)
  4.1  Endpoint-first puzzle solving
  4.2  Phase model inversion
  4.3  Genre-specific solver swap
```

---

## Antilife Equation Seal Violation Summary

| Seal | Violation Count | Key Locations |
|------|----------------|---------------|
| **Amnesia** (2) | 5 | stuck_count disabled, world model lost, meaningful_change not in rungs, Action6Behavior never written, frame_changed always True |
| **Monolith** (1) | 3 | One meaningful_change for all games, one fitness function for all games, one rung ordering for all games |
| **Isolation** (6) | 3 | Action6BehaviorEngine orphaned, FitnessCalculator orphaned, cross-game transfer absent |
| **Stasis** (7) | 2 | EXPLORATION->OPTIMIZATION static, dead code accumulation |
| **Hierarchy** (3) | 1 | All agents get same rungs regardless of role |
| **Monopoly** (4) | 1 | Meta-learning fitness monopolized by score-based proxy |
| **Hoarding** (5) | 1 | World model knowledge not shared across sessions |

**Total**: 16 violations across all 7 Seals.

---

## Relationship to Lab Architecture

Per user instruction: the lab concept is preserved. These fixes "get the system right first" — they repair the broken data flows, reconnect orphaned engines, and differentiate game-type handling. Once these are in place, the lab orchestrator has a working system to make informed hypotheses against, rather than tuning dials that aren't connected to anything.

The lab orchestrator should then be able to:
- Generate hypotheses about FT09-specific fitness functions (Tier 4.1)
- Test phase model variations (Tier 4.2)
- Propose genre-specific solver swaps (Tier 4.3)
- All without needing to fix dead wires first

---

## Q&A Answer Index

| Q# | Domain | Rating | Key Insight | Applied In |
|----|--------|--------|-------------|------------|
| Q1 | Orphan detection | 9/10 | Load-bearing absence vs missing wire | Fix 1.1, 2.4 |
| Q2 | Progress measurement | 9/10 | Three-axis model (Knowledge/Want/Capability) | Fix 1.2, 1.3 |
| Q3 | Activity vs development | 8/10 | Wound-contact metric for real progress | Fix 1.2 |
| Q4 | Orphan detection | 7/10 | Archetype role + reference contradiction test | Fix 3.5 |
| Q5 | Fix portability | 8/10 | Reliability vs resolution layer distinction | Fix 1.2 context |
| Q6 | Flat landscape | 9/10 | Role-assigned fitness partitioning | Fix 2.1, 3.2 |
| Q7 | Combinatorial value | 10/10 | Endpoint-first declaration | Fix 3.1, 4.1 |
| Q8 | Genre incompatibility | 10/10 | Don't adapt — replace the method | Fix 1.4, 4.3 |
| Q9 | Cross-domain transfer | 7/10 | Architecture-level transfer, not solution-level | Fix 3.3, 3.4 |
| Q10 | Phase model validity | 9/10 | Phase model as modifiable character | Fix 2.2, 4.2 |
