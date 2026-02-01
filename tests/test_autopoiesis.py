"""
Tests for AutopoiesisMonitor - core autopoiesis metrics.

Part of the Societal Metrics System test suite.
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import pytest

# Imports handled by conftest.py sys.path setup
from manual_tools.analysis.autopoiesis_monitor import AutopoiesisMonitor


class MockDatabase:
    """Mock database for testing without real SQLite."""
    
    def __init__(self):
        self.data = {
            'ecosystem_metrics': [],
            'autopoiesis_snapshots': [],
            'agent_arc_performance': [],
            'winning_sequences': [],
            'agents': [],
            'game_results': []
        }
    
    def execute_query(self, query, params=None):
        """Mock execute_query that handles basic operations."""
        query_lower = query.lower().strip()
        
        # Handle CREATE TABLE/INDEX
        if query_lower.startswith('create'):
            return None
        
        # Handle INSERT
        if query_lower.startswith('insert'):
            if 'ecosystem_metrics' in query_lower and params:
                record = {
                    'metric_name': params[0],
                    'generation': params[1],
                    'value': params[2],
                    'metadata': params[3] if len(params) > 3 else None
                }
                self.data['ecosystem_metrics'].append(record)
            elif 'autopoiesis_snapshots' in query_lower and params:
                record = {
                    'snapshot_id': params[0],
                    'generation': params[1],
                    'emergence_gain': params[2],
                    'identity_drift': params[3],
                    'control_error': params[4],
                    'loop_detection_score': params[5],
                    'overall_health': params[6],
                    'metadata': params[7]
                }
                self.data['autopoiesis_snapshots'].append(record)
            return None
        
        # Handle SELECT for agent_arc_performance
        if 'agent_arc_performance' in query_lower:
            return [{'count': len(self.data['agent_arc_performance'])}]
        
        # Handle SELECT for winning_sequences
        if 'winning_sequences' in query_lower:
            if 'count(distinct' in query_lower:
                return [{'count': len(self.data['winning_sequences'])}]
            if 'times_referenced = 0' in query_lower:
                solo = [s for s in self.data['winning_sequences'] 
                       if s.get('times_referenced', 0) == 0]
                return [{'count': len(solo)}]
            return [{'count': len(self.data['winning_sequences'])}]
        
        # Handle SELECT for agents
        if 'agents' in query_lower:
            if 'count(*)' in query_lower:
                active = [a for a in self.data['agents'] if a.get('is_active', True)]
                return [{'count': len(active)}]
            return self.data['agents']
        
        # Handle SELECT for game_results
        if 'game_results' in query_lower:
            if 'final_score = 0' in query_lower:
                zero = [g for g in self.data['game_results'] if g.get('final_score', 0) == 0]
                return [{'count': len(zero)}]
            return [{'count': len(self.data['game_results'])}]
        
        # Handle SELECT for ecosystem_metrics
        if 'ecosystem_metrics' in query_lower:
            if 'order by generation desc' in query_lower:
                metric_name = params[0] if params else None
                matching = [m for m in self.data['ecosystem_metrics']
                           if m['metric_name'] == metric_name]
                matching.sort(key=lambda x: x['generation'], reverse=True)
                limit = params[1] if len(params) > 1 else 50
                return matching[:limit]
            if 'group by metric_name' in query_lower:
                # Return variance-like data
                return [{'metric_name': 'test', 'avg_value': 0.5, 'variance': 0.01}]
            return self.data['ecosystem_metrics']
        
        # Handle SELECT for autopoiesis_snapshots
        if 'autopoiesis_snapshots' in query_lower:
            return self.data['autopoiesis_snapshots']
        
        return [{'count': 0}]
    
    def add_agents(self, count: int, active: bool = True):
        """Helper to add mock agents."""
        for i in range(count):
            self.data['agents'].append({
                'agent_id': f'agent_{i}',
                'is_active': active,
                'prestige': 1.0
            })
    
    def add_winning_sequences(self, count: int, times_referenced: int = 0):
        """Helper to add mock winning sequences."""
        for i in range(count):
            self.data['winning_sequences'].append({
                'sequence_id': f'seq_{i}',
                'times_referenced': times_referenced,
                'times_validated': 1
            })


class TestEmergenceGain:
    """Tests for emergence gain calculation."""
    
    def test_returns_positive_value(self):
        """Should return positive emergence gain."""
        db = MockDatabase()
        monitor = AutopoiesisMonitor(db)
        
        gain = monitor.calculate_emergence_gain(100)
        
        assert gain >= 0.0
    
    def test_solo_discoveries_gives_emergence_1(self):
        """When no sharing, emergence should be low."""
        db = MockDatabase()
        db.add_winning_sequences(5, times_referenced=0)  # Solo discoveries
        monitor = AutopoiesisMonitor(db)
        
        gain = monitor.calculate_emergence_gain(100)
        
        # With only solo discoveries (times_referenced=0), 
        # network_wins should be 0, so gain = 0/5 = 0
        assert gain <= 1.0
    
    def test_emergence_stored_in_db(self):
        """Emergence should be stored in database."""
        db = MockDatabase()
        monitor = AutopoiesisMonitor(db)
        
        monitor.calculate_emergence_gain(100)
        
        stored = [m for m in db.data['ecosystem_metrics']
                 if m['metric_name'] == 'emergence_gain']
        assert len(stored) == 1


class TestIdentityDrift:
    """Tests for identity drift calculation."""
    
    def test_returns_value_in_range(self):
        """Identity drift should be between 0 and 1."""
        db = MockDatabase()
        monitor = AutopoiesisMonitor(db)
        
        drift = monitor.calculate_identity_drift(100)
        
        assert 0.0 <= drift <= 1.0
    
    def test_no_problems_low_drift(self):
        """With good progress and no issues, drift should be low."""
        db = MockDatabase()
        db.add_winning_sequences(10, times_referenced=5)  # Good sequences, validated
        db.add_agents(10)
        monitor = AutopoiesisMonitor(db)
        
        drift = monitor.calculate_identity_drift(100)
        
        assert drift < 0.5
    
    def test_drift_stored_in_db(self):
        """Identity drift should be stored."""
        db = MockDatabase()
        monitor = AutopoiesisMonitor(db)
        
        monitor.calculate_identity_drift(100)
        
        stored = [m for m in db.data['ecosystem_metrics']
                 if m['metric_name'] == 'identity_drift']
        assert len(stored) == 1


class TestControlError:
    """Tests for control error calculation."""
    
    def test_returns_numeric_value(self):
        """Control error should be a number."""
        db = MockDatabase()
        monitor = AutopoiesisMonitor(db)
        
        error = monitor.calculate_control_error(100)
        
        assert isinstance(error, (int, float))
    
    def test_positive_error_means_undershooting(self):
        """Positive error means actual < target."""
        db = MockDatabase()
        # No winning sequences = 0 progress
        monitor = AutopoiesisMonitor(db)
        
        error = monitor.calculate_control_error(100)
        
        # Target is 0.5, actual is 0, so error = 0.5 - 0 = 0.5
        assert error > 0
    
    def test_control_error_stored(self):
        """Control error should be stored."""
        db = MockDatabase()
        monitor = AutopoiesisMonitor(db)
        
        monitor.calculate_control_error(100)
        
        stored = [m for m in db.data['ecosystem_metrics']
                 if m['metric_name'] == 'control_error']
        assert len(stored) == 1


class TestLoopDetection:
    """Tests for loop detection calculation."""
    
    def test_returns_value_in_range(self):
        """Loop score should be between 0 and 1."""
        db = MockDatabase()
        db.add_agents(10)
        monitor = AutopoiesisMonitor(db)
        
        score = monitor.calculate_loop_detection_score(100)
        
        assert 0.0 <= score <= 1.0
    
    def test_no_stuck_agents_low_score(self):
        """With no stuck agents, score should be low."""
        db = MockDatabase()
        db.add_agents(10)
        # No game results with repetitive patterns
        monitor = AutopoiesisMonitor(db)
        
        score = monitor.calculate_loop_detection_score(100)
        
        assert score < 0.5


class TestSystemHealth:
    """Tests for aggregate system health."""
    
    def test_returns_health_dict(self):
        """Should return comprehensive health dictionary."""
        db = MockDatabase()
        db.add_agents(10)
        monitor = AutopoiesisMonitor(db)
        
        health = monitor.get_system_health(100)
        
        assert isinstance(health, dict)
        assert 'emergence_gain' in health
        assert 'identity_drift' in health
        assert 'control_error' in health
        assert 'loop_detection_score' in health
        assert 'overall_health' in health
        assert 'status' in health
        assert 'warnings' in health
    
    def test_overall_health_in_range(self):
        """Overall health should be between 0 and 1."""
        db = MockDatabase()
        db.add_agents(10)
        monitor = AutopoiesisMonitor(db)
        
        health = monitor.get_system_health(100)
        
        assert 0.0 <= health['overall_health'] <= 1.0
    
    def test_status_is_valid(self):
        """Status should be a valid status string."""
        db = MockDatabase()
        db.add_agents(10)
        monitor = AutopoiesisMonitor(db)
        
        health = monitor.get_system_health(100)
        
        valid_statuses = ['EXCELLENT', 'GOOD', 'FAIR', 'POOR', 'CRITICAL']
        assert health['status'] in valid_statuses
    
    def test_snapshot_stored(self):
        """Health snapshot should be stored in database."""
        db = MockDatabase()
        db.add_agents(10)
        monitor = AutopoiesisMonitor(db)
        
        monitor.get_system_health(100)
        
        assert len(db.data['autopoiesis_snapshots']) == 1


class TestHealthWarnings:
    """Tests for warning generation."""
    
    def test_no_warnings_when_healthy(self):
        """Should have no warnings when metrics are good."""
        db = MockDatabase()
        monitor = AutopoiesisMonitor(db)
        
        # Good values
        warnings = monitor._get_warnings(
            emergence=1.5,  # Above minimum
            drift=0.1,      # Below threshold
            control=0.1,    # Near zero
            loops=0.1       # Low
        )
        
        assert len(warnings) == 0
    
    def test_warning_on_low_emergence(self):
        """Should warn on low emergence."""
        db = MockDatabase()
        monitor = AutopoiesisMonitor(db)
        
        warnings = monitor._get_warnings(
            emergence=0.5,  # Below 1.0
            drift=0.1,
            control=0.1,
            loops=0.1
        )
        
        assert any('emergence' in w.lower() for w in warnings)
    
    def test_warning_on_high_drift(self):
        """Should warn on high identity drift."""
        db = MockDatabase()
        monitor = AutopoiesisMonitor(db)
        
        warnings = monitor._get_warnings(
            emergence=1.5,
            drift=0.5,  # Above 0.3 threshold
            control=0.1,
            loops=0.1
        )
        
        assert any('drift' in w.lower() for w in warnings)


class TestMetricTrends:
    """Tests for metric trend analysis."""
    
    def test_returns_trend_dict(self):
        """Should return trend analysis dictionary."""
        db = MockDatabase()
        # Add some metric history
        for i in range(10):
            db.data['ecosystem_metrics'].append({
                'metric_name': 'test_metric',
                'generation': 90 + i,
                'value': 0.5 + i * 0.01
            })
        
        monitor = AutopoiesisMonitor(db)
        trend = monitor.get_metric_trend('test_metric')
        
        assert 'metric_name' in trend
        assert 'trend' in trend
    
    def test_unknown_trend_with_no_data(self):
        """Should return UNKNOWN trend with no data."""
        db = MockDatabase()
        monitor = AutopoiesisMonitor(db)
        
        trend = monitor.get_metric_trend('nonexistent')
        
        assert trend['trend'] == 'UNKNOWN'


class TestRegimeChange:
    """Tests for regime change detection."""
    
    def test_returns_boolean(self):
        """Should return boolean for regime change."""
        db = MockDatabase()
        monitor = AutopoiesisMonitor(db)
        
        result = monitor.detect_regime_change(100)
        
        assert isinstance(result, bool)
    
    def test_no_change_with_stable_metrics(self):
        """Should not detect change with stable metrics."""
        db = MockDatabase()
        # Add stable metric history
        for i in range(40):
            db.data['ecosystem_metrics'].append({
                'metric_name': 'stable_metric',
                'generation': 60 + i,
                'value': 0.5  # Constant value
            })
        
        monitor = AutopoiesisMonitor(db)
        result = monitor.detect_regime_change(100)
        
        # Should not detect regime change with stable data
        assert result is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
