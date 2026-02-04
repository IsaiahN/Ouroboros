"""
Rung Role Taxonomy - Phase 7.2.

Classifies rungs by their role in the universal problem-solving pattern,
not just their category. This enables:
1. Abstract pattern extraction (process knowledge)
2. Transfer learning between domains
3. Suggesting paths for new game types

The Four Roles:
- ENTRY: Low-friction starting points, orientation, broad coverage
- LEVERAGE: Build on entry points to reach deeper understanding
- COMPOUNDING: Knowledge spreads, connections multiply
- RESOLUTION: Path crystallizes, commit to action

Usage:
    from engines.cognition.rung_roles import RungRole, get_rung_role

    role = get_rung_role("survey")  # Returns RungRole.ENTRY
    phase_role = get_role_for_phase("exploration")  # Returns RungRole.ENTRY
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

import logging
from enum import Enum
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


# =============================================================================
# RUNG ROLE ENUM
# =============================================================================

class RungRole(Enum):
    """
    Roles rungs play in the universal problem-solving pattern.

    From Part 4: Problem-solving follows a universal pattern:
    1. Entry - Find easy starting points
    2. Leverage - Use entry points to reach harder targets
    3. Compounding - Knowledge spreads, connections multiply
    4. Resolution - Path becomes obvious, commit to action
    """
    ENTRY = "entry"              # Low-friction starting points
    LEVERAGE = "leverage"        # Build on entry points to reach harder targets
    COMPOUNDING = "compounding"  # Connections multiply, knowledge spreads
    RESOLUTION = "resolution"    # Path becomes obvious, commit to action

    def __str__(self) -> str:
        return self.value

    @property
    def description(self) -> str:
        """Human-readable description of this role."""
        descriptions = {
            RungRole.ENTRY: "Low-friction starting points for orientation",
            RungRole.LEVERAGE: "Build on entry points for deeper understanding",
            RungRole.COMPOUNDING: "Knowledge spreads, connections multiply",
            RungRole.RESOLUTION: "Path crystallizes, commit to action",
        }
        return descriptions[self]

    @property
    def typical_confidence_range(self) -> tuple:
        """Typical confidence range for rungs in this role."""
        ranges = {
            RungRole.ENTRY: (0.3, 0.6),        # Exploratory, lower confidence
            RungRole.LEVERAGE: (0.5, 0.75),    # Building understanding
            RungRole.COMPOUNDING: (0.6, 0.85), # Confidence growing
            RungRole.RESOLUTION: (0.8, 1.0),   # High confidence for action
        }
        return ranges[self]


# =============================================================================
# RUNG ROLE MAPPING
# =============================================================================

# Map rungs to their primary role in problem-solving
# Based on Part 4 taxonomy analysis
RUNG_ROLE_MAP: Dict[str, RungRole] = {
    # =========================================================================
    # ENTRY RUNGS: Low friction, broad coverage, orientation
    # These rungs provide the initial survey and understanding
    # =========================================================================
    "survey": RungRole.ENTRY,
    "frame_interpretation": RungRole.ENTRY,
    "sparse_grid": RungRole.ENTRY,
    "palette_detection": RungRole.ENTRY,
    "scan_for_goals": RungRole.ENTRY,
    "pattern_recognition": RungRole.ENTRY,
    "novelty_detection": RungRole.ENTRY,
    "boundary_detection": RungRole.ENTRY,
    "object_recognition": RungRole.ENTRY,
    "initial_survey": RungRole.ENTRY,
    "environment_scan": RungRole.ENTRY,
    "attention_guidance": RungRole.ENTRY,

    # =========================================================================
    # LEVERAGE RUNGS: Build on entry points to reach deeper understanding
    # These rungs use initial observations to develop understanding
    # =========================================================================
    "control_tracker": RungRole.LEVERAGE,
    "object_interaction_test": RungRole.LEVERAGE,
    "hypothesis_testing": RungRole.LEVERAGE,
    "event_understanding": RungRole.LEVERAGE,
    "spatial_relationship": RungRole.LEVERAGE,
    "physics_probe": RungRole.LEVERAGE,
    "affordance_detection": RungRole.LEVERAGE,
    "goal_decomposition": RungRole.LEVERAGE,
    "constraint_analysis": RungRole.LEVERAGE,
    "sequence_detection": RungRole.LEVERAGE,
    "temporal_reasoning": RungRole.LEVERAGE,
    "causal_probing": RungRole.LEVERAGE,
    "movement_analysis": RungRole.LEVERAGE,
    "collision_detection": RungRole.LEVERAGE,
    "transformation_detection": RungRole.LEVERAGE,

    # =========================================================================
    # COMPOUNDING RUNGS: Knowledge spreads, connections multiply
    # These rungs connect observations and build understanding
    # =========================================================================
    "rule_transfer": RungRole.COMPOUNDING,
    "abstraction_matching": RungRole.COMPOUNDING,
    "network_wisdom": RungRole.COMPOUNDING,
    "theory_gate": RungRole.COMPOUNDING,
    "causal_chain": RungRole.COMPOUNDING,
    "pattern_synthesis": RungRole.COMPOUNDING,
    "cross_domain_transfer": RungRole.COMPOUNDING,
    "meta_strategy": RungRole.COMPOUNDING,
    "knowledge_integration": RungRole.COMPOUNDING,
    "analogy_mapping": RungRole.COMPOUNDING,
    "principle_extraction": RungRole.COMPOUNDING,
    "generalization": RungRole.COMPOUNDING,
    "working_memory_update": RungRole.COMPOUNDING,
    "scientific_method": RungRole.COMPOUNDING,

    # =========================================================================
    # RESOLUTION RUNGS: Path crystallizes, commit to action
    # These rungs make final decisions and execute actions
    # =========================================================================
    "smart_action_selection": RungRole.RESOLUTION,
    "optimal_sequence": RungRole.RESOLUTION,
    "confident_commit": RungRole.RESOLUTION,
    "action_execution": RungRole.RESOLUTION,
    "final_decision": RungRole.RESOLUTION,
    "action_selection": RungRole.RESOLUTION,
    "sequence_execution": RungRole.RESOLUTION,
    "goal_achievement": RungRole.RESOLUTION,
    "plan_execution": RungRole.RESOLUTION,
    "commit_action": RungRole.RESOLUTION,
    "discovery_exploitation": RungRole.RESOLUTION,
    "exploration_exploitation": RungRole.RESOLUTION,
}


# =============================================================================
# PHASE TO ROLE MAPPING
# =============================================================================

PHASE_ROLE_MAP: Dict[str, RungRole] = {
    "exploration": RungRole.ENTRY,
    "building": RungRole.LEVERAGE,
    "connecting": RungRole.COMPOUNDING,
    "resolving": RungRole.RESOLUTION,
    # Aliases
    "orient": RungRole.ENTRY,
    "investigate": RungRole.LEVERAGE,
    "synthesize": RungRole.COMPOUNDING,
    "act": RungRole.RESOLUTION,
}


# =============================================================================
# ROLE TRANSITIONS
# =============================================================================

# Valid role transitions (from -> to)
# Some transitions are natural progressions, others are backtracking
VALID_ROLE_TRANSITIONS: Dict[RungRole, Set[RungRole]] = {
    RungRole.ENTRY: {RungRole.ENTRY, RungRole.LEVERAGE},
    RungRole.LEVERAGE: {RungRole.ENTRY, RungRole.LEVERAGE, RungRole.COMPOUNDING},
    RungRole.COMPOUNDING: {RungRole.LEVERAGE, RungRole.COMPOUNDING, RungRole.RESOLUTION},
    RungRole.RESOLUTION: {RungRole.COMPOUNDING, RungRole.RESOLUTION},
}

# Transitions that indicate backtracking (need more information)
BACKTRACK_TRANSITIONS: Set[tuple] = {
    (RungRole.LEVERAGE, RungRole.ENTRY),
    (RungRole.COMPOUNDING, RungRole.LEVERAGE),
    (RungRole.COMPOUNDING, RungRole.ENTRY),
    (RungRole.RESOLUTION, RungRole.COMPOUNDING),
    (RungRole.RESOLUTION, RungRole.LEVERAGE),
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_rung_role(rung_name: str) -> RungRole:
    """
    Get the role for a rung.

    Args:
        rung_name: Name of the rung

    Returns:
        RungRole for the rung, defaults to ENTRY if unknown
    """
    return RUNG_ROLE_MAP.get(rung_name, RungRole.ENTRY)


def get_role_for_phase(phase: str) -> RungRole:
    """
    Map problem-solving phase to appropriate rung role.

    Args:
        phase: Phase name (exploration, building, connecting, resolving)

    Returns:
        RungRole for the phase
    """
    return PHASE_ROLE_MAP.get(phase.lower(), RungRole.ENTRY)


def get_rungs_by_role(role: RungRole) -> List[str]:
    """
    Get all rungs with a specific role.

    Args:
        role: The RungRole to filter by

    Returns:
        List of rung names with that role
    """
    return [rung for rung, r in RUNG_ROLE_MAP.items() if r == role]


def is_valid_transition(from_role: RungRole, to_role: RungRole) -> bool:
    """
    Check if a role transition is valid.

    Args:
        from_role: Current role
        to_role: Target role

    Returns:
        True if transition is valid
    """
    return to_role in VALID_ROLE_TRANSITIONS.get(from_role, set())


def is_backtrack_transition(from_role: RungRole, to_role: RungRole) -> bool:
    """
    Check if a transition represents backtracking.

    Args:
        from_role: Current role
        to_role: Target role

    Returns:
        True if this is a backtrack transition
    """
    return (from_role, to_role) in BACKTRACK_TRANSITIONS


def extract_role_sequence(path: List[str]) -> List[RungRole]:
    """
    Extract the role sequence from a concrete path.

    Args:
        path: List of rung names

    Returns:
        List of RungRoles
    """
    return [get_rung_role(rung) for rung in path]


def role_sequence_to_id(roles: List[RungRole]) -> str:
    """
    Convert a role sequence to a pattern ID string.

    Args:
        roles: List of RungRoles

    Returns:
        Pattern ID string (e.g., "ENTRY->LEVERAGE->RESOLUTION")
    """
    return "->".join(role.name for role in roles)


def count_backtrack_transitions(path: List[str]) -> int:
    """
    Count backtrack transitions in a path.

    Args:
        path: List of rung names

    Returns:
        Number of backtrack transitions
    """
    if len(path) < 2:
        return 0

    count = 0
    roles = extract_role_sequence(path)

    for i in range(len(roles) - 1):
        if is_backtrack_transition(roles[i], roles[i + 1]):
            count += 1

    return count


def analyze_path_structure(path: List[str]) -> Dict:
    """
    Analyze the structure of a path.

    Args:
        path: List of rung names

    Returns:
        Dictionary with path analysis
    """
    if not path:
        return {
            'length': 0,
            'roles': [],
            'pattern_id': '',
            'backtrack_count': 0,
            'role_distribution': {},
            'is_progressive': True,
        }

    roles = extract_role_sequence(path)
    pattern_id = role_sequence_to_id(roles)
    backtrack_count = count_backtrack_transitions(path)

    # Count role distribution
    role_distribution = {}
    for role in RungRole:
        role_distribution[role.name] = sum(1 for r in roles if r == role)

    # Check if progressive (no backtracks)
    is_progressive = backtrack_count == 0

    return {
        'length': len(path),
        'roles': [r.name for r in roles],
        'pattern_id': pattern_id,
        'backtrack_count': backtrack_count,
        'role_distribution': role_distribution,
        'is_progressive': is_progressive,
    }


# =============================================================================
# ROLE COMPATIBILITY
# =============================================================================

def get_compatible_roles(epistemic_quadrant: str) -> List[RungRole]:
    """
    Get roles that are compatible with an epistemic quadrant.

    Args:
        epistemic_quadrant: KK, KU, UK, or UU

    Returns:
        List of compatible roles (ordered by preference)
    """
    compatibility = {
        'KK': [RungRole.RESOLUTION, RungRole.COMPOUNDING],  # High confidence, resolve
        'KU': [RungRole.LEVERAGE, RungRole.COMPOUNDING],    # Building understanding
        'UK': [RungRole.ENTRY, RungRole.LEVERAGE],          # Need to explore
        'UU': [RungRole.ENTRY],                             # Start fresh
    }
    return compatibility.get(epistemic_quadrant, [RungRole.ENTRY])


def suggest_next_role(current_role: RungRole, confidence: float) -> RungRole:
    """
    Suggest the next role based on current role and confidence.

    Args:
        current_role: Current role
        confidence: Current confidence level (0-1)

    Returns:
        Suggested next role
    """
    # Low confidence: stay in current phase or backtrack
    if confidence < 0.4:
        if current_role in (RungRole.RESOLUTION, RungRole.COMPOUNDING):
            return RungRole.LEVERAGE  # Backtrack
        return current_role  # Stay

    # Medium confidence: progress one step
    if confidence < 0.7:
        progressions = {
            RungRole.ENTRY: RungRole.LEVERAGE,
            RungRole.LEVERAGE: RungRole.COMPOUNDING,
            RungRole.COMPOUNDING: RungRole.COMPOUNDING,  # Build more
            RungRole.RESOLUTION: RungRole.RESOLUTION,
        }
        return progressions.get(current_role, current_role)

    # High confidence: progress toward resolution
    progressions = {
        RungRole.ENTRY: RungRole.LEVERAGE,
        RungRole.LEVERAGE: RungRole.COMPOUNDING,
        RungRole.COMPOUNDING: RungRole.RESOLUTION,
        RungRole.RESOLUTION: RungRole.RESOLUTION,
    }
    return progressions.get(current_role, RungRole.RESOLUTION)


logger.info(f"[RUNG-ROLES] Loaded {len(RUNG_ROLE_MAP)} rung role mappings")
