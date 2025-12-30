# Event Payload Schemas and Guard Codes

Authoritative event contracts for the event-first runtime. All payloads must carry attempt_id, mode, role, and step_idx (where applicable). No optional-by-default fields; use explicit nulls only when justified.

## Core Events
- RUN_INIT: {attempt_id, game_id, level, generation, agent_id, role, mode, budgets {actions_remaining, game_actions_remaining}, w_A_weight, w_B_weight, sequence_source_id?, operator_source_id?, source_mode?, timestamp}
- ACTION_PROPOSALS: {attempt_id, step_idx, available_actions, proposals: [{action, weight_delta, evidence, source, w_A, w_B, mode_guard, role_guard}], timestamp}
- ACTION_CHOSEN: {attempt_id, step_idx, chosen_action, chosen_reason, proposals_snapshot_id (fk to action_proposals_log), w_A_mix, w_B_mix, timestamp}
- ACTION_EXECUTED: {attempt_id, step_idx, chosen_action, arc_request, arc_response, exec_ms, timestamp}
- FRAME_CHANGED: {attempt_id, step_idx, frame_delta_hash, objects_moved, score_delta, state_flag (WIN/LOSS/IN_PROGRESS), timestamp}
- STEP_COMPLETE: {attempt_id, step_idx, guards {budget_ok, mode_ok, role_ok}, actions_remaining, game_actions_remaining, heartbeat_tick, timestamp}
- RUN_FINALIZED: {attempt_id, outcome (WIN/LOSS/ABORT/GUARD), actions_used, levels_completed, score, time_ms, failure_reason?, timestamp}

## Health and Guard Events
- HOOK_FAILURE_DETECTED: {attempt_id, hook_name, hook_phase, exception_type, message, stack_hash, auto_disabled_flag, timestamp}
- GUARD_TRIGGERED: {attempt_id, guard_code, step_idx?, detail, actions_remaining?, game_actions_remaining?, timestamp}
- HEARTBEAT_MISSED: {attempt_id, step_idx, expected_tick, observed_tick, timestamp}
- MODE_VIOLATION: {attempt_id, attempted_write, mode, timestamp}

## Domain Events
- ROLE_ASSIGNMENT_SET: {attempt_id, role, mode, timestamp}
- SEQUENCE_REPLAY_STARTED: {attempt_id, sequence_id, source_mode, timestamp}
- SEQUENCE_REPLAY_FINISHED: {attempt_id, sequence_id, succeeded, timestamp}
- CODS_OPERATOR_USED: {attempt_id, operator_id, validation_state, evidence, timestamp}
- LESSON_INTERPRETATION_READY: {attempt_id, interpretation_id, explains_examples, fails_examples, contradictions, timestamp}

## Guard Failure Codes
- BUDGET_EXHAUSTED: actions_remaining < 0 or game_actions_remaining < 0.
- ROLE_VIOLATION: role attempted a forbidden level/game per policy.
- MODE_WRITE_BLOCKED: non-LIVE attempted learning write.
- HEARTBEAT_LOST: heartbeat gap exceeded threshold.
- ACTION_SOURCE_EMPTY: no safe action available; ladder exhausted.
- FRAME_SANITY_FAIL: frame delta missing when action claimed change (possible API mismatch).

## Expectations
- All events are immutable, append-only; ordered by emit time within a step.
- Plugins must be idempotent with respect to duplicate events.
- No plugin may throw through the bus; exceptions are captured as HOOK_FAILURE_DETECTED.
- Guard codes must match the above enumerations; add new codes via ADR before use.
