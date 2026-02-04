# Primitive-to-Blackboard-Slot Mapping

**Phase 0 Deliverable - Cognitive Routing Implementation**
**Generated**: 2026-01-XX
**Purpose**: Map 110 seed primitive categories to blackboard slots they inform

---

## Overview

This document maps the 9 primary primitive categories from `seed_primitives.py` to the blackboard context slots they populate. This enables the Rumsfeld epistemic engine to assess what knowledge domains have been explored (Known-Known vs Unknown-Unknown).

---

## Primitive Category → Slot Mappings

### 1. ATTENTION AND SALIENCE

**Primitives**: `detect_novelty`, `detect_motion`, `face_detection`, `detect_contingency`, `surprise_detection`

| Primitive | Populates Slot | Rung Consumer |
|-----------|---------------|---------------|
| detect_novelty | `novelty_score`, `novel_objects` | `discovery_exploitation`, `exploration_phase` |
| detect_motion | `moving_objects`, `motion_vectors` | `event_understanding`, `control_tracker` |
| detect_contingency | `contingent_pairs`, `action_effects` | `click_behavior_learning`, `trigger_sequences` |
| surprise_detection | `surprise_events`, `expectation_violations` | `hypothesis_system`, `belief_system` |

**Blackboard Slots Informed**:
- `novelty_score`: Float 0.0-1.0 indicating how novel current frame is
- `novel_objects`: List of object IDs that are new/unexpected
- `moving_objects`: Dict mapping object_id → velocity vector
- `contingent_pairs`: List of (action, effect) tuples with correlation scores

---

### 2. PHYSICAL INTUITION (Weak Priors)

**Primitives**: `object_permanence_bias`, `solidity_constraint`, `continuity_bias`, `gravity_expectation`, `contact_causality`

| Primitive | Populates Slot | Rung Consumer |
|-----------|---------------|---------------|
| object_permanence_bias | `expected_objects`, `missing_objects` | `event_understanding`, `symbolic_tracker` |
| solidity_constraint | `collision_predictions`, `passable_cells` | `map_intel_collision`, `frontier_topology` |
| continuity_bias | `trajectory_predictions`, `expected_positions` | `control_tracker`, `subgoal_planning` |
| gravity_expectation | `fall_predictions`, `support_relations` | `event_understanding`, `spatial_relationship` |
| contact_causality | `contact_events`, `push_predictions` | `trigger_sequences`, `click_behavior_learning` |

**Blackboard Slots Informed**:
- `expected_objects`: Objects we expect to persist frame-to-frame
- `collision_predictions`: Cells where movement would fail
- `trajectory_predictions`: Where moving objects will be next frame
- `support_relations`: Which objects support/rest-on which

**Prior Strength Override**: Physics priors are adjustable (0.0-1.0) and can be weakened when evidence contradicts (e.g., teleportation games, portal mechanics)

---

### 3. AFFORDANCE DETECTION

**Primitives**: `is_movable`, `is_container`, `is_obstacle`, `is_interactive`, `is_reference`, `is_collectible`, `is_boundary`, `is_goal`

| Primitive | Populates Slot | Rung Consumer |
|-----------|---------------|---------------|
| is_movable | `movable_objects`, `static_objects` | `control_tracker`, `subgoal_planning` |
| is_container | `container_objects`, `containment_relations` | `symbolic_tracker`, `spatial_relationship` |
| is_obstacle | `obstacle_map`, `blocked_cells` | `frontier_topology`, `map_intel_collision` |
| is_interactive | `clickable_objects`, `interaction_targets` | `action6_object_exploration`, `click_behavior_learning` |
| **is_reference** | `reference_objects`, `legend_objects`, `palette_info` | `palette_detection`, `abstraction_templates` |
| is_collectible | `collectible_objects`, `reward_objects` | `valence_goals`, `click_behavior_learning` |
| is_boundary | `boundary_cells`, `boundary_type` | `survey`, `sparse_grid`, `visual_analyzer` |
| is_goal | `goal_objects`, `goal_positions`, `goal_conditions` | `valence_goals`, `subgoal_planning`, `completion_prediction` |

**Blackboard Slots Informed**:
- `movable_objects`: Objects that respond to actions
- `obstacle_map`: 2D boolean grid of impassable cells
- `clickable_objects`: Objects that respond to ACTION6/7
- `reference_objects`: **CRITICAL** - Legend/palette objects that encode rules about OTHER objects (FT09 lesson)
- `goal_objects`: Target objects to reach/collect/transform

**Special Note on `is_reference`**: This is the most architecturally important affordance. Reference objects (palettes, legends, keys) don't participate in gameplay directly - they encode transformation rules for other objects. Detecting these correctly prevents the "top-to-bottom vs inside-out" error that causes 76% of ARC failures.

---

### 4. SPATIAL REASONING

**Primitives**: `distance`, `adjacent`, `enclosed`, `detect_hole`, `open_edges`

| Primitive | Populates Slot | Rung Consumer |
|-----------|---------------|---------------|
| distance | `distance_matrix`, `nearest_objects` | `frontier_topology`, `subgoal_planning` |
| adjacent | `adjacency_graph`, `neighbor_map` | `sparse_grid`, `map_intel_collision` |
| enclosed | `enclosure_regions`, `inside_outside` | `spatial_relationship`, `symbolic_tracker` |
| **detect_hole** | `hole_positions`, `cavity_objects` | `sparse_grid`, `topology analysis` |
| open_edges | `open_edges`, `escape_routes` | `frontier_topology`, `grid_exploration` |

**Blackboard Slots Informed**:
- `distance_matrix`: NxN distances between all object pairs
- `adjacency_graph`: Graph of which objects touch which
- `enclosure_regions`: Regions fully enclosed by boundaries
- `hole_positions`: **CRITICAL for SP80** - Empty spaces within otherwise solid objects
- `open_edges`: Grid edges that are passable (not walls)

---

### 5. TEMPORAL PROCESSING

**Primitives**: `recency_weighting`, `temporal_contiguity`, `duration_sensitivity`, `rhythm_detection`

| Primitive | Populates Slot | Rung Consumer |
|-----------|---------------|---------------|
| recency_weighting | `recency_weights`, `recent_events` | `event_understanding`, `replay_learning` |
| temporal_contiguity | `contiguous_events`, `event_chains` | `trigger_sequences`, `click_behavior_learning` |
| duration_sensitivity | `event_durations`, `stable_states` | `frame_interpretation`, `event_understanding` |
| rhythm_detection | `detected_rhythms`, `cycle_patterns` | `infinite_loop_breaker`, `coordinate_oscillation` |

**Blackboard Slots Informed**:
- `recency_weights`: How much to weight recent vs old events
- `contiguous_events`: Events that happened immediately after actions
- `event_durations`: How long states/events persist
- `detected_rhythms`: Repeating patterns in frame sequences

---

### 6. QUANTITATIVE SENSE

**Primitives**: `subitizing`, `approximate_numerosity`, `one_to_one_correspondence`

| Primitive | Populates Slot | Rung Consumer |
|-----------|---------------|---------------|
| subitizing | `small_counts`, `immediate_quantities` | `survey`, `visual_analyzer` |
| approximate_numerosity | `object_counts`, `color_counts`, `region_sizes` | `sparse_grid`, `palette_detection` |
| one_to_one_correspondence | `matching_pairs`, `correspondence_map` | `symbolic_tracker`, `spatial_relationship` |

**Blackboard Slots Informed**:
- `small_counts`: Instant (< 4) object counts per category
- `object_counts`: Approximate counts of each object type
- `matching_pairs`: Objects that correspond 1-to-1 (keys/locks, colors/targets)

---

### 7. SOCIAL LEARNING PRIMITIVES

**Primitives**: `imitation_bias`, `joint_attention`, `pedagogical_stance`, `social_referencing`

| Primitive | Populates Slot | Rung Consumer |
|-----------|---------------|---------------|
| imitation_bias | `imitation_targets`, `trusted_sequences` | `network_wisdom`, `three_try_sequence` |
| joint_attention | `shared_focus`, `network_attention` | `network_sharing`, `resonance_detector` |
| pedagogical_stance | `teaching_signals`, `demonstration_frames` | `few_shot_invariants`, `abstraction_templates` |
| social_referencing | `network_opinions`, `trust_scores` | `two_streams`, `network_wisdom` |

**Blackboard Slots Informed**:
- `imitation_targets`: Winning sequences from other agents to imitate
- `shared_focus`: Objects/regions that multiple agents attend to
- `trust_scores`: Bayesian trust weights for different network sources
- `network_opinions`: Aggregated advice from Stream B

---

### 8. EXPLORE/EXPLOIT TRADE-OFF

**Primitives**: `curiosity_drive`, `competence_motivation`, `exploration_bonus`, `boredom_threshold`

| Primitive | Populates Slot | Rung Consumer |
|-----------|---------------|---------------|
| curiosity_drive | `curiosity_score`, `unexplored_regions` | `exploration_phase`, `grid_exploration` |
| competence_motivation | `competence_score`, `mastery_level` | `discovery_exploitation`, `prior_lessons` |
| exploration_bonus | `exploration_rewards`, `visit_counts` | `frontier_topology`, `exploration_phase` |
| boredom_threshold | `boredom_level`, `staleness_score` | `frustration_detection`, `regulatory_signal` |

**Blackboard Slots Informed**:
- `curiosity_score`: Intrinsic motivation to explore
- `unexplored_regions`: Grid cells never visited
- `visit_counts`: How many times each cell has been visited
- `boredom_level`: Indicator of repetitive behavior

---

### 9. METACOGNITION

**Primitives**: `get_confidence`, `detect_stuck`, `strategy_effectiveness`, `get_knowledge_state`, `estimate_learning_curve`

| Primitive | Populates Slot | Rung Consumer |
|-----------|---------------|---------------|
| get_confidence | `confidence_level`, `uncertainty_regions` | `metacognitive_prediction`, `deliberation_system` |
| detect_stuck | `stuck_detected`, `stuck_duration`, `stuck_context` | `infinite_loop_breaker`, `frustration_detection` |
| strategy_effectiveness | `strategy_scores`, `winning_strategies` | `replay_learning`, `near_miss_analyzer` |
| get_knowledge_state | `known_knowns`, `known_unknowns`, `unknown_unknowns` | **Rumsfeld Engine** (Phase 1) |
| estimate_learning_curve | `learning_rate`, `plateau_detected` | `breakthrough_budget`, `completion_prediction` |

**Blackboard Slots Informed**:
- `confidence_level`: Agent's confidence in current strategy (0.0-1.0)
- `stuck_detected`: Boolean flag indicating agent is stuck
- `strategy_scores`: Effectiveness ratings for each strategy tried
- `known_knowns`, `known_unknowns`, `unknown_unknowns`: **RUMSFELD STATE** - drives algorithm selection

---

## Rumsfeld State Integration

The metacognition primitives directly feed the Rumsfeld epistemic engine:

```
Rumsfeld State = {
  KK: sum(slot.confidence for slot in populated_slots if slot.confidence > 0.7),
  KU: sum(1 for slot in populated_slots if 0.3 < slot.confidence <= 0.7),
  UK: count(slots where we know we lack data),
  UU: total_possible_slots - (KK + KU + UK)
}
```

### Slot → Rumsfeld Category Mapping

| Slot State | Rumsfeld Category | Example |
|------------|-------------------|---------|
| Populated, high confidence | **Known-Known (KK)** | `survey_complete=True`, `controlled_objects=[...]` |
| Populated, low confidence | **Known-Unknown (KU)** | `hypothesis_action` with confidence 0.4 |
| Not populated, known missing | **Unknown-Known (UK)** | `winning_sequences` on unbeaten level |
| Not even queried | **Unknown-Unknown (UU)** | `resonance_patterns` never checked |

---

## Primitive → Question Taxonomy

Each primitive category answers specific questions that the QuestionManager should track:

| Primitive Category | Questions Answered |
|-------------------|-------------------|
| ATTENTION | "What is new/novel?", "What changed?", "What is salient?" |
| PHYSICAL_INTUITION | "Where are things?", "What will happen?", "Is physics normal?" |
| AFFORDANCE | "What can I do?", "What is this for?", "What is the goal?" |
| SPATIAL | "Where is X relative to Y?", "What's inside/outside?", "What's connected?" |
| TEMPORAL | "What just happened?", "Is this a pattern?", "How long has this lasted?" |
| QUANTITATIVE | "How many?", "Are these matched?", "Is this more or less?" |
| SOCIAL | "What do others know?", "Should I trust this?", "What worked for them?" |
| MOTIVATION | "Should I explore or exploit?", "Am I bored?", "Am I competent here?" |
| METACOGNITION | "How sure am I?", "Am I stuck?", "What do I not know?" |

---

## Implementation Notes

### For Phase 1 (Blackboard Architecture)

1. Each slot should track:
   - `value`: The actual data
   - `confidence`: 0.0-1.0 certainty
   - `source_primitive`: Which primitive populated it
   - `timestamp`: When it was last updated
   - `staleness_threshold`: When to consider it stale

2. Slot dependencies should be encoded:
   ```python
   SLOT_DEPENDENCIES = {
       'frontier_topology': ['sparse_grid', 'controlled_objects'],
       'subgoal_planning': ['goal_objects', 'player_position', 'obstacle_map'],
       # ...
   }
   ```

### For Phase 2 (Rumsfeld Engine)

1. Implement `get_knowledge_state()` to return current Rumsfeld quadrant
2. Track transitions between quadrants (UU→UK→KU→KK)
3. Use quadrant to select routing algorithm:
   - High UU → More exploration (Bidirectional, BeamSearch)
   - High KK → More exploitation (TopologicalDP, cached paths)
   - High UK → Targeted queries (LandmarkA*)

---

## Appendix: Full Slot List

Total unique slots identified: **87**

### Orientation Slots (populated early)
- `survey`, `survey_complete`, `detected_palette`, `extracted_objects`, `detected_transformations`
- `sparse_grid`, `sparse_hash`, `sparse_cell_count`, `sparse_colors`, `sparse_components`, `sparse_diff`
- `likely_physics_game`, `expect_large_deltas`, `detected_process_type`, `likely_direct_control`
- `controlled_objects`, `primary_control`, `visual_features`, `symmetry_info`, `color_blocks`
- `object_inventory`, `known_objects`

### Identity Slots (self-model)
- `game_id`, `game_type`, `level`, `level_number`, `agent_id`
- `player_position`, `target_position`, `goal_position`

### Hypothesis Slots
- `active_beliefs`, `untested_hypotheses`, `new_assumptions`, `assumption_confidence`
- `causal_model`, `productive_events`, `event_history`
- `click_patterns`, `spatial_rules`, `click_rules`, `collectible_patterns`
- `trigger_chains`, `key_lock_pairs`
- `good_objects`, `bad_objects`, `goal_objects`

### Exploitation Slots
- `checkpoint_sequence`, `active_sequence`, `winning_sequences`
- `matched_stage`, `matched_state`, `similar_states`
- `subgoal_path`, `current_subgoal`, `frontier_target`, `checkpoint_path`
- `exploration_action`, `frontier_cells`, `unexplored_cells`, `reachable_cells`
- `template_action`, `matched_template`, `transferred_rules`

### Filter Slots
- `death_weights`, `avoided_positions`, `collision_map`, `safe_directions`
- `theory_aligned_actions`, `theory_blocked_actions`, `contradicted_actions`
- `filtered_actions`, `filter_reasons`
- `pariah_actions`, `pariah_decay`, `terminal_patterns`, `terminal_weights`
- `failure_context`, `avoided_contexts`

### Metacognition Slots
- `frustration_level`, `confidence_level`, `energy_level`
- `predicted_outcome`, `confidence_calibration`, `completion_probability`
- `near_miss_patterns`, `improvement_hints`, `replay_insights`, `pattern_extractions`
- `resonance_patterns`, `cross_game_matches`
- `exploration_stats`, `coverage_map`
- `trust_weight_a`, `trust_weight_b`, `stream_integration`
- `remaining_budget`, `simulated_outcomes`, `estimated_actions_remaining`

### History Slots (external, read-only)
- `action_history`, `state_history`, `position_history`, `score_history`
- `action_count`, `action_budget`, `score`
- `frame_delta_count`, `recent_events`
- `visited_cells`, `clicked_objects`

---

**END OF MAPPING DOCUMENT**
