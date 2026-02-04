"""
Shadow Testing Infrastructure - Phase 5.1.

Compare cognitive router vs static ordering in parallel,
tracking divergences and collecting performance metrics.

This enables safe rollout by:
1. Running both systems on same inputs
2. Using static system for actual decisions (safety)
3. Logging divergences for analysis
4. Building confidence before full switch

Usage:
    tester = ShadowTester(db_interface)
    result = tester.shadow_test(game_state, context)

    # Always returns static action (safety)
    # But logs cognitive router result for comparison
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

class DivergenceType(Enum):
    """Types of divergence between static and cognitive routing."""
    ACTION_MISMATCH = "action_mismatch"       # Different final action
    CONFIDENCE_DELTA = "confidence_delta"      # Different confidence level
    PATH_DIFFERENCE = "path_difference"        # Different rungs evaluated
    TIMING_ANOMALY = "timing_anomaly"          # Significant timing difference
    NO_DIVERGENCE = "no_divergence"            # Systems agreed


@dataclass
class DivergenceRecord:
    """Record of a divergence between static and cognitive routing."""
    timestamp: str
    game_id: str
    agent_id: str
    divergence_type: DivergenceType

    # Static system results
    static_action: str
    static_confidence: float
    static_rungs_evaluated: int
    static_latency_ms: float

    # Cognitive system results
    cognitive_action: str
    cognitive_confidence: float
    cognitive_rungs_evaluated: int
    cognitive_latency_ms: float
    cognitive_algorithm: str
    cognitive_quadrant: str

    # Analysis
    severity: str = "low"  # low, medium, high
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'timestamp': self.timestamp,
            'game_id': self.game_id,
            'agent_id': self.agent_id,
            'divergence_type': self.divergence_type.value,
            'static_action': self.static_action,
            'static_confidence': self.static_confidence,
            'static_rungs_evaluated': self.static_rungs_evaluated,
            'static_latency_ms': self.static_latency_ms,
            'cognitive_action': self.cognitive_action,
            'cognitive_confidence': self.cognitive_confidence,
            'cognitive_rungs_evaluated': self.cognitive_rungs_evaluated,
            'cognitive_latency_ms': self.cognitive_latency_ms,
            'cognitive_algorithm': self.cognitive_algorithm,
            'cognitive_quadrant': self.cognitive_quadrant,
            'severity': self.severity,
            'notes': self.notes,
        }


@dataclass
class ShadowTestResult:
    """Result of a shadow test comparing both systems."""
    # Primary output (always from static for safety)
    action: str
    confidence: float
    reasoning: str

    # Divergence info
    divergence: Optional[DivergenceRecord] = None
    has_divergence: bool = False

    # Metadata
    static_latency_ms: float = 0.0
    cognitive_latency_ms: float = 0.0
    total_latency_ms: float = 0.0


@dataclass
class ShadowTestConfig:
    """Configuration for shadow testing."""
    # Divergence thresholds
    confidence_delta_threshold: float = 0.15  # Log if confidence differs by >15%
    timing_ratio_threshold: float = 3.0  # Log if timing differs by >3x

    # Behavior
    log_all_divergences: bool = True
    store_to_database: bool = True
    use_cognitive_if_static_fails: bool = False  # Fallback option

    # Limits
    max_cognitive_latency_ms: float = 100.0  # Skip cognitive if too slow


# =============================================================================
# SHADOW TESTER
# =============================================================================

class ShadowTester:
    """
    Shadow testing infrastructure for cognitive routing rollout.

    Runs both static and cognitive systems in parallel, using
    static results for actual decisions while logging divergences.
    """

    def __init__(
        self,
        db_interface: Optional[Any] = None,
        config: Optional[ShadowTestConfig] = None
    ):
        """Initialize shadow tester."""
        self.db = db_interface
        self.config = config or ShadowTestConfig()

        # Statistics
        self._test_count = 0
        self._divergence_count = 0
        self._divergences: List[DivergenceRecord] = []

        # Cached systems (lazy-loaded)
        self._static_system = None
        self._cognitive_router = None

        logger.info("[SHADOW] Shadow tester initialized")

    # -------------------------------------------------------------------------
    # LAZY LOADING
    # -------------------------------------------------------------------------

    def _get_static_system(self):
        """Lazy-load the static decision system."""
        if self._static_system is None:
            # Import here to avoid circular imports
            from decision_rung_system import DecisionRungSystem, DecisionStrategy
            self._static_system = DecisionRungSystem(strategy=DecisionStrategy.LADDER)
            self._static_system.load_ordering('comprehensive')
        return self._static_system

    def _get_cognitive_router(self):
        """Lazy-load the cognitive router."""
        if self._cognitive_router is None:
            from engines.cognition.cognitive_router import CognitiveRouter, RouterConfig
            config = RouterConfig(
                max_iterations=30,
                commit_threshold=0.85,
                use_hysteresis=True,
                use_catastrophic_fallback=True,
            )
            self._cognitive_router = CognitiveRouter(config=config)
        return self._cognitive_router

    # -------------------------------------------------------------------------
    # MAIN SHADOW TEST
    # -------------------------------------------------------------------------

    def shadow_test(
        self,
        game_state: Dict[str, Any],
        context: Dict[str, Any],
        game_id: str = "unknown",
        agent_id: str = "unknown",
        rung_executor: Optional[Callable] = None
    ) -> ShadowTestResult:
        """
        Run both static and cognitive systems, compare outputs.

        Always returns static action for safety during rollout.
        Logs divergences for analysis.

        Args:
            game_state: Current game state
            context: Decision context
            game_id: Game identifier
            agent_id: Agent identifier
            rung_executor: Optional rung executor for cognitive router

        Returns:
            ShadowTestResult with static action and divergence info
        """
        self._test_count += 1
        total_start = time.perf_counter()

        # Run static system first (always)
        static_start = time.perf_counter()
        static_action, static_confidence, static_reasoning, static_rungs = (
            self._run_static(game_state, context)
        )
        static_latency = (time.perf_counter() - static_start) * 1000

        # Run cognitive system (for comparison)
        cognitive_start = time.perf_counter()
        cognitive_result = self._run_cognitive(
            game_state, context, rung_executor
        )
        cognitive_latency = (time.perf_counter() - cognitive_start) * 1000

        total_latency = (time.perf_counter() - total_start) * 1000

        # Compare results
        divergence = self._analyze_divergence(
            game_id=game_id,
            agent_id=agent_id,
            static_action=static_action,
            static_confidence=static_confidence,
            static_rungs=static_rungs,
            static_latency=static_latency,
            cognitive_result=cognitive_result,
            cognitive_latency=cognitive_latency,
        )

        # Store divergence if found
        if divergence and divergence.divergence_type != DivergenceType.NO_DIVERGENCE:
            self._divergence_count += 1
            self._divergences.append(divergence)

            if self.config.store_to_database and self.db:
                self._store_divergence(divergence)

            if self.config.log_all_divergences:
                logger.warning(
                    f"[SHADOW] Divergence in {game_id}: "
                    f"static={static_action} vs cognitive={cognitive_result.get('action', 'N/A')}"
                )

        return ShadowTestResult(
            action=static_action,
            confidence=static_confidence,
            reasoning=static_reasoning,
            divergence=divergence,
            has_divergence=(
                divergence is not None and
                divergence.divergence_type != DivergenceType.NO_DIVERGENCE
            ),
            static_latency_ms=static_latency,
            cognitive_latency_ms=cognitive_latency,
            total_latency_ms=total_latency,
        )

    # -------------------------------------------------------------------------
    # SYSTEM RUNNERS
    # -------------------------------------------------------------------------

    def _run_static(
        self,
        game_state: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[str, float, str, int]:
        """
        Run the static decision system.

        Returns:
            Tuple of (action, confidence, reasoning, rungs_evaluated)
        """
        try:
            system = self._get_static_system()
            result = system.decide(game_state, context)

            if isinstance(result, tuple) and len(result) >= 2:
                action = result[0]
                reasoning = result[1] if len(result) > 1 else ""
                confidence = context.get('confidence', 0.5)
                rungs = context.get('rungs_evaluated', len(system._ordering))
            else:
                action = str(result)
                reasoning = ""
                confidence = 0.5
                rungs = len(system._ordering)

            return action, confidence, reasoning, rungs

        except Exception as e:
            logger.error(f"[SHADOW] Static system error: {e}")
            return "ACTION1", 0.0, f"Error: {e}", 0

    def _run_cognitive(
        self,
        game_state: Dict[str, Any],
        context: Dict[str, Any],
        rung_executor: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Run the cognitive router.

        Returns:
            Dictionary with cognitive router results
        """
        try:
            router = self._get_cognitive_router()

            # Initialize if needed
            if not router._initialized:
                # Get nodes/edges from config
                from engines.cognition.precomputation import load_graph_config
                nodes, edges = load_graph_config()
                router.initialize(nodes, edges)

            # Run decision
            result = router.decide(game_state, rung_executor)

            return {
                'action': result.selected_action,
                'confidence': result.confidence,
                'iterations': result.iterations,
                'algorithm': result.algorithm_used,
                'quadrant': result.final_quadrant,
                'path': result.rung_path,
                'used_fallback': result.used_fallback,
            }

        except Exception as e:
            logger.error(f"[SHADOW] Cognitive router error: {e}")
            return {
                'action': 'ERROR',
                'confidence': 0.0,
                'iterations': 0,
                'algorithm': 'none',
                'quadrant': 'UU',
                'path': [],
                'used_fallback': False,
                'error': str(e),
            }

    # -------------------------------------------------------------------------
    # DIVERGENCE ANALYSIS
    # -------------------------------------------------------------------------

    def _analyze_divergence(
        self,
        game_id: str,
        agent_id: str,
        static_action: str,
        static_confidence: float,
        static_rungs: int,
        static_latency: float,
        cognitive_result: Dict[str, Any],
        cognitive_latency: float,
    ) -> DivergenceRecord:
        """Analyze divergence between static and cognitive results."""
        cognitive_action = cognitive_result.get('action', 'N/A')
        cognitive_confidence = cognitive_result.get('confidence', 0.0)
        cognitive_iterations = cognitive_result.get('iterations', 0)

        # Determine divergence type
        divergence_type = DivergenceType.NO_DIVERGENCE
        severity = "low"
        notes = ""

        # Check action mismatch (highest priority)
        if static_action != cognitive_action:
            divergence_type = DivergenceType.ACTION_MISMATCH
            severity = "high"
            notes = f"Actions differ: {static_action} vs {cognitive_action}"

        # Check confidence delta
        elif abs(static_confidence - cognitive_confidence) > self.config.confidence_delta_threshold:
            divergence_type = DivergenceType.CONFIDENCE_DELTA
            severity = "medium"
            notes = f"Confidence delta: {abs(static_confidence - cognitive_confidence):.2f}"

        # Check timing anomaly
        elif cognitive_latency > 0 and static_latency > 0:
            ratio = max(cognitive_latency, static_latency) / min(cognitive_latency, static_latency)
            if ratio > self.config.timing_ratio_threshold:
                divergence_type = DivergenceType.TIMING_ANOMALY
                severity = "low"
                notes = f"Timing ratio: {ratio:.1f}x"

        # Check path difference (rungs evaluated)
        elif abs(static_rungs - cognitive_iterations) > 10:
            divergence_type = DivergenceType.PATH_DIFFERENCE
            severity = "low"
            notes = f"Rungs: {static_rungs} vs {cognitive_iterations}"

        return DivergenceRecord(
            timestamp=datetime.now().isoformat(),
            game_id=game_id,
            agent_id=agent_id,
            divergence_type=divergence_type,
            static_action=static_action,
            static_confidence=static_confidence,
            static_rungs_evaluated=static_rungs,
            static_latency_ms=static_latency,
            cognitive_action=cognitive_action,
            cognitive_confidence=cognitive_confidence,
            cognitive_rungs_evaluated=cognitive_iterations,
            cognitive_latency_ms=cognitive_latency,
            cognitive_algorithm=cognitive_result.get('algorithm', 'unknown'),
            cognitive_quadrant=cognitive_result.get('quadrant', 'UU'),
            severity=severity,
            notes=notes,
        )

    def _store_divergence(self, record: DivergenceRecord) -> None:
        """Store divergence record to database."""
        if not self.db:
            return

        try:
            self.db.execute("""
                INSERT INTO shadow_test_divergences (
                    timestamp, game_id, agent_id, divergence_type,
                    static_action, static_confidence, static_rungs_evaluated, static_latency_ms,
                    cognitive_action, cognitive_confidence, cognitive_rungs_evaluated, cognitive_latency_ms,
                    cognitive_algorithm, cognitive_quadrant, severity, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.timestamp, record.game_id, record.agent_id, record.divergence_type.value,
                record.static_action, record.static_confidence, record.static_rungs_evaluated, record.static_latency_ms,
                record.cognitive_action, record.cognitive_confidence, record.cognitive_rungs_evaluated, record.cognitive_latency_ms,
                record.cognitive_algorithm, record.cognitive_quadrant, record.severity, record.notes,
            ))
        except Exception as e:
            logger.error(f"[SHADOW] Failed to store divergence: {e}")

    # -------------------------------------------------------------------------
    # STATISTICS
    # -------------------------------------------------------------------------

    def get_statistics(self) -> Dict[str, Any]:
        """Get shadow testing statistics."""
        if self._test_count == 0:
            return {
                'test_count': 0,
                'divergence_count': 0,
                'divergence_rate': 0.0,
                'by_type': {},
                'by_severity': {},
            }

        # Count by type
        by_type: Dict[str, int] = {}
        by_severity: Dict[str, int] = {}

        for d in self._divergences:
            type_key = d.divergence_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1
            by_severity[d.severity] = by_severity.get(d.severity, 0) + 1

        return {
            'test_count': self._test_count,
            'divergence_count': self._divergence_count,
            'divergence_rate': self._divergence_count / self._test_count,
            'by_type': by_type,
            'by_severity': by_severity,
            'action_mismatch_rate': by_type.get('action_mismatch', 0) / self._test_count,
        }

    def reset_statistics(self) -> None:
        """Reset all statistics."""
        self._test_count = 0
        self._divergence_count = 0
        self._divergences.clear()

    def get_recent_divergences(self, n: int = 10) -> List[DivergenceRecord]:
        """Get the most recent divergences."""
        return self._divergences[-n:]


# =============================================================================
# DATABASE SCHEMA FOR DIVERGENCES
# =============================================================================

SHADOW_TEST_SCHEMA = """
CREATE TABLE IF NOT EXISTS shadow_test_divergences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    game_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    divergence_type TEXT NOT NULL,
    static_action TEXT,
    static_confidence REAL,
    static_rungs_evaluated INTEGER,
    static_latency_ms REAL,
    cognitive_action TEXT,
    cognitive_confidence REAL,
    cognitive_rungs_evaluated INTEGER,
    cognitive_latency_ms REAL,
    cognitive_algorithm TEXT,
    cognitive_quadrant TEXT,
    severity TEXT,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_shadow_test_game_id ON shadow_test_divergences(game_id);
CREATE INDEX IF NOT EXISTS idx_shadow_test_divergence_type ON shadow_test_divergences(divergence_type);
CREATE INDEX IF NOT EXISTS idx_shadow_test_severity ON shadow_test_divergences(severity);
"""
