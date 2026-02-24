import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
Fitness Calculator - RLVR Evolutionary Fitness Scoring
======================================================

Calculates evolutionary fitness from real ARC game results.
This is the CORE of post-game processing that drives evolution.

Key Responsibilities:
- Extract ARC-native rewards from game results
- Calculate derived metrics (efficiency, consistency, etc.)
- Generate evolutionary feedback signals for agent selection
- Track path efficiency (fewer actions to win = better)

Fitness Components:
1. Win Achievement (100 points) - Did agent win the game?
2. Score Progress (1x) - How close to win_score?
3. Score Efficiency (10x) - Score per action taken
4. Level Progression (20 points each) - Detecting/completing levels
5. Consistency Bonus (5x) - Reliable performance over time
6. Exploration Bonus (2x) - Strategy diversity
7. Path Efficiency (15x) - Fewer actions to success

Following Rules:
- Rule 2: Database-only storage
- Rule 6: Real games only (no simulation)
- Rule 7: Verify real actions sent to ARC games
"""

import json
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from engines.engine_logger import get_engine_logger

logger = get_engine_logger("fitness_calculator")
from dataclasses import dataclass

if TYPE_CHECKING:
    from database_interface import DatabaseInterface


@dataclass
class FitnessConfig:
    """Configurable weights for fitness calculation."""
    win_achievement: float = 100.0      # Winning is most important
    score_progress: float = 1.0         # Points toward win_score
    score_efficiency: float = 10.0      # Score per action taken
    level_progression: float = 20.0     # Per level completed
    consistency_bonus: float = 5.0      # Consistent performance
    exploration_bonus: float = 2.0      # Strategy diversity
    path_efficiency: float = 15.0       # Efficient win paths

    # Tuning parameters
    typical_game_length: int = 500      # For normalizing path efficiency
    consistency_history_size: int = 10  # Games to consider for consistency


@dataclass
class FitnessResult:
    """Result of fitness calculation."""
    total_reward: float
    breakdown: Dict[str, float]
    fitness_signals: Dict[str, float]
    arc_rewards: Dict[str, Any]
    derived_metrics: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_reward': self.total_reward,
            'breakdown': self.breakdown,
            'fitness_signals': self.fitness_signals,
            'arc_rewards': self.arc_rewards,
            'derived_metrics': self.derived_metrics,
        }


class FitnessCalculator:
    """
    Calculates evolutionary fitness from ARC game performance.

    This is the "evolutionary nervous system" - it converts real game
    results into signals that drive agent selection and reproduction.
    """

    def __init__(
        self,
        db: 'DatabaseInterface',
        config: Optional[FitnessConfig] = None
    ):
        self.db = db
        self.config = config or FitnessConfig()
        self._calculator_id = f"fitness_{uuid.uuid4().hex[:8]}"

    def calculate_fitness(
        self,
        agent_id: str,
        game_results: Dict[str, Any]
    ) -> FitnessResult:
        """
        Calculate complete fitness from game results.

        Args:
            agent_id: The agent that played
            game_results: Results from actual ARC game (Rule 6)

        Returns:
            FitnessResult with total reward and breakdown
        """
        # 1. Extract raw ARC rewards
        arc_rewards = self._extract_arc_native_rewards(game_results)

        # 2. Calculate derived metrics
        derived_metrics = self._calculate_derived_metrics(arc_rewards, agent_id)

        # 3. Generate evolutionary feedback
        feedback = self._generate_evolutionary_feedback(arc_rewards, derived_metrics)

        # Fix 3.1: Add genre-specific fitness bonus
        genre_bonus = self._calculate_genre_bonus(arc_rewards, game_results)
        feedback['total_reward'] += genre_bonus
        feedback['reward_breakdown']['genre_bonus'] = genre_bonus

        result = FitnessResult(
            total_reward=feedback['total_reward'],
            breakdown=feedback['reward_breakdown'],
            fitness_signals=feedback['fitness_signals'],
            arc_rewards=arc_rewards,
            derived_metrics=derived_metrics,
        )

        # Store in database (Rule 2)
        self._store_fitness_data(agent_id, game_results, result)

        return result

    def _extract_arc_native_rewards(
        self,
        game_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract ARC-native rewards from real game results.
        These are verifiable rewards directly from ARC API.
        """
        return {
            # Primary ARC rewards
            'game_win': game_results.get('win_detected', False),
            'final_score': game_results.get('final_score', 0.0),
            'win_score_threshold': game_results.get('win_score', 0.0),
            'total_actions': game_results.get('total_actions', 0),
            'level_progressions': game_results.get('level_completions', 0),

            # Game state information
            'frame_changes': game_results.get('frame_changes', 0),
            'coordinate_attempts': game_results.get('coordinate_attempts', 0),
            'coordinate_successes': game_results.get('coordinate_successes', 0),
            'game_duration_seconds': game_results.get('duration_seconds', 0.0),

            # Action effectiveness from real API responses
            'actions_taken': game_results.get('actions_taken', []),
            'score_progression': game_results.get('score_history', []),
        }

    def _calculate_derived_metrics(
        self,
        arc_rewards: Dict[str, Any],
        agent_id: str
    ) -> Dict[str, Any]:
        """Calculate derived metrics from ARC-native rewards."""
        final_score = arc_rewards['final_score']
        win_score = arc_rewards['win_score_threshold']
        total_actions = max(arc_rewards['total_actions'], 1)

        # Core efficiency metrics
        score_efficiency = final_score / total_actions
        win_proximity = final_score / max(win_score, 1.0)

        # Coordinate success rate
        coord_attempts = arc_rewards['coordinate_attempts']
        coord_successes = arc_rewards['coordinate_successes']
        coordinate_success_rate = (
            coord_successes / coord_attempts if coord_attempts > 0 else 0.0
        )

        # Score progression analysis
        score_progression = arc_rewards.get('score_progression', [])
        score_improvement_rate = 0.0
        if len(score_progression) > 1:
            start_score = score_progression[0]
            end_score = score_progression[-1]
            score_improvement_rate = (end_score - start_score) / len(score_progression)

        # Consistency from historical data
        consistency_score = self._calculate_agent_consistency(agent_id)

        # Path efficiency (for wins)
        path_efficiency = 0.0
        if arc_rewards['game_win'] and total_actions > 0:
            path_efficiency = min(1.0, 100.0 / total_actions)

        return {
            'score_efficiency': score_efficiency,
            'win_proximity': win_proximity,
            'coordinate_success_rate': coordinate_success_rate,
            'score_improvement_rate': score_improvement_rate,
            'consistency_score': consistency_score,
            'level_progression_rate': arc_rewards['level_progressions'] / total_actions,
            'action_effectiveness': self._calculate_action_effectiveness(arc_rewards),
            'path_efficiency': path_efficiency,
        }

    def _generate_evolutionary_feedback(
        self,
        arc_rewards: Dict[str, Any],
        derived_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate evolutionary feedback signals from ARC performance."""
        cfg = self.config

        # Base reward from actual score
        base_reward = arc_rewards['final_score']

        # Win bonus (most important)
        win_bonus = cfg.win_achievement if arc_rewards['game_win'] else 0.0

        # Score efficiency bonus
        efficiency_bonus = derived_metrics['score_efficiency'] * cfg.score_efficiency

        # Win proximity bonus
        proximity_bonus = derived_metrics['win_proximity'] * cfg.score_progress

        # Level progression bonus
        level_bonus = arc_rewards['level_progressions'] * cfg.level_progression

        # Consistency bonus
        consistency_bonus = derived_metrics['consistency_score'] * cfg.consistency_bonus

        # Exploration bonus
        exploration_bonus = (
            self._calculate_exploration_bonus(arc_rewards) * cfg.exploration_bonus
        )

        # Path efficiency bonus
        path_efficiency_bonus = 0.0
        if arc_rewards['game_win'] and arc_rewards['total_actions'] > 0:
            efficiency_ratio = cfg.typical_game_length / arc_rewards['total_actions']
            path_efficiency_bonus = min(efficiency_ratio, 2.0) * cfg.path_efficiency

        total_reward = (
            base_reward +
            win_bonus +
            efficiency_bonus +
            proximity_bonus +
            level_bonus +
            consistency_bonus +
            exploration_bonus +
            path_efficiency_bonus
        )

        return {
            'total_reward': total_reward,
            'reward_breakdown': {
                'base_reward': base_reward,
                'win_bonus': win_bonus,
                'efficiency_bonus': efficiency_bonus,
                'proximity_bonus': proximity_bonus,
                'level_bonus': level_bonus,
                'consistency_bonus': consistency_bonus,
                'exploration_bonus': exploration_bonus,
                'path_efficiency_bonus': path_efficiency_bonus,
            },
            'fitness_signals': {
                'primary_fitness': win_bonus + proximity_bonus,
                'efficiency_fitness': efficiency_bonus,
                'exploration_fitness': exploration_bonus,
                'consistency_fitness': consistency_bonus,
            }
        }

    def _calculate_agent_consistency(self, agent_id: str) -> float:
        """Calculate consistency from historical performance."""
        if not agent_id:
            return 0.0

        try:
            recent = self.db.get_agent_recent_performance(
                agent_id,
                limit=self.config.consistency_history_size
            )
        except Exception:
            return 0.0

        if len(recent) < 3:
            return 0.0

        scores = [p['final_score'] for p in recent]
        win_rates = [1.0 if p.get('win_achieved') else 0.0 for p in recent]

        score_variance = self._variance(scores)
        win_rate_variance = self._variance(win_rates)

        score_consistency = max(0.0, 1.0 - (score_variance / 100.0))
        win_rate_consistency = max(0.0, 1.0 - win_rate_variance)

        return (score_consistency + win_rate_consistency) / 2.0

    def _calculate_action_effectiveness(self, arc_rewards: Dict[str, Any]) -> float:
        """Calculate effectiveness of actions taken."""
        actions = arc_rewards.get('actions_taken', [])
        if not actions:
            return 0.0

        effective = sum(1 for a in actions if a.get('score_change', 0) > 0)
        return effective / len(actions)

    def _calculate_genre_bonus(self, arc_rewards: Dict[str, Any], game_results: Dict[str, Any]) -> float:
        """Fix 3.1: Genre-specific fitness bonus.

        Different game genres measure progress on different axes:
        - LS20 (movement): capability axis — spatial exploration
        - FT09 (constraint): knowledge axis — constraint satisfaction progress
        - VC33 (alignment): knowledge axis — spatial alignment progress

        For click-based games with 0 scores, frame_changes and coordinate
        diversity provide a gradient signal that pure score cannot.
        """
        game_id = game_results.get('game_id', '')
        game_type = game_id[:4] if len(game_id) >= 4 else game_id

        if game_type in ('FT09', 'VC33'):
            # Knowledge-axis games: reward click diversity and frame responsiveness
            frame_changes = arc_rewards.get('frame_changes', 0)
            total_actions = max(arc_rewards.get('total_actions', 1), 1)
            coord_attempts = arc_rewards.get('coordinate_attempts', 0)
            coord_successes = arc_rewards.get('coordinate_successes', 0)

            # Click responsiveness: what fraction of clicks caused a frame change?
            responsiveness = coord_successes / max(coord_attempts, 1)

            # Frame activity: normalised frame changes per action
            activity = min(frame_changes / total_actions, 1.0)

            # Genre bonus: weighted average of responsiveness and activity
            return (responsiveness * 0.6 + activity * 0.4) * 10.0
        else:
            # Capability-axis (LS20): use standard exploration bonus
            return 0.0

    def _calculate_exploration_bonus(self, arc_rewards: Dict[str, Any]) -> float:
        """Calculate bonus for strategy diversity."""
        actions = arc_rewards.get('actions_taken', [])
        if not actions:
            return 0.0

        action_types = set()
        coordinate_diversity = set()

        for action in actions:
            action_types.add(action.get('action_number', 0))
            if action.get('action_number') == 6:
                coords = action.get('coordinates', {})
                if coords:
                    coordinate_diversity.add((coords.get('x', 0), coords.get('y', 0)))

        type_diversity = len(action_types) / 6.0
        coord_diversity = min(len(coordinate_diversity) / 20.0, 1.0)

        return (type_diversity + coord_diversity) / 2.0

    def _variance(self, values: List[float]) -> float:
        """Calculate variance of values."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)

    def _store_fitness_data(
        self,
        agent_id: str,
        game_results: Dict[str, Any],
        result: FitnessResult
    ) -> None:
        """Store fitness data in database (Rule 2)."""
        try:
            reward_data = {
                'agent_id': agent_id,
                'game_id': game_results.get('game_id'),
                'session_id': game_results.get('session_id'),
                'arc_native_rewards': result.arc_rewards,
                'derived_metrics': result.derived_metrics,
                'evolutionary_feedback': {
                    'total_reward': result.total_reward,
                    'breakdown': result.breakdown,
                    'fitness_signals': result.fitness_signals,
                },
                'total_evolutionary_reward': result.total_reward,
                'processing_timestamp': datetime.now().isoformat(),
            }
            self.db.store_arc_reward_data(agent_id, reward_data)
        except Exception as e:
            # Log but don't fail - fitness calculation succeeded
            logger.warning("Failed to store fitness data", exc=e)

    # =========================================================================
    # Population-Level Methods (for Evolution)
    # =========================================================================

    def calculate_population_fitness_summary(
        self,
        generation: int
    ) -> Dict[str, Any]:
        """
        Calculate fitness summary for entire population.
        Used by evolutionary_engine for selection decisions.
        """
        try:
            agents = self.db.get_agents_by_generation(generation)
        except Exception:
            agents = []

        if not agents:
            return {
                'generation': generation,
                'population_size': 0,
                'fitness_stats': {},
            }

        fitness_scores = []
        win_rates = []
        efficiencies = []

        for agent in agents:
            try:
                perf = self.db.get_agent_arc_performance(agent['agent_id'])
                if perf:
                    fitness_scores.append(perf.get('total_evolutionary_reward', 0.0))
                    win_rates.append(perf.get('win_rate', 0.0))
                    efficiencies.append(perf.get('score_efficiency', 0.0))
            except Exception:
                continue

        fitness_stats = {
            'mean_fitness': sum(fitness_scores) / max(len(fitness_scores), 1),
            'max_fitness': max(fitness_scores) if fitness_scores else 0.0,
            'min_fitness': min(fitness_scores) if fitness_scores else 0.0,
            'fitness_variance': self._variance(fitness_scores),
            'mean_win_rate': sum(win_rates) / max(len(win_rates), 1),
            'mean_score_efficiency': sum(efficiencies) / max(len(efficiencies), 1),
        }

        summary = {
            'generation': generation,
            'population_size': len(agents),
            'fitness_stats': fitness_stats,
            'calculated_at': datetime.now().isoformat(),
        }

        try:
            self.db.store_population_fitness_summary(summary)
        except Exception:
            pass

        return summary

    def validate_reward_calculation(
        self,
        agent_id: str,
        game_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate that reward calculations are correct (Rule 7)."""
        arc_rewards = self._extract_arc_native_rewards(game_results)
        derived_metrics = self._calculate_derived_metrics(arc_rewards, agent_id)
        feedback = self._generate_evolutionary_feedback(arc_rewards, derived_metrics)

        validation = {
            'agent_id': agent_id,
            'validation_timestamp': datetime.now().isoformat(),
            'checks': {
                'arc_data_present': arc_rewards['final_score'] is not None,
                'win_detection_valid': isinstance(arc_rewards['game_win'], bool),
                'score_positive': arc_rewards['final_score'] >= 0,
                'actions_valid': arc_rewards['total_actions'] > 0,
                'reward_calculation_valid': feedback['total_reward'] >= 0,
                'coordinate_range_valid': self._validate_coordinates(arc_rewards),
            },
            'calculated_reward': feedback['total_reward'],
        }

        validation['validation_passed'] = all(validation['checks'].values())

        try:
            self.db.store_reward_validation(validation)
        except Exception:
            pass

        return validation

    def _validate_coordinates(self, arc_rewards: Dict[str, Any]) -> bool:
        """Validate ACTION6 coordinates are in valid range (0-63)."""
        for action in arc_rewards.get('actions_taken', []):
            if action.get('action_number') == 6:
                coords = action.get('coordinates', {})
                x, y = coords.get('x', -1), coords.get('y', -1)
                if not (0 <= x <= 63 and 0 <= y <= 63):
                    return False
        return True
