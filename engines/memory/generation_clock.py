"""
Generation Clock - Hardware-Agnostic Time for the Network

Provides a centralized, generation-based time model that decouples the system
from wall-clock time. This makes behavior consistent across different hardware
speeds and allows knowledge decay/relevance to be measured in evolutionary terms.

DESIGN PRINCIPLE:
    Wall-clock time measures compute speed.
    Generation time measures learning opportunity.

A fast machine running 100 generations/hour and a slow machine running
10 generations/hour should treat 50-generation-old knowledge identically.
The fast machine just accumulated more experience, not "older" knowledge.

COMPOSITE TIME MODEL:
    composite_time = generation + (action_in_generation / max_actions_per_generation)

    This gives sub-generation granularity while keeping the generation as the
    fundamental unit. A composite_time of 42.75 means "generation 42, 75% through."

WHEN TO USE GENERATION TIME:
    - Knowledge decay (embeddings, patterns, lessons)
    - Experience relevance (how recent is this learning?)
    - Evolutionary metrics (prestige decay, pariah toxicity)
    - Cross-agent comparisons (when was this discovered?)

WHEN TO KEEP WALL-CLOCK:
    - API timeouts (network latency is real)
    - User-facing displays (humans think in seconds)
    - Performance profiling (measuring actual compute)
    - Database timestamps (for debugging/audit trails)
"""

from __future__ import annotations

import math
import threading
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

# Default assumptions for composite time calculation
DEFAULT_MAX_ACTIONS_PER_GENERATION = 7000  # From copilot-instructions.md


@dataclass
class GenerationContext:
    """
    Snapshot of current generation state.

    Immutable snapshot that can be passed around without worrying about
    the clock advancing mid-computation.
    """
    generation: int
    action_in_generation: int
    max_actions: int = DEFAULT_MAX_ACTIONS_PER_GENERATION

    @property
    def composite_time(self) -> float:
        """Get composite time as generation + fractional progress."""
        if self.max_actions <= 0:
            return float(self.generation)
        return self.generation + (self.action_in_generation / self.max_actions)

    @property
    def progress_fraction(self) -> float:
        """Get progress through current generation as 0.0-1.0."""
        if self.max_actions <= 0:
            return 0.0
        return min(1.0, self.action_in_generation / self.max_actions)

    def generations_since(self, other_composite_time: float) -> float:
        """Calculate generations elapsed since another composite time."""
        return self.composite_time - other_composite_time

    def to_dict(self) -> Dict[str, float]:
        """Serialize for storage/transmission."""
        return {
            'generation': self.generation,
            'action_in_generation': self.action_in_generation,
            'max_actions': self.max_actions,
            'composite_time': self.composite_time
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'GenerationContext':
        """Deserialize from storage."""
        return cls(
            generation=int(data.get('generation', 0)),
            action_in_generation=int(data.get('action_in_generation', 0)),
            max_actions=int(data.get('max_actions', DEFAULT_MAX_ACTIONS_PER_GENERATION))
        )


class GenerationClock:
    """
    Singleton clock providing generation-based time to the entire system.

    Thread-safe. Multiple agents/components can query the clock simultaneously.
    The clock is advanced by the evolution runner, not by individual agents.

    Usage:
        clock = GenerationClock.instance()
        clock.set_generation(42, action=150)
        ctx = clock.get_context()
        print(f"Composite time: {ctx.composite_time}")  # 42.021...
    """

    _instance: Optional['GenerationClock'] = None
    _lock = threading.Lock()

    def __new__(cls) -> 'GenerationClock':
        """Singleton pattern - only one clock exists."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize clock state (only runs once due to singleton)."""
        if getattr(self, '_initialized', False):
            return

        self._generation: int = 0
        self._action_in_generation: int = 0
        self._max_actions: int = DEFAULT_MAX_ACTIONS_PER_GENERATION
        self._state_lock = threading.RLock()
        self._initialized = True

    @classmethod
    def instance(cls) -> 'GenerationClock':
        """Get the singleton instance."""
        return cls()

    def set_generation(
        self,
        generation: int,
        action: int = 0,
        max_actions: Optional[int] = None
    ) -> None:
        """
        Set current generation state.

        Called by evolution runner at generation boundaries and
        optionally updated during gameplay.

        Args:
            generation: Current generation number
            action: Action count within this generation
            max_actions: Override max actions per generation
        """
        with self._state_lock:
            self._generation = generation
            self._action_in_generation = action
            if max_actions is not None:
                self._max_actions = max_actions

    def advance_action(self, count: int = 1) -> None:
        """Increment action counter within current generation."""
        with self._state_lock:
            self._action_in_generation += count

    def get_context(self) -> GenerationContext:
        """
        Get immutable snapshot of current time.

        Returns a frozen context that won't change even if the clock advances.
        """
        with self._state_lock:
            return GenerationContext(
                generation=self._generation,
                action_in_generation=self._action_in_generation,
                max_actions=self._max_actions
            )

    @property
    def composite_time(self) -> float:
        """Get current composite time (convenience property)."""
        return self.get_context().composite_time

    @property
    def generation(self) -> int:
        """Get current generation (convenience property)."""
        with self._state_lock:
            return self._generation


# ============================================================================
# DECAY UTILITIES
# ============================================================================

def compute_generation_decay(
    generations_elapsed: float,
    half_life_generations: float,
    floor: float = 0.0
) -> float:
    """
    Compute exponential decay weight based on generations elapsed.

    Args:
        generations_elapsed: How many generations since the event
        half_life_generations: Generations for weight to halve
        floor: Minimum weight (prevents total forgetting)

    Returns:
        Weight between floor and 1.0

    Example:
        # 30-generation half-life for embeddings
        weight = compute_generation_decay(
            generations_elapsed=45,
            half_life_generations=30
        )
        # Returns ~0.35 (45 gens = 1.5 half-lives)
    """
    if half_life_generations <= 0:
        return 1.0 if generations_elapsed <= 0 else floor

    if generations_elapsed <= 0:
        return 1.0

    decay = 0.5 ** (generations_elapsed / half_life_generations)
    return max(floor, decay)


def compute_access_boost(
    access_count: int,
    max_boost: float = 1.5,
    saturation_accesses: int = 10
) -> float:
    """
    Compute boost factor based on access frequency.

    Frequently-accessed knowledge is likely more useful.
    Uses logarithmic saturation to prevent runaway boosts.

    Args:
        access_count: How many times this item was accessed
        max_boost: Maximum boost multiplier
        saturation_accesses: Access count for ~90% of max boost

    Returns:
        Multiplier between 1.0 and max_boost

    Example:
        boost = compute_access_boost(access_count=5, max_boost=1.5)
        # Returns ~1.35
    """
    if access_count <= 0:
        return 1.0

    # Logarithmic saturation: boost approaches max_boost asymptotically
    # Formula: 1 + (max_boost - 1) * (1 - e^(-access_count / saturation_k))
    saturation_k = saturation_accesses / 2.3  # ~90% at saturation_accesses
    boost_fraction = 1 - math.exp(-access_count / saturation_k)

    return 1.0 + (max_boost - 1.0) * boost_fraction


def compute_relevance_score(
    base_similarity: float,
    generations_elapsed: float,
    access_count: int = 0,
    half_life_generations: float = 30.0,
    access_max_boost: float = 1.5,
    recency_weight: float = 0.3
) -> float:
    """
    Compute composite relevance score combining similarity, recency, and access.

    This is the recommended function for ranking retrieved knowledge.

    Formula:
        relevance = base_similarity * (
            (1 - recency_weight) +
            recency_weight * decay * access_boost
        )

    Args:
        base_similarity: Raw similarity score (e.g., cosine similarity)
        generations_elapsed: Generations since this knowledge was stored
        access_count: How many times this was accessed
        half_life_generations: Decay half-life
        access_max_boost: Maximum access frequency boost
        recency_weight: How much recency matters (0=none, 1=fully)

    Returns:
        Adjusted relevance score

    Example:
        # Rank embeddings by relevance
        relevance = compute_relevance_score(
            base_similarity=0.85,
            generations_elapsed=20,
            access_count=3,
            half_life_generations=30
        )
    """
    decay = compute_generation_decay(generations_elapsed, half_life_generations)
    boost = compute_access_boost(access_count, access_max_boost)

    # Blend: mostly similarity, but recency/access can adjust ranking
    recency_factor = decay * boost

    return base_similarity * ((1 - recency_weight) + recency_weight * recency_factor)


# ============================================================================
# HALF-LIFE CONSTANTS BY KNOWLEDGE TYPE
# ============================================================================

@dataclass
class KnowledgeDecayConfig:
    """
    Decay configuration for different knowledge types.

    Based on analysis in thoughts.md and temporal_decay_implementation_plan.md:
    - Fast-changing tactical knowledge decays quickly
    - Proven patterns decay slowly
    - Cross-domain knowledge decays faster (0.7x half-life)
    """
    # Generation-based half-lives
    EMBEDDING_HALF_LIFE: float = 30.0        # Frame embeddings
    LESSON_HALF_LIFE: float = 15.0           # Game-specific lessons
    CHECKPOINT_HALF_LIFE: float = 50.0       # Frontier checkpoints
    DEATH_PATTERN_HALF_LIFE: float = 10.0    # Terminal state patterns
    HYPOTHESIS_HALF_LIFE: float = 20.0       # Unconfirmed hypotheses

    # Winning sequences: NO DECAY (they're proven correct)
    # Pariah patterns: Separate decay in pariah_manager.py

    # Cross-domain penalty (multiply half-life by this when crossing games)
    CROSS_DOMAIN_MULTIPLIER: float = 0.7

    def get_half_life(
        self,
        knowledge_type: str,
        cross_domain: bool = False
    ) -> float:
        """Get half-life for knowledge type, with cross-domain adjustment."""
        half_lives = {
            'embedding': self.EMBEDDING_HALF_LIFE,
            'lesson': self.LESSON_HALF_LIFE,
            'checkpoint': self.CHECKPOINT_HALF_LIFE,
            'death_pattern': self.DEATH_PATTERN_HALF_LIFE,
            'hypothesis': self.HYPOTHESIS_HALF_LIFE,
        }

        base = half_lives.get(knowledge_type, 30.0)

        if cross_domain:
            return base * self.CROSS_DOMAIN_MULTIPLIER
        return base


# Singleton config instance
DECAY_CONFIG = KnowledgeDecayConfig()
