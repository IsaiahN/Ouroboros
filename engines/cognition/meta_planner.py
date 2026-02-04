"""
Meta-Planner with Caching - Algorithm Selection Orchestrator

Phase 3.1 Implementation - Cognitive Routing

This module implements the MetaPlanner with intelligent caching:
- Bucketed cache keys prevent thrashing (confidence 0.73→0.74 doesn't invalidate)
- Tiered selection: O(1) profile lookup → cached → full computation
- Invalidation only on algorithm-relevant slot changes
- Precomputed algorithm profiles for common cases

Key insight from Part 2: Algorithm selection drops from ~50 ops to ~5 for 90%+ of iterations.
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

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
)
from engines.cognition.search_context import SearchContext

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

# Slots that affect algorithm selection - invalidate cache when these change significantly
ALGORITHM_RELEVANT_SLOTS: Set[str] = {
    "complexity",
    "rumsfeld",
    "contradiction",
    "time_budget_remaining",
    "domain_signature",
    "max_confidence",
    "uu_estimate",
}


# =============================================================================
# BUCKETING FUNCTIONS
# =============================================================================

class ConfidenceBucket(Enum):
    """Discretized confidence levels to prevent cache thrashing."""
    LOW = "LOW"           # 0.0 - 0.3
    MEDIUM = "MEDIUM"     # 0.3 - 0.6
    HIGH = "HIGH"         # 0.6 - 0.9
    VERY_HIGH = "VERY_HIGH"  # 0.9 - 1.0


class UUBucket(Enum):
    """Discretized unknown-unknown levels."""
    LOW = "LOW"           # 0.0 - 0.33
    MEDIUM = "MEDIUM"     # 0.33 - 0.66
    HIGH = "HIGH"         # 0.66 - 1.0


class TimeBucket(Enum):
    """Discretized time budget levels."""
    PLENTY = "PLENTY"     # > 60% remaining
    LOW = "LOW"           # 20% - 60%
    CRITICAL = "CRITICAL" # < 20%


class ComplexityLevel(Enum):
    """Problem complexity levels."""
    SIMPLE = "SIMPLE"     # < 10 rungs active
    MEDIUM = "MEDIUM"     # 10 - 30 rungs
    COMPLEX = "COMPLEX"   # > 30 rungs


def bucket_confidence(conf: float) -> ConfidenceBucket:
    """Discretize confidence to reduce cache churn."""
    if conf < 0.3:
        return ConfidenceBucket.LOW
    if conf < 0.6:
        return ConfidenceBucket.MEDIUM
    if conf < 0.9:
        return ConfidenceBucket.HIGH
    return ConfidenceBucket.VERY_HIGH


def bucket_uu(uu: float) -> UUBucket:
    """Discretize unknown-unknown estimate."""
    if uu < 0.33:
        return UUBucket.LOW
    if uu < 0.66:
        return UUBucket.MEDIUM
    return UUBucket.HIGH


def bucket_time(time_remaining: float, total_budget: float = 1.0) -> TimeBucket:
    """Discretize time budget."""
    if total_budget <= 0:
        return TimeBucket.CRITICAL

    ratio = time_remaining / total_budget
    if ratio > 0.6:
        return TimeBucket.PLENTY
    if ratio > 0.2:
        return TimeBucket.LOW
    return TimeBucket.CRITICAL


def determine_complexity(active_rungs: int) -> ComplexityLevel:
    """Determine problem complexity from active rung count."""
    if active_rungs < 10:
        return ComplexityLevel.SIMPLE
    if active_rungs < 30:
        return ComplexityLevel.MEDIUM
    return ComplexityLevel.COMPLEX


# =============================================================================
# CACHE KEY
# =============================================================================

@dataclass(frozen=True)
class CacheKey:
    """
    Hashable cache key for algorithm selection.

    Uses bucketed values to prevent thrashing.
    Confidence 0.73 → 0.74 doesn't invalidate, but 0.59 → 0.61 does.
    """
    complexity: ComplexityLevel
    confidence: ConfidenceBucket
    uu_level: UUBucket
    has_contradiction: bool
    time_bucket: TimeBucket
    domain: str
    quadrant: str

    def __hash__(self) -> int:
        return hash((
            self.complexity,
            self.confidence,
            self.uu_level,
            self.has_contradiction,
            self.time_bucket,
            self.domain,
            self.quadrant,
        ))


def compute_cache_key(context: SearchContext) -> CacheKey:
    """Compute cache key from search context."""
    # Get bucketed values
    max_conf = context.get_confidence()
    uu_est = context.get_slot('uu_estimate', 0.5)

    # Time budget
    time_remaining = context.get_slot('time_budget_remaining', 1.0)
    total_budget = context.get_slot('time_budget_total', 1.0)

    # Contradiction state
    has_contradiction = bool(context.get_slot('contradiction'))

    # Domain and quadrant
    domain = context.get_slot('domain_signature', 'unknown')
    quadrant = context.current_quadrant

    # Active rungs for complexity
    visited_count = len(context.visited_rungs)

    return CacheKey(
        complexity=determine_complexity(visited_count),
        confidence=bucket_confidence(max_conf),
        uu_level=bucket_uu(uu_est),
        has_contradiction=has_contradiction,
        time_bucket=bucket_time(time_remaining, total_budget),
        domain=domain if isinstance(domain, str) else 'unknown',
        quadrant=quadrant,
    )


# =============================================================================
# ALGORITHM PROFILES (PRECOMPUTED)
# =============================================================================

@dataclass
class AlgorithmProfile:
    """Precomputed algorithm configuration for common situations."""
    algorithm: SearchAlgorithm
    description: str
    priority: int = 0  # Higher = more specific match


# Static profiles - computed once at startup
# Key: (complexity, confidence, uu, contradiction, time, domain_pattern)
# None = wildcard match
PRECOMPUTED_PROFILES: Dict[Tuple, AlgorithmProfile] = {}


def _init_profiles():
    """Initialize precomputed algorithm profiles."""
    global PRECOMPUTED_PROFILES

    # Contradiction ALWAYS triggers backtracking (highest priority)
    for complexity in ComplexityLevel:
        for conf in ConfidenceBucket:
            for uu in UUBucket:
                for time_b in TimeBucket:
                    PRECOMPUTED_PROFILES[(
                        complexity, conf, uu, True, time_b, None, None
                    )] = AlgorithmProfile(
                        algorithm=BacktrackingAStar(),
                        description="Contradiction detected - systematic backtrack",
                        priority=100
                    )

    # High confidence + simple problem = greedy
    PRECOMPUTED_PROFILES[(
        ComplexityLevel.SIMPLE, ConfidenceBucket.HIGH, UUBucket.LOW, False, TimeBucket.PLENTY, None, "KK"
    )] = AlgorithmProfile(
        algorithm=GreedyBestFirst(),
        description="Simple problem, high confidence, exploit",
        priority=50
    )

    PRECOMPUTED_PROFILES[(
        ComplexityLevel.SIMPLE, ConfidenceBucket.VERY_HIGH, UUBucket.LOW, False, TimeBucket.PLENTY, None, "KK"
    )] = AlgorithmProfile(
        algorithm=GreedyBestFirst(),
        description="Simple problem, very high confidence, greedy exploit",
        priority=50
    )

    # Low confidence + high UU = exploration
    PRECOMPUTED_PROFILES[(
        ComplexityLevel.MEDIUM, ConfidenceBucket.LOW, UUBucket.HIGH, False, TimeBucket.PLENTY, None, "UU"
    )] = AlgorithmProfile(
        algorithm=InformationMaximizingSearch(),
        description="Uncertain territory, maximize information",
        priority=40
    )

    # Time pressure = beam search
    for complexity in ComplexityLevel:
        for conf in ConfidenceBucket:
            for uu in UUBucket:
                PRECOMPUTED_PROFILES[(
                    complexity, conf, uu, False, TimeBucket.CRITICAL, None, None
                )] = AlgorithmProfile(
                    algorithm=BeamSearch(beam_width=2),
                    description="Critical time pressure - bounded search",
                    priority=80
                )

    # Physics domain = topological
    for complexity in ComplexityLevel:
        for conf in ConfidenceBucket:
            for uu in UUBucket:
                for time_b in [TimeBucket.PLENTY, TimeBucket.LOW]:
                    PRECOMPUTED_PROFILES[(
                        complexity, conf, uu, False, time_b, "physics", None
                    )] = AlgorithmProfile(
                        algorithm=TopologicalDPSearch(),
                        description="Physics domain - causal DAG structure",
                        priority=60
                    )

    # Symbolic domain = bidirectional
    for complexity in ComplexityLevel:
        for conf in ConfidenceBucket:
            for uu in UUBucket:
                for time_b in [TimeBucket.PLENTY, TimeBucket.LOW]:
                    PRECOMPUTED_PROFILES[(
                        complexity, conf, uu, False, time_b, "symbolic", None
                    )] = AlgorithmProfile(
                        algorithm=BidirectionalSearch(),
                        description="Symbolic domain - known goal state",
                        priority=60
                    )

    # Spatial domain = hierarchical
    for complexity in ComplexityLevel:
        for conf in ConfidenceBucket:
            for uu in UUBucket:
                for time_b in [TimeBucket.PLENTY, TimeBucket.LOW]:
                    PRECOMPUTED_PROFILES[(
                        complexity, conf, uu, False, time_b, "spatial", None
                    )] = AlgorithmProfile(
                        algorithm=HierarchicalAStar(),
                        description="Spatial domain - region clusters",
                        priority=60
                    )

    # KU quadrant = targeted question search
    for complexity in ComplexityLevel:
        for conf in ConfidenceBucket:
            for uu in UUBucket:
                for time_b in [TimeBucket.PLENTY, TimeBucket.LOW]:
                    PRECOMPUTED_PROFILES[(
                        complexity, conf, uu, False, time_b, None, "KU"
                    )] = AlgorithmProfile(
                        algorithm=TargetedQuestionSearch(),
                        description="KU quadrant - search toward question answerers",
                        priority=45
                    )

    # UK quadrant = retrieval search
    for complexity in ComplexityLevel:
        for conf in ConfidenceBucket:
            for uu in UUBucket:
                for time_b in [TimeBucket.PLENTY, TimeBucket.LOW]:
                    PRECOMPUTED_PROFILES[(
                        complexity, conf, uu, False, time_b, None, "UK"
                    )] = AlgorithmProfile(
                        algorithm=RetrievalSearch(),
                        description="UK quadrant - retrieve cached knowledge",
                        priority=45
                    )


def _profile_matches(profile_key: Tuple, cache_key: CacheKey) -> bool:
    """Check if a profile key matches a cache key (with wildcards)."""
    complexity, conf, uu, contradiction, time_b, domain, quadrant = profile_key

    # Wildcard matching
    if complexity is not None and complexity != cache_key.complexity:
        return False
    if conf is not None and conf != cache_key.confidence:
        return False
    if uu is not None and uu != cache_key.uu_level:
        return False
    if contradiction is not None and contradiction != cache_key.has_contradiction:
        return False
    if time_b is not None and time_b != cache_key.time_bucket:
        return False
    if domain is not None and domain != cache_key.domain:
        return False
    if quadrant is not None and quadrant != cache_key.quadrant:
        return False

    return True


def lookup_profile(cache_key: CacheKey) -> Optional[AlgorithmProfile]:
    """O(1) lookup for precomputed profiles with wildcard support."""
    # Try exact match first (fast path)
    exact_key = (
        cache_key.complexity,
        cache_key.confidence,
        cache_key.uu_level,
        cache_key.has_contradiction,
        cache_key.time_bucket,
        cache_key.domain,
        cache_key.quadrant,
    )
    if exact_key in PRECOMPUTED_PROFILES:
        return PRECOMPUTED_PROFILES[exact_key]

    # Find best matching profile
    best_profile: Optional[AlgorithmProfile] = None
    best_priority = -1

    for profile_key, profile in PRECOMPUTED_PROFILES.items():
        if _profile_matches(profile_key, cache_key):
            if profile.priority > best_priority:
                best_profile = profile
                best_priority = profile.priority

    return best_profile


# Initialize profiles at module load
_init_profiles()


# =============================================================================
# META-PLANNER CACHE
# =============================================================================

@dataclass
class CacheStats:
    """Statistics for cache performance monitoring."""
    hits: int = 0
    misses: int = 0
    invalidations: int = 0
    profile_hits: int = 0
    full_computations: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    @property
    def profile_rate(self) -> float:
        total = self.profile_hits + self.full_computations
        return self.profile_hits / total if total > 0 else 0.0


class MetaPlannerCache:
    """
    Cache algorithm selection with smart invalidation.

    Three-tier selection:
    1. Profile lookup: O(1) for common cases (90%+ of iterations)
    2. Cache hit: O(1) if already computed for this key
    3. Full computation: Only when cache key changes significantly
    """

    def __init__(self, default_algorithm: Optional[SearchAlgorithm] = None):
        self._cached_algorithm: Optional[SearchAlgorithm] = None
        self._cache_key: Optional[CacheKey] = None
        self._default_algorithm = default_algorithm or LandmarkAStar()
        self._stats = CacheStats()

        # Selection callback for full computation
        self._select_algorithm_impl: Optional[Callable[[SearchContext], SearchAlgorithm]] = None

    @property
    def stats(self) -> CacheStats:
        """Get cache performance statistics."""
        return self._stats

    def set_selector(self, selector: Callable[[SearchContext], SearchAlgorithm]):
        """Set the full algorithm selection implementation."""
        self._select_algorithm_impl = selector

    def get_algorithm(self, context: SearchContext) -> SearchAlgorithm:
        """
        Get algorithm for current context with caching.

        Selection order:
        1. Try precomputed profile (O(1), handles 90%+)
        2. Try cache hit (O(1))
        3. Fall back to full computation
        """
        current_key = compute_cache_key(context)

        # Check cache first
        if self._cache_key == current_key and self._cached_algorithm:
            self._stats.hits += 1
            return self._cached_algorithm

        self._stats.misses += 1

        # Try profile lookup
        profile = lookup_profile(current_key)
        if profile:
            self._stats.profile_hits += 1
            self._cached_algorithm = profile.algorithm
            self._cache_key = current_key
            logger.debug(f"[CACHE] Profile hit: {profile.description}")
            return profile.algorithm

        # Full computation
        self._stats.full_computations += 1
        if self._select_algorithm_impl:
            self._cached_algorithm = self._select_algorithm_impl(context)
        else:
            # Fallback selection based on quadrant
            self._cached_algorithm = self._default_select(context)

        self._cache_key = current_key
        return self._cached_algorithm

    def _default_select(self, context: SearchContext) -> SearchAlgorithm:
        """Default algorithm selection based on quadrant."""
        quadrant = context.current_quadrant

        # Map quadrant to algorithm
        quadrant_map = {
            'KK': GreedyBestFirst(),
            'KU': TargetedQuestionSearch(),
            'UK': RetrievalSearch(),
            'UU': InformationMaximizingSearch(),
        }

        return quadrant_map.get(quadrant, self._default_algorithm)

    def invalidate(self, reason: str = "manual"):
        """Force recomputation on next call."""
        self._cache_key = None
        self._cached_algorithm = None
        self._stats.invalidations += 1
        logger.debug(f"[CACHE] Invalidated: {reason}")

    def should_invalidate(self, slot_name: str, old_value: Any, new_value: Any) -> bool:
        """
        Check if a slot change should invalidate the cache.

        Only invalidates for algorithm-relevant slots with significant change.
        """
        if slot_name not in ALGORITHM_RELEVANT_SLOTS:
            return False

        return self._value_changed_significantly(slot_name, old_value, new_value)

    def _value_changed_significantly(
        self,
        slot_name: str,
        old_value: Any,
        new_value: Any
    ) -> bool:
        """Check if value changed enough to warrant cache invalidation."""
        if old_value is None or new_value is None:
            return old_value != new_value

        # For numeric values, check if bucket changed
        if slot_name == 'max_confidence' or slot_name == 'confidence':
            old_bucket = bucket_confidence(float(old_value))
            new_bucket = bucket_confidence(float(new_value))
            return old_bucket != new_bucket

        if slot_name == 'uu_estimate':
            old_bucket = bucket_uu(float(old_value))
            new_bucket = bucket_uu(float(new_value))
            return old_bucket != new_bucket

        if slot_name == 'time_budget_remaining':
            # Need total budget for proper bucketing
            # Assume significant if crosses 20% or 60% threshold
            old_ratio = float(old_value)
            new_ratio = float(new_value)
            old_bucket = bucket_time(old_ratio)
            new_bucket = bucket_time(new_ratio)
            return old_bucket != new_bucket

        # For other values, any change is significant
        return old_value != new_value

    def reset_stats(self):
        """Reset cache statistics."""
        self._stats = CacheStats()


# =============================================================================
# META-PLANNER
# =============================================================================

@dataclass
class SelectionResult:
    """Result of algorithm selection."""
    algorithm: SearchAlgorithm
    cache_hit: bool
    profile_hit: bool
    selection_time_ms: float
    reason: str


class MetaPlanner:
    """
    Algorithm selection orchestrator with caching.

    Implements the cognitive routing meta-planner that:
    1. Selects optimal search algorithm based on context
    2. Caches selections to avoid redundant computation
    3. Invalidates cache only on significant changes
    """

    def __init__(self):
        self._cache = MetaPlannerCache()
        self._selection_history: List[SelectionResult] = []

        # Configure custom selector if needed
        self._cache.set_selector(self._full_select)

    def select_algorithm(
        self,
        context: SearchContext,
        graph_info: Optional[Dict[str, Any]] = None
    ) -> SelectionResult:
        """
        Select the optimal algorithm for the current context.

        Args:
            context: Current search context
            graph_info: Optional graph structure information

        Returns:
            SelectionResult with algorithm and metadata
        """
        start_time = time.perf_counter()

        # Get stats before selection
        prev_hits = self._cache.stats.hits
        prev_profile = self._cache.stats.profile_hits

        # Get algorithm through cache
        algorithm = self._cache.get_algorithm(context)

        # Determine how we got it
        cache_hit = self._cache.stats.hits > prev_hits
        profile_hit = self._cache.stats.profile_hits > prev_profile

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Determine reason
        if cache_hit:
            reason = "cache_hit"
        elif profile_hit:
            reason = f"profile_match"
        else:
            reason = "full_computation"

        result = SelectionResult(
            algorithm=algorithm,
            cache_hit=cache_hit,
            profile_hit=profile_hit,
            selection_time_ms=elapsed_ms,
            reason=reason,
        )

        self._selection_history.append(result)

        logger.debug(
            f"[META-PLANNER] Selected {algorithm.name} via {reason} "
            f"in {elapsed_ms:.2f}ms"
        )

        return result

    def _full_select(self, context: SearchContext) -> SearchAlgorithm:
        """
        Full algorithm selection when cache misses.

        Selection hierarchy:
        1. Contradiction -> BacktrackingAStar
        2. Time critical -> BeamSearch
        3. Domain-specific -> Appropriate algorithm
        4. Quadrant-based -> Appropriate algorithm
        5. Fallback -> LandmarkAStar
        """
        # 1. Contradiction override
        if context.get_slot('contradiction'):
            return BacktrackingAStar()

        # 2. Time pressure override
        time_remaining = context.get_slot('time_budget_remaining', 1.0)
        total_budget = context.get_slot('time_budget_total', 1.0)
        if total_budget > 0 and time_remaining / total_budget < 0.2:
            return BeamSearch(beam_width=2)

        # 3. Domain-specific selection
        domain = context.get_slot('domain_signature', 'unknown')
        if domain and domain != 'unknown':
            domain_config = DOMAIN_ALGORITHMS.get(domain)
            if domain_config:
                primary_name = domain_config.get('primary', 'landmark_astar')
                return get_algorithm(primary_name)

        # 4. Quadrant-based selection
        quadrant = context.current_quadrant
        quadrant_name = QUADRANT_ALGORITHMS.get(quadrant, 'landmark_astar')
        return get_algorithm(quadrant_name)

    def notify_slot_change(self, slot_name: str, old_value: Any, new_value: Any):
        """Notify the meta-planner of a slot change for cache invalidation."""
        if self._cache.should_invalidate(slot_name, old_value, new_value):
            self._cache.invalidate(f"slot_change:{slot_name}")

    def invalidate_cache(self, reason: str = "manual"):
        """Manually invalidate the algorithm cache."""
        self._cache.invalidate(reason)

    @property
    def cache_stats(self) -> CacheStats:
        """Get cache performance statistics."""
        return self._cache.stats

    def get_selection_summary(self) -> Dict[str, Any]:
        """Get summary of selection history."""
        if not self._selection_history:
            return {
                "total_selections": 0,
                "cache_hit_rate": 0.0,
                "profile_hit_rate": 0.0,
                "avg_selection_time_ms": 0.0,
            }

        cache_hits = sum(1 for r in self._selection_history if r.cache_hit)
        profile_hits = sum(1 for r in self._selection_history if r.profile_hit)
        total = len(self._selection_history)

        return {
            "total_selections": total,
            "cache_hit_rate": cache_hits / total,
            "profile_hit_rate": profile_hits / total,
            "avg_selection_time_ms": sum(r.selection_time_ms for r in self._selection_history) / total,
            "algorithm_distribution": self._get_algorithm_distribution(),
        }

    def _get_algorithm_distribution(self) -> Dict[str, int]:
        """Get distribution of algorithms selected."""
        distribution: Dict[str, int] = {}
        for result in self._selection_history:
            name = result.algorithm.name
            distribution[name] = distribution.get(name, 0) + 1
        return distribution


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_meta_planner() -> MetaPlanner:
    """Create a new MetaPlanner instance."""
    return MetaPlanner()


def create_cache(default_algorithm: Optional[SearchAlgorithm] = None) -> MetaPlannerCache:
    """Create a new MetaPlannerCache instance."""
    return MetaPlannerCache(default_algorithm)
