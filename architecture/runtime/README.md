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
- w_A_weight, w_B_weight, w_R_weight (resonance), available_actions (per step), sequence_source_id (if replay), operator_source_id (if CODS), source_mode.
- heartbeat_counters {step_idx, max_steps}, guard_states {budget_ok, mode_ok, role_ok}.
- replay_guard: ensures REPLAY_VALIDATION/EVAL prohibit writes.
- hypothesis_context: current hypothesis id/version, assumptions, prediction-for-this-step, expected outcome, contradiction_count, elimination flags.
- biography_context: learning history pointer, active hypothesis list, revisions pending, struggle indicators, blind-spot tags, WA/WB adoption/rejection notes, peer-source references.
- competence_rollup (per attempt snapshot): prediction accuracy to-date, theory coherence score, transfer attempts/success, explanation quality votes, metacog calibration, recovery rate.
- attention_windows: per-step focus windows from object/attention detectors (bbox, color/shape cues, prior flags) so proposals and hypotheses can reference concrete regions; linked to proposals via attention_window_id.
- validation_state: per-step theory_validation_state (PENDING, TOO_EARLY, INVALID_SETUP, VALIDATED, CONTRADICTED) persisted via experiments for guard/analysis use.
- role_compliance_state: per-step note of whether chosen proposal adhered to role constraints; persisted in action_proposals_log for compliance vs guard analysis.

## Guards and Heartbeats
- BudgetGuard: decrements per action; triggers GUARD_TRIGGERED when exhausted.
- ModeGuard: rejects learning writes unless mode == LIVE; emits MODE_VIOLATION otherwise.
- RoleGuard: enforces frontier vs beaten level access; emits GUARD_TRIGGERED on violation.
- Heartbeat: every step increments heartbeat_counters; missing tick within threshold emits HEARTBEAT_MISSED and forces safe abort.
- TheoryActionGuard: compares stated hypothesis/prediction vs chosen action; flags circular probes, assumption drift, and premature convergence; emits GUARD_TRIGGERED or HOOK_FAILURE_DETECTED with contradiction tags.
- StruggleGuard: detects stuck-patterns, blind spots (ignored lesson aspects), assumption traps, and working-memory overload signals; emits GUARD_TRIGGERED tags to steer probes or hand off to interventions. Wire oscillation_no_closure (>=4 offset sweeps without state change) and no_delta (>=5 unchanged frames) tags here; both should forward COMPREHENSION_GAP_DETECTED to GapRegistry.

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
- Reasoning logs: ingest legacy/live logs by attempt_id/mode/role; translate narrative steps into hangup tags and contradictions tied to ACTION_PROPOSALS and LESSON_INTERPRETATION_READY events so plugins can react (e.g., boost CODS operator that resolves a logged contradiction, or trigger GUARD_TRIGGERED on repeated oscillation patterns).
- Two-Streams + resonance: propagate w_A/w_B/w_R through events and plugins; resonance tags come from cross-game/operator/lesson agreement and only affect weighting, not budgets.
- Priors plugin: apply weak attention/physics/social priors as soft weights; log when evidence overturns priors to avoid brittleness.
- Lesson interface: capture lesson setup (initial frames), learning objective (win condition), attended vs ignored aspects, and curriculum placement; ambiguous lessons keep multiple interpretations until evidence resolves contradictions.
- Metacog instrumentation: store prediction-before-action, theory revisions on mismatch, elimination of disproven hypotheses, and cross-attempt failure pattern tags; expose to events so validation can replay divergences.
- Agent-observer surfaces: emit per-step/per-run signals needed for agent biography dashboards (theory evolution, struggles, WA/WB updates), peer-teaching edges (who learned from whom), and gap detection signals (performance/comprehension/metacog/architectural/pedagogical).
- Gap registry hooks: when gaps are detected/diagnosed, emit events for remediation planner; include severity, type, root-cause hints, and affected population counts.

## Immediate wiring items (must-implement)
- Populate role_compliance and theory_validation_state snapshots on every action_proposals_log write; block if fields missing in LIVE.
- Implement no-delta guard: when frames_unchanged >= threshold (default 5), emit GUARD_TRIGGERED with code NO_DELTA and forward COMPREHENSION_GAP_DETECTED.
- Implement oscillation_no_closure detector: detect repeated offset sweeps with no closure, tag struggle_guard, emit COMPREHENSION_GAP_DETECTED, and enqueue closure_probe operator as next intervention.
- Register closure_probe CODS operator; log CODS_OPERATOR_USED with operator_id=closure_probe and validation_state from experiments.
- GapRegistry consumer: on COMPREHENSION_GAP_DETECTED create gap_registry row, enqueue interventions (peer_fetch, operator_change→closure_probe), and mark outcomes.
