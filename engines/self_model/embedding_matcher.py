"""
Embedding Matcher - Neural Similarity for Action Suggestions

Finds similar past situations using frame embeddings and returns
what action worked best. Enables implicit generalization through
learned representations that capture structural similarity.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from database_interface import DatabaseInterface
    from representation_learner import RepresentationLearner

logger = logging.getLogger(__name__)


class EmbeddingMatcher:
    """
    Provides action suggestions based on learned frame embeddings.

    Uses a RepresentationLearner to find similar past situations
    and aggregates action suggestions from those situations.
    """

    def __init__(
        self,
        db: "DatabaseInterface",
        rep_learner: Optional["RepresentationLearner"] = None
    ):
        """
        Initialize embedding matcher.

        Args:
            db: Database interface for queries
            rep_learner: Optional RepresentationLearner instance for embeddings
        """
        self.db = db
        self.rep_learner = rep_learner

    def set_representation_learner(self, rep_learner: "RepresentationLearner") -> None:
        """Set or update the representation learner."""
        self.rep_learner = rep_learner

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
            # Find similar past situations
            similar = self.rep_learner.find_similar_situations(
                current_frame,
                game_type=game_type,
                level=level,
                top_k=top_k
            )

            if not similar:
                return None

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
                'similar_situations': similar[:3]  # Return top 3 for debugging
            }

        except Exception as e:
            logger.debug(f"[REP_LEARNER] Error getting suggestion: {e}")
            return None

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
            metadata: Optional additional metadata

        Returns:
            True if stored successfully
        """
        if self.rep_learner is None:
            return False

        try:
            self.rep_learner.store_frame(
                frame,
                game_type=game_type,
                level=level,
                action_taken=action_taken,
                score_delta=score_delta,
                metadata=metadata
            )
            return True
        except Exception as e:
            logger.debug(f"[EMBEDDING] Error storing frame: {e}")
            return False
