# play_single_game Side-Effects Mapping (Behavior-Parity Plan)

Goal: inventory all side-effects in play_single_game and assign them to plugins/events with guard placement for behavior-parity migration. This is a planning map; actual code changes follow the phases in architecture/overview.md.

## Loop Phases and Side-Effects
- INIT
  - Current side-effects: session setup, budget initialization, role/mode selection, sequence candidate loading, logging start.
  - Target: emit RUN_INIT; write attempts row; no learning writes yet. Guard: role guard on frontier vs beaten selection.
  - Plugins: HookFailureMonitor (observes), Sequence plugin (notes candidate), Prestige/Budget plugin (records budgets), Sensation/Self-Model plugin (initializes state).

- STEP (per action)
  - Current side-effects: propose action (sequence/heuristic/CODS), log reasoning, execute ARC API call, update budgets, collect frame.
  - Target: emit ACTION_PROPOSALS, ACTION_CHOSEN, ACTION_EXECUTED, FRAME_CHANGED, STEP_COMPLETE.
  - Guards: budget guard before execute; mode guard on any learning write; role guard if level access changes.
  - Plugins: Sequence plugin (replay/proposals), CODS plugin (operator proposals/validation), Hypothesis/Metacog plugin (reasoning/lesson hooks), Prestige/Budget plugin (budget decrement), HookFailureMonitor (captures any hook exceptions), Sensation/Self-Model plugin (frame deltas), Viral/Horizontal Transfer plugin (candidate extraction queued for finalize if LIVE), Action ladder enforcement (Sequence→CODS→Heuristic→Noop).

- POST_STEP
  - Current side-effects: check win/loss, maybe save sequence fragments, update stats, frustration/loop detectors.
  - Target: emit STEP_COMPLETE (with guard state), optionally LESSON_INTERPRETATION_READY when applicable.
  - Guards: heartbeat tick; frame sanity check (FRAME_SANITY_FAIL if deltas missing while action claimed change).
  - Plugins: Sequence plugin (partial save in LIVE), Viral plugin (package candidates), Metacog (lesson coverage/contradictions), Health monitors (frustration/loop/oscillation/no-delta detection) emitting HOOK_FAILURE_DETECTED on exceptions; StruggleGuard must emit oscillation_no_closure and no_delta tags plus COMPREHENSION_GAP_DETECTED for GapRegistry.

- FINALIZE
  - Current side-effects: save sequences, prestige updates, budget accounting, logging summaries.
  - Target: emit RUN_FINALIZED; finalize attempts row; flush action_proposals_log; commit lesson_interpretations in LIVE; close out sequence/viral/hypothesis writes in LIVE only.
  - Guards: mode guard on all writes; role guard not needed if game concluded; heartbeat not required after finalize.
  - Plugins: Sequence plugin (save/reputation), Viral plugin (package persistence), CODS plugin (operator validation results), Prestige/Budget plugin (final accounting), HookFailureMonitor (final errors), Reliability hooks (mark auto-disabled if threshold exceeded), GapRegistry (mark interventions completed/failed).

## Cross-Cutting Side-Effects to Extract
- Learning writes (sequences, viral packages, hypotheses, lessons): move to plugins; gated by mode == LIVE; attach source_attempt_id/source_mode.
- Reasoning logs: reframe to lesson interpretations; store in lesson_interpretations in LIVE; telemetry-only in other modes.
- Budget updates: centralized in Prestige/Budget plugin; guard emits BUDGET_EXHAUSTED.
- Role enforcement: enforced before INIT and on level transitions; emits ROLE_VIOLATION on breach.
- Mode enforcement: any write attempt in non-LIVE emits MODE_WRITE_BLOCKED and is blocked.
- Action ladder: when a source is unavailable, emit ACTION_SOURCE_EMPTY if ladder exhausted; log skip reasons at each rung.
- Heartbeats: emitted every STEP; HEARTBEAT_LOST triggers safe abort and RUN_FINALIZED with outcome=GUARD.
- Frame sanity: compare claimed action to frame delta; emit FRAME_SANITY_FAIL if mismatch; safe abort with RUN_FINALIZED outcome=GUARD.

## Migration Notes
- Phase 2 (loop split): instrument events without changing decisions; route existing logs to action_proposals_log and attempts.
- Phase 3 (pipeline): introduce proposal combiner but keep selection equivalent to current logic until toggled.
- Phase 4 (mode hygiene): enforce guards; block writes in non-LIVE; expect initial guard-triggered aborts to surface hidden side-effects.
- Phase 5 (plugins): move each side-effect into its plugin with try/except to HOOK_FAILURE_DETECTED; enable auto-disable flags.
- Regression: use REPLAY_VALIDATION to replay attempts and verify parity; compare action_proposals_log traces.
