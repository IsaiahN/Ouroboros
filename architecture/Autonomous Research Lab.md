# Autonomous Research Lab

## Purpose
A self-running scientific research loop that evolves the BitterTruth-AI codebase toward full game wins across all test games (FT09, VC33, LS20) without human intervention — except at the final merge gate into production branches.

## Sacred Branches
- `Ouroboros-v3` and all `Ouroboros-v*` branches are **production branches**
- No autonomous agent may ever commit, push, merge, rebase, or modify these branches
- The human is the sole merge authority for production branches
- All autonomous work happens on experiment branches owned by the lab

---

## Benchmarks: How the Lab Measures Progress and Knows When It's Done

### The Five Metrics (in order of priority)

**Metric 1: Level Completion Rate**
Per-game, per-level: what percentage of agents complete each level?
- Tracked as: `% of agents that complete Level N` for each game
- Example: "FT09 L1: 85%, L2: 42%, L3: 12%, L4: 0%, L5: 0%, L6: 0%"
- This shows exactly where agents are getting stuck — which level is the current wall

**Metric 2: Full Game Completion Milestone**
End-to-end: can any agent beat the entire game (all levels) in a single run?
- Binary milestone per game: has full completion ever been achieved?
- Once achieved, tracks consistency (see Metric 3)
- First full game completion for each game is a major lab milestone that triggers a human notification

**Metric 3: Game Completion Frequency per Generation**
Per-game, per-generation: how many agents out of the population complete the full game?
- Tracked as: `N out of 50 agents completed all levels of [game]` per generation
- Example: "Gen 5200: FT09 15/50 (30%), VC33 3/50 (6%), LS20 0/50 (0%)"
- This measures how robust the reasoning is — a single lucky agent completing a game is noise; 40/50 completing it is genuine capability

**Metric 4: Action Efficiency per Level**
Per-game, per-level: how many actions do agents take to complete each level?
- Tracked as: median and minimum action count for agents that completed the level
- Example: "FT09 L1 — median: 23 actions, min: 8 actions, trend: decreasing"
- High completion + high action count = brute-force stumbling into solutions
- High completion + low action count = genuine understanding
- The minimum converges toward the game's true optimal (which nobody in the lab knows — it discovers it empirically)

**Metric 5: Aggregate Action Efficiency per Game**
Total actions across all levels for full game completions:
- Tracked as: median and minimum total action count for agents that completed all levels
- Example: "FT09 full game — median: 89 total actions, min: 34 total actions"
- This is the ultimate efficiency measure — can agents not just beat every level, but do so without wasted moves?

### Stabilization = Completion

The lab is "done" when **all five metrics stabilize at their optimal bounds simultaneously:**

1. Level completion rates are at or near 100% for all levels of all games
2. Full game completion has been achieved for all three games
3. Game completion frequency is consistently high (e.g., 40+/50 agents per generation)
4. Per-level action counts have converged — diminishing returns across generations, the minimum isn't dropping anymore
5. Aggregate action counts have converged — the total-actions curve has flattened

**Stabilization is defined as:** After N generations (e.g., 1000+), the rate of improvement across all five metrics drops below a threshold (e.g., <0.1% improvement per generation sustained over 100 generations). The agents are consistently completing all games, doing so efficiently, and no amount of further code evolution is producing meaningful improvement.

At that point:
- The current `lab/mainline` represents a mature cognitive architecture
- The human is notified with the full metric history
- The lab has discovered, empirically and without any game knowledge, an action-optimal (or near-optimal) approach to all three games
- The real test begins: point the same architecture at a game it has never seen

### How the Comparative Analyst Uses These Metrics

The five metrics give the Comparative Analyst its differential signal:
- Metric 1 tells it WHERE agents are stuck (which level, which game)
- Metric 3 tells it HOW ROBUST the solution is (one lucky agent vs. population-wide capability)
- Metrics 4-5 tell it WHETHER improvement is real understanding or brute force (completing a level in 120 actions vs. 13 is a qualitative difference, even though both register as "completed")

The Analyst uses these to build its cohort comparisons: "Among agents that completed FT09 L2 in under 20 actions vs. those that took 80+ actions, what's different in their cognitive traces?"

---

## No Oracle — The Game Is the Only Teacher

There is no Oracle. No agent in the system knows the rules of any game. No agent has access to any human-provided knowledge about game mechanics. The only signal is what the game environment itself returns:

- **Level completion:** binary — did the agent finish the level or not?
- **Final score:** numeric — how well did the agent do?
- **Action count:** how many steps did the agent take?
- **Level progression:** did the agent advance to the next level, or stall on the same one?
- **Timer/lifespan:** did the agent run out of time?

This is the entire feedback surface. Everything the research lab does — every diagnosis, every hypothesis, every code change — must be derived from these signals plus observation of the agents' internal cognitive traces. Nothing else.

**Why no Oracle:** An Oracle — even one that only provides distance metrics — is supervised learning with extra steps. The research loop would be optimizing against a signal that encodes human knowledge of game mechanics. The code changes it produces would be *shaped by* that knowledge, even if no playing agent ever reads the rules directly. This produces a system that solves *these three games* well but can't generalize. The mission is explicit: "We will know we succeeded, when the agents can reason without needing sequences through all puzzles and even quickly understand new games they've never encountered with no training data, just their past understanding and logic built through experience."

An Oracle-dependent lab couldn't operate on a new game without a human first playing it, writing up the rules, and feeding them in. That's not autonomous. The lab must work with *only* what the game gives back.

---

## The Agents

### Agent 1: The Comparative Analyst (replaces Oracle + Gap Analyst)

**Purpose:** The core intelligence of the lab. Since there is no Oracle providing "correct" answers, this agent discovers what works by comparing agents that succeed against agents that fail. It is a pattern miner, not a correctness checker.

**Method — Differential Analysis:**
- After each evolution run, divide agents into cohorts: top performers, middle performers, bottom performers (per game, per level)
- For each cohort, pull the full cognitive traces (from the Code Tracer)
- Ask: **What is systematically different about agents that complete levels vs. agents that don't?**

**What it looks for:**
- **Causal map density:** Do successful agents have richer causal maps? Do they map more of the game world?
- **Subsystem engagement:** Which cognitive subsystems actually fire in successful runs vs. which are silent? If the symbolic reasoning engine never fires in ANY agent's run, that's a dead subsystem regardless of whether anyone scored well.
- **Decision patterns:** Do successful agents explore more early and exploit later? Do they repeat actions less? Do they use episodic memory more?
- **Action diversity:** Are successful agents using more of the action space, or are they focused on fewer actions?
- **Frame attention:** Are successful agents responding to frame changes that unsuccessful agents ignore?
- **Rung selection:** Which rungs correlate with successful outcomes? Which rungs correlate with stalling?

**Produces:**
- Per-game, per-level comparative reports: "Agents that completed FT09 Level 2 had 3x denser causal maps, used episodic memory on 40% of steps vs. 2%, and never selected Rung 4 (random exploration) after step 10. Agents that failed had sparse causal maps and fell back to random exploration on 80% of steps."
- Subsystem health reports: "Symbolic reasoning fired in 0% of agents across all games — this subsystem is either dead code or incorrectly wired."
- Failure taxonomy: {perception failure, causal reasoning failure, memory failure, strategy selection failure, exploration/exploitation imbalance} — inferred from the differential, not from comparison to a known answer.
- Priority ranking: "The strongest correlate of failure across all games is sparse causal mapping. Agents that build denser causal maps succeed more. This is the highest-leverage subsystem to improve."

**Critical constraint:** This agent has NO knowledge of game rules. It doesn't know that FT09 tiles don't affect neighbors, or that VC33 is fluid dynamics. It only knows: "agents with trait X succeed more than agents without trait X." The *interpretation* of why trait X helps is a hypothesis, not a fact.

---

### Agent 2: The Code Tracer

**Purpose:** Given any decision an agent made during gameplay, trace backwards through the cognitive architecture to explain exactly *why* that decision was made — which code paths fired, which subsystems contributed, and where the reasoning chain broke down.

**Reads:**
- Decision logs (which rung was selected, what candidates were generated)
- Causal maps (what cause-effect relationships the agent believed existed)
- Symbolic reasoning engine outputs (what patterns were matched or missed)
- Frame data and world model states
- Episodic memory retrievals (what past experiences influenced the decision)

**Produces:**
- Per-decision trace reports: "Step 14: Agent clicked (2,3) because Rung 4 (exploration) was selected. The causal map had no entries for cells (0,0)-(1,2), so the entire top-left quadrant was invisible to the agent. Symbolic reasoning returned no pattern match. Fallback: uniform random over all cells."
- Subsystem health reports: "Causal mapping populated 12% of expected entries. Symbolic reasoning fired on 3 of 45 steps. Episodic memory was never queried."

**Collaborates with:** The Code Reviewer (Agent 6) to cross-reference traces against code structure — if a subsystem never fires, is it dead code? Is it an integration gap? Is the calling code not wired up correctly?

---

### Agent 3: The Theorist

**Purpose:** Generates testable hypotheses about code changes that would address the Comparative Analyst's findings. Runs after evolution ends and analysis is complete.

**Inputs:** Comparative Analyst's differential reports and subsystem health data

**Reasoning approach (without game knowledge):**
The Theorist doesn't know WHY denser causal maps lead to success. It only knows THAT they do. So its hypotheses target the cognitive machinery, not game-specific strategies:
- "If denser causal maps correlate with success, what prevents causal maps from being denser? Is the frame differencing threshold too high? Is the causal map update being called? Is it discarding entries too aggressively?"
- "If episodic memory usage correlates with success but only 5% of agents use it heavily, is there a bug in the memory retrieval path? Or is the rung that triggers memory retrieval rarely selected?"
- "If symbolic reasoning never fires for any agent, is it a code integration issue (never called), a threshold issue (called but never matches), or a data issue (called with wrong inputs)?"

**Produces ranked hypotheses, each containing:**
- **Finding reference:** which differential observation it targets
- **Proposed intervention:** specific code change described at the conceptual level
- **Predicted effect:** "This should increase causal map density across all agents, which based on the differential should improve level completion rates"
- **Risk assessment:** what might regress, which other subsystems could be affected
- **Test criteria:** what metrics to watch to confirm or refute

**Does NOT produce:** actual code. That's the Code Modifier's job.

---

### Agent 4: The Code Modifier (Experimenter)

**Purpose:** Takes a hypothesis from the Theorist and implements it as a code change on an experiment branch.

**Branch management:**
- Creates branches like `experiment/causal-map-density-v1` off the current best mainline test branch (or production if no mainline exists yet)
- Full autonomy over its branches: create, commit, modify, delete
- Never touches `Ouroboros-v*`
- Can run evolution trials on its branch: small trials (10 agents x target game x 5 gens) for quick signal, larger trials for promising changes

**Produces:**
- A branch with the code change implemented
- Evolution trial results
- Before/after metrics compared to the branch point

---

### Agent 5: The Branch Breeder

**Purpose:** Combines successful experiment branches to test whether improvements are additive, synergistic, or conflicting.

**Logic:**
- Branch A improved FT09 by 5%. Branch B improved FT09 by 10%.
- Create `crossbred/A+B-v1` that merges both changes
- Run evolution trial on the combined branch
- Possible outcomes:
  - **Additive:** ~15% improvement (changes are independent)
  - **Synergistic:** >15% improvement (changes amplify each other)
  - **Conflicting:** <15% or regression (changes interfere)
  - **Dominant:** ~10% (Branch B's change makes Branch A's redundant)

**Also handles:**
- Three-way and N-way combinations of successful branches
- Conflict resolution when merges aren't clean (flags for Code Reviewer)
- Cross-game combinations: "Branch A helped FT09 but Branch C helped VC33 — combine to test if both improvements hold"

---

### Agent 6: The Code Reviewer

**Purpose:** The counterbalance to the Code Modifier. Every code change — whether from the Modifier or the Branch Breeder — passes through the Reviewer before evolution trials run. Catches structural damage that metrics alone won't reveal until much later.

**Checks for:**
- **Code orphans:** functions/classes that are no longer called after the change
- **Integration gaps:** new code that should connect to existing subsystems but doesn't
- **Integration errors:** incorrect wiring (e.g., passing wrong types, missing parameters, the dict-vs-object pattern)
- **Dead code:** leverages vulture + its own analysis to find unreachable paths
- **Feature duplication:** new code that reimplements something that already exists elsewhere
- **Obsolescence:** changes that supersede or make other parts of the codebase redundant (flags these for cleanup rather than letting dead weight accumulate)
- **Dependency violations:** imports that cross architectural boundaries that shouldn't be crossed
- **The cascading bugs pattern:** checks that changes in one subsystem don't silently break assumptions in downstream subsystems (the pattern that produced the 60 numpy errors, the monopoly bugs, the game_state dict-vs-object issues)

**Tools:** vulture, AST analysis, import graph analysis, the existing pre-commit hooks, plus its own structural analysis

**Collaborates with:**
- **Code Tracer:** if a subsystem never fires in traces, Reviewer checks if it's dead code or an integration gap
- **Code Modifier:** Review happens BEFORE evolution trials. If the Reviewer finds issues, the Modifier fixes them before any compute is spent on trials

---

### Agent 7: The Trend Tracker

**Purpose:** Maintains perfect memory across all experiments. Answers the question: "What kinds of changes work for what kinds of problems?"

**Tracks:**
- Every experiment branch, its hypothesis, its results, and whether it was confirmed or refuted
- Per-game improvement trajectories across all branches
- Which subsystem changes have the highest hit rate
- Which combinations (from Branch Breeder) were synergistic vs. conflicting
- Regression alerts: if a previously-working game starts declining

**Enforces:**
- Minimum trial length before new hypotheses can be proposed (prevents churn from noise in stochastic evolution)
- Statistical significance thresholds: "This 2% improvement is within noise bounds, need more generations" vs. "This 15% improvement is real signal"

**Produces:**
- Periodic state-of-the-lab reports
- Input to the Theorist: "Causal map improvements have worked 3/4 times across all games. Threshold tuning plateaus after 5 gens. Exploration bias changes have never helped."
- Cross-game pattern detection: "Changes that improve FT09 tend to also improve LS20 but have no effect on VC33 — these games may exercise different cognitive subsystems"

---

### The Mainline Test Branch

A living branch — call it `lab/mainline` — that accumulates the best proven changes:

1. Experiment branches prove individual improvements
2. Branch Breeder tests combinations
3. When a combination shows clear, statistically significant improvement with no regressions across all three games, it gets merged into `lab/mainline`
4. `lab/mainline` represents the current "best known configuration"
5. All new experiments branch off `lab/mainline` (not production) to build on accumulated gains
6. When `lab/mainline` reaches a milestone (e.g., "FT09: 78%, VC33: 68%, LS20: 85%"), the human is notified for potential merge to `Ouroboros-v*`

---

## The Loop

```
  ┌──────────────────────────────────────────────────────────────┐
  │                    GAME ENVIRONMENT                          │
  │   (the ONLY teacher — returns scores, level completions,     │
  │    action counts, timer status. nothing else.)               │
  └──────────────────────────┬───────────────────────────────────┘
                             │ raw gameplay results
                             ▼
┌─────────────┐   ┌───────────────────────────┐
│ CODE TRACER │──▶│   COMPARATIVE ANALYST     │
│ "why did    │   │ "agents that succeed have │
│  agent do   │   │  3x denser causal maps    │
│  this?"     │   │  and use episodic memory" │
└──────┬──────┘   └─────────────┬─────────────┘
       │                        │ differential findings
       │                        ▼
       │           ┌───────────────────────────┐
       │           │        THEORIST           │
       │           │ "Hypothesis: causal map   │
       │           │  update is being skipped  │
       │           │  due to threshold bug"    │
       │           └─────────────┬─────────────┘
       │                        │ hypothesis
       │                        ▼
       │           ┌───────────────────────┐   ┌──────────────────┐
       │           │    CODE MODIFIER      │◀─▶│  CODE REVIEWER   │
       │           │  implement on branch  │   │  check for       │
       │           │  run evolution trial  │   │  orphans, gaps,  │
       ├──────────▶│                       │   │  dead code, etc. │
       │           └───────────┬───────────┘   └──────────────────┘
       │                       │ trial results
       │                       ▼
       │           ┌───────────────────────┐
       │           │    TREND TRACKER      │
       │           │  "this worked, add    │
       │           │   to candidate pool"  │
       │           └───────────┬───────────┘
       │                       │ successful experiments
       │                       ▼
       │           ┌───────────────────────┐
       │           │    BRANCH BREEDER     │
       │           │  combine A+B, test    │
       │           │  if additive/synergy  │
       │           └───────────┬───────────┘
       │                       │ proven combinations
       │                       ▼
       │           ┌───────────────────────┐
       │           │    LAB/MAINLINE       │
       │           │  best accumulated     │
       │           │  changes              │
       │           │  "FT09:34% VC33:12%"  │
       │           └───────────┬───────────┘
       │                       │ milestone reached
       │                       ▼
       │           ┌───────────────────────┐
       │           │    HUMAN (you)        │
       │           │  review & merge to    │
       │           │  Ouroboros-v*          │
       │           └───────────────────────┘
       │
       │ (loop restarts: new evolution on
       │  lab/mainline, fresh gameplay data
       │  flows back to Comparative Analyst)
       └────────────────────────────────────
```

---

## Key Design Principles

1. **The game is the only teacher.** No agent in the system knows game rules. No agent has access to human knowledge about game mechanics. The only feedback is what the game environment returns: scores, level completions, action counts, timer status. Everything else is inferred.

2. **Comparative analysis, not correctness checking.** Without an Oracle, the lab can't say "this move was wrong." It can only say "agents that do X succeed more than agents that don't." This is weaker per-decision but stronger for generalization — it discovers what cognitive capabilities matter, not what game-specific moves to make.

3. **The Code Reviewer is the immune system.** Without it, the Code Modifier will accumulate technical debt, orphaned code, and integration rot faster than the metrics improve. The Reviewer ensures the codebase stays structurally sound even as it evolves rapidly.

4. **Branch breeding is combinatorial search done right.** Individual improvements might conflict, cancel out, or amplify each other. You can't know without testing. The Breeder systematically explores the combination space.

5. **Production branches are sacred.** The autonomous lab can burn through dozens of experiment branches, create terrible code, revert everything, and try again. None of it matters because production is untouched until a human says otherwise.

6. **Behavioral invariants over unit tests.** The lab doesn't maintain a traditional test suite that breaks on every refactor. Instead, it maintains contracts at subsystem boundaries:
   - "An agent must produce a valid action for its game type on every step"
   - "After N steps of gameplay, cognitive subsystems must have produced non-empty output"
   - "No subsystem should silently return None and let execution continue"
   - These survive any refactor because they describe *what* the system must do, not *how*.

7. **Generalization is the success metric, not game-specific performance.** The lab succeeds when improvements to the cognitive architecture transfer across games. If a change helps FT09 but not VC33 or LS20, it's likely a game-specific hack. If a change helps all three, it's likely improving genuine reasoning capability. The Trend Tracker watches for this cross-game transfer as the ultimate signal of progress.

8. **This architecture itself must generalize.** Because no agent knows game rules, the entire lab can be pointed at a brand new game with zero changes. Swap out the game environment, run the loop, and the Comparative Analyst will start discovering what works. No Oracle to bootstrap, no rules to write up, no human in the loop. This is what makes it a true autonomous research lab, not just an elaborate testing harness for three known puzzles.

---

## Implementation Reality: 3 LLM Subagents + Python Scripts + Checklists

The 7 "agents" described above are conceptual roles, not 7 separate LLM instances. In practice, the lab is:

### One Main Orchestrator LLM
A single LLM that manages the research loop. It calls Python scripts for data gathering, invokes LLM subagents when judgment is needed, and follows checklist templates to stay on track. It is the loop itself.

### 3 LLM Subagents (the only parts that require LLM reasoning)

**1. The Theorist**
- Reads the Comparative Analyst's statistical output (produced by Python)
- Reads the relevant source code of the cognitive architecture
- Generates hypotheses about what code changes would improve the metrics
- Uses: `checklists/theorist.md`

**2. The Code Modifier**
- Takes a hypothesis from the Theorist
- Implements the code change on an experiment branch
- Uses: `checklists/code_modifier.md`

**3. The Code Reviewer**
- Runs after the Code Modifier, before evolution trials
- Invokes pylance, vulture, pre-commit hooks, AST checks, import graph analysis
- Walks through a structured checklist of what to look for
- Uses: `checklists/code_reviewer.md`

### Python Scripts (everything else — all codebase-agnostic)

These scripts NEVER hardcode subsystem names, table schemas, rung numbers, file paths, or any other implementation detail of the cognitive architecture. The codebase is constantly being modified by the Code Modifier, so the scripts must discover what exists at runtime.

#### The Two Stable Contracts

Only two things are stable across all codebase changes:

1. **The game environment output** — `game_results` table always has: `game_id`, `agent_id`, `generation`, `level_completions`, `final_score`, `action_count` (or equivalent). The game doesn't change, so its output format doesn't change. The 5 benchmark metrics are computed entirely from this.

2. **The trace output contract** — Every cognitive subsystem that runs during gameplay MUST write structured trace data to a standard location using a standard format. This is the one architectural rule the Code Modifier must preserve:

```
traces/{generation}/{agent_id}/{step_N}.json
```

Each trace file contains whatever the subsystem produced at that step — but it MUST include:
```json
{
  "step": 14,
  "subsystem": "<name>",      // whatever the subsystem calls itself
  "produced_output": true,     // did it actually produce something?
  "action_selected": "ACTION6_2_3",  // what action was chosen
  "decision_path": [...]       // ordered list of subsystems that contributed
}
```

The scripts don't need to know WHAT subsystems exist. They discover them from whatever shows up in the trace files.

#### Discovery-Based Scripts

| Script | What it discovers at runtime | What it computes |
|--------|------------------------------|------------------|
| `lab/metrics.py` | Queries `game_results` schema dynamically (column names via DB introspection) | All 5 benchmark metrics. Stable — the game output doesn't change. |
| `lab/code_tracer.py` | Scans `traces/` directory, discovers all unique `subsystem` names that appear, discovers all `decision_path` patterns | Per-agent reports: which subsystems fired, which were silent, what % of steps each subsystem produced output. Discovers new subsystems automatically if the Code Modifier adds one. |
| `lab/comparative_analyst.py` | Takes Code Tracer output + metrics. Discovers all available features (every subsystem's engagement rate, every trace field that varies between agents) | For every discovered feature: compute statistical difference between success cohort and failure cohort. Rank all features by effect size. No hardcoded feature list — if a new subsystem appears, it gets measured automatically. |
| `lab/trend_tracker.py` | Reads its own ledger (experiment results DB). Schema is lab-internal and stable. | Statistical significance, convergence detection, plateau detection, cross-game patterns. Codebase-agnostic by nature — it tracks experiment outcomes, not code structure. |
| `lab/branch_breeder.py` | Reads Trend Tracker's successful experiment list. Uses git for all branch operations. | Merge combinations, run trials, classify results. Entirely codebase-agnostic — it doesn't read code, just manages branches. |
| `lab/evolution_runner.py` | Discovers how to run evolution from a standard entrypoint (e.g., `python run_evolution.py --agents N --games G --generations K`) | Runs trials, waits for completion, returns metrics. The entrypoint contract is stable even if internals change. |

#### How Discovery Works in Practice

**The Code Tracer doesn't know what subsystems exist.** It scans:
```python
# Discover all subsystems that produced traces this generation
subsystems = set()
for trace_file in glob("traces/{gen}/{agent}/*.json"):
    data = json.load(trace_file)
    subsystems.add(data["subsystem"])

# For each discovered subsystem, compute engagement rate
for subsystem in subsystems:
    engagement = count(fired) / count(total_steps)
```

If the Code Modifier adds a new subsystem called `"spatial_reasoning_v2"`, the Code Tracer will find it next run without any code change. If it renames `"symbolic_reasoning"` to `"pattern_matcher"`, the Tracer doesn't care — it just reports what it finds.

**The Comparative Analyst doesn't know what features matter.** It measures everything:
```python
# For every feature the Code Tracer discovered, compare cohorts
for feature in tracer_output.all_features():
    success_vals = [agent[feature] for agent in success_cohort]
    failure_vals = [agent[feature] for agent in failure_cohort]
    effect_size = compute_effect_size(success_vals, failure_vals)
    report.add(feature, effect_size)

# Rank by effect size — the biggest gaps surface automatically
report.sort_by_effect_size()
```

If a new subsystem appears and it turns out that agents using it succeed 5x more, it'll show up as the top-ranked feature — without anyone telling the Analyst to look for it.

### Checklist Templates (with Copilot Instructions Assimilated)

Each role — LLM or Python — has a markdown checklist that absorbs the relevant sections from `copilot-instructions.md`. The orchestrator loads the relevant checklist at each stage. No agent needs to read the full copilot-instructions — only its own checklist.

#### Cross-Cutting Rules (ALL agents must follow)

These rules from copilot-instructions apply universally:
```
- PYTHONDONTWRITEBYTECODE=1 in all environments (Rule 1)
- ALL data in SQLite core_data.db — NEVER create .log files (Rule 2)
- NEVER use Unicode emoji characters — use ASCII: [OK], [FAIL], etc. (Rule 11)
- The database is the organism. Agents are temporary. Knowledge must survive agent death (Reminder 9)
- The system naturally drifts toward death (Seven Seals). Active anti-entropic maintenance required (Reminder 10)
- Every problem is an alignment problem — the agent discovers the game's interface contract (Reminder 8)
```

---

**`checklists/orchestrator.md`** (the main loop controller)
```
# Orchestrator — manages the research loop
# Absorbs: copilot-instructions Rules 4, Part 10, Part 11

## Environment
- [ ] Verify .venv is active before any Python execution
- [ ] PYTHONDONTWRITEBYTECODE=1 set
- [ ] Long-running processes (evolution trials) in dedicated terminals — NEVER send commands to a terminal with an active background process

## Loop Management
- [ ] Call Python scripts for data gathering (metrics, traces, analysis, trends)
- [ ] Invoke LLM subagents only when judgment is needed (Theorist, Modifier, Reviewer)
- [ ] Gate new experiments on Trend Tracker's statistical readiness signal
- [ ] Track the 5 benchmark metrics across all iterations
- [ ] Detect stabilization (all 5 metrics converged)
- [ ] Notify human at milestones (first full game completion, mainline merge candidates)

## The Matryoshka Principle (copilot-instructions Part 11)
- The orchestrator IS the outer scaffolding. Goal: make the inner system stand on its own.
- Phase transitions are benchmark milestones, not arbitrary thresholds:
  - A→B: First successful experiment merged to lab/mainline (loop proven)
  - B→C: Metric 2 achieved for ALL games (full game completion — discovery phase over)
  - C→D: Metric 3 robust — majority of agents consistently complete all games (not fragile)
  - D→E: Stabilization — all 5 metrics converged (<0.1% improvement/gen over 100 gens)
```

---

**`checklists/comparative_analyst.md`** (Python script)
```
# Comparative Analyst — discovers what differentiates success from failure
# Absorbs: copilot-instructions Part 4 (run log analysis), Part 10.3 (success metrics)

## Data Gathering
- [ ] Query game_results for latest generation(s)
- [ ] Split agents into top/mid/bottom cohorts per game per level

## Feature Discovery (codebase-agnostic — discover, don't hardcode)
- [ ] Discover all features from Code Tracer output (subsystem engagement rates, decision path patterns, action diversity, any numeric/categorical field)
- [ ] For each discovered feature, compute effect size between success and failure cohorts
- [ ] Rank all features by effect size
- [ ] Flag features with zero variance (subsystems that never fire or always fire)
- [ ] Flag NEW features not seen in previous runs (new subsystems added by Code Modifier)

## Per-Agent Behavioral Analysis (from copilot-instructions Part 4.3)
- [ ] Action diversity: count unique (action_type, x, y) triples per agent
- [ ] Rung diversity: count unique rung names per agent (1 rung = monopoly)
- [ ] Confidence trajectory: is confidence varying or constant? (constant = not learning)
- [ ] Frame change rate: what % of actions actually changed the frame? (<5% = clicking dead positions)

## Cross-Agent Patterns (from copilot-instructions Part 4.4)
- [ ] How many unique game types played across population?
- [ ] Best score per game type
- [ ] Any agent significantly outperforming? (breeding candidate)
- [ ] Any level progressions? (primary success signal)

## Output
- [ ] Structured report as JSON (feature rankings + raw statistics + behavioral analysis)
```

---

**`checklists/code_tracer.md`** (Python script)
```
# Code Tracer — traces decisions back through the cognitive architecture
# Absorbs: copilot-instructions Part 3.1 (silent integration failures), Part 3.3 (dead feedback loops),
#           Part 3.5 (coordinate fixation), Part 3.6 (pipeline health check)

## Trace Discovery (codebase-agnostic)
- [ ] Scan traces/ directory for current generation
- [ ] Discover all unique subsystem names from trace files
- [ ] For each agent: compute per-subsystem engagement rate (% of steps with produced_output=true)
- [ ] For each agent: extract decision_path sequences and compute pattern frequencies

## Known Failure Pattern Detection (from copilot-instructions Part 3)
- [ ] Silent Integration Failure (3.1): find subsystems with code but zero trace output
      — tables with readers but zero writers, tables with writers but zero readers
- [ ] Dead Feedback Loop (3.3): verify notify_action_complete called N times per game (N = action count)
      — check that action coordinates in feedback are actual coords, not defaults like (0,0)
- [ ] Coordinate Fixation (3.5): count unique (x,y) positions per click game
      — same position across all actions = fixated. Center coords (36,36)/(32,32) = fallback defaults
- [ ] Rung Monopoly (3.2): same rung on every action = monopoly. Confidence that never decays = not learning

## Pipeline Health (from copilot-instructions Part 3.6)
- [ ] Check critical tables have recent writes (not just historical data)
- [ ] Check rung diversity per game session (should be 3-5 different rungs)
- [ ] Check coordinate diversity for click games (>=5 unique positions)
- [ ] Check context completeness (any key returning None that shouldn't be?)

## Output
- [ ] Structured trace reports as JSON (all discovered features, failure pattern flags, no hardcoded list)
```

---

**`checklists/theorist.md`** (LLM subagent)
```
# Theorist — reads data + code, generates hypotheses about what to change
# Absorbs: copilot-instructions Part 1 (theoretical foundation), Part 2 (architecture discovery),
#           Part 5 (visual diagnosis), Part 6 (PTMA architecture), Part 7 (implementation priorities)

## Theoretical Grounding (from copilot-instructions Part 1)
- You must understand the theory to debug the implementation. Bugs are theory violations.
- Core thesis: every problem is an alignment problem. The agent discovers the game's interface contract.
- The Seven Seals of Intellectual Death: Monolith, Amnesia, Hierarchy, Monopoly, Hoarding, Isolation, Stasis
  — every failure maps to one of these. Check which seal the current failure mode violates.
- Intelligence emerges from compression under constraints. Database compresses via forgetting.
  Agent compresses high-dimensional input. Network compresses individual solutions.

## Architecture Understanding (from copilot-instructions Part 2 + 6)
- PTMA Loop: Perceive -> Think -> Map -> Act. The loop IS the intelligence.
- Three-speed decision making: MAPPED (fast, plan exists) -> REASONED (medium) -> EXPLORATORY (slow)
- Dual economy: ATP (action budget) + Prestige (trustworthiness), NEVER mixed. PrestigeFirewall is SACRED.
- Use grep/glob to discover current wiring — don't assume documentation is current

## Priority Ordering (from copilot-instructions Part 7)
When generating hypotheses, fix in this order:
1. Broken feedback loops (blocks all learning)
2. Rung monopoly (blocks cognitive diversity)
3. Coordinate fixation (blocks game-specific learning)
4. Missing context data (blocks informed decisions)
5. Dead pipelines (blocks persistence)
6. Missing compression (blocks abstraction)
7. Missing resonance (blocks generalization)

## Hypothesis Generation Process
- [ ] Read the Comparative Analyst's latest report (feature rankings by effect size)
- [ ] Read the Code Tracer's subsystem health report (engagement rates, dead subsystems, failure pattern flags)
- [ ] Identify the top 1-3 features with largest effect size gap between success/failure cohorts
- [ ] For each top feature, search the codebase for the relevant subsystem source code
      (use subsystem name from trace data to grep/glob — not hardcoded paths)
- [ ] Map the finding to one of the Seven Seals — what death mode is active?
- [ ] Generate 1-3 ranked hypotheses, each with:
      - [ ] Which feature/finding it targets
      - [ ] Which Seal it addresses
      - [ ] Proposed conceptual change (not code — describe the intervention)
      - [ ] Predicted effect on the 5 benchmark metrics
      - [ ] Risk assessment (what might regress)
      - [ ] Test criteria (what to measure to confirm/refute)
- [ ] Check Trend Tracker history: has a similar hypothesis been tried before? What happened?
- [ ] Output hypotheses as structured markdown
```

---

**`checklists/code_modifier.md`** (LLM subagent)
```
# Code Modifier — implements hypotheses as code changes on experiment branches
# Absorbs: copilot-instructions Rules 3,5,9,10,11,15,16, Part 2 (architecture discovery),
#           Part 6 (PTMA architecture)

## Immutable Rules
- NEVER create .log files — all data to SQLite (Rule 2)
- NEVER use Unicode emojis — use ASCII: [OK], [FAIL], etc. (Rule 11)
- NEVER create test files outside tests/ (Rule 5, exception Rule 15)
- NEVER mock/simulate games — real API only (Rule 6)
- NEVER touch Ouroboros-v* branches

## Code Change Rules
- No orphaned code: delete/integrate ALL old code when refactoring (Rule 3)
- Prevent code drift: enhance existing files >> new standalone files (Rule 10)
- Update all references when moving/renaming code (Rule 3)
- No duplicate functionality (Rule 10)

## Architecture Rules (from copilot-instructions Part 6)
- Preserve PTMA loop: Perceive -> Think -> Map -> Act
- Preserve dual economy: ATP + Prestige NEVER mixed. PrestigeFirewall is SACRED.
- Preserve three-layer agents: Genome (fixed) + Epigenetic (slow) + Somatic (fast)
- Preserve event bus pub/sub pattern
- Preserve database-as-organism: knowledge survives agent death

## Process
- [ ] Read the Theorist's top hypothesis
- [ ] Create experiment branch off lab/mainline (or production if no mainline)
- [ ] Use architecture discovery techniques (grep/glob) to find current wiring before modifying
- [ ] Implement the code change
- [ ] CRITICAL: any new or modified subsystem MUST write traces in the standard format
      (traces/{gen}/{agent}/{step}.json with subsystem, produced_output, action_selected, decision_path)
- [ ] Run pre-commit hooks — fix failures (vulture, isort, trailing-whitespace, AST check, end-of-file)
- [ ] If pre-commit fails: fix genuine errors, re-stage auto-fixed files, recommit until clean (Rule 16)
- [ ] Hand off to Code Reviewer BEFORE running any evolution trials
- [ ] After review passes, run evolution trial (small: 10 agents x target game x 5 gens)
- [ ] Collect before/after metrics
- [ ] Record results for Trend Tracker
```

---

**`checklists/code_reviewer.md`** (LLM subagent)
```
# Code Reviewer — the immune system. Counterbalance to the Code Modifier.
# Absorbs: copilot-instructions Rules 3,13,14,16, Part 3 (debugging methodology),
#           Part 8 (testing protocols), Appendix B (file change checklist)

## Automated Tool Checks
- [ ] Run vulture (min-confidence=80, --ignore-names=_*) — flag new dead code
- [ ] Run pylance — type errors, missing imports, unresolved references
- [ ] Run pre-commit hooks (isort, trailing whitespace, AST check, end-of-file)
- [ ] Run dependency analysis: python manual_tools/analysis/analyze_dependencies.py --stats --orphans
      — zero circular imports, no new orphaned modules (Rule 13)

## Trace Contract Verification
- [ ] CRITICAL: verify any new/modified subsystem writes traces in the standard format
      (this is the one contract that must be preserved for the lab scripts to work)

## Structural Integrity (from copilot-instructions Rule 3 + Part 3)
- [ ] Code orphans: functions/classes no longer called after the change
- [ ] Integration gaps: new code that should connect to existing subsystems but doesn't (Part 3.1)
- [ ] Integration errors: wrong types, missing parameters, dict-vs-object pattern (Part 3.4)
- [ ] Feature duplication: does this reimplement something that already exists? (Rule 10)
- [ ] Obsolescence: does this change make other code redundant? Flag for cleanup
- [ ] Dependency violations: imports crossing architectural boundaries (Rule 13)
- [ ] Cascading assumption breaks: does this change affect downstream expectations? (Part 3.4)

## Behavioral Regression (from copilot-instructions Part 8 + Appendix B)
- [ ] One generation runs without crashes
- [ ] Pipeline assertions produce 0 CRITICAL findings
- [ ] No new rung monopoly introduced (check action log diversity)
- [ ] No context field newly returning None
- [ ] notify_action_complete still fires for every action (Part 3.3)
- [ ] Game results still written to database after each game
- [ ] At least 3 game types assigned across population
- [ ] For click games: >=5 unique positions per game session
- [ ] For movement games: all 4 directional actions represented

## Theory Validation (from copilot-instructions Part 8.4)
- [ ] PrestigeFirewall never raises (dual economy separation)
- [ ] DB size growth rate should slow (evolutionary forgetting)
- [ ] Event bus fired at least 1 event

## Cross-Reference
- [ ] If Code Tracer flagged a subsystem as never-firing, did this change fix it?
- [ ] PASS or FAIL with specific findings — if FAIL, hand back to Code Modifier with fix list
```

---

**`checklists/trend_tracker.md`** (Python script)
```
# Trend Tracker — perfect memory across all experiments
# Absorbs: copilot-instructions Part 10.3 (success metrics), Part 10.4 (when to stop),
#           Appendix C (alignment velocity)

## Record Keeping
- [ ] Record experiment: branch name, hypothesis, metrics before/after, confirmed/refuted
- [ ] Update per-game improvement trajectories
- [ ] Compute alignment velocity: levels_completed / actions_taken (Appendix C)

## Statistical Analysis
- [ ] Check statistical significance of latest result
- [ ] Check if minimum trial length met before allowing new hypotheses
- [ ] Detect cross-game patterns (does this change help multiple games?)
- [ ] Check for regressions on non-target games

## Convergence Detection
- [ ] Track all 5 benchmark metrics over time
- [ ] Detect plateaus (diminishing returns)
- [ ] Flag stabilization when all metrics converge simultaneously

## When to Reassess (from copilot-instructions Part 10.4)
- [ ] If 5 consecutive experiments don't improve any metric -> flag for Theorist to rethink approach
- [ ] If a metric improves but another regresses -> flag coupling issue
- [ ] If one game improves but others don't -> flag game-specific hack (not general improvement)

## Output
- [ ] Update state-of-lab report with all the above
```

---

**`checklists/branch_breeder.md`** (Python script + LLM for conflict resolution)
```
# Branch Breeder — combinatorial search across successful experiments
# Absorbs: copilot-instructions Part 9 (branch management, cherry-picking)

## Branch Operations (from copilot-instructions Part 9)
- [ ] Before merging, understand WHY branches differ (intentional design vs. merge accident)
- [ ] Check if borrowed code depends on other changes in the source branch
- [ ] Document what was combined and why in commit message

## Process
- [ ] Identify successful experiment branches from Trend Tracker
- [ ] Generate combination candidates (all pairs, then triples if pairs succeed)
- [ ] For each combination:
      - [ ] Attempt git merge into new crossbred/ branch
      - [ ] If merge conflict: flag for Code Reviewer LLM to resolve
      - [ ] Run Code Reviewer checklist on combined code
      - [ ] Run evolution trial on combined branch
      - [ ] Classify result: additive / synergistic / conflicting / dominant
- [ ] Promote best combination to lab/mainline candidate
```

---

**`checklists/evolution_runner.md`** (Python script)
```
# Evolution Runner — runs trials on branches
# Absorbs: copilot-instructions Rules 6,7,12, Appendix A

## Immutable Rules
- NEVER mock/simulate ARC games — always use real API (Rule 6)
- Verify real actions sent to ARC games — monitor API calls (Rule 7)
- Run SafeDatabaseCleaner every 10 generations (Rule 12)
- PYTHONDONTWRITEBYTECODE=1 always (Rule 1)

## Process
- [ ] Activate .venv before execution
- [ ] Run evolution: python evolution_runner.py --mode offline --max-generations=K
- [ ] Monitor via get_terminal_output (NEVER send commands to active terminal)
- [ ] After completion: collect all 5 benchmark metrics
- [ ] Verify game_results table has new rows
- [ ] Return structured results to orchestrator
```

### The Orchestrator Loop (pseudocode)

```python
while not stabilization_reached():
    # === PYTHON: Gather data ===
    run_evolution(branch="lab/mainline")
    metrics = compute_metrics()          # lab/metrics.py
    traces = run_code_tracer()           # lab/code_tracer.py
    analysis = run_comparative_analyst() # lab/comparative_analyst.py
    trend = update_trend_tracker()       # lab/trend_tracker.py

    # === CHECK: Is there enough signal for a new experiment? ===
    if not trend.ready_for_new_hypothesis():
        continue  # need more generations of data

    # === LLM: Generate hypothesis ===
    hypothesis = invoke_theorist(analysis, traces, trend)

    # === LLM: Implement change ===
    branch = invoke_code_modifier(hypothesis)

    # === LLM: Review change ===
    review = invoke_code_reviewer(branch)
    if review.failed:
        invoke_code_modifier_fix(branch, review.findings)
        review = invoke_code_reviewer(branch)  # re-review
        if review.failed:
            abandon_branch(branch)
            continue

    # === PYTHON: Run trial ===
    trial_results = run_evolution(branch=branch)
    record_experiment(hypothesis, trial_results)

    # === PYTHON: Breed successful branches ===
    if has_successful_experiments():
        combinations = breed_branches()
        for combo in combinations:
            trial = run_evolution(branch=combo.branch)
            record_combination(combo, trial)

    # === PYTHON: Promote to mainline ===
    if best_combination_beats_mainline():
        merge_to_mainline(best_combination)
        notify_if_milestone()
```
