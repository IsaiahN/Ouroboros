"""
Oracle Interface - The unlock gatekeeper
========================================

The Oracle decides whether a discovered pattern qualifies for unlocking
a locked primitive. It's designed to be oracle-agnostic - the system
doesn't know if it's human, LLM, or automated.

Oracle Responsibilities:
1. Compare discovered patterns to locked primitives
2. Validate that RLVR criteria are met
3. Decide: unlock, reject, or mark as novel
4. Provide reasoning for decisions
5. Track oracle accuracy over time

The system earns knowledge through demonstrated understanding,
not by being handed answers.

Rule 1: Disable pycache
Rule 2: All data in database
Rule 10: Leverage existing systems
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import json
import uuid
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum

from database_interface import DatabaseInterface
from primitive_unlock_manager import PrimitiveUnlockManager, PrimitiveStatus

logger = logging.getLogger(__name__)


class OracleVerdict(Enum):
    """Possible oracle verdicts on unlock attempts."""
    APPROVED = "approved"       # Pattern matches, unlock granted
    REJECTED = "rejected"       # RLVR criteria not met
    NOVEL = "novel"            # Valid but no human analog
    PENDING = "pending"        # Awaiting human review
    COMPETITION = "competition"  # Similar to locked, run competition


@dataclass
class OracleDecision:
    """An oracle's decision on an unlock attempt."""
    decision_id: str
    attempt_id: str
    primitive_name: Optional[str]
    verdict: OracleVerdict
    confidence: float
    reasoning: str
    similarity_to_locked: float = 0.0
    novel_primitive_id: Optional[str] = None
    decided_at: str = field(default_factory=lambda: datetime.now().isoformat())


class OracleInterface:
    """
    The oracle that decides on primitive unlocks.
    
    Designed to be oracle-agnostic - could be:
    - Automated (pattern matching + RLVR validation)
    - Human review (for edge cases)
    - LLM evaluation (future capability)
    
    Key principle: System doesn't know what the oracle is.
    It just submits attempts and receives verdicts.
    """
    
    # Minimum thresholds for auto-approval
    MIN_SUCCESS_RATE = 0.70
    MIN_CROSS_GAME_RATE = 0.50
    MIN_SIMILARITY = 0.75
    MIN_GAMES_TESTED = 5
    
    def __init__(
        self,
        db: Optional[DatabaseInterface] = None,
        db_path: str = "core_data.db",
        unlock_manager: Optional[PrimitiveUnlockManager] = None
    ):
        self.db = db or DatabaseInterface(db_path)
        self.unlock_manager = unlock_manager or PrimitiveUnlockManager(db=self.db)
        self._initialize_schema()
        
        # Pattern matching functions for locked primitives
        self._pattern_matchers: Dict[str, Callable] = {}
        self._register_pattern_matchers()
    
    def _initialize_schema(self):
        """Create oracle decision tracking tables."""
        
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS oracle_decisions (
                decision_id TEXT PRIMARY KEY,
                attempt_id TEXT NOT NULL,
                primitive_name TEXT,
                
                -- Verdict
                verdict TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                reasoning TEXT,
                
                -- Pattern analysis
                similarity_to_locked REAL DEFAULT 0.0,
                matched_features TEXT,  -- JSON: which features matched
                
                -- For novel discoveries
                novel_primitive_id TEXT,
                
                -- Oracle metadata
                oracle_type TEXT DEFAULT 'automated',  -- 'automated', 'human', 'llm'
                review_needed BOOLEAN DEFAULT FALSE,
                
                decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (attempt_id) REFERENCES primitive_unlock_attempts(attempt_id)
            )
        """)
        
        # Oracle accuracy tracking
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS oracle_accuracy (
                accuracy_id TEXT PRIMARY KEY,
                decision_id TEXT NOT NULL,
                
                -- Validation
                was_correct BOOLEAN,
                validation_method TEXT,  -- 'game_performance', 'human_review', 'cross_validation'
                
                -- Performance impact
                pre_decision_success_rate REAL,
                post_decision_success_rate REAL,
                improvement REAL,
                
                validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (decision_id) REFERENCES oracle_decisions(decision_id)
            )
        """)
        
        # Pending human reviews
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS oracle_pending_reviews (
                review_id TEXT PRIMARY KEY,
                decision_id TEXT NOT NULL,
                attempt_id TEXT NOT NULL,
                
                -- Context for human reviewer
                primitive_name TEXT,
                discovered_pattern TEXT,
                success_rate REAL,
                cross_game_rate REAL,
                automated_similarity REAL,
                
                -- Review status
                reviewed BOOLEAN DEFAULT FALSE,
                reviewer_verdict TEXT,
                reviewer_notes TEXT,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_at TIMESTAMP,
                
                FOREIGN KEY (decision_id) REFERENCES oracle_decisions(decision_id)
            )
        """)
    
    def _register_pattern_matchers(self):
        """Register pattern matching functions for locked primitives."""
        
        # Pattern matchers check if a composition resembles a locked primitive
        
        self._pattern_matchers['detect_symmetry'] = self._match_symmetry_pattern
        self._pattern_matchers['flood_fill'] = self._match_flood_fill_pattern
        self._pattern_matchers['detect_shapes'] = self._match_shape_detection_pattern
        self._pattern_matchers['path_exists'] = self._match_path_exists_pattern
        self._pattern_matchers['entropy_calc'] = self._match_entropy_pattern
        self._pattern_matchers['goal_distance'] = self._match_goal_distance_pattern
        self._pattern_matchers['detect_cycles'] = self._match_cycle_detection_pattern
        self._pattern_matchers['containment_check'] = self._match_containment_pattern
        
        # Generic matchers for primitives without specific patterns
        for prim in self.unlock_manager.list_locked():
            name = prim['primitive_name']
            if name not in self._pattern_matchers:
                self._pattern_matchers[name] = self._make_generic_matcher(prim)
    
    # ======================================================================
    # MAIN API
    # ======================================================================
    
    def evaluate_unlock_attempt(
        self,
        attempt_id: str,
        force_human_review: bool = False
    ) -> OracleDecision:
        """
        Evaluate an unlock attempt and return a verdict.
        
        This is the main entry point. The system submits an attempt
        and receives a decision without knowing how it was made.
        
        Args:
            attempt_id: The unlock attempt to evaluate
            force_human_review: Request human review regardless of confidence
            
        Returns:
            OracleDecision with verdict and reasoning
        """
        # Get attempt details
        attempt = self.db.execute_query(
            "SELECT * FROM primitive_unlock_attempts WHERE attempt_id = ?",
            (attempt_id,)
        )
        if not attempt:
            return self._make_decision(
                attempt_id, None, OracleVerdict.REJECTED, 0.0,
                "Attempt not found"
            )
        
        attempt = dict(attempt[0])
        primitive_name = attempt['primitive_name']
        success_rate = attempt['success_rate'] or 0.0
        cross_game_rate = attempt['cross_game_success_rate'] or 0.0
        rlvr_passed = attempt['rlvr_validation_passed']
        pattern = json.loads(attempt['discovered_pattern']) if attempt['discovered_pattern'] else {}
        games_count = attempt['games_tested_count'] or 0
        
        # Quick rejection if RLVR failed
        if not rlvr_passed:
            return self._make_decision(
                attempt_id, primitive_name, OracleVerdict.REJECTED, 0.95,
                f"RLVR validation failed: success_rate={success_rate:.2f}, "
                f"cross_game={cross_game_rate:.2f}"
            )
        
        # Check minimum criteria
        if success_rate < self.MIN_SUCCESS_RATE:
            return self._make_decision(
                attempt_id, primitive_name, OracleVerdict.REJECTED, 0.9,
                f"Success rate {success_rate:.2f} below threshold {self.MIN_SUCCESS_RATE}"
            )
        
        if cross_game_rate < self.MIN_CROSS_GAME_RATE:
            return self._make_decision(
                attempt_id, primitive_name, OracleVerdict.REJECTED, 0.85,
                f"Cross-game rate {cross_game_rate:.2f} below threshold {self.MIN_CROSS_GAME_RATE}"
            )
        
        if games_count < self.MIN_GAMES_TESTED:
            return self._make_decision(
                attempt_id, primitive_name, OracleVerdict.PENDING, 0.5,
                f"Only {games_count} games tested, need {self.MIN_GAMES_TESTED} minimum"
            )
        
        # Pattern matching against locked primitive
        similarity = 0.0
        matched_features = []
        
        if primitive_name in self._pattern_matchers:
            matcher = self._pattern_matchers[primitive_name]
            similarity, matched_features = matcher(pattern)
        
        # Decision logic
        if similarity >= self.MIN_SIMILARITY:
            # High similarity - approve unlock
            if force_human_review:
                decision = self._make_decision(
                    attempt_id, primitive_name, OracleVerdict.PENDING, similarity,
                    f"High similarity ({similarity:.2f}) but human review requested",
                    similarity_to_locked=similarity
                )
                self._queue_human_review(decision, attempt)
                return decision
            
            # Auto-approve
            decision = self._make_decision(
                attempt_id, primitive_name, OracleVerdict.APPROVED, similarity,
                f"Pattern matches locked primitive with {similarity:.2%} similarity. "
                f"Matched features: {matched_features}",
                similarity_to_locked=similarity
            )
            
            # Actually unlock the primitive
            self.unlock_manager.approve_unlock(
                attempt_id,
                oracle_reasoning=decision.reasoning,
                similarity=similarity
            )
            
            return decision
        
        elif similarity >= 0.5:
            # Medium similarity - run competition
            decision = self._make_decision(
                attempt_id, primitive_name, OracleVerdict.COMPETITION, similarity,
                f"Partial match ({similarity:.2%}). Running competition between "
                f"discovered and human versions.",
                similarity_to_locked=similarity
            )
            self._setup_competition(attempt_id, primitive_name, pattern)
            return decision
        
        elif similarity < 0.3 and success_rate >= 0.8 and cross_game_rate >= 0.6:
            # Low similarity but high performance - NOVEL discovery!
            novel_id = self.unlock_manager.record_novel_primitive(
                composition_tree=pattern,
                discovered_by_agent=attempt.get('agent_id', 'unknown'),
                discovered_in_game=json.loads(attempt['game_ids_tested'])[0] if attempt['game_ids_tested'] else 'unknown',
                generation=attempt.get('generation', 0),
                success_rate=success_rate,
                games_validated=games_count,
                cross_game_rate=cross_game_rate
            )
            
            return self._make_decision(
                attempt_id, None, OracleVerdict.NOVEL, 0.9,
                f"Novel discovery! Pattern does not match any locked primitive "
                f"but achieves {success_rate:.1%} success across {games_count} games.",
                novel_primitive_id=novel_id
            )
        
        else:
            # Low similarity, low performance - reject
            return self._make_decision(
                attempt_id, primitive_name, OracleVerdict.REJECTED, 0.7,
                f"Pattern similarity ({similarity:.2%}) too low and performance "
                f"insufficient for novel classification."
            )
    
    def bulk_evaluate(
        self,
        attempt_ids: List[str],
        threshold_for_review: float = 0.7
    ) -> List[OracleDecision]:
        """
        Evaluate multiple unlock attempts.
        
        Args:
            attempt_ids: List of attempt IDs to evaluate
            threshold_for_review: Auto-reject below this success rate
            
        Returns:
            List of OracleDecisions
        """
        decisions = []
        
        for attempt_id in attempt_ids:
            decision = self.evaluate_unlock_attempt(attempt_id)
            decisions.append(decision)
            
            logger.info(f"[Oracle] {attempt_id[:8]}: {decision.verdict.value} "
                       f"(confidence={decision.confidence:.2f})")
        
        return decisions
    
    def get_pending_reviews(self) -> List[Dict[str, Any]]:
        """Get all pending human reviews."""
        results = self.db.execute_query("""
            SELECT * FROM oracle_pending_reviews
            WHERE reviewed = FALSE
            ORDER BY created_at ASC
        """)
        return [dict(r) for r in results] if results else []
    
    def _compute_similarity(
        self,
        composition_tree: Dict[str, Any],
        primitive_name: str
    ) -> float:
        """
        Compute similarity between a composition tree and a locked primitive.
        
        Used by post-generation unlock checker to find potential matches.
        
        Args:
            composition_tree: The composed operator's structure
            primitive_name: Target locked primitive name
            
        Returns:
            Similarity score 0.0-1.0
        """
        if primitive_name not in self._pattern_matchers:
            # No specific matcher - use generic analysis
            return self._generic_similarity(composition_tree, primitive_name)
        
        try:
            matcher = self._pattern_matchers[primitive_name]
            similarity, matched_features = matcher(composition_tree)
            return similarity
        except Exception as e:
            logger.debug(f"[Oracle] Similarity computation failed for {primitive_name}: {e}")
            return 0.0
    
    def _generic_similarity(
        self,
        composition_tree: Dict[str, Any],
        primitive_name: str
    ) -> float:
        """
        Generic similarity based on primitive name matching and structure.
        
        Used when no specific pattern matcher exists.
        """
        primitives_used = self._extract_primitives(composition_tree)
        
        # Check if primitive name appears in composition
        name_parts = primitive_name.lower().replace('_', ' ').split()
        
        similarity = 0.0
        for prim in primitives_used:
            prim_lower = prim.lower()
            for part in name_parts:
                if part in prim_lower:
                    similarity += 0.15
        
        # Cap at 0.5 for generic matching (need specific matcher for higher)
        return min(similarity, 0.5)
    
    def submit_human_review(
        self,
        review_id: str,
        verdict: str,
        notes: str = ""
    ) -> bool:
        """
        Submit human review for a pending decision.
        
        Args:
            review_id: The pending review ID
            verdict: 'approved', 'rejected', or 'novel'
            notes: Reviewer notes
            
        Returns:
            True if review processed successfully
        """
        review = self.db.execute_query(
            "SELECT * FROM oracle_pending_reviews WHERE review_id = ?",
            (review_id,)
        )
        if not review:
            return False
        
        review = dict(review[0])
        attempt_id = review['attempt_id']
        primitive_name = review['primitive_name']
        
        # Update review record
        self.db.execute_query("""
            UPDATE oracle_pending_reviews
            SET reviewed = TRUE, reviewer_verdict = ?, reviewer_notes = ?,
                reviewed_at = CURRENT_TIMESTAMP
            WHERE review_id = ?
        """, (verdict, notes, review_id))
        
        # Update oracle decision
        self.db.execute_query("""
            UPDATE oracle_decisions
            SET verdict = ?, reasoning = ?, oracle_type = 'human'
            WHERE decision_id = ?
        """, (verdict, f"Human review: {notes}", review['decision_id']))
        
        # Process verdict
        if verdict == 'approved':
            self.unlock_manager.approve_unlock(
                attempt_id,
                oracle_reasoning=f"Human approved: {notes}",
                similarity=review.get('automated_similarity', 0.8)
            )
        elif verdict == 'novel':
            pattern = json.loads(review['discovered_pattern']) if review['discovered_pattern'] else {}
            self.unlock_manager.record_novel_primitive(
                composition_tree=pattern,
                discovered_by_agent='human_validated',
                discovered_in_game='review',
                generation=0,
                success_rate=review.get('success_rate', 0.8),
                games_validated=5,
                cross_game_rate=review.get('cross_game_rate', 0.6)
            )
        
        logger.info(f"[Oracle] Human review completed: {review_id} -> {verdict}")
        return True
    
    # ======================================================================
    # PATTERN MATCHERS
    # ======================================================================
    
    def _match_symmetry_pattern(self, pattern: Dict) -> Tuple[float, List[str]]:
        """Check if pattern matches symmetry detection."""
        similarity = 0.0
        matched = []
        
        # Look for symmetry-related primitives in composition
        primitives_used = self._extract_primitives(pattern)
        
        # Symmetry typically involves:
        # - Comparing halves of grid
        # - Using equals/comparison
        # - Flipping or mirroring
        
        if 'equals' in primitives_used or 'not_equals' in primitives_used:
            similarity += 0.2
            matched.append('comparison')
        
        if 'for_each_pixel' in primitives_used:
            similarity += 0.15
            matched.append('pixel_iteration')
        
        if 'get_pixel' in primitives_used:
            similarity += 0.1
            matched.append('pixel_access')
        
        if 'subtract' in primitives_used or 'abs' in primitives_used:
            similarity += 0.15
            matched.append('difference_calc')
        
        # Check for mirror-like structure (accessing x and width-x)
        if self._has_mirror_access(pattern):
            similarity += 0.3
            matched.append('mirror_access')
        
        return min(similarity, 1.0), matched
    
    def _match_flood_fill_pattern(self, pattern: Dict) -> Tuple[float, List[str]]:
        """Check if pattern matches flood fill algorithm."""
        similarity = 0.0
        matched = []
        
        primitives_used = self._extract_primitives(pattern)
        
        # Flood fill typically involves:
        # - Recursive or iterative neighbor checking
        # - Color/value comparison
        # - Region tracking
        
        if 'get_pixel' in primitives_used:
            similarity += 0.15
            matched.append('pixel_access')
        
        if 'equals' in primitives_used:
            similarity += 0.15
            matched.append('color_comparison')
        
        if 'append' in primitives_used or 'concat' in primitives_used:
            similarity += 0.2
            matched.append('region_building')
        
        if 'contains' in primitives_used:
            similarity += 0.2
            matched.append('visited_check')
        
        # Check for neighbor access pattern
        if self._has_neighbor_access(pattern):
            similarity += 0.3
            matched.append('neighbor_access')
        
        return min(similarity, 1.0), matched
    
    def _match_shape_detection_pattern(self, pattern: Dict) -> Tuple[float, List[str]]:
        """Check if pattern matches shape detection."""
        similarity = 0.0
        matched = []
        
        primitives_used = self._extract_primitives(pattern)
        
        # Shape detection typically involves:
        # - Connected component finding
        # - Bounding box calculation
        # - Size/area computation
        
        if 'min' in primitives_used or 'max' in primitives_used:
            similarity += 0.2
            matched.append('bounds_calc')
        
        if 'len' in primitives_used or 'sum' in primitives_used:
            similarity += 0.15
            matched.append('size_calc')
        
        if 'filter' in primitives_used:
            similarity += 0.15
            matched.append('filtering')
        
        if 'unique' in primitives_used:
            similarity += 0.15
            matched.append('uniqueness')
        
        # If it has flood-fill-like patterns, it's likely shape detection
        ff_sim, _ = self._match_flood_fill_pattern(pattern)
        if ff_sim >= 0.5:
            similarity += 0.3
            matched.append('connected_components')
        
        return min(similarity, 1.0), matched
    
    def _match_path_exists_pattern(self, pattern: Dict) -> Tuple[float, List[str]]:
        """Check if pattern matches path existence checking."""
        similarity = 0.0
        matched = []
        
        primitives_used = self._extract_primitives(pattern)
        
        # Path existence typically involves:
        # - Start/end point specification
        # - Neighbor traversal
        # - Goal check
        
        if 'any' in primitives_used or 'all' in primitives_used:
            similarity += 0.2
            matched.append('condition_check')
        
        if 'equals' in primitives_used:
            similarity += 0.15
            matched.append('goal_comparison')
        
        ff_sim, _ = self._match_flood_fill_pattern(pattern)
        if ff_sim >= 0.4:
            similarity += 0.4
            matched.append('connectivity')
        
        return min(similarity, 1.0), matched
    
    def _match_entropy_pattern(self, pattern: Dict) -> Tuple[float, List[str]]:
        """Check if pattern matches entropy calculation."""
        similarity = 0.0
        matched = []
        
        primitives_used = self._extract_primitives(pattern)
        
        # Entropy typically involves:
        # - Counting occurrences
        # - Probability calculation
        # - Log-based computation (approximated)
        
        if 'map' in primitives_used or 'for_each_pixel' in primitives_used:
            similarity += 0.15
            matched.append('iteration')
        
        if 'sum' in primitives_used:
            similarity += 0.15
            matched.append('aggregation')
        
        if 'divide' in primitives_used:
            similarity += 0.2
            matched.append('normalization')
        
        if 'multiply' in primitives_used:
            similarity += 0.15
            matched.append('probability_weight')
        
        if 'unique' in primitives_used:
            similarity += 0.2
            matched.append('value_diversity')
        
        return min(similarity, 1.0), matched
    
    def _match_goal_distance_pattern(self, pattern: Dict) -> Tuple[float, List[str]]:
        """Check if pattern matches goal distance calculation."""
        similarity = 0.0
        matched = []
        
        primitives_used = self._extract_primitives(pattern)
        
        # Goal distance typically involves:
        # - Position comparison
        # - Absolute difference
        # - Aggregation (Manhattan or Euclidean)
        
        if 'subtract' in primitives_used:
            similarity += 0.2
            matched.append('difference')
        
        if 'abs' in primitives_used:
            similarity += 0.25
            matched.append('absolute_value')
        
        if 'add' in primitives_used or 'sum' in primitives_used:
            similarity += 0.2
            matched.append('distance_aggregation')
        
        if 'min' in primitives_used:
            similarity += 0.15
            matched.append('closest_goal')
        
        return min(similarity, 1.0), matched
    
    def _match_cycle_detection_pattern(self, pattern: Dict) -> Tuple[float, List[str]]:
        """Check if pattern matches cycle detection."""
        similarity = 0.0
        matched = []
        
        primitives_used = self._extract_primitives(pattern)
        
        # Cycle detection typically involves:
        # - State tracking
        # - History comparison
        # - Repetition finding
        
        if 'hash' in primitives_used or 'hash_frame' in primitives_used:
            similarity += 0.3
            matched.append('state_hashing')
        
        if 'contains' in primitives_used:
            similarity += 0.25
            matched.append('history_check')
        
        if 'equals' in primitives_used:
            similarity += 0.2
            matched.append('state_comparison')
        
        if 'get_action_history' in primitives_used or 'get_elapsed_actions' in primitives_used:
            similarity += 0.2
            matched.append('history_access')
        
        return min(similarity, 1.0), matched
    
    def _match_containment_pattern(self, pattern: Dict) -> Tuple[float, List[str]]:
        """Check if pattern matches containment checking."""
        similarity = 0.0
        matched = []
        
        primitives_used = self._extract_primitives(pattern)
        
        # Containment typically involves:
        # - Boundary detection
        # - All-sides check
        # - Enclosure verification
        
        if 'all' in primitives_used:
            similarity += 0.25
            matched.append('complete_check')
        
        if 'not_equals' in primitives_used or 'equals' in primitives_used:
            similarity += 0.15
            matched.append('boundary_comparison')
        
        # Check for edge access patterns
        if self._has_edge_access(pattern):
            similarity += 0.3
            matched.append('edge_access')
        
        ff_sim, _ = self._match_flood_fill_pattern(pattern)
        if ff_sim >= 0.4:
            similarity += 0.2
            matched.append('region_analysis')
        
        return min(similarity, 1.0), matched
    
    def _make_generic_matcher(self, prim_info: Dict) -> Callable:
        """Create a generic matcher for primitives without specific patterns."""
        category = prim_info.get('category', 'unknown')
        difficulty = prim_info.get('difficulty', 0.5)
        
        def generic_match(pattern: Dict) -> Tuple[float, List[str]]:
            primitives_used = self._extract_primitives(pattern)
            
            # Base similarity from complexity matching
            complexity = len(primitives_used) / 10.0  # Normalize
            target_complexity = difficulty
            complexity_match = 1.0 - abs(complexity - target_complexity)
            
            similarity = complexity_match * 0.3  # Max 0.3 from complexity
            matched = ['complexity_match'] if complexity_match > 0.5 else []
            
            # Category-based heuristics
            if category == 'spatial':
                if 'get_pixel' in primitives_used:
                    similarity += 0.2
                    matched.append('spatial_access')
            elif category == 'temporal':
                if 'get_previous_frame' in primitives_used:
                    similarity += 0.2
                    matched.append('temporal_access')
            elif category == 'goal':
                if 'subtract' in primitives_used or 'abs' in primitives_used:
                    similarity += 0.2
                    matched.append('distance_calc')
            
            return min(similarity, 0.6), matched  # Cap generic matches at 0.6
        
        return generic_match
    
    # ======================================================================
    # HELPERS
    # ======================================================================
    
    def _extract_primitives(self, pattern: Dict) -> List[str]:
        """Extract all primitive names used in a composition pattern."""
        primitives = []
        
        def extract(node):
            if isinstance(node, dict):
                if node.get('type') == 'primitive':
                    primitives.append(node.get('name', ''))
                for v in node.values():
                    extract(v)
            elif isinstance(node, list):
                for item in node:
                    extract(item)
        
        extract(pattern)
        return primitives
    
    def _has_mirror_access(self, pattern: Dict) -> bool:
        """Check if pattern accesses mirrored positions (x and width-x)."""
        # Simplified check - look for subtract with frame_size
        pattern_str = json.dumps(pattern)
        return 'subtract' in pattern_str and 'get_frame_size' in pattern_str
    
    def _has_neighbor_access(self, pattern: Dict) -> bool:
        """Check if pattern accesses neighboring pixels."""
        # Look for +1/-1 patterns in pixel access
        pattern_str = json.dumps(pattern)
        return ('add' in pattern_str or 'subtract' in pattern_str) and 'get_pixel' in pattern_str
    
    def _has_edge_access(self, pattern: Dict) -> bool:
        """Check if pattern specifically accesses edges."""
        pattern_str = json.dumps(pattern)
        # Check for 0 or max dimension access
        return ('0' in pattern_str and 'get_pixel' in pattern_str)
    
    def _make_decision(
        self,
        attempt_id: str,
        primitive_name: Optional[str],
        verdict: OracleVerdict,
        confidence: float,
        reasoning: str,
        similarity_to_locked: float = 0.0,
        novel_primitive_id: Optional[str] = None
    ) -> OracleDecision:
        """Create and store an oracle decision."""
        decision_id = f"dec_{uuid.uuid4().hex[:12]}"
        
        decision = OracleDecision(
            decision_id=decision_id,
            attempt_id=attempt_id,
            primitive_name=primitive_name,
            verdict=verdict,
            confidence=confidence,
            reasoning=reasoning,
            similarity_to_locked=similarity_to_locked,
            novel_primitive_id=novel_primitive_id
        )
        
        # Store in database
        self.db.execute_query("""
            INSERT INTO oracle_decisions
            (decision_id, attempt_id, primitive_name, verdict, confidence,
             reasoning, similarity_to_locked, novel_primitive_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            decision_id, attempt_id, primitive_name, verdict.value,
            confidence, reasoning, similarity_to_locked, novel_primitive_id
        ))
        
        logger.info(f"[Oracle] Decision {decision_id[:8]}: {verdict.value} "
                   f"for {primitive_name or 'novel'} (conf={confidence:.2f})")
        
        return decision
    
    def _queue_human_review(self, decision: OracleDecision, attempt: Dict):
        """Queue a decision for human review."""
        review_id = f"rev_{uuid.uuid4().hex[:12]}"
        
        self.db.execute_query("""
            INSERT INTO oracle_pending_reviews
            (review_id, decision_id, attempt_id, primitive_name, discovered_pattern,
             success_rate, cross_game_rate, automated_similarity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            review_id, decision.decision_id, attempt['attempt_id'],
            attempt['primitive_name'], attempt['discovered_pattern'],
            attempt['success_rate'], attempt['cross_game_success_rate'],
            decision.similarity_to_locked
        ))
        
        logger.info(f"[Oracle] Queued for human review: {review_id}")
    
    def _setup_competition(
        self,
        attempt_id: str,
        primitive_name: str,
        discovered_pattern: Dict
    ):
        """Set up competition between discovered and human versions."""
        competition_id = f"comp_{uuid.uuid4().hex[:12]}"
        
        self.db.execute_query("""
            INSERT OR IGNORE INTO primitive_competition
            (competition_id, primitive_name)
            VALUES (?, ?)
        """, (competition_id, primitive_name))
        
        logger.info(f"[Oracle] Competition set up for {primitive_name}")
    
    def get_oracle_stats(self) -> Dict[str, Any]:
        """Get oracle decision statistics."""
        stats = {}
        
        # Decisions by verdict
        verdicts = self.db.execute_query("""
            SELECT verdict, COUNT(*) as cnt
            FROM oracle_decisions
            GROUP BY verdict
        """)
        stats['by_verdict'] = {r['verdict']: r['cnt'] for r in verdicts} if verdicts else {}
        
        # Pending reviews
        pending = self.db.execute_query("""
            SELECT COUNT(*) as cnt FROM oracle_pending_reviews WHERE reviewed = FALSE
        """)
        stats['pending_reviews'] = pending[0]['cnt'] if pending else 0
        
        # Recent decisions
        recent = self.db.execute_query("""
            SELECT primitive_name, verdict, confidence, decided_at
            FROM oracle_decisions
            ORDER BY decided_at DESC
            LIMIT 5
        """)
        stats['recent_decisions'] = [dict(r) for r in recent] if recent else []
        
        return stats
