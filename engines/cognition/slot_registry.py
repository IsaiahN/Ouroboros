"""
Slot Registry - Defines all 87 blackboard slots with type information.

Phase 1 Implementation - Cognitive Routing

This module provides SLOT_DEFINITIONS, a comprehensive registry of all
blackboard slots identified from the rung dependency matrix. Each slot
has metadata including:
- category: Which cognitive category (orientation, identity, hypothesis, etc.)
- expected_type: Python type hint for validation
- description: Human-readable description
- written_by: Rungs that write to this slot
- read_by: Rungs that read from this slot

The registry enables:
1. Static type validation at slot write time
2. Automatic slot creation with correct categories
3. Documentation of data flow through the system
4. Discovery of missing/orphaned slots
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

from typing import Any, Dict, List, Optional

from engines.cognition.blackboard import SlotCategory

# =============================================================================
# SLOT DEFINITIONS REGISTRY
# =============================================================================

SLOT_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    # =========================================================================
    # ORIENTATION SLOTS - Initial game state understanding
    # =========================================================================
    "survey": {
        "category": SlotCategory.ORIENTATION,
        "expected_type": dict,
        "description": "Grid analysis result from survey rung",
        "written_by": ["survey"],
        "read_by": ["embedding_suggestion", "scientific_method", "primitive_suggester",
                   "exploration_phase", "smart_action_selection", "visual_analyzer",
                   "network_object_inventory", "action6_object_exploration",
                   "deliberation_system", "assumption_formation", "few_shot_invariants",
                   "few_shot_relations"]
    },
    "survey_complete": {
        "category": SlotCategory.ORIENTATION,
        "expected_type": bool,
        "description": "Whether survey has been completed this frame",
        "written_by": ["survey"],
        "read_by": []
    },
    "detected_palette": {
        "category": SlotCategory.ORIENTATION,
        "expected_type": dict,
        "description": "Detected color palette and legend blocks",
        "written_by": ["palette_detection"],
        "read_by": ["spatial_relationship", "abstraction_templates"]
    },
    "extracted_objects": {
        "category": SlotCategory.ORIENTATION,
        "expected_type": list,
        "description": "List of extracted game objects",
        "written_by": ["palette_detection"],
        "read_by": ["spatial_relationship", "network_object_inventory",
                   "action6_object_exploration", "symbolic_tracker", "valence_goals"]
    },
    "detected_transformations": {
        "category": SlotCategory.ORIENTATION,
        "expected_type": list,
        "description": "Detected transformation patterns",
        "written_by": ["palette_detection"],
        "read_by": ["resonance_detector", "symbolic_tracker"]
    },
    "sparse_grid": {
        "category": SlotCategory.ORIENTATION,
        "expected_type": dict,
        "description": "Sparse grid representation for efficient pattern matching",
        "written_by": ["sparse_grid"],
        "read_by": ["primitive_suggester", "exploration_phase", "frontier_topology",
                   "frontier_checkpoint", "map_intel_collision", "abstraction_templates",
                   "state_matching", "subgoal_planning", "visual_analyzer",
                   "grid_exploration", "imagination_budget"]
    },
    "sparse_hash": {
        "category": SlotCategory.ORIENTATION,
        "expected_type": str,
        "description": "Hash of sparse grid for quick state comparison",
        "written_by": ["sparse_grid"],
        "read_by": ["multi_stage_matching", "state_matching", "embedding_matcher",
                   "resonance_detector"]
    },
    "sparse_cell_count": {
        "category": SlotCategory.ORIENTATION,
        "expected_type": int,
        "description": "Count of non-empty cells in sparse grid",
        "written_by": ["sparse_grid"],
        "read_by": []
    },
    "sparse_colors": {
        "category": SlotCategory.ORIENTATION,
        "expected_type": list,
        "description": "List of colors present in sparse grid",
        "written_by": ["sparse_grid"],
        "read_by": []
    },
    "sparse_components": {
        "category": SlotCategory.ORIENTATION,
        "expected_type": list,
        "description": "Connected components in sparse grid",
        "written_by": ["sparse_grid"],
        "read_by": []
    },
    "sparse_diff": {
        "category": SlotCategory.ORIENTATION,
        "expected_type": dict,
        "description": "Difference from previous sparse grid",
        "written_by": ["sparse_grid"],
        "read_by": ["trigger_sequences"]
    },
    "likely_physics_game": {
        "category": SlotCategory.ORIENTATION,
        "expected_type": bool,
        "description": "Whether game appears to be physics-based",
        "written_by": ["frame_interpretation"],
        "read_by": []
    },
    "expect_large_deltas": {
        "category": SlotCategory.ORIENTATION,
        "expected_type": bool,
        "description": "Whether large frame-to-frame changes expected",
        "written_by": ["frame_interpretation"],
        "read_by": []
    },
    "detected_process_type": {
        "category": SlotCategory.ORIENTATION,
        "expected_type": str,
        "description": "Type of game process (direct_control, physics, puzzle)",
        "written_by": ["frame_interpretation"],
        "read_by": []
    },
    "likely_direct_control": {
        "category": SlotCategory.ORIENTATION,
        "expected_type": bool,
        "description": "Whether agent likely has direct object control",
        "written_by": ["frame_interpretation"],
        "read_by": []
    },
    "visual_features": {
        "category": SlotCategory.ORIENTATION,
        "expected_type": dict,
        "description": "Extracted visual features (edges, patterns)",
        "written_by": ["visual_analyzer"],
        "read_by": []
    },
    "symmetry_info": {
        "category": SlotCategory.ORIENTATION,
        "expected_type": dict,
        "description": "Detected symmetry information",
        "written_by": ["visual_analyzer"],
        "read_by": []
    },
    "color_blocks": {
        "category": SlotCategory.ORIENTATION,
        "expected_type": list,
        "description": "Contiguous color block regions",
        "written_by": ["visual_analyzer"],
        "read_by": []
    },
    "object_inventory": {
        "category": SlotCategory.ORIENTATION,
        "expected_type": dict,
        "description": "Network-shared object inventory",
        "written_by": ["network_object_inventory"],
        "read_by": []
    },
    "known_objects": {
        "category": SlotCategory.ORIENTATION,
        "expected_type": list,
        "description": "List of known object types",
        "written_by": ["network_object_inventory"],
        "read_by": []
    },

    # =========================================================================
    # IDENTITY SLOTS - Self-model and control
    # =========================================================================
    "controlled_objects": {
        "category": SlotCategory.IDENTITY,
        "expected_type": list,
        "description": "Objects the agent controls",
        "written_by": ["control_tracker"],
        "read_by": ["frontier_topology"]
    },
    "primary_control": {
        "category": SlotCategory.IDENTITY,
        "expected_type": dict,
        "description": "Primary controlled object details",
        "written_by": ["control_tracker"],
        "read_by": []
    },
    "blocking_questions": {
        "category": SlotCategory.IDENTITY,
        "expected_type": list,
        "description": "Questions that BLOCK action selection",
        "written_by": ["questioning_engine"],
        "read_by": []
    },
    "allowed_actions": {
        "category": SlotCategory.IDENTITY,
        "expected_type": list,
        "description": "Actions currently allowed",
        "written_by": ["questioning_engine"],
        "read_by": []
    },

    # =========================================================================
    # HYPOTHESIS SLOTS - Beliefs, theories, predictions
    # =========================================================================
    "active_beliefs": {
        "category": SlotCategory.HYPOTHESIS,
        "expected_type": list,
        "description": "Currently active agent beliefs",
        "written_by": ["belief_system"],
        "read_by": ["theory_gate", "theory_contradiction", "network_sharing", "rule_transfer"]
    },
    "untested_hypotheses": {
        "category": SlotCategory.HYPOTHESIS,
        "expected_type": list,
        "description": "Hypotheses awaiting testing",
        "written_by": ["hypothesis_system"],
        "read_by": ["hypothesis_testing"]
    },
    "hypothesis_action": {
        "category": SlotCategory.HYPOTHESIS,
        "expected_type": int,
        "description": "Action suggested by hypothesis testing",
        "written_by": ["hypothesis_system"],
        "read_by": ["theory_gate"]
    },
    "causal_model": {
        "category": SlotCategory.HYPOTHESIS,
        "expected_type": dict,
        "description": "Causal world model from frame changes",
        "written_by": ["event_understanding"],
        "read_by": []
    },
    "productive_events": {
        "category": SlotCategory.HYPOTHESIS,
        "expected_type": list,
        "description": "Events that led to positive outcomes",
        "written_by": ["event_understanding"],
        "read_by": []
    },
    "event_history": {
        "category": SlotCategory.HYPOTHESIS,
        "expected_type": list,
        "description": "History of significant events",
        "written_by": ["event_understanding"],
        "read_by": []
    },
    "click_patterns": {
        "category": SlotCategory.HYPOTHESIS,
        "expected_type": dict,
        "description": "Detected click effect patterns",
        "written_by": ["spatial_relationship"],
        "read_by": []
    },
    "spatial_rules": {
        "category": SlotCategory.HYPOTHESIS,
        "expected_type": list,
        "description": "Spatial relationship rules",
        "written_by": ["spatial_relationship"],
        "read_by": []
    },
    "experiment_action": {
        "category": SlotCategory.HYPOTHESIS,
        "expected_type": int,
        "description": "Action for systematic experimentation",
        "written_by": ["scientific_method"],
        "read_by": []
    },
    "control_variables": {
        "category": SlotCategory.HYPOTHESIS,
        "expected_type": list,
        "description": "Variables being controlled in experiment",
        "written_by": ["scientific_method"],
        "read_by": []
    },
    "stream_a_action": {
        "category": SlotCategory.HYPOTHESIS,
        "expected_type": int,
        "description": "Action from Stream A (private experience)",
        "written_by": ["two_streams"],
        "read_by": ["i_thread", "self_trust_boost"]
    },
    "stream_b_action": {
        "category": SlotCategory.HYPOTHESIS,
        "expected_type": int,
        "description": "Action from Stream B (collective wisdom)",
        "written_by": ["two_streams"],
        "read_by": ["i_thread", "self_trust_boost"]
    },
    "integrated_action": {
        "category": SlotCategory.HYPOTHESIS,
        "expected_type": int,
        "description": "Integrated Stream A/B action",
        "written_by": ["two_streams"],
        "read_by": []
    },
    "click_rules": {
        "category": SlotCategory.HYPOTHESIS,
        "expected_type": dict,
        "description": "Learned click behavior rules",
        "written_by": ["click_behavior_learning"],
        "read_by": ["trigger_sequences"]
    },
    "collectible_patterns": {
        "category": SlotCategory.HYPOTHESIS,
        "expected_type": list,
        "description": "Detected collectible patterns",
        "written_by": ["click_behavior_learning"],
        "read_by": []
    },
    "trigger_chains": {
        "category": SlotCategory.HYPOTHESIS,
        "expected_type": list,
        "description": "Trigger chain sequences",
        "written_by": ["trigger_sequences"],
        "read_by": []
    },
    "trigger_action": {
        "category": SlotCategory.HYPOTHESIS,
        "expected_type": int,
        "description": "Action from trigger learning",
        "written_by": ["trigger_sequences"],
        "read_by": []
    },
    "key_lock_pairs": {
        "category": SlotCategory.HYPOTHESIS,
        "expected_type": list,
        "description": "Detected key/lock symbolic pairs",
        "written_by": ["symbolic_tracker"],
        "read_by": []
    },
    "symbolic_action": {
        "category": SlotCategory.HYPOTHESIS,
        "expected_type": int,
        "description": "Action from symbolic matching",
        "written_by": ["symbolic_tracker"],
        "read_by": []
    },
    "good_objects": {
        "category": SlotCategory.HYPOTHESIS,
        "expected_type": list,
        "description": "Objects with positive valence",
        "written_by": ["valence_goals"],
        "read_by": []
    },
    "bad_objects": {
        "category": SlotCategory.HYPOTHESIS,
        "expected_type": list,
        "description": "Objects with negative valence",
        "written_by": ["valence_goals"],
        "read_by": []
    },
    "goal_objects": {
        "category": SlotCategory.HYPOTHESIS,
        "expected_type": list,
        "description": "Detected goal objects",
        "written_by": ["valence_goals"],
        "read_by": []
    },
    "test_action": {
        "category": SlotCategory.HYPOTHESIS,
        "expected_type": int,
        "description": "Action for hypothesis testing",
        "written_by": ["hypothesis_testing"],
        "read_by": []
    },
    "hypothesis_under_test": {
        "category": SlotCategory.HYPOTHESIS,
        "expected_type": dict,
        "description": "Currently tested hypothesis",
        "written_by": ["hypothesis_testing"],
        "read_by": []
    },
    "new_assumptions": {
        "category": SlotCategory.HYPOTHESIS,
        "expected_type": list,
        "description": "Newly formed assumptions",
        "written_by": ["assumption_formation"],
        "read_by": []
    },
    "assumption_confidence": {
        "category": SlotCategory.HYPOTHESIS,
        "expected_type": float,
        "description": "Confidence in current assumptions",
        "written_by": ["assumption_formation"],
        "read_by": []
    },

    # =========================================================================
    # EXPLOITATION SLOTS - Sequences, checkpoints, navigation
    # =========================================================================
    "applied_lessons": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": list,
        "description": "Lessons applied this cycle",
        "written_by": ["prior_lessons"],
        "read_by": []
    },
    "lesson_weights": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": dict,
        "description": "Weight adjustments from lessons",
        "written_by": ["prior_lessons"],
        "read_by": []
    },
    "discovery_action": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": int,
        "description": "Action for discovery mode",
        "written_by": ["discovery_exploitation"],
        "read_by": []
    },
    "exploitation_action": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": int,
        "description": "Action for exploitation mode",
        "written_by": ["discovery_exploitation"],
        "read_by": []
    },
    "embedding_action": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": int,
        "description": "Action from embedding similarity",
        "written_by": ["embedding_suggestion"],
        "read_by": []
    },
    "embedding_confidence": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": float,
        "description": "Confidence in embedding suggestion",
        "written_by": ["embedding_suggestion"],
        "read_by": []
    },
    "network_action": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": int,
        "description": "Action from network wisdom",
        "written_by": ["network_wisdom"],
        "read_by": []
    },
    "network_confidence": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": float,
        "description": "Confidence in network suggestion",
        "written_by": ["network_wisdom"],
        "read_by": []
    },
    "primitive_action": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": int,
        "description": "Action from primitive suggester",
        "written_by": ["primitive_suggester"],
        "read_by": []
    },
    "primitive_name": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": str,
        "description": "Name of applied primitive",
        "written_by": ["primitive_suggester"],
        "read_by": []
    },
    "exploration_action": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": int,
        "description": "Action for exploration",
        "written_by": ["exploration_phase"],
        "read_by": []
    },
    "frontier_cells": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": list,
        "description": "Frontier cells for exploration",
        "written_by": ["exploration_phase"],
        "read_by": []
    },
    "topology_action": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": int,
        "description": "Action from topology analysis",
        "written_by": ["frontier_topology"],
        "read_by": []
    },
    "reachable_cells": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": list,
        "description": "Currently reachable cells",
        "written_by": ["frontier_topology"],
        "read_by": []
    },
    "checkpoint_path": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": list,
        "description": "Path via checkpoints",
        "written_by": ["frontier_checkpoint"],
        "read_by": []
    },
    "frontier_target": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": tuple,
        "description": "Current frontier target",
        "written_by": ["frontier_checkpoint"],
        "read_by": []
    },
    "template_action": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": int,
        "description": "Action from template matching",
        "written_by": ["abstraction_templates"],
        "read_by": []
    },
    "matched_template": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": str,
        "description": "Name of matched template",
        "written_by": ["abstraction_templates"],
        "read_by": []
    },
    "invariant_action": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": int,
        "description": "Action from invariant detection",
        "written_by": ["few_shot_invariants"],
        "read_by": []
    },
    "detected_invariants": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": list,
        "description": "Detected control invariants",
        "written_by": ["few_shot_invariants"],
        "read_by": []
    },
    "relation_action": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": int,
        "description": "Action from relation detection",
        "written_by": ["few_shot_relations"],
        "read_by": []
    },
    "detected_relations": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": list,
        "description": "Detected relations",
        "written_by": ["few_shot_relations"],
        "read_by": []
    },
    "sequence_action": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": int,
        "description": "Action from sequence following",
        "written_by": ["three_try_sequence"],
        "read_by": []
    },
    "sequence_position": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": int,
        "description": "Current position in sequence",
        "written_by": ["three_try_sequence"],
        "read_by": []
    },
    "matched_stage": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": str,
        "description": "Matched multi-stage identifier",
        "written_by": ["multi_stage_matching"],
        "read_by": []
    },
    "stage_action": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": int,
        "description": "Action from stage matching",
        "written_by": ["multi_stage_matching"],
        "read_by": []
    },
    "embedding_match": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": dict,
        "description": "Best embedding match result",
        "written_by": ["embedding_matcher"],
        "read_by": []
    },
    "similar_states": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": list,
        "description": "States similar to current",
        "written_by": ["embedding_matcher"],
        "read_by": []
    },
    "shared_hypothesis": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": dict,
        "description": "Hypothesis shared with network",
        "written_by": ["network_sharing"],
        "read_by": []
    },
    "network_strategy": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": dict,
        "description": "Strategy from network",
        "written_by": ["network_sharing"],
        "read_by": []
    },
    "transferred_rules": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": list,
        "description": "Rules transferred from other games",
        "written_by": ["rule_transfer"],
        "read_by": []
    },
    "transfer_action": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": int,
        "description": "Action from rule transfer",
        "written_by": ["rule_transfer"],
        "read_by": []
    },
    "matched_state": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": str,
        "description": "Matched state identifier",
        "written_by": ["state_matching"],
        "read_by": []
    },
    "state_action": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": int,
        "description": "Action from state matching",
        "written_by": ["state_matching"],
        "read_by": []
    },
    "subgoal_action": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": int,
        "description": "Action toward current subgoal",
        "written_by": ["subgoal_planning"],
        "read_by": []
    },
    "current_subgoal": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": tuple,
        "description": "Current active subgoal",
        "written_by": ["subgoal_planning"],
        "read_by": []
    },
    "subgoal_path": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": list,
        "description": "Path to current subgoal",
        "written_by": ["subgoal_planning"],
        "read_by": []
    },
    "grid_action": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": int,
        "description": "Action for grid exploration",
        "written_by": ["grid_exploration"],
        "read_by": []
    },
    "unexplored_cells": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": list,
        "description": "Cells not yet explored",
        "written_by": ["grid_exploration"],
        "read_by": []
    },
    "click_target": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": tuple,
        "description": "Target for click action",
        "written_by": ["action6_object_exploration"],
        "read_by": ["click_behavior_learning"]
    },
    "click_action": {
        "category": SlotCategory.EXPLOITATION,
        "expected_type": int,
        "description": "Click action (ACTION6)",
        "written_by": ["action6_object_exploration"],
        "read_by": []
    },

    # =========================================================================
    # FILTER SLOTS - Safety, avoidance, constraints
    # =========================================================================
    "death_weights": {
        "category": SlotCategory.FILTER,
        "expected_type": dict,
        "description": "Position-bucket death pattern weights",
        "written_by": ["death_avoidance"],
        "read_by": ["three_layer_filter"]
    },
    "avoided_positions": {
        "category": SlotCategory.FILTER,
        "expected_type": list,
        "description": "Positions to avoid",
        "written_by": ["death_avoidance"],
        "read_by": []
    },
    "collision_map": {
        "category": SlotCategory.FILTER,
        "expected_type": dict,
        "description": "Map of collision points",
        "written_by": ["map_intel_collision"],
        "read_by": []
    },
    "safe_directions": {
        "category": SlotCategory.FILTER,
        "expected_type": list,
        "description": "Safe movement directions",
        "written_by": ["map_intel_collision"],
        "read_by": []
    },
    "theory_aligned_actions": {
        "category": SlotCategory.FILTER,
        "expected_type": list,
        "description": "Actions aligned with current theory",
        "written_by": ["theory_gate"],
        "read_by": []
    },
    "theory_blocked_actions": {
        "category": SlotCategory.FILTER,
        "expected_type": list,
        "description": "Actions blocked by theory",
        "written_by": ["theory_gate"],
        "read_by": ["three_layer_filter"]
    },
    "contradicted_actions": {
        "category": SlotCategory.FILTER,
        "expected_type": list,
        "description": "Actions contradicting theory",
        "written_by": ["theory_contradiction"],
        "read_by": []
    },
    "filtered_actions": {
        "category": SlotCategory.FILTER,
        "expected_type": list,
        "description": "Final filtered action set",
        "written_by": ["three_layer_filter"],
        "read_by": []
    },
    "filter_reasons": {
        "category": SlotCategory.FILTER,
        "expected_type": dict,
        "description": "Reasons for action filtering",
        "written_by": ["three_layer_filter"],
        "read_by": []
    },
    "pariah_actions": {
        "category": SlotCategory.FILTER,
        "expected_type": list,
        "description": "Actions marked as pariahs",
        "written_by": ["pariah_avoidance"],
        "read_by": ["three_layer_filter"]
    },
    "pariah_decay": {
        "category": SlotCategory.FILTER,
        "expected_type": dict,
        "description": "Decay weights for pariah actions",
        "written_by": ["pariah_avoidance"],
        "read_by": []
    },
    "terminal_patterns": {
        "category": SlotCategory.FILTER,
        "expected_type": list,
        "description": "Detected terminal state patterns",
        "written_by": ["terminal_pattern"],
        "read_by": []
    },
    "terminal_weights": {
        "category": SlotCategory.FILTER,
        "expected_type": dict,
        "description": "Weights for terminal pattern avoidance",
        "written_by": ["terminal_pattern"],
        "read_by": []
    },
    "failure_context": {
        "category": SlotCategory.FILTER,
        "expected_type": dict,
        "description": "Context of recent failures",
        "written_by": ["contextual_failure"],
        "read_by": []
    },
    "avoided_contexts": {
        "category": SlotCategory.FILTER,
        "expected_type": list,
        "description": "Contexts to avoid",
        "written_by": ["contextual_failure"],
        "read_by": []
    },
    "loop_detected": {
        "category": SlotCategory.FILTER,
        "expected_type": bool,
        "description": "Whether infinite loop detected",
        "written_by": ["infinite_loop_breaker"],
        "read_by": []
    },
    "escape_action": {
        "category": SlotCategory.FILTER,
        "expected_type": int,
        "description": "Action to escape detected loop",
        "written_by": ["infinite_loop_breaker"],
        "read_by": []
    },
    "oscillation_detected": {
        "category": SlotCategory.FILTER,
        "expected_type": bool,
        "description": "Whether position oscillation detected",
        "written_by": ["coordinate_oscillation"],
        "read_by": []
    },
    "oscillation_escape": {
        "category": SlotCategory.FILTER,
        "expected_type": int,
        "description": "Action to escape oscillation",
        "written_by": ["coordinate_oscillation"],
        "read_by": []
    },
    "smart_action": {
        "category": SlotCategory.FILTER,
        "expected_type": int,
        "description": "Smart fallback action",
        "written_by": ["smart_action_selection"],
        "read_by": []
    },
    "action_weights": {
        "category": SlotCategory.FILTER,
        "expected_type": dict,
        "description": "Weights for action selection",
        "written_by": ["smart_action_selection"],
        "read_by": []
    },

    # =========================================================================
    # METACOGNITION SLOTS - Learning, adaptation, confidence
    # =========================================================================
    "predicted_outcome": {
        "category": SlotCategory.METACOGNITION,
        "expected_type": dict,
        "description": "Predicted outcome of action",
        "written_by": ["metacognitive_prediction"],
        "read_by": []
    },
    "confidence_calibration": {
        "category": SlotCategory.METACOGNITION,
        "expected_type": float,
        "description": "Calibration of prediction confidence",
        "written_by": ["metacognitive_prediction"],
        "read_by": []
    },
    "frustration_level": {
        "category": SlotCategory.METACOGNITION,
        "expected_type": float,
        "description": "Current frustration level [0, 1]",
        "written_by": ["frustration_detection"],
        "read_by": ["regulatory_signal"]
    },
    "frustration_action": {
        "category": SlotCategory.METACOGNITION,
        "expected_type": int,
        "description": "Action response to frustration",
        "written_by": ["frustration_detection"],
        "read_by": []
    },
    "sensations": {
        "category": SlotCategory.METACOGNITION,
        "expected_type": dict,
        "description": "Object-sensation mappings",
        "written_by": ["sensation_engine"],
        "read_by": []
    },
    "sensation_weights": {
        "category": SlotCategory.METACOGNITION,
        "expected_type": dict,
        "description": "Weights for sensation-based intuition",
        "written_by": ["sensation_engine"],
        "read_by": []
    },
    "i_thread_action": {
        "category": SlotCategory.METACOGNITION,
        "expected_type": int,
        "description": "Action from I-thread integration",
        "written_by": ["i_thread"],
        "read_by": []
    },
    "stream_integration": {
        "category": SlotCategory.METACOGNITION,
        "expected_type": dict,
        "description": "Stream A/B integration details",
        "written_by": ["i_thread"],
        "read_by": []
    },
    "near_miss_patterns": {
        "category": SlotCategory.METACOGNITION,
        "expected_type": list,
        "description": "Detected near-miss patterns",
        "written_by": ["near_miss_analyzer"],
        "read_by": []
    },
    "improvement_hints": {
        "category": SlotCategory.METACOGNITION,
        "expected_type": list,
        "description": "Hints for improvement from near misses",
        "written_by": ["near_miss_analyzer"],
        "read_by": []
    },
    "resonance_patterns": {
        "category": SlotCategory.METACOGNITION,
        "expected_type": list,
        "description": "Cross-game resonance patterns",
        "written_by": ["resonance_detector"],
        "read_by": ["rule_transfer"]
    },
    "cross_game_matches": {
        "category": SlotCategory.METACOGNITION,
        "expected_type": list,
        "description": "Games with matching patterns",
        "written_by": ["resonance_detector"],
        "read_by": []
    },
    "deliberation_result": {
        "category": SlotCategory.METACOGNITION,
        "expected_type": dict,
        "description": "Result of explicit deliberation",
        "written_by": ["deliberation_system"],
        "read_by": []
    },
    "deliberation_confidence": {
        "category": SlotCategory.METACOGNITION,
        "expected_type": float,
        "description": "Confidence in deliberation result",
        "written_by": ["deliberation_system"],
        "read_by": []
    },
    "replay_insights": {
        "category": SlotCategory.METACOGNITION,
        "expected_type": list,
        "description": "Insights from replay analysis",
        "written_by": ["replay_learning"],
        "read_by": []
    },
    "pattern_extractions": {
        "category": SlotCategory.METACOGNITION,
        "expected_type": list,
        "description": "Patterns extracted from replay",
        "written_by": ["replay_learning"],
        "read_by": []
    },
    "budget_action": {
        "category": SlotCategory.METACOGNITION,
        "expected_type": int,
        "description": "Action from budget allocation",
        "written_by": ["breakthrough_budget"],
        "read_by": []
    },
    "remaining_budget": {
        "category": SlotCategory.METACOGNITION,
        "expected_type": int,
        "description": "Remaining action budget",
        "written_by": ["breakthrough_budget"],
        "read_by": []
    },
    "regulatory_action": {
        "category": SlotCategory.METACOGNITION,
        "expected_type": int,
        "description": "Action from regulatory signal",
        "written_by": ["regulatory_signal"],
        "read_by": []
    },
    "energy_level": {
        "category": SlotCategory.METACOGNITION,
        "expected_type": float,
        "description": "Current energy/arousal level",
        "written_by": ["regulatory_signal"],
        "read_by": []
    },
    "imagination_action": {
        "category": SlotCategory.METACOGNITION,
        "expected_type": int,
        "description": "Action from mental simulation",
        "written_by": ["imagination_budget"],
        "read_by": []
    },
    "simulated_outcomes": {
        "category": SlotCategory.METACOGNITION,
        "expected_type": list,
        "description": "Outcomes from mental simulation",
        "written_by": ["imagination_budget"],
        "read_by": []
    },
    "completion_probability": {
        "category": SlotCategory.METACOGNITION,
        "expected_type": float,
        "description": "Estimated completion probability",
        "written_by": ["completion_prediction"],
        "read_by": []
    },
    "estimated_actions_remaining": {
        "category": SlotCategory.METACOGNITION,
        "expected_type": int,
        "description": "Estimated actions to completion",
        "written_by": ["completion_prediction"],
        "read_by": []
    },
    "exploration_stats": {
        "category": SlotCategory.METACOGNITION,
        "expected_type": dict,
        "description": "Network exploration statistics",
        "written_by": ["network_exploration_stats"],
        "read_by": []
    },
    "coverage_map": {
        "category": SlotCategory.METACOGNITION,
        "expected_type": dict,
        "description": "Exploration coverage map",
        "written_by": ["network_exploration_stats"],
        "read_by": []
    },
    "trust_weight_a": {
        "category": SlotCategory.METACOGNITION,
        "expected_type": float,
        "description": "Current Stream A trust weight",
        "written_by": ["self_trust_boost"],
        "read_by": []
    },
    "trust_weight_b": {
        "category": SlotCategory.METACOGNITION,
        "expected_type": float,
        "description": "Current Stream B trust weight",
        "written_by": ["self_trust_boost"],
        "read_by": []
    },

    # =========================================================================
    # HISTORY SLOTS - Read-only external state (populated by game loop)
    # =========================================================================
    "frame_delta_count": {
        "category": SlotCategory.HISTORY,
        "expected_type": int,
        "description": "Number of frame changes",
        "written_by": [],  # External
        "read_by": ["frame_interpretation", "event_understanding"]
    },
    "recent_events": {
        "category": SlotCategory.HISTORY,
        "expected_type": list,
        "description": "Recent game events",
        "written_by": [],  # External
        "read_by": ["frame_interpretation", "event_understanding"]
    },
    "game_id": {
        "category": SlotCategory.HISTORY,
        "expected_type": str,
        "description": "Current game identifier",
        "written_by": [],  # External
        "read_by": ["control_tracker"]
    },
    "game_type": {
        "category": SlotCategory.HISTORY,
        "expected_type": str,
        "description": "Type/category of game",
        "written_by": [],  # External
        "read_by": ["control_tracker", "discovery_exploitation", "belief_system",
                   "hypothesis_system", "event_understanding", "embedding_suggestion",
                   "scientific_method", "network_wisdom", "primitive_suggester",
                   "exploration_phase", "abstraction_templates", "few_shot_invariants",
                   "three_try_sequence", "multi_stage_matching", "pariah_avoidance",
                   "terminal_pattern", "sensation_engine", "near_miss_analyzer",
                   "state_matching", "network_object_inventory", "embedding_matcher",
                   "network_sharing", "deliberation_system", "replay_learning",
                   "completion_prediction", "network_exploration_stats", "rule_transfer",
                   "hypothesis_testing", "assumption_formation", "contextual_failure"]
    },
    "level": {
        "category": SlotCategory.HISTORY,
        "expected_type": int,
        "description": "Current level number",
        "written_by": [],  # External
        "read_by": ["control_tracker", "prior_lessons", "three_try_sequence",
                   "pariah_avoidance", "terminal_pattern", "frustration_detection",
                   "completion_prediction", "network_exploration_stats", "contextual_failure"]
    },
    "level_number": {
        "category": SlotCategory.HISTORY,
        "expected_type": int,
        "description": "Alternative level number slot",
        "written_by": [],  # External
        "read_by": ["control_tracker"]
    },
    "player_position": {
        "category": SlotCategory.HISTORY,
        "expected_type": tuple,
        "description": "Current player position (x, y)",
        "written_by": [],  # External
        "read_by": ["control_tracker", "death_avoidance", "coordinate_oscillation",
                   "map_intel_collision", "exploration_phase", "frontier_topology",
                   "frontier_checkpoint", "subgoal_planning", "grid_exploration",
                   "imagination_budget", "terminal_pattern"]
    },
    "target_position": {
        "category": SlotCategory.HISTORY,
        "expected_type": tuple,
        "description": "Target/goal position",
        "written_by": [],  # External
        "read_by": ["control_tracker"]
    },
    "goal_position": {
        "category": SlotCategory.HISTORY,
        "expected_type": tuple,
        "description": "Goal position",
        "written_by": [],  # External
        "read_by": ["control_tracker", "subgoal_planning"]
    },
    "agent_id": {
        "category": SlotCategory.HISTORY,
        "expected_type": str,
        "description": "Current agent identifier",
        "written_by": [],  # External
        "read_by": ["hypothesis_system", "two_streams", "i_thread"]
    },
    "action_history": {
        "category": SlotCategory.HISTORY,
        "expected_type": list,
        "description": "History of recent actions",
        "written_by": [],  # External
        "read_by": ["infinite_loop_breaker", "metacognitive_prediction",
                   "smart_action_selection", "theory_contradiction", "pariah_avoidance",
                   "sensation_engine", "near_miss_analyzer", "click_behavior_learning",
                   "trigger_sequences", "replay_learning", "imagination_budget",
                   "network_exploration_stats", "self_trust_boost", "assumption_formation",
                   "contextual_failure", "valence_goals"]
    },
    "state_history": {
        "category": SlotCategory.HISTORY,
        "expected_type": list,
        "description": "History of game states",
        "written_by": [],  # External
        "read_by": ["infinite_loop_breaker"]
    },
    "position_history": {
        "category": SlotCategory.HISTORY,
        "expected_type": list,
        "description": "History of positions",
        "written_by": [],  # External
        "read_by": ["coordinate_oscillation"]
    },
    "checkpoint_sequence": {
        "category": SlotCategory.HISTORY,
        "expected_type": list,
        "description": "Sequence of checkpoints",
        "written_by": [],  # External
        "read_by": ["network_wisdom", "three_try_sequence"]
    },
    "active_sequence": {
        "category": SlotCategory.HISTORY,
        "expected_type": list,
        "description": "Currently active action sequence",
        "written_by": [],  # External
        "read_by": ["three_try_sequence"]
    },
    "winning_sequences": {
        "category": SlotCategory.HISTORY,
        "expected_type": list,
        "description": "Known winning sequences",
        "written_by": [],  # External
        "read_by": ["frontier_checkpoint"]
    },
    "visited_cells": {
        "category": SlotCategory.HISTORY,
        "expected_type": set,
        "description": "Set of visited cell coordinates",
        "written_by": [],  # External
        "read_by": ["grid_exploration"]
    },
    "clicked_objects": {
        "category": SlotCategory.HISTORY,
        "expected_type": set,
        "description": "Set of clicked object IDs",
        "written_by": [],  # External
        "read_by": ["action6_object_exploration"]
    },
    "score_history": {
        "category": SlotCategory.HISTORY,
        "expected_type": list,
        "description": "History of scores",
        "written_by": [],  # External
        "read_by": ["frustration_detection", "near_miss_analyzer",
                   "click_behavior_learning", "replay_learning", "valence_goals",
                   "contextual_failure"]
    },
    "score": {
        "category": SlotCategory.HISTORY,
        "expected_type": int,
        "description": "Current score",
        "written_by": [],  # External
        "read_by": ["completion_prediction"]
    },
    "action_count": {
        "category": SlotCategory.HISTORY,
        "expected_type": int,
        "description": "Total actions taken",
        "written_by": [],  # External
        "read_by": ["frustration_detection", "breakthrough_budget",
                   "regulatory_signal", "completion_prediction"]
    },
    "action_budget": {
        "category": SlotCategory.HISTORY,
        "expected_type": int,
        "description": "Total action budget",
        "written_by": [],  # External
        "read_by": ["breakthrough_budget"]
    },
    "last_discovery": {
        "category": SlotCategory.HISTORY,
        "expected_type": dict,
        "description": "Last discovery made",
        "written_by": [],  # External
        "read_by": ["discovery_exploitation"]
    },
}


# =============================================================================
# SLOT LOOKUP FUNCTIONS
# =============================================================================

def get_slot_category(slot_name: str) -> SlotCategory:
    """Get the category for a slot name."""
    if slot_name in SLOT_DEFINITIONS:
        return SLOT_DEFINITIONS[slot_name]["category"]
    return SlotCategory.ORIENTATION  # Default


def get_slots_by_category(category: SlotCategory) -> List[str]:
    """Get all slot names for a category."""
    return [
        name for name, defn in SLOT_DEFINITIONS.items()
        if defn["category"] == category
    ]


def get_slot_writers(slot_name: str) -> List[str]:
    """Get rungs that write to a slot."""
    if slot_name in SLOT_DEFINITIONS:
        return SLOT_DEFINITIONS[slot_name].get("written_by", [])
    return []


def get_slot_readers(slot_name: str) -> List[str]:
    """Get rungs that read from a slot."""
    if slot_name in SLOT_DEFINITIONS:
        return SLOT_DEFINITIONS[slot_name].get("read_by", [])
    return []


def validate_slot_definition_coverage() -> Dict[str, Any]:
    """
    Validate that all slots have proper definitions.

    Returns:
        Dict with validation results
    """
    results = {
        "total_slots": len(SLOT_DEFINITIONS),
        "by_category": {},
        "orphan_writes": [],  # Slots written but never read
        "orphan_reads": [],   # Slots read but never written
        "external_inputs": []  # Slots with no writers (external)
    }

    # Count by category
    for cat in SlotCategory:
        slots = get_slots_by_category(cat)
        results["by_category"][cat.name] = len(slots)

    # Find orphans
    for name, defn in SLOT_DEFINITIONS.items():
        writers = defn.get("written_by", [])
        readers = defn.get("read_by", [])

        if not writers:
            results["external_inputs"].append(name)
        elif not readers:
            results["orphan_writes"].append(name)

    return results


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "SLOT_DEFINITIONS",
    "get_slot_category",
    "get_slots_by_category",
    "get_slot_writers",
    "get_slot_readers",
    "validate_slot_definition_coverage",
]
