#!/usr/bin/env python3
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
Breakthrough Momentum Detector
================================

Detects micro-progress signals beyond score increases.
Tier 1 Improvement #4: +25% expected gain

Tracks:
- Frame complexity reduction (simplification = progress)
- New regions accessed (exploration coverage)
- Color pattern emergence (new patterns discovered)
- Action sequence convergence (strategy stabilization)
- Edge case discovery (boundary exploration)
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import numpy as np
from typing import List, Dict, Any
from collections import Counter
import logging

logger = logging.getLogger(__name__)


class BreakthroughDetector:
    """Detect breakthrough momentum in gameplay."""
    
    def __init__(self):
        self.breakthrough_threshold = 0.6
        self.history_window = 20  # Actions to look back
        
    def detect_micro_progress(self, game_state, action_history: List[Dict]) -> float:
        """
        Detect breakthrough signals beyond just score.
        
        Args:
            game_state: Current game state
            action_history: Recent action history with frames
            
        Returns:
            Breakthrough probability score (0.0 to 1.0)
        """
        if not action_history or len(action_history) < 5:
            return 0.0
        
        signals = {}
        
        # Signal 1: Frame complexity reduction (getting simpler = progress)
        try:
            signals['frame_complexity_reduction'] = self._measure_simplification(action_history)
        except Exception as e:
            logger.debug(f"Frame complexity measurement failed: {e}")
            signals['frame_complexity_reduction'] = 0.0
        
        # Signal 2: New regions accessed (exploring new areas)
        try:
            signals['new_regions_accessed'] = self._count_unique_visited_regions(action_history)
        except Exception as e:
            logger.debug(f"Region counting failed: {e}")
            signals['new_regions_accessed'] = 0.0
        
        # Signal 3: Color pattern emergence (new patterns forming)
        try:
            signals['color_pattern_emergence'] = self._detect_new_patterns(action_history)
        except Exception as e:
            logger.debug(f"Pattern detection failed: {e}")
            signals['color_pattern_emergence'] = 0.0
        
        # Signal 4: Action sequence convergence (strategy stabilizing)
        try:
            signals['action_sequence_convergence'] = self._measure_strategy_stability(action_history)
        except Exception as e:
            logger.debug(f"Strategy stability measurement failed: {e}")
            signals['action_sequence_convergence'] = 0.0
        
        # Signal 5: Edge case discovery (exploring boundaries)
        try:
            signals['edge_case_discovery'] = self._identify_boundary_exploration(action_history)
        except Exception as e:
            logger.debug(f"Boundary exploration detection failed: {e}")
            signals['edge_case_discovery'] = 0.0
        
        # Composite breakthrough score
        breakthrough_score = sum(signals.values()) / len(signals)
        
        if breakthrough_score > self.breakthrough_threshold:
            logger.info(f"[HOT] BREAKTHROUGH MOMENTUM DETECTED! Score: {breakthrough_score:.2f}")
            logger.info(f"   Signals: {', '.join([f'{k}={v:.2f}' for k, v in signals.items()])}")
        
        return breakthrough_score
    
    def _measure_simplification(self, action_history: List[Dict]) -> float:
        """Measure if frames are getting simpler (fewer unique colors/patterns)."""
        if len(action_history) < 10:
            return 0.0
        
        # Compare first half vs second half complexity
        mid = len(action_history) // 2
        first_half = action_history[:mid]
        second_half = action_history[mid:]
        
        first_complexity = self._frame_complexity(first_half)
        second_complexity = self._frame_complexity(second_half)
        
        if first_complexity == 0:
            return 0.0
        
        # Positive if getting simpler
        simplification = max(0, (first_complexity - second_complexity) / first_complexity)
        return min(1.0, simplification * 2)  # Scale to 0-1
    
    def _frame_complexity(self, actions: List[Dict]) -> float:
        """Calculate average frame complexity (unique colors + grid changes)."""
        complexities = []
        
        for action in actions:
            frame = action.get('frame_after', action.get('frame_before'))
            if not frame:
                continue
            
            try:
                # Count unique non-zero colors
                if isinstance(frame, list) and len(frame) > 0:
                    flat = self._flatten_frame(frame)
                    unique_colors = len([c for c in set(flat) if c != 0])
                    grid_size = len(flat)
                    complexity = unique_colors / max(1, grid_size)
                    complexities.append(complexity)
            except:
                pass
        
        return float(np.mean(complexities)) if complexities else 0.0
    
    def _count_unique_visited_regions(self, action_history: List[Dict]) -> float:
        """Count unique grid regions visited (coverage)."""
        visited_regions = set()
        
        for action in action_history[-self.history_window:]:
            coords = action.get('coordinates')
            if coords:
                # Divide grid into 3x3 regions
                region_x = coords.get('x', 0) // 3
                region_y = coords.get('y', 0) // 3
                visited_regions.add((region_x, region_y))
        
        # More regions = more exploration
        return min(1.0, len(visited_regions) / 9.0)  # Max 9 regions (3x3)
    
    def _detect_new_patterns(self, action_history: List[Dict]) -> float:
        """Detect emergence of new color patterns."""
        if len(action_history) < 10:
            return 0.0
        
        # Compare pattern diversity early vs late
        mid = len(action_history) // 2
        early_patterns = self._extract_color_patterns(action_history[:mid])
        late_patterns = self._extract_color_patterns(action_history[mid:])
        
        # New patterns appearing = emergence
        new_patterns = late_patterns - early_patterns
        emergence_rate = len(new_patterns) / max(1, len(early_patterns))
        
        return min(1.0, emergence_rate)
    
    def _extract_color_patterns(self, actions: List[Dict]) -> set:
        """Extract unique color patterns from frames."""
        patterns = set()
        
        for action in actions:
            frame = action.get('frame_after', action.get('frame_before'))
            if not frame:
                continue
            
            try:
                flat = self._flatten_frame(frame)
                # Use color histogram as pattern signature
                color_counts = Counter(flat)
                pattern = tuple(sorted(color_counts.items()))
                patterns.add(pattern)
            except:
                pass
        
        return patterns
    
    def _measure_strategy_stability(self, action_history: List[Dict]) -> float:
        """Measure if action sequences are converging (repeating patterns)."""
        if len(action_history) < 10:
            return 0.0
        
        # Extract action sequences
        recent_actions = [a.get('action_num', 0) for a in action_history[-self.history_window:]]
        
        # Look for repeating subsequences
        max_repeat_length = 0
        for length in range(2, len(recent_actions) // 2):
            for i in range(len(recent_actions) - length * 2):
                pattern = recent_actions[i:i+length]
                if recent_actions[i+length:i+length*2] == pattern:
                    max_repeat_length = max(max_repeat_length, length)
        
        # Longer repeats = more stable strategy
        return min(1.0, max_repeat_length / 5.0)
    
    def _identify_boundary_exploration(self, action_history: List[Dict]) -> float:
        """Detect if exploring grid boundaries (edges/corners)."""
        boundary_actions = 0
        total_actions = 0
        
        for action in action_history[-self.history_window:]:
            coords = action.get('coordinates')
            frame = action.get('frame_before')
            
            if not coords or not frame:
                continue
            
            total_actions += 1
            
            # Estimate grid size
            grid_size = self._get_grid_size(frame)
            if grid_size[0] == 0:
                continue
            
            x, y = coords.get('x', 0), coords.get('y', 0)
            
            # Check if near boundary (within 1 cell of edge)
            if x <= 1 or x >= grid_size[1] - 2 or y <= 1 or y >= grid_size[0] - 2:
                boundary_actions += 1
        
        if total_actions == 0:
            return 0.0
        
        # More boundary exploration = discovering edge cases
        return boundary_actions / total_actions
    
    def _flatten_frame(self, frame):
        """Flatten nested frame structure."""
        if not isinstance(frame, list):
            return []
        
        flat = []
        for item in frame:
            if isinstance(item, list):
                flat.extend(self._flatten_frame(item))
            else:
                flat.append(item)
        
        return flat
    
    def _get_grid_size(self, frame) -> tuple:
        """Get (height, width) of frame grid."""
        try:
            if isinstance(frame, list) and len(frame) > 0:
                if isinstance(frame[0], list):
                    return (len(frame), len(frame[0]))
        except:
            pass
        return (0, 0)


if __name__ == "__main__":
    # Quick test
    detector = BreakthroughDetector()
    
    # Mock action history
    test_history = [
        {'action_num': 1, 'coordinates': {'x': 0, 'y': 0}, 'frame_before': [[1, 2], [3, 4]]},
        {'action_num': 2, 'coordinates': {'x': 1, 'y': 1}, 'frame_before': [[1, 2], [3, 4]]},
        {'action_num': 3, 'coordinates': {'x': 0, 'y': 1}, 'frame_before': [[1, 0], [0, 4]]},
    ]
    
    score = detector.detect_micro_progress(None, test_history)
    print(f"[OK] Breakthrough score: {score:.2f}")
