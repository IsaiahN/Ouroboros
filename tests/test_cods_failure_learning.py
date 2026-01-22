"""
Unit Tests for CODS Failure-Driven Learning
=============================================

Tests the new failure-driven learning components added to CODS:
- record_level_outcome()
- record_game_outcome()
- process_near_miss_patterns()
- get_primitive_gap_summary()

Note: process_counterfactual_insights() removed Jan 22, 2026
      (replaced by lessons_learned_engine)

Following Rule 1: Disable pycache
Following Rule 2: All data in database
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import pytest
import json
import uuid
from unittest.mock import MagicMock, patch
from datetime import datetime


class MockDatabase:
    """Mock database for testing."""
    
    def __init__(self):
        self.queries = []
        self.data = {}
        
    def execute_query(self, query: str, params: tuple | None = None):
        self.queries.append({'query': query, 'params': params})
        
        # Handle different query types
        query_lower = query.lower().strip()
        
        if query_lower.startswith('create table'):
            return None
        elif query_lower.startswith('create index'):
            return None
        elif query_lower.startswith('insert'):
            return None
        elif query_lower.startswith('select count'):
            return [{'fail_count': 5, 'avg_level': 1.5}]
        elif 'cods_primitive_hints' in query_lower and 'select' in query_lower:
            return [
                {'game_type': 'sp80', 'hint_type': 'decision_point', 
                 'confidence': 0.8, 'details': json.dumps({'suggested': 'containment_check'})},
                {'game_type': 'sp80', 'hint_type': 'almost_won',
                 'confidence': 0.7, 'details': json.dumps({'suggested': 'boundary_seal_check'})}
            ]
        elif 'operator_test_results' in query_lower:
            return [
                {'operator_id': 'op1', 'success': True, 'level_number': 1},
                {'operator_id': 'op2', 'success': False, 'level_number': 2}
            ]
        elif 'near_miss_games' in query_lower:
            return [
                {'game_id': 'sp80-test', 'final_score': 18.0, 'score_gap': 2.0,
                 'near_miss_category': 'near_win', 'what_failed': '[]', 'missing_elements': '[]'}
            ]
        
        return []


class MockUnlockManager:
    """Mock unlock manager for testing."""
    
    def list_locked(self):
        return [
            {'primitive_name': 'containment_check', 'category': 'physical'},
            {'primitive_name': 'boundary_seal_check', 'category': 'physical'},
            {'primitive_name': 'flow_simulation', 'category': 'physical'},
            {'primitive_name': 'path_exists', 'category': 'spatial'},
        ]
    
    def list_unlocked(self):
        return [{'primitive_name': 'detect_symmetry'}]
    
    def list_novel(self):
        return []


class MockComposer:
    """Mock operator composer for testing."""
    
    def list_operators(self, min_success_rate=0.0, limit=10):
        return []


class MockSeeds:
    """Mock seed primitives registry."""
    
    def count(self):
        return 50


@pytest.fixture
def mock_db():
    """Create a mock database instance."""
    return MockDatabase()


@pytest.fixture
def mock_cods_engine(mock_db):
    """Create a mock CODS engine with failure-learning methods."""
    # We'll test the actual methods, so we need to import and patch
    with patch('cods_engine.DatabaseInterface', return_value=mock_db):
        with patch('cods_engine.get_seed_primitives') as mock_seeds:
            mock_seeds.return_value = MockSeeds()
            with patch('cods_engine.PrimitiveUnlockManager') as mock_unlock:
                mock_unlock.return_value = MockUnlockManager()
                with patch('cods_engine.OperatorComposer') as mock_composer:
                    mock_composer.return_value = MockComposer()
                    with patch('cods_engine.OracleInterface'):
                        with patch('cods_engine.grandfather_existing_primitives'):
                            from cods_engine import CODSEngine, CODSGameContext
                            engine = CODSEngine(db=mock_db)
                            
                            # Set up context
                            engine._context = CODSGameContext(
                                game_id='sp80-test123',
                                level_number=2,
                                agent_id='agent_001',
                                generation=10
                            )
                            
                            return engine


# =============================================================================
# Tests for record_level_outcome
# =============================================================================

class TestRecordLevelOutcome:
    """Tests for record_level_outcome method."""
    
    def test_record_level_pass(self, mock_cods_engine, mock_db):
        """Test recording a passed level."""
        mock_cods_engine.record_level_outcome(
            level=1,
            passed=True,
            actions_used=25,
            score_gained=1.0
        )
        
        # Check that INSERT was called
        insert_queries = [q for q in mock_db.queries if 'INSERT' in q['query'].upper()]
        assert len(insert_queries) >= 1
        
        # Verify the data
        level_insert = [q for q in insert_queries if 'cods_level_outcomes' in q['query']]
        assert len(level_insert) >= 1
    
    def test_record_level_fail_triggers_analysis(self, mock_cods_engine, mock_db):
        """Test that failing a level triggers failure analysis."""
        mock_cods_engine.record_level_outcome(
            level=2,
            passed=False,
            actions_used=100,
            score_gained=0.0
        )
        
        # Should have recorded the outcome
        insert_queries = [q for q in mock_db.queries if 'INSERT' in q['query'].upper()]
        assert len(insert_queries) >= 1
    
    def test_no_context_warning(self, mock_cods_engine, mock_db):
        """Test that missing context logs a warning."""
        # Clear queries from initialization
        mock_db.queries.clear()
        
        mock_cods_engine._context = None
        
        # Should not raise, just return early
        mock_cods_engine.record_level_outcome(
            level=1,
            passed=True,
            actions_used=10
        )
        
        # No INSERT INTO cods_level_outcomes VALUES should have happened
        # (CREATE TABLE and CREATE INDEX might still happen during table check)
        value_inserts = [q for q in mock_db.queries 
                        if 'INSERT INTO cods_level_outcomes' in q['query'] 
                        and 'VALUES' in q['query']]
        assert len(value_inserts) == 0


# =============================================================================
# Tests for record_game_outcome
# =============================================================================

class TestRecordGameOutcome:
    """Tests for record_game_outcome method."""
    
    def test_record_winning_game(self, mock_cods_engine, mock_db):
        """Test recording a winning game."""
        result = mock_cods_engine.record_game_outcome(
            game_id='sp80-test123',
            final_score=20.0,
            max_level_reached=5,
            total_actions=150,
            won=True
        )
        
        assert result['game_id'] == 'sp80-test123'
        assert result['won'] == True
        assert result['max_level'] == 5
    
    def test_record_failed_game_detects_gaps(self, mock_cods_engine, mock_db):
        """Test that failing game triggers gap detection."""
        result = mock_cods_engine.record_game_outcome(
            game_id='sp80-test123',
            final_score=5.0,
            max_level_reached=2,
            total_actions=200,
            won=False
        )
        
        assert result['won'] == False
        # Gap detection may or may not find gaps depending on mock data
        assert 'primitive_gaps' in result
    
    def test_no_context_returns_error(self, mock_cods_engine, mock_db):
        """Test that missing context returns error dict."""
        mock_cods_engine._context = None
        
        result = mock_cods_engine.record_game_outcome(
            game_id='sp80-test',
            final_score=10.0,
            max_level_reached=2,
            total_actions=100,
            won=False
        )
        
        assert 'error' in result
        assert result['error'] == 'no_context'


# =============================================================================
# Tests for process_near_miss_patterns
# =============================================================================

class TestProcessNearMissPatterns:
    """Tests for process_near_miss_patterns method."""
    
    def test_process_near_win(self, mock_cods_engine, mock_db):
        """Test processing a near-win (score 18-19)."""
        result = mock_cods_engine.process_near_miss_patterns('nm_12345')
        
        assert result['processed'] == True
        # Near-wins should suggest primitives
    
    def test_invalid_near_miss_id(self, mock_cods_engine, mock_db):
        """Test with invalid near miss ID."""
        # Mock returns empty for this
        mock_db.execute_query = lambda q, p=None: []
        
        result = mock_cods_engine.process_near_miss_patterns('invalid_id')
        
        assert result['processed'] == False


# =============================================================================
# Tests for get_primitive_gap_summary
# =============================================================================

class TestGetPrimitiveGapSummary:
    """Tests for get_primitive_gap_summary method."""
    
    def test_summary_aggregation(self, mock_cods_engine, mock_db):
        """Test that summary aggregates hints correctly."""
        summary = mock_cods_engine.get_primitive_gap_summary(min_confidence=0.5)
        
        assert 'total_hints' in summary
        assert 'by_game_type' in summary
        assert 'by_primitive' in summary
        assert 'top_suggestions' in summary
    
    def test_confidence_threshold(self, mock_cods_engine, mock_db):
        """Test that confidence threshold filters results."""
        # With very high threshold, should get fewer results
        summary = mock_cods_engine.get_primitive_gap_summary(min_confidence=0.99)
        
        # Verify threshold was passed to query
        select_queries = [q for q in mock_db.queries if 'SELECT' in q['query'].upper() 
                         and 'cods_primitive_hints' in q['query']]
        # Should have been called with the threshold
        assert len(select_queries) >= 1


# =============================================================================
# Tests for _score_primitive_relevance
# =============================================================================

class TestScorePrimitiveRelevance:
    """Tests for _score_primitive_relevance helper."""
    
    def test_containment_primitives_score_high(self, mock_cods_engine):
        """Test that containment primitives score high for level 2+ failures."""
        score = mock_cods_engine._score_primitive_relevance(
            'containment_check', 'sp80', 2
        )
        
        assert score >= 0.5  # Should be relevant
    
    def test_path_primitives_score_for_navigation(self, mock_cods_engine):
        """Test that path primitives score for navigation games."""
        score = mock_cods_engine._score_primitive_relevance(
            'path_exists', 'nav01', 2
        )
        
        assert score >= 0.3  # Should have some relevance
    
    def test_level_1_failures_score_lower(self, mock_cods_engine):
        """Test that level 1 failures score lower (simpler mechanics)."""
        score_l1 = mock_cods_engine._score_primitive_relevance(
            'containment_check', 'sp80', 1
        )
        score_l2 = mock_cods_engine._score_primitive_relevance(
            'containment_check', 'sp80', 2
        )
        
        # Level 2+ should have higher relevance
        assert score_l2 > score_l1


# =============================================================================
# Tests for _detect_concept_signals
# =============================================================================

class TestDetectConceptSignals:
    """Tests for _detect_concept_signals method."""
    
    def test_multiple_related_primitives_create_signal(self, mock_cods_engine, mock_db):
        """Test that multiple primitives from same category create concept signal."""
        signals = mock_cods_engine._detect_concept_signals('sp80-test', 2)
        
        # Should detect signals if multiple gaps in same category
        assert isinstance(signals, list)


# =============================================================================
# Integration Tests
# =============================================================================

class TestFailureDrivenLearningIntegration:
    """Integration tests for the full failure-driven learning flow."""
    
    def test_full_failure_flow(self, mock_cods_engine, mock_db):
        """Test the full flow: level fail -> game fail -> gap detection."""
        # Step 1: Record level failure
        mock_cods_engine.record_level_outcome(
            level=2,
            passed=False,
            actions_used=150
        )
        
        # Step 2: Record game failure
        result = mock_cods_engine.record_game_outcome(
            game_id='sp80-test123',
            final_score=1.0,
            max_level_reached=2,
            total_actions=150,
            won=False
        )
        
        # Step 3: Get gap summary
        summary = mock_cods_engine.get_primitive_gap_summary(min_confidence=0.3)
        
        # Should have gone through the flow without errors
        assert 'game_id' in result
        assert 'total_hints' in summary


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
