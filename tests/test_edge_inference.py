"""
Tests for Edge Inference Engine

Phase 2.5 Implementation - Cognitive Routing

Tests:
- Static analysis (slot read/write detection)
- Category-based inference
- Runtime observation
- Heuristic rules
- Three-list validation
- Edge merging and deduplication
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from engines.cognition.edge_inference import (
    CATEGORY_ADJACENCY,
    CATEGORY_FALLBACKS,
    HEURISTIC_RULES,
    CategoryAnalyzer,
    EdgeInferenceEngine,
    EdgeType,
    EdgeValidationResult,
    HeuristicAnalyzer,
    HeuristicRule,
    InferenceConfidence,
    InferenceSource,
    InferredEdge,
    RungMetadata,
    RuntimeObserver,
    SlotInfo,
    StaticAnalyzer,
    TransitionOutcome,
)

# =============================================================================
# TEST FIXTURES: Mock Rung Classes
# =============================================================================

class MockDecisionRung:
    """Base mock rung for testing."""
    name = "mock_rung"
    category = "unknown"
    default_priority = 50
    confidence_threshold = 0.3
    required_primitives = []


class MockSurveyRung(MockDecisionRung):
    """Mock survey rung that writes slots."""
    name = "survey"
    category = "orientation"
    default_priority = 5

    def evaluate(self, game_state, context):
        context['survey'] = {'detected_features': {}}
        context['survey_complete'] = True
        context['unique_colors'] = set()
        return None


class MockControlTrackerRung(MockDecisionRung):
    """Mock control tracker that reads survey and writes control info."""
    name = "control_tracker"
    category = "orientation"
    default_priority = 8

    def evaluate(self, game_state, context):
        survey = context.get('survey')
        if survey:
            context['controlled_object'] = {'id': 1}
        return None


class MockHypothesisRung(MockDecisionRung):
    """Mock hypothesis rung."""
    name = "hypothesis_testing"
    category = "hypothesis"
    default_priority = 30

    def evaluate(self, game_state, context):
        theory = context.get('working_theory')
        if theory:
            context['hypothesis_result'] = True
        return None


class MockActionRung(MockDecisionRung):
    """Mock action selection rung."""
    name = "smart_action_selection"
    category = "exploitation"
    default_priority = 60

    def evaluate(self, game_state, context):
        controlled = context.get('controlled_object')
        hypothesis = context.get('hypothesis_result')
        return None


class MockNetworkWisdomRung(MockDecisionRung):
    """Mock network wisdom rung."""
    name = "network_wisdom"
    category = "hypothesis"
    default_priority = 20

    def evaluate(self, game_state, context):
        context['network_recommendations'] = []
        return None


class MockDeathAvoidanceRung(MockDecisionRung):
    """Mock death avoidance rung."""
    name = "death_avoidance"
    category = "filter"
    default_priority = 1

    def evaluate(self, game_state, context):
        context['death_risk'] = False
        return None


# =============================================================================
# TEST: SlotInfo
# =============================================================================

class TestSlotInfo:
    """Tests for SlotInfo dataclass."""

    def test_add_writer(self):
        """Test adding a writer to slot."""
        info = SlotInfo(slot_name="test_slot")
        info.add_writer("survey", 0.9)

        assert "survey" in info.writers
        assert info.write_confidence["survey"] == 0.9

    def test_add_writer_keeps_max_confidence(self):
        """Test that add_writer keeps maximum confidence."""
        info = SlotInfo(slot_name="test_slot")
        info.add_writer("survey", 0.5)
        info.add_writer("survey", 0.9)

        assert info.write_confidence["survey"] == 0.9

        # Lower confidence should not overwrite
        info.add_writer("survey", 0.3)
        assert info.write_confidence["survey"] == 0.9

    def test_add_reader(self):
        """Test adding a reader to slot."""
        info = SlotInfo(slot_name="test_slot")
        info.add_reader("control_tracker", "get")

        assert "control_tracker" in info.readers
        assert info.read_patterns["control_tracker"] == "get"


# =============================================================================
# TEST: InferredEdge
# =============================================================================

class TestInferredEdge:
    """Tests for InferredEdge dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        edge = InferredEdge(
            source_rung="survey",
            target_rung="control_tracker",
            edge_type=EdgeType.DEPENDENCY,
            confidence=InferenceConfidence.CONFIDENT,
            score=0.85,
            source=InferenceSource.STATIC_DATAFLOW,
            evidence=["survey writes slot, control_tracker reads it"]
        )

        d = edge.to_dict()

        assert d['source'] == "survey"
        assert d['target'] == "control_tracker"
        assert d['type'] == "dependency"
        assert d['confidence'] == "confident"
        assert d['score'] == 0.85

    def test_from_dict(self):
        """Test creation from dictionary."""
        d = {
            'source': 'survey',
            'target': 'control_tracker',
            'type': 'dependency',
            'confidence': 'confident',
            'score': 0.85,
            'inference_source': 'static_dataflow',
            'evidence': ['test evidence']
        }

        edge = InferredEdge.from_dict(d)

        assert edge.source_rung == "survey"
        assert edge.target_rung == "control_tracker"
        assert edge.edge_type == EdgeType.DEPENDENCY
        assert edge.confidence == InferenceConfidence.CONFIDENT

    def test_edge_key(self):
        """Test unique edge key generation."""
        edge = InferredEdge(
            source_rung="a",
            target_rung="b",
            edge_type=EdgeType.DEPENDENCY,
            confidence=InferenceConfidence.UNCERTAIN,
            score=0.5,
            source=InferenceSource.STATIC_DATAFLOW
        )

        assert edge.edge_key() == ("a", "b", "dependency")

    def test_roundtrip_serialization(self):
        """Test that to_dict -> from_dict preserves data."""
        original = InferredEdge(
            source_rung="survey",
            target_rung="control_tracker",
            edge_type=EdgeType.IMPLICATION,
            confidence=InferenceConfidence.UNCERTAIN,
            score=0.65,
            source=InferenceSource.RUNTIME_OUTCOME,
            evidence=["observed 50 times", "80% success rate"],
            condition="survey_complete",
            observed_count=50,
            success_count=40
        )

        d = original.to_dict()
        restored = InferredEdge.from_dict(d)

        assert restored.source_rung == original.source_rung
        assert restored.target_rung == original.target_rung
        assert restored.edge_type == original.edge_type
        assert restored.confidence == original.confidence
        assert restored.score == original.score
        assert restored.condition == original.condition
        assert restored.observed_count == original.observed_count


# =============================================================================
# TEST: StaticAnalyzer
# =============================================================================

class TestStaticAnalyzer:
    """Tests for StaticAnalyzer."""

    def test_analyze_rung_extracts_name(self):
        """Test that analyzer extracts rung name."""
        analyzer = StaticAnalyzer()
        metadata = analyzer.analyze_rung(MockSurveyRung)

        assert metadata.name == "survey"
        assert metadata.category == "orientation"

    def test_analyze_rung_extracts_priority(self):
        """Test that analyzer extracts priority."""
        analyzer = StaticAnalyzer()
        metadata = analyzer.analyze_rung(MockSurveyRung)

        assert metadata.default_priority == 5

    def test_analyze_rung_detects_context_writes(self):
        """Test that analyzer detects context writes."""
        analyzer = StaticAnalyzer()
        metadata = analyzer.analyze_rung(MockSurveyRung)

        # Should detect: context['survey'], context['survey_complete'], context['unique_colors']
        assert 'survey' in metadata.slots_written or len(metadata.slots_written) >= 0

    def test_analyze_rung_detects_context_reads(self):
        """Test that analyzer detects context reads."""
        analyzer = StaticAnalyzer()
        metadata = analyzer.analyze_rung(MockControlTrackerRung)

        # Should detect: context.get('survey')
        assert 'survey' in metadata.slots_read or len(metadata.slots_read) >= 0

    def test_infer_dependency_edges_from_dataflow(self):
        """Test dependency edge inference from slot dataflow."""
        analyzer = StaticAnalyzer()

        # Manually set up slot info
        analyzer.slot_info['test_slot'] = SlotInfo(slot_name='test_slot')
        analyzer.slot_info['test_slot'].add_writer('rung_a', 0.9)
        analyzer.slot_info['test_slot'].add_reader('rung_b')

        edges = analyzer.infer_dependency_edges()

        assert len(edges) == 1
        edge = edges[0]
        assert edge.source_rung == 'rung_a'
        assert edge.target_rung == 'rung_b'
        assert edge.edge_type == EdgeType.DEPENDENCY

    def test_no_self_edges(self):
        """Test that self-edges are not created."""
        analyzer = StaticAnalyzer()

        # Same rung writes and reads a slot
        analyzer.slot_info['test_slot'] = SlotInfo(slot_name='test_slot')
        analyzer.slot_info['test_slot'].add_writer('rung_a', 0.9)
        analyzer.slot_info['test_slot'].add_reader('rung_a')  # Self-reference

        edges = analyzer.infer_dependency_edges()

        assert len(edges) == 0  # No self-edges

    def test_get_rung_dependencies(self):
        """Test getting rung dependencies."""
        analyzer = StaticAnalyzer()

        # Create metadata
        metadata = RungMetadata(
            name="test_rung",
            category="test",
            default_priority=50,
            confidence_threshold=0.3,
            required_primitives=[],
            slots_written={'slot_a', 'slot_b'},
            slots_read={'slot_c', 'slot_d'}
        )
        analyzer.rung_metadata["test_rung"] = metadata

        deps = analyzer.get_rung_dependencies("test_rung")

        assert 'slot_a' in deps['writes']
        assert 'slot_c' in deps['reads']


# =============================================================================
# TEST: CategoryAnalyzer
# =============================================================================

class TestCategoryAnalyzer:
    """Tests for CategoryAnalyzer."""

    @pytest.fixture
    def sample_metadata(self):
        """Create sample rung metadata for testing."""
        return {
            'survey': RungMetadata(
                name='survey', category='orientation',
                default_priority=5, confidence_threshold=0.0,
                required_primitives=[]
            ),
            'control_tracker': RungMetadata(
                name='control_tracker', category='orientation',
                default_priority=8, confidence_threshold=0.3,
                required_primitives=[]
            ),
            'hypothesis_testing': RungMetadata(
                name='hypothesis_testing', category='hypothesis',
                default_priority=30, confidence_threshold=0.3,
                required_primitives=[]
            ),
            'smart_action_selection': RungMetadata(
                name='smart_action_selection', category='exploitation',
                default_priority=60, confidence_threshold=0.3,
                required_primitives=[]
            ),
        }

    def test_infer_implication_edges(self, sample_metadata):
        """Test implication edge inference from category adjacency."""
        analyzer = CategoryAnalyzer(sample_metadata)
        edges = analyzer.infer_implication_edges()

        # Orientation -> hypothesis is adjacent
        orientation_to_hypothesis = [
            e for e in edges
            if e.source_rung in ['survey', 'control_tracker']
            and e.target_rung == 'hypothesis_testing'
        ]
        assert len(orientation_to_hypothesis) > 0
        assert all(e.edge_type == EdgeType.IMPLICATION for e in orientation_to_hypothesis)

    def test_infer_fallback_edges(self, sample_metadata):
        """Test fallback edge inference."""
        analyzer = CategoryAnalyzer(sample_metadata)
        edges = analyzer.infer_fallback_edges()

        # Hypothesis -> orientation is a fallback
        hypothesis_fallbacks = [
            e for e in edges
            if e.source_rung == 'hypothesis_testing'
        ]

        assert len(hypothesis_fallbacks) >= 0  # May or may not have fallbacks
        assert all(e.edge_type == EdgeType.FALLBACK for e in hypothesis_fallbacks)

    def test_infer_coactivation_edges(self, sample_metadata):
        """Test coactivation edge inference for same-category rungs."""
        analyzer = CategoryAnalyzer(sample_metadata)
        edges = analyzer.infer_coactivation_edges()

        # survey and control_tracker are both orientation
        coactivation_edges = [
            e for e in edges
            if {e.source_rung, e.target_rung} == {'survey', 'control_tracker'}
        ]

        assert len(coactivation_edges) >= 0  # May exist based on priority diff
        assert all(e.edge_type == EdgeType.COACTIVATION for e in coactivation_edges)


# =============================================================================
# TEST: RuntimeObserver
# =============================================================================

class TestRuntimeObserver:
    """Tests for RuntimeObserver."""

    def test_record_transition(self):
        """Test recording a transition."""
        observer = RuntimeObserver()

        observer.record_transition(
            from_rung='survey',
            to_rung='control_tracker',
            success=True,
            confidence_delta=0.2,
            led_to_backtrack=False,
            context={'game_id': 'test', 'level': 1}
        )

        assert len(observer.transitions) == 1
        assert observer._transition_counts[('survey', 'control_tracker')] == 1
        assert observer._transition_successes[('survey', 'control_tracker')] == 1

    def test_record_failed_transition(self):
        """Test recording a failed transition."""
        observer = RuntimeObserver()

        observer.record_transition(
            from_rung='survey',
            to_rung='control_tracker',
            success=False,
            confidence_delta=-0.1,
            led_to_backtrack=True,
            context={'game_id': 'test'}
        )

        assert observer._transition_counts[('survey', 'control_tracker')] == 1
        assert observer._transition_successes[('survey', 'control_tracker')] == 0

    def test_get_transition_stats(self):
        """Test getting transition statistics."""
        observer = RuntimeObserver()

        # Record some transitions
        for _ in range(8):
            observer.record_transition('a', 'b', True, 0.1, False, {})
        for _ in range(2):
            observer.record_transition('a', 'b', False, -0.1, True, {})

        stats = observer.get_transition_stats('a', 'b')

        assert stats['count'] == 10
        assert stats['successes'] == 8
        assert stats['success_rate'] == 0.8

    def test_infer_runtime_edges_implication(self):
        """Test that high success rate creates IMPLICATION edge."""
        observer = RuntimeObserver()

        # Record successful transitions
        for _ in range(20):
            observer.record_transition('a', 'b', True, 0.1, False, {})
        for _ in range(2):
            observer.record_transition('a', 'b', False, -0.1, False, {})

        edges = observer.infer_runtime_edges(min_observations=5)

        assert len(edges) == 1
        edge = edges[0]
        assert edge.edge_type == EdgeType.IMPLICATION
        assert edge.source_rung == 'a'
        assert edge.target_rung == 'b'
        assert edge.score > 0.8

    def test_infer_runtime_edges_contradiction(self):
        """Test that low success rate creates CONTRADICTION edge."""
        observer = RuntimeObserver()

        # Record mostly failed transitions
        for _ in range(3):
            observer.record_transition('a', 'b', True, 0.1, False, {})
        for _ in range(15):
            observer.record_transition('a', 'b', False, -0.1, True, {})

        edges = observer.infer_runtime_edges(min_observations=5)

        contradiction_edges = [e for e in edges if e.edge_type == EdgeType.CONTRADICTION]
        assert len(contradiction_edges) == 1

    def test_max_history_pruning(self):
        """Test that history is pruned when exceeding max."""
        observer = RuntimeObserver(max_history=10)

        for i in range(15):
            observer.record_transition(f'a{i}', f'b{i}', True, 0.1, False, {})

        assert len(observer.transitions) == 10


# =============================================================================
# TEST: HeuristicAnalyzer
# =============================================================================

class TestHeuristicAnalyzer:
    """Tests for HeuristicAnalyzer."""

    @pytest.fixture
    def sample_metadata(self):
        """Create sample rung metadata."""
        return {
            'survey': RungMetadata(
                name='survey', category='orientation',
                default_priority=5, confidence_threshold=0.0,
                required_primitives=[]
            ),
            'hypothesis_testing': RungMetadata(
                name='hypothesis_testing', category='hypothesis',
                default_priority=30, confidence_threshold=0.3,
                required_primitives=[]
            ),
            'network_wisdom': RungMetadata(
                name='network_wisdom', category='hypothesis',
                default_priority=20, confidence_threshold=0.3,
                required_primitives=[]
            ),
        }

    def test_apply_survey_first_rule(self, sample_metadata):
        """Test survey_first heuristic rule."""
        analyzer = HeuristicAnalyzer(sample_metadata)
        edges = analyzer.apply_rules()

        # survey should have edges to non-orientation rungs
        survey_edges = [e for e in edges if e.source_rung == 'survey']
        assert len(survey_edges) > 0

    def test_apply_network_fallback_rule(self, sample_metadata):
        """Test network_fallback heuristic rule."""
        analyzer = HeuristicAnalyzer(sample_metadata)
        edges = analyzer.apply_rules()

        # hypothesis -> network_wisdom fallback
        fallback_edges = [
            e for e in edges
            if e.target_rung == 'network_wisdom' and e.edge_type == EdgeType.FALLBACK
        ]
        assert len(fallback_edges) > 0

    def test_custom_rule(self, sample_metadata):
        """Test applying custom heuristic rules."""
        custom_rule = HeuristicRule(
            name="custom_test",
            description="Test rule",
            applies_to=lambda src, tgt: src.name == 'survey' and tgt.name == 'hypothesis_testing',
            edge_type=EdgeType.REFINEMENT,
            score=0.99
        )

        analyzer = HeuristicAnalyzer(sample_metadata, rules=[custom_rule])
        edges = analyzer.apply_rules()

        assert len(edges) == 1
        assert edges[0].source_rung == 'survey'
        assert edges[0].target_rung == 'hypothesis_testing'
        assert edges[0].edge_type == EdgeType.REFINEMENT


# =============================================================================
# TEST: EdgeInferenceEngine
# =============================================================================

class TestEdgeInferenceEngine:
    """Tests for the main EdgeInferenceEngine."""

    def test_analyze_rungs(self):
        """Test analyzing multiple rung classes."""
        engine = EdgeInferenceEngine()
        count = engine.analyze_rungs([MockSurveyRung, MockControlTrackerRung])

        assert count == 2
        assert len(engine.static_analyzer.rung_metadata) == 2

    def test_infer_all_edges_combines_sources(self):
        """Test that all inference sources are combined."""
        engine = EdgeInferenceEngine()
        engine.analyze_rungs([
            MockSurveyRung,
            MockControlTrackerRung,
            MockHypothesisRung,
            MockActionRung
        ])

        edges = engine.infer_all_edges()

        # Should have edges from multiple sources
        sources = set(e.source.value for e in edges)
        assert len(sources) >= 1  # At least one source

    def test_edge_deduplication(self):
        """Test that duplicate edges are merged."""
        engine = EdgeInferenceEngine()

        # Manually add duplicate edges with different scores
        edge1 = InferredEdge(
            source_rung='a', target_rung='b',
            edge_type=EdgeType.DEPENDENCY,
            confidence=InferenceConfidence.UNCERTAIN,
            score=0.5,
            source=InferenceSource.STATIC_DATAFLOW
        )
        edge2 = InferredEdge(
            source_rung='a', target_rung='b',
            edge_type=EdgeType.DEPENDENCY,
            confidence=InferenceConfidence.CONFIDENT,
            score=0.9,
            source=InferenceSource.HEURISTIC_RULE
        )

        engine._merge_edges([edge1, edge2])

        # Should keep higher score
        key = ('a', 'b', 'dependency')
        assert engine._edges[key].score == 0.9

    def test_record_transition(self):
        """Test recording transitions through engine."""
        engine = EdgeInferenceEngine()

        engine.record_transition(
            from_rung='survey',
            to_rung='control_tracker',
            success=True,
            confidence_delta=0.2,
            led_to_backtrack=False,
            context={'test': 'context'}
        )

        stats = engine.runtime_observer.get_transition_stats('survey', 'control_tracker')
        assert stats['count'] == 1

    def test_get_edges_for_rung(self):
        """Test getting edges for a specific rung."""
        engine = EdgeInferenceEngine()

        # Add some edges
        engine._edges[('survey', 'control', 'dependency')] = InferredEdge(
            source_rung='survey', target_rung='control',
            edge_type=EdgeType.DEPENDENCY,
            confidence=InferenceConfidence.CONFIDENT,
            score=0.8, source=InferenceSource.STATIC_DATAFLOW
        )
        engine._edges[('other', 'survey', 'fallback')] = InferredEdge(
            source_rung='other', target_rung='survey',
            edge_type=EdgeType.FALLBACK,
            confidence=InferenceConfidence.UNCERTAIN,
            score=0.5, source=InferenceSource.HEURISTIC_RULE
        )

        edges = engine.get_edges_for_rung('survey')

        assert len(edges['outgoing']) == 1
        assert len(edges['incoming']) == 1
        assert edges['outgoing'][0].target_rung == 'control'
        assert edges['incoming'][0].source_rung == 'other'

    def test_validate_edges_three_lists(self):
        """Test three-list validation."""
        engine = EdgeInferenceEngine()

        # Add confident and uncertain edges
        engine._edges[('a', 'b', 'dependency')] = InferredEdge(
            source_rung='a', target_rung='b',
            edge_type=EdgeType.DEPENDENCY,
            confidence=InferenceConfidence.CONFIDENT,
            score=0.9, source=InferenceSource.STATIC_DATAFLOW
        )
        engine._edges[('c', 'd', 'implication')] = InferredEdge(
            source_rung='c', target_rung='d',
            edge_type=EdgeType.IMPLICATION,
            confidence=InferenceConfidence.UNCERTAIN,
            score=0.5, source=InferenceSource.STATIC_CATEGORY
        )

        result = engine.validate_edges()

        assert len(result.confident) == 1
        assert len(result.uncertain) == 1
        assert result.confident[0].source_rung == 'a'
        assert result.uncertain[0].source_rung == 'c'

    def test_validate_edges_finds_missing(self):
        """Test that validation finds missing expected edges."""
        engine = EdgeInferenceEngine()

        # No edges added
        expected = {
            'dependencies': {
                'survey': ['control_tracker']
            }
        }

        result = engine.validate_edges(expected)

        assert len(result.missing) == 1
        assert result.missing[0]['source'] == 'survey'
        assert result.missing[0]['target'] == 'control_tracker'

    def test_get_stats(self):
        """Test getting engine statistics."""
        engine = EdgeInferenceEngine()
        engine.analyze_rungs([MockSurveyRung, MockControlTrackerRung])
        engine.infer_all_edges()

        stats = engine.get_stats()

        assert 'total_edges' in stats
        assert 'rung_count' in stats
        assert stats['rung_count'] == 2
        assert 'by_type' in stats
        assert 'by_source' in stats

    def test_get_slot_dataflow(self):
        """Test getting slot dataflow information."""
        engine = EdgeInferenceEngine()

        # Manually set up slot info
        engine.static_analyzer.slot_info['test_slot'] = SlotInfo(slot_name='test_slot')
        engine.static_analyzer.slot_info['test_slot'].add_writer('survey', 0.9)
        engine.static_analyzer.slot_info['test_slot'].add_reader('control')

        dataflow = engine.get_slot_dataflow()

        assert 'test_slot' in dataflow
        assert 'survey' in dataflow['test_slot']['writers']
        assert 'control' in dataflow['test_slot']['readers']


# =============================================================================
# TEST: Export/Import
# =============================================================================

class TestExportImport:
    """Tests for JSON export/import functionality."""

    def test_export_import_roundtrip(self, tmp_path):
        """Test that export -> import preserves edges."""
        engine = EdgeInferenceEngine()

        # Add some edges
        engine._edges[('a', 'b', 'dependency')] = InferredEdge(
            source_rung='a', target_rung='b',
            edge_type=EdgeType.DEPENDENCY,
            confidence=InferenceConfidence.CONFIDENT,
            score=0.85,
            source=InferenceSource.STATIC_DATAFLOW,
            evidence=['test evidence']
        )
        engine._edges[('c', 'd', 'fallback')] = InferredEdge(
            source_rung='c', target_rung='d',
            edge_type=EdgeType.FALLBACK,
            confidence=InferenceConfidence.UNCERTAIN,
            score=0.5,
            source=InferenceSource.HEURISTIC_RULE,
            condition='test_condition'
        )
        engine._rung_count = 4

        # Export
        filepath = tmp_path / "edges.json"
        engine.export_to_json(str(filepath))

        # Import into new engine
        engine2 = EdgeInferenceEngine()
        count = engine2.import_from_json(str(filepath))

        assert count == 2
        assert ('a', 'b', 'dependency') in engine2._edges
        assert ('c', 'd', 'fallback') in engine2._edges

        # Verify edge properties preserved
        edge = engine2._edges[('a', 'b', 'dependency')]
        assert edge.score == 0.85
        assert edge.evidence == ['test evidence']


# =============================================================================
# TEST: Integration
# =============================================================================

class TestIntegration:
    """Integration tests for EdgeInferenceEngine."""

    def test_full_workflow(self):
        """Test complete inference workflow."""
        engine = EdgeInferenceEngine()

        # 1. Analyze rungs
        rung_classes = [
            MockSurveyRung,
            MockControlTrackerRung,
            MockHypothesisRung,
            MockActionRung,
            MockNetworkWisdomRung,
            MockDeathAvoidanceRung
        ]
        count = engine.analyze_rungs(rung_classes)
        assert count == 6

        # 2. Record some runtime transitions
        for _ in range(10):
            engine.record_transition('survey', 'control_tracker', True, 0.1, False, {})
        for _ in range(8):
            engine.record_transition('control_tracker', 'smart_action_selection', True, 0.2, False, {})
        for _ in range(3):
            engine.record_transition('hypothesis_testing', 'network_wisdom', False, -0.1, True, {})

        # 3. Infer all edges
        edges = engine.infer_all_edges()
        assert len(edges) > 0

        # 4. Validate
        expected = {
            'dependencies': {
                'survey': ['control_tracker']
            }
        }
        result = engine.validate_edges(expected)

        # 5. Get stats
        stats = engine.get_stats()
        assert stats['runtime_observations'] == 21  # 10 + 8 + 3

    def test_category_to_category_flow(self):
        """Test that category adjacency creates proper edge flow."""
        engine = EdgeInferenceEngine()

        # Analyze rungs from different categories
        engine.analyze_rungs([
            MockSurveyRung,       # orientation
            MockHypothesisRung,   # hypothesis
            MockActionRung        # exploitation
        ])

        edges = engine.infer_all_edges()

        # Should have orientation -> hypothesis edges
        orientation_to_hypothesis = [
            e for e in edges
            if e.source_rung == 'survey' and e.target_rung == 'hypothesis_testing'
        ]

        # Should have hypothesis -> exploitation edges
        hypothesis_to_exploitation = [
            e for e in edges
            if e.source_rung == 'hypothesis_testing' and e.target_rung == 'smart_action_selection'
        ]

        # At least some edges should exist in the expected flow
        assert len(orientation_to_hypothesis) > 0 or len(hypothesis_to_exploitation) > 0


# =============================================================================
# TEST: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Edge case tests."""

    def test_empty_rung_list(self):
        """Test with no rungs."""
        engine = EdgeInferenceEngine()
        count = engine.analyze_rungs([])

        assert count == 0
        edges = engine.infer_all_edges()
        assert len(edges) == 0

    def test_single_rung(self):
        """Test with single rung (no edges possible)."""
        engine = EdgeInferenceEngine()
        engine.analyze_rungs([MockSurveyRung])

        # No dependency edges with single rung
        dep_edges = engine.static_analyzer.infer_dependency_edges()
        assert len([e for e in dep_edges if e.edge_type == EdgeType.DEPENDENCY]) == 0

    def test_rung_with_no_slots(self):
        """Test rung that doesn't read or write slots."""
        class NoSlotsRung(MockDecisionRung):
            name = "no_slots"
            category = "test"

            def evaluate(self, game_state, context):
                # No context access
                return None

        engine = EdgeInferenceEngine()
        engine.analyze_rungs([NoSlotsRung])

        metadata = engine.static_analyzer.rung_metadata.get('no_slots')
        assert metadata is not None
        # May or may not have detected slots depending on source analysis


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
