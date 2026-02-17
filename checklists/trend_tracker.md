# Trend Tracker -- perfect memory across all experiments
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
