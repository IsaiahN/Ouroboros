#!/usr/bin/env python3
"""
Sequence Abstraction - Simple Concept Matching
==============================================

Adds concept-based sequence matching using action patterns.
Key insight: Action patterns ARE the concepts!
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import json
from typing import Dict, List, Optional
from database_interface import DatabaseInterface
import logging

logger = logging.getLogger(__name__)


class SequenceAbstraction:
    """Simple concept matching for sequences."""
    
    # 3x3 region grid for 64x64 coordinate space
    GRID_SIZE = 64
    REGION_NAMES = {
        (0, 0): 'NW', (1, 0): 'N', (2, 0): 'NE',
        (0, 1): 'W',  (1, 1): 'C', (2, 1): 'E',
        (0, 2): 'SW', (1, 2): 'S', (2, 2): 'SE'
    }
    
    def __init__(self, db_path: str = "core_data.db"):
        """Initialize abstraction engine."""
        self.db = DatabaseInterface(db_path)
    
    def _coords_to_region(self, x: int, y: int) -> str:
        """Convert (x, y) coordinates to region name (NW, N, NE, W, C, E, SW, S, SE)."""
        # Divide 64x64 grid into 3x3 regions (~21x21 each)
        col = min(x // (self.GRID_SIZE // 3), 2)  # 0, 1, or 2
        row = min(y // (self.GRID_SIZE // 3), 2)  # 0, 1, or 2
        return self.REGION_NAMES.get((col, row), 'C')  # Default to center
    
    def get_sequence_by_concept(
        self,
        game_id: str,
        level_number: int,
        current_actions: List[int] = None,
        pattern_similarity: float = 0.7
    ) -> Optional[Dict]:
        """
        Match sequences by ACTION PATTERN (concept), not frames.
        
        Action patterns like [1,3,1,3] = "zigzag right-left" work
        across ANY game state!
        """
        candidates = self._get_candidates(game_id, level_number)
        
        if not candidates or not current_actions:
            return candidates[0] if candidates else None
        
        # Score by pattern similarity
        scored = []
        for seq in candidates:
            try:
                seq_actions = json.loads(seq['action_sequence']) if isinstance(seq['action_sequence'], str) else seq['action_sequence']
                seq_pattern = self._extract_pattern(seq_actions)
                
                similarity = self._pattern_similarity(current_actions, seq_pattern)
                
                if similarity >= pattern_similarity:
                    scored.append((seq, similarity))
            except Exception as e:
                logger.debug(f"Error scoring: {e}")
                continue
        
        if scored:
            best_seq, score = max(scored, key=lambda x: x[1])
            logger.info(f"✓ Concept match: {best_seq['sequence_id'][:12]} ({score:.1%} similar)")
            return best_seq
        
        return candidates[0] if candidates else None
    
    def _extract_pattern(self, actions: List) -> List[int]:
        """Extract action type pattern."""
        pattern = []
        for action in actions:
            if isinstance(action, dict):
                action_type = action.get('action', 0)
                if isinstance(action_type, str) and action_type.startswith('ACTION'):
                    action_type = int(action_type.replace('ACTION', ''))
                pattern.append(action_type)
            elif isinstance(action, int):
                pattern.append(action)
        return pattern
    
    def _pattern_similarity(self, p1: List[int], p2: List[int]) -> float:
        """Calculate pattern similarity using LCS."""
        if not p1 or not p2:
            return 0.0
        
        if p1 == p2:
            return 1.0
        
        # Length + overlap similarity
        len_ratio = min(len(p1), len(p2)) / max(len(p1), len(p2))
        lcs_len = self._lcs(p1, p2)
        overlap_ratio = lcs_len / max(len(p1), len(p2))
        
        return (len_ratio * 0.3) + (overlap_ratio * 0.7)
    
    def _lcs(self, s1: List, s2: List) -> int:
        """Longest common subsequence length."""
        if not s1 or not s2:
            return 0
        
        m, n = len(s1), len(s2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i-1] == s2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        return dp[m][n]
    
    def _get_candidates(self, game_id: str, level_number: int, max_results: int = 50) -> List[Dict]:
        """Get candidate sequences."""
        try:
            game_type = game_id.split('-')[0] if '-' in game_id else game_id
            
            sequences = self.db.execute_query("""
                SELECT ws.*, COALESCE(sr.success_rate, 0.5) as success_rate
                FROM winning_sequences ws
                LEFT JOIN sequence_reputation sr ON ws.sequence_id = sr.sequence_id
                WHERE ws.game_id LIKE ? AND ws.level_number = ?
                ORDER BY sr.success_rate DESC, ws.total_actions ASC
                LIMIT ?
            """, (f"{game_type}%", level_number, max_results))
            
            return sequences or []
        except Exception as e:
            logger.error(f"Error fetching candidates: {e}")
            return []
    
    def extract_multi_sequence_concept(
        self,
        game_id: str,
        level_number: int,
        min_sequences: int = 3
    ) -> Optional[Dict]:
        """
        Extract common concept from MULTIPLE sequences (same game/level).
        
        Returns what MUST happen (invariants) vs what CAN vary (variants).
        THIS IS TRUE ABSTRACTION!
        """
        try:
            game_type = game_id.split('-')[0] if '-' in game_id else game_id
            
            sequences = self.db.execute_query("""
                SELECT action_sequence, coordinate_sequence, game_id, level_number
                FROM winning_sequences
                WHERE game_id LIKE ? AND level_number = ?
                ORDER BY total_score DESC
                LIMIT 20
            """, (f"{game_type}%", level_number))
            
            if not sequences or len(sequences) < min_sequences:
                return None
            
            # Extract all patterns
            patterns = []
            for seq in sequences:
                try:
                    actions = json.loads(seq['action_sequence']) if isinstance(seq['action_sequence'], str) else seq['action_sequence']
                    pattern = self._extract_pattern(actions)
                    if pattern:
                        patterns.append(pattern)
                except:
                    continue
            
            if len(patterns) < min_sequences:
                return None
            
            # Find invariants and variants
            min_len = min(len(p) for p in patterns)
            
            # Find positions where ALL patterns have same action
            invariant_positions = []
            for pos in range(min_len):
                actions_at_pos = [p[pos] for p in patterns]
                if len(set(actions_at_pos)) == 1:  # All same
                    action_type = actions_at_pos[0]
                    
                    # Get coordinates for this position across all sequences
                    coords = []
                    for seq in sequences[:len(patterns)]:
                        try:
                            # Coordinates are in separate 'coordinate_sequence' column
                            if seq.get('coordinate_sequence'):
                                coord_seq = json.loads(seq['coordinate_sequence']) if isinstance(seq['coordinate_sequence'], str) else seq['coordinate_sequence']
                                if pos < len(coord_seq) and coord_seq[pos]:
                                    # coord_seq[pos] is [x, y]
                                    coords.append(tuple(coord_seq[pos]))
                        except Exception as e:
                            logger.debug(f"Error parsing coordinates: {e}")
                            continue
                    
                    # Calculate coordinate approximation
                    coord_info = None
                    if coords:
                        x_coords = [c[0] for c in coords]
                        y_coords = [c[1] for c in coords]
                        
                        # Convert to regions
                        regions = [self._coords_to_region(c[0], c[1]) for c in coords]
                        unique_regions = sorted(set(regions))
                        
                        # Check if coordinates are consistent
                        x_variance = max(x_coords) - min(x_coords) if x_coords else 0
                        y_variance = max(y_coords) - min(y_coords) if y_coords else 0
                        
                        coord_info = {
                            'regions': unique_regions,
                            'region_count': len(unique_regions),
                            'x_range': (min(x_coords), max(x_coords)),
                            'y_range': (min(y_coords), max(y_coords)),
                            'x_mean': sum(x_coords) / len(x_coords),
                            'y_mean': sum(y_coords) / len(y_coords),
                            'is_fixed': (x_variance <= 1 and y_variance <= 1),  # Within 1 cell = fixed
                            'is_regional': len(unique_regions) <= 2  # 1-2 regions = regional pattern
                        }
                    
                    invariant_positions.append({
                        'position': pos,
                        'action': action_type,
                        'coordinates': coord_info
                    })
            
            # Find variable regions
            variable_regions = []
            current_region = None
            
            for pos in range(min_len):
                actions_at_pos = [p[pos] for p in patterns]
                is_variable = len(set(actions_at_pos)) > 1
                
                if is_variable:
                    if current_region is None:
                        current_region = {'start': pos, ' variations': set(actions_at_pos)}
                    else:
                        current_region['variations'].update(actions_at_pos)
                else:
                    if current_region:
                        current_region['end'] = pos - 1
                        variable_regions.append(current_region)
                        current_region = None
            
            if current_region:
                current_region['end'] = min_len - 1
                variable_regions.append(current_region)
            
            # Build template
            template = []
            action_names = {1: "right", 2: "down", 3: "left", 4: "up", 5: "select", 6: "submit", 7: "reset"}
            
            for pos in range(min_len):
                if any(inv['position'] == pos for inv in invariant_positions):
                    action = next(inv['action'] for inv in invariant_positions if inv['position'] == pos)
                    template.append(f"ACTION{action}")
                else:
                    template.append("VARIABLE")
            
            # Description
            if len(invariant_positions) >= 3:
                desc = f"Fixed {len(invariant_positions)} checkpoints"
            elif len(invariant_positions) > 0:
                desc = f"{len(invariant_positions)} required actions"
            else:
                desc = "Flexible strategy"
            
            return {
                'description': desc,
                'invariant_positions': invariant_positions,
                'variable_regions': [
                    {
                        'start': r['start'],
                        'end': r['end'],
                        'options': list(r['variations'])
                    } for r in variable_regions
                ],
                'template': template,
                'sample_size': len(patterns),
                'confidence': min(len(patterns) / 10.0, 1.0),
                'game_type': game_type,
                'level': level_number
            }
        
        except Exception as e:
            logger.error(f"Error extracting concept: {e}")
            return None


# Abstraction levels
ABSTRACTION_LEVELS = {
    'exact': 1.0,
    'tight': 0.95,
    'moderate': 0.85,
    'loose': 0.75
}


if __name__ == "__main__":
    print("=" * 70)
    print("SEQUENCE ABSTRACTION - CONCEPT MATCHING ")
    print("=" * 70)
    
    abstraction = SequenceAbstraction()
    
    # Test pattern similarity
    print("\n[TEST] Test: Action Pattern Similarity")
    p1 = [1, 3, 1, 3, 1, 3]
    p2 = [1, 3, 1, 3, 1, 3]
    p3 = [1, 3, 1, 3]
    p4 = [2, 4, 2, 4]
    
    print(f"  Identical: {abstraction._pattern_similarity(p1, p2):.2%}")
    print(f"  Similar: {abstraction._pattern_similarity(p1, p3):.2%}")
    print(f"  Different: {abstraction._pattern_similarity(p1, p4):.2%}")
    
    # Test multi-sequence concept extraction
    print("\n[TEST] Test: Multi-Sequence Concept Extraction")
    concept = abstraction.extract_multi_sequence_concept("vc33", level_number=1, min_sequences=3)
    
    if concept:
        print(f"  [STATS] Concept: {concept['description']}")
        print(f"  Sample: {concept['sample_size']} sequences")
        print(f"  Confidence: {concept['confidence']:.0%}")
        
        if concept['invariant_positions']:
            action_names = {1: "right", 2: "down", 3: "left", 4: "up", 5: "select", 6: "submit", 7: "reset"}
            print(f"\n  [LOCK] INVARIANTS (MUST do):")
            for inv in concept['invariant_positions'][:5]:
                coord_str = ""
                if inv.get('coordinates'):
                    c = inv['coordinates']
                    if c['is_fixed']:
                        # Fixed position (within 1 cell)
                        region = self._coords_to_region(int(c['x_mean']), int(c['y_mean']))
                        coord_str = f" at ({c['x_mean']:.0f},{c['y_mean']:.0f}) [{region}]"
                    elif c['is_regional']:
                        # 1-2 regions (regional pattern)
                        coord_str = f" in {'+'.join(c['regions'])}"
                    else:
                        # Multiple regions (wide spread)
                        coord_str = f" in {len(c['regions'])} regions ({', '.join(c['regions'][:4])}{'...' if len(c['regions']) > 4 else ''})"
                print(f"     Pos {inv['position']}: ACTION{inv['action']} ({action_names.get(inv['action'], '?')}){coord_str}")
        
        if concept['variable_regions']:
            print(f"\n  [SYNC] VARIANTS (CAN adapt):")
            for region in concept['variable_regions'][:3]:
                print(f"     Pos {region['start']}-{region['end']}: {len(region['options'])} options")
        
        print(f"\n  [NOTE] Template: {' → '.join(concept['template'][:10])}")
    else:
        print("  Need more sequences")
    
    print("\n[OK] Multi-sequence concept extraction ready!")
    print("\n[IDEA] BREAKTHROUGH: Comparing sequences reveals TRUE concepts!")
    print("   Invariants = what MUST happen")
    print("   Variants = what CAN adapt")
