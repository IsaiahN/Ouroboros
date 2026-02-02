"""
Embedding Matcher - Neural Similarity for Action Suggestions

Finds similar past situations using frame embeddings and returns
what action worked best. Enables implicit generalization through
learned representations that capture structural similarity.

RECENCY MODEL (as of 2026-02-01):
Uses generation-based time for relevance scoring. Recent embeddings
are weighted higher than old ones, with a 30-generation half-life.
Access frequency also boosts relevance (frequently-used = more useful).

Formula:
    relevance = similarity * ((1 - recency_weight) + recency_weight * decay * boost)

Where:
    - decay = 0.5 ^ (generations_elapsed / 30)
    - boost = 1 + 0.5 * (1 - e^(-access_count / 4.3))
    - recency_weight = 0.3 (similarity still dominates)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from database_interface import DatabaseInterface
    from representation_learner import RepresentationLearner

logger = logging.getLogger(__name__)

# Import generation clock utilities (graceful fallback if not available)
try:
    from engines.memory.generation_clock import (
        DECAY_CONFIG,
        GenerationClock,
        compute_relevance_score,
    )
    GENERATION_CLOCK_AVAILABLE = True
except ImportError:
    GENERATION_CLOCK_AVAILABLE = False
    logger.debug("[EMBEDDING] GenerationClock not available, using similarity-only ranking")


class EmbeddingMatcher:
    """
    Provides action suggestions based on learned frame embeddings.

    Uses a RepresentationLearner to find similar past situations
    and aggregates action suggestions from those situations.

    Recency weighting (if GenerationClock available):
    - Recent embeddings weighted higher than old ones
    - Frequently-accessed embeddings get boost
    - 30-generation half-life for decay
    """

    def __init__(
        self,
        db: "DatabaseInterface",
        rep_learner: Optional["RepresentationLearner"] = None,
        enable_recency: bool = True,
        recency_weight: float = 0.3
    ):
        """
        Initialize embedding matcher.

        Args:
            db: Database interface for queries
            rep_learner: Optional RepresentationLearner instance for embeddings
            enable_recency: Whether to apply generation-based recency weighting
            recency_weight: How much recency affects ranking (0=none, 1=fully)
        """
        self.db = db
        self.rep_learner = rep_learner
        self.enable_recency = enable_recency and GENERATION_CLOCK_AVAILABLE
        self.recency_weight = recency_weight

    def set_representation_learner(self, rep_learner: "RepresentationLearner") -> None:
        """Set or update the representation learner."""
        self.rep_learner = rep_learner

    def _get_current_generation(self) -> int:
        """Get current generation from clock, or 0 if unavailable."""
        if not GENERATION_CLOCK_AVAILABLE:
            return 0
        try:
            return GenerationClock.instance().generation
        except Exception:
            return 0

    def _compute_adjusted_similarity(
        self,
        base_similarity: float,
        created_generation: int,
        access_count: int,
        current_generation: int
    ) -> float:
        """
        Compute relevance-adjusted similarity score.

        Applies generation-based decay and access boost to raw similarity.
        """
        if not self.enable_recency or not GENERATION_CLOCK_AVAILABLE:
            return base_similarity

        generations_elapsed = max(0, current_generation - created_generation)

        return compute_relevance_score(
            base_similarity=base_similarity,
            generations_elapsed=generations_elapsed,
            access_count=access_count,
            half_life_generations=DECAY_CONFIG.EMBEDDING_HALF_LIFE,
            recency_weight=self.recency_weight
        )

    def _increment_access_count(self, trace_ids: List[int]) -> None:
        """Increment access count for retrieved embeddings."""
        if not trace_ids:
            return
        try:
            current_gen = self._get_current_generation()
            placeholders = ','.join('?' * len(trace_ids))
            self.db.execute_query(f"""
                UPDATE frame_embeddings
                SET access_count = COALESCE(access_count, 0) + 1,
                    last_accessed_generation = ?
                WHERE trace_id IN ({placeholders})
            """, (current_gen, *trace_ids))
        except Exception as e:
            logger.debug(f"[EMBEDDING] Failed to update access counts: {e}")

    def get_embedding_suggested_action(
        self,
        game_type: str,
        level: int,
        current_frame: List[List[int]],
        action_scores: Optional[Dict[int, float]] = None,
        top_k: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Get action suggestion based on learned frame embeddings.

        Finds similar past situations and returns what action worked best.
        This enables implicit generalization - the neural network learns
        representations that capture structural similarity, not just pixel matching.

        Recency weighting: Recent embeddings are weighted higher than old ones
        using generation-based decay (30-generation half-life).

        Args:
            game_type: Current game type
            level: Current level number
            current_frame: 64x64 grid
            action_scores: Optional dict of action_idx -> current score estimate
            top_k: Number of similar situations to consider

        Returns:
            Dict with 'suggested_action', 'confidence', 'similar_situations' if found,
            None if no suggestion available
        """
        if self.rep_learner is None:
            return None

        try:
            # Find similar past situations (get more candidates for recency filtering)
            candidates_k = top_k * 3 if self.enable_recency else top_k
            similar = self.rep_learner.find_similar_situations(
                current_frame,
                game_type=game_type,
                level=level,
                top_k=candidates_k
            )

            if not similar:
                return None

            # Apply recency weighting if enabled
            current_gen = self._get_current_generation()
            if self.enable_recency and current_gen > 0:
                # Get generation/access info for these embeddings
                trace_ids = [s.get('trace_id') for s in similar if s.get('trace_id')]
                gen_info = self._get_embedding_generation_info(trace_ids)

                # Adjust similarities based on recency
                for situation in similar:
                    trace_id = situation.get('trace_id')
                    if trace_id and trace_id in gen_info:
                        created_gen, access_count = gen_info[trace_id]
                        situation['raw_similarity'] = situation.get('similarity', 0.5)
                        situation['similarity'] = self._compute_adjusted_similarity(
                            base_similarity=situation['raw_similarity'],
                            created_generation=created_gen,
                            access_count=access_count,
                            current_generation=current_gen
                        )

                # Re-sort by adjusted similarity and take top_k
                similar.sort(key=lambda x: x.get('similarity', 0), reverse=True)
                similar = similar[:top_k]

                # Update access counts for retrieved embeddings
                used_trace_ids = [s.get('trace_id') for s in similar if s.get('trace_id')]
                self._increment_access_count(used_trace_ids)

            # Aggregate action suggestions from similar situations
            action_votes: Dict[int, float] = {}
            action_outcomes: Dict[int, List[float]] = {}

            for situation in similar:
                # Note: find_similar_situations returns 'action_taken' and 'score_delta'
                action_idx = situation.get('action_taken')
                score_change = situation.get('score_delta', 0)
                similarity = situation.get('similarity', 0.5)

                if action_idx is None:
                    continue

                # Weight by similarity and outcome
                weight = similarity * (1 + score_change * 0.5)  # Boost positive outcomes

                if action_idx not in action_votes:
                    action_votes[action_idx] = 0.0
                    action_outcomes[action_idx] = []

                action_votes[action_idx] += weight
                action_outcomes[action_idx].append(score_change)

            if not action_votes:
                return None

            # Find best action
            best_action = max(action_votes, key=lambda k: action_votes[k])
            total_votes = sum(action_votes.values())
            confidence = action_votes[best_action] / total_votes if total_votes > 0 else 0.0

            # Average outcome for the suggested action
            avg_outcome = (
                sum(action_outcomes[best_action]) / len(action_outcomes[best_action])
                if action_outcomes[best_action] else 0.0
            )

            return {
                'suggested_action': best_action,
                'confidence': confidence,
                'avg_outcome': avg_outcome,
                'similar_count': len(similar),
                'action_votes': action_votes,
                'similar_situations': similar[:3],  # Return top 3 for debugging
                'recency_enabled': self.enable_recency
            }

        except Exception as e:
            logger.debug(f"[REP_LEARNER] Error getting suggestion: {e}")
            return None

    def _get_embedding_generation_info(self, trace_ids: List[int]) -> Dict[int, tuple]:
        """
        Get generation and access info for embeddings.

        Returns:
            Dict mapping trace_id -> (created_generation, access_count)
        """
        if not trace_ids:
            return {}

        try:
            placeholders = ','.join('?' * len(trace_ids))
            rows = self.db.execute_query(f"""
                SELECT trace_id,
                       COALESCE(created_generation, 0) as created_generation,
                       COALESCE(access_count, 0) as access_count
                FROM frame_embeddings
                WHERE trace_id IN ({placeholders})
            """, tuple(trace_ids))

            return {
                row['trace_id']: (row['created_generation'], row['access_count'])
                for row in rows
            }
        except Exception as e:
            logger.debug(f"[EMBEDDING] Failed to get generation info: {e}")
            return {}

    def find_similar_situations(
        self,
        frame: List[List[int]],
        game_type: Optional[str] = None,
        level: Optional[int] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find similar past situations from the embedding store.

        Wrapper around rep_learner.find_similar_situations with
        additional error handling.

        Args:
            frame: Current frame (64x64 grid)
            game_type: Filter by game type (optional)
            level: Filter by level (optional)
            top_k: Number of similar situations to return

        Returns:
            List of similar situation dictionaries
        """
        if self.rep_learner is None:
            return []

        try:
            return self.rep_learner.find_similar_situations(
                frame,
                game_type=game_type,
                level=level,
                top_k=top_k
            ) or []
        except Exception as e:
            logger.debug(f"[EMBEDDING] Error finding similar: {e}")
            return []

    def store_frame_embedding(
        self,
        frame: List[List[int]],
        game_type: str,
        level: int,
        action_taken: int,
        score_delta: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store a frame embedding for future similarity lookups.

        Args:
            frame: Frame to store (64x64 grid)
            game_type: Game type identifier
            level: Level number
            action_taken: Action that was taken in this situation
            score_delta: Score change after action
            metadata: Optional additional metadata (will include created_generation)

        Returns:
            True if stored successfully
        """
        if self.rep_learner is None:
            return False

        try:
            # Add current generation to metadata for recency tracking
            enriched_metadata = dict(metadata) if metadata else {}
            enriched_metadata['created_generation'] = self._get_current_generation()

            self.rep_learner.store_frame(
                frame,
                game_type=game_type,
                level=level,
                action_taken=action_taken,
                score_delta=score_delta,
                metadata=enriched_metadata
            )
            return True
        except Exception as e:
            logger.debug(f"[EMBEDDING] Error storing frame: {e}")
            return False
