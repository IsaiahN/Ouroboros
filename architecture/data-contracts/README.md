# Data Contracts (Additive)

Authoritative data spine for behavior-parity refactor. All new tables are additive; existing schema remains untouched.

## Core Tables
- attempts: per-run provenance (attempt_id, game_id, level, agent_id, role, mode, budgets, outcomes, w_A/w_B/w_R, guard results).
- hook_failures: plugin failures with stack_hash, auto-disable flag, mode/role, attempt_id, guard code, contradiction tags.
 action_proposals_log: proposals (chosen/unchosen) with sources, weights, evidence, w_A/w_B/w_R, resonance_tags, reasoning_tags, role_compliance, attention_window_id, theory_validation_state snapshot.
 experiments: prediction-before-action tied to hypotheses (prediction, expected outcome, action taken, actual outcome, interpretation, theory_validation_state, contradiction flag, elimination flag).
 attention_windows: per-step detected focus windows (bbox, salient color/shape cues, cluster_size, prior flags, frame_id, attempt_id) to anchor proposals and hypotheses to specific regions; referenced by action_proposals_log via attention_window_id.
 theory_validation_states: enum to capture early/invalid/valid tests (e.g., PENDING, TOO_EARLY, INVALID_SETUP, VALIDATED, CONTRADICTED), referenced from experiments and action_proposals_log snapshots.
 Cluster cues: attention_windows.salient_cue should encode singleton vs cluster (e.g., rare_color_singleton, rare_color_cluster_146px) and cluster_size column to disambiguate hypotheses.
 Experiments must carry theory_validation_state; action_proposals_log must store role_compliance and theory_validation_state snapshot; attention_windows must store salient_cue granularity (singleton vs cluster) and cluster_size for rare-color patterns.
 action_proposals_log: (attempt_id, step_idx), (game_id, level), (resonance_tags), (role_compliance), (theory_validation_state).
 attention_windows: (attempt_id, step_idx), (salient_cue), (cluster_size), (prior_flag).
- competence_metrics: per-agent/per-generation rollups (prediction accuracy, theory coherence, transfer rate, explanation quality/adoption, metacog calibration, recovery rate).
- peer_teaching_graph: directed edges (teacher_agent_id → learner_agent_id) with concept_id, outcome, adoption success, and timestamps.
- gap_registry: detected gaps with type (performance/comprehension/metacog/architectural/pedagogical), root cause, severity, affected population, consensus vs accuracy flags.
- interventions: planned/executed interventions with type (agent-level, network-level, curriculum, code-level), resources, success criteria, rollback conditions, outcome metrics.
- code_proposals: autonomous code-change proposals with what/why/risk/impact, branch/PR metadata, test results, canary vs baseline metrics, merge/rollback status (respecting human/manual branches and production branch Ouroboros-v2).
- replay_index: pointers to ARC scorecards/replays/recordings (scorecard_id, replay_id, arc_game_id, agent_type, tags, local_recording_path optional), linked to attempts for REPLAY_VALIDATION and auditing without storing full frames.
- attention_windows: per-step detected focus windows (bbox, salient color/shape cues, prior flags, frame_id, attempt_id) to anchor proposals and hypotheses to specific regions; referenced by action_proposals_log via attention_window_id.
- theory_validation_states: enum to capture early/invalid/valid tests (e.g., PENDING, TOO_EARLY, INVALID_SETUP, VALIDATED, CONTRADICTED), referenced from experiments.
- role_compliance: per-proposal flag persisted on action_proposals_log to reflect role adherence seen in logs.
- cluster cues: attention_windows.salient_cue should encode singleton vs cluster (e.g., rare_color_singleton, rare_color_cluster_146px) to disambiguate hypotheses.

## Invariants & Constraints
- All tables carry attempt_id where applicable; source_attempt_id/source_mode for derived artifacts (sequences, viral packages, operators, lessons, hypotheses).
- mode ENUM constrained to {LIVE, REPLAY_VALIDATION, EVAL}; booleans constrained to {0,1}; status fields constrained to allowed sets.
- foreign_keys=ON required; NULL allowed for legacy rows during migration, but new writes must include mode + provenance in LIVE.
- Lesson coverage recorded as explains_count, fails_count; contradictions required when fails_count > 0.
- Hypotheses require at least one assumption or theory text; experiments require prediction, expected outcome, actual outcome, and interpretation; elimination_tracker requires target_type + reason.
- Biographies require agent_id linkage; peer_teaching edges require teacher/learner IDs and concept_id; gaps require type/severity; interventions require linked gap_id; code_proposals require branch name and mode tags.
- Attention windows require attempt_id and frame/step reference; action_proposals_log rows referencing attention_window_id must have matching attempt_id.
- Experiments must carry theory_validation_state; action_proposals_log must store role_compliance; attention_windows must store salient_cue granularity (singleton vs cluster) for rare-color patterns.

## Indices
- attempts: (mode, role, game_id, level), (agent_id, created_at).
- action_proposals_log: (attempt_id, step_idx), (game_id, level), (resonance_tags).
- lesson_interpretations: (game_id, level), (resonance_tags), (concept_id).
- hypotheses: (game_id, level, current_status), (concept_id, version), (source_attempt_id).
- experiments: (hypothesis_id, attempt_id, step_idx), (prediction_outcome_flag).
- concept_library: (concept_name), (merge_status), (peer_review_score).
- agent_biographies: (agent_id), (updated_at).
- competence_metrics: (agent_id, generation), (game_id, level).
- peer_teaching_graph: (teacher_agent_id, learner_agent_id, concept_id).
- gap_registry: (gap_type, severity, concept_id), (status).
- interventions: (gap_id, status, intervention_type).
- code_proposals: (branch_name, status), (gap_id), (created_at).
- attention_windows: (attempt_id, step_idx), (salient_cue), (prior_flag).
- theory_validation_states: (state) enum lookup; experiments.state indexed for quick contradiction/too-early scans.
- action_proposals_log: index role_compliance for compliance vs guard analysis.
- replay_index: (attempt_id, scorecard_id, replay_id, arc_game_id, agent_type, tags).

## Tagging Existing Artifacts (additive columns)
- sequences, viral_packages, hypotheses, prestige logs: add source_attempt_id (uuid) and source_mode (enum) to track provenance.
- Invariants: source_attempt_id required for new writes; legacy rows allowed null; writes blocked unless mode == LIVE.
- Add CHECK constraints where safe: booleans in {0,1}; mode enum enforced on new columns; status fields constrained to allowed values.

## Constraints & Hygiene
- Enforce PRAGMA foreign_keys=ON in connections; add a guard that asserts it remains on.
- Add unique constraint on (game_id, level_number, is_active) for winning_sequences to prevent duplicate active solutions; add index on winning_sequences_full_game.game_id for retrieval.
- Index source tags to trace lineage across artifacts.
- Reasoning log derivatives: map legacy/live reasoning logs to attempts via attempt_id/mode/role; store distilled hangup tags and contradictions alongside lesson_interpretations and action_proposals_log (JSON ok if small; extend tables if needed).
- Replays/recordings: persist only pointers in replay_index and thin summaries (actions, deltas, contradictions); raw recording files may be staged then deleted after ingestion per “no log files” rule.
- Two-Streams fields: persist w_A/w_B/w_R in action_proposals_log and attempts; resonance_tags on lesson_interpretations; ensure CHECK constraints for mode enum and booleans.
- Priors/meta/operators: if stored, keep priors_applied/prior_overturned flags and meta_operator references as JSON with provenance; remain additive and nullable for legacy compatibility.
- Observer hygiene: biography/competence/peer_teaching/gap/intervention tables are read-mostly; ensure writes only in LIVE; enforce that human/manual branches remain untouched by automated code_proposals; production branch fixed as Ouroboros-v2 in metadata.

## Retention & Cleanup
- safe_cleanup must coordinate with database_logger to delete stale hooks/log payloads while preserving wins, positive evidence, active lessons/operators, and contradiction histories.
- Large JSON blobs (proposal traces, frames) should have configurable TTL; vacuum mindful of 200 GB limit.
- Hypotheses/experiments elimination history must persist long enough to prevent circular probes; retain contradiction counts even when pruning large payloads.

## Governance
- All writes pass through data interface that enforces mode/role/budget guards and emits HOOK_FAILURE_DETECTED on violation.
- VACUUM and cleanup remain in safe_cleanup; no log files allowed; database is the source of truth.
