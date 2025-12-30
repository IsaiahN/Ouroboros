# Sequenced Refactor Plan

Phased execution to reach the event-first, guard-heavy runtime with provenance. Behavior parity first, then extraction. Testing and pycache hygiene are first-class: use python -B or PYTHONDONTWRITEBYTECODE=1 at all entry points, and run regression suites per phase.

## Phase 0: Migrations & Plumbing
- Apply additive migrations for attempts, hook_failures, action_proposals_log, lesson_interpretations, source_attempt_id/source_mode tags.
- Update DB interfaces to require mode + provenance on writes in LIVE; allow NULL for legacy reads.
- Enforce pycache off globally: set PYTHONDONTWRITEBYTECODE=1 (or python -B) in run_evolution/autonomous_evolution_runner and test runners; add a guard that fails if __pycache__ exists after startup.
- Testing: smoke import tests for migrated interfaces; DB migration validation queries; ensure env flag is honored.

## Phase 1: Instrumentation (No Logic Change)
- Wrap play_single_game with INIT/STEP/POST_STEP/FINALIZE scaffolding.
- Emit RUN_INIT, ACTION_PROPOSALS (even stub), ACTION_CHOSEN, ACTION_EXECUTED, FRAME_CHANGED, STEP_COMPLETE, RUN_FINALIZED with attempt_id/mode/role/step_idx.
- Log proposals to action_proposals_log; record ARC request/response in ACTION_EXECUTED.
- Add guard emissions (BUDGET_EXHAUSTED, ROLE_VIOLATION, MODE_WRITE_BLOCKED, HEARTBEAT_LOST, ACTION_SOURCE_EMPTY, FRAME_SANITY_FAIL) without blocking yet.
- Testing: regression replay on a small set of seeds to confirm behavior parity; assert event streams match prior actions; verify no __pycache__ generated.

## Phase 2: Mode & Guard Enforcement
- Enforce: only LIVE writes learning artifacts; REPLAY_VALIDATION/EVAL telemetry-only.
- Enforce budgets/roles; guard-triggered safe aborts with RUN_FINALIZED outcome=GUARD.
- Enable heartbeats; HEARTBEAT_LOST aborts.
- Testing: add cases for MODE_WRITE_BLOCKED, ROLE_VIOLATION, BUDGET_EXHAUSTED, HEARTBEAT_LOST; ensure attempts rows reflect guard outcomes; verify no new pycache.

## Phase 3: Plugin Extraction (Side-Effects Out of Core)
- Extract Sequence plugin (replay/save), CODS plugin (operator proposals/validation), Prestige/Budget plugin (accounting), Hypothesis/Lesson plugin (lesson_interpretations), Viral/HT plugin (packages), Sensation/Self-Model plugin (frame deltas), HookFailureMonitor (auto-disable).
- Core orchestrator becomes emit-only; plugins are idempotent, mode-aware, and HOOK_FAILURE_DETECTED-wrapped.
- Testing: plugin failure injection to ensure HOOK_FAILURE_DETECTED rows; parity checks on sequences/operators vs baseline; check auto-disable behavior; confirm pycache guard still passing.

## Phase 4: Action Source Ladder & Combiner
- Implement deterministic ladder Sequence → CODS → Heuristic/Escape → Noop with skip reasons logged.
- Proposal combiner logs w_A/w_B, evidence, mode/role guards; chosen action recorded in action_proposals_log.
- Testing: ladder coverage tests; confirm ACTION_SOURCE_EMPTY when exhausted; compare chosen actions to baseline on replay fixtures.

## Phase 5: Replay Validation Harness
- Use recorded attempts to replay in REPLAY_VALIDATION; compare proposal traces and outcomes for regression.
- Add health dashboards over attempts + hook_failures + guard codes.
- Testing: CI job to run replay suite; fail on drift in proposal distributions or guard rates; ensure no pycache creation in CI artifacts.

## Phase 6: Tests & Harden
- Update tests to cover: guard codes, mode hygiene, action ladder, end-sequence win invariant, provenance on writes.
- Add frame sanity checks; abort on FRAME_SANITY_FAIL.
- Testing: expand unit/integration suites; enforce python -B in test runner; add lint to fail if __pycache__ is present post-run.

## Phase 7: Deprecate Legacy Paths
- Remove inline learning writes in core_gameplay/action_handler.
- Mark legacy migrations deprecated; regenerate complete_database_schema.sql.
- Remove residual log-file writes (database_logger to DB-only).
- Testing: final replay/CI gate on attempts/action_proposals_log parity; filesystem check ensures no __pycache__ remains.
