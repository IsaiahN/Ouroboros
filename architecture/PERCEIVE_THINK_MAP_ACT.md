# Perceive → Think → Map → Act: The Cognitive Loop

**Date**: 2026-02-13
**Status**: IMPLEMENTED (v1) — Core loop built, adapter ready, replay viewer done.
**Problem**: The system has eyes (VisualCortex) and a brain (CognitiveRouter + Phenomenology + 80 rungs) but they're not connected. The agent doesn't SEE, doesn't THINK about what it sees, doesn't MAP causes to effects, and doesn't ACT based on understanding. It pattern-matches context keys.

### Implementation Files (v1 — Created 2026-02-13)

| File | Purpose | Lines |
|------|---------|-------|
| `engines/perception/perceptual_field.py` | PerceptualField dataclass — 5-channel fused perception output | ~200 |
| `engines/perception/perceiver.py` | Perceiver — runs 5 channels in parallel, integrates with cross-validation | ~500 |
| `engines/cognition/causal_map.py` | CausalMap — typed, persistent, queryable causal knowledge | ~550 |
| `engines/cognition/cognitive_frame.py` | CognitiveFrame — observable record of one P-T-M-A cycle | ~150 |
| `cognitive_loop.py` | CognitiveLoop — the main orchestrator (perceive→think→map→act) | ~450 |
| `cognitive_game_player.py` | CognitiveGamePlayer — drop-in adapter wrapping GamePlayer | ~250 |
| `tools/replay_viewer.py` | ReplayViewer — console + HTML replay rendering | ~200 |

---

## The Diagnosis

### What Exists (Rich Components, Dead Wiring)

| Component | File | Lines | Status |
|-----------|------|-------|--------|
| **VisualCortex** | `engines/perception/visual_cortex.py` | 1,957 | Called from ContextBuilder, output buried in `visual_scene` dict key. **1 out of 80 rungs reads it.** |
| **VisualAnalyzer** | `engines/perception/visual_analyzer.py` | 1,077 | Finds click targets. Used by Action6CoordinateProvider. Not part of any perception loop. |
| **ObjectDetector** | `engines/perception/object_detector.py` | ? | Exists. Not called from game loop. |
| **PhenomenologyLayer** | `engines/cognition/phenomenology_layer.py` | 834 | Compresses state to 5D FeltState. Called ONLY inside CognitiveRouter.decide() — never feeds back to perception. |
| **CognitiveRouter** | `engines/cognition/cognitive_router.py` | 2,225 | Has full pipeline (Blackboard→Epistemic→Phenomenology→Eisenhower). But receives rungs as black-box executors, not structured perception. |
| **I-Thread** | `engines/consciousness/i_thread.py` | 1,278 | Weighs Stream A vs Stream B. Has IThreadRung wrapper. **Never integrated into the per-action loop.** |
| **CausalMap** | `context_builder.py` _world_model | ~50 | Simple dict. Written to by 2 rungs. Never read by perception or reasoning pipeline. |
| **Blackboard** | `engines/cognition/blackboard.py` | ? | Shared state for cognitive router. Not populated from visual analysis. |

### The Current "Loop" (Flat, Not a Loop)

```
Frame arrives
    ↓
ContextBuilder.build_from_runner_state()
    ├── Calls VisualCortex.analyze(frame) → dict buried in 60+ context keys
    ├── Classifies puzzle type (once)
    ├── Extracts goal state (if reference panel found)
    ├── Builds flat DecisionContext with 60+ fields
    ↓
DecisionRungSystem.decide(obs, context_dict)
    ├── Picks ordering (ladder/cognitive/weighted)
    ├── Iterates rungs until one returns confident action
    ├── Most rungs read: score, action_count, available_actions, recent_actions
    ├── Almost NONE read: visual_scene, causal_map, world_model, goal_delta
    ↓
Action taken → frame changes → traces recorded
    ├── notify_action_complete → some rungs update internal state
    ├── update_world_model_from_action → causal dict updated
    ├── BUT: no re-perception of result
    ├── BUT: no phenomenological compression
    ├── BUT: no causal map update feeding back into next perception
    ↓
Next iteration: same flat process
```

**The problem**: There is no LOOP. There's a pipeline that runs once per action. The output of acting doesn't feed back into seeing. The agent is blind to the consequences of its own actions at a structural level.

---

## The Architecture: Perceive → Think → Map → Act

### Core Insight

You described it perfectly: "several layers of information are being input with gradient descent. Several constellations form from points across several dimensions of information allowing you to create causal mappings across information types that allow you to leapfrog the slow thinking."

This is **multimodal fusion with confidence-weighted integration**. Not an LLM — a structured cognitive loop where:

1. **PERCEIVE**: Multiple parallel perception channels extract different information types from the same frame. Each channel has a confidence. Channels weight each other (gradient-like descent toward a coherent percept).

2. **THINK**: The integrated percept is compressed into a felt-state (phenomenology) that captures: "what changed?", "how does this relate to my goal?", "am I surprised?", "is this familiar?". This is the consciousness step — where raw perception becomes meaning.

3. **MAP**: The meaning gets written into persistent causal maps. "When I clicked HERE, THAT changed." "This game works like THAT game." The mapping step creates the leapfrog — once you've mapped cause→effect, you don't need to think slowly anymore.

4. **ACT**: Action selection reads the MAP first (fast path), falls through to THINK (slow path), falls through to PERCEIVE-driven exploration (discovery path). This is the dual-process architecture — System 1 (mapped patterns) vs System 2 (deliberate reasoning).

### The Loop Structure

```
┌──────────────────────────────────────────────────────────┐
│                    COGNITIVE LOOP                         │
│                                                          │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌──────┐  │
│  │PERCEIVE │───→│  THINK  │───→│   MAP   │───→│  ACT │  │
│  │(parallel│    │(compress│    │(causal  │    │(fast/│  │
│  │ channels│    │ + feel) │    │ update) │    │slow) │  │
│  └────┬────┘    └─────────┘    └────┬────┘    └──┬───┘  │
│       │                             │             │      │
│       │         ┌───────────────────┘             │      │
│       │         │  causal map informs             │      │
│       │         │  next perception                │      │
│       └─────────┤                                 │      │
│                 │  action result feeds             │      │
│                 └─────────────────────────────────┘      │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## Phase 1: PERCEIVE — Multimodal Scene Understanding

### The Perception Channels (Parallel)

Each channel extracts ONE type of information from the frame. All run in parallel. Each returns a typed result with a confidence score.

```python
@dataclass
class PerceptualField:
    """The integrated output of all perception channels."""

    # Channel 1: Spatial Structure (from VisualCortex)
    panels: List[Panel]              # Where are the panels?
    tile_grid: Optional[TileGrid]    # What's the grid structure?
    interactive_region: Bounds       # Where can I click/move?

    # Channel 2: Object Inventory (from ObjectDetector)
    objects: List[DetectedObject]    # What objects exist?
    object_changes: List[Change]     # What changed since last frame?

    # Channel 3: Goal State (from VisualCortex reference detection)
    goal_state: Optional[GridState]  # What should it look like?
    current_state: GridState         # What does it look like now?
    delta: List[CellDiff]            # What needs to change?

    # Channel 4: Temporal (from action history)
    last_action_effect: ActionEffect # What did my last action do?
    frame_changed: bool              # Did anything change?
    surprise: float                  # How unexpected was the change?

    # Channel 5: Causal Context (from CausalMap — MAP feeds PERCEIVE)
    known_effects: Dict[Pos, Effect] # What do I already know about clicking here?
    unexplored_positions: List[Pos]  # Where haven't I clicked yet?
    predicted_next: Optional[Action] # If map is complete, what should I do?

    # Meta
    confidence: float                # Overall perceptual confidence (0-1)
    narrative: str                   # Human-readable scene description
```

### Channel Integration (The "Gradient Descent")

Channels don't just report independently — they **weight each other**:

```python
def integrate_channels(channels: List[ChannelResult]) -> PerceptualField:
    """
    Integrate multiple perception channels into a coherent percept.

    This is the 'gradient descent' step:
    - If spatial structure says "3x3 grid" and object detector finds 9 objects,
      confidence in both goes UP (agreement)
    - If spatial says "4 panels" but objects are found in only 2,
      confidence in spatial goes DOWN (contradiction)
    - Temporal channel (what changed) validates spatial predictions
    - Causal channel (what I know) prunes impossible perceptions

    This isn't backprop — it's mutual constraint satisfaction.
    Like how your brain resolves the Necker cube: multiple signals
    converge on the interpretation that satisfies the most constraints.
    """
    # Each channel votes on key properties
    # Agreement amplifies confidence, disagreement dampens
    # The winning interpretation is the one with highest integrated confidence
```

### What This Replaces

Currently: `VisualCortex.analyze()` runs once, returns a flat dict, nobody reads it.

After: `Perceiver.perceive(frame, causal_map, last_action)` runs 5 channels in parallel, integrates them into a `PerceptualField` that IS the input to thinking. Every rung receives structured perception, not a 60-key dict.

---

## Phase 2: THINK — Phenomenological Compression

### From Percept to Meaning

The PhenomenologyLayer already exists and does exactly this — it compresses high-dimensional state into 5D FeltState (valence, arousal, certainty, agency, salience). The problem is it only runs inside CognitiveRouter and reads the Blackboard, not the PerceptualField.

```python
@dataclass
class ThoughtState:
    """The output of the THINK phase."""

    # From PhenomenologyLayer
    felt: FeltState                  # 5D compression of experience

    # From PerceptualField analysis
    what_changed: str                # "Two cells flipped from blue to red"
    what_matters: str                # "I'm 3 cells away from goal state"
    what_to_try: str                 # "Click the remaining blue cells"

    # Epistemic state
    quadrant: str                    # KK/KU/UK/UU — what do I know?
    information_gain: float          # How much did I learn from last action?

    # Dual-stream integration (I-Thread)
    stream_a: float                  # My own understanding weight
    stream_b: float                  # Network knowledge weight
    conflict: float                  # How much do streams disagree?

    # Decision guidance
    strategy: str                    # "explore" / "exploit" / "experiment"
    urgency: float                   # How quickly should I act?
```

### The Key Transition

```
PERCEIVE output: "I see a 3x3 grid. 6 cells match the goal. 3 don't."
                                    ↓
THINK output:    FeltState(valence=OPPORTUNITY, certainty=0.7, agency=0.8)
                 strategy="exploit" (I know enough to act purposefully)
                 what_to_try="Click cells at (36,44), (52,36), (44,52)"
```

**This is where 'constellations form from points across dimensions'** — the 5D compression creates a point in felt-space. Similar situations create nearby points. The system can recognize "I've been in a state like this before" without needing to match every individual feature.

---

## Phase 3: MAP — Causal Knowledge Accumulation

### The Causal Map Structure

The current `world_model['causal_map']` is a flat dict. It needs to be a **typed, persistent, queryable structure**:

```python
@dataclass
class CausalMap:
    """
    Persistent causal knowledge for a game.

    This is where the 'leapfrog' happens:
    - First few actions: Perceive→Think→Act (slow, exploratory)
    - After mapping: Perceive→MAP LOOKUP→Act (fast, purposeful)

    The map is the system's compressed understanding of HOW THE GAME WORKS.
    """

    # Per-position effects: "clicking HERE does THAT"
    effects: Dict[TilePos, TileEffect]

    # Cross-position rules: "clicking any cell toggles its neighbors"
    rules: List[CausalRule]

    # Goal mapping: "to match the goal, I need to change THESE cells"
    goal_plan: Optional[List[PlannedAction]]

    # Confidence: how sure am I about each mapping?
    effect_confidence: Dict[TilePos, float]

    # Transfer: "this game works like THAT game"
    similar_games: List[str]

    def lookup(self, position: TilePos) -> Optional[TileEffect]:
        """Fast path: do I know what clicking here does?"""

    def plan_to_goal(self, current: GridState, goal: GridState) -> List[PlannedAction]:
        """Use known rules to compute a plan from current to goal state."""

    def update_from_action(self, pos: TilePos, before: GridState, after: GridState):
        """Learn from an action's consequence."""

    def information_gain(self, pos: TilePos) -> float:
        """How much would clicking here teach me? (High for unexplored positions)"""
```

### MAP Feeds Back Into PERCEIVE

This is the critical loop closure:

```
Action taken → frame changes
    ↓
MAP.update_from_action(pos, before, after)    # Learn the effect
    ↓
Next frame arrives
    ↓
PERCEIVE reads MAP:
    - Channel 5 now knows "clicking (36,44) toggles 3 neighbors"
    - Unexplored positions list shrinks
    - predicted_next may be non-None if map is sufficient
    ↓
THINK sees: certainty went UP, strategy shifts from "explore" to "exploit"
    ↓
ACT uses MAP.plan_to_goal() instead of rung ladder
```

---

## Phase 4: ACT — Three-Speed Decision Making

### The Speed Hierarchy

```python
def act(thought: ThoughtState, causal_map: CausalMap, percept: PerceptualField) -> Action:
    """
    Three speeds of action, tried in order:

    SPEED 1 — MAPPED (System 1, fast):
        If causal_map.goal_plan exists and has steps remaining,
        execute the next planned step.
        This is the 'leapfrog' — no thinking needed, just execute the plan.

    SPEED 2 — REASONED (System 2, slow):
        If ThoughtState.strategy is "exploit" and certainty > 0.6,
        use the constraint solver / rung system to find the best action
        given what we know from the causal map.

    SPEED 3 — EXPLORATORY (Discovery, deliberate):
        If ThoughtState.strategy is "explore" or certainty < 0.3,
        select the action with highest information_gain.
        Click where we haven't clicked. Move where we haven't moved.
        The goal is to FILL THE MAP, not to win yet.
    """
```

### What Changes in the Rung System

The 80 rungs don't go away — they become the implementation of SPEED 2. But instead of being the ONLY decision path, they're the fallback when the fast path (mapped causal knowledge) doesn't apply.

```
Current: rungs are the ONLY path. Every action goes through rung ladder.
After:   MAP → RUNGS → EXPLORE. Three speeds. Rungs are middle speed.
```

---

## Phase 5: OBSERVABILITY — Watch the Agent Think

### The Replay System

Every step of the loop produces structured, human-readable output:

```python
@dataclass
class CognitiveFrame:
    """One complete cycle of the Perceive→Think→Map→Act loop.
    This is what you watch in replay."""

    # When
    action_number: int
    timestamp: float

    # PERCEIVE
    frame_image: Optional[bytes]     # PNG of the 64x64 frame
    percept: PerceptualField         # Structured perception
    perception_narrative: str        # "I see a 3x3 grid with 6/9 cells matching goal"

    # THINK
    thought: ThoughtState            # Compressed thought
    felt_state: FeltState            # 5D emotional compression
    thought_narrative: str           # "I'm fairly certain. 3 cells left. Strategy: exploit."

    # MAP
    causal_map_snapshot: Dict        # Current state of causal knowledge
    map_update: Optional[str]        # "Learned: clicking (36,44) toggles (36,36) and (44,44)"
    map_completeness: float          # 0-1: how much of the game do I understand?

    # ACT
    action_taken: Action             # What I did
    action_speed: str                # "mapped" / "reasoned" / "exploratory"
    action_reason: str               # "Plan step 3/7: click (52,36) to flip it to red"
    action_narrative: str            # Human-readable explanation

    # RESULT (filled after action)
    frame_changed: bool
    surprise: float                  # How unexpected was the result?
    information_gained: float        # How much did I learn?
```

### Live Dashboard

```
╔══════════════════════════════════════════════════════════════╗
║  FT09 Level 3  |  Action 15/500  |  Score: 0.23            ║
╠══════════════════════════════════════════════════════════════╣
║ PERCEIVE                                                     ║
║  Grid: 3x3 tiles  |  Panels: 4 (input/goal/state/interact) ║
║  Goal delta: 3 cells differ  |  Interactive region: (33-62) ║
║  Objects: 9 tiles  |  Changed: 2 (from last action)         ║
╠══════════════════════════════════════════════════════════════╣
║ THINK                                                        ║
║  Felt: OPPORTUNITY  |  Certainty: 0.72  |  Agency: 0.85     ║
║  Strategy: EXPLOIT  |  Epistemic: KK (Known-Known)          ║
║  "3 cells away from goal. I know what each click does."     ║
╠══════════════════════════════════════════════════════════════╣
║ MAP                                                          ║
║  Causal effects known: 9/9 tiles  |  Rules: Von Neumann     ║
║  Goal plan: [click(52,36), click(44,52), click(36,44)]      ║
║  Completeness: 100%  |  Similar games: [vc33-level2]        ║
╠══════════════════════════════════════════════════════════════╣
║ ACT                                                          ║
║  Speed: MAPPED (fast path)                                   ║
║  Action: Click (52, 36)  |  Plan step 1/3                   ║
║  Expected: flip (52,36) red→blue, (44,36) blue→red          ║
╠══════════════════════════════════════════════════════════════╣
║ RESULT                                                       ║
║  Frame changed: YES  |  Surprise: 0.02 (expected)           ║
║  Goal delta: 2 cells differ (was 3)  [PROGRESS]             ║
║  Info gained: 0.01 (already mapped)                          ║
╚══════════════════════════════════════════════════════════════╝
```

---

## Implementation Plan

### File Changes

| Priority | What | Where | Effort |
|----------|------|-------|--------|
| **P0** | Create `CognitiveLoop` class — the PTMA orchestrator | New: `cognitive_loop.py` | 1 session |
| **P0** | Create `PerceptualField` dataclass | New: `engines/perception/perceptual_field.py` | Small |
| **P0** | Create `Perceiver` class — integrates all perception channels | New: `engines/perception/perceiver.py` | 1 session |
| **P0** | Create `CausalMap` class — typed, queryable causal knowledge | New: `engines/cognition/causal_map.py` | 1 session |
| **P1** | Wire CognitiveLoop into GamePlayer.play_game() | Edit: `game_player.py` | 1 session |
| **P1** | Wire PerceptualField into ThoughtState via PhenomenologyLayer | Edit: `engines/cognition/phenomenology_layer.py` | Small |
| **P1** | Create `CognitiveFrame` logging for replay | New: `engines/cognition/cognitive_frame.py` | Small |
| **P2** | Three-speed ACT (mapped→reasoned→explore) | Edit: `cognitive_loop.py` | 1 session |
| **P2** | Replay viewer (CLI or simple web) | New: `tools/replay_viewer.py` | 1 session |
| **P3** | Channel integration (mutual constraint satisfaction) | Edit: `engines/perception/perceiver.py` | 1 session |
| **P3** | MAP→PERCEIVE feedback loop (causal knowledge informs perception) | Edit: perceiver + causal_map | Small |

### Phase 0: The Minimal Loop (Can Ship in 1 Session)

The absolute minimum to get See→Think→Act working:

1. **Perceiver** wraps existing VisualCortex + VisualAnalyzer + frame diff into one `perceive(frame)` call
2. **CausalMap** wraps existing `world_model['causal_map']` dict into typed class with `lookup()` and `update()`
3. **CognitiveLoop** replaces the flat `build_context → decide → act` with `perceive → think → map → act`
4. **CognitiveFrame** logs each cycle for observability

This doesn't delete any rungs or break any existing code. It WRAPS the existing system in a proper loop structure.

### The Key Architectural Principle

**The loop IS the intelligence.** Not the rungs. Not the visual cortex. Not the causal map. The LOOP — the fact that perceiving informs thinking, thinking informs mapping, mapping informs the next perception, and acting closes the cycle. The components are organs. The loop is the circulatory system that makes them alive.

Without the loop, you have a bag of organs. With the loop, you have an organism.

---

## Why This Works Without an LLM

An LLM achieves generality by training on internet-scale data to learn statistical associations.

This system achieves generality through the loop:

1. **PERCEIVE** decomposes any frame into structured primitives (panels, objects, grids, colors). No training needed — it's algorithmic decomposition.

2. **THINK** compresses to a 5D felt-state that captures the MEANING of any situation. "Confused + low certainty + high salience" means the same thing whether you're playing FT09 or VC33 — it means "I see something interesting that I don't understand yet."

3. **MAP** builds causal models FROM INTERACTION. No pre-training. Click → observe → record. The system discovers the game's API by using it.

4. **ACT** uses the map for fast execution and falls back to deliberate reasoning when the map is incomplete.

The LLM's "world model" is implicit in billions of parameters. This system's world model is EXPLICIT in the CausalMap — inspectable, debuggable, transferable between agents, and built from scratch for each new game.

**The loop is the alternative to scale. Instead of learning everything in advance, you learn exactly what you need, right now, from the game itself.**
