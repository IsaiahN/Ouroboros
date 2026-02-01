"""
Tests for MetricConfidenceTracker - meta-metric confidence tracking.

Part of the Societal Metrics System test suite.
"""

import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import pytest

# Imports handled by conftest.py sys.path setup
from metric_confidence import MetricConfidenceTracker


class MockDatabase:
    """Mock database for testing without real SQLite."""

    def __init__(self):
        self.data = {
            'ecosystem_metrics': [],
            'metric_confidence': [],
            'trigger_history': [],
            'winning_sequences': []
        }

    def execute_query(self, query, params=None):
        """Mock execute_query that handles basic operations."""
        query_lower = query.lower().strip()

        # Handle CREATE TABLE/INDEX
        if query_lower.startswith('create'):
            return None

        # Handle INSERT
        if query_lower.startswith('insert'):
            if 'metric_confidence' in query_lower:
                if params:
                    record = {
                        'metric_name': params[0],
                        'generation': params[1],
                        'confidence_score': params[2],
                        'contradiction_rate': params[3],
                        'adaptation_speed': params[4],
                        'predictive_power': params[5],
                        'influence_concentration': params[6],
                        'decay_multiplier': params[7]
                    }
                    self.data['metric_confidence'].append(record)
            elif 'ecosystem_metrics' in query_lower:
                if params:
                    record = {
                        'metric_name': params[0],
                        'generation': params[1],
                        'value': params[2],
                        'metadata': params[3] if len(params) > 3 else None
                    }
                    self.data['ecosystem_metrics'].append(record)
            return None

        # Handle SELECT for ecosystem_metrics
        if 'ecosystem_metrics' in query_lower:
            metric_name = params[0] if params else None

            if 'order by generation asc' in query_lower:
                matching = [r for r in self.data['ecosystem_metrics']
                           if r['metric_name'] == metric_name]
                return matching[-5:] if matching else []

            if 'metric_name !=' in query_lower:
                matching = [r for r in self.data['ecosystem_metrics']
                           if r['metric_name'] != metric_name]
                return matching

            return [r for r in self.data['ecosystem_metrics']
                   if r['metric_name'] == metric_name]

        # Handle SELECT for metric_confidence
        if 'metric_confidence' in query_lower:
            if 'order by generation desc' in query_lower:
                metric_name = params[0] if params else None
                matching = [r for r in self.data['metric_confidence']
                           if r['metric_name'] == metric_name]
                # Sort by generation descending
                matching.sort(key=lambda x: x.get('generation', 0), reverse=True)
                # Apply limit if present in query (LIMIT N)
                if 'limit' in query_lower and params and len(params) > 1:
                    limit = params[-1] if isinstance(params[-1], int) else 10
                    return matching[:limit]
                return matching

            if 'confidence_score <' in query_lower:
                threshold = params[0] if params else 0.4
                return [r for r in self.data['metric_confidence']
                       if r['confidence_score'] < threshold]

            return self.data['metric_confidence']

        # Handle SELECT for trigger_history
        if 'trigger_history' in query_lower:
            return [{'count': 0}]

        # Handle SELECT for winning_sequences
        if 'winning_sequences' in query_lower:
            return [{'count': 0}]

        return []

    def add_metric_history(self, metric_name: str, values: list):
        """Helper to add metric history for testing."""
        for i, value in enumerate(values):
            self.data['ecosystem_metrics'].append({
                'metric_name': metric_name,
                'generation': 100 - len(values) + i,
                'value': value
            })


class TestMetricConfidenceCalculation:
    """Tests for confidence calculation."""

    def test_neutral_confidence_with_no_data(self):
        """Should return neutral confidence when no data."""
        db = MockDatabase()
        tracker = MetricConfidenceTracker(db)

        confidence = tracker.calculate_metric_confidence("test_metric", 100)

        # Should be around 0.5 (neutral) when no data
        assert 0.3 <= confidence <= 0.7

    def test_confidence_in_valid_range(self):
        """Confidence should always be between 0 and 1."""
        db = MockDatabase()
        tracker = MetricConfidenceTracker(db)

        # Add some metric history
        db.add_metric_history("test_metric", [0.5, 0.6, 0.7, 0.8, 0.9])

        confidence = tracker.calculate_metric_confidence("test_metric", 100)

        assert 0.0 <= confidence <= 1.0

    def test_confidence_stored_in_db(self):
        """Confidence should be stored in database."""
        db = MockDatabase()
        tracker = MetricConfidenceTracker(db)

        tracker.calculate_metric_confidence("test_metric", 100)

        assert len(db.data['metric_confidence']) == 1
        assert db.data['metric_confidence'][0]['metric_name'] == "test_metric"


class TestDecayMultiplier:
    """Tests for decay multiplier calculation."""

    def test_low_confidence_high_decay(self):
        """Low confidence should result in high decay multiplier."""
        db = MockDatabase()
        tracker = MetricConfidenceTracker(db)

        # Formula: 2.0 - (confidence * 1.5)
        # For confidence = 0.3: 2.0 - 0.45 = 1.55
        decay = tracker._calculate_decay_multiplier(0.3)

        assert decay > 1.0  # Should be accelerated
        assert abs(decay - 1.55) < 0.01

    def test_high_confidence_low_decay(self):
        """High confidence should result in low decay multiplier."""
        db = MockDatabase()
        tracker = MetricConfidenceTracker(db)

        # For confidence = 0.9: 2.0 - 1.35 = 0.65
        decay = tracker._calculate_decay_multiplier(0.9)

        assert decay < 1.0  # Should be slowed
        assert abs(decay - 0.65) < 0.01

    def test_neutral_confidence_neutral_decay(self):
        """Mid-range confidence should give neutral decay."""
        db = MockDatabase()
        tracker = MetricConfidenceTracker(db)

        # For confidence = 0.67: 2.0 - 1.0 = 1.0
        decay = tracker._calculate_decay_multiplier(0.67)

        assert abs(decay - 1.0) < 0.1


class TestAdaptationSpeed:
    """Tests for adaptation speed calculation."""

    def test_stable_metric_low_adaptation(self):
        """Stable metric should have low adaptation speed."""
        db = MockDatabase()
        tracker = MetricConfidenceTracker(db)

        # Add stable values
        db.add_metric_history("stable", [0.5, 0.5, 0.5, 0.5, 0.5])

        speed = tracker._calculate_adaptation_speed("stable", 100)

        assert speed < 0.3  # Should be low

    def test_fast_improving_high_adaptation(self):
        """Fast improving metric should have high adaptation speed."""
        db = MockDatabase()
        tracker = MetricConfidenceTracker(db)

        # Add rapidly improving values (20% per gen = very fast)
        db.add_metric_history("improving", [0.1, 0.3, 0.5, 0.7, 0.9])

        speed = tracker._calculate_adaptation_speed("improving", 100)

        assert speed > 0.5  # Should be high


class TestGetLowConfidenceMetrics:
    """Tests for low confidence metric detection."""

    def test_returns_low_confidence_only(self):
        """Should only return metrics below threshold."""
        db = MockDatabase()
        tracker = MetricConfidenceTracker(db)

        # Add metrics with different confidences
        db.data['metric_confidence'] = [
            {'metric_name': 'low', 'confidence_score': 0.2, 'decay_multiplier': 1.7},
            {'metric_name': 'high', 'confidence_score': 0.8, 'decay_multiplier': 0.8}
        ]

        low = tracker.get_low_confidence_metrics(100, threshold=0.5)

        assert len(low) == 1
        assert low[0]['metric_name'] == 'low'

    def test_empty_when_all_high(self):
        """Should return empty when all metrics above threshold."""
        db = MockDatabase()
        tracker = MetricConfidenceTracker(db)

        db.data['metric_confidence'] = [
            {'metric_name': 'm1', 'confidence_score': 0.8, 'decay_multiplier': 0.8},
            {'metric_name': 'm2', 'confidence_score': 0.9, 'decay_multiplier': 0.65}
        ]

        low = tracker.get_low_confidence_metrics(100, threshold=0.5)

        assert len(low) == 0


class TestConfidenceHistory:
    """Tests for confidence history retrieval."""

    def test_get_history_returns_records(self):
        """Should return confidence history records."""
        db = MockDatabase()
        tracker = MetricConfidenceTracker(db)

        # Add some history
        db.data['metric_confidence'] = [
            {'metric_name': 'test', 'generation': 100, 'confidence_score': 0.7},
            {'metric_name': 'test', 'generation': 99, 'confidence_score': 0.6}
        ]

        history = tracker.get_confidence_history('test', limit=10)

        assert len(history) == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
