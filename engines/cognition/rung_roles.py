"""
Rung Role Taxonomy - Phase 7.2 + H41 Cognitive Phase Mapping.

Two complementary taxonomies:

1. **RungRole** (4-tier): Problem-solving progression
   - ENTRY → LEVERAGE → COMPOUNDING → RESOLUTION

2. **CognitivePhase** (7-phase): Solver cognitive pipeline
   - OBSERVE → CLASSIFY → EXTRACT_GOAL → MAP_EFFECTS → PLAN → EXECUTE → VERIFY
   - Mirrors the universal pattern behind all solver solutions.
   - Used by H41 rung affinity to group learned affinities by phase.

Usage:
    from engines.cognition.rung_roles import (
        RungRole, get_rung_role,
        CognitivePhase, get_cognitive_phase, get_rungs_by_phase,
    )

    role = get_rung_role("survey")           # RungRole.ENTRY
    phase = get_cognitive_phase("survey")    # CognitivePhase.OBSERVE
    plan_rungs = get_rungs_by_phase(CognitivePhase.PLAN)  # [...]
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
# COGNITIVE PHASE ENUM — The 7-Phase Solver Pipeline
# =============================================================================

class CognitivePhase(Enum):
    """
    The 7-phase cognitive pipeline behind all solver solutions.

    OBSERVE → CLASSIFY → EXTRACT_GOAL → MAP_EFFECTS → PLAN → EXECUTE → VERIFY

    Each rung participates primarily in one phase. Context-setter rungs
    (confidence=0.0) are pure phase contributions. Action-proposing rungs
    participate in their phase AND implicitly in EXECUTE.

    Used by H41 rung affinity to report phase-level coverage per game type.
    """
    OBSERVE = "observe"            # Perceive state, detect features
    CLASSIFY = "classify"          # Determine game type, mechanics, problem class
    EXTRACT_GOAL = "extract_goal"  # Identify target state, constraints
    MAP_EFFECTS = "map_effects"    # Learn action → outcome mappings
    PLAN = "plan"                  # Compute action sequence toward goal
    EXECUTE = "execute"            # Select and commit to next action
    VERIFY = "verify"              # Check outcome, track progress, detect errors

    def __str__(self) -> str:
        return self.value

    @property
    def description(self) -> str:
        descriptions = {
            CognitivePhase.OBSERVE: "Perceive game state, extract visual features",
            CognitivePhase.CLASSIFY: "Determine game type and problem class",
            CognitivePhase.EXTRACT_GOAL: "Identify target state and constraints",
            CognitivePhase.MAP_EFFECTS: "Learn what each action does",
            CognitivePhase.PLAN: "Compute optimal action sequence",
            CognitivePhase.EXECUTE: "Select and commit to action",
            CognitivePhase.VERIFY: "Check outcome against prediction",
        }
        return descriptions[self]

    @property
    def maps_to_role(self) -> RungRole:
        """Which RungRole this phase most naturally maps to."""
        mapping = {
            CognitivePhase.OBSERVE: RungRole.ENTRY,
            CognitivePhase.CLASSIFY: RungRole.ENTRY,
            CognitivePhase.EXTRACT_GOAL: RungRole.LEVERAGE,
            CognitivePhase.MAP_EFFECTS: RungRole.LEVERAGE,
            CognitivePhase.PLAN: RungRole.COMPOUNDING,
            CognitivePhase.EXECUTE: RungRole.RESOLUTION,
            CognitivePhase.VERIFY: RungRole.COMPOUNDING,
        }
        return mapping[self]


# =============================================================================
# COGNITIVE PHASE MAP — Every real rung → its primary phase
# =============================================================================

# Maps all actual rung names (from rung registries) to their primary cognitive
# phase. Rungs may contribute to multiple phases, but this records the PRIMARY
# phase where the rung's core logic lives.
COGNITIVE_PHASE_MAP: Dict[str, CognitivePhase] = {
    # -------------------------------------------------------------------------
    # OBSERVE: Perceive state, detect features, scan environment
    # -------------------------------------------------------------------------
    "survey": CognitivePhase.OBSERVE,
    "frame_interpretation": CognitivePhase.OBSERVE,
    "sparse_grid": CognitivePhase.OBSERVE,
    "palette_detection": CognitivePhase.OBSERVE,
    "affordance_detection": CognitivePhase.OBSERVE,
    "visual_analyzer": CognitivePhase.OBSERVE,
    "network_object_inventory": CognitivePhase.OBSERVE,
    "action6_object_exploration": CognitivePhase.OBSERVE,
    "exploration_phase": CognitivePhase.OBSERVE,
    "grid_exploration": CognitivePhase.OBSERVE,
    "control_tracker": CognitivePhase.OBSERVE,
    "questioning_engine": CognitivePhase.OBSERVE,
    "network_exploration_stats": CognitivePhase.OBSERVE,
    "self_trust_boost": CognitivePhase.OBSERVE,

    # -------------------------------------------------------------------------
    # CLASSIFY: Determine game type, problem class, click semantics
    # -------------------------------------------------------------------------
    "game_classifier": CognitivePhase.CLASSIFY,
    "sensation_engine": CognitivePhase.CLASSIFY,
    "two_streams": CognitivePhase.CLASSIFY,

    # -------------------------------------------------------------------------
    # EXTRACT_GOAL: Identify target state, constraints, subgoals
    # -------------------------------------------------------------------------
    "solver_goal_extraction": CognitivePhase.EXTRACT_GOAL,
    "constraint_decoder": CognitivePhase.EXTRACT_GOAL,
    "interactable_tile_discovery": CognitivePhase.EXTRACT_GOAL,
    "goal_relationship_modeling": CognitivePhase.EXTRACT_GOAL,
    "valence_goals": CognitivePhase.EXTRACT_GOAL,
    "subgoal_planning": CognitivePhase.EXTRACT_GOAL,

    # -------------------------------------------------------------------------
    # MAP_EFFECTS: Learn action → outcome, build causal model
    # -------------------------------------------------------------------------
    "causal_click_mapping": CognitivePhase.MAP_EFFECTS,
    "click_behavior_learning": CognitivePhase.MAP_EFFECTS,
    "spatial_relationship": CognitivePhase.MAP_EFFECTS,
    "event_understanding": CognitivePhase.MAP_EFFECTS,
    "object_color_targeting": CognitivePhase.MAP_EFFECTS,
    "hypothesis_system": CognitivePhase.MAP_EFFECTS,
    "hypothesis_testing": CognitivePhase.MAP_EFFECTS,
    "scientific_method": CognitivePhase.MAP_EFFECTS,
    "assumption_formation": CognitivePhase.MAP_EFFECTS,
    "belief_system": CognitivePhase.MAP_EFFECTS,
    "resonance_detector": CognitivePhase.MAP_EFFECTS,
    "symbolic_tracker": CognitivePhase.MAP_EFFECTS,
    "map_intel_collision": CognitivePhase.MAP_EFFECTS,
    "effect_prediction": CognitivePhase.MAP_EFFECTS,

    # -------------------------------------------------------------------------
    # PLAN: Compute action sequence, solve constraints, navigate
    # -------------------------------------------------------------------------
    "constraint_satisfaction": CognitivePhase.PLAN,
    "wall_aware_navigation": CognitivePhase.PLAN,
    "spatial_map": CognitivePhase.PLAN,
    "controlled_movement_planning": CognitivePhase.PLAN,
    "trigger_sequences": CognitivePhase.PLAN,
    "theory_gate": CognitivePhase.PLAN,
    "metacognitive_prediction": CognitivePhase.PLAN,
    "deliberation_system": CognitivePhase.PLAN,
    "i_thread": CognitivePhase.PLAN,
    "budget_aware_planning": CognitivePhase.PLAN,

    # -------------------------------------------------------------------------
    # EXECUTE: Select action, commit, fallback strategies
    # -------------------------------------------------------------------------
    "smart_action_selection": CognitivePhase.EXECUTE,
    "three_try_sequence": CognitivePhase.EXECUTE,
    "discovery_exploitation": CognitivePhase.EXECUTE,
    "embedding_suggestion": CognitivePhase.EXECUTE,
    "embedding_matcher": CognitivePhase.EXECUTE,
    "network_wisdom": CognitivePhase.EXECUTE,
    "network_sharing": CognitivePhase.EXECUTE,
    "primitive_suggester": CognitivePhase.EXECUTE,
    "state_matching": CognitivePhase.EXECUTE,
    "multi_stage_matching": CognitivePhase.EXECUTE,
    "replay_learning": CognitivePhase.EXECUTE,
    "few_shot_invariants": CognitivePhase.EXECUTE,
    "few_shot_relations": CognitivePhase.EXECUTE,
    "abstraction_templates": CognitivePhase.EXECUTE,

    # -------------------------------------------------------------------------
    # VERIFY: Check outcome, track progress, detect errors
    # -------------------------------------------------------------------------
    "goal_progress": CognitivePhase.VERIFY,
    "near_miss_analyzer": CognitivePhase.VERIFY,
    "completion_prediction": CognitivePhase.VERIFY,
    "rule_transfer": CognitivePhase.VERIFY,
    "frontier_topology": CognitivePhase.VERIFY,
    "frontier_checkpoint": CognitivePhase.VERIFY,
    "theory_contradiction": CognitivePhase.VERIFY,
    "metacognitive_elimination": CognitivePhase.VERIFY,
    "contextual_failure": CognitivePhase.VERIFY,
    "action_outcome_verifier": CognitivePhase.VERIFY,

    # -------------------------------------------------------------------------
    # SAFETY RUNGS: Cross-cutting (mapped to VERIFY — they check/filter)
    # -------------------------------------------------------------------------
    "death_avoidance": CognitivePhase.VERIFY,
    "prior_lessons": CognitivePhase.VERIFY,
    "three_layer_filter": CognitivePhase.VERIFY,
    "pariah_avoidance": CognitivePhase.VERIFY,
    "terminal_pattern": CognitivePhase.VERIFY,
    "destructive_action_detection": CognitivePhase.VERIFY,
    "viral_package_weights": CognitivePhase.EXECUTE,

    # -------------------------------------------------------------------------
    # EMERGENCY: Always-first (mapped to OBSERVE — they perceive danger)
    # -------------------------------------------------------------------------
    "infinite_loop_breaker": CognitivePhase.OBSERVE,
    "coordinate_oscillation": CognitivePhase.OBSERVE,

    # -------------------------------------------------------------------------
    # BUDGET/META: Resource tracking (mapped to PLAN — they constrain)
    # -------------------------------------------------------------------------
    "frustration_detection": CognitivePhase.VERIFY,
    "breakthrough_budget": CognitivePhase.PLAN,
    "regulatory_signal": CognitivePhase.PLAN,
    "imagination_budget": CognitivePhase.PLAN,
}


# =============================================================================
# RUNG ROLE MAPPING — Grounded to actual rung names
# =============================================================================

# Map rungs to their primary role in problem-solving.
# All entries correspond to actual registered rung names.
RUNG_ROLE_MAP: Dict[str, RungRole] = {
    # ENTRY: Orientation, perception, broad survey
    "survey": RungRole.ENTRY,
    "frame_interpretation": RungRole.ENTRY,
    "sparse_grid": RungRole.ENTRY,
    "palette_detection": RungRole.ENTRY,
    "affordance_detection": RungRole.ENTRY,
    "visual_analyzer": RungRole.ENTRY,
    "network_object_inventory": RungRole.ENTRY,
    "action6_object_exploration": RungRole.ENTRY,
    "exploration_phase": RungRole.ENTRY,
    "grid_exploration": RungRole.ENTRY,
    "questioning_engine": RungRole.ENTRY,
    "game_classifier": RungRole.ENTRY,
    "control_tracker": RungRole.ENTRY,
    "network_exploration_stats": RungRole.ENTRY,
    "self_trust_boost": RungRole.ENTRY,
    "infinite_loop_breaker": RungRole.ENTRY,
    "coordinate_oscillation": RungRole.ENTRY,
    "sensation_engine": RungRole.ENTRY,
    "two_streams": RungRole.ENTRY,

    # LEVERAGE: Build understanding, test hypotheses, map effects
    "solver_goal_extraction": RungRole.LEVERAGE,
    "constraint_decoder": RungRole.LEVERAGE,
    "interactable_tile_discovery": RungRole.LEVERAGE,
    "goal_relationship_modeling": RungRole.LEVERAGE,
    "causal_click_mapping": RungRole.LEVERAGE,
    "click_behavior_learning": RungRole.LEVERAGE,
    "spatial_relationship": RungRole.LEVERAGE,
    "event_understanding": RungRole.LEVERAGE,
    "object_color_targeting": RungRole.LEVERAGE,
    "hypothesis_system": RungRole.LEVERAGE,
    "hypothesis_testing": RungRole.LEVERAGE,
    "scientific_method": RungRole.LEVERAGE,
    "assumption_formation": RungRole.LEVERAGE,
    "belief_system": RungRole.LEVERAGE,
    "resonance_detector": RungRole.LEVERAGE,
    "symbolic_tracker": RungRole.LEVERAGE,
    "map_intel_collision": RungRole.LEVERAGE,
    "effect_prediction": RungRole.LEVERAGE,
    "valence_goals": RungRole.LEVERAGE,
    "subgoal_planning": RungRole.LEVERAGE,

    # COMPOUNDING: Connect knowledge, plan sequences
    "constraint_satisfaction": RungRole.COMPOUNDING,
    "wall_aware_navigation": RungRole.COMPOUNDING,
    "spatial_map": RungRole.COMPOUNDING,
    "controlled_movement_planning": RungRole.COMPOUNDING,
    "trigger_sequences": RungRole.COMPOUNDING,
    "theory_gate": RungRole.COMPOUNDING,
    "metacognitive_prediction": RungRole.COMPOUNDING,
    "deliberation_system": RungRole.COMPOUNDING,
    "i_thread": RungRole.COMPOUNDING,
    "rule_transfer": RungRole.COMPOUNDING,
    "near_miss_analyzer": RungRole.COMPOUNDING,
    "completion_prediction": RungRole.COMPOUNDING,
    "frontier_topology": RungRole.COMPOUNDING,
    "frontier_checkpoint": RungRole.COMPOUNDING,
    "goal_progress": RungRole.COMPOUNDING,
    "action_outcome_verifier": RungRole.COMPOUNDING,
    "frustration_detection": RungRole.COMPOUNDING,

    # RESOLUTION: Select action, commit, exploit knowledge
    "smart_action_selection": RungRole.RESOLUTION,
    "three_try_sequence": RungRole.RESOLUTION,
    "discovery_exploitation": RungRole.RESOLUTION,
    "embedding_suggestion": RungRole.RESOLUTION,
    "embedding_matcher": RungRole.RESOLUTION,
    "network_wisdom": RungRole.RESOLUTION,
    "network_sharing": RungRole.RESOLUTION,
    "primitive_suggester": RungRole.RESOLUTION,
    "state_matching": RungRole.RESOLUTION,
    "multi_stage_matching": RungRole.RESOLUTION,
    "replay_learning": RungRole.RESOLUTION,
    "few_shot_invariants": RungRole.RESOLUTION,
    "few_shot_relations": RungRole.RESOLUTION,
    "abstraction_templates": RungRole.RESOLUTION,
    "death_avoidance": RungRole.RESOLUTION,
    "prior_lessons": RungRole.RESOLUTION,
    "three_layer_filter": RungRole.RESOLUTION,
    "pariah_avoidance": RungRole.RESOLUTION,
    "terminal_pattern": RungRole.RESOLUTION,
    "destructive_action_detection": RungRole.RESOLUTION,
    "budget_aware_planning": RungRole.RESOLUTION,
    "theory_contradiction": RungRole.RESOLUTION,
    "viral_package_weights": RungRole.RESOLUTION,
    "metacognitive_elimination": RungRole.RESOLUTION,
    "contextual_failure": RungRole.RESOLUTION,
    "breakthrough_budget": RungRole.RESOLUTION,
    "regulatory_signal": RungRole.RESOLUTION,
    "imagination_budget": RungRole.RESOLUTION,
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


def get_cognitive_phase(rung_name: str) -> CognitivePhase:
    """Get the primary cognitive phase for a rung.

    Falls back to EXECUTE if rung is unknown (action-proposing by default).
    """
    return COGNITIVE_PHASE_MAP.get(rung_name, CognitivePhase.EXECUTE)


def get_rungs_by_phase(phase: CognitivePhase) -> List[str]:
    """Get all rungs in a specific cognitive phase."""
    return [rung for rung, p in COGNITIVE_PHASE_MAP.items() if p == phase]


def get_phase_coverage() -> Dict[str, int]:
    """Get rung count per cognitive phase — used by H41 affinity summary."""
    counts: Dict[str, int] = {}
    for phase in CognitivePhase:
        counts[phase.value] = sum(
            1 for p in COGNITIVE_PHASE_MAP.values() if p == phase
        )
    return counts


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


logger.info(
    f"[RUNG-ROLES] Loaded {len(RUNG_ROLE_MAP)} role + "
    f"{len(COGNITIVE_PHASE_MAP)} phase mappings"
)
