# Sequenced Refactor Plan

Phased execution to reach the event-first, guard-heavy runtime with provenance. Behavior parity first, then extraction. Testing and pycache hygiene are first-class: use python -B or PYTHONDONTWRITEBYTECODE=1 at all entry points, and run regression suites per phase.

## Immediate wiring (no code refactor yet, required for build readiness)
- Add closure_probe CODS operator and log CODS_OPERATOR_USED with validation_state from experiments; enqueue closure_probe when oscillation_no_closure is raised.
- StruggleGuard: emit oscillation_no_closure after >=4 offset sweeps without state change and no_delta after >=5 unchanged frames; both emit COMPREHENSION_GAP_DETECTED.
- TheoryActionGuard/Action logging: persist role_compliance and theory_validation_state on every action_proposals_log row; fail fast in LIVE if missing.
- GapRegistry consumer: on COMPREHENSION_GAP_DETECTED create gap_registry row and enqueue interventions (peer_fetch, operator_change→closure_probe); track outcomes in interventions table.

## ARC API alignment (actions, scorecards, swarm, recordings)
- Enforce Action 6 protocol: always send x,y (0-63), prefer ACTION1-5/7 first, and justify ACTION6 coordinates from frame salience (rare color, contrast, shape). Add guard to block raw ACTION6 without coords; add Action6Reasoner hook to pick coords from attention_windows salience (aligns with actions.md and arc_api_actions_rules).
- Scorecards: always open/close per run; propagate tags from evolution scheduler into scorecard to mirror attempts.mode/role/game_id; record scorecard_id in attempts and replay_index.
- Swarm orchestration: default runner becomes swarm-style (one agent per game concurrently, auto scorecard/replay links, tag propagation). Allow game filters and tags passthrough. Frontier/optimizer/exploiter assignments map to swarm slots instead of bespoke loops.
- Recordings/replays: rely on ARC-provided replays; store pointers (scorecard_id, replay_id, local recording filename if staged) instead of frames. In LIVE, optionally stage JSONL to temp, ingest summaries (actions/deltas/contradictions), then delete file. In REPLAY_VALIDATION, pull from replay_index instead of regenerating actions.

## Swarm orchestration and replay usage (space-saving and parity)
- Replace per-game serial execution with swarm-style orchestration: one agent instance per game, concurrent threads, automatic scorecard open/close, and tag capture (from ARC swarms.md). Integrate into evolution scheduler so frontier/optimizer/exploiter assignments map to swarm slots instead of bespoke loops.
- Stop persisting raw frame blobs in DB when ARC already records runs: store replay/recording pointers (scorecard_id, replay_id, local recording filename if enabled) in a new replay_index table; persist step-level telemetry only when needed for learning (actions, deltas, contradictions), not full frames.
- In LIVE mode, optionally mirror ARC JSONL recordings to a staging directory, then ingest summaries (actions, deltas, contradictions) into DB and delete raw file to honor “no log files” rule; keep replay links for audit instead of heavy blobs.
- When running in REPLAY_VALIDATION, prefer pulling frames from replay_index (ARC replay link) instead of regenerating actions; compare predicted vs recorded outcomes to detect drift.
- Scheduler change: allow `--game` filters and tag propagation so ARC scorecards/tags mirror our attempt_id/mode/role; store tags in attempts for cross-system traceability.

## Phase 0: Migrations & Plumbing
- Apply additive migrations for attempts, hook_failures, action_proposals_log, lesson_interpretations, source_attempt_id/source_mode tags.
- Add CHECK/ENUM constraints where safe (mode in {LIVE, REPLAY_VALIDATION, EVAL}; booleans as {0,1}; status fields constrained to allowed sets) and enforce PRAGMA foreign_keys=ON in connections.
- Update DB interfaces to require mode + provenance on writes in LIVE; allow NULL for legacy reads.
- Add indices for hot paths: winning_sequences/winning_sequences_full_game (game_id, level_number, is_active), sequence_validation_attempts (sequence_id, agent_id), attempts (mode, role, game_id, level), action_proposals_log (attempt_id, step_idx), lesson_interpretations (game_id, level).
- Add metacog schema: hypotheses (theory, assumptions, supporting/contradicting evidence, confidence), experiments (prediction, action, expected vs actual, interpretation), elimination tracker, theory_versions, and concept_library entries with peer review status; keep additive and nullable for legacy.
- Add observer tables/views: agent biographies (timeline, mental model snapshots, WA/WB adoption/rejection), struggle indicators, competence metrics, peer-teaching graph, gap_registry, interventions, and code_proposals with branch/PR metadata.
- Enforce pycache off globally: set PYTHONDONTWRITEBYTECODE=1 (or python -B) in run_evolution/autonomous_evolution_runner and test runners; add a guard that fails if __pycache__ exists after startup.
- Coordinate retention: align database_logger cleanup with safe_cleanup and set retention knobs for large JSON tables (proposals, frames) to stay under 10 GB.
- Testing: smoke import tests for migrated interfaces; DB migration validation queries; ensure env flag is honored.

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
- Add Games-as-Teachers prompts: enforce “teacher showing?”, “what changed?”, “what to manipulate?”, “does interpretation explain all examples?” every N steps; log contradictions in reasoning_tags.
- Preserve dynamic ATP reweighting: ensure adaptive_action_limits + agent_operating_mode_system role/w_B growth bonuses/penalties remain behavior-parity before moving to plugins.
- Add theory-action gap detector: record stated hypothesis vs chosen action; flag circular probes, assumption drift, premature convergence; emit guard/contradiction tags without blocking.
- Instrument assumption tracker, prediction-before-action, theory revision trigger, elimination tracker, and cross-attempt failure pattern tagging (hangups + failed hypotheses).
- Instrument agent biography fields: learning history timeline, active hypotheses, revisions, struggles, WA/WB adoption/rejection, blind-spot and stuck-pattern tags.
- Instrument competence metrics: prediction accuracy, theory coherence, transfer success, explanation quality (peer adoption), metacognitive calibration, recovery rate; store per-attempt/per-agent rollups.
- Instrument gap detection signals (performance/comprehension/metacog/architectural/pedagogical) and peer-teaching edges (who learned from whom, with outcome).
- Testing: add cases for MODE_WRITE_BLOCKED, ROLE_VIOLATION, BUDGET_EXHAUSTED, HEARTBEAT_LOST; ensure attempts rows reflect guard outcomes; verify no new pycache.

## Phase 2: Plugins (Extraction of Side-Effects)
- Add Lesson Extraction/Contradiction plugin: mid-run lesson extraction on repeated patterns; triggers when contradictions persist; records misunderstandings and updates lesson_interpretations.
- Add Attention/Priors plugin: apply weak priors (change/motion/novelty/solidity/continuity/social cues) as soft weights in proposals; log when evidence contradicts priors.
- Add Resonance/Meta-Operator plugin: detect cross-game/operator/lesson resonance, compute w_R contributions, and register meta_operators (operator factories, discovery strategies) with provenance.
- Add Budget/Pacing plugin (wrap existing adaptive_action_limits): keep role multipliers, w_B growth bonuses, low-start boosts, stagnation penalties; expose telemetry to attempts.
- Core orchestrator becomes emit-only; plugins are idempotent, mode-aware, and HOOK_FAILURE_DETECTED-wrapped.
- Testing: plugin failure injection to ensure HOOK_FAILURE_DETECTED rows; parity checks on sequences/operators vs baseline; check auto-disable behavior; confirm pycache guard still passing.

## Phase 3: Observer Dashboards & Gap System
- Build agent deep-dive views: learning history timeline, theory evolution, struggle indicators, active hypotheses with evidence, WA/WB adoption/rejection, assumption inventory, metacog self-assessment.
- Build competence/struggle analytics: prediction accuracy, coherence score, transfer rate, explanation quality, metacog calibration, recovery rate; stuck-pattern and blind-spot detection surfacing.
- Build network-wide views: generation competence distribution, collective knowledge map, peer teaching network, consensus vs accuracy, knowledge gaps by concept, diversity/stagnation detection.
- Build gap registry: detection → diagnosis (root cause, severity, type) → remediation plan (intervention type, resource estimate, success criteria, rollback conditions); link to interventions executed.
- Testing: dashboard queries return with mode/role filters; ensure no learning writes in read paths; validate severity/diagnosis classifications reproducible.

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
- Evaluate metacog KPIs: transfer success, explanation quality/peer adoption, theory coherence, prediction accuracy, metacognitive calibration, concept extraction coverage, theory revision rate, assumption counts, and teaching-effectiveness lift.
- Evaluate observer KPIs: biography completeness, struggle indicator coverage, peer-teaching impact, consensus vs accuracy alignment, stagnation and diversity metrics, gap detection precision/recall, intervention success/rollback rates.

## Phase 6: Tests & Harden
- Update tests to cover: guard codes, mode hygiene, action ladder, end-sequence win invariant, provenance on writes.
- Add frame sanity checks; abort on FRAME_SANITY_FAIL.
- Add audits for AGI-unified-theory invariants: dual economies separation (prestige vs actions), database-as-organism provenance fields present, viral spread tracked via source_attempt_id/source_mode, and decay/cleanup active.
- Add assertions for Two-Streams (w_A/w_B/w_R persisted), resonance tagging, prior override behavior, and meta-operator logging.
- Add dashboards and comparative analysis: theory evolution timelines, assumption audit trails, and Agent A vs B comparative traces for decisions and outcomes.
- Add ambiguity handlers: allow multiple concurrent interpretations, track consensus vs dissent, and resolve with evidence-driven contradiction counts.
- Noise/quality controls: explanation quality ranking, concept consolidation/merge rules, and curriculum progression checks to prevent network noise.
- Reviewer dashboards: real-time health (current learning activity, active gaps, recent interventions, learning velocity, stability), historical evolution (competence over time, gap resolution timeline, code evolution history, success/failure patterns), and deep-dive triggers (anomalies, stagnation, runaway changes, critical gaps, breakthroughs).
- Git automation safeguards: branch naming/ownership rules (system-managed feature branches; leave human/manual branches untouched; production is Ouroboros-v2), change-rate limiting, canaries vs baseline cohorts, comparative analysis, audit trail of proposed/merged/rolled-back changes.
- Testing: expand unit/integration suites; enforce python -B in test runner; add lint to fail if __pycache__ is present post-run.

## Phase 7: Deprecate Legacy Paths
- Remove inline learning writes in core_gameplay/action_handler.
- Mark legacy migrations deprecated; regenerate complete_database_schema.sql.
- Remove residual log-file writes (database_logger to DB-only).
- Testing: final replay/CI gate on attempts/action_proposals_log parity; filesystem check ensures no __pycache__ remains.
