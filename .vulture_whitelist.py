# Vulture Whitelist - Intentionally Unused Code
# Run vulture with: python -m vulture . .vulture_whitelist.py --min-confidence 80
#
# This file tells vulture to ignore code that LOOKS unused but is intentional.
# Categories:
#   1. Context manager signatures (__aexit__ params)
#   2. Placeholder methods (documented as future implementation)
#   3. Seed primitives (partial implementations with planned variables)
#   4. Conditional imports (assigned None in except blocks)

# type: ignore  # noqa - This file is for vulture, not for Pylance

from typing import Any

_: Any = None  # Placeholder for attribute access

# =============================================================================
# CONTEXT MANAGER SIGNATURES (Required by Python protocol)
# =============================================================================
# arc_api_client.py:169 - __aexit__ signature
exc_type: Any  # unused-variable
exc_val: Any   # unused-variable  
exc_tb: Any    # unused-variable

# =============================================================================
# PARAMETER PLACEHOLDERS (Documented for future use)
# =============================================================================
# core_gameplay.py:2781 - _get_map_intelligence parameter
# This parameter is declared for future position-specific intelligence queries
# but the current implementation uses frame-wide analysis only.
target_position: Any  # unused-variable

# =============================================================================
# DATABASE PLACEHOLDER METHODS
# =============================================================================
# database_interface.py:1739, 1744 - Placeholder methods
since_date: Any   # unused-variable
before_date: Any  # unused-variable

# =============================================================================
# SEED PRIMITIVES - Remaining Partial Implementations
# =============================================================================
# These seed primitive parameters are intentionally unused - they are placeholders
# for future implementation or have limited utility in the current system.

# Note: Most seed primitive parameters have been fixed and properly implemented.
# The remaining items below are edge cases or optional parameters.

# =============================================================================
# CONDITIONAL IMPORTS (Used when available)
# =============================================================================
# These are imported and used conditionally. Vulture can't trace the usage
# because they're behind AVAILABLE flags.

# autonomous_evolution_runner.py:116
get_metrics_capture: Any
reset_metrics_capture: Any
record_game_start: Any
record_game_end: Any
record_cods: Any
record_stuck: Any
get_reasoning_diagnostics: Any
ReasoningLogCapture: Any

# autonomous_evolution_runner.py:77
PariahValidator: Any  # Used via run_pariah_validation

# core_gameplay.py:101
GoalEvaluator: Any
SymbolicWorldModel: Any

# core_gameplay.py:188
ReplayLearningContext: Any

# core_gameplay.py:198
UIDetector: Any

# agent_self_model.py:25
IThreadType: Any  # TYPE_CHECKING import
