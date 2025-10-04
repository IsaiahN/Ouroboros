#!/usr/bin/env python3
"""
REVOLUTIONARY SMART COORDINATE GENERATION ENGINE
================================================================
Phase 1 Implementation: +180% improvement target

Replaces static (32,32) pattern with intelligent coordinate selection
based on success heat maps and failure avoidance.
"""

import json
import math
import random
import sqlite3
import logging
from typing import Tuple, Dict, List, Any, Optional
from dataclasses import dataclass
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class CoordinatePerformance:
    """Track performance of specific coordinate regions."""
    attempts: int = 0
    successes: int = 0
    total_score_improvement: float = 0.0
    avg_score_improvement: float = 0.0
    success_rate: float = 0.0
    last_used: float = 0.0  # timestamp

    def update(self, score_improvement: float):
        """Update performance metrics."""
        self.attempts += 1
        if score_improvement > 0:
            self.successes += 1
            self.total_score_improvement += score_improvement

        self.success_rate = self.successes / self.attempts if self.attempts > 0 else 0.0
        self.avg_score_improvement = self.total_score_improvement / self.attempts if self.attempts > 0 else 0.0

class SmartCoordinateEngine:
    """Revolutionary coordinate generation with learning and adaptation."""

    def __init__(self, grid_size: int = 16, db_path: str = "core_data.db"):
        """Initialize the smart coordinate engine.

        Args:
            grid_size: Size of analysis grid (16x16 = 256 regions)
            db_path: Database path for persistence
        """
        self.grid_size = grid_size
        self.cell_size = 64 // grid_size  # Size of each grid cell
        self.db_path = db_path

        # Performance tracking per grid cell
        self.grid_performance: Dict[Tuple[int, int], CoordinatePerformance] = defaultdict(CoordinatePerformance)

        # Heat maps for visualization and analysis
        self.success_heat_map = np.zeros((grid_size, grid_size))
        self.failure_heat_map = np.zeros((grid_size, grid_size))

        # Exploration tracking
        self.unexplored_cells = set()
        self.initialize_exploration_grid()

        # Learning parameters
        self.exploration_bonus = 2.0  # Bonus for unexplored areas
        self.recency_weight = 0.95   # Exponential decay for old data
        self.min_attempts_for_confidence = 5  # Minimum attempts for reliable statistics

        # Load historical data
        self.load_historical_performance()

        logger.info(f"SmartCoordinateEngine initialized with {grid_size}x{grid_size} grid")

    def initialize_exploration_grid(self):
        """Initialize all grid cells as unexplored."""
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                self.unexplored_cells.add((i, j))

    def load_historical_performance(self):
        """Load historical coordinate performance from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Query historical ACTION6 coordinate data
            cursor.execute("""
                SELECT coordinates, score_change
                FROM action_traces
                WHERE action_number = 6
                AND coordinates IS NOT NULL
                AND score_change IS NOT NULL
                ORDER BY timestamp DESC
                LIMIT 10000
            """)

            historical_data = cursor.fetchall()

            for coord_json, score_change in historical_data:
                try:
                    coord_data = json.loads(coord_json)
                    x, y = coord_data.get('x', 32), coord_data.get('y', 32)

                    # Convert to grid cell
                    grid_x, grid_y = self.coordinate_to_grid(x, y)

                    # Update performance
                    self.grid_performance[(grid_x, grid_y)].update(score_change)

                    # Remove from unexplored if we have data
                    self.unexplored_cells.discard((grid_x, grid_y))

                except (json.JSONDecodeError, KeyError, TypeError):
                    continue

            self.update_heat_maps()
            conn.close()

            logger.info(f"Loaded {len(historical_data)} historical coordinate records")
            logger.info(f"Unexplored regions: {len(self.unexplored_cells)}/{self.grid_size**2}")

        except Exception as e:
            logger.warning(f"Could not load historical performance: {e}")

    def coordinate_to_grid(self, x: int, y: int) -> Tuple[int, int]:
        """Convert coordinate to grid cell."""
        grid_x = min(x // self.cell_size, self.grid_size - 1)
        grid_y = min(y // self.cell_size, self.grid_size - 1)
        return grid_x, grid_y

    def grid_to_coordinate(self, grid_x: int, grid_y: int, jitter: bool = True) -> Tuple[int, int]:
        """Convert grid cell to coordinate with optional jitter."""
        base_x = grid_x * self.cell_size + self.cell_size // 2
        base_y = grid_y * self.cell_size + self.cell_size // 2

        if jitter:
            # Add random jitter within cell
            jitter_range = self.cell_size // 4
            x = base_x + random.randint(-jitter_range, jitter_range)
            y = base_y + random.randint(-jitter_range, jitter_range)
        else:
            x, y = base_x, base_y

        # Clamp to valid bounds
        x = max(0, min(63, x))
        y = max(0, min(63, y))

        return x, y

    def update_heat_maps(self):
        """Update heat maps from performance data."""
        self.success_heat_map.fill(0)
        self.failure_heat_map.fill(0)

        for (grid_x, grid_y), perf in self.grid_performance.items():
            if perf.attempts > 0:
                self.success_heat_map[grid_y, grid_x] = perf.success_rate
                self.failure_heat_map[grid_y, grid_x] = 1.0 - perf.success_rate

    def calculate_cell_value(self, grid_x: int, grid_y: int) -> float:
        """Calculate the value/attractiveness of a grid cell."""
        perf = self.grid_performance[(grid_x, grid_y)]

        # Base value from success rate and score improvement
        base_value = perf.success_rate + (perf.avg_score_improvement * 10)

        # Exploration bonus for unexplored/under-explored cells
        if (grid_x, grid_y) in self.unexplored_cells:
            exploration_value = self.exploration_bonus
        elif perf.attempts < self.min_attempts_for_confidence:
            exploration_value = self.exploration_bonus * (1.0 - perf.attempts / self.min_attempts_for_confidence)
        else:
            exploration_value = 0.0

        # Penalty for known bad regions
        if perf.attempts >= self.min_attempts_for_confidence and perf.success_rate == 0.0:
            penalty = -1.0
        else:
            penalty = 0.0

        # Recency bonus (favor recently successful areas)
        recency_bonus = 0.0  # TODO: Implement based on timestamp

        total_value = base_value + exploration_value + penalty + recency_bonus

        return total_value

    def select_best_coordinate(self, algorithm_id: str = "", game_context: Dict = None) -> Tuple[int, int]:
        """Select the best coordinate using intelligent strategy."""

        # Calculate values for all grid cells
        cell_values = {}
        for grid_x in range(self.grid_size):
            for grid_y in range(self.grid_size):
                cell_values[(grid_x, grid_y)] = self.calculate_cell_value(grid_x, grid_y)

        # Strategy selection based on algorithm and context
        strategy = self.select_strategy(algorithm_id, game_context)

        if strategy == "exploit_best":
            # Pure exploitation - select highest value cell
            best_cell = max(cell_values.items(), key=lambda x: x[1])
            grid_x, grid_y = best_cell[0]

        elif strategy == "explore_unknown":
            # Pure exploration - select random unexplored cell
            if self.unexplored_cells:
                grid_x, grid_y = random.choice(list(self.unexplored_cells))
            else:
                # All explored - select least explored
                min_attempts = min(self.grid_performance[cell].attempts
                                 for cell in cell_values.keys())
                candidates = [cell for cell, perf in self.grid_performance.items()
                            if perf.attempts == min_attempts]
                grid_x, grid_y = random.choice(candidates)

        elif strategy == "epsilon_greedy":
            # Epsilon-greedy: 80% exploitation, 20% exploration
            if random.random() < 0.8:
                # Exploit - select from top 25% cells
                sorted_cells = sorted(cell_values.items(), key=lambda x: x[1], reverse=True)
                top_quartile = sorted_cells[:max(1, len(sorted_cells) // 4)]
                grid_x, grid_y = random.choice(top_quartile)[0]
            else:
                # Explore - prefer unexplored or under-explored
                exploration_candidates = list(self.unexplored_cells)
                if not exploration_candidates:
                    exploration_candidates = [cell for cell, perf in self.grid_performance.items()
                                            if perf.attempts < self.min_attempts_for_confidence]
                if exploration_candidates:
                    grid_x, grid_y = random.choice(exploration_candidates)
                else:
                    grid_x, grid_y = random.choice(list(cell_values.keys()))

        else:  # "adaptive_probabilistic"
            # Probabilistic selection based on cell values
            # Convert values to probabilities using softmax
            values = list(cell_values.values())
            if max(values) > min(values):
                # Apply softmax with temperature
                temperature = 2.0
                exp_values = [math.exp(v / temperature) for v in values]
                total = sum(exp_values)
                probabilities = [ev / total for ev in exp_values]

                # Sample based on probabilities
                cells = list(cell_values.keys())
                selected_idx = np.random.choice(len(cells), p=probabilities)
                grid_x, grid_y = cells[selected_idx]
            else:
                # All cells have equal value - random selection
                grid_x, grid_y = random.choice(list(cell_values.keys()))

        # Convert grid cell to coordinate
        coordinate = self.grid_to_coordinate(grid_x, grid_y)

        logger.debug(f"Selected coordinate {coordinate} from grid cell ({grid_x}, {grid_y}) "
                    f"using strategy {strategy}, value: {cell_values[(grid_x, grid_y)]:.3f}")

        return coordinate

    def select_strategy(self, algorithm_id: str, game_context: Dict = None) -> str:
        """Select coordinate selection strategy based on algorithm and context."""

        if game_context is None:
            game_context = {}

        actions_taken = game_context.get('actions_taken', 0)
        current_score = game_context.get('current_score', 0.0)

        # Early game: Heavy exploration
        if actions_taken < 50:
            return "explore_unknown"

        # Mid game: Balanced exploration/exploitation
        elif actions_taken < 200:
            return "epsilon_greedy"

        # Late game: Exploit known good areas
        elif actions_taken < 1000:
            return "adaptive_probabilistic"

        # Very late game: Pure exploitation
        else:
            return "exploit_best"

    def update_coordinate_performance(self, x: int, y: int, score_change: float):
        """Update performance tracking for a coordinate."""
        grid_x, grid_y = self.coordinate_to_grid(x, y)

        # Update performance
        self.grid_performance[(grid_x, grid_y)].update(score_change)

        # Remove from unexplored
        self.unexplored_cells.discard((grid_x, grid_y))

        # Update heat maps
        self.update_heat_maps()

        logger.debug(f"Updated coordinate ({x}, {y}) -> grid ({grid_x}, {grid_y}), "
                    f"score_change: {score_change:.3f}")

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        total_attempts = sum(perf.attempts for perf in self.grid_performance.values())
        total_successes = sum(perf.successes for perf in self.grid_performance.values())
        total_score_improvement = sum(perf.total_score_improvement for perf in self.grid_performance.values())

        explored_cells = len(self.grid_performance) - len(self.unexplored_cells)

        # Find best performing regions
        best_cells = sorted(
            [(cell, perf) for cell, perf in self.grid_performance.items() if perf.attempts >= 3],
            key=lambda x: x[1].success_rate * x[1].avg_score_improvement,
            reverse=True
        )[:5]

        # Find worst performing regions
        worst_cells = sorted(
            [(cell, perf) for cell, perf in self.grid_performance.items() if perf.attempts >= 5],
            key=lambda x: x[1].success_rate,
        )[:5]

        return {
            "total_attempts": total_attempts,
            "total_successes": total_successes,
            "overall_success_rate": total_successes / total_attempts if total_attempts > 0 else 0.0,
            "total_score_improvement": total_score_improvement,
            "explored_cells": explored_cells,
            "unexplored_cells": len(self.unexplored_cells),
            "exploration_progress": explored_cells / (self.grid_size ** 2),
            "best_regions": [
                {
                    "grid_cell": cell,
                    "coordinate": self.grid_to_coordinate(cell[0], cell[1], jitter=False),
                    "success_rate": perf.success_rate,
                    "avg_improvement": perf.avg_score_improvement,
                    "attempts": perf.attempts
                }
                for cell, perf in best_cells
            ],
            "worst_regions": [
                {
                    "grid_cell": cell,
                    "coordinate": self.grid_to_coordinate(cell[0], cell[1], jitter=False),
                    "success_rate": perf.success_rate,
                    "attempts": perf.attempts
                }
                for cell, perf in worst_cells
            ]
        }

    @property
    def coordinate_performances(self):
        """Compatibility property for accessing grid performance data."""
        return self.grid_performance

# Global instance
smart_coordinate_engine = SmartCoordinateEngine()

def generate_smart_coordinates(algorithm_id: str = "",
                             current_score: float = 0.0,
                             previous_score: float = 0.0,
                             actions_taken: int = 0,
                             **kwargs) -> Tuple[int, int]:
    """Generate smart coordinates using the new engine.

    This is a drop-in replacement for the existing coordinate generation.
    """

    game_context = {
        'current_score': current_score,
        'previous_score': previous_score,
        'actions_taken': actions_taken
    }

    coordinates = smart_coordinate_engine.select_best_coordinate(algorithm_id, game_context)

    logger.info(f"Smart coordinate generation: {coordinates} for {algorithm_id}")

    return coordinates

def update_smart_coordinate_performance(x: int, y: int, score_improvement: float):
    """Update coordinate performance tracking."""
    smart_coordinate_engine.update_coordinate_performance(x, y, score_improvement)

def get_smart_coordinate_statistics() -> Dict[str, Any]:
    """Get smart coordinate system statistics."""
    return smart_coordinate_engine.get_performance_summary()

def record_coordinate_performance(coordinates: Tuple[int, int], algorithm_id: str,
                                 score_change: float, success: bool):
    """Record coordinate performance for tracking."""
    x, y = coordinates
    smart_coordinate_engine.update_coordinate_performance(x, y, score_change)

def get_coordinate_system_status() -> Dict[str, Any]:
    """Get current status of the coordinate system."""
    return {
        "smart_coordinate_active": True,
        "grid_size": smart_coordinate_engine.grid_size,
        "total_coordinates_tracked": len(smart_coordinate_engine.grid_performance),
        "performance_summary": smart_coordinate_engine.get_performance_summary()
    }

if __name__ == "__main__":
    # Test the smart coordinate engine
    engine = SmartCoordinateEngine()

    print("=== SMART COORDINATE ENGINE TEST ===")

    # Generate some test coordinates
    for i in range(10):
        coord = engine.select_best_coordinate(f"test_algorithm_{i % 3}")
        print(f"Generated: {coord}")

        # Simulate some score improvements
        score_improvement = random.uniform(-0.1, 0.5)
        engine.update_coordinate_performance(coord[0], coord[1], score_improvement)

    # Print summary
    summary = engine.get_performance_summary()
    print(f"\nSummary: {summary}")