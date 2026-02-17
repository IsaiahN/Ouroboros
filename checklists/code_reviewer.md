# Code Reviewer -- the immune system. Counterbalance to the Code Modifier.
# Absorbs: copilot-instructions Rules 3,13,14,16, Part 3 (debugging methodology),
#           Part 8 (testing protocols), Appendix B (file change checklist)

## Automated Tool Checks
- [ ] Run vulture (min-confidence=80, --ignore-names=_*) -- flag new dead code
- [ ] Run pylance -- type errors, missing imports, unresolved references
- [ ] Run pre-commit hooks (isort, trailing whitespace, AST check, end-of-file)
- [ ] Run dependency analysis: python manual_tools/analysis/analyze_dependencies.py --stats --orphans
      -- zero circular imports, no new orphaned modules (Rule 13)

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
- [ ] PASS or FAIL with specific findings -- if FAIL, hand back to Code Modifier with fix list
