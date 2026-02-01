#!/usr/bin/env python3
"""
Primitive Suggester - Direct primitive-to-action mapping
=========================================================

Simplified replacement for CODS engine complexity.
Does three things well:

1. Applies seed primitives to frames
2. Maps primitive outputs to action suggestions
3. Tracks which primitive→action mappings work (RLVR feedback)

No unlock ceremonies, no oracle, no composition discovery.
Just primitives → actions → learn what works.

Rule 1: Disable pycache
Rule 2: All data in database
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

from database_interface import DatabaseInterface
from seed_primitives import get_seed_primitives, SeedPrimitiveRegistry

logger = logging.getLogger(__name__)


@dataclass
class ActionCandidate:
    """A suggested action with reasoning."""
    action: int
    confidence: float
    primitive: str
    reasoning: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'action': self.action,
            'confidence': self.confidence,
            'primitive': self.primitive,
            'reasoning': self.reasoning
        }


@dataclass
class SuggestionResult:
    """Result of suggest_action()."""
    action: int
    confidence: float
    primitive: str
    reasoning: str
    candidates: List[ActionCandidate] = field(default_factory=list)
    primitives_applied: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'action': self.action,
            'confidence': self.confidence,
            'primitive': self.primitive,
            'reasoning': self.reasoning,
            'candidates': [c.to_dict() for c in self.candidates],
            'primitives_applied': self.primitives_applied
        }


class PrimitiveSuggester:
    """
    Direct primitive → action mapping.
    
    Replaces ~8,000 lines of CODS with ~400 lines that do the actual work:
    1. Run primitives on frame
    2. Map outputs to actions
    3. Track what works
    
    Usage:
        suggester = PrimitiveSuggester(db)
        result = suggester.suggest_action(frame, game_type)
        # After action outcome known:
        suggester.record_outcome(game_type, primitive, action, success)
    """
    
    def __init__(self, db: Optional[DatabaseInterface] = None, db_path: str = "core_data.db"):
        self.db = db or DatabaseInterface(db_path)
        self.seeds = get_seed_primitives()
        self._ensure_tables()
        
        # Cache for primitive effectiveness by game type
        self._effectiveness_cache: Dict[str, Dict[str, float]] = {}
    
    def _ensure_tables(self):
        """Create simple tracking tables."""
        try:
            # Track primitive→action effectiveness
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS primitive_action_effectiveness (
                    game_type TEXT NOT NULL,
                    primitive_name TEXT NOT NULL,
                    action INT NOT NULL,
                    successes INT DEFAULT 0,
                    failures INT DEFAULT 0,
                    last_used DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (game_type, primitive_name, action)
                )
            """)
            
            # Track which primitives are useful per game type
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS primitive_game_relevance (
                    game_type TEXT NOT NULL,
                    primitive_name TEXT NOT NULL,
                    times_suggested INT DEFAULT 0,
                    times_helped INT DEFAULT 0,
                    relevance_score REAL DEFAULT 0.5,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (game_type, primitive_name)
                )
            """)
        except Exception as e:
            logger.debug(f"Table creation (may exist): {e}")
    
    def suggest_action(
        self,
        frame: List[List[int]],
        game_type: Optional[str] = None,
        recent_actions: Optional[List[int]] = None
    ) -> SuggestionResult:
        """
        Suggest an action based on primitive analysis of the frame.
        
        Args:
            frame: Current game frame (2D list of pixel values)
            game_type: Game type for learning which primitives help
            recent_actions: Recent actions to avoid repetition
            
        Returns:
            SuggestionResult with best action and all candidates
        """
        if not frame or not frame[0]:
            return self._random_result()
        
        recent_actions = recent_actions or []
        candidates: List[ActionCandidate] = []
        primitives_applied: List[str] = []
        
        # Get primitive relevance for this game type
        relevance = self._get_primitive_relevance(game_type) if game_type else {}
        
        # 1. Symmetry detection → movement along axis
        try:
            symmetry = self._detect_symmetry(frame)
            primitives_applied.append('detect_symmetry')
            
            if symmetry.get('vertical'):
                boost = relevance.get('detect_symmetry', 0.5)
                candidates.append(ActionCandidate(
                    action=1, confidence=0.35 * boost,
                    primitive='detect_symmetry',
                    reasoning='Vertical symmetry - try up'
                ))
                candidates.append(ActionCandidate(
                    action=2, confidence=0.30 * boost,
                    primitive='detect_symmetry',
                    reasoning='Vertical symmetry - try down'
                ))
            
            if symmetry.get('horizontal'):
                boost = relevance.get('detect_symmetry', 0.5)
                candidates.append(ActionCandidate(
                    action=3, confidence=0.35 * boost,
                    primitive='detect_symmetry',
                    reasoning='Horizontal symmetry - try right'
                ))
                candidates.append(ActionCandidate(
                    action=4, confidence=0.30 * boost,
                    primitive='detect_symmetry',
                    reasoning='Horizontal symmetry - try left'
                ))
        except Exception:
            pass
        
        # 2. Motion detection → continue or counter motion
        try:
            motion = self._detect_motion(frame)
            primitives_applied.append('detect_motion')
            
            if motion.get('direction'):
                boost = relevance.get('detect_motion', 0.5)
                dir_map = {'up': 1, 'down': 2, 'right': 3, 'left': 4}
                action = dir_map.get(motion['direction'])
                if action:
                    candidates.append(ActionCandidate(
                        action=action, confidence=0.4 * boost,
                        primitive='detect_motion',
                        reasoning=f"Motion detected {motion['direction']}"
                    ))
        except Exception:
            pass
        
        # 3. Color clustering → move toward distinct regions
        try:
            clusters = self._find_color_clusters(frame)
            primitives_applied.append('find_color_clusters')
            
            if clusters:
                boost = relevance.get('find_color_clusters', 0.5)
                # Move toward largest non-background cluster
                for cluster in clusters[:2]:
                    cx, cy = cluster.get('center', (0, 0))
                    action = self._direction_to_point(frame, cx, cy)
                    if action:
                        candidates.append(ActionCandidate(
                            action=action, confidence=0.3 * boost,
                            primitive='find_color_clusters',
                            reasoning=f"Color cluster at ({cx}, {cy})"
                        ))
        except Exception:
            pass
        
        # 4. Edge detection → explore boundaries
        try:
            edges = self._detect_edges(frame)
            primitives_applied.append('detect_edges')
            
            if edges.get('strongest_direction'):
                boost = relevance.get('detect_edges', 0.5)
                dir_map = {'up': 1, 'down': 2, 'right': 3, 'left': 4}
                action = dir_map.get(edges['strongest_direction'])
                if action:
                    candidates.append(ActionCandidate(
                        action=action, confidence=0.25 * boost,
                        primitive='detect_edges',
                        reasoning=f"Strong edge {edges['strongest_direction']}"
                    ))
        except Exception:
            pass
        
        # 5. Novelty detection → explore unseen areas
        try:
            novelty = self._detect_novelty(frame)
            primitives_applied.append('detect_novelty')
            
            if novelty.get('novel_region'):
                boost = relevance.get('detect_novelty', 0.5)
                nx, ny = novelty['novel_region']
                action = self._direction_to_point(frame, nx, ny)
                if action:
                    candidates.append(ActionCandidate(
                        action=action, confidence=0.35 * boost,
                        primitive='detect_novelty',
                        reasoning=f"Novel region at ({nx}, {ny})"
                    ))
        except Exception:
            pass
        
        # 6. Goal detection (bright/distinct objects)
        try:
            goal = self._detect_goal(frame)
            primitives_applied.append('detect_goal')
            
            if goal.get('position'):
                boost = relevance.get('detect_goal', 0.6)
                gx, gy = goal['position']
                action = self._direction_to_point(frame, gx, gy)
                if action:
                    candidates.append(ActionCandidate(
                        action=action, confidence=0.5 * boost,
                        primitive='detect_goal',
                        reasoning=f"Potential goal at ({gx}, {gy})"
                    ))
        except Exception:
            pass
        
        # Penalize recently used actions
        for candidate in candidates:
            if candidate.action in recent_actions[-3:]:
                candidate.confidence *= 0.5
        
        # Sort by confidence and pick best
        candidates.sort(key=lambda c: c.confidence, reverse=True)
        
        if candidates:
            best = candidates[0]
            return SuggestionResult(
                action=best.action,
                confidence=best.confidence,
                primitive=best.primitive,
                reasoning=best.reasoning,
                candidates=candidates[:5],
                primitives_applied=primitives_applied
            )
        
        return self._random_result(primitives_applied)
    
    def record_outcome(
        self,
        game_type: str,
        primitive: str,
        action: int,
        success: bool
    ):
        """
        Record whether a primitive→action mapping worked.
        
        Call this after taking the suggested action and seeing the result.
        This is the RLVR feedback loop - learn what works.
        """
        try:
            # Update effectiveness
            if success:
                self.db.execute_query("""
                    INSERT INTO primitive_action_effectiveness 
                    (game_type, primitive_name, action, successes, last_used)
                    VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(game_type, primitive_name, action) DO UPDATE SET
                    successes = successes + 1, last_used = CURRENT_TIMESTAMP
                """, (game_type, primitive, action))
            else:
                self.db.execute_query("""
                    INSERT INTO primitive_action_effectiveness 
                    (game_type, primitive_name, action, failures, last_used)
                    VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(game_type, primitive_name, action) DO UPDATE SET
                    failures = failures + 1, last_used = CURRENT_TIMESTAMP
                """, (game_type, primitive, action))
            
            # Update relevance
            self.db.execute_query("""
                INSERT INTO primitive_game_relevance 
                (game_type, primitive_name, times_suggested, times_helped, last_updated)
                VALUES (?, ?, 1, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(game_type, primitive_name) DO UPDATE SET
                times_suggested = times_suggested + 1,
                times_helped = times_helped + ?,
                relevance_score = CAST(times_helped + ? AS REAL) / MAX(times_suggested + 1, 1),
                last_updated = CURRENT_TIMESTAMP
            """, (game_type, primitive, 1 if success else 0, 1 if success else 0, 1 if success else 0))
            
            # Invalidate cache
            self._effectiveness_cache.pop(game_type, None)
            
        except Exception as e:
            logger.debug(f"Record outcome failed: {e}")
    
    def _get_primitive_relevance(self, game_type: str) -> Dict[str, float]:
        """Get cached relevance scores for primitives on this game type."""
        if game_type in self._effectiveness_cache:
            return self._effectiveness_cache[game_type]
        
        relevance = {}
        try:
            results = self.db.execute_query("""
                SELECT primitive_name, relevance_score
                FROM primitive_game_relevance
                WHERE game_type = ?
            """, (game_type,))
            
            for r in results or []:
                relevance[r['primitive_name']] = max(0.3, min(1.5, r['relevance_score'] + 0.5))
            
            self._effectiveness_cache[game_type] = relevance
        except Exception:
            pass
        
        return relevance
    
    def _random_result(self, primitives_applied: Optional[List[str]] = None) -> SuggestionResult:
        """Return random action when no primitives help."""
        action = self.seeds.call('rand_int', 1, 7)
        return SuggestionResult(
            action=action,
            confidence=0.1,
            primitive='random',
            reasoning='No primitive suggestions - random exploration',
            candidates=[],
            primitives_applied=primitives_applied or []
        )
    
    def _direction_to_point(self, frame: List[List[int]], tx: int, ty: int) -> Optional[int]:
        """Get action to move toward target point."""
        if not frame:
            return None
        
        h, w = len(frame), len(frame[0])
        cx, cy = w // 2, h // 2
        
        dx = tx - cx
        dy = ty - cy
        
        if abs(dx) > abs(dy):
            return 3 if dx > 0 else 4  # right or left
        elif dy != 0:
            return 2 if dy > 0 else 1  # down or up
        
        return None
    
    # =========================================================================
    # PRIMITIVE WRAPPERS (call seed_primitives)
    # =========================================================================
    
    def _detect_symmetry(self, frame: List[List[int]]) -> Dict[str, Any]:
        """Detect frame symmetry."""
        try:
            return self.seeds.call('detect_symmetry', frame) or {}
        except Exception:
            # Fallback: simple symmetry check
            h, w = len(frame), len(frame[0])
            
            # Check horizontal symmetry
            h_sym = True
            for y in range(h):
                for x in range(w // 2):
                    if frame[y][x] != frame[y][w - 1 - x]:
                        h_sym = False
                        break
                if not h_sym:
                    break
            
            # Check vertical symmetry  
            v_sym = True
            for y in range(h // 2):
                if frame[y] != frame[h - 1 - y]:
                    v_sym = False
                    break
            
            return {'horizontal': h_sym, 'vertical': v_sym}
    
    def _detect_motion(self, frame: List[List[int]]) -> Dict[str, Any]:
        """Detect motion between frames."""
        try:
            return self.seeds.call('detect_motion', frame) or {}
        except Exception:
            return {}
    
    def _find_color_clusters(self, frame: List[List[int]]) -> List[Dict[str, Any]]:
        """Find color clusters/regions."""
        try:
            result = self.seeds.call('find_color_clusters', frame)
            return result if isinstance(result, list) else []
        except Exception:
            # Fallback: find unique colors and their centers
            h, w = len(frame), len(frame[0])
            colors: Dict[int, List[Tuple[int, int]]] = {}
            
            for y in range(h):
                for x in range(w):
                    c = frame[y][x]
                    if c not in colors:
                        colors[c] = []
                    colors[c].append((x, y))
            
            clusters = []
            for color, positions in colors.items():
                if len(positions) > 5:  # Ignore tiny clusters
                    cx = sum(p[0] for p in positions) // len(positions)
                    cy = sum(p[1] for p in positions) // len(positions)
                    clusters.append({
                        'color': color,
                        'center': (cx, cy),
                        'size': len(positions)
                    })
            
            return sorted(clusters, key=lambda c: c['size'], reverse=True)
    
    def _detect_edges(self, frame: List[List[int]]) -> Dict[str, Any]:
        """Detect edges/boundaries."""
        try:
            return self.seeds.call('detect_edges', frame) or {}
        except Exception:
            # Fallback: count color transitions in each direction
            h, w = len(frame), len(frame[0])
            edges = {'up': 0, 'down': 0, 'left': 0, 'right': 0}
            
            # Check top/bottom edges
            for x in range(w):
                if frame[0][x] != frame[1][x]:
                    edges['up'] += 1
                if frame[h-1][x] != frame[h-2][x]:
                    edges['down'] += 1
            
            # Check left/right edges
            for y in range(h):
                if frame[y][0] != frame[y][1]:
                    edges['left'] += 1
                if frame[y][w-1] != frame[y][w-2]:
                    edges['right'] += 1
            
            strongest = max(edges, key=lambda k: edges[k])
            return {'strongest_direction': strongest if edges[strongest] > 2 else None}
    
    def _detect_novelty(self, frame: List[List[int]]) -> Dict[str, Any]:
        """Detect novel/unusual regions."""
        try:
            return self.seeds.call('detect_novelty', frame) or {}
        except Exception:
            # Fallback: find rarest color cluster
            clusters = self._find_color_clusters(frame)
            if clusters:
                # Smallest non-trivial cluster is most "novel"
                for c in reversed(clusters):
                    if c['size'] > 3:
                        return {'novel_region': c['center']}
            return {}
    
    def _detect_goal(self, frame: List[List[int]]) -> Dict[str, Any]:
        """Detect potential goal objects."""
        try:
            return self.seeds.call('detect_goal', frame) or {}
        except Exception:
            # Fallback: bright/distinct colored small objects
            h, w = len(frame), len(frame[0])
            clusters = self._find_color_clusters(frame)
            
            # Look for small bright clusters (potential goals)
            for c in clusters:
                if 3 < c['size'] < 50 and c['color'] > 5:  # Small, non-dark
                    return {'position': c['center'], 'color': c['color']}
            
            return {}
    
    # =========================================================================
    # STATS
    # =========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        try:
            effectiveness = self.db.execute_query("""
                SELECT game_type, primitive_name, 
                       SUM(successes) as total_success,
                       SUM(failures) as total_fail
                FROM primitive_action_effectiveness
                GROUP BY game_type, primitive_name
                ORDER BY total_success DESC
                LIMIT 20
            """)
            
            relevance = self.db.execute_query("""
                SELECT game_type, primitive_name, relevance_score
                FROM primitive_game_relevance
                WHERE relevance_score > 0.5
                ORDER BY relevance_score DESC
                LIMIT 20
            """)
            
            return {
                'effectiveness': [dict(r) for r in effectiveness] if effectiveness else [],
                'relevance': [dict(r) for r in relevance] if relevance else [],
                'primitives_available': len(self.seeds.primitives)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_effectiveness_stats(self) -> Dict[str, Any]:
        """
        Get effectiveness statistics for autonomous_evolution_runner.
        
        Returns:
            dict with total_tracked, top_performing, underexplored primitives
        """
        try:
            # Count total tracked primitive-action pairs
            total_result = self.db.execute_query("""
                SELECT COUNT(*) as cnt FROM primitive_action_effectiveness
            """)
            total_tracked = total_result[0]['cnt'] if total_result else 0
            
            # Get top performing primitives (highest success rate with min samples)
            top_result = self.db.execute_query("""
                SELECT primitive_name,
                       SUM(successes) as wins,
                       SUM(failures) as losses,
                       CASE WHEN SUM(successes + failures) > 0 
                            THEN CAST(SUM(successes) AS REAL) / SUM(successes + failures)
                            ELSE 0 END as score
                FROM primitive_action_effectiveness
                GROUP BY primitive_name
                HAVING SUM(successes + failures) >= 5
                ORDER BY score DESC
                LIMIT 10
            """)
            
            top_performing = []
            if top_result:
                for r in top_result:
                    top_performing.append({
                        'primitive': r['primitive_name'],
                        'score': r['score'],
                        'wins': r['wins'],
                        'losses': r['losses']
                    })
            
            # Get underexplored primitives (few uses)
            underexplored_result = self.db.execute_query("""
                SELECT primitive_name, SUM(successes + failures) as uses
                FROM primitive_action_effectiveness
                GROUP BY primitive_name
                HAVING uses < 5
                ORDER BY uses ASC
                LIMIT 10
            """)
            
            underexplored = []
            if underexplored_result:
                underexplored = [r['primitive_name'] for r in underexplored_result]
            
            return {
                'total_tracked': total_tracked,
                'top_performing': top_performing,
                'underexplored': underexplored
            }
        except Exception as e:
            logger.debug(f"Effectiveness stats error: {e}")
            return {
                'total_tracked': 0,
                'top_performing': [],
                'underexplored': [],
                'error': str(e)
            }
    
    def record_game_result(
        self,
        game_type: str,
        won: bool,
        final_score: int
    ) -> None:
        """
        Record overall game result for primitive effectiveness tracking.
        
        This provides feedback on which primitives contributed to wins.
        Called periodically (not every game) to track overall trends.
        
        Args:
            game_type: Type of game played
            won: Whether the game was won
            final_score: Final score achieved
        """
        try:
            # Update relevance scores based on win/loss
            # If we won, primitives with high relevance for this game were helpful
            adjustment = 0.05 if won else -0.02
            
            self.db.execute_query("""
                UPDATE primitive_game_relevance
                SET relevance_score = MIN(1.0, MAX(0.1, relevance_score + ?)),
                    last_updated = CURRENT_TIMESTAMP
                WHERE game_type = ?
            """, (adjustment, game_type))
            
            logger.debug(f"Recorded game result for {game_type}: won={won}, score={final_score}")
        except Exception as e:
            logger.debug(f"Record game result error: {e}")


# Singleton instance
_suggester: Optional[PrimitiveSuggester] = None


def get_primitive_suggester(
    db: Optional[DatabaseInterface] = None,
    db_path: str = "core_data.db"
) -> PrimitiveSuggester:
    """
    Get or create singleton PrimitiveSuggester.
    
    Args:
        db: Existing database interface (preferred)
        db_path: Path to database if db not provided
        
    Returns:
        PrimitiveSuggester instance
    """
    global _suggester
    if _suggester is None:
        if db:
            _suggester = PrimitiveSuggester(db=db)
        else:
            _suggester = PrimitiveSuggester(db_path=db_path)
    return _suggester
