"""
Memory Engines Package

Provides memory systems for agent experience tracking, recall, and learning from failures.
"""

from engines.memory.episodic_memory import EpisodicMemorySystem


def get_near_miss_analyzer():
    from engines.memory.near_miss_analyzer import NearMissAnalyzer
    return NearMissAnalyzer

__all__ = [
    'EpisodicMemorySystem',
    'get_near_miss_analyzer',
]
