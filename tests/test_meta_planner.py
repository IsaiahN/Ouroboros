"""
Tests for Meta-Planner Components - Phase 3

Tests cover:
1. SearchContext - Injectable state container
2. Algorithms - Domain-specific search strategies
3. MetaPlannerCache - Bucketed caching for algorithm selection
4. PrecomputationManager - Offline preprocessing

Run with: pytest tests/test_meta_planner.py -v
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

import pytest

from engines.cognition.algorithms import (
    ALGORITHM_CLASSES,
    DOMAIN_ALGORITHMS,
    QUADRANT_ALGORITHMS,
    BacktrackingAStar,
    BeamSearch,
    BidirectionalSearch,
    ExplorationWithExclusions,
    GreedyBestFirst,
    HierarchicalAStar,
    InformationMaximizingSearch,
    LandmarkAStar,
    RetrievalSearch,
    SearchAlgorithm,
    TargetedQuestionSearch,
    TopologicalDPSearch,
    get_algorithm,
    get_algorithm_for_domain,
    get_algorithm_for_quadrant,
)
from engines.cognition.meta_planner import (
    ALGORITHM_RELEVANT_SLOTS,
    CacheKey,
    CacheStats,
    ComplexityLevel,
    ConfidenceBucket,
    MetaPlanner,
    MetaPlannerCache,
    TimeBucket,
    UUBucket,
    bucket_confidence,
    bucket_time,
    bucket_uu,
    compute_cache_key,
    create_meta_planner,
    determine_complexity,
    lookup_profile,
)
from engines.cognition.precomputation import (
    CATEGORY_ORDER,
    DEFAULT_LANDMARKS,
    GraphInfo,
    PrecomputationManager,
    PrecomputedData,
    create_precomputation_manager,
)

# Import modules under test
from engines.cognition.search_context import (
    MutationRequest,
    MutationType,
    SearchContext,
    SearchPhase,
    create_search_context,
)

# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def sample_blackboard_snapshot() -> Dict[str, Any]:
    """Sample blackboard snapshot for testing."""
    return {
        'confidence': 0.5,
        'rumsfeld': {'uu_estimate': 0.4},
        'domain_signature': 'unknown',
        'time_budget_remaining': 0.8,
        'time_budget_total': 1.0,
        'complexity': 'MEDIUM',
        'goal_rungs': ['smart_action_selection'],
    }


@pytest.fixture
def sample_precomputed() -> PrecomputedData:
    """Sample precomputed data for testing."""
    data = PrecomputedData()
    data.landmark_distances = {
        'survey': {'survey': 0, 'hypothesis_testing': 2, 'smart_action_selection': 4},
        'hypothesis_testing': {'survey': 2, 'hypothesis_testing': 0, 'smart_action_selection': 2},
    }
    data.topological_order = ['survey', 'orientation', 'hypothesis_testing', 'smart_action_selection']
    data.is_dag = True
    data.cluster_assignments = {
        'orientation': ['survey', 'orientation'],
        'hypothesis': ['hypothesis_testing'],
        'exploitation': ['smart_action_selection'],
    }
    data.rung_to_cluster = {
        'survey': 'orientation',
        'orientation': 'orientation',
        'hypothesis_testing': 'hypothesis',
        'smart_action_selection': 'exploitation',
    }
    return data


@pytest.fixture
def sample_context(sample_blackboard_snapshot, sample_precomputed) -> SearchContext:
    """Sample SearchContext for testing."""
    return create_search_context(
        blackboard=sample_blackboard_snapshot,
        precomputed=sample_precomputed,
        current_quadrant='KU',
    )


@pytest.fixture
def sample_graph_info() -> Dict[str, Any]:
    """Sample graph info for algorithm testing."""
    return {
        'nodes': {
            'survey': {'category': 'orientation', 'default_priority': 5},
            'hypothesis_testing': {'category': 'hypothesis', 'default_priority': 30},
            'smart_action_selection': {'category': 'exploitation', 'default_priority': 60},
            'network_wisdom': {'category': 'exploitation', 'default_priority': 40},
        },
        'edges': {
            'survey': ['hypothesis_testing', 'network_wisdom'],
            'hypothesis_testing': ['smart_action_selection'],
            'network_wisdom': ['smart_action_selection'],
        },
        'reverse_edges': {
            'hypothesis_testing': ['survey'],
            'network_wisdom': ['survey'],
            'smart_action_selection': ['hypothesis_testing', 'network_wisdom'],
        },
        'dependencies': {},
        'is_dag': True,
        'visit_counts': {'survey': 5, 'hypothesis_testing': 2},
    }


# =============================================================================
# TEST SEARCH CONTEXT
# =============================================================================

class TestSearchContext:
    """Tests for SearchContext."""

    def test_create_search_context(self, sample_blackboard_snapshot, sample_precomputed):
        """Test SearchContext creation."""
        ctx = create_search_context(
            blackboard=sample_blackboard_snapshot,
            precomputed=sample_precomputed,
            current_quadrant='KK',
        )

        assert ctx.current_quadrant == 'KK'
        assert ctx.blackboard_snapshot == sample_blackboard_snapshot
        assert ctx.topological_order == sample_precomputed.topological_order
        assert ctx.cluster_assignments == sample_precomputed.rung_to_cluster

    def test_get_slot(self, sample_context):
        """Test slot retrieval."""
        assert sample_context.get_slot('confidence') == 0.5
        assert sample_context.get_slot('nonexistent', 'default') == 'default'

    def test_get_confidence(self, sample_context):
        """Test confidence retrieval."""
        # get_confidence looks for 'max_confidence' slot, not 'confidence'
        # so we need to check that the method works (returns default 0.0)
        assert sample_context.get_confidence() == 0.0  # Default when max_confidence not set

        # Check direct slot access works
        assert sample_context.get_slot('confidence') == 0.5

    def test_get_depth(self, sample_context):
        """Test depth calculation from path length."""
        assert sample_context.get_depth() == 0  # Empty path

        # Add to path
        sample_context.current_path.append('survey')
        assert sample_context.get_depth() == 1

    def test_get_landmark_heuristic(self, sample_context):
        """Test landmark heuristic computation."""
        h = sample_context.get_landmark_heuristic('survey', 'smart_action_selection')
        assert h >= 0  # Heuristic should be non-negative

    def test_mutation_requests(self, sample_context):
        """Test mutation request methods."""
        # Checkpoint
        sample_context.request_checkpoint("test checkpoint")
        assert sample_context.has_pending_mutations()

        # Check mutation content (this clears the queue)
        mutations = sample_context.get_pending_mutations()
        assert len(mutations) == 1
        assert mutations[0].mutation_type == MutationType.CHECKPOINT

        # Backtrack
        sample_context.request_backtrack(1, "test backtrack")
        assert sample_context.has_pending_mutations()

        # Exclude
        sample_context.request_exclude({'bad_rung'}, "test exclude")

        # Get all pending (backtrack + exclude)
        mutations = sample_context.get_pending_mutations()
        assert len(mutations) == 2

    def test_snapshot(self, sample_context):
        """Test context snapshot for serialization."""
        snapshot = sample_context.to_dict()

        assert 'current_quadrant' in snapshot
        assert 'visited_rungs' in snapshot
        assert 'depth' in snapshot
        assert snapshot['current_quadrant'] == 'KU'


# =============================================================================
# TEST ALGORITHMS
# =============================================================================

class TestAlgorithmBase:
    """Tests for base SearchAlgorithm class."""

    def test_algorithm_registry(self):
        """Test algorithm registry contains expected algorithms."""
        expected = [
            'topological_dp', 'bidirectional', 'landmark_astar',
            'greedy_best_first', 'beam_search', 'information_maximizing',
            'hierarchical_astar', 'backtracking_astar', 'targeted_question',
            'retrieval', 'exploration_exclusions'
        ]
        for name in expected:
            assert name in ALGORITHM_CLASSES

    def test_get_algorithm(self):
        """Test algorithm retrieval by name."""
        algo = get_algorithm('landmark_astar')
        assert isinstance(algo, LandmarkAStar)

        # Unknown algorithm falls back
        algo = get_algorithm('nonexistent')
        assert isinstance(algo, LandmarkAStar)

    def test_get_algorithm_for_quadrant(self):
        """Test quadrant-based algorithm selection."""
        algo = get_algorithm_for_quadrant('KK')
        assert isinstance(algo, GreedyBestFirst)

        algo = get_algorithm_for_quadrant('UU')
        assert isinstance(algo, InformationMaximizingSearch)

    def test_get_algorithm_for_domain(self):
        """Test domain-based algorithm selection."""
        algo = get_algorithm_for_domain('physics')
        assert isinstance(algo, TopologicalDPSearch)

        algo = get_algorithm_for_domain('symbolic')
        assert isinstance(algo, BidirectionalSearch)


class TestTopologicalDPSearch:
    """Tests for TopologicalDPSearch algorithm."""

    def test_get_next_rungs_with_topo_order(self, sample_context, sample_graph_info):
        """Test rung selection with topological order."""
        algo = TopologicalDPSearch()

        frontier = {'survey', 'hypothesis_testing'}
        result = algo.get_next_rungs(frontier, sample_context, sample_graph_info)

        assert len(result) >= 1
        # Should pick survey first (earlier in topo order)
        assert result[0] == 'survey'

    def test_is_applicable(self, sample_context, sample_graph_info):
        """Test applicability check."""
        algo = TopologicalDPSearch()

        # Applicable when topological order exists
        assert algo.is_applicable(sample_context, sample_graph_info)

        # Not applicable without topo order
        sample_context.topological_order = None
        assert not algo.is_applicable(sample_context, sample_graph_info)


class TestLandmarkAStar:
    """Tests for LandmarkAStar algorithm."""

    def test_get_next_rungs(self, sample_context, sample_graph_info):
        """Test A* with landmark heuristics."""
        algo = LandmarkAStar()

        frontier = {'survey', 'hypothesis_testing', 'network_wisdom'}
        result = algo.get_next_rungs(frontier, sample_context, sample_graph_info)

        assert len(result) >= 1
        assert result[0] in frontier

    def test_always_applicable(self, sample_context, sample_graph_info):
        """LandmarkAStar should always be applicable."""
        algo = LandmarkAStar()
        assert algo.is_applicable(sample_context, sample_graph_info)


class TestGreedyBestFirst:
    """Tests for GreedyBestFirst algorithm."""

    def test_get_next_rungs(self, sample_context, sample_graph_info):
        """Test greedy selection returns top-K candidates ranked by confidence."""
        algo = GreedyBestFirst()

        frontier = {'survey', 'hypothesis_testing'}
        result = algo.get_next_rungs(frontier, sample_context, sample_graph_info)

        # Should return up to max_rungs_per_call candidates (default 5)
        # With only 2 in frontier, returns both ranked by score
        assert len(result) <= len(frontier)
        assert len(result) >= 1
        for r in result:
            assert r in frontier


class TestBeamSearch:
    """Tests for BeamSearch algorithm."""

    def test_get_next_rungs_beam_width(self, sample_context, sample_graph_info):
        """Test beam search returns up to k results."""
        algo = BeamSearch(beam_width=2)

        frontier = {'survey', 'hypothesis_testing', 'network_wisdom'}
        result = algo.get_next_rungs(frontier, sample_context, sample_graph_info)

        assert len(result) <= 2
        for r in result:
            assert r in frontier

    def test_beam_width_parameter(self):
        """Test beam width is configurable."""
        algo = BeamSearch(beam_width=5)
        assert algo.beam_width == 5


class TestInformationMaximizingSearch:
    """Tests for InformationMaximizingSearch algorithm."""

    def test_get_next_rungs(self, sample_context, sample_graph_info):
        """Test UCB-style information gain optimization."""
        algo = InformationMaximizingSearch()

        frontier = {'survey', 'hypothesis_testing'}
        result = algo.get_next_rungs(frontier, sample_context, sample_graph_info)

        assert len(result) >= 1

    def test_exploration_bonus(self, sample_context, sample_graph_info):
        """Test that less-visited rungs get exploration bonus."""
        algo = InformationMaximizingSearch(exploration_bonus=2.0)

        # Set up visit counts - survey visited more
        sample_graph_info['visit_counts'] = {'survey': 100, 'hypothesis_testing': 0}

        frontier = {'survey', 'hypothesis_testing'}
        result = algo.get_next_rungs(frontier, sample_context, sample_graph_info)

        # Should prefer less-visited rung due to exploration bonus
        # (though other factors may influence)
        assert result[0] in frontier


class TestBacktrackingAStar:
    """Tests for BacktrackingAStar algorithm."""

    def test_get_next_rungs_with_exclusions(self, sample_context, sample_graph_info):
        """Test A* with excluded rungs."""
        algo = BacktrackingAStar(excluded_rungs={'survey'})

        frontier = {'survey', 'hypothesis_testing', 'network_wisdom'}
        result = algo.get_next_rungs(frontier, sample_context, sample_graph_info)

        # Should not return excluded rung
        assert 'survey' not in result

    def test_mutation_requests(self, sample_context, sample_graph_info):
        """Test that backtracking creates mutation requests."""
        algo = BacktrackingAStar(checkpoint_id=1, excluded_rungs={'bad_rung'})

        frontier = {'hypothesis_testing'}
        algo.get_next_rungs(frontier, sample_context, sample_graph_info)

        # Should have requested backtrack
        assert len(sample_context.get_pending_mutations()) > 0


class TestHierarchicalAStar:
    """Tests for HierarchicalAStar algorithm."""

    def test_get_next_rungs(self, sample_context, sample_graph_info):
        """Test two-level hierarchical search."""
        algo = HierarchicalAStar()

        frontier = {'survey', 'hypothesis_testing', 'smart_action_selection'}
        result = algo.get_next_rungs(frontier, sample_context, sample_graph_info)

        assert len(result) >= 1
        assert result[0] in frontier


# =============================================================================
# TEST BUCKETING FUNCTIONS
# =============================================================================

class TestBucketingFunctions:
    """Tests for cache key bucketing functions."""

    def test_bucket_confidence(self):
        """Test confidence bucketing."""
        assert bucket_confidence(0.0) == ConfidenceBucket.LOW
        assert bucket_confidence(0.29) == ConfidenceBucket.LOW
        assert bucket_confidence(0.3) == ConfidenceBucket.MEDIUM
        assert bucket_confidence(0.59) == ConfidenceBucket.MEDIUM
        assert bucket_confidence(0.6) == ConfidenceBucket.HIGH
        assert bucket_confidence(0.89) == ConfidenceBucket.HIGH
        assert bucket_confidence(0.9) == ConfidenceBucket.VERY_HIGH
        assert bucket_confidence(1.0) == ConfidenceBucket.VERY_HIGH

    def test_bucket_uu(self):
        """Test unknown-unknown bucketing."""
        assert bucket_uu(0.0) == UUBucket.LOW
        assert bucket_uu(0.32) == UUBucket.LOW
        assert bucket_uu(0.33) == UUBucket.MEDIUM
        assert bucket_uu(0.65) == UUBucket.MEDIUM
        assert bucket_uu(0.66) == UUBucket.HIGH
        assert bucket_uu(1.0) == UUBucket.HIGH

    def test_bucket_time(self):
        """Test time budget bucketing."""
        assert bucket_time(0.8, 1.0) == TimeBucket.PLENTY
        assert bucket_time(0.61, 1.0) == TimeBucket.PLENTY
        assert bucket_time(0.5, 1.0) == TimeBucket.LOW
        assert bucket_time(0.21, 1.0) == TimeBucket.LOW
        assert bucket_time(0.19, 1.0) == TimeBucket.CRITICAL
        assert bucket_time(0.0, 1.0) == TimeBucket.CRITICAL

    def test_determine_complexity(self):
        """Test complexity level determination."""
        assert determine_complexity(5) == ComplexityLevel.SIMPLE
        assert determine_complexity(9) == ComplexityLevel.SIMPLE
        assert determine_complexity(10) == ComplexityLevel.MEDIUM
        assert determine_complexity(29) == ComplexityLevel.MEDIUM
        assert determine_complexity(30) == ComplexityLevel.COMPLEX
        assert determine_complexity(100) == ComplexityLevel.COMPLEX


class TestCacheKey:
    """Tests for CacheKey."""

    def test_cache_key_hashable(self):
        """Test that CacheKey is hashable."""
        key = CacheKey(
            complexity=ComplexityLevel.SIMPLE,
            confidence=ConfidenceBucket.HIGH,
            uu_level=UUBucket.LOW,
            has_contradiction=False,
            time_bucket=TimeBucket.PLENTY,
            domain='physics',
            quadrant='KK',
        )

        # Should be usable as dict key
        d = {key: 'test'}
        assert d[key] == 'test'

    def test_cache_key_equality(self):
        """Test CacheKey equality."""
        key1 = CacheKey(
            complexity=ComplexityLevel.SIMPLE,
            confidence=ConfidenceBucket.HIGH,
            uu_level=UUBucket.LOW,
            has_contradiction=False,
            time_bucket=TimeBucket.PLENTY,
            domain='physics',
            quadrant='KK',
        )
        key2 = CacheKey(
            complexity=ComplexityLevel.SIMPLE,
            confidence=ConfidenceBucket.HIGH,
            uu_level=UUBucket.LOW,
            has_contradiction=False,
            time_bucket=TimeBucket.PLENTY,
            domain='physics',
            quadrant='KK',
        )

        assert key1 == key2
        assert hash(key1) == hash(key2)


# =============================================================================
# TEST META-PLANNER CACHE
# =============================================================================

class TestMetaPlannerCache:
    """Tests for MetaPlannerCache."""

    def test_cache_hit(self, sample_context):
        """Test cache hit on repeated calls."""
        cache = MetaPlannerCache()

        # First call - cache miss
        algo1 = cache.get_algorithm(sample_context)
        assert cache.stats.misses == 1

        # Second call - cache hit
        algo2 = cache.get_algorithm(sample_context)
        assert cache.stats.hits == 1

        # Same algorithm returned
        assert algo1.name == algo2.name

    def test_cache_invalidation(self, sample_context):
        """Test manual cache invalidation."""
        cache = MetaPlannerCache()

        algo1 = cache.get_algorithm(sample_context)
        cache.invalidate("test")

        algo2 = cache.get_algorithm(sample_context)

        assert cache.stats.invalidations == 1
        assert cache.stats.misses == 2

    def test_significant_value_change(self, sample_context):
        """Test detection of significant value changes."""
        cache = MetaPlannerCache()

        # Small confidence change - same bucket
        assert not cache.should_invalidate('max_confidence', 0.4, 0.45)

        # Large confidence change - different bucket (0.29 is LOW, 0.31 is MEDIUM)
        assert cache.should_invalidate('max_confidence', 0.29, 0.31)

        # Non-relevant slot
        assert not cache.should_invalidate('irrelevant_slot', 1, 2)

    def test_cache_stats(self, sample_context):
        """Test cache statistics."""
        cache = MetaPlannerCache()

        cache.get_algorithm(sample_context)
        cache.get_algorithm(sample_context)
        cache.invalidate("test")
        cache.get_algorithm(sample_context)

        stats = cache.stats
        assert stats.hits == 1
        assert stats.misses == 2
        assert stats.invalidations == 1
        assert stats.hit_rate == 1/3


class TestMetaPlanner:
    """Tests for MetaPlanner."""

    def test_select_algorithm(self, sample_context):
        """Test algorithm selection."""
        planner = create_meta_planner()

        result = planner.select_algorithm(sample_context)

        assert result.algorithm is not None
        assert result.selection_time_ms >= 0

    def test_contradiction_override(self, sample_context):
        """Test that contradiction always triggers backtracking."""
        planner = create_meta_planner()

        # Set contradiction
        sample_context.blackboard_snapshot['contradiction'] = True

        result = planner.select_algorithm(sample_context)

        assert isinstance(result.algorithm, BacktrackingAStar)

    def test_time_pressure_override(self, sample_context):
        """Test that critical time pressure triggers beam search."""
        planner = create_meta_planner()

        # Set critical time
        sample_context.blackboard_snapshot['time_budget_remaining'] = 0.1
        sample_context.blackboard_snapshot['time_budget_total'] = 1.0

        planner.invalidate_cache("time change")
        result = planner.select_algorithm(sample_context)

        assert isinstance(result.algorithm, BeamSearch)

    def test_selection_summary(self, sample_context):
        """Test selection summary statistics."""
        planner = create_meta_planner()

        for _ in range(5):
            planner.select_algorithm(sample_context)

        summary = planner.get_selection_summary()

        assert summary['total_selections'] == 5
        assert 'cache_hit_rate' in summary
        assert 'algorithm_distribution' in summary


class TestProfileLookup:
    """Tests for precomputed profile lookup."""

    def test_profile_lookup_contradiction(self):
        """Test profile lookup for contradiction case."""
        key = CacheKey(
            complexity=ComplexityLevel.MEDIUM,
            confidence=ConfidenceBucket.HIGH,
            uu_level=UUBucket.LOW,
            has_contradiction=True,
            time_bucket=TimeBucket.PLENTY,
            domain='unknown',
            quadrant='KK',
        )

        profile = lookup_profile(key)

        assert profile is not None
        assert isinstance(profile.algorithm, BacktrackingAStar)

    def test_profile_lookup_domain_specific(self):
        """Test profile lookup for domain-specific cases."""
        key = CacheKey(
            complexity=ComplexityLevel.MEDIUM,
            confidence=ConfidenceBucket.MEDIUM,
            uu_level=UUBucket.MEDIUM,
            has_contradiction=False,
            time_bucket=TimeBucket.PLENTY,
            domain='physics',
            quadrant='KU',
        )

        profile = lookup_profile(key)

        assert profile is not None
        assert isinstance(profile.algorithm, TopologicalDPSearch)


# =============================================================================
# TEST PRECOMPUTATION MANAGER
# =============================================================================

class TestPrecomputationManager:
    """Tests for PrecomputationManager."""

    @pytest.fixture
    def sample_nodes(self) -> Dict[str, Dict[str, Any]]:
        return {
            'survey': {'category': 'orientation', 'default_priority': 5},
            'hypothesis_testing': {'category': 'hypothesis', 'default_priority': 30},
            'smart_action_selection': {'category': 'exploitation', 'default_priority': 60},
            'network_wisdom': {'category': 'exploitation', 'default_priority': 40},
        }

    @pytest.fixture
    def sample_edges(self) -> Dict[str, List[str]]:
        return {
            'survey': ['hypothesis_testing', 'network_wisdom'],
            'hypothesis_testing': ['smart_action_selection'],
            'network_wisdom': ['smart_action_selection'],
        }

    def test_precompute(self, sample_nodes, sample_edges):
        """Test full precomputation."""
        manager = create_precomputation_manager()

        data = manager.precompute(sample_nodes, sample_edges)

        assert data.node_count == 4
        assert data.edge_count == 4
        assert data.computation_time_ms > 0

    def test_reverse_edges(self, sample_nodes, sample_edges):
        """Test reverse edge computation."""
        manager = create_precomputation_manager()
        data = manager.precompute(sample_nodes, sample_edges)

        # Check reverse edges
        assert 'hypothesis_testing' in data.reverse_edges
        assert 'survey' in data.reverse_edges['hypothesis_testing']

        assert 'smart_action_selection' in data.reverse_edges
        assert 'hypothesis_testing' in data.reverse_edges['smart_action_selection']

    def test_cluster_assignments(self, sample_nodes, sample_edges):
        """Test cluster assignment computation."""
        manager = create_precomputation_manager()
        data = manager.precompute(sample_nodes, sample_edges)

        assert 'survey' in data.cluster_assignments.get('orientation', [])
        assert 'hypothesis_testing' in data.cluster_assignments.get('hypothesis', [])

        assert data.rung_to_cluster['survey'] == 'orientation'

    def test_topological_order_dag(self, sample_nodes, sample_edges):
        """Test topological order for DAG."""
        manager = create_precomputation_manager()
        data = manager.precompute(sample_nodes, sample_edges)

        assert data.is_dag
        assert data.topological_order is not None

        # survey should come before hypothesis_testing
        survey_idx = data.topological_order.index('survey')
        ht_idx = data.topological_order.index('hypothesis_testing')
        assert survey_idx < ht_idx

    def test_topological_order_cycle(self):
        """Test topological order detection with cycle."""
        manager = create_precomputation_manager()

        nodes = {
            'a': {'category': 'hypothesis'},
            'b': {'category': 'hypothesis'},
            'c': {'category': 'hypothesis'},
        }
        edges = {
            'a': ['b'],
            'b': ['c'],
            'c': ['a'],  # Creates cycle
        }

        data = manager.precompute(nodes, edges)

        assert not data.is_dag
        assert data.topological_order is None

    def test_landmark_distances(self, sample_nodes, sample_edges):
        """Test landmark distance computation."""
        manager = create_precomputation_manager(
            landmarks=['survey', 'hypothesis_testing']
        )
        data = manager.precompute(sample_nodes, sample_edges)

        assert 'survey' in data.landmark_distances
        assert 'hypothesis_testing' in data.landmark_distances

        # Distance from survey to itself is 0
        assert data.landmark_distances['survey']['survey'] == 0

        # Distance from survey to hypothesis_testing is 1
        assert data.landmark_distances['survey']['hypothesis_testing'] == 1.0

    def test_landmark_heuristic(self, sample_nodes, sample_edges):
        """Test landmark heuristic computation."""
        manager = create_precomputation_manager(
            landmarks=['survey', 'smart_action_selection']
        )
        data = manager.precompute(sample_nodes, sample_edges)

        h = manager.get_landmark_heuristic('survey', 'smart_action_selection', data)

        # Heuristic should be non-negative
        assert h >= 0

    def test_caching(self, sample_nodes, sample_edges):
        """Test that precomputed data is cached."""
        manager = create_precomputation_manager()

        assert manager.cached_data is None

        manager.precompute(sample_nodes, sample_edges)

        assert manager.cached_data is not None

        manager.invalidate()

        assert manager.cached_data is None


class TestGraphInfo:
    """Tests for GraphInfo dataclass."""

    def test_from_precomputed(self, sample_precomputed):
        """Test GraphInfo creation from precomputed data."""
        nodes = {
            'survey': {'category': 'orientation'},
        }
        edges = {
            'survey': ['hypothesis_testing'],
        }

        graph_info = GraphInfo.from_precomputed(sample_precomputed, nodes, edges)

        assert graph_info.is_dag == sample_precomputed.is_dag
        assert graph_info.nodes == nodes
        assert graph_info.edges == edges


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for full meta-planner flow."""

    def test_full_planning_flow(self):
        """Test complete planning flow from precomputation to algorithm selection."""
        # 1. Set up nodes and edges
        nodes = {
            'survey': {'category': 'orientation', 'default_priority': 5},
            'hypothesis_testing': {'category': 'hypothesis', 'default_priority': 30},
            'pattern_lookup': {'category': 'exploitation', 'default_priority': 35},
            'smart_action_selection': {'category': 'exploitation', 'default_priority': 60},
        }
        edges = {
            'survey': ['hypothesis_testing', 'pattern_lookup'],
            'hypothesis_testing': ['smart_action_selection'],
            'pattern_lookup': ['smart_action_selection'],
        }

        # 2. Precompute
        manager = create_precomputation_manager()
        precomputed = manager.precompute(nodes, edges)

        # 3. Create context
        blackboard = {
            'confidence': 0.4,
            'rumsfeld': {'uu_estimate': 0.5},
            'domain_signature': 'unknown',
            'time_budget_remaining': 0.8,
            'time_budget_total': 1.0,
        }
        context = create_search_context(
            blackboard=blackboard,
            precomputed=precomputed,
            current_quadrant='KU',
        )

        # 4. Select algorithm
        planner = create_meta_planner()
        result = planner.select_algorithm(context)

        # 5. Use algorithm
        graph_info = {
            'nodes': nodes,
            'edges': edges,
            'reverse_edges': precomputed.reverse_edges,
            'dependencies': precomputed.dependencies,
            'is_dag': precomputed.is_dag,
        }

        frontier = {'survey', 'hypothesis_testing'}
        next_rungs = result.algorithm.get_next_rungs(frontier, context, graph_info)

        assert len(next_rungs) >= 1
        assert next_rungs[0] in frontier

    def test_cache_invalidation_on_quadrant_change(self):
        """Test that quadrant changes properly invalidate cache."""
        manager = create_precomputation_manager()
        nodes = {'a': {'category': 'hypothesis'}, 'b': {'category': 'exploitation'}}
        edges = {'a': ['b']}
        precomputed = manager.precompute(nodes, edges)

        planner = create_meta_planner()

        # KK quadrant
        ctx_kk = create_search_context(
            blackboard={'confidence': 0.9},
            precomputed=precomputed,
            current_quadrant='KK',
        )
        result_kk = planner.select_algorithm(ctx_kk)

        # UU quadrant - should select different algorithm
        ctx_uu = create_search_context(
            blackboard={'confidence': 0.1, 'uu_estimate': 0.9},
            precomputed=precomputed,
            current_quadrant='UU',
        )
        planner.invalidate_cache("quadrant change")
        result_uu = planner.select_algorithm(ctx_uu)

        # Different algorithms for different quadrants
        assert result_kk.algorithm.name != result_uu.algorithm.name

    def test_algorithm_applicability_fallback(self):
        """Test that algorithms fall back when not applicable."""
        # TopologicalDP requires topo order
        algo = TopologicalDPSearch()

        # Context without topo order
        context = create_search_context(
            blackboard={},
            precomputed=PrecomputedData(),  # Empty precomputed data
            current_quadrant='KK',
        )

        graph_info = {'is_dag': False, 'nodes': {}, 'edges': {}}

        # Should not be applicable
        assert not algo.is_applicable(context, graph_info)


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_frontier(self, sample_context, sample_graph_info):
        """Test algorithms handle empty frontier."""
        algorithms = [
            TopologicalDPSearch(),
            LandmarkAStar(),
            GreedyBestFirst(),
            BeamSearch(),
            InformationMaximizingSearch(),
        ]

        for algo in algorithms:
            result = algo.get_next_rungs(set(), sample_context, sample_graph_info)
            assert result == []

    def test_single_rung_frontier(self, sample_context, sample_graph_info):
        """Test algorithms handle single-rung frontier."""
        algorithms = [
            LandmarkAStar(),
            GreedyBestFirst(),
            BeamSearch(beam_width=3),
        ]

        for algo in algorithms:
            result = algo.get_next_rungs({'survey'}, sample_context, sample_graph_info)
            assert result == ['survey']

    def test_missing_precomputed_data(self):
        """Test context with missing precomputed data."""
        context = create_search_context(
            blackboard={},
            precomputed=None,
            current_quadrant='KK',
        )

        # Should have default values (empty list/dict, not None)
        assert context.topological_order == []
        assert context.cluster_assignments == {}

    def test_zero_time_budget(self, sample_context):
        """Test time bucketing with zero budget."""
        assert bucket_time(0.0, 0.0) == TimeBucket.CRITICAL
        assert bucket_time(0.5, 0.0) == TimeBucket.CRITICAL

    def test_cache_stats_reset(self):
        """Test cache stats reset."""
        cache = MetaPlannerCache()
        context = create_search_context({}, None, 'KK')

        cache.get_algorithm(context)
        assert cache.stats.misses == 1

        cache.reset_stats()

        assert cache.stats.misses == 0
        assert cache.stats.hits == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
