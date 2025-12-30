# Code Disposition Map (Root + manual_tools)

Legend: Keep (no functional change; wire to events/guards), Refactor (move side-effects to plugins; add guards/provenance), Consolidate (merge/rehome), Retire (remove/replace), Migrate (schema scripts).

## manual_tools
- check_cods_status.py — Refactor to consume CODS telemetry (attempts, action_proposals_log); drop ad-hoc queries.
- check_primitives.py — Refactor; read provenance-tagged attempts; honor guard states.
- analysis/theory_verification.py — Refactor; use lesson_interpretations and hypothesis reliability; no direct writes.
- analysis/theory_analysis.py — Refactor; derive from attempts/hypotheses views; mode filters.
- analysis/pariah_analysis.py — Refactor; use guard codes + source_mode.
- analysis/network_health_report.py — Refactor; hook_failures + guard codes + heartbeat gaps.
- analysis/gameplay_analyzer.py — Refactor; attempts/action_proposals_log; mode filters.
- analysis/audit_prestige_system.py — Refactor; enforce prestige vs budgets separation; read attempts.
- utilities/test_pariah_decay.py — Keep; add provenance awareness; ensure PYTHONDONTWRITEBYTECODE.
- utilities/remove_emojis.py — Keep utility.
- utilities/get_replay_url.py — Keep; use attempt_id for reproducible replay.
- monitoring/review_scorecards.py — Refactor; pull from attempts + lesson_interpretations.
- monitoring/system_status_report.py — Refactor; hook_failures + guard codes + heartbeats.
- database/inspect_db.py — Keep read-only; include new tables.
- database/schema_inspector.py — Keep; include new tables/columns.

## Root gameplay/orchestration
- core_gameplay.py — Refactor: split INIT/STEP/POST_STEP/FINALIZE; emit events; guards; attempts + proposal logging; side-effects to plugins.
- action_handler.py — Refactor: pure execution; emit ACTION_EXECUTED; no learning writes.
- game_session_manager.py — Refactor: thin orchestrator; emit RUN_INIT/RUN_FINALIZED; owns RunContext.
- run_evolution.py — Keep orchestration; use modes; create attempts.
- evolutionary_engine.py — Refactor to attempts spine; no inline DB writes.
- evolution_game_scheduler.py, game_scheduler.py, ouroboros_coordinator.py, specialist_coordinator.py — Refactor for roles/modes; emit role assignments; no learning writes.
- agent_factory.py, agent_lifecycle_manager.py, agent_operating_mode_system.py, adaptive_action_limits.py — Refactor to set budgets/roles in RunContext; emit guard codes; log to attempts.
- agent_self_model.py — Refactor as plugin; consumes FRAME_CHANGED; writes only in LIVE with provenance.
- sensation_engine.py, object_detector.py, visual_reasoning_engine.py, visual_analyzer.py, terminal_pattern_detector.py — Refactor into sensing plugins; no direct DB writes; provenance on outputs.
- emotional_gameplay_mixin.py — Refactor/fold into sensation plugin; remove silent catches.
- subgoal_planner.py, subgoal_planning_activator.py — Refactor as proposal sources; emit proposals with w_A/w_B; no side-effects.

## Sequences/knowledge/CODS
- sequence_miner.py, sequence_abstraction.py, sequence_pruning_system.py — Refactor to plugins; write with source_attempt_id/source_mode; enforce end-sequence win.
- oracle_interface.py, horizontal_transfer_engine.py, viral_package_engine.py, multi_stage_matching_pipeline.py — Refactor to event-driven plugins; mode-guarded writes with provenance.
- cods_engine.py, arc_rlvr_framework.py, operator_composer.py, rule_induction_engine.py, concept_discovery_engine.py, symbolic_reasoning_engine.py, primitive_unlock_manager.py, seed_primitives.py — Refactor as proposal/validator plugins; log operator usage to attempts/action_proposals_log; writes only in LIVE.
- audit_cods.py, scientific_method_engine.py — Refactor to standardized telemetry/lesson_interpretations.
- near_miss_analyzer.py, counterfactual_analyzer.py — Refactor as analytical plugins consuming attempts; provenance outputs.

## Prestige/budgets/roles/health
- prestige_engine.py, prestige_vampire_detector.py, breakthrough_budget_allocator.py, optimization_threshold_system.py — Refactor into Prestige/Budget plugin; enforce dual-economy separation; writes via attempts.
- game_diversity_preservation.py, metric_rotator.py, metric_confidence.py, performance_analyzer.py — Refactor as health/rotation plugins; read attempts; no inline writes.
- oracle_health_monitor.py, autopoiesis_monitor.py, frustration_detector.py, pariah_validator.py, resonance_detector.py, terminal_pattern_detector.py — Refactor as monitoring plugins; emit HOOK_FAILURE_DETECTED; support auto-disable.

## API/IO/DB
- arc_api_client.py, api_reset_strategy.py — Keep; wrap retries; log request/response in ACTION_EXECUTED payloads.
- database_interface.py, enhanced_database_interface.py, database_logger.py — Refactor to enforce mode guard + provenance; expose writes for new tables; no log files.
- disk_space_monitor.py, safe_cleanup.py, cleanup_temp_files.py, schema_auto_maintenance.py — Keep; add awareness of new tables; ensure PYTHONDONTWRITEBYTECODE.
- complete_database_schema.sql — Update only after additive migrations.

## Scheduling/coordination
- trigger_controller.py, evolution_with_vampires.py, ouroboros_coordinator.py — Refactor to event-driven triggers; avoid inline side-effects.

## Knowledge synthesis/diagnostics
- network_knowledge_synthesis.py, network_intelligence_engine.py, oracle_stuck_game_diagnostics.py — Refactor to consume attempts and guard codes; advisory only; writes with provenance in LIVE.

## Migrations/tests/other
- migrations/*.py — Migrate to additive scripts (attempts, hook_failures, action_proposals_log, lesson_interpretations, provenance tags); keep legacy scripts as history (deprecated).
- tests/* — Update to exercise attempts spine, guard codes, mode hygiene, proposal logging; remove reliance on inline side-effects.
- abstraction_config.py, abstraction_schema.py — Keep; access via plugins/events.
- console_metrics_capture.py, console_tags.py — Refactor to consume events; no inline logging.
- automated_assessment_runner.py — Refactor to run in REPLAY_VALIDATION/EVAL using attempts replay.
