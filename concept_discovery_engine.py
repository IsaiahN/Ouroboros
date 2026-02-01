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

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from database_interface import DatabaseInterface

# Primitive unlock pressure - concepts drive primitive unlocking
try:
    from primitive_unlock_manager import PrimitiveStatus, PrimitiveUnlockManager
    UNLOCK_MANAGER_AVAILABLE = True
except ImportError:
    UNLOCK_MANAGER_AVAILABLE = False
    PrimitiveUnlockManager = None
    PrimitiveStatus = None

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

        # Primitive unlock manager - concepts drive primitive unlocking
        if UNLOCK_MANAGER_AVAILABLE:
            self.unlock_manager = PrimitiveUnlockManager(db=self.db, db_path=db_path)
            logger.info("[CONCEPT] PrimitiveUnlockManager integrated for unlock pressure")
        else:
            self.unlock_manager = None
            logger.warning("[CONCEPT] PrimitiveUnlockManager not available - no unlock pressure")

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

        # NEW: Apply unlock pressure for primitives required by this concept
        self._apply_unlock_pressure_for_concept(concept)

        # =====================================================================
        # COGNITIVE INTEGRATION PHASE 4: Concepts become Sensations
        # =====================================================================
        # When a concept is confirmed, it doesn't just become "data" - it becomes
        # something the agent FEELS about objects. Red objects that killed you
        # feel dangerous BEFORE you think about why. This is categorization as
        # knowing - the agent recognizes patterns immediately through feeling.
        # =====================================================================
        self._wire_concept_to_sensations(concept)

        logger.info(f"[CONCEPT CONFIRMED] '{concept.name}' (ID: {concept_id[:8]})")

        return concept

    def _apply_unlock_pressure_for_concept(self, concept: Concept) -> int:
        """
        Apply unlock pressure for primitives required by a confirmed concept.

        When a concept is confirmed, we know the system needs certain primitives
        to fully implement it. This creates pressure to unlock those primitives.

        Args:
            concept: The confirmed concept

        Returns:
            Number of unlock attempts created
        """
        if not self.unlock_manager:
            return 0

        # Find required primitives from CONCEPTUAL_PRIMITIVES
        matched_name = self._match_to_known_concept(concept.pattern)
        if not matched_name:
            return 0

        known_data = CONCEPTUAL_PRIMITIVES.get(matched_name, {})
        required_components = known_data.get('components', [])

        unlock_attempts = 0
        for primitive_name in required_components:
            try:
                # Check if primitive is locked
                status = self.unlock_manager.db.execute_query("""
                    SELECT status FROM primitive_status WHERE primitive_name = ?
                """, (primitive_name,))

                if not status:
                    # Primitive not in system - skip
                    continue

                if status[0]['status'] in ('unlocked', 'seed', 'grandfathered'):
                    # Already available - skip
                    continue

                # Record unlock attempt driven by concept discovery
                attempt_id = self.unlock_manager.record_unlock_attempt(
                    primitive_name=primitive_name,
                    discovered_pattern={
                        'source': 'concept_discovery',
                        'concept_id': concept.concept_id,
                        'concept_name': concept.name,
                        'games_proven': concept.games_proven[:5],  # Limit for storage
                        'operators_using': concept.operators_using[:5]
                    },
                    game_ids_tested=concept.games_proven[:10],
                    success_rate=concept.confidence,
                    cross_game_success_rate=min(1.0, len(concept.games_proven) / 5.0),  # Scale by game count
                    agent_id=None,  # System-driven
                    generation=0  # No generation context here
                )

                unlock_attempts += 1
                logger.info(
                    f"[CONCEPT->UNLOCK] Concept '{concept.name}' drives pressure for "
                    f"primitive '{primitive_name}' (attempt: {attempt_id[:8]})"
                )

            except Exception as e:
                logger.debug(f"[CONCEPT] Failed to apply unlock pressure for {primitive_name}: {e}")

        if unlock_attempts > 0:
            logger.info(
                f"[CONCEPT] Concept '{concept.name}' created {unlock_attempts} "
                f"primitive unlock attempts for components: {required_components}"
            )

        return unlock_attempts

    def _wire_concept_to_sensations(self, concept: 'Concept') -> None:
        """
        Wire a confirmed concept to the sensation engine.

        This implements Phase 4 of the Agent-Centric Integration Plan:
        When a concept is confirmed, it becomes something the agent FEELS
        about objects - categorization as knowing. The agent recognizes
        patterns immediately through sensation, not just computation.

        Args:
            concept: The confirmed concept to wire to sensations
        """
        try:
            # Determine valence from concept's pattern and success rate
            # Higher confidence concepts should have stronger valence
            valence = 0.0

            # Analyze the pattern for typical valence indicators
            pattern_lower = concept.pattern.lower() if concept.pattern else ''

            # Negative patterns (danger, avoid, fail, death, etc.)
            negative_indicators = ['fail', 'death', 'avoid', 'danger', 'kill', 'lose', 'collision']
            # Positive patterns (success, goal, win, collect, complete)
            positive_indicators = ['success', 'goal', 'win', 'collect', 'complete', 'progress', 'solve']

            for neg in negative_indicators:
                if neg in pattern_lower:
                    valence = -0.5 * concept.confidence
                    break

            for pos in positive_indicators:
                if pos in pattern_lower:
                    valence = 0.5 * concept.confidence
                    break

            # If neutral, assign slight positive (knowledge is usually good)
            if valence == 0.0:
                valence = 0.1 * concept.confidence

            # Create sensation mapping for this concept
            # This goes into the network_sensation_mappings table
            sensation_mapping = {
                'structural_signature': concept.pattern[:100],
                'concept_id': concept.concept_id,
                'concept_name': concept.name,
                'feeling': 'known',  # "I know what this is"
                'confidence': concept.confidence,
                'valence': valence,  # good/bad/neutral
                'games_validated': concept.games_proven[:5],
                'created_from': 'concept_discovery'
            }

            # Store in database for agents to query
            self.db.execute_query("""
                INSERT OR REPLACE INTO concept_sensation_mappings
                (concept_id, concept_name, structural_signature, feeling,
                 confidence, valence, games_validated, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                concept.concept_id,
                concept.name,
                concept.pattern[:100],
                'known',
                concept.confidence,
                valence,
                json.dumps(concept.games_proven[:5])
            ))

            logger.info(
                f"[CONCEPT->SENSATION] Concept '{concept.name}' wired to sensations "
                f"(valence={valence:.2f}, feeling='known')"
            )

        except Exception as e:
            # Sensation wiring is enhancement, not critical
            logger.debug(f"[CONCEPT->SENSATION] Failed to wire concept to sensations: {e}")

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

        This is critical for GENERALIZATION - suggesting concepts for NEW games
        based on structural similarity, not just games we've seen before.

        Args:
            game_type: The game type to analyze
            frame: Optional current frame for visual analysis

        Returns:
            Best matching concept or None
        """
        # 1. Direct match: Check if this game type has known concept associations
        for concept in self.confirmed_concepts.values():
            if game_type in concept.games_proven:
                logger.debug(
                    f"[CONCEPT] Game {game_type} known to use '{concept.name}'"
                )
                return concept

        # 2. STRUCTURAL GENERALIZATION: Use frame analysis to detect concept-relevant patterns
        # This is the key to generalization - finding concepts in NEW games
        if frame is not None:
            try:
                # Get pattern library for structural matching
                pattern_lib = get_pattern_library(self.db.db_path)

                # Extract objects from frame for structural analysis
                objects = self._extract_objects_from_frame(frame)

                if objects:
                    # Find matching patterns from OTHER games
                    matches = pattern_lib.find_matching_patterns(
                        objects=objects,
                        frame=frame,
                        min_success_rate=0.4
                    )

                    if matches:
                        # Find which concepts these patterns belong to
                        for match in matches:
                            for match_game_type in match.get('game_types', []):
                                # Look for concept used in the matching game
                                for concept in self.confirmed_concepts.values():
                                    if match_game_type in concept.games_proven:
                                        logger.info(
                                            f"[CONCEPT->GENERALIZE] Suggesting '{concept.name}' for NEW game {game_type} "
                                            f"based on structural match with {match_game_type} "
                                            f"(success_rate={match.get('success_rate', 0):.0%})"
                                        )
                                        return concept

                        # If no direct concept match but patterns found, track this
                        logger.debug(
                            f"[CONCEPT] {len(matches)} structural matches found for {game_type} "
                            f"but no confirmed concept yet"
                        )
            except Exception as e:
                logger.debug(f"[CONCEPT] Structural suggestion failed: {e}")

        return None

    def _extract_objects_from_frame(self, frame: List[List[int]]) -> List[Dict[str, Any]]:
        """
        Extract object representations from a frame for structural matching.

        This enables cross-game generalization by finding similar structures.
        """
        if not frame or not isinstance(frame, list):
            return []

        try:
            # Simple object extraction: find connected regions of same color
            objects = []
            height = len(frame)
            width = len(frame[0]) if frame else 0
            visited = set()

            for y in range(height):
                for x in range(width):
                    if (x, y) not in visited:
                        color = frame[y][x]
                        if color != 0:  # Skip background
                            # Flood fill to find object
                            positions = []
                            stack = [(x, y)]
                            while stack:
                                cx, cy = stack.pop()
                                if (cx, cy) in visited or cx < 0 or cx >= width or cy < 0 or cy >= height:
                                    continue
                                if frame[cy][cx] == color:
                                    visited.add((cx, cy))
                                    positions.append((cx, cy))
                                    stack.extend([(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)])

                            if positions:
                                # Compute centroid
                                cx = sum(p[0] for p in positions) / len(positions)
                                cy = sum(p[1] for p in positions) / len(positions)

                                objects.append({
                                    'color': color,
                                    'positions': positions,
                                    'centroid': (cx, cy),
                                    'size': len(positions)
                                })

            return objects
        except Exception as e:
            logger.debug(f"[CONCEPT] Object extraction failed: {e}")
            return []

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

    def update_concept_confidence(self, concept_name: str, delta: float) -> None:
        """
        Update confidence for a concept based on outcome feedback.

        This is called by experience_outcome() when cognitive faculties provide
        feedback about whether a concept-based action was successful.

        Args:
            concept_name: Name of the concept to update
            delta: Amount to adjust confidence (positive = increase, negative = decrease)
        """
        try:
            # Update in-memory cache
            if concept_name in self.confirmed_concepts:
                concept = self.confirmed_concepts[concept_name]
                old_confidence = concept.confidence
                concept.confidence = max(0.1, min(1.0, concept.confidence + delta))

                logger.debug(
                    f"[CONCEPT] Updated '{concept_name}' confidence: "
                    f"{old_confidence:.2f} -> {concept.confidence:.2f}"
                )

            # Update database
            self.db.execute_query("""
                UPDATE concept_library
                SET confidence = MIN(1.0, MAX(0.1, confidence + ?))
                WHERE concept_name = ?
            """, (delta, concept_name))

            # Also update sensation mapping if it exists
            self.db.execute_query("""
                UPDATE concept_sensation_mappings
                SET confidence = MIN(1.0, MAX(0.1, confidence + ?))
                WHERE concept_name = ?
            """, (delta, concept_name))

        except Exception as e:
            logger.debug(f"Concept confidence update failed: {e}")


# =============================================================================
# STRUCTURAL PATTERN LIBRARY
# =============================================================================
# Fast-indexed library of structural patterns for analogical reasoning.
# Patterns are indexed by structural hash for O(1) lookup.
# =============================================================================

@dataclass
class StructuralPattern:
    """A structural pattern with its associated outcomes."""
    pattern_id: str
    structural_hash: str           # Hash of the relational structure
    object_graph: Dict[str, Any]   # Relational graph of objects
    outcomes: List[Dict[str, Any]] # What happened when this pattern was seen
    game_types: Set[str]           # Games where this pattern appeared
    success_count: int = 0
    failure_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_matched: Optional[datetime] = None


class StructuralPatternLibrary:
    """
    Fast-indexed library of structural patterns for analogical reasoning.

    Patterns are indexed by structural hash for O(1) lookup.
    Supports:
    - Pattern storage with outcome tracking
    - Fast structural matching via hash index
    - Pattern generalization across games
    - Success/failure rate tracking per pattern
    """

    def __init__(self, db: Optional[DatabaseInterface] = None, db_path: str = "core_data.db"):
        self.db = db or DatabaseInterface(db_path)
        self.patterns: Dict[str, StructuralPattern] = {}
        self.hash_index: Dict[str, List[str]] = {}  # structural_hash -> [pattern_ids]

        self._ensure_schema()
        self._load_patterns()

        logger.info(f"[PATTERN-LIB] Initialized with {len(self.patterns)} patterns")

    def _ensure_schema(self) -> None:
        """Create structural pattern tables."""
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS structural_patterns (
                pattern_id TEXT PRIMARY KEY,
                structural_hash TEXT NOT NULL,
                object_graph TEXT,     -- JSON serialized graph
                outcomes TEXT,         -- JSON list of outcomes
                game_types TEXT,       -- JSON list of game types
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_matched DATETIME
            )
        """)

        # Index for fast hash lookup
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_structural_patterns_hash
            ON structural_patterns(structural_hash)
        """)

    def _load_patterns(self) -> None:
        """Load existing patterns from database."""
        results = self.db.execute_query("""
            SELECT * FROM structural_patterns
            ORDER BY success_count DESC
            LIMIT 10000
        """)

        for row in results or []:
            pattern = StructuralPattern(
                pattern_id=row['pattern_id'],
                structural_hash=row['structural_hash'],
                object_graph=json.loads(row['object_graph'] or '{}'),
                outcomes=json.loads(row['outcomes'] or '[]'),
                game_types=set(json.loads(row['game_types'] or '[]')),
                success_count=row['success_count'],
                failure_count=row['failure_count']
            )
            self.patterns[pattern.pattern_id] = pattern

            # Build hash index
            if pattern.structural_hash not in self.hash_index:
                self.hash_index[pattern.structural_hash] = []
            self.hash_index[pattern.structural_hash].append(pattern.pattern_id)

    def compute_structural_hash(self, objects: List[Dict[str, Any]], frame: Optional[List[List[int]]] = None) -> str:
        """
        Compute a structural hash that captures relational properties.

        Hash is based on:
        - Object count by color
        - Relative positions (not absolute)
        - Adjacency relationships
        - Size distributions

        This allows matching structurally similar patterns even if
        they differ in absolute positions or colors.
        """
        import hashlib

        if not objects:
            return "empty"

        # Feature vector for hashing
        features = []

        # 1. Object count by relative size (small/medium/large)
        sizes = [len(obj.get('positions', [])) for obj in objects if obj.get('positions')]
        if sizes:
            avg_size = sum(sizes) / len(sizes)
            size_dist = {
                'small': sum(1 for s in sizes if s < avg_size * 0.5),
                'medium': sum(1 for s in sizes if avg_size * 0.5 <= s <= avg_size * 1.5),
                'large': sum(1 for s in sizes if s > avg_size * 1.5)
            }
            features.append(f"sizes:{size_dist['small']},{size_dist['medium']},{size_dist['large']}")

        # 2. Color diversity (how many unique colors)
        colors = set(obj.get('color') for obj in objects if obj.get('color') is not None)
        features.append(f"colors:{len(colors)}")

        # 3. Spatial distribution (clustered vs spread)
        centroids = [obj.get('centroid') for obj in objects if obj.get('centroid')]
        if len(centroids) >= 2:
            # Calculate average distance between objects
            total_dist = 0
            count = 0
            for i, c1 in enumerate(centroids):
                for c2 in centroids[i+1:]:
                    if c1 and c2 and len(c1) >= 2 and len(c2) >= 2:
                        dist = abs(c1[0] - c2[0]) + abs(c1[1] - c2[1])
                        total_dist += dist
                        count += 1
            avg_dist = total_dist / count if count > 0 else 0
            spread = 'tight' if avg_dist < 5 else ('medium' if avg_dist < 15 else 'spread')
            features.append(f"spread:{spread}")

        # 4. Adjacency count (how many objects touch each other)
        adjacencies = 0
        for i, obj1 in enumerate(objects):
            pos1 = set(tuple(p) for p in obj1.get('positions', []))
            for obj2 in objects[i+1:]:
                pos2 = set(tuple(p) for p in obj2.get('positions', []))
                # Check if any positions are adjacent
                for p in pos1:
                    neighbors = [(p[0]+dx, p[1]+dy) for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]]
                    if any(n in pos2 for n in neighbors):
                        adjacencies += 1
                        break
        features.append(f"adj:{adjacencies}")

        # 5. Object count
        features.append(f"count:{len(objects)}")

        # Create hash
        feature_str = "|".join(sorted(features))
        return hashlib.md5(feature_str.encode()).hexdigest()[:16]

    def index_pattern(
        self,
        objects: List[Dict[str, Any]],
        outcome: Dict[str, Any],
        game_type: str,
        success: bool,
        frame: Optional[List[List[int]]] = None
    ) -> str:
        """
        Index a new pattern or update existing one.

        Args:
            objects: List of objects in the pattern
            outcome: What happened (action taken, result)
            game_type: Game type where pattern was observed
            success: Whether the outcome was successful
            frame: Optional frame for additional context

        Returns:
            Pattern ID (new or existing)
        """
        structural_hash = self.compute_structural_hash(objects, frame)

        # Check if we have a matching pattern
        existing_ids = self.hash_index.get(structural_hash, [])

        for pid in existing_ids:
            if pid in self.patterns:
                # Update existing pattern
                pattern = self.patterns[pid]
                pattern.outcomes.append(outcome)
                pattern.game_types.add(game_type)
                if success:
                    pattern.success_count += 1
                else:
                    pattern.failure_count += 1
                pattern.last_matched = datetime.now()

                self._save_pattern(pattern)
                return pid

        # Create new pattern
        import uuid
        pattern_id = f"pat_{uuid.uuid4().hex[:12]}"

        # Build object graph (simplified relational representation)
        object_graph = {
            'objects': [
                {
                    'color': obj.get('color'),
                    'size': len(obj.get('positions', [])),
                    'centroid': obj.get('centroid')
                }
                for obj in objects
            ],
            'object_count': len(objects),
            'hash': structural_hash
        }

        pattern = StructuralPattern(
            pattern_id=pattern_id,
            structural_hash=structural_hash,
            object_graph=object_graph,
            outcomes=[outcome],
            game_types={game_type},
            success_count=1 if success else 0,
            failure_count=0 if success else 1
        )

        self.patterns[pattern_id] = pattern

        if structural_hash not in self.hash_index:
            self.hash_index[structural_hash] = []
        self.hash_index[structural_hash].append(pattern_id)

        self._save_pattern(pattern)

        logger.debug(f"[PATTERN-LIB] Indexed new pattern {pattern_id} (hash={structural_hash[:8]})")
        return pattern_id

    def find_matching_patterns(
        self,
        objects: List[Dict[str, Any]],
        frame: Optional[List[List[int]]] = None,
        min_success_rate: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Find all stored patterns structurally similar to query.

        Args:
            objects: Query objects to match
            frame: Optional frame for context
            min_success_rate: Minimum success rate to include pattern

        Returns:
            List of matching patterns with their outcomes and stats
        """
        structural_hash = self.compute_structural_hash(objects, frame)

        matching_ids = self.hash_index.get(structural_hash, [])
        results = []

        for pid in matching_ids:
            if pid not in self.patterns:
                continue

            pattern = self.patterns[pid]
            total = pattern.success_count + pattern.failure_count
            success_rate = pattern.success_count / total if total > 0 else 0

            if success_rate >= min_success_rate:
                results.append({
                    'pattern_id': pattern.pattern_id,
                    'structural_hash': pattern.structural_hash,
                    'success_rate': success_rate,
                    'success_count': pattern.success_count,
                    'failure_count': pattern.failure_count,
                    'game_types': list(pattern.game_types),
                    'outcomes': pattern.outcomes[-5:],  # Last 5 outcomes
                    'cross_game': len(pattern.game_types) > 1
                })

        # Sort by success rate and cross-game applicability
        results.sort(key=lambda x: (x['cross_game'], x['success_rate']), reverse=True)

        return results

    def get_suggested_action(
        self,
        objects: List[Dict[str, Any]],
        frame: Optional[List[List[int]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get best action suggestion based on matching patterns.

        Returns the most successful action from matching patterns.
        """
        matches = self.find_matching_patterns(objects, frame)

        if not matches:
            return None

        # Aggregate actions across all matching patterns
        action_scores: Dict[str, float] = {}

        for match in matches:
            weight = match['success_rate'] * (1.5 if match['cross_game'] else 1.0)

            for outcome in match['outcomes']:
                action = outcome.get('action')
                if action:
                    action_key = str(action)
                    if action_key not in action_scores:
                        action_scores[action_key] = 0
                    action_scores[action_key] += weight

        if not action_scores:
            return None

        best_action = max(action_scores.items(), key=lambda x: x[1])

        return {
            'suggested_action': best_action[0],
            'confidence': best_action[1] / sum(action_scores.values()),
            'pattern_count': len(matches),
            'source': 'structural_pattern_library'
        }

    def _save_pattern(self, pattern: StructuralPattern) -> None:
        """Save pattern to database."""
        self.db.execute_query("""
            INSERT OR REPLACE INTO structural_patterns
            (pattern_id, structural_hash, object_graph, outcomes, game_types,
             success_count, failure_count, created_at, last_matched)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pattern.pattern_id,
            pattern.structural_hash,
            json.dumps(pattern.object_graph),
            json.dumps(pattern.outcomes[-100:]),  # Keep last 100 outcomes
            json.dumps(list(pattern.game_types)),
            pattern.success_count,
            pattern.failure_count,
            pattern.created_at.isoformat(),
            pattern.last_matched.isoformat() if pattern.last_matched else None
        ))

    def get_stats(self) -> Dict[str, Any]:
        """Get library statistics."""
        total_patterns = len(self.patterns)
        cross_game_patterns = sum(1 for p in self.patterns.values() if len(p.game_types) > 1)

        return {
            'total_patterns': total_patterns,
            'unique_hashes': len(self.hash_index),
            'cross_game_patterns': cross_game_patterns,
            'top_patterns': [
                {
                    'id': p.pattern_id[:12],
                    'hash': p.structural_hash[:8],
                    'success_rate': p.success_count / max(p.success_count + p.failure_count, 1),
                    'games': len(p.game_types)
                }
                for p in sorted(
                    self.patterns.values(),
                    key=lambda x: x.success_count,
                    reverse=True
                )[:5]
            ]
        }


# Global instance
_pattern_library: Optional[StructuralPatternLibrary] = None


def get_pattern_library(db_path: str = "core_data.db") -> StructuralPatternLibrary:
    """Get or create the global structural pattern library."""
    global _pattern_library
    if _pattern_library is None:
        _pattern_library = StructuralPatternLibrary(db_path=db_path)
    return _pattern_library


# Global instance
_concept_engine: Optional[ConceptDiscoveryEngine] = None


def get_concept_engine(db_path: str = "core_data.db") -> ConceptDiscoveryEngine:
    """Get or create the global concept discovery engine."""
    global _concept_engine
    if _concept_engine is None:
        _concept_engine = ConceptDiscoveryEngine(db_path=db_path)
    return _concept_engine
