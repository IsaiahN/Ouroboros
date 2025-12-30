# Sequenced Refactor Plan

Phased execution to reach the event-first, guard-heavy runtime with provenance. Behavior parity first, then extraction. Testing and pycache hygiene are first-class: use python -B or PYTHONDONTWRITEBYTECODE=1 at all entry points, and run regression suites per phase.

## Phase 0: Migrations & Plumbing
- Apply additive migrations for attempts, hook_failures, action_proposals_log, lesson_interpretations, source_attempt_id/source_mode tags.
- Add CHECK/ENUM constraints where safe (mode in {LIVE, REPLAY_VALIDATION, EVAL}; booleans as {0,1}; status fields constrained to allowed sets) and enforce PRAGMA foreign_keys=ON in connections.
- Update DB interfaces to require mode + provenance on writes in LIVE; allow NULL for legacy reads.
- Add indices for hot paths: winning_sequences/winning_sequences_full_game (game_id, level_number, is_active), sequence_validation_attempts (sequence_id, agent_id), attempts (mode, role, game_id, level), action_proposals_log (attempt_id, step_idx), lesson_interpretations (game_id, level).
- Enforce pycache off globally: set PYTHONDONTWRITEBYTECODE=1 (or python -B) in run_evolution/autonomous_evolution_runner and test runners; add a guard that fails if __pycache__ exists after startup.
- Coordinate retention: align database_logger cleanup with safe_cleanup and set retention knobs for large JSON tables (proposals, frames) to stay under 10 GB.
- Testing: smoke import tests for migrated interfaces; DB migration validation queries; ensure env flag is honored.

## Phase 1: Instrumentation (No Logic Change)
- Wrap play_single_game with INIT/STEP/POST_STEP/FINALIZE scaffolding.
- Emit RUN_INIT, ACTION_PROPOSALS (even stub), ACTION_CHOSEN, ACTION_EXECUTED, FRAME_CHANGED, STEP_COMPLETE, RUN_FINALIZED with attempt_id/mode/role/step_idx.
- Log proposals to action_proposals_log; record ARC request/response in ACTION_EXECUTED.
- Add guard emissions (BUDGET_EXHAUSTED, ROLE_VIOLATION, MODE_WRITE_BLOCKED, HEARTBEAT_LOST, ACTION_SOURCE_EMPTY, FRAME_SANITY_FAIL) without blocking yet.
- Ingest legacy reasoning logs: map frames to attempt_id/mode/role, derive hangup tags (rare-color fixation, pseudo-button oscillation, offset sweeps) and attach to attempts and lesson_interpretations for analytics.
- Log Two-Streams weights with resonance: w_A, w_B, w_R on RUN_INIT/ACTION_PROPOSALS/ACTION_CHOSEN; store reasoning_tags for prompts used.
- Testing: regression replay on a small set of seeds to confirm behavior parity; assert event streams match prior actions; verify no __pycache__ generated.
- Preserve dynamic ATP reweighting: ensure adaptive_action_limits + agent_operating_mode_system role/w_B growth bonuses/penalties remain behavior-parity before moving to plugins.

## Phase 2: Mode & Guard Enforcement
- Enforce: only LIVE writes learning artifacts; REPLAY_VALIDATION/EVAL telemetry-only.
- Enforce budgets/roles; guard-triggered safe aborts with RUN_FINALIZED outcome=GUARD.
- Enable heartbeats; HEARTBEAT_LOST aborts.
- Testing: add cases for MODE_WRITE_BLOCKED, ROLE_VIOLATION, BUDGET_EXHAUSTED, HEARTBEAT_LOST; ensure attempts rows reflect guard outcomes; verify no new pycache.

## Phase 3: Plugin Extraction (Side-Effects Out of Core)
- Extract Sequence plugin (replay/save), CODS plugin (operator proposals/validation), Prestige/Budget plugin (accounting), Hypothesis/Lesson plugin (lesson_interpretations), Viral/HT plugin (packages), Sensation/Self-Model plugin (frame deltas), HookFailureMonitor (auto-disable).
- Add Lesson-Operator Fusion plugin (Games-as-Teachers + CODS): correlates lesson_interpretations with operator proposals, boosts operators that improve lesson coverage, records contradictions and transfer failures.
- Add Attention/Priors plugin: apply weak priors (change/motion/novelty/solidity/continuity/social cues) as soft weights in proposals; log when evidence contradicts priors.
- Add Resonance/Meta-Operator plugin: detect cross-game/operator/lesson resonance, compute w_R contributions, and register meta_operators (operator factories, discovery strategies) with provenance.
- Add Budget/Pacing plugin (wrap existing adaptive_action_limits): keep role multipliers, w_B growth bonuses, low-start boosts, stagnation penalties; expose telemetry to attempts.
- Core orchestrator becomes emit-only; plugins are idempotent, mode-aware, and HOOK_FAILURE_DETECTED-wrapped.
- Testing: plugin failure injection to ensure HOOK_FAILURE_DETECTED rows; parity checks on sequences/operators vs baseline; check auto-disable behavior; confirm pycache guard still passing.

## Phase 4: Action Source Ladder & Combiner
- Implement deterministic ladder Sequence → CODS → Heuristic/Escape → Noop with skip reasons logged.
- Proposal combiner logs w_A/w_B, evidence, mode/role guards; chosen action recorded in action_proposals_log.
- Testing: ladder coverage tests; confirm ACTION_SOURCE_EMPTY when exhausted; compare chosen actions to baseline on replay fixtures.

## Phase 5: Replay Validation Harness
- Use recorded attempts to replay in REPLAY_VALIDATION; compare proposal traces and outcomes for regression.
- Add health dashboards over attempts + hook_failures + guard codes.
- Validate lesson+operator transfer: replay teacher lessons with operator vocabulary; flag mismatches and decrement operator reliability; verify hangup tags drop after fixes.
- Validate priors and resonance: ensure weak priors can be overturned with evidence; track resonance_tags improvements across games; assert w_R use does not violate dual economies.
- Testing: CI job to run replay suite; fail on drift in proposal distributions or guard rates; ensure no pycache creation in CI artifacts.

## Phase 6: Tests & Harden
- Update tests to cover: guard codes, mode hygiene, action ladder, end-sequence win invariant, provenance on writes.
- Add frame sanity checks; abort on FRAME_SANITY_FAIL.
- Add audits for AGI-unified-theory invariants: dual economies separation (prestige vs actions), database-as-organism provenance fields present, viral spread tracked via source_attempt_id/source_mode, and decay/cleanup active.
- Add assertions for Two-Streams (w_A/w_B/w_R persisted), resonance tagging, prior override behavior, and meta-operator logging.
- Testing: expand unit/integration suites; enforce python -B in test runner; add lint to fail if __pycache__ is present post-run.

## Phase 7: Deprecate Legacy Paths
- Remove inline learning writes in core_gameplay/action_handler.
- Mark legacy migrations deprecated; regenerate complete_database_schema.sql.
- Remove residual log-file writes (database_logger to DB-only).
- Testing: final replay/CI gate on attempts/action_proposals_log parity; filesystem check ensures no __pycache__ remains.
