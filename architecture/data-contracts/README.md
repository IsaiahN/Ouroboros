# Data Contracts (Additive)

Authoritative data spine for behavior-parity refactor. All new tables are additive; existing schema remains untouched.

## attempts (authoritative run record)
- Columns: attempt_id (pk, uuid), game_id, level, agent_id, role, mode, generation, actions_used, actions_budget, game_actions_used, game_actions_budget, levels_completed, score, time_ms, succeeded (bool), source_sequence_id (nullable), source_mode.
- Invariants: must exist for every run; mode in {LIVE, REPLAY_VALIDATION, EVAL}; budgets non-negative; succeeded only true if WIN criteria met.

## hook_failures (failure attribution)
- Columns: id (pk), attempt_id, hook_name, hook_phase (init/step/post_step/finalize), exception_type, message, stack_hash, auto_disabled_flag (bool), game_id, level, agent_id, generation, timestamp.
- Invariants: created on every caught plugin/hook exception; stack_hash used for bucketing; auto_disabled_flag flipped after N occurrences (configurable via DB flags).

## action_proposals_log (decision trace)
- Columns: id (pk), attempt_id, step_idx, available_actions, proposals (json: action, weight_delta, evidence, source, w_A, w_B, mode_guard, role_guard), chosen_action, chosen_reason, mode.
- Invariants: one row per step; proposals must include w_A and w_B weights; chosen_action must be member of available_actions; mode_guard recorded for audit.

## lesson_interpretations (Games-as-Teachers)
- Columns: id (pk), attempt_id, game_id, level, interpretation, explains_examples (bool), fails_examples (bool), confidence, contradictions, coverage_notes, source_mode, created_at.
- Invariants: only written in LIVE; references attempt_id; contradictions cannot be null (use empty list if none).

## Tagging Existing Artifacts (additive columns)
- sequences, viral_packages, hypotheses, prestige logs: add source_attempt_id (uuid) and source_mode (enum) to track provenance.
- Invariants: source_attempt_id required for new writes; legacy rows allowed null; writes blocked unless mode == LIVE.

## Constraints & Indices
- attempts.mode, attempts.role indexed for analytics.
- hook_failures.stack_hash + hook_name indexed for bucketing and auto-disable logic.
- action_proposals_log.attempt_id + step_idx indexed for fast trace reconstruction.
- source tags indexed to trace lineage across artifacts.

## Governance
- All writes pass through data interface that enforces mode/role/budget guards and emits HOOK_FAILURE_DETECTED on violation.
- VACUUM and cleanup remain in safe_cleanup; no log files allowed; database is the source of truth.
