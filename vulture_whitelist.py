# Vulture whitelist for false positives
# These items are flagged as unused but are actually used in TYPE_CHECKING blocks
# or as type hints that vulture doesn't recognize.

# TYPE_CHECKING imports - vulture doesn't understand TYPE_CHECKING guards
# These are used for type hints but vulture sees them as unused
IThreadType  # noqa: F821 - Used in type hint line 63 of weaving_reporter.py
RepresentationLearner  # noqa: F821 - Used in type hints in cognitive_core.py, embedding_matcher.py
CognitiveStageSystem  # noqa: F821 - Used in type hint in hypothesis_system.py
DatabaseInterface  # noqa: F821 - Used in type hint in hypothesis_system.py
EngineRegistry  # noqa: F821 - Used in TYPE_CHECKING in multiple files

# decision_rung_system.py - Method parameters for future wiring
# These parameters are part of the API signature but not yet used
success  # noqa: F821 - RuleTransferRung.record_outcome() param for future rule feedback

# deprecated/engines_decision/ - Moved Feb 1, 2026
# Experimental 7-phase decision system, superseded by decision_rung_system.py
# Kept for reference but no longer in use
PhaseExecutor  # noqa: F821 - deprecated/engines_decision/phase_executor.py
EmergencyCheck  # noqa: F821 - deprecated/engines_decision/phases/emergency.py
EmergencyThresholds  # noqa: F821 - deprecated/engines_decision/phases/emergency.py
OrientPhase  # noqa: F821 - deprecated/engines_decision/phases/phase1_orient.py
GroundTruthPhase  # noqa: F821 - deprecated/engines_decision/phases/phase2_ground_truth.py
ReasonPhase  # noqa: F821 - deprecated/engines_decision/phases/phase3_reason.py
PatternPhase  # noqa: F821 - deprecated/engines_decision/phases/phase4_pattern.py
ProposePhase  # noqa: F821 - deprecated/engines_decision/phases/phase5_propose.py
FilterPhase  # noqa: F821 - deprecated/engines_decision/phases/phase6_filter.py
SelectPhase  # noqa: F821 - deprecated/engines_decision/phases/phase7_select.py
FinalDecision  # noqa: F821 - deprecated/engines_decision/phase_contracts.py
Proposal  # noqa: F821 - deprecated/engines_decision/phase_contracts.py

# engines/consciousness/ - Type hints used with string quotes for forward refs
# Vulture doesn't recognize quoted type hints like Optional['MortalityState']
MortalityState  # noqa: F821 - Used in type hints i_thread.py:1012, deliberation_engine.py:1019
WorldModel  # noqa: F821 - Used in type hints deliberation_engine.py:1025

# engines/cognition/ - TYPE_CHECKING imports for type hints
# Blackboard is used in string annotation: def __init__(self, blackboard: 'Blackboard')
Blackboard  # noqa: F821 - Used in eisenhower_layer.py:231, phenomenology_layer.py:359

# =============================================================================
# PYTHON API REQUIREMENTS (vulture doesn't understand these conventions)
# =============================================================================

# Context manager __exit__ protocol - Python REQUIRES these 3 params
exc_type  # noqa: F821 - arc_api_client.py:184 - __exit__(self, exc_type, exc_val, exc_tb)
exc_val  # noqa: F821 - arc_api_client.py:184 - __exit__(self, exc_type, exc_val, exc_tb)
exc_tb  # noqa: F821 - arc_api_client.py:184 - __exit__(self, exc_type, exc_val, exc_tb)

# Signal handler protocol - Python REQUIRES (signum, frame) params
signum  # noqa: F821 - evolution_runner.py:706 - signal handler param

# =============================================================================
# PYTEST CONVENTIONS (vulture doesn't understand pytest DI)
# =============================================================================

# Pytest hook params
exitstatus  # noqa: F821 - tests/conftest.py:62 - pytest hook param

# Pytest fixtures injected as params
monkeypatch  # noqa: F821 - tests/test_action_ladder.py - pytest fixture
is_unbeaten  # noqa: F821 - tests/test_action_ladder.py - test fixture param
mock_game_state  # noqa: F821 - tests/test_reasoning_system_fixes.py:91 - fixture
id_col  # noqa: F821 - tests/test_safe_cleanup.py:135 - loop variable used for assertion context

# Unused patch imports in tests - kept for future test expansion
# These are common test utilities that may be needed when adding test cases
patch  # noqa: F821 - Multiple test files - unittest.mock.patch for future tests
AsyncMock  # noqa: F821 - test_reasoning_system_fixes.py, test_sequence_system.py

# =============================================================================
# API COMPATIBILITY PARAMS (kept for backward compat or future use)
# =============================================================================

# Function params kept for API stability
culling_config  # noqa: F821 - agent_lifecycle_manager.py:44 - param kept for compatibility
level_before  # noqa: F821 - evolution_runner.py:357 - param available for future use

# Variables assigned for potential debugging/future use
since_date  # noqa: F821 - database_interface.py:1740 - date range query building
before_date  # noqa: F821 - database_interface.py:1745 - date range query building
hours  # noqa: F821 - representation_learner.py:366 - time calculation
timestamp_column  # noqa: F821 - safe_cleanup.py:757 - column name for queries

# =============================================================================
# UNUSED IMPORTS (kept for future use or API completeness)
# =============================================================================

arc_agi  # noqa: F821 - arc_api_adapter.py:39 - module reference for future use
PrimitiveStatus  # noqa: F821 - concept_discovery_engine.py:40 - enum for future use
