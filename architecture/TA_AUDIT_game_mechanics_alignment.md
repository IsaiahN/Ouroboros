# TA AUDIT: Game Mechanics Alignment & System Capability Assessment
**Date**: 2026-02-15
**Author**: Claude (Technical Architect / Scaffolding Intelligence)
**Scope**: Honest assessment of what I got wrong, what the codebase gets wrong, what works, what doesn't, and what's needed for real-time observation

---

## SECTION 1: WHAT I GOT WRONG ABOUT THE GAMES

### FT09 — "Color Tile Puzzle" (NOT "Lights Out")

**My Initial Analysis**: I called this "Lights Out Color Cycling Puzzle" — implying neighbor propagation, where clicking one tile affects adjacent tiles.

**What's Actually Happening**:
- Each tile click affects ONLY that tile. No neighbor propagation for standard tiles (`Hkx` class).
- The game has **four mini-puzzles** visible in the 32x32 grid. The 16x16 camera viewport means actions 1-4 PAN the camera to focus on different quadrants.
- **Constraint sprites** (`bsT` tag) sit between tiles and encode the TARGET color for the adjacent interactive tile. The center pixel of each constraint sprite = the color that tile should become.
- **Multiple color palettes** per level (`cwU` parameter). Tiles cycle through their palette on click.
- **Some tiles have special kernels** — the `NTi` (non-trivial) class tiles DO affect neighbors based on their pixel pattern. But the basic `Hkx` tiles are self-contained. I conflated these two mechanics.
- **Action 6 is NOT the only action.** FT09 reports `available_actions = [1, 2, 3, 4, 5, 6]`. Actions 1-4 control the camera. This is CRITICAL because some levels require panning to access all puzzles.
- **Level progression changes mechanics.** Higher levels can add new tile types, change palettes, add NTi tiles with neighbor effects. Level 1 is deliberately simple.

**Impact on Codebase**: The copilot-instructions.md (line 406) says `available_actions=[6]` for FT09. This is FALSE. This false assumption may have guided multiple development decisions. It MUST be corrected.

### VC33 — "Fluid Dynamics" (NOT "Factory Sorting")

**My Initial Analysis**: I called this "Conveyor Belt Sorting Puzzle" — implying a factory with conveyor belts moving boxes to destinations.

**What's Actually Happening**:
- This is a **fluid dynamics simulation** with a rotated axis (the game developers deliberately rotated the gravity axis to prevent LLMs from inferring the physics from screenshots).
- "Conveyors" are actually **fluid chambers**. The `TiD` direction vector controls flow direction.
- "Membranes" (`qoD` class) are permeable boundaries between chambers. Their permeability is controlled by switches.
- "Passengers" (`HQB`) are objects floating/sinking in the fluid. They need to reach chambers matching their color.
- Clicking switches (`action 6`) changes membrane permeability, which changes fluid flow, which moves passengers.
- The system is inherently DYNAMIC — fluid continues to flow after an action. The agent must understand state evolution over time, not just instant cause-effect.
- This explains why VC33 has 0 wins across 5,000+ generations. The game requires understanding delayed consequences (fluid takes time to move passengers), not just direct click-effect mappings.

**Why This Is Hard for the Current Architecture**: The CausalMap assumes instant causation — "I clicked X, pixel Y changed." In VC33, clicking a switch changes membrane state, which changes fluid flow, which EVENTUALLY moves a passenger 10+ frames later. The cause-effect chain has temporal delay. The current causal learning can't represent this.

### LS20 — "Locksmith" (NOT "Deliver the Shape")

**My Initial Analysis**: I called it "Deliver the Shape Navigation Puzzle" — right spirit, wrong specifics.

**What's Actually Happening**:
- Agent navigates a maze carrying a "key" (visible in HUD).
- The key has properties: shape, color, rotation.
- The maze contains modifier tiles that change key properties when walked over:
  - Shape changers: transform the key's outline
  - Color changers: change the key's color
  - Rotation modifiers: rotate the key
- The "lock" is displayed at a fixed location (top of screen). It shows the TARGET configuration.
- The agent must find the RIGHT modifiers, in the RIGHT order, to transform their key to match the lock.
- Then navigate to the exit with the matching key.
- Timer pressure + limited lives (3). Battery pickups extend timer.
- Higher levels add fog-of-war (limited visibility) and more complex modifier chains.

**Why This Is the Hardest Game**: It requires:
1. State tracking (key configuration changes)
2. Goal recognition (lock = target)
3. Exploration under time pressure (find modifiers)
4. Sequential planning (modifier A then B, not B then A)
5. Spatial memory (remember where modifiers are)
6. Resource management (timer, lives)

The current agent has NONE of these capabilities beyond basic spatial exploration.

---

## SECTION 2: WHAT THE CODEBASE GETS WRONG

### 2.1 copilot-instructions.md — False Claims

| Line | Claim | Reality | Severity |
|------|-------|---------|----------|
| 406 | `FT09's available_actions=[6]` (click-only) | FT09 has `[1,2,3,4,5,6]` — it's a hybrid game | **CRITICAL** |
| 547 | `FT09 (click game, 6 levels)` | FT09 is a hybrid game with camera pan + click | MEDIUM |
| 482 | `clicking same spot → coordinate fixation` referring to FT09's 9-cell grid | FT09 has a 32x32 grid with 16x16 viewport, not 9 cells | MEDIUM |
| 482 | `>=5 unique positions per game session` for FT09 | Should be MORE — FT09 has dozens of interactive tiles | LOW |
| 547 | `VC33 (click game, 7 levels)` description | Correct on available_actions, but missing the temporal-delay issue | LOW |

**Recommendation**: Fix lines 406 and 547. Remove the false FT09 = click-only references. Update Part 5 game descriptions to reflect corrected understanding.

### 2.2 classify_puzzle_type() — Partially Correct

In `context_builder.py` line ~1128, `classify_puzzle_type()` classifies based on available actions:
- If only directional (1-4): `movement_maze`
- If only click (5-6): `click_toggle` or `click_transform`
- If both: `hybrid`

FT09 will correctly classify as `hybrid` because it has all 6 actions. This is GOOD — the classifier works correctly despite the copilot-instructions being wrong. However:

- `hybrid` has no special handling in the codebase. It just falls through as "both click and movement available."
- There's no concept of "camera-panning hybrid" vs "movement + interaction hybrid." These are VERY different.
- The agent doesn't understand that actions 1-4 in FT09 pan the camera (changing the visible region) rather than moving an agent through a world.

**Recommendation**: Don't add game-specific classification. Instead, let the agent DISCOVER that actions 1-4 produce "the whole frame shifted" vs "one object moved." This is a learnable distinction — it's a frame-level vs object-level change.

### 2.3 action_effectiveness — Dead Metric

The `action_effectiveness` table records `avg_score_impact` for each action type per game. But score only changes on level completion. So every action shows `0.000` impact. This is the equivalent of measuring a student's GPA after each sentence they read — the granularity is wrong.

The real signal is frame change, specifically goal-directed frame change (see Implementation Plan Gap 4).

### 2.4 CausalMap — Missing Temporal Dimension

The CausalMap records: "at step T, action A at position P changed pixel Q from color C1 to C2."

This works for FT09 (instant effect) and LS20 (movement is instant). But for VC33, the causal chain is:
```
Step T:   Click switch S → membrane M opens
Step T+1: Fluid flows through M
Step T+5: Passenger P moves to new chamber
Step T+8: Passenger P reaches destination
```

The CausalMap at step T records: "clicked S, some pixels near S changed." It does NOT record: "5 steps later, passenger P moved." The temporal gap between cause and effect breaks the causal learning pipeline.

**Recommendation**: Add a "delayed observation" window to the CausalMap. After each action, observe frames for N additional steps (maybe 3-5) and attribute changes within that window to the action. This is a temporal smearing of the causal signal, and it's how humans learn delayed-effect systems too — you click the switch and WATCH what happens.

### 2.5 Agent Knowledge — Partially Correct but Shallow

Database audit from last session shows:

**FT09 learned knowledge**:
- "I can toggle 3 objects by clicking" → Correct! Tiles do toggle.
- "I know 8 positions that change colors" → Correct! Tiles change colors on click.
- But: no understanding of WHICH color each tile SHOULD be. No goal awareness.

**LS20 learned knowledge**:
- "I control 2 moveable and 2 toggleable objects" → Wrong. There's 1 moveable object (the agent). No toggleable objects in the LS20 interaction model.
- The agent conflated different games' knowledge or misattributed observations.
- 0 wins in recent memory, suggesting correct spatial reasoning hasn't developed.

**VC33 learned knowledge**:
- Essentially nothing. 0 wins ever. 0 meaningful causal rules learned.
- The temporal-delay problem means the agent never connects its actions to outcomes.

---

## SECTION 3: WHAT THE ARCHITECTURE GETS RIGHT

Despite the gaps, the theoretical architecture has real strengths that shouldn't be thrown away:

### 3.1 The PTMA Loop Is Sound
Perceive → Think → Map → Act is the correct cognitive loop. The problem isn't the loop structure — it's that each phase is incomplete:
- PERCEIVE doesn't extract goal state
- THINK doesn't compute goal delta
- MAP doesn't plan
- ACT doesn't track state changes

The loop itself is fine. Fill in the phases.

### 3.2 The CausalMap Concept Is Right
The idea that "each position has learned effects" is exactly correct. The implementation just needs:
- Goal-directedness (which effects move toward the goal?)
- Temporal extension (delayed effects for VC33)
- State context (effects may differ based on carried state in LS20)

### 3.3 The Dual Economy Is Right
ATP and Prestige separation prevents perverse incentives. This is working as designed.

### 3.4 The Evolutionary Selection Is Right
Population-based evolution with breeding, mutation, and knowledge transfer is the correct meta-learning approach. But evolution can only select for what agents CAN express. If agents can't represent goals, evolution can't select for goal-directed behavior.

### 3.5 The Event Bus Architecture Is Right
Pub/sub decoupling lets components evolve independently. This is architecturally sound and should be preserved.

### 3.6 Agent Knowledge Persistence Is Right
The three-layer genome/epigenetic/somatic model is correct. Knowledge survives agent death through database persistence. But what's being persisted is too shallow — "I can click things" rather than "clicking tile X when it's blue makes it red, and the constraint says it should be red."

---

## SECTION 4: THE REAL-TIME OBSERVATION PROBLEM

### 4.1 Why We Need It

The current feedback loop for system improvement is:
```
Run N generations → Read log file → Try to infer what happened → Make changes → Repeat
```

This is like debugging a program by reading its stdout from yesterday. We need:
```
Watch agent in real-time → See frame + action + state → Notice learning moments → Tag for analysis
```

### 4.2 What Human Observers Need

A human watching an agent should see:
1. **The current frame** rendered as a color image (64x64 or 32x32 with colors mapped to visible palette)
2. **The agent's action** on each step (which action, which coordinates, why)
3. **Frame diff** highlighted (what changed from last action)
4. **Goal state** if identified (reference region, current delta)
5. **Agent's internal state** (strategy, confidence, active rung, plan if any)
6. **Key metrics** updating live (goal_progress, actions_taken, level, score)
7. **Ability to annotate** — human can write notes tagged to specific step/frame

### 4.3 What the LLM Observer Needs

When I (Claude) observe, I need:
1. **Frame data as grid** — 2D array of color values, compact enough to reason about
2. **Action history** — last 10 actions with outcomes
3. **Agent's causal model** — what rules does the agent think it knows?
4. **Goal representation** — what does the agent think the goal is?
5. **Surprise events** — moments when the frame changed unexpectedly or a level completed
6. **Database query access** — to check what was persisted vs what was lost

### 4.4 Implementation Proposal: Observer Dashboard v2

Three-tier approach:

**Tier 1: Logging Tier (Minimal Effort, Immediate Value)**

Structured JSON-Lines log of each action step, written during game play:

```python
# In cognitive_game_player.py, after each action:
import json, datetime

observation_record = {
    "timestamp": datetime.datetime.now().isoformat(),
    "agent_id": agent.id,
    "game_id": game_id,
    "generation": generation,
    "step": step_number,
    "level": current_level,
    "action": {"type": action_type, "x": x, "y": y},
    "frame_hash": hash(frame.tobytes()),
    "frame_changed": bool,
    "goal_progress": goal_delta_count,
    "strategy": strategy_name,
    "active_rung": rung_name,
    "confidence": confidence,
    "carried_state": carried_state_dict,
}

# Write to a ring-buffer file (overwrite after N entries)
with open("observation_log.jsonl", "a") as f:
    f.write(json.dumps(observation_record) + "\n")
```

This gives both human and LLM a detailed record to analyze after runs.

**Tier 2: Snapshot Tier (Moderate Effort, Frame Capture)**

Save actual frames at key moments:

```python
# Key moments to capture:
# - First action of each level
# - Any action that changed goal_progress
# - Level completion
# - Game over
# - Every Nth action (e.g., every 10th)

from engines.perception.visual_cortex import VisualCortex
cortex = VisualCortex()

# Save as compact numpy array (not PNG — too slow)
snapshot = {
    "step": step,
    "frame": frame.tolist(),  # 2D list of ints
    "goal_frame": goal_frame.tolist() if goal_frame else None,
    "action_outcome": outcome,
}
# Store in database or append to snapshots file
```

**Tier 3: Live Streaming Tier (Higher Effort, Real-Time)**

WebSocket-based live dashboard:

```
Architecture:
  cognitive_game_player.py → publishes via event bus → WebSocket server
  Browser client → connects to WebSocket → renders frames + metrics

Components:
  1. WebSocket server (simple asyncio, runs in background thread)
  2. HTML/JS client with:
     - Canvas rendering the game frame (color-mapped)
     - Side panel with metrics, action history, state
     - Annotation input field (human can type notes per step)
  3. Event bus integration (GAME_STEP event triggers broadcast)
```

**Recommendation**: Start with Tier 1 immediately (zero infrastructure, just structured logging). Move to Tier 2 when debugging specific games. Build Tier 3 when the system is stable enough that real-time observation is more useful than code fixes.

### 4.5 LLM-Driven Observation Sessions

For me (Claude) to observe agents in real-time during development sessions:

```
Protocol:
  1. Human starts a generation with --observe flag
  2. System writes observation_log.jsonl during play
  3. After each game (or on-demand), I read the log
  4. I analyze the sequence of actions, frame changes, decisions
  5. I write observations to an observations/ folder as dated MD files
  6. I identify specific moments where the agent made a learning error
  7. I propose targeted fixes based on observed behavior, not guesses
```

This creates a discipline: DON'T fix what you haven't observed. Every fix should be traceable to a specific observed agent behavior that was suboptimal.

---

## SECTION 5: CAPABILITY GAPS VS. ARCHITECTURAL GAPS

Important distinction:

### Capability Gaps (What agents can't do yet)
- Represent goals
- Compute deltas
- Plan sequences
- Track carried state
- Learn from delayed effects

These are fixed by implementing the 5 gaps in the Implementation Plan.

### Architectural Gaps (What the codebase structure prevents)
- **No temporal causal learning**: CausalMap is instant-effect only
- **No camera-awareness**: Agent doesn't know actions 1-4 pan the view vs move an agent
- **No HUD parsing**: Timer, lives, key display are invisible to the agent
- **No re-planning**: Once an action is chosen, there's no "wait, that made things worse" recovery
- **Dead metrics**: action_effectiveness measures the wrong thing

The capability gaps are easier to fix (add code). The architectural gaps require understanding the codebase deeply and modifying core data structures.

---

## SECTION 6: HONEST ASSESSMENT — CAN THIS SYSTEM LEARN?

### Given the corrections, can the current architecture achieve the prime mission?

**Short answer: Yes, but not without the 5 gaps filled.**

The architecture is sound at the theory level. PTMA is the right loop. CausalMap is the right memory. Evolutionary selection is the right meta-learning. The database-as-organism is the right persistence model.

But the implementation is approximately 40% complete. The 60% that's missing is the cognitive machinery that turns raw perception into understanding:
- Perception exists but doesn't extract goals
- Thinking exists but doesn't compute deltas
- Mapping exists but doesn't plan
- Acting exists but doesn't track state changes
- Feedback exists but measures the wrong thing

### What gives me confidence:
1. The theory is self-consistent and correct. Every theoretical concept maps to a real cognitive need.
2. The codebase infrastructure (database, event bus, evolution, agents) is robust and working.
3. FT09 shows 6 level completions in Gen 5145 — agents CAN stumble into solutions. With goal-awareness, they should find solutions deliberately.
4. The code is well-organized and the architecture docs are detailed. This isn't a messy codebase — it's an incomplete one.

### What concerns me:
1. VC33's temporal-delay problem is genuinely hard. Even with delayed observation windows, the agent needs to understand that fluid flows CONTINUOUSLY, not in discrete steps. This may require a fundamentally different causal model.
2. LS20's combinatorial modifier problem means the agent needs to try modifier combinations, which grows exponentially with the number of modifiers. Without heuristics (which we can't hardcode), the agent may struggle on levels with many modifiers.
3. The current winning sequences database has 154 entries — but these are memorized action lists, not learned strategies. The system needs to transition from "replay this sequence" to "recompute the solution from understanding." This transition is the hardest part.

### Timeline estimate:
- Gap 4 (Feedback): 1 session to implement, immediate testability
- Gap 5 (State Tracking): 1 session, testable on LS20
- Gap 1 (Goal Representation): 1-2 sessions, testable on FT09
- Gap 2 (Delta Computation): 1 session, builds on Gap 1
- Gap 3 (Planning): 1-2 sessions, builds on Gaps 1+2
- Observation tooling (Tier 1): Can be done alongside any gap
- Total: ~5-8 focused sessions to implement all gaps

After all gaps are filled, the system enters a new phase: **evolutionary tuning of cognitive parameters**. How quickly should confidence decay? How many frames of delayed observation? How often should the agent re-plan? These are parameters that evolution can tune — but only once the cognitive machinery exists.

---

## SECTION 7: THINGS I WANT TO OBSERVE FIRST

Before implementing anything, I want to see:

1. **One FT09 L1 game in detail**: Every frame, every action, every frame-diff. I want to see exactly what the agent sees when it looks at the constraint sprites. Does the visual cortex detect them as objects? Does anything in the perception pipeline notice they encode target colors?

2. **One LS20 L1 game in detail**: Does the agent's key display change when walking over modifiers? Does the frame-diff detect it? Is the lock display in a consistent location? Can the agent's perception distinguish "key display" from "lock display" from "maze walls"?

3. **One VC33 L1 game in detail**: After clicking a switch, what happens over the next 10 frames? Does fluid actually move visibly? How long is the delay between switch click and passenger movement? Is the causal chain visible at all in the frame sequence?

These observations would validate or invalidate assumptions in the Implementation Plan before we write a single line of implementation code.

---

## SECTION 8: COPILOT-INSTRUCTIONS.MD CORRECTIONS

The following corrections have been applied to `copilot-instructions.md` (verified 2026-02-15):

### ~~Line 406 (Section 3.5)~~ [APPLIED]
**Current**: `Check that FT09's available_actions=[6] (click-only, no directional)`
**Corrected**: `Check that FT09's available_actions=[1,2,3,4,5,6] (hybrid: camera pan + click)`
**Status**: Applied. Line 406 now reads: `Check FT09's available_actions=[1,2,3,4,5,6] (hybrid: camera pan + click)`

### ~~Line 482 (Section 3.5)~~ [APPLIED]
**Current**: `Verify at least N distinct positions are being clicked per game (should be >=5 for a 9-cell grid)`
**Corrected**: `Verify at least N distinct positions are being clicked per game (should be >=10 for a 32x32 grid with 16x16 viewport)`
**Status**: Applied. Line 482 now reads: `FT09: Should have >=10 unique positions (32x32 grid, 16x16 viewport, hybrid game with camera pan)`

### ~~Lines 547-549 (Section 5.3)~~ [APPLIED]
**Current**: `FT09 (click game, 6 levels)`
**Corrected**: `FT09 (hybrid game, 6 levels)` — and update the description to note camera panning + tile clicking
**Status**: Applied. Line 547 now reads: `FT09 (hybrid game, 6 levels, actions=[1,2,3,4,5,6])` with correct mechanics description.

### ~~Lines 552-553~~ [APPLIED]
**Current**: Describes FT09 as having "distinct colored cells in a grid pattern" with "clicking a cell should toggle it and neighbors (von Neumann neighborhood)"
**Corrected**: Remove the "and neighbors (von Neumann neighborhood)" claim. Standard tiles (`Hkx`) only affect the clicked tile.
**Status**: Applied. Lines 549-551 now describe constraint sprites, palette cycling, and "Standard tiles affect ONLY the clicked tile."

---

## APPENDIX: GAME MECHANICS QUICK REFERENCE (FOR CODEBASE ALIGNMENT)

This is what the CODEBASE should be ALIGNED to discover, not hardcode:

| Property | FT09 | LS20 | VC33 |
|----------|------|------|------|
| Available Actions | [1,2,3,4,5,6] | [1,2,3,4] | [6] |
| Camera Viewport | 16x16 on 32x32 | 16x16 | 64x64 (full) |
| Grid Size | 32x32 | Variable per level | Variable per level |
| Primary Mechanic | Camera pan + tile click | Movement | Click switches |
| Effect Timing | Instant | Instant | DELAYED (fluid flow) |
| Goal Encoding | Constraint sprites adjacent to tiles | Lock display (shape+color+rotation) | Color-matched destinations |
| State Tracking Needed | Tile colors, constraint patterns | Key properties, modifier locations | Membrane states, passenger positions |
| Levels | 6 | 7+ | 7 |
| Difficulty Source | More tiles, NTi tiles with neighbor effects | Fog-of-war, complex modifier chains | More chambers, complex flow paths |

---

**END OF AUDIT**
