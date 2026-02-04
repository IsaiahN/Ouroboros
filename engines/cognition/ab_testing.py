"""
A/B Testing Framework - Phase 5.3.

Manages gradual rollout of cognitive routing:
- Phase 5a: 10% of games use cognitive routing
- Phase 5b: 50% of games (if metrics good)
- Phase 5c: 100% (deprecate ORDERING_PRESETS)

Features:
- Deterministic assignment (same game always gets same variant)
- Metrics-driven promotion/rollback
- Emergency kill switch
- Automatic variant assignment based on game_id hash

Usage:
    ab = ABTestManager(initial_rollout=0.10)

    # For each game
    if ab.use_cognitive(game_id):
        action = cognitive_router.decide(...)
    else:
        action = static_system.decide(...)

    # Check for promotion
    ab.maybe_promote()
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class RolloutPhase(Enum):
    """Rollout phases for cognitive routing."""
    PHASE_5A = "5a"  # 10% rollout
    PHASE_5B = "5b"  # 50% rollout
    PHASE_5C = "5c"  # 100% rollout (deprecate static)
    KILLED = "killed"  # Emergency rollback


class Variant(Enum):
    """Test variants."""
    STATIC = "static"       # Traditional static ordering
    COGNITIVE = "cognitive"  # New cognitive routing


@dataclass
class PhaseConfig:
    """Configuration for a rollout phase."""
    phase: RolloutPhase
    cognitive_percentage: float
    min_games_before_promotion: int
    required_metrics: Dict[str, float]  # metric_name -> threshold

    @classmethod
    def phase_5a(cls) -> 'PhaseConfig':
        """Phase 5a: 10% rollout, conservative."""
        return cls(
            phase=RolloutPhase.PHASE_5A,
            cognitive_percentage=0.10,
            min_games_before_promotion=100,
            required_metrics={
                'avg_rungs_evaluated': 15.0,      # < 15
                'avg_latency_ms': 50.0,           # < 50ms
                'first_win_rate': 0.60,           # > 60%
                'backtracking_rate': 0.05,        # < 5%
                'divergence_rate': 0.10,          # < 10% divergence from static
            }
        )

    @classmethod
    def phase_5b(cls) -> 'PhaseConfig':
        """Phase 5b: 50% rollout, moderate."""
        return cls(
            phase=RolloutPhase.PHASE_5B,
            cognitive_percentage=0.50,
            min_games_before_promotion=500,
            required_metrics={
                'avg_rungs_evaluated': 15.0,
                'avg_latency_ms': 50.0,
                'first_win_rate': 0.60,
                'backtracking_rate': 0.05,
                'divergence_rate': 0.05,  # Tighter threshold
            }
        )

    @classmethod
    def phase_5c(cls) -> 'PhaseConfig':
        """Phase 5c: 100% rollout, full deployment."""
        return cls(
            phase=RolloutPhase.PHASE_5C,
            cognitive_percentage=1.00,
            min_games_before_promotion=0,  # Final phase
            required_metrics={}  # No promotion needed
        )


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class VariantAssignment:
    """Record of variant assignment for a game."""
    game_id: str
    variant: Variant
    phase: RolloutPhase
    timestamp: str
    hash_value: float


@dataclass
class PhaseMetrics:
    """Metrics collected during a phase."""
    phase: RolloutPhase
    games_played: int
    cognitive_games: int
    static_games: int

    # Cognitive metrics
    cognitive_avg_rungs: float
    cognitive_avg_latency: float
    cognitive_first_win_rate: float
    cognitive_backtrack_rate: float

    # Comparison
    divergence_rate: float
    cognitive_better_count: int
    static_better_count: int

    def meets_thresholds(self, thresholds: Dict[str, float]) -> Tuple[bool, List[str]]:
        """Check if metrics meet thresholds for promotion."""
        issues = []

        if 'avg_rungs_evaluated' in thresholds:
            if self.cognitive_avg_rungs >= thresholds['avg_rungs_evaluated']:
                issues.append(
                    f"Avg rungs {self.cognitive_avg_rungs:.1f} >= {thresholds['avg_rungs_evaluated']}"
                )

        if 'avg_latency_ms' in thresholds:
            if self.cognitive_avg_latency >= thresholds['avg_latency_ms']:
                issues.append(
                    f"Avg latency {self.cognitive_avg_latency:.1f}ms >= {thresholds['avg_latency_ms']}ms"
                )

        if 'first_win_rate' in thresholds:
            if self.cognitive_first_win_rate < thresholds['first_win_rate']:
                issues.append(
                    f"First-win rate {self.cognitive_first_win_rate:.1%} < {thresholds['first_win_rate']:.0%}"
                )

        if 'backtracking_rate' in thresholds:
            if self.cognitive_backtrack_rate >= thresholds['backtracking_rate']:
                issues.append(
                    f"Backtrack rate {self.cognitive_backtrack_rate:.1%} >= {thresholds['backtracking_rate']:.0%}"
                )

        if 'divergence_rate' in thresholds:
            if self.divergence_rate >= thresholds['divergence_rate']:
                issues.append(
                    f"Divergence rate {self.divergence_rate:.1%} >= {thresholds['divergence_rate']:.0%}"
                )

        return len(issues) == 0, issues


# =============================================================================
# A/B TEST MANAGER
# =============================================================================

class ABTestManager:
    """
    Manages A/B testing for cognitive routing rollout.

    Key features:
    - Deterministic assignment based on game_id hash
    - Metrics-driven phase promotion
    - Emergency kill switch
    - Sticky assignments (same game always gets same variant)
    """

    def __init__(
        self,
        initial_phase: RolloutPhase = RolloutPhase.PHASE_5A,
        db_interface: Optional[Any] = None,
        metrics_tracker: Optional[Any] = None,
        shadow_tester: Optional[Any] = None
    ):
        """Initialize A/B test manager."""
        self.db = db_interface
        self.metrics_tracker = metrics_tracker
        self.shadow_tester = shadow_tester

        # Current phase
        self._current_phase = initial_phase
        self._phase_config = self._get_phase_config(initial_phase)

        # Assignment tracking
        self._assignments: Dict[str, VariantAssignment] = {}

        # Phase statistics
        self._games_this_phase = 0
        self._cognitive_games = 0
        self._static_games = 0

        # Metrics accumulators
        self._cognitive_rungs_sum = 0.0
        self._cognitive_latency_sum = 0.0
        self._cognitive_first_wins = 0
        self._cognitive_backtracks = 0
        self._divergences = 0

        # Kill switch
        self._killed = False
        self._kill_reason = ""

        logger.info(f"[AB] A/B test manager initialized at phase {initial_phase.value}")

    def _get_phase_config(self, phase: RolloutPhase) -> PhaseConfig:
        """Get configuration for a phase."""
        if phase == RolloutPhase.PHASE_5A:
            return PhaseConfig.phase_5a()
        elif phase == RolloutPhase.PHASE_5B:
            return PhaseConfig.phase_5b()
        elif phase == RolloutPhase.PHASE_5C:
            return PhaseConfig.phase_5c()
        else:
            return PhaseConfig.phase_5a()

    # -------------------------------------------------------------------------
    # VARIANT ASSIGNMENT
    # -------------------------------------------------------------------------

    def use_cognitive(self, game_id: str) -> bool:
        """
        Determine if a game should use cognitive routing.

        Assignment is deterministic based on game_id hash.
        """
        if self._killed:
            return False

        if self._current_phase == RolloutPhase.PHASE_5C:
            return True  # 100% cognitive

        # Check for existing assignment
        if game_id in self._assignments:
            return self._assignments[game_id].variant == Variant.COGNITIVE

        # Compute deterministic assignment
        hash_value = self._hash_game_id(game_id)
        use_cognitive = hash_value < self._phase_config.cognitive_percentage

        # Store assignment
        variant = Variant.COGNITIVE if use_cognitive else Variant.STATIC
        self._assignments[game_id] = VariantAssignment(
            game_id=game_id,
            variant=variant,
            phase=self._current_phase,
            timestamp=datetime.now().isoformat(),
            hash_value=hash_value,
        )

        return use_cognitive

    def _hash_game_id(self, game_id: str) -> float:
        """Hash game_id to a value between 0 and 1."""
        hash_bytes = hashlib.sha256(game_id.encode()).digest()
        hash_int = int.from_bytes(hash_bytes[:8], 'big')
        return hash_int / (2 ** 64)

    def get_variant(self, game_id: str) -> Variant:
        """Get the variant for a game."""
        if self.use_cognitive(game_id):
            return Variant.COGNITIVE
        return Variant.STATIC

    # -------------------------------------------------------------------------
    # METRICS RECORDING
    # -------------------------------------------------------------------------

    def record_game_result(
        self,
        game_id: str,
        variant: Variant,
        rungs_evaluated: int,
        latency_ms: float,
        first_win: bool,
        backtracked: bool,
        had_divergence: bool = False
    ) -> None:
        """Record result of a game."""
        self._games_this_phase += 1

        if variant == Variant.COGNITIVE:
            self._cognitive_games += 1
            self._cognitive_rungs_sum += rungs_evaluated
            self._cognitive_latency_sum += latency_ms
            if first_win:
                self._cognitive_first_wins += 1
            if backtracked:
                self._cognitive_backtracks += 1
        else:
            self._static_games += 1

        if had_divergence:
            self._divergences += 1

        # Store to database
        if self.db:
            self._store_result(game_id, variant, rungs_evaluated, latency_ms, first_win, backtracked, had_divergence)

    def _store_result(
        self,
        game_id: str,
        variant: Variant,
        rungs_evaluated: int,
        latency_ms: float,
        first_win: bool,
        backtracked: bool,
        had_divergence: bool
    ) -> None:
        """Store result to database."""
        if self.db is None:
            return
        try:
            self.db.execute("""
                INSERT INTO ab_test_results (
                    timestamp, game_id, variant, phase,
                    rungs_evaluated, latency_ms, first_win, backtracked, had_divergence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(), game_id, variant.value, self._current_phase.value,
                rungs_evaluated, latency_ms, int(first_win), int(backtracked), int(had_divergence),
            ))
        except Exception as e:
            logger.error(f"[AB] Failed to store result: {e}")

    # -------------------------------------------------------------------------
    # PHASE MANAGEMENT
    # -------------------------------------------------------------------------

    def get_phase_metrics(self) -> PhaseMetrics:
        """Get metrics for current phase."""
        cognitive_avg_rungs = (
            self._cognitive_rungs_sum / self._cognitive_games
            if self._cognitive_games > 0 else 0
        )
        cognitive_avg_latency = (
            self._cognitive_latency_sum / self._cognitive_games
            if self._cognitive_games > 0 else 0
        )
        cognitive_first_win_rate = (
            self._cognitive_first_wins / self._cognitive_games
            if self._cognitive_games > 0 else 0
        )
        cognitive_backtrack_rate = (
            self._cognitive_backtracks / self._cognitive_games
            if self._cognitive_games > 0 else 0
        )
        divergence_rate = (
            self._divergences / self._games_this_phase
            if self._games_this_phase > 0 else 0
        )

        return PhaseMetrics(
            phase=self._current_phase,
            games_played=self._games_this_phase,
            cognitive_games=self._cognitive_games,
            static_games=self._static_games,
            cognitive_avg_rungs=cognitive_avg_rungs,
            cognitive_avg_latency=cognitive_avg_latency,
            cognitive_first_win_rate=cognitive_first_win_rate,
            cognitive_backtrack_rate=cognitive_backtrack_rate,
            divergence_rate=divergence_rate,
            cognitive_better_count=0,  # Would need per-game comparison
            static_better_count=0,
        )

    def maybe_promote(self) -> Tuple[bool, str]:
        """
        Check if we should promote to next phase.

        Returns:
            Tuple of (promoted, reason)
        """
        if self._killed:
            return False, "System killed"

        if self._current_phase == RolloutPhase.PHASE_5C:
            return False, "Already at final phase"

        # Check minimum games
        if self._games_this_phase < self._phase_config.min_games_before_promotion:
            return False, f"Need {self._phase_config.min_games_before_promotion - self._games_this_phase} more games"

        # Check metrics
        metrics = self.get_phase_metrics()
        meets_thresholds, issues = metrics.meets_thresholds(self._phase_config.required_metrics)

        if not meets_thresholds:
            return False, f"Metrics not met: {'; '.join(issues)}"

        # Promote!
        old_phase = self._current_phase
        if self._current_phase == RolloutPhase.PHASE_5A:
            self._promote_to_phase(RolloutPhase.PHASE_5B)
        elif self._current_phase == RolloutPhase.PHASE_5B:
            self._promote_to_phase(RolloutPhase.PHASE_5C)

        return True, f"Promoted from {old_phase.value} to {self._current_phase.value}"

    def _promote_to_phase(self, new_phase: RolloutPhase) -> None:
        """Promote to a new phase."""
        logger.info(f"[AB] Promoting from {self._current_phase.value} to {new_phase.value}")

        self._current_phase = new_phase
        self._phase_config = self._get_phase_config(new_phase)

        # Reset phase counters
        self._games_this_phase = 0
        self._cognitive_games = 0
        self._static_games = 0
        self._cognitive_rungs_sum = 0.0
        self._cognitive_latency_sum = 0.0
        self._cognitive_first_wins = 0
        self._cognitive_backtracks = 0
        self._divergences = 0

        # Keep assignments for continuity

    def force_promote(self, new_phase: RolloutPhase) -> None:
        """Force promotion to a specific phase (admin override)."""
        logger.warning(f"[AB] Force promoting to {new_phase.value}")
        self._promote_to_phase(new_phase)

    def rollback(self, reason: str = "Manual rollback") -> None:
        """Rollback to previous phase."""
        if self._current_phase == RolloutPhase.PHASE_5A:
            logger.warning("[AB] Already at initial phase, cannot rollback")
            return

        logger.warning(f"[AB] Rolling back from {self._current_phase.value}: {reason}")

        if self._current_phase == RolloutPhase.PHASE_5C:
            self._promote_to_phase(RolloutPhase.PHASE_5B)
        elif self._current_phase == RolloutPhase.PHASE_5B:
            self._promote_to_phase(RolloutPhase.PHASE_5A)

    # -------------------------------------------------------------------------
    # KILL SWITCH
    # -------------------------------------------------------------------------

    def kill(self, reason: str) -> None:
        """Emergency kill switch - disable all cognitive routing."""
        logger.critical(f"[AB] KILL SWITCH ACTIVATED: {reason}")
        self._killed = True
        self._kill_reason = reason
        self._current_phase = RolloutPhase.KILLED

    def resurrect(self, new_phase: RolloutPhase = RolloutPhase.PHASE_5A) -> None:
        """Resurrect after kill (with caution)."""
        logger.warning(f"[AB] Resurrecting to phase {new_phase.value}")
        self._killed = False
        self._kill_reason = ""
        self._promote_to_phase(new_phase)

    @property
    def is_killed(self) -> bool:
        """Check if system is killed."""
        return self._killed

    # -------------------------------------------------------------------------
    # STATUS
    # -------------------------------------------------------------------------

    def get_status(self) -> Dict[str, Any]:
        """Get current A/B test status."""
        metrics = self.get_phase_metrics()

        return {
            'current_phase': self._current_phase.value,
            'cognitive_percentage': self._phase_config.cognitive_percentage,
            'is_killed': self._killed,
            'kill_reason': self._kill_reason,
            'games_this_phase': self._games_this_phase,
            'cognitive_games': self._cognitive_games,
            'static_games': self._static_games,
            'min_games_for_promotion': self._phase_config.min_games_before_promotion,
            'games_until_promotion': max(0, self._phase_config.min_games_before_promotion - self._games_this_phase),
            'metrics': {
                'avg_rungs': metrics.cognitive_avg_rungs,
                'avg_latency_ms': metrics.cognitive_avg_latency,
                'first_win_rate': metrics.cognitive_first_win_rate,
                'backtrack_rate': metrics.cognitive_backtrack_rate,
                'divergence_rate': metrics.divergence_rate,
            },
            'thresholds': self._phase_config.required_metrics,
        }


# =============================================================================
# DATABASE SCHEMA
# =============================================================================

AB_TEST_SCHEMA = """
CREATE TABLE IF NOT EXISTS ab_test_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    game_id TEXT NOT NULL,
    variant TEXT NOT NULL,
    phase TEXT NOT NULL,
    rungs_evaluated INTEGER,
    latency_ms REAL,
    first_win INTEGER,
    backtracked INTEGER,
    had_divergence INTEGER
);

CREATE INDEX IF NOT EXISTS idx_ab_test_game_id ON ab_test_results(game_id);
CREATE INDEX IF NOT EXISTS idx_ab_test_variant ON ab_test_results(variant);
CREATE INDEX IF NOT EXISTS idx_ab_test_phase ON ab_test_results(phase);
"""
