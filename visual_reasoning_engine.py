"""
Visual Reasoning Engine - Extract semantic meaning from ARC grids
==================================================================

Provides visual understanding capabilities for ARC games:
- Symmetry detection (horizontal, vertical, rotational)
- Pattern recognition (repeated motifs)
- Color analysis (distribution, regions)
- Shape detection (objects, boundaries)
- Spatial relationship analysis

Following Rule 2: All analysis results stored in database
Following Rule 3: Clean integration with existing systems
"""

import os
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from collections import Counter, defaultdict
from database_interface import DatabaseInterface

# Rule 1: Disable pycache
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'


class VisualReasoningEngine:
    """
    Extract semantic visual features from ARC game grids
    Enables abstract reasoning about grid patterns and transformations
    """
    
    def __init__(self, database_interface: Optional[DatabaseInterface] = None):
        self.db = database_interface
        self.analysis_cache = {}  # Cache recent analyses
    
    def analyze_grid(self, frame: List[List[int]]) -> Dict[str, Any]:
        """
        Comprehensive visual analysis of grid frame
        
        Args:
            frame: 2D grid of integers representing colors/states
            
        Returns:
            Dictionary with all visual features detected
        """
        if not frame or not frame[0]:
            return self._empty_analysis()
        
        # Convert to numpy for easier manipulation
        grid = np.array(frame)
        height, width = grid.shape
        
        analysis = {
            'grid_size': {'height': height, 'width': width},
            'symmetry': self.detect_symmetry(grid),
            'patterns': self.find_repeating_patterns(grid),
            'colors': self.analyze_color_distribution(grid),
            'shapes': self.detect_shapes(grid),
            'spatial_relations': self.analyze_spatial_relations(grid),
            'transformations': self.infer_likely_transformations(grid),
            'complexity': self.calculate_complexity(grid)
        }
        
        return analysis
    
    def detect_symmetry(self, grid: np.ndarray) -> Dict[str, Any]:
        """
        Detect symmetry in grid
        
        Returns:
            Dictionary with symmetry types and confidence scores
        """
        height, width = grid.shape
        
        symmetries = {
            'horizontal': False,
            'vertical': False,
            'diagonal_main': False,
            'diagonal_anti': False,
            'rotational_180': False,
            'rotational_90': False
        }
        
        confidences = {}
        
        # Horizontal symmetry (mirror across horizontal axis)
        if height > 1:
            top_half = grid[:height//2]
            bottom_half = grid[height//2:][::-1]
            if top_half.shape == bottom_half.shape:
                matches = np.sum(top_half == bottom_half)
                total = top_half.size
                confidences['horizontal'] = matches / total if total > 0 else 0.0
                symmetries['horizontal'] = confidences['horizontal'] > 0.9
        
        # Vertical symmetry (mirror across vertical axis)
        if width > 1:
            left_half = grid[:, :width//2]
            right_half = grid[:, width//2:][:, ::-1]
            if left_half.shape == right_half.shape:
                matches = np.sum(left_half == right_half)
                total = left_half.size
                confidences['vertical'] = matches / total if total > 0 else 0.0
                symmetries['vertical'] = confidences['vertical'] > 0.9
        
        # Diagonal symmetry (main diagonal)
        if height == width:
            transposed = grid.T
            matches = np.sum(grid == transposed)
            total = grid.size
            confidences['diagonal_main'] = matches / total if total > 0 else 0.0
            symmetries['diagonal_main'] = confidences['diagonal_main'] > 0.9
        
        # Rotational 180 degrees
        rotated_180 = np.rot90(grid, 2)
        matches = np.sum(grid == rotated_180)
        total = grid.size
        confidences['rotational_180'] = matches / total if total > 0 else 0.0
        symmetries['rotational_180'] = confidences['rotational_180'] > 0.9
        
        # Rotational 90 degrees (only if square)
        if height == width:
            rotated_90 = np.rot90(grid, 1)
            matches = np.sum(grid == rotated_90)
            total = grid.size
            confidences['rotational_90'] = matches / total if total > 0 else 0.0
            symmetries['rotational_90'] = confidences['rotational_90'] > 0.9
        
        return {
            'detected': symmetries,
            'confidence': confidences,
            'has_any_symmetry': any(symmetries.values())
        }
    
    def find_repeating_patterns(self, grid: np.ndarray) -> List[Dict[str, Any]]:
        """
        Find repeated visual patterns (motifs) in grid
        
        Returns:
            List of patterns with their locations and frequencies
        """
        patterns = []
        height, width = grid.shape
        
        # Check for repeated 2x2, 3x3 blocks
        for pattern_size in [2, 3]:
            if height < pattern_size or width < pattern_size:
                continue
            
            pattern_dict = defaultdict(list)
            
            # Extract all possible pattern_size x pattern_size blocks
            for i in range(height - pattern_size + 1):
                for j in range(width - pattern_size + 1):
                    block = grid[i:i+pattern_size, j:j+pattern_size]
                    block_tuple = tuple(block.flatten())
                    pattern_dict[block_tuple].append((i, j))
            
            # Find patterns that appear more than once
            for pattern_tuple, locations in pattern_dict.items():
                if len(locations) > 1:
                    patterns.append({
                        'size': pattern_size,
                        'pattern': np.array(pattern_tuple).reshape(pattern_size, pattern_size).tolist(),
                        'locations': locations,
                        'frequency': len(locations),
                        'coverage': (len(locations) * pattern_size * pattern_size) / (height * width)
                    })
        
        # Sort by frequency
        patterns.sort(key=lambda p: p['frequency'], reverse=True)
        
        return patterns[:10]  # Return top 10 patterns
    
    def analyze_color_distribution(self, grid: np.ndarray) -> Dict[str, Any]:
        """
        Analyze color/value distribution in grid
        
        Returns:
            Color statistics and distribution info
        """
        flat_grid = grid.flatten()
        color_counts = Counter(flat_grid)
        total_cells = len(flat_grid)
        
        # Calculate statistics
        unique_colors = len(color_counts)
        most_common = color_counts.most_common(3)
        
        # Calculate entropy (measure of color diversity)
        entropy = 0.0
        for count in color_counts.values():
            prob = count / total_cells
            entropy -= prob * np.log2(prob) if prob > 0 else 0
        
        # Identify background color (most common)
        background_color = most_common[0][0] if most_common else 0
        background_percentage = (most_common[0][1] / total_cells) if most_common else 0.0
        
        return {
            'unique_colors': unique_colors,
            'most_common_colors': [{'color': c, 'count': cnt, 'percentage': cnt/total_cells} 
                                   for c, cnt in most_common],
            'background_color': int(background_color),
            'background_percentage': float(background_percentage),
            'entropy': float(entropy),
            'is_sparse': background_percentage > 0.7,  # Mostly background
            'is_diverse': unique_colors > 5,
            'color_counts': dict(color_counts)
        }
    
    def detect_shapes(self, grid: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect distinct shapes/objects in grid using connected components
        
        Returns:
            List of detected shapes with properties
        """
        shapes = []
        height, width = grid.shape
        visited = np.zeros_like(grid, dtype=bool)
        
        def flood_fill(start_i, start_j, color):
            """Find connected component of same color"""
            stack = [(start_i, start_j)]
            cells = []
            
            while stack:
                i, j = stack.pop()
                if i < 0 or i >= height or j < 0 or j >= width:
                    continue
                if visited[i, j] or grid[i, j] != color:
                    continue
                
                visited[i, j] = True
                cells.append((i, j))
                
                # Check 4-connected neighbors
                stack.extend([(i+1, j), (i-1, j), (i, j+1), (i, j-1)])
            
            return cells
        
        # Find all connected components
        for i in range(height):
            for j in range(width):
                if not visited[i, j] and grid[i, j] != 0:  # 0 assumed as background
                    color = grid[i, j]
                    cells = flood_fill(i, j, color)
                    
                    if len(cells) > 1:  # Ignore single-cell "shapes"
                        # Calculate shape properties
                        rows = [c[0] for c in cells]
                        cols = [c[1] for c in cells]
                        
                        min_row, max_row = min(rows), max(rows)
                        min_col, max_col = min(cols), max(cols)
                        
                        bbox_height = max_row - min_row + 1
                        bbox_width = max_col - min_col + 1
                        bbox_area = bbox_height * bbox_width
                        
                        shapes.append({
                            'color': int(color),
                            'size': len(cells),
                            'bounding_box': {
                                'top': int(min_row),
                                'left': int(min_col),
                                'height': int(bbox_height),
                                'width': int(bbox_width)
                            },
                            'center': (
                                int(sum(rows) / len(rows)),
                                int(sum(cols) / len(cols))
                            ),
                            'density': len(cells) / bbox_area if bbox_area > 0 else 0.0,
                            'is_rectangular': len(cells) == bbox_area
                        })
        
        return shapes
    
    def analyze_spatial_relations(self, grid: np.ndarray) -> Dict[str, Any]:
        """
        Analyze spatial relationships between shapes/objects
        
        Returns:
            Spatial relationship information
        """
        shapes = self.detect_shapes(grid)
        
        if len(shapes) < 2:
            return {'num_shapes': len(shapes), 'relations': []}
        
        relations = []
        
        # Analyze pairwise relationships
        for i in range(len(shapes)):
            for j in range(i + 1, len(shapes)):
                shape1 = shapes[i]
                shape2 = shapes[j]
                
                # Calculate relative positions
                c1 = shape1['center']
                c2 = shape2['center']
                
                dx = c2[1] - c1[1]  # Horizontal distance
                dy = c2[0] - c1[0]  # Vertical distance
                
                relation = {
                    'shape1_index': i,
                    'shape2_index': j,
                    'relative_position': self._classify_relative_position(dx, dy),
                    'distance': float(np.sqrt(dx**2 + dy**2)),
                    'aligned_horizontally': abs(dy) < 2,
                    'aligned_vertically': abs(dx) < 2
                }
                
                relations.append(relation)
        
        return {
            'num_shapes': len(shapes),
            'relations': relations,
            'shapes': shapes
        }
    
    def _classify_relative_position(self, dx: int, dy: int) -> str:
        """Classify relative position (above, below, left, right, etc.)"""
        if abs(dx) < 2 and abs(dy) < 2:
            return 'adjacent'
        elif abs(dx) > abs(dy):
            return 'right' if dx > 0 else 'left'
        else:
            return 'below' if dy > 0 else 'above'
    
    def infer_likely_transformations(self, grid: np.ndarray) -> List[Dict[str, Any]]:
        """
        Infer what transformations might be useful for this grid
        Based on visual analysis
        
        Returns:
            List of suggested transformations with confidence scores
        """
        transformations = []
        
        symmetry = self.detect_symmetry(grid)
        colors = self.analyze_color_distribution(grid)
        shapes = self.detect_shapes(grid)
        
        # If symmetric, might need to preserve or exploit symmetry
        if symmetry['has_any_symmetry']:
            for sym_type, detected in symmetry['detected'].items():
                if detected:
                    transformations.append({
                        'type': 'exploit_symmetry',
                        'subtype': sym_type,
                        'confidence': symmetry['confidence'].get(sym_type, 0.0),
                        'reasoning': f'Grid has {sym_type} symmetry'
                    })
        
        # If sparse (mostly background), might need to fill/expand
        if colors['is_sparse']:
            transformations.append({
                'type': 'fill_or_expand',
                'confidence': colors['background_percentage'],
                'reasoning': 'Grid is sparse, may need filling'
            })
        
        # If has repeated patterns, might need pattern completion
        patterns = self.find_repeating_patterns(grid)
        if patterns:
            transformations.append({
                'type': 'pattern_completion',
                'confidence': patterns[0]['coverage'],
                'reasoning': f'Found {len(patterns)} repeating patterns'
            })
        
        # If has multiple distinct shapes, might need spatial transformation
        if len(shapes) > 1:
            transformations.append({
                'type': 'spatial_transformation',
                'confidence': min(len(shapes) / 5, 1.0),
                'reasoning': f'Found {len(shapes)} distinct shapes'
            })
        
        # Sort by confidence
        transformations.sort(key=lambda t: t['confidence'], reverse=True)
        
        return transformations
    
    def calculate_complexity(self, grid: np.ndarray) -> Dict[str, float]:
        """
        Calculate various complexity metrics for grid
        
        Returns:
            Complexity scores
        """
        colors = self.analyze_color_distribution(grid)
        shapes = self.detect_shapes(grid)
        patterns = self.find_repeating_patterns(grid)
        
        # Visual complexity (based on entropy and shape count)
        visual_complexity = (colors['entropy'] / 3.0) + (len(shapes) / 10)
        visual_complexity = min(visual_complexity, 1.0)
        
        # Pattern complexity (more patterns = more complex)
        pattern_complexity = min(len(patterns) / 5, 1.0)
        
        # Spatial complexity (based on shape relationships)
        spatial_complexity = min(len(shapes) * (len(shapes) - 1) / 20, 1.0)
        
        return {
            'visual_complexity': float(visual_complexity),
            'pattern_complexity': float(pattern_complexity),
            'spatial_complexity': float(spatial_complexity),
            'overall_complexity': float((visual_complexity + pattern_complexity + spatial_complexity) / 3)
        }
    
    def _empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis structure"""
        return {
            'grid_size': {'height': 0, 'width': 0},
            'symmetry': {'detected': {}, 'confidence': {}, 'has_any_symmetry': False},
            'patterns': [],
            'colors': {'unique_colors': 0, 'most_common_colors': []},
            'shapes': [],
            'spatial_relations': {'num_shapes': 0, 'relations': []},
            'transformations': [],
            'complexity': {'overall_complexity': 0.0}
        }


# Convenience function for quick analysis
def analyze_arc_frame(frame: List[List[int]]) -> Dict[str, Any]:
    """
    Quick analysis of ARC frame without database
    
    Args:
        frame: 2D grid from ARC game
        
    Returns:
        Analysis dictionary with visual features
    """
    engine = VisualReasoningEngine()
    return engine.analyze_grid(frame)


# [CHECKPOINT: VISUAL REASONING ENGINE IMPLEMENTATION COMPLETE]
# Next: Create Rule Induction Engine to extract transferable rules
