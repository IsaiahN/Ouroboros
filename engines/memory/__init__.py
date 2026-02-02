"""
Memory Engines Package

Provides memory systems for agent experience tracking, recall, and learning from failures.

Components:
- EpisodicMemorySystem: Agent autobiographical memory
- NearMissAnalyzer: Learning from near-miss failures
- TemporalIntegrator: Multi-scale exponential integration of experience
- GenerationClock: Hardware-agnostic generation-based time
"""

from engines.memory.episodic_memory import EpisodicMemorySystem
from engines.memory.generation_clock import (
    DECAY_CONFIG,
    GenerationClock,
    GenerationContext,
    KnowledgeDecayConfig,
    compute_access_boost,
    compute_generation_decay,
    compute_relevance_score,
)
from engines.memory.temporal_integrator import (
    TEMPORAL_WINDOWS,
    TemporalIntegrator,
    TemporalWindow,
    get_temporal_integrator,
)


def get_near_miss_analyzer():
    from engines.memory.near_miss_analyzer import NearMissAnalyzer
    return NearMissAnalyzer

__all__ = [
    'EpisodicMemorySystem',
    'get_near_miss_analyzer',
    'TemporalIntegrator',
    'TemporalWindow',
    'TEMPORAL_WINDOWS',
    'get_temporal_integrator',
    # Generation clock exports
    'GenerationClock',
    'GenerationContext',
    'KnowledgeDecayConfig',
    'DECAY_CONFIG',
    'compute_generation_decay',
    'compute_access_boost',
    'compute_relevance_score',
]
