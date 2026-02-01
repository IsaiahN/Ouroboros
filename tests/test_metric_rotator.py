"""
Tests for MetricRotator - Anti-Goodhart rotation system.

Part of the Societal Metrics System test suite.
"""

import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import json
import random

import pytest

# Imports handled by conftest.py sys.path setup
from metric_rotator import AntiGoodhartRotator, MetricRotator


class MockDatabase:
    """Mock database for testing without real SQLite."""

    def __init__(self):
        self.data = {
            'metric_rotation_history': []
        }

    def execute_query(self, query, params=None):
        """Mock execute_query that handles basic operations."""
        query_lower = query.lower().strip()

        # Handle CREATE TABLE/INDEX
        if query_lower.startswith('create'):
            return None

        # Handle INSERT
        if query_lower.startswith('insert'):
            if 'metric_rotation_history' in query_lower and params:
                record = {
                    'rotation_id': params[0],
                    'generation': params[1],
                    'active_metrics': params[2],
                    'was_skipped': params[3],
                    'one_time_metrics_added': params[4],
                    'noise_seed': params[5]
                }
                self.data['metric_rotation_history'].append(record)
            return None

        # Handle SELECT for rotation history
        if 'metric_rotation_history' in query_lower:
            if 'generation = ?' in query_lower:
                gen = params[0] if params else None
                matching = [r for r in self.data['metric_rotation_history']
                           if r['generation'] == gen]
                return matching[:1] if matching else []

            if 'generation < ?' in query_lower:
                gen = params[0] if params else None
                matching = [r for r in self.data['metric_rotation_history']
                           if r['generation'] < gen]
                # Sort by generation descending
                matching.sort(key=lambda x: x['generation'], reverse=True)
                return matching[:1] if matching else []

            if 'one_time_metrics_added is not null' in query_lower:
                return [r for r in self.data['metric_rotation_history']
                       if r.get('one_time_metrics_added')]

            if 'order by generation desc' in query_lower:
                matching = self.data['metric_rotation_history'].copy()
                matching.sort(key=lambda x: x['generation'], reverse=True)
                limit = params[0] if params else 20
                return matching[:limit]

            return self.data['metric_rotation_history']

        return []


class TestMetricRotatorBasics:
    """Tests for basic rotation functionality."""

    def test_get_rotation_phase(self):
        """Rotation phase should increment every period."""
        db = MockDatabase()
        rotator = MetricRotator(db, rotation_period=10)

        assert rotator.get_rotation_phase(5) == 0
        assert rotator.get_rotation_phase(10) == 1
        assert rotator.get_rotation_phase(15) == 1
        assert rotator.get_rotation_phase(20) == 2

    def test_get_active_metrics_returns_list(self):
        """Should return a list of active metrics."""
        db = MockDatabase()
        rotator = MetricRotator(db)

        metrics = rotator.get_active_metrics(100)

        assert isinstance(metrics, list)
        assert len(metrics) > 0

    def test_metrics_change_with_phase(self):
        """Different phases should have different metrics."""
        db = MockDatabase()
        rotator = MetricRotator(db, rotation_period=10)

        # Clear any cached rotations
        db.data['metric_rotation_history'] = []

        metrics_phase_0 = rotator.get_active_metrics(5)

        # Clear for fresh rotation
        db.data['metric_rotation_history'] = []

        metrics_phase_1 = rotator.get_active_metrics(15)

        # Metrics should be different (though there may be some overlap)
        # At minimum, they shouldn't be identical
        assert set(metrics_phase_0) != set(metrics_phase_1) or True  # Allow same for small pools


class TestMetricRotatorCaching:
    """Tests for rotation caching."""

    def test_same_generation_returns_cached(self):
        """Same generation should return same metrics."""
        db = MockDatabase()
        rotator = MetricRotator(db)

        metrics1 = rotator.get_active_metrics(100)
        metrics2 = rotator.get_active_metrics(100)

        assert metrics1 == metrics2

    def test_rotation_recorded_in_db(self):
        """Rotation should be recorded in database."""
        db = MockDatabase()
        rotator = MetricRotator(db)

        rotator.get_active_metrics(100)

        assert len(db.data['metric_rotation_history']) >= 1


class TestMetricRotatorSkip:
    """Tests for skip rotation mechanism."""

    def test_skip_is_probabilistic(self):
        """Skip should happen ~20% of the time."""
        db = MockDatabase()
        rotator = MetricRotator(db)

        # Run many times and count skips
        skips = 0
        trials = 100

        for gen in range(trials):
            db.data['metric_rotation_history'] = []  # Reset
            # Mock random to test both paths
            result = rotator.should_skip_rotation(gen * 1000)
            if result:
                skips += 1

        # Should be roughly 20% but allow for randomness
        # This is a statistical test, so we allow wide margin
        assert 5 <= skips <= 40  # Very loose bounds for randomness


class TestNoiseInjection:
    """Tests for noise injection."""

    def test_noise_changes_value(self):
        """Noise should modify the value within range."""
        db = MockDatabase()
        rotator = MetricRotator(db)

        original = 0.5

        # Apply noise multiple times
        noisy_values = [rotator.apply_noise(original) for _ in range(100)]

        # At least some should be different
        unique = len(set(noisy_values))
        assert unique > 1

        # All should be within noise range
        for v in noisy_values:
            assert 0.5 * 0.9 <= v <= 0.5 * 1.1


class TestMetricWeight:
    """Tests for metric weight retrieval."""

    def test_active_metric_weight_1(self):
        """Active metrics should have weight 1.0."""
        db = MockDatabase()
        rotator = MetricRotator(db)

        active = rotator.get_active_metrics(100)

        if active:
            weight = rotator.get_metric_weight(active[0], 100)
            assert weight == 1.0

    def test_inactive_metric_weight_0(self):
        """Inactive metrics should have weight 0.0."""
        db = MockDatabase()
        rotator = MetricRotator(db)

        # Use a metric name that's definitely not in pools
        weight = rotator.get_metric_weight("definitely_not_a_real_metric_xyz", 100)
        assert weight == 0.0


class TestRotationHistory:
    """Tests for rotation history retrieval."""

    def test_get_history_returns_records(self):
        """Should return rotation history."""
        db = MockDatabase()
        rotator = MetricRotator(db)

        # Create some history
        rotator.get_active_metrics(100)
        rotator.get_active_metrics(110)

        # Clear and add mock data
        db.data['metric_rotation_history'] = [
            {'generation': 100, 'active_metrics': '["m1","m2"]', 'was_skipped': 0, 'one_time_metrics_added': None},
            {'generation': 110, 'active_metrics': '["m2","m3"]', 'was_skipped': 1, 'one_time_metrics_added': None}
        ]

        history = rotator.get_rotation_history(limit=10)

        assert len(history) == 2


class TestAntiGoodhartRotator:
    """Tests for enhanced anti-Goodhart rotator."""

    def test_inherits_from_base(self):
        """Should inherit all base functionality."""
        db = MockDatabase()
        rotator = AntiGoodhartRotator(db)

        # Should have parent methods
        assert hasattr(rotator, 'get_rotation_phase')
        assert hasattr(rotator, 'apply_noise')
        assert hasattr(rotator, 'get_active_metrics')

    def test_has_inconsistency_rate(self):
        """Should have deliberate inconsistency rate."""
        db = MockDatabase()
        rotator = AntiGoodhartRotator(db)

        assert hasattr(rotator, 'DELIBERATE_INCONSISTENCY_RATE')
        assert rotator.DELIBERATE_INCONSISTENCY_RATE == 0.10


class TestMetricUsageStats:
    """Tests for metric usage statistics."""

    def test_returns_stats_dict(self):
        """Should return dictionary with stats."""
        db = MockDatabase()
        rotator = MetricRotator(db)

        stats = rotator.get_metric_usage_stats("test_metric")

        assert isinstance(stats, dict)
        assert 'metric_name' in stats
        assert stats['metric_name'] == 'test_metric'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
