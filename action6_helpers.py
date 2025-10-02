#!/usr/bin/env python3
"""
BitterTruth-AI ACTION6 Helper Functions

Helper functions to create ActionNode instances with dynamic coordinate strategies
for full coordinate space exploration (0,0) to (64,64).
"""

from typing import Dict, Any, Optional
from algorithm_representations import ActionNode
from coordinate_strategies import CoordinateStrategy


def create_dynamic_action6(strategy: CoordinateStrategy,
                         params: Optional[Dict[str, Any]] = None) -> ActionNode:
    """Create an ACTION6 node with dynamic coordinate generation.

    Args:
        strategy: Coordinate generation strategy to use
        params: Optional parameters for coordinate generation

    Returns:
        ActionNode configured for dynamic ACTION6 coordinate generation
    """
    return ActionNode(
        node_type="action",  # Required first argument
        action_type="ACTION6",
        coordinate_strategy=strategy.value,
        coordinate_params=params or {}
    )


def create_random_action6() -> ActionNode:
    """Create ACTION6 with random uniform coordinate generation."""
    return create_dynamic_action6(CoordinateStrategy.RANDOM_UNIFORM)


def create_systematic_action6() -> ActionNode:
    """Create ACTION6 with systematic grid exploration."""
    return create_dynamic_action6(CoordinateStrategy.SYSTEMATIC_GRID)


def create_spiral_action6() -> ActionNode:
    """Create ACTION6 with spiral outward exploration."""
    return create_dynamic_action6(CoordinateStrategy.SPIRAL_OUTWARD)


def create_corner_action6() -> ActionNode:
    """Create ACTION6 with corner-focused exploration."""
    return create_dynamic_action6(CoordinateStrategy.CORNER_FOCUSED)


def create_edge_action6() -> ActionNode:
    """Create ACTION6 with edge-focused exploration."""
    return create_dynamic_action6(CoordinateStrategy.EDGE_FOCUSED)


def create_gradient_action6() -> ActionNode:
    """Create ACTION6 with gradient-following coordinates."""
    return create_dynamic_action6(CoordinateStrategy.GRADIENT_FOLLOWING)


def create_clustered_action6() -> ActionNode:
    """Create ACTION6 with clustered exploration around successful coordinates."""
    return create_dynamic_action6(CoordinateStrategy.CLUSTERED_EXPLORATION)


def create_frame_analysis_action6() -> ActionNode:
    """Create ACTION6 with frame analysis for optimal coordinate selection."""
    return create_dynamic_action6(CoordinateStrategy.FRAME_ANALYSIS)


def create_adaptive_action6() -> ActionNode:
    """Create ACTION6 that adapts strategy based on algorithm type.

    The coordinate strategy will be auto-selected by the evaluator
    based on the algorithm ID and game context.
    """
    return ActionNode(
        node_type="action",
        action_type="ACTION6",
        coordinate_strategy=None,  # Will be auto-selected
        coordinate_params={"adaptive": True}
    )


def create_multi_strategy_action6(strategies: list) -> list:
    """Create multiple ACTION6 nodes with different strategies.

    Args:
        strategies: List of CoordinateStrategy values

    Returns:
        List of ActionNode instances with different coordinate strategies
    """
    return [create_dynamic_action6(strategy) for strategy in strategies]


def create_exploration_sequence() -> list:
    """Create a sequence of ACTION6 nodes for comprehensive exploration.

    Returns:
        List of ActionNode instances covering different exploration patterns
    """
    return [
        create_systematic_action6(),    # Start with systematic coverage
        create_gradient_action6(),      # Follow any gradients found
        create_corner_action6(),        # Check corners
        create_edge_action6(),          # Check edges
        create_clustered_action6(),     # Explore around successes
        create_random_action6()         # Fill gaps with random
    ]


def update_algorithms_with_dynamic_coordinates():
    """Helper function to demonstrate updating existing algorithms.

    This shows how to replace static ACTION6 coordinates with dynamic ones.
    """

    # Example transformations:

    # OLD: Static coordinate
    # ActionNode("action", action_type="ACTION6", coordinates={"x": 32, "y": 32})

    # NEW: Dynamic coordinate with systematic exploration
    # create_systematic_action6()

    # OLD: Multiple static coordinates
    # [ActionNode("action", action_type="ACTION6", coordinates={"x": 16, "y": 16}),
    #  ActionNode("action", action_type="ACTION6", coordinates={"x": 48, "y": 48})]

    # NEW: Dynamic exploration sequence
    # create_exploration_sequence()[:2]

    print("Use these patterns to replace static ACTION6 coordinates:")
    print("1. Single systematic: create_systematic_action6()")
    print("2. Gradient following: create_gradient_action6()")
    print("3. Full exploration: create_exploration_sequence()")
    print("4. Adaptive strategy: create_adaptive_action6()")


# Mapping of algorithm types to recommended ACTION6 strategies
ALGORITHM_STRATEGY_MAP = {
    'astar': CoordinateStrategy.SYSTEMATIC_GRID,
    'dijkstra': CoordinateStrategy.SYSTEMATIC_GRID,
    'bfs': CoordinateStrategy.SYSTEMATIC_GRID,
    'dfs': CoordinateStrategy.SPIRAL_OUTWARD,
    'gradient_descent': CoordinateStrategy.GRADIENT_FOLLOWING,
    'gradient_ascent': CoordinateStrategy.GRADIENT_FOLLOWING,
    'hill_climbing': CoordinateStrategy.SPIRAL_OUTWARD,
    'simulated_annealing': CoordinateStrategy.CLUSTERED_EXPLORATION,
    'kmeans': CoordinateStrategy.CLUSTERED_EXPLORATION,
    'knn': CoordinateStrategy.CLUSTERED_EXPLORATION,
    'random': CoordinateStrategy.RANDOM_UNIFORM,
    'conservative': CoordinateStrategy.CORNER_FOCUSED,
    'exploration': CoordinateStrategy.EDGE_FOCUSED,
    'default': CoordinateStrategy.SYSTEMATIC_GRID
}


def get_recommended_action6_for_algorithm(algorithm_name: str) -> ActionNode:
    """Get recommended ACTION6 strategy for a specific algorithm.

    Args:
        algorithm_name: Name/ID of the algorithm

    Returns:
        ActionNode with appropriate coordinate strategy
    """
    algorithm_lower = algorithm_name.lower()

    # Find matching strategy
    for key, strategy in ALGORITHM_STRATEGY_MAP.items():
        if key in algorithm_lower:
            return create_dynamic_action6(strategy)

    # Default to systematic grid
    return create_systematic_action6()


def create_algorithm_specific_action6_sequence(algorithm_name: str) -> list:
    """Create a sequence of ACTION6 nodes optimized for a specific algorithm type.

    Args:
        algorithm_name: Name/ID of the algorithm

    Returns:
        List of ActionNode instances optimized for the algorithm type
    """
    algorithm_lower = algorithm_name.lower()

    if 'gradient' in algorithm_lower:
        return [
            create_gradient_action6(),
            create_systematic_action6(),
            create_clustered_action6()
        ]
    elif 'search' in algorithm_lower or 'astar' in algorithm_lower or 'dijkstra' in algorithm_lower:
        return [
            create_systematic_action6(),
            create_spiral_action6(),
            create_edge_action6()
        ]
    elif 'cluster' in algorithm_lower or 'kmeans' in algorithm_lower:
        return [
            create_clustered_action6(),
            create_corner_action6(),
            create_random_action6()
        ]
    elif 'random' in algorithm_lower:
        return [
            create_random_action6(),
            create_edge_action6(),
            create_corner_action6()
        ]
    else:
        # Default comprehensive sequence
        return create_exploration_sequence()