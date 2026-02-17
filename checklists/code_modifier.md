# Code Modifier -- implements hypotheses as code changes on experiment branches
# Absorbs: copilot-instructions Rules 3,5,9,10,11,15,16, Part 2 (architecture discovery),
#           Part 6 (PTMA architecture)

## Immutable Rules
- NEVER create .log files -- all data to SQLite (Rule 2)
- NEVER use Unicode emojis -- use ASCII: [OK], [FAIL], etc. (Rule 11)
- NEVER create test files outside tests/ (Rule 5, exception Rule 15)
- NEVER mock/simulate games -- real API only (Rule 6)
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
- [ ] Run pre-commit hooks -- fix failures (vulture, isort, trailing-whitespace, AST check, end-of-file)
- [ ] If pre-commit fails: fix genuine errors, re-stage auto-fixed files, recommit until clean (Rule 16)
- [ ] Hand off to Code Reviewer BEFORE running any evolution trials
- [ ] After review passes, run evolution trial (small: 10 agents x target game x 5 gens)
- [ ] Collect before/after metrics
- [ ] Record results for Trend Tracker
