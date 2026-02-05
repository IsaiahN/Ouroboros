"""
Test suite for Phase 10: Valence-Tagged Slots.

Tests cover:
1. ValenceTaggedValue creation and serialization
2. ValenceSlotStore O(1) access patterns
3. Auto-tagging from CRITICAL_SLOT_VALENCE_RULES
4. Blackboard valence-aware methods
5. EisenhowerLayer integration with valence-tagged urgency/importance
6. Helper functions for rung integration
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

from typing import Any, Dict

import pytest

from engines.cognition.blackboard import Blackboard
from engines.cognition.phenomenology_layer import Valence

# Import the modules under test
from engines.cognition.valence_tagged_slot import (
    CRITICAL_SLOT_VALENCE_RULES,
    ValenceContext,
    ValenceSlotStore,
    ValenceTaggedValue,
    get_valence_for_slot,
    tag_action_result,
    tag_discovery,
)


class TestValenceTaggedValue:
    """Test ValenceTaggedValue dataclass."""

    def test_creation_with_all_fields(self):
        """ValenceTaggedValue can be created with all fields."""
        tagged = ValenceTaggedValue(
            value=True,
            valence=Valence.THREAT,
            urgency_inherent=0.9,
            importance_inherent=0.8,
            urgency_reason="Critical threat",
            importance_reason="Must address immediately",
            source_rung="survey",
        )

        assert tagged.value is True
        assert tagged.valence == Valence.THREAT
        assert tagged.urgency_inherent == 0.9
        assert tagged.importance_inherent == 0.8

    def test_get_with_context_returns_tuple(self):
        """get_with_context() returns (value, valence, urgency, importance)."""
        tagged = ValenceTaggedValue(
            value="test_value",
            valence=Valence.OPPORTUNITY,
            urgency_inherent=0.6,
            importance_inherent=0.7,
        )

        result = tagged.get_with_context()

        assert result == ("test_value", Valence.OPPORTUNITY, 0.6, 0.7)

    def test_to_dict_serialization(self):
        """ValenceTaggedValue can be serialized to dict."""
        tagged = ValenceTaggedValue(
            value=42,
            valence=Valence.STABILITY,
            urgency_inherent=0.3,
            importance_inherent=0.4,
            urgency_reason="Low urgency",
            source_rung="test_rung",
        )

        d = tagged.to_dict()

        assert d['value'] == 42
        assert d['valence'] == 'stability'
        assert d['urgency_inherent'] == 0.3
        assert d['importance_inherent'] == 0.4
        assert d['source_rung'] == 'test_rung'

    def test_from_dict_deserialization(self):
        """ValenceTaggedValue can be deserialized from dict."""
        d = {
            'value': "restored",
            'valence': 'confusion',
            'urgency_inherent': 0.5,
            'importance_inherent': 0.6,
            'urgency_reason': None,
            'importance_reason': None,
            'source_rung': None,
            'timestamp': None,
        }

        tagged = ValenceTaggedValue.from_dict(d)

        assert tagged.value == "restored"
        assert tagged.valence == Valence.CONFUSION
        assert tagged.urgency_inherent == 0.5


class TestValenceContext:
    """Test ValenceContext pre-defined mappings."""

    def test_threat_critical(self):
        """threat_critical() returns max urgency and importance."""
        ctx = ValenceContext.threat_critical()

        assert ctx.valence == Valence.THREAT
        assert ctx.urgency == 1.0
        assert ctx.importance == 1.0

    def test_opportunity_strategic(self):
        """opportunity_strategic() is important but not urgent."""
        ctx = ValenceContext.opportunity_strategic()

        assert ctx.valence == Valence.OPPORTUNITY
        assert ctx.urgency < 0.5  # Not urgent
        assert ctx.importance >= 0.7  # Important

    def test_confusion_blocking(self):
        """confusion_blocking() is urgent to resolve."""
        ctx = ValenceContext.confusion_blocking()

        assert ctx.valence == Valence.CONFUSION
        assert ctx.urgency >= 0.6  # Urgent
        assert ctx.importance >= 0.7  # Important


class TestCriticalSlotValenceRules:
    """Test CRITICAL_SLOT_VALENCE_RULES auto-tagging."""

    def test_contradiction_detected_true_is_threat(self):
        """contradiction_detected=True should be THREAT."""
        context = get_valence_for_slot('contradiction_detected', True)

        assert context is not None
        assert context.valence == Valence.THREAT
        assert context.urgency == 1.0

    def test_contradiction_detected_false_is_stability(self):
        """contradiction_detected=False should be STABILITY."""
        context = get_valence_for_slot('contradiction_detected', False)

        assert context is not None
        assert context.valence == Valence.STABILITY

    def test_object_moving_true_is_threat(self):
        """object_moving=True should be THREAT (needs tracking)."""
        context = get_valence_for_slot('object_moving', True)

        assert context is not None
        assert context.valence == Valence.THREAT

    def test_stuck_detected_is_confusion(self):
        """stuck_detected=True should be CONFUSION."""
        context = get_valence_for_slot('stuck_detected', True)

        assert context is not None
        assert context.valence == Valence.CONFUSION

    def test_has_value_rule_for_controlled_object(self):
        """controlled_object with any value should be STABILITY."""
        context = get_valence_for_slot('controlled_object', 'player')

        assert context is not None
        assert context.valence == Valence.STABILITY

    def test_none_value_for_controlled_object(self):
        """controlled_object=None should be CONFUSION."""
        context = get_valence_for_slot('controlled_object', None)

        assert context is not None
        assert context.valence == Valence.CONFUSION

    def test_unknown_slot_returns_none(self):
        """Unknown slot should return None."""
        context = get_valence_for_slot('random_unknown_slot', "value")

        assert context is None


class TestValenceSlotStore:
    """Test ValenceSlotStore O(1) access patterns."""

    @pytest.fixture
    def store(self):
        """Create empty ValenceSlotStore."""
        return ValenceSlotStore()

    def test_write_and_read(self, store):
        """Write and read a valence-tagged value."""
        store.write(
            'test_slot',
            value="test",
            valence=Valence.OPPORTUNITY,
            urgency=0.7,
            importance=0.8,
        )

        tagged = store.read('test_slot')

        assert tagged is not None
        assert tagged.value == "test"
        assert tagged.valence == Valence.OPPORTUNITY
        assert tagged.urgency_inherent == 0.7

    def test_read_urgency_o1_access(self, store):
        """read_urgency() is O(1) - direct access, no computation."""
        store.write('urgent_slot', True, urgency=0.9)

        # This should be instant - just dictionary lookup
        urgency = store.read_urgency('urgent_slot')

        assert urgency == 0.9

    def test_read_urgency_default_for_missing(self, store):
        """read_urgency() returns 0.5 for missing slots."""
        urgency = store.read_urgency('nonexistent')

        assert urgency == 0.5  # Neutral default

    def test_read_importance_o1_access(self, store):
        """read_importance() is O(1) - direct access."""
        store.write('important_slot', True, importance=0.85)

        importance = store.read_importance('important_slot')

        assert importance == 0.85

    def test_auto_tagging_from_rules(self, store):
        """Writing critical slot auto-tags based on rules."""
        # Write a critical slot without explicit valence
        store.write('contradiction_detected', True)

        tagged = store.read('contradiction_detected')

        assert tagged is not None
        assert tagged.valence == Valence.THREAT  # Auto-tagged
        assert tagged.urgency_inherent == 1.0    # From CRITICAL_SLOT_VALENCE_RULES

    def test_get_urgent_slots(self, store):
        """get_urgent_slots() returns slots above threshold."""
        store.write('low_urgency', True, urgency=0.3)
        store.write('medium_urgency', True, urgency=0.5)
        store.write('high_urgency', True, urgency=0.9)

        urgent = store.get_urgent_slots(threshold=0.6)

        assert len(urgent) == 1
        assert urgent[0][0] == 'high_urgency'
        assert urgent[0][1] == 0.9

    def test_get_threat_slots(self, store):
        """get_threat_slots() returns THREAT valence slots."""
        store.write('threat1', True, valence=Valence.THREAT)
        store.write('threat2', True, valence=Valence.THREAT)
        store.write('stable', True, valence=Valence.STABILITY)

        threats = store.get_threat_slots()

        assert len(threats) == 2
        assert 'threat1' in threats
        assert 'threat2' in threats
        assert 'stable' not in threats

    def test_compute_aggregate_urgency_uses_max(self, store):
        """aggregate_urgency uses max, not average."""
        store.write('slot1', True, urgency=0.3)
        store.write('slot2', True, urgency=0.9)  # Highest
        store.write('slot3', True, urgency=0.5)

        aggregate = store.compute_aggregate_urgency()

        assert aggregate == 0.9  # Max, not average

    def test_stats_tracking(self, store):
        """Stats track writes, reads, auto-tagging."""
        store.write('slot1', True, valence=Valence.STABILITY)  # Manual
        store.write('contradiction_detected', True)             # Auto-tagged
        store.read('slot1')
        store.read('contradiction_detected')

        stats = store.get_stats()

        assert stats['writes'] == 2
        assert stats['reads'] == 2
        assert stats['auto_tagged'] == 1
        assert stats['manual_tagged'] == 1


class TestBlackboardValenceIntegration:
    """Test Blackboard valence-aware methods."""

    @pytest.fixture
    def blackboard(self):
        """Create Blackboard instance."""
        return Blackboard()

    def test_write_with_valence_stores_both(self, blackboard):
        """write_with_valence() stores in both regular and valence store."""
        blackboard.write_with_valence(
            'test_slot',
            "test_value",
            valence=Valence.OPPORTUNITY,
            urgency=0.7,
            importance=0.8,
        )

        # Regular slot access
        assert blackboard.get('test_slot') == "test_value"

        # Valence-tagged access
        assert blackboard.get_urgency('test_slot') == 0.7
        assert blackboard.get_importance('test_slot') == 0.8

    def test_get_with_valence_returns_tuple(self, blackboard):
        """get_with_valence() returns (value, valence, urgency, importance)."""
        blackboard.write_with_valence(
            'tuple_test',
            42,
            valence=Valence.STABILITY,
            urgency=0.3,
            importance=0.4,
        )

        result = blackboard.get_with_valence('tuple_test')

        assert result == (42, Valence.STABILITY, 0.3, 0.4)

    def test_get_with_valence_missing_slot(self, blackboard):
        """get_with_valence() returns defaults for missing slots."""
        result = blackboard.get_with_valence('nonexistent')

        # (value, valence, urgency, importance)
        assert result[0] is None       # value
        assert result[1] is None       # valence
        assert result[2] == 0.5        # default urgency
        assert result[3] == 0.5        # default importance

    def test_auto_tagging_through_blackboard(self, blackboard):
        """Critical slots are auto-tagged when written through blackboard."""
        blackboard.write_with_valence('cascade_failure', True)

        valence = blackboard.get_valence('cascade_failure')
        urgency = blackboard.get_urgency('cascade_failure')

        assert valence == Valence.THREAT
        assert urgency == 1.0  # Critical threat

    def test_get_urgent_slots(self, blackboard):
        """get_urgent_slots() from blackboard."""
        blackboard.write_with_valence('low', True, urgency=0.2)
        blackboard.write_with_valence('high', True, urgency=0.9)

        urgent = blackboard.get_urgent_slots(threshold=0.5)

        assert len(urgent) == 1
        assert urgent[0][0] == 'high'

    def test_get_threat_slots(self, blackboard):
        """get_threat_slots() from blackboard."""
        blackboard.write_with_valence('threat', True, valence=Valence.THREAT)
        blackboard.write_with_valence('stable', True, valence=Valence.STABILITY)

        threats = blackboard.get_threat_slots()

        assert 'threat' in threats
        assert 'stable' not in threats

    def test_aggregate_urgency(self, blackboard):
        """get_aggregate_urgency() from blackboard."""
        blackboard.write_with_valence('slot1', True, urgency=0.3)
        blackboard.write_with_valence('slot2', True, urgency=0.8)

        aggregate = blackboard.get_aggregate_urgency()

        assert aggregate == 0.8  # Max

    def test_summary_includes_valence_stats(self, blackboard):
        """summary() includes valence store stats when initialized."""
        blackboard.write_with_valence('test', True, valence=Valence.OPPORTUNITY)

        summary = blackboard.summary()

        assert 'valence_store' in summary
        assert summary['valence_store']['total_slots'] == 1


class TestHelperFunctions:
    """Test helper functions for rung integration."""

    def test_tag_discovery_contradicting(self):
        """Contradicting discovery is CONFUSION with high importance."""
        valence, urgency, importance, reason = tag_discovery(
            value="contradiction",
            is_contradicting=True,
            blocking_progress=True,
        )

        assert valence == Valence.CONFUSION
        assert urgency >= 0.7  # High urgency when blocking
        assert importance >= 0.8

    def test_tag_discovery_confirming(self):
        """Confirming discovery is STABILITY."""
        valence, urgency, importance, reason = tag_discovery(
            value="confirmation",
            is_confirming=True,
        )

        assert valence == Valence.STABILITY
        assert urgency < 0.5  # Not urgent

    def test_tag_discovery_novel(self):
        """Novel discovery is OPPORTUNITY."""
        valence, urgency, importance, reason = tag_discovery(
            value="new_thing",
            is_novel=True,
        )

        assert valence == Valence.OPPORTUNITY

    def test_tag_action_result_unexpected_failure(self):
        """Unexpected failure is THREAT."""
        valence, urgency, importance, reason = tag_action_result(
            success=False,
            expected=False,
            resource_cost=0.5,
        )

        assert valence == Valence.THREAT
        assert urgency >= 0.7  # High urgency

    def test_tag_action_result_unexpected_success(self):
        """Unexpected success is OPPORTUNITY."""
        valence, urgency, importance, reason = tag_action_result(
            success=True,
            expected=False,
        )

        assert valence == Valence.OPPORTUNITY
        assert importance >= 0.7  # Worth investigating


class TestEisenhowerValenceIntegration:
    """Test EisenhowerLayer uses valence-tagged urgency/importance."""

    @pytest.fixture
    def blackboard_with_valence(self):
        """Create blackboard with high-urgency valence-tagged slot."""
        bb = Blackboard()
        # Write a critical threat that should boost urgency
        bb.write_with_valence(
            'contradiction_detected',
            True,
            # Will auto-tag with THREAT, urgency=1.0, importance=1.0
        )
        return bb

    def test_compute_urgency_uses_aggregate(self, blackboard_with_valence):
        """compute_urgency() incorporates aggregate_urgency from valence slots."""
        from engines.cognition.eisenhower_layer import EisenhowerLayer

        layer = EisenhowerLayer(blackboard_with_valence)
        urgency = layer.compute_urgency('test_rung')

        # With contradiction_detected=True (threat, urgency=1.0),
        # cascade_risk should be boosted
        assert urgency.cascade_risk >= 0.7  # Boosted by aggregate urgency

    def test_compute_importance_uses_aggregate(self, blackboard_with_valence):
        """compute_importance() incorporates aggregate_importance from valence slots."""
        from engines.cognition.eisenhower_layer import EisenhowerLayer

        layer = EisenhowerLayer(blackboard_with_valence)
        importance = layer.compute_importance('test_rung', edge_trust=0.5)

        # With high aggregate importance from threat slot,
        # win_probability_delta should be boosted
        assert importance.win_probability_delta >= 0.3  # Boosted


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
