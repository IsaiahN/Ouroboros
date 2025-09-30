"""
Multi-Armed Bandit Module

Implements real-time algorithm selection using multi-armed bandit approaches including:
- Upper Confidence Bound (UCB) selection
- Thompson Sampling
- Epsilon-greedy strategies
- Real-time reward tracking and arm updates
- Exploration-exploitation balance optimization
"""

import math
import random
import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

from algorithm_representations import AlgorithmRepresentation

logger = logging.getLogger(__name__)


@dataclass
class BanditArm:
    """Represents a single arm in the multi-armed bandit."""
    arm_id: str
    algorithm_id: str
    total_pulls: int = 0
    total_reward: float = 0.0
    avg_reward: float = 0.0
    confidence_interval: float = 1.0
    last_pulled: Optional[datetime] = None
    created_at: Optional[datetime] = None
    # Thompson Sampling parameters
    alpha: float = 1.0  # Successes + 1
    beta: float = 1.0   # Failures + 1

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class MABConfig:
    """Configuration for multi-armed bandit operations."""
    selection_strategy: str = "ucb"  # "ucb", "thompson", "epsilon_greedy"
    epsilon: float = 0.1  # For epsilon-greedy
    ucb_confidence: float = 2.0  # UCB confidence parameter
    decay_factor: float = 0.99  # Reward decay over time
    min_pulls_per_arm: int = 3  # Minimum pulls before exploitation
    exploration_bonus: float = 0.1  # Bonus for unexplored arms
    reward_normalization: bool = True  # Normalize rewards to [0,1]


class MultiArmedBandit:
    """Main class for multi-armed bandit algorithm selection."""

    def __init__(self, config: MABConfig = None, database_interface=None):
        self.config = config or MABConfig()
        self.db = database_interface
        self.arms: Dict[str, BanditArm] = {}
        self.total_pulls = 0
        self.selection_history = []
        self.reward_stats = {"min": 0.0, "max": 100.0, "mean": 50.0, "std": 25.0}

    def add_algorithm(self, algorithm: AlgorithmRepresentation) -> str:
        """Add an algorithm as a new bandit arm.

        Args:
            algorithm: Algorithm to add as an arm

        Returns:
            Arm ID for the new arm
        """
        arm_id = f"arm_{algorithm.algorithm_id}"

        # Check if arm already exists
        if arm_id in self.arms:
            logger.info(f"Arm {arm_id} already exists, updating algorithm reference")
            return arm_id

        # Create new arm
        arm = BanditArm(
            arm_id=arm_id,
            algorithm_id=algorithm.algorithm_id
        )

        self.arms[arm_id] = arm

        # Save to database if available
        if self.db:
            try:
                self.db.save_mab_arm(arm_id, algorithm.algorithm_id)
                logger.info(f"Added new bandit arm: {arm_id}")
            except Exception as e:
                logger.error(f"Failed to save arm to database: {e}")

        return arm_id

    def select_algorithm(self, available_algorithms: List[AlgorithmRepresentation],
                        context: Dict[str, Any] = None) -> Optional[AlgorithmRepresentation]:
        """Select an algorithm using the configured bandit strategy.

        Args:
            available_algorithms: List of algorithms to choose from
            context: Optional context for selection (game state, etc.)

        Returns:
            Selected algorithm or None if no algorithms available
        """
        if not available_algorithms:
            return None

        # Ensure all algorithms have arms
        for algorithm in available_algorithms:
            self.add_algorithm(algorithm)

        # Get available arms
        available_arm_ids = [f"arm_{alg.algorithm_id}" for alg in available_algorithms]
        available_arms = [self.arms[arm_id] for arm_id in available_arm_ids
                         if arm_id in self.arms]

        if not available_arms:
            logger.warning("No available arms for selection")
            return random.choice(available_algorithms)

        # Select arm based on strategy
        selected_arm = self._select_arm(available_arms, context)

        if not selected_arm:
            return random.choice(available_algorithms)

        # Find corresponding algorithm
        selected_algorithm = None
        for algorithm in available_algorithms:
            if algorithm.algorithm_id == selected_arm.algorithm_id:
                selected_algorithm = algorithm
                break

        # Update selection history
        self.selection_history.append({
            "timestamp": datetime.now(),
            "arm_id": selected_arm.arm_id,
            "algorithm_id": selected_arm.algorithm_id,
            "strategy": self.config.selection_strategy,
            "context": context
        })

        self.total_pulls += 1
        logger.info(f"Selected algorithm {selected_arm.algorithm_id} using {self.config.selection_strategy}")

        return selected_algorithm

    def _select_arm(self, available_arms: List[BanditArm],
                   context: Dict[str, Any] = None) -> Optional[BanditArm]:
        """Select an arm using the configured strategy."""
        if not available_arms:
            return None

        if self.config.selection_strategy == "ucb":
            return self._ucb_selection(available_arms)
        elif self.config.selection_strategy == "thompson":
            return self._thompson_sampling(available_arms)
        elif self.config.selection_strategy == "epsilon_greedy":
            return self._epsilon_greedy_selection(available_arms)
        else:
            logger.warning(f"Unknown selection strategy: {self.config.selection_strategy}")
            return random.choice(available_arms)

    def _ucb_selection(self, available_arms: List[BanditArm]) -> BanditArm:
        """Upper Confidence Bound selection."""
        if self.total_pulls == 0:
            return random.choice(available_arms)

        best_arm = None
        best_ucb_value = float('-inf')

        for arm in available_arms:
            if arm.total_pulls == 0:
                # Always try arms that haven't been pulled
                return arm

            # Calculate UCB value
            confidence_bonus = self.config.ucb_confidence * math.sqrt(
                math.log(self.total_pulls) / arm.total_pulls
            )

            ucb_value = arm.avg_reward + confidence_bonus

            # Add exploration bonus for underexplored arms
            if arm.total_pulls < self.config.min_pulls_per_arm:
                ucb_value += self.config.exploration_bonus

            if ucb_value > best_ucb_value:
                best_ucb_value = ucb_value
                best_arm = arm

        return best_arm or random.choice(available_arms)

    def _thompson_sampling(self, available_arms: List[BanditArm]) -> BanditArm:
        """Thompson Sampling selection using Beta distributions."""
        best_arm = None
        best_sample = float('-inf')

        for arm in available_arms:
            # Sample from Beta distribution
            if arm.total_pulls == 0:
                # Prior: Beta(1, 1) = Uniform(0, 1)
                sample = random.betavariate(1, 1)
            else:
                # Update Beta parameters based on performance
                normalized_reward = self._normalize_reward(arm.avg_reward)
                # Convert to success/failure counts
                successes = max(1, normalized_reward * arm.total_pulls)
                failures = max(1, (1 - normalized_reward) * arm.total_pulls)

                sample = random.betavariate(successes + 1, failures + 1)

            if sample > best_sample:
                best_sample = sample
                best_arm = arm

        return best_arm or random.choice(available_arms)

    def _epsilon_greedy_selection(self, available_arms: List[BanditArm]) -> BanditArm:
        """Epsilon-greedy selection."""
        # Exploration
        if random.random() < self.config.epsilon:
            return random.choice(available_arms)

        # Exploitation - choose arm with highest average reward
        best_arm = None
        best_reward = float('-inf')

        for arm in available_arms:
            if arm.total_pulls == 0:
                # Give untried arms a chance
                adjusted_reward = self.config.exploration_bonus
            else:
                adjusted_reward = arm.avg_reward

            if adjusted_reward > best_reward:
                best_reward = adjusted_reward
                best_arm = arm

        return best_arm or random.choice(available_arms)

    def update_reward(self, algorithm_id: str, reward: float,
                     context: Dict[str, Any] = None):
        """Update the reward for an algorithm.

        Args:
            algorithm_id: ID of the algorithm that was used
            reward: Reward value received
            context: Optional context about the reward
        """
        arm_id = f"arm_{algorithm_id}"

        if arm_id not in self.arms:
            logger.warning(f"Arm {arm_id} not found for reward update")
            return

        arm = self.arms[arm_id]

        # Apply decay to previous rewards if configured
        if self.config.decay_factor < 1.0 and arm.total_pulls > 0:
            arm.total_reward *= self.config.decay_factor

        # Update arm statistics
        arm.total_pulls += 1
        arm.total_reward += reward
        arm.avg_reward = arm.total_reward / arm.total_pulls
        arm.last_pulled = datetime.now()

        # Update confidence interval for UCB
        if self.total_pulls > 0:
            arm.confidence_interval = self.config.ucb_confidence * math.sqrt(
                math.log(self.total_pulls) / max(1, arm.total_pulls)
            )

        # Update reward statistics for normalization
        self._update_reward_stats(reward)

        # Save to database if available
        if self.db:
            try:
                self.db.update_mab_arm(arm_id, reward)
            except Exception as e:
                logger.error(f"Failed to update arm in database: {e}")

        logger.debug(f"Updated arm {arm_id}: pulls={arm.total_pulls}, "
                    f"avg_reward={arm.avg_reward:.3f}, reward={reward}")

    def _normalize_reward(self, reward: float) -> float:
        """Normalize reward to [0, 1] range."""
        if not self.config.reward_normalization:
            return reward

        min_reward = self.reward_stats["min"]
        max_reward = self.reward_stats["max"]

        if max_reward <= min_reward:
            return 0.5  # Default if no range

        return (reward - min_reward) / (max_reward - min_reward)

    def _update_reward_stats(self, reward: float):
        """Update running statistics for reward normalization."""
        self.reward_stats["min"] = min(self.reward_stats["min"], reward)
        self.reward_stats["max"] = max(self.reward_stats["max"], reward)

        # Simple running average update
        alpha = 0.1  # Learning rate
        self.reward_stats["mean"] = (
            alpha * reward + (1 - alpha) * self.reward_stats["mean"]
        )

    def get_arm_statistics(self) -> Dict[str, Any]:
        """Get statistics for all arms."""
        stats = {
            "total_arms": len(self.arms),
            "total_pulls": self.total_pulls,
            "strategy": self.config.selection_strategy,
            "arms": {}
        }

        for arm_id, arm in self.arms.items():
            stats["arms"][arm_id] = {
                "algorithm_id": arm.algorithm_id,
                "total_pulls": arm.total_pulls,
                "avg_reward": arm.avg_reward,
                "confidence_interval": arm.confidence_interval,
                "last_pulled": arm.last_pulled.isoformat() if arm.last_pulled else None,
                "pull_rate": arm.total_pulls / max(1, self.total_pulls)
            }

        return stats

    def get_best_algorithms(self, count: int = 5) -> List[str]:
        """Get the algorithm IDs of the best performing arms.

        Args:
            count: Number of algorithms to return

        Returns:
            List of algorithm IDs sorted by performance
        """
        # Sort arms by average reward
        sorted_arms = sorted(self.arms.values(),
                           key=lambda x: x.avg_reward if x.total_pulls > 0 else 0,
                           reverse=True)

        return [arm.algorithm_id for arm in sorted_arms[:count]]

    def reset_arm(self, algorithm_id: str):
        """Reset statistics for a specific arm.

        Args:
            algorithm_id: ID of algorithm whose arm to reset
        """
        arm_id = f"arm_{algorithm_id}"

        if arm_id in self.arms:
            arm = self.arms[arm_id]
            arm.total_pulls = 0
            arm.total_reward = 0.0
            arm.avg_reward = 0.0
            arm.confidence_interval = 1.0
            arm.last_pulled = None

            logger.info(f"Reset arm {arm_id}")

    def remove_algorithm(self, algorithm_id: str):
        """Remove an algorithm from the bandit.

        Args:
            algorithm_id: ID of algorithm to remove
        """
        arm_id = f"arm_{algorithm_id}"

        if arm_id in self.arms:
            del self.arms[arm_id]
            logger.info(f"Removed arm {arm_id}")

    def load_from_database(self):
        """Load arm data from database."""
        if not self.db:
            logger.warning("No database interface available")
            return

        try:
            arms_data = self.db.get_mab_arms()

            for arm_data in arms_data:
                arm = BanditArm(
                    arm_id=arm_data['arm_id'],
                    algorithm_id=arm_data['algorithm_id'],
                    total_pulls=arm_data['total_pulls'],
                    total_reward=arm_data['total_reward'],
                    avg_reward=arm_data['avg_reward'],
                    confidence_interval=arm_data['confidence_interval']
                )

                if arm_data['last_pulled']:
                    arm.last_pulled = datetime.fromisoformat(arm_data['last_pulled'])

                self.arms[arm.arm_id] = arm

            self.total_pulls = sum(arm.total_pulls for arm in self.arms.values())

            logger.info(f"Loaded {len(self.arms)} arms from database")

        except Exception as e:
            logger.error(f"Failed to load arms from database: {e}")

    def get_selection_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get summary of recent selections.

        Args:
            days: Number of days to look back

        Returns:
            Selection summary dictionary
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_selections = [
            s for s in self.selection_history
            if s["timestamp"] >= cutoff_date
        ]

        if not recent_selections:
            return {"message": "No recent selections found"}

        # Calculate selection frequencies
        algorithm_counts = {}
        for selection in recent_selections:
            alg_id = selection["algorithm_id"]
            algorithm_counts[alg_id] = algorithm_counts.get(alg_id, 0) + 1

        total_selections = len(recent_selections)

        return {
            "total_selections": total_selections,
            "unique_algorithms": len(algorithm_counts),
            "selection_distribution": {
                alg_id: {
                    "count": count,
                    "percentage": (count / total_selections) * 100
                }
                for alg_id, count in algorithm_counts.items()
            },
            "most_selected": max(algorithm_counts.items(), key=lambda x: x[1])[0] if algorithm_counts else None,
            "strategy_used": self.config.selection_strategy,
            "exploration_rate": self.config.epsilon if self.config.selection_strategy == "epsilon_greedy" else "N/A"
        }

    def optimize_parameters(self, recent_rewards: List[float]):
        """Automatically optimize bandit parameters based on recent performance.

        Args:
            recent_rewards: List of recent reward values
        """
        if len(recent_rewards) < 10:
            return  # Need sufficient data

        reward_variance = np.var(recent_rewards)
        reward_mean = np.mean(recent_rewards)

        # Adjust epsilon for epsilon-greedy based on performance variance
        if self.config.selection_strategy == "epsilon_greedy":
            if reward_variance > reward_mean * 0.5:
                # High variance - increase exploration
                self.config.epsilon = min(0.3, self.config.epsilon * 1.1)
            else:
                # Low variance - decrease exploration
                self.config.epsilon = max(0.05, self.config.epsilon * 0.95)

        # Adjust UCB confidence based on reward distribution
        elif self.config.selection_strategy == "ucb":
            if reward_variance > reward_mean * 0.3:
                # High variance - increase confidence
                self.config.ucb_confidence = min(3.0, self.config.ucb_confidence * 1.05)
            else:
                # Low variance - decrease confidence
                self.config.ucb_confidence = max(1.0, self.config.ucb_confidence * 0.98)

        logger.info(f"Optimized parameters: epsilon={self.config.epsilon:.3f}, "
                   f"ucb_confidence={self.config.ucb_confidence:.3f}")