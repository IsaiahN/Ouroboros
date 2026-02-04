"""
Blackboard Phase 1 Tests

Tests for the Blackboard architecture including:
- TypedSlot get/set operations
- Checkpoint/restore functionality
- RumsfeldAssessment computation
- Legacy context compatibility
- Slot registry integration
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

from datetime import datetime
from typing import Any, Dict

import pytest

# Import blackboard components
from engines.cognition.blackboard import (
    Blackboard,
    EdgeType,
    KnownFact,
    Question,
    RoutingPriority,
    RumsfeldAssessment,
    RumsfeldQuadrant,
    SlotCategory,
    SlotMetadata,
    SlotState,
    TypedSlot,
)
from engines.cognition.slot_registry import (
    SLOT_DEFINITIONS,
    get_slot_category,
    get_slots_by_category,
    validate_slot_definition_coverage,
)

# =============================================================================
# TYPED SLOT TESTS
# =============================================================================

class TestTypedSlot:
    """Tests for TypedSlot functionality."""

    def test_slot_creation(self):
        """Test creating a typed slot."""
        slot = TypedSlot(
            name="test_slot",
            category=SlotCategory.ORIENTATION
        )
        assert slot.name == "test_slot"
        assert slot.category == SlotCategory.ORIENTATION
        assert slot.state == SlotState.EMPTY
        assert slot.value is None

    def test_slot_set_value(self):
        """Test setting a value on a slot."""
        slot = TypedSlot(name="grid_size", category=SlotCategory.ORIENTATION)

        slot.set_value(value=10, source_rung="survey", confidence=0.95)

        assert slot.value == 10
        assert slot.state == SlotState.POPULATED
        assert slot.metadata.confidence == 0.95
        assert slot.metadata.source_rung == "survey"

    def test_slot_get_value(self):
        """Test getting value from slot."""
        slot = TypedSlot(name="player_x", category=SlotCategory.IDENTITY)
        slot.set_value(42, source_rung="control_tracker")

        assert slot.get_value() == 42

    def test_slot_access_tracking(self):
        """Test that access count is tracked."""
        slot = TypedSlot(name="pattern", category=SlotCategory.HYPOTHESIS)
        slot.set_value("rotation", source_rung="pattern_detection")

        initial_count = slot.metadata.access_count
        slot.get_value()
        slot.get_value()

        assert slot.metadata.access_count == initial_count + 2

    def test_slot_source_primitive(self):
        """Test source primitive tracking on slot writes."""
        slot = TypedSlot(name="conclusion", category=SlotCategory.HYPOTHESIS)

        slot.set_value(
            value="grid_is_symmetric",
            source_rung="visual_analyzer",
            confidence=0.8,
            source_primitive="symmetry_detection"
        )

        assert slot.metadata.source_primitive == "symmetry_detection"


# =============================================================================
# BLACKBOARD TESTS
# =============================================================================

class TestBlackboard:
    """Tests for Blackboard functionality."""

    def test_blackboard_creation(self):
        """Test creating a blackboard."""
        bb = Blackboard()
        assert len(bb.slots) == 0
        assert len(bb) == 0

    def test_blackboard_with_registry(self):
        """Test creating blackboard with slot registry."""
        mini_registry = {
            "test_slot": {
                "category": SlotCategory.ORIENTATION,
                "expected_type": int,
                "description": "Test slot"
            }
        }

        bb = Blackboard(slot_registry=mini_registry)
        assert "test_slot" in bb.slots
        assert bb.slots["test_slot"].category == SlotCategory.ORIENTATION

    def test_slot_method_getter(self):
        """Test slot() method as getter."""
        bb = Blackboard()
        bb.slot("value", 42, source_rung="test")

        result = bb.slot("value")
        assert result == 42

    def test_slot_method_setter(self):
        """Test slot() method as setter."""
        bb = Blackboard()

        returned = bb.slot("pattern", "rotation", source_rung="pattern_rung", confidence=0.9)

        assert returned == "rotation"
        assert bb.slot("pattern") == "rotation"
        assert bb.slots["pattern"].metadata.confidence == 0.9

    def test_dict_like_access(self):
        """Test dict-like bracket access."""
        bb = Blackboard()

        bb["game_type"] = "puzzle"
        assert bb["game_type"] == "puzzle"

        assert bb.get("nonexistent", "default") == "default"

    def test_contains(self):
        """Test 'in' operator."""
        bb = Blackboard()
        bb.slot("present", True)

        assert "present" in bb
        assert "absent" not in bb

    def test_keys_items_values(self):
        """Test dict-like iteration methods."""
        bb = Blackboard()
        bb.slot("a", 1)
        bb.slot("b", 2)
        bb.slot("c", 3)

        assert set(bb.keys()) == {"a", "b", "c"}
        assert len(bb.items()) == 3
        assert set(bb.values()) == {1, 2, 3}

    def test_update(self):
        """Test bulk update from dict."""
        bb = Blackboard()
        bb.update({
            "x": 10,
            "y": 20,
            "z": 30
        }, source_rung="bulk_test")

        assert bb.slot("x") == 10
        assert bb.slot("y") == 20
        assert bb.slot("z") == 30

    def test_len(self):
        """Test length (populated slot count)."""
        bb = Blackboard()
        bb.slot("a", 1)
        bb.slot("b", 2)

        assert len(bb) == 2


# =============================================================================
# CHECKPOINT/RESTORE TESTS
# =============================================================================

class TestCheckpointRestore:
    """Tests for checkpoint/restore functionality."""

    def test_checkpoint_creation(self):
        """Test creating a checkpoint."""
        bb = Blackboard()
        bb.slot("value", 100)

        cp_id = bb.checkpoint()

        # Checkpoint ID is now a string (hash-based)
        assert isinstance(cp_id, str)
        assert len(cp_id) == 8  # 8-character hash
        assert len(bb._checkpoints) == 1

    def test_restore_from_checkpoint(self):
        """Test restoring from checkpoint."""
        bb = Blackboard()
        bb.slot("value", 100)

        cp_id = bb.checkpoint()

        # Modify after checkpoint
        bb.slot("value", 999)
        bb.slot("new_slot", "added")

        assert bb.slot("value") == 999

        # Restore using the string checkpoint ID
        success = bb.restore(cp_id)

        assert success
        # Value should be restored (as JSON string that gets deserialized)
        restored_value = bb.slot("value")
        assert restored_value == 100 or restored_value == "100"

    def test_restore_nonexistent_checkpoint(self):
        """Test restoring from invalid checkpoint ID."""
        bb = Blackboard()

        # Use a string ID that doesn't exist
        success = bb.restore("xxxxxxxx")

        assert not success

    def test_checkpoint_pruning(self):
        """Test that old checkpoints are pruned."""
        bb = Blackboard()
        bb.MAX_CHECKPOINTS = 5

        for i in range(10):
            bb.slot("counter", i)
            bb.checkpoint()

        # Should only keep last 5
        assert len(bb._checkpoints) <= 5

    def test_list_checkpoints(self):
        """Test listing available checkpoints."""
        bb = Blackboard()
        bb.slot("value", 1)

        bb.checkpoint()
        bb.checkpoint()

        cps = bb.list_checkpoints()

        assert len(cps) == 2
        # Each checkpoint is (string_id, datetime)
        for cp_id, timestamp in cps:
            assert isinstance(cp_id, str)  # Hash-based string ID
            assert isinstance(timestamp, datetime)


# =============================================================================
# RUMSFELD ASSESSMENT TESTS
# =============================================================================

class TestRumsfeldAssessment:
    """Tests for Rumsfeld epistemic state assessment."""

    def test_rumsfeld_counts_basic(self):
        """Test basic rumsfeld counting."""
        bb = Blackboard()

        # High confidence -> KK
        bb.slot("high_conf", "known", confidence=0.9)

        # Low confidence -> KU
        bb.slot("low_conf", "uncertain", confidence=0.4)

        counts = bb.get_rumsfeld_counts()

        assert counts["KK"] == 1
        assert counts["KU"] == 1

    def test_rumsfeld_assessment_full(self):
        """Test full rumsfeld assessment."""
        bb = Blackboard()

        # Add various slots
        bb.slot("certain", "yes", source_rung="rung1", confidence=0.95)
        bb.slot("uncertain", "maybe", source_rung="rung2", confidence=0.3)

        # Register UK need
        bb.register_uk_need("needed_slot", ["discovery_rung"])

        assessment = bb.rumsfeld_assessment()

        # Should have KK fact from certain slot
        assert len(assessment.known_knowns) >= 1
        # Should have KU question from uncertain slot
        assert len(assessment.known_unknowns) >= 1

    def test_uk_index_management(self):
        """Test UK index registration and clearing."""
        bb = Blackboard()

        # Register UK need
        bb.register_uk_need(
            "missing_data",
            potential_sources=["survey", "analysis"],
            questions_answerable=["q1", "q2"]
        )

        assert "missing_data" in bb._uk_index

        # Clear it
        bb.clear_uk_need("missing_data")

        assert "missing_data" not in bb._uk_index

    def test_assessment_routing_priority(self):
        """Test routing priority computation."""
        assessment = RumsfeldAssessment()
        assessment.kk_confidence = 0.9  # High KK confidence
        assessment.known_knowns = ["a", "b", "c", "d", "e"]

        priority = assessment.compute_routing_priority()

        # High KK confidence should give exploitation priority
        assert priority == RoutingPriority.EXPLOITATION_GREEDY

    def test_assessment_primary_quadrant(self):
        """Test primary quadrant detection."""
        assessment = RumsfeldAssessment()
        # Add many questions with high urgency
        for i in range(6):
            q = Question(
                question_id=f"q{i}",
                description=f"Question {i}",
                answerable_by=[],
                priority=0.8
            )
            assessment.add_question(q)

        assessment._recalculate_urgency()
        quadrant = assessment.compute_primary_quadrant()

        # High KU urgency with many questions
        assert quadrant == RumsfeldQuadrant.KU


# =============================================================================
# LEGACY CONTEXT TESTS
# =============================================================================

class TestLegacyContext:
    """Tests for legacy context dict compatibility."""

    def test_from_context(self):
        """Test creating blackboard from legacy context."""
        context = {
            "game_type": "puzzle",
            "level": 3,
            "score": 100,
            "player_position": (5, 10)
        }

        bb = Blackboard.from_context(context)

        assert bb.slot("game_type") == "puzzle"
        assert bb.slot("level") == 3
        assert bb.slot("score") == 100
        assert bb.slot("player_position") == (5, 10)

    def test_to_context(self):
        """Test exporting blackboard to legacy context."""
        bb = Blackboard()
        bb.slot("game_type", "action")
        bb.slot("level", 5)
        bb.slot("score", 250)

        context = bb.to_context()

        assert context["game_type"] == "action"
        assert context["level"] == 5
        assert context["score"] == 250

    def test_roundtrip(self):
        """Test roundtrip context -> blackboard -> context."""
        original = {
            "a": 1,
            "b": "two",
            "c": [1, 2, 3]
        }

        bb = Blackboard.from_context(original)
        exported = bb.to_context()

        assert exported["a"] == original["a"]
        assert exported["b"] == original["b"]
        assert exported["c"] == original["c"]


# =============================================================================
# SLOT REGISTRY TESTS
# =============================================================================

class TestSlotRegistry:
    """Tests for slot registry."""

    def test_registry_not_empty(self):
        """Test that registry has definitions."""
        assert len(SLOT_DEFINITIONS) > 0

    def test_all_categories_represented(self):
        """Test that all slot categories have definitions."""
        categories_found = set()

        for defn in SLOT_DEFINITIONS.values():
            cat = defn["category"]
            if isinstance(cat, SlotCategory):
                categories_found.add(cat)

        # Should have most categories
        assert len(categories_found) >= 5

    def test_get_slot_category(self):
        """Test category lookup function."""
        # Known slot
        cat = get_slot_category("survey")
        assert cat == SlotCategory.ORIENTATION

        # Unknown slot gets default
        cat = get_slot_category("unknown_slot_xyz")
        assert cat == SlotCategory.ORIENTATION

    def test_get_slots_by_category(self):
        """Test getting slots by category."""
        orientation_slots = get_slots_by_category(SlotCategory.ORIENTATION)

        assert len(orientation_slots) > 0
        assert "survey" in orientation_slots

    def test_validation_coverage(self):
        """Test slot definition coverage validation."""
        results = validate_slot_definition_coverage()

        assert results["total_slots"] > 50  # Should have many slots
        assert "by_category" in results
        assert "external_inputs" in results

        # External inputs should include history slots
        assert "game_type" in results["external_inputs"]


# =============================================================================
# EDGE TRUST TESTS
# =============================================================================

class TestEdgeTrust:
    """Tests for edge trust tracking."""

    def test_record_edge_traversal(self):
        """Test recording edge traversals."""
        bb = Blackboard()

        bb.record_edge_traversal(
            from_rung="survey",
            to_rung="primitive_suggester",
            edge_type=EdgeType.DEPENDENCY,
            success=True
        )

        trust = bb.get_edge_trust("survey", "primitive_suggester")

        # Success should increase trust (from default 0.5)
        assert trust >= 0.5

    def test_edge_trust_default(self):
        """Test default trust for unknown edges."""
        bb = Blackboard()

        trust = bb.get_edge_trust("unknown1", "unknown2")

        assert trust == 0.5  # Neutral default


# =============================================================================
# SUMMARY/DEBUG TESTS
# =============================================================================

class TestSummaryDebug:
    """Tests for debugging and introspection."""

    def test_summary(self):
        """Test blackboard summary."""
        bb = Blackboard()
        bb.slot("a", 1)
        bb.slot("b", 2)
        bb.checkpoint()

        summary = bb.summary()

        assert summary["populated_slots"] == 2
        assert summary["checkpoints"] == 1
        assert "rumsfeld_counts" in summary

    def test_repr(self):
        """Test string representation."""
        bb = Blackboard()
        bb.slot("test", 1)

        repr_str = repr(bb)

        assert "Blackboard" in repr_str
        assert "slots=" in repr_str


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests combining multiple features."""

    def test_full_workflow(self):
        """Test a full blackboard workflow."""
        # Create with a minimal registry
        mini_registry = {
            "game_type": {"category": SlotCategory.HISTORY, "expected_type": str},
            "level": {"category": SlotCategory.HISTORY, "expected_type": int},
        }
        bb = Blackboard(slot_registry=mini_registry)

        # Migrate from legacy context
        legacy = {"game_type": "puzzle", "level": 1}
        bb.update(legacy, source_rung="migration")

        # Create checkpoint before exploration
        cp = bb.checkpoint()

        # Add discoveries
        bb.slot("pattern_type", "rotation", source_rung="pattern_detection", confidence=0.85)
        bb.slot("goal_detected", True, source_rung="visual_analyzer", confidence=0.9)

        # Check rumsfeld state
        assessment = bb.rumsfeld_assessment()
        assert len(assessment.known_knowns) > 0 or assessment.kk_confidence > 0

        # Export for legacy code
        context = bb.to_context()
        assert "pattern_type" in context

        # Restore works
        assert bb.restore(cp)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
