#!/usr/bin/env python3
"""
BitterTruth-AI Coordinate Strategies

Advanced coordinate generation strategies for ACTION6 to explore
the full 65x65 coordinate space (0,0) to (64,64) intelligently.
"""

import random
import math
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class CoordinateStrategy(Enum):
    """Available coordinate generation strategies."""
    RANDOM_UNIFORM = "random_uniform"
    SYSTEMATIC_GRID = "systematic_grid"
    SPIRAL_OUTWARD = "spiral_outward"
    CORNER_FOCUSED = "corner_focused"
    EDGE_FOCUSED = "edge_focused"
    GRADIENT_FOLLOWING = "gradient_following"
    CLUSTERED_EXPLORATION = "clustered_exploration"
    FRAME_ANALYSIS = "frame_analysis"


@dataclass
class CoordinateContext:
    """Context for coordinate generation."""
    current_score: float = 0.0
    previous_score: float = 0.0
    actions_taken: int = 0
    successful_coordinates: List[Tuple[int, int]] = None
    frame: List[List[int]] = None
    algorithm_id: str = ""

    def __post_init__(self):
        if self.successful_coordinates is None:
            self.successful_coordinates = []


class CoordinateGenerator:
    """Generates intelligent ACTION6 coordinates based on strategy and context."""

    def __init__(self):
        self.coordinate_history = {}  # Track coordinates by algorithm
        self.success_clusters = {}    # Track successful coordinate clusters
        self.grid_positions = {}      # Track systematic grid exploration

    def generate_coordinates(self, strategy: CoordinateStrategy,
                           context: CoordinateContext = None) -> Tuple[int, int]:
        """Generate coordinates based on strategy and context.

        Args:
            strategy: Coordinate generation strategy
            context: Optional context for adaptive generation

        Returns:
            Tuple of (x, y) coordinates
        """
        if context is None:
            context = CoordinateContext()

        # Ensure coordinates are within bounds [0, 64]
        x, y = self._generate_raw_coordinates(strategy, context)
        x = max(0, min(64, x))
        y = max(0, min(64, y))

        # Track coordinate usage
        alg_id = context.algorithm_id
        if alg_id not in self.coordinate_history:
            self.coordinate_history[alg_id] = []
        self.coordinate_history[alg_id].append((x, y))

        logger.debug(f"Generated coordinates ({x}, {y}) using {strategy.value}")
        return x, y

    def _generate_raw_coordinates(self, strategy: CoordinateStrategy,
                                context: CoordinateContext) -> Tuple[int, int]:
        """Generate raw coordinates before bounds checking."""

        if strategy == CoordinateStrategy.RANDOM_UNIFORM:
            return self._random_uniform()

        elif strategy == CoordinateStrategy.SYSTEMATIC_GRID:
            return self._systematic_grid(context)

        elif strategy == CoordinateStrategy.SPIRAL_OUTWARD:
            return self._spiral_outward(context)

        elif strategy == CoordinateStrategy.CORNER_FOCUSED:
            return self._corner_focused(context)

        elif strategy == CoordinateStrategy.EDGE_FOCUSED:
            return self._edge_focused()

        elif strategy == CoordinateStrategy.GRADIENT_FOLLOWING:
            return self._gradient_following(context)

        elif strategy == CoordinateStrategy.CLUSTERED_EXPLORATION:
            return self._clustered_exploration(context)

        elif strategy == CoordinateStrategy.FRAME_ANALYSIS:
            return self._frame_analysis(context)

        else:
            # Fallback to random
            return self._random_uniform()

    def _random_uniform(self) -> Tuple[int, int]:
        """Random uniform distribution across coordinate space."""
        return random.randint(0, 63), random.randint(0, 63)

    def _systematic_grid(self, context: CoordinateContext) -> Tuple[int, int]:
        """Systematic grid exploration (8x8 grid)."""
        alg_id = context.algorithm_id

        if alg_id not in self.grid_positions:
            self.grid_positions[alg_id] = 0

        # 8x8 grid positions (9x9 coordinates including boundaries)
        grid_size = 8
        position = self.grid_positions[alg_id]
        grid_x = position % grid_size
        grid_y = position // grid_size

        # Convert grid position to coordinates
        x = int(grid_x * (64 / (grid_size - 1)))
        y = int(grid_y * (64 / (grid_size - 1)))

        # Advance grid position
        self.grid_positions[alg_id] = (position + 1) % (grid_size * grid_size)

        return x, y

    def _spiral_outward(self, context: CoordinateContext) -> Tuple[int, int]:
        """Spiral outward from center (32, 32)."""
        actions = context.actions_taken

        # Calculate spiral position
        center_x, center_y = 32, 32
        layer = int(math.sqrt(actions // 4)) + 1
        position_in_layer = actions % (layer * 8) if layer > 0 else 0

        if layer == 0:
            return center_x, center_y

        # Calculate position on spiral
        if position_in_layer < layer * 2:
            # Top edge
            x = center_x - layer + position_in_layer
            y = center_y - layer
        elif position_in_layer < layer * 4:
            # Right edge
            x = center_x + layer
            y = center_y - layer + (position_in_layer - layer * 2)
        elif position_in_layer < layer * 6:
            # Bottom edge
            x = center_x + layer - (position_in_layer - layer * 4)
            y = center_y + layer
        else:
            # Left edge
            x = center_x - layer
            y = center_y + layer - (position_in_layer - layer * 6)

        # Clamp to valid bounds
        x = min(max(x, 0), 63)
        y = min(max(y, 0), 63)
        return x, y

    def _corner_focused(self, context: CoordinateContext) -> Tuple[int, int]:
        """Focus on corners with occasional center exploration."""
        corners = [(0, 0), (0, 63), (63, 0), (63, 63)]
        center_points = [(32, 32), (16, 16), (48, 48), (16, 48), (48, 16)]

        # 70% corners, 30% center exploration
        if random.random() < 0.7:
            return random.choice(corners)
        else:
            return random.choice(center_points)

    def _edge_focused(self) -> Tuple[int, int]:
        """Focus on edges of the coordinate space."""
        edge_choice = random.randint(0, 3)

        if edge_choice == 0:  # Top edge
            return random.randint(0, 63), 0
        elif edge_choice == 1:  # Bottom edge
            return random.randint(0, 63), 63
        elif edge_choice == 2:  # Left edge
            return 0, random.randint(0, 63)
        else:  # Right edge
            return 63, random.randint(0, 63)

    def _gradient_following(self, context: CoordinateContext) -> Tuple[int, int]:
        """Follow score gradients by analyzing recent successful coordinates."""
        if context.current_score > context.previous_score and context.successful_coordinates:
            # Score improved - bias toward recent successful coordinates
            if len(context.successful_coordinates) > 0:
                base_x, base_y = context.successful_coordinates[-1]

                # Add random variation around successful coordinate
                variation = 8  # 8-unit variation
                x = base_x + random.randint(-variation, variation)
                y = base_y + random.randint(-variation, variation)
                
                # Clamp to valid bounds
                x = min(max(x, 0), 63)
                y = min(max(y, 0), 63)
                return x, y

        # No gradient info - use systematic exploration
        return self._systematic_grid(context)

    def _clustered_exploration(self, context: CoordinateContext) -> Tuple[int, int]:
        """Explore around clusters of successful coordinates."""
        alg_id = context.algorithm_id

        if alg_id in self.success_clusters and len(self.success_clusters[alg_id]) > 0:
            # Choose random cluster center
            cluster_center = random.choice(self.success_clusters[alg_id])

            # Explore around cluster with decreasing probability by distance
            max_distance = 16
            distance = random.expovariate(1/8)  # Exponential distribution
            distance = min(distance, max_distance)

            angle = random.uniform(0, 2 * math.pi)
            x = cluster_center[0] + int(distance * math.cos(angle))
            y = cluster_center[1] + int(distance * math.sin(angle))

            # Clamp to valid bounds
            x = min(max(x, 0), 63)
            y = min(max(y, 0), 63)
            return x, y

        # No clusters yet - random exploration
        return self._random_uniform()

    def _frame_analysis(self, context: CoordinateContext) -> Tuple[int, int]:
        """Analyze game frame to find optimal coordinates (advanced)."""
        if context.frame is None or len(context.frame) == 0:
            return self._random_uniform()

        # Simple frame analysis - find non-zero areas
        try:
            frame_height = len(context.frame)
            frame_width = len(context.frame[0]) if frame_height > 0 else 0

            if frame_width == 0 or frame_height == 0:
                return self._random_uniform()

            # Find areas with activity (non-zero values)
            active_regions = []
            for y in range(0, frame_height, 4):  # Sample every 4th pixel
                for x in range(0, frame_width, 4):
                    if context.frame[y][x] != 0:
                        # Scale coordinates to ACTION6 space
                        scaled_x = int((x / frame_width) * 64)
                        scaled_y = int((y / frame_height) * 64)
                        active_regions.append((scaled_x, scaled_y))

            if active_regions:
                return random.choice(active_regions)

        except Exception as e:
            logger.warning(f"Frame analysis failed: {e}")

        return self._random_uniform()

    def update_success(self, algorithm_id: str, coordinates: Tuple[int, int],
                      score_improvement: float):
        """Update success tracking for coordinate generation."""
        if score_improvement > 0:
            # Add to successful coordinates
            if algorithm_id not in self.success_clusters:
                self.success_clusters[algorithm_id] = []

            self.success_clusters[algorithm_id].append(coordinates)

            # Keep only recent successes (last 20)
            if len(self.success_clusters[algorithm_id]) > 20:
                self.success_clusters[algorithm_id] = self.success_clusters[algorithm_id][-20:]

    def get_strategy_for_algorithm(self, algorithm_id: str,
                                 actions_taken: int = 0) -> CoordinateStrategy:
        """Get recommended coordinate strategy for an algorithm type."""
        alg_lower = algorithm_id.lower()

        # Algorithm-specific strategy mapping
        if 'astar' in alg_lower or 'dijkstra' in alg_lower:
            return CoordinateStrategy.SYSTEMATIC_GRID
        elif 'gradient' in alg_lower:
            return CoordinateStrategy.GRADIENT_FOLLOWING
        elif 'hill_climbing' in alg_lower or 'simulated_annealing' in alg_lower:
            return CoordinateStrategy.SPIRAL_OUTWARD
        elif 'bfs' in alg_lower or 'dfs' in alg_lower:
            return CoordinateStrategy.SYSTEMATIC_GRID
        elif 'random' in alg_lower:
            return CoordinateStrategy.RANDOM_UNIFORM
        elif 'kmeans' in alg_lower or 'knn' in alg_lower:
            return CoordinateStrategy.CLUSTERED_EXPLORATION
        elif actions_taken < 50:
            # Early exploration - use systematic
            return CoordinateStrategy.SYSTEMATIC_GRID
        elif actions_taken < 100:
            # Mid-game - try gradient following
            return CoordinateStrategy.GRADIENT_FOLLOWING
        else:
            # Late game - clustered exploration
            return CoordinateStrategy.CLUSTERED_EXPLORATION

    def get_algorithm_statistics(self) -> Dict[str, Any]:
        """Get statistics about coordinate usage."""
        stats = {
            "total_algorithms": len(self.coordinate_history),
            "total_coordinates_generated": sum(len(coords) for coords in self.coordinate_history.values()),
            "algorithms_with_clusters": len(self.success_clusters),
            "total_successful_coordinates": sum(len(coords) for coords in self.success_clusters.values())
        }

        # Coverage analysis
        all_coordinates = []
        for coords in self.coordinate_history.values():
            all_coordinates.extend(coords)

        if all_coordinates:
            unique_coordinates = set(all_coordinates)
            total_possible = 65 * 65  # 0-64 inclusive
            stats["coordinate_coverage"] = len(unique_coordinates) / total_possible
            stats["unique_coordinates"] = len(unique_coordinates)

        return stats


# Global coordinate generator instance
coordinate_generator = CoordinateGenerator()


def generate_action6_coordinates(algorithm_id: str = "",
                               current_score: float = 0.0,
                               previous_score: float = 0.0,
                               actions_taken: int = 0,
                               frame: List[List[int]] = None,
                               strategy: CoordinateStrategy = None,
                               use_smart_engine: bool = True) -> Tuple[int, int]:
    """Convenience function to generate ACTION6 coordinates.

    Args:
        algorithm_id: ID of the algorithm requesting coordinates
        current_score: Current game score
        previous_score: Previous game score
        actions_taken: Number of actions taken so far
        frame: Current game frame (optional)
        strategy: Specific strategy to use (optional, auto-selected if None)
        use_smart_engine: Enable revolutionary smart coordinate generation

    Returns:
        Tuple of (x, y) coordinates
    """
    # CRITICAL FIX: Ensure scores are numeric, not lists
    try:
        if isinstance(current_score, (list, tuple)):
            logger.warning(f"Current score is list/tuple: {current_score}, taking first element")
            current_score = current_score[0] if len(current_score) > 0 else 0.0
        elif not isinstance(current_score, (int, float)):
            logger.warning(f"Current score is not numeric: {type(current_score)} {current_score}, using 0.0")
            current_score = 0.0
        current_score = float(current_score)

        if isinstance(previous_score, (list, tuple)):
            logger.warning(f"Previous score is list/tuple: {previous_score}, taking first element")
            previous_score = previous_score[0] if len(previous_score) > 0 else 0.0
        elif not isinstance(previous_score, (int, float)):
            logger.warning(f"Previous score is not numeric: {type(previous_score)} {previous_score}, using 0.0")
            previous_score = 0.0
        previous_score = float(previous_score)
    except (TypeError, ValueError, IndexError) as e:
        logger.warning(f"Score type conversion failed: {e}")
        current_score = 0.0
        previous_score = 0.0

    # ===== REVOLUTIONARY SMART COORDINATE GENERATION =====
    if use_smart_engine:
        try:
            from smart_coordinate_engine import generate_smart_coordinates, update_smart_coordinate_performance

            # Use the revolutionary smart coordinate engine
            coordinates = generate_smart_coordinates(
                algorithm_id=algorithm_id,
                current_score=current_score,
                previous_score=previous_score,
                actions_taken=actions_taken
            )

            # Update performance tracking if score improved
            if current_score > previous_score:
                score_improvement = current_score - previous_score
                update_smart_coordinate_performance(coordinates[0], coordinates[1], score_improvement)
                logger.info(f"[SMART ENGINE] Coordinate success recorded: {coordinates}, improvement: {score_improvement:.3f}")
            elif current_score <= previous_score and actions_taken > 0:
                # Record failure/no improvement
                update_smart_coordinate_performance(coordinates[0], coordinates[1], 0.0)

            logger.info(f"[SMART ENGINE] Generated coordinates: {coordinates} for {algorithm_id}")
            return coordinates

        except ImportError:
            logger.warning("Smart coordinate engine not available, falling back to legacy system")
        except Exception as e:
            logger.warning(f"Smart coordinate engine failed: {e}, falling back to legacy system")
    
    context = CoordinateContext(
        current_score=current_score,
        previous_score=previous_score,
        actions_taken=actions_taken,
        frame=frame,
        algorithm_id=algorithm_id
    )

    if strategy is None:
        strategy = coordinate_generator.get_strategy_for_algorithm(algorithm_id, actions_taken)

    coordinates = coordinate_generator.generate_coordinates(strategy, context)

    # Track success if score improved
    try:
        # CRITICAL FIX: Ensure both scores are numbers before comparison/subtraction
        if isinstance(current_score, (list, tuple)):
            logger.warning(f"Current score is list/tuple: {current_score}, taking first element")
            current_score = current_score[0] if len(current_score) > 0 else 0.0
        elif not isinstance(current_score, (int, float)):
            logger.warning(f"Current score is not numeric: {type(current_score)} {current_score}, using 0.0")
            current_score = 0.0

        if isinstance(previous_score, (list, tuple)):
            logger.warning(f"Previous score is list/tuple: {previous_score}, taking first element")
            previous_score = previous_score[0] if len(previous_score) > 0 else 0.0
        elif not isinstance(previous_score, (int, float)):
            logger.warning(f"Previous score is not numeric: {type(previous_score)} {previous_score}, using 0.0")
            previous_score = 0.0

        if float(current_score) > float(previous_score):
            score_improvement = float(current_score) - float(previous_score)
            coordinate_generator.update_success(algorithm_id, coordinates, score_improvement)
    except (TypeError, ValueError) as e:
        logger.warning(f"Score comparison failed - current_score: {type(current_score)} {current_score}, previous_score: {type(previous_score)} {previous_score}. Error: {e}")
    except Exception as e:
        logger.warning(f"Unexpected error in score tracking: {e}")

    return coordinates