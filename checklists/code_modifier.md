# Code Modifier -- implements hypotheses as code changes on experiment branches
# Absorbs: copilot-instructions Rules 3,5,9,10,11,15,16, Part 2 (architecture discovery),
#           Part 6 (PTMA architecture)
#           + change-propagation scope declarations, Stream B maintenance, relationship graph updates

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
- [ ] **Consult the relationship graph** before modifying:
      ```sql
      -- What edges touch the module(s) I am about to change?
      SELECT * FROM relationship_graph
      WHERE source_module = '<module>' OR target_module = '<module>';
      -- What does the module's contract promise?
      SELECT * FROM module_contracts WHERE module_name = '<module>';
      ```
- [ ] Implement the code change
- [ ] CRITICAL: any new or modified subsystem MUST write traces in the standard format
      (traces/{gen}/{agent}/{step}.json with subsystem, produced_output, action_selected, decision_path)
- [ ] **Declare change-propagation scope**: "I changed module X, which affects edges Y,
      which touch modules A, B, C." This declaration goes in the commit message or PR description.
      The Code Reviewer verifies completeness by querying the graph.
- [ ] **Update relationship graph** for any modified data flows:
      ```sql
      -- Update or insert edges
      INSERT OR REPLACE INTO relationship_graph
      (source_module, target_module, edge_type, contract, status)
      VALUES ('<source>', '<target>', '<type>', '<what flows>', 'live');
      -- Update module contract if Stream B changed
      UPDATE module_contracts SET stream_b_produces = '...', updated_at = datetime('now')
      WHERE module_name = '<module>';
      ```
- [ ] **New modules MUST have a Stream B declaration** -- insert into `module_contracts`
      with role, stream_a, stream_b_produces, stream_b_consumes, stream_b_side_effects,
      stream_b_promises. An unregistered module is an orphan by definition.
- [ ] Run pre-commit hooks -- fix failures (vulture, isort, trailing-whitespace, AST check, end-of-file)
- [ ] If pre-commit fails: fix genuine errors, re-stage auto-fixed files, recommit until clean (Rule 16)
- [ ] Hand off to Code Reviewer BEFORE running any evolution trials
- [ ] After review passes, run evolution trial (small: 10 agents x target game x 5 gens)
- [ ] Collect before/after metrics
- [ ] Record results for Trend Tracker
