# Code Tracer -- traces decisions back through the cognitive architecture
# Absorbs: copilot-instructions Part 3.1 (silent integration failures), Part 3.3 (dead feedback loops),
#           Part 3.5 (coordinate fixation), Part 3.6 (pipeline health check)

## Trace Discovery (codebase-agnostic)
- [ ] Scan traces/ directory for current generation
- [ ] Discover all unique subsystem names from trace files
- [ ] For each agent: compute per-subsystem engagement rate (% of steps with produced_output=true)
- [ ] For each agent: extract decision_path sequences and compute pattern frequencies

## Known Failure Pattern Detection (from copilot-instructions Part 3)
- [ ] Silent Integration Failure (3.1): find subsystems with code but zero trace output
      -- tables with readers but zero writers, tables with writers but zero readers
- [ ] Dead Feedback Loop (3.3): verify notify_action_complete called N times per game (N = action count)
      -- check that action coordinates in feedback are actual coords, not defaults like (0,0)
- [ ] Coordinate Fixation (3.5): count unique (x,y) positions per click game
      -- same position across all actions = fixated. Center coords (36,36)/(32,32) = fallback defaults
- [ ] Rung Monopoly (3.2): same rung on every action = monopoly. Confidence that never decays = not learning

## Pipeline Health (from copilot-instructions Part 3.6)
- [ ] Check critical tables have recent writes (not just historical data)
- [ ] Check rung diversity per game session (should be 3-5 different rungs)
- [ ] Check coordinate diversity for click games (>=5 unique positions)
- [ ] Check context completeness (any key returning None that shouldn't be?)

## Output
- [ ] Structured trace reports as JSON (all discovered features, failure pattern flags, no hardcoded list)
