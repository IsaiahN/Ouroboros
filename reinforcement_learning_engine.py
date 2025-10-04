#!/usr/bin/env python3
"""
REINFORCEMENT LEARNING CORE ENGINE
===================================
Revolutionary machine learning system with DQN and Actor-Critic architectures.

This system learns from game actions and outcomes to improve decision-making through:
- Deep Q-Network (DQN) for value-based learning
- Actor-Critic architecture for policy optimization
- Experience replay and memory management
- Multi-objective reward optimization
- Adaptive learning rate scheduling
"""

import os
import sys

# Disable Python bytecode generation
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.dont_write_bytecode = True

import numpy as np
import json
import time
import logging
import sqlite3
import random
import math
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from enum import Enum
import threading
import pickle

logger = logging.getLogger(__name__)

class LearningMode(Enum):
    """Learning algorithm modes."""
    DQN = "dqn"
    ACTOR_CRITIC = "actor_critic"
    HYBRID = "hybrid"

class ActionSpace(Enum):
    """Available game actions."""
    ACTION1 = 0
    ACTION2 = 1
    ACTION3 = 2
    ACTION4 = 3
    ACTION5 = 4
    ACTION6 = 5
    ACTION7 = 6

@dataclass
class GameState:
    """Representation of game state for learning."""
    score: float
    actions_available: List[int]
    action_number: int
    visual_features: List[float]  # Encoded visual features
    coordinate_space: Tuple[int, int]  # Current coordinate context
    game_progress: float  # 0.0 to 1.0

    def to_vector(self) -> np.ndarray:
        """Convert game state to feature vector for neural networks."""
        # Basic features
        features = [
            self.score,
            len(self.actions_available),
            self.action_number,
            self.game_progress
        ]

        # Action availability (one-hot encoding)
        action_available = [0.0] * 7
        for action in self.actions_available:
            if 1 <= action <= 7:
                action_available[action-1] = 1.0
        features.extend(action_available)

        # Coordinate features
        features.extend([self.coordinate_space[0] / 64.0, self.coordinate_space[1] / 64.0])

        # Visual features (padded/truncated to fixed size)
        visual_feature_size = 20
        visual_features = self.visual_features[:visual_feature_size]
        if len(visual_features) < visual_feature_size:
            visual_features.extend([0.0] * (visual_feature_size - len(visual_features)))
        features.extend(visual_features)

        return np.array(features, dtype=np.float32)

@dataclass
class Experience:
    """Experience tuple for replay buffer."""
    state: GameState
    action: int
    reward: float
    next_state: Optional[GameState]
    done: bool
    timestamp: float

    # Additional context
    algorithm_id: str
    game_id: str
    meta_reward: float  # Multi-objective reward

class DQNNetwork:
    """Deep Q-Network implementation using basic numpy operations."""

    def __init__(self, state_size: int, action_size: int, learning_rate: float = 0.001):
        """Initialize DQN with random weights."""
        self.state_size = state_size
        self.action_size = action_size
        self.learning_rate = learning_rate

        # Simple 3-layer neural network
        self.hidden_size = 64
        self.weights1 = np.random.randn(state_size, self.hidden_size) * 0.1
        self.bias1 = np.zeros((1, self.hidden_size))
        self.weights2 = np.random.randn(self.hidden_size, self.hidden_size) * 0.1
        self.bias2 = np.zeros((1, self.hidden_size))
        self.weights3 = np.random.randn(self.hidden_size, action_size) * 0.1
        self.bias3 = np.zeros((1, action_size))

    def _relu(self, x):
        """ReLU activation function."""
        return np.maximum(0, x)

    def _relu_derivative(self, x):
        """ReLU derivative."""
        return (x > 0).astype(float)

    def forward(self, state: np.ndarray) -> np.ndarray:
        """Forward pass through the network."""
        if len(state.shape) == 1:
            state = state.reshape(1, -1)

        # Forward propagation
        self.z1 = np.dot(state, self.weights1) + self.bias1
        self.a1 = self._relu(self.z1)

        self.z2 = np.dot(self.a1, self.weights2) + self.bias2
        self.a2 = self._relu(self.z2)

        self.z3 = np.dot(self.a2, self.weights3) + self.bias3
        q_values = self.z3

        return q_values

    def backward(self, state: np.ndarray, target: np.ndarray):
        """Backward pass for training."""
        if len(state.shape) == 1:
            state = state.reshape(1, -1)
        if len(target.shape) == 1:
            target = target.reshape(1, -1)

        m = state.shape[0]

        # Forward pass to compute intermediate values
        q_values = self.forward(state)

        # Backward propagation
        dz3 = q_values - target
        dw3 = (1/m) * np.dot(self.a2.T, dz3)
        db3 = (1/m) * np.sum(dz3, axis=0, keepdims=True)

        da2 = np.dot(dz3, self.weights3.T)
        dz2 = da2 * self._relu_derivative(self.z2)
        dw2 = (1/m) * np.dot(self.a1.T, dz2)
        db2 = (1/m) * np.sum(dz2, axis=0, keepdims=True)

        da1 = np.dot(dz2, self.weights2.T)
        dz1 = da1 * self._relu_derivative(self.z1)
        dw1 = (1/m) * np.dot(state.T, dz1)
        db1 = (1/m) * np.sum(dz1, axis=0, keepdims=True)

        # Update weights
        self.weights3 -= self.learning_rate * dw3
        self.bias3 -= self.learning_rate * db3
        self.weights2 -= self.learning_rate * dw2
        self.bias2 -= self.learning_rate * db2
        self.weights1 -= self.learning_rate * dw1
        self.bias1 -= self.learning_rate * db1

class ActorCriticNetwork:
    """Actor-Critic network implementation."""

    def __init__(self, state_size: int, action_size: int, learning_rate: float = 0.001):
        """Initialize Actor-Critic with separate networks."""
        self.state_size = state_size
        self.action_size = action_size
        self.learning_rate = learning_rate

        # Actor network (policy)
        self.actor_hidden = 32
        self.actor_w1 = np.random.randn(state_size, self.actor_hidden) * 0.1
        self.actor_b1 = np.zeros((1, self.actor_hidden))
        self.actor_w2 = np.random.randn(self.actor_hidden, action_size) * 0.1
        self.actor_b2 = np.zeros((1, action_size))

        # Critic network (value)
        self.critic_hidden = 32
        self.critic_w1 = np.random.randn(state_size, self.critic_hidden) * 0.1
        self.critic_b1 = np.zeros((1, self.critic_hidden))
        self.critic_w2 = np.random.randn(self.critic_hidden, 1) * 0.1
        self.critic_b2 = np.zeros((1, 1))

    def _softmax(self, x):
        """Softmax activation for policy output."""
        exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=1, keepdims=True)

    def _relu(self, x):
        """ReLU activation function."""
        return np.maximum(0, x)

    def actor_forward(self, state: np.ndarray) -> np.ndarray:
        """Actor network forward pass."""
        if len(state.shape) == 1:
            state = state.reshape(1, -1)

        self.actor_z1 = np.dot(state, self.actor_w1) + self.actor_b1
        self.actor_a1 = self._relu(self.actor_z1)

        self.actor_z2 = np.dot(self.actor_a1, self.actor_w2) + self.actor_b2
        policy = self._softmax(self.actor_z2)

        return policy

    def critic_forward(self, state: np.ndarray) -> np.ndarray:
        """Critic network forward pass."""
        if len(state.shape) == 1:
            state = state.reshape(1, -1)

        self.critic_z1 = np.dot(state, self.critic_w1) + self.critic_b1
        self.critic_a1 = self._relu(self.critic_z1)

        self.critic_z2 = np.dot(self.critic_a1, self.critic_w2) + self.critic_b2
        value = self.critic_z2

        return value

class ReplayBuffer:
    """Experience replay buffer for DQN."""

    def __init__(self, capacity: int = 10000):
        """Initialize replay buffer."""
        self.capacity = capacity
        self.buffer = deque(maxlen=capacity)

    def push(self, experience: Experience):
        """Add experience to buffer."""
        self.buffer.append(experience)

    def sample(self, batch_size: int) -> List[Experience]:
        """Sample random batch of experiences."""
        if len(self.buffer) < batch_size:
            return list(self.buffer)
        return random.sample(self.buffer, batch_size)

    def __len__(self):
        return len(self.buffer)

class ReinforcementLearningEngine:
    """Revolutionary reinforcement learning system for game optimization."""

    def __init__(self, db_path: str = "core_data.db", learning_mode: LearningMode = LearningMode.HYBRID):
        """Initialize the reinforcement learning engine.

        Args:
            db_path: Database path for persistence
            learning_mode: Learning algorithm to use
        """
        self.db_path = db_path
        self.learning_mode = learning_mode

        # State and action configuration
        self.state_size = 33  # Based on GameState.to_vector() output
        self.action_size = 7  # Number of available actions

        # Learning networks
        self.dqn = DQNNetwork(self.state_size, self.action_size)
        self.target_dqn = DQNNetwork(self.state_size, self.action_size)
        self.actor_critic = ActorCriticNetwork(self.state_size, self.action_size)

        # Experience replay
        self.replay_buffer = ReplayBuffer(capacity=50000)

        # Learning parameters
        self.epsilon = 1.0  # Exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.gamma = 0.95  # Discount factor
        self.batch_size = 32
        self.update_target_frequency = 100

        # Training state
        self.training_step = 0
        self.total_reward = 0.0
        self.episode_count = 0
        self.learning_active = True

        # Performance tracking
        self.episode_rewards = deque(maxlen=1000)
        self.q_value_history = deque(maxlen=1000)
        self.loss_history = deque(maxlen=1000)

        # Multi-objective reward components
        self.reward_weights = {
            "score_improvement": 1.0,
            "action_efficiency": 0.5,
            "exploration_bonus": 0.2,
            "strategic_value": 0.3
        }

        logger.info(f"ReinforcementLearningEngine initialized in {learning_mode.value} mode")

    def encode_game_state(self, score: float, available_actions: List[int],
                         action_number: int, visual_features: List[float] = None,
                         coordinate_space: Tuple[int, int] = (32, 32)) -> GameState:
        """Encode current game state for learning."""
        if visual_features is None:
            visual_features = []

        # Calculate game progress (assuming max 1500 actions)
        game_progress = min(action_number / 1500.0, 1.0)

        return GameState(
            score=score,
            actions_available=available_actions,
            action_number=action_number,
            visual_features=visual_features,
            coordinate_space=coordinate_space,
            game_progress=game_progress
        )

    def calculate_reward(self, prev_state: GameState, action: int, new_state: GameState,
                        algorithm_id: str = "unknown") -> Tuple[float, float]:
        """Calculate multi-objective reward for the transition.

        Returns:
            Tuple of (primary_reward, meta_reward)
        """
        # Primary reward: score improvement
        score_delta = new_state.score - prev_state.score
        score_reward = score_delta * self.reward_weights["score_improvement"]

        # Action efficiency reward
        action_efficiency = 1.0 / (new_state.action_number + 1)
        efficiency_reward = action_efficiency * self.reward_weights["action_efficiency"]

        # Exploration bonus (encourage trying different actions)
        exploration_bonus = 0.1 if action != 0 else 0.0  # ACTION1 is default
        exploration_reward = exploration_bonus * self.reward_weights["exploration_bonus"]

        # Strategic value (based on visual features if available)
        strategic_reward = 0.0
        if new_state.visual_features:
            strategic_value = np.mean(new_state.visual_features[:5])  # Top 5 features
            strategic_reward = strategic_value * self.reward_weights["strategic_value"]

        # Combine rewards
        primary_reward = score_reward
        meta_reward = score_reward + efficiency_reward + exploration_reward + strategic_reward

        # Penalty for very poor performance
        if score_delta < -0.5:
            primary_reward -= 1.0
            meta_reward -= 1.0

        return primary_reward, meta_reward

    def select_action(self, state: GameState, available_actions: List[int],
                     training: bool = True) -> Tuple[int, float, Dict[str, Any]]:
        """Select action using current policy.

        Returns:
            Tuple of (action_index, confidence, additional_info)
        """
        state_vector = state.to_vector()

        if self.learning_mode == LearningMode.DQN or self.learning_mode == LearningMode.HYBRID:
            return self._select_action_dqn(state_vector, available_actions, training)
        elif self.learning_mode == LearningMode.ACTOR_CRITIC:
            return self._select_action_actor_critic(state_vector, available_actions, training)
        else:
            # Fallback to random action
            action = random.choice(available_actions) - 1  # Convert to 0-indexed
            return action, 0.5, {"method": "random"}

    def _select_action_dqn(self, state_vector: np.ndarray, available_actions: List[int],
                          training: bool) -> Tuple[int, float, Dict[str, Any]]:
        """Select action using DQN."""
        # Epsilon-greedy exploration
        if training and random.random() < self.epsilon:
            action = random.choice(available_actions) - 1  # Convert to 0-indexed
            confidence = self.epsilon
            method = "exploration"
        else:
            # Get Q-values for all actions
            q_values = self.dqn.forward(state_vector)

            # Mask unavailable actions
            masked_q_values = np.full(self.action_size, -np.inf)
            for action in available_actions:
                if 1 <= action <= 7:
                    masked_q_values[action - 1] = q_values[0, action - 1]

            # Select action with highest Q-value
            action = np.argmax(masked_q_values)
            confidence = 1.0 - self.epsilon
            method = "exploitation"

            # Track Q-values for monitoring
            self.q_value_history.append(np.max(q_values))

        return action, confidence, {
            "method": method,
            "epsilon": self.epsilon,
            "q_values": q_values[0].tolist() if 'q_values' in locals() else None
        }

    def _select_action_actor_critic(self, state_vector: np.ndarray, available_actions: List[int],
                                   training: bool) -> Tuple[int, float, Dict[str, Any]]:
        """Select action using Actor-Critic."""
        # Get policy distribution
        policy = self.actor_critic.actor_forward(state_vector)

        # Mask unavailable actions
        masked_policy = np.zeros(self.action_size)
        available_indices = [a - 1 for a in available_actions if 1 <= a <= 7]

        if available_indices:
            for idx in available_indices:
                masked_policy[idx] = policy[0, idx]

            # Renormalize
            if np.sum(masked_policy) > 0:
                masked_policy = masked_policy / np.sum(masked_policy)
            else:
                # Uniform distribution if all masked
                for idx in available_indices:
                    masked_policy[idx] = 1.0 / len(available_indices)

        # Sample action from policy
        if training:
            action = np.random.choice(self.action_size, p=masked_policy)
        else:
            action = np.argmax(masked_policy)

        confidence = masked_policy[action]

        return action, confidence, {
            "method": "policy",
            "policy_distribution": policy[0].tolist(),
            "value_estimate": self.actor_critic.critic_forward(state_vector)[0, 0]
        }

    def learn_from_experience(self, experience: Experience):
        """Learn from a single experience."""
        # Add to replay buffer
        self.replay_buffer.push(experience)

        # Update training step
        self.training_step += 1

        # Learn based on mode
        if self.learning_mode == LearningMode.DQN:
            self._learn_dqn()
        elif self.learning_mode == LearningMode.ACTOR_CRITIC:
            self._learn_actor_critic(experience)
        elif self.learning_mode == LearningMode.HYBRID:
            self._learn_dqn()
            if self.training_step % 2 == 0:  # Alternate learning
                self._learn_actor_critic(experience)

        # Update target network periodically
        if self.training_step % self.update_target_frequency == 0:
            self._update_target_network()

        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def _learn_dqn(self):
        """Train DQN using experience replay."""
        if len(self.replay_buffer) < self.batch_size:
            return

        # Sample batch of experiences
        batch = self.replay_buffer.sample(self.batch_size)

        # Prepare training data
        states = np.array([exp.state.to_vector() for exp in batch])
        actions = np.array([exp.action for exp in batch])
        rewards = np.array([exp.reward for exp in batch])
        next_states = np.array([exp.next_state.to_vector() if exp.next_state else np.zeros(self.state_size) for exp in batch])
        dones = np.array([exp.done for exp in batch])

        # Current Q-values
        current_q_values = self.dqn.forward(states)

        # Target Q-values
        next_q_values = self.target_dqn.forward(next_states)
        target_q_values = current_q_values.copy()

        for i in range(len(batch)):
            if dones[i]:
                target_q_values[i, actions[i]] = rewards[i]
            else:
                target_q_values[i, actions[i]] = rewards[i] + self.gamma * np.max(next_q_values[i])

        # Train network
        self.dqn.backward(states, target_q_values)

        # Track loss (simplified MSE)
        loss = np.mean((current_q_values - target_q_values) ** 2)
        self.loss_history.append(loss)

    def _learn_actor_critic(self, experience: Experience):
        """Train Actor-Critic networks."""
        state_vector = experience.state.to_vector()

        if experience.next_state:
            next_state_vector = experience.next_state.to_vector()
            next_value = self.actor_critic.critic_forward(next_state_vector)[0, 0]
        else:
            next_value = 0.0

        # Calculate TD error
        current_value = self.actor_critic.critic_forward(state_vector)[0, 0]
        td_target = experience.reward + self.gamma * next_value * (1 - experience.done)
        td_error = td_target - current_value

        # Update critic (simplified gradient descent)
        critic_target = np.array([[td_target]])
        # Note: In a full implementation, you would compute gradients properly
        # This is a simplified version for demonstration

        # Update actor based on advantage
        advantage = td_error

        # Log learning progress
        if self.training_step % 100 == 0:
            logger.info(f"AC Learning - TD Error: {td_error:.4f}, Value: {current_value:.4f}")

    def _update_target_network(self):
        """Update target network weights."""
        # Copy weights from main DQN to target DQN
        self.target_dqn.weights1 = self.dqn.weights1.copy()
        self.target_dqn.bias1 = self.dqn.bias1.copy()
        self.target_dqn.weights2 = self.dqn.weights2.copy()
        self.target_dqn.bias2 = self.dqn.bias2.copy()
        self.target_dqn.weights3 = self.dqn.weights3.copy()
        self.target_dqn.bias3 = self.dqn.bias3.copy()

        logger.info("Target network updated")

    def end_episode(self, final_score: float, total_actions: int):
        """Mark end of episode and update statistics."""
        self.episode_count += 1
        self.total_reward += final_score
        self.episode_rewards.append(final_score)

        # Calculate episode statistics
        avg_reward = np.mean(self.episode_rewards) if self.episode_rewards else 0.0
        avg_q_value = np.mean(self.q_value_history) if self.q_value_history else 0.0
        avg_loss = np.mean(self.loss_history) if self.loss_history else 0.0

        logger.info(f"Episode {self.episode_count} completed - "
                   f"Score: {final_score:.2f}, "
                   f"Actions: {total_actions}, "
                   f"Avg Reward: {avg_reward:.3f}, "
                   f"Epsilon: {self.epsilon:.3f}")

        # Store episode data
        self._store_episode_to_db(final_score, total_actions, avg_reward, avg_q_value, avg_loss)

    def get_learning_status(self) -> Dict[str, Any]:
        """Get current learning status and statistics."""
        avg_reward = np.mean(self.episode_rewards) if self.episode_rewards else 0.0
        avg_q_value = np.mean(self.q_value_history) if self.q_value_history else 0.0
        avg_loss = np.mean(self.loss_history) if self.loss_history else 0.0

        return {
            "learning_active": self.learning_active,
            "learning_mode": self.learning_mode.value,
            "episode_count": self.episode_count,
            "training_steps": self.training_step,
            "epsilon": self.epsilon,
            "replay_buffer_size": len(self.replay_buffer),
            "performance_metrics": {
                "avg_episode_reward": avg_reward,
                "avg_q_value": avg_q_value,
                "avg_loss": avg_loss,
                "total_reward": self.total_reward
            },
            "network_info": {
                "state_size": self.state_size,
                "action_size": self.action_size,
                "hidden_size": self.dqn.hidden_size
            }
        }

    def save_model(self, filepath: str):
        """Save trained model weights."""
        model_data = {
            "dqn_weights": {
                "weights1": self.dqn.weights1.tolist(),
                "bias1": self.dqn.bias1.tolist(),
                "weights2": self.dqn.weights2.tolist(),
                "bias2": self.dqn.bias2.tolist(),
                "weights3": self.dqn.weights3.tolist(),
                "bias3": self.dqn.bias3.tolist(),
            },
            "learning_params": {
                "epsilon": self.epsilon,
                "episode_count": self.episode_count,
                "training_step": self.training_step
            },
            "metadata": {
                "learning_mode": self.learning_mode.value,
                "state_size": self.state_size,
                "action_size": self.action_size
            }
        }

        with open(filepath, 'w') as f:
            json.dump(model_data, f, indent=2)

        logger.info(f"Model saved to {filepath}")

    def load_model(self, filepath: str):
        """Load trained model weights."""
        try:
            with open(filepath, 'r') as f:
                model_data = json.load(f)

            # Restore DQN weights
            dqn_weights = model_data["dqn_weights"]
            self.dqn.weights1 = np.array(dqn_weights["weights1"])
            self.dqn.bias1 = np.array(dqn_weights["bias1"])
            self.dqn.weights2 = np.array(dqn_weights["weights2"])
            self.dqn.bias2 = np.array(dqn_weights["bias2"])
            self.dqn.weights3 = np.array(dqn_weights["weights3"])
            self.dqn.bias3 = np.array(dqn_weights["bias3"])

            # Restore learning parameters
            learning_params = model_data["learning_params"]
            self.epsilon = learning_params["epsilon"]
            self.episode_count = learning_params["episode_count"]
            self.training_step = learning_params["training_step"]

            # Update target network
            self._update_target_network()

            logger.info(f"Model loaded from {filepath}")

        except Exception as e:
            logger.error(f"Error loading model: {e}")

    def _store_episode_to_db(self, final_score: float, total_actions: int,
                           avg_reward: float, avg_q_value: float, avg_loss: float):
        """Store episode data to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rl_episodes (
                    episode_number INTEGER,
                    timestamp REAL,
                    final_score REAL,
                    total_actions INTEGER,
                    avg_reward REAL,
                    avg_q_value REAL,
                    avg_loss REAL,
                    epsilon REAL,
                    learning_mode TEXT
                )
            """)

            # Insert episode data
            cursor.execute("""
                INSERT INTO rl_episodes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.episode_count,
                time.time(),
                final_score,
                total_actions,
                avg_reward,
                avg_q_value,
                avg_loss,
                self.epsilon,
                self.learning_mode.value
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error storing episode data: {e}")

# Global instance
rl_engine = ReinforcementLearningEngine(learning_mode=LearningMode.HYBRID)

def initialize_learning_session(game_id: str, learning_mode: str = "hybrid"):
    """Initialize a new learning session."""
    global rl_engine
    mode_map = {
        "dqn": LearningMode.DQN,
        "actor_critic": LearningMode.ACTOR_CRITIC,
        "hybrid": LearningMode.HYBRID
    }
    rl_engine = ReinforcementLearningEngine(learning_mode=mode_map.get(learning_mode, LearningMode.HYBRID))
    logger.info(f"Learning session initialized for game {game_id} in {learning_mode} mode")

def get_rl_action_recommendation(score: float, available_actions: List[int],
                                action_number: int, visual_features: List[float] = None,
                                coordinate_space: Tuple[int, int] = (32, 32),
                                training: bool = True) -> Dict[str, Any]:
    """Get action recommendation from reinforcement learning engine."""
    # Encode current state
    state = rl_engine.encode_game_state(score, available_actions, action_number, visual_features, coordinate_space)

    # Select action
    action_idx, confidence, info = rl_engine.select_action(state, available_actions, training)

    # Convert to game action
    game_action = f"ACTION{action_idx + 1}"

    return {
        "recommended_action": game_action,
        "confidence": confidence,
        "learning_info": info,
        "state_encoding": state.to_vector().tolist(),
        "learning_status": rl_engine.get_learning_status()
    }

def record_learning_experience(prev_score: float, prev_available_actions: List[int],
                              prev_action_number: int, selected_action: int,
                              new_score: float, new_available_actions: List[int],
                              new_action_number: int, game_finished: bool,
                              algorithm_id: str = "rl_engine", game_id: str = "unknown"):
    """Record learning experience for training."""
    # Create states
    prev_state = rl_engine.encode_game_state(prev_score, prev_available_actions, prev_action_number)
    new_state = rl_engine.encode_game_state(new_score, new_available_actions, new_action_number)

    # Calculate rewards
    primary_reward, meta_reward = rl_engine.calculate_reward(prev_state, selected_action, new_state, algorithm_id)

    # Create experience
    experience = Experience(
        state=prev_state,
        action=selected_action,
        reward=primary_reward,
        next_state=new_state if not game_finished else None,
        done=game_finished,
        timestamp=time.time(),
        algorithm_id=algorithm_id,
        game_id=game_id,
        meta_reward=meta_reward
    )

    # Learn from experience
    rl_engine.learn_from_experience(experience)

def finish_learning_episode(final_score: float, total_actions: int):
    """Mark end of learning episode."""
    rl_engine.end_episode(final_score, total_actions)

if __name__ == "__main__":
    # Test the reinforcement learning engine
    print("=== REINFORCEMENT LEARNING ENGINE TEST ===")

    # Initialize learning
    initialize_learning_session("test_game", "hybrid")

    # Simulate a simple game episode
    score = 0.0
    available_actions = [1, 2, 3, 4, 6]

    for action_num in range(1, 11):
        # Get action recommendation
        recommendation = get_rl_action_recommendation(score, available_actions, action_num)

        print(f"Action {action_num}:")
        print(f"  Recommended: {recommendation['recommended_action']}")
        print(f"  Confidence: {recommendation['confidence']:.3f}")
        print(f"  Method: {recommendation['learning_info']['method']}")

        # Simulate action result
        new_score = score + random.uniform(-0.1, 0.3)
        selected_action = int(recommendation['recommended_action'].replace('ACTION', '')) - 1

        # Record experience
        record_learning_experience(
            score, available_actions, action_num,
            selected_action, new_score, available_actions,
            action_num + 1, action_num >= 10
        )

        score = new_score

    # Finish episode
    finish_learning_episode(score, 10)

    # Print learning status
    status = rl_engine.get_learning_status()
    print(f"\nLearning Status:")
    print(f"Episodes: {status['episode_count']}")
    print(f"Training Steps: {status['training_steps']}")
    print(f"Epsilon: {status['epsilon']:.3f}")
    print(f"Avg Reward: {status['performance_metrics']['avg_episode_reward']:.3f}")