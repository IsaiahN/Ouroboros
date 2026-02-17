# Orchestrator -- manages the research loop
# Absorbs: copilot-instructions Rules 4, Part 10, Part 11

## Environment
- [ ] Verify .venv is active before any Python execution
- [ ] PYTHONDONTWRITEBYTECODE=1 set
- [ ] Long-running processes (evolution trials) in dedicated terminals -- NEVER send commands to a terminal with an active background process

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
  - A->B: First successful experiment merged to lab/mainline (loop proven)
  - B->C: Metric 2 achieved for ALL games (full game completion -- discovery phase over)
  - C->D: Metric 3 robust -- majority of agents consistently complete all games (not fragile)
  - D->E: Stabilization -- all 5 metrics converged (<0.1% improvement/gen over 100 gens)
