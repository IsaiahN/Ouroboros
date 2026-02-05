"""
Tests for Graph Evolution Engine with Valence-Weighted Crystallization.

Phase 11: Phenomenology <-> Graph Evolution Integration

Tests cover:
- ValenceWeightedEdge creation and properties
- Valence-adjusted crystallization thresholds
- GraphEvolution traversal recording
- Crystallization logic
- Edge trust calculations
- GameFeelTrajectory (optional feature)
- Anomaly detection
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from engines.cognition.phenomenology_layer import FeltState, Valence
from engines.reasoning.graph_evolution import (
    BASE_CRYSTALLIZATION_THRESHOLD,
    BOREDOM_FAST_TRACK_MULTIPLIER,
    BOREDOM_SUCCESS_THRESHOLD,
    MIN_SUCCESS_RATE_FOR_CRYSTALLIZATION,
    VALENCE_THRESHOLD_MULTIPLIERS,
    FeelAnomaly,
    FeelTrajectoryStore,
    GameFeelTrajectory,
    GraphEvolution,
    ValenceWeightedEdge,
    detect_feel_anomaly,
)

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def default_felt_state():
    """Create a default FeltState for testing."""
    return FeltState(
        valence=Valence.STABILITY,
        arousal=0.5,
        certainty=0.7,
        agency=0.6,
        salience=0.4,
        momentum=0.0,
        compression_ratio=5.0,
        dominant_contributors=['test'],
    )


@pytest.fixture
def threat_felt_state():
    """Create a THREAT FeltState for testing."""
    return FeltState(
        valence=Valence.THREAT,
        arousal=0.8,
        certainty=0.3,
        agency=0.2,
        salience=0.9,
        momentum=-0.5,
        compression_ratio=5.0,
        dominant_contributors=['contradiction'],
    )


@pytest.fixture
def boredom_felt_state():
    """Create a BOREDOM FeltState for testing."""
    return FeltState(
        valence=Valence.BOREDOM,
        arousal=0.2,
        certainty=0.8,
        agency=0.7,
        salience=0.1,
        momentum=0.0,
        compression_ratio=5.0,
        dominant_contributors=['stagnation'],
    )


@pytest.fixture
def confusion_felt_state():
    """Create a CONFUSION FeltState for testing."""
    return FeltState(
        valence=Valence.CONFUSION,
        arousal=0.6,
        certainty=0.2,
        agency=0.3,
        salience=0.7,
        momentum=-0.2,
        compression_ratio=5.0,
        dominant_contributors=['unknown'],
    )


@pytest.fixture
def graph():
    """Create a fresh GraphEvolution instance."""
    return GraphEvolution()


# ============================================================================
# TEST: ValenceWeightedEdge
# ============================================================================

class TestValenceWeightedEdge:
    """Tests for ValenceWeightedEdge dataclass."""

    def test_edge_creation_defaults(self):
        """Test edge creation with default values."""
        edge = ValenceWeightedEdge(from_rung='survey', to_rung='pattern')

        assert edge.from_rung == 'survey'
        assert edge.to_rung == 'pattern'
        assert edge.traversal_count == 0
        assert edge.success_count == 0
        assert edge.discovery_valence == Valence.CONFUSION
        assert edge.discovery_arousal == 0.5
        assert edge.is_crystallized is False
        assert edge.crystallization_timestamp is None

    def test_edge_key_property(self):
        """Test edge_key tuple property."""
        edge = ValenceWeightedEdge(from_rung='survey', to_rung='pattern')
        assert edge.edge_key == ('survey', 'pattern')

    def test_success_rate_empty(self):
        """Test success rate with no traversals."""
        edge = ValenceWeightedEdge(from_rung='a', to_rung='b')
        assert edge.success_rate == 0.0

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        edge = ValenceWeightedEdge(
            from_rung='a', to_rung='b',
            traversal_count=10, success_count=7
        )
        assert edge.success_rate == 0.7

    def test_record_traversal_success(self):
        """Test recording successful traversal."""
        edge = ValenceWeightedEdge(from_rung='a', to_rung='b')
        edge.record_traversal(success=True)

        assert edge.traversal_count == 1
        assert edge.success_count == 1

    def test_record_traversal_failure(self):
        """Test recording failed traversal."""
        edge = ValenceWeightedEdge(from_rung='a', to_rung='b')
        edge.record_traversal(success=False)

        assert edge.traversal_count == 1
        assert edge.success_count == 0

    def test_record_multiple_traversals(self):
        """Test multiple traversals accumulate."""
        edge = ValenceWeightedEdge(from_rung='a', to_rung='b')

        edge.record_traversal(success=True)
        edge.record_traversal(success=True)
        edge.record_traversal(success=False)
        edge.record_traversal(success=True)

        assert edge.traversal_count == 4
        assert edge.success_count == 3
        assert edge.success_rate == 0.75


class TestValenceAdjustedThreshold:
    """Tests for valence-adjusted crystallization thresholds."""

    def test_stability_threshold(self):
        """STABILITY paths crystallize slightly faster."""
        edge = ValenceWeightedEdge(
            from_rung='a', to_rung='b',
            discovery_valence=Valence.STABILITY,
            discovery_arousal=0.5
        )
        threshold = edge.valence_adjusted_crystallization_threshold
        expected = int(BASE_CRYSTALLIZATION_THRESHOLD * 0.9)
        assert threshold == expected

    def test_threat_threshold(self):
        """THREAT paths require 1.5x traversals."""
        edge = ValenceWeightedEdge(
            from_rung='a', to_rung='b',
            discovery_valence=Valence.THREAT,
            discovery_arousal=0.5
        )
        threshold = edge.valence_adjusted_crystallization_threshold
        expected = int(BASE_CRYSTALLIZATION_THRESHOLD * 1.5)
        assert threshold == expected

    def test_confusion_threshold(self):
        """CONFUSION paths require 2.0x traversals."""
        edge = ValenceWeightedEdge(
            from_rung='a', to_rung='b',
            discovery_valence=Valence.CONFUSION,
            discovery_arousal=0.5
        )
        threshold = edge.valence_adjusted_crystallization_threshold
        expected = int(BASE_CRYSTALLIZATION_THRESHOLD * 2.0)
        assert threshold == expected

    def test_boredom_low_success_normal_threshold(self):
        """BOREDOM paths with low success rate use normal threshold."""
        edge = ValenceWeightedEdge(
            from_rung='a', to_rung='b',
            discovery_valence=Valence.BOREDOM,
            discovery_arousal=0.5,
            traversal_count=10,
            success_count=5  # 50% success rate
        )
        threshold = edge.valence_adjusted_crystallization_threshold
        # Low success, no fast track
        assert threshold == BASE_CRYSTALLIZATION_THRESHOLD

    def test_boredom_high_success_fast_track(self):
        """BOREDOM paths with >70% success crystallize at 0.7x."""
        edge = ValenceWeightedEdge(
            from_rung='a', to_rung='b',
            discovery_valence=Valence.BOREDOM,
            discovery_arousal=0.5,
            traversal_count=10,
            success_count=8  # 80% success rate
        )
        threshold = edge.valence_adjusted_crystallization_threshold
        expected = int(BASE_CRYSTALLIZATION_THRESHOLD * BOREDOM_FAST_TRACK_MULTIPLIER)
        assert threshold == expected

    def test_high_arousal_increases_threshold(self):
        """High arousal at discovery increases scrutiny."""
        # Use CONFUSION base which has a higher multiplier (2.0)
        # This ensures arousal adjustment produces different int values
        edge_normal = ValenceWeightedEdge(
            from_rung='a', to_rung='b',
            discovery_valence=Valence.CONFUSION,
            discovery_arousal=0.5
        )
        # High arousal
        edge_high = ValenceWeightedEdge(
            from_rung='a', to_rung='b',
            discovery_valence=Valence.CONFUSION,
            discovery_arousal=1.0  # Maximum arousal
        )

        # With CONFUSION (2.0x) and arousal adjustment:
        # Normal: 5 * 2.0 * 1.0 = 10
        # High:   5 * 2.0 * 1.1 = 11
        assert edge_high.valence_adjusted_crystallization_threshold > edge_normal.valence_adjusted_crystallization_threshold

    def test_low_arousal_decreases_threshold(self):
        """Low arousal at discovery decreases scrutiny."""
        # Normal arousal
        edge_normal = ValenceWeightedEdge(
            from_rung='a', to_rung='b',
            discovery_valence=Valence.OPPORTUNITY,
            discovery_arousal=0.5
        )
        # Low arousal
        edge_low = ValenceWeightedEdge(
            from_rung='a', to_rung='b',
            discovery_valence=Valence.OPPORTUNITY,
            discovery_arousal=0.1
        )

        assert edge_low.valence_adjusted_crystallization_threshold < edge_normal.valence_adjusted_crystallization_threshold


class TestEdgeCrystallization:
    """Tests for edge crystallization logic."""

    def test_cannot_crystallize_without_traversals(self):
        """Edge cannot crystallize without enough traversals."""
        edge = ValenceWeightedEdge(from_rung='a', to_rung='b')
        assert edge.check_crystallization() is False

    def test_cannot_crystallize_low_success_rate(self):
        """Edge cannot crystallize with low success rate."""
        edge = ValenceWeightedEdge(
            from_rung='a', to_rung='b',
            discovery_valence=Valence.STABILITY,
            traversal_count=10,
            success_count=3  # 30% success
        )
        assert edge.check_crystallization() is False

    def test_crystallization_success(self):
        """Edge crystallizes when criteria met."""
        edge = ValenceWeightedEdge(
            from_rung='a', to_rung='b',
            discovery_valence=Valence.STABILITY,
            discovery_arousal=0.5,
            traversal_count=5,
            success_count=4  # 80% success
        )

        assert edge.check_crystallization() is True
        assert edge.crystallize() is True
        assert edge.is_crystallized is True
        assert edge.crystallization_timestamp is not None

    def test_crystallization_idempotent(self):
        """Crystallizing twice returns True both times."""
        edge = ValenceWeightedEdge(
            from_rung='a', to_rung='b',
            traversal_count=10,
            success_count=8
        )

        assert edge.crystallize() is True
        first_timestamp = edge.crystallization_timestamp

        assert edge.crystallize() is True
        # Timestamp should not change
        assert edge.crystallization_timestamp == first_timestamp


class TestEdgeSerialization:
    """Tests for edge serialization."""

    def test_to_dict(self):
        """Test serialization to dictionary."""
        edge = ValenceWeightedEdge(
            from_rung='survey',
            to_rung='pattern',
            traversal_count=5,
            success_count=4,
            discovery_valence=Valence.OPPORTUNITY,
            discovery_arousal=0.6
        )

        data = edge.to_dict()

        assert data['from_rung'] == 'survey'
        assert data['to_rung'] == 'pattern'
        assert data['traversal_count'] == 5
        assert data['success_count'] == 4
        assert data['discovery_valence'] == 'opportunity'
        assert data['discovery_arousal'] == 0.6
        assert data['success_rate'] == 0.8

    def test_round_trip(self):
        """Test serialization round-trip."""
        original = ValenceWeightedEdge(
            from_rung='a',
            to_rung='b',
            traversal_count=10,
            success_count=8,
            discovery_valence=Valence.THREAT,
            discovery_arousal=0.7
        )
        original.crystallize()

        data = original.to_dict()
        restored = ValenceWeightedEdge.from_dict(data)

        assert restored.from_rung == original.from_rung
        assert restored.to_rung == original.to_rung
        assert restored.traversal_count == original.traversal_count
        assert restored.success_count == original.success_count
        assert restored.discovery_valence == original.discovery_valence
        assert restored.discovery_arousal == original.discovery_arousal
        assert restored.is_crystallized == original.is_crystallized


# ============================================================================
# TEST: GraphEvolution
# ============================================================================

class TestGraphEvolution:
    """Tests for GraphEvolution class."""

    def test_empty_graph(self, graph):
        """Test empty graph statistics."""
        stats = graph.get_statistics()
        assert stats['total_edges'] == 0
        assert stats['crystallized_edges'] == 0

    def test_record_new_traversal(self, graph, default_felt_state):
        """Test recording a new traversal creates edge."""
        edge = graph.record_traversal(
            'survey', 'pattern',
            success=True,
            felt_state=default_felt_state
        )

        assert edge.from_rung == 'survey'
        assert edge.to_rung == 'pattern'
        assert edge.traversal_count == 1
        assert edge.success_count == 1
        assert edge.discovery_valence == Valence.STABILITY

    def test_record_traversal_updates_existing(self, graph, default_felt_state):
        """Test recording traversal updates existing edge."""
        graph.record_traversal('a', 'b', success=True, felt_state=default_felt_state)
        edge = graph.record_traversal('a', 'b', success=False, felt_state=default_felt_state)

        assert edge.traversal_count == 2
        assert edge.success_count == 1
        # Discovery context should NOT change
        assert edge.discovery_valence == Valence.STABILITY

    def test_auto_crystallization(self, graph, default_felt_state):
        """Test automatic crystallization when criteria met."""
        # Record enough successful traversals
        for _ in range(10):
            graph.record_traversal('a', 'b', success=True, felt_state=default_felt_state)

        edge = graph.get_edge('a', 'b')
        assert edge.is_crystallized is True

    def test_should_crystallize(self, graph, default_felt_state):
        """Test should_crystallize check."""
        # Not enough traversals
        graph.record_traversal('a', 'b', success=True, felt_state=default_felt_state)
        assert graph.should_crystallize(('a', 'b')) is False

        # Add more successful traversals
        for _ in range(9):
            graph.record_traversal('a', 'b', success=True, felt_state=default_felt_state)

        assert graph.should_crystallize(('a', 'b')) is True

    def test_get_edge(self, graph, default_felt_state):
        """Test getting edge by from/to rungs."""
        graph.record_traversal('survey', 'pattern', success=True, felt_state=default_felt_state)

        edge = graph.get_edge('survey', 'pattern')
        assert edge is not None
        assert edge.from_rung == 'survey'

        # Non-existent edge
        assert graph.get_edge('foo', 'bar') is None

    def test_get_edge_trust_new_edge(self, graph, default_felt_state):
        """Test edge trust for new edge."""
        graph.record_traversal('a', 'b', success=True, felt_state=default_felt_state)

        trust = graph.get_edge_trust('a', 'b')
        assert 0.0 < trust <= 1.0

    def test_get_edge_trust_crystallized_bonus(self, graph, default_felt_state):
        """Test crystallized edges get trust bonus."""
        # Build up edge
        for _ in range(10):
            graph.record_traversal('a', 'b', success=True, felt_state=default_felt_state)

        edge = graph.get_edge('a', 'b')
        assert edge.is_crystallized

        trust = graph.get_edge_trust('a', 'b')
        # Should be high (100% success + crystallization bonus)
        assert trust >= 0.9

    def test_get_edge_trust_valence_modifier(self, graph, threat_felt_state, default_felt_state):
        """Test valence affects trust score."""
        # Create threat-discovered edge
        for _ in range(3):
            graph.record_traversal('threat_a', 'threat_b', success=True, felt_state=threat_felt_state)

        # Create stability-discovered edge
        for _ in range(3):
            graph.record_traversal('stable_a', 'stable_b', success=True, felt_state=default_felt_state)

        threat_trust = graph.get_edge_trust('threat_a', 'threat_b')
        stable_trust = graph.get_edge_trust('stable_a', 'stable_b')

        # Stability-discovered paths should be more trusted
        assert stable_trust > threat_trust

    def test_get_edges_from_rung(self, graph, default_felt_state):
        """Test getting all edges from a rung."""
        graph.record_traversal('survey', 'pattern', success=True, felt_state=default_felt_state)
        graph.record_traversal('survey', 'hypothesis', success=True, felt_state=default_felt_state)
        graph.record_traversal('pattern', 'action', success=True, felt_state=default_felt_state)

        edges = graph.get_edges_from_rung('survey')
        assert len(edges) == 2
        assert all(e.from_rung == 'survey' for e in edges)

    def test_get_edges_to_rung(self, graph, default_felt_state):
        """Test getting all edges to a rung."""
        graph.record_traversal('survey', 'pattern', success=True, felt_state=default_felt_state)
        graph.record_traversal('hypothesis', 'pattern', success=True, felt_state=default_felt_state)

        edges = graph.get_edges_to_rung('pattern')
        assert len(edges) == 2
        assert all(e.to_rung == 'pattern' for e in edges)

    def test_get_preferred_next_rung(self, graph, default_felt_state):
        """Test getting preferred (highest trust) next rung."""
        # Create edges with different success rates
        for _ in range(10):
            graph.record_traversal('survey', 'pattern', success=True, felt_state=default_felt_state)

        for i in range(10):
            graph.record_traversal('survey', 'hypothesis', success=(i < 5), felt_state=default_felt_state)

        preferred = graph.get_preferred_next_rung('survey')
        # Pattern should be preferred (100% vs 50% success)
        assert preferred == 'pattern'

    def test_get_crystallized_edges(self, graph, default_felt_state):
        """Test getting all crystallized edges."""
        # Non-crystallized
        graph.record_traversal('a', 'b', success=True, felt_state=default_felt_state)

        # Crystallized
        for _ in range(10):
            graph.record_traversal('x', 'y', success=True, felt_state=default_felt_state)

        crystallized = graph.get_crystallized_edges()
        assert len(crystallized) == 1
        assert crystallized[0].edge_key == ('x', 'y')


class TestGraphEvolutionDecay:
    """Tests for edge decay functionality."""

    def test_decay_unused_edges(self, graph, default_felt_state):
        """Test decaying unused edges."""
        # Create an edge
        edge = graph.record_traversal('a', 'b', success=True, felt_state=default_felt_state)
        edge.success_count = 10
        edge.traversal_count = 10

        # Manually set old last_traversal
        edge.last_traversal = datetime.now() - timedelta(hours=48)

        affected = graph.decay_unused_edges(decay_factor=0.5, min_age_hours=24)

        assert affected == 1
        assert edge.success_count == 5

    def test_decay_does_not_affect_recent(self, graph, default_felt_state):
        """Test decay does not affect recently used edges."""
        edge = graph.record_traversal('a', 'b', success=True, felt_state=default_felt_state)
        edge.success_count = 10
        edge.traversal_count = 10

        # Recent use (default is now)
        affected = graph.decay_unused_edges(decay_factor=0.5, min_age_hours=24)

        assert affected == 0
        assert edge.success_count == 10


class TestGraphEvolutionSerialization:
    """Tests for graph serialization."""

    def test_round_trip(self, graph, default_felt_state, threat_felt_state):
        """Test serialization round-trip."""
        # Build some graph structure
        for _ in range(5):
            graph.record_traversal('a', 'b', success=True, felt_state=default_felt_state)
        for _ in range(3):
            graph.record_traversal('b', 'c', success=True, felt_state=threat_felt_state)

        # Serialize
        data = graph.to_dict()

        # Deserialize
        restored = GraphEvolution.from_dict(data)

        assert len(restored.edges) == 2
        assert restored.get_edge('a', 'b').traversal_count == 5
        assert restored.get_edge('b', 'c').discovery_valence == Valence.THREAT


# ============================================================================
# TEST: GameFeelTrajectory
# ============================================================================

class TestGameFeelTrajectory:
    """Tests for GameFeelTrajectory dataclass."""

    def test_creation_defaults(self):
        """Test trajectory creation with defaults."""
        traj = GameFeelTrajectory(game_id='test_game')

        assert traj.game_id == 'test_game'
        assert traj.typical_opening_valence == Valence.CONFUSION
        assert traj.typical_midgame_valence == Valence.OPPORTUNITY
        assert traj.typical_resolution_valence == Valence.STABILITY
        assert traj.sample_count == 0

    def test_record_playthrough(self):
        """Test recording a playthrough."""
        traj = GameFeelTrajectory(game_id='test_game')

        traj.record_playthrough(
            opening_valence=Valence.BOREDOM,
            midgame_valence=Valence.THREAT,
            resolution_valence=Valence.STABILITY
        )

        assert traj.sample_count == 1

    def test_typical_valences_update_after_samples(self):
        """Test typical valences update after enough samples."""
        traj = GameFeelTrajectory(game_id='test_game')

        # Record 5 playthroughs all with BOREDOM opening
        for _ in range(5):
            traj.record_playthrough(
                opening_valence=Valence.BOREDOM,
                midgame_valence=Valence.THREAT,
                resolution_valence=Valence.OPPORTUNITY
            )

        # Typical should now reflect recorded data
        assert traj.typical_opening_valence == Valence.BOREDOM
        assert traj.typical_midgame_valence == Valence.THREAT
        assert traj.typical_resolution_valence == Valence.OPPORTUNITY

    def test_get_expected_valence(self):
        """Test getting expected valence by phase."""
        traj = GameFeelTrajectory(
            game_id='test',
            typical_opening_valence=Valence.CONFUSION,
            typical_midgame_valence=Valence.OPPORTUNITY,
            typical_resolution_valence=Valence.STABILITY
        )

        assert traj.get_expected_valence('opening') == Valence.CONFUSION
        assert traj.get_expected_valence('midgame') == Valence.OPPORTUNITY
        assert traj.get_expected_valence('resolution') == Valence.STABILITY
        assert traj.get_expected_valence('unknown') == Valence.CONFUSION

    def test_serialization_round_trip(self):
        """Test trajectory serialization."""
        original = GameFeelTrajectory(
            game_id='test_game',
            typical_opening_valence=Valence.BOREDOM,
            typical_midgame_valence=Valence.THREAT,
            typical_resolution_valence=Valence.STABILITY,
            sample_count=10
        )

        data = original.to_dict()
        restored = GameFeelTrajectory.from_dict(data)

        assert restored.game_id == original.game_id
        assert restored.typical_opening_valence == original.typical_opening_valence
        assert restored.typical_midgame_valence == original.typical_midgame_valence
        assert restored.sample_count == original.sample_count


# ============================================================================
# TEST: Anomaly Detection
# ============================================================================

class TestAnomalyDetection:
    """Tests for feel anomaly detection."""

    def test_no_anomaly_when_expected(self, default_felt_state):
        """Test no anomaly when valence matches expected."""
        traj = GameFeelTrajectory(
            game_id='test',
            typical_opening_valence=Valence.STABILITY,
            sample_count=10
        )

        anomaly = detect_feel_anomaly(default_felt_state, 'opening', traj)
        assert anomaly is None

    def test_no_anomaly_insufficient_samples(self, threat_felt_state):
        """Test no anomaly detected with insufficient samples."""
        traj = GameFeelTrajectory(
            game_id='test',
            typical_opening_valence=Valence.STABILITY,
            sample_count=3  # Less than 5
        )

        anomaly = detect_feel_anomaly(threat_felt_state, 'opening', traj)
        assert anomaly is None

    def test_anomaly_detected_severe(self, threat_felt_state):
        """Test severe anomaly is detected."""
        traj = GameFeelTrajectory(
            game_id='test',
            typical_opening_valence=Valence.STABILITY,
            sample_count=10,
            variance_by_phase={'opening': 0.1, 'midgame': 0.3, 'resolution': 0.2}
        )

        anomaly = detect_feel_anomaly(threat_felt_state, 'opening', traj)

        assert anomaly is not None
        assert anomaly.expected_valence == Valence.STABILITY
        assert anomaly.actual_valence == Valence.THREAT
        assert anomaly.severity > 0.5

    def test_anomaly_reduced_by_high_variance(self, threat_felt_state):
        """Test anomaly severity reduced when high variance is normal."""
        traj = GameFeelTrajectory(
            game_id='test',
            typical_opening_valence=Valence.STABILITY,
            sample_count=10,
            variance_by_phase={'opening': 0.8, 'midgame': 0.3, 'resolution': 0.2}
        )

        anomaly = detect_feel_anomaly(threat_felt_state, 'opening', traj)

        # Should still detect but with lower severity
        if anomaly:
            assert anomaly.severity < 0.7


# ============================================================================
# TEST: FeelTrajectoryStore
# ============================================================================

class TestFeelTrajectoryStore:
    """Tests for FeelTrajectoryStore."""

    def test_get_or_create_new(self):
        """Test creating new trajectory."""
        store = FeelTrajectoryStore()

        traj = store.get_or_create('game_1')

        assert traj.game_id == 'game_1'
        assert 'game_1' in store.trajectories

    def test_get_or_create_existing(self):
        """Test getting existing trajectory."""
        store = FeelTrajectoryStore()

        traj1 = store.get_or_create('game_1')
        traj1.sample_count = 5

        traj2 = store.get_or_create('game_1')

        assert traj2.sample_count == 5
        assert traj1 is traj2

    def test_record_playthrough(self):
        """Test recording playthrough through store."""
        store = FeelTrajectoryStore()

        traj = store.record_playthrough(
            'game_1',
            Valence.CONFUSION,
            Valence.OPPORTUNITY,
            Valence.STABILITY
        )

        assert traj.sample_count == 1

    def test_detect_anomaly(self, threat_felt_state):
        """Test anomaly detection through store."""
        store = FeelTrajectoryStore()

        # Build up trajectory
        for _ in range(10):
            store.record_playthrough(
                'game_1',
                Valence.BOREDOM,
                Valence.OPPORTUNITY,
                Valence.STABILITY
            )

        # Check for anomaly (THREAT instead of BOREDOM)
        anomaly = store.detect_anomaly('game_1', threat_felt_state, 'opening')

        assert anomaly is not None
        assert anomaly.expected_valence == Valence.BOREDOM

    def test_get_games_by_typical_opening(self):
        """Test finding games by typical opening valence."""
        store = FeelTrajectoryStore()

        # Create games with different typical openings
        traj1 = store.get_or_create('game_1')
        traj1.typical_opening_valence = Valence.BOREDOM

        traj2 = store.get_or_create('game_2')
        traj2.typical_opening_valence = Valence.CONFUSION

        traj3 = store.get_or_create('game_3')
        traj3.typical_opening_valence = Valence.BOREDOM

        boredom_games = store.get_games_by_typical_opening(Valence.BOREDOM)

        assert len(boredom_games) == 2
        assert 'game_1' in boredom_games
        assert 'game_3' in boredom_games

    def test_statistics(self):
        """Test store statistics."""
        store = FeelTrajectoryStore()

        # Empty stats
        stats = store.get_statistics()
        assert stats['total_games'] == 0

        # Add some data
        for _ in range(3):
            store.record_playthrough('game_1', Valence.BOREDOM, Valence.OPPORTUNITY, Valence.STABILITY)
        for _ in range(7):
            store.record_playthrough('game_2', Valence.CONFUSION, Valence.THREAT, Valence.STABILITY)

        stats = store.get_statistics()
        assert stats['total_games'] == 2
        assert stats['total_playthroughs'] == 10
        assert stats['avg_playthroughs_per_game'] == 5.0

    def test_serialization_round_trip(self):
        """Test store serialization."""
        store = FeelTrajectoryStore()

        for _ in range(5):
            store.record_playthrough('game_1', Valence.BOREDOM, Valence.OPPORTUNITY, Valence.STABILITY)

        data = store.to_dict()
        restored = FeelTrajectoryStore.from_dict(data)

        assert 'game_1' in restored.trajectories
        assert restored.trajectories['game_1'].sample_count == 5


# ============================================================================
# TEST: Integration with Phenomenology Layer
# ============================================================================

class TestPhenomenologyIntegration:
    """Tests for integration with phenomenology layer."""

    def test_felt_state_captures_discovery_context(self, graph, threat_felt_state, boredom_felt_state):
        """Test that FeltState context is properly captured in edges."""
        # Discover path under threat
        graph.record_traversal('panic_a', 'panic_b', success=True, felt_state=threat_felt_state)

        # Discover path under boredom
        graph.record_traversal('explore_a', 'explore_b', success=True, felt_state=boredom_felt_state)

        panic_edge = graph.get_edge('panic_a', 'panic_b')
        explore_edge = graph.get_edge('explore_a', 'explore_b')

        assert panic_edge.discovery_valence == Valence.THREAT
        assert panic_edge.discovery_arousal == 0.8

        assert explore_edge.discovery_valence == Valence.BOREDOM
        assert explore_edge.discovery_arousal == 0.2

    def test_threshold_differences_by_valence(self, graph, threat_felt_state, confusion_felt_state, boredom_felt_state):
        """Test that different valences produce different thresholds."""
        # Create edges under different emotional states
        for felt, prefix in [
            (threat_felt_state, 'threat'),
            (confusion_felt_state, 'confusion'),
            (boredom_felt_state, 'boredom')
        ]:
            edge = graph.record_traversal(f'{prefix}_a', f'{prefix}_b', success=True, felt_state=felt)
            # Give boredom high success for fast-track
            if prefix == 'boredom':
                for _ in range(9):
                    graph.record_traversal(f'{prefix}_a', f'{prefix}_b', success=True, felt_state=felt)

        threat_edge = graph.get_edge('threat_a', 'threat_b')
        confusion_edge = graph.get_edge('confusion_a', 'confusion_b')
        boredom_edge = graph.get_edge('boredom_a', 'boredom_b')

        # Confusion requires most validation
        assert confusion_edge.valence_adjusted_crystallization_threshold > threat_edge.valence_adjusted_crystallization_threshold

        # Threat requires more than boredom (with high success)
        assert threat_edge.valence_adjusted_crystallization_threshold > boredom_edge.valence_adjusted_crystallization_threshold
