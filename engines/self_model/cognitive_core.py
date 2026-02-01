"""
Cognitive Core - Unified cognitive interface for agents

The agent's core cognitive infrastructure, composing individual
engines to provide unified self-awareness capabilities.

Replaces the deprecated AgentSelfModel monolith (~10,000 lines) with
clean delegation to focused, testable engines:

- EmbeddingMatcher: get_embedding_suggested_action()
- FewShotRelations: get_few_shot_control_relations()
- NetworkSharingEngine: get_network_object_inventory(), share_control_discovery_to_network()
- ControlTracker: "I am this object" tracking

This is the canonical implementation of SelfModelInterface.
"""
import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from database_interface import DatabaseInterface
    from representation_learner import RepresentationLearner

logger = logging.getLogger(__name__)


class CognitiveCore:
    """
    Unified cognitive interface for agent self-awareness.

    Composes individual engines to provide the full SelfModelInterface
    expected by decision rungs. This is the agent's core cognitive
    infrastructure - knowing what it controls, what works, and what to try.
    """

    def __init__(
        self,
        db: "DatabaseInterface",
        rep_learner: Optional["RepresentationLearner"] = None
    ):
        """
        Initialize self-model facade.

        Args:
            db: Database interface
            rep_learner: Optional representation learner for embeddings
        """
        self.db = db
        self._rep_learner = rep_learner

        # Lazy-loaded component engines
        self._embedding_matcher = None
        self._few_shot_relations = None
        self._network_sharing = None
        self._control_tracker = None

        # Current prediction state (for metacognitive tracking)
        self._current_prediction: Optional[Dict[str, Any]] = None

    def _get_embedding_matcher(self):
        """Lazy load embedding matcher."""
        if self._embedding_matcher is None:
            try:
                from engines.self_model.embedding_matcher import EmbeddingMatcher
                self._embedding_matcher = EmbeddingMatcher(self.db, self._rep_learner)
            except ImportError:
                logger.debug("[FACADE] EmbeddingMatcher not available")
        return self._embedding_matcher

    def _get_few_shot_relations(self):
        """Lazy load few-shot relations."""
        if self._few_shot_relations is None:
            try:
                from engines.self_model.few_shot_relations import FewShotRelations
                self._few_shot_relations = FewShotRelations(self.db)
            except ImportError:
                logger.debug("[FACADE] FewShotRelations not available")
        return self._few_shot_relations

    def _get_network_sharing(self):
        """Lazy load network sharing engine."""
        if self._network_sharing is None:
            try:
                from engines.self_model.network_sharing import NetworkSharingEngine
                self._network_sharing = NetworkSharingEngine(self.db)
            except ImportError:
                logger.debug("[FACADE] NetworkSharingEngine not available")
        return self._network_sharing

    def _get_control_tracker(self):
        """Lazy load control tracker."""
        if self._control_tracker is None:
            try:
                from engines.self_model.control_tracker import ControlTracker
                self._control_tracker = ControlTracker(self.db)
            except ImportError:
                logger.debug("[FACADE] ControlTracker not available")
        return self._control_tracker

    # =========================================================================
    # SelfModelInterface Implementation
    # =========================================================================

    def get_embedding_suggested_action(
        self,
        game_type: Optional[str] = None,
        level: Optional[int] = None,
        current_frame: Optional[List[List[int]]] = None,
        action_scores: Optional[Dict[int, float]] = None,
        top_k: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Get action suggestion based on learned frame embeddings.

        Delegates to EmbeddingMatcher.
        """
        matcher = self._get_embedding_matcher()
        if matcher is None:
            return None

        try:
            return matcher.get_embedding_suggested_action(
                game_type=game_type or '',
                level=level or 1,
                current_frame=current_frame or [],
                action_scores=action_scores,
                top_k=top_k
            )
        except Exception as e:
            logger.debug(f"[FACADE] Embedding suggestion failed: {e}")
            return None

    def get_current_prediction(self) -> Optional[Dict[str, Any]]:
        """
        Get the current hypothesis being tested.

        Returns locally stored prediction state.
        """
        return self._current_prediction

    def set_current_prediction(self, prediction: Optional[Dict[str, Any]]) -> None:
        """Set the current prediction being tested."""
        self._current_prediction = prediction

    def get_few_shot_control_relations(
        self,
        game_id: str = '',
        level: int = 1,
        min_confidence: float = 0.5
    ) -> Optional[Dict[str, Any]]:
        """
        Get few-shot invariants/variants from sequence abstraction.

        Delegates to FewShotRelations.
        """
        relations = self._get_few_shot_relations()
        if relations is None:
            return None

        try:
            return relations.get_few_shot_control_relations(
                game_id=game_id,
                level=level,
                min_confidence=min_confidence
            )
        except Exception as e:
            logger.debug(f"[FACADE] Few-shot relations failed: {e}")
            return None

    def get_network_object_inventory(
        self,
        game_type: str,
        level: int
    ) -> Dict[str, Any]:
        """
        Query network knowledge about interactable objects.

        Delegates to NetworkSharingEngine.
        """
        sharing = self._get_network_sharing()
        if sharing is None:
            return {'total_unique': 0, 'interactable': []}

        try:
            if hasattr(sharing, 'get_network_object_inventory'):
                return sharing.get_network_object_inventory(game_type, level)
            return {'total_unique': 0, 'interactable': []}
        except Exception as e:
            logger.debug(f"[FACADE] Network inventory failed: {e}")
            return {'total_unique': 0, 'interactable': []}

    def share_control_discovery_to_network(
        self,
        agent_id: str,
        game_id: str,
        level: int,
        controlled_objects: List[str],
        action_response_map: Dict[str, List[str]],
        confidence: float,
        generation: int = 0
    ) -> Optional[str]:
        """
        Share "I am this object" discovery to network.

        Delegates to NetworkSharingEngine.
        """
        sharing = self._get_network_sharing()
        if sharing is None:
            return None

        try:
            if hasattr(sharing, 'share_control_discovery_to_network'):
                return sharing.share_control_discovery_to_network(
                    agent_id=agent_id,
                    game_id=game_id,
                    level=level,
                    controlled_objects=controlled_objects,
                    action_response_map=action_response_map,
                    confidence=confidence,
                    generation=generation
                )
            return None
        except Exception as e:
            logger.debug(f"[FACADE] Share discovery failed: {e}")
            return None

    # =========================================================================
    # Additional Methods for Compatibility
    # =========================================================================

    def reset(self, game_id: str = '') -> None:
        """Reset state for new game."""
        self._current_prediction = None
        # Reset component engines if they have reset methods
        tracker = self._get_control_tracker()
        if tracker and hasattr(tracker, 'reset'):
            tracker.reset()

    def record_movement_observation(
        self,
        game_id: str,
        level: int,
        action: str,
        objects_moved: List[Dict[str, Any]],
        frame_before: Optional[List[List[int]]] = None,
        frame_after: Optional[List[List[int]]] = None
    ) -> None:
        """
        Record an observation of object movement in response to action.

        Delegates to ControlTracker.
        """
        tracker = self._get_control_tracker()
        if tracker and hasattr(tracker, 'record_observation'):
            try:
                tracker.record_observation(
                    game_id=game_id,
                    level=level,
                    action=action,
                    objects_moved=objects_moved
                )
            except Exception as e:
                logger.debug(f"[FACADE] Record movement failed: {e}")
