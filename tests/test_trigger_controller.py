"""
Tests for TriggerController - feedback resonance prevention.

Part of the Societal Metrics System test suite.
"""

import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import json

import pytest

# Imports handled by conftest.py sys.path setup
from engines.regulation.trigger_controller import TriggerController


class MockDatabase:
    """Mock database for testing without real SQLite."""

    def __init__(self):
        self.tables = {}
        self.data = {}

    def execute_query(self, query, params=None):
        """Mock execute_query that handles basic operations."""
        query_lower = query.lower().strip()

        # Handle CREATE TABLE
        if query_lower.startswith('create table'):
            return None

        # Handle CREATE INDEX
        if query_lower.startswith('create index'):
            return None

        # Handle INSERT
        if query_lower.startswith('insert'):
            if 'trigger_history' not in self.data:
                self.data['trigger_history'] = []

            if params:
                record = {
                    'trigger_id': params[0],
                    'trigger_name': params[1],
                    'generation': params[2],
                    'metric_value': params[3],
                    'adjustment_magnitude': params[4],
                    'corroborating_metrics': params[5],
                    'was_damped': params[6],
                    'consecutive_fire_count': params[7]
                }
                self.data['trigger_history'].append(record)
            return None

        # Handle SELECT MAX(generation)
        if 'max(generation)' in query_lower and 'trigger_history' in query_lower:
            if not self.data.get('trigger_history'):
                return [{'last_gen': None}]

            trigger_name = params[0] if params else None
            matching = [r for r in self.data['trigger_history']
                       if r['trigger_name'] == trigger_name]

            if not matching:
                return [{'last_gen': None}]

            max_gen = max(r['generation'] for r in matching)
            return [{'last_gen': max_gen}]

        # Handle SELECT COUNT(*)
        if 'count(*)' in query_lower and 'trigger_history' in query_lower:
            if not self.data.get('trigger_history'):
                return [{'count': 0}]

            trigger_name = params[0] if params else None
            min_gen = params[1] if len(params) > 1 else 0

            matching = [r for r in self.data['trigger_history']
                       if r['trigger_name'] == trigger_name
                       and r['generation'] > min_gen]

            return [{'count': len(matching)}]

        # Handle SELECT * FROM trigger_history
        if 'select *' in query_lower and 'trigger_history' in query_lower:
            return self.data.get('trigger_history', [])

        return []


class TestTriggerControllerCooldown:
    """Tests for cooldown mechanism."""

    def test_first_fire_allowed(self):
        """First trigger fire should always be allowed."""
        db = MockDatabase()
        controller = TriggerController(db)

        assert controller.can_fire("test_trigger", 100) is True

    def test_immediate_refire_blocked(self):
        """Trigger should not fire again within cooldown period."""
        db = MockDatabase()
        controller = TriggerController(db)

        # First fire
        controller.record_fire("test_trigger", 100, 0.8, 0.1, ["metric_a"])

        # Immediate refire should be blocked
        assert controller.can_fire("test_trigger", 101) is False
        assert controller.can_fire("test_trigger", 102) is False

    def test_fire_after_cooldown_allowed(self):
        """Trigger should be allowed after cooldown period."""
        db = MockDatabase()
        controller = TriggerController(db)

        # First fire
        controller.record_fire("test_trigger", 100, 0.8, 0.1, ["metric_a"])

        # After cooldown (3 generations)
        assert controller.can_fire("test_trigger", 103) is True

    def test_different_triggers_independent(self):
        """Different trigger names should have independent cooldowns."""
        db = MockDatabase()
        controller = TriggerController(db)

        # Fire trigger A
        controller.record_fire("trigger_a", 100, 0.8, 0.1, [])

        # Trigger B should still be allowed
        assert controller.can_fire("trigger_b", 101) is True


class TestTriggerControllerDamping:
    """Tests for damping mechanism."""

    def test_first_fire_no_damping(self):
        """First fire should have no damping."""
        db = MockDatabase()
        controller = TriggerController(db)

        mag = controller.calculate_damped_magnitude("test", 0.08, 100)
        assert mag == 0.08  # No damping, under max

    def test_consecutive_fires_damped(self):
        """Consecutive fires should reduce magnitude."""
        db = MockDatabase()
        controller = TriggerController(db)

        # First fire
        mag1 = controller.calculate_damped_magnitude("test", 0.1, 100)
        controller.record_fire("test", 100, 0.8, mag1, [])

        # Second fire (after cooldown)
        mag2 = controller.calculate_damped_magnitude("test", 0.1, 104)

        assert mag2 < mag1
        # With damping factor 0.5, should be 0.1 * 0.5 = 0.05
        assert abs(mag2 - 0.05) < 0.01

    def test_max_adjustment_cap(self):
        """Adjustment should never exceed MAX_ADJUSTMENT."""
        db = MockDatabase()
        controller = TriggerController(db)

        # Request very high magnitude
        mag = controller.calculate_damped_magnitude("test", 0.5, 100)
        assert mag <= controller.MAX_ADJUSTMENT


class TestTriggerControllerCorroboration:
    """Tests for corroboration requirement."""

    def test_empty_secondary_allows_fire(self):
        """Empty secondary metrics should allow fire (with warning)."""
        db = MockDatabase()
        controller = TriggerController(db)

        # No secondary metrics
        assert controller.require_corroboration(0.8, []) is True

    def test_insufficient_corroboration_blocks(self):
        """Should block when not enough metrics agree."""
        db = MockDatabase()
        controller = TriggerController(db)

        # Only primary high, secondaries low
        assert controller.require_corroboration(0.8, [0.1, 0.2, 0.3]) is False

    def test_sufficient_corroboration_allows(self):
        """Should allow when enough metrics agree."""
        db = MockDatabase()
        controller = TriggerController(db)

        # Primary and 2+ secondaries high
        assert controller.require_corroboration(0.8, [0.6, 0.7, 0.3]) is True


class TestTriggerControllerFullWorkflow:
    """Tests for complete fire_with_safeguards workflow."""

    def test_fire_with_all_checks_passing(self):
        """Full fire should succeed when all checks pass."""
        db = MockDatabase()
        controller = TriggerController(db)

        applied = []

        result = controller.fire_with_safeguards(
            trigger_name="emergence_low",
            generation=100,
            primary_metric_value=0.3,
            secondary_metric_values={
                "velocity_low": 0.6,
                "diversity_low": 0.7
            },
            base_adjustment=0.15,
            apply_func=lambda adj: applied.append(adj)
        )

        assert result is not None
        assert len(applied) == 1
        assert applied[0] <= 0.10  # Respects MAX_ADJUSTMENT
        assert 'trigger_id' in result

    def test_fire_blocked_by_cooldown(self):
        """Fire should be blocked during cooldown."""
        db = MockDatabase()
        controller = TriggerController(db)

        # First fire
        controller.fire_with_safeguards(
            trigger_name="test",
            generation=100,
            primary_metric_value=0.3,
            secondary_metric_values={"m1": 0.6, "m2": 0.7},
            base_adjustment=0.1,
            apply_func=lambda adj: None
        )

        # Second fire during cooldown
        result = controller.fire_with_safeguards(
            trigger_name="test",
            generation=101,
            primary_metric_value=0.3,
            secondary_metric_values={"m1": 0.6, "m2": 0.7},
            base_adjustment=0.1,
            apply_func=lambda adj: None
        )

        assert result is None

    def test_fire_blocked_by_corroboration(self):
        """Fire should be blocked when corroboration fails."""
        db = MockDatabase()
        controller = TriggerController(db)

        result = controller.fire_with_safeguards(
            trigger_name="test",
            generation=100,
            primary_metric_value=0.3,
            secondary_metric_values={
                "m1": 0.1,  # Low - doesn't agree
                "m2": 0.2,  # Low - doesn't agree
                "m3": 0.1   # Low - doesn't agree
            },
            base_adjustment=0.1,
            apply_func=lambda adj: None
        )

        assert result is None


class TestTriggerControllerRecording:
    """Tests for trigger recording."""

    def test_record_creates_entry(self):
        """Recording should create database entry."""
        db = MockDatabase()
        controller = TriggerController(db)

        trigger_id = controller.record_fire(
            "test_trigger", 100, 0.8, 0.1, ["metric_a", "metric_b"]
        )

        assert trigger_id is not None
        assert trigger_id.startswith("trig_")
        assert len(db.data.get('trigger_history', [])) == 1

    def test_consecutive_count_increments(self):
        """Consecutive fire count should increment."""
        db = MockDatabase()
        controller = TriggerController(db)

        # First fire
        controller.record_fire("test", 100, 0.8, 0.1, [])

        # Second fire
        controller.record_fire("test", 104, 0.8, 0.05, [])

        records = db.data.get('trigger_history', [])
        assert len(records) == 2
        assert records[1]['consecutive_fire_count'] == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
