#!/usr/bin/env python3
"""
Tests for I-Thread and Two Streams Consciousness Implementation

Tests the following consciousness theory components:
1. I-Thread: w_A/w_B weight management and learning
2. Stream conflict detection
3. Synthesis with surprise scoring
4. Role-based weight resets
5. Personality development tracking

Per Rule 15: Tests in tests/ folder are preserved and exempt from "No Test Files" rule.
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

from engines.consciousness.i_thread import (
    IThread, 
    IThreadState, 
    StreamProposal, 
    ConflictResult,
    SynthesisResult,
    ROLE_DEFAULT_WEIGHTS,
    CONFLICT_THRESHOLD,
    compute_surprise
)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from database_interface import DatabaseInterface


class MockDatabaseInterface:
    """Mock database for testing without real DB access."""
    
    def __init__(self):
        self.queries = []
        self.agent_data = {}
        self.history = []
    
    def execute_query(self, query: str, params=None):
        self.queries.append((query, params))
        
        # Mock SELECT self_network_bias
        if 'SELECT self_network_bias FROM agents' in query:
            agent_id = params[0] if params else None
            if agent_id in self.agent_data:
                return [{'self_network_bias': self.agent_data[agent_id]}]
            return [{'self_network_bias': 0.5}]
        
        # Mock UPDATE self_network_bias
        if 'UPDATE agents SET self_network_bias' in query:
            if params and len(params) >= 2:
                self.agent_data[params[1]] = params[0]
            return None
        
        # Mock INSERT INTO i_thread_history
        if 'INSERT INTO i_thread_history' in query:
            self.history.append(params)
            return None
        
        # Mock COUNT queries
        if 'COUNT(*)' in query:
            return [{'total_conflicts': 0, 'stream_a_wins': 0, 'stream_b_wins': 0}]
        
        # Mock CREATE TABLE (always succeeds)
        if 'CREATE TABLE' in query or 'CREATE INDEX' in query:
            return None
        
        return []


class TestIThreadState(unittest.TestCase):
    """Test IThreadState dataclass."""
    
    def test_default_state(self):
        """Default state should have balanced weights."""
        state = IThreadState(agent_id='test_agent')
        self.assertEqual(state.w_a, 0.5)
        self.assertEqual(state.w_b, 0.5)
        self.assertEqual(state.personality_label, 'balanced')
    
    def test_custom_state(self):
        """Custom weights should be stored correctly."""
        state = IThreadState(
            agent_id='pioneer_agent',
            w_a=0.7,
            w_b=0.3,
            personality_label='self-trusting'
        )
        self.assertEqual(state.w_a, 0.7)
        self.assertEqual(state.w_b, 0.3)


class TestStreamProposal(unittest.TestCase):
    """Test StreamProposal dataclass."""
    
    def test_stream_proposal_creation(self):
        """StreamProposal should store action and confidence."""
        proposal = StreamProposal(
            action='ACTION1',
            confidence=0.8,
            source='stream_a',
            reasoning='Based on past experience'
        )
        self.assertEqual(proposal.action, 'ACTION1')
        self.assertEqual(proposal.confidence, 0.8)
        self.assertEqual(proposal.source, 'stream_a')


class TestIThread(unittest.TestCase):
    """Test IThread class functionality."""
    
    def setUp(self):
        """Set up mock database and IThread instance."""
        self.mock_db = MockDatabaseInterface()
        self.i_thread = IThread(self.mock_db)  # type: ignore[arg-type]
    
    def test_initialization(self):
        """IThread should initialize with empty cache."""
        self.assertEqual(len(self.i_thread._state_cache), 0)
    
    def test_get_state_default(self):
        """get_state should return balanced weights for unknown agent."""
        state = self.i_thread.get_state('new_agent')
        self.assertEqual(state.agent_id, 'new_agent')
        self.assertEqual(state.w_a, 0.5)
        self.assertEqual(state.w_b, 0.5)
    
    def test_get_state_cached(self):
        """get_state should cache and return same instance."""
        state1 = self.i_thread.get_state('test_agent')
        state2 = self.i_thread.get_state('test_agent')
        self.assertIs(state1, state2)  # Same object
    
    def test_get_state_from_database(self):
        """get_state should load w_b from database."""
        self.mock_db.agent_data['db_agent'] = 0.7  # w_b stored in DB
        state = self.i_thread.get_state('db_agent')
        self.assertEqual(state.w_b, 0.7)
        self.assertAlmostEqual(state.w_a, 0.3, places=5)  # w_a = 1.0 - w_b


class TestConflictDetection(unittest.TestCase):
    """Test stream conflict detection."""
    
    def setUp(self):
        self.mock_db = MockDatabaseInterface()
        self.i_thread = IThread(self.mock_db)  # type: ignore[arg-type]
    
    def test_no_conflict_same_action(self):
        """Same action = no conflict."""
        proposal_a = StreamProposal('ACTION1', 0.8, 'stream_a')
        proposal_b = StreamProposal('ACTION1', 0.9, 'stream_b')
        
        result = self.i_thread.detect_conflict(proposal_a, proposal_b)
        
        self.assertFalse(result.has_conflict)
        self.assertEqual(result.conflict_score, 0.0)
        self.assertEqual(result.consciousness_intensity, 'automatic')
    
    def test_conflict_different_actions(self):
        """Different actions with high confidence = conflict."""
        proposal_a = StreamProposal('ACTION1', 0.8, 'stream_a')
        proposal_b = StreamProposal('ACTION2', 0.8, 'stream_b')
        
        result = self.i_thread.detect_conflict(proposal_a, proposal_b)
        
        self.assertTrue(result.has_conflict)
        self.assertGreater(result.conflict_score, CONFLICT_THRESHOLD)
        self.assertIn(result.consciousness_intensity, ['deliberative', 'vivid'])
    
    def test_low_confidence_low_conflict(self):
        """Different actions with low confidence = weaker conflict."""
        proposal_a = StreamProposal('ACTION1', 0.2, 'stream_a')
        proposal_b = StreamProposal('ACTION2', 0.2, 'stream_b')
        
        result = self.i_thread.detect_conflict(proposal_a, proposal_b)
        
        # Low confidence means lower conflict score
        self.assertLess(result.conflict_score, 0.5)


class TestSynthesis(unittest.TestCase):
    """Test I-Thread synthesis of stream proposals."""
    
    def setUp(self):
        self.mock_db = MockDatabaseInterface()
        self.i_thread = IThread(self.mock_db)  # type: ignore[arg-type]
    
    def test_synthesis_high_w_a_chooses_stream_a(self):
        """High w_A should favor Stream A proposal."""
        state = IThreadState(agent_id='test', w_a=0.8, w_b=0.2)
        proposal_a = StreamProposal('ACTION1', 0.7, 'stream_a')
        proposal_b = StreamProposal('ACTION2', 0.7, 'stream_b')
        
        result = self.i_thread.synthesize(state, proposal_a, proposal_b)
        
        self.assertEqual(result.chosen_action, 'ACTION1')
        self.assertEqual(result.chosen_source, 'stream_a')
    
    def test_synthesis_high_w_b_chooses_stream_b(self):
        """High w_B should favor Stream B proposal."""
        state = IThreadState(agent_id='test', w_a=0.2, w_b=0.8)
        proposal_a = StreamProposal('ACTION1', 0.7, 'stream_a')
        proposal_b = StreamProposal('ACTION2', 0.7, 'stream_b')
        
        result = self.i_thread.synthesize(state, proposal_a, proposal_b)
        
        self.assertEqual(result.chosen_action, 'ACTION2')
        self.assertEqual(result.chosen_source, 'stream_b')
    
    def test_synthesis_confidence_can_override_weight(self):
        """Very high confidence can overcome lower weight."""
        state = IThreadState(agent_id='test', w_a=0.3, w_b=0.7)
        proposal_a = StreamProposal('ACTION1', 0.95, 'stream_a')  # High confidence
        proposal_b = StreamProposal('ACTION2', 0.2, 'stream_b')   # Low confidence
        
        result = self.i_thread.synthesize(state, proposal_a, proposal_b)
        
        # score_a = 0.95 * 0.3 = 0.285
        # score_b = 0.2 * 0.7 = 0.14
        # Stream A should win despite lower weight
        self.assertEqual(result.chosen_action, 'ACTION1')
        self.assertGreater(result.surprise_score, 0)  # Underdog won = surprise
    
    def test_synthesis_deliberation_on_conflict(self):
        """Deliberation should be required when streams conflict."""
        state = IThreadState(agent_id='test', w_a=0.5, w_b=0.5)
        proposal_a = StreamProposal('ACTION1', 0.8, 'stream_a')
        proposal_b = StreamProposal('ACTION2', 0.8, 'stream_b')
        
        result = self.i_thread.synthesize(state, proposal_a, proposal_b)
        
        self.assertTrue(result.deliberation_required)


class TestLearning(unittest.TestCase):
    """Test I-Thread learning from outcomes."""
    
    def setUp(self):
        self.mock_db = MockDatabaseInterface()
        self.i_thread = IThread(self.mock_db)  # type: ignore[arg-type]
    
    def test_positive_outcome_increases_chosen_stream_weight(self):
        """Positive outcome for stream_a should increase w_a."""
        self.mock_db.agent_data['learner'] = 0.5  # Start balanced
        state = self.i_thread.get_state('learner')
        initial_w_a = state.w_a
        
        new_w_a, new_w_b = self.i_thread.learn_from_outcome(
            agent_id='learner',
            chosen_source='stream_a',
            outcome='positive'
        )
        
        self.assertGreater(new_w_a, initial_w_a)
        self.assertLess(new_w_b, 0.5)
    
    def test_negative_outcome_decreases_chosen_stream_weight(self):
        """Negative outcome for stream_a should decrease w_a."""
        self.mock_db.agent_data['learner'] = 0.5
        state = self.i_thread.get_state('learner')
        initial_w_a = state.w_a
        
        new_w_a, new_w_b = self.i_thread.learn_from_outcome(
            agent_id='learner',
            chosen_source='stream_a',
            outcome='negative'
        )
        
        self.assertLess(new_w_a, initial_w_a)
        self.assertGreater(new_w_b, 0.5)
    
    def test_neutral_outcome_no_change(self):
        """Neutral outcome should not change weights."""
        self.mock_db.agent_data['learner'] = 0.5
        
        new_w_a, new_w_b = self.i_thread.learn_from_outcome(
            agent_id='learner',
            chosen_source='stream_a',
            outcome='neutral'
        )
        
        self.assertEqual(new_w_a, 0.5)
        self.assertEqual(new_w_b, 0.5)
    
    def test_weights_bounded(self):
        """Weights should stay within 0.1-0.9 bounds."""
        self.mock_db.agent_data['extreme'] = 0.9  # w_b very high
        
        # Try to push w_a even lower
        for _ in range(20):
            self.i_thread.learn_from_outcome(
                agent_id='extreme',
                chosen_source='stream_a',
                outcome='negative'
            )
        
        state = self.i_thread.get_state('extreme')
        self.assertGreaterEqual(state.w_a, 0.1)
        self.assertLessEqual(state.w_b, 0.9)


class TestRoleTransitions(unittest.TestCase):
    """Test role-based weight resets."""
    
    def setUp(self):
        self.mock_db = MockDatabaseInterface()
        self.i_thread = IThread(self.mock_db)  # type: ignore[arg-type]
    
    def test_pioneer_role_reset(self):
        """Pioneer should get high w_A (0.7)."""
        self.mock_db.agent_data['agent'] = 0.5
        
        new_w_a, new_w_b = self.i_thread.reset_for_role_change('agent', 'pioneer')
        
        self.assertEqual(new_w_a, 0.7)
        self.assertEqual(new_w_b, 0.3)
    
    def test_optimizer_role_reset(self):
        """Optimizer should get high w_B (0.7)."""
        new_w_a, new_w_b = self.i_thread.reset_for_role_change('agent', 'optimizer')
        
        self.assertEqual(new_w_a, 0.3)
        self.assertEqual(new_w_b, 0.7)
    
    def test_generalist_role_reset(self):
        """Generalist should get balanced weights."""
        new_w_a, new_w_b = self.i_thread.reset_for_role_change('agent', 'generalist')
        
        self.assertEqual(new_w_a, 0.5)
        self.assertEqual(new_w_b, 0.5)
    
    def test_all_roles_have_defaults(self):
        """All defined roles should have default weights."""
        for role in ['pioneer', 'optimizer', 'generalist', 'exploiter']:
            self.assertIn(role, ROLE_DEFAULT_WEIGHTS)


class TestPersonalitySummary(unittest.TestCase):
    """Test personality analysis."""
    
    def setUp(self):
        self.mock_db = MockDatabaseInterface()
        self.i_thread = IThread(self.mock_db)  # type: ignore[arg-type]
    
    def test_personality_summary_structure(self):
        """Personality summary should have required fields."""
        summary = self.i_thread.get_personality_summary('test_agent')
        
        required_fields = [
            'agent_id', 'w_a', 'w_b', 'personality_label',
            'total_conflicts_resolved', 'stream_a_win_rate', 'stream_b_win_rate'
        ]
        
        for field in required_fields:
            self.assertIn(field, summary)
    
    def test_personality_label_self_trusting(self):
        """High w_A should give 'self-trusting' label."""
        self.mock_db.agent_data['pioneer'] = 0.3  # w_b low = w_a high
        summary = self.i_thread.get_personality_summary('pioneer')
        
        self.assertEqual(summary['personality_label'], 'self-trusting')
    
    def test_personality_label_network_trusting(self):
        """High w_B should give 'network-trusting' label."""
        self.mock_db.agent_data['optimizer'] = 0.8  # w_b high
        summary = self.i_thread.get_personality_summary('optimizer')
        
        self.assertEqual(summary['personality_label'], 'network-trusting')


class TestComputeSurprise(unittest.TestCase):
    """Test surprise computation function."""
    
    def test_no_surprise_expected_winner(self):
        """Expected winner = low surprise."""
        surprise = compute_surprise(
            stream_a_confidence=0.8,
            stream_b_confidence=0.5,
            chosen_source='stream_a',  # Expected winner (higher confidence, higher weight)
            w_a=0.7,
            w_b=0.3
        )
        
        self.assertLess(surprise, 0.3)
    
    def test_high_surprise_underdog_wins(self):
        """Underdog winning = high surprise."""
        surprise = compute_surprise(
            stream_a_confidence=0.8,
            stream_b_confidence=0.8,
            chosen_source='stream_a',  # Won despite lower weight
            w_a=0.3,  # Underdog
            w_b=0.7
        )
        
        self.assertGreater(surprise, 0.2)
    
    def test_surprise_bounded(self):
        """Surprise should be bounded 0-1."""
        surprise = compute_surprise(
            stream_a_confidence=1.0,
            stream_b_confidence=1.0,
            chosen_source='stream_a',
            w_a=0.1,
            w_b=0.9
        )
        
        self.assertLessEqual(surprise, 1.0)
        self.assertGreaterEqual(surprise, 0.0)


class TestCacheManagement(unittest.TestCase):
    """Test cache clearing functionality."""
    
    def setUp(self):
        self.mock_db = MockDatabaseInterface()
        self.i_thread = IThread(self.mock_db)  # type: ignore[arg-type]
    
    def test_clear_single_agent_cache(self):
        """clear_cache should remove specific agent."""
        self.i_thread.get_state('agent1')
        self.i_thread.get_state('agent2')
        
        self.i_thread.clear_cache('agent1')
        
        self.assertNotIn('agent1', self.i_thread._state_cache)
        self.assertIn('agent2', self.i_thread._state_cache)
    
    def test_clear_all_cache(self):
        """clear_cache without agent should clear all."""
        self.i_thread.get_state('agent1')
        self.i_thread.get_state('agent2')
        
        self.i_thread.clear_cache()
        
        self.assertEqual(len(self.i_thread._state_cache), 0)


if __name__ == '__main__':
    unittest.main()
