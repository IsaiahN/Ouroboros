import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
Execution Trace Miner - Primitive Sequence Pattern Discovery
=============================================================

Extracted from cods_engine.py - discovers frequent primitive composition 
patterns by mining agent execution logs.

Similar to market basket analysis - finds patterns like:
"When agents succeed, they often do: detect_object -> get_position -> calculate_distance"

This is the MISSING LINK in the composition system - it generates composition
suggestions based on what actually works in practice.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


class ExecutionTraceMiner:
    """
    Mines agent execution logs to find frequent primitive sequences.
    
    Similar to market basket analysis - finds patterns like:
    "When agents succeed, they often do: detect_object -> get_position -> calculate_distance"
    
    This is the MISSING LINK in the composition system - it generates composition
    suggestions based on what actually works in practice.
    
    OPTIMIZED VERSION (Dec 2025):
    - Pre-aggregates sequences into counts (no raw log storage)
    - Rolling buffer for recent calls only
    - O(unique_sequences) lookups instead of O(total_calls)
    """
    
    def __init__(
        self, 
        db: Optional[DatabaseInterface] = None, 
        min_frequency: int = 5
    ):
        self.db = db
        self.min_frequency = min_frequency
        
        # Rolling buffer of recent calls (limited to 1000)
        self.execution_log: List[Dict[str, Any]] = []
        self._max_buffer_size = 1000
        
        # Aggregated sequence counts: {tuple_of_primitives: {count, successes, last_seen}}
        self.sequence_counts: Dict[Tuple[str, ...], Dict[str, Any]] = {}
        
        # Track which patterns have been composed
        self._composed_patterns: Set[Tuple[str, ...]] = set()
        
    def record_primitive_call(
        self,
        primitive_name: str,
        success: bool,
        execution_time_ms: float = 0.0,
        game_context: Optional[Dict] = None
    ):
        """
        Record a primitive call.
        
        Args:
            primitive_name: Name of primitive called
            success: Whether call succeeded
            execution_time_ms: How long it took
            game_context: Optional context (game_id, level, agent_id)
        """
        # Add to rolling buffer
        entry = {
            'primitive': primitive_name,
            'success': success,
            'time_ms': execution_time_ms,
            'timestamp': time.time(),
            'context': game_context
        }
        self.execution_log.append(entry)
        
        # Trim buffer if needed
        if len(self.execution_log) > self._max_buffer_size:
            self.execution_log = self.execution_log[-self._max_buffer_size:]
        
        # Aggregate into sequences (2 and 3-grams)
        self._aggregate_recent_sequences(is_success=success)
    
    def _aggregate_recent_sequences(self, is_success: bool):
        """Extract and count sequences from recent buffer."""
        if len(self.execution_log) < 2:
            return
        
        # Get last 5 primitives
        recent = [e['primitive'] for e in self.execution_log[-5:]]
        
        # Count 2-grams and 3-grams
        for window in [2, 3]:
            if len(recent) >= window:
                seq = tuple(recent[-window:])
                
                if seq not in self.sequence_counts:
                    self.sequence_counts[seq] = {
                        'count': 0,
                        'successes': 0,
                        'last_seen': 0,
                        'first_seen': time.time()
                    }
                
                self.sequence_counts[seq]['count'] += 1
                if is_success:
                    self.sequence_counts[seq]['successes'] += 1
                self.sequence_counts[seq]['last_seen'] = time.time()
        
    def mine_sequences(
        self, 
        window_size: int = 3,
        min_frequency: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Return frequent primitive sequences from AGGREGATED counts.
        
        No more sliding window over raw logs - just query the pre-aggregated data.
        Much faster: O(unique_sequences) instead of O(total_calls).
        
        Args:
            window_size: Filter to sequences of this length (2-5 typical)
            min_frequency: Minimum times pattern must appear
            
        Returns:
            List of {sequence: ['prim1', 'prim2'], count: 10, success_rate: 0.8}
        """
        min_freq = min_frequency or self.min_frequency
        results = []
        
        for seq, stats in self.sequence_counts.items():
            # Filter by sequence length if specified
            if window_size and len(seq) != window_size:
                continue
                
            if stats['count'] >= min_freq:
                success_rate = stats['successes'] / stats['count'] if stats['count'] > 0 else 0
                # Only keep patterns that correlate with success (60%+)
                if success_rate >= 0.6:
                    results.append({
                        'sequence': list(seq),
                        'count': stats['count'],
                        'success_rate': success_rate,
                        'confidence': self._calculate_confidence(stats['count']),
                        'first_seen': stats.get('first_seen'),
                        'last_seen': stats.get('last_seen'),
                    })
        
        # Sort by combination of frequency and success rate
        results.sort(key=lambda x: x['count'] * x['success_rate'], reverse=True)
        return results
    
    def _calculate_confidence(self, count: int) -> float:
        """Wilson score confidence interval approximation."""
        if count == 0:
            return 0.0
        # More observations = higher confidence (full confidence at 20+)
        return min(1.0, count / 20.0)
    
    def mine_success_patterns(self) -> List[Dict[str, Any]]:
        """
        Return patterns that correlate with success from AGGREGATED data.
        
        No more re-scanning raw logs - just filter sequence_counts by success_rate.
        """
        results = []
        
        for seq, stats in self.sequence_counts.items():
            if stats['count'] >= 3:  # Need at least 3 observations
                success_rate = stats['successes'] / stats['count'] if stats['count'] > 0 else 0
                if success_rate >= 0.5:  # 50%+ success correlation
                    results.append({
                        'sequence': list(seq),
                        'success_episodes': stats['successes'],
                        'total_episodes': stats['count'],
                        'correlation': success_rate
                    })
        
        # Sort by correlation strength
        results.sort(key=lambda x: x['correlation'], reverse=True)
        return results[:20]  # Top 20
    
    def mark_composed(self, sequence: List[str]):
        """Mark a sequence as having been composed into an operator."""
        self._composed_patterns.add(tuple(sequence))
    
    def is_composed(self, sequence: List[str]) -> bool:
        """Check if sequence has already been composed."""
        return tuple(sequence) in self._composed_patterns
    
    def get_uncomposed_patterns(
        self, 
        min_frequency: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get patterns that haven't been composed yet."""
        all_patterns = self.mine_sequences(
            window_size=0,  # All sizes
            min_frequency=min_frequency
        )
        return [
            p for p in all_patterns 
            if tuple(p['sequence']) not in self._composed_patterns
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current mining statistics."""
        total_observations = sum(s['count'] for s in self.sequence_counts.values())
        return {
            'unique_sequences': len(self.sequence_counts),
            'total_observations': total_observations,
            'buffer_size': len(self.execution_log),
            'composed_patterns': len(self._composed_patterns),
        }
    
    def clear_log(self):
        """Clear the rolling buffer (aggregated counts are preserved)."""
        self.execution_log = []
    
    def clear_all(self):
        """Clear everything including aggregated counts."""
        self.execution_log = []
        self.sequence_counts = {}


__all__ = ['ExecutionTraceMiner']
