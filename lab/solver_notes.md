# Solver Notes: Game-by-Game Approaches & Cognitive Principles
**Date**: 2026-03-27 | Phase 2 (Solver Development) → Phase 3 (Principle Extraction)

---

## THE CORE COGNITIVE LOOP: How to Reason Through Any Unknown Game

This is the process used when encountering each new game. The finished notebook will replicate this reasoning using its arsenal of pre-built tools — it cannot rewrite itself, but it CAN select which tools to apply.

```
OBSERVE → CLASSIFY → EXTRACT_GOAL → MAP_EFFECTS → PLAN → EXECUTE → VERIFY
```

### Phase 1: OBSERVE
**What to do**: Read the game object's attributes. Don't pixel-analyse first — the internal state is far richer.
```python
attrs = [a for a in dir(game) if not a.startswith('__')]
# Find: player position, score, win condition, level count
# Look for: lists of sprites, movement step sizes, phase counters
```
**Decision criteria**: What attributes change when I take actions? What stays fixed?
**Signal that observation is complete**: You can name the player, the target, and at least one obstacle.

### Phase 2: CLASSIFY
**What to do**: Assign the game to a known mechanic category. This selects the solver strategy.

| Category | Key Signal | Example Games |
|----------|-----------|---------------|
| Navigation | Player moves, reach target | ls20, tu93, sc25 |
| Toggle-puzzle | Actions cycle group states | ft09, vc33 |
| Push/force | Collision propagates pieces | ka59 |
| Sequence-commitment | Action locks in a replay | g50t |
| Merge-elimination | Same-type proximity reduces count | lf52, su15 |
| Coverage | Path must visit all targets | sk48 |
| Pattern-input | Game shows required pattern to replicate | sc25 |
| Extension | Repeated action grows/extends state | s5i5 |
| Traversal-ordering | Nodes must be visited in sequence | sb26 |

**What failed**: Relying on pixel analysis to classify — internal attributes expose category directly (e.g., `game.spell_legends`, `game.ghosts`, `game.gates`).

### Phase 3: EXTRACT_GOAL
**What to do**: Identify the win signal. Always use `game._score > prev_score` — NOT `game.cbdaoltbck()` which fails after level transitions.
```python
# Reliable win check:
prev = game._score
game.perform_action(...)
won = game._score > prev
```
**Common goal structures found**:
- Reach position (flag/exit sprite): g50t, sc25, tu93, ls20
- Eliminate all pieces: lf52, sk48 (cover all targets)
- Set collective state to target: ft09 (all cells right color), vc33 (switches → path opens)
- Push pieces to target positions: ka59

### Phase 4: MAP_EFFECTS
**What to do**: Probe each available action. Record what changes in the game state.
```python
for action_n in range(1, 8):
    g_copy = copy.deepcopy(game)
    g_copy.perform_action(ActionInput(id=getattr(GameAction, f'ACTION{action_n}')))
    # What changed? Player position? Score? Sprite positions?
```
**Critical insight**: Some actions are productive only under certain conditions. Example: sc25 ACTION6 clicks only work AFTER the first-input demo animation clears. G50T ACTION5 commits a recording (not undo).

### Phase 5: PLAN
**Toolbox selection — how to choose a solver**:

1. **Direct calculation** (O(1)): When effects are predictable and composition is simple.
   - *Use when*: distance / step_size gives you the answer (s5i5: count clicks needed)
   - *Chose this for*: s5i5, simple ft09 levels

2. **BFS with deepcopy** (reliable, slow): Gold standard. Each node is a full game copy.
   - *Use when*: solution depth < 25, branching factor < 6, budget allows
   - *Chose this for*: g50t, tu93, sk48, sc25, ka59
   - *Pitfall avoided*: State-restore BFS misses hidden internal state; deepcopy doesn't

3. **Recursive multi-phase BFS**: For commitment-based games with sequential phases.
   - *Use when*: game has phases (commits/Z presses) that each need a separate BFS
   - *Chose this for*: g50t L2+ (2 Z-commits, 3 total phases)

4. **Constraint satisfaction / enumeration**: When state space is a grid of toggles.
   - *Use when*: collective state must reach specific config, actions are toggles
   - *Chose this for*: ft09 (lights-out style)

5. **Greedy + closed-loop control**: For physics games where BFS is intractable.
   - *Use when*: state is continuous (positions, velocities), brute-force is impossible
   - *Chose this for*: su15 (merge + enemy avoidance)

6. **State-hash deduplication**: Always needed for BFS to prevent loops.
   - Minimal hash = (player_pos, relevant_dynamic_state)
   - Include ghost/piece positions, gate states, phase counter
   - Exclude: visual/animation state, pixel colors

### Phase 6: EXECUTE
**What to do**: Run the solver. Track action count. Watch for budget depletion.
- Actions are always `game.perform_action(ActionInput(id=GameAction.ACTION{n}))` for internal solvers
- Click actions: `ActionInput(id=GameAction.ACTION6, data={'x': gx, 'y': gy})`
- Camera coordinate conversion: `camera.display_to_grid(display_x, display_y)` → grid coords

### Phase 7: VERIFY
**What to do**: After finding a solution sequence, replay it on a fresh game and confirm `_score > 0`.
- BFS solutions are often verified implicitly (win was detected during BFS)
- For replay-based solvers: replay entire sequence from scratch, check each step
- Save to DB only after verification

---

## Decision Framework: How to Approach a New Game (Quick Reference)

1. **Read the game source** — don't rely on pixel analysis alone. The game object attributes expose the full state (piece positions, gate states, score, win condition) without needing CV.
2. **Probe actions** — try each ACTION1-7 and observe what changes in game attributes.
3. **Identify the win signal** — `game._score > prev_score` = level completed. `game.cbdaoltbck()` sometimes fails after level transition. Always check score delta.
4. **Map the mechanics** — categorize the game type, then select the right solver strategy.
5. **BFS with `deepcopy`** is reliable but slow. Use for short solutions (<20 moves). Use replay-from-scratch for verification.
6. **State hashing for dedup** — always hash the minimal state (player position + relevant dynamic state). Ghost positions, gate states, piece positions are key.

---

## Game-by-Game: Mechanics, Approach, Key Decisions

### FT09 — Lights-Out Constraint Satisfaction
- **Mechanic**: Grid of cells that cycle colors on click. Target = all cells at goal color. Actions 1-5 exist but only ACTION6 (click) is productive.
- **Key insight**: Clicking a cell cycles its color. Multiple cells may share a toggle group. Win = collective state reaches target configuration.
- **Solver**: Constraint satisfaction — enumerate which cells to click and in what order. For lights-out variants, linear algebra over GF(2) works.
- **Agnostic principle**: *Detect that actions cycle local state; find minimum action set that drives collective state to target configuration.*

### S5I5 — Rail Extension Puzzle
- **Mechanic**: Click a controller sprite to extend a rail in one direction (up/down/left/right depending on controller orientation). Target sprite (zylvdxoiuq) needs to reach a goal sprite (cpdhnkdobh).
- **Key insight**: Each controller click extends the rail by 1 unit. Count how many clicks needed to push target to goal.
- **L1 solution**: 6 clicks at vertical controller → target reaches y=51. 7 clicks at horizontal controller → target reaches x=51.
- **Solver**: Read controller positions, target positions, goal positions from game internals. Compute clicks needed = distance / step_size.
- **Agnostic principle**: *Detect directional extension mechanic; compute how many applications needed to reach goal.*

### G50T — Time-Loop Maze (Multi-Phase Ghost Puzzle)
- **Mechanic**: N-phase time loop. Each phase: record moves (A1-4), commit with ACTION5 (Z). Z spawns a "ghost" that replays recorded moves (1 step per player action). Player resets to start. Final phase: navigate to flag using ghosts to keep gates open.
- **Key insight (critical)**: Z resets player to start AND spawns ghost that replays recording in sync with subsequent moves. Gates open when specific positions are occupied (by player OR ghost).
- **L1 solution (2 phases)**: RRRR Z (ghost1 replays RRRR, reaches x=37 = gate trigger) DDDDDDD RRRRR (ghost stays at trigger, gate stays open, player navigates to win).
- **L2+ (3 phases)**: Need 2 Z commits. Phase1 opens gate A, Phase2 (with ghost1 active) opens gate B, then navigate with both open.
- **State hash for BFS**: `(player_x, player_y, ghost_positions_tuple, open_gates_tuple)`.
- **Solver approach**: Recursive multi-phase search. Enumerate recording sequences (via BFS), commit each with Z, then recurse into remaining phases.
- **Key pitfall**: `deepcopy` required for BFS branching — state-restore via attribute setting misses internal derived state.
- **Agnostic principle**: *Detect state-commitment mechanic; learn that actions cause local state change that persists; chain commitments to reach goal-enabling configurations.*

### KA59 — Block Push Puzzle
- **Mechanic**: Select active piece (ACTION6 click), move it (A1-4). When selected piece collides with another xlfuqjygey piece, push mechanic: pushed piece slides 5×step_size in push direction, passing through "soft" walls, stopping at hard walls.
- **Key insight**: Pushing allows long-range piece placement without moving the selected piece. Selection (ACTION6) changes which piece is active.
- **Win condition**: Each rktpmjcpkt target needs a piece at (target.x+1, target.y+1) with matching size.
- **L1 solution**: RRR (push P1 from x=18 to x=33), LLLL D (navigate P0 to target position), CLICK P1 (select P1), R U (move P1 to second target).
- **Verification pitfall**: `cbdaoltbck()` returns False AFTER level transition. Check `game._score > prev_score` instead.
- **Solver approach**: BFS with replay-from-scratch for verification. State = (selected_piece_idx, all_piece_positions).
- **Agnostic principle**: *Detect push mechanic; identify that indirect force (pushing) enables piece placement not reachable by direct navigation; plan push sequences to simultaneously satisfy multiple placement goals.*

### SB26 — Traversal/Token-Collection Puzzle
- **Mechanic**: Navigate tokens through directed paths (rail-like). Tokens must traverse specific segments in specific orders. Multiple "frames" with different connectivity. Sub-frames use redirect tokens that can teleport paths.
- **Solver approach**: v4 solver used per-frame BFS tracking which headers are satisfied. Sub-frame revisit support: frame_done dict keyed by frame_id to avoid re-solving already-solved sub-frames. Mutual revisit chains (frame8→frame9→frame8) need careful state tracking.
- **All 8 levels solved**: Including L5 (sub-frame revisit) and L8 (mutual redirect chain satisfying 12 headers across 2 rows).
- **Agnostic principle**: *Detect directed-path traversal; identify required sequence of node visits; BFS over traversal state.*

### SU15 — Suika/Waterfall Merge (Physics-Based)
- **Mechanic**: Fruit types 1-N. Click canvas position to attract nearest fruit. Same-type fruits within VACUUM_RADIUS merge into next type. Different-type collision = UNDO. Enemy moves toward nearest fruit, downgrades type on contact.
- **Key insight**: Closed-loop control needed — read live `game.hmeulfxgy` (fruit positions) each tick rather than simulating.
- **L1-4 strategy**: Sort merge opportunities by (type_priority, enemy_urgency, safe_merge_position). Emergency flee at 6px from enemy. Goal-blended flee for all_produced phase.
- **Why L5 failed**: 2 enemies converge on type-1 fruits faster than they can be merged. Fundamentally hard. Accepted.
- **Agnostic principle**: *Detect merge-on-proximity mechanic with enemy interference; plan merge sequences that avoid enemy positions; use closed-loop control reading live state each tick.*

### TU93 — Rotation Maze
- **Mechanic**: S-shaped maze with rotatable/navigable elements. BFS over game states.
- **L1 solution**: 18 actions found by BFS.
- **Agnostic principle**: *Map navigable positions via BFS; handle rotatable elements as state-changing obstacles.*

### LS20 — Shape/Color/Rotation Matching Maze
- **Mechanic**: Move player through maze (A1-4). Reach goal matching shape+color+rotation. Multiple configurations (96 total). Timer + 3 lives.
- **Solver**: A* / BFS with spatial navigation. Injecting known solutions per variant as warm-start.
- **Agnostic principle**: *Navigate to target while matching multi-dimensional classification (shape, color, orientation).*

### VC33 — Rail Switching Puzzle
- **Mechanic**: Click switches (ACTION6) to redirect rail segments. Train follows rail to win position.
- **Solver**: Enumerate switch configurations, verify which leads to win.
- **Agnostic principle**: *Detect causal action → state change → output path change; try switch combinations.*

### LF52 — Peg Solitaire / Ball Merge
- **Mechanic**: Balls merge when moved into adjacent same-color ball. Win when single ball remains. Also has sliding puck mechanics (hupkpseyuim2 pucks) that create new landing cells.
- **L1**: 4 BFS moves — merge chain reduces 5 balls to 1. Saved as 8 actions.
- **L2 pitfall**: Isolated ball permanently unreachable = unsolvable. Confirmed via full BFS including all puck positions.
- **Agnostic principle**: *Detect merge-on-adjacency mechanic; compute merge chain that eliminates all but one piece. Verify structural solvability before exhausting budget.*

### SK48 — Snake/Slide-Block Puzzle
- **Mechanic**: Snake head controlled (A1-4). Extending snake body covers target cells. Win when all targets covered.
- **L1 solution**: 14 actions found by BFS (depth 14, 637 states explored).
- **Solver**: BFS with state = (head_pos, body_segments, target_positions).
- **Agnostic principle**: *Detect coverage mechanic; plan path that visits all target cells without collision.*

### SC25 — Spellcasting Dungeon (Multi-Spell Navigation)
- **Mechanic**: Player moves (A1-4) through dungeon. Spell panel shows `highlighted_spell`. Click 3×3 spell slots (ACTION6 at predefined display coords) to match the spell pattern. Correct match triggers spell effect. Multiple spells unlock paths to exit.
- **Three spells** and their effects:
  - `fpokrvgln` (diamond pattern): size-change — toggles player scale 1↔2. Small player can reach otherwise blocked areas.
  - `jzukcpajs` (top-left L pattern): teleport — moves player to preset teleport target.
  - `aprnrzeyj` (vertical column): fireball — fires in player's facing direction, destroys `edusagitv` boss sprites, which removes `ltwvrfpfp` door sprites.
- **Key attributes**: `spell_legends` (spell→pattern), `highlighted_spell`, `spell_slot_active`, `wdsxxkugj` (spell queue), `sykpecmoq` (action budget), `doors` (ltwvrfpfp sprites), `second_doors` (ckmqitdgq-ltwvrfpfp).
- **Critical quirk**: First action on each level triggers a spell-pattern demo animation (runs internally), consuming one action. To cast spell: (1) send any action to clear demo, (2) then click the pattern slots.
- **Spell slot coordinates** (display → slot [row][col]):
  - (25,50)=[0][0], (30,50)=[0][1], (35,50)=[0][2]
  - (25,55)=[1][0], (30,55)=[1][1], (35,55)=[1][2]
  - (25,60)=[2][0], (30,60)=[2][1], (35,60)=[2][2]
- **fpokrvgln** = `[F,T,F],[T,F,T],[F,T,F]` → click (30,50),(25,55),(35,55),(30,60)
- **jzukcpajs** = `[T,T,F],[F,T,F],[F,F,F]` → click (25,50),(30,50),(30,55)
- **aprnrzeyj** = `[F,T,F],[F,T,F],[F,T,F]` → click (30,50),(30,55),(30,60)
- **L1 solution**: Click(30,50)[demo], Click(30,50)[slot], Click(25,55), Click(35,55), Click(30,60) → spell fires (player shrinks) → L×12 to exit. Total: 17 actions.
- **L2 solution**: Click(25,50)[demo], Click(25,50),(30,50),(30,55) → teleport → U×2. Total: 5 actions (budget=25).
- **Solver approach**: Full deepcopy BFS with all 9 slot clicks + 4 movement actions. State hash = (player_x, player_y, scale, slot_pattern_tuple, door_count, teleport_index). Budget-constrained exploration.
- **Agnostic principle**: *Detect pattern-input mechanic; read required pattern from game state (`spell_legends[highlighted_spell]`); compute slot positions from pattern; click in order; state-hash must include both spell slot state AND positional/door state.*

---

## Solver Strategy Hierarchy (from most to least reliable)

1. **Game-internal BFS** (deepcopy): Reliable, slow. Use when <25 actions, branching factor manageable.
2. **Replay-from-scratch BFS**: Very reliable (gold standard), O(depth²) slow. Use for verification.
3. **State-restore BFS**: Fast, fragile (misses hidden state). Use only after validating state representation.
4. **Greedy/heuristic**: For physics games (su15) where BFS is intractable.
5. **Direct analysis**: When structure is obvious from game attributes (s5i5: count clicks needed).

---

## What the Notebook Needs to Learn Agnostically

These mechanics recur across games and should be cognitive primitives. When the system encounters a private eval game, it runs through these in order until it identifies a match:

| Primitive | Detection Signal | Tool to Apply |
|-----------|-----------------|---------------|
| Toggle detection | action causes state cycle → BFS over toggle combinations | constraint satisfaction |
| Push detection | collision causes propagation | plan indirect force chains |
| Merge detection | proximity + same-type causes fusion | position same-type pairs |
| Gate/door detection | specific position opens path | identify trigger positions, plan to activate |
| Sequence-commit | action locks future replay | multi-phase BFS with commit points |
| Pattern-input | game exposes required pattern in attributes | read pattern, compute clicks, execute |
| Coverage | path must visit all targets | BFS path covering all required cells |
| Extension | repeated action grows state toward goal | count steps = distance / step_size |
| Teleport | action jumps player to preset position | plan to cast at right time, nav after |
| Size-change | spell changes player hitbox → new paths open | cast to unlock, then re-navigate |
| Causal attribution | action A causes observable B | track which actions produce state changes |

### Why these matter for unseen games
The private eval games will have DIFFERENT obfuscated attribute names but SIMILAR mechanical structures. The cognitive notebook:
1. Reads all game attributes using the `OBSERVE` phase
2. Probes all actions and records delta-states using `MAP_EFFECTS`
3. Classifies the mechanic by matching observed patterns to the table above
4. Selects the corresponding solver tool
5. Executes and verifies

The key is that the notebook doesn't need to "understand" a game — it needs to detect which pre-built solver archetype fits, then apply it.

---

## Key Technical Pitfalls Encountered

1. **Win detection after level transition**: `game.cbdaoltbck()` fails post-transition. Use `game._score > prev_score`.
2. **State restoration**: Attribute-setting misses derived/cached internal state. Always use `deepcopy` for BFS.
3. **Ghost mechanic in g50t**: Ghost positions change each step — state hash must include ALL ghost positions + gate states.
4. **Action5 (Z) vs undo**: In g50t, ACTION5 = commit (spawn ghost). In other games, ACTION5/7 = undo.
5. **Click coordinate mapping**: Game uses grid coordinates; display uses scaled+padded coordinates. Camera.display_to_grid() handles conversion.
6. **Level index vs level number**: `set_level(0)` = Level 1. Always +1 when reporting.
7. **sc25 first-input demo**: First action on every level triggers a tutorial demo animation that runs to completion internally. The action itself is consumed by the demo. Slot (0,1)=(30,50) was missed on the very first attempt because the click triggered the demo instead of toggling the slot.
8. **Demo not blocking in sc25**: The demo animation resolves completely within a single `perform_action()` call (it loops frames until `complete_action()` fires). So there's NO need to "wait" for the demo — just send 1 dummy action to clear it, then proceed with spell clicks.
9. **Structural unsolvability**: Some levels (lf52 L2) have permanently isolated pieces. A full BFS confirmation is needed before concluding failure. Don't assume the solver is broken — inspect topology.
10. **Budget depletion during BFS**: sc25 has explicit budget (sykpecmoq). BFS must prune branches where `game.actions_taken > budget`. Track budget in state hash to avoid revisiting same position with different budget levels.

---

## DB Coverage as of 2026-03-28 (UPDATED)

| Game | Solved Levels | Win Levels | % | Notes |
|------|--------------|------------|---|-------|
| cn04 | L1 | 9 | 11% | Coord-click, probe finds 0 active (player must move first) |
| ft09 (main) | L1-L6 | 6 | **100%** | COMPLETE |
| ft09 (new) | L1, L2 | 6 | 33% | L3-L6 pending (background solver running) |
| g50t | L1, L2 | 7 | 29% | L3+ BFS no-solution (only 1 valid action from probe pos; may need deeper) |
| ka59 | L1, L3 | 9 | 33% | Missing L2; coord-click requires player adjacency — BFS incompatible |
| lf52 | L1 | 10 | 10% | State hash unfixable (3-level deep obfuscated objects) — BFS blocked |
| lp85 | L1-L8 | 8 | **100%** | COMPLETE |
| ls20 (new) | L1-L7 | 7 | **100%** | COMPLETE |
| ls20 (main) | L1-L7 | 7 | **100%** | COMPLETE |
| m0r0 | L1-L6 | 6 | **100%** | COMPLETE — L3 solved 2026-03-28 (gap detection fix) |
| r11l | L1 | 9 | 11% | Coord-click, ACTION6 only works near objects — BFS incompatible |
| s5i5 | L1 | 9 | 11% | Coord-click, probe finds few active coords from initial position |
| sb26 | L1-L8 | 8 | **100%** | COMPLETE |
| sc25 | L1-L4 | 6 | 67% | L5-L6 unsolved (two-click selection mechanic blocks coord probe) |
| sk48 | L1 | 8 | 12% | Coverage game, BFS with level hash should work (solver running) |
| sp80 | L1, L2 | 6 | 33% | L3+ mixed movement+coord, BFS needs movement+coord combined |
| su15 | L1-L4 | 9 | 44% | L5+ very hard (physics + 2 enemies) |
| tr87 | L1-L4 | 6 | 67% | L5-L6 no solution in 30k nodes — solutions may be 90+ actions |
| tu93 | L1, L2 | 9 | 22% | L3+ no solution in 30k nodes — state hash works now but depth/nodes insufficient |
| vc33 | L1-L7 | 7 | **100%** | COMPLETE |
| wa30 | — | 1 | 0% | Game source missing (competition-only) |

**Completed**: ft09, lp85, ls20×2, sb26, vc33, m0r0 (6/21 games 100%)
**Partial**: tr87 (67%), sc25 (67%), su15 (44%), sp80 (33%), ft09-new (33%), ka59 (33%), g50t (29%), tu93 (22%), sk48 (12%)
**Stuck**: r11l, cn04 (coord-click + proximity), lf52 (hash blocked), tr87/sp80/sk48/tu93/g50t (BFS depth/speed insufficient)

---

## _extend_solvers.py Bug Fixes (2026-03-28)

### Bug 1: Navigation check too aggressive
- **Problem**: `if has_movement and not has_interact and win_levels > 2` skipped ALL movement-only games, including tr87/tu93/g50t which have partially solved levels.
- **Fix**: Added `all_no_frame = all(...)` check — only skip if NO actions change state from initial position.

### Bug 2: Old-format sequence in fast-forward
- **Problem**: lf52 stores sequences as `{'actions': [6,6,...], 'data': [{x,y},...]}` (old format). Fast-forward code did `entry.get('action')` on dict keys → AttributeError.
- **Fix**: Normalize old-format sequences before iterating; also handle raw integer entries.

### Bug 3: get_frame_hash misses _levels-based state
- **Problem**: Games like tu93/g50t store all state in `_levels[idx]._sprites` (private attribute). `_sprite_state_hash` skips all `_`-prefixed attrs → all states hash identical → BFS terminates immediately.
- **Fix**: Added `_levels[current_level_index]._sprites` hashing to `get_frame_hash` fallback.

### Bug 4: lf52 state hash still blocked (unresolved)
- **Problem**: lf52's distinguishing state is buried 3+ levels deep in obfuscated objects (`ikhhdzfmarl.hncnfaqaddg.<something>`). Added recursive numpy-array hash but only goes 2 levels — still doesn't capture the difference between click positions.
- **Diagnosis**: `(16,17)` and `(28,17)` clicks produce identical hashes despite different game outcomes. `btiyglcumku.cisfibgucg` (an embedded Lf52 copy) and `ikhhdzfmarl.hncnfaqaddg` (type `nfpetofmbpr`) differ between clicks but can't be accessed without going 3+ levels deep through obfuscated class hierarchy.
- **Status**: BFS blocked for lf52 L2+. Not fixable without reimplementing hash to recursively walk object graph.

### Other findings
- **tr87 L5-L6**: BFS depth=30, nodes=15000 finds no solution. tr87 L1 needed 92 actions. Solution depth likely 50-100+. BFS approach fundamentally too slow.
- **tu93 L3+**: Hash works (ACTION1 changes state). BFS depth=200 nodes=20000 still no solution. Navigation maze too large for BFS.
- **g50t L3+**: Multi-phase ghost replay game requiring 2+ ACTION5 commits. BFS depth=200 nodes=20000 no solution. Needs recursive multi-phase solver (separate from standard BFS).
- **sp80 L3+, sk48 L2+**: Mixed/complex movement, no solution at depth=28/15000. Solutions likely require 30-60+ actions.
- **su15 L5+**: Continuous physics; solutions use non-grid coords (e.g., (9,53), step-by-step at 6px increments). Grid-probe misses these. Needs closed-loop physics solver.

---

## Notebook Version History
- v55: Game-agnostic deepcopy BFS + env IDDFS (single-level)
- v56: Multi-level BFS (continues L1→L2→...→Ln), action probing for param tuning
  - Submitted as Kaggle kernel v52 to thezetaproject/bittertruth-ai-arc-agi-3-competition-submission
- v59: Add coordinate-click BFS tier (Tier 1b in _mechanic_solve)
  - `_sprite_pixel_hash`, `_coord_state_hash`, `_probe_coord_effects` (independent x,y offsets), `_dedup_coords`, `_coordinate_bfs`
  - Auto-detects coord-click games when all standard action probes return frame_changed=False
  - Removes dead code (old v55 copy of _mechanic_solve after return None)
  - Submitted as Kaggle kernel v55
- v60: Multi-level coord-BFS with per-level re-probe (compositional balance approach)
  - Replaces single-level Tier 1b with a loop over win_levels
  - Per-level re-probe: after each level WIN, re-classify mechanics at the new level boundary
  - Applies coord sequence to game_obj in-place (same pattern as `_multilevel_deepcopy_bfs`)
  - Stops if an action-based level is detected mid-loop
  - Node budget: `min(max(n^5, 20000), 400000)` instead of `n^4 * 2`
  - Executes full multi-level coord sequence via env.reset + env.step at end
  - Submitted as Kaggle kernel v56

## _extend_solvers.py Bug Fixes (2026-03-28 afternoon)

### Bug 5: m0r0 gap detection — remaining_levels wrong
- **Problem**: `remaining_levels = win_levels - max_existing = 0` for m0r0 with gap at L3 (max_existing=6). BFS tried 0 levels.
- **Fix**: Changed to `remaining_levels = win_levels - (start_level - 1)`. Also fixed log message to use `start_level-1` instead of `max_existing`.
- **Result**: m0r0 L3 solved (23 actions).

### Bug 6: Action filter removed movement actions
- **Problem**: Applied `frame_changed=False` filter to remove no-op actions. For movement games, an action may be no-op from start position but valid after navigation (e.g., can't move down at start, can after moving up).
- **Fix**: Only filter for non-movement games (when no WASD-style actions in available set).

### Bug 7: single-action linear search applied to wrong games
- **Problem**: `n_acts==1` triggered deep linear search (depth=500) even when caused by wrong filtering.
- **Fix**: Only apply when `not movement_actions` (i.e., pure coord-click games).

### tune_params improvement: depth=200 for single-frame-change games
- **Problem**: Games where only 1 action changes state (tu93 L3, g50t L3) get depth=30, which is far too shallow for navigation mazes.
- **Fix**: `if n_frame == 1: return 200, 20000` in `tune_params`.
- **Result**: tu93 and g50t still no solution (solution depth exceeds 200 sequential steps, or state space too large for BFS with standard hash).

### coord_nodes formula improved
- **Old**: `n^4 * 2` → for 8 coords = 8192
- **New**: `min(max(n^5, 20000), 400000)` → for 8 coords = 32768 (but su15 still not solved — continuous physics game).
