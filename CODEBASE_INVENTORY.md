# BitterTruth-AI Codebase Inventory

**Updated**: 2025-12-08  
**Architecture**: Autonomous ARC-AGI-3 game playing with evolutionary agents

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Folder Structure](#folder-structure)
3. [File Categories](#file-categories)
4. [Recently Implemented Features](#recently-implemented-features)
5. [Dependency Graph](#dependency-graph)
6. [Orphaned/Duplicate Functionality](#orphanedduplicate-functionality)
7. [Missing Components](#missing-components)
8. [Key Classes](#key-classes)
9. [Recommendations](#recommendations)

---

## Executive Summary

BitterTruth-AI is an **autonomous evolutionary system** for playing ARC-AGI-3 games. The codebase implements:

- **Biome Theory**: Database as the primary "organism" with agents as temporary cellular expressions
- **Three-Layer Architecture**: Genome (static) -> Epigenetic (adaptive) -> Somatic (learned)
- **Four Agent Roles**: Pioneer, Optimizer, Generalist, Exploiter
- **Two-Streams Consciousness**: Agents balance private memory vs network wisdom with explicit bias
- **Prestige Economy**: Social capital separate from action budgets
- **Viral Knowledge Transfer**: Horizontal gene transfer between unrelated agents
- **Network Failure Hypotheses**: Shared learning from failures across agents
- **Agent Self-Model**: "I am this object" comprehension with network sharing

### Core Entry Points
| File | Purpose |
|------|---------|
| `run_evolution.py` | Main entry point - starts evolution runner |
| `autonomous_evolution_runner.py` | Orchestrates continuous evolution cycles |
| `core_gameplay.py` | Game loop and decision-making engine |

---

## Folder Structure

```
BitterTruth-AI/
|-- *.py                    # Core Python files (root)
|-- tests/                  # Unit test files
|-- manual_tools/           # Debug/utility files (manual execution only)
|   |-- analysis/           # Data analysis and auditing
|   |-- database/           # Database inspection tools
|   |-- monitoring/         # System monitoring tools
|   +-- utilities/          # Misc utility scripts
|-- migrations/             # Database migration scripts (historical)
|   +-- completed/          # Completed migrations
|-- DOCS/                   # Documentation files
|-- .github/                # GitHub configuration
+-- complete_database_schema.sql  # Full schema reference
```

---

## File Categories

### 1. CORE GAMEPLAY
Files responsible for direct game interaction with ARC-AGI-3 API.

| File | Purpose | Status |
|------|---------|--------|
| `core_gameplay.py` | Main game loop, sequence matching, action selection, Two-Streams integration | Active |
| `action_handler.py` | Clean interface for sending ACTION1-7 to API | Active |
| `game_session_manager.py` | Session lifecycle, game creation, budget enforcement | Active |
| `arc_api_client.py` | Async HTTP client for ARC-AGI-3 API | Active |
| `visual_analyzer.py` | Frame analysis for ACTION6 coordinate selection | Active |
| `object_detector.py` | Detects objects/patterns in game frames | Active |
| `emotional_gameplay_mixin.py` | Mixin for sensation-based gameplay | Partial |

### 2. SEQUENCE SYSTEM
Files for capturing, storing, matching, and replaying winning sequences.

| File | Purpose | Status |
|------|---------|--------|
| `multi_stage_matching_pipeline.py` | 5-stage fallback matching (exact->prefix->suffix->subsequence->conceptual) | Active |
| `sequence_abstraction.py` | Concept-based sequence matching | Active |
| `sequence_pruning_system.py` | Removes stale/invalid sequences | Active |
| `abstraction_config.py` | Configuration for abstraction system | Active |
| `abstraction_schema.py` | Schema definitions for abstractions | Active |

### 3. AGENT SYSTEM
Files for agent creation, lifecycle, roles, and self-modeling.

| File | Purpose | Status |
|------|---------|--------|
| `agent_factory.py` | Creates specialized agents (5 types) | Active |
| `agent_lifecycle_manager.py` | Agent creation/retirement/revival | Active |
| `agent_operating_mode_system.py` | Dynamic role assignment (Pioneer/Optimizer/Generalist/Exploiter), meta-bias updates | Active |
| `agent_self_model.py` | "I am this object" comprehension, WeavingReporter, network control hypotheses | Active |
| `revive_agents.py` | Agent revival mechanism | Integrated (every 5 generations) |
| `adaptive_action_limits.py` | Performance-based action budget adjustment | Active |
| `somatic_profile_system.py` | Layer 3 somatic learning management | Partial |

### 4. EVOLUTION SYSTEM
Files for evolutionary algorithms, breeding, and selection.

| File | Purpose | Status |
|------|---------|--------|
| `autonomous_evolution_runner.py` | Main orchestrator for continuous evolution | Active |
| `evolutionary_engine.py` | Breeding, mutation, crossover, selection | Active |
| `evolution_with_vampires.py` | Vampire detection during evolution | Partial |
| `evolution_game_scheduler.py` | Schedules games during evolution | Active |
| `game_scheduler.py` | General game scheduling logic | Active |
| `run_evolution.py` | Entry point script | Active |
| `game_diversity_preservation.py` | Maintains game variety | Active |

### 5. LEARNING/KNOWLEDGE SYSTEM
Files for meta-learning, knowledge transfer, and abstract reasoning.

| File | Purpose | Status |
|------|---------|--------|
| `sensation_engine.py` | Emotional intelligence, semantic impressions, personal associations | Active |
| `rule_induction_engine.py` | Extract IF-THEN rules from wins | Partial |
| `meta_learning_curriculum.py` | Curriculum-based learning | Partial |
| `symbolic_reasoning_engine.py` | Abstract symbolic reasoning, WorldModel | Orphaned |
| `visual_reasoning_engine.py` | Visual pattern reasoning | Orphaned |
| `subgoal_planner.py` | Hierarchical multi-step planning | Active |
| `subgoal_planning_activator.py` | Activates subgoal planning | Active |
| `counterfactual_analyzer.py` | "What if" analysis | Active |
| `near_miss_analyzer.py` | Analyzes near-win situations | Active |
| `frustration_detector.py` | Detects stuck agents | Active |
| `collective_reasoning_engine.py` | Network-level reasoning | Partial |

### 6. PRESTIGE/VIRAL SYSTEM
Files for prestige economy and horizontal gene transfer.

| File | Purpose | Status |
|------|---------|--------|
| `prestige_engine.py` | Network contribution currency | Active |
| `prestige_vampire_detector.py` | Detects prestige exploitation | Active |
| `viral_package_engine.py` | Bidirectional evolution (viral packages + pariahs), role-based sequence reputation | Active |
| `horizontal_transfer_engine.py` | Direct knowledge transfer between agents | Partial |
| `knowledge_recombination_engine.py` | Sequence chaining and pattern synthesis | Partial |

### 7. NETWORK INTELLIGENCE
Files treating the database as the primary organism.

| File | Purpose | Status |
|------|---------|--------|
| `network_intelligence_engine.py` | Ecosystem health monitoring | Partial |
| `regulatory_signal_engine.py` | Quorum sensing / homeostasis | Partial |
| `ouroboros_coordinator.py` | High-level system coordination | Partial |

### 8. BREAKTHROUGH DETECTION
Files for detecting and rewarding breakthrough moments.

| File | Purpose | Status |
|------|---------|--------|
| `breakthrough_detector.py` | Detects significant improvements | Active |
| `breakthrough_budget_allocator.py` | Allocates extra budget for breakthroughs | Active |
| `optimization_threshold_system.py` | Detects optimization saturation | Partial |
| `arc_rlvr_framework.py` | Reinforcement learning framework | Partial |

### 9. DATABASE
Files for database operations and schema management.

| File | Purpose | Status |
|------|---------|--------|
| `database_interface.py` | Core SQLite operations | Active |
| `enhanced_database_interface.py` | Extended database operations | Active |
| `database_logger.py` | DatabaseLogHandler (no file logs per Rule 2) | Active |
| `schema_auto_maintenance.py` | Auto-updates schema | Manual |
| `complete_database_schema.sql` | Full schema reference | Reference |

### 10. CLEANUP UTILITIES

| File | Purpose | Location |
|------|---------|----------|
| `safe_cleanup.py` | Safe database cleanup (Rule 12) | Root |
| `cleanup_temp_files.py` | Cleans temporary files | Root |
| `disk_space_monitor.py` | Monitors disk usage | Root |

### 11. ANALYSIS/MONITORING

| File | Purpose | Location |
|------|---------|----------|
| `performance_analyzer.py` | Comprehensive population analysis | Root |
| `automated_assessment_runner.py` | Automated assessment | Root |

### 12. CONFIGURATION/INFRASTRUCTURE

| File | Purpose |
|------|---------|
| `__init__.py` | Package initialization |
| `api_reset_strategy.py` | API reset handling |
| `specialist_coordinator.py` | Specialist coordination (orphaned) |

---

## Recently Implemented Features

### Two-Streams Consciousness (Session: Dec 4, 2025)
Agents balance private memory (Stream A) vs network wisdom (Stream B):

| Feature | File | Method/Location |
|---------|------|-----------------|
| Self-network bias tracking | `agents` table | `self_network_bias` column |
| Role-specific sequence selection | `core_gameplay.py` | `_get_best_sequence_for_game()` |
| Sequence role reputation | `viral_package_engine.py` | `update_sequence_role_reputation()` |
| Semantic impressions | `sensation_engine.py` | `form_semantic_impression()`, `query_personal_impression()` |
| Meta-bias updates | `agent_operating_mode_system.py` | `update_meta_bias()` |
| Weaving reports | `agent_self_model.py` | `WeavingReporter` class |

### Network Failure Hypotheses (Session: Dec 4, 2025)
Shared learning from failures with action biases:

| Feature | File | Method/Location |
|---------|------|-----------------|
| Hypothesis generation | `core_gameplay.py` | `_generate_failure_hypothesis()` |
| Hypothesis query | `core_gameplay.py` | `_get_network_failure_hypotheses()` |
| Action bias application | `core_gameplay.py` | `_select_action()` (hypothesis_biases) |
| Database table | `network_failure_hypotheses` | Bayesian reliability scoring |

### Agent Self-Model / Network Control Sharing (Session: Dec 4, 2025)
"I am this object" comprehension shared to network:

| Feature | File | Method/Location |
|---------|------|-----------------|
| Control discovery sharing | `agent_self_model.py` | `share_control_discovery_to_network()` |
| Network hypothesis query | `agent_self_model.py` | `get_network_control_hypotheses()` |
| Hypothesis validation | `agent_self_model.py` | `validate_control_hypothesis()` |
| Database table | `network_object_control_hypotheses` | Bayesian reliability scoring |

---

## Manual Tools (`manual_tools/`)

Debug and utility files for manual execution only. Reorganized into subfolders:

```
manual_tools/
|-- analysis/           # Data analysis and auditing tools
|-- database/           # Database inspection and schema tools
|-- monitoring/         # System status and scorecard monitoring
|-- utilities/          # Replay URLs, emoji removal, tests
+-- README.md
```

### Analysis Tools (`analysis/`)
| File | Purpose | Usage |
|------|---------|-------|
| `gameplay_analyzer.py` | Gameplay progression analysis | `python manual_tools/analysis/gameplay_analyzer.py --hours 3` |
| `audit_prestige_system.py` | Audits prestige calculations | `python manual_tools/analysis/audit_prestige_system.py` |
| `pariah_analysis.py` | Analyzes pariah system state | `python manual_tools/analysis/pariah_analysis.py` |
| `theory_verification.py` | Verify AGI unified theory alignment | `python manual_tools/analysis/theory_verification.py` |
| `theory_analysis.py` | Comprehensive theory alignment analysis | `python manual_tools/analysis/theory_analysis.py` |

### Database Tools (`database/`)
| File | Purpose | Usage |
|------|---------|-------|
| `schema_inspector.py` | Database schema inspection | `python manual_tools/database/schema_inspector.py --table agents` |
| `inspect_db.py` | Detailed database inspection | `python manual_tools/database/inspect_db.py` |

### Monitoring Tools (`monitoring/`)
| File | Purpose | Usage |
|------|---------|-------|
| `system_status_report.py` | Generates status reports | `python manual_tools/monitoring/system_status_report.py` |
| `review_scorecards.py` | Reviews scorecard data | `python manual_tools/monitoring/review_scorecards.py` |

### Utility Tools (`utilities/`)
| File | Purpose | Usage |
|------|---------|-------|
| `get_replay_url.py` | Gets replay URLs for games | `python manual_tools/utilities/get_replay_url.py <game_id>` |
| `remove_emojis.py` | Removes Unicode emojis (Rule 11) | `python manual_tools/utilities/remove_emojis.py` |
| `test_pariah_decay.py` | Tests pariah decay system | `python manual_tools/utilities/test_pariah_decay.py` |

---

## Tests (`tests/`)

Unit test files (allowed per Rule 5 exception):

| File | Purpose |
|------|---------|
| `test_safe_cleanup.py` | Tests for SafeDatabaseCleaner |
| `test_critical_systems.py` | Tests for critical systems |
| `test_recent_changes.py` | Tests for recent changes |
| `test_sequence_system.py` | Tests for sequence system |
| `README.md` | Test documentation |
| `__init__.py` | Package initialization |

---

## Migrations (`migrations/completed/`)

Historical database migration scripts:

| File | Purpose |
|------|---------|
| `migrate_epigenetics.py` | Epigenetics migration |
| `backfill_viral_packages.py` | Viral packages backfill |
| `apply_high_priority_migrations.py` | Priority migrations |
| `add_level_tracking_to_traces.py` | Level tracking migration |
| `add_performance_method.py` | Performance method addition |
| `add_performance_tracking.py` | Performance tracking |
| `add_scorecard_columns.py` | Scorecard columns |
| `add_self_awareness.py` | Self-awareness features |
| `apply_db_fix.py` | Database fixes |
| `backfill_generation_discovered.py` | Generation discovered backfill |

---

## Documentation (`DOCS/`)

| File | Purpose |
|------|---------|
| `Ouroboros_Master_Ruleset.md` | Master operating rules (source of truth) |
| `agi_unified_theory.md` | AGI as Network Intelligence unified theory |
| `two_streams_implementation_plan.md` | Two-Streams consciousness design |
| `two-streams.md` | Two-Streams concept overview |
| `ouroboros - biome theory.md` | Biome theory philosophy |
| `Ouroboros Concept.md` | Core concept documentation |
| `ouroboros_final_implementation.md` | Final implementation notes |
| `Ouroboros_Three_Layer_Quick_Reference.md` | Three-layer architecture reference |
| `how_arc_api_works.md` | ARC API documentation |
| `arc_api_actions_rules.md` | Action rules for API |
| `how_the_system_works.md` | System overview |
| `core_gameplay_refactor_plan.md` | Refactoring plans |
| `agent-game-assessment.md` | Agent assessment documentation |
| `system-health-metrics.md` | Health metrics |
| `operational_philosophy_and_10_questions.md` | Philosophy guide |
| `Roadmap_Level_4_to_5.md` | Development roadmap |
| `emergent-reasoning-compressed.md` | Emergent reasoning concepts |
| `payload_quality_improvement_plan.md` | Payload quality improvements |

---

## Dependency Graph

### Core Import Tree (Simplified)
```
run_evolution.py
+-- autonomous_evolution_runner.py
    |-- core_gameplay.py
    |   |-- game_session_manager.py
    |   |   +-- arc_api_client.py
    |   |-- action_handler.py
    |   |   |-- visual_analyzer.py
    |   |   +-- arc_api_client.py
    |   |-- database_interface.py
    |   |-- prestige_engine.py
    |   |-- sensation_engine.py
    |   |-- viral_package_engine.py
    |   |-- agent_operating_mode_system.py
    |   |-- breakthrough_budget_allocator.py
    |   |-- multi_stage_matching_pipeline.py
    |   |   +-- sequence_abstraction.py
    |   |-- subgoal_planning_activator.py
    |   |   +-- subgoal_planner.py
    |   +-- agent_self_model.py
    |-- evolutionary_engine.py
    |   |-- database_interface.py
    |   |-- prestige_engine.py
    |   |-- agent_operating_mode_system.py
    |   +-- sensation_engine.py
    |-- agent_factory.py
    |-- revive_agents.py (every 5 generations)
    |-- performance_analyzer.py
    |-- game_scheduler.py
    |-- sequence_pruning_system.py
    |-- safe_cleanup.py
    +-- disk_space_monitor.py
```

---

## Orphaned/Duplicate Functionality

### Potentially Orphaned Files
Files that may no longer be actively used in the main execution path:

| File | Reason | Recommendation |
|------|--------|----------------|
| `symbolic_reasoning_engine.py` | WorldModel, object tracking - never imported | Integrate or document as future |
| `visual_reasoning_engine.py` | Pattern reasoning - never imported | Integrate or document as future |
| `emotional_gameplay_mixin.py` | Mixin not inherited by GameplayEngine | Integrate or delete |
| `specialist_coordinator.py` | Never imported | Investigate, likely delete |

### Duplicate Functionality Detected

#### Database Cleanup
| File | Approach |
|------|----------|
| `safe_cleanup.py` | **Primary** (Rule 12), safe operations |

**Note**: Redundant cleanup utilities (`aggressive_cleanup.py`, `emergency_sequence_cleanup.py`, `historical_data_cleanup.py`) were deleted - `safe_cleanup.py` handles all cleanup needs.

#### Game Scheduling
| File | Purpose |
|------|---------|
| `game_scheduler.py` | General game scheduling |
| `evolution_game_scheduler.py` | Evolution-specific scheduling |

**Status**: These are complementary, not duplicate.

---


---

## Key Classes

| Class | File | Purpose |
|-------|------|---------|
| `GameplayEngine` | `core_gameplay.py` | Main game loop |
| `AutonomousEvolutionRunner` | `autonomous_evolution_runner.py` | Evolution orchestrator |
| `ARCClient` | `arc_api_client.py` | API client |
| `ARCAgent` | `agent_factory.py` | Agent representation |
| `AgentFactory` | `agent_factory.py` | Agent creation |
| `DatabaseInterface` | `database_interface.py` | Database operations |
| `PrestigeEngine` | `prestige_engine.py` | Prestige calculations |
| `ViralPackageEngine` | `viral_package_engine.py` | Viral transfer, role reputation |
| `SensationEngine` | `sensation_engine.py` | Emotional intelligence, semantic impressions |
| `EvolutionaryEngine` | `evolutionary_engine.py` | Breeding/selection |
| `AgentOperatingModeSystem` | `agent_operating_mode_system.py` | Role assignment, meta-bias |
| `AgentSelfModel` | `agent_self_model.py` | Self-model, control hypotheses |
| `WeavingReporter` | `agent_self_model.py` | Two-Streams weaving reports |
| `MultiStageMatchingPipeline` | `multi_stage_matching_pipeline.py` | Sequence matching |
| `SequenceAbstraction` | `sequence_abstraction.py` | Concept matching |
| `SafeDatabaseCleaner` | `safe_cleanup.py` | Safe cleanup |
| `AgentRevivalSystem` | `revive_agents.py` | Agent revival |

---

## Recommendations

### Low Priority
4. **Audit Learning Engines** - Identify which are actively used
6. **Expand Unit Test Coverage** - Cover critical systems

### Completed
- [x] Agent Revival Integration - Working every 5 generations
- [x] Two-Streams Implementation - All 5 integrations complete
- [x] Network Failure Hypotheses - Active in action selection
- [x] Agent Self-Model Network Sharing - Control hypotheses shared
- [x] Target Win Rate Removal - Simplified stopping criteria

---

*This inventory follows Rule 9: No summary files unless asked. Generated on user request.*
*Note: Line counts and exact file counts omitted as they change frequently.*
