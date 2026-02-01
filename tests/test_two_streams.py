#!/usr/bin/env python3
"""
Tests for Two Streams Architecture in Sensation Engine

Tests the consciousness theory implementation:
1. Stream A (private experience) vs Stream B (collective wisdom)
2. Synthesis with surprise scoring
3. Stream conflict detection
4. Consciousness intensity levels

Per Rule 15: Tests in tests/ folder are preserved.
"""

import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class MockDatabaseInterface:
    """Mock database for testing sensation engine without real DB."""

    def __init__(self):
        self.queries = []
        self.impressions = {}

    def execute_query(self, query: str, params=None):
        self.queries.append((query, params))

        # Mock sensation impression query
        if 'SELECT' in query and 'sensation_impressions' in query.lower():
            if params and params[0] in self.impressions:
                return [self.impressions[params[0]]]
            return []

        # Mock CREATE TABLE
        if 'CREATE TABLE' in query or 'CREATE INDEX' in query:
            return None

        return []

    def add_impression(self, agent_id: str, data: dict):
        """Add mock impression data."""
        self.impressions[agent_id] = data


class TestSynthesisWithSurprise(unittest.TestCase):
    """Test synthesis calculation with surprise scoring."""

    def setUp(self):
        """Set up sensation engine with mock DB."""
        self.mock_db = MockDatabaseInterface()

        # Import here to allow mocking
        from engines.consciousness.sensation_engine import SensationEngine
        self.engine = SensationEngine(self.mock_db)  # type: ignore[arg-type]

    def test_synthesis_includes_surprise_score(self):
        """Synthesis should include surprise_score field."""
        stream_a = {'goal_relevance': 0.8, 'threat_level': 0.1, 'approach_score': 0.7}
        stream_b = {'network_goal_relevance': 0.3, 'network_threat_level': 0.2, 'network_approach_score': 0.4}
        hypothesis = {'control_correlation': 0.5}

        synthesis = self.engine._calculate_synthesis(
            agent_id='test',
            object_type='target',
            stream_a=stream_a,
            stream_b=stream_b,
            hypothesis=hypothesis,
            w_a=0.6,
            w_b=0.4
        )

        self.assertIn('surprise_score', synthesis)
        self.assertIn('consciousness_intensity', synthesis)
        self.assertIn('stream_disagreement', synthesis)

    def test_high_disagreement_high_surprise(self):
        """High stream disagreement should produce high surprise."""
        # Streams strongly disagree
        stream_a = {'goal_relevance': 1.0, 'threat_level': 0.0, 'approach_score': 1.0}
        stream_b = {'network_goal_relevance': 0.0, 'network_threat_level': 1.0, 'network_approach_score': 0.0}
        hypothesis = {'control_correlation': 0.0}

        synthesis = self.engine._calculate_synthesis(
            agent_id='test',
            object_type='target',
            stream_a=stream_a,
            stream_b=stream_b,
            hypothesis=hypothesis,
            w_a=0.5,
            w_b=0.5
        )

        self.assertGreater(synthesis['surprise_score'], 0.3)
        self.assertIn(synthesis['consciousness_intensity'], ['deliberative', 'vivid'])

    def test_agreement_low_surprise(self):
        """Streams agreeing should produce low surprise."""
        # Streams agree
        stream_a = {'goal_relevance': 0.7, 'threat_level': 0.2, 'approach_score': 0.6}
        stream_b = {'network_goal_relevance': 0.7, 'network_threat_level': 0.2, 'network_approach_score': 0.6}
        hypothesis = {'control_correlation': 0.0}

        synthesis = self.engine._calculate_synthesis(
            agent_id='test',
            object_type='target',
            stream_a=stream_a,
            stream_b=stream_b,
            hypothesis=hypothesis,
            w_a=0.5,
            w_b=0.5
        )

        self.assertLess(synthesis['surprise_score'], 0.3)
        self.assertEqual(synthesis['consciousness_intensity'], 'automatic')

    def test_underdog_stream_wins_surprise(self):
        """When low-weight stream dominates, surprise should increase."""
        # Stream A has low weight but high approach score
        stream_a = {'goal_relevance': 0.5, 'threat_level': 0.1, 'approach_score': 0.9}
        stream_b = {'network_goal_relevance': 0.5, 'network_threat_level': 0.1, 'network_approach_score': 0.2}
        hypothesis = {'control_correlation': 0.0}

        synthesis = self.engine._calculate_synthesis(
            agent_id='test',
            object_type='target',
            stream_a=stream_a,
            stream_b=stream_b,
            hypothesis=hypothesis,
            w_a=0.3,  # Low weight
            w_b=0.7   # High weight but low contribution
        )

        # Stream A contribution = 0.9 * 0.3 = 0.27
        # Stream B contribution = 0.2 * 0.7 = 0.14
        # Stream A wins despite lower weight = underdog surprise
        self.assertGreater(synthesis['surprise_score'], 0)

    def test_synthesis_preserves_legacy_fields(self):
        """Synthesis should still include legacy semantic role fields."""
        stream_a = {'goal_relevance': 0.8, 'threat_level': 0.0, 'approach_score': 0.5}
        stream_b = {'network_goal_relevance': 0.5, 'network_threat_level': 0.0, 'network_approach_score': 0.5}
        hypothesis = {'control_correlation': 0.9}  # High = controlled object

        synthesis = self.engine._calculate_synthesis(
            agent_id='test',
            object_type='controlled',
            stream_a=stream_a,
            stream_b=stream_b,
            hypothesis=hypothesis,
            w_a=0.5,
            w_b=0.5
        )

        # Legacy fields should still exist
        self.assertIn('semantic_role', synthesis)
        self.assertIn('is_self', synthesis)
        self.assertIn('attraction', synthesis)

        # High control = self
        self.assertEqual(synthesis['semantic_role'], 'self')
        self.assertTrue(synthesis['is_self'])


class TestTetrahedralSensation(unittest.TestCase):
    """Test full tetrahedral sensation with streams."""

    def setUp(self):
        self.mock_db = MockDatabaseInterface()
        from engines.consciousness.sensation_engine import SensationEngine
        self.engine = SensationEngine(self.mock_db)  # type: ignore[arg-type]

    def test_tetrahedral_returns_both_streams(self):
        """get_tetrahedral_sensation should return stream_a and stream_b."""
        object_info = {
            'object_type': 'target_color_5',
            'position': (3, 4),
            'color': 5
        }

        result = self.engine.get_tetrahedral_sensation(
            agent_id='test_agent',
            object_info=object_info,
            w_a=0.6,
            w_b=0.4
        )

        self.assertIn('stream_a', result)
        self.assertIn('stream_b', result)
        self.assertIn('synthesis', result)
        self.assertIn('stream_conflict', result)
        self.assertIn('dominant_stream', result)

    def test_stream_conflict_calculation(self):
        """Stream conflict should be calculated from disagreement."""
        # This test verifies the conflict is computed
        object_info = {
            'object_type': 'unknown_object',
            'position': (0, 0),
            'color': 0
        }

        result = self.engine.get_tetrahedral_sensation(
            agent_id='test_agent',
            object_info=object_info,
            w_a=0.5,
            w_b=0.5
        )

        # Conflict should be a float between 0 and 1
        self.assertIsInstance(result['stream_conflict'], float)
        self.assertGreaterEqual(result['stream_conflict'], 0.0)
        self.assertLessEqual(result['stream_conflict'], 1.0)

    def test_dominant_stream_based_on_weights(self):
        """Dominant stream should reflect weight imbalance."""
        object_info = {'object_type': 'test', 'position': (0, 0), 'color': 0}

        # High w_a
        result_a = self.engine.get_tetrahedral_sensation(
            'agent', object_info, w_a=0.8, w_b=0.2
        )
        self.assertEqual(result_a['dominant_stream'], 'stream_a')

        # High w_b
        result_b = self.engine.get_tetrahedral_sensation(
            'agent', object_info, w_a=0.2, w_b=0.8
        )
        self.assertEqual(result_b['dominant_stream'], 'stream_b')

        # Balanced
        result_balanced = self.engine.get_tetrahedral_sensation(
            'agent', object_info, w_a=0.5, w_b=0.5
        )
        self.assertEqual(result_balanced['dominant_stream'], 'balanced')


class TestConsciousnessIntensity(unittest.TestCase):
    """Test consciousness intensity levels from theory."""

    def setUp(self):
        self.mock_db = MockDatabaseInterface()
        from engines.consciousness.sensation_engine import SensationEngine
        self.engine = SensationEngine(self.mock_db)  # type: ignore[arg-type]

    def test_automatic_intensity(self):
        """Low surprise should produce 'automatic' intensity."""
        stream_a = {'goal_relevance': 0.5, 'threat_level': 0.1, 'approach_score': 0.5}
        stream_b = {'network_goal_relevance': 0.5, 'network_threat_level': 0.1, 'network_approach_score': 0.5}
        hypothesis = {}

        synthesis = self.engine._calculate_synthesis(
            'agent', 'obj', stream_a, stream_b, hypothesis, 0.5, 0.5
        )

        self.assertEqual(synthesis['consciousness_intensity'], 'automatic')

    def test_deliberative_intensity(self):
        """Moderate surprise should produce 'deliberative' intensity."""
        # Higher disagreement to trigger deliberative (need surprise >= 0.3)
        # Need stream_disagreement >= 0.5 to get surprise = 0.5 * 0.6 = 0.3
        stream_a = {'goal_relevance': 1.0, 'threat_level': 0.0, 'approach_score': 0.6}
        stream_b = {'network_goal_relevance': 0.3, 'network_threat_level': 0.6, 'network_approach_score': 0.3}
        hypothesis = {}

        synthesis = self.engine._calculate_synthesis(
            'agent', 'obj', stream_a, stream_b, hypothesis, 0.5, 0.5
        )

        # Should be either deliberative or vivid based on exact disagreement
        self.assertIn(synthesis['consciousness_intensity'], ['deliberative', 'vivid'])

    def test_vivid_intensity(self):
        """High surprise should produce 'vivid' intensity."""
        # Complete disagreement
        stream_a = {'goal_relevance': 1.0, 'threat_level': 0.0, 'approach_score': 1.0}
        stream_b = {'network_goal_relevance': 0.0, 'network_threat_level': 1.0, 'network_approach_score': 0.0}
        hypothesis = {}

        synthesis = self.engine._calculate_synthesis(
            'agent', 'obj', stream_a, stream_b, hypothesis, 0.5, 0.5
        )

        self.assertEqual(synthesis['consciousness_intensity'], 'vivid')


class TestStreamDocumentation(unittest.TestCase):
    """Test that module documentation describes Two Streams."""

    def test_module_docstring_mentions_streams(self):
        """Sensation engine docstring should document Two Streams."""
        import engines.consciousness.sensation_engine as sensation_engine
        from engines.consciousness.sensation_engine import SensationEngine

        docstring = sensation_engine.__doc__

        # Module docstring must exist and describe Two Streams
        self.assertIsNotNone(docstring, "sensation_engine should have a module docstring")
        assert docstring is not None  # Type narrowing for Pylance

        # Module docstring uses uppercase "STREAM A/B" format
        self.assertIn('STREAM A', docstring)
        self.assertIn('STREAM B', docstring)
        self.assertIn('Private Experience', docstring)
        self.assertIn('Collective', docstring)
        self.assertIn('i_thread', docstring)


if __name__ == '__main__':
    unittest.main()
