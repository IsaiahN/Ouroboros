#!/usr/bin/env python3
# pyright: reportOptionalMemberAccess=false
# pyright: reportGeneralTypeIssues=false
import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: MUST be before other imports

"""
Self-Supervised Dynamics: Representation Learner
================================================

Learns continuous vector embeddings from gameplay data for implicit generalization.
Uses dynamics prediction (frame_before, action) -> frame_after to learn what matters.

This enables finding "similar situations" across games without exact symbolic matches.
A rotated, color-swapped version of a pattern lands near the original in embedding space.

Architecture:
- GridEncoder: Conv net that compresses 64x64x10 frames to 128-dim embeddings
- DynamicsPredictor: Predicts next frame embedding from (current_embed, action)
- RepresentationLearner: Training, inference, and database integration

Training Data Source: action_traces table (frame_before, action, frame_after, score_delta)
Training Frequency: Every 10 generations (matches safe_cleanup cadence)

See architecture/Self_Supervised_Dynamics_Implementation.md for full design.
"""

import json
import logging
import random
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

import numpy as np

# PyTorch imports - graceful degradation if not available
TORCH_AVAILABLE = False
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    torch = None  # type: ignore[assignment]
    nn = None  # type: ignore[assignment]
    F = None  # type: ignore[assignment]

if TYPE_CHECKING:
    import torch
    import torch.nn as nn

    from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


# ============================================================================
# NEURAL NETWORK ARCHITECTURE
# ============================================================================

if TORCH_AVAILABLE:  # type: ignore[truthy-bool]

    class GridEncoder(nn.Module):
        """
        Convolutional encoder for 64x64 ARC game frames.

        Input: (batch, 10, 64, 64) - one-hot color channels
        Output: (batch, 128) - latent embedding

        Architecture designed for:
        - Fast CPU inference (~1ms per frame)
        - Robust to small variations (BatchNorm + LayerNorm)
        - Cosine similarity compatible (LayerNorm output)
        """

        def __init__(self, num_colors: int = 10, latent_dim: int = 128):
            super().__init__()
            self.num_colors = num_colors
            self.latent_dim = latent_dim

            self.encoder = nn.Sequential(
                # 64x64 -> 32x32
                nn.Conv2d(num_colors, 32, kernel_size=3, stride=2, padding=1),
                nn.BatchNorm2d(32),
                nn.ReLU(),

                # 32x32 -> 16x16
                nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1),
                nn.BatchNorm2d(64),
                nn.ReLU(),

                # 16x16 -> 8x8
                nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1),
                nn.BatchNorm2d(128),
                nn.ReLU(),

                # 8x8 -> 4x4
                nn.Conv2d(128, 128, kernel_size=3, stride=2, padding=1),
                nn.BatchNorm2d(128),
                nn.ReLU(),

                # Flatten and project
                nn.Flatten(),
                nn.Linear(128 * 4 * 4, latent_dim),
                nn.LayerNorm(latent_dim)  # Normalize for cosine similarity
            )

        def forward(self, x: Any) -> Any:
            return self.encoder(x)


    class DynamicsPredictor(nn.Module):
        """
        Predicts next frame embedding from current embedding + action.

        Input: (batch, 128 + 8) - embedding + one-hot action
        Output: (batch, 128) - predicted next embedding

        This learns the dynamics of the game - what happens when you take an action.
        """

        def __init__(self, latent_dim: int = 128, num_actions: int = 8):
            super().__init__()
            self.latent_dim = latent_dim
            self.num_actions = num_actions

            self.predictor = nn.Sequential(
                nn.Linear(latent_dim + num_actions, 256),
                nn.ReLU(),
                nn.Dropout(0.1),
                nn.Linear(256, 256),
                nn.ReLU(),
                nn.Linear(256, latent_dim)
            )

        def forward(self, embedding: Any, action_onehot: Any) -> Any:
            combined = torch.cat([embedding, action_onehot], dim=-1)
            return self.predictor(combined)


    class DynamicsModel(nn.Module):
        """
        Combined encoder + dynamics predictor.

        Training objective: Given (frame_before, action), predict frame_after's embedding.
        This forces the encoder to learn features that matter for game progression.
        """

        def __init__(self, num_colors: int = 10, latent_dim: int = 128, num_actions: int = 8):
            super().__init__()
            self.encoder = GridEncoder(num_colors, latent_dim)
            self.dynamics = DynamicsPredictor(latent_dim, num_actions)
            self.latent_dim = latent_dim
            self.num_actions = num_actions

        def encode(self, frame: Any) -> Any:
            """Get embedding for a frame."""
            return self.encoder(frame)

        def predict_next(self, frame: Any, action_onehot: Any) -> Any:
            """Predict next frame's embedding."""
            current_embed = self.encode(frame)
            return self.dynamics(current_embed, action_onehot)

        def forward(
            self,
            frame_before: Any,
            action_onehot: Any,
            frame_after: Any
        ) -> Tuple[Any, Any]:
            """
            Training forward pass.
            Returns: (predicted_next_embed, actual_next_embed)
            """
            embed_before = self.encode(frame_before)
            embed_after_actual = self.encode(frame_after)
            embed_after_predicted = self.dynamics(embed_before, action_onehot)
            return embed_after_predicted, embed_after_actual


# ============================================================================
# REPRESENTATION LEARNER (Main Class)
# ============================================================================

class RepresentationLearner:
    """
    Main interface for self-supervised dynamics learning.

    Responsibilities:
    - Load training data from action_traces
    - Train the dynamics model
    - Encode frames to embeddings
    - Find similar situations via embedding similarity
    - Store/load model checkpoints
    - Compute embeddings for database storage

    Integration Points:
    - Called by autonomous_evolution_runner every 10 generations for training
    - Called by agent_self_model for similarity-based action suggestions
    - Embeddings stored in frame_embeddings table
    """

    def __init__(
        self,
        db_path: str = "core_data.db",
        model_path: Optional[str] = None,
        latent_dim: int = 128,
        num_colors: int = 10,
        num_actions: int = 8
    ):
        """
        Initialize the representation learner.

        Args:
            db_path: Path to database (creates DatabaseInterface internally)
            model_path: Path to load existing model from (creates new if None/missing)
            latent_dim: Dimensionality of embedding space (default 128)
            num_colors: Number of color channels in frames (default 10)
            num_actions: Number of possible actions (default 8, including ACTION0)
        """
        # Import here to avoid circular imports
        from database_interface import DatabaseInterface
        self.db = DatabaseInterface(db_path)

        self.model_path = model_path or "models/dynamics_model.pt"
        self.latent_dim = latent_dim
        self.num_colors = num_colors
        self.num_actions = num_actions

        if not TORCH_AVAILABLE:
            logger.warning("[REP] PyTorch not available - representation learning disabled")
            self.model = None
            self.optimizer = None
            return

        # Initialize or load model
        self.model = DynamicsModel(num_colors, latent_dim, num_actions)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=1e-4)

        # Try to load existing model
        model_exists = os.path.exists(self.model_path)
        if model_exists:
            try:
                self.load_model(self.model_path)
                logger.info(f"[REP] Loaded model from {self.model_path}")
            except Exception as e:
                logger.warning(f"[REP] Could not load model: {e}, starting fresh")
        else:
            logger.info("[REP] Initialized new dynamics model")

        # Ensure models directory exists
        Path(self.model_path).parent.mkdir(parents=True, exist_ok=True)

    # ========================================================================
    # DATA LOADING
    # ========================================================================

    def load_training_data(self, limit: int = 50000) -> List[Dict]:
        """
        Load training data directly from existing action_traces table.

        Filters:
        - Must have both frame_before and frame_after
        - Action must be 1-7 (valid game actions)
        - Prioritizes score-changing actions (more learning signal)

        Args:
            limit: Maximum number of samples to load

        Returns:
            List of training samples with frame_before, frame_after, action, etc.
        """
        if not self.db:
            return []

        rows = self.db.execute_query("""
            SELECT
                id,
                game_id,
                level_number,
                action_number,
                frame_before,
                frame_after,
                score_change,
                frame_changed
            FROM action_traces
            WHERE frame_before IS NOT NULL
              AND frame_after IS NOT NULL
              AND action_number BETWEEN 1 AND 7
            ORDER BY
                ABS(COALESCE(score_change, 0)) DESC,
                RANDOM()
            LIMIT ?
        """, (limit,))

        data = []
        for row in rows or []:
            try:
                frame_before = json.loads(row['frame_before'])
                frame_after = json.loads(row['frame_after'])

                # Validate frames are non-empty
                if not frame_before or not frame_after:
                    continue
                if not frame_before[0] or not frame_after[0]:
                    continue

                data.append({
                    'trace_id': row['id'],
                    'game_type': row['game_id'].split('-')[0] if row['game_id'] else 'unknown',
                    'level': row['level_number'] or 1,
                    'action': row['action_number'],
                    'frame_before': frame_before,
                    'frame_after': frame_after,
                    'score_delta': row['score_change'] or 0.0,
                    'frame_changed': bool(row['frame_changed']),
                })
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.debug(f"Skipping malformed trace: {e}")
                continue

        return data

    # ========================================================================
    # TENSOR CONVERSION
    # ========================================================================

    def _frame_to_tensor(self, frame: List[List[int]]) -> Any:
        """
        Convert JSON grid to one-hot tensor.

        Input: HxW list of color integers (0-9)
        Output: (10, 64, 64) tensor with one-hot channels

        Handles variable-sized frames by padding/cropping to 64x64.
        """
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch not available")

        h = len(frame)
        w = len(frame[0]) if frame else 0

        # Create padded 64x64 grid (black background)
        padded = [[0] * 64 for _ in range(64)]
        for i in range(min(h, 64)):
            for j in range(min(w, 64)):
                val = frame[i][j] if i < len(frame) and j < len(frame[i]) else 0
                padded[i][j] = val if 0 <= val < self.num_colors else 0

        # Convert to numpy then one-hot
        arr = np.array(padded, dtype=np.int64)
        one_hot = np.eye(self.num_colors, dtype=np.float32)[arr]  # (64, 64, 10)
        one_hot = one_hot.transpose(2, 0, 1)  # (10, 64, 64)

        return torch.from_numpy(one_hot)

    # ========================================================================
    # TRAINING
    # ========================================================================

    def train_on_recent_games(
        self,
        max_traces: int = 50000,
        hours: int = 72,
        epochs: int = 10,
        batch_size: int = 64,
        min_samples: int = 1000
    ) -> Optional[Dict[str, Any]]:
        """
        Train the dynamics model on recent gameplay data.
        Called every 10 generations by autonomous_evolution_runner.

        Training objective: Predict next frame embedding from (current frame, action).

        Args:
            max_traces: Maximum number of traces to train on
            hours: Lookback window (not currently used, loads by count)
            epochs: Number of training epochs
            batch_size: Training batch size
            min_samples: Minimum samples required to train

        Returns:
            Training stats dict or None if insufficient data
        """
        if not TORCH_AVAILABLE or self.model is None:
            print("[REP] PyTorch not available, skipping training")
            return None

        print(f"[REP] Loading training data...")
        data = self.load_training_data(limit=max_traces)

        if len(data) < min_samples:
            print(f"[REP] Insufficient data ({len(data)} samples < {min_samples}), skipping training")
            return None

        print(f"[REP] Training on {len(data)} frame transitions...")
        start_time = time.time()
        self.model.train()

        epoch_losses = []

        for epoch in range(epochs):
            random.shuffle(data)
            total_loss = 0.0
            num_batches = 0

            for i in range(0, len(data) - batch_size, batch_size):
                batch = data[i:i+batch_size]

                try:
                    # Convert to tensors
                    frames_before = torch.stack([
                        self._frame_to_tensor(b['frame_before']) for b in batch
                    ])
                    frames_after = torch.stack([
                        self._frame_to_tensor(b['frame_after']) for b in batch
                    ])
                    actions = torch.tensor([b['action'] for b in batch], dtype=torch.long)
                    action_onehot = F.one_hot(actions, num_classes=self.num_actions).float()

                    # Forward pass
                    predicted, actual = self.model(frames_before, action_onehot, frames_after)

                    # MSE loss on embeddings
                    base_loss = F.mse_loss(predicted, actual.detach(), reduction='none')

                    # Weight by importance (score-changing transitions matter more)
                    importance = torch.tensor([
                        1.0 + min(5.0, abs(b['score_delta']))
                        for b in batch
                    ], dtype=torch.float32)

                    # Apply importance weighting
                    weighted_loss = (base_loss.mean(dim=1) * importance).mean()

                    # Backward pass
                    self.optimizer.zero_grad()
                    weighted_loss.backward()
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                    self.optimizer.step()

                    total_loss += weighted_loss.item()
                    num_batches += 1

                except Exception as e:
                    logger.debug(f"Batch failed: {e}")
                    continue

            avg_loss = total_loss / max(1, num_batches)
            epoch_losses.append(avg_loss)
            print(f"  Epoch {epoch+1}/{epochs}: Loss = {avg_loss:.4f}")

        training_duration = time.time() - start_time

        # Save updated model
        self.save_model()
        print(f"[REP] Training complete in {training_duration:.1f}s, model saved")

        # Record training history
        final_loss = epoch_losses[-1] if epoch_losses else None
        self._record_training_history(len(data), final_loss, training_duration)

        return {
            'samples': len(data),
            'traces_used': len(data),  # Alias for compatibility
            'epochs': epochs,
            'final_loss': final_loss,
            'duration_seconds': training_duration,
            'epoch_losses': epoch_losses,
        }

    def _record_training_history(
        self,
        training_samples: int,
        final_loss: Optional[float],
        duration_seconds: float
    ):
        """Record training run to database for monitoring."""
        try:
            self.db.execute_query("""
                INSERT INTO representation_model_history
                (model_version, training_samples, final_loss, training_duration_seconds, trained_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            """, ('v1', training_samples, final_loss, duration_seconds))
        except Exception as e:
            logger.debug(f"Could not record training history: {e}")

    def get_model_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the current model state.

        Returns:
            Dict with model info, or None if no model exists
        """
        if not TORCH_AVAILABLE:
            return None

        # Check if model file exists
        if not os.path.exists(self.model_path):
            return None

        try:
            # Get last training record from database
            rows = self.db.execute_query("""
                SELECT
                    model_version,
                    training_samples,
                    final_loss,
                    training_duration_seconds,
                    trained_at
                FROM representation_model_history
                ORDER BY trained_at DESC
                LIMIT 1
            """)

            if rows:
                return {
                    'model_path': self.model_path,
                    'model_version': rows[0]['model_version'],
                    'training_samples': rows[0]['training_samples'],
                    'final_loss': rows[0]['final_loss'],
                    'training_duration': rows[0]['training_duration_seconds'],
                    'trained_at': rows[0]['trained_at'],
                    'file_exists': True
                }
            else:
                # Model file exists but no training history
                return {
                    'model_path': self.model_path,
                    'model_version': 'v1',
                    'training_samples': 0,
                    'final_loss': None,
                    'trained_at': None,
                    'file_exists': True
                }

        except Exception as e:
            logger.debug(f"Could not get model info: {e}")
            return None

    def count_new_traces_since_training(self) -> int:
        """
        Count how many new action traces exist since last training.

        Used to determine if retraining is needed.

        Returns:
            Number of action traces added since last model training
        """
        try:
            # Get last training timestamp
            rows = self.db.execute_query("""
                SELECT trained_at FROM representation_model_history
                ORDER BY trained_at DESC
                LIMIT 1
            """)

            if not rows or not rows[0]['trained_at']:
                # No training history - count all traces
                count_rows = self.db.execute_query("""
                    SELECT COUNT(*) as cnt FROM action_traces
                    WHERE frame_before IS NOT NULL
                    AND frame_after IS NOT NULL
                """)
                return count_rows[0]['cnt'] if count_rows else 0

            last_trained = rows[0]['trained_at']

            # Count traces added since last training
            count_rows = self.db.execute_query("""
                SELECT COUNT(*) as cnt FROM action_traces
                WHERE frame_before IS NOT NULL
                AND frame_after IS NOT NULL
                AND timestamp > ?
            """, (last_trained,))

            return count_rows[0]['cnt'] if count_rows else 0

        except Exception as e:
            logger.debug(f"Could not count new traces: {e}")
            return 0

    # ========================================================================
    # INFERENCE
    # ========================================================================

    def encode_frame(self, frame: List[List[int]]) -> Optional[np.ndarray]:
        """
        Get learned representation (embedding) for a game frame.

        Args:
            frame: 2D list of color values

        Returns:
            128-dimensional numpy array, or None if encoding fails
        """
        if not TORCH_AVAILABLE or self.model is None:
            return None

        try:
            self.model.eval()
            with torch.no_grad():
                tensor = self._frame_to_tensor(frame).unsqueeze(0)
                embedding = self.model.encode(tensor)
                return embedding.squeeze().numpy()
        except Exception as e:
            logger.debug(f"Encoding failed: {e}")
            return None

    def find_similar_situations(
        self,
        frame: List[List[int]],
        game_type: Optional[str] = None,
        level: Optional[int] = None,
        top_k: int = 10
    ) -> List[Dict]:
        """
        Find historically similar situations using embedding similarity.

        Args:
            frame: Current game frame to find matches for
            game_type: Optional filter to same game type
            level: Optional filter to same level
            top_k: Number of results to return

        Returns:
            List of similar past experiences with their outcomes
        """
        if not TORCH_AVAILABLE or self.model is None:
            return []

        # Encode query frame
        query_embed = self.encode_frame(frame)
        if query_embed is None:
            return []

        # Build SQL filter
        where_clauses = ["1=1"]
        params: List[Any] = []

        if game_type:
            where_clauses.append("game_type = ?")
            params.append(game_type)
        if level is not None:
            where_clauses.append("level_number = ?")
            params.append(level)

        where_sql = " AND ".join(where_clauses)
        params.append(top_k * 10)  # Get more candidates, filter by similarity

        # Get candidate embeddings from database
        try:
            rows = self.db.execute_query(f"""
                SELECT
                    trace_id,
                    embedding,
                    game_type,
                    level_number,
                    action_taken,
                    score_delta,
                    frame_changed
                FROM frame_embeddings
                WHERE {where_sql}
                ORDER BY RANDOM()
                LIMIT ?
            """, tuple(params))
        except Exception as e:
            logger.debug(f"Embedding query failed: {e}")
            return []

        if not rows:
            return []

        # Compute similarities
        results = []
        for row in rows:
            try:
                stored_embed = np.frombuffer(row['embedding'], dtype=np.float32)

                # Cosine similarity
                norm_query = np.linalg.norm(query_embed)
                norm_stored = np.linalg.norm(stored_embed)
                if norm_query < 1e-8 or norm_stored < 1e-8:
                    continue

                similarity = float(np.dot(query_embed, stored_embed) / (norm_query * norm_stored))

                results.append({
                    'trace_id': row['trace_id'],
                    'similarity': similarity,
                    'game_type': row['game_type'],
                    'level': row['level_number'],
                    'action_taken': row['action_taken'],
                    'score_delta': row['score_delta'] or 0.0,
                    'frame_changed': bool(row['frame_changed']),
                })
            except Exception as e:
                logger.debug(f"Similarity computation failed: {e}")
                continue

        # Sort by similarity and return top_k
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]

    # ========================================================================
    # EMBEDDING COMPUTATION FOR DATABASE
    # ========================================================================

    def compute_embeddings_for_recent_traces(self, max_traces: int = 10000, batch_size: int = 100) -> int:
        """
        Compute and store embeddings for recent action traces that don't have them.

        Args:
            max_traces: Maximum number of traces to compute embeddings for
            batch_size: Number of traces to process at once

        Returns:
            Number of embeddings computed
        """
        if not TORCH_AVAILABLE or self.model is None:
            return 0

        # Get traces without embeddings
        rows = self.db.execute_query("""
            SELECT
                at.id as trace_id,
                at.game_id,
                at.level_number,
                at.action_number,
                at.frame_before,
                at.score_change,
                at.frame_changed
            FROM action_traces at
            LEFT JOIN frame_embeddings fe ON at.id = fe.trace_id
            WHERE fe.id IS NULL
              AND at.frame_before IS NOT NULL
              AND at.action_number BETWEEN 1 AND 7
            ORDER BY at.id DESC
            LIMIT ?
        """, (max_traces,))

        if not rows:
            return 0

        computed = 0
        self.model.eval()

        for row in rows:
            try:
                frame = json.loads(row['frame_before'])
                if not frame or not frame[0]:
                    continue

                embedding = self.encode_frame(frame)
                if embedding is None:
                    continue

                game_type = row['game_id'].split('-')[0] if row['game_id'] else 'unknown'

                # Store embedding
                self.db.execute_query("""
                    INSERT OR IGNORE INTO frame_embeddings
                    (trace_id, game_type, level_number, embedding, action_taken, score_delta, frame_changed, model_version)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['trace_id'],
                    game_type,
                    row['level_number'] or 1,
                    embedding.tobytes(),
                    row['action_number'],
                    row['score_change'] or 0.0,
                    bool(row['frame_changed']),
                    'v1'
                ))

                computed += 1

                if computed % 500 == 0:
                    print(f"  [REP] Computed {computed} embeddings...")

            except Exception as e:
                logger.debug(f"Embedding computation failed for trace {row.get('trace_id')}: {e}")
                continue

        return computed

    # ========================================================================
    # MODEL PERSISTENCE
    # ========================================================================

    def save_model(self, path: Optional[str] = None):
        """Save model checkpoint."""
        if not TORCH_AVAILABLE or self.model is None:
            return

        save_path = path or self.model_path
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)

        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'latent_dim': self.latent_dim,
            'num_colors': self.num_colors,
            'num_actions': self.num_actions,
        }, save_path)

        logger.debug(f"[REP] Model saved to {save_path}")

    def load_model(self, path: Optional[str] = None):
        """Load model checkpoint."""
        if not TORCH_AVAILABLE:
            return

        load_path = path or self.model_path

        checkpoint = torch.load(load_path, map_location='cpu')

        # Verify dimensions match
        if checkpoint.get('latent_dim') != self.latent_dim:
            raise ValueError(f"Latent dim mismatch: {checkpoint.get('latent_dim')} vs {self.latent_dim}")

        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])

        logger.debug(f"[REP] Model loaded from {load_path}")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def is_representation_learning_available() -> bool:
    """Check if representation learning is available (PyTorch installed)."""
    return TORCH_AVAILABLE


# ============================================================================
# STANDALONE TESTING
# ============================================================================

if __name__ == "__main__":
    # Quick test if run directly
    print("Self-Supervised Dynamics Representation Learner")
    print("=" * 50)
    print(f"PyTorch available: {TORCH_AVAILABLE}")

    if TORCH_AVAILABLE:
        # Test model creation
        model = DynamicsModel()
        print(f"Model created: {sum(p.numel() for p in model.parameters())} parameters")

        # Test forward pass
        dummy_frame = torch.randn(1, 10, 64, 64)
        dummy_action = F.one_hot(torch.tensor([1]), num_classes=8).float()

        with torch.no_grad():
            embed = model.encode(dummy_frame)
            print(f"Embedding shape: {embed.shape}")

            pred, actual = model(dummy_frame, dummy_action, dummy_frame)
            print(f"Prediction shape: {pred.shape}")

        print("\nModel test passed!")
    else:
        print("\nInstall PyTorch to enable representation learning:")
        print("  pip install torch>=2.0.0")
