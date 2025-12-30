# Reliability, Redundancy, and Playbooks

Designing for airline-grade robustness: predictable failure modes, explicit attribution, safe degradation, and recovery.

## Reliability Principles
- No silent failure: every exception becomes HOOK_FAILURE_DETECTED and a hook_failures row with stack_hash.
- Deterministic traces: attempts and action_proposals_log reconstruct every decision (role, mode, w_A, w_B, source, evidence).
- Separation of concerns: orchestrator emits events only; plugins cannot crash the loop.
- Mode hygiene: only LIVE writes learning; REPLAY_VALIDATION/EVAL are telemetry-only.

## Failure Mode Taxonomy
- Plugin error: captured, bucketed, plugin auto-disabled after threshold; core loop continues with reduced capability.
- Guard violation: budget/mode/role guard triggers safe abort; recorded in hook_failures with guard type.
- Heartbeat loss: missing step heartbeat triggers safe abort; attempt marked failed with reason.
- External API error: ARC API failure recorded with request/response; retry policy bounded; no infinite loops.

## Guard Codes (authoritative)
- BUDGET_EXHAUSTED: actions_remaining < 0 or game_actions_remaining < 0.
- ROLE_VIOLATION: role attempted forbidden frontier/beaten access.
- MODE_WRITE_BLOCKED: non-LIVE attempted learning write.
- HEARTBEAT_LOST: heartbeat gap exceeded threshold.
- ACTION_SOURCE_EMPTY: action source ladder exhausted; noop exit.
- FRAME_SANITY_FAIL: frame delta missing or inconsistent with claimed change.

## Redundancy & Degrade Paths
- Action source ladder: Sequence → CODS → Heuristic/Escape → Deterministic Noop Exit. Each step emits why the previous source was skipped.
- Learning side-effects: each plugin independently mode-checked; failure of one does not block others.
- Data lineage: source_attempt_id/source_mode on all artifacts ensures replayability even with partial data.
- Watchdogs: per-plugin health counters; repeated failures flip auto_disabled_flag; re-enable via DB flags after fix.

## Observability & Health
- Heartbeats per step; HEARTBEAT_MISSED → abort and record.
- Health dashboard queries (to be scripted): count of hook_failures by stack_hash (top offenders), attempts success rate by mode, action_proposals_log completeness (steps without proposals).
- Missing data detection: absence of proposals or heartbeats is itself an anomaly; recorded as hook_failures.

## Recovery Playbooks
- Plugin crash: identify stack_hash, auto-disabled; run REPLAY_VALIDATION on same input after fix; re-enable flag.
- Guard trips: inspect guard type, adjust budgets/roles only after root cause found; never bypass guard without reason.
- ARC API instability: bounded retries; if repeated, mark attempt failed with reason; no runaway loops.
- Data corruption suspicion: verify invariants via data-contracts checks; never delete, prefer additive fixes and migrations.

## Operational Checks (pre/post run)
- Pre-run: ensure mode set, budgets set, heartbeats enabled, plugin flags loaded, PYTHONDONTWRITEBYTECODE=1 (or python -B), no __pycache__ present.
- Post-run: run investigate_bugs.py; query hook_failures for new stack_hashes; run REPLAY_VALIDATION for recent regressions; vacuum/cleanup via safe_cleanup when required; fail the run if __pycache__ appears.
