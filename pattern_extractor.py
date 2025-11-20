#!/usr/bin/env python3
"""
Pattern Extractor - Phase 3
============================

Extracts movement patterns and strategies from sequences.
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import json
import uuid
from typing import Dict, List, Optional
from datetime import datetime
from database_interface import DatabaseInterface
from abstraction_config import is_abstraction_enabled, MIN_PATTERN_FREQUENCY
import logging

logger = logging.getLogger(__name__)


class PatternExtractor:
    """Extracts reusable patterns from action sequences."""
    
    def __init__(self, db_path: str = "core_data.db"):
        self.db = DatabaseInterface(db_path)
        self.enabled = is_abstraction_enabled()
    
    def extract_movement_pattern(
        self,
        positions: List[tuple],
        actions: List[str]
    ) -> Optional[Dict]:
        """Extract movement pattern from position sequence."""
        if not self.enabled or len(positions) < 2:
            return None
        
        # Determine pattern type
        pattern_type = self._classify_movement(positions)
        
        # Create template
        template = self._create_template(positions, actions, pattern_type)
        
        pattern_id = f"pattern_{uuid.uuid4().hex[:12]}"
        
        return {
            'pattern_id': pattern_id,
            'pattern_type': pattern_type,
            'template': json.dumps(template),
            'example_sequences': json.dumps([]),
            'frequency': 1,
            'success_rate': 1.0,
            'created_at': datetime.now().isoformat()
        }
    
    def _classify_movement(self, positions: List[tuple]) -> str:
        """Classify type of movement pattern."""
        if len(positions) < 2:
            return 'static'
        
        # Calculate movement vectors
        vectors = []
        for i in range(len(positions) - 1):
            dx = positions[i+1][0] - positions[i][0]
            dy = positions[i+1][1] - positions[i][1]
            vectors.append((dx, dy))
        
        # Check for linear movement
        if all(v == vectors[0] for v in vectors):
            return 'linear'
        
        # Check for zigzag (alternating directions)
        if len(vectors) > 2:
            alternates = all(
                vectors[i][0] * vectors[i+1][0] <= 0 or
                vectors[i][1] * vectors[i+1][1] <= 0
                for i in range(len(vectors) - 1)
            )
            if alternates:
                return 'zigzag'
        
        # Check for spiral (increasing distance from center)
        # Simplified: check if generally moving outward
        distances = [abs(p[0]) + abs(p[1]) for p in positions]
        if all(distances[i] <= distances[i+1] for i in range(len(distances)-1)):
            return 'spiral'
        
        return 'complex'
    
    def _create_template(
        self,
        positions: List[tuple],
        actions: List[str],
        pattern_type: str
    ) -> Dict:
        """Create abstract template from concrete positions."""
        return {
            'type': pattern_type,
            'length': len(positions),
            'actions': actions,
            'relative_positions': self._to_relative(positions)
        }
    
    def _to_relative(self, positions: List[tuple]) -> List[tuple]:
        """Convert absolute positions to relative movements."""
        if not positions:
            return []
        
        relative = [(0, 0)]  # Start at origin
        for i in range(len(positions) - 1):
            dx = positions[i+1][0] - positions[i][0]
            dy = positions[i+1][1] - positions[i][1]
            relative.append((dx, dy))
        
        return relative
    
    def extract_strategy(
        self,
        sequence: Dict,
        success: bool
    ) -> Optional[str]:
        """Extract high-level strategy from sequence."""
        if not self.enabled:
            return None
        
        actions = sequence.get('actions', [])
        if not actions:
            return 'exploration'
        
        # Simple strategy classification
        action_types = [a.get('action', '') for a in actions]
        
        # Repetitive actions = methodical
        unique_ratio = len(set(action_types)) / len(action_types)
        if unique_ratio < 0.3:
            return 'methodical'
        
        # Many different actions = exploratory
        if unique_ratio > 0.7:
            return 'exploratory'
        
        # Mix = adaptive
        return 'adaptive'
    
    def update_pattern_frequency(
        self,
        pattern_id: str,
        success: bool
    ):
        """Update pattern frequency and success rate."""
        if not self.enabled:
            return
        
        try:
            # Get current stats
            result = self.db.execute_query("""
                SELECT frequency, success_rate
                FROM movement_patterns
                WHERE pattern_id = ?
            """, (pattern_id,))
            
            if result:
                freq = result[0]['frequency']
                old_rate = result[0]['success_rate']
                
                new_freq = freq + 1
                new_rate = (old_rate * freq + (1.0 if success else 0.0)) / new_freq
                
                self.db.execute_query("""
                    UPDATE movement_patterns
                    SET frequency = ?, success_rate = ?
                    WHERE pattern_id = ?
                """, (new_freq, new_rate, pattern_id))
        except Exception as e:
            logger.error(f"Failed to update pattern: {e}")
    
    def store_pattern(self, pattern: Dict):
        """Store movement pattern in database."""
        if not self.enabled or not pattern:
            return
        
        try:
            self.db.execute_query("""
                INSERT OR REPLACE INTO movement_patterns
                (pattern_id, pattern_type, template, example_sequences, 
                 frequency, success_rate, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                pattern['pattern_id'], pattern['pattern_type'], pattern['template'],
                pattern['example_sequences'], pattern['frequency'],
                pattern['success_rate'], pattern['created_at']
            ))
        except Exception as e:
            logger.error(f"Failed to store pattern: {e}")
    
    def get_frequent_patterns(self, min_frequency: int = MIN_PATTERN_FREQUENCY) -> List[Dict]:
        """Get patterns that occur frequently."""
        if not self.enabled:
            return []
        
        return self.db.execute_query("""
            SELECT *
            FROM movement_patterns
            WHERE frequency >= ?
            ORDER BY success_rate DESC, frequency DESC
            LIMIT 20
        """, (min_frequency,)) or []
