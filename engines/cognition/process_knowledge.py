"""
Process Knowledge Extraction - Phase 7.4.

Extracts abstract patterns from successful concrete paths. Instead of
memorizing "survey -> control_tracker -> event_understanding", we
extract the pattern "ENTRY -> LEVERAGE -> COMPOUNDING" and can
instantiate it for new domains.

From Part 4: Process knowledge enables transfer learning. A pattern
that works for physics puzzles might also work for symbolic grids
when properly instantiated.

Domain-Specific Patterns (from Part 5):
- Track pattern success rates per domain, not just globally
- Different domains may need different patterns
- E.g., spatial puzzles might skip COMPOUNDING and go ENTRY->LEVERAGE->RESOLUTION

Usage:
    extractor = ProcessKnowledgeExtractor()

    # Record successful paths (extracts patterns automatically)
    extractor.record_success("physics_puzzle", ["survey", "physics_probe", "action_selection"])
    extractor.record_success("symbolic_grid", ["pattern_recognition", "rule_transfer", "optimal_sequence"])

    # Suggest path for new domain
    suggested = extractor.suggest_path_for_new_domain(
        "new_game_type",
        available_rungs={"survey": RungRole.ENTRY, "physics_probe": RungRole.LEVERAGE, ...}
    )
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from engines.cognition.rung_roles import (
    RUNG_ROLE_MAP,
    RungRole,
    extract_role_sequence,
    role_sequence_to_id,
)

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class AbstractPattern:
    """
    Abstract pattern extracted from concrete paths.

    Instead of: "survey -> control_tracker -> event_understanding"
    We extract: "ENTRY -> LEVERAGE -> COMPOUNDING" with domain mappings
    """
    pattern_id: str                              # e.g., "ENTRY->LEVERAGE->COMPOUNDING"
    role_sequence: List[RungRole]                # Abstract: [ENTRY, LEVERAGE, COMPOUNDING]
    domain_instantiations: Dict[str, List[str]] = field(default_factory=dict)  # domain -> concrete rungs
    success_count: int = 0                       # Total successful uses
    failure_count: int = 0                       # Total failed uses
    created_at: str = ""                         # When first seen
    last_used: str = ""                          # Last successful use

    # Domain-specific success tracking (Part 5)
    domain_success_counts: Dict[str, int] = field(default_factory=dict)
    domain_failure_counts: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.last_used:
            self.last_used = self.created_at

    @property
    def success_rate(self) -> float:
        """Overall success rate."""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return self.success_count / total

    def get_domain_success_rate(self, domain: str) -> float:
        """Get success rate for a specific domain."""
        successes = self.domain_success_counts.get(domain, 0)
        failures = self.domain_failure_counts.get(domain, 0)
        total = successes + failures
        if total == 0:
            return 0.0
        return successes / total

    def instantiate_for_domain(self, domain: str) -> Optional[List[str]]:
        """Get concrete rung sequence for a domain, or None if unknown."""
        return self.domain_instantiations.get(domain)

    def add_instantiation(
        self,
        domain: str,
        concrete_path: List[str],
        success: bool = True
    ):
        """Record a new domain instantiation of this pattern."""
        self.domain_instantiations[domain] = concrete_path
        self.last_used = datetime.now().isoformat()

        if success:
            self.success_count += 1
            self.domain_success_counts[domain] = self.domain_success_counts.get(domain, 0) + 1
        else:
            self.failure_count += 1
            self.domain_failure_counts[domain] = self.domain_failure_counts.get(domain, 0) + 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'pattern_id': self.pattern_id,
            'role_sequence': [r.name for r in self.role_sequence],
            'domain_instantiations': self.domain_instantiations,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'created_at': self.created_at,
            'last_used': self.last_used,
            'domain_success_counts': self.domain_success_counts,
            'domain_failure_counts': self.domain_failure_counts,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AbstractPattern':
        """Create from dictionary."""
        return cls(
            pattern_id=data['pattern_id'],
            role_sequence=[RungRole[r] for r in data['role_sequence']],
            domain_instantiations=data.get('domain_instantiations', {}),
            success_count=data.get('success_count', 0),
            failure_count=data.get('failure_count', 0),
            created_at=data.get('created_at', ''),
            last_used=data.get('last_used', ''),
            domain_success_counts=data.get('domain_success_counts', {}),
            domain_failure_counts=data.get('domain_failure_counts', {}),
        )


@dataclass
class PatternMatch:
    """Result of matching a pattern to available rungs."""
    pattern: AbstractPattern
    instantiated_path: List[str]
    confidence: float                 # How well this matches
    domain_specific: bool             # Is this a domain-specific instantiation?
    missing_roles: List[RungRole]     # Roles we couldn't fill


# =============================================================================
# PROCESS KNOWLEDGE EXTRACTOR
# =============================================================================

class ProcessKnowledgeExtractor:
    """
    Extracts abstract patterns from successful concrete paths.

    This enables transfer learning between domains by identifying
    common problem-solving patterns at the role level.
    """

    def __init__(self, db_interface: Optional[Any] = None):
        """Initialize process knowledge extractor."""
        self.db = db_interface

        # Pattern storage
        self.patterns: Dict[str, AbstractPattern] = {}

        # Domain -> pattern_id -> success_rate cache
        self._domain_pattern_cache: Dict[str, Dict[str, float]] = defaultdict(dict)

        # Statistics
        self._total_paths_recorded = 0
        self._unique_patterns_found = 0

        # Load from database if available
        if self.db:
            self._load_from_db()

        logger.info("[PROCESS-KNOWLEDGE] ProcessKnowledgeExtractor initialized")

    # -------------------------------------------------------------------------
    # PATTERN EXTRACTION
    # -------------------------------------------------------------------------

    def extract_pattern(self, path: List[str]) -> str:
        """
        Extract abstract role pattern from concrete path.

        Args:
            path: List of rung names

        Returns:
            Pattern ID string (e.g., "ENTRY->LEVERAGE->RESOLUTION")
        """
        role_sequence = extract_role_sequence(path)
        pattern_id = role_sequence_to_id(role_sequence)
        return pattern_id

    def record_success(self, domain: str, path: List[str]) -> AbstractPattern:
        """
        Record a successful path, extracting its abstract pattern.

        Args:
            domain: Domain signature
            path: List of rung names that succeeded

        Returns:
            The AbstractPattern that was updated/created
        """
        pattern_id = self.extract_pattern(path)
        self._total_paths_recorded += 1

        if pattern_id not in self.patterns:
            role_sequence = extract_role_sequence(path)
            self.patterns[pattern_id] = AbstractPattern(
                pattern_id=pattern_id,
                role_sequence=role_sequence,
            )
            self._unique_patterns_found += 1

        pattern = self.patterns[pattern_id]
        pattern.add_instantiation(domain, path, success=True)

        # Update domain cache
        self._domain_pattern_cache[domain][pattern_id] = pattern.get_domain_success_rate(domain)

        if self.db:
            self._save_pattern(pattern)

        logger.debug(
            f"[PROCESS-KNOWLEDGE] Recorded success: {pattern_id} in {domain}"
        )
        return pattern

    def record_failure(self, domain: str, path: List[str]) -> Optional[AbstractPattern]:
        """
        Record a failed path attempt.

        Args:
            domain: Domain signature
            path: List of rung names that failed

        Returns:
            The AbstractPattern if it exists, None otherwise
        """
        pattern_id = self.extract_pattern(path)

        if pattern_id not in self.patterns:
            # Don't create patterns from failures
            return None

        pattern = self.patterns[pattern_id]
        pattern.add_instantiation(domain, path, success=False)

        # Update domain cache
        self._domain_pattern_cache[domain][pattern_id] = pattern.get_domain_success_rate(domain)

        if self.db:
            self._save_pattern(pattern)

        return pattern

    # -------------------------------------------------------------------------
    # PATH SUGGESTION
    # -------------------------------------------------------------------------

    def suggest_path_for_new_domain(
        self,
        _new_domain: str,
        available_rungs: Dict[str, RungRole]
    ) -> Optional[List[str]]:
        """
        Suggest a path for a new domain based on successful patterns.

        Uses the most successful abstract pattern and instantiates
        it using available rungs.

        Args:
            new_domain: Domain to suggest path for
            available_rungs: Map of rung_name -> RungRole for available rungs

        Returns:
            Suggested path, or None if can't instantiate
        """
        if not self.patterns:
            return None

        # Find most successful pattern overall
        best_pattern = max(
            self.patterns.values(),
            key=lambda p: p.success_count * p.success_rate
        )

        # Try to instantiate for new domain
        return self._instantiate_pattern(best_pattern, available_rungs)

    def get_best_pattern_for_domain(
        self,
        domain: str,
        available_rungs: Optional[Dict[str, RungRole]] = None
    ) -> Optional[List[str]]:
        """
        Get the best pattern for a specific domain.

        Part 5 refinement: Track pattern success per domain.
        Different domains may need different patterns.

        Args:
            domain: Domain to get pattern for
            available_rungs: Optional override for available rungs

        Returns:
            Best path for this domain, or None
        """
        if available_rungs is None:
            available_rungs = RUNG_ROLE_MAP

        # Check for domain-specific data
        domain_patterns = self._domain_pattern_cache.get(domain, {})

        if not domain_patterns:
            # No domain-specific data, fall back to universal best
            return self.suggest_path_for_new_domain(domain, available_rungs)

        # Use best pattern FOR THIS DOMAIN
        best_pattern_id = max(
            domain_patterns.items(),
            key=lambda x: x[1]  # Sort by success rate
        )[0]

        pattern = self.patterns.get(best_pattern_id)
        if not pattern:
            return None

        # Return domain-specific instantiation if exists
        domain_path = pattern.instantiate_for_domain(domain)
        if domain_path:
            return domain_path

        # Otherwise try to instantiate from pattern
        return self._instantiate_pattern(pattern, available_rungs)

    def _instantiate_pattern(
        self,
        pattern: AbstractPattern,
        available_rungs: Dict[str, RungRole]
    ) -> Optional[List[str]]:
        """
        Try to instantiate a pattern using available rungs.

        Args:
            pattern: Pattern to instantiate
            available_rungs: Map of available rungs

        Returns:
            Instantiated path, or None if can't fill all roles
        """
        suggested_path = []

        # Group available rungs by role
        rungs_by_role: Dict[RungRole, List[str]] = defaultdict(list)
        for rung, role in available_rungs.items():
            rungs_by_role[role].append(rung)

        for role in pattern.role_sequence:
            candidates = rungs_by_role.get(role, [])
            if candidates:
                # Take first match (could be smarter about selection)
                suggested_path.append(candidates[0])
            else:
                return None  # Can't instantiate this pattern

        return suggested_path

    def find_matching_patterns(
        self,
        available_rungs: Dict[str, RungRole],
        min_success_rate: float = 0.5
    ) -> List[PatternMatch]:
        """
        Find all patterns that can be instantiated with available rungs.

        Args:
            available_rungs: Map of available rungs
            min_success_rate: Minimum success rate to include

        Returns:
            List of PatternMatch objects, sorted by confidence
        """
        matches = []

        # Group available rungs by role
        rungs_by_role: Dict[RungRole, List[str]] = defaultdict(list)
        for rung, role in available_rungs.items():
            rungs_by_role[role].append(rung)

        for pattern in self.patterns.values():
            if pattern.success_rate < min_success_rate:
                continue

            # Try to instantiate
            path = []
            missing_roles = []

            for role in pattern.role_sequence:
                candidates = rungs_by_role.get(role, [])
                if candidates:
                    path.append(candidates[0])
                else:
                    missing_roles.append(role)

            if not missing_roles:
                matches.append(PatternMatch(
                    pattern=pattern,
                    instantiated_path=path,
                    confidence=pattern.success_rate,
                    domain_specific=False,
                    missing_roles=[],
                ))

        # Sort by confidence
        matches.sort(key=lambda m: m.confidence, reverse=True)
        return matches

    # -------------------------------------------------------------------------
    # PATTERN ANALYSIS
    # -------------------------------------------------------------------------

    def get_common_patterns(self, min_occurrences: int = 3) -> List[AbstractPattern]:
        """Get patterns that appear frequently across domains."""
        return [
            p for p in self.patterns.values()
            if p.success_count >= min_occurrences
        ]

    def get_domain_patterns(self, domain: str) -> List[Tuple[AbstractPattern, float]]:
        """
        Get patterns used in a domain, sorted by success rate.

        Returns:
            List of (pattern, domain_success_rate) tuples
        """
        results = []

        for pattern_id, success_rate in self._domain_pattern_cache.get(domain, {}).items():
            pattern = self.patterns.get(pattern_id)
            if pattern:
                results.append((pattern, success_rate))

        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def compare_domains(
        self,
        domain1: str,
        domain2: str
    ) -> Dict[str, Any]:
        """
        Compare pattern usage between two domains.

        Useful for understanding domain similarity.
        """
        patterns1 = set(self._domain_pattern_cache.get(domain1, {}).keys())
        patterns2 = set(self._domain_pattern_cache.get(domain2, {}).keys())

        shared = patterns1 & patterns2
        only1 = patterns1 - patterns2
        only2 = patterns2 - patterns1

        # Calculate Jaccard similarity
        union = patterns1 | patterns2
        similarity = len(shared) / len(union) if union else 0.0

        return {
            'domain1': domain1,
            'domain2': domain2,
            'similarity': similarity,
            'shared_patterns': list(shared),
            'only_in_domain1': list(only1),
            'only_in_domain2': list(only2),
        }

    # -------------------------------------------------------------------------
    # STATISTICS
    # -------------------------------------------------------------------------

    def get_statistics(self) -> Dict[str, Any]:
        """Get extractor statistics."""
        if not self.patterns:
            return {
                'total_patterns': 0,
                'total_paths_recorded': self._total_paths_recorded,
                'domains_covered': 0,
                'avg_success_rate': 0.0,
            }

        success_rates = [p.success_rate for p in self.patterns.values()]

        return {
            'total_patterns': len(self.patterns),
            'total_paths_recorded': self._total_paths_recorded,
            'domains_covered': len(self._domain_pattern_cache),
            'avg_success_rate': sum(success_rates) / len(success_rates),
            'most_successful_pattern': max(
                self.patterns.values(),
                key=lambda p: p.success_count
            ).pattern_id if self.patterns else None,
            'pattern_distribution': {
                p.pattern_id: p.success_count
                for p in sorted(
                    self.patterns.values(),
                    key=lambda p: p.success_count,
                    reverse=True
                )[:10]
            },
        }

    def get_pattern_report(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed report for a pattern."""
        pattern = self.patterns.get(pattern_id)
        if not pattern:
            return None

        return {
            'pattern_id': pattern_id,
            'role_sequence': [r.name for r in pattern.role_sequence],
            'success_count': pattern.success_count,
            'failure_count': pattern.failure_count,
            'success_rate': pattern.success_rate,
            'domains_used': list(pattern.domain_instantiations.keys()),
            'domain_success_rates': {
                domain: pattern.get_domain_success_rate(domain)
                for domain in pattern.domain_instantiations.keys()
            },
            'best_domain': max(
                pattern.domain_instantiations.keys(),
                key=lambda d: pattern.get_domain_success_rate(d),
                default=None
            ),
            'instantiations': pattern.domain_instantiations,
        }

    # -------------------------------------------------------------------------
    # DATABASE PERSISTENCE
    # -------------------------------------------------------------------------

    def _load_from_db(self):
        """Load patterns from database."""
        if not self.db:
            return

        try:
            rows = self.db.execute("""
                SELECT pattern_id, pattern_data
                FROM abstract_patterns
            """).fetchall()

            for row in rows:
                pattern_id = row[0]
                data = json.loads(row[1])
                pattern = AbstractPattern.from_dict(data)
                self.patterns[pattern_id] = pattern

                # Rebuild domain cache
                for domain in pattern.domain_instantiations.keys():
                    self._domain_pattern_cache[domain][pattern_id] = \
                        pattern.get_domain_success_rate(domain)

            self._unique_patterns_found = len(self.patterns)
            logger.info(f"[PROCESS-KNOWLEDGE] Loaded {len(rows)} patterns from database")
        except Exception as e:
            logger.warning(f"[PROCESS-KNOWLEDGE] Failed to load from DB: {e}")

    def _save_pattern(self, pattern: AbstractPattern):
        """Save pattern to database."""
        if not self.db:
            return

        try:
            self.db.execute("""
                INSERT OR REPLACE INTO abstract_patterns
                (pattern_id, pattern_data)
                VALUES (?, ?)
            """, (
                pattern.pattern_id,
                json.dumps(pattern.to_dict()),
            ))
        except Exception as e:
            logger.error(f"[PROCESS-KNOWLEDGE] Failed to save pattern: {e}")


# =============================================================================
# DATABASE SCHEMA
# =============================================================================

ABSTRACT_PATTERNS_SCHEMA = """
CREATE TABLE IF NOT EXISTS abstract_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id TEXT UNIQUE NOT NULL,
    pattern_data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_patterns_id ON abstract_patterns(pattern_id);
"""
