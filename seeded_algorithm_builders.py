"""
Seeded Algorithm Builders

Creates real-world algorithm adaptations for the ARC-AGI-3 game context.
Each algorithm is adapted to work within the game's action space while
maintaining the core principles of the original algorithm.
"""

import random
import string
from typing import Dict, Any, List
from algorithm_representations import (
    AlgorithmRepresentation, AlgorithmNode, ActionNode, ConditionalNode,
    SequenceNode, ConditionNode, RandomChoiceNode, RepeatNode
)


class SeededAlgorithmBuilder:
    """Builder class for creating seeded algorithm adaptations."""

    @staticmethod
    def create_astar_algorithm() -> AlgorithmRepresentation:
        """A* Search: f(n) = g(n) + h(n) - Score-based pathfinding with heuristic exploration."""

        # High score condition (good position, explore more)
        high_score_condition = ConditionNode(
            "condition",
            condition_type="score_threshold",
            parameters={"threshold": 50, "operator": "greater_than"}
        )

        # Exploration action (ACTION6) with systematic coordinate exploration
        from action6_helpers import create_systematic_action6

        explore_action = create_systematic_action6()  # Dynamic systematic exploration

        # Conservative building sequence for low scores
        conservative_sequence = SequenceNode("sequence", children=[
            ActionNode("action", action_type="ACTION1"),  # Foundation
            ActionNode("action", action_type="ACTION2"),  # Build
            ActionNode("action", action_type="ACTION3")   # Consolidate
        ])

        root = ConditionalNode(
            "conditional",
            condition=high_score_condition,
            true_branch=explore_action,
            false_branch=conservative_sequence
        )

        algorithm = AlgorithmRepresentation(root)
        algorithm.algorithm_id = "astar_seed_001"
        algorithm.metadata = {
            "original_name": "A* Search Algorithm",
            "category": "Search & Optimization",
            "adaptation_notes": "Score-based pathfinding with heuristic exploration"
        }
        return algorithm

    @staticmethod
    def create_decision_tree_algorithm() -> AlgorithmRepresentation:
        """Decision Tree: Multi-level conditional logic for systematic decision making."""

        # Level 1: Score threshold
        score_condition = ConditionNode(
            "condition",
            condition_type="score_threshold",
            parameters={"threshold": 40, "operator": "greater_than"}
        )

        # Level 2: Action count for high scores
        action_count_condition = ConditionNode(
            "condition",
            condition_type="action_count",
            parameters={"count": 15, "operator": "less_than"}
        )

        # Leaf nodes: specific actions
        aggressive_action = ActionNode("action", action_type="ACTION6",
                                     coordinates={"x": random.randint(10, 53), "y": random.randint(10, 53)})
        moderate_action = ActionNode("action", action_type="ACTION4")
        conservative_action = ActionNode("action", action_type="ACTION1")
        safe_action = ActionNode("action", action_type="ACTION2")

        # Build tree structure
        high_score_branch = ConditionalNode(
            "conditional",
            condition=action_count_condition,
            true_branch=aggressive_action,
            false_branch=moderate_action
        )

        low_score_branch = RandomChoiceNode(
            "random_choice",
            choices=[conservative_action, safe_action],
            weights=[0.7, 0.3]
        )

        root = ConditionalNode(
            "conditional",
            condition=score_condition,
            true_branch=high_score_branch,
            false_branch=low_score_branch
        )

        algorithm = AlgorithmRepresentation(root)
        algorithm.algorithm_id = "decision_tree_seed_001"
        algorithm.metadata = {
            "original_name": "Decision Tree",
            "category": "Machine Learning",
            "adaptation_notes": "Multi-level conditional logic for systematic decisions"
        }
        return algorithm

    @staticmethod
    def create_hill_climbing_algorithm() -> AlgorithmRepresentation:
        """Hill Climbing: Always try to improve score, with exploration when stuck."""

        # Check if we're making progress
        progress_condition = ConditionNode(
            "condition",
            condition_type="frame_changed",
            parameters={"within_last_actions": 3}
        )

        # If making progress, continue similar actions
        continue_actions = RandomChoiceNode(
            "random_choice",
            choices=[
                ActionNode("action", action_type="ACTION1"),
                ActionNode("action", action_type="ACTION2"),
                ActionNode("action", action_type="ACTION3")
            ],
            weights=[0.4, 0.4, 0.2]
        )

        # If stuck, try exploration
        exploration_sequence = SequenceNode("sequence", children=[
            ActionNode("action", action_type="ACTION6",
                      coordinates={"x": random.randint(0, 63), "y": random.randint(0, 63)}),
            ActionNode("action", action_type="ACTION5")
        ])

        root = ConditionalNode(
            "conditional",
            condition=progress_condition,
            true_branch=continue_actions,
            false_branch=exploration_sequence
        )

        algorithm = AlgorithmRepresentation(root)
        algorithm.algorithm_id = "hill_climbing_seed_001"
        algorithm.metadata = {
            "original_name": "Hill Climbing",
            "category": "Search & Optimization",
            "adaptation_notes": "Score improvement focus with exploration when stuck"
        }
        return algorithm

    @staticmethod
    def create_dijkstra_algorithm() -> AlgorithmRepresentation:
        """Dijkstra's Algorithm: Shortest path logic adapted to action efficiency."""

        # Efficiency-based action selection (shortest path to goal)
        efficiency_condition = ConditionNode(
            "condition",
            condition_type="action_count",
            parameters={"count": 10, "operator": "greater_than"}
        )

        # High efficiency path (few actions, direct approach)
        efficient_path = SequenceNode("sequence", children=[
            ActionNode("action", action_type="ACTION4"),  # Direct action
            ActionNode("action", action_type="ACTION7")   # Completion action
        ])

        # Exploration path (more actions, comprehensive approach)
        exploration_path = SequenceNode("sequence", children=[
            ActionNode("action", action_type="ACTION1"),
            ActionNode("action", action_type="ACTION6",
                      coordinates={"x": 20, "y": 20}),
            ActionNode("action", action_type="ACTION3")
        ])

        root = ConditionalNode(
            "conditional",
            condition=efficiency_condition,
            true_branch=efficient_path,
            false_branch=exploration_path
        )

        algorithm = AlgorithmRepresentation(root)
        algorithm.algorithm_id = "dijkstra_seed_001"
        algorithm.metadata = {
            "original_name": "Dijkstra's Algorithm",
            "category": "Graph & Network Algorithms",
            "adaptation_notes": "Shortest path logic for action efficiency"
        }
        return algorithm

    @staticmethod
    def create_bfs_algorithm() -> AlgorithmRepresentation:
        """Breadth-First Search: Systematic exploration level by level."""

        # Systematic exploration pattern
        exploration_sequence = SequenceNode("sequence", children=[
            ActionNode("action", action_type="ACTION1"),  # Level 1
            ActionNode("action", action_type="ACTION2"),  # Level 1
            ActionNode("action", action_type="ACTION3"),  # Level 1
            ActionNode("action", action_type="ACTION6",   # Level 2 exploration
                      coordinates={"x": 16, "y": 16}),
            ActionNode("action", action_type="ACTION6",   # Level 2 exploration
                      coordinates={"x": 48, "y": 16}),
            ActionNode("action", action_type="ACTION4")   # Level 3
        ])

        algorithm = AlgorithmRepresentation(exploration_sequence)
        algorithm.algorithm_id = "bfs_seed_001"
        algorithm.metadata = {
            "original_name": "Breadth-First Search (BFS)",
            "category": "Search & Optimization",
            "adaptation_notes": "Systematic level-by-level exploration"
        }
        return algorithm

    @staticmethod
    def create_dfs_algorithm() -> AlgorithmRepresentation:
        """Depth-First Search: Deep exploration before backtracking."""

        # Deep exploration condition
        depth_condition = ConditionNode(
            "condition",
            condition_type="score_threshold",
            parameters={"threshold": 30, "operator": "less_than"}
        )

        # Deep exploration path
        deep_exploration = RepeatNode(
            "repeat",
            child=ActionNode("action", action_type="ACTION6",
                           coordinates={"x": random.randint(0, 63), "y": random.randint(0, 63)}),
            repeat_count=3
        )

        # Backtrack and try different approach
        backtrack_sequence = SequenceNode("sequence", children=[
            ActionNode("action", action_type="ACTION5"),  # Reset/backtrack
            ActionNode("action", action_type="ACTION2"),  # Try different path
            ActionNode("action", action_type="ACTION4")   # Continue
        ])

        root = ConditionalNode(
            "conditional",
            condition=depth_condition,
            true_branch=deep_exploration,
            false_branch=backtrack_sequence
        )

        algorithm = AlgorithmRepresentation(root)
        algorithm.algorithm_id = "dfs_seed_001"
        algorithm.metadata = {
            "original_name": "Depth-First Search (DFS)",
            "category": "Search & Optimization",
            "adaptation_notes": "Deep exploration with backtracking strategy"
        }
        return algorithm

    @staticmethod
    def create_simulated_annealing_algorithm() -> AlgorithmRepresentation:
        """Simulated Annealing: Probabilistic optimization with cooling schedule."""

        # "Temperature" based on actions taken (cooling schedule)
        cooling_condition = ConditionNode(
            "condition",
            condition_type="action_count",
            parameters={"count": 20, "operator": "less_than"}
        )

        # High temperature (early game) - more exploration
        high_temp_actions = RandomChoiceNode(
            "random_choice",
            choices=[
                ActionNode("action", action_type="ACTION6",
                          coordinates={"x": random.randint(0, 63), "y": random.randint(0, 63)}),
                ActionNode("action", action_type="ACTION1"),
                ActionNode("action", action_type="ACTION2"),
                ActionNode("action", action_type="ACTION5")
            ],
            weights=[0.4, 0.2, 0.2, 0.2]  # Heavy exploration
        )

        # Low temperature (late game) - more exploitation
        low_temp_actions = RandomChoiceNode(
            "random_choice",
            choices=[
                ActionNode("action", action_type="ACTION3"),
                ActionNode("action", action_type="ACTION4"),
                ActionNode("action", action_type="ACTION7")
            ],
            weights=[0.4, 0.4, 0.2]  # Conservative, goal-oriented
        )

        root = ConditionalNode(
            "conditional",
            condition=cooling_condition,
            true_branch=high_temp_actions,
            false_branch=low_temp_actions
        )

        algorithm = AlgorithmRepresentation(root)
        algorithm.algorithm_id = "simulated_annealing_seed_001"
        algorithm.metadata = {
            "original_name": "Simulated Annealing",
            "category": "Search & Optimization",
            "adaptation_notes": "Cooling schedule for exploration-exploitation balance"
        }
        return algorithm

    @staticmethod
    def create_gradient_descent_algorithm() -> AlgorithmRepresentation:
        """Gradient Descent: Iterative score improvement with momentum."""

        # Check if last actions improved score
        improvement_condition = ConditionNode(
            "condition",
            condition_type="frame_changed",
            parameters={"within_last_actions": 2}
        )

        # Continue in same direction (momentum)
        momentum_actions = RepeatNode(
            "repeat",
            child=RandomChoiceNode(
                "random_choice",
                choices=[
                    ActionNode("action", action_type="ACTION1"),
                    ActionNode("action", action_type="ACTION2")
                ]
            ),
            repeat_count=2
        )

        # Change direction (gradient step) using dynamic coordinates
        from action6_helpers import create_gradient_action6

        gradient_step = RandomChoiceNode(
            "random_choice",
            choices=[
                ActionNode("action", action_type="ACTION3"),
                ActionNode("action", action_type="ACTION4"),
                create_gradient_action6()  # Dynamic gradient descent coordinates
            ],
            weights=[0.3, 0.3, 0.4]
        )

        root = ConditionalNode(
            "conditional",
            condition=improvement_condition,
            true_branch=momentum_actions,
            false_branch=gradient_step
        )

        algorithm = AlgorithmRepresentation(root)
        algorithm.algorithm_id = "gradient_descent_seed_001"
        algorithm.metadata = {
            "original_name": "Gradient Descent",
            "category": "Search & Optimization",
            "adaptation_notes": "Iterative improvement with momentum"
        }
        return algorithm

    @staticmethod
    def create_gradient_ascent_algorithm() -> AlgorithmRepresentation:
        """Gradient Ascent: Maximize score by following steepest ascent direction."""

        # Check if recent actions increased score significantly
        strong_improvement_condition = ConditionNode(
            "condition",
            condition_type="score_threshold",
            parameters={"threshold": 1.0, "operator": "greater_than", "within_last_actions": 3}
        )

        # Aggressive upward movement when improvement detected
        ascent_actions = SequenceNode("sequence", children=[
            ActionNode("action", action_type="ACTION1"),  # Push forward
            ActionNode("action", action_type="ACTION2"),  # Continue ascent
            ActionNode("action", action_type="ACTION4"),  # Maximize gain
        ])

        # Exploration for new gradient when no strong improvement
        exploration_condition = ConditionNode(
            "condition",
            condition_type="frame_changed",
            parameters={"within_last_actions": 1}
        )

        # Small gradient steps to find direction using dynamic coordinates
        from action6_helpers import create_gradient_action6, create_systematic_action6

        gradient_search = RandomChoiceNode(
            "random_choice",
            choices=[
                ActionNode("action", action_type="ACTION3"),
                create_gradient_action6(),  # Dynamic gradient-following coordinates
                create_systematic_action6(),  # Systematic exploration
                ActionNode("action", action_type="ACTION5")
            ],
            weights=[0.3, 0.4, 0.2, 0.1]
        )

        # Random exploration when stuck using dynamic coordinates
        from action6_helpers import create_random_action6

        random_step = RandomChoiceNode(
            "random_choice",
            choices=[
                ActionNode("action", action_type="ACTION1"),
                ActionNode("action", action_type="ACTION2"),
                ActionNode("action", action_type="ACTION3"),
                create_random_action6()  # Dynamic random coordinates
            ]
        )

        # Build conditional tree: Strong improvement -> Ascent, Some change -> Search, No change -> Random
        gradient_exploration = ConditionalNode(
            "conditional",
            condition=exploration_condition,
            true_branch=gradient_search,
            false_branch=random_step
        )

        root = ConditionalNode(
            "conditional",
            condition=strong_improvement_condition,
            true_branch=ascent_actions,
            false_branch=gradient_exploration
        )

        algorithm = AlgorithmRepresentation(root)
        algorithm.algorithm_id = "gradient_ascent_seed_001"
        algorithm.metadata = {
            "original_name": "Gradient Ascent",
            "category": "Search & Optimization",
            "adaptation_notes": "Maximize score by following steepest ascent direction with exploration"
        }
        return algorithm

    @staticmethod
    def create_knn_algorithm() -> AlgorithmRepresentation:
        """K-Nearest Neighbors: Pattern matching based on similar game states."""

        # High score state (similar to successful patterns)
        successful_pattern_condition = ConditionNode(
            "condition",
            condition_type="score_threshold",
            parameters={"threshold": 60, "operator": "greater_than"}
        )

        # Replicate successful patterns
        successful_actions = SequenceNode("sequence", children=[
            ActionNode("action", action_type="ACTION4"),  # Continue success
            ActionNode("action", action_type="ACTION7")   # Complete
        ])

        # For unknown patterns, use ensemble approach
        ensemble_actions = RandomChoiceNode(
            "random_choice",
            choices=[
                ActionNode("action", action_type="ACTION1"),
                ActionNode("action", action_type="ACTION2"),
                ActionNode("action", action_type="ACTION3"),
                ActionNode("action", action_type="ACTION6",
                          coordinates={"x": 25, "y": 25})
            ],
            weights=[0.25, 0.25, 0.25, 0.25]  # Equal weighting
        )

        root = ConditionalNode(
            "conditional",
            condition=successful_pattern_condition,
            true_branch=successful_actions,
            false_branch=ensemble_actions
        )

        algorithm = AlgorithmRepresentation(root)
        algorithm.algorithm_id = "knn_seed_001"
        algorithm.metadata = {
            "original_name": "K-Nearest Neighbors (KNN)",
            "category": "Machine Learning",
            "adaptation_notes": "Pattern matching for similar game states"
        }
        return algorithm

    @staticmethod
    def create_quick_sort_algorithm() -> AlgorithmRepresentation:
        """Quick Sort: Divide and conquer action prioritization."""

        # Partition condition (divide strategy)
        partition_condition = ConditionNode(
            "condition",
            condition_type="action_count",
            parameters={"count": 12, "operator": "less_than"}
        )

        # First partition: high priority actions
        high_priority = SequenceNode("sequence", children=[
            ActionNode("action", action_type="ACTION1"),  # Foundation
            ActionNode("action", action_type="ACTION3"),  # Build
            ActionNode("action", action_type="ACTION7")   # Complete
        ])

        # Second partition: exploratory actions
        exploratory = SequenceNode("sequence", children=[
            ActionNode("action", action_type="ACTION6",
                      coordinates={"x": 10, "y": 10}),
            ActionNode("action", action_type="ACTION6",
                      coordinates={"x": 50, "y": 50}),
            ActionNode("action", action_type="ACTION4")
        ])

        root = ConditionalNode(
            "conditional",
            condition=partition_condition,
            true_branch=high_priority,
            false_branch=exploratory
        )

        algorithm = AlgorithmRepresentation(root)
        algorithm.algorithm_id = "quick_sort_seed_001"
        algorithm.metadata = {
            "original_name": "Quick Sort",
            "category": "Sorting & Ordering",
            "adaptation_notes": "Divide and conquer action prioritization"
        }
        return algorithm

    @staticmethod
    def create_binary_search_algorithm() -> AlgorithmRepresentation:
        """Binary Search: Systematic elimination strategy."""

        # Mid-point exploration strategy
        mid_score_condition = ConditionNode(
            "condition",
            condition_type="score_threshold",
            parameters={"threshold": 50, "operator": "greater_than"}
        )

        # Upper half search
        upper_search = ActionNode("action", action_type="ACTION6",
                                coordinates={"x": 48, "y": 32})  # Upper region

        # Lower half search
        lower_search = ActionNode("action", action_type="ACTION6",
                                coordinates={"x": 16, "y": 32})  # Lower region

        root = ConditionalNode(
            "conditional",
            condition=mid_score_condition,
            true_branch=upper_search,
            false_branch=lower_search
        )

        algorithm = AlgorithmRepresentation(root)
        algorithm.algorithm_id = "binary_search_seed_001"
        algorithm.metadata = {
            "original_name": "Binary Search",
            "category": "Search & Optimization",
            "adaptation_notes": "Systematic elimination with spatial search"
        }
        return algorithm

    @staticmethod
    def create_pagerank_algorithm() -> AlgorithmRepresentation:
        """PageRank: Authority-based action weighting."""

        # Authority condition (high-value game state)
        authority_condition = ConditionNode(
            "condition",
            condition_type="score_threshold",
            parameters={"threshold": 45, "operator": "greater_than"}
        )

        # High authority actions (proven valuable)
        authority_actions = RandomChoiceNode(
            "random_choice",
            choices=[
                ActionNode("action", action_type="ACTION3"),  # High authority
                ActionNode("action", action_type="ACTION4"),  # High authority
                ActionNode("action", action_type="ACTION7")   # Highest authority
            ],
            weights=[0.3, 0.4, 0.3]
        )

        # Lower authority actions (exploration)
        exploration_actions = RandomChoiceNode(
            "random_choice",
            choices=[
                ActionNode("action", action_type="ACTION1"),
                ActionNode("action", action_type="ACTION2"),
                ActionNode("action", action_type="ACTION6",
                          coordinates={"x": random.randint(20, 43), "y": random.randint(20, 43)})
            ],
            weights=[0.3, 0.3, 0.4]
        )

        root = ConditionalNode(
            "conditional",
            condition=authority_condition,
            true_branch=authority_actions,
            false_branch=exploration_actions
        )

        algorithm = AlgorithmRepresentation(root)
        algorithm.algorithm_id = "pagerank_seed_001"
        algorithm.metadata = {
            "original_name": "PageRank Algorithm",
            "category": "Graph & Network Algorithms",
            "adaptation_notes": "Authority-based action ranking and selection"
        }
        return algorithm

    @staticmethod
    def get_all_seeded_algorithms() -> List[AlgorithmRepresentation]:
        """Get all available seeded algorithms."""
        builders = [
            SeededAlgorithmBuilder.create_astar_algorithm,
            SeededAlgorithmBuilder.create_decision_tree_algorithm,
            SeededAlgorithmBuilder.create_hill_climbing_algorithm,
            SeededAlgorithmBuilder.create_dijkstra_algorithm,
            SeededAlgorithmBuilder.create_bfs_algorithm,
            SeededAlgorithmBuilder.create_dfs_algorithm,
            SeededAlgorithmBuilder.create_simulated_annealing_algorithm,
            SeededAlgorithmBuilder.create_gradient_descent_algorithm,
            SeededAlgorithmBuilder.create_gradient_ascent_algorithm,
            SeededAlgorithmBuilder.create_knn_algorithm,
            SeededAlgorithmBuilder.create_quick_sort_algorithm,
            SeededAlgorithmBuilder.create_binary_search_algorithm,
            SeededAlgorithmBuilder.create_pagerank_algorithm,
        ]

        # Additional algorithms to reach 25+ total
        additional_algorithms = [
            SeededAlgorithmBuilder._create_beam_search_algorithm(),
            SeededAlgorithmBuilder._create_naive_bayes_algorithm(),
            SeededAlgorithmBuilder._create_random_forest_algorithm(),
            SeededAlgorithmBuilder._create_merge_sort_algorithm(),
            SeededAlgorithmBuilder._create_heap_sort_algorithm(),
            SeededAlgorithmBuilder._create_kmeans_algorithm(),
            SeededAlgorithmBuilder._create_svm_algorithm(),
            SeededAlgorithmBuilder._create_topological_sort_algorithm(),
            SeededAlgorithmBuilder._create_prims_algorithm(),
            SeededAlgorithmBuilder._create_floyd_warshall_algorithm(),
            SeededAlgorithmBuilder._create_monte_carlo_algorithm(),
            SeededAlgorithmBuilder._create_genetic_algorithm_inspired(),
            SeededAlgorithmBuilder._create_ensemble_algorithm(),
        ]

        all_algorithms = []
        for builder in builders:
            all_algorithms.append(builder())

        for builder in additional_algorithms:
            all_algorithms.append(builder())

        return all_algorithms

    # Additional algorithm implementations
    @staticmethod
    def _create_beam_search_algorithm() -> AlgorithmRepresentation:
        """Beam Search: Limited exploration of most promising options."""
        beam_actions = RandomChoiceNode(
            "random_choice",
            choices=[
                ActionNode("action", action_type="ACTION3"),
                ActionNode("action", action_type="ACTION4"),
                ActionNode("action", action_type="ACTION6", coordinates={"x": 32, "y": 32})
            ],
            weights=[0.4, 0.4, 0.2]
        )

        algorithm = AlgorithmRepresentation(beam_actions)
        algorithm.algorithm_id = "beam_search_seed_001"
        algorithm.metadata = {
            "original_name": "Beam Search",
            "category": "Search & Optimization",
            "adaptation_notes": "Limited exploration of promising actions"
        }
        return algorithm

    @staticmethod
    def _create_naive_bayes_algorithm() -> AlgorithmRepresentation:
        """Naive Bayes: Probabilistic classification based on action independence."""
        # Simple probability-based action selection
        prob_condition = ConditionNode(
            "condition",
            condition_type="score_threshold",
            parameters={"threshold": 35, "operator": "greater_than"}
        )

        high_prob_actions = RandomChoiceNode(
            "random_choice",
            choices=[
                ActionNode("action", action_type="ACTION2"),
                ActionNode("action", action_type="ACTION3")
            ],
            weights=[0.6, 0.4]
        )

        low_prob_actions = ActionNode("action", action_type="ACTION1")

        root = ConditionalNode("conditional", condition=prob_condition,
                             true_branch=high_prob_actions, false_branch=low_prob_actions)

        algorithm = AlgorithmRepresentation(root)
        algorithm.algorithm_id = "naive_bayes_seed_001"
        algorithm.metadata = {
            "original_name": "Naive Bayes Classifier",
            "category": "Machine Learning",
            "adaptation_notes": "Probabilistic action classification"
        }
        return algorithm

    @staticmethod
    def _create_random_forest_algorithm() -> AlgorithmRepresentation:
        """Random Forest: Ensemble of decision strategies."""
        # Multiple decision branches (forest of trees)
        tree1 = ConditionalNode(
            "conditional",
            condition=ConditionNode("condition", condition_type="score_threshold",
                                   parameters={"threshold": 40, "operator": "greater_than"}),
            true_branch=ActionNode("action", action_type="ACTION4"),
            false_branch=ActionNode("action", action_type="ACTION1")
        )

        tree2 = ConditionalNode(
            "conditional",
            condition=ConditionNode("condition", condition_type="action_count",
                                   parameters={"count": 15, "operator": "less_than"}),
            true_branch=ActionNode("action", action_type="ACTION6", coordinates={"x": 25, "y": 25}),
            false_branch=ActionNode("action", action_type="ACTION3")
        )

        forest = RandomChoiceNode("random_choice", choices=[tree1, tree2], weights=[0.5, 0.5])

        algorithm = AlgorithmRepresentation(forest)
        algorithm.algorithm_id = "random_forest_seed_001"
        algorithm.metadata = {
            "original_name": "Random Forest",
            "category": "Machine Learning",
            "adaptation_notes": "Ensemble of decision trees"
        }
        return algorithm

    @staticmethod
    def _create_merge_sort_algorithm() -> AlgorithmRepresentation:
        """Merge Sort: Divide and merge strategy."""
        # Divide phase
        divide_actions = SequenceNode("sequence", children=[
            ActionNode("action", action_type="ACTION1"),
            ActionNode("action", action_type="ACTION2")
        ])

        # Merge phase
        merge_actions = SequenceNode("sequence", children=[
            ActionNode("action", action_type="ACTION3"),
            ActionNode("action", action_type="ACTION4")
        ])

        root = SequenceNode("sequence", children=[divide_actions, merge_actions])

        algorithm = AlgorithmRepresentation(root)
        algorithm.algorithm_id = "merge_sort_seed_001"
        algorithm.metadata = {
            "original_name": "Merge Sort",
            "category": "Sorting & Ordering",
            "adaptation_notes": "Divide and merge action strategy"
        }
        return algorithm

    @staticmethod
    def _create_heap_sort_algorithm() -> AlgorithmRepresentation:
        """Heap Sort: Priority-based action ordering."""
        priority_condition = ConditionNode(
            "condition",
            condition_type="score_threshold",
            parameters={"threshold": 55, "operator": "greater_than"}
        )

        high_priority = ActionNode("action", action_type="ACTION7")  # Highest priority
        medium_priority = ActionNode("action", action_type="ACTION4")

        root = ConditionalNode("conditional", condition=priority_condition,
                             true_branch=high_priority, false_branch=medium_priority)

        algorithm = AlgorithmRepresentation(root)
        algorithm.algorithm_id = "heap_sort_seed_001"
        algorithm.metadata = {
            "original_name": "Heap Sort",
            "category": "Sorting & Ordering",
            "adaptation_notes": "Priority-based action selection"
        }
        return algorithm

    @staticmethod
    def _create_kmeans_algorithm() -> AlgorithmRepresentation:
        """K-Means: Clustering actions into groups."""
        # Cluster 1: Building actions
        cluster1 = RandomChoiceNode("random_choice", choices=[
            ActionNode("action", action_type="ACTION1"),
            ActionNode("action", action_type="ACTION2"),
            ActionNode("action", action_type="ACTION3")
        ])

        # Cluster 2: Exploration actions
        cluster2 = ActionNode("action", action_type="ACTION6",
                            coordinates={"x": random.randint(15, 48), "y": random.randint(15, 48)})

        cluster_condition = ConditionNode(
            "condition",
            condition_type="action_count",
            parameters={"count": 10, "operator": "less_than"}
        )

        root = ConditionalNode("conditional", condition=cluster_condition,
                             true_branch=cluster1, false_branch=cluster2)

        algorithm = AlgorithmRepresentation(root)
        algorithm.algorithm_id = "kmeans_seed_001"
        algorithm.metadata = {
            "original_name": "K-Means Clustering",
            "category": "Machine Learning",
            "adaptation_notes": "Action clustering strategy"
        }
        return algorithm

    @staticmethod
    def _create_svm_algorithm() -> AlgorithmRepresentation:
        """SVM: Optimal separation boundary."""
        # Find optimal decision boundary
        boundary_condition = ConditionNode(
            "condition",
            condition_type="score_threshold",
            parameters={"threshold": 42, "operator": "greater_than"}  # Optimal boundary
        )

        above_boundary = ActionNode("action", action_type="ACTION4")
        below_boundary = ActionNode("action", action_type="ACTION2")

        root = ConditionalNode("conditional", condition=boundary_condition,
                             true_branch=above_boundary, false_branch=below_boundary)

        algorithm = AlgorithmRepresentation(root)
        algorithm.algorithm_id = "svm_seed_001"
        algorithm.metadata = {
            "original_name": "Support Vector Machines (SVM)",
            "category": "Machine Learning",
            "adaptation_notes": "Optimal decision boundary for actions"
        }
        return algorithm

    @staticmethod
    def _create_topological_sort_algorithm() -> AlgorithmRepresentation:
        """Topological Sort: Dependency-ordered actions."""
        # Sequential dependency chain
        dependency_sequence = SequenceNode("sequence", children=[
            ActionNode("action", action_type="ACTION1"),  # Prerequisite
            ActionNode("action", action_type="ACTION2"),  # Depends on ACTION1
            ActionNode("action", action_type="ACTION3"),  # Depends on ACTION2
            ActionNode("action", action_type="ACTION4")   # Final dependent action
        ])

        algorithm = AlgorithmRepresentation(dependency_sequence)
        algorithm.algorithm_id = "topological_sort_seed_001"
        algorithm.metadata = {
            "original_name": "Topological Sort",
            "category": "Graph & Network Algorithms",
            "adaptation_notes": "Dependency-ordered action execution"
        }
        return algorithm

    @staticmethod
    def _create_prims_algorithm() -> AlgorithmRepresentation:
        """Prim's Algorithm: Minimum spanning tree construction."""
        # Build minimum cost spanning structure
        spanning_condition = ConditionNode(
            "condition",
            condition_type="action_count",
            parameters={"count": 8, "operator": "less_than"}
        )

        # Build foundation (minimum cost edges)
        foundation = SequenceNode("sequence", children=[
            ActionNode("action", action_type="ACTION1"),
            ActionNode("action", action_type="ACTION3")
        ])

        # Expand tree (add new edges)
        expansion = ActionNode("action", action_type="ACTION6",
                             coordinates={"x": 30, "y": 30})

        root = ConditionalNode("conditional", condition=spanning_condition,
                             true_branch=foundation, false_branch=expansion)

        algorithm = AlgorithmRepresentation(root)
        algorithm.algorithm_id = "prims_seed_001"
        algorithm.metadata = {
            "original_name": "Prim's Algorithm",
            "category": "Graph & Network Algorithms",
            "adaptation_notes": "Minimum spanning tree construction"
        }
        return algorithm

    @staticmethod
    def _create_floyd_warshall_algorithm() -> AlgorithmRepresentation:
        """Floyd-Warshall: All-pairs shortest path."""
        # Try all possible intermediate paths
        path_exploration = RepeatNode(
            "repeat",
            child=RandomChoiceNode("random_choice", choices=[
                ActionNode("action", action_type="ACTION6", coordinates={"x": 16, "y": 16}),
                ActionNode("action", action_type="ACTION6", coordinates={"x": 32, "y": 32}),
                ActionNode("action", action_type="ACTION6", coordinates={"x": 48, "y": 48})
            ]),
            repeat_count=2
        )

        algorithm = AlgorithmRepresentation(path_exploration)
        algorithm.algorithm_id = "floyd_warshall_seed_001"
        algorithm.metadata = {
            "original_name": "Floyd–Warshall Algorithm",
            "category": "Graph & Network Algorithms",
            "adaptation_notes": "All-pairs shortest path exploration"
        }
        return algorithm

    @staticmethod
    def _create_monte_carlo_algorithm() -> AlgorithmRepresentation:
        """Monte Carlo: Randomized sampling approach."""
        # Pure randomized exploration with sampling
        monte_carlo_actions = RandomChoiceNode(
            "random_choice",
            choices=[
                ActionNode("action", action_type="ACTION1"),
                ActionNode("action", action_type="ACTION2"),
                ActionNode("action", action_type="ACTION3"),
                ActionNode("action", action_type="ACTION4"),
                ActionNode("action", action_type="ACTION5"),
                ActionNode("action", action_type="ACTION6",
                          coordinates={"x": random.randint(0, 63), "y": random.randint(0, 63)}),
                ActionNode("action", action_type="ACTION7")
            ],
            weights=[0.15, 0.15, 0.15, 0.15, 0.1, 0.2, 0.1]
        )

        algorithm = AlgorithmRepresentation(monte_carlo_actions)
        algorithm.algorithm_id = "monte_carlo_seed_001"
        algorithm.metadata = {
            "original_name": "Monte Carlo Method",
            "category": "Numerical & Mathematical",
            "adaptation_notes": "Randomized sampling approach"
        }
        return algorithm

    @staticmethod
    def _create_genetic_algorithm_inspired() -> AlgorithmRepresentation:
        """Genetic Algorithm Inspired: Evolutionary action selection."""
        # Selection pressure based on score
        selection_condition = ConditionNode(
            "condition",
            condition_type="score_threshold",
            parameters={"threshold": 50, "operator": "greater_than"}
        )

        # High fitness actions (survived selection)
        fit_actions = RandomChoiceNode("random_choice", choices=[
            ActionNode("action", action_type="ACTION3"),
            ActionNode("action", action_type="ACTION4"),
            ActionNode("action", action_type="ACTION7")
        ], weights=[0.4, 0.4, 0.2])

        # Mutation/exploration
        mutation_action = ActionNode("action", action_type="ACTION6",
                                   coordinates={"x": random.randint(10, 53), "y": random.randint(10, 53)})

        root = ConditionalNode("conditional", condition=selection_condition,
                             true_branch=fit_actions, false_branch=mutation_action)

        algorithm = AlgorithmRepresentation(root)
        algorithm.algorithm_id = "genetic_inspired_seed_001"
        algorithm.metadata = {
            "original_name": "Genetic Algorithm Inspired",
            "category": "Search & Optimization",
            "adaptation_notes": "Evolutionary selection and mutation"
        }
        return algorithm

    @staticmethod
    def _create_ensemble_algorithm() -> AlgorithmRepresentation:
        """Ensemble Method: Voting among multiple strategies."""
        # Multiple strategy voting
        strategy1 = ActionNode("action", action_type="ACTION1")  # Conservative vote
        strategy2 = ActionNode("action", action_type="ACTION3")  # Moderate vote
        strategy3 = ActionNode("action", action_type="ACTION6",  # Aggressive vote
                             coordinates={"x": 25, "y": 25})

        ensemble_vote = RandomChoiceNode(
            "random_choice",
            choices=[strategy1, strategy2, strategy3],
            weights=[0.3, 0.4, 0.3]  # Weighted voting
        )

        algorithm = AlgorithmRepresentation(ensemble_vote)
        algorithm.algorithm_id = "ensemble_seed_001"
        algorithm.metadata = {
            "original_name": "Ensemble Method",
            "category": "Machine Learning",
            "adaptation_notes": "Voting among multiple strategies"
        }
        return algorithm