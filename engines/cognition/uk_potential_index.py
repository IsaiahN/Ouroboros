"""
UK Potential Index for Epistemic State Machine.

This module provides O(1) lookup for "do we have cached knowledge?" (UK quadrant).

Phase 1.6.3 of cognitive_routing_implementation_plan.md

Problem: Checking for cached knowledge requires DB queries which are too slow
during routing decisions.

Solution: Maintain a lightweight UK Potential Index with:
1. Bloom filter for fast "definitely no" responses
2. Dictionary for detailed cache info
3. Cold-start fallback for first game / new game types

The index is populated once at game start (async from routing) and queried
during routing for O(1) "might we know?" checks.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Set

logger = logging.getLogger(__name__)


# =============================================================================
# UK ENTRY
# =============================================================================

@dataclass
class UKEntry:
    """
    Entry in the UK Potential Index.

    Represents cached knowledge that a specific rung might access.
    """
    rung_name: str
    has_cached: bool          # Does this rung have cached knowledge?
    cache_count: int          # Number of cached items
    relevance: float          # 0.0 to 1.0, relevance to current game
    last_updated: int         # Tick when last refreshed
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional info


# =============================================================================
# SIMPLE BLOOM FILTER
# =============================================================================

class SimpleBloomFilter:
    """
    Simple bloom filter for fast "definitely no" checks.

    Uses built-in hash functions instead of mmh3 to avoid dependency.
    False positive rate depends on size and number of items.
    """

    def __init__(self, size_bytes: int = 1024, hash_count: int = 3):
        """
        Initialize bloom filter.

        Args:
            size_bytes: Size of filter in bytes (default 1KB)
            hash_count: Number of hash functions to use
        """
        self.size_bits = size_bytes * 8
        self.filter = bytearray(size_bytes)
        self.hash_count = hash_count
        self._item_count = 0

    def add(self, item: str) -> None:
        """Add an item to the filter."""
        for i in range(self.hash_count):
            # Use different seeds for each hash
            idx = self._hash(item, i) % self.size_bits
            byte_idx = idx // 8
            bit_idx = idx % 8
            self.filter[byte_idx] |= (1 << bit_idx)
        self._item_count += 1

    def might_contain(self, item: str) -> bool:
        """
        Check if item might be in the filter.

        Returns:
            False = definitely not in filter
            True = might be in filter (possible false positive)
        """
        for i in range(self.hash_count):
            idx = self._hash(item, i) % self.size_bits
            byte_idx = idx // 8
            bit_idx = idx % 8
            if not (self.filter[byte_idx] & (1 << bit_idx)):
                return False
        return True

    def reset(self) -> None:
        """Clear the filter."""
        self.filter = bytearray(len(self.filter))
        self._item_count = 0

    def _hash(self, item: str, seed: int) -> int:
        """Hash function with seed."""
        # Simple hash combining Python's hash with seed
        h = hash(item) ^ (seed * 0x9e3779b9)
        return abs(h)

    @property
    def estimated_false_positive_rate(self) -> float:
        """Estimate false positive rate based on fill ratio."""
        if self._item_count == 0:
            return 0.0
        # Approximate: (1 - e^(-kn/m))^k
        # where k=hash_count, n=item_count, m=size_bits
        import math
        k = self.hash_count
        n = self._item_count
        m = self.size_bits
        try:
            return (1 - math.exp(-k * n / m)) ** k
        except (ValueError, OverflowError):
            return 1.0


# =============================================================================
# STRUCTURAL UK METADATA (Cold-Start Fallback)
# =============================================================================

# Rungs that structurally might have cached/network knowledge
# Used when DB is empty (first game, new game type)
STRUCTURAL_UK_RUNGS: Dict[str, Dict[str, Any]] = {
    "network_wisdom": {
        "has_network_component": True,
        "always_worth_trying": True,
        "description": "Collective wisdom from agent network"
    },
    "prior_lessons": {
        "has_cache": True,
        "description": "Lessons learned from previous games"
    },
    "embedding_suggestion": {
        "has_cache": True,
        "description": "Embedding-based action suggestions"
    },
    "rule_transfer": {
        "has_network_component": True,
        "description": "Rules that transfer across games"
    },
    "abstraction_templates": {
        "has_network_component": True,
        "description": "Abstract patterns that might apply"
    },
    "global_game_patterns": {
        "has_network_component": True,
        "description": "Patterns observed across all games"
    },
    "similar_game_lookup": {
        "has_cache": True,
        "description": "Knowledge from similar games"
    },
    "winning_sequence_replay": {
        "has_cache": True,
        "description": "Known winning sequences"
    },
}


# =============================================================================
# UK POTENTIAL INDEX
# =============================================================================

class UKPotentialIndex:
    """
    Lightweight index for O(1) "might we know?" checks.

    The index is populated once at game start (async from routing) and
    provides fast lookups during routing decisions.

    Usage:
        index = UKPotentialIndex()

        # At game start (async)
        index.populate_for_game(game_id, game_type, db_query_func)

        # During routing (O(1))
        if index.has_potential("network_wisdom"):
            # Worth trying to retrieve cached knowledge
            ...

        # When knowledge is accessed
        index.mark_surfaced("network_wisdom")
    """

    # Minimum relevance threshold
    DEFAULT_MIN_RELEVANCE = 0.3

    def __init__(self, bloom_size: int = 1024):
        """
        Initialize the UK Potential Index.

        Args:
            bloom_size: Size of bloom filter in bytes
        """
        self.index: Dict[str, UKEntry] = {}
        self.bloom = SimpleBloomFilter(size_bytes=bloom_size)
        self._is_cold_start = False
        self._game_id: Optional[str] = None
        self._game_type: Optional[str] = None

    def reset(self) -> None:
        """Reset index for a new game."""
        self.index.clear()
        self.bloom.reset()
        self._is_cold_start = False
        self._game_id = None
        self._game_type = None

    def populate_for_game(
        self,
        game_id: str,
        game_type: str,
        db_query_func: Optional[Callable[[str, str], Dict[str, Dict[str, Any]]]] = None
    ) -> None:
        """
        Populate index at game start.

        This queries the DB once (not during routing) and builds the index.

        Args:
            game_id: Current game ID
            game_type: Type of game (for relevance filtering)
            db_query_func: Function to query cached knowledge availability
                           Signature: (game_id, game_type) -> {rung_name: {count, relevance}}
        """
        self.reset()
        self._game_id = game_id
        self._game_type = game_type

        # Query DB for available cached knowledge
        if db_query_func:
            try:
                available = db_query_func(game_id, game_type)
            except Exception as e:
                logger.warning(f"DB query failed, using cold-start fallback: {e}")
                available = {}
        else:
            available = {}

        # Check for cold-start
        if self._is_cold_start_result(available):
            logger.info("UK Index: Cold-start detected, using structural fallback")
            self._is_cold_start = True
            self.populate_structural_fallback()
            return

        # Populate from DB results
        for rung_name, cache_info in available.items():
            count = cache_info.get("count", 0)
            relevance = cache_info.get("relevance", 0.0)

            entry = UKEntry(
                rung_name=rung_name,
                has_cached=count > 0,
                cache_count=count,
                relevance=relevance,
                last_updated=0,
                metadata=cache_info
            )
            self.index[rung_name] = entry

            if count > 0:
                self.bloom.add(rung_name)

        logger.debug(
            f"UK Index populated: {len(self.index)} rungs, "
            f"{sum(1 for e in self.index.values() if e.has_cached)} with cache"
        )

    def populate_structural_fallback(self) -> None:
        """
        Fallback for cold-start: first game ever or new game type never seen.

        Uses structural metadata about which rungs COULD have knowledge.
        """
        for rung_name, metadata in STRUCTURAL_UK_RUNGS.items():
            entry = UKEntry(
                rung_name=rung_name,
                has_cached=True,  # Assume yes until proven otherwise
                cache_count=0,    # Unknown count
                relevance=0.5,    # Default relevance
                last_updated=0,
                metadata=metadata
            )
            self.index[rung_name] = entry
            self.bloom.add(rung_name)

        logger.debug(f"UK Index: Structural fallback with {len(self.index)} potential rungs")

    def has_potential(
        self,
        rung_name: str,
        min_relevance: Optional[float] = None
    ) -> bool:
        """
        O(1) check: Does this rung have cached knowledge worth accessing?

        Args:
            rung_name: Name of the rung to check
            min_relevance: Minimum relevance threshold (uses default if None)

        Returns:
            True if rung has potentially valuable cached knowledge
        """
        if min_relevance is None:
            min_relevance = self.DEFAULT_MIN_RELEVANCE

        # Fast bloom filter check first
        if not self.bloom.might_contain(rung_name):
            return False  # Definitely no

        # Check index for details
        entry = self.index.get(rung_name)
        if not entry:
            return False

        return entry.has_cached and entry.relevance >= min_relevance

    def get_potential_rungs(
        self,
        min_relevance: Optional[float] = None
    ) -> list[str]:
        """
        Get all rungs with cached knowledge above relevance threshold.

        Args:
            min_relevance: Minimum relevance threshold

        Returns:
            List of rung names sorted by relevance (highest first)
        """
        if min_relevance is None:
            min_relevance = self.DEFAULT_MIN_RELEVANCE

        matching = [
            entry for entry in self.index.values()
            if entry.has_cached and entry.relevance >= min_relevance
        ]

        matching.sort(key=lambda e: e.relevance, reverse=True)
        return [e.rung_name for e in matching]

    def get_entry(self, rung_name: str) -> Optional[UKEntry]:
        """Get detailed entry for a rung."""
        return self.index.get(rung_name)

    def mark_surfaced(self, rung_name: str) -> None:
        """
        Mark that cached knowledge was accessed (UK -> KK).

        After surfacing, the knowledge is no longer "unknown known" -
        it's now "known known" (or we found it was empty).
        """
        if rung_name in self.index:
            self.index[rung_name].has_cached = False  # No longer "unknown"
            logger.debug(f"UK Index: {rung_name} surfaced (UK->KK)")

    def mark_empty(self, rung_name: str) -> None:
        """Mark that a rung's cache was actually empty (false positive)."""
        if rung_name in self.index:
            self.index[rung_name].has_cached = False
            self.index[rung_name].cache_count = 0

    def update_relevance(self, rung_name: str, new_relevance: float) -> None:
        """Update relevance for a rung based on game progress."""
        if rung_name in self.index:
            self.index[rung_name].relevance = max(0.0, min(1.0, new_relevance))

    def _is_cold_start_result(self, db_result: Dict) -> bool:
        """Check if this is a cold-start situation (no cached data)."""
        if not db_result:
            return True
        return all(
            info.get("count", 0) == 0
            for info in db_result.values()
        )

    @property
    def is_cold_start(self) -> bool:
        """Check if index is in cold-start mode."""
        return self._is_cold_start

    @property
    def total_potential(self) -> float:
        """
        Calculate total UK potential (sum of relevances for cached rungs).

        Returns:
            Total potential score (higher = more untapped knowledge)
        """
        return sum(
            e.relevance for e in self.index.values()
            if e.has_cached
        )

    @property
    def potential_count(self) -> int:
        """Number of rungs with cached knowledge."""
        return sum(1 for e in self.index.values() if e.has_cached)

    def get_statistics(self) -> Dict[str, Any]:
        """Get index statistics for monitoring."""
        return {
            "game_id": self._game_id,
            "game_type": self._game_type,
            "is_cold_start": self._is_cold_start,
            "total_entries": len(self.index),
            "with_cache": self.potential_count,
            "total_potential": self.total_potential,
            "bloom_fpp_estimate": self.bloom.estimated_false_positive_rate,
        }

    def __repr__(self) -> str:
        return (
            f"UKPotentialIndex(entries={len(self.index)}, "
            f"potential={self.potential_count}, "
            f"cold_start={self._is_cold_start})"
        )
