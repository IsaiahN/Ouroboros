# Traceability to Codebase and Architect Mindset

Linking the refactor plan to concrete modules so every concept has an owner. This is a map, not a refactor diff; behavior parity remains the first execution milestone.

## Architecture Style
- Event-first, plugin-driven core within a single-process runtime; SQLite as the source of truth; ARC API and frame recovery preserved.
- Modes (LIVE/REPLAY_VALIDATION/EVAL) and roles enforced at guards; side-effects leave core into plugins.

## Codebase Surface Map (responsibilities)
- Gameplay orchestration: [core_gameplay.py](core_gameplay.py), [action_handler.py](action_handler.py), [arc_api_client.py](arc_api_client.py), [game_session_manager.py](game_session_manager.py), [evolutionary_engine.py](evolutionary_engine.py), [evolution_game_scheduler.py](evolution_game_scheduler.py).
- Sequences and knowledge: [sequence_miner.py](sequence_miner.py), [sequence_abstraction.py](sequence_abstraction.py), [sequence_pruning_system.py](sequence_pruning_system.py), [oracle_interface.py](oracle_interface.py), [horizontal_transfer_engine.py](horizontal_transfer_engine.py), [viral_package_engine.py](viral_package_engine.py), [complete_database_schema.sql](complete_database_schema.sql).
- CODS and operators: [cods_engine.py](cods_engine.py), [arc_rlvr_framework.py](arc_rlvr_framework.py), [operator_composer.py](operator_composer.py), [symbolic_reasoning_engine.py](symbolic_reasoning_engine.py), [rule_induction_engine.py](rule_induction_engine.py), [concept_discovery_engine.py](concept_discovery_engine.py), [primitive_unlock_manager.py](primitive_unlock_manager.py).
- Roles, budgets, prestige: [agent_factory.py](agent_factory.py), [agent_lifecycle_manager.py](agent_lifecycle_manager.py), [agent_operating_mode_system.py](agent_operating_mode_system.py), [adaptive_action_limits.py](adaptive_action_limits.py), [prestige_engine.py](prestige_engine.py), [prestige_vampire_detector.py](prestige_vampire_detector.py), [breakthrough_budget_allocator.py](breakthrough_budget_allocator.py).
- Sensation, self-model, perception: [sensation_engine.py](sensation_engine.py), [agent_self_model.py](agent_self_model.py), [object_detector.py](object_detector.py), [visual_reasoning_engine.py](visual_reasoning_engine.py), [visual_analyzer.py](visual_analyzer.py), [terminal_pattern_detector.py](terminal_pattern_detector.py).
- Evolution meta-control and health: [oracle_health_monitor.py](oracle_health_monitor.py), [autopoiesis_monitor.py](autopoiesis_monitor.py), [performance_analyzer.py](performance_analyzer.py), [manual_tools/gameplay_analyzer.py](manual_tools/gameplay_analyzer.py), [frustration_detector.py](frustration_detector.py), [near_miss_analyzer.py](near_miss_analyzer.py), [breakthrough_detector.py](breakthrough_detector.py), [trigger_controller.py](trigger_controller.py).
- Reliability and cleanup: [safe_cleanup.py](safe_cleanup.py), [cleanup_temp_files.py](cleanup_temp_files.py), [disk_space_monitor.py](disk_space_monitor.py), [database_logger.py](database_logger.py), [database_interface.py](database_interface.py), [enhanced_database_interface.py](enhanced_database_interface.py), [schema_auto_maintenance.py](schema_auto_maintenance.py).
- Scheduling and coordination: [game_scheduler.py](game_scheduler.py), [ouroboros_coordinator.py](ouroboros_coordinator.py), [specialist_coordinator.py](specialist_coordinator.py), [agent_lifecycle_manager.py](agent_lifecycle_manager.py).
- Reasoning and metacog: [collective_reasoning_engine.py](collective_reasoning_engine.py), [meta_learning_curriculum.py](meta_learning_curriculum.py), [near_miss_analyzer.py](near_miss_analyzer.py), [pariah_validator.py](pariah_validator.py), [resonance_detector.py](resonance_detector.py), [optimization_threshold_system.py](optimization_threshold_system.py), [metric_rotator.py](metric_rotator.py), [metric_confidence.py](metric_confidence.py).
- Docs and plans: [DOCS](DOCS), [architecture/overview.md](architecture/overview.md), [architecture/diagrams.md](architecture/diagrams.md), [architecture/runtime/README.md](architecture/runtime/README.md), [architecture/data-contracts/README.md](architecture/data-contracts/README.md), [architecture/reliability/README.md](architecture/reliability/README.md), [architecture/nfrs/README.md](architecture/nfrs/README.md).

## Mapping to Architect Questions
- Business/Functional: ARC 3 real-game wins; see gameplay and evolution orchestrators above; sequences/CODS/lessons deliver the “understanding” outcome.
- NFRs: captured in architecture/nfrs/README.md with guards, heartbeats, mode hygiene, invariants, and indices.
- Architecture style: event-first, pluginized core; monolith-with-bus (not microservices) for latency and simplicity; documented in architecture/runtime/README.md.
- Scalability/Performance: proposal pipeline O(#sources); DB indices defined; sequence reputation cached; bus is in-process.
- Security/Reliability: mode/role/budget guards; hook_failures; auto-disable; no log files; provenance tagging.
- API Contracts: ARC API untouched; internal contract is RunContext + events; see architecture/runtime/README.md and architecture/data-contracts/README.md.
- Deployment/Infra: SQLite + WAL; no pycache; safe_cleanup for hygiene; CI should run investigate_bugs.py and replay validation.
- Documentation: diagrams plus reliability/runtime/data-contracts/nfrs/traceability; add ADRs here as decisions solidify.
- Iteration: phased delivery in architecture/overview.md; replay validation for regressions; hook buckets drive fixes.

## Gaps to Close (actionable follow-ups)
- Define event payload schemas and guard failure codes (runtime) — added in architecture/runtime/events.md.
- Write migrations for additive tables and source tags (data-contracts) — added in architecture/data-contracts/migrations.md.
- Map each side-effect in play_single_game to a plugin with mode/role/budget guard placement (runtime + reliability) — added in architecture/runtime/side-effects-map.md.
- Add ADR entries for key decisions (bus vs. inline, mode hygiene rules, action source ladder) — added in architecture/traceability/adr-index.md.
