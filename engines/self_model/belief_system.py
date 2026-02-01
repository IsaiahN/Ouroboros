"""
Belief System - Belief Dependencies and Cascade Invalidation
===========================================================

Manages agent beliefs with proper dependency tracking:
- Beliefs depend on other beliefs
- When a foundation belief is invalidated, dependents cascade
- Confidence propagation through belief network

Design Principles:
- Explicit dependency tracking
- Cascade invalidation with audit trail
- No orphaned beliefs
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import logging
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Tuple
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class BeliefType(Enum):
    """Types of beliefs."""
    AXIOM = "axiom"              # Foundational, not dependent
    OBSERVATION = "observation"  # From direct observation
    INFERENCE = "inference"      # Inferred from other beliefs
    HYPOTHESIS = "hypothesis"    # Tentative, needs validation
    RULE = "rule"               # Learned rule/pattern


class BeliefStatus(Enum):
    """Status of a belief."""
    ACTIVE = "active"
    INVALIDATED = "invalidated"
    SUPERSEDED = "superseded"
    PENDING = "pending"


@dataclass
class Belief:
    """A belief with dependencies."""
    belief_id: str
    belief_type: BeliefType
    status: BeliefStatus
    
    # Content
    statement: str
    domain: str  # game_type or "universal"
    evidence: List[str]
    
    # Confidence
    confidence: float  # 0.0 to 1.0
    supporting_observations: int = 0
    contradicting_observations: int = 0
    
    # Dependencies
    depends_on: Set[str] = field(default_factory=set)  # belief_ids this depends on
    depended_by: Set[str] = field(default_factory=set)  # belief_ids that depend on this
    
    # Metadata
    created_at: str = ""
    invalidated_at: str = ""
    invalidation_reason: str = ""
    
    @property
    def is_valid(self) -> bool:
        return self.status == BeliefStatus.ACTIVE
    
    def add_evidence(self, evidence_str: str, supports: bool = True) -> None:
        """Add evidence for/against this belief."""
        self.evidence.append(evidence_str)
        
        if supports:
            self.supporting_observations += 1
            self.confidence = min(1.0, self.confidence + 0.05)
        else:
            self.contradicting_observations += 1
            self.confidence = max(0.0, self.confidence - 0.1)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'belief_id': self.belief_id,
            'belief_type': self.belief_type.value,
            'status': self.status.value,
            'statement': self.statement,
            'domain': self.domain,
            'evidence': self.evidence,
            'confidence': self.confidence,
            'supporting_observations': self.supporting_observations,
            'contradicting_observations': self.contradicting_observations,
            'depends_on': list(self.depends_on),
            'depended_by': list(self.depended_by),
            'created_at': self.created_at,
            'invalidated_at': self.invalidated_at,
            'invalidation_reason': self.invalidation_reason
        }


@dataclass
class InvalidationEvent:
    """Record of a belief invalidation."""
    event_id: str
    source_belief_id: str
    invalidation_reason: str
    cascade_count: int
    invalidated_beliefs: List[str]
    timestamp: str


class BeliefSystem:
    """
    Manages beliefs with dependency tracking and cascade invalidation.
    
    Usage:
        system = BeliefSystem(db_path)
        
        # Create a foundation belief
        belief1 = system.create_belief(
            belief_type=BeliefType.OBSERVATION,
            statement="ACTION1 moves the blue object up",
            domain="sp80",
            confidence=0.8,
            evidence=["Observed movement in level 1"]
        )
        
        # Create dependent belief
        belief2 = system.create_belief(
            belief_type=BeliefType.INFERENCE,
            statement="The blue object is player-controlled",
            domain="sp80",
            confidence=0.7,
            evidence=["Inferred from movement response"],
            depends_on={belief1.belief_id}
        )
        
        # When foundation fails, dependents cascade
        system.invalidate_belief(belief1.belief_id, reason="Movement stopped working")
        # belief2 is also invalidated automatically
        
        # Query valid beliefs
        active = system.get_beliefs(domain="sp80", only_valid=True)
    """
    
    def __init__(self, db_path: str = "core_data.db"):
        """
        Initialize belief system.
        
        Args:
            db_path: Path to database
        """
        try:
            from database_interface import DatabaseInterface
            self.db = DatabaseInterface(db_path)
        except Exception as e:
            raise RuntimeError(f"[BELIEF] Failed to connect to database: {e}")
        
        self._beliefs: Dict[str, Belief] = {}
        self._ensure_tables()
        logger.info("[BELIEF] Initialized")
    
    def _ensure_tables(self) -> None:
        """Ensure required tables exist."""
        try:
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS beliefs (
                    belief_id TEXT PRIMARY KEY,
                    belief_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    statement TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    evidence_json TEXT,
                    confidence REAL DEFAULT 0.5,
                    supporting_observations INTEGER DEFAULT 0,
                    contradicting_observations INTEGER DEFAULT 0,
                    depends_on_json TEXT,
                    depended_by_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    invalidated_at TIMESTAMP,
                    invalidation_reason TEXT
                )
            """)
            
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS belief_invalidation_events (
                    event_id TEXT PRIMARY KEY,
                    source_belief_id TEXT NOT NULL,
                    invalidation_reason TEXT,
                    cascade_count INTEGER DEFAULT 0,
                    invalidated_beliefs_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_beliefs_domain
                ON beliefs(domain, status)
            """)
            
            logger.debug("[BELIEF] Tables verified")
        except Exception as e:
            logger.error(f"[BELIEF] Table creation failed: {e}")
            raise
    
    def create_belief(
        self,
        belief_type: BeliefType,
        statement: str,
        domain: str,
        confidence: float = 0.5,
        evidence: Optional[List[str]] = None,
        depends_on: Optional[Set[str]] = None
    ) -> Belief:
        """
        Create a new belief.
        
        Args:
            belief_type: Type of belief
            statement: What the belief states
            domain: Domain this applies to (game_type or "universal")
            confidence: Initial confidence level
            evidence: Supporting evidence
            depends_on: Set of belief_ids this depends on
            
        Returns:
            Created Belief
            
        Raises:
            ValueError: If depends_on contains invalid belief_id
        """
        belief_id = self._generate_belief_id(statement, domain)
        
        # Verify dependencies exist and are valid
        depends_on = depends_on or set()
        for dep_id in depends_on:
            dep = self._get_belief(dep_id)
            if not dep:
                raise ValueError(f"[BELIEF] Dependency {dep_id} does not exist")
            if not dep.is_valid:
                raise ValueError(f"[BELIEF] Dependency {dep_id} is not valid")
        
        belief = Belief(
            belief_id=belief_id,
            belief_type=belief_type,
            status=BeliefStatus.ACTIVE,
            statement=statement,
            domain=domain,
            evidence=evidence or [],
            confidence=confidence,
            depends_on=depends_on,
            created_at=datetime.now().isoformat()
        )
        
        # Update dependency graph
        for dep_id in depends_on:
            dep = self._get_belief(dep_id)
            if dep:
                dep.depended_by.add(belief_id)
                self._save_belief(dep)
        
        self._beliefs[belief_id] = belief
        self._save_belief(belief)
        
        logger.info(
            f"[BELIEF] Created {belief_type.value}: '{statement}' "
            f"(domain={domain}, conf={confidence:.2f}, deps={len(depends_on)})"
        )
        
        return belief
    
    def invalidate_belief(
        self,
        belief_id: str,
        reason: str,
        cascade: bool = True
    ) -> InvalidationEvent:
        """
        Invalidate a belief and optionally cascade to dependents.
        
        Args:
            belief_id: Belief to invalidate
            reason: Why it's being invalidated
            cascade: Whether to cascade to dependents
            
        Returns:
            InvalidationEvent with details
            
        Raises:
            ValueError: If belief not found
        """
        belief = self._get_belief(belief_id)
        if not belief:
            raise ValueError(f"[BELIEF] Belief {belief_id} not found")
        
        if not belief.is_valid:
            logger.warning(f"[BELIEF] Belief {belief_id} already invalidated")
            return InvalidationEvent(
                event_id=f"already_{belief_id}",
                source_belief_id=belief_id,
                invalidation_reason="Already invalidated",
                cascade_count=0,
                invalidated_beliefs=[],
                timestamp=datetime.now().isoformat()
            )
        
        # Track all invalidated beliefs
        invalidated = []
        
        # Invalidate this belief
        belief.status = BeliefStatus.INVALIDATED
        belief.invalidated_at = datetime.now().isoformat()
        belief.invalidation_reason = reason
        self._save_belief(belief)
        invalidated.append(belief_id)
        
        # Cascade to dependents
        if cascade and belief.depended_by:
            cascade_reason = f"Dependency {belief_id} invalidated: {reason}"
            for dep_id in list(belief.depended_by):
                cascade_event = self.invalidate_belief(dep_id, cascade_reason, cascade=True)
                invalidated.extend(cascade_event.invalidated_beliefs)
        
        # Record event
        event = InvalidationEvent(
            event_id=f"inv_{belief_id}_{datetime.now().strftime('%H%M%S%f')}",
            source_belief_id=belief_id,
            invalidation_reason=reason,
            cascade_count=len(invalidated) - 1,  # Exclude source
            invalidated_beliefs=invalidated,
            timestamp=datetime.now().isoformat()
        )
        
        self._save_invalidation_event(event)
        
        logger.warning(
            f"[BELIEF] Invalidated {belief_id}: {reason} "
            f"(cascaded to {event.cascade_count} dependents)"
        )
        
        return event
    
    def add_evidence(
        self,
        belief_id: str,
        evidence: str,
        supports: bool = True
    ) -> Optional[Belief]:
        """
        Add evidence for or against a belief.
        
        Args:
            belief_id: Belief to update
            evidence: Evidence description
            supports: True if evidence supports the belief
            
        Returns:
            Updated belief or None if not found
        """
        belief = self._get_belief(belief_id)
        if not belief:
            logger.warning(f"[BELIEF] Cannot add evidence - belief {belief_id} not found")
            return None
        
        if not belief.is_valid:
            logger.warning(f"[BELIEF] Cannot add evidence - belief {belief_id} is invalidated")
            return None
        
        belief.add_evidence(evidence, supports)
        self._save_belief(belief)
        
        # Check for auto-invalidation
        if belief.contradicting_observations > belief.supporting_observations * 2:
            if belief.confidence < 0.2:
                logger.warning(f"[BELIEF] Auto-invalidating {belief_id} due to contradicting evidence")
                self.invalidate_belief(belief_id, "Too much contradicting evidence")
        
        return belief
    
    def get_belief(self, belief_id: str) -> Optional[Belief]:
        """
        Get a specific belief.
        
        Args:
            belief_id: Belief identifier
            
        Returns:
            Belief or None
        """
        return self._get_belief(belief_id)
    
    def get_beliefs(
        self,
        domain: Optional[str] = None,
        belief_type: Optional[BeliefType] = None,
        only_valid: bool = True,
        min_confidence: float = 0.0
    ) -> List[Belief]:
        """
        Query beliefs with filters.
        
        Args:
            domain: Filter by domain (game_type)
            belief_type: Filter by type
            only_valid: Only return valid beliefs
            min_confidence: Minimum confidence
            
        Returns:
            List of matching beliefs
        """
        query = "SELECT * FROM beliefs WHERE 1=1"
        params = []
        
        if only_valid:
            query += " AND status = ?"
            params.append(BeliefStatus.ACTIVE.value)
        
        if domain:
            query += " AND domain = ?"
            params.append(domain)
        
        if belief_type:
            query += " AND belief_type = ?"
            params.append(belief_type.value)
        
        query += " AND confidence >= ?"
        params.append(min_confidence)
        
        query += " ORDER BY confidence DESC"
        
        try:
            rows = self.db.execute_query(query, tuple(params))
            
            beliefs = []
            for row in rows:
                belief = self._row_to_belief(row)
                if belief:
                    beliefs.append(belief)
            
            return beliefs
            
        except Exception as e:
            logger.error(f"[BELIEF] Query failed: {e}")
            return []
    
    def find_related_beliefs(
        self,
        belief_id: str,
        include_dependencies: bool = True,
        include_dependents: bool = True
    ) -> Dict[str, List[Belief]]:
        """
        Find beliefs related to a given belief.
        
        Args:
            belief_id: Central belief
            include_dependencies: Include beliefs this depends on
            include_dependents: Include beliefs that depend on this
            
        Returns:
            Dict with 'dependencies' and 'dependents' lists
        """
        belief = self._get_belief(belief_id)
        if not belief:
            return {'dependencies': [], 'dependents': []}
        
        result = {'dependencies': [], 'dependents': []}
        
        if include_dependencies:
            for dep_id in belief.depends_on:
                dep = self._get_belief(dep_id)
                if dep:
                    result['dependencies'].append(dep)
        
        if include_dependents:
            for dep_id in belief.depended_by:
                dep = self._get_belief(dep_id)
                if dep:
                    result['dependents'].append(dep)
        
        return result
    
    def get_belief_chain(self, belief_id: str) -> List[Belief]:
        """
        Get full dependency chain for a belief (all the way to axioms).
        
        Args:
            belief_id: Belief to trace
            
        Returns:
            List of beliefs from axioms to this belief
        """
        belief = self._get_belief(belief_id)
        if not belief:
            return []
        
        visited = set()
        chain = []
        
        def trace(b_id: str):
            if b_id in visited:
                return
            visited.add(b_id)
            
            b = self._get_belief(b_id)
            if not b:
                return
            
            # First trace dependencies
            for dep_id in b.depends_on:
                trace(dep_id)
            
            chain.append(b)
        
        trace(belief_id)
        return chain
    
    def propagate_confidence(self, belief_id: str) -> float:
        """
        Recalculate belief confidence based on dependencies.
        
        Args:
            belief_id: Belief to recalculate
            
        Returns:
            New confidence value
        """
        belief = self._get_belief(belief_id)
        if not belief:
            return 0.0
        
        if not belief.depends_on:
            # No dependencies - confidence is intrinsic
            return belief.confidence
        
        # Average confidence of dependencies affects this belief
        dep_confidences = []
        for dep_id in belief.depends_on:
            dep = self._get_belief(dep_id)
            if dep and dep.is_valid:
                dep_confidences.append(dep.confidence)
            else:
                # Invalid dependency = 0 confidence
                dep_confidences.append(0.0)
        
        if not dep_confidences:
            return belief.confidence
        
        # New confidence is minimum of self and dependency average
        dep_avg = sum(dep_confidences) / len(dep_confidences)
        new_confidence = min(belief.confidence, dep_avg)
        
        if new_confidence != belief.confidence:
            belief.confidence = new_confidence
            self._save_belief(belief)
            logger.debug(f"[BELIEF] Propagated confidence for {belief_id}: {new_confidence:.2f}")
        
        return new_confidence
    
    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================
    
    def _get_belief(self, belief_id: str) -> Optional[Belief]:
        """Get belief from cache or database."""
        if belief_id in self._beliefs:
            return self._beliefs[belief_id]
        
        belief = self._load_belief(belief_id)
        if belief:
            self._beliefs[belief_id] = belief
        return belief
    
    def _load_belief(self, belief_id: str) -> Optional[Belief]:
        """Load belief from database."""
        try:
            rows = self.db.execute_query("""
                SELECT * FROM beliefs WHERE belief_id = ?
            """, (belief_id,))
            
            if rows:
                return self._row_to_belief(rows[0])
            return None
            
        except Exception as e:
            logger.warning(f"[BELIEF] Failed to load belief {belief_id}: {e}")
            return None
    
    def _row_to_belief(self, row: Dict[str, Any]) -> Optional[Belief]:
        """Convert database row to Belief."""
        try:
            return Belief(
                belief_id=row['belief_id'],
                belief_type=BeliefType(row['belief_type']),
                status=BeliefStatus(row['status']),
                statement=row['statement'],
                domain=row['domain'],
                evidence=json.loads(row.get('evidence_json') or '[]'),
                confidence=row.get('confidence', 0.5),
                supporting_observations=row.get('supporting_observations', 0),
                contradicting_observations=row.get('contradicting_observations', 0),
                depends_on=set(json.loads(row.get('depends_on_json') or '[]')),
                depended_by=set(json.loads(row.get('depended_by_json') or '[]')),
                created_at=row.get('created_at', ''),
                invalidated_at=row.get('invalidated_at', ''),
                invalidation_reason=row.get('invalidation_reason', '')
            )
        except Exception as e:
            logger.warning(f"[BELIEF] Failed to parse belief row: {e}")
            return None
    
    def _save_belief(self, belief: Belief) -> None:
        """Save belief to database."""
        try:
            self.db.execute_query("""
                INSERT INTO beliefs
                (belief_id, belief_type, status, statement, domain, evidence_json,
                 confidence, supporting_observations, contradicting_observations,
                 depends_on_json, depended_by_json, created_at, invalidated_at,
                 invalidation_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(belief_id) DO UPDATE SET
                    status = excluded.status,
                    evidence_json = excluded.evidence_json,
                    confidence = excluded.confidence,
                    supporting_observations = excluded.supporting_observations,
                    contradicting_observations = excluded.contradicting_observations,
                    depended_by_json = excluded.depended_by_json,
                    invalidated_at = excluded.invalidated_at,
                    invalidation_reason = excluded.invalidation_reason
            """, (
                belief.belief_id,
                belief.belief_type.value,
                belief.status.value,
                belief.statement,
                belief.domain,
                json.dumps(belief.evidence[-50:]),  # Keep last 50 evidence
                belief.confidence,
                belief.supporting_observations,
                belief.contradicting_observations,
                json.dumps(list(belief.depends_on)),
                json.dumps(list(belief.depended_by)),
                belief.created_at,
                belief.invalidated_at,
                belief.invalidation_reason
            ))
        except Exception as e:
            logger.error(f"[BELIEF] Failed to save belief: {e}")
    
    def _save_invalidation_event(self, event: InvalidationEvent) -> None:
        """Save invalidation event to database."""
        try:
            self.db.execute_query("""
                INSERT INTO belief_invalidation_events
                (event_id, source_belief_id, invalidation_reason,
                 cascade_count, invalidated_beliefs_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                event.event_id,
                event.source_belief_id,
                event.invalidation_reason,
                event.cascade_count,
                json.dumps(event.invalidated_beliefs),
                event.timestamp
            ))
        except Exception as e:
            logger.error(f"[BELIEF] Failed to save invalidation event: {e}")
    
    def _generate_belief_id(self, statement: str, domain: str) -> str:
        """Generate unique belief ID."""
        content_hash = hash(statement + domain)
        timestamp = datetime.now().strftime('%H%M%S')
        return f"belief_{domain[:4]}_{timestamp}_{abs(content_hash) % 10000:04d}"
