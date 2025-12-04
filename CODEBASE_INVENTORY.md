# BitterTruth-AI Codebase Inventory

**Generated**: 2024-12-XX  
**Updated**: 2025-12-04 (File Organization Cleanup)  
**Total Files**: 61 Python files in root + 29 in manual_tools + 6 in tests + SQL schema + documentation  
**Architecture**: Autonomous ARC-AGI-3 game playing with evolutionary agents

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Folder Structure](#folder-structure)
3. [File Categories](#file-categories)
4. [Dependency Graph](#dependency-graph)
5. [Orphaned/Duplicate Functionality](#orphanedduplicate-functionality)
6. [Missing Components](#missing-components)
7. [Detailed File Inventory](#detailed-file-inventory)

---

## Executive Summary

BitterTruth-AI is an **autonomous evolutionary system** for playing ARC-AGI-3 games. The codebase implements:

- **Biome Theory**: Database as the primary "organism" with agents as temporary cellular expressions
- **Three-Layer Architecture**: Genome (static) → Epigenetic (adaptive) → Somatic (learned)
- **Four Agent Roles**: Pioneer (60%), Optimizer (30%), Generalist (10%), Exploiter (variable)
- **Prestige Economy**: Social capital separate from action budgets
- **Viral Knowledge Transfer**: Horizontal gene transfer between unrelated agents

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
├── *.py                    # 61 core Python files (actively used)
├── tests/                  # 6 unit test files
│   ├── __init__.py
│   ├── test_critical_systems.py
│   ├── test_new_modules.py
│   ├── test_recent_changes.py
│   ├── test_safe_cleanup.py
│   └── test_sequence_system.py
├── manual_tools/           # 29 debug/utility files (manual execution only)
│   ├── README.md
│   ├── action_analyzer.py
│   ├── aggressive_cleanup.py
│   ├── assess_results.py
│   ├── audit_prestige_system.py
│   ├── check_db.py
│   ├── dump_logs.py
│   ├── emergency_*.py       # Emergency recovery tools
│   ├── get_replay_url.py
│   ├── historical_data_cleanup.py
│   ├── hypothesis_monitoring.py
│   ├── inspect_db.py
│   ├── list_sequences.py
│   ├── list_tables.py
│   ├── monitor_*.py         # Monitoring utilities
│   ├── readiness_check.py
│   ├── real_progress_check.py
│   ├── rebuild_*.py         # Rebuild utilities
│   ├── remove_emojis.py
│   ├── review_*.py          # Review/inspection tools
│   ├── run_validation_cycle.py
│   ├── sequence_recovery_tool.py
│   └── system_status_report.py
├── migrations/             # Database migration scripts (historical)
├── DOCS/                   # Documentation files
└── experimental/           # Experimental features
```

---

## File Categories

### 1. CORE GAMEPLAY (7 files)
Files responsible for direct game interaction with ARC-AGI-3 API.

| File | Lines | Purpose | Actively Used |
|------|-------|---------|---------------|
| `core_gameplay.py` | 5942 | Main game loop, sequence matching, action selection | ✅ Yes |
| `action_handler.py` | ~500 | Clean interface for sending ACTION1-7 to API | ✅ Yes |
| `game_session_manager.py` | ~600 | Session lifecycle, game creation, budget enforcement | ✅ Yes |
| `arc_api_client.py` | 659 | Async HTTP client for ARC-AGI-3 API | ✅ Yes |
| `visual_analyzer.py` | 666 | Frame analysis for ACTION6 coordinate selection | ✅ Yes |
| `object_detector.py` | ~350 | Detects objects/patterns in game frames | ✅ Yes |
| `emotional_gameplay_mixin.py` | ~100 | Mixin for sensation-based gameplay | ⚠️ Partial |

### 2. SEQUENCE SYSTEM (8 files)
Files for capturing, storing, matching, and replaying winning sequences.

| File | Lines | Purpose | Actively Used |
|------|-------|---------|---------------|
| `multi_stage_matching_pipeline.py` | 285 | 5-stage fallback matching (exact→prefix→suffix→subsequence→conceptual) | ✅ Yes |
| `sequence_abstraction.py` | 427 | Concept-based sequence matching | ✅ Yes |
| `sequence_pruning_system.py` | ~450 | Removes stale/invalid sequences | ✅ Yes |
| `sequence_recovery_tool.py` | ~550 | Rebuilds sequences from action traces | ⚠️ Manual |
| `rebuild_sequences.py` | ~150 | Utility to rebuild sequence table | ⚠️ Manual |
| `abstraction_config.py` | ~100 | Configuration for abstraction system | ✅ Yes |
| `abstraction_schema.py` | ~180 | Schema definitions for abstractions | ✅ Yes |
| `list_sequences.py` | ~50 | Debug utility to list sequences | ⚠️ Manual |

### 3. AGENT SYSTEM (8 files)
Files for agent creation, lifecycle, roles, and self-modeling.

| File | Lines | Purpose | Actively Used |
|------|-------|---------|---------------|
| `agent_factory.py` | ~400 | Creates specialized agents (5 types) | ✅ Yes |
| `agent_lifecycle_manager.py` | ~250 | Agent creation/retirement/revival | ✅ Yes |
| `agent_operating_mode_system.py` | 730 | Dynamic role assignment (Pioneer/Optimizer/Generalist/Exploiter) | ✅ Yes |
| `agent_self_model.py` | ~260 | "I am this object" comprehension | ⚠️ Partial |
| `revive_agents.py` | ~360 | Agent revival mechanism | ⚠️ Manual |
| `adaptive_action_limits.py` | ~200 | Performance-based action budget adjustment | ✅ Yes |
| `somatic_profile_system.py` | ~170 | Layer 3 somatic learning management | ⚠️ Partial |
| `review_agent_roles.py` | ~470 | Debug utility to review agent assignments | ⚠️ Manual |

### 4. EVOLUTION SYSTEM (7 files)
Files for evolutionary algorithms, breeding, and selection.

| File | Lines | Purpose | Actively Used |
|------|-------|---------|---------------|
| `autonomous_evolution_runner.py` | 2242 | Main orchestrator for continuous evolution | ✅ Yes |
| `evolutionary_engine.py` | ~800 | Breeding, mutation, crossover, selection | ✅ Yes |
| `evolution_with_vampires.py` | ~110 | Vampire detection during evolution | ⚠️ Partial |
| `evolution_game_scheduler.py` | ~210 | Schedules games during evolution | ✅ Yes |
| `game_scheduler.py` | ~450 | General game scheduling logic | ✅ Yes |
| `run_evolution.py` | ~150 | Entry point script | ✅ Yes |
| `game_diversity_preservation.py` | ~280 | Maintains game variety | ✅ Yes |

### 5. LEARNING/KNOWLEDGE SYSTEM (12 files)
Files for meta-learning, knowledge transfer, and abstract reasoning.

| File | Lines | Purpose | Actively Used |
|------|-------|---------|---------------|
| `sensation_engine.py` | 613 | Emotional intelligence for actions 1-7 | ✅ Yes |
| `rule_induction_engine.py` | 587 | Extract IF-THEN rules from wins | ⚠️ Partial |
| `meta_learning_curriculum.py` | ~600 | Curriculum-based learning | ⚠️ Partial |
| `symbolic_reasoning_engine.py` | 1451 | Abstract symbolic reasoning | ⚠️ Partial |
| `visual_reasoning_engine.py` | ~700 | Visual pattern reasoning | ⚠️ Partial |
| `subgoal_planner.py` | 666 | Hierarchical multi-step planning | ⚠️ Partial |
| `subgoal_planning_activator.py` | ~350 | Activates subgoal planning | ⚠️ Partial |
| `counterfactual_analyzer.py` | ~400 | "What if" analysis | ⚠️ Partial |
| `near_miss_analyzer.py` | ~350 | Analyzes near-win situations | ⚠️ Partial |
| `frustration_detector.py` | ~300 | Detects stuck agents | ✅ Yes |
| `action_analyzer.py` | ~300 | Analyzes action effectiveness | ⚠️ Partial |
| `collective_reasoning_engine.py` | ~400 | Network-level reasoning | ⚠️ Partial |

### 6. PRESTIGE/VIRAL SYSTEM (5 files)
Files for prestige economy and horizontal gene transfer.

| File | Lines | Purpose | Actively Used |
|------|-------|---------|---------------|
| `prestige_engine.py` | 711 | Network contribution currency | ✅ Yes |
| `prestige_vampire_detector.py` | ~270 | Detects prestige exploitation | ✅ Yes |
| `viral_package_engine.py` | 972 | Bidirectional evolution (viral packages + pariahs) | ✅ Yes |
| `horizontal_transfer_engine.py` | 839 | Direct knowledge transfer between agents | ⚠️ Partial |
| `knowledge_recombination_engine.py` | 439 | Sequence chaining and pattern synthesis | ⚠️ Partial |

### 7. NETWORK INTELLIGENCE (3 files)
Files treating the database as the primary organism.

| File | Lines | Purpose | Actively Used |
|------|-------|---------|---------------|
| `network_intelligence_engine.py` | 675 | Ecosystem health monitoring | ⚠️ Partial |
| `regulatory_signal_engine.py` | ~400 | Quorum sensing / homeostasis | ⚠️ Partial |
| `ouroboros_coordinator.py` | ~500 | High-level system coordination | ⚠️ Partial |

### 8. BREAKTHROUGH DETECTION (4 files)
Files for detecting and rewarding breakthrough moments.

| File | Lines | Purpose | Actively Used |
|------|-------|---------|---------------|
| `breakthrough_detector.py` | ~280 | Detects significant improvements | ✅ Yes |
| `breakthrough_budget_allocator.py` | ~160 | Allocates extra budget for breakthroughs | ✅ Yes |
| `optimization_threshold_system.py` | ~460 | Detects optimization saturation | ⚠️ Partial |
| `arc_rlvr_framework.py` | ~300 | Reinforcement learning framework | ⚠️ Partial |

### 9. DATABASE (5 files)
Files for database operations and schema management.

| File | Lines | Purpose | Actively Used |
|------|-------|---------|---------------|
| `database_interface.py` | ~1200 | Core SQLite operations | ✅ Yes |
| `enhanced_database_interface.py` | ~70 | Extended database operations | ⚠️ Unclear |
| `database_logger.py` | ~150 | DatabaseLogHandler (no file logs) | ✅ Yes |
| `schema_auto_maintenance.py` | ~250 | Auto-updates schema | ⚠️ Manual |
| `complete_database_schema.sql` | 2216 | Full schema export (73 tables) | Reference |

### 10. CLEANUP UTILITIES (3 files in root, 5 in manual_tools)
Files for database and file system cleanup.

| File | Lines | Purpose | Location |
|------|-------|---------|----------|
| `safe_cleanup.py` | ~380 | Safe database cleanup (Rule 12) | Root (active) |
| `cleanup_temp_files.py` | ~340 | Cleans temporary files | Root (active) |
| `disk_space_monitor.py` | ~180 | Monitors disk usage | Root (active) |
| `aggressive_cleanup.py` | ~300 | More aggressive cleanup | `manual_tools/` |
| `emergency_sequence_cleanup.py` | ~280 | Emergency sequence cleanup | `manual_tools/` |
| `historical_data_cleanup.py` | ~270 | Cleans old historical data | `manual_tools/` |
| `remove_emojis.py` | ~100 | Removes Unicode emojis (Rule 11) | `manual_tools/` |

### 11. ANALYSIS/MONITORING (3 files in root, 6 in manual_tools)
Files for performance analysis and system monitoring.

| File | Lines | Purpose | Location |
|------|-------|---------|----------|
| `performance_analyzer.py` | 769 | Comprehensive population analysis | Root (active) |
| `automated_assessment_runner.py` | ~440 | Automated assessment | Root (partial) |
| `hypothesis_monitoring.py` | ~930 | Hypothesis test tracking | `manual_tools/` |
| `assess_results.py` | ~90 | Quick result assessment | `manual_tools/` |
| `monitor_game_results.py` | ~60 | Game result monitoring | `manual_tools/` |
| `monitor_sequence_validation.py` | ~370 | Sequence validation monitoring | `manual_tools/` |
| `audit_prestige_system.py` | ~250 | Audits prestige calculations | `manual_tools/` |
| `system_status_report.py` | ~180 | Generates status reports | `manual_tools/` |
| `real_progress_check.py` | ~200 | Checks actual progress | `manual_tools/` |

### 12. TESTING (6 files) - Located in `/tests/`
Unit test files (allowed per Rule 5 exception for core components).

| File | Lines | Purpose | Location |
|------|-------|---------|----------|
| `__init__.py` | ~5 | Package init | `/tests/` |
| `test_safe_cleanup.py` | ~380 | Tests for SafeDatabaseCleaner | `/tests/` |
| `test_critical_systems.py` | ~570 | Tests for critical systems | `/tests/` |
| `test_new_modules.py` | ~410 | Tests for new modules | `/tests/` |
| `test_recent_changes.py` | ~480 | Tests for recent changes | `/tests/` |
| `test_sequence_system.py` | ~300 | Tests for sequence system | `/tests/` |

### 13. DEBUG/INSPECTION UTILITIES - Located in `/manual_tools/`
Manual utilities for debugging and inspection. **All in `/manual_tools/` folder.**

| File | Lines | Purpose |
|------|-------|---------|
| `action_analyzer.py` | ~300 | Analyzes action effectiveness |
| `aggressive_cleanup.py` | ~300 | More aggressive cleanup |
| `assess_results.py` | ~90 | Quick result assessment |
| `audit_prestige_system.py` | ~250 | Audits prestige calculations |
| `check_db.py` | ~30 | Quick database check |
| `dump_logs.py` | ~40 | Dumps logs from database |
| `emergency_sequence_cleanup.py` | ~280 | Emergency sequence cleanup |
| `get_replay_url.py` | ~80 | Gets replay URLs for games |
| `historical_data_cleanup.py` | ~270 | Cleans old historical data |
| `hypothesis_monitoring.py` | ~930 | Hypothesis test tracking |
| `inspect_db.py` | ~40 | Database inspection |
| `list_sequences.py` | ~50 | Lists winning sequences |
| `list_tables.py` | ~30 | Lists database tables |
| `monitor_game_results.py` | ~60 | Game result monitoring |
| `monitor_sequence_validation.py` | ~370 | Sequence validation monitoring |
| `readiness_check.py` | ~200 | System readiness check |
| `real_progress_check.py` | ~200 | Checks actual progress |
| `rebuild_database.py` | ~150 | Database rebuild utility |
| `rebuild_sequences.py` | ~150 | Rebuilds sequence table |
| `remove_emojis.py` | ~100 | Removes Unicode emojis (Rule 11) |
| `review_agent_roles.py` | ~470 | Reviews agent assignments |
| `review_scorecards.py` | ~230 | Reviews scorecard data |
| `review_sequence_system.py` | ~810 | Reviews sequence system |
| `review_test_evolution.py` | ~200 | Reviews test evolution |
| `run_validation_cycle.py` | ~110 | Validation cycle runner |
| `sequence_recovery_tool.py` | ~550 | Rebuilds sequences from traces |
| `system_status_report.py` | ~180 | Generates status reports |

### 14. CONFIGURATION/INFRASTRUCTURE (4 files)
Infrastructure and configuration files.

| File | Lines | Purpose | Actively Used |
|------|-------|---------|---------------|
| `__init__.py` | ~5 | Package initialization | ✅ Yes |
| `api_reset_strategy.py` | ~200 | API reset handling | ✅ Yes |

### 15. MIGRATIONS (folder)
Database migration scripts (historical).

| File | Purpose |
|------|---------|
| `migrations/completed/migrate_epigenetics.py` | Epigenetics migration |
| `migrations/completed/backfill_viral_packages.py` | Viral packages backfill |
| `migrations/completed/apply_high_priority_migrations.py` | Priority migrations |
| `migrations/completed/add_level_tracking_to_traces.py` | Level tracking migration |

---

## Dependency Graph

### Core Import Tree (Simplified)
```
run_evolution.py
└── autonomous_evolution_runner.py (2242 lines)
    ├── core_gameplay.py (5942 lines)
    │   ├── game_session_manager.py
    │   │   └── arc_api_client.py
    │   ├── action_handler.py
    │   │   ├── visual_analyzer.py
    │   │   └── arc_api_client.py
    │   ├── database_interface.py
    │   ├── prestige_engine.py
    │   ├── sensation_engine.py
    │   ├── breakthrough_budget_allocator.py
    │   ├── multi_stage_matching_pipeline.py
    │   │   └── sequence_abstraction.py
    │   ├── subgoal_planning_activator.py
    │   │   └── subgoal_planner.py
    │   └── agent_self_model.py
    ├── evolutionary_engine.py
    │   ├── database_interface.py
    │   ├── prestige_engine.py
    │   ├── agent_operating_mode_system.py
    │   └── sensation_engine.py
    ├── agent_factory.py
    │   ├── database_interface.py
    │   └── sensation_engine.py
    ├── performance_analyzer.py
    ├── viral_package_engine.py
    ├── game_scheduler.py
    ├── sequence_pruning_system.py
    ├── safe_cleanup.py
    └── disk_space_monitor.py
```

### Dependency Counts
| File | Imports From | Imported By |
|------|--------------|-------------|
| `database_interface.py` | 1 (sqlite3) | 40+ files |
| `arc_api_client.py` | 5 | 3 files |
| `core_gameplay.py` | 15+ | 3 files |
| `prestige_engine.py` | 2 | 10+ files |
| `sensation_engine.py` | 2 | 8+ files |
| `agent_factory.py` | 3 | 5+ files |

---

## Orphaned/Duplicate Functionality

### Potentially Orphaned Files
Files that may no longer be actively used in the main execution path:

| File | Reason | Recommendation |
|------|--------|----------------|
| `enhanced_database_interface.py` | Only 70 lines, unclear if used | Investigate or merge into `database_interface.py` |
| `emotional_gameplay_mixin.py` | Mixin pattern, unclear integration | Verify integration with `core_gameplay.py` |
| `somatic_profile_system.py` | Layer 3 handling, may overlap with `sensation_engine.py` | Review for duplication |
| `arc_rlvr_framework.py` | Separate RL framework, unclear integration | Verify if actively called |
| `ouroboros_coordinator.py` | High-level coordinator, may be superseded | Check if used by `autonomous_evolution_runner.py` |

### Duplicate Functionality Detected

#### 1. Database Cleanup (Multiple implementations)
| File | Approach |
|------|----------|
| `safe_cleanup.py` | Recommended (Rule 12), safe operations |
| `aggressive_cleanup.py` | More aggressive, manual use |
| `emergency_sequence_cleanup.py` | Sequence-specific emergency |
| `historical_data_cleanup.py` | Historical data cleanup |

**Recommendation**: Consolidate into `safe_cleanup.py` with configurable aggressiveness levels.

#### 2. Sequence System (Overlapping concerns)
| File | Responsibility |
|------|----------------|
| `sequence_abstraction.py` | Concept-based matching |
| `multi_stage_matching_pipeline.py` | 5-stage fallback matching |
| `sequence_recovery_tool.py` | Rebuilds from traces |
| `rebuild_sequences.py` | Manual rebuild utility |

**Recommendation**: These are complementary, not duplicate. Keep separate but ensure clear boundaries.

#### 3. Game Scheduling (Two implementations)
| File | Purpose |
|------|---------|
| `game_scheduler.py` | General game scheduling |
| `evolution_game_scheduler.py` | Evolution-specific scheduling |

**Recommendation**: Consider merging or establishing clearer hierarchy.

#### 4. Learning Engines (Many similar engines)
Multiple "engine" files with potentially overlapping responsibilities:
- `rule_induction_engine.py`
- `symbolic_reasoning_engine.py`
- `visual_reasoning_engine.py`
- `collective_reasoning_engine.py`

**Recommendation**: Audit which are actively used and consider consolidation.

---

## Missing Components

Based on codebase patterns and the Master Ruleset, these components appear to be missing or incomplete:

### 1. Full Game Sequence Table Separation (CRITICAL)
**Status**: TABLE EXISTS but NOT USED in code  
**Per Ruleset**: "Full Game Sequences (Holy Grail)" should be in `winning_sequences_full_game` table  
**Current**: Table created in migrations but NO code writes to it (check `core_gameplay.py` line 3235 - only inserts to `winning_sequences`)  
**Impact**: Cannot properly protect full game wins from cleanup  
**Fix Required**: Add ~50 lines to `_capture_winning_sequence` to detect and store full game wins

### 2. Optimizer Penultimate Checkpoint / End Subsequence (BLOCKING)
**Status**: NOT IMPLEMENTED  
**Per Ruleset**: "Auto-append end subsequence before DB save"  
**Current**: When optimizers reset levels, they save sequences that DON'T include the final win actions  
**Impact**: Optimizer sequences are INCOMPLETE and may not lead to level wins when replayed  
**Fix Required**: Add logic to append guaranteed-win ending to optimizer sequences before storage

### 3. Agent Revival Mechanism (ORPHANED)
**Status**: `revive_agents.py` EXISTS but NEVER CALLED  
**Per Ruleset**: "Option B + C for revival" (Genome + network knowledge hybrid)  
**Current**: `AgentRevivalSystem` class is fully implemented but not integrated into `autonomous_evolution_runner.py` or `evolutionary_engine.py`  
**Impact**: Good agents die permanently when they could be revived  
**Fix Required**: Add ~20 lines to evolution loop to call revival system

### 4. Sequence Validation Subroutine (MANUAL ONLY)
**Status**: `monitor_sequence_validation.py` exists but requires manual execution  
**Per Ruleset**: Should run "at end of each generation"  
**Current**: Not integrated into `autonomous_evolution_runner.py`  
**Impact**: Stale sequences not detected automatically

### 5. Exploiter 50/50 Split (PARTIALLY IMPLEMENTED)
**Status**: `social_rule_adherence` column EXISTS but split logic incomplete  
**Per Ruleset**: "50% Sociopathic (social_rule_adherence = 0.0-0.3), 50% Normal (0.7-1.0)"  
**Current**: `agent_operating_mode_system.py` sets values but not 50/50 split for exploiters specifically  
**Impact**: Missing strategic diversity in optimized games

### 6. Orphaned Learning Engines (NOT INTEGRATED)
**Status**: Major engines exist but aren't used  
**Files**:
- `symbolic_reasoning_engine.py` (1,451 lines) - WorldModel, object tracking, relations
- `visual_reasoning_engine.py` (~700 lines) - Pattern reasoning
- `emotional_gameplay_mixin.py` (~100 lines) - Not inherited by GameplayEngine
- `specialist_coordinator.py` (236 lines) - Never imported  
**Impact**: Significant functionality unused  
**Fix Required**: Either integrate or document as future features

### 7. Email Notifications (MISSING)
**Status**: Not implemented  
**Per Ruleset**: "Daily email updates to `isaiahnwu@gmail.com`"  
**Current**: No email functionality found  
**Impact**: User not informed of critical issues (LOW PRIORITY - User preference may be no email)

---

## Files Actively Used vs Orphaned

### Actively Used (Imported by core systems)
| File | Imported By |
|------|-------------|
| `multi_stage_matching_pipeline.py` | `core_gameplay.py` |
| `agent_self_model.py` | `core_gameplay.py` |
| `sequence_abstraction.py` | `core_gameplay.py` |
| `subgoal_planner.py` | `core_gameplay.py`, `autonomous_evolution_runner.py` |
| `subgoal_planning_activator.py` | `core_gameplay.py` |
| `enhanced_database_interface.py` | `autonomous_evolution_runner.py` |
| `frustration_detector.py` | `autonomous_evolution_runner.py` |
| `breakthrough_detector.py` | `core_gameplay.py` |
| `breakthrough_budget_allocator.py` | `core_gameplay.py`, `autonomous_evolution_runner.py` |
| `near_miss_analyzer.py` | `autonomous_evolution_runner.py` |
| `counterfactual_analyzer.py` | `autonomous_evolution_runner.py` |
| `safe_cleanup.py` | `autonomous_evolution_runner.py` |
| `action_handler.py` | `core_gameplay.py` |
| `visual_analyzer.py` | `action_handler.py` |
| `game_session_manager.py` | `core_gameplay.py` |

### Orphaned (Not Imported, Exist as Standalone)
| File | Lines | Action Needed |
|------|-------|---------------|
| `revive_agents.py` | 386 | **INTEGRATE** - valuable, just not connected |
| `symbolic_reasoning_engine.py` | 1,451 | Document as future feature OR integrate |
| `visual_reasoning_engine.py` | ~700 | Document as future feature OR integrate |
| `emotional_gameplay_mixin.py` | ~100 | Integrate OR delete |
| `specialist_coordinator.py` | 236 | Investigate purpose, likely delete |


---

## Detailed File Inventory

### Files by Line Count (Top 20)
| Rank | File | Lines | Category |
|------|------|-------|----------|
| 1 | `core_gameplay.py` | 5942 | Core Gameplay |
| 2 | `complete_database_schema.sql` | 2216 | Database |
| 3 | `autonomous_evolution_runner.py` | 2242 | Evolution |
| 4 | `symbolic_reasoning_engine.py` | 1451 | Learning |
| 5 | `database_interface.py` | ~1200 | Database |
| 6 | `viral_package_engine.py` | 972 | Prestige/Viral |
| 7 | `hypothesis_monitoring.py` | ~930 | Analysis |
| 8 | `horizontal_transfer_engine.py` | 839 | Prestige/Viral |
| 9 | `review_sequence_system.py` | ~810 | Debug |
| 10 | `evolutionary_engine.py` | ~800 | Evolution |
| 11 | `performance_analyzer.py` | 769 | Analysis |
| 12 | `agent_operating_mode_system.py` | 730 | Agent System |
| 13 | `prestige_engine.py` | 711 | Prestige/Viral |
| 14 | `visual_reasoning_engine.py` | ~700 | Learning |
| 15 | `network_intelligence_engine.py` | 675 | Network |
| 16 | `subgoal_planner.py` | 666 | Learning |
| 17 | `visual_analyzer.py` | 666 | Core Gameplay |
| 18 | `arc_api_client.py` | 659 | Core Gameplay |
| 19 | `sensation_engine.py` | 613 | Learning |
| 20 | `meta_learning_curriculum.py` | ~600 | Learning |

### Key Classes Exported
| Class | File | Purpose |
|-------|------|---------|
| `GameplayEngine` | `core_gameplay.py` | Main game loop |
| `AutonomousEvolutionRunner` | `autonomous_evolution_runner.py` | Evolution orchestrator |
| `ARCClient` | `arc_api_client.py` | API client |
| `ARCAgent` | `agent_factory.py` | Agent representation |
| `AgentFactory` | `agent_factory.py` | Agent creation |
| `DatabaseInterface` | `database_interface.py` | Database operations |
| `PrestigeEngine` | `prestige_engine.py` | Prestige calculations |
| `ViralPackageEngine` | `viral_package_engine.py` | Viral transfer |
| `SensationEngine` | `sensation_engine.py` | Emotional intelligence |
| `EvolutionaryEngine` | `evolutionary_engine.py` | Breeding/selection |
| `AgentOperatingModeSystem` | `agent_operating_mode_system.py` | Role assignment |
| `MultiStageMatchingPipeline` | `multi_stage_matching_pipeline.py` | Sequence matching |
| `SequenceAbstraction` | `sequence_abstraction.py` | Concept matching |
| `VisualAnalyzer` | `visual_analyzer.py` | Frame analysis |
| `SubgoalPlanner` | `subgoal_planner.py` | Hierarchical planning |
| `SafeDatabaseCleaner` | `safe_cleanup.py` | Safe cleanup |
| `NetworkIntelligenceEngine` | `network_intelligence_engine.py` | Ecosystem health |

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total Python Files (root) | 61 |
| Manual Tools (manual_tools/) | 29 |
| Test Files (tests/) | 6 |
| Core Gameplay Files | 7 |
| Sequence System Files | 6 (root) + 2 (manual_tools) |
| Agent System Files | 6 (root) + 2 (manual_tools) |
| Evolution System Files | 7 |
| Learning/Knowledge Files | 12 |
| Prestige/Viral Files | 5 |
| Network Intelligence Files | 3 |
| Cleanup Utilities | 3 (root) + 5 (manual_tools) |
| Analysis/Monitoring Files | 3 (root) + 6 (manual_tools) |
| Total Lines of Code | ~35,000+ |
| Database Tables | 73 |
| Actively Used Files | ~55 (88% of root) |
| Manual/Debug Utilities | 29 (in manual_tools/) |
| Test Files | 6 (in tests/) |

---

## Recommendations

### High Priority
1. **Implement Full Game Sequence Table** - Critical for protecting full wins
2. **Fix Optimizer Checkpoint Bug** - Blocking optimization progress
3. **Consolidate Cleanup Utilities** - Reduce code drift
4. **Add Automated Sequence Validation** - Run every generation

### Medium Priority
5. **Audit Learning Engines** - Identify which are actually used
6. **Implement Exploiter 50/50 Split** - Per ruleset design
7. **Add Agent Revival Integration** - Connect `revive_agents.py` to main loop
8. **Expand Unit Test Coverage** - Cover critical systems

### Low Priority
9. **Merge Game Schedulers** - Reduce duplication
10. **Investigate Orphaned Files** - Clean or integrate
11. **Add Email Notifications** - Per ruleset requirement
12. **Document API Endpoints** - Improve maintainability

---

*This inventory follows Rule 9: No summary files unless asked. Generated on user request.*
