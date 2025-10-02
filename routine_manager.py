#!/usr/bin/env python3
"""
BitterTruth-AI Routine Manager

Manages game-type specific algorithm sequences and routine optimization.
This component handles switching between algorithms based on game type,
performance metrics, and dynamic conditions during gameplay.
"""

import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from algorithm_representations import AlgorithmRepresentation

logger = logging.getLogger(__name__)


@dataclass
class SwitchCondition:
    """Defines when to switch between algorithms in a routine."""
    condition_type: str  # 'score_threshold', 'action_count', 'time_limit', 'performance_drop', 'level_stagnation', 'score_plateau', 'level_completion', 'efficiency_drop'
    threshold: float
    operator: str  # 'greater_than', 'less_than', 'equal_to'
    consecutive_failures: int = 0


@dataclass
class RoutineStep:
    """A single step in an algorithm routine."""
    algorithm_id: str
    max_actions: int = 50
    switch_conditions: List[SwitchCondition] = None
    priority: int = 1  # Higher priority = more likely to be selected


@dataclass
class AlgorithmRoutine:
    """A complete routine for a specific game type."""
    routine_id: str
    game_type: str
    routine_name: str
    steps: List[RoutineStep]
    success_rate: float = 0.0
    games_tested: int = 0
    levels_completed: int = 0
    avg_actions_per_level: float = 0.0
    last_used: Optional[datetime] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class RoutineManager:
    """Manages algorithm routines for different game types."""

    def __init__(self, database_interface):
        self.db = database_interface
        self.active_routines: Dict[str, AlgorithmRoutine] = {}
        self.game_type_cache: Dict[str, str] = {}
        self.current_routine_state: Dict[str, Dict] = {}

        logger.info("RoutineManager initialized")

    def extract_game_type(self, game_id: str) -> str:
        """Extract game type from game ID (e.g., 'vc33-001' -> 'vc33')."""
        if game_id in self.game_type_cache:
            return self.game_type_cache[game_id]

        # Extract prefix before first dash or underscore
        match = re.match(r'^([a-zA-Z0-9]+)[-_]', game_id)
        if match:
            game_type = match.group(1).lower()
        else:
            # Fallback: use first 4 characters
            game_type = game_id[:4].lower()

        self.game_type_cache[game_id] = game_type
        logger.debug(f"Extracted game type '{game_type}' from game_id '{game_id}'")
        return game_type

    def create_default_routine(self, game_type: str, algorithm_ids: List[str]) -> AlgorithmRoutine:
        """Create a default routine for a game type."""
        routine_id = f"default_{game_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        steps = []
        for i, algo_id in enumerate(algorithm_ids[:3]):  # Limit to 3 algorithms
            conditions = [
                SwitchCondition("action_count", 15.0, "greater_than"),
                SwitchCondition("performance_drop", 0.1, "greater_than", consecutive_failures=3)
            ]

            step = RoutineStep(
                algorithm_id=algo_id,
                max_actions=20,
                switch_conditions=conditions,
                priority=len(algorithm_ids) - i  # First algorithm has highest priority
            )
            steps.append(step)

        routine = AlgorithmRoutine(
            routine_id=routine_id,
            game_type=game_type,
            routine_name=f"Default routine for {game_type}",
            steps=steps
        )

        logger.info(f"Created default routine {routine_id} for game type {game_type}")
        return routine

    def get_best_routine_for_game_type(self, game_type: str) -> Optional[AlgorithmRoutine]:
        """Get the best performing routine for a specific game type."""
        try:
            # Query database for best routine
            query = """
                SELECT routine_id, routine_name, algorithm_sequence, switch_conditions,
                       success_rate, games_tested, levels_completed, avg_actions_per_level,
                       last_used, created_at
                FROM algorithm_routines
                WHERE game_type = ? AND games_tested >= 1
                ORDER BY success_rate DESC, avg_actions_per_level ASC
                LIMIT 1
            """

            result = self.db.execute_query(query, (game_type,))
            if not result:
                logger.debug(f"No routines found for game type {game_type}")
                return None

            row = result[0]

            # Parse algorithm sequence
            algorithm_sequence = json.loads(row[2])
            switch_conditions_data = json.loads(row[3]) if row[3] else []

            # Build routine steps
            steps = []
            for i, algo_id in enumerate(algorithm_sequence):
                conditions = []
                if i < len(switch_conditions_data):
                    for cond_data in switch_conditions_data[i]:
                        condition = SwitchCondition(
                            condition_type=cond_data.get('condition_type', 'action_count'),
                            threshold=cond_data.get('threshold', 15.0),
                            operator=cond_data.get('operator', 'greater_than'),
                            consecutive_failures=cond_data.get('consecutive_failures', 0)
                        )
                        conditions.append(condition)

                step = RoutineStep(
                    algorithm_id=algo_id,
                    max_actions=20,
                    switch_conditions=conditions,
                    priority=len(algorithm_sequence) - i
                )
                steps.append(step)

            routine = AlgorithmRoutine(
                routine_id=row[0],
                game_type=game_type,
                routine_name=row[1],
                steps=steps,
                success_rate=row[4],
                games_tested=row[5],
                levels_completed=row[6],
                avg_actions_per_level=row[7],
                last_used=datetime.fromisoformat(row[8]) if row[8] else None,
                created_at=datetime.fromisoformat(row[9])
            )

            logger.info(f"Retrieved best routine {routine.routine_id} for game type {game_type} "
                       f"(success_rate: {routine.success_rate:.2f})")
            return routine

        except Exception as e:
            logger.error(f"Error retrieving routine for game type {game_type}: {e}")
            return None

    def save_routine(self, routine: AlgorithmRoutine) -> bool:
        """Save a routine to the database."""
        try:
            # Prepare algorithm sequence
            algorithm_sequence = [step.algorithm_id for step in routine.steps]

            # Prepare switch conditions
            switch_conditions = []
            for step in routine.steps:
                step_conditions = []
                if step.switch_conditions:
                    for cond in step.switch_conditions:
                        step_conditions.append({
                            'condition_type': cond.condition_type,
                            'threshold': cond.threshold,
                            'operator': cond.operator,
                            'consecutive_failures': cond.consecutive_failures
                        })
                switch_conditions.append(step_conditions)

            # Insert or update routine
            query = """
                INSERT OR REPLACE INTO algorithm_routines
                (routine_id, game_type, routine_name, algorithm_sequence, switch_conditions,
                 success_rate, games_tested, levels_completed, avg_actions_per_level,
                 last_used, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            params = (
                routine.routine_id,
                routine.game_type,
                routine.routine_name,
                json.dumps(algorithm_sequence),
                json.dumps(switch_conditions),
                routine.success_rate,
                routine.games_tested,
                routine.levels_completed,
                routine.avg_actions_per_level,
                routine.last_used.isoformat() if routine.last_used else None,
                routine.created_at.isoformat()
            )

            self.db.execute_query(query, params)
            logger.info(f"Saved routine {routine.routine_id} for game type {routine.game_type}")
            return True

        except Exception as e:
            logger.error(f"Error saving routine {routine.routine_id}: {e}")
            return False

    def start_routine(self, game_id: str, routine: AlgorithmRoutine) -> Dict[str, Any]:
        """Start executing a routine for a game."""
        game_type = self.extract_game_type(game_id)

        routine_state = {
            'routine': routine,
            'current_step': 0,
            'actions_in_current_step': 0,
            'step_start_score': 0,
            'consecutive_failures': 0,
            'total_actions': 0,
            'levels_completed': 0,
            'game_start_time': datetime.now(),
            # Level-based switching state
            'actions_since_last_score_increase': 0,
            'score_plateau_counter': 0,
            'last_level_score': 0.0,
            'last_score': 0.0,
            'algorithm_switches': 0,
            'score_history': []
        }

        self.current_routine_state[game_id] = routine_state
        self.active_routines[game_id] = routine

        logger.info(f"Started routine {routine.routine_id} for game {game_id}")
        return routine_state

    def get_current_algorithm(self, game_id: str) -> Optional[str]:
        """Get the current algorithm ID for a game."""
        if game_id not in self.current_routine_state:
            return None

        state = self.current_routine_state[game_id]
        routine = state['routine']

        if state['current_step'] >= len(routine.steps):
            # Routine completed, stay on last algorithm
            return routine.steps[-1].algorithm_id

        return routine.steps[state['current_step']].algorithm_id

    def should_switch_algorithm(self, game_id: str, current_score: float,
                              actions_taken: int) -> Tuple[bool, str]:
        """Check if we should switch to the next algorithm in the routine."""
        if game_id not in self.current_routine_state:
            return False, "No active routine"

        state = self.current_routine_state[game_id]
        routine = state['routine']

        # Update level-based tracking state
        self._update_level_tracking_state(state, current_score)

        if state['current_step'] >= len(routine.steps):
            return False, "Routine completed"

        current_step = routine.steps[state['current_step']]

        # Check switch conditions
        for condition in current_step.switch_conditions or []:
            should_switch = self._evaluate_switch_condition(
                condition, state, current_score, actions_taken
            )

            if should_switch:
                reason = f"Switch condition met: {condition.condition_type} {condition.operator} {condition.threshold}"
                return True, reason

        # Check max actions for current step
        if state['actions_in_current_step'] >= current_step.max_actions:
            return True, f"Max actions reached for step ({current_step.max_actions})"

        return False, "No switch conditions met"

    def _evaluate_switch_condition(self, condition: SwitchCondition, state: Dict,
                                 current_score: float, actions_taken: int) -> bool:
        """Evaluate a single switch condition."""
        if condition.condition_type == "action_count":
            value = state['actions_in_current_step']
        elif condition.condition_type == "score_threshold":
            value = current_score
        elif condition.condition_type == "performance_drop":
            # Check if score hasn't improved in recent actions
            score_improvement = current_score - state['step_start_score']
            value = score_improvement
            # For performance drop, we want to switch if improvement is below threshold
            if condition.operator == "greater_than":
                return score_improvement < condition.threshold
        elif condition.condition_type == "level_stagnation":
            # Switch if no level advancement after X actions
            actions_since_score_increase = state.get('actions_since_last_score_increase', 0)
            return actions_since_score_increase > condition.threshold
        elif condition.condition_type == "score_plateau":
            # Switch if score hasn't changed for X actions
            score_plateau_actions = state.get('score_plateau_counter', 0)
            return score_plateau_actions > condition.threshold
        elif condition.condition_type == "level_completion":
            # Switch when significant score increase detected (level completed)
            score_increase = current_score - state.get('last_level_score', 0.0)
            return score_increase >= condition.threshold
        elif condition.condition_type == "efficiency_drop":
            # Switch when actions per score point becomes inefficient
            if state['actions_in_current_step'] > 0:
                score_gain = current_score - state['step_start_score']
                if score_gain > 0:
                    actions_per_point = state['actions_in_current_step'] / score_gain
                    return actions_per_point > condition.threshold
                else:
                    # No score gain - consider inefficient after threshold actions
                    return state['actions_in_current_step'] > condition.threshold
            return False
        else:
            return False

        if condition.operator == "greater_than":
            return value > condition.threshold
        elif condition.operator == "less_than":
            return value < condition.threshold
        elif condition.operator == "equal_to":
            return abs(value - condition.threshold) < 0.001

        return False

    def _update_level_tracking_state(self, state: Dict, current_score: float) -> None:
        """Update level-based tracking state variables."""
        # Update score history
        state['score_history'].append(current_score)
        if len(state['score_history']) > 100:  # Keep only last 100 scores
            state['score_history'] = state['score_history'][-100:]

        # Check for score increases (level progress)
        if current_score > state['last_score']:
            # Score increased - reset stagnation counters
            state['actions_since_last_score_increase'] = 0
            state['score_plateau_counter'] = 0
            state['last_level_score'] = state['last_score']  # Mark previous score as level completion

            # Update coordinate success tracking
            self._update_coordinate_success_tracking(state, current_score - state['last_score'])
        else:
            # No score increase - increment counters
            state['actions_since_last_score_increase'] += 1
            state['score_plateau_counter'] += 1

        # Update last score
        state['last_score'] = current_score

    def _update_coordinate_success_tracking(self, state: Dict, score_improvement: float) -> None:
        """Update coordinate success tracking for the routine."""
        # Initialize coordinate tracking if not present
        if 'coordinate_success_history' not in state:
            state['coordinate_success_history'] = []
            state['last_action6_coordinates'] = None
            state['coordinate_success_rate'] = 0.0
            state['total_action6_attempts'] = 0
            state['successful_action6_attempts'] = 0

        # If we have recent ACTION6 coordinates and score improved, mark as successful
        if state['last_action6_coordinates'] and score_improvement > 0:
            state['coordinate_success_history'].append({
                'coordinates': state['last_action6_coordinates'],
                'score_improvement': score_improvement,
                'algorithm_id': state.get('current_algorithm_id', 'unknown')
            })
            state['successful_action6_attempts'] += 1

            # Limit history size
            if len(state['coordinate_success_history']) > 50:
                state['coordinate_success_history'] = state['coordinate_success_history'][-50:]

            # Update global coordinate generator with success
            if hasattr(self, '_coordinate_generator'):
                from coordinate_strategies import coordinate_generator
                coordinate_generator.update_success(
                    state.get('current_algorithm_id', 'routine'),
                    state['last_action6_coordinates'],
                    score_improvement
                )

        # Update success rate
        if state['total_action6_attempts'] > 0:
            state['coordinate_success_rate'] = state['successful_action6_attempts'] / state['total_action6_attempts']

    def switch_to_next_algorithm(self, game_id: str) -> Optional[str]:
        """Switch to the next algorithm in the routine."""
        if game_id not in self.current_routine_state:
            return None

        state = self.current_routine_state[game_id]
        routine = state['routine']

        # Move to next step
        state['current_step'] += 1
        state['actions_in_current_step'] = 0
        state['consecutive_failures'] = 0
        state['algorithm_switches'] += 1

        # Reset step-specific tracking
        state['step_start_score'] = state['last_score']

        if state['current_step'] >= len(routine.steps):
            logger.info(f"Routine {routine.routine_id} completed for game {game_id}")
            return routine.steps[-1].algorithm_id  # Stay on last algorithm

        next_algorithm = routine.steps[state['current_step']].algorithm_id
        logger.info(f"Switched to algorithm {next_algorithm} (step {state['current_step']}) "
                   f"for game {game_id}")

        return next_algorithm

    def update_routine_performance(self, game_id: str, final_score: float,
                                 actions_taken: int, levels_completed: int,
                                 win_detected: bool) -> None:
        """Update routine performance after game completion."""
        if game_id not in self.active_routines:
            return

        routine = self.active_routines[game_id]

        # Calculate performance metrics
        routine.games_tested += 1
        routine.levels_completed += levels_completed

        # Update success rate (wins + partial completions)
        success_score = 1.0 if win_detected else min(levels_completed / 10.0, 0.8)
        routine.success_rate = (
            (routine.success_rate * (routine.games_tested - 1) + success_score)
            / routine.games_tested
        )

        # Update average actions per level
        if levels_completed > 0:
            actions_per_level = actions_taken / levels_completed
            if routine.games_tested == 1:
                routine.avg_actions_per_level = actions_per_level
            else:
                routine.avg_actions_per_level = (
                    (routine.avg_actions_per_level * (routine.games_tested - 1) + actions_per_level)
                    / routine.games_tested
                )

        routine.last_used = datetime.now()

        # Save updated routine
        self.save_routine(routine)

        # Update game type performance tracking
        self._update_game_type_performance(routine, final_score, actions_taken,
                                         levels_completed, win_detected)

        logger.info(f"Updated routine {routine.routine_id} performance: "
                   f"success_rate={routine.success_rate:.2f}, "
                   f"avg_actions={routine.avg_actions_per_level:.1f}")

        # Clean up
        if game_id in self.current_routine_state:
            del self.current_routine_state[game_id]
        if game_id in self.active_routines:
            del self.active_routines[game_id]

    def _update_game_type_performance(self, routine: AlgorithmRoutine, final_score: float,
                                    actions_taken: int, levels_completed: int,
                                    win_detected: bool) -> None:
        """Update game type performance tracking in database."""
        try:
            success_rate = 1.0 if win_detected else min(levels_completed / 10.0, 0.8)
            actions_per_level = actions_taken / max(levels_completed, 1)

            query = """
                INSERT INTO game_type_performance
                (game_type, routine_id, levels_completed, total_actions,
                 avg_actions_per_level, success_rate, games_played)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """

            params = (
                routine.game_type,
                routine.routine_id,
                levels_completed,
                actions_taken,
                actions_per_level,
                success_rate
            )

            self.db.execute_query(query, params)

        except Exception as e:
            logger.error(f"Error updating game type performance: {e}")

    def get_routine_recommendations(self, game_type: str,
                                  available_algorithms: List[str]) -> List[AlgorithmRoutine]:
        """Get recommended routines for a game type."""
        recommendations = []

        # Get existing best routine
        best_routine = self.get_best_routine_for_game_type(game_type)
        if best_routine:
            recommendations.append(best_routine)

        # Create new routine variations
        if len(available_algorithms) >= 2:
            # High-exploration routine (try diverse algorithms)
            exploration_routine = self.create_default_routine(
                f"{game_type}_exploration",
                available_algorithms[:4]
            )
            recommendations.append(exploration_routine)

            # Fast-action routine (shorter timeouts)
            if len(available_algorithms) >= 2:
                fast_routine = self.create_default_routine(
                    f"{game_type}_fast",
                    available_algorithms[:2]
                )
                # Reduce max actions per step
                for step in fast_routine.steps:
                    step.max_actions = 10
                recommendations.append(fast_routine)

        return recommendations[:3]  # Limit to 3 recommendations

    def get_system_status(self) -> Dict[str, Any]:
        """Get routine manager system status."""
        try:
            # Count routines by game type
            query = """
                SELECT game_type, COUNT(*) as routine_count,
                       AVG(success_rate) as avg_success_rate,
                       SUM(games_tested) as total_games
                FROM algorithm_routines
                GROUP BY game_type
                ORDER BY avg_success_rate DESC
            """

            results = self.db.execute_query(query)
            game_type_stats = [
                {
                    'game_type': row[0],
                    'routine_count': row[1],
                    'avg_success_rate': row[2],
                    'total_games': row[3]
                }
                for row in results
            ]

            return {
                'active_routines': len(self.active_routines),
                'cached_game_types': len(self.game_type_cache),
                'game_type_stats': game_type_stats,
                'current_routine_states': len(self.current_routine_state)
            }

        except Exception as e:
            logger.error(f"Error getting routine manager status: {e}")
            return {
                'active_routines': len(self.active_routines),
                'cached_game_types': len(self.game_type_cache),
                'error': str(e)
            }

    def create_level_based_routine(self, game_type: str, available_algorithms: List[str],
                                 aggressive_switching: bool = True) -> AlgorithmRoutine:
        """Create a routine optimized for level-based algorithm switching.

        Args:
            game_type: The game type to create routine for
            available_algorithms: List of algorithm IDs to use
            aggressive_switching: If True, use more aggressive switching conditions

        Returns:
            AlgorithmRoutine with level-based switching configured
        """
        routine_id = f"{game_type}_level_based_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Define switching conditions based on aggressiveness
        if aggressive_switching:
            # Aggressive switching - change algorithms frequently
            switch_conditions = [
                # Switch if no score improvement in 100 actions
                SwitchCondition("level_stagnation", 100, "greater_than"),
                # Switch if score plateau for 75 actions
                SwitchCondition("score_plateau", 75, "greater_than"),
                # Switch when level completed (score increase >= 1.0)
                SwitchCondition("level_completion", 1.0, "greater_than"),
                # Switch if efficiency drops (>150 actions per score point)
                SwitchCondition("efficiency_drop", 150, "greater_than"),
                # Max 200 actions per algorithm
                SwitchCondition("action_count", 200, "greater_than")
            ]
            max_actions_per_step = 200
        else:
            # Conservative switching - give algorithms more time
            switch_conditions = [
                # Switch if no score improvement in 200 actions
                SwitchCondition("level_stagnation", 200, "greater_than"),
                # Switch if score plateau for 150 actions
                SwitchCondition("score_plateau", 150, "greater_than"),
                # Switch when level completed (score increase >= 1.0)
                SwitchCondition("level_completion", 1.0, "greater_than"),
                # Switch if efficiency drops (>300 actions per score point)
                SwitchCondition("efficiency_drop", 300, "greater_than"),
                # Max 400 actions per algorithm
                SwitchCondition("action_count", 400, "greater_than")
            ]
            max_actions_per_step = 400

        # Create routine steps for each algorithm
        steps = []
        for i, algorithm_id in enumerate(available_algorithms):
            step = RoutineStep(
                algorithm_id=algorithm_id,
                max_actions=max_actions_per_step,
                switch_conditions=switch_conditions.copy(),
                priority=len(available_algorithms) - i  # Higher priority for earlier algorithms
            )
            steps.append(step)

        # Create the routine
        routine = AlgorithmRoutine(
            routine_id=routine_id,
            game_type=game_type,
            routine_name=f"Level-Based {'Aggressive' if aggressive_switching else 'Conservative'} Routine",
            steps=steps,
            success_rate=0.0,
            games_tested=0,
            levels_completed=0,
            avg_actions_per_level=0.0
        )

        logger.info(f"Created level-based routine {routine_id} with {len(steps)} algorithms")
        return routine

    def track_action6_usage(self, game_id: str, coordinates: tuple, algorithm_id: str = None) -> None:
        """Track ACTION6 coordinate usage for success rate analysis.

        Args:
            game_id: Game identifier
            coordinates: (x, y) coordinates used
            algorithm_id: ID of algorithm that generated the coordinates
        """
        if game_id not in self.current_routine_state:
            return

        state = self.current_routine_state[game_id]

        # Initialize coordinate tracking if needed
        if 'coordinate_success_history' not in state:
            state['coordinate_success_history'] = []
            state['last_action6_coordinates'] = None
            state['coordinate_success_rate'] = 0.0
            state['total_action6_attempts'] = 0
            state['successful_action6_attempts'] = 0

        # Track the coordinates and algorithm
        state['last_action6_coordinates'] = coordinates
        state['current_algorithm_id'] = algorithm_id
        state['total_action6_attempts'] += 1

        logger.debug(f"Tracked ACTION6({coordinates[0]}, {coordinates[1]}) for {algorithm_id}")

    def get_coordinate_statistics(self, game_id: str = None) -> Dict[str, Any]:
        """Get coordinate usage statistics.

        Args:
            game_id: Specific game ID, or None for all games

        Returns:
            Dictionary containing coordinate statistics
        """
        if game_id and game_id in self.current_routine_state:
            # Single game statistics
            state = self.current_routine_state[game_id]
            return {
                'game_id': game_id,
                'total_action6_attempts': state.get('total_action6_attempts', 0),
                'successful_action6_attempts': state.get('successful_action6_attempts', 0),
                'coordinate_success_rate': state.get('coordinate_success_rate', 0.0),
                'successful_coordinates': [
                    entry['coordinates'] for entry in state.get('coordinate_success_history', [])
                ]
            }
        else:
            # Aggregate statistics across all active games
            total_attempts = 0
            total_successes = 0
            all_successful_coords = []

            for state in self.current_routine_state.values():
                total_attempts += state.get('total_action6_attempts', 0)
                total_successes += state.get('successful_action6_attempts', 0)
                all_successful_coords.extend([
                    entry['coordinates'] for entry in state.get('coordinate_success_history', [])
                ])

            overall_success_rate = total_successes / total_attempts if total_attempts > 0 else 0.0

            return {
                'total_games': len(self.current_routine_state),
                'total_action6_attempts': total_attempts,
                'successful_action6_attempts': total_successes,
                'overall_coordinate_success_rate': overall_success_rate,
                'unique_successful_coordinates': len(set(all_successful_coords)),
                'coordinate_coverage': len(set(all_successful_coords)) / (65 * 65) if all_successful_coords else 0.0
            }