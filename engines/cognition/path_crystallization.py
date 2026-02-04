"""
Path Crystallization - Phase 7.3.

Detects when paths have been traversed enough times to become
direct lookups instead of searches. This is a key optimization:
proven reliable paths skip expensive graph searches.

From Part 4: A path that succeeds 15 times in a row for physics
puzzles becomes a "crystallized path" - we skip search and just
execute it directly.

Domain-Relative Thresholds (from Part 5):
- For rare game types (< 20 games), threshold = min(10, 50% of games)
- This prevents premature crystallization in sparse domains

Usage:
    crystallizer = PathCrystallizer()

    # Record successful paths
    crystallizer.record_successful_path(
        domain="physics_puzzle",
        path=["survey", "control_tracker", "physics_probe", "action_selection"],
        confidence=0.92,
        ticks=8
    )

    # Later, check for crystallized path
    path = crystallizer.get_crystallized_path("physics_puzzle")
    if path:
        # Skip search, use crystallized path directly
        execute_path(path)
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class CrystallizedPath:
    """
    A path proven reliable enough to skip search.

    Once a path is crystallized, we can use it directly without
    running expensive graph search algorithms.
    """
    domain_signature: str        # e.g., "physics_puzzle", "symbolic_grid"
    path: List[str]              # Ordered list of rung names
    traversal_count: int = 0     # How many times this exact path succeeded
    success_count: int = 0       # Successful completions
    failure_count: int = 0       # Failed attempts after crystallization
    avg_confidence: float = 0.0  # Average final confidence
    avg_ticks: int = 0           # Average ticks to resolution
    min_ticks: int = 999         # Best (minimum) ticks achieved
    max_confidence: float = 0.0  # Best (maximum) confidence achieved
    created_at: str = ""         # When first recorded
    last_used: str = ""          # Last successful use

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.last_used:
            self.last_used = self.created_at

    @property
    def path_id(self) -> str:
        """Unique identifier for this path."""
        return "->".join(self.path)

    @property
    def success_rate(self) -> float:
        """Success rate of this path."""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return self.success_count / total

    def is_reliable(self, domain_game_count: int = 100) -> bool:
        """
        Is this path reliable enough to use as a lookup?

        Part 5 refinement: Use domain-relative threshold for rare game types.
        Threshold = min(10, 50% of domain games)

        Args:
            domain_game_count: Number of games played in this domain

        Returns:
            True if path is reliable enough to crystallize
        """
        # Domain-relative threshold (Part 5)
        threshold = min(10, max(3, domain_game_count // 2))

        return (
            self.traversal_count >= threshold and
            self.avg_confidence > 0.85 and
            self.avg_ticks < 15 and
            self.success_rate > 0.9  # Added: high success rate requirement
        )

    def update_stats(self, confidence: float, ticks: int, success: bool = True):
        """Update statistics with a new traversal."""
        self.traversal_count += 1
        self.last_used = datetime.now().isoformat()

        if success:
            self.success_count += 1
            # Update running averages
            n = self.success_count
            self.avg_confidence = ((self.avg_confidence * (n - 1)) + confidence) / n
            self.avg_ticks = int(((self.avg_ticks * (n - 1)) + ticks) / n)

            # Track bests
            self.min_ticks = min(self.min_ticks, ticks)
            self.max_confidence = max(self.max_confidence, confidence)
        else:
            self.failure_count += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'domain_signature': self.domain_signature,
            'path': self.path,
            'traversal_count': self.traversal_count,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'avg_confidence': self.avg_confidence,
            'avg_ticks': self.avg_ticks,
            'min_ticks': self.min_ticks,
            'max_confidence': self.max_confidence,
            'created_at': self.created_at,
            'last_used': self.last_used,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CrystallizedPath':
        """Create from dictionary."""
        return cls(
            domain_signature=data['domain_signature'],
            path=data['path'],
            traversal_count=data.get('traversal_count', 0),
            success_count=data.get('success_count', 0),
            failure_count=data.get('failure_count', 0),
            avg_confidence=data.get('avg_confidence', 0.0),
            avg_ticks=data.get('avg_ticks', 0),
            min_ticks=data.get('min_ticks', 999),
            max_confidence=data.get('max_confidence', 0.0),
            created_at=data.get('created_at', ''),
            last_used=data.get('last_used', ''),
        )


@dataclass
class DomainStats:
    """Statistics for a domain."""
    domain: str
    total_games: int = 0
    successful_games: int = 0
    total_paths_tried: int = 0
    crystallized_path_count: int = 0

    @property
    def success_rate(self) -> float:
        if self.total_games == 0:
            return 0.0
        return self.successful_games / self.total_games


# =============================================================================
# PATH CRYSTALLIZER
# =============================================================================

class PathCrystallizer:
    """
    Detects and stores crystallized paths.

    A crystallized path is one that has been traversed enough times
    with consistent success to be used directly without search.
    """

    def __init__(self, db_interface: Optional[Any] = None):
        """Initialize path crystallizer."""
        self.db = db_interface

        # Domain -> list of crystallized paths
        self.path_history: Dict[str, List[CrystallizedPath]] = defaultdict(list)

        # Domain statistics
        self.domain_stats: Dict[str, DomainStats] = {}

        # Cache for fast lookups
        self._crystallized_cache: Dict[str, CrystallizedPath] = {}

        # Load from database if available
        if self.db:
            self._load_from_db()

        logger.info("[PATH-CRYSTAL] PathCrystallizer initialized")

    # -------------------------------------------------------------------------
    # PATH RECORDING
    # -------------------------------------------------------------------------

    def record_successful_path(
        self,
        domain: str,
        path: List[str],
        confidence: float,
        ticks: int
    ) -> CrystallizedPath:
        """
        Record a successful path for potential crystallization.

        Args:
            domain: Domain signature (e.g., "physics_puzzle")
            path: List of rung names traversed
            confidence: Final confidence achieved
            ticks: Number of ticks to resolution

        Returns:
            The CrystallizedPath record (new or updated)
        """
        path_key = "->".join(path)

        # Update domain stats
        self._update_domain_stats(domain, success=True)

        # Find or create crystallized path record
        for cp in self.path_history[domain]:
            if cp.path_id == path_key:
                # Update existing
                cp.update_stats(confidence, ticks, success=True)
                self._check_crystallization(cp, domain)

                if self.db:
                    self._save_path(cp)

                logger.debug(
                    f"[PATH-CRYSTAL] Updated path in {domain}: "
                    f"{len(path)} rungs, count={cp.traversal_count}"
                )
                return cp

        # New path
        cp = CrystallizedPath(
            domain_signature=domain,
            path=path,
        )
        cp.update_stats(confidence, ticks, success=True)
        self.path_history[domain].append(cp)

        if self.db:
            self._save_path(cp)

        logger.debug(
            f"[PATH-CRYSTAL] New path in {domain}: {len(path)} rungs"
        )
        return cp

    def record_failed_path(
        self,
        domain: str,
        path: List[str],
        confidence: float,
        ticks: int
    ) -> Optional[CrystallizedPath]:
        """
        Record a failed path attempt.

        This is important for tracking when crystallized paths start failing.
        """
        path_key = "->".join(path)

        # Update domain stats
        self._update_domain_stats(domain, success=False)

        # Find existing path
        for cp in self.path_history[domain]:
            if cp.path_id == path_key:
                cp.update_stats(confidence, ticks, success=False)

                # Check if path should be de-crystallized
                self._check_decrystallization(cp, domain)

                if self.db:
                    self._save_path(cp)

                return cp

        # Don't create new records for failed paths
        return None

    def _update_domain_stats(self, domain: str, success: bool):
        """Update domain statistics."""
        if domain not in self.domain_stats:
            self.domain_stats[domain] = DomainStats(domain=domain)

        stats = self.domain_stats[domain]
        stats.total_games += 1
        if success:
            stats.successful_games += 1

    def _check_crystallization(self, cp: CrystallizedPath, domain: str):
        """Check if path should be crystallized."""
        domain_games = self.domain_stats.get(domain, DomainStats(domain)).total_games

        if cp.is_reliable(domain_games):
            cache_key = f"{domain}:{cp.path_id}"
            if cache_key not in self._crystallized_cache:
                self._crystallized_cache[cache_key] = cp
                self.domain_stats[domain].crystallized_path_count += 1
                logger.info(
                    f"[PATH-CRYSTAL] Path crystallized in {domain}: "
                    f"{cp.path_id} (count={cp.traversal_count})"
                )

    def _check_decrystallization(self, cp: CrystallizedPath, domain: str):
        """Check if path should be de-crystallized due to failures."""
        cache_key = f"{domain}:{cp.path_id}"

        if cache_key in self._crystallized_cache:
            # If success rate drops below threshold, de-crystallize
            if cp.success_rate < 0.7:
                del self._crystallized_cache[cache_key]
                self.domain_stats[domain].crystallized_path_count -= 1
                logger.warning(
                    f"[PATH-CRYSTAL] Path de-crystallized in {domain}: "
                    f"{cp.path_id} (success_rate={cp.success_rate:.2f})"
                )

    # -------------------------------------------------------------------------
    # PATH RETRIEVAL
    # -------------------------------------------------------------------------

    def get_crystallized_path(
        self,
        domain: str,
        domain_game_count: Optional[int] = None
    ) -> Optional[List[str]]:
        """
        Get a crystallized path for domain if one exists.

        Args:
            domain: Domain signature
            domain_game_count: Override for domain game count

        Returns:
            List of rung names, or None if no reliable path exists
        """
        if domain_game_count is None:
            domain_game_count = self.domain_stats.get(
                domain, DomainStats(domain)
            ).total_games

        # Check cache first
        for key, cp in self._crystallized_cache.items():
            if key.startswith(f"{domain}:") and cp.is_reliable(domain_game_count):
                return cp.path

        # Check all paths for domain
        candidates = [
            cp for cp in self.path_history.get(domain, [])
            if cp.is_reliable(domain_game_count)
        ]

        if not candidates:
            return None

        # Return most reliable (highest success count * confidence)
        best = max(
            candidates,
            key=lambda cp: cp.success_count * cp.avg_confidence
        )
        return best.path

    def get_all_crystallized_paths(self, domain: str) -> List[CrystallizedPath]:
        """Get all crystallized paths for a domain."""
        domain_games = self.domain_stats.get(domain, DomainStats(domain)).total_games
        return [
            cp for cp in self.path_history.get(domain, [])
            if cp.is_reliable(domain_games)
        ]

    def get_path_candidates(
        self,
        domain: str,
        min_traversals: int = 3
    ) -> List[CrystallizedPath]:
        """Get path candidates (not yet crystallized but promising)."""
        return [
            cp for cp in self.path_history.get(domain, [])
            if cp.traversal_count >= min_traversals and not cp.is_reliable()
        ]

    # -------------------------------------------------------------------------
    # STATISTICS
    # -------------------------------------------------------------------------

    def get_statistics(self) -> Dict[str, Any]:
        """Get crystallizer statistics."""
        total_paths = sum(len(paths) for paths in self.path_history.values())
        total_crystallized = len(self._crystallized_cache)

        return {
            'total_domains': len(self.path_history),
            'total_paths': total_paths,
            'total_crystallized': total_crystallized,
            'crystallization_rate': (
                total_crystallized / total_paths if total_paths > 0 else 0
            ),
            'domain_stats': {
                domain: {
                    'total_games': stats.total_games,
                    'success_rate': stats.success_rate,
                    'paths_tried': len(self.path_history.get(domain, [])),
                    'crystallized': stats.crystallized_path_count,
                }
                for domain, stats in self.domain_stats.items()
            },
        }

    def get_domain_report(self, domain: str) -> Dict[str, Any]:
        """Get detailed report for a domain."""
        stats = self.domain_stats.get(domain, DomainStats(domain))
        paths = self.path_history.get(domain, [])
        domain_games = stats.total_games

        crystallized = [cp for cp in paths if cp.is_reliable(domain_games)]
        candidates = [
            cp for cp in paths
            if cp.traversal_count >= 3 and not cp.is_reliable(domain_games)
        ]

        return {
            'domain': domain,
            'total_games': stats.total_games,
            'success_rate': stats.success_rate,
            'total_paths': len(paths),
            'crystallized_count': len(crystallized),
            'candidate_count': len(candidates),
            'crystallized_paths': [
                {
                    'path': cp.path,
                    'traversals': cp.traversal_count,
                    'avg_confidence': cp.avg_confidence,
                    'avg_ticks': cp.avg_ticks,
                }
                for cp in crystallized
            ],
            'candidates': [
                {
                    'path': cp.path,
                    'traversals': cp.traversal_count,
                    'avg_confidence': cp.avg_confidence,
                    'needs': self._calculate_needed_traversals(cp, domain_games),
                }
                for cp in candidates
            ],
        }

    def _calculate_needed_traversals(
        self,
        cp: CrystallizedPath,
        domain_games: int
    ) -> int:
        """Calculate how many more traversals needed for crystallization."""
        threshold = min(10, max(3, domain_games // 2))

        if cp.avg_confidence <= 0.85:
            return -1  # Confidence too low, won't crystallize
        if cp.avg_ticks >= 15:
            return -1  # Too slow, won't crystallize

        return max(0, threshold - cp.traversal_count)

    # -------------------------------------------------------------------------
    # DATABASE PERSISTENCE
    # -------------------------------------------------------------------------

    def _load_from_db(self):
        """Load paths from database."""
        if not self.db:
            return

        try:
            rows = self.db.execute("""
                SELECT domain, path_data
                FROM crystallized_paths
            """).fetchall()

            for row in rows:
                domain = row[0]
                data = json.loads(row[1])
                cp = CrystallizedPath.from_dict(data)
                self.path_history[domain].append(cp)

                # Check if already crystallized
                if cp.is_reliable():
                    cache_key = f"{domain}:{cp.path_id}"
                    self._crystallized_cache[cache_key] = cp

            logger.info(f"[PATH-CRYSTAL] Loaded {len(rows)} paths from database")
        except Exception as e:
            logger.warning(f"[PATH-CRYSTAL] Failed to load from DB: {e}")

    def _save_path(self, cp: CrystallizedPath):
        """Save path to database."""
        if not self.db:
            return

        try:
            self.db.execute("""
                INSERT OR REPLACE INTO crystallized_paths
                (domain, path_id, path_data)
                VALUES (?, ?, ?)
            """, (
                cp.domain_signature,
                cp.path_id,
                json.dumps(cp.to_dict()),
            ))
        except Exception as e:
            logger.error(f"[PATH-CRYSTAL] Failed to save path: {e}")


# =============================================================================
# DATABASE SCHEMA
# =============================================================================

CRYSTALLIZED_PATHS_SCHEMA = """
CREATE TABLE IF NOT EXISTS crystallized_paths (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain TEXT NOT NULL,
    path_id TEXT NOT NULL,
    path_data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(domain, path_id)
);

CREATE INDEX IF NOT EXISTS idx_crystallized_domain ON crystallized_paths(domain);
"""
