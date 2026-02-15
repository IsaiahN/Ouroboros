# IMPLEMENTATION PLAN: Closing the 5 Cognitive Gaps
**Date**: 2026-02-15
**Priority**: CRITICAL -- these gaps prevent real learning
**Scope**: Changes to PTMA loop, context builder, feedback pipeline, cognitive loop

---

## THE 5 GAPS

| # | Gap | Impact | Current State |
|---|-----|--------|---------------|
| 1 | Goal-State Representation | Agents don't know what "winning" looks like | `extract_goal_state()` exists in context_builder but returns None for all 3 games |
| 2 | Difference-from-Goal Computation | Can't compute "what needs to change" | No delta computation wired into PTMA PERCEIVE phase |
| 3 | Combinatorial Planning | Can't plan multi-step action sequences | PTMA ACT phase picks one action at a time, no lookahead |
| 4 | Broken Feedback Signal | `action_effectiveness.avg_score_impact` = 0.000 for everything | Score only changes on level completion; frame-change is the real signal |
| 5 | State Tracking | No internal representation of mutable game state | LS20 key (shape/color/rotation) changes are invisible to the agent |

---

## GAP 1: GOAL-STATE REPRESENTATION

### Problem
The agent takes actions but has no representation of "what does the world look like when I've won?" Without a goal, you can't plan toward it. Every action is equally plausible.

Each game has a different goal structure:
- **FT09**: Key constraint sprites (`bsT` tag) encode what color each neighboring tile should be. The center pixel of each constraint = the target color. The 0/non-0 pattern around it = which positions must match vs not-match.
- **LS20**: The lock symbol at the top of the screen shows the target key configuration (shape + color + rotation). The agent must modify their carried key to match it.
- **VC33**: Passengers (`HQB` tag) have colored bases. Destination markers (`fZK` tag) have matching colors. Passengers must be on lanes reaching their color destination.

### What Exists
`ContextBuilder.extract_goal_state()` exists at line ~1181 of context_builder.py. It tries to find a "reference panel" and compare it to the current state. But:
- It relies on `reference_panel_idx` from VisualCortex, which returns None for all 3 games
- It's frame-diffing based (pixel comparison), not semantic
- It doesn't understand constraint patterns, lock symbols, or color-matching goals

### Implementation Plan

**Phase 1A: Frame-Derived Goal Extraction (no game-specific logic)**

Instead of trying to parse game semantics, teach the agent to identify "stable reference regions" -- areas of the frame that DON'T change when actions are taken.

```
Location: cognitive_loop.py -> _perceive() phase
New method: _identify_reference_regions(frames_history)

Logic:
  After N actions (e.g., 5), compare all collected frames.
  Regions that NEVER changed = likely reference/goal display.
  Regions that DID change = likely interactive workspace.
  Store reference_region_pixels as the "goal snapshot."
```

**Phase 1B: Goal-State Differencing**

Once we have a reference region identified:
```
Location: cognitive_loop.py -> _perceive() -> add to Percept
New field: Percept.goal_delta

Logic:
  For each interactive region:
    Compare current pixels to corresponding reference region pixels.
    Identify cells where current != reference.
    goal_delta = list of (position, current_color, target_color)
```

**Phase 1C: Goal Completion Tracking**

```
Location: cognitive_loop.py -> CognitiveFrame
New fields:
  cf.goal_cells_total: int    # Total cells that must match
  cf.goal_cells_correct: int  # Currently matching cells
  cf.goal_progress: float     # correct / total

This becomes the PRIMARY feedback signal -- not score, not frame-change,
but "am I getting closer to the goal?"
```

### Key Design Constraint
This must work WITHOUT game-specific knowledge. The agent discovers the goal structure from observation. If it sees 4 mini-puzzles with constraint patterns, it doesn't need to know they're "constraints" -- it just needs to notice "these pixels never change, those pixels do, and when the changing ones match the stable ones, good things happen."

### Files to Modify
- `cognitive_loop.py`: Add reference region detection to PERCEIVE, goal delta to CognitiveFrame
- `context_builder.py`: Enhance `extract_goal_state()` with frame-history approach
- `engines/perception/visual_cortex.py`: Add stable-region detection method

---

## GAP 2: DIFFERENCE-FROM-GOAL COMPUTATION

### Problem
Even if the agent could identify the goal state, it currently has no mechanism to compute "what specific changes need to happen?" The system sees the frame holistically rather than as a set of discrete state variables.

### What Exists
- CausalMap records "clicking position X changed pixel Y from color A to color B"
- Frame differencing exists in the temporal perception channel
- But these are disconnected from goal-awareness

### Implementation Plan

**Phase 2A: Cell-Level State Abstraction**

Before computing deltas, we need to abstract the frame into discrete state variables:

```
Location: cognitive_loop.py -> new method _abstract_frame_state()

For click games (FT09, VC33):
  Detect the grid of interactive objects (tiles/sprites).
  For each object: record (position, primary_color).
  State = dict of {position: color}

For movement games (LS20):
  Detect agent position, key display, lock display.
  State = {agent_pos, key_shape, key_color, key_rotation, lock_config}
```

**Phase 2B: Delta Computation**

```
Location: cognitive_loop.py -> _think() phase
New computation in _derive_strategy():

  current_state = _abstract_frame_state(current_frame)
  goal_state = _abstract_frame_state(reference_region) # or inferred goal

  delta = {}
  for pos in goal_state:
    if current_state.get(pos) != goal_state[pos]:
      delta[pos] = (current_state[pos], goal_state[pos])

  cf.goal_delta = delta
  cf.cells_remaining = len(delta)
```

**Phase 2C: Wire Delta into Strategy Selection**

```
In _derive_strategy():
  if cf.cells_remaining == 0:
    return "wait"  # We might have won, let the game confirm
  if cf.cells_remaining <= 3:
    return "exploit"  # Close to goal, use known causal rules
  if cf.cells_remaining > cf.goal_cells_total * 0.7:
    return "explore"  # Far from goal, need more causal knowledge
  else:
    return "experiment"  # Medium distance, test hypotheses
```

### Files to Modify
- `cognitive_loop.py`: Add state abstraction, delta computation, strategy integration
- `context_builder.py`: Add delta fields to Percept/CognitiveFrame

---

## GAP 3: COMBINATORIAL PLANNING

### Problem
The agent picks one action per cycle. It has no concept of "if I do A then B then C, I'll reach the goal." For FT09 with 2-color tiles, each tile needs 0 or 1 click -- the entire solution is computable once you know the delta. For LS20, pathfinding to modifiers requires multi-step planning.

### What Exists
- CausalMap stores per-position effects
- MAPPED speed in PTMA ACT phase can follow a plan
- But no plan-generation mechanism exists

### Implementation Plan

**Phase 3A: CausalMap Plan Generator**

```
Location: New method in CausalMap or cognitive_loop.py

Given:
  - goal_delta: {pos: (current_color, target_color)}
  - causal_rules: {pos: {action -> effect}}

Compute:
  plan = []
  for pos, (current, target) in goal_delta.items():
    # How many clicks to cycle current -> target?
    if pos in causal_rules:
      color_cycle = causal_rules[pos].color_list  # e.g., [9, 8] or [9, 8, 12]
      if current in color_cycle and target in color_cycle:
        steps = (color_cycle.index(target) - color_cycle.index(current)) % len(color_cycle)
        for _ in range(steps):
          plan.append(('click', pos))

  return plan
```

**Phase 3B: Plan Execution in PTMA ACT**

```
Location: cognitive_loop.py -> _act() phase

When strategy == "exploit" and a plan exists:
  action_speed = "MAPPED"
  next_step = plan.pop(0)
  execute(next_step)

When plan is empty:
  Re-perceive, re-compute delta, generate new plan if needed
```

**Phase 3C: Movement Planning for LS20**

```
For movement games:
  - BFS/A* pathfinding from agent position to target
  - Target selection: nearest unvisited modifier, or nearest lock position
  - Walls learned from "moved but position didn't change" = blocked
  - Plan = sequence of directional actions to reach target
```

### Key Design Constraint
Plans must be SHORT and re-evaluated frequently. The agent should plan 3-5 steps ahead, execute, re-perceive, re-plan. Not compute the entire game solution upfront (that's brittle to any misunderstanding).

### Files to Modify
- `cognitive_loop.py`: Plan generation in MAP phase, plan execution in ACT phase
- CausalMap: Add `generate_plan(goal_delta)` method
- New pathfinding utility for movement games

---

## GAP 4: BROKEN FEEDBACK SIGNAL

### Problem
`action_effectiveness` records `avg_score_impact = 0.000` for all actions across all games because score only changes on level completion. The agents literally cannot distinguish between productive and wasted actions.

The REAL signal is **frame change** -- specifically, **change in the direction of the goal**. Three tiers of signal quality:

1. **Frame changed at all**: Basic -- "this action did something" (currently tracked but not fed back to learning)
2. **Frame changed toward goal**: Better -- "this action was productive"
3. **Goal-delta decreased**: Best -- "this action reduced the number of cells still needing change"

### What Exists
- `notify_action_complete(pre_frame, post_frame, action, coordinates)` fires after each action
- Rungs have `on_action_complete` hooks
- But the signal is: did frame change? Yes/No. Not: did it change TOWARD the goal?

### Implementation Plan

**Phase 4A: Rich Action Outcome Signal**

```
Location: cognitive_loop.py -> after each action

Replace binary frame_changed with:
  action_outcome = {
    'frame_changed': bool,
    'pixels_changed': int,
    'goal_delta_before': int,  # cells wrong before action
    'goal_delta_after': int,   # cells wrong after action
    'goal_progress': int,      # delta_before - delta_after (positive = good)
    'was_productive': bool,    # goal_progress > 0
    'was_destructive': bool,   # goal_progress < 0
    'was_neutral': bool,       # goal_progress == 0 but frame changed
    'was_wasted': bool,        # frame didn't change at all
  }
```

**Phase 4B: Feed Signal into CausalMap**

```
Location: CausalMap update after each action

Instead of just recording "click at (x,y) changed color A->B":
  Record: "click at (x,y) changed color A->B AND moved goal_progress by +1"

This lets the planner know which actions are USEFUL, not just which have effects.
```

**Phase 4C: Replace action_effectiveness Metric**

```
Location: outcome_processor.py or result_recorder.py

New metric: action_productivity
  = count of goal_progress > 0 actions / total actions

This replaces avg_score_impact as the learning signal.
Write to database so it persists across generations.
```

**Phase 4D: Confidence Decay from Wasteful Actions**

```
Location: Rung system confidence updates

When a rung produces an action with was_wasted=True:
  rung.confidence *= 0.8  # Rapid decay for useless actions

When a rung produces was_productive=True:
  rung.confidence = min(1.0, rung.confidence * 1.2)  # Reward

This naturally kills rung monopolies -- a rung that keeps
producing zero-change actions will lose confidence fast.
```

### Files to Modify
- `cognitive_loop.py`: Rich action outcome computation
- `cognitive_game_player.py`: Pass goal-aware feedback to notify_action_complete
- CausalMap: Store goal-progress alongside effects
- `decision_rung_system.py`: Goal-aware confidence updates
- `outcome_processor.py`: New productivity metric

---

## GAP 5: STATE TRACKING

### Problem
The agent has no internal representation of mutable game state beyond the raw frame. In LS20, the agent's "key" (shape, color, rotation) changes when walking over modifier tiles. The agent doesn't track this -- it walks over a modifier and doesn't register that its key changed.

### What Exists
- Frame-to-frame differencing in temporal perception channel
- CausalMap records position-based effects
- But nothing says "my carried object changed from Shape-A-Red-0deg to Shape-B-Red-0deg"

### Implementation Plan

**Phase 5A: HUD State Extraction**

Many games display mutable state in a HUD (health bar, key display, score counter, timer). Teach the agent to extract this:

```
Location: cognitive_loop.py -> _perceive() phase
New method: _extract_hud_state(frame)

Logic:
  Identify HUD region (typically edges/corners of the frame).
  On FT09: bottom row = timer bar (orange/yellow pixels)
  On LS20: bottom-left = key display, bottom-right = lives/timer
  On VC33: top row = timer bar

  Extract:
    - Timer remaining (count of colored pixels in timer region)
    - Key/tool display (small sprite region, extract colors + shape)
    - Lives remaining (count of colored indicators)
```

**Phase 5B: State Change Detection**

```
Location: cognitive_loop.py -> after each action

Compare hud_state_before and hud_state_after:
  If key display changed: record "my key changed to [new config]"
  If timer changed: record urgency level
  If lives changed: record "DANGER -- lost a life"

Feed state changes into CausalMap:
  "Walking over position (X,Y) changed my key from A to B"
```

**Phase 5C: State Variables in CognitiveFrame**

```
New fields in CognitiveFrame:
  cf.timer_remaining: float      # 0.0 to 1.0
  cf.timer_urgency: str          # 'safe', 'moderate', 'critical'
  cf.carried_state: dict         # Extracted key/tool properties
  cf.carried_state_changed: bool # Did it change this step?
  cf.lives_remaining: int
```

**Phase 5D: State-Aware Strategy**

```
In _derive_strategy():
  if cf.timer_urgency == 'critical':
    return "exploit"  # No time to explore, use best known actions
  if cf.carried_state_changed:
    # Something about me changed -- re-evaluate goal match
    check if new state matches any target
    if match found: navigate to target for delivery
```

### Files to Modify
- `cognitive_loop.py`: HUD extraction, state tracking, state-aware strategy
- `context_builder.py`: Add state fields to CognitiveFrame/Percept
- CausalMap: Store "environmental state changes" (not just pixel changes)

---

## IMPLEMENTATION ORDER

These gaps have dependencies. Implementation order:

```
Phase 1: FEEDBACK SIGNAL (Gap 4A-4B)
  Why first: Without a signal, nothing else can learn.
  Scope: cognitive_loop.py action outcome computation.
  Test: After 1 generation, verify action_outcomes have non-zero goal_progress.

Phase 2: STATE TRACKING (Gap 5A-5C)
  Why second: State extraction feeds into goal detection.
  Scope: HUD extraction, state change detection.
  Test: Verify LS20 key changes are detected, timer tracked.

Phase 3: GOAL-STATE REPRESENTATION (Gap 1A-1C)
  Why third: Needs stable-region detection which needs several frames.
  Scope: Reference region identification, goal delta computation.
  Test: Verify FT09 constraint patterns identified, delta computed.

Phase 4: DELTA COMPUTATION (Gap 2A-2C)
  Why fourth: Builds on goal representation.
  Scope: Cell-level abstraction, delta-aware strategy.
  Test: Verify goal_cells_remaining decreases as agent acts productively.

Phase 5: PLANNING (Gap 3A-3C)
  Why last: Needs everything above to generate useful plans.
  Scope: CausalMap plan generation, plan execution.
  Test: Verify agent follows a computed plan for FT09 L1.
```

Estimated scope per phase: ~100-200 lines of code each. Total: ~600-1000 lines.

---

## SUCCESS CRITERIA

After all 5 phases:
- FT09 L1 solved in <30 actions (baseline: 15, current: 118 avg when winning at all)
- LS20 L1: Agent tracks key state, navigates to modifiers intentionally
- VC33 L1: Agent identifies which switch to click based on goal-color matching
- `action_effectiveness` shows non-zero `goal_progress` for productive actions
- Agents don't need sequences for L1 of any game -- they compute the solution

---

## WHAT THIS DOES NOT DO (BY DESIGN)

- Does NOT tell agents the game rules
- Does NOT hardcode game-specific logic
- Does NOT use LLM reasoning to solve the games
- Every mechanism is general-purpose: "find stable regions", "compute deltas", "plan from causal rules"
- The agents must still DISCOVER that clicking toggles colors, that walking over tiles changes keys, that switches move fluid

The discovery happens through interaction. These 5 gaps just give the agents the cognitive machinery to USE what they discover.
