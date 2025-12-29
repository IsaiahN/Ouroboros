# C4 Container Diagram - Ouroboros System

## Container-Level Architecture

This diagram shows the major containers (deployable units/major code modules) within the Ouroboros system and their relationships.

```
+==============================================================================+
|                              OUROBOROS SYSTEM                                 |
|                     (Autonomous ARC-AGI Evolution Platform)                  |
+==============================================================================+

+------------------------------------------------------------------------------+
|                         ORCHESTRATION LAYER                                   |
+------------------------------------------------------------------------------+
|                                                                              |
|   +----------------------------------+    +--------------------------------+ |
|   |   AutonomousEvolutionRunner     |    |     GameScheduler              | |
|   |   [autonomous_evolution_runner] |    |     [evolution_game_scheduler] | |
|   |----------------------------------|    |--------------------------------| |
|   | - Main orchestration loop        |    | - Game selection strategy      | |
|   | - Generation management          |--->| - Adaptive sampling            | |
|   | - Population management          |    | - Cold/stuck game promotion    | |
|   | - Signal handling                |    | - Weighted priority scoring    | |
|   | - Cleanup coordination           |    +--------------------------------+ |
|   | - Checkpoint/resume              |                                       |
|   +------------------+---------------+    +--------------------------------+ |
|                      |                    |   OuroborosCoordinator         | |
|                      |                    |   [ouroboros_coordinator]      | |
|                      |                    |--------------------------------| |
|                      +-------------------->  - Multi-agent coordination    | |
|                                           |  - Session lifecycle           | |
|                                           |  - Error recovery              | |
|                                           +--------------------------------+ |
|                                                                              |
|   +----------------------------------+    +--------------------------------+ |
|   |      AgentFactory               |    |   AgentLifecycleManager        | |
|   |      [agent_factory]            |    |   [agent_lifecycle_manager]    | |
|   |----------------------------------|    |--------------------------------| |
|   | - Agent creation                 |    | - Birth/death management       | |
|   | - Genome initialization          |--->| - Retirement logic             | |
|   | - Role assignment                |    | - Revival mechanism            | |
|   +----------------------------------+    +--------------------------------+ |
|                                                                              |
|   +----------------------------------+                                       |
|   |      run_evolution.py           |    Entry point: python run_evolution  |
|   |      [run_evolution]            |    --max-generations N                |
|   +----------------------------------+                                       |
+------------------------------------------------------------------------------+
         |                        |                          |
         v                        v                          v
+------------------------------------------------------------------------------+
|                           GAMEPLAY LAYER                                      |
+------------------------------------------------------------------------------+
|                                                                              |
|   +----------------------------------+    +--------------------------------+ |
|   |        GameplayEngine           |    |      ActionHandler             | |
|   |        [core_gameplay]          |    |      [action_handler]          | |
|   |----------------------------------|    |--------------------------------| |
|   | - Main game loop (_run_game)    |    | - Action validation            | |
|   | - Action selection              |--->| - Coordinate processing        | |
|   | - Frame analysis                |    | - Spam/oscillation detection   | |
|   | - Win/loss detection            |    | - Frame dimension checks       | |
|   | - Sequence capture              |    | - Recovery attempts            | |
|   | - CODS integration              |    +--------------------------------+ |
|   | - 14,708 lines (main engine)    |                                       |
|   +------------------+---------------+    +--------------------------------+ |
|                      |                    |   GameSessionManager           | |
|                      |                    |   [game_session_manager]       | |
|                      |                    |--------------------------------| |
|                      +-------------------->  - Session start/stop          | |
|                                           |  - Game/level reset            | |
|                                           |  - Budget enforcement          | |
|                                           |  - Generation tagging          | |
|                                           +--------------------------------+ |
+------------------------------------------------------------------------------+
         |                        |                          |
         v                        v                          v
+------------------------------------------------------------------------------+
|                        INTELLIGENCE LAYER                                     |
+------------------------------------------------------------------------------+
|                                                                              |
|   +----------------------------------+    +--------------------------------+ |
|   |         CODSEngine              |    |    AgentSelfModel              | |
|   |         [cods_engine]           |    |    [agent_self_model]          | |
|   |----------------------------------|    |--------------------------------| |
|   | - Cognitive Operator Discovery  |    | - "I am this object" tracking  | |
|   | - Bayesian hypothesis tracking  |--->| - Object control correlation   | |
|   | - Operator composition          |    | - Network hypothesis sharing   | |
|   | - Primitive unlock management   |    | - ACTION5/ACTION6 behavior     | |
|   | - 4,530 lines                   |    | - Selection state tracking     | |
|   +----------------------------------+    +--------------------------------+ |
|                                                                              |
|   +----------------------------------+    +--------------------------------+ |
|   |     RuleInductionEngine         |    |    SubgoalPlanner              | |
|   |     [rule_induction_engine]     |    |    [subgoal_planner]           | |
|   |----------------------------------|    |--------------------------------| |
|   | - Learn rules from wins         |    | - Hierarchical planning        | |
|   | - Precondition extraction       |<-->| - Subgoal decomposition        | |
|   | - Abstract action templates     |    | - Plan execution tracking      | |
|   | - Transfer learning             |    | - Subgoal pattern learning     | |
|   +----------------------------------+    +--------------------------------+ |
|                                                                              |
|   +----------------------------------+    +--------------------------------+ |
|   |      VisualAnalyzer             |    |   VisualReasoningEngine        | |
|   |      [visual_analyzer]          |    |   [visual_reasoning_engine]    | |
|   |----------------------------------|    |--------------------------------| |
|   | - Frame change detection         |    | - Pattern recognition          | |
|   | - Object tracking               |--->| - Symmetry detection           | |
|   | - Anomaly detection             |    | - Complexity analysis          | |
|   +----------------------------------+    +--------------------------------+ |
|                                                                              |
|   +----------------------------------+    +--------------------------------+ |
|   |      ObjectDetector             |    |   ConceptDiscoveryEngine       | |
|   |      [object_detector]          |    |   [concept_discovery_engine]   | |
|   |----------------------------------|    |--------------------------------| |
|   | - Color-based object finding    |    | - Abstract concept learning    | |
|   | - Shape identification          |--->| - Concept generalization       | |
|   | - Connected component analysis  |    | - Cross-game concept transfer  | |
|   +----------------------------------+    +--------------------------------+ |
|                                                                              |
|   +----------------------------------+    +--------------------------------+ |
|   |   SymbolicReasoningEngine       |    |   OperatorComposer             | |
|   |   [symbolic_reasoning_engine]   |    |   [operator_composer]          | |
|   |----------------------------------|    |--------------------------------| |
|   | - Logical inference             |    | - Compose primitive operators  | |
|   | - Symbolic pattern matching     |--->| - Test compositions            | |
|   | - Rule application              |    | - Operator chaining            | |
|   +----------------------------------+    +--------------------------------+ |
|                                                                              |
|   +----------------------------------+    +--------------------------------+ |
|   |   PrimitiveUnlockManager        |    |   SeedPrimitives               | |
|   |   [primitive_unlock_manager]    |    |   [seed_primitives]            | |
|   |----------------------------------|    |--------------------------------| |
|   | - Progressive primitive unlock  |    | - Initial operator set         | |
|   | - Unlock conditions             |--->| - Foundational patterns        | |
|   +----------------------------------+    +--------------------------------+ |
+------------------------------------------------------------------------------+
         |                        |                          |
         v                        v                          v
+------------------------------------------------------------------------------+
|                          SOCIAL LAYER                                         |
+------------------------------------------------------------------------------+
|                                                                              |
|   +----------------------------------+    +--------------------------------+ |
|   |        PrestigeEngine           |    |    ViralPackageEngine          | |
|   |        [prestige_engine]        |    |    [viral_package_engine]      | |
|   |----------------------------------|    |--------------------------------| |
|   | - Network contribution scoring  |    | - Horizontal knowledge xfer    | |
|   | - Breeding priority (1-3x)      |--->| - Viral packages (success)     | |
|   | - Survival protection (0-80%)   |    | - Pariah patterns (failure)    | |
|   | - 3% decay per generation       |    | - Frontier exploration pkgs    | |
|   | - Validated recombination       |    | - Usefulness tracking          | |
|   +----------------------------------+    +--------------------------------+ |
|                                                                              |
|   +----------------------------------+    +--------------------------------+ |
|   |      HorizontalTransferEngine   |    |    KnowledgeRecombinationEng   | |
|   |      [horizontal_transfer_eng]  |    |    [knowledge_recombination]   | |
|   |----------------------------------|    |--------------------------------| |
|   | - Agent-to-agent transfer       |    | - Knowledge fusion             | |
|   | - Sequence sharing              |<-->| - Pattern recombination        | |
|   | - Operator sharing              |    | - Novel hypothesis generation  | |
|   +----------------------------------+    +--------------------------------+ |
|                                                                              |
|   +----------------------------------+    +--------------------------------+ |
|   |   CollectiveReasoningEngine     |    |    PariahValidator             | |
|   |   [collective_reasoning_engine] |    |    [pariah_validator]          | |
|   |----------------------------------|    |--------------------------------| |
|   | - Multi-agent reasoning         |    | - Validate failure patterns    | |
|   | - Consensus building            |--->| - Pariah reliability tracking  | |
|   | - Distributed problem solving   |    | - False positive detection     | |
|   +----------------------------------+    +--------------------------------+ |
+------------------------------------------------------------------------------+
         |                        |                          |
         v                        v                          v
+------------------------------------------------------------------------------+
|                        EMOTIONAL LAYER (Phase 4.5)                           |
+------------------------------------------------------------------------------+
|                                                                              |
|   +----------------------------------+    +--------------------------------+ |
|   |       SensationEngine           |    |    FrustrationDetector         | |
|   |       [sensation_engine]        |    |    [frustration_detector]      | |
|   |----------------------------------|    |--------------------------------| |
|   | - Object-sensation mappings     |    | - Plateau detection            | |
|   | - Navigation state tracking     |--->| - Frustration thresholds       | |
|   | - Action biasing                |    | - Stuck state recognition      | |
|   | - Emotional learning            |    | - Behavioral triggers          | |
|   | - Role-based modes              |    +--------------------------------+ |
|   +----------------------------------+                                       |
|                                           +--------------------------------+ |
|   +----------------------------------+    |    NearMissAnalyzer            | |
|   |    ResonanceDetector            |    |    [near_miss_analyzer]        | |
|   |    [resonance_detector]         |    |--------------------------------| |
|   |----------------------------------|    | - Almost-win detection         | |
|   | - Strategy resonance             |--->| - Critical action analysis     | |
|   | - Amplification signals         |    | - Solution proximity scoring   | |
|   +----------------------------------+    +--------------------------------+ |
|                                                                              |
|   +----------------------------------+    +--------------------------------+ |
|   |     SomaticProfileSystem        |    |   EmotionalGameplayMixin       | |
|   |     [somatic_profile_system]    |    |   [emotional_gameplay_mixin]   | |
|   |----------------------------------|    |--------------------------------| |
|   | - Layer 3 somatic profiles      |    | - Emotional action biasing     | |
|   | - Agent experience storage      |--->| - Feeling-based decisions      | |
|   | - Personality persistence       |    | - Integration with gameplay    | |
|   +----------------------------------+    +--------------------------------+ |
+------------------------------------------------------------------------------+
         |                        |                          |
         v                        v                          v
+------------------------------------------------------------------------------+
|                        REGULATION LAYER                                       |
+------------------------------------------------------------------------------+
|                                                                              |
|   +----------------------------------+    +--------------------------------+ |
|   |    RegulatorySignalEngine       |    |    NetworkIntelligenceEngine   | |
|   |    [regulatory_signal_engine]   |    |    [network_intelligence_eng]  | |
|   |----------------------------------|    |--------------------------------| |
|   | - Quorum sensing (bacterial)    |    | - Ecosystem health metrics     | |
|   | - 8 signal types                |--->| - Shannon entropy diversity    | |
|   | - Role need signals             |    | - Information flow rates       | |
|   | - Homeostasis maintenance       |    | - Metabolic health tracking    | |
|   | - Emergent regulation           |    | - Resilience assessment        | |
|   +----------------------------------+    +--------------------------------+ |
|                                                                              |
|   +----------------------------------+    +--------------------------------+ |
|   |   AgentOperatingModeSystem      |    |    EvolutionaryEngine          | |
|   |   [agent_operating_mode_system] |    |    [evolutionary_engine]       | |
|   |----------------------------------|    |--------------------------------| |
|   | - Dynamic role assignment       |    | - Breeding selection           | |
|   | - Pioneer/Optimizer/Generalist  |--->| - Crossover operations         | |
|   | - Phase detection (EXPL/OPT)    |    | - Mutation strategies          | |
|   | - Mode persistence per game     |    | - Population management        | |
|   +----------------------------------+    +--------------------------------+ |
|                                                                              |
|   +----------------------------------+    +--------------------------------+ |
|   |     AutopoiesisMonitor          |    |   GameDiversityPreservation    | |
|   |     [autopoiesis_monitor]       |    |   [game_diversity_preservation]| |
|   |----------------------------------|    |--------------------------------| |
|   | - Self-organization tracking    |    | - Diversity metrics            | |
|   | - System stability checks       |--->| - Anti-monoculture safeguards  | |
|   | - Emergent behavior detection   |    | - Game type coverage           | |
|   +----------------------------------+    +--------------------------------+ |
|                                                                              |
|   +----------------------------------+    +--------------------------------+ |
|   |     AdaptiveActionLimits        |    |   MetaLearningCurriculum       | |
|   |     [adaptive_action_limits]    |    |   [meta_learning_curriculum]   | |
|   |----------------------------------|    |--------------------------------| |
|   | - Dynamic budget adjustment     |    | - Learning curriculum design   | |
|   | - Per-game action limits        |--->| - Difficulty progression       | |
|   | - Performance-based scaling     |    | - Meta-learning optimization   | |
|   +----------------------------------+    +--------------------------------+ |
+------------------------------------------------------------------------------+
         |                        |                          |
         v                        v                          v
+------------------------------------------------------------------------------+
|                        BREAKTHROUGH LAYER                                     |
+------------------------------------------------------------------------------+
|                                                                              |
|   +----------------------------------+    +--------------------------------+ |
|   |      BreakthroughDetector       |    |  BreakthroughBudgetAllocator   | |
|   |      [breakthrough_detector]    |    |  [breakthrough_budget_alloc]   | |
|   |----------------------------------|    |--------------------------------| |
|   | - Novel win detection           |    | - Dynamic budget allocation    | |
|   | - Improvement tracking          |--->| - Priority game targeting      | |
|   | - Breakthrough events           |    | - Resource optimization        | |
|   +----------------------------------+    +--------------------------------+ |
|                                                                              |
|   +----------------------------------+    +--------------------------------+ |
|   |   TerminalPatternDetector       |    |    OracleHealthMonitor         | |
|   |   [terminal_pattern_detector]   |    |    [oracle_health_monitor]     | |
|   |----------------------------------|    |--------------------------------| |
|   | - Infinite loop detection       |    | - System health checks         | |
|   | - Unwinnable state detection    |--->| - Bug detection/logging        | |
|   | - Early termination signals     |    | - Investigation prompts        | |
|   +----------------------------------+    +--------------------------------+ |
|                                                                              |
|   +----------------------------------+    +--------------------------------+ |
|   |   CounterfactualAnalyzer        |    | OptimizationThresholdSystem    | |
|   |   [counterfactual_analyzer]     |    | [optimization_threshold_system]| |
|   |----------------------------------|    |--------------------------------| |
|   | - "What if" analysis            |    | - Optimization saturation      | |
|   | - Alternative path evaluation   |--->| - Diminishing returns detect   | |
|   | - Regret minimization           |    | - <2% improvement threshold    | |
|   +----------------------------------+    +--------------------------------+ |
|                                                                              |
|   +----------------------------------+    +--------------------------------+ |
|   |     SequenceMiner               |    |   SequenceAbstraction          | |
|   |     [sequence_miner]            |    |   [sequence_abstraction]       | |
|   |----------------------------------|    |--------------------------------| |
|   | - Extract winning sequences     |    | - Generalize sequences         | |
|   | - Pattern mining                |--->| - Abstract action templates    | |
|   | - Sequence validation           |    | - Cross-level transfer         | |
|   +----------------------------------+    +--------------------------------+ |
|                                                                              |
|   +----------------------------------+    +--------------------------------+ |
|   | MultiStageMatchingPipeline      |    |   SequencePruningSystem        | |
|   | [multi_stage_matching_pipeline] |    |   [sequence_pruning_system]    | |
|   |----------------------------------|    |--------------------------------| |
|   | - Progressive sequence matching |    | - Remove stale sequences       | |
|   | - Frame similarity scoring      |--->| - Reliability-based pruning    | |
|   | - Fuzzy matching                |    | - Storage optimization         | |
|   +----------------------------------+    +--------------------------------+ |
+------------------------------------------------------------------------------+

+------------------------------------------------------------------------------+
|                          DATA LAYER                                           |
+------------------------------------------------------------------------------+
|                                                                              |
|   +------------------------------------------------------------------------+ |
|   |                      DatabaseInterface                                  | |
|   |                      [database_interface]                               | |
|   |------------------------------------------------------------------------| |
|   | - Thread-local SQLite connections                                       | |
|   | - WAL mode with aggressive checkpointing                               | |
|   | - 73+ tables for complete system state                                 | |
|   | - Session/game/action/agent management                                 | |
|   | - Schema from complete_database_schema.sql                             | |
|   +------------------------------------------------------------------------+ |
|                                         |                                    |
|   +----------------------------------+  |  +--------------------------------+ |
|   |      SafeCleanup               |  |  |   SchemaAutoMaintenance        | |
|   |      [safe_cleanup]            |  |  |   [schema_auto_maintenance]    | |
|   |----------------------------------|  |  |--------------------------------| |
|   | - Database cleanup (Rule 12)    |  +->| - Auto schema migrations       | |
|   | - Zero-score game purging       |     | - Column additions             | |
|   | - Old log purging               |     | - Index management             | |
|   | - Preserve winning sequences    |     +--------------------------------+ |
|   +----------------------------------+                                       |
|                                                                              |
|   +----------------------------------+    +--------------------------------+ |
|   |      DatabaseLogger             |    |   DiskSpaceMonitor             | |
|   |      [database_logger]          |    |   [disk_space_monitor]         | |
|   |----------------------------------|    |--------------------------------| |
|   | - Log to DB, not files (Rule 2) |    | - Track database size          | |
|   | - DatabaseLogHandler            |--->| - 10 GB limit enforcement      | |
|   | - Structured logging            |    | - Space warnings               | |
|   +----------------------------------+    +--------------------------------+ |
|                                         |                                    |
|                                         v                                    |
|   +------------------------------------------------------------------------+ |
|   |                        core_data.db (SQLite)                           | |
|   |                        [persistent storage]                             | |
|   |------------------------------------------------------------------------| |
|   | Key Tables:                                                             | |
|   | - agents: Population with fitness, prestige, budgets                   | |
|   | - game_results: All game outcomes                                      | |
|   | - winning_sequences: Discovered solutions                              | |
|   | - network_object_control_hypotheses: Shared "I am X" knowledge         | |
|   | - viral_packages: Horizontal knowledge transfer                        | |
|   | - learned_rules: Abstract transferable patterns                        | |
|   | - subgoal_plans: Hierarchical planning data                           | |
|   | - operator_*: CODS operator system                                     | |
|   +------------------------------------------------------------------------+ |
+------------------------------------------------------------------------------+

+------------------------------------------------------------------------------+
|                      EXTERNAL SYSTEMS                                         |
+------------------------------------------------------------------------------+
|                                                                              |
|   +----------------------------------+    +--------------------------------+ |
|   |        ARCClient                |    |      ARC-AGI 3 API             | |
|   |        [arc_api_client]         |    |      [External Service]        | |
|   |----------------------------------|    |--------------------------------| |
|   | - HTTP/async session management |    | REAL GAMES ONLY                | |
|   | - Action encoding/sending       |--->| https://three.arcprize.org/api | |
|   | - Game state parsing            |    | - create_game                  | |
|   | - Scorecard tag generation      |    | - send_action                  | |
|   | - Rate limit handling           |    | - reset_game/reset_level       | |
|   +----------------------------------+    +--------------------------------+ |
+------------------------------------------------------------------------------+
```

## Container Relationships

### Data Flow Summary

| From | To | Data/Purpose |
|------|-----|-------------|
| AutonomousEvolutionRunner | GameplayEngine | Agent assignments, game configs |
| GameplayEngine | ActionHandler | Action requests for validation |
| GameplayEngine | CODSEngine | Operator application requests |
| GameplayEngine | SensationEngine | Emotional state updates |
| ActionHandler | GameSessionManager | Validated actions for API |
| GameSessionManager | ARCClient | API calls to ARC-AGI 3 |
| CODSEngine | AgentSelfModel | Object control discovery |
| PrestigeEngine | EvolutionaryEngine | Breeding priority scores |
| ViralPackageEngine | All Agents | Shared successful patterns |
| RegulatorySignalEngine | AgentOperatingModeSystem | Role need signals |
| NetworkIntelligenceEngine | AutonomousEvolutionRunner | Health metrics |
| All Containers | DatabaseInterface | Persistent storage |

### Dependency Arrows

```
Orchestration
     |
     +---> Gameplay ---> Intelligence
     |         |              |
     |         v              v
     +---> Social <-----> Emotional
     |         |              |
     |         v              v
     +---> Regulation <--> Breakthrough
     |                        |
     +---> Data <-------------+
             |
             v
       External (ARC API)
```

## Technology Stack

| Layer | Technologies |
|-------|-------------|
| Language | Python 3.11+ |
| Database | SQLite with WAL mode |
| Async | asyncio, aiohttp |
| External API | ARC-AGI 3 REST API |
| Visualization | Console output, logging |

## Key Design Decisions

1. **Single Database**: All state in `core_data.db` (Rule 2)
2. **No Pycache**: PYTHONDONTWRITEBYTECODE=1 everywhere (Rule 1)
3. **No Log Files**: DatabaseLogHandler instead (Rule 2)
4. **Real Games Only**: No mocking/simulation (Rules 5-6)
5. **Network-Centric**: Database is the organism, agents are temporary vessels

## Complete Module Inventory (Root Directory)

### Orchestration Layer
| Module | Purpose |
|--------|---------|
| `autonomous_evolution_runner.py` | Main orchestration loop (2,994 lines) |
| `evolution_game_scheduler.py` | Game selection strategy |
| `ouroboros_coordinator.py` | Multi-agent coordination |
| `agent_factory.py` | Agent creation |
| `agent_lifecycle_manager.py` | Birth/death management |
| `run_evolution.py` | Entry point script |

### Gameplay Layer
| Module | Purpose |
|--------|---------|
| `core_gameplay.py` | Main game engine (14,708 lines) |
| `action_handler.py` | Action validation |
| `game_session_manager.py` | Session lifecycle |
| `arc_api_client.py` | ARC API client |
| `api_reset_strategy.py` | Reset strategies |

### Intelligence Layer
| Module | Purpose |
|--------|---------|
| `cods_engine.py` | Cognitive Operator Discovery (4,530 lines) |
| `agent_self_model.py` | "I am this object" tracking (8,840 lines) |
| `rule_induction_engine.py` | Transfer learning |
| `subgoal_planner.py` | Hierarchical planning |
| `visual_analyzer.py` | Frame change detection |
| `visual_reasoning_engine.py` | Pattern recognition |
| `object_detector.py` | Object detection |
| `concept_discovery_engine.py` | Concept learning |
| `symbolic_reasoning_engine.py` | Logical inference |
| `operator_composer.py` | Operator composition |
| `primitive_unlock_manager.py` | Progressive unlocks |
| `seed_primitives.py` | Initial operators |

### Social Layer
| Module | Purpose |
|--------|---------|
| `prestige_engine.py` | Network contribution scoring |
| `viral_package_engine.py` | Horizontal knowledge transfer |
| `horizontal_transfer_engine.py` | Agent-to-agent sharing |
| `knowledge_recombination_engine.py` | Knowledge fusion |
| `collective_reasoning_engine.py` | Multi-agent reasoning |
| `pariah_validator.py` | Failure pattern validation |

### Emotional Layer
| Module | Purpose |
|--------|---------|
| `sensation_engine.py` | Emotional intelligence |
| `frustration_detector.py` | Plateau detection |
| `near_miss_analyzer.py` | Almost-win detection |
| `resonance_detector.py` | Strategy resonance |
| `somatic_profile_system.py` | Layer 3 profiles |
| `emotional_gameplay_mixin.py` | Feeling-based decisions |

### Regulation Layer
| Module | Purpose |
|--------|---------|
| `regulatory_signal_engine.py` | Quorum sensing |
| `network_intelligence_engine.py` | Ecosystem health |
| `agent_operating_mode_system.py` | Role assignment |
| `evolutionary_engine.py` | Breeding/selection |
| `autopoiesis_monitor.py` | Self-organization |
| `game_diversity_preservation.py` | Anti-monoculture |
| `adaptive_action_limits.py` | Dynamic budgets |
| `meta_learning_curriculum.py` | Learning curriculum |
| `prestige_vampire_detector.py` | Vampire detection |
| `trigger_controller.py` | Event triggers |

### Breakthrough Layer
| Module | Purpose |
|--------|---------|
| `breakthrough_detector.py` | Novel win detection |
| `breakthrough_budget_allocator.py` | Dynamic allocation |
| `terminal_pattern_detector.py` | Loop detection |
| `oracle_health_monitor.py` | System health |
| `counterfactual_analyzer.py` | "What if" analysis |
| `optimization_threshold_system.py` | Saturation detection |
| `sequence_miner.py` | Pattern mining |
| `sequence_abstraction.py` | Sequence generalization |
| `multi_stage_matching_pipeline.py` | Sequence matching |
| `sequence_pruning_system.py` | Stale sequence removal |

### Data Layer
| Module | Purpose |
|--------|---------|
| `database_interface.py` | Core SQLite interface |
| `database_logger.py` | Log to DB (Rule 2) |
| `safe_cleanup.py` | Database cleanup (Rule 12) |
| `schema_auto_maintenance.py` | Schema migrations |
| `disk_space_monitor.py` | Size monitoring |
| `complete_database_schema.sql` | Full schema definition |

### Other/Support
| Module | Purpose |
|--------|---------|
| `performance_analyzer.py` | Performance metrics |
| `oracle_interface.py` | Oracle integration |
| `console_metrics_capture.py` | Console parsing |
| `console_tags.py` | Tag management |
| `metric_confidence.py` | Metric reliability |
| `metric_rotator.py` | Metric rotation |
| `abstraction_config.py` | Config settings |
| `abstraction_schema.py` | Abstraction types |
| `specialist_coordinator.py` | Specialist management |
| `subgoal_planning_activator.py` | Subgoal activation |
| `revive_agents.py` | Agent revival |
| `arc_rlvr_framework.py` | RLVR framework |
| `audit_cods.py` | CODS auditing |
| `automated_assessment_runner.py` | Assessment automation |
| `cleanup_temp_files.py` | Temp file cleanup |
| `evolution_with_vampires.py` | Vampire handling |
| `enhanced_database_interface.py` | Extended DB interface |

---

*Generated from full codebase analysis*  
*Total: ~80 Python modules in root*  
*Last Updated: December 2025*
