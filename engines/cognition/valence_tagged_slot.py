"""
Valence-Tagged Slots - Phase 10: Knowledge with Inherent Urgency

The core insight from phenomenology:
> "Pain doesn't represent tissue damage then feel bad. Pain IS the
>  representation of tissue damage in a format that includes 'STOP
>  DOING THIS' as part of the encoding."

This module implements ValenceTaggedSlot where urgency and importance
are PART of the encoding, not metadata looked up separately.

Benefits:
1. O(1) urgency access - no computation needed
2. Context-appropriate urgency - same fact can have different urgency
   in different contexts because the ENCODING varies
3. Faster Eisenhower decisions - read urgency from slot directly
4. Matches biology - this is how pain/pleasure actually work

Example:
    # Old way: Data + separate urgency lookup
    blackboard.write('object_moving', True)
    # Later: compute if this is urgent based on context

    # New way: Valence is part of the encoding
    blackboard.write_with_valence('object_moving', True,
                                   valence=Valence.THREAT,
                                   urgency=0.9, importance=0.8)
    # No lookup needed - the knowledge carries its urgency
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar

# Import Valence from phenomenology layer
from engines.cognition.phenomenology_layer import Valence

logger = logging.getLogger(__name__)

T = TypeVar('T')


# =============================================================================
# VALENCE-TAGGED SLOT
# =============================================================================

@dataclass
class ValenceTaggedValue(Generic[T]):
    """
    A value with inherent urgency and importance.

    This is the core concept: the representation INCLUDES urgency,
    not as metadata but as part of the encoding itself.

    Like pain encoding "STOP" in the representation - the urgency
    IS the format, not something added after.
    """
    value: T
    valence: Valence
    urgency_inherent: float       # 0-1: urgency baked into the data
    importance_inherent: float    # 0-1: importance baked into the data

    # Context for why this urgency was assigned
    urgency_reason: Optional[str] = None
    importance_reason: Optional[str] = None

    # Source tracking
    source_rung: Optional[str] = None
    timestamp: Optional[datetime] = None

    def get_with_context(self) -> Tuple[T, Valence, float, float]:
        """Return value with its inherent urgency/importance."""
        return (self.value, self.valence, self.urgency_inherent, self.importance_inherent)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for database storage."""
        return {
            'value': self.value,
            'valence': self.valence.value,
            'urgency_inherent': self.urgency_inherent,
            'importance_inherent': self.importance_inherent,
            'urgency_reason': self.urgency_reason,
            'importance_reason': self.importance_reason,
            'source_rung': self.source_rung,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValenceTaggedValue':
        """Deserialize from dictionary."""
        return cls(
            value=data['value'],
            valence=Valence(data['valence']),
            urgency_inherent=data['urgency_inherent'],
            importance_inherent=data['importance_inherent'],
            urgency_reason=data.get('urgency_reason'),
            importance_reason=data.get('importance_reason'),
            source_rung=data.get('source_rung'),
            timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else None,
        )


# =============================================================================
# VALENCE CONTEXT - Pre-defined Urgency/Importance Mappings
# =============================================================================

@dataclass
class ValenceContext:
    """
    Pre-defined mapping from condition to urgency/importance.

    Used by rungs to consistently tag values with appropriate
    urgency based on the situation.
    """
    valence: Valence
    urgency: float
    importance: float
    reason: str

    @staticmethod
    def threat_critical() -> 'ValenceContext':
        """Critical threat - highest urgency and importance."""
        return ValenceContext(
            valence=Valence.THREAT,
            urgency=1.0,
            importance=1.0,
            reason="Critical threat requiring immediate action"
        )

    @staticmethod
    def threat_warning() -> 'ValenceContext':
        """Warning-level threat - high urgency, moderate importance."""
        return ValenceContext(
            valence=Valence.THREAT,
            urgency=0.8,
            importance=0.7,
            reason="Warning condition that needs attention"
        )

    @staticmethod
    def opportunity_immediate() -> 'ValenceContext':
        """Time-sensitive opportunity - high urgency."""
        return ValenceContext(
            valence=Valence.OPPORTUNITY,
            urgency=0.7,
            importance=0.8,
            reason="Opportunity that may disappear"
        )

    @staticmethod
    def opportunity_strategic() -> 'ValenceContext':
        """Strategic opportunity - important but not urgent."""
        return ValenceContext(
            valence=Valence.OPPORTUNITY,
            urgency=0.3,
            importance=0.8,
            reason="Strategic opportunity worth pursuing"
        )

    @staticmethod
    def stability_confirmed() -> 'ValenceContext':
        """Confirmed stable state - low urgency/importance."""
        return ValenceContext(
            valence=Valence.STABILITY,
            urgency=0.2,
            importance=0.4,
            reason="Stable confirmed state"
        )

    @staticmethod
    def confusion_blocking() -> 'ValenceContext':
        """Confusion that's blocking progress - urgent to resolve."""
        return ValenceContext(
            valence=Valence.CONFUSION,
            urgency=0.7,
            importance=0.8,
            reason="Confusion blocking progress"
        )

    @staticmethod
    def confusion_exploratory() -> 'ValenceContext':
        """Exploratory confusion - not urgent but important to resolve."""
        return ValenceContext(
            valence=Valence.CONFUSION,
            urgency=0.3,
            importance=0.6,
            reason="Exploratory uncertainty worth investigating"
        )

    @staticmethod
    def boredom_stagnation() -> 'ValenceContext':
        """Boredom from stagnation - needs novelty."""
        return ValenceContext(
            valence=Valence.BOREDOM,
            urgency=0.4,
            importance=0.5,
            reason="Stagnation requiring novelty injection"
        )


# =============================================================================
# CRITICAL SLOT DEFINITIONS
# =============================================================================

# Pre-defined urgency mappings for critical slots
# These define how different values of critical slots should be tagged

CRITICAL_SLOT_VALENCE_RULES: Dict[str, Dict[Any, ValenceContext]] = {
    # Threat indicators
    'contradiction_detected': {
        True: ValenceContext.threat_critical(),
        False: ValenceContext.stability_confirmed(),
    },
    'cascade_failure': {
        True: ValenceContext.threat_critical(),
        False: ValenceContext.stability_confirmed(),
    },
    'action_budget_critical': {
        True: ValenceContext.threat_warning(),
        False: ValenceContext.stability_confirmed(),
    },

    # Movement and change
    'object_moving': {
        True: ValenceContext(
            valence=Valence.THREAT,
            urgency=0.7,
            importance=0.6,
            reason="Moving object requires tracking"
        ),
        False: ValenceContext.stability_confirmed(),
    },
    'frame_changed': {
        True: ValenceContext(
            valence=Valence.OPPORTUNITY,
            urgency=0.5,
            importance=0.5,
            reason="Frame change may indicate progress"
        ),
        False: ValenceContext(
            valence=Valence.BOREDOM,
            urgency=0.3,
            importance=0.4,
            reason="No change detected"
        ),
    },

    # Stuck detection
    'stuck_detected': {
        True: ValenceContext.confusion_blocking(),
        False: ValenceContext.stability_confirmed(),
    },

    # Control and agency
    'controlled_object': {
        # Non-None means we know what we control
        '__has_value__': ValenceContext(
            valence=Valence.STABILITY,
            urgency=0.3,
            importance=0.7,
            reason="Control identified - agency established"
        ),
        None: ValenceContext.confusion_blocking(),
    },

    # Theory validation
    'working_theory': {
        '__has_value__': ValenceContext(
            valence=Valence.OPPORTUNITY,
            urgency=0.4,
            importance=0.8,
            reason="Working theory guides strategy"
        ),
        None: ValenceContext.confusion_exploratory(),
    },

    # Pattern discovery
    'pattern_break': {
        True: ValenceContext(
            valence=Valence.CONFUSION,
            urgency=0.6,
            importance=0.7,
            reason="Pattern violation needs investigation"
        ),
        False: ValenceContext.stability_confirmed(),
    },

    # Level/game progress
    'level_completed': {
        True: ValenceContext(
            valence=Valence.OPPORTUNITY,
            urgency=0.2,
            importance=0.9,
            reason="Level complete - major milestone"
        ),
        False: ValenceContext.stability_confirmed(),
    },
}


def get_valence_for_slot(slot_name: str, value: Any) -> Optional[ValenceContext]:
    """
    Get the appropriate ValenceContext for a slot value.

    Args:
        slot_name: Name of the slot
        value: Value being written

    Returns:
        ValenceContext if slot is in critical rules, None otherwise
    """
    if slot_name not in CRITICAL_SLOT_VALENCE_RULES:
        return None

    rules = CRITICAL_SLOT_VALENCE_RULES[slot_name]

    # Check for exact match first
    if value in rules:
        return rules[value]

    # Check for __has_value__ rule (any non-None value)
    if value is not None and '__has_value__' in rules:
        return rules['__has_value__']

    # Check for None explicitly
    if value is None and None in rules:
        return rules[None]

    return None


# =============================================================================
# VALENCE SLOT STORE
# =============================================================================

class ValenceSlotStore:
    """
    Storage for valence-tagged slots.

    This is a companion to the main Blackboard that stores the
    valence-tagged versions of values. It can be used alongside
    the regular slots for backward compatibility.
    """

    def __init__(self):
        self._tagged_values: Dict[str, ValenceTaggedValue] = {}
        self._stats = {
            'writes': 0,
            'reads': 0,
            'auto_tagged': 0,
            'manual_tagged': 0,
        }

    def write(
        self,
        slot_name: str,
        value: Any,
        valence: Optional[Valence] = None,
        urgency: Optional[float] = None,
        importance: Optional[float] = None,
        reason: Optional[str] = None,
        source_rung: Optional[str] = None,
    ) -> ValenceTaggedValue:
        """
        Write a valence-tagged value.

        If valence/urgency/importance not provided, attempts to auto-tag
        based on CRITICAL_SLOT_VALENCE_RULES.

        Args:
            slot_name: Name of the slot
            value: Value to store
            valence: Optional explicit valence
            urgency: Optional explicit urgency (0-1)
            importance: Optional explicit importance (0-1)
            reason: Optional reason for this urgency
            source_rung: Rung that wrote this value

        Returns:
            The created ValenceTaggedValue
        """
        self._stats['writes'] += 1

        # Try auto-tagging if explicit values not provided
        if valence is None or urgency is None or importance is None:
            context = get_valence_for_slot(slot_name, value)
            if context:
                valence = valence or context.valence
                urgency = urgency if urgency is not None else context.urgency
                importance = importance if importance is not None else context.importance
                reason = reason or context.reason
                self._stats['auto_tagged'] += 1
            else:
                # Default to neutral if no rule exists
                valence = valence or Valence.STABILITY
                urgency = urgency if urgency is not None else 0.5
                importance = importance if importance is not None else 0.5
                self._stats['manual_tagged'] += 1
        else:
            self._stats['manual_tagged'] += 1

        tagged = ValenceTaggedValue(
            value=value,
            valence=valence,
            urgency_inherent=urgency,
            importance_inherent=importance,
            urgency_reason=reason,
            importance_reason=reason,
            source_rung=source_rung,
            timestamp=datetime.now(),
        )

        self._tagged_values[slot_name] = tagged

        logger.debug(
            "[VALENCE] Wrote %s = %s (valence=%s, urgency=%.2f, importance=%.2f)",
            slot_name, value, valence.value, urgency, importance
        )

        return tagged

    def read(self, slot_name: str) -> Optional[ValenceTaggedValue]:
        """Read a valence-tagged value."""
        self._stats['reads'] += 1
        return self._tagged_values.get(slot_name)

    def read_urgency(self, slot_name: str) -> float:
        """
        Read just the urgency for a slot - O(1) access.

        This is the key benefit: no computation needed,
        urgency is part of the stored encoding.

        Args:
            slot_name: Name of the slot

        Returns:
            Urgency value (0-1), or 0.5 if slot not found
        """
        tagged = self._tagged_values.get(slot_name)
        if tagged:
            return tagged.urgency_inherent
        return 0.5  # Default neutral

    def read_importance(self, slot_name: str) -> float:
        """
        Read just the importance for a slot - O(1) access.

        Args:
            slot_name: Name of the slot

        Returns:
            Importance value (0-1), or 0.5 if slot not found
        """
        tagged = self._tagged_values.get(slot_name)
        if tagged:
            return tagged.importance_inherent
        return 0.5  # Default neutral

    def read_valence(self, slot_name: str) -> Optional[Valence]:
        """
        Read just the valence for a slot.

        Args:
            slot_name: Name of the slot

        Returns:
            Valence enum value, or None if slot not found
        """
        tagged = self._tagged_values.get(slot_name)
        if tagged:
            return tagged.valence
        return None

    def get_slots_by_valence(self, valence: Valence) -> List[str]:
        """Get all slot names with a specific valence."""
        return [
            name for name, tagged in self._tagged_values.items()
            if tagged.valence == valence
        ]

    def get_urgent_slots(self, threshold: float = 0.6) -> List[Tuple[str, float]]:
        """
        Get all slots with urgency above threshold.

        Args:
            threshold: Minimum urgency to include

        Returns:
            List of (slot_name, urgency) tuples, sorted by urgency descending
        """
        urgent = [
            (name, tagged.urgency_inherent)
            for name, tagged in self._tagged_values.items()
            if tagged.urgency_inherent >= threshold
        ]
        return sorted(urgent, key=lambda x: x[1], reverse=True)

    def get_important_slots(self, threshold: float = 0.6) -> List[Tuple[str, float]]:
        """
        Get all slots with importance above threshold.

        Args:
            threshold: Minimum importance to include

        Returns:
            List of (slot_name, importance) tuples, sorted by importance descending
        """
        important = [
            (name, tagged.importance_inherent)
            for name, tagged in self._tagged_values.items()
            if tagged.importance_inherent >= threshold
        ]
        return sorted(important, key=lambda x: x[1], reverse=True)

    def get_threat_slots(self) -> List[str]:
        """Get all slots currently tagged with THREAT valence."""
        return self.get_slots_by_valence(Valence.THREAT)

    def compute_aggregate_urgency(self) -> float:
        """
        Compute aggregate urgency across all valence-tagged slots.

        Uses max of all urgencies, not average, because a single
        high-urgency item should drive urgency.

        Returns:
            Maximum urgency across all slots, or 0.0 if no slots
        """
        if not self._tagged_values:
            return 0.0
        return max(tv.urgency_inherent for tv in self._tagged_values.values())

    def compute_aggregate_importance(self) -> float:
        """
        Compute aggregate importance across all valence-tagged slots.

        Uses weighted average where higher-urgency items contribute more.

        Returns:
            Weighted average importance, or 0.0 if no slots
        """
        if not self._tagged_values:
            return 0.0

        total_weight = 0.0
        weighted_sum = 0.0

        for tv in self._tagged_values.values():
            weight = 1.0 + tv.urgency_inherent  # Urgent items weight more
            weighted_sum += tv.importance_inherent * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def clear(self) -> None:
        """Clear all valence-tagged values."""
        self._tagged_values.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about valence slot usage."""
        valence_counts = {}
        for v in Valence:
            valence_counts[v.value] = len(self.get_slots_by_valence(v))

        return {
            'total_slots': len(self._tagged_values),
            'writes': self._stats['writes'],
            'reads': self._stats['reads'],
            'auto_tagged': self._stats['auto_tagged'],
            'manual_tagged': self._stats['manual_tagged'],
            'valence_distribution': valence_counts,
            'aggregate_urgency': self.compute_aggregate_urgency(),
            'aggregate_importance': self.compute_aggregate_importance(),
            'threat_count': len(self.get_threat_slots()),
        }

    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """Serialize all tagged values for persistence."""
        return {
            name: tagged.to_dict()
            for name, tagged in self._tagged_values.items()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Dict[str, Any]]) -> 'ValenceSlotStore':
        """Deserialize from dictionary."""
        store = cls()
        for name, tagged_dict in data.items():
            store._tagged_values[name] = ValenceTaggedValue.from_dict(tagged_dict)
        return store


# =============================================================================
# HELPER FUNCTIONS FOR RUNG INTEGRATION
# =============================================================================

def tag_discovery(
    value: Any,
    is_novel: bool = False,
    is_confirming: bool = False,
    is_contradicting: bool = False,
    blocking_progress: bool = False,
) -> Tuple[Valence, float, float, str]:
    """
    Helper to determine valence/urgency for a discovery.

    Used by rungs when they discover something new.

    Args:
        value: The discovered value
        is_novel: Is this a new type of thing we haven't seen?
        is_confirming: Does this confirm our working theory?
        is_contradicting: Does this contradict our working theory?
        blocking_progress: Is understanding this blocking progress?

    Returns:
        (valence, urgency, importance, reason) tuple
    """
    if is_contradicting:
        return (
            Valence.CONFUSION,
            0.8 if blocking_progress else 0.5,
            0.9,
            "Contradicts working theory"
        )

    if is_confirming:
        return (
            Valence.STABILITY,
            0.3,
            0.6,
            "Confirms working theory"
        )

    if is_novel:
        return (
            Valence.OPPORTUNITY if not blocking_progress else Valence.CONFUSION,
            0.6 if blocking_progress else 0.4,
            0.7,
            "Novel discovery"
        )

    # Default: neutral
    return (Valence.STABILITY, 0.4, 0.5, "Standard observation")


def tag_action_result(
    success: bool,
    expected: bool = True,
    resource_cost: float = 0.1,
) -> Tuple[Valence, float, float, str]:
    """
    Helper to determine valence/urgency for an action result.

    Used after executing an action.

    Args:
        success: Did the action succeed?
        expected: Was this outcome expected?
        resource_cost: How much of action budget was used (0-1)

    Returns:
        (valence, urgency, importance, reason) tuple
    """
    if success and expected:
        return (Valence.STABILITY, 0.2, 0.5, "Expected success")

    if success and not expected:
        return (Valence.OPPORTUNITY, 0.6, 0.8, "Unexpected success - investigate")

    if not success and expected:
        return (Valence.CONFUSION, 0.5, 0.6, "Expected failure")

    # Unexpected failure
    urgency = 0.7 + (resource_cost * 0.3)  # More urgent if costly
    return (Valence.THREAT, urgency, 0.8, "Unexpected failure - danger")
