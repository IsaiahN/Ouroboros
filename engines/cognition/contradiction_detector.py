"""
Contradiction Detector for Cognitive Routing.

This module detects contradictions between beliefs/facts and classifies them
as mild (KK->KU) or severe (KK->UU).

Phase 1.5.3 of cognitive_routing_implementation_plan.md

Contradiction severity levels:
- MILD (KK->KU): New evidence weakens confidence, specific question emerges
- SEVERE (KK->UU): New evidence completely invalidates previous belief

The detector tracks:
1. Contradicted facts (for exclusion lists)
2. Contradiction history (for penalty calculation)
3. Failed paths (for graph evolution negative reputation)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from engines.cognition.blackboard import KnownFact, RumsfeldQuadrant

logger = logging.getLogger(__name__)


# =============================================================================
# CONTRADICTION SEVERITY
# =============================================================================

class ContradictionSeverity(Enum):
    """Severity levels for contradictions."""
    NONE = "none"          # No contradiction
    MILD = "mild"          # Confidence weakened (KK->KU)
    SEVERE = "severe"      # Belief invalidated (KK->UU)
    CATASTROPHIC = "catastrophic"  # Multiple severe contradictions


# =============================================================================
# CONTRADICTION RECORD
# =============================================================================

@dataclass
class ContradictionRecord:
    """
    Record of a detected contradiction.

    This tracks what was contradicted, by what, and how severe it was.
    Used for:
    1. Deciding which quadrant to transition to
    2. Building exclusion lists for exploration
    3. Applying negative reputation to failed paths
    """
    # What was contradicted
    contradicted_slot: str
    old_value: Any
    old_confidence: float
    old_source_rung: str

    # What contradicted it
    new_value: Any
    new_confidence: float
    new_source_rung: str

    # Classification
    severity: ContradictionSeverity

    # Metadata
    detected_at: int  # Action number
    timestamp: datetime = field(default_factory=datetime.now)

    # Path that led to the contradiction (for negative reputation)
    path_to_contradiction: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"Contradiction({self.severity.name}: "
            f"{self.contradicted_slot}={self.old_value} vs {self.new_value})"
        )


# =============================================================================
# CONTRADICTION DETECTOR
# =============================================================================

class ContradictionDetector:
    """
    Detects and classifies contradictions between facts.

    A contradiction occurs when:
    1. A slot has a high-confidence value (KK)
    2. A new result provides a different value with reasonable confidence

    Severity classification:
    - MILD: Old confidence was high but new evidence weakens it
      - Example: control_object was "blue square" (0.85), now "red circle" (0.6)
      - Result: Transition to KU, ask "what do I control?"

    - SEVERE: New evidence completely invalidates the old belief
      - Example: physics_game was False (0.9), now True (0.95)
      - Result: Transition to UU, exclude failed path, start fresh

    Usage:
        detector = ContradictionDetector()

        # Check for contradiction
        contradiction = detector.check_contradiction(
            slot_name="control_object",
            old_fact=known_fact,
            new_value="red_circle",
            new_confidence=0.85,
            new_source_rung="control_tracker"
        )

        if contradiction:
            if contradiction.severity == ContradictionSeverity.SEVERE:
                # Transition to UU with exclusions
                excluded_rungs = detector.get_exclusion_list()
    """

    # Thresholds
    MILD_THRESHOLD = 0.3      # Confidence drop > this = mild contradiction
    SEVERE_THRESHOLD = 0.5    # Confidence in NEW value > this + old high = severe
    HIGH_CONFIDENCE = 0.7     # What counts as "high confidence" (KK)

    # Maximum contradictions before catastrophic
    CATASTROPHIC_THRESHOLD = 3

    def __init__(self):
        """Initialize the contradiction detector."""
        self.contradictions: List[ContradictionRecord] = []
        self.excluded_rungs: Set[str] = set()
        self.excluded_slots: Set[str] = set()
        self._contradiction_count_this_decision = 0

    def reset(self) -> None:
        """Reset for a new decision (keep history for game-level tracking)."""
        self._contradiction_count_this_decision = 0

    def full_reset(self) -> None:
        """Full reset for a new game."""
        self.contradictions.clear()
        self.excluded_rungs.clear()
        self.excluded_slots.clear()
        self._contradiction_count_this_decision = 0

    def check_contradiction(
        self,
        slot_name: str,
        old_fact: Optional[KnownFact],
        new_value: Any,
        new_confidence: float,
        new_source_rung: str,
        action_number: int = 0,
        path_so_far: Optional[List[str]] = None
    ) -> Optional[ContradictionRecord]:
        """
        Check if a new value contradicts an existing fact.

        Args:
            slot_name: The slot being updated
            old_fact: The existing KnownFact (if any)
            new_value: The new value being proposed
            new_confidence: Confidence in the new value
            new_source_rung: Rung providing the new value
            action_number: Current action number
            path_so_far: Rungs executed so far (for exclusion)

        Returns:
            ContradictionRecord if contradiction detected, None otherwise
        """
        # No contradiction if no old fact
        if old_fact is None:
            return None

        # No contradiction if values are the same
        if self._values_equal(old_fact.value, new_value):
            return None

        # No contradiction if old confidence was low (not really a "known known")
        if old_fact.confidence < self.HIGH_CONFIDENCE:
            return None

        # Determine severity
        severity = self._classify_severity(old_fact, new_confidence)

        if severity == ContradictionSeverity.NONE:
            return None

        # Create record
        record = ContradictionRecord(
            contradicted_slot=slot_name,
            old_value=old_fact.value,
            old_confidence=old_fact.confidence,
            old_source_rung=old_fact.source_rung,
            new_value=new_value,
            new_confidence=new_confidence,
            new_source_rung=new_source_rung,
            severity=severity,
            detected_at=action_number,
            path_to_contradiction=list(path_so_far) if path_so_far else []
        )

        # Track contradiction
        self.contradictions.append(record)
        self._contradiction_count_this_decision += 1

        # Update exclusions for severe contradictions
        if severity in (ContradictionSeverity.SEVERE, ContradictionSeverity.CATASTROPHIC):
            self._update_exclusions(record)

        logger.info(
            f"Contradiction detected: {record}"
        )

        return record

    def _values_equal(self, v1: Any, v2: Any) -> bool:
        """Check if two values are effectively equal."""
        # Handle None
        if v1 is None and v2 is None:
            return True
        if v1 is None or v2 is None:
            return False

        # Handle numeric comparison with tolerance
        if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
            return abs(v1 - v2) < 0.001

        # Handle list/set comparison
        if isinstance(v1, (list, set)) and isinstance(v2, (list, set)):
            return set(v1) == set(v2)

        # Default equality
        return v1 == v2

    def _classify_severity(
        self,
        old_fact: KnownFact,
        new_confidence: float
    ) -> ContradictionSeverity:
        """
        Classify contradiction severity.

        MILD: Old was confident, new is less confident
              -> We're uncertain now, need to investigate

        SEVERE: Both old and new are confident but disagree
               -> Previous belief was wrong, need fresh start
        """
        # Check for catastrophic (too many contradictions)
        if self._contradiction_count_this_decision >= self.CATASTROPHIC_THRESHOLD:
            return ContradictionSeverity.CATASTROPHIC

        # Both confident but different = SEVERE
        if old_fact.confidence > self.HIGH_CONFIDENCE and new_confidence > self.SEVERE_THRESHOLD:
            return ContradictionSeverity.SEVERE

        # Old confident, new less so = MILD
        confidence_drop = old_fact.confidence - new_confidence
        if confidence_drop > self.MILD_THRESHOLD:
            return ContradictionSeverity.MILD

        # New much more confident than old = SEVERE
        if new_confidence > old_fact.confidence + 0.2:
            return ContradictionSeverity.SEVERE

        return ContradictionSeverity.NONE

    def _update_exclusions(self, record: ContradictionRecord) -> None:
        """Update exclusion lists based on contradiction."""
        # Exclude the rung that produced the wrong value
        self.excluded_rungs.add(record.old_source_rung)

        # Exclude the contradicted slot from influencing decisions
        self.excluded_slots.add(record.contradicted_slot)

        # For severe contradictions, exclude the whole path
        if record.severity in (ContradictionSeverity.SEVERE, ContradictionSeverity.CATASTROPHIC):
            for rung in record.path_to_contradiction:
                self.excluded_rungs.add(rung)

    def get_exclusion_list(self) -> Set[str]:
        """Get the set of rungs to exclude from future exploration."""
        return self.excluded_rungs.copy()

    def get_excluded_slots(self) -> Set[str]:
        """Get the set of slots that have been contradicted."""
        return self.excluded_slots.copy()

    def get_target_quadrant(
        self,
        contradiction: ContradictionRecord
    ) -> RumsfeldQuadrant:
        """
        Determine which quadrant to transition to based on contradiction.

        MILD -> KU (we have a specific question to answer)
        SEVERE -> UU (we need to explore from scratch)
        CATASTROPHIC -> UU (definitely lost, explore with heavy exclusions)
        """
        if contradiction.severity == ContradictionSeverity.MILD:
            return RumsfeldQuadrant.KU
        else:
            return RumsfeldQuadrant.UU

    def is_catastrophic(self) -> bool:
        """Are we in a catastrophic contradiction state?"""
        return self._contradiction_count_this_decision >= self.CATASTROPHIC_THRESHOLD

    def get_contradiction_count(self) -> int:
        """Get number of contradictions this decision."""
        return self._contradiction_count_this_decision

    def get_failed_paths(self) -> List[List[str]]:
        """Get all paths that led to contradictions (for negative reputation)."""
        return [
            c.path_to_contradiction
            for c in self.contradictions
            if c.path_to_contradiction
        ]

    def __repr__(self) -> str:
        return (
            f"ContradictionDetector("
            f"contradictions={len(self.contradictions)}, "
            f"excluded_rungs={len(self.excluded_rungs)})"
        )
