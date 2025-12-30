# Runtime & Event Model

This captures the behavior-parity loop split (init/step/post_step/finalize), event taxonomy, RunContext, and guardrails for mode-safe execution.

## Loop Phases (behavior parity target)
- INIT: hydrate RunContext (mode, role, budgets, sequence candidates), register heartbeat counters, emit RUN_INIT.
- STEP: gather proposals, combine, emit ACTION_CHOSEN, execute via ARC API, emit ACTION_EXECUTED, FRAME_CHANGED, and HEARTBEAT_TICK.
- POST_STEP: evaluate frame deltas, append step metrics, emit STEP_COMPLETE; decide continue/terminate based on budgets and state.
- FINALIZE: emit RUN_FINALIZED with outcome, flush buffered logs, release resources; plugins close out (e.g., sequence save, lesson extraction) respecting mode guards.

## Event Taxonomy (publish-only from orchestrator)
- RUN_INIT, ACTION_PROPOSALS, ACTION_CHOSEN, ACTION_EXECUTED, FRAME_CHANGED, STEP_COMPLETE, RUN_FINALIZED.
- HOOK_FAILURE_DETECTED, GUARD_TRIGGERED (budget/mode/role), HEARTBEAT_MISSED, MODE_VIOLATION.
- ROLE_ASSIGNMENT_SET, SEQUENCE_REPLAY_STARTED/FINISHED, CODS_OPERATOR_USED, LESSON_INTERPRETATION_READY.

## RunContext (required fields)
- attempt_id (uuid), game_id, level, generation, agent_id, role, mode, budgets {actions_remaining, game_actions_remaining}.
- w_A_weight, w_B_weight, available_actions (per step), sequence_source_id (if replay), operator_source_id (if CODS), source_mode.
- heartbeat_counters {step_idx, max_steps}, guard_states {budget_ok, mode_ok, role_ok}.
- replay_guard: ensures REPLAY_VALIDATION/EVAL prohibit writes.

## Guards and Heartbeats
- BudgetGuard: decrements per action; triggers GUARD_TRIGGERED when exhausted.
- ModeGuard: rejects learning writes unless mode == LIVE; emits MODE_VIOLATION otherwise.
- RoleGuard: enforces frontier vs beaten level access; emits GUARD_TRIGGERED on violation.
- Heartbeat: every step increments heartbeat_counters; missing tick within threshold emits HEARTBEAT_MISSED and forces safe abort.

## Event Bus Contract
- Orchestrator emits only; plugins subscribe.
- No plugin may throw through the bus; exceptions captured, bucketed (stack_hash), emitted as HOOK_FAILURE_DETECTED, and recorded in hook_failures with auto-disable flag.
- Ordering: events processed in publish order per step; plugins must be idempotent and mode-aware.

## Mode Effects
- LIVE: full telemetry + learning writes permitted.
- REPLAY_VALIDATION: telemetry only; no learning writes; used to confirm sequences and regression-check fixes.
- EVAL: telemetry only; used for benchmarks/health; zero learning writes.

## Behavior Parity Plan
- Start with existing play_single_game; instrument emissions without changing decisions.
- Move side-effects into plugins behind the bus.
- Enforce guards and heartbeats; abort safely with recorded reason rather than silent failure.
