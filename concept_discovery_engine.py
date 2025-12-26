import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
Concept Discovery Engine - Tier 4 of CODS Architecture

Discovers high-level concepts that organize operators.
Concepts are abstractions over successful operator patterns.

FOUR-TIER ARCHITECTURE:
- Tier 1: Seed Primitives (Given) - Raw data access
- Tier 2: Operators (Compositions) - Tested through RLVR
- Tier 3: Locked/Novel Primitives (Earned) - Discovered or composed
- Tier 4: Concepts (Semantic Models) - Cross-game pattern recognition

Concepts emerge when:
1. Operators succeed across multiple games
2. System detects shared sub-patterns
3. The shared pattern is abstracted as the organizing principle
4. Future games use concept to suggest relevant operators

Example:
- Operators for "boundary sealing" work across FT09, SP80, etc.
- Common pattern: "seal edges before flow"
- Concept emerges: "Containment"
- Future: "This looks like containment, try boundary operators"
"""

import logging
import json
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


@dataclass
class ConceptCandidate:
    """Tracks a pattern that might become a concept."""
    pattern: str
    games: Set[str] = field(default_factory=set)
    operators: Set[str] = field(default_factory=set)
    success_count: int = 0
    failure_count: int = 0
    first_seen: datetime = field(default_factory=datetime.now)
    last_success: Optional[datetime] = None


@dataclass
class Concept:
    """A confirmed high-level organizing concept."""
    concept_id: str
    name: str
    pattern: str
    games_proven: List[str]
    operators_using: List[str]
    confidence: float
    semantic_model: str
    biological_analog: Optional[str] = None
    physical_analog: Optional[str] = None
    computational_analog: Optional[str] = None
    discovered_at: datetime = field(default_factory=datetime.now)


# Pre-defined conceptual primitives (from CODS design)
# These are targets that the system can discover
CONCEPTUAL_PRIMITIVES = {
    'containment': {
        'components': ['boundary_detection', 'capacity_estimation', 'overflow_prediction'],
        'semantic_model': 'Bounded regions with finite capacity',
        'biological_analog': 'Cell membranes, immune barriers',
        'organizes_operators': ['boundary_seal_check', 'flow_simulation', 'containment_check'],
        'keywords': ['boundary', 'seal', 'contain', 'overflow', 'capacity', 'flow']
    },
    'reference_semantics': {
        'components': ['reference_detection', 'schema_extraction', 'variable_binding'],
        'semantic_model': 'Objects can represent rules about other objects',
        'biological_analog': 'DNA as template for proteins',
        'computational_analog': 'Functions with parameters',
        'organizes_operators': ['identify_reference_object', 'extract_schema', 'apply_template'],
        'keywords': ['reference', 'template', 'schema', 'pattern', 'apply', 'binding']
    },
    'conservation': {
        'components': ['quantity_tracking', 'transformation_rules', 'balance_verification'],
        'semantic_model': 'Quantities preserved under transformation',
        'physical_analog': 'Conservation of mass/energy',
        'organizes_operators': ['conservation_tracking', 'quantity_balance', 'transformation_verify'],
        'keywords': ['conserve', 'preserve', 'balance', 'total', 'quantity', 'count']
    },
    'causality': {
        'components': ['precondition_detection', 'effect_prediction', 'counterfactual_analysis'],
        'semantic_model': 'Action A causes state change B',
        'organizes_operators': ['causal_link', 'effect_scope', 'action_impact', 'dependency_check'],
        'keywords': ['cause', 'effect', 'trigger', 'result', 'if_then', 'dependency']
    },
    'goal_directedness': {
        'components': ['goal_identification', 'distance_estimation', 'subgoal_decomposition'],
        'semantic_model': 'Current state should transform toward target state',
        'organizes_operators': ['goal_distance', 'subgoal_extract', 'progress_estimate'],
        'keywords': ['goal', 'target', 'destination', 'reach', 'achieve', 'complete']
    },
    'symmetry': {
        'components': ['symmetry_detection', 'axis_identification', 'transformation_type'],
        'semantic_model': 'Patterns that are invariant under transformation',
        'biological_analog': 'Bilateral symmetry in organisms',
        'organizes_operators': ['detect_symmetry', 'mirror_pattern', 'rotate_pattern'],
        'keywords': ['symmetric', 'mirror', 'rotate', 'flip', 'same_on_both']
    },
    'hierarchy': {
        'components': ['containment_relations', 'parent_child_detection', 'nesting_level'],
        'semantic_model': 'Objects can contain other objects in tree structure',
        'computational_analog': 'Tree data structures',
        'organizes_operators': ['detect_nesting', 'find_parent', 'enumerate_children'],
        'keywords': ['nested', 'inside', 'contains', 'parent', 'child', 'level']
    }
}


class ConceptDiscoveryEngine:
    """
    Discovers high-level concepts that organize operators.
    Concepts are abstractions over successful operator patterns.
    
    EMERGENCE CRITERIA:
    - Pattern must succeed across 3+ different game types
    - Pattern must be used by 2+ distinct operators
    - Success rate must exceed 60%
    
    DISCOVERY METHODS:
    1. Cross-game pattern tracking (operators that work across games)
    2. Counterfactual analysis (what made success different from failure)
    3. Keyword clustering (semantic similarity of operator descriptions)
    """
    
    def __init__(
        self,
        db: Optional[DatabaseInterface] = None,
        db_path: str = "core_data.db"
    ):
        self.db = db or DatabaseInterface(db_path)
        self.concept_candidates: Dict[str, ConceptCandidate] = {}
        self.confirmed_concepts: Dict[str, Concept] = {}
        
        # Ensure database tables exist
        self._ensure_schema()
        
        # Load existing concepts from database
        self._load_concepts()
        
        logger.info(f"[CONCEPT] Engine initialized with {len(self.confirmed_concepts)} concepts")
    
    def _ensure_schema(self) -> None:
        """Ensure required database tables exist."""
        # Concept candidates table
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS concept_candidates (
                pattern TEXT PRIMARY KEY,
                games TEXT,           -- JSON list
                operators TEXT,       -- JSON list
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_success DATETIME
            )
        """)
        
        # Confirmed concepts table
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS discovered_concepts (
                concept_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                pattern TEXT NOT NULL,
                games_proven TEXT,    -- JSON list
                operators_using TEXT, -- JSON list
                confidence REAL,
                semantic_model TEXT,
                biological_analog TEXT,
                physical_analog TEXT,
                computational_analog TEXT,
                discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Concept-operator associations
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS concept_operator_map (
                concept_id TEXT NOT NULL,
                operator_id TEXT NOT NULL,
                relevance_score REAL DEFAULT 0.5,
                use_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                last_used DATETIME,
                PRIMARY KEY (concept_id, operator_id)
            )
        """)
        
        # Index for fast lookup
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_concept_candidates_success 
            ON concept_candidates(success_count DESC)
        """)
    
    def _load_concepts(self) -> None:
        """Load existing concepts from database."""
        results = self.db.execute_query("""
            SELECT * FROM discovered_concepts
            ORDER BY confidence DESC
        """)
        
        for row in results or []:
            concept = Concept(
                concept_id=row['concept_id'],
                name=row['name'],
                pattern=row['pattern'],
                games_proven=json.loads(row['games_proven'] or '[]'),
                operators_using=json.loads(row['operators_using'] or '[]'),
                confidence=row['confidence'],
                semantic_model=row['semantic_model'] or '',
                biological_analog=row.get('biological_analog'),
                physical_analog=row.get('physical_analog'),
                computational_analog=row.get('computational_analog')
            )
            self.confirmed_concepts[concept.concept_id] = concept
    
    def track_successful_operator_pattern(
        self,
        operator_id: str,
        game_id: str,
        sub_patterns: List[str]
    ) -> None:
        """
        Track which sub-patterns appear in successful operators.
        When same sub-pattern succeeds across multiple games,
        it's a concept candidate.
        
        Args:
            operator_id: ID of the successful operator
            game_id: Game where success occurred
            sub_patterns: Component patterns of the operator
        """
        game_type = game_id.split('-')[0] if '-' in game_id else game_id
        
        for pattern in sub_patterns:
            if pattern not in self.concept_candidates:
                self.concept_candidates[pattern] = ConceptCandidate(pattern=pattern)
            
            candidate = self.concept_candidates[pattern]
            candidate.games.add(game_type)
            candidate.operators.add(operator_id)
            candidate.success_count += 1
            candidate.last_success = datetime.now()
            
            # Update database
            self._save_candidate(candidate)
        
        logger.debug(
            f"[CONCEPT] Tracked {len(sub_patterns)} patterns from "
            f"operator {operator_id[:8]} on {game_type}"
        )
    
    def track_failed_operator_pattern(
        self,
        operator_id: str,
        game_id: str,
        sub_patterns: List[str]
    ) -> None:
        """
        Track patterns from failed operators.
        This helps refine concept boundaries.
        """
        for pattern in sub_patterns:
            if pattern in self.concept_candidates:
                self.concept_candidates[pattern].failure_count += 1
                self._save_candidate(self.concept_candidates[pattern])
    
    def _save_candidate(self, candidate: ConceptCandidate) -> None:
        """Save or update a concept candidate in database."""
        self.db.execute_query("""
            INSERT OR REPLACE INTO concept_candidates
            (pattern, games, operators, success_count, failure_count, 
             first_seen, last_success)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            candidate.pattern,
            json.dumps(list(candidate.games)),
            json.dumps(list(candidate.operators)),
            candidate.success_count,
            candidate.failure_count,
            candidate.first_seen.isoformat(),
            candidate.last_success.isoformat() if candidate.last_success else None
        ))
    
    def check_concept_emergence(
        self,
        min_games: int = 3,
        min_operators: int = 2,
        min_success_rate: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        Check if any pattern has emerged as a concept.
        A concept emerges when a pattern succeeds across N different games.
        
        Args:
            min_games: Minimum games for concept confirmation
            min_operators: Minimum operators using the pattern
            min_success_rate: Minimum success rate threshold
            
        Returns:
            List of emerging concept dicts
        """
        emerging_concepts = []
        
        for pattern, data in self.concept_candidates.items():
            # Skip if already a confirmed concept
            if any(c.pattern == pattern for c in self.confirmed_concepts.values()):
                continue
            
            # Check emergence criteria
            games_count = len(data.games)
            operators_count = len(data.operators)
            total_attempts = data.success_count + data.failure_count
            success_rate = data.success_count / total_attempts if total_attempts > 0 else 0
            
            if (games_count >= min_games and 
                operators_count >= min_operators and 
                success_rate >= min_success_rate):
                
                # Match to known conceptual primitives
                matched_concept = self._match_to_known_concept(pattern)
                
                concept_dict = {
                    'pattern': pattern,
                    'games_proven': list(data.games),
                    'operators_using': list(data.operators),
                    'confidence': success_rate,
                    'success_count': data.success_count,
                    'matched_known_concept': matched_concept
                }
                emerging_concepts.append(concept_dict)
                
                logger.info(
                    f"[CONCEPT EMERGE] Pattern '{pattern}' emerged! "
                    f"{games_count} games, {operators_count} operators, "
                    f"{success_rate:.0%} success rate"
                )
        
        return emerging_concepts
    
    def _match_to_known_concept(self, pattern: str) -> Optional[str]:
        """Check if pattern matches a known conceptual primitive."""
        pattern_lower = pattern.lower()
        
        for concept_name, concept_data in CONCEPTUAL_PRIMITIVES.items():
            keywords = concept_data.get('keywords', [])
            if any(kw in pattern_lower for kw in keywords):
                return concept_name
        
        return None
    
    def confirm_concept(
        self,
        pattern: str,
        name: Optional[str] = None
    ) -> Optional[Concept]:
        """
        Confirm a candidate pattern as a concept.
        
        Args:
            pattern: The pattern to confirm
            name: Optional human-readable name
            
        Returns:
            Confirmed Concept or None if candidate not found
        """
        if pattern not in self.concept_candidates:
            logger.warning(f"[CONCEPT] Pattern '{pattern}' not found in candidates")
            return None
        
        candidate = self.concept_candidates[pattern]
        
        # Generate concept ID
        import uuid
        concept_id = str(uuid.uuid4())
        
        # Match to known concept for semantic model
        matched = self._match_to_known_concept(pattern)
        known_data = CONCEPTUAL_PRIMITIVES.get(matched, {}) if matched else {}
        
        # Create concept
        concept = Concept(
            concept_id=concept_id,
            name=name or matched or pattern[:30],
            pattern=pattern,
            games_proven=list(candidate.games),
            operators_using=list(candidate.operators),
            confidence=candidate.success_count / (candidate.success_count + candidate.failure_count + 1),
            semantic_model=known_data.get('semantic_model', f'Pattern: {pattern}'),
            biological_analog=known_data.get('biological_analog'),
            physical_analog=known_data.get('physical_analog'),
            computational_analog=known_data.get('computational_analog')
        )
        
        # Save to database
        self.db.execute_query("""
            INSERT INTO discovered_concepts
            (concept_id, name, pattern, games_proven, operators_using, 
             confidence, semantic_model, biological_analog, physical_analog,
             computational_analog)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            concept.concept_id,
            concept.name,
            concept.pattern,
            json.dumps(concept.games_proven),
            json.dumps(concept.operators_using),
            concept.confidence,
            concept.semantic_model,
            concept.biological_analog,
            concept.physical_analog,
            concept.computational_analog
        ))
        
        self.confirmed_concepts[concept_id] = concept
        
        logger.info(f"[CONCEPT CONFIRMED] '{concept.name}' (ID: {concept_id[:8]})")
        
        return concept
    
    def extract_concept_from_counterfactuals(
        self,
        failed_attempts: List[Dict],
        successful_attempt: Dict
    ) -> Optional[Dict[str, Any]]:
        """
        When attempts 1-99 fail and attempt 100 succeeds,
        extract what made the difference as a concept candidate.
        
        Example pattern (containment problems):
        - Failed: Create path from source to target
        - Success: Seal edges THEN create path
        - Concept: "Containment" = seal boundaries before flow
        
        Args:
            failed_attempts: List of failed attempt dicts with 'sub_patterns' key
            successful_attempt: The successful attempt dict
            
        Returns:
            Concept candidate dict or None
        """
        # Find what's in success but not in failures
        success_patterns = set(successful_attempt.get('sub_patterns', []))
        failure_patterns = set()
        
        # Only look at recent failures
        for attempt in failed_attempts[-10:]:
            failure_patterns.update(attempt.get('sub_patterns', []))
        
        novel_patterns = success_patterns - failure_patterns
        
        if novel_patterns:
            candidate = {
                'candidate_patterns': list(novel_patterns),
                'source': 'counterfactual_analysis',
                'game_id': successful_attempt.get('game_id'),
                'hypothesis': 'These patterns differentiate success from failure'
            }
            
            # Track these as candidates
            game_id = successful_attempt.get('game_id', 'unknown')
            operator_id = successful_attempt.get('operator_id', 'counterfactual')
            
            for pattern in novel_patterns:
                self.track_successful_operator_pattern(
                    operator_id=operator_id,
                    game_id=game_id,
                    sub_patterns=[pattern]
                )
            
            logger.info(
                f"[COUNTERFACTUAL] Found {len(novel_patterns)} novel patterns: "
                f"{list(novel_patterns)[:3]}"
            )
            
            return candidate
        
        return None
    
    def get_relevant_operators_for_concept(
        self,
        concept_id: str,
        min_relevance: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Get operators that are relevant to a concept.
        
        Args:
            concept_id: Concept to query
            min_relevance: Minimum relevance score
            
        Returns:
            List of operator info dicts
        """
        results = self.db.execute_query("""
            SELECT operator_id, relevance_score, use_count, success_count
            FROM concept_operator_map
            WHERE concept_id = ? AND relevance_score >= ?
            ORDER BY relevance_score DESC, success_count DESC
        """, (concept_id, min_relevance))
        
        return [
            {
                'operator_id': r['operator_id'],
                'relevance': r['relevance_score'],
                'use_count': r['use_count'],
                'success_count': r['success_count']
            }
            for r in results or []
        ]
    
    def suggest_concept_for_game(
        self,
        game_type: str,
        frame: Optional[List] = None
    ) -> Optional[Concept]:
        """
        Suggest which concept might apply to a game.
        
        Args:
            game_type: The game type to analyze
            frame: Optional current frame for visual analysis
            
        Returns:
            Best matching concept or None
        """
        # Check if this game type has known concept associations
        for concept in self.confirmed_concepts.values():
            if game_type in concept.games_proven:
                logger.debug(
                    f"[CONCEPT] Game {game_type} known to use '{concept.name}'"
                )
                return concept
        
        # TODO: Use frame analysis to detect concept-relevant patterns
        # (e.g., detect boundaries for containment, detect templates for reference_semantics)
        
        return None
    
    def associate_operator_with_concept(
        self,
        operator_id: str,
        concept_id: str,
        success: bool
    ) -> None:
        """
        Record association between operator and concept.
        Updates relevance score based on success/failure.
        """
        existing = self.db.execute_query("""
            SELECT relevance_score, use_count, success_count
            FROM concept_operator_map
            WHERE concept_id = ? AND operator_id = ?
        """, (concept_id, operator_id))
        
        if existing:
            old_relevance = existing[0]['relevance_score']
            old_use = existing[0]['use_count']
            old_success = existing[0]['success_count']
            
            # Update relevance using exponential moving average
            new_relevance = old_relevance * 0.9 + (1.0 if success else 0.0) * 0.1
            
            self.db.execute_query("""
                UPDATE concept_operator_map
                SET relevance_score = ?,
                    use_count = use_count + 1,
                    success_count = success_count + ?,
                    last_used = CURRENT_TIMESTAMP
                WHERE concept_id = ? AND operator_id = ?
            """, (new_relevance, 1 if success else 0, concept_id, operator_id))
        else:
            # New association
            self.db.execute_query("""
                INSERT INTO concept_operator_map
                (concept_id, operator_id, relevance_score, use_count, success_count, last_used)
                VALUES (?, ?, ?, 1, ?, CURRENT_TIMESTAMP)
            """, (concept_id, operator_id, 0.5 if success else 0.3, 1 if success else 0))
    
    def get_concept_stats(self) -> Dict[str, Any]:
        """Get statistics about discovered concepts."""
        return {
            'total_concepts': len(self.confirmed_concepts),
            'candidate_count': len(self.concept_candidates),
            'concepts': [
                {
                    'name': c.name,
                    'confidence': c.confidence,
                    'games_proven': len(c.games_proven),
                    'operators': len(c.operators_using)
                }
                for c in self.confirmed_concepts.values()
            ],
            'top_candidates': [
                {
                    'pattern': p,
                    'games': len(c.games),
                    'success_rate': c.success_count / (c.success_count + c.failure_count + 1)
                }
                for p, c in sorted(
                    self.concept_candidates.items(),
                    key=lambda x: len(x[1].games),
                    reverse=True
                )[:5]
            ]
        }


# Global instance
_concept_engine: Optional[ConceptDiscoveryEngine] = None


def get_concept_engine(db_path: str = "core_data.db") -> ConceptDiscoveryEngine:
    """Get or create the global concept discovery engine."""
    global _concept_engine
    if _concept_engine is None:
        _concept_engine = ConceptDiscoveryEngine(db_path=db_path)
    return _concept_engine
