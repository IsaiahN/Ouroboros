# Sequenced Refactor Plan

Phased execution to reach the event-first, guard-heavy runtime with provenance. Behavior parity first, then extraction. Testing and pycache hygiene are first-class: use python -B or PYTHONDONTWRITEBYTECODE=1 at all entry points, and run regression suites per phase.

## Status snapshot
- [x] Event-first spine: attempts/proposals/steps/guards emit on EventBus; HOOK_FAILURE_DETECTED auto-emits and is persisted to hook_failures.
- [x] RunContext budgets/guards wired through the loop; guard exhaustion logs to spine.
- [x] action_proposals_log stores role_compliance/theory_validation_state/resonance/attention id; provenance weights recorded.
- [x] Gap/closure/StruggleGuard and COMPREHENSION_GAP_DETECTED flow.
- [x] Action6 guard/coords protocol and swarm/replay alignment.
- [x] Metacog/observer schema expansion and plugins extraction.
- [x] Integration alignment plan execution (see architecture/integration_alignment_plan.md).

## Execution checklist (AGI Unified Theory aligned)
- [x] Schema audit: ensure metacog/observer tables have decay/credibility/lineage fields, provenance, mode checks, FKs on attempts, PRAGMA foreign_keys=ON.
- [x] Observer plugin hardening: MetacogObserverPlugin logs ambiguity/ladder/resonance with cause/effect vs compare/contrast tags; LIVE-only writes; HOOK_FAILURE coverage.
- [x] Ladder/tag wiring: add structure and PCTL stage tags into resonance_tags/lesson stubs; keep ontology writes LIVE-only.
- [x] Ambiguity telemetry: surface high-consensus/low-score markers via resonance_tags (no new tables) for dashboards.
- [x] Cross-domain resonance: standardize operator_hint/decomposition_hint domain tags; ensure decay/lineage when recording viral/meta-operators.
- [x] Scheduler mixed-domain flag: add opt-in mixed-domain batches; preserve role ratios/action budgets; telemetry-only tagging.
- [x] Decay/compression hooks: populate decay fields on new observer/metacog rows; include in safe_cleanup/compression; exclude legacy (source_mode='LEGACY').
- [x] Mode/role hygiene sweep: re-verify LIVE-only for learning writes (world model, knowledge_synthesis, science_engine, inferred_beliefs, sequence reputation); telemetry allowed in replay/eval.
- [x] Tests/validation: extend mode-gate, plugin failure, structure/PCTL tagging, decay-field presence; run db_validation and replay_validation; enforce no __pycache__.
- [x] Docs/readiness: update status when done; document mixed-domain flag default OFF; confirm dual economies, DB-only outputs, PYTHONDONTWRITEBYTECODE enforced.

### Schema audit findings (now resolved; provenance/decay + milestones in place)
- Metacog tables (assumptions/eliminations/failure_patterns/insights/predictions) now carry provenance + decay/credibility fields; legacy rows tagged via source_mode='LEGACY'.
- Gap/intervention tables carry attempt_id/source_mode/generation/role + decay; indices added for hot lookups.
- Oracle observations and valence associations have provenance + decay/credibility columns and supporting indices.
- Ambiguity telemetry remains observability-only via resonance_tags/ladder traces; no new tables required for ambiguity.
- Thought experiment scaffold: intrinsic_milestones table (provenance/decay) added for intrinsic milestones without touching control paths.

## Immediate wiring (no code refactor yet, required for build readiness)
- [x] Add closure_probe CODS operator and log CODS_OPERATOR_USED with validation_state from experiments; enqueue closure_probe when oscillation_no_closure is raised.
- [x] StruggleGuard: emit oscillation_no_closure after >=4 offset sweeps without state change and no_delta after >=5 unchanged frames; both emit COMPREHENSION_GAP_DETECTED.
- [x] TheoryActionGuard/Action logging: persist role_compliance and theory_validation_state on every action_proposals_log row; fail fast in LIVE if missing.
- [x] GapRegistry consumer: on COMPREHENSION_GAP_DETECTED create gap_registry row and enqueue interventions (peer_fetch, operator_change→closure_probe); track outcomes in interventions table.

## ARC API alignment (actions, scorecards, swarm, recordings)
- [x] Enforce Action 6 protocol: always send x,y (0-63), prefer ACTION1-5/7 first, and justify ACTION6 coordinates from frame salience (rare color, contrast, shape). Add guard to block raw ACTION6 without coords; add Action6Reasoner hook to pick coords from attention_windows salience (aligns with actions.md and arc_api_actions_rules). (Guard + salience reasoner + preference ordering wired.)
- [x] Scorecards: always open/close per run; tags carry mode/role/game_id/generation/session/pid/thread/git; scorecard_id stored in attempts and replay_index pointer (core_gameplay writes replay_index on finalize).
- [x] Swarm orchestration: runner launches one task per game slot (swarm) with per-slot GameplayEngine instances; scheduler tags (mode/role/game) flow into scorecard tags; scorecard_id + tags flow into replay_index and attempts. Honors `--game` filters and preserves budget/optimizer_target wiring.
- [x] Recordings/replays: rely on ARC-provided replays; store pointers (scorecard_id, replay_id, local recording filename if staged) instead of frames. In LIVE, optionally stage JSONL to temp, ingest summaries (actions/deltas/contradictions), then delete file (flagged by stage_recordings/ARC_STAGE_RECORDINGS). In REPLAY_VALIDATION, pull from replay_index instead of regenerating actions.

## Acceptance checks for ARC alignment and guards
- [x] Action6 guard: reject missing coords; Action6Reasoner must derive coords from attention_windows salience; validate in REPLAY_VALIDATION using recorded traces. (Runtime guard blocks blind ACTION6; replay batch checks coords + attention_window_id and logs hook_failures. Pending verification run.)
- [x] Swarm runner: verify scorecards auto open/close, tags propagate, and concurrent per-game agents replace serial loop; honor `--game` filters.
- [x] Replay_index flow: attempts.scorecard_id + replay_index populated; DB stores thin summaries only (no frame blobs); staged recordings deleted after ingestion; REPLAY_VALIDATION consumes replay_index (core_gameplay pointer path done). Runner batch flag added for replay validation batches (optional limit) plus missing coverage report.
- [x] Gap/Struggle guards: NO_DELTA and OSCILLATION_NO_CLOSURE emit COMPREHENSION_GAP_DETECTED and enqueue closure_probe intervention; closure_probe logged via CODS_OPERATOR_USED with validation_state from experiments.

## Phase 0: Migrations & Plumbing
- [x] Apply additive migrations for attempts, hook_failures, action_proposals_log, lesson_interpretations, source_attempt_id/source_mode tags. (Applied; hook_failures populated via spine.)
- [x] Add CHECK/ENUM constraints where safe (mode in {LIVE, REPLAY_VALIDATION, EVAL}; booleans as {0,1}; status fields constrained to allowed sets). (Implemented via triggers in migrations/add_check_triggers.py.)
- [x] Enforce PRAGMA foreign_keys=ON in connections.
- [x] Update DB interfaces to require mode + provenance on writes in LIVE; allow NULL for legacy reads.
- [x] Add indices for hot paths: winning_sequences/winning_sequences_full_game (game_id, level_number, is_active), sequence_validation_attempts (sequence_id, agent_id), attempts (mode, role, game_id, level), action_proposals_log (attempt_id, step_idx), lesson_interpretations (game_id, level).
- [x] Add metacog schema: hypotheses (theory, assumptions, supporting/contradicting evidence, confidence), experiments (prediction, action, expected vs actual, interpretation), elimination tracker, theory_versions, and concept_library entries with peer review status; keep additive and nullable for legacy.
- [x] Add observer tables/views: agent biographies (timeline, mental model snapshots, WA/WB adoption/rejection), struggle indicators, competence metrics, peer-teaching graph, gap_registry, interventions, and code_proposals with branch/PR metadata.
- [x] Enforce pycache off globally: set PYTHONDONTWRITEBYTECODE=1 (or python -B) in run_evolution/autonomous_evolution_runner and test runners; guard now fails run on __pycache__ detection at startup.
- [x] Coordinate retention: align database_logger cleanup with safe_cleanup and set retention knobs for large JSON tables (proposals, frames) to stay under 10 GB. (database_logger now enforces 5k log retention with PRAGMA guards; safe_cleanup still handles bulk tables.)
- [x] Testing: smoke import tests for migrated interfaces; DB migration validation queries; ensure env flag is honored. (Manual validator added at manual_tools/db_validation.py.)

### Legacy data preservation (sequences/agents/pariahs/viral packages)
- Snapshot legacy rows before enforcing new constraints: dump winning_sequences, winning_sequences_full_game, agents, pariahs, viral_packages with created_at/source hints.
- Backfill provenance: set source_mode='LEGACY' and source_attempt_id=NULL for legacy rows; do not overwrite content. For artifacts with natural keys (game_id, level_number, is_active), preserve current active flags and add a legacy_provenance flag.
- Create compatibility views that UNION legacy rows with new schema columns (defaulted) so readers do not drop historical wins/viral packages. Ensure pariahs remain excluded by default filters but stay queryable.
- Add migration script to create placeholder attempts for legacy artifacts when needed (attempt_id=synthetic UUID, mode='LEGACY', role='unknown') so foreign keys resolve without mutating payloads.
- Ensure safe_cleanup excludes legacy wins/viral packages/pariahs; cleanup may trim large blobs but must retain lineage columns.
- During rollout, run dual-path reads (legacy + new) and compare counts; only enable write-enforcement after parity confirmed.

### Database changes for swarm/replays
- New table replay_index: attempt_id, scorecard_id, replay_id, arc_game_id, agent_type, tags, local_recording_path (optional, transient), created_at. Index on (attempt_id), (scorecard_id), (replay_id, arc_game_id).
- attempts: add scorecard_id, swarm_tag, recording_pointer (nullable) for linking ARC assets to runs; default NULL for legacy.
- action_proposals_log / experiments: no frame blobs; keep thin summaries (actions, deltas, contradictions) and attention_window references only.
- retention: configure ingestion to drop staged recording files post-summary to honor no-log-files rule; rely on replay_index pointers for audit/regression.

## Phase 1: Instrumentation (No Logic Change)
- [x] Add Games-as-Teachers prompts: enforce “teacher showing?”, “what changed?”, “what to manipulate?”, “does interpretation explain all examples?” every N steps; log contradictions in reasoning_tags.
- [x] Preserve dynamic ATP reweighting: ensure adaptive_action_limits + agent_operating_mode_system role/w_B growth bonuses/penalties remain behavior-parity before moving to plugins.
- [x] Add theory-action gap detector: record stated hypothesis vs chosen action; flag circular probes, assumption drift, premature convergence; emit guard/contradiction tags without blocking.
- [x] Instrument assumption tracker, prediction-before-action, theory revision trigger, elimination tracker, and cross-attempt failure pattern tagging (hangups + failed hypotheses).
- [x] Instrument agent biography fields: learning history timeline, active hypotheses, revisions, struggles, WA/WB adoption/rejection, blind-spot and stuck-pattern tags. (Initial spine snapshot with metacog summary + wA/wB at attempt end.)
- [x] Instrument competence metrics: prediction accuracy, theory coherence, transfer success, explanation quality (peer adoption), metacognitive calibration, recovery rate; store per-attempt/per-agent rollups. (Seeded via competence_snapshot resonance tag.)
- [x] Instrument gap detection signals (performance/comprehension/metacog/architectural/pedagogical) and peer-teaching edges (who learned from whom, with outcome). (Gap resonance tags + peer_teaching edge spine log.)
- [x] Testing: add cases for MODE_WRITE_BLOCKED, ROLE_VIOLATION, BUDGET_EXHAUSTED, HEARTBEAT_LOST; ensure attempts rows reflect guard outcomes; verify no new pycache.

## Phase 2: Plugins (Extraction of Side-Effects)
- [x] Scaffold emit-only plugin set (lesson extraction stub, priors tracker, resonance/meta-operator telemetry, budget/pacing telemetry) with opt-in flag and HOOK_FAILURE probe wiring.
- [x] Wire DB-backed telemetry paths for lesson interpretations, priors/resonance traces, and budget pacing while keeping plugins mode-aware and emit-only.
- [x] Add Lesson Extraction/Contradiction plugin: mid-run lesson extraction on repeated patterns; triggers when contradictions persist; records misunderstandings and updates lesson_interpretations.
- [x] Add Attention/Priors plugin: apply weak priors (change/motion/novelty/solidity/continuity/social cues) as soft weights in proposals; log when evidence contradicts priors.
- [x] Add Resonance/Meta-Operator plugin: detect cross-game/operator/lesson resonance, compute w_R contributions, and register meta_operators (operator factories, discovery strategies) with provenance.
- [x] Add Budget/Pacing plugin (wrap existing adaptive_action_limits): keep role multipliers, w_B growth bonuses, low-start boosts, stagnation penalties; expose telemetry to attempts.
- Core orchestrator becomes emit-only; plugins are idempotent, mode-aware, and HOOK_FAILURE_DETECTED-wrapped.
- Testing: plugin failure injection to ensure HOOK_FAILURE_DETECTED rows; parity checks on sequences/operators vs baseline; check auto-disable behavior; confirm pycache guard still passing.

## Phase 3: Observer Dashboards & Gap System
- Read-only observer dashboard (manual_tools/observer_dashboard.py) now covers: biographies (WA/WB adoption), struggles, competence (distribution + generation trends), peer teaching, gaps/interventions (recent + severity + by-concept), stuck-game interventions, concept library, theory versions (timelines + contradictions + trends), agent theories (contradictions), agent hypotheses, assumptions, knowledge graph edges, population health, success insights, failure patterns, metacognitive insights, predictions, and eliminations. Phase 3 dashboard to-dos are complete (read-only; no writes).
- Build agent deep-dive views: learning history timeline, theory evolution, struggle indicators, active hypotheses with evidence, WA/WB adoption/rejection, assumption inventory, metacog self-assessment.
- Build competence/struggle analytics: prediction accuracy, coherence score, transfer rate, explanation quality, metacog calibration, recovery rate; stuck-pattern and blind-spot detection surfacing.
- Build network-wide views: generation competence distribution, collective knowledge map, peer teaching network, consensus vs accuracy, knowledge gaps by concept, diversity/stagnation detection.
- Build gap registry: detection → diagnosis (root cause, severity, type) → remediation plan (intervention type, resource estimate, success criteria, rollback conditions); link to interventions executed.
- Testing: dashboard queries return with mode/role filters; ensure no learning writes in read paths; validate severity/diagnosis classifications reproducible.

## Phase 4: Action Source Ladder & Combiner
- [x] Implement deterministic ladder Sequence → CODS → Heuristic/Escape → Noop with skip reasons logged; all `_select_action` exits funnel through `_finalize_ladder_and_return`, including ACTION6→movement downgrades.
- [x] Proposal combiner logs w_A/w_B, evidence, mode/role guards; chosen action recorded in action_proposals_log with ladder_trace.
- [x] Testing: ladder coverage tests; confirm ACTION_SOURCE_EMPTY when exhausted; compare chosen actions to baseline on replay fixtures; spot-check ladder_trace for ACTION6 fallbacks (test_action_ladder).

## Phase 5: Replay Validation Harness
- [x] Use recorded attempts to replay in REPLAY_VALIDATION; compare proposal traces and outcomes for regression.
- [x] Add health dashboards over attempts + hook_failures + guard codes (manual_tools/replay_health_dashboard.py).
- [x] Validate lesson+operator transfer and priors/resonance: replay teacher lessons with operator vocabulary; ensure weak priors can be overturned; track resonance_tags and guard incidence.
- [x] Testing: CI replay drift gate
	- Command: `python -B -m pytest -q -s tests/test_replay_validation.py`
	- Env: `PYTHONDONTWRITEBYTECODE=1`; no ARC_API_KEY; plugins optional (`ENABLE_OBSERVABILITY_PLUGINS=0` by default)
	- Pass criteria:
		- No replay validation errors
		- attempts rows exist for all replays; hook_failures only for expected replay validation checks; no MODE_WRITE_BLOCKED in replay runs
		- Drift thresholds: per-action frequency delta ≤5% vs baseline; guard incidence delta ≤2 absolute counts
		- __pycache__ check: fail if any __pycache__ remains after run
	- Artifacts: DB-only (replay_index pointers); no log files
- [x] Evaluate metacog/observer KPIs via dashboards (replay health and reviewer dashboards cover guards/attempts/sequence recency).

## Phase 6: Tests & Harden
- [x] Update tests to cover: guard codes, mode hygiene, action ladder, end-sequence win invariant, provenance on writes.
- [x] Add frame sanity checks; abort on FRAME_SANITY_FAIL.
- [x] Add audits for AGI-unified-theory invariants: dual economies separation (prestige vs actions), database-as-organism provenance fields present, viral spread tracked via source_attempt_id/source_mode, and decay/cleanup active.
- [x] Add assertions for Two-Streams (w_A/w_B/w_R persisted), resonance tagging, prior override behavior, and meta-operator logging.
- [x] Add dashboards and comparative analysis: theory evolution timelines, assumption audit trails, and Agent A vs B comparative traces for decisions and outcomes (manual_tools/reviewer_dashboard.py covers guard/hook/sequence recency slices).
- [x] Add ambiguity handlers: allow multiple concurrent interpretations, track consensus vs dissent, and resolve with evidence-driven contradiction counts (captured via resonance_tags and ladder traces, monitored in dashboards).
- [x] Noise/quality controls: explanation quality ranking, concept consolidation/merge rules, and curriculum progression checks to prevent network noise (observability-only, no new writes).
- [x] Reviewer dashboards: real-time health and recent activity (reviewer dashboard), historical evolution snapshots, and deep-dive triggers.
- [x] Git automation safeguards: branch naming/ownership rules, change-rate limiting, canaries vs baseline cohorts, comparative analysis, audit trail of proposed/merged/rolled-back changes (documented; guardrails active in conftest and pycache enforcement).
- [x] Testing: expand unit/integration suites; enforce python -B in test runner; add lint to fail if __pycache__ is present post-run.
- [x] Testing: enforce PYTHONDONTWRITEBYTECODE and fail tests if __pycache__ remains (pytest hook added).

### Ambiguity/Noise Controls (implementation outline)
- Run ambiguity handling in observability-only paths: for each decision, store parallel interpretations and consensus/dissent counts; surface contradiction deltas in dashboards. No new writes in control path; use existing resonance_tags and ladder traces for signals.
- Quality/noise filters: rank explanations by adoption + coherence; merge/retire duplicate concepts; enforce curriculum progression checks to curb noisy hypotheses. Keep DB-only telemetry; no file logs.
- Consensus vs accuracy: track agreement vs outcomes; flag high-consensus/low-accuracy cases for reviewer dashboard.

### Git Safeguards (implementation outline)
- Enforce PYTHONDONTWRITEBYTECODE and pycache cleanup (already in conftest); keep python -B in runners.
- Honor branch ownership rules: system-managed feature branches only; preserve human/manual branches; production branch Ouroboros-v2. Add lightweight audit log for proposed/merged/rolled-back changes (DB-only, no files).
- Change-rate limiting and canaries: prefer cohort comparisons before full rollout; add optional env knobs for rate caps.
- Comparative analysis: use replay validation and dashboards to compare baseline vs change cohorts; block deploy if guard/attempt drift exceeds thresholds.

## Phase 7: Deprecate Legacy Paths
- [x] Remove inline learning writes in core_gameplay/action_handler.
	- [x] Gate replay_index/world_model/wA-wB/viral evolution writes to LIVE mode only.
	- [x] Gate sequence capture (winning_sequences, inferred_beliefs), sequence validation/reputation, metacog/knowledge_synthesis/science_engine side-effects to LIVE mode only.
- [x] Mark legacy migrations deprecated; regenerate complete_database_schema.sql.
- [x] Remove residual log-file writes (database_logger to DB-only).
- [x] Testing: final replay/CI gate on attempts/action_proposals_log parity; filesystem check ensures no __pycache__ remains.

## Post-Phase: Live Testing
- Defer all LIVE ARC runs until after Phase 7 deliverables are merged and pycache checks pass.
- When ready, run a short LIVE sanity (ARC_API_KEY set; pointers only, no frame files):
	- `python -B run_evolution.py --max-generations 1 --mode LIVE --game-limit 1` (or equivalent flag set)
	- Ensure stage_recordings off unless summaries are ingested then deleted; rely on replay_index pointers.
	- Verify attempts/replay_index rows exist for the run; no __pycache__ created; no log files.
- After the live sanity, rerun replay validation and db validation to confirm no drift.

### LIVE sanity run plan (pointer-only, no frames)
- Env: set `PYTHONDONTWRITEBYTECODE=1`, `ARC_API_KEY` (live key), `STAGE_RECORDINGS=0`, `ENABLE_OBSERVABILITY_PLUGINS=0` (optional), `DATABASE_PATH` if non-default.
- Command: `python -B run_evolution.py --max-generations 1 --mode LIVE --game-limit 1 --game <TARGET>`; keep budgets minimal (defaults ok for single game).
- Expectations: attempts + replay_index rows created with scorecard_id tags; no __pycache__; no log files; hook_failures only for expected guards; no MODE_WRITE_BLOCKED.
- Post-run checks: (1) run `python -B -m pytest -q -s tests/test_replay_validation.py` (baseline pointers only; drift test will skip without env); (2) run `python -B manual_tools/replay_health_dashboard.py`; (3) run `python -B manual_tools/reviewer_dashboard.py`; (4) optional `python -B manual_tools/db_validation.py`.
- Cleanup: ensure staged recordings are absent; database size within limits; if any __pycache__ appears, delete and rerun.
