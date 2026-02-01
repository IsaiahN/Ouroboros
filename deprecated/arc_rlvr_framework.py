import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
DEPRECATED: Use engines.postgame module instead
==============================================

This file is kept for backwards compatibility only.
All post-game processing has been consolidated in:
    - engines/postgame/fitness_calculator.py - RLVR fitness calculation
    - engines/postgame/lessons_extractor.py - Learning from outcomes
    - engines/postgame/orchestrator.py - Coordinates all post-game processing

New code should use:
    from engines.postgame import PostGameProcessor, FitnessCalculator

Existing imports will continue to work but are deprecated:
    from arc_rlvr_framework import ARCRLVRFramework  # DEPRECATED

Original docstring:
ARC RLVR Framework - Reasoning, Learning, Validation, Revision
Uses ARC-native rewards for evolutionary feedback
Processes real ARC game results into evolutionary fitness signals
Following Rule 2: Database-only storage, Rule 6: Real games only
"""

import warnings
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from database_interface import DatabaseInterface

# Issue deprecation warning on import
warnings.warn(
    "arc_rlvr_framework is deprecated. Use 'from engines.postgame import FitnessCalculator' instead.",
    DeprecationWarning,
    stacklevel=2
)


class ARCRLVRFramework:
    """
    Reasoning, Learning, Validation, Revision using ARC-native rewards
    Processes ARC game performance into evolutionary feedback signals
    """

    def __init__(self, database_interface: DatabaseInterface):
        self.db = database_interface
        self.framework_id = f"rlvr_{uuid.uuid4().hex[:8]}"

        # ARC-native reward weights (based on what matters for ARC success)
        self.reward_weights = {
            'win_achievement': 100.0,      # Winning a game is most important
            'score_progress': 1.0,         # Points toward win_score
            'score_efficiency': 10.0,      # Score per action taken
            'level_progression': 20.0,     # Detecting and completing levels
            'consistency_bonus': 5.0,      # Consistent performance across games
            'exploration_bonus': 2.0,      # Trying different strategies
            'path_efficiency': 15.0        # NEW: Reward efficient win paths (fewer actions to success)
        }

    def process_arc_rewards(self, agent_id: str, game_session_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process ARC game results into evolutionary feedback
        Rule 6: Only processes real ARC game data, never simulated
        """
        self._log_rlvr_event("processing_arc_rewards", {
            "agent_id": agent_id,
            "game_id": game_session_results.get('game_id'),
            "session_id": game_session_results.get('session_id')
        })

        try:
            # Extract ARC-native rewards from real game results
            arc_rewards = self._extract_arc_native_rewards(game_session_results)

            # Calculate derived evolutionary metrics
            derived_metrics = self._calculate_derived_metrics(arc_rewards)

            # Generate evolutionary feedback signals
            evolutionary_feedback = self._generate_evolutionary_feedback(
                arc_rewards, derived_metrics
            )

            # Store comprehensive reward data in database (Rule 2)
            reward_data = {
                'agent_id': agent_id,
                'game_id': game_session_results.get('game_id'),
                'session_id': game_session_results.get('session_id'),
                'arc_native_rewards': arc_rewards,
                'derived_metrics': derived_metrics,
                'evolutionary_feedback': evolutionary_feedback,
                'total_evolutionary_reward': evolutionary_feedback['total_reward'],
                'processing_timestamp': datetime.now().isoformat()
            }

            self.db.store_arc_reward_data(agent_id, reward_data)

            self._log_rlvr_event("arc_rewards_processed", {
                "agent_id": agent_id,
                "total_reward": evolutionary_feedback['total_reward'],
                "win_achieved": arc_rewards['game_win']
            })

            return reward_data

        except Exception as e:
            self._log_rlvr_event("arc_reward_processing_error", {
                "agent_id": agent_id,
                "error": str(e)
            })
            raise

    def _extract_arc_native_rewards(self, game_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract ARC-native rewards from real game results
        These are the verifiable rewards that come directly from ARC API
        """
        return {
            # Primary ARC rewards (directly from ARC system)
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
            'score_progression': game_results.get('score_history', [])
        }

    def _calculate_derived_metrics(self, arc_rewards: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate derived metrics from ARC-native rewards
        These provide additional insights for evolutionary decisions
        """
        final_score = arc_rewards['final_score']
        win_score = arc_rewards['win_score_threshold']
        total_actions = max(arc_rewards['total_actions'], 1)  # Avoid division by zero

        # Core efficiency metrics
        score_efficiency = final_score / total_actions
        win_proximity = final_score / max(win_score, 1.0)  # How close to winning

        # Action effectiveness metrics
        coordinate_success_rate = 0.0
        if arc_rewards['coordinate_attempts'] > 0:
            coordinate_success_rate = arc_rewards['coordinate_successes'] / arc_rewards['coordinate_attempts']

        # Score progression analysis
        score_progression = arc_rewards.get('score_progression', [])
        score_improvement_rate = 0.0
        if len(score_progression) > 1:
            start_score = score_progression[0]
            end_score = score_progression[-1]
            score_improvement_rate = (end_score - start_score) / len(score_progression)

        # Consistency metrics (for agents with game history)
        agent_id = arc_rewards.get('agent_id', '')
        consistency_score = self._calculate_agent_consistency(agent_id) if agent_id else 0.0

        # NEW: Path efficiency (for wins, how efficient was the path?)
        path_efficiency = 0.0
        if arc_rewards['game_win'] and total_actions > 0:
            # Lower actions to win = higher efficiency
            # Normalize: 1.0 at 100 actions, 0.5 at 500 actions, 0.1 at 1000+ actions
            path_efficiency = min(1.0, 100.0 / total_actions)

        return {
            'score_efficiency': score_efficiency,
            'win_proximity': win_proximity,
            'coordinate_success_rate': coordinate_success_rate,
            'score_improvement_rate': score_improvement_rate,
            'consistency_score': consistency_score,
            'level_progression_rate': arc_rewards['level_progressions'] / max(total_actions, 1),
            'action_effectiveness': self._calculate_action_effectiveness(arc_rewards),
            'path_efficiency': path_efficiency  # NEW: Track efficient win paths
        }

    def _generate_evolutionary_feedback(self, arc_rewards: Dict[str, Any],
                                      derived_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate evolutionary feedback signals from ARC performance
        This is what drives agent evolution based on real ARC success
        """
        # Base reward from actual ARC score
        base_reward = arc_rewards['final_score']

        # Win bonus (most important reward signal)
        win_bonus = 0.0
        if arc_rewards['game_win']:
            win_bonus = self.reward_weights['win_achievement']

        # Score efficiency bonus
        efficiency_bonus = derived_metrics['score_efficiency'] * self.reward_weights['score_efficiency']

        # Win proximity bonus (getting closer to winning)
        proximity_bonus = derived_metrics['win_proximity'] * self.reward_weights['score_progress']

        # Level progression bonus
        level_bonus = arc_rewards['level_progressions'] * self.reward_weights['level_progression']

        # Consistency bonus (for reliable agents)
        consistency_bonus = derived_metrics['consistency_score'] * self.reward_weights['consistency_bonus']

        # Exploration bonus (for trying different strategies)
        exploration_bonus = self._calculate_exploration_bonus(arc_rewards) * self.reward_weights['exploration_bonus']

        # NEW: Path efficiency bonus (reward winning in fewer actions)
        path_efficiency_bonus = 0.0
        if arc_rewards['game_win'] and arc_rewards['total_actions'] > 0:
            # Calculate efficiency: inverse of actions taken (fewer actions = higher reward)
            # Normalize by typical game length (e.g., 500 actions)
            typical_game_length = 500
            efficiency_ratio = typical_game_length / arc_rewards['total_actions']
            # Cap at 2x bonus (if win in 250 actions or less)
            path_efficiency_bonus = min(efficiency_ratio, 2.0) * self.reward_weights['path_efficiency']

        # Calculate total evolutionary reward
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
                'path_efficiency_bonus': path_efficiency_bonus  # NEW
            },
            'fitness_signals': {
                'primary_fitness': win_bonus + proximity_bonus,  # Winning focus
                'efficiency_fitness': efficiency_bonus,         # Score per action
                'exploration_fitness': exploration_bonus,       # Strategy diversity
                'consistency_fitness': consistency_bonus        # Reliability
            }
        }

    def _calculate_agent_consistency(self, agent_id: str) -> float:
        """
        Calculate agent consistency score based on historical performance
        Higher consistency = more reliable agent for evolution
        """
        if not agent_id:
            return 0.0

        # Get agent's recent performance history from database
        recent_performance = self.db.get_agent_recent_performance(agent_id, limit=10)

        if len(recent_performance) < 3:
            return 0.0  # Not enough data for consistency calculation

        # Calculate variance in win rates and scores
        scores = [perf['final_score'] for perf in recent_performance]
        win_rates = [1.0 if perf['win_achieved'] else 0.0 for perf in recent_performance]

        # Lower variance = higher consistency
        score_variance = self._calculate_variance(scores)
        win_rate_variance = self._calculate_variance(win_rates)

        # Convert variance to consistency score (0-1, higher is better)
        score_consistency = max(0.0, 1.0 - (score_variance / 100.0))  # Normalize by expected score range
        win_rate_consistency = max(0.0, 1.0 - win_rate_variance)

        # Combined consistency score
        consistency_score = (score_consistency + win_rate_consistency) / 2.0

        return consistency_score

    def _calculate_action_effectiveness(self, arc_rewards: Dict[str, Any]) -> float:
        """
        Calculate effectiveness of actions taken during game
        Based on score improvements per action
        """
        actions_taken = arc_rewards.get('actions_taken', [])
        if not actions_taken:
            return 0.0

        effective_actions = 0
        total_actions = len(actions_taken)

        for action in actions_taken:
            score_change = action.get('score_change', 0.0)
            if score_change > 0:
                effective_actions += 1

        return effective_actions / max(total_actions, 1)

    def _calculate_exploration_bonus(self, arc_rewards: Dict[str, Any]) -> float:
        """
        Calculate bonus for exploration and strategy diversity
        Rewards agents that try different approaches
        """
        actions_taken = arc_rewards.get('actions_taken', [])
        if not actions_taken:
            return 0.0

        # Count unique action types used
        action_types = set()
        coordinate_diversity = set()

        for action in actions_taken:
            action_types.add(action.get('action_number', 0))

            # For ACTION6, track coordinate diversity
            if action.get('action_number') == 6:
                coords = action.get('coordinates', {})
                if coords:
                    coordinate_diversity.add((coords.get('x', 0), coords.get('y', 0)))

        # Diversity bonuses
        action_type_diversity = len(action_types) / 6.0  # Max 6 action types in ARC
        coordinate_diversity_score = min(len(coordinate_diversity) / 20.0, 1.0)  # Cap at 20 unique coordinates

        return (action_type_diversity + coordinate_diversity_score) / 2.0

    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of a list of values"""
        if len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance

    def calculate_population_fitness_summary(self, generation: int) -> Dict[str, Any]:
        """
        Calculate fitness summary for entire population
        Used by Claude Code for evolution strategy decisions
        """
        # Get all agents in current generation
        generation_agents = self.db.get_agents_by_generation(generation)

        if not generation_agents:
            return {
                'generation': generation,
                'population_size': 0,
                'fitness_stats': {},
                'reward_distribution': {}
            }

        # Calculate fitness statistics
        fitness_scores = []
        win_rates = []
        score_efficiencies = []

        for agent in generation_agents:
            agent_performance = self.db.get_agent_arc_performance(agent['agent_id'])
            if agent_performance:
                fitness_scores.append(agent_performance.get('total_evolutionary_reward', 0.0))
                win_rates.append(agent_performance.get('win_rate', 0.0))
                score_efficiencies.append(agent_performance.get('score_efficiency', 0.0))

        fitness_stats = {
            'mean_fitness': sum(fitness_scores) / max(len(fitness_scores), 1),
            'max_fitness': max(fitness_scores) if fitness_scores else 0.0,
            'min_fitness': min(fitness_scores) if fitness_scores else 0.0,
            'fitness_variance': self._calculate_variance(fitness_scores),
            'mean_win_rate': sum(win_rates) / max(len(win_rates), 1),
            'mean_score_efficiency': sum(score_efficiencies) / max(len(score_efficiencies), 1)
        }

        # Store population fitness summary in database
        summary_data = {
            'generation': generation,
            'population_size': len(generation_agents),
            'fitness_stats': fitness_stats,
            'calculated_at': datetime.now().isoformat()
        }

        self.db.store_population_fitness_summary(summary_data)

        return summary_data

    def validate_reward_calculation(self, agent_id: str, game_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that reward calculations are correct and verifiable
        Rule 2: Store validation results in database for auditing
        """
        # Recalculate rewards
        arc_rewards = self._extract_arc_native_rewards(game_results)
        derived_metrics = self._calculate_derived_metrics(arc_rewards)
        evolutionary_feedback = self._generate_evolutionary_feedback(arc_rewards, derived_metrics)

        # Validation checks
        validation_results = {
            'agent_id': agent_id,
            'validation_timestamp': datetime.now().isoformat(),
            'checks': {
                'arc_data_present': bool(arc_rewards['final_score'] is not None),
                'win_detection_valid': isinstance(arc_rewards['game_win'], bool),
                'score_positive': arc_rewards['final_score'] >= 0,
                'actions_valid': arc_rewards['total_actions'] > 0,
                'reward_calculation_valid': evolutionary_feedback['total_reward'] >= 0,
                'coordinate_range_valid': self._validate_coordinate_ranges(arc_rewards)
            },
            'calculated_reward': evolutionary_feedback['total_reward'],
            'validation_passed': True
        }

        # Overall validation status
        validation_results['validation_passed'] = all(validation_results['checks'].values())

        # Store validation results in database
        self.db.store_reward_validation(validation_results)

        return validation_results

    def _validate_coordinate_ranges(self, arc_rewards: Dict[str, Any]) -> bool:
        """
        Validate that all ACTION6 coordinates are in valid range (0-63)
        Rule 7: Verify real actions sent to ARC games
        """
        actions_taken = arc_rewards.get('actions_taken', [])

        for action in actions_taken:
            if action.get('action_number') == 6:
                coords = action.get('coordinates', {})
                x, y = coords.get('x', -1), coords.get('y', -1)
                if not (0 <= x <= 63 and 0 <= y <= 63):
                    return False

        return True

    def _log_rlvr_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log RLVR events to database (Rule 2: no log files)"""
        self.db.store_rlvr_log({
            'event_type': event_type,
            'event_data': json.dumps(event_data),
            'framework_id': self.framework_id,
            'timestamp': datetime.now().isoformat()
        })

# [CHECKPOINT 4 COMPLETED: ARC RLVR FRAMEWORK IMPLEMENTATION]
# Next: Implement Performance Analyzer and Agent Factory