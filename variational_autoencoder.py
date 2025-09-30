"""
Variational Autoencoder Module

Implements latent space modeling and algorithmic synthesis including:
- Algorithm encoding to latent space representations
- Decoding from latent space to algorithm structures
- Performance prediction through regression on latent vectors
- Latent space interpolation and sampling
- Algorithm generation via latent space exploration

Note: This is a simplified implementation that can work without deep learning frameworks.
For production use, consider implementing with TensorFlow/PyTorch.
"""

import math
import random
import logging
import json
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import pickle

from algorithm_representations import (
    AlgorithmRepresentation, AlgorithmNode, ActionNode, ConditionalNode,
    SequenceNode, ConditionNode, RandomChoiceNode, RepeatNode,
    AlgorithmBuilder
)

logger = logging.getLogger(__name__)


@dataclass
class VAEConfig:
    """Configuration for VAE operations."""
    latent_dimensions: int = 16
    encoding_layers: List[int] = None
    decoding_layers: List[int] = None
    learning_rate: float = 0.001
    batch_size: int = 32
    training_epochs: int = 100
    kl_divergence_weight: float = 0.1
    performance_prediction_weight: float = 0.3
    max_tree_depth: int = 8

    def __post_init__(self):
        if self.encoding_layers is None:
            self.encoding_layers = [64, 32]
        if self.decoding_layers is None:
            self.decoding_layers = [32, 64]


class SimpleDenseLayer:
    """Simple dense layer implementation without external dependencies."""

    def __init__(self, input_size: int, output_size: int, activation: str = "relu"):
        self.input_size = input_size
        self.output_size = output_size
        self.activation = activation

        # Xavier initialization
        limit = math.sqrt(6.0 / (input_size + output_size))
        self.weights = np.random.uniform(-limit, limit, (input_size, output_size))
        self.biases = np.zeros(output_size)

        # For training
        self.last_input = None
        self.last_output = None

    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass through the layer."""
        self.last_input = x.copy()

        # Linear transformation
        output = np.dot(x, self.weights) + self.biases

        # Apply activation
        if self.activation == "relu":
            output = np.maximum(0, output)
        elif self.activation == "sigmoid":
            output = 1 / (1 + np.exp(-np.clip(output, -500, 500)))
        elif self.activation == "tanh":
            output = np.tanh(output)
        # "linear" activation (no transformation)

        self.last_output = output.copy()
        return output

    def backward(self, grad_output: np.ndarray, learning_rate: float = 0.001) -> np.ndarray:
        """Backward pass through the layer."""
        if self.last_input is None or self.last_output is None:
            raise ValueError("Forward pass must be called before backward pass")

        # Gradient of activation function
        if self.activation == "relu":
            activation_grad = (self.last_output > 0).astype(float)
        elif self.activation == "sigmoid":
            activation_grad = self.last_output * (1 - self.last_output)
        elif self.activation == "tanh":
            activation_grad = 1 - self.last_output ** 2
        else:  # linear
            activation_grad = np.ones_like(self.last_output)

        # Apply activation gradient
        grad_output = grad_output * activation_grad

        # Compute gradients
        grad_weights = np.outer(self.last_input, grad_output)
        grad_biases = grad_output
        grad_input = np.dot(grad_output, self.weights.T)

        # Update parameters
        self.weights -= learning_rate * grad_weights
        self.biases -= learning_rate * grad_biases

        return grad_input


class AlgorithmEncoder:
    """Encodes algorithm representations to fixed-size vectors."""

    def __init__(self, max_nodes: int = 50, max_depth: int = 8):
        self.max_nodes = max_nodes
        self.max_depth = max_depth

        # Feature indices for different node types
        self.node_type_features = {
            "action": 0,
            "conditional": 1,
            "sequence": 2,
            "random_choice": 3,
            "repeat": 4,
            "condition": 5
        }

        # Action type features
        self.action_features = {
            f"ACTION{i}": i for i in range(1, 8)
        }

        # Condition type features
        self.condition_features = {
            "score_threshold": 0,
            "action_count": 1,
            "frame_changed": 2,
            "available_actions": 3,
            "coordinate_success": 4
        }

    def encode_algorithm(self, algorithm: AlgorithmRepresentation) -> np.ndarray:
        """Encode algorithm to fixed-size vector."""
        # Get all nodes
        nodes = algorithm.get_all_nodes()

        # Create feature vector
        features = []

        # Basic statistics
        features.extend([
            len(nodes) / self.max_nodes,  # Normalized node count
            algorithm.get_depth() / self.max_depth,  # Normalized depth
            algorithm.fitness_score / 100.0,  # Normalized fitness
            algorithm.generation / 100.0,  # Normalized generation
        ])

        # Node type distribution
        node_type_counts = {nt: 0 for nt in self.node_type_features.keys()}
        action_type_counts = {at: 0 for at in self.action_features.keys()}
        condition_type_counts = {ct: 0 for ct in self.condition_features.keys()}

        for node in nodes:
            node_type = node.node_type
            if node_type in node_type_counts:
                node_type_counts[node_type] += 1

            if isinstance(node, ActionNode):
                if node.action_type in action_type_counts:
                    action_type_counts[node.action_type] += 1

            elif isinstance(node, ConditionNode):
                if node.condition_type in condition_type_counts:
                    condition_type_counts[node.condition_type] += 1

        # Normalize counts
        total_nodes = max(1, len(nodes))
        features.extend([count / total_nodes for count in node_type_counts.values()])
        features.extend([count / total_nodes for count in action_type_counts.values()])
        features.extend([count / total_nodes for count in condition_type_counts.values()])

        # Structural features
        features.extend([
            self._calculate_branching_factor(algorithm),
            self._calculate_action_diversity(nodes),
            self._calculate_condition_complexity(nodes),
            len(algorithm.parent_ids) / 10.0,  # Normalized parent count
        ])

        return np.array(features, dtype=np.float32)

    def _calculate_branching_factor(self, algorithm: AlgorithmRepresentation) -> float:
        """Calculate average branching factor of the algorithm tree."""
        nodes = algorithm.get_all_nodes()
        total_children = 0
        branching_nodes = 0

        for node in nodes:
            if isinstance(node, ConditionalNode):
                total_children += 3  # condition + true + false
                branching_nodes += 1
            elif isinstance(node, SequenceNode):
                total_children += len(node.children)
                branching_nodes += 1
            elif isinstance(node, RandomChoiceNode):
                total_children += len(node.choices)
                branching_nodes += 1
            elif isinstance(node, RepeatNode):
                total_children += 1
                branching_nodes += 1

        return (total_children / max(1, branching_nodes)) / 10.0  # Normalized

    def _calculate_action_diversity(self, nodes: List[AlgorithmNode]) -> float:
        """Calculate diversity of actions in the algorithm."""
        action_nodes = [n for n in nodes if isinstance(n, ActionNode)]
        if not action_nodes:
            return 0.0

        unique_actions = set(node.action_type for node in action_nodes)
        return len(unique_actions) / 7.0  # Normalized by max actions (7)

    def _calculate_condition_complexity(self, nodes: List[AlgorithmNode]) -> float:
        """Calculate complexity of conditions in the algorithm."""
        condition_nodes = [n for n in nodes if isinstance(n, ConditionNode)]
        if not condition_nodes:
            return 0.0

        complexity_score = 0.0
        for node in condition_nodes:
            # Score based on condition type and parameters
            if node.condition_type == "score_threshold":
                complexity_score += 0.2
            elif node.condition_type == "action_count":
                complexity_score += 0.3
            elif node.condition_type == "frame_changed":
                complexity_score += 0.4
            elif node.condition_type == "available_actions":
                complexity_score += 0.5
            elif node.condition_type == "coordinate_success":
                complexity_score += 0.6

        return min(1.0, complexity_score / len(condition_nodes))

    def get_feature_size(self) -> int:
        """Get the size of the encoded feature vector."""
        return (4 +  # Basic stats
                len(self.node_type_features) +  # Node types
                len(self.action_features) +  # Action types
                len(self.condition_features) +  # Condition types
                4)  # Structural features


class SimpleVariationalAutoencoder:
    """Simplified VAE implementation for algorithm representations."""

    def __init__(self, config: VAEConfig = None, database_interface = None):
        self.config = config or VAEConfig()
        self.db = database_interface

        # Initialize encoder
        self.algorithm_encoder = AlgorithmEncoder()
        input_size = self.algorithm_encoder.get_feature_size()

        # Build encoder network
        self.encoder_layers = []
        layer_sizes = [input_size] + self.config.encoding_layers
        for i in range(len(layer_sizes) - 1):
            activation = "relu" if i < len(layer_sizes) - 2 else "linear"
            self.encoder_layers.append(
                SimpleDenseLayer(layer_sizes[i], layer_sizes[i + 1], activation)
            )

        # Latent space layers (mean and log variance)
        final_encoder_size = self.config.encoding_layers[-1]
        self.mu_layer = SimpleDenseLayer(final_encoder_size, self.config.latent_dimensions, "linear")
        self.logvar_layer = SimpleDenseLayer(final_encoder_size, self.config.latent_dimensions, "linear")

        # Build decoder network
        self.decoder_layers = []
        layer_sizes = [self.config.latent_dimensions] + self.config.decoding_layers + [input_size]
        for i in range(len(layer_sizes) - 1):
            activation = "relu" if i < len(layer_sizes) - 2 else "sigmoid"
            self.decoder_layers.append(
                SimpleDenseLayer(layer_sizes[i], layer_sizes[i + 1], activation)
            )

        # Performance prediction head
        self.performance_predictor = SimpleDenseLayer(self.config.latent_dimensions, 1, "linear")

        # Training state
        self.training_epoch = 0
        self.training_history = []

    def encode(self, algorithm: AlgorithmRepresentation) -> Tuple[np.ndarray, np.ndarray]:
        """Encode algorithm to latent space (mean and log variance).

        Args:
            algorithm: Algorithm to encode

        Returns:
            Tuple of (mean, log_variance) vectors
        """
        # Convert algorithm to feature vector
        features = self.algorithm_encoder.encode_algorithm(algorithm)

        # Forward pass through encoder
        x = features
        for layer in self.encoder_layers:
            x = layer.forward(x)

        # Get latent parameters
        mu = self.mu_layer.forward(x)
        logvar = self.logvar_layer.forward(x)

        return mu, logvar

    def reparameterize(self, mu: np.ndarray, logvar: np.ndarray) -> np.ndarray:
        """Reparameterization trick for sampling from latent space.

        Args:
            mu: Mean vector
            logvar: Log variance vector

        Returns:
            Sampled latent vector
        """
        std = np.exp(0.5 * logvar)
        eps = np.random.normal(0, 1, size=std.shape)
        return mu + eps * std

    def decode(self, z: np.ndarray) -> np.ndarray:
        """Decode latent vector to algorithm features.

        Args:
            z: Latent vector

        Returns:
            Reconstructed feature vector
        """
        x = z
        for layer in self.decoder_layers:
            x = layer.forward(x)
        return x

    def predict_performance(self, z: np.ndarray) -> float:
        """Predict algorithm performance from latent vector.

        Args:
            z: Latent vector

        Returns:
            Predicted performance score
        """
        prediction = self.performance_predictor.forward(z)
        return float(prediction[0]) * 100.0  # Scale to 0-100 range

    def generate_algorithm(self, z: np.ndarray = None) -> AlgorithmRepresentation:
        """Generate algorithm from latent space.

        Args:
            z: Optional latent vector. If None, samples from prior.

        Returns:
            Generated algorithm
        """
        if z is None:
            # Sample from prior (standard normal)
            z = np.random.normal(0, 1, self.config.latent_dimensions)

        # Decode to features
        features = self.decode(z)

        # Convert features to algorithm structure
        # This is a simplified approach - in practice would need more sophisticated generation
        return self._features_to_algorithm(features)

    def _features_to_algorithm(self, features: np.ndarray) -> AlgorithmRepresentation:
        """Convert feature vector to algorithm structure.

        This is a simplified implementation that creates algorithms based on feature patterns.
        """
        # Extract key features
        node_count = max(1, int(features[0] * self.algorithm_encoder.max_nodes))
        depth = max(1, int(features[1] * self.algorithm_encoder.max_depth))

        # Get most likely node types from features
        node_type_start = 4
        node_type_probs = features[node_type_start:node_type_start + 6]
        dominant_node_type = np.argmax(node_type_probs)

        # Get most likely action types
        action_type_start = node_type_start + 6
        action_type_probs = features[action_type_start:action_type_start + 7]
        dominant_action = np.argmax(action_type_probs) + 1  # ACTION1-7

        # Create algorithm based on dominant patterns
        if dominant_node_type == 0:  # Action-dominant
            if np.random.random() < 0.5:
                return AlgorithmBuilder.create_random_action_algorithm()
            else:
                # Create simple action sequence
                actions = [f"ACTION{dominant_action}"]
                if node_count > 1:
                    actions.extend([f"ACTION{random.randint(1, 7)}" for _ in range(min(3, node_count - 1))])

                action_nodes = [ActionNode("action", action_type=action) for action in actions]
                if len(action_nodes) == 1:
                    return AlgorithmRepresentation(action_nodes[0])
                else:
                    sequence = SequenceNode("sequence", children=action_nodes)
                    return AlgorithmRepresentation(sequence)

        elif dominant_node_type == 1:  # Conditional-dominant
            return AlgorithmBuilder.create_score_based_algorithm()

        else:  # Mixed or other types
            return AlgorithmBuilder.create_adaptive_algorithm()

    def train_on_algorithms(self, algorithms: List[AlgorithmRepresentation],
                          performances: List[float] = None) -> Dict[str, Any]:
        """Train the VAE on a collection of algorithms.

        Args:
            algorithms: List of algorithms to train on
            performances: Optional performance scores for each algorithm

        Returns:
            Training statistics
        """
        if not algorithms:
            return {"error": "No algorithms provided for training"}

        if performances is None:
            performances = [alg.fitness_score for alg in algorithms]

        total_loss = 0.0
        reconstruction_loss = 0.0
        kl_loss = 0.0
        performance_loss = 0.0

        # Simple batch training (process all at once for simplicity)
        for algorithm, performance in zip(algorithms, performances):
            try:
                # Encode
                mu, logvar = self.encode(algorithm)

                # Sample from latent space
                z = self.reparameterize(mu, logvar)

                # Decode
                original_features = self.algorithm_encoder.encode_algorithm(algorithm)
                reconstructed_features = self.decode(z)

                # Predict performance
                predicted_performance = self.predict_performance(z)

                # Calculate losses
                recon_loss = np.mean((original_features - reconstructed_features) ** 2)
                kl_div = -0.5 * np.sum(1 + logvar - mu ** 2 - np.exp(logvar))
                perf_loss = (performance - predicted_performance) ** 2

                reconstruction_loss += recon_loss
                kl_loss += kl_div
                performance_loss += perf_loss

            except Exception as e:
                logger.warning(f"Error training on algorithm {algorithm.algorithm_id}: {e}")
                continue

        # Average losses
        num_algorithms = len(algorithms)
        reconstruction_loss /= num_algorithms
        kl_loss /= num_algorithms
        performance_loss /= num_algorithms

        total_loss = (reconstruction_loss +
                     self.config.kl_divergence_weight * kl_loss +
                     self.config.performance_prediction_weight * performance_loss)

        self.training_epoch += 1

        # Store training history
        training_stats = {
            "epoch": self.training_epoch,
            "total_loss": float(total_loss),
            "reconstruction_loss": float(reconstruction_loss),
            "kl_loss": float(kl_loss),
            "performance_loss": float(performance_loss),
            "num_algorithms": num_algorithms,
            "timestamp": datetime.now().isoformat()
        }

        self.training_history.append(training_stats)

        logger.info(f"VAE training epoch {self.training_epoch} complete. "
                   f"Total loss: {total_loss:.4f}")

        return training_stats

    def interpolate_algorithms(self, alg1: AlgorithmRepresentation,
                             alg2: AlgorithmRepresentation,
                             steps: int = 5) -> List[AlgorithmRepresentation]:
        """Interpolate between two algorithms in latent space.

        Args:
            alg1: First algorithm
            alg2: Second algorithm
            steps: Number of interpolation steps

        Returns:
            List of interpolated algorithms
        """
        # Encode both algorithms
        mu1, _ = self.encode(alg1)
        mu2, _ = self.encode(alg2)

        # Interpolate in latent space
        interpolated_algorithms = []
        for i in range(steps):
            alpha = i / (steps - 1) if steps > 1 else 0.5
            z_interp = (1 - alpha) * mu1 + alpha * mu2

            # Generate algorithm from interpolated latent vector
            interp_alg = self.generate_algorithm(z_interp)
            interp_alg.algorithm_id = f"interp_{alg1.algorithm_id}_{alg2.algorithm_id}_{i}"
            interp_alg.metadata["interpolation"] = {
                "parent1": alg1.algorithm_id,
                "parent2": alg2.algorithm_id,
                "alpha": alpha
            }

            interpolated_algorithms.append(interp_alg)

        return interpolated_algorithms

    def find_similar_algorithms(self, target_algorithm: AlgorithmRepresentation,
                               candidate_algorithms: List[AlgorithmRepresentation],
                               top_k: int = 5) -> List[Tuple[AlgorithmRepresentation, float]]:
        """Find algorithms similar to target in latent space.

        Args:
            target_algorithm: Algorithm to find similarities for
            candidate_algorithms: Pool of candidate algorithms
            top_k: Number of similar algorithms to return

        Returns:
            List of (algorithm, similarity_score) tuples
        """
        # Encode target
        target_mu, _ = self.encode(target_algorithm)

        # Calculate similarities
        similarities = []
        for candidate in candidate_algorithms:
            if candidate.algorithm_id == target_algorithm.algorithm_id:
                continue

            try:
                candidate_mu, _ = self.encode(candidate)

                # Calculate cosine similarity in latent space
                dot_product = np.dot(target_mu, candidate_mu)
                norm_target = np.linalg.norm(target_mu)
                norm_candidate = np.linalg.norm(candidate_mu)

                similarity = dot_product / (norm_target * norm_candidate + 1e-8)
                similarities.append((candidate, float(similarity)))

            except Exception as e:
                logger.warning(f"Error calculating similarity for {candidate.algorithm_id}: {e}")
                continue

        # Sort by similarity and return top-k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def save_model(self, filepath: str):
        """Save VAE model to file.

        Args:
            filepath: Path to save the model
        """
        model_data = {
            "config": self.config,
            "training_epoch": self.training_epoch,
            "training_history": self.training_history,
            # Note: In a real implementation, would save neural network weights
            "model_id": f"vae_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }

        try:
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            logger.info(f"VAE model saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save VAE model: {e}")

    def load_model(self, filepath: str):
        """Load VAE model from file.

        Args:
            filepath: Path to load the model from
        """
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)

            self.config = model_data.get("config", self.config)
            self.training_epoch = model_data.get("training_epoch", 0)
            self.training_history = model_data.get("training_history", [])

            logger.info(f"VAE model loaded from {filepath}")
        except Exception as e:
            logger.error(f"Failed to load VAE model: {e}")

    def get_latent_space_statistics(self, algorithms: List[AlgorithmRepresentation]) -> Dict[str, Any]:
        """Get statistics about the latent space for a set of algorithms.

        Args:
            algorithms: Algorithms to analyze

        Returns:
            Latent space statistics
        """
        if not algorithms:
            return {"error": "No algorithms provided"}

        # Encode all algorithms
        latent_vectors = []
        for algorithm in algorithms:
            try:
                mu, logvar = self.encode(algorithm)
                latent_vectors.append(mu)
            except Exception as e:
                logger.warning(f"Error encoding algorithm {algorithm.algorithm_id}: {e}")

        if not latent_vectors:
            return {"error": "No algorithms could be encoded"}

        latent_matrix = np.array(latent_vectors)

        # Calculate statistics
        mean_vector = np.mean(latent_matrix, axis=0)
        std_vector = np.std(latent_matrix, axis=0)

        # Calculate pairwise distances
        distances = []
        for i in range(len(latent_vectors)):
            for j in range(i + 1, len(latent_vectors)):
                dist = np.linalg.norm(latent_vectors[i] - latent_vectors[j])
                distances.append(dist)

        return {
            "num_algorithms": len(algorithms),
            "latent_dimensions": self.config.latent_dimensions,
            "mean_vector": mean_vector.tolist(),
            "std_vector": std_vector.tolist(),
            "avg_pairwise_distance": np.mean(distances) if distances else 0.0,
            "min_distance": np.min(distances) if distances else 0.0,
            "max_distance": np.max(distances) if distances else 0.0,
            "latent_space_coverage": np.mean(std_vector) / np.mean(np.abs(mean_vector) + 1e-8)
        }