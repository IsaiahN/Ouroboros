"""
Few-Shot Relations - Control Bootstrapping from Sequence Abstraction

Exposes few-shot invariants/variants from sequence abstraction
for quick control relationship bootstrapping.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


class FewShotRelations:
    """
    Provides few-shot control relation bootstrapping.

    Uses sequence abstraction to identify control invariants
    (what always works) and variants (what changes) across
    a small number of examples.
    """

    def __init__(self, db: "DatabaseInterface", db_path: str = "core_data.db"):
        """
        Initialize few-shot relations.

        Args:
            db: Database interface
            db_path: Path to database (for abstraction engine)
        """
        self.db = db
        self.db_path = db_path
        self._abstraction_engine: Optional[Any] = None
        self._abstraction_unavailable = False

    def _get_abstraction_engine(self) -> Optional[Any]:
        """Lazy init abstraction engine; returns None if unavailable."""
        if self._abstraction_engine or self._abstraction_unavailable:
            return self._abstraction_engine
        try:
            from engines.planning.sequence_abstraction import SequenceAbstraction
            self._abstraction_engine = SequenceAbstraction(self.db_path)
            return self._abstraction_engine
        except Exception as exc:
            logger.debug(f"Abstraction engine unavailable: {exc}")
            self._abstraction_unavailable = True
            return None

    def get_few_shot_control_relations(
        self,
        game_id: str,
        level: int,
        min_confidence: float = 0.5,
    ) -> Optional[Dict[str, Any]]:
        """
        Expose few-shot invariants/variants from sequence abstraction.

        Returns None if insufficient data or low confidence.

        Args:
            game_id: Game identifier (may include instance suffix)
            level: Level number
            min_confidence: Minimum confidence threshold

        Returns:
            Dict with invariants, variants, and confidence if available
        """
        engine = self._get_abstraction_engine()
        if not engine:
            return None

        game_type = game_id.split('-')[0] if '-' in game_id else game_id
        relations = engine.get_few_shot_relations(game_type, level)

        if not relations or relations.get("confidence", 0.0) < min_confidence:
            return None
        return relations

    def get_action_invariants(
        self,
        game_id: str,
        level: int,
        action: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get invariant properties for a specific action.

        What ALWAYS happens when this action is taken?

        Args:
            game_id: Game identifier
            level: Level number
            action: Action to query (e.g., 'ACTION1')

        Returns:
            Dict with invariant properties or None
        """
        relations = self.get_few_shot_control_relations(game_id, level)
        if not relations:
            return None

        invariants = relations.get('invariants', {})
        return invariants.get(action)

    def get_action_variants(
        self,
        game_id: str,
        level: int,
        action: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get variant properties for a specific action.

        What CHANGES depending on context when this action is taken?

        Args:
            game_id: Game identifier
            level: Level number
            action: Action to query (e.g., 'ACTION1')

        Returns:
            Dict with variant properties or None
        """
        relations = self.get_few_shot_control_relations(game_id, level)
        if not relations:
            return None

        variants = relations.get('variants', {})
        return variants.get(action)
