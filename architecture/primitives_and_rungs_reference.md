# Complete Primitives and Rungs Reference

**Last Updated**: 2026-02-03
**Purpose**: Comprehensive reference for all seed primitives and decision rungs

---

## PRIMITIVES (110+ Seed Primitives)

### Categories and Their Primitives

| Category | Primitives | Use Case |
|----------|-----------|----------|
| **RAW_DATA** | `get_pixel`, `get_frame`, `get_previous_frame`, `get_frame_size`, `set_frame` | Access pixel/frame data for perception |
| **MATH** | `add`, `subtract`, `multiply`, `divide`, `modulo`, `abs`, `neg`, `floor` | Arithmetic operations for calculations |
| **COMPARISON** | `equals`, `not_equals`, `greater_than`, `less_than`, `greater_eq`, `less_eq`, `between` | Boolean comparisons for conditions |
| **CONTROL_FLOW** | `if_else`, `select`, `coalesce` | Branching and conditional logic |
| **DATA_STRUCTURE** | `make_list`, `append`, `len`, `get_at`, `slice`, `concat`, `contains`, `index_of`, `unique` | List manipulation and data storage |
| **ITERATION** | `for_each_pixel`, `for_range`, `map`, `filter`, `reduce`, `any`, `all` | Looping and functional operations |
| **AGGREGATION** | `sum`, `max`, `min`, `average`, `median` | Statistical operations on collections |
| **TEMPORAL** | `get_step_index`, `get_episode_id`, `get_action_count`, `get_elapsed_actions`, `detect_causation`, `detect_precedence`, `detect_simultaneity`, `detect_periodic`, `detect_decay_persistence`, `detect_sequence_pattern` | Time-aware cognition and causality |
| **ACTION** | `get_action_space`, `get_last_action`, `get_action_history`, `record_action` | Action introspection and history |
| **RNG** | `rand`, `rand_int`, `rand_choice`, `seed_rng` | Randomness for exploration |
| **HASHING** | `hash`, `hash_frame`, `signature` | Creating unique signatures for caching |
| **OBJECT_INTERACTION** | `test_object_control`, `find_distinct_objects`, `did_object_move`, `get_object_movement`, `action_matches_movement`, `get_click_target`, `detect_click_effect`, `find_all_interactable_objects`, `find_similar_objects`, `pattern_matching`, `count_matching_objects`, `detect_collision`, `detect_contact`, `detect_blocking`, `detect_pushing`, `detect_overlap`, `detect_engulfing`, `detect_partial_containment`, `detect_nesting`, `detect_wrapping`, `detect_coating`, `detect_pass_through`, `detect_embedding`, `detect_proximity_effect`, `detect_attraction_repulsion`, `detect_merging`, `detect_adhesion`, `detect_snapping`, `hypothesize_interaction_type`, `test_interaction_hypothesis`, `get_interaction_effect`, `detect_following`, `detect_mirroring`, `detect_chasing`, `detect_fleeing`, `detect_synchronized_movement`, `detect_dragging` | Object discovery, tracking, and interaction hypothesis testing |
| **ATTENTION** | `detect_change`, `detect_motion`, `detect_contingency`, `surprise_magnitude`, `information_gain` | Focus attention on novel/important stimuli |
| **AFFORDANCE** | `is_movable`, `is_obstacle`, `is_interactive`, `is_container`, `is_support`, `is_reference`, `is_tool` | Perceive what objects are FOR (function) |
| **SOCIAL_LEARNING** | `credibility_weighting`, `demonstration_bias`, `attention_following`, `teaching_detection` | Learn from network agents efficiently |
| **MOTIVATION** | `novelty_bonus`, `competence_signal`, `exploration_value`, `boredom_threshold`, `direction_to_goal`, `systematic_exploration_direction`, `explore_toward_unexplored`, `edge_exploration_needed`, `exploration_coverage` | Intrinsic motivation for explore/exploit |
| **PHYSICS_PRIOR** | `solidity_bias`, `continuity_bias`, `gravity_bias`, `persistence_bias`, `contact_causality` | Weak physical expectations (adjustable) |
| **QUANTITATIVE** | `count_objects`, `compare_quantities`, `detect_one_vs_many`, `one_to_one_match` | Approximate numerosity sense |
| **METACOGNITION** | `get_confidence`, `detect_stuck`, `strategy_effectiveness`, `get_knowledge_state`, `estimate_learning_curve` | Know what you know (self-awareness) |
| **NEGATIVE_SPACE** | `detect_enclosed_empty`, `detect_open_edge`, `detect_absence`, `negative_space_volume` | Detect holes, gaps, missing things |
| **EXPLORATION_STRATEGY** | `detect_stuck_pattern`, `select_unexplored_target`, `estimate_exploration_budget`, `calculate_reachability`, `get_strategic_exploration_action` | Strategic exploration (executive function) |
| **PERCEPTUAL** | `color_sampling`, `pattern_detection`, `scale_measurement`, `spatial_relationships`, `template_extraction`, `analogical_mapping`, `role_binding`, `hierarchical_composition`, `color_substitution`, `pattern_replication`, `functional_attribution`, `rule_detection`, `metadata_recognition`, `complexity_signaling` | ARC-specific perceptual operations |
| **SPATIAL** | `detect_adjacency`, `detect_connectivity`, `detect_path_between`, `detect_separation`, `detect_surrounding`, `detect_clustering`, `detect_layering`, `detect_attachment`, `detect_part_whole`, `detect_occluding`, `compute_visibility`, `detect_casting` | Topological spatial relationships |
| **PHYSICS** | `detect_supporting`, `detect_stacking`, `detect_hanging`, `detect_leaning`, `detect_guiding`, `detect_gating`, `detect_actuating` | Support, constraint, and control |
| **TOPOLOGY** | `detect_hole`, `detect_cavity`, `detect_protrusion`, `count_connected_components`, `detect_boundary_closure`, `detect_euler_characteristic`, `detect_genus` | Holes, boundaries, connected components |
| **ALIGNMENT** | `detect_parallel`, `detect_perpendicular`, `detect_colinear`, `detect_coplanar`, `measure_angle_between`, `detect_facing_direction`, `detect_alignment` | Geometric alignment detection |
| **SYMMETRY** | `detect_reflection_symmetry`, `detect_rotational_symmetry`, `detect_translational_symmetry`, `detect_self_similarity`, `detect_periodicity_spatial` | Symmetry and pattern repetition |
| **BOUNDARY** | `detect_inside_outside`, `compute_distance_to_boundary`, `detect_boundary_crossing`, `detect_enclosure`, `measure_convexity` | Inside/outside and enclosure |
| **HIERARCHY** | `get_parent_object`, `get_child_objects`, `detect_composite_object`, `decompose_object`, `find_root_object` | Part-whole relationships |
| **PERSISTENCE** | `object_first_appearance`, `object_last_seen`, `detect_object_creation`, `detect_object_destruction`, `track_object_identity` | Object permanence and tracking |
| **RELATIONAL** | `get_all_relations`, `get_relation_strength`, `detect_relation_change`, `relation_history` | Meta-queries on relationships |
| **SCALE** | `detect_aggregation`, `detect_subdivision`, `measure_granularity`, `scale_invariance_check` | Aggregation and subdivision |
| **FLOW** | `detect_flowing_through`, `detect_filling`, `detect_draining`, `detect_transfer`, `detect_propagation`, `measure_fill_level`, `detect_source_sink` | Flow, filling, propagation |
| **TRANSFORMATION** | `detect_state_change`, `detect_growth`, `detect_decay`, `detect_crystallization`, `detect_dissolution`, `detect_color_transformation`, `detect_restoration` | State changes and transformations |
| **CONSTRAINT** | `detect_binding`, `detect_tethering` | Binding and constraint detection |

---

## DECISION RUNGS (63+ Rungs)

### Rung Categories

| Category | Purpose |
|----------|---------|
| **EMERGENCY** | Highest priority, break infinite loops/oscillations |
| **ORIENTATION** | Early context-setting, surveys, budget allocation |
| **FILTER** | Apply weights/penalties to dangerous actions |
| **HYPOTHESIS** | Theory formation, testing, metacognition |
| **EXPLOITATION** | Use learned knowledge to suggest actions |
| **FALLBACK** | Last-resort action selection |

### Complete Rung Reference

| Rung Name | Category | Priority | Use Case | Key Primitives Used |
|-----------|----------|----------|----------|---------------------|
| `infinite_loop_breaker` | emergency | 1 | Break stuck loops (>15 same actions) | `detect_stuck` |
| `coordinate_oscillation` | emergency | 3 | Detect bouncing between coordinates | `detect_motion`, position tracking |
| `self_trust_boost` | orientation | 3 | Boost wA on frontier, restore when sequences exist | Stream weights (wA/wB) |
| `palette_detection` | orientation | 3 | TWO-STAGE: Extract objects, detect palette/legend | `pattern_detection`, `template_extraction` |
| `sparse_grid` | orientation | 3 | Efficient sparse frame representation | `find_distinct_objects`, connected components |
| `frame_interpretation` | orientation | 4 | Set context flags for physics/animation games | `detect_motion`, frame delta analysis |
| `imagination_budget` | orientation | 4 | Allocate compute based on novelty | `novelty_bonus`, `information_gain` |
| `survey` | orientation | 5 | Survey environment at level start | `find_distinct_objects`, `color_sampling` |
| `breakthrough_budget` | orientation | 6 | Dynamic action allocation | Budget calculation |
| `regulatory_signal` | orientation | 7 | Network homeostasis signals | Network metabolism |
| `control_tracker` | orientation | 8 | "I am this object" tracking | `test_object_control`, `action_matches_movement` |
| `network_exploration_stats` | orientation | 9 | Coverage, coldspots, hotspots | `exploration_coverage` |
| `questioning_engine` | orientation | 10 | Q1-Q9 blocking questions | Scientific method |
| `scientific_method` | hypothesis | 12 | Theory formation and testing | Theory stages |
| `frustration_detection` | orientation | 13 | Detect stuck agents | `detect_stuck`, `boredom_threshold` |
| `terminal_pattern` | filter | 14 | Recognize approaching terminal states | Death pattern detection |
| `contextual_failure` | filter | 14 | Position/direction-aware failure tracking | Position regions |
| `death_avoidance` | filter | 15 | Position-bucket death pattern avoidance | Terminal pattern detection |
| `prior_lessons` | filter | 16 | Apply learned lessons as weights | Database lessons |
| `assumption_formation` | hypothesis | 16 | Form testable assumptions from patterns | Pattern correlation |
| `theory_contradiction` | filter | 17 | Filter actions contradicting theory | Metacognition |
| `metacognitive_prediction` | hypothesis | 18 | Make predictions, learn from errors | `get_confidence`, prediction |
| `hypothesis_testing` | hypothesis | 19 | Test untested assumptions | Assumption system |
| `discovery_exploitation` | exploitation | 20 | Exploit recent discoveries | `test_object_control` |
| `exploration_phase` | orientation | 22 | Phase-based exploration forcing | Budget phases |
| `event_understanding` | hypothesis | 23 | Causal world model for physics games | `detect_causation`, event detection |
| `map_intel_collision` | exploitation | 24 | Perpendicular movement on collision | `detect_blocking` |
| `symbolic_tracker` | hypothesis | 24 | Key/lock symbolic matching | `pattern_matching`, symbolic state |
| `embedding_suggestion` | exploitation | 25 | Cross-game neural similarity | Frame embeddings |
| `belief_system` | hypothesis | 25 | Track and use agent beliefs | Belief persistence |
| `rule_transfer` | exploitation | 25 | Apply learned rules from other games | Rule induction |
| `state_matching` | exploitation | 26 | Compare properties to goal requirements | Property extraction |
| `hypothesis_system` | hypothesis | 26 | Agent-initiated hypothesis testing | Hypothesis management |
| `frontier_topology` | exploitation | 28 | Network topology for frontier levels | Network action traces |
| `deliberation_system` | hypothesis | 29 | TRM-inspired iterative refinement | Theory hints |
| `two_streams` | hypothesis | 30 | Stream A vs Stream B conflict | wA/wB weights |
| `i_thread` | hypothesis | 31 | Persistent identity, death personas | Stream weaving |
| `sensation_engine` | hypothesis | 33 | Emotional context from sensations | Tetrahedral sensation |
| `resonance_detector` | hypothesis | 34 | Cross-role pattern discovery | Resonance detection |
| `valence_goals` | exploitation | 35 | Valence associations (good/bad/neutral) | Goal inference |
| `network_wisdom` | exploitation | 35 | Query network-wide action wisdom | Episodic memory |
| `click_behavior_learning` | exploitation | 36 | Learn click patterns (collectibles, triggers) | Click behavior classification |
| `visual_analyzer` | exploitation | 36 | Priority targets for ACTION6 clicks | Visual analysis |
| `network_object_inventory` | exploitation | 37 | Network knowledge about objects | Object inventory |
| `action6_object_exploration` | exploration | 38 | Find clickable objects via Action6BehaviorEngine | Object detection, pseudobuttons |
| `subgoal_planning` | exploitation | 38 | Decompose into subgoals | Subgoal decomposition |
| `completion_prediction` | exploitation | 39 | Estimate steps to completion | Progress tracking |
| `primitive_suggester` | exploitation | 40 | Direct primitive-to-action mapping | Multiple primitives |
| `trigger_sequences` | exploitation | 43 | Learn and use trigger chains | Trigger effect detection |
| `replay_learning` | exploitation | 43 | Prediction during sequence replay | Replay system |
| `embedding_matcher` | exploitation | 44 | Frame embedding similarity | Neural embeddings |
| `spatial_relationship` | exploitation | 44 | Click effect patterns for puzzles | Spatial effect learning |
| `grid_exploration` | orientation | 47 | Systematic 8x8 grid walking | Grid walking |
| `near_miss_analyzer` | exploitation | 48 | Learn from high-score failures | Near-miss patterns |
| `network_sharing` | exploitation | 50 | Network control hypotheses | Thought process colony |
| `few_shot_invariants` | exploitation | 51 | Control invariants from examples | Few-shot learning |
| `few_shot_relations` | exploitation | 52 | Quick control bootstrapping | Invariant/variant detection |
| `theory_gate` | hypothesis | 55 | Working theory must score proposals | Theory validation |
| `abstraction_templates` | exploitation | 60 | Game-type specific templates | Template matching |
| `three_try_sequence` | exploitation | 65 | Try 3 variations of sequences | Sequence variation |
| `multi_stage_matching` | exploitation | 70 | Multi-stage pattern matching | Pipeline matching |
| `three_layer_filter` | filter | 75 | Three-layer action filtering | Layered filtering |
| `pariah_avoidance` | filter | 80 | Avoid toxic patterns (pariahs) | Pariah decay |
| `frontier_checkpoint` | exploitation | 85 | Constructive pathfinding | Checkpoint system |
| `smart_action_selection` | fallback | 99 | Strategy-based random selection | Weighted random |

---

## Orderings (Rung Sequences)

### Built-in Orderings

| Ordering | Description | Key Characteristics |
|----------|-------------|---------------------|
| `comprehensive` | Default 63-rung ordering | Full cognitive architecture |
| `action6_world` | 31 rungs for hybrid ACTION6 games | Prioritizes perception, self-model, world-model, object targeting |
| `action6_only` | 25 rungs for click-only games (e.g., vc33) | Optimized for touchscreen/click-based games |
| `experimental_curiosity_first` | Exploration-heavy | Early exploration_phase, late death_avoidance |
| `minimal_fear` | Low death penalty | death_avoidance at priority 90 |
| `maximum_caution` | Safety-first | death_avoidance at priority 2 |
| `network_learner` | Network-focused | network_wisdom first |
| `pure_exploration` | Discovery mode | exploration_phase at priority 10 |
| `world_model_heavy` | Physics games | event_understanding prioritized |

---

## Key Architectural Patterns

### Primitive → Rung Mapping

1. **Perception Primitives** feed → `survey`, `palette_detection`, `sparse_grid`
2. **Object Interaction Primitives** feed → `control_tracker`, `discovery_exploitation`
3. **Attention Primitives** feed → `frame_interpretation`, `event_understanding`
4. **Metacognition Primitives** feed → `metacognitive_prediction`, `hypothesis_testing`
5. **Spatial Primitives** feed → `spatial_relationship`, `frontier_topology`
6. **Motivation Primitives** feed → `exploration_phase`, `valence_goals`

### Three-Layer Architecture Alignment

| Layer | Primitives | Rungs |
|-------|-----------|-------|
| **Layer 1 (Static Genome)** | Base perception, math, comparison | Emergency rungs, basic filters |
| **Layer 2 (Epigenetic)** | Attention, affordance, motivation | Hypothesis rungs, exploration |
| **Layer 3 (Somatic)** | Metacognition, social learning | Exploitation rungs, network wisdom |

---

## Piaget Stage Mapping

Primitives unlock at different cognitive development stages:

| Stage | Unlock Level | Example Primitives |
|-------|--------------|-------------------|
| **Sensorimotor** | `seed` (always available) | `detect_change`, `test_object_control`, `detect_motion` |
| **Preoperational** | `early` | `is_container`, `gravity_bias`, `information_gain` |
| **Concrete Operational** | `early`/`late` | `teaching_detection`, `boredom_threshold` |
| **Formal Operational** | `late` | `strategy_effectiveness`, `get_knowledge_state`, `is_reference` |

---

## ACTION6-Specific Architecture

For click-based games (ACTION6-only like vc33):

### Specialized Orderings
- `action6_only`: 25 rungs optimized for touchscreen games
- `action6_world`: 31 rungs for hybrid movement+click games

### Key Rungs for ACTION6
1. `action6_object_exploration` - Find clickable objects
2. `click_behavior_learning` - Learn what clicks do
3. `visual_analyzer` - Priority click targets
4. `spatial_relationship` - Click effect patterns
5. `grid_exploration` - Systematic 8x8 walking

### Coordinate Provider Strategies
1. **Detected objects** - Click on identified game objects
2. **Grid exploration** - Systematic grid walking
3. **Frame analysis** - Visual analyzer targets
4. **Random fallback** - Random valid coordinates
