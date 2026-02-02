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
