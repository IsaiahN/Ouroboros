# Comparative Analyst -- discovers what differentiates success from failure
# Absorbs: copilot-instructions Part 4 (run log analysis), Part 10.3 (success metrics)

## Data Gathering
- [ ] Query game_results for latest generation(s)
- [ ] Split agents into top/mid/bottom cohorts per game per level

## Feature Discovery (codebase-agnostic -- discover, don't hardcode)
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
