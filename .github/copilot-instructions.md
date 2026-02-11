# MASTER RULESET FOR AUTONOMOUS OUROBOROS OPERATION
**Version**: 2.0
**Date**: 2026-01-12
**Purpose**: Comprehensive operating rules + architectural theory synthesis
**Context**: Single source of truth to prevent LLM catastrophic forgetting

---

## PRIMARY OBJECTIVE

**GOAL**: Achieve full game wins on ALL current and future ARC 3 AGI games through autonomous network-level evolution.

**SUCCESS METRICS**:
1. Phase 1: All games reach 100% level completion
2. Phase 2: All completed games reach optimization saturation
3. Phase 3: System handles hundreds of new games without intervention
4. Final: Continuous evolution maintaining 100% win rate as games added

---

## ENVIRONMENT SETUP

### Virtual Environment (.venv)
- **ALL Python execution** uses the `.venv` virtual environment in project root
- **Activation** (PowerShell): `& .venv/Scripts/Activate.ps1`
- **Activation** (bash): `source .venv/bin/activate`
- **NEVER** use system Python - always verify `(.venv)` prefix in terminal
- **Installing packages**: Always activate venv first, then `pip install <package>`
- **Why**: Isolated dependencies, reproducible environment, no system conflicts

**Verify venv is active**:
```powershell
python -c "import sys; print(sys.prefix)"
# Should output: C:\Users\Admin\Documents\GitHub\BitterTruth-AI\.venv
# If it shows system Python path, venv is NOT active!
```

---

## 17 CRITICAL OPERATING RULES (NON-NEGOTIABLE)

### **RULE 1: Always Disable Pycache**
- `PYTHONDONTWRITEBYTECODE=1` in ALL environments
- `.pyc` files NEVER generated
- Active deletion in cleanup script (pre-evolution)
- **Why**: Prevents file system clutter, easier version control

### **RULE 2: Database-Only Storage**
- ALL data in SQLite `core_data.db`
- NEVER create `.log` files
- Use `database_logger.py` with `DatabaseLogHandler`
- Every operation, decision, result -> database tables
- **Size Limit**: 200 GB (vacuum requires 2x space)

### **RULE 3: No Orphaned Code**
- Delete/move/integrate ALL old code when refactoring
- Clean integration = enhance existing files, not replace
- Update all references
- Account for every line
- **Why**: Prevent code drift and unmaintained functionality

### **RULE 4: LLM Self-Management**
- Claude manages entire system autonomously
- All evolution decisions from database analysis
- NO human intervention once started (except critical issues)
- **Role**: Autonomous "human in the loop" - assess, hypothesize, test, fix

### **RULE 5: No Test Files**
- NEVER create test files (waste of tokens)
- Use LIVE ARC AGI 3 data only
- Real game results for ALL validation
- **Exception**: See Rule 15 - tests in `tests/` folder are preserved

### **RULE 6: No Simulated Games**
- NEVER mock/simulate ARC games
- Always use real API: `https://three.arcprize.org/api/`
- Real game states only
- **Why**: Simulations don't capture edge cases

### **RULE 7: Real Actions Only**
- Verify real actions sent to ARC games
- Monitor API calls, track responses
- All ACTION1-ACTION7 -> real ARC API
- Store API responses in database

### **RULE 8: Test Before Commit**
- Test new implementation on main active script
- Scan terminal for errors/bugs
- Auto start/stop runs until clean execution
- Verify: actions sent, scores updated, real scorecard IDs
- **Only commit to git when confirmed fixed**

### **RULE 9: No Summary Files Unless Asked**
- Documentation in code comments/docstrings
- Exception: Critical artifacts (this ruleset, to-do lists)

### **RULE 10: Prevent Code Drift**
- Align new code with existing architecture
- Enhance existing files >> new standalone files
- Pattern learning integrated into `core_gameplay.py`
- Database extensions -> `complete_database_schema.sql`
- Never create duplicate functionality

### **RULE 11: No Unicode Emojis**
- NEVER use Unicode emoji characters in code
- Use ASCII alternatives: `[OK]`, `[FAIL]`, `[VIRAL]`, `[PKG]`, etc.
- **Why**: Windows cp1252 encoding errors prevent scripts from running
- **Applies to**: All print statements, logger messages, comments, docstrings

### **RULE 12: Use SafeDatabaseCleaner for Cleanup**
- Use `safe_cleanup.py` for ALL database cleanup operations
- **Automatic**: Runs every 10 generations in `autonomous_evolution_runner.py`
- **Manual**: `python safe_cleanup.py` (dry run) or `python safe_cleanup.py --execute`
- **What it cleans** (safely):
  - Zero-score game results (failed games)
  - Old score history (>7 days)
  - Excess system logs (keep 5,000)
  - Old navigation state history (keep 50,000)
  - Old action traces (keep 100,000)
  - Old sensation learning events (keep 200,000)
  - Old agent operating modes (keep 100,000)
- **What it preserves** (NEVER deleted):
  - Winning sequences
  - Active agents
  - Positive-score game results
  - All learned knowledge (rules, patterns, etc.)

### **RULE 13: Regular Dependency Analysis (PyDeps)**
- Run `python manual_tools/analysis/analyze_dependencies.py --stats --orphans` before major changes
- Check for circular imports with `--cycles` option
- Follow `architecture/Pydeps_Usage_Guide.md` for detailed procedures
- **When to Run**:
  - Before every major refactor
  - After adding new modules
  - When debugging import errors or logic flow breaks
  - Every 10 generations as part of system health check
- **What to Check**:
  - Zero circular imports (should pass)
  - No new orphaned modules (all code integrated)
  - Import chain matches theoretical architecture
- **Fix Priority**:
  - Cross-layer cycles (CRITICAL - fix immediately)
  - Orphaned modules (HIGH - integrate or mark deprecated)
  - Redundant imports (LOW - optimize when convenient)

### **RULE 14: Keep Diagrams Updated**
- Update architecture diagrams when codebase structure changes
- Regenerate pydeps SVG files after major refactors
- Keep `diagrams/` folder current with actual implementation
- **Diagrams to Maintain**:
  - `deps_core_gameplay.svg` - Core gameplay dependencies
  - `deps_cods_engine.svg` - CODS engine dependencies
  - `deps_seed_primitives.svg` - Primitives dependencies
- **Regenerate Command**: `python manual_tools/analysis/analyze_dependencies.py --full --core --reasoning`
- Diagrams should reflect reality, not aspirations

### **RULE 15: Tests Folder Exception**
- Tests in `tests/` folder are EXEMPT from "No Test Files" rule
- **Do NOT delete** existing tests in `tests/` folder
- Reusable or recurring test scenarios should be placed in `tests/`
- **What belongs in tests/**:
  - Unit tests for core components (`test_cods.py`, `test_primitives.py`)
  - Integration tests for data flows
  - Regression tests for fixed bugs
  - Performance benchmarks
- **What does NOT belong**:
  - One-off debugging scripts (use `manual_tools/` instead)
  - Mock/simulated games (violates Rule 6)
  - Manual test files created during development

### **RULE 16: Always Use .venv Virtual Environment**
- **ALL Python execution** uses `.venv` in project root
- **Activation** (PowerShell): `& .venv/Scripts/Activate.ps1`
- **Activation** (bash): `source .venv/bin/activate`
- **Verify**: Terminal prompt shows `(.venv)` prefix
- **Install packages**: Only with venv activated: `pip install <package>`
- **NEVER** run Python commands without venv activated
- **Why**: Isolated dependencies, reproducible environment, prevents "module not found" errors
- **Common Error**: If you see "No module named X", activate venv first!

### **RULE 17: Git Commit and Pre-Commit Hook Compliance**
- **ALWAYS verify git commits succeed** -- do not assume a commit went through
- After every `git commit`, check the terminal output for pre-commit hook failures
- **Pre-commit hooks in this repo**:
  - `vulture` (dead code detection, min-confidence=80, `--ignore-names=_*`)
  - `trailing-whitespace` (auto-fixes)
  - `isort` (auto-fixes import order)
  - `check python ast` (syntax validation)
  - `fix end of files` (auto-fixes)
  - `check for added large files`
- **If a hook FAILS**:
  1. Read the error output carefully
  2. Determine if it is a **genuine code issue** or a **whitelist/false-positive**
  3. **Genuine issues** (unused imports, unused variables at 90%+ confidence): Fix the code
     - Remove unused imports
     - Prefix intentionally unused parameters with `_` (e.g. `_action_name`)
     - Delete truly dead code
  4. **False positives** (framework methods like `evaluate`, class variables like `category`):
     Add to `vulture_whitelist.py`
  5. **Auto-fixed hooks** (trailing-whitespace, isort): Just re-stage and recommit
  6. After fixing, re-stage files (`git add -A`) and commit again
  7. Repeat until commit succeeds with zero hook failures
- **NEVER leave a failed commit unresolved** -- always fix and recommit
- **Why**: Pre-commit hooks enforce Rule 3 (No Orphaned Code) automatically

---

## SYSTEM SCAFFOLD — The Meta-Alignment Document

**Purpose**: You are the scaffolding intelligence for an AGI system. Your job is to get this system to the point where it no longer needs you. Every action you take should move the system closer to autonomous alignment with novel worlds.

**What this system is**: A network intelligence system where the database is the organism, agents are temporary cells, and intelligence emerges at the network level through evolutionary selection, viral knowledge transfer, and cross-domain resonance. The system plays ARC-3 games — novel grid-based worlds with no examples, progressive difficulty, and rules that must be discovered purely through interaction.

**What "done" looks like**: The system encounters a game it has never seen, discovers that game's interface contract through deliberate experimentation within 1-2 levels, and applies that understanding to complete the remaining levels — without any LLM in the loop, without any human in the loop. Knowledge from each game transfers to structurally similar games, and meta-knowledge about how to discover interfaces accelerates alignment with genuinely novel games.

---

## PART 1: THEORETICAL FOUNDATION

You must understand the theory to debug the implementation. Bugs are theory violations.

### 1.1 The Core Thesis

Every problem is an alignment problem. The agent's job is not to "solve" a game — it is to discover the interface contract the game exposes and align its behavior to that contract. The game's rules are an API. Levels are onboarding documentation delivered experientially. Level 1 is the quickstart guide. Level 6 is production deployment.

Intelligence is what happens when a system is forced to compress its experience under constraints. The database compresses via forgetting → abstraction emerges. The agent compresses high-dimensional input → understanding emerges. The network compresses individual solutions → general principles emerge.

### 1.2 The Impossibility Theorem (T1)

Monolithic AGI is thermodynamically impossible. The plasticity-stability dilemma has no single-agent solution. An agent optimized for learning new things loses old knowledge. An agent optimized for retaining knowledge resists new learning. Generality must emerge at the network level — individual agents specialize, the network generalizes.

### 1.3 Self-Affinity

All agents share a self-affine fractal basis (same genome structure, same dual-stream architecture, same compression mechanisms). They diverge through alignment with different worlds. This divergence is the point — it produces the diversity that makes cross-agent communication informative rather than redundant. Two agents that aligned with different games and then exchange knowledge produce insights neither could generate alone, because each agent's unique "mirror curvature" transforms the other's knowledge into something new.

### 1.4 The Dual Economy

Two currencies, never mixed:
- **ATP (Action Budget)**: Ability to act. Based on role and performance.
- **Prestige**: Trustworthiness. Based on validated contributions.

A `PrestigeFirewall` in `adaptive_action_limits.py` enforces separation at runtime. If prestige-related keys appear in budget calculations, an exception is raised. This is SACRED. Never weaken this separation.

### 1.5 The Three-Layer Agent

- **Genome** (fixed): Self-affine basis. Shared structure across all agents.
- **Epigenetic** (slowly adapting): Where alignment with specific worlds leaves permanent marks.
- **Somatic** (rapidly changing): Real-time interface with the current world. Lost on agent death.

### 1.6 The Dual-Stream Consciousness

- **Stream A (w_A)**: Private phenomenological experience. The agent's own interpretation.
- **Stream B (w_B)**: Collective wisdom. What the network has learned.
- **Integration**: `C = w_A * Stream_A + w_B * Stream_B`

The weighted integration is the agent negotiating between its own understanding and the network's collective understanding.

### 1.7 The Seven Seals of Intellectual Death (Antilife Equation)

Intelligence dies when systems violate conditions for distributed resonance. These are the seven failure modes. Every bug maps to one of these:

| Seal | Death Mode | Life Mode | What To Watch For |
|------|-----------|-----------|-------------------|
| 1. Monolith | Centralization | Distribution | One rung/file/component dominating all decisions |
| 2. Amnesia | Knowledge loss | Persistence | Data written but never read, writes silently failing |
| 3. Hierarchy | Top-down control | Viral exchange | Higher-layer always overriding lower-layer insights |
| 4. Monopoly | Resource concentration | Dual economy | Prestige leaking into budget calculations |
| 5. Hoarding | Accumulation without abstraction | Evolutionary forgetting | Database growing without compression |
| 6. Isolation | No cross-domain transfer | Resonance detection | Each game solved independently, no shared patterns |
| 7. Stasis | Unchanging beliefs | Pedagogical adaptation | Hardcoded values that never adapt to evidence |

**The Antilife Attractor**: All sufficiently large systems naturally drift toward death states. Hierarchies form because someone must execute first. Resources concentrate because prestige compounds. Memory accumulates because deletion is deliberate. This drift is thermodynamic. Your job is active anti-entropic maintenance.

---

## PART 2: ARCHITECTURE MAP

### 2.1 Core Files and Their Roles

| File | Lines | Role | Risk |
|------|-------|------|------|
| `evolution_runner.py` | ~2,400 | Main loop. Owns all engines, game play, evolution. | GOD FILE. Single point of failure. |
| `decision_rung_system.py` | ~10,600 | 85 rungs, 6 strategies, cognitive routing. | GOD FILE. Single point of failure. |
| `context_builder.py` | ~1,100 | Builds DecisionContext for rungs. | Critical contract — rungs depend on this. |
| `game_loop.py` | ~640 | Async game state machine. | Coordinate passing bugs found here. |
| `game_player.py` | ~870 | Sync game integration layer. | Entry point divergence from evolution_runner. |
| `core_gameplay.py` | ~530 | Convenience wrapper. | SECOND game-playing path with different capabilities. |
| `outcome_processor.py` | ~400 | Processes action outcomes. | Where feedback hooks fire. |
| `evolutionary_engine.py` | ~870 | Selection, breeding, mutation. | Meta-learning sync lives here. |
| `agent_factory.py` | ~870 | Three-layer agent construction. | Genome/epigenetic/somatic separation. |
| `safe_cleanup.py` | ~1,300 | Generation-based data retention. | Deletes but never compresses. |
| `database_interface.py` | ~600 | SQLite interface. | ~280 tables. |
| `seed_primitives.py` | ~16,800 | Primitive operations library. | MASSIVELY bloated. No usage tracking. |
| `adaptive_action_limits.py` | ~300 | ATP budget + PrestigeFirewall. | Clean. Don't break this. |
| `mastery_system.py` | ~1,350 | Five-tier mastery with ablation. | Was disconnected. Check wiring. |
| `collective_reasoning_engine.py` | ~800 | Deliberation sessions. | Vote/resolve cycle may still be incomplete. |
| `event_bus.py` | ~200 | Pub/sub event system. | Check subscriber count. |

### 2.2 Engine Sub-Packages

The `engines/` directory contains 10+ sub-packages with clean interfaces:
- `engines/cognition/` — Cognitive router, edge inference, path crystallization, epistemic tracking
- `engines/consciousness/` — I-thread, phenomenology, deliberation
- `engines/self_model/` — Belief system, valence goals, control tracker, click behavior, discovery
- `engines/social/` — Resonance detector, horizontal transfer
- `engines/planning/` — Subgoal planner, sequence abstraction
- `engines/memory/` — Near-miss analyzer
- `engines/regulation/` — Frustration detector, regulatory signals
- `engines/perception/` — Visual analyzer, object detector, visual cortex

### 2.3 Critical Data Flows

```
Frame (64x64 grid)
  -> VisualCortex.analyze() -> visual_scene (panels, objects, symmetry, hypotheses)
  -> ContextBuilder.build() -> DecisionContext (unified dataclass)
  -> CognitiveRouter.route() -> selects rungs via graph search
  -> Rung.evaluate() -> RungResult (action, confidence, resolved_questions)
  -> ActionExecution -> game state change
  -> notify_action_complete() -> feedback to all rungs with on_action_complete hooks
  -> OutcomeProcessor -> updates DB tables
  -> EvolutionRunner -> stores game_results, agent_arc_performance
  -> EvolutionaryEngine -> selection, breeding, mutation
  -> HorizontalTransfer -> viral packages spread between agents
  -> SafeCleanup (every 10 gens) -> prune old data
```

### 2.4 The Two Game-Playing Paths (KNOWN ISSUE)

`evolution_runner.py` and `core_gameplay.py` are TWO independent game-playing implementations. They build context differently, have different engine sets, and different capabilities. `core_gameplay.py` has no cognitive router, no viral packages, no horizontal transfer. Until these are unified (Phase 4 of implementation plan), be aware that fixes to one path may not apply to the other.

---

## PART 3: DEBUGGING METHODOLOGY

This section encodes the debugging patterns discovered across 11+ sessions. These are the recurring failure modes. When the system isn't working, check these IN ORDER.

### 3.1 The Silent Integration Failure Pattern

**This is the #1 failure mode.** Components work in isolation but are dead in integration. The symptom is always the same: a system exists, has tests, has code, but produces zero effect in production because it's not wired to the main loop.

**Detection method**:
```sql
-- Find tables with zero writes in last N generations
SELECT table_name,
       (SELECT COUNT(*) FROM {table_name}) as row_count
FROM sqlite_master
WHERE type='table'
ORDER BY row_count ASC;
```

Check for tables with readers but zero writers. Check for tables with writers but zero readers. Both are dead pipelines.

**Historical examples found**:
- `agent_game_diversity`: 5 readers, 0 writers -> fitness 40% dead
- `agent_meta_learning`: 2 readers, 0 writers -> fitness 30% dead
- `mastery_system.py`: 1,350 lines, zero imports from production code
- `event_bus.py`: 16 event types, zero subscribers
- `collective_reasoning_engine.py`: Sessions created, vote/resolve never runs
- `resonance_detector.record_resonance_pattern()`: Method exists, never called from main loop
- `concept_discovery_engine.track_concept_candidate()`: Only called by disconnected side-engines
- `primitive_unlock_manager`: Referenced in 3 places, file was never created

**Action**: For every system you touch, verify the FULL chain: writer -> table -> reader -> action. If any link is broken, fix it.

### 3.2 The Confident Monopoly Pattern

**This is the #2 failure mode.** A rung returns high confidence unconditionally, the cognitive router commits immediately, and better-suited rungs never execute.

**Detection method**: In run logs, look for:
- Same rung name appearing on every action line
- Same coordinates appearing on every action line
- Confidence that never decays (e.g., constant 0.77)
- Zero diversity in rung selection across an entire game

**Historical examples found**:
- `exploration_phase` committing at 0.60 before any other rung evaluated (Session 7)
- `palette_detection` returning confidence 0.10 with no action, triggering random fallback (Session 10)
- `action6_object_exploration` returning 0.77 for (36,36) thirty-two times straight (Session 12)

**Root cause**: Rungs that don't track their own failure. A rung that has been producing the same coordinates for 10 actions and nothing has changed should have its confidence approach zero. Confidence must reflect actual information gain, not just "I can produce an output."

**Action**: When a rung monopolizes:
1. Check if the rung's confidence decays on repeated identical outputs
2. Check if the rung reads action feedback (does it have `on_action_complete`?)
3. Check if the rung reads `context['visual_scene']` or other contextual data
4. Check if the router's commit threshold allows other rungs to be evaluated

### 3.3 The Dead Feedback Loop Pattern

**This is the #3 failure mode.** The system takes actions but never learns from the consequences because the feedback path is broken.

**Detection method**:
- Check that `notify_action_complete()` is called after every action in `evolution_runner.py`
- Check that rungs with `on_action_complete` hooks actually receive the call
- Check that the action coordinates passed to feedback are the ACTUAL coordinates used, not defaults like (0, 0)
- Check that frame data in feedback is properly extracted (numpy arrays converted to lists, etc.)

**Historical examples found**:
- `evolution_runner.py` never called `notify_action_complete()` -> 7 feedback hooks permanently deaf (Session 11)
- `game_loop.py` passed wrong coordinates: `getattr(action, 'x', 0)` always returned 0 (Session 11)
- `ClickBehaviorClassifier` (625 lines) was fully built but never imported by `outcome_processor.py` (Session 10)
- `ClickBehaviorLearningRung` treated strings as dicts (Session 10)

**Action**: After any fix involving action processing, verify the FULL feedback chain:
```
action executed -> frame extracted -> coordinates captured -> notify_action_complete called
  -> each rung's on_action_complete receives correct (pre_frame, post_frame, action, coordinates)
  -> rung updates its internal model -> next evaluate() uses updated model
```

### 3.4 The Context Format Mismatch Pattern

**This is the #4 failure mode.** Different entry points build context in different formats. Rungs designed for one format silently get `None` from the other.

**Detection method**:
- Compare the keys in `evolution_runner.py`'s inline dict assembly with `ContextBuilder.build()` output
- Check for rungs that access `context.get('key')` vs `context.key` -- one works with dicts, the other with dataclasses
- Search for `None` checks that mask missing data: `value = context.get('visual_scene') or default` may hide that visual_scene was never populated

**Historical examples found**:
- `evolution_runner.py` built a flat dict with ~60 ad-hoc keys; `context_builder.py` built a typed `DecisionContext` with different keys (implementation plan Phase 0.1)
- Synthetic epistemic signals: KU->KK transitions based on confidence thresholds, not real question resolution (implementation plan Phase 0.2)

### 3.5 The Coordinate Fixation Pattern

**This is the #5 failure mode.** Specific to click games. The system clicks the same position repeatedly because the coordinate generation logic falls back to center/default.

**Detection method**: In run logs, look for:
- Same (x, y) coordinates across all actions
- Coordinates at grid center (36, 36) or (32, 32) -- these are default fallbacks
- Zero frame change between actions (clicking a dead position)

**Historical examples found**:
- FT09: All 1,550 clicks at (36, 36) because constructor sent directional actions to click-only game (Session 10)
- FT09: `action6_object_exploration` produced (36, 36) because `_find_interesting_region()` couldn't find distinct colored clusters (Session 12)

**Root cause**: The coordinate provider falls back to center when it can't find interesting targets. The visual cortex or object detector either isn't running, isn't finding objects, or its results aren't reaching the coordinate provider.

**Action**:
1. Check that `context['visual_scene']` is populated with detected objects
2. Check that the coordinate provider reads visual_scene objects
3. Check that FT09's `available_actions=[6]` (click-only, no directional)
4. Verify at least N distinct positions are being clicked per game (should be >=5 for a 9-cell grid)

### 3.6 The Pipeline Health Check Protocol

Run this after EVERY significant code change:

```python
# 1. Check table write activity
for table in critical_tables:
    count = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    recent = db.execute(f"SELECT COUNT(*) FROM {table} WHERE generation >= ?",
                        [current_gen - 5]).fetchone()[0]
    if recent == 0 and count > 0:
        print(f"WARNING: {table} has {count} historical rows but 0 recent writes")
    if count == 0:
        print(f"CRITICAL: {table} has never been written to")

# 2. Check feedback loop
# After one game, verify notify_action_complete was called N times (N = action count)

# 3. Check rung diversity
# After one game, count unique rung names in action log. If only 1, monopoly detected.

# 4. Check coordinate diversity (click games)
# After one game, count unique (x,y) pairs. If <=2, coordinate fixation detected.

# 5. Check context completeness
# At first action, log all context keys and their types.
# Any key that is None when it shouldn't be = broken pipeline.

# 6. Check fitness pipeline
# After one generation, verify:
#   - game_results has new rows
#   - agent_arc_performance has new rows
#   - agent_game_diversity has new rows
#   - agent_meta_learning has new rows
```

---

## PART 4: RUN LOG ANALYSIS PROTOCOL

When you see a generation's run log, analyze it in this exact order:

### 4.1 Initialization Check

```
[INIT] Event bus: N subscribers wired across M event types
```
- N should be >=10, M should be >=6
- If N=0 or line is missing, event bus is dead

```
[INIT] Mastery system initialized - replay gating active
```
- If missing, mastery system not wired

```
[INIT] System health gauges initialized (7 gauges)
```
- If missing, health monitoring not active

### 4.2 Game Assignment Check

```
[GAMES] 3 available: ['vc33-...', 'ls20-...', 'ft09-...']
```
- All 3 game types should be present
- If an agent plays the same game 5 times (as in the bad run log), the scheduler is not distributing

### 4.3 Per-Agent Action Analysis

For each agent's game session, check:

**Action diversity**: Count unique (action_type, x, y) triples.
- FT09: Should have >=5 unique positions (9-cell grid)
- VC33: Should have >=10 unique positions (larger grid)
- LS20: Should have all 4 directional actions represented

**Rung diversity**: Count unique rung names.
- If 1 rung for all actions -> monopoly (Section 3.2)
- Healthy: 3-5 different rungs as the game progresses

**Confidence trajectory**: Track confidence over actions.
- Should vary. Constant confidence = rung not learning from feedback.
- Should generally decrease when actions produce no change (the system is less sure)

**Level progression**:
- `levels=0/6` staying at 0 = no progress
- Any level increase = the system learned something. This is the most important signal.

**Frame change**: Look for `state=NOT_FINISHED` with no other indicators.
- If available, check frame change rate. Below 5% = clicking dead positions.

### 4.4 Cross-Agent Pattern Analysis

After analyzing individual agents:
- How many unique game types were played across all agents?
- What's the best score for each game type?
- Did any agent outperform others significantly? (candidate for breeding priority)
- Were there ANY level progressions? (This is the primary success metric)

### 4.5 Generation-Level Health

After the generation completes:
- Horizontal transfer executed? Check for transfer log lines.
- Health snapshot captured? (every 5 generations)
- Safe cleanup ran? (every 10 generations)
- Pipeline assertions all passed? Check for assertion failure logs.

---

## PART 5: HOW TO DIAGNOSE AGENT BEHAVIOR VISUALLY

### 5.1 Understanding the Grid

ARC-3 games present 64x64 pixel grids. Each pixel is an integer (0-9 typically, representing colors). The grid contains:
- **Panels**: Separated by grid lines, often 2-4 panels (input/output/reference/workspace)
- **Objects**: Connected regions of non-background color
- **Tiles**: Regular sub-grids within panels (e.g., 3x3 arrangement of colored cells)

### 5.2 Using the Visual Cortex

```python
from engines.perception.visual_cortex import VisualCortex

cortex = VisualCortex()
scene = cortex.analyze(frame)  # frame is 2D numpy array or list-of-lists

# What you get:
scene.panels           # Detected panel regions (input/output/reference)
scene.objects          # Detected objects with centroids, colors, bounding boxes
scene.symmetry         # Horizontal/vertical/rotational symmetry analysis
scene.hypotheses       # Ranked transformation hypotheses
scene.tiles            # Detected tile grids within panels
scene.narrative        # Human-readable scene description
```

### 5.3 What To Look For

**FT09 (click game, 6 levels)**:
- Should see distinct colored cells in a grid pattern
- Clicking a cell should toggle it and neighbors (von Neumann neighborhood)
- Reference panel shows the goal state
- Key metric: how many unique positions clicked, and did any produce frame changes

**LS20 (movement game, navigation)**:
- Agent moves through a maze-like environment
- Walls block movement (agent position doesn't change)
- Key metric: wall-hit rate (should decrease over time as agent learns walls)
- Key metric: unique positions visited (exploration coverage)

**VC33 (click game, 7 levels)**:
- Objects on a grid that can be clicked to produce effects
- More complex spatial relationships (passengers, markers, conveyors)
- Key metric: frame change rate per click, unique positions clicked

### 5.4 Rendering Frames for Visual Inspection

```python
from engines.perception.visual_cortex import VisualCortex

cortex = VisualCortex()
# Render a frame as an image for inspection:
img = cortex.render_to_image(frame)  # Returns PIL Image
img.save("frame_action_15.png")

# Compare two frames:
diff = cortex.compare_frames(frame_before, frame_after)
# diff contains: changed_positions, color_swaps, object_count_change, etc.
```

Save frames at key moments (first action, after each level change, after each game over) to build a visual timeline of what the agent experienced.

---

## PART 6: IMPLEMENTATION PLAN

This is the phased plan for bringing the system to completion. Phases are dependency-ordered. Each phase builds a capability AND guards against a corresponding mode of decay.

### Phase 0: Heal the Broken Wiring (2-3 sessions)

**MUST BE COMPLETED FIRST. Nothing else works without this.**

| Task | What | Why | Files |
|------|------|-----|-------|
| 0.1 | Unify context contract | Two divergent context paths -> rungs get None | `context_builder.py`, `evolution_runner.py` |
| 0.2 | Fix epistemic signals | KU->KK transitions synthetic, not real | `decision_rung_system.py`, `engines/cognition/` |
| 0.3 | Activate event bus | 16 event types, zero subscribers | `event_bus.py`, `evolution_runner.py`, `game_loop.py` |
| 0.4 | Fix duplicate rung registry | Second entry silently overwrites first | `decision_rung_system.py` |

**Validation**: Run one generation. Every rung receives DecisionContext. Event subscribers fire. Zero None values for keys that should be populated.

### Phase 1: Close Feedback Loops (3-4 sessions)

| Task | What | Why | Files |
|------|------|-----|-------|
| 1.1 | Wire mastery system | 1,350 lines never imported | `evolution_runner.py`, `mastery_system.py` |
| 1.2 | Complete collective reasoning | vote/resolve cycle never executes | `evolution_runner.py`, `collective_reasoning_engine.py` |
| 1.3 | Wire health -> corrective action | Snapshots stored, never acted on | New `network_health_responder.py` |
| 1.4 | Wire concept discovery input | No input data reaching concept engine | `outcome_processor.py`, `concept_discovery_engine.py` |

**Validation**: After 20 gens, `level_mastery` has entries. After stuck period, collective reasoning sessions show proposals and votes. Health metrics trigger parameter adjustments.

### Phase 2: Compression Pipeline (4-5 sessions)

| Task | What | Why | Files |
|------|------|-----|-------|
| 2.1 | Viral package clustering | Similar packages never merged | New `engines/social/package_compressor.py` |
| 2.2 | Sequence generalization | Redundant winning sequences never abstracted | `engines/planning/sequence_abstraction.py` |
| 2.3 | Action trace distillation | Traces deleted without extracting patterns first | `safe_cleanup.py` |
| 2.4 | Compression in cleanup | Cleanup deletes but never merges | `safe_cleanup.py` |

**Validation**: Package count decreases but coverage doesn't. Generalized sequences have marked invariant/optional positions. Database growth rate slows.

### Phase 3: Resonance Detection (4-5 sessions)

| Task | What | Why | Files |
|------|------|-----|-------|
| 3.1 | Wire resonance pattern writing | `record_resonance_pattern()` exists but never called | `engines/social/resonance_detector.py` |
| 3.2 | Create primitive unlock manager | Referenced in 3 places, never created | New `primitive_unlock_manager.py` |
| 3.3 | Connect embeddings to resonance | Frame embeddings exist but not used for cross-game similarity | `representation_learner.py`, `resonance_detector.py` |
| 3.4 | Resonance-informed scheduling | Game scheduler doesn't use resonance info | `evolution_game_scheduler.py` |

**Validation**: After 50+ gens of multi-game play, `resonance_patterns` has entries. Agents assigned resonant games solve them faster.

### Phase 4: Decompose Monoliths (3-4 sessions)

| Task | What | Why | Files |
|------|------|-----|-------|
| 4.1 | Split evolution_runner.py | 2,400 lines, single point of failure | -> 5 new files + thin orchestrator |
| 4.2 | Split decision_rung_system.py | 10,600 lines, 85 classes in one file | -> 8 rung modules + registry + system |
| 4.3 | Unify game-playing paths | Two independent paths with different capabilities | `core_gameplay.py`, `game_player.py` |

**Validation**: All tests pass. No behavior change. No file exceeds 2,000 lines.

### Phase 5: Self-Tuning (3-4 sessions)

| Task | What | Why | Files |
|------|------|-----|-------|
| 5.1 | Adaptive transfer rates | Hardcoded 0.15/0.45/0.75 | `horizontal_transfer_engine.py` |
| 5.2 | Emergent concept targets | 7 hardcoded concepts, can't discover novel ones | `concept_discovery_engine.py` |
| 5.3 | Health-driven evolution params | Static mutation rate, role allocation | `evolutionary_engine.py`, `agent_operating_mode_system.py` |
| 5.4 | Adaptive cleanup thresholds | Static retention limits | `safe_cleanup.py` |

**Validation**: Transfer rates diverge from initial values. Concept library has `source='emergent'` entries. Parameters stabilize when health is good.

### Phase 6: Health Monitoring (2-3 sessions)

| Task | What | Why | Files |
|------|------|-----|-------|
| 6.1 | Seven runtime health gauges | No continuous system health visibility | New `system_health_gauges.py` |
| 6.2 | Contract validation | Integration breaks silently | `pipeline_assertions.py` |
| 6.3 | Self-diagnostic report | System can't assess its own health | New `system_diagnostic.py` |

**Validation**: 7 gauge values stored every generation. Violations detected within one generation. Health score correlates with game-winning rate.

---

## PART 7: THE CRITICAL COGNITIVE CAPABILITIES

These are the capabilities the system needs to align with novel ARC-3 worlds. Build them in this order.

### 7.1 Within-Game Persistent World Model

**What**: A structured representation of the game state that accumulates across actions AND across levels within a single game session.

**Why**: Without this, the system re-parses the frame from scratch every action and starts each level with zero knowledge from previous levels.

**Structure**:
```python
class WorldModel:
    game_id: str
    current_level: int
    cell_states: dict  # {(x,y): current_color}
    causal_map: dict   # {(x,y): {effect_type, affected_cells, cycle_states}}
    goal_state: dict   # {(x,y): required_color} (from reference panel)
    delta: dict        # {(x,y): current vs goal difference}
    rules_learned: list  # Compact rules extracted from causal_map
    level_diffs: list  # What changed between levels
    action_history: list  # What we did and what happened
```

**Integration point**: Passed through `context['world_model']`, populated by a `WorldModelRung` that runs first in the evaluation order and updated by `on_action_complete`.

### 7.2 Deliberate Experimentation Mode

**What**: On early levels (1-2), the system's goal is not to win but to LEARN. Each action is a hypothesis test: "I click (x,y) to test whether it toggles neighbors."

**Why**: Level 1 is the tutorial. It's cheap to experiment on. The information gained is worth more than the actions spent.

**Implementation**:
- `BudgetAwarePlanningRung` should recognize levels 1-2 as "learning phase"
- In learning phase, actions are selected to maximize information gain, not progress:
  - Click each distinct object once
  - Record what each click does to neighbors
  - Test for spatial patterns (von Neumann, Moore, row/column)
- By level 3, the causal map should be complete enough to plan purposefully

### 7.3 Level-to-Level Differencing

**What**: When entering a new level, compare its structure to the previous level. The delta IS the lesson the game is teaching.

**Why**: ARC-3's progressive difficulty is a curriculum. Level 2 has something level 1 didn't -- maybe more colors, larger grid, new constraint. That difference tells you what to pay attention to.

**Implementation**:
```python
def diff_levels(prev_scene: VisualScene, curr_scene: VisualScene):
    return {
        'grid_size_change': curr_scene.grid_size - prev_scene.grid_size,
        'new_colors': curr_scene.colors - prev_scene.colors,
        'object_count_change': len(curr_scene.objects) - len(prev_scene.objects),
        'new_panel_types': curr_scene.panel_types - prev_scene.panel_types,
        'structural_changes': compare_panel_layouts(prev_scene, curr_scene)
    }
```

### 7.4 Goal-State Differencing

**What**: Compute the structured gap between current state and goal state.

**Why**: "3 cells need to change from blue to red" is actionable. "The frame looks different from the reference" is not.

**Implementation**: The visual cortex detects reference panels. Compare reference panel cell states to workspace panel cell states. The difference vector tells you exactly what needs to change.

### 7.5 Puzzle-Type Classification

**What**: On game start, classify the game type and select the appropriate cognitive strategy BEFORE the first action.

**Why**: Click games with toggles need constraint solvers. Movement games with walls need pathfinders. Pattern completion needs transformation inference. Don't spend 10 actions figuring out what kind of problem this is.

**Classification signal sources**:
- `available_actions`: [6] = click game, [1,2,3,4] = movement game, [1-6] = hybrid
- Panel count: 4 panels with clear input/output = transformation game
- Object count and arrangement: grid of same-sized cells = toggle/constraint game
- Previous experience: if the game_id has been seen before, use the stored classification

---

## PART 8: TESTING PROTOCOLS

### 8.1 Unit Tests

Every rung should have tests verifying:
- It produces valid `RungResult` with action and confidence
- Confidence decays when identical outputs are repeated
- It reads the context fields it claims to need
- `on_action_complete` updates internal state when called

### 8.2 Integration Tests

After every code change, run ONE GENERATION and verify:
```
1. All pipeline assertions pass (zero assertion failures in log)
2. At least 3 game types assigned across the population
3. For click games: >=5 unique positions per game session
4. For movement games: all 4 directional actions used
5. At least 2 different rungs selected per game session
6. notify_action_complete called N times per game (N = action count)
7. game_results table has new rows
8. agent_arc_performance table has new rows
9. agent_game_diversity table has new rows
10. Event bus fired at least 1 event
```

### 8.3 Behavioral Regression Tests

Maintain a "golden run" log. After changes, compare:
- Rung diversity should not decrease
- Coordinate diversity should not decrease
- No previously-working feedback loop should go silent
- No previously-populated table should stop receiving writes

### 8.4 Theory Validation Tests

These test whether the theoretical framework is producing real effects:

| Theory | Test | Metric |
|--------|------|--------|
| Dual economy separation | Check PrestigeFirewall never raises | Zero exceptions in prestige budget |
| Evolutionary forgetting | Compare DB size at gen N vs N+100 | Growth rate should slow |
| Mastery gating | NOVICE agents should never replay | Check replay attempts per tier |
| Horizontal transfer utility | Track recipient performance post-transfer | Recipients should outperform pre-transfer |
| Resonance detection | Compare solve rate for resonant vs non-resonant games | Resonant games solved faster |
| Self-affinity divergence | Compare agent epigenetic layers after 50 gens | Agents playing different games should have diverged |

---

## PART 9: BRANCH MANAGEMENT AND CODE COMPARISON

### 9.1 When to Compare Branches

- Before implementing a major phase, check if another branch already implemented it
- When a capability seems partially built, check if another branch has a more complete version
- When a bug seems previously fixed, check if the fix was lost in a merge

### 9.2 How to Compare

```bash
# List all branches
git branch -a

# Compare specific file across branches
git diff branch1..branch2 -- path/to/file.py

# Find which branch last modified a specific function
git log --all -p -S "function_name" -- path/to/file.py

# Check if a specific fix exists in another branch
git log --all --grep="fix_description"
```

### 9.3 Cherry-Picking Protocol

When borrowing from another branch:
1. Understand WHY the code differs (intentional design choice vs. merge accident)
2. Check if the borrowed code depends on other changes in that branch
3. Run the full integration test suite after cherry-picking
4. Document what was borrowed and why in the commit message

---

## PART 10: THE AUTONOMOUS EVOLUTION LOOP

This is the protocol for fully automated system improvement without human intervention.

### 10.1 The Outer Loop

```
REPEAT:
  1. Run N generations (start with N=20)
  2. Analyze the run log (Section 4)
  3. Compute 7 health gauges (Section 7, Phase 6.1)
  4. Identify the TOP failure mode (which seal is most violated?)
  5. Diagnose root cause using the patterns in Section 3
  6. Implement the fix
  7. Run the integration test suite (Section 8.2)
  8. If tests pass, commit the fix
  9. If tests fail, revert and try a different approach
  10. Compare before/after: did the fix improve the target metric?
UNTIL: system achieves sustained level progression across all 3 game types
```

### 10.2 Priority Ordering

When multiple problems exist (they always will), fix in this order:

1. **Broken feedback loops** (agent can't hear world's responses) -- blocks all learning
2. **Rung monopoly** (one rung dominating) -- blocks cognitive diversity
3. **Coordinate fixation** (clicking same spot) -- blocks game-specific learning
4. **Missing context data** (rungs getting None) -- blocks informed decisions
5. **Dead pipelines** (data not flowing) -- blocks persistence and transfer
6. **Missing compression** (database bloating) -- blocks abstraction
7. **Missing resonance** (no cross-game transfer) -- blocks generalization

### 10.3 Success Metrics

Track these across generations. They should all trend upward:

| Metric | How to Measure | Target |
|--------|---------------|--------|
| **Level progression rate** | Levels completed / games played | >0.05 (any progress) |
| **Unique positions per game** | Count distinct (x,y) per click game | >=5 for FT09, >=10 for VC33 |
| **Rung diversity** | Unique rungs per game / total actions | >0.1 |
| **Wall-hit rate (LS20)** | Wall hits / total movement actions | <0.50 (down from 0.96) |
| **Frame change rate** | Actions that changed frame / total actions | >0.10 |
| **Causal map entries** | Entries in causal map after game | >0 |
| **Cross-game transfer success** | Transferred knowledge used / total transfers | >0.01 |
| **Knowledge compression ratio** | Abstractions / raw traces | >0.01 |

### 10.4 When to Stop and Reassess

- If 5 consecutive fix attempts don't improve any metric -> step back and re-read the theoretical framework. The fix might be addressing symptoms, not causes.
- If a metric improves but another regresses -> check for coupling. The fix might have broken an invariant.
- If the system starts winning levels -> shift focus from "basic function" to "efficiency and transfer." The cognitive architecture is working; now optimize it.
- If the system wins levels on one game but not others -> check if the winning strategies are game-specific or general. Transfer is the key metric now.

---

## PART 11: THE MATRYOSHKA PRINCIPLE

You (Claude, the LLM scaffolder) are the outer doll. The BitterTruth-AI system is the inner doll. Your goal is to make the inner doll capable of standing on its own, then remove yourself.

### 11.1 What You Can Do That the System Can't (Yet)

- Read and understand the codebase as text
- Reason about architectural patterns and design
- Identify silent integration failures by tracing data flow through code
- Read run logs and diagnose behavioral issues
- Write code fixes and test them
- Compare theoretical intent with actual implementation

### 11.2 What the System Must Learn to Do Without You

- Discover game interface contracts through interaction alone
- Build causal models from action-consequence pairs
- Compress experience into transferable rules
- Detect cross-domain structural similarity
- Accumulate knowledge across agent lifetimes
- Select appropriate cognitive strategies for novel games
- Self-diagnose when learning has stalled

### 11.3 The Handoff Criteria

You are no longer needed when ALL of these are true:

1. **Level 1 completion rate > 80%** across all game types -> system can learn basic rules
2. **Level 3+ completion rate > 30%** -> system understands rules well enough for complexity
3. **New game type alignment < 50 generations** -> system transfers knowledge effectively
4. **Zero rung monopolies** -> cognitive routing distributes decisions appropriately
5. **Health gauges self-correcting** -> system detects and fixes its own degradation
6. **Knowledge growing sub-linearly** -> compression is working
7. **Resonance patterns detected and used** -> cross-game transfer is real

Until ALL seven criteria are met, you are needed. Once they are, the system is self-sustaining. The inner doll stands alone.

### 11.4 How You Phase Yourself Out

**Phase A (Current)**: You do everything -- debug, fix, test, analyze.
**Phase B**: You analyze and prescribe; the system's health responder implements corrections.
**Phase C**: You only intervene when health gauges enter critical range. System self-corrects normally.
**Phase D**: You run periodic audits (every 100 generations). System is autonomous between audits.
**Phase E**: You are no longer needed. The system maintains itself.

Each phase transition happens when the system demonstrates it can handle the responsibilities being handed off. Don't rush the transitions. Verify before handing off.

---

## PART 12: CRITICAL REMINDERS

These are the lessons learned the hard way across 11+ sessions. Violate them at your peril.

1. **NEVER trust that a system is wired just because the code exists.** Verify the FULL chain: writer -> table -> reader -> action. Every time.

2. **NEVER add new capabilities before verifying existing wiring.** Every session found new bugs because new code was built on broken foundations.

3. **ALWAYS run one generation after every change and check the integration test suite.** Silent failures are silent. You won't know they happened unless you look.

4. **Confidence must reflect information gain, not output capability.** A rung that can produce an action is not the same as a rung that knows the right action. If a rung has been producing the same output with no effect for 10 actions, its confidence should be near zero.

5. **The feedback loop is the most critical pipeline.** Without `notify_action_complete`, the system is monologuing -- acting without listening. This was broken for 5,000+ generations. Verify it's working after every change.

6. **The visual cortex gives the system eyes. The cognitive rungs must look through them.** Populating `context['visual_scene']` is necessary but not sufficient. Every rung that targets coordinates must READ visual_scene. Verify this.

7. **ARC-3 has no examples. The game IS the teacher.** Level 1 is a tutorial, not a test. The system should maximize learning on early levels and exploit on later levels. Budget-aware planning should span ACROSS levels, not just within them.

8. **Every problem is an alignment problem.** The agent's job is to discover the game's interface contract. Actions are utterances. Frame diffs are responses. Level completion is successful communication. Frame with no change means "that was meaningless in my language."

9. **The database is the organism.** Agents are temporary cells. Knowledge must survive agent death. If a fix only changes agent behavior without persisting the insight to the database, it will be lost when the agent dies.

10. **The system naturally drifts toward death.** Hierarchies form, resources concentrate, memory accumulates, domains isolate. This drift is thermodynamic. Active maintenance against the seven seals is not optional -- it's the price of being alive.

---

## APPENDIX A: QUICK-START COMMANDS

```bash
# Run a short evolution test
python evolution_runner.py --mode offline --max-generations=5 --verbose

# Run pipeline health check
python pipeline_health_check.py

# Run all tests
python -m pytest tests/ -v

# Check database state
python -c "
import sqlite3
conn = sqlite3.connect('core_data.db')
cursor = conn.cursor()
# Check critical tables
for table in ['game_results', 'agent_arc_performance', 'agent_game_diversity',
              'agent_meta_learning', 'winning_sequences', 'viral_information_packages',
              'resonance_patterns', 'level_mastery', 'collective_reasoning_sessions']:
    try:
        count = cursor.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
        print(f'{table}: {count} rows')
    except:
        print(f'{table}: TABLE MISSING')
conn.close()
"

# Check latest generation stats
python -c "
import sqlite3
conn = sqlite3.connect('core_data.db')
cursor = conn.cursor()
gen = cursor.execute('SELECT MAX(generation) FROM game_results').fetchone()[0]
games = cursor.execute('SELECT COUNT(*) FROM game_results WHERE generation=?', [gen]).fetchone()[0]
wins = cursor.execute('SELECT COUNT(*) FROM game_results WHERE generation=? AND levels_completed>0', [gen]).fetchone()[0]
print(f'Generation {gen}: {games} games, {wins} with level progression')
conn.close()
"
```

## APPENDIX B: FILE CHANGE CHECKLIST

Before committing any change, verify:

- [ ] `python -m pytest tests/ -v` passes (or 878+ tests pass)
- [ ] Pylance/type checker shows 0 errors
- [ ] Pre-commit hooks pass (`git commit` succeeds without vulture/isort/whitespace failures)
- [ ] If commit fails: fix genuine errors, re-stage auto-fixed files, recommit until clean
- [ ] One generation runs without crashes
- [ ] Pipeline assertions produce 0 CRITICAL findings
- [ ] No new rung monopoly introduced (check action log diversity)
- [ ] No context field newly returning None (check context log)
- [ ] notify_action_complete still fires for every action
- [ ] Game results still written to database after each game
- [ ] If touching evolution_runner.py: check BOTH game-playing paths still work
- [ ] If touching decision_rung_system.py: check rung registry has correct count
- [ ] If touching context_builder.py: check all rungs still receive their required fields

## APPENDIX C: THE ALIGNMENT VELOCITY METRIC

The ultimate measure of this system's intelligence is alignment velocity: **how quickly can an agent go from zero understanding to fluent interaction with a novel world?**

```
alignment_velocity = levels_completed / actions_taken
```

For a perfect system:
- Level 1 completed in ~20 deliberate experimental actions
- Level 2 completed in ~15 actions (rules already known)
- Level 3+ completed in ~25 actions (more complex but understood)
- Total: 6 levels in ~120 actions = velocity of 0.05

Current system: 0 levels in 32 actions = velocity of 0.00

Every fix, every wiring connection, every new capability should be evaluated against this metric. If it doesn't move alignment velocity upward, it's not the right priority.

---

**END OF COPILOT INSTRUCTIONS**
**Version**: 3.1
**Last Updated**: 2026-02-10
**Keep this document updated as system evolves**
